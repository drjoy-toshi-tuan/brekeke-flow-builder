// ==================================================================
// Unit tests for "DOB Re-confirmation.js"
//
// 対象: Part A (元号なし1〜2桁年の安全処理) と
//       Part B (円→年 / 助詞 / MMDD連結 / 先頭ノイズ除去) の各補正。
//
// 実行方法:
//   node "tests/dob-reconfirmation.test.js"
//
// 仕組み:
//   本体スクリプトはロード時に「6. メイン処理」で $runner.getProperty(...) を
//   実行してしまうため、そのままでは Node で読み込めない。
//   そこでメイン処理より前の「関数定義部分だけ」を切り出し、$runner をスタブ
//   したサンドボックス上で eval して各パーサ関数をテストする。
// ==================================================================

var fs = require("fs");
var path = require("path");
var vm = require("vm");

var SRC_PATH = path.join(__dirname, "..", "DOB Re-confirmation.js");
var source = fs.readFileSync(SRC_PATH, "utf8");

// --- メイン処理（副作用あり）を切り離し、関数定義部分だけ取り出す ---
var mainMarker = "// 6. メイン処理";
var cutIdx = source.indexOf(mainMarker);
if (cutIdx === -1) {
    throw new Error("メイン処理マーカーが見つかりません。ファイル構成が変わった可能性があります。");
}
var functionsOnly = source.slice(0, cutIdx);

// --- $runner スタブ（ロガーのみ利用される） ---
var sandbox = {
    $runner: {
        getLogger: function () {
            return { info: function () {}, warn: function () {}, error: function () {} };
        }
    }
};
vm.createContext(sandbox);
vm.runInContext(functionsOnly, sandbox, { filename: "DOB Re-confirmation.functions.js" });

var parseDateByCode = sandbox.parseDateByCode;
var parsePartialDate = sandbox.parsePartialDate;
var normalizeYearChar = sandbox.normalizeYearChar;
var stripLeadingNoise = sandbox.stripLeadingNoise;
var normalizeConcatenatedMMDD = sandbox.normalizeConcatenatedMMDD;
var normalizeAll = sandbox.normalizeAll;

// ==================================================================
// 簡易テストランナー
// ==================================================================
var passed = 0;
var failed = 0;
var failures = [];

function eq(actual, expected, name) {
    var a = JSON.stringify(actual);
    var e = JSON.stringify(expected);
    if (a === e) {
        passed++;
    } else {
        failed++;
        failures.push(name + "\n    expected: " + e + "\n    actual:   " + a);
    }
}

// parseDateByCode の { status, dbValue } だけを検証するヘルパ
function code(input) {
    var r = parseDateByCode(input);
    return { status: r.status, dbValue: r.dbValue };
}

// ==================================================================
// PART A: 元号なしの1〜2桁年 → INVALID（自動補完しない）
// ==================================================================

// 2桁年（曖昧）→ INVALID
eq(code("57年3月12日"), { status: "INVALID", dbValue: "INVALID" }, "A: 57年3月12日 → INVALID (2桁年は曖昧)");
eq(code("79年3月12日"), { status: "INVALID", dbValue: "INVALID" }, "A: 79年3月12日 → INVALID (2桁年は曖昧)");
// 1桁年 → INVALID
eq(code("9年3月12日"), { status: "INVALID", dbValue: "INVALID" }, "A: 9年3月12日 → INVALID (1桁年は曖昧)");

// 3桁年 → 1900 + 下2桁 で救済（STTの先頭欠落パターン）
eq(code("079年3月12日"), { status: "OK", dbValue: "1979-03-12 00:00" }, "A: 079年3月12日 → 1979 救済 (3桁年)");

// 4桁西暦 → そのまま
eq(code("1979年3月12日"), { status: "OK", dbValue: "1979-03-12 00:00" }, "A: 1979年3月12日 → 1979 (4桁西暦)");

// 元号付きの2桁年は従来通り有効（安全ルールは元号なしのみ）
eq(code("昭和57年3月12日"), { status: "OK", dbValue: "1982-03-12 00:00" }, "A: 昭和57年3月12日 → 1982 (元号付きは有効)");

// 部分日付でも2桁年は無効（none）
eq(parsePartialDate("66年").has, false, "A: parsePartialDate('66年') → has=false (2桁年は特定不能)");
eq(parsePartialDate("079年").has, true, "A: parsePartialDate('079年') → has=true (3桁年は救済)");
eq(parsePartialDate("079年").year, 1979, "A: parsePartialDate('079年').year → 1979");

// ==================================================================
// PART B1: 円 → 年
// ==================================================================
eq(normalizeYearChar("1947円7月10日"), "1947年7月10日", "B1: normalizeYearChar 円→年");
eq(code("1947円7月10日"), { status: "OK", dbValue: "1947-07-10 00:00" }, "B1: 1947円7月10日 → 1947-07-10");
eq(code("昭和22円7月10日"), { status: "OK", dbValue: "1947-07-10 00:00" }, "B1: 昭和22円7月10日 → 1947-07-10 (元号年でも円→年)");

