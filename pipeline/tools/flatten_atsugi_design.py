# -*- coding: utf-8 -*-
"""厚木 統合CC 設計書を「フラット 1flow（決定論・patch_atsugi 不要）」へ変換する単発スクリプト。

入力 : output/scenarios/ヘルスケアクリニック厚木_統合CC/設計書_..._統合CC.yaml（subflow 形・OpenAI hearings）
出力 : output/scenarios/ヘルスケアクリニック厚木_統合CC_1flow/設計書_..._統合CC_1flow.yaml（フラット）

変換規則（権威 = tools/bivr_patches/patch_atsugi_deterministic_20260610.py の SITES と決定論 bivr）:
- 分類 hearing → hearing(output_format:text=STTのみ) + script(認定分類器・reference_module=入力_<聴取>) のペア。
  NO_RESULT は リトライ_<聴取step> へ（resolve がパススルー）。save はラベルを context へ（script.save_to）。
  その他コース確認だけは hearing が course 生テキストを保存・script は save 無し（SITES 準拠）。
- 明日以降確認/再受診希望 = yes_no_classifier。遅刻種別=checkup_intent SCOPE=lateness。
  用件=checkup_intent SCOPE=full。コース/その他コース=checkup_course。エリア/施設=checkup_menu(MENU)。
- 現在の予約日 = text hearing + stt_success_condition '^[0-9]{8}$' → 再受診希望（8 桁 DTMF ガード維持）。
- お問い合わせ内容 = text hearing（FAQ なし・そのまま）。
- 氏名/生年月日/電話番号 subflow → type:slot(patient_name/date_of_birth/phone)。flow_structure 1flow 化。
- CMR 施設確定後分岐 ref → <%classification%>。終話分岐_電話種別 ref → <%phonetype%>。
- context_fields に phonetype を追加。
"""
import io
import os
import sys
import copy

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "output", "scenarios", "ヘルスケアクリニック厚木_統合CC",
                   "設計書_ヘルスケアクリニック厚木_統合CC.yaml")
DST_DIR = os.path.join(ROOT, "output", "scenarios", "ヘルスケアクリニック厚木_統合CC_1flow")
DST = os.path.join(DST_DIR, "設計書_ヘルスケアクリニック厚木_統合CC_1flow.yaml")

