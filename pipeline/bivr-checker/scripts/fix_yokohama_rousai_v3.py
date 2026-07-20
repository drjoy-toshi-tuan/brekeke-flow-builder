#!/usr/bin/env python3
"""
fix_yokohama_rousai_v3.py — 横浜労災病院 フロー順序根本修正

フロー順序を以下に変更:
  冒頭アナウンス
  → 1. 氏名聴取（インライン）
  → 2. 注意事項アナウンス
  → 3. 生年月日聴取（インライン）
  → 4. 診療健診分岐
  → 5. 診察券番号聴取（インライン）   ※診療パスのみ
  → 6. 電話番号聴取（インライン）
  → 7. 用件聴取
  → 各用件ルーティング → script_SMS判定 → 完了フラグ_受付完了_SMS/noSMS

変更内容:
  - Jump to Flow × 4 を削除
  - 4サブフローのモジュールをメインフローにインライン化
  - 既存モジュールのレイアウトを一括シフト（+8000〜+11000px）して挿入スペースを確保
  - Jump_氏名聴取 参照箇所を script_SMS判定 に置き換え
  - script_SMS判定 モジュールを新規追加
"""

import json
import sys
import os
import glob
import zipfile
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FIXED_DIR  = "output/横浜労災病院/fixed/flows"
MAIN_FLOW  = os.path.join(FIXED_DIR, "横浜労災$診療_20260403.json")
BIVR_OUT   = "output/横浜労災病院/横浜労災病院_fixed.bivr"

# サブフローパス
SUBFLOWS = {
    "氏名":       os.path.join(FIXED_DIR, "横浜労災$氏名聴取.json"),
    "生年月日":   os.path.join(FIXED_DIR, "横浜労災$生年月日聴取.json"),
    "診察券番号": os.path.join(FIXED_DIR, "横浜労災$診察券番号聴取.json"),
    "電話番号":   os.path.join(FIXED_DIR, "横浜労災$電話番号聴取.json"),
}

# 既存モジュールでシフト対象外（冒頭チェーン + 非通知/時間外ブランチ）
NO_SHIFT_MODULES = {
    "冒頭",                  # wait
    "コンテキスト設定",      # saveContextModel2DB
    "着信分類",              # incoming-classifier
    "acceptance_times",
    "非通知_アナウンス",
    "完了フラグ_非通知",
    "切断_非通知",
    "時間外_アナウンス",
    "完了フラグ_時間外",
    "切断_時間外",
    "save-時間外",
    "冒頭_アナウンス",
    "save-冒頭",
}

# 2段階シフト量
#  y < 1200 (注意事項系) → +8000
#  y >= 1200 (診療健診以降) → +11000
SHIFT_LOW  = 8000   # for 注意事項_アナウンス family (y=1000)
SHIFT_HIGH = 11000  # for 診療健診 and everything below (y>=1200)
Y_BOUNDARY = 1150   # 境界y値（注意事項は1000、診療健診は1200）


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ────────────────────────────────────────────
# Step 1: 既存モジュールのレイアウトシフト
# ────────────────────────────────────────────
def shift_existing_layouts(modules):
    """
    - NO_SHIFT_MODULESは変更しない
    - y < Y_BOUNDARY: +SHIFT_LOW
    - y >= Y_BOUNDARY: +SHIFT_HIGH
    """
    shifted = 0
    for name, mod in modules.items():
        if name in NO_SHIFT_MODULES:
            continue
        layout = mod.get("layout", {})
        y = layout.get("y", 0)
        if y < Y_BOUNDARY:
            layout["y"] = y + SHIFT_LOW
        else:
            layout["y"] = y + SHIFT_HIGH
        mod["layout"] = layout
        shifted += 1
    print(f"  [SHIFT] {shifted} modules shifted")


# ────────────────────────────────────────────
# Step 2: サブフローモジュール抽出
# ────────────────────────────────────────────
# サブフロー固有モジュール（インライン化時に除外）
SUBFLOW_ONLY_TYPES = {
    "Custom$wait",
    "drjoy^Persistence$saveContextModel2DB",
    "drjoy^External Integration$acceptance_times",
}
SUBFLOW_RESULT_SCRIPT_PREFIX = "script_結果返却_"

def extract_subflow_modules(subflow_path, exclude_names=None):
    """サブフローからインライン化対象のモジュールを抽出する"""
    flow = load_json(subflow_path)
    mods = flow["modules"]
    extracted = {}
    excluded = set(exclude_names or [])
    for name, mod in mods.items():
        mtype = mod.get("type", "")
        # サブフロー固有モジュールを除外
        skip = False
        for st in SUBFLOW_ONLY_TYPES:
            if st in mtype:
                skip = True
                break
        if name.startswith(SUBFLOW_RESULT_SCRIPT_PREFIX):
            skip = True
        if name in excluded:
            skip = True
        if not skip:
            extracted[name] = mod
    return extracted


