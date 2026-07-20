#!/usr/bin/env python3
"""Stage 2: 関東労災病院 profile_words 生成・充実"""
import json, os

BASE = "output/関東労災病院/fixed/flows"

# ===== 辞書定義 =====

# フィラー14種
FILLERS = ["あ", "あー", "あの", "あのー", "え", "えー", "えっと", "えーと", "ん", "んー", "はい", "そうですね"]

def add_fillers(base_words):
    """キーワードにフィラー前置きを追加"""
    result = []
    for entry in base_words:
        parts = entry.split(" ", 1)
        if len(parts) != 2:
            continue
        hyoji, yomi = parts
        result.append(entry)
        for f in FILLERS:
            result.append(f"{hyoji} {f}{yomi}")
    return result

def add_gobi(base_words):
    """語尾バリエーション追加"""
    suffixes = ["です", "で", "なんですが", "になります", "なんだけど", "ですけど", "ですが"]
    result = list(base_words)
    for entry in base_words:
        parts = entry.split(" ", 1)
        if len(parts) != 2:
            continue
        hyoji, yomi = parts
        for s in suffixes:
            result.append(f"{hyoji}{s} {yomi}{s}")
    return result

# ----- 用件確認 (DTMF) -----
PW_YOUKEN = """予約変更 よやくへんこう
変更 へんこう
予約の変更 よやくのへんこう
日程変更 にっていへんこう
日にちを変えたい ひにちをかえたい
キャンセル きゃんせる
予約キャンセル よやくきゃんせる
取り消し とりけし
取消 とりけし
やめたい やめたい
予約を取り消したい よやくをとりけしたい
行けなくなった いけなくなった
予約日時の確認 よやくにちじのかくにん
確認 かくにん
予約確認 よやくかくにん
予約の確認 よやくのかくにん
聞きたい ききたい
日にちの確認 ひにちのかくにん
文書作成 ぶんしょさくせい
文書 ぶんしょ
書類 しょるい
診断書 しんだんしょ
文書のお問い合わせ ぶんしょのおといあわせ
紹介状 しょうかいじょう
予約 よやく
1 いち
2 に
3 さん
4 よん
1番 いちばん
2番 にばん
3番 さんばん
4番 よんばん"""

# ----- 診療科 (STT) — 関東労災病院の科一覧 -----
PW_SHINRYOKA_BASE = """内科 ないか
一般内科 いっぱんないか
消化器内科 しょうかきないか
循環器内科 じゅんかんきないか
呼吸器内科 こきゅうきないか
脳神経内科 のうしんけいないか
外科 げか
消化器外科 しょうかきげか
心臓血管外科 しんぞうけっかんげか
脳神経外科 のうしんけいげか
整形外科 せいけいげか
整形 せいけい
眼科 がんか
耳鼻咽喉科 じびいんこうか
耳鼻科 じびか
皮膚科 ひふか
泌尿器科 ひにょうきか
形成外科 けいせいげか
産婦人科 さんふじんか
婦人科 ふじんか
産科 さんか
リハビリテーション科 りはびりてーしょんか
リハビリ科 りはびりか
リハビリ りはびり
専門外来 せんもんがいらい
脳外科 のうげか
耳鼻 じび
泌尿器 ひにょうき"""

PW_SHINRYOKA_HEADFALL = """消化器内科 ょうかきないか
消化器外科 ょうかきげか
循環器内科 ゅんかんきないか
整形外科 いけいげか
脳神経外科 うしんけいげか
脳神経内科 うしんけいないか
心臓血管外科 んぞうけっかんげか
耳鼻咽喉科 びいんこうか
リハビリテーション科 はびりてーしょんか
産婦人科 んふじんか"""

# ----- 複数診療科確認 (STT) — 同じ診療科辞書を使用 -----
# 入力_複数診療科確認_変更 / _キャンセル

