#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qa_validator.py -- 設計書YAML 機械的整合性チェック（33項目）

設計書のQAを全て機械的に実行する。LLM審査は廃止済み。

使い方:
    python3 schemas/qa_validator.py output/scenarios/〇〇病院_〇〇/設計書_〇〇病院_〇〇.yaml

終了コード:
    0: PASS（CRITICAL なし）
    1: FAIL（CRITICAL あり）

対応チェック:
    T-1〜T-8: テンプレート適合性（全8項目）
    L-1, L-2, L-3, L-5, L-6, L-8: 論理整合性（6項目）
    E-1, E-2, E-5a〜E-5d, E-6, E-7, E-8, E-9, E-10: エラーパス網羅性（11項目）
    E-17: Scripts 最大化（enum/datetime hearing の専用ブロック型推奨・fallback 値推奨）(R-3/R-2)
    E-18: script_blocks (gen_scripts.py) の NO_RESULT/REPEAT_LIMIT フォールバック未接続検出
    I-1, I-3, I-4, I-5, I-6: インテント網羅性（5項目）
    I-7: 個人情報4種（slot: patient_name/date_of_birth/phone/card_number）の主要TTSに
         施設固有の文言（tts_modules/step_details）が定義されているか（未定義は gen_properties.py が
         汎用デフォルトで救済するため WARNING）
    L-4: TTS カバレッジ（1項目）
    M-2: トーン＆マナー（1項目）
    F-1, F-2, F-3, F-4, F-6, F-7a: scenario_flow ブロック構造（6項目）
      F-1  到達性 (start から全ブロック到達可能)
      F-2  参照整合性 (next/conditions.next が実在 step を指す)
      F-3  ブロック型 allowlist (KNOWN_BLOCK_TYPES 参照・augment 使用は WARNING)
      F-4  step 名一意性
      F-6  ブロック型ごとの必須フィールド
      F-7a subflow flowname が flow_structure.subflows に登録済
    F-8: faq_items 定義時に type: faq ブロック必須 (R-7)
    F-9: 電話番号/患者氏名/生年月日の hearing は type: slot 必須 (R-8)
    V-1: TTS 変数/プレースホルダー位置規則 — 中間フローの TTS に <%変数%> や
         （A/B）型プレースホルダーを置かない（ルート分割で解消）。<%変数%> の
         TTS 参照は終話（termination）のみ許可（2026-07-16 設計原則）
    V-2: <%変数%> プロベナンス — TTS / reference_module が参照する変数が
         setObject する部品（intent/slot/script/faq 等）で保存されているか。
         OpenAI 系 hearing の save_to は setObject されず実行時に空になるため検出
    V-3: TTS 文中の隣接重複フレーズ（コピペ typo）検出 — 「ない場合は、ない場合は」
         のような CSV/設計書の手入力ミスを壁打ちに頼らず機械的に検出する（2026-07-17）
    V-5: TTS 文中の未確定プレースホルダー文字「〇」検出（例: 〇月〇日）（2026-07-17）
    V-6: 復唱あり時の復唱文言（reconfirm_tts）未記入 / 代入位置なしを警告（2026-07-17）
    S-1: TTS↔選択肢↔スクリプト整合（2026-07-16 設計原則）
         1) TTS の「N番、ラベル」列挙と options/choices の (number,label) 一致
         2) 列挙数と選択肢数の一致
         3) TTS プッシュ案内 ⇔ stt_type DTMF 系の整合
         4) label が自身の keywords に含まれるか
         5) CMR conditions.match ⊆ 保存元 intent/hearing の label 集合
    S-2: DTMF キー約束整合 — TTS が押下を約束したキーと設定の照合。
         '#'（scaffold 終端キー）の選択肢利用 / '*' 系の終端案内 /
         受付キー集合に無いキーの約束を CRITICAL、「こめじるし」呼称は WARNING
"""

import argparse
import json
import re
import sys
import urllib.parse
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

import yaml

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
try:
    from scaffold_generator import SLOT_SUPPORTED
except ImportError:
    # scaffold_generator.py が読めない環境向けのフォールバック。
    # scaffold_generator.SLOT_SUPPORTED と手動で同期させること（本来はここに来ない想定）。
    SLOT_SUPPORTED = {"patient_name", "date_of_birth", "phone"}

# ──────────────────────────────────────────────
# 定数
# ──────────────────────────────────────────────

REQUIRED_SECTIONS = [
    "basic_info", "flow_structure", "purpose", "flow_diagrams",
    "context_fields", "hearing_items", "step_details", "termination_patterns",
    "tts_modules", "amivoice_dictionary", "special_notes", "confirmation_items",
]

VALID_FLOW_TYPES = {"1flow", "subflow"}
VALID_WORK_TYPES = {"new", "modify", "gen2_migration", "gen1_migration"}
VALID_DISPLAY_TYPES = {
    "CLASSIFICATION", "DEPARTMENT", "TEXT", "NUMBER",
    "DATE_OF_BIRTH", "PHONE_NUMBER", "PHONE_NUMBER_CALL", "DATE", "STATUS",
}
VALID_RETRY_FAILURE = {"skip", "end_failure", "disconnect"}


# ──────────────────────────────────────────────
# 結果バッファ
# ──────────────────────────────────────────────

@dataclass
class QAIssue:
    """1 件の検証結果。

    fix_category:
      "director" (default) — LLM director に差し戻して修正させる
      "auto"               — yaml_auto_fixer.py が fix_action に従って機械的に修正
    fix_action (fix_category="auto" 時のみ参照):
      {"op": "replace_all", "pattern": <regex>, "replacement": <str>}
        → yaml テキストに対する正規表現全置換（text-level でコメント保持）
    """
    severity: str  # "CRITICAL" / "WARNING"
    code: str      # "T-1" / "E-8" / etc.
    message: str
    fix_category: str = "director"
    fix_action: Optional[dict] = None


_issues: list[QAIssue] = []


def _add(level: str, code: str, msg: str,
         fix_category: str = "director",
         fix_action: Optional[dict] = None) -> None:
    _issues.append(QAIssue(level, code, msg, fix_category, fix_action))


# ──────────────────────────────────────────────
# ヘルパー
# ──────────────────────────────────────────────

def _safe_list(d: dict, key: str) -> list:
    """キーが存在し list である場合のみ返す。それ以外は []。"""
    val = d.get(key)
    return val if isinstance(val, list) else []


def _get_subflow_targets(d: dict) -> set[str]:
    """flow_structure.subflows から委譲対象ターゲット名を収集"""
    return {
        sub.get("target", "")
        for sub in _safe_list(d.get("flow_structure") or {}, "subflows")
        if isinstance(sub, dict) and sub.get("target")
    }


def _is_subflow_delegated(name: str, subflow_targets: set[str]) -> bool:
    """hearing_item 名がサブフロー委譲対象かを判定（部分一致含む）"""
    return any(name in t or t in name for t in subflow_targets)


# slot: 宣言的個人情報スロット。
# SLOT_SUPPORTED は scripts/scaffold_generator.py から import（単一情報源・冒頭 import 参照）。
# type:slot ブロックは認定済み決定論部品でインライン展開されるため、サブフロー委譲と
# 同様に step_details / DTMF対応表（director 記述）を要さない。


# slot: 系ファーストクラス型（scaffold がインライン展開するため step_details 不要）
SLOT_LIKE_TYPES = {"slot", "dob", "phone", "patient_name"}


def _get_slot_delegated_names(d: dict) -> set[str]:
    """type:slot / dob / phone / patient_name ブロックが決定論インライン展開で受け持つ聴取項目名を収集。"""
    names: set[str] = set()
    for blk in _safe_list(d, "scenario_flow"):
        if isinstance(blk, dict) and blk.get("type") in SLOT_LIKE_TYPES:
            step = blk.get("step")
            if step:
                names.add(str(step))
    return names


def _is_slot_delegated(name: str, slot_names: set[str]) -> bool:
    """hearing_item 名が slot インライン展開対象かを判定（部分一致含む。subflow と同セマンティクス）"""
    return any(name in s or s in name for s in slot_names)


def _count_todo(raw_text: str) -> int:
    """コメント行を除いた TODO_要確認 の出現数を返す。"""
    count = 0
    for line in raw_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#"):
            continue
        count += line.count("TODO_要確認")
    return count


# ──────────────────────────────────────────────
# チェック関数
# ──────────────────────────────────────────────

def check_t1(d: dict) -> None:
    """T-1: 全12セクション存在確認"""
    for key in REQUIRED_SECTIONS:
        if key not in d or d[key] is None:
            _add("CRITICAL", "T-1", f"必須セクション '{key}' が欠落または null")


def check_t2(d: dict) -> None:
    """T-2: 必須フィールドが空でない + flow_name 形式 + scenario_name 整合"""
    bi = d.get("basic_info") or {}
    for field in ["facility_name", "group_name", "flow_name", "flow_type"]:
        val = bi.get(field)
        if not val or str(val).strip() == "":
            _add("CRITICAL", "T-2", f"basic_info.{field} が空または未設定")
    flow_name = str(bi.get("flow_name") or "").strip()
    scenario_name = str(bi.get("scenario_name") or "").strip()
    # T-2a: flow_name は「グループ名$シナリオ名」形式であること
    if flow_name and "$" not in flow_name:
        _add("CRITICAL", "T-2a",
             f"basic_info.flow_name='{flow_name}' が 'グループ名$シナリオ名' 形式ではない（$ が含まれていない）")
    # T-2b: flow_name の $ 以降が scenario_name と一致していること（両方設定されている場合のみ）
    if flow_name and scenario_name and "$" in flow_name:
        flow_scenario = flow_name.split("$", 1)[1]
        if flow_scenario != scenario_name:
            _add("CRITICAL", "T-2b",
                 f"basic_info.flow_name='{flow_name}' の '$' 以降 '{flow_scenario}' と "
                 f"basic_info.scenario_name='{scenario_name}' が不一致")
    # T-2d: flow_name の '$' より前が group_name と完全一致していること。
    # 命名規則（日付サフィックスは group_name 側に付ける）の整合性を担保するため、
    # flow_name の group 部・全 flowname 参照・サブフロー JSON 名がすべて group_name と
    # 揃っている必要がある（docs/brekeke/naming_convention.md）。
    group_name = str(bi.get("group_name") or "").strip()
    if flow_name and group_name and "$" in flow_name:
        flow_group = flow_name.split("$", 1)[0]
        if flow_group != group_name:
            _add("CRITICAL", "T-2d",
                 f"basic_info.flow_name='{flow_name}' の '$' より前 '{flow_group}' が "
                 f"basic_info.group_name='{group_name}' と不一致。日付サフィックスを変えた場合は "
                 f"group_name / flow_name / 全 flowname 参照をすべて同じグループ名に揃えること "
                 f"(naming_convention.md)")
    # T-2c: scenario_name は推奨（orchestrator の state.flow 正規化に使用）。
    # 未設定でも flow_name の '$' 以降から派生可能なので WARNING 止まり。
    # 既存の YAML との後方互換を保ち、director に次回から書くよう促す用途。
    if not scenario_name:
        derivable = "$" in flow_name
        if derivable:
            _add("WARNING", "T-2c",
                 f"basic_info.scenario_name が未設定（推奨）。flow_name から派生可能だが、director は次回から明示的に設定すること")
        else:
            _add("CRITICAL", "T-2c",
                 f"basic_info.scenario_name が未設定で flow_name からも派生不可（'$' 無し）。director が設定すること")
    purpose = d.get("purpose")
    if not purpose or str(purpose).strip() == "":
        _add("CRITICAL", "T-2", "purpose が空または未設定")


def check_t3(d: dict) -> None:
    """T-3: flow_type 値域チェック"""
    bi = d.get("basic_info") or {}
    ft = bi.get("flow_type", "")
    if ft and ft not in VALID_FLOW_TYPES:
        _add("CRITICAL", "T-3",
             f"basic_info.flow_type='{ft}' が不正。許容値: {sorted(VALID_FLOW_TYPES)}。"
             f"auto fix: '1flow' に正規化",
             fix_category="auto",
             fix_action={
                 "op": "replace_all",
                 "pattern": rf'(\bflow_type\s*:\s*)["\']?{re.escape(ft)}["\']?',
                 "replacement": r'\1"1flow"',
             })
    fs_type = (d.get("flow_structure") or {}).get("type", "")
    if fs_type and fs_type not in VALID_FLOW_TYPES:
        _add("CRITICAL", "T-3",
             f"flow_structure.type='{fs_type}' が不正。許容値: {sorted(VALID_FLOW_TYPES)}。"
             f"auto fix: '1flow' に正規化",
             fix_category="auto",
             fix_action={
                 "op": "replace_all",
                 "pattern": rf'(\btype\s*:\s*)["\']?{re.escape(fs_type)}["\']?',
                 "replacement": r'\1"1flow"',
             })


def check_t4(d: dict) -> None:
    """T-4: work_type 値域チェック"""
    bi = d.get("basic_info") or {}
    wt = bi.get("work_type", "")
    if wt and wt not in VALID_WORK_TYPES:
        _add("CRITICAL", "T-4",
             f"basic_info.work_type='{wt}' が不正。許容値: {sorted(VALID_WORK_TYPES)}。"
             f"auto fix: 'new' に正規化（新規作成として扱う）",
             fix_category="auto",
             fix_action={
                 "op": "replace_all",
                 "pattern": rf'(\bwork_type\s*:\s*)["\']?{re.escape(wt)}["\']?',
                 "replacement": r'\1"new"',
             })


def check_t5(d: dict, raw_text: str) -> None:
    """T-5: TODO_要確認 が confirmation_items に列挙されているか（WARNING）"""
    todo_count = _count_todo(raw_text)
    conf_items = _safe_list(d, "confirmation_items")
    unresolved = [
        ci for ci in conf_items
        if isinstance(ci, dict) and ci.get("resolved") is False
    ]
    if todo_count > 0 and len(unresolved) == 0:
        _add("WARNING", "T-5",
             f"TODO_要確認 が {todo_count} 件あるが confirmation_items に未解決項目がない")
    elif todo_count > len(unresolved):
        _add("WARNING", "T-5",
             f"TODO_要確認 が {todo_count} 件に対し confirmation_items 未解決が {len(unresolved)} 件。"
             "未登録の TODO がある可能性")


def check_t6(d: dict) -> None:
    """T-6: hearing_items が1件以上"""
    if len(_safe_list(d, "hearing_items")) == 0:
        _add("CRITICAL", "T-6", "hearing_items が空または未定義")


def check_t7(d: dict) -> None:
    """T-7: termination_patterns が1件以上"""
    if len(_safe_list(d, "termination_patterns")) == 0:
        _add("CRITICAL", "T-7", "termination_patterns が空または未定義")


def check_t8(d: dict) -> None:
    """T-8: context_fields が1件以上"""
    if len(_safe_list(d, "context_fields")) == 0:
        _add("CRITICAL", "T-8", "context_fields が空または未定義")


def check_t9(d: dict) -> None:
    """T-9: 新規/移行フローは個人情報を 1flow インライン配置必須（#255）。"""
    bi = d.get("basic_info") or {}
    wt = (bi.get("work_type") or "new").strip()
    if wt not in {"new", "gen2_migration", "gen1_migration"}:
        return
    personal = sorted({
        t for t in _get_subflow_targets(d)
        if t in {"氏名聴取", "生年月日聴取", "電話番号聴取", "診察券番号聴取"} or t.startswith("個人情報聴取")
    })
    if personal:
        _add("CRITICAL", "T-9",
             f"work_type='{wt}' は 1flow 必須ですが個人情報サブフロー {personal} が分割されています（#255）。"
             f"type:slot=氏名/生年月日/電話・診察券は hearing ブロックでインライン配置に作り直してください。")


