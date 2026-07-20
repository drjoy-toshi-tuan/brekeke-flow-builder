// ==================================================================
// 1. ユーティリティ関数 (Utility Functions)
// ==================================================================

function getTranscribe(prompt) {
    if (!prompt) return "";
    var match = prompt.match(/\{tts_g:([^}]*)\}/);
    if (!match) {
        return prompt.replace(/\{/g, "").replace(/\}/g, "");
    }
    return match[1];
}

function normalizeInput(value) {
    if (!value) return "INVALID";
    var sVal = String(value);
    var dtmfPattern = /^(\d{4})(\d{2})(\d{2})$/;
    if (dtmfPattern.test(sVal)) {
        var match = sVal.match(dtmfPattern);
        sVal = match[1] + "-" + match[2] + "-" + match[3] + " 00:00";
    }
    var formatPattern = /^(\d{2,4})-(\d{2})-(\d{2}) \d{2}:\d{2}$/;
    if (!formatPattern.test(sVal)) return "INVALID";
    return sVal;
}

// ==================================================================
// 1.1 Kanji/全角数字 → 半角数字変換
// ==================================================================
function normalizeNumbers(text) {
    if (!text) return "";
    var result = text;

    // 全角数字 → 半角 (全角文字を正しくマッピング)
    var zenkakuMap = {
        "０":"0","１":"1","２":"2","３":"3","４":"4",
        "５":"5","６":"6","７":"7","８":"8","９":"9"
    };
    for (var k in zenkakuMap) {
        result = result.split(k).join(zenkakuMap[k]);
    }

    // 漢数字 → 半角数字 (十の位対応)
    result = result.replace(/([一二三四五六七八九])?十([一二三四五六七八九])?/g, function(_, tens, ones) {
        var kanjiDigit = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9};
        var t = tens ? kanjiDigit[tens] : 1;
        var o = ones ? kanjiDigit[ones] : 0;
        return String(t * 10 + o);
    });

    // 残った単独の漢数字
    var kanjiDigitMap = {
        "零":"0","〇":"0","一":"1","二":"2","三":"3","四":"4",
        "五":"5","六":"6","七":"7","八":"8","九":"9"
    };
    for (var k2 in kanjiDigitMap) {
        result = result.split(k2).join(kanjiDigitMap[k2]);
    }

    return result;
}

// ==================================================================
// 1.2 Era alias 正規化
// ==================================================================
function normalizeEra(text) {
    if (!text) return "";
    var eraAliases = {
        "昭和": ["昭和", "しょうわ", "ショウワ", "唱和", "社長は", "少和", "名所", "正和", "うわー", "うわ", "今日は"],
        "平成": ["平成", "へいせい", "ヘイセイ", "平静", "閉成", "平清"],
        "令和": ["令和", "れいわ", "レイワ", "例は", "冷和", "例話"],
        "大正": ["大正", "たいしょう", "タイショウ", "対象", "大将", "大賞", "大勝", "対照"],
        "明治": ["明治", "めいじ", "メイジ", "命じ", "銘じ", "明示"]
    };
    var result = text;
    for (var era in eraAliases) {
        var aliases = eraAliases[era];
        for (var i = 0; i < aliases.length; i++) {
            if (aliases[i] === era) continue;
            result = result.split(aliases[i]).join(era);
        }
    }
    return result;
}

// ==================================================================
// 1.3 妥当性チェック
// ==================================================================
function isValidDate(y, m, d) {
    if (!y || !m || !d) return false;
    if (m < 1 || m > 12) return false;
    if (d < 1 || d > 31) return false;
    var daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    var isLeap = (y % 4 === 0 && y % 100 !== 0) || (y % 400 === 0);
    if (m === 2 && isLeap) daysInMonth[1] = 29;
    return d <= daysInMonth[m - 1];
}

