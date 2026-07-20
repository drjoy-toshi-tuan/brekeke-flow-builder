# -*- coding: utf-8 -*-
import json, sys, os, re
from collections import defaultdict

FLOW_PATH = 'C:/Users/takahashi.s/VSCode/bivr-checker/output/関越病院_薬剤部_20260416.json'
PROP_PATH = 'C:/Users/takahashi.s/VSCode/bivr-checker/input/関越病院_薬剤部/properties_関越病院_薬剤部.md'
OUTPUT_PATH = 'C:/Users/takahashi.s/VSCode/bivr-checker/output/check_関越病院_薬剤部.md'

with open(FLOW_PATH, 'r', encoding='utf-8') as f:
    flow = json.load(f)

with open(PROP_PATH, 'r', encoding='utf-8') as f:
    prop_text = f.read()

modules = flow.get('modules', {})
start_mod = flow.get('start', '')
issues = []

def add(sev, code, mod, msg):
    issues.append((sev, code, mod, msg))

SLOT_COUNTS = {
    '@General$Script': (12, 0),
    'drjoy^Context Logic$ContextMatchRouter': (10, 3),
    'drjoy^AmiVoice$Speech to Text': (11, 3),
    'drjoy^External Integration$DTMF AmiVoice STT Input': (11, 3),
    'drjoy^External Integration$generate_by_OpenAI': (10, 3),
    'drjoy^Text To Speech$Speech Retry Counter': (2, 3),
    'drjoy^Text To Speech$Text to speech': (1, 3),
    'drjoy^Text To Speech$Re-confirmation node data': (1, 3),
    'drjoy^Persistence$saveCompletionFlag2db': (1, 3),
    'drjoy^Persistence$saveContext2DB': (1, 3),
    'drjoy^Persistence$saveContextModel2DB': (1, 3),
    'drjoy^Persistence$save2db': (0, 0),
    'drjoy^External Integration$acceptance_times': (4, 3),
    'drjoy^Incoming$incoming-classifier': (5, 3),
    'drjoy^Custom Module$Custom Jump to Flow': (1, 3),
    'Custom$wait': (1, 3),
    '@IVR$Disconnect': (0, 0),
    '@IVR$Call Transfer': (1, 3),
}

KEY_ORDER = ['layout', 'next', 'subs', 'name', 'description', 'matchingmethod', 'type', 'params']

########################################
# Stage 1: STRUCTURAL_FIX
########################################

# 1. matchingmethod
for name, mod in modules.items():
    mm = mod.get('matchingmethod')
    mtype = mod.get('type', '')
    expected = 0 if mtype == 'drjoy^Text To Speech$Speech Retry Counter' else 1
    if mm != expected:
        add('CRITICAL', 'S1-MM', name, f'matchingmethod={mm} ({expected}であるべき)')
    if not isinstance(mm, int):
        add('CRITICAL', 'S1-MM-TYPE', name, f'matchingmethod型={type(mm).__name__} (int必須)')

# 2. Key order
for name, mod in modules.items():
    keys = list(mod.keys())
    filtered = [k for k in keys if k in KEY_ORDER]
    expected = [k for k in KEY_ORDER if k in filtered]
    if filtered != expected:
        add('WARNING', 'S1-KEYORDER', name, f'キー順序不正: {filtered}')

# 3. next/subs slot count
for name, mod in modules.items():
    mtype = mod.get('type', '')
    if mtype in SLOT_COUNTS:
        exp_next, exp_subs = SLOT_COUNTS[mtype]
        actual_next = len(mod.get('next', []))
        actual_subs = len(mod.get('subs', []))
        if actual_next != exp_next:
            add('CRITICAL', 'S1-SLOTS', name, f'nextスロット数={actual_next} (期待: {exp_next}, type={mtype})')
        if actual_subs != exp_subs:
            add('CRITICAL', 'S1-SLOTS', name, f'subsスロット数={actual_subs} (期待: {exp_subs}, type={mtype})')

# 5. Required fields
REQUIRED_FIELDS = ['name', 'description', 'matchingmethod', 'type', 'params', 'next', 'subs', 'layout']
for name, mod in modules.items():
    for field in REQUIRED_FIELDS:
        if field not in mod:
            add('CRITICAL', 'S-001', name, f'必須フィールド "{field}" 欠落')

