#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — store 役の自前検証（department_classifier engine v2 = universe 構造化・新エンジン）。

fixer≠grader: これは store（製造役）が出荷前に回す自前検証。独立採点（検品）は
score_department.py / carve_department.py（oracle をカタログ解決）で別途走らせる。

VFB #263 差し戻し対応（2026-07-01「script.js 未同梱＝実機認定に進めない」）:
  新規 17KB エンジンの JS parity を、ローカルに JS ランタイム（node/jjs/java）が無い環境で
  最大限保証する三段構成。最終 Nashorn 実行 parity は VFB P6 実機（オーナーゲート）で確定する。

  [A] oracle 回帰 … promotion/test_oracle.py の全ケースを promotion/oracle.py に通し全 PASS。
  [B] spec 一致  … promotion/script.js の @spec ブロックからレキシコン（DEPARTMENTS/WAKARANAI/
                   OOS/AMBIGUOUS/ABBREV/MOD_*/BASE_*/TRAILERS/STRIP）を機械パースし、
                   oracle.py のモジュール定数とバイト同値であることを要求（辞書ドリフト検出）。
  [C] 挙動 parity … script.js を Python に忠実ミラー（限定正規化 nrm + decide 制御フロー）した
                   js_classify を、本番コーパス（head+tail 全ユニーク語）+ test_oracle 全ケースで
                   oracle.classify（実 NFKC）と突合。差分 0 を要求。
                   ＝JS が採る「NFKC 不使用の限定正規化」と「step 1-8 制御フロー」が
                     oracle と等価であることを実データで実証（独立参照＝oracle.py）。