// ==================================================================
// 1.3.1 元号年の範囲チェック
// ==================================================================
function isValidEraYear(era, eraY) {
    if (era === "明治") return eraY >= 1 && eraY <= 45;
    if (era === "大正") return eraY >= 1 && eraY <= 15;
    if (era === "昭和") return eraY >= 1 && eraY <= 64;
    if (era === "平成") return eraY >= 1 && eraY <= 31;
    if (era === "令和") {
        var maxReiwaYear = new Date().getFullYear() - 2018;
        return eraY >= 1 && eraY <= maxReiwaYear;
    }
    return false;
}

function toWareki(dateStr) {
    var datePart = dateStr.split(" ")[0];
    var bits = datePart.split("-");
    var y = parseInt(bits[0], 10), m = parseInt(bits[1], 10), d = parseInt(bits[2], 10);
    var date = new Date(y, m - 1, d);
    var eras = [
        { name: "令和", start: new Date(2019, 4, 1) },
        { name: "平成", start: new Date(1989, 0, 8) },
        { name: "昭和", start: new Date(1926, 11, 25) },
        { name: "大正", start: new Date(1912, 6, 30) },
        { name: "明治", start: new Date(1868, 0, 25) }
    ];
    for (var i = 0; i < eras.length; i++) {
        if (date >= eras[i].start) {
            var era = eras[i];
            var eraYear = y - era.start.getFullYear() + 1;
            var yearStr = (eraYear === 1) ? "元" : String(eraYear);
            return era.name + yearStr + "年" + m + "月" + d + "日";
        }
    }
    return "明治以前";
}

function toSeireki(dateStr) {
    var bits = dateStr.split(" ")[0].split("-");
    return bits[0] + "年" + parseInt(bits[1], 10) + "月" + parseInt(bits[2], 10) + "日";
}

function warekiToStandardDate(warekiStr) {
    var match = warekiStr.match(/(明治|大正|昭和|平成|令和)(元|\d+)年(\d+)月(\d+)日/);
    if (!match) return "INVALID";
    var era = match[1];
    var yStr = match[2];
    var m = parseInt(match[3], 10);
    var d = parseInt(match[4], 10);
    var eraY = (yStr === "元") ? 1 : parseInt(yStr, 10);

    if (!isValidEraYear(era, eraY)) return "INVALID";

    var seirekiY = 0;
    if (era === "令和")      seirekiY = 2018 + eraY;
    else if (era === "平成") seirekiY = 1988 + eraY;
    else if (era === "昭和") seirekiY = 1925 + eraY;
    else if (era === "大正") seirekiY = 1911 + eraY;
    else if (era === "明治") seirekiY = 1867 + eraY;

    if (!isValidDate(seirekiY, m, d)) return "INVALID";
    var mm = m < 10 ? "0" + m : String(m);
    var dd = d < 10 ? "0" + d : String(d);
    return seirekiY + "-" + mm + "-" + dd + " 00:00";
}

function isAgeOver120(baseDateStr) {
    if (baseDateStr === "INVALID") return false;
    var yearPart = baseDateStr.split("-")[0];
    if (yearPart.length < 4) return true;
    var year = parseInt(yearPart, 10);
    var currentYear = new Date().getFullYear();
    return (currentYear - year) > 120;
}

function isFutureDate(baseDateStr) {
    if (baseDateStr === "INVALID") return false;
    var parts = baseDateStr.split(" ")[0].split("-");
    var inputDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    return inputDate.getTime() > today.getTime();
}

// ==================================================================
// 1.4 「の」誤認識補正 (Rule 0-6)
// 数字 + no/No/NO(.?) + 数字 のみ → の に変換
// それ以外の no 変換は禁止
// ==================================================================
function normalizeNoParticle(text) {
    if (!text) return text;
    return text.replace(/(\d)\s*[Nn][Oo]\.?\s*(\d)/g, "$1の$2");
}

