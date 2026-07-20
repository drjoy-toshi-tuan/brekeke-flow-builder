"""FAQ Matcher オラクル — script.js (Brekeke Nashorn 本体) と同一の検索ロジックの
Python 独立実装。エンベディング/外部API を使わず、NFKC 正規化 + 文字 2-gram + BM25 +
coverage しきい値で「答えるべき FAQ があるか」を決定する。

stdlib のみ (json / math / re / unicodedata)。pip 不使用。

CLI:
    python oracle.py --probe          # 内蔵プローブ質問の判定結果を一覧表示 (期待値設計用)
    python oracle.py "駐車場はありますか"  # 任意の質問を 1 件判定

script.js と「同じ入力 → 同じ FOUND/NOT_FOUND と同じ id」を返すことを保証する正本。
アルゴリズムを変更したら script.js も同時に直し、test_oracle.py + 実機受入を再実行する。
"""
from __future__ import annotations

import json
import math
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).parent

# =============================================================================
# CONFIG — script.js の CONFIG ブロック既定値と一致させること
# =============================================================================
MIN_COVERAGE = 0.5      # 質問 bigram のうちマッチ FAQ に含まれる割合の下限 (これ未満は NOT_FOUND)
MIN_QUERY_CHARS = 3     # 正規化後この文字数未満の発話は質問とみなさず NOT_FOUND
MIN_IDF_MARGIN = 0.12   # 採用 entry と次点 entry の「IDF 重み付き被覆率」の差の下限。これ未満は
                        # 「団子(曖昧)」とみなし NOT_FOUND。STT 誤認識で内容語が崩れ「〜は必要ですか」等の
                        # 敬語尾だけ残った発話が複数 FAQ に等しくマッチする事故への安全弁 (→有人転送)。
BM25_K1 = 1.2
BM25_B = 0.75

# =============================================================================
# NO_QUESTION 前段ゲート CONFIG — script.js の同名リストと完全一致させること
# =============================================================================
# 役割: 終話「最後にご質問はございますか?」等への「いいえ/特にありません/大丈夫です」系の
# 応答を、FAQ 検索 (BM25) に流す前に決定論で分離し、制御トークン NO_QUESTION を返す。
# これにより「ありません」「ありませんね」「えっとありません」等の語尾だけ発話が、FAQ 本文
# (例 q006「他院からの手紙がありませんが…」) と 2-gram 衝突して ambiguity gate で誤棄却
# される事故を根治する。FAQ コーパス (Note) には依存しない (= 単独モジュールで完結)。
NOQ_MAX_NORM_LEN = 16  # 語尾判定の正規化後 文字数 上限。これを超える発話は「文」とみなし対象外。

# 正規化後 完全一致で NO_QUESTION とみなす定型句 (敬語/口語/ひらがな表記ゆれ込み)
NO_QUESTION_PHRASES = [
    # 既存 aug_no_question 由来 (コーパス側と同義・前段で先取り)
    "特にありません", "特にないです", "質問はありません", "質問はないです",
    "聞きたいことはありません", "もう大丈夫です", "大丈夫です", "結構です",
    "以上です", "特にございません",
    # 裸形・口語
    "ありません", "ございません", "ないです", "ない", "なし",
    "特にない", "特になし", "大丈夫", "結構", "以上",
    "問題ない", "問題ないです", "質問なし", "質問はない",
    # 終了・了解系
    "わかりました", "了解です", "了解しました", "もういいです", "もういい",
    # ひらがな表記ゆれ (STT 出力対策)
    "けっこう", "けっこうです", "だいじょうぶ", "だいじょうぶです",
    "いじょう", "いじょうです", "もんだいない",
]
# 「この語尾で終わる短い発話」を NO_QUESTION とみなす否定/終了サフィックス
NO_QUESTION_SUFFIXES = [
    "ありません", "ございません", "ないです", "ない", "なし",
    "大丈夫", "だいじょうぶ", "結構", "けっこう", "以上", "いじょう",
    "問題ない", "もんだいない",
]
# 先頭で剥がすフィラー (繰り返し剥離)
NO_QUESTION_FILLERS = [
    "えーと", "えっと", "えと", "えーっと", "あのー", "あの", "うーん", "うんと",
    "うん", "まあ", "まぁ", "その", "ええと", "ええ", "んー", "んと", "えー", "あー",
]
# 末尾で剥がす助詞・丁寧コピュラ (繰り返し剥離、長い順)
NO_QUESTION_TRAILERS = [
    "ですね", "ですよ", "でーす", "です", "だね", "だよ", "だ",
    "ねー", "よー", "ね", "よ", "な", "わ",
]

