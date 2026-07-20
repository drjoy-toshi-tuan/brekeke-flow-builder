#!/usr/bin/env python3
"""
copy_subflows.py -- サブフロー静的JSONをサンプルからコピーし、施設名・日付でリネームする

設計書YAMLの flow_structure.subflows[] と rag_subflow.pattern を読み取り、
docs/reference/bivr/samples/json/ から該当サンプルJSONをコピーして
output/json/draft_{施設名}_{サブフロー名}.json として出力する。

JSON内の "name" フィールドを "{group_name}${target}" に書き換える。
日付サフィックスは group_name 側に含まれる前提（命名規則 2026-06-04 確定,
docs/brekeke/naming_convention.md）。サブフロー名・フロー名には日付を付けない。
これにより director の flowname 参照（group_name verbatim）とサブフロー JSON 名が
完全一致し、broken_ref を構造的に防ぐ。

orchestrator.py から qa ステップ通過後に自動呼び出しされる。
手動実行も可能:
    python3 scripts/copy_subflows.py --spec output/scenarios/xxx_yyy/設計書_xxx.yaml
    python3 scripts/copy_subflows.py --spec output/scenarios/xxx_yyy/設計書_xxx.yaml --date 20260409
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = PROJECT_DIR / "docs" / "reference" / "bivr" / "samples" / "json"

# target名 → (サンプルJSONファイル名テンプレート, 復唱フラグが必要か)
# 復唱フラグが必要なもの: template に {recitation} プレースホルダーを使う
SUBFLOW_MAP = {
    "氏名聴取":      ("氏名聴取.json",                        False),
    "生年月日聴取":   ("生年月日聴取_復唱{recitation}.json",   True),
    "電話番号聴取":   ("電話番号聴取.json",                    False),   # 2026-07-08: 単一テンプレ（復唱あり/なし統合済み）
    "用件聴取":       ("用件聴取_復唱{recitation}.json",       True),    # 2026-07-08: 用件_区分聴取（復唱あり/なし）
    "診察券番号聴取": ("診察券番号聴取.json",                   False),
    # 2026-07-08: FAQ照合サブフロー（TTS→STT→OpenAI→Script→DB保存→TTS回答）
    "問い合わせ":     ("FAQ照合.json",                         False),
    "内容確認":       ("FAQ照合.json",                         False),
    "その他の質問":   ("FAQ照合.json",                         False),
    "確認事項":       ("FAQ照合.json",                         False),
    "最後の質問":     ("FAQ照合.json",                         False),
}

# 「個人情報聴取」wrapper target は 4 つの個別サブフローに展開する。
# 設計書が抽象的な単一subflow（"個人情報聴取（...）"）で書かれている場合の対応。
# 順序: 診察券番号 → 氏名 → 生年月日 → 電話番号
PERSONAL_INFO_WRAPPER_TARGETS = [
    "診察券番号聴取", "氏名聴取", "生年月日聴取", "電話番号聴取",
]


def _is_personal_info_wrapper(target: str) -> bool:
    """target名が「個人情報聴取」wrapper パターンか判定
    例: "個人情報聴取", "個人情報聴取（診察券番号・氏名・生年月日・電話番号）"
    個別target（"氏名聴取"等）は False。
    """
    t = target.strip()
    return t.startswith("個人情報聴取") and t not in SUBFLOW_MAP


def _normalize_target(target: str) -> tuple[str, str | None]:
    """target から `_復唱あり` / `_復唱なし` suffix を剥がして正規化する

    director が `target: "生年月日聴取_復唱あり"` と suffix 付きで書いた場合でも
    SUBFLOW_MAP キーに当たるよう、suffix を剥がしたキーと取り出した recitation 値を返す。
    suffix が無ければ (target, None) を返す。

    戻り値: (normalized_target, recitation)
    """
    for recitation in ("あり", "なし"):
        suffix = f"_復唱{recitation}"
        if target.endswith(suffix):
            return target[: -len(suffix)], recitation
    return target, None


def _copy_subflow(sample_path: Path, dest_path: Path, new_name: str) -> None:
    """サンプルJSONをコピーし name フィールドを書き換える"""
    with open(sample_path, encoding="utf-8") as f:
        data = json.load(f)
    data["name"] = new_name
    with open(dest_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="サブフロー静的JSONコピーツール")
    parser.add_argument("--spec", required=True, help="設計書YAMLパス（プロジェクトルートからの相対パスまたは絶対パス）")
    parser.add_argument("--date", default=datetime.now().strftime("%Y%m%d"),
                        help="[非推奨] 日付サフィックス。命名規則変更（2026-06-04）により日付は "
                             "group_name 側に含めるためサブフロー名には付与しない。後方互換のため引数は受理するが命名には不使用")
    parser.add_argument("--output-dir", default=None, help="出力先ディレクトリ（デフォルト: output/json/）")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = PROJECT_DIR / spec_path
    if not spec_path.exists():
        print(f"[ERROR] 設計書が見つかりません: {spec_path}", file=sys.stderr)
        return 1

    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    basic = spec.get("basic_info", {})
    facility = basic.get("facility_name", "").strip()
    group_name = basic.get("group_name", "").strip()

    if not facility:
        print("[ERROR] 設計書の basic_info.facility_name が空です", file=sys.stderr)
        return 1
    if not group_name:
        print("[ERROR] 設計書の basic_info.group_name が空です", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir) if args.output_dir else PROJECT_DIR / "output" / "json"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 命名規則（2026-06-04）: 日付サフィックスは group_name 側に持つ。
    # group_name が `_YYYYMMDD` で終わっていない場合は版管理されていないので注意喚起のみ
    # （ブロックはしない。pipeline では qa_validator E-16 が CRITICAL 検出する）。
    import re as _re
    if not _re.search(r"_\d{8}$", group_name):
        print(f"[WARN] group_name '{group_name}' に日付サフィックス '_YYYYMMDD' がありません。"
              f"コピー作成・修正時は group_name 末尾に作業日を付けて版管理してください "
              f"(naming_convention.md / qa_validator E-16)")

    subflows = spec.get("flow_structure", {}).get("subflows", []) or []
    rag_pattern = spec.get("rag_subflow", {}).get("pattern", "none")

    copied = []
    errors = []

    def _copy_one(target: str, recitation_override: str | None = None) -> None:
        """1つの個別サブフロー target をコピー（エラーは外側の errors/copied に追記）"""
        template_name, needs_recitation = SUBFLOW_MAP[target]
        if needs_recitation:
            recitation = (recitation_override or "あり").strip()
            if recitation not in ("あり", "なし"):
                print(f"[WARN] {target}: recitation='{recitation}' は不正値（あり | なし）。'あり' を使用します")
                recitation = "あり"
            sample_filename = template_name.format(recitation=recitation)
        else:
            sample_filename = template_name

        sample_path = SAMPLES_DIR / sample_filename
        if not sample_path.exists():
            msg = f"[ERROR] サンプルJSONが存在しません: {sample_path}"
            print(msg, file=sys.stderr)
            errors.append(msg)
            return

        dest_path = output_dir / f"draft_{facility}_{target}.json"
        new_name = f"{group_name}${target}"
        _copy_subflow(sample_path, dest_path, new_name)
        copied.append(dest_path.name)
        print(f"[OK] {target}: {sample_filename} → {dest_path.name}  (name={new_name})")

    # --- 個人情報聴取サブフロー ---
    for sf in subflows:
        target = (sf.get("target") or "").strip()
        if not target:
            continue

        # 「個人情報聴取」wrapper は 4 つの個別サブフローに展開
        if _is_personal_info_wrapper(target):
            print(f"[INFO] wrapper target '{target}' を 4 つの個別サブフローに展開します")
            recitation = sf.get("recitation")  # 指定があれば 復唱あり/なし を各サブフローに伝搬
            for sub_target in PERSONAL_INFO_WRAPPER_TARGETS:
                _copy_one(sub_target, recitation_override=recitation)
            continue

        # `_復唱あり` / `_復唱なし` suffix を剥がして正規化
        normalized_target, suffix_recitation = _normalize_target(target)

        if normalized_target not in SUBFLOW_MAP:
            # 氏名聴取を含む未知 target は PatientName サブフロー誤登録の可能性が高い
            # (入電者氏名聴取 / 受診者氏名聴取 / 担当者氏名聴取 等は hearing ブロック扱い)
            if "氏名聴取" in normalized_target:
                msg = (f"[ERROR] 未知の氏名聴取系サブフロー target: '{target}'。"
                       f"PatientName サブフローは '氏名聴取' 1 本のみ。"
                       f"入電者氏名・受診者氏名・担当者氏名等は hearing ブロックで対応してください "
                       f"(docs/brekeke/モジュール選定ガイド_v2.md §3.1.1)")
                print(msg, file=sys.stderr)
                errors.append(msg)
                continue
            print(f"[WARN] 未知のサブフロー target: '{target}' -- スキップ（RAG検索は rag_subflow.pattern で制御）")
            continue

        # YAML の recitation フィールドを最優先、なければ target suffix から取り出した値
        recitation_override = sf.get("recitation") or suffix_recitation
        _copy_one(normalized_target, recitation_override=recitation_override)

    # --- RAGサブフロー ---
    if rag_pattern != "none":
        sample_path = SAMPLES_DIR / "RAG検索.json"
        if not sample_path.exists():
            msg = f"[ERROR] RAG検索.json が存在しません: {sample_path}"
            print(msg, file=sys.stderr)
            errors.append(msg)
        else:
            dest_path = output_dir / f"draft_{facility}_RAG検索.json"
            new_name = f"{group_name}$RAG検索"
            _copy_subflow(sample_path, dest_path, new_name)
            copied.append(dest_path.name)
            print(f"[OK] RAG検索 (pattern={rag_pattern}): RAG検索.json → {dest_path.name}  (name={new_name})")

    if errors:
        print(f"\n[FAILED] {len(errors)} 件のエラーが発生しました", file=sys.stderr)
        return 1

    if not copied:
        print("[INFO] コピー対象のサブフローなし（設計書にサブフロー定義がなく RAG も none）")
    else:
        print(f"\n[完了] {len(copied)} 件のサブフローJSONをコピーしました: {', '.join(copied)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
