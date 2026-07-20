#!/usr/bin/env python3
"""
GitHub Project Metrics Collector
=================================
GitHub APIからメトリクスを取得し metrics.json を出力する。

ローカル実行:
  $env:GITHUB_TOKEN="ghp_xxx"; python metrics/fetch_metrics.py

GitHub Actions:
  GITHUB_TOKEN は自動で利用可能（secrets.GITHUB_TOKEN）
"""

import os, json, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

TOKEN = os.environ.get("GITHUB_TOKEN", "")
REPO = os.environ.get("GITHUB_REPO", "TS-dong-nc/gen_flow")
API = "https://api.github.com"
OUT = "metrics.json"
# pipeline_state_*.json はプロジェクトルートの output/ に格納される
PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"


def get(path, params=None):
    url = f"{API}{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "voicebot-metrics",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    try:
        with urlopen(req) as r:
            return json.loads(r.read().decode())
    except HTTPError as e:
        print(f"  API {e.code}: {url}")
        return None


def get_all(path, params=None):
    params = dict(params or {}, per_page="100")
    page, items = 1, []
    while True:
        params["page"] = str(page)
        batch = get(path, params)
        if not batch:
            break
        items.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return items


def dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def load_pipeline_states():
    """pipeline_state を読み込み {branch_name: state_dict} を返す。

    新パス: output/scenarios/{施設}_{flow}/pipeline_state_*.json
    旧パス: output/pipeline_state_*.json（後方互換）
    """
    states = {}
    files = list(OUTPUT_DIR.glob("scenarios/*/pipeline_state_*.json")) \
          + list(OUTPUT_DIR.glob("pipeline_state_*.json"))
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            branch = data.get("branch_name", "")
            if branch and data.get("started_at"):
                states[branch] = {
                    "started_at":   data.get("started_at", ""),
                    "ended_at":     data.get("ended_at", ""),
                    "step_timings": data.get("step_timings", {}),
                    "facility":     data.get("facility", ""),
                    "flow":         data.get("flow", ""),
                    "pattern":      data.get("pattern", 0),
                }
        except Exception:
            pass
    return states


def fetch_prs():
    print("  PR取得中...")
    prs = get_all(f"/repos/{REPO}/pulls", {"state": "all"})
    out = []
    for p in (prs or []):
        created, merged = dt(p.get("created_at")), dt(p.get("merged_at"))
        dur = round((merged - created).total_seconds() / 3600, 2) if created and merged else None
        head_ref = (p.get("head") or {}).get("ref", "")
        out.append({
            "number": p["number"], "title": p["title"],
            "author": (p.get("user") or {}).get("login", "unknown"),
            "state": "merged" if p.get("merged_at") else p["state"],
            "head_ref": head_ref,
            "created_at": p.get("created_at"), "merged_at": p.get("merged_at"),
            "closed_at": p.get("closed_at"), "duration_hours": dur,
            "additions": p.get("additions", 0), "deletions": p.get("deletions", 0),
            "changed_files": p.get("changed_files", 0),
            "labels": [l["name"] for l in p.get("labels", [])],
        })
    return out


def fetch_commits():
    print("  コミット取得中...")
    commits = get_all(f"/repos/{REPO}/commits")
    out = []
    for c in (commits or []):
        author = (c.get("author") or {}).get("login") or (c.get("commit", {}).get("author") or {}).get("name", "unknown")
        d = get(f"/repos/{REPO}/commits/{c['sha']}")
        files = []
        adds = dels = 0
        if d:
            adds = (d.get("stats") or {}).get("additions", 0)
            dels = (d.get("stats") or {}).get("deletions", 0)
            for f in (d.get("files") or []):
                files.append({"filename": f["filename"], "additions": f.get("additions", 0),
                              "deletions": f.get("deletions", 0), "changes": f.get("changes", 0)})
        out.append({
            "sha": c["sha"][:7], "author": author,
            "date": (c.get("commit", {}).get("author") or {}).get("date"),
            "message": (c.get("commit", {}).get("message") or "").split("\n")[0],
            "additions": adds, "deletions": dels, "files_changed": files,
        })
    return out


def author_stats(commits):
    s = {}
    for c in commits:
        a = c["author"]
        if a not in s:
            s[a] = {"commits": 0, "additions": 0, "deletions": 0, "files": set()}
        s[a]["commits"] += 1
        s[a]["additions"] += c["additions"]
        s[a]["deletions"] += c["deletions"]
        for f in c.get("files_changed", []):
            s[a]["files"].add(f["filename"])
    return sorted([{"author": a, "commits": v["commits"], "additions": v["additions"],
                     "deletions": v["deletions"], "files_touched": len(v["files"])}
                    for a, v in s.items()], key=lambda x: -x["commits"])


