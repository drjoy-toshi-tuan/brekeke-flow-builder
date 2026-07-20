// Script Template: inquiry_extractor （用件抽出 決定論パーサ v2・OpenAI不使用）
// 商談デモ「フリー発話受付」の 用件抽出。自由発話の STT テキストを直接解析し、
// 用件種別＋各スロット値＋取得有無フラグ＋復唱用の用件概要文へ分解して context へ撒く。
// parity: modules/inquiry_extractor/oracle.py（同一辞書・同一手順・同順）。仕様 = 同 REQUIREMENTS.md。
// プレースホルダー:
//   {{INPUT_MODULE}}  = 入力元モジュール名（用件フリー聴取の STT。fallback 読込用）
//   {{CONTEXT_FIELD}} = STT 結果が保存される context 名（用件フリー聴取の save_to）。本命はここから読む。
// Nashorn(ES5.1)想定: String.normalize / includes / arrow / let / const / テンプレート文字列 不使用。
var OUT_SEP = "‖";     // U+2016 canonical の項目区切り
var FLAG_SEP = "@";        // value@flag
var SLOTS = ["診療科", "予約希望日", "予約日時", "氏名", "連絡先", "生年月日", "診察券番号"];

var KW_CANCEL = ["取消", "取り消し", "キャンセル", "やめ", "中止"];
var KW_CHANGE = ["変更", "変えたい", "ずらし", "ずらす", "振替", "振り替え", "日にちを変", "時間を変", "予定を変"];
var KW_NEW = ["新規", "初めて", "はじめて", "予約", "受診したい", "診てもらい", "みてもらい", "診ていただき", "かかりたい"];

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

var ERAS = ["昭和", "平成", "令和", "大正"];
var RELATIVE_DATES = ["再来週", "来週", "今週", "今度", "明々後日", "しあさって", "明後日", "あさって",
                      "明日", "あした", "本日", "今日", "きょう"];
var HONORIFICS = ["さん", "様", "さま", "君", "ちゃん"];
var NAME_PREFIX = ["私は", "わたしは", "名前は", "なまえは", "私、", "わたし、"];
var NAME_SUFFIX = ["と申します", "ともうします", "と言います", "といいます", "と申し上げます"];
var NAME_BOUNDARY = ["。", "、", " ", "　", "は", "が", "を", "の", "\t", "\n", "\r"];
var SEPARATORS = ["-", "－", "ー", "‐", "–", "—", "―", " ", "　", "\t", "\r", "\n"];

function inArr(arr, ch) { for (var i = 0; i < arr.length; i++) { if (arr[i] === ch) return true; } return false; }
function containsAny(s, kws) { for (var i = 0; i < kws.length; i++) { if (s.indexOf(kws[i]) >= 0) return true; } return false; }

function z2hDigits(s) {
  var out = "";
  for (var i = 0; i < s.length; i++) {
    var o = s.charCodeAt(i);
    if (o >= 0xFF10 && o <= 0xFF19) { out += String.fromCharCode(o - 0xFEE0); }
    else { out += s.charAt(i); }
  }
  return out;
}

function normalize(raw) {
  if (raw == null) return "";
  if (typeof raw === "object" && raw.text != null) raw = raw.text;
  var s = String(raw);
  s = z2hDigits(s);
  return s.replace(/^\s+|\s+$/g, "");
}

function stripSeparators(s) {
  for (var i = 0; i < SEPARATORS.length; i++) { s = s.split(SEPARATORS[i]).join(""); }
  return s;
}

function decideIntent(s) {
  if (containsAny(s, KW_CANCEL)) return "キャンセル";
  if (containsAny(s, KW_CHANGE)) return "変更";
  if (containsAny(s, KW_NEW)) return "新規";
  return "問い合わせ";
}

