// Script Template: shinjuku_kenshin_date_gate
// 新宿健診プラザ_健診 専用: 受診希望日_ゲート判定
// 判定順序: 1. 年度末超過 → 2. 休館日 → 3. 最短日
// 出力: "年度末エラー" / "休館日エラー" / "最短日エラー" / "OK"
//
// 副次的に setObject する表示用 context（TTS 内で <%name%> 参照用）:
//   desired_date_jp     例: "5月10日"     最短予約日（TODAY+MIN_DAYS_AHEAD）の和形式
//   desired_date_mmdd   例: "0510"        最短予約日の MMDD 4桁
//   fiscal_end_jp       例: "3月31日"     年度末日付の和形式
//   fiscal_end_full_jp  例: "2027年3月31日"
//
// 注: 値は受診希望日聴取_*の TTS 直前にも desired_date_precompute.js が同じ値を
//     setObject する（こちらは判定結果と一緒にもう一度更新するだけの位置付け）。
//
// プレースホルダー (scaffold 時に値置換):
//   - INPUT_MODULE  入力元 OpenAI モジュール名（template_params で指定）
//
// 参照元: docs/reference/customer_docs/【本番｜n8n実行｜健診1】：新宿健診プラザ.md §10-1 / §10-3
// FISCAL_END_DATE・MIN_DAYS_AHEAD は customer_doc §10-3 の定数。
// HOLIDAYS は customer_doc §10-2 の休館日リスト（2026 年度分）。
// 2027 年度の HOLIDAYS は施設から取得後、本テンプレに追加すること。
//
// 注意: 年度末超過 / 最短日判定は本来 OpenAI プロンプトで処理可能だが、
// 休館日判定は HOLIDAYS リスト必須のため Script に集約している（モジュール選定ガイド §3.8）。

var FISCAL_END_DATE = "2027-03-31";
var MIN_DAYS_AHEAD = 7;
var HOLIDAYS = [
    "2026-03-01","2026-03-08","2026-03-14","2026-03-15","2026-03-20","2026-03-21",
    "2026-03-22","2026-03-29","2026-04-04","2026-04-05","2026-04-11","2026-04-12",
    "2026-04-18","2026-04-19","2026-04-25","2026-04-26","2026-04-29","2026-04-30",
    "2026-05-01","2026-05-02","2026-05-03","2026-05-04","2026-05-05","2026-05-06",
    "2026-05-09","2026-05-10","2026-05-16","2026-05-17","2026-05-24","2026-05-31",
    "2026-06-07","2026-06-14","2026-06-21","2026-06-28","2026-07-05","2026-07-12",
    "2026-07-19","2026-07-20","2026-07-25","2026-07-26","2026-08-01","2026-08-02",
    "2026-08-09","2026-08-11","2026-08-16","2026-08-23","2026-08-30","2026-09-06",
    "2026-09-13","2026-09-20","2026-09-21","2026-09-22","2026-09-23","2026-09-27",
    "2026-10-04","2026-10-11","2026-10-12","2026-10-18","2026-10-25","2026-11-01",
    "2026-11-03","2026-11-08","2026-11-15","2026-11-22","2026-11-23","2026-11-28",
    "2026-11-29"
];

// 1. 値の取得（YYYY-MM-DD 形式の正規化済み日付を優先取得する）
//
// 重要: ゲートに到達するパスは複数ある:
//   (a) 初回: 受診希望日聴取_*_(新規/変更) → OpenAI_受診希望日聴取_*  → ゲート
//   (b) リトライ: エラー_受診希望日_(年度末/休館日/最短)_*  → OpenAI_エラー_xxx → ゲート
// (b) のときに (a) の結果（休館日候補）を引き続き読むと永久ループする。
// そのため main + エラー系すべての OpenAI モジュールの結果を順次試す。
var input = null;
var DATE_RE = /(\d{4})-(\d{1,2})-(\d{1,2})/;

// 1-a. INPUT_MODULE から suffix (新規 or 変更) を抽出して候補リスト生成
var INPUT_MODULE = "{{INPUT_MODULE}}";
var parts = INPUT_MODULE.split("_");
var suffix = parts[parts.length - 1];  // "新規" or "変更"
var openai_candidates = [
    "OpenAI_エラー_受診希望日_最短_" + suffix,
    "OpenAI_エラー_受診希望日_休館日_" + suffix,
    "OpenAI_エラー_受診希望日_年度末_" + suffix,
    INPUT_MODULE
];

