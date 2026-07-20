"""faq_exact_match オラクル — script.js (Brekeke Nashorn 本体) と同一の
「完全一致辞書引き」ロジックの Python 独立実装。

script.js の挙動:
  1. 入力テキストを trim
  2. 空文字なら NO_RESULT
  3. faqMap に「自前キーとして」完全一致するキーがあれば ANSWER + その回答本文、無ければ NO_RESULT
     - 参照は Object.prototype.hasOwnProperty.call(faqMap, text)（継承プロパティ除外）

この Python 実装は同じ判定（同じ入力 → 同じ ANSWER/NO_RESULT と同じ回答本文）を返すことを保証する正本。
faqMap は script.js から抽出するので、辞書の二重管理 (drift) は起きない。
アルゴリズム/辞書を変更したら script.js を直し、test_oracle.py + 実機受入を再実行する。

stdlib のみ (json / re)。pip 不使用。

CLI:
    python oracle.py "駐車場はありますか"   # 任意テキストを 1 件判定
    python oracle.py --probe                 # 内蔵プローブの判定一覧 (期待値設計用)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent

# script.js の `var faqMap = { ... };` を抽出する正規表現。
# 値はすべて二重引用符の文字列・ネストした波括弧なし → 最初の "};" が faqMap の閉じ。
_FAQMAP_RE = re.compile(r"var\s+faqMap\s*=\s*(\{.*?\})\s*;", re.DOTALL)


def load_faq_map(script_path: Path | None = None) -> dict:
    """script.js から faqMap (= JS オブジェクトリテラル) を抽出して dict で返す。
    keys/values はすべて二重引用符文字列なので、抽出した {...} はそのまま妥当な JSON。"""
    p = script_path or (HERE / "script.js")
    src = p.read_text(encoding="utf-8")
    m = _FAQMAP_RE.search(src)
    if not m:
        raise RuntimeError(f"faqMap が script.js に見つからない: {p}")
    return json.loads(m.group(1))


def match(text: str, faq_map: dict) -> dict:
    """script.js の メインロジック (section 3-4) と 1:1。

    戻り値: {"result": "ANSWER"|"NO_RESULT", "answer": <回答本文 or "">}
      - text を trim し、空なら NO_RESULT
      - faq_map に自前キーとして完全一致すれば ANSWER + その本文
      - それ以外 (言い換え・部分一致・継承プロパティ "toString" 等) は NO_RESULT
    """
    t = text.strip()  # JS String.prototype.trim() 相当
    if t == "":
        return {"result": "NO_RESULT", "answer": ""}
    # Python の `in dict` は自前キーのみ判定する (継承プロパティを持たない) ので、
    # 堅牢化後の JS `hasOwnProperty.call(faqMap, text)` と一致する。
    if t in faq_map:
        return {"result": "ANSWER", "answer": faq_map[t]}
    return {"result": "NO_RESULT", "answer": ""}


# プローブ (期待値設計用)。実機テストケースはこの実測結果から選ぶ。
PROBE_INPUTS = [
    "駐車場はありますか",          # 完全一致 → ANSWER
    "面会時間を教えてください",      # 完全一致 → ANSWER
    "会計時にクレジットカードは使えますか？",  # 末尾？込み完全一致 → ANSWER
    "  駐車場はありますか  ",        # 前後空白 → trim → ANSWER
    "駐車場ありますか",            # 「は」欠落 (言い換え) → NO_RESULT
    "クレジットカードは使えますか",  # 接頭/末尾？欠落 → NO_RESULT
    "今日の天気は",                # 無関係 → NO_RESULT
    "",                            # 空 → NO_RESULT
    "   ",                         # 空白のみ → NO_RESULT
    "toString",                    # 継承プロパティ → NO_RESULT (堅牢化検証)
    "constructor",                 # 継承プロパティ → NO_RESULT
    "__proto__",                   # 継承プロパティ → NO_RESULT
]


def main(argv: list[str]) -> int:
    faq_map = load_faq_map()
    if argv and argv[0] != "--probe":
        r = match(argv[0], faq_map)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    print(f"# faqMap: {len(faq_map)} entries (script.js から抽出)\n")
    for q in PROBE_INPUTS:
        r = match(q, faq_map)
        ans = (r["answer"][:30] + "…") if len(r["answer"]) > 30 else r["answer"]
        print(f"{r['result']:9} | {q!r:40} | {ans}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
