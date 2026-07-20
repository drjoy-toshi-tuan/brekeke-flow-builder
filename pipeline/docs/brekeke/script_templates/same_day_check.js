// Script Template: same_day_check
// context に保存済みの日付が「今日から N 日以内」か判定（当日・直前の変更/キャンセル振り分け）
//
// これまで 当日予約判定 / 当日翌日判定 / 予約日判定_変更・キャンセル は
// script_template: custom で施設ごとに手書きされていた（鎌ケ谷・牛久愛和・筑波記念・島村）。
// 本テンプレートはその共通形「予約日が当日（または翌日まで）なら自動処理せず
// スタッフ対応へ回す」を吸収する。
//
// プレースホルダー:
//   {{CONTEXT_FIELD}}   = 判定対象の日付 context 名（例: currentAppointmentDate）。
//                         current_appointment_date / reservation_date_classifier 等の
//                         正規化部品が保存した yyyy-MM-dd 系文字列を想定
//   {{DAYS_AHEAD}}      = 「以内」と見なす日数。0=当日のみ / 1=当日+翌日。未指定は 0
//   {{TARGET_DATETIME}} = 判定基準日。本番は未指定（= now）。P6 受入テストで固定日を注入
// 出力: 期限内 / 期限外 / 判定不能
//   期限内   … 予約日 <= 今日+N 日（過去日を含む。過去日はデータ異常のため
//              安全側=スタッフ対応に倒す）
//   期限外   … 予約日が今日+N 日より先（自動処理してよい）
//   判定不能 … context 未保存 or 日付として解釈不能（安全側=スタッフ対応を推奨）
//
// 設計書の conditions 例:
//   - match: "期限内"
//     next: 転送_当日窓口
//   - match: "判定不能"
//     next: 転送_当日窓口
//   - match: "other"
//     next: キャンセル受付

var logger = $runner.getLogger();

var CONTEXT_FIELD = "{{CONTEXT_FIELD}}";
var DAYS_RAW      = "{{DAYS_AHEAD}}";
var TARGET_RAW    = "{{TARGET_DATETIME}}";

var DAYS_AHEAD = /^\d+$/.test(DAYS_RAW) ? parseInt(DAYS_RAW, 10) : 0;

// --- context 読み取り（複数 API パターンにフォールバック）---
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
    } catch (e) { logger.error("[same_day_check] ctx read: " + e); }
    if (v == null) {
        try { v = $runner.getObject(field); } catch (e2) {}
    }
    return v == null ? "" : ("" + v);
}

// --- 日付パース（yyyy-MM-dd / yyyy/MM/dd / yyyyMMdd / "yyyy-MM-dd 00:00" 等）---
function parseYmd(s) {
    var m = ("" + s).match(/(\d{4})\D{0,3}(\d{1,2})\D{0,3}(\d{1,2})/);
    if (!m) return null;
    var y = parseInt(m[1], 10), mo = parseInt(m[2], 10), d = parseInt(m[3], 10);
    if (mo < 1 || mo > 12 || d < 1 || d > 31) return null;
    return new Date(y, mo - 1, d);
}

var base;
if (TARGET_RAW.indexOf("{{") === 0 || TARGET_RAW === "" || TARGET_RAW === "now") {
    base = new Date();
} else {
    base = parseYmd(TARGET_RAW) || new Date();
}
var today0 = new Date(base.getFullYear(), base.getMonth(), base.getDate());

var raw = readContext(CONTEXT_FIELD);
var appt = parseYmd(raw);

var res;
if (appt === null) {
    res = "判定不能";
} else {
    var diffDays = Math.round((appt.getTime() - today0.getTime()) / 86400000);
    // 過去日（diff<0）は異常データ → 安全側の 期限内（スタッフ対応）に倒す
    res = (diffDays <= DAYS_AHEAD) ? "期限内" : "期限外";
}

logger.info("[same_day_check] " + CONTEXT_FIELD + "=" + raw +
            " daysAhead=" + DAYS_AHEAD + " -> " + res);
$runner.setResult(res);