# 正規化時に除去する文字 (script.js の STRIP_CHARS と完全一致させる)。
# 長音記号 ー(U+30FC) は語の一部なので除去しない。NFKC で全角→半角化される記号も
# 念のため両形を含める。空白類も全部ここで落とす。
STRIP_CHARS = set(
    " \t\r\n　"
    "。、，．！？!?,.・…〜~「」『』（）()【】[]｜|‐-—―"
    "\"'`：:；;／/＼\\＿_"
)


def normalize(s: str) -> str:
    """NFKC → lower → STRIP_CHARS 除去。"""
    s = unicodedata.normalize("NFKC", s)
    s = s.lower()
    return "".join(ch for ch in s if ch not in STRIP_CHARS)


def bigrams(s: str) -> list[str]:
    """正規化文字列を文字 2-gram 化。長さ 1 は unigram、0 は空。"""
    n = normalize(s)
    if len(n) == 0:
        return []
    if len(n) == 1:
        return [n]
    return [n[i:i + 2] for i in range(len(n) - 1)]


# =============================================================================
# NO_QUESTION 前段ゲート — script.js の detectNoQuestion と 1:1
# =============================================================================
_NOQ_SET = {normalize(p) for p in NO_QUESTION_PHRASES}
_NOQ_SUFFIXES_N = [normalize(s) for s in NO_QUESTION_SUFFIXES]
_NOQ_FILLERS_N = [normalize(f) for f in NO_QUESTION_FILLERS]
_NOQ_TRAILERS_N = [normalize(t) for t in NO_QUESTION_TRAILERS]


def _strip_leading_fillers(n: str) -> str:
    changed = True
    while changed:
        changed = False
        for f in _NOQ_FILLERS_N:
            if f and n.startswith(f) and len(n) > len(f):
                n = n[len(f):]
                changed = True
    return n


def _strip_trailers(n: str) -> str:
    changed = True
    while changed:
        changed = False
        for t in _NOQ_TRAILERS_N:
            if t and n.endswith(t) and len(n) > len(t):
                n = n[:-len(t)]
                changed = True
    return n


def detect_no_question(question: str) -> bool:
    """終話質問への否定/終了応答 (「ありません」系) を FAQ 検索前に分離する決定論ゲート。
    True = NO_QUESTION (質問なし)。real question (q006「…ありませんが…ますか」等) は
    疑問終止「か」ガードで必ず False に倒す。FAQ コーパスには依存しない。"""
    n = normalize(question)
    if not n:
        return False
    n = _strip_leading_fillers(n)
    n = _strip_trailers(n)
    if not n:
        return False
    # 疑問終止「か」で終わる発話は質問 → NO_QUESTION にしない (誤検知の最重要ガード)
    if n.endswith("か"):
        return False
    if n in _NOQ_SET:
        return True
    # 短い否定/終了発話 (語尾一致 + 長さ上限)
    if len(n) <= NOQ_MAX_NORM_LEN:
        for suf in _NOQ_SUFFIXES_N:
            if suf and n.endswith(suf):
                return True
    return False


