#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_branch_cases_from_yaml.py — 設計書 YAML の scenario_flow から
全分岐経路を DFS で列挙し、P7 連結テスト用 cases JSON を自動生成する。

各分岐経路ごとに「どのSTTノードに何を inject するか」を
条件ラベル（conditions[].match / choices[].label）から導出する。

hearing / stt 系ノードの inject 値:
  - choices がある場合: choices[0].label（最初の正常選択肢）
  - conditions がある場合: その分岐に入るための match 値
  - どちらもない場合: defaults または hospital_config の inject_pools から補完

Usage:
  python3 connection_test/gen_branch_cases_from_yaml.py \\
      --yaml  output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml \\
      --out   connection_test/cases/{施設}_{flow}_branches.json \\
      [--config connection_test/hospital_configs/{施設}_{flow}.json]  # defaults/inject_pools 補完用
      [--happy-only]   # 正常経路（other/エラー分岐除外）のみ出力
      [--max-paths 40]

出力形式:
  stub_stt_connection.py / gen_tts_preview_bivr.py が直接読める cases JSON
"""

import argparse
import json
import re
import sys
from pathlib import Path


try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML が必要です。pip install pyyaml を実行してください。", file=sys.stderr)
    sys.exit(1)

MAX_DEPTH = 60


# ─── ブロック分類 ──────────────────────────────────────────────────────────────

STT_TYPES = {"hearing", "slot", "patient_name", "dob", "phone", "card_number",
             "free_text", "clinical_department", "intent", "faq"}

SKIP_TYPES = {"opening", "announcement", "wait", "null_check", "subflow"}

BRANCH_TYPES = {"script", "context_match_router", "date_of_call_classifier",
                "incoming_category_classifier", "phone_branch",
                "clinical_department_normalize", "clinical_department_classifier",
                "cmr_chain", "phone2name"}

TERMINAL_TYPES = {"termination", "call_transfer", "disconnect"}


def is_stt(block: dict) -> bool:
    return block.get("type", "") in STT_TYPES


def is_terminal(block: dict) -> bool:
    return block.get("type", "") in TERMINAL_TYPES


def is_branch(block: dict) -> bool:
    return block.get("type", "") in BRANCH_TYPES


# ─── YAMLインデックス構築 ────────────────────────────────────────────────────────

def build_index(sf: list) -> dict:
    """step名 → block dict のインデックスを作る。"""
    idx = {}
    for b in sf:
        step = b.get("step", "")
        if step:
            idx[step] = b
    return idx


def start_step(sf: list) -> str:
    """シナリオ開始ブロックを探す（type=opening または先頭）。"""
    for b in sf:
        if b.get("type") == "opening":
            return b.get("step", "")
    return sf[0].get("step", "") if sf else ""


# ─── inject値の決定 ─────────────────────────────────────────────────────────────

def inject_value_for_stt(block: dict, entering_label: str, defaults: dict) -> list[str]:
    """STTノードへの inject 値を決定する。"""
    step = block.get("step", "")
    btype = block.get("type", "")

    # 1. 呼び出し元の分岐ラベル（このノードに来るときの条件値）は inject には使わない
    #    → このノード「から出る」分岐ラベルを使う

    # 2. choices がある hearing → 最初の正常選択肢
    choices = block.get("choices", [])
    if choices:
        first = choices[0].get("label", "")
        if first:
            return [first]

    # 3. conditions がある → 最初の非エラー条件のラベル
    conds = block.get("conditions", [])
    normal_conds = [c for c in conds if c.get("match", "") not in ("other", "OTHER", "error", "ERROR")]
    if normal_conds:
        return [normal_conds[0].get("match", "")]

    # 4. save_to / type ヒューリスティック
    save_to = block.get("save_to", "")
    for key_part, val in defaults.items():
        if key_part in step or key_part in save_to or key_part in btype:
            if isinstance(val, list):
                return val[:1]
            return [str(val)]

    # 5. 固有型のデフォルト
    TYPE_DEFAULTS = {
        "dob":         ["19800101"],
        "phone":       ["09012345678"],
        "card_number": ["1234567"],
        "patient_name":["山田太郎"],
        "slot":        ["はい"],
        "free_text":   ["NO_RESULT"],
    }
    if btype in TYPE_DEFAULTS:
        return TYPE_DEFAULTS[btype]

    # 6. output_format ベース
    output_fmt = block.get("output_format", "")
    if output_fmt == "datetime":
        return ["来週の月曜日"]

    # 7. ステップ名・save_to キーワードによるヒューリスティック
    STEP_KEYWORDS = [
        (["予約日", "希望日", "変更日", "候補日", "ご希望日"], "来週の月曜日"),
        (["生年月日", "誕生日"],                               "19800101"),
        (["診療科", "科名"],                                   "内科"),
        (["氏名", "患者名", "お名前"],                         "山田太郎"),
        (["電話", "連絡先", "携帯"],                           "09012345678"),
        (["診察券"],                                           "1234567"),
        (["追加", "連絡事項", "備考"],                         "ないです"),
        (["理由", "キャンセル理由"],                           "特になし"),
        (["通院", "受診歴"],                                   "再診"),
        (["用件", "ご用件"],                                   "予約"),
        (["確認", "復唱", "よろしい"],                         "はい"),
    ]
    for keywords, val in STEP_KEYWORDS:
        if any(kw in step or kw in save_to for kw in keywords):
            return [val]

    return ["はい"]


# ─── DFS 経路列挙 ────────────────────────────────────────────────────────────────

class PathStep:
    __slots__ = ("step", "inject_key", "inject_val", "branch_label")

    def __init__(self, step: str, inject_key: str = "", inject_val: list = None,
                 branch_label: str = ""):
        self.step = step
        self.inject_key = inject_key
        self.inject_val = inject_val or []
        self.branch_label = branch_label


def dfs(
    step_name: str,
    idx: dict,
    defaults: dict,
    path: list,          # list[PathStep]
    visited: set,
    happy_only: bool,
    results: list,
    max_paths: int,
    depth: int = 0,
) -> None:
    if len(results) >= max_paths or depth >= MAX_DEPTH:
        return

    if step_name not in idx:
        results.append(list(path))
        return

    block = idx[step_name]
    btype = block.get("type", "")

    # 終端
    if is_terminal(block):
        terminal_ps = PathStep(step_name, "", [], "")
        results.append(list(path) + [terminal_ps])
        return

    # subflow は透過（visited に入れず next へ進む）
    if btype == "subflow":
        nxt_single = block.get("next", "")
        if nxt_single:
            dfs(nxt_single, idx, defaults, path, visited, happy_only, results, max_paths, depth + 1)
        else:
            results.append(list(path))
        return

    # ループ検出
    if step_name in visited:
        results.append(list(path))
        return

    visited = visited | {step_name}

    # STT 系: inject 情報を path に記録（inject 値は後でラベルで上書き）
    if is_stt(block):
        inject_key = f"入力_{block.get('save_to', step_name) or step_name}"
        ps = PathStep(step_name, inject_key, [], "")
        path = path + [ps]

    # conditions / choices で分岐
    conds = block.get("conditions", [])
    choices = block.get("choices", [])
    nxt_single = block.get("next", "")

    if conds:
        for cond in conds:
            match_label = cond.get("match", cond.get("label", ""))
            next_step = cond.get("next", "")

            # happy_only: other / error 分岐をスキップ
            if happy_only and match_label.lower() in ("other", "error"):
                continue

            if not next_step:
                continue

            # このSTTノードの inject 値を確定
            new_path = list(path)
            if new_path and new_path[-1].step == step_name and is_stt(block):
                ps_copy = PathStep(
                    new_path[-1].step,
                    new_path[-1].inject_key,
                    [match_label] if match_label else inject_value_for_stt(block, match_label, defaults),
                    match_label,
                )
                new_path[-1] = ps_copy

            dfs(next_step, idx, defaults, new_path, visited, happy_only, results, max_paths, depth + 1)

    elif choices:
        # N択 hearing: 各選択肢を別経路として列挙
        for ch in choices:
            label = ch.get("label", "")
            next_step = ch.get("next", nxt_single)
            if not next_step:
                next_step = nxt_single

            if happy_only and label.lower() in ("other", "error"):
                continue

            new_path = list(path)
            if new_path and new_path[-1].step == step_name and is_stt(block):
                ps_copy = PathStep(
                    new_path[-1].step,
                    new_path[-1].inject_key,
                    [label],
                    label,
                )
                new_path[-1] = ps_copy

            if next_step:
                dfs(next_step, idx, defaults, new_path, visited, happy_only, results, max_paths, depth + 1)
            else:
                results.append(new_path)

    elif nxt_single:
        # 単一 next（分岐なし）: inject は heuristic
        if path and path[-1].step == step_name and is_stt(block):
            ps_copy = PathStep(
                path[-1].step,
                path[-1].inject_key,
                inject_value_for_stt(block, "", defaults),
                "",
            )
            path = path[:-1] + [ps_copy]
        dfs(nxt_single, idx, defaults, path, visited, happy_only, results, max_paths, depth + 1)
    else:
        results.append(list(path))


# ─── cases JSON 構築 ─────────────────────────────────────────────────────────────

def path_to_case(path_steps: list, case_id: int, idx: dict) -> dict:
    """PathStep リストを cases JSON の 1 ケースに変換する。"""
    inject = {}
    labels = []

    for ps in path_steps:
        if ps.inject_key and ps.inject_val:
            inject[ps.inject_key] = ps.inject_val
        if ps.branch_label and ps.branch_label.lower() not in ("other", "error", ""):
            labels.append(ps.branch_label)

    # 終端ステップの名前
    terminal = ""
    for ps in reversed(path_steps):
        if ps.step in idx and is_terminal(idx[ps.step]):
            terminal = ps.step
            break
    if not terminal and path_steps:
        terminal = path_steps[-1].step

    label = " → ".join(labels[:5]) if labels else f"経路{case_id}"

    return {
        "id":     str(case_id),
        "dtmf":   str(case_id),
        "label":  label,
        "_path":  [ps.step for ps in path_steps],
        "inject": inject,
        "expect": {
            "終端": terminal,
            "checkpoints": [],
        },
    }


def dedup_inject_key(case: dict) -> str:
    """inject dict をキーにして重複排除する（terminal の違いは無視）。
    CMR など「コンテキストで分岐するノード」が同じ inject から複数終端を生成する場合、
    テストケースとしては inject が同一なら同一ケースとして扱う。"""
    return json.dumps(case["inject"], ensure_ascii=False, sort_keys=True)


# ─── メイン ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(description="設計書YAML → 全分岐 cases JSON")
    ap.add_argument("--yaml",       required=True, help="設計書 YAML パス")
    ap.add_argument("--out",        required=True, help="出力 cases JSON パス")
    ap.add_argument("--config",     help="hospital_config JSON（defaults/inject_pools 補完用）")
    ap.add_argument("--happy-only", action="store_true", help="正常経路（other除外）のみ")
    ap.add_argument("--max-paths",  type=int, default=200, help="出力上限（default: 200）")
    args = ap.parse_args()

    yaml_path = Path(args.yaml)
    if not yaml_path.exists():
        print(f"[ERROR] YAML not found: {yaml_path}", file=sys.stderr)
        return 1

    doc = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    sf = doc.get("scenario_flow", [])
    if not sf:
        print("[ERROR] scenario_flow が見つかりません。", file=sys.stderr)
        return 1

    # hospital_config から defaults/inject_pools を補完
    defaults: dict = {}
    cfg_meta: dict = {}
    if args.config:
        cfg_path = Path(args.config)
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            defaults = {**cfg.get("defaults", {}), **{k: v[0] if v else "" for k, v in cfg.get("inject_pools", {}).items()}}
            cfg_meta = {"facility": cfg.get("facility", ""), "flow": cfg.get("flow", "")}
            print(f"[INFO] hospital_config: {cfg_path.name} ({len(defaults)} defaults)", file=sys.stderr)
        else:
            print(f"[WARN] config not found: {cfg_path}", file=sys.stderr)

    # basic_info から施設・フロー名を取得
    bi = doc.get("basic_info", {})
    facility = cfg_meta.get("facility") or bi.get("facility_name", "")
    flow     = cfg_meta.get("flow")     or bi.get("flow_name", "")

    idx   = build_index(sf)
    start = start_step(sf)
    print(f"[INFO] start={start}, blocks={len(idx)}", file=sys.stderr)

    results: list = []
    dfs(start, idx, defaults, [], set(), args.happy_only, results, args.max_paths)

    # inject+terminal が同じケースを重複排除してから採番
    seen_keys: set[str] = set()
    deduped: list = []
    for path in results:
        c = path_to_case(path, 0, idx)
        key = dedup_inject_key(c)
        if key not in seen_keys:
            seen_keys.add(key)
            deduped.append(path)

    cases = [path_to_case(path, i + 1, idx) for i, path in enumerate(deduped)]

    output = {
        "_about": f"P7 全分岐ケース自動生成 — {facility} {flow}",
        "meta": {
            "facility":       facility,
            "flow":           flow,
            "entry_flow":     bi.get("entry_flow", flow),
            "version":        "3.0",
            "_generated_by":  "gen_branch_cases_from_yaml.py",
            "_happy_only":    args.happy_only,
        },
        "selector": {},
        "defaults": {},
        "cases":    cases,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] {len(cases)} cases → {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
