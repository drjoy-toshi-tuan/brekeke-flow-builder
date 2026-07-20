#!/usr/bin/env python3
"""
fix_teikyo_mizoguchi_v2_layout.py — レイアウト修正（LAYOUT-003解消）

y座標をスケールして y_range >= modules*100 を満たす
"""
import json, glob, zipfile, sys
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')

FIXED_DIR = "output/帝京大学付属溝口病院/fixed/flows"
MAIN_FLOW = f"{FIXED_DIR}/帝京溝口$診療_20260413.json"
BIVR_OUT = "output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed.bivr"

with open(MAIN_FLOW, encoding='utf-8') as f:
    flow = json.load(f)
mods = flow['modules']

ys = [m['layout']['y'] for m in mods.values() if 'layout' in m]
y_range = max(ys) - min(ys)
n_mods = len(mods)
needed = n_mods * 100
factor = (needed / y_range) * 1.05 if y_range > 0 else 1
print(f"y_range: {y_range} → target: {needed} px, scale factor: {factor:.2f}")

for mod in mods.values():
    if 'layout' in mod:
        mod['layout']['y'] = round(mod['layout']['y'] * factor)

ys_new = [m['layout']['y'] for m in mods.values() if 'layout' in m]
xs_new = [m['layout']['x'] for m in mods.values() if 'layout' in m]
print(f"New x_range: {max(xs_new)-min(xs_new)}, y_range: {max(ys_new)-min(ys_new)} (need {needed})")

with open(MAIN_FLOW, 'w', encoding='utf-8') as f:
    json.dump(flow, f, ensure_ascii=False, indent=2)
print(f"[OK] saved: {MAIN_FLOW}")

flow_files = glob.glob(f"{FIXED_DIR}/*.json")
with zipfile.ZipFile(BIVR_OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fpath in flow_files:
        with open(fpath, encoding='utf-8') as f:
            fl = json.load(f)
        flow_name = fl.get("name", "")
        entry_name = f"flows/@flow_{quote(flow_name, safe='')}.txt"
        json_str = json.dumps(fl, ensure_ascii=False, separators=(',', ':'))
        zf.writestr(entry_name, json_str.encode('utf-8'))
import os
size = os.path.getsize(BIVR_OUT)
print(f"[OK] .bivr rebuilt: {BIVR_OUT} ({size:,} bytes)")
print("=== 完了 ===")
