"""ingest_ai_settings_csv.py — 実運用「AI応答設定」CSV → FAQ Matcher コーパス JSON 変換。

Dr.JOY 診療予約フローの「AI応答設定」CSV (列: AI / HP / 対象者 / カテゴリ / 質問 / 回答) を、
FAQ Matcher が読む corpus JSON ( [{"id","q":[...],"a"}, ...] ) に決定論変換する常設ツール。
build_bivr.py / acceptance_test/build_test_flow_bivr.py と同列のモジュール build スクリプト。
LLM 不使用・再実行で同一出力 (べき等)。

質問セルの構造:
    <主質問>
    【類似質問】
    <言い換え1> / <言い換え2> / ...
    【AI正規化クエリ】
    <正規化された 1 文>
→ q = [主質問] + 類似質問群。 【AI正規化クエリ】 は患者の発話ではない (話題ラベル) ため
  検索対象 q には入れず、参照用に norm_query フィールドへ退避する。

使い方:
    python ingest_ai_settings_csv.py                 # 既定 source/ の CSV → faq_full.json
    python ingest_ai_settings_csv.py <input.csv> <output.json>

出力後は oracle/test_oracle/build_test_flow_bivr 側で読み込み、δ チューニング + 受入へ。
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
DEFAULT_IN = HERE / "source" / "診療予約_AI応答設定_完全正規化対応版.csv"
DEFAULT_OUT = HERE / "faq_full.json"

SIM_MARKER = "類似質問"        # 【類似質問】
NORM_MARKER = "正規化"          # 【AI正規化クエリ】
MARKERS = (SIM_MARKER, NORM_MARKER)


def read_rows(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp932"):
        try:
            txt = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise SystemExit(f"ERROR: encoding を判定できない: {path}")
    return list(csv.reader(io.StringIO(txt)))


def is_marker(line: str) -> bool:
    return any(m in line for m in MARKERS)


def parse_question_cell(cell: str) -> tuple[list[str], str]:
    """質問セル → (q リスト, 正規化クエリ)。"""
    lines = [ln.strip() for ln in cell.split("\n")]
    lines = [ln for ln in lines if ln]
    sim_i = next((i for i, ln in enumerate(lines) if SIM_MARKER in ln), None)
    norm_i = next((i for i, ln in enumerate(lines) if NORM_MARKER in ln), None)

    # 主質問: 先頭〜最初のマーカーまで (通常 1 行)
    head_end = min([i for i in (sim_i, norm_i) if i is not None], default=len(lines))
    main = [ln for ln in lines[:head_end] if not is_marker(ln)]

    # 類似質問: 【類似質問】〜【AI正規化クエリ】の間
    if sim_i is not None:
        para_end = norm_i if (norm_i is not None and norm_i > sim_i) else len(lines)
        paras = [ln for ln in lines[sim_i + 1:para_end] if not is_marker(ln)]
    else:
        paras = []

    # 正規化クエリ (参照用、q には入れない)
    norm_q = ""
    if norm_i is not None:
        norm_lines = [ln for ln in lines[norm_i + 1:] if not is_marker(ln)]
        norm_q = " ".join(norm_lines).strip()

    # q = 主質問 + 類似質問。順序保持で重複除去。
    q: list[str] = []
    for item in main + paras:
        if item and item not in q:
            q.append(item)
    return q, norm_q


def main(argv: list[str]) -> int:
    in_path = Path(argv[0]) if len(argv) >= 1 else DEFAULT_IN
    out_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_OUT
    if not in_path.exists():
        raise SystemExit(f"ERROR: 入力 CSV が無い: {in_path}")

    rows = read_rows(in_path)
    if not rows:
        raise SystemExit("ERROR: CSV が空")
    header, data = rows[0], rows[1:]
    # 列位置 (カテゴリ/質問/回答) をヘッダ名で解決。無ければ既定 3/4/5。
    def col(name: str, default: int) -> int:
        for i, h in enumerate(header):
            if name in h:
                return i
        return default
    c_cat, c_q, c_a = col("カテゴリ", 3), col("質問", 4), col("回答", 5)

    corpus: list[dict] = []
    skipped: list[str] = []
    dq_warn: list[str] = []
    for idx, r in enumerate(data, start=1):
        if len(r) <= max(c_q, c_a):
            skipped.append(f"row{idx}: 列不足")
            continue
        cat = r[c_cat].strip() if len(r) > c_cat else ""
        q, norm_q = parse_question_cell(r[c_q])
        # 回答は 1 行化 (改行で分かれた複数文を連結)。日本語は句点で自己区切りされるため "" 連結。
        # bivr の ^答え$ 条件 / TTS 読み上げで改行が事故らないようにする。マッチは q のみ使うので無害。
        a = "".join(ln.strip() for ln in r[c_a].split("\n") if ln.strip())
        if not q or not a:
            skipped.append(f"row{idx}: q/a 空 (cat={cat})")
            continue
        # build_test_flow_bivr.py は質問に " を含むと JS 文字列を壊す → 検出して警告
        for item in q:
            if '"' in item:
                dq_warn.append(f'q{idx:03d}: 質問に " を含む: {item!r}')
        entry = {"id": f"q{idx:03d}", "category": cat, "q": q, "a": a}
        if norm_q:
            entry["norm_query"] = norm_q
        corpus.append(entry)

    # --- augment マージ (実機FB対応の上乗せ分。元CSV は不変) ---
    aug_path = HERE / "faq_augment.json"
    if aug_path.exists():
        aug = json.loads(aug_path.read_text(encoding="utf-8"))
        byid = {e["id"]: e for e in corpus}
        nv = ne = 0
        for eid, variants in aug.get("add_variants", {}).items():
            if eid not in byid:
                print(f"   WARN augment: 未知 id {eid} (add_variants スキップ)")
                continue
            for v in variants:
                if v not in byid[eid]["q"]:
                    byid[eid]["q"].append(v)
                    nv += 1
        for e in aug.get("add_entries", []):
            if e["id"] in byid:
                print(f"   WARN augment: id 衝突 {e['id']} (add_entries スキップ)")
                continue
            corpus.append({"id": e["id"], "category": e.get("category", ""),
                           "q": list(e["q"]), "a": e["a"]})
            ne += 1
        if nv or ne:
            print(f"   augment 適用: +variants {nv} / +entries {ne} (from {aug_path.name})")

    out_path.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Note 投入用の最小・コンパクト版 (matcher が読む id/q/a のみ)。
    # Brekeke Note に貼る本体 = これ。oracle/受入 bivr もこのファイルを参照源にして
    # 「Note の中身」と「期待値の計算元」を完全一致させる。
    note_min = [{"id": e["id"], "q": e["q"], "a": e["a"]} for e in corpus]
    note_path = out_path.parent / "faq_note.json"
    note_path.write_text(
        json.dumps(note_min, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    nq = sum(len(e["q"]) for e in corpus)
    print(f"wrote {out_path.name}: {len(corpus)} entries / {nq} q-variants "
          f"(avg {nq / len(corpus):.1f}/entry)")
    print(f"   note   : {note_path.name} ({note_path.stat().st_size} bytes, 最小 id/q/a = Note 投入用)")
    print(f"   source: {in_path.name} ({len(data)} data rows)")
    if skipped:
        print(f"   skipped {len(skipped)}:")
        for s in skipped:
            print("     -", s)
    if dq_warn:
        print(f"   WARNING: {len(dq_warn)} 質問に \" 混入 (bivr 生成前に要対処):")
        for w in dq_warn:
            print("     -", w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
