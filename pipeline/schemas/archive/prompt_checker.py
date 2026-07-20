#!/usr/bin/env python3
"""
prompt_checker.py — OpenAIモジュール 4本柱プロンプト品質チェッカー

フローJSON内の generate_by_OpenAI モジュールに対し、
入力統制・前処理・文脈定義・例外処理・整合性の5観点で静的チェックを行う。

Usage (単体テスト用):
    python schemas/prompt_checker.py output/json/merged_xxx.json --properties output/scenarios/{施設}_{flow}/properties_{施設}_{flow}.md
"""

import json
import re
import sys
from dataclasses import dataclass, field


# ============================================================
# データモデル
# ============================================================

@dataclass
class CheckItem:
    code: str       # P-1a, P-2, etc.
    pillar: str     # 入力統制, 前処理, 文脈定義, 例外処理, 整合性
    severity: str   # CRITICAL, WARNING
    passed: bool
    message: str


@dataclass
class PromptCheckResult:
    module_name: str
    items: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not any(
            not item.passed and item.severity == "CRITICAL" for item in self.items
        )

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.items if not i.passed and i.severity == "CRITICAL")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.items if not i.passed and i.severity == "WARNING")


# ============================================================
# ヘルパー
# ============================================================

def is_stt(mod_type: str) -> bool:
    return any(kw in mod_type for kw in ["AmiVoice", "DTMF AmiVoice", "Speech to Text"])


def is_tts(mod_type: str) -> bool:
    # Text To Speech 通常モジュール、および Re-confirmation node data（復唱TTS）を含む
    return ("Text To Speech$Text to speech" in mod_type
            or "Text To Speech$Re-confirmation node data" in mod_type)


def is_openai(mod_type: str) -> bool:
    return "generate_by_OpenAI" in mod_type


def build_reverse_map(modules: dict) -> dict:
    """target_name -> [source_name, ...] の逆引きマップを構築"""
    reverse = {}
    for name, mod in modules.items():
        for nxt in mod.get("next", []):
            target = nxt.get("nextModuleName", "")
            if target:
                reverse.setdefault(target, []).append(name)
    return reverse


def parse_properties(path: str) -> dict:
    """IVRプロパティファイルから TTS名 -> 発話テキスト のマッピングを構築

    対応形式:
        モジュール名.prompt={tts_g: テキスト}
        モジュール名.prompt={tts_g: テキスト}{recstart}
    """
    tts_prompts = {}
    pattern = re.compile(r'^(\S+?)\.prompt=\{tts_g:\s*(.+?)\}')
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = pattern.match(line.strip())
                if m:
                    tts_prompts[m.group(1)] = m.group(2)
    except FileNotFoundError:
        print(f"[ERROR] プロパティファイルが見つかりません: {path}", file=sys.stderr)
    return tts_prompts


def find_upstream_input(openai_mod: dict, modules: dict) -> tuple[str | None, str]:
    """OpenAIモジュールの params.module から上流入力モジュールを返す

    Returns:
        (module_name, module_kind) — kind は "stt", "openai", "unknown" のいずれか
    """
    ref = openai_mod.get("params", {}).get("module", "")
    if ref and ref in modules:
        mod_type = modules[ref].get("type", "")
        if is_stt(mod_type):
            return ref, "stt"
        if is_openai(mod_type):
            return ref, "openai"
        return ref, "unknown"
    return None, ""


def find_upstream_tts(stt_name: str, modules: dict, reverse_map: dict) -> str | None:
    """STTモジュールの上流にあるTTSモジュール名を返す"""
    sources = reverse_map.get(stt_name, [])
    for src in sources:
        if src in modules and is_tts(modules[src].get("type", "")):
            return src
    return None