def check_l1(d: dict) -> None:
    """L-1: hearing_items[].save_to が context_fields[].context_name に存在"""
    ctx_names = {
        c.get("context_name")
        for c in _safe_list(d, "context_fields")
        if isinstance(c, dict) and c.get("context_name")
    }
    for hi in _safe_list(d, "hearing_items"):
        if not isinstance(hi, dict):
            continue
        st = hi.get("save_to", "")
        if st and st not in ctx_names:
            _add("CRITICAL", "L-1",
                 f"hearing_items '{hi.get('name', '?')}' の save_to='{st}' が context_fields に存在しない")


def check_l2(d: dict) -> None:
    """L-2: termination_patterns[].status が STATUS context_field の range_values に含まれる"""
    status_field = next(
        (c for c in _safe_list(d, "context_fields")
         if isinstance(c, dict) and c.get("display_type") == "STATUS"),
        None,
    )
    if status_field is None:
        return
    valid_ids = {
        str(rv.get("id"))
        for rv in (status_field.get("range_values") or [])
        if isinstance(rv, dict) and rv.get("id") is not None
    }
    if not valid_ids:
        return
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        s = str(tp.get("status", ""))
        if s and s not in valid_ids:
            _add("CRITICAL", "L-2",
                 f"termination_patterns '{tp.get('name', '?')}' の status='{s}' が "
                 f"STATUS context_field の range_values に存在しない（有効値: {sorted(valid_ids)}）")


def check_l5(d: dict) -> None:
    """L-5: context_fields[].display_type 値域チェック"""
    for c in _safe_list(d, "context_fields"):
        if not isinstance(c, dict):
            continue
        dt = c.get("display_type", "")
        if dt and dt not in VALID_DISPLAY_TYPES:
            _add("CRITICAL", "L-5",
                 f"context_fields '{c.get('context_name', '?')}' の display_type='{dt}' が不正。"
                 f"許容値: {sorted(VALID_DISPLAY_TYPES)}。auto fix: 'TEXT' に正規化",
                 fix_category="auto",
                 fix_action={
                     "op": "replace_all",
                     "pattern": rf'(\bdisplay_type\s*:\s*)["\']?{re.escape(dt)}["\']?',
                     "replacement": r'\1"TEXT"',
                 })


# Dr.JOY デフォルト項目（scaffold_generator.SYSTEM_CONTEXT_OVERRIDES の item_default: True と同期）。
# これ以外の contextName はすべて「カスタム項目」＝ itemDefault: false 必須・rangeValues に id 不要
# （羽生総合病院_診療 実機確定 2026-07-18）。
DEFAULT_CONTEXT_NAMES = {
    "classification", "patientName", "medicalCardNumber", "clinicalDepartment",
    "patientDateOfBirth", "reason", "reservationDate", "telephoneNumber",
    "additionalPhoneNumber", "status", "dateOfCall",
}


def check_l11(d: dict) -> None:
    """L-11: カスタムコンテキスト項目の仕様チェック（羽生総合病院_診療 実機確定 2026-07-18）。
    デフォルト項目以外の context_fields は:
      (a) item_default: true を宣言してはいけない（デフォルト項目のコピペ事故）→ CRITICAL
      (b) range_values に id は不要（value と order のみ）→ WARNING（scaffold が出力時に除去する）
    """
    for c in _safe_list(d, "context_fields"):
        if not isinstance(c, dict):
            continue
        cn = c.get("context_name", "")
        if not cn or cn in DEFAULT_CONTEXT_NAMES:
            continue
        # callId は案件固有システム値だが scaffold の SYSTEM_CONTEXT_OVERRIDES が
        # itemDefault: false へ機械的に上書きするため、YAML 側の誤記は無害（既存設計書に多数存在）
        if cn != "callId" and c.get("item_default") is True:
            _add("CRITICAL", "L-11",
                 f"カスタムコンテキスト項目 '{cn}' に item_default: true が宣言されている。"
                 f"デフォルト項目以外は itemDefault: false 必須（item_default 行を削除するか false にする）")
        for rv in c.get("range_values") or []:
            if isinstance(rv, dict) and "id" in rv:
                _add("WARNING", "L-11",
                     f"カスタムコンテキスト項目 '{cn}' の range_values に id が指定されている。"
                     f"カスタム項目の rangeValues は value と order のみでよい（id 不要）。"
                     f"scaffold は出力時に id を除去する")
                break


def check_l6(d: dict) -> None:
    """L-6: flow_type=subflow の場合 subflows が1件以上定義されている"""
    bi = d.get("basic_info") or {}
    if bi.get("flow_type") != "subflow":
        return
    fs = d.get("flow_structure") or {}
    subs = _safe_list(fs, "subflows")
    if not subs:
        _add("CRITICAL", "L-6", "flow_type=subflow だが flow_structure.subflows が空または未定義")
        return
    named = [s for s in subs if isinstance(s, dict) and s.get("name")]
    if not named:
        _add("CRITICAL", "L-6", "flow_structure.subflows の全エントリに name が未設定")


# Dr.JOY 仕様: CLASSIFICATION/DEPARTMENT は「予約型」でそれぞれ専用 context にしか使えない。
#   CLASSIFICATION = 用件区分(context_name='classification') 専用
#   DEPARTMENT     = 診療科(context_name='clinicalDepartment') 専用
# 他のカスタム項目に割り当てると、Dr.JOY 項目をプルダウンにしても AI 保存値が反映されない
# （実機確定 2026-06-24 ヘルスケアクリニック厚木: 受診エリア/受診施設を CLASSIFICATION から
#   TEXT に変えて初めて反映）。カスタム項目は TEXT / NUMBER 等の非予約型を使う。
_RESERVED_DISPLAY_TYPES = {
    "CLASSIFICATION": "classification",
    "DEPARTMENT": "clinicalDepartment",
}


def check_l9(d: dict) -> None:
    """L-9: 予約型 display_type(CLASSIFICATION/DEPARTMENT) を専用 context 以外に割り当てていないか。"""
    for c in _safe_list(d, "context_fields"):
        if not isinstance(c, dict):
            continue
        dt = c.get("display_type", "")
        cn = c.get("context_name", "")
        reserved_for = _RESERVED_DISPLAY_TYPES.get(dt)
        if reserved_for and cn != reserved_for:
            _add("WARNING", "L-9",
                 f"context_fields '{cn}' の display_type='{dt}' は予約型です"
                 f"（{dt} は context_name='{reserved_for}' 専用＝Dr.JOY 仕様）。"
                 f"カスタム項目は TEXT / NUMBER 等の非予約型にしてください"
                 f"（プルダウンにしても AI 保存値が反映されません。Dr.JOY 項目設定の入力形式も"
                 f"プルダウン以外に。実機確定 2026-06-24 厚木）。")


def check_l8(d: dict) -> None:
    """L-8: sms_flag_routing.enabled=true の場合 routing_keys が空でない"""
    sfr = d.get("sms_flag_routing") or {}
    if sfr.get("enabled") is True:
        rk = _safe_list(sfr, "routing_keys")
        if not rk:
            _add("CRITICAL", "L-8",
                 "sms_flag_routing.enabled=true だが routing_keys が空")


def check_e1(d: dict) -> None:
    """E-1: 全 hearing_items に retry_count が設定されている（サブフロー委譲項目を除く）"""
    subflow_targets = _get_subflow_targets(d)
    for hi in _safe_list(d, "hearing_items"):
        if not isinstance(hi, dict):
            continue
        name = hi.get("name", "?")
        # サブフロー委譲項目のリトライ制御はサブフロー側が担当するためスキップ
        if _is_subflow_delegated(name, subflow_targets):
            continue
        if hi.get("retry_count") is None:
            _add("CRITICAL", "E-1",
                 f"hearing_items '{name}' に retry_count が未設定")


def check_e2b(d: dict) -> None:
    """E-2b: step_details.retry_failure と hearing_items.retry_failure の整合（#291）。"""
    DEFAULT_RF = "end_failure"
    hi_map = {
        hi.get("name"): hi
        for hi in _safe_list(d, "hearing_items")
        if isinstance(hi, dict) and hi.get("name")
    }
    for sd in _safe_list(d, "step_details"):
        if not isinstance(sd, dict):
            continue
        name = sd.get("step_name")
        if not name or name not in hi_map:
            continue
        hi = hi_map[name]
        sd_rf = sd.get("retry_failure") or DEFAULT_RF
        hi_rf = hi.get("retry_failure") or DEFAULT_RF
        if sd_rf != hi_rf:
            _add("CRITICAL", "E-2b",
                 f"'{name}': step_details.retry_failure='{sd_rf}' と "
                 f"hearing_items.retry_failure='{hi_rf}' が不一致（#291）。"
                 f"scaffold は hearing_items 側を読むため hearing_items にも同値を明記してください。")


def check_e2(d: dict) -> None:
    """E-2: 全 step_details に retry_failure が設定されている"""
    for sd in _safe_list(d, "step_details"):
        if not isinstance(sd, dict):
            continue
        rf = sd.get("retry_failure", "")
        if not rf:
            _add("CRITICAL", "E-2",
                 f"step_details '{sd.get('step_name', '?')}' に retry_failure が未設定")
        elif rf not in VALID_RETRY_FAILURE:
            _add("WARNING", "E-2",
                 f"step_details '{sd.get('step_name', '?')}' の retry_failure='{rf}' が不正。"
                 f"許容値: {sorted(VALID_RETRY_FAILURE)}")


def check_i1(d: dict) -> None:
    """I-1: 各 hearing_item に対応する step_details が存在する
    （サブフロー委譲項目・slot インライン展開項目を除く）"""
    sd_names = {
        sd.get("step_name")
        for sd in _safe_list(d, "step_details")
        if isinstance(sd, dict) and sd.get("step_name")
    }
    subflow_targets = _get_subflow_targets(d)
    slot_names = _get_slot_delegated_names(d)

    for hi in _safe_list(d, "hearing_items"):
        if not isinstance(hi, dict):
            continue
        name = hi.get("name", "")
        if not name:
            continue
        # slot インライン展開は認定済み決定論部品が処理を担うため step_details 不要（subflow 委譲と同扱い）
        if (name in sd_names or _is_subflow_delegated(name, subflow_targets)
                or _is_slot_delegated(name, slot_names)):
            continue
        _add("CRITICAL", "I-1",
             f"hearing_items '{name}' に対応する step_details が存在しない"
             "（サブフロー委譲でも slot インライン展開でもない）")


def check_i3(d: dict) -> None:
    """I-3: output_labels ↔ openai_rules.output_values 一致（Single Source of Truth）"""
    sd_map = {
        sd.get("step_name"): sd
        for sd in _safe_list(d, "step_details")
        if isinstance(sd, dict) and sd.get("step_name")
    }
    for hi in _safe_list(d, "hearing_items"):
        if not isinstance(hi, dict):
            continue
        if hi.get("openai_processing", "none") == "none":
            continue
        labels = [str(lb) for lb in (hi.get("output_labels") or []) if lb]
        if not labels:
            continue
        name = hi.get("name", "")
        sd = sd_map.get(name)
        if sd is None:
            continue  # I-1 で検出済み
        rules = sd.get("openai_rules") or {}
        # NO_RESULT は step_details 側のフォールバック用センチネルのため比較から除外
        out_vals = [str(v) for v in (rules.get("output_values") or []) if v and str(v) != "NO_RESULT"]
        if set(labels) != set(out_vals):
            _add("CRITICAL", "I-3",
                 f"'{name}': hearing_items.output_labels={labels} と "
                 f"step_details.openai_rules.output_values={out_vals} が不一致")


# ──────────────────────────────────────────────
# E-5a〜E-5d, E-6, E-7: termination_patterns チェック
# ──────────────────────────────────────────────

def check_e5a(d: dict) -> None:
    """E-5a: termination_patterns に非通知パターンが存在する"""
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        name = str(tp.get("name", ""))
        condition = str(tp.get("condition", ""))
        if "非通知" in name or "非通知" in condition:
            return
    _add("CRITICAL", "E-5a", "termination_patterns に非通知パターンが存在しない")


def check_e5b(d: dict) -> None:
    """E-5b: termination_patterns に時間外パターンが存在する"""
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        name = str(tp.get("name", ""))
        condition = str(tp.get("condition", ""))
        if "時間外" in name or "時間外" in condition:
            return
    _add("CRITICAL", "E-5b", "termination_patterns に時間外パターンが存在しない")


def check_e5c(d: dict) -> None:
    """E-5c: termination_patterns に聴取失敗/リトライ上限パターンが存在する"""
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        name = str(tp.get("name", ""))
        condition = str(tp.get("condition", ""))
        if "聴取失敗" in name or "リトライ" in name or "リトライ" in condition:
            return
    _add("CRITICAL", "E-5c", "termination_patterns に聴取失敗/リトライ上限パターンが存在しない")


def check_e5d(d: dict) -> None:
    """E-5d: termination_patterns に正常系パターン（status が 2,3,6 以外）が1つ以上存在する"""
    abnormal_statuses = {"2", "3", "6"}
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        status = str(tp.get("status", ""))
        if status and status not in abnormal_statuses:
            return
    _add("CRITICAL", "E-5d",
         "termination_patterns に正常系パターン（status が 2,3,6 以外）が存在しない")


# 許可される status 値（第3世代）。"0" と "5" は第2世代予約値で禁止。
VALID_TERMINATION_STATUS = {"1", "2", "3", "6", "7", "8", "9"}


def check_e9(d: dict) -> None:
    """E-9: OpenAI プロンプト記述が「外部 context による動的制御」を前提にしていないか検出
    OpenAI モジュールに渡されるのは params.module の直前モジュール出力（STT 結果）のみ。
    他の context（例: age, classification）はプロンプト実行時に参照できないため、
    step_details.openai_rules.mapping が「{他の context} に応じて〜」等の動的制御を求めていたら設計不整合。
    フロー構造で先に分岐するか、OpenAI 後の ContextMatchRouter で組み合わせ検証する設計に director が直す必要がある。
    """
    # 各 hearing_item が書き込む context 名と、その順序（scenario_flow 内の位置）を把握
    ctx_names = {
        c.get("context_name", "")
        for c in _safe_list(d, "context_fields")
        if isinstance(c, dict)
    }
    # 動的制御を示唆するキーワードパターン
    #   「age の値に応じて〜」「age が小児の場合〜」「classification によって〜」等
    dynamic_keywords = ["に応じて", "に従って", "によって", "の値で", "の場合は", "ごとに", "を参照して"]

    for sd in _safe_list(d, "step_details"):
        if not isinstance(sd, dict):
            continue
        step_name = sd.get("step_name", "?")
        save_to_here = sd.get("save_to", "")  # このステップ自身が書き込む context
        rules = sd.get("openai_rules") or {}
        mappings = _safe_list(rules, "mapping")

        for m in mappings:
            if not isinstance(m, dict):
                continue
            input_desc = str(m.get("input", ""))
            output_desc = str(m.get("output", ""))
            combined = input_desc + " " + output_desc

            # 他の context 名が mapping 記述に含まれているか
            referenced_ctx = [
                c for c in ctx_names
                if c and c != save_to_here and c in combined
            ]
            if not referenced_ctx:
                continue

            # 動的制御キーワードを伴っているか
            if any(kw in combined for kw in dynamic_keywords):
                _add("CRITICAL", "E-9",
                     f"step_details '{step_name}' の mapping が外部 context "
                     f"{referenced_ctx} に応じた動的制御を求めている "
                     f"（'{input_desc[:60]}' → '{output_desc[:40]}'）。"
                     f"OpenAI モジュールには直前の STT 出力しか渡らないため実行時に効かない。"
                     f"フロー構造で先に分岐する（例: context で ContextMatchRouter 分岐 → 各ルートに専用 OpenAI）か、"
                     f"OpenAI 後にもう 1 段 ContextMatchRouter で組み合わせ検証する設計に直すこと")


