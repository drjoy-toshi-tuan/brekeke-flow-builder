# -*- coding: utf-8 -*-
"""field_presence オラクル（聴取STTに「当該フィールドの答え」が含まれるかの判定）。

商談デモ「フリー発話受付」の各聴取STTの直後に置く L1（答え取得判定）の正本。
入力 STT テキストを kind 別に検査し、当該フィールドの答えが取れていれば "PRESENT"、
取れていなければ "ABSENT" を返す（背後の雑音質問が混ざっていても、答えがあれば PRESENT）。

呼び出し側（分岐_L1_X CMR）: "ABSENT" → L0（戻る検知）→ FAQ へ。それ以外(=PRESENT,^0$ other) → 当該聴取の通常処理へ進む。

JS テンプレート docs/brekeke/script_templates/field_presence.js と同一手順・同一辞書（parity）。
検出ロジックは inquiry_extractor（診療科/日付）・field_normalizer（電話/生年月日/診察券）の正本と整合。

kind:
  department … 診療科辞書 longest-match が当たれば PRESENT
  date       … 相対日キーワード or 「N月」「N日」「N年」パターンがあれば PRESENT
  phone      … 0\\d{9,10} があれば PRESENT
  birthday   … 和暦/西暦の「YYYY年M月D日」型があれば PRESENT
  card       … \\d{3,10} があれば PRESENT、または「持っていない/ありません」等の no-card 表明も PRESENT（=カード無しで先へ進める）
"""

import re

# inquiry_extractor / field_normalizer と同一の診療科辞書（longest-match）
DEPARTMENTS = [
    ("循環器内科", ["循環器内科", "循環器"]),
    ("呼吸器内科", ["呼吸器内科"]),
    ("消化器内科", ["消化器内科"]),
    ("脳神経内科", ["脳神経内科", "神経内科"]),
    ("腎臓内科", ["腎臓内科"]),
    ("血液内科", ["血液内科"]),
    ("糖尿病内分泌内科", ["糖尿病内分泌内科", "糖尿病", "内分泌"]),
    ("精神神経科", ["精神神経科", "精神科", "心療内科"]),
    ("小児科", ["小児科", "こども"]),
    ("整形外科", ["整形外科"]),
    ("脳神経外科", ["脳神経外科"]),
    ("心臓血管外科", ["心臓血管外科", "心臓外科"]),
    ("呼吸器外科", ["呼吸器外科"]),
    ("消化器外科", ["消化器外科"]),
    ("形成外科", ["形成外科"]),
    ("美容外科", ["美容外科"]),
    ("乳腺外科", ["乳腺外科", "乳腺"]),
    ("皮膚科", ["皮膚科"]),
    ("泌尿器科", ["泌尿器科", "泌尿器"]),
    ("眼科", ["眼科"]),
    ("耳鼻咽喉科", ["耳鼻咽喉科", "耳鼻科", "耳鼻"]),
    ("婦人科", ["産婦人科", "婦人科"]),
    ("産科", ["産科"]),
    ("放射線科", ["放射線科", "放射線"]),
    ("麻酔科", ["麻酔科", "ペインクリニック"]),
    ("リハビリテーション科", ["リハビリテーション科", "リハビリ"]),
    ("歯科", ["歯科", "歯医者"]),
    ("内科", ["内科"]),
    ("外科", ["外科"]),
]

SEPARATORS = ["-", "－", "ー", "‐", "–", "—", "―", " ", "　", "\t", "\r", "\n"]

# 日付プレゼンス: 相対日キーワード（inquiry_extractor の RELATIVE_DATES と同一集合）
RELATIVE_DATES = ["再来週", "来週", "今週", "今度", "明々後日", "しあさって", "明後日", "あさって",
                  "明日", "あした", "本日", "今日", "きょう"]

# 診察券 no-card 表明（カードを持っていない＝有効な回答として先へ進める）
NO_CARD_PHRASES = ["持っていない", "持ってない", "持ってません", "持っていません",
                   "ありません", "ないです", "なしです", "ございません",
                   "わからない", "わかりません", "不明", "なし"]


def z2h(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFF10 <= o <= 0xFF19:
            out.append(chr(o - 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


def strip_sep(s):
    for sep in SEPARATORS:
        s = s.replace(sep, "")
    return s


def has_department(s):
    keys = []
    for canon, ks in DEPARTMENTS:
        for k in ks:
            keys.append((k, canon))
    keys.sort(key=lambda x: -len(x[0]))
    for k, _canon in keys:
        if k in s:
            return True
    return False


def has_date(s):
    for kw in RELATIVE_DATES:
        if kw in s:
            return True
    if re.search(r"\d{1,2}\s*月", s):
        return True
    if re.search(r"\d{1,2}\s*日", s):
        return True
    if re.search(r"\d{1,4}\s*年", s):
        return True
    return False


def has_phone(s):
    d = strip_sep(z2h(s))
    return re.search(r"0\d{9,10}", d) is not None


def has_birthday(s):
    s = z2h(s)
    if re.search(r"(昭和|平成|令和|大正)\s*\d{1,2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", s):
        return True
    if re.search(r"(?:19|20)\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", s):
        return True
    return False


def has_card(s):
    d = strip_sep(z2h(s))
    if re.search(r"\d{3,10}", d):
        return True
    for p in NO_CARD_PHRASES:
        if p in s:
            return True
    return False


def detect(kind, raw):
    if raw is None:
        return False
    s = z2h(str(raw)).strip()
    if kind == "department":
        return has_department(s)
    if kind == "date":
        return has_date(s)
    if kind == "phone":
        return has_phone(s)
    if kind == "birthday":
        return has_birthday(s)
    if kind == "card":
        return has_card(s)
    return False


def classify(kind, raw):
    """kind の答えが取れていれば 'PRESENT'、無ければ 'ABSENT'。"""
    return "PRESENT" if detect(kind, raw) else "ABSENT"
