/**
 * 【Brekeke PBX Module Script】
 * 予約日 抽出・正規化ロジック (期間制限なし版)
 * Input:  直前の STT/DTMF 入力（wiring: SOURCE_MODULE に施設別の入力モジュール名を充填）
 * Output: setResult — DATE形式 "YYYY-MM-DD 00:00" / "不明" / "NO_RESULT"
 *         context=reservationDate (+ 派生 reservationDate_yMda/_Mda/_yMd/_Md)
 */
// @part-id: reservation_date_classifier
// @engine-version: v2
// SOURCE_MODULE = 直前の STT/DTMF 入力モジュール名（wiring placeholder・施設別・engine_hash 対象外）。
// この行以外の本文（engine）を 1 文字でも改変すると engine_hash が変わり再受入（modules/certified_hashes.json）。
// parity: reservation_date_classifier/oracle.py（同一辞書・同一手順）。テストの正は test_oracle.py。
var SOURCE_MODULE = "__SOURCE_MODULE__";
// --- 1. 入力取得 ---
var rawResult = $runner.getModuleResult(SOURCE_MODULE);
var rawInput = "";
if (rawResult !== null && rawResult !== undefined) {
    rawInput = String(rawResult).replace(/\s+/g, "");
}
// --- 2. システム日付の取得 (JST固定) ---
// FIX(2026-06-12): new Date() は JVM デフォルト TZ 依存（VN サーバ等で深夜帯に 1 日ズレ）。
//   Asia/Tokyo の暦日で today を確定する。以降の日付演算は today 基準のローカル Date で一貫。
var _SDF = Java.type("java.text.SimpleDateFormat");
var _JavaDate = Java.type("java.util.Date");
var _sdf = new _SDF("yyyy-MM-dd");
_sdf.setTimeZone(java.util.TimeZone.getTimeZone("Asia/Tokyo"));
var _todayStr = String(_sdf.format(new _JavaDate()));
var today = new Date(
    parseInt(_todayStr.substring(0, 4), 10),
    parseInt(_todayStr.substring(5, 7), 10) - 1,
    parseInt(_todayStr.substring(8, 10), 10)
);
var todayYear = today.getFullYear();
// --- ユーティリティ関数 ---
function addDays(dt, n) {
    var r = new Date(dt.getTime());
    r.setDate(r.getDate() + n);
    return r;
}
function formatDate(dt) {
    var y = dt.getFullYear();
    var m = ("0" + (dt.getMonth() + 1)).slice(-2);
    var d = ("0" + dt.getDate()).slice(-2);
    return y + "-" + m + "-" + d + " 00:00";
}
function output(v) {
    $runner.setObject("reservationDate", v);
    if (v !== "NO_RESULT" && v !== "不明") {
        try {
            var contextField = {
                contextName: "reservationDate",
                displayType: "DATE",
                value: v
            };
            $ivr.exec("save2db", "save", JSON.stringify({ contextField: contextField }));
        } catch (e) { /* silent */ }
                var DOW_JA = ["日", "月", "火", "水", "木", "金", "土"];
        var parts = v.split(" ")[0].split("-");
        var fy = parseInt(parts[0], 10);
        var fm = parseInt(parts[1], 10);
        var fd = parseInt(parts[2], 10);
        var fdt = new Date(fy, fm - 1, fd);
        var dow = DOW_JA[fdt.getDay()] + "曜日";
        $runner.setObject("reservationDate_yMda", fy + "年" + fm + "月" + fd + "日 " + dow);
        $runner.setObject("reservationDate_Mda",  fm + "月" + fd + "日 " + dow);
        $runner.setObject("reservationDate_yMd",  fy + "年" + fm + "月" + fd + "日");
        $runner.setObject("reservationDate_Md",   fm + "月" + fd + "日");
    } else {
        $runner.setObject("reservationDate_yMda", v);
        $runner.setObject("reservationDate_Mda",  v);
        $runner.setObject("reservationDate_yMd",  v);
        $runner.setObject("reservationDate_Md",   v);
    }
    $runner.setResult(v);
}

