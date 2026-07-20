// Script Template: drjoy_finalize （終端 正規化＋Dr.JOY再保存＋ダンプ）
// 終話直前に置き、Dr.JOY へ送られる各フィールドを「正規化 → save2db＋$runner へ上書き → トレース出力」する。
// 背景: Dr.JOY 画面 = 通話中 save2db の累積（[[reference_brekeke_savedatatodrjoy]]）。聴取経路は生STTが
//   save2db されるため（例「診察券番号は12345です」）、抽出経路（クリーン）と品質が非対称になる。
//   フォームは contextName キーの upsert なので、終端でクリーン値を再 save2db すれば最終的に画面が揃う。
// 正規化ロジックは modules/field_normalizer/oracle.py と parity（同一辞書・同一手順・oracle 33/33）。
//
// 値の読み: getSystemVariableValue($runner=抽出値) 優先・空なら getModuleResult(STT=聴取値)。
// 冪等ガード: 正規化結果が空なら raw を維持（既にクリーンな抽出値を消さない）。
//
// プレースホルダー:
//   {{DUMP_MAP_JSON}} = [[label, contextName, sttModule, kind, displayType], ...]
//     kind: name / phone / card / birthday / department / date / raw（raw=無変換）
// Nashorn(ES5.1)想定: endsWith/startsWith/includes/normalize 等 不使用。

var logger = $runner.getLogger();
var MAP = {{DUMP_MAP_JSON}};

var HONORIFICS = ["さん", "様", "さま", "君", "ちゃん"];
var NAME_PREFIX = ["私は", "わたしは", "名前は", "なまえは", "氏名は", "私、", "わたし、"];
var NAME_SUFFIX = ["と申します", "ともうします", "と言います", "といいます", "と申し上げます",
                   "と言う名前です", "という名前です", "です", "でございます"];
var SEPARATORS = ["-", "－", "ー", "‐", "–", "—", "―", " ", "　", "\t", "\r", "\n"];
var DATE_TAIL = ["でお願いいたします", "でお願いします", "にお願いします", "をお願いします",
                 "でお願い", "の予約です", "に予約です", "の予約", "に予約", "です", "でございます"];
var TRIM_CHARS = "、。 　\t\r\n";
var DEPARTMENTS = [
  ["循環器内科", ["循環器内科", "循環器"]], ["呼吸器内科", ["呼吸器内科"]], ["消化器内科", ["消化器内科"]],
  ["脳神経内科", ["脳神経内科", "神経内科"]], ["腎臓内科", ["腎臓内科"]], ["血液内科", ["血液内科"]],
  ["糖尿病内分泌内科", ["糖尿病内分泌内科", "糖尿病", "内分泌"]], ["精神神経科", ["精神神経科", "精神科", "心療内科"]],
  ["小児科", ["小児科", "こども"]], ["整形外科", ["整形外科"]], ["脳神経外科", ["脳神経外科"]],
  ["心臓血管外科", ["心臓血管外科", "心臓外科"]], ["呼吸器外科", ["呼吸器外科"]], ["消化器外科", ["消化器外科"]],
  ["形成外科", ["形成外科"]], ["美容外科", ["美容外科"]], ["乳腺外科", ["乳腺外科", "乳腺"]],
  ["皮膚科", ["皮膚科"]], ["泌尿器科", ["泌尿器科", "泌尿器"]], ["眼科", ["眼科"]],
  ["耳鼻咽喉科", ["耳鼻咽喉科", "耳鼻科", "耳鼻"]], ["婦人科", ["産婦人科", "婦人科"]], ["産科", ["産科"]],
  ["放射線科", ["放射線科", "放射線"]], ["麻酔科", ["麻酔科", "ペインクリニック"]],
  ["リハビリテーション科", ["リハビリテーション科", "リハビリ"]], ["歯科", ["歯科", "歯医者"]],
  ["内科", ["内科"]], ["外科", ["外科"]]
];

function endsWith(s, suf) { return s.length >= suf.length && s.lastIndexOf(suf) === s.length - suf.length; }
function startsWith(s, pre) { return s.lastIndexOf(pre, 0) === 0; }
function trimChars(s) {
  var a = 0, b = s.length;
  while (a < b && TRIM_CHARS.indexOf(s.charAt(a)) >= 0) a++;
  while (b > a && TRIM_CHARS.indexOf(s.charAt(b - 1)) >= 0) b--;
  return s.substring(a, b);
}
function z2h(s) {
  var out = "";
  for (var i = 0; i < s.length; i++) {
    var o = s.charCodeAt(i);
    out += (o >= 0xFF10 && o <= 0xFF19) ? String.fromCharCode(o - 0xFEE0) : s.charAt(i);
  }
  return out;
}
function stripSep(s) { for (var i = 0; i < SEPARATORS.length; i++) { s = s.split(SEPARATORS[i]).join(""); } return s; }