実行: python store/department_classifier/promotion/verify.py
"""
import csv
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SCRIPT_JS = os.path.join(HERE, "script.js")
CORPUS = [
    os.path.join(REPO, "data", "_corpus_department_head.tsv"),
    os.path.join(REPO, "data", "_corpus_department_tail_sample.tsv"),
]

# promotion/oracle.py を最優先で import（独立参照＝真値）
sys.path.insert(0, HERE)
import oracle  # noqa: E402


# ============================ [A] 回帰 ============================
def run_regression():
    """promotion/test_oracle.py を promotion/oracle.py に対して実行し (pass, fail) を返す。"""
    sys.modules.pop("test_oracle", None)
    to = importlib.import_module("test_oracle")
    fails = []
    for utt, exp in to.CASES:
        got = oracle.classify(utt)
        if got != exp:
            fails.append((utt, exp, got))
    return len(to.CASES), fails


# ==================== [B] script.js @spec パース ====================
def _extract_spec_block(js):
    m = re.search(r"@spec-begin(.*?)@spec-end", js, re.S)
    if not m:
        raise ValueError("script.js に @spec-begin/@spec-end が見つからない")
    return m.group(1)


def _parse_var(block, name):
    """`var NAME = <array-literal>;` を括弧バランスで切り出し JSON として読む。
    レキシコンは二重引用符文字列と入れ子配列のみ＝有効な JSON。科名に `[` `]` は無い。"""
    idx = block.find("var " + name)
    if idx < 0:
        raise ValueError("script.js に var %s が無い" % name)
    start = block.index("[", idx)
    depth = 0
    for i in range(start, len(block)):
        c = block[i]
        if c == "[":
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                return json.loads(block[start:i + 1])
    raise ValueError("var %s の配列が閉じていない" % name)


def run_spec_parity():
    with open(SCRIPT_JS, encoding="utf-8") as f:
        block = _extract_spec_block(f.read())

    diffs = []

    def check(label, js_val, py_val):
        if js_val != py_val:
            diffs.append((label, js_val, py_val))

    # 単純リスト
    check("STRIP", _parse_var(block, "STRIP"), oracle._STRIP)
    check("TRAILERS", _parse_var(block, "TRAILERS"), oracle._TRAILERS)
    check("WAKARANAI", _parse_var(block, "WAKARANAI"), oracle.WAKARANAI)
    check("OOS_NAMES", _parse_var(block, "OOS_NAMES"), oracle.OOS_NAMES)
    check("OOS_SUFFIX", _parse_var(block, "OOS_SUFFIX"), oracle.OOS_SUFFIX)
    check("AMBIGUOUS_ORGAN", _parse_var(block, "AMBIGUOUS_ORGAN"), oracle.AMBIGUOUS_ORGAN)
    # DEPARTMENTS: JS [canon,[keys]] ↔ oracle (canon,[keys])
    js_dep = [[c, ks] for c, ks in _parse_var(block, "DEPARTMENTS")]
    py_dep = [[c, list(ks)] for c, ks in oracle.DEPARTMENTS]
    check("DEPARTMENTS", js_dep, py_dep)
    # BASE_* tuples
    check("BASE_INNER", _parse_var(block, "BASE_INNER"), list(oracle._BASE_INNER))
    check("BASE_OUTER", _parse_var(block, "BASE_OUTER"), list(oracle._BASE_OUTER))
    # MOD_*/ABBREV: JS [[k,v]...] ↔ oracle dict.items()（挿入順）
    check("MOD_INNER", [list(p) for p in _parse_var(block, "MOD_INNER")],
          [[k, v] for k, v in oracle._MOD_INNER.items()])
    check("MOD_OUTER", [list(p) for p in _parse_var(block, "MOD_OUTER")],
          [[k, v] for k, v in oracle._MOD_OUTER.items()])
    check("ABBREV", [list(p) for p in _parse_var(block, "ABBREV")],
          [[k, v] for k, v in oracle._ABBREV.items()])
    return diffs


# ============ [C] script.js 忠実ミラー（Python）============
# 以下は promotion/script.js の nrm / decide を「JS を読んで」Python へ 1:1 転写したもの。
# 独立参照 oracle.py と突合するので、転写バグ（辞書でなく制御フロー側）を検出する。
_STRIP = oracle._STRIP
_TRAILERS = oracle._TRAILERS


def _js_nrm(raw):
    """script.js nrm と同じ限定正規化（NFKC 不使用）。全角ASCII(FF01-FF5E)→半角 + STRIP + trim + 末尾定型語。"""
    s = "" if raw is None else str(raw)
    out = []
    for ch in s:
        o = ord(ch)
        out.append(chr(o - 0xFEE0) if 0xFF01 <= o <= 0xFF5E else ch)
    s = "".join(out)
    for k in _STRIP:
        s = s.replace(k, "")
    s = s.strip()
    changed = True
    while changed:
        changed = False
        for t in _TRAILERS:
            tt = t.replace("・", "")
            if tt and len(s) > len(tt) and s.endswith(tt):
                s = s[: -len(tt)]
                changed = True
    return s


def _js_match_abbrev(s):
    cands = [s]
    if len(s) > 2 and s.endswith("か"):
        cands.append(s[:-1])
    for c in cands:
        for k, v in oracle._ABBREV.items():
            if k == c:
                return v
    return None


def _js_compose(s):
    for bases, mod_map, base_canon in (
        (list(oracle._BASE_INNER), oracle._MOD_INNER, "内科"),
        (list(oracle._BASE_OUTER), oracle._MOD_OUTER, "外科"),
    ):
        mods = sorted([(k, v, i) for i, (k, v) in enumerate(mod_map.items())],
                      key=lambda x: (-len(x[0]), x[2]))
        for bk in bases:
            if s == bk:
                return base_canon
            if len(s) > len(bk) and s.endswith(bk):
                prefix = s[: -len(bk)]
                for k, v, _ in mods:
                    if k in prefix:
                        return v
    return None


_JS_KEYS = sorted(
    [(k, canon, i) for i, (k, canon) in enumerate(
        [(k, c) for c, keys in oracle.DEPARTMENTS for k in keys])],
    key=lambda x: (-len(x[0]), x[2]),
)


def js_classify(raw, facility=None):
    s = _js_nrm(raw)
    if s == "":
        return "NO_RESULT"
    if re.match(r"^[0-9]+$", s):
        return "NO_RESULT"
    for m in oracle.OOS_NAMES:
        if m in s:
            return "OUT_OF_SCOPE"
    for w in oracle.WAKARANAI:
        if w.replace("・", "") in s:
            return "登録なし"
    for k, canon, _ in _JS_KEYS:
        if k in s:
            if facility is not None and canon not in facility:
                return canon + "|OFF_MENU"
            return canon
    ab = _js_match_abbrev(s)
    if ab:
        if facility is not None and ab not in facility:
            return ab + "|OFF_MENU"
        return ab
    g = _js_compose(s)
    if g:
        return g
    for suf in oracle.OOS_SUFFIX:
        if suf in s:
            return "OUT_OF_SCOPE"
    for o in oracle.AMBIGUOUS_ORGAN:
        if o in s:
            return "AMBIGUOUS"
    return "NO_RESULT"


def run_behavior_parity():
    phrases = set()
    for fp in CORPUS:
        if not os.path.exists(fp):
            continue
        with open(fp, encoding="utf-8") as fh:
            for row in csv.DictReader(fh, delimiter="\t"):
                phrases.add(row["phrase"])
    # test_oracle ケースも母集団に含める
    sys.modules.pop("test_oracle", None)
    to = importlib.import_module("test_oracle")
    for utt, _ in to.CASES:
        phrases.add(utt)
    div = []
    for p in phrases:
        a = oracle.classify(p)   # 実 NFKC 経路（真値）
        b = js_classify(p)       # script.js ミラー（限定正規化）
        if a != b:
            div.append((p, a, b))
    return len(phrases), div


def main():
    if getattr(sys.stdout, "reconfigure", None):
        sys.stdout.reconfigure(encoding="utf-8")
    print("=" * 64)
    print("[A] oracle 回帰（promotion/test_oracle → promotion/oracle）")
    print("=" * 64)
    n, fails = run_regression()
    print("  %d件中 PASS=%d FAIL=%d" % (n, n - len(fails), len(fails)))
    for utt, exp, got in fails[:20]:
        print("    NG %r exp=%s got=%s" % (utt, exp, got))

    print("=" * 64)
    print("[B] spec 一致（script.js @spec ↔ oracle.py 定数）")
    print("=" * 64)
    spec_diffs = run_spec_parity()
    if not spec_diffs:
        print("  全レキシコン一致（DEPARTMENTS/WAKARANAI/OOS/AMBIGUOUS/ABBREV/MOD_*/BASE_*/TRAILERS/STRIP）")
    for label, jv, pv in spec_diffs:
        print("    DRIFT %s\n      js=%r\n      py=%r" % (label, jv, pv))

    print("=" * 64)
    print("[C] 挙動 parity（script.js ミラー ↔ oracle・本番コーパス+ケース）")
    print("=" * 64)
    pop, div = run_behavior_parity()
    print("  母集団ユニーク=%d  classify 差分=%d" % (pop, len(div)))
    for p, a, b in div[:30]:
        print("    DIV %r  oracle=%s  js=%s" % (p, a, b))

    ok = (len(fails) == 0) and (len(spec_diffs) == 0) and (len(div) == 0)
    print("=" * 64)
    if ok:
        print("VERDICT: PASS  (回帰 %d/%d ・ spec 完全一致 ・ 挙動 parity 差分0/%d)" % (n, n, pop))
        print("  ※最終 Nashorn 実行 parity は VFB P6 実機で確定（エンジン変更ゆえ spec-skip 不可・フル再認定）。")
    else:
        print("VERDICT: FAIL  (回帰fail=%d ・ spec drift=%d ・ 挙動 div=%d)"
              % (len(fails), len(spec_diffs), len(div)))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
