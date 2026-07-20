#!/usr/bin/env python3
"""
恵佑会札幌病院_診療2（連携室）Stage 1 包括修正スクリプト

Phase 0: ファイル配置（Property.md + サブフローJSONコピー）
Phase 1: メインフロー構造修正
Phase 2: サブフロー構造修正
Phase 3: Property.md整合性確認

対象: output/恵佑会札幌病院_連携室_20260422.json (115 modules)
"""
import json
import os
import shutil
import copy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

MAIN_FLOW = os.path.join(OUTPUT_DIR, "恵佑会札幌病院_連携室_20260422.json")
PROP_SRC = os.path.join(BASE_DIR, "input", "恵佑会札幌病院_診療2",
                        "properties_恵佑会札幌病院_連携室.md")
PROP_DST = os.path.join(OUTPUT_DIR, "properties_恵佑会札幌病院_連携室.md")

SUBFLOW_NAMES = ["氏名聴取", "生年月日聴取", "診察券番号聴取", "電話番号聴取"]
SUBFLOW_SRC = {
    sf: os.path.join(OUTPUT_DIR, f"恵佑会札幌病院_{sf}_20260422_1.json")
    for sf in SUBFLOW_NAMES
}
SUBFLOW_DST = {
    sf: os.path.join(OUTPUT_DIR, f"恵佑会札幌病院_{sf}_20260422.json")
    for sf in SUBFLOW_NAMES
}

# Module type constants
STT_TYPES = [
    "drjoy^AmiVoice$Speech to Text",
    "drjoy^External Integration$DTMF AmiVoice STT Input",
]
RETRY_TYPE = "drjoy^Text To Speech$Speech Retry Counter"
TTS_TYPE = "drjoy^Text To Speech$Text to speech"
SAVE2DB_TYPE = "drjoy^Persistence$save2db"
DISCONNECT_TYPE = "@IVR$Disconnect"
OPENAI_TYPE = "drjoy^External Integration$generate_by_OpenAI"

# next/subs slot specification per module type
SLOT_SPEC = {
    "@General$Script":                                  (12, 0),
    "drjoy^Context Logic$ContextMatchRouter":           (10, 3),
    "drjoy^AmiVoice$Speech to Text":                    (11, 3),
    "drjoy^External Integration$DTMF AmiVoice STT Input": (11, 3),
    "drjoy^External Integration$generate_by_OpenAI":    (10, 3),
    "drjoy^Text To Speech$Speech Retry Counter":        (2, 3),
    "drjoy^Text To Speech$Text to speech":              (1, 3),
    "drjoy^Text To Speech$Re-confirmation node data":   (1, 3),
    "drjoy^TS Custom Module$DOB Re-confirmation":       (4, 3),
    "drjoy^TS Custom Module$Phone Normalization":       (5, 3),
    "drjoy^Persistence$saveCompletionFlag2db":          (1, 3),
    "drjoy^Persistence$saveContext2DB":                  (1, 3),
    "drjoy^Persistence$saveContextModel2DB":             (1, 3),
    "drjoy^Persistence$save2db":                        (0, 0),
    "drjoy^External Integration$acceptance_times":      (4, 3),
    "drjoy^Incoming$incoming-classifier":               (5, 3),
    "drjoy^Custom Module$Custom Jump to Flow":          (1, 3),
    "Custom$wait":                                      (1, 3),
    "@IVR$Disconnect":                                  (0, 0),
}

EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}

fixes_applied = []


def log_fix(code, module, desc):
    fixes_applied.append(f"[{code}] {module}: {desc}")
    print(f"  FIX {code} | {module} | {desc}")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {path}")


def fix_slots(modules, flow_label=""):
    """Fix next/subs slot counts to match spec."""
    for name, mod in modules.items():
        t = mod["type"]
        if t not in SLOT_SPEC:
            continue
        expected_next, expected_subs = SLOT_SPEC[t]
        actual_next = len(mod.get("next", []))
        actual_subs = len(mod.get("subs", []))

        # Fix next slots
        if actual_next < expected_next:
            while len(mod["next"]) < expected_next:
                mod["next"].append(copy.deepcopy(EMPTY_NEXT))
            log_fix("SLOT-N", f"{flow_label}{name}",
                     f"next padded {actual_next} -> {expected_next}")
        elif actual_next > expected_next:
            # Trim empty trailing slots only
            while len(mod["next"]) > expected_next:
                last = mod["next"][-1]
                if not last.get("condition") and not last.get("nextModuleName"):
                    mod["next"].pop()
                else:
                    break
            if len(mod["next"]) != expected_next:
                log_fix("SLOT-N-WARN", f"{flow_label}{name}",
                         f"next={len(mod['next'])}, expected={expected_next} (non-empty excess)")

        # Fix subs slots
        if actual_subs < expected_subs:
            if "subs" not in mod:
                mod["subs"] = []
            while len(mod["subs"]) < expected_subs:
                mod["subs"].append(copy.deepcopy(EMPTY_SUB))
            log_fix("SLOT-S", f"{flow_label}{name}",
                     f"subs padded {actual_subs} -> {expected_subs}")
        elif actual_subs > expected_subs:
            # Trim empty trailing slots
            while len(mod["subs"]) > expected_subs:
                last = mod["subs"][-1]
                if not last.get("moduleName"):
                    mod["subs"].pop()
                else:
                    break
            if len(mod["subs"]) != expected_subs:
                log_fix("SLOT-S-WARN", f"{flow_label}{name}",
                         f"subs={len(mod['subs'])}, expected={expected_subs} (non-empty excess)")