// ==================================================================
// 1.5 「じゅう(10)」誤認識補正 (Rule 0-5)
// 月・日の文脈内のみ適用（年には絶対適用しない）
// 後続に1桁数字あり → 連結して2桁、後続なし → 10
// ==================================================================
function normalizeJuuMisrecognition(text) {
    if (!text) return text;
    var result = text;

    // Step 1: 複合語の先行置換（重要 → 14）
    result = result.replace(/重要/g, "14");

    // Step 2: じゅう系パターン（十の位）
    var juuPat = "(?:中|重|渋|縦|銃|自由|じゆう|ジユウ|じゅう|ジュウ)";

    // Step 3: じゅう + 一の位 → 2桁数字
    var onesList = [
        ["(?:いち|一)", 1],
        ["(?:に|二)", 2],
        ["(?:さん|三)", 3],
        ["(?:よ(?:う)?|し|四)", 4],
        ["(?:ごう|号|ご|五)", 5],
        ["(?:ろく|六)", 6],
        ["(?:しち|なな|七)", 7],
        ["(?:はち|八)", 8],
        ["(?:きゅう|く|九)", 9]
    ];
    for (var i = 0; i < onesList.length; i++) {
        var pat = new RegExp(juuPat + onesList[i][0], "g");
        result = result.replace(pat, String(10 + onesList[i][1]));
    }

    // Step 4: じゅう単独 → 10（後続に数字なし）
    result = result.replace(new RegExp(juuPat, "g"), "10");

    // Step 5: 数字+号 補正 (ご→号 の STT誤認識)
    // 「じゅうご(15)」が先にじゅう→10に変換された後、ご→号 が残るケース
    // 例: 10号 → 15 / 20号 → 25
    result = result.replace(/10号/g, "15");
    result = result.replace(/20号/g, "25");

    return result;
}

// ==================================================================
// 1.6 「野」→「の」誤認識補正
// じゅう系または数字の直前に限定して変換（過剰変換防止）
// 例: 野重さん → の重さん（→ じゅう補正で の13）
// ==================================================================
function normalizeYaParticle(text) {
    if (!text) return text;
    return text.replace(
        /野(?=(?:中|重|渋|縦|銃|自由|じゆう|ジユウ|じゅう|ジュウ|\d))/g,
        "の"
    );
}

// ==================================================================
// 1.7 並び順補正 (Rule 0-7)
// 年が存在する場合のみ 月日年 → 年月日 に並び替え
// 例: 3月12日昭和54年 → 昭和54年3月12日
//     12月1日1985年   → 1985年12月1日
// ==================================================================
function normalizeDateOrder(text) {
    if (!text) return text;
    var result = text;
    // 西暦: 月日 + 西暦年 → 西暦年 + 月日
    result = result.replace(
        /(\d{1,2})月(\d{1,2})日\s*(\d{4})\s*年/g,
        "$3年$1月$2日"
    );
    // 和暦: 月日 + 元号年 → 元号年 + 月日
    result = result.replace(
        /(\d{1,2})月(\d{1,2})日\s*(明治|大正|昭和|平成|令和)(元|\d{1,2})\s*年/g,
        "$3$4年$1月$2日"
    );
    return result;
}

