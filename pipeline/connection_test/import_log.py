#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_log.py — ダウンロードフォルダの Brekeke ログ CSV を output/ に移動

Usage:
  python connection_test\import_log.py --facility 福岡大学 --flow 診療
  python connection_test\import_log.py --facility 福岡大学 --flow 診療 --date 2026-07-09
  python connection_test\import_log.py --facility 福岡大学 --flow 診療 --file "C:/Users/dong.nguyen/Downloads/call_log_20260709.csv"
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path


def find_downloads_dir() -> Path:
    """Windows / Mac / Linux のダウンロードフォルダを返す"""
    home = Path.home()
    for candidate in ["Downloads", "ダウンロード", "downloads"]:
        p = home / candidate
        if p.exists():
            return p
    return home


def pick_latest_csv(downloads: Path) -> Path | None:
    """ダウンロードフォルダの中で最新の CSV を返す"""
    csvs = sorted(downloads.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not csvs:
        return None
    return csvs[0]


def main() -> int:
    ap = argparse.ArgumentParser(description="ダウンロード CSV を output/ に移動")
    ap.add_argument("--facility", required=True, help="施設名（例: 福岡大学）")
    ap.add_argument("--flow",     required=True, help="フロー名（例: 診療）")
    ap.add_argument("--date",     default="",    help="対象日 YYYY-MM-DD（省略=今日）")
    ap.add_argument("--file",     default="",    help="CSV ファイルパスを直接指定（省略=Downloads の最新）")
    ap.add_argument("--copy",     action="store_true", help="移動ではなくコピーにする")
    args = ap.parse_args()

    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    ts = date_str.replace("-", "")

    # ── ソースファイルを決定 ───────────────────────────────────────────────
    if args.file:
        src = Path(args.file)
        if not src.exists():
            print(f"[ERROR] ファイルが見つかりません: {src}", file=sys.stderr)
            return 1
    else:
        downloads = find_downloads_dir()
        src = pick_latest_csv(downloads)
        if src is None:
            print(f"[ERROR] {downloads} に CSV が見つかりません。--file で指定してください。", file=sys.stderr)
            return 1
        print(f"[FOUND] 最新 CSV: {src}")
        ans = input("このファイルを使いますか？ [Y/n] ").strip().lower()
        if ans not in ("", "y", "yes"):
            print("キャンセルしました。--file でファイルを直接指定してください。")
            return 0

    # ── 出力先を決定 ──────────────────────────────────────────────────────
    out_dir = Path(f"output/{args.facility}/logs")
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / f"{args.facility}_{args.flow}_run_{ts}.csv"

    # ── コピー or 移動 ────────────────────────────────────────────────────
    if args.copy:
        shutil.copy2(src, dst)
        print(f"[COPY] {src} → {dst}")
    else:
        shutil.move(str(src), dst)
        print(f"[MOVE] {src} → {dst}")

    print(f"\n[OK] {dst}")
    print(f"\n[NEXT] レポート生成:")
    print(f"  python connection_test\\compare_p7_results.py ^")
    print(f"      --log   {dst} ^")
    print(f"      --cases connection_test\\cases\\{args.facility}_{args.flow}_real.json ^")
    print(f"      --out   output\\scenarios\\{args.facility}_{args.flow}\\p7_report_{ts}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
