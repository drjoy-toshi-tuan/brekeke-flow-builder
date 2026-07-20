#!/usr/bin/env python3
"""
gen_prompts.py — 決定論的 OpenAI プロンプト生成スクリプト（prompter LLM の代替）

設計書 YAML の hearing ブロックから generate_by_OpenAI モジュールのプロンプトを
SKILL_A〜E テンプレートを用いて決定論的に生成し、サイドカー MD に書き出す。

使い方:
    python3 scripts/gen_prompts.py \
        --spec output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml \
        --output output/scenarios/{施設}_{flow}/prompts_{施設}_{flow}.md

終了コード:
    0 — 全モジュール生成完了（LLM 不要）
    2 — 一部モジュールが未解決（LLM フォールバック推奨）
    1 — 致命的エラー

依存: PyYAML のみ（標準ライブラリ + yaml）
"""

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が必要です", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# 定数 / ヘルパー
# ---------------------------------------------------------------------------

# はい/いいえ系の標準キーワードパターン（STT誤変換を含む）
_YES_PATTERNS: dict[str, list[str]] = {
    "はい": ["はい", "はーい", "うん", "そう", "そうです", "はいそうです", "お願いします",
              "お願い", "大丈夫", "いいです", "よろしい", "よろしく", "よろしくお願い",
              "いいですよ", "もちろん", "ええ", "ええそうです", "そうですね"],
    "再診": ["再診", "さいしん", "来たことある", "来たことあります", "以前に来た",
              "前に来た", "以前来た", "かかったことある", "かかったことあります"],
    "初診": ["初診", "しょしん", "初めて", "はじめて", "初めてです", "はじめてです",
              "ない", "ありません", "なかった", "来たことない", "来たことありません"],
    "肯定": ["はい", "はーい", "うん", "そう", "そうです", "大丈夫", "いいです",
               "よろしい", "お願いします", "問題ない", "構いません", "かまいません",
               "了解", "承知", "わかりました", "分かりました"],
    "否定": ["いいえ", "いや", "違う", "ちがう", "だめ", "ダメ", "嫌", "いやです",
               "やめます", "やめる", "必要ない", "けっこうです", "結構です",
               "いりません", "要りません", "いらない"],
    "有": ["はい", "あります", "有ります", "持っています", "持ってます", "ある"],
    "無": ["いいえ", "ありません", "ない", "持っていません", "持ってません", "なし"],
}

# 数字→ラベル 標準パターン（DTMF対応時）
_DIGIT_LABEL_TMPL = "{digit}, {digit}番, {kanji} → {label}"
_DIGIT_KANJI = ["", "いち", "に", "さん", "よん", "ご", "ろく", "なな", "はち", "きゅう", "じゅう"]


def _kanji(n: int) -> str:
    return _DIGIT_KANJI[n] if n < len(_DIGIT_KANJI) else str(n)


def _labels_block(labels: list[str]) -> str:
    return "\n".join(f"- {lbl}" for lbl in labels)


def _digit_patterns_block(labels: list[str]) -> str:
    lines = []
    for i, lbl in enumerate(labels, start=1):
        lines.append(_DIGIT_LABEL_TMPL.format(digit=i, kanji=_kanji(i), label=lbl))
    return "\n".join(lines)


def _keyword_patterns_block_A(labels: list[str], mapping: list[dict]) -> tuple[str, bool]:
    """SKILL_A 用キーワードブロックを生成。mapping がある場合は優先使用。
    Returns: (block_text, has_todos)
    """
    if mapping:
        # openai_rules.mapping から生成
        blocks = []
        for item in mapping:
            inp = item.get("input", "")
            out = item.get("output", "")
            if inp and out:
                blocks.append(f"### {out}\n{inp}")
        return "\n\n".join(blocks), False

    # 標準キーワードを流用できるラベルがあれば使う
    blocks = []
    has_todos = False
    for lbl in labels:
        known = _YES_PATTERNS.get(lbl)
        if known:
            blocks.append("### " + lbl + "\n" + "\n".join(known))
        else:
            blocks.append(f"### {lbl}\n# TODO: キーワードを設計書から補完してください")
            has_todos = True
    return "\n\n".join(blocks), has_todos


