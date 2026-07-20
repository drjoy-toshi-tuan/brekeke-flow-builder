#!/usr/bin/env python3
"""
extract_bivr.py — .bivr パッケージからフローJSONを取り出すスクリプト

build_bivr.py の逆変換。.bivr（ZIPアーカイブ）内のフローJSONを展開する。

使い方:
    # 全フローを output/ に展開（pretty-print）
    python3 scripts/extract_bivr.py path/to/file.bivr

    # 指定ディレクトリに展開
    python3 scripts/extract_bivr.py path/to/file.bivr -o output/

    # minified（1行）で出力
    python3 scripts/extract_bivr.py path/to/file.bivr --minified

    # フロー一覧だけ表示（展開しない）
    python3 scripts/extract_bivr.py path/to/file.bivr --list

.bivr 仕様:
    - ZIPアーカイブ（拡張子を .bivr に変えたもの）
    - 内部に flows/ フォルダを持つ
    - フローJSONは @flow_{URLエンコード済みフロー名}.txt として配置
    - 中身は1行のJSON
"""

import json
import sys
import os
import zipfile
from urllib.parse import unquote
from pathlib import Path


def decode_flow_entry(entry_name: str) -> str:
    """
    ZIPエントリ名からフロー名をデコードする。
    例: flows/@flow_%48%43%E3%82%AF%E3%83%AA%E3%83%8B%E3%83%83%E3%82%AF...txt
    → HCクリニック厚木$健診_20260311
    """
    # flows/ プレフィックスを除去
    basename = entry_name
    if "/" in basename:
        basename = basename.split("/", 1)[1]

    # @flow_ プレフィックスを除去
    if basename.startswith("@flow_"):
        basename = basename[len("@flow_"):]

    # .txt 拡張子を除去
    if basename.endswith(".txt"):
        basename = basename[:-4]
    elif basename.endswith(".json"):
        basename = basename[:-5]

    # URLデコード
    return unquote(basename)


def safe_filename(flow_name: str) -> str:
    """フロー名をファイル名に安全な文字列に変換する。"""
    return flow_name.replace("$", "_").replace("/", "_").replace("\\", "_")


def list_flows(bivr_path: str):
    """bivrファイル内のフロー一覧を表示する。"""
    with zipfile.ZipFile(bivr_path, "r") as zf:
        entries = zf.namelist()

    print(f"[INFO] {bivr_path}")
    print(f"       エントリ数: {len(entries)}")
    print()

    for entry in entries:
        flow_name = decode_flow_entry(entry)

        # ファイルサイズ取得
        with zipfile.ZipFile(bivr_path, "r") as zf:
            info = zf.getinfo(entry)
            size = info.file_size

        # JSON読み込んでモジュール数を取得
        with zipfile.ZipFile(bivr_path, "r") as zf:
            data = zf.read(entry).decode("utf-8")
            try:
                flow = json.loads(data)
                mod_count = len(flow.get("modules", {}))
                start = flow.get("start", "N/A")
            except json.JSONDecodeError:
                mod_count = "?"
                start = "?"

        print(f"  [{entries.index(entry) + 1}] {flow_name}")
        print(f"      エントリ   : {entry}")
        print(f"      サイズ     : {size:,} bytes")
        print(f"      モジュール数: {mod_count}")
        print(f"      start     : {start}")
        print()


def extract_bivr(bivr_path: str, output_dir: str, minified: bool = False):
    """bivrファイルからフローJSONを展開する。"""
    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(bivr_path, "r") as zf:
        entries = zf.namelist()

    if not entries:
        print(f"[WARN] bivrファイルにエントリがありません: {bivr_path}")
        return

    extracted = []

    for entry in entries:
        flow_name = decode_flow_entry(entry)
        safe_name = safe_filename(flow_name)

        # JSON読み込み
        with zipfile.ZipFile(bivr_path, "r") as zf:
            raw = zf.read(entry).decode("utf-8")

        try:
            flow = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSONパースエラー: {entry} — {e}")
            continue

        # 出力ファイル名
        output_filename = f"{safe_name}.json"
        output_path = os.path.join(output_dir, output_filename)

        # 重複回避
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{safe_name}_{counter}.json"
            output_path = os.path.join(output_dir, output_filename)
            counter += 1

        # JSON出力
        if minified:
            json_str = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
        else:
            json_str = json.dumps(flow, ensure_ascii=False, indent=2)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)

        mod_count = len(flow.get("modules", {}))
        extracted.append((flow_name, output_path, mod_count))

    # レポート
    print(f"[OK] 展開完了: {bivr_path}")
    print(f"     出力先: {output_dir}")
    print(f"     フロー数: {len(extracted)}")
    print()

    for flow_name, path, mod_count in extracted:
        print(f"  ✓ {flow_name}")
        print(f"    → {path} ({mod_count} modules)")
    print()


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/extract_bivr.py <file.bivr>              # output/ に展開")
        print("  python3 scripts/extract_bivr.py <file.bivr> -o <dir>     # 指定先に展開")
        print("  python3 scripts/extract_bivr.py <file.bivr> --minified   # 1行JSONで出力")
        print("  python3 scripts/extract_bivr.py <file.bivr> --list       # 一覧表示のみ")
        sys.exit(1)

    bivr_path = sys.argv[1]

    if not os.path.exists(bivr_path):
        print(f"[ERROR] ファイルが見つかりません: {bivr_path}")
        sys.exit(1)

    if not zipfile.is_zipfile(bivr_path):
        print(f"[ERROR] ZIPファイルではありません: {bivr_path}")
        sys.exit(1)

    # --list モード
    if "--list" in sys.argv:
        list_flows(bivr_path)
        return

    # 出力先
    output_dir = "output"
    if "-o" in sys.argv:
        idx = sys.argv.index("-o")
        if idx + 1 < len(sys.argv):
            output_dir = sys.argv[idx + 1]

    minified = "--minified" in sys.argv

    extract_bivr(bivr_path, output_dir, minified)


if __name__ == "__main__":
    main()