# ────────────────────────────────────────────
# Step 3: 新規モジュールの接続を修正してメインフローに追加
# ────────────────────────────────────────────

# 氏名聴取インライン用レイアウト（y=1000〜2200）
NAME_LAYOUTS = {
    "患者_氏名":             {"x": 500,  "y": 1000},
    "save-患者_氏名":         {"x": 800,  "y": 1000},
    "入力_患者_氏名":         {"x": 500,  "y": 1180},
    "OpenAI_患者_氏名":       {"x": 500,  "y": 1360},
    "リトライ_患者_氏名":      {"x": 200,  "y": 1360},
    "復唱_患者_氏名":          {"x": 500,  "y": 1560},
    "save-復唱_患者_氏名":     {"x": 800,  "y": 1560},
    "入力_復唱_患者_氏名":     {"x": 500,  "y": 1740},
    "OpenAI_復唱_患者_氏名":   {"x": 500,  "y": 1920},
    "リトライ_復唱_患者_氏名":  {"x": 200,  "y": 1920},
}

# 生年月日聴取インライン用レイアウト（注意事項_アナウンス y=9000の直後 y=9200〜10400）
DOB_LAYOUTS = {
    "患者_生年月日":             {"x": 500,  "y": 9200},
    "save-患者_生年月日":         {"x": 800,  "y": 9200},
    "入力_患者_生年月日":         {"x": 500,  "y": 9380},
    "OpenAI_患者_生年月日":       {"x": 500,  "y": 9560},
    "リトライ_患者_生年月日":      {"x": 200,  "y": 9560},
    "復唱_患者_生年月日":          {"x": 500,  "y": 9760},
    "save-復唱_患者_生年月日":     {"x": 800,  "y": 9760},
    "入力_復唱_患者_生年月日":     {"x": 500,  "y": 9940},
    "OpenAI_復唱_患者_生年月日":   {"x": 500,  "y": 10120},
    "リトライ_復唱_患者_生年月日":  {"x": 200,  "y": 10120},
}

# 診察券番号聴取インライン用レイアウト（診療健診 y=12200の直後 y=12500〜13700）
CARD_LAYOUTS = {
    "患者_診察券番号":             {"x": 500,  "y": 12500},
    "save-患者_診察券番号":         {"x": 800,  "y": 12500},
    "入力_患者_診察券番号":         {"x": 500,  "y": 12680},
    "OpenAI_患者_診察券番号":       {"x": 500,  "y": 12860},
    "リトライ_患者_診察券番号":      {"x": 200,  "y": 12860},
    "復唱_患者_診察券番号":          {"x": 500,  "y": 13060},
    "save-復唱_患者_診察券番号":     {"x": 800,  "y": 13060},
    "入力_復唱_患者_診察券番号":     {"x": 500,  "y": 13240},
    "OpenAI_復唱_患者_診察券番号":   {"x": 500,  "y": 13420},
    "リトライ_復唱_患者_診察券番号":  {"x": 200,  "y": 13420},
}

# 電話番号聴取インライン用レイアウト（診察券番号の後 y=13700〜15200）
PHONE_LAYOUTS = {
    "患者_連絡先":               {"x": 500,  "y": 13700},
    "save-患者_連絡先":           {"x": 800,  "y": 13700},
    "着信分類_電話番号":           {"x": 500,  "y": 13880},
    "入力_患者_連絡先":           {"x": 500,  "y": 14060},
    "OpenAI_患者_連絡先":         {"x": 500,  "y": 14240},
    "リトライ_患者_連絡先":        {"x": 200,  "y": 14240},
    "script_携帯判別":            {"x": 500,  "y": 14440},
    "復唱_患者_連絡先":            {"x": 500,  "y": 14640},
    "save-復唱_患者_連絡先":       {"x": 800,  "y": 14640},
    "入力_復唱_患者_連絡先":       {"x": 500,  "y": 14820},
    "OpenAI_復唱_患者_連絡先":     {"x": 500,  "y": 15000},
    "リトライ_復唱_患者_連絡先":    {"x": 200,  "y": 15000},
    "script_smsFlag設定":         {"x": 500,  "y": 15200},
}

ALL_LAYOUTS = {**NAME_LAYOUTS, **DOB_LAYOUTS, **CARD_LAYOUTS, **PHONE_LAYOUTS}


