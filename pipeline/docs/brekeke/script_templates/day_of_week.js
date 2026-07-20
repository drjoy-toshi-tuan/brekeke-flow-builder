// Script Template: day_of_week
// 現在の曜日を判定
// プレースホルダー: なし（システム日時を直接参照）
// 出力: 平日 / 土曜 / 日曜祝日

var now = new Date();
var day = now.getDay();  // 0=日, 1=月, 2=火, 3=水, 4=木, 5=金, 6=土
var res = "平日";

if (day === 0) {
    res = "日曜祝日";
} else if (day === 6) {
    res = "土曜";
} else {
    res = "平日";
}

// 祝日リストとの照合（必要に応じて拡張）
// var holidays = ["2026-01-01", "2026-01-13", ...];
// var year = now.getFullYear();
// var month = ("0" + (now.getMonth() + 1)).slice(-2);
// var date = ("0" + now.getDate()).slice(-2);
// var todayStr = year + "-" + month + "-" + date;
// if (holidays.indexOf(todayStr) >= 0) {
//     res = "日曜祝日";
// }

$runner.setResult(res);
