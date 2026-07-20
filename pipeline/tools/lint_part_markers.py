#!/usr/bin/env python3
"""部品規格マーカー リンタ — 正本(@part-id / @spec) と part.json の整合を機械検査する。

仕様: docs/governance/part-certification-spec.md（engine/spec 二段判定ゲート v2）

検査項目（modules/*/part.json を持つ各部品）:
  1. // @part-id マーカーがディレクトリ名・part.json.part_id と一致
  2. part.json.spec_vars の各 var 宣言が必ず @spec-begin..@spec-end ブロック内にある
  3. part.json.wiring_vars の各 var 宣言が @spec ブロックの外にある
  4. engine 領域（@spec ブロック・wiring 行・コメントを除いた残り）に placeholder
     （{{...}} / __NAME__）が無い ← engine_hash を充填で不変に保つ不変条件
  5. 正本の engine_hash が certified_hashes.json の parts.engine_hash と一致
     （不一致 = エンジン改変 → 意図的なら台帳更新で再認定、そうでなければ事故）

exit 0 = 全 OK / 1 = 違反あり。CI / pre-commit / 手動で実行する。
  実行: python tools/lint_part_markers.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import orchestrator as o  # noqa: E402  (_engine_spec_hashes / _read_part_marker)

PLACEHOLDER = re.compile(r"\{\{|__[A-Z][A-Z0-9_]*__")


def _spec_line_set(text):
    """@spec ブロック内の行インデックス集合を返す。"""
    lines = text.replace("\r\n", "\n").split("\n")
    inside, on = set(), False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("// @spec-begin"):
            on = True
            continue
        if s.startswith("// @spec-end"):
            on = False
            continue
        if on:
            inside.add(i)
    return lines, inside


def _engine_region_text(text, wiring):
    lines = text.replace("\r\n", "\n").split("\n")
    out, on = [], False
    wre = re.compile(r"^\s*var\s+(" + "|".join(map(re.escape, wiring)) + r")\s*=") if wiring else None
    for ln in lines:
        s = ln.strip()
        if s.startswith("// @spec-begin"):
            on = True
            continue
        if s.startswith("// @spec-end"):
            on = False
            continue
        if s.startswith("//"):
            continue
        if on:
            continue
        if wre and wre.match(ln):
            continue
        out.append(ln)
    return "\n".join(out)


def lint_part(part_dir: Path, reg_parts: dict):
    pid = part_dir.name
    man = json.loads((part_dir / "part.json").read_text(encoding="utf-8"))
    wiring = man.get("wiring_vars", [])
    specv = man.get("spec_vars", [])
    errs = []

    sjs = part_dir / "script.js"
    if not sjs.exists():
        return [f"{pid}: script.js が無い"]
    txt = sjs.read_text(encoding="utf-8")

    marker_id, _ver = o._read_part_marker(txt)
    if marker_id != pid:
        errs.append(f"@part-id={marker_id!r} がディレクトリ名 {pid!r} と不一致")
    if man.get("part_id") != pid:
        errs.append(f"part.json.part_id={man.get('part_id')!r} がディレクトリ名と不一致")

    lines, inside = _spec_line_set(txt)
    for v in specv:
        idx = [i for i, l in enumerate(lines) if re.match(r"^\s*var\s+" + re.escape(v) + r"\s*=", l)]
        if not idx:
            errs.append(f"spec_var {v}: var 宣言が見つからない")
        elif not all(i in inside for i in idx):
            errs.append(f"spec_var {v}: @spec ブロックの外にある")
    for w in wiring:
        idx = [i for i, l in enumerate(lines) if re.match(r"^\s*var\s+" + re.escape(w) + r"\s*=", l)]
        if any(i in inside for i in idx):
            errs.append(f"wiring_var {w}: @spec ブロックの中にある（除外対象なのに）")

    eng = _engine_region_text(txt, wiring)
    m = PLACEHOLDER.search(eng)
    if m:
        errs.append(f"engine 領域に placeholder {m.group(0)!r} がある（wiring/spec へ移すこと）")

    eh, sh = o._engine_spec_hashes(txt, wiring)
    cert = reg_parts.get(pid, {}).get("engine_hash")
    if cert and cert != eh:
        errs.append(f"engine_hash ドリフト（正本 {eh[:12]}… != 認定 {cert[:12]}…）= エンジン改変。意図的なら certified_hashes.json を更新")
    return errs, eh, sh


def main():
    reg_path = ROOT / "modules" / "certified_hashes.json"
    reg_parts = {}
    if reg_path.exists():
        reg_parts = json.loads(reg_path.read_text(encoding="utf-8")).get("parts", {})

    part_jsons = sorted((ROOT / "modules").glob("*/part.json"))
    violations = 0
    for pj in part_jsons:
        res = lint_part(pj.parent, reg_parts)
        if isinstance(res, list):
            violations += 1
            print(f"[FAIL] {pj.parent.name}")
            for e in res:
                print(f"    - {e}")
            continue
        errs, eh, sh = res
        if errs:
            violations += 1
            print(f"[FAIL] {pj.parent.name}")
            for e in errs:
                print(f"    - {e}")
        else:
            print(f"[ OK ] {pj.parent.name}  engine={eh[:12]}… spec={sh[:12]}…")
    print(f"\n{len(part_jsons)} parts checked, {violations} violation(s)")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
