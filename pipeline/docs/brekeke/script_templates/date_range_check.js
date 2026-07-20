// Script Template: date_range_check
// context に保存済みの日付が「絶対日付の受付範囲」（START..END）内か判定
//
// これまで 受診希望日N_範囲チェック / 変更希望日N_範囲チェック は
// script_template: custom（START_DATE/END_DATE を手書き JS に埋め込み）で
// 施設ごとに手書きされていた（島村記念 ×6）。本テンプレートはその共通形
// 「正規化済み希望日が予約受付期間内か」を吸収する。
//
// プレースホルダー:
//   {{CONTEXT_FIELD}} = 判定対象の日付 context 名（例: reservationDate）
//   {{START_DATE}}    = 受付開始日 "YYYY-MM-DD"（当日を含む）
//   {{END_DATE}}      = 受付終了日 "YYYY-MM-DD"（当日を含む）
// 出力: 範囲内 / 範囲外 / 判定不能 / ERROR（START/END の書式不正）
//
// 設計書の conditions 例:
//   - match: "範囲内"
//     next: 予約確定
//   - match: "判定不能"
//     next: リトライ_希望日
//   - match: "other"
//     next: 範囲外アナウンス
//
// 注意: 期間は絶対日付（年込み）。年度が変わったら設計書の template_params を
// 更新して再ビルドする運用（毎年更新が要る場合は notes に明記すること）。

var logger = $runner.getLogger();

var CONTEXT_FIELD = "{{CONTEXT_FIELD}}";
var START_RAW     = "{{START_DATE}}";
var END_RAW       = "{{END_DATE}}";

function readContext(field) {
    var v = null;
    try {
        if (typeof $runner.getContextModel === "function") {
            var cm = $runner.getContextModel();
            if (cm) {
                if (typeof cm.get === "function") v = cm.get(field);
                else if (cm[field] != null) v = cm[field];
            }
        }
    } catch (e) { logger.error("[date_range_check] ctx read: " + e); }
    if (v == null) {
        try { v = $runner.getObject(field); } catch (e2) {}
    }
    return v == null ? "" : ("" + v);
}

function parseYmd(s) {
    var m = ("" + s).match(/(\d{4})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})/);
    if (!m) return null;
    var y = parseInt(m[1], 10), mo = parseInt(m[2], 10), d = parseInt(m[3], 10);
    if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
    return new Date(y, mo - 1, d);
}

var start = parseYmd(START_RAW);
var end   = parseYmd(END_RAW);

var res;
if (start === null || end === null || start.getTime() > end.getTime()) {
    logger.error("[date_range_check] 範囲設定不正: START=" + START_RAW + " END=" + END_RAW);
    res = "ERROR";
} else {
    var raw = readContext(CONTEXT_FIELD);
    var d = parseYmd(raw);
    if (d === null) {
        res = "判定不能";
    } else {
        res = (d.getTime() >= start.getTime() && d.getTime() <= end.getTime())
              ? "範囲内" : "範囲外";
    }
}

logger.info("[date_range_check] " + CONTEXT_FIELD + " in " + START_RAW + ".." + END_RAW + " -> " + res);
$runner.setResult(res);
