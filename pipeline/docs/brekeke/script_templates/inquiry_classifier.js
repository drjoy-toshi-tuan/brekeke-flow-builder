// inquiry_classifier — 用件分類（自由発話・決定論）正本 v1
// 用途: 総合相談室の「ご用件」自由発話を決定論的に分類する。OpenAI 不使用。
// 出力: 相談 / 予約 / 大代表 / 定型案内 / その他 / NO_RESULT
// ランタイム: Brekeke @General$Script（Nashorn / ES5 only）
// 由来: 髙橋 VFB-Script reference/scripts/inquiry_classifier.js のエンジン構造
//       （RULES=groups の AND ＋ exclude 排他 / no_question / filler / saveContext）を踏襲し、
//       RULES の中身を亀田 総合相談室の用件語彙＋顧客大原則に置換したもの。
// @part-id: inquiry_classifier
// @engine-version: v1
//
// 【顧客大原則（2026-06-10 浜口確定）】相談室業務に関係する電話のみ受け、予約関連は弾く。
//   優先順位: 相談 ＞ 予約 ＞ 大代表 ＞ 定型案内（RULES の配列順＝優先順位。先勝ち）。
//   ・「相談」を含む発話は必ず相談を優先（相談予約を誤って弾かない）。
//   ・相談を含まず予約系を含む発話は必ず予約として弾く。
//
// 【テンプレート】wiring（設定行・hash 除外）: {{INPUT_MODULE}} / {{CONTEXT_NAME}} / {{CONTEXT_DISPLAY_TYPE}}
//   spec（規格・受入必須）: RULES / NO_QUESTION / FILLER_ONLY（@spec ブロック）

var logger = $runner.getLogger();
var INPUT_MODULE = "{{INPUT_MODULE}}";
var CONTEXT_NAME = "{{CONTEXT_NAME}}";
var CONTEXT_DISPLAY_TYPE = "{{CONTEXT_DISPLAY_TYPE}}";

// === コンテキスト保存関数群（VFB 共通流儀）===
function _saveCheckpoint(v){try{if(!$ivr.connected())return;$ivr.exec("save2db","save",JSON.stringify({contextField:{contextName:"checkpoint",displayType:"TEXT",value:v}}));}catch(e){logger.error("[ctx]"+e);}}
function _setObj(k,v){try{$ivr.setObject(k,v);}catch(e){logger.error("[ctx]"+e);}}
function saveContext(val,name,type){var rid=$ivr.getRID();var mod=$runner.getCurrentModuleName();_saveCheckpoint(mod+"_IN");_setObj("checkpoint."+rid,mod+"_IN");if(name&&val){var r=JSON.stringify({contextField:{contextName:name,displayType:type||"TEXT",value:val}});logger.info("[saveContext2DB] "+r);try{$ivr.exec("save2db","save",r);$runner.setObject(name,val);}catch(e){logger.error("[ctx]"+e);}}_saveCheckpoint(mod+"_OUT");_setObj("checkpoint."+rid,mod+"_OUT");_setObj("saveContext."+rid,true);}
// === END ===

// @spec-begin
// ============================================================
// 用件分類ルール（配列順＝優先順位。groups は AND、exclude は排他。先勝ち）
// 亀田 OpenAI 用件プロンプト STEP2 の語彙を決定論 regex に転記。
// ============================================================
var RULES = [
    // 1. 相談（最優先 — 相談室業務。相談予約も相談として受ける）
    {
        label: "相談",
        groups: ["相談|ご相談|総合相談室|相談室|退院|退院調整|転院|ケアマネ|ケアマネージャー|在宅|介護|医療相談|ソーシャルワーカー|ソーシャルワーカ|MSW|PSW"],
        exclude: ""
    },
    // 2. 予約（相談を含まない予約・受診意図は弾く）
    {
        label: "予約",
        groups: ["予約|ご予約|受診予約|外来予約|予約変更|予約の変更|予約確認|予約の確認|受診|診察|外来|キャンセル|取り消し|取消"],
        exclude: ""
    },
    // 3. 大代表（代表番号・他部署・誤着信）
    {
        label: "大代表",
        groups: ["代表|代表番号|大代表|別の部署|他の部署|違う部署|別の窓口|かけ間違|間違え|担当部署"],
        exclude: ""
    },
    // 4. 定型案内（場所・時間・番号などの案内）
    {
        label: "定型案内",
        groups: ["場所|駐車場|行き方|道順|アクセス|受付時間|診療時間|外来時間|面会時間|何時|営業時間|電話番号|番号"],
        exclude: ""
    }
];

// 用件として意味をなさない応答（→ NO_RESULT）。
var NO_QUESTION = /^(特にありません|特にないです|特にない|ないです|ありません|なし|無し|大丈夫です|だいじょうぶです|結構です|けっこうです|以上です|いじょうです)$/;
var FILLER_ONLY = /^(えー[っとー]*|えっと|えーっと|あのー?|うーん?|まあ|その|はい|うん|ん+)+$/;
// @spec-end

var rawInput = $runner.getResult(INPUT_MODULE);
logger.info("[inquiry_classifier] rawInput: " + rawInput);

var result = null;
var source = "";

if (rawInput === null || rawInput === undefined || rawInput === "") {
    result = "NO_RESULT"; source = "empty";
} else {
    var s = String(rawInput);
    var normalized = s.replace(/[、。,.!?！？\s\r\n\t]/g, "");
    logger.info("[inquiry_classifier] normalized: " + normalized);

    if (normalized === "") { result = "NO_RESULT"; source = "empty_after_normalize"; }
    // 用件なし応答
    else if (NO_QUESTION.test(normalized)) { result = "NO_RESULT"; source = "no_question"; }
    // フィラーのみ
    else if (FILLER_ONLY.test(normalized)) { result = "NO_RESULT"; source = "filler_only"; }
    // 数字のみ（用件として解釈不能）
    else if (/^[0-9０-９]+$/.test(normalized)) { result = "NO_RESULT"; source = "digits_only"; }

    // RULES マッチング（優先順位＝配列順・先勝ち）
    if (result === null) {
        for (var i = 0; i < RULES.length; i++) {
            var rule = RULES[i];
            if (rule.exclude !== "" && new RegExp(rule.exclude).test(normalized)) { continue; }
            var allGroupsMatch = true;
            for (var g = 0; g < rule.groups.length; g++) {
                if (!new RegExp(rule.groups[g]).test(normalized)) { allGroupsMatch = false; break; }
            }
            if (allGroupsMatch) { result = rule.label; source = "rule_match[" + i + "]"; break; }
        }
    }

    // どのルールにも該当しないが何らかの発話あり → その他（伝言・折返しの安全な受け皿）
    if (result === null) { result = "その他"; source = "other_fallback"; }
}

logger.info("[inquiry_classifier] input=\"" + rawInput + "\" source=" + source + " => " + result);
$runner.setResult(result);
saveContext(result, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