// ==================================================================
// 2. コードベース解析 (rawText フォールバック用)
// 戻り値: { status: "OK"|"INVALID"|"UNCERTAIN", dbValue: "...", eraDetected: bool }
// ==================================================================
function parseDateByCode(rawText) {
    if (!rawText || rawText.trim() === "") {
        return { status: "UNCERTAIN", dbValue: "", eraDetected: false };
    }

    var text = normalizeNumbers(rawText);
    text = normalizeEra(text);
    text = normalizeNoParticle(text);         // Rule 0-6: No/NO/no → の（数字間のみ）
    text = normalizeJuuMisrecognition(text);  // Rule 0-5: じゅう系誤認識 → 数字
    text = normalizeYaParticle(text);         // 野 → の（じゅう系/数字の直前のみ）
    text = normalizeDateOrder(text);          // Rule 0-7: 月日年 → 年月日

    // ★ DTMF: 8桁 YYYYMMDD
    var dtmfMatch = text.match(/^(\d{4})(\d{2})(\d{2})$/);
    if (dtmfMatch) {
        var y = parseInt(dtmfMatch[1], 10);
        var mo = parseInt(dtmfMatch[2], 10);
        var da = parseInt(dtmfMatch[3], 10);

        if (!isValidDate(y, mo, da)) {
            return { status: "INVALID", dbValue: "INVALID", eraDetected: false };
        }
        var mm = mo < 10 ? "0" + mo : String(mo);
        var dd = da < 10 ? "0" + da : String(da);
        var dbVal = y + "-" + mm + "-" + dd + " 00:00";

        if (isFutureDate(dbVal) || isAgeOver120(dbVal)) {
            return { status: "INVALID", dbValue: "INVALID", eraDetected: false };
        }
        return { status: "OK", dbValue: dbVal, eraDetected: false };
    }

    // --- 元号検出 ---
    var eraMatch = text.match(/(明治|大正|昭和|平成|令和)/);
    var eraDetected = !!eraMatch;

    if (eraDetected) {
        // SEP: STT現実的な区切りのみ対応
        //   の → "昭和58の3月の12日" / "昭和の58の3月12日" (自然な話し方)
        //   スペース → "昭和58 3月 12日"
        //   、→ "昭和58年、3月、12日"
        //   年/月/日 → 単位語あり (省略も可)
        //   無区切り → "昭和583月の12日" (元号年は最大2桁なので月の「月」でアンカー)
        var warekiPattern = new RegExp(
            "(明治|大正|昭和|平成|令和)" +
            "(?:の|\\s)*(元|\\d{1,2})" +   // 元号年 (元 or 1〜99)、前に「の」も許容
            "(?:年|の|、|-|\\s)*" +         // 年→月の区切り (省略可、「月」は除外)
            "(\\d{1,2})月" +               // 月 (「月」でアンカー)
            "(?:の|、|-|\\s)*" +           // 月→日の区切り (省略可)
            "(\\d{1,2})" +                 // 日
            "(?:日)?"                      // 「日」省略可
        );
        var wm = text.match(warekiPattern);

        if (!wm || !wm[2] || !wm[3] || !wm[4]) {
            $runner.getLogger().info("[WarekiParser] Incomplete date parts. rawText=" + rawText);
            return { status: "UNCERTAIN", dbValue: "", eraDetected: true };
        }

        var era = wm[1];
        var eraY = (wm[2] === "元") ? 1 : parseInt(wm[2], 10);
        var wmo = parseInt(wm[3], 10);
        var wda = parseInt(wm[4], 10);

        if (!isValidEraYear(era, eraY)) {
            $runner.getLogger().info("[WarekiParser] 元号年が範囲外: " + era + eraY + "年");
            return { status: "INVALID", dbValue: "INVALID", eraDetected: true };
        }

        var seirekiY = 0;
        if (era === "令和")      seirekiY = 2018 + eraY;
        else if (era === "平成") seirekiY = 1988 + eraY;
        else if (era === "昭和") seirekiY = 1925 + eraY;
        else if (era === "大正") seirekiY = 1911 + eraY;
        else if (era === "明治") seirekiY = 1867 + eraY;

        if (!isValidDate(seirekiY, wmo, wda)) {
            return { status: "INVALID", dbValue: "INVALID", eraDetected: true };
        }
        var wmm = wmo < 10 ? "0" + wmo : String(wmo);
        var wdd = wda < 10 ? "0" + wda : String(wda);
        var wDbVal = seirekiY + "-" + wmm + "-" + wdd + " 00:00";

        if (isFutureDate(wDbVal) || isAgeOver120(wDbVal)) {
            return { status: "INVALID", dbValue: "INVALID", eraDetected: true };
        }
        return { status: "OK", dbValue: wDbVal, eraDetected: true };
    }

    // --- 元号なし: 西暦パターン ---
    var seirSEP = "(?:年|月|の|、|-|\\s)+";
    var seirekiPattern = new RegExp(
        "(\\d{1,4})" +
        seirSEP +
        "(\\d{1,2})" +
        seirSEP +
        "(\\d{1,2})" +
        "(?:日)?"
    );
    var s = text.match(seirekiPattern);

    if (!s || !s[1] || !s[2] || !s[3]) {
        $runner.getLogger().info("[SeirekiParser] Incomplete date parts. rawText=" + rawText);
        var hasAnyDateHint2 = /\d/.test(text) || /年|月|日/.test(text);
        return hasAnyDateHint2
            ? { status: "UNCERTAIN", dbValue: "", eraDetected: false }
            : { status: "INVALID", dbValue: "INVALID", eraDetected: false };
    }

    var yRaw = parseInt(s[1], 10);
    var smo = parseInt(s[2], 10);
    var sda = parseInt(s[3], 10);

    var sy = yRaw;
    if (yRaw < 100)       sy = 1900 + yRaw;
    else if (yRaw < 1000) sy = 1900 + (yRaw % 100);

    if (!isValidDate(sy, smo, sda)) {
        return { status: "INVALID", dbValue: "INVALID", eraDetected: false };
    }
    var smm = smo < 10 ? "0" + smo : String(smo);
    var sdd = sda < 10 ? "0" + sda : String(sda);
    var sDbVal = sy + "-" + smm + "-" + sdd + " 00:00";

    if (isFutureDate(sDbVal) || isAgeOver120(sDbVal)) {
        return { status: "INVALID", dbValue: "INVALID", eraDetected: false };
    }
    return { status: "OK", dbValue: sDbVal, eraDetected: false };
}

