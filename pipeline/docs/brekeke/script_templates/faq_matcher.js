// Script Template: faq_matcher （横断FAQ・在slot質問検知用）
// ★ engine は認定済 modules/faq_matcher/script.js と **verbatim**（master#198系・NO_QUESTION前段ゲート+揺れフォールバック込）。
//   差し替えたのは設定行 QUESTION_SOURCE / FAQ_NOTE_NAME を {{INPUT_MODULE}}/{{FAQ_NOTE}} に置換した点のみ。
//   LOGIC を編集したら modules/faq_matcher/ を更新し oracle+受入を再実行のうえ本テンプレへ再同期。
// プレースホルダー: {{INPUT_MODULE}}=直前STTモジュール名 / {{FAQ_NOTE}}=FAQ Note名(例 drjoy.faq)
// 出力: ^NO_QUESTION$ / <答え本文> / ^NOT_FOUND$ / ^ERROR$（横断: NO_QUESTION・NOT_FOUND・ERROR→次へ / 答え→回答#data#後に同聴取へ復帰）
// =============================================================================
// FAQ Matcher — @General$Script モジュールに直接貼り付けて使う版
// =============================================================================
// 役割: 患者の発話 (直前 STT の文字起こし) を、Brekeke Note 内の FAQ 仮想 DB に対して
//   NFKC 正規化 + 文字 2-gram + BM25 + coverage しきい値で照合し、
//   「答えるべき FAQ があれば答え本文を、無ければ NOT_FOUND を」返す。
//   OpenAI / 外部 API / エンベディングを一切使わない決定論 RAG。
//
// 出力 (= jumps):
//   ^NO_QUESTION$ ← 「特にありません/大丈夫です」等の否定/終了応答。FAQ 検索より前に分離する前段ゲート
//   <答え本文>   ← FOUND。Re-confirmation node data (module=本モジュール) の #data# で発話する
//   ^NOT_FOUND$  ← 該当 FAQ なし / 質問でない / 短すぎる → フォールバック (有人転送等)
//   ^ERROR$      ← Note 不在・JSON 破損・内部例外 → 安全側フォールバック
//   ※ jumps は ^ERROR$ / ^NOT_FOUND$ / ^NO_QUESTION$ を先に並べ、最後に catch-all ^.+$ (= 答え本文) を置く
//
// 正本ロジックは oracle.py と 1:1。アルゴリズムを変えたら oracle.py も同時に直し、
// test_oracle.py + 実機受入 (acceptance_test/) を再実行すること。
// =============================================================================

// =============================================================================
// CONFIG — 配置・施設ごとに調整
// =============================================================================
// 質問文の取得元:
//   "module:<STTモジュール名>"  ← 本番。直前 STT の結果を $runner.getModuleResult で読む
//   "<リテラル質問文>"          ← テスト注入 (受入テストフローが 1 ケースずつ上書きする)
var QUESTION_SOURCE = "module:{{INPUT_MODULE}}";

var FAQ_NOTE_NAME    = "{{FAQ_NOTE}}";   // FAQ 仮想 DB の Brekeke Note 名 (JSON 配列)
var SYNONYM_NOTE_NAME = "";           // 任意。シノニム辞書 Note 名 ("" で無効)
var MIN_COVERAGE     = "0.5";         // 質問 bigram のうちマッチ FAQ に含まれる割合の下限
var MIN_QUERY_CHARS  = "3";           // 正規化後この文字数未満は質問とみなさず NOT_FOUND
var MIN_IDF_MARGIN   = "0.12";        // 採用entryと次点entryの idf-coverage 差の下限。未満は曖昧→NOT_FOUND
var BM25_K1          = "1.2";
var BM25_B           = "0.75";

// =============================================================================
// LOGIC — 編集禁止 (バグ修正・機能追加時は元 repo 側を更新し oracle.py と同期)
// =============================================================================
var NoteUtils  = Java.type("com.brekeke.pbx.common.NoteUtils");
var Normalizer = Java.type("java.text.Normalizer");
var NForm      = Java.type("java.text.Normalizer$Form");
var logger     = $runner.getLogger();

var minCoverage   = parseFloat(MIN_COVERAGE);
var minQueryChars = parseInt(MIN_QUERY_CHARS, 10);
var minIdfMargin  = parseFloat(MIN_IDF_MARGIN);
var k1            = parseFloat(BM25_K1);
var b             = parseFloat(BM25_B);

