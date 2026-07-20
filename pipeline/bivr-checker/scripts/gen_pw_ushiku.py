#!/usr/bin/env python3
"""Generate profile_words for all 25 STT modules in 牛久愛和総合病院_診療.json"""

import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

FLOW_PATH = 'output/牛久愛和総合病院/fixed/flows/牛久愛和総合病院_診療.json'
YES_NO_PATH = 'reference/dictionaries/profile_words_yes_no.txt'

with open(FLOW_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === HELPER FUNCTIONS ===

FILLERS = ['あ', 'え', 'えー', 'あの', 'はい', 'ま']
GOBIS = ['です', 'で', 'なんですが', 'になります', 'ね', 'さ', 'でして', 'か']


def filler_expand(keyword, yomi):
    return [f"{keyword} {fl}{yomi}" for fl in FILLERS]


def gobi_expand(keyword, yomi):
    return [f"{keyword} {yomi}{g}" for g in GOBIS]


def atama_kire(keyword, yomi):
    lines = []
    if len(yomi) >= 2:
        cut1 = yomi[1:]
        if len(cut1) >= 2:
            lines.append(f"{keyword} {cut1}")
        if len(yomi) >= 3:
            cut2 = yomi[2:]
            if len(cut2) >= 2:
                lines.append(f"{keyword} {cut2}")
    return lines


def full_expand(keyword, yomi):
    lines = [f"{keyword} {yomi}"]
    lines.extend(filler_expand(keyword, yomi))
    lines.extend(gobi_expand(keyword, yomi))
    lines.extend(atama_kire(keyword, yomi))
    return lines


def dedup(lines, limit=200):
    seen = set()
    result = []
    for l in lines:
        if l not in seen:
            seen.add(l)
            result.append(l)
    return result[:limit]


def read_yes_no():
    lines = []
    with open(YES_NO_PATH, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                lines.append(line)
    return lines


def _num_to_yomi(n):
    ones = {1: 'いち', 2: 'に', 3: 'さん', 4: 'よん', 5: 'ご',
            6: 'ろく', 7: 'しち', 8: 'はち', 9: 'く'}
    tens = {10: 'じゅう', 20: 'にじゅう', 30: 'さんじゅう'}
    if n in tens:
        return tens[n]
    t = (n // 10) * 10
    o = n % 10
    return tens.get(t, '') + ones.get(o, '')


# ===== GENERATORS =====

def gen_yoken():
    lines = []
    groups = [
        # 予約系
        [('予約', 'よやく'), ('新規予約', 'しんきよやく'), ('予約したい', 'よやくしたい'),
         ('受診したい', 'じゅしんしたい'), ('診てほしい', 'みてほしい'),
         ('お願いしたい', 'おねがいしたい'), ('取りたい', 'とりたい'),
         ('新規', 'しんき'), ('初めて', 'はじめて'), ('初診', 'しょしん')],
        # 再診系
        [('再診', 'さいしん'), ('再診予約', 'さいしんよやく'), ('定期', 'ていき'),
         ('通院', 'つういん'), ('いつもの', 'いつもの')],
        # 変更系
        [('変更', 'へんこう'), ('予約変更', 'よやくへんこう'),
         ('日程変更', 'にっていへんこう'), ('日にちを変えたい', 'ひにちをかえたい'),
         ('ずらしたい', 'ずらしたい')],
        # キャンセル系
        [('キャンセル', 'きゃんせる'), ('取消', 'とりけし'),
         ('やめたい', 'やめたい'), ('行けなくなった', 'いけなくなった')],
        # 確認系
        [('確認', 'かくにん'), ('聞きたい', 'ききたい'),
         ('わからない', 'わからない'), ('問い合わせ', 'といあわせ')],
        # がん検診系
        [('がん検診', 'がんけんしん'), ('子宮がん検診', 'しきゅうがんけんしん'),
         ('乳がん検診', 'にゅうがんけんしん'), ('検診', 'けんしん')],
        # 予防接種系
        [('予防接種', 'よぼうせっしゅ'), ('インフルエンザ', 'いんふるえんざ'),
         ('コロナ', 'ころな'), ('ワクチン', 'わくちん')],
        # 複数人系
        [('二人', 'ふたり'), ('複数', 'ふくすう'), ('二人分', 'ふたりぶん')],
    ]
    for group in groups:
        for kw, ym in group:
            lines.extend(full_expand(kw, ym))
    return '\n'.join(dedup(lines, 200))


def gen_department():
    lines = []
    dept_list = [
        ('総合診療科', 'そうごうしんりょうか'), ('血液内科', 'けつえきないか'),
        ('消化器内科', 'しょうかきないか'), ('循環器科', 'じゅんかんきか'),
        ('腎臓内科', 'じんぞうないか'), ('泌尿器科', 'ひにょうきか'),
        ('総合外科', 'そうごうげか'), ('消化器外科', 'しょうかきげか'),
        ('整形外科', 'せいけいげか'), ('脳神経外科', 'のうしんけいげか'),
        ('形成外科', 'けいせいげか'), ('小児科', 'しょうにか'),
        ('眼科', 'がんか'), ('脳神経内科', 'のうしんけいないか'),
        ('耳鼻咽喉科', 'じびいんこうか'), ('歯科口腔外科', 'しかこうくうげか'),
        ('皮膚科', 'ひふか'), ('糖尿病代謝内科', 'とうにょうびょうたいしゃないか'),
        ('血管内治療科', 'けっかんないちりょうか'), ('産婦人科', 'さんふじんか'),
        ('呼吸器内科', 'こきゅうきないか'), ('呼吸器外科', 'こきゅうきげか'),
        ('リウマチ膠原病内科', 'りうまちこうげんびょうないか'),
        ('甲状腺内分泌外科', 'こうじょうせんないぶんぴつげか'),
        ('初診外来', 'しょしんがいらい'), ('女性泌尿器科', 'じょせいひにょうきか'),
        ('乳腺科', 'にゅうせんか'), ('小児循環器科', 'しょうにじゅんかんきか'),
        ('リハビリ', 'りはびり'), ('乳腺・甲状腺科', 'にゅうせんこうじょうせんか'),
    ]
    extras = [
        ('内科', 'ないか'), ('外科', 'げか'), ('整形', 'せいけい'),
        ('脳外科', 'のうげか'), ('耳鼻科', 'じびか'),
        ('婦人科', 'ふじんか'), ('産科', 'さんか'),
        ('消化器', 'しょうかき'), ('循環器', 'じゅんかんき'),
        ('泌尿器', 'ひにょうき'), ('呼吸器', 'こきゅうき'),
        ('乳腺', 'にゅうせん'), ('糖尿病', 'とうにょうびょう'),
        ('リウマチ', 'りうまち'), ('甲状腺', 'こうじょうせん'),
        ('歯科', 'しか'), ('口腔外科', 'こうくうげか'),
        ('わからない', 'わからない'), ('わかりません', 'わかりません'),
        ('不明', 'ふめい'),
    ]
    # Base + atama_kire for all departments
    for kw, ym in dept_list:
        lines.append(f"{kw} {ym}")
        lines.extend(atama_kire(kw, ym))
    for kw, ym in extras:
        lines.append(f"{kw} {ym}")
    # Filler for key departments
    key_depts = [
        ('内科', 'ないか'), ('外科', 'げか'), ('整形外科', 'せいけいげか'),
        ('消化器内科', 'しょうかきないか'), ('眼科', 'がんか'),
        ('皮膚科', 'ひふか'), ('耳鼻科', 'じびか'),
        ('泌尿器科', 'ひにょうきか'), ('産婦人科', 'さんふじんか'),
    ]
    for kw, ym in key_depts:
        for fl in FILLERS:
            lines.append(f"{kw} {fl}{ym}")
    # Gobi for common ones
    for kw, ym in [('内科', 'ないか'), ('外科', 'げか'), ('整形外科', 'せいけいげか'),
                    ('眼科', 'がんか'), ('皮膚科', 'ひふか')]:
        for g in GOBIS:
            lines.append(f"{kw} {ym}{g}")
    return '\n'.join(dedup(lines, 200))


def gen_department2():
    lines = []
    yes_no_kw = [
        ('はい', 'はい'), ('ある', 'ある'), ('あります', 'あります'),
        ('ない', 'ない'), ('ありません', 'ありません'), ('ないです', 'ないです'),
        ('特にない', 'とくにない'), ('それだけ', 'それだけ'),
        ('一つだけ', 'ひとつだけ'), ('大丈夫', 'だいじょうぶ'),
    ]
    for kw, ym in yes_no_kw:
        lines.extend(full_expand(kw, ym))
    dept_short = [
        ('内科', 'ないか'), ('外科', 'げか'), ('整形外科', 'せいけいげか'),
        ('眼科', 'がんか'), ('皮膚科', 'ひふか'), ('耳鼻科', 'じびか'),
        ('泌尿器科', 'ひにょうきか'), ('産婦人科', 'さんふじんか'),
        ('消化器内科', 'しょうかきないか'), ('循環器科', 'じゅんかんきか'),
        ('脳神経外科', 'のうしんけいげか'), ('呼吸器内科', 'こきゅうきないか'),
    ]
    for kw, ym in dept_short:
        lines.append(f"{kw} {ym}")
        lines.extend(atama_kire(kw, ym))
    return '\n'.join(dedup(lines, 200))


def gen_doctor():
    lines = []
    keywords = [
        ('わからない', 'わからない'), ('わかりません', 'わかりません'),
        ('覚えていない', 'おぼえていない'), ('忘れました', 'わすれました'),
        ('誰でもいい', 'だれでもいい'), ('特にない', 'とくにない'),
        ('担当', 'たんとう'), ('先生', 'せんせい'),
        ('担当の先生', 'たんとうのせんせい'), ('主治医', 'しゅじい'),
        ('ドクター', 'どくたー'),
    ]
    for kw, ym in keywords:
        lines.extend(full_expand(kw, ym))
    name_phrases = [
        ('私は', 'わたしは'), ('名前は', 'なまえは'),
        ('先生は', 'せんせいは'), ('です', 'です'),
        ('と申します', 'ともうします'), ('という先生', 'というせんせい'),
    ]
    for kw, ym in name_phrases:
        lines.append(f"{kw} {ym}")
    return '\n'.join(dedup(lines, 200))


def gen_date():
    lines = []
    eras = [('令和', 'れいわ'), ('平成', 'へいせい'),
            ('昭和', 'しょうわ'), ('大正', 'たいしょう')]
    for kw, ym in eras:
        lines.append(f"{kw} {ym}")
        lines.extend(filler_expand(kw, ym))
        lines.extend(atama_kire(kw, ym))
    # Era misrecognition patterns
    lines.extend(['昭和 きょうわ', '昭和 きょうは', '令和 えいわ', '平成 えいせい'])
    # Months
    months = [('1月', 'いちがつ'), ('2月', 'にがつ'), ('3月', 'さんがつ'),
              ('4月', 'しがつ'), ('5月', 'ごがつ'), ('6月', 'ろくがつ'),
              ('7月', 'しちがつ'), ('8月', 'はちがつ'), ('9月', 'くがつ'),
              ('10月', 'じゅうがつ'), ('11月', 'じゅういちがつ'), ('12月', 'じゅうにがつ')]
    for kw, ym in months:
        lines.append(f"{kw} {ym}")
    # Special day readings
    days_special = [
        ('1日', 'ついたち'), ('2日', 'ふつか'), ('3日', 'みっか'),
        ('4日', 'よっか'), ('5日', 'いつか'), ('6日', 'むいか'),
        ('7日', 'なのか'), ('8日', 'ようか'), ('9日', 'ここのか'),
        ('10日', 'とおか'), ('14日', 'じゅうよっか'), ('20日', 'はつか'),
        ('24日', 'にじゅうよっか')]
    for kw, ym in days_special:
        lines.append(f"{kw} {ym}")
    # Regular day readings
    for d in [11, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 28, 29, 30, 31]:
        lines.append(f"{d}日 {_num_to_yomi(d)}にち")
    # Relative dates
    rel_dates = [
        ('来週', 'らいしゅう'), ('再来週', 'さらいしゅう'), ('来月', 'らいげつ'),
        ('明日', 'あした'), ('明後日', 'あさって'), ('今週', 'こんしゅう'),
        ('今月', 'こんげつ'), ('明日', 'あす'),
    ]
    for kw, ym in rel_dates:
        lines.append(f"{kw} {ym}")
        lines.extend(filler_expand(kw, ym))
    # Days of week
    dow = [('月曜日', 'げつようび'), ('火曜日', 'かようび'), ('水曜日', 'すいようび'),
           ('木曜日', 'もくようび'), ('金曜日', 'きんようび'),
           ('土曜日', 'どようび'), ('日曜日', 'にちようび')]
    for kw, ym in dow:
        lines.append(f"{kw} {ym}")
        lines.extend(atama_kire(kw, ym))
    # Gobi for relative dates
    for kw, ym in [('来週', 'らいしゅう'), ('来月', 'らいげつ')]:
        lines.extend(gobi_expand(kw, ym))
    # Number readings
    nums = [('1', 'いち'), ('2', 'に'), ('3', 'さん'), ('4', 'よん'), ('4', 'し'),
            ('5', 'ご'), ('6', 'ろく'), ('7', 'なな'), ('7', 'しち'),
            ('8', 'はち'), ('9', 'きゅう'), ('10', 'じゅう'),
            ('20', 'にじゅう'), ('30', 'さんじゅう')]
    for kw, ym in nums:
        lines.append(f"{kw} {ym}")
    return '\n'.join(dedup(lines, 200))


def gen_reason():
    lines = []
    keywords = [
        ('体調不良', 'たいちょうふりょう'), ('風邪', 'かぜ'), ('発熱', 'はつねつ'),
        ('熱が出た', 'ねつがでた'), ('急用', 'きゅうよう'), ('仕事', 'しごと'),
        ('仕事が入った', 'しごとがはいった'), ('都合が悪い', 'つごうがわるい'),
        ('コロナ', 'ころな'), ('インフル', 'いんふる'), ('家族', 'かぞく'),
        ('子供', 'こども'), ('急病', 'きゅうびょう'), ('忘れていた', 'わすれていた'),
        ('入院', 'にゅういん'), ('旅行', 'りょこう'), ('引っ越し', 'ひっこし'),
        ('日程が合わない', 'にっていがあわない'), ('予定が入った', 'よていがはいった'),
        ('別の病院', 'べつのびょういん'), ('用事', 'ようじ'),
        ('交通機関', 'こうつうきかん'), ('電車が止まった', 'でんしゃがとまった'),
    ]
    for kw, ym in keywords:
        lines.extend(full_expand(kw, ym))
    return '\n'.join(dedup(lines, 200))


def gen_yes_no_shokaijo():
    lines = read_yes_no()
    # 紹介状 specific expansions
    shokaijo_kw = [
        ('紹介状', 'しょうかいじょう'), ('持っています', 'もっています'),
        ('持ってます', 'もってます'), ('持ってない', 'もってない'),
        ('持っていません', 'もっていません'), ('あります', 'あります'),
        ('ありません', 'ありません'),
    ]
    for kw, ym in shokaijo_kw:
        lines.extend(full_expand(kw, ym))
    return '\n'.join(dedup(lines, 200))


def gen_yes_no_symptom():
    lines = read_yes_no()
    symptom_kw = [
        ('症状', 'しょうじょう'), ('何もない', 'なにもない'),
        ('特にない', 'とくにない'), ('少しある', 'すこしある'),
        ('痛い', 'いたい'), ('痛み', 'いたみ'),
        ('出血', 'しゅっけつ'), ('しこり', 'しこり'),
        ('あります', 'あります'), ('ないです', 'ないです'),
        ('気になる', 'きになる'), ('違和感', 'いわかん'),
    ]
    for kw, ym in symptom_kw:
        lines.extend(full_expand(kw, ym))
    return '\n'.join(dedup(lines, 200))


def gen_yes_no_jushinken():
    lines = read_yes_no()
    jushinken_kw = [
        ('受診券', 'じゅしんけん'), ('利用券', 'りようけん'),
        ('クーポン', 'くーぽん'), ('持っています', 'もっています'),
        ('持ってます', 'もってます'), ('持ってない', 'もってない'),
        ('持っていません', 'もっていません'), ('あります', 'あります'),
        ('ありません', 'ありません'),
    ]
    for kw, ym in jushinken_kw:
        lines.extend(full_expand(kw, ym))
    return '\n'.join(dedup(lines, 200))


def gen_shichoson():
    lines = []
    municipalities = [
        ('牛久市', 'うしくし'), ('つくば市', 'つくばし'),
        ('龍ケ崎市', 'りゅうがさきし'), ('取手市', 'とりでし'),
        ('守谷市', 'もりやし'), ('土浦市', 'つちうらし'),
        ('阿見町', 'あみまち'), ('利根町', 'とねまち'),
        ('河内町', 'かわちまち'), ('美浦村', 'みほむら'),
        ('稲敷市', 'いなしきし'), ('つくばみらい市', 'つくばみらいし'),
        ('かすみがうら市', 'かすみがうらし'), ('石岡市', 'いしおかし'),
        ('常総市', 'じょうそうし'), ('坂東市', 'ばんどうし'),
        ('水戸市', 'みとし'), ('日立市', 'ひたちし'),
        ('柏市', 'かしわし'), ('流山市', 'ながれやまし'),
        ('我孫子市', 'あびこし'),
    ]
    for kw, ym in municipalities:
        lines.append(f"{kw} {ym}")
        lines.extend(filler_expand(kw, ym))
        lines.extend(atama_kire(kw, ym))
    lines.extend([
        'わからない わからない', 'わかりません わかりません',
    ])
    return '\n'.join(dedup(lines, 200))


def gen_yes_no_douji():
    lines = read_yes_no()
    douji_kw = [
        ('子宮がん', 'しきゅうがん'), ('乳がん', 'にゅうがん'),
        ('両方', 'りょうほう'), ('片方だけ', 'かたほうだけ'),
        ('一緒に', 'いっしょに'), ('同時に', 'どうじに'),
        ('お願いします', 'おねがいします'), ('結構です', 'けっこうです'),
        ('子宮がん検診', 'しきゅうがんけんしん'), ('乳がん検診', 'にゅうがんけんしん'),
    ]
    for kw, ym in douji_kw:
        lines.extend(full_expand(kw, ym))
    return '\n'.join(dedup(lines, 200))


# ===== MODULE MAPPING =====

module_config = {
    '入力_用件聴取': ('yoken', gen_yoken),
    '入力_確認_診療科': ('department', gen_department),
    '入力_確認_診療科2': ('department2', gen_department2),
    '入力_変更_診療科': ('department', gen_department),
    '入力_変更_診療科2': ('department2', gen_department2),
    '入力_変更_担当先生': ('doctor', gen_doctor),
    '入力_変更_現在の予約日': ('date', gen_date),
    '入力_変更_予約希望日': ('date', gen_date),
    '入力_変更_理由': ('reason', gen_reason),
    '入力_キャンセル_理由': ('reason', gen_reason),
    '入力_新規_診療科': ('department', gen_department),
    '入力_新規_診療科2': ('department2', gen_department2),
    '入力_新規_紹介状確認': ('yes_no_shokaijo', gen_yes_no_shokaijo),
    '入力_新規_担当先生': ('doctor', gen_doctor),
    '入力_新規_予約希望日': ('date', gen_date),
    '入力_再診_診療科': ('department', gen_department),
    '入力_再診_診療科2': ('department2', gen_department2),
    '入力_再診_担当先生': ('doctor', gen_doctor),
    '入力_再診_予約希望日': ('date', gen_date),
    '入力_がん検診_症状確認': ('symptom', gen_yes_no_symptom),
    '入力_がん検診_受診券確認': ('jushinken', gen_yes_no_jushinken),
    '入力_がん検診_市町村': ('shichoson', gen_shichoson),
    '入力_がん検診_同時予約': ('douji', gen_yes_no_douji),
    '入力_がん検診_担当先生': ('doctor', gen_doctor),
    '入力_がん検診_予約希望日': ('date', gen_date),
}

# ===== GENERATE & ASSIGN =====

cache = {}
for mod_name, (dtype, gen_func) in module_config.items():
    if dtype not in cache:
        cache[dtype] = gen_func()
    pw = cache[dtype]
    data['modules'][mod_name]['params']['profile_words'] = pw
    word_count = len(pw.strip().split('\n'))
    print(f"{mod_name}: {word_count} words [{dtype}]")

# ===== QUALITY CHECKLIST =====

print('\n=== QUALITY CHECKLIST ===')
all_pass = True
for mod_name in module_config:
    pw = data['modules'][mod_name]['params']['profile_words']
    lines_list = [l for l in pw.strip().split('\n') if l.strip()]
    dtype = module_config[mod_name][0]

    # 1. Format check
    fmt_ok = all(len(l.split(' ')) >= 2 for l in lines_list)
    # 2. Yomi is hiragana + long vowel mark
    yomi_ok = True
    for l in lines_list:
        parts = l.split(' ', 1)
        if len(parts) >= 2:
            yomi = parts[1]
            if not re.match(r'^[ぁ-ゖー]+$', yomi):
                yomi_ok = False
                break
    # 3. Word count
    count = len(lines_list)
    is_freetext = dtype in ['shichoson']
    count_ok = (50 <= count) if is_freetext else (100 <= count <= 200)
    # 4. Filler TOP6 present
    pw_text = pw
    if dtype not in ['shichoson']:
        has_fillers = all(f' {fl}' in pw_text for fl in FILLERS)
    else:
        has_fillers = True
    # 5. No まー
    no_maar = ' まー' not in pw_text
    # 6. Half-width digits only
    fullwidth = re.search(r'[０-９]', pw_text)
    hw_ok = fullwidth is None

    status = 'PASS' if (fmt_ok and yomi_ok and count_ok and no_maar and hw_ok and has_fillers) else 'FAIL'
    if status == 'FAIL':
        all_pass = False
        issues = []
        if not fmt_ok: issues.append('FORMAT')
        if not yomi_ok: issues.append('YOMI')
        if not count_ok: issues.append(f'COUNT={count}')
        if not has_fillers: issues.append('FILLERS')
        if not no_maar: issues.append('MAAR')
        if not hw_ok: issues.append('FULLWIDTH')
        print(f"  {mod_name}: {status} [{', '.join(issues)}]")
    else:
        print(f"  {mod_name}: {status} (count={count})")

print(f"\nOverall: {'ALL PASS' if all_pass else 'SOME FAILURES - FIX REQUIRED'}")

# ===== SAVE =====

with open(FLOW_PATH, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f'\nJSON saved to {FLOW_PATH}')
