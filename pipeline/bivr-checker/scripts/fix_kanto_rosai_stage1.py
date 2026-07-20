#!/usr/bin/env python3
"""Stage 1 追加修正: 関東労災病院 — structural_fixer がカバーしない項目"""
import json, os, copy

BASE = "output/関東労災病院/fixed/flows"

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
    "drjoy^TS Custom Module$DOB Re-confirmation": (4, 3),
    "drjoy^TS Custom Module$Phone Normalization": (5, 3),
}

EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}

KEY_ORDER = ["layout", "next", "subs", "name", "description", "matchingmethod", "type", "params"]


def fix_slot_counts(mod, mtype):
    fixes = []
    if mtype not in SLOT_COUNTS:
        return fixes
    expected_next, expected_subs = SLOT_COUNTS[mtype]

    cur_next = mod.get("next", [])
    cur_subs = mod.get("subs", [])

    if len(cur_next) != expected_next:
        if len(cur_next) > expected_next:
            mod["next"] = cur_next[:expected_next]
        else:
            mod["next"] = cur_next + [copy.deepcopy(EMPTY_NEXT) for _ in range(expected_next - len(cur_next))]
        fixes.append(f"next: {len(cur_next)} -> {expected_next}")

    if len(cur_subs) != expected_subs:
        if len(cur_subs) > expected_subs:
            mod["subs"] = cur_subs[:expected_subs]
        else:
            mod["subs"] = cur_subs + [copy.deepcopy(EMPTY_SUB) for _ in range(expected_subs - len(cur_subs))]
        fixes.append(f"subs: {len(cur_subs)} -> {expected_subs}")

    return fixes


def fix_key_order(mod):
    ordered = {}
    for key in KEY_ORDER:
        if key in mod:
            ordered[key] = mod[key]
    for key in mod:
        if key not in ordered:
            ordered[key] = mod[key]
    return ordered


def fix_detection_flag(mod, mtype):
    stt_types = [
        "drjoy^AmiVoice$Speech to Text",
        "drjoy^External Integration$DTMF AmiVoice STT Input",
    ]
    if mtype not in stt_types:
        return False
    params = mod.get("params", {})
    if params.get("detection_flag") != "デフォルト":
        old = params.get("detection_flag", "(未設定)")
        params["detection_flag"] = "デフォルト"
        return old
    return False


def fix_fields(mod):
    params = mod.get("params", {})
    fields_str = params.get("fields", "")
    if not fields_str:
        return []

    try:
        fields = json.loads(fields_str)
    except Exception:
        return ["fields JSON parse error"]

    fixes = []

    # Fix callId
    for f in fields:
        if f.get("contextName") == "callId":
            if f.get("itemDefault") is not False:
                f["itemDefault"] = False
                fixes.append("callId.itemDefault: true -> false")
            if f.get("displayType") != "NUMBER":
                old = f.get("displayType")
                f["displayType"] = "NUMBER"
                fixes.append(f"callId.displayType: {old} -> NUMBER")
            if f.get("editable") is not True:
                f["editable"] = True
                fixes.append("callId.editable -> true")

    # Fix clinicalDepartment displayType
    for f in fields:
        if f.get("contextName") == "clinicalDepartment":
            if f.get("displayType") != "DEPARTMENT":
                old = f.get("displayType")
                f["displayType"] = "DEPARTMENT"
                fixes.append(f"clinicalDepartment.displayType: {old} -> DEPARTMENT")

    # Fix status
    for f in fields:
        if f.get("contextName") == "status":
            if f.get("deletable") is not False:
                f["deletable"] = False
                fixes.append("status.deletable: true -> false")
            rv = f.get("rangeValues", [])
            required = [
                {"id": "0", "order": 0, "value": "途中切断"},
                {"id": "1", "order": 1, "value": "未処理"},
                {"id": "2", "order": 2, "value": "代表案内"},
                {"id": "3", "order": 3, "value": "転送"},
                {"id": "6", "order": 6, "value": "時間外"},
            ]
            new_rv = []
            for r in required:
                found = False
                for existing in rv:
                    if str(existing.get("id", "")) == r["id"]:
                        new_rv.append(existing)
                        found = True
                        break
                if not found:
                    new_rv.append(r)
                    fixes.append(f"status.rangeValues: added id={r['id']} ({r['value']})")
            f["rangeValues"] = new_rv

    # Check for reservationDate
    has_reservation = any(f.get("contextName") == "reservationDate" for f in fields)
    if not has_reservation:
        new_field = {
            "contextName": "reservationDate",
            "contextNameJp": "予約日",
            "displayType": "DATE",
            "rangeValues": [],
            "editable": True,
            "deletable": False,
            "itemDefault": True
        }
        idx = len(fields)
        for i, f in enumerate(fields):
            if f.get("contextName") == "callId":
                idx = i
                break
        fields.insert(idx, new_field)
        fixes.append("reservationDate field added")

    if fixes:
        params["fields"] = json.dumps(fields, ensure_ascii=False, indent=2)

    return fixes


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    fname = os.path.basename(filepath)
    all_fixes = []

    modules = data.get("modules", {})
    new_modules = {}

    for mname, mod in modules.items():
        mtype = mod.get("type", "")

        # 1. detection_flag
        old_flag = fix_detection_flag(mod, mtype)
        if old_flag:
            all_fixes.append(f"  [FIX] detection_flag: {mname} '{old_flag}' -> 'デフォルト'")

        # 2. fields (saveContextModel2DB)
        if mtype == "drjoy^Persistence$saveContextModel2DB":
            field_fixes = fix_fields(mod)
            for ff in field_fixes:
                all_fixes.append(f"  [FIX] fields: {mname} -- {ff}")

        # 3. slot counts
        slot_fixes = fix_slot_counts(mod, mtype)
        for sf in slot_fixes:
            all_fixes.append(f"  [FIX] slots: {mname} ({mtype}) -- {sf}")

        # 4. key order
        mod = fix_key_order(mod)

        new_modules[mname] = mod

    data["modules"] = new_modules

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== {fname} ===")
    if all_fixes:
        for fix in all_fixes:
            print(fix)
        print(f"  Total: {len(all_fixes)} fixes")
    else:
        print("  No fixes needed")

    return len(all_fixes)


if __name__ == "__main__":
    total = 0
    for fname in sorted(os.listdir(BASE)):
        if fname.endswith(".json"):
            total += process_file(os.path.join(BASE, fname))
    print(f"\n[TOTAL] {total} fixes applied")
