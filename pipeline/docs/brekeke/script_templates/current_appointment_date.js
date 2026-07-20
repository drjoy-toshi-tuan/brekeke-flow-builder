var JavaDate = Java.type("java.util.Date");
var SimpleDateFormat = Java.type("java.text.SimpleDateFormat");
var logger = $runner.getLogger();
var INPUT_MODULE = "入力_現在の予約日";
var CONTEXT_NAME = "currentAppointmentDate";
var CONTEXT_DISPLAY_TYPE = "DATE";

// === コンテキスト保存 ===
function _saveCheckpoint(v){try{if(!$ivr.connected())return;$ivr.exec("save2db","save",JSON.stringify({contextField:{contextName:"checkpoint",displayType:"TEXT",value:v}}));}catch(e){logger.error("[ctx]"+e);}}
function _setObj(k,v){try{$ivr.setObject(k,v);}catch(e){logger.error("[ctx]"+e);}}
function saveContext(val,name,type){var rid=$ivr.getRID();var mod=$runner.getCurrentModuleName();_saveCheckpoint(mod+"_IN");_setObj("checkpoint."+rid,mod+"_IN");if(name&&val){var r=JSON.stringify({contextField:{contextName:name,displayType:type||"TEXT",value:val}});logger.info("[saveContext2DB] "+r);try{$ivr.exec("save2db","save",r);$runner.setObject(name,val);}catch(e){logger.error("[ctx]"+e);}}_saveCheckpoint(mod+"_OUT");_setObj("checkpoint."+rid,mod+"_OUT");_setObj("saveContext."+rid,true);}

// === 漢数字→算用数字 ===
function kanjiToNum(str) {
    var s = str;
    var kanjiDigits = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9};
    var kanjiTens = {"十":10,"二十":20,"三十":30,"四十":40,"五十":50};
    s = s.replace(/二千(\d*)/g, function(m, rest) { return "2" + (rest || "000").substring(0,3); });
    s = s.replace(/千九百/g, "19").replace(/千/g, "1");
    for (var tk in kanjiTens) {
        var tv = kanjiTens[tk];
        for (var dk in kanjiDigits) { s = s.split(tk + dk).join(String(tv + kanjiDigits[dk])); }
        s = s.split(tk).join(String(tv));
    }
    for (var k in kanjiDigits) { s = s.split(k).join(String(kanjiDigits[k])); }
    s = s.replace(/〇/g, "0").replace(/零/g, "0");
    return s;
}

// === ひらがな月→数字 ===
function hiraMonthToNum(s) {
    var map = {
        "いちがつ":"1","にがつ":"2","さんがつ":"3","しがつ":"4","ごがつ":"5","ろくがつ":"6",
        "しちがつ":"7","なながつ":"7","はちがつ":"8","くがつ":"9","きゅうがつ":"9",
        "じゅうがつ":"10","じゅういちがつ":"11","じゅうにがつ":"12"
    };
    for (var k in map) { s = s.split(k).join(map[k] + "月"); }
    return s;
}

// === ひらがな日→数字 ===
function hiraDayToNum(s) {
    var map = {
        "ついたち":"1","ふつか":"2","みっか":"3","よっか":"4","いつか":"5",
        "むいか":"6","なのか":"7","ようか":"8","ここのか":"9","とおか":"10",
        "じゅういちにち":"11","じゅうににち":"12","じゅうさんにち":"13","じゅうよっか":"14","じゅうごにち":"15",
        "じゅうろくにち":"16","じゅうしちにち":"17","じゅうはちにち":"18","じゅうくにち":"19","はつか":"20",
        "にじゅういちにち":"21","にじゅうににち":"22","にじゅうさんにち":"23","にじゅうよっか":"24",
        "にじゅうごにち":"25","にじゅうろくにち":"26","にじゅうしちにち":"27","にじゅうはちにち":"28",
        "にじゅうくにち":"29","さんじゅうにち":"30","さんじゅういちにち":"31"
    };
    for (var k in map) { s = s.split(k).join(map[k] + "日"); }
    return s;
}

