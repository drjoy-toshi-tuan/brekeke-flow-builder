# -*- coding: utf-8 -*-
"""厚木統合CC: generate_by_OpenAI 全 13 箇所を決定論 Script へ差し替える単発パッチ（bivr_patches 規約）。

実行: python tools/bivr_patches/patch_atsugi_deterministic_20260610.py
入力: output/scenarios/ヘルスケアクリニック厚木_統合CC/ヘルスケアクリニック厚木_統合CC_20260610.bivr
出力: 同ディレクトリ ..._20260610_deterministic.bivr（メインフロー + 復唱系を含むサブフロー2本を書き換え）

差し替え内容（メインフロー $統合CC, 10 箇所）:
- 9 箇所: 入力STT ^.+$ → Script_X（@General$Script、modules/ の oracle 受入済み正本を SOURCE_MODULE/MENU 置換で埋込）
  - DTMF 数字も Script が 1 ホップで正規化（context にラベルを保存するため STT 直接分岐にはしない。
    例外は下記の現在の予約日）。Script の sub に save2db を付けてラベルを context 保存
    （その他コース確認のみ sub なし＝STT の生テキスト保存を温存）。
- 1 箇所: 現在の予約日 = STT 直接分岐（^[0-9]{8}$ → 再受診希望。生 8 桁こそが保存値のため）。
- CMR 施設確定後分岐 の参照を OpenAI_遅刻種別確認 → Script_遅刻種別確認 に付替え。
- OpenAI_* 10 モジュールを削除。

差し替え内容（サブフロー, 3 箇所＝2026-06-15 追加。旧版はメインのみで未変換だった分）:
- 生年月日聴取: openAI_復唱_患者生年月日 → Script_復唱_患者生年月日（yes_no_classifier）
- 電話番号聴取: openAI_患者_復唱連絡先 / openAI_患者_携帯電話 → Script_*（yes_no_classifier）
  いずれも復唱の肯定/否定確認。肯定/否定/NO_RESULT の分岐先は原 OpenAI のものを温存。

検証: 差替後に各フロー内へ 'OpenAI'/'openAI' 参照が残っていないこと / 全 next・subs 参照先が存在することを機械チェック。
"""
import io
import json
import os
import sys
import zipfile
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCN = os.path.join(ROOT, "output", "scenarios", "ヘルスケアクリニック厚木_統合CC")
SRC_BIVR = os.path.join(SCN, "ヘルスケアクリニック厚木_統合CC_20260610.bivr")
DST_BIVR = os.path.join(SCN, "ヘルスケアクリニック厚木_統合CC_20260610_deterministic.bivr")
MODULES_DIR = os.path.join(ROOT, "modules")

