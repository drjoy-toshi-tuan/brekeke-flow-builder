"""
tools/csv_to_yaml.py — Sheet1 auto-filled CSV → 設計書 YAML

Input:
  --input   : raw_to_spec.py が出力した Sheet1_input.csv
  --facility: 施設名
  --flow    : フロー名
  --outdir  : 出力ディレクトリ（省略時は output/scenarios/<facility>_<flow>/）

Output:
  設計書_<facility>_<flow>.yaml

YAML 構造:
  basic_info / flow_structure / purpose / scenario_flow / step_details / termination_patterns

Notes:
  - scenario_flow は Sheet1 の順番通りの直線フローを生成（デフォルト）
  - choices が複数ある step（intent/hearing enum）は routing_hint 付きで出力
  - slot 系（patient_name/dob/phone/card_number）は scaffold が決定論展開するため type そのまま
  - TTS は step_details に {tts_g:...} 形式で出力
  - retry_failure はデフォルト end_failure。retry_next が指定されている場合は next step に接続
"""

import argparse
import csv
import re
import sys
from pathlib import Path
from datetime import date

# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def safe_id(name: str) -> str:
    return name.strip().replace(" ", "_").replace("　", "_")


def tts_wrap(text: str, step_name: str = "", field: str = "tts",
             missing_list: list | None = None) -> str:
    if not text:
        if missing_list is not None:
            missing_list.append((step_name, field))
        return "{tts_g:(要記入)}"
    return f"{{tts_g:{text}}}"


def load_sheet1(csv_path: str) -> list[dict]:
    rows = []
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            choices_raw = row.get("choices", "").strip()
            choices = [c.strip() for c in choices_raw.split("|") if c.strip()] if choices_raw else []
            amivoice_raw = row.get("amivoice_words", "").strip()
            amivoice = [w.strip() for w in amivoice_raw.split("|") if w.strip()] if amivoice_raw else []
            rows.append({
                "name":             row.get("聴取項目名", "").strip(),
                "canonical":        row.get("canonical名(auto)", "").strip() or row.get("聴取項目名", "").strip(),
                "tts":              row.get("TTS文言", "").strip(),
                "choices":          choices,
                "retry":            row.get("retry回数", "3").strip() or "3",
                "retry_next":       row.get("retry後遷移先", "").strip(),
                "reconfirm":        row.get("reconfirm", "なし").strip(),
                "amivoice":         amivoice,
                "block_type":       row.get("block_type(auto)", "hearing").strip(),
                "input_mode":       row.get("入力方式(auto)", "AmiVoice").strip(),
                "context_var":      row.get("context変数(auto)", "").strip(),
                "display_type":     row.get("display_type(auto)", "TEXT").strip(),
                "processing":       row.get("processing", "").strip(),
                "processing_note":  row.get("処理参照(自動)", "").strip(),
                "risk":             row.get("risk", "").strip(),
                "output_format":    row.get("output_format", "").strip(),
                "status":           row.get("状態", "").strip(),
            })
    return rows


# ---------------------------------------------------------------------------
# scenario_flow ブロック生成
# ---------------------------------------------------------------------------

SLOT_TYPES = {"patient_name", "dob", "phone", "card_number"}

# Sheet2 block_type 列の許容値（設計時検証①）。qa_validator KNOWN_BLOCK_TYPES +
# csv_to_yaml ローカルの特殊型（custom_scriptsN / Status_Sms）。
_S2_KNOWN_BLOCK_TYPES = {
    "opening", "announcement", "hearing", "subflow", "context_match_router",
    "script", "call_transfer", "termination", "augment",
    "incoming_category_classifier", "phone2name", "cmr_chain", "slot",
    "clinical_department_classifier", "dob", "phone", "patient_name",
    "intent", "phone_branch", "clinical_department", "clinical_department_normalize",
    "free_text", "faq", "card_number", "null_check", "clinic_day_default",
    "custom_scripts1", "custom_scripts2", "custom_scripts3", "Status_Sms",
}
NO_INPUT_TYPES = {"opening", "termination", "announcement"}
INTENT_TYPES = {"intent", "faq"}  # choice-gate blocks: cell value = choice, not custom name
# Sheet2 special block types
SCRIPT_BLOCK_TYPES = {"custom_scripts1", "custom_scripts2", "custom_scripts3"}
STATUS_SMS_TYPE = "Status_Sms"  # → type: termination, cell value = termination name


def _infer_amivoice_templates(row: dict) -> list[str]:
    """block_type/canonical名/choices から docs/specs/stt_dictionary_templates.json の
    use_template キーを推定する（機構: get_profile_words が amivoice_dictionary[].use_template
    を読み profile_words へ展開する。各項目ごとに適切な辞書を個別に当てる方針— 全項目共通の
    一律辞書は使わない）。該当なしなら空リスト（additional_words のみで運用）。
    """
    bt = row.get("block_type", "")
    name = row.get("name", "") or row.get("canonical", "")
    choices = row.get("choices") or []
    templates: list[str] = []

    if bt == "patient_name" or "氏名" in name or "名前" in name:
        templates.append("hearing_name")
    if bt == "clinical_department" or "診療科" in name:
        templates.append("hearing_shinryoka_basic")
    if bt == "phone" or "電話番号" in name or "連絡先" in name:
        templates.append("hearing_phone_number")
        templates.append("hearing_unknown")
    if bt == "card_number" or "診察券番号" in name or "登録番号" in name:
        templates.append("hearing_unknown")
    if bt == "intent" or "用件" in name:
        templates.append("hearing_yoken_common")
    if "コース" in name:
        templates.append("hearing_kenshin_course_basic")
    if any(k in name for k in ("予約日", "希望日", "変更日", "受診希望日")):
        templates.append("hearing_datetime")
    if "時間" in name and "何時" not in name:
        templates.append("hearing_time")
    if bt == "hearing" and set(choices) & {"はい", "いいえ"}:
        templates.append("hearing_yesno_common")
    if row.get("reconfirm") == "あり":
        templates.append("echo_back_yesno")

    seen: set = set()
    out: list[str] = []
    for t in templates:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


# ---------------------------------------------------------------------------
# Sheet_Script 読み込み
# ---------------------------------------------------------------------------

def load_sheet_termination(csv_path: str) -> list[dict]:
    """Sheet_Termination.csv → termination_patterns 用リスト。

    columns: 名前 / TTS / status / SMSフラグ / 完了フラグ / 適用ルート(コンマ区切り)
    status '0' は第3世代で使用禁止（qa E-8）のため '2' に正規化する。
    """
    patterns = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("名前") or "").strip()
            if not name:
                continue
            status = (row.get("status") or "1").strip()
            if status == "0":
                status = "2"
            tts = (row.get("TTS") or "").strip()
            patterns.append({
                "name": name,
                "condition": (row.get("適用ルート(コンマ区切り)") or "").strip() or "(要記入)",
                "tts_announcement": tts if tts.startswith("{tts_") else f"{{tts_g:{tts or '(要記入)'}}}",
                "status": status,
                "sms_flag": (row.get("SMSフラグ") or "-2").strip(),
                "completion_flag_name": (row.get("完了フラグ") or f"完了フラグ_{name.replace('END_', '', 1)}").strip(),
            })
    return patterns


def load_sheet_department(csv_path: str) -> list[dict]:
    """sheet_department.csv → [{canonical, synonyms, reading}]。

    決定論部品 department_classifier の spec データ（辞書）になる。LLM 不使用。
    columns: 診療科名(正式) / 類義語(|区切り) / 読み
    """
    rows = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("診療科名(正式)") or "").strip()
            if not name:
                continue
            syn = (row.get("類義語(|区切り)") or "").strip()
            rows.append({
                "canonical": name,
                "synonyms": [s.strip() for s in syn.split("|") if s.strip()],
                "reading": (row.get("読み") or "").strip(),
            })
    return rows


def load_sheet_faq(csv_path: str) -> list[dict]:
    """sheet_faq.csv → [{q, a, keywords}]。

    決定論部品 faq_matcher の spec データ（faq_map）になる。LLM 不使用。
    columns: 質問(正式) / 回答TTS / キーワード(|区切り)
    """
    rows = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            q = (row.get("質問(正式)") or "").strip()
            if not q:
                continue
            kw = (row.get("キーワード(|区切り)") or "").strip()
            rows.append({
                "q": q,
                "a": (row.get("回答TTS") or "").strip(),
                "keywords": [k.strip() for k in kw.split("|") if k.strip()],
            })
    return rows