def extract_prompt_output_values(prompt: str) -> list[str]:
    """プロンプトの出力仕様セクションから期待される出力値リストを抽出する

    パターン:
        - 値1
        - 値2
        - NO_RESULT
    """
    values = []
    # "- 値" パターンで列挙されている出力値を抽出
    in_output_section = False
    for line in prompt.split("\n"):
        stripped = line.strip()
        # 出力仕様セクションの開始を検出
        if re.search(r"出力仕様|出力ルール|出力値|#\s*Output|いずれか.*のみ.*出力|1語のみ|一つのみ", stripped):
            in_output_section = True
            continue
        # セクション区切り（---）で終了
        if stripped == "---" and in_output_section:
            in_output_section = False
            continue
        # 見出し行で別セクションに入ったら終了
        if stripped.startswith("#") and in_output_section:
            in_output_section = False
            continue
        # リスト項目から値を抽出
        if in_output_section:
            m = re.match(r"^[-*]\s+(.+)$", stripped)
            if m:
                val = m.group(1).strip()
                # 説明文を除去（括弧やコロン以降）
                val = re.split(r"[（(：:]", val)[0].strip()
                if val:
                    values.append(val)
    return values


def extract_next_conditions(openai_mod: dict) -> list[str]:
    """OpenAIモジュールのnext配列から分岐条件値を抽出する

    ^TIMEOUT$, ^ERROR$, ^NO_RESULT$, ^.*$, ^.+$, 空文字 は除外し、
    ^値$ パターンの「値」部分だけを返す。
    """
    skip = {"^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.*$", "^.+$", ""}
    values = []
    for nxt in openai_mod.get("next", []):
        cond = nxt.get("condition", "")
        if cond in skip:
            continue
        # ^値$ → 値 を抽出
        m = re.match(r"^\^(.+)\$$", cond)
        if m:
            values.append(m.group(1))
    return values


# ============================================================
# 4本柱チェック
# ============================================================

