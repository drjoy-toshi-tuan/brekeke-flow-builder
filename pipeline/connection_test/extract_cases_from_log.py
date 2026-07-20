#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_cases_from_log.py — Brekeke実ログCSVからパターンを抽出し
  1. master_patterns.json を更新（seen_in / observed_cases）
  2. 既存ケースファイルに無い新規ケース候補を提案

Usage:
  python3 connection_test/extract_cases_from_log.py \\
      --log    output/東京都立豊島/logs/東京都立豊島_診療_run_20260709.csv \\
      --cases  connection_test/cases/東京都立豊島_診療_テスト.json \\
      --master connection_test/master_patterns.json \\
      [--facility 東京都立豊島] \\
      [--flow    診療] \\
      [--out-cases connection_test/cases/東京都立豊島_診療_テスト.json]  # --apply で上書き \\
      [--apply]   # 新規ケースを既存ケースファイルに追記 \\
      [--dry-run] # master更新せず提案のみ表示
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path


# ── ログ解析 ──────────────────────────────────────────────────────────────────

def parse_trace(trace_str: str) -> list[tuple[str, str]]:
    """'k1:v1;k2:v2;' → [('k1','v1'), ('k2','v2'), ...]  順序保持"""
    result = []
    for seg in trace_str.split(";"):
        seg = seg.strip()
        if not seg:
            continue
        idx = seg.find(":")
        if idx < 0:
            result.append((seg, ""))
        else:
            result.append((seg[:idx], seg[idx + 1:]))
    return result