def load_sheet_settings(csv_path: str) -> dict:
    """Sheet_Settings.csv → {キー: 値}。faq_mode 等の施設別設定を読む。"""
    settings = {}
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            k = (row.get("キー") or "").strip()
            v = (row.get("値") or "").strip()
            if k and v and v != "(要記入)":
                settings[k] = v
    return settings


def apply_faq_mode(blocks: list[dict], step_details: list[dict],
                   settings: dict, rows: list[dict]) -> None:
    """FAQ ブロックに faq_mode（standard / mismatch_tts / ari_nashi）を適用する。

    - 全モード共通: method=openai（SKILL_FAQ_Prompt 判定）+ 回答不要→next。
      回答読み上げ後はループせず next へ（2026-07-15 確定）。
    - mismatch_tts: OpenAI に FAQ不一致 分岐を追加 → 不一致案内 announcement → next
    - ari_nashi:   FAQ の前に あり/なし hearing を自動挿入（あり→FAQ / なし→next）
    """
    mode = settings.get("faq_mode", "standard")
    faq_idx = next((i for i, b in enumerate(blocks) if b.get("type") == "faq"), None)
    if faq_idx is None:
        return
    faq = blocks[faq_idx]
    faq_step = faq["step"]
    nxt = faq.get("next", "end_success")
    conds = faq.setdefault("conditions", [])
    faq["method"] = "openai"
    existing = {c.get("match") for c in conds}
    if "回答不要" not in existing:
        conds.append({"match": "回答不要", "next": nxt})

    if mode == "mismatch_tts":
        mm_step = f"FAQ不一致案内_{faq_step}"
        if "FAQ不一致" not in existing:
            conds.append({"match": "FAQ不一致", "next": mm_step})
        blocks.insert(faq_idx + 1, {"step": mm_step, "type": "announcement", "next": nxt})
        step_details.append({
            "step_name": mm_step,
            "tts_announcement": tts_wrap(settings.get("faq_mismatch_tts") or "(要記入 — 不一致時の案内文言)"),
            "input_method": "none", "retry_failure": "skip", "next_step": nxt,
        })

    elif mode == "ari_nashi":
        gate_step = f"FAQ有無確認_{faq_step}"
        # FAQ を指す next / conditions を gate に付け替え
        for b in blocks:
            if b is faq:
                continue
            if b.get("next") == faq_step:
                b["next"] = gate_step
            for c in (b.get("conditions") or []):
                if c.get("next") == faq_step:
                    c["next"] = gate_step
        blocks.insert(faq_idx, {
            "step": gate_step, "type": "hearing", "output_format": "enum",
            "options": ["あり", "なし"],
            "conditions": [{"match": "あり", "next": faq_step},
                           {"match": "なし", "next": nxt}],
            "retry_failure": "end_failure",
        })
        step_details.append({
            "step_name": gate_step,
            "tts_announcement": tts_wrap(settings.get("faq_ari_nashi_tts")
                                         or "他にご質問はありますか？「あり」「なし」でお答えください。"),
            "input_method": "voice_only", "retry_count": 3,
            "retry_failure": "end_failure", "next_step": faq_step,
        })


def load_sheet_script(csv_path: str) -> dict:
    """Sheet_Script.csv を読み込んで {参照ID: row_dict} を返す。

    参照ID は Sheet2 の custom_scripts1/2/3 の N と対応する。
    columns: 参照ID / ステップ名 / スクリプト種別 / 出力1〜5 / 次1〜5 / other→次 / スクリプト内容
    """
    result: dict[str, dict] = {}
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ref_id = (row.get("参照ID") or "").strip()
            if ref_id:
                result[ref_id] = {k: (v or "").strip() for k, v in row.items()}
    return result


# ---------------------------------------------------------------------------
# Sheet2 読み込み（マルチブランチ対応）
# ---------------------------------------------------------------------------

_S2_FIXED_COLS = {
    "Step(canonical)", "入力元(Sheet1)", "block_type", "input_mode",
    "output_format", "processing", "処理参照(自動)", "risk",
}


def load_sheet2(csv_path: str) -> dict:
    """Sheet2_flow.csv を読み込んでルート構造を返す。

    Returns:
        {
            "routes": ["予約ルート", "変更ルート", ...],
            "steps": [
                {
                    "canonical": "用件確認",
                    "block_type": "intent",
                    "output_format": "enum",
                    "processing": "script",
                    "processing_note": "SKILL_用件",
                    "risk": "high",
                    "routes": {
                        "予約ルート": "予約",        # choice gate
                        "変更ルート": "変更",
                        "キャンセルルート": "キャンセル",
                    }
                },
                {
                    "canonical": "診療科",
                    "block_type": "clinical_department",
                    ...
                    "routes": {
                        "予約ルート": "診療科_予約",  # custom name
                        "変更ルート": "診療科_変更",
                        # キャンセルルート: absent (not in this route)
                    }
                },
                ...
            ]
        }
    """
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        # ルート列 = 固定列でもヒント列でもない列
        route_cols = [h for h in headers
                      if h not in _S2_FIXED_COLS and not h.startswith("[")]

        steps = []
        for row in reader:
            route_cells: dict[str, str] = {}
            for rc in route_cols:
                cell = (row.get(rc) or "").strip()
                if cell:
                    route_cells[rc] = cell
            steps.append({
                "canonical":      (row.get("Step(canonical)") or "").strip(),
                "block_type":     (row.get("block_type") or "hearing").strip(),
                "input_mode":     (row.get("input_mode") or "AmiVoice").strip(),
                "output_format":  (row.get("output_format") or "").strip(),
                "processing":     (row.get("processing") or "").strip(),
                "processing_note":(row.get("処理参照(自動)") or "").strip(),
                "risk":           (row.get("risk") or "").strip(),
                "routes":         route_cells,
            })

    return {"routes": route_cols, "steps": steps}


def _s2_module_name(step: dict, route_col: str) -> str | None:
    """このステップがルートcolに存在するかを判定し、存在すればモジュール名を返す。

    セル値ルール:
      "✓"          → canonical名を使う
      intent/faq   → choice値（canonical名を維持）
      その他       → カスタムモジュール名
      ""           → このルートには含まれない → None
    """
    cell = step["routes"].get(route_col, "")
    if not cell:
        return None
    if cell == "✓":
        return step["canonical"]
    if step["block_type"] in INTENT_TYPES:
        return step["canonical"]  # choice gate; module name stays canonical
    return cell  # custom module name


def _s2_choice_gate(step: dict, route_col: str) -> str | None:
    """intent/faq ステップのルート入場条件 choice 値を返す（それ以外は None）。"""
    if step["block_type"] not in INTENT_TYPES:
        return None
    cell = step["routes"].get(route_col, "")
    if cell and cell != "✓":
        return cell
    return None