function normName(s) {
  s = s.replace(/^\s+|\s+$/g, "");
  for (var p = 0; p < NAME_PREFIX.length; p++) { if (startsWith(s, NAME_PREFIX[p])) { s = s.substring(NAME_PREFIX[p].length); break; } }
  var cut = s.length;
  for (var q = 0; q < NAME_SUFFIX.length; q++) { var i = s.indexOf(NAME_SUFFIX[q]); if (i >= 0 && i < cut) cut = i; }
  s = s.substring(0, cut);
  var changed = true;
  while (changed) {
    changed = false;
    for (var h = 0; h < HONORIFICS.length; h++) { if (endsWith(s, HONORIFICS[h]) && s.length > HONORIFICS[h].length) { s = s.substring(0, s.length - HONORIFICS[h].length); changed = true; } }
  }
  return trimChars(s);
}
function normPhone(s) { var m = stripSep(z2h(s)).match(/0\d{9,10}/); return m ? m[0] : ""; }
function normCard(s) { var m = stripSep(z2h(s)).match(/\d{3,10}/); return m ? m[0] : ""; }
// 和暦元号 → 西暦の基準年（西暦 = base + 元号年）。oracle.py ERA_BASE と一致。
var ERA_BASE = { "令和": 2018, "平成": 1988, "昭和": 1925, "大正": 1911 };
function pad(n, w) { var s = "" + n; while (s.length < w) { s = "0" + s; } return s; }
function fmtDate(y, mo, d) { return pad(y, 4) + "-" + pad(mo, 2) + "-" + pad(d, 2) + " 00:00:00"; }
function normBirthday(s) {
  s = z2h(s);
  var m = s.match(/(昭和|平成|令和|大正)\s*(\d{1,2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (m) { return fmtDate(ERA_BASE[m[1]] + parseInt(m[2], 10), parseInt(m[3], 10), parseInt(m[4], 10)); }
  m = s.match(/((?:19|20)\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
  if (m) { return fmtDate(parseInt(m[1], 10), parseInt(m[2], 10), parseInt(m[3], 10)); }
  return "";
}
function normDepartment(s) {
  var keys = [];
  for (var d = 0; d < DEPARTMENTS.length; d++) { var ks = DEPARTMENTS[d][1]; for (var k = 0; k < ks.length; k++) { keys.push([ks[k], DEPARTMENTS[d][0]]); } }
  keys.sort(function (a, b) { return b[0].length - a[0].length; });
  for (var j = 0; j < keys.length; j++) { if (s.indexOf(keys[j][0]) >= 0) return keys[j][1]; }
  return "";
}
function normDate(s) {
  s = trimChars(z2h(s).replace(/^\s+|\s+$/g, ""));
  var changed = true;
  while (changed) {
    changed = false;
    for (var t = 0; t < DATE_TAIL.length; t++) { if (endsWith(s, DATE_TAIL[t]) && s.length > DATE_TAIL[t].length) { s = s.substring(0, s.length - DATE_TAIL[t].length); changed = true; } }
  }
  return trimChars(s);
}
function normalize(kind, raw) {
  if (raw == null) return "";
  raw = "" + raw;
  if (kind === "name") return normName(raw);
  if (kind === "phone") return normPhone(raw);
  if (kind === "card") return normCard(raw);
  if (kind === "birthday") return normBirthday(raw);
  if (kind === "department") return normDepartment(raw);
  if (kind === "date") return normDate(raw);
  return raw;
}

function readRaw(ctx, stt) {
  var v = null;
  try { v = $ivr.exec("system-variable", "getSystemVariableValue", ctx); } catch (e) { v = null; }
  if ((v == null || v === "") && stt) { try { v = $runner.getModuleResult(stt); } catch (e2) { v = null; } }
  return (v == null) ? "" : ("" + v);
}
function saveClean(ctx, val, dtype) {
  try {
    $ivr.exec("save2db", "save", JSON.stringify({ contextField: { contextName: ctx, displayType: dtype || "TEXT", value: String(val) } }));
  } catch (e) { logger.info("[DRJOY-FINALIZE] save skipped " + ctx + ": " + e); }
  try { if ($runner && $runner.setObject) $runner.setObject(ctx, val); } catch (e2) {}
}

var parts = [];
for (var i = 0; i < MAP.length; i++) {
  var label = MAP[i][0], ctx = MAP[i][1], stt = MAP[i][2] || "", kind = MAP[i][3] || "raw", dtype = MAP[i][4] || "TEXT";
  var raw = readRaw(ctx, stt);
  var clean = normalize(kind, raw);
  var fin = (clean !== "") ? clean : raw;        // 冪等ガード: 空なら raw 維持
  if (fin !== "") { saveClean(ctx, fin, dtype); } // クリーン値を Dr.JOY へ上書き（空は保存しない）
  parts.push(label + "=" + fin);
}
var dump = parts.join(" | ");
logger.info("[DRJOY-FINALIZE] " + dump);
$runner.setResult(dump);
