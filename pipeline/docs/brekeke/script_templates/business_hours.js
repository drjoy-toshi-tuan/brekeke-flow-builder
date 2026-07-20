// Script Template: business_hours
// 現在時刻が営業時間内か判定
// プレースホルダー: {{START_HOUR}}, {{END_HOUR}} = 営業開始/終了時刻（24時間制、0-23）
// 出力: 営業時間内 / 営業時間外

var now = new Date();
var hour = now.getHours();
var startHour = {{START_HOUR}};
var endHour = {{END_HOUR}};
var res = "営業時間外";

if (hour >= startHour && hour < endHour) {
    res = "営業時間内";
}

$runner.setResult(res);
