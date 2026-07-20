#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""部品カタログ INDEX 生成ツール（factory-v2 Phase 2 / 工場長の「部品調達」基盤）。

工場長エージェントと壁打ち入口が「今どの認定部品が使えるか」を機械的に
列挙できるようにするための、単一の機械可読カタログ index を生成する。

SSoT（手編集する正本）はあくまで:
  - modules/certified_hashes.json  … parts(engine 刻印) + specs(認定台帳)
  - modules/<part>/part.json        … output_labels / wiring_vars / spec_vars / specs

本ツールはそれらを READ するだけで、SSoT を一切書き換えない。出力:
  - modules/parts_catalog.json   … 機械可読 index（工場長/入口が読む）
  - modules/PARTS_CATALOG.md     … 人間向けサマリ表

status の定義（調達可否の正直な表現）:
  - certified            : certified_hashes.parts に engine 登録済み かつ specs に ≥1 認定規格あり
  - engine_only          : certified_hashes.parts に engine 登録済みだが認定 spec が無い（実機待ち）
  - pending_registration : part.json + oracle はあるが certified_hashes.parts 未登録（engine_hash 計算済み・登録待ち）
  - oracle_only          : oracle.py はあるが part.json も certified 登録も無い（非標準の認定経路 等）
  - draft                : modules dir はあるが part.json も oracle も無い（雛形のみ）

LLM 不使用・stdlib のみ（決定論）。pip install 不要。
使い方: python3 tools/generate_parts_catalog.py [--check]
  --check : 既存の parts_catalog.json と差分が無いか検証（CI / pre-commit 用・書き換えない）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULES_DIR = REPO_ROOT / "modules"
CERTIFIED_HASHES = MODULES_DIR / "certified_hashes.json"
OUT_JSON = MODULES_DIR / "parts_catalog.json"
OUT_MD = MODULES_DIR / "PARTS_CATALOG.md"

# modules/ 直下で「部品」ではない作業用ディレクトリは除外する
NON_PART_DIRS = {"__pycache__", "session_object_probe"}


def _rel(p: Path) -> str:
    """REPO_ROOT 相対の POSIX パス文字列。"""
    return p.relative_to(REPO_ROOT).as_posix()


def _load_certified_hashes() -> dict:
    if not CERTIFIED_HASHES.exists():
        return {"parts": {}, "specs": {}}
    data = json.loads(CERTIFIED_HASHES.read_text(encoding="utf-8"))
    return {"parts": data.get("parts", {}), "specs": data.get("specs", {})}


def _extract_purpose(module_dir: Path) -> str:
    """REQUIREMENTS.md の最初の H1 見出し（無ければ最初の非空行）を 1 行用途として抜く。"""
    req = module_dir / "REQUIREMENTS.md"
    if not req.exists():
        return ""
    first_nonempty = ""
    for line in req.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        if not first_nonempty:
            first_nonempty = s
        if s.startswith("# "):
            return s.lstrip("#").strip()
    # H1 が無ければ最初の非空行（先頭の # は剥がす）
    return first_nonempty.lstrip("#").strip()


def _specs_for_engine(engine_hash: str, specs: dict) -> list[dict]:
    """certified_hashes.specs から、この engine_hash に紐づく認定規格を列挙。"""
    out = []
    for combo_key, meta in specs.items():
        if ":" not in combo_key:
            continue
        e_hash, s_hash = combo_key.split(":", 1)
        if e_hash != engine_hash:
            continue
        out.append(
            {
                "spec_label": meta.get("spec_label", ""),
                "spec_hash": s_hash,
                "cases": meta.get("cases", ""),
                "certified_date": meta.get("certified_date", ""),
                "scenario": meta.get("scenario", ""),
            }
        )
    out.sort(key=lambda d: (d.get("certified_date", ""), d.get("spec_label", "")))
    return out


def _compute_status(*, in_parts: bool, certified_specs: list, has_part_json: bool, has_oracle: bool) -> str:
    if in_parts:
        return "certified" if certified_specs else "engine_only"
    if has_part_json and has_oracle:
        return "pending_registration"
    if has_oracle:
        return "oracle_only"
    return "draft"


