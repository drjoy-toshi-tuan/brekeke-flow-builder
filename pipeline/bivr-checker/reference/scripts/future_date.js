// Script Template: future_date
// 入力モジュールから取得した日付が今日より未来か判定
// プレースホルダー: {{INPUT_MODULE}} = 入力元モジュール名
// 出力: SUCCESS（未来日付）/ FAIL（今日以前 or 解釈不能）

// 1. 前のモジュールからデータを取得
var input = $runner.getModuleResult("{{INPUT_MODULE}}");
var res = "FAIL";

if (input) {
    var inputStr = input.toString().trim();
    var finalInputDate = "";

    // 2. 入力値を yyyy-MM-dd 形式に正規化
    if (inputStr.length === 8 && /^\d{8}$/.test(inputStr)) {
        // 8桁数字: yyyyMMdd → yyyy-MM-dd
        finalInputDate = inputStr.substring(0, 4) + "-" +
                         inputStr.substring(4, 6) + "-" +
                         inputStr.substring(6, 8);
    } else if (inputStr.length >= 10) {
        // yyyy-MM-dd HH:mm 形式 → 先頭10文字（yyyy-MM-dd）のみ
        finalInputDate = inputStr.substring(0, 10);
    }

    // 3. 現在日付を yyyy-MM-dd 形式で取得
    var now = new Date();
    var year = now.getFullYear();
    var month = ("0" + (now.getMonth() + 1)).slice(-2);
    var day = ("0" + now.getDate()).slice(-2);
    var todayDate = year + "-" + month + "-" + day;

    // 4. 比較: 今日より後の日付なら SUCCESS
    if (finalInputDate > todayDate) {
        res = "SUCCESS";
    } else {
        res = "FAIL";
    }
}

// 5. 結果をセット
$runner.setResult(res);
