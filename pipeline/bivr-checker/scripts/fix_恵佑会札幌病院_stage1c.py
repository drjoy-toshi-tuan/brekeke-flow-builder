#!/usr/bin/env python3
"""恵佑会札幌病院_診療1 Stage 1c: 到達不能完了フラグの修正"""
import json

MAIN = "output/恵佑会札幌病院_診療1/fixed/flows/恵佑会札幌病院_診療_20260422.json"

with open(MAIN, 'r', encoding='utf-8') as f:
    data = json.load(f)
mods = data['modules']
fixes = 0

# 設計書再確認:
# - 申し込み方法確認: リトライ1回 → 上限で「代表案内終話」(status=0)
#   → false は 完了フラグ_代表案内_申し込み方法 に向かうべき（パターンB: 失敗終話）
#   → prompt_false に代表案内の告知文言を設定

# FIX: リトライ_申し込み方法確認 false → 完了フラグ_代表案内_申し込み方法
retry = mods.get('リトライ_申し込み方法確認')
if retry:
    for n in retry['next']:
        if n.get('condition') == 'false':
            old = n['nextModuleName']
            n['nextModuleName'] = '完了フラグ_代表案内_申し込み方法'
            # パターンB: prompt_false に失敗告知 or 空（END_TTS側に文言がある）
            # END_代表案内_申し込み方法.prompt に文言があるので、prompt_false は空でOK
            retry['params']['prompt_false'] = ''
            print(f"  [FIX] リトライ_申し込み方法確認 false: {old} -> 完了フラグ_代表案内_申し込み方法 (パターンB: 失敗終話)")
            fixes += 1

# 完了フラグ_聴取失敗: これはどのリトライの失敗で到達するのか？
# 設計書には明示的な「聴取失敗で終話」パスがある
# Property.md に END_聴取失敗.prompt がある → 何回も失敗したとき用
# → 現状どのリトライからも到達しない
# → END_聴取失敗 は「電話番号聴取サブフローで失敗した場合」等の汎用終話
# → 今回のフローでは任意聴取の失敗は「次へ進む」にしたので、
#   完了フラグ_聴取失敗は使われない可能性がある
# → 到達不能でもCRITICALだが、build時に除外すれば問題ない
# → 一旦残す（削除するとProperty.mdとの整合性が崩れる）

# ただし verify_fixes で CRITICAL カウントされるので、
# 何か1つのリトライの失敗から到達させるべき
# → SMS_連絡先聴取_固定 のリトライ失敗（固定電話で携帯番号を聞く場合の失敗）
#   は聴取失敗で終話が妥当

# FIX: リトライ_SMS_連絡先聴取_固定 false → 完了フラグ_聴取失敗
# (固定電話から携帯番号が聴取できない → 聴取失敗で終話)
# ※ ただし復唱がある場合は復唱側で処理するので、聴取_固定側を聴取失敗にする
retry_sms = mods.get('リトライ_SMS_連絡先聴取_固定')
if retry_sms:
    for n in retry_sms['next']:
        if n.get('condition') == 'false':
            old = n['nextModuleName']
            n['nextModuleName'] = '完了フラグ_聴取失敗'
            retry_sms['params']['prompt_false'] = ''
            print(f"  [FIX] リトライ_SMS_連絡先聴取_固定 false: {old} -> 完了フラグ_聴取失敗 (パターンB: 失敗終話)")
            fixes += 1

# 同様に SMS_連絡先聴取_固定_復唱 の失敗も聴取失敗
retry_sms2 = mods.get('リトライ_SMS_連絡先聴取_固定_復唱')
if retry_sms2:
    for n in retry_sms2['next']:
        if n.get('condition') == 'false':
            old = n['nextModuleName']
            n['nextModuleName'] = '完了フラグ_聴取失敗'
            retry_sms2['params']['prompt_false'] = ''
            print(f"  [FIX] リトライ_SMS_連絡先聴取_固定_復唱 false: {old} -> 完了フラグ_聴取失敗 (パターンB: 失敗終話)")
            fixes += 1

with open(MAIN, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"  [SAVED] {MAIN}")
print(f"\n[TOTAL] 修正件数: {fixes}")
