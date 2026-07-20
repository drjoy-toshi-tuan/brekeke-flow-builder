# -*- coding: utf-8 -*-
"""department_classifier — universe 構造化版 v0（ストア試作 / engine v2 候補）

現行 v1（北里30科フラット・施設別）を、標榜診療科 universe を覆う**施設非依存**の分類器へ。
土台データ: reference/departments/（レセE-20/E-19 63科 + 基本科 + 経過措置単独 + 命名規則）。

v0 スコープ（意図的に「広く浅く」を避ける）:
  - ENUMERATED レキシコン（universe canonical + 読み/表記/エイリアス）を **最長一致**で引く。
    読みは北里 v1 oracle の資産を継承、未収のものは canonical/基本読みで seed（実ログ 1b で enrich）。
  - 経過措置の単独禁止科（胃腸科/神経科等）は**実ログに出る**ので受理し、可能なら現行系へ正規化。
  - 出力ラベルを拡張: canonical / AMBIGUOUS(基本科なしの臓器語=内/外不明) /
    OUT_OF_SCOPE(専門外来・法令根拠なし単独=T) / 登録なし(わからない) / NO_RESULT。
  - **生成コンポーザ（base×modifier の合成・1050パターン）は v0.1 に後置**＝実ログ 1b で
    実在する組み合わせを見てから作る（机上合成を先に作らない）。compose_generative() は stub。

施設サブセット: facility_offered（任意・その施設が実際に持つ科の集合）。指定時、universe で当たった
canonical がサブセット外なら OFF_MENU を併記できる（v0 は recognized canonical をそのまま返す）。
"""
import unicodedata

# ---- 正規化（北里 v1 oracle と同方式） ----
_STRIP = [" ", "　", "「", "」", "、", "。", "・", "．", "，", "”", "“", "\t", "\r", "\n"]
_TRAILERS = ["でお願いします", "をお願いします", "おねがいします", "になります", "です",
             "でお願い", "が希望", "を希望", "希望", "の方", "のほう", "科目", "かな", "かも",
             "を受診", "に行きたい", "がいい", "でいい"]

WAKARANAI = ["わからない", "わかりません", "わからん", "不明", "決まっていない",
             "決まってない", "きまっていない", "未定", "忘れ", "わすれ"]

# スコープ外（決定論化せず OpenAI/再質問へ＝T バケット）。
# OOS_NAMES = 具体名。enumerated/WAKARANAI より「前」に弾く
#   （審美歯科⊃歯科 の最長一致誤取り・もの忘れ外来⊃忘れ の WAKARANAI 誤取りを回避）。
OOS_NAMES = [
    "頭痛外来", "禁煙外来", "もの忘れ外来", "物忘れ外来", "発熱外来", "渡航外来",
    "女性科", "老年科", "化学療法科", "疼痛緩和科", "ペインクリニック科",
    "性感染症科", "インプラント科", "審美歯科", "アンチエイジング",
]
# OOS_SUFFIX = 汎用「○○外来」。enumerated の「後」に判定
#   （整形外科外来→整形外科 を守りつつ、未知の専門外来を捕捉）。
OOS_SUFFIX = ["外来"]

# 基本科なしで来ると 内/外 等が決まらない臓器・系統語 → AMBIGUOUS（確認要）
AMBIGUOUS_ORGAN = [
    "消化器", "呼吸器", "循環器", "脳神経", "心臓", "心臓血管", "血管", "乳腺",
    "甲状腺", "腎臓", "肝臓", "胆のう", "膵臓", "胃腸", "大腸", "頭頸部", "神経",
]

