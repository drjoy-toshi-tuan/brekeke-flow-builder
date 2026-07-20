# -*- coding: utf-8 -*-
"""scenario_from_drawio.py — enriched drawio → VFB 設計書 YAML（工場入口の生成側）。

drawio_to_scenario の寛容パーサで業務構造を取り出し、**工場デフォルト**（drawio に
載らない実現知識: input_method / retry_failure / termination の status・sms_flag /
subflow flowname 等）を合成して、scaffold_generator が食える設計書 YAML を組む。

設計（project-governance/initiatives/vfb-factory-restructure.md §2-1, 2026-06-22）:
  「ベース数値・分岐方法・ブロック配置は工場が持つ」= drawio はビジネス構造だけ運び、
  実現知識は工場デフォルトが埋める。埋められない facility 固有値は TODO で残し
  qa_validator / surfacing が壁打ちアジェンダとして出す。

使い方:
  python scenario_from_drawio.py <設計.drawio> -o <設計書.yaml>

stdlib + PyYAML（pre-install 済前提・インストール禁止方針）。
"""
import sys
import os
import datetime
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drawio_to_scenario import parse_drawio, build_scenario_flow, _hardened_parser  # noqa: E402

try:
    import yaml
except ImportError:
    print("Error: PyYAML が必要（pre-install 前提・インストール禁止）", file=sys.stderr)
    sys.exit(1)

TODO = "TODO_要確認"

# 工場デフォルト: 終話名（部分一致）→ (status, sms_flag, condition)
# SMS 既定は 0/送らない（feedback_sms_flag_default）。受付完了系のみ携帯=1。
# SMS 既定: 送らない=0（-1 は録音分割バグで禁止・scaffold が矯正する／feedback_sms_flag_default）。
# 受付完了_携帯 のみ 1（送信）。
TERM_DEFAULTS = [
    ("非通知", ("2", "0", "非通知着信")),
    ("時間外", ("6", "0", "受付時間外")),
    ("聴取失敗", ("3", "0", "リトライ上限到達")),
    ("受付完了_携帯", ("1", "1", "受付完了 かつ phonetype=携帯")),
    ("受付完了_固定", ("1", "0", "受付完了 かつ phonetype=その他")),
    ("代表案内", ("2", "0", "用件が聞き取れない / 受け皿")),
]

# context_name(ASCII) → 画面表示用 日本語名（contextNameJp）。
# 未収載の context は「最初にその context を保存するステップ名」（日本語）でフォールバック。
CONTEXT_JP_NAMES = {
    "classification":        "区分",
    "clinicalDepartment":    "診療科",
    "reservationDate":       "受診希望日",
    "currentReservationDate": "現在の予約日",
    "patientName":           "氏名",
    "patientDateOfBirth":    "生年月日",
    "medicalCardNumber":     "診察券番号",
    "telephoneNumber":       "着信元電話番号",
    "additionalPhoneNumber": "連絡先電話番号",
    "reason":                "用件",
}

# slot_type（catalog feature.id）→ subflow ターゲット名（flowname の末尾）
SLOT_SUBFLOW = {
    "氏名": "氏名聴取",
    "生年月日": "生年月日聴取",
    "診察券番号": "診察券番号聴取",
    "電話番号": "電話番号聴取",
}


def extract_title(path):
    """フロー図 title セル（"<施設名>  <シナリオ名>"）を返す。"""
    tree = ET.parse(path, parser=_hardened_parser())
    for d in tree.getroot().findall("diagram"):
        model = d.find("mxGraphModel")
        root = model.find("root") if model is not None else None
        if root is None:
            continue
        for el in list(root):
            if el.tag == "mxCell" and el.get("id") == "title":
                return el.get("value", "")
    return ""


def _term_defaults(name):
    for key, vals in TERM_DEFAULTS:
        if key in name:
            return vals
    return (TODO, "0", TODO)  # 未知終話: status は壁打ち、SMS は既定 0


