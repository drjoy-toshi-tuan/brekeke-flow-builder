// @part-id: clinic_day_default
// @engine-version: v2-lazy
// ⚠️ SECURITY FOLLOW-UP (未対応・別件): 本体に GCP service account の private_key が
// ハードコードされている（配布元 Clinic Day Classifier と同一）。
// 環境変数/シークレット管理への切り出しは別 PR で対応予定。
//
// fork 追加分（clinic_day_default 用途 = 聴取なし配置で「N診療日後」を変数化）:
//   - noInputMode プロパティ（"yes" で入力パース全スキップ・available_date 算出のみ）
//   - noInputMode / <%today%> センチネル時に contextName 設定なら受付可能初日を DB 保存
// それ以外は配布元エンジン（lazy CSV load / PAST_DAY / STT補正 / stripFillers）を無改変で保持。
//
// ------------------------------------------------------------------
// 1. 設定・日付初期化
// ------------------------------------------------------------------
var moduleName       = $runner.getProperty("module")            || "stt";
var holidayCsvUrl    = $runner.getProperty("holidaySource")     || "";
var customHolidayUrl = $runner.getProperty("customHoliday")     || "";
// SERVICE_ACCOUNT_KEY: Google service account の JSON キー (ハードコード)
//   Drive の共有リンクが「リンクを知っている全員」で無くても
//   Drive API 経由 (Bearer トークン) で非公開ファイルをダウンロード可能。
//   ※ 対象ファイル (またはフォルダ) を client_email に閲覧者として共有しておくこと。
//   ⚠️ 秘密鍵をコードに埋め込むため、リポジトリの閲覧権限に注意 (漏洩時は GCP でローテート)。
var SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "vn-ts-501714",
    "private_key_id": "f6d7c90e3fe25045dc7b1303dbd88053424aeee0",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDA5Y4Z+Nl6vPhi\nzghxVxYS3Yxm94MIQOW9vRvUg0FJ4qYvIX+1sA2YtB9pJx8v2BSSUkbWOYABszsw\nFhn5XtQS3eUsntxZtfURun6vuuj6bIBBsP26zKgtiBOvseV7Sd3gIbwiE9gWiLYk\nIMTg9XQwP8492/H9dJlGtM4FxhYvjAfGwJCS+bWwC2Q3hakQD5ySVzysHMkKRhGj\nY5fdGcKNCJJgys5ZS6ssR/yEOsjQNbWvO8bmLlrorXKVyeLqPaUVS/FFp5Qu9VEx\nvuX0boVyYrEfd3rKXxkgITbMKOeSMG/uVaVMm3CVnPFr9Ko8hBQiw4XhE/GutTaU\nFF/FkInxAgMBAAECggEACvHbbrjSaibntv92tiuZSoe8jCkWC7VW872ToyqxXSZZ\nhIoTi3UKSHRL5fT8zYOmoyi88THBBBetz4wpfB83zDw/4RjAauyqk49v2buytWbL\nni6TLvKmxjKW31yqJyUpTCrN2Gck1x55qzIayaLTrVspchQVNmrTuZHPsL8tChSA\nDpISFTWqXut2wYqKU6T1Lx1UbIYCiv031IdxqVfwUQvrDn8Ukyj32cQRiVzebiGa\n7FHeYY/FfWmqlOtdeMpRwpuehr1RSSpFi99TXXvpUA0bdLioMWJEG2RX8D8ZHu1H\nw49IFSCXnPNDQveVQsOOiNgEoBg7b2BNuB4xQfKNswKBgQD3CwMaIxhLNg2q6YLN\nN01jODMFd6V7kUtGmI6X5fqyw4H8pA5tGZ8ZCFEN3P31WalyJZAtQOLKfR9ffqZY\nfCIPS5IZfF4gw0pyCWCl/DVCvzHoo6jzLdtZ4rteh+vMa8ejLOWBfjcmOgLuT415\nvlgT6hRVJuam/2qUu39ASUQYewKBgQDH4/if0/bJaGmgUEwM0TNZHnyBtI5/se5P\nagaW7CsHmH3wEVY+U+lcOAEIGKG7ihjx279yt/ngRIJWPiSmVgbBi0Hn3w18MxKs\n5BUwY6vvkn6ldA3N3WdiL1tbjDatnbCpLH0kS14ljqigiyahrzyJm7+lewV/Tyrj\nW39OxbwZgwKBgGJkWmnwjF54Ot1Vf6koW4Qm//svehNK/QYzAKfzCvRj9cOfu7cs\nOzeHHnE9EVDE0z4JQ/EiJLGtP++Sy8H2PsKEwL2x0POPlHjyzzGMz9GzwLb9Z+7i\n1rhoG2Q9EmcqjiqpWQdIM8Lf3Ab6XEiezQmxc0Ou6LKei96NBtOd2qc9AoGBAIaZ\n8ZqWnjEj2TS1vXBIEx6o08h3sBk21LWvPL62S4dy3SMiWYPg91w87hzokUf7By8d\n/X4feujU2Tt/3ygO97+uqXOdFLSUo7e+YrJR+754VEXPr1f4BhzsrMUp1sv0Sriw\nl5gwFDaQKObqrNnlaYt0UIn7HEmNIuE0hLajmjVHAoGAXixMZpkOUResw1AmtK/M\nWXO+o0tQk5JSwkkks+ocd2bshnrp6lBi2Ur0rVcuzZ4ifI3r5nyksfeWKlqendgR\nH9tj7LGA0xQtMR3Z1UMv4ORtax2M5aMMXSUzMRB3ebkgVTGLXm/wba+1oauqDLZO\nXLPo00seay4nD1K/0a3knBQ=\n-----END PRIVATE KEY-----\n",
    "client_email": "brekeke-module-dev@vn-ts-501714.iam.gserviceaccount.com",
    "client_id": "111078634441579004069",
    "token_uri": "https://oauth2.googleapis.com/token"
};
// closedDayMode: 休診日判定 + blockDays診療日カウントの共通区分
//   なし / 土日祝日 / 祝日 / 土日 / 日祝日 / 土 / 日
var closedDayMode    = $runner.getProperty("closedDayMode")     || "土日祝日";
// blockDays: 受付開始までの診療日数 (0またはなしの場合はスキップ)
var blockDays        = parseInt($runner.getProperty("blockDays") || "0", 10);
blockDays            = isNaN(blockDays) ? 0 : blockDays;
// output_type: business時の出力形式 (日時 / フリーテキスト)
var outputType       = String($runner.getProperty("output_type") || "日時").trim();
// noInputMode: "yes" で聴取なしモード (clinic_day_default fork 追加)。
//   入力パースを全てスキップし、休診日 + blockDays から available_date のみ算出・保存する。
var noInputMode      = String($runner.getProperty("noInputMode") || "").trim().toLowerCase() === "yes";
// DB保存用プロパティ (両方設定された場合のみDB保存)
var contextName        = $runner.getProperty("contextName");
var contextDisplayType = $runner.getProperty("contextDisplayType");