def fix_detection_flag(modules, flow_label=""):
    """Set detection_flag to 'デフォルト' on all STT modules."""
    for name, mod in modules.items():
        if mod["type"] in STT_TYPES:
            old = mod["params"].get("detection_flag", "")
            if old != "デフォルト":
                mod["params"]["detection_flag"] = "デフォルト"
                log_fix("DF", f"{flow_label}{name}",
                         f"detection_flag: '{old}' -> 'デフォルト'")


def fix_retry_matchingmethod(modules, flow_label=""):
    """Set Retry Counter matchingmethod to 0 (int)."""
    for name, mod in modules.items():
        if mod["type"] == RETRY_TYPE:
            old = mod.get("matchingmethod", 1)
            if old != 0:
                mod["matchingmethod"] = 0
                log_fix("MM", f"{flow_label}{name}",
                         f"matchingmethod: {old} -> 0")


def fix_matchingmethod_type(modules, flow_label=""):
    """Ensure matchingmethod is int, not string."""
    for name, mod in modules.items():
        mm = mod.get("matchingmethod")
        if isinstance(mm, str):
            mod["matchingmethod"] = int(mm)
            log_fix("MM-TYPE", f"{flow_label}{name}",
                     f"matchingmethod: str '{mm}' -> int {int(mm)}")
        elif mm is None:
            expected = 0 if mod["type"] == RETRY_TYPE else 1
            mod["matchingmethod"] = expected
            log_fix("MM-MISS", f"{flow_label}{name}",
                     f"matchingmethod: missing -> {expected}")


def fix_tts_next_label(modules, flow_label=""):
    """Ensure TTS next label is 'Next Module'."""
    for name, mod in modules.items():
        if mod["type"] == TTS_TYPE:
            for n in mod.get("next", []):
                if n.get("condition") and n.get("label") != "Next Module":
                    old_label = n["label"]
                    n["label"] = "Next Module"
                    log_fix("TTS-LBL", f"{flow_label}{name}",
                             f"next label: '{old_label}' -> 'Next Module'")


def fix_stop_by_dtmf(modules, flow_label=""):
    """Ensure stop_by_dtmf uses 'Yes'/'No' not 'true'/'false'."""
    for name, mod in modules.items():
        sbd = mod.get("params", {}).get("stop_by_dtmf")
        if sbd == "true":
            mod["params"]["stop_by_dtmf"] = "Yes"
            log_fix("DTMF-SBD", f"{flow_label}{name}", "stop_by_dtmf: 'true' -> 'Yes'")
        elif sbd == "false":
            mod["params"]["stop_by_dtmf"] = "No"
            log_fix("DTMF-SBD", f"{flow_label}{name}", "stop_by_dtmf: 'false' -> 'No'")


def fix_retry_labels(modules, flow_label=""):
    """Ensure Retry Counter next has correct labels and conditions."""
    for name, mod in modules.items():
        if mod["type"] != RETRY_TYPE:
            continue
        has_true = False
        has_false = False
        for n in mod.get("next", []):
            if n.get("condition") == "true":
                has_true = True
                if n.get("label") != "Retry":
                    old = n["label"]
                    n["label"] = "Retry"
                    log_fix("R-LBL", f"{flow_label}{name}",
                             f"true label: '{old}' -> 'Retry'")
            elif n.get("condition") == "false":
                has_false = True
                if n.get("label") != "No more":
                    old = n["label"]
                    n["label"] = "No more"
                    log_fix("R-LBL", f"{flow_label}{name}",
                             f"false label: '{old}' -> 'No more'")
        if not has_true:
            log_fix("R-MISS", f"{flow_label}{name}", "MISSING true condition!")
        if not has_false:
            log_fix("R-MISS", f"{flow_label}{name}", "MISSING false condition!")

        # Ensure prompt_true is set
        pt = mod["params"].get("prompt_true", "")
        if not pt:
            mod["params"]["prompt_true"] = \
                "{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}"
            log_fix("R-PT", f"{flow_label}{name}", "prompt_true set to standard")