def _split_title(title):
    """"さくら内科クリニック  診療" → (facility, scenario)。"""
    parts = [p for p in title.replace("　", " ").split("  ") if p.strip()]
    if len(parts) >= 2:
        return parts[0].strip(), parts[-1].strip()
    if parts:
        return parts[0].strip(), ""
    return TODO, ""


def _today_yyyymmdd():
    """作業日サフィックス（工場デフォルト＝生成日）。E-16 / naming_convention.md。"""
    return datetime.date.today().strftime("%Y%m%d")


def _display_type(save_to, output_format):
    """save_to 名 + output_format → context_fields の display_type（VALID_DISPLAY_TYPES）。"""
    s = (save_to or "").lower()
    if s.endswith("date") or output_format == "datetime":
        return "DATE"
    if "department" in s:
        return "DEPARTMENT"
    if "phone" in s:
        return "PHONE_NUMBER"
    if save_to == "classification" or output_format == "enum":
        return "CLASSIFICATION"
    return "TEXT"


def build_spec(nodes, edges, title, work_date=None):
    """nodes/edges + 工場デフォルト → 設計書 spec(dict)。

    work_date: 作業日サフィックス（YYYYMMDD）。未指定なら生成日（_today_yyyymmdd）。
    """
    work_date = work_date or _today_yyyymmdd()
    facility, scenario = _split_title(title)
    # 命名規則（E-16 / naming_convention.md）: 日付サフィックスは group_name に集約し、
    # flow_name・全 flowname 参照は同じ dated group_name を prefix に揃える。
    group_name = f"{facility}_{scenario}_{work_date}" if scenario else f"{facility}_{work_date}"
    flow_name = f"{group_name}${scenario}" if scenario else f"{group_name}$main"
    blocks = build_scenario_flow(nodes, edges)
    node_by_step = {n["step"]: n for n in nodes}

    # 冒頭（最初の announce 系ブロック）を opening に昇格
    opening_step = None
    for b in blocks:
        if b["type"] != "termination":
            opening_step = b["step"]
            break

    scenario_flow, step_details, hearing_items, subflows = [], [], [], []
    term_steps = []
    seen_subflows = set()
    context_used = {}        # save_to -> output_format（context_fields 合成元・初出を採用）
    main_intent_labels = []  # 最初の用件分岐ラベル（purpose 文言に使用）

    def _register_subflow(flowname, target, recitation):
        if flowname not in seen_subflows:
            seen_subflows.add(flowname)
            subflows.append({"name": flowname, "target": target,
                             "recitation": recitation,
                             "transition_module": "drjoy^Custom Module$Custom Jump to Flow",
                             "termination": "return"})

    for b in blocks:
        n = node_by_step.get(b["step"], {})
        slot = b.get("slot_type", "")
        sf = {"step": b["step"]}

        if b["type"] == "termination":
            sf["type"] = "termination"
            sf["termination_ref"] = b["step"]
            term_steps.append(b["step"])
        elif b.get("reference_module"):
            # CMR は slot_type を併せ持つことがある（forall の forward 注釈）→ ref を優先判定
            sf["type"] = "context_match_router"
            sf["reference_module"] = b["reference_module"]
            sf["conditions"] = b.get("conditions", [])
        elif slot in SLOT_SUBFLOW:
            # 個人情報 = 標準 subflow（factory-v2 は非フラット。flowname を工場デフォルトで合成）
            sf["type"] = "subflow"
            sf["flowname"] = f"{group_name}${SLOT_SUBFLOW[slot]}"
            _register_subflow(sf["flowname"], SLOT_SUBFLOW[slot],
                              "あり" if n.get("repeat") == "あり" else "なし")
            if b.get("next"):
                sf["next"] = b["next"]
        elif "RAG" in b["step"] or "FAQ" in b["step"]:
            sf["type"] = "subflow"
            sf["flowname"] = f"{group_name}$FAQ検索"
            _register_subflow(sf["flowname"], "FAQ検索", "なし")
            if b.get("next"):
                sf["next"] = b["next"]
        elif b["step"] == opening_step:
            sf["type"] = "opening"
            sf["use_acceptance_times"] = True
            if b.get("next"):
                sf["next"] = b["next"]
        elif b.get("output_format"):
            sf["type"] = "hearing"
            sf["output_format"] = b["output_format"]
            if b.get("conditions"):
                # 宣言ラベル = drawio 記載 match（受け皿 other は除外）
                labels = [c.get("match", "") for c in b["conditions"]
                          if c.get("match") and c.get("match") not in ("other", "default", "*")]
                if labels:
                    sf["output_labels"] = labels
                    if not main_intent_labels:
                        main_intent_labels = labels
                sf["conditions"] = b["conditions"]
            elif b.get("next"):
                sf["next"] = b["next"]
        else:
            sf["type"] = "announcement"
            if b.get("next"):
                sf["next"] = b["next"]

        scenario_flow.append(sf)

        # step_details（announce/ save_to を持つ実ステップ）+ 工場デフォルト
        announce = n.get("announce", "")
        save_to = b.get("save_to", "")
        if announce or save_to:
            sd = {"step_name": b["step"]}
            if announce:
                sd["tts_announcement"] = announce
            if sf["type"] == "hearing":
                sd["input_method"] = "dtmf_voice" if b.get("output_format") == "datetime" else "voice_only"
                sd["retry_failure"] = "end_failure" if save_to else "skip"
            else:
                sd["input_method"] = "voice_only"
                sd["retry_failure"] = "skip"
            if save_to:
                sd["save_to"] = save_to
                # 初出のステップ（日本語名）を context_name_jp フォールバックに使う
                context_used.setdefault(save_to, {"output_format": b.get("output_format", ""),
                                                   "jp": b["step"]})
            step_details.append(sd)

        # hearing_items（echo_back / retry_count の工場デフォルト）
        if sf["type"] == "hearing":
            hearing_items.append({
                "name": b["step"],
                "echo_back": n.get("repeat") == "あり",
                "retry_count": 2,
            })

    # termination_patterns（status/sms_flag を工場デフォルトで合成）+ TODO 採取
    termination_patterns = []
    todos = [
        ("office_id", "施設の Dr.JOY オフィス ID（office_id）。施設台帳 / Mazrica で確認"),
        ("phone_number", "このシナリオに割り当てる着信電話番号。確認"),
    ]
    for name in term_steps:
        n = node_by_step.get(name, {})
        status, sms, cond = _term_defaults(name)
        if status == TODO:
            todos.append((f"{name}.status",
                          f"終話 '{name}' の status は工場デフォルトで決まらないため確認"))
        termination_patterns.append({
            "name": name, "condition": cond,
            "tts_announcement": n.get("announce", ""),
            "status": status, "sms_flag": sms,
            "completion_flag_name": "完了フラグ_" + name.replace("END_", "", 1),
        })

    # context_fields（step_details.save_to から合成）。
    # display_type は SYSTEM_CONTEXT_OVERRIDES が既知 context を上書きするため、ここでは推定値で可。
    # context_name_jp は CONTEXT_JP_NAMES → 初出ステップ名 の順でフォールバック。
    context_fields = [
        {"context_name": k,
         "context_name_jp": CONTEXT_JP_NAMES.get(k, meta["jp"]),
         "display_type": _display_type(k, meta["output_format"]),
         "description": f"{k}（drawio save_to 由来・自動生成）"}
        for k, meta in context_used.items()
    ]

    # tts_modules（step_details の announce をカタログ化）
    tts_modules = [
        {"module_name": sd["step_name"], "announcement": sd["tts_announcement"]}
        for sd in step_details if sd.get("tts_announcement")
    ]

    # flow_diagrams（scenario_flow を簡易テキスト化。(STT)/(TTS) 注記は付けず I-4/L-4 誤検知を避ける）
    diagram_lines = []
    for blk in scenario_flow:
        head = f"[{blk['step']}] {blk['type']}"
        if blk.get("next"):
            head += f" -> {blk['next']}"
        diagram_lines.append(head)
        for c in (blk.get("conditions") or []):
            diagram_lines.append(f"    - {c.get('match', '')} -> {c.get('next', '')}")
    flow_diagrams = [{"name": flow_name, "diagram": "\n".join(diagram_lines)}]

    # confirmation_items（TODO 台帳 = 壁打ちアジェンダ。T-5 の未解決数 ↔ TODO 数を揃える）
    confirmation_items = [
        {"item": field, "description": desc, "resolved": False}
        for field, desc in todos
    ]

    intent_phrase = ("、".join(main_intent_labels) + " 等に振り分けて"
                     if main_intent_labels else "")
    purpose = (f"{facility}（{scenario}）のAI電話自動受付。患者からの用件を聴取し、"
               f"{intent_phrase}受け付ける。本設計書は drawio から自動生成された骨子で、"
               f"facility 固有値（office_id・電話番号等）は壁打ちで確定する。")

    special_notes = [
        "本設計書は drawio から自動生成（scenario_from_drawio.py）。",
        "実現知識（input_method / retry_failure / status / sms_flag / flowname）は工場デフォルト合成済。",
        "未確定の facility 固有値（プレースホルダ）は confirmation_items に壁打ちアジェンダとして列挙。",
    ]

    flow_type = "subflow" if subflows else "1flow"
    spec = {
        "version": "1.0",
        "basic_info": {
            "facility_name": facility,
            "scenario_name": scenario,
            "group_name": group_name,
            "flow_name": flow_name,
            "flow_type": flow_type,
            "office_id": TODO,
            "phone_number": TODO,
            "environment": "demo",
        },
        "purpose": purpose,
        "flow_structure": {
            "type": flow_type,
            "flows": [{"name": flow_name, "role": "main",
                       "description": f"{facility} {scenario}（drawio 由来・自動生成）"}],
            "subflows": subflows,
        },
        "flow_diagrams": flow_diagrams,
        "context_fields": context_fields,
        "scenario_flow": scenario_flow,
        "step_details": step_details,
        "hearing_items": hearing_items,
        "tts_modules": tts_modules,
        "termination_patterns": termination_patterns,
        "amivoice_dictionary": [],
        "special_notes": special_notes,
        "confirmation_items": confirmation_items,
    }
    return spec


