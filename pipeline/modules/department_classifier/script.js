// [SCRIPT-DEPT] 診療科 決定論分類 engine v2（universe 構造化・OpenAI_診療科 置換）。
// parity: department_classifier/oracle.py（build/oracle.py v0 = 出荷 sha 9ee1eb01…）。
//   同一レキシコン・同一手順（classify step 1-8）・同順タイブレーク（最長一致 len 降順 + 元順）。
// 入力: $runner.getModuleResult("入力_診療科")
// 出力: canonical 科名 | "AMBIGUOUS" | "OUT_OF_SCOPE" | "登録なし"(わからない) | "NO_RESULT"
//   （施設サブセット FACILITY_OFFERED 指定時のみ canonical+"|OFF_MENU" 併記。既定 null＝oracle 既定と一致）
// Nashorn(ES5.1)想定: String.normalize 不使用。全角ASCII(FF01-FF5E)→半角・空白/記号除去・末尾定型語除去の
//   限定正規化で十分（NFKC の実効サブセット）。store verify.py [C] が本番コーパス 16,053 語で
//   NFKC 経路と classify 出力 100% 一致を実証済み（診療科入力は漢字/かな/カナ科名・読みで
//   NFKC の互換分解が効く文字を含まないため）。
// @part-id: department_classifier
// @engine-version: v2-universe-v0.1
// @spec-begin
var STRIP = [" ","　","「","」","、","。","・","．","，","”","“","\t","\r","\n"];
var TRAILERS = ["でお願いします","をお願いします","おねがいします","になります","です","でお願い","が希望","を希望","希望","の方","のほう","科目","かな","かも","を受診","に行きたい","がいい","でいい"];
var WAKARANAI = ["わからない","わかりません","わからん","不明","決まっていない","決まってない","きまっていない","未定","忘れ","わすれ"];
// スコープ外・具体名（enumerated/WAKARANAI より前＝審美歯科⊃歯科・もの忘れ外来⊃忘れ の誤取り回避）
var OOS_NAMES = ["頭痛外来","禁煙外来","もの忘れ外来","物忘れ外来","発熱外来","渡航外来","女性科","老年科","化学療法科","疼痛緩和科","ペインクリニック科","性感染症科","インプラント科","審美歯科","アンチエイジング"];
// 汎用「○○外来」＝未知の専門外来（enumerated の後で判定＝整形外科外来→整形外科 を守る）
var OOS_SUFFIX = ["外来"];
// 基本科なしで来ると内/外等が決まらない臓器・系統語 → AMBIGUOUS
var AMBIGUOUS_ORGAN = ["消化器","呼吸器","循環器","脳神経","心臓","心臓血管","血管","乳腺","甲状腺","腎臓","肝臓","胆のう","膵臓","胃腸","大腸","頭頸部","神経"];
// ENUMERATED レキシコン（universe canonical -> 一致キー）。oracle.DEPARTMENTS と同順・同内容。
var DEPARTMENTS = [
  ["内科", ["内科"]],
  ["外科", ["外科"]],
  ["精神科", ["精神科","心療内科","精神神経科","せいしんか","しんりょうないか"]],
  ["小児科", ["小児科","しょうにか","しょうに","こども","ようじ"]],
  ["皮膚科", ["皮膚科","ひふか","ひふ"]],
  ["泌尿器科", ["泌尿器科","泌尿器","ひにょうきか","ひにょうき","ひにょう"]],
  ["眼科", ["眼科","がんか","めか"]],
  ["耳鼻咽喉科", ["耳鼻咽喉科","耳鼻いんこう科","耳鼻科","じびいんこうか","じびか","じび","いんこうか"]],
  ["アレルギー科", ["アレルギー科","あれるぎーか","あれるぎー"]],
  ["リウマチ科", ["リウマチ科","りうまちか","りうまち"]],
  ["産婦人科", ["産婦人科","さんふじんか"]],
  ["産科", ["産科","さんか"]],
  ["婦人科", ["婦人科","ふじんか"]],
  ["リハビリテーション科", ["リハビリテーション科","リハビリ科","リハビリ","りはびり","りはびりてーしょん"]],
  ["放射線科", ["放射線科","ほうしゃせんか"]],
  ["放射線治療科", ["放射線治療科","放射線治療","ほうしゃせんちりょう"]],
  ["放射線診断科", ["放射線診断科","放射線診断","ほうしゃせんしんだん"]],
  ["病理診断科", ["病理診断科","病理診断","びょうり"]],
  ["臨床検査科", ["臨床検査科","臨床検査"]],
  ["救急科", ["救急科","救急医学科","きゅうきゅうか","きゅうきゅう"]],
  ["麻酔科", ["麻酔科","ますいか","ますい","ペインクリニック","ぺいん"]],
  ["歯科", ["歯科","歯医者","はいしゃ"]],
  ["小児歯科", ["小児歯科","しょうにしか"]],
  ["矯正歯科", ["矯正歯科","歯科矯正科","きょうせいしか"]],
  ["歯科口腔外科", ["歯科口腔外科","口腔外科","こうくうげか"]],
  ["呼吸器内科", ["呼吸器内科","こきゅうきないか","こきゅうか","こきゅう","こない"]],
  ["循環器内科", ["循環器内科","循環器","じゅんかんきないか","じゅんかんき","じゅんない"]],
  ["消化器内科", ["消化器内科","しょうかきないか","しょうかき","しょうない"]],
  ["腎臓内科", ["腎臓内科","じんぞうないか","じんぞう","じんない"]],
  ["糖尿病・内分泌代謝内科", ["糖尿病内分泌代謝内科","糖尿病代謝内科","内分泌代謝内科","内分泌内科","代謝内科","糖尿病内科","とうにょうびょう","ないぶんぴつ","ないぶん"]],
  ["血液内科", ["血液内科","けつえきないか","けつえき","けつない"]],
  ["脳神経内科", ["脳神経内科","神経内科","のうしんけいないか","しんけいないか","のうない"]],
  ["膠原病リウマチ内科", ["膠原病リウマチ内科","リウマチ膠原病感染内科","膠原病感染内科","膠原病","こうげんびょう"]],
  ["腫瘍内科", ["腫瘍内科","腫瘍治療科","しゅようないか"]],
  ["消化器外科", ["消化器外科","一般消化器外科","一般外科","肝胆膵外科","大腸肛門科","しょうかきげか","いっぱんげか"]],
  ["呼吸器外科", ["呼吸器外科","こきゅうきげか","こげ"]],
  ["心臓血管外科", ["心臓血管外科","心臓外科","しんぞうけっかんげか","しんぞうげか","しんげ"]],
  ["脳神経外科", ["脳神経外科","脳外科","のうしんけいげか","のうげか","のうげ"]],
  ["整形外科", ["整形外科","せいけいげか","せいけい"]],
  ["形成外科", ["形成外科","形成外科美容外科","けいせいげか","けいせい"]],
  ["美容外科", ["美容外科","びようげか"]],
  ["乳腺甲状腺外科", ["乳腺甲状腺外科","乳腺甲状腺","乳腺外科","乳腺","にゅうせん"]],
  ["小児外科", ["小児外科","しょうにげか"]],
  ["耳鼻咽喉科・頭頸部外科", ["耳鼻咽喉科頭頸部外科","頭頸部外科","頭頸部","とうけいぶ"]],
  ["胃腸科", ["胃腸科","いちょうか","いちょう"]],
  ["こう門科", ["こう門科","肛門科","こうもんか"]],
  ["総合診療科", ["総合診療科","総合診療部","総合診療","そうごうしんりょう","そうごう","そうしん"]],
  ["新生児科", ["新生児科","しんせいじか","しんせいじ"]],
  ["小児循環器科", ["小児循環器科","しょうにじゅんかんき"]],
  ["小児心臓血管外科", ["小児心臓血管外科","しょうにしんぞう"]],
  ["脳卒中科", ["脳卒中科","のうそっちゅう"]],
  ["性病科", ["性病科","せいびょうか"]],
  ["気管食道科", ["気管食道科","きかんしょくどう"]],
  ["皮膚泌尿器科", ["皮膚泌尿器科"]]
];
// 生成コンポーザ v0.1（base科 suffix + 修飾語）。順序は oracle._MOD_* の挿入順（安定タイブレーク用）。
var BASE_INNER = ["内科","ないか"];
var BASE_OUTER = ["外科","げか"];
var MOD_INNER = [
  ["循環器","循環器内科"],["消化器","消化器内科"],["呼吸器","呼吸器内科"],
  ["腎臓","腎臓内科"],["血液","血液内科"],["脳神経","脳神経内科"],["神経","脳神経内科"],
  ["糖尿病","糖尿病・内分泌代謝内科"],["内分泌","糖尿病・内分泌代謝内科"],["腫瘍","腫瘍内科"]
];
var MOD_OUTER = [
  ["脳神経","脳神経外科"],["消化器","消化器外科"],["呼吸器","呼吸器外科"],
  ["心臓血管","心臓血管外科"],["心臓","心臓血管外科"],["乳腺","乳腺甲状腺外科"],
  ["甲状腺","乳腺甲状腺外科"],["頭頸部","耳鼻咽喉科・頭頸部外科"],
  ["整形","整形外科"],["形成","形成外科"],["小児","小児外科"]
];
// 略語・別表記の完全一致（bare 略語＝整形/内分泌科/糖尿病…・短キー磁石を作らないため exact のみ）。
var ABBREV = [
  ["整形","整形外科"],
  ["形成","形成外科"],
  ["糖尿病","糖尿病・内分泌代謝内科"],["糖尿","糖尿病・内分泌代謝内科"],
  ["内分泌","糖尿病・内分泌代謝内科"],["内分泌科","糖尿病・内分泌代謝内科"],
  ["内分泌代謝","糖尿病・内分泌代謝内科"],["内分泌代謝科","糖尿病・内分泌代謝内科"],
  ["代謝内分泌","糖尿病・内分泌代謝内科"]
];
// @spec-end