// 正規化時に除去する文字 (oracle.py の STRIP_CHARS と完全一致)。長音 ー(U+30FC) は残す。
var STRIP = {};
(function () {
    var s = " \t\r\n　。、，．！？!?,.・…〜~「」『』（）()【】[]｜|‐-—―\"'`：:；;／/＼\\＿_";
    for (var i = 0; i < s.length; i++) STRIP[s.charAt(i)] = true;
})();

function normalize(str) {
    if (str === null || str === undefined) return "";
    var s = "" + Normalizer.normalize("" + str, NForm.NFKC);
    s = s.toLowerCase();
    var out = "";
    for (var i = 0; i < s.length; i++) {
        var c = s.charAt(i);
        if (!STRIP[c]) out += c;
    }
    return out;
}

function bigrams(str) {
    var n = normalize(str);
    if (n.length === 0) return [];
    if (n.length === 1) return [n];
    var arr = [];
    for (var i = 0; i < n.length - 1; i++) arr.push(n.substring(i, i + 2));
    return arr;
}

// 質問 bigram の重複除去キー
function distinct(toks) {
    var seen = {}, out = [];
    for (var i = 0; i < toks.length; i++) {
        if (!seen[toks[i]]) { seen[toks[i]] = true; out.push(toks[i]); }
    }
    return out;
}

// =============================================================================
// NO_QUESTION 前段ゲート — oracle.py の detect_no_question と 1:1 (リストも完全一致)
// 終話質問への否定/終了応答 (「ありません」系) を FAQ 検索前に分離し NO_QUESTION を返す。
// FAQ コーパス (Note) には依存しない (= 単独モジュールで完結)。
// =============================================================================
var NOQ_MAX_NORM_LEN = 16;
var NO_QUESTION_PHRASES = [
    "特にありません", "特にないです", "質問はありません", "質問はないです",
    "聞きたいことはありません", "もう大丈夫です", "大丈夫です", "結構です",
    "以上です", "特にございません",
    "ありません", "ございません", "ないです", "ない", "なし",
    "特にない", "特になし", "大丈夫", "結構", "以上",
    "問題ない", "問題ないです", "質問なし", "質問はない",
    "わかりました", "了解です", "了解しました", "もういいです", "もういい",
    "けっこう", "けっこうです", "だいじょうぶ", "だいじょうぶです",
    "いじょう", "いじょうです", "もんだいない"
];
var NO_QUESTION_SUFFIXES = [
    "ありません", "ございません", "ないです", "ない", "なし",
    "大丈夫", "だいじょうぶ", "結構", "けっこう", "以上", "いじょう",
    "問題ない", "もんだいない"
];
var NO_QUESTION_FILLERS = [
    "えーと", "えっと", "えと", "えーっと", "あのー", "あの", "うーん", "うんと",
    "うん", "まあ", "まぁ", "その", "ええと", "ええ", "んー", "んと", "えー", "あー"
];
var NO_QUESTION_TRAILERS = [
    "ですね", "ですよ", "でーす", "です", "だね", "だよ", "だ",
    "ねー", "よー", "ね", "よ", "な", "わ"
];

// 正規化済み集合/配列 (oracle.py の _NOQ_* と同一)
var NOQ_SET = {};
(function () {
    for (var i = 0; i < NO_QUESTION_PHRASES.length; i++) NOQ_SET[normalize(NO_QUESTION_PHRASES[i])] = true;
})();
function normList(arr) { var o = []; for (var i = 0; i < arr.length; i++) o.push(normalize(arr[i])); return o; }
var NOQ_SUFFIXES_N = normList(NO_QUESTION_SUFFIXES);
var NOQ_FILLERS_N  = normList(NO_QUESTION_FILLERS);
var NOQ_TRAILERS_N = normList(NO_QUESTION_TRAILERS);

function strStartsWith(s, p) { return p.length > 0 && s.length > p.length && s.substring(0, p.length) === p; }
function strEndsWith(s, suf) { return suf.length > 0 && s.length >= suf.length && s.substring(s.length - suf.length) === suf; }

function stripLeadingFillers(n) {
    var changed = true;
    while (changed) {
        changed = false;
        for (var i = 0; i < NOQ_FILLERS_N.length; i++) {
            var f = NOQ_FILLERS_N[i];
            if (strStartsWith(n, f)) { n = n.substring(f.length); changed = true; }
        }
    }
    return n;
}
function stripTrailers(n) {
    var changed = true;
    while (changed) {
        changed = false;
        for (var i = 0; i < NOQ_TRAILERS_N.length; i++) {
            var t = NOQ_TRAILERS_N[i];
            if (t.length > 0 && n.length > t.length && strEndsWith(n, t)) { n = n.substring(0, n.length - t.length); changed = true; }
        }
    }
    return n;
}