def patch_module_connections(mods_dict, conn_changes):
    """
    conn_changes: {module_name: [(old_next_name, new_next_name), ...]}
    next配列の nextModuleName を付け替える
    """
    for mod_name, changes in conn_changes.items():
        mod = mods_dict.get(mod_name)
        if not mod:
            print(f"  [WARN] patch target not found: {mod_name}")
            continue
        for old_name, new_name in changes:
            patched = False
            for item in mod.get("next", []):
                if item.get("nextModuleName") == old_name:
                    item["nextModuleName"] = new_name
                    patched = True
            if not patched:
                print(f"  [WARN] {mod_name}: next→{old_name} not found")
            else:
                print(f"  [CONN] {mod_name}: {old_name} → {new_name}")


def replace_all_references(modules, old_name, new_name):
    """フロー全体でモジュール名参照を一括置換"""
    count = 0
    for mod in modules.values():
        for item in mod.get("next", []):
            if item.get("nextModuleName") == old_name:
                item["nextModuleName"] = new_name
                count += 1
        for item in mod.get("subs", []):
            if item.get("moduleName") == old_name:
                item["moduleName"] = new_name
                count += 1
    if count:
        print(f"  [REPLACE] {old_name} → {new_name}: {count} refs updated")
    else:
        print(f"  [WARN] no refs to {old_name} found")


def add_inline_modules(main_mods, subflow_mods, layouts):
    """抽出したサブフローモジュールをメインフローに追加"""
    for name, mod in subflow_mods.items():
        if name in layouts:
            mod["layout"] = layouts[name]
        main_mods[name] = mod
    print(f"  [ADD] {len(subflow_mods)} modules added")


# ────────────────────────────────────────────
# Step 4: script_smsFlag設定 / script_SMS判定 モジュール生成
# ────────────────────────────────────────────

def make_sms_flag_module():
    """script_結果返却_電話番号 の代替: smsFlag設定後に 用件 へ"""
    script = (
        "var phone = $runner.getModuleResult('OpenAI_患者_連絡先') || '';"
        "var classify = $runner.getModuleResult('script_携帯判別') || '';"
        "var smsFlag = (classify === '携帯') ? '1' : '0';"
        "$runner.setContext('smsFlag', smsFlag);"
        "$flow.result = phone;"
        "// 携帯電話判別/携帯以外の集約結果をsmsFlagに反映"
    )
    return {
        "type": "@General$Script",
        "name": "script_smsFlag設定",
        "params": {"script": script},
        "next": [
            {"condition": "^.*$", "label": "next", "nextModuleName": "用件"},
            {"condition": "", "label": "", "nextModuleName": ""},
        ],
        "subs": [],
        "layout": PHONE_LAYOUTS.get("script_smsFlag設定", {"x": 500, "y": 15200}),
    }


def make_sms_router_module():
    """script_SMS判定: smsFlag に基づき 完了フラグ_受付完了_SMS/noSMS へルーティング"""
    script = (
        "var classify = $runner.getModuleResult('script_携帯判別') || '';"
        "classify === '携帯' ? 'SMS' : 'noSMS';"
    )
    return {
        "type": "@General$Script",
        "name": "script_SMS判定",
        "params": {"script": script},
        "next": [
            {"condition": "^SMS$",  "label": "SMS",   "nextModuleName": "完了フラグ_受付完了_SMS"},
            {"condition": "^.*$",   "label": "noSMS", "nextModuleName": "完了フラグ_受付完了_noSMS"},
            {"condition": "", "label": "", "nextModuleName": ""},
        ],
        "subs": [],
        "layout": {"x": 500, "y": 15500},
    }


