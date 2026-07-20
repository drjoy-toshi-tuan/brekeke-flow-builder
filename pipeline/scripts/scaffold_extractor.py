#!/usr/bin/env python3
"""
scaffold_extractor.py -- 既存フローJSONから scenario_flow YAML を逆抽出

scaffold_generator の逆操作。既存フローJSONを解析して8ブロック型に分類し、
scenario_flow セクションを含む YAML を生成する。Pattern 2（既存修正）の入力として、
gen_spec_html.py / dirlite が利用する。

v2 追加機能（Pattern 2 逆走用・完全設計書抽出モード）:
- `--properties` 引数で IVR プロパティ .md を読み込み、tts_modules の announcement に流し込む
- `--full-spec` 指定時、tts_modules / termination_patterns / context_fields /
  flow_structure / hearing_items / step_details / amivoice_dictionary も抽出し、
  qa_validator が通る完全な設計書 YAML を出力する

ガベージモジュールの扱い:
- どこからも参照されず、どこにも遷移しない孤立モジュールは「ガベージ」として扱う
- ガベージは scenario_flow に含めず、レポートに警告として出力
- 基本的には触らない（人間判断に委ねる）

Usage:
    # 従来: scenario_flow だけ抽出
    python3 scripts/scaffold_extractor.py <json_path> [-o output.yaml]

    # 新: 完全設計書抽出（Pattern 2 逆走用）
    python3 scripts/scaffold_extractor.py <json_path> \\
        --full-spec \\
        --properties path/to/properties.md \\
        -o output.yaml
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml as _yaml
except ImportError:
    print("Error: PyYAML が必要です", file=sys.stderr)
    sys.exit(1)


# ─── モジュール type → ブロック型のマッピング ──────────────────────────

TYPE_PATTERNS = {
    "wait":              ["Custom$wait"],
    "saveContextModel":  ["Persistence$saveContextModel2DB"],
    "incoming_classifier": ["Incoming$incoming-classifier"],
    "acceptance_times":  ["External Integration$acceptance_times"],
    "tts":               ["Text To Speech$Text to speech"],
    "stt_amivoice":      ["AmiVoice$Speech to Text"],
    "stt_dtmf":          ["External Integration$DTMF AmiVoice STT Input"],
    "stt_soniox":        ["Soniox$Speech to Text"],  # drjoy^Soniox$Speech to Text
    "openai":            ["External Integration$generate_by_OpenAI"],
    "retry":             ["Text To Speech$Speech Retry Counter"],
    "save2db":           ["Persistence$save2db"],
    "save_completion":   ["Persistence$saveCompletionFlag2db"],
    "disconnect":        ["IVR$Disconnect"],
    "jump_to_flow":      ["Custom Module$Custom Jump to Flow"],
    "context_match_router": ["Context Logic$ContextMatchRouter"],
    "script":            ["TS Custom Module$Script"],
    "date_of_call":      ["Date of Call Classifier"],
    "reconfirmation":    ["Re-confirmation node data"],
    "dob_reconfirmation":["DOB Re-confirmation"],
    "phone_normalization":["Phone Normalization"],
    "call_transfer":     ["Call Transfer$call-transfer"],
}


def get_module_type_kind(mod: dict) -> str:
    """モジュールの type 文字列から種別を判定"""
    t = mod.get("type", "")
    for kind, patterns in TYPE_PATTERNS.items():
        for p in patterns:
            if p in t:
                return kind
    return "unknown"


def get_main_next(mod: dict, exclude_labels: set = None) -> str | None:
    """主接続先を取得（最初の有効な next）。exclude_labels を除外。"""
    exclude_labels = exclude_labels or set()
    for n in mod.get("next", []):
        label = n.get("label", "")
        target = n.get("nextModuleName", "")
        if target and label not in exclude_labels:
            return target
    return None


def collect_reachable(modules: dict, start: str) -> set:
    """start から到達可能な全モジュールを収集（next + subs 経由）"""
    reachable = set()
    stack = [start]
    while stack:
        cur = stack.pop()
        if cur in reachable or cur not in modules:
            continue
        reachable.add(cur)
        mod = modules[cur]
        for n in mod.get("next", []):
            t = n.get("nextModuleName", "")
            if t and t in modules and t not in reachable:
                stack.append(t)
        for s in mod.get("subs", []):
            t = s.get("moduleName", "")
            if t and t in modules and t not in reachable:
                stack.append(t)
    return reachable


# ─── ブロック検出 ─────────────────────────────────────────────────

def _find_module_by_type(modules: dict, kind: str) -> str | None:
    """type 種別で最初にマッチするモジュール名を返す"""
    for name, mod in modules.items():
        if get_module_type_kind(mod) == kind:
            return name
    return None


def detect_opening_block(modules: dict, visited: set) -> dict | None:
    """opening ブロックを検出: wait → saveContextModel2DB → incoming-classifier → [acceptance_times]
    モジュール名ではなく type で検索し、Gen2/Gen3 両方に対応する。
    """
    # wait モジュールを type で検索（Gen3: "冒頭", Gen2: 任意の名前）
    wait_name = _find_module_by_type(modules, "wait")
    if not wait_name:
        return None

    # opening チェーンを type で辿る
    context_name = _find_module_by_type(modules, "saveContextModel")
    incoming_name = _find_module_by_type(modules, "incoming_classifier")
    acceptance_name = _find_module_by_type(modules, "acceptance_times")

    opening_modules = [wait_name]
    if context_name:
        opening_modules.append(context_name)
    if incoming_name:
        opening_modules.append(incoming_name)

    use_acceptance = acceptance_name is not None
    if use_acceptance:
        opening_modules.append(acceptance_name)
        next_step = get_main_next(modules[acceptance_name],
                                  exclude_labels={"timeout", "error", "rejected"})
    elif incoming_name:
        next_step = get_main_next(modules[incoming_name],
                                  exclude_labels={"非通知", "海外"})
    else:
        next_step = get_main_next(modules[wait_name])

    visited.update(opening_modules)

    return {
        "step": "冒頭",
        "type": "opening",
        "use_acceptance_times": use_acceptance,
        "next": next_step or "",
    }


def detect_termination_blocks(modules: dict, visited: set) -> list[dict]:
    """termination チェーンを検出。2パターン対応:
    - Gen3 標準形式: 完了フラグ_* → END_* (TTS) → save-END_* → 切断_*
    - 旧/移管形式:   終話_* (TTS) → save-終話_* → 切断_*（完了フラグなし）
    """
    blocks = []
    emitted_steps: set = set()

    # パターン 1: 完了フラグ_ 起点のチェーン検出
    for mod_name, mod in modules.items():
        if mod_name in visited:
            continue
        if not mod_name.startswith("完了フラグ_"):
            continue
        if get_module_type_kind(mod) != "save_completion":
            continue

        chain = [mod_name]
        cur = mod_name
        while True:
            cur_mod = modules.get(cur)
            if not cur_mod:
                break
            nxt = get_main_next(cur_mod)
            if nxt and nxt in modules and nxt not in chain:
                chain.append(nxt)
                cur = nxt
            else:
                break

        visited.update(chain)
        for c in chain:
            for s in modules.get(c, {}).get("subs", []):
                sm = s.get("moduleName", "")
                if sm:
                    visited.add(sm)

        end_name = next((c for c in chain if c.startswith("END_")), mod_name)
        blocks.append({
            "step": end_name,
            "type": "termination",
            "termination_ref": end_name,
        })
        emitted_steps.add(end_name)

    # パターン 2: Disconnect から逆引き（完了フラグなしの旧/移管形式）
    for mod_name, mod in modules.items():
        if mod_name in visited:
            continue
        if get_module_type_kind(mod) != "disconnect":
            continue
        short = mod_name[3:] if mod_name.startswith("切断_") else mod_name
        # 命名ゆれ対策: 終話_ / END_ / XXX_アナウンス 3種
        tts_candidates = [f"終話_{short}", f"END_{short}", f"{short}_アナウンス"]
        found = False
        for tts_name in tts_candidates:
            if tts_name in modules and get_module_type_kind(modules[tts_name]) == "tts":
                if tts_name in emitted_steps:
                    break
                chain = [tts_name, f"save-{tts_name}", mod_name]
                visited.update(c for c in chain if c in modules)
                blocks.append({
                    "step": tts_name,
                    "type": "termination",
                    "termination_ref": tts_name,
                })
                emitted_steps.add(tts_name)
                found = True
                break
        if not found and mod_name not in emitted_steps:
            visited.add(mod_name)
            blocks.append({
                "step": mod_name,
                "type": "termination",
                "termination_ref": mod_name,
            })
            emitted_steps.add(mod_name)
    return blocks


def detect_hearing_or_announcement(modules: dict, mod_name: str, visited: set) -> dict | None:
    """TTS から始まるブロックを検出: hearing or announcement"""
    mod = modules.get(mod_name)
    if not mod or get_module_type_kind(mod) != "tts":
        return None

    # next を辿って STT があれば hearing、なければ announcement
    next_target = get_main_next(mod)
    next_mod = modules.get(next_target) if next_target else None
    next_kind = get_module_type_kind(next_mod) if next_mod else None

    block = {"step": mod_name}
    visited.add(mod_name)

    if next_kind in ("stt_amivoice", "stt_dtmf", "stt_soniox"):
        # hearing ブロック
        block["type"] = "hearing"
        visited.add(next_target)

        # OpenAI と Retry を visited に
        stt_success = None
        for n in modules[next_target].get("next", []):
            label = n.get("label", "")
            tgt = n.get("nextModuleName", "")
            if label == "success" and tgt:
                stt_success = tgt
            elif label in ("timeout", "error", "no_result") and tgt:
                visited.add(tgt)  # retry

        if stt_success:
            visited.add(stt_success)
            success_mod = modules.get(stt_success, {})
            if get_module_type_kind(success_mod) == "openai":
                block["output_format"] = "datetime"  # 暫定
                # OpenAI の next 分岐から enum 判定
                conditions = []
                for n in success_mod.get("next", []):
                    label = n.get("label", "")
                    tgt = n.get("nextModuleName", "")
                    if label not in ("timeout", "error", "no_result", "default") and tgt:
                        conditions.append({"match": label, "next": tgt})
                    elif label == "default" and tgt:
                        block["next"] = tgt
                if conditions:
                    block["output_format"] = "enum"
                    block["conditions"] = conditions
            else:
                block["output_format"] = "text"
                block["next"] = stt_success
        else:
            block["output_format"] = "text"

        # subs (save2db) を visited に
        for c in [mod_name, next_target]:
            for s in modules.get(c, {}).get("subs", []):
                sm = s.get("moduleName", "")
                if sm:
                    visited.add(sm)
    else:
        # announcement ブロック
        block["type"] = "announcement"
        if next_target:
            block["next"] = next_target
        for s in mod.get("subs", []):
            sm = s.get("moduleName", "")
            if sm:
                visited.add(sm)

    return block


def detect_simple_block(modules: dict, mod_name: str, visited: set, btype: str) -> dict | None:
    """単一モジュール型のブロック（subflow / context_match_router / script）"""
    mod = modules.get(mod_name)
    if not mod:
        return None

    visited.add(mod_name)
    block = {"step": mod_name, "type": btype}

    if btype == "subflow":
        block["flowname"] = mod.get("params", {}).get("flowname", "")
        nxt = get_main_next(mod)
        if nxt:
            block["next"] = nxt
    elif btype in ("context_match_router", "script", "date_of_call_classifier"):
        ref = mod.get("params", {}).get("module1Name", "") or mod.get("params", {}).get("module", "")
        if ref:
            block["reference_module"] = ref
        # 条件を取得（^.+$ Other は除外）
        conditions = []
        for n in mod.get("next", []):
            cond = n.get("condition", "")
            label = n.get("label", "")
            tgt = n.get("nextModuleName", "")
            if label == "Other" or cond == "^.+$":
                continue
            if cond and tgt:
                conditions.append({"match": label or cond.strip("^$"), "next": tgt})
        if conditions:
            block["conditions"] = conditions

    return block


# ─── メイン抽出 ───────────────────────────────────────────────────

# ─── Pattern 2 逆走用: 完全設計書抽出 ──────────────────────────────

_TTS_PROP_RE = re.compile(r'^(\S+?)\.prompt\s*=\s*\{tts_(?:g|ai):\s*(.*?)\s*\}\s*$')
_TTS_INLINE_RE = re.compile(r'^\s*\{tts_(?:g|ai):\s*(.*?)\s*\}\s*$')


def parse_ivr_properties(props_path: Path) -> dict:
    """IVRプロパティ.mdを解析して {module_name: tts_text} を返す。
    Brekeke標準形式: `module_name.prompt={tts_g:発話テキスト}` / `{tts_ai:...}` 両対応。
    """
    tts_map: dict[str, str] = {}
    if not props_path or not Path(props_path).exists():
        return tts_map
    text = Path(props_path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("```") or s.startswith("---"):
            continue
        m = _TTS_PROP_RE.match(s)
        if m:
            tts_map[m.group(1)] = m.group(2)
    return tts_map


def _unwrap_tts(raw: str) -> str:
    """インライン params.prompt が `{tts_g:...}` で囲まれていたら中身だけ返す"""
    if not raw:
        return ""
    m = _TTS_INLINE_RE.match(raw.strip())
    return m.group(1) if m else raw.strip()


def extract_tts_modules(modules: dict, tts_from_properties: dict) -> list[dict]:
    """TTSモジュールを抽出。優先順位: properties > inline params.prompt。
    Re-confirmation node data は除外（params.prompt に #data# 埋め込みがあるため別物）。
    """
    result = []
    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        mod_type = mod.get("type", "")
        if "Text To Speech$Text to speech" not in mod_type:
            continue
        if "Re-confirmation node data" in mod_type:
            continue
        text = tts_from_properties.get(name, "")
        if not text:
            inline = mod.get("params", {}).get("prompt", "") or ""
            text = _unwrap_tts(inline)
        if text:
            result.append({
                "module_name": name,
                "announcement": text,
            })
    return result


def extract_context_fields(modules: dict) -> list[dict]:
    """save2db 系モジュールから contextName と display_type を収集。同名は1件に集約。"""
    fields: dict[str, dict] = {}
    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        mod_type = mod.get("type", "")
        is_save = ("Persistence$save2db" in mod_type
                   or "Persistence$saveContext2DB" in mod_type
                   or "Persistence$saveContextModel2DB" in mod_type)
        if not is_save:
            continue
        params = mod.get("params", {}) if isinstance(mod.get("params"), dict) else {}
        ctx = params.get("contextName", "") or params.get("context_name", "")
        dt = params.get("display_type", "") or params.get("contextDisplayType", "") or "TEXT"
        if ctx and ctx not in fields:
            fields[ctx] = {"context_name": ctx, "display_type": dt}
    return list(fields.values())


def extract_termination_patterns(modules: dict, term_blocks: list) -> list[dict]:
    """termination ブロックから status/smsFlag を抽出。完了フラグがあれば params から、
    無ければ名前ベースで condition を推定し status/smsFlag はデフォルト値。
    """
    patterns = []
    for blk in term_blocks:
        ref = blk.get("termination_ref") or blk.get("step", "")
        if not ref:
            continue
        short = ref[4:] if ref.startswith("END_") else ref
        flag_name = f"完了フラグ_{short}"
        flag_mod = modules.get(flag_name, {}) or {}
        params = flag_mod.get("params", {}) if isinstance(flag_mod.get("params"), dict) else {}
        pattern = {
            "name": ref,
            "completion_flag_name": flag_name,
            "status": str(params.get("status", "1")),
            "sms_flag": str(params.get("smsFlag", params.get("sms_flag", "0"))),
        }
        if "非通知" in ref or "非通知" in short:
            pattern["condition"] = "非通知時"
        elif "時間外" in ref or "時間外" in short:
            pattern["condition"] = "時間外"
        elif "聴取失敗" in ref or "聴取失敗" in short:
            pattern["condition"] = "聴取失敗（リトライ上限）"
        elif "切断" in ref:
            pattern["condition"] = "途中切断"
        else:
            pattern["condition"] = "正常終話"
        patterns.append(pattern)
    return patterns


def extract_flow_structure(data: dict, modules: dict) -> dict:
    """flow_structure セクションを抽出。Jump to Flow の flowname (or flowName) + モジュール名推定。"""
    main_flow_name = data.get("name", "") or ""
    group_name = main_flow_name.split("$", 1)[0] if "$" in main_flow_name else ""
    subflow_entries: dict[str, dict] = {}

    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        if "Custom Jump to Flow" not in mod.get("type", ""):
            continue
        params = mod.get("params", {}) if isinstance(mod.get("params"), dict) else {}
        fname = params.get("flowname", "") or params.get("flowName", "")
        if fname:
            full_name = fname
            target = fname.split("$", 1)[-1] if "$" in fname else fname
        else:
            # モジュール名から推定（Jump_氏名聴取 → 氏名聴取）
            short = name
            for prefix in ("Jump_", "jump_"):
                if short.startswith(prefix):
                    short = short[len(prefix):]
                    break
            for fp in ("変更_", "キャンセル_", "予約_", "確認_", "新規_", "再診_"):
                if short.startswith(fp):
                    short = short[len(fp):]
                    break
            target = short
            full_name = f"{group_name}${target}" if group_name else target
        if full_name not in subflow_entries:
            subflow_entries[full_name] = {
                "name": full_name,
                "target": target,
                "recitation": "なし",
                "transition_module": "drjoy^Custom Module$Custom Jump to Flow",
                "termination": "return",
                "notes": "逆走抽出",
            }
    subflows_list = list(subflow_entries.values())
    return {
        "type": "subflow" if subflows_list else "1flow",
        "flows": [{"name": main_flow_name, "role": "main", "description": "（逆走抽出）"}],
        "subflows": subflows_list,
    }


def _derive_openai_labels_from_prompt(prompt_text: str) -> list[str]:
    """OpenAI params.prompt から出力値候補を抽出（validator パーサと同等）"""
    if not prompt_text:
        return []
    labels: list[str] = []
    in_section = False
    list_marker = re.compile(r'^[-\*・•]\s*(.+?)$')
    inline_output = re.compile(r'^出力\s*[:：]\s*(.+)$')
    trigger = re.compile(
        r'(出力.*(?:仕様|値|候補|形式|は|とは))|'
        r'(以下の(?:いずれか|どれか|値|語).*出力)|'
        r'(次の(?:いずれか|どれか|値|語).*出力)'
    )

    def _clean(label: str) -> str:
        s = label.strip()
        s = re.sub(r'[。、:：（(].*$', '', s).strip()
        return s.rstrip("*")

    for line in prompt_text.split("\n"):
        s = line.strip()
        if re.match(r'^#.*出力', s) or trigger.search(s):
            in_section = True
            continue
        if in_section and s.startswith("#") and "出力" not in s:
            in_section = False
            continue
        if in_section:
            if re.match(r'^-{2,}$', s):
                continue
            m = list_marker.match(s)
            if m:
                lbl = _clean(m.group(1))
                if lbl and lbl != "NO_RESULT":
                    labels.append(lbl)
        im = inline_output.match(s)
        if im:
            lbl = _clean(im.group(1))
            lbl = lbl.split()[0] if lbl else ""
            if lbl and lbl != "NO_RESULT" and 1 <= len(lbl) <= 40:
                labels.append(lbl)
    seen = set()
    result = []
    for l in labels:
        if l not in seen:
            seen.add(l)
            result.append(l)
    return result


def extract_hearing_items(modules: dict, scenario_flow: list) -> list[dict]:
    """hearing ブロックから hearing_items を抽出"""
    items = []
    for blk in scenario_flow:
        if blk.get("type") != "hearing":
            continue
        step_name = blk.get("step", "")
        if not step_name:
            continue
        candidates = [
            f"openAI_{step_name}",
            f"OpenAI_{step_name}",
            f"openai_{step_name}",
            step_name if "generate_by_OpenAI" in modules.get(step_name, {}).get("type", "") else None,
        ]
        openai_mod = None
        for cand in candidates:
            if cand and cand in modules and "generate_by_OpenAI" in modules[cand].get("type", ""):
                openai_mod = modules[cand]
                break
        if not openai_mod:
            items.append({
                "step_name": step_name,
                "output_format": "text",
                "retry_count": 3,
            })
            continue
        next_labels: list[str] = []
        for n in openai_mod.get("next", []):
            cond = n.get("condition", "")
            m = re.match(r'^\^(.+)\$$', cond)
            if not m:
                continue
            lbl = m.group(1)
            if lbl in ("TIMEOUT", "ERROR", "NO_RESULT", ".*", ".+"):
                continue
            next_labels.append(lbl)
        prompt_text = openai_mod.get("params", {}).get("prompt", "") or ""
        prompt_labels = _derive_openai_labels_from_prompt(prompt_text)
        all_labels = list(dict.fromkeys(next_labels + [l for l in prompt_labels if l not in next_labels]))
        output_format = "enum" if all_labels else "text"
        item = {"step_name": step_name, "output_format": output_format, "retry_count": 3}
        if all_labels:
            item["output_labels"] = all_labels
        items.append(item)
    return items


def extract_step_details(scenario_flow: list, tts_modules: list) -> list[dict]:
    """scenario_flow から step_details の骨格を抽出"""
    tts_lookup = {t["module_name"]: t["announcement"] for t in tts_modules}
    details = []
    for blk in scenario_flow:
        btype = blk.get("type", "")
        if btype not in ("hearing", "announcement"):
            continue
        step_name = blk.get("step", "")
        if not step_name:
            continue
        detail = {
            "step_name": step_name,
            "type": btype,
            "retry_count": 3,
            "retry_failure": "end_failure",
        }
        ann = tts_lookup.get(step_name, "")
        if ann:
            detail["tts_announcement"] = ann
        details.append(detail)
    return details


def extract_amivoice_dictionary(modules: dict) -> list[dict]:
    """STT モジュール (AmiVoice) の profile_words を抽出"""
    items = []
    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        if "AmiVoice$Speech to Text" not in mod.get("type", ""):
            continue
        words = mod.get("params", {}).get("profile_words", "") if isinstance(mod.get("params"), dict) else ""
        if not words:
            continue
        step_name = name
        if step_name.startswith("入力_"):
            step_name = step_name[len("入力_"):]
        items.append({"step_name": step_name, "words": words})
    return items


def extract_full_spec(json_path: str, properties_path: str = "",
                      facility_name: str = "", flow_name: str = "") -> tuple[dict, list]:
    """BIVR展開JSON + IVRプロパティから完全設計書 YAML を逆抽出"""
    base_spec, garbage = extract_scenario_flow(json_path)
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    modules = data.get("modules", {})
    scenario_flow = base_spec.get("scenario_flow", [])
    term_blocks = [b for b in scenario_flow if b.get("type") == "termination"]

    tts_from_props = parse_ivr_properties(Path(properties_path)) if properties_path else {}

    tts_modules = extract_tts_modules(modules, tts_from_props)
    context_fields = extract_context_fields(modules)
    termination_patterns = extract_termination_patterns(modules, term_blocks)
    flow_structure = extract_flow_structure(data, modules)
    hearing_items = extract_hearing_items(modules, scenario_flow)
    step_details = extract_step_details(scenario_flow, tts_modules)
    amivoice_dict = extract_amivoice_dictionary(modules)

    full_flow_name = flow_name or base_spec.get("basic_info", {}).get("flow_name", "") or data.get("name", "")
    group_name = full_flow_name.split("$", 1)[0] if "$" in full_flow_name else (facility_name or "TODO_要確認")
    flow_label = full_flow_name.split("$", 1)[1] if "$" in full_flow_name else full_flow_name

    full_spec = {
        "version": "2.0",
        "basic_info": {
            "facility_name": facility_name or base_spec.get("basic_info", {}).get("facility_name", "TODO_施設名を記入"),
            "group_name": group_name,
            "flow_name": flow_label or full_flow_name or "TODO_要確認",
            "flow_type": "subflow" if any("Custom Jump to Flow" in m.get("type", "") for m in modules.values()) else "1flow",
            "office_id": "TODO_要確認",
            "work_type": "modify",
        },
        "flow_structure": flow_structure,
        "purpose": "TODO_要確認（BIVRから逆抽出のため要追記）",
        "flow_diagrams": [],
        "context_fields": context_fields,
        "hearing_items": hearing_items,
        "step_details": step_details,
        "termination_patterns": termination_patterns,
        "tts_modules": tts_modules,
        "amivoice_dictionary": amivoice_dict,
        "special_notes": "（BIVR逆走で生成。修正指示書と照合してから pipeline へ）",
        "confirmation_items": [],
        "scenario_flow": scenario_flow,
    }
    return full_spec, garbage


def _is_echo_back_tts(name: str) -> bool:
    """Echo-back（復唱）TTS モジュールかどうかを命名規則で判定。
    ブロックの二次 TTS なので、ブロック同定時の「起点 TTS」としては扱わない。
    """
    if not name:
        return False
    return name.startswith("復唱_") or name.endswith("_復唱") or "_復唱" in name


def _compute_bfs_order(modules: dict, start: str) -> dict:
    """start から BFS で辿れるモジュールの訪問順を返す。
    scenario_flow のブロック並びを「フロー順」に整列するために使う。
    到達不能なモジュールは辞書に載らない。
    """
    order = {}
    if start not in modules:
        return order
    queue = [start]
    seen = {start}
    i = 0
    while queue:
        cur = queue.pop(0)
        order[cur] = i
        i += 1
        mod = modules.get(cur, {})
        if not isinstance(mod, dict):
            continue
        for n in mod.get("next", []) or []:
            tgt = n.get("nextModuleName", "")
            if tgt and tgt in modules and tgt not in seen:
                seen.add(tgt)
                queue.append(tgt)
        for s in mod.get("subs", []) or []:
            tgt = s.get("moduleName", "")
            if tgt and tgt in modules and tgt not in seen:
                seen.add(tgt)
                queue.append(tgt)
    return order


def _build_block_for_non_tts(modules: dict, name: str, mod: dict, visited: set) -> dict | None:
    """TTS 以外を起点とするブロック（subflow / CMR / script / date_of_call / call_transfer）を組み立てる"""
    kind = get_module_type_kind(mod)
    if kind == "jump_to_flow":
        return detect_simple_block(modules, name, visited, "subflow")
    if kind == "context_match_router":
        return detect_simple_block(modules, name, visited, "context_match_router")
    if kind == "script":
        return detect_simple_block(modules, name, visited, "script")
    if kind == "date_of_call":
        return detect_simple_block(modules, name, visited, "date_of_call_classifier")
    if kind == "call_transfer":
        visited.add(name)
        params = mod.get("params", {})
        block = {
            "step": name,
            "type": "call_transfer",
            "transfer_type": params.get("transfer_type", "Blind Transfer"),
        }
        for n in mod.get("next", []):
            label = n.get("label", "")
            tgt = n.get("nextModuleName", "")
            if label == "Succeeded" and tgt:
                block["next_success_module"] = tgt
            elif label == "Failed" and tgt:
                block["next_failure_module"] = tgt
        if params.get("prompt_failed"):
            block["on_failure_announcement"] = params["prompt_failed"]
        return block
    return None


def extract_scenario_flow(json_path: str) -> tuple[dict, list]:
    """既存JSONから scenario_flow と garbage modules を抽出（TTS-first アーキテクチャ）

    scaffold_generator の逆変換として、設計書 YAML を復元することが目的。
    start → next の DFS では分岐先ブロックを全件拾えないため、TTS を全件起点に
    ブロック同定し、後段で BFS 順に並べる。
    """
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    modules = data.get("modules", {})
    start = data.get("start", "冒頭")
    flow_name = data.get("name", "")

    visited: set = set()

    # 1. opening（wait / saveContextModel / incoming-classifier / acceptance_times を visited に）
    opening = detect_opening_block(modules, visited)

    # 2. termination（完了フラグ_ / END_ / save-END_ / 切断_ チェーンを visited に）
    term_blocks = detect_termination_blocks(modules, visited)
    term_step_names = {b["step"] for b in term_blocks}

    # 3. TTS-first: 全 TTS を起点に hearing / announcement ブロックを組み立てる
    tts_blocks: list = []
    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        if name in visited or name in term_step_names:
            continue
        if get_module_type_kind(mod) != "tts":
            continue
        if _is_echo_back_tts(name):
            continue  # echo-back は別ブロックの二次TTS、独立ブロックにしない
        block = detect_hearing_or_announcement(modules, name, visited)
        if block:
            tts_blocks.append(block)

    # 4. 非 TTS 起点ブロック（subflow / CMR / script / date_of_call / call_transfer）
    non_tts_blocks: list = []
    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        if name in visited or name in term_step_names:
            continue
        block = _build_block_for_non_tts(modules, name, mod, visited)
        if block:
            non_tts_blocks.append(block)

    # 5. BFS 順で並べる（到達不能ブロックは unreachable フラグ付きで末尾近くへ）
    bfs_order = _compute_bfs_order(modules, start)
    all_flow_blocks = tts_blocks + non_tts_blocks
    for blk in all_flow_blocks:
        step = blk.get("step", "")
        if step not in bfs_order:
            blk["unreachable"] = True

    def _sort_key(blk):
        step = blk.get("step", "")
        # 到達可能: BFS順、到達不能: 最後（安定ソートで元の順序を保つ）
        return (1 if step not in bfs_order else 0, bfs_order.get(step, 0))

    ordered_blocks = sorted(all_flow_blocks, key=_sort_key)

    # 6. scenario_flow 組み立て: opening → 本体 → termination
    scenario_flow: list = []
    if opening:
        scenario_flow.append(opening)
    scenario_flow.extend(ordered_blocks)
    scenario_flow.extend(term_blocks)

    # 5. ガベージ検出（どのブロックにも属さず、start から到達不能なモジュール）
    reachable = collect_reachable(modules, start)
    block_modules = set()
    for blk in scenario_flow:
        block_modules.add(blk["step"])
        if blk.get("type") == "termination":
            ref = blk.get("termination_ref", blk["step"])
            short = ref[4:] if ref.startswith("END_") else ref
            block_modules.update([
                f"完了フラグ_{short}",
                ref,
                f"save-{ref}",
                f"切断_{short}",
            ])

    garbage = []
    for mod_name, mod in modules.items():
        if mod_name in visited or mod_name in block_modules:
            continue
        if mod_name.startswith("save-"):
            continue  # save2db は親のチェック対象外
        is_reachable = mod_name in reachable
        is_referenced = any(
            mod_name == n.get("nextModuleName", "")
            for m in modules.values()
            for n in m.get("next", [])
        )
        if not is_reachable and not is_referenced:
            garbage.append({
                "module": mod_name,
                "type": mod.get("type", ""),
                "reason": "孤立: どこからも参照されず、どこにも遷移しない",
            })

    # 出力 YAML 構造
    spec = {
        "version": "2.0",
        "basic_info": {
            "facility_name": "（既存JSONから抽出）",
            "flow_name": flow_name,
        },
        "scenario_flow": scenario_flow,
    }

    return spec, garbage


def main():
    parser = argparse.ArgumentParser(description="既存JSONから scenario_flow YAML を逆抽出")
    parser.add_argument("json_path", help="既存フローJSONパス")
    parser.add_argument("-o", "--output", help="出力YAMLパス（デフォルト: extracted_<stem>.yaml）")
    parser.add_argument("--garbage-report", help="ガベージレポート出力パス（デフォルト: 同じディレクトリの garbage_<stem>.md）")
    parser.add_argument("--full-spec", action="store_true",
                        help="完全設計書モード（Pattern 2 逆走用）。"
                             "tts_modules/hearing_items/step_details/termination_patterns/"
                             "context_fields/flow_structure/amivoice_dictionary も抽出")
    parser.add_argument("--properties", default="",
                        help="IVRプロパティ.md パス（--full-spec 時に tts_modules の announcement として読み込む）")
    parser.add_argument("--facility-name", default="", help="施設名（basic_info.facility_name に入る）")
    parser.add_argument("--flow-name", default="", help="フロー名（basic_info.flow_name に入る）")
    args = parser.parse_args()

    json_path = Path(args.json_path)
    if not json_path.exists():
        print(f"Error: {json_path} が見つかりません", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output) if args.output else json_path.parent / f"extracted_{json_path.stem}.yaml"
    garbage_path = Path(args.garbage_report) if args.garbage_report else json_path.parent / f"garbage_{json_path.stem}.md"

    if args.full_spec:
        spec, garbage = extract_full_spec(
            str(json_path),
            properties_path=args.properties,
            facility_name=args.facility_name,
            flow_name=args.flow_name,
        )
        mode_label = "完全設計書"
    else:
        spec, garbage = extract_scenario_flow(str(json_path))
        mode_label = "scenario_flow のみ"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        _yaml.dump(spec, f, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"[extract] モード: {mode_label}", file=sys.stderr)
    print(f"[extract] scenario_flow ブロック数: {len(spec.get('scenario_flow', []))}", file=sys.stderr)
    if args.full_spec:
        print(f"[extract] tts_modules: {len(spec.get('tts_modules', []))}  "
              f"context_fields: {len(spec.get('context_fields', []))}  "
              f"hearing_items: {len(spec.get('hearing_items', []))}  "
              f"termination_patterns: {len(spec.get('termination_patterns', []))}",
              file=sys.stderr)
    print(f"[extract] 出力: {output_path}", file=sys.stderr)

    if garbage:
        garbage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(garbage_path, "w", encoding="utf-8") as f:
            f.write(f"# ガベージモジュールレポート — {json_path.name}\n\n")
            f.write(f"以下のモジュールはどのブロックにも属さず、孤立しています。\n")
            f.write(f"基本的には触らず、人間が判断してください。\n\n")
            f.write(f"| モジュール名 | type | 理由 |\n|---|---|---|\n")
            for g in garbage:
                f.write(f"| `{g['module']}` | `{g['type']}` | {g['reason']} |\n")
        print(f"[extract] ガベージ {len(garbage)}件 → {garbage_path}", file=sys.stderr)
    else:
        print(f"[extract] ガベージなし", file=sys.stderr)

    print(str(output_path))


if __name__ == "__main__":
    main()
