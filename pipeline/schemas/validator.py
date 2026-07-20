#!/usr/bin/env python3
"""
validator.py — ボイスボットフローJSON バリデーター

フローJSONがBrekeke IVR仕様に適合しているかを自動検証する。
生成→校閲パイプラインの最終検品工程として使用。

Usage:
    python schemas/validator.py output/reviewed_xxx.json
    python schemas/validator.py output/*.json
"""

import json
import sys
import re
import os
from dataclasses import dataclass, field

# Windows cp932 環境での日本語・特殊文字出力対応
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


# ============================================================
# 検証結果モデル
# ============================================================

@dataclass
class Issue:
    severity: str  # "CRITICAL", "WARNING", "INFO"
    code: str
    module: str
    field: str
    message: str
    # 修正の振り分け: auto / prompter / properties / fixer / human
    #   auto:       auto_fixer.py が fix_action に従って機械的に修正
    #   prompter:   OpenAI プロンプト文言の書き換え → prompter エージェント
    #   properties: IVR プロパティファイル (*.md) の修正 → properties エージェント
    #   fixer:      フロー構造の判断が必要 → fixer エージェント
    #   human:      設計判断 / 顧客確認が必要 → director 差し戻し or BLOCKER
    fix_category: str = "fixer"
    # 機械的修正の指示書（fix_category="auto" のときのみ参照）
    # 形式例:
    #   {"op": "set",       "path": ["modules", M, "params", "status"], "value": "2"}
    #   {"op": "set_next",  "module": M, "index": 0, "field": "nextModuleName", "value": "..."}
    #   {"op": "replace",   "path": [...], "find": "\\n", "replace": "\n"}
    #   {"op": "recalc_layout"}  -- レイアウト再計算が必要
    fix_action: dict = field(default_factory=dict)
    # block_mapper.py が付与するブロック名（設計書 YAML の scenario_flow[].step）
    block_name: str = ""

    @property
    def icon(self) -> str:
        return {"CRITICAL": "[C]", "WARNING": "[W]", "INFO": "[I]"}[self.severity]

    def __str__(self) -> str:
        return f"{self.icon} [{self.code}] {self.module} > {self.field}: {self.message}"

    def to_dict(self) -> dict:
        """JSON/Markdown レポート出力用の辞書化"""
        return {
            "severity":     self.severity,
            "code":         self.code,
            "module":       self.module,
            "field":        self.field,
            "message":      self.message,
            "fix_category": self.fix_category,
            "fix_action":   self.fix_action,
            "block_name":   self.block_name,
        }


@dataclass
class ValidationResult:
    file_path: str
    issues: list = field(default_factory=list)
    module_count: int = 0
    flow_name: str = ""

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "CRITICAL" for i in self.issues)

    @property
    def critical_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "CRITICAL")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARNING")

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "INFO")


# ============================================================
# ヘルパー
# ============================================================

def is_stt(mod_type: str) -> bool:
    return any(kw in mod_type for kw in ["AmiVoice", "DTMF AmiVoice", "Speech to Text"])

def is_tts(mod_type: str) -> bool:
    # Text To Speech 通常モジュール、および Re-confirmation node data（復唱TTS）を含む
    return ("Text To Speech$Text to speech" in mod_type
            or "Text To Speech$Re-confirmation node data" in mod_type)

def is_audio_reconfirmation(mod_type: str) -> bool:
    """ユーザーへ音声で読み上げる復唱系モジュール（TTS-001/SB-001 等の「通常TTSモジュール」
    としての構造チェックは対象外だが、STTの前段として音声を発話済みという意味では
    is_tts() 相当に扱いたい場面向け）。DOB Re-confirmation は next が
    timeout/error/invalid/success の4分岐で通常TTS（単一 Next Module）とは構造が異なるため
    is_tts() には含めず、この専用ヘルパーで判定する（slot: date_of_birth 専用カスタム部品）。
    """
    return is_tts(mod_type) or "TS Custom Module$DOB Re-confirmation" in mod_type

def is_retry(mod_type: str) -> bool:
    return "Speech Retry Counter" in mod_type or "Retry Counter" in mod_type

def is_save2db(mod_type: str) -> bool:
    return "Persistence$save2db" in mod_type

def is_persistence_main(mod_type: str) -> bool:
    """メインフローに配置すべき Persistence モジュール（サブモジュール禁止）"""
    return any(kw in mod_type for kw in [
        "saveCompletionFlag2db", "saveContext2DB", "saveContextModel2DB"
    ])


# ============================================================
# ルールコード → fix_category のデフォルト対応表
# ============================================================
# 明示的に Issue(...) 生成時に fix_category を指定している場合はそちらが優先。
# この表は未指定 (default="fixer") のままの Issue に対して post-processing で適用される。
# カテゴリ定義:
#   auto       — auto_fixer.py が機械的に修正
#   prompter   — OpenAI prompt 文言の修正が必要（prompter エージェント）
#   properties — IVR プロパティ (*.md) ファイルの修正が必要（properties エージェント）
#   fixer      — フロー構造の判断が必要（fixer エージェント、デフォルト）
#   human      — 設計判断が必要（director 差し戻し or BLOCKER）

RULE_CATEGORIES: dict[str, str] = {
    # properties (IVR プロパティファイル修正)
    "P-000":     "properties",
    "P-010":     "properties",
    "P-012":     "properties",  # Retry prompt 混入
    "P-013":     "properties",
    "P-014":     "properties",
    "P-015":     "properties",  # STT 個別 .uri= 設定
    "P-016":     "properties",
    "P-020":     "properties",

    # prompter (OpenAI prompt 文言)
    "PROMPT-001": "prompter",
    "PROMPT-002": "prompter",
    "PROMPT-003": "prompter",
    "PROMPT-004": "prompter",   # NO_RESULT 記述欠落
    # PROMPT-005 は CMR slot ↔ OpenAI 出力ラベル不整合。issue 内で auto/fixer を動的設定するため
    # ここではマッピングしない（Issue.fix_category 直接設定が優先される）

    # CMR / 4 層責任モデル（2026-04-28）
    "CMR-005": "auto",      # ^0$ next 不在 → scaffold 再生成
    "CMR-006": "auto",      # ^0$ ラベル "default" → "other" に rename
    "CMR-007": "fixer",     # ^0$ next の broken_ref / placeholder → fallback 先判断要

    # human (顧客確認 / 人間が埋めるべき TODO_)
    "P-030":  "human",      # properties TODO_ 残存（人間が確認して記入）
    "P-001":  "human",      # properties ファイル読み込み失敗

    # human (設計判断 / 顧客確認)
    "S-001":  "human",      # 必須フィールド欠落
    "S-002":  "human",      # フロー名形式不正
    "S-003":  "human",      # start 不正
    "N-001":  "human",      # 命名規則違反
    "N-002":  "human",
    "N-003":  "human",
    "CTX-012": "human",     # status 空（設計判断）
    "SF-TERM-001": "human", # 終話設計欠落
    "J-001":  "human",      # JSON パースエラー
    "J-002":  "human",
}


def finalize_categories(result: "ValidationResult") -> None:
    """Issue の fix_category を default のままのものに RULE_CATEGORIES を適用する"""
    for issue in result.issues:
        # 明示的に指定済み（auto/prompter/properties/human）は触らない
        if issue.fix_category != "fixer":
            continue
        cat = RULE_CATEGORIES.get(issue.code)
        if cat:
            issue.fix_category = cat


# ============================================================
# バリデーション関数群
# ============================================================

def validate_top_level(data: dict, result: ValidationResult):
    for f in ["name", "start", "modules"]:
        if f not in data:
            result.issues.append(Issue("CRITICAL", "S-001", "(root)", f,
                f"必須フィールド '{f}' が存在しません"))

    if "name" in data:
        result.flow_name = data["name"]
        if "$" not in data["name"]:
            result.issues.append(Issue("WARNING", "S-002", "(root)", "name",
                f"フロー名が 'グループ名$フロー名' 形式ではありません: {data['name']}"))

    if "modules" in data and "start" in data:
        if data["start"] not in data["modules"]:
            result.issues.append(Issue("CRITICAL", "S-003", "(root)", "start",
                f"startモジュール '{data['start']}' が modules 内に存在しません"))


def validate_transitions(data: dict, result: ValidationResult):
    if "modules" not in data:
        return

    module_names = set(data["modules"].keys())
    result.module_count = len(module_names)
    referenced = {data.get("start", "")}

    for mod_name, mod in data["modules"].items():
        # ラベル重複チェック
        labels = []
        # Brekeke 固有の "^*$" は Python の re では無効だが、incoming-classifier の
        # catch-all（ラベル「その他」）や get-header（WebRTC 専用・X-UA-EX 取込で唯一の
        # next となる catch-all）として Brekeke Flow Designer / scaffold_generator.py が
        # 自動生成する正規の値。T-005 の regex コンパイルチェックからは除外する。
        # acceptance_times は 4 分岐構成で catch-all を持たないため対象外。
        mod_type_for_regex = mod.get("type", "")
        brekeke_catchall_allowed = (
            "incoming-classifier" in mod_type_for_regex
            or "get-header" in mod_type_for_regex
        )
        for i, nxt in enumerate(mod.get("next", [])):
            label = nxt.get("label", "")
            if label:
                labels.append(label)
            # T-005: condition の正規表現構文チェック
            condition = nxt.get("condition", "")
            if condition:
                # Brekeke 仕様の "^*$"（catch-all）は許容モジュールではスキップ
                if condition == "^*$" and brekeke_catchall_allowed:
                    pass
                else:
                    try:
                        re.compile(condition)
                    except re.error as e:
                        result.issues.append(Issue("CRITICAL", "T-005", mod_name,
                            f"next[{i}].condition",
                            f"無効な正規表現 '{condition}' -- {e}"))
            target = nxt.get("nextModuleName", "")
            if target:
                referenced.add(target)
                if target not in module_names:
                    result.issues.append(Issue("CRITICAL", "T-001", mod_name,
                        f"next[{i}].nextModuleName",
                        f"遷移先 '{target}' が modules 内に存在しません"))

        # 同一モジュール内のラベル重複検出
        seen_labels = {}
        for label in labels:
            if label in seen_labels:
                result.issues.append(Issue("CRITICAL", "T-004", mod_name,
                    "next[].label",
                    f"ラベル '{label}' が重複しています — "
                    "同一モジュール内のnext配列でラベルは一意でなければなりません"))
            seen_labels[label] = True

        for i, sub in enumerate(mod.get("subs", [])):
            sub_name = sub.get("moduleName", "")
            if sub_name:
                referenced.add(sub_name)
                if sub_name not in module_names:
                    result.issues.append(Issue("CRITICAL", "T-003", mod_name,
                        f"subs[{i}].moduleName",
                        f"subs参照先 '{sub_name}' が modules 内に存在しません"))

    orphans = module_names - referenced
    for orphan in orphans:
        result.issues.append(Issue("WARNING", "T-002", orphan, "(module)",
            "どこからも参照されていない孤立モジュールです"))


def validate_stt_modules(data: dict, result: ValidationResult):
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        if not is_stt(mod.get("type", "")):
            continue

        next_list = mod.get("next", [])
        conditions = [n.get("condition", "") for n in next_list]
        targets = {n.get("condition", ""): n.get("nextModuleName", "") for n in next_list}

        # スロット数チェック（最大11: timeout/error/no_result/success + jump1〜jump7）
        if len(next_list) > 11:
            result.issues.append(Issue("CRITICAL", "STT-000", mod_name, "next",
                f"STT next は最大11スロットですが {len(next_list)} スロットになっています"))

        # TIMEOUT / ERROR / NO_RESULT チェック
        for cond in ["^TIMEOUT$", "^ERROR$", "^NO_RESULT$"]:
            if cond not in conditions:
                result.issues.append(Issue("CRITICAL", "STT-001", mod_name, "next",
                    f"STTに {cond} の遷移先がありません"))
            elif not targets.get(cond):
                result.issues.append(Issue("CRITICAL", "STT-002", mod_name, "next",
                    f"{cond} の遷移先が空です"))

        # success = ^.+$ 1本受けチェック
        if "^.+$" not in conditions or not targets.get("^.+$"):
            result.issues.append(Issue("CRITICAL", "STT-003", mod_name, "next",
                "success遷移 ^.+$ が定義されていません"))

        # 個別パターン禁止チェック
        # ^[*＊]$ は scaffold の repeat_star wiring（DTMF「*」単独押下→TTS再生）による
        # 構造的パターン（#264/31bb00be）。qa_validator S-2 側は既に許容済み・
        # こちら（post-build validator）も同様に reserved 扱いにする。
        reserved = {"^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", "^.*$", "",
                    "^[*＊]$"}
        bad_patterns = [c for c in conditions if c not in reserved]
        if bad_patterns:
            result.issues.append(Issue("CRITICAL", "STT-004", mod_name, "next",
                f"STTに個別パターンが含まれています（後続OpenAIで分岐すること）: {bad_patterns}"))


