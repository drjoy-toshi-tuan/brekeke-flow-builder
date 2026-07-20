#!/usr/bin/env python3
"""
fix_yokohama_rousai_v5.py — 横浜労災病院 FB 4点修正

1. DOB Re-confirmation: 復唱_患者_生年月日 を TS Custom Module$DOB Re-confirmation に変更
2. Re-confirmation module param: 復唱_患者_連絡先 に module 追加
3. Script グループ判定 → OpenAI グループ直接出力に変更
4. Script 携帯判別/smsFlag/SMS判定 → 正しいルーティングに変更
5. AmiVoice STT timeout_ms を空欄化
6. DTMF timeout_ms → timeout: "30000" に変更
7. .bivr 再構築
"""

import json, os, sys, glob, zipfile
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FIXED_DIR = "output/横浜労災病院/fixed/flows"
MAIN_FLOW = os.path.join(FIXED_DIR, "横浜労災$診療_20260403.json")
BIVR_OUT = "output/横浜労災病院/横浜労災病院_fixed.bivr"

print("=== 横浜労災病院 v5 修正パッチ ===\n")

with open(MAIN_FLOW, encoding='utf-8') as f:
    flow = json.load(f)
mods = flow['modules']

# =========================================================
# Fix 1: DOB Re-confirmation
# 復唱_患者_生年月日 を DOB Re-confirmation タイプに変更
# =========================================================
DOB_RECONF_OPENAI_PROMPT = """# Role
あなたは「生年月日」を抽出・正規化する専門 AI です。
音声認識テキスト（STT）から生年月日を特定し、指定されたフォーマットで回答してください。
※数値のみの入力（DTMF）は考慮不要です。

# 最重要指示
以下の Processing Logic に記載されたルールをすべての入力に対して適用すること。
Few-Shot Examples はルールの動作確認用サンプルであり、
Examples に含まれない入力に対しても必ずルールを適用して回答すること。
Examples に存在しない入力を INVALID にしてはならない。

# Output Format（厳守）
出力は以下の3パターンのいずれか1行のみとし、説明や記号は一切含めないこと。
1. 西暦形式: yyyy-MM-dd 00:00
2. 和暦形式: gggg年M月d日
3. エラー: INVALID

# Processing Logic

## Step 1: 元号・類似語の検出
入力テキストに以下のキーワードが含まれる場合、対応する元号として扱い和暦形式で出力する。
- 令和: 令和、れいわ、レイワ、例は、冷和
- 平成: 平成、へいせい、ヘイセイ、平静、閉成、平清
- 昭和: 昭和、しょうわ、ショウワ、唱和、社長は、少和、名所、正和、うわ、うわー
- 大正: 大正、たいしょう、タイショウ、対象、大将
- 明治: 明治、めいじ、メイジ、命じ、明示
※「元年」は「1年」として扱う。
※元号が検出された場合は Step 2 をスキップして Step 3 へ進む。

## Step 2: 元号なしの場合 — 年の桁数による補完
入力から年・月・日を抽出し、年の桁数に応じて以下の手順で西暦に補完する。

### 2桁の場合
- 先頭に「19」を付加する
- 計算式: 西暦年 = 1900 + 入力値
- 例: 93 → 1900 + 93 = 1993、60 → 1900 + 60 = 1960

### 3桁の場合
- 下2桁を取得し、先頭に「19」を付加する
- 計算式: 西暦年 = 1900 + (入力値 mod 100)
- 例:
  - 193 → 193 mod 100 = 93 → 1900 + 93 = 1993
  - 185 → 185 mod 100 = 85 → 1900 + 85 = 1985

### 4桁の場合
- そのまま西暦として扱う
- 例: 1985 → 1985

## Step 3: 妥当性チェック
補完後の日付が以下をすべて満たすこと。満たさない場合は INVALID を返す。
- 実在する日付であること（例: 2月30日、13月 → INVALID）
- 現在より過去の日付であること（未来日付 → INVALID）
- 現在から120年以内であること（古すぎる → INVALID）
- 生年月日に無関係な発話であること → INVALID

# Few-Shot Examples（ルール適用の確認用）

入力: 昭和60年12月1日です
出力: 昭和60年12月1日

入力: 社長は45年の4月1日
出力: 昭和45年4月1日

入力: 平成元年5月3日
出力: 平成1年5月3日

入力: 93年3月12日
出力: 1993-03-12 00:00

入力: 185年4月1日
出力: 1985-04-01 00:00

入力: 90 4 1
出力: 1990-04-01 00:00

入力: 1985 1 1
出力: 1985-01-01 00:00

入力: 明日の天気は？
出力: INVALID"""

