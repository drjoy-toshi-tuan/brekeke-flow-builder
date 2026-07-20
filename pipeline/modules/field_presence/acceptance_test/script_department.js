// Script Template: field_presence （L1 答え取得判定・OpenAI不使用）
// 商談デモ「フリー発話受付」の各聴取STT直後に置く。入力STTテキストを kind 別に検査し、
// 当該フィールドの答えが取れていれば "PRESENT"、無ければ "ABSENT" を setResult する。
// 背後の雑音質問が混ざっていても、答えがあれば PRESENT（答え優先）。
// parity: modules/field_presence/oracle.py（同一辞書・同一手順）。
// プレースホルダー:
//   {{INPUT_MODULE}}  = 入力元モジュール名（聴取の STT。getModuleResult フォールバック）
//   {{CONTEXT_FIELD}} = STT 結果が保存される context 名（本命の読み取り元）
//   {{KIND}}          = department / date / phone / birthday / card のいずれか
// Nashorn(ES5.1)想定: String.normalize / includes / arrow / let / const / テンプレート文字列 不使用。

var KIND = "department";   // P6受入用に解決（正本テンプレは {{KIND}}）

var DEPARTMENTS = [
  ["循環器内科", ["循環器内科", "循環器"]],
  ["呼吸器内科", ["呼吸器内科"]],
  ["消化器内科", ["消化器内科"]],
  ["脳神経内科", ["脳神経内科", "神経内科"]],
  ["腎臓内科", ["腎臓内科"]],
  ["血液内科", ["血液内科"]],
  ["糖尿病内分泌内科", ["糖尿病内分泌内科", "糖尿病", "内分泌"]],
  ["精神神経科", ["精神神経科", "精神科", "心療内科"]],
  ["小児科", ["小児科", "こども"]],
  ["整形外科", ["整形外科"]],
  ["脳神経外科", ["脳神経外科"]],
  ["心臓血管外科", ["心臓血管外科", "心臓外科"]],
  ["呼吸器外科", ["呼吸器外科"]],
  ["消化器外科", ["消化器外科"]],
  ["形成外科", ["形成外科"]],
  ["美容外科", ["美容外科"]],
  ["乳腺外科", ["乳腺外科", "乳腺"]],
  ["皮膚科", ["皮膚科"]],
  ["泌尿器科", ["泌尿器科", "泌尿器"]],
  ["眼科", ["眼科"]],
  ["耳鼻咽喉科", ["耳鼻咽喉科", "耳鼻科", "耳鼻"]],
  ["婦人科", ["産婦人科", "婦人科"]],
  ["産科", ["産科"]],
  ["放射線科", ["放射線科", "放射線"]],
  ["麻酔科", ["麻酔科", "ペインクリニック"]],
  ["リハビリテーション科", ["リハビリテーション科", "リハビリ"]],
  ["歯科", ["歯科", "歯医者"]],
  ["内科", ["内科"]],
  ["外科", ["外科"]]
];

var SEPARATORS = ["-", "－", "ー", "‐", "–", "—", "―", " ", "　", "\t", "\r", "\n"];
var RELATIVE_DATES = ["再来週", "来週", "今週", "今度", "明々後日", "しあさって", "明後日", "あさって",
                      "明日", "あした", "本日", "今日", "きょう"];
var NO_CARD_PHRASES = ["持っていない", "持ってない", "持ってません", "持っていません",
                       "ありません", "ないです", "なしです", "ございません",
                       "わからない", "わかりません", "不明", "なし"];

function z2h(s) {
  var out = "";
  for (var i = 0; i < s.length; i++) {
    var o = s.charCodeAt(i);
    if (o >= 0xFF10 && o <= 0xFF19) { out += String.fromCharCode(o - 0xFEE0); }
    else { out += s.charAt(i); }
  }
  return out;
}

function stripSep(s) {
  for (var i = 0; i < SEPARATORS.length; i++) { s = s.split(SEPARATORS[i]).join(""); }
  return s;
}

function hasDepartment(s) {
  var keys = [];
  for (var d = 0; d < DEPARTMENTS.length; d++) {
    var ks = DEPARTMENTS[d][1];
    for (var k = 0; k < ks.length; k++) { keys.push(ks[k]); }
  }
  keys.sort(function (a, b) { return b.length - a.length; });
  for (var j = 0; j < keys.length; j++) { if (s.indexOf(keys[j]) >= 0) return true; }
  return false;
}

function hasAny(s, arr) {
  for (var i = 0; i < arr.length; i++) { if (s.indexOf(arr[i]) >= 0) return true; }
  return false;
}

function hasDate(s) {
  if (hasAny(s, RELATIVE_DATES)) return true;
  if (/\d{1,2}\s*月/.test(s)) return true;
  if (/\d{1,2}\s*日/.test(s)) return true;
  if (/\d{1,4}\s*年/.test(s)) return true;
  return false;
}

function hasPhone(s) {
  var d = stripSep(z2h(s));
  return /0\d{9,10}/.test(d);
}

function hasBirthday(s) {
  var t = z2h(s);
  if (/(昭和|平成|令和|大正)\s*\d{1,2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日/.test(t)) return true;
  if (/(?:19|20)\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日/.test(t)) return true;
  return false;
}

function hasCard(s) {
  var d = stripSep(z2h(s));
  if (/\d{3,10}/.test(d)) return true;
  return hasAny(s, NO_CARD_PHRASES);
}

function detect(kind, raw) {
  if (raw == null) return false;
  if (typeof raw === "object" && raw.text != null) raw = raw.text;
  var s = z2h(String(raw)).replace(/^\s+|\s+$/g, "");
  if (kind === "department") return hasDepartment(s);
  if (kind === "date") return hasDate(s);
  if (kind === "phone") return hasPhone(s);
  if (kind === "birthday") return hasBirthday(s);
  if (kind === "card") return hasCard(s);
  return false;
}

// ── 入力取得: STT 保存 context（{{CONTEXT_FIELD}}）優先 → getModuleResult（{{INPUT_MODULE}}）fallback ──
var rawIn = null;
try {
  if (typeof $runner.getContextModel === "function") {
    var cm = $runner.getContextModel();
    if (cm) {
      if (typeof cm.get === "function") rawIn = cm.get("{{CONTEXT_FIELD}}");
      else if (cm["{{CONTEXT_FIELD}}"] != null) rawIn = cm["{{CONTEXT_FIELD}}"];
    }
  }
} catch (e) { /* fallthrough */ }
try { if ((rawIn == null || rawIn === "") && typeof $runner.getContext === "function") rawIn = $runner.getContext("{{CONTEXT_FIELD}}"); } catch (e) { /* fallthrough */ }
if (rawIn == null || rawIn === "") { try { rawIn = $runner.getModuleResult("{{INPUT_MODULE}}"); } catch (e) { rawIn = null; } }

var out = detect(KIND, rawIn) ? "PRESENT" : "ABSENT";
$runner.getLogger().info("[FIELD-PRESENCE] kind=" + KIND + " in=" + rawIn + " => " + out);
$runner.setResult(out);