def validate_tts_modules(data: dict, result: ValidationResult):
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if not is_tts(mod_type):
            continue

        # Re-confirmation node data は通常の TTS と next ラベル体系が異なる
        # (timeout/error/success を使用) ため TTS-001 の "Next Module" 必須チェックから除外
        is_reconfirmation = "Re-confirmation node data" in mod_type

        # next label チェック
        if not is_reconfirmation:
            for i, nxt in enumerate(mod.get("next", [])):
                if nxt.get("nextModuleName") and nxt.get("label") != "Next Module":
                    result.issues.append(Issue("CRITICAL", "TTS-001", mod_name,
                        f"next[{i}].label",
                        f"TTS next label は 'Next Module' が必須ですが '{nxt.get('label')}' になっています"))

        # stop_by_dtmf チェック
        params = mod.get("params", {})
        if isinstance(params, dict):
            val = params.get("stop_by_dtmf", "")
            if val in ("true", "false"):
                result.issues.append(Issue("CRITICAL", "TTS-002", mod_name,
                    "params.stop_by_dtmf",
                    f"stop_by_dtmf は 'Yes'/'No' が必須ですが '{val}' になっています"))

        # TTS prompt 形式チェック
        # 現在許容される TTS 形式:
        #   - {tts_g: ...}    Google TTS (デフォルト)
        #   - {tts_ai: ...}   AI TTS (新仕様、本番稼働時にデフォルト移行予定)
        #   - {recstart}      STT 録音開始記号
        # Re-confirmation node data の {tts_g: #data#...} は別形式なのでスキップ
        if isinstance(params, dict) and not is_reconfirmation:
            prompt = params.get("prompt", "")
            if prompt and "{tts_g:" not in prompt and "{tts_ai:" not in prompt and prompt != "{recstart}":
                result.issues.append(Issue("INFO", "TTS-003", mod_name, "params.prompt",
                    "promptが {tts_g: ...} / {tts_ai: ...} 形式ではありません"
                    "（IVRプロパティで管理する場合は無視可）"))


def validate_openai_modules(data: dict, result: ValidationResult):
    """generate_by_OpenAI モジュールのパラメータチェック"""
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        if "generate_by_OpenAI" not in mod.get("type", ""):
            continue

        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue

        # module パラメータ（出力元モジュール名）チェック
        module_ref = params.get("module", "")
        if not module_ref:
            result.issues.append(Issue("CRITICAL", "OAI-001", mod_name, "params.module",
                "generate_by_OpenAI の module が空です（出力元のSTT/OpenAIモジュール名を設定してください）"))
        elif module_ref not in data.get("modules", {}):
            result.issues.append(Issue("CRITICAL", "OAI-002", mod_name, "params.module",
                f"generate_by_OpenAI の module '{module_ref}' が modules 内に存在しません"))

        # promptTTS は必ず空欄
        prompt_tts = params.get("promptTTS", "")
        if prompt_tts:
            result.issues.append(Issue("WARNING", "OAI-003", mod_name, "params.promptTTS",
                f"generate_by_OpenAI の promptTTS に値が設定されています（空欄にしてください）: {prompt_tts[:50]}"))

        # next配列の順序チェック（TIMEOUT/ERROR/NO_RESULTが先頭3スロット）
        next_list = mod.get("next", [])
        if len(next_list) >= 3:
            expected_order = ["^TIMEOUT$", "^ERROR$", "^NO_RESULT$"]
            actual_order = [n.get("condition", "") for n in next_list[:3]]
            if actual_order != expected_order:
                result.issues.append(Issue("WARNING", "OAI-004", mod_name, "next[0:3]",
                    f"generate_by_OpenAI の next 先頭3スロットは TIMEOUT/ERROR/NO_RESULT の順序が必須ですが "
                    f"{actual_order} になっています"))


def validate_retry_modules(data: dict, result: ValidationResult):
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        if not is_retry(mod.get("type", "")):
            continue

        next_list = mod.get("next", [])
        conditions = [n.get("condition", "") for n in next_list]
        labels = [n.get("label", "") for n in next_list]

        # condition は true/false
        if "true" not in conditions:
            result.issues.append(Issue("CRITICAL", "R-001", mod_name, "next",
                "Retry に condition='true' がありません"))
        if "false" not in conditions:
            result.issues.append(Issue("CRITICAL", "R-002", mod_name, "next",
                "Retry に condition='false' がありません"))

        # label は Retry/No more
        if "true" in conditions:
            idx = conditions.index("true")
            if labels[idx] != "Retry":
                result.issues.append(Issue("CRITICAL", "R-003", mod_name, f"next[{idx}].label",
                    f"condition='true' の label は 'Retry' が必須ですが '{labels[idx]}' になっています"))
        if "false" in conditions:
            idx = conditions.index("false")
            if labels[idx] != "No more":
                result.issues.append(Issue("CRITICAL", "R-004", mod_name, f"next[{idx}].label",
                    f"condition='false' の label は 'No more' が必須ですが '{labels[idx]}' になっています"))

        # retry_count チェック
        params = mod.get("params", {})
        if isinstance(params, dict) and not params.get("retry_count"):
            result.issues.append(Issue("WARNING", "R-005", mod_name, "params.retry_count",
                "retry_count が設定されていません（推奨: 1）"))


def validate_save2db(data: dict, result: ValidationResult):
    """save2dbのサブモジュール接続チェック"""
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")

        # TTS/STT に save2db サブモジュールが必要
        # ただし Re-confirmation node data は #data# 参照元の OpenAI が既に保存済みなので不要
        if (is_tts(mod_type) or is_stt(mod_type)) and "Re-confirmation node data" not in mod_type:
            subs = mod.get("subs", [])
            has_save2db = any(
                s.get("label", "").startswith("save-") and s.get("moduleName")
                for s in subs
            )
            if not has_save2db:
                result.issues.append(Issue("WARNING", "SB-001", mod_name, "subs",
                    "TTS/STTモジュールに save2db サブモジュールが接続されていません（音声録音に必須）"))

        # save2db が next 連鎖（通常フロー）のターゲットになっていないか
        # （save2db は modules に定義必須だが、next からは参照禁止。subs 経由のみ）
        if is_save2db(mod_type):
            if mod.get("next"):
                result.issues.append(Issue("CRITICAL", "SB-002", mod_name, "next",
                    "save2db に next 遷移が設定されています。save2db は subs 経由のみ接続可能です"))

        # saveCompletionFlag2db等がサブモジュールとして使われていないか
        # （サブモジュールとして使われているかはsubs参照では検出困難のため、
        #   メインフローへの配置はOKとしてチェックしない）

        # saveContext2DB の必須パラメータチェック
        if "saveContext2DB" in mod_type:
            params = mod.get("params", {})
            if isinstance(params, dict):
                ctx_name = params.get("contextName", "")
                ctx_value = params.get("contextValue", "")
                if not ctx_name:
                    result.issues.append(Issue("CRITICAL", "CTX-010", mod_name,
                        "params.contextName",
                        "saveContext2DB の contextName が空です"))
                if not ctx_value:
                    result.issues.append(Issue("CRITICAL", "CTX-011", mod_name,
                        "params.contextValue",
                        "saveContext2DB の contextValue が空です（保存する値が設定されていません）"))
                # コンテキスト参照の禁止チェック
                if ctx_value and "#data#" in ctx_value.lower():
                    result.issues.append(Issue("CRITICAL", "CTX-013", mod_name,
                        "params.contextValue",
                        f"saveContext2DB の contextValue に '#data#' 記法 '{ctx_value}' が使用されています — "
                        "'#data#' は Re-confirmation node data（TTS復唱）専用です。"
                        "saveContext2DB では固定文字列またはシステム変数（<% sys-customer-phone-number %> 等）のみ使用可能です"))

        # saveCompletionFlag2db の必須パラメータチェック
        if "saveCompletionFlag2db" in mod_type:
            params = mod.get("params", {})
            if isinstance(params, dict):
                status = params.get("status", "")
                if not status:
                    result.issues.append(Issue(
                        severity="CRITICAL", code="CTX-012", module=mod_name,
                        field="params.status",
                        message="saveCompletionFlag2db の status が空です",
                        fix_category="human",  # 適切な値は設計書判断
                    ))
                elif status in ("0", "5"):
                    result.issues.append(Issue(
                        severity="CRITICAL", code="COMP-001", module=mod_name,
                        field="params.status",
                        message=f"status=\"{status}\" は第2世代予約値のため使用禁止（許可: 1,2,3,6,7以降）",
                        fix_category="auto",
                        fix_action={"op": "set",
                                    "path": ["modules", mod_name, "params", "status"],
                                    "value": "2"},
                    ))

        # saveContextModel2DB の fields フォーマットチェック
        if "saveContextModel2DB" in mod_type:
            params = mod.get("params", {})
            if isinstance(params, dict):
                fields_str = params.get("fields", "")
                if fields_str and isinstance(fields_str, str):
                    if "\n" not in fields_str:
                        result.issues.append(Issue("WARNING", "CTX-014", mod_name,
                            "params.fields",
                            "saveContextModel2DB の fields がminified（1行）です — "
                            "動作には影響しませんが、Brekekeフローデザイナーでの目視確認が困難です。"
                            "scripts/format_fields.py で自動整形できます"))

                    # fields の displayType チェック
                    try:
                        fields_obj = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
                        if isinstance(fields_obj, list):
                            # displayType の重複チェック
                            # TEXT, NUMBER, DATE のみ重複可。それ以外は1つだけ
                            duplicable_types = {"TEXT", "NUMBER", "DATE"}
                            dtype_counts = {}
                            for field in fields_obj:
                                ctx_name = field.get("contextName", "")
                                disp_type = field.get("displayType", "")

                                if disp_type:
                                    if disp_type not in dtype_counts:
                                        dtype_counts[disp_type] = []
                                    dtype_counts[disp_type].append(ctx_name)

                                # clinicalDepartment は DEPARTMENT であること
                                if ctx_name == "clinicalDepartment" and disp_type != "DEPARTMENT":
                                    result.issues.append(Issue("CRITICAL", "CTX-016", mod_name,
                                        f"fields[clinicalDepartment].displayType",
                                        f"clinicalDepartment の displayType が '{disp_type}' です — "
                                        "'DEPARTMENT' を使用してください"))

                            # 重複不可の displayType が2つ以上ある場合
                            # 重複時の「残すべき contextName」ヒューリスティック。
                            # 該当 contextName がある場合はそれを残し、他を TEXT に倒す。
                            # 該当が無ければ先頭を残す。
                            preferred_context_by_dtype = {
                                "CLASSIFICATION": "classification",
                                "DEPARTMENT":     "clinicalDepartment",
                                "PATIENT_NAME":   "patientName",
                                "PHONE_NUMBER":   "patientPhoneNumber",
                                "DATE_OF_BIRTH":  "patientDateOfBirth",
                                "MEDICAL_CARD":   "medicalCardNumber",
                            }
                            for dtype, ctx_names in dtype_counts.items():
                                if dtype not in duplicable_types and len(ctx_names) > 1:
                                    preferred = preferred_context_by_dtype.get(dtype)
                                    keep = preferred if preferred in ctx_names else ctx_names[0]
                                    result.issues.append(Issue("CRITICAL", "CTX-017", mod_name,
                                        "fields[].displayType",
                                        f"displayType '{dtype}' が {len(ctx_names)} 件あります（{', '.join(ctx_names)}） — "
                                        f"'{dtype}' はフロー全体で1つのみ使用可です（重複可能なのは TEXT / NUMBER / DATE のみ）。"
                                        f"'{keep}' を残し、他を TEXT に自動置換します",
                                        fix_category="auto",
                                        fix_action={
                                            "op": "dedup_displaytype",
                                            "path": ["modules", mod_name, "params", "fields"],
                                            "display_type": dtype,
                                            "keep_context": keep,
                                            "fallback_type": "TEXT",
                                        }))
                    except (json.JSONDecodeError, TypeError):
                        pass  # パース失敗は別チェック（CTX-014）で検出済み


def validate_phone_subflow(data: dict, result: ValidationResult):
    """電話番号聴取サブフロー（旧: 別ファイル方式 / 新: メインフロー内インライン展開）の
    必須モジュール配置チェック。

    2026-07〜: 個人情報4種（氏名/生年月日/電話番号/診察券番号）は scaffold_generator が
    Jump to Flow を使わずメインフロー JSON 内へインライン展開する（CLAUDE.md「モジュール
    /script開発ポリシー」参照）。旧来の「ファイル名（data['name']）に '電話番号' を含む」
    判定だけでは新方式のメインフローを検出できず、本チェックが恒久的にスキップされる
    （PH-001/002/003 dormant）。認定済み電話種別判定スクリプト
    （modules/phone_type/script.js, MOBILE_REGEX マーカー持ち）の有無で
    インライン展開された電話スロットも検出する。
    """
    if "modules" not in data:
        return

    modules = data["modules"]
    flow_name = data.get("name", "")

    def _script_content(mod: dict) -> str:
        return mod.get("params", {}).get("script", "") or ""

    # インライン方式の電話スロットは build_phone_type_script が埋め込む認定スクリプト
    # （modules/phone_type/script.js, MOBILE_REGEX マーカー）で確実に検出できる
    phone_type_modules = [
        name for name, mod in modules.items()
        if "Script" in mod.get("type", "") and "MOBILE_REGEX" in _script_content(mod)
    ]
    has_inline_phone_slot = bool(phone_type_modules)
    is_legacy_phone_subflow_file = "電話番号" in flow_name

    if not (has_inline_phone_slot or is_legacy_phone_subflow_file):
        return

    # incoming-classifier が存在するか確認
    # インライン方式では opening 共通の「着信電話番号分類」とは別に、電話スロット専用の
    # incoming-classifier（着信分類_{step}）が必要 — opening 側だけでは充足させない
    has_incoming = False
    has_mobile_script = False
    has_aggregation_script = False
    for mod_name, mod in modules.items():
        mod_type = mod.get("type", "")
        if "incoming-classifier" in mod_type.lower() or "incoming" in mod_type.lower():
            if not has_inline_phone_slot or mod_name != "着信電話番号分類":
                has_incoming = True
        # script_携帯判別 or 携帯判別スクリプト
        if ("Script" in mod_type or "script" in mod_type):
            script_content = _script_content(mod)
            if "mobilePattern" in script_content or "MOBILE" in script_content:
                has_mobile_script = True
            if "携帯電話判別" in script_content and "携帯以外" in script_content:
                has_aggregation_script = True

    # インライン方式には旧来の「集約スクリプト」は存在せず、phone_type Script の
    # next[] 3値分岐（携帯/固定/その他）がその役割を兼ねる。ラベルの揃いで代替判定する。
    if has_inline_phone_slot and not has_aggregation_script:
        for name in phone_type_modules:
            labels = {n.get("label", "") for n in modules[name].get("next", []) if n.get("label")}
            if {"携帯", "その他"} <= labels:
                has_aggregation_script = True
                break

    if not has_incoming:
        result.issues.append(Issue("CRITICAL", "PH-001", "(flow)", "incoming-classifier",
            "電話番号聴取サブフローに incoming-classifier が配置されていません — "
            "着信番号の種別判定（携帯/固定/非通知等）に必要です"))

    if not has_mobile_script:
        result.issues.append(Issue("CRITICAL", "PH-002", "(flow)", "script_携帯判別",
            "電話番号聴取サブフローに携帯判別スクリプトが配置されていません — "
            "聴取した連絡先番号が携帯電話かどうかを正規表現で判定するスクリプトが必要です"))

    if not has_aggregation_script:
        result.issues.append(Issue("WARNING", "PH-003", "(flow)", "携帯かその他",
            "電話番号聴取サブフローに集約スクリプト（携帯かその他）が見つかりません — "
            "携帯電話判別/携帯以外の結果を集約して結果返却スクリプトに渡すスクリプトが推奨されます"))