var RESULT_NONE = "NO_RESULT";
var RESULT_WAKARANAI = "登録なし";
var RESULT_AMBIGUOUS = "AMBIGUOUS";
var RESULT_OUT = "OUT_OF_SCOPE";

function delDot(t) { return t.split("・").join(""); }  // "・" 除去（oracle の t.replace("・","")）

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  // 全角 ASCII（U+FF01..FF5E）→ 半角。全角空白 U+3000 は STRIP 側で除去。NFKC の実効サブセット。
  var out = "";
  for (var i = 0; i < s.length; i++) {
    var code = s.charCodeAt(i);
    out += (code >= 0xFF01 && code <= 0xFF5E) ? String.fromCharCode(code - 0xFEE0) : s.charAt(i);
  }
  s = out;
  for (var k = 0; k < STRIP.length; k++) { s = s.split(STRIP[k]).join(""); }
  s = s.replace(/^\s+|\s+$/g, "");
  var changed = true;
  while (changed) {
    changed = false;
    for (var t = 0; t < TRAILERS.length; t++) {
      var tt = delDot(TRAILERS[t]);
      if (tt && s.length > tt.length && s.lastIndexOf(tt) === s.length - tt.length) {
        s = s.substring(0, s.length - tt.length); changed = true;
      }
    }
  }
  return s;
}

