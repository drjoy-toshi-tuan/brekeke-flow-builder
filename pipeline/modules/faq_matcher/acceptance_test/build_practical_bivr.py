"""build_practical_bivr.py — 実データ(faq_note.json / 112件)に対する実践受入 bivr 生成。

build_test_flow_bivr.py (faq_sample 12 件の回帰用) の実践版。実運用「AI応答設定」由来の
faq_note.json コーパスに対し、患者が実際に話す言い回しのケースを Pattern 6 チェイン式で
1 コール内に直列実行する。各ケースは QUESTION_SOURCE にリテラル質問を注入するので
STT 非依存の「新エンジン (exact-match短絡 + IDF-marginゲート) × 実データ」の決定論検証になる。

期待値は oracle.search(faq_note コーパス) で実測 → bivr とオラクルの判定は構造的に一致:
  FOUND      → 「正解の答え本文そのもの」を期待条件 (^答え$) にする → ルーティングの正しさまで assert
  NOT_FOUND  → ^NOT_FOUND$ (崩れ入力・真の重複・総論曖昧 → 有人転送が正解、の検証)

前提: テナント drjoy 配下の Note drjoy.faq_practice = faq_note.json と同一内容であること。
（商談デモ用 drjoy.faq とは別 Note。FAQ_NOTE_NAME は wiring 化済み）

出力: ./FAQPracticalTest.bivr
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
PROJECT_ROOT = HERE.parent  # faq_matcher/
sys.path.insert(0, str(PROJECT_ROOT))

import oracle  # noqa: E402
from build_test_flow_bivr import (  # noqa: E402  ヘルパー再利用
    regex_escape,
    build_script_for_case,
    make_script_module,
    make_disconnect_module,
    set_faq_note,
)

FLOW_NAME = "テスト$FAQ実践"
CORPUS = PROJECT_ROOT / "faq_note.json"
# 実践テスト専用 Note 名。商談デモ用 drjoy.faq と衝突しないよう別サフィックス（FAQ_NOTE_NAME は wiring）。
FAQ_NOTE_NAME = "drjoy.faq_practice"

# (case_id, label, question) — 患者の自然な言い回し。期待値は oracle で実測する。
# " は JS 文字列を壊すので質問に含めない。
TEST_QUESTIONS = [
    # --- アクセス仕分け (識別語で各論へ正しくルーティングできるかの主検証) ---
    ("ACC-01", "駐車場料金",     "駐車場の料金っていくらですか"),
    ("ACC-02", "駐車場台数",     "車は何台くらい停められますか"),
    ("ACC-03", "障害者駐車",     "障害者用の駐車場はありますか"),
    ("ACC-04", "駐輪場",         "自転車で行ってもいいですか"),
    ("ACC-05", "面会駐車",       "面会でも駐車場は使えますか"),
    ("ACC-06", "無料シャトル",   "無料のシャトルバスはありますか"),
    ("ACC-07", "路線バス",       "路線バスで行けますか"),
    ("ACC-08", "最寄り駅",       "最寄り駅はどこですか"),
    ("ACC-09", "駅出口",         "駅の何番出口から出ればいいですか"),
    ("ACC-10", "雨に濡れず",     "雨に濡れずに病院まで行けますか"),
    ("ACC-11", "住所",           "病院の住所を教えてください"),
    ("ACC-12", "カーナビ",       "カーナビには何て入力すればいいですか"),
    ("ACC-13", "高速IC",         "高速道路はどこのインターで降りますか"),
    ("ACC-14", "新幹線",         "新幹線で行く場合のアクセスは"),
    ("ACC-15", "羽田",           "羽田空港からの行き方を教えて"),
    # --- exact-match 短絡 (総論質問が各論に埋もれず即採用されるか) ---
    ("EX-01",  "駐車場総論",     "駐車場はありますか"),
    ("EX-02",  "タクシー乗り場", "タクシー乗り場"),
    # --- 施設・その他 ---
    ("FAC-01", "車いす貸出",     "車椅子は貸してもらえますか"),
    ("FAC-02", "WiFi",           "Wi-Fiは使えますか"),
    ("FAC-03", "売店",           "院内にコンビニや売店はありますか"),
    ("FAC-04", "喫煙",           "タバコを吸える場所はありますか"),
    ("FAC-05", "カフェ",         "院内に食事できる場所はありますか"),
    ("GEN-01", "セカンドオピニオン", "セカンドオピニオンを受けたいです"),
    ("GEN-02", "診断書",         "診断書を発行してもらえますか"),
    ("GEN-03", "紹介状",         "紹介状は必要ですか"),
    # --- 真の重複 (同一変種を 2 entry が共有 → 曖昧 → NOT_FOUND が正解) ---
    ("DUP-01", "送迎バス重複",   "送迎バスはありますか"),
    # --- 崩れ / 無関係 / 短すぎ (NOT_FOUND → 有人転送 が正解) ---
    ("NG-01",  "崩れ炎症",       "炎症は必要ですか"),
    ("NG-02",  "無関係宇宙人",   "宇宙人はありますか"),
    ("NG-03",  "崩れぐるぐる",   "ぐるぐるは必要ですか"),
    ("NG-04",  "崩れほげ何時",   "ほげほげは何時ですか"),
    ("NG-05",  "崩れあいうえお", "あいうえおを教えて"),
    ("NG-06",  "短すぎ",         "うん"),
    # --- 発話の揺れ吸収 (会話的前置き/言い直し/反復/口語語尾 → クリーンな節へ落として拾う) ---
    ("DIS-01", "前置き到着時刻",   "ギリギリに行きたいんですけれども10分前で大丈夫ですか"),
    ("DIS-02", "言い直し駐車場",   "ないです嘘です。駐車場ありましたよね。"),
    ("DIS-03", "反復クレジット",   "クレジットで支払いできますかクレジットで支払いできますか"),
    ("DIS-04", "言い直し駐輪場",   "ないです嘘です。駐輪場ありましたよね。"),
    ("DIS-05", "口語語尾駐車場",   "駐車場ありましたよね"),
    ("DIS-06", "口語語尾駐輪場",   "駐輪場ありましたよね"),
    ("DIS-07", "言い直し駐車→駐輪", "駐車場じゃなくて駐輪場ありますか"),
    ("DIS-08", "逆接駐車場",       "車で行きたいんですけど駐車場ありますか"),
    ("DIS-09", "クレジット口語",   "クレジットで支払いできますか"),
    ("DIS-10", "前置き無関係",     "ギリギリに着きたいんですけど近くにカフェありますか"),
    # --- NO_QUESTION 前段ゲート (否定/終了応答は FAQ 検索前に分離 → ^NO_QUESTION$) ---
    ("NQ-01",  "質問なし裸",       "ありません"),
    ("NQ-02",  "質問なし口語",     "ありませんね"),
    ("NQ-03",  "質問なし大丈夫",   "大丈夫です"),
]


def main() -> int:
    base_script = (PROJECT_ROOT / "script.js").read_text(encoding="utf-8")
    base_script = set_faq_note(base_script, FAQ_NOTE_NAME)  # 実践テスト用 Note 名を充填
    corpus = oracle.load_corpus(CORPUS)
    byid = {e["id"]: e for e in corpus.entries}

    resolved = []  # (case_id, label, question, cond, desc)
    print(f"# building {len(TEST_QUESTIONS)} cases on {CORPUS.name} "
          f"({len(corpus.entries)} entries) — 期待値は oracle.search で実測\n")
    n_found = n_nf = n_nq = 0
    for case_id, label, question in TEST_QUESTIONS:
        r = oracle.search(question, corpus)
        if r["status"] == "FOUND":
            cond = "^" + regex_escape(r["answer"]) + "$"
            desc = f"FOUND:{r['id']}"
            ans_snip = r["answer"][:36]
            n_found += 1
        elif r["status"] == "NO_QUESTION":
            cond = "^NO_QUESTION$"
            desc = "NO_QUESTION"
            ans_snip = "(no-question pre-gate)"
            n_nq += 1
        else:
            cond = "^NOT_FOUND$"
            desc = "NOT_FOUND"
            ans_snip = "(" + str(r.get("reason", "")) [:40] + ")"
            n_nf += 1
        resolved.append((case_id, label, question, cond, desc))
        print(f"  {case_id:7} {desc:14} | {question[:24]:24} -> {ans_snip}")
    print(f"\n# resolved: FOUND={n_found}  NOT_FOUND={n_nf}  NO_QUESTION={n_nq}\n")

    modules: dict[str, dict] = {}
    x_test, x_fail = 300, 760
    y_step, y0 = 200, 100

    pass_name = "PASS_全件PASS"
    modules[pass_name] = make_disconnect_module(
        pass_name,
        layout={"x": x_test, "y": y0 + (len(resolved) + 1) * y_step},
        description=f"全 {len(resolved)} ケースの期待 jump が連続発火 → 実践受入 PASS",
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
            description=f"実践ケース {case_id}: {label} (expected={desc})",
        )
        next_module = test_name

    start_name = next_module
    flow = {
        "name": FLOW_NAME,
        "desc": f"FAQ Matcher 実践受入 {len(resolved)} ケース (Pattern 6 チェイン式)。"
                f"faq_note.json({len(corpus.entries)}件)に対し新エンジン(exact-match短絡 + IDF-marginゲート + "
                f"NO_QUESTION前段ゲート + 発話の揺れフォールバック)を STT非依存で検証。"
                f"PASS_全件PASS 到達で受入確定。前提: Note drjoy.faq_practice = faq_note.json。",
        "start": start_name,
        "modules": modules,
        "layout": {"width": 1200, "height": y0 + (len(resolved) + 2) * y_step},
        "resultValue": "",
        "postCallAction": "",
    }

    out = HERE / "FAQPracticalTest.bivr"
    body = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(FLOW_NAME, safe="") + ".txt"
        zf.writestr(fname, body)
    print(f"wrote {out} ({out.stat().st_size} bytes, {len(modules)} modules)")
    print(f"   start: {start_name}")
    print(f"   {len(resolved)} cases + {len(resolved)} FAIL + 1 PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
