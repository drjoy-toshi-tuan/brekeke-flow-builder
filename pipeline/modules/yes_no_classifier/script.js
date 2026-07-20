// [SCRIPT-YESNO] Yes/No 決定論分類（ECHO_YESNO_PROMPT 置換）。完全一致＋マーカー走査（否定優先）。
// parity: yes_no_classifier/oracle.py（同一辞書・同一手順・同一順序）。テストの正は acceptance_test/cases.tsv。
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
  "はい", "はいです", "はいそうです", "そうです", "そうですね", "そうですよ",
  "ええ", "うん", "はいはい",
  "大丈夫", "大丈夫です", "合ってます", "合っています", "あってます", "あっています",
  "正しいです", "それで", "それでお願いします", "お願いします",
  "オッケー", "おっけー", "ok", "いち",
  "いいです", "いいですよ", "いいよ",
  // #279: 承諾の「よろしい」系（生年月日復唱等の確認応答・完全一致＝部分一致誤爆なし）
  "よろしい", "よろしいです", "よろしいですね", "よろしいですよ", "宜しい", "宜しいです",
  "ございます", "問題ないです", "問題ありません", "構いません", "構わないです", "かまいません",
  "います", "いる",
  "はあい", "はぁい", "はーい",
  // A3 Phase2: 有無/該当 polar 設問の肯定側ドメイン語（完全一致のみ＝部分一致誤爆なし）
  "有", "有り", "あり", "ある", "該当", "該当する", "該当します",
  // scorecard v1.1 G 回収（完全一致＝部分一致誤爆/インジェクション混入を避ける）
  // ラベル語(肯定/yes/イエス)・「お願い」はマーカー化すると R014/R019/R020 を壊すため EXACT 限定。
  "そう", "その通り", "その通りです", "お願い",
  "肯定", "肯定です", "yes", "イエス", "イエスです"
];

var EXACT_NO = [
  "いいえ", "いえ", "いや",
  "違います", "ちがいます", "違う", "ちがう", "違いました",
  "間違い", "間違いです", "間違っています",
  "ダメ", "だめ", "駄目", "やめて", "やり直し", "もう一度",
  "に", "いません", "いない", "ありません", "ないです", "当てはまりません",
  // A3 Phase2: 有無/該当 polar 設問の否定側ドメイン語（完全一致のみ＝部分一致誤爆なし）
  "無", "無し", "なし", "ない", "非該当", "該当しない", "該当しません",
  // #290: 否定側ラベル語（EXACT_YES「肯定/肯定です」と対称・完全一致＝部分一致誤爆なし）
  "否定", "否定です"
];

var WAKARANAI_MARKERS = [
  "わからない", "わかりません", "わかんない", "分からない", "分かりません"
];

// step 5.5: NO_MARKERS より優先の肯定イディオム（「間違いない」=誤りが無い=肯定）。engine v3 新設。
var YES_PRECEDENCE = [
  "間違いない", "間違いなし", "間違いありません", "間違いなく"
];

// 部分一致・否定優先。「ない」単独は誤爆するため述語形のみ（REQUIREMENTS 参照）
var NO_MARKERS = [
  "当てはまりません", "ありません", "ないそうです", "ないです",
  "違います", "ちがいます", "違いました", "違う", "ちがう",
  "いいえ", "間違い", "駄目", "だめ", "ダメ", "やめて", "やり直し",
  // scorecard v1.1 G 回収（bare `違い` は step5.5 で 間違いない系が先に肯定確定ゆえ安全）
  "違い", "間違え", "間違っ", "嫌"
];

var YES_MARKERS = [
  "当てはまります", "そうです", "あります", "お願いします", "希望します", "はい",
  // scorecard v1.1 G 回収（語幹マーカー＝変種吸収・NO 走査の後段ゆえ極性反転語に食われない）
  // ※ ラベル語(肯定/yes/イエス)・「お願い」は EXACT_YES 側（インジェクション/再質問の過剰被覆回避）。
  "お願いいたします", "同じ", "了解", "正しい", "さよう",
  "合っ", "正解", "かしこまり", "もちろん", "わかった", "拝承", "当たって",
  // #279: 「よろしい」語幹（よろしいかと/よろしいでしょう 等の変種吸収・NO 走査の後段ゆえ極性反転語に食われない）
  "よろしい"
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