SITES = [
    {"step": "明日以降確認", "part": "yes_no_classifier", "save": None,
     "next": [("^肯定$", "エリア選択"), ("^否定$", "遅刻種別確認"),
              ("^NO_RESULT$", "リトライ_明日以降確認")]},
    {"step": "遅刻種別確認", "part": "checkup_intent_classifier", "save": "save-classification", "scope": "lateness",
     "next": [("^遅刻$", "エリア選択"), ("^変更$", "完了フラグ_当日受付不可"),
              ("^キャンセル$", "完了フラグ_当日受付不可"), ("^NO_RESULT$", "リトライ_遅刻種別確認"),
              ("^.*$", "リトライ_遅刻種別確認")]},
    # 用件確認: drawio v1.0 で {予約/変更/キャンセル/その他} の4分岐。市/特定は廃止用語＝SITES からも削除（死に枝防止）。
    {"step": "用件確認", "part": "checkup_intent_classifier", "save": "save-classification", "scope": "full",
     "next": [("^予約$", "コース選択"), ("^変更$", "変更受付案内"), ("^キャンセル$", "現在の予約日"),
              ("^その他$", "お問い合わせ内容"), ("^雇用時健診$", "完了フラグ_雇用時健診"),
              ("^遅刻$", "氏名聴取"), ("^NO_RESULT$", "リトライ_用件確認")]},
    {"step": "コース選択", "part": "checkup_course_classifier", "save": "save-course",
     "next": [("^人間ドック$", "氏名聴取"), ("^協会けんぽ$", "氏名聴取"), ("^定期健診$", "氏名聴取"),
              ("^雇用時健診$", "完了フラグ_雇用時健診"), ("^その他の健診$", "その他コース確認"),
              ("^NO_RESULT$", "リトライ_コース選択")]},
    # course の生テキスト保存（STT sub）を温存するため save なし
    {"step": "その他コース確認", "part": "checkup_course_classifier", "save": None,
     "next": [("^雇用時健診$", "完了フラグ_雇用時健診"), ("^NO_RESULT$", "リトライ_その他コース確認"),
              ("^.*$", "氏名聴取")]},
    {"step": "再受診希望", "part": "yes_no_classifier", "save": "save-rebooking",
     "next": [("^肯定$", "氏名聴取"), ("^否定$", "氏名聴取"), ("^NO_RESULT$", "リトライ_再受診希望")]},
    {"step": "エリア選択", "part": "checkup_menu_classifier", "menu": "area", "save": "save-area",
     "next": [("^神奈川エリア$", "施設案内_神奈川"), ("^新宿渋谷エリア$", "施設選択_新宿渋谷"),
              ("^東京品川エリア$", "施設選択_東京品川"), ("^NO_RESULT$", "リトライ_エリア選択")]},
    {"step": "施設選択_新宿渋谷", "part": "checkup_menu_classifier", "menu": "shinjuku_shibuya", "save": "save-facility",
     "next": [("^ヒロオカクリニック$", "施設確定後分岐"), ("^渋谷ウエストクリニック$", "施設確定後分岐"),
              ("^NO_RESULT$", "リトライ_施設選択_新宿渋谷")]},
    {"step": "施設選択_東京品川", "part": "checkup_menu_classifier", "menu": "tokyo_shinagawa", "save": "save-facility",
     "next": [("^ヘルスケアクリニック秋葉原$", "施設確定後分岐"), ("^鉄鋼ビル丸の内クリニック$", "施設確定後分岐"),
              ("^みなと健診クリニック$", "施設確定後分岐"), ("^NO_RESULT$", "リトライ_施設選択_東京品川")]},
]

# サブフロー内の OpenAI yes/no 確認（メインフロー外。旧版が未変換だった3箇所）。
# 命名が openAI_ 小文字のため openai/stt/script を明示。next は原 OpenAI の分岐を温存
# （yes_no_classifier は 肯定/否定/NO_RESULT を出力。STT 由来の TIMEOUT/ERROR は Script では発生しないため不要）。
SUBFLOW_SITES = {
    "生年月日聴取": [
        {"openai": "openAI_復唱_患者生年月日", "stt": "入力_復唱_患者生年月日",
         "script": "Script_復唱_患者生年月日", "part": "yes_no_classifier", "save": None,
         "next": [("^肯定$", ""), ("^否定$", "患者_生年月日"),
                  ("^NO_RESULT$", "リトライ_復唱_患者生年月日")]},
    ],
    "電話番号聴取": [
        {"openai": "openAI_患者_復唱連絡先", "stt": "入力_患者_復唱連絡先",
         "script": "Script_患者_復唱連絡先", "part": "yes_no_classifier", "save": None,
         "next": [("^肯定$", "script_携帯判別"), ("^否定$", "患者_連絡先"),
                  ("^NO_RESULT$", "リトライ_患者_復唱連絡先")]},
        {"openai": "openAI_患者_携帯電話", "stt": "入力_患者_携帯電話",
         "script": "Script_患者_携帯電話", "part": "yes_no_classifier", "save": None,
         "next": [("^肯定$", "携帯電話判別"), ("^否定$", "患者_連絡先"),
                  ("^NO_RESULT$", "リトライ_患者_携帯電話")]},
    ],
}