// ==================================================================
// 2.1 rawText が日付らしいか判定
//   メインロジックの優先順位判定に使用 (Priority A の条件)
// ==================================================================
function looksLikeDateUtterance(rawText) {
    if (!rawText || rawText.trim() === "") return false;
    var normalized = normalizeNumbers(normalizeEra(rawText));
    normalized = normalizeNoParticle(normalized);
    normalized = normalizeJuuMisrecognition(normalized);
    normalized = normalizeYaParticle(normalized);
    normalized = normalizeDateOrder(normalized);
    // 元号キーワードあり
    if (/明治|大正|昭和|平成|令和/.test(normalized)) return true;
    // 数字 + 年月日マーカー
    if (/\d+\s*[年月日]/.test(normalized)) return true;
    // 6〜8桁の数字列 (DTMF風)
    if (/\d{6,8}/.test(normalized)) return true;
    // ISO形式 yyyy-MM-dd または yyyy-MM-dd HH:mm
    if (/^\d{2,4}-\d{2}-\d{2}(\s\d{2}:\d{2})?$/.test(normalized.trim())) return true;
    return false;
}

// ==================================================================
// 2.2 rawText 解析フロー (ローカルのみ・LLMなし)
//   rawText が日付らしい場合に最優先で解析する。
//   - 解析成功 (OK)            → resolveAndSave して true を返す
//   - 解析失敗 (INVALID/UNCERTAIN) → INVALID を設定せず false を返す
//     （呼び出し元で nodeValue → cache へフォールバックさせる）
// ==================================================================
function handleRawTextFlow(rawText) {

    var codeResult = parseDateByCode(rawText);
    $runner.getLogger().info(
        "[CodeParser] status=" + codeResult.status +
        " | dbValue=" + codeResult.dbValue +
        " | eraDetected=" + codeResult.eraDetected +
        " | rawText=" + rawText
    );

    if (codeResult.status === "OK") {
        var finalDbValue = codeResult.dbValue;
        var finalReadingValue = formatReadingValue(finalDbValue, mode, codeResult.eraDetected);
        $runner.getLogger().info("[LOCAL] resolved | dbValue=" + finalDbValue + " | readingValue=" + finalReadingValue);
        resolveAndSave(finalDbValue, finalReadingValue);
        return true;
    }

    // INVALID / UNCERTAIN: rawText からは解析できない
    //   → ここでは INVALID を設定せず false を返し、呼び出し元で nodeValue にフォールバックする
    $runner.getLogger().info("[LOCAL] rawText parse failed (" + codeResult.status + ") → fallback to nodeValue");
    return false;
}

// ==================================================================
// 3. 読み上げ値フォーマッタ
// ==================================================================
function formatReadingValue(dbValue, mode, preferWareki) {
    if (dbValue === "INVALID") return "INVALID";
    if (mode === "和暦") return toWareki(dbValue);
    if (mode === "西暦") return toSeireki(dbValue);
    return preferWareki ? toWareki(dbValue) : toSeireki(dbValue);
}

