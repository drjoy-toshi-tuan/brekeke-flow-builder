#!/usr/bin/env python3
"""
validator.py — bivr-checker フローJSON バリデーター

フローJSONがBrekeke IVR仕様に適合しているかを自動検証する。
VoiceBot Flow Builder の validator.py をベースに、Property.md バリデーション
およびクロスバリデーション機能を追加。

Usage:
    python scripts/validator.py output/flows/*.json
    python scripts/validator.py output/flows/*.json --properties output/properties/xxx_Property.md
    python scripts/validator.py output/flows/*.json --subflows output/flows/sub_*.json
    python scripts/validator.py output/flows/*.json --json
    python scripts/validator.py output/flows/*.json --no-props --no-prompts
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

    @property
    def icon(self) -> str:
        return {"CRITICAL": "[C]", "WARNING": "[W]", "INFO": "[I]"}[self.severity]

    def __str__(self) -> str:
        return f"{self.icon} [{self.code}] {self.module} > {self.field}: {self.message}"

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "code": self.code,
            "module": self.module,
            "field": self.field,
            "message": self.message
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

    def to_dict(self) -> dict:
        return {
            "file": self.file_path,
            "flow_name": self.flow_name,
            "module_count": self.module_count,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "info_count": self.info_count,
            "is_valid": self.is_valid,
            "issues": [i.to_dict() for i in self.issues]
        }


# ============================================================
# ヘルパー
# ============================================================

def is_stt(mod_type: str) -> bool:
    return any(kw in mod_type for kw in ["AmiVoice", "DTMF AmiVoice", "Speech to Text"])

def is_tts(mod_type: str) -> bool:
    return "Text To Speech$Text to speech" in mod_type

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
            result.issues.append(Issue("CRITICAL", "S-002", "(root)", "name",
                f"フロー名が 'グループ名$フロー名' 形式ではありません: '{data['name']}' — "
                "Brekekeでフロー識別ができません。入力フォルダ名などから正しいグループ名を補完してください"))

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
        for i, nxt in enumerate(mod.get("next", [])):
            label = nxt.get("label", "")
            if label:
                labels.append(label)
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
        reserved = {"^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", "^.*$", ""}
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

        # next label チェック
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
        if isinstance(params, dict):
            prompt = params.get("prompt", "")
            if prompt and "{tts_g:" not in prompt and prompt != "{recstart}":
                result.issues.append(Issue("INFO", "TTS-003", mod_name, "params.prompt",
                    "promptが {tts_g: ...} 形式ではありません（IVRプロパティで管理する場合は無視可）"))


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

    # R-006/R-007: リトライパターン整合性チェック（フロー単位）
    _validate_retry_patterns(data, result)


def _classify_retry_pattern(mod: dict, modules: dict) -> str:
    """Retry Counterのパターン判定: A(次へ進む)/B(失敗終話)/C(無限ループ)"""
    next_list = mod.get("next", [])
    params = mod.get("params", {}) if isinstance(mod.get("params"), dict) else {}
    true_target = ""
    false_target = ""
    for n in next_list:
        if n.get("condition") == "true":
            true_target = n.get("nextModuleName", "")
        elif n.get("condition") == "false":
            false_target = n.get("nextModuleName", "")
    prompt_false = params.get("prompt_false", "")
    # パターンC: prompt_false空 かつ false==true (ループ)
    if prompt_false == "" and false_target == true_target:
        return "C"
    # パターンB: false遷移先が終話系
    false_mod = modules.get(false_target, {})
    false_mod_type = false_mod.get("type", "")
    if ("失敗" in false_target or "聴取失敗" in false_target or
            "@IVR$Disconnect" in false_mod_type):
        return "B"
    return "A"


def _validate_retry_patterns(data: dict, result: ValidationResult):
    """R-006: 全Retry同一パターン警告 / R-007: 用件/区分のPattern C未適用警告"""
    if "modules" not in data:
        return
    modules = data["modules"]
    retry_patterns = {}
    for mod_name, mod in modules.items():
        if not is_retry(mod.get("type", "")):
            continue
        retry_patterns[mod_name] = _classify_retry_pattern(mod, modules)
    if not retry_patterns:
        return
    # R-006: 全リトライが同一パターン (2件以上)
    unique = set(retry_patterns.values())
    if len(retry_patterns) >= 2 and len(unique) == 1:
        only = next(iter(unique))
        result.issues.append(Issue(
            "WARNING", "R-006", "(flow)", "retry_pattern",
            f"全 {len(retry_patterns)} 件のリトライが全てパターン{only} — "
            f"VFBデフォルトのままカスタマイズされていない可能性があります"))
    # R-007: 用件/区分がパターンC以外
    for mod_name, pattern in retry_patterns.items():
        if ("用件" in mod_name or "区分" in mod_name) and pattern != "C":
            result.issues.append(Issue(
                "WARNING", "R-007", mod_name, "retry_pattern",
                f"用件/区分の必須聴取はパターンC（無限ループ）推奨ですがパターン{pattern}です"))


def validate_save2db(data: dict, result: ValidationResult):
    """save2dbのサブモジュール接続チェック"""
    if "modules" not in data:
        return

    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")

        # TTS/STT に save2db サブモジュールが必要
        if is_tts(mod_type) or is_stt(mod_type):
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
                    result.issues.append(Issue("CRITICAL", "CTX-012", mod_name,
                        "params.status",
                        "saveCompletionFlag2db の status が空です"))
                elif status in ("0", "5"):
                    result.issues.append(Issue("CRITICAL", "COMP-001", mod_name,
                        "params.status",
                        f"status=\"{status}\" は第2世代予約値のため使用禁止（許可: 1,2,3,6,7以降）"))

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
                            for dtype, ctx_names in dtype_counts.items():
                                if dtype not in duplicable_types and len(ctx_names) > 1:
                                    result.issues.append(Issue("CRITICAL", "CTX-017", mod_name,
                                        "fields[].displayType",
                                        f"displayType '{dtype}' が {len(ctx_names)} 件あります（{', '.join(ctx_names)}） — "
                                        f"'{dtype}' はフロー全体で1つのみ使用可です（重複可能なのは TEXT / NUMBER / DATE のみ）"))
                    except (json.JSONDecodeError, TypeError):
                        pass  # パース失敗は別チェック（CTX-014）で検出済み


def validate_phone_subflow(data: dict, result: ValidationResult):
    """電話番号聴取サブフローの必須モジュール配置チェック"""
    if "modules" not in data:
        return

    flow_name = data.get("name", "")
    is_phone_subflow = "電話番号" in flow_name

    if not is_phone_subflow:
        return

    # incoming-classifier が存在するか確認
    has_incoming = False
    has_mobile_script = False
    has_aggregation_script = False
    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "incoming-classifier" in mod_type.lower() or "incoming" in mod_type.lower():
            has_incoming = True
        # script_携帯判別 or 携帯判別スクリプト
        if ("Script" in mod_type or "script" in mod_type):
            script_content = mod.get("params", {}).get("script", "")
            if "mobilePattern" in script_content or "MOBILE" in script_content:
                has_mobile_script = True
            if "携帯電話判別" in script_content and "携帯以外" in script_content:
                has_aggregation_script = True

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
    subflow_keywords = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取", "個人情報", "診療科聴取", "RAG"]
    is_subflow = any(kw in flow_name for kw in subflow_keywords)

    # スクリプトモジュールの命名規則チェック（全フロー共通）
    for mod_name, mod in data["modules"].items():
        mod_type = mod.get("type", "")
        if "Script" in mod_type or "script" in mod_type:
            if not mod_name.startswith("script_"):
                result.issues.append(Issue("WARNING", "SCR-001", mod_name, "name",
                    f"スクリプトモジュール名が 'script_' プレフィックスで始まっていません: {mod_name}"))

    # サブフローの場合、結果返却スクリプトモジュールの存在チェック
    # self_contained型（サブフロー内で終話する設計）は結果返却不要
    desc = data.get("desc", "")
    is_self_contained = "termination:self_contained" in desc
    if is_subflow and not is_self_contained:
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
    subflow_keywords = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取", "個人情報", "診療科聴取", "RAG"]
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
        # 設計書フラグが未指定でDisconnectがある場合はCRITICAL（desc マーカー追加を強制）
        result.issues.append(Issue("CRITICAL", "SF-TERM-003", "(flow)", "termination",
            f"サブフロー '{flow_name}' に Disconnect モジュール ({', '.join(disconnect_modules)}) が "
            "配置されていますが、desc に 'termination:self_contained' マーカーがありません。"
            "サブフロー内で終話する設計であれば、フローJSONの desc フィールドに "
            "'termination:self_contained' を設定してください"))


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
            result.issues.append(Issue("WARNING", "N-002", mod_name, "name",
                "モジュール名に括弧が含まれています（実フローでの使用例あり、動作への影響は軽微）"))
        if " " in mod_name or "\u3000" in mod_name:
            result.issues.append(Issue("WARNING", "N-003", mod_name, "name",
                "モジュール名にスペースが含まれています"))


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
        result.issues.append(Issue("CRITICAL", "LAYOUT-001", "(flow)", "layout",
            f"{total}モジュール中{zero_count}モジュールのlayoutが(0,0)です — "
            "layout座標の自動計算が実行されていない可能性があります。"
            f"先頭5件: {zero_modules[:5]}"))
    elif zero_count > 2 and total > 1:
        result.issues.append(Issue("WARNING", "LAYOUT-002", "(flow)", "layout",
            f"{zero_count}モジュールのlayoutが(0,0)です: {zero_modules[:5]}"))

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
            # x幅が2000以上かつy幅がモジュール数×100未満 → 横並びと判定
            if x_range > 2000 and y_range < total * 100:
                result.issues.append(Issue("WARNING", "LAYOUT-003", "(flow)", "layout",
                    f"フローが横並び（水平）に配置されています "
                    f"（x範囲:{x_range}px, y範囲:{y_range}px）— "
                    "主経路はy軸方向（上から下）に配置してください"))


# ============================================================
# サブフロー参照チェック
# ============================================================

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

        properties = params.get("properties", "")
        if not properties:
            result.issues.append(Issue("INFO", "FLOW-005", mod_name,
                "params.properties",
                "Custom Jump to Flow の properties が空です — "
                "メインフローの Property.md がサブフローにも反映されるため、通常は問題ありません"))


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
            is_tts(modules[p].get("type", "")) or is_retry(modules[p].get("type", ""))
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
    subflow_keywords = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取", "個人情報", "診療科聴取", "RAG"]
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

    # 冒頭チェーンを最大8ホップたどる（wait→CTX→incoming→acceptance→冒頭TTS まで到達するため）
    # incoming-classifier では通常着信ルート、acceptance_times では true ルートを優先的に辿る
    chain = [start_name]
    current = start_name
    for _ in range(8):
        mod = modules.get(current, {})
        next_list = mod.get("next", [])
        if not next_list:
            break
        next_mod = ""
        mod_type = mod.get("type", "")

        if "incoming-classifier" in mod_type:
            # 通常着信ルートを辿る（非通知以外: 固定/携帯/海外/その他）
            for n in next_list:
                cond = n.get("condition", "")
                nm = n.get("nextModuleName", "")
                if nm and cond and "非通知" not in cond:
                    next_mod = nm
                    break
        elif "acceptance_times" in mod_type:
            # true 遷移先を辿る（営業時間内 → 冒頭アナウンス）
            for n in next_list:
                cond = n.get("condition", "")
                nm = n.get("nextModuleName", "")
                if nm and cond in ("true", "^true$"):
                    next_mod = nm
                    break

        if not next_mod:
            # デフォルト: 最初の有効な遷移先
            for n in next_list:
                nm = n.get("nextModuleName", "")
                if nm:
                    next_mod = nm
                    break
        if not next_mod or next_mod not in modules:
            break
        chain.append(next_mod)
        current = next_mod
        # TTSに到達したら冒頭チェーン探索終了
        if is_tts(modules.get(next_mod, {}).get("type", "")):
            break

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

    # FLOW-007: acceptance_times (or incoming-classifier) の直後がTTSモジュール（冒頭アナウンス）であるか
    # 冒頭アナウンスは acceptance_times の true 遷移先、または incoming-classifier の通常着信遷移先の
    # 直後にあるべき。途中の OpenAI やリトライを経由して辿り着くTTSは冒頭アナウンスではない。
    has_opening_tts = False
    for i, mod_name in enumerate(chain):
        mod = modules.get(mod_name, {})
        mod_type = mod.get("type", "")
        # acceptance_times または incoming-classifier の次のモジュールがTTSかチェック
        if "acceptance_times" in mod_type or "incoming-classifier" in mod_type:
            # この次のchain要素がTTSであるべき
            if i + 1 < len(chain):
                next_in_chain = chain[i + 1]
                next_type = modules.get(next_in_chain, {}).get("type", "")
                if is_tts(next_type):
                    has_opening_tts = True
                    break

    # acceptance_times がない場合、incoming-classifier の直後がTTSかチェック
    if not has_opening_tts:
        has_acceptance = any("acceptance_times" in modules.get(m, {}).get("type", "") for m in chain)
        has_incoming = any("incoming-classifier" in modules.get(m, {}).get("type", "") for m in chain)
        if not has_acceptance and not has_incoming:
            # どちらもない場合、チェーン内にTTSがあればOK（簡易フロー）
            for mod_name in chain:
                if is_tts(modules.get(mod_name, {}).get("type", "")):
                    has_opening_tts = True
                    break

    if not has_opening_tts:
        result.issues.append(Issue("CRITICAL", "FLOW-007", "(flow)",
            "冒頭チェーン",
            f"冒頭チェーン {' → '.join(chain[:6])} に冒頭アナウンス（TTSモジュール）が見つかりません — "
            "冒頭チェーン（wait → saveContextModel2DB → incoming-classifier → acceptance_times）の "
            "true遷移先に冒頭アナウンスTTSモジュールが必須です"))


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
            result.issues.append(Issue("CRITICAL", "PROMPT-003", mod_name,
                "params.prompt",
                "OpenAIモジュールの prompt が空欄です — prompter未実行の可能性があります"))
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
        prompt_labels = set()
        in_output_section = False
        for line in prompt.split("\n"):
            stripped = line.strip()
            # 「出力仕様」「出力」セクションの開始を検出
            if re.match(r'^#.*出力', stripped):
                in_output_section = True
                continue
            # 次のセクション開始で終了
            if in_output_section and stripped.startswith("#") and "出力" not in stripped:
                in_output_section = False
                continue
            # 出力仕様セクション内の "- ラベル" 行を抽出
            if in_output_section:
                # マークダウン区切り線 (---) はスキップ
                if re.match(r'^-{2,}$', stripped):
                    continue
                m = re.match(r'^[-\*]\s+(.+?)$', stripped)
                if m:
                    label = m.group(1).strip()
                    # NO_RESULT は分岐ラベルとしてはスキップ
                    if label and label != "NO_RESULT" and not label.startswith("-"):
                        prompt_labels.add(label)

        # PROMPT-001: next分岐ラベルがprompt出力仕様にない
        for label in next_labels:
            if label not in prompt_labels:
                result.issues.append(Issue("CRITICAL", "PROMPT-001", mod_name,
                    f"next.condition=^{label}$",
                    f"next分岐ラベル '{label}' がprompt出力仕様に存在しません — "
                    "OpenAIの応答がこの条件に一致しないため、フローが正しく分岐しません"))

        # PROMPT-002: prompt出力仕様にあるがnextに対応しないラベル
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
                # サイクル内にRetry Counterがあるか確認
                has_retry = any(is_retry(modules[m].get("type", "")) for m in cycle)
                if not has_retry:
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
        if ctx_name:
            if ctx_name in ctx_names_seen:
                result.issues.append(Issue("WARNING", "SAVECTX-002", mod_name,
                    "params.contextName",
                    f"contextName '{ctx_name}' が複数の saveContext2DB で保存されています — "
                    f"既出: {ctx_names_seen[ctx_name]}"))
            else:
                ctx_names_seen[ctx_name] = mod_name

    # SAVECTX-003: OpenAI分岐直後のsaveContext2DB（冗長パターン）
    # generate_by_OpenAI の next 先が saveContext2DB の場合は不要
    error_labels = {"timeout", "error", "no_result", "no_result"}
    for mod_name, mod in data["modules"].items():
        if "generate_by_OpenAI" not in mod.get("type", ""):
            continue
        for nx in mod.get("next", []):
            if nx.get("label", "").lower() in error_labels:
                continue
            next_name = nx.get("nextModuleName", "")
            if not next_name or next_name not in data["modules"]:
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
                result.issues.append(Issue("WARNING", "COMP-003", mod_name,
                    "next",
                    f"saveCompletionFlag2db が Disconnect/Reject に直接接続されています — "
                    f"終話ガイダンス（TTS）を間に配置してください: "
                    f"saveCompletionFlag2db → TTS → {next_mod_name}"))


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
                result.issues.append(Issue("WARNING", "COMP-003", mod_name,
                    "next",
                    f"saveCompletionFlag2db が Disconnect/Reject に直接接続されています — "
                    f"終話ガイダンス（TTS）を間に配置してください: "
                    f"saveCompletionFlag2db → TTS → {next_mod_name}"))


# ============================================================
# Brekeke 必須要件チェック（2026-04-22追加）
# ============================================================

def validate_matchingmethod_type(data: dict, result: ValidationResult):
    """matchingmethod が int型であることを検証"""
    if "modules" not in data:
        return
    for mod_name, mod in data["modules"].items():
        mm = mod.get("matchingmethod")
        if isinstance(mm, str):
            result.issues.append(Issue("CRITICAL", "MM-001", mod_name, "matchingmethod",
                f"matchingmethod が文字列 \"{mm}\" です — int型（{mm}）に修正してください"))
        elif mm is None:
            result.issues.append(Issue("CRITICAL", "MM-001", mod_name, "matchingmethod",
                "matchingmethod が未設定です — int型で設定してください（通常1, Retry Counterは0）"))


def validate_module_required_fields(data: dict, result: ValidationResult):
    """全モジュールに必須8フィールドが存在することを検証"""
    if "modules" not in data:
        return
    required = ["name", "description", "matchingmethod", "type", "params", "next", "subs", "layout"]
    for mod_name, mod in data["modules"].items():
        for field in required:
            if field not in mod:
                result.issues.append(Issue("CRITICAL", "S-004", mod_name, field,
                    f"必須フィールド '{field}' がモジュール内に存在しません — Brekekeアップロードに必要です"))


def validate_module_overlap(data: dict, result: ValidationResult):
    """モジュール座標の重なりを検出（同一座標に複数モジュール配置禁止）"""
    if "modules" not in data:
        return
    coords = []
    for mod_name, mod in data["modules"].items():
        layout = mod.get("layout", {})
        x = layout.get("x", 0)
        y = layout.get("y", 0)
        coords.append((mod_name, x, y))

    reported = set()
    for i in range(len(coords)):
        for j in range(i + 1, len(coords)):
            name_a, xa, ya = coords[i]
            name_b, xb, yb = coords[j]
            dx = abs(xa - xb)
            dy = abs(ya - yb)
            if dx < 200 and dy < 150:
                # (0,0) 同士は LAYOUT-001 で別途検出、ここではスキップ
                if xa == 0 and ya == 0 and xb == 0 and yb == 0:
                    continue
                pair = tuple(sorted([name_a, name_b]))
                if pair not in reported:
                    reported.add(pair)
                    result.issues.append(Issue("WARNING", "LAYOUT-004", name_a, "layout",
                        f"モジュール '{name_a}' ({xa},{ya}) と '{name_b}' ({xb},{yb}) が重なっています "
                        f"（距離 x:{dx}px, y:{dy}px — 最低 x:200px/y:150px 必要）"))


def validate_termination_position(data: dict, result: ValidationResult):
    """終話モジュール（完了フラグ→TTS→Disconnect）がフロー最下部にあることを検証"""
    if "modules" not in data:
        return
    modules = data["modules"]
    max_y = max((mod.get("layout", {}).get("y", 0) for mod in modules.values()), default=0)
    if max_y == 0:
        return
    threshold_y = max_y * 0.3  # y < 30% は冒頭付近 → 終話配置は不適切

    for mod_name, mod in modules.items():
        if "saveCompletionFlag2db" not in mod.get("type", ""):
            continue
        # 非通知・時間外は例外
        if "非通知" in mod_name or "時間外" in mod_name:
            continue
        y = mod.get("layout", {}).get("y", 0)
        if y < threshold_y:
            result.issues.append(Issue("WARNING", "LAYOUT-005", mod_name, "layout",
                f"完了フラグ '{mod_name}' (y={y}) がフロー上部に配置されています — "
                f"終話モジュールはフロー最下部（y >= {int(threshold_y)}）に配置してください"))


def validate_incoming_classifier_count(data: dict, result: ValidationResult):
    """incoming-classifier がフロー内に2つ以上ないことを検証"""
    if "modules" not in data:
        return
    flow_name = data.get("name", "")
    subflow_kw = ["氏名", "生年月日", "電話番号", "診察券番号", "聴取", "個人情報", "診療科聴取", "RAG"]
    if any(kw in flow_name for kw in subflow_kw):
        return  # サブフローはスキップ

    ic_modules = []
    for mod_name, mod in data["modules"].items():
        if "incoming-classifier" in mod.get("type", ""):
            ic_modules.append(mod_name)

    if len(ic_modules) > 1:
        result.issues.append(Issue("CRITICAL", "FLOW-008", "(flow)", "incoming-classifier",
            f"incoming-classifier がフロー内に {len(ic_modules)} 個あります（{', '.join(ic_modules)}）— "
            "フロー内1つのみ使用してください。SMS判定等はContextMatchRouterで実装すること"))


def validate_subflow_existence(data: dict, result: ValidationResult):
    """Jump to Flow の参照先サブフローが同ディレクトリに存在するか（CROSS-003）"""
    if "modules" not in data:
        return
    import glob as _glob_sf
    json_dir = os.path.dirname(os.path.abspath(result.file_path)) if result.file_path else "."
    available_flow_names = set()
    for sf_path in _glob_sf.glob(os.path.join(json_dir, "*.json")):
        try:
            with open(sf_path, "r", encoding="utf-8") as sf_f:
                sf_data = json.load(sf_f)
            sf_name = sf_data.get("name", "")
            if sf_name:
                available_flow_names.add(sf_name)
                # Jump to Flow の flowname は "drjoy^グループ名$フロー名" 形式だが、
                # フローJSON の name は "グループ名$フロー名" 形式のため、
                # drjoy^ プレフィックス付きも登録する
                available_flow_names.add(f"drjoy^{sf_name}")
        except Exception:
            pass

    for mod_name, mod in data["modules"].items():
        if "Custom Jump to Flow" not in mod.get("type", ""):
            continue
        params = mod.get("params", {})
        flowname = params.get("flowname", "") if isinstance(params, dict) else ""
        if flowname and available_flow_names and flowname not in available_flow_names:
            result.issues.append(Issue("CRITICAL", "CROSS-003", mod_name, "params.flowname",
                f"Jump to Flow の参照先 '{flowname}' に対応するサブフローJSONが見つかりません — "
                f"サブフローが .bivr に同梱されていない可能性があります"))


# ============================================================
# Properties 整合性チェック
# ============================================================

def find_properties_file(json_path: str) -> str:
    """フローJSONに対応するpropertiesファイルを探す（glob検索）"""
    import glob as _glob
    dir_path = os.path.dirname(json_path)
    # 同ディレクトリ → 親ディレクトリ → output/ の順で properties_*.md を検索
    search_dirs = [
        dir_path,
        os.path.dirname(dir_path),
        "output",
    ]
    for search_dir in search_dirs:
        if not search_dir or not os.path.isdir(search_dir):
            continue
        matches = _glob.glob(os.path.join(search_dir, "properties_*.md"))
        if matches:
            # demo環境を優先
            demo = [m for m in matches if "_demo" in os.path.basename(m)]
            return demo[0] if demo else matches[0]
    return ""


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

    # プロパティ行をパース（key=value 行を抽出。コードブロック内外両方に対応）
    prop_keys = set()
    prop_values = {}  # key → value（P-013/P-014チェック用）
    todo_lines = []
    for line in prop_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            continue
        if "=" in stripped and not stripped.startswith("#") and not stripped.startswith("//"):
            key, _, val = stripped.partition("=")
            key = key.strip()
            if key and not key.startswith("-") and not key.startswith("*"):
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
        prompt_key = f"{mod_name}.prompt"
        if prompt_key not in prop_keys:
            result.issues.append(Issue("WARNING", "P-010", mod_name, "properties",
                f"TTSモジュール '{mod_name}' に対応するプロパティ行 '{prompt_key}=' がありません"))

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
    for mod_name in retry_modules:
        mod = data["modules"].get(mod_name, {})
        params = mod.get("params", {})
        if isinstance(params, dict):
            for suffix in ["prompt_true", "prompt_false"]:
                val = params.get(suffix, "")
                if not val:
                    result.issues.append(Issue("WARNING", "P-011", mod_name, f"params.{suffix}",
                        f"Retryモジュール '{mod_name}' の params.{suffix} が空です — "
                        "リトライ発話文言はフローJSON内のparamsに直接記述する必要があります"
                        "（IVRプロパティでは動作しません）"))

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
            flow_name = data.get("name", "")
            # グループ名$フロー名 → グループ名部分（施設プレフィックス）を取得
            facility_prefix = flow_name.split("$")[0].split("_", 1)[-1] if "$" in flow_name else ""
            if facility_prefix:
                for sf_path in _glob.glob(os.path.join(json_dir, f"*{facility_prefix}*.json")):
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

    # チェック4: TODO_ 残存チェック
    for line in todo_lines:
        result.issues.append(Issue("WARNING", "P-030", "(properties)", "TODO",
            f"propertiesに TODO_ が残っています: {line[:80]}"))


# ============================================================
# メイン実行
# ============================================================

def validate_property_md(properties_path: str, flow_data: dict, result: ValidationResult):
    """bivr-checker固有: Property.mdの独自バリデーション (PROP-001〜004)"""
    if not properties_path or not os.path.exists(properties_path):
        return

    try:
        with open(properties_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return

    lines = content.split("\n")
    prop_keys = {}
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("#") or stripped.startswith("//"):
            continue
        if "=" in stripped:
            key, _, val = stripped.partition("=")
            key = key.strip()
            if key and not key.startswith("-") and not key.startswith("*"):
                prop_keys[key] = val.strip()

    # PROP-001: プロンプトキーとTTSモジュール名の整合性
    # メインフローの Property.md はサブフローにも反映されるため、
    # サブフロー内のTTSモジュール名も照合対象に含める
    tts_names = set()
    all_module_names = set()
    if "modules" in flow_data:
        for mod_name, mod in flow_data["modules"].items():
            all_module_names.add(mod_name)
            if is_tts(mod.get("type", "")):
                tts_names.add(mod_name)

    # サブフローJSONからもTTSモジュール名を収集
    import glob as _glob_prop
    json_dir = os.path.dirname(os.path.abspath(result.file_path)) if result.file_path else "."
    flow_name = flow_data.get("name", "")
    facility_prefix = flow_name.split("$")[0] if "$" in flow_name else ""
    if facility_prefix:
        for sf_path in _glob_prop.glob(os.path.join(json_dir, f"*{facility_prefix}*.json")):
            try:
                with open(sf_path, "r", encoding="utf-8") as sf_f:
                    sf_data = json.load(sf_f)
                if "modules" in sf_data:
                    for sf_mod_name, sf_mod in sf_data["modules"].items():
                        all_module_names.add(sf_mod_name)
                        if is_tts(sf_mod.get("type", "")):
                            tts_names.add(sf_mod_name)
            except Exception:
                pass

    prompt_keys = {k.replace(".prompt", "") for k in prop_keys if k.endswith(".prompt")}
    # 設定系プレフィックスを除外
    system_prefixes = {"amivoice", "office_id", "pbx", "context", "acceptance_times",
                       "openAI_generate", "rag_ssml", "speech"}
    prompt_keys = {k for k in prompt_keys if not any(k.startswith(p) for p in system_prefixes)}

    for pk in prompt_keys:
        if pk not in tts_names and pk not in all_module_names:
            result.issues.append(Issue("CRITICAL", "PROP-001", pk, "Property.md",
                f"Property.md のプロンプトキー '{pk}.prompt' に対応するTTSモジュールがフローJSONおよびサブフローに存在しません"))

    # PROP-002: 必須セクション欠落
    required_keys = ["amivoice.uri", "amivoice.language", "pbx.db.name",
                     "context.settings.url"]
    for rk in required_keys:
        if rk not in prop_keys:
            result.issues.append(Issue("CRITICAL", "PROP-002", "(Property.md)", rk,
                f"必須キー '{rk}' が Property.md に存在しません"))

    # office_id チェック（キー名にドットなし）
    if "office_id" not in prop_keys:
        result.issues.append(Issue("CRITICAL", "PROP-002", "(Property.md)", "office_id",
            "必須キー 'office_id' が Property.md に存在しません"))

    # PROP-003: 環境URL不一致
    demo_urls = [v for k, v in prop_keys.items() if "url" in k.lower() and "demo-reserve" in v]
    prod_urls = [v for k, v in prop_keys.items() if "url" in k.lower() and "reserve.drjoy" in v]
    if demo_urls and prod_urls:
        result.issues.append(Issue("WARNING", "PROP-003", "(Property.md)", "url",
            f"demo環境URL({len(demo_urls)}件)とprod環境URL({len(prod_urls)}件)が混在しています"))

    # PROP-004: amivoice設定欠落
    ami_required = ["amivoice.uri", "amivoice.language", "amivoice.engine"]
    for ak in ami_required:
        if ak not in prop_keys:
            result.issues.append(Issue("WARNING", "PROP-004", "(Property.md)", ak,
                f"amivoice設定 '{ak}' が欠落しています"))


def validate_cross(flow_data: dict, properties_path: str, subflow_paths: list, result: ValidationResult):
    """bivr-checker固有: フローJSON + Property.md + サブフロー間のクロスバリデーション"""
    if "modules" not in flow_data:
        return

    # CROSS-001: promptが空のTTSモジュールがProperty.mdにも未登録
    if properties_path and os.path.exists(properties_path):
        try:
            with open(properties_path, "r", encoding="utf-8") as f:
                prop_content = f.read()
            prop_module_keys = set()
            for line in prop_content.split("\n"):
                stripped = line.strip()
                if ".prompt=" in stripped and not stripped.startswith("#"):
                    key = stripped.split(".prompt=")[0].strip()
                    prop_module_keys.add(key)

            for mod_name, mod in flow_data["modules"].items():
                if not is_tts(mod.get("type", "")):
                    continue
                params = mod.get("params", {})
                prompt = params.get("prompt", "") if isinstance(params, dict) else ""
                if not prompt and mod_name not in prop_module_keys:
                    result.issues.append(Issue("CRITICAL", "CROSS-001", mod_name, "prompt",
                        f"TTSモジュール '{mod_name}' のpromptが空で、Property.mdにも対応キーがありません — 発話不能"))
        except Exception:
            pass

    # CROSS-003: Jump to Flow の参照先サブフローが同ディレクトリに存在するか
    # （サブフロー欠落チェック — .bivr に同梱されていない場合を検出）
    import glob as _glob_cross
    json_dir = os.path.dirname(os.path.abspath(result.file_path)) if result.file_path else "."
    available_flow_names = set()
    for sf_path in _glob_cross.glob(os.path.join(json_dir, "*.json")):
        try:
            with open(sf_path, "r", encoding="utf-8") as sf_f:
                sf_data = json.load(sf_f)
            sf_name = sf_data.get("name", "")
            if sf_name:
                available_flow_names.add(sf_name)
                # Jump to Flow の flowname は "drjoy^グループ名$フロー名" 形式だが、
                # フローJSON の name は "グループ名$フロー名" 形式のため、
                # drjoy^ プレフィックス付きも登録する
                available_flow_names.add(f"drjoy^{sf_name}")
        except Exception:
            pass

    for mod_name, mod in flow_data["modules"].items():
        if "Custom Jump to Flow" not in mod.get("type", ""):
            continue
        params = mod.get("params", {})
        flowname = params.get("flowname", "") if isinstance(params, dict) else ""
        if flowname and available_flow_names and flowname not in available_flow_names:
            result.issues.append(Issue("CRITICAL", "CROSS-003", mod_name, "params.flowname",
                f"Jump to Flow の参照先 '{flowname}' に対応するサブフローJSONが見つかりません — "
                f"サブフローが .bivr に同梱されていない可能性があります"))

    # CROSS-002: Custom Jump to Flow の flowname がサブフローと不一致
    if subflow_paths:
        subflow_names = set()
        for sf_path in subflow_paths:
            try:
                with open(sf_path, "r", encoding="utf-8") as f:
                    sf_data = json.load(f)
                name = sf_data.get("name", "")
                if name:
                    subflow_names.add(name)
            except Exception:
                pass

        for mod_name, mod in flow_data["modules"].items():
            if "Custom Jump to Flow" not in mod.get("type", ""):
                continue
            params = mod.get("params", {})
            flowname = params.get("flowname", "") if isinstance(params, dict) else ""
            if flowname and subflow_names and flowname not in subflow_names:
                result.issues.append(Issue("CRITICAL", "CROSS-002", mod_name, "params.flowname",
                    f"Jump to Flow の flowname '{flowname}' がサブフローJSONのname値と一致しません — "
                    f"利用可能なサブフロー: {', '.join(sorted(subflow_names))}"))


def validate_flow(file_path: str, check_properties: bool = True, check_prompts: bool = True, properties_override: str = None, subflow_paths: list = None) -> ValidationResult:
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
    validate_phone_subflow(data, result)
    validate_script_modules(data, result)
    # desc フィールドから termination マーカーを自動読み取り
    desc = data.get("desc", "")
    design_term = ""
    if "termination:self_contained" in desc:
        design_term = "self_contained"
    validate_subflow_termination(data, result, design_termination=design_term)
    validate_naming(data, result)
    validate_layout(data, result)
    validate_subflow_references(data, result)
    validate_dtmf_modules(data, result)
    validate_stt_predecessors(data, result)
    validate_flow_structure(data, result)
    if check_prompts:
        validate_prompt_labels(data, result)
    validate_reachability(data, result)
    validate_savectx(data, result)
    validate_completion_flag_order(data, result)
    validate_matchingmethod_type(data, result)
    validate_module_required_fields(data, result)
    validate_module_overlap(data, result)
    validate_termination_position(data, result)
    validate_incoming_classifier_count(data, result)
    validate_subflow_existence(data, result)

    # Properties 整合性チェック
    if check_properties:
        prop_path = properties_override or find_properties_file(file_path)
        if prop_path:
            validate_properties(data, prop_path, result)
            validate_property_md(prop_path, data, result)
            validate_cross(data, prop_path, subflow_paths or [], result)
            print(f"  [Properties] チェック対象: {prop_path}")
        else:
            result.issues.append(Issue("CRITICAL", "P-000", "(properties)", "file",
                "対応するpropertiesファイルが見つかりません — TTSが発話できない状態です（--no-props で無視可）"))
    elif subflow_paths:
        validate_cross(data, "", subflow_paths, result)

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
    print()

    if result.issues:
        print("--- 検出事項 ---")
        for issue in sorted(result.issues,
                            key=lambda x: {"CRITICAL": 0, "WARNING": 1, "INFO": 2}[x.severity]):
            print(f"  {issue}")
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validator.py <flow.json> [options]")
        print("       python scripts/validator.py output/flows/*.json")
        print()
        print("Options:")
        print("  --no-props              propertiesチェックをスキップ")
        print("  --no-prompts            promptラベル整合性チェックをスキップ")
        print("  --properties <file>     propertiesファイルを明示的に指定")
        print("  --subflows <file> ...   サブフローJSONを指定（CROSS-002チェック有効化）")
        print("  --json                  結果をJSON形式で出力（orchestrator連携用）")
        sys.exit(1)

    check_properties = "--no-props" not in sys.argv
    check_prompts = "--no-prompts" not in sys.argv
    output_json = "--json" in sys.argv

    # オプション解析
    properties_override = None
    subflow_paths = []
    files = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--properties" and i + 1 < len(sys.argv):
            properties_override = sys.argv[i + 1]
            i += 2
            continue
        elif arg == "--subflows":
            i += 1
            while i < len(sys.argv) and not sys.argv[i].startswith("--"):
                subflow_paths.append(sys.argv[i])
                i += 1
            continue
        elif arg.startswith("--"):
            i += 1
            continue
        else:
            files.append(arg)
        i += 1

    all_pass = True
    results = []

    for file_path in files:
        if not os.path.exists(file_path):
            if not output_json:
                print(f"[WARN] ファイルが見つかりません: {file_path}")
            continue
        result = validate_flow(file_path, check_properties=check_properties,
                               check_prompts=check_prompts,
                               properties_override=properties_override,
                               subflow_paths=subflow_paths)
        results.append(result)
        if not output_json:
            print_report(result)
        if not result.is_valid:
            all_pass = False

    if output_json:
        output = [r.to_dict() for r in results]
        print(json.dumps(output, ensure_ascii=False, indent=2))

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
