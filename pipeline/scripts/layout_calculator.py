#!/usr/bin/env python3
"""
layout_calculator.py — Stage B: ブロックトップ位置を基準にブロック内モジュールを配置する

block_layout.py (Stage A) が決定した各ブロックのトップ位置を受けて、
ブロック型ごとに定義された slot 配置（block_layout_spec.py）に従って
全モジュールの (x, y) を確定し、JSON の layout フィールドを上書きする。

Usage:
    python3 scripts/layout_calculator.py <json_path> <spec_yaml_path> [output_path]
    output_path 省略時は json_path を上書き。

    スペック YAML が無い場合（scenario_flow 非採用の旧フロー）は、v1 互換の DAG-DFS に fallback する。
"""

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from block_layout_spec import (
    CELL_WIDTH, CELL_HEIGHT, BLOCK_HPAD,
    SUB_OFFSET_X, SUB_OFFSET_Y, COLS_PER_BLOCK,
    get_block_spec, BlockSpec,
)
from block_layout import extract_blocks_from_spec, assign_block_tops
from scaffold_generator import _short

# intent/free_text/clinical_department は scaffold_generator.py が hearing と同じ
# TTS→STT→(script|OpenAI)→Retry→save2db 構造で生成するため、layout 上は hearing 系として扱う
# （block_layout.py の対応する elif 節と同期させること）。
HEARING_FAMILY = ("hearing", "intent", "free_text", "clinical_department", "faq")