// ENUMERATED キーを (key, canon, idx) で展開し len 降順 + 元順で安定ソート（最長一致）。
function buildKeys() {
  var keys = [];
  for (var d = 0; d < DEPARTMENTS.length; d++) {
    var canon = DEPARTMENTS[d][0], ks = DEPARTMENTS[d][1];
    for (var k = 0; k < ks.length; k++) { keys.push([ks[k], canon, keys.length]); }
  }
  keys.sort(function(a, b) { return (b[0].length - a[0].length) || (a[2] - b[2]); });
  return keys;
}
var KEYS = buildKeys();

function matchAbbrev(s) {
  // exact のみ。末尾疑問助詞「か」1字は許容（内分泌か→内分泌）。
  var cands = [s];
  if (s.length > 2 && s.charAt(s.length - 1) === "か") { cands.push(s.substring(0, s.length - 1)); }
  for (var c = 0; c < cands.length; c++) {
    for (var a = 0; a < ABBREV.length; a++) { if (ABBREV[a][0] === cands[c]) return ABBREV[a][1]; }
  }
  return null;
}

function composeGenerative(s) {
  var groups = [[BASE_INNER, MOD_INNER, "内科"], [BASE_OUTER, MOD_OUTER, "外科"]];
  for (var g = 0; g < groups.length; g++) {
    var bases = groups[g][0], modMap = groups[g][1], baseCanon = groups[g][2];
    // modMap を len 降順 + 元順で安定ソート
    var mods = [];
    for (var mi = 0; mi < modMap.length; mi++) { mods.push([modMap[mi][0], modMap[mi][1], mi]); }
    mods.sort(function(a, b) { return (b[0].length - a[0].length) || (a[2] - b[2]); });
    for (var b = 0; b < bases.length; b++) {
      var bk = bases[b];
      if (s === bk) return baseCanon;
      if (s.length > bk.length && s.lastIndexOf(bk) === s.length - bk.length) {
        var prefix = s.substring(0, s.length - bk.length);
        for (var m = 0; m < mods.length; m++) {
          if (prefix.indexOf(mods[m][0]) >= 0) return mods[m][1];
        }
      }
    }
  }
  return null;
}

