#!/usr/bin/env python3
"""
diversify_master_cases.py — マスターケース CSV のフィラー値多様化ツール

master_test_patterns_*.csv では「テスト対象外の聴取項目（フィラー）」が
定型値（試験太郎です / 0101010です / 090-0000-0001です / 昭和55年1月1日です 等）で
埋められており、gen_p7_from_master.py の diversity_check() が大量の重複警告を出す。
本ツールは既知のフィラー (入力, 期待) ペアのみを、ケースごとに異なる値へ
決定論的に置換する（意図的に作り込まれた値・プレースホルダー・空欄は触らない）。

置換対象は 2 系統:
1. 個人情報 4 列（患者名/生年月日/診察券番号/連絡先番号）: ファイル全体で 2 回以上
   出現する (入力, 期待) ペアを自動的にフィラーとみなし全出現を置換する。
   個人情報を複数ケースで共有する意図的なテスト軸は存在しないため安全。
   ガード: かな読み・漢数字などの STT 特殊表記ペア（数字/漢字を含まない入力）は
   意図的なケースとみなして保護する。スタイルは元値から検出して保存する
   （DTMF の素の数字は素の数字のまま、ハイフン区切りはハイフン区切りのまま）。
2. 言い回し列（用件/通院歴/診療科/最後の問い合わせ 等）: FILLER_PAIRS に列挙した
   完全一致ペアのみ置換。期待値の分類クラスは変えない（用件 {YOYAKU} は {YOYAKU} のまま、
   言い回しだけ多様化）。診療科のみ、コーパスに既出の一般的な診療科の中でローテーション。

決定論: md5(case_id + column) を開始位置に、列内で未使用の値を線形探索で割当。
乱数・時刻を使わないため再実行しても同じ結果になる。

使い方:
  python3 tools/diversify_master_cases.py --check  docs/testcase_master/master_test_patterns_v3.csv
  python3 tools/diversify_master_cases.py --write  docs/testcase_master/master_test_patterns_v3.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from collections import Counter

# ─── 汎用部品 ───────────────────────────────────────────────────

_PREFIX = ["", "あの、", "すみません、", "えっと、", "もしもし、", "お世話になります、"]
_PREFIX_L = _PREFIX + ["恐れ入りますが、", "お忙しいところすみません、"]

_HAS_DIGIT = re.compile(r"[0-9０-９]")
_HAS_KANJI = re.compile(r"[一-鿿]")


def _phrases(bodies: list[str], expected: str,
             prefixes: list[str] | None = None,
             suffixes: list[str] | None = None) -> list[tuple[str, str]]:
    """言い回しプール。期待値は固定（分類クラスを変えない）。"""
    pref = prefixes if prefixes is not None else [""]
    suf = suffixes if suffixes is not None else [""]
    return [(px + b + sx, expected) for b in bodies for px in pref for sx in suf]


# ─── 個人情報 4 列のスタイル別プール ─────────────────────────────

_SURNAMES = ["青木", "石田", "上野", "遠藤", "岡本", "加藤", "木村", "小林", "斉藤", "柴田",
             "杉山", "関口", "高橋", "田村", "中島", "西村", "野口", "橋本", "福田", "堀田",
             "前田", "三浦", "村上", "森田", "矢野", "横山", "吉田", "和田"]
_GIVEN = ["一郎", "健太", "翔平", "大輔", "直樹", "誠", "浩二", "隆",
          "花子", "美咲", "由美", "恵子", "真理", "彩", "沙織", "陽子"]
_NAME_STYLES = ["{n}です", "{n}と申します", "名前は{n}です", "{n}といいます"]


def _pool_name(style: str) -> list[tuple[str, str]]:
    pool = []
    for i, s in enumerate(_SURNAMES):
        for j, g in enumerate(_GIVEN):
            name = s + g
            if style == "bare":
                pool.append((name, name))
            else:
                pool.append((_NAME_STYLES[(i + j) % len(_NAME_STYLES)].format(n=name), name))
    return pool


def _dob_parts(i: int) -> tuple[int, int, int, str]:
    y = 1930 + (i * 7) % 75          # 1930-2004
    m = 1 + (i * 5) % 12
    d = 1 + (i * 11) % 28
    era = f"昭和{y - 1925}年" if y <= 1988 else f"平成{y - 1988}年"
    return y, m, d, era


def _pool_dob(style: str) -> list[tuple[str, str]]:
    pool = []
    for i in range(400):
        y, m, d, era = _dob_parts(i)
        iso = f"{y:04d}-{m:02d}-{d:02d}"
        if style == "bare":
            pool.append((f"{y:04d}{m:02d}{d:02d}", iso))      # DTMF 8桁
        else:
            styles = [
                f"{era}{m}月{d}日です",
                f"{y}年{m}月{d}日です",
                f"{era}の{m}月{d}日生まれです",
                f"{y}年{m}月{d}日生まれです",
            ]
            pool.append((styles[i % 4], iso))
    return pool


def _pool_card(style: str) -> list[tuple[str, str]]:
    pool = []
    for i in range(300):
        digits = f"{(202020 + i * 13579) % 10000000:07d}"
        if style == "bare":
            pool.append((digits, digits))
        else:
            styles = [f"{digits}です", f"{digits[:3]}の{digits[3:]}です"]
            pool.append((styles[i % 2], digits))
    return pool


def _pool_phone(style: str) -> list[tuple[str, str]]:
    """安全なダミー電話番号（中間 0000 帯を維持し実在番号を避ける）。"""
    pool = []
    prefixes = ["090", "080", "070"]
    for i in range(300):
        p = prefixes[i % 3]
        last = f"{(i * 7 + 2) % 9999 + 1:04d}"
        digits = f"{p}0000{last}"
        if style == "bare":
            pool.append((digits, digits))
        elif style == "hyphen":
            pool.append((f"{p}-0000-{last}", digits))
        else:
            styles = [f"{p}-0000-{last}です", f"{p}の0000の{last}です"]
            pool.append((styles[i % 2], digits))
    return pool


def _detect_style(col: str, value: str) -> str | None:
    """元値からスタイルを判定。None は保護（置換しない）。"""
    if col == "入力_患者名":
        if not _HAS_KANJI.search(value):
            return None                      # かな読み等の STT 特殊表記は保護
        return "bare" if re.fullmatch(r"[一-鿿]+", value) else "polite"
    if not _HAS_DIGIT.search(value):
        return None                          # 漢数字・かな読みは保護
    if col == "入力_生年月日":
        return "bare" if re.fullmatch(r"[0-9]{8}", value) else "polite"
    if col in ("入力_診察券番号", "入力_連絡先番号"):
        if re.fullmatch(r"[0-9]+", value):
            return "bare"
        if col == "入力_連絡先番号" and re.fullmatch(r"[0-9\-]+", value):
            return "hyphen"
        return "polite"
    return "polite"


_PERSONAL_POOLS = {
    ("入力_患者名", "bare"):     lambda: _pool_name("bare"),
    ("入力_患者名", "polite"):   lambda: _pool_name("polite"),
    ("入力_生年月日", "bare"):   lambda: _pool_dob("bare"),
    ("入力_生年月日", "polite"): lambda: _pool_dob("polite"),
    ("入力_診察券番号", "bare"):   lambda: _pool_card("bare"),
    ("入力_診察券番号", "polite"): lambda: _pool_card("polite"),
    ("入力_連絡先番号", "bare"):   lambda: _pool_phone("bare"),
    ("入力_連絡先番号", "hyphen"): lambda: _pool_phone("hyphen"),
    ("入力_連絡先番号", "polite"): lambda: _pool_phone("polite"),
}

PERSONAL_COLS = ("入力_患者名", "入力_生年月日", "入力_診察券番号", "入力_連絡先番号")


# ─── 言い回し列の静的フィラーペア ────────────────────────────────

_DEPTS = ["内科", "外科", "整形外科", "皮膚科", "眼科", "耳鼻咽喉科"]
# 素の科名プール用の拡張リスト。実ログ由来ケースの科名シングルトンが used に多数
# 事前登録されるため、プールが枯渇しないよう十分広く取る（枯渇すると least_used
# フォールバックが元値と衝突し得る）。
_DEPTS_WIDE = _DEPTS + ["泌尿器科", "婦人科", "小児科", "脳神経外科", "循環器内科",
                        "消化器内科", "呼吸器内科", "精神科", "形成外科", "糖尿病内科",
                        "腎臓内科", "血液内科", "乳腺外科", "心臓血管外科", "放射線科",
                        "リハビリテーション科"]
_DEPT_STYLES = ["{d}です", "{d}でお願いします", "{d}をお願いします",
                "{d}なんですけど", "{d}を受診したいです", "{d}希望です"]


def _pool_dept() -> list[tuple[str, str]]:
    """診療科はコーパス既出の一般科の中でローテーション（期待値も対で変える）。"""
    pool = []
    for k, d in enumerate(_DEPTS):
        for t, style in enumerate(_DEPT_STYLES):
            for p, px in enumerate(["", "あの、", "すみません、", "えっと、"]):
                pool.append((px + style.format(d=d), d))
    return pool


def _pool_saishin() -> list[tuple[str, str]]:
    bodies = ["再診です", "通院しています", "かかりつけです", "以前から通っています",
              "何度か受診しています", "定期的に通院しています", "前にもかかったことがあります",
              "毎月通っています", "先月も受診しました", "ずっとお世話になっています"]
    bodies += [f"{n}年前から通っています" for n in range(2, 16)]
    bodies += [f"{n}ヶ月に一度通院しています" for n in range(1, 7)]
    return _phrases(bodies, "再診", _PREFIX)


def _pool_nashi() -> list[tuple[str, str]]:
    bodies = ["ないです", "大丈夫です", "特にないです", "ありません", "特にありません",
              "以上です", "結構です", "他にはないです", "質問はないです",
              "特に聞きたいことはないです", "もうないです", "いえ大丈夫です"]
    return _phrases(bodies, "なし", ["", "いえ、", "いいえ、", "あ、", "えっと、", "はい、"],
                    ["", "、ありがとうございます", "、お願いします"])


def _pool_ryoushou() -> list[tuple[str, str]]:
    return _phrases(
        ["はい", "はいわかりました", "はい大丈夫です", "わかりました", "承知しました",
         "はい承知しました", "はい問題ないです"], "了承", _PREFIX)


def build_filler_table() -> dict[tuple[str, str, str], list[tuple[str, str]]]:
    dept = _pool_dept()
    nashi = _pool_nashi()
    ryoushou = _pool_ryoushou()

    return {
        # 用件（期待はプレースホルダーのまま固定・言い回しは明確に予約系のみ）
        ("入力_用件", "予約です", "{YOYAKU}"): _phrases(
            ["予約です", "予約をお願いします", "予約したいんですけど", "予約を取りたいのですが",
             "診察の予約をお願いします", "予約の件でお電話しました", "新しく予約をお願いしたいです",
             "予約希望です", "予約をしたくてお電話しました", "受診の予約を取りたいです",
             "来院の予約をお願いします", "診察を予約したいです", "予約を入れたいのですが",
             "予約をお願いしたいのですが", "予約を一件お願いします"],
            "{YOYAKU}", _PREFIX_L),
        ("入力_用件", "健診の予約です", "{K_YOYAKU}"): _phrases(
            ["健診の予約です", "健康診断の予約をお願いします", "健診を予約したいのですが",
             "健康診断を受けたいのですが", "健診の予約をお願いしたいです"],
            "{K_YOYAKU}", _PREFIX),
        ("入力_用件", "予約の変更です", "{HENKOU}"): _phrases(
            ["予約の変更です", "予約を変更したいのですが", "変更をお願いします",
             "予約日を変更したいです", "日程を変更してもらえますか"],
            "{HENKOU}", _PREFIX),
        ("入力_用件", "検査の依頼です", "{R_KENSA}"): _phrases(
            ["検査の依頼です", "検査をお願いしたいのですが", "検査の予約をお願いします", "検査依頼です"],
            "{R_KENSA}", _PREFIX),
        # 通院歴
        ("入力_通院歴", "再診です", "再診"): _pool_saishin(),
        ("入力_通院歴", "初めてです", "初診"): _phrases(
            ["初めてです", "初診です", "初めてかかります", "今回が初めてです",
             "初めて受診します", "初めてお電話しました", "初めての利用です"],
            "初診", _PREFIX),
        # 診療科（一般科ローテーション）
        ("入力_診療科", "内科です", "内科"): dept,
        ("入力_診療科", "整形外科です", "整形外科"): dept,
        # 最後の問い合わせ
        ("入力_最後の問い合わせ", "ないです", "なし"): nashi,
        ("入力_最後の問い合わせ", "大丈夫です", "なし"): nashi,
        # 受診希望時期
        ("入力_受診希望時期", "9月ごろで", "9月頃"): [
            (fmt.format(m=m), f"{m}月頃")
            for m in range(1, 13)
            for fmt in ("{m}月ごろで", "{m}月頃でお願いします", "{m}月あたりで考えています")
        ],
        # 現在の予約日（7月固定・日のみ変える → 希望日 8月との前後関係を維持）
        ("入力_現在の予約日", "7月の20日です", "07-20"): [
            (fmt.format(d=d), f"07-{d:02d}") for d in range(1, 29)
            for fmt in ("7月の{d}日です", "7月{d}日です", "7月の{d}日なんですけど")
        ],
        ("入力_現在の予約日", "7月の25日です", "07-25"): [
            (fmt.format(d=d), f"07-{d:02d}") for d in range(1, 29)
            for fmt in ("7月の{d}日です", "7月{d}日です", "7月の{d}日なんですけど")
        ],
        # 予約希望日（8月固定）
        ("入力_予約希望日", "8月の1日でお願いします", "08-01"): [
            (fmt.format(d=d), f"08-{d:02d}") for d in range(1, 29)
            for fmt in ("8月の{d}日でお願いします", "8月{d}日でお願いします", "8月の{d}日はどうでしょうか")
        ],
        # 性別（かな読みペア「おんなです」等は列挙しない＝保護）
        ("入力_性別", "女性です", "女性"): _phrases(
            ["女性です", "女です", "女性になります"], "女性", _PREFIX),
        ("入力_性別", "男です", "男性"): _phrases(
            ["男です", "男性です", "男性になります"], "男性", _PREFIX),
        # 緊急性
        ("入力_緊急性", "通常です", "通常"): _phrases(
            ["通常です", "急ぎではありません", "普通で大丈夫です", "特に急ぎません"],
            "通常", _PREFIX),
        # 理由（期待の分類語を含む言い回しのみ）
        ("入力_理由", "都合が悪くなりまして", "都合"): _phrases(
            ["都合が悪くなりまして", "都合がつかなくなりまして", "都合が合わなくなってしまって",
             "仕事の都合で難しくなりました", "急に都合がつかなくなりました",
             "家の都合で行けなくなりまして", "その日の都合が悪くなってしまいました"], "都合"),
        ("入力_理由", "体調不良です", "体調不良"): _phrases(
            ["体調不良です", "体調不良のためです", "体調不良になってしまいまして"], "体調不良"),
        # 受診内容
        ("入力_受診内容", "健康診断でお願いします", "健康診断"): _phrases(
            ["健康診断でお願いします", "健康診断をお願いします", "健康診断です",
             "健康診断を受けたいです", "健康診断で予約したいです", "健康診断になります",
             "健康診断希望です", "健康診断を予約したいのですが"], "健康診断", _PREFIX),
        ("入力_受診内容", "特定健診をお願いします", "特定健診"): _phrases(
            ["特定健診をお願いします", "特定健診です", "特定健診を受けたいです"], "特定健診"),
        # 選定療養費
        ("入力_選定療養費", "はい", "了承"): ryoushou,
        ("入力_選定療養費", "はいわかりました", "了承"): ryoushou,
    }


# ─── 個人情報列の動的フィラー検出 ────────────────────────────────

def build_dynamic_table(rows: list[dict]) -> dict[tuple[str, str, str], list[tuple[str, str]]]:
    """2 回以上出現する (入力, 期待) ペアをフィラーとみなして置換対象に加える。

    - 個人情報 4 列: 個人情報を複数ケースで共有する意図的なテスト軸は存在しないため、
      重複ペアは常にフィラー。スタイル（DTMF素数字/ハイフン/口語）は元値から検出して保存。
      かな読み・漢数字などの STT 特殊表記は保護（_detect_style が None を返す）。
    - 診療科: 期待値が素の診療科名で、入力にその科名がそのまま含まれる「復唱型」ペアのみ
      フィラー扱い（STT誤認識ケースは入力に正しい科名を含まないため保護される）。
    - 最後の問い合わせ（期待=なし）/ 選定療養費（期待=了承）: 分類クラスが固定の相槌フィラー。
    """
    table: dict[tuple[str, str, str], list[tuple[str, str]]] = {}
    pool_cache: dict = {}

    def pool_of(key, factory):
        if key not in pool_cache:
            pool_cache[key] = factory()
        return pool_cache[key]

    def rule_personal(col, fin, fexp):
        style = _detect_style(col, fin)
        if style is None:
            return None
        return pool_of((col, style), _PERSONAL_POOLS[(col, style)])

    def rule_dept(col, fin, fexp):
        # プレースホルダー期待・不明・エイリアス/誤認識入力（科名を含まない）は保護
        if not fexp or "{" in fexp or fexp == "不明" or fexp not in fin:
            return None
        if fin == fexp:  # 素の科名（DTMF/簡略ケース）→ 科名のみのプール（拡張リスト）
            return pool_of(("dept", "bare"), lambda: [(d, d) for d in _DEPTS_WIDE])
        return pool_of(("dept", "polite"), _pool_dept)

    def rule_nashi(col, fin, fexp):
        return pool_of(("nashi",), _pool_nashi) if fexp == "なし" else None

    def rule_ryoushou(col, fin, fexp):
        return pool_of(("ryoushou",), _pool_ryoushou) if fexp == "了承" else None

    def rule_tsuuin(col, fin, fexp):
        # 分類クラス（初診/再診/初回/リピーター）ごとの言い回しプール
        factories = {
            "再診": _pool_saishin,
            "初診": lambda: _phrases(
                ["初めてです", "初診です", "初めてかかります", "今回が初めてです",
                 "初めて受診します", "初めてお電話しました", "初めての利用です"],
                "初診", _PREFIX),
            "初回": lambda: _phrases(
                ["初めてです", "初めてなんです", "初めて受けます", "今回が初めてです",
                 "初めての受診です", "初めて利用します"],
                "初回", _PREFIX),
            "リピーター": lambda: _phrases(
                ["去年も受けました", "毎年受けています", "何度か受けています",
                 "去年も利用しました", "毎年こちらで受けています"],
                "リピーター", _PREFIX),
        }
        if fexp not in factories:
            return None
        return pool_of(("tsuuin", fexp), factories[fexp])

    rules = {col: rule_personal for col in PERSONAL_COLS}
    rules["入力_診療科"] = rule_dept
    rules["入力_最後の問い合わせ"] = rule_nashi
    rules["入力_選定療養費"] = rule_ryoushou
    rules["入力_通院歴"] = rule_tsuuin

    for col, rule in rules.items():
        exp_col = "期待" + col[2:]
        cnt = Counter((r.get(col, "").strip(), r.get(exp_col, "").strip())
                      for r in rows if r.get(col, "").strip())
        for (fin, fexp), n in cnt.items():
            if n < 2:
                continue
            pool = rule(col, fin, fexp)
            if pool:
                table[(col, fin, fexp)] = pool
    return table


# ─── 置換エンジン ────────────────────────────────────────────────

def _start_index(case_id: str, column: str, pool_size: int) -> int:
    h = hashlib.md5(f"{column}:{case_id}".encode("utf-8")).hexdigest()
    return int(h, 16) % pool_size


def diversify(rows: list[dict], table: dict) -> tuple[int, Counter]:
    """rows を in-place で置換。戻り値: (置換セル数, 列ごとの置換数)"""
    used: dict[str, set[str]] = {}          # 列ごとの使用済み入力値
    least_used: dict[str, Counter] = {}      # プール枯渇時の最少使用選択
    replaced = 0
    per_col: Counter = Counter()

    # 置換対象外の既存値も used に登録し、置換値が既存値と衝突しないようにする
    filler_cols = {col for (col, _, _) in table.keys()}
    for row in rows:
        for col in filler_cols:
            v = row.get(col, "").strip()
            exp = row.get("期待" + col[2:], "").strip()
            if v and (col, v, exp) not in table:
                used.setdefault(col, set()).add(v)

    for row in rows:
        cid = row.get("case_id", "")
        for (col, fin, fexp), pool in table.items():
            exp_col = "期待" + col[2:]
            if row.get(col, "").strip() != fin or row.get(exp_col, "").strip() != fexp:
                continue
            u = used.setdefault(col, set())
            lu = least_used.setdefault(col, Counter())
            start = _start_index(cid, col, len(pool))
            chosen = None
            for k in range(len(pool)):
                cand = pool[(start + k) % len(pool)]
                if cand[0] not in u:
                    chosen = cand
                    break
            if chosen is None:
                # プール枯渇 → 最少使用の値を選ぶ（重複最小化のベストエフォート）
                idx = {id(c): i for i, c in enumerate(pool)}
                chosen = min(pool, key=lambda c: (lu[c[0]], idx[id(c)]))
            u.add(chosen[0])
            lu[chosen[0]] += 1
            row[col] = chosen[0]
            row[exp_col] = chosen[1]
            replaced += 1
            per_col[col] += 1
    return replaced, per_col


# ─── 統計表示 ────────────────────────────────────────────────────

def print_stats(rows: list[dict], label: str) -> None:
    print(f"── {label} ──")
    cols = [c for c in rows[0].keys() if c.startswith("入力_")]
    total_dup = 0
    for col in cols:
        vals = [r[col].strip() for r in rows if r.get(col, "").strip()]
        if len(vals) < 2:
            continue
        c = Counter(vals)
        dup = len(vals) - len(c)
        total_dup += dup
        if dup:
            top = c.most_common(1)[0]
            print(f"  {col}: {len(vals)}件中 distinct {len(c)}（重複 {dup}）"
                  f" 最多: {top[0][:24]!r}×{top[1]}")
    print(f"  合計重複セル: {total_dup}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="統計表示のみ（変更しない）")
    mode.add_argument("--write", action="store_true", help="置換して上書き保存")
    args = ap.parse_args()

    with open(args.csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print_stats(rows, "置換前")
    if args.check:
        return

    table = dict(build_filler_table())
    table.update(build_dynamic_table(rows))
    replaced, per_col = diversify(rows, table)
    print(f"\n置換セル数: {replaced}")
    for col, n in per_col.most_common():
        print(f"  {col}: {n}")
    print()
    print_stats(rows, "置換後")

    with open(args.csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n書き込み完了: {args.csv_path}")


if __name__ == "__main__":
    main()
