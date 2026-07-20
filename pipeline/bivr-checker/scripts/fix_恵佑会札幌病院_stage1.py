#!/usr/bin/env python3
"""恵佑会札幌病院_診療1 Stage 1 追加構造修正"""
import json, copy

BASE = "output/恵佑会札幌病院_診療1/fixed/flows/"
MAIN = BASE + "恵佑会札幌病院_診療_20260422.json"
SUB_SHIMEI = BASE + "恵佑会札幌病院_氏名聴取_20260422.json"
SUB_DOB = BASE + "恵佑会札幌病院_生年月日聴取_20260422.json"
SUB_CARD = BASE + "恵佑会札幌病院_診察券番号聴取_20260422.json"
SUB_TEL = BASE + "恵佑会札幌病院_電話番号聴取_20260422.json"

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {path}")

SCRIPT_TEMPLATE = {
    "layout": {"x": 0, "y": 0},
    "next": [{"condition":"","label":"","nextModuleName":""}]*12,
    "subs": [],
    "name": "",
    "description": "",
    "matchingmethod": 1,
    "type": "@General$Script",
    "params": {
        "script": "var result = $runner.getModuleResult($session);\nif (result) {\n  $runner.setReturnValue(result);\n}"
    }
}

fixes = 0

# ==================== MAIN FLOW ====================
print("=" * 60)
print("[FIX] メインフロー")
print("=" * 60)
data = load(MAIN)
mods = data['modules']

# FIX 1: リトライ_申し込み方法確認 false → 完了フラグ_代表案内_申し込み方法
retry_app = mods.get('リトライ_申し込み方法確認')
if retry_app:
    for n in retry_app['next']:
        if n.get('condition') == 'false' and n.get('nextModuleName') != '完了フラグ_代表案内_申し込み方法':
            old = n['nextModuleName']
            n['nextModuleName'] = '完了フラグ_代表案内_申し込み方法'
            print(f"  [FIX] リトライ_申し込み方法確認 false: {old} -> 完了フラグ_代表案内_申し込み方法")
            fixes += 1

# FIX 2: 復唱_SMS_連絡先聴取_固定 next修正
reconf = mods.get('復唱_SMS_連絡先聴取_固定')
if reconf:
    reconf['next'] = [
        {"condition": "^.*$", "label": "Next Module", "nextModuleName": "入力_SMS_連絡先聴取_固定_復唱"}
    ]
    print("  [FIX] 復唱_SMS_連絡先聴取_固定 next -> ^.*$ Next Module -> 入力_SMS_連絡先聴取_固定_復唱")
    fixes += 1

# FIX 3: save-Medical Referral Letter → save-紹介状確認
old_name = "save-Medical Referral Letter"
new_name = "save-紹介状確認"
if old_name in mods:
    mod = mods.pop(old_name)
    mod['name'] = new_name
    mod['params']['contextName'] = 'referralLetter'
    mods[new_name] = mod
    for mname, m in mods.items():
        for s in m.get('subs', []):
            if s.get('moduleName') == old_name:
                s['moduleName'] = new_name
                s['label'] = new_name
                print(f"  [FIX] {mname} subs: {old_name} -> {new_name}")
    fixes += 1
    print(f"  [FIX] Rename: {old_name} -> {new_name}")