# 分類 hearing → (認定部品, template_params, script.save_to, conditions[(match,next)])
# conditions の next は step 名（resolve が entry へ）/ リトライ_<step>（パススルー）。
CLASSIFY = {
    "明日以降確認": {
        "part": "yes_no_classifier", "params": {}, "save": None,
        "conds": [("肯定", "エリア選択"), ("否定", "遅刻種別確認"),
                  ("NO_RESULT", "リトライ_明日以降確認")],
    },
    "遅刻種別確認": {
        "part": "checkup_intent_classifier", "params": {"SCOPE": "lateness"}, "save": "classification",
        "conds": [("遅刻", "エリア選択"), ("変更", "END_当日受付不可"), ("キャンセル", "END_当日受付不可"),
                  ("NO_RESULT", "リトライ_遅刻種別確認"), ("other", "リトライ_遅刻種別確認")],
    },
    "用件確認": {
        "part": "checkup_intent_classifier", "params": {"SCOPE": "full"}, "save": "classification",
        "conds": [("予約", "コース選択"), ("変更", "変更受付案内"), ("キャンセル", "現在の予約日"),
                  ("その他", "お問い合わせ内容"), ("雇用時健診", "END_雇用時健診_HP案内"),
                  ("遅刻", "氏名聴取"), ("NO_RESULT", "リトライ_用件確認")],
    },
    "コース選択": {
        "part": "checkup_course_classifier", "params": {}, "save": "course",
        "conds": [("人間ドック", "氏名聴取"), ("協会けんぽ", "氏名聴取"), ("定期健診", "氏名聴取"),
                  ("雇用時健診", "END_雇用時健診_HP案内"), ("その他の健診", "その他コース確認"),
                  ("NO_RESULT", "リトライ_コース選択")],
    },
    "その他コース確認": {
        "part": "checkup_course_classifier", "params": {}, "save": None,  # course 生テキストは hearing が保存
        "conds": [("雇用時健診", "END_雇用時健診_HP案内"), ("NO_RESULT", "リトライ_その他コース確認"),
                  ("other", "氏名聴取")],
    },
    "再受診希望": {
        "part": "yes_no_classifier", "params": {}, "save": "rebooking",
        "conds": [("肯定", "氏名聴取"), ("否定", "氏名聴取"), ("NO_RESULT", "リトライ_再受診希望")],
    },
    "エリア選択": {
        "part": "checkup_menu_classifier", "params": {"MENU": "area"}, "save": "area",
        "conds": [("神奈川エリア", "施設案内_神奈川"), ("新宿渋谷エリア", "施設選択_新宿渋谷"),
                  ("東京品川エリア", "施設選択_東京品川"), ("NO_RESULT", "リトライ_エリア選択")],
    },
    "施設選択_新宿渋谷": {
        "part": "checkup_menu_classifier", "params": {"MENU": "shinjuku_shibuya"}, "save": "facility",
        "conds": [("ヒロオカクリニック", "施設確定後分岐"), ("渋谷ウエストクリニック", "施設確定後分岐"),
                  ("NO_RESULT", "リトライ_施設選択_新宿渋谷")],
    },
    "施設選択_東京品川": {
        "part": "checkup_menu_classifier", "params": {"MENU": "tokyo_shinagawa"}, "save": "facility",
        "conds": [("ヘルスケアクリニック秋葉原", "施設確定後分岐"), ("鉄鋼ビル丸の内クリニック", "施設確定後分岐"),
                  ("みなと健診クリニック", "施設確定後分岐"), ("NO_RESULT", "リトライ_施設選択_東京品川")],
    },
}

# subflow step → slot 種別
SLOT_MAP = {"氏名聴取": "patient_name", "生年月日聴取": "date_of_birth", "電話番号聴取": "phone"}


def _hearing_by_name(d, name):
    for h in d.get("hearing_items", []):
        if h.get("name") == name:
            return h
    return None


# フラット版のグループ日付サフィックス。元 subflow 版(_20260610)と混ざらないよう付け替える。
OLD_DATE = "_20260610"
NEW_DATE = "_20260617"


