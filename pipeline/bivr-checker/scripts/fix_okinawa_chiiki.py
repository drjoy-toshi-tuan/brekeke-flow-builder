#!/usr/bin/env python3
"""Stage 1: Structural fix for 沖縄県立南部医療センター_地域連携"""
import json, sys, copy

sys.stdout.reconfigure(encoding='utf-8')

INPUT = 'output/沖縄県立南部医療センター_地域連携_20260415.json'

with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

mods = data['modules']
fixes = []

# ============================================================
# 1. Add 冒頭_アナウンス module (FLOW-007)
# ============================================================
mods['冒頭_アナウンス'] = {
    'layout': {'x': 0, 'y': 960},
    'next': [{'condition': '^.*$', 'label': 'Next Module', 'nextModuleName': '緊急対応確認'}],
    'subs': [{'moduleName': 'save-冒頭_アナウンス', 'label': 'save-冒頭_アナウンス'}, {'moduleName': '', 'label': ''}, {'moduleName': '', 'label': ''}],
    'name': '冒頭_アナウンス',
    'description': '',
    'matchingmethod': 1,
    'type': 'drjoy^Text To Speech$Text to speech',
    'params': {'prompt': '', 'stop_by_dtmf': 'No'}
}
mods['save-冒頭_アナウンス'] = {
    'layout': {'x': -280, 'y': 1180},
    'next': [],
    'subs': [],
    'name': 'save-冒頭_アナウンス',
    'description': '',
    'matchingmethod': 1,
    'type': 'drjoy^Persistence$save2db',
    'params': {}
}
# Redirect 受付時間判定 true → 冒頭_アナウンス
for n in mods['受付時間判定']['next']:
    if n.get('condition') == '^true$' and n.get('nextModuleName') == '緊急対応確認':
        n['nextModuleName'] = '冒頭_アナウンス'
        fixes.append('受付時間判定: true → 冒頭_アナウンス')
fixes.append('Added 冒頭_アナウンス + save-冒頭_アナウンス')

# ============================================================
# 2. Fix matchingmethod for Retry counters (should be 0)
# ============================================================
for name, mod in mods.items():
    if mod['type'] == 'drjoy^Text To Speech$Speech Retry Counter':
        if mod['matchingmethod'] != 0:
            mod['matchingmethod'] = 0
            fixes.append(f'{name}: matchingmethod 1 → 0')

# ============================================================
# 3. Fix {TTS_AI: → {tts_g: everywhere
# ============================================================
for name, mod in mods.items():
    params = mod.get('params', {})
    for key in ['prompt', 'prompt_true', 'prompt_false']:
        if key in params and isinstance(params[key], str):
            orig = params[key]
            params[key] = params[key].replace('{TTS_AI:', '{tts_g:')
            params[key] = params[key].replace('{tts_ai:', '{tts_g:')
            if params[key] != orig:
                fixes.append(f'{name}.{key}: TTS_AI → tts_g')

# ============================================================
# 4. Fix Retry false targets + prompt_false
# ============================================================
retry_fixes = {
    'リトライ_緊急対応確認': {
        'false_target': '緊急対応確認',
        'prompt_false': '',
        'reason': '無限ループ(必須:緊急対応有無)'
    },
    'リトライ_医療機関名': {
        'false_target': '入電者氏名',
        'prompt_false': '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}',
        'reason': '次へ進む(任意)'
    },
    'リトライ_入電者氏名': {
        'false_target': '用件確認',
        'prompt_false': '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}',
        'reason': '次へ進む(任意)'
    },
    'リトライ_用件確認': {
        'false_target': '用件確認',
        'prompt_false': '',
        'reason': '無限ループ(必須:用件選択)'
    },
    'リトライ_診療科': {
        'false_target': '診療科',
        'prompt_false': '',
        'reason': '無限ループ(必須:診療科)'
    },
    'リトライ_担当者名': {
        'false_target': 'jump_患者生年月日聴取',
        'prompt_false': '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}',
        'reason': '次へ進む(任意)'
    },
    'リトライ_問い合わせ内容': {
        'false_target': '完了フラグ_通話完了',
        'prompt_false': '{tts_g:かしこまりました。内容は担当者にて確認いたします。}',
        'reason': '次へ進む(最終聴取)'
    },
    'リトライ_FAX送信時期': {
        'false_target': '完了フラグ_外来入院完了',
        'prompt_false': '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}',
        'reason': '次へ進む(任意)'
    },
    'リトライ_返信期限': {
        'false_target': '完了フラグ_通話完了',
        'prompt_false': '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}',
        'reason': '次へ進む(任意)'
    },
}