# 6. detection_flag
for name, mod in modules.items():
    mtype = mod.get('type', '')
    if mtype in ('drjoy^AmiVoice$Speech to Text', 'drjoy^External Integration$DTMF AmiVoice STT Input'):
        df = mod.get('params', {}).get('detection_flag', '')
        if df != 'デフォルト':
            add('CRITICAL', 'S1-DETFLAG', name, f'detection_flag="{df}" ("デフォルト"であるべき)')

# 7. incoming-classifier count
ic_count = sum(1 for m in modules.values() if m.get('type') == 'drjoy^Incoming$incoming-classifier')
if ic_count != 1:
    add('CRITICAL', 'S1-IC', '', f'incoming-classifierが{ic_count}個 (1個のみ許可)')

# 8. save2db sub-module
for name, mod in modules.items():
    mtype = mod.get('type', '')
    needs_save2db = mtype in (
        'drjoy^Text To Speech$Text to speech',
        'drjoy^AmiVoice$Speech to Text',
        'drjoy^External Integration$DTMF AmiVoice STT Input',
        'drjoy^Text To Speech$Speech Retry Counter',
    )
    if needs_save2db:
        subs = mod.get('subs', [])
        has_save2db = any(s.get('moduleName', '').startswith('save-') for s in subs)
        if not has_save2db:
            add('WARNING', 'SB-001', name, f'save2dbサブモジュール未接続 (type={mtype})')

# 9. Retry settings
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Text To Speech$Speech Retry Counter':
        params = mod.get('params', {})
        nexts = mod.get('next', [])
        has_true = any(n.get('condition') == 'true' for n in nexts)
        has_false = any(n.get('condition') == 'false' for n in nexts)
        if not has_true:
            add('CRITICAL', 'R-001', name, 'condition="true" なし')
        if not has_false:
            add('CRITICAL', 'R-002', name, 'condition="false" なし')
        for n in nexts:
            if n.get('condition') == 'true' and n.get('label') != 'Retry':
                add('CRITICAL', 'R-003', name, f'true label="{n.get("label")}" ("Retry"であるべき)')
            if n.get('condition') == 'false' and n.get('label') != 'No more':
                add('CRITICAL', 'R-004', name, f'false label="{n.get("label")}" ("No more"であるべき)')
        pt = params.get('prompt_true', '')
        expected_pt = '{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}'
        if pt != expected_pt:
            add('WARNING', 'R-PT', name, f'prompt_true不一致: "{pt[:80]}"')
        if mod.get('matchingmethod') != 0:
            add('CRITICAL', 'R-MM', name, f'Retry matchingmethod={mod.get("matchingmethod")} (0であるべき)')

# 10. TTS settings
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Text To Speech$Text to speech':
        nexts = mod.get('next', [])
        if nexts:
            first = nexts[0]
            if first.get('label') != 'Next Module':
                add('CRITICAL', 'TTS-001', name, f'TTS next label="{first.get("label")}" ("Next Module"であるべき)')
        params = mod.get('params', {})
        sbd = params.get('stop_by_dtmf', '')
        if sbd not in ('Yes', 'No'):
            add('CRITICAL', 'TTS-002', name, f'stop_by_dtmf="{sbd}" ("Yes"/"No"であるべき)')

# 11. STT next
for name, mod in modules.items():
    mtype = mod.get('type', '')
    if mtype in ('drjoy^AmiVoice$Speech to Text', 'drjoy^External Integration$DTMF AmiVoice STT Input'):
        nexts = mod.get('next', [])
        conditions = [n.get('condition') for n in nexts if n.get('condition', '') != '']
        if '^TIMEOUT$' not in conditions:
            add('CRITICAL', 'STT-001', name, 'TIMEOUT遷移先なし')
        if '^ERROR$' not in conditions:
            add('CRITICAL', 'STT-001', name, 'ERROR遷移先なし')
        if '^NO_RESULT$' not in conditions:
            add('CRITICAL', 'STT-001', name, 'NO_RESULT遷移先なし')
        if '^.+$' not in conditions:
            add('CRITICAL', 'STT-003', name, 'success(^.+$)遷移先なし')
        for n in nexts:
            c = n.get('condition', '')
            if c and c not in ('^TIMEOUT$', '^ERROR$', '^NO_RESULT$', '^.+$', ''):
                if mtype == 'drjoy^AmiVoice$Speech to Text':
                    add('CRITICAL', 'STT-004', name, f'STTに個別パターン "{c}" (OpenAIで分岐すべき)')

