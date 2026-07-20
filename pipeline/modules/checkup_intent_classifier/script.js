// [SCRIPT-INTENT] 健診CC 用件 決定論分類（用件確認/遅刻種別確認の generate_by_OpenAI 置換）。
// parity: checkup_intent_classifier/oracle.py（同一辞書・同一手順・同一順序）。テストの正は acceptance_test/cases.tsv。
// 入力: $runner.getModuleResult(SOURCE_MODULE)
// 出力: "予約"|"変更"|"キャンセル"|"雇用時健診"|"遅刻"|"その他"|"NO_RESULT"（市の健診/特定健診は廃止用語）
// Nashorn(ES5.1)想定。※ SOURCE_MODULE / SCOPE の2行のみ組込先ごとの設定行。これ以外の行の改変は再受入。
// SCOPE=第一層TTSが提示した出口に活性カテゴリを絞る（full=用件確認 / lateness=遅刻種別確認）。
// @part-id: checkup_intent_classifier
// @engine-version: v2
var SOURCE_MODULE = "__SOURCE_MODULE__";
var SCOPE = "__SCOPE__";
// @template CONTEXT_NAME: 保存先 context 名（wiring・空なら保存スキップ）
var CONTEXT_NAME = "__CONTEXT_NAME__";
// @template CONTEXT_DISPLAY_TYPE: context の displayType（wiring）
var CONTEXT_DISPLAY_TYPE = "__CONTEXT_DISPLAY_TYPE__";

// 表記揺れ畳み込み（正規化の最終段。順序固定: 長い語から）
// @spec-begin
var FOLDINGS = [
  ["健康診断", "健診"],
  ["健康診査", "健診"],
  ["検診", "健診"],
  ["一番", "1"],
  ["二番", "2"],
  ["三番", "3"],
  ["四番", "4"],
  ["1番", "1"],
  ["2番", "2"],
  ["3番", "3"],
  ["4番", "4"]
];

var WAKARANAI_MARKERS = [
  "わからない", "わかりません", "わかんない", "分からない", "分かりません"
];
// @spec-end

// カテゴリ語彙（マスタ）。走査順・活性集合は SCOPES が文脈ごとに規定する。
// @spec-begin
var CATEGORY_KEYS = {
  "その他": ["その他", "そのほか", "問い合わせ", "問合せ", "問いあわせ", "質問", "聞きたい", "伺いたい", "相談", "確認"],
  "変更": ["変更", "変えたい", "変えて", "ずらしたい", "ずらして", "日にちを変え", "日程を変え", "時間を変え"],
  "キャンセル": ["キャンセル", "取り消し", "取消", "取りやめ", "中止", "やめたい", "やめます", "やめて"],
  "雇用時健診": ["雇用時健診", "雇用時の健診", "雇い入れ", "雇入れ", "入社時健診", "入社前健診", "入社前の健診", "入社時の健診"],
  "遅刻": ["遅刻", "時刻", "遅れ", "間に合いません", "間に合わない", "間に合わなそう"],
  "予約": ["予約", "受けたい", "受診したい", "申し込み", "申込"]
};
// SCOPE 別の活性カテゴリ（評価順）。full=用件確認（現行と同一順序）/ lateness=遅刻種別確認（遅刻 or 変更・キャンセル）
var SCOPES = {
  "full": ["その他", "変更", "キャンセル", "雇用時健診", "遅刻", "予約"],
  "lateness": ["遅刻", "変更", "キャンセル"]
};
// DTMF も SCOPE 別。lateness はTTS非提示（speech-only）→数字は NO_RESULT。
var DTMF_BY_SCOPE = {
  "full": { "1": "予約", "2": "変更", "3": "キャンセル", "4": "その他" },
  "lateness": {}
};
// @spec-end

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  s = "" + Java.type("java.text.Normalizer").normalize(s, Java.type("java.text.Normalizer$Form").NFKC); // NFKC: 半角カナ/全半/互換を正規化（FAQ Matcher と同方式）
  s = s.replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  s = s.replace(/[Ａ-Ｚａ-ｚ]/g, function (c) {
    var h = String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
    return h.toLowerCase();
  });
  s = s.replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
  var strip = ["、", "。", "，", "．", ",", ".", "・", "･", ":", ";", "：", "；",
               "!", "！", "?", "？", "…", "‥", "〜", "～", "「", "」", "『", "』",
               "(", ")", "（", "）", "[", "]", "【", "】", "<", ">", "＜", "＞",
               "\"", "'", "“", "”", "‘", "’", "｢", "｣", "-",
               "　", " ", "\t", "\r", "\n"];
  for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
  for (var f = 0; f < FOLDINGS.length; f++) { s = s.split(FOLDINGS[f][0]).join(FOLDINGS[f][1]); }
  return s;
}