var _today       = new Date();
var CURRENT_YEAR = _today.getFullYear();
var _m1          = _today.getMonth() + 1;
var _d1          = _today.getDate();
var TODAY_ISO    = CURRENT_YEAR + "-" + (_m1 < 10 ? "0" + _m1 : String(_m1)) + "-" + (_d1 < 10 ? "0" + _d1 : String(_d1));

// 曜日名 → 曜日番号 (月=1, 火=2, ..., 日=0)
var DOW_MAP = {"月":1,"火":2,"水":3,"木":4,"金":5,"土":6,"日":0,
               "月曜":1,"火曜":2,"水曜":3,"木曜":4,"金曜":5,"土曜":6,"日曜":0,
               "月曜日":1,"火曜日":2,"水曜日":3,"木曜日":4,"金曜日":5,"土曜日":6,"日曜日":0};

function addDays(isoDate, n) {
    var d = new Date(isoDate + "T00:00:00");
    d.setDate(d.getDate() + n);
    var y = d.getFullYear();
    var m = d.getMonth() + 1 < 10 ? "0" + (d.getMonth() + 1) : String(d.getMonth() + 1);
    var dd = d.getDate() < 10 ? "0" + d.getDate() : String(d.getDate());
    return y + "-" + m + "-" + dd;
}

// 翌週の指定曜日を返す (weekOffset: 0=今週, 1=来週, 2=再来週)
function getNthWeekDay(todayIso, dowTarget, weekOffset) {
    var base  = new Date(todayIso + "T00:00:00");
    var today = base.getDay();
    var daysToThisMon = (today === 0) ? -6 : (1 - today);
    var thisMon = new Date(base.getTime());
    thisMon.setDate(thisMon.getDate() + daysToThisMon);
    thisMon.setDate(thisMon.getDate() + weekOffset * 7);
    var dowOffset = (dowTarget === 0) ? 6 : (dowTarget - 1);
    thisMon.setDate(thisMon.getDate() + dowOffset);
    var y  = thisMon.getFullYear();
    var m  = thisMon.getMonth() + 1 < 10 ? "0" + (thisMon.getMonth() + 1) : String(thisMon.getMonth() + 1);
    var d  = thisMon.getDate() < 10 ? "0" + thisMon.getDate() : String(thisMon.getDate());
    return y + "-" + m + "-" + d;
}

// 基準日より後の直近の指定曜日
function getNextDayOfWeek(todayIso, dowTarget) {
    var base = new Date(todayIso + "T00:00:00");
    var diff = (dowTarget - base.getDay() + 7) % 7 || 7;
    var target = new Date(base.getTime());
    target.setDate(target.getDate() + diff);
    var y  = target.getFullYear();
    var m  = target.getMonth() + 1 < 10 ? "0" + (target.getMonth() + 1) : String(target.getMonth() + 1);
    var d  = target.getDate() < 10 ? "0" + target.getDate() : String(target.getDate());
    return y + "-" + m + "-" + d;
}

// 月オフセット付きの日付を返す (monthOffset: 1=来月, 2=再来月)
function getMonthOffsetDate(todayIso, monthOffset, day) {
    var base  = new Date(todayIso + "T00:00:00");
    var year  = base.getFullYear();
    var month = base.getMonth() + 1 + monthOffset;
    if (month > 12) {
        year  += Math.floor((month - 1) / 12);
        month  = ((month - 1) % 12) + 1;
    }
    // 実在する暦日のみ返す (存在しない日 → null)。toIso で閏年・月末を検証
    return toIso(year, month, day);
}

// STT モジュールの出力を直接取得
var rawInput = String($runner.getModuleResult(moduleName) || "");
var rawInputTrimmed = rawInput.trim();
$runner.getLogger().info("[checkClosedDay] module=" + moduleName + " rawInput: " + rawInput);

// ------------------------------------------------------------------
// 2. 休診日 Set 構築
//    ① holidaySource CSV  (内閣府祝日 — Shift_JIS)
//    ② customHoliday CSV  (病院独自休診日 — UTF-8)
//    ※ どちらも空の場合はスキップして続行 (土日判定のみ)
//    ※ 両方に同じ日付があっても重複エラーにならない (customSet 優先でマージ)
// ------------------------------------------------------------------
var holidaySet      = {}; // { "2026-01-01": "元日", ... }
var customSet       = {}; // { "2026-12-29": "年末休診", ... }
var mergedClosedSet = {}; // holidaySet + customSet をマージしたもの

// --- Google Drive URL から fileId を抽出 (共有リンク各種形式に対応) ---
//   https://drive.google.com/file/d/<ID>/view
//   https://drive.google.com/open?id=<ID>
//   https://drive.google.com/uc?export=download&id=<ID>
function extractDriveFileId(url) {
    var m = url.match(/\/d\/([a-zA-Z0-9_-]+)/);
    if (m) return m[1];
    m = url.match(/[?&]id=([a-zA-Z0-9_-]+)/);
    if (m) return m[1];
    return null;
}

