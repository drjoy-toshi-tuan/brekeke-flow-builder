// n_choice — N択分類 + コンテキスト保存（決定論・正本 v4）
// 用途: DTMF（プッシュ番号）または音声キーワードで N 択メニューを判定する汎用エンジン。
//       OpenAI を使わず、正規化 → DTMF_MAP → token/keyword 正規表現で決定論的に分類する。
// 出力: 選択肢ラベル / NO_RESULT
// ランタイム: Brekeke @General$Script（Nashorn / ES5 only）
// 由来: 髙橋 VFB-Script reference/scripts/n_choice.js (v4) を VFB の DoD に載せた正本。
// @part-id: n_choice
// @engine-version: v4
//
// 【テンプレート（設定行 — 施設・設問ごとに充填。hash 認定では除外対象）】
//   {{INPUT_MODULE}}          直前の入力（STT/DTMF）モジュール名（wiring）
//   {{CONTEXT_NAME}}          保存先 context 名（例: callerType）（wiring）
//   {{CONTEXT_DISPLAY_TYPE}}  context の displayType（例: TEXT）（wiring）
//   {{DTMF_MAP}}              {"1":"ラベルA","2":"ラベルB",...} 数字→ラベル（spec）
//   {{TOKEN_MAP}}             [{regex:"...",result:"ラベル"},...] 完全一致トークン（spec）
//   {{DIGIT_KEYWORD_PATTERNS}}[{digit:"1",regex:"...",result:"ラベル"},...] 先頭数字＋語（spec）
//   {{COMPOUND_PATTERNS}}     [{regex:"...",result:"ラベル"},...] 複合語（先に評価）（spec）
//   {{KEYWORD_PATTERNS}}      [{regex:"...",result:"ラベル"},...] 単独キーワード（spec）
//
// 【判定順】空 → 正規化 → DTMF（単一数字）→ TOKEN → 先頭数字+語 → 複合 → 単独keyword
//          → filler のみ → no_match（いずれも NO_RESULT に倒す）

var logger = $runner.getLogger();
var INPUT_MODULE = "{{INPUT_MODULE}}";
var CONTEXT_NAME = "{{CONTEXT_NAME}}";
var CONTEXT_DISPLAY_TYPE = "{{CONTEXT_DISPLAY_TYPE}}";

// === コンテキスト保存関数群（VFB 共通流儀: save2db + setObject + checkpoint）===
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

var input = $runner.getResult(INPUT_MODULE);
logger.info("[n_choice] raw input: " + input);

var result = null;
var source = "";

if (input === null || input === undefined || input === "") {
    result = "NO_RESULT"; source = "empty";
} else {
    var s = String(input);
    s = s.replace(/[０-９]/g, function(c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    s = s.replace(/[、。,.:;!?！？「」『』（）()\s\r\n\t]/g, "");
    s = s.replace(/^(えーと|えーっと|えー|あのー|あの|うーんと|うーん|まー|まあ|そうですね|えっと|そのー|あー|んー|んーと|ねえ|ちょっと)+/g, "");
    s = s.replace(/(えーと|えーっと|えー|あのー|あの|うーんと|うーん|まー|まあ|そうですね|えっと|そのー|あー|んー|んーと|ねえ|ちょっと)+$/g, "");
    // 方言/敬語/タメ口 接尾辞除去 (DIALECT/POLITE/CASUAL)
    s = s.replace(/(だべさ|だべ|っしょ|べし|だす|んだ|じゃん|だよね|じゃね|やん|やねん|やで|やんか|やわ|ねん|やろ|じゃけん|じゃけ|けん|ばい|たい|さー|さあ)$/g, "");
    s = s.replace(/(でございます|ございます|いただけますか|いただきたい|させていただきたい|でしょうか|いたします|ですよね|ですわ|だわ)$/g, "");
    s = s.replace(/(だよ|だね|だぜ|だろ|じゃね|じゃん|っす|すか|かよ|だっけ|っけ|だわ|やん|やろ|やで|けど|けんど|だに|ずら|だら)$/g, "");
    s = s.replace(/(です|でお願いします|お願いします|なんですけど|にお願い|ですけど|なんですが|をお願い)$/g, "");
    // AmiVoice カテゴリ重複正規化: "再診再診" → "再診"
    if (s.length >= 4) {
        for (var dl = Math.floor(s.length / 2); dl >= 2; dl--) {
            var chunk = s.substring(0, dl);
            var rep = new RegExp("^(" + chunk.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")+$");
            if (rep.test(s)) { s = chunk; break; }
        }
    }
    var trimmed = s.replace(/^([0-9])(です|だ|でお願いします|でお願い|ね|よ|かな)+$/, "$1");
    if (trimmed !== s) { logger.info("[n_choice] trimmed: " + s + " => " + trimmed); s = trimmed; }
    logger.info("[n_choice] normalized: " + s);
    if (s === "") { result = "NO_RESULT"; source = "empty_after_normalize"; }

    // @spec-begin
    var DTMF_MAP = {{DTMF_MAP}};
    // @spec-end
    if (result === null && /^[0-9]$/.test(s)) {
        if (DTMF_MAP[s] !== undefined) { result = DTMF_MAP[s]; source = "dtmf"; }
        else { result = "NO_RESULT"; source = "dtmf_invalid"; }
    }

    // @spec-begin
    var TOKEN_MAP = {{TOKEN_MAP}};
    // @spec-end
    if (result === null) {
        for (var ti = 0; ti < TOKEN_MAP.length; ti++) {
            if (new RegExp("^(" + TOKEN_MAP[ti].regex + ")$").test(s)) { result = TOKEN_MAP[ti].result; source = "token"; break; }
        }
    }

    // @spec-begin
    var DIGIT_KEYWORD_PATTERNS = {{DIGIT_KEYWORD_PATTERNS}};
    // @spec-end
    if (result === null) {
        var hdm = s.match(/^([0-9])/);
        if (hdm !== null) {
            for (var dk = 0; dk < DIGIT_KEYWORD_PATTERNS.length; dk++) {
                var dkp = DIGIT_KEYWORD_PATTERNS[dk];
                if (dkp.digit === hdm[1] && new RegExp(dkp.regex).test(s)) { result = dkp.result; source = "digit_keyword"; break; }
            }
        }
    }

    // @spec-begin
    var COMPOUND_PATTERNS = {{COMPOUND_PATTERNS}};
    // @spec-end
    if (result === null) {
        for (var cp = 0; cp < COMPOUND_PATTERNS.length; cp++) {
            if (new RegExp(COMPOUND_PATTERNS[cp].regex).test(s)) { result = COMPOUND_PATTERNS[cp].result; source = "compound"; break; }
        }
    }

    // @spec-begin
    var KEYWORD_PATTERNS = {{KEYWORD_PATTERNS}};
    // @spec-end
    if (result === null) {
        for (var kp = 0; kp < KEYWORD_PATTERNS.length; kp++) {
            if (new RegExp(KEYWORD_PATTERNS[kp].regex).test(s)) { result = KEYWORD_PATTERNS[kp].result; source = "keyword"; break; }
        }
    }

    if (result === null && /^(えー[っとー]*|えっと|えーっと|あのー?|うーん?|まあ|その|はい|うん|ん+)+$/.test(s)) {
        result = "NO_RESULT"; source = "filler_only";
    }
    if (result === null) { result = "NO_RESULT"; source = "no_match"; }
}

logger.info("[n_choice] input=\"" + input + "\" source=" + source + " => " + result);
$runner.setResult(result);

// コンテキスト保存
saveContext(result, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
