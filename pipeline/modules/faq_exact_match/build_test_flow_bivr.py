"""build_test_flow_bivr.py — faq_exact_match 受入テストフロー .bivr 生成。

oracle.py (Python オラクル) と同一の入力セットを Pattern 6 形式 (チェイン式) で
1 コール内に直列実行する。faq_matcher / business_hour_classifier /
build_classifier_acceptance_bivr.py と同型。

== 入力注入 (STT 非依存・1 行差し替え) ==
本番 script.js の入力取得行
    var rawInput = $runner.getModuleResult("OpenAI_RAG");
の「この 1 行だけ」を
    var rawInput = "<入力>";              (kind="string")
    var rawInput = {"text": "<入力>"};    (kind="object")
に差し替える。後続の trim・object/string 振り分け・faqMap 完全一致判定・setObject は本番 script.js
verbatim で実行されるので、入力読み (getModuleResult 配線) の不確実性から独立しつつ、
**trim と入力形状ハンドリングまで含めた**「辞書引きロジックの決定論ユニットテスト」になる。
(in-flow の getModuleResult 配線自体は P7 連結テストで網羅する。P6 は辞書引きの全ケース網羅が責務。)

== 期待値の合成 (分岐 + 回答本文を 1 値で assert) ==
本番 script.js は分岐を $runner.setResult(result)（"ANSWER"/"NO_RESULT"）で、回答本文を
$runner.setObject("scripts-faq", answer) で出す。受入では「正しい分岐かつ正しい回答本文か」まで
1 つの jump 条件で検証したいので、最終行 $runner.setResult(result); を
    $runner.setResult(result === "ANSWER" ? answer : result);
に差し替える（setObject は verbatim で実行されたまま）。これにより:
  - ANSWER ケース → setResult = 回答本文 → 期待条件 ^<回答本文>$（本文一致まで assert）
  - NO_RESULT ケース → setResult = "NO_RESULT" → 期待条件 ^NO_RESULT$
期待値は oracle.match() を呼んで構築するため、bivr とオラクルの判定は構造的に一致する。

期待 jump が連続発火すれば PASS_全件PASS へ、不一致なら対応 FAIL 終話で停止。

出力: ./acceptance_test/FaqExactMatchAcceptanceTest.bivr (Brekeke 管理画面で flow として import)
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import oracle  # noqa: E402  (faq_exact_match/oracle.py)

FLOW_NAME = "テスト$FAQ完全一致受入"
OUT_DIR = HERE / "acceptance_test"
OUT_FILE = OUT_DIR / "FaqExactMatchAcceptanceTest.bivr"

# (case_id, label, 入力テキスト[, kind]) — kind 省略時は "string"。期待値は oracle.match() で実測。
# 入力は script.js の faqMap キーと「1文字単位で」一致/不一致を作るので、ここを編集したら
# build を再実行し、resolved 出力で期待が意図通りか必ず目視確認すること。
TEST_INPUTS = [
    # --- 完全一致 → ANSWER（回答本文の正しさまで検証）---
    ("EM-01", "駐車場_完全一致",        "駐車場はありますか"),
    ("EM-02", "面会時間_完全一致",      "面会時間を教えてください"),
    ("EM-03", "診察券紛失_読点キー",    "診察券を紛失したのですが、どうしたらいいですか"),
    ("EM-04", "カード_末尾全角？",      "会計時にクレジットカードは使えますか？"),
    ("EM-05", "診断書料金_短答",        "保険会社診断書の作成料金はいくらですか"),
    ("EM-06", "差額ベッド_半角カナ",    "差額ﾍﾞｯﾄ代は医療費控除に含まれますか"),
    ("EM-07", "手の外科_末尾。キー",    "手の外科が無くなっても診断書を作成可能ですか。"),
    ("EM-08", "領収書_答に半角(",       "領収書を紛失しました。再発行できますか"),
    ("EM-09", "車いす_末尾？",          "車いすは借りられますか？"),
    ("EM-10", "付添年齢_短答",          "保護者付添が不要年齢は何歳からですか"),
    ("EM-11", "予約なし_末尾？",        "予約なしで受診できますか？"),
    ("EM-12", "診断書記載依頼_末尾。",  "保険会社の診断書を書いてほしい"),
    # --- trim 検証（前後空白でも完全一致 = 本番 trim が走ることの確認）---
    ("TR-01", "駐車場_両端空白",        "  駐車場はありますか  "),
    ("TR-02", "面会_両端タブ",          "\t面会時間を教えてください\t"),
    # --- object 入力形状（{text:...}）でも同じ判定（入力ハンドリング＋extract＋trim 検証）---
    ("OB-01", "object入力_駐車場",      "駐車場はありますか",            "object"),
    ("OB-02", "object入力_面会_空白",   "  面会時間を教えてください  ",  "object"),
    # --- 非マッチ（完全一致である証明：1文字でも違えば NO_RESULT）---
    ("NF-01", "駐車場_は欠落",          "駐車場ありますか"),
    ("NF-02", "カード_接頭末尾欠落",    "クレジットカードは使えますか"),
    ("NF-03", "面会時間_部分",          "面会時間"),
    ("NF-04", "無関係_天気",            "今日の天気は"),
    ("NF-05", "手の外科_末尾。欠落",    "手の外科が無くなっても診断書を作成可能ですか"),
    # --- 空・空白 → NO_RESULT ---
    ("EP-01", "空文字",                 ""),
    ("EP-02", "空白のみ",               "   "),
    # --- 継承プロパティ → NO_RESULT（hasOwnProperty 堅牢化の検証）---
    ("PT-01", "継承_toString",          "toString"),
    ("PT-02", "継承_constructor",       "constructor"),
    ("PT-03", "継承_hasOwnProperty",    "hasOwnProperty"),
    ("PT-04", "継承___proto__",         "__proto__"),
    ("PT-05", "継承_valueOf",           "valueOf"),
]

# script.js の入力取得行。この 1 行だけをリテラル注入に差し替える（trim / 形状振り分けは verbatim）。
INPUT_LINE = 'var rawInput = $runner.getModuleResult("OpenAI_RAG");'
# 本番の最終出力行。受入用の合成 assert に差し替える。
FINAL_SETRESULT = "$runner.setResult(result);"


def regex_escape(s: str) -> str:
    """Brekeke condition (regex) 用に正規表現メタ文字をエスケープ。"""
    return re.sub(r"([.^$*+?()\[\]{}|\\/])", r"\\\1", s)


def js_str(s: str) -> str:
    """JS 文字列リテラルを安全に生成（json.dumps の出力は妥当な JS 文字列）。"""
    return json.dumps(s, ensure_ascii=False)


def build_script_for_case(case_id: str, inp: str, kind: str,
                          expected_desc: str, base_script: str) -> str:
    """入力取得行をリテラル注入に、最終 setResult を合成 assert に差し替える。
    kind="string": rawInput=文字列リテラル / kind="object": rawInput={"text":...}。
    どちらも後続の trim・object|string 振り分けは本番 verbatim で実行される。"""
    if INPUT_LINE not in base_script:
        raise SystemExit(f"ERROR: 入力取得行 '{INPUT_LINE}' が見つからない（script.js が想定外）")
    if FINAL_SETRESULT not in base_script:
        raise SystemExit(f"ERROR: 最終出力行 '{FINAL_SETRESULT}' が見つからない")

    if kind == "object":
        inject = 'var rawInput = {"text": ' + js_str(inp) + "};"
    else:
        inject = "var rawInput = " + js_str(inp) + ";"
    s = base_script.replace(INPUT_LINE, inject, 1)
    s = s.replace(
        FINAL_SETRESULT,
        '$runner.getLogger().info("[' + case_id + '] expected=' + expected_desc
        + ' result=" + result + " answer=" + answer);\n'
        + '$runner.setResult(result === "ANSWER" ? answer : result);',
    )
    marker = ('$runner.getLogger().info("[' + case_id + '] kind=' + kind
              + ' input=" + ' + js_str(inp) + ');\n\n')
    return marker + s


def empty_next_slot() -> dict:
    return {"condition": "", "label": "", "nextModuleName": ""}


def empty_subs() -> list:
    return [{"moduleName": "", "label": ""} for _ in range(3)]


def make_script_module(name, script, layout, expected_condition,
                       on_match_next, on_fail_next, description) -> dict:
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


def make_disconnect_module(name, layout, description) -> dict:
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
    base_script = (HERE / "script.js").read_text(encoding="utf-8")
    faq_map = oracle.load_faq_map()

    # 各ケースの期待値を oracle で実測
    resolved = []  # (case_id, label, inp, kind, expected_condition, expected_desc)
    print(f"# building {len(TEST_INPUTS)} cases (expected は oracle.match で実測)\n")
    for entry in TEST_INPUTS:
        case_id, label, inp = entry[0], entry[1], entry[2]
        kind = entry[3] if len(entry) > 3 else "string"
        r = oracle.match(inp, faq_map)
        if r["result"] == "ANSWER":
            cond = "^" + regex_escape(r["answer"]) + "$"
            desc = "ANSWER"
        else:
            cond = "^NO_RESULT$"
            desc = "NO_RESULT"
        resolved.append((case_id, label, inp, kind, cond, desc))
        ans_preview = (r["answer"][:26] + "…") if len(r["answer"]) > 26 else r["answer"]
        print(f"  {case_id} {desc:9} {kind:6} | {inp!r:42} | {ans_preview}")
    print()

    modules: dict[str, dict] = {}
    x_test, x_fail = 300, 760
    y_step, y0 = 160, 100

    pass_name = "PASS_全件PASS"
    modules[pass_name] = make_disconnect_module(
        pass_name,
        layout={"x": x_test, "y": y0 + (len(resolved) + 1) * y_step},
        description=f"全 {len(resolved)} ケースの期待 jump が連続発火 → 受入テスト PASS",
    )

    next_module = pass_name
    for idx, (case_id, label, inp, kind, cond, desc) in reversed(list(enumerate(resolved))):
        i = idx + 1
        fail_name = f"FAIL_{case_id}_期待:{desc}"
        modules[fail_name] = make_disconnect_module(
            fail_name,
            layout={"x": x_fail, "y": y0 + i * y_step},
            description=f"{case_id} ({label}) で期待 '{desc}' と異なる結果。回帰",
        )
        test_name = f"テスト{case_id}_{label}"
        script = build_script_for_case(case_id, inp, kind, desc, base_script)
        modules[test_name] = make_script_module(
            test_name,
            script=script,
            layout={"x": x_test, "y": y0 + i * y_step},
            expected_condition=cond,
            on_match_next=next_module,
            on_fail_next=fail_name,
            description=f"受入テストケース {case_id}: {label} (kind={kind}, expected={desc})",
        )
        next_module = test_name

    start_name = next_module

    flow = {
        "name": FLOW_NAME,
        "desc": f"faq_exact_match 受入テスト {len(resolved)} ケース (Pattern 6 チェイン式)。"
                f"oracle.py と同一カバー。入力取得行のみリテラル注入で STT 非依存（trim/形状振り分けは verbatim）。"
                f"1 コールで全ケース直列実行、PASS_全件PASS 到達で受入確定。前提: script.js verbatim (faqMap 改変なし)。",
        "start": start_name,
        "modules": modules,
        "layout": {"width": 1200, "height": y0 + (len(resolved) + 2) * y_step},
        "resultValue": "",
        "postCallAction": "",
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    body = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(OUT_FILE, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(FLOW_NAME, safe="") + ".txt"
        zf.writestr(fname, body)
    print(f"wrote {OUT_FILE} ({OUT_FILE.stat().st_size} bytes, {len(modules)} modules)")
    print(f"   flow file: {fname}")
    print(f"   start: {start_name}")
    print(f"   {len(resolved)} cases + {len(resolved)} FAIL terminations + 1 PASS termination")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