class Corpus:
    """faq_sample.json (= Brekeke Note drjoy.faq 相当) から転置統計を構築。"""

    def __init__(self, faq_list: list[dict]):
        self.entries = faq_list
        # 各質問バリアントを 1 ドキュメントとして展開 (同一エントリの別言い回しは別 doc)
        self.docs = []  # [(entry_index, variant_text, bigram_tokens)]
        for ei, entry in enumerate(faq_list):
            q = entry.get("q", [])
            variants = q if isinstance(q, list) else [q]
            for v in variants:
                self.docs.append((ei, v, bigrams(v)))
        self.n = len(self.docs)
        self.df: dict[str, int] = {}
        total_len = 0
        for (_ei, _v, toks) in self.docs:
            total_len += len(toks)
            for t in set(toks):
                self.df[t] = self.df.get(t, 0) + 1
        self.avgdl = (total_len / self.n) if self.n else 0.0

    def idf(self, term: str) -> float:
        df = self.df.get(term, 0)
        return math.log(1 + (self.n - df + 0.5) / (df + 0.5))

    def bm25(self, qtoks: list[str], doc_toks: list[str]) -> float:
        dl = len(doc_toks)
        dtf: dict[str, int] = {}
        for t in doc_toks:
            dtf[t] = dtf.get(t, 0) + 1
        score = 0.0
        for t in set(qtoks):
            f = dtf.get(t, 0)
            if f == 0:
                continue
            denom = f + BM25_K1 * (1 - BM25_B + BM25_B * (dl / self.avgdl if self.avgdl else 0))
            score += self.idf(t) * (f * (BM25_K1 + 1)) / denom
        return score

    @staticmethod
    def coverage(qtoks: list[str], doc_toks: list[str]) -> float:
        qset = set(qtoks)
        if not qset:
            return 0.0
        return len(qset & set(doc_toks)) / len(qset)

    def idf_coverage(self, qtoks: list[str], doc_toks: list[str]) -> float:
        """質問 bigram のうちマッチした分の IDF 質量比。素の coverage と違い、
        ありふれた敬語尾 (「は必要ですか」等、複数 doc に出る = IDF 小) は寄与が小さく、
        珍しい内容語 (「駐車場」「紹介状」等 = IDF 大) のマッチを強く反映する。
        ambiguity gate 用。den=0 は呼び出し側で起きない (空クエリは先に弾く)。"""
        qset = set(qtoks)
        if not qset:
            return 0.0
        dset = set(doc_toks)
        num = 0.0
        den = 0.0
        for t in qset:
            w = self.idf(t)
            den += w
            if t in dset:
                num += w
        return (num / den) if den else 0.0