// === 相対日付 ===
function resolveRelativeDate(s, raw) {
    var tz = java.util.TimeZone.getTimeZone("Asia/Tokyo");
    var cal = java.util.Calendar.getInstance(tz);

    // 過去日 (raw 参照: kanjiToNum で「一」→「1」変換される前の元入力を検査)
    if (/一昨日|おととい|いっさくじつ/.test(raw)) { cal.add(java.util.Calendar.DATE, -2); return cal; }
    if (/昨日|きのう/.test(raw)) { cal.add(java.util.Calendar.DATE, -1); return cal; }

    if (/明々後日|しあさって/.test(s)) { cal.add(java.util.Calendar.DATE, 3); return cal; }
    if (/明後日|あさって|みょうごにち/.test(s)) { cal.add(java.util.Calendar.DATE, 2); return cal; }
    if (/明日|あした|あす|みょうにち/.test(s)) { cal.add(java.util.Calendar.DATE, 1); return cal; }
    if (/今日|きょう|本日/.test(s)) { return cal; }

    // 来週/再来週の◯曜日
    var weekdayMap = {"月":java.util.Calendar.MONDAY,"火":java.util.Calendar.TUESDAY,"水":java.util.Calendar.WEDNESDAY,"木":java.util.Calendar.THURSDAY,"金":java.util.Calendar.FRIDAY,"土":java.util.Calendar.SATURDAY,"日":java.util.Calendar.SUNDAY};
    var wm = s.match(/(来週|再来週).*?(月|火|水|木|金|土|日)曜/);
    if (wm) {
        var targetDow = weekdayMap[wm[2]];
        if (targetDow !== undefined) {
            var weeksAhead = (wm[1] === "再来週") ? 2 : 1;
            var currentDow = cal.get(java.util.Calendar.DAY_OF_WEEK);
            var daysUntilMonday = (java.util.Calendar.MONDAY - currentDow + 7) % 7;
            if (daysUntilMonday === 0) daysUntilMonday = 7;
            cal.add(java.util.Calendar.DATE, daysUntilMonday + (weeksAhead - 1) * 7);
            var daysFromMonday = (targetDow - java.util.Calendar.MONDAY + 7) % 7;
            cal.add(java.util.Calendar.DATE, daysFromMonday);
            return cal;
        }
    }

    // 今週の◯曜日 (今日の曜日から今週月曜まで戻ってから target 曜日まで進む。過去/未来両方ありえる)
    var twm = s.match(/今週.*?(月|火|水|木|金|土|日)曜/);
    if (twm) {
        var targetDow2 = weekdayMap[twm[1]];
        if (targetDow2 !== undefined) {
            var currentDow2 = cal.get(java.util.Calendar.DAY_OF_WEEK);
            var daysToCurrentMonday = (currentDow2 - java.util.Calendar.MONDAY + 7) % 7;
            cal.add(java.util.Calendar.DATE, -daysToCurrentMonday);
            var daysFromMonday2 = (targetDow2 - java.util.Calendar.MONDAY + 7) % 7;
            cal.add(java.util.Calendar.DATE, daysFromMonday2);
            return cal;
        }
    }
    return null;
}

// ================================================================
// メイン処理
// ================================================================
var rawInput = $runner.getResult(INPUT_MODULE);
logger.info("[date_current] rawInput: " + rawInput);

var result = "ERROR";
var dbValue = "ERROR";

