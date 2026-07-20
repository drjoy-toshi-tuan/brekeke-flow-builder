# -*- coding: utf-8 -*-
"""dob_normalizer — Python オラクル（script.js parseDateByCode コアの独立再現）。

script.js の決定論コア（normalize* → parseDateByCode）と 1:1。
出力: classify(rawText) -> "YYYY-MM-DD HH:MM"(OK) / "INVALID" / "UNCERTAIN"

注意:
- script.js は Brekeke ランタイム（$runner/$ivr・復唱フロー・再入キャッシュ）も持つが、
  本オラクルは決定論コア（rawText → 正規化日付）だけを対象にする。復唱の優先順位 A/B/C/D は
  state 依存のグルーで P6/実機側の検証範囲。
- "現在" は JST 固定（script.js の _jstNow と対称。VN サーバ TZ ズレ回避）。
- JS の \\d は [0-9] のみ。Python re はデフォルト Unicode 数字を拾うため [0-9] を明示。
- Nashorn ↔ Python のバイト一致は別途ハーネス/実機で確認（本環境に node 無し）。
"""
import re
from datetime import datetime, timezone, timedelta

_JST = timezone(timedelta(hours=9))


def _jst_year():
    return datetime.now(_JST).year


def _jst_today():
    n = datetime.now(_JST)
    return datetime(n.year, n.month, n.day)


# 1.1 全角/漢数字 → 半角
_ZENKAKU = {"０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
            "５": "5", "６": "6", "７": "7", "８": "8", "９": "9"}
_KANJI1 = {"零": "0", "〇": "0", "一": "1", "二": "2", "三": "3", "四": "4",
           "五": "5", "六": "6", "七": "7", "八": "8", "九": "9"}
_KD = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def normalize_numbers(text):
    if not text:
        return ""
    r = text
    for k, v in _ZENKAKU.items():
        r = r.replace(k, v)

    def _tens(m):
        t = _KD.get(m.group(1), 1) if m.group(1) else 1
        o = _KD.get(m.group(2), 0) if m.group(2) else 0
        return str(t * 10 + o)
    r = re.sub(r"([一二三四五六七八九])?十([一二三四五六七八九])?", _tens, r)
    for k, v in _KANJI1.items():
        r = r.replace(k, v)
    return r


# 1.2 元号エイリアス
_ERA_ALIASES = [
    ("昭和", ["昭和", "しょうわ", "ショウワ", "唱和", "社長は", "少和", "名所", "正和", "うわー", "うわ", "今日は"]),
    ("平成", ["平成", "へいせい", "ヘイセイ", "平静", "閉成", "平清"]),
    ("令和", ["令和", "れいわ", "レイワ", "例は", "冷和", "例話"]),
    ("大正", ["大正", "たいしょう", "タイショウ", "対象", "大将", "大賞", "大勝", "対照"]),
    ("明治", ["明治", "めいじ", "メイジ", "命じ", "銘じ", "明示"]),
]


def normalize_era(text):
    if not text:
        return ""
    r = text
    for era, aliases in _ERA_ALIASES:
        for a in aliases:
            if a == era:
                continue
            r = r.replace(a, era)
    return r


# 1.4 「の」誤認補正（数字間のみ）
def normalize_no_particle(text):
    if not text:
        return text
    return re.sub(r"([0-9])\s*[Nn][Oo]\.?\s*([0-9])", r"\1の\2", text)


# 1.5 「じゅう」誤認補正
_JUU = r"(?:中|重|渋|縦|銃|自由|じゆう|ジユウ|じゅう|ジュウ)"
_ONES = [(r"(?:いち|一)", 1), (r"(?:に|二)", 2), (r"(?:さん|三)", 3),
         (r"(?:よ(?:う)?|し|四)", 4), (r"(?:ごう|号|ご|五)", 5), (r"(?:ろく|六)", 6),
         (r"(?:しち|なな|七)", 7), (r"(?:はち|八)", 8), (r"(?:きゅう|く|九)", 9)]


def normalize_juu(text):
    if not text:
        return text
    r = text.replace("重要", "14")
    for pat, n in _ONES:
        r = re.sub(_JUU + pat, str(10 + n), r)
    r = re.sub(_JUU, "10", r)
    r = r.replace("10号", "15").replace("20号", "25")
    return r


# 1.6 「野」→「の」
def normalize_ya(text):
    if not text:
        return text
    return re.sub(r"野(?=(?:中|重|渋|縦|銃|自由|じゆう|ジユウ|じゅう|ジュウ|[0-9]))", "の", text)


