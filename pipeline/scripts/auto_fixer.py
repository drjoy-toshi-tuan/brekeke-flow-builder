#!/usr/bin/env python3
"""
auto_fixer.py -- 機械的修正（fix_category="auto"）を適用する

validator.py が出力した JSON レポート（--json-report で生成）を読み込み、
fix_category="auto" の Issue に付いている fix_action を順番に JSON フローに適用する。
LLM を通さず決定論的に処理するため、トークン消費ゼロで高速。

対応 op:
  - set        : path で指定したフィールドに value を書き込む
  - replace    : path の文字列値に対し find → replace 置換
  - recalc_layout : layout_calculator.py を呼んでレイアウトを再計算
                    （スクリプト内では処理せずフラグだけ返し、呼び出し側に任せる）
  - deoverlap_layout : 同一座標に重複配置されたモジュールをずらして解消
  - dedup_displaytype : saveContextModel2DB の params.fields（JSON文字列）で
                        重複不可 displayType の衝突を解消。keep_context を残し
                        他を fallback_type（通常 TEXT）に置換（CTX-017 対応）
  - rename_module : OpenAI_* と命名された決定論 Script モジュールを script_* へ改名し、
                    全参照を追従（SCR-001 / issue #236 / #348）

Usage:
    python3 scripts/auto_fixer.py --json <flow.json> --report <validator_report.json> [--spec <spec.yaml>]

    --spec: layout 再計算に使う設計書 YAML（recalc_layout op 時のみ必須）
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Windows の cp932 化け対策（Issue #225）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rename_openai_modules import (  # noqa: E402
    apply_rename_mapping,
    expand_mapping_with_aux,
)


def _apply_rename_module(data: dict, old: str, new: str) -> tuple[bool, str]:
    """OpenAI_* な Script を script_* へ改名し全参照を追従（issue #236）。"""
    if not old or not new:
        return False, "old/new が空"
    if old not in data.get("modules", {}):
        return False, f"対象モジュール '{old}' が存在しない（既に改名済み？）"
    mapping = expand_mapping_with_aux(data, {old: new})
    changes = apply_rename_mapping(data, mapping)
    if not changes:
        return False, "変更なし"
    return True, f"'{old}' → '{new}'（補助含め {len(mapping)} 名 / 参照追従）"


def _apply_set(data: dict, path: list, value) -> tuple[bool, str]:
    """path (["modules", m, "params", "status"] 等) に従って value をセット"""
    if not path:
        return False, "path が空"
    cur = data
    for key in path[:-1]:
        if isinstance(cur, dict):
            if key not in cur:
                return False, f"path {path} の途中 '{key}' が存在しない"
            cur = cur[key]
        elif isinstance(cur, list):
            try:
                cur = cur[int(key)]
            except (ValueError, IndexError):
                return False, f"path {path} のリスト index '{key}' が不正"
        else:
            return False, f"path {path} を辿れない（型 {type(cur).__name__}）"
    last = path[-1]
    if isinstance(cur, dict):
        old = cur.get(last, "(未設定)")
        cur[last] = value
        return True, f"{'.'.join(str(p) for p in path)} : {old!r} → {value!r}"
    elif isinstance(cur, list):
        try:
            idx = int(last)
            old = cur[idx] if 0 <= idx < len(cur) else "(範囲外)"
            cur[idx] = value
            return True, f"{'.'.join(str(p) for p in path)} : {old!r} → {value!r}"
        except (ValueError, IndexError):
            return False, f"末尾 index '{last}' が不正"
    return False, "末尾の型が不正"


def _apply_replace(data: dict, path: list, find: str, replace: str) -> tuple[bool, str]:
    """path の文字列値に対して find → replace"""
    cur = data
    for key in path[:-1]:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return False, f"path {path} を辿れない"
    last = path[-1]
    if isinstance(cur, dict) and isinstance(cur.get(last), str):
        val = cur[last]
        new = val.replace(find, replace)
        if new == val:
            return False, f"{'.'.join(str(p) for p in path)} : 置換対象なし"
        cur[last] = new
        return True, f"{'.'.join(str(p) for p in path)} : {val.count(find)} 箇所置換"
    return False, "文字列ではない"