// ==================================================================
// 5. 保存・再生処理 (共通)
// ==================================================================
function resolveAndSave(dbValue, readingValue) {
    $runner.setResult(readingValue);

    var finalPrompt = prompt.split("#data#").join(readingValue);
    if (finalPrompt) {
        $ivr.play(finalPrompt, true);
    }

    // ★ raw_dob_data キャッシュ保存
    //   sourceBaseDate: 保存時点の baseDate（= getModuleResult(moduleName) の正規化値）
    //   再入判定に使用: 次回起動時に baseDate が同じなら再入、変わっていれば新規入力とみなす
    try {
        $runner.setObject("raw_dob_data", JSON.stringify({
            dbValue: dbValue,
            readingValue: readingValue,
            sourceBaseDate: baseDate
        }));
        $runner.getLogger().info("[DOB Cache] Saved: readingValue=" + readingValue + " | sourceBaseDate=" + baseDate);
    } catch(e) {
        $runner.getLogger().warn("[DOB Cache] Failed to save raw_dob_data: " + e);
    }

    try {
        var seqNum = parseInt(String($runner.get("seq") || "1"), 10);
        var timeISO = new Date().toISOString();
        var logText = getTranscribe(finalPrompt);

        if (saveDOB2db) {
            // DB保存値は必ず yyyy-MM-dd HH:mm 形式であることを保証する
            if (!/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/.test(dbValue)) {
                $runner.getLogger().error(">>> DOB保存中止: dbValueの形式不正: " + dbValue);
            } else {
                var dobSuccess = $ivr.exec("save2db", "save", JSON.stringify({
                    contextField: {
                        contextName: "patientDateOfBirth",
                        displayType: "Date",
                        value: dbValue
                    }
                }));
                if (dobSuccess) {
                    $runner.getLogger().info(">>> DOB保存成功: " + dbValue);
                } else {
                    $runner.getLogger().error(">>> DOB保存失敗!");
                }
            }
        }

        if (!logText || logText.trim() === "") {
            $runner.getLogger().warn(">>> logTextが空のため、対話の保存をスキップします。");
        } else {
            var utteranceData = {
                seq: seqNum,
                messageType: 0,
                text: logText,
                utteranceType: "MESSAGE",
                startMsec: $ivr.exec("save2db", "parseTimestamp", timeISO),
                endMsec: $ivr.exec("save2db", "parseTimestamp", timeISO)
            };
            var success = $ivr.exec("save2db", "save", JSON.stringify({ utterance: utteranceData }));
            if (success) {
                $runner.set("seq", seqNum + 1);
                $runner.getLogger().info(">>> 対話の保存に成功しました。");
            }
        }
    } catch (e) {
        $runner.getLogger().error(">>> 保存エラー: " + e);
    }
}

// ==================================================================
// 6. メイン処理
// ==================================================================

var prompt = $runner.getProperty("prompt") || "";
var moduleName = $runner.getProperty("module");
var mode = $runner.getProperty("dateReadingMode");
var saveDOB2db = String($runner.getProperty("saveDOB2db") || "").toLowerCase() === "yes";

// 入力読み込み
var nodeValue = $runner.getModuleResult(moduleName);
var baseDate = normalizeInput(nodeValue);

var _rawObj = $runner.getObject("raw_text");
var rawText = (_rawObj && String(_rawObj).trim())
    ? String(_rawObj).trim()
    : String($runner.get("raw_text") || $runner.get("GLOBAL_RAW_TEXT") || "").trim();

$runner.setResult("RAW_INPUT:" + (rawText || "EMPTY"));

// ★ raw_dob_data キャッシュ読み込み
var _dobCacheStr = String($runner.getObject("raw_dob_data") || "").trim();
var _cachedDob = null;
if (_dobCacheStr) {
    try {
        var _parsed = JSON.parse(_dobCacheStr);
        if (_parsed && _parsed.dbValue && _parsed.readingValue) {
            _cachedDob = _parsed;
        }
    } catch(e) {
        $runner.getLogger().warn("[DOB Cache] Parse error: " + e);
    }
}