def load_layout_roles_sidecar(json_path: Path) -> dict:
    """scaffold_generator.py が書き出す scaffold_layout_roles_{stem}.json を読む。

    v2: {"version": 2, "blocks": {block_step: {module_name: slot_role}}}
        全 block type の membership を含む（slot_role 未記録は ""）。
    v1（後方互換）: {termination_ref: {module_name: slot_role}} のフラット形式。

    いずれも scaffold_generator が実際に生成したモジュール名の正本であり、
    これがあれば layout 側は所属ブロックを「推測」せずに済む。
    サイドカーが無い場合（旧バージョンの scaffold JSON 等）は空 dict を返し、
    呼び出し側は既存の推測ロジックにフォールバックする。
    """
    name = json_path.name
    if not name.startswith("scaffold_"):
        return {}
    sidecar = json_path.parent / f"scaffold_layout_roles_{name[len('scaffold_'):]}"
    if not sidecar.exists():
        return {}
    try:
        with open(sidecar, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    if isinstance(data, dict) and "version" in data:
        blocks = data.get("blocks", {})
        return blocks if isinstance(blocks, dict) else {}
    return data if isinstance(data, dict) else {}


# ─── モジュール名 → ブロック内 slot 役割の判定 ─────────────────
def _is_system_opening_module(name: str) -> tuple[bool, str]:
    """opening ブロックのシステム固定モジュールを識別"""
    if name == "冒頭":
        return True, "wait"
    if name == "コンテキスト設定":
        return True, "ContextModel"
    if name == "着信電話番号分類":
        return True, "incoming-classifier"
    if name == "受付時間判定":
        return True, "acceptance_times"
    return False, ""


def _classify_module_in_block(mod_name: str, block_step: str, block_type: str,
                              echo_back: bool, save_to: str = "",
                              dtmf_labels: list[str] | None = None,
                              cmr_chain_size: int = 0,
                              termination_ref: str = "",
                              slot_kind: str = "") -> tuple[str, bool]:
    """モジュール名が所属ブロックのどの slot 役割に対応するか判定。
    戻り値: (slot_role, is_submodule)
      slot_role が "" の場合は特定できない（副層に倒すか末尾に追加）
      is_submodule=True の場合は save-* 副層モジュール（SUB_OFFSET を適用）

    slot_kind: block_type=="slot" のときの slot 種別（patient_name/date_of_birth/
      phone/card_number）。date_of_birth と patient_name の言い直し確認チェーンは
      card_number の言い直しチェーンと同名モジュール（復唱_{step}/復唱_{step}_言い直し/
      入力_{step}_再確認/save-{step}_再確認）を使うため、判別に必須（2026-07-19）。
    """
    # hearing ブロックの共有 save2db: save-{save_to} or save-{step}（1ブロック1個）
    # 汎用 save- ハンドラより先に判定（save-classification 等が副層扱いにならないように）
    if block_type in HEARING_FAMILY and mod_name.startswith("save-"):
        if (save_to and mod_name == f"save-{save_to}") or mod_name == f"save-{block_step}":
            return "save2db", False
        # 復唱STT + 復唱Retry で共有される save2db（scaffold: save-{step}_復唱）。
        # echo_back=True の場合のみ実在するが、汎用 save- ハンドラ（再帰）より先に
        # 判定しないと解決できないためここで扱う。
        if echo_back and mod_name == f"save-{block_step}_復唱":
            return "save2db_復唱", False
        # clinical_department: 認定辞書に無い発話時の save2db（登録なし判定）。
        # 汎用 save- ハンドラ（再帰）より先に判定しないと解決できない。
        if mod_name == f"save-登録なし_{block_step}":
            return "save2db_登録なし", True

    # slot ブロック専用の save-* モジュール（モジュール名構造が一般規則と異なるため先に判定）
    if block_type == "slot" and mod_name.startswith("save-"):
        _step = block_step
        if mod_name == f"save-{_step}_ANI復唱":
            return "echo_ANI", True
        if mod_name == f"save-{_step}_連絡先復唱":
            return "echo_renrakusaki", True
        if mod_name == f"save-{_step}_ANI再確認":
            return "echo_ANI_sv", True
        if mod_name == f"save-{_step}_連絡先再確認":
            return "echo_ren_sv", True
        if mod_name == f"save-{_step}_確認":
            return "confirm_STT", True
        # 言い直しサルベージの save2db（否定+訂正の複合発話を再確認する1回のみのループ・
        # INC-260716-2）。date_of_birth/patient_name と card_number は同名
        # save-{step}_再確認 を使うが役割（対応する slot）が異なるため slot_kind で判別する。
        if mod_name == f"save-{_step}_再確認":
            return ("salvage_STT" if slot_kind == "card_number" else "confirm_STT_sv"), True
        # 個人情報4種インライン展開の save2db 共有モジュール（save-{save_to}）
        if save_to and mod_name == f"save-{save_to}":
            return "save2db", False

    # termination ブロック専用の save-*（汎用 save- ハンドラより先に判定しないと
    # termination_ref を引き継げず解決できない。上の hearing/slot と同じ理由）
    if block_type == "termination" and mod_name.startswith("save-"):
        _ref = termination_ref or block_step
        if mod_name == f"save-{_ref}":
            return "END_TTS", True

    # save-* 副層（TTS/STT/Retry の subs で参照される save2db のうち、上で捕まらなかったもの）
    if mod_name.startswith("save-"):
        parent = mod_name[5:]
        return (_classify_module_in_block(parent, block_step, block_type, echo_back, save_to,
                                          slot_kind=slot_kind)[0], True)
    if mod_name.startswith("saveDefault-"):
        # no_result_default 用の固定値 saveContext2DB。専用 slot に配置。
        inner = mod_name[len("saveDefault-"):]
        if inner.startswith("入力_"):
            return "saveDefault_STT", False
        elif inner.startswith("OpenAI_"):
            return "saveDefault_OAI", False
        # それ以外は副層扱い
        parent = inner
        return (_classify_module_in_block(parent, block_step, block_type, echo_back, save_to,
                                          slot_kind=slot_kind)[0], True)

    # opening 固定
    is_sys, role = _is_system_opening_module(mod_name)
    if is_sys:
        return role, False

    if block_type == "opening":
        # opening に属するがシステム外 → fallback
        return "", False

    if block_type == "announcement":
        if mod_name == block_step:
            return "TTS", False
        if mod_name == f"設定_{block_step}":
            return "設定", False

    if block_type in HEARING_FAMILY:
        if mod_name == block_step:
            return "TTS", False
        if mod_name == f"入力_{block_step}":
            return "STT", False
        if mod_name == f"OpenAI_{block_step}":
            return "OpenAI", False
        # 決定論化 Phase A/B: OpenAI の代わりに認定スクリプト（yes_no/n_choice）が同じ slot に入る
        if mod_name in (f"script_{block_step}", f"script_{block_step}_発話"):
            return "OpenAI", False
        # 全音声入力ブロック共通: STT → [repeat_filter] → 次 の間に挟む
        # もう一度/待って検出 Script（scaffold_generator.build_repeat_filter）
        if mod_name == f"script_repeat_filter_{block_step}":
            return "repeat_filter", False
        # faq: 回答読み上げ TTS
        if mod_name == f"FAQ回答_{block_step}":
            return "FAQ回答", False
        # faq (method: openai): 回答ルックアップ Script
        if mod_name == f"script_{block_step}_answer":
            return "script_answer", False
        if mod_name == f"リトライ_{block_step}":
            return "Retry", False
        # OpenAI TIMEOUT/ERROR フォールバック Scripts（scaffold が自動配置）
        if mod_name == f"script_{block_step}_fallback":
            return "script_fallback", False
        if echo_back:
            if mod_name == f"復唱_{block_step}":
                return "復唱", False
            if mod_name == f"入力_{block_step}_復唱":
                return "STT_復唱", False
            # script_{step}_復唱判定 = reservation_date_classifier の復唱後 Yes/No 判定
            # （build_yes_no_branch_script。他の enum/yes_no 系と役割は同じ「復唱後の判定」）
            if mod_name in (f"openAI_{block_step}_復唱", f"script_{block_step}_復唱",
                            f"script_{block_step}_復唱判定"):
                return "OpenAI_復唱", False
            if mod_name == f"リトライ_{block_step}_復唱":
                return "Retry_復唱", False
            if mod_name == f"ContextMatchRouter_{block_step}_復唱後":
                return "CMR_復唱後", False
            # 言い直しサルベージ（否定+訂正の複合発話から再抽出する1回のみのループ・
            # INC-260716-2）: date_of_call_classifier の日付版(_言い直し日付) と
            # enum(n_choice)版(_言い直し分類) のどちらも同じ「判定系」の1枠に集約する
            # （既存 STT の raw text を再解析するだけの Script で、専用 TTS/STT/Retry は伴わない）。
            if mod_name in (f"script_{block_step}_言い直し日付", f"script_{block_step}_言い直し分類"):
                return "言い直しサルベージ", False
        # 多段分岐（Script + per-group CMR）
        if mod_name == f"script_{block_step}_群分類":
            return "script_群分類", False
        import re as _re
        _cmr_group_m = _re.match(rf"^ContextMatchRouter_{_re.escape(block_step)}_群(\d+)$", mod_name)
        if _cmr_group_m:
            return f"CMR_群{_cmr_group_m.group(1)}", False

        # Pattern C: DTMF 分離 hearing の save_{step}_{label} を slot に割当
        if dtmf_labels:
            def _safe(s: str) -> str:
                return s.replace(" ", "_").replace("　", "_")
            for idx, label in enumerate(dtmf_labels):
                if mod_name == f"save_{block_step}_{_safe(label)}":
                    return f"save_label_{idx}", False

    if block_type == "cmr_chain":
        import re as _re
        _cm = _re.match(rf"^ContextMatchRouter_{_re.escape(block_step)}_chain_(\d+)$", mod_name)
        if _cm:
            return f"cmr_chain_{_cm.group(1)}", False

    if block_type == "subflow":
        # 個人情報聴取 wrapper 展開の場合は block_step に属する 4 連 jump の先頭のみ
        if mod_name.startswith("jump_"):
            return "jump", False
        # 単独 subflow（wrapper を介さず block_step 自身が Jump to Flow モジュール名）
        if mod_name == block_step:
            return "jump", False

    if block_type in ("context_match_router", "script",
                       "date_of_call_classifier", "call_transfer", "null_check", "augment"):
        if mod_name in (block_step, f"script_{block_step}"):
            return "box", False

    if block_type == "termination":
        # 終話チェーン: 完了フラグ / END_ / 切断
        if mod_name.startswith("完了フラグ_"):
            return "完了フラグ", False
        if mod_name.startswith("END_"):
            return "END_TTS", False
        if mod_name.startswith("切断_"):
            return "切断", False
        # termination_patterns の name（ref）が "END_" プレフィックス無しの場合
        # （命名規則違反だが、慣習未遵守を理由に所属不明へ落とさない。
        #  save-{ref} は汎用 save- ハンドラより前の専用チェックで既に捕まえている）
        ref = termination_ref or block_step
        if mod_name == ref:
            return "END_TTS", False

    if block_type == "slot":
        step = block_step
        if mod_name == step:
            return "TTS", False
        if mod_name == f"入力_{step}":
            return "STT", False
        # 全音声入力ブロック共通: STT → [repeat_filter] → 次 の間に挟む
        # もう一度/待って検出 Script（scaffold_generator.build_repeat_filter）
        if mod_name == f"script_repeat_filter_{step}":
            return "repeat_filter", False
        if mod_name == f"リトライ_{step}":
            return "Retry", False
        # date_of_birth / patient_name(echo_back時) 共有の確認チェーン。
        # 「復唱_{step}」は card_number の echo_TTS（復唱なしTTS）と同名のため、
        # slot_kind で判別する（card_number は下の専用セクションで拾う）。
        if slot_kind != "card_number":
            if mod_name == f"復唱_{step}":
                return "DOB_reconf", False
            if mod_name == f"入力_{step}_確認":
                return "confirm_STT", False
            if mod_name == f"リトライ_{step}_確認":
                return "confirm_Retry", False
            if mod_name == f"script_{step}_確認分類":
                return "yes_no_script", False
            # 言い直しサルベージ（否定+訂正の複合発話を再確認する1回のみのループ・
            # INC-260716-2）。「入力_{step}_再確認」「復唱_{step}_言い直し」は
            # card_number の同名モジュールと役割が異なるため、この if 節（非 card_number）
            # の中で先に判定する。
            if mod_name == f"復唱_{step}_言い直し":
                return "DOB_reconf_sv", False
            if mod_name == f"入力_{step}_再確認":
                return "confirm_STT_sv", False
            if mod_name == f"リトライ_{step}_再確認":
                return "confirm_Retry_sv", False
            if mod_name == f"script_{step}_再確認分類":
                return "yes_no_script_sv", False
        # phone 追加モジュール（slot phone v2 — docs/specs/slot_phone_v2.md）
        if mod_name == f"着信分類_{step}":
            return "incoming", False
        # 全音声入力ブロック共通: もう一度/待って検出（電話番号は base STT / 連絡先 STT 各々に付く）
        if mod_name == f"script_repeat_filter_{step}_連絡先":
            return "repeat_filter_連絡先", False
        if mod_name == f"正規化_{step}_ANI":
            return "norm_ANI", False
        if mod_name == f"復唱_{step}_ANI":
            return "echo_ANI", False
        if mod_name == f"入力_{step}_ANI確認":
            return "confirm_STT_ANI", False
        if mod_name == f"リトライ_{step}_ANI確認":
            return "retry_ANI_confirm", False
        if mod_name == f"script_{step}_ANI確認分類":
            return "script_ANI", False
        if mod_name == f"正規化_{step}_ANI言い直し":
            return "norm_ANI_sv", False
        if mod_name == f"復唱_{step}_ANI言い直し":
            return "echo_ANI_sv", False
        if mod_name == f"入力_{step}_ANI再確認":
            return "confirm_STT_ANI_sv", False
        if mod_name == f"リトライ_{step}_ANI再確認":
            return "retry_ANI_sv", False
        if mod_name == f"script_{step}_ANI再確認分類":
            return "script_ANI_sv", False
        if mod_name == f"聴取_{step}_連絡先":
            return "TTS_renrakusaki", False
        if mod_name == f"入力_{step}_連絡先":
            return "STT_renrakusaki", False
        if mod_name == f"リトライ_{step}_連絡先":
            return "retry_renrakusaki", False
        if mod_name == f"正規化_{step}_連絡先":
            return "norm_renrakusaki", False
        if mod_name == f"復唱_{step}_連絡先":
            return "echo_renrakusaki", False
        if mod_name == f"入力_{step}_連絡先確認":
            return "confirm_STT_ren", False
        if mod_name == f"リトライ_{step}_連絡先確認":
            return "retry_ren_confirm", False
        if mod_name == f"script_{step}_連絡先確認分類":
            return "script_ren", False
        if mod_name == f"正規化_{step}_連絡先言い直し":
            return "norm_ren_sv", False
        if mod_name == f"復唱_{step}_連絡先言い直し":
            return "echo_ren_sv", False
        if mod_name == f"入力_{step}_連絡先再確認":
            return "confirm_STT_ren_sv", False
        if mod_name == f"リトライ_{step}_連絡先再確認":
            return "retry_ren_sv", False
        if mod_name == f"script_{step}_連絡先再確認分類":
            return "script_ren_sv", False
        if mod_name == f"設定_{step}_ANIフォールバック":
            return "fallback_set", False
        if mod_name == f"script_{step}_連絡先なし判定":
            return "nashi_mrb", False
        # phone 副層 save-* モジュール (save-{step}_ANI復唱 等, 親モジュール名と構造が異なるため明示)
        if mod_name == f"save-{step}_ANI復唱":
            return "echo_ANI", True
        if mod_name == f"save-{step}_連絡先復唱":
            return "echo_renrakusaki", True
        if mod_name == f"save-{step}_ANI再確認":
            return "echo_ANI_sv", True
        if mod_name == f"save-{step}_連絡先再確認":
            return "echo_ren_sv", True
        # date_of_birth 副層 save-* モジュール
        if mod_name == f"save-{step}_確認":
            return "confirm_STT", True
        # card_number 追加モジュール
        if mod_name == f"script_{step}":
            return "script", False
        if mod_name == f"復唱_{step}":
            return "echo_TTS", False
        if mod_name == f"入力_{step}_復唱":
            return "echo_STT", False
        if mod_name == f"リトライ_{step}_復唱":
            return "echo_Retry", False
        if mod_name == f"script_{step}_復唱確認":
            return "echo_script", False
        # 言い直しサルベージ（否定+訂正の複合発話を拾う1回のみのループ・INC-260716-2・
        # slot phone/dob と同型）。「入力_{step}_再確認」「復唱_{step}_言い直し」は
        # date_of_birth/patient_name の同名モジュールと役割が異なるが、上のセクションは
        # slot_kind!="card_number" でガード済みのため、slot_kind=="card_number" のときは
        # ここまで到達してから拾われる。
        if mod_name == f"script_{step}_言い直し":
            return "salvage_extract", False
        if mod_name == f"復唱_{step}_言い直し":
            return "salvage_TTS", False
        if mod_name == f"入力_{step}_再確認":
            return "salvage_STT", False
        if mod_name == f"script_{step}_再確認判定":
            return "salvage_judge", False
        # 副層 save-* モジュール
        if mod_name.startswith("save-") or mod_name.startswith("save-入力_"):
            parent = mod_name[5:]
            role, _ = _classify_module_in_block(parent, block_step, block_type, echo_back, save_to,
                                                slot_kind=slot_kind)
            return role, True

    return "", False


# ─── モジュール → 所属ブロック の逆引き ───────────────────────
def build_module_to_block_map(blocks: list[dict], modules: dict,
                              layout_roles: dict | None = None) -> dict[str, dict]:
    """モジュール名 → 所属ブロック情報（辞書 step/type/echo_back/top） のマップ"""
    layout_roles = layout_roles or {}
    mod_to_block: dict[str, dict] = {}
    # 1. opening システム固定モジュール
    opening = next((b for b in blocks if b["type"] == "opening"), None)
    if opening:
        for m in ("冒頭", "コンテキスト設定", "着信電話番号分類", "受付時間判定"):
            if m in modules:
                mod_to_block[m] = opening

    # 2. 各ブロックごとに所属モジュールを列挙。
    #    scaffold_generator の layout_roles サイドカー（membership の正本）にエントリが
    #    あるブロックはそれをそのまま使い、無いブロックのみ従来の命名規則推測に
    #    フォールバックする（旧 scaffold JSON・block_layout が合成した擬似ブロック等）。
    for b in blocks:
        step  = b["step"]
        btype = b["type"]
        echo  = b.get("echo_back", False)

        sidecar_key = b.get("termination_module_ref") or step
        sidecar_entry = layout_roles.get(sidecar_key)
        if sidecar_entry:
            for mn in sidecar_entry:
                if mn in modules:
                    mod_to_block[mn] = b
            continue

        if btype == "opening":
            continue  # 既に割当済み
        elif btype == "announcement":
            # save_to + save_value 指定時（定数セット手段）は 設定_{step}（saveContext2DB）が追加生成される
            for mn in (step, f"save-{step}", f"設定_{step}"):
                if mn in modules:
                    mod_to_block[mn] = b
        elif btype in HEARING_FAMILY:
            save_to = b.get("save_to", "")
            candidates = [step, f"save-{step}", f"入力_{step}", f"save-入力_{step}",
                          f"OpenAI_{step}", f"リトライ_{step}", f"save-リトライ_{step}",
                          f"saveDefault-入力_{step}", f"saveDefault-OpenAI_{step}",
                          # 決定論化 Phase A/B: OpenAI 代替の認定スクリプト
                          f"script_{step}", f"script_{step}_発話", f"script_{step}_復唱",
                          # OpenAI TIMEOUT/ERROR フォールバック（scaffold が自動配置）
                          f"script_{step}_fallback",
                          # faq (method: openai): 回答ルックアップ Script
                          f"script_{step}_answer",
                          # 全音声入力ブロック共通: もう一度/待って検出（scaffold が自動配置）
                          f"script_repeat_filter_{step}",
                          # clinical_department: 認定辞書に無い発話時の save2db
                          f"save-登録なし_{step}",
                          # faq: 回答読み上げ TTS
                          f"FAQ回答_{step}"]
            # save2db 共有モジュール: scaffold は save-{save_to} で命名
            if save_to and save_to != step:
                candidates.append(f"save-{save_to}")
            if echo:
                # save-{step}_復唱 は 復唱STT + 復唱Retry で共有される1個の save2db
                # （scaffold_generator.py: echo_save = f"save-{step}_復唱"）。
                # "save-入力_{step}_復唱" / "save-リトライ_{step}_復唱" という名前のモジュールは
                # 実際には生成されない（過去の誤った想定）。
                candidates += [f"復唱_{step}", f"入力_{step}_復唱",
                               f"save-{step}_復唱", f"openAI_{step}_復唱",
                               f"リトライ_{step}_復唱",
                               f"ContextMatchRouter_{step}_復唱後"]
            # 多段分岐（Script + per-group CMR）
            candidates.append(f"script_{step}_群分類")
            for gi in range(1, 11):
                candidates.append(f"ContextMatchRouter_{step}_群{gi}")
            # Pattern C: DTMF 分離 hearing の save_{step}_{label} 群
            if b.get("input_method") == "dtmf_split":
                def _safe(s: str) -> str:
                    return s.replace(" ", "_").replace("　", "_")
                for opt in (b.get("dtmf_options") or []):
                    if not isinstance(opt, dict):
                        continue
                    label = opt.get("label", "")
                    if not label or opt.get("action", "save") == "replay":
                        continue
                    candidates.append(f"save_{step}_{_safe(label)}")
            for mn in candidates:
                if mn in modules:
                    mod_to_block[mn] = b
        elif btype == "cmr_chain":
            refs = b.get("reference_modules", []) or []
            for i in range(len(refs)):
                mn = f"ContextMatchRouter_{step}_chain_{i}"
                if mn in modules:
                    mod_to_block[mn] = b
        elif btype == "subflow":
            # 個人情報聴取 wrapper は step + jump_氏名聴取 等を含む
            if step in modules:
                mod_to_block[step] = b
            for jump_target in ("jump_氏名聴取", "jump_生年月日聴取",
                                "jump_診察券番号聴取", "jump_電話番号聴取"):
                if jump_target in modules and jump_target not in mod_to_block:
                    # 個人情報聴取 wrapper の展開されたチェーン要素
                    # 所属は wrapper ブロック（step が jump_個人情報聴取 等）
                    mod_to_block[jump_target] = b
        elif btype == "slot":
            slot_kind = b.get("slot", "")
            save_to = b.get("save_to", "")
            candidates = [
                step,
                f"入力_{step}",
                f"リトライ_{step}",
                # 全音声入力ブロック共通: もう一度/待って検出（scaffold が自動配置）
                f"script_repeat_filter_{step}",
            ]
            if save_to:
                candidates.append(f"save-{save_to}")
            if slot_kind == "date_of_birth":
                candidates += [
                    f"復唱_{step}",
                    f"入力_{step}_確認",
                    f"リトライ_{step}_確認",
                    f"script_{step}_確認分類",
                    f"save-{step}_確認",
                ]
            elif slot_kind == "phone":
                candidates += [
                    f"着信分類_{step}",
                    f"設定_{step}_ANI番号",
                    f"正規化_{step}_ANI",
                    f"save-{step}_ANI復唱",
                    f"復唱_{step}_ANI",
                    f"入力_{step}_ANI確認",
                    f"リトライ_{step}_ANI確認",
                    f"script_{step}_ANI確認分類",
                    f"聴取_{step}_連絡先",
                    f"入力_{step}_連絡先",
                    f"script_repeat_filter_{step}_連絡先",
                    f"リトライ_{step}_連絡先",
                    f"正規化_{step}_連絡先",
                    f"save-{step}_連絡先復唱",
                    f"復唱_{step}_連絡先",
                    f"入力_{step}_連絡先確認",
                    f"リトライ_{step}_連絡先確認",
                    f"script_{step}_連絡先確認分類",
                    f"設定_{step}_ANIフォールバック",
                    f"script_{step}_種別判別",
                    f"設定_{step}_phonetype携帯",
                    f"設定_{step}_phonetypeその他",
                    f"script_{step}_連絡先なし判定",  # next_no_phone 指定時のみ
                    # ANI/連絡先の再確認（言い直し）チェーン — slot_phone の2段階目
                    f"正規化_{step}_ANI言い直し",
                    f"save-{step}_ANI再確認",
                    f"復唱_{step}_ANI言い直し",
                    f"入力_{step}_ANI再確認",
                    f"リトライ_{step}_ANI再確認",
                    f"script_{step}_ANI再確認分類",
                    f"正規化_{step}_連絡先言い直し",
                    f"save-{step}_連絡先再確認",
                    f"復唱_{step}_連絡先言い直し",
                    f"入力_{step}_連絡先再確認",
                    f"リトライ_{step}_連絡先再確認",
                    f"script_{step}_連絡先再確認分類",
                ]
                # save-{save_to} は additionalPhoneNumber 等; 上で追加済み
            elif slot_kind == "card_number":
                candidates += [
                    # _build_card_number_block は save_to に関わらず save_sub=f"save-{step}" 固定
                    # （patient_name/date_of_birth/phone の save-{save_to} 規則とは異なる）
                    f"save-{step}",
                    f"script_{step}",
                    f"save-入力_{step}_復唱",
                    f"復唱_{step}",
                    f"入力_{step}_復唱",
                    f"リトライ_{step}_復唱",
                    f"script_{step}_復唱確認",
                ]
            for mn in candidates:
                if mn in modules:
                    mod_to_block[mn] = b
        elif btype in ("context_match_router", "script",
                        "date_of_call_classifier", "call_transfer", "null_check", "augment"):
            for mn in (step, f"script_{step}"):
                if mn in modules:
                    mod_to_block[mn] = b
        elif btype == "termination":
            # ※ サイドカーがあるブロックはループ冒頭で処理済み。ここは無い場合の推測フォールバック。
            # モジュール名は termination_ref（term_patterns の name）から生成される。
            # scenario_flow の step（例: "END_受付完了"）はグラフ traversal 専用で、
            # ref（例: "受付完了"）と異なることがあるため、ref を優先して使う。
            ref = b.get("termination_module_ref") or step
            short = _short(ref)
            flag_name = b.get("completion_flag_name") or f"完了フラグ_{short}"
            for mn in (flag_name, ref, f"save-{ref}", f"切断_{short}"):
                if mn in modules:
                    mod_to_block[mn] = b

    return mod_to_block


# ─── Stage B: ブロック内モジュールを配置 ───────────────────────
def calculate_layout(modules: dict, blocks: list[dict],
                     block_tops: dict[str, tuple[int, int]],
                     layout_roles: dict | None = None
                     ) -> tuple[dict[str, tuple[int, int]], dict[str, list]]:
    """全モジュールの (x, y) を計算して返す。

    layout_roles: scaffold_generator.py 由来のロールマップ（現状 termination のみ）。
      {termination_ref: {module_name: slot_role}}。与えられた場合、対応する
      block type は推測ロジックの代わりにこれを正本として使う。

    戻り値: (pos, diagnostics)
      diagnostics["unclassified"] : どのブロックにも属さなかったモジュール名のリスト
                                     （命名不一致バグの兆候。呼び出し側は CRITICAL 扱い推奨）
      diagnostics["slot_unresolved"]: ブロックには属したが slot 役割を特定できず
                                     ブロックトップに retreat したモジュール
                                     (mod_name, block_step, block_type) のリスト
    """
    layout_roles = layout_roles or {}
    mod_to_block = build_module_to_block_map(blocks, modules, layout_roles)
    pos: dict[str, tuple[int, int]] = {}
    unclassified: list[str] = []
    slot_unresolved: list[tuple[str, str, str]] = []

    # 個人情報聴取 wrapper の 4 連 jump を chain 内で縦に配置するためのカウンタ
    wrapper_jump_order = ["jump_個人情報聴取", "jump_氏名聴取",
                          "jump_生年月日聴取", "jump_電話番号聴取"]

    for mod_name in modules.keys():
        b = mod_to_block.get(mod_name)
        if not b:
            # 所属不明 → あとで末尾に詰める
            unclassified.append(mod_name)
            continue
        step  = b["step"]
        btype = b["type"]
        echo  = b.get("echo_back", False)
        top_x, top_y = block_tops.get(step, (0, 0))

        input_method = b.get("input_method", "voice_only")
        spec = get_block_spec(btype, echo, input_method, slot_kind=b.get("slot", ""))
        save_to = b.get("save_to", "")
        # Pattern C: dtmf_labels と cmr_chain_size を渡す
        dtmf_labels: list[str] = []
        if btype == "hearing" and input_method == "dtmf_split":
            for opt in (b.get("dtmf_options") or []):
                if isinstance(opt, dict) and opt.get("label") and opt.get("action", "save") != "replay":
                    dtmf_labels.append(opt["label"])
        cmr_chain_size = len(b.get("reference_modules", []) or []) if btype == "cmr_chain" else 0
        termination_ref = b.get("termination_module_ref", "") if btype == "termination" else ""

        # サイドカーに slot_role の明示記録があればそれを正本とする。
        # membership のみ記録（role=""）のモジュールは None 扱い → 従来ロジックで role 判定。
        sidecar_key = termination_ref or step
        sidecar_role = (layout_roles.get(sidecar_key, {}).get(mod_name) or None)

        guessed_role, guessed_is_sub = _classify_module_in_block(
            mod_name, step, btype, echo, save_to,
            dtmf_labels=dtmf_labels, cmr_chain_size=cmr_chain_size,
            termination_ref=termination_ref, slot_kind=b.get("slot", ""))

        if sidecar_role is not None:
            if sidecar_role != guessed_role:
                print(f"[layout] NOTICE: '{mod_name}' の slot_role が推測({guessed_role!r})と "
                      f"layout_roles サイドカー({sidecar_role!r})で不一致。サイドカーを優先します。",
                      file=sys.stderr)
            slot_role, is_sub = sidecar_role, mod_name.startswith("save-")
        else:
            slot_role, is_sub = guessed_role, guessed_is_sub

        # 個人情報聴取 wrapper 特殊処理: 4 連 jump を縦に積む
        if btype == "subflow" and mod_name in wrapper_jump_order and step == "jump_個人情報聴取":
            idx = wrapper_jump_order.index(mod_name)
            pos[mod_name] = (top_x, top_y + idx * CELL_HEIGHT)
            continue

        slot = spec.slots.get(slot_role)
        if slot is None:
            # slot 特定不能 → ブロックトップに配置
            slot_unresolved.append((mod_name, step, btype))
            pos[mod_name] = (top_x, top_y)
            continue

        col_off, row_off = slot
        x = top_x + col_off * (CELL_WIDTH + BLOCK_HPAD)
        y = top_y + row_off * CELL_HEIGHT

        if is_sub:
            x += SUB_OFFSET_X
            y += SUB_OFFSET_Y

        pos[mod_name] = (x, y)

    # 所属不明モジュールは右端下に詰める
    if len(pos) < len(modules):
        fallback_x = max((x for x, _ in pos.values()), default=0) + 400
        fallback_y = 0
        for mn in modules:
            if mn not in pos:
                pos[mn] = (fallback_x, fallback_y)
                fallback_y += CELL_HEIGHT

    diagnostics = {"unclassified": unclassified, "slot_unresolved": slot_unresolved}
    return pos, diagnostics


# ─── JSON 書き換え ─────────────────────────────────────────────
def apply(modules: dict, pos: dict[str, tuple[int, int]]) -> None:
    for name, mod in modules.items():
        if name in pos:
            x, y = pos[name]
            mod.setdefault("layout", {})
            mod["layout"]["x"] = x
            mod["layout"]["y"] = y


# ─── CLI ────────────────────────────────────────────────────────
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: layout_calculator.py <json_path> [spec_yaml_path] [output_path]",
              file=sys.stderr)
        sys.exit(1)

    json_path = Path(sys.argv[1])
    if not json_path.exists():
        print(f"Error: {json_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    # 第 2 引数: 設計書 YAML（省略可。指定時のみブロックレイアウト適用）
    spec_path: Path | None = None
    output_path: Path = json_path
    if len(sys.argv) >= 3:
        p = Path(sys.argv[2])
        if p.suffix in (".yaml", ".yml") and p.exists():
            spec_path = p
            if len(sys.argv) >= 4:
                output_path = Path(sys.argv[3])
        else:
            output_path = p

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    modules = data.get("modules", {})

    # 設計書 YAML が指定され、scenario_flow を持つ場合は block-based レイアウト
    if spec_path and yaml is not None:
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
        blocks = extract_blocks_from_spec(spec)
        if blocks:
            block_tops = assign_block_tops(blocks)
            layout_roles = load_layout_roles_sidecar(json_path)
            pos, diagnostics = calculate_layout(modules, blocks, block_tops, layout_roles)
            apply(modules, pos)

            slot_unresolved = diagnostics["slot_unresolved"]
            if slot_unresolved:
                print(f"[layout] WARNING: slot 特定不能でブロックトップに配置したモジュールが"
                      f"{len(slot_unresolved)}件あります（block_layout.py/layout_calculator.py の"
                      f"命名判定漏れの可能性）:", file=sys.stderr)
                for mn, step, btype in slot_unresolved:
                    print(f"  - {mn}  (block={step}, type={btype})", file=sys.stderr)

            unclassified = diagnostics["unclassified"]
            if unclassified:
                print(f"[layout] ERROR: どのブロックにも分類できなかったモジュールが"
                      f"{len(unclassified)}件あります（所属不明・命名不一致バグの兆候）。"
                      f"scaffold_generator.py が生成したモジュール名と "
                      f"block_layout.py/layout_calculator.py の判定ロジックがずれています:",
                      file=sys.stderr)
                for mn in unclassified:
                    print(f"  - {mn}", file=sys.stderr)
                sys.exit(1)

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
            print(f"[layout] {len(pos)} モジュールを block-based レイアウトで配置", file=sys.stderr)
            print(str(output_path))
            return

    # YAML 未指定 or scenario_flow 不在 → エラー終了（サイレントフォールバック禁止）
    if not spec_path:
        print("[layout] ERROR: 設計書 YAML が指定されていません。"
              "第2引数に spec_yaml_path を渡してください。", file=sys.stderr)
    elif yaml is None:
        print("[layout] ERROR: PyYAML が利用できません。", file=sys.stderr)
    else:
        print("[layout] ERROR: 設計書 YAML に scenario_flow が無い、"
              "またはブロック抽出に失敗しました。", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