mod_dob = mods.get('復唱_患者_生年月日')
if mod_dob:
    print("[Fix 1] 復唱_患者_生年月日 → DOB Re-confirmation タイプに変更")
    mod_dob['type'] = 'drjoy^TS Custom Module$DOB Re-confirmation'
    mod_dob['params'] = {
        'module': '入力_患者_生年月日',
        'openAI_prompt': DOB_RECONF_OPENAI_PROMPT,
        'prompt': '{tts_g: <speak> #data# <break time = "300ms"/> でよろしいでしょうか。 </speak> 「はい、そうです。」または、「いいえ、違います。」でお答えください。}',
        'saveDOB2db': 'Yes',
        'dateReadingMode': '自動',
    }
    # Update next: add INVALID condition → リトライ
    mod_dob['next'] = [
        {'condition': '^TIMEOUT$', 'label': 'timeout', 'nextModuleName': 'リトライ_患者_生年月日'},
        {'condition': '^ERROR$',   'label': 'error',   'nextModuleName': 'リトライ_患者_生年月日'},
        {'condition': '^INVALID$', 'label': 'invalid', 'nextModuleName': 'リトライ_患者_生年月日'},
        {'condition': '^.*$',      'label': 'success', 'nextModuleName': '入力_復唱_患者_生年月日'},
    ]
    print("  [OK] type=DOB Re-confirmation, params設定, next更新完了")
else:
    print("[SKIP] 復唱_患者_生年月日 not found")

# =========================================================
# Fix 2: Re-confirmation node data — module param追加
# 復唱_患者_連絡先 に module: "OpenAI_患者_連絡先" を追加
# =========================================================
print()
mod_renraku = mods.get('復唱_患者_連絡先')
if mod_renraku and mod_renraku.get('type') == 'drjoy^Text To Speech$Re-confirmation node data':
    print("[Fix 2] 復唱_患者_連絡先: module param追加")
    mod_renraku['params']['module'] = 'OpenAI_患者_連絡先'
    print("  [OK] module=OpenAI_患者_連絡先 追加")
else:
    print("[SKIP] 復唱_患者_連絡先 not found or wrong type")

# =========================================================
# Fix 3: OpenAI_診療科_予約/紹介なし → グループ直接出力
# =========================================================
GROUP_MAPPING_SECTION = """
# グループマッピング（出力値の決定）
以下のマッピングに従ってグループを決定し、グループ名を1語で出力する。

## グループ1: 血液内科 / 腫瘍内科 / 放射線治療科

## グループ2: 放射線診断科 / 放射線IVR科 / 緩和支持治療科 / 救急科 / 救急災害医療部 / 麻酔科

## グループ3: 小児科 / 形成外科 / 産科分娩部 / 婦人部 / 女性ヘルスケア部 / 産婦人科 / 外科 / 呼吸器外科

## グループ4（上記以外の全診療科）:
糖尿病内科 / 膠原病内科 / 精神科 / 眼科 / 泌尿器科 / 消化器外科 / 脊椎脊髄外科
心臓血管外科 / 内分泌内科 / 腎臓内科 / 脳神経外科 / 消化器内科 / 新生児内科
耳鼻咽喉科 / 頭頚部外科 / 歯科口腔外科口腔内科 / 乳腺外科 / 手末梢神経外科
脳神経内科 / 皮膚科 / 代謝内科 / リウマチ科 / 心療内科 / 呼吸器内科 / 循環器内科
小児外科 / 整形外科 / 人工関節外科 / 脳神経血管内治療科

## リハビリ: リハビリ・リハビリテーション関連"""

