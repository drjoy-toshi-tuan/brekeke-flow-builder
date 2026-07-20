// Script Template: future_date
// 入力モジュールから取得した日付が今日より未来か判定
// プレースホルダー:
//   {{INPUT_MODULE}}  = 入力元モジュール名（通常は OpenAI_{step}）
//   {{CONTEXT_FIELD}} = OpenAI モジュールが書き込む context 名（通常は reservationDate）
// 出力: SUCCESS（未来日付）/ FAIL（今日以前 or 解釈不能）
//
// 注: Brekeke の $runner.getModuleResult(OpenAIモジュール名) は **マッチした next 条件の
// label**（"default" 等）を返し、OpenAI の生出力は返さない（2026-04-22 大分赤十字病院_診療
// で判明）。このためまず context field から値を読み、取れなかった場合のみ getModuleResult
// の結果を正規表現で抽出する多段フォールバック方式とする。

// 1. 値の取得（context → getModuleResult の順で試行）
var input = null;

// 1-a. context field から取得（Brekeke API の揺れに備えて複数パターン試行）
try {
    if (typeof $runner.getContextModel === "function") {
        var cm = $runner.getContextModel();
        if (cm) {
            if (typeof cm.get === "function") {
                input = cm.get("{{CONTEXT_FIELD}}");
            } else if (cm["{{CONTEXT_FIELD}}"] != null) {
                input = cm["{{CONTEXT_FIELD}}"];
            }
        }
    }
} catch (e) { /* 次のフォールバックへ */ }

try {
    if (!input && typeof $runner.getContext === "function") {
        input = $runner.getContext("{{CONTEXT_FIELD}}");
    }
} catch (e) { /* 次のフォールバックへ */ }

// 1-b. fallback: getModuleResult（script/CMR モジュールが入力先なら有効）
if (!input) {
    try {
        input = $runner.getModuleResult("{{INPUT_MODULE}}");
    } catch (e) { input = null; }
}

var res = "FAIL";

if (input) {
    var inputStr = String(input).trim();
    var finalInputDate = "";

    // 2. yyyy-MM-dd パターンを最初に探す（文字列のどこに含まれていても抽出）
    var isoMatch = inputStr.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (isoMatch) {
        finalInputDate = isoMatch[1] + "-" +
                         ("0" + isoMatch[2]).slice(-2) + "-" +
                         ("0" + isoMatch[3]).slice(-2);
    }

    // 3. 見つからなければ yyyyMMdd 8桁数字を探す
    if (!finalInputDate) {
        var compactMatch = inputStr.match(/(\d{4})(\d{2})(\d{2})/);
        if (compactMatch) {
            finalInputDate = compactMatch[1] + "-" + compactMatch[2] + "-" + compactMatch[3];
        }
    }

    // 4. 見つからなければ 日本語 "yyyy年M月d日" を探す（OpenAI が不正出力したケース救済）
    if (!finalInputDate) {
        var jpMatch = inputStr.match(/(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日/);
        if (jpMatch) {
            finalInputDate = jpMatch[1] + "-" +
                             ("0" + jpMatch[2]).slice(-2) + "-" +
                             ("0" + jpMatch[3]).slice(-2);
        }
    }

    // 5. いずれも見つからなければ FAIL（finalInputDate 空のまま）
    if (finalInputDate) {
        // 6. 現在日付を yyyy-MM-dd 形式で取得（ローカルタイムゾーン）
        var now = new Date();
        var year = now.getFullYear();
        var month = ("0" + (now.getMonth() + 1)).slice(-2);
        var day = ("0" + now.getDate()).slice(-2);
        var todayDate = year + "-" + month + "-" + day;
        var todayMonthDay = month + "-" + day;

        // 7. 年サニティチェック: OpenAI が古い年を出力するケース（LLM ハルシネーション）を救済。
        //    2026-04-22 大分赤十字病院_診療 で「4月25日」が 2024-04-25 と解釈されて常に
        //    FAIL になる事象が発生。プロンプトの年決定ルール（基準日の月日以降→同年、
        //    以前→翌年）を script 側でも再適用して補正する。
        var parsedYear = parseInt(finalInputDate.substring(0, 4), 10);
        var parsedMonthDay = finalInputDate.substring(5); // "MM-DD"
        if (parsedYear < year - 1 || parsedYear > year + 2) {
            // 当年 -1 〜 +2 の範囲を逸脱 → 明らかに異常値と判断して再計算
            var recomputedYear = (parsedMonthDay >= todayMonthDay) ? year : (year + 1);
            finalInputDate = recomputedYear + "-" + parsedMonthDay;
        }

        // 8. 比較: 今日より後の日付なら SUCCESS
        if (finalInputDate > todayDate) {
            res = "SUCCESS";
        }
    }
}

// 8. 結果をセット
$runner.setResult(res);