// --- service account の JSON キーから OAuth2 access_token を取得 ---
//   JWT (RS256) を自前で署名し jwt-bearer grant で交換する。
//   実行内で使い回せるよう _saAccessToken にキャッシュ。
var _saAccessToken = null;
function getServiceAccountToken(saKey) {
    if (_saAccessToken) return _saAccessToken;
    try {
        var sa = (typeof saKey === "string") ? JSON.parse(saKey) : saKey;
        var clientEmail   = sa.client_email;
        var privateKeyPem = sa.private_key;
        if (!clientEmail || !privateKeyPem) {
            $runner.getLogger().warn("[serviceAccount] キーJSONに client_email / private_key がありません");
            return null;
        }

        var Base64           = Java.type("java.util.Base64");
        var StandardCharsets = Java.type("java.nio.charset.StandardCharsets");
        function strBytes(s) { return new java.lang.String(s).getBytes(StandardCharsets.UTF_8); }
        function b64url(bytes) { return String(Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)); }

        // --- JWT header / claims ---
        var now    = Math.floor(new Date().getTime() / 1000);
        var header = '{"alg":"RS256","typ":"JWT"}';
        var claims = JSON.stringify({
            iss:   clientEmail,
            scope: "https://www.googleapis.com/auth/drive.readonly",
            aud:   "https://oauth2.googleapis.com/token",
            iat:   now,
            exp:   now + 3600
        });
        var signingInput = b64url(strBytes(header)) + "." + b64url(strBytes(claims));

        // --- RS256 署名 (PKCS#8 秘密鍵) ---
        var KeyFactory          = Java.type("java.security.KeyFactory");
        var PKCS8EncodedKeySpec = Java.type("java.security.spec.PKCS8EncodedKeySpec");
        var Signature           = Java.type("java.security.Signature");
        var pem = String(privateKeyPem)
            .replace(/-----BEGIN PRIVATE KEY-----/, "")
            .replace(/-----END PRIVATE KEY-----/, "")
            .replace(/\\n/g, "")   // JSON二重エスケープの \n 対策
            .replace(/\s/g, "");
        var privKey = KeyFactory.getInstance("RSA")
            .generatePrivate(new PKCS8EncodedKeySpec(Base64.getDecoder().decode(pem)));
        var sig = Signature.getInstance("SHA256withRSA");
        sig.initSign(privKey);
        sig.update(strBytes(signingInput));
        var jwt = signingInput + "." + b64url(sig.sign());

        // --- access_token 交換 ---
        var URI          = Java.type("java.net.URI");
        var HttpClient   = Java.type("java.net.http.HttpClient");
        var HttpRequest  = Java.type("java.net.http.HttpRequest");
        var HttpResponse = Java.type("java.net.http.HttpResponse");
        var Duration     = Java.type("java.time.Duration");

        var client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(10)).build();
        var form = "grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Ajwt-bearer&assertion=" + jwt;
        var req = HttpRequest.newBuilder()
            .uri(URI.create("https://oauth2.googleapis.com/token"))
            .timeout(Duration.ofSeconds(10))
            .header("Content-Type", "application/x-www-form-urlencoded")
            .POST(HttpRequest.BodyPublishers.ofString(form))
            .build();
        var resp = client.send(req, HttpResponse.BodyHandlers.ofString());
        if (resp.statusCode() !== 200) {
            $runner.getLogger().warn("[serviceAccount] token endpoint status=" + resp.statusCode() + " body=" + String(resp.body()));
            return null;
        }
        _saAccessToken = JSON.parse(String(resp.body())).access_token;
        $runner.getLogger().info("[serviceAccount] access_token 取得成功");
        return _saAccessToken;

    } catch (e) {
        $runner.getLogger().error("[serviceAccount] token取得エラー: " + e);
        return null;
    }
}

// --- 汎用CSV取得関数 ---
//   Drive の URL かつ serviceAccountKey が設定されていれば
//   Drive API (files.get?alt=media + Bearer) で非公開ファイルを取得。
//   それ以外は従来どおり素の GET (公開URL用)。
function fetchCsvLines(url, label, encoding) {
    if (!url) {
        $runner.getLogger().info("[" + label + "] URL未設定 — スキップ");
        return null;
    }
    try {
        var URI          = Java.type("java.net.URI");
        var HttpClient   = Java.type("java.net.http.HttpClient");
        var HttpRequest  = Java.type("java.net.http.HttpRequest");
        var HttpResponse = Java.type("java.net.http.HttpResponse");
        var Duration     = Java.type("java.time.Duration");
        var Charset      = Java.type("java.nio.charset.Charset");

        var client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .followRedirects(Java.type("java.net.http.HttpClient.Redirect").ALWAYS)
            .build();

        // Drive 非公開ファイル → service account 経由で取得
        var reqUrl  = url;
        var builder = HttpRequest.newBuilder().timeout(Duration.ofSeconds(10)).GET();
        var fileId  = extractDriveFileId(url);
        if (fileId && SERVICE_ACCOUNT_KEY && SERVICE_ACCOUNT_KEY.private_key) {
            var token = getServiceAccountToken(SERVICE_ACCOUNT_KEY);
            if (token) {
                reqUrl  = "https://www.googleapis.com/drive/v3/files/" + fileId + "?alt=media";
                builder = builder.header("Authorization", "Bearer " + token);
                $runner.getLogger().info("[" + label + "] Drive API 経由で取得 (fileId=" + fileId + ")");
            } else {
                $runner.getLogger().warn("[" + label + "] SAトークン取得失敗 — 素のGETにフォールバック");
            }
        }

        var req  = builder.uri(URI.create(reqUrl)).build();
        var resp = client.send(req, HttpResponse.BodyHandlers.ofByteArray());

        if (resp.statusCode() !== 200) {
            $runner.getLogger().warn("[" + label + "] HTTP status=" + resp.statusCode());
            return null;
        }

        var charset = (encoding && encoding.length > 0) ? encoding : "UTF-8";
        var text = String(new java.lang.String(resp.body(), Charset.forName(charset)));
        var lines = text.split("\n");
        $runner.getLogger().info("[" + label + "] Fetched " + lines.length + " lines (encoding=" + charset + ")");
        return lines;

    } catch (err) {
        $runner.getLogger().error("[" + label + "] fetchエラー: " + err);
        return null;
    }
}