def update_shinryoka_prompt_and_next(mod_name, next_grp3_dest, next_grp4_dest):
    mod = mods.get(mod_name)
    if not mod:
        print(f"[SKIP] {mod_name} not found")
        return

    # Update 出力仕様 section in prompt
    prompt = mod['params']['prompt']
    old_spec = """# 出力仕様（厳守）
以下のいずれか1語のみを出力すること：
- 診療科名
- リハビリ
- NO_RESULT

診療科名: 下記対象科目の正式名称（1語）を出力する
リハビリ: ユーザーがリハビリ・リハビリテーションと発話した場合
NO_RESULT: 診療科が特定できない場合
解説・理由・グループ番号・文章は一切出力しない。"""

    new_spec = """# 出力仕様（厳守）
以下のいずれか1語のみを出力すること：
- グループ1
- グループ2
- グループ3
- グループ4
- リハビリ
- NO_RESULT

グループ1〜4: 下記グループマッピングに従い、該当するグループ名（1語）を出力する
リハビリ: ユーザーがリハビリ・リハビリテーションと発話した場合
NO_RESULT: 診療科が特定できない場合
解説・理由・診療科名・文章は一切出力しない。"""

    prompt = prompt.replace(old_spec, new_spec)

    # Add グループマッピング section after 略称・類義語マッピング section
    if GROUP_MAPPING_SECTION not in prompt:
        # Insert before ## NO_RESULT となる場合
        no_result_idx = prompt.find('## NO_RESULT となる場合')
        if no_result_idx >= 0:
            prompt = prompt[:no_result_idx] + GROUP_MAPPING_SECTION + '\n\n' + prompt[no_result_idx:]
        else:
            prompt = prompt + '\n' + GROUP_MAPPING_SECTION

    mod['params']['prompt'] = prompt

    # Update next routing
    mod['next'] = [
        {'condition': '^TIMEOUT$', 'label': 'timeout',   'nextModuleName': f'リトライ_診療科_{mod_name.split("_")[2]}'},
        {'condition': '^ERROR$',   'label': 'error',     'nextModuleName': f'リトライ_診療科_{mod_name.split("_")[2]}'},
        {'condition': '^NO_RESULT$','label':'no_result', 'nextModuleName': f'リトライ_診療科_{mod_name.split("_")[2]}'},
        {'condition': '^グループ1$', 'label': 'グループ1', 'nextModuleName': '完了フラグ_終話1'},
        {'condition': '^グループ2$', 'label': 'グループ2', 'nextModuleName': '完了フラグ_終話2'},
        {'condition': '^グループ3$', 'label': 'グループ3', 'nextModuleName': next_grp3_dest},
        {'condition': '^グループ4$', 'label': 'グループ4', 'nextModuleName': next_grp4_dest},
        {'condition': '^リハビリ$',  'label': 'リハビリ',  'nextModuleName': '転送_リハビリ'},
    ]
    print(f"  [OK] {mod_name}: prompt更新 + next グループ直接ルーティング設定")


print()
print("[Fix 3] OpenAI_診療科 グループ直接出力設定")

# OpenAI_診療科_予約: グループ3→紹介元, グループ4→紹介元
retry_suffix = lambda s: s.replace('OpenAI', 'リトライ')
update_shinryoka_prompt_and_next('OpenAI_診療科_予約', '紹介元', '紹介元')

# OpenAI_診療科_紹介なし: グループ3→完了フラグ_終話3, グループ4→選定療養費_説明
update_shinryoka_prompt_and_next('OpenAI_診療科_紹介なし', '完了フラグ_終話3', '選定療養費_説明')

# Fix リトライ_診療科_予約 false → 紹介元 (was → script_グループ判定_予約)
mod_r = mods.get('リトライ_診療科_予約')
if mod_r:
    for n in mod_r['next']:
        if n['condition'] == 'false':
            n['nextModuleName'] = '紹介元'
    print("  [OK] リトライ_診療科_予約 false → 紹介元")

# Fix リトライ_診療科_紹介なし false → 選定療養費_説明
mod_r2 = mods.get('リトライ_診療科_紹介なし')
if mod_r2:
    for n in mod_r2['next']:
        if n['condition'] == 'false':
            n['nextModuleName'] = '選定療養費_説明'
    print("  [OK] リトライ_診療科_紹介なし false → 選定療養費_説明")

# Delete 復唱_診療科 related modules (no longer needed)
delete_reconf = [
    '復唱_診療科_予約', '入力_復唱_診療科_予約', 'OpenAI_復唱_診療科_予約',
    'リトライ_復唱_診療科_予約', 'save-復唱_診療科_予約',
    '復唱_診療科_紹介なし', '入力_復唱_診療科_紹介なし', 'OpenAI_復唱_診療科_紹介なし',
    'リトライ_復唱_診療科_紹介なし', 'save-復唱_診療科_紹介なし',
    'script_グループ判定_予約', 'script_グループ判定_紹介なし',
]
deleted = []
for name in delete_reconf:
    if name in mods:
        del mods[name]
        deleted.append(name)
print(f"  [OK] 削除: {deleted}")

# =========================================================
# Fix 4a: script_携帯判別 / script_smsFlag設定 削除
# OpenAI_患者_連絡先 (^.+$) → 復唱_患者_連絡先
# OpenAI_復唱_患者_連絡先 (^肯定$) → 用件
# リトライ_患者_連絡先 false → 用件
# リトライ_復唱_患者_連絡先 false → 用件
# =========================================================
print()
print("[Fix 4a] 電話番号/script_携帯判別・smsFlag設定 削除")

# OpenAI_患者_連絡先: ^.+$ → 復唱_患者_連絡先 (was → script_携帯判別)
mod_oai = mods.get('OpenAI_患者_連絡先')
if mod_oai:
    for n in mod_oai['next']:
        if n['condition'] == '^.+$':
            n['nextModuleName'] = '復唱_患者_連絡先'
    print("  [OK] OpenAI_患者_連絡先 ^.+$ → 復唱_患者_連絡先")

