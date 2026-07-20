// [SCRIPT-AMBIGUITY-GATE] 紛れペア(最小対)の曖昧検出器。決定論分類の多段構成 Stage2（検品）。
// parity: ambiguity_gate/oracle.py（同一アルゴリズム）。テストの正は acceptance_test/cases.tsv。
// 入力: $runner.getModuleResult(SOURCE_MODULE) / GROUP=紛れ候補群名
// 出力: 勝者ラベル | "CONFIRM"（団子→確認ステップへ） | "NO_RESULT"
// 手順: NFKC正規化 → 文字2-gram → member別 IDF被覆率 → トップと次点の idf-margin で分離可否判定。
// Nashorn(ES5.1)想定。java.text.Normalizer で NFKC。faq_matcher と同方式。
// ※ SOURCE_MODULE / GROUP の2行のみ組込先ごとの設定行。これ以外の行の改変は再受入。
// @part-id: ambiguity_gate
// @engine-version: v1
var SOURCE_MODULE = "__SOURCE_MODULE__";
var GROUP = "__GROUP__";

// CONFIG（oracle.py と一致させること）
// @spec-begin
var MIN_QUERY_CHARS = 2;
var MIN_IDF_MARGIN = 0.12;
// @spec-end

// 紛れ候補群（組込先データ。形式: group -> [[label, [variant...]], ...]）。検証用の例を内蔵。
// @spec-begin
var GROUPS = {
  "course_dock": [
    ["1日ドック", ["1日ドック", "日帰りドック", "一日ドック", "日帰り"]],
    ["2日ドック", ["2日ドック", "一泊ドック", "二日ドック", "1泊2日ドック", "泊まりのドック"]]
  ],
  "dept_shoukaki": [
    ["消化器内科", ["消化器内科", "消化器の内科", "胃腸内科"]],
    ["消化器外科", ["消化器外科", "消化器の外科"]]
  ]
};
// @spec-end

var Normalizer = Java.type("java.text.Normalizer");
var NForm = Java.type("java.text.Normalizer$Form");

// NFKC 後に除去する記号・空白（oracle.py STRIP_CHARS と同集合）。長音 ー(U+30FC) は残す。
// @spec-begin
var STRIP = {};
(function () {
  var s = " \t\r\n　、。，．,.・…‥〜~「」『』（）()【】[]＜＞<>｜|‐-—―／/＼\\＿_：:；;！!？?“”‘’\"'`｢｣･";
  for (var i = 0; i < s.length; i++) STRIP[s.charAt(i)] = true;
})();
// @spec-end

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

function distinct(toks) {
  var seen = {}, out = [];
  for (var i = 0; i < toks.length; i++) {
    if (!seen[toks[i]]) { seen[toks[i]] = true; out.push(toks[i]); }
  }
  return out;
}

function idf(df, n, term) {
  var d = df[term] || 0;
  return Math.log(1 + (n - d + 0.5) / (d + 0.5));
}

function idfCoverage(qd, docToks, df, n) {
  if (qd.length === 0) return 0.0;
  var dset = {}, i;
  for (i = 0; i < docToks.length; i++) dset[docToks[i]] = true;
  var num = 0.0, den = 0.0;
  for (i = 0; i < qd.length; i++) {
    var w = idf(df, n, qd[i]);
    den += w;
    if (dset[qd[i]]) num += w;
  }
  return den ? (num / den) : 0.0;
}

function classify(rawValue, group) {
  var members = GROUPS[group];
  if (members == null) return "NO_RESULT";
  var qn = normalize(rawValue);
  if (qn.length < MIN_QUERY_CHARS) return "NO_RESULT";
  var qtoks = bigrams(rawValue);

  // docs + df
  var docs = [], df = {}, i, j, k;
  for (i = 0; i < members.length; i++) {
    var label = members[i][0];
    var variants = members[i][1];
    for (j = 0; j < variants.length; j++) {
      var toks = bigrams(variants[j]);
      docs.push({ label: label, nv: normalize(variants[j]), toks: toks });
      var seen = {};
      for (k = 0; k < toks.length; k++) {
        if (!seen[toks[k]]) { seen[toks[k]] = true; df[toks[k]] = (df[toks[k]] || 0) + 1; }
      }
    }
  }
  var n = docs.length;

  // exact-match 短絡（1ラベルに限るとき）
  var exactSeen = {}, exactCount = 0, exactLabel = "";
  for (i = 0; i < docs.length; i++) {
    if (docs[i].nv === qn && !exactSeen[docs[i].label]) {
      exactSeen[docs[i].label] = true; exactCount++; exactLabel = docs[i].label;
    }
  }
  if (exactCount === 1) return exactLabel;

  // member別 最大 idf_coverage
  var qd = distinct(qtoks);
  var bestByLabel = {}, labelOrder = [];
  for (i = 0; i < docs.length; i++) {
    var ic = idfCoverage(qd, docs[i].toks, df, n);
    var lb = docs[i].label;
    if (!(lb in bestByLabel)) { bestByLabel[lb] = ic; labelOrder.push(lb); }
    else if (ic > bestByLabel[lb]) { bestByLabel[lb] = ic; }
  }
  // top-2
  var bestL = "", bestIc = -1, secondIc = -1;
  for (i = 0; i < labelOrder.length; i++) {
    var v = bestByLabel[labelOrder[i]];
    if (v > bestIc) { secondIc = bestIc; bestIc = v; bestL = labelOrder[i]; }
    else if (v > secondIc) { secondIc = v; }
  }
  if (bestIc <= 0.0) return "NO_RESULT";
  if (secondIc < 0) secondIc = 0.0;
  if ((bestIc - secondIc) < MIN_IDF_MARGIN) return "CONFIRM";
  return bestL;
}

var r = $runner.getModuleResult(SOURCE_MODULE);
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var out = classify(raw, GROUP);
$runner.getLogger().info("[SCRIPT-AMBIGUITY-GATE] group=" + GROUP + " raw=" + raw + " out=" + out);
$runner.setResult(out);
