"""健生病院_健診_20260420.json のレイアウト修正スクリプト

CLAUDE.md基準:
- 冒頭チェーン: 冒頭(0,0)→CTX(0,240)→着信(0,480)→受付(0,720)→冒頭TTS(0,960)
- 会話ステップ内: TTS→STT: +220, TTS→OpenAI: +460, TTS→Retry: Δx=-280 Δy=+460
- ステップ間隔: Δy=800
- y_range >= modules×100
"""

import json
import sys
from collections import defaultdict

TARGET = "output/健生病院/健生病院_健診_20260420.json"


def get_type(modules, name):
    return modules[name]["type"] if name in modules else ""


def is_tts(t):
    return "Text to speech" in t or "Re-confirmation" in t


def is_stt(t):
    return "Speech to Text" in t or "DTMF" in t


def is_oai(t):
    return "generate_by_OpenAI" in t


def is_retry(t):
    return "Speech Retry Counter" in t


def is_save2db(t):
    return t == "drjoy^Persistence$save2db"


def get_next_names(mod):
    return [n["nextModuleName"] for n in mod.get("next", []) if n.get("nextModuleName")]


def get_sub_names(mod):
    return [s["moduleName"] for s in mod.get("subs", []) if s.get("moduleName")]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    with open(TARGET, encoding="utf-8") as f:
        data = json.load(f)

    modules = data["modules"]

    # === STEP 1: Fix header chain ===
    header_map = {
        "冒頭": {"x": 0, "y": 0},
        "コンテキスト設定": {"x": 0, "y": 240},
        "着信電話番号分類": {"x": 0, "y": 480},
        "受付時間判定": {"x": 0, "y": 720},
    }

    for name, layout in header_map.items():
        if name in modules:
            old = modules[name]["layout"]
            modules[name]["layout"] = dict(layout)
            print(f"Header: {name} ({old['x']},{old['y']}) -> ({layout['x']},{layout['y']})")

    # === STEP 2: Identify conversation step groups ===
    step_groups = []
    assigned = set(header_map.keys())

    for name, mod in modules.items():
        t = mod["type"]
        if not is_tts(t):
            continue
        if name in assigned:
            continue

        tts_x = mod["layout"]["x"]
        tts_y = mod["layout"]["y"]

        # Find STT in next chain
        stt_name = None
        oai_name = None
        retry_name = None

        nexts = get_next_names(mod)
        for nn in nexts:
            if nn in modules and is_stt(get_type(modules, nn)):
                stt_name = nn
                break

        if stt_name:
            stt_nexts = get_next_names(modules[stt_name])
            for nn in stt_nexts:
                if nn in modules and is_oai(get_type(modules, nn)):
                    oai_name = nn
                    break

            candidates = set(stt_nexts)
            if oai_name:
                candidates.update(get_next_names(modules[oai_name]))
            for nn in candidates:
                if nn in modules and is_retry(get_type(modules, nn)):
                    retry_name = nn
                    break

        if not retry_name and not stt_name:
            for nn in nexts:
                if nn in modules and is_retry(get_type(modules, nn)):
                    retry_name = nn
                    break

        # Find associated save2db modules
        save_names = []
        for sn in get_sub_names(mod):
            if sn in modules and is_save2db(get_type(modules, sn)):
                save_names.append(("tts_save", sn))
        if stt_name:
            for sn in get_sub_names(modules[stt_name]):
                if sn in modules and is_save2db(get_type(modules, sn)):
                    save_names.append(("stt_save", sn))
        if oai_name:
            for sn in get_sub_names(modules[oai_name]):
                if sn in modules and is_save2db(get_type(modules, sn)):
                    save_names.append(("oai_save", sn))
        if retry_name:
            for sn in get_sub_names(modules[retry_name]):
                if sn in modules and is_save2db(get_type(modules, sn)):
                    save_names.append(("retry_save", sn))

        group = {
            "tts": name,
            "stt": stt_name,
            "oai": oai_name,
            "retry": retry_name,
            "saves": save_names,
            "orig_x": tts_x,
            "orig_y": tts_y,
        }
        step_groups.append(group)
        assigned.add(name)
        if stt_name:
            assigned.add(stt_name)
        if oai_name:
            assigned.add(oai_name)
        if retry_name:
            assigned.add(retry_name)
        for _, sn in save_names:
            assigned.add(sn)

    step_groups.sort(key=lambda g: (g["orig_x"], g["orig_y"]))

    # === STEP 3: Position each x-column steps with dynamic spacing ===
    # Need y_range >= modules*100. Calculate step interval dynamically.
    x_col_steps = defaultdict(list)
    for g in step_groups:
        x_col_steps[g["orig_x"]].append(g)

    # Find the x-column with most steps to determine needed interval
    max_steps_in_col = max(len(gs) for gs in x_col_steps.values())
    target_y_range = len(modules) * 100
    # y_range = base_y(960) + (max_steps-1)*interval + 460(retry offset)
    # We need this >= target_y_range
    # interval = (target_y_range - 960 - 460) / (max_steps_in_col - 1)
    if max_steps_in_col > 1:
        needed_interval = (target_y_range - 960 - 460) / (max_steps_in_col - 1)
        step_interval = max(800, int(needed_interval) + 1)  # At least 800
    else:
        step_interval = 800
    print(f"\nStep interval: {step_interval} (max steps in column: {max_steps_in_col})")

    new_positions = {}

    for x, groups in sorted(x_col_steps.items()):
        groups.sort(key=lambda g: g["orig_y"])

        if x == 0:
            base_y = 960  # After header chain
        else:
            base_y = groups[0]["orig_y"]

        for i, g in enumerate(groups):
            step_y = base_y + i * step_interval
            tts_x = x
            tts_y = step_y

            new_positions[g["tts"]] = (tts_x, tts_y)

            if g["stt"]:
                new_positions[g["stt"]] = (tts_x, tts_y + 220)

            if g["oai"]:
                new_positions[g["oai"]] = (tts_x, tts_y + 460)

            if g["retry"]:
                new_positions[g["retry"]] = (tts_x - 280, tts_y + 460)

            for save_type, sn in g["saves"]:
                if save_type == "tts_save":
                    new_positions[sn] = (tts_x + 280, tts_y + 30)
                elif save_type == "stt_save":
                    new_positions[sn] = (tts_x + 280, tts_y + 250)
                elif save_type == "oai_save":
                    new_positions[sn] = (tts_x + 280, tts_y + 490)
                elif save_type == "retry_save":
                    new_positions[sn] = (tts_x, tts_y + 490)

    # === STEP 4: Handle non-step modules ===
    unassigned = []
    for name in modules:
        if name not in new_positions and name not in header_map:
            unassigned.append(name)

    # Calculate overall y scaling for unassigned modules
    max_new_y = max(ny for _, ny in new_positions.values()) if new_positions else 960
    orig_max_y = max(mod["layout"]["y"] for mod in modules.values())
    orig_min_step_y = 750  # original first TTS y on x=0

    for name in unassigned:
        mod = modules[name]
        ox = mod["layout"]["x"]
        oy = mod["layout"]["y"]

        if oy <= 720:
            # Near header area - scale proportionally
            if orig_min_step_y > 0:
                ratio = oy / orig_min_step_y
                new_y = int(960 * ratio)
            else:
                new_y = oy
            new_positions[name] = (ox, new_y)
        else:
            # Scale proportionally within step area
            if orig_max_y > orig_min_step_y:
                ratio = (oy - orig_min_step_y) / (orig_max_y - orig_min_step_y)
                new_step_max = max_new_y + 460
                new_y = int(960 + ratio * (new_step_max - 960))
            else:
                new_y = oy
            new_positions[name] = (ox, new_y)

    # === STEP 5: Apply new positions ===
    changes = 0
    for name, (nx, ny) in new_positions.items():
        old = modules[name]["layout"]
        if old["x"] != nx or old["y"] != ny:
            modules[name]["layout"] = {"x": nx, "y": ny}
            changes += 1

    for name, layout in header_map.items():
        modules[name]["layout"] = dict(layout)

    # === STEP 6: Verify y_range ===
    all_y = [mod["layout"]["y"] for mod in modules.values()]
    all_x = [mod["layout"]["x"] for mod in modules.values()]
    y_range = max(all_y) - min(all_y)
    x_range = max(all_x) - min(all_x)
    threshold = len(modules) * 100

    print(f"\nResults:")
    print(f"  Modules: {len(modules)}")
    print(f"  x_range: {x_range} (min={min(all_x)}, max={max(all_x)})")
    print(f"  y_range: {y_range} (min={min(all_y)}, max={max(all_y)})")
    print(f"  Threshold (modules*100): {threshold}")
    print(f"  y_range >= threshold: {y_range >= threshold}")
    print(f"  Changes applied: {changes}")

    # Show header chain
    print("\nHeader chain:")
    for name in ["冒頭", "コンテキスト設定", "着信電話番号分類", "受付時間判定"]:
        l = modules[name]["layout"]
        print(f"  {name}: ({l['x']}, {l['y']})")

    # Show first few steps on x=0
    print("\nFirst conversation steps (x=0):")
    x0_steps = [g for g in step_groups if g["orig_x"] == 0]
    for g in x0_steps[:5]:
        tts_l = modules[g["tts"]]["layout"]
        print(f"  {g['tts']}: ({tts_l['x']}, {tts_l['y']})")
        if g["stt"]:
            stt_l = modules[g["stt"]]["layout"]
            print(f"    STT {g['stt']}: ({stt_l['x']}, {stt_l['y']}) dy={stt_l['y']-tts_l['y']}")
        if g["oai"]:
            oai_l = modules[g["oai"]]["layout"]
            print(f"    OAI {g['oai']}: ({oai_l['x']}, {oai_l['y']}) dy={oai_l['y']-tts_l['y']}")
        if g["retry"]:
            r_l = modules[g["retry"]]["layout"]
            print(f"    Retry {g['retry']}: ({r_l['x']}, {r_l['y']}) dx={r_l['x']-tts_l['x']} dy={r_l['y']-tts_l['y']}")

    # LAYOUT-003 check
    print(f"\nLAYOUT-003 check: x_range={x_range} > 2000? {x_range > 2000}")
    print(f"  y_range={y_range} < modules*100={threshold}? {y_range < threshold}")
    if x_range > 2000 and y_range < threshold:
        print("  LAYOUT-003: WOULD TRIGGER")
    else:
        print("  LAYOUT-003: CLEAR")

    # Save
    with open(TARGET, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\nFile saved.")


if __name__ == "__main__":
    main()