def build_scenario_flow_from_sheet2(
    sheet2: dict,
    sheet1_rows: list[dict],
    sheet_script: dict | None = None,
    route_end_map: dict | None = None,
) -> list[dict]:
    """Sheet2 のルート構造から scenario_flow ブロックリストを生成する。

    sheet_script: load_sheet_script() の戻り値。custom_scriptsN ブロックの展開に使用。
    アルゴリズム:
    1. 各ルートのステップ順序列を構築
    2. ユニークなモジュール名（登場順）を収集
    3. 各モジュールに対して next / conditions を決定してブロックを組み立てる
    """
    routes = sheet2["routes"]
    s2_steps = sheet2["steps"]

    # ---- 設計時検証①: block_type が既知の型か（fail-closed）----
    # 「UNKNOWN」等のドラフト残骸が YAML に素通りし、後段で F-3 / F-1 の雪崩になるのを
    # 入口で止める（実例: カレス Sheet2 ドラフトの block_type=UNKNOWN 6 行）。
    _unknown_types = [(s["canonical"], s["block_type"]) for s in s2_steps
                      if s["block_type"] not in _S2_KNOWN_BLOCK_TYPES]
    if _unknown_types:
        detail = ", ".join(f"'{c}'(type={t})" for c, t in _unknown_types)
        raise ValueError(
            f"[Sheet2 検証] 未知の block_type が {len(_unknown_types)} 行あります: {detail}\n"
            f"→ Sheet2 の block_type 列を確定してください（許容値: "
            f"{', '.join(sorted(_S2_KNOWN_BLOCK_TYPES))}）")

    # ---- Sheet1 逆引き（canonical / name でルックアップ）----
    s1_index: dict[str, dict] = {}
    for r in sheet1_rows:
        s1_index[r["canonical"]] = r
        s1_index[r["name"]] = r

    # ---- ステップ逆引き（canonical名 → sheet2 step dict）----
    s2_index: dict[str, dict] = {s["canonical"]: s for s in s2_steps}

    # ---- per-route シーケンス: [(step_dict, module_name, choice_gate_or_None)] ----
    route_seqs: dict[str, list[tuple]] = {}
    for rc in routes:
        seq = []
        for step in s2_steps:
            mn = _s2_module_name(step, rc)
            if mn is not None:
                gate = _s2_choice_gate(step, rc)
                seq.append((step, mn, gate))
        route_seqs[rc] = seq

    # ---- 設計時検証②: 同一モジュール名が同一ルートに複数回登場（Sheet2 行重複）----
    # 重複行があると next_in_route が自分自身を next に返し self-loop JSON になる
    # （実例: カレス Sheet2 ドラフトの 電話番号 ×2 行 → 電話番号.next=電話番号）。
    for rc in routes:
        _seen_mn: set = set()
        for _, _mn, _ in route_seqs[rc]:
            if _mn in _seen_mn:
                raise ValueError(
                    f"[Sheet2 検証] ルート '{rc}' にモジュール '{_mn}' が複数回登場します。"
                    f"Sheet2 の行重複を解消するか、別モジュールならルート列にカスタム名を"
                    f"指定して区別してください（fail-closed）")
            _seen_mn.add(_mn)

    # ---- ユニークモジュール名を登場順で収集 ----
    seen: set[str] = set()
    ordered: list[tuple[dict, str]] = []  # (step_dict, module_name)
    for rc in routes:
        for step, mn, _ in route_seqs[rc]:
            if mn not in seen:
                seen.add(mn)
                ordered.append((step, mn))

    # ---- モジュールごとの next を計算 ----
    def next_in_route(rc: str, module_name: str) -> str:
        seq = route_seqs[rc]
        for i, (_, mn, _) in enumerate(seq):
            if mn == module_name:
                return seq[i + 1][1] if i + 1 < len(seq) else "end_success"
        return None  # not in this route

    # ---- ルート分岐の自動ルーター化 ----
    # intent/faq ステップの choice gate（route → 選択肢ラベル）と save_to を控えておき、
    # ある step の next がルートで異なる場合に context_match_router を自動挿入する
    # （director 設計書の 用件ルーター と同型。従来は conflict エラーで人間差し戻し）。
    _gate_step = next((s for s in s2_steps if s["block_type"] in INTENT_TYPES), None)
    _route_gate = ({rc: _s2_choice_gate(_gate_step, rc) for rc in routes}
                   if _gate_step else {})
    _gate_save_to = "classification"
    if _gate_step:
        _gs1 = s1_index.get(_gate_step["canonical"]) or {}
        _gate_save_to = _gs1.get("context_var") or "classification"
    pending_routers: list[tuple] = []  # (owner_module_name, router_block)

    def next_or_router(mn: str, nexts: dict, btype_label: str) -> str:
        """next がルート間で一意ならそれを、分岐するなら自動ルーター名を返す。
        default（CMR フォールバック）は Sheet2 ルート列の最後のルートの next。"""
        unique = list(dict.fromkeys(nexts.values()))
        if not unique:
            return "end_success"
        if len(unique) == 1:
            if unique[0] == mn:
                raise ValueError(
                    f"[Sheet2 検証] block '{mn}' の next が自分自身を指しています"
                    f"（行重複 or ルート列の記載ミス）")
            return unique[0]
        # 分岐: 全ルートに choice gate ラベルがあれば CMR 自動挿入
        if _gate_step and all(_route_gate.get(rc) for rc in nexts):
            router_name = f"{mn}_ルーター"
            conds = [{"match": _route_gate[rc], "next": nx} for rc, nx in nexts.items()]
            conds.append({"match": "default", "next": list(nexts.values())[-1]})
            pending_routers.append((mn, {
                "step": router_name,
                "type": "context_match_router",
                "reference_module": f"<%{_gate_save_to}%>",
                "conditions": conds,
            }))
            return router_name
        detail = ", ".join(f"{rc}→{nx}" for rc, nx in nexts.items())
        raise ValueError(
            f"[Sheet2 conflict] block '{mn}' (type: {btype_label}) の next がルートで異なりますが、"
            f"intent/faq の choice gate が見つからず自動ルーター化できません: {detail}\n"
            f"→ Sheet2 でカスタム名を付けて分けるか、intent/faq ステップの各ルート列に"
            f"選択肢ラベルを記入してください")

    # ---- YAML ブロック構築 ----
    blocks = []
    for step, mn in ordered:
        btype = step["block_type"]
        s1 = s1_index.get(step["canonical"]) or s1_index.get(mn) or {}

        block: dict = {"step": mn, "type": btype}

        # --- opening ---
        if btype == "opening":
            block["use_acceptance_times"] = True
            nexts = {rc: next_in_route(rc, mn) for rc in routes
                     if next_in_route(rc, mn) is not None}
            unique_nexts = list(dict.fromkeys(nexts.values()))
            if len(unique_nexts) > 1:
                detail = ", ".join(f"{rc}→{nx}" for rc, nx in nexts.items())
                raise ValueError(
                    f"[Sheet2 conflict] opening block '{mn}' の next がルートで異なります: {detail}\n"
                    f"→ Sheet2 でカスタム名を付けて分けてください（同一ステップを複数行に分割）"
                )
            block["next"] = unique_nexts[0] if unique_nexts else "end_success"

        # --- slot types (決定論展開、scaffold が処理) ---
        elif btype in SLOT_TYPES:
            ctx = s1.get("context_var", "")
            if ctx:
                block["save_to"] = ctx
            # 復唱列「あり」→ echo_back: true を明示（scaffold の slot 既定:
            # patient_name=なし / dob・phone=あり を上書きできる。「なし」/空欄は
            # 既定のまま＝プリフィル「なし」で全施設の dob/phone 復唱が消えるのを防ぐ）
            if s1.get("reconfirm") == "あり":
                block["echo_back"] = True
            nexts = {rc: next_in_route(rc, mn) for rc in routes
                     if next_in_route(rc, mn) is not None}
            # ルート分岐は context_match_router を自動挿入（next_or_router）
            block["next"] = next_or_router(mn, nexts, btype)

        # --- intent / faq (conditions 生成) ---
        elif btype in INTENT_TYPES:
            block["output_format"] = step["output_format"] or "enum"
            ctx = s1.get("context_var", "classification")
            if ctx:
                block["save_to"] = ctx
            # conditions: choice → next
            conditions = []
            seen_choices: set[str] = set()
            for rc in routes:
                gate = _s2_choice_gate(step, rc)
                if gate and gate not in seen_choices:
                    seen_choices.add(gate)
                    nxt = next_in_route(rc, mn)
                    if nxt:
                        conditions.append({"match": gate, "next": nxt})
            if conditions:
                block["options"] = [c["match"] for c in conditions]
                block["conditions"] = conditions
            else:
                # フォールバック: 単純 next
                nexts_vals = [next_in_route(rc, mn) for rc in routes
                              if next_in_route(rc, mn)]
                block["next"] = nexts_vals[0] if nexts_vals else "end_success"
            block["retry_failure"] = _retry_failure_target(s1, sheet1_rows,
                                                           sheet1_rows.index(s1) if s1 in sheet1_rows else -1)

        # --- termination ---
        elif btype == "termination":
            block["termination_ref"] = mn

        # --- Status_Sms: e2e flow に置く termination 参照 ---
        elif btype == STATUS_SMS_TYPE:
            block["type"] = "termination"
            block["termination_ref"] = mn  # cell value = termination name (Sheet_Termination の 名前 列)

        # --- custom_scripts1/2/3: Sheet_Script 参照ID で展開 → type: script ---
        elif btype in SCRIPT_BLOCK_TYPES:
            ref_id = btype.replace("custom_scripts", "")
            block["type"] = "script"
            sc = (sheet_script or {}).get(ref_id, {})
            block["script_template"] = sc.get("スクリプト種別") or "custom"
            # 出力/次 分岐を branches リストに変換
            branches = []
            for n in range(1, 6):
                out = sc.get(f"出力{n}", "").strip()
                nxt = sc.get(f"次{n}", "").strip()
                if out and nxt:
                    branches.append({"output": out, "next": nxt})
            if branches:
                block["branches"] = branches
            other_nxt = sc.get("other→次", "").strip()
            if other_nxt:
                block["other_next"] = other_nxt
            else:
                # route sequence の next をフォールバックとして使う
                nexts = {rc: next_in_route(rc, mn) for rc in routes
                         if next_in_route(rc, mn) is not None}
                unique = list(dict.fromkeys(nexts.values()))
                block["other_next"] = unique[0] if unique else "end_failure"
            logic = sc.get("スクリプト内容", "").strip()
            block["template_params"] = {"logic": logic or "(要記入)"}
            block["_p6_warning"] = (
                "⚠️ P6受入テスト必須 — scripts/p6_acceptance/ にテストケースを追加してください"
            )

        # --- その他 (hearing, clinical_department, free_text, script, etc.) ---
        else:
            block["output_format"] = step["output_format"] or "text"
            ctx = s1.get("context_var", "")
            if ctx:
                block["save_to"] = ctx
            nexts = {rc: next_in_route(rc, mn) for rc in routes
                     if next_in_route(rc, mn) is not None}
            # ルート分岐は context_match_router を自動挿入（next_or_router）
            block["next"] = next_or_router(mn, nexts, btype)
            if btype not in NO_INPUT_TYPES:
                block["retry_failure"] = _retry_failure_target(
                    s1, sheet1_rows,
                    sheet1_rows.index(s1) if s1 in sheet1_rows else -1
                )

        blocks.append(block)

    # ---- 自動ルーターを所有ブロックの直後に挿入 ----
    for owner_mn, router_block in pending_routers:
        idx = next((i for i, b in enumerate(blocks) if b.get("step") == owner_mn), None)
        if idx is not None:
            blocks.insert(idx + 1, router_block)
        else:
            blocks.append(router_block)

    # ルート別終話（END_予約完了 等）が複数ある場合:
    # 合流後の末尾から context_match_router で classification により振り分ける
    if route_end_map and len(set(route_end_map.values())) >= 2:
        intent_step = next(
            (s for s in s2_steps if s["block_type"] in INTENT_TYPES
             and any(_s2_choice_gate(s, rc) for rc in routes)),
            None)
        if intent_step:
            s1i = s1_index.get(intent_step["canonical"], {})
            save_to = s1i.get("context_var") or "classification"
            cmr_conditions = []
            for rc in routes:
                gate = _s2_choice_gate(intent_step, rc)
                term = route_end_map.get(rc)
                if gate and term:
                    cmr_conditions.append({"match": gate, "next": term})
            if cmr_conditions:
                for b in blocks:
                    if b.get("next") == "end_success":
                        b["next"] = "終話振り分け"
                    for c in (b.get("conditions") or []):
                        if c.get("next") == "end_success":
                            c["next"] = "終話振り分け"
                blocks.append({
                    "step": "終話振り分け",
                    "type": "context_match_router",
                    # <%context名%> 直接参照形式（実機受入CMR-201〜211で検証済み）。
                    # save-{context} のモジュール名参照より単純で、subflow内保存値も参照できる。
                    "reference_module": f"<%{save_to}%>",
                    "conditions": cmr_conditions,
                })
    return blocks