# ----- はい/いいえ (DTMF) — 複数診療科聴取 -----
PW_YESNO_SIMPLE = """はい はい
はい はあ
はい あい
はい い
はーい はーい
ええ ええ
うん うん
あります あります
ある ある
ございます ございます
いいえ いいえ
いいえ いえ
いいえ いい
ないです ないです
ない ない
ありません ありません
ございません ございません
1 いち
2 に"""

# ----- 日付 (DTMF) — 予約日 -----
PW_DATE = """1月 いちがつ
2月 にがつ
3月 さんがつ
4月 しがつ
5月 ごがつ
6月 ろくがつ
7月 しちがつ
8月 はちがつ
9月 くがつ
10月 じゅうがつ
11月 じゅういちがつ
12月 じゅうにがつ
1日 ついたち
2日 ふつか
3日 みっか
4日 よっか
5日 いつか
6日 むいか
7日 なのか
8日 ようか
9日 ここのか
10日 とおか
11日 じゅういちにち
12日 じゅうににち
13日 じゅうさんにち
14日 じゅうよっか
15日 じゅうごにち
16日 じゅうろくにち
17日 じゅうしちにち
18日 じゅうはちにち
19日 じゅうくにち
20日 はつか
21日 にじゅういちにち
22日 にじゅうににち
23日 にじゅうさんにち
24日 にじゅうよっか
25日 にじゅうごにち
26日 にじゅうろくにち
27日 にじゅうしちにち
28日 にじゅうはちにち
29日 にじゅうくにち
30日 さんじゅうにち
31日 さんじゅういちにち
月曜日 げつようび
火曜日 かようび
水曜日 すいようび
木曜日 もくようび
金曜日 きんようび
土曜日 どようび
日曜日 にちようび
来週 らいしゅう
再来週 さらいしゅう
今月 こんげつ
来月 らいげつ
今週 こんしゅう"""

# ----- 変更理由 (STT) -----
PW_HENKOU_RIYUU = """体調不良 たいちょうふりょう
体調が悪い たいちょうがわるい
風邪 かぜ
発熱 はつねつ
熱が出た ねつがでた
仕事 しごと
仕事が入った しごとがはいった
急用 きゅうよう
都合が悪い つごうがわるい
都合がつかない つごうがつかない
予定が入った よていがはいった
用事 ようじ
用事ができた ようじができた
家族の都合 かぞくのつごう
子供 こども
子どもの用事 こどものようじ
通院できない つういんできない
交通機関 こうつうきかん
電車が止まった でんしゃがとまった
忘れていた わすれていた
入院 にゅういん
コロナ ころな
インフルエンザ いんふるえんざ
時間を変えたい じかんをかえたい
日にちを変えたい ひにちをかえたい"""

# ----- キャンセル理由 (STT) — 変更理由と同系 -----
PW_CANCEL_RIYUU = """体調不良 たいちょうふりょう
体調が悪い たいちょうがわるい
風邪 かぜ
発熱 はつねつ
熱が出た ねつがでた
仕事 しごと
仕事が入った しごとがはいった
急用 きゅうよう
都合が悪い つごうがわるい
都合がつかない つごうがつかない
予定が入った よていがはいった
用事 ようじ
行けなくなった いけなくなった
必要なくなった ひつようなくなった
他の病院に行く ほかのびょういんにいく
転院 てんいん
引っ越し ひっこし
遠い とおい
治った なおった
症状が改善した しょうじょうがかいぜんした
もういい もういい
キャンセルしたい きゃんせるしたい"""

# ----- 予約希望日 (STT) — 日付+ない -----
PW_KIBOU_DATE = PW_DATE + """
初旬 しょじゅん
中旬 ちゅうじゅん
下旬 げじゅん
上旬 じょうじゅん
ないです ないです
ない ない
ありません ありません
なし なし
特にありません とくにありません
お任せします おまかせします
いつでもいい いつでもいい
午前 ごぜん
午後 ごご
朝 あさ
昼 ひる
夕方 ゆうがた"""