// ★ 再入判定
//   DOBキャプチャモジュール(moduleName)の結果が前回キャッシュ保存時と同じ
//   → そのモジュールは再実行されていない（= 別モジュール経由での再入の可能性）
//   ★ ただし rawText に新しい日付がある場合はそちらを優先する（下記①の通り）
var _isReentry = _cachedDob && (baseDate === _cachedDob.sourceBaseDate);

// ★ rawText が日付らしいかを先に判定（優先処理の判断材料）
var _rawLooksLikeDate = looksLikeDateUtterance(rawText);

$runner.getLogger().info(
    "[Main] nodeValue=" + nodeValue +
    " | baseDate=" + baseDate +
    " | rawText='" + rawText + "'" +
    " | rawLooksLikeDate=" + _rawLooksLikeDate +
    " | cached=" + (!!_cachedDob) +
    " | sourceBaseDate=" + (_cachedDob ? _cachedDob.sourceBaseDate : "N/A") +
    " | isReentry=" + _isReentry
);

// ==================================================================
// ★ 優先順位設計（フロー観点）
//
//   TTS (DOB を尋ねる)
//     ↓
//   STT/DTMF (キャプチャ)
//     ↓
//   DOB Re-confirmation ← このモジュール
//     ↓
//   STT (はい/いいえを確認)
//     ↓
//   分岐:
//     - 「はい」 → 次工程へ
//     - 「いいえ」 → STT(DOBキャプチャ)に戻る → DOB Re-confirmation に戻る
//     - 「はい/いいえ」parse不能 → DOB Re-confirmation に戻る（同じ DOB を復唱）
//
//   ★ フォールバックチェーン: rawText → nodeValue → cache → INVALID
//     上から順に試し、解決できた段階で確定する（解決できなければ次へフォールバック）。
//
//     【A】rawText が日付らしい → 最優先で解析
//          → 解析成功: cache と一致・不一致に関わらず rawText を使用（最も信頼できる情報源）
//          → 解析失敗: INVALID にせず【B】nodeValue へフォールバック
//     【B】nodeValue 有効 → 解析（主に DTMF 入力。STT/DTMF の最新入力を取得）
//          → 妥当: 西暦で読み上げ。ただし sourceBaseDate と一致（= 同一日付の復唱）の
//                  場合のみ、キャッシュの読み上げ（元号など）を保持（比較ロジックは維持）
//          → 妥当性NG: INVALID にせず【C】cache へフォールバック
//     【C】cache 有効 + 再入（同じ baseDate） → キャッシュ使用
//          → rawText も nodeValue も解決できず、確認段階で parse不能発話があり
//            再度復唱に戻ったケース
//     【D】すべて失敗 → INVALID
// ==================================================================

// ★ フォールバックチェーン: rawText → nodeValue → cache → INVALID
//   いずれかの段階で解決できたら _resolved = true として後続をスキップする
var _resolved = false;

// ==================================================================
// ① 【A】rawText が日付らしい → rawText を最優先で解析
//   ユーザーが新しい日付を発話した場合は rawText に必ず含まれているため、
//   キャッシュや stale な nodeValue より rawText を信頼する。
//   ★ rawText が解析できた場合は cache との一致・不一致に関わらず rawText を使用する。
//   ★ rawText が解析できなかった場合は INVALID にせず nodeValue へフォールバックする。
// ==================================================================
if (_rawLooksLikeDate) {
    $runner.getLogger().info("[Priority A] rawText looks like a date → handleRawTextFlow(rawText)");
    _resolved = handleRawTextFlow(rawText);
    if (!_resolved) {
        $runner.getLogger().info("[Priority A] rawText could not be parsed → fallback to nodeValue");
    }
}