def load_log(log_path: Path, facility: str, flow: str) -> list[dict]:
    """CSVを読み込み、対象施設・フローの行を返す"""
    rows = []
    with log_path.open(encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        for raw in reader:
            if len(raw) < 7:
                continue
            # col4: flow name  例) drjoy^と）東京都立豊島$T_M｜診療
            flow_col = raw[4] if len(raw) > 4 else ""

            # 施設フィルタ
            if facility and facility not in flow_col:
                continue
            if flow and flow not in flow_col:
                continue

            trace_str = raw[7] if len(raw) > 7 else ""
            trace = parse_trace(trace_str)
            trace_dict = dict(trace)  # 最後の値で上書き（重複キー対策）

            rows.append({
                "call_id":   raw[0].strip(),
                "caller":    raw[2].strip(),
                "flow":      flow_col.strip(),
                "datetime":  raw[5].strip() if len(raw) > 5 else "",
                "duration":  raw[6].strip() if len(raw) > 6 else "",
                "trace_raw": trace_str,
                "trace":     trace,
                "trace_dict": trace_dict,
            })
    return rows


# ── パターン抽出 ──────────────────────────────────────────────────────────────

SAVE_PATTERN = re.compile(r'^save[-_](.+)$', re.IGNORECASE)

# 典型的なSTT入力ノード名のキーワード → inject キーのマッピング候補
STT_KEYWORDS = [
    ("用件",       "入力_用件"),
    ("受診歴",     "入力_受診歴"),
    ("診療科",     "入力_変更_診療科"),
    ("紹介状",     "入力_予約_紹介状有無"),
    ("選定療養費", "入力_選定療養費"),
    ("診察か否か", "入力－診察か否か"),
    ("症状",       "入力_症状"),
    ("希望日",     "入力_希望日①"),
    ("現在の予約日","入力_現在の予約日"),
    ("不可日",     "入力_不可日"),
    ("理由",       "入力_理由"),
    ("問合せ",     "入力_相談_問合せ"),
    ("追加の質問", "入力_追加の質問"),
    ("診察券",     "入力_患者_診察券番号"),
    ("氏名",       "入力_患者_氏名"),
    ("生年月日",   "入力_生年月日"),
]

TERMINAL_KEYWORDS = ["終話", "切断", "TIMEOUT_EXIT", "exit", "reject"]

# save-xxx:value から inject 値を推定するためのキーワードマップ
SAVE_TO_INJECT = {
    "用件": "入力_用件",
    "受診歴": "入力_受診歴",
    "診療科": "入力_変更_診療科",
    "紹介状": "入力_予約_紹介状有無",
    "選定療養費": "入力_選定療養費",
    "診察": "入力－診察か否か",
    "理由": "入力_理由",
    "問合せ": "入力_相談_問合せ",
    "希望日": "入力_希望日①",
    "予約日": "入力_現在の予約日",
    "不可日": "入力_不可日",
    "症状": "入力_症状",
}


def extract_inject_from_trace(trace: list[tuple[str, str]]) -> dict:
    """トレースから inject 値を推定。3つのフォーマットに対応:

    Format A (P7スタブログ・東京都立豊島型):
      入力_用件:予約
      jump-予約.入力_変更_診療科:内科
      入力－診察か否か:診察   (em dash)

    Format B (実ログ・福岡大学型):
      save-用件:OK;save-用件:予約の変更   → 2番目採用
      ジャンプ_用件.入力_用件:TIMEOUT

    Format C (P7スタブ・旧型):
      ジャンプ_診療科.Scripts_診療科:整形外科
    """
    inject = {}
    # 値が有効かチェック（除外する値）
    SKIP_VALS = {"", "OK", "true", "false", "SUCCESS", "YES", "NO"}
    # inject対象ノード名プレフィックス
    INJECT_PREFIX = ("入力_", "入力－", "入力-")

    def append_val(inject_key: str, val: str):
        """リトライシーケンスとして追記。連続同値は重複しない"""
        if inject_key not in inject:
            inject[inject_key] = [val]
        else:
            last = inject[inject_key][-1]
            if val == "NO_RESULT" and last == "NO_RESULT":
                return  # 重複NO_RESULTはスキップ
            elif last != "NO_RESULT" and val != "NO_RESULT":
                # 実値→実値: 後勝ち（save-xxx:OK;save-xxx:実値 の2番目採用）
                inject[inject_key][-1] = val
            else:
                inject[inject_key].append(val)

    # ── Format A: 入力_xxx:value / jump-yyy.入力_xxx:value ───────────────────
    def try_inject_node(node_name: str, val: str):
        """node_name が inject ノードなら inject に追記"""
        for pfx in INJECT_PREFIX:
            if node_name.startswith(pfx):
                if val == "TIMEOUT" or val == "NO_RESULT":
                    append_val(node_name, "NO_RESULT")
                elif val and val not in SKIP_VALS:
                    append_val(node_name, val)
                return True
        return False

    # ── Format B: save-xxx:value ─────────────────────────────────────────────
    def try_save_key(save_key: str, val: str):
        for kw, inject_key in SAVE_TO_INJECT.items():
            if kw in save_key:
                if val == "OK":
                    # placeholder: 後続の実値で上書き
                    if inject_key not in inject:
                        inject[inject_key] = []
                elif val == "TIMEOUT":
                    if inject_key in inject and inject[inject_key] == []:
                        inject[inject_key] = ["NO_RESULT"]
                    else:
                        append_val(inject_key, "NO_RESULT")
                elif val and val not in SKIP_VALS:
                    if inject_key in inject and inject[inject_key] == []:
                        inject[inject_key] = [val]
                    else:
                        append_val(inject_key, val)
                return True
        return False

    for key, val in trace:
        # ── Format A直接: 入力_xxx ──────────────────────────────────────────
        if try_inject_node(key, val):
            continue

        # ── Format A jump-: jump-subflow.入力_xxx ───────────────────────────
        if key.startswith("jump-"):
            # "jump-subflow.node_name:value" → node_name が inject ノードなら採用
            dot = key.find(".")
            if dot >= 0:
                node_name = key[dot + 1:]
                try_inject_node(node_name, val)
            # fallback なし: jump- 形式は必ず 入力_xxx 形式のノード名を使う
            continue

        # ── Format B: save-xxx / ジャンプ_xxx ──────────────────────────────
        if key.startswith("save-") or key.startswith("save_"):
            try_save_key(key[5:], val)
        elif key.startswith("ジャンプ_"):
            inner = key[len("ジャンプ_"):]
            dot = inner.find(".")
            node_name = inner[dot + 1:] if dot >= 0 else inner
            if not try_inject_node(node_name, val):
                for kw, inject_key in SAVE_TO_INJECT.items():
                    if kw in inner:
                        if val == "TIMEOUT":
                            append_val(inject_key, "NO_RESULT")
                        elif val and val not in SKIP_VALS:
                            append_val(inject_key, val)
                        break

    # placeholder（空リスト）を除去
    inject = {k: v for k, v in inject.items() if v}
    return inject


def find_terminal(trace: list[tuple[str, str]]) -> str:
    """トレースの末尾ノードを探す"""
    if not trace:
        return "UNKNOWN"
    # 終話・切断ノードを優先探索
    for key, val in reversed(trace):
        for kw in TERMINAL_KEYWORDS:
            if kw in key:
                return key
    # 最後のノード
    return trace[-1][0] if trace else "UNKNOWN"


def detect_inject_pattern(inject_list: list) -> str:
    """inject配列のパターン名を判定"""
    if not inject_list:
        return "normal"
    no_result_count = inject_list.count("NO_RESULT") + inject_list.count("TIMEOUT")
    if no_result_count == 0:
        return "normal"
    elif no_result_count == 1 and len(inject_list) >= 2:
        return "retry_once"
    elif no_result_count == 2 and len(inject_list) >= 3:
        return "retry_twice"
    elif no_result_count >= 3:
        return "exhaust"
    return "normal"


# ── 既存ケースとの比較 ────────────────────────────────────────────────────────

def cases_fingerprint(case: dict) -> frozenset:
    """ケースの inject + terminal の fingerprint"""
    inject = case.get("inject", {})
    terminal = case.get("expect", {}).get("終端", "")
    items = []
    for k, v in inject.items():
        items.append(f"{k}={v[0] if v else ''}")
    items.append(f"終端={terminal}")
    return frozenset(items)


def existing_fingerprints(cases_doc: dict) -> set:
    fps = set()
    for c in cases_doc.get("cases", []):
        fps.add(cases_fingerprint(c))
    return fps


# ── マスター更新 ──────────────────────────────────────────────────────────────

def update_master(master: dict, facility: str, flow: str,
                  inject: dict, terminal: str, call_id: str, dt: str):
    """master_patterns.json の seen_in / observed_cases を更新"""
    tag = f"{facility}_{flow}_{dt[:10] if dt else '?'}_{call_id}"

    # value_patterns の seen_in を更新
    vp = master.get("value_patterns", {})
    for inject_key, vals in inject.items():
        # inject_key → value_pattern カテゴリにマップ
        cat = None
        for kw in ["用件", "受診歴", "診療科", "紹介状", "選定療養費", "診察か否か"]:
            if kw in inject_key:
                cat = kw
                break
        if cat and cat in vp:
            for v in vals:
                if v in vp[cat]:
                    seen = vp[cat][v].setdefault("seen_in", [])
                    if tag not in seen:
                        seen.append(tag)
                elif v not in ("NO_RESULT", "TIMEOUT"):
                    # 新しい値を追加
                    vp[cat][v] = {"desc": v, "seen_in": [tag]}

    # terminal_patterns の seen_in を更新
    tp = master.get("terminal_patterns", {})
    if terminal in tp:
        seen = tp[terminal].setdefault("seen_in", [])
        if tag not in seen:
            seen.append(tag)
    elif terminal and terminal != "UNKNOWN":
        tp[terminal] = {"desc": "（実ログから検出）", "seen_in": [tag]}

    # observed_cases に追加
    obs = master.setdefault("observed_cases", [])
    entry = {
        "call_id":   call_id,
        "facility":  facility,
        "flow":      flow,
        "datetime":  dt,
        "terminal":  terminal,
        "inject":    inject,
    }
    # 重複チェック（同じcall_idは1回だけ）
    if not any(o.get("call_id") == call_id for o in obs):
        obs.append(entry)


# ── 新規ケース生成 ────────────────────────────────────────────────────────────

def generate_new_case(base_id: int, inject: dict, terminal: str,
                      call_id: str, facility: str, flow: str, dt: str) -> dict:
    """実ログから新規ケースを生成"""
    # ラベル自動生成
    yoken = inject.get("入力_用件", ["?"])[0]
    shika = inject.get("入力_変更_診療科", [""])[0]
    pattern_parts = []
    for k, v in inject.items():
        p = detect_inject_pattern(v)
        if p != "normal":
            pattern_parts.append(f"{k.replace('入力_','')}={p}")

    label_parts = [yoken]
    if shika:
        label_parts.append(shika)
    if pattern_parts:
        label_parts.append("_".join(pattern_parts))
    label = "_".join(filter(None, label_parts))

    checkpoints = []
    if terminal not in ("UNKNOWN", "TIMEOUT_EXIT"):
        checkpoints.append(terminal)

    return {
        "id":      str(base_id),
        "dtmf":    str(base_id),
        "label":   f"実ログ_{label}",
        "_source": f"log:{dt[:10] if dt else '?'} call_id:{call_id} facility:{facility}",
        "_status": "proposed",
        "inject":  inject,
        "expect":  {
            "終端":        terminal,
            "checkpoints": checkpoints,
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="実ログからP7テストケースを抽出")
    ap.add_argument("--log",      required=True, help="Brekekeログ CSV パス")
    ap.add_argument("--cases",    required=True, help="既存ケースJSON パス")
    ap.add_argument("--master",   required=True, help="マスターパターンJSON パス")
    ap.add_argument("--facility", default="",    help="施設名フィルタ（部分一致）")
    ap.add_argument("--flow",     default="",    help="フロー名フィルタ（部分一致）")
    ap.add_argument("--out-cases", default="",   help="新規ケース追記先（省略=--cases と同じ）")
    ap.add_argument("--apply",    action="store_true", help="新規ケースをファイルに追記")
    ap.add_argument("--dry-run",  action="store_true", help="ファイル書き込みなし")
    args = ap.parse_args()

    log_path    = Path(args.log)
    cases_path  = Path(args.cases)
    master_path = Path(args.master)
    out_cases   = Path(args.out_cases) if args.out_cases else cases_path

    # ── ロード ─────────────────────────────────────────────────────────────
    if not log_path.exists():
        print(f"[ERROR] ログファイルが見つかりません: {log_path}", file=sys.stderr)
        return 1

    with cases_path.open(encoding="utf-8") as f:
        cases_doc = json.load(f)

    with master_path.open(encoding="utf-8") as f:
        master = json.load(f)

    # ── ログ解析 ────────────────────────────────────────────────────────────
    rows = load_log(log_path, args.facility, args.flow)
    print(f"[LOG] {len(rows)} 行を読み込み（施設={args.facility or '全て'} / フロー={args.flow or '全て'}）")

    if not rows:
        print("[WARN] 対象行が0件です。--facility / --flow を確認してください。")
        return 0

    # ── 既存ケースのfingerprint ─────────────────────────────────────────────
    existing_fps = existing_fingerprints(cases_doc)
    existing_ids = [int(c["id"]) for c in cases_doc.get("cases", []) if str(c.get("id","")).isdigit()]
    next_id = max(existing_ids, default=0) + 1

    # ── 各ログ行を解析してパターン抽出 ─────────────────────────────────────
    new_cases = []
    stats = {"total": 0, "new": 0, "duplicate": 0, "no_inject": 0}

    for row in rows:
        stats["total"] += 1
        inject = extract_inject_from_trace(row["trace"])
        terminal = find_terminal(row["trace"])

        # masterを更新
        if not args.dry_run:
            update_master(master, args.facility or row["flow"], args.flow or "",
                          inject, terminal, row["call_id"], row["datetime"])

        if not inject:
            stats["no_inject"] += 1
            continue

        # 既存との重複チェック
        new_case = generate_new_case(next_id, inject, terminal,
                                     row["call_id"], args.facility, args.flow,
                                     row["datetime"])
        fp = cases_fingerprint(new_case)
        if fp in existing_fps:
            stats["duplicate"] += 1
            continue

        existing_fps.add(fp)
        new_cases.append(new_case)
        stats["new"] += 1
        next_id += 1

    # ── 結果表示 ────────────────────────────────────────────────────────────
    print(f"\n[SUMMARY]")
    print(f"  ログ行数:        {stats['total']}")
    print(f"  inject抽出なし:  {stats['no_inject']}")
    print(f"  既存と重複:      {stats['duplicate']}")
    print(f"  新規ケース候補:  {stats['new']}")

    if new_cases:
        print(f"\n[NEW CASES] ↓ 追加候補 {len(new_cases)}件")
        for c in new_cases:
            print(f"  id={c['id']:>3}  label={c['label']}")
            print(f"         inject={json.dumps(c['inject'], ensure_ascii=False)}")
            print(f"         terminal={c['expect']['終端']}")
    else:
        print("\n[OK] 新規パターンなし（全て既存ケースでカバー済み）")

    # ── ファイル書き込み ─────────────────────────────────────────────────────
    if args.dry_run:
        print("\n[DRY-RUN] ファイルは変更しませんでした。")
        return 0

    # master_patterns.json を更新
    master["_updated"] = datetime.now().isoformat(timespec="seconds")
    with master_path.open("w", encoding="utf-8") as f:
        json.dump(master, f, ensure_ascii=False, indent=2)
    print(f"\n[MASTER] 更新: {master_path}")
    print(f"  observed_cases: {len(master.get('observed_cases', []))} 件")

    # 新規ケースを追記
    if new_cases and args.apply:
        cases_doc["cases"].extend(new_cases)
        with out_cases.open("w", encoding="utf-8") as f:
            json.dump(cases_doc, f, ensure_ascii=False, indent=2)
        print(f"[CASES] {len(new_cases)}件を追記: {out_cases}")
    elif new_cases:
        print(f"\n[HINT] --apply を付けると {len(new_cases)}件をケースファイルに追記します。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