def check_e8(d: dict) -> None:
    """E-8: termination_patterns の status が第3世代許可値であること
    禁止: '0' / '5'（第2世代予約）。許可: 1, 2, 3, 6, 7, 8, 9
    Gen2 移管時に migration note の status をそのまま転記してしまう典型的バグの早期検出。
    """
    # Gen2 の 0/5 → Gen3 の 2 に正規化するのが標準対応。
    # その他の禁止値（future-proof）は同じく 2 にクランプ（代表案内扱い）。
    gen2_legacy = {"0", "5"}
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        status = str(tp.get("status", "")).strip()
        if not status:
            continue
        if status not in VALID_TERMINATION_STATUS:
            hint = "Gen2 legacy を '2' に置換" if status in gen2_legacy else "不明値を '2' にクランプ"
            _add("CRITICAL", "E-8",
                 f"termination_patterns '{tp.get('name', '?')}' の status='{status}' は第3世代では使用禁止 "
                 f"（許可: {sorted(VALID_TERMINATION_STATUS)}）。auto fix: {hint}",
                 fix_category="auto",
                 fix_action={
                     "op": "replace_all",
                     "pattern": rf'(\bstatus\s*:\s*)["\']?{re.escape(status)}["\']?(?=\s|$)',
                     "replacement": r'\1"2"',
                 })


def check_e6(d: dict) -> None:
    """E-6: 非通知パターンにアナウンス文言が定義されている（tts_announcement または tts_modules）"""
    # termination_patterns 内の非通知パターンの tts_announcement を確認
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        name = str(tp.get("name", ""))
        condition = str(tp.get("condition", ""))
        if "非通知" in name or "非通知" in condition:
            announcement = str(tp.get("tts_announcement", "")).strip()
            if announcement:
                return
    # tts_modules に非通知用モジュールがあるか確認
    for tm in _safe_list(d, "tts_modules"):
        if not isinstance(tm, dict):
            continue
        module_name = str(tm.get("module_name", ""))
        if "非通知" in module_name:
            return
    _add("CRITICAL", "E-6",
         "非通知パターンのアナウンス文言が未定義（termination_patterns.tts_announcement も tts_modules も空）")


def check_e7(d: dict) -> None:
    """E-7: 廃止（2026-07-09）。時間外 TTS は acceptance_times モジュール内で再生されるため終話チェーンへの定義は不要。"""
    pass


# ──────────────────────────────────────────────
# I-6: DTMF notes チェック
# ──────────────────────────────────────────────

def check_i6(d: dict) -> None:
    """I-6: DTMF_AmiVoice の hearing_items に notes で DTMF 対応が記載されている
    サブフロー委譲項目（生年月日・電話番号・診察券番号等）はスキップ:
    DTMF処理はサブフロー側の設計書が担当するため、メインフロー側に対応表は不要。
    """
    subflow_targets = _get_subflow_targets(d)
    slot_names = _get_slot_delegated_names(d)
    for hi in _safe_list(d, "hearing_items"):
        if not isinstance(hi, dict):
            continue
        stt_type = str(hi.get("stt_type", ""))
        if stt_type != "DTMF_AmiVoice":
            continue
        name = hi.get("name", "?")
        # サブフロー委譲項目・slot インライン展開項目はスキップ
        # （DTMF処理はサブフロー側 spec / 認定済み slot 部品 = DOB Re-confirmation 内で定義）
        if (_is_subflow_delegated(name, subflow_targets)
                or _is_slot_delegated(name, slot_names)):
            continue
        notes = str(hi.get("notes", ""))
        if not re.search(r"DTMF", notes, re.IGNORECASE):
            _add("CRITICAL", "I-6",
                 f"hearing_items '{name}' は stt_type=DTMF_AmiVoice だが "
                 f"notes に DTMF 対応表が記載されていない")


# type: slot（および dob/phone/patient_name/card_number ファーストクラスエイリアス）の
# slot 値 → 主要TTSモジュール名の解決規則。scripts/gen_properties.py の
# resolve_slot_tts_defaults() と同期させること（単一の命名規則を二重管理しないよう
# 将来的に共有モジュール化を検討可）。
_SLOT_KIND_BY_TYPE = {
    "dob": "date_of_birth", "phone": "phone",
    "patient_name": "patient_name", "card_number": "card_number",
}


def _slot_tts_module_name(slot_kind: str, step: str) -> str:
    """slot 種別 + step 名から、properties で文言解決が必要な主要TTSモジュール名を返す。
    phone のみ着信分類が入口のため、実際にTTSが必要なのは連絡先聴取モジュール。"""
    return f"聴取_{step}_連絡先" if slot_kind == "phone" else step


def check_i7(d: dict) -> None:
    """I-7: 個人情報4種（slot: patient_name/date_of_birth/phone/card_number）の主要TTSに
    施設固有の文言（tts_modules または step_details）が定義されているか確認。

    scaffold_generator.py の build_tts() はこれらのモジュールで params.prompt を
    空欄のまま出力する（TTS発話文言はプロパティ側で定義する前提・CLAUDE.md）。
    未定義でも gen_properties.py の resolve_slot_tts_defaults() が汎用デフォルト文言で
    救済するため CRITICAL にはしない（パイプラインは止まらない）が、
    施設ごとの呼称・敬語レベルに合わせた文言か人間が確認すべき事項として WARNING で可視化する。
    """
    tts_module_names = {
        tm.get("module_name", "") for tm in _safe_list(d, "tts_modules")
        if isinstance(tm, dict) and (tm.get("announcement") or tm.get("text"))
    }
    step_detail_names = {
        sd.get("step_name", "") for sd in _safe_list(d, "step_details")
        if isinstance(sd, dict) and sd.get("tts_announcement")
    }
    covered = tts_module_names | step_detail_names

    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict):
            continue
        btype = blk.get("type", "")
        step = blk.get("step", "")
        if not step:
            continue
        slot_kind = blk.get("slot", "") if btype == "slot" else _SLOT_KIND_BY_TYPE.get(btype, "")
        if slot_kind not in ("patient_name", "date_of_birth", "phone", "card_number"):
            continue
        module_name = _slot_tts_module_name(slot_kind, step)
        if module_name not in covered:
            _add("WARNING", "I-7",
                 f"個人情報聴取 '{step}'（slot: {slot_kind}）の主要TTS '{module_name}' に "
                 f"施設固有の文言（tts_modules または step_details）が定義されていません。"
                 f"gen_properties.py が汎用デフォルト文言で自動補完しますが、"
                 f"施設の呼称・敬語レベルに合わせた文言か確認してください")


# ──────────────────────────────────────────────
# M-2: 技術用語チェック
# ──────────────────────────────────────────────

_FORBIDDEN_TERMS = ["DTMF", "STT", "コンテキスト", "saveContext", "OpenAI", "API"]


def check_m2(d: dict) -> None:
    """M-2: TTS文言に技術用語が含まれていない"""
    # tts_modules の announcement をチェック
    for tm in _safe_list(d, "tts_modules"):
        if not isinstance(tm, dict):
            continue
        announcement = str(tm.get("announcement", ""))
        if not announcement or announcement == "TODO_要確認":
            continue
        for term in _FORBIDDEN_TERMS:
            if term in announcement:
                _add("CRITICAL", "M-2",
                     f"tts_modules '{tm.get('module_name', '?')}' の announcement に "
                     f"技術用語 '{term}' が含まれている（患者に見えてはいけない）")
    # step_details の tts_announcement をチェック
    for sd in _safe_list(d, "step_details"):
        if not isinstance(sd, dict):
            continue
        announcement = str(sd.get("tts_announcement", ""))
        if not announcement or announcement == "TODO_要確認":
            continue
        for term in _FORBIDDEN_TERMS:
            if term in announcement:
                _add("CRITICAL", "M-2",
                     f"step_details '{sd.get('step_name', '?')}' の tts_announcement に "
                     f"技術用語 '{term}' が含まれている（患者に見えてはいけない）")
    # termination_patterns の tts_announcement をチェック
    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        announcement = str(tp.get("tts_announcement", ""))
        if not announcement or announcement == "TODO_要確認":
            continue
        for term in _FORBIDDEN_TERMS:
            if term in announcement:
                _add("CRITICAL", "M-2",
                     f"termination_patterns '{tp.get('name', '?')}' の tts_announcement に "
                     f"技術用語 '{term}' が含まれている（患者に見えてはいけない）")


# ──────────────────────────────────────────────
# L-3: smsFlag 競合チェック
# ──────────────────────────────────────────────

def check_l3(d: dict) -> None:
    """L-3: sms_flag_routing.patterns で同一 condition に異なる sms_flag が割り当てられていない"""
    sfr = d.get("sms_flag_routing") or {}
    patterns = _safe_list(sfr, "patterns")
    if not patterns:
        return
    condition_to_flags: dict[str, set] = {}
    for pat in patterns:
        if not isinstance(pat, dict):
            continue
        condition = str(pat.get("condition", "")).strip()
        sms_flag = str(pat.get("sms_flag", "")).strip()
        if not condition or not sms_flag:
            continue
        if condition not in condition_to_flags:
            condition_to_flags[condition] = set()
        condition_to_flags[condition].add(sms_flag)
    for condition, flags in condition_to_flags.items():
        if len(flags) > 1:
            _add("CRITICAL", "L-3",
                 f"sms_flag_routing.patterns で condition='{condition}' に "
                 f"異なる sms_flag が割り当てられている: {sorted(flags)}")


def check_i4(d: dict) -> None:
    """I-4: フロー図のステップが step_details でカバーされているか"""
    step_names = {s.get("step_name", "") for s in _safe_list(d, "step_details") if s}
    hearing_names = {h.get("name", "") for h in _safe_list(d, "hearing_items") if h}
    known_names = step_names | hearing_names
    for fd in _safe_list(d, "flow_diagrams"):
        if not fd:
            continue
        diagram = fd.get("diagram", "")
        if not diagram:
            continue
        # フロー図から聴取ステップを抽出: xxx(STT), xxx(OpenAI), xxx(DTMF) パターン
        step_refs = re.findall(r'(\S+?)[\(（](?:STT|OpenAI|DTMF|聴取)', diagram)
        for ref in step_refs:
            ref_clean = ref.strip("→├└─ ")
            if ref_clean and ref_clean not in known_names:
                _add("WARNING", "I-4",
                     f"フロー図に '{ref_clean}' があるが step_details/hearing_items に未定義")


def check_i5(d: dict) -> None:
    """I-5: 複合発話パターンがないか（第3世代は1発話1意図）"""
    # 複合発話を示すパターン: 「AしてB」「AかつB」「AとBも」「AおよびB」
    compound_re = re.compile(r'して.{2,}も|かつ|および|だけでなく|それと|ついでに')
    for sd in _safe_list(d, "step_details"):
        if not sd:
            continue
        step_name = sd.get("step_name", "")
        mapping = sd.get("openai_rules", {}) or {}
        for m in _safe_list(mapping, "mapping"):
            if not m:
                continue
            input_val = str(m.get("input", ""))
            if compound_re.search(input_val):
                _add("WARNING", "I-5",
                     f"step '{step_name}' のmapping入力 '{input_val[:40]}' に複合発話パターンの可能性 "
                     "-- 第3世代は1発話1意図。分岐で対応する")


def check_e11(d: dict) -> None:
    """E-11: opening ブロックの直後に 冒頭_アナウンス (announcement) が必須

    冒頭ブロックは論理的に「非通知拒否 + 時間外設定 + 冒頭アナウンス」の複合単位。
    冒頭アナウンス TTS が欠落すると、Brekeke が着信直後に挨拶発話なしで
    ヒアリングやサブフローに遷移して UX が崩壊する。

    チェック内容:
    - scenario_flow[0] が type:opening であれば、その next が指す step は
      type:announcement で、step 名に "冒頭" / "アナウンス" / "挨拶" のいずれかを含むこと
    - scaffold_generator 側に safety net があるため通常は自動補完されるが、
      director の yaml 段階で明示されるのが望ましいため本チェックでも警告

    不適合時は WARNING (scaffold で自動補完されるため FAIL ではないが、
    director に修正を促す)
    """
    scenario_flow = _safe_list(d, "scenario_flow")
    if not scenario_flow:
        return
    opening = scenario_flow[0] if isinstance(scenario_flow[0], dict) else None
    if not opening or opening.get("type") != "opening":
        return
    next_step = str(opening.get("next", "") or "")
    if not next_step:
        _add("CRITICAL", "E-11",
             "opening.next が未設定。冒頭_アナウンス announcement ブロックを挟むこと")
        return
    following = next((b for b in scenario_flow
                      if isinstance(b, dict) and b.get("step") == next_step), None)
    if not following:
        _add("CRITICAL", "E-11",
             f"opening.next='{next_step}' が scenario_flow 内に見つかりません")
        return
    if following.get("type") != "announcement":
        _add("WARNING", "E-11",
             f"opening の直後が announcement ブロックではありません "
             f"(現在: type={following.get('type')}, step={following.get('step')})。"
             f"冒頭_アナウンス announcement を挟むこと。"
             f"scaffold_generator で自動補完されるが、director yaml で明示する方が望ましい")
        return
    step_name = str(following.get("step", "") or "")
    if not any(kw in step_name for kw in ("冒頭", "アナウンス", "挨拶")):
        _add("WARNING", "E-11",
             f"opening 直後 announcement の step 名が '冒頭' / 'アナウンス' / '挨拶' を"
             f"含みません (現在: '{step_name}')。命名規約として 冒頭_アナウンス を推奨")


def check_e12(d: dict) -> None:
    """E-12: 氏名聴取の分岐ルール検証（PatientName サブフローは 1 枠のみ）

    ルール（docs/brekeke/モジュール選定ガイド_v2.md §3.1.1 準拠）:
    - 患者氏名があれば PatientName サブフローで聴取。他の氏名聴取項目
      （入電者氏名・受診者氏名・担当者氏名等）は hearing ブロックで対応する
    - 患者氏名がなければ、入電者氏名 / 受診者氏名を PatientName サブフローに充当
    - save_to: patientName の hearing ブロックはインライン配置禁止（必ずサブフロー経由）

    チェック内容:
    (a) flow_structure.subflows[] に「氏名聴取」を含む subflow が 2 本以上登録されていれば CRITICAL
    (b) scenario_flow に type:hearing かつ save_to:patientName のブロックがあれば CRITICAL

    slot 例外（フラット化フェーズ2）: 患者氏名を type:slot / slot:patient_name で表すのは
    認定済み決定論部品によるサンクションされたインライン展開であり、サブフロー必須ルールの対象外。
    (b) は type:hearing のみを見るため slot ブロックは元から発火しない（=明示的に免除）。

    memory: feedback_patientname_subflow_allocation
    """
    flow_structure = d.get("flow_structure") or {}
    subflows = _safe_list(flow_structure, "subflows") or []

    # (a) 氏名聴取系サブフローの多重登録
    name_like = []
    for sf in subflows:
        if not isinstance(sf, dict):
            continue
        sf_name = str(sf.get("flowname") or sf.get("name") or sf.get("target") or "")
        if "氏名聴取" in sf_name:
            name_like.append(sf_name)
    if len(name_like) >= 2:
        _add("CRITICAL", "E-12",
             f"氏名聴取系サブフローが複数登録されています ({name_like})。"
             f"PatientName サブフローは 1 枠のみ。"
             f"入電者氏名・受診者氏名・担当者氏名等は hearing ブロックで対応してください "
             f"(モジュール選定ガイド §3.1.1)")

    # (b) save_to: patientName の hearing ブロックがインライン配置されていないか
    scenario_flow = _safe_list(d, "scenario_flow")
    for block in scenario_flow:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "hearing":
            continue
        save_to = str(block.get("save_to", "") or "")
        if save_to == "patientName":
            step = str(block.get("step", "") or "")
            _add("CRITICAL", "E-12",
                 f"step '{step}' は save_to: patientName の hearing ブロックですが、"
                 f"インライン配置されています。患者氏名は必ずサブフロー経由で聴取してください "
                 f"(type: subflow + flowname: '{{group_name}}$氏名聴取'。日付は group_name 末尾に付け、サブフロー名には付けない)")