# 12. OpenAI
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^External Integration$generate_by_OpenAI':
        params = mod.get('params', {})
        if not params.get('module', ''):
            add('CRITICAL', 'OAI-001', name, 'params.module が空')
        else:
            ref = params.get('module', '')
            if ref not in modules:
                add('CRITICAL', 'OAI-002', name, f'module参照先 "{ref}" がmodules内に存在しない')
        if not params.get('prompt', ''):
            add('CRITICAL', 'PROMPT-003', name, 'OpenAI prompt が空欄')
        ptts = params.get('promptTTS', '')
        if ptts and ptts.strip():
            add('WARNING', 'OAI-003', name, f'promptTTS に値あり: "{ptts[:30]}..."')

# 13. DTMF
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^External Integration$DTMF AmiVoice STT Input':
        params = mod.get('params', {})
        prompt = params.get('prompt', '')
        if '{recstart}' not in prompt:
            add('CRITICAL', 'DTMF-001', name, f'prompt に {{recstart}} なし: "{prompt[:40]}"')
        termdtmf = params.get('termdtmf', '')
        if termdtmf != '#':
            add('WARNING', 'DTMF-004', name, f'termdtmf="{termdtmf}" ("#"であるべき)')
        stop_play = params.get('stop_play_when_speech', '')
        if stop_play != 'Yes':
            add('WARNING', 'DTMF-004', name, f'stop_play_when_speech="{stop_play}" ("Yes"であるべき)')
        retry = params.get('retry', '')
        if retry == '0':
            add('WARNING', 'DTMF-003', name, 'retry="0"')

# 14. saveContextModel2DB fields
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Persistence$saveContextModel2DB':
        params = mod.get('params', {})
        fields_str = params.get('fields', '')
        if not fields_str:
            add('CRITICAL', 'CTX-014', name, 'fields が空')
            continue
        try:
            fields = json.loads(fields_str)
        except:
            add('CRITICAL', 'CTX-014', name, 'fields がJSON解析不能')
            continue
        callid_field = next((f for f in fields if f.get('contextName') == 'callId'), None)
        if callid_field:
            if callid_field.get('itemDefault') != False:
                add('CRITICAL', 'CTX-CALLID', name, f'callId.itemDefault={callid_field.get("itemDefault")} (falseであるべき)')
            if callid_field.get('displayType') != 'NUMBER':
                add('CRITICAL', 'CTX-CALLID', name, f'callId.displayType={callid_field.get("displayType")} (NUMBERであるべき)')
            if callid_field.get('editable') != True:
                add('CRITICAL', 'CTX-CALLID', name, f'callId.editable={callid_field.get("editable")} (trueであるべき)')
        else:
            add('CRITICAL', 'CTX-CALLID', name, 'callIdフィールドなし')
        status_field = next((f for f in fields if f.get('contextName') == 'status'), None)
        if status_field:
            rv = status_field.get('rangeValues', [])
            if len(rv) != 5:
                add('CRITICAL', 'CTX-STATUS', name, f'status.rangeValues={len(rv)}個 (5個であるべき: 途中切断/未処理/代表案内/転送/時間外)')
        else:
            add('CRITICAL', 'CTX-STATUS', name, 'statusフィールドなし')
        standard_names = ['classification','patientName','medicalCardNumber','clinicalDepartment',
                         'patientDateOfBirth','reason','reservationDate','telephoneNumber',
                         'additionalPhoneNumber','status','callId','dateOfCall']
        actual_names = [f.get('contextName') for f in fields]
        for sn in standard_names:
            if sn not in actual_names:
                add('WARNING', 'CTX-STD12', name, f'標準フィールド "{sn}" なし')
        unique_types = ['CLASSIFICATION','DEPARTMENT','DATE_OF_BIRTH','PHONE_NUMBER','PHONE_NUMBER_CALL','STATUS']
        for ut in unique_types:
            count = sum(1 for f in fields if f.get('displayType') == ut)
            if count > 1:
                add('CRITICAL', 'CTX-017', name, f'displayType "{ut}" が{count}回使用 (1回のみ許可)')
        if '\n' not in fields_str:
            add('WARNING', 'CTX-014-MIN', name, 'fields がminified (indent=2推奨)')

