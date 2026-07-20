#!/usr/bin/env python3
"""
Fix script for 沖縄県立南部医療センター_診療 flow JSON.
Applies structural fixes (Stage 1).
"""

import json
import sys
import re
from collections import OrderedDict

INPUT_FILE = "C:/Users/takahashi.s/VSCode/bivr-checker/output/沖縄県立南部医療センター_診療_20260415.json"
OUTPUT_FILE = INPUT_FILE  # overwrite

# Expected slot counts: type -> (next_count, subs_count)
SLOT_SPEC = {
    "@General$Script": (12, 0),
    "drjoy^Context Logic$ContextMatchRouter": (10, 3),
    "drjoy^AmiVoice$Speech to Text": (11, 3),
    "drjoy^External Integration$DTMF AmiVoice STT Input": (11, 3),
    "drjoy^External Integration$generate_by_OpenAI": (10, 3),
    "drjoy^Text To Speech$Speech Retry Counter": (2, 3),
    "drjoy^Text To Speech$Text to speech": (1, 3),
    "drjoy^Text To Speech$Re-confirmation node data": (1, 3),
    "drjoy^Persistence$saveCompletionFlag2db": (1, 3),
    "drjoy^Persistence$saveContext2DB": (1, 3),
    "drjoy^Persistence$saveContextModel2DB": (1, 3),
    "drjoy^Persistence$save2db": (0, 0),
    "drjoy^External Integration$acceptance_times": (4, 3),
    "drjoy^Incoming$incoming-classifier": (5, 3),
    "drjoy^Custom Module$Custom Jump to Flow": (1, 3),
    "Custom$wait": (1, 3),
    "@IVR$Disconnect": (0, 0),
}

KEY_ORDER = ["layout", "next", "subs", "name", "description", "matchingmethod", "type", "params"]

EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}

summary = []

def log(msg):
    summary.append(msg)
    print(msg)


def reorder_keys(mod):
    """Reorder module keys to match KEY_ORDER."""
    ordered = OrderedDict()
    for k in KEY_ORDER:
        if k in mod:
            ordered[k] = mod[k]
    # include any extra keys not in KEY_ORDER (shouldn't exist but just in case)
    for k in mod:
        if k not in ordered:
            ordered[k] = mod[k]
    return dict(ordered)


def fix_slot_count(mod, mod_name, mod_type):
    """Fix next/subs array sizes to match expected."""
    if mod_type not in SLOT_SPEC:
        return

    expected_next, expected_subs = SLOT_SPEC[mod_type]
    changes = []

    # Fix next
    current_next = mod.get("next", [])
    if len(current_next) != expected_next:
        if expected_next == 0:
            mod["next"] = []
            changes.append(f"next {len(current_next)}->{expected_next}")
        elif len(current_next) > expected_next:
            # Keep non-empty ones first, then trim
            non_empty = [n for n in current_next if n.get("condition") or n.get("nextModuleName")]
            empty = [n for n in current_next if not n.get("condition") and not n.get("nextModuleName")]

            # For Re-confirmation with 3->1, keep only the first valid one (condition="^.*$")
            if mod_type == "drjoy^Text To Speech$Re-confirmation node data" and expected_next == 1:
                valid = [n for n in current_next if n.get("condition") == "^.*$"]
                if valid:
                    mod["next"] = [valid[0]]
                else:
                    mod["next"] = [current_next[0]]
            else:
                # Keep non-empty first, fill rest
                result = non_empty[:expected_next]
                while len(result) < expected_next:
                    result.append(dict(EMPTY_NEXT))
                mod["next"] = result
            changes.append(f"next {len(current_next)}->{expected_next}")
        else:
            # Too few - add empty slots
            while len(current_next) < expected_next:
                current_next.append(dict(EMPTY_NEXT))
            mod["next"] = current_next
            changes.append(f"next {len(current_next) - (expected_next - len(mod['next']))}->{expected_next}")

    # Fix subs
    current_subs = mod.get("subs", [])
    if len(current_subs) != expected_subs:
        if expected_subs == 0:
            mod["subs"] = []
            changes.append(f"subs {len(current_subs)}->{expected_subs}")
        elif len(current_subs) > expected_subs:
            non_empty = [s for s in current_subs if s.get("moduleName")]
            result = non_empty[:expected_subs]
            while len(result) < expected_subs:
                result.append(dict(EMPTY_SUB))
            mod["subs"] = result
            changes.append(f"subs {len(current_subs)}->{expected_subs}")
        else:
            while len(current_subs) < expected_subs:
                current_subs.append(dict(EMPTY_SUB))
            mod["subs"] = current_subs
            changes.append(f"subs padded to {expected_subs}")

    if changes:
        log(f"  [7] Slot fix {mod_name}: {', '.join(changes)}")


