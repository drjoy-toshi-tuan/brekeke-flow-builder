#!/usr/bin/env python3
"""
マスターパターン CSV → P7 テストケース JSON 生成ツール

使い方:
  python tools/gen_p7_from_master.py \
      --master docs/testcase_master/master_test_patterns_v3.csv \
      --flow-type 診療 \
      --facility 東京都立豊島病院 \
      --flow-name 診療 \
      --out output/scenarios/東京都立豊島病院_診療/テストケース仕様_東京都立豊島病院_診療_20260709.json
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime


# --- プレースホルダー解決テーブル（施設共通デフォルト）---
# 施設設計書の step_details に値があればそちらを優先する
PLACEHOLDER_DEFAULTS = {
    "{YOYAKU}":          "予約",
    "{HENKOU}":          "変更",
    "{CANCEL}":          "キャンセル",
    "{KAKUNIN}":         "確認",
    "{SONOTA}":          "その他",
    "{YOYAKU_KAKUNIN}":  "予約確認",
    "{K_YOYAKU}":        "予約",
    "{K_HENKOU}":        "変更",
    "{K_CANCEL}":        "キャンセル",
    "{K_TOIAWASE}":      "問い合わせ",
    "{R_SHINSATSU}":     "診察依頼",
    "{R_KENSA}":         "検査依頼",
    "{R_SONOTA}":        "その他",
    "{FAQ_PARKING}":     "駐車場はありますか",
    "{FAQ_BELONGINGS}":  "何を持っていけばいいですか",
    "{FAQ_PAYMENT}":     "クレジットカードは使えますか",
    "{NEXT_MON}":        "来週月曜",
    "{NEXT_TUE}":        "来週火曜",
    "{NEXT_FRI}":        "来週金曜",
    "{THIS_WED}":        "今週水曜",
    "{THIS_FRI}":        "今週金曜",
    "{DEPT_2}":          "内科",
    "{DEPT_3}":          "外科",
    "{TOIAWASE}":        "問い合わせ",
    # ── 以下は施設依存が強い既定値（標準 scaffold の想定）。施設で値が違う場合は
    #    設計書/施設設定側の解決値で上書きすること ──
    "{MENU_1}":          "再診",            # 通院歴メニュー 1=はい(通院あり)
    "{MENU_2}":          "変更",            # 用件メニュー 2 番の標準割当
    "{HENKOU_OTHER}":    "変更",            # 日程以外の変更 → 変更クラスに合流が標準
    "{FAQ_SOGEI}":       "送迎バスはありますか",
    "{FAQ_HOURS}":       "診察時間は何時までですか",
    "NO_RESULT":         "NO_RESULT",
}
# 施設依存のため既定値を持てないプレースホルダー（期待_ 列の分類クラス等）。
# 残存したまま出力すると「{MENU_1} という文字列」を期待値として突合してしまうので
# 生成後に検出して fail-fast する（--facility 側の設計書/設定で解決値を与えること）。

# 入力フィールド（CSV の入力_* カラム群）
INPUT_FIELDS = [
    "入力_用件", "入力_通院歴", "入力_選定療養費", "入力_診療科",
    "入力_生年月日", "入力_患者名", "入力_診察券番号", "入力_連絡先番号",
    "入力_予約希望日", "入力_現在の予約日", "入力_理由", "入力_性別",
    "入力_受診内容", "入力_健保組合名", "入力_企業団体名", "入力_被保険者区分",
    "入力_特例退職者", "入力_希望コース", "入力_オプション", "入力_受診希望時期",
    "入力_緊急性", "入力_紹介目的", "入力_検査項目", "入力_最後の問い合わせ",
]

# 期待値フィールド（CSV の期待_* カラム群）
EXPECT_FIELDS = [
    "期待_用件", "期待_通院歴", "期待_選定療養費", "期待_診療科",
    "期待_生年月日", "期待_患者名", "期待_診察券番号", "期待_連絡先番号",
    "期待_予約希望日", "期待_現在の予約日", "期待_理由", "期待_性別",
    "期待_受診内容", "期待_健保組合名", "期待_企業団体名", "期待_被保険者区分",
    "期待_特例退職者", "期待_希望コース", "期待_オプション", "期待_受診希望時期",
    "期待_緊急性", "期待_紹介目的", "期待_検査項目", "期待_最後の問い合わせ",
]


def resolve_placeholder(value):
    """プレースホルダー（{YOYAKU} 等）を解決する"""
    if not value:
        return value
    return PLACEHOLDER_DEFAULTS.get(value, value)


def load_master(path, flow_type_filter=None):
    """マスター CSV を読み込みフィルタリング済みの行リストを返す"""
    rows = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ft = row.get("flow_type", "").strip()
            if flow_type_filter and ft != flow_type_filter:
                continue
            rows.append(row)
    return rows


def row_to_case(row):
    """CSV 行を P7 ケース dict に変換する"""
    inject = {}
    for field in INPUT_FIELDS:
        val = row.get(field, "").strip()
        if val:
            inject[field] = val

    expect = {}
    for field in EXPECT_FIELDS:
        val = row.get(field, "").strip()
        if val:
            expect[field] = resolve_placeholder(val)

    terminal = row.get("期待_終端", "").strip()

    return {
        "case_id":      row.get("case_id", "").strip(),
        "flow_type":    row.get("flow_type", "").strip(),
        "category":     row.get("category", "").strip(),
        "case_name":    row.get("case_name", "").strip(),
        "inject":       inject,
        "expect":       expect,
        "expect_terminal": terminal,
        "note":         row.get("備考", "").strip(),
    }


def diversity_check(cases):
    """同一フィールドの重複値を検出して警告を返す"""
    warnings = []
    field_values = defaultdict(list)
    for c in cases:
        for field, val in c["inject"].items():
            field_values[field].append((c["case_id"], val))

    skip_fields = {"入力_用件"}  # 用件は多様性チェック除外（Scripts バリエーションを意図的に重複させる場合あり）
    for field, entries in field_values.items():
        if field in skip_fields:
            continue
        from collections import Counter
        cnt = Counter(v for _, v in entries)
        for val, count in cnt.items():
            if count > 1 and val not in ("", "NO_RESULT"):
                ids = [cid for cid, v in entries if v == val]
                warnings.append(
                    f"[WARN] {field}='{val}' が {count} ケースで重複: {ids}"
                )
    return warnings


def generate(master_path, flow_type, facility, flow_name, out_path):
    print(f"Loading: {master_path}", file=sys.stderr)
    rows = load_master(master_path, flow_type_filter=flow_type)
    print(f"  {len(rows)} 行を読み込みました（flow_type={flow_type}）", file=sys.stderr)

    if not rows:
        print("WARNING: 対象行が 0 件です。--flow-type を確認してください。", file=sys.stderr)
        sys.exit(0)

    cases = [row_to_case(r) for r in rows]

    # 未解決プレースホルダー検出（残存すると "{MENU_1}" という文字列を注入/期待してしまう）
    import re as _re
    unresolved = sorted(set(_re.findall(
        r"\{[A-Z_0-9]+\}", json.dumps(cases, ensure_ascii=False))))
    if unresolved:
        print(f"ERROR: 未解決プレースホルダー {len(unresolved)} 種が出力に残ります: {unresolved}",
              file=sys.stderr)
        print("  → PLACEHOLDER_DEFAULTS への追加、または施設側の解決値の指定が必要です。",
              file=sys.stderr)
        sys.exit(1)

    warnings = diversity_check(cases)
    for w in warnings:
        print(w, file=sys.stderr)

    output = {
        "meta": {
            "facility":       facility,
            "flow":           flow_name,
            "generated_from": master_path,
            "flow_type":      flow_type,
            "total_cases":    len(cases),
            "generated_at":   datetime.now().strftime("%Y-%m-%d"),
            "diversity_warnings": len(warnings),
        },
        "cases": cases,
    }

    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"出力: {out_path}  ({len(cases)} ケース, 警告 {len(warnings)} 件)", file=sys.stderr)
    if warnings:
        print("  多様性警告を確認してください（上記 WARN 行）", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="マスターパターン CSV → P7 テストケース JSON")
    parser.add_argument("--master",    required=True, help="マスター CSV ファイルパス")
    parser.add_argument("--flow-type", required=True, help="flow_type フィルター（例: 診療）")
    parser.add_argument("--facility",  required=True, help="施設名（meta に記載）")
    parser.add_argument("--flow-name", required=True, help="フロー名（meta に記載）")
    parser.add_argument("--out",       required=True, help="出力 JSON ファイルパス")
    args = parser.parse_args()

    if not os.path.exists(args.master):
        print(f"ERROR: CSV ファイルが見つかりません: {args.master}", file=sys.stderr)
        sys.exit(1)

    generate(args.master, args.flow_type, args.facility, args.flow_name, args.out)


if __name__ == "__main__":
    main()