// --- 補正エンジン (期間制限なし) ---
function runCorrection(y, m, d) {
    var mTable = { 1: [7], 2: [4], 4: [2, 7], 7: [1, 4] };
    var dTable = {
        1:  [7],  4:  [7],  7:  [1, 4],
        11: [17], 14: [17], 17: [11, 14],
        21: [27], 24: [27], 27: [21, 24]
    };
    function isOk(dt, targetM, targetD) {
        return (dt.getMonth() === targetM - 1 && dt.getDate() === targetD && dt >= today);
    }
    var validCandidates = [];
    if (mTable[m]) {
        for (var i = 0; i < mTable[m].length; i++) {
            var testM = new Date(y, mTable[m][i] - 1, d);
            if (isOk(testM, mTable[m][i], d)) validCandidates.push(testM);
        }
    }
    if (dTable[d]) {
        for (var j = 0; j < dTable[d].length; j++) {
            var testD = new Date(y, m - 1, dTable[d][j]);
            if (isOk(testD, m, dTable[d][j])) validCandidates.push(testD);
        }
    }
    if (validCandidates.length === 0) return null;
    var closestDate = validCandidates[0];
    var minDiff = closestDate.getTime() - today.getTime();
    for (var k = 1; k < validCandidates.length; k++) {
        var diff = validCandidates[k].getTime() - today.getTime();
        if (diff < minDiff) { minDiff = diff; closestDate = validCandidates[k]; }
    }
    return closestDate;
}
// --- バリデーションエンジン (期間制限なし) ---
function validateAndOutput(y, m, d, isDtmf) {
    var checkDate = new Date(y, m - 1, d);
    if (checkDate.getFullYear() !== y || checkDate.getMonth() !== m - 1 || checkDate.getDate() !== d) {
        output("NO_RESULT"); return;
    }
    if (checkDate >= today) {
        output(formatDate(checkDate));
    } else {
        if (isDtmf) {
            output("NO_RESULT");
        } else {
            // 年指定なし → まず来年の同日で再試行
            var nextYearDate = new Date(y + 1, m - 1, d);
            if (nextYearDate.getMonth() === m - 1 && nextYearDate.getDate() === d) {
                output(formatDate(nextYearDate));
            } else {
                var corrected = runCorrection(y, m, d);
                if (corrected) output(formatDate(corrected));
                else output("NO_RESULT");
            }
        }
    }
}
// --- 3. メインロジック ---
function main(input) {
    if (!input || input === "null" || input === "undefined") {
        output("NO_RESULT"); return;
    }
    // 不明ワード
    var UNKNOWN_RE = /わから[なね]い|わかりません|分から[なね]い|分かりません|わかんない|わかんな[いく]|不明|知らない|知りません|覚えていない|覚えてない|覚えておりません|覚えてません|忘れた|忘れました|忘れてしまいました|思い出せない|思い出せません|記憶にない|記憶がない|はっきりしない|定かでない|決まっていない|決まってない|未定|わからん|知らん|初旬|上旬|中旬|下旬/i;
    if (UNKNOWN_RE.test(input)) { output("不明"); return; }
    // DTMF (数字のみ)
    if (/^\d+$/.test(input)) {
        var dY = 0, dM = 0, dD = 0;
        if (input.length === 8) {
            dY = parseInt(input.substring(0, 4), 10);
            dM = parseInt(input.substring(4, 6), 10);
            dD = parseInt(input.substring(6, 8), 10);
        } else if (input.length === 4) {
            dM = parseInt(input.substring(0, 2), 10);
            dD = parseInt(input.substring(2, 4), 10);
            var thisYearDate = new Date(todayYear, dM - 1, dD);
            dY = (thisYearDate < today) ? todayYear + 1 : todayYear;
        } else {
            output("NO_RESULT"); return;
        }
        validateAndOutput(dY, dM, dD, true);
        return;
    }
    var processed = input;
    // 時刻除去
    processed = processed.replace(/\d{1,2}時(\d{1,2}分)?/g, "");
    // 漢数字変換
    var kanjiNumList = [
        ["三十一","31"],["三十","30"],["二十九","29"],["二十八","28"],
        ["二十七","27"],["二十六","26"],["二十五","25"],["二十四","24"],
        ["二十三","23"],["二十二","22"],["二十一","21"],["二十","20"],
        ["十九","19"],["十八","18"],["十七","17"],["十六","16"],
        ["十五","15"],["十四","14"],["十三","13"],["十二","12"],
        ["十一","11"],["十","10"],
        ["九","9"],["八","8"],["七","7"],["六","6"],
        ["五","5"],["四","4"],["三","3"],["二","2"],["一","1"]
    ];
    for (var ki = 0; ki < kanjiNumList.length; ki++) {
        processed = processed.replace(
            new RegExp(kanjiNumList[ki][0] + "(?=月|日|年)", "g"),
            kanjiNumList[ki][1]
        );
    }
    // 表記ゆれ正規化
    processed = processed
        .replace(/(\d{1,2})月no(\d{1,2})日/gi, "$1月$2日")
        .replace(/(\d{1,2})月no(\d{1,2})(?!\d)/gi, "$1月$2日")
        .replace(/通知/g, "1日")
        .replace(/発火/g, "20日")
        .replace(/(\d{1,2})月[のをにはが](\d{1,2})日/g, "$1月$2日")
        .replace(/(\d{1,2})月[のをにはが](\d{1,2})(?!\d)/g, "$1月$2日")
        .replace(/(\d{1,2})月\s+(\d{1,2})日/g, "$1月$2日")
        .replace(/(\d{1,2})月\s+(\d{1,2})(?!\d)/g, "$1月$2日")
        .replace(/(\d{1,2})の(\d{1,2})日/g, "$1月$2日")
        .replace(/(\d{1,2})の(\d{1,2})/g, "$1月$2日")
        .replace(/(\d{1,2})\/(\d{1,2})/g, "$1月$2日")
        .replace(/(\d{1,2})-(\d{1,2})(?!\d)/g, "$1月$2日");
    // FIX(engine v2 / 2026-07-01): has_月 の取りこぼし回収（scorecard date）
    // Rule A: 数字+十（STT が「さんじゅう」→ `3十` と混在レンダリング）→ ×10。`3十`→`30`。
    processed = processed.replace(/(\d)十(?!\d)/g, function (m0, d1) { return d1 + "0"; });
    // Rule B: 「N月M」（月直後に日数字・末尾に日なし）→ 日を補う。`1月27`/`5月27。`/`5月7のか` を回収。
    //   (?![\d日年]) で二重日付与・桁溢れ(`1月100`)・M月D年 の化け(`1月20年`)を防ぐ。
    //   GUARD: 完成した M月D日 が既存なら不発火（言い直し `3月5ではなく4月10日` で破棄側を予約する M を防ぐ）。
    if (!/(\d{1,2})月(\d{1,2})日/.test(processed)) {
        processed = processed.replace(/(\d{1,2})月(\d{1,2})(?![\d日年])/g, "$1月$2日");
    }
    // 月末処理
    if (processed.indexOf("月末") !== -1) {
        if (processed.indexOf("今月末") !== -1) {
            var endOfThisMonth = new Date(todayYear, today.getMonth() + 1, 0);
            processed = processed.replace(/今月末/g, (today.getMonth() + 1) + "月" + endOfThisMonth.getDate() + "日");
        } else if (processed.indexOf("来月末") !== -1) {
            var endOfNextMonth = new Date(todayYear, today.getMonth() + 2, 0);
            processed = processed.replace(/来月末/g, (endOfNextMonth.getMonth() + 1) + "月" + endOfNextMonth.getDate() + "日");
        } else {
            processed = processed.replace(/(\d{1,2})月末/g, function(match, mo) {
                var eom = new Date(todayYear, parseInt(mo, 10), 0);
                return mo + "月" + eom.getDate() + "日";
            });
        }
    }
    // 相対日付
    var targetDate = null;
    var dayMap = {"日":0,"月":1,"火":2,"水":3,"木":4,"金":5,"土":6};
    if (processed.indexOf("今日") !== -1 || processed.indexOf("本日") !== -1) {
        targetDate = addDays(today, 0);
    } else if (processed.match(/明々後日|しあさって/)) {
        // FIX(2026-06-12): しあさって(+3) を あさって(+2) より先に判定（あさって⊂しあさって の先取り防止）
        targetDate = addDays(today, 3);
    } else if (processed.match(/明後日|あさって|あさて/)) {
        targetDate = addDays(today, 2);
    } else if (processed.match(/明日|あした|みょうにち/)) {
        targetDate = addDays(today, 1);
    } else if (processed.match(/来週の?(月|火|水|木|金|土|日)曜日?/)) {
        // FIX(2026-06-12): 暦週・月曜始まり。「今週の月曜」+ 7日 + 目標曜日(月曜起点オフセット)。
        //   例: 金曜時点の「来週月曜」= 今週月曜 + 7 = 翌週月曜（15日）。
        var mMatch = processed.match(/来週の?(月|火|水|木|金|土|日)曜日?/);
        var thisMonday = addDays(today, -((today.getDay() + 6) % 7));
        targetDate = addDays(thisMonday, 7 + ((dayMap[mMatch[1]] + 6) % 7));
    } else if (processed.match(/今週の?(月|火|水|木|金|土|日)曜日?/)) {
        // FIX(2026-06-12): 暦週・月曜始まり。今週の月曜 + 目標曜日(月曜起点)。過去でも「今週の実日」。
        //   例: 金曜時点の「今週月曜」= 今週の月曜（8日）。
        var twMatch = processed.match(/今週の?(月|火|水|木|金|土|日)曜日?/);
        var twMonday = addDays(today, -((today.getDay() + 6) % 7));
        targetDate = addDays(twMonday, (dayMap[twMatch[1]] + 6) % 7);
    } else if (processed.match(/今月の?(\d{1,2})日?/)) {
        var imMatch = processed.match(/今月の?(\d{1,2})日?/);
        targetDate = new Date(today.getFullYear(), today.getMonth(), parseInt(imMatch[1], 10));
    } else if (processed.match(/来月の?(\d{1,2})日/)) {
        var nMatch = processed.match(/来月の?(\d{1,2})日/);
        targetDate = new Date(today.getFullYear(), today.getMonth() + 1, parseInt(nMatch[1], 10));
    } else if (processed.match(/(\d+)日後/)) {
        var aMatch = processed.match(/(\d+)日後/);
        targetDate = addDays(today, parseInt(aMatch[1], 10));
    } else if (processed.match(/(月|火|水|木|金|土|日)曜日?/) && !/\d{1,2}日/.test(processed)) {
        var dMatch = processed.match(/(月|火|水|木|金|土|日)曜日?/);
        var diff2 = (dayMap[dMatch[1]] - today.getDay() + 7) % 7;
        targetDate = addDays(today, diff2 === 0 ? 7 : diff2);
    }
    if (targetDate) {
        // FIX(2026-06-12): 明示的な相対表現(今日/明日/今週/今月N日/来週/来月N日/N日後)は
        //   名指しの日付をそのまま採用する（過去でも翌年送りしない）。年未指定の裸の数値日付のみ
        //   下の validateAndOutput で翌年/翌月送りする。
        output(formatDate(targetDate));
        return;
    }
    // 元号
    var tY = todayYear, tM = 0, tD = 0;
    var gMatch = processed.match(/(令和|平成|昭和|大正)(\d+|元)年/);
    if (gMatch) {
        var gv = (gMatch[2] === "元") ? 1 : parseInt(gMatch[2], 10);
        if      (gMatch[1] === "令和") tY = gv + 2018;
        else if (gMatch[1] === "平成") tY = gv + 1988;
        else if (gMatch[1] === "昭和") tY = gv + 1925;
        else if (gMatch[1] === "大正") tY = gv + 1911;
    }
    // 西暦年
    var yearMatch = processed.match(/(\d{4})年/);
    if (yearMatch) tY = parseInt(yearMatch[1], 10);
    // 日付抽出 (月あり)
    var mdMatch = processed.match(/(\d{1,2})月(\d{1,2})日/);
    if (mdMatch) {
        tM = parseInt(mdMatch[1], 10);
        tD = parseInt(mdMatch[2], 10);
        validateAndOutput(tY, tM, tD, false);
        return;
    }
    // 月のみ + 日のみ が別々にある場合
    var mOnlyMatch = processed.match(/(\d{1,2})月/);
    var dOnlyMatch = processed.match(/(\d{1,2})日/);
    if (mOnlyMatch && dOnlyMatch) {
        tM = parseInt(mOnlyMatch[1], 10);
        tD = parseInt(dOnlyMatch[1], 10);
        validateAndOutput(tY, tM, tD, false);
        return;
    }
    // 日のみ
    if (dOnlyMatch && !mOnlyMatch) {
        var onlyD = parseInt(dOnlyMatch[1], 10);
        if (onlyD >= 1 && onlyD <= 31) {
            var tempDate = new Date(today.getFullYear(), today.getMonth(), onlyD);
            if (tempDate < today) tempDate = new Date(today.getFullYear(), today.getMonth() + 1, onlyD);
            validateAndOutput(tempDate.getFullYear(), tempDate.getMonth() + 1, tempDate.getDate(), false);
        } else {
            output("NO_RESULT");
        }
        return;
    }
    // 事故①: pin できない曖昧な時期表現は NO_RESULT でループさせず 不明 へ（上旬/中旬/下旬 と統一）
    var VAGUE_PERIOD_RE = /初め頃|初めごろ|始め頃|始めごろ|中頃|なかごろ|半ば|末頃|末ごろ|月初め?|あたり|ぐらい|くらい|頃|ごろ|どこか|どの辺|その辺|その頃/;
    if (VAGUE_PERIOD_RE.test(processed)) { output("不明"); return; }
    output("NO_RESULT");
}
// --- 4. 実行 ---
main(rawInput);
