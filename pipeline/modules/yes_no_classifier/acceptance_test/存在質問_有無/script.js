// [SCRIPT-YESNO] Yes/No 決定論分類（ECHO_YESNO_PROMPT 置換）。完全一致＋マーカー走査（否定優先）。
// spec: 存在質問_有無（#254 / #256）。engine は spec#1（同意質問）とバイト不変・@spec 辞書のみ存在質問版。
// 存在質問（「ご相談はありますか」）: 用件あり→肯定 / 用件なし→否定。同意質問で肯定の
//   「大丈夫/問題ありません/問題ないです」は存在質問では否定（規格: SKILL_B_yes_no.md #254）。
// parity: acceptance_test/存在質問_有無/oracle_existence.py（同一辞書・同一手順・同一順序）。
// 入力: $runner.getModuleResult(SOURCE_MODULE) / 出力: 内部enum(肯定/否定/NO_RESULT)を YES_LABEL/NO_LABEL(wiring)へ写像し setResult/保存（#270）
// Nashorn(ES5.1)想定: String.normalize 不使用の限定正規化（全角数字/英字→半角・ASCII小文字化・記号空白除去）。
// ※ SOURCE_MODULE は組込先ごとの設定行（インスタンスパラメータ）。これ以外の行の改変は再受入。
// @part-id: yes_no_classifier
// @engine-version: v4
var SOURCE_MODULE = "__SOURCE_MODULE__";
// @template CONTEXT_NAME: 保存先 context 名（wiring・空なら保存スキップ）
var CONTEXT_NAME = "__CONTEXT_NAME__";
// @template CONTEXT_DISPLAY_TYPE: context の displayType（wiring）
var CONTEXT_DISPLAY_TYPE = "__CONTEXT_DISPLAY_TYPE__";
// @template YES_LABEL: 肯定側の表示/保存ラベル（wiring・既定 肯定）。CMR マッチャは scaffold が同値から生成しドリフト不能（#270）。
var YES_LABEL = "__YES_LABEL__";
// @template NO_LABEL: 否定側の表示/保存ラベル（wiring・既定 否定）。
var NO_LABEL = "__NO_LABEL__";

// @spec-begin
var EXACT_YES = [
  "はい", "はいです", "はいそうです", "ええ", "うん", "はいはい",
  "はあい", "はぁい", "はーい",
  "ある", "あります", "ございます", "有", "有り", "あり", "はいあります",
  "お願いします", "お願い", "それでお願いします", "はいお願いします",
  "相談したい", "聞きたい", "質問", "質問です",
  "オッケー", "おっけー", "ok", "いち"
];

var EXACT_NO = [
  "いいえ", "いえ", "いや",
  "ない", "ないです", "ありません", "なし", "無", "無し",
  "特にない", "特にないです", "特にありません", "特になし",
  "とくにない", "とくにないです", "とくにありません", "とくになし",
  "結構です", "けっこうです",
  "問題ない", "問題ないです", "問題ありません",
  "大丈夫", "大丈夫です", "だいじょうぶ", "だいじょうぶです",
  "以上です", "以上",
  "違います", "ちがいます", "違う", "ちがう", "だめ", "ダメ", "駄目"
];

var WAKARANAI_MARKERS = [
  "わからない", "わかりません", "わかんない", "分からない", "分かりません"
];

// 存在質問では「間違いない」系イディオムは発生しないため空（engine の走査自体は保持）。
var YES_PRECEDENCE = [];

// 部分一致・否定優先。安全側（用件取りこぼし回避）のため明確な用件なし述語のみに限定。
var NO_MARKERS = [
  "ありません", "ございません", "ないです",
  "特にない", "特になし", "問題ない",
  "結構です", "大丈夫", "いいえ"
];

// 部分一致・用件あり（NO 走査の後段）。
// ※「質問」はインジェクション文を肯定に倒すため部分一致から除外し EXACT_YES 限定。
//   用件ありの「質問があります」は「あります」マーカーで回収するため漏れなし。
var YES_MARKERS = [
  "あります", "ございます", "相談", "聞きたい",
  "教え", "知りたい", "お尋ね", "伺いたい", "確認したい",
  "お願いします", "はい"
];
// @spec-end

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  s = "" + Java.type("java.text.Normalizer").normalize(s, Java.type("java.text.Normalizer$Form").NFKC); // NFKC: 半角カナ/全半/互換を正規化（FAQ Matcher と同方式）
  // 全角数字→半角
  s = s.replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  // 全角英字→半角小文字
  s = s.replace(/[Ａ-Ｚａ-ｚ]/g, function (c) {
    var h = String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
    return h.toLowerCase();
  });
  // ASCII 大文字→小文字
  s = s.replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
  // 句読点・記号・空白の除去（oracle.py PUNCT と同一集合。長音「ー」は除去しない）
  var strip = ["、", "。", "，", "．", ",", ".", "・", "･", ":", ";", "：", "；",
               "!", "！", "?", "？", "…", "‥", "〜", "～", "「", "」", "『", "』",
               "(", ")", "（", "）", "[", "]", "【", "】", "<", ">", "＜", "＞",
               "\"", "'", "“", "”", "‘", "’", "｢", "｣", "-",
               "　", " ", "\t", "\r", "\n"];
  for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
  return s;
}

function decide(s) {
  // 1. 空
  if (s === "") return "NO_RESULT";
  // 2. 数字のみ（DTMF 流入）
  if (/^[0-9]+$/.test(s)) {
    if (s === "1") return "肯定";
    if (s === "2") return "否定";
    return "NO_RESULT";
  }
  var i;
  // 3. 完全一致（肯定）
  for (i = 0; i < EXACT_YES.length; i++) { if (s === EXACT_YES[i]) return "肯定"; }
  // 4. 完全一致（否定）
  for (i = 0; i < EXACT_NO.length; i++) { if (s === EXACT_NO[i]) return "否定"; }
  // 5. わからない検知（「ないです」誤爆防止のためマーカー走査より先）
  for (i = 0; i < WAKARANAI_MARKERS.length; i++) { if (s.indexOf(WAKARANAI_MARKERS[i]) >= 0) return "NO_RESULT"; }
  // 5.5 否定マーカーより優先の肯定イディオム（間違いない系・engine v3 新設）
  for (i = 0; i < YES_PRECEDENCE.length; i++) { if (s.indexOf(YES_PRECEDENCE[i]) >= 0) return "肯定"; }
  // 6. 否定マーカー走査（否定優先）
  for (i = 0; i < NO_MARKERS.length; i++) { if (s.indexOf(NO_MARKERS[i]) >= 0) return "否定"; }
  // 7. 肯定マーカー走査
  for (i = 0; i < YES_MARKERS.length; i++) { if (s.indexOf(YES_MARKERS[i]) >= 0) return "肯定"; }
  // 8. 不一致
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
var out = decide(norm);
// 内部enum(肯定/否定/NO_RESULT)を施設の表示/保存ラベルへ写像（wiring・#270）。NO_RESULT は内部sentinel（再質問誘発）ゆえ非ラベル化。
var label = (out === "肯定") ? YES_LABEL : ((out === "否定") ? NO_LABEL : out);
$runner.getLogger().info("[SCRIPT-YESNO] raw=" + raw + " norm=" + norm + " out=" + out + " label=" + label);
$runner.setResult(label);

// コンテキスト保存（スクリプト内で完結。@General$Script は subs の save2db を実行しないため必須）
saveContext(label, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