def _retry_failure_target(row: dict, rows: list[dict], idx: int) -> str:
    """retry_next が '終話' / '次へ' / 空 → end_failure / next step / end_failure

    scenario_flow[].retry_failure 用。ここは実ステップ名を返してよい
    （qa_validator は scenario_flow の retry_failure に enum 制約を課さない）。
    """
    rn = row.get("retry_next", "")
    if not rn or rn == "終話":
        return "end_failure"
    if rn == "次へ":
        # 次のステップの canonical 名
        if idx + 1 < len(rows):
            return rows[idx + 1]["canonical"]
        return "end_failure"
    # 具体的なステップ名が書かれている場合
    return rn


def _retry_failure_keyword(row: dict) -> str:
    """step_details[].retry_failure 用。

    qa_validator E-2: step_details.retry_failure は
    ['disconnect', 'end_failure', 'skip'] のみ許容（実ステップ名は不可）。
    実際の遷移先は scenario_flow[].retry_failure（_retry_failure_target）が担う。
    """
    rn = row.get("retry_next", "")
    if rn == "次へ":
        return "skip"
    return "end_failure"


def build_scenario_flow(rows: list[dict]) -> list[dict]:
    blocks = []
    n = len(rows)

    for i, row in enumerate(rows):
        btype = row["block_type"]
        canonical = row["canonical"]
        next_step = rows[i + 1]["canonical"] if i + 1 < n else "end_success"

        block: dict = {"step": canonical, "type": btype}

        if btype == "opening":
            block["use_acceptance_times"] = True
            block["next"] = next_step

        elif btype == "termination":
            # termination は最後のステップ扱い
            block["type"] = "termination"
            # next は不要

        elif btype in SLOT_TYPES:
            # scaffold が決定論展開。save_to と next だけ指定
            if row["context_var"]:
                block["save_to"] = row["context_var"]
            # 復唱列「あり」→ echo_back: true を明示（Sheet2 経路と同じ規約）
            if row.get("reconfirm") == "あり":
                block["echo_back"] = True
            block["next"] = next_step

        elif btype in ("intent", "faq"):
            block["output_format"] = row["output_format"] or "enum"
            if row["context_var"]:
                block["save_to"] = row["context_var"]
            if row["choices"]:
                block["options"] = row["choices"]
                hint_lines = ["# ▼ Sheet2 推奨: 以下の choice ごとに next を設定してください:"]
                for c in row["choices"]:
                    hint_lines.append(f"#   {c} → (要設定)")
                hint_lines.append(f"#   デフォルト / 不一致 → {next_step}")
                block["routing_hint"] = "\n    ".join(hint_lines)
                block["next"] = next_step
            else:
                block["next"] = next_step
            block["retry_failure"] = _retry_failure_target(row, rows, i)

        elif btype == "clinical_department":
            block["output_format"] = "enum"
            if row["context_var"]:
                block["save_to"] = row["context_var"]
            block["next"] = next_step
            block["retry_failure"] = _retry_failure_target(row, rows, i)

        elif btype == "hearing":
            block["output_format"] = row["output_format"] or "text"
            if row["context_var"]:
                block["save_to"] = row["context_var"]
            if row["choices"] and (row["output_format"] or "") == "enum":
                block["choices"] = row["choices"]
                hint_lines = ["# ▼ Sheet2 推奨: 以下の choice ごとに next を設定してください:"]
                for c in row["choices"]:
                    hint_lines.append(f"#   {c} → (要設定)")
                hint_lines.append(f"#   デフォルト → {next_step}")
                block["routing_hint"] = "\n    ".join(hint_lines)
            block["next"] = next_step
            block["retry_failure"] = _retry_failure_target(row, rows, i)

        else:
            # free_text, script, etc.
            block["output_format"] = row["output_format"] or "text"
            if row["context_var"]:
                block["save_to"] = row["context_var"]
            block["next"] = next_step
            if btype not in NO_INPUT_TYPES:
                block["retry_failure"] = _retry_failure_target(row, rows, i)

        blocks.append(block)
    return blocks


# ---------------------------------------------------------------------------
# step_details 生成
# ---------------------------------------------------------------------------