if (rawInput !== null && rawInput !== undefined && rawInput !== "") {
    var s = String(rawInput);

    // --- STEP 0: STT雑音・フィラー除去 ---
    s = s.replace(/[%％]/g, " ");
    s = s.replace(/[\s　\r\n\t]+/g, " ").replace(/^ +| +$/g, "");

    var FILLER_NOISE = [
        "えーっと", "えーと", "えっと", "えー", "えぇ", "あのー", "あの",
        "うーん", "うん", "まあ", "その", "ええと", "ああ", "おー",
        "そうですね", "ちょっと", "なんか", "あれ", "これ", "それ",
        "ありがとう", "ありがとうございます", "お願いします", "お願い",
        "すみません", "すいません", "はい", "予約日は", "予約は"
    ];
    var segments = s.split(" ");
    var cleaned = [];
    for (var fi = 0; fi < segments.length; fi++) {
        var seg = segments[fi].replace(/[、。,.!?！？]/g, "");
        var isNoise = false;
        for (var ni = 0; ni < FILLER_NOISE.length; ni++) {
            if (seg === FILLER_NOISE[ni]) { isNoise = true; break; }
        }
        if (!isNoise && seg.length > 0) {
            if (!/[0-9０-９月日年曜一二三四五六七八九十来再週今明本]/.test(seg)
                && !/がつ|にち|ねん|しゅう|きょう|きのう|あした|あす|あさって|みょう|ほんじつ|おととい|いっさくじつ|らいしゅう|らいげつ/.test(seg)
                && !/わからない|わかりません|わかんない|分から|不明|ふめい|覚えて|おぼえ|忘れ|わすれ|知らない|しらない|未定|みてい/.test(seg)) {
                isNoise = true;
                logger.info("[date_current] noise removed: " + seg);
            }
        }
        if (!isNoise && seg.length > 0) { cleaned.push(seg); }
    }
    s = cleaned.join("");
    logger.info("[date_current] step0 cleaned: " + s);

    // --- STEP 1: 正規化 ---
    s = s.replace(/[、。,.!?！？]/g, "");
    s = s.replace(/(です|でお願いします|お願いします|なんですけど|にお願い)$/g, "");
    s = s.replace(/[\uFF10-\uFF19]/g, function(c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    s = s.replace(/月の/g, "月");

    logger.info("[date_current] step1 normalized: " + s);

    // --- STEP 2: ひらがな→数字変換 ---
    s = hiraMonthToNum(s);
    s = hiraDayToNum(s);
    s = kanjiToNum(s);

    logger.info("[date_current] step2 converted: " + s);

    var tz = java.util.TimeZone.getTimeZone("Asia/Tokyo");
    var dateFormat = new SimpleDateFormat("yyyyMMdd");
    dateFormat.setTimeZone(tz);
    var todayStr = dateFormat.format(new JavaDate());
    var todayYear = parseInt(todayStr.substring(0, 4), 10);
    var todayMonth = parseInt(todayStr.substring(4, 6), 10);
    var todayDay = parseInt(todayStr.substring(6, 8), 10);

    var year = null, month = null, day = null;
    var ERA_MAP = {"令和":2018,"れいわ":2018,"平成":1988,"へいせい":1988,"昭和":1925,"しょうわ":1925,"大正":1911};

    try {
        // --- STEP 3: 相対日付 ---
        var relCal = resolveRelativeDate(s, String(rawInput));
        if (relCal !== null) {
            year = relCal.get(java.util.Calendar.YEAR);
            month = relCal.get(java.util.Calendar.MONTH) + 1;
            day = relCal.get(java.util.Calendar.DATE);
        }

        // --- STEP 4: 具体日付パース ---
        // YYYY年MM月DD日 / YYYY-MM-DD / YYYY/MM/DD
        if (year === null) {
            var m1 = s.match(/(\d{4})[年\-\/](\d{1,2})[月\-\/]?(\d{1,2})?/);
            if (m1) {
                year = parseInt(m1[1], 10);
                month = parseInt(m1[2], 10);
                day = m1[3] ? parseInt(m1[3], 10) : null;
            }
        }

        // 和暦N年M月D日
        if (year === null) {
            for (var era in ERA_MAP) {
                var m2 = s.match(new RegExp(era + "(\\d{1,2})年(\\d{1,2})月(\\d{1,2})"));
                if (m2) {
                    year = ERA_MAP[era] + parseInt(m2[1], 10);
                    month = parseInt(m2[2], 10);
                    day = parseInt(m2[3], 10);
                    break;
                }
            }
        }

        // M月D日 / M月D
        if (year === null) {
            var m3 = s.match(/(\d{1,2})月(\d{1,2})/);
            if (m3) {
                month = parseInt(m3[1], 10);
                day = parseInt(m3[2], 10);
                var isPast = (month < todayMonth) || (month === todayMonth && day < todayDay);
                year = isPast ? todayYear + 1 : todayYear;
            }
        }

        // D日のみ
        if (year === null) {
            var m4 = s.match(/(\d{1,2})日/);
            if (m4) {
                day = parseInt(m4[1], 10);
                month = todayMonth;
                year = todayYear;
                if (day < todayDay) {
                    month++;
                    if (month > 12) { month = 1; year++; }
                }
            }
        }

        // 数字のみ (DTMF: 8桁 YYYYMMDD / 4桁 MMDD)
        if (year === null) {
            var m5 = s.match(/^(\d{8})$/);
            if (m5) {
                year = parseInt(m5[1].substring(0, 4), 10);
                month = parseInt(m5[1].substring(4, 6), 10);
                day = parseInt(m5[1].substring(6, 8), 10);
            }
        }
        if (year === null) {
            var m6 = s.match(/^(\d{3,4})$/);
            if (m6) {
                var digits = m6[1];
                if (digits.length === 4) {
                    month = parseInt(digits.substring(0, 2), 10);
                    day = parseInt(digits.substring(2, 4), 10);
                } else if (digits.length === 3) {
                    month = parseInt(digits.substring(0, 1), 10);
                    day = parseInt(digits.substring(1, 3), 10);
                }
                if (month !== null && day !== null) {
                    var isPast2 = (month < todayMonth) || (month === todayMonth && day < todayDay);
                    year = isPast2 ? todayYear + 1 : todayYear;
                }
            }
        }

        // --- STEP 5: 日付フォーマット・妥当性検証 ---
        if (year !== null && month !== null && day !== null && month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            var cal = java.util.Calendar.getInstance(tz);
            cal.setLenient(false);
            cal.clear();
            cal.set(year, month - 1, day, 0, 0, 0);
            try {
                cal.getTime();
                var mm = (month < 10 ? "0" : "") + month;
                var dd = (day < 10 ? "0" : "") + day;
                // DB保存: YYYY-MM-DD 00:00:00 (script_3days分岐が参照する形式)
                dbValue = year + "-" + mm + "-" + dd + " 00:00:00";
                // 読み上げ用
                var wasWareki = /令和|平成|昭和|大正|れいわ|へいせい|しょうわ|たいしょう/.test(String(rawInput));
                if (wasWareki) {
                    var eraName = ""; var eraYear = 0;
                    if (year >= 2019) { eraName = "令和"; eraYear = year - 2018; }
                    else if (year >= 1989) { eraName = "平成"; eraYear = year - 1988; }
                    else if (year >= 1926) { eraName = "昭和"; eraYear = year - 1925; }
                    else { eraName = "大正"; eraYear = year - 1911; }
                    result = eraName + eraYear + "年" + month + "月" + day + "日";
                } else {
                    result = month + "月" + day + "日";
                }
            } catch (e) {
                logger.warn("[date_current] invalid date: " + year + "-" + month + "-" + day);
            }
        }

        // --- STEP 6: 「わからない」系 ---
        if (result === "ERROR" && /わからない|わかりません|わかんない|分からない|分かりません|不明|ふめい|覚えてない|覚えていない|おぼえてない|おぼえていない|忘れた|わすれた|忘れました|わすれました|知らない|しらない|未定|みてい/.test(s)) {
            result = "分からない";
            dbValue = "分からない";
        }

        // --- STEP 7: フォールバック ---
        if (result === "ERROR" && s.length > 0) {
            if (/^(えー[っとー]*|えっと|えーっと|あのー?|うーん?|まあ|その|ん+)+$/.test(s)) {
                result = "ERROR";
            } else {
                result = s;
                dbValue = s;
                logger.info("[date_current] freetext fallback: " + s);
            }
        }

    } catch (e) {
        logger.error("[date_current] error: " + e);
    }
}

logger.info("[date_current] result=" + result + " dbValue=" + dbValue);
$runner.setResult(result);
// saveContext: DB保存 (YYYY-MM-DD 00:00:00 / 分からない)
saveContext(dbValue, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);