# ---- ENUMERATED レキシコン（universe canonical -> 一致キー） ----
# 北里 v1 の読み資産を継承しつつ、レセ63 と基本科を網羅。canonical は universe 形を採る。
DEPARTMENTS = [
    # 基本科（医科の幹・単独標榜可）
    # `ないか` 除去（2026-07-01）= 短キー磁石。「循環器ないか/脳神経ないか/睡眠障害ないか」等を
    # bare 内科 へ潰し具体科の特異性を喪失（diagnose 620freq）。bare 内科 は kanji キーで拾え、
    # 〜ないか 系は compose_generative が修飾語+内科へ復元する。
    ("内科", ["内科"]),
    # `げか` 除去（2026-07-01）= ないか と同型。臓器+げか（脳神経げか等）を bare 外科へ潰しコンポーザを
    # 先取りするのを回避。bare 外科 は kanji キーで拾い、〜げか 系はコンポーザが修飾語+外科へ復元。
    ("外科", ["外科"]),
    ("精神科", ["精神科", "心療内科", "精神神経科", "せいしんか", "しんりょうないか"]),
    ("小児科", ["小児科", "しょうにか", "しょうに", "こども", "ようじ"]),
    ("皮膚科", ["皮膚科", "ひふか", "ひふ"]),
    ("泌尿器科", ["泌尿器科", "泌尿器", "ひにょうきか", "ひにょうき", "ひにょう"]),
    ("眼科", ["眼科", "がんか", "めか"]),
    ("耳鼻咽喉科", ["耳鼻咽喉科", "耳鼻いんこう科", "耳鼻科", "じびいんこうか", "じびか", "じび", "いんこうか"]),
    ("アレルギー科", ["アレルギー科", "あれるぎーか", "あれるぎー"]),
    ("リウマチ科", ["リウマチ科", "りうまちか", "りうまち"]),
    ("産婦人科", ["産婦人科", "さんふじんか"]),
    ("産科", ["産科", "さんか"]),
    ("婦人科", ["婦人科", "ふじんか"]),
    ("リハビリテーション科", ["リハビリテーション科", "リハビリ科", "リハビリ", "りはびり", "りはびりてーしょん"]),
    ("放射線科", ["放射線科", "ほうしゃせんか"]),
    ("放射線治療科", ["放射線治療科", "放射線治療", "ほうしゃせんちりょう"]),
    ("放射線診断科", ["放射線診断科", "放射線診断", "ほうしゃせんしんだん"]),
    ("病理診断科", ["病理診断科", "病理診断", "びょうり"]),
    ("臨床検査科", ["臨床検査科", "臨床検査"]),
    ("救急科", ["救急科", "救急医学科", "きゅうきゅうか", "きゅうきゅう"]),
    ("麻酔科", ["麻酔科", "ますいか", "ますい", "ペインクリニック", "ぺいん"]),
    # `しか` 除去（2026-07-01）= 助詞「しか」(〜しかない/しかし)を歯科へ吸込む磁石（diagnose 40freq）。
    # `ますい`(8freq) は保持＝有効な麻酔読み・yes/no 越境ガベージは carve が上流除去・test 依存（見直し結論）。
    ("歯科", ["歯科", "歯医者", "はいしゃ"]),
    ("小児歯科", ["小児歯科", "しょうにしか"]),
    ("矯正歯科", ["矯正歯科", "歯科矯正科", "きょうせいしか"]),
    ("歯科口腔外科", ["歯科口腔外科", "口腔外科", "こうくうげか"]),
    # 内科系（臓器×内科）
    ("呼吸器内科", ["呼吸器内科", "こきゅうきないか", "こきゅうか", "こきゅう", "こない"]),
    ("循環器内科", ["循環器内科", "循環器", "じゅんかんきないか", "じゅんかんき", "じゅんない"]),
    ("消化器内科", ["消化器内科", "しょうかきないか", "しょうかき", "しょうない"]),
    ("腎臓内科", ["腎臓内科", "じんぞうないか", "じんぞう", "じんない"]),
    ("糖尿病・内分泌代謝内科", ["糖尿病内分泌代謝内科", "糖尿病代謝内科", "内分泌代謝内科", "内分泌内科", "代謝内科", "糖尿病内科", "とうにょうびょう", "ないぶんぴつ", "ないぶん"]),
    ("血液内科", ["血液内科", "けつえきないか", "けつえき", "けつない"]),
    ("脳神経内科", ["脳神経内科", "神経内科", "のうしんけいないか", "しんけいないか", "のうない"]),
    ("膠原病リウマチ内科", ["膠原病リウマチ内科", "リウマチ膠原病感染内科", "膠原病感染内科", "膠原病", "こうげんびょう"]),
    # `がん`/`癌` 除去（2026-07-01）= 偽マッチ磁石。「癌化」(医学用語・科でない508)・「乳がん検診」を
    # 腫瘍内科へ吸込み exact 僅か2%（diagnose 776+160freq）。腫瘍内科は明示形のみで引く。
    ("腫瘍内科", ["腫瘍内科", "腫瘍治療科", "しゅようないか"]),
    # 外科系（臓器×外科）
    ("消化器外科", ["消化器外科", "一般消化器外科", "一般外科", "肝胆膵外科", "大腸肛門科", "しょうかきげか", "いっぱんげか"]),
    ("呼吸器外科", ["呼吸器外科", "こきゅうきげか", "こげ"]),
    ("心臓血管外科", ["心臓血管外科", "心臓外科", "しんぞうけっかんげか", "しんぞうげか", "しんげ"]),
    ("脳神経外科", ["脳神経外科", "脳外科", "のうしんけいげか", "のうげか", "のうげ"]),
    ("整形外科", ["整形外科", "せいけいげか", "せいけい"]),
    ("形成外科", ["形成外科", "形成外科美容外科", "けいせいげか", "けいせい"]),
    ("美容外科", ["美容外科", "びようげか"]),
    ("乳腺甲状腺外科", ["乳腺甲状腺外科", "乳腺甲状腺", "乳腺外科", "乳腺", "にゅうせん"]),
    ("小児外科", ["小児外科", "しょうにげか"]),
    ("耳鼻咽喉科・頭頸部外科", ["耳鼻咽喉科頭頸部外科", "頭頸部外科", "頭頸部", "とうけいぶ"]),
    # 経過措置の単独禁止科（実ログに残存・受理する。系へ寄せる）
    ("胃腸科", ["胃腸科", "いちょうか", "いちょう"]),
    ("こう門科", ["こう門科", "肛門科", "こうもんか"]),
    # その他レセ実在
    ("総合診療科", ["総合診療科", "総合診療部", "総合診療", "そうごうしんりょう", "そうごう", "そうしん"]),
    ("新生児科", ["新生児科", "しんせいじか", "しんせいじ"]),
    ("小児循環器科", ["小児循環器科", "しょうにじゅんかんき"]),
    ("小児心臓血管外科", ["小児心臓血管外科", "しょうにしんぞう"]),
    ("脳卒中科", ["脳卒中科", "のうそっちゅう"]),
    ("性病科", ["性病科", "せいびょうか"]),
    ("気管食道科", ["気管食道科", "きかんしょくどう"]),
    ("皮膚泌尿器科", ["皮膚泌尿器科"]),
]