// 休診日データ(CSV)を遅延ロード (lazy fetch)。
//   具体日があるブランチ (分類が必要なとき) でのみ呼ぶ。
//   不明 / NO_RESULT / 曖昧 / PAST_DAY では呼ばれず、ネットワーク往復を省く。
var _closedDataLoaded = false;
function loadClosedData() {
    if (_closedDataLoaded) return;
    _closedDataLoaded = true;

// ① holidaySource CSV をパース (内閣府形式: yyyy/M/d,祝日名 — Shift_JIS)
var holidayLines = fetchCsvLines(holidayCsvUrl, "holidaySource", "Shift_JIS");
if (holidayLines) {
    for (var li = 0; li < holidayLines.length; li++) {
        var line = holidayLines[li];
        if (line.charAt(line.length - 1) === "\r") line = line.substring(0, line.length - 1);
        if (!line) continue;
        if (line.indexOf("国民の祝日") >= 0 || line.indexOf("月日") >= 0) continue;

        var commaIdx = line.indexOf(",");
        if (commaIdx < 0) continue;
        var dateParts = line.substring(0, commaIdx).split("/");
        if (dateParts.length !== 3) continue;

        var hYear = parseInt(dateParts[0], 10);
        if (isNaN(hYear) || hYear < CURRENT_YEAR) continue;

        var yy = dateParts[0];
        var mm = dateParts[1].length === 1 ? "0" + dateParts[1] : dateParts[1];
        var dd = dateParts[2].length === 1 ? "0" + dateParts[2] : dateParts[2];
        holidaySet[yy + "-" + mm + "-" + dd] = line.substring(commaIdx + 1);
    }
    $runner.getLogger().info("[holidaySource] Loaded " + Object.keys(holidaySet).length + " holidays from " + CURRENT_YEAR + "+");
}

// ② customHoliday CSV をパース (形式: yyyy-MM-dd,休診名 または yyyy-MM-dd のみ — UTF-8)
var customLines = fetchCsvLines(customHolidayUrl, "customHoliday", "UTF-8");
if (customLines) {
    for (var ci = 0; ci < customLines.length; ci++) {
        var cLine = customLines[ci];
        if (cLine.charAt(cLine.length - 1) === "\r") cLine = cLine.substring(0, cLine.length - 1);
        if (!cLine || cLine.trim() === "") continue;

        var cComma = cLine.indexOf(",");
        var cDateStr = (cComma >= 0 ? cLine.substring(0, cComma) : cLine).replace(/[\s　]/g, "");
        var cName    = (cComma >= 0 ? cLine.substring(cComma + 1) : "病院休診日").trim() || "病院休診日";

        var cDateMatch = cDateStr.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
        if (cDateMatch) {
            var cY  = cDateMatch[1];
            var cM  = cDateMatch[2].length === 1 ? "0" + cDateMatch[2] : cDateMatch[2];
            var cD  = cDateMatch[3].length === 1 ? "0" + cDateMatch[3] : cDateMatch[3];
            customSet[cY + "-" + cM + "-" + cD] = cName;
        }
    }
    $runner.getLogger().info("[customHoliday] Loaded " + Object.keys(customSet).length + " days — " + JSON.stringify(Object.keys(customSet)));
}

// ③ マージ (holidaySet → customSet の順、重複は customSet 優先)
for (var hKey in holidaySet) mergedClosedSet[hKey] = holidaySet[hKey];
for (var cKey in customSet)  mergedClosedSet[cKey] = customSet[cKey];
$runner.getLogger().info("[mergedClosedSet] Total " + Object.keys(mergedClosedSet).length + " closed days");
} // end loadClosedData

// ------------------------------------------------------------------
// 3. 日付判定・パース
// ------------------------------------------------------------------

// --- 曜日判定 ---
function isSaturday(isoDate) { return new Date(isoDate + "T00:00:00").getDay() === 6; }
function isSunday(isoDate)   { return new Date(isoDate + "T00:00:00").getDay() === 0; }

// --- 祝日・休診日判定 ---
function isHoliday(isoDate)       { return holidaySet.hasOwnProperty(isoDate); }
function isCustomHoliday(isoDate) { return customSet.hasOwnProperty(isoDate); }

// closedDayMode に基づく休診日判定 (customHoliday は常に休診)
function isClosedDay(isoDate) {
    if (isCustomHoliday(isoDate)) return true;
    switch (closedDayMode) {
        case "なし":     return false;
        case "土日祝日": return isSaturday(isoDate) || isSunday(isoDate) || isHoliday(isoDate);
        case "祝日":     return isHoliday(isoDate);
        case "土日":     return isSaturday(isoDate) || isSunday(isoDate);
        case "日祝日":   return isSunday(isoDate)   || isHoliday(isoDate);
        case "土":       return isSaturday(isoDate);
        case "日":       return isSunday(isoDate);
        default:         return isSaturday(isoDate) || isSunday(isoDate) || isHoliday(isoDate);
    }
}

function closedReason(isoDate) {
    if (isCustomHoliday(isoDate)) return customSet[isoDate];
    if (isHoliday(isoDate))       return "祝日(" + holidaySet[isoDate] + ")";
    if (isSunday(isoDate))        return "日曜日";
    if (isSaturday(isoDate))      return "土曜日";
    return "営業日";
}

// 1日の分類: CLOSED(reason) / BLOCKED / BUSINESS
//   ※ 過去日という区分は廃止。年なし入力は resolveMMdd で必ず未来日に補完される。
//     年付きの過去日は isBlockedByLeadTime により BLOCKED 扱い。
function classifyDate(isoDate) {
    if (isClosedDay(isoDate))         return { type: "CLOSED", reason: closedReason(isoDate) };
    if (isBlockedByLeadTime(isoDate)) return { type: "BLOCKED" };
    return { type: "BUSINESS" };
}

// Dateオブジェクト → 休診日判定 (blockDays診療日カウント用)
function isClosedDayObj(d) {
    var iso = d.getFullYear() + "-"
        + (d.getMonth() + 1 < 10 ? "0" + (d.getMonth() + 1) : String(d.getMonth() + 1)) + "-"
        + (d.getDate() < 10 ? "0" + d.getDate() : String(d.getDate()));
    return isClosedDay(iso);
}

// --- blockDays判定 (closedDayMode の診療日を基準にリードタイムをカウント) ---
function isBlockedByLeadTime(isoDate) {
    var target = new Date(isoDate + "T00:00:00");
    var today  = new Date(TODAY_ISO + "T00:00:00");

    // 過去日付は常にブロック
    if (target < today) return true;
    // blockDays=0 or 未設定 → 今日以降はブロックなし
    if (!blockDays || blockDays <= 0) return false;

    // 今日から診療日をカウント (今日が診療日なら1日目)
    var cursor  = new Date(TODAY_ISO + "T00:00:00");
    var bizDays = 0;
    if (!isClosedDayObj(cursor)) bizDays++;

    var safety = 0;
    while (bizDays < blockDays && safety < 365) {
        cursor.setDate(cursor.getDate() + 1);
        safety++;
        if (!isClosedDayObj(cursor)) bizDays++;
    }

    // cursor = blockDays番目の診療日 → 次の診療日から受付可能
    var okDate  = new Date(cursor.getTime());
    var safety2 = 0;
    do {
        okDate.setDate(okDate.getDate() + 1);
        safety2++;
    } while (isClosedDayObj(okDate) && safety2 < 365);

    return target < okDate;
}

// --- available_date計算 (休診日 + リードタイム両方を考慮した最初の受付可能日) ---
function getFirstAvailableDate() {
    var cursor = new Date(TODAY_ISO + "T00:00:00");
    var safety = 0;
    while (safety < 365) {
        var y   = cursor.getFullYear();
        var m   = cursor.getMonth() + 1;
        var d   = cursor.getDate();
        var iso = y + "-" + (m < 10 ? "0" + m : String(m)) + "-" + (d < 10 ? "0" + d : String(d));
        if (!isClosedDay(iso) && !isBlockedByLeadTime(iso)) {
            return { full: y + "年" + m + "月" + d + "日", short: m + "月" + d + "日" };
        }
        cursor.setDate(cursor.getDate() + 1);
        safety++;
    }
    return null;
}

// --- 日付パース ---
function isLeapYear(y) {
    return (y % 4 === 0 && y % 100 !== 0) || (y % 400 === 0);
}