def check_openai_module(
    mod_name: str,
    mod: dict,
    modules: dict,
    reverse_map: dict,
    tts_prompts: dict,
) -> PromptCheckResult:
    """1つのOpenAIモジュールに対して4本柱 + 整合性チェックを実行"""

    result = PromptCheckResult(module_name=mod_name)
    prompt = mod.get("params", {}).get("prompt", "")

    # --- P-1a: 入力統制（構造チェーン） ---
    upstream_name, upstream_kind = find_upstream_input(mod, modules)
    tts_name = None

    if upstream_kind == "stt" and upstream_name:
        tts_name = find_upstream_tts(upstream_name, modules, reverse_map)
        # Soniox STT は TTS 内蔵（IVR プロパティで発話）→ 上流 TTS 不要
        is_soniox_stt = upstream_name and "Soniox" in modules.get(upstream_name, {}).get("type", "")
        tts_ok = tts_name is not None or is_soniox_stt
        result.items.append(CheckItem(
            code="P-1a",
            pillar="入力統制",
            severity="CRITICAL",
            passed=tts_ok,
            message=(
                f"TTS({tts_name})→STT({upstream_name})→OpenAI チェーン確認OK"
                if tts_name
                else (f"Soniox STT({upstream_name})→OpenAI（TTS内蔵モード）" if is_soniox_stt
                      else f"STT({upstream_name})の上流にTTSが見つからない")
            ),
        ))
    elif upstream_kind == "openai" and upstream_name:
        result.items.append(CheckItem(
            code="P-1a",
            pillar="入力統制",
            severity="CRITICAL",
            passed=True,
            message=f"OpenAI({upstream_name})→OpenAI カスケード構成",
        ))
    else:
        result.items.append(CheckItem(
            code="P-1a",
            pillar="入力統制",
            severity="CRITICAL",
            passed=False,
            message=f"params.moduleの参照先が見つからない（module='{mod.get('params', {}).get('module', '')}'）",
        ))

    # --- P-1b: 入力統制（Context節にTTS発話内容が反映されているか） ---
    if tts_name and tts_prompts:
        tts_text = tts_prompts.get(tts_name, "")
        if tts_text:
            # プロンプトのContext節にTTSテキストの主要部分が含まれているか
            # 完全一致は求めず、TTSテキストの最初の20文字程度が含まれていればOK
            tts_snippet = tts_text[:20].replace("。", "").replace("、", "")
            context_match = tts_snippet in prompt.replace("。", "").replace("、", "")
            result.items.append(CheckItem(
                code="P-1b",
                pillar="入力統制",
                severity="WARNING",
                passed=context_match,
                message=(
                    f"Context節にTTS発話内容が反映されている"
                    if context_match
                    else f"Context節にTTS「{tts_name}」の発話内容が見つからない "
                         f"(TTS: 「{tts_text[:40]}...」)"
                ),
            ))
        else:
            result.items.append(CheckItem(
                code="P-1b",
                pillar="入力統制",
                severity="WARNING",
                passed=True,
                message=f"TTS「{tts_name}」のプロパティが未定義（propertiesに記載なし — スキップ）",
            ))
    elif not tts_prompts:
        result.items.append(CheckItem(
            code="P-1b",
            pillar="入力統制",
            severity="WARNING",
            passed=True,
            message="propertiesが未指定のためTTS発話内容チェックをスキップ",
        ))

    # --- P-2: 前処理（STT profile_words） ---
    stt_name = upstream_name if upstream_kind == "stt" else None
    if stt_name and stt_name in modules:
        stt_mod = modules[stt_name]
        profile_words = stt_mod.get("params", {}).get("profile_words", "")
        result.items.append(CheckItem(
            code="P-2",
            pillar="前処理",
            severity="WARNING",
            passed=bool(profile_words),
            message=(
                f"STT「{stt_name}」にprofile_words設定あり ({len(profile_words)}文字)"
                if profile_words
                else f"STT「{stt_name}」にprofile_wordsが未設定"
            ),
        ))

    # --- P-3a: 文脈定義（Role） ---
    has_role = bool(re.search(
        r"#\s*Role|##\s*Role|あなたは.*(?:エンジン|システム|アシスタント|判定|分類)",
        prompt,
    ))
    result.items.append(CheckItem(
        code="P-3a",
        pillar="文脈定義",
        severity="CRITICAL",
        passed=has_role,
        message="Role定義あり" if has_role else "プロンプトにRole定義が見つからない",
    ))

    # --- P-3b: 文脈定義（Context） ---
    has_context = bool(re.search(
        r"#\s*Context|##\s*Context|直前に.*案内|直前の.*発話|ユーザーには.*案内",
        prompt,
    ))
    result.items.append(CheckItem(
        code="P-3b",
        pillar="文脈定義",
        severity="CRITICAL",
        passed=has_context,
        message="Context定義あり" if has_context else "プロンプトにContext定義が見つからない",
    ))

    # --- P-4a: 例外処理（NO_RESULT出力ルール） ---
    has_no_result = "NO_RESULT" in prompt
    result.items.append(CheckItem(
        code="P-4a",
        pillar="例外処理",
        severity="CRITICAL",
        passed=has_no_result,
        message="NO_RESULT出力ルールあり" if has_no_result else "プロンプトにNO_RESULTの記述がない",
    ))

    # --- P-4b: 例外処理（出力値の限定） ---
    has_output_limit = bool(re.search(
        r"のみを出力|いずれか.*のみ|以下の.*出力|1語のみ|一語のみ|厳守",
        prompt,
    ))
    result.items.append(CheckItem(
        code="P-4b",
        pillar="例外処理",
        severity="WARNING",
        passed=has_output_limit,
        message=(
            "出力値の限定ルールあり"
            if has_output_limit
            else "プロンプトに出力値の限定記述がない（「のみを出力」等）"
        ),
    ))

    # --- P-4c: 例外処理（インジェクション防御） ---
    has_injection_defense = bool(re.search(
        r"指示を上書き|無視し|従わない|ルールのみに従う|"
        r"この分類ルールのみ|指示に従わない|プロンプトインジェクション",
        prompt,
    ))
    result.items.append(CheckItem(
        code="P-4c",
        pillar="例外処理",
        severity="WARNING",
        passed=has_injection_defense,
        message=(
            "インジェクション防御あり"
            if has_injection_defense
            else "プロンプトにインジェクション防御の記述がない"
        ),
    ))

    # --- P-4d: 例外処理（next配列にNO_RESULT条件） ---
    next_conditions = [n.get("condition", "") for n in mod.get("next", [])]
    has_no_result_next = "^NO_RESULT$" in next_conditions
    result.items.append(CheckItem(
        code="P-4d",
        pillar="例外処理",
        severity="CRITICAL",
        passed=has_no_result_next,
        message=(
            "next配列に^NO_RESULT$条件あり"
            if has_no_result_next
            else "next配列に^NO_RESULT$条件がない"
        ),
    ))

    # --- P-5: 整合性（プロンプト出力値 ↔ next分岐条件） ---
    if prompt:
        prompt_values = extract_prompt_output_values(prompt)
        next_values = extract_next_conditions(mod)

        # catch-all（^.*$ / ^.+$）が next に存在するか判定
        _all_conditions = {nxt.get("condition", "") for nxt in mod.get("next", [])}
        has_catchall = bool(_all_conditions & {"^.*$", "^.+$"})

        if prompt_values and next_values:
            # NO_RESULTはnext側で別途チェック済みなので除外
            prompt_set = {v for v in prompt_values if v != "NO_RESULT"}
            next_set = set(next_values)

            missing_in_next = prompt_set - next_set
            missing_in_prompt = next_set - prompt_set

            # catch-all が存在する場合、prompt にあって next にない値は
            # catch-all で到達可能なため不一致としない
            if has_catchall:
                missing_in_next = set()

            passed = not missing_in_next and not missing_in_prompt
            details = []
            if missing_in_next:
                details.append(
                    f"プロンプトにあるがnextにない: {missing_in_next}"
                )
            if missing_in_prompt:
                details.append(
                    f"nextにあるがプロンプトにない: {missing_in_prompt}"
                )

            result.items.append(CheckItem(
                code="P-5",
                pillar="整合性",
                severity="CRITICAL",
                passed=passed,
                message=(
                    f"プロンプト出力値とnext分岐条件が一致 ({len(next_set)}件"
                    + (f", catch-all で{len(prompt_set - next_set)}件カバー" if has_catchall and prompt_set - next_set else "")
                    + ")"
                    if passed
                    else f"プロンプト出力値とnext分岐条件が不一致: {'; '.join(details)}"
                ),
            ))
        elif next_values:
            # プロンプトから出力値を抽出できなかった場合はスキップ
            result.items.append(CheckItem(
                code="P-5",
                pillar="整合性",
                severity="WARNING",
                passed=True,
                message=f"プロンプトから出力値リストを自動抽出できず（next分岐: {next_values}）— 手動確認推奨",
            ))

    return result