# (key, canonical) を長さ降順 = 最長一致優先（消化器 ⊂ 消化器内科 等の包含を正しく裁く）
_KEYS = sorted(
    [(k, canon) for canon, keys in DEPARTMENTS for k in keys],
    key=lambda kc: len(kc[0]), reverse=True,
)
CANONICAL = [c for c, _ in DEPARTMENTS]

RESULT_NONE = "NO_RESULT"
RESULT_WAKARANAI = "登録なし"
RESULT_AMBIGUOUS = "AMBIGUOUS"
RESULT_OUT = "OUT_OF_SCOPE"


def normalize(raw):
    if raw is None:
        return ""
    s = unicodedata.normalize("NFKC", str(raw)).strip()
    for ch in _STRIP:
        s = s.replace(ch, "")
    changed = True
    while changed:
        changed = False
        for t in _TRAILERS:
            t2 = t.replace("・", "")
            if t2 and s.endswith(t2) and len(s) > len(t2):
                s = s[: -len(t2)]
                changed = True
    return s


# ---- 生成コンポーザ v0.1（base科 × 修飾語の合成） ----
# 診療科は数十の列挙でなく base×modifier の生成空間（reference/departments/）。enumerated（明示 kanji 形）が
# 外した残差のうち、「修飾語(臓器/系統) + base科 suffix」の形を canonical へ合成する。
# 主な発火源 = STT が base を hiragana 化した形（循環器ないか/脳神経ないか…）と、bare organ key を
# 持たない臓器×内科の組合せ。実在組合せは実ログ 1b(diagnose の `ないか`磁石620freq) で確認済。
# base suffix（kanji + STT hiragana）。順序は最長一致用に長い順。
_BASE_INNER = ("内科", "ないか")
_BASE_OUTER = ("外科", "げか")
# 修飾語 → 内科系 canonical
_MOD_INNER = {
    "循環器": "循環器内科", "消化器": "消化器内科", "呼吸器": "呼吸器内科",
    "腎臓": "腎臓内科", "血液": "血液内科", "脳神経": "脳神経内科", "神経": "脳神経内科",
    "糖尿病": "糖尿病・内分泌代謝内科", "内分泌": "糖尿病・内分泌代謝内科", "腫瘍": "腫瘍内科",
}
# 修飾語 → 外科系 canonical
_MOD_OUTER = {
    "脳神経": "脳神経外科", "消化器": "消化器外科", "呼吸器": "呼吸器外科",
    "心臓血管": "心臓血管外科", "心臓": "心臓血管外科", "乳腺": "乳腺甲状腺外科",
    "甲状腺": "乳腺甲状腺外科", "頭頸部": "耳鼻咽喉科・頭頸部外科",
    "整形": "整形外科", "形成": "形成外科", "小児": "小児外科",
}