def convert(drawio_path, out_path, work_date=None):
    nodes, edges = parse_drawio(drawio_path)
    title = extract_title(drawio_path)
    spec = build_spec(nodes, edges, title, work_date=work_date)
    header = (f"# 設計書（drawio 自動生成 / scenario_from_drawio.py）\n"
              f"# 元 drawio: {os.path.basename(drawio_path)}\n"
              f"# 工場デフォルト合成済（input_method/retry_failure/status/sms_flag/flowname/"
              f"context_fields/tts_modules/group_name 日付/purpose/flow_diagrams/special_notes）。\n"
              f"# {TODO} は facility 固有値＝壁打ちで確定（confirmation_items にアジェンダ化）。\n")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        yaml.safe_dump(spec, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return out_path


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = sys.argv[1:]
    if not args or "-o" not in args:
        print("usage: python scenario_from_drawio.py <設計.drawio> -o <設計書.yaml> "
              "[--work-date YYYYMMDD]", file=sys.stderr)
        sys.exit(2)
    out_path = args[args.index("-o") + 1]
    consumed = {"-o", out_path}
    work_date = None
    if "--work-date" in args:
        work_date = args[args.index("--work-date") + 1]
        consumed |= {"--work-date", work_date}
    drawio_path = next(a for a in args if not a.startswith("-") and a not in consumed)
    if not os.path.exists(drawio_path):
        print(f"input not found: {drawio_path}", file=sys.stderr)
        sys.exit(1)
    print("OK:", convert(drawio_path, out_path, work_date=work_date))


if __name__ == "__main__":
    main()