# ----- 別日希望確認 (STT) — 日付+ない -----
PW_BETSUBI = PW_KIBOU_DATE

# ----- 問い合わせ内容 (STT) -----
PW_TOIAWASE = """予約の確認 よやくのかくにん
予約確認 よやくかくにん
予約日を知りたい よやくびをしりたい
次の予約 つぎのよやく
いつですか いつですか
何時ですか なんじですか
場所 ばしょ
どこですか どこですか
担当医 たんとうい
先生 せんせい
診察時間 しんさつじかん
受付時間 うけつけじかん
持ち物 もちもの
必要なもの ひつようなもの
保険証 ほけんしょう
紹介状 しょうかいじょう
検査結果 けんさけっか
検査 けんさ
薬 くすり
処方箋 しょほうせん
入院 にゅういん
費用 ひよう
料金 りょうきん
支払い しはらい
駐車場 ちゅうしゃじょう
アクセス あくせす
わからない わからない
その他 そのた
相談 そうだん"""

# ----- 生年月日 (DTMF) -----
PW_DOB = """令和 れいわ
平成 へいせい
昭和 しょうわ
大正 たいしょう
西暦 せいれき
1 いち
2 に
3 さん
4 よん
4 し
5 ご
6 ろく
7 なな
7 しち
8 はち
9 きゅう
9 く
0 ぜろ
0 れい
10 じゅう
1月 いちがつ
2月 にがつ
3月 さんがつ
4月 しがつ
5月 ごがつ
6月 ろくがつ
7月 しちがつ
8月 はちがつ
9月 くがつ
10月 じゅうがつ
11月 じゅういちがつ
12月 じゅうにがつ
1日 ついたち
2日 ふつか
3日 みっか
4日 よっか
5日 いつか
6日 むいか
7日 なのか
8日 ようか
9日 ここのか
10日 とおか
20日 はつか"""

# ----- 診察券番号 (DTMF) -----
PW_SHINSAKUKEN = """1 いち
2 に
3 さん
4 よん
4 し
5 ご
6 ろく
7 なな
7 しち
8 はち
9 きゅう
9 く
0 ぜろ
0 れい
わからない わからない
覚えていない おぼえていない
忘れました わすれました
ありません ありません
持っていない もっていない
ないです ないです"""

# ----- はい/いいえ辞書 (DTMF) — 電話番号復唱 -----
PW_YESNO_FULL = """はい はい
はい はあ
はい あい
はい い
はーい はーい
ええ ええ
うん うん
そうです そうです
そうです おうです
そうです うです
合ってます あってます
あってます ってます
大丈夫です だいじょうぶです
だいじょうぶです いじょうぶです
お願いします おねがいします
おねがいします ねがいします
よろしいです よろしいです
いいです いいです
問題ないです もんだいないです
正しいです ただしいです
その通りです そのとおりです
いいえ いいえ
いいえ いえ
いいえ いい
違います ちがいます
ちがいます がいます
違う ちがう
間違いです まちがいです
そうじゃない そうじゃない
違うんです ちがうんです
ダメ だめ
1 いち
2 に"""

# ----- 電話番号 (DTMF) -----
PW_DENWA = """1 いち
2 に
3 さん
4 よん
4 し
5 ご
6 ろく
7 なな
7 しち
8 はち
9 きゅう
9 く
0 ぜろ
0 れい"""


def build_pw_string(raw_text):
    """改行区切りのテキストからprofile_words文字列を生成（重複除去）"""
    seen = set()
    lines = []
    for line in raw_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line not in seen:
            seen.add(line)
            lines.append(line)
    return "\n".join(lines)


def build_shinryoka_pw():
    """診療科辞書: ベース + フィラー + 頭落ち"""
    base_lines = [l.strip() for l in PW_SHINRYOKA_BASE.strip().split("\n") if l.strip()]
    headfall_lines = [l.strip() for l in PW_SHINRYOKA_HEADFALL.strip().split("\n") if l.strip()]
    with_fillers = add_fillers(base_lines)
    all_lines = with_fillers + headfall_lines
    return build_pw_string("\n".join(all_lines))