def _apply_dedup_displaytype(data: dict, path: list, display_type: str,
                             keep_context: str, fallback_type: str) -> tuple[bool, str]:
    """saveContextModel2DB の params.fields（JSON string）内で重複不可 displayType の衝突を解消。

    path は通常 ["modules", "<モジュール名>", "params", "fields"] を指す。
    display_type の付いた field のうち contextName==keep_context を残し、
    他を fallback_type（通常 TEXT）に置換する。
    keep_context が見つからなければ先頭のみ残す。
    """
    cur = data
    for key in path[:-1]:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return False, f"path {path} を辿れない"
    last = path[-1]
    if not isinstance(cur, dict) or last not in cur:
        return False, f"path 末尾 '{last}' が存在しない"
    fields_str = cur[last]
    if not isinstance(fields_str, str):
        return False, "fields が JSON 文字列ではない"
    try:
        fields_obj = json.loads(fields_str)
    except (json.JSONDecodeError, TypeError) as e:
        return False, f"fields JSON パース失敗: {e}"
    if not isinstance(fields_obj, list):
        return False, "fields は配列である必要がある"

    # 該当 displayType を持つ field のインデックスを集める
    targets = [i for i, f in enumerate(fields_obj)
               if isinstance(f, dict) and f.get("displayType") == display_type]
    if len(targets) <= 1:
        return True, f"displayType '{display_type}' の重複なし（{len(targets)}件）"

    # keep_context を含むものを残す。なければ先頭。
    keeper_idx = None
    for i in targets:
        if fields_obj[i].get("contextName") == keep_context:
            keeper_idx = i
            break
    if keeper_idx is None:
        keeper_idx = targets[0]

    replaced = []
    for i in targets:
        if i == keeper_idx:
            continue
        ctx_name = fields_obj[i].get("contextName", "?")
        fields_obj[i]["displayType"] = fallback_type
        replaced.append(ctx_name)

    # JSON 文字列に戻す。元の整形（改行・インデント）を尊重するため、元と同じ区切りで再シリアライズ。
    has_newline = "\n" in fields_str
    if has_newline:
        cur[last] = json.dumps(fields_obj, ensure_ascii=False, indent=2)
    else:
        cur[last] = json.dumps(fields_obj, ensure_ascii=False, separators=(",", ":"))
    return True, (f"displayType '{display_type}' 重複解消: "
                  f"'{fields_obj[keeper_idx].get('contextName', '?')}' を保持、"
                  f"{len(replaced)} 件を '{fallback_type}' に置換 ({', '.join(replaced)})")


def _apply_deoverlap(data: dict) -> tuple[bool, str]:
    """同一座標に重複配置されたモジュールをずらして解消する"""
    modules = data.get("modules", {})
    if not modules:
        return False, "modules がない"

    coord_to_mods: dict[tuple[int, int], list[str]] = {}
    for mod_name, mod in modules.items():
        layout = mod.get("layout", {})
        x, y = layout.get("x", 0), layout.get("y", 0)
        coord_to_mods.setdefault((x, y), []).append(mod_name)

    shifted = 0
    for (x, y), mods in coord_to_mods.items():
        if len(mods) <= 1 or (x == 0 and y == 0):
            continue
        # 2番目以降のモジュールを右方向にずらす（180px = CELL_WIDTH 間隔）
        for i, mod_name in enumerate(mods[1:], 1):
            modules[mod_name]["layout"]["x"] = x + i * 180
            shifted += 1

    if shifted:
        return True, f"{shifted} モジュールを右方向にシフトして重複解消"
    return True, "重複なし"


