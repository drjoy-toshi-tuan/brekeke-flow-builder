"""
fix_teikyo_mizoguchi_v5.py

v5修正: ユーザー手修正版(user_v3)をベースに分岐漏れを修正

ベース: output/帝京大学付属溝口病院/user_fixed_v4/flows/帝京溝口_user_v3.json
出力:   output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed_v5.bivr
        output/帝京大学付属溝口病院/fixed_v5/flows/帝京溝口_v5.json

修正内容:
  Fix A: OpenAI_前回と同じ確認
    - ^はい$ -> 担当医_聴取_再診 を catch-all の前に挿入
    - (現状: ^.+$ -> 診療科_聴取_再診 のみ)
    - (修正後: ^はい$ -> 担当医_聴取_再診, ^.+$ -> 診療科_聴取_再診)

  Fix B: OpenAI_紹介状確認
    - ^はい$ -> 診療科_聴取_初診 を明示追加
    - ^いいえ$ -> 診療科_聴取_初診 を明示追加
    - catch-all ^.+$ は残す（フォールバック）
"""

import json
import zipfile
import urllib.parse
import shutil
import os

BASE_DIR = "output/帝京大学付属溝口病院"
INPUT_JSON = f"{BASE_DIR}/user_fixed_v4/flows/帝京溝口_user_v3.json"
OUT_DIR = f"{BASE_DIR}/fixed_v5/flows"
OUT_JSON = f"{OUT_DIR}/帝京溝口_v5.json"
OUT_BIVR = f"{BASE_DIR}/帝京大学附属溝口病院_fixed_v5.bivr"

os.makedirs(OUT_DIR, exist_ok=True)

with open(INPUT_JSON, "r", encoding="utf-8") as f:
    flow = json.load(f)

modules = flow["modules"]

# =====================================
# Fix A: OpenAI_前回と同じ確認
# ^はい$ -> 担当医_聴取_再診 を catch-all の前に挿入
# =====================================
MODULE_A = "OpenAI_前回と同じ確認"
if MODULE_A in modules:
    m = modules[MODULE_A]
    new_next = []
    inserted = False
    for slot in m["next"]:
        cond = slot.get("condition", "")
        if cond == "^.+$" and not inserted:
            # Insert はい branch before catch-all
            new_next.append({
                "condition": "^はい$",
                "label": "はい",
                "nextModuleName": "担当医_聴取_再診"
            })
            inserted = True
        new_next.append(slot)
    m["next"] = new_next
    print(f"[Fix A] {MODULE_A}: ^はい$ -> 担当医_聴取_再診 を挿入")
else:
    print(f"[WARN] {MODULE_A} が見つかりません")

# =====================================
# Fix B: OpenAI_紹介状確認
# ^はい$ / ^いいえ$ -> 診療科_聴取_初診 を明示追加（catch-allの前）
# =====================================
MODULE_B = "OpenAI_紹介状確認"
if MODULE_B in modules:
    m = modules[MODULE_B]
    new_next = []
    inserted_b = False
    for slot in m["next"]:
        cond = slot.get("condition", "")
        if cond == "^.+$" and not inserted_b:
            # Insert はい/いいえ branches before catch-all
            new_next.append({
                "condition": "^はい$",
                "label": "はい",
                "nextModuleName": "診療科_聴取_初診"
            })
            new_next.append({
                "condition": "^いいえ$",
                "label": "いいえ",
                "nextModuleName": "診療科_聴取_初診"
            })
            inserted_b = True
        new_next.append(slot)
    m["next"] = new_next
    print(f"[Fix B] {MODULE_B}: ^はい$/^いいえ$ -> 診療科_聴取_初診 を挿入")
else:
    print(f"[WARN] {MODULE_B} が見つかりません")

# =====================================
# Save fixed JSON
# =====================================
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(flow, f, ensure_ascii=False, indent=2)
print(f"[OK] JSON saved: {OUT_JSON}")

# =====================================
# Build .bivr
# =====================================
flow_name = flow["name"]
encoded_name = urllib.parse.quote(flow_name, safe="")
txt_filename = f"@flow_{encoded_name}.txt"
flow_json_str = json.dumps(flow, ensure_ascii=False)

with zipfile.ZipFile(OUT_BIVR, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(f"flows/{txt_filename}", flow_json_str)

print(f"[OK] .bivr built: {OUT_BIVR}")
print(f"     flow name: {flow_name}")
print(f"     modules: {len(modules)}")

# =====================================
# Verify Fix A
# =====================================
print()
print("=== 検証: OpenAI_前回と同じ確認 ===")
for slot in modules[MODULE_A]["next"]:
    if slot.get("condition"):
        print(f"  {slot['condition']} -> {slot['nextModuleName']}")

# =====================================
# Verify Fix B
# =====================================
print()
print("=== 検証: OpenAI_紹介状確認 ===")
for slot in modules[MODULE_B]["next"]:
    if slot.get("condition"):
        print(f"  {slot['condition']} -> {slot['nextModuleName']}")
