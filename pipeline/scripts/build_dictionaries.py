#!/usr/bin/env python3
"""build_dictionaries.py -- 辞書テキストから派生ファイルを再生成する。

SSoT は docs/reference/dictionaries/*.txt。本スクリプトはこれを読んで:
  1. docs/specs/stt_dictionary_templates.json の各テンプレ "words" を更新
  2. docs/reference/bivr/samples/json/氏名聴取.json の入力_患者_氏名.profile_words を更新

辞書を編集したい場合は docs/reference/dictionaries/*.txt を Edit/Write した後に
本スクリプトを実行する。

Usage:
    python3 scripts/build_dictionaries.py
    python3 scripts/build_dictionaries.py --dry-run

Exit code: 0 (no changes / changes applied), 1 (error / missing txt)
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DICT_DIR = ROOT / "docs" / "reference" / "dictionaries"
TPL_JSON = ROOT / "docs" / "specs" / "stt_dictionary_templates.json"
NAME_SUBFLOW = ROOT / "docs" / "reference" / "bivr" / "samples" / "json" / "氏名聴取.json"

# txt ファイル名 -> stt_dictionary_templates.json のテンプレ名
# 新規テンプレは _NEW_TEMPLATE_META に description/applies_to_examples を定義
TXT_TO_TEMPLATE = {
    "name.txt": "hearing_name",
    "datetime.txt": "hearing_datetime",
    "time.txt": "hearing_time",
    "shinryoka.txt": "hearing_shinryoka_basic",
    "kenshin.txt": "hearing_kenshin_course_basic",
    "yoken.txt": "hearing_yoken_common",
    "yesno.txt": "hearing_yesno_common",
    "echo_back_yesno.txt": "echo_back_yesno",
    "unknown.txt": "hearing_unknown",
    "phone_number.txt": "hearing_phone_number",
}

# 新規テンプレ (JSON に未存在の場合) を作る際のメタデータ
_NEW_TEMPLATE_META = {
    "hearing_name": {
        "description": "患者氏名カナ聴取の汎用辞書。Subflow PatientName 標準利用 + 非サブフロー氏名 hearing でも use_template で参照可",
        "applies_to_examples": [
            "氏名聴取（サブフロー）",
            "入電者氏名聴取",
            "受診者氏名聴取",
            "家族氏名聴取",
        ],
    },
}

# 名前 txt は subflow 氏名聴取.json の profile_words にも反映する
SUBFLOW_SYNC = {
    "name.txt": (NAME_SUBFLOW, ["modules", "入力_患者_氏名", "params", "profile_words"]),
}


def _read_txt(fp: Path) -> str:
    """Read txt, strip trailing newlines, return content."""
    if not fp.exists():
        print(f"[ERROR] missing dictionary file: {fp}", file=sys.stderr)
        sys.exit(1)
    text = fp.read_text(encoding="utf-8")
    return text.rstrip("\n")


def _set_in(obj: dict, path: list[str], value):
    cur = obj
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value


def main() -> int:
    parser = argparse.ArgumentParser(description="辞書テキスト → 派生ファイル再生成")
    parser.add_argument("--dry-run", action="store_true", help="差分のみ表示、書き込まない")
    args = parser.parse_args()

    if not DICT_DIR.exists():
        print(f"[ERROR] dictionaries dir not found: {DICT_DIR}", file=sys.stderr)
        return 1

    # 1. Templates JSON
    with TPL_JSON.open(encoding="utf-8") as f:
        tpl_data = json.load(f)
    templates = tpl_data.setdefault("templates", {})

    changes_tpl: list[str] = []
    for txt_name, tpl_name in TXT_TO_TEMPLATE.items():
        txt_path = DICT_DIR / txt_name
        words = _read_txt(txt_path)
        if tpl_name not in templates:
            meta = _NEW_TEMPLATE_META.get(tpl_name, {
                "description": f"Auto-created from {txt_name}",
                "applies_to_examples": [],
            })
            templates[tpl_name] = {**meta, "words": words}
            changes_tpl.append(f"  CREATE template {tpl_name} ({len(words.splitlines())} lines)")
        else:
            old = templates[tpl_name].get("words", "")
            if old.rstrip("\n") != words:
                old_count = len(old.splitlines())
                new_count = len(words.splitlines())
                templates[tpl_name]["words"] = words
                changes_tpl.append(f"  UPDATE template {tpl_name}: {old_count} -> {new_count} lines")
            else:
                pass  # no change

    if changes_tpl:
        print(f"[stt_dictionary_templates.json] changes:")
        for c in changes_tpl:
            print(c)
    else:
        print("[stt_dictionary_templates.json] no changes")

    # 2. Subflow JSON sync
    changes_sub: list[str] = []
    subflow_data_cache: dict[Path, dict] = {}
    for txt_name, (sub_path, key_path) in SUBFLOW_SYNC.items():
        words = _read_txt(DICT_DIR / txt_name)
        if sub_path not in subflow_data_cache:
            with sub_path.open(encoding="utf-8") as f:
                subflow_data_cache[sub_path] = json.load(f)
        data = subflow_data_cache[sub_path]
        cur = data
        for k in key_path[:-1]:
            cur = cur[k]
        old = cur.get(key_path[-1], "")
        if old.rstrip("\n") != words:
            cur[key_path[-1]] = words
            changes_sub.append(
                f"  UPDATE {sub_path.relative_to(ROOT)} .{'.'.join(key_path)}: "
                f"{len(old.splitlines())} -> {len(words.splitlines())} lines"
            )

    if changes_sub:
        print(f"[subflow samples] changes:")
        for c in changes_sub:
            print(c)
    else:
        print("[subflow samples] no changes")

    if args.dry_run:
        print("\n[DRY RUN] no files written")
        return 0

    # Write
    if changes_tpl:
        with TPL_JSON.open("w", encoding="utf-8") as f:
            json.dump(tpl_data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(f"WROTE {TPL_JSON.relative_to(ROOT)}")

    if changes_sub:
        for sub_path, data in subflow_data_cache.items():
            with sub_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"WROTE {sub_path.relative_to(ROOT)}")

    if not changes_tpl and not changes_sub:
        print("\nNothing to do.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
