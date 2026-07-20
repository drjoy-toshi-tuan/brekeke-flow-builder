#!/usr/bin/env python3
"""沖縄県立南部医療センター profile_words 一括適用スクリプト"""
import json

# Read flow JSON
with open('output/沖縄県立南部医療センター・こども医療センター_診療_20260423.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Read reference dictionaries
def read_dict(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith('#')]
            return '\n'.join(lines)
    except:
        return ''

yes_no = read_dict('reference/dictionaries/profile_words_yes_no.txt')
dob = read_dict('reference/dictionaries/profile_words_dob.txt')

def expand_keyword(word, yomi, include_fillers=True, include_suffixes=True, include_head_drop=True):
    lines = [f'{word} {yomi}']
    fillers = ['あ', 'え', 'えー', 'あの', 'はい', 'ま']
    suffixes = ['です', 'で', 'なんですが', 'になります', 'ね', 'さ', 'でして', 'か']
    if include_fillers:
        for fl in fillers:
            lines.append(f'{word} {fl}{yomi}')
    if include_suffixes:
        for s in suffixes:
            lines.append(f'{word} {yomi}{s}')
    if include_head_drop and len(yomi) >= 3:
        dropped1 = yomi[1:]
        if len(dropped1) >= 2:
            lines.append(f'{word} {dropped1}')
        if len(yomi) >= 4:
            dropped2 = yomi[2:]
            if len(dropped2) >= 2:
                lines.append(f'{word} {dropped2}')
    return lines

def gen_yoken():
    keywords = [
        ('予約', 'よやく'), ('予約したい', 'よやくしたい'), ('受診したい', 'じゅしんしたい'),
        ('診てほしい', 'みてほしい'), ('取りたい', 'とりたい'), ('新規予約', 'しんきよやく'),
        ('初診', 'しょしん'), ('お願いしたい', 'おねがいしたい'),
        ('変更', 'へんこう'), ('予約変更', 'よやくへんこう'), ('日程変更', 'にっていへんこう'),
        ('日にちを変えたい', 'ひにちをかえたい'), ('ずらしたい', 'ずらしたい'),
        ('キャンセル', 'きゃんせる'), ('取消', 'とりけし'), ('やめたい', 'やめたい'),
        ('行けなくなった', 'いけなくなった'), ('取り消し', 'とりけし'),
        ('確認', 'かくにん'), ('聞きたい', 'ききたい'), ('予約の確認', 'よやくのかくにん'),
        ('教えてほしい', 'おしえてほしい'), ('わからない', 'わからない'),
    ]
    lines = []
    for w, y in keywords:
        lines.extend(expand_keyword(w, y))
    return '\n'.join(dict.fromkeys(lines))

def gen_yes_no():
    return yes_no

def gen_date():
    base_lines = dob.split('\n')
    extra = [
        '来週 らいしゅう', '再来週 さらいしゅう', '来月 らいげつ',
        '明日 あした', '明日 あす', '明後日 あさって',
        '今週 こんしゅう', '今月 こんげつ', '今日 きょう',
        '月曜日 げつようび', '火曜日 かようび', '水曜日 すいようび',
        '木曜日 もくようび', '金曜日 きんようび', '土曜日 どようび', '日曜日 にちようび',
        '月曜 げつよう', '火曜 かよう', '水曜 すいよう',
        '木曜 もくよう', '金曜 きんよう', '土曜 どよう', '日曜 にちよう',
        '令和 えいわ', '平成 えいせい', '昭和 きょうわ', '昭和 きょうは',
        '分からない わからない', '分かりません わかりません', '未定 みてい',
        '特にない とくにない', '特にありません とくにありません',
    ]
    all_lines = base_lines + extra
    return '\n'.join(dict.fromkeys(l for l in all_lines if l.strip()))

def gen_dept_adult():
    depts = [
        ('内科', 'ないか'), ('消化器内科', 'しょうかきないか'), ('循環器内科', 'じゅんかんきないか'),
        ('呼吸器内科', 'こきゅうきないか'), ('脳神経内科', 'のうしんけいないか'),
        ('感染症内科', 'かんせんしょうないか'), ('腎臓内科', 'じんぞうないか'),
        ('血液腫瘍内科', 'けつえきしゅようないか'), ('リウマチ膠原病科', 'りうまちこうげんびょうか'),
        ('外科', 'げか'), ('心臓血管外科', 'しんぞうけっかんげか'),
        ('整形外科', 'せいけいげか'), ('形成外科', 'けいせいげか'),
        ('脳神経外科', 'のうしんけいげか'), ('産婦人科', 'さんふじんか'),
        ('眼科', 'がんか'), ('耳鼻咽喉科', 'じびいんこうか'),
        ('皮膚科', 'ひふか'), ('泌尿器科', 'ひにょうきか'),
        ('放射線科', 'ほうしゃせんか'), ('麻酔科', 'ますいか'),
        ('リハビリテーション科', 'りはびりてーしょんか'), ('歯科口腔外科', 'しかこうくうげか'),
        ('精神科', 'せいしんか'), ('救急集中治療科', 'きゅうきゅうしゅうちゅうちりょうか'),
        ('総合診療科', 'そうごうしんりょうか'), ('病理診断科', 'びょうりしんだんか'),
        ('ぱいかじ大動脈センター', 'ぱいかじだいどうみゃくせんたー'),
        ('脳卒中センター', 'のうそっちゅうせんたー'),
        ('血管内治療センター', 'けっかんないちりょうせんたー'),
        ('成人先天性心疾患外来', 'せいじんせんてんせいしんしっかんがいらい'),
    ]
    abbrevs = [
        ('整形', 'せいけい'), ('リハビリ', 'りはびり'), ('脳外科', 'のうげか'),
        ('耳鼻科', 'じびか'), ('消化器', 'しょうかき'), ('循環器', 'じゅんかんき'),
        ('呼吸器', 'こきゅうき'), ('泌尿器', 'ひにょうき'),
        ('歯科', 'しか'), ('口腔外科', 'こうくうげか'),
        ('わからない', 'わからない'), ('分かりません', 'わかりません'),
    ]
    lines = []
    for w, y in depts + abbrevs:
        lines.extend(expand_keyword(w, y, include_suffixes=False))
    return '\n'.join(dict.fromkeys(lines))

def gen_dept_child():
    depts = [
        ('小児内科', 'しょうにないか'), ('小児外科', 'しょうにげか'),
        ('小児心臓血管外科', 'しょうにしんぞうけっかんげか'),
        ('新生児内科', 'しんせいじないか'), ('小児整形外科', 'しょうにせいけいげか'),
        ('小児脳神経外科', 'しょうにのうしんけいげか'),
        ('小児泌尿器科', 'しょうにひにょうきか'),
        ('小児眼科', 'しょうにがんか'), ('小児耳鼻咽喉科', 'しょうにじびいんこうか'),
        ('小児皮膚科', 'しょうにひふか'), ('小児形成外科', 'しょうにけいせいげか'),
        ('小児放射線科', 'しょうにほうしゃせんか'),
        ('小児リハビリテーション科', 'しょうにりはびりてーしょんか'),
        ('児童精神科', 'じどうせいしんか'),
    ]
    abbrevs = [
        ('小児科', 'しょうにか'), ('こども科', 'こどもか'),
        ('わからない', 'わからない'), ('分かりません', 'わかりません'),
    ]
    lines = []
    for w, y in depts + abbrevs:
        lines.extend(expand_keyword(w, y, include_suffixes=False))
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_reason():
    keywords = [
        ('体調不良', 'たいちょうふりょう'), ('仕事', 'しごと'), ('都合が悪い', 'つごうがわるい'),
        ('急用', 'きゅうよう'), ('引っ越し', 'ひっこし'), ('転院', 'てんいん'),
        ('他の病院', 'ほかのびょういん'), ('良くなった', 'よくなった'),
        ('治った', 'なおった'), ('入院', 'にゅういん'), ('通院できない', 'つういんできない'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
        for fl in ['あ', 'え', 'えー']:
            lines.append(f'{w} {fl}{y}')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_inquiry():
    keywords = [
        ('予約日', 'よやくび'), ('次の予約', 'つぎのよやく'), ('いつ', 'いつ'),
        ('何時', 'なんじ'), ('場所', 'ばしょ'), ('持ち物', 'もちもの'),
        ('検査', 'けんさ'), ('結果', 'けっか'), ('薬', 'くすり'),
        ('紹介状', 'しょうかいじょう'), ('費用', 'ひよう'), ('駐車場', 'ちゅうしゃじょう'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
        for fl in ['あ', 'え', 'えー']:
            lines.append(f'{w} {fl}{y}')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_last_inquiry():
    keywords = [
        ('はい', 'はい'), ('ある', 'ある'), ('あります', 'あります'),
        ('ありません', 'ありません'), ('ないです', 'ないです'), ('ない', 'ない'),
        ('いいえ', 'いいえ'), ('大丈夫です', 'だいじょうぶです'), ('特にない', 'とくにない'),
        ('特にありません', 'とくにありません'), ('以上です', 'いじょうです'),
        ('それだけです', 'それだけです'), ('もう大丈夫', 'もうだいじょうぶ'),
        ('結構です', 'けっこうです'), ('もういい', 'もういい'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
        for fl in ['あ', 'え', 'えー']:
            lines.append(f'{w} {fl}{y}')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_medication():
    keywords = [
        ('はい', 'はい'), ('飲んでいます', 'のんでいます'), ('服用しています', 'ふくようしています'),
        ('飲んでます', 'のんでます'), ('しています', 'しています'),
        ('いいえ', 'いいえ'), ('飲んでいません', 'のんでいません'), ('していません', 'していません'),
        ('飲んでません', 'のんでません'), ('ない', 'ない'), ('ないです', 'ないです'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
        for fl in ['あ', 'え', 'えー']:
            lines.append(f'{w} {fl}{y}')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_drug_remain():
    keywords = [
        ('一週間', 'いっしゅうかん'), ('二週間', 'にしゅうかん'), ('三週間', 'さんしゅうかん'),
        ('一ヶ月', 'いっかげつ'), ('二ヶ月', 'にかげつ'), ('三ヶ月', 'さんかげつ'),
        ('半年', 'はんとし'), ('ない', 'ない'), ('ないです', 'ないです'),
        ('ありません', 'ありません'), ('わからない', 'わからない'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
    for i, yomi in enumerate(['いちにち','ふつか','みっか','よっか','いつか','むいか','なのか'], 1):
        lines.append(f'{i}日分 {yomi}ぶん')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_referral():
    keywords = [
        ('はい', 'はい'), ('あります', 'あります'), ('持ってます', 'もってます'),
        ('持っています', 'もっています'), ('ある', 'ある'),
        ('いいえ', 'いいえ'), ('ない', 'ない'), ('ないです', 'ないです'),
        ('ありません', 'ありません'), ('持ってません', 'もってません'),
        ('持っていません', 'もっていません'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
        for fl in ['あ', 'え', 'えー']:
            lines.append(f'{w} {fl}{y}')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_hospital():
    keywords = [
        ('クリニック', 'くりにっく'), ('病院', 'びょういん'), ('医院', 'いいん'),
        ('診療所', 'しんりょうじょ'), ('内科', 'ないか'), ('外科', 'げか'),
        ('わからない', 'わからない'), ('覚えていない', 'おぼえていない'),
    ]
    lines = []
    for w, y in keywords:
        lines.append(f'{w} {y}')
        for fl in ['あ', 'え', 'えー']:
            lines.append(f'{w} {fl}{y}')
    return '\n'.join(dict.fromkeys(lines))

def gen_freetext_bad_days():
    extra = [
        '特にない とくにない', '特にありません とくにありません',
        'ない ない', 'ないです ないです', 'ありません ありません',
        '大丈夫です だいじょうぶです', 'いつでも いつでも',
        '来週 らいしゅう', '来月 らいげつ',
        '月曜日 げつようび', '火曜日 かようび', '水曜日 すいようび',
        '木曜日 もくようび', '金曜日 きんようび', '土曜日 どようび', '日曜日 にちようび',
    ]
    base = dob.split('\n')[:12]
    return '\n'.join(dict.fromkeys(l for l in base + extra if l.strip()))

# Apply
mods = data['modules']
mapping = {
    '入力_用件聴取': gen_yoken,
    '入力_用件聴取_復唱': gen_yes_no,
    '入力_年齢確認': gen_yes_no,
    '入力_予約日_変更': gen_date,
    '入力_予約日_変更_復唱': gen_yes_no,
    '入力_予約日_キャンセル': gen_date,
    '入力_予約日_キャンセル_復唱': gen_yes_no,
    '入力_診療科_変更_成人': gen_dept_adult,
    '入力_診療科_変更_小児': gen_dept_child,
    '入力_診療科_キャンセル_成人': gen_dept_adult,
    '入力_診療科_キャンセル_小児': gen_dept_child,
    '入力_診療科_確認_成人': gen_dept_adult,
    '入力_診療科_確認_小児': gen_dept_child,
    '入力_紹介状有無_新規': gen_freetext_referral,
    '入力_医療機関名_新規': gen_freetext_hospital,
    '入力_都合が悪い日_新規': gen_freetext_bad_days,
    '入力_都合が悪い日_変更': gen_freetext_bad_days,
    '入力_理由_変更': gen_freetext_reason,
    '入力_理由_キャンセル': gen_freetext_reason,
    '入力_薬服用中か_変更': gen_freetext_medication,
    '入力_薬服用中か_キャンセル': gen_freetext_medication,
    '入力_薬残数確認_変更': gen_freetext_drug_remain,
    '入力_薬残数確認_キャンセル': gen_freetext_drug_remain,
    '入力_確認事項_確認': gen_freetext_inquiry,
    '入力_最後の問い合わせ': gen_freetext_last_inquiry,
}

updates = {}
for mod_name, gen_func in mapping.items():
    if mod_name in mods:
        pw = gen_func()
        line_count = len([l for l in pw.split('\n') if l.strip()])
        mods[mod_name]['params']['profile_words'] = pw
        updates[mod_name] = line_count

with open('output/沖縄県立南部医療センター・こども医療センター_診療_20260423.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('=== profile_words update complete ===')
for name, count in sorted(updates.items()):
    print(f'  {name}: {count} words')
print(f'\nTotal: {len(updates)} modules updated')
