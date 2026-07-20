#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collect_evidence.py — P7 連結テスト 証跡収集 & Git コミット (Phase 6)

Usage:
  python3 connection_test/collect_evidence.py \
      --facility 福岡大学 \
      --flow     診療 \
      [--date    2026-07-09]   # 対象日 YYYY-MM-DD（省略=今日）
      [--log     output/福岡大学/logs/福岡大学_診療_run_20260709.csv]
      [--report  output/scenarios/福岡大学_診療/p7_report_20260709.md]
      [--bivr    output/連結テスト_福岡大学_診療.bivr]
      [--dry-run]   # ファイルコピーのみ。git commit/push しない
      [--push]      # git commit 後に git push も実行（--dry-run と排他）

処理:
  1. 証跡ファイルを output/scenarios/{施設}_{フロー}/evidence/{日付}/ にコピー
  2. manifest.json を生成（ファイル一覧・SHA256・収集日時）
  3. git add → git commit
  4. --push 指定時: git push origin <current-branch>
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ── ユーティリティ ────────────────────────────────────────────────────────────

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def find_latest(pattern: str) -> Path | None:
    """glob パターンにマッチするファイルのうち最新 mtime のものを返す"""
    matches = list(Path(".").glob(pattern))
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime)


def git_run(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(["git"] + list(args), capture_output=True, text=True, encoding="utf-8", errors="replace", check=check)


def current_branch() -> str:
    r = git_run("rev-parse", "--abbrev-ref", "HEAD")
    return r.stdout.strip()


# ── 証跡収集 ──────────────────────────────────────────────────────────────────

def collect_evidence(
    facility: str,
    flow: str,
    date_str: str,
    log_path: Path | None,
    report_path: Path | None,
    bivr_path: Path | None,
) -> tuple[Path, dict]:
    """
    証跡ファイルを evidence ディレクトリにコピーし manifest を返す。
    Returns: (evidence_dir, manifest_dict)
    """
    scenario_dir = Path(f"output/scenarios/{facility}_{flow}")
    evidence_dir = scenario_dir / "evidence" / date_str
    evidence_dir.mkdir(parents=True, exist_ok=True)

    entries = []

    def copy_and_record(src: Path, label: str):
        if src is None or not src.exists():
            print(f"[WARN] {label} が見つかりません: {src}")
            return
        dst = evidence_dir / src.name
        shutil.copy2(src, dst)
        entries.append({
            "label":  label,
            "source": str(src),
            "dest":   str(dst),
            "sha256": sha256(dst),
            "size":   dst.stat().st_size,
        })
        print(f"[COPY] {label}: {src} → {dst}")

    copy_and_record(log_path,    "brekeke_log")
    copy_and_record(report_path, "p7_report")
    copy_and_record(bivr_path,   "bivr")

    manifest = {
        "_about":    "P7 連結テスト 証跡マニフェスト",
        "facility":  facility,
        "flow":      flow,
        "date":      date_str,
        "collected": datetime.now().isoformat(timespec="seconds"),
        "files":     entries,
    }
    manifest_path = evidence_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[MANIFEST] {manifest_path}")

    return evidence_dir, manifest


# ── レポート要約 ──────────────────────────────────────────────────────────────

def summarize_report(report_path: Path | None) -> str:
    """p7_report.md から PASS/FAIL/NO_LOG 件数を抽出してコミットメッセージ用文字列を返す"""
    if report_path is None or not report_path.exists():
        return ""
    text = report_path.read_text(encoding="utf-8", errors="replace")
    summary_lines = [l for l in text.splitlines() if l.startswith("| ") and "件数" not in l and "|---" not in l]
    # テーブル行: "| PASS | 10 |" など
    stats = {}
    for line in summary_lines:
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) == 2:
            try:
                stats[parts[0]] = int(parts[1])
            except ValueError:
                pass
    if stats:
        return "  ".join(f"{k}: {v}" for k, v in stats.items())
    return ""


# ── Git 操作 ──────────────────────────────────────────────────────────────────