def _patterns_B(label: str, mapping: list[dict], side: str) -> tuple[str, bool]:
    """SKILL_B 用パターン行生成。side='A' or 'B'"""
    # mapping から該当ラベルのパターンを抽出
    if mapping:
        for item in mapping:
            if item.get("output") == label:
                return item.get("input", ""), False
    known = _YES_PATTERNS.get(label)
    if known:
        return "\n".join(known), False
    return f"# TODO: {label} のキーワードパターンを補完してください", True


# ---------------------------------------------------------------------------
# テンプレート読み込み
# ---------------------------------------------------------------------------

SKILL_DIR = Path(__file__).parent.parent / "docs" / "ai" / "skills"

def _load_template(skill_file: str) -> str:
    candidates = list(SKILL_DIR.glob(f"{skill_file}*.md"))
    if not candidates:
        return ""
    return candidates[0].read_text(encoding="utf-8")


def _extract_base_prompt(template_text: str) -> str:
    """テンプレートMDの ```ブロック内のベースプロンプトを抽出する"""
    in_block = False
    lines = []
    for line in template_text.splitlines():
        if line.strip().startswith("```") and not in_block:
            in_block = True
            continue
        if line.strip() == "```" and in_block:
            break
        if in_block:
            lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SKILL別プロンプト生成
# ---------------------------------------------------------------------------

def _gen_skill_A(target: dict) -> tuple[str, bool]:
    """分類型（N択判定）"""
    labels = target.get("output_labels", [])
    tts = target.get("tts_announcement", "（TTS文言不明）")
    mapping = (target.get("openai_rules") or {}).get("mapping", [])
    stt_type = target.get("stt_type", "AmiVoice")

    n = len(labels)
    output_labels_block = _labels_block(labels)
    keyword_block, has_todos = _keyword_patterns_block_A(labels, mapping)

    use_dtmf = "DTMF" in stt_type
    digit_block = _digit_patterns_block(labels) if use_dtmf else ""
    if not use_dtmf:
        # STEP2 (数字モード) ごと削除するため、プレースホルダーは空欄に
        digit_section = "（DTMF非対応のため STEP2 は省略）"
    else:
        digit_section = digit_block

    template = _load_template("SKILL_A_classification")
    base = _extract_base_prompt(template)

    prompt = base.replace("{{N}}", str(n))
    prompt = prompt.replace("{{TTS_ANNOUNCEMENT}}", tts)
    prompt = prompt.replace("{{OUTPUT_LABELS}}", output_labels_block)
    prompt = prompt.replace("{{DIGIT_PATTERNS}}", digit_section)
    prompt = prompt.replace("{{KEYWORD_PATTERNS}}", keyword_block)

    if not use_dtmf:
        # STEP2 ブロックを削除
        lines = prompt.splitlines()
        filtered = []
        skip = False
        for line in lines:
            if "STEP2：数字モード判定" in line:
                skip = True
            if skip and line.startswith("---") and len(line) >= 3 and all(c == "-" for c in line.strip()):
                skip = False
                continue
            if not skip:
                filtered.append(line)
        prompt = "\n".join(filtered)

    return prompt, has_todos


def _gen_skill_B(target: dict) -> tuple[str, bool]:
    """はい/いいえ判定型（二値分類）"""
    labels = target.get("output_labels", [])
    tts = target.get("tts_announcement", "（TTS文言不明）")
    mapping = (target.get("openai_rules") or {}).get("mapping", [])
    step_name = target.get("step_name", "")

    label_a = labels[0] if len(labels) > 0 else "はい"
    label_b = labels[1] if len(labels) > 1 else "いいえ"

    judgment_type = f"{label_a}／{label_b}"
    judgment_desc = f"{label_a}か{label_b}かの判定"

    patterns_a_str, todo_a = _patterns_B(label_a, mapping, "A")
    patterns_b_str, todo_b = _patterns_B(label_b, mapping, "B")
    has_todos = todo_a or todo_b

    template = _load_template("SKILL_B_yes_no")
    base = _extract_base_prompt(template)

    prompt = base.replace("{{JUDGMENT_TYPE}}", judgment_type)
    prompt = prompt.replace("{{JUDGMENT_DESCRIPTION}}", judgment_desc)
    prompt = prompt.replace("{{TTS_QUESTION}}", tts)
    prompt = prompt.replace("{{LABEL_A}}", label_a)
    prompt = prompt.replace("{{LABEL_B}}", label_b)
    prompt = prompt.replace("{{PATTERNS_A}}", patterns_a_str)
    prompt = prompt.replace("{{PATTERNS_B}}", patterns_b_str)

    return prompt, has_todos


