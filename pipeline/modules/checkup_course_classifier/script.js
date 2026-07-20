// [SCRIPT-COURSE] 健診CC コース 決定論分類（コース選択/その他コース確認の generate_by_OpenAI 置換）。
// parity: checkup_course_classifier/oracle.py（同一辞書・同一手順・同一順序）。テストの正は acceptance_test/cases.tsv。
// 入力: $runner.getModuleResult(SOURCE_MODULE)
// 出力: universe コース種別ラベル（施設非提供時は "ラベル|OFF_MENU"）| "NO_RESULT"
// Nashorn(ES5.1)想定。※ SOURCE_MODULE / FACILITY_OFFERED は組込先ごとの設定行（wiring）。これ以外の行の改変は再受入。
// @part-id: checkup_course_classifier
// @engine-version: v3
// #274 universe 化: CATEGORIES を universe 種別へ・DTMF/GENERIC を data-driven(@spec)・facility_offered(OFF_MENU) 対応。
var SOURCE_MODULE = "__SOURCE_MODULE__";
// @template CONTEXT_NAME: 保存先 context 名（wiring・空なら保存スキップ）
var CONTEXT_NAME = "__CONTEXT_NAME__";
// @template CONTEXT_DISPLAY_TYPE: context の displayType（wiring）
var CONTEXT_DISPLAY_TYPE = "__CONTEXT_DISPLAY_TYPE__";
// @template FACILITY_OFFERED: 施設が提供するコース種別ラベルの配列（wiring・null=サブセットなし=universe）。
var FACILITY_OFFERED = __FACILITY_OFFERED__;

// @spec-begin
// 実ログ最大の 一般健診/健康診断 を潰さないため 健康診断→健診 は畳まない（検診/健康診査 のみ健診へ）。
var FOLDINGS = [
  ["健康診査", "健診"],
  ["検診", "健診"]
];

var WAKARANAI_MARKERS = [
  "わからない", "わかりません", "わかんない", "分からない", "分かりません"
];

// カテゴリ優先順位（上から評価・部分一致・先勝ち・単一出力）。抽出2ケース（雇用時/市区町村）を最優先。
var CATEGORIES = [
  ["雇用時健診", ["雇用時", "雇用の健", "雇い入れ", "雇入れ", "入社時", "入社前", "採用時", "就職時"]],
  ["市区町村健診", ["市の健", "市民健", "市健診", "区の健", "区民健", "町の健", "村の健",
                "自治体", "住民健", "特定健", "特定健康", "後期高齢", "がん検診クーポン"]],
  ["協会けんぽ・生活習慣病予防健診", ["協会けんぽ", "けんぽ", "協会健保", "生活習慣", "成人病"]],
  ["一般・定期健診", ["一般健", "一般の健", "健康診断", "定期健", "定期の健", "基本健", "職場の健", "会社の健", "法定健"]],
  ["レディース・専門ドック", ["レディース", "女性ドック", "ウィメンズ", "婦人科", "脳ドック", "心臓ドック",
                      "肺ドック", "眼科ドック", "消化器ドック", "pet", "ペット", "がんドック", "なでしこ"]],
  ["人間ドック", ["人間ドック", "ドック", "半日", "一日ドック", "1日ドック", "一泊", "1泊", "日帰り", "胃カメラ", "バリウム"]]
];

var GENERIC_FALLBACK_KEY = "健診";
var GENERIC_FALLBACK_LABEL = "その他の健診";

// DTMF は施設ごとに割当が違う（下記は universe 既定・facility 側で差し替え）。data-driven。
var DTMF_MAP = { "1": "人間ドック", "2": "一般・定期健診", "3": "協会けんぽ・生活習慣病予防健診", "4": "市区町村健診" };
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

function inFacility(label) {
  if (FACILITY_OFFERED == null) { return true; }
  for (var i = 0; i < FACILITY_OFFERED.length; i++) { if (FACILITY_OFFERED[i] === label) { return true; } }
  return false;
}

function decide(s) {
  // 1. 空
  if (s === "") return "NO_RESULT";
  // 2. 数字のみ（DTMF 併用・data-driven）
  if (/^[0-9]+$/.test(s)) {
    if (DTMF_MAP.hasOwnProperty(s)) return DTMF_MAP[s];
    return "NO_RESULT";
  }
  var i, k;
  // 3. わからない検知 → その他の健診（-6 誘導文言と整合。REQUIREMENTS 参照）
  for (i = 0; i < WAKARANAI_MARKERS.length; i++) { if (s.indexOf(WAKARANAI_MARKERS[i]) >= 0) return GENERIC_FALLBACK_LABEL; }
  // 4. カテゴリ走査（優先順位順・部分一致・先勝ち）。facility_offered 非該当は OFF_MENU 併記。
  for (i = 0; i < CATEGORIES.length; i++) {
    var label = CATEGORIES[i][0];
    var keys = CATEGORIES[i][1];
    for (k = 0; k < keys.length; k++) {
      if (s.indexOf(keys[k]) >= 0) {
        if (!inFacility(label)) return label + "|OFF_MENU";
        return label;
      }
    }
  }
  // 5. 総称の受け皿走査
  if (s.indexOf(GENERIC_FALLBACK_KEY) >= 0) return GENERIC_FALLBACK_LABEL;
  // 6. 不一致
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
$runner.getLogger().info("[SCRIPT-COURSE] raw=" + raw + " norm=" + norm + " out=" + out);
$runner.setResult(out);

// コンテキスト保存（スクリプト内で完結。@General$Script は subs の save2db を実行しないため必須）
saveContext(out, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
