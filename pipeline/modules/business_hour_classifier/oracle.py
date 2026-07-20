"""BusinessHour Classifier oracle — Python port of script.js for local testing.

JS 側の判定順序 (固定休 → 祝日 → 曜日定休 → 営業時間) を厳密に再現する。
本番では祝日リストを Brekeke Note (NoteUtils.read) から取得するが、ローカル
テストでは `holiday_note_content` (改行区切り yyyy-MM-dd 文字列) で同等入力を与える。
"""
from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass
from typing import Optional

DOW_KEYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
# datetime.weekday(): Mon=0..Sun=6


@dataclass
class Params:
    target_datetime: str = "now"
    reference_date: str = "now"  # 過去日判定の基準「今日」。本番は "now" (= 着信時刻)
    weekday_schedule: str = (
        "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-18:00,"
        "thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"
    )
    closed_dates: str = "12-29,12-30,12-31,01-02,01-03"
    national_holiday: str = "closed"  # closed | open
    holiday_note_name: str = "drjoy.holidays"  # 単一 Note に多年詰める設計 (2026-05-29 確定)


def _parse_target(target: str, now: _dt.datetime) -> _dt.datetime:
    if target == "now":
        return now
    s = target.strip().replace("T", " ")
    fmts = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d")
    for fmt in fmts:
        try:
            return _dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"unsupported target_datetime: {target}")


def _parse_schedule(schedule: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for entry in schedule.split(","):
        if "=" not in entry:
            continue
        k, v = entry.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _parse_holiday_note(content: Optional[str]) -> set[str]:
    """Brekeke Note 本文 (1 行 1 件 yyyy-MM-dd) を yyyy-MM-dd set に変換。"""
    if not content:
        return set()
    out: set[str] = set()
    for line in content.splitlines():
        s = line.strip()
        if s:
            out.add(s)
    return out


def classify(
    params: Params,
    now: Optional[_dt.datetime] = None,
    holiday_note_content: Optional[str] = None,
    holiday_set: Optional[set[str]] = None,
) -> str:
    """Return one of: 営業中 / 営業時間外 / 定休日 / 祝日 / 固定休 / ERROR.

    本番では祝日リストを Brekeke Note (NoteUtils.read) から取得する。テスト時は:
    - `holiday_note_content`: Note 本文を直接渡す (改行区切り yyyy-MM-dd)
    - `holiday_set`: 既存テスト互換のため受け入れる (set of yyyy-MM-dd)
    どちらも未指定なら空集合扱い (= 祝日チェックは fail-open でスキップ)。
    """
    if now is None:
        now = _dt.datetime.now()

    try:
        dt = _parse_target(params.target_datetime, now)
    except Exception:
        return "ERROR"

    # 基準「今日」を解決 (過去日ガード用)。本番は "now" = 着信時刻 (= now 引数)。
    # JS 側 (parseToCalendar(reference_date)) と同様、解析不能なら ERROR。
    try:
        ref = _parse_target(params.reference_date, now)
    except Exception:
        return "ERROR"

    # 0) 過去日ガード: 対象日が基準日より前 (日付単位) なら一律 営業時間外。
    #    予約受付特性上「過去その日時に営業していたか」は不要なため、曜日/祝日/固定休より
    #    手前で倒す。同じ「今日」内の過ぎた時刻枠は過去扱いしない (2026-06-04 確定)。
    if (dt.year, dt.month, dt.day) < (ref.year, ref.month, ref.day):
        return "営業時間外"

    mmdd = dt.strftime("%m-%d")
    yyyymmdd = dt.strftime("%Y-%m-%d")
    dow_key = DOW_KEYS[dt.weekday()]
    hhmm_num = dt.hour * 100 + dt.minute

    # 1) 固定休
    if params.closed_dates:
        for tok in params.closed_dates.split(","):
            if tok.strip() == mmdd:
                return "固定休"

    # 2) 祝日
    if params.national_holiday == "closed":
        if holiday_set is None:
            holiday_set = _parse_holiday_note(holiday_note_content)
        if yyyymmdd in holiday_set:
            return "祝日"

    # 3) 曜日定休 / 営業時間
    schedule = _parse_schedule(params.weekday_schedule)
    today_spec = schedule.get(dow_key)
    if today_spec is None or today_spec == "" or today_spec == "closed":
        return "定休日"
    m = re.match(r"^(\d{2}):(\d{2})-(\d{2}):(\d{2})$", today_spec)
    if not m:
        return "ERROR"
    open_num = int(m.group(1)) * 100 + int(m.group(2))
    close_num = int(m.group(3)) * 100 + int(m.group(4))
    # 時刻 00:00 (= DATE 型 context or yyyy-MM-dd リテラル) は「日付のみの判定」とみなし、
    # 営業時間外チェックをスキップして営業日扱い (= 営業中) を返す。
    if hhmm_num == 0:
        return "営業中"
    if open_num <= hhmm_num < close_num:
        return "営業中"
    return "営業時間外"