def build_step_details(rows: list[dict],
                        missing_list: list | None = None) -> list[dict]:
    details = []
    n = len(rows)
    for i, row in enumerate(rows):
        btype = row["block_type"]
        if btype in SLOT_TYPES:
            # scaffold が自動処理するため step_details は最小限
            continue

        next_step = rows[i + 1]["canonical"] if i + 1 < n else "end_success"
        step_name = row["canonical"]
        d: dict = {
            "step_name": step_name,
            "tts_announcement": tts_wrap(row["tts"], step_name, "tts_announcement",
                                         missing_list),
        }

        if btype == "opening":
            d["input_method"] = "none"
            d["next_step"] = next_step
            d["retry_failure"] = "skip"
        elif btype in ("termination", "announcement"):
            d["input_method"] = "none"
            d["retry_failure"] = "skip"
            if btype == "announcement":
                d["next_step"] = next_step
        else:
            d["input_method"] = "dtmf_voice" if "DTMF" in row["input_mode"] else "voice_only"
            d["next_step"] = next_step

            retry = row["retry"]
            try:
                retry_count = int(retry) if retry else 3
            except ValueError:
                retry_count = 3
            d["retry_count"] = retry_count

            if retry_count > 0 and row["tts"]:
                d["retry_tts"] = tts_wrap(f"恐れ入りますが再度、{row['tts']}")

            if row["reconfirm"] == "あり":
                d["reconfirm"] = True
                d["reconfirm_tts"] = "{tts_g:(要記入 — 復唱文言)}"

            d["retry_failure"] = _retry_failure_keyword(row)
            if row["context_var"]:
                d["save_to"] = row["context_var"]
            if row["amivoice"]:
                d["amivoice_words"] = row["amivoice"]
            if row["processing_note"]:
                d["processing_ref"] = row["processing_note"]

        details.append(d)
    return details


# ---------------------------------------------------------------------------
# termination_patterns スケルトン
# ---------------------------------------------------------------------------

TERMINATION_SKELETON = [
    {
        "name": "END_通話完了",
        "condition": "全聴取完了",
        "tts_announcement": "{tts_g:(要記入)}",
        "status": "1",
        "sms_flag": "1",
        "completion_flag_name": "完了フラグ_通話完了",
    },
    {
        "name": "END_時間外",
        "condition": "受付時間外",
        "tts_announcement": "{tts_g:(要記入)}",
        "status": "6",
        "sms_flag": "-2",
        "completion_flag_name": "完了フラグ_時間外",
    },
    {
        "name": "END_非通知",
        "condition": "非通知着信",
        "tts_announcement": "{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}",
        "status": "2",
        "sms_flag": "-2",
        "completion_flag_name": "完了フラグ_非通知",
    },
    {
        "name": "END_聴取失敗",
        "condition": "retry 上限到達",
        "tts_announcement": "{tts_g:(要記入)}",
        "status": "2",
        "sms_flag": "-2",
        "completion_flag_name": "完了フラグ_聴取失敗",
    },
]


# ---------------------------------------------------------------------------
# YAML シリアライザ（ruamel/PyYAML 不要・手書き）
# ---------------------------------------------------------------------------

def _indent(level: int) -> str:
    return "  " * level