def check_e13(d: dict) -> None:
    """E-13: Script ブロックはカレンダー計算専用

    ルール（docs/brekeke/モジュール選定ガイド_v2.md §3.8 準拠）:
    - Script は営業日・祝日・施設固有休館日などカレンダーデータを使う計算のみに限る
    - 年齢分岐・多段分岐・日付判定・文字列一致等は OpenAI + ContextMatchRouter で組む
    - `script_template` に既存テンプレート (future_date / day_of_week / business_hours /
      business_hour_classifier / current_appointment_date / phone_type / condition_group /
      shinjuku_kenshin_date_gate / desired_date_precompute) を明示指定するか、
      `custom` の場合は `notes` にカレンダー必須の理由（「営業日」「祝日」「休館日」のいずれか）を明記すること

    チェック内容:
    (a) type: script ブロックで script_template 未指定 → CRITICAL
    (b) script_template: custom で notes にカレンダー必須キーワード無し → CRITICAL

    過去施設で既に Script に逃げたブロックがある場合、このルールで作り直し時に
    自然に矯正される（director が OpenAI + CMR に組み直す）。

    例外（フラット化フェーズ2）: 認定分類器（checkup_intent/course/menu_classifier・yes_no_classifier）は
    決定論 Script で分類するのが正であり ALLOWED_TEMPLATES に含める（カレンダー専用ルールの対象外）。

    memory: project_scaffold_bugs_backlog (#10 Script モジュール中身書き手未定義)
    """
    # ALLOWED_TEMPLATES は script_templates/ 配下の *.js から動的取得（新規テンプレ追加時に自動対応）
    _TPL_DIR = Path(__file__).resolve().parent.parent / "docs" / "brekeke" / "script_templates"
    ALLOWED_TEMPLATES = {"custom"}
    if _TPL_DIR.exists():
        ALLOWED_TEMPLATES |= {p.stem for p in _TPL_DIR.glob("*.js")}
    # 認定分類器（modules/ の認定正本を build_script が直接読む。script_templates/ には置かない）。
    # scaffold_generator.CERTIFIED_MODULE_TEMPLATES と一致させること（フラット化フェーズ2）。
    ALLOWED_TEMPLATES |= {
        "checkup_intent_classifier", "checkup_course_classifier",
        "checkup_menu_classifier", "yes_no_classifier",
        "reservation_date_classifier",
    }
    CALENDAR_KEYWORDS = ("営業日", "祝日", "休館日")

    scenario_flow = _safe_list(d, "scenario_flow")
    for block in scenario_flow:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "script":
            continue
        step = str(block.get("step", "") or "(unnamed)")
        template = block.get("script_template")

        # (a) script_template 未指定
        if not template:
            _add("CRITICAL", "E-13",
                 f"script ブロック '{step}' に script_template が指定されていません。"
                 f"Script はカレンダー計算専用です。年齢分岐・多段分岐・日付判定等は "
                 f"OpenAI + ContextMatchRouter で組み直してください。"
                 f"カレンダー計算が必要な場合は script_template に既存テンプレート名 "
                 f"(future_date/day_of_week/business_hours/business_hour_classifier/"
                 f"current_appointment_date/phone_type/condition_group 等) を"
                 f"指定、もしくは custom + notes にカレンダー必須の理由を明記してください "
                 f"(モジュール選定ガイド §3.8)")
            continue

        template_str = str(template).strip()
        if template_str not in ALLOWED_TEMPLATES:
            _add("CRITICAL", "E-13",
                 f"script ブロック '{step}' の script_template='{template_str}' は "
                 f"未知のテンプレートです。許容値: " + "/".join(sorted(ALLOWED_TEMPLATES)) +
                 f" (モジュール選定ガイド §3.8)")
            continue

        # (b) custom で notes にカレンダーキーワード無し
        if template_str == "custom":
            notes = str(block.get("notes", "") or "")
            if not any(kw in notes for kw in CALENDAR_KEYWORDS):
                _add("CRITICAL", "E-13",
                     f"script ブロック '{step}' は script_template: custom ですが、"
                     f"notes にカレンダー必須の理由が書かれていません。"
                     f"Script は営業日・祝日・休館日などカレンダー計算にのみ許可されます。"
                     f"notes に「営業日」「祝日」「休館日」のいずれかを含めて理由を明記してください。"
                     f"それ以外の分岐は OpenAI + ContextMatchRouter で組み直してください "
                     f"(モジュール選定ガイド §3.8)")


def check_e14(d: dict) -> None:
    """E-14: jump 参照の URL エンコード後文字数が Brekeke 制限 255 以内

    Brekeke の Jump to Flow は flowname を URL エンコードしてパスに埋め込むため、
    URL エンコード後 255 文字を超えると本番投入時にエラーになる。
    式: `drjoy^ + {group_name} + $ + {最長サブフロー名}` の URL エンコード長 ≤ 255
    （日付サフィックス `_YYYYMMDD` は group_name 側に含まれる。E-16 / naming_convention.md）
    すなわち `URL(group_name) + URL(最長サブフロー名) ≤ 239`

    検出: 沖縄県立南部医療センター・こども医療センター_地域連携 (2026-04-23)
    group_name 23 文字（中黒含む）→ URL 207 文字。最長サブフロー「生年月日聴取」「電話番号聴取」
    で jump 参照が 272 文字となり制限超過。

    memory: feedback_group_name_url_length_limit
    """
    basic = d.get("basic_info") or {}
    group_name = str(basic.get("group_name", "") or "").strip()
    if not group_name:
        return

    flow_structure = d.get("flow_structure") or {}
    subflows = _safe_list(flow_structure, "subflows") or []

    longest_target = ""
    longest_target_url = 0
    for sf in subflows:
        if not isinstance(sf, dict):
            continue
        target = str(sf.get("target") or "").strip()
        if not target:
            continue
        url_len = len(urllib.parse.quote(target, safe=""))
        if url_len > longest_target_url:
            longest_target = target
            longest_target_url = url_len

    if not longest_target:
        return  # サブフロー無しならチェック不要

    # drjoy^ (6) + group_name + $ (1) + target を URL エンコード。
    # 日付サフィックス _YYYYMMDD は group_name 側に含まれる前提（E-16）。
    # group_name に日付が未付与の段階（E-16 未解消）でも長さを過小評価しないよう、
    # 日付分 (_20260101 = 9 文字) を安全側に補う。
    effective_group = group_name if re.search(r"_\d{8}$", group_name) else f"{group_name}_20260101"
    sample = f"drjoy^{effective_group}${longest_target}"
    encoded_len = len(urllib.parse.quote(sample, safe=""))

    if encoded_len > 255:
        excess = encoded_len - 255
        group_url = len(urllib.parse.quote(group_name, safe=""))
        _add("CRITICAL", "E-14",
             f"group_name '{group_name}' (URL {group_url}文字) と最長サブフロー "
             f"'{longest_target}' (URL {longest_target_url}文字) で構成される jump 参照が "
             f"URL エンコード後 {encoded_len} 文字となり、Brekeke の 255 文字制限を {excess} 文字超過します。"
             f" group_name を短縮してください（目安: 漢字 19 文字以内、中黒「・」も 9 バイト消費）。"
             f"元資料に長い正式名があっても通称・短縮名を採用すること "
             f"(モジュール選定ガイド §3.8 / director.md の URL 制限ルール参照)")


def check_e15(d: dict) -> None:
    """E-15: TTS テキストに Brekeke 非対応の偽プレースホルダーが含まれていないこと

    Brekeke が TTS prompt 内で解釈する変数構文は **`<% 変数名 %>`** のみ。
    director が customer_doc から `<{VAR}のM月D日>` `＜{VAR}の表示形式＞` のような
    旧 OpenAI Assistant 仕様の表示テンプレートを書き写すと、Brekeke は処理せず
    Google TTS がリテラルとして読み上げてしまう。

    検出対象（CRITICAL）:
      - `<{...}` (半角山括弧 + 中括弧)
      - `＜{...` (全角山括弧 + 中括弧)
      - `${...}` (一部 customer_doc に出現する別形式)

    除外: `<% ... %>` は Brekeke 公式の変数構文のため許容。

    対処: TTS で動的値を埋め込む場合は `<% context_name %>` 形式に書き換え、
    対応する context を script モジュール側で setContext しておく。

    検出: 新宿健診プラザ (2026-04-27) で 13 箇所の `<{DESIRED_DATE}のM月D日>` 等
    を確認。Google TTS でリテラル読み上げ → 本番動作不能。
    """
    # `<{` または `＜{` または `${` で始まり、中括弧と閉じ括弧を含む
    # 偽プレースホルダーを検出。`<% ... %>` は除外。
    fake_re = re.compile(r"[<＜\$]\s*\{[^}]+\}[^<＞>]*[>＞]")

    def _scan(name: str, text: str, where: str) -> None:
        if not isinstance(text, str) or not text:
            return
        # Brekeke 公式の <% ... %> は除外
        cleaned = re.sub(r"<%[^%]*%>", "", text)
        for m in fake_re.finditer(cleaned):
            _add(
                "CRITICAL", "E-15",
                f"{where} '{name}' の TTS テキスト内に Brekeke 非対応の偽プレースホルダー "
                f"'{m.group(0)}' が含まれています。Brekeke + Google TTS は処理せず "
                f"リテラルとして読み上げます。動的値を埋め込む場合は <% context_name %> "
                f"形式に書き換え、対応する context を script モジュール側で saveContext "
                f"してください（モジュール選定ガイド §3.8 / director.md 参照）。"
            )

    for tm in d.get("tts_modules", []) or []:
        if not isinstance(tm, dict):
            continue
        name = tm.get("module_name", "")
        text = tm.get("announcement", "") or tm.get("text", "")
        _scan(name, text, "tts_modules")

    for sd in d.get("step_details", []) or []:
        if not isinstance(sd, dict):
            continue
        name = sd.get("step_name", "")
        text = sd.get("tts_announcement", "")
        _scan(name, text, "step_details")


def check_e16(d: dict) -> None:
    """E-16: group_name は末尾に日付サフィックス `_YYYYMMDD`（作業日）を持つこと

    命名規則（2026-06-04 確定, docs/brekeke/naming_convention.md）:
    - 日付サフィックスは **グループ名** に付ける（フロー名・サブフロー名には付けない）
    - コピー作成・修正のたびに新しい作業日でグループを版管理し、サブフローは
      全てまとめて新グループ配下へ再エクスポートする → jump 参照が確実に解決する

    旧方式（日付をサブフロー名に付与）は director の flowname 参照（日付なし）と
    copy_subflows のサブフロー JSON 名（日付あり）が食い違い、broken_ref を誘発した。
    日付を group_name 1 箇所に集約することで、全参照が group_name verbatim で揃う。
    """
    bi = d.get("basic_info") or {}
    group_name = str(bi.get("group_name") or "").strip()
    if not group_name:
        return  # 空は T-2 が CRITICAL 検出済み
    if not re.search(r"_\d{8}$", group_name):
        _add("CRITICAL", "E-16",
             f"basic_info.group_name='{group_name}' に日付サフィックス '_YYYYMMDD'（作業日）が "
             f"ありません。コピー作成・修正時はグループ名末尾に作業日を付けて版管理してください "
             f"(例: '{group_name}_20260604')。フロー名・サブフロー名には日付を付けないこと "
             f"(naming_convention.md)。flow_name / 全 flowname 参照も同じ日付付きグループ名に揃える")


def check_e10(d: dict) -> None:
    """E-10: termination_patterns の全終話が scenario_flow から到達可能であること

    scaffold が自動接続する標準パターン（非通知・時間外・聴取失敗）以外の全終話は、
    scenario_flow のいずれかの step の conditions[].next に明示されている必要がある。
    CustomerDocs にリトライ失敗時・特定条件時の接続経路が記載されている場合、
    director は必ず scenario_flow の conditions に next='{END_xxx}' を追記すること。
    """
    scenario_flow = _safe_list(d, "scenario_flow")
    if not scenario_flow:
        return  # scenario_flow 未定義は別チェックで検出

    # scenario_flow の全 next 値を収集
    next_values: set[str] = set()
    for step in scenario_flow:
        if not isinstance(step, dict):
            continue
        if step.get("next"):
            next_values.add(str(step["next"]))
        for cond in _safe_list(step, "conditions"):
            if isinstance(cond, dict) and cond.get("next"):
                next_values.add(str(cond["next"]))
        # Pattern C: dtmf_options[].next
        for opt in _safe_list(step, "dtmf_options"):
            if isinstance(opt, dict) and opt.get("next"):
                next_values.add(str(opt["next"]))
        # Pattern C: cmr_chain.reference_modules[].next + default_next
        if step.get("type") == "cmr_chain":
            for ref in _safe_list(step, "reference_modules"):
                if isinstance(ref, dict) and ref.get("next"):
                    next_values.add(str(ref["next"]))
            if step.get("default_next"):
                next_values.add(str(step["default_next"]))

    for tp in _safe_list(d, "termination_patterns"):
        if not isinstance(tp, dict):
            continue
        name = str(tp.get("name", ""))
        condition = str(tp.get("condition", ""))
        if not name:
            continue

        # scaffold が自動接続する標準パターンはスキップ
        is_auto = (
            "非通知" in name or "非通知" in condition or
            "時間外" in name or "時間外" in condition or
            "聴取失敗" in name  # scaffold が全 retry.false から自動接続する主要パターン
        )
        if is_auto:
            continue

        # scenario_flow の conditions に routing が明示されているか確認
        if name not in next_values:
            _add("CRITICAL", "E-10",
                 f"termination_patterns '{name}' が scenario_flow のいずれの step の "
                 f"conditions/next にも登録されていない。"
                 f"CustomerDocs からリトライ失敗時等の到達経路を確認し、"
                 f"scenario_flow の該当 step の conditions に next='{name}' を追記すること。"
                 f"（scaffold は自動接続できないため director が明示する必要がある）")


# ──────────────────────────────────────────────
# F-* : scenario_flow ブロック構造チェック
# ──────────────────────────────────────────────

KNOWN_BLOCK_TYPES = {
    "opening", "announcement", "hearing", "subflow",
    "context_match_router", "script",
    "call_transfer", "termination", "augment",
    # 電話帳マッチ系 (2026-05-11 追加)
    "incoming_category_classifier", "phone2name",
    # Pattern C: DTMF 分離 関連 (2026-05-21 追加)
    "cmr_chain",
    # 宣言的個人情報スロットの決定論インライン展開 (2026-06-17 追加・フラット化フェーズ2)
    "slot",
    # 診療科 Custom Module (2026-06-23 追加・プロパティ駆動・同義語辞書内蔵)
    "clinical_department_classifier",
    # ファーストクラス slot 型エイリアス (2026-07-09 追加)
    "dob", "phone", "patient_name",
    # 用件判定スクリプト / 電話種別分岐 / 診療科スクリプト (2026-07-09 追加)
    "intent", "phone_branch",
    "clinical_department", "clinical_department_normalize",
    # 自由発話 / FAQ照合 (2026-07-09 追加)
    "free_text", "faq",
    # 診察券番号 正規化スクリプト (2026-07-09 追加)
    "card_number",
    # WebRTC 事前入力フォーム対応: null-check ブロック型 (2026-07-10 追加・BLOCKER B-3)
    "null_check",
    # 聴取なしで「N診療日後」を自動計算する部品 (2026-07-17 追加・P6未受入)
    "clinic_day_default",
}

