#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_cases_from_master.py — master_test_patterns_v3.csv × hospital_config → cases/*.json

Usage:
  python3 connection_test/gen_cases_from_master.py \
      --master  docs/testcase_master/master_test_patterns_v3.csv \
      --config  connection_test/hospital_configs/福岡大学_診療.json \
      --out     connection_test/cases/福岡大学_診療_master.json \
      [--add-missing]   # マスターに不足ケースを追記する

マスターCSV の列体系:
  case_id, flow_type, category, case_name
  入力_XXX / 期待_XXX   ... 汎用フィールド名
  期待_終端, 備考

施設コンフィグ (JSON) で指定:
  flow_type_filter   : 抽出する flow_type リスト (例: ["診療","共通"])
  exclude_ids        : スキップする case_id リスト
  column_map         : マスター列名 → 施設固有ノード名 のリネーム辞書
  placeholders       : {XXX} → 実値 の展開辞書
  terminal_map       : 期待_終端の日本語 → cases JSON 用文字列
  checkpoint_hints   : case_id → 追加チェックポイントリスト
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path


# ── stub 用 defaults の標準ブロック ────────────────────────────────────────────
# stub_stt_connection.py はケースが inject しないノードに対して defaults を参照する
# （node 名に _order のキーワードが含まれれば先頭一致を採用、無ければ _fallback）。
# hospital_config の "defaults" キーで施設ごとに上書き・追加できる。
STANDARD_DEFAULTS = {
    "_about": ("サブフローSTTの既定注入値(完走させるための最善推定)。"
               "ゴールデンログ観察後に調整。node名にキーワードが含まれれば _order の先頭一致を採用。"),
    "_order": ["復唱", "確認", "用件", "診療科", "診察券", "患者", "氏名",
               "生年月日", "連絡先", "予約日", "希望日", "問い合わせ"],
    "復唱":       ["はい"],
    "確認":       ["はい"],
    "用件":       ["予約"],
    "診療科":     ["内科"],
    "診察券":     ["1234567"],
    "患者":       ["山田太郎"],
    "氏名":       ["山田太郎"],
    "生年月日":   ["19800101"],
    "連絡先":     ["09000000001"],
    "予約日":     ["7月20日"],
    "希望日":     ["来週の月曜日"],
    "問い合わせ": ["NO_RESULT"],
    "_fallback":  ["NO_RESULT"],
}

# 入力セル内の複数トライ区切り文字。
# 例: "いくらかかるんですか|はい大丈夫です" → 1回目 NG → リトライで OK
# （stub の attempt-aware injection がリスト順に注入する）。
ATTEMPT_SEPARATOR = "|"


# ── プレースホルダ展開 ─────────────────────────────────────────────────────────

def resolve_placeholder(value: str, ph_map: dict[str, str]) -> str:
    """'{YOYAKU}' → '予約' などプレースホルダを実値に変換。複数あれば順に置換。"""
    for token, real in ph_map.items():
        value = value.replace(token, real)
    return value


def resolve_all(value: str, ph_map: dict[str, str]) -> str:
    resolved = resolve_placeholder(value, ph_map)
    # 未解決プレースホルダが残っていれば空扱いにする
    if re.search(r'\{[A-Z_0-9]+\}', resolved):
        return ""
    return resolved


# ── マスター CSV 行 → case dict ───────────────────────────────────────────────

INPUT_PREFIX  = "入力_"
EXPECT_PREFIX = "期待_"

FIXED_COLS = {"case_id", "flow_type", "category", "case_name", "期待_終端", "備考"}


def row_to_case(
    row: dict,
    dtmf: str,
    column_map: dict[str, str],
    placeholders: dict[str, str],
    terminal_map: dict[str, str],
    checkpoint_hints: dict[str, list[str]],
) -> dict:
    case_id   = row["case_id"].strip()
    case_name = row["case_name"].strip()
    category  = row["category"].strip()

    inject: dict[str, list[str]] = {}
    for col, raw_val in row.items():
        if not col.startswith(INPUT_PREFIX):
            continue
        raw_val = raw_val.strip()
        if not raw_val:
            continue
        # 複数トライ区切り: "NG発話|OK発話" → attempt ごとのリスト
        attempts = []
        for part in raw_val.split(ATTEMPT_SEPARATOR):
            resolved = resolve_all(part.strip(), placeholders)
            if resolved:
                attempts.append(resolved)
        if not attempts:
            continue
        # リネーム
        mapped_col = column_map.get(col, col)
        inject[mapped_col] = attempts

    # 期待_終端
    raw_terminal = row.get("期待_終端", "").strip()
    raw_terminal = resolve_all(raw_terminal, placeholders) or raw_terminal
    terminal = terminal_map.get(raw_terminal, raw_terminal) if raw_terminal else "ログ観察"

    # チェックポイント
    checkpoints = list(checkpoint_hints.get(case_id, []))

    return {
        "id":       case_id,
        "dtmf":     dtmf,
        "label":    f"[{category}] {case_name}",
        "_source":  "master_csv",
        "inject":   inject,
        "expect": {
            "終端":        terminal,
            "checkpoints": checkpoints,
        },
        "備考": row.get("備考", "").strip(),
    }


# ── 不足ケース検出 ─────────────────────────────────────────────────────────────