// ==================================================================
// ② 【B】nodeValue 有効 → nodeValue を処理
//   到達条件: rawText が無い/日付でない、または rawText 解析失敗（フォールバック）。
//   ★ STT/DTMF の最新入力を取得するため、キャッシュ(sourceBaseDate)より
//      nodeValue を先に処理する。
//   ※ rawText に元号がない前提なので 2/3桁年は西暦として補完。
//   ※ sourceBaseDate と一致（= 同一日付の復唱）の場合のみ、キャッシュの
//      読み上げ（元号など）を保持する（比較ロジックは維持）。
//   ※ nodeValue が妥当性NGの場合は INVALID にせず cache へフォールバックする。
// ==================================================================
if (!_resolved && baseDate !== "INVALID") {

    var resolvedBase = baseDate;
    var shortYearMatch = baseDate.match(/^(\d{2,3})(-\d{2}-\d{2} \d{2}:\d{2})$/);
    if (shortYearMatch) {
        var yNum = parseInt(shortYearMatch[1], 10);
        yNum = (shortYearMatch[1].length === 2) ? 1900 + yNum : 1900 + (yNum % 100);
        resolvedBase = yNum + shortYearMatch[2];
        $runner.getLogger().info(
            "[Priority B] Short year " + shortYearMatch[1] + " → Gregorian → " + yNum
        );
    }

    // 妥当性チェック（4月31日・非閏年2月29日・未来日・120歳超）
    var _parts = resolvedBase.split(" ")[0].split("-");
    var _y = parseInt(_parts[0], 10);
    var _m = parseInt(_parts[1], 10);
    var _d = parseInt(_parts[2], 10);

    if (!isValidDate(_y, _m, _d) || isFutureDate(resolvedBase) || isAgeOver120(resolvedBase)) {
        // nodeValue 妥当性NG → INVALID にせず cache へフォールバック（後続③で処理）
        $runner.getLogger().warn(
            "[Priority B] nodeValue validation failed: " + resolvedBase +
            " (isValid=" + isValidDate(_y, _m, _d) +
            " isFuture=" + isFutureDate(resolvedBase) +
            " isOver120=" + isAgeOver120(resolvedBase) + ") → fallback to cache"
        );
    } else if (_isReentry) {
        // ★ 同一日付の復唱（baseDate === sourceBaseDate） → 元号読みを保持するためキャッシュ使用
        //   （比較ロジックは維持。日付自体は nodeValue と一致しているため値は変わらない）
        $runner.getLogger().info(
            "[Priority B] nodeValue valid & matches sourceBaseDate (re-entry). " +
            "Keeping cached reading: " + _cachedDob.readingValue
        );
        resolveAndSave(_cachedDob.dbValue, _cachedDob.readingValue);
        _resolved = true;
    } else {
        // 新規入力 → rawText に元号情報なし → 西暦で読み上げ
        var readingValue = formatReadingValue(resolvedBase, mode, false);
        $runner.getLogger().info(
            "[Priority B] nodeValue (DTMF/non-era STT) resolved: " + resolvedBase + " → " + readingValue
        );
        $runner.setResult("LOCAL_RESULT:" + readingValue);
        resolveAndSave(resolvedBase, readingValue);
        _resolved = true;
    }
}

// ==================================================================
// ③ 【C】cache フォールバック（rawText も nodeValue も解決できず + 再入）
//   確認段階で「わかりません」等の parse不能発話があり、再度復唱に戻ったケース。
//   前回保存した結果（昭和58年4月25日 など）を再生する。
// ==================================================================
if (!_resolved && _isReentry) {
    $runner.getLogger().info(
        "[Priority C] Fallback to cache (rawText/nodeValue unresolved, baseDate matches sourceBaseDate). " +
        "Using cached: " + _cachedDob.readingValue
    );
    resolveAndSave(_cachedDob.dbValue, _cachedDob.readingValue);
    _resolved = true;
}

// ==================================================================
// ④ 【D】すべて失敗 → INVALID
// ==================================================================
if (!_resolved) {
    $runner.getLogger().warn(
        "[Main] Unresolved (rawText/nodeValue/cache all failed). rawText='" + rawText +
        "' | baseDate=" + baseDate + " | cached=" + (!!_cachedDob) + " → INVALID"
    );
    $runner.setResult("INVALID");
}