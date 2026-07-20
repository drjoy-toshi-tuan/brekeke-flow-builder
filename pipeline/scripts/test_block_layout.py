# -*- coding: utf-8 -*-
"""test_block_layout.py — block_layout のバックエッジ層計算ガード（#281 回帰防止）。

背景（#281）: 再聴取ループ B→A（A=手前の聴取ステップ, B=A の子孫ゲート）があると、
A が「後続ブロック B を親に持つ」扱いになり、①DFS で配置が後回しにされ ②合流ロジック
で自分のループ本体 B より下へ押し下げられ、分岐の横展開が壊れて全体が縦1列に潰れていた。

find_back_edges() でバックエッジを検出し、層計算に使う parents からのみ除外することで
戻り先ブロックが本来の位置に inline 配置される。本テストはその機序を合成グラフでピン留めする:

  Test 1: find_back_edges が再聴取ループの戻り辺のみをバックエッジとして検出する
          （フォワード辺・分岐辺は誤検出しない）
  Test 2: 再聴取ループのループ頭が、自分のループ本体より下へ押し下げられない
          （y(頭) < y(本体) ＝ 縦1列潰れの直接原因が消えている）
  Test 3: 分岐が別列へ横展開される（同一列へ潰れない）
  Test 4: acyclic な DAG では back_edges が空集合（旧挙動と同一＝回帰なし）

stdlib のみ・standalone 実行:
  python scripts/test_block_layout.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from block_layout import assign_block_tops, find_back_edges  # noqa: E402


def _blk(step, btype, nexts, echo_back=False):
    return {
        "step": step, "type": btype, "echo_back": echo_back,
        "save_to": "", "next_blocks": list(nexts),
        "is_terminal": (btype == "termination"),
    }


def _children(blocks):
    return {b["step"]: list(dict.fromkeys(b["next_blocks"])) for b in blocks}


def _bmap(blocks):
    return {b["step"]: b for b in blocks}


# 用件分岐 + 日付の再聴取ループを持つ最小フロー
#   冒頭 → 用件 ─┬→ 日付 → 日付ゲート ─┬→ 日付（再聴取＝バックエッジ）
#               │                      └→ END_完了
#               └→ END_他
def _loop_flow():
    return [
        _blk("冒頭", "opening", ["用件"]),
        _blk("用件", "hearing", ["日付", "END_他"]),
        _blk("日付", "hearing", ["日付ゲート"], echo_back=True),
        _blk("日付ゲート", "script", ["日付", "END_完了"]),
        _blk("END_完了", "termination", []),
        _blk("END_他", "termination", []),
    ]


def run():
    results = []

    # ── Test 1: バックエッジ検出 ──
    blocks = _loop_flow()
    be = find_back_edges(_children(blocks), _bmap(blocks))
    ok1 = be == {("日付ゲート", "日付")}
    print(f"[Test 1] back-edges={be} expected={{('日付ゲート','日付')}} -> {'PASS' if ok1 else 'FAIL'}")
    results.append(ok1)

    # ── Test 2: ループ頭が本体より下へ押し下げられない ──
    tops = assign_block_tops(blocks)
    y_head = tops["日付"][1]
    y_body = tops["日付ゲート"][1]
    ok2 = y_head < y_body
    print(f"[Test 2] y(日付)={y_head} < y(日付ゲート)={y_body} -> {'PASS' if ok2 else 'FAIL'}")
    results.append(ok2)

    # ── Test 3: 用件の分岐が別列へ横展開される ──
    x_hicashi = tops["END_他"][0]
    x_hizuke = tops["日付"][0]
    ok3 = x_hicashi != x_hizuke
    print(f"[Test 3] 分岐先が別列 x(END_他)={x_hicashi} x(日付)={x_hizuke} -> {'PASS' if ok3 else 'FAIL'}")
    results.append(ok3)

    # ── Test 4: acyclic DAG では back_edges が空（回帰なし）──
    dag = [
        _blk("冒頭", "opening", ["用件"]),
        _blk("用件", "hearing", ["A", "B"]),
        _blk("A", "termination", []),
        _blk("B", "termination", []),
    ]
    be_dag = find_back_edges(_children(dag), _bmap(dag))
    ok4 = be_dag == set()
    print(f"[Test 4] acyclic back-edges={be_dag} expected=set() -> {'PASS' if ok4 else 'FAIL'}")
    results.append(ok4)

    npass = sum(1 for r in results if r)
    print("-" * 60)
    print(f"{npass}/{len(results)} PASS")
    return npass == len(results)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(0 if run() else 1)
