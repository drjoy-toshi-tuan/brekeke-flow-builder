// Script Template: business_hour_classifier
// 着信日時もしくは指定日時を施設の営業ルール (曜日別営業時間 + 固定休 + 祝日 + Note 連携)
// と照合し、営業中 / 営業時間外 / 定休日 / 祝日 / 固定休 / ERROR の 6 分岐に仕分ける。
//
// プレースホルダー (scaffold_generator が template_params で置換):
//   WEEKDAY_SCHEDULE  — 曜日別営業時間 (例: "mon=09:00-18:00,...,sat=closed,sun=closed")
//   CLOSED_DATES      — 固定休 mm-dd 列 (例: "12-29,12-30,12-31,01-02,01-03")。空文字可
//   NATIONAL_HOLIDAY  — "closed" (祝日休) / "open" (祝日も営業)
//   HOLIDAY_NOTE_NAME — 祝日マスタ Note 名 (例: "drjoy.holidays"、multi-tenant 規約 tenant.note)
//   TARGET_DATETIME   — "now" / yyyy-MM-dd[ HH:mm[:ss]] リテラル / context 参照
//
// 出力: $runner.setResult() で 営業中/営業時間外/定休日/祝日/固定休/ERROR のいずれか。
//       設計書側で 6 個の jumps (^営業中$ ^営業時間外$ ^定休日$ ^祝日$ ^固定休$ ^ERROR$) を配線する。
// 参照: docs/brekeke/script_templates/README.md、modules/business_hour_classifier/REQUIREMENTS.md

// CONFIG — 施設ごとに調整。営業時間/独自休/祝日 Note 名を施設業務ルールに合わせて編集
// =============================================================================
// 曜日別営業時間: <weekday>=HH:MM-HH:MM か closed。指定なしの曜日は定休扱い
//   例: 水曜午後休 → "wed=09:00-12:00"、24h営業 → "mon=00:00-23:59,..."
var WEEKDAY_SCHEDULE = "{{WEEKDAY_SCHEDULE}}";

// 毎年の固定休 (mm-dd 列): 年末年始、お盆休み、創立記念日等。空文字なら無し
var CLOSED_DATES = "{{CLOSED_DATES}}";

// 国民の祝日扱い: "closed"=祝日休 / "open"=祝日も営業 (ER対応病院等)
var NATIONAL_HOLIDAY = "{{NATIONAL_HOLIDAY}}";

// 祝日マスタ Note 名 (Brekeke 管理画面 Note。多年同居、年初末尾追記運用)
var HOLIDAY_NOTE_NAME = "{{HOLIDAY_NOTE_NAME}}";

// 判定対象日時: 下記の書式のいずれか (それ以外は ERROR 出力)
//   "now"                       ← 着信時刻 (IVR セッション開始時刻) を使う ★既定、一般的にはこれ
//   "yyyy-MM-dd HH:mm:ss"       ← リテラル日時 (例: "2026-05-29 12:00:00")
//                                 ※ saveContext2DB の DATE 型保存形式と同一
//   "yyyy-MM-dd HH:mm"          ← 秒省略 (例: "2026-05-29 12:00")
//   "yyyy-MM-dd"                ← 日付のみ (例: "2026-05-29") → date-only 判定
//   "yyyy-MM-ddTHH:mm:ss"       ← ISO 8601 (T 区切り、例: "2026-05-29T12:00:00")
//   "yyyy-MM-ddTHH:mm"          ← ISO 8601 秒省略
//   "<%contextName%>"           ← Brekeke session context 値を参照
//                                 例: "<%currentAppointmentDate%>" → 上流 saveContext2DB の値を読む
//                                 内部で $ivr.exec("system-variable", "getSystemVariableValue", name) 呼び出し
//
// 受け付け不可: スラッシュ区切り "yyyy/MM/dd" / 和暦・自由発話 "5月15日" / 全角数字 / null など
var TARGET_DATETIME = "{{TARGET_DATETIME}}";

// 過去日判定の基準「今日」: 予約受付特性上「過去その日時に営業していたか」は不要なため、
// TARGET_DATETIME の日付がこの基準日より前 (= 過去日) なら、曜日/祝日/固定休に関わらず
// 一律「営業時間外」に倒す (日付単位比較。同じ今日の過ぎた時刻枠は過去扱いしない)。
// 本番は "now" (= 着信時刻) 固定。固定日付の注入は受入テスト専用なのでプレースホルダー化しない。
var REFERENCE_DATE = "now";

// =============================================================================
// LOGIC — 編集禁止 (バグ修正・機能追加時は元 repo 側を更新)
// =============================================================================

var JavaDate = Java.type("java.util.Date");
var SimpleDateFormat = Java.type("java.text.SimpleDateFormat");
var NoteUtils = Java.type("com.brekeke.pbx.common.NoteUtils");
var Calendar = java.util.Calendar;
var TimeZone = java.util.TimeZone;