def validate_script_modules(data: dict, result: ValidationResult):
    """スクリプトモジュールの検証"""
    if "modules" not in data:
        return

    flow_name = data.get("name", "")

    # サブフローかどうかを判定（聴取系のキーワードで判定）
    subflow_keywords = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取"]
    is_subflow = any(kw in flow_name for kw in subflow_keywords)

    # スクリプトモジュールの命名規則チェック（全フロー共通）
    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "Script" in mod_type or "script" in mod_type:
            if not mod_name.startswith("script_"):
                result.issues.append(Issue("WARNING", "SCR-001", mod_name, "name",
                    f"スクリプトモジュール名が 'script_' プレフィックスで始まっていません: {mod_name}"))

    # SCR-007: 未実装の scaffold stub がそのまま残っていないか（全フロー共通）
    # _build_faq_block（type: faq, method: script[既定]）は scaffold_generator が
    # 「TODO_scaffold」プレースホルダを埋め込み、prompter か gen_scripts.py が実装することを
    # 前提としているが、どちらの工程にも自動では拾われない（script_blocks: セクションは
    # scenario_flow の type: faq とは別物・prompter の担当範囲は generate_by_OpenAI のみ）。
    # このスタブは構文的に正しい ES5（$runner.setResult(text ? "NO_RESULT" : "NO_RESULT")）
    # のため常に NO_RESULT を返すだけで実行時エラーにならず、他のチェックでは検出できない。
    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "Script" in mod_type or "script" in mod_type:
            script_content = mod.get("params", {}).get("script", "")
            # TODO_script: load_script_template() のテンプレート未指定/未発見 fallback
            # ERROR: テンプレート/認定正本 が見つからない場合の fallback
            # いずれも構文上正しい ES5（常に空/NO_RESULT を返す）のため実行時に気付けない
            if ("TODO_script" in script_content
                    or "ERROR: テンプレート" in script_content
                    or "ERROR: 認定正本" in script_content):
                result.issues.append(Issue("CRITICAL", "SCR-007", mod_name, "params.script",
                    f"スクリプトモジュール '{mod_name}' に未実装スタブ（TODO_script）または"
                    f"テンプレート/認定正本の解決失敗スタブ（ERROR:）が残っています — "
                    f"構文上は正しいため実行時エラーにならないが、常に空/NO_RESULT を返すだけで"
                    f"実質無効です。script_template 名の確認、または認定部品の配線を見直してください"))
            elif "TODO_scaffold" in script_content:
                result.issues.append(Issue("CRITICAL", "SCR-007", mod_name, "params.script",
                    f"スクリプトモジュール '{mod_name}' が scaffold の未実装プレースホルダ（TODO_scaffold）"
                    f"のまま残っています — 構文上は正しいため実行時エラーにならず気付きにくいが、"
                    f"常に NO_RESULT 等の固定値を返すだけで実質無効です。"
                    f"type: faq, method: script の場合は script_blocks: セクション + gen_scripts.py で"
                    f"決定論生成するか、method: openai に切り替えるか、認定済みスクリプトを人手で実装してください"
                    f"（CLAUDE.md「新規 module/script の必須要件」参照）"))

    # サブフローの場合、結果返却スクリプトモジュールの存在チェック
    if is_subflow:
        has_result_script = False
        # パターン1: script_結果返却_* という名前のスクリプトモジュール（単一出口型）
        for mod_name, mod in data["modules"].items():
            mod_type = mod.get("type", "")
            if ("Script" in mod_type or "script" in mod_type) and "結果返却" in mod_name:
                has_result_script = True
                # スクリプト内容の検証
                script_content = mod.get("params", {}).get("script", "")
                if "getModuleResult" not in script_content:
                    result.issues.append(Issue("WARNING", "SCR-003", mod_name, "params.script",
                        "結果返却スクリプトに $runner.getModuleResult() の呼び出しがありません"))
                if "setResult" not in script_content:
                    result.issues.append(Issue("WARNING", "SCR-004", mod_name, "params.script",
                        "結果返却スクリプトに $runner.setResult() の呼び出しがありません"))
                if "setObject" not in script_content:
                    result.issues.append(Issue("WARNING", "SCR-005", mod_name, "params.script",
                        "結果返却スクリプトに $ivr.setObject() の呼び出しがありません — "
                        "setObject がないと結果がIVRセッションに永続化されず、メインフローが受け取れない場合があります"))
                if "getCurrentFlowName" not in script_content or "getRID" not in script_content:
                    result.issues.append(Issue("WARNING", "SCR-006", mod_name, "params.script",
                        "結果返却スクリプトに $runner.getCurrentFlowName() / $ivr.getRID() の呼び出しがありません — "
                        "setObject のキー生成に必要です（正しい形式: var key = flowName + '.' + rid）"))
                break

        # パターン2: 複数経路が各自 setResult() を呼ぶ構造（電話番号聴取型）
        # 任意のスクリプトモジュールが setResult() を含んでいれば結果返却とみなす
        if not has_result_script:
            for mod_name, mod in data["modules"].items():
                mod_type = mod.get("type", "")
                if "Script" in mod_type or "script" in mod_type:
                    script_content = mod.get("params", {}).get("script", "")
                    if "setResult" in script_content:
                        has_result_script = True
                        # パターン2のスクリプトにも同じ内容チェックを適用
                        if "setObject" not in script_content:
                            result.issues.append(Issue("WARNING", "SCR-005", mod_name, "params.script",
                                "結果返却スクリプトに $ivr.setObject() の呼び出しがありません — "
                                "setObject がないと結果がIVRセッションに永続化されず、メインフローが受け取れない場合があります"))
                        if "getCurrentFlowName" not in script_content or "getRID" not in script_content:
                            result.issues.append(Issue("WARNING", "SCR-006", mod_name, "params.script",
                                "結果返却スクリプトに $runner.getCurrentFlowName() / $ivr.getRID() の呼び出しがありません — "
                                "setObject のキー生成に必要です（正しい形式: var key = flowName + '.' + rid）"))
                        break

        if not has_result_script:
            result.issues.append(Issue("CRITICAL", "SCR-002", "(flow)", "script",
                f"サブフロー '{flow_name}' に結果返却スクリプトモジュール（script_結果返却_*）が配置されていません — "
                "全サブフローの出口に必須です"))


def validate_subflow_termination(data: dict, result: ValidationResult, design_termination: str = ""):
    """サブフロー内Disconnect整合性チェック（終話方式フラグ駆動）

    設計書の termination フラグと実際のDisconnect配置の整合性を検証する。
    - return（デフォルト）: サブフロー内にDisconnect禁止
    - self_contained: サブフロー内にDisconnect必須
    - 設計書フラグが不明な場合はWARNINGのみ
    """
    if "modules" not in data:
        return

    flow_name = data.get("name", "")

    # サブフローかどうかを判定
    subflow_keywords = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取"]
    is_subflow = any(kw in flow_name for kw in subflow_keywords)

    if not is_subflow:
        return

    # Disconnect モジュールの存在チェック
    has_disconnect = False
    disconnect_modules = []
    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "Disconnect" in mod_type:
            has_disconnect = True
            disconnect_modules.append(mod_name)

    # 終話方式フラグとの整合性チェック
    termination = design_termination.lower().strip() if design_termination else "return"

    if termination == "return" and has_disconnect:
        result.issues.append(Issue("CRITICAL", "SF-TERM-001", "(flow)", "termination",
            f"サブフロー '{flow_name}' の終話方式が return ですが、Disconnect モジュール "
            f"({', '.join(disconnect_modules)}) が配置されています — "
            "return の場合はサブフロー内にDisconnectを配置せず、メインフローに返却してください。"
            "サブフロー内で終話する場合は設計書の termination を self_contained に変更してください"))
    elif termination == "self_contained" and not has_disconnect:
        result.issues.append(Issue("WARNING", "SF-TERM-002", "(flow)", "termination",
            f"サブフロー '{flow_name}' の終話方式が self_contained ですが、Disconnect モジュールが "
            "配置されていません — self_contained の場合は終話チェーン（saveCompletionFlag2db + TTS + Disconnect）が必要です"))
    elif not design_termination and has_disconnect:
        # 設計書フラグが未指定でDisconnectがある場合はWARNING
        result.issues.append(Issue("WARNING", "SF-TERM-003", "(flow)", "termination",
            f"サブフロー '{flow_name}' に Disconnect モジュール ({', '.join(disconnect_modules)}) が "
            "配置されています。設計書の termination フラグが未設定のため、意図的な配置かどうか確認してください。"
            "意図的であれば設計書に termination: self_contained を明記してください"))


def validate_naming(data: dict, result: ValidationResult):
    """命名規則チェック"""
    if "modules" not in data:
        return

    # 環境依存文字パターン（丸数字等）
    env_dep_pattern = re.compile(
        r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳'
        r'㉑㉒㉓㉔㉕㉖㉗㉘㉙㉚㉛㉜㉝㉞㉟'
        r'㊱㊲㊳㊴㊵㊶㊷㊸㊹㊺㊻㊼㊽㊾㊿]'
    )
    bracket_pattern = re.compile(r'[（）()［］\[\]｛｝{}]')

    for mod_name in data["modules"].keys():
        if env_dep_pattern.search(mod_name):
            result.issues.append(Issue("CRITICAL", "N-001", mod_name, "name",
                "モジュール名に環境依存文字（丸数字等）が含まれています"))
        if bracket_pattern.search(mod_name):
            result.issues.append(Issue("CRITICAL", "N-002", mod_name, "name",
                "モジュール名に括弧が含まれています — Brekeke インポートで失敗する可能性があります"))
        if " " in mod_name or "\u3000" in mod_name:
            result.issues.append(Issue("CRITICAL", "N-003", mod_name, "name",
                "モジュール名にスペースが含まれています — Brekeke インポートで失敗する可能性があります"))


# ============================================================
# Layout チェック
# ============================================================