def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    modules = data["modules"]

    # =========================================================================
    # Fix 1: Retry matchingmethod 1 -> 0
    # =========================================================================
    fix1_count = 0
    for name, mod in modules.items():
        if mod["type"] == "drjoy^Text To Speech$Speech Retry Counter":
            if mod["matchingmethod"] != 0:
                mod["matchingmethod"] = 0
                fix1_count += 1
    log(f"[1] Retry matchingmethod: fixed {fix1_count} modules (1->0)")

    # =========================================================================
    # Fix 2: callId field in saveContextModel2DB
    # =========================================================================
    ctx_mod = modules["コンテキスト設定"]
    fields = json.loads(ctx_mod["params"]["fields"])
    for field in fields:
        if field["contextName"] == "callId":
            old_default = field["itemDefault"]
            old_display = field["displayType"]
            field["itemDefault"] = False
            field["displayType"] = "NUMBER"
            log(f"[2] callId: itemDefault {old_default}->False, displayType {old_display}->NUMBER")
            break

    # =========================================================================
    # Fix 3: status rangeValues - add missing values
    # =========================================================================
    for field in fields:
        if field["contextName"] == "status":
            rv = field["rangeValues"]
            existing_ids = {v["id"] for v in rv}

            if "0" not in existing_ids:
                rv.insert(0, {"id": "0", "value": "途中切断", "order": 0})
            if "3" not in existing_ids:
                # Insert after 代表案内(id=2)
                idx = next((i for i, v in enumerate(rv) if v["id"] == "2"), len(rv))
                rv.insert(idx + 1, {"id": "3", "value": "転送", "order": 3})

            # Sort by order
            rv.sort(key=lambda x: x["order"])
            field["rangeValues"] = rv
            log(f"[3] status rangeValues: now {len(rv)} values ({', '.join(v['id'] for v in rv)})")
            break

    # Write fields back as JSON string
    ctx_mod["params"]["fields"] = json.dumps(fields, ensure_ascii=False, indent=2)

    # =========================================================================
    # Fix 4 & 5 & 6: {TTS_AI:...} -> {tts_g:...} in ALL params
    # =========================================================================
    fix4_count = 0
    for name, mod in modules.items():
        for k, v in mod.get("params", {}).items():
            if isinstance(v, str) and "{TTS_AI:" in v:
                new_v = v.replace("{TTS_AI:", "{tts_g:")
                mod["params"][k] = new_v
                fix4_count += 1
    log(f"[4/5/6] TTS_AI->tts_g: fixed {fix4_count} param values")

    # Fix 5 specifically: Retry prompt_true format (add spaces after periods)
    fix5_count = 0
    RETRY_PROMPT_TRUE_OLD = "{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}"
    RETRY_PROMPT_TRUE_NEW = "{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}"
    for name, mod in modules.items():
        if mod["type"] == "drjoy^Text To Speech$Speech Retry Counter":
            pt = mod["params"].get("prompt_true", "")
            if pt == RETRY_PROMPT_TRUE_OLD:
                mod["params"]["prompt_true"] = RETRY_PROMPT_TRUE_NEW
                fix5_count += 1
    log(f"[5] Retry prompt_true spacing: fixed {fix5_count} modules")

    # =========================================================================
    # Fix 7: Slot count fixes
    # =========================================================================
    log("[7] Slot count fixes:")
    for name, mod in modules.items():
        fix_slot_count(mod, name, mod["type"])

    # =========================================================================
    # Fix 9: Add 冒頭_アナウンス TTS module
    # =========================================================================
    # 受付時間判定 true -> 小児科確認. Insert 冒頭_アナウンス between them.
    # Update 受付時間判定 true to point to 冒頭_アナウンス
    acc_mod = modules["受付時間判定"]
    original_true_target = None
    for slot in acc_mod["next"]:
        if slot.get("condition") == "^true$":
            original_true_target = slot["nextModuleName"]
            slot["nextModuleName"] = "冒頭_アナウンス"
            break

    log(f"[9] 受付時間判定 true: {original_true_target} -> 冒頭_アナウンス")

    # Create 冒頭_アナウンス TTS module
    tts_announce = {
        "layout": {"x": 0, "y": 960},
        "next": [
            {"condition": "^.*$", "label": "Next Module", "nextModuleName": original_true_target}
        ],
        "subs": [
            {"moduleName": "save-冒頭_アナウンス", "label": "save-冒頭_アナウンス"},
            {"moduleName": "", "label": ""},
            {"moduleName": "", "label": ""}
        ],
        "name": "冒頭_アナウンス",
        "description": "",
        "matchingmethod": 1,
        "type": "drjoy^Text To Speech$Text to speech",
        "params": {
            "prompt": "{tts_g:お電話ありがとうございます。沖縄県立南部医療センター・こども医療センターの、予約専用AI電話です。}",
            "stop_by_dtmf": "No"
        }
    }
    modules["冒頭_アナウンス"] = tts_announce

    # Create save-冒頭_アナウンス save2db module
    save_announce = {
        "layout": {"x": 220, "y": 990},
        "next": [],
        "subs": [],
        "name": "save-冒頭_アナウンス",
        "description": "",
        "matchingmethod": 1,
        "type": "drjoy^Persistence$save2db",
        "params": {}
    }
    modules["save-冒頭_アナウンス"] = save_announce

    log(f"[9] Added 冒頭_アナウンス (TTS) and save-冒頭_アナウンス (save2db)")

    # =========================================================================
    # Fix 10: Layout y_range fix - scale all y coordinates
    # =========================================================================
    current_max_y = max(mod["layout"]["y"] for mod in modules.values() if "layout" in mod)
    current_min_y = min(mod["layout"]["y"] for mod in modules.values() if "layout" in mod)
    current_range = current_max_y - current_min_y
    target_range = 20500
    # Need total modules * 100 >= y_range. 207 modules * 100 = 20700
    needed = len(modules) * 100
    if needed > target_range:
        target_range = needed

    scale = target_range / current_range if current_range > 0 else 1.0
    fix10_count = 0
    for name, mod in modules.items():
        if "layout" in mod:
            old_y = mod["layout"]["y"]
            new_y = round((old_y - current_min_y) * scale + current_min_y)
            if new_y != old_y:
                mod["layout"]["y"] = new_y
                fix10_count += 1

    new_max_y = max(mod["layout"]["y"] for mod in modules.values() if "layout" in mod)
    new_min_y = min(mod["layout"]["y"] for mod in modules.values() if "layout" in mod)
    log(f"[10] Layout y_range: {current_range} -> {new_max_y - new_min_y} (scale={scale:.4f}, {fix10_count} modules adjusted)")

    # =========================================================================
    # Fix 11: Re-confirmation module fixes
    # =========================================================================
    reconf_names = ["復唱_用件確認", "復唱_予約日_変更", "復唱_予約日_キャンセル"]
    for rname in reconf_names:
        if rname in modules:
            mod = modules[rname]
            # Keep only the slot with condition="^.*$"
            valid = [n for n in mod["next"] if n.get("condition") == "^.*$"]
            if valid:
                mod["next"] = [valid[0]]
            else:
                mod["next"] = [mod["next"][0]]  # fallback: keep first

            # Ensure params.module references nodeName (the param is "nodeName" not "module")
            # Re-confirmation uses "nodeName" param to reference source module
            node_name = mod["params"].get("nodeName", "")
            if node_name and node_name in modules:
                log(f"[11] {rname}: trimmed to 1 next slot, nodeName={node_name} (valid)")
            elif node_name:
                log(f"[11] {rname}: trimmed to 1 next slot, nodeName={node_name} (WARNING: not in modules)")
            else:
                log(f"[11] {rname}: trimmed to 1 next slot, no nodeName set")

    # =========================================================================
    # Fix 8: Key order (apply last so all additions are covered)
    # =========================================================================
    fix8_count = 0
    new_modules = OrderedDict()
    for name, mod in modules.items():
        reordered = reorder_keys(mod)
        if list(reordered.keys()) != list(mod.keys()):
            fix8_count += 1
        new_modules[name] = reordered
    data["modules"] = dict(new_modules)
    log(f"[8] Key order: reordered {fix8_count} modules")

    # =========================================================================
    # Write output
    # =========================================================================
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    log(f"\nOutput written to: {OUTPUT_FILE}")
    log(f"Total modules: {len(data['modules'])}")

    # Verification
    print("\n=== Verification ===")
    # Verify Retry matchingmethod
    for name, mod in data["modules"].items():
        if mod["type"] == "drjoy^Text To Speech$Speech Retry Counter":
            assert mod["matchingmethod"] == 0, f"{name} matchingmethod should be 0"
            assert isinstance(mod["matchingmethod"], int), f"{name} matchingmethod should be int"
    print("  Retry matchingmethod: OK (all 0, int type)")

    # Verify callId
    fields_check = json.loads(data["modules"]["コンテキスト設定"]["params"]["fields"])
    for f in fields_check:
        if f["contextName"] == "callId":
            assert f["itemDefault"] == False, "callId itemDefault should be False"
            assert f["displayType"] == "NUMBER", "callId displayType should be NUMBER"
            print(f"  callId: OK (itemDefault=False, displayType=NUMBER)")

    # Verify status rangeValues
    for f in fields_check:
        if f["contextName"] == "status":
            ids = [v["id"] for v in f["rangeValues"]]
            assert ids == ["0", "1", "2", "3", "6", "7"], f"status ids should be [0,1,2,3,6,7] but got {ids}"
            print(f"  status rangeValues: OK ({len(f['rangeValues'])} values)")

    # Verify no TTS_AI remains
    tts_ai_count = 0
    for name, mod in data["modules"].items():
        for k, v in mod.get("params", {}).items():
            if isinstance(v, str) and "{TTS_AI:" in v:
                tts_ai_count += 1
    assert tts_ai_count == 0, f"Still {tts_ai_count} TTS_AI occurrences"
    print(f"  TTS_AI: OK (0 remaining)")

    # Verify 冒頭_アナウンス exists
    assert "冒頭_アナウンス" in data["modules"], "冒頭_アナウンス missing"
    assert "save-冒頭_アナウンス" in data["modules"], "save-冒頭_アナウンス missing"
    print(f"  冒頭_アナウンス: OK")

    # Verify slot counts
    slot_errors = []
    for name, mod in data["modules"].items():
        t = mod["type"]
        if t in SLOT_SPEC:
            en, es = SLOT_SPEC[t]
            an = len(mod.get("next", []))
            as_ = len(mod.get("subs", []))
            if an != en or as_ != es:
                slot_errors.append(f"{name}: next={an}(expect {en}), subs={as_}(expect {es})")
    if slot_errors:
        print(f"  Slot counts: ERRORS ({len(slot_errors)}):")
        for e in slot_errors[:10]:
            print(f"    {e}")
    else:
        print(f"  Slot counts: OK (all match spec)")

    # Verify y_range
    ys = [mod["layout"]["y"] for mod in data["modules"].values()]
    yr = max(ys) - min(ys)
    needed = len(data["modules"]) * 100
    print(f"  y_range: {yr} (need >= {needed}): {'OK' if yr >= needed else 'FAIL'}")

    # Verify Re-confirmation next slots
    for rname in reconf_names:
        if rname in data["modules"]:
            assert len(data["modules"][rname]["next"]) == 1, f"{rname} should have 1 next slot"
    print(f"  Re-confirmation next slots: OK (all 1)")

    print("\n=== Summary ===")
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