var tz = TimeZone.getTimeZone("Asia/Tokyo");

// CONFIG から内部変数へ
var targetDatetime  = TARGET_DATETIME;
var referenceDate   = REFERENCE_DATE;
var weekdaySchedule = WEEKDAY_SCHEDULE;
var closedDates     = CLOSED_DATES;
var nationalHoliday = NATIONAL_HOLIDAY;
var holidayNoteName = HOLIDAY_NOTE_NAME;

// `<%varName%>` 形式の Brekeke 変数参照を session context から解決
// (script 本文は Brekeke の自動置換対象外のため、ここで明示的に解決する)
// 参照解決 API: $ivr.exec("system-variable", "getSystemVariableValue", varName)
var varRefPattern = /^<%\s*([\w\-]+)\s*%>$/;
function resolveVarRef(value) {
    var m = ("" + value).match(varRefPattern);
    if (!m) return value;
    var varName = m[1];
    try {
        var resolved = $ivr.exec("system-variable", "getSystemVariableValue", varName);
        $runner.getLogger().info("[BusinessHour] resolved <%" + varName + "%> -> " + resolved);
        return (resolved === null || resolved === undefined) ? "" : ("" + resolved);
    } catch (e) {
        $runner.getLogger().warn("[BusinessHour] var resolution failed for <%" + varName + "%>: " + (e && e.message ? e.message : e));
        return value;  // fallback to literal (= 後段の parser が ERROR 判定する)
    }
}
targetDatetime = resolveVarRef(targetDatetime);
referenceDate  = resolveVarRef(referenceDate);

$runner.getLogger().info("[BusinessHour] params target=" + targetDatetime
  + " reference=" + referenceDate
  + " schedule=" + weekdaySchedule
  + " closed=" + closedDates
  + " national=" + nationalHoliday
  + " holiday_note=" + holidayNoteName);

// datetime 文字列 (もしくは "now") → Calendar。parse 不能なら throw。
// "now" は着信時刻 (timeStart)、それ以外は yyyy-MM-dd[ HH:mm[:ss]] / ISO8601(T区切り) を受理。
function parseToCalendar(value, label) {
    var c = Calendar.getInstance(tz);
    if (value === "now") {
        c.setTimeInMillis($ivr.getEx().ivr.timeStart);
        return c;
    }
    // accept "yyyy-MM-dd HH:mm:ss" or "yyyy-MM-dd HH:mm" or "yyyy-MM-dd" (T 区切りも可)
    var s = ("" + value).trim();
    var fmt;
    if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}$/.test(s)) {
        fmt = "yyyy-MM-dd HH:mm:ss"; s = s.replace("T", " ");
    } else if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}$/.test(s)) {
        fmt = "yyyy-MM-dd HH:mm"; s = s.replace("T", " ");
    } else if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
        fmt = "yyyy-MM-dd";
    } else {
        throw new Error("unsupported " + label + " format: " + s);
    }
    var sdf = new SimpleDateFormat(fmt);
    sdf.setTimeZone(tz);
    c.setTime(sdf.parse(s));
    return c;
}

// ---------- 1. target / reference datetime → Calendar ----------
var cal, nowCal;
try {
    cal = parseToCalendar(targetDatetime, "target_datetime");
} catch (e) {
    $runner.getLogger().error("[BusinessHour] target_datetime parse error: " + e.message);
    $runner.setResult("ERROR");
    return;
}
try {
    nowCal = parseToCalendar(referenceDate, "reference_date");
} catch (e) {
    $runner.getLogger().error("[BusinessHour] reference_date parse error: " + e.message);
    $runner.setResult("ERROR");
    return;
}

var year   = cal.get(Calendar.YEAR);
var month  = cal.get(Calendar.MONTH) + 1;
var day    = cal.get(Calendar.DATE);
var hour   = cal.get(Calendar.HOUR_OF_DAY);
var minute = cal.get(Calendar.MINUTE);
var dowIdx = cal.get(Calendar.DAY_OF_WEEK); // SUNDAY=1..SATURDAY=7
var dowKey = ["", "sun", "mon", "tue", "wed", "thu", "fri", "sat"][dowIdx];
var pad = function(n){ return (n < 10 ? "0" : "") + n; };
var mmdd = pad(month) + "-" + pad(day);
var yyyymmdd = year + "-" + pad(month) + "-" + pad(day);
var hhmmNum = hour * 100 + minute;

$runner.getLogger().info("[BusinessHour] resolved " + yyyymmdd
  + " " + pad(hour) + ":" + pad(minute)
  + " dow=" + dowKey);

