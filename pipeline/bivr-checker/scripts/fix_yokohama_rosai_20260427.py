#!/usr/bin/env python3
"""
横浜労災病院 20260427 フロー順序修正スクリプト

人間FBに基づく4件の修正:
  FB①: 予約パス — 診療科を先に聴取し、グループ3/4のみ紹介状確認
  FB②: 変更パス — 診療科を先に聴取してから現在の予約日→当日確認→変更理由
  FB③: キャンセルパス — 変更と共有せず独立フロー（診療科→現在の予約日→終話④）
  FB④: 確認パス — 診療科を追加してから確認内容

実装方針:
  - ContextMatchRouter_用件: 全4パスの遷移先を診療科モジュールに変更
  - 予約パス: 診療科→グループ分岐→[グループ3/4]→紹介状確認→あり:紹介元/なし:ContextMatchRouter判定
  - 変更/キャンセル/確認パス: 診療科_変更を共有→ContextMatchRouterで分岐
  - 当日確認(いいえ): 診療科→変更理由 から 直接→変更理由 に変更（診療科は前で聴取済み）
"""

import json
import sys
import copy

sys.stdout.reconfigure(encoding='utf-8')

INPUT = "output/横浜労災_20260427/横浜労災_診療_20260403_3.json"
OUTPUT = "output/横浜労災_20260427/横浜労災_診療_20260403_3.json"

# --- ContextMatchRouter テンプレート ---
CMR_TYPE = "drjoy^Context Logic$ContextMatchRouter"

def make_cmr(name, ref_module, values, routes, default_route="", layout_x=0, layout_y=0):
    """ContextMatchRouter モジュールを生成する"""
    params = {
        "module1Name": ref_module,
        "module2Name": ref_module,
    }
    for i in range(1, 11):
        v = values[i - 1] if i <= len(values) else ""
        params[f"module1Value{i}"] = v
        params[f"module2Value{i}"] = v

    # params を交互配置に並び替え
    ordered = {}
    ordered["module1Name"] = params["module1Name"]
    ordered["module2Name"] = params["module2Name"]
    for i in range(1, 11):
        ordered[f"module1Value{i}"] = params[f"module1Value{i}"]
        ordered[f"module2Value{i}"] = params[f"module2Value{i}"]

    next_arr = []
    for i, (cond, label, target) in enumerate(routes):
        next_arr.append({"condition": cond, "label": label, "nextModuleName": target})
    # default
    if default_route:
        next_arr.append({"condition": "^.*$", "label": "default", "nextModuleName": default_route})
    # 空スロットで10まで埋める
    while len(next_arr) < 10:
        next_arr.append({"condition": "", "label": "", "nextModuleName": ""})

    subs = [{"moduleName": "", "label": ""} for _ in range(3)]

    return {
        "layout": {"x": layout_x, "y": layout_y},
        "next": next_arr,
        "subs": subs,
        "name": name,
        "description": "",
        "matchingmethod": 1,
        "type": CMR_TYPE,
        "params": ordered,
    }


