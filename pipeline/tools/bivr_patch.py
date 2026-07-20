#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""bivr_patch.py — Pattern 2 外科的修正の決定論実行器（docs/specs/bivr-patch-dsl.md v1）

人間が承認した patch YAML を、既存フロー JSON へ原文どおり適用する。
LLM 不使用・fail-closed:
  - 全 op を先に検証し、1 件でもエラーなら何も書かない（部分適用なし）
  - expect ガード: 現在値が一致しない op があれば全体中止（古い patch の誤適用防止）

使い方:
  # 壁打ちレビュー用（変更一覧のみ表示・書き込みなし）
  python3 tools/bivr_patch.py --json <flow.json> --patch <patch.yaml> --dry-run

  # 適用（既定は in-place。--out で別ファイルへ）
  python3 tools/bivr_patch.py --json <flow.json> --patch <patch.yaml> --apply \\
      [--out <out.json>] [--report <report.md>]

終了コード: 0=成功 / 2=検証エラー（レポート参照・未適用）
stdout 最終行: {"touched": [モジュール名...]}（orchestrator が validator scope に使う）
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が必要です。", file=sys.stderr)
    sys.exit(1)

SUPPORTED_OPS = ("set_next", "set_param", "set_type")


class PatchError(Exception):
    pass


def _find_slot(next_list: list, op: dict) -> int:
    """set_next の対象スロットを 1 つに特定する（slot 1-based / label / condition）。"""
    if "slot" in op:
        idx = int(op["slot"]) - 1
        if idx < 0 or idx >= len(next_list):
            raise PatchError(f"slot={op['slot']} が範囲外です（next は {len(next_list)} スロット）")
        return idx
    key, field = (("label", "label") if "label" in op else
                  ("condition", "condition") if "condition" in op else (None, None))
    if key is None:
        raise PatchError("set_next には slot / label / condition のいずれかが必要です")
    matches = [i for i, s in enumerate(next_list)
               if str((s or {}).get(field, "")) == str(op[key])]
    if len(matches) != 1:
        raise PatchError(
            f"{field}='{op[key]}' に一致するスロットが {len(matches)} 件"
            f"（1 件に特定できません — slot 番号で指定してください）")
    return matches[0]


def validate_and_plan(modules: dict, patches: list) -> list[dict]:
    """全 op を検証し、適用計画 [{desc, apply(fn)}] を返す。エラーは PatchError 集約。"""
    plan = []
    errors = []
    for i, op in enumerate(patches, 1):
        try:
            kind = op.get("op", "")
            if kind not in SUPPORTED_OPS:
                raise PatchError(f"未知の op '{kind}'（対応: {', '.join(SUPPORTED_OPS)}）")
            mname = op.get("module", "")
            if mname not in modules:
                raise PatchError(f"モジュール '{mname}' が JSON に存在しません")
            mod = modules[mname]

            if kind == "set_next":
                if "next" not in op:
                    raise PatchError("set_next には next が必要です")
                next_list = mod.get("next") or []
                idx = _find_slot(next_list, op)
                current = str((next_list[idx] or {}).get("nextModuleName", ""))
                new = str(op["next"])
                if "expect" in op and current != str(op["expect"]):
                    raise PatchError(
                        f"expect 不一致: next[{idx + 1}].nextModuleName は"
                        f" '{current}'（patch の期待値 '{op['expect']}'）")
                if new and new not in modules:
                    raise PatchError(f"遷移先 '{new}' が JSON に存在しません")
                desc = (f"set_next  {mname}.next[{idx + 1}]"
                        f" ({next_list[idx].get('condition', '')}) : '{current}' → '{new}'")

                def apply(m=mod, i2=idx, v=new):
                    m["next"][i2]["nextModuleName"] = v
                plan.append({"module": mname, "desc": desc, "apply": apply})

            elif kind == "set_param":
                pkey = op.get("param", "")
                if not pkey or "value" not in op:
                    raise PatchError("set_param には param と value が必要です")
                params = mod.setdefault("params", {})
                current = str(params.get(pkey, ""))
                new = str(op["value"])
                if "expect" in op and current != str(op["expect"]):
                    raise PatchError(
                        f"expect 不一致: params.{pkey} は '{current}'"
                        f"（patch の期待値 '{op['expect']}'）")
                desc = f"set_param {mname}.params.{pkey} : '{current}' → '{new}'"

                def apply(p=params, k=pkey, v=new):
                    p[k] = v
                plan.append({"module": mname, "desc": desc, "apply": apply})

            elif kind == "set_type":
                new_type = op.get("type", "")
                if not new_type:
                    raise PatchError("set_type には type が必要です")
                current = str(mod.get("type", ""))
                if "expect" in op and current != str(op["expect"]):
                    raise PatchError(
                        f"expect 不一致: type は '{current}'（patch の期待値 '{op['expect']}'）")
                new_params = op.get("params")  # None = 既存 params 温存
                desc = (f"set_type  {mname}.type : '{current}' → '{new_type}'"
                        + (" (params 全置換)" if new_params is not None else ""))

                def apply(m=mod, t=new_type, np=new_params):
                    m["type"] = t
                    if np is not None:
                        m["params"] = dict(np)
                plan.append({"module": mname, "desc": desc, "apply": apply})

        except PatchError as e:
            errors.append(f"patch #{i} ({op.get('op', '?')} {op.get('module', '?')}): {e}")

    if errors:
        raise PatchError("\n".join(errors))
    return plan