def _gen_skill_C(target: dict) -> tuple[str, bool]:
    """日付変換型"""
    tts = target.get("tts_announcement", "（TTS文言不明）")
    rules = target.get("openai_rules") or {}
    step_name = target.get("step_name", "")
    labels = target.get("output_labels", [])

    date_purpose = rules.get("date_purpose") or f"{step_name} の日付取得"
    unknown_label = rules.get("unknown_label") or (labels[0] if labels else "分からない")
    max_months = str(rules.get("max_future_months", 3))

    template = _load_template("SKILL_C_date")
    base = _extract_base_prompt(template)

    prompt = base.replace("{{DATE_PURPOSE}}", date_purpose)
    prompt = prompt.replace("{{TTS_QUESTION}}", tts)
    prompt = prompt.replace("{{UNKNOWN_LABEL}}", unknown_label)
    prompt = prompt.replace("{{MAX_FUTURE_MONTHS}}", max_months)

    return prompt, False


def _gen_skill_D(target: dict) -> tuple[str, bool]:
    """正規化型（リスト照合）"""
    labels = target.get("output_labels", []) or []
    range_values = target.get("range_values", []) or []
    tts = target.get("tts_announcement", "（TTS文言不明）")
    mapping = (target.get("openai_rules") or {}).get("mapping", [])
    step_name = target.get("step_name", "")

    # ラベルリスト: output_labels > range_values > 空
    if not labels and range_values:
        labels = [r.get("value", "") for r in range_values if isinstance(r, dict) and r.get("value")]

    n = len(labels)
    output_labels_block = _labels_block(labels)

    # キーワードパターン
    if mapping:
        kw_lines = []
        for item in mapping:
            inp = item.get("input", "")
            out = item.get("output", "")
            if inp and out:
                kw_lines.append(f"### {out}\n{inp}")
        keyword_block = "\n\n".join(kw_lines)
        has_todos = False
    else:
        # ラベルをそのままパターンとして使う（最低限）
        kw_lines = [f"### {lbl}\n{lbl}" for lbl in labels]
        keyword_block = "\n\n".join(kw_lines)
        has_todos = True  # 読み仮名等が不足しているためフォールバック推奨

    # 対象名・単位をステップ名から推測
    normalization_target = step_name.replace("_", " ").split()[-1] if step_name else "項目"
    unit = normalization_target
    domain_rule = "意味的推論"

    template = _load_template("SKILL_D_normalization")
    base = _extract_base_prompt(template)

    prompt = base.replace("{{NORMALIZATION_TARGET}}", normalization_target)
    prompt = prompt.replace("{{N}}", str(n))
    prompt = prompt.replace("{{UNIT}}", unit)
    prompt = prompt.replace("{{TTS_QUESTION}}", tts)
    prompt = prompt.replace("{{OUTPUT_LABELS}}", output_labels_block)
    prompt = prompt.replace("{{DOMAIN_SPECIFIC_RULE}}", domain_rule)
    prompt = prompt.replace("{{KEYWORD_PATTERNS}}", keyword_block)

    return prompt, has_todos


def _gen_skill_E(target: dict) -> tuple[str, bool]:
    """自由テキスト型"""
    tts = target.get("tts_announcement", "（TTS文言不明）")
    step_name = target.get("step_name", "")
    text_purpose = step_name.replace("_", " ")

    template = _load_template("SKILL_E_freetext")
    base = _extract_base_prompt(template)

    prompt = base.replace("{{TEXT_PURPOSE}}", text_purpose)
    prompt = prompt.replace("{{TTS_QUESTION}}", tts)

    return prompt, False


_GENERATORS = {
    "classify":  _gen_skill_A,
    "judge":     _gen_skill_B,
    "convert":   _gen_skill_C,
    "normalize": _gen_skill_D,
    "summarize": _gen_skill_E,
}