AUGMENT_PATTERNS = {"new_module", "none_applicable", "director_handled"}

BLOCK_REQUIRED_FIELDS = {
    "hearing": ["output_format"],
    "subflow": ["flowname"],
    "context_match_router": ["reference_module"],
    "termination": ["termination_ref"],
    "incoming_category_classifier": ["conditions"],
    "phone2name": ["found_template"],
    "cmr_chain": ["reference_modules", "default_next"],
    "slot": ["slot"],
    "clinical_department_classifier": ["reference_module", "conditions"],
    # ファーストクラス slot エイリアス: slot フィールド不要（型名が識別子）
    "dob": [],
    "phone": [],
    "patient_name": [],
    # 新規ブロック型
    "intent": ["options", "save_to"],
    "phone_branch": ["conditions"],
    "clinical_department": ["departments"],
    "clinical_department_normalize": ["departments"],
    "free_text": ["save_to"],
    "faq": ["conditions"],
    "card_number": ["save_to"],
    "null_check": ["key", "true_next", "false_next"],
}

VALID_INPUT_METHODS = {"voice_only", "dtmf_split"}


def check_f1(d: dict) -> None:
    """F-1: scenario_flow の全 step が start (scenario_flow[0]) から到達可能。
    ただし scaffold が自動接続する標準 termination（非通知/時間外/聴取失敗）は
    scenario_flow.next に明記されなくても到達扱いとする（E-10 と同じ扱い）。
    """
    sf = _safe_list(d, "scenario_flow")
    step_map = {s.get("step"): s for s in sf if isinstance(s, dict) and s.get("step")}
    if not step_map:
        return
    start = sf[0].get("step") if isinstance(sf[0], dict) else None
    if not start:
        return
    reachable: set[str] = set()
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur in reachable or cur not in step_map:
            continue
        reachable.add(cur)
        blk = step_map[cur]
        nxt = blk.get("next")
        if nxt:
            stack.append(nxt)
        for c in _safe_list(blk, "conditions"):
            if isinstance(c, dict) and c.get("next"):
                stack.append(c["next"])
        # Pattern C: dtmf_options[].next を follow
        for opt in _safe_list(blk, "dtmf_options"):
            if isinstance(opt, dict) and opt.get("next"):
                stack.append(opt["next"])
        # Pattern C: cmr_chain.reference_modules[].next + default_next を follow
        if blk.get("type") == "cmr_chain":
            for ref in _safe_list(blk, "reference_modules"):
                if isinstance(ref, dict) and ref.get("next"):
                    stack.append(ref["next"])
            if blk.get("default_next"):
                stack.append(blk["default_next"])
        # null_check: true_next / false_next を follow (WebRTC 事前入力フォーム対応・B-3)
        if blk.get("type") == "null_check":
            if blk.get("true_next"):
                stack.append(blk["true_next"])
            if blk.get("false_next"):
                stack.append(blk["false_next"])
    for name, blk in step_map.items():
        if name in reachable:
            continue
        # scaffold 自動接続 termination (非通知/時間外/聴取失敗) は unreachable でも OK
        if blk.get("type") == "termination":
            ref = str(blk.get("termination_ref", name))
            if any(k in ref for k in ("非通知", "時間外", "聴取失敗")):
                continue
        _add("CRITICAL", "F-1",
             f"scenario_flow step '{name}' が start='{start}' から到達不能。"
             f"next / conditions.next の接続を見直すこと")


def check_f2(d: dict) -> None:
    """F-2: next / conditions.next / dtmf_options.next / cmr_chain.* の遷移先 step が scenario_flow に実在する"""
    sf = _safe_list(d, "scenario_flow")
    step_names = {s.get("step") for s in sf if isinstance(s, dict) and s.get("step")}
    # フラット化: 認定分類器 script の NO_RESULT は hearing の自動生成リトライカウンタ
    # 「リトライ_<hearing step>」へ落とす（resolve がパススルー・build_retry が必ず生成）。
    # これは scenario_flow に明示されない自動モジュールなので有効遷移先として許容する。
    auto_retry_targets = {
        f"リトライ_{s.get('step')}"
        for s in sf
        if isinstance(s, dict) and s.get("type") == "hearing" and s.get("step")
    }
    valid_targets = step_names | auto_retry_targets
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        src = blk.get("step", "?")
        nxt = blk.get("next")
        if nxt and nxt not in valid_targets:
            _add("CRITICAL", "F-2",
                 f"step '{src}' の next='{nxt}' が scenario_flow に存在しない step を指している")
        for c in _safe_list(blk, "conditions"):
            if isinstance(c, dict):
                cn = c.get("next")
                if cn and cn not in valid_targets:
                    _add("CRITICAL", "F-2",
                         f"step '{src}' の conditions[match='{c.get('match','?')}'].next='{cn}' "
                         f"が scenario_flow に存在しない step を指している")
        # Pattern C: dtmf_options[].next の参照整合性
        for opt in _safe_list(blk, "dtmf_options"):
            if isinstance(opt, dict) and opt.get("action") != "replay":
                on = opt.get("next")
                if on and on not in step_names:
                    _add("CRITICAL", "F-2",
                         f"step '{src}' の dtmf_options[label='{opt.get('label','?')}'].next='{on}' "
                         f"が scenario_flow に存在しない step を指している")
        # Pattern C: cmr_chain.reference_modules[].next と default_next の参照整合性
        if blk.get("type") == "cmr_chain":
            for ref in _safe_list(blk, "reference_modules"):
                if isinstance(ref, dict):
                    rn = ref.get("next")
                    if rn and rn not in step_names:
                        _add("CRITICAL", "F-2",
                             f"step '{src}' (cmr_chain) の reference_modules[module='{ref.get('module','?')}'].next='{rn}' "
                             f"が scenario_flow に存在しない step を指している")
            dn = blk.get("default_next")
            if dn and dn not in step_names:
                _add("CRITICAL", "F-2",
                     f"step '{src}' (cmr_chain) の default_next='{dn}' が scenario_flow に存在しない step を指している")
        # null_check: true_next / false_next の参照整合性 (WebRTC 事前入力フォーム対応・B-3)
        if blk.get("type") == "null_check":
            tn = blk.get("true_next")
            if tn and tn not in valid_targets:
                _add("CRITICAL", "F-2",
                     f"step '{src}' (null_check) の true_next='{tn}' が scenario_flow に存在しない step を指している")
            fn = blk.get("false_next")
            if fn and fn not in valid_targets:
                _add("CRITICAL", "F-2",
                     f"step '{src}' (null_check) の false_next='{fn}' が scenario_flow に存在しない step を指している")


def check_f3(d: dict) -> None:
    """F-3: ブロック型が既知型 + augment のいずれか。augment は WARNING で詳細報告"""
    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        step = blk.get("step", "?")
        btype = blk.get("type", "")
        if btype not in KNOWN_BLOCK_TYPES:
            _add("CRITICAL", "F-3",
                 f"step '{step}' の type='{btype}' が未知ブロック型。既知型 "
                 f"(opening/announcement/hearing/subflow/context_match_router/"
                 f"script/call_transfer/termination/"
                 f"incoming_category_classifier/phone2name/cmr_chain/slot/"
                 f"dob/phone/patient_name/intent/phone_branch/"
                 f"clinical_department/clinical_department_normalize/"
                 f"free_text/faq/clinical_department_classifier/null_check) "
                 f"または 'augment' のいずれかを使うこと")
            continue
        if btype == "augment":
            pattern = blk.get("augment_pattern", "")
            purpose = blk.get("augment_purpose", "")
            if pattern not in AUGMENT_PATTERNS:
                _add("CRITICAL", "F-3",
                     f"step '{step}' (type=augment) の augment_pattern='{pattern}' が不正。"
                     f"必須: new_module | none_applicable | director_handled")
            else:
                _add("WARNING", "F-3",
                     f"augment ブロック使用（レビュー対象）: step='{step}', "
                     f"pattern='{pattern}', purpose='{purpose}'. "
                     f"正式ブロック型への昇格 or 既存型への書き直しを検討すること")


def check_f4(d: dict) -> None:
    """F-4: scenario_flow の step 名が一意"""
    sf = _safe_list(d, "scenario_flow")
    seen: dict[str, int] = {}
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        name = blk.get("step", "")
        if not name:
            continue
        seen[name] = seen.get(name, 0) + 1
    for name, count in seen.items():
        if count > 1:
            _add("CRITICAL", "F-4",
                 f"step 名 '{name}' が scenario_flow 内で {count} 回重複。step 名は一意にすること")


def check_f6(d: dict) -> None:
    """F-6: ブロック型ごとの必須フィールド存在チェック"""
    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        step = blk.get("step", "?")
        btype = blk.get("type", "")
        required = BLOCK_REQUIRED_FIELDS.get(btype, [])
        # intent + engine:v2 + intent_spec: options は不要（spec の rules が label 集合を定義）
        if btype == "intent" and str(blk.get("engine", "")).lower() == "v2" \
                and isinstance(blk.get("intent_spec"), dict):
            required = [f for f in required if f != "options"]
        for field in required:
            if not blk.get(field):
                _add("CRITICAL", "F-6",
                     f"step '{step}' (type={btype}) の必須フィールド '{field}' が未設定")
        # slot ブロックの slot 値は対応済みスロット（scaffold が決定論インライン展開できるもの）に限る
        if btype == "slot":
            slot_val = str(blk.get("slot", "") or "")
            if slot_val and slot_val not in SLOT_SUPPORTED:
                _add("CRITICAL", "F-6",
                     f"step '{step}' (type=slot) の slot='{slot_val}' は未対応。"
                     f"対応 slot: {sorted(SLOT_SUPPORTED)}（scaffold_generator._build_slot と同期）。"
                     f"これ以外の聴取は hearing / subflow ブロックを使うこと")


# ──────────────────────────────────────────────
# D-* : Pattern C (DTMF 分離) 専用チェック
# 仕様: docs/specs/dtmf_split_pattern_c.md
# ──────────────────────────────────────────────

def check_d1(d: dict) -> None:
    """D-1: input_method 値が VALID_INPUT_METHODS のいずれか、dtmf_options との整合"""
    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") != "hearing":
            continue
        step = blk.get("step", "?")
        im = blk.get("input_method")
        if im is None:
            continue
        if im not in VALID_INPUT_METHODS:
            _add("CRITICAL", "D-1",
                 f"step '{step}' の input_method='{im}' が未定義値。許可: {sorted(VALID_INPUT_METHODS)}")
            continue
        if im == "dtmf_split":
            if not _safe_list(blk, "dtmf_options"):
                _add("CRITICAL", "D-1",
                     f"step '{step}' は input_method=dtmf_split だが dtmf_options が空")
            if blk.get("conditions"):
                _add("CRITICAL", "D-1",
                     f"step '{step}' は input_method=dtmf_split のため conditions は書けない（dtmf_options に統合してください）")


def check_d2(d: dict) -> None:
    """D-2: dtmf_options の DTMF 値重複チェック / replay の必須フィールド整合"""
    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        opts = _safe_list(blk, "dtmf_options")
        if not opts:
            continue
        step = blk.get("step", "?")
        seen_dtmf: dict = {}
        seen_label: dict = {}
        for opt in opts:
            if not isinstance(opt, dict):
                continue
            dval = str(opt.get("dtmf", "")).strip()
            label = str(opt.get("label", "")).strip()
            action = opt.get("action", "save")
            if not dval:
                _add("CRITICAL", "D-2",
                     f"step '{step}' dtmf_options に dtmf 値欠落のエントリあり: {opt!r}")
            if not label:
                _add("CRITICAL", "D-2",
                     f"step '{step}' dtmf_options に label 欠落のエントリあり: {opt!r}")
            if dval in seen_dtmf:
                _add("CRITICAL", "D-2",
                     f"step '{step}' dtmf_options で DTMF 値 '{dval}' が重複（既出: label='{seen_dtmf[dval]}'）")
            else:
                seen_dtmf[dval] = label
            if label and label in seen_label and action != "replay":
                # replay 以外で label 重複は禁止（OpenAI 発話路の分岐が壊れる）
                _add("CRITICAL", "D-2",
                     f"step '{step}' dtmf_options で label '{label}' が重複（DTMF='{dval}'）")
            elif label:
                seen_label[label] = dval
            if action == "save" and not opt.get("next"):
                _add("CRITICAL", "D-2",
                     f"step '{step}' dtmf_options[label='{label}'] の action=save には next が必要")
            if action not in ("save", "replay"):
                _add("CRITICAL", "D-2",
                     f"step '{step}' dtmf_options[label='{label}'] の action='{action}' が不正（save/replay のみ）")


def check_d3(d: dict) -> None:
    """D-3: dtmf_split hearing の save_to / stt_type 整合"""
    sf = _safe_list(d, "scenario_flow")
    hi = {h.get("name"): h for h in _safe_list(d, "hearing_items") if isinstance(h, dict)}
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") != "hearing":
            continue
        if blk.get("input_method") != "dtmf_split":
            continue
        step = blk.get("step", "?")
        h = hi.get(step)
        if not h:
            _add("WARNING", "D-3",
                 f"step '{step}' (dtmf_split) に対応する hearing_items エントリが見つからない（補完推奨）")
            continue
        if not h.get("save_to"):
            _add("CRITICAL", "D-3",
                 f"step '{step}' (dtmf_split) は hearing_items.save_to が必須（各 DTMF 値の保存先 context が決まらない）")
        stt = h.get("stt_type", "")
        if stt not in ("DTMF_AmiVoice", "DTMF_AmiVoice_STT"):
            _add("WARNING", "D-3",
                 f"step '{step}' (dtmf_split) の stt_type='{stt}' は DTMF_AmiVoice 推奨")


def check_d4(d: dict) -> None:
    """D-4: cmr_chain.reference_modules の整合（最低 1 個、命名は save_ プレフィックス推奨）"""
    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") != "cmr_chain":
            continue
        step = blk.get("step", "?")
        refs = _safe_list(blk, "reference_modules")
        if not refs:
            _add("CRITICAL", "D-4",
                 f"step '{step}' (cmr_chain) の reference_modules が空")
        for ref in refs:
            if not isinstance(ref, dict):
                continue
            mod = ref.get("module", "")
            if not mod:
                _add("CRITICAL", "D-4",
                     f"step '{step}' (cmr_chain) reference_modules に module 欠落: {ref!r}")
            elif not mod.startswith("save_"):
                _add("WARNING", "D-4",
                     f"step '{step}' (cmr_chain) reference_modules module='{mod}' は "
                     f"`save_` プレフィックスが推奨（Pattern C で生成される saveContext2DB 命名）")
            if not ref.get("next"):
                _add("CRITICAL", "D-4",
                     f"step '{step}' (cmr_chain) reference_modules[module='{mod}'] の next 欠落")
        if not blk.get("default_next"):
            _add("CRITICAL", "D-4",
                 f"step '{step}' (cmr_chain) default_next 欠落（catchall として必須）")


def check_f7a(d: dict) -> None:
    """F-7a: subflow ブロックの flowname が flow_structure.subflows に登録されている"""
    sf = _safe_list(d, "scenario_flow")
    flow_structure = d.get("flow_structure") or {}
    registered_names = {
        s.get("name", "") for s in _safe_list(flow_structure, "subflows")
        if isinstance(s, dict) and s.get("name")
    }
    if not registered_names:
        # subflows section 自体が空の場合は L-6 で別途検出されるのでスキップ
        return
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") != "subflow":
            continue
        step = blk.get("step", "?")
        flowname = blk.get("flowname", "")
        if not flowname:
            # F-6 で検出されるので skip
            continue
        if flowname not in registered_names:
            _add("CRITICAL", "F-7a",
                 f"subflow step '{step}' の flowname='{flowname}' が "
                 f"flow_structure.subflows に未登録。subflows セクションに追加するか、"
                 f"scenario_flow 側で既存登録名に修正すること")


