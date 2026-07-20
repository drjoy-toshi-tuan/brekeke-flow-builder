#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reservation_date_classifier — Python オラクル (期待値の独立実装 / script.js パリティ port)

検証対象: modules/reservation_date_classifier/script.js（予約日 抽出・正規化, 期間制限なし版）
出力契約:
  - 有効日付  → "YYYY-MM-DD 00:00"
  - 不明意図  → "不明"
  - 解釈不能  → "NO_RESULT"

JS(Nashorn/ES5.1) 固有挙動の再現:
  - new Date(y, monthIndex, day) のオーバーフロー桁送り（monthIndex/day は範囲外可・桁送りで正規化）
  - new Date(y, m-1, d) のラウンドトリップで日付妥当性を判定（2月30日 → 桁送り → 不一致 → NO_RESULT）
  - JS \\d は ASCII [0-9] のみ（全角数字は対象外）。\\s は全角空白(\\u3000)を含む
  - 相対日付の getDay() は 0=日..6=土

today はパラメタ化（既定 = システム日付）。相対日付・過去日補正は today 相対のため
受入テストでは today を固定して期待値を確定する。
"""

import re
from datetime import date, timedelta

# JS getDay(): 0=Sun..6=Sat
DAY_MAP = {"日": 0, "月": 1, "火": 2, "水": 3, "木": 4, "金": 5, "土": 6}


def js_getday(d):
    """Python weekday()(0=Mon..6=Sun) -> JS getDay()(0=Sun..6=Sat)"""
    return (d.weekday() + 1) % 7


def js_date(y, month_index, day):
    """JS new Date(y, monthIndex, day) を date で再現（monthIndex は 0-based・範囲外可）。"""
    # 月の正規化（Python の floor 除算は JS のオーバーフローと一致）
    yy = y + (month_index // 12)
    mm = month_index % 12  # 0-based, 0..11
    base = date(yy, mm + 1, 1)
    return base + timedelta(days=day - 1)


KANJI_NUM_LIST = [
    ("三十一", "31"), ("三十", "30"), ("二十九", "29"), ("二十八", "28"),
    ("二十七", "27"), ("二十六", "26"), ("二十五", "25"), ("二十四", "24"),
    ("二十三", "23"), ("二十二", "22"), ("二十一", "21"), ("二十", "20"),
    ("十九", "19"), ("十八", "18"), ("十七", "17"), ("十六", "16"),
    ("十五", "15"), ("十四", "14"), ("十三", "13"), ("十二", "12"),
    ("十一", "11"), ("十", "10"),
    ("九", "9"), ("八", "8"), ("七", "7"), ("六", "6"),
    ("五", "5"), ("四", "4"), ("三", "3"), ("二", "2"), ("一", "1"),
]

UNKNOWN_RE = re.compile(
    "わから[なね]い|わかりません|分から[なね]い|分かりません|わかんない|わかんな[いく]|"
    "不明|知らない|知りません|覚えていない|覚えてない|覚えておりません|覚えてません|"
    "忘れた|忘れました|忘れてしまいました|思い出せない|思い出せません|記憶にない|記憶がない|"
    "はっきりしない|定かでない|決まっていない|決まってない|未定|わからん|知らん|初旬|上旬|中旬|下旬",
    re.IGNORECASE,
)

# 事故①(2026-07-01): 具体日を pin しない曖昧な時期表現。**具体日付き（`6月3日ぐらい`→6/3）は
#   md/月日/日のみ 経路が先に解決するため、この RE は全解決失敗後にのみ照合する（過剰発火なし）**。
#   既存 上旬/中旬/下旬→不明（UNKNOWN_RE・早期）と統一し、NO_RESULT ループを 不明 誘導へ。
VAGUE_PERIOD_RE = re.compile(
    "初め頃|初めごろ|始め頃|始めごろ|中頃|なかごろ|半ば|末頃|末ごろ|月初め?|"
    "あたり|ぐらい|くらい|頃|ごろ|どこか|どの辺|その辺|その頃",
    re.IGNORECASE,
)


class _Out:
    """script.js の output() に相当（最初に確定した値を保持して返す）。"""
    __slots__ = ("value",)

    def __init__(self):
        self.value = None

    def __call__(self, v):
        if self.value is None:
            self.value = v


def _format_date(d):
    return "%04d-%02d-%02d 00:00" % (d.year, d.month, d.day)


def _run_correction(y, m, d, today):
    m_table = {1: [7], 2: [4], 4: [2, 7], 7: [1, 4]}
    d_table = {
        1: [7], 4: [7], 7: [1, 4],
        11: [17], 14: [17], 17: [11, 14],
        21: [27], 24: [27], 27: [21, 24],
    }

    def is_ok(dt, target_m, target_d):
        return dt.month == target_m and dt.day == target_d and dt >= today

    candidates = []
    if m in m_table:
        for cand_m in m_table[m]:
            test_m = js_date(y, cand_m - 1, d)
            if is_ok(test_m, cand_m, d):
                candidates.append(test_m)
    if d in d_table:
        for cand_d in d_table[d]:
            test_d = js_date(y, m - 1, cand_d)
            if is_ok(test_d, m, cand_d):
                candidates.append(test_d)
    if not candidates:
        return None
    closest = candidates[0]
    min_diff = (closest - today).days
    for c in candidates[1:]:
        diff = (c - today).days
        if diff < min_diff:
            min_diff = diff
            closest = c
    return closest


def _validate_and_output(y, m, d, is_dtmf, today, out):
    # new Date(y, m-1, d) のラウンドトリップ妥当性
    check = js_date(y, m - 1, d)
    if check.year != y or check.month != m or check.day != d:
        out("NO_RESULT")
        return
    if check >= today:
        out(_format_date(check))
    else:
        if is_dtmf:
            out("NO_RESULT")
        else:
            next_year = js_date(y + 1, m - 1, d)
            if next_year.month == m and next_year.day == d:
                out(_format_date(next_year))
            else:
                corrected = _run_correction(y, m, d, today)
                if corrected:
                    out(_format_date(corrected))
                else:
                    out("NO_RESULT")


def classify(raw_input, today=None):
    """予約日入力を分類して文字列を返す。today は date（既定=システム日付）。"""
    if today is None:
        today = date.today()
    today_year = today.year

    # --- 1. 入力取得: 全空白除去（JS \s は全角空白含む） ---
    if raw_input is None:
        raw = ""
    else:
        raw = re.sub(r"\s+", "", str(raw_input))

    out = _Out()

    # --- 3. メインロジック ---
    if not raw or raw == "null" or raw == "undefined":
        out("NO_RESULT")
        return out.value

    if UNKNOWN_RE.search(raw):
        out("不明")
        return out.value

    # DTMF（ASCII 数字のみ）
    if re.fullmatch(r"[0-9]+", raw):
        if len(raw) == 8:
            d_y = int(raw[0:4]); d_m = int(raw[4:6]); d_d = int(raw[6:8])
        elif len(raw) == 4:
            d_m = int(raw[0:2]); d_d = int(raw[2:4])
            this_year = js_date(today_year, d_m - 1, d_d)
            d_y = today_year + 1 if this_year < today else today_year
        else:
            out("NO_RESULT")
            return out.value
        _validate_and_output(d_y, d_m, d_d, True, today, out)
        return out.value

    processed = raw
    # 時刻除去
    processed = re.sub(r"[0-9]{1,2}時([0-9]{1,2}分)?", "", processed)
    # 漢数字変換（月|日|年 の直前のみ）
    for key, val in KANJI_NUM_LIST:
        processed = re.sub(key + r"(?=月|日|年)", val, processed)
    # 表記ゆれ正規化
    processed = re.sub(r"([0-9]{1,2})月no([0-9]{1,2})日", r"\1月\2日", processed, flags=re.IGNORECASE)
    processed = re.sub(r"([0-9]{1,2})月no([0-9]{1,2})(?![0-9])", r"\1月\2日", processed, flags=re.IGNORECASE)
    processed = re.sub(r"通知", "1日", processed)
    processed = re.sub(r"発火", "20日", processed)
    processed = re.sub(r"([0-9]{1,2})月[のをにはが]([0-9]{1,2})日", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})月[のをにはが]([0-9]{1,2})(?![0-9])", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})月\s+([0-9]{1,2})日", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})月\s+([0-9]{1,2})(?![0-9])", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})の([0-9]{1,2})日", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})の([0-9]{1,2})", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})/([0-9]{1,2})", r"\1月\2日", processed)
    processed = re.sub(r"([0-9]{1,2})-([0-9]{1,2})(?![0-9])", r"\1月\2日", processed)
    # FIX(engine v2 / 2026-07-01): has_月 の取りこぼし回収（scorecard date v1.1・has_月 fixable ~5.6%P）
    #   Rule A: 数字+十（STT が「さんじゅう」→ `3十` と混在レンダリング）→ ×10 に正規化。
    #           `3十`→`30` / `2十`→`20`。Rule B の前に置く（`1月3十`→`1月30`→`1月30日`）。
    #           (?![0-9]) で後続数字を除外（漢数字リストで純漢数字 二十/三十 は既に変換済み）。
    processed = re.sub(r"([0-9])十(?![0-9])", lambda mo: mo.group(1) + "0", processed)
    #   Rule B: 「N月M」（月直後に日の数字・末尾に日なし）→ 日を補う。末尾切れ/句点/です等で
    #           日が落ちた発話（`1月27`/`5月27。`/`5月7のか`）を回収。(?![0-9日年]) で
    #           既に日がある場合の二重付与・桁溢れ（`1月100`）・日の後ろに年が続く化け
    #           （`1月20年`= 実日付は YYYY年M月D日 の順ゆえ M月D年 は常にゴミ）を防ぐ。
    #           GUARD(grader 2026-07-01): 完成した `M月D日` が既に文中にある場合は Rule B を
    #           発火させない。言い直し（`3月5ではなく4月10日`=「3月5 じゃなく 4月10日」）で
    #           破棄された第1候補に日を補うと、先頭一致抽出が破棄側(3月5)を予約してしまう
    #           安全クリティカルな誤被覆(M)を防ぐ。完成日があるならそれを md 抽出に任せる。
    if not re.search(r"[0-9]{1,2}月[0-9]{1,2}日", processed):
        processed = re.sub(r"([0-9]{1,2})月([0-9]{1,2})(?![0-9日年])", r"\1月\2日", processed)

    # 月末処理
    if "月末" in processed:
        if "今月末" in processed:
            eom = js_date(today_year, today.month - 1 + 1, 0)  # today.getMonth()+1, day0
            processed = re.sub(r"今月末", "%d月%d日" % (today.month, eom.day), processed)
        elif "来月末" in processed:
            eonm = js_date(today_year, today.month - 1 + 2, 0)  # today.getMonth()+2, day0
            processed = re.sub(r"来月末", "%d月%d日" % (eonm.month, eonm.day), processed)
        else:
            def _eom_repl(mobj):
                mo = int(mobj.group(1))
                eom2 = js_date(today_year, mo, 0)
                return "%d月%d日" % (mo, eom2.day)
            processed = re.sub(r"([0-9]{1,2})月末", _eom_repl, processed)

    # 相対日付
    target = None
    gd = js_getday(today)
    if ("今日" in processed) or ("本日" in processed):
        target = today + timedelta(days=0)
    elif re.search(r"明々後日|しあさって", processed):
        # FIX(2026-06-12): しあさって(+3) を あさって(+2) より先に判定
        target = today + timedelta(days=3)
    elif re.search(r"明後日|あさって|あさて", processed):
        target = today + timedelta(days=2)
    elif re.search(r"明日|あした|みょうにち", processed):
        target = today + timedelta(days=1)
    else:
        m_wk = re.search(r"来週の?(月|火|水|木|金|土|日)曜日?", processed)
        m_tw = re.search(r"今週の?(月|火|水|木|金|土|日)曜日?", processed)
        m_im = re.search(r"今月の?([0-9]{1,2})日?", processed)
        m_nm = re.search(r"来月の?([0-9]{1,2})日", processed)
        m_af = re.search(r"([0-9]+)日後", processed)
        m_dow = re.search(r"(月|火|水|木|金|土|日)曜日?", processed)
        if m_wk:
            # FIX(2026-06-12): 暦週・月曜始まり。今週月曜 + 7 + 目標曜日(月曜起点オフセット)
            monday_off = (gd + 6) % 7
            this_monday = today + timedelta(days=-monday_off)
            target = this_monday + timedelta(days=7 + (DAY_MAP[m_wk.group(1)] + 6) % 7)
        elif m_tw:
            # FIX(2026-06-12): 暦週・月曜始まり。今週の月曜 + 目標曜日(月曜起点)。過去でも今週の実日。
            monday_off = (gd + 6) % 7
            this_monday = today + timedelta(days=-monday_off)
            target = this_monday + timedelta(days=(DAY_MAP[m_tw.group(1)] + 6) % 7)
        elif m_im:
            target = js_date(today.year, today.month - 1, int(m_im.group(1)))
        elif m_nm:
            target = js_date(today.year, today.month - 1 + 1, int(m_nm.group(1)))
        elif m_af:
            target = today + timedelta(days=int(m_af.group(1)))
        elif m_dow and not re.search(r"[0-9]{1,2}日", processed):
            diff2 = (DAY_MAP[m_dow.group(1)] - gd + 7) % 7
            target = today + timedelta(days=(7 if diff2 == 0 else diff2))

    if target is not None:
        # FIX(2026-06-12): 明示的な相対表現は名指しの日付をそのまま採用（過去でも翌年送りしない）
        out(_format_date(target))
        return out.value

    # 元号
    t_y = today_year
    g = re.search(r"(令和|平成|昭和|大正)([0-9]+|元)年", processed)
    if g:
        gv = 1 if g.group(2) == "元" else int(g.group(2))
        era = g.group(1)
        if era == "令和":
            t_y = gv + 2018
        elif era == "平成":
            t_y = gv + 1988
        elif era == "昭和":
            t_y = gv + 1925
        elif era == "大正":
            t_y = gv + 1911

    # 西暦年
    ym = re.search(r"([0-9]{4})年", processed)
    if ym:
        t_y = int(ym.group(1))

    # 日付抽出（月あり）
    md = re.search(r"([0-9]{1,2})月([0-9]{1,2})日", processed)
    if md:
        t_m = int(md.group(1)); t_d = int(md.group(2))
        _validate_and_output(t_y, t_m, t_d, False, today, out)
        return out.value

    # 月のみ + 日のみ が別々にある場合
    m_only = re.search(r"([0-9]{1,2})月", processed)
    d_only = re.search(r"([0-9]{1,2})日", processed)
    if m_only and d_only:
        t_m = int(m_only.group(1)); t_d = int(d_only.group(1))
        _validate_and_output(t_y, t_m, t_d, False, today, out)
        return out.value

    # 日のみ
    if d_only and not m_only:
        only_d = int(d_only.group(1))
        if 1 <= only_d <= 31:
            temp = js_date(today.year, today.month - 1, only_d)
            if temp < today:
                temp = js_date(today.year, today.month - 1 + 1, only_d)
            _validate_and_output(temp.year, temp.month, temp.day, False, today, out)
        else:
            out("NO_RESULT")
        return out.value

    # 事故①: 具体日が解決できなかった曖昧な時期表現は NO_RESULT でループさせず 不明 へ。
    #   ここは md / 月日 / 日のみ の全解決失敗後ゆえ、`6月3日ぐらい` 等の具体日付き修飾は
    #   既に上で解決済み＝ここには到達しない（過剰発火なし）。`5月ぐらい`/`5月あたり`/
    #   `5月のどこか`/`5月初め頃` 等の pin できない発話のみ 不明 に倒す。
    if VAGUE_PERIOD_RE.search(processed):
        out("不明")
        return out.value

    out("NO_RESULT")
    return out.value


if __name__ == "__main__":
    import sys
    t = date.today()
    for arg in sys.argv[1:]:
        print("%s -> %s" % (arg, classify(arg, t)))