// 実在する暦日のみ ISO を返す (閏年対応)。存在しない日 (2/30, 4/31 等) は null
function toIso(y, mo, d) {
    if (mo < 1 || mo > 12 || d < 1) return null;
    var dim = [31, isLeapYear(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    if (d > dim[mo - 1]) return null;
    var mm = mo < 10 ? "0" + mo : String(mo);
    var dd = d  < 10 ? "0" + d  : String(d);
    return y + "-" + mm + "-" + dd;
}


// --- STT文字起こし補正エンジン (期間制限なし) ---
//   STTが日本語の数字を聞き間違えると、月/日が実際より過去の値になることがある
//   (例: 「しちがつ(7月)」→「いちがつ(1月)」)。読み方が似た月/日に1回だけ置換し、
//   今年で今日以降になる実在日の候補を集め、今日に最も近い (= 最小の ISO) を返す。
//   候補が無ければ null。
//   ※ 日付比較は resolveMMdd と同じく ISO文字列で行う (Dateオブジェクト比較の
//     エンジン差異・パース失敗を避けるため)。
function runCorrection(mo, day) {
    var mTable = { 1: [7], 2: [4], 4: [2, 7], 7: [1, 4] };
    var dTable = {
        1:  [7],  4:  [7],  7:  [1, 4],
        11: [17], 14: [17], 17: [11, 14],
        21: [27], 24: [27], 27: [21, 24]
    };
    var candidates = []; // 今日以降の実在日 (ISO文字列)
    function tryCand(tm, td) {
        var iso = toIso(CURRENT_YEAR, tm, td); // 実在する暦日のみ (閏年対応)
        if (iso && iso >= TODAY_ISO) candidates.push(iso);
    }
    if (mTable[mo]) {
        for (var i = 0; i < mTable[mo].length; i++) tryCand(mTable[mo][i], day);
    }
    if (dTable[day]) {
        for (var j = 0; j < dTable[day].length; j++) tryCand(mo, dTable[day][j]);
    }
    if (candidates.length === 0) return null;
    // すべて今日以降・同一年なので、今日に最も近い候補 = ISO文字列が最小のもの
    var best = candidates[0];
    for (var k = 1; k < candidates.length; k++) {
        if (candidates[k] < best) best = candidates[k];
    }
    return best;
}

// 年なし日付 (MMdd / M月d日) の年補完
//   今年で仮組みした日付を今日と比較し、
//     今日以降 (>= 今日) → 今年のまま
//     今日より過去 (< 今日) → (STT入力のみ) 文字起こし補正を1回試行 → だめなら翌年
//   allowCorrection: true のとき (STT の M月d日) だけ補正エンジンを使う。
//     DTMF (数字キー) は聞き間違いが無いため補正しない。
function resolveMMdd(mo, day, allowCorrection) {
    var c0 = toIso(CURRENT_YEAR,     mo, day);
    var c1 = toIso(CURRENT_YEAR + 1, mo, day);
    if (!c0 && !c1) return null;

    if (c0 && c0 >= TODAY_ISO) return c0; // 仮組み日が今日以降 → 今年

    // 仮組み日が過去。STT なら聞き間違い (月/日) を1回補正して今日以降を探す
    if (allowCorrection && c0) {
        var corrected = runCorrection(mo, day);
        if (corrected) {
            $runner.getLogger().info("[checkClosedDay] STT補正: " + CURRENT_YEAR + "-" + mo + "-" + day + " → " + corrected);
            return corrected;
        }
    }

    if (c1) return c1;                     // 補正不可 → 翌年
    return c0;
}

// 年 (yyyy) が明示された入力から得た日付の集合。
//   これらが過去日なら PAST_DAY 扱い (年なし入力の過去日は対象外)。
var _explicitYearDates = {};

// 具体的な日付を抽出 (yyyy-MM-dd の配列。重複除去済み)
function extractConcreteDates(text) {
    var results = [];
    var m;
    _explicitYearDates = {};

    // DTMF: 8桁数字 yyyyMMdd (年月日が明示)
    var dtmf8 = text.trim().match(/^(\d{4})(\d{2})(\d{2})$/);
    if (dtmf8) {
        var iso8 = toIso(parseInt(dtmf8[1]), parseInt(dtmf8[2]), parseInt(dtmf8[3]));
        if (!iso8) {
            $runner.getLogger().warn("[checkClosedDay] DTMF 8digits invalid date: " + text);
            return []; // 実在しない日 (2/30, 6/31, 閏年NG 等) → NO_RESULT
        }
        _explicitYearDates[iso8] = true; // 年付き → 過去日なら PAST_DAY
        return [iso8];
    }

    // DTMF: 4桁数字 MMdd (年なし → resolveMMdd で補完)
    var dtmf4 = text.trim().match(/^(\d{2})(\d{2})$/);
    if (dtmf4) {
        var iso4 = resolveMMdd(parseInt(dtmf4[1], 10), parseInt(dtmf4[2], 10));
        if (!iso4) {
            $runner.getLogger().warn("[checkClosedDay] DTMF 4digits invalid date: " + text);
            return []; // 実在しない日 → NO_RESULT
        }
        return [iso4];
    }

    // パターン0: yyyy-MM-dd hh:mm (年付き)
    var p0 = /(\d{4})-(\d{2})-(\d{2}) \d{2}:\d{2}/g;
    while ((m = p0.exec(text)) !== null) { var iso0 = m[1] + "-" + m[2] + "-" + m[3]; _explicitYearDates[iso0] = true; results.push(iso0); }
    if (results.length > 0) return dedupe(results);

    // パターン3: yyyy/M/d (年付き)
    var p3 = /(\d{4})\/(\d{1,2})\/(\d{1,2})/g;
    while ((m = p3.exec(text)) !== null) { var iso3 = toIso(parseInt(m[1]), parseInt(m[2]), parseInt(m[3])); if (iso3) _explicitYearDates[iso3] = true; results.push(iso3); }
    if (dedupe(results).length > 0) return dedupe(results);

    // パターン1: yyyy年M月d日 (年付き。月と日の間の「の」/空白を許容: 2026年1月の15日 等)
    var p1 = /(\d{4})年(\d{1,2})月\s*の?\s*(\d{1,2})日/g;
    while ((m = p1.exec(text)) !== null) { var iso1 = toIso(parseInt(m[1]), parseInt(m[2]), parseInt(m[3])); if (iso1) _explicitYearDates[iso1] = true; results.push(iso1); }

    // パターン(範囲): M月D1日からD2日[まで] — 同月・昇順を D1..D2 に展開 (年なし → resolveMMdd)
    //   マッチ部分は後続の M月d日 パターンから除去し、開始日を二重に補正しないようにする
    var rangeStripped = text;
    var rangeRe = /(\d{1,2})月(\d{1,2})日から(?:\d{1,2}月)?(\d{1,2})日/g;
    var rgM;
    while ((rgM = rangeRe.exec(text)) !== null) {
        rangeStripped = rangeStripped.replace(rgM[0], "");
        var rMonth = parseInt(rgM[1], 10);
        var rStart = parseInt(rgM[2], 10);
        var rEnd   = parseInt(rgM[3], 10);
        if (rEnd < rStart) continue;
        var rStartIso = resolveMMdd(rMonth, rStart, false);
        if (!rStartIso) continue;
        var rYear = parseInt(rStartIso.substring(0, 4), 10);
        for (var rd = rStart; rd <= rEnd; rd++) {
            var rIso = toIso(rYear, rMonth, rd);
            if (rIso) results.push(rIso);
        }
    }

    // パターン2: M月d日 (年なし) — resolveMMdd で年補完
    //   今年で仮組み → 今日以降ならそのまま今年、過去なら STT補正を1回試行 → だめなら翌年
    //   STT入力のため allowCorrection=true。月と日の間の「の」/空白を許容。範囲は除去済み。
    var textNoYear = rangeStripped.replace(/\d{4}年\d{1,2}月\s*の?\s*\d{1,2}日/g, "");
    var p2 = /(\d{1,2})月\s*の?\s*(\d{1,2})日/g;
    while ((m = p2.exec(textNoYear)) !== null) {
        var p2iso = resolveMMdd(parseInt(m[1], 10), parseInt(m[2], 10), true);
        if (p2iso) results.push(p2iso);
    }

    // パターン4: 今月・来月・再来月 + 日付 (複数対応)
    // 「再来月」を先に判定できる単一正規表現で double-match バグを回避
    var mpRe = /(再来月|来月|今月)(?:の)?(\d{1,2})日((?:[とや、・]\d{1,2}日)*)/g;
    var mpMatch;
    while ((mpMatch = mpRe.exec(text)) !== null) {
        var offset   = (mpMatch[1] === "再来月") ? 2 : (mpMatch[1] === "来月" ? 1 : 0);
        var firstDay = parseInt(mpMatch[2], 10);
        if (firstDay >= 1 && firstDay <= 31) results.push(getMonthOffsetDate(TODAY_ISO, offset, firstDay));
        if (mpMatch[3]) {
            var extraDays = mpMatch[3].match(/\d{1,2}/g) || [];
            for (var ei = 0; ei < extraDays.length; ei++) {
                var ed = parseInt(extraDays[ei], 10);
                if (ed >= 1 && ed <= 31) results.push(getMonthOffsetDate(TODAY_ISO, offset, ed));
            }
        }
    }

    // 相対日: 今日/本日=0, 明日/あした=+1, 明後日/あさって=+2 (長い語を先に判定)
    var relDays = [
        { re: /明後日|あさって/, off: 2 },
        { re: /明日|あした|あす|みょうにち/, off: 1 },
        { re: /今日|本日|きょう|ほんじつ/, off: 0 }
    ];
    for (var rli = 0; rli < relDays.length; rli++) {
        if (relDays[rli].re.test(text)) results.push(addDays(TODAY_ISO, relDays[rli].off));
    }

    // N日後: 今日 + N日 (暦日)。N は 1..90 のみ (数字ノイズ対策)。具体日として扱う。
    //   ※ 今週末 / 月末 は「具体日なし (曖昧)」扱い → detectVague 側で判定 (ここでは解析しない)
    var afterRe = /(\d{1,3})日後/g;
    var afM;
    while ((afM = afterRe.exec(text)) !== null) {
        var afN = parseInt(afM[1], 10);
        if (afN >= 1 && afN <= 90) results.push(addDays(TODAY_ISO, afN));
    }

    // パターン5: 曜日指定 (来週/再来週/今週/指定なし)。multi (2曜日) を single より先に判定。
    var dowPatterns = [
        { re: /来週(?:の)?([月火水木金土日]曜(?:日)?)[とや、・]([月火水木金土日]曜(?:日)?)/g, week: 1, multi: true },
        { re: /再来週(?:の)?([月火水木金土日]曜(?:日)?)[とや、・]([月火水木金土日]曜(?:日)?)/g, week: 2, multi: true },
        { re: /今週(?:の)?([月火水木金土日]曜(?:日)?)[とや、・]([月火水木金土日]曜(?:日)?)/g, week: 0, multi: true },
        { re: /来週(?:の)?([月火水木金土日]曜(?:日)?)/g, week: 1, multi: false },
        { re: /再来週(?:の)?([月火水木金土日]曜(?:日)?)/g, week: 2, multi: false },
        { re: /今週(?:の)?([月火水木金土日]曜(?:日)?)/g, week: 0, multi: false }
    ];
    var textForDow = text;
    var dowFound   = false;
    for (var pi = 0; pi < dowPatterns.length; pi++) {
        var pat = dowPatterns[pi];
        var dm;
        pat.re.lastIndex = 0;
        while ((dm = pat.re.exec(textForDow)) !== null) {
            dowFound = true;
            if (pat.multi) {
                var dow1 = DOW_MAP[dm[1].replace(/日$/,"")];
                var dow2 = DOW_MAP[dm[2].replace(/日$/,"")];
                if (dow1 !== undefined) results.push(getNthWeekDay(TODAY_ISO, dow1, pat.week));
                if (dow2 !== undefined) results.push(getNthWeekDay(TODAY_ISO, dow2, pat.week));
            } else {
                var dow1s = DOW_MAP[dm[1].replace(/日$/,"")];
                if (dow1s !== undefined) results.push(getNthWeekDay(TODAY_ISO, dow1s, pat.week));
            }
            textForDow = textForDow.replace(dm[0], "");
            pat.re.lastIndex = 0;
        }
    }

    // 週指定なし: X曜とY曜 (複数)
    if (!dowFound) {
        var pDowMulti = /([月火水木金土日]曜(?:日)?)[とや、・]([月火水木金土日]曜(?:日)?)/g;
        var dmm;
        while ((dmm = pDowMulti.exec(textForDow)) !== null) {
            dowFound = true;
            var d1 = DOW_MAP[dmm[1].replace(/日$/,"")];
            var d2 = DOW_MAP[dmm[2].replace(/日$/,"")];
            if (d1 !== undefined) results.push(getNextDayOfWeek(TODAY_ISO, d1));
            if (d2 !== undefined) results.push(getNextDayOfWeek(TODAY_ISO, d2));
        }
    }

    // 週指定なし: 単体曜日 (月曜日 / 月曜 など。「日」は任意 — 他の曜日パターンと統一)
    if (!dowFound) {
        var pDowSingle = /([月火水木金土日]曜(?:日)?)/g;
        var ds;
        while ((ds = pDowSingle.exec(textForDow)) !== null) {
            var dsKey = ds[1].replace(/日$/,"");
            if (DOW_MAP[dsKey] !== undefined) {
                results.push(getNextDayOfWeek(TODAY_ISO, DOW_MAP[dsKey]));
                dowFound = true;
            }
        }
    }

    return dedupe(results);
}

// 重複除去 + null除去 + 上限 (範囲展開で最大 ~31 日になり得るため 40 に設定)
var MAX_DATES = 40;
function dedupe(arr) {
    var seen = {};
    var unique = [];
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] && !seen[arr[i]]) {
            seen[arr[i]] = true;
            unique.push(arr[i]);
        }
    }
    if (unique.length > MAX_DATES) {
        $runner.getLogger().warn("[checkClosedDay] Truncated to " + MAX_DATES + " dates from " + unique.length);
        unique = unique.slice(0, MAX_DATES);
    }
    return unique;
}