def check_e17(d: dict) -> None:
    """E-17: enum/datetime hearing で Scripts 最大化（R-3）

    以下のパターンは OpenAI を使わず専用ブロック型またはスクリプトで処理すべき:
    (a) save_to/step に 診療科 / department 関連 → type: clinical_department_classifier 必須 (CRITICAL)
    (b) save_to/step に 用件 / intent 関連 → type: intent 必須 (CRITICAL)
    (c) output_format: datetime かつ save_to が 予約日 / appointment 系 → current_appointment_date script 推奨
    (d) output_format: enum かつ no_result_default 未設定 → WARNING（フォールバック値なし）
    (e) output_format: enum で polar でも choices[] でもない → WARNING（決定論化できない語彙未定義）

    (a)(b) は認定代替が存在するため CRITICAL（決定論置換の強制）。(c)〜(e) は WARNING。
    注: polar（はい/いいえ系）enum と choices[] 宣言済み enum は scaffold が自動的に
    yes_no_classifier / n_choice スクリプトへ置換するため対象外。
    """
    DEPT_KEYWORDS = ("診療科", "department", "科名", "科目")
    INTENT_KEYWORDS = ("用件", "intent", "youken", "目的")
    APPT_KEYWORDS  = ("予約日", "appointment", "appt", "reserve", "yoyaku")

    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        btype = blk.get("type", "")
        if btype != "hearing":
            continue
        step = str(blk.get("step", "") or "")
        save_to = str(blk.get("save_to", "") or "")
        output_format = str(blk.get("output_format", "") or "")
        target = (step + " " + save_to).lower()

        # 希望日系（予約希望日/変更希望日/希望時期…）は人間承認済みの OpenAI 例外:
        # SKILL_希望日.md の固定プロンプトを scaffold が自動埋め込みする（決定論置換の対象外）
        if ("希望日" in target) or ("希望時期" in target):
            continue

        # (a) 診療科 — 認定代替（clinical_department_classifier）が存在するため CRITICAL
        if any(kw.lower() in target for kw in DEPT_KEYWORDS):
            _add("CRITICAL", "E-17",
                 f"hearing ブロック '{step}' は診療科関連（save_to='{save_to}'）です。"
                 f"OpenAI hearing は禁止。type: clinical_department_classifier に変更してください "
                 f"(モジュール選定ガイド §3 / R-3 Scripts 最大化)")
            continue  # ブロック型変更が必要なため (d)/(e) は冗長

        # (b) 用件 — 認定代替（intent ブロック / checkup_intent_classifier）が存在するため CRITICAL
        elif any(kw.lower() in target for kw in INTENT_KEYWORDS):
            _add("CRITICAL", "E-17",
                 f"hearing ブロック '{step}' は用件関連（save_to='{save_to}'）です。"
                 f"OpenAI hearing は禁止。type: intent（options[].keywords で語彙定義）に"
                 f"変更してください (モジュール選定ガイド §3 / R-3 Scripts 最大化)")
            continue  # ブロック型変更が必要なため (d)/(e) は冗長

        # (c) datetime + 予約日
        elif output_format == "datetime" and any(kw.lower() in target for kw in APPT_KEYWORDS):
            _add("WARNING", "E-17",
                 f"hearing ブロック '{step}' (output_format: datetime) は予約日関連です。"
                 f"type: script + script_template: current_appointment_date に変更できます "
                 f"(R-3 Scripts 最大化)")

        # (d) enum/datetime で no_result_default 未設定
        # （polar / choices[] の enum は scaffold が認定スクリプトへ置換し OpenAI 障害が
        #   存在しないため対象外）
        _det_labels = {str(c.get("match", "")) for c in _safe_list(blk, "conditions")
                       if isinstance(c, dict)} - {"other", "Other", "OTHER", "default",
                                                  "Default", "DEFAULT", "_default_",
                                                  "NO_RESULT", ""}
        _determinized = bool(blk.get("choices")) or (
            output_format == "enum" and _det_labels
            and _det_labels <= (_POLAR_AFFIRM_E17 | _POLAR_DENY_E17)
            and not blk.get("echo_back") and not blk.get("force_openai"))
        if (output_format in ("enum", "datetime") and not blk.get("no_result_default")
                and not _determinized):
            _add("WARNING", "E-17",
                 f"hearing ブロック '{step}' (output_format: {output_format}) に "
                 f"no_result_default が設定されていません。OpenAI TIMEOUT/ERROR 時にフォールバック値なしで "
                 f"リトライに戻ります。no_result_default を設定すると障害時もデフォルト値で続行できます "
                 f"(R-2 OpenAI フォールバック)")

        # (e) enum で polar でも choices でもない → 決定論化できない（語彙未定義）
        if (output_format == "enum" and blk.get("conditions")
                and not blk.get("choices") and not blk.get("force_openai")
                and not blk.get("echo_back")):
            labels = {str(c.get("match", "")) for c in _safe_list(blk, "conditions")
                      if isinstance(c, dict)}
            labels -= {"other", "Other", "OTHER", "default", "Default", "DEFAULT",
                       "_default_", "NO_RESULT", ""}
            if labels and not labels <= (_POLAR_AFFIRM_E17 | _POLAR_DENY_E17):
                _add("WARNING", "E-17",
                     f"hearing ブロック '{step}' (enum) はラベル {sorted(labels)} が polar でも "
                     f"choices[] 宣言でもないため OpenAI が使われます。choices[]（label + keywords）を"
                     f"宣言すると認定 n_choice スクリプトで決定論化できます (R-3 Scripts 最大化)。"
                     f"意図的に OpenAI を使う場合は force_openai: true を明示してください")


# scaffold_generator._POLAR_AFFIRM/_POLAR_DENY と同期させること（polar 自動置換の判定に使用）
_POLAR_AFFIRM_E17 = {"はい", "あり", "ある", "該当", "する", "希望", "希望する", "必要", "肯定"}
_POLAR_DENY_E17 = {"いいえ", "なし", "ない", "非該当", "しない", "希望しない", "不要", "否定"}


def check_e18(d: dict) -> None:
    """E-18: script_blocks (gen_scripts.py 経由) の NO_RESULT / REPEAT_LIMIT フォールバック未接続検出

    設計書ルートの `script_blocks:`（youken/enum_classifier/faq/department。
    docs/governance/flow-spec-scripts-faq-testing.md §8）は gen_scripts.py が ES5 本体
    (params.script) を生成するだけで、遷移先 (next[]) は対応する scenario_flow の
    `type: script` ブロックの `conditions:` がそのまま使われる。
    このため YAML 側で NO_RESULT / REPEAT_LIMIT の遷移先を明示し忘れても、
    gen_scripts.py 自体は気づかず (WARN も出さず) 生成を続けてしまう。

    チェック内容:
    (a) script_blocks[].module_name に対応する scenario_flow ブロック（type: script、
        step または "script_"+step が module_name と一致）が見つからない → WARNING
        （gen_scripts.py 実行時にも同様の WARN が出るが、設計段階で先に検出する）
    (b) 対応ブロックが見つかった場合、conditions に match: "NO_RESULT" が無い → WARNING
    (c) repeat_guard が明示的に false でない（既定 true）のに conditions に
        match: "REPEAT_LIMIT" が無い → WARNING
        （docs/governance/flow-spec-scripts-faq-testing.md §1-2 のフォールバック方針
        に沿って、次のいずれかを設計者が意図的に決めること: OpenAI フォールバック /
        担当者転送 / 定型リトライ。「暗黙のフォールバックは推定しない」原則に基づく）

    fix_category は付けない（適切な遷移先の判断は人間/director が行う。auto_fixer 対象外）。
    """
    script_blocks = _safe_list(d, "script_blocks")
    if not script_blocks:
        return

    sf = _safe_list(d, "scenario_flow")
    script_blocks_by_module: dict[str, dict] = {}
    for blk in sf:
        if not isinstance(blk, dict) or blk.get("type") != "script":
            continue
        step = str(blk.get("step", "") or "")
        entry_name = step if step.startswith("script_") else f"script_{step}"
        script_blocks_by_module[step] = blk
        script_blocks_by_module[entry_name] = blk

    FALLBACK_TYPES = {"youken", "enum_classifier", "faq", "department"}
    for entry in script_blocks:
        if not isinstance(entry, dict):
            continue
        block_type = str(entry.get("type", "") or "")
        if block_type not in FALLBACK_TYPES:
            continue
        module_name = str(entry.get("module_name", "") or "")
        if not module_name:
            continue

        target_blk = script_blocks_by_module.get(module_name)
        if target_blk is None:
            _add("WARNING", "E-18",
                 f"script_blocks[module_name='{module_name}', type='{block_type}'] に対応する "
                 f"scenario_flow の type: script ブロックが見つかりません。NO_RESULT / REPEAT_LIMIT "
                 f"の遷移先が検証できないため、module_name と scenario_flow の step 名（または "
                 f"'script_'+step）を一致させてください")
            continue

        conditions = target_blk.get("conditions", []) or []
        matches = {str(c.get("match", "")) for c in conditions if isinstance(c, dict)}
        step = str(target_blk.get("step", "") or "")

        if "NO_RESULT" not in matches:
            _add("WARNING", "E-18",
                 f"script ブロック '{step}'（script_blocks type='{block_type}'）の conditions に "
                 f"match: \"NO_RESULT\" がありません。キーワード不一致時の遷移先が未定義です "
                 f"(フォールバック方針: docs/governance/flow-spec-scripts-faq-testing.md §1-2)")

        repeat_guard = entry.get("repeat_guard", True)
        if repeat_guard and "REPEAT_LIMIT" not in matches:
            _add("WARNING", "E-18",
                 f"script ブロック '{step}'（script_blocks type='{block_type}'）は repeat_guard "
                 f"既定 true ですが、conditions に match: \"REPEAT_LIMIT\" がありません。"
                 f"リピート上限到達後の遷移先（OpenAIフォールバック/担当者転送/定型リトライ等）を"
                 f"明示的に決めてください（暗黙のフォールバックは推定しません。"
                 f"docs/governance/flow-spec-scripts-faq-testing.md §1-2）")


def check_e19(d: dict) -> None:
    """E-19: hearing の choices[]（n_choice 決定論化用の語彙宣言）の整合性チェック

    choices[] が宣言された enum hearing は scaffold が認定 n_choice スクリプトへ置換する。
    その前提が壊れていると実行時に行き止まりになるため設計段階で検証する:
    (a) 各 choice に label が無い → CRITICAL
    (b) 各 choice に keywords も dtmf も無い → CRITICAL（ラベル完全一致でしか判定できない）
    (c) conditions の分岐ラベル（other/NO_RESULT 以外）が choices の label 集合に無い → CRITICAL
        （n_choice は choices の label しか出力しないため、その分岐は永久に到達不能）
    (d) choices があるのに output_format != enum → CRITICAL

    ★ choices から生成される n_choice spec は新規 spec 扱い。part-certification-spec.md に
    従い oracle_gate / P6 受入が必要（「1 文字でも改変したら再受入」）。
    """
    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict) or blk.get("type") != "hearing":
            continue
        choices = _safe_list(blk, "choices")
        if not choices:
            continue
        step = str(blk.get("step", "") or "(unnamed)")

        # (d) output_format
        if str(blk.get("output_format", "") or "") != "enum":
            _add("CRITICAL", "E-19",
                 f"hearing ブロック '{step}' に choices[] がありますが output_format が "
                 f"'{blk.get('output_format')}' です。n_choice 決定論化は enum のみ対象のため "
                 f"output_format: enum に修正してください")

        choice_labels: set = set()
        for i, c in enumerate(choices):
            if not isinstance(c, dict):
                _add("CRITICAL", "E-19",
                     f"hearing ブロック '{step}' choices[{i}] が辞書ではありません: {c!r}")
                continue
            label = str(c.get("label", "") or "").strip()
            if not label:
                _add("CRITICAL", "E-19",
                     f"hearing ブロック '{step}' choices[{i}] に label がありません")
                continue
            choice_labels.add(label)
            has_kw = bool([k for k in _safe_list(c, "keywords") if str(k).strip()])
            has_strong = bool([k for k in _safe_list(c, "strong_keywords") if str(k).strip()])
            has_preset = bool(str(c.get("preset", "") or "").strip())
            has_dtmf = bool(str(c.get("dtmf", "") or "").strip())
            if not (has_kw or has_strong or has_preset or has_dtmf):
                _add("CRITICAL", "E-19",
                     f"hearing ブロック '{step}' choices[label='{label}'] に keywords / "
                     f"strong_keywords / preset / dtmf のいずれもありません。ラベル完全一致で"
                     f"しか判定できず認識率が極端に低くなります。発話語彙を keywords に"
                     f"列挙してください")

        # (c) conditions ラベルが choices でカバーされているか
        skip_tokens = {"other", "Other", "OTHER", "default", "Default", "DEFAULT",
                       "_default_", "NO_RESULT"}
        for c in _safe_list(blk, "conditions"):
            if not isinstance(c, dict):
                continue
            m = str(c.get("match", "") or "")
            if not m or m in skip_tokens:
                continue
            if m not in choice_labels:
                _add("CRITICAL", "E-19",
                     f"hearing ブロック '{step}' の conditions[match='{m}'] が choices の "
                     f"label 集合 {sorted(choice_labels)} にありません。n_choice は choices の "
                     f"label しか出力しないため、この分岐は到達不能です。choices に追加するか "
                     f"conditions 側のラベルを修正してください")


def check_f8(d: dict) -> None:
    """F-8: faq_items が定義されているなら scenario_flow に type: faq ブロックが必須（R-7）

    設計書に faq_items リストが存在するのに scenario_flow で FAQ ブロックを使っていない場合は
    CRITICAL。FAQ 照合が意図されているのにフローから省かれている可能性が高い。
    """
    faq_items = _safe_list(d, "faq_items")
    if not faq_items:
        return

    sf = _safe_list(d, "scenario_flow")
    has_faq_block = any(
        isinstance(blk, dict) and blk.get("type") == "faq"
        for blk in sf
    )
    if not has_faq_block:
        _add("CRITICAL", "F-8",
             "faq_items が定義されていますが scenario_flow に type: faq ブロックがありません。"
             "FAQ 照合ブロックを scenario_flow に追加するか、faq_items を削除してください (R-7)")


def check_f9(d: dict) -> None:
    """F-9: 電話番号/氏名/生年月日の hearing ブロックは type: slot が必須（R-8）

    以下の save_to または step 名を持つ hearing ブロックは認定済み決定論部品（slot）で
    処理すべきであり、type: hearing は禁止:
    - 電話番号 / phone → slot_kind: phone
    - 氏名（patientName 以外の患者氏名）/ 名前 → slot_kind: patient_name
    - 生年月日 / dateOfBirth / dob → slot_kind: date_of_birth
    """
    PHONE_KW   = ("電話番号", "phone", "denwabango", "renrakusaki", "tel")
    NAME_KW    = ("患者氏名", "patient_name", "patientname", "shimei")
    DOB_KW     = ("生年月日", "dateofbirth", "dateofbirth", "dob", "birthday")

    sf = _safe_list(d, "scenario_flow")
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        if blk.get("type") != "hearing":
            continue
        step    = str(blk.get("step", "") or "")
        save_to = str(blk.get("save_to", "") or "")
        target  = (step + " " + save_to).lower()

        if any(kw in target for kw in PHONE_KW):
            _add("CRITICAL", "F-9",
                 f"hearing ブロック '{step}' (save_to='{save_to}') は電話番号聴取です。"
                 f"type: slot / slot_kind: phone に変更してください（認定済み決定論部品）(R-8)")
        elif any(kw in target for kw in NAME_KW):
            _add("CRITICAL", "F-9",
                 f"hearing ブロック '{step}' (save_to='{save_to}') は患者氏名聴取です。"
                 f"type: slot / slot_kind: patient_name に変更してください（認定済み決定論部品）(R-8)")
        elif any(kw in target for kw in DOB_KW):
            _add("CRITICAL", "F-9",
                 f"hearing ブロック '{step}' (save_to='{save_to}') は生年月日聴取です。"
                 f"type: slot / slot_kind: date_of_birth に変更してください（認定済み決定論部品）(R-8)")


