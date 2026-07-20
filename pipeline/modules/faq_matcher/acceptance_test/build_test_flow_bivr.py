"""build_test_flow_bivr.py — FAQ Matcher 受入テストフロー .bivr 生成。

oracle.py (Python オラクル) と同一の質問セットを Pattern 6 形式 (チェイン式) で
1 コール内に直列実行する。各ケースは QUESTION_SOURCE にリテラル質問を注入するので
STT / AmiVoice 設定・入力読みの不確実性から独立した「検索エンジンの決定論テスト」になる。

期待値は oracle.search() を呼んで構築するため、bivr とオラクルの判定は構造的に一致する:
  - FOUND ケース → 「正解の答え本文そのもの」を期待条件 (^答え$) にする → 答えの正しさまで assert
  - NOT_FOUND ケース → ^NOT_FOUND$ を期待条件にする

期待 jump が連続発火すれば PASS_全件PASS へ、不一致なら対応 FAIL 終話で停止。

前提: テナント drjoy 配下に Note drjoy.faq_acceptance が存在し、faq_sample.json と同一内容であること。
（商談デモ用 drjoy.faq とは別 Note ＝上書き衝突を回避。FAQ_NOTE_NAME は wiring 化済み #faq-note-wiring）

出力: ./FAQAcceptanceTest.bivr (Brekeke 管理画面で flow として import)
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent  # faq_matcher/
sys.path.insert(0, str(PROJECT_ROOT))

import oracle  # noqa: E402  (faq_matcher/oracle.py)

FLOW_NAME = "テスト$FAQ受入"

# 受入テスト専用 Note 名。商談デモ用 drjoy.faq と衝突しないよう別サフィックス。
# FAQ_NOTE_NAME は wiring 変数（part.json）＝この差し替えは engine_hash に影響しない。
FAQ_NOTE_NAME = "drjoy.faq_acceptance"


def set_faq_note(base_script: str, note_name: str) -> str:
    """script.js の FAQ_NOTE_NAME(wiring) をテスト用 Note 名へ差し替える。"""
    pat = re.compile(r'var FAQ_NOTE_NAME\s*=\s*"[^"]*"\s*;')
    if not pat.search(base_script):
        raise SystemExit("ERROR: FAQ_NOTE_NAME 行が見つからない (script.js が想定外フォーマット)")
    return pat.sub(f'var FAQ_NOTE_NAME    = "{note_name}";', base_script)

# (case_id, label, question) — oracle で期待値を実測して条件を組む
TEST_QUESTIONS = [
    # --- FOUND 期待 (完全一致 / 強い言い換え) ---
    ("FAQ-01", "駐車場_完全一致",   "駐車場はありますか"),
    ("FAQ-02", "駐車場_言い換え",   "駐車場の場所を教えてください"),
    ("FAQ-03", "受付時間_一致",     "受付時間を教えて"),
    ("FAQ-04", "保険証_一致",       "保険証は必要ですか"),
    ("FAQ-05", "カード_完全一致",   "クレジットカードは使えますか"),
    ("FAQ-06", "カード_言い換え",   "カードで支払えますか"),
    ("FAQ-07", "面会_一致",         "面会時間を教えて"),
    ("FAQ-08", "小児科_一致",       "子供を診てもらえますか"),
    ("FAQ-09", "紹介状_境界cov0.5", "紹介状はいりますか"),
    # --- NOT_FOUND 期待 (弱い言い換え=しきい値未満 / 無関係 / フィラー / 短すぎ) ---
    ("FAQ-10", "駐車場_弱い言換",   "車を停めるところはありますか"),
    ("FAQ-11", "診療時間_弱い言換", "診療は何時までですか"),
    ("FAQ-12", "無関係_天気",       "今日の天気はどうですか"),
    ("FAQ-13", "フィラーのみ",       "あのー、えっと"),
    ("FAQ-14", "短すぎ_はい",       "はい"),
]


def regex_escape(s: str) -> str:
    """Brekeke condition (regex) 用に正規表現メタ文字をエスケープ。"""
    return re.sub(r'([.^$*+?()\[\]{}|\\/])', r'\\\1', s)


def build_script_for_case(case_id: str, question: str, expected_desc: str, base_script: str) -> str:
    """script.js の QUESTION_SOURCE をリテラル質問に差し替え、先頭にマーカーログを足す。"""
    if '"' in question:
        raise SystemExit(f"ERROR: 質問に \" を含む ({case_id}) — JS 文字列を壊すので別表現に")
    marker = (
        '$runner.getLogger().info('
        f'"[{case_id}] expected={expected_desc} q={question}");\n\n'
    )
    pattern = re.compile(r'var QUESTION_SOURCE\s*=\s*"[^"]*"\s*;')
    if not pattern.search(base_script):
        raise SystemExit("ERROR: QUESTION_SOURCE 行が見つからない (script.js が想定外フォーマット)")
    s = pattern.sub(f'var QUESTION_SOURCE = "{question}";', base_script)
    return marker + s


def empty_next_slot() -> dict:
    return {"condition": "", "label": "", "nextModuleName": ""}


def empty_subs() -> list:
    return [{"moduleName": "", "label": ""} for _ in range(3)]


def make_script_module(name: str, script: str, layout: dict,
                       expected_condition: str, on_match_next: str, on_fail_next: str,
                       description: str) -> dict:
    next_slots = [
        {"condition": expected_condition, "label": "PASS→次", "nextModuleName": on_match_next},
        {"condition": "^.*$",             "label": "FAIL",     "nextModuleName": on_fail_next},
    ]
    while len(next_slots) < 10:
        next_slots.append(empty_next_slot())
    return {
        "name": name,
        "type": "@General$Script",
        "matchingmethod": 1,
        "description": description,
        "layout": layout,
        "params": {"script": script.replace("\r\n", "\n").replace("\n", "\r\n")},
        "next": next_slots,
        "subs": empty_subs(),
    }


def make_disconnect_module(name: str, layout: dict, description: str) -> dict:
    return {
        "name": name,
        "type": "@IVR$Disconnect",
        "matchingmethod": 1,
        "description": description,
        "layout": layout,
        "params": {},
        "next": [empty_next_slot() for _ in range(10)],
        "subs": empty_subs(),
    }


def main() -> int:
    base_script = (PROJECT_ROOT / "script.js").read_text(encoding="utf-8")
    base_script = set_faq_note(base_script, FAQ_NOTE_NAME)  # 受入テスト用 Note 名を充填
    corpus = oracle.load_corpus()

    # 各ケースの期待値を oracle で実測
    resolved = []  # (case_id, label, question, expected_condition, expected_desc)
    print(f"# building {len(TEST_QUESTIONS)} cases (expected値は oracle.search で実測)\n")
    for case_id, label, question in TEST_QUESTIONS:
        r = oracle.search(question, corpus)
        if r["status"] == "FOUND":
            cond = "^" + regex_escape(r["answer"]) + "$"
            desc = f"FOUND:{r['id']}"
        else:
            cond = "^NOT_FOUND$"
            desc = "NOT_FOUND"
        resolved.append((case_id, label, question, cond, desc))
        print(f"  {case_id} {desc:16} score={r['score']:<7} cov={r['coverage']:<6} | {question}")
    print()

    modules: dict[str, dict] = {}
    x_test, x_fail = 300, 760
    y_step, y0 = 200, 100

    pass_name = "PASS_全件PASS"
    modules[pass_name] = make_disconnect_module(
        pass_name,
        layout={"x": x_test, "y": y0 + (len(resolved) + 1) * y_step},
        description=f"全 {len(resolved)} ケースの期待 jump が連続発火 → 受入テスト PASS",
    )

    next_module = pass_name
    for idx, (case_id, label, question, cond, desc) in reversed(list(enumerate(resolved))):
        i = idx + 1
        fail_name = f"FAIL_{case_id}_期待:{desc}"
        modules[fail_name] = make_disconnect_module(
            fail_name,
            layout={"x": x_fail, "y": y0 + i * y_step},
            description=f"{case_id} ({label}) で期待 '{desc}' と異なる結果。回帰",
        )
        test_name = f"テスト{case_id}_{label}"
        script = build_script_for_case(case_id, question, desc, base_script)
        modules[test_name] = make_script_module(
            test_name,
            script=script,
            layout={"x": x_test, "y": y0 + i * y_step},
            expected_condition=cond,
            on_match_next=next_module,
            on_fail_next=fail_name,
            description=f"受入テストケース {case_id}: {label} (expected={desc})",
        )
        next_module = test_name

    start_name = next_module

    flow = {
        "name": FLOW_NAME,
        "desc": f"FAQ Matcher 受入テスト {len(resolved)} ケース (Pattern 6 チェイン式)。"
                f"oracle.py と同一カバー。リテラル質問注入で STT 非依存。1 コールで全ケース直列実行、"
                f"PASS_全件PASS 到達で受入確定。前提: Note drjoy.faq_acceptance = faq_sample.json。",
        "start": start_name,
        "modules": modules,
        "layout": {"width": 1200, "height": y0 + (len(resolved) + 2) * y_step},
        "resultValue": "",
        "postCallAction": "",
    }

    out = HERE / "FAQAcceptanceTest.bivr"
    body = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(FLOW_NAME, safe="") + ".txt"
        zf.writestr(fname, body)
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(modules)} modules)")
    print(f"   flow file: {fname}")
    print(f"   start: {start_name}")
    print(f"   {len(resolved)} cases + {len(resolved)} FAIL terminations + 1 PASS termination")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
