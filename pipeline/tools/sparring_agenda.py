#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""壁打ちアジェンダ生成（factory-v2 Phase 2 / 壁打ち入口の中核）。

メンバーの Claude が「壁打ち相手」として人間に渡すための、1 枚のチェックリストを作る。
3 つの決定論ゲート出力を 1 つに束ねる:

  1. qa_validator(設計書 YAML の完全性)  … 何が設計として足りないか（差し戻し票）
  2. drawio_to_scenario(surfacing)        … どの判定点が認定部品に配線できていないか（調達対象）
  3. parts_catalog.json(在庫)             … 今どの認定部品が調達できるか

壁打ち = 人間 + Claude でこのアジェンダを埋め、**生成物でなく生成器（設計書/部品）を直して再実行**する。
本ツールは設計書も成果物も書き換えない（読むだけ・アジェンダ md を 1 枚出すだけ）。

stdlib のみ・LLM 不使用。pip install 不要。
使い方:
  python3 tools/sparring_agenda.py <設計書.yaml> [--drawio <設計.drawio>] [-o <agenda.md>]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_VALIDATOR = REPO_ROOT / "schemas" / "qa_validator.py"
DRAWIO_TO_SCENARIO = REPO_ROOT / "scripts" / "drawio_to_scenario.py"
CATALOG = REPO_ROOT / "modules" / "parts_catalog.json"
REPORTS_DIR = REPO_ROOT / "output" / "reports"


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """サブプロセス実行（CRITICAL 検出で exit!=0 は想定内なので check しない）。"""
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", cwd=str(REPO_ROOT))