def validate_layout(data: dict, result: ValidationResult):
    """レイアウト座標の大量(0,0)検出"""
    if "modules" not in data:
        return

    total = len(data["modules"])
    if total == 0:
        return

    zero_count = 0
    zero_modules = []
    for mod_name, mod in data["modules"].items():
        layout = mod.get("layout", {})
        if isinstance(layout, dict):
            x = layout.get("x", 0)
            y = layout.get("y", 0)
            if x == 0 and y == 0:
                zero_count += 1
                zero_modules.append(mod_name)

    if total > 5 and zero_count / total > 0.5:
        result.issues.append(Issue(
            severity="CRITICAL", code="LAYOUT-001", module="(flow)", field="layout",
            message=f"{total}モジュール中{zero_count}モジュールのlayoutが(0,0)です — "
                    "layout座標の自動計算が実行されていない可能性があります。"
                    f"先頭5件: {zero_modules[:5]}",
            fix_category="auto",
            fix_action={"op": "recalc_layout"},
        ))
    elif zero_count > 2 and total > 1:
        result.issues.append(Issue(
            severity="CRITICAL", code="LAYOUT-002", module="(flow)", field="layout",
            message=f"{zero_count}モジュールのlayoutが(0,0)です: {zero_modules[:5]} — "
                    "視認性悪化により人間の修正コストが大幅に増加します",
            fix_category="auto",
            fix_action={"op": "recalc_layout"},
        ))

    # LAYOUT-003: 横並び（水平）レイアウト検出
    # y範囲が極端に小さいのにx範囲が大きい場合 → 縦方向への配置が行われていない
    if total > 5:
        all_x = [mod.get("layout", {}).get("x", 0)
                 for mod in data["modules"].values() if isinstance(mod.get("layout"), dict)]
        all_y = [mod.get("layout", {}).get("y", 0)
                 for mod in data["modules"].values() if isinstance(mod.get("layout"), dict)]
        if all_x and all_y:
            x_range = max(all_x) - min(all_x)
            y_range = max(all_y) - min(all_y)
            # 「主経路が縦方向」を満たさないケースのみ横並びと判定。
            #   - x_range が y_range より大きい、かつ
            #   - x_range が 2000px 超（分岐なしの単線なら x_range が小さい）
            # これにより「x:2000+ / y:10000+ （縦に長く、横にも展開した正常なフロー）」は許容
            if x_range > 2000 and x_range > y_range:
                result.issues.append(Issue(
                    severity="CRITICAL", code="LAYOUT-003", module="(flow)", field="layout",
                    message=f"フローが横並び（水平）に配置されています "
                            f"（x範囲:{x_range}px, y範囲:{y_range}px）— "
                            "主経路はy軸方向（上から下）に配置してください。視認性悪化により人間の修正コストが増加します",
                    fix_category="auto",
                    fix_action={"op": "recalc_layout"},
                ))

    # LAYOUT-004: 同座標モジュール検出（複数モジュールが同一 (x, y) に配置されている）
    coord_to_mods: dict[tuple[int, int], list[str]] = {}
    for mod_name, mod in data.get("modules", {}).items():
        layout = mod.get("layout", {})
        x = layout.get("x", 0)
        y = layout.get("y", 0)
        coord_to_mods.setdefault((x, y), []).append(mod_name)

    overlap_groups = {coord: mods for coord, mods in coord_to_mods.items()
                      if len(mods) > 1 and coord != (0, 0)}  # (0,0) は LAYOUT-001/002 で検出済み
    if overlap_groups:
        overlap_count = sum(len(mods) for mods in overlap_groups.values())
        example_coords = list(overlap_groups.items())[:3]
        examples_str = "; ".join(
            f"({x},{y}): {', '.join(mods[:3])}" for (x, y), mods in example_coords
        )
        result.issues.append(Issue(
            severity="CRITICAL", code="LAYOUT-004", module="(flow)", field="layout",
            message=f"{len(overlap_groups)}箇所で{overlap_count}モジュールが同一座標に重複配置されています — "
                    f"{examples_str}",
            fix_category="auto",
            fix_action={"op": "deoverlap_layout"},
        ))


# ============================================================
# サブフロー参照チェック
# ============================================================

# [#303] 参照元モジュール/コンテキストが実行時に emit しうる値の語彙（CMR 待受値の SSoT・複製）。
# CMR の moduleNValue がこの語彙外だと「実行時に決してマッチせず ^0$(other) に倒れる dead slot」。
# 値の出所（真の SSoT）: modules/phone_type/oracle.py の RESULT_*（携帯/固定/その他）と
# scaffold_generator.build_incoming_classifier() の emit ラベル（非通知/固定/海外/携帯/WebRTC/その他）。
# scaffold_generator.CMR_REFERENCE_VOCAB と同一内容（複製・要同期）。
# ドリフト防止: schemas/test_cmr_reference_vocab.py が両コピーの一致を保証。
CMR_REFERENCE_VOCAB = {
    "電話番号聴取":     {"携帯", "固定", "その他"},
    "phonetype":        {"携帯", "固定", "その他"},
    "phone_type":       {"携帯", "固定", "その他"},
    "着信電話番号分類": {"非通知", "固定", "海外", "携帯", "WebRTC", "その他"},
}


def _resolve_reference_vocab(reference: str):
    """CMR の moduleNName から、既知 emitter の値語彙(set)を返す（未知なら None）。
    '<%phonetype%>' 等の context 参照は <% %> と空白を剥がして突き合わせる。"""
    if not reference:
        return None
    key = reference.strip()
    if key.startswith("<%") and key.endswith("%>"):
        key = key[2:-2].strip()
    return CMR_REFERENCE_VOCAB.get(key)


def validate_cmr_reference_vocab(data: dict, result: ValidationResult):
    """ContextMatchRouter 待受値 vs 参照元 emitter の値語彙の整合性検証（CMR-008, #303 追加）

    終話分岐_*_phonetype（reference='電話番号聴取' / '<%phonetype%>'）や SMS_電話種別判定
    （reference='着信電話番号分類'）が、実行時には決して返らない値（'1' / 'MOBILE' 等）を
    待受値に持つと、CMR は常時マッチ 0 → ^0$(other) に倒れ、携帯着信の全経路が到達不能になる。

    このルールは **参照元が既知 emitter（CMR_REFERENCE_VOCAB のキー）に解決できる CMR のみ**を
    対象とし、非空スロット値が emit 語彙外なら CRITICAL を起票する（保守的＝未知参照は無視）。
    パイプライン生成物だけでなく **手動修正 BIVR（extract_bivr.py で展開した flow JSON）にも走る**
    のが本ルールの狙い（#303: 手動修正 BIVR は再生成されないため validator だけが救済路になる）。

    fix_category は fixer（'1'→'携帯' 等の意図推定はせず、設計 YAML 修正 or BIVR 手当を人間が判断）。
    catch-all 予約語（other/default 系）は CMR-002 の管轄なのでここでは対象外。
    """
    if "modules" not in data:
        return
    OTHER_TOKENS = {"other", "Other", "OTHER", "default", "Default", "DEFAULT", "_default_"}
    for mod_name, mod in data["modules"].items():
        if "ContextMatchRouter" not in mod.get("type", ""):
            continue
        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue
        for idx in (1, 2):
            vocab = _resolve_reference_vocab(params.get(f"module{idx}Name", ""))
            if vocab is None:
                continue
            ref = params.get(f"module{idx}Name", "")
            for slot in range(1, 11):
                val = params.get(f"module{idx}Value{slot}", "")
                if not val or val in OTHER_TOKENS:
                    continue
                if val not in vocab:
                    result.issues.append(Issue(
                        severity="CRITICAL", code="CMR-008", module=mod_name,
                        field=f"params.module{idx}Value{slot}",
                        message=f"待受値 '{val}' は参照元 '{ref}' が実行時に返す値の語彙 "
                                f"{sorted(vocab)} に含まれません — 実行時に決してマッチせず "
                                f"^0$(other) に倒れる dead slot です（#303 電話種別マッピング不整合）。"
                                f"設計書 YAML の conditions[].match を実値へ直して再生成、または手動修正 "
                                f"BIVR は該当 CMR の待受値を修正してください（'1'/'MOBILE' 等の推定変換はしません）。",
                        fix_category="fixer",
                    ))


def validate_cmr_default_token(data: dict, result: ValidationResult):
    """ContextMatchRouter の moduleNValueN に "default" リテラルが混入していないか検証

    設計書 conditions の `match: "default"` は catch-all 用であり、scaffold は
    これを `^0$` 分岐として処理しなければならない。誤って module1Value/2Value
    に "default" 文字列が書き込まれると、Brekeke は「default という文字列との完全比較」を
    実行してしまい catch-all として機能せず、フローが分岐しない事故になる。
    Medcity21 / リウマチ科みやもと（2026-04-27）で発覚。

    memory: feedback_cmr_subflow_context_resolution の追記参照
    """
    if "modules" not in data:
        return
    DEFAULT_TOKENS = {"default", "Default", "DEFAULT", "_default_"}
    for mod_name, mod in data["modules"].items():
        if "ContextMatchRouter" not in mod.get("type", ""):
            continue
        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue
        for key, val in params.items():
            if not (key.startswith("module1Value") or key.startswith("module2Value")):
                continue
            if val in DEFAULT_TOKENS:
                result.issues.append(Issue("CRITICAL", "CMR-002", mod_name,
                    f"params.{key}",
                    f"ContextMatchRouter の {key}='{val}' は catch-all 用の予約語ですが、"
                    f"値リテラルとして書き込まれています。設計書 conditions の "
                    f"match: \"default\" は scaffold が `^0$` 分岐に変換するため、"
                    f"moduleNValueN には書き込まれません。scaffold 再実行で修正されます"))


def validate_cmr_modules(data: dict, result: ValidationResult):
    """ContextMatchRouter の module1Name/module2Name が実在モジュール名か検証

    Brekeke の Module1 Name/Module2 Name は **モジュール名** を要求し、
    Brekeke はそのモジュールが context に保存した値を内部で読む（director.md L.179 参照）。
    context 名（例: 'classification', 'phonetype'）や生の変数名を渡すと Brekeke は
    モジュール検索に失敗して broken_ref と同等の状態になるため、本番投入前に必ず止める。

    変数を渡す Brekeke 仕様 `<%変数名%>` フォーマットは現状未使用（動作保証外）。
    本ルールでは `<%...%>` 形式は許容して通す。

    検出パターン:
      - reference_module の context 名指定が scaffold_generator の逆引きで解決できなかった
      - subflow 戻り値の context が SUBFLOW_RETURN_CONTEXTS に未登録
      - サブフロー / 出力先システム変数 (incoming-classifier 等) を context 名で書いた

    memory: feedback_cmr_subflow_context_resolution
    """
    if "modules" not in data:
        return

    modules = data["modules"]
    for mod_name, mod in modules.items():
        if "ContextMatchRouter" not in mod.get("type", ""):
            continue
        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue
        for key in ("module1Name", "module2Name"):
            ref = params.get(key, "")
            if not ref:
                continue
            # Brekeke 変数フォーマット <%var%> は通す（現状未使用だが仕様上許容）
            if ref.startswith("<%") and ref.endswith("%>"):
                continue
            # モジュール名として実在しなければ CRITICAL
            if ref not in modules:
                result.issues.append(Issue("CRITICAL", "CMR-001", mod_name,
                    f"params.{key}",
                    f"ContextMatchRouter の {key}='{ref}' は実在しないモジュール名です。"
                    f"Brekeke は Module1/2 Name にモジュール名を要求し、context 名や変数名の直接指定は不可。"
                    f"設計書 YAML の reference_module をモジュール名（例: 'OpenAI_用件確認', '電話番号聴取'）"
                    f"に書き直してください（.claude/agents/director.md / モジュール選定ガイド §3.x 参照）"))


def validate_cmr_other_branch(data: dict, result: ValidationResult):
    """ContextMatchRouter の `^0$ other` 安全網ルール検証（2026-04-28 追加）

    4 層責任モデル: CMR の `^0$` は「最後に残った排他的分岐」として設計時に意図して使う。
    prompter↔CMR ズレ時の救済路を兼ねるため、必ず存在しラベル "other" 統一が必須。

    検出:
      - CMR-005 (CRITICAL): `^0$` next が存在しない → ズレ時に dead-end
      - CMR-006 (WARNING):  `^0$` next のラベルが "other" でない（"default" 等の旧表記）
      - CMR-007 (CRITICAL): `^0$` next の nextModuleName が broken_ref（存在しないモジュール）
                           or 空文字 or "TODO_other_target" placeholder

    fix_category:
      - CMR-005: auto (scaffold 再生成で補完可能、ただし YAML に match: "other" 必須)
      - CMR-006: auto (label rename のみ、機械修正可)
      - CMR-007: fixer (適切な fallback 先の判断は LLM 必要)
    """
    if "modules" not in data:
        return
    modules = data["modules"]
    PLACEHOLDER_TARGETS = {"", "TODO_other_target", "TODO"}

    for mod_name, mod in modules.items():
        if "ContextMatchRouter" not in mod.get("type", ""):
            continue
        next_list = mod.get("next") or []
        zero_branch = None
        for n in next_list:
            if isinstance(n, dict) and n.get("condition") == "^0$":
                zero_branch = n
                break

        # CMR-005: ^0$ next が存在しない
        if zero_branch is None:
            result.issues.append(Issue(
                severity="CRITICAL", code="CMR-005", module=mod_name,
                field="next",
                message="ContextMatchRouter に `^0$ other` next が存在しません — "
                        "明示値以外が来た時に dead-end になります。設計書 YAML の "
                        "conditions に `match: \"other\"` 分岐を追加して scaffold を再生成してください。",
                fix_category="auto",
            ))
            continue

        # CMR-006: ラベルが "other" でない
        label = zero_branch.get("label", "")
        if label != "other":
            # fix_action を埋めて _apply_set で機械修正
            zero_idx = next((i for i, n in enumerate(next_list) if n.get("condition") == "^0$"), None)
            fix_action: dict = {}
            if zero_idx is not None:
                fix_action = {
                    "op": "set",
                    "path": ["modules", mod_name, "next", zero_idx, "label"],
                    "value": "other",
                }
            result.issues.append(Issue(
                severity="WARNING", code="CMR-006", module=mod_name,
                field="next.^0$.label",
                message=f"^0$ 分岐のラベルが '{label}' です。'other' に統一してください "
                        f"（4 層責任モデル参照、auto_fixer で自動修正可能）",
                fix_category="auto",
                fix_action=fix_action,
            ))

        # CMR-007: ^0$ next の nextModuleName が broken_ref / placeholder
        target = zero_branch.get("nextModuleName", "")
        if target in PLACEHOLDER_TARGETS:
            result.issues.append(Issue(
                severity="CRITICAL", code="CMR-007", module=mod_name,
                field="next.^0$.nextModuleName",
                message=f"^0$ other 分岐の遷移先が未指定 (target='{target}') です。"
                        f"設計書 YAML の `match: \"other\"` 条件に明示的な next を指定してください "
                        f"（暗黙のフォールバックは推定しません）",
                fix_category="fixer",
            ))
        elif target and target not in modules:
            result.issues.append(Issue(
                severity="CRITICAL", code="CMR-007", module=mod_name,
                field="next.^0$.nextModuleName",
                message=f"^0$ other 分岐の遷移先 '{target}' が存在しないモジュール (broken_ref) です。"
                        f"設計書 YAML の `match: \"other\"` 条件の next 先モジュールを存在するものに修正してください",
                fix_category="fixer",
            ))