# 15. ContextMatchRouter params
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Context Logic$ContextMatchRouter':
        params = mod.get('params', {})
        m1n = params.get('module1Name', '')
        m2n = params.get('module2Name', '')
        if m1n != m2n:
            add('CRITICAL', 'CMR-001', name, f'module1Name="{m1n}" != module2Name="{m2n}"')
        param_keys = list(params.keys())
        expected_order = ['module1Name', 'module2Name']
        for i in range(1, 11):
            expected_order.extend([f'module1Value{i}', f'module2Value{i}'])
        actual_relevant = [k for k in param_keys if k.startswith('module')]
        if actual_relevant != expected_order[:len(actual_relevant)]:
            add('WARNING', 'CMR-ORDER', name, 'paramsキー順序不正 (交互配置必須)')
        for i in range(1, 11):
            v1 = params.get(f'module1Value{i}', '')
            v2 = params.get(f'module2Value{i}', '')
            if v1 != v2:
                add('CRITICAL', 'CMR-VAL', name, f'module1Value{i}="{v1}" != module2Value{i}="{v2}"')

# 16. Opening chain
if start_mod not in modules:
    add('CRITICAL', 'S-003', '', f'startモジュール "{start_mod}" がmodules内に存在しない')
else:
    start = modules[start_mod]
    if start.get('type') != 'Custom$wait':
        add('CRITICAL', 'FLOW-001', '', f'startモジュール "{start_mod}" がwaitでない (type={start.get("type")})')
    chain = [start_mod]
    current = start_mod
    for step in range(6):
        m = modules.get(current, {})
        nexts = m.get('next', [])
        used = [n for n in nexts if n.get('nextModuleName', '') != '']
        if len(used) == 1:
            current = used[0].get('nextModuleName', '')
            chain.append(current)
        elif len(used) > 1:
            true_next = next((n for n in used if n.get('label') == 'true'), None)
            if true_next:
                current = true_next.get('nextModuleName', '')
                chain.append(current)
            break
        else:
            break
    chain_types = [modules.get(c, {}).get('type', '') for c in chain]
    if 'drjoy^Persistence$saveContextModel2DB' not in chain_types:
        add('CRITICAL', 'FLOW-002', '', '冒頭チェーンにsaveContextModel2DBなし')
    if 'drjoy^Incoming$incoming-classifier' not in chain_types:
        add('WARNING', 'FLOW-CHAIN', '', '冒頭チェーンにincoming-classifierなし')
    if 'drjoy^Text To Speech$Text to speech' not in chain_types:
        add('CRITICAL', 'FLOW-007', '', '冒頭チェーンにTTSモジュールが存在しない(冒頭アナウンス欠落の可能性)')

# 17. CompletionFlag status
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Persistence$saveCompletionFlag2db':
        s = mod.get('params', {}).get('status', '')
        if s in ('0', '5'):
            add('CRITICAL', 'COMP-001', name, f'status="{s}" 使用禁止')

# 18. Transition target existence
for name, mod in modules.items():
    for n in mod.get('next', []):
        target = n.get('nextModuleName', '')
        if target and target not in modules:
            add('CRITICAL', 'T-001', name, f'遷移先 "{target}" がmodules内に存在しない')
    for s in mod.get('subs', []):
        target = s.get('moduleName', '')
        if target and target not in modules:
            add('CRITICAL', 'T-003', name, f'subs参照先 "{target}" がmodules内に存在しない')

# 19. Layout
coords = {}
for name, mod in modules.items():
    layout = mod.get('layout', {})
    coords[name] = (layout.get('x', 0), layout.get('y', 0))
coord_list = list(coords.items())
for i in range(len(coord_list)):
    for j in range(i+1, len(coord_list)):
        n1, (x1, y1) = coord_list[i]
        n2, (x2, y2) = coord_list[j]
        if x1 == x2 and y1 == y2:
            add('WARNING', 'LAYOUT-OVERLAP', n1, f'"{n2}" と座標完全重複 ({x1},{y1})')
zero_layouts = [n for n, (x,y) in coords.items() if x == 0 and y == 0 and n != start_mod]
if len(zero_layouts) > len(modules) * 0.5:
    add('CRITICAL', 'LAYOUT-001', '', f'大半のlayoutが(0,0): {len(zero_layouts)}個')
elif zero_layouts:
    first5 = zero_layouts[:5]
    add('WARNING', 'LAYOUT-002', '', f'一部layoutが(0,0): {len(zero_layouts)}個 ({", ".join(first5)}...)')

# 21. Retry->TTS日本語接続
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Text To Speech$Speech Retry Counter':
        pt = mod.get('params', {}).get('prompt_true', '')
        for n in mod.get('next', []):
            if n.get('condition') == 'true':
                target = n.get('nextModuleName', '')
                if target in modules:
                    tp = modules[target].get('params', {}).get('prompt', '')
                    if pt.endswith('再度、}') and tp:
                        m = re.search(r'\{tts_g:(.+?)\}', tp)
                        if m:
                            tts_text = m.group(1).strip()
                            if re.match(r'^[0-9０-９]|^以下|^次の|^1|^2|^3', tts_text):
                                add('WARNING', 'R-TTS-JP', name, f'「再度、」+ "{tts_text[:40]}" が不自然')