# OpenAI_復唱_患者_連絡先: ^肯定$ → 用件 (was → script_smsFlag設定)
mod_reconf_oai = mods.get('OpenAI_復唱_患者_連絡先')
if mod_reconf_oai:
    for n in mod_reconf_oai['next']:
        if n.get('nextModuleName') == 'script_smsFlag設定':
            n['nextModuleName'] = '用件'
    print("  [OK] OpenAI_復唱_患者_連絡先 肯定 → 用件")

# リトライ_患者_連絡先 false → 用件
mod_r3 = mods.get('リトライ_患者_連絡先')
if mod_r3:
    for n in mod_r3['next']:
        if n['condition'] == 'false':
            n['nextModuleName'] = '用件'
    print("  [OK] リトライ_患者_連絡先 false → 用件")

# リトライ_復唱_患者_連絡先 false → 用件
mod_r4 = mods.get('リトライ_復唱_患者_連絡先')
if mod_r4:
    for n in mod_r4['next']:
        if n['condition'] == 'false':
            n['nextModuleName'] = '用件'
    print("  [OK] リトライ_復唱_患者_連絡先 false → 用件")

# Delete script_携帯判別, script_smsFlag設定
for name in ['script_携帯判別', 'script_smsFlag設定']:
    if name in mods:
        del mods[name]
        print(f"  [OK] {name} 削除")

# =========================================================
# Fix 4b: script_SMS判定 → 着信分類_SMS判定（incoming-classifier）
# =========================================================
print()
print("[Fix 4b] script_SMS判定 → 着信分類_SMS判定 に変更")

# Create 着信分類_SMS判定 module
mods['着信分類_SMS判定'] = {
    'layout': {'x': 0, 'y': 0},
    'next': [
        {'condition': '^携帯$', 'label': '携帯', 'nextModuleName': '完了フラグ_受付完了_SMS'},
        {'condition': '^固定$', 'label': '固定', 'nextModuleName': '完了フラグ_受付完了_noSMS'},
        {'condition': '^海外$', 'label': '海外', 'nextModuleName': '完了フラグ_受付完了_noSMS'},
        {'condition': '^.*$',   'label': 'other','nextModuleName': '完了フラグ_受付完了_noSMS'},
    ],
    'subs': [{'moduleName': '', 'label': ''}, {'moduleName': '', 'label': ''}, {'moduleName': '', 'label': ''}],
    'name': '着信分類_SMS判定',
    'description': '着信電話番号の種別でSMS/noSMS分岐',
    'matchingmethod': 1,
    'type': 'drjoy^Incoming$incoming-classifier',
    'params': {},
}
print("  [OK] 着信分類_SMS判定 モジュール作成（incoming-classifier）")

# Replace all references to script_SMS判定 with 着信分類_SMS判定
replaced_count = 0
for name, mod in mods.items():
    for n in mod.get('next', []):
        if n.get('nextModuleName') == 'script_SMS判定':
            n['nextModuleName'] = '着信分類_SMS判定'
            replaced_count += 1
print(f"  [OK] script_SMS判定 参照 {replaced_count}件 → 着信分類_SMS判定")

# Delete script_SMS判定
if 'script_SMS判定' in mods:
    del mods['script_SMS判定']
    print("  [OK] script_SMS判定 削除")

# =========================================================
# Fix 5: AmiVoice STT timeout_ms → "" (グローバル管理)
# =========================================================
print()
print("[Fix 5] AmiVoice STT timeout_ms → 空欄化")
stt_cleared = 0
for name, mod in mods.items():
    if mod.get('type') == 'drjoy^AmiVoice$Speech to Text':
        if mod.get('params', {}).get('timeout_ms'):
            mod['params']['timeout_ms'] = ''
            stt_cleared += 1
print(f"  [OK] AmiVoice STT timeout_ms 空欄化: {stt_cleared}件")

# =========================================================
# Fix 6: DTMF timeout_ms → timeout: "30000"
# =========================================================
print()
print("[Fix 6] DTMF timeout_ms → timeout: '30000'")
dtmf_fixed = 0
for name, mod in mods.items():
    if mod.get('type') == 'drjoy^External Integration$DTMF AmiVoice STT Input':
        params = mod.get('params', {})
        if 'timeout_ms' in params:
            del params['timeout_ms']
        params['timeout'] = '30000'
        dtmf_fixed += 1
        print(f"  [OK] {name}: timeout_ms 削除, timeout=30000 追加")
print(f"  合計 {dtmf_fixed}件")

# =========================================================
# Save
# =========================================================
with open(MAIN_FLOW, 'w', encoding='utf-8') as f:
    json.dump(flow, f, ensure_ascii=False, indent=2)
print(f"\n[OK] saved: {MAIN_FLOW}")

# Verify script modules remaining
scripts_remaining = [k for k, v in mods.items() if v.get('type') == '@General$Script']
print(f"Script modules remaining: {scripts_remaining}")

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