def build_reason_pw(raw):
    """理由辞書: ベース + フィラー + 語尾"""
    base_lines = [l.strip() for l in raw.strip().split("\n") if l.strip() and not l.startswith("#")]
    with_fillers = add_fillers(base_lines)
    with_gobi = add_gobi(with_fillers)
    return build_pw_string("\n".join(with_gobi))


# ===== モジュール→辞書マッピング =====
PW_MAP = {
    # Main flow - 診療
    "入力_用件確認": build_pw_string(PW_YOUKEN),
    "入力_診療科": build_shinryoka_pw(),
    "入力_複数診療科聴取_変更": build_pw_string(PW_YESNO_SIMPLE),
    "入力_複数診療科確認_変更": build_shinryoka_pw(),
    "入力_現在の予約日_変更": build_pw_string(PW_DATE),
    "入力_変更理由": build_reason_pw(PW_HENKOU_RIYUU),
    "入力_予約希望日_変更": build_pw_string(PW_KIBOU_DATE),
    "入力_複数診療科聴取_キャンセル": build_pw_string(PW_YESNO_SIMPLE),
    "入力_複数診療科確認_キャンセル": build_shinryoka_pw(),
    "入力_現在の予約日_キャンセル": build_pw_string(PW_DATE),
    "入力_キャンセル理由": build_reason_pw(PW_CANCEL_RIYUU),
    "入力_別日希望確認": build_pw_string(PW_BETSUBI),
    "入力_診療科_確認": build_shinryoka_pw(),
    "入力_問い合わせ内容": build_reason_pw(PW_TOIAWASE),
    # Subflow - 生年月日
    "入力_患者_生年月日": build_pw_string(PW_DOB),
    # Subflow - 復唱生年月日
    "入力_復唱_患者生年月日": build_pw_string(PW_YESNO_FULL),
    # Subflow - 診察券番号
    "入力_患者_診察券番号": build_pw_string(PW_SHINSAKUKEN),
    # Subflow - 電話番号
    "入力_患者_携帯電話": build_pw_string(PW_YESNO_FULL),
    "入力_患者_連絡先": build_pw_string(PW_DENWA),
    "入力_患者_復唱連絡先": build_pw_string(PW_YESNO_FULL),
}


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)

    fname = os.path.basename(filepath)
    fixes = []
    modules = data.get("modules", {})

    for mname, mod in modules.items():
        mtype = mod.get("type", "")
        if mtype not in (
            "drjoy^AmiVoice$Speech to Text",
            "drjoy^External Integration$DTMF AmiVoice STT Input",
        ):
            continue

        if mname in PW_MAP:
            new_pw = PW_MAP[mname]
            old_pw = mod.get("params", {}).get("profile_words", "")
            old_count = len([l for l in old_pw.split("\n") if l.strip()]) if old_pw else 0
            new_count = len([l for l in new_pw.split("\n") if l.strip()])
            mod["params"]["profile_words"] = new_pw
            fixes.append(f"  [PW] {mname}: {old_count} -> {new_count} words")
        else:
            pw = mod.get("params", {}).get("profile_words", "")
            count = len([l for l in pw.split("\n") if l.strip()]) if pw else 0
            if count == 0:
                fixes.append(f"  [WARN] {mname}: profile_words EMPTY (no mapping)")
            else:
                fixes.append(f"  [OK] {mname}: {count} words (kept)")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n=== {fname} ===")
    for fix in fixes:
        print(fix)
    return len([f for f in fixes if "[PW]" in f])


if __name__ == "__main__":
    total = 0
    for fname in sorted(os.listdir(BASE)):
        if fname.endswith(".json"):
            total += process_file(os.path.join(BASE, fname))
    print(f"\n[TOTAL] {total} modules updated with profile_words")