// 曖昧な指定 (具体的な日なし) の判定
//   "vague": 月コンテキスト (X月 / 今月 / 来月 / 再来月, 旬あり/なし)、
//            または 期間表現 (月末 / 週末: 今月末・来月末・再来月末・今週末 等)
//   "none" : 上記いずれも無し
function detectVague(text) {
    var mNum       = text.match(/(\d{1,2})月/);
    var hasMonthNum = mNum && parseInt(mNum[1], 10) >= 1 && parseInt(mNum[1], 10) <= 12;
    var hasRelMonth = /(今月|来月|再来月)/.test(text);
    var hasJun      = /[上中下]旬/.test(text);
    // 月末 / 週末 系は「具体日なし」の曖昧扱い (今週末・月末・来月末・再来月末 等)
    var hasPeriod   = /月末|週末/.test(text);

    if (hasJun) {
        // 旬 は月コンテキストが必須。月がなければ NO_RESULT
        return (hasMonthNum || hasRelMonth) ? "vague" : "none";
    }
    return (hasMonthNum || hasRelMonth || hasPeriod) ? "vague" : "none";
}

// ------------------------------------------------------------------
// 4. DBコンテキスト保存 (Module Result Binder と同方式)
// ------------------------------------------------------------------
function saveContext2DB(value) {
    if (!contextName || !contextDisplayType || !value) return;
    if (!$ivr.connected()) return;
    var saveRequestData = JSON.stringify({
        contextField: { contextName: contextName, displayType: contextDisplayType, value: value }
    });
    try {
        var saveSuccess = $ivr.exec("save2db", "save", saveRequestData);
        if (saveSuccess) $runner.setObject(contextName, value);
    } catch (e) {
        $runner.getLogger().error("[checkClosedDay] DB保存失敗: " + e);
    }
}