// 1-b. 各候補 OpenAI モジュールの結果を試行。最初に YYYY-MM-DD 正規表現にマッチした値を採用
//      （リトライ系 OpenAI が走った場合はそちらを優先、走っていなければ getModuleResult が
//        null/empty を返すので次の候補へ進む想定）
for (var ci = 0; ci < openai_candidates.length; ci++) {
    try {
        var r = $runner.getModuleResult(openai_candidates[ci]);
        if (r && DATE_RE.test(String(r))) {
            input = r;
            break;
        }
    } catch (e) { /* 次の候補へ */ }
}

// 1-c. fallback: context field Preferred_date を直接読む（OpenAI 候補がすべて空の場合）
if (!input) {
    try {
        if (typeof $runner.getContextModel === "function") {
            var cm = $runner.getContextModel();
            if (cm) {
                if (typeof cm.get === "function") {
                    input = cm.get("Preferred_date");
                } else if (cm["Preferred_date"] != null) {
                    input = cm["Preferred_date"];
                }
            }
        }
    } catch (e) { /* 次のフォールバックへ */ }
}

// 1-d. 採用した値を Preferred_date に明示保存（後段の saveContextModel2DB が
//      確実に正規化済み日付を見るようにする。Brekeke の OpenAI contextName 自動保存は
//      実装依存なので二重に確実化する）
if (input && DATE_RE.test(String(input))) {
    try {
        $runner.setObject("Preferred_date", String(input));
    } catch (e) { /* setObject 不可なら諦める */ }
}

var res = "OK";

if (input) {
    // 2. yyyy-MM-dd 抽出（文字列のどこにあっても取れるように）
    var m = String(input).match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (m) {
        var confirmed = m[1] + "-" +
                        ("0" + m[2]).slice(-2) + "-" +
                        ("0" + m[3]).slice(-2);

        // 3. 年度末超過判定（customer_doc §10-3 STEP3-1）
        if (confirmed > FISCAL_END_DATE) {
            res = "年度末エラー";
        } else {
            // 4. 休館日判定（customer_doc §10-3 STEP3-2, YYYY-MM-DD 完全一致のみ）
            var isHoliday = false;
            for (var i = 0; i < HOLIDAYS.length; i++) {
                if (HOLIDAYS[i] === confirmed) {
                    isHoliday = true;
                    break;
                }
            }
            if (isHoliday) {
                res = "休館日エラー";
            } else {
                // 5. 最短日判定（customer_doc §10-3 STEP3-3, {DESIRED_DATE} = TODAY+MIN_DAYS_AHEAD）
                var now = new Date();
                var d = new Date(now.getTime() + MIN_DAYS_AHEAD * 86400000);
                var desired = d.getFullYear() + "-" +
                              ("0" + (d.getMonth() + 1)).slice(-2) + "-" +
                              ("0" + d.getDate()).slice(-2);
                if (confirmed < desired) {
                    res = "最短日エラー";
                }
            }
        }
    }
}

// 6. 表示用 context を保存（TTS の <%name%> 参照用）
//    cardnumber_raw の動作実例に倣い $runner.setObject を使用。
var nowForJp = new Date();
var dForJp = new Date(nowForJp.getTime() + MIN_DAYS_AHEAD * 86400000);
var desiredMonth = dForJp.getMonth() + 1;
var desiredDay = dForJp.getDate();
var desiredJp = desiredMonth + "月" + desiredDay + "日";
var desiredMmdd = ("0" + desiredMonth).slice(-2) + ("0" + desiredDay).slice(-2);

var feMatch = FISCAL_END_DATE.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
var fiscalJp = "";
var fiscalFullJp = "";
if (feMatch) {
    fiscalJp = parseInt(feMatch[2], 10) + "月" + parseInt(feMatch[3], 10) + "日";
    fiscalFullJp = feMatch[1] + "年" + parseInt(feMatch[2], 10) + "月" + parseInt(feMatch[3], 10) + "日";
}

$runner.setObject("desired_date_jp", desiredJp);
$runner.setObject("desired_date_mmdd", desiredMmdd);
$runner.setObject("fiscal_end_jp", fiscalJp);
$runner.setObject("fiscal_end_full_jp", fiscalFullJp);

// 7. 結果をセット
$runner.setResult(res);