########################################
# Stage 2: PROFILE_WORDS
########################################
FILLER_10 = ['あ', 'あー', 'あの', 'あのー', 'え', 'えー', 'えっと', 'えーと', 'ん', 'んー']

for name, mod in modules.items():
    mtype = mod.get('type', '')
    if mtype in ('drjoy^AmiVoice$Speech to Text', 'drjoy^External Integration$DTMF AmiVoice STT Input'):
        pw = mod.get('params', {}).get('profile_words', '')
        if not pw or not pw.strip():
            add('WARNING', 'PW-EMPTY', name, 'profile_words が空')
        else:
            if re.search(r'[０-９]', pw):
                add('WARNING', 'PW-ZENKAKU', name, 'profile_words に全角数字あり')
            if 'まー' in pw:
                add('WARNING', 'PW-MAA', name, 'profile_words に「まー」あり (使用禁止)')
            if mtype == 'drjoy^AmiVoice$Speech to Text':
                missing = [f for f in FILLER_10 if f not in pw]
                if missing:
                    add('INFO', 'PW-FILLER', name, f'フィラー不足: {", ".join(missing[:5])}...')

########################################
# Stage 3: PROMPT_APPLY
########################################
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^External Integration$generate_by_OpenAI':
        prompt = mod.get('params', {}).get('prompt', '')
        if prompt:
            if '# Role' not in prompt and '#Role' not in prompt:
                add('CRITICAL', 'PROMPT-005', name, 'OpenAI prompt に # Role セクションなし')
            if '# Context' not in prompt and '#Context' not in prompt:
                add('CRITICAL', 'PROMPT-006', name, 'OpenAI prompt に # Context セクションなし')
            if '出力仕様' not in prompt:
                add('WARNING', 'PROMPT-OUT', name, 'OpenAI prompt に出力仕様セクションなし')
            if 'セキュリティ' not in prompt and 'インジェクション' not in prompt:
                add('WARNING', 'PROMPT-007', name, 'OpenAI prompt にインジェクション防御セクションなし')
            nexts = mod.get('next', [])
            used_conditions = [n.get('condition') for n in nexts
                             if n.get('condition') not in ('', '^TIMEOUT$', '^ERROR$', '^NO_RESULT$', '^.+$')]
            for cond in used_conditions:
                val = cond.replace('^', '').replace('$', '')
                if val and val not in prompt:
                    add('WARNING', 'PROMPT-001', name, f'next条件 "{val}" がprompt内に見つからない')

########################################
# Stage 4: PROPERTY_FIX
########################################
prop_keys = re.findall(r'^([^#\n][^.=\n]+)\.prompt=', prop_text, re.MULTILINE)
tts_modules = [name for name, mod in modules.items()
               if mod.get('type') == 'drjoy^Text To Speech$Text to speech']

for pk in prop_keys:
    pk_clean = pk.strip()
    if pk_clean not in tts_modules:
        add('INFO', 'PROP-SUBFLOW', pk_clean, f'Property.mdキー "{pk_clean}" がメインフローTTSに不在 (サブフロー用なら正常)')

for tm in tts_modules:
    if tm not in prop_keys:
        inline_prompt = modules[tm].get('params', {}).get('prompt', '')
        if not inline_prompt:
            add('CRITICAL', 'PROP-001', tm, f'TTSモジュール "{tm}" がProperty.mdに不在 & インラインpromptも空')

todo_matches = re.findall(r'TODO_[^\n]*', prop_text)
for t in todo_matches:
    add('WARNING', 'PROP-TODO', '', f'Property.mdにTODO残存: {t[:60]}')

mandatory_checks = {
    'amivoice.uri': 'amivoice.uri',
    'amivoice.language': 'amivoice.language',
    'amivoice.engine': 'amivoice.engine',
    'amivoice.detection_flag': 'amivoice.detection_flag',
    'office_id': 'office_id',
    'pbx.db.name': 'pbx.db.name',
    'context.settings.url': 'context.settings.url',
    'acceptance_times.url': 'acceptance_times.url',
    'openAI_generate.url': 'openAI_generate.url',
    'speech.rag.url': 'speech.rag.url',
}
for key, label in mandatory_checks.items():
    if key not in prop_text:
        add('CRITICAL', 'PROP-002', '', f'Property.md必須セクション欠落: {label}')

