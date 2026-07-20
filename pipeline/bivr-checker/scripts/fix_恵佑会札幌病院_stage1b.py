#!/usr/bin/env python3
"""恵佑会札幌病院_診療1 Stage 1b: リトライfalse整合性 + fields修正"""
import json

MAIN = "output/恵佑会札幌病院_診療1/fixed/flows/恵佑会札幌病院_診療_20260422.json"

def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {path}")

data = load(MAIN)
mods = data['modules']
fixes = 0

# ==========================================
# リトライfalse整合性修正
# ==========================================
# 設計書ルール:
# - 必須聴取(用件,受診歴,紹介状,申し込み方法,SMS確認携帯) → 無限ループ(false=先頭TTS, prompt_false空)
# - 任意聴取(医師名,希望医師,予約日,キャンセル理由,内容確認) → 次へ進む(false=次ステップ)
# - SMS連絡先聴取_固定 → 次へ進む(false=次ステップに進む or 復唱に進む)
# - SMS連絡先聴取_固定_復唱 → 無限ループ(false=復唱TTS)

RETRY_FIXES = {
    # パターンC: 無限ループ（false=先頭TTS、prompt_false空）
    "リトライ_申し込み方法確認": {
        "false_target": "申し込み方法確認",
        "prompt_false": "",
        "reason": "必須聴取→無限ループ"
    },
    "リトライ_SMS_連絡先確認_携帯": {
        "false_target": "SMS_連絡先確認_携帯",
        "prompt_false": "",
        "reason": "必須聴取→無限ループ"
    },
    "リトライ_SMS_連絡先聴取_固定_復唱": {
        "false_target": "復唱_SMS_連絡先聴取_固定",
        "prompt_false": "",
        "reason": "復唱→無限ループ"
    },
    "リトライ_用件確認": {
        "false_target": "用件確認",
        "prompt_false": "",
        "reason": "必須聴取→無限ループ"
    },
    "リトライ_受診歴確認": {
        "false_target": "受診歴確認",
        "prompt_false": "",
        "reason": "必須聴取→無限ループ"
    },
    "リトライ_紹介状確認": {
        "false_target": "紹介状確認",
        "prompt_false": "",
        "reason": "必須聴取→無限ループ"
    },

    # パターンA: 次へ進む（false=次のステップTTS、prompt_false=告知メッセージ）
    "リトライ_医師名": {
        "false_target": "氏名聴取",  # Jump to Flow (次のサブフロー)
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_希望医師": {
        "false_target": "氏名聴取",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_予約希望日_再診": {
        "false_target": "氏名聴取",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_予約日_変更": {
        "false_target": "予約希望日_変更",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_予約希望日_変更": {
        "false_target": "氏名聴取",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_予約日_キャンセル": {
        "false_target": "キャンセル理由",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_キャンセル理由": {
        "false_target": "氏名聴取",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    "リトライ_内容確認_その他": {
        "false_target": "氏名聴取",
        "prompt_false": "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}",
        "reason": "任意聴取→次へ進む"
    },
    # SMS連絡先聴取_固定: 次へ進む（失敗したら再度携帯番号聞く）
    "リトライ_SMS_連絡先聴取_固定": {
        "false_target": "入力_SMS_連絡先聴取_固定_復唱",
        "prompt_false": "{tts_g:かしこまりました。もう一度携帯番号をお伺いします。}",
        "reason": "任意聴取→次へ進む(復唱)"
    },
}

print("=" * 60)
print("[FIX] リトライfalse整合性修正")
print("=" * 60)

for retry_name, fix in RETRY_FIXES.items():
    retry = mods.get(retry_name)
    if not retry:
        print(f"  [SKIP] {retry_name} not found")
        continue

    changed = False
    for n in retry['next']:
        if n.get('condition') == 'false':
            old_target = n.get('nextModuleName', '')
            new_target = fix['false_target']
            if old_target != new_target:
                n['nextModuleName'] = new_target
                print(f"  [FIX] {retry_name} false: {old_target} -> {new_target} ({fix['reason']})")
                changed = True
                fixes += 1

    # prompt_false修正
    old_pf = retry.get('params', {}).get('prompt_false', '')
    new_pf = fix['prompt_false']
    if old_pf != new_pf:
        retry['params']['prompt_false'] = new_pf
        if not changed:
            print(f"  [FIX] {retry_name} prompt_false updated ({fix['reason']})")
        fixes += 1

# ==========================================
# fields修正: clinicalDepartment追加
# ==========================================
print()
print("=" * 60)
print("[FIX] fields修正")
print("=" * 60)

ctx = mods.get('コンテキスト設定')
if ctx:
    fields = json.loads(ctx['params']['fields'])
    existing_names = {f['contextName'] for f in fields}

    if 'clinicalDepartment' not in existing_names:
        # 歯科口腔外科のみ受付対象
        cd_field = {
            "contextName": "clinicalDepartment",
            "contextNameJp": "診療科",
            "displayType": "DEPARTMENT",
            "rangeValues": [
                {"value": "歯科口腔外科", "order": 1}
            ],
            "editable": True,
            "deletable": False,
            "itemDefault": True
        }
        # Insert after classification (index 1) or at position 3
        insert_idx = 3
        for i, f in enumerate(fields):
            if f['contextName'] == 'medicalCardNumber':
                insert_idx = i + 1
                break
        fields.insert(insert_idx, cd_field)
        ctx['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)
        print(f"  [FIX] clinicalDepartment added at index {insert_idx} (歯科口腔外科)")
        fixes += 1

    # Also check: inquiry field for その他 route
    if 'inquiryContent' not in existing_names:
        fields = json.loads(ctx['params']['fields'])
        fields.append({
            "contextName": "inquiryContent",
            "contextNameJp": "問合せ内容",
            "displayType": "TEXT",
            "rangeValues": [],
            "editable": True,
            "deletable": True,
            "itemDefault": False
        })
        ctx['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)
        print(f"  [FIX] inquiryContent added (その他問い合わせ用)")
        fixes += 1

    # referralLetter field
    if 'referralLetter' not in existing_names:
        fields = json.loads(ctx['params']['fields'])
        fields.append({
            "contextName": "referralLetter",
            "contextNameJp": "紹介状",
            "displayType": "TEXT",
            "rangeValues": [],
            "editable": True,
            "deletable": True,
            "itemDefault": False
        })
        ctx['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)
        print(f"  [FIX] referralLetter added")
        fixes += 1

    # DoctorName / preferredDoctor fields
    for cn, jp in [('doctorName', '医師名'), ('preferredDoctor', '希望医師')]:
        if cn not in existing_names:
            fields = json.loads(ctx['params']['fields'])
            fields.append({
                "contextName": cn,
                "contextNameJp": jp,
                "displayType": "TEXT",
                "rangeValues": [],
                "editable": True,
                "deletable": True,
                "itemDefault": False
            })
            ctx['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)
            existing_names.add(cn)
            print(f"  [FIX] {cn} added")
            fixes += 1

    # history (受診歴)
    if 'history' not in existing_names:
        fields = json.loads(ctx['params']['fields'])
        fields.append({
            "contextName": "history",
            "contextNameJp": "受診歴",
            "displayType": "TEXT",
            "rangeValues": [],
            "editable": True,
            "deletable": True,
            "itemDefault": False
        })
        ctx['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)
        print(f"  [FIX] history added (受診歴)")
        fixes += 1

save(MAIN, data)

print(f"\n{'='*60}")
print(f"[TOTAL] 修正件数: {fixes}")
print(f"{'='*60}")