def validate_openai_consumer_consistency(data: dict, result: ValidationResult):
    """OpenAI 出力仕様 vs CMR slot 値の整合性検証（PROMPT-005, 2026-04-28 追加）

    prompter が SKILL に従って書いた OpenAI 出力仕様（prompt 内の列挙ラベル）と、
    後段で OpenAI を参照する CMR の moduleXValue1〜10 が整合しているか検証する。

    不整合の場合:
      - CMR slot が OpenAI 出力に無い値を持つ → その slot は到達不能 (dead slot)
      - OpenAI 出力が CMR slot に無い値 → CMR は ^0$ other に流す（設計意図次第で問題）

    本検証では「**slot に書かれた値 V が OpenAI 出力ラベル集合に存在するか**」のみ機械検出。
    値が存在しない場合は CRITICAL（設計意図にかかわらず slot が死んでいる）。

    fix_category:
      - auto: OpenAI 出力ラベル集合に類似値が 1 つだけ存在する場合（曖昧性なくリネーム可能）
      - fixer: 類似値が複数 or 無い場合（LLM 判断要）

    依存: schemas/module_graph.py の find_cmr_consumers
    """
    if "modules" not in data:
        return

    # 個人情報サブフロー等はスキップ（リファレンスからコピーのため）
    flow_name = data.get("name", "")
    skip_keywords = ["氏名聴取", "生年月日聴取", "電話番号聴取", "診察券番号聴取"]
    if any(kw in flow_name for kw in skip_keywords):
        return

    # find_cmr_consumers を使うため module_graph.py をインポート
    try:
        from schemas.module_graph import find_cmr_consumers
    except ImportError:
        try:
            from .module_graph import find_cmr_consumers
        except ImportError:
            from module_graph import find_cmr_consumers

    for mod_name, mod in data["modules"].items():
        if "generate_by_OpenAI" not in mod.get("type", ""):
            continue
        params = mod.get("params", {}) or {}
        prompt = params.get("prompt", "")
        if not prompt:
            continue  # PROMPT-003 で別途検出

        # prompt から出力ラベルを抽出（既存 validate_prompt_labels と同じロジックを再利用したいが
        # 関数内ローカル実装のため、ここでは簡易版を再実装。将来 _extract_prompt_labels に切り出し）
        prompt_labels = _extract_output_labels_from_prompt(prompt)
        if not prompt_labels:
            continue

        # この OpenAI モジュールを参照する CMR を全件取得
        cmr_consumers = find_cmr_consumers(data, mod_name)
        for c in cmr_consumers:
            cmr_name = c["cmr_name"]
            for slot_idx, slot_value in c["slot_values"]:
                if slot_value not in prompt_labels:
                    # 類似一致が 1 つだけあれば auto、それ以外は fixer
                    similar = [lab for lab in prompt_labels if slot_value in lab or lab in slot_value]
                    fix_cat = "auto" if len(similar) == 1 else "fixer"
                    issue_kwargs = dict(
                        severity="CRITICAL", code="PROMPT-005", module=cmr_name,
                        field=f"params.module{c['module_index']}Value{slot_idx}",
                        message=f"CMR slot '{slot_value}' が OpenAI '{mod_name}' の prompt 出力仕様 "
                                f"{sorted(prompt_labels)[:8]}{'...' if len(prompt_labels) > 8 else ''} に存在しません — "
                                f"OpenAI はこの値を出さないため slot 1〜10 のこの分岐は到達不能 (dead slot)。"
                                + (f" 類似ラベル候補: '{similar[0]}'" if fix_cat == "auto" else " fixer 判断要"),
                        fix_category=fix_cat,
                    )
                    if fix_cat == "auto":
                        # module1Value と module2Value 両方を新値にリネーム（CMR は両 slot ペア比較のため）
                        issue_kwargs["fix_action"] = {
                            "op": "set",
                            "path": ["modules", cmr_name, "params", f"module{c['module_index']}Value{slot_idx}"],
                            "value": similar[0],
                        }
                    result.issues.append(Issue(**issue_kwargs))


def _extract_output_labels_from_prompt(prompt: str) -> set:
    """prompt 内の出力仕様セクションから列挙ラベルを抽出する簡易版。

    将来は validate_prompt_labels 内のロジックを共通ヘルパーに切り出して再利用する。
    現時点では PROMPT-005 用に独立実装。
    """
    labels: set = set()
    in_output_section = False
    _LIST_MARKER = re.compile(r'^[-\*・•]\s*(.+?)$')
    _TRIGGER_HEADER = re.compile(
        r'(出力.*(?:仕様|値|候補|形式|は|とは))|'
        r'(以下の(?:いずれか|どれか|値|語).*出力)|'
        r'(次の(?:いずれか|どれか|値|語).*出力)'
    )

    def _clean(label: str) -> str:
        s = label.strip()
        s = re.sub(r'[。、:：（(].*$', '', s).strip()
        s = s.rstrip('*').strip()
        return s

    for line in prompt.split("\n"):
        stripped = line.strip()
        if re.match(r'^#.*出力', stripped) or _TRIGGER_HEADER.search(stripped):
            in_output_section = True
            continue
        if in_output_section and stripped.startswith("#") and "出力" not in stripped:
            in_output_section = False
            continue
        if in_output_section:
            m = _LIST_MARKER.match(stripped)
            if m:
                label = _clean(m.group(1))
                if label and label != "NO_RESULT" and 1 <= len(label) <= 40 and not label.startswith("-"):
                    labels.add(label)
    return labels


def validate_node_reference(data: dict, result: ValidationResult):
    """params.nodeName（復唱/保存ノードの参照モジュール）の broken_ref 検証（NODE-001, #358）

    `drjoy^Text To Speech$Re-confirmation node data`（復唱・#data# 参照元）と
    `drjoy^Persistence$saveNodeData2Session`（ノード値保存）は params.nodeName に
    「対象モジュール名」を持つ。ここが存在しないモジュールを指すと、復唱が実行時に空/破綻し、
    保存も解決不能になる（#348 で rename 追従と --verify ダングリング検出は塞いだが、
    毎パイプライン実行の構造 validator には参照実在チェックが無く手書き/stale が素通りしていた）。

    検出:
      - NODE-001 (CRITICAL): 非空 nodeName が modules に存在しない（broken_ref）

    誤検出防止:
      - 空 `""` はスキップ（受入済みフローに実在する正当パターン）
      - `<%context名%>` 形はスキップ（context 直接参照。CMR module1Name と同じ扱い）

    fix_category=fixer（正しい参照先の判断は人間/壁打ち。CMR-007 と同型）。
    """
    if "modules" not in data:
        return
    modules = data["modules"]
    for mod_name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        params = mod.get("params")
        if not isinstance(params, dict):
            continue
        node_name = (params.get("nodeName") or "").strip()
        if not node_name:
            continue  # 空は正当（復唱対象なし）
        if node_name.startswith("<%") and node_name.endswith("%>"):
            continue  # context 直接参照はモジュール実在チェック対象外
        if node_name not in modules:
            result.issues.append(Issue(
                severity="CRITICAL", code="NODE-001", module=mod_name,
                field="params.nodeName",
                message=f"params.nodeName='{node_name}' が存在しないモジュール (broken_ref) です。"
                        f"復唱(#data# 参照元)/ノード保存の対象が実行時に解決できず、復唱が空/破綻します。"
                        f"nodeName を実在するモジュール名へ修正してください"
                        f"（OpenAI→script リネーム等で stale になった場合は #348 の rename 追従で追随します）。",
                fix_category="fixer",
            ))


def validate_subflow_references(data: dict, result: ValidationResult):
    """Custom Jump to Flow のサブフロー存在チェック"""
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "Custom Jump to Flow" not in mod_type:
            continue

        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue

        flowname = params.get("flowname", "")
        if not flowname:
            result.issues.append(Issue("CRITICAL", "FLOW-004", mod_name,
                "params.flowname",
                "Custom Jump to Flow の flowname が空です — "
                "遷移先サブフローが未設定です"))

        # FLOW-005 は削除: Custom Jump to Flow の properties 空チェックは不要
        # （デフォルト Jump to Flow は使用しない。properties 空でも Brekeke は正常動作する）


# ============================================================
# DTMF モジュールチェック
# ============================================================

def validate_dtmf_modules(data: dict, result: ValidationResult):
    """DTMF AmiVoice STT Input モジュールの詳細パラメータチェック"""
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "DTMF AmiVoice" not in mod_type:
            continue

        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue

        # DTMF-001: prompt に {recstart} が必要
        prompt = params.get("prompt", "")
        if "{recstart}" not in prompt:
            result.issues.append(Issue("CRITICAL", "DTMF-001", mod_name,
                "params.prompt",
                f"DTMFモジュールの prompt に {{recstart}} が含まれていません — "
                "DTMF録音開始マーカーが必須です"))

        # DTMF-002: max_dtmf_length が未設定
        max_len = params.get("max_dtmf_length", "")
        if not max_len:
            result.issues.append(Issue("WARNING", "DTMF-002", mod_name,
                "params.max_dtmf_length",
                "max_dtmf_length が未設定です（デフォルト10）"))

        # DTMF-003: retry が "0"
        retry = params.get("retry", "")
        if retry == "0":
            result.issues.append(Issue("WARNING", "DTMF-003", mod_name,
                "params.retry",
                "DTMFモジュールの retry が '0' です — 最低1以上を推奨"))

        # DTMF-004: termdtmf / remove_term / stop_play_when_speech が未設定
        missing = []
        for p in ["termdtmf", "remove_term", "stop_play_when_speech"]:
            if not params.get(p, ""):
                missing.append(p)
        if missing:
            result.issues.append(Issue("WARNING", "DTMF-004", mod_name,
                "params",
                f"DTMFモジュールの必須パラメータが未設定です: {', '.join(missing)}"))


# ============================================================
# STT前段チェック（TTS/Retryが直前にあるか）
# ============================================================

def validate_stt_predecessors(data: dict, result: ValidationResult):
    """STTモジュールの直前にTTSまたはRetryCounterがあるかチェック（FLOW-006）"""
    if "modules" not in data:
        return

    modules = data["modules"]

    # 全モジュールの逆引きマップを構築（target → {predecessor, ...}）
    predecessors: dict[str, set] = {mod_name: set() for mod_name in modules}
    for mod_name, mod in modules.items():
        for next_item in mod.get("next", []):
            target = next_item.get("nextModuleName", "")
            if target and target in predecessors:
                predecessors[target].add(mod_name)

    for mod_name, mod in modules.items():
        mod_type = mod.get("type", "")
        if not is_stt(mod_type):
            continue

        preds = predecessors.get(mod_name, set())
        if not preds:
            continue  # 前段なし（startモジュールにSTTが来ることは通常ない）

        has_valid_pred = any(
            is_audio_reconfirmation(modules[p].get("type", "")) or is_retry(modules[p].get("type", ""))
            for p in preds if p in modules
        )
        if not has_valid_pred:
            pred_names = ", ".join(sorted(preds))
            result.issues.append(Issue("WARNING", "FLOW-006", mod_name, "predecessors",
                f"STTモジュール '{mod_name}' の直前にTTS/Retryモジュールがありません "
                f"（前段モジュール: {pred_names}）— "
                "STTの前には必ずTTSで質問を発話してください"))


# ============================================================
# フロー冒頭チェーン構造チェック
# ============================================================

def validate_flow_structure(data: dict, result: ValidationResult):
    """冒頭チェーン構造の検証（wait → saveContextModel2DB → ...）"""
    if "modules" not in data or "start" not in data:
        return

    flow_name = data.get("name", "")
    # サブフローは冒頭チェーン構造が異なるためスキップ
    subflow_keywords = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取"]
    if any(kw in flow_name for kw in subflow_keywords):
        return

    modules = data["modules"]
    start_name = data["start"]

    if start_name not in modules:
        return  # S-003 で検出済み

    start_mod = modules[start_name]

    # FLOW-001: startモジュールがwait系であること
    # wait は params.wait が設定されているか、モジュール名に「待ち時間」「wait」を含む
    start_params = start_mod.get("params", {})
    has_wait = False
    if isinstance(start_params, dict) and start_params.get("wait", ""):
        has_wait = True
    if "待ち時間" in start_name.lower() or "wait" in start_name.lower():
        has_wait = True
    if not has_wait:
        result.issues.append(Issue("CRITICAL", "FLOW-001", start_name,
            "start",
            f"startモジュール '{start_name}' がwait（冒頭待ち時間）モジュールではありません — "
            "冒頭に wait 2000ms が必須です"))

    # 冒頭チェーンを3ホップたどる
    chain = [start_name]
    current = start_name
    for _ in range(3):
        mod = modules.get(current, {})
        next_list = mod.get("next", [])
        if not next_list:
            break
        # 最初の有効な遷移先を取得
        next_mod = ""
        for n in next_list:
            nm = n.get("nextModuleName", "")
            if nm:
                next_mod = nm
                break
        if not next_mod or next_mod not in modules:
            break
        chain.append(next_mod)
        current = next_mod

    # FLOW-002/003: saveContextModel2DB が冒頭チェーンに含まれるか
    has_save_ctx_model = False
    for mod_name in chain:
        mod = modules.get(mod_name, {})
        if "saveContextModel2DB" in mod.get("type", ""):
            has_save_ctx_model = True
            break

    if not has_save_ctx_model:
        if len(chain) >= 2:
            result.issues.append(Issue("CRITICAL", "FLOW-002", chain[0],
                "冒頭チェーン",
                f"冒頭チェーン {' → '.join(chain[:4])} に saveContextModel2DB が含まれていません"))
        else:
            result.issues.append(Issue("WARNING", "FLOW-003", "(flow)",
                "冒頭チェーン",
                "冒頭チェーンが短すぎます — saveContextModel2DB の配置を確認してください"))


