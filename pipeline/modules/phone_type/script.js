// phone_type — 電話番号 → 種別(携帯/固定/その他) 決定論判定（正本 v1）
// 用途: 着信 ANI または手入力番号の数字列から回線種別を分類する。OpenAI 不使用。
// 出力: "携帯" | "固定" | "その他"
// ランタイム: Brekeke @General$Script（Nashorn / ES5 only）
// 由来: 本番 script_携帯判別 準拠（050=その他）。テンプレ docs/brekeke/script_templates/phone_type.js の
//       050=携帯 を上書きした版。後段 ContextMatchRouter が module-result（携帯/固定/その他）で分岐する。
// parity: modules/phone_type/oracle.py（同一規則・同順評価）。テストの正は acceptance_test/cases.tsv。
// @part-id: phone_type
// @engine-version: v1
//
// 【wiring（組込先ごとの設定行。hash 認定では除外対象）】
//   SOURCE_MODULE  直前の番号入力モジュール名（getModuleResult で番号文字列を取る）
var SOURCE_MODULE = "__SOURCE_MODULE__";

// @spec-begin
// 種別判定規則（050=その他。本番 script_携帯判別 準拠）。
//   携帯: 11 桁 かつ 先頭 060/070/080/090
//   固定: 10 桁 かつ 先頭 0[1-9]（050 は 11 桁なので該当せず → その他に落ちる）
// 注: 060 も携帯（11 桁・060-XXXX-XXXX）。10 桁 06x（大阪 06 市外局番）は桁数が違うので固定のまま。
var MOBILE_REGEX = /^(060|070|080|090)/;
var MOBILE_LEN = 11;
var FIXED_REGEX = /^0[1-9]/;
var FIXED_LEN = 10;
var RESULT_DEFAULT = "その他";
// @spec-end

var logger = $runner.getLogger();
var input = $runner.getModuleResult(SOURCE_MODULE);
var res = RESULT_DEFAULT;
if (input) {
    var num = input.toString().replace(/[^0-9]/g, "");
    if (num.length === MOBILE_LEN && MOBILE_REGEX.test(num)) {
        res = "携帯";
    } else if (num.length === FIXED_LEN && FIXED_REGEX.test(num)) {
        res = "固定";
    }
}
logger.info("[phone_type] input=" + input + " digits-> " + res);
$runner.setResult(res);