if 'detection_flag' in prop_text:
    df_match = re.search(r'detection_flag=(.+)', prop_text)
    if df_match:
        df_val = df_match.group(1).strip()
        if df_val == 'デフォルト':
            add('WARNING', 'PROP-DF', '', f'Property.md detection_flag="{df_val}" (Property.md側は"検出しない"が標準)')

########################################
# Additional checks
########################################
# Reachability
reachable = set()
def trace(mod_name):
    if mod_name in reachable or mod_name not in modules:
        return
    reachable.add(mod_name)
    m = modules[mod_name]
    for n in m.get('next', []):
        if n.get('nextModuleName', ''):
            trace(n['nextModuleName'])
    for s in m.get('subs', []):
        if s.get('moduleName', ''):
            trace(s['moduleName'])

sys.setrecursionlimit(5000)
trace(start_mod)
unreachable = set(modules.keys()) - reachable
for u in sorted(unreachable):
    add('WARNING', 'REACH-001', u, 'startから到達不能モジュール')

# Naming
for name in modules:
    if re.search(r'[①②③④⑤⑥⑦⑧⑨⑩]', name):
        add('CRITICAL', 'N-001', name, 'モジュール名に環境依存文字')
    if re.search(r'[（）\(\)\[\]]', name):
        add('WARNING', 'N-002', name, 'モジュール名に括弧')
    if ' ' in name:
        add('WARNING', 'N-003', name, 'モジュール名にスペース')

# save2db no next
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Persistence$save2db':
        used_nexts = [n for n in mod.get('next', []) if n.get('nextModuleName', '') != '']
        if used_nexts:
            add('CRITICAL', 'SB-002', name, 'save2db に next遷移が設定されている')

# Jump to Flow
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Custom Module$Custom Jump to Flow':
        if not mod.get('params', {}).get('flowname', ''):
            add('CRITICAL', 'FLOW-004', name, 'Custom Jump to Flow の flowname が空')

# saveContext2DB
for name, mod in modules.items():
    if mod.get('type') == 'drjoy^Persistence$saveContext2DB':
        params = mod.get('params', {})
        if not params.get('contextName', ''):
            add('CRITICAL', 'CTX-010', name, 'saveContext2DB contextName が空')
        if not params.get('contextValue', ''):
            add('CRITICAL', 'CTX-011', name, 'saveContext2DB contextValue が空')

########################################
# Output
########################################
sev_order = {'CRITICAL': 0, 'WARNING': 1, 'INFO': 2}
issues.sort(key=lambda x: (sev_order.get(x[0], 3), x[1], x[2]))

crit = sum(1 for i in issues if i[0] == 'CRITICAL')
warn = sum(1 for i in issues if i[0] == 'WARNING')
info = sum(1 for i in issues if i[0] == 'INFO')

# Generate markdown report
lines = []
lines.append('# 品質検証レポート: 関越病院_薬剤部')
lines.append('')
lines.append(f'- 対象ファイル: `output/関越病院_薬剤部_20260416.json`')
lines.append(f'- モジュール数: {len(modules)}')
lines.append(f'- 検証日: 2026-04-22')
lines.append('')
lines.append('## サマリー')
lines.append('')
lines.append(f'| 重要度 | 件数 |')
lines.append(f'|--------|------|')
lines.append(f'| CRITICAL | {crit} |')
lines.append(f'| WARNING | {warn} |')
lines.append(f'| INFO | {info} |')
lines.append(f'| **合計** | **{len(issues)}** |')
lines.append('')

# Group by severity
for sev_label in ['CRITICAL', 'WARNING', 'INFO']:
    sev_issues = [i for i in issues if i[0] == sev_label]
    if not sev_issues:
        continue
    lines.append(f'## {sev_label}')
    lines.append('')
    lines.append(f'| # | コード | モジュール | 内容 |')
    lines.append(f'|---|--------|------------|------|')
    for idx, (sev, code, mod, msg) in enumerate(sev_issues, 1):
        mod_disp = mod if mod else '(フロー全体)'
        msg_escaped = msg.replace('|', '\\|')
        lines.append(f'| {idx} | {code} | {mod_disp} | {msg_escaped} |')
    lines.append('')

report = '\n'.join(lines)

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    f.write(report)

print(report)
print(f'\n--- レポート保存先: {OUTPUT_PATH} ---')
