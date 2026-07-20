#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix script for 帯広第一病院 main flow"""

import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('output/帯広第一病院/帯広第一病院_診療_20260415.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

mods = data['modules']

# === FIX 1: 着信分類 condition "^*$" -> "^.*$" ===
if '着信分類' in mods:
    for slot in mods['着信分類']['next']:
        if slot.get('condition') == '^*$':
            slot['condition'] = '^.*$'
            print('FIX: 着信分類 condition ^*$ -> ^.*$')

# === FIX 2: 完了フラグ_聴取失敗 status "3" -> "2" ===
if '完了フラグ_聴取失敗' in mods:
    old_status = mods['完了フラグ_聴取失敗']['params'].get('status')
    if old_status == '3':
        mods['完了フラグ_聴取失敗']['params']['status'] = '2'
        print(f'FIX: 完了フラグ_聴取失敗 status {old_status} -> 2')

# === FIX 3: ContextMatchRouter params key order (交互配置) ===
def fix_cmr_params(params):
    ordered = {}
    ordered['module1Name'] = params.get('module1Name', '')
    ordered['module2Name'] = params.get('module2Name', '')
    for i in range(1, 11):
        ordered[f'module1Value{i}'] = params.get(f'module1Value{i}', '')
        ordered[f'module2Value{i}'] = params.get(f'module2Value{i}', '')
    return ordered

cmr_modules = ['終話分岐_用件', '終話分岐_受付完了', '終話分岐_キャンセル',
                'ルート分岐', 'ルート分岐_現在予約日後', 'ルート分岐_予約希望日後']
for mod_name in cmr_modules:
    if mod_name in mods:
        old_keys = list(mods[mod_name]['params'].keys())
        mods[mod_name]['params'] = fix_cmr_params(mods[mod_name]['params'])
        new_keys = list(mods[mod_name]['params'].keys())
        if old_keys != new_keys:
            print(f'FIX: {mod_name} params key order fixed')

# === FIX 4: keep_filter_token "No" -> "Yes" for STT modules ===
for mod_name, mod in mods.items():
    if mod.get('type') == 'drjoy^AmiVoice$Speech to Text':
        if mod['params'].get('keep_filter_token') == 'No':
            mod['params']['keep_filter_token'] = 'Yes'
            print(f'FIX: {mod_name} keep_filter_token No -> Yes')

# === FIX 5: Profile words enrichment ===

# 入力_通院歴確認
tsuuin_words = (
    "はい はい\nはい はあ\nはい はーい\nはい あい\nはい い\nはーい はーい\nはあ はあ\n"
    "いいえ いいえ\nいいえ いーえ\nいいえ いえ\nいいえ いい\n"
    "あります あります\nあります ります\nありません ありません\nありません りません\n"
    "ある ある\nない ない\n初めて はじめて\n初めてです はじめてです\n"
    "受診したことがあります じゅしんしたことがあります\n通っています かよっています\n"
    "通院しています つういんしています\nかかっています かかっています\n"
    "再診 さいしん\n初診 しょしん\nええ ええ\nええ えー\nうん うん\n"
    "そうです そうです\nはいあります はいあります\nいいえありません いいえありません\n"
    "はい あはい\nはい えはい\nはい えーはい\nはい あのはい\n"
    "いいえ あいいえ\nいいえ えいいえ\nいいえ えーいいえ\n"
    "あります あーあります\nあります えあります\nあります えーあります\n"
    "ありません あーありません\nありません えありません\nありません えーありません"
)
if '入力_通院歴確認' in mods:
    mods['入力_通院歴確認']['params']['profile_words'] = tsuuin_words
    print('FIX: 入力_通院歴確認 profile_words enriched')

# 入力_診療科聴取
shinryouka_words = (
    "内科 ないか\n外科 げか\n整形外科 せいけいげか\n整形 せいけい\n"
    "小児科 しょうにか\n小児 しょうに\n眼科 がんか\n"
    "耳鼻咽喉科 じびいんこうか\n耳鼻科 じびか\n耳鼻 じび\n"
    "皮膚科 ひふか\n皮膚 ひふ\n"
    "脳神経外科 のうしんけいげか\n脳外科 のうげか\n脳神経 のうしんけい\n"
    "歯科口腔外科 しかこうくうげか\n口腔外科 こうくうげか\n歯科 しか\n"
    "透析内科 とうせきないか\n透析 とうせき\n"
    "発熱外来 はつねつがいらい\n発熱 はつねつ\n"
    "ストーマ外来 すとーまがいらい\nストーマ すとーま\n"
    "わからない わからない\nわかりません わかりません\n分からない わからない\n不明 ふめい\n"
    "内科 あないか\n内科 えないか\n内科 えーないか\n内科 あのないか\n"
    "外科 あげか\n外科 えげか\n外科 えーげか\n"
    "整形外科 あせいけいげか\n整形外科 えせいけいげか\n整形外科 えーせいけいげか\n"
    "眼科 あがんか\n眼科 えがんか\n皮膚科 あひふか\n皮膚科 えひふか\n"
    "小児科 あしょうにか\n小児科 えしょうにか\n"
    "耳鼻咽喉科 あじびいんこうか\n耳鼻科 あじびか\n"
    "内科 いか\n外科 か\n整形外科 いけいげか\n眼科 んか\n皮膚科 ふか\n小児科 ょうにか"
)
if '入力_診療科聴取' in mods:
    mods['入力_診療科聴取']['params']['profile_words'] = shinryouka_words
    print('FIX: 入力_診療科聴取 profile_words enriched')

# 入力_追加診療科確認
tsuika_words = (
    "ありません ありません\nないです ないです\nない ない\nなし なし\n"
    "特にない とくにない\n大丈夫 だいじょうぶ\n"
    "内科 ないか\n外科 げか\n整形外科 せいけいげか\n整形 せいけい\n"
    "小児科 しょうにか\n眼科 がんか\n耳鼻咽喉科 じびいんこうか\n耳鼻科 じびか\n"
    "皮膚科 ひふか\n脳神経外科 のうしんけいげか\n脳外科 のうげか\n"
    "歯科口腔外科 しかこうくうげか\n口腔外科 こうくうげか\n"
    "透析内科 とうせきないか\n透析 とうせき\n"
    "発熱外来 はつねつがいらい\nストーマ外来 すとーまがいらい\nわからない わからない\n"
    "ありません あーありません\nありません えありません\nありません えーありません\nありません あのありません\n"
    "ないです あないです\nないです えないです\n"
    "内科 あないか\n内科 えないか\n外科 あげか\n外科 えげか\n"
    "整形外科 あせいけいげか\n眼科 あがんか\n皮膚科 あひふか\n"
    "小児科 あしょうにか\n耳鼻科 あじびか"
)
if '入力_追加診療科確認' in mods:
    mods['入力_追加診療科確認']['params']['profile_words'] = tsuika_words
    print('FIX: 入力_追加診療科確認 profile_words enriched')

# 入力_用件確認
youken_words = (
    "予約 よやく\n変更 へんこう\nキャンセル きゃんせる\n確認 かくにん\n取り消し とりけし\n"
    "1番 いちばん\n2番 にばん\n3番 さんばん\n4番 よんばん\n"
    "一番 いちばん\n二番 にばん\n三番 さんばん\n四番 よんばん\n"
    "1 いち\n2 に\n3 さん\n4 よん\n"
    "予約したい よやくしたい\n受診したい じゅしんしたい\n診てほしい みてほしい\nお願いしたい おねがいしたい\n"
    "予約変更 よやくへんこう\n日程変更 にっていへんこう\n日にちを変えたい ひにちをかえたい\n"
    "取消 とりけし\nやめたい やめたい\n行けなくなった いけなくなった\n"
    "聞きたい ききたい\n問い合わせ といあわせ\n"
    "予約 あよやく\n予約 えよやく\n予約 えーよやく\n予約 あのよやく\n予約 はいよやく\n"
    "変更 あへんこう\n変更 えへんこう\n変更 えーへんこう\n変更 あのへんこう\n変更 はいへんこう\n"
    "キャンセル あきゃんせる\nキャンセル えきゃんせる\nキャンセル えーきゃんせる\n"
    "キャンセル あのきゃんせる\nキャンセル はいきゃんせる\n"
    "確認 あかくにん\n確認 えかくにん\n確認 えーかくにん\n確認 あのかくにん\n確認 はいかくにん\n"
    "予約 やく\n変更 んこう\nキャンセル ゃんせる\n確認 くにん\n1番 ちばん\n"
    "予約です よやくです\n変更です へんこうです\nキャンセルです きゃんせるです\n確認です かくにんです\n"
    "予約で よやくで\n変更で へんこうで\nキャンセルで きゃんせるで\n確認で かくにんで"
)
if '入力_用件確認' in mods:
    mods['入力_用件確認']['params']['profile_words'] = youken_words
    print('FIX: 入力_用件確認 profile_words enriched')

# 入力_現在の予約日 / 入力_予約希望日
date_words = (
    "ありません ありません\nわからない わからない\n分からない わからない\n"
    "一月 いちがつ\n二月 にがつ\n三月 さんがつ\n四月 しがつ\n五月 ごがつ\n"
    "六月 ろくがつ\n七月 しちがつ\n八月 はちがつ\n九月 くがつ\n"
    "十月 じゅうがつ\n十一月 じゅういちがつ\n十二月 じゅうにがつ\n"
    "令和 れいわ\n平成 へいせい\n昭和 しょうわ\n"
    "一日 ついたち\n二日 ふつか\n三日 みっか\n四日 よっか\n五日 いつか\n"
    "六日 むいか\n七日 なのか\n八日 ようか\n九日 ここのか\n十日 とおか\n"
    "十一日 じゅういちにち\n十二日 じゅうににち\n十三日 じゅうさんにち\n"
    "十四日 じゅうよっか\n十五日 じゅうごにち\n十六日 じゅうろくにち\n"
    "十七日 じゅうしちにち\n十八日 じゅうはちにち\n十九日 じゅうくにち\n"
    "二十日 はつか\n二十一日 にじゅういちにち\n二十二日 にじゅうににち\n"
    "二十三日 にじゅうさんにち\n二十四日 にじゅうよっか\n二十五日 にじゅうごにち\n"
    "二十六日 にじゅうろくにち\n二十七日 にじゅうしちにち\n二十八日 にじゅうはちにち\n"
    "二十九日 にじゅうくにち\n三十日 さんじゅうにち\n三十一日 さんじゅういちにち\n"
    "月曜日 げつようび\n火曜日 かようび\n水曜日 すいようび\n木曜日 もくようび\n"
    "金曜日 きんようび\n土曜日 どようび\n日曜日 にちようび\n"
    "明日 あした\n明後日 あさって\n来週 らいしゅう\n来月 らいげつ\n"
    "一 いち\n二 に\n三 さん\n四 よん\n四 し\n五 ご\n六 ろく\n七 なな\n七 しち\n"
    "八 はち\n九 きゅう\n九 く\n零 ぜろ\n十 じゅう\n二十 にじゅう\n三十 さんじゅう\n"
    "年 ねん\n月 がつ\n日 にち\n"
    "ありません あーありません\nありません えありません\nありません えーありません\n"
    "わからない あーわからない\nわからない えわからない"
)
for stt_name in ['入力_現在の予約日', '入力_予約希望日']:
    if stt_name in mods:
        mods[stt_name]['params']['profile_words'] = date_words
        print(f'FIX: {stt_name} profile_words enriched')

# 入力_症状聴取
shoujou_words = (
    "頭痛 ずつう\n頭が痛い あたまがいたい\n腹痛 ふくつう\nお腹が痛い おなかがいたい\n"
    "発熱 はつねつ\n熱がある ねつがある\n咳 せき\n咳が出る せきがでる\n"
    "風邪 かぜ\nめまい めまい\n吐き気 はきけ\n下痢 げり\n便秘 べんぴ\n"
    "腰痛 ようつう\n腰が痛い こしがいたい\n肩こり かたこり\n息切れ いきぎれ\n"
    "動悸 どうき\nむくみ むくみ\nかゆみ かゆみ\n痛い いたい\n痛み いたみ\n"
    "しびれ しびれ\nだるい だるい\n疲れやすい つかれやすい\n眠れない ねむれない\n"
    "食欲がない しょくよくがない\n体調不良 たいちょうふりょう\n検査 けんさ\n"
    "定期検診 ていきけんしん\n経過観察 けいかかんさつ\n薬 くすり\n処方 しょほう"
)
if '入力_症状聴取' in mods:
    mods['入力_症状聴取']['params']['profile_words'] = shoujou_words
    print('FIX: 入力_症状聴取 profile_words enriched')

# 入力_理由聴取
riyuu_words = (
    "体調不良 たいちょうふりょう\n仕事 しごと\n仕事が入った しごとがはいった\n"
    "都合が悪い つごうがわるい\n急用 きゅうよう\n用事 ようじ\n旅行 りょこう\n予定 よてい\n"
    "引っ越し ひっこし\n転勤 てんきん\n入院 にゅういん\n通院 つういん\n"
    "体調 たいちょう\n風邪 かぜ\n発熱 はつねつ\n日程 にってい\n時間 じかん\n"
    "変更したい へんこうしたい\n忘れていた わすれていた\n間違えた まちがえた"
)
if '入力_理由聴取' in mods:
    mods['入力_理由聴取']['params']['profile_words'] = riyuu_words
    print('FIX: 入力_理由聴取 profile_words enriched')

# 入力_内容確認
naiyo_words = (
    "予約 よやく\n予約日 よやくび\n診療科 しんりょうか\n先生 せんせい\n担当医 たんとうい\n"
    "時間 じかん\n場所 ばしょ\n持ち物 もちもの\n準備 じゅんび\n"
    "薬 くすり\n処方 しょほう\n検査 けんさ\n結果 けっか\n"
    "費用 ひよう\n料金 りょうきん\n保険 ほけん\n紹介状 しょうかいじょう\n"
    "受付 うけつけ\n駐車場 ちゅうしゃじょう\nアクセス あくせす"
)
if '入力_内容確認' in mods:
    mods['入力_内容確認']['params']['profile_words'] = naiyo_words
    print('FIX: 入力_内容確認 profile_words enriched')

# 入力_最終確認
saishuu_words = (
    "ありません ありません\nないです ないです\nない ない\n大丈夫です だいじょうぶです\n"
    "特にありません とくにありません\n以上です いじょうです\n"
    "お願いします おねがいします\nよろしくお願いします よろしくおねがいします\n"
    "はい はい\nはい はあ\nいいえ いいえ\n"
    "薬 くすり\n処方 しょほう\n検査 けんさ\n予約 よやく\n先生 せんせい\n時間 じかん\n"
    "質問 しつもん\n確認 かくにん\n"
    "ありません あーありません\nありません えありません\n"
    "ないです あないです\nないです えないです\n"
    "大丈夫です あだいじょうぶです\n大丈夫です えだいじょうぶです"
)
if '入力_最終確認' in mods:
    mods['入力_最終確認']['params']['profile_words'] = saishuu_words
    print('FIX: 入力_最終確認 profile_words enriched')

# === FIX 6: saveContextModel2DB fields ===
if 'コンテキスト設定' in mods:
    fields_str = mods['コンテキスト設定']['params']['fields']
    fields = json.loads(fields_str)
    existing_names = {f['contextName'] for f in fields}

    for f in fields:
        if f['contextName'] == 'clinicalDepartment':
            if f.get('itemDefault') == False:
                f['itemDefault'] = True
                f['deletable'] = False
                print('FIX: clinicalDepartment itemDefault -> true')
        if f['contextName'] == 'callId':
            if f.get('editable') == False:
                f['editable'] = True
                print('FIX: callId editable -> true')
        if f['contextName'] == 'status':
            range_vals = f.get('rangeValues', [])
            ids = {r.get('id') for r in range_vals}
            if '0' not in ids:
                range_vals.insert(0, {"id": "0", "value": "途中切断", "order": 0})
                print('FIX: status rangeValues added 途中切断(0)')
        if f['contextName'] == 'reason':
            if f.get('itemDefault') == False:
                f['itemDefault'] = True
                f['deletable'] = False
                print('FIX: reason itemDefault -> true')

    if 'reservationDate' not in existing_names:
        idx = next((i for i, f in enumerate(fields) if f['contextName'] == 'reason'), len(fields))
        fields.insert(idx + 1, {
            "contextName": "reservationDate",
            "contextNameJp": "予約日",
            "displayType": "DATE",
            "rangeValues": [],
            "editable": True,
            "deletable": False,
            "itemDefault": True
        })
        print('FIX: Added missing reservationDate standard field')

    mods['コンテキスト設定']['params']['fields'] = json.dumps(fields, ensure_ascii=False, indent=2)
    print('FIX: コンテキスト設定 fields reformatted with indent=2')

# === FIX 7: Brekeke key order for all modules ===
for mod_name in list(mods.keys()):
    mod = mods[mod_name]
    ordered = {}
    for key in ['layout', 'next', 'subs', 'name', 'description', 'matchingmethod', 'type', 'params']:
        if key in mod:
            ordered[key] = mod[key]
    for key in mod:
        if key not in ordered:
            ordered[key] = mod[key]
    mods[mod_name] = ordered

# === FIX 8: Retry prompt_true standardization ===
if 'リトライ_追加診療科' in mods:
    pt = mods['リトライ_追加診療科']['params'].get('prompt_true', '')
    if '再度お伺いいたします' in pt:
        mods['リトライ_追加診療科']['params']['prompt_true'] = '{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}'
        print('FIX: リトライ_追加診療科 prompt_true standardized')

# === FIX 9: ContextMatchRouter next slots -> 10 ===
for mod_name in cmr_modules:
    if mod_name in mods and mods[mod_name]['type'] == 'drjoy^Context Logic$ContextMatchRouter':
        nxt = mods[mod_name]['next']
        if len(nxt) > 10:
            # Keep the default/Other in last used slot, trim to 10
            mods[mod_name]['next'] = nxt[:10]
            print(f'FIX: {mod_name} trimmed to 10 next slots')
        while len(mods[mod_name]['next']) < 10:
            mods[mod_name]['next'].append({"condition": "", "label": "", "nextModuleName": ""})

# === Write fixed file ===
with open('output/帯広第一病院/帯広第一病院_診療_20260415.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('\nMain flow fixes complete!')