def apply_actions(data: dict, issues: list) -> dict:
    """Issue リストの fix_action を順番に適用。結果サマリを返す"""
    stats = {
        "applied":    0,
        "skipped":    0,
        "failed":     0,
        "recalc_layout_needed": False,
        "details":    [],
    }
    for issue in issues:
        if issue.get("fix_category") != "auto":
            continue
        action = issue.get("fix_action") or {}
        op = action.get("op", "")
        code = issue.get("code", "?")
        mod  = issue.get("module", "?")

        if op == "set":
            ok, msg = _apply_set(data, action.get("path", []), action.get("value"))
        elif op == "replace":
            ok, msg = _apply_replace(data, action.get("path", []),
                                     action.get("find", ""), action.get("replace", ""))
        elif op == "recalc_layout":
            stats["recalc_layout_needed"] = True
            ok, msg = True, "layout 再計算をマーク（後段で layout_calculator 呼び出し）"
        elif op == "deoverlap_layout":
            ok, msg = _apply_deoverlap(data)
        elif op == "rename_module":
            ok, msg = _apply_rename_module(data, action.get("old", ""), action.get("new", ""))
        elif op == "dedup_displaytype":
            ok, msg = _apply_dedup_displaytype(
                data,
                action.get("path", []),
                action.get("display_type", ""),
                action.get("keep_context", ""),
                action.get("fallback_type", "TEXT"),
            )
        else:
            ok, msg = False, f"未対応 op: '{op}'"

        if ok and not msg.endswith("置換対象なし"):
            stats["applied"] += 1
            stats["details"].append(f"[{code}] {mod}: {msg}")
        elif msg.endswith("置換対象なし"):
            stats["skipped"] += 1
            stats["details"].append(f"[{code}] {mod}: {msg}")
        else:
            stats["failed"] += 1
            stats["details"].append(f"[{code}] {mod}: FAIL - {msg}")
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description="auto_fixer: fix_category=auto の修正を機械的に適用")
    ap.add_argument("--json", required=True, help="修正対象のフロー JSON")
    ap.add_argument("--report", required=True, help="validator --json-report で出力した JSON レポート")
    ap.add_argument("--spec", help="設計書 YAML (recalc_layout が必要な場合)")
    ap.add_argument("--output", help="出力先 JSON（省略時は --json を上書き）")
    args = ap.parse_args()

    json_path = Path(args.json)
    report_path = Path(args.report)
    if not json_path.exists():
        print(f"[ERROR] フロー JSON が見つかりません: {json_path}", file=sys.stderr)
        return 1
    if not report_path.exists():
        print(f"[ERROR] レポート JSON が見つかりません: {report_path}", file=sys.stderr)
        return 1

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    with open(report_path, encoding="utf-8") as f:
        report = json.load(f)

    issues = report.get("issues", [])
    auto_issues = [i for i in issues if i.get("fix_category") == "auto"]

    print(f"[auto_fixer] 対象フロー: {json_path}", file=sys.stderr)
    print(f"[auto_fixer] 検出 Issue 総数: {len(issues)}", file=sys.stderr)
    print(f"[auto_fixer] auto 修正対象: {len(auto_issues)} 件", file=sys.stderr)

    if not auto_issues:
        print("[auto_fixer] 修正対象なし（auto カテゴリの Issue なし）", file=sys.stderr)
        return 0

    stats = apply_actions(data, auto_issues)

    print(f"[auto_fixer] 適用: {stats['applied']} 件 / スキップ: {stats['skipped']} / 失敗: {stats['failed']}",
          file=sys.stderr)
    for d in stats["details"]:
        print(f"  {d}", file=sys.stderr)

    output_path = Path(args.output) if args.output else json_path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[auto_fixer] 保存: {output_path}", file=sys.stderr)

    # レイアウト再計算が必要な場合、layout_calculator を呼ぶ
    if stats["recalc_layout_needed"]:
        if not args.spec:
            print("[auto_fixer] WARN: recalc_layout が必要だが --spec が指定されていないためスキップ",
                  file=sys.stderr)
        else:
            layout_script = PROJECT_DIR / "scripts" / "layout_calculator.py"
            cmd = ["python3", str(layout_script), str(output_path), args.spec]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
            if r.returncode == 0:
                print("[auto_fixer] layout 再計算 OK", file=sys.stderr)
            else:
                print(f"[auto_fixer] layout 再計算 FAIL: {r.stderr[:200]}", file=sys.stderr)

    print(str(output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