def transform(d):
    out = copy.deepcopy(d)

    # flow_structure: 1flow 化（subflows 撤去）
    flows = copy.deepcopy(d.get("flow_structure", {}).get("flows", []))
    for fl in flows:
        if isinstance(fl, dict) and fl.get("name"):
            fl["name"] = fl["name"].replace(OLD_DATE, NEW_DATE)
    out["flow_structure"] = {"type": "1flow", "flows": flows, "subflows": []}
    bi = out.get("basic_info", {})
    bi["flow_type"] = "1flow"
    # 日付サフィックス付け替え（group_name + flow_name。フラット版はサブフロー無し＝他の flowname 参照なし）。
    # naming_convention: _YYYYMMDD は group_name のみ、フロー名素・jump は group_name verbatim。
    for key in ("group_name", "flow_name"):
        if bi.get(key):
            bi[key] = bi[key].replace(OLD_DATE, NEW_DATE)

    # context_fields に phonetype を追加（未存在時）
    cf_names = {c.get("context_name") for c in out.get("context_fields", [])}
    if "phonetype" not in cf_names:
        out["context_fields"].append({
            "context_name": "phonetype", "context_name_jp": "電話種別",
            "display_type": "CLASSIFICATION",
            "range_values": [{"id": "1", "order": "1", "value": "携帯"},
                             {"id": "2", "order": "2", "value": "固定"},
                             {"id": "3", "order": "3", "value": "その他"}],
            "item_default": False, "editable": True, "deletable": False,
            "notes": "電話番号スロットの phone_type 結果。終話分岐_電話種別 が <%phonetype%> で参照。",
        })

    # scenario_flow 変換
    new_flow = []
    for blk in d["scenario_flow"]:
        step = blk.get("step")
        btype = blk.get("type")

        if btype == "hearing" and step in CLASSIFY:
            cfg = CLASSIFY[step]
            h = _hearing_by_name(d, step) or {}
            script_step = f"{step}_分類"
            # hearing(text): STT のみ。save_to は通常 ""、その他コース確認のみ course 生テキスト保存。
            hearing_save = "course" if step == "その他コース確認" else ""
            hearing_blk = {
                "step": step, "type": "hearing", "output_format": "text",
                "save_to": hearing_save, "next": script_step,
            }
            new_flow.append(hearing_blk)
            # script(認定分類器)
            tp = dict(cfg["params"]); tp["INPUT_MODULE"] = f"入力_{step}"
            script_blk = {
                "step": script_step, "type": "script",
                "script_template": cfg["part"],
                "reference_module": f"入力_{step}",
                "template_params": tp,
                "conditions": [{"match": m, "next": n} for m, n in cfg["conds"]],
            }
            if cfg["save"]:
                script_blk["save_to"] = cfg["save"]
            new_flow.append(script_blk)
            continue

        if step == "現在の予約日":
            # 8 桁 DTMF ガード: text hearing + stt_success_condition。生 8 桁が保存値。
            new_flow.append({
                "step": "現在の予約日", "type": "hearing", "output_format": "text",
                "save_to": "reservationDate", "stt_success_condition": "^[0-9]{8}$",
                "next": "再受診希望",
            })
            continue

        if btype == "subflow" and step in SLOT_MAP:
            slot = SLOT_MAP[step]
            save_map = {"patient_name": "patientName", "date_of_birth": "patientDateOfBirth",
                        "phone": "additionalPhoneNumber"}
            new_flow.append({
                "step": step, "type": "slot", "slot": slot,
                "save_to": save_map[slot], "next": blk.get("next"),
            })
            continue

        if btype == "context_match_router":
            nb = copy.deepcopy(blk)
            if step == "施設確定後分岐":
                nb["reference_module"] = "<%classification%>"
            elif step == "終話分岐_電話種別":
                nb["reference_module"] = "<%phonetype%>"
            new_flow.append(nb)
            continue

        # opening / announcement / termination / お問い合わせ内容(text hearing) はそのまま
        new_flow.append(copy.deepcopy(blk))

    out["scenario_flow"] = new_flow

    # hearing_items: 分類項目は openai_processing:none / output_format:text へ（分類は script 担当）
    for h in out.get("hearing_items", []):
        if h.get("name") in CLASSIFY:
            h["openai_processing"] = "none"
            h["output_format"] = "text"
        if h.get("name") == "現在の予約日":
            h["openai_processing"] = "none"
            h["output_format"] = "text"
            h["notes"] = (h.get("notes", "") + " / フラット化: STT を ^[0-9]{8}$ 直接ガード（分類器なし）。")

    # 念のため全文字列を再帰的に日付付け替え（flow_diagrams 等の残り group/flow 名参照を統一）。
    def _rename(o):
        if isinstance(o, dict):
            return {k: _rename(v) for k, v in o.items()}
        if isinstance(o, list):
            return [_rename(v) for v in o]
        if isinstance(o, str):
            return o.replace(OLD_DATE, NEW_DATE)
        return o
    out = _rename(out)
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    d = yaml.safe_load(io.open(SRC, encoding="utf-8"))
    out = transform(d)
    os.makedirs(DST_DIR, exist_ok=True)
    with io.open(DST, "w", encoding="utf-8", newline="\n") as f:
        yaml.safe_dump(out, f, allow_unicode=True, sort_keys=False, width=4096)
    print("[DONE] wrote", DST)
    # サマリ
    types = {}
    for b in out["scenario_flow"]:
        types[b["type"]] = types.get(b["type"], 0) + 1
    print("scenario_flow block types:", types)
    print("script blocks:", [b["step"] for b in out["scenario_flow"] if b["type"] == "script"])
    print("slot blocks:", [(b["step"], b["slot"]) for b in out["scenario_flow"] if b["type"] == "slot"])


if __name__ == "__main__":
    main()