for retry_name, fix in retry_fixes.items():
    mod = mods[retry_name]
    for n in mod['next']:
        if n.get('label') == 'No more':
            old = n['nextModuleName']
            n['nextModuleName'] = fix['false_target']
            fixes.append(f"{retry_name}: false {old} → {fix['false_target']} ({fix['reason']})")
    mod['params']['prompt_false'] = fix['prompt_false']

# ============================================================
# 5. Fix next/subs slot counts
# ============================================================
empty_next = {'condition': '', 'label': '', 'nextModuleName': ''}
empty_subs = {'moduleName': '', 'label': ''}

slot_spec = {
    'drjoy^Text To Speech$Text to speech': (1, 3),
    'drjoy^AmiVoice$Speech to Text': (11, 3),
    'drjoy^External Integration$DTMF AmiVoice STT Input': (11, 3),
    'drjoy^External Integration$generate_by_OpenAI': (10, 3),
    'drjoy^Text To Speech$Speech Retry Counter': (2, 3),
    'drjoy^Persistence$save2db': (0, 0),
    'drjoy^Persistence$saveCompletionFlag2db': (1, 3),
    'drjoy^Persistence$saveContext2DB': (1, 3),
    'drjoy^Persistence$saveContextModel2DB': (1, 3),
    'drjoy^Incoming$incoming-classifier': (5, 3),
    'drjoy^External Integration$acceptance_times': (4, 3),
    'drjoy^Custom Module$Custom Jump to Flow': (1, 3),
    'Custom$wait': (1, 3),
    '@IVR$Disconnect': (0, 0),
    'drjoy^Context Logic$ContextMatchRouter': (10, 3),
    '@General$Script': (12, 0),
}

for name, mod in mods.items():
    t = mod['type']
    spec = slot_spec.get(t)
    if not spec:
        continue
    expected_next, expected_subs = spec

    # Fix next
    current_next = mod.get('next', [])
    if len(current_next) < expected_next:
        while len(current_next) < expected_next:
            current_next.append(copy.deepcopy(empty_next))
        mod['next'] = current_next
        fixes.append(f'{name}: padded next to {expected_next}')
    elif len(current_next) > expected_next:
        # Trim empty slots from end
        while len(current_next) > expected_next:
            last = current_next[-1]
            if not last.get('nextModuleName') and not last.get('condition'):
                current_next.pop()
            else:
                break
        mod['next'] = current_next
        if len(current_next) != expected_next:
            fixes.append(f'WARNING: {name}: next={len(current_next)}, expected={expected_next}')
        else:
            fixes.append(f'{name}: trimmed next to {expected_next}')

    # Fix subs
    current_subs = mod.get('subs', [])
    if len(current_subs) < expected_subs:
        while len(current_subs) < expected_subs:
            current_subs.append(copy.deepcopy(empty_subs))
        mod['subs'] = current_subs
        fixes.append(f'{name}: padded subs to {expected_subs}')
    elif len(current_subs) > expected_subs:
        if expected_subs == 0:
            all_empty = all(not s.get('moduleName') for s in current_subs)
            if all_empty:
                mod['subs'] = []
                fixes.append(f'{name}: cleared empty subs')

# ============================================================
# 6. Fix fields (saveContextModel2DB)
# ============================================================
fields = json.loads(mods['コンテキスト設定']['params']['fields'])
existing_by_name = {f['contextName']: f for f in fields}

# Preserve original classification rangeValues
cls_rv = existing_by_name.get('classification', {}).get('rangeValues', [
    {'value': '外来入院申込み', 'order': 1},
    {'value': '情報提供依頼', 'order': 2},
    {'value': '入退院支援室', 'order': 3},
    {'value': 'その他お問い合わせ', 'order': 4},
])
# Remove 'id' from classification rangeValues if present (should be order+value only)
cls_rv = [{'value': r['value'], 'order': r['order']} for r in cls_rv]

# Preserve clinicalDepartment rangeValues
dept_rv = existing_by_name.get('clinicalDepartment', {}).get('rangeValues', [{'value': 'IVRセンター', 'order': 1}])
dept_rv = [{'value': r['value'], 'order': r['order']} for r in dept_rv]

