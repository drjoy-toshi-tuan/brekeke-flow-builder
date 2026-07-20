#!/usr/bin/env python3
"""inject_prompts.py — プロンプトサイドカーMDをフローJSONに注入する

フローJSONのgenerate_by_OpenAIモジュールに対し、
サイドカーMD（## セクション形式）からparams.promptを一括注入する。
prompterが書き出したプレーンテキストをjson.dumpsで正しくエンコードしてJSONに書き込む。

Usage:
    python3 scripts/inject_prompts.py <sidecar_md_path> <target_json_path>

サイドカーMD形式:
    ## モジュール名（例: OpenAI_診療科）
    # Role
    あなたは...

    ## 次のモジュール名
    # Role
    ...
"""
import sys
import json
from pathlib import Path


def parse_sidecar(md_text: str, known_modules: set | None = None) -> dict:
    """## セクションを解析してモジュール名→プロンプトのマップを返す。

    ## で始まる行をセクション区切りとする。
    known_modules が指定された場合はその中に含まれる名前のみをセクション見出しとして扱い、
    プロンプト本文中の "## NO_RESULT の分類" 等の内部見出しを誤ってセクション分割しない。
    前後の空白行はトリムする。
    """
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in md_text.splitlines():
        if line.startswith("## "):
            candidate = line[3:].strip()
            # known_modules が指定されている場合は exact match のみセクション区切り
            # 未指定の場合は "【" / "#" で始まる行のみ除外
            if known_modules is not None:
                is_module_header = candidate in known_modules
            else:
                is_module_header = bool(candidate) and not candidate.startswith("【") and not candidate.startswith("#")

            if is_module_header:
                if current_name is not None:
                    sections[current_name] = "\n".join(current_lines).strip()
                current_name = candidate
                current_lines = []
            else:
                if current_name is not None:
                    current_lines.append(line)
        else:
            if current_name is not None:
                current_lines.append(line)

    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()

    return sections


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <sidecar_md> <target_json>", file=sys.stderr)
        sys.exit(1)

    sidecar_path = Path(sys.argv[1])
    json_path = Path(sys.argv[2])

    if not sidecar_path.exists():
        print(f"ERROR: sidecar not found: {sidecar_path}", file=sys.stderr)
        sys.exit(1)

    if not json_path.exists():
        print(f"ERROR: target JSON not found: {json_path}", file=sys.stderr)
        sys.exit(1)

    # JSON先読み: generate_by_OpenAI モジュール名を known_modules として parse_sidecar に渡す
    # これにより "## NO_RESULT の分類" 等の内部見出しがセクション誤分割されない
    try:
        _flow_pre = json.loads(json_path.read_bytes())
        _mods_pre: dict = _flow_pre.get("modules", _flow_pre)
        known_modules: set | None = {
            k for k, v in _mods_pre.items()
            if isinstance(v, dict) and "generate_by_OpenAI" in v.get("type", "")
        }
    except Exception:
        known_modules = None

    # サイドカー解析
    md_text = sidecar_path.read_text(encoding="utf-8")
    prompts = parse_sidecar(md_text, known_modules=known_modules)

    if not prompts:
        print("WARNING: ## セクションが見つかりません — 注入をスキップ", file=sys.stderr)
        sys.exit(0)

    # JSON読み込み
    flow = json.loads(json_path.read_bytes())

    # Brekeke JSON は {"modules": {モジュール名: {...}}} 構造
    modules: dict = flow.get("modules", flow)

    # 注入
    injected = 0
    not_found: list[str] = []

    for module_name, prompt_text in prompts.items():
        if module_name not in modules:
            not_found.append(module_name)
            continue
        mod = modules[module_name]
        if not isinstance(mod, dict):
            not_found.append(module_name)
            continue
        params = mod.setdefault("params", {})
        params["prompt"] = prompt_text
        injected += 1

    # ミニファイ形式で書き戻し（元のフォーマットと同一）
    json_path.write_bytes(
        json.dumps(flow, ensure_ascii=False, separators=(',', ':')).encode("utf-8")
    )

    print(
        f"inject_prompts: {injected}/{len(prompts)} モジュールに注入完了 → {json_path.name}",
        file=sys.stderr,
    )
    if not_found:
        print(f"WARNING: JSON内に見つからないモジュール: {not_found}", file=sys.stderr)
        sys.exit(2)  # 部分成功


if __name__ == "__main__":
    main()