# ============================================================
# PROMPT ラベル整合性チェック
# ============================================================

def validate_prompt_labels(data: dict, result: ValidationResult):
    """OpenAIモジュールのnext分岐ラベルとprompt出力仕様の突合せ"""
    if "modules" not in data:
        return

    flow_name = data.get("name", "")
    # 個人情報サブフローはスキップ（リファレンスからコピーのため）
    skip_keywords = ["氏名聴取", "生年月日聴取", "電話番号聴取", "診察券番号聴取"]
    if any(kw in flow_name for kw in skip_keywords):
        return

    for mod_name, mod in data["modules"].items():
        if "generate_by_OpenAI" not in mod.get("type", ""):
            continue

        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue

        prompt = params.get("prompt", "")

        # PROMPT-003: prompt が空欄
        if not prompt:
            result.issues.append(Issue(
                severity="CRITICAL", code="PROMPT-003", module=mod_name,
                field="params.prompt",
                message="OpenAIモジュールの prompt が空欄です — prompter未実行の可能性があります",
                fix_category="prompter",
            ))
            continue

        # next配列から分岐ラベルを抽出（TIMEOUT/ERROR/NO_RESULT/空/ワイルドカードを除外）
        skip_conditions = {"^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", "^.*$", ""}
        next_labels = set()
        has_wildcard = False
        for nxt in mod.get("next", []):
            cond = nxt.get("condition", "")
            if cond in skip_conditions:
                if cond in ("^.+$", "^.*$"):
                    has_wildcard = True
                continue
            # ^ラベル$ → ラベル を抽出
            label = cond.strip("^$")
            if label:
                next_labels.add(label)

        # 分岐がない（ワイルドカードのみ）場合は出力仕様チェックをスキップ
        if not next_labels and has_wildcard:
            # PROMPT-004: ワイルドカードのみの場合でもNO_RESULTの考慮を確認
            if "NO_RESULT" not in prompt:
                result.issues.append(Issue("WARNING", "PROMPT-004", mod_name,
                    "params.prompt",
                    "ワイルドカード分岐ですが、prompt内にNO_RESULTの記述がありません"))
            continue

        if not next_labels:
            continue

        # prompt から出力仕様セクションのラベルを抽出
        # 対応パターン:
        #  (a) `# XXX出力` ヘッダー以降のリスト行（マーカー: -, *, ・, •）
        #  (b) 「出力は以下の[いずれか|どれか|値]」等の文言以降のリスト行
        #  (c) 「出力: A / B / C」形式のインライン区切りリスト
        #  (d) Few-Shot の「出力: XXX」行（追加のラベル拾い）
        prompt_labels = set()
        in_output_section = False

        _LIST_MARKER = re.compile(r'^[-\*・•]\s*(.+?)$')
        _INLINE_OUTPUT = re.compile(r'^出力\s*[:：]\s*(.+)$')
        _TRIGGER_HEADER = re.compile(
            r'(出力.*(?:仕様|値|候補|形式|は|とは))|'
            r'(以下の(?:いずれか|どれか|値|語).*出力)|'
            r'(次の(?:いずれか|どれか|値|語).*出力)|'
            r'(出力.*(?:1語|一語).*(?:いずれか|どれか).*)'
        )

        def _clean(label: str) -> str:
            """末尾の句読点・記号・注釈を除去"""
            s = label.strip()
            s = re.sub(r'[。、:：（(].*$', '', s).strip()
            s = s.rstrip('*')
            return s

        for line in prompt.split("\n"):
            stripped = line.strip()

            # セクション開始検出（# ヘッダー or 本文トリガー）
            if re.match(r'^#.*出力', stripped) or _TRIGGER_HEADER.search(stripped):
                in_output_section = True
                # トリガー行内にインライン列挙があれば拾う（例: "出力は A / B / C から選択"）
                inline_m = re.search(r'(?:出力|候補).*?[:：は]?\s*([ぁ-ヿ一-龥A-Za-z0-9_ \\/／、・]+(?:\s*[・・/／、]\s*[ぁ-ヿ一-龥A-Za-z0-9_ \\/／、・]+)+)', stripped)
                if inline_m:
                    for part in re.split(r'\s*[・/／、]\s*', inline_m.group(1)):
                        label = _clean(part)
                        if label and label != "NO_RESULT" and 1 <= len(label) <= 40:
                            prompt_labels.add(label)
                continue

            # 次の # ヘッダーでセクション離脱（「出力」含む見出しは継続）
            if in_output_section and stripped.startswith("#") and "出力" not in stripped:
                in_output_section = False
                continue

            # セクション内: リストマーカー（-, *, ・, •）行
            if in_output_section:
                if re.match(r'^-{2,}$', stripped):
                    continue
                m = _LIST_MARKER.match(stripped)
                if m:
                    label = _clean(m.group(1))
                    if label and label != "NO_RESULT" and not label.startswith("-"):
                        prompt_labels.add(label)

            # セクション外でも「出力: XXX」形式は Few-Shot として拾う
            im = _INLINE_OUTPUT.match(stripped)
            if im:
                label = _clean(im.group(1))
                # Few-Shot の値は通常1語。スペース区切りの最初のトークンだけ取る
                label = label.split()[0] if label else ""
                if label and label != "NO_RESULT" and 1 <= len(label) <= 40:
                    prompt_labels.add(label)

        # PROMPT-001: next分岐ラベルがprompt出力仕様にない
        for label in next_labels:
            if label not in prompt_labels:
                result.issues.append(Issue(
                    severity="CRITICAL", code="PROMPT-001", module=mod_name,
                    field=f"next.condition=^{label}$",
                    message=f"next分岐ラベル '{label}' がprompt出力仕様に存在しません — "
                            "OpenAIの応答がこの条件に一致しないため、フローが正しく分岐しません",
                    fix_category="prompter",
                ))

        # PROMPT-002: prompt出力仕様にあるがnextに対応しないラベル
        # ただしワイルドカード (^.*$ / ^.+$) がある場合は全 output_value が
        # default 経路で処理されるため、個別ラベルのチェックはスキップする
        # （例: 診療科 OpenAI で 48 科列挙 + ^.*$ default 分岐のケース）
        if not has_wildcard:
            for label in prompt_labels:
                if label not in next_labels:
                    result.issues.append(Issue("WARNING", "PROMPT-002", mod_name,
                        f"params.prompt出力仕様",
                        f"prompt出力仕様の '{label}' に対応するnext分岐条件がありません — "
                        "OpenAIがこの値を返してもルーティングされません"))


# ============================================================
# 到達可能性チェック
# ============================================================

def validate_reachability(data: dict, result: ValidationResult):
    """startモジュールからの到達可能性チェック"""
    if "modules" not in data or "start" not in data:
        return

    modules = data["modules"]
    start = data.get("start", "")
    if start not in modules:
        return

    # BFS で到達可能なモジュールを収集
    reachable = set()
    queue = [start]
    while queue:
        current = queue.pop(0)
        if current in reachable:
            continue
        reachable.add(current)
        mod = modules.get(current, {})

        # next 遷移先
        for nxt in mod.get("next", []):
            target = nxt.get("nextModuleName", "")
            if target and target in modules and target not in reachable:
                queue.append(target)

        # subs 遷移先
        for sub in mod.get("subs", []):
            target = sub.get("moduleName", "")
            if target and target in modules and target not in reachable:
                queue.append(target)

    # REACH-001: startから到達不能なモジュール（save2dbはsubs経由のため除外済み）
    all_modules = set(modules.keys())
    unreachable = all_modules - reachable
    for mod_name in unreachable:
        # save2db はsubs専用なので到達不能でも問題ない場合がある
        # ただしsubs経由で参照されていないsave2dbはT-002で検出済み
        if not is_save2db(modules[mod_name].get("type", "")):
            result.issues.append(Issue("CRITICAL", "REACH-001", mod_name,
                "(module)",
                "startモジュールから到達不能です — "
                "このモジュールへの遷移パスが存在しません"))

    # REACH-002: Disconnect モジュールへの到達パスが存在するか
    has_disconnect = False
    for mod_name in reachable:
        mod_type = modules[mod_name].get("type", "")
        if "Disconnect" in mod_type:
            has_disconnect = True
            break
    if not has_disconnect:
        result.issues.append(Issue("WARNING", "REACH-002", "(flow)", "Disconnect",
            "startから到達可能なDisconnectモジュールが存在しません — "
            "通話終了パスが未定義の可能性があります"))

    # REACH-003: Retry Counter を経由しないループ検出
    # DFS でサイクルを検出し、サイクル内にRetry Counterがあるか確認
    # 隣接リスト構築（next遷移のみ、subs除外）
    # 復唱 (echo_back) チェーンは scaffold が生成する正規構造で、内部に
    # 'リトライ_{step}_復唱' が Retry Counter として存在する。このパターンを
    # 正しく認識するため、サブモジュール検索も含めた拡張が必要
    adj = {}
    for mod_name, mod in modules.items():
        adj[mod_name] = []
        for nxt in mod.get("next", []):
            target = nxt.get("nextModuleName", "")
            if target and target in modules:
                adj[mod_name].append(target)

    # DFS ベースのサイクル検出
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {m: WHITE for m in modules}
    parent = {m: None for m in modules}
    reported_cycles = set()

    def dfs_cycle(node, path):
        color[node] = GRAY
        path.append(node)
        for neighbor in adj.get(node, []):
            if color[neighbor] == GRAY and neighbor in path:
                # サイクル検出: path 内で neighbor の位置から現在地まで
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:]
                # サイクル内に Retry Counter または Re-confirmation が含まれるか確認
                # Re-confirmation node data / DOB Re-confirmation が含まれる場合は
                # ユーザー主導の「否定→再入力」意図的ループなので正常扱い
                # （無限ループ懸念なし、ユーザー切断で抜ける）
                has_retry = any(is_retry(modules[m].get("type", "")) for m in cycle)
                has_reconfirmation = any(
                    "Re-confirmation node data" in modules[m].get("type", "")
                    or "DOB Re-confirmation" in modules[m].get("type", "")
                    for m in cycle
                )
                if not has_retry and not has_reconfirmation:
                    cycle_key = frozenset(cycle)
                    if cycle_key not in reported_cycles:
                        reported_cycles.add(cycle_key)
                        cycle_display = " → ".join(cycle[:5])
                        if len(cycle) > 5:
                            cycle_display += f" ...（計{len(cycle)}モジュール）"
                        result.issues.append(Issue("WARNING", "REACH-003",
                            cycle[0], "next",
                            f"Retry Counterを経由しないループが検出されました: {cycle_display}"))
            elif color[neighbor] == WHITE:
                dfs_cycle(neighbor, path)
        path.pop()
        color[node] = BLACK

    for mod_name in modules:
        if color[mod_name] == WHITE and mod_name in reachable:
            dfs_cycle(mod_name, [])


# ============================================================
# SAVECTX 重複・禁止パターンチェック
# ============================================================

def validate_savectx(data: dict, result: ValidationResult):
    """saveContext2DB の重複保存・禁止パターン検出"""
    if "modules" not in data:
        return

    # contextName の重複検出用
    ctx_names_seen = {}

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "saveContext2DB" not in mod_type:
            continue

        params = mod.get("params", {})
        if not isinstance(params, dict):
            continue

        ctx_name = params.get("contextName", "")
        ctx_value = params.get("contextValue", "")

        # SAVECTX-001: contextValue に禁止パターン（#data# は CTX-013 で既存）
        # 追加: ${} パターンのうちシステム変数以外
        if ctx_value:
            allowed_sys_vars = ["<% sys-customer-phone-number %>"]
            if "${" in ctx_value and ctx_value not in allowed_sys_vars:
                result.issues.append(Issue("CRITICAL", "SAVECTX-001", mod_name,
                    "params.contextValue",
                    f"contextValue に未認識の変数パターンが含まれています: '{ctx_value}' — "
                    "使用可能なのは固定文字列またはシステム変数のみです"))

        # SAVECTX-002: contextName の重複保存検出
        # ただし "saveDefault-" プレフィックスは scaffold が no_result_default 機能で
        # 意図的に複数ルートに配置する固定値保存用モジュール。重複は正常なのでスキップ。
        if ctx_name and not mod_name.startswith("saveDefault-"):
            if ctx_name in ctx_names_seen:
                result.issues.append(Issue("WARNING", "SAVECTX-002", mod_name,
                    "params.contextName",
                    f"contextName '{ctx_name}' が複数の saveContext2DB で保存されています — "
                    f"既出: {ctx_names_seen[ctx_name]}"))
            else:
                ctx_names_seen[ctx_name] = mod_name

    # SAVECTX-003: OpenAI分岐直後のsaveContext2DB（冗長パターン）
    # generate_by_OpenAI の next 先が saveContext2DB の場合は不要
    # ただし saveDefault-* は no_result_default の固定値保存（診療科「登録なし」等）なので除外
    error_labels = {"timeout", "error", "no_result"}
    for mod_name, mod in data["modules"].items():
        if "generate_by_OpenAI" not in mod.get("type", ""):
            continue
        for nx in mod.get("next", []):
            if nx.get("label", "").lower() in error_labels:
                continue
            next_name = nx.get("nextModuleName", "")
            if not next_name or next_name not in data["modules"]:
                continue
            # saveDefault-* は意図的な固定値保存なのでスキップ
            if next_name.startswith("saveDefault-"):
                continue
            next_mod = data["modules"][next_name]
            if "saveContext2DB" in next_mod.get("type", ""):
                result.issues.append(Issue("WARNING", "SAVECTX-003", mod_name,
                    f"next[{nx.get('label')}] → {next_name}",
                    f"generate_by_OpenAI の分岐直後に saveContext2DB が配置されています — "
                    f"OpenAIルーティング済みのパスで固定値を再保存するのは冗長です。"
                    f"削除して直接次のモジュールに接続してください"))