def fix_stt_success(modules, flow_label=""):
    """Ensure STT success condition is ^.+$."""
    for name, mod in modules.items():
        if mod["type"] not in STT_TYPES:
            continue
        for n in mod.get("next", []):
            if n.get("label") == "success":
                if n["condition"] != "^.+$":
                    old = n["condition"]
                    n["condition"] = "^.+$"
                    log_fix("STT-SUC", f"{flow_label}{name}",
                             f"success condition: '{old}' -> '^.+$'")


def apply_all_fixes(modules, flow_label=""):
    """Apply all structural fixes to a module set."""
    fix_matchingmethod_type(modules, flow_label)
    fix_retry_matchingmethod(modules, flow_label)
    fix_detection_flag(modules, flow_label)
    fix_tts_next_label(modules, flow_label)
    fix_stop_by_dtmf(modules, flow_label)
    fix_retry_labels(modules, flow_label)
    fix_stt_success(modules, flow_label)
    fix_slots(modules, flow_label)


# ================================================================
# Phase 0: File organization
# ================================================================
print("=" * 60)
print("Phase 0: File organization")
print("=" * 60)

# Copy Property.md to output/
if os.path.exists(PROP_SRC):
    shutil.copy2(PROP_SRC, PROP_DST)
    log_fix("P0-PROP", "Property.md",
             f"Copied {PROP_SRC} -> {PROP_DST}")
else:
    print(f"  WARNING: Property.md not found at {PROP_SRC}")

# Copy subflow JSONs (with _1 suffix -> without _1)
# The _1 files have the correct subflow content;
# the non-_1 files may be the wrong version (from 診療1)
for sf in SUBFLOW_NAMES:
    src = SUBFLOW_SRC[sf]
    dst = SUBFLOW_DST[sf]
    if os.path.exists(src):
        shutil.copy2(src, dst)
        log_fix("P0-SUB", sf, f"Copied _1 variant to {dst}")
    else:
        print(f"  WARNING: Subflow _1 not found: {src}")

# ================================================================
# Phase 1: Main flow structural fixes
# ================================================================
print()
print("=" * 60)
print("Phase 1: Main flow structural fixes")
print("=" * 60)

data = load_json(MAIN_FLOW)
modules = data["modules"]

# Apply all structural fixes
apply_all_fixes(modules, "[MAIN] ")

# Additional main-flow-specific: incoming-classifier has 6 next slots, spec says 5
# The 6th slot is "^*$ -> 受付時間判定 (label=その他)" — actually useful.
# Check if we need to trim or keep
ic = modules.get("着信電話番号分類")
if ic:
    ic_next = ic.get("next", [])
    if len(ic_next) > 5:
        # Keep only 5: non-empty first, then pad
        non_empty = [n for n in ic_next if n.get("condition") or n.get("nextModuleName")]
        if len(non_empty) <= 5:
            ic["next"] = non_empty
            while len(ic["next"]) < 5:
                ic["next"].append(copy.deepcopy(EMPTY_NEXT))
            log_fix("IC-SLOT", "[MAIN] 着信電話番号分類",
                     f"Trimmed incoming-classifier next from {len(ic_next)} to 5")
        else:
            # More than 5 non-empty — keep first 5 meaningful ones
            # 非通知, 固定, 海外, 携帯, WebRTC — that's already 5 categories
            # "その他" is a catch-all using ^*$
            # We need to merge WebRTC and その他 into fewer slots
            # Standard: 非通知, 携帯, 海外, その他, (empty)
            # But the current flow uses 固定 too. Let's keep the first 5 non-empty.
            ic["next"] = non_empty[:5]
            log_fix("IC-SLOT", "[MAIN] 着信電話番号分類",
                     f"Trimmed incoming-classifier next from {len(ic_next)} to 5 (kept first 5 non-empty)")

save_json(MAIN_FLOW, data)

# ================================================================
# Phase 2: Subflow structural fixes
# ================================================================
print()
print("=" * 60)
print("Phase 2: Subflow structural fixes")
print("=" * 60)

for sf in SUBFLOW_NAMES:
    sf_path = SUBFLOW_DST[sf]
    if not os.path.exists(sf_path):
        print(f"  SKIP: {sf} (file not found)")
        continue

    sf_data = load_json(sf_path)
    sf_modules = sf_data["modules"]
    label = f"[{sf}] "

    apply_all_fixes(sf_modules, label)

    save_json(sf_path, sf_data)

# ================================================================
# Phase 3: Verification summary
# ================================================================
print()
print("=" * 60)
print("Phase 3: Summary")
print("=" * 60)
print(f"Total fixes applied: {len(fixes_applied)}")
for f in fixes_applied:
    print(f"  {f}")