# ────────────────────────────────────────────
# Main
# ────────────────────────────────────────────
def main():
    print("=== 横浜労災病院 フロー順序根本修正 (v3) ===\n")

    flow = load_json(MAIN_FLOW)
    mods = flow["modules"]

    # ── Step 1: 既存モジュールレイアウトシフト ──
    print("[Step 1] 既存モジュールレイアウトシフト")
    shift_existing_layouts(mods)
    print()

    # ── Step 2: サブフローからモジュール抽出 ──
    print("[Step 2] サブフローモジュール抽出")
    sf_name    = extract_subflow_modules(SUBFLOWS["氏名"])
    sf_dob     = extract_subflow_modules(SUBFLOWS["生年月日"])
    sf_card    = extract_subflow_modules(SUBFLOWS["診察券番号"])
    sf_phone   = extract_subflow_modules(SUBFLOWS["電話番号"])
    print(f"  氏名:       {len(sf_name)} modules")
    print(f"  生年月日:   {len(sf_dob)} modules")
    print(f"  診察券番号: {len(sf_card)} modules")
    print(f"  電話番号:   {len(sf_phone)} modules")
    print()

    # ── Step 3: インライン化モジュール追加 ──
    print("[Step 3] インライン化モジュール追加")
    add_inline_modules(mods, sf_name,  NAME_LAYOUTS)
    add_inline_modules(mods, sf_dob,   DOB_LAYOUTS)
    add_inline_modules(mods, sf_card,  CARD_LAYOUTS)
    add_inline_modules(mods, sf_phone, PHONE_LAYOUTS)
    # script_smsFlag設定 と script_SMS判定 を追加（電話番号の script_結果返却_電話番号 除去済みのため）
    mods["script_smsFlag設定"] = make_sms_flag_module()
    mods["script_SMS判定"]    = make_sms_router_module()
    print(f"  [ADD] script_smsFlag設定, script_SMS判定")
    print()

    # ── Step 4: 接続修正 ──
    print("[Step 4] 接続修正")

    # 4-1. 冒頭_アナウンス → 患者_氏名（was: 注意事項_アナウンス）
    patch_module_connections(mods, {
        "冒頭_アナウンス": [("注意事項_アナウンス", "患者_氏名")],
    })

    # 4-2. 氏名聴取終了 → 注意事項_アナウンス
    patch_module_connections(mods, {
        "OpenAI_復唱_患者_氏名":  [("script_結果返却_氏名", "注意事項_アナウンス")],
        "リトライ_復唱_患者_氏名": [("script_結果返却_氏名", "注意事項_アナウンス")],
    })

    # 4-3. 注意事項_アナウンス → 患者_生年月日（was: 診療健診）
    patch_module_connections(mods, {
        "注意事項_アナウンス": [("診療健診", "患者_生年月日")],
    })

    # 4-4. 生年月日聴取終了 → 診療健診
    patch_module_connections(mods, {
        "OpenAI_復唱_患者_生年月日":  [("script_結果返却_生年月日", "診療健診")],
        "リトライ_復唱_患者_生年月日": [("script_結果返却_生年月日", "診療健診")],
    })

    # 4-5. OpenAI_診療健診 診療パス → 患者_診察券番号（was: 用件）
    patch_module_connections(mods, {
        "OpenAI_診療健診": [("用件", "患者_診察券番号")],
    })

    # 4-6. 診察券番号聴取終了 → 患者_連絡先
    patch_module_connections(mods, {
        "OpenAI_患者_診察券番号":       [("script_結果返却_診察券番号", "患者_連絡先")],
        "OpenAI_復唱_患者_診察券番号":  [("script_結果返却_診察券番号", "患者_連絡先")],
        "リトライ_患者_診察券番号":      [("script_結果返却_診察券番号", "患者_連絡先")],
        "リトライ_復唱_患者_診察券番号": [("script_結果返却_診察券番号", "患者_連絡先")],
    })

    # 4-7. 電話番号聴取終了 → script_smsFlag設定（新規）
    patch_module_connections(mods, {
        "OpenAI_復唱_患者_連絡先":  [("script_結果返却_電話番号", "script_smsFlag設定")],
        "リトライ_復唱_患者_連絡先": [("script_結果返却_電話番号", "script_smsFlag設定")],
        "リトライ_患者_連絡先":      [("script_結果返却_電話番号", "script_smsFlag設定")],
    })

    # 4-8. Jump_氏名聴取 → script_SMS判定（全参照一括置換）
    replace_all_references(mods, "Jump_氏名聴取", "script_SMS判定")
    print()

    # ── Step 5: 不要モジュール削除 ──
    print("[Step 5] 不要モジュール削除")
    REMOVE_MODULES = [
        "Jump_氏名聴取",
        "Jump_生年月日聴取",
        "Jump_診察券番号聴取",
        "Jump_電話番号聴取",
    ]
    for name in REMOVE_MODULES:
        if name in mods:
            del mods[name]
            print(f"  [DEL] {name}")
        else:
            print(f"  [SKIP] {name} (not found)")
    print()

    # ── Step 6: 保存 ──
    print("[Step 6] メインフロー保存")
    save_json(flow, MAIN_FLOW)
    print(f"  [OK] {MAIN_FLOW}")
    print(f"  modules: {len(mods)}")
    print()

    # ── Step 7: サブフローJSONを削除 ──
    print("[Step 7] サブフローJSON削除")
    for label, path in SUBFLOWS.items():
        if os.path.exists(path):
            os.remove(path)
            print(f"  [DEL] {path}")
        else:
            print(f"  [SKIP] {path}")
    print()

    # ── Step 8: .bivr 再構築 ──
    print("[Step 8] .bivr 再構築")
    flow_files = glob.glob(os.path.join(FIXED_DIR, "*.json"))
    with zipfile.ZipFile(BIVR_OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fpath in flow_files:
            fl = load_json(fpath)
            fn = fl.get("name", "")
            entry = f"flows/@flow_{quote(fn, safe='')}.txt"
            zf.writestr(entry, json.dumps(fl, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    size = os.path.getsize(BIVR_OUT)
    print(f"  [OK] {BIVR_OUT} ({size:,} bytes, {len(flow_files)} flows)")
    print()

    print("=== 完了 ===")


if __name__ == "__main__":
    main()