# ---------------------------------------------------------------------------
# YAML 読み込み・ターゲット列挙（orchestrator._list_prompter_targets と同等）
# ---------------------------------------------------------------------------

def _list_targets(spec_path: Path) -> list[dict]:
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    scenario_flow = spec.get("scenario_flow", []) or []
    hearing_index: dict = {}
    for h in spec.get("hearing_items", []) or []:
        if not h:
            continue
        key = h.get("name") or h.get("step_name")
        if key:
            hearing_index[key] = h
    step_index = {
        s["step_name"]: s
        for s in spec.get("step_details", []) or []
        if s and s.get("step_name")
    }
    ctx_index = {
        c["context_name"]: c
        for c in spec.get("context_fields", []) or []
        if isinstance(c, dict) and c.get("context_name")
    }

    targets = []
    for block in scenario_flow:
        if block.get("type") != "hearing":
            continue
        if block.get("unreachable"):
            continue
        output_format = block.get("output_format", "text")
        if output_format == "text":
            continue

        step = block["step"]
        h_item = hearing_index.get(step) or hearing_index.get(step.rsplit("_", 1)[0], {})
        step_detail = step_index.get(step) or step_index.get(step.rsplit("_", 1)[0], {})

        processing = (h_item or {}).get("openai_processing", "classify")
        save_to = (h_item or {}).get("save_to", "")
        ctx_field = ctx_index.get(save_to, {})

        targets.append({
            "module_name": f"OpenAI_{step}",
            "step_name": step,
            "processing": processing,
            "output_format": output_format,
            "tts_announcement": (step_detail or {}).get("tts_announcement", ""),
            "output_labels": (h_item or {}).get("output_labels", []),
            "openai_rules": (step_detail or {}).get("openai_rules", {}),
            "stt_type": (h_item or {}).get("stt_type", "AmiVoice"),
            "save_to": save_to,
            "range_values": ctx_field.get("range_values", []),
        })
    return targets


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="決定論的 OpenAI プロンプト生成")
    parser.add_argument("--spec", required=True, help="設計書 YAML パス")
    parser.add_argument("--output", required=True, help="サイドカー MD 出力パス")
    parser.add_argument("--dry-run", action="store_true", help="標準出力のみ（ファイル書き出しなし）")
    args = parser.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: 設計書が見つかりません: {spec_path}", file=sys.stderr)
        return 1

    targets = _list_targets(spec_path)
    if not targets:
        print("INFO: OpenAI モジュールなし（全て scaffold 解決済み）", file=sys.stderr)
        Path(args.output).write_text("", encoding="utf-8")
        return 0

    print(f"INFO: {len(targets)} 件の OpenAI モジュールを処理中...", file=sys.stderr)

    sections: list[str] = []
    fallback_modules: list[str] = []

    for t in targets:
        processing = t["processing"]
        gen_fn = _GENERATORS.get(processing)
        if gen_fn is None:
            print(f"WARN: 未知の processing '{processing}' → {t['module_name']} はフォールバック", file=sys.stderr)
            fallback_modules.append(t["module_name"])
            continue

        try:
            prompt_text, has_todos = gen_fn(t)
        except Exception as e:
            print(f"WARN: {t['module_name']} 生成エラー: {e} → フォールバック", file=sys.stderr)
            fallback_modules.append(t["module_name"])
            continue

        if has_todos:
            print(f"WARN: {t['module_name']} — キーワードが不完全（LLM補完推奨）", file=sys.stderr)
            fallback_modules.append(t["module_name"])
            continue  # sidecar に書かない（LLM に委ねる）

        sections.append(f"## {t['module_name']}\n{prompt_text}")

    sidecar = "\n\n".join(sections)

    if args.dry_run:
        print(sidecar)
    else:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(sidecar, encoding="utf-8")
        print(f"OK: サイドカー書き出し完了: {out_path}", file=sys.stderr)

    if fallback_modules:
        print(
            f"FALLBACK: {len(fallback_modules)} 件は LLM(prompter) でのフォールバック推奨: "
            + ", ".join(fallback_modules),
            file=sys.stderr,
        )
        return 2  # 部分的に未解決

    print(f"OK: 全 {len(targets)} 件を決定論的に生成（LLM 不使用）", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