function decide(s, scope) {
  var cats = SCOPES[scope];
  if (cats == null) cats = SCOPES["full"];   // 未知スコープは full にフォールバック（設定行未注入の保険）
  // 1. 空
  if (s === "") return "NO_RESULT";
  // 2. 数字のみ（DTMF 併用・SCOPE 別表。lateness は空＝NO_RESULT）
  if (/^[0-9]+$/.test(s)) {
    var dt = DTMF_BY_SCOPE[scope]; if (dt == null) dt = DTMF_BY_SCOPE["full"];
    return dt.hasOwnProperty(s) ? dt[s] : "NO_RESULT";
  }
  var i, k;
  // 3. わからない検知
  for (i = 0; i < WAKARANAI_MARKERS.length; i++) { if (s.indexOf(WAKARANAI_MARKERS[i]) >= 0) return "NO_RESULT"; }
  // 4. カテゴリ走査（SCOPE の活性カテゴリのみ・評価順・部分一致）
  for (i = 0; i < cats.length; i++) {
    var keys = CATEGORY_KEYS[cats[i]];
    for (k = 0; k < keys.length; k++) { if (s.indexOf(keys[k]) >= 0) return cats[i]; }
  }
  // 5. 不一致
  return "NO_RESULT";
}

var logger = $runner.getLogger();

// === コンテキスト保存関数群（VFB 共通流儀: save2db + setObject + checkpoint。n_choice / checkup_option と同一）===
// @General$Script は subs の save2db を実行しないため、保存はスクリプト内で完結させる（reference_brekeke_script_subs_no_save2db）。
function _saveCheckpoint(value) {
    try { if (!$ivr.connected()) return; $ivr.exec("save2db", "save", JSON.stringify({ contextField: { contextName: "checkpoint", displayType: "TEXT", value: value } })); } catch (e) { logger.error("[saveContext2DB] Checkpoint: " + e); }
}
function _setObj(k, v) { try { $ivr.setObject(k, v); } catch (e) { logger.error("[saveContext2DB] setObj: " + e); } }
function saveContext(val, name, type) {
    var rid = $ivr.getRID(); var mod = $runner.getCurrentModuleName();
    _saveCheckpoint(mod + "_IN"); _setObj("checkpoint." + rid, mod + "_IN");
    if (name && val) { var req = JSON.stringify({ contextField: { contextName: name, displayType: type || "TEXT", value: val } }); logger.info("[saveContext2DB] " + req); try { $ivr.exec("save2db", "save", req); $runner.setObject(name, val); } catch (e) { logger.error("[saveContext2DB] " + e); } }
    _saveCheckpoint(mod + "_OUT"); _setObj("checkpoint." + rid, mod + "_OUT"); _setObj("saveContext." + rid, true);
}
// === END ===

var r = $runner.getModuleResult(SOURCE_MODULE);
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var norm = nrm(raw);
var out = decide(norm, SCOPE);
$runner.getLogger().info("[SCRIPT-INTENT] scope=" + SCOPE + " raw=" + raw + " norm=" + norm + " out=" + out);
$runner.setResult(out);

// コンテキスト保存（スクリプト内で完結。@General$Script は subs の save2db を実行しないため必須）
saveContext(out, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