function inFacility(canon, facility) {
  if (facility == null) return true;
  for (var i = 0; i < facility.length; i++) { if (facility[i] === canon) return true; }
  return false;
}

function classify(raw, facilityOffered) {
  if (facilityOffered === undefined) facilityOffered = null;
  var s = nrm(raw);
  if (s === "") return RESULT_NONE;
  // 1) DTMF 数字のみ
  if (/^[0-9]+$/.test(s)) return RESULT_NONE;
  // 2) スコープ外・具体名
  for (var i = 0; i < OOS_NAMES.length; i++) { if (s.indexOf(OOS_NAMES[i]) >= 0) return RESULT_OUT; }
  // 3) 不明意図
  for (var w = 0; w < WAKARANAI.length; w++) { if (s.indexOf(delDot(WAKARANAI[w])) >= 0) return RESULT_WAKARANAI; }
  // 4) ENUMERATED 最長一致
  for (var j = 0; j < KEYS.length; j++) {
    if (s.indexOf(KEYS[j][0]) >= 0) {
      var canon = KEYS[j][1];
      if (facilityOffered != null && !inFacility(canon, facilityOffered)) return canon + "|OFF_MENU";
      return canon;
    }
  }
  // 4.5) 略語・別表記の完全一致
  var ab = matchAbbrev(s);
  if (ab) {
    if (facilityOffered != null && !inFacility(ab, facilityOffered)) return ab + "|OFF_MENU";
    return ab;
  }
  // 5) 生成合成（v0.1 後置）
  var gg = composeGenerative(s);
  if (gg) return gg;
  // 6) 汎用「○○外来」
  for (var su = 0; su < OOS_SUFFIX.length; su++) { if (s.indexOf(OOS_SUFFIX[su]) >= 0) return RESULT_OUT; }
  // 7) 基本科なしの臓器・系統語 → AMBIGUOUS
  for (var o = 0; o < AMBIGUOUS_ORGAN.length; o++) { if (s.indexOf(AMBIGUOUS_ORGAN[o]) >= 0) return RESULT_AMBIGUOUS; }
  // 8) 不一致
  return RESULT_NONE;
}

// ---- Brekeke ハーネス（wiring・engine/spec 対象外） ----
// v0 出荷スコープ = facility_offered なし（universe 全科をそのまま返す＝oracle 既定 classify(raw, None) と一致）。
// 施設サブセット運用は VFB 側の config 時に facility を差し込む（classify の第2引数＝canonical 配列/カンマ区切り）。
// その際は下の facility を getModuleResult("入力_施設診療科リスト") 等から解決する（engine 再生成不要・wiring のみ）。
var r = $runner.getModuleResult("入力_診療科");
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var facility = null;
var norm = nrm(raw);
var out = classify(raw, facility);
$runner.getLogger().info("[SCRIPT-DEPT] raw=" + raw + " norm=" + norm + " out=" + out);
$runner.setResult(out);