def check_f10(d: dict) -> None:
    """F-10: 個人情報4種（phone/dob/patient_name/card_number）ブロックの重複（INC-260716-2）

    phone/dob/patient_name/card_number は scaffold が内部で全パターン
    （phone なら携帯/固定/その他の分岐）を1ブロックで処理する決定論部品のため、
    同じ save_to（またはブロック型が同一で save_to 未指定）を持つブロックを
    複数書くと、内部分岐一式が scenario_flow の数だけ重複生成される
    （例: 携帯電話用・固定電話用で type: phone を2つ書いてしまう誤り）。
    """
    SLOT_ALIAS_TYPES = ("phone", "dob", "patient_name", "card_number")
    sf = _safe_list(d, "scenario_flow")
    seen: dict[tuple[str, str], list[str]] = {}
    for blk in sf:
        if not isinstance(blk, dict):
            continue
        btype = blk.get("type", "")
        if btype not in SLOT_ALIAS_TYPES:
            continue
        save_to = str(blk.get("save_to", "") or "")
        key = (btype, save_to)
        seen.setdefault(key, []).append(str(blk.get("step", "?")))
    for (btype, save_to), steps in seen.items():
        if len(steps) > 1:
            _add("WARNING", "F-10",
                 f"type: {btype} のブロックが {len(steps)} 件（save_to='{save_to}'）: "
                 f"{', '.join(steps)}。この型は1ブロックで全パターンを内部分岐するため、"
                 f"通常は1つに統合すべき（分岐一式の重複生成の兆候。INC-260716-2）。"
                 f"施設固有の理由で意図的に分けている場合は無視してよい")


def check_l4(d: dict) -> None:
    """L-4: フロー図のTTSモジュールが tts_modules でカバーされているか"""
    tts_names = {t.get("module_name", "") for t in _safe_list(d, "tts_modules") if t}
    for fd in _safe_list(d, "flow_diagrams"):
        if not fd:
            continue
        diagram = fd.get("diagram", "")
        if not diagram:
            continue
        # フロー図から (TTS) を含むモジュール名を抽出
        tts_refs = re.findall(r'(\S+?)[\(（]TTS[\)）]', diagram)
        for ref in tts_refs:
            ref_clean = ref.strip("→├└─ ")
            if ref_clean and ref_clean not in tts_names:
                _add("WARNING", "L-4",
                     f"フロー図に TTS '{ref_clean}' があるが tts_modules に未登録")


# ──────────────────────────────────────────────
# V 系: TTS 変数・プレースホルダー規則（2026-07-16 設計原則）
# ──────────────────────────────────────────────

# <%変数%> 参照パターン（空白許容: <% var %> / <%var%>）
_VAR_REF_RE = re.compile(r"<%\s*([^%\s]+)\s*%>")
# （A/B）型プレースホルダー: 全角/半角括弧内にスラッシュ区切り
_PLACEHOLDER_RE = re.compile(r"[（(]([^）)/]+/[^）)]+)[）)]")

# setObject でコンテキスト変数を保存するブロック型（scaffold_generator 実装準拠）。
# これらの save_to は <%変数%> で TTS / reference_module から参照可能。
SETOBJECT_TYPES = {
    "intent", "slot", "dob", "phone", "patient_name", "card_number",
    "script", "faq", "clinical_department", "clinical_department_normalize",
    "clinical_department_classifier", "phone2name", "clinic_day_default",
}

def check_l10(d: dict) -> None:
    """L-10: hearing ブロックの yes_label/no_label 整合（#270）。

    未指定は既定 肯定/否定（合法）。規約: docs/governance/output-label-convention.md
    """
    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict) or blk.get("type") != "hearing":
            continue
        yl, nl = blk.get("yes_label"), blk.get("no_label")
        if yl is None and nl is None:
            continue
        step = blk.get("step", "?")
        if (yl is None) != (nl is None):
            _add("CRITICAL", "L-10",
                 f"hearing '{step}': yes_label/no_label は両方指定か両方省略（片方のみ不可）")
            continue
        yl, nl = str(yl), str(nl)
        if not yl.strip() or not nl.strip():
            _add("CRITICAL", "L-10", f"hearing '{step}': yes_label/no_label が空")
        elif yl == nl:
            _add("CRITICAL", "L-10", f"hearing '{step}': yes_label と no_label が同一（{yl!r}）＝分岐不能")
        if "NO_RESULT" in (yl, nl):
            _add("CRITICAL", "L-10",
                 f"hearing '{step}': ラベルに予約語 'NO_RESULT' は使えない")


# scaffold / Brekeke が実行時に自前で setObject するシステム変数
_SYSTEM_CONTEXT_VARS = {
    "additionalPhoneNumber", "incoming_phone", "scripts-faq",
    "user_classification", "classification", "yomiage_cardnumber",
}


def _termination_step_names(d: dict) -> set[str]:
    """終話扱いの step 名を収集（scenario_flow type:termination + termination_patterns 名）"""
    names = {
        str(b.get("step"))
        for b in _safe_list(d, "scenario_flow")
        if isinstance(b, dict) and b.get("type") == "termination" and b.get("step")
    }
    names |= {
        str(t.get("name"))
        for t in _safe_list(d, "termination_patterns")
        if isinstance(t, dict) and t.get("name")
    }
    return names


def _iter_tts_texts(d: dict):
    """(step名, フィールド名, TTSテキスト) を step_details / tts_modules から列挙"""
    for sd in _safe_list(d, "step_details"):
        if not isinstance(sd, dict):
            continue
        name = str(sd.get("step_name", ""))
        for fld in ("tts_announcement", "retry_tts", "reconfirm_tts"):
            txt = sd.get(fld)
            if isinstance(txt, str) and txt:
                yield name, fld, txt
    for tm in _safe_list(d, "tts_modules"):
        if not isinstance(tm, dict):
            continue
        name = str(tm.get("module_name", ""))
        txt = tm.get("announcement")
        if isinstance(txt, str) and txt:
            yield name, "announcement", txt


def _setobject_var_names(d: dict) -> set[str]:
    """SETOBJECT_TYPES ブロックの save_to 集合（中間 TTS 参照が許される変数名）。
    OpenAI 系（hearing 等）の save_to は setObject されず実行時に空になるため対象外。"""
    names: set[str] = set()
    for blk in _safe_list(d, "scenario_flow"):
        if isinstance(blk, dict) and blk.get("type") in SETOBJECT_TYPES and blk.get("save_to"):
            names.add(str(blk["save_to"]))
    return names


def check_v1(d: dict) -> None:
    """V-1: 中間フロー TTS の <%変数%> / （A/B）プレースホルダー禁止。
    <%変数%> の TTS 参照は終話（termination）、または SETOBJECT_TYPES ブロック
    （聴取なしで setObject する決定論ブロック。例: clinic_day_default）の save_to
    のみ許可（2026-07-17 例外追加 — OpenAI/hearing 系の save_to は実行時に空になる
    ため引き続き禁止）。
    （A/B）型は終話含め全 TTS で禁止（ルート分割 or 文言確定で解消する）。"""
    term_names = _termination_step_names(d)
    setobject_vars = _setobject_var_names(d)
    for name, fld, txt in _iter_tts_texts(d):
        is_term = name in term_names
        ph = _PLACEHOLDER_RE.search(txt)
        if ph:
            _add("CRITICAL", "V-1",
                 f"TTS '{name}'.{fld} に プレースホルダー（{ph.group(1)}）が残っています。"
                 f"ルート分割（各ルート固定TTS）または文言確定で解消してください")
        if not is_term:
            var = _VAR_REF_RE.search(txt)
            if var and var.group(1) in setobject_vars:
                var = None
            if var:
                _add("CRITICAL", "V-1",
                     f"中間フロー TTS '{name}'.{fld} が <%{var.group(1)}%> を参照しています。"
                     f"<%変数%> の TTS 参照は終話のみ許可。ルート分割で固定TTSにしてください")


def check_v2(d: dict) -> None:
    """V-2: <%変数%> プロベナンス。TTS / reference_module が参照する変数が
    setObject する部品（SETOBJECT_TYPES）の save_to かシステム変数であること。
    OpenAI 系ブロック（hearing/free_text 等）の save_to は setObject されないため、
    参照すると実行時に空文字になる。"""
    setobject_vars: set[str] = set(_SYSTEM_CONTEXT_VARS)
    openai_vars: dict[str, str] = {}  # var -> 保存元 step（非 setObject 系）
    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict):
            continue
        save_to = blk.get("save_to")
        if not save_to:
            continue
        if blk.get("type") in SETOBJECT_TYPES:
            setobject_vars.add(str(save_to))
        else:
            openai_vars.setdefault(str(save_to), str(blk.get("step", "?")))

    def _check_ref(location: str, var: str) -> None:
        if var in setobject_vars:
            return
        if var in openai_vars:
            _add("CRITICAL", "V-2",
                 f"{location} が <%{var}%> を参照していますが、保存元 "
                 f"'{openai_vars[var]}' は setObject しないブロック型のため実行時に空になります。"
                 f"intent/slot/script 等の setObject 部品で保存するか参照をやめてください")
        else:
            _add("CRITICAL", "V-2",
                 f"{location} が <%{var}%> を参照していますが、"
                 f"この変数を save_to するブロックが scenario_flow にありません")

    for name, fld, txt in _iter_tts_texts(d):
        for var in _VAR_REF_RE.findall(txt):
            _check_ref(f"TTS '{name}'.{fld}", var)
    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict):
            continue
        ref = blk.get("reference_module")
        if isinstance(ref, str):
            for var in _VAR_REF_RE.findall(ref):
                _check_ref(f"ブロック '{blk.get('step', '?')}'.reference_module", var)
    for t in _safe_list(d, "termination_patterns"):
        if not isinstance(t, dict):
            continue
        txt = t.get("tts_announcement")
        if isinstance(txt, str):
            for var in _VAR_REF_RE.findall(txt):
                _check_ref(f"終話パターン '{t.get('name', '?')}'.tts_announcement", var)


# ──────────────────────────────────────────────
# S 系: TTS↔選択肢↔スクリプト整合（2026-07-16 設計原則）
# ──────────────────────────────────────────────

# TTS 内の列挙「1番、予約」「２、キャンセル」「1番は はい」等を抽出（全角数字対応）
_ENUM_ITEM_RE = re.compile(r"[「]?([0-9０-９])\s*番?\s*(?:[、，,]|は[\s、，]*)\s*([^」。\n、]+)")

# CMR conditions.match で label 照合を免除する制御値
_CMR_CONTROL_MATCHES = {"default", "NO_RESULT", "REPEAT", "FALLBACK", ""}


def _z2h(s: str) -> str:
    """全角数字→半角"""
    return s.translate(str.maketrans("０１２３４５６７８９", "0123456789"))


def _step_tts_map(d: dict) -> dict[str, str]:
    """step 名 → TTS 本文（step_details 優先・tts_modules フォールバック）"""
    out: dict[str, str] = {}
    for tm in _safe_list(d, "tts_modules"):
        if isinstance(tm, dict) and isinstance(tm.get("announcement"), str):
            out[str(tm.get("module_name", ""))] = tm["announcement"]
    for sd in _safe_list(d, "step_details"):
        if isinstance(sd, dict) and isinstance(sd.get("tts_announcement"), str):
            out[str(sd.get("step_name", ""))] = sd["tts_announcement"]
    return out


# 隣接重複フレーズ検出: 「XXない場合は、XXない場合は」のようなコピペ typo を検出する。
# 読点区切りの節が「丸ごと」直後に繰り返される形のみを対象とする。
# - 前方一致だけでは誤検知する（例:「診療予約、診療予約の変更」は列挙であり typo でない）
#   ため、繰り返し末尾に読点/句点/文末が来ることを (?=...) で要求し、節全体の一致を強制する。
# - 4文字未満の短い相槌・助詞の偶然一致は対象外。
_DUP_PHRASE_RE = re.compile(r"([^、。\s]{4,})、\1(?=[、。「」『』（）()]|$)")
# 電話番号の意図的な2回読み上げ（聞き取りやすさのための正規の設計パターン。
# 信州大学医学部附属病院・福岡大学筑紫病院 等で確認済み）は typo ではないため除外する。
_PHONE_LIKE_RE = re.compile(r"^[0-9０-９\-－‐ー]+$")


def check_v3(d: dict) -> None:
    """V-3: TTS 文中の隣接重複フレーズ（コピペ typo）検出。
    実例: 「ご予約ご希望日をお話しください。ない場合は、ない場合は「ありません。」とお話しください。」
    （INC調査: カレス記念病院_診療 Sheet1 CSV の手入力 typo が properties まで無検知で
    到達していた。壁打ちに頼らず機械ゲートで検出する）。
    電話番号の2回読み上げ（意図的な設計パターン）は除外する。"""
    for name, fld, txt in _iter_tts_texts(d):
        for m in _DUP_PHRASE_RE.finditer(txt):
            phrase = m.group(1)
            if _PHONE_LIKE_RE.match(phrase):
                continue
            _add("CRITICAL", "V-3",
                 f"TTS '{name}'.{fld} に隣接重複フレーズ「{phrase}、{phrase}」が検出されました"
                 f"（コピペ typo の可能性。CSV/設計書の文言を確認し重複を解消してください）")


# 未確定日付/数値のプレースホルダー文字（〇月〇日 等）。（A/B）型と違い単独の記号のため
# 別パターンとして検出する。
_MARU_PLACEHOLDER_RE = re.compile(r"〇")


def check_v6(d: dict) -> None:
    """V-6: 復唱あり（echo_back/reconfirm）なのに復唱文言（reconfirm_tts）が未確定。
    Sheet1 の復唱文言列が空のまま生成されると「(要記入 — 復唱文言)」プレースホルダーが
    残る。scaffold は既定文言（例: 予約日は <%reservationDate_Md%> 読み）で補完するため
    CRITICAL にはしないが、施設固有の言い回しを意図している場合の記入漏れを警告する。
    復唱文言に値の代入位置（~ / 〜 / <%変数%> / #data#）が無い場合も警告
    （復唱は valid な値を文言に差し込んで読み上げる前提のため）。"""
    for sd in _safe_list(d, "step_details"):
        if not isinstance(sd, dict):
            continue
        if not (sd.get("reconfirm") or sd.get("echo_back")):
            continue
        name = str(sd.get("step_name", "?"))
        txt = str(sd.get("reconfirm_tts") or "")
        if not txt or "要記入" in txt:
            _add("WARNING", "V-6",
                 f"'{name}': 復唱あり（reconfirm/echo_back）ですが復唱文言"
                 f"（reconfirm_tts）が未記入です。scaffold の既定文言が使われます。"
                 f"施設固有の言い回しにする場合は「~でよろしいですか」形式で記入してください"
                 f"（~ に聴取値が代入されます）")
        elif not re.search(
                r"[~〜]|[〇○×✕]{2,}|[…‥][…‥.．。]*|[・]{3,}|[.。．]{3,}|[_＿]{2,}|[-ー]{3,}"
                r"|<%[^%]+%>|#data#"
                # アンカー式（scaffold _RECONF_ANCHOR_RE と同認識）: 、/は/文頭 直後の
                # で(よろしい|いい|間違い…) は挿入位置ありとみなす
                r"|(?:^|\{tts_(?:g|ai):|[、。:：はが])[^ぁ-んァ-ヶー一-龥々a-zA-Z0-9０-９、。]*で(?:よろしい|いい|お間違い|間違い|大丈夫)",
                txt):
            _add("WARNING", "V-6",
                 f"'{name}': reconfirm_tts に値の代入位置（~ / <%変数%> / #data#）が"
                 f"ありません。復唱は聴取値を文言へ差し込んで読み上げるため、"
                 f"固定文のままだと値が読まれません")