// ------------------------------------------------------------------
// 5. メイン判定フロー
// ------------------------------------------------------------------
//   ※ available_date は「具体日あり・非過去」ブランチでのみ計算 (CSVが必要なため)。
//     不明 / NO_RESULT / 曖昧 / PAST_DAY では計算せず、ネットワーク往復を省く。

// フリーテキスト出力の整形: STTのフィラー語・記号・方言/敬語/タメ口の接尾辞を除去
//   ※ フリーテキスト出力にのみ適用 (日時/不明/NO_RESULT/NON_BUSINESS_DAY には影響しない)
// 先頭・末尾のフィラー語
var _FILLERS = ["えーと","えーっと","えー","あのー","あの","うーんと","うーん","まー","まあ",
    "そうですね","えっと","そのー","あー","んー","んーと","ねえ","ちょっと"];
// 末尾の 方言/敬語/タメ口 接尾辞 (重複は集合で吸収)
var _SUFFIXES = ["だべさ","だべ","っしょ","べし","だす","んだ","じゃん","だよね","じゃね","やん","やねん",
    "やで","やんか","やわ","ねん","やろ","じゃけん","じゃけ","けん","ばい","たい","さー","さあ",
    "でございます","ございます","いただけますか","いただきたい","させていただきたい","でしょうか",
    "いたします","ですよね","ですわ","だわ","だよ","だね","だぜ","だろ","っす","すか","かよ",
    "だっけ","っけ","けど","けんど","だに","ずら","だら","です","でお願いします","お願いします",
    "なんですけど","にお願い","ですけど","なんですが","をお願い"];
// 長い接尾辞を先に試すため長さ降順にソート (「なんですけど」を「けど」より先にマッチさせる)
_SUFFIXES.sort(function(a, b) { return b.length - a.length; });
var _FILLER_HEAD_RE = new RegExp("^(?:" + _FILLERS.join("|") + ")+");
var _FILLER_TAIL_RE = new RegExp("(?:" + _FILLERS.join("|") + ")+$");
var _SUFFIX_RE      = new RegExp("(?:" + _SUFFIXES.join("|") + ")$");