# ---- 略語・別表記の完全一致テーブル（2026-07-01 enrich・triage part-fixable由来） ----
# bare 略語（内科/外科 接尾なし）は compose_generative の経路に乗らず取りこぼす（内分泌科/糖尿病/整形…）。
# **完全一致のみ**で拾う＝短キー部分一致の over-match 磁石（diagnose 教訓）を作らない。ASK スロット
# 文脈では「整形」=整形外科・「糖尿病」=糖尿病内科 と一意ゆえ exact は安全。曖昧 bare（放射線=科/治療/
# 診断・循環=内/外・小児=科/外/循環器・精神="精神的に"誤爆）は**入れない**（AMBIGUOUS/据置が正）。
_ABBREV = {
    "整形": "整形外科",
    "形成": "形成外科",
    "糖尿病": "糖尿病・内分泌代謝内科", "糖尿": "糖尿病・内分泌代謝内科",
    "内分泌": "糖尿病・内分泌代謝内科", "内分泌科": "糖尿病・内分泌代謝内科",
    "内分泌代謝": "糖尿病・内分泌代謝内科", "内分泌代謝科": "糖尿病・内分泌代謝内科",
    "代謝内分泌": "糖尿病・内分泌代謝内科",
}


def match_abbrev(s):
    """略語の完全一致（末尾の疑問助詞「か」1字は許容＝内分泌か→内分泌）。無ければ None。"""
    for cand in (s, s[:-1] if (s.endswith("か") and len(s) > 2) else None):
        if cand and cand in _ABBREV:
            return _ABBREV[cand]
    return None


def compose_generative(s):
    """base科 suffix を剥がし、prefix の修飾語(臓器/系統)を最長一致で引いて canonical を合成。

    enumerated が外した後の残差専用（classify step5）。base suffix が無ければ None。
    例: 脳神経ないか→脳神経内科 / 消化器外科の hiragana 崩れ → 消化器外科。
    """
    for bases, mod_map, base_canon in (
        (_BASE_INNER, _MOD_INNER, "内科"),
        (_BASE_OUTER, _MOD_OUTER, "外科"),
    ):
        for bk in bases:
            # bare base科の STT hiragana（ないか=内科 / げか=外科）＝完全一致のみ。
            # enumerated で `ないか`/`げか` キーを除去した分の bare 内科/外科 を取り戻す。
            # 完全一致に限るので「じゃないか/のではないか」等の非診療語は内科に化けない。
            if s == bk:
                return base_canon
            # 修飾語(臓器/系統) + base科 → 特定科。prefix に既知 modifier が無ければ合成しない。
            if s.endswith(bk) and len(s) > len(bk):
                prefix = s[: -len(bk)]
                for mod in sorted(mod_map, key=len, reverse=True):
                    if mod in prefix:
                        return mod_map[mod]
    return None


def classify(raw, facility_offered=None):
    """診療科を universe canonical / AMBIGUOUS / OUT_OF_SCOPE / 登録なし / NO_RESULT に分類。"""
    s = normalize(raw)
    if s == "":
        return RESULT_NONE
    # 1) DTMF 数字のみ
    if s.isdigit():
        return RESULT_NONE
    # 2) スコープ外・具体名（enumerated/WAKARANAI より前＝審美歯科⊃歯科・もの忘れ⊃忘れ の誤取り回避）
    for m in OOS_NAMES:
        if m in s:
            return RESULT_OUT
    # 3) 不明意図（わからない・未定・忘れた）
    for w in WAKARANAI:
        if w.replace("・", "") in s:
            return RESULT_WAKARANAI
    # 4) ENUMERATED 最長一致
    for key, canon in _KEYS:
        if key in s:
            if facility_offered is not None and canon not in facility_offered:
                return canon + "|OFF_MENU"
            return canon
    # 4.5) 略語・別表記の完全一致（enumerated が外した bare 略語＝整形/内分泌科/糖尿病…）
    ab = match_abbrev(s)
    if ab:
        if facility_offered is not None and ab not in facility_offered:
            return ab + "|OFF_MENU"
        return ab
    # 5) 生成合成（v0.1 後置）
    g = compose_generative(s)
    if g:
        return g
    # 6) 汎用「○○外来」＝未知の専門外来（enumerated 後＝整形外科外来→整形外科 を守る）
    for suf in OOS_SUFFIX:
        if suf in s:
            return RESULT_OUT
    # 7) 基本科なしの臓器・系統語 → 内/外 等が決まらず AMBIGUOUS
    for o in AMBIGUOUS_ORGAN:
        if o in s:
            return RESULT_AMBIGUOUS
    # 8) 不一致
    return RESULT_NONE


if __name__ == "__main__":
    import sys
    if getattr(sys.stdout, "reconfigure", None):
        sys.stdout.reconfigure(encoding="utf-8")
    for a in sys.argv[1:]:
        print("%r -> %s" % (a, classify(a)))