def main() -> int:
    ap = argparse.ArgumentParser(description="patch YAML を既存フロー JSON へ決定論適用する")
    ap.add_argument("--json", required=True, help="対象フロー JSON（modules 辞書を持つ）")
    ap.add_argument("--patch", required=True, help="patch YAML（top-level patches:）")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="変更一覧のみ表示（書き込みなし）")
    mode.add_argument("--apply", action="store_true", help="適用して書き込む")
    ap.add_argument("--out", default=None, help="出力先（省略時 in-place）")
    ap.add_argument("--report", default=None, help="監査レポート md の出力先")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    json_path = Path(args.json)
    patch_path = Path(args.patch)
    for p, label in ((json_path, "JSON"), (patch_path, "patch YAML")):
        if not p.exists():
            print(f"[ERROR] {label} が見つかりません: {p}", file=sys.stderr)
            return 2

    data = json.loads(json_path.read_text(encoding="utf-8"))
    modules = data.get("modules")
    if not isinstance(modules, dict):
        print("[ERROR] JSON に modules 辞書がありません（フロー JSON を指定してください）",
              file=sys.stderr)
        return 2

    spec = yaml.safe_load(patch_path.read_text(encoding="utf-8")) or {}
    patches = spec.get("patches")
    if not isinstance(patches, list) or not patches:
        print("[ERROR] patch YAML に patches: リストがありません", file=sys.stderr)
        return 2
    target_flow = spec.get("target_flow")
    if target_flow and data.get("name") and str(data["name"]) != str(target_flow):
        print(f"[ERROR] target_flow 不一致: patch は '{target_flow}' 用ですが"
              f" JSON は '{data['name']}' です", file=sys.stderr)
        return 2

    try:
        plan = validate_and_plan(modules, patches)
    except PatchError as e:
        print("[ERROR] patch 検証失敗 — 何も適用していません（fail-closed）:", file=sys.stderr)
        print(str(e), file=sys.stderr)
        return 2

    header = f"[bivr_patch] {patch_path.name} → {json_path.name}: {len(plan)} 変更"
    print(header, file=sys.stderr)
    for item in plan:
        print(f"  {item['desc']}", file=sys.stderr)

    touched = sorted({item["module"] for item in plan})

    if args.dry_run:
        print("[bivr_patch] dry-run（書き込みなし）", file=sys.stderr)
        print(json.dumps({"touched": touched}, ensure_ascii=False))
        return 0

    for item in plan:
        item["apply"]()

    out_path = Path(args.out) if args.out else json_path
    out_path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                        encoding="utf-8")
    print(f"[bivr_patch] 適用完了 → {out_path}", file=sys.stderr)

    if args.report:
        rp = Path(args.report)
        rp.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# bivr_patch 適用レポート", "",
                 f"- patch: `{patch_path}`", f"- 対象: `{json_path}` → `{out_path}`",
                 f"- 変更数: {len(plan)} / touched モジュール: {', '.join(touched)}", ""]
        lines += [f"- {item['desc']}" for item in plan]
        rp.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[bivr_patch] レポート → {rp}", file=sys.stderr)

    print(json.dumps({"touched": touched}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
