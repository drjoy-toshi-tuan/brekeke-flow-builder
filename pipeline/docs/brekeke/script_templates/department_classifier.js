// [SCRIPT-DEPT] 診療科 決定論分類（OpenAI_診療科 置換）。施設別の科辞書・最長一致。
// parity: department_classifier/oracle.py（同一辞書・同一手順・同順タイブレーク）。
// 入力: $runner.getModuleResult(SOURCE_MODULE) / 出力: 科名 | "登録なし"(わからない) | "NO_RESULT"
// Nashorn(ES5.1)想定: String.normalize 不使用。診療科入力は漢字/ひらがな科名・読みのため、
//   全角数字→半角・空白/記号除去・末尾定型語除去 の限定正規化で十分（NFKCの実効サブセット）。
// @part-id: department_classifier
// @engine-version: v2
//
// 【テンプレート（穴あき版・A3 #2 出口）】v1 module（modules/department_classifier/script.js・"入力_診療科"
//   ハードコード・deployed）と論理同一だが、複数診療科 hearing に対応するため入力を SOURCE_MODULE へ wiring 化
//   した v2 engine。build_script が充填する。
//   - wiring（設定行・hash 除外）: {{INPUT_MODULE}} … 直前の入力（STT）モジュール名。var SOURCE_MODULE に充填。
//   - spec（規格・受入必須・@spec ブロック・hash 認定対象）:
//       {{DEPARTMENTS}} … **施設別**の [正準名, [同義語/読み...]] 配列リテラル。マスター標榜科辞書（v1 の
//                         30科辞書が源）から当該施設の科を subset/拡張して著作する。
//       WAKARANAI / TRAILERS … 普遍（全施設共通・施設別に変えない）。
//   出力は 正準科名 / "登録なし"(わからない検知) / "NO_RESULT"。設計書の科分岐に build_script が next 配線。
//   ※ engine v2 と各施設 spec の認定（certified_hashes 登録）は Brekeke 実機 P6 後（node-gated）。
var SOURCE_MODULE = "{{INPUT_MODULE}}";

// @spec-begin
var WAKARANAI = ["わからない","わかりません","わからん","不明","決まっていない","決まってない","きまっていない","未定","忘れ","わすれ"];
var DEPARTMENTS = {{DEPARTMENTS}};
var TRAILERS = ["でお願いします","をお願いします","おねがいします","になります","です","でお願い","が希望","を希望","希望","の方","のほう","科目","かな","かも"];
// @spec-end

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  s = s.replace(/[０-９]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  var strip = [" ","　","「","」","、","。","・","．","，","”","“","\t","\r","\n"];
  for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
  s = s.replace(/^\s+|\s+$/g, "");
  var changed = true;
  while (changed) {
    changed = false;
    for (var t = 0; t < TRAILERS.length; t++) {
      var tt = TRAILERS[t].split("・").join("");
      if (tt && s.length > tt.length && s.lastIndexOf(tt) === s.length - tt.length) {
        s = s.substring(0, s.length - tt.length); changed = true;
      }
    }
  }
  return s;
}

function decide(s) {
  if (s === "") return "NO_RESULT";
  for (var i = 0; i < WAKARANAI.length; i++) {
    if (s.indexOf(WAKARANAI[i].split("・").join("")) >= 0) return "登録なし";
  }
  if (/^[0-9]+$/.test(s)) return "NO_RESULT";
  var keys = [];
  for (var d = 0; d < DEPARTMENTS.length; d++) {
    var canon = DEPARTMENTS[d][0]; var ks = DEPARTMENTS[d][1];
    for (var k = 0; k < ks.length; k++) { keys.push([ks[k], canon, keys.length]); }
  }
  keys.sort(function(a, b) { return (b[0].length - a[0].length) || (a[2] - b[2]); });
  for (var j = 0; j < keys.length; j++) { if (s.indexOf(keys[j][0]) >= 0) return keys[j][1]; }
  return "NO_RESULT";
}

var r = $runner.getModuleResult(SOURCE_MODULE);
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var norm = nrm(raw);
var out = decide(norm);
$runner.getLogger().info("[SCRIPT-DEPT] raw=" + raw + " norm=" + norm + " out=" + out);
$runner.setResult(out);