def _match_query(question: str, corpus: Corpus) -> dict:
    """1 クエリ文字列 → FAQ 照合 (exact / coverage / ambiguity)。NO_QUESTION 前段ゲートと
    節分割は呼び出し側 search() が行う。script.js の matchQuery と 1:1。"""
    qn = normalize(question)
    qtoks = bigrams(question)
    result = {"status": "NOT_FOUND", "id": None, "answer": "", "score": 0.0, "coverage": 0.0, "top": []}

    # 全 doc をスコア化。選択は「元順 + strict-max」(同点は最若番 doc)で sort 安定性に依存しない。
    # script.js も同一の走査をすること。
    scored = []  # (sc, cov, idfc, ei, v) — 元の doc 順
    best = None  # coverage gate を通過した中で BM25 最大 (同点は先に出た doc)
    for (ei, v, toks) in corpus.docs:
        sc = corpus.bm25(qtoks, toks)
        cov = corpus.coverage(qtoks, toks)
        idfc = corpus.idf_coverage(qtoks, toks)
        scored.append((sc, cov, idfc, ei, v))
        if cov >= MIN_COVERAGE and sc > 0:
            if best is None or sc > best[0]:
                best = (sc, cov, idfc, ei, v)

    # ログ/calibration 用 top3 (表示専用。選択には使わない)
    top_sorted = sorted(scored, key=lambda x: x[0], reverse=True)
    result["top"] = [
        {"id": corpus.entries[ei]["id"], "variant": v, "score": round(sc, 3),
         "coverage": round(cov, 3), "idf_coverage": round(idfc, 3)}
        for (sc, cov, idfc, ei, v) in top_sorted[:3]
    ]

    # 短すぎる発話は質問とみなさない
    if len(qn) < MIN_QUERY_CHARS:
        result["reason"] = f"query too short ({len(qn)}<{MIN_QUERY_CHARS})"
        return result

    # --- exact-match short-circuit ---
    # 正規化クエリが登録質問の正規化と完全一致する entry が「ちょうど 1 件」なら、
    # 患者が登録質問そのものを言った最強シグナルとして margin gate を通さず即採用。
    # 総論質問 (「駐車場はありますか」) が各論 doc (「バイク用の駐車場はありますか」) に
    # 埋もれて団子になる事故を回避する。完全一致が複数 entry にまたがる (= 真の重複) 場合は
    # 曖昧なので通常の margin gate に委ねる。崩れ入力は完全一致しないので棄却率に影響しない。
    exact = {}  # ei -> (sc, cov, idfc, v)
    for (sc, cov, idfc, ei, v) in scored:
        if ei not in exact and normalize(v) == qn:
            exact[ei] = (sc, cov, idfc, v)
    if len(exact) == 1:
        ei = next(iter(exact))
        sc, cov, idfc, v = exact[ei]
        entry = corpus.entries[ei]
        result.update({
            "status": "FOUND",
            "id": entry["id"],
            "answer": entry["a"],
            "score": round(sc, 3),
            "coverage": round(cov, 3),
            "idf_coverage": round(idfc, 3),
            "matched_variant": v,
            "reason": "exact-match",
        })
        return result

    if best is None:
        result["reason"] = "no candidate passed coverage gate"
        return result

    sc, cov, idfc, ei, v = best
    # --- ambiguity gate ---
    # 採用 entry と次点 (別 id) entry の IDF重み付き被覆率の差で「団子(曖昧)」を弾く。
    # STT 誤認識で内容語が崩れ「〜は必要ですか」等の敬語尾だけ残ると複数 FAQ に等しく
    # マッチ (同点) するため勝者が立たない。その場合は自信なし＝NOT_FOUND (→有人転送) に倒す。
    best_entry_idfc = max(ic for (s2, c2, ic, e2, v2) in scored if e2 == ei)
    other_idfcs = [ic for (s2, c2, ic, e2, v2) in scored if e2 != ei]
    competitor_idfc = max(other_idfcs) if other_idfcs else 0.0
    margin = best_entry_idfc - competitor_idfc
    if margin < MIN_IDF_MARGIN:
        result["reason"] = (
            f"ambiguous: idf-margin {round(margin, 3)} < {MIN_IDF_MARGIN} "
            f"(top={corpus.entries[ei]['id']} idfc={round(best_entry_idfc, 3)} "
            f"vs next {round(competitor_idfc, 3)})"
        )
        result["score"] = round(sc, 3)
        result["coverage"] = round(cov, 3)
        result["idf_margin"] = round(margin, 3)
        return result

    entry = corpus.entries[ei]
    result.update({
        "status": "FOUND",
        "id": entry["id"],
        "answer": entry["a"],
        "score": round(sc, 3),
        "coverage": round(cov, 3),
        "idf_coverage": round(idfc, 3),
        "idf_margin": round(margin, 3),
        "matched_variant": v,
    })
    return result


# =============================================================================
# 発話の揺れ前処理 (会話的前置き/言い直し/反復を切り出す) — script.js と 1:1
# whole がNOT_FOUNDのとき、節分割して「クリーンな質問節」を exact-match に乗せるための候補生成。
# =============================================================================
SENTENCE_SPLIT_CHARS = set("。．.!！?？\n\r")
# 言い直しマーカー: これ以降を採用 (「駐車場じゃなくて駐輪場」→「駐輪場」)。長い順。
CORRECTION_MARKERS = ["間違えました", "まちがえました", "ごめんなさい", "すみません",
                      "ではなくて", "じゃなくて", "間違えた", "やっぱり", "嘘です", "うそです"]
# 逆接マーカー: これ以降を採用 (「…たいんですけれども10分前で…」→「10分前で…」)。長い順。
CONJUNCTION_MARKERS = ["けれども", "けれど", "んですが", "のですが", "ですが", "ますが", "けど"]


def _collapse_repeat(s: str) -> str:
    """同一文の単純反復 (STT 二重認識) を 1 回に畳む。"""
    n = len(s)
    half = n // 2
    while half >= 4:
        if s[:half] == s[half:half * 2] and half * 2 >= n - 2:
            return s[:half]
        half -= 1
    return s


def _segment_candidates(raw: str) -> list[str]:
    """raw 発話 → 照合候補 (whole / 反復畳み / 文・言い直し・逆接で切った後続節)。順序保持・重複除去。"""
    cands: list[str] = []

    def push(x: str) -> None:
        x = x.strip()
        if x and x not in cands:
            cands.append(x)

    base = raw.strip()
    push(base)
    push(_collapse_repeat(base))
    # 文区切り
    pieces, buf = [], ""
    for ch in base:
        if ch in SENTENCE_SPLIT_CHARS:
            pieces.append(buf); buf = ""
        else:
            buf += ch
    pieces.append(buf)
    for p in pieces:
        for m in CORRECTION_MARKERS:
            idx = p.rfind(m)
            if idx >= 0:
                p = p[idx + len(m):]
        for m in CONJUNCTION_MARKERS:
            idx = p.rfind(m)
            if idx >= 0:
                p = p[idx + len(m):]
        push(p)
    return cands