// フリーテキスト出力の整形: STTのフィラー語・記号・方言/敬語/タメ口の接尾辞を除去
//   ※ フリーテキスト出力にのみ適用 (日時/不明/NO_RESULT/NON_BUSINESS_DAY には影響しない)
function stripFillers(input) {
    var s = String(input);
    // 全角数字 → 半角
    s = s.replace(/[０-９]/g, function(c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    // 記号・空白除去
    s = s.replace(/[、。,.:;!?！？「」『』（）()\s\r\n\t]/g, "");
    // フィラー語 (先頭・末尾)
    s = s.replace(_FILLER_HEAD_RE, "");
    s = s.replace(_FILLER_TAIL_RE, "");
    // 末尾の接尾辞を長い順で、変化が無くなるまで最大5回除去 (「〜なんですけど」等の重なり対策)
    for (var i = 0; i < 5; i++) {
        var before = s;
        s = s.replace(_SUFFIX_RE, "");
        if (s === before) break;
    }
    return s;
}

// business時の出力値を生成 (日時 / フリーテキスト)
//   concreteFirstIso: 具体日がある場合の先頭ISO (曖昧時は null)
function buildBusinessOutput(concreteFirstIso) {
    if (outputType === "フリーテキスト") {
        // フィラー語等を除去。除去後に空になったら NO_RESULT
        return stripFillers(rawInputTrimmed) || "NO_RESULT";
    }
    // 日時: 具体日があれば yyyy-MM-dd 00:00、曖昧なら NO_RESULT
    if (concreteFirstIso) return concreteFirstIso + " 00:00";
    return "NO_RESULT";
}

// Step -1: 聴取なしモード (noInputMode=yes) / <%today%> センチネル入力。
//   通常のパース/曖昧判定を全てスキップし、休診日判定 (CSV取得 + available_date算出) だけを
//   今日基準で実行する。clinic_day_default（冒頭アナウンス直後等の聴取なし配置）は
//   noInputMode=yes で必ずこの経路に入る。
if (noInputMode || rawInputTrimmed === "<%today%>") {
    $runner.getLogger().info("[checkClosedDay] no-input evaluation (noInputMode=" + noInputMode + ") — closed-day evaluation only");
    loadClosedData();
    var _availSentinel = getFirstAvailableDate();
    if (_availSentinel) {
        $runner.setObject("available_date_full",  _availSentinel.full);
        $runner.setObject("available_date_short", _availSentinel.short);
        // fork 追加: contextName 設定時は受付可能初日を DB 保存
        // （後段 TTS の <%contextName%> 参照用。聴取なし配置では business 分岐に
        //   到達しないため、ここで保存しないと save_to が永久に未保存になる）
        saveContext2DB(_availSentinel.full);
    }
    $runner.setResult(_availSentinel ? "OK" : "NO_RESULT");

} else {

// Step1: 具体的な日付をローカルパース (曖昧な相槌より優先。日付が取れればそれを採用する)
var parsedDates = extractConcreteDates(rawInput);
$runner.getLogger().info("[checkClosedDay] localParse: " + JSON.stringify(parsedDates));

// Step0: 「不明・わからない」系、および「希望なし・特にない」系の入力 → 不明
//   ※ 具体的な日付が取れた場合はヘッジ表現 (「覚えていませんが」等) より日付を優先するため、
//     日付が取れなかった場合のみ判定する。
var UNKNOWN_DATE_RE = /わから[なね]い|わかりません|分から[なね]い|分かりません|わかんない|わかんな[いく]|不明|知らない|知りません|覚えていない|覚えてない|覚えておりません|覚えてません|忘れた|忘れました|忘れてしまいました|思い出せない|思い出せません|記憶にない|記憶がない|はっきりしない|はっきりとわからない|定かでない|定かではない|決まっていない|決まってない|未定|わからん|知らん/i;
// 「(受診)希望なし・希望がない・希望しません」等の否定・辞退表現 (どこにあってもマッチ)
var NO_PREFERENCE_RE = /希望[はがも]?(?:特に)?(?:ない|ないです|ありません|無い|無いです|なし|しません|いたしません|ございません)/;
// 単独の否定応答 (「ない」「ありません」「特にない」等)。末尾の句読点は無視して全体一致で判定
var _bareNeg = rawInputTrimmed.replace(/[。、．，.！!？?\s　]+$/g, "");
var BARE_NEGATION_RE = /^(?:特に|とくに|別に)?(?:ない|ないです|ありません|無い|無いです|なし|ございません)$/;

if (parsedDates.length === 0 &&
    (UNKNOWN_DATE_RE.test(rawInput) || NO_PREFERENCE_RE.test(rawInput) || BARE_NEGATION_RE.test(_bareNeg))) {
    $runner.getLogger().info("[checkClosedDay] Unknown / no-preference date input detected — returning 不明");
    $runner.setResult("不明");

} else {
    if (parsedDates.length > 0) {
        $runner.set("checked_dates", JSON.stringify(parsedDates));

        // --- PAST_DAY: 年付き (yyyy明示) の過去日を含む → フィルタを通さず即 PAST_DAY ---
        //   年なし入力 (M月d日 等) は resolveMMdd で未来日に補完されるため対象外。
        //   過去判定は ISO文字列比較のみ (CSV不要 → ネットワーク往復を省く)。
        var pastExplicit = [];
        for (var pk = 0; pk < parsedDates.length; pk++) {
            if (parsedDates[pk] < TODAY_ISO && _explicitYearDates[parsedDates[pk]]) {
                pastExplicit.push(parsedDates[pk]);
            }
        }

        if (pastExplicit.length > 0) {
            $runner.set("closed_dates", pastExplicit.join(", ") + "(過去日)");
            $runner.getLogger().info("[checkClosedDay] Result: PAST_DAY — " + pastExplicit.join(", "));
            $runner.setResult("PAST_DAY");

        } else {
            // --- 具体日あり (非過去): ここで初めて CSV をロード (lazy) ---
            loadClosedData();

            // available_date は CSV が必要なのでこのブランチでのみ計算
            var _avail = getFirstAvailableDate();
            if (_avail) {
                $runner.setObject("available_date_full",  _avail.full);
                $runner.setObject("available_date_short", _avail.short);
            }

            // 各日を分類。休診/受付不可はスキップし、最初の BUSINESS 日を採用。
            var closedDates      = [];
            var firstBusinessIso = null;
            for (var k = 0; k < parsedDates.length; k++) {
                var isoDate = parsedDates[k];
                if (!isoDate) continue;
                var c = classifyDate(isoDate);
                if (c.type === "BUSINESS") {
                    if (!firstBusinessIso) firstBusinessIso = isoDate;
                } else if (c.type === "CLOSED") {
                    closedDates.push(isoDate + "(" + c.reason + ")");
                } else if (c.type === "BLOCKED") {
                    closedDates.push(isoDate + "(受付不可期間)");
                }
            }
            $runner.set("closed_dates", closedDates.join(", "));

            if (!firstBusinessIso) {
                // 全件が休診/受付不可 → NON_BUSINESS_DAY
                $runner.getLogger().info("[checkClosedDay] Result: NON_BUSINESS_DAY — " + closedDates.join(", "));
                $runner.setResult("NON_BUSINESS_DAY");
            } else {
                // 最初の受付可能 (BUSINESS) 日を採用
                var out = buildBusinessOutput(firstBusinessIso);
                $runner.getLogger().info("[checkClosedDay] Result: BUSINESS (output_type=" + outputType + ") — " + out + " (firstBusiness=" + firstBusinessIso + ")");
                if (out !== "NO_RESULT") saveContext2DB(out);
                $runner.setResult(out);
            }
        }

    } else {
        // --- 具体日なし: 曖昧(月/旬)判定 ---
        var vague = detectVague(rawInput);
        if (vague === "vague") {
            // 月コンテキストあり → business 扱い (ただし月中のどの日でもよい想定)
            var vagueOut = buildBusinessOutput(null);
            $runner.getLogger().info("[checkClosedDay] Vague month input — BUSINESS (output_type=" + outputType + ") — " + vagueOut);
            if (vagueOut !== "NO_RESULT") saveContext2DB(vagueOut);
            $runner.setResult(vagueOut);
        } else {
            $runner.getLogger().warn("[checkClosedDay] No parseable date — NO_RESULT");
            $runner.setResult("NO_RESULT");
        }
    }
}
}
