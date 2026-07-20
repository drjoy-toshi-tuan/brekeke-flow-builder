# -*- coding: utf-8 -*-
"""field_normalizer オラクル（聴取値の単独フィールド正規化）。

商談デモ「フリー発話受付」の終端 finalize（drjoy_finalize.js）が、聴取経路で
save2db された生 STT を Dr.JOY へ送る前にクリーン化するための正規化ロジックの正本。
JS テンプレート docs/brekeke/script_templates/drjoy_finalize.js と同一手順・同一辞書（parity）。

入力は「フィールド単独」前提（用件抽出=自由発話前提とは別ロジック）。
kind ごとに raw STT を正規化して返す。マッチしなければ "" を返す（呼び出し側=finalize が
clean or raw のフォールバックで既にクリーンな抽出値を消さないようガードする）。
"""

import re

# inquiry_extractor と同一の診療科辞書（longest-match）
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

HONORIFICS = ["さん", "様", "さま", "君", "ちゃん"]
NAME_PREFIX = ["私は", "わたしは", "名前は", "なまえは", "氏名は", "私、", "わたし、"]
NAME_SUFFIX = ["と申します", "ともうします", "と言います", "といいます", "と申し上げます",
               "と言う名前です", "という名前です", "です", "でございます"]
NAME_TRIM = "、。 　\t\r\n"
SEPARATORS = ["-", "－", "ー", "‐", "–", "—", "―", " ", "　", "\t", "\r", "\n"]
# 日付フィールドの末尾丁寧表現（長いものから）
DATE_TAIL = ["でお願いいたします", "でお願いします", "にお願いします", "をお願いします",
             "でお願い", "の予約です", "に予約です", "の予約", "に予約", "です", "でございます"]


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


def norm_name(s):
    s = s.strip()
    for p in NAME_PREFIX:
        if s.startswith(p):
            s = s[len(p):]
            break
    cut = len(s)
    for suf in NAME_SUFFIX:
        i = s.find(suf)
        if 0 <= i < cut:
            cut = i
    s = s[:cut]
    changed = True
    while changed:
        changed = False
        for h in HONORIFICS:
            if s.endswith(h) and len(s) > len(h):
                s = s[:-len(h)]
                changed = True
    return s.strip(NAME_TRIM)


def norm_phone(s):
    d = strip_sep(z2h(s))
    m = re.search(r"0\d{9,10}", d)
    return m.group(0) if m else ""


def norm_card(s):
    d = strip_sep(z2h(s))
    m = re.search(r"\d{3,10}", d)
    return m.group(0) if m else ""


# 和暦元号 → 西暦の基準年（西暦 = base + 元号年）。current_appointment_date.js と同一。
ERA_BASE = {"令和": 2018, "平成": 1988, "昭和": 1925, "大正": 1911}


def _fmt_date(y, mo, d):
    # DATE_OF_BIRTH ウィジェットが要求する保存形式（浜口さん確認 2026-06-17）
    return "%04d-%02d-%02d 00:00:00" % (y, mo, d)


def norm_birthday(s):
    """和暦/西暦の自由発話 → "YYYY-MM-DD 00:00:00"。パース不可なら ""（呼び出し側で raw 維持）。"""
    s = z2h(s)
    m = re.search(r"(昭和|平成|令和|大正)\s*(\d{1,2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if m:
        y = ERA_BASE[m.group(1)] + int(m.group(2))
        return _fmt_date(y, int(m.group(3)), int(m.group(4)))
    m = re.search(r"((?:19|20)\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", s)
    if m:
        return _fmt_date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return ""


def norm_department(s):
    keys = []
    for canon, ks in DEPARTMENTS:
        for k in ks:
            keys.append((k, canon))
    keys.sort(key=lambda x: -len(x[0]))
    for k, canon in keys:
        if k in s:
            return canon
    return ""


def norm_date(s):
    s = z2h(s).strip()
    changed = True
    while changed:
        changed = False
        for t in DATE_TAIL:
            if s.endswith(t) and len(s) > len(t):
                s = s[:-len(t)]
                changed = True
    return s.strip(NAME_TRIM)


def normalize(kind, raw):
    """kind に応じて raw を正規化。マッチ無しは "" を返す（呼び出し側で raw フォールバック）。"""
    if raw is None:
        return ""
    raw = str(raw)
    if kind == "name":
        return norm_name(raw)
    if kind == "phone":
        return norm_phone(raw)
    if kind == "card":
        return norm_card(raw)
    if kind == "birthday":
        return norm_birthday(raw)
    if kind == "department":
        return norm_department(raw)
    if kind == "date":
        return norm_date(raw)
    return raw  # raw kind = 無変換（用件種別/概要/自由発話）