// True = NO_QUESTION (質問なし)。real question は疑問終止「か」ガードで必ず False。
function detectNoQuestion(question) {
    var n = normalize(question);
    if (n.length === 0) return false;
    n = stripLeadingFillers(n);
    n = stripTrailers(n);
    if (n.length === 0) return false;
    if (strEndsWith(n, "か")) return false;       // 疑問終止 → 質問 (誤検知の最重要ガード)
    if (NOQ_SET[n]) return true;
    if (n.length <= NOQ_MAX_NORM_LEN) {
        for (var i = 0; i < NOQ_SUFFIXES_N.length; i++) {
            if (strEndsWith(n, NOQ_SUFFIXES_N[i])) return true;
        }
    }
    return false;
}

function buildCorpus(faqList) {
    var docs = [];  // {ei, v, toks}
    for (var ei = 0; ei < faqList.length; ei++) {
        var q = faqList[ei].q;
        var variants = Array.isArray(q) ? q : [q];
        for (var vi = 0; vi < variants.length; vi++) {
            docs.push({ ei: ei, v: variants[vi], nv: normalize(variants[vi]), toks: bigrams(variants[vi]) });
        }
    }
    var df = {}, totalLen = 0;
    for (var d = 0; d < docs.length; d++) {
        var toks = docs[d].toks;
        totalLen += toks.length;
        var seen = {};
        for (var t = 0; t < toks.length; t++) {
            var tk = toks[t];
            if (!seen[tk]) { seen[tk] = true; df[tk] = (df[tk] || 0) + 1; }
        }
    }
    return { docs: docs, n: docs.length, df: df, avgdl: docs.length ? totalLen / docs.length : 0 };
}

function idf(corpus, term) {
    var d = corpus.df[term] || 0;
    return Math.log(1 + (corpus.n - d + 0.5) / (d + 0.5));
}

function bm25(corpus, qkeys, docToks) {
    var dl = docToks.length, dtf = {};
    for (var i = 0; i < docToks.length; i++) { var t = docToks[i]; dtf[t] = (dtf[t] || 0) + 1; }
    var score = 0;
    for (var k = 0; k < qkeys.length; k++) {
        var term = qkeys[k];
        var f = dtf[term] || 0;
        if (f === 0) continue;
        var denom = f + k1 * (1 - b + b * (corpus.avgdl ? dl / corpus.avgdl : 0));
        score += idf(corpus, term) * (f * (k1 + 1)) / denom;
    }
    return score;
}

function coverage(qkeys, docToks) {
    if (qkeys.length === 0) return 0;
    var dset = {};
    for (var i = 0; i < docToks.length; i++) dset[docToks[i]] = true;
    var hit = 0;
    for (var k = 0; k < qkeys.length; k++) if (dset[qkeys[k]]) hit++;
    return hit / qkeys.length;
}

// 質問 bigram のうちマッチした分の IDF 質量比 (oracle.py idf_coverage と同一)。
// ありふれた敬語尾は IDF が小さく寄与せず、珍しい内容語のマッチを強く反映する。ambiguity gate 用。
function idfCoverage(corpus, qkeys, docToks) {
    if (qkeys.length === 0) return 0;
    var dset = {};
    for (var i = 0; i < docToks.length; i++) dset[docToks[i]] = true;
    var num = 0, den = 0;
    for (var k = 0; k < qkeys.length; k++) {
        var w = idf(corpus, qkeys[k]);
        den += w;
        if (dset[qkeys[k]]) num += w;
    }
    return den ? num / den : 0;
}

// 質問文の取得 ("module:<STT名>" なら直前 STT 結果、それ以外はリテラル)
function resolveQuestion(src) {
    if (("" + src).indexOf("module:") === 0) {
        var mod = ("" + src).substring(7);
        try {
            var r = $runner.getModuleResult(mod);
            logger.info("[FAQ] getModuleResult(" + mod + ") => [" + ((r === null || r === undefined) ? "null" : ("" + r)) + "]");
            return (r === null || r === undefined) ? "" : ("" + r);
        } catch (e) {
            logger.warn("[FAQ] getModuleResult failed: " + (e && e.message ? e.message : e));
            return "";
        }
    }
    return "" + src;  // リテラル (テスト注入)
}