// ---------- 1.5 過去日ガード ----------
// 予約受付特性上「過去その日時に営業していたか」を返す必要はないため、
// 対象日が基準日 (今日) より前なら、曜日/祝日/固定休に関わらず一律「営業時間外」に倒す。
// 比較は日付単位 (時刻は無視) — 同じ今日の過ぎた時刻枠は過去扱いしない (2026-06-04 確定)。
function dateInt(c){ return c.get(Calendar.YEAR) * 10000 + (c.get(Calendar.MONTH) + 1) * 100 + c.get(Calendar.DATE); }
var targetDateInt = dateInt(cal);
var refDateInt    = dateInt(nowCal);
if (targetDateInt < refDateInt) {
    $runner.getLogger().info("[BusinessHour] => 営業時間外 (past date: target " + targetDateInt + " < reference " + refDateInt + ")");
    $runner.setResult("営業時間外");
    return;
}

// ---------- 2. 固定休 (closed_dates) ----------
try {
    if (closedDates && closedDates.length > 0) {
        var list = closedDates.split(",");
        for (var i = 0; i < list.length; i++) {
            if (list[i].trim() === mmdd) {
                $runner.getLogger().info("[BusinessHour] => 固定休 (matched " + mmdd + ")");
                $runner.setResult("固定休");
                return;
            }
        }
    }
} catch (e) {
    $runner.getLogger().error("[BusinessHour] closed_dates parse error: " + e.message);
    $runner.setResult("ERROR");
    return;
}

// ---------- 3. 祝日 (Brekeke Note 経由で取得、外部 HTTP 通信なし) ----------
// 設計方針: 単一 Note に複数年分を詰める ([[project_business_hour_classifier]] 2026-05-29 確定)。
//   翌年の予約が当年中に入ってくる業務特性を踏まえ、Note を年単位で持たず多年同居させて
//   「来年分を作り忘れる」事故を構造的に防ぐ。年初運用は末尾に追記するだけ。
// Note 本文: 1 行 1 件 yyyy-MM-dd 形式 (年混在 OK、空行 OK、先頭/末尾 whitespace 無視)。
// Note 不在/読取り失敗時は祝日チェックを fail-open でスキップ (営業時間判定にフォールスルー)。
if (nationalHoliday === "closed") {
    try {
        if (NoteUtils.exists(holidayNoteName)) {
            var raw = NoteUtils.read(holidayNoteName);
            if (raw !== null && raw !== undefined && ("" + raw).length > 0) {
                var lines = ("" + raw).split(/\r?\n/);
                for (var i = 0; i < lines.length; i++) {
                    if (lines[i].trim() === yyyymmdd) {
                        $runner.getLogger().info("[BusinessHour] => 祝日 (matched " + yyyymmdd + " via Note " + holidayNoteName + ")");
                        $runner.setResult("祝日");
                        return;
                    }
                }
            }
        } else {
            $runner.getLogger().warn("[BusinessHour] Note " + holidayNoteName + " not found; skipping 祝日 check");
        }
    } catch (e) {
        $runner.getLogger().error("[BusinessHour] NoteUtils error: " + (e && e.message ? e.message : e));
        // Note 読取り失敗は ERROR ではなく fail-open で曜日判定にフォールスルー
    }
}

// ---------- 4. weekday_schedule で曜日別判定 ----------
try {
    var scheduleMap = {};
    var entries = weekdaySchedule.split(",");
    for (var j = 0; j < entries.length; j++) {
        var kv = entries[j].split("=");
        if (kv.length !== 2) continue;
        scheduleMap[kv[0].trim()] = kv[1].trim();
    }
    var todaySpec = scheduleMap[dowKey];
    if (todaySpec === undefined || todaySpec === "" || todaySpec === "closed") {
        $runner.getLogger().info("[BusinessHour] => 定休日 (" + dowKey + "=" + todaySpec + ")");
        $runner.setResult("定休日");
        return;
    }
    var m = /^(\d{2}):(\d{2})-(\d{2}):(\d{2})$/.exec(todaySpec);
    if (!m) {
        throw new Error("invalid schedule entry: " + dowKey + "=" + todaySpec);
    }
    var openNum  = parseInt(m[1], 10) * 100 + parseInt(m[2], 10);
    var closeNum = parseInt(m[3], 10) * 100 + parseInt(m[4], 10);
    // 時刻 00:00 (= DATE 型 context or yyyy-MM-dd リテラル) は「日付のみの判定」とみなし、
    // 営業時間外チェックをスキップして営業日扱い (= 営業中) を返す。予約日が営業日か等の用途。
    if (hhmmNum === 0) {
        $runner.getLogger().info("[BusinessHour] => 営業中 (date-only input: " + dowKey + "=" + todaySpec + ", time check skipped)");
        $runner.setResult("営業中");
    } else if (hhmmNum >= openNum && hhmmNum < closeNum) {
        $runner.getLogger().info("[BusinessHour] => 営業中 (" + todaySpec + ")");
        $runner.setResult("営業中");
    } else {
        $runner.getLogger().info("[BusinessHour] => 営業時間外 (in_range_of=" + todaySpec + ")");
        $runner.setResult("営業時間外");
    }
} catch (e) {
    $runner.getLogger().error("[BusinessHour] schedule parse error: " + e.message);
    $runner.setResult("ERROR");
}
