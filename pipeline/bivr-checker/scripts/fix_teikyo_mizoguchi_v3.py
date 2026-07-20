#!/usr/bin/env python3
"""
fix_teikyo_mizoguchi_v3.py — 帝京大学附属溝口病院 v3 修正パッチ

修正内容:
  Fix 1: Retry モジュール save2db 未接続 26件 → 新規 save2db 作成＆subs接続
  Fix 2: Retry false ルーティング修正 (7件)
         - リトライ_用件確認 false → 問合せ内容_聴取（その他問い合わせ）
         - 分岐があるリトライ 6件 → 無限ループ（false → true先と同じ）
  Fix 3: レイアウト整理
         - ユーザー手修正版のレイアウト座標を採用
         - 新規 save2db モジュールの座標を適切に配置
  Fix 4: .bivr 再構築
"""

import json, os, sys, glob, zipfile
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FIXED_DIR = "output/帝京大学付属溝口病院/fixed/flows"
MAIN_FLOW = os.path.join(FIXED_DIR, "帝京溝口$診療_20260413.json")
USER_FLOW = "output/帝京大学付属溝口病院/user_fixed/flows/帝京溝口$診療_20260413_1.json"
BIVR_OUT = "output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed.bivr"

print("=== 帝京大学附属溝口病院 v3 修正パッチ ===\n")

with open(MAIN_FLOW, encoding='utf-8') as f:
    flow = json.load(f)
mods = flow['modules']

with open(USER_FLOW, encoding='utf-8') as f:
    user_flow = json.load(f)
u_mods = user_flow['modules']

# =========================================================
# Fix 3 (先行): ユーザーレイアウト適用
# =========================================================
print("[Fix 3] ユーザーレイアウト適用")
layout_applied = 0
for name, mod in mods.items():
    if name in u_mods and 'layout' in u_mods[name]:
        mod['layout'] = u_mods[name]['layout'].copy()
        layout_applied += 1
print(f"  [OK] {layout_applied} モジュールのレイアウト更新")

# =========================================================
# Fix 1: Retry モジュール save2db 未接続 → 修正
# =========================================================
print()
print("[Fix 1] Retry save2db 接続")

# Retry modules that need save2db
retry_no_save = []
for name, mod in mods.items():
    if mod.get('type') == 'drjoy^Text To Speech$Speech Retry Counter':
        subs = mod.get('subs', [])
        has_save = any(s.get('moduleName','').startswith('save-') for s in subs)
        if not has_save:
            retry_no_save.append(name)

print(f"  対象: {len(retry_no_save)} 件")

for retry_name in retry_no_save:
    save_name = f"save-{retry_name}"
    retry_mod = mods[retry_name]
    retry_layout = retry_mod.get('layout', {'x': 0, 'y': 0})

    # Create save2db module
    mods[save_name] = {
        'layout': {
            'x': retry_layout.get('x', 0) - 300,
            'y': retry_layout.get('y', 0),
        },
        'next': [],
        'subs': [
            {'moduleName': '', 'label': ''},
            {'moduleName': '', 'label': ''},
            {'moduleName': '', 'label': ''},
        ],
        'name': save_name,
        'description': '',
        'matchingmethod': 1,
        'type': 'drjoy^Persistence$save2db',
        'params': {
            'contextName': '',
            'contextDisplayType': 'TEXT',
        },
    }

    # Connect to retry module subs[0]
    subs = retry_mod.get('subs', [
        {'moduleName': '', 'label': ''},
        {'moduleName': '', 'label': ''},
        {'moduleName': '', 'label': ''},
    ])
    # Ensure subs has at least 3 slots
    while len(subs) < 3:
        subs.append({'moduleName': '', 'label': ''})
    subs[0] = {'moduleName': save_name, 'label': save_name}
    retry_mod['subs'] = subs

    print(f"  [OK] {retry_name} → subs[0]={save_name}")

# =========================================================
# Fix 2: Retry false ルーティング修正
# =========================================================
print()
print("[Fix 2] Retry false ルーティング修正")

# 用件確認 → その他問い合わせ
mod_r = mods.get('リトライ_用件確認')
if mod_r:
    for n in mod_r['next']:
        if n['condition'] == 'false':
            n['nextModuleName'] = '問合せ内容_聴取'
    mod_r['params']['prompt_false'] = ''
    print("  [OK] リトライ_用件確認 false → 問合せ内容_聴取（その他問い合わせ）")

# 無限ループ対象（分岐がある問い）: false → true先と同じ
infinite_loop_targets = [
    'リトライ_診察券確認',
    'リトライ_本日予約確認',
    'リトライ_診療科_再診',
    'リトライ_診療科_初診',
    'リトライ_診療科_変更',
    'リトライ_診療科_キャンセル',
]

for name in infinite_loop_targets:
    mod = mods.get(name)
    if not mod:
        print(f"  [SKIP] {name} not found")
        continue
    true_dest = ''
    for n in mod['next']:
        if n['condition'] == 'true':
            true_dest = n['nextModuleName']
    for n in mod['next']:
        if n['condition'] == 'false':
            old_dest = n['nextModuleName']
            n['nextModuleName'] = true_dest
            # 無限ループの prompt_false は空文字
            mod['params']['prompt_false'] = ''
    print(f"  [OK] {name} false → {true_dest}（無限ループ）")

# =========================================================
# Save
# =========================================================
with open(MAIN_FLOW, 'w', encoding='utf-8') as f:
    json.dump(flow, f, ensure_ascii=False, indent=2)
print(f"\n[OK] saved: {MAIN_FLOW}")

# Verify save2db on retry
retry_still_missing = []
for name, mod in mods.items():
    if mod.get('type') == 'drjoy^Text To Speech$Speech Retry Counter':
        subs = mod.get('subs', [])
        has_save = any(s.get('moduleName','').startswith('save-') for s in subs)
        if not has_save:
            retry_still_missing.append(name)
print(f"Retry without save2db remaining: {retry_still_missing}")

# =========================================================
# Rebuild .bivr
# =========================================================
flow_files = glob.glob(os.path.join(FIXED_DIR, "*.json"))
with zipfile.ZipFile(BIVR_OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fpath in flow_files:
        with open(fpath, encoding='utf-8') as f:
            fl = json.load(f)
        flow_name = fl.get("name", "")
        entry_name = f"flows/@flow_{quote(flow_name, safe='')}.txt"
        json_str = json.dumps(fl, ensure_ascii=False, separators=(',', ':'))
        zf.writestr(entry_name, json_str.encode('utf-8'))
size = os.path.getsize(BIVR_OUT)
print(f"[OK] .bivr rebuilt: {BIVR_OUT} ({size:,} bytes)")
print("\n=== 完了 ===")
