#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reference_validator.py -- spec ファイル内のパス参照の実在検証

移管ノート / 設計書 YAML / その他 spec ファイル内に書かれた
`元資料:` / `元 bivr:` / `参照:` / `customer_doc:` / `base:` 等のパス参照を抽出し、
実ファイルが存在するかをチェックする。

Why:
    福岡徳洲会病院_リハビリ (2026-04-27) で移管ノートの「元資料」パスが
    実ファイル名と不一致のまま orchestrator が走り、director が customer_doc を
    見つけられず移管ノート自体を「設計書」として qa を通そうとして scaffold で
    破綻した事故が発生。launch_parallel / orchestrator の入口で参照パスの実在を
    一括検証して早期エラー化することで再発を防止する。

Usage:
    python3 scripts/reference_validator.py docs/migration/gen2_xxx.md
    python3 scripts/reference_validator.py output/scenarios/xxx_yyy/設計書_xxx.yaml docs/migration/gen2_yyy.md

Exit:
    0: 全参照 OK
    1: 1件以上の参照不在
"""

import argparse
import re
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

# パス参照を検出する正規表現パターン:
#   キーワード [:：] (空白) <パス> (拡張子)
# 拡張子 .md / .yaml / .yml / .bivr / .json / .txt / .docx を対象
# パス内の半角スペースは customer_docs ファイル名規約違反だがマッチさせる（検証で蹴る）
PATH_REF_PATTERN = re.compile(
    r"(?:元資料|元\s*bivr|参照|customer_doc|base|spec_path|design_spec|migration_note)"
    r"\s*[:：]\s*"
    r"([^\s`'\"]+(?:[ \t][^\s`'\"]+)*?\.(?:md|yaml|yml|bivr|json|txt|docx))"
)


def extract_path_refs(text: str) -> list[tuple[int, str]]:
    """テキストから (line_no, path) のリストを抽出"""
    refs = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in PATH_REF_PATTERN.finditer(line):
            ref = m.group(1).strip()
            refs.append((line_no, ref))
    return refs


def validate_spec(spec_path: Path) -> list[str]:
    """spec ファイルを読み、参照パスの実在を検証。エラー文字列のリストを返す（空なら OK）"""
    if not spec_path.exists():
        return [f"spec ファイル自体が存在しない: {spec_path}"]

    try:
        text = spec_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        return [f"spec ファイル読み込み失敗 (encoding): {spec_path}: {e}"]

    refs = extract_path_refs(text)
    errors = []
    seen = set()
    for line_no, ref_path in refs:
        if ref_path in seen:
            continue
        seen.add(ref_path)
        # 相対パスは PROJECT_DIR 基準で解決
        if Path(ref_path).is_absolute():
            abs_path = Path(ref_path)
        else:
            abs_path = PROJECT_DIR / ref_path
        if not abs_path.exists():
            errors.append(
                f"  L.{line_no}: 参照先ファイルが見つかりません: {ref_path}"
            )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="spec 内パス参照の実在検証")
    parser.add_argument(
        "spec_paths",
        nargs="+",
        help="検証対象の spec ファイル (.md / .yaml / .yml)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="OK 行を出力しない（エラー時のみ出力）",
    )
    args = parser.parse_args()

    has_errors = False
    for sp in args.spec_paths:
        spec_path = Path(sp)
        if not spec_path.is_absolute():
            spec_path = PROJECT_DIR / spec_path

        errors = validate_spec(spec_path)
        if errors:
            has_errors = True
            print(f"[FAIL] {sp}", file=sys.stderr)
            for e in errors:
                print(e, file=sys.stderr)
        elif not args.quiet:
            print(f"[OK] {sp}")

    if has_errors:
        print(
            "\n参照先ファイルが見つかりません。spec のパス記述を実ファイル名に揃えるか、"
            "対象ファイルを所定の場所に配置してください。",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