# 1.7 並び順補正（年があるときだけ 月日年 → 年月日）
def normalize_date_order(text):
    if not text:
        return text
    r = re.sub(r"([0-9]{1,2})月([0-9]{1,2})日\s*([0-9]{4})\s*年", r"\3年\1月\2日", text)
    r = re.sub(r"([0-9]{1,2})月([0-9]{1,2})日\s*(明治|大正|昭和|平成|令和)(元|[0-9]{1,2})\s*年",
               r"\3\4年\1月\2日", r)
    return r


def is_valid_date(y, m, d):
    if not y or not m or not d:
        return False
    if m < 1 or m > 12:
        return False
    if d < 1 or d > 31:
        return False
    dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    is_leap = (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)
    if m == 2 and is_leap:
        dim[1] = 29
    return d <= dim[m - 1]


def is_valid_era_year(era, eY):
    if era == "明治":
        return 1 <= eY <= 45
    if era == "大正":
        return 1 <= eY <= 15
    if era == "昭和":
        return 1 <= eY <= 64
    if era == "平成":
        return 1 <= eY <= 31
    if era == "令和":
        return 1 <= eY <= (_jst_year() - 2018)
    return False


def _is_age_over_120(db):
    if db == "INVALID":
        return False
    yp = db.split("-")[0]
    if len(yp) < 4:
        return True
    return (_jst_year() - int(yp)) > 120


def _is_future(db):
    if db == "INVALID":
        return False
    p = db.split(" ")[0].split("-")
    inp = datetime(int(p[0]), int(p[1]), int(p[2]))
    return inp > _jst_today()


def parse_date_by_code(raw):
    """(status, dbValue) を返す。status: OK/INVALID/UNCERTAIN。"""
    if not raw or raw.strip() == "":
        return ("UNCERTAIN", "")
    text = normalize_numbers(raw)
    text = normalize_era(text)
    text = normalize_no_particle(text)
    text = normalize_juu(text)
    text = normalize_ya(text)
    text = normalize_date_order(text)

    # DTMF 8桁 YYYYMMDD
    m = re.match(r"^([0-9]{4})([0-9]{2})([0-9]{2})$", text)
    if m:
        y, mo, da = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not is_valid_date(y, mo, da):
            return ("INVALID", "INVALID")
        db = "%d-%02d-%02d 00:00" % (y, mo, da)
        if _is_future(db) or _is_age_over_120(db):
            return ("INVALID", "INVALID")
        return ("OK", db)

    era_detected = bool(re.search(r"(明治|大正|昭和|平成|令和)", text))
    if era_detected:
        wm = re.search(
            r"(明治|大正|昭和|平成|令和)(?:の|\s)*(元|[0-9]{1,2})(?:年|の|、|-|\s)*"
            r"([0-9]{1,2})月(?:の|、|-|\s)*([0-9]{1,2})(?:日)?", text)
        if not wm or not wm.group(2) or not wm.group(3) or not wm.group(4):
            return ("UNCERTAIN", "")
        era = wm.group(1)
        eY = 1 if wm.group(2) == "元" else int(wm.group(2))
        wmo, wda = int(wm.group(3)), int(wm.group(4))
        if not is_valid_era_year(era, eY):
            return ("INVALID", "INVALID")
        sy = {"令和": 2018, "平成": 1988, "昭和": 1925, "大正": 1911, "明治": 1867}[era] + eY
        if not is_valid_date(sy, wmo, wda):
            return ("INVALID", "INVALID")
        db = "%d-%02d-%02d 00:00" % (sy, wmo, wda)
        if _is_future(db) or _is_age_over_120(db):
            return ("INVALID", "INVALID")
        return ("OK", db)

    # 元号なし: 西暦
    sep = r"(?:年|月|の|、|-|\s)+"
    s = re.search(r"([0-9]{1,4})" + sep + r"([0-9]{1,2})" + sep + r"([0-9]{1,2})(?:日)?", text)
    if not s or not s.group(1) or not s.group(2) or not s.group(3):
        has_hint = bool(re.search(r"[0-9]", text) or re.search(r"年|月|日", text))
        return ("UNCERTAIN", "") if has_hint else ("INVALID", "INVALID")
    yraw, smo, sda = int(s.group(1)), int(s.group(2)), int(s.group(3))
    sy = yraw
    if yraw < 100:
        sy = 1900 + yraw
    elif yraw < 1000:
        sy = 1900 + (yraw % 100)
    if not is_valid_date(sy, smo, sda):
        return ("INVALID", "INVALID")
    db = "%d-%02d-%02d 00:00" % (sy, smo, sda)
    if _is_future(db) or _is_age_over_120(db):
        return ("INVALID", "INVALID")
    return ("OK", db)


def classify(raw):
    status, db = parse_date_by_code(raw)
    if status == "OK":
        return db
    return status