def main():
    with open(INPUT, encoding="utf-8") as f:
        flow = json.load(f)

    modules = flow["modules"]
    changes = []

    # ============================================================
    # 1. ContextMatchRouter_用件: 全4パスの遷移先を診療科モジュールに変更
    # ============================================================
    cmr_youken = modules["ContextMatchRouter_用件"]
    for nx in cmr_youken["next"]:
        if nx.get("condition") == "^1$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "診療科_予約"
            changes.append(f"ContextMatchRouter_用件 ^1$(予約): {old} → 診療科_予約")
        elif nx.get("condition") == "^2$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "診療科_変更"
            changes.append(f"ContextMatchRouter_用件 ^2$(変更): {old} → 診療科_変更")
        elif nx.get("condition") == "^3$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "診療科_変更"
            changes.append(f"ContextMatchRouter_用件 ^3$(キャンセル): {old} → 診療科_変更")
        elif nx.get("condition") == "^4$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "診療科_変更"
            changes.append(f"ContextMatchRouter_用件 ^4$(確認): {old} → 診療科_変更")
        elif nx.get("condition") == "^.*$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "診療科_予約"
            changes.append(f"ContextMatchRouter_用件 default: {old} → 診療科_予約")

    # ============================================================
    # 2. 予約パス: 診療科→グループ分岐→紹介状確認（グループ3/4のみ）
    # ============================================================
    # OpenAI_診療科_予約: グループ3/4 → 紹介状確認 に変更（紹介元→紹介状確認）
    oai_shinryo_yoyaku = modules["OpenAI_診療科_予約"]
    for nx in oai_shinryo_yoyaku["next"]:
        if nx.get("condition") == "^グループ3$" and nx["nextModuleName"] == "紹介元":
            nx["nextModuleName"] = "紹介状確認"
            changes.append("OpenAI_診療科_予約 グループ3: 紹介元 → 紹介状確認")
        elif nx.get("condition") == "^グループ4$" and nx["nextModuleName"] == "紹介元":
            nx["nextModuleName"] = "紹介状確認"
            changes.append("OpenAI_診療科_予約 グループ4: 紹介元 → 紹介状確認")

    # saveCtx_紹介状_あり: 診療科_予約 → 紹介元（診療科は既に聴取済み）
    ctx_ari = modules["saveCtx_紹介状_あり"]
    for nx in ctx_ari["next"]:
        if nx.get("nextModuleName") == "診療科_予約":
            nx["nextModuleName"] = "紹介元"
            changes.append("saveCtx_紹介状_あり: 診療科_予約 → 紹介元")

    # saveCtx_紹介状_なし: 診療科_紹介なし → ContextMatchRouter_紹介なし（新規）
    ctx_nashi = modules["saveCtx_紹介状_なし"]
    for nx in ctx_nashi["next"]:
        if nx.get("nextModuleName") == "診療科_紹介なし":
            nx["nextModuleName"] = "ContextMatchRouter_紹介なし"
            changes.append("saveCtx_紹介状_なし: 診療科_紹介なし → ContextMatchRouter_紹介なし")

    # 新規: ContextMatchRouter_紹介なし
    # OpenAI_診療科_予約 の出力（グループ3/グループ4）で分岐
    # グループ3 + 紹介なし → 終話③
    # グループ4 + 紹介なし → 選定療養費 → 終話④
    # 紹介状確認のレイアウト付近に配置
    shoukai_layout = modules["紹介状確認"]["layout"]
    modules["ContextMatchRouter_紹介なし"] = make_cmr(
        name="ContextMatchRouter_紹介なし",
        ref_module="OpenAI_診療科_予約",
        values=["グループ3", "グループ4"],
        routes=[
            ("^1$", "グループ3", "完了フラグ_終話3"),
            ("^2$", "グループ4", "選定療養費_説明"),
        ],
        default_route="完了フラグ_終話3",
        layout_x=shoukai_layout["x"] + 600,
        layout_y=shoukai_layout["y"] + 300,
    )
    changes.append("CREATE ContextMatchRouter_紹介なし (グループ3→終話3, グループ4→選定療養費)")

    # ============================================================
    # 3. 変更/キャンセル/確認パス: 診療科_変更を共有→ContextMatchRouterで分岐
    # ============================================================
    # OpenAI_復唱_診療科_変更: 肯定 → ContextMatchRouter_診療科後（新規）
    oai_fukusho_shinryo = modules["OpenAI_復唱_診療科_変更"]
    for nx in oai_fukusho_shinryo["next"]:
        if nx.get("condition") == "^肯定$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "ContextMatchRouter_診療科後"
            changes.append(f"OpenAI_復唱_診療科_変更 肯定: {old} → ContextMatchRouter_診療科後")

    # 新規: ContextMatchRouter_診療科後
    # OpenAI_用件 の出力で分岐
    # 変更 → 現在の予約日
    # キャンセル → 現在の予約日
    # 確認 → 確認内容
    shinryo_henkou_layout = modules["診療科_変更"]["layout"]
    modules["ContextMatchRouter_診療科後"] = make_cmr(
        name="ContextMatchRouter_診療科後",
        ref_module="OpenAI_用件",
        values=["予約変更", "キャンセル", "予約確認"],
        routes=[
            ("^1$", "予約変更", "現在の予約日"),
            ("^2$", "キャンセル", "現在の予約日"),
            ("^3$", "予約確認", "確認内容"),
        ],
        default_route="現在の予約日",
        layout_x=shinryo_henkou_layout["x"] + 600,
        layout_y=shinryo_henkou_layout["y"] + 500,
    )
    changes.append("CREATE ContextMatchRouter_診療科後 (変更→予約日, キャンセル→予約日, 確認→確認内容)")

    # ============================================================
    # 4. キャンセルパス: 復唱_現在の予約日 肯定 → ContextMatchRouter_予約日後（新規）
    # ============================================================
    oai_fukusho_yoyakubi = modules["OpenAI_復唱_現在の予約日"]
    for nx in oai_fukusho_yoyakubi["next"]:
        if nx.get("condition") == "^肯定$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "ContextMatchRouter_予約日後"
            changes.append(f"OpenAI_復唱_現在の予約日 肯定: {old} → ContextMatchRouter_予約日後")

    # 新規: ContextMatchRouter_予約日後
    # OpenAI_用件 の出力で分岐
    # 変更 → 当日確認
    # キャンセル → 着信分類_SMS判定（終話④ルート直行）
    yoyakubi_layout = modules["現在の予約日"]["layout"]
    modules["ContextMatchRouter_予約日後"] = make_cmr(
        name="ContextMatchRouter_予約日後",
        ref_module="OpenAI_用件",
        values=["予約変更", "キャンセル"],
        routes=[
            ("^1$", "予約変更", "当日確認"),
            ("^2$", "キャンセル", "着信分類_SMS判定"),
        ],
        default_route="当日確認",
        layout_x=yoyakubi_layout["x"] + 600,
        layout_y=yoyakubi_layout["y"] + 500,
    )
    changes.append("CREATE ContextMatchRouter_予約日後 (変更→当日確認, キャンセル→SMS判定)")

    # ============================================================
    # 5. 当日確認(いいえ): 診療科_変更 → 変更理由（診療科は前で聴取済み）
    # ============================================================
    oai_toujitsu = modules["OpenAI_当日確認"]
    for nx in oai_toujitsu["next"]:
        if nx.get("condition") == "^いいえ$":
            old = nx["nextModuleName"]
            nx["nextModuleName"] = "変更理由"
            changes.append(f"OpenAI_当日確認 いいえ: {old} → 変更理由")

    # ============================================================
    # 保存
    # ============================================================
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"=== 修正完了: {len(changes)} 件 ===")
    for c in changes:
        print(f"  [FIX] {c}")
    print(f"\n出力: {OUTPUT}")
    print(f"モジュール数: {len(modules)}")


if __name__ == "__main__":
    main()