// ==================================================================
// PART B2: 助詞/言い淀み（の・です）を要素間に許容
// ==================================================================
eq(code("平成12年の5月12日です。"), { status: "OK", dbValue: "2000-05-12 00:00" }, "B2: 平成12年の5月12日です。→ 2000-05-12");
eq(code("昭和58の3月の12日"), { status: "OK", dbValue: "1983-03-12 00:00" }, "B2: 昭和58の3月の12日 → 1983-03-12");
eq(code("平成12年の5月の12日です"), { status: "OK", dbValue: "2000-05-12 00:00" }, "B2: 平成12年の5月の12日です → 2000-05-12");

// ==================================================================
// PART B3: 月日連結（MMDD, 区切りなし4桁）
// ==================================================================
eq(normalizeConcatenatedMMDD("1952年0203"), "1952年02月03日", "B3: normalizeConcatenatedMMDD 西暦");
eq(normalizeConcatenatedMMDD("昭和61年0203"), "昭和61年02月03日", "B3: normalizeConcatenatedMMDD 和暦");
eq(code("1952年0203"), { status: "OK", dbValue: "1952-02-03 00:00" }, "B3: 1952年0203 → 1952-02-03");
eq(code("昭和61年0203"), { status: "OK", dbValue: "1986-02-03 00:00" }, "B3: 昭和61年0203 → 1986-02-03");
// 通常の完全日付は MMDD 補正に巻き込まれない
eq(normalizeConcatenatedMMDD("1952年02月03日"), "1952年02月03日", "B3: 完全日付は不変（誤爆しない）");
// 不正な MMDD（13月）は妥当性チェックで INVALID
eq(code("1952年1305"), { status: "INVALID", dbValue: "INVALID" }, "B3: 1952年1305 → INVALID (13月)");

// ==================================================================
// PART B4: 先頭ノイズ除去（数字+読点 + 後続が日付らしい場合のみ）
// ==================================================================
eq(stripLeadingNoise("1909、66年10月17日"), "66年10月17日", "B4: stripLeadingNoise 数字+読点+2桁年");
eq(stripLeadingNoise("1909、1979年3月12日"), "1979年3月12日", "B4: stripLeadingNoise 数字+読点+4桁年");
eq(stripLeadingNoise("1909、昭和54年3月12日"), "昭和54年3月12日", "B4: stripLeadingNoise 数字+読点+元号");
// 先頭ノイズ除去後に2桁年 → Part A で INVALID
eq(code("1909、66年10月17日"), { status: "INVALID", dbValue: "INVALID" }, "B4: 1909、66年10月17日 → INVALID (残りが2桁年)");
// 先頭ノイズ除去後に4桁年 → 有効
eq(code("1909、1979年3月12日"), { status: "OK", dbValue: "1979-03-12 00:00" }, "B4: 1909、1979年3月12日 → 1979-03-12");
// 後続が日付らしくない場合は除去しない（過剰除去防止）
eq(stripLeadingNoise("1979年3月12日"), "1979年3月12日", "B4: 通常の日付は不変");
eq(stripLeadingNoise("1979、3月12日"), "1979、3月12日", "B4: 後続が '数字+年'/元号 でない場合は除去しない");

// ==================================================================
// 回帰: 既存の正常系がそのまま通ること
// ==================================================================
eq(code("昭和54年3月12日"), { status: "OK", dbValue: "1979-03-12 00:00" }, "REG: 昭和54年3月12日 → 1979-03-12");
eq(code("令和元年5月1日"), { status: "OK", dbValue: "2019-05-01 00:00" }, "REG: 令和元年5月1日 → 2019-05-01");
eq(code("１９７９年３月１２日"), { status: "OK", dbValue: "1979-03-12 00:00" }, "REG: 全角 → 1979-03-12");
eq(code("19790312"), { status: "OK", dbValue: "1979-03-12 00:00" }, "REG: DTMF 8桁 → 1979-03-12");
// 「日」欠落（末尾）は従来通り解析成功
eq(code("昭和21年1月17"), { status: "OK", dbValue: "1946-01-17 00:00" }, "REG: 昭和21年1月17（日欠落）→ 1946-01-17");
// 元号年範囲外
eq(code("昭和70年3月12日"), { status: "INVALID", dbValue: "INVALID" }, "REG: 昭和70年 → INVALID (範囲外)");

// ==================================================================
// 結果出力
// ==================================================================
console.log("\n==================================================");
console.log("  DOB Re-confirmation unit tests");
console.log("==================================================");
console.log("  PASSED: " + passed);
console.log("  FAILED: " + failed);
if (failed > 0) {
    console.log("\n  --- Failures ---");
    failures.forEach(function (f) { console.log("  ✗ " + f); });
    process.exitCode = 1;
} else {
    console.log("\n  ✓ All tests passed.");
}
console.log("==================================================\n");
