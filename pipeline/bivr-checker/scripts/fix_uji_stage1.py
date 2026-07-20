#!/usr/bin/env python3
"""Stage 1 追加修正: 宇治徳洲会病院 — スロット数/detection_flag/キー順序"""
import json, os, copy, sys, io

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "output/宇治徳洲会病院/fixed/flows"

SLOT_COUNTS = {
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
    "drjoy^External Integration$RAG": (4, 3),
    "drjoy^TS Custom Module$DOB Re-confirmation": (4, 3),
    "drjoy^TS Custom Module$Phone Normalization": (5, 3),
}
EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}
KEY_ORDER = ["layout", "next", "subs", "name", "description", "matchingmethod", "type", "params"]

def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    fname = os.path.basename(filepath)
    fixes = []
    modules = data.get("modules", {})
    new_modules = {}
    for mname, mod in modules.items():
        mtype = mod.get("type", "")
        # detection_flag
        if mtype in ("drjoy^AmiVoice$Speech to Text", "drjoy^External Integration$DTMF AmiVoice STT Input"):
            params = mod.get("params", {})
            if params.get("detection_flag") != "デフォルト":
                old = params.get("detection_flag", "(unset)")
                params["detection_flag"] = "デフォルト"
                fixes.append(f"  detection_flag: {mname} '{old}' -> 'デフォルト'")
        # slot counts
        if mtype in SLOT_COUNTS:
            exp_next, exp_subs = SLOT_COUNTS[mtype]
            cur_next = mod.get("next", [])
            cur_subs = mod.get("subs", [])
            if len(cur_next) != exp_next:
                if len(cur_next) > exp_next:
                    mod["next"] = cur_next[:exp_next]
                else:
                    mod["next"] = cur_next + [copy.deepcopy(EMPTY_NEXT) for _ in range(exp_next - len(cur_next))]
                fixes.append(f"  slots: {mname} next {len(cur_next)}->{exp_next}")
            if len(cur_subs) != exp_subs:
                if len(cur_subs) > exp_subs:
                    mod["subs"] = cur_subs[:exp_subs]
                else:
                    mod["subs"] = cur_subs + [copy.deepcopy(EMPTY_SUB) for _ in range(exp_subs - len(cur_subs))]
                fixes.append(f"  slots: {mname} subs {len(cur_subs)}->{exp_subs}")
        # key order
        ordered = {}
        for key in KEY_ORDER:
            if key in mod:
                ordered[key] = mod[key]
        for key in mod:
            if key not in ordered:
                ordered[key] = mod[key]
        new_modules[mname] = ordered
    data["modules"] = new_modules
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n=== {fname}: {len(fixes)} fixes ===")
    for fix in fixes:
        print(fix)
    return len(fixes)

total = 0
for fname in sorted(os.listdir(BASE)):
    if fname.endswith(".json"):
        total += process_file(os.path.join(BASE, fname))
print(f"\n[TOTAL] {total} fixes")
