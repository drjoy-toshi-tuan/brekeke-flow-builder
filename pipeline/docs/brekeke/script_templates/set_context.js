// Script Template: set_context
// 固定値を context に保存して次へ進む（分岐なしの「分類保存」用途）
//
// これまで 予約_新規_分類保存 / 予約_再診_分類保存 等は script_template: custom
// （CONTEXT_NAME/FIXED_VALUE を手書き JS に埋め込み）で書かれていた（蘇生会 ×2）。
// 本テンプレートはその共通形「ルート確定時に分類値を刻む」を吸収する。
//
// ※ announcement ブロックの save_to/save_value（saveContext2DB モジュール）でも
//   同じことができる。TTS 再生が不要で「無音で値だけ保存したい」場合に本テンプレートを使う。
//
// プレースホルダー:
//   {{CONTEXT_NAME}}  = 保存先 context 名（例: classification）
//   {{FIXED_VALUE}}   = 保存する固定値（例: 新規予約）
//   {{DISPLAY_TYPE}}  = context の displayType。未指定は TEXT
// 出力: SUCCESS（常に）
//
// 設計書の記述例:
//   - step: 予約_新規_分類保存
//     type: script
//     script_template: set_context
//     template_params:
//       CONTEXT_NAME: classification
//       FIXED_VALUE: 新規予約
//     next: 診療科聴取

var logger = $runner.getLogger();

var NAME  = "{{CONTEXT_NAME}}";
var VALUE = "{{FIXED_VALUE}}";
var DT    = "{{DISPLAY_TYPE}}";
if (DT.indexOf("{{") === 0 || DT === "") DT = "TEXT";

try {
    var req = JSON.stringify({contextField: {contextName: NAME, displayType: DT, value: VALUE}});
    $ivr.exec("save2db", "save", req);
    $runner.setObject(NAME, VALUE);
    logger.info("[set_context] " + NAME + "=" + VALUE + " (" + DT + ")");
} catch (e) {
    logger.error("[set_context] " + e);
}
$runner.setResult("SUCCESS");