def validate_completion_flag_order(data: dict, result: ValidationResult):
    """saveCompletionFlag2db が終話TTS の直前に配置されているかチェック"""
    if "modules" not in data:
        return

    modules = data["modules"]

    for mod_name, mod in modules.items():
        mod_type = mod.get("type", "")
        if "saveCompletionFlag2db" not in mod_type:
            continue

        # next 先を確認
        nexts = mod.get("next", [])
        if not nexts:
            result.issues.append(Issue("WARNING", "COMP-002", mod_name,
                "next",
                "saveCompletionFlag2db の next が空です — 終話TTS に接続してください"))
            continue

        next_mod_name = nexts[0].get("nextModuleName", "")
        if not next_mod_name or next_mod_name not in modules:
            continue

        next_mod = modules[next_mod_name]
        next_type = next_mod.get("type", "")

        # next 先が TTS であることを確認
        if "Text to speech" not in next_type and "Text To Speech" not in next_type:
            # Disconnect に直接繋がっている場合（TTS なし）
            if "Disconnect" in next_type or "Reject" in next_type:
                # 時間外は acceptance_times モジュール内で TTS を再生する設計のため、
                # 終話チェーンに TTS が無いのは意図通り（scaffold_generator.py の
                # is_jikangai 分岐と同期）。誤検出を避けるため対象外とする。
                if "時間外" in mod_name or "時間外" in next_mod_name:
                    continue
                result.issues.append(Issue("WARNING", "COMP-003", mod_name,
                    "next",
                    f"saveCompletionFlag2db が Disconnect/Reject に直接接続されています — "
                    f"終話ガイダンス（TTS）を間に配置してください: "
                    f"saveCompletionFlag2db → TTS → {next_mod_name}"))


# ============================================================
# Properties 整合性チェック
# ============================================================

def find_properties_file(json_path: str) -> str:
    """フローJSONに対応するpropertiesファイルを探す（glob検索）

    検索順: target_key 一致 (施設_flow) → 同ディレクトリ → 親ディレクトリ →
             output/scenarios/* 全体 → output/（後方互換）

    - 絶対パスでも動くように output/ ディレクトリを上向き探索で発見する
      （旧実装は os.path.dirname を 2 段かけて worktree root を返してしまい、
        そこに "scenarios" サブディレクトリが無いため glob が空になる事故あり）
    - json basename から target_key (施設_flow) を抽出し、key を含む
      properties_*.md を最優先（worktree に他施設の properties が混在する
      ケースで先頭 hit 暴走を防ぐ）
    """
    import glob as _glob
    import re as _re

    abs_json = os.path.abspath(json_path)
    dir_path = os.path.dirname(abs_json)

    # output/ ディレクトリを発見（dir_path から上向き探索）
    output_dir = None
    p = dir_path
    while p and p != os.path.dirname(p):
        if os.path.basename(p) == "output":
            output_dir = p
            break
        p = os.path.dirname(p)
    scenarios_root = os.path.join(output_dir, "scenarios") if output_dir else ""

    # 施設_flow key 抽出（prompted_/merged_/reviewed_/draft_ プレフィックス対応）
    basename = os.path.basename(abs_json)
    m = _re.match(r"(?:prompted|merged|reviewed|draft)_(.+)\.json$", basename)
    target_key = m.group(1) if m else None

    search_dirs = [dir_path, os.path.dirname(dir_path)]
    if scenarios_root and os.path.isdir(scenarios_root):
        for sub in sorted(os.listdir(scenarios_root)):
            full = os.path.join(scenarios_root, sub)
            if os.path.isdir(full):
                search_dirs.append(full)
    if output_dir:
        search_dirs.append(output_dir)

    def _select(matches: list[str]) -> str:
        demo = [x for x in matches if "_demo" in os.path.basename(x)]
        return demo[0] if demo else matches[0]

    # Pass 1: target_key を含む properties を最優先
    if target_key:
        for search_dir in search_dirs:
            if not search_dir or not os.path.isdir(search_dir):
                continue
            matches = _glob.glob(os.path.join(search_dir, "properties_*.md"))
            keyed = [x for x in matches if target_key in os.path.basename(x)]
            if keyed:
                return _select(keyed)

    # Pass 2: 通常の検索順で先頭 hit (target_key 抽出失敗 or 一致無し)
    for search_dir in search_dirs:
        if not search_dir or not os.path.isdir(search_dir):
            continue
        matches = _glob.glob(os.path.join(search_dir, "properties_*.md"))
        if matches:
            return _select(matches)

    return ""


def validate_save2db_group_consistency(data: dict, result: ValidationResult):
    """SB-003 (#253): hearing/確認ブロックグループの save2db 共有整合チェック。"""
    if "modules" not in data:
        return
    mods = data["modules"]

    def _save_sub(m: dict):
        for s in m.get("subs", []) or []:
            if isinstance(s, dict) and s.get("label", "").startswith("save-") and s.get("moduleName"):
                return s["moduleName"]
        return None

    groups: dict[str, dict[str, tuple]] = {}
    for nm, m in mods.items():
        if not isinstance(m, dict):
            continue
        if nm.startswith("入力_"):
            groups.setdefault(nm[len("入力_"):], {})["入力"] = (nm, _save_sub(m))
        elif nm.startswith("リトライ_"):
            groups.setdefault(nm[len("リトライ_"):], {})["リトライ"] = (nm, _save_sub(m))
    for base, roles in groups.items():
        if base in mods and isinstance(mods[base], dict):
            roles["TTS"] = (base, _save_sub(mods[base]))

    for base, roles in groups.items():
        present = [(role, nm, sv) for role, (nm, sv) in roles.items()]
        saves = [sv for _, _, sv in present if sv]
        if not saves:
            continue
        expected = max(saves, key=saves.count)
        for role, nm, sv in present:
            if sv != expected:
                detail = "subs が空" if not sv else f"save2db='{sv}' が不一致"
                result.issues.append(Issue("CRITICAL", "SB-003", nm, "subs",
                    f"確認グループ '{base}' の save2db 共有が崩れています（{role}: {detail}・期待値 '{expected}'）。"
                    f"TTS/入力/リトライの 3 ノードは同一 save2db を共有してください（#253）。",
                    fix_category="human"))


DATE_OF_CALL_TYPE = "drjoy^Incoming$DateOfCall Classifier"
DATE_OF_CALL_REQUIRED_OUTPUTS = ("時間後", "時間一致", "時間前")
DATE_OF_CALL_ERROR_OUTPUT = "ERROR"
_DATE_OF_CALL_ALL_OUTPUTS = DATE_OF_CALL_REQUIRED_OUTPUTS + (DATE_OF_CALL_ERROR_OUTPUT,)


def validate_date_of_call_coverage(data: dict, result: ValidationResult):
    """DOC-001: DateOfCall Classifier の出力値カバレッジ検証（#326）。"""
    if "modules" not in data:
        return
    modules = data["modules"]
    for mod_name, mod in modules.items():
        if not isinstance(mod, dict) or mod.get("type") != DATE_OF_CALL_TYPE:
            continue
        conditions = [
            (slot.get("condition") or "").strip()
            for slot in (mod.get("next") or [])
            if isinstance(slot, dict) and (slot.get("condition") or "").strip()
        ]

        def _matches(cond, value):
            try:
                return re.match(cond, value) is not None
            except re.error:
                return False

        stray = [c for c in conditions if not any(_matches(c, v) for v in _DATE_OF_CALL_ALL_OUTPUTS)]
        for cond in stray:
            result.issues.append(Issue(
                severity="CRITICAL", code="DOC-001", module=mod_name, field="next.condition",
                message=f"DateOfCall condition '{cond}' はモジュール出力値ではありません。決してマッチせず通話が強制終了します。",
                fix_category="fixer"))

        missing = [v for v in DATE_OF_CALL_REQUIRED_OUTPUTS if not any(_matches(c, v) for c in conditions)]
        if missing:
            result.issues.append(Issue(
                severity="CRITICAL", code="DOC-001", module=mod_name, field="next.condition",
                message=f"DateOfCall 出力値 {missing} にマッチする next 条件がありません。その時間区分の入電で通話が強制終了します。",
                fix_category="fixer"))

        if not any(_matches(c, DATE_OF_CALL_ERROR_OUTPUT) for c in conditions):
            result.issues.append(Issue(
                severity="WARNING", code="DOC-001", module=mod_name, field="next.condition",
                message="DateOfCall に ERROR 出力をカバーする next 条件がありません（^ERROR$ 推奨）。",
                fix_category="fixer"))