function extractDepartment(s) {
  var keys = [];
  for (var d = 0; d < DEPARTMENTS.length; d++) {
    var canon = DEPARTMENTS[d][0], ks = DEPARTMENTS[d][1];
    for (var k = 0; k < ks.length; k++) { keys.push([ks[k], canon]); }
  }
  keys.sort(function (a, b) { return b[0].length - a[0].length; });
  for (var j = 0; j < keys.length; j++) { if (s.indexOf(keys[j][0]) >= 0) return keys[j][1]; }
  return "";
}

function extractPhone(s) {
  var d = stripSeparators(s);
  var m = d.match(/0\d{9,10}/);
  return m ? m[0] : "";
}

function extractBirthday(s) {
  var m = s.match(/(?:昭和|平成|令和|大正)\s*\d{1,2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日/);
  if (m) return m[0];
  m = s.match(/(?:19|20)\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日/);
  if (m) return m[0];
  return "";
}

function spaces(n) { var s = ""; for (var i = 0; i < n; i++) { s += " "; } return s; }

function extractBookingDate(s, birthday) {
  var work = s;
  if (birthday) work = work.split(birthday).join(spaces(birthday.length));
  var parts = [];
  for (var r = 0; r < RELATIVE_DATES.length; r++) {
    var rd = RELATIVE_DATES[r];
    var idx = work.indexOf(rd);
    if (idx >= 0) { parts.push([idx, rd]); work = work.substring(0, idx) + spaces(rd.length) + work.substring(idx + rd.length); }
  }
  var re1 = /\d{1,2}\s*月\s*\d{1,2}\s*日/g, mm;
  while ((mm = re1.exec(work)) !== null) { parts.push([mm.index, mm[0]]); }
  var re2 = /[月火水木金土日]曜日?/g;
  while ((mm = re2.exec(work)) !== null) { parts.push([mm.index, mm[0]]); }
  var re3 = /(?:午前|午後)?\s*\d{1,2}\s*時(?:\s*\d{1,2}\s*分)?(?:半)?/g;
  while ((mm = re3.exec(work)) !== null) { parts.push([mm.index, mm[0]]); }
  if (parts.length === 0) return "";
  parts.sort(function (a, b) { return a[0] - b[0]; });
  var out = "";
  for (var p = 0; p < parts.length; p++) { out += parts[p][1]; }
  return out.replace(/^\s+|\s+$/g, "");
}

function cleanName(name) {
  name = name.replace(/^\s+|\s+$/g, "");
  for (var b = 0; b < NAME_BOUNDARY.length; b++) {
    if (NAME_BOUNDARY[b] === " " || NAME_BOUNDARY[b] === "　" || NAME_BOUNDARY[b] === "\t" ||
        NAME_BOUNDARY[b] === "\n" || NAME_BOUNDARY[b] === "\r" || NAME_BOUNDARY[b] === "。" || NAME_BOUNDARY[b] === "、") {
      name = name.split(NAME_BOUNDARY[b]).join("");
    }
  }
  var changed = true;
  while (changed) {
    changed = false;
    for (var h = 0; h < HONORIFICS.length; h++) {
      var hh = HONORIFICS[h];
      if (name.length >= hh.length && name.lastIndexOf(hh) === name.length - hh.length) {
        name = name.substring(0, name.length - hh.length); changed = true;
      }
    }
  }
  if (name.indexOf("先生") >= 0) return "";
  if (name.length > 10) return "";
  return name;
}

function extractName(s) {
  for (var i = 0; i < NAME_SUFFIX.length; i++) {
    var suf = NAME_SUFFIX[i];
    var idx = s.indexOf(suf);
    if (idx > 0) {
      var head = s.substring(0, idx);
      var cut = -1;
      for (var b = 0; b < NAME_BOUNDARY.length; b++) {
        var p = head.lastIndexOf(NAME_BOUNDARY[b]);
        if (p > cut) cut = p;
      }
      var cand = (cut >= 0) ? head.substring(cut + 1) : head;
      var nm = cleanName(cand);
      if (nm) return nm;
    }
  }
  var stops = ["です", "と申", "と言", "。", "、", " ", "　"];
  for (var pre = 0; pre < NAME_PREFIX.length; pre++) {
    var pm = NAME_PREFIX[pre];
    var idx2 = s.indexOf(pm);
    if (idx2 >= 0) {
      var rest = s.substring(idx2 + pm.length);
      var cut2 = rest.length;
      for (var st = 0; st < stops.length; st++) {
        var q = rest.indexOf(stops[st]);
        if (q >= 0 && q < cut2) cut2 = q;
      }
      var nm2 = cleanName(rest.substring(0, cut2));
      if (nm2) return nm2;
    }
  }
  return "";
}

function extractCardNumber(s, phone, birthday) {
  // 発話は順不同なので「先頭の数字列」では生年月日の年などを誤取得する。
  // 数字列を全部拾ってから確からしさで選ぶ:
  //   1) 電話番号・生年月日の年（西暦4桁）は診察券番号ではないので候補から外す
  //   2) 「診察券」ラベル以降で最も近い数字列を最有力とする（ラベル近接＝確からしさ）
  //   3) ラベル以降に無ければ、残った最初の数字列にフォールバック
  if (s.indexOf("診察券") < 0) return "";
  var d = stripSeparators(s);
  if (phone) d = d.split(phone).join(" ");
  var bYear = "";
  if (birthday) { var ym = stripSeparators(birthday).match(/(?:19|20)\d{2}/); if (ym) bYear = ym[0]; }
  var labelIdx = d.indexOf("診察券");
  var cands = [];
  var re = /\d{3,10}/g, mm;
  while ((mm = re.exec(d)) !== null) {
    if (bYear && mm[0] === bYear) continue;
    cands.push([mm.index, mm[0]]);
  }
  if (cands.length === 0) return "";
  for (var i = 0; i < cands.length; i++) {
    if (labelIdx >= 0 && cands[i][0] >= labelIdx) return cands[i][1];
  }
  return cands[0][1];
}

function joined(items) {
  var out = [];
  for (var i = 0; i < items.length; i++) { if (items[i]) out.push(items[i]); }
  return out.join("、");
}

function summary(intent, vals) {
  var body;
  if (intent === "新規") {
    body = joined([vals["診療科"], vals["予約希望日"]]);
    return body ? ("新規のご予約、" + body + "、でお間違いないですか？") : "新規のご予約、でお間違いないですか？";
  }
  if (intent === "変更") {
    body = joined([vals["予約日時"]]);
    return body ? ("ご予約の変更、" + body + "、でお間違いないですか？") : "ご予約の変更、でお間違いないですか？";
  }
  if (intent === "キャンセル") {
    body = joined([vals["予約日時"]]);
    return body ? ("ご予約のキャンセル、" + body + "、でお間違いないですか？") : "ご予約のキャンセル、でお間違いないですか？";
  }
  return "お問い合わせ、でお間違いないですか？";
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

var s = normalize(rawIn);
var intent = decideIntent(s);
var dept = extractDepartment(s);
var phone = extractPhone(s);
var bday = extractBirthday(s);
var bdate = extractBookingDate(s, bday);
var card = extractCardNumber(s, phone, bday);
var vals = {
  "診療科": dept,
  "予約希望日": (intent === "新規") ? bdate : "",
  "予約日時": (intent === "変更" || intent === "キャンセル") ? bdate : "",
  "氏名": "", "連絡先": phone, "生年月日": bday, "診察券番号": card
};
function flagOf(v) { return (v !== "") ? "取得済" : "未取得"; }
var summ = summary(intent, vals);

// canonical（setResult / 受入テスト照合）
var out = intent;
for (var si = 0; si < SLOTS.length; si++) { out += OUT_SEP + vals[SLOTS[si]] + FLAG_SEP + flagOf(vals[SLOTS[si]]); }
out += OUT_SEP + "SUMMARY:" + summ;

// context 撒き出し（production）
// ※ context名は ASCII 必須（日本語だと saveContextModel2DB の宣言が通らない・2026-06-16確認）。
// ※ <%key%>(CMR module1Name / TTS) は getSystemVariableValue で読まれ、resolver 不在時は
//   $runner のオブジェクトストアにフォールバックする → 下流 CMR/announcement が <%asciiKey%> で読む
//   routing/復唱/取得フラグ(classification/inquirySummary/各_Acquired)は必ず $runner.setObject で撒く。
//   用件区分は標準 CLASSIFICATION フィールド context=classification（旧 inquiryType(TEXT) を統合・2026-06-17）。
//   値は range_values の value 文字列（新規/変更/キャンセル/問い合わせ）と一致＝Dr.JOY「用件区分」に表示。
//   $ivr.setObject は $ivr 専用ストアで <%key%> から読めない／save2db は Dr.JOY画面のDB記録のみ（2026-06-17 実機確定）。
//   save2db(saveCtx) は Dr.JOY 通話結果画面の記録用に併存。抽出スロット値も save2db する
//   （自由発話で埋まり聴取がスキップされた値が画面に乗るように・型は hearing の save-* と一致）。
// 内部スロット名(日本語) → 保存 context 名(ASCII) の対応:
var CTX_VAL = { "診療科": "clinicalDepartment", "予約希望日": "preferredDate", "予約日時": "reservationDate",
                "氏名": "patientName", "連絡先": "additionalPhoneNumber", "生年月日": "patientDateOfBirth", "診察券番号": "medicalCardNumber" };
var CTX_FLAG = { "診療科": "deptAcquired", "予約希望日": "preferredDateAcquired", "予約日時": "reservationDateAcquired",
                 "氏名": "nameAcquired", "連絡先": "contactAcquired", "生年月日": "dobAcquired", "診察券番号": "cardAcquired" };
// スロット値の displayType（hearing 内の save-* サブモジュールと一致させる＝Dr.JOY画面の型と整合）
var CTX_TYPE = { "診療科": "DEPARTMENT", "予約希望日": "DATE", "予約日時": "DATE",
                 "氏名": "TEXT", "連絡先": "PHONE_NUMBER", "生年月日": "DATE_OF_BIRTH", "診察券番号": "TEXT" };
function saveCtx(name, val, type) {
  if (val == null || val === "") return;   // saveContext2DB は空文字を拒否
  try {
    $ivr.exec("save2db", "save", JSON.stringify({ contextField: { contextName: name, displayType: type || "TEXT", value: String(val) } }));
  } catch (e) { $runner.getLogger().info("[SCRIPT-INQUIRY] saveCtx skipped " + name + ": " + e); }
}
saveCtx("classification", intent, "CLASSIFICATION");
saveCtx("inquirySummary", summ, "TEXT");
for (var ti = 0; ti < SLOTS.length; ti++) {
  var sk = SLOTS[ti];
  // 抽出できたスロット値も Dr.JOY 画面へ save2db（聴取がスキップされても値が画面に乗るように）
  saveCtx(CTX_VAL[sk], vals[sk], CTX_TYPE[sk]);
  saveCtx(CTX_FLAG[sk], flagOf(vals[sk]), "TEXT");   // 取得済/未取得（常に非空・チェック_*CMRが <%…Acquired%> で読む）
}
try {
  if (typeof $runner !== "undefined" && $runner && $runner.setObject) {
    $runner.setObject("classification", intent);
    $runner.setObject("inquirySummary", summ);
    for (var tj = 0; tj < SLOTS.length; tj++) {
      var kk = SLOTS[tj];
      $runner.setObject(CTX_VAL[kk], vals[kk]);
      $runner.setObject(CTX_FLAG[kk], flagOf(vals[kk]));
    }
  }
} catch (e) { $runner.getLogger().info("[SCRIPT-INQUIRY] setObject skipped: " + e); }

$runner.getLogger().info("[SCRIPT-INQUIRY] in=" + s + " intent=" + intent + " out=" + out);
$runner.setResult(out);
