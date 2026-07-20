#!/usr/bin/env python3
"""
gen_phonebook_csv.py — Dr.JOY 電話帳 CSV を設計書 YAML から決定論的に生成する

設計書 YAML の `phonebook` セクション（phonebook.enabled: true）が定義されている場合のみ
output/scenarios/{施設}_{flow}/phonebook_{施設}_{flow}.csv を出力する。
未定義 / enabled: false の場合は何もせず exit 0 (skip)。

LLM 不使用。完全決定論的。

CSV スキーマ（sample_phonebook_相談室.csv 形式）:
    "電話番号","氏名","フリガナ","ブラックリスト","リスト1","リスト2","リスト3","リスト4","リスト5","入電通知"

設計書 YAML 上の phonebook entries:
    phonebook:
      enabled: true
      list_labels: {list1: "薬局カテゴリ", ...}   # ドキュメンテーション目的、CSV には出力されない
      entries:
        - phone_number: "0333205751"             # ハイフン無し国内番号
          name: "クオール薬局"
          furigana: "クオールヤッキョク"           # 元資料に記載がある場合のみ。無ければ空欄
          blacklist: 0
          list1: 1
          list2: 0
          list3: 0
          list4: 0
          list5: 0
          notification: 0

Usage:
    python3 scripts/gen_phonebook_csv.py <yaml_spec_path> [--out <output_path>]

Exit codes:
    0  — CSV を出力した、または phonebook が未定義/disabled なので skip
    1  — YAML 読み取り失敗、entries 不正、CSV 書き込み失敗等の致命エラー
"""

import argparse
import csv
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が必要です（pip install pyyaml）", file=sys.stderr)
    sys.exit(1)

# Windows 環境で UTF-8 出力を強制
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


PROJECT_DIR = Path(__file__).resolve().parent.parent
CSV_HEADER = [
    "電話番号", "氏名", "フリガナ", "ブラックリスト",
    "リスト1", "リスト2", "リスト3", "リスト4", "リスト5",
    "入電通知",
]


def _load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML のトップレベルが dict ではありません: {path}")
    return data


def _resolve_output_path(yaml_path: Path, spec: dict, override: str | None) -> Path:
    """設計書 YAML の basic_info から `output/scenarios/{施設}_{flow}/phonebook_{施設}_{flow}.csv` を決定。

    --out 指定があればそちらを優先する。
    """
    if override:
        return Path(override).resolve()

    basic_info = spec.get("basic_info") or {}
    facility = (basic_info.get("facility_name") or "").strip()
    # scenario_name 優先、無ければ flow_name の '$' 以降
    scenario = (basic_info.get("scenario_name") or "").strip()
    if not scenario:
        flow_name = (basic_info.get("flow_name") or "").strip()
        if "$" in flow_name:
            scenario = flow_name.split("$", 1)[1]
    if not facility or not scenario:
        raise ValueError(
            f"basic_info.facility_name / scenario_name から出力先を決定できません: {yaml_path}"
        )
    return PROJECT_DIR / "output" / "scenarios" / f"{facility}_{scenario}" / f"phonebook_{facility}_{scenario}.csv"


def _coerce_flag(v, default: int = 0) -> int:
    """0/1 を期待する int フラグ。文字列 "0"/"1" や bool も許容する。"""
    if v is None:
        return default
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, int):
        return 1 if v else 0
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y"):
        return 1
    if s in ("", "0", "false", "no", "n"):
        return 0
    raise ValueError(f"不正なフラグ値: {v!r}")


def _normalize_phone(s) -> str:
    """ハイフン・全角数字・スペース等を除去して半角数字のみに正規化する。

    Dr.JOY 電話帳 CSV はハイフン無し国内番号（例: "0333205751"）。
    """
    if s is None:
        return ""
    t = str(s).strip()
    # 全角 → 半角
    t = t.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    # ハイフン・スペース・各種区切り除去
    for c in "-‐‑‒–—－ 　":
        t = t.replace(c, "")
    return t


def _validate_entry(entry: dict, idx: int) -> tuple[str, str, str, int, int, int, int, int, int, int]:
    """1 entry を CSV 行のタプルに変換。検証エラー時は ValueError。"""
    phone = _normalize_phone(entry.get("phone_number", ""))
    name = str(entry.get("name", "") or "").strip()
    furigana = str(entry.get("furigana", "") or "").strip()
    blacklist = _coerce_flag(entry.get("blacklist"))
    list1 = _coerce_flag(entry.get("list1"))
    list2 = _coerce_flag(entry.get("list2"))
    list3 = _coerce_flag(entry.get("list3"))
    list4 = _coerce_flag(entry.get("list4"))
    list5 = _coerce_flag(entry.get("list5"))
    notification = _coerce_flag(entry.get("notification"))

    if not phone:
        raise ValueError(f"entry[{idx}]: phone_number が空")
    if not phone.isdigit():
        raise ValueError(f"entry[{idx}]: phone_number は数字のみであるべき (got {phone!r})")
    if not name:
        raise ValueError(f"entry[{idx}]: name が空")
    # フリガナは空欄許容（元資料に無い場合）

    return (phone, name, furigana, blacklist, list1, list2, list3, list4, list5, notification)


def generate_csv(yaml_path: Path, out_path: Path) -> tuple[bool, str]:
    """設計書 YAML を読んで CSV を生成する。

    Returns:
        (wrote, message):
          wrote=True  → CSV を書き出した（行数を message に）
          wrote=False → phonebook 未定義 / disabled で skip（理由を message に）
    """
    spec = _load_yaml(yaml_path)
    pb = spec.get("phonebook")
    if not isinstance(pb, dict):
        return False, "phonebook セクション未定義 (skip)"
    if not _coerce_flag(pb.get("enabled")):
        return False, "phonebook.enabled が false (skip)"
    entries = pb.get("entries") or []
    if not isinstance(entries, list) or not entries:
        raise ValueError("phonebook.enabled=true だが entries が空")

    rows = []
    for i, e in enumerate(entries):
        if not isinstance(e, dict):
            raise ValueError(f"phonebook.entries[{i}] が dict ではありません")
        rows.append(_validate_entry(e, i))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    # quoting=csv.QUOTE_ALL で全フィールド ダブルクォート（sample 形式に合わせる）
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)

    return True, f"{len(rows)} entry → {out_path.relative_to(PROJECT_DIR) if out_path.is_absolute() else out_path}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Dr.JOY 電話帳 CSV 生成 (sample_phonebook_相談室.csv 形式)")
    parser.add_argument("yaml_spec", help="設計書 YAML パス")
    parser.add_argument("--out", default=None, help="出力 CSV パス (省略時は output/scenarios/{施設}_{flow}/phonebook_{施設}_{flow}.csv)")
    args = parser.parse_args()

    yaml_path = Path(args.yaml_spec).resolve()
    if not yaml_path.exists():
        print(f"ERROR: 設計書 YAML が見つかりません: {yaml_path}", file=sys.stderr)
        return 1

    try:
        spec = _load_yaml(yaml_path)
        out_path = _resolve_output_path(yaml_path, spec, args.out)
    except Exception as e:
        print(f"ERROR: 出力先解決に失敗: {e}", file=sys.stderr)
        return 1

    try:
        wrote, msg = generate_csv(yaml_path, out_path)
    except Exception as e:
        print(f"ERROR: CSV 生成失敗: {e}", file=sys.stderr)
        return 1

    print(("OK" if wrote else "SKIP") + ": " + msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