def git_commit(evidence_dir: Path, facility: str, flow: str, date_str: str, summary: str) -> str:
    """git add + commit。コミットハッシュを返す"""
    git_run("add", str(evidence_dir))

    msg_lines = [f"p7 evidence: {facility} {flow} {date_str}"]
    if summary:
        msg_lines.append("")
        msg_lines.append(summary)
    msg = "\n".join(msg_lines)

    git_run("commit", "-m", msg)
    r = git_run("rev-parse", "--short", "HEAD")
    return r.stdout.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="P7 証跡収集 & git commit (Phase 6)")
    ap.add_argument("--facility", required=True,  help="施設名")
    ap.add_argument("--flow",     required=True,  help="フロー名")
    ap.add_argument("--date",     default="",     help="対象日 YYYY-MM-DD（省略=今日）")
    ap.add_argument("--log",      default="",     help="Brekeke ログ CSV パス（省略=自動検索）")
    ap.add_argument("--report",   default="",     help="P7 レポート MD パス（省略=自動検索）")
    ap.add_argument("--bivr",     default="",     help="BIVR ファイルパス（省略=自動検索）")
    ap.add_argument("--dry-run",  action="store_true", help="コピーのみ。git commit/push しない")
    ap.add_argument("--push",     action="store_true", help="commit 後に git push も実行")
    args = ap.parse_args()

    facility = args.facility
    flow     = args.flow

    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    ts = date_str.replace("-", "")

    # ── ファイル解決 ─────────────────────────────────────────────────────────

    log_path = Path(args.log) if args.log else find_latest(
        f"output/{facility}/logs/{facility}_{flow}_run_{ts}.csv"
    ) or find_latest(f"output/{facility}/logs/*.csv")

    report_path = Path(args.report) if args.report else find_latest(
        f"output/scenarios/{facility}_{flow}/p7_report_{ts}*.md"
    ) or find_latest(f"output/scenarios/{facility}_{flow}/p7_report_*.md")

    bivr_path = Path(args.bivr) if args.bivr else find_latest(
        f"output/連結テスト_{facility}_{flow}.bivr"
    ) or find_latest(f"output/連結テスト_{facility}_{flow}*.bivr")

    print(f"[RESOLVE] log    = {log_path}")
    print(f"[RESOLVE] report = {report_path}")
    print(f"[RESOLVE] bivr   = {bivr_path}")

    if not any([
        log_path    and log_path.exists(),
        report_path and report_path.exists(),
        bivr_path   and bivr_path.exists(),
    ]):
        print("[ERROR] 証跡ファイルが1つも見つかりません。--log / --report / --bivr で指定してください。",
              file=sys.stderr)
        return 1

    # ── 収集 ─────────────────────────────────────────────────────────────────

    evidence_dir, manifest = collect_evidence(
        facility, flow, date_str,
        log_path, report_path, bivr_path,
    )

    if args.dry_run:
        print(f"\n[DRY-RUN] git commit はスキップしました。証跡: {evidence_dir}")
        return 0

    # ── Git commit ────────────────────────────────────────────────────────────

    summary = summarize_report(report_path)
    commit_hash = git_commit(evidence_dir, facility, flow, date_str, summary)
    print(f"\n[COMMIT] {commit_hash}")

    if args.push:
        branch = current_branch()
        print(f"[PUSH] origin/{branch} ...")
        r = git_run("push", "-u", "origin", branch, check=False)
        if r.returncode == 0:
            print(f"[PUSH] OK")
        else:
            print(f"[PUSH ERROR]\n{r.stderr}", file=sys.stderr)
            return 1

    print(f"\n[DONE] 証跡コミット完了")
    print(f"  evidence: {evidence_dir}")
    print(f"  commit:   {commit_hash}")
    if args.push:
        print(f"\n[NEXT] PR を作成してレビュー依頼してください。")
    else:
        print(f"\n[NEXT] git push して PR を作成してください:")
        print(f"  git push -u origin {current_branch()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
