#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用件抽出 決定論パーサ オラクル v2（商談デモ フリー発話受付・OpenAI不使用）。

自由発話の STT テキストを直接解析し、用件種別＋各スロット値＋取得有無フラグ＋復唱用の用件概要文へ
決定論的に分解する Python 参照実装。LLM 不使用。Brekeke テンプレート版（script_templates/inquiry_extractor.js）と一致させる。
仕様: REQUIREMENTS.md（同ディレクトリ）。ベストエフォート抽出（高精度優先・抜けは下流で回収）。
"""
import re

OUT_SEP = "‖"        # ‖ canonical の項目区切り
FLAG_SEP = "@"            # value@flag

SLOTS = ["診療科", "予約希望日", "予約日時", "氏名", "連絡先", "生年月日", "診察券番号"]

# 用件種別キーワード（評価順＝precision優先）
KW_CANCEL = ["取消", "取り消し", "キャンセル", "やめ", "中止"]
KW_CHANGE = ["変更", "変えたい", "ずらし", "ずらす", "振替", "振り替え", "日にちを変", "時間を変", "予定を変"]
KW_NEW = ["新規", "初めて", "はじめて", "予約", "受診したい", "診てもらい", "みてもらい", "診ていただき", "かかりたい"]

# 診療科辞書（canonical, [一致キー]）— department_classifier と整合＋デモ向け一般語(内科/外科)を追加。最長一致。
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
    # デモ向け一般語（official canonical ではないが頻出）
    ("内科", ["内科"]),
    ("外科", ["外科"]),
]

ERAS = ["昭和", "平成", "令和", "大正"]
RELATIVE_DATES = ["再来週", "来週", "今週", "今度", "明々後日", "しあさって", "明後日", "あさって",
                  "明日", "あした", "本日", "今日", "きょう"]
HONORIFICS = ["さん", "様", "さま", "君", "ちゃん"]
NAME_PREFIX = ["私は", "わたしは", "名前は", "なまえは", "私、", "わたし、"]
NAME_SUFFIX = ["と申します", "ともうします", "と言います", "といいます", "と申し上げます"]
NAME_BOUNDARY = ["。", "、", " ", "　", "は", "が", "を", "の", "\t", "\n", "\r"]


def _z2h_digits(s):
    out = []
    for ch in s:
        o = ord(ch)
        if 0xFF10 <= o <= 0xFF19:
            out.append(chr(o - 0xFEE0))
        else:
            out.append(ch)
    return "".join(out)


def normalize(raw):
    if raw is None:
        return ""
    if isinstance(raw, dict):
        raw = raw.get("text", "") or ""
    s = str(raw)
    s = _z2h_digits(s)
    return s.strip()


def _contains_any(s, kws):
    for k in kws:
        if k in s:
            return True
    return False


def decide_intent(s):
    if _contains_any(s, KW_CANCEL):
        return "キャンセル"
    if _contains_any(s, KW_CHANGE):
        return "変更"
    if _contains_any(s, KW_NEW):
        return "新規"
    return "問い合わせ"


def extract_department(s):
    keys = []
    for canon, ks in DEPARTMENTS:
        for k in ks:
            keys.append((k, canon))
    keys.sort(key=lambda kv: -len(kv[0]))  # 最長一致
    for k, canon in keys:
        if k in s:
            return canon
    return ""


_SEPARATORS = ["-", "－", "ー", "‐", "–", "—", "―", " ", "　", "\t", "\r", "\n"]


def _strip_separators(s):
    for sep in _SEPARATORS:
        s = s.replace(sep, "")
    return s


def extract_phone(s):
    digits_only = _strip_separators(s)
    m = re.search(r"0\d{9,10}", digits_only)
    return m.group(0) if m else ""


def extract_birthday(s):
    # 元号付き / 西暦4桁 を含む 年月日
    era_alt = "|".join(ERAS)
    m = re.search(r"(?:" + era_alt + r")\s*\d{1,2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", s)
    if m:
        return m.group(0)
    m = re.search(r"(?:19|20)\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", s)
    if m:
        return m.group(0)
    return ""


def extract_booking_date(s, birthday):
    # 生年月日のスパンを除外
    work = s
    if birthday:
        work = work.replace(birthday, "", 1)
    parts = []
    # 相対日付（最長優先）
    for rd in RELATIVE_DATES:
        if rd in work:
            parts.append((work.index(rd), rd))
            work = work.replace(rd, " " * len(rd), 1)
    # ◯月◯日（年なし）
    for m in re.finditer(r"\d{1,2}\s*月\s*\d{1,2}\s*日", work):
        parts.append((m.start(), m.group(0)))
    # 曜日
    for m in re.finditer(r"[月火水木金土日]曜日?", work):
        parts.append((m.start(), m.group(0)))
    # 時刻
    for m in re.finditer(r"(?:午前|午後)?\s*\d{1,2}\s*時(?:\s*\d{1,2}\s*分)?(?:半)?", work):
        parts.append((m.start(), m.group(0)))
    if not parts:
        return ""
    parts.sort(key=lambda p: p[0])
    return "".join(p[1] for p in parts).strip()


def _clean_name(name):
    name = name.strip()
    for b in ["。", "、", " ", "　", "\t", "\n", "\r"]:
        name = name.replace(b, "")
    # 敬称除去（末尾）
    changed = True
    while changed:
        changed = False
        for h in HONORIFICS:
            if name.endswith(h):
                name = name[: -len(h)]
                changed = True
    if "先生" in name:
        return ""  # 第三者（医師名等）は対象外
    if len(name) > 10:
        return ""
    return name


def extract_name(s):
    # 接尾マーカー（◯◯と申します）優先
    for suf in NAME_SUFFIX:
        idx = s.find(suf)
        if idx > 0:
            head = s[:idx]
            cut = -1
            for b in NAME_BOUNDARY:
                p = head.rfind(b)
                if p > cut:
                    cut = p
            cand = head[cut + 1:] if cut >= 0 else head
            nm = _clean_name(cand)
            if nm:
                return nm
    # 接頭マーカー（私は◯◯／名前は◯◯）
    for pre in NAME_PREFIX:
        idx = s.find(pre)
        if idx >= 0:
            rest = s[idx + len(pre):]
            cut = len(rest)
            for stop in ["です", "と申", "と言", "。", "、", " ", "　"]:
                p = rest.find(stop)
                if p >= 0 and p < cut:
                    cut = p
            cand = rest[:cut]
            nm = _clean_name(cand)
            if nm:
                return nm
    return ""


def extract_card_number(s, phone, birthday=""):
    # 発話は順不同なので「先頭の数字列」では生年月日の年などを誤取得する。
    # 数字列を全部拾ってから確からしさで選ぶ:
    #   1) 電話番号・生年月日の年（西暦4桁）は診察券番号ではないので候補から外す
    #   2) 「診察券」ラベル以降で最も近い数字列を最有力とする（ラベル近接＝確からしさ）
    #   3) ラベル以降に無ければ、残った最初の数字列にフォールバック
    if "診察券" not in s:
        return ""
    digits_norm = _strip_separators(s)
    if phone:
        digits_norm = digits_norm.replace(phone, " ", 1)  # 電話の桁列を分離（空白へ）
    b_year = ""
    if birthday:
        ym = re.search(r"(?:19|20)\d{2}", _strip_separators(birthday))
        if ym:
            b_year = ym.group(0)  # 生年月日の年（西暦4桁）
    label_idx = digits_norm.find("診察券")
    cands = []  # (index, digits)
    for m in re.finditer(r"\d{3,10}", digits_norm):
        if b_year and m.group(0) == b_year:
            continue  # 生年月日の年は診察券番号ではない
        cands.append((m.start(), m.group(0)))
    if not cands:
        return ""
    for idx, digits in cands:
        if label_idx >= 0 and idx >= label_idx:
            return digits  # ラベル以降で最初＝最も確からしい
    return cands[0][1]  # fallback: 残った最初の数字列


def _summary(intent, vals):
    def joined(items):
        return "、".join([x for x in items if x])
    if intent == "新規":
        body = joined([vals["診療科"], vals["予約希望日"]])
        return "新規のご予約、" + body + "、でお間違いないですか？" if body else "新規のご予約、でお間違いないですか？"
    if intent == "変更":
        body = joined([vals["予約日時"]])
        return "ご予約の変更、" + body + "、でお間違いないですか？" if body else "ご予約の変更、でお間違いないですか？"
    if intent == "キャンセル":
        body = joined([vals["予約日時"]])
        return "ご予約のキャンセル、" + body + "、でお間違いないですか？" if body else "ご予約のキャンセル、でお間違いないですか？"
    return "お問い合わせ、でお間違いないですか？"


def parse(raw):
    s = normalize(raw)
    intent = decide_intent(s)
    dept = extract_department(s)
    phone = extract_phone(s)
    bday = extract_birthday(s)
    bdate = extract_booking_date(s, bday)
    card = extract_card_number(s, phone, bday)

    予約希望日 = bdate if intent == "新規" else ""
    予約日時 = bdate if intent in ("変更", "キャンセル") else ""

    vals = {
        "診療科": dept, "予約希望日": 予約希望日, "予約日時": 予約日時,
        "氏名": "", "連絡先": phone, "生年月日": bday, "診察券番号": card,
    }
    flags = {k: ("取得済" if vals[k] != "" else "未取得") for k in SLOTS}
    summary = _summary(intent, vals)
    return {"用件種別": intent, "values": vals, "flags": flags, "用件概要": summary}


def serialize(result):
    parts = [result["用件種別"]]
    for k in SLOTS:
        parts.append(result["values"][k] + FLAG_SEP + result["flags"][k])
    parts.append("SUMMARY:" + result["用件概要"])
    return OUT_SEP.join(parts)


def run(raw):
    return serialize(parse(raw))


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    samples = [
        "来週の月曜日に内科を予約したいです。山田太郎と申します。電話番号は09012345678です。",
        "予約を変更したいんですけど、6月20日の10時の予約です。",
        "駐車場はありますか？",
    ]
    for x in samples:
        print(run(x))