// =============================================================================
// 1 クエリ照合本体 — oracle.py の _match_query と 1:1。戻り値 = {found,exact,score,output,logmsg}
// =============================================================================
function matchQuery(question, corpus, faqList) {
    var qn = normalize(question);
    var qkeys = distinct(bigrams(question));

    if (qn.length < minQueryChars) {
        return { found: false, exact: false, score: 0, output: "NOT_FOUND",
                 logmsg: "NOT_FOUND (too short " + qn.length + "<" + minQueryChars + ")" };
    }

    var best = null;
    var perEntryIdfc = {};
    var exactByEntry = {};
    for (var d = 0; d < corpus.docs.length; d++) {
        var doc = corpus.docs[d];
        var sc = bm25(corpus, qkeys, doc.toks);
        var cov = coverage(qkeys, doc.toks);
        var idfc = idfCoverage(corpus, qkeys, doc.toks);
        if (perEntryIdfc[doc.ei] === undefined || idfc > perEntryIdfc[doc.ei]) perEntryIdfc[doc.ei] = idfc;
        if (doc.nv === qn && exactByEntry[doc.ei] === undefined) exactByEntry[doc.ei] = { sc: sc, cov: cov };
        if (cov >= minCoverage && sc > 0) {
            if (best === null || sc > best.sc) best = { sc: sc, cov: cov, idfc: idfc, ei: doc.ei };
        }
    }

    // exact-match short-circuit
    var exactIds = [];
    for (var ek in exactByEntry) { if (exactByEntry.hasOwnProperty(ek)) exactIds.push(ek); }
    if (exactIds.length === 1) {
        var exEntry = faqList[parseInt(exactIds[0], 10)];
        var exInfo = exactByEntry[exactIds[0]];
        return { found: true, exact: true, score: exInfo.sc, output: exEntry.a,
                 logmsg: "FOUND id=" + exEntry.id + " (exact-match) score=" + exInfo.sc.toFixed(3) + " cov=" + exInfo.cov.toFixed(3) };
    }

    if (best === null) {
        return { found: false, exact: false, score: 0, output: "NOT_FOUND",
                 logmsg: "NOT_FOUND (no candidate >= coverage " + minCoverage + ")" };
    }

    // ambiguity gate
    var bestEntryIdfc = perEntryIdfc[best.ei];
    var competitorIdfc = 0;
    for (var pk in perEntryIdfc) {
        if (!perEntryIdfc.hasOwnProperty(pk)) continue;
        if (parseInt(pk, 10) === best.ei) continue;
        if (perEntryIdfc[pk] > competitorIdfc) competitorIdfc = perEntryIdfc[pk];
    }
    var margin = bestEntryIdfc - competitorIdfc;
    if (margin < minIdfMargin) {
        return { found: false, exact: false, score: best.sc, output: "NOT_FOUND",
                 logmsg: "NOT_FOUND (ambiguous: idf-margin " + margin.toFixed(3) + " < " + minIdfMargin
                    + " top=" + faqList[best.ei].id + " idfc=" + bestEntryIdfc.toFixed(3) + " vs next " + competitorIdfc.toFixed(3) + ")" };
    }

    var entry = faqList[best.ei];
    return { found: true, exact: false, score: best.sc, output: entry.a,
             logmsg: "FOUND id=" + entry.id + " score=" + best.sc.toFixed(3) + " cov=" + best.cov.toFixed(3) + " idfMargin=" + margin.toFixed(3) };
}

// =============================================================================
// 発話の揺れ前処理 (会話的前置き/言い直し/反復を切り出す) — oracle.py と 1:1
// =============================================================================
var SENTENCE_SPLIT = "。．.!！?？\n\r";
var CORRECTION_MARKERS = ["間違えました", "まちがえました", "ごめんなさい", "すみません",
    "ではなくて", "じゃなくて", "間違えた", "やっぱり", "嘘です", "うそです"];
var CONJUNCTION_MARKERS = ["けれども", "けれど", "んですが", "のですが", "ですが", "ますが", "けど"];

function collapseRepeat(s) {
    var n = s.length;
    var half = Math.floor(n / 2);
    while (half >= 4) {
        if (s.substring(0, half) === s.substring(half, half * 2) && half * 2 >= n - 2) return s.substring(0, half);
        half--;
    }
    return s;
}