def _scalar(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    s = str(v)
    if any(c in s for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
        # エスケープが必要な場合はダブルクォート
        escaped = s.replace('\\', '\\\\').replace('"', '\\"')
        return f'"{escaped}"'
    if s == "" or s.lower() in ("true", "false", "null", "yes", "no"):
        return f'"{s}"'
    return s


def _serialize_value(val, level: int) -> str:
    ind = _indent(level)
    if isinstance(val, list):
        if not val:
            return "[]\n"
        lines = "\n"
        for item in val:
            if isinstance(item, dict):
                # list of dicts
                first = True
                for k, v in item.items():
                    prefix = f"{ind}- " if first else f"{ind}  "
                    first = False
                    lines += f"{prefix}{k}: {_serialize_value(v, level + 2)}"
                lines += "\n"
            else:
                lines += f"{ind}- {_scalar(item)}\n"
        return lines
    if isinstance(val, dict):
        lines = "\n"
        for k, v in val.items():
            lines += f"{ind}  {k}: {_serialize_value(v, level + 2)}"
        return lines
    if isinstance(val, str) and "\n" in val:
        # multiline → literal block
        lines = "|\n"
        for ln in val.split("\n"):
            lines += f"{ind}{ln}\n"
        return lines
    return f"{_scalar(val)}\n"


def serialize_section(key: str, val, level: int = 0) -> str:
    ind = _indent(level)
    if isinstance(val, list):
        lines = f"{ind}{key}:\n"
        for item in val:
            if isinstance(item, dict):
                first = True
                for k, v in item.items():
                    prefix = f"{ind}  - " if first else f"{ind}    "
                    first = False
                    if k.startswith("#"):
                        # comment
                        lines += f"{ind}    {k}\n"
                    else:
                        lines += f"{prefix}{k}: {_serialize_value(v, level + 3)}"
                lines += "\n"
            else:
                lines += f"{ind}  - {_scalar(item)}\n"
        return lines
    if isinstance(val, dict):
        lines = f"{ind}{key}:\n"
        for k, v in val.items():
            lines += serialize_section(k, v, level + 1)
        return lines
    if isinstance(val, str) and "\n" in val:
        lines = f"{ind}{key}: |\n"
        for ln in val.split("\n"):
            lines += f"{_indent(level + 1)}{ln}\n"
        return lines
    return f"{ind}{key}: {_scalar(val)}\n"


# ---------------------------------------------------------------------------
# メイン YAML 組み立て
# ---------------------------------------------------------------------------

def run_design_gates(yaml_text: str) -> list[tuple[str, str]]:
    """生成した YAML に qa_validator の設計時ゲート（V-1/V-2/S-1/S-2）を適用し、
    CRITICAL の (code, message) を返す。QA 工程を待たず生成時点で止めるための
    シフトレフト（ロジックは qa_validator と同一実装を共有・二重管理しない）。"""
    import yaml as _yaml
    schemas_dir = str(Path(__file__).resolve().parent.parent / "schemas")
    if schemas_dir not in sys.path:
        sys.path.insert(0, schemas_dir)
    try:
        import qa_validator as qv
    except ImportError as e:
        print(f"[WARN] qa_validator を読み込めないため設計時ゲートをスキップ: {e}",
              file=sys.stderr)
        return []
    try:
        d = _yaml.safe_load(yaml_text)
    except _yaml.YAMLError as e:
        return [("YAML", f"生成 YAML が parse できません: {e}")]
    if not isinstance(d, dict):
        return [("YAML", "生成 YAML のルートが辞書ではありません")]
    qv._issues.clear()
    qv.check_v1(d)
    qv.check_v2(d)
    qv.check_v3(d)
    qv.check_v5(d)
    qv.check_v6(d)
    qv.check_s1(d)
    qv.check_s2(d)
    criticals = [(i.code, i.message) for i in qv._issues if i.severity == "CRITICAL"]
    warnings = [(i.code, i.message) for i in qv._issues if i.severity == "WARNING"]
    qv._issues.clear()
    for code, msg in warnings:
        print(f"[設計時ゲート WARNING] {code}: {msg}", file=sys.stderr)
    return criticals


_N_CLINIC_DAY_RE = re.compile(r"([0-9０-９])\s*診療日")
_Z2H_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def apply_clinic_day_default(blocks: list[dict], rows_for_details: list[dict]) -> bool:
    """TTS の「〇月〇日」未確定プレースホルダー + 「N診療日」表記から、
    clinic_day_default ブロック（聴取なしで受付可能初日を自動計算する認定部品）を
    冒頭（アナウンスがあればその直後）に自動挿入し、TTS を <%availableDateFull%> に置換する。

    blockDays 導出: 「N診療日」= 今日を 1 日目として N 番目の診療日以降を受付
    → block_days = N - 1（例: 3診療日 → 2。今日が月曜・土日休診なら水曜を案内）。
    「N診療日」表記が見つからない場合は挿入せずスキップ（V-5 ゲートが 〇 残存を
    CRITICAL で止めるため、無言で誤った日数を仮定するより安全）。

    戻り値: 挿入したら True（context_fields へ availableDateFull を追加合成するフラグ）。
    """
    target_rows = [r for r in rows_for_details if "〇月〇日" in (r.get("tts") or "")]
    if not target_rows:
        return False

    n = None
    for r in target_rows:
        m = _N_CLINIC_DAY_RE.search(
            (r.get("canonical") or "") + " " + (r.get("name") or "") + " " + (r.get("tts") or ""))
        if m:
            n = int(m.group(1).translate(_Z2H_DIGITS))
            break
    if n is None:
        print("[csv_to_yaml] WARN: TTS に「〇月〇日」を検出しましたが「N診療日」表記が"
              "見つからず block_days を導出できません — clinic_day_default 自動挿入を"
              "スキップします（V-5 ゲートで停止・文言を確定してください）", file=sys.stderr)
        return False

    op_idx = next((i for i, b in enumerate(blocks) if b.get("type") == "opening"), None)
    if op_idx is None:
        print("[csv_to_yaml] WARN: opening ブロックが無いため clinic_day_default を"
              "挿入できません — スキップ", file=sys.stderr)
        return False

    # 挿入位置: opening 直後。直後が announcement（冒頭アナウンス）ならその後ろ。
    ins_idx = op_idx
    prev = blocks[op_idx]
    if op_idx + 1 < len(blocks) and blocks[op_idx + 1].get("type") == "announcement":
        ins_idx = op_idx + 1
        prev = blocks[ins_idx]

    step_name = "診療日基準日設定"
    block_days = max(0, n - 1)
    new_block = {
        "step": step_name,
        "type": "clinic_day_default",
        "block_days": block_days,
        "closed_day_mode": "土日祝日",
        "save_to": "availableDateFull",
        "next": prev.get("next", ""),
    }
    prev["next"] = step_name
    blocks.insert(ins_idx + 1, new_block)

    for r in target_rows:
        r["tts"] = r["tts"].replace("〇月〇日", "<%availableDateFull%>")

    print(f"[csv_to_yaml] clinic_day_default 自動挿入: {step_name}"
          f"（{n}診療日 → block_days={block_days}）/ TTS「〇月〇日」→"
          f" <%availableDateFull%>（{len(target_rows)} 行）", file=sys.stderr)
    return True


def build_yaml(rows: list[dict], facility: str, flow: str,
               sheet2: dict | None = None,
               sheet_script: dict | None = None,
               termination_patterns: list[dict] | None = None,
               departments: list[dict] | None = None,
               faqs: list[dict] | None = None,
               settings: dict | None = None) -> str:
    today = date.today().strftime("%Y/%m/%d")
    work_date = date.today().strftime("%Y%m%d")
    # E-16 / naming_convention.md: 日付サフィックスは group_name に集約
    group_name = f"{facility}_{flow}_{work_date}"
    flow_name = f"{group_name}${flow}"

    term_patterns = termination_patterns or TERMINATION_SKELETON

    # 適用ルート列 → ルート別終話マッピング（END_予約完了 等）
    route_end_map: dict = {}
    if sheet2 is not None and termination_patterns:
        for t in termination_patterns:
            cond = t.get("condition", "")
            for rc in sheet2["routes"]:
                if cond == rc:
                    route_end_map[rc] = t["name"]

    if sheet2 is not None:
        scenario_flow_blocks = build_scenario_flow_from_sheet2(
            sheet2, rows, sheet_script, route_end_map)
        # Sheet2 でどの route にも含まれない（全 route 列が空 = 孤立行）Sheet1 行を除外する。
        # build_step_details は元々 rows を無条件に走査していたため、Sheet2 で不使用と
        # 明示された行（例: 終話①/終話② の重複下書き）の生 TTS プレースホルダーが
        # scenario_flow に登場しないまま step_details にだけ残り、V-1 を誤検出させていた。
        used_canonicals = {s["canonical"] for s in sheet2["steps"] if s["routes"]}
        rows_for_details = [r for r in rows
                             if r["canonical"] in used_canonicals or r["name"] in used_canonicals]
    else:
        scenario_flow_blocks = build_scenario_flow(rows)
        rows_for_details = rows

    # 「〇月〇日」プレースホルダー + 「N診療日」表記 → clinic_day_default 自動挿入
    # （TTS を <%availableDateFull%> に置換。build_step_details より前に行うこと）
    clinic_day_inserted = apply_clinic_day_default(scenario_flow_blocks, rows_for_details)

    tts_missing: list = []
    step_details_list = build_step_details(rows_for_details, missing_list=tts_missing)

    # FAQ モード適用（standard / mismatch_tts / ari_nashi — Sheet_Settings faq_mode）
    if faqs:
        apply_faq_mode(scenario_flow_blocks, step_details_list, settings or {}, rows)

    term_names = [t["name"] for t in term_patterns]
    default_success = "END_通話完了" if "END_通話完了" in term_names else (
        next((t["name"] for t in term_patterns if t["status"] == "1"), term_names[0] if term_names else "END_通話完了"))
    default_failure = "END_聴取失敗" if "END_聴取失敗" in term_names else default_success

    # end_success / end_failure → 実 termination 名に張り替え（F-2 / E-10）
    def _map_end(v):
        if v == "end_success":
            return default_success
        if v == "end_failure":
            return default_failure
        return v

    existing_steps = {b["step"] for b in scenario_flow_blocks}
    for b in scenario_flow_blocks:
        if "next" in b:
            b["next"] = _map_end(b["next"])
        if "other_next" in b:
            b["other_next"] = _map_end(b["other_next"])
        if "retry_failure" in b:
            b["retry_failure"] = _map_end(b["retry_failure"])
        for c in (b.get("conditions") or []):
            if "next" in c:
                c["next"] = _map_end(c["next"])
    # step_details の retry_failure は張り替えない（E-2 許容値: disconnect/end_failure/skip）

    # termination ブロックを scenario_flow 末尾に追加（未登場のもののみ）
    for t in term_patterns:
        if t["name"] not in existing_steps:
            scenario_flow_blocks.append({
                "step": t["name"], "type": "termination",
                "termination_ref": t["name"],
            })

    lines = []

    # ヘッダーコメント
    lines.append(f"# 設計書 — {facility} {flow}")
    lines.append(f"# 生成元: tools/csv_to_yaml.py (raw_to_spec.py 出力から自動生成)")
    lines.append(f"# 生成日: {today}")
    lines.append(f"# ⚠️  TTS文言・business_hours・office_id は (要記入) 箇所を確認・修正してください")
    lines.append('version: "1.0"')
    lines.append("")

    # basic_info
    lines.append("# --- セクション1: 基本情報 ---")
    lines.append("basic_info:")
    lines.append(f'  facility_name: "{facility}"')
    lines.append(f'  scenario_name: "{flow}"')
    lines.append(f'  group_name: "{group_name}"')
    lines.append(f'  flow_name: "{flow_name}"')
    _settings = settings or {}
    lines.append(f'  office_id: "{_settings.get("office_id", "TODO_要確認")}"')
    lines.append(f'  phone_number: "{_settings.get("phone_number", "TODO_要確認")}"')
    lines.append(f'  business_hours: "{_settings.get("business_hours", "TODO_要確認")}"')
    lines.append(f'  flow_type: "1flow"')
    lines.append(f'  work_type: "new"')
    lines.append(f'  environment: "demo"')
    lines.append("")

    # flow_structure
    lines.append("# --- セクション2: フロー構成 ---")
    lines.append("flow_structure:")
    lines.append('  type: "1flow"')
    lines.append("  flows:")
    lines.append(f'    - name: "{flow_name}"')
    lines.append(f'      role: "main"')
    lines.append(f'      description: "CSV 入口（csv_to_yaml.py）から自動生成"')
    lines.append("")

    # purpose
    lines.append("# --- セクション3: フローの目的 ---")
    lines.append(f'purpose: "(要記入) — {facility}の{flow}フロー"')
    lines.append("")

    # scenario_flow
    lines.append("# --- セクション4: シナリオフロー定義（ブロック構成）---")
    lines.append("scenario_flow:")
    has_custom_scripts = any(
        b.get("type") == "script" and "_p6_warning" in b
        for b in scenario_flow_blocks
    )
    if has_custom_scripts:
        lines.append("# ⚠️ このフローにはカスタムスクリプトが含まれます。P6受入テスト必須。")
        lines.append("")

    for block in scenario_flow_blocks:
        routing_hint = block.pop("routing_hint", None)
        warning = block.pop("# WARNING", None)
        p6_warning = block.pop("_p6_warning", None)
        first = True
        for k, v in block.items():
            prefix = "  - " if first else "    "
            first = False
            if isinstance(v, list) and v and isinstance(v[0], dict):
                # conditions / choices リスト of dicts
                lines.append(f"{prefix}{k}:")
                for item in v:
                    item_first = True
                    for ik, iv in item.items():
                        item_prefix = "      - " if item_first else "        "
                        item_first = False
                        lines.append(f"{item_prefix}{ik}: {_scalar(iv)}")
            elif isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    lines.append(f"      - {_scalar(item)}")
            elif isinstance(v, bool):
                lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
            else:
                lines.append(f"{prefix}{k}: {_scalar(v)}")
        if routing_hint:
            lines.append(f"    {routing_hint}")
        if warning:
            lines.append(f"    {warning}")
        if p6_warning:
            lines.append(f"    # {p6_warning}")
        lines.append("")

    # step_details
    lines.append("# --- セクション5: ステップ詳細 ---")
    lines.append("step_details:")
    for d in step_details_list:
        first = True
        for k, v in d.items():
            prefix = "  - " if first else "    "
            first = False
            if isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    lines.append(f"      - {_scalar(item)}")
            elif isinstance(v, bool):
                lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
            else:
                lines.append(f"{prefix}{k}: {_scalar(v)}")
        lines.append("")

    # termination_patterns
    lines.append("# --- セクション6: 終話パターン ---")
    lines.append("termination_patterns:")
    for t in term_patterns:
        first = True
        for k, v in t.items():
            prefix = "  - " if first else "    "
            first = False
            lines.append(f"{prefix}{k}: {_scalar(v)}")
        lines.append("")

    # --- 工場デフォルト合成セクション（qa_validator T-1 必須12セクション対応）---

    # flow_diagrams（scenario_flow の簡易テキスト化）
    lines.append("# --- セクション7: フロー図（自動生成テキスト）---")
    lines.append("flow_diagrams:")
    lines.append(f'  - name: "{flow_name}"')
    lines.append("    diagram: |")
    for b in scenario_flow_blocks:
        head = f"[{b['step']}] {b['type']}"
        if b.get("next"):
            head += f" -> {b['next']}"
        lines.append(f"      {head}")
        for c in (b.get("conditions") or []):
            lines.append(f"          - {c.get('match', '')} -> {c.get('next', '')}")
    lines.append("")

    # context_fields（rows の context_var から合成）
    lines.append("# --- セクション8: コンテキストフィールド ---")
    lines.append("context_fields:")
    seen_ctx = set()
    if clinic_day_inserted:
        # clinic_day_default 自動挿入時: 受付可能初日（和文日付テキスト）の保存先を合成
        seen_ctx.add("availableDateFull")
        lines.append('  - context_name: "availableDateFull"')
        lines.append('    context_name_jp: "受付可能初日"')
        lines.append('    display_type: "TEXT"')
        lines.append('    description: "clinic_day_default が算出する受付可能初日（自動挿入）"')
    for row in rows:
        cv = row.get("context_var")
        if not cv or cv in seen_ctx:
            continue
        seen_ctx.add(cv)
        of = (row.get("output_format") or "").lower()
        cvl = cv.lower()
        if "date" in cvl or of == "datetime":
            dt = "DATE"
        elif "phone" in cvl:
            dt = "PHONE_NUMBER"
        elif "department" in cvl:
            dt = "DEPARTMENT"
        elif cv == "classification" or of == "enum":
            dt = "CLASSIFICATION"
        else:
            dt = "TEXT"
        lines.append(f'  - context_name: "{cv}"')
        lines.append(f'    context_name_jp: "{row["canonical"]}"')
        lines.append(f'    display_type: "{dt}"')
        lines.append(f'    description: "{row["canonical"]}（CSV 入口由来・自動生成）"')
        # choices 列がある enum 項目は rangeValues も合成（saveContextModel2DB の
        # Dr.JOY 画面プルダウン用。ContextModel2DB は enum を持たないと空プルダウンになる）。
        # ここで range_values を省略しても、scaffold_generator._enum_values_for_context が
        # scenario_flow の options[]（intent）/ choices[]（hearing enum）/ departments[]
        # （clinical_department）から自動合成する（2026-07-18〜 二重の安全網）。
        if row.get("choices"):
            lines.append("    range_values:")
            for ci, choice_val in enumerate(row["choices"], start=1):
                lines.append(f'      - value: "{choice_val}"')
                lines.append(f"        order: {ci}")
    if not seen_ctx:
        lines[-1] += " []"
    lines.append("")

    # hearing_items（聴取ステップの echo_back / retry_count）
    lines.append("# --- セクション9: 聴取項目 ---")
    lines.append("hearing_items:")
    any_hearing = False
    for row in rows_for_details:
        if row["block_type"] in NO_INPUT_TYPES or row["block_type"] == "termination":
            continue
        any_hearing = True
        try:
            rc = int(row["retry"]) if row["retry"] else 3
        except ValueError:
            rc = 3
        lines.append(f'  - name: "{row["canonical"]}"')
        lines.append(f"    echo_back: {'true' if row.get('reconfirm') == 'あり' else 'false'}")
        lines.append(f"    retry_count: {rc}")
        # E-2b: step_details.retry_failure と同値を明記（省略時に qa が 'end_failure' を
        # 仮定し、生成 YAML が自ゲートで FAIL する自己矛盾を防ぐ — #291）
        lines.append(f'    retry_failure: "{_retry_failure_keyword(row)}"')
        if row["context_var"]:
            lines.append(f'    save_to: "{row["context_var"]}"')
        if row["choices"]:
            lines.append("    output_labels:")
            for c in row["choices"]:
                lines.append(f'      - "{c}"')
    if not any_hearing:
        lines[-1] += " []"
    lines.append("")

    # tts_modules（TTS 文言カタログ）
    lines.append("# --- セクション10: TTS モジュール ---")
    lines.append("tts_modules:")
    any_tts = False
    for row in rows_for_details:
        if row.get("tts"):
            any_tts = True
            lines.append(f'  - module_name: "{row["canonical"]}"')
            lines.append(f'    announcement: {_scalar(tts_wrap(row["tts"]))}')
    if not any_tts:
        lines[-1] += " []"
    lines.append("")

    # amivoice_dictionary: 項目ごとに docs/specs/stt_dictionary_templates.json のテンプレを自動推定して
    # 割り当てる（未申告でも既定で入る＝2026-07-16 施設担当者BIVRレビュー指摘の恒久対応）。
    # CSV の amivoice_words 列（施設固有語彙・手入力）は additional_words として併載する。
    lines.append("# --- セクション11: AmiVoice 辞書（block_type から自動推定 + CSV amivoice_words 列を additional_words に反映）---")
    lines.append("amivoice_dictionary:")
    any_dict = False
    for row in rows:
        if row["block_type"] in NO_INPUT_TYPES:
            continue
        tpls = _infer_amivoice_templates(row)
        additional = "|".join(row.get("amivoice") or [])
        if not tpls and not additional:
            continue
        any_dict = True
        lines.append(f'  - step_name: "{row["canonical"]}"')
        if tpls:
            lines.append("    use_template:")
            for t in tpls:
                lines.append(f'      - "{t}"')
        if additional:
            additional_lines = "\n".join(w for w in row.get("amivoice") or [] if w)
            lines.append(f"    additional_words: |")
            for w_line in additional_lines.splitlines():
                lines.append(f"      {w_line}")
    if not any_dict:
        lines[-1] += " []"
    lines.append("")

    # special_notes / confirmation_items（壁打ちアジェンダ）
    lines.append("# --- セクション12: 特記事項・確認項目 ---")
    lines.append("special_notes:")
    lines.append('  - "本設計書は CSV 入口（tools/csv_to_yaml.py）から自動生成。"')
    lines.append('  - "TODO_要確認 は facility 固有値＝壁打ちで確定（confirmation_items にアジェンダ化）。"')
    lines.append("")
    lines.append("confirmation_items:")
    lines.append('  - item: "office_id"')
    lines.append('    description: "施設の Dr.JOY オフィス ID。施設台帳で確認"')
    lines.append(f"    resolved: {str(bool(_settings.get('office_id'))).lower()}")
    lines.append('  - item: "phone_number"')
    lines.append('    description: "このシナリオに割り当てる着信電話番号"')
    lines.append(f"    resolved: {str(bool(_settings.get('phone_number'))).lower()}")
    lines.append('  - item: "business_hours"')
    lines.append('    description: "受付時間（時間外判定に使用）"')
    lines.append(f"    resolved: {str(bool(_settings.get('business_hours'))).lower()}")
    lines.append("")

    # script_blocks（認定部品の spec データ。LLM 不使用 — CSV から決定論生成）
    if departments or faqs:
        lines.append("# --- セクション13: script_blocks（認定部品 spec データ・CSV 由来）---")
        lines.append("# ⚠️ spec 新規/変更時は P6 受入（part-certification-spec: engine既知・spec要受入）")
        lines.append("script_blocks:")
        if departments:
            dep_input = next((r["canonical"] for r in rows
                              if r["block_type"] == "clinical_department"), "診療科")
            lines.append("  - type: department")
            lines.append(f'    input_module: "{dep_input}"')
            lines.append("    departments:")
            for d in departments:
                lines.append(f"      - {_scalar(d['canonical'])}")
            lines.append("    synonyms:")
            for d in departments:
                if d["synonyms"]:
                    lines.append(f"      {d['canonical']}: [{', '.join(_scalar(s) for s in d['synonyms'])}]")
            lines.append("    readings:")
            for d in departments:
                if d["reading"]:
                    lines.append(f"      {d['canonical']}: {_scalar(d['reading'])}")
        if faqs:
            faq_input = next((r["canonical"] for r in rows
                              if r["block_type"] == "faq"), "FAQ")
            lines.append("  - type: faq")
            lines.append(f'    module_name: "script_{faq_input}"')
            lines.append(f'    faq_input_module: "{faq_input}"')
            lines.append("    faq_map:")
            for f in faqs:
                lines.append(f"      - q: {_scalar(f['q'])}")
                if f["a"]:
                    lines.append(f"        a: {_scalar(tts_wrap(f['a']))}")
                if f["keywords"]:
                    lines.append(f"        keywords: [{', '.join(_scalar(k) for k in f['keywords'])}]")
        lines.append("")

    if tts_missing:
        print(f"\n⚠️  TTS (要記入) が {len(tts_missing)} 箇所あります:", file=sys.stderr)
        for step, field in tts_missing:
            print(f"   - {step} [{field}]", file=sys.stderr)
        print("→ YAMLの該当箇所を検索: (要記入)", file=sys.stderr)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sheet1 CSV → 設計書 YAML\n\n"
                    "Sheet2 を指定するとマルチブランチ対応 YAML を生成します。\n"
                    "Sheet2 はまず raw_to_spec.py で生成し、ルート列を調整してから使用してください。",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--input",    required=True,
                        help="raw_to_spec.py が出力した Sheet1_input.csv パス")
    parser.add_argument("--sheet2",   default="",
                        help="Sheet2_flow.csv パス（省略時: Sheet1 直線フロー。指定時: ルート構造読み込み）")
    parser.add_argument("--sheet-script", default="",
                        help="Sheet_Script.csv パス（custom_scripts1/2/3 ブロックの展開に使用）")
    parser.add_argument("--sheet-termination", default="",
                        help="Sheet_Termination.csv パス（終話パターンをシートから生成。省略時はスケルトン）")
    parser.add_argument("--sheet-department", default="",
                        help="sheet_department.csv パス（診療科リスト → script_blocks/department spec）")
    parser.add_argument("--sheet-faq", default="",
                        help="sheet_faq.csv パス（FAQリスト → script_blocks/faq spec）")
    parser.add_argument("--sheet-settings", default="",
                        help="Sheet_Settings.csv パス（faq_mode 等の施設別設定）")
    parser.add_argument("--facility", required=True, help="施設名")
    parser.add_argument("--flow",     required=True, help="フロー名")
    parser.add_argument("--outdir",   default="",
                        help="出力ディレクトリ（省略時: output/scenarios/<facility>_<flow>/）")
    args = parser.parse_args()

    rows = load_sheet1(args.input)

    if not rows:
        print("ERROR: CSV が空です。", file=sys.stderr)
        sys.exit(1)

    unknown = [r for r in rows if r["status"] == "🔴"]
    if unknown:
        print(f"⚠️  未知の項目 {len(unknown)}件 — normalize できていません:")
        for r in unknown:
            print(f"  🔴 {r['name']}")
        print("  → normalize_dictionary.json に追加してから再実行してください。\n")

    sheet2 = None
    if args.sheet2:
        sheet2 = load_sheet2(args.sheet2)
        print(f"Sheet2 読み込み: {len(sheet2['routes'])} ルート, {len(sheet2['steps'])} ステップ")
        for rc in sheet2["routes"]:
            cnt = sum(1 for s in sheet2["steps"] if s["routes"].get(rc))
            print(f"  {rc}: {cnt} ステップ")

    sheet_script = None
    if args.sheet_script:
        sheet_script = load_sheet_script(args.sheet_script)
        print(f"Sheet_Script 読み込み: {len(sheet_script)} スクリプト定義")

    term_patterns = None
    if args.sheet_termination:
        term_patterns = load_sheet_termination(args.sheet_termination)
        print(f"Sheet_Termination 読み込み: {len(term_patterns)} 終話パターン")

    departments = load_sheet_department(args.sheet_department) if args.sheet_department else None
    if departments:
        print(f"sheet_department 読み込み: {len(departments)} 科")
    faqs = load_sheet_faq(args.sheet_faq) if args.sheet_faq else None
    if faqs:
        print(f"sheet_faq 読み込み: {len(faqs)} 件")

    settings = load_sheet_settings(args.sheet_settings) if args.sheet_settings else {}
    if settings.get("faq_mode"):
        print(f"faq_mode: {settings['faq_mode']}")

    yaml_text = build_yaml(rows, args.facility, args.flow, sheet2=sheet2,
                           sheet_script=sheet_script, termination_patterns=term_patterns,
                           departments=departments, faqs=faqs, settings=settings)

    # ── 設計時ゲート（生成器を直す原則・2026-07-16）──
    # qa_validator の V-1/V-2/S-1/S-2 を「生成直後」に実行し、CSV 入力起因の
    # TTS 変数/プレースホルダー・分岐配線・DTMFキー約束の不整合をここで止める。
    # QA 段まで問題を持ち越さない（QA はCSVを経由しない旧経路・P2 用の最終網）。
    design_criticals = run_design_gates(yaml_text)
    if design_criticals:
        print("\n❌ 設計時ゲートで CRITICAL を検出しました（YAML は書き出しません）:",
              file=sys.stderr)
        for code, msg in design_criticals:
            print(f"  [{code}] {msg}", file=sys.stderr)
        print("\n→ 該当する CSV（Sheet_TTS / Sheet1 の TTS 文言・choices・next）を"
              "修正して再実行してください", file=sys.stderr)
        sys.exit(1)

    # 出力先
    if args.outdir:
        out_dir = Path(args.outdir)
    else:
        out_dir = Path("output/scenarios") / f"{args.facility}_{args.flow}"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"設計書_{args.facility}_{args.flow}.yaml"
    out_path.write_text(yaml_text, encoding="utf-8")

    print(f"✓ {out_path}")
    print(f"\n次のステップ:")
    if sheet2:
        print(f"  1. {out_path} を開き conditions / next を確認・修正")
        print(f"  2. termination_patterns の TTS/status/smsFlag を記入")
        print(f"  3. python3 schemas/qa_validator.py {out_path} を実行して検証")
    else:
        print(f"  1. {out_path} を開き (要記入) 箇所を確認・修正")
        print(f"  2. routing_hint コメントを見て enum 分岐の next を設定")
        print(f"  3. python3 schemas/qa_validator.py {out_path} を実行して検証")