def load_script_body(part, source_module, menu=None, scope=None):
    path = os.path.join(MODULES_DIR, part, "script.js")
    body = io.open(path, "r", encoding="utf-8").read()
    if "__SOURCE_MODULE__" not in body:
        raise SystemExit("[ERROR] %s: __SOURCE_MODULE__ placeholder が見つからない" % part)
    body = body.replace("__SOURCE_MODULE__", source_module)
    if menu is not None:
        if "__MENU__" not in body:
            raise SystemExit("[ERROR] %s: __MENU__ placeholder が見つからない" % part)
        body = body.replace("__MENU__", menu)
    if scope is not None:
        if "__SCOPE__" not in body:
            raise SystemExit("[ERROR] %s: __SCOPE__ placeholder が見つからない（scope 指定だが SCOPE 設定行なし）" % part)
        body = body.replace("__SCOPE__", scope)
    return body


def pad_next(entries):
    out = [{"condition": c, "label": c.strip("^$") or "next", "nextModuleName": t} for c, t in entries]
    while len(out) < 10:
        out.append({"condition": "", "label": "", "nextModuleName": ""})
    return out


def pad_subs(names):
    out = [{"moduleName": n, "label": n} for n in names]
    while len(out) < 3:
        out.append({"moduleName": "", "label": ""})
    return out


def verify_flow_no_openai(mods, where):
    """フロー内に OpenAI/openAI 構造参照が残っていないこと + next/subs 参照先実在を機械チェック。"""
    leftovers = []
    for n, m in mods.items():
        if "OpenAI" in n or "openAI" in n or "OpenAI" in m.get("type", ""):
            leftovers.append(("module:" + n, m.get("type", "")))
        for nx in m.get("next", []):
            t = nx.get("nextModuleName") or ""
            if "OpenAI" in t or "openAI" in t:
                leftovers.append((n + ".next", t))
        for sb in m.get("subs", []):
            t = sb.get("moduleName") or ""
            if "OpenAI" in t or "openAI" in t:
                leftovers.append((n + ".subs", t))
        for k in ("module", "module1Name", "module2Name", "nodeName"):
            v = str(m.get("params", {}).get(k, ""))
            if "OpenAI" in v or "openAI" in v:
                leftovers.append((n + ".params." + k, v))
    if leftovers:
        for p, v in leftovers:
            print("[LEFTOVER] %s = %s" % (p, v))
        raise SystemExit("[ERROR] %s に OpenAI 構造参照が残存（%d 件）" % (where, len(leftovers)))
    names = set(mods.keys())
    for n, m in mods.items():
        for nx in m.get("next", []):
            t = nx.get("nextModuleName")
            if t and t not in names:
                raise SystemExit("[ERROR] %s: %s の next 参照先が不存在: %s" % (where, n, t))
        for sb in m.get("subs", []):
            t = sb.get("moduleName")
            if t and t not in names:
                raise SystemExit("[ERROR] %s: %s の subs 参照先が不存在: %s" % (where, n, t))
    print("[OK] 検証(%s): OpenAI 残存なし / 参照整合 %d modules" % (where, len(names)))


def patch_subflow(flow, sites):
    """サブフロー内の OpenAI yes/no モジュールを決定論 Script へ差し替える。"""
    mods = flow["modules"]
    for site in sites:
        openai, stt, script = site["openai"], site["stt"], site["script"]
        if openai not in mods:
            raise SystemExit("[ERROR] %s が見つからない（パッチ適用済み？）" % openai)
        if stt not in mods:
            raise SystemExit("[ERROR] %s が見つからない" % stt)
        body = load_script_body(site["part"], stt, site.get("menu"))
        mods[script] = {
            "layout": mods[openai].get("layout", {"x": 0, "y": 0}),
            "next": pad_next(site["next"]),
            "subs": pad_subs([site["save"]] if site.get("save") else []),
            "name": script,
            "description": "",
            "matchingmethod": 1,
            "type": "@General$Script",
            "params": {"module": stt, "script": body},
        }
        hit = False
        for nx in mods[stt].get("next", []):
            if nx.get("nextModuleName") == openai:
                nx["nextModuleName"] = script
                hit = True
        if not hit:
            raise SystemExit("[ERROR] %s から %s への next が見つからない" % (stt, openai))
        del mods[openai]
        print("[OK] %s -> %s（%s）" % (openai, script, site["part"]))
    return flow


