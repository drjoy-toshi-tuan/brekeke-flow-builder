// Script Template: closed_period
// 入電日が「毎年繰り返す休業期間」（GW・年末年始・夏季休診 等）に該当するか判定
//
// これまで GW判定 / 年末年始判定 / 休診期間判定 は script_template: custom で
// 施設ごとに手書きされていた（相澤・慈恵会西田・鹿児島市立・蘇生会・鹿児島生協）。
// 本テンプレートはその共通形「MM-DD の期間リストに今日が入るか」を吸収する。
//
// プレースホルダー:
//   {{PERIODS}}         = 期間リスト。"MM-DD..MM-DD" をカンマ区切りで複数指定可。
//                         年跨ぎ可（例: "12-29..01-03"）。
//                         例: "04-29..05-06" / "12-29..01-03,08-13..08-15"
//   {{TARGET_DATETIME}} = 判定基準日。本番は未指定（= now）。P6 受入テストでは
//                         "2026-05-03" 等の固定日を渡して期間内/期間外を再現する。
// 出力: 期間内 / 期間外 / ERROR（PERIODS の書式不正）
//
// 設計書の conditions 例:
//   - match: "期間内"
//     next: END_GW案内
//   - match: "other"
//     next: 用件確認
//
// 注意: 期間は毎年同じ日付で繰り返す前提（祝日連動で年ごとに変わる場合は
// 年次更新運用が必要。その旨を設計書 notes に明記すること）。

var logger = $runner.getLogger();

var PERIODS_RAW = "{{PERIODS}}";
var TARGET_RAW  = "{{TARGET_DATETIME}}";

// 判定基準日（未指定プレースホルダー "{{...}}" は now 扱い）
var target;
if (TARGET_RAW.indexOf("{{") === 0 || TARGET_RAW === "" || TARGET_RAW === "now") {
    target = new Date();
} else {
    var tm = TARGET_RAW.match(/(\d{4})\D(\d{1,2})\D(\d{1,2})/);
    target = tm ? new Date(parseInt(tm[1], 10), parseInt(tm[2], 10) - 1, parseInt(tm[3], 10))
                : new Date();
}
var todayMd = (target.getMonth() + 1) * 100 + target.getDate();

// "MM-DD..MM-DD,MM-DD..MM-DD" をパース
var res = "期間外";
var ranges = PERIODS_RAW.split(",");
var parsed = 0;
for (var i = 0; i < ranges.length; i++) {
    var r = ranges[i].replace(/\s/g, "");
    if (!r) continue;
    var m = r.match(/^(\d{1,2})-(\d{1,2})\.\.(\d{1,2})-(\d{1,2})$/);
    if (!m) {
        logger.error("[closed_period] 期間書式不正: " + r);
        res = "ERROR";
        break;
    }
    parsed++;
    var s = parseInt(m[1], 10) * 100 + parseInt(m[2], 10);
    var e = parseInt(m[3], 10) * 100 + parseInt(m[4], 10);
    var hit;
    if (s <= e) {
        hit = (todayMd >= s && todayMd <= e);          // 通常期間（例 04-29..05-06）
    } else {
        hit = (todayMd >= s || todayMd <= e);          // 年跨ぎ（例 12-29..01-03）
    }
    if (hit) {
        res = "期間内";
        break;
    }
}
if (res !== "ERROR" && parsed === 0) {
    logger.error("[closed_period] PERIODS が空です");
    res = "ERROR";
}

logger.info("[closed_period] today=" + todayMd + " periods=" + PERIODS_RAW + " -> " + res);
$runner.setResult(res);
