// Script Template: desired_date_precompute
// 受診希望日聴取_*の TTS 直前で「読み上げ用 context」を計算してセットする前段 script。
//
// なぜ必要か:
//   TTS prompt が <%desired_date_jp%> / <%desired_date_mmdd%> を参照しているため、
//   ヒアリング前に context が saveObject されていないと「変数部分が無音」になる。
//   ゲート判定 script (shinjuku_kenshin_date_gate) は TTS の後段にいるため初回ヒアリング時には間に合わない。
//
// 出力 context（$runner.setObject で保存、TTS 内で <%name%> として参照可能）:
//   desired_date_jp     例: "5月10日"     最短予約日（TODAY + MIN_DAYS_AHEAD）
//   desired_date_mmdd   例: "0510"        最短予約日の MMDD 4桁
//   fiscal_end_jp       例: "3月31日"     年度末日付
//   fiscal_end_full_jp  例: "2027年3月31日"
//
// プレースホルダー (scaffold 時に値置換):
//   - MIN_DAYS_AHEAD   最短予約日のオフセット日数（customer_doc §10-3 由来）
//   - FISCAL_END_DATE  年度末日付 YYYY-MM-DD
//
// 実例: cardnumber_raw（動作確認済み）の setObject 利用パターンに準拠。

var MIN_DAYS_AHEAD = {{MIN_DAYS_AHEAD}};
var FISCAL_END_DATE = "{{FISCAL_END_DATE}}";

// 1. 最短予約日の和形式・MMDD を計算
var now = new Date();
var d = new Date(now.getTime() + MIN_DAYS_AHEAD * 86400000);
var month = d.getMonth() + 1;
var day = d.getDate();
var desiredJp = month + "月" + day + "日";
var desiredMmdd = ("0" + month).slice(-2) + ("0" + day).slice(-2);

// 2. 年度末日付の和形式
var feMatch = FISCAL_END_DATE.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
var fiscalJp = "";
var fiscalFullJp = "";
if (feMatch) {
    fiscalJp = parseInt(feMatch[2], 10) + "月" + parseInt(feMatch[3], 10) + "日";
    fiscalFullJp = feMatch[1] + "年" + parseInt(feMatch[2], 10) + "月" + parseInt(feMatch[3], 10) + "日";
}

// 3. context へ保存（TTS から <%name%> で参照可能になる）
$runner.setObject("desired_date_jp", desiredJp);
$runner.setObject("desired_date_mmdd", desiredMmdd);
$runner.setObject("fiscal_end_jp", fiscalJp);
$runner.setObject("fiscal_end_full_jp", fiscalFullJp);

// 4. 分岐用の結果（無条件で次のモジュールへ流す）
$runner.setResult("OK");
