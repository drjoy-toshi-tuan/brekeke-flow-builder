#!/usr/bin/env python3
"""
シナリオ台本ジェネレーター

フロー JSON + properties ファイルを読んで、
「どの分岐経路でどの順番に何を喋るか」を台本 MD として出力する。

Usage:
    python3 tools/gen_scenario_script.py \
        --json  output/scenarios/{施設}_{flow}/json/{施設}_{flow}.json \
        --props output/scenarios/{施設}_{flow}/properties_*.md \
        [--out  output/scenarios/{施設}_{flow}/scenario_script_{施設}_{flow}.md] \
        [--max-paths 40]        # 出力する経路数の上限（デフォルト 40）
        [--max-depth 60]        # DFS の深さ上限（ループ防止）
        [--happy-only]          # 正常経路（リトライなし）のみ出力

TTS が properties に書かれていないモジュールは「(TTS 未設定)」と表示する。
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator

PROJECT_DIR = Path(__file__).resolve().parent.parent

# ── モジュールタイプ分類 ─────────────────────────────────────────────────────

def classify(mod: dict) -> str:
    """モジュールを台本上の役割に分類する。"""
    t = mod.get("type", "")
    if "Text to speech" in t and "Speech Retry Counter" not in t and "Re-confirmation" not in t:
        return "tts"
    if "Re-confirmation" in t:
        return "reconfirm"
    if "Speech Retry Counter" in t:
        return "retry"
    if "AmiVoice" in t or "Speech to text" in t:
        return "stt"
    if "generate_by_OpenAI" in t or "GenerateByOpenAI" in t:
        return "openai"
    if "Script" in t or "script" in t:
        return "script"
    if "Jump to Flow" in t or "JumpToFlow" in t:
        return "jump"
    if "Call Transfer" in t or "Blind Transfer" in t:
        return "transfer"
    if "Disconnect" in t or "disconnect" in t or t == "":
        return "disconnect"
    if "wait" in t.lower() or "Wait" in t:
        return "wait"
    if "saveContext" in t or "Save" in t or "save" in t:
        return "save"
    if "incoming" in t.lower():
        return "incoming"
    return "other"


# ── properties パーサー ──────────────────────────────────────────────────────

def parse_properties(props_path: Path) -> dict[str, str]:
    """properties_*.md から {モジュール名: TTS文言} を抽出する。"""
    tts_map: dict[str, str] = {}
    text = props_path.read_text(encoding="utf-8", errors="replace")
    # コードブロック内を対象にする
    code_blocks = re.findall(r"```(.*?)```", text, re.DOTALL)
    target = "\n".join(code_blocks) if code_blocks else text

    for line in target.splitlines():
        line = line.strip()
        # module.prompt={tts_g:...} 形式
        m = re.match(r"^([^#=\s][^=]*?)\.prompt\s*=\s*(.+)$", line)
        if m:
            mod_name = m.group(1).strip()
            raw_val = m.group(2).strip()
            # {tts_g:...} または {tts_ai:...} から文言を取り出す
            inner = re.sub(r"^\{tts_[ga]i?:", "", raw_val)
            inner = re.sub(r"\}$", "", inner)
            # ネストした {tts_g:...} も除去
            inner = re.sub(r"^\{tts_[ga]i?:", "", inner)
            inner = re.sub(r"\}$", "", inner)
            tts_map[mod_name] = inner.strip()
    return tts_map


# ── DFS 経路列挙 ─────────────────────────────────────────────────────────────

# 台本上の 1 ステップ
class Step:
    __slots__ = ("mod_name", "role", "text", "branch_label")

    def __init__(self, mod_name: str, role: str, text: str, branch_label: str = ""):
        self.mod_name = mod_name
        self.role = role        # "bot" / "user" / "system" / "end"
        self.text = text
        self.branch_label = branch_label  # このステップに来るときの分岐ラベル


def _next_modules(mod: dict, happy_only: bool) -> list[tuple[str, str]]:
    """next リストから (label, nextModuleName) を返す。

    happy_only=True のとき: TIMEOUT/ERROR/NO_RESULT/false の枝を除外する。
    """
    nexts = mod.get("next", [])
    result: list[tuple[str, str]] = []
    for nx in nexts:
        cond = nx.get("condition", "")
        label = nx.get("label", cond)
        target = nx.get("nextModuleName", "")
        if not target:
            continue
        if happy_only:
            skip_patterns = [
                r"TIMEOUT", r"ERROR", r"NO_RESULT",
                r"^false$",
            ]
            if any(re.search(p, cond, re.I) for p in skip_patterns):
                continue
        result.append((label, target))
    return result


def dfs_paths(
    modules: dict,
    tts_map: dict,
    start: str,
    max_depth: int,
    happy_only: bool,
) -> Iterator[list[Step]]:
    """DFS で start から全終端経路を列挙する (generator)。"""

    def _dfs(
        mod_name: str,
        path: list[Step],
        visited: set[str],
        branch_label: str,
    ) -> Iterator[list[Step]]:
        if len(path) >= max_depth:
            # 深さ上限に達したら打ち切り（無限ループ防止）
            yield path + [Step(mod_name, "end", "(深さ上限に達したため打ち切り)", branch_label)]
            return

        if mod_name not in modules:
            yield path + [Step(mod_name, "end", f"(モジュール未定義: {mod_name})", branch_label)]
            return

        mod = modules[mod_name]
        role = classify(mod)
        tts = tts_map.get(mod_name, "")

        # このモジュールのステップを作成
        if role == "tts":
            step = Step(mod_name, "bot", tts or "(TTS 未設定)", branch_label)
        elif role == "reconfirm":
            step = Step(mod_name, "bot", f"[復唱] {tts or mod_name}", branch_label)
        elif role == "retry":
            step = Step(mod_name, "bot", f"[リトライ] {tts or mod_name}", branch_label)
        elif role == "stt":
            step = Step(mod_name, "user", "[発話 / DTMF 入力]", branch_label)
        elif role == "openai":
            step = Step(mod_name, "system", f"[AI 判定: {mod_name}]", branch_label)
        elif role == "script":
            step = Step(mod_name, "system", f"[Script 判定: {mod_name}]", branch_label)
        elif role == "jump":
            target_flow = mod.get("params", {}).get("name", mod_name)
            step = Step(mod_name, "system", f"[→ サブフロー: {target_flow}]", branch_label)
        elif role == "transfer":
            step = Step(mod_name, "system", "[有人転送]", branch_label)
        elif role == "disconnect":
            yield path + [Step(mod_name, "end", "[切断]", branch_label)]
            return
        elif role in ("wait", "save", "incoming", "other"):
            # 台本に載せない内部処理 — 透過してそのまま次へ
            step = None
        else:
            step = None

        new_path = path + [step] if step is not None else path

        # 終端判定: next が空 or disconnect 系
        nexts = _next_modules(mod, happy_only)
        if not nexts:
            yield new_path + [Step(mod_name, "end", "[終端]", "")]
            return

        # 切断モジュール
        if role == "disconnect":
            yield new_path
            return

        # 単一 next（分岐なし）
        if len(nexts) == 1:
            _, next_name = nexts[0]
            if next_name in visited:
                # ループ検出 → 打ち切り
                yield new_path + [Step(next_name, "end", f"(ループ: {next_name})", "")]
                return
            yield from _dfs(next_name, new_path, visited | {next_name}, "")
            return

        # 複数 next（分岐あり）
        for lbl, next_name in nexts:
            if next_name in visited:
                yield new_path + [Step(next_name, "end", f"(ループ: {next_name})", lbl)]
                continue
            yield from _dfs(next_name, new_path, visited | {next_name}, lbl)

    start_mod = modules.get(start)
    if start_mod is None:
        # start が modules に無い場合は冒頭 TTS を探す
        for name, m in modules.items():
            if classify(m) in ("wait", "save", "incoming", "other"):
                continue
            start = name
            break

    yield from _dfs(start, [], {start}, "")


# ── 経路名生成 ────────────────────────────────────────────────────────────────

def path_label(steps: list[Step]) -> str:
    """経路の代表ラベルを生成する（分岐ラベルの連鎖）。"""
    labels = [s.branch_label for s in steps if s.branch_label and s.branch_label not in (
        "Next Module", "^.*$", "true", "false", "Retry", "No more",
    )]
    # TIMEOUT/ERROR/NO_RESULT は省略
    labels = [l for l in labels if not re.match(r"TIMEOUT|ERROR|NO_RESULT", l, re.I)]
    if not labels:
        return "正常経路"
    return " → ".join(labels[:6])


def path_end_label(steps: list[Step]) -> str:
    """経路の終端モジュール名を返す。"""
    for s in reversed(steps):
        if s.role == "end":
            return s.mod_name
        if s.mod_name:
            return s.mod_name
    return "不明"


# ── MD 出力 ──────────────────────────────────────────────────────────────────

ROLE_ICON = {
    "bot":    "🤖 Bot",
    "user":   "🧑 User",
    "system": "⚙️  System",
    "end":    "🔚 終端",
}


def render_path(idx: int, steps: list[Step], show_system: bool = True) -> str:
    lines: list[str] = []
    lbl = path_label(steps)
    end = path_end_label(steps)
    lines.append(f"### 経路 {idx}: {lbl}")
    lines.append(f"> **終端**: `{end}`")
    lines.append("")
    lines.append("| # | 話者 | 発話 / アクション | モジュール名 |")
    lines.append("|---|---|---|---|")

    step_num = 0
    for s in steps:
        if not show_system and s.role in ("system",):
            continue
        step_num += 1
        icon = ROLE_ICON.get(s.role, s.role)
        branch = f" ← `{s.branch_label}`" if s.branch_label and s.branch_label not in (
            "Next Module", "^.*$", "Retry", "No more",
        ) else ""
        text = s.text.replace("|", "｜")  # MD テーブル内の | をエスケープ
        lines.append(f"| {step_num} | {icon}{branch} | {text} | `{s.mod_name}` |")

    lines.append("")
    return "\n".join(lines)


def generate_script(
    flow_json: dict,
    tts_map: dict,
    max_paths: int,
    max_depth: int,
    happy_only: bool,
    show_system: bool,
) -> str:
    flow_name = flow_json.get("name", "不明フロー")
    modules: dict = flow_json.get("modules", {})
    start: str = flow_json.get("start", "")

    if not start and modules:
        start = next(iter(modules))

    lines: list[str] = []
    lines.append(f"# シナリオ台本 — {flow_name}")
    lines.append("")
    lines.append(f"> **フロー名**: `{flow_name}`  ")
    lines.append(f"> **モジュール数**: {len(modules)}  ")
    lines.append(f"> **生成オプション**: {'正常経路のみ' if happy_only else '全経路（リトライ含む）'}  ")
    lines.append("")
    lines.append("---")
    lines.append("")

    seen_paths: set[tuple] = set()
    path_count = 0

    for steps in dfs_paths(modules, tts_map, start, max_depth, happy_only):
        # 重複排除: (モジュール名列) でキーを作成
        key = tuple(s.mod_name for s in steps)
        if key in seen_paths:
            continue
        seen_paths.add(key)

        path_count += 1
        lines.append(render_path(path_count, steps, show_system=show_system))

        if path_count >= max_paths:
            lines.append(f"> ⚠️ 経路数が上限 {max_paths} に達したため出力を打ち切りました。")
            lines.append(f"> `--max-paths` オプションで増やせます。")
            break

    if path_count == 0:
        lines.append("> 経路が見つかりませんでした。start モジュール名を確認してください。")

    lines.append("")
    lines.append(f"---")
    lines.append(f"*合計 {path_count} 経路*")

    return "\n".join(lines)


# ── メイン ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="シナリオ台本生成ツール")
    parser.add_argument("--json",  required=True, help="フロー JSON ファイルのパス")
    parser.add_argument("--props", help="properties_*.md ファイルのパス（省略時: TTS 未設定）")
    parser.add_argument("--out",   help="出力先 MD パス（省略時: stdout）")
    parser.add_argument("--max-paths",  type=int, default=40, help="出力する経路数の上限（デフォルト 40）")
    parser.add_argument("--max-depth",  type=int, default=60, help="DFS 深さ上限（デフォルト 60）")
    parser.add_argument("--happy-only", action="store_true", help="正常経路（TIMEOUT/ERROR/NO_RESULT/false 枝除外）のみ出力")
    parser.add_argument("--hide-system", action="store_true", help="System（AI 判定・Script 等）行を非表示にする")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"ERROR: JSON ファイルが見つかりません: {json_path}", file=sys.stderr)
        sys.exit(1)

    with open(json_path, encoding="utf-8", errors="replace") as f:
        flow_json = json.load(f)

    tts_map: dict[str, str] = {}
    if args.props:
        props_path = Path(args.props)
        if props_path.exists():
            tts_map = parse_properties(props_path)
            print(f"INFO: TTS マップ {len(tts_map)} 件読み込み", file=sys.stderr)
        else:
            print(f"WARN: properties ファイルが見つかりません: {props_path}", file=sys.stderr)

    md = generate_script(
        flow_json=flow_json,
        tts_map=tts_map,
        max_paths=args.max_paths,
        max_depth=args.max_depth,
        happy_only=args.happy_only,
        show_system=not args.hide_system,
    )

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(md, encoding="utf-8")
        print(f"OK: 台本を出力しました → {out_path}", file=sys.stderr)
        print(str(out_path))
    else:
        print(md)


if __name__ == "__main__":
    main()