# FIX 4: status rangeValues に 6(時間外) と 8(SMS送信) を追加
ctx = mods.get('コンテキスト設定')
if ctx and 'fields' in ctx.get('params', {}):
    fields_str = ctx['params']['fields']
    fields = json.loads(fields_str) if isinstance(fields_str, str) else fields_str
    for f in fields:
        if f.get('contextName') == 'status':
            rv = f.get('rangeValues', [])
            existing_ids = {str(r.get('id', '')) for r in rv}
            for new_id, new_val in [('6', '時間外'), ('8', 'SMS送信')]:
                if new_id not in existing_ids:
                    rv.append({"id": new_id, "order": len(rv), "value": new_val})
                    print(f"  [FIX] status rangeValues: added id={new_id} ({new_val})")
                    fixes += 1
            f['rangeValues'] = rv
    ctx['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)

save(MAIN, data)

# ==================== SUBFLOW HELPER ====================
def make_script_mod(name, x, y):
    m = copy.deepcopy(SCRIPT_TEMPLATE)
    m['name'] = name
    m['layout'] = {"x": x, "y": y}
    # Proper 12 empty slots
    m['next'] = [{"condition":"","label":"","nextModuleName":""} for _ in range(12)]
    return m

# ==================== 氏名聴取 ====================
print("\n" + "="*60)
print("[FIX] サブフロー: 氏名聴取")
print("="*60)
d = load(SUB_SHIMEI)
ms = d['modules']
sn = "script_結果返却_patientName"
stt = ms.get('入力_患者_氏名')
if stt and sn not in ms:
    ms[sn] = make_script_mod(sn, stt['layout']['x'], stt['layout']['y'] + 240)
    for n in stt.get('next', []):
        if n.get('condition') == '^.+$' and not n.get('nextModuleName'):
            n['nextModuleName'] = sn
            print(f"  [FIX] 入力_患者_氏名 success -> {sn}")
            fixes += 1
    retry = ms.get('リトライ_患者_氏名')
    if retry:
        for n in retry.get('next', []):
            if n.get('condition') == 'false':
                old = n.get('nextModuleName', '')
                n['nextModuleName'] = sn
                print(f"  [FIX] リトライ_患者_氏名 false -> {sn} (was: {old})")
                fixes += 1
    print(f"  [FIX] Added {sn}")
save(SUB_SHIMEI, d)

# ==================== 生年月日聴取 ====================
print("\n" + "="*60)
print("[FIX] サブフロー: 生年月日聴取")
print("="*60)
d = load(SUB_DOB)
ms = d['modules']
sn = "script_結果返却_patientDateOfBirth"
oai = ms.get('openAI_復唱_患者生年月日')
if oai and sn not in ms:
    ms[sn] = make_script_mod(sn, oai['layout']['x'], oai['layout']['y'] + 240)
    for n in oai.get('next', []):
        cond = n.get('condition', '')
        nm = n.get('nextModuleName', '')
        if cond in ('^.*$', '^.+$') and not nm:
            n['nextModuleName'] = sn
            print(f"  [FIX] openAI_復唱_患者生年月日 wildcard -> {sn}")
            fixes += 1
        elif 'はい' in cond and not nm:
            n['nextModuleName'] = sn
            print(f"  [FIX] openAI_復唱_患者生年月日 はい -> {sn}")
            fixes += 1
    for rname in ['リトライ_患者_生年月日', 'リトライ_復唱_患者生年月日']:
        retry = ms.get(rname)
        if retry:
            for n in retry.get('next', []):
                if n.get('condition') == 'false':
                    old = n.get('nextModuleName', '')
                    if not old:
                        n['nextModuleName'] = sn
                        print(f"  [FIX] {rname} false -> {sn}")
                        fixes += 1
    # Fix layout overlap
    tts = ms.get('患者_生年月日')
    inp = ms.get('入力_患者_生年月日')
    if tts and inp:
        ty = tts['layout']['y']
        sy = inp['layout']['y']
        if abs(sy - ty) < 150:
            inp['layout']['y'] = ty + 220
            print(f"  [FIX] LAYOUT: 入力_患者_生年月日 y: {sy} -> {ty + 220}")
            fixes += 1
    print(f"  [FIX] Added {sn}")
save(SUB_DOB, d)

# ==================== 診察券番号聴取 ====================
print("\n" + "="*60)
print("[FIX] サブフロー: 診察券番号聴取")
print("="*60)
d = load(SUB_CARD)
ms = d['modules']
sn = "script_結果返却_medicalCardNumber"
oai = ms.get('openAI_患者_診察券番号')
if oai and sn not in ms:
    ms[sn] = make_script_mod(sn, oai['layout']['x'], oai['layout']['y'] + 240)
    for n in oai.get('next', []):
        if n.get('condition') in ('^.*$', '^.+$') and not n.get('nextModuleName'):
            n['nextModuleName'] = sn
            print(f"  [FIX] openAI_患者_診察券番号 success -> {sn}")
            fixes += 1
    retry = ms.get('リトライ_患者_診察券番号')
    if retry:
        for n in retry.get('next', []):
            if n.get('condition') == 'false':
                old = n.get('nextModuleName', '')
                if not old:
                    n['nextModuleName'] = sn
                    print(f"  [FIX] リトライ_患者_診察券番号 false -> {sn}")
                    fixes += 1
    print(f"  [FIX] Added {sn}")
save(SUB_CARD, d)

# ==================== 電話番号聴取 ====================
print("\n" + "="*60)
print("[FIX] サブフロー: 電話番号聴取")
print("="*60)
d = load(SUB_TEL)
ms = d['modules']
sn = "script_結果返却_phoneNumber"
if sn not in ms:
    max_y = max(m['layout']['y'] for m in ms.values() if 'layout' in m)
    ms[sn] = make_script_mod(sn, 0, max_y + 240)
    for exit_name in ['携帯ルート', 'その他ルート']:
        m = ms.get(exit_name)
        if m:
            connected = False
            for n in m.get('next', []):
                if n.get('condition') and not n.get('nextModuleName'):
                    n['nextModuleName'] = sn
                    print(f"  [FIX] {exit_name} -> {sn}")
                    fixes += 1
                    connected = True
                    break
            if not connected and m.get('next'):
                m['next'][0]['nextModuleName'] = sn
                if not m['next'][0].get('condition'):
                    m['next'][0]['condition'] = '^.*$'
                    m['next'][0]['label'] = 'next'
                print(f"  [FIX] {exit_name} [0] -> {sn}")
                fixes += 1
    for rname in ['リトライ_患者_連絡先', 'リトライ_患者_携帯電話', 'リトライ_復唱_患者生年月日']:
        retry = ms.get(rname)
        if retry:
            for n in retry.get('next', []):
                if n.get('condition') == 'false' and not n.get('nextModuleName'):
                    n['nextModuleName'] = sn
                    print(f"  [FIX] {rname} false -> {sn}")
                    fixes += 1
    print(f"  [FIX] Added {sn}")
save(SUB_TEL, d)

print(f"\n{'='*60}")
print(f"[TOTAL] 追加修正件数: {fixes}")
print(f"{'='*60}")