# ============================================================
# メイン関数
# ============================================================

def check_all_prompts(
    flow_data: dict,
    properties_path: str | None = None,
) -> list[PromptCheckResult]:
    """フローJSON内の全OpenAIモジュールに対してチェックを実行"""

    modules = flow_data.get("modules", {})
    reverse_map = build_reverse_map(modules)
    tts_prompts = parse_properties(properties_path) if properties_path else {}

    results = []
    for mod_name, mod in modules.items():
        if not is_openai(mod.get("type", "")):
            continue

        prompt = mod.get("params", {}).get("prompt", "")
        if not prompt:
            # プロンプト未記入（prompter未実行）→ 全チェックスキップ
            r = PromptCheckResult(module_name=mod_name)
            r.items.append(CheckItem(
                code="P-0",
                pillar="前提",
                severity="CRITICAL",
                passed=False,
                message="params.promptが空です（prompter未実行の可能性）",
            ))
            results.append(r)
            continue

        results.append(check_openai_module(
            mod_name, mod, modules, reverse_map, tts_prompts,
        ))

    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schemas/prompt_checker.py <flow.json> [--properties <props.md>]")
        sys.exit(1)

    json_path = sys.argv[1]
    props_path = None
    if "--properties" in sys.argv:
        idx = sys.argv.index("--properties")
        if idx + 1 < len(sys.argv):
            props_path = sys.argv[idx + 1]

    with open(json_path, encoding="utf-8") as f:
        flow_data = json.load(f)

    results = check_all_prompts(flow_data, props_path)

    total_critical = sum(r.critical_count for r in results)
    total_warning = sum(r.warning_count for r in results)

    print(f"\n=== プロンプト品質チェック結果 ===")
    print(f"対象: {json_path}")
    print(f"OpenAIモジュール数: {len(results)}")
    print(f"CRITICAL: {total_critical}  WARNING: {total_warning}")
    print()

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"--- {r.module_name} [{status}] ---")
        for item in r.items:
            icon = "✓" if item.passed else ("✗" if item.severity == "CRITICAL" else "△")
            print(f"  {icon} [{item.code}] {item.pillar}: {item.message}")
        print()

    sys.exit(0 if total_critical == 0 else 1)