def build_catalog() -> dict:
    ch = _load_certified_hashes()
    parts_reg: dict = ch["parts"]
    specs_reg: dict = ch["specs"]

    # 走査対象 = modules/ 直下のディレクトリ（部品でない作業 dir は除外）
    module_dirs = sorted(
        d for d in MODULES_DIR.iterdir()
        if d.is_dir() and d.name not in NON_PART_DIRS
    )

    parts_out: list[dict] = []
    for d in module_dirs:
        name = d.name
        part_json_path = d / "part.json"
        oracle_path = d / "oracle.py"
        test_oracle_path = d / "test_oracle.py"
        has_part_json = part_json_path.exists()
        has_oracle = oracle_path.exists()

        # part.json が無く oracle も無い（REQUIREMENTS だけ等）= 部品台帳に載せない
        if not has_part_json and not has_oracle:
            continue

        part_json: dict = {}
        if has_part_json:
            try:
                part_json = json.loads(part_json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:  # 壊れた part.json は status に出して継続
                part_json = {"_parse_error": str(exc)}

        reg_entry = parts_reg.get(name, {})
        engine_hash = reg_entry.get("engine_hash", "")
        engine_version = reg_entry.get("engine_version") or part_json.get("engine_version", "")
        certified_specs = _specs_for_engine(engine_hash, specs_reg) if engine_hash else []

        # part.json 側で宣言されている規格（未認定含む）
        declared_specs = []
        for label, meta in (part_json.get("specs") or {}).items():
            declared_specs.append(
                {
                    "spec_label": label,
                    "cases": meta.get("cases", ""),
                    "filled_script": meta.get("filled_script", ""),
                    "note": meta.get("note", ""),
                }
            )

        status = _compute_status(
            in_parts=name in parts_reg,
            certified_specs=certified_specs,
            has_part_json=has_part_json,
            has_oracle=has_oracle,
        )

        parts_out.append(
            {
                "part_id": part_json.get("part_id", name),
                "module_dir": _rel(d),
                "status": status,
                "engine_version": engine_version,
                "purpose": _extract_purpose(d),
                "output_labels": part_json.get("output_labels", []),
                "wiring_vars": part_json.get("wiring_vars", []),
                "spec_vars": part_json.get("spec_vars", []),
                "engine_hash": engine_hash,
                "oracle": _rel(oracle_path) if has_oracle else "",
                "test_oracle": _rel(test_oracle_path) if test_oracle_path.exists() else "",
                "certified_specs": certified_specs,
                "declared_specs": declared_specs,
                "part_json": _rel(part_json_path) if has_part_json else "",
            }
        )

    parts_out.sort(key=lambda p: (p["status"] != "certified", p["part_id"]))

    summary: dict = {"total": len(parts_out)}
    for p in parts_out:
        summary[p["status"]] = summary.get(p["status"], 0) + 1

    return {
        "_doc": (
            "自動生成カタログ INDEX（factory-v2 Phase 2）。SSoT は modules/certified_hashes.json + "
            "各 modules/<part>/part.json。手編集しない。再生成: python3 tools/generate_parts_catalog.py。"
            "工場長エージェント / 壁打ち入口が『調達可能な認定部品』を機械的に列挙するために読む。"
        ),
        "generated_from": {
            "certified_hashes": _rel(CERTIFIED_HASHES),
            "part_jsons": sum(1 for p in parts_out if p["part_json"]),
        },
        "summary": summary,
        "parts": parts_out,
    }


_STATUS_JP = {
    "certified": "認定済（調達可）",
    "engine_only": "engine登録のみ・実機待ち",
    "pending_registration": "oracle有・登録待ち",
    "oracle_only": "oracle有・part.json無（別経路）",
    "draft": "雛形のみ",
}


def render_md(catalog: dict) -> str:
    lines = []
    lines.append("# 部品カタログ（自動生成 — 手編集しない）")
    lines.append("")
    lines.append(
        "> `tools/generate_parts_catalog.py` が `certified_hashes.json` + 各 `part.json` から生成。"
        "工場長・壁打ち入口が「調達可能な認定部品」を引くための index。SSoT はあくまで certified_hashes.json + part.json。"
    )
    lines.append("")
    s = catalog["summary"]
    summary_bits = [f"総数 {s.get('total', 0)}"] + [
        f"{_STATUS_JP.get(k, k)} {v}" for k, v in s.items() if k != "total"
    ]
    lines.append("**サマリ**: " + " / ".join(summary_bits))
    lines.append("")
    lines.append("| 部品 | status | engine_ver | 出力ラベル(branch surface) | 認定規格数 | 用途 |")
    lines.append("|---|---|---|---|---|---|")
    for p in catalog["parts"]:
        labels = "、".join(p["output_labels"]) if p["output_labels"] else "—"
        purpose = (p["purpose"] or "").replace("|", "/")
        if len(purpose) > 48:
            purpose = purpose[:47] + "…"
        lines.append(
            f"| `{p['part_id']}` | {_STATUS_JP.get(p['status'], p['status'])} | "
            f"{p['engine_version'] or '—'} | {labels} | {len(p['certified_specs'])} | {purpose or '—'} |"
        )
    lines.append("")
    return "\n".join(lines)


def _canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="部品カタログ INDEX を生成する")
    ap.add_argument(
        "--check",
        action="store_true",
        help="既存の parts_catalog.json / PARTS_CATALOG.md と一致するか検証（書き換えない）。差分があれば exit 1。",
    )
    args = ap.parse_args()

    catalog = build_catalog()
    json_text = _canonical(catalog)
    md_text = render_md(catalog)

    if args.check:
        ok = True
        for path, text in ((OUT_JSON, json_text), (OUT_MD, md_text)):
            current = path.read_text(encoding="utf-8") if path.exists() else ""
            if current != text:
                ok = False
                print(f"[DRIFT] {_rel(path)} が SSoT と不一致。`python3 tools/generate_parts_catalog.py` で再生成してください。")
        if ok:
            print("[OK] parts_catalog は SSoT と一致しています。")
            return 0
        return 1

    OUT_JSON.write_text(json_text, encoding="utf-8")
    OUT_MD.write_text(md_text, encoding="utf-8")
    s = catalog["summary"]
    print(f"[generated] {_rel(OUT_JSON)} / {_rel(OUT_MD)}")
    print(f"  部品 {s.get('total', 0)} 件: " + ", ".join(
        f"{k}={v}" for k, v in s.items() if k != "total"
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