standard_fields = [
    {'contextName': 'classification', 'contextNameJp': '区分', 'displayType': 'CLASSIFICATION',
     'rangeValues': cls_rv, 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'patientName', 'contextNameJp': '患者名', 'displayType': 'TEXT',
     'rangeValues': [], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'medicalCardNumber', 'contextNameJp': '診察券番号', 'displayType': 'NUMBER',
     'rangeValues': [], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'clinicalDepartment', 'contextNameJp': '診療科', 'displayType': 'DEPARTMENT',
     'rangeValues': dept_rv, 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'patientDateOfBirth', 'contextNameJp': '生年月日(和暦)', 'displayType': 'DATE_OF_BIRTH',
     'rangeValues': [], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'reason', 'contextNameJp': '理由', 'displayType': 'TEXT',
     'rangeValues': [], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'reservationDate', 'contextNameJp': '予約日', 'displayType': 'DATE',
     'rangeValues': [], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'telephoneNumber', 'contextNameJp': '電話番号', 'displayType': 'PHONE_NUMBER_CALL',
     'rangeValues': [], 'editable': False, 'deletable': False, 'itemDefault': True},
    {'contextName': 'additionalPhoneNumber', 'contextNameJp': '連絡先電話番号', 'displayType': 'PHONE_NUMBER',
     'rangeValues': [], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'status', 'contextNameJp': '状態', 'displayType': 'STATUS',
     'rangeValues': [
         {'id': '0', 'value': '途中切断', 'order': 0},
         {'id': '1', 'value': '未処理', 'order': 1},
         {'id': '2', 'value': '代表案内', 'order': 2},
         {'id': '3', 'value': '転送', 'order': 3},
         {'id': '6', 'value': '時間外', 'order': 6},
     ], 'editable': True, 'deletable': False, 'itemDefault': True},
    {'contextName': 'callId', 'contextNameJp': '通話ID', 'displayType': 'NUMBER',
     'rangeValues': [], 'editable': True, 'deletable': True, 'itemDefault': False},
    {'contextName': 'dateOfCall', 'contextNameJp': '入電日時', 'displayType': 'DATE',
     'rangeValues': [], 'editable': False, 'deletable': False, 'itemDefault': True},
]

# Custom fields (non-standard)
standard_names = {f['contextName'] for f in standard_fields}
custom_fields = []
for f in fields:
    if f['contextName'] not in standard_names:
        f['deletable'] = True
        f['itemDefault'] = False
        custom_fields.append(f)

new_fields = standard_fields + custom_fields
mods['コンテキスト設定']['params']['fields'] = json.dumps(new_fields, ensure_ascii=False, indent=2)
fixes.append(f'fields: rebuilt (12 standard + {len(custom_fields)} custom)')

# ============================================================
# 7. Shift layout for 冒頭_アナウンス insertion
# ============================================================
at_y = mods['受付時間判定']['layout']['y']
skip_names = {'冒頭', 'コンテキスト設定', '着信電話番号分類', '受付時間判定',
              '冒頭_アナウンス', 'save-冒頭_アナウンス',
              '完了フラグ_非通知', 'END_非通知', 'save-END_非通知', '切断_非通知',
              '完了フラグ_時間外', 'END_時間外', 'save-END_時間外', '切断_時間外'}
for name, mod in mods.items():
    if name in skip_names:
        continue
    if mod['layout']['y'] > at_y:
        mod['layout']['y'] += 240
fixes.append('Layout: shifted modules down 240px for 冒頭_アナウンス')

# ============================================================
# 8. Ensure key ordering: layout→next→subs→name→description→matchingmethod→type→params
# ============================================================
key_order = ['layout', 'next', 'subs', 'name', 'description', 'matchingmethod', 'type', 'params']
new_modules = {}
for name, mod in mods.items():
    ordered = {}
    for k in key_order:
        if k in mod:
            ordered[k] = mod[k]
    # Add any remaining keys
    for k in mod:
        if k not in ordered:
            ordered[k] = mod[k]
    new_modules[name] = ordered
data['modules'] = new_modules

# ============================================================
# Save
# ============================================================
with open(INPUT, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f'Total fixes applied: {len(fixes)}')
for fix in fixes:
    print(f'  ✓ {fix}')