def patch_main(flow):
    mods = flow["modules"]
    for site in SITES:
        step = site["step"]
        stt, openai, script = "入力_" + step, "OpenAI_" + step, "Script_" + step
        if openai not in mods:
            raise SystemExit("[ERROR] %s が見つからない（パッチ適用済み？）" % openai)
        if stt not in mods:
            raise SystemExit("[ERROR] %s が見つからない" % stt)
        # 1. Script モジュール生成（レイアウトは旧 OpenAI の位置を流用）
        body = load_script_body(site["part"], stt, site.get("menu"), site.get("scope"))
        mods[script] = {
            "layout": mods[openai].get("layout", {"x": 0, "y": 0}),
            "next": pad_next(site["next"]),
            "subs": pad_subs([site["save"]] if site.get("save") else []),
            "name": script,
            "description": "",
            "matchingmethod": 1,
            "type": "@General$Script",
            "params": {"module": stt, "script": body},
        }
        # 2. STT の ^.+$ → Script へ付替え
        hit = False
        for nx in mods[stt].get("next", []):
            if nx.get("nextModuleName") == openai:
                nx["nextModuleName"] = script
                hit = True
        if not hit:
            raise SystemExit("[ERROR] %s から %s への next が見つからない" % (stt, openai))
        # 3. OpenAI 削除
        del mods[openai]
        print("[OK] %s -> %s（%s%s）" % (openai, script, site["part"],
                                         ", menu=" + site["menu"] if site.get("menu") else ""))

    # 現在の予約日: STT 直接分岐（生 8 桁が保存値のため Script 不要）
    stt, openai = "入力_現在の予約日", "OpenAI_現在の予約日"
    if openai not in mods:
        raise SystemExit("[ERROR] %s が見つからない（パッチ適用済み？）" % openai)
    hit = False
    for nx in mods[stt].get("next", []):
        if nx.get("nextModuleName") == openai:
            nx["condition"] = "^[0-9]{8}$"
            nx["label"] = "date8"
            nx["nextModuleName"] = "再受診希望"
            hit = True
    if not hit:
        raise SystemExit("[ERROR] %s から %s への next が見つからない" % (stt, openai))
    placed = False
    for nx in mods[stt]["next"]:
        if not nx.get("condition") and not placed:
            nx.update({"condition": "^.+$", "label": "invalid", "nextModuleName": "リトライ_現在の予約日"})
            placed = True
    if not placed:
        raise SystemExit("[ERROR] %s の next に空きスロットがない" % stt)
    del mods[openai]
    print("[OK] %s -> STT直接分岐（^[0-9]{8}$ → 再受診希望 / その他 → リトライ）" % openai)

    # CMR 等の module1Name/module2Name 参照を OpenAI_<step> → Script_<step> へ一括付替え。
    # 施設確定後分岐 だけでなく 終話分岐_遅刻 等、削除した OpenAI を参照する全モジュールが対象
    # （旧版は 施設確定後分岐 のみ手当てし 終話分岐_遅刻 を取りこぼしていた＝leftover 検証で検出）。
    openai_to_script = {"OpenAI_" + s["step"]: "Script_" + s["step"] for s in SITES}
    repointed = []
    for n, m in mods.items():
        params = m.get("params", {})
        for key in ("module1Name", "module2Name"):
            if params.get(key) in openai_to_script:
                old = params[key]
                params[key] = openai_to_script[old]
                repointed.append((n, key, old, params[key]))
    if not repointed:
        raise SystemExit("[ERROR] CMR の OpenAI 参照付替えが0件（施設確定後分岐/終話分岐_遅刻 が想定どおりか確認）")
    for n, key, old, new in repointed:
        print("[OK] %s.%s 参照付替え: %s → %s" % (n, key, old, new))

    # 検証（構造参照のみ。prompt/script 内の説明文は対象外）
    leftovers = []
    for n, m in mods.items():
        if "OpenAI" in n or "OpenAI" in m.get("type", ""):
            leftovers.append(("module:" + n, m.get("type", "")))
        for nx in m.get("next", []):
            if "OpenAI" in (nx.get("nextModuleName") or ""):
                leftovers.append((n + ".next", nx["nextModuleName"]))
        for sb in m.get("subs", []):
            if "OpenAI" in (sb.get("moduleName") or ""):
                leftovers.append((n + ".subs", sb["moduleName"]))
        for k in ("module", "module1Name", "module2Name", "nodeName"):
            if "OpenAI" in str(m.get("params", {}).get(k, "")):
                leftovers.append((n + ".params." + k, m["params"][k]))
    if leftovers:
        for p, v in leftovers:
            print("[LEFTOVER] %s = %s" % (p, v))
        raise SystemExit("[ERROR] メインフローに OpenAI 構造参照が残存（%d 件）" % len(leftovers))
    names = set(mods.keys())
    for n, m in mods.items():
        for nx in m.get("next", []):
            t = nx.get("nextModuleName")
            if t and t not in names:
                raise SystemExit("[ERROR] %s の next 参照先が不存在: %s" % (n, t))
        for sb in m.get("subs", []):
            t = sb.get("moduleName")
            if t and t not in names:
                raise SystemExit("[ERROR] %s の subs 参照先が不存在: %s" % (n, t))
    print("[OK] 検証: OpenAI 残存なし / 参照整合 %d modules" % len(names))
    return flow


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    # 既定はこのチェックアウト配下。worktree 等の別ロケーションを対象にする場合は --src/--dst で上書き
    # （modules/ 正本はこのチェックアウトの MODULES_DIR を常に使用）。
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=SRC_BIVR, help="入力 OpenAI bivr（既定: %s）" % SRC_BIVR)
    ap.add_argument("--dst", default=DST_BIVR, help="出力 deterministic bivr（既定: %s）" % DST_BIVR)
    args = ap.parse_args()
    src_bivr, dst_bivr = args.src, args.dst
    print("入力: %s\n出力: %s\nmodules: %s\n" % (src_bivr, dst_bivr, MODULES_DIR))
    zin = zipfile.ZipFile(src_bivr, "r")
    zout = zipfile.ZipFile(dst_bivr, "w", zipfile.ZIP_DEFLATED)
    patched = 0
    sub_patched = 0
    for info in zin.infolist():
        data = zin.read(info.filename)
        decoded = urllib.parse.unquote(info.filename)
        if decoded.endswith("$統合CC.txt"):
            flow = json.loads(data.decode("utf-8"))
            flow = patch_main(flow)
            data = json.dumps(flow, ensure_ascii=False).encode("utf-8")
            patched += 1
        else:
            for suffix, sites in SUBFLOW_SITES.items():
                if decoded.endswith("$" + suffix + ".txt"):
                    flow = json.loads(data.decode("utf-8"))
                    flow = patch_subflow(flow, sites)
                    verify_flow_no_openai(flow["modules"], suffix)
                    data = json.dumps(flow, ensure_ascii=False).encode("utf-8")
                    sub_patched += 1
                    break
        zout.writestr(info.filename, data)
    zout.close()
    zin.close()
    if patched != 1:
        raise SystemExit("[ERROR] メインフローを %d 件パッチ（期待=1）" % patched)
    if sub_patched != len(SUBFLOW_SITES):
        raise SystemExit("[ERROR] サブフローを %d 件パッチ（期待=%d）" % (sub_patched, len(SUBFLOW_SITES)))
    print("[DONE] %s" % dst_bivr)


if __name__ == "__main__":
    main()