def search(question: str, corpus: Corpus) -> dict:
    """質問文 → 判定。NO_QUESTION 前段ゲート → whole 照合 → (NOT_FOUND 時) 節分割フォールバック。
    節フォールバックは exact-match を最優先、次に score 最大の FOUND を採用 (whole が FOUND なら即返す)。
    戻り値: {"status": "FOUND"|"NOT_FOUND"|"NO_QUESTION", "id":..., "answer":..., ...}"""
    # --- NO_QUESTION 前段ゲート (whole のみ) ---
    if detect_no_question(question):
        return {"status": "NO_QUESTION", "id": "NO_QUESTION", "answer": "NO_QUESTION",
                "score": 0.0, "coverage": 0.0, "top": [], "reason": "no-question pre-gate"}

    whole = _match_query(question, corpus)
    if whole["status"] == "FOUND":
        return whole

    # --- 発話の揺れフォールバック: 節ごとに照合し最良 FOUND を採用 ---
    qn_whole = normalize(question)
    best = None  # (rank, score, result); rank: exact-match=2 / その他 FOUND=1
    for c in _segment_candidates(question):
        if normalize(c) == qn_whole:
            continue  # whole は評価済み
        r = _match_query(c, corpus)
        if r["status"] != "FOUND":
            continue
        rank = 2 if r.get("reason") == "exact-match" else 1
        sc = r.get("score", 0.0)
        if best is None or (rank, sc) > (best[0], best[1]):
            best = (rank, sc, r)
    if best is not None:
        res = dict(best[2])
        res["reason"] = (str(res.get("reason", "")) + " (segment)").strip()
        return res
    return whole


def load_corpus(path: Path | None = None) -> Corpus:
    p = path or (HERE / "faq_sample.json")
    return Corpus(json.loads(p.read_text(encoding="utf-8")))


# プローブ質問 (期待値設計用)。実機テストケースはこの実測結果から選ぶ。
PROBE_QUESTIONS = [
    "駐車場はありますか",          # parking 完全一致
    "駐車場の場所を教えてください",  # parking 言い換え
    "車を停めるところはありますか",  # parking 弱い言い換え
    "受付時間を教えて",            # hours 完全一致
    "診療は何時までですか",        # hours 言い換え
    "保険証は必要ですか",          # insurance 完全一致
    "クレジットカードは使えますか",  # payment 完全一致
    "カードで支払えますか",        # payment 言い換え
    "面会時間を教えて",            # visiting 完全一致
    "子供を診てもらえますか",      # pediatrics 完全一致
    "紹介状はいりますか",          # referral 言い換え
    "今日の天気はどうですか",      # off-topic → NOT_FOUND 期待
    "あのー、えっと",              # filler → NOT_FOUND 期待
    "はい",                        # too short → NOT_FOUND 期待
]


def main(argv: list[str]) -> int:
    corpus = load_corpus()
    if len(argv) >= 1 and argv[0] != "--probe":
        r = search(argv[0], corpus)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    # --probe (既定)
    print(f"# corpus: {len(corpus.entries)} entries / {corpus.n} variant-docs / avgdl={corpus.avgdl:.2f}")
    print(f"# gate: MIN_COVERAGE={MIN_COVERAGE} MIN_QUERY_CHARS={MIN_QUERY_CHARS} k1={BM25_K1} b={BM25_B}\n")
    for q in PROBE_QUESTIONS:
        r = search(q, corpus)
        top = r["top"][0] if r["top"] else {}
        print(f"{r['status']:9} id={str(r['id']):12} score={r['score']:<7} cov={r['coverage']:<6} | {q}")
        if r["status"] == "NOT_FOUND" and r["top"]:
            print(f"          (best: id={top.get('id')} score={top.get('score')} cov={top.get('coverage')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