function segmentCandidates(raw) {
    var cands = [];
    function push(x) {
        x = ("" + x).replace(/^[\s　]+|[\s　]+$/g, "");
        if (x.length === 0) return;
        for (var i = 0; i < cands.length; i++) if (cands[i] === x) return;
        cands.push(x);
    }
    var base = ("" + raw).replace(/^[\s　]+|[\s　]+$/g, "");
    push(base);
    push(collapseRepeat(base));
    var pieces = [], buf = "";
    for (var i = 0; i < base.length; i++) {
        var c = base.charAt(i);
        if (SENTENCE_SPLIT.indexOf(c) >= 0) { pieces.push(buf); buf = ""; }
        else buf += c;
    }
    pieces.push(buf);
    for (var pi = 0; pi < pieces.length; pi++) {
        var p = pieces[pi];
        for (var mi = 0; mi < CORRECTION_MARKERS.length; mi++) {
            var m = CORRECTION_MARKERS[mi];
            var idx = p.lastIndexOf(m);
            if (idx >= 0) p = p.substring(idx + m.length);
        }
        for (var cj = 0; cj < CONJUNCTION_MARKERS.length; cj++) {
            var cm = CONJUNCTION_MARKERS[cj];
            var idx2 = p.lastIndexOf(cm);
            if (idx2 >= 0) p = p.substring(idx2 + cm.length);
        }
        push(p);
    }
    return cands;
}

// ---------- main ----------
var question = resolveQuestion(QUESTION_SOURCE);
logger.info("[FAQ] question=[" + question + "] note=" + FAQ_NOTE_NAME
    + " minCov=" + minCoverage + " minChars=" + minQueryChars);

// --- NO_QUESTION 前段ゲート (FAQ 検索・Note 読み取りより前に分離) ---
if (detectNoQuestion(question)) {
    logger.info("[FAQ] => NO_QUESTION (no-question pre-gate)");
    $runner.setResult("NO_QUESTION");
    return;
}

// Note 読み取り → JSON parse
var faqList;
try {
    if (!NoteUtils.exists(FAQ_NOTE_NAME)) {
        logger.error("[FAQ] note not found: " + FAQ_NOTE_NAME);
        $runner.setResult("ERROR");
        return;
    }
    var raw = NoteUtils.read(FAQ_NOTE_NAME);
    faqList = JSON.parse("" + raw);
} catch (e) {
    logger.error("[FAQ] note read/parse error: " + (e && e.message ? e.message : e));
    $runner.setResult("ERROR");
    return;
}
if (!faqList || !faqList.length) {
    logger.error("[FAQ] empty faq list");
    $runner.setResult("ERROR");
    return;
}

var corpus = buildCorpus(faqList);

// --- whole 照合 (NO_QUESTION 前段ゲートは上で処理済み) ---
var rWhole = matchQuery(question, corpus, faqList);
logger.info("[FAQ] whole => " + rWhole.logmsg);
if (rWhole.found) {
    $runner.setResult(rWhole.output);
    return;
}

// --- 発話の揺れフォールバック: 節分割して最良 FOUND (exact-match 優先) を採用 ---
// 会話的前置き・言い直し・反復で whole の coverage/margin が落ちたケースを、クリーンな節で救う。
var qnWhole = normalize(question);
var bestSeg = null;  // {rank, score, output, label}  rank: exact-match=2 / その他 FOUND=1
var cands = segmentCandidates(question);
for (var ci2 = 0; ci2 < cands.length; ci2++) {
    var cand = cands[ci2];
    if (normalize(cand) === qnWhole) continue;  // whole は評価済み
    var rr = matchQuery(cand, corpus, faqList);
    if (!rr.found) continue;
    var rank = rr.exact ? 2 : 1;
    if (bestSeg === null || rank > bestSeg.rank || (rank === bestSeg.rank && rr.score > bestSeg.score)) {
        bestSeg = { rank: rank, score: rr.score, output: rr.output, label: cand };
    }
}
if (bestSeg !== null) {
    logger.info("[FAQ] => FOUND via segment [" + bestSeg.label + "] (rank=" + bestSeg.rank + " score=" + bestSeg.score.toFixed(3) + ")");
    $runner.setResult(bestSeg.output);
    return;
}

logger.info("[FAQ] => " + rWhole.output + " (no segment matched)");
$runner.setResult(rWhole.output);