def collect_qa(yaml_path: Path) -> dict:
    """qa_validator --json-report を実行して完全性 CRITICAL を集める。

    fix_category="auto" の Issue があれば yaml_auto_fixer を1回かけて再実行し、
    アジェンダには「人間が壁打ちで直す残差」だけを載せる（決定論・LLM 不使用）。
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"qa_report_{yaml_path.stem}.json"

    def _qa_once() -> dict | None:
        proc = _run([sys.executable, str(QA_VALIDATOR), str(yaml_path), "--json-report", str(report_path)])
        if not report_path.exists():
            return {"ok": False, "error": (proc.stderr or proc.stdout or "qa_validator 実行失敗").strip()[:400], "issues": []}
        try:
            return json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return {"ok": False, "error": f"qa レポート parse 失敗: {exc}", "issues": []}

    data = _qa_once()
    if data.get("ok") is False:
        return data

    auto_fixed = []
    auto_issues = [i for i in data.get("issues", []) if i.get("fix_category") == "auto"]
    if auto_issues:
        fixer = REPO_ROOT / "scripts" / "yaml_auto_fixer.py"
        proc = _run([sys.executable, str(fixer), "--spec", str(yaml_path), "--report", str(report_path)])
        auto_fixed = [f"`{i.get('code', '?')}` {i.get('message', i.get('msg', ''))[:80]}" for i in auto_issues]
        if proc.returncode != 0:
            auto_fixed.append("⚠ yaml_auto_fixer が一部 Issue を適用できませんでした（stderr 参照）")
        data = _qa_once()  # 修正後の残差で再判定
        if data.get("ok") is False:
            data["auto_fixed"] = auto_fixed
            return data

    criticals = [i for i in data.get("issues", [])
                 if i.get("severity", i.get("level")) == "CRITICAL"]
    return {"ok": True, "criticals": criticals, "counts": data.get("counts", {}),
            "report_path": report_path, "auto_fixed": auto_fixed}


def collect_surfacing(drawio_path: Path) -> dict:
    """drawio_to_scenario --json を実行して surfacing findings を集める。"""
    proc = _run([sys.executable, str(DRAWIO_TO_SCENARIO), str(drawio_path), "--json"])
    out = proc.stdout.strip()
    if not out:
        return {"ok": False, "error": (proc.stderr or "drawio_to_scenario 出力なし").strip()[:400], "findings": []}
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"surfacing JSON parse 失敗: {exc}", "findings": []}
    findings = [f for f in data.get("findings", []) if f.get("severity") in ("CRITICAL", "WARN")]
    return {
        "ok": True,
        "findings": findings,
        "n_nodes": data.get("n_nodes", 0),
        "n_surfaces": data.get("n_surfaces", 0),
    }


def load_catalog() -> dict:
    if not CATALOG.exists():
        return {"ok": False, "parts": []}
    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "parts": []}
    data["ok"] = True
    return data


def _procurable(catalog: dict) -> tuple[list, list]:
    """在庫を「調達可（certified）」と「登録待ち（pending）」に分ける。"""
    certified, pending = [], []
    for p in catalog.get("parts", []):
        labels = "/".join(p.get("output_labels", [])) or "—"
        line = f"`{p['part_id']}`（{labels}）"
        if p.get("status") == "certified":
            certified.append(line)
        elif p.get("status") in ("pending_registration", "engine_only"):
            pending.append(f"{line} [{p.get('status')}]")
    return certified, pending


def render(yaml_path: Path, qa: dict, surf: dict | None, catalog: dict) -> str:
    scenario = yaml_path.stem.replace("設計書_", "")
    L = []
    L.append(f"# 壁打ちアジェンダ — {scenario}")
    L.append("")
    L.append(
        "> 入口スキルが生成（`tools/sparring_agenda.py`）。qa_validator(完全性) + surfacing(調達) + "
        "部品カタログ(在庫) を 1 枚に束ねたもの。**壁打ち = 人間 + Claude でこれを埋め、生成物でなく生成器"
        "（設計書 YAML・部品）を直して再実行**する。本アジェンダは指針であり、設計書は壁打ちで直す。"
    )
    L.append("")

    # 1. 完全性（qa CRITICAL）
    L.append("## 1. 設計の不備（qa_validator CRITICAL）= 壁打ちで埋める")
    if qa.get("auto_fixed"):
        L.append(f"- 🔧 yaml_auto_fixer が {len(qa['auto_fixed'])} 件を機械修正済み（下記は修正後の残差）:")
        for a in qa["auto_fixed"]:
            L.append(f"  - {a}")
    if not qa.get("ok"):
        L.append(f"- ⚠ qa_validator を実行できませんでした: {qa.get('error', '')}")
    elif not qa.get("criticals"):
        L.append("- ✅ CRITICAL なし（完全性ゲート PASS）。")
    else:
        for i in qa["criticals"]:
            L.append(f"- [ ] `{i.get('code', '?')}` {i.get('message', i.get('msg', ''))}")
    L.append("")

    # 2. 調達対象（surfacing）
    L.append("## 2. 決定論で解けていない判定点（surfacing）= 調達対象")
    if surf is None:
        L.append("- （drawio 未指定のため surfacing 監査はスキップ。`--drawio` で有効化）")
    elif not surf.get("ok"):
        L.append(f"- ⚠ surfacing を実行できませんでした: {surf.get('error', '')}")
    elif not surf.get("findings"):
        L.append(f"- ✅ 未配線/未知ラベルの判定点なし（ノード {surf.get('n_nodes', 0)} / 認定 surface {surf.get('n_surfaces', 0)}）。")
    else:
        for f in surf["findings"]:
            mark = "🟥" if f.get("severity") == "CRITICAL" else "🟧"
            L.append(f"- {mark} `{f.get('code', '?')}` {f.get('step', '')}: {f.get('message', '')}")
    L.append("")

    # 3. 在庫（カタログ）
    L.append("## 3. 調達できる在庫（部品カタログ）")
    if not catalog.get("ok"):
        L.append("- ⚠ parts_catalog.json が無い/壊れています。`python3 tools/generate_parts_catalog.py` で生成してください。")
    else:
        certified, pending = _procurable(catalog)
        L.append(f"**認定済（そのまま調達可・{len(certified)}件）**: " + ("、".join(certified) if certified else "—"))
        L.append("")
        L.append(f"**登録待ち/engine のみ（要・人間ゲート・{len(pending)}件）**: " + ("、".join(pending) if pending else "—"))
    L.append("")

    # 4. 次アクション
    L.append("## 4. 次アクション")
    qa_blocked = qa.get("ok") and qa.get("criticals")
    surf_blocked = surf is not None and surf.get("ok") and surf.get("findings")
    actions = []
    if qa_blocked:
        actions.append("上記 §1 の不備を**壁打ちで設計書 YAML に反映** → このスキルを再実行（生成器を直す）。")
    if surf_blocked:
        actions.append("§2 の判定点を §3 の在庫で賄えるか確認。**賄えなければ `@工場長` に新部品調達（Case B）を依頼**。")
    if not actions:
        try:
            spec_ref = yaml_path.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            spec_ref = str(yaml_path)  # repo 外（テスト等）は絶対パスのまま
        actions.append(f"✅ ゲート PASS。ビルドへ: `python3 scripts/orchestrator.py --pattern 1 --spec {spec_ref}`")
        actions.append("テスト後の残差・起票・調達は `@工場長` が担当。")
    for n, a in enumerate(actions, 1):
        L.append(f"{n}. {a}")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description="壁打ちアジェンダ（qa + surfacing + 部品カタログ）を生成")
    ap.add_argument("yaml", help="設計書 YAML パス")
    ap.add_argument("--drawio", help="設計 drawio パス（surfacing 監査を有効化）")
    ap.add_argument("-o", "--out", help="アジェンダ md の出力先（既定: 設計書と同じフォルダ）")
    args = ap.parse_args()

    yaml_path = Path(args.yaml).resolve()
    if not yaml_path.exists():
        print(f"設計書が見つかりません: {yaml_path}", file=sys.stderr)
        return 1

    qa = collect_qa(yaml_path)
    surf = collect_surfacing(Path(args.drawio).resolve()) if args.drawio else None
    catalog = load_catalog()

    agenda = render(yaml_path, qa, surf, catalog)
    out_path = Path(args.out).resolve() if args.out else yaml_path.parent / f"sparring_agenda_{yaml_path.stem.replace('設計書_', '')}.md"
    out_path.write_text(agenda, encoding="utf-8")
    print(f"[壁打ちアジェンダ] {out_path}")
    if qa.get("ok"):
        print(f"  qa CRITICAL={len(qa.get('criticals', []))}", end="")
    if surf is not None and surf.get("ok"):
        print(f" / surfacing findings={len(surf.get('findings', []))}", end="")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