def validate_properties(data: dict, properties_path: str, result: ValidationResult):
    """フローJSONとpropertiesファイルの整合性チェック"""
    if not properties_path:
        result.issues.append(Issue("CRITICAL", "P-000", "(properties)", "file",
            "対応するpropertiesファイルが見つかりません（TTSが発話できない状態です）"))
        return

    try:
        with open(properties_path, "r", encoding="utf-8") as f:
            prop_content = f.read()
    except Exception as e:
        result.issues.append(Issue("WARNING", "P-001", "(properties)", "file",
            f"propertiesファイルの読み込みに失敗: {e}"))
        return

    if "modules" not in data:
        return

    # プロパティ行をパース（```ブロック内の key=value 行を抽出）
    prop_keys = set()
    prop_values = {}  # key → value（P-013/P-014チェック用）
    in_code_block = False
    todo_lines = []
    for line in prop_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block and "=" in stripped and not stripped.startswith("#"):
            key, _, val = stripped.partition("=")
            key = key.strip()
            prop_keys.add(key)
            prop_values[key] = val.strip()
            if "TODO_" in stripped:
                todo_lines.append(stripped)

    # JSON内の TTS/Retry/STT モジュール名を収集
    tts_modules = set()
    retry_modules = set()
    wait_modules = set()
    transfer_modules = set()
    stt_modules_nonDTMF = set()
    stt_modules_DTMF = set()

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if is_tts(mod_type):
            tts_modules.add(mod_name)
        if is_retry(mod_type):
            retry_modules.add(mod_name)
        if is_stt(mod_type):
            if "DTMF" in mod_type:
                stt_modules_DTMF.add(mod_name)
            else:
                stt_modules_nonDTMF.add(mod_name)
        params = mod.get("params", {})
        if isinstance(params, dict) and params.get("wait", ""):
            wait_modules.add(mod_name)
        if "Transfer" in mod_type:
            transfer_modules.add(mod_name)

    # チェック1: TTS モジュール → properties に .prompt= があるか
    for mod_name in tts_modules:
        # Re-confirmation node data は params.prompt に `{tts_g: #data#...}` がインラインで入る仕様。
        # properties ファイルには .prompt= 行を書かないため P-010 チェックの対象外。
        mod_type = data["modules"][mod_name].get("type", "")
        if "Re-confirmation node data" in mod_type:
            continue
        prompt_key = f"{mod_name}.prompt"
        if prompt_key not in prop_keys:
            result.issues.append(Issue("CRITICAL", "P-010", mod_name, "properties",
                f"TTSモジュール '{mod_name}' に対応するプロパティ行 '{prompt_key}=' がありません — "
                "このまま本番適用するとTTS発話が全て無音になります"))

    # チェック1b: AmiVoice STTモジュール（非DTMF）に .prompt= が設定されていないか
    # AmiVoice STTは発話機能を持たないためIVRプロパティのpromptは設定不可
    for mod_name in stt_modules_nonDTMF:
        prompt_key = f"{mod_name}.prompt"
        if prompt_key in prop_keys:
            result.issues.append(Issue("CRITICAL", "P-013", mod_name, "properties",
                f"AmiVoice STTモジュール '{mod_name}' に '{prompt_key}=' が設定されています — "
                "STTモジュールには発話プロパティを設定しないでください。"
                "発話はSTTの直前のTTSモジュールで行います"))

    # チェック1c: DTMF STTモジュールの .prompt= に {recstart} が含まれるか
    for mod_name in stt_modules_DTMF:
        prompt_key = f"{mod_name}.prompt"
        if prompt_key in prop_keys:
            val = prop_values.get(prompt_key, "")
            if "{recstart}" not in val:
                result.issues.append(Issue("CRITICAL", "P-014", mod_name, "properties",
                    f"DTMF STTモジュール '{mod_name}' のプロパティ '{prompt_key}' に "
                    "{recstart} が含まれていません — "
                    "DTMF STTのpromptには必ず{recstart}を含める必要があります"))

    # チェック2: Retry モジュール → フローJSON内の params に prompt_true/prompt_false があるか
    # ※ IVRプロパティではなく、フローJSON内のparamsに記述する必要がある
    # Retry 空 prompt の自動補完テンプレート（デフォルト: tts_g 小文字）
    RETRY_DEFAULT_PROMPTS = {
        "prompt_true":  "{tts_g: すみません、もう一度お伺いします。}",
        "prompt_false": "{tts_g: ご回答の確認ができませんでしたので、改めておかけ直しください。お電話ありがとうございました。}",
    }
    for mod_name in retry_modules:
        mod = data["modules"].get(mod_name, {})
        params = mod.get("params", {})
        if isinstance(params, dict):
            for suffix in ["prompt_true", "prompt_false"]:
                val = params.get(suffix, "")
                if not val:
                    result.issues.append(Issue(
                        severity="WARNING", code="P-011", module=mod_name,
                        field=f"params.{suffix}",
                        message=f"Retryモジュール '{mod_name}' の params.{suffix} が空です — "
                                "リトライ発話文言はフローJSON内のparamsに直接記述する必要があります"
                                "（IVRプロパティでは動作しません）",
                        fix_category="auto",
                        fix_action={"op": "set",
                                    "path": ["modules", mod_name, "params", suffix],
                                    "value": RETRY_DEFAULT_PROMPTS[suffix]},
                    ))

    # チェック2b: IVRプロパティにRetry prompt行が含まれていないか（含まれていたら警告）
    for key in prop_keys:
        if ".prompt_true" in key or ".prompt_false" in key:
            result.issues.append(Issue("WARNING", "P-012", key.split(".")[0], "properties",
                f"IVRプロパティに '{key}=' が含まれています — "
                "Retry Counter の prompt_true/prompt_false はIVRプロパティでは動作しません。"
                "フローJSON内の params に直接記述してください"))

    # チェック3: properties にあるがJSON に存在しないモジュール名
    all_module_names = set(data["modules"].keys())
    # サブフローJSONからもモジュール名を収集（Jump to Flow経由で参照されるサブフロー）
    import glob as _glob
    json_dir = os.path.dirname(os.path.abspath(result.file_path)) if result.file_path else "."
    for mod in data["modules"].values():
        if "Jump to Flow" in mod.get("type", ""):
            # 同ディレクトリの同施設サブフローJSONを探す
            # 検索プレフィックスを2種類用意: ①フロー名由来 ②ファイル名由来（文字コード相違・略称対応）
            search_prefixes: list[str] = []

            # ①フロー名から施設プレフィックスを抽出（グループ名$フロー名形式）
            flow_name = data.get("name", "")
            fp_from_flow = flow_name.split("$")[0].split("_", 1)[-1] if "$" in flow_name else ""
            if fp_from_flow:
                search_prefixes.append(fp_from_flow)

            # ②ファイル名から施設プレフィックスを抽出（prompted_/draft_/reviewed_ を除去）
            if result.file_path:
                stem = os.path.splitext(os.path.basename(result.file_path))[0]
                for pfx in ("prompted_", "draft_", "reviewed_", "merged_"):
                    if stem.startswith(pfx):
                        stem = stem[len(pfx):]
                        break
                # stem = "施設名_フロー名" → 施設名部分
                fp_from_file = stem.rsplit("_", 1)[0] if "_" in stem else stem
                if fp_from_file and fp_from_file not in search_prefixes:
                    search_prefixes.append(fp_from_file)

            collected: set[str] = set()
            for prefix in search_prefixes:
                for sf_path in _glob.glob(os.path.join(json_dir, f"*{prefix}*.json")):
                    if sf_path in collected:
                        continue
                    collected.add(sf_path)
                    try:
                        with open(sf_path, "r", encoding="utf-8") as sf_f:
                            sf_data = json.load(sf_f)
                        if "modules" in sf_data:
                            all_module_names.update(sf_data["modules"].keys())
                    except Exception:
                        pass
            break  # 一度収集すれば十分
    for key in prop_keys:
        if "." in key:
            mod_part = key.split(".")[0]
            # office_id, amivoice, pbx, context, acceptance_times, openAI_generate, rag_ssml, speech 等はスキップ
            skip_prefixes = ["office_id", "amivoice", "pbx", "context", "acceptance_times",
                             "openAI_generate", "rag_ssml", "speech"]
            if any(mod_part.startswith(p) or mod_part == p for p in skip_prefixes):
                continue
            if mod_part not in all_module_names:
                result.issues.append(Issue("CRITICAL", "P-020", mod_part, "properties",
                    f"プロパティキー '{key}' のモジュール '{mod_part}' がフローJSON内に存在しません（名前不一致の可能性）"))

    # チェック3b: STTモジュールの個別URI設定が含まれていないか
    # AmiVoice URIはグローバル設定（amivoice.uri=）で管理するため、
    # 入力_xxx.uri= のような個別URI設定はプロパティに記述しない
    for mod_name in (stt_modules_nonDTMF | stt_modules_DTMF):
        uri_key = f"{mod_name}.uri"
        if uri_key in prop_keys:
            result.issues.append(Issue("WARNING", "P-015", mod_name, "properties",
                f"STTモジュール '{mod_name}' に '{uri_key}=' が設定されています — "
                "AmiVoice URIはグローバル設定 'amivoice.uri=' で一括管理します。"
                "個別の .uri= 行は不要なため削除してください"))

    # チェック3c: Custom Jump to Flow のサブフロータイプ別 必須TTSプロパティエントリチェック (P-016)
    # テンプレートJSON（docs/specs/subflow_property_templates.json）を読み込み、
    # メインフロー内のCustom Jump to Flowのflownameからサブフロータイプを判定して
    # 必須TTSプロパティエントリがpropertiesに存在するか確認する
    _tmpl_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs", "specs", "subflow_property_templates.json"
    )
    if os.path.exists(_tmpl_path):
        try:
            with open(_tmpl_path, "r", encoding="utf-8") as _f:
                _tmpl_data = json.load(_f)
            _subflow_templates = _tmpl_data.get("subflows", [])
        except Exception:
            _subflow_templates = []

        for mod_name, mod in data["modules"].items():
            if "Custom Jump to Flow" not in mod.get("type", ""):
                continue
            flowname = mod.get("params", {}).get("flowname", "")
            # "drjoy^施設名$サブフロー名_YYYYMMDD" → "$"以降 → "サブフロー名_YYYYMMDD"
            if "$" not in flowname:
                continue
            subflow_part = flowname.split("$", 1)[1]
            for tmpl in _subflow_templates:
                keyword = tmpl.get("match_keyword", "")
                if keyword and keyword in subflow_part:
                    for tts_mod in tmpl.get("required_tts", []):
                        prompt_key = f"{tts_mod}.prompt"
                        if prompt_key not in prop_keys:
                            result.issues.append(Issue("CRITICAL", "P-016", mod_name, "properties",
                                f"サブフロー '{subflow_part}'（タイプ: {tmpl['type']}）に対応する "
                                f"必須TTSプロパティ '{prompt_key}=' がありません"))
                    break  # 1つのflownameに対してテンプレートは1つだけ照合

    # チェック4: TODO_ 残存チェック
    for line in todo_lines:
        result.issues.append(Issue("WARNING", "P-030", "(properties)", "TODO",
            f"propertiesに TODO_ が残っています: {line[:80]}"))


# ============================================================
# メイン実行
# ============================================================

def validate_flow(file_path: str, check_properties: bool = True, check_prompts: bool = True, properties_override: str = None) -> ValidationResult:
    result = ValidationResult(file_path=file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.issues.append(Issue("CRITICAL", "J-001", "(file)", "JSON",
            f"JSONパースエラー: {e}"))
        return result
    except FileNotFoundError:
        result.issues.append(Issue("CRITICAL", "J-002", "(file)", "path",
            f"ファイルが見つかりません: {file_path}"))
        return result

    validate_top_level(data, result)
    validate_transitions(data, result)
    validate_stt_modules(data, result)
    validate_tts_modules(data, result)
    validate_openai_modules(data, result)
    validate_retry_modules(data, result)
    validate_save2db(data, result)
    validate_save2db_group_consistency(data, result)  # SB-003 (#253)
    validate_phone_subflow(data, result)
    validate_script_modules(data, result)
    validate_subflow_termination(data, result, data.get("termination", ""))
    validate_naming(data, result)
    validate_layout(data, result)
    validate_cmr_modules(data, result)
    validate_cmr_default_token(data, result)
    validate_cmr_other_branch(data, result)
    validate_cmr_reference_vocab(data, result)  # CMR-008 (#303): 待受値 vs 参照元 emitter 語彙
    validate_openai_consumer_consistency(data, result)
    validate_node_reference(data, result)  # NODE-001 (#358): params.nodeName の broken_ref
    validate_date_of_call_coverage(data, result)  # DOC-001 (#326)
    validate_subflow_references(data, result)
    validate_dtmf_modules(data, result)
    validate_stt_predecessors(data, result)
    validate_flow_structure(data, result)
    if check_prompts:
        validate_prompt_labels(data, result)
    validate_reachability(data, result)
    validate_savectx(data, result)
    validate_completion_flag_order(data, result)

    # Properties 整合性チェック
    if check_properties:
        prop_path = properties_override or find_properties_file(file_path)
        if prop_path:
            validate_properties(data, prop_path, result)
            print(f"  [Properties] チェック対象: {prop_path}")
        else:
            result.issues.append(Issue("CRITICAL", "P-000", "(properties)", "file",
                "対応するpropertiesファイルが見つかりません — TTSが発話できない状態です（--no-props で無視可）"))

    # ルールコードに基づいて fix_category を最終決定
    finalize_categories(result)

    return result


def print_report(result: ValidationResult):
    print(f"\n{'='*60}")
    print(f"[REPORT] バリデーション結果: {result.flow_name or result.file_path}")
    print(f"{'='*60}")
    print(f"モジュール数: {result.module_count}")
    print(f"検出問題数: {len(result.issues)}")
    print(f"  [Critical]: {result.critical_count}")
    print(f"  [Warning]:  {result.warning_count}")
    print(f"  [Info]:     {result.info_count}")
    print(f"判定: {'[PASS]' if result.is_valid else '[FAIL]'}")

    # fix_category 別のカウント
    cat_counts: dict[str, int] = {}
    for issue in result.issues:
        cat_counts[issue.fix_category] = cat_counts.get(issue.fix_category, 0) + 1
    if cat_counts:
        print("修正の振り分け:")
        for cat in ("auto", "prompter", "properties", "fixer", "human"):
            if cat in cat_counts:
                print(f"  [{cat}]: {cat_counts[cat]}")
    print()

    if result.issues:
        print("--- 検出事項 ---")
        for issue in sorted(result.issues,
                            key=lambda x: {"CRITICAL": 0, "WARNING": 1, "INFO": 2}[x.severity]):
            print(f"  {issue}  <{issue.fix_category}>")
        print()


def write_json_report(result: ValidationResult, json_path: str) -> None:
    """auto_fixer.py が機械的に読める JSON 形式で結果を出力"""
    data = {
        "file_path":     result.file_path,
        "flow_name":     result.flow_name,
        "module_count":  result.module_count,
        "critical":      result.critical_count,
        "warning":       result.warning_count,
        "info":          result.info_count,
        "is_valid":      result.is_valid,
        "issues":        [i.to_dict() for i in result.issues],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage: python schemas/validator.py <flow.json> [--no-props] [--no-prompts] [--properties <file>] [--json-report <path>] [--yaml <spec.yaml>]")
        print("       python schemas/validator.py output/*.json")
        print("  --no-props              propertiesファイルとの整合性チェックをスキップ")
        print("  --no-prompts            promptラベル整合性チェックをスキップ（generator直後など、prompter未実行時に使用）")
        print("  --properties <file>     propertiesファイルを明示的に指定")
        print("  --json-report <path>    auto_fixer.py が読む JSON 形式レポートを出力")
        print("  --yaml <spec.yaml>      設計書YAMLパス（指定時: Issueにblock_nameを付与してJSONレポートに含める）")
        sys.exit(1)

    check_properties = "--no-props" not in sys.argv
    check_prompts = "--no-prompts" not in sys.argv

    # --properties / --json-report / --yaml オプションのパース
    properties_override = None
    json_report_path = None
    yaml_spec_path = None
    skip_next = None  # None | "properties" | "json-report" | "yaml"
    files = []
    for arg in sys.argv[1:]:
        if skip_next == "properties":
            properties_override = arg
            skip_next = None
            continue
        if skip_next == "json-report":
            json_report_path = arg
            skip_next = None
            continue
        if skip_next == "yaml":
            yaml_spec_path = arg
            skip_next = None
            continue
        if arg == "--properties":
            skip_next = "properties"
            continue
        if arg == "--json-report":
            skip_next = "json-report"
            continue
        if arg == "--yaml":
            skip_next = "yaml"
            continue
        if not arg.startswith("--"):
            files.append(arg)

    all_pass = True

    for file_path in files:
        if not os.path.exists(file_path):
            print(f"[WARN] ファイルが見つかりません: {file_path}")
            continue
        result = validate_flow(file_path, check_properties=check_properties,
                               check_prompts=check_prompts,
                               properties_override=properties_override)

        # --yaml が指定されていれば block_mapper で block_name を付与
        if yaml_spec_path and os.path.exists(yaml_spec_path):
            try:
                _validator_dir = os.path.dirname(os.path.abspath(__file__))
                _scripts_dir = os.path.join(os.path.dirname(_validator_dir), "scripts")
                if _scripts_dir not in sys.path:
                    sys.path.insert(0, _scripts_dir)
                from block_mapper import build_module_to_block_map
                _mod_to_block = build_module_to_block_map(yaml_spec_path)
                for _issue in result.issues:
                    if not _issue.block_name:
                        _issue.block_name = _mod_to_block.get(_issue.module, "")
            except Exception as _e:
                print(f"[WARN] block_mapper でのblock_name付与に失敗: {_e}")

        print_report(result)
        if json_report_path:
            write_json_report(result, json_report_path)
            print(f"[REPORT] JSON レポート出力: {json_report_path}")
        if not result.is_valid:
            all_pass = False

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
