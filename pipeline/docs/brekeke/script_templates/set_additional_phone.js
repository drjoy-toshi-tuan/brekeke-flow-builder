// Script Template: set_additional_phone — 発話された電話番号を連絡先(additionalPhoneNumber)へ確定
// 着信番号確認で患者が別番号を発話した場合に、その発話番号を additionalPhoneNumber に格納する。
// $runner.setObject で resolver に載せ、終端 drjoy_finalize が getSystemVariableValue で拾って正規化・save2db する。
// （着信番号採用ケースは saveContext2DB(contextValue=<% sys-customer-phone-number %>) 側で設定済み）
// プレースホルダー: {{INPUT_MODULE}} = 確認聴取の STT 入力モジュール名（例: 入力_連絡先_着信確認）
// Nashorn(ES5.1)想定。

var v = "";
try { v = String($runner.getModuleResult("{{INPUT_MODULE}}") || ""); } catch (e) { v = ""; }

if (v !== "") {
  $runner.setObject("additionalPhoneNumber", v);
}
$runner.getLogger().info("[SET-PHONE-SPOKEN] additionalPhoneNumber='" + v + "'");
$runner.setResult("OK");