def check_v5(d: dict) -> None:
    """V-5: TTS 文中の未確定プレースホルダー文字（〇月〇日 等）検出。
    実例: カレス記念病院_診療の '3診療日確認'「こちらのお電話は、〇月〇日以降の
    受診を希望される...」— 日付が確定していないまま本番文言として出力されていた。"""
    for name, fld, txt in _iter_tts_texts(d):
        if _MARU_PLACEHOLDER_RE.search(txt):
            _add("CRITICAL", "V-5",
                 f"TTS '{name}'.{fld} に未確定プレースホルダー「〇」が残っています"
                 f"（例: 〇月〇日）。実際の日付/数値に確定してから出力してください")


def _block_choice_list(blk: dict) -> list[dict]:
    """intent の options / hearing の choices を統一的に返す"""
    for key in ("options", "choices"):
        v = blk.get(key)
        if isinstance(v, list) and v and all(isinstance(o, dict) for o in v):
            return v
    return []


def _block_stt_type(blk: dict, d: dict) -> str:
    """ブロックの stt_type（scenario_flow 直接指定 or hearing_items から）"""
    if blk.get("stt_type"):
        return str(blk["stt_type"])
    step = str(blk.get("step", ""))
    for h in _safe_list(d, "hearing_items"):
        if isinstance(h, dict) and str(h.get("name", "")) == step and h.get("stt_type"):
            return str(h["stt_type"])
    return ""


def check_s1(d: dict) -> None:
    """S-1: TTS↔選択肢↔スクリプト整合"""
    tts_map = _step_tts_map(d)

    # ---- 変数 → 保存元 label 集合（S-1-5 用） ----
    var_labels: dict[str, set[str]] = {}
    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict):
            continue
        save_to = blk.get("save_to")
        chs = _block_choice_list(blk)
        if save_to and chs:
            var_labels.setdefault(str(save_to), set()).update(
                str(c.get("label", "")) for c in chs if c.get("label"))
        # intent + engine:v2 + intent_spec: label 集合は rules[].intent / numbers 値から
        ispec = blk.get("intent_spec")
        if save_to and isinstance(ispec, dict):
            labels = {str(r.get("intent")) for r in (ispec.get("rules") or [])
                      if isinstance(r, dict) and r.get("intent")}
            labels |= {str(v) for v in (ispec.get("numbers") or {}).values()}
            if labels:
                var_labels.setdefault(str(save_to), set()).update(labels)

    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict):
            continue
        step = str(blk.get("step", "?"))
        chs = _block_choice_list(blk)

        # ---- S-1-5: CMR conditions.match ⊆ 保存元 label 集合 ----
        ref = blk.get("reference_module")
        if isinstance(ref, str):
            for var in _VAR_REF_RE.findall(ref):
                labels = var_labels.get(var)
                if labels is None:
                    continue  # 選択肢型でない保存元（V-2 の担当範囲）
                for c in _safe_list(blk, "conditions"):
                    if not isinstance(c, dict):
                        continue
                    m = str(c.get("match", ""))
                    if m in _CMR_CONTROL_MATCHES:
                        continue
                    if m not in labels:
                        _add("CRITICAL", "S-1",
                             f"ルーター '{step}' の match '{m}' は保存元 <%{var}%> の "
                             f"label 集合 {sorted(labels)} に存在しません。"
                             f"スクリプト出力と一致しないため default へ落ちます")

        if not chs:
            continue

        # ---- S-1-4: label が自身の keywords に含まれるか ----
        for c in chs:
            label = str(c.get("label", ""))
            kws = c.get("keywords")
            if label and isinstance(kws, list) and kws and label not in [str(k) for k in kws]:
                _add("WARNING", "S-1",
                     f"ブロック '{step}' の選択肢 '{label}' が自身の keywords に含まれていません。"
                     f"label をそのまま発話した場合にマッチしない可能性があります")

        tts = tts_map.get(step, "")
        if not tts:
            continue

        # ---- S-1-1 / S-1-2: TTS 列挙 と (number, label) の一致 ----
        enum_items = [(_z2h(n), lbl.strip()) for n, lbl in _ENUM_ITEM_RE.findall(tts)]
        if enum_items:
            by_number = {str(c.get("number")): str(c.get("label", ""))
                         for c in chs if c.get("number") is not None}
            for n, spoken in enum_items:
                if n not in by_number:
                    _add("CRITICAL", "S-1",
                         f"ブロック '{step}' の TTS が「{n}番、{spoken}」と案内していますが、"
                         f"選択肢に number: {n} がありません")
                elif by_number[n] not in spoken and spoken not in by_number[n]:
                    _add("CRITICAL", "S-1",
                         f"ブロック '{step}' の TTS「{n}番、{spoken}」と選択肢 "
                         f"number: {n} の label '{by_number[n]}' が一致しません。"
                         f"プッシュ/発話が別の分岐に飛びます")
            if len(enum_items) != len(chs):
                _add("CRITICAL", "S-1",
                     f"ブロック '{step}' の TTS は {len(enum_items)} 択を案内していますが、"
                     f"選択肢は {len(chs)} 件です。案内されない/存在しない選択肢が発生します")

        # ---- S-1-3: プッシュ案内 ⇔ DTMF 系 stt_type ----
        stt = _block_stt_type(blk, d)
        mentions_push = ("プッシュ" in tts) or ("押して" in tts)
        is_dtmf = "DTMF" in stt.upper()
        if mentions_push and stt and not is_dtmf:
            _add("CRITICAL", "S-1",
                 f"ブロック '{step}' の TTS はプッシュ入力を案内していますが "
                 f"stt_type '{stt}' は DTMF 非対応です。案内どおり押しても認識されません")
        elif is_dtmf and enum_items and not mentions_push:
            _add("WARNING", "S-1",
                 f"ブロック '{step}' は stt_type DTMF 系ですが TTS にプッシュ案内がありません。"
                 f"番号入力できることが利用者に伝わりません")


# ──────────────────────────────────────────────
# S-2: DTMF キー約束 ↔ 設定整合（2026-07-16 設計原則）
# ──────────────────────────────────────────────

# scaffold_generator.py build_stt / build_stt_dtmf_split の termdtmf ハードコード値。
# 変更時はここも同期すること（"#" = DTMF 入力の終端キー・remove_term=Yes）。
SCAFFOLD_TERMDTMF = "#"

# キー呼称 → 実キー。こめじるし は曖昧（一般телephony では * /
# docs/brekeke/brekeke_module_reference.md では # と注記）のため AMBIGUOUS 扱い。
_KEY_WORD_TO_KEY = {
    "アスタリスク": "*", "米印": "*", "ほし": "*", "スター": "*",
    "＊": "*", "*": "*",
    "シャープ": "#", "いげた": "#", "井桁": "#", "＃": "#", "#": "#",
}
_AMBIGUOUS_KEY_WORDS = {"こめじるし"}

# 「…を押して」直前のキー表現（数字 / 記号 / 呼称）
_PRESS_RE = re.compile(
    r"([0-9０-９＊*＃#]|こめじるし|アスタリスク|米印|シャープ|いげた|井桁|スター)"
    r"[」』]?\s*(?:を|キーを)?\s*押し")
# 終端案内の文（選択肢でなく入力終了の合図）
_TERMINATOR_SENT_RE = re.compile(r"最後に|入力が終わ|終わりましたら")


def _block_dtmf_keys(blk: dict) -> set[str]:
    """ブロックが受け付ける DTMF キー集合（choices/options の dtmf・number、dtmf_options）"""
    keys: set[str] = set()
    for c in _block_choice_list(blk):
        for f in ("dtmf", "number"):
            if c.get(f) is not None:
                keys.add(_z2h(str(c[f]).strip()))
    for o in _safe_list(blk, "dtmf_options"):
        if isinstance(o, dict) and o.get("dtmf") is not None:
            keys.add(_z2h(str(o["dtmf"]).strip()))
    if blk.get("type") in ("intent", "hearing"):
        # scaffold が STT wiring（^[*＊]$ → repeat_star）で「*」→TTS再生 を自動配線する
        keys.add("*")
    return keys


def check_s2(d: dict) -> None:
    """S-2: TTS が押下を約束したキーと DTMF 設定の整合。
    - 選択肢として '#'（=scaffold 終端キー）を約束 → CRITICAL（押した瞬間 入力終了扱い）
    - 終端案内が '*' 系呼称 → CRITICAL（実際の終端は '#'。* を押しても終わらない）
    - 「こめじるし」→ WARNING（呼称が曖昧。実キーを確認し シャープ 等に統一推奨）
    - 選択肢キー約束が受付キー集合に無い → CRITICAL"""
    # ── パス1: 全 TTS（slot 展開のサブモジュール TTS 含む）に対する呼称・終端キー検査 ──
    for name, fld, tts in _iter_tts_texts(d):
        if "押し" not in tts:
            continue
        for sent in re.split(r"(?<=[。！？!?])", tts):
            is_term_sent = bool(_TERMINATOR_SENT_RE.search(sent))
            for raw in _PRESS_RE.findall(sent):
                word = raw.strip()
                if word in _AMBIGUOUS_KEY_WORDS:
                    _add("WARNING", "S-2",
                         f"TTS '{name}'.{fld} が「こめじるし」の押下を案内していますが、"
                         f"呼称が曖昧です（一般には '*'、本システムの終端キーは "
                         f"'{SCAFFOLD_TERMDTMF}'）。「シャープ」等の一意な呼称に統一してください")
                    continue
                key = _KEY_WORD_TO_KEY.get(word, _z2h(word))
                if is_term_sent and key != SCAFFOLD_TERMDTMF:
                    _add("CRITICAL", "S-2",
                         f"TTS '{name}'.{fld} が入力終了キーとして '{key}' を案内していますが、"
                         f"実際の終端キー(termdtmf)は '{SCAFFOLD_TERMDTMF}' です。"
                         f"案内どおり押しても入力が終わりません")
                elif not is_term_sent and key == SCAFFOLD_TERMDTMF:
                    _add("CRITICAL", "S-2",
                         f"TTS '{name}'.{fld} が選択肢として '{key}' の押下を案内していますが、"
                         f"'{SCAFFOLD_TERMDTMF}' は DTMF 終端キー(termdtmf)です。"
                         f"押した瞬間に空入力確定となり選択できません")

    # ── パス2: scenario_flow ブロックに紐づく TTS の「約束キー ∈ 受付キー集合」検査 ──
    tts_map = _step_tts_map(d)
    for blk in _safe_list(d, "scenario_flow"):
        if not isinstance(blk, dict):
            continue
        step = str(blk.get("step", "?"))
        tts = tts_map.get(step, "")
        if not tts or "押し" not in tts:
            continue
        keys = _block_dtmf_keys(blk)
        if not keys:
            continue
        for sent in re.split(r"(?<=[。！？!?])", tts):
            if _TERMINATOR_SENT_RE.search(sent):
                continue
            for raw in _PRESS_RE.findall(sent):
                word = raw.strip()
                if word in _AMBIGUOUS_KEY_WORDS:
                    continue
                key = _KEY_WORD_TO_KEY.get(word, _z2h(word))
                if key != SCAFFOLD_TERMDTMF and key not in keys:
                    _add("CRITICAL", "S-2",
                         f"ブロック '{step}' の TTS が '{key}' の押下を案内していますが、"
                         f"受付キー集合 {sorted(keys)} に '{key}' がありません。"
                         f"押しても NO_RESULT / 無反応になります")


# ──────────────────────────────────────────────
# メイン
# ──────────────────────────────────────────────

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="設計書 YAML 機械的整合性チェック")
    ap.add_argument("spec", help="設計書 YAML パス")
    ap.add_argument("--json-report", help="Issue の JSON レポート出力先（yaml_auto_fixer.py 用）")
    args = ap.parse_args()

    spec_path = args.spec

    try:
        with open(spec_path, encoding="utf-8") as f:
            raw_text = f.read()
        d = yaml.safe_load(raw_text)
    except FileNotFoundError:
        print(f"[ERROR] ファイルが見つかりません: {spec_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"[ERROR] YAML解析エラー: {e}")
        sys.exit(1)

    if not isinstance(d, dict):
        print("[ERROR] YAMLのルートが辞書ではありません")
        sys.exit(1)

    # 全チェック実行
    check_t1(d)
    check_t2(d)
    check_t3(d)
    check_t4(d)
    check_t5(d, raw_text)
    check_t6(d)
    check_t7(d)
    check_t8(d)
    check_t9(d)
    check_l1(d)
    check_l2(d)
    check_l3(d)
    check_l5(d)
    check_l6(d)
    check_l8(d)
    check_l9(d)
    check_e1(d)
    check_e2b(d)
    check_e2(d)
    check_e5a(d)
    check_e5b(d)
    check_e5c(d)
    check_e5d(d)
    check_e6(d)
    check_e7(d)
    check_e8(d)
    check_e9(d)
    check_e10(d)
    check_e11(d)
    check_e12(d)
    check_e13(d)
    check_e14(d)
    check_e15(d)
    check_e16(d)
    check_e17(d)
    check_e18(d)
    check_e19(d)
    check_i1(d)
    check_i3(d)
    check_i6(d)
    check_i7(d)
    check_m2(d)
    check_i4(d)
    check_i5(d)
    check_l4(d)
    check_l10(d)
    check_l11(d)
    check_f1(d)
    check_f2(d)
    check_f3(d)
    check_f4(d)
    check_f6(d)
    check_f7a(d)
    check_f8(d)
    check_f9(d)
    check_f10(d)
    # Pattern C (DTMF 分離) — 仕様: docs/specs/dtmf_split_pattern_c.md
    check_d1(d)
    check_d2(d)
    check_d3(d)
    check_d4(d)
    # V 系: TTS 変数・プレースホルダー規則（2026-07-16 設計原則）
    check_v1(d)
    check_v2(d)
    check_v3(d)
    check_v5(d)
    check_v6(d)
    # S 系: TTS↔選択肢↔スクリプト整合（2026-07-16 設計原則）
    check_s1(d)
    check_s2(d)

    # 結果集計・出力
    criticals = [i for i in _issues if i.severity == "CRITICAL"]
    warnings  = [i for i in _issues if i.severity == "WARNING"]
    auto_count = sum(1 for i in _issues if i.fix_category == "auto")

    print(f"=== qa_validator.py: {spec_path} ===")
    print(f"CRITICAL: {len(criticals)} 件  WARNING: {len(warnings)} 件  (うち auto 修正可: {auto_count} 件)")
    print()

    for issue in _issues:
        prefix = "[CRITICAL]" if issue.severity == "CRITICAL" else "[WARNING] "
        tag = "  <auto>" if issue.fix_category == "auto" else ""
        print(f"{prefix} {issue.code}: {issue.message}{tag}")

    if not _issues:
        print("全チェック PASS")

    # JSON レポート出力（yaml_auto_fixer.py 用）
    if args.json_report:
        report = {
            "spec": spec_path,
            "issues": [asdict(i) for i in _issues],
            "counts": {
                "critical": len(criticals),
                "warning": len(warnings),
                "auto_fixable": auto_count,
            },
        }
        with open(args.json_report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n[json-report] {args.json_report}")

    print()
    if criticals:
        print("判定: FAIL -- CRITICAL が残存。Director差し戻し後に再実行すること")
        sys.exit(1)
    else:
        print("判定: PASS -- 全チェック通過。generatorへ進行可")
        sys.exit(0)


if __name__ == "__main__":
    main()