def file_freq(commits):
    f = {}
    for c in commits:
        for fi in c.get("files_changed", []):
            n = fi["filename"]
            if n not in f:
                f[n] = {"filename": n, "change_count": 0, "total_additions": 0, "total_deletions": 0}
            f[n]["change_count"] += 1
            f[n]["total_additions"] += fi["additions"]
            f[n]["total_deletions"] += fi["deletions"]
    return sorted(f.values(), key=lambda x: -x["change_count"])


def pipeline_times(prs, states):
    """
    states: {branch_name: state_dict}
    - actual_duration_hours  = merged_at - started_at（ローカル着手〜マージ）
    - pipeline_duration_seconds = ended_at - started_at（orchestrator純実行時間）
    - step_timings: ステップ別所要時間 {step_id: {status, seconds}}
    """
    rows = []
    for p in prs:
        if p["state"] != "merged" or not p["duration_hours"]:
            continue
        sd = states.get(p.get("head_ref", "")) or {}
        started_str = sd.get("started_at", "")
        ended_str   = sd.get("ended_at", "")

        actual_started_at       = None
        actual_duration_hours   = None
        pipeline_duration_seconds = None

        if started_str and p.get("merged_at"):
            try:
                started_dt = datetime.fromisoformat(started_str)
                if started_dt.tzinfo is None:
                    started_dt = started_dt.replace(tzinfo=timezone.utc)
                merged_dt = dt(p["merged_at"])
                actual_started_at     = started_dt.isoformat()
                actual_duration_hours = round((merged_dt - started_dt).total_seconds() / 3600, 2)
            except Exception:
                pass

        if started_str and ended_str:
            try:
                s_dt = datetime.fromisoformat(started_str)
                e_dt = datetime.fromisoformat(ended_str)
                pipeline_duration_seconds = round((e_dt - s_dt).total_seconds())
            except Exception:
                pass

        rows.append({
            "pr_number": p["number"], "title": p["title"], "author": p["author"],
            "duration_hours": p["duration_hours"],
            "actual_started_at": actual_started_at,
            "actual_duration_hours": actual_duration_hours,
            "pipeline_duration_seconds": pipeline_duration_seconds,
            "step_timings": sd.get("step_timings", {}),
            "created_at": p["created_at"], "merged_at": p["merged_at"],
            "is_pipeline_run": any(
                l in p.get("labels", []) for l in ["pipeline", "auto-generation", "flow-build"]
            ),
        })
    return sorted(rows, key=lambda x: x["created_at"], reverse=True)


def main():
    if not TOKEN:
        print("警告: GITHUB_TOKEN 未設定。Public API rate limit (60 req/hr) で実行します。")

    print(f"リポジトリ: {REPO}")
    states = load_pipeline_states()
    print(f"  pipeline_state: {len(states)}件 ({', '.join(states.keys()) or 'なし'})")
    prs = fetch_prs()
    commits = fetch_commits()
    astats = author_stats(commits)
    ffreq = file_freq(commits)
    ptimes = pipeline_times(prs, states)

    merged_with_dur = [p for p in prs if p["duration_hours"]]
    avg_dur = round(sum(p["duration_hours"] for p in merged_with_dur) / max(len(merged_with_dur), 1), 2)
    actual_durs   = [p["actual_duration_hours"]    for p in ptimes if p.get("actual_duration_hours")    is not None]
    pipeline_durs = [p["pipeline_duration_seconds"] for p in ptimes if p.get("pipeline_duration_seconds") is not None]
    avg_actual_dur   = round(sum(actual_durs)   / len(actual_durs),   2) if actual_durs   else None
    avg_pipeline_dur = round(sum(pipeline_durs) / len(pipeline_durs))    if pipeline_durs else None

    metrics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": REPO,
        "summary": {
            "total_prs": len(prs),
            "merged_prs": len([p for p in prs if p["state"] == "merged"]),
            "open_prs": len([p for p in prs if p["state"] == "open"]),
            "total_commits": len(commits),
            "contributors": len(astats),
            "avg_pr_duration_hours": avg_dur,
            "avg_actual_duration_hours": avg_actual_dur,
            "avg_pipeline_duration_seconds": avg_pipeline_dur,
            "note_actual_duration":   "actual_duration_hours = ローカル着手〜マージ。pipeline_state_*.jsonがある案件のみ。",
            "note_pipeline_duration": "pipeline_duration_seconds = orchestrator started_at〜ended_at（純実行時間。承認待ち含まず）",
        },
        "pull_requests": prs,
        "commits": [{k: v for k, v in c.items() if k != "files_changed"} for c in commits],
        "author_stats": astats,
        "file_frequency": ffreq[:50],
        "pipeline_times": ptimes,
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"\n完了: {OUT}")
    print(f"  PR: {len(prs)} / Commits: {len(commits)} / Contributors: {len(astats)}")
    print(f"  平均PR所要時間(created_at〜merged_at): {avg_dur}h")
    if avg_actual_dur is not None:
        print(f"  平均実所要時間(ローカル着手〜merged_at): {avg_actual_dur}h ({len(actual_durs)}件計測済み)")


if __name__ == "__main__":
    main()
