# -*- coding: utf-8 -*-
"""triage_router オラクル受入テスト。

A→B→C→D カスケードの全分岐＋代表的な自由発話ケースを網羅し、
出力が入力から一意に決まる（決定論）ことを検証する。
発話は全て合成（実 PII なし）。実行: python test_oracle.py
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from oracle import (GOAL1, GOAL2, GOAL3, classify_complaint, triage)

# (説明, kwargs, 期待goal, 期待block or None, 期待category or None)
CASES = [
    # ---- A-0 CPA（全テキスト検知・最優先） ----
    ("CPA 呼吸なし", dict(complaint="母が呼吸をしていません"), GOAL1, "A0", None),
    ("CPA 脈なし", dict(complaint="脈がないみたいです"), GOAL1, "A0", None),
    ("CPA 溺水", dict(complaint="子どもがお風呂で沈んでいて"), GOAL1, "A0", None),
    # ---- A ABCD（閉じた Yes/No・unclear=危険側） ----
    ("ABCD 呼吸yes", dict(abcd={"A3_呼吸": "yes"}, complaint="ちょっと相談です"), GOAL1, "A", None),
    ("ABCD 意識unclear→危険側", dict(abcd={"A1_意識": "unclear"}, complaint="相談です"), GOAL1, "A", None),
    ("ABCD 全no→通過", dict(abcd={k: "no" for k in ("A1_意識", "A2_気道", "A3_呼吸", "A4_循環")},
                            complaint="少し鼻がつまっています"), GOAL3, "D", None),
    # ---- B 頭痛めまい ----
    ("B頭痛 突発激痛", dict(complaint="突然、頭を殴られたような痛みがします"), GOAL1, "B", "頭痛めまい"),
    ("B頭痛 神経脱落", dict(complaint="頭が痛くて、手足がしびれてきました"), GOAL1, "B", "頭痛めまい"),
    ("頭痛 軽症→非発火", dict(complaint="昨日から軽い頭痛があります"), GOAL3, "D", "頭痛めまい"),
    # ---- B 胸痛 ----
    ("B胸痛 放散痛+冷汗", dict(complaint="胸が痛くて、腕にも広がって冷や汗が出ます"), GOAL1, "B", "胸痛"),
    ("B胸痛 安静時痛(助詞混在)", dict(complaint="胸も痛いし、安静にしても痛みます"), GOAL1, "B", "胸痛"),
    # ---- B 腹痛 ----
    ("B腹痛 激痛", dict(complaint="今まで経験したことのない激しい腹痛です"), GOAL1, "B", "腹痛"),
    ("B腹痛 ヘルニア嵌頓", dict(complaint="お腹が痛くて、足の付け根にこぶが出ています"), GOAL1, "B", "腹痛"),
    # ---- B 発熱 ----
    ("B発熱 高熱薬無効", dict(complaint="40度の熱があって解熱薬も効きません"), GOAL1, "B", "発熱"),
    ("B発熱 NFKC全角40+意識", dict(complaint="４０度の熱で意識がもうろうとします"), GOAL1, "B", None),
    ("B発熱 けいれん", dict(complaint="熱があって、けいれんを起こしました"), GOAL1, "B", "発熱"),
    # ---- B 外傷出血 ----
    ("B外傷 止血不能", dict(complaint="指を切って、圧迫しても血が止まりません"), GOAL1, "B", "外傷出血"),
    ("B外傷 開放骨折", dict(complaint="転んで、骨が見えています"), GOAL1, "B", "外傷出血"),
    # ---- B 共通致死語（その他カテゴリでも拾う） ----
    ("B共通 呼吸困難(その他)", dict(complaint="なんだか息ができなくて苦しいです"), GOAL1, "B", "その他"),
    ("B共通 麻痺(その他)", dict(complaint="呂律が回らなくて、片側の手が動きません"), GOAL1, "B", "その他"),
    # ---- B 自由発話フォールバック: free_texts からも Red Flag を拾う ----
    ("B free_texts走査", dict(complaint="胸が痛い", free_texts=["腕に広がって冷や汗も出てきました"]),
     GOAL1, "B", "胸痛"),
    # ---- C 修飾因子 → GOAL2 ----
    ("C 歩行不能", dict(complaint="腰が少しだるくて、歩けなくなりました"), GOAL2, "C", None),
    ("C 抗凝固薬", dict(complaint="頭を軽くぶつけました。血をサラサラにする薬を飲んでいます"), GOAL2, "C", "外傷出血"),
    ("C 妊娠", dict(complaint="少し熱っぽいです。妊娠しています"), GOAL2, "C", "発熱"),
    ("C 高齢", dict(complaint="喉が痛いです。父は80歳です"), GOAL2, "C", None),
    # ---- D 通常 ----
    ("D 軽い鼻づまり", dict(complaint="少し鼻がつまっています"), GOAL3, "D", "その他"),
    ("D 空入力", dict(), GOAL3, "D", None),
    ("D のどいがいが", dict(complaint="のどが少しいがいがします"), GOAL3, "D", None),
    # ---- 優先順位（ランクダウンなし・上位ブロック先勝ち） ----
    ("優先 CPA>C", dict(complaint="母が呼吸をしていません。父は80歳です"), GOAL1, "A0", None),
    ("優先 A>B", dict(abcd={"A4_循環": "yes"}, complaint="昨日から軽い頭痛"), GOAL1, "A", None),
    ("優先 B>C", dict(complaint="胸が痛くて腕に広がる。父は80歳で歩けない"), GOAL1, "B", "胸痛"),
]

# 分類の単体ケース
CLASSIFY_CASES = [
    ("胸も痛い", "胸痛"),
    ("お腹が痛い", "腹痛"),
    ("熱がある", "発熱"),
    ("転んでけがをした", "外傷出血"),
    ("頭が痛い", "頭痛めまい"),
    ("眠れません", "その他"),
    ("熱があって胸も痛い", "胸痛"),   # A系(胸痛)優先 over 発熱
]


def _run() -> int:
    passed = failed = 0
    fails: list[str] = []

    for desc, kwargs, exp_goal, exp_block, exp_cat in CASES:
        r = triage(**kwargs)
        ok = (r.goal == exp_goal)
        if exp_block is not None:
            ok = ok and (r.block == exp_block)
        if exp_cat is not None:
            ok = ok and (r.category == exp_cat)
        if ok:
            passed += 1
        else:
            failed += 1
            fails.append(f"[TRIAGE] {desc}: got goal={r.goal}/block={r.block}/cat={r.category} "
                         f"reason={r.reason} | expect goal={exp_goal}/block={exp_block}/cat={exp_cat}")

    for text, exp in CLASSIFY_CASES:
        got = classify_complaint(text)
        if got == exp:
            passed += 1
        else:
            failed += 1
            fails.append(f"[CLASSIFY] '{text}': got {got} expect {exp}")

    # 決定論: 同一入力を2回 → 完全一致
    a = triage(complaint="胸が痛くて腕に広がって冷や汗", free_texts=["歩けない"])
    b = triage(complaint="胸が痛くて腕に広がって冷や汗", free_texts=["歩けない"])
    if a.as_dict() == b.as_dict():
        passed += 1
    else:
        failed += 1
        fails.append(f"[DETERMINISM] 同一入力で不一致: {a.as_dict()} != {b.as_dict()}")

    print(f"[TEST] triage_router oracle: {passed} PASS / {failed} FAIL (total {passed + failed})")
    for f in fails:
        print("  [FAIL]", f)
    if failed == 0:
        print("[TEST DONE] 全ケース PASS = 入力→出力が一意（決定論で書き切れる）")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