def detect_missing(
    master_rows: list[dict],
    flow_types: list[str],
    exclude_ids: set[str],
) -> list[str]:
    """マスターに存在しない flow_type パターンを報告する（拡張用）"""
    present_categories = {
        r["category"]
        for r in master_rows
        if (not flow_types or r["flow_type"] in flow_types)
        and r["case_id"] not in exclude_ids
    }
    # 最低限あるべきカテゴリ（拡張可能）
    required = {"正常_予約", "正常_変更", "正常_キャンセル", "エラー", "システム"}
    missing = sorted(required - present_categories)
    return missing


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="master CSV × hospital config → cases JSON")
    ap.add_argument("--master",      required=True, help="master_test_patterns_*.csv")
    ap.add_argument("--config",      required=True, help="hospital_configs/XXX.json")
    ap.add_argument("--out",         required=True, help="output cases JSON path")
    ap.add_argument("--add-missing", action="store_true",
                    help="不足カテゴリをレポートして終了 (実際の追記は人間が行う)")
    args = ap.parse_args()

    master_path = Path(args.master)
    config_path = Path(args.config)
    out_path    = Path(args.out)

    if not master_path.exists():
        print(f"[ERROR] master CSV not found: {master_path}", file=sys.stderr)
        return 1
    if not config_path.exists():
        print(f"[ERROR] config JSON not found: {config_path}", file=sys.stderr)
        return 1

    cfg = json.loads(config_path.read_text(encoding="utf-8"))

    flow_types      = cfg.get("flow_type_filter", [])
    exclude_ids     = set(cfg.get("exclude_ids", []))
    column_map      = cfg.get("column_map", {})
    placeholders    = cfg.get("placeholders", {})
    terminal_map    = cfg.get("terminal_map", {})
    checkpoint_hints = cfg.get("checkpoint_hints", {})

    # マスター読み込み
    with master_path.open(encoding="utf-8-sig", newline="") as f:
        master_rows = list(csv.DictReader(f))

    # 不足チェック
    missing_cats = detect_missing(master_rows, flow_types, exclude_ids)
    if missing_cats:
        print(f"[WARN] マスターに不足カテゴリ: {missing_cats}", file=sys.stderr)

    if args.add_missing:
        print("--add-missing: 不足カテゴリを人間がマスターに追記してください:")
        for cat in missing_cats:
            print(f"  - {cat}")
        return 0 if not missing_cats else 2

    # フィルタ
    filtered = [
        r for r in master_rows
        if (not flow_types or r["flow_type"] in flow_types)
        and r["case_id"].strip() not in exclude_ids
        and r["case_id"].strip()
    ]

    # dtmf は 1 始まりの連番（発信時に「ケース番号+#」で選択するコード）
    cases = [
        row_to_case(r, str(i + 1), column_map, placeholders, terminal_map, checkpoint_hints)
        for i, r in enumerate(filtered)
    ]

    # 品質ガード 1: inject が空のケース（沈黙/システム系）は STT スタブでは表現できず
    # defaults で普通に完走してしまう＝「テストしたつもり」になる。明示タグ + 警告。
    empty_inject = [c for c in cases if not c["inject"]]
    for c in empty_inject:
        c["_warning"] = ("inject なし: 全ノード defaults 動作。沈黙/非通知/時間外系は "
                         "STT スタブで表現不可のため実機マニュアル確認が必要")
    if empty_inject:
        print(f"[WARN] inject 空ケース {len(empty_inject)} 件（スタブでは沈黙/システム系を再現できません）:",
              file=sys.stderr)
        for c in empty_inject:
            print(f"   {c['id']} {c['label']}", file=sys.stderr)

    # 品質ガード 2: 未解決プレースホルダー（config の placeholders に無い {XXX}）は
    # そのまま注入/期待値になってしまうため fail-fast。
    unresolved = sorted(set(re.findall(r"\{[A-Z_0-9]+\}", json.dumps(cases, ensure_ascii=False))))
    if unresolved:
        print(f"[ERROR] 未解決プレースホルダー {len(unresolved)} 種: {unresolved}", file=sys.stderr)
        print(f"   → {config_path.name} の placeholders に解決値を追加してください。", file=sys.stderr)
        return 1

    # defaults: 標準ブロック + 施設コンフィグの "defaults" で上書き・追加。
    # config が _order にキーを追加した場合はそのまま尊重、無ければ標準順。
    defaults = dict(STANDARD_DEFAULTS)
    cfg_defaults = cfg.get("defaults", {})
    for k, v in cfg_defaults.items():
        defaults[k] = v
    # config が新キーワードを足したのに _order に載せ忘れた場合は末尾に補完
    for k in cfg_defaults:
        if not k.startswith("_") and k not in defaults["_order"]:
            defaults["_order"] = list(defaults["_order"]) + [k]

    # meta
    meta = {
        "facility":   cfg.get("facility", ""),
        "flow":       cfg.get("flow", ""),
        "entry_flow": cfg.get("entry_flow", ""),
        "_master":    master_path.name,
        "_config":    config_path.name,
    }

    output = {
        "_about": f"cases generated from master × {config_path.name}",
        "meta":   meta,
        "selector": {"context": "__tc_id", "module": "__テストセレクタ",
                     "usage": "発信→ケース番号+#"},
        "defaults": defaults,
        "cases":  cases,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(cases)} cases ({len(flow_types) and ','.join(flow_types) or 'all'}) → {out_path}")
    if missing_cats:
        print(f"[WARN] 以下のカテゴリがマスターにありません（追記推奨）: {missing_cats}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
