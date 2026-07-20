// Script Template: consultation_finalize_contact — 受診相談ルート 個人情報を $runner へ確定
// 受診相談ルートは個人情報を別建て(相談_生年月日聴取／相談_氏名聴取／相談_連絡先聴取)で取るため、
// 共通 finalize(drjoy_finalize) が読む getSystemVariableValue($runner) 経路へ値を載せておく。
// hearing の save2db は $runner を立てないため、終端 finalize が拾えるよう本scriptで $runner.setObject する。
//   patientDateOfBirth ← 相談_生年月日聴取（共通の入力_生年月日聴取は受診相談では走らない）
//   callerName/callerPhone ← 相談_氏名/連絡先聴取（発信者起点＝本人/家族）
// 共通ルート(新規/変更/キャンセル)ではこのscriptは通らないので $runner は空のまま＝finalize は従来の fallback モジュールを使う。
// プレースホルダー: {{DOB_MODULE}} {{NAME_MODULE}} {{PHONE_MODULE}}（各 STT 入力モジュール名）
// Nashorn(ES5.1)想定。

function mr(name) {
  var v = "";
  try { v = String($runner.getModuleResult(name) || ""); } catch (e) { v = ""; }
  return v;
}

var dob = mr("{{DOB_MODULE}}");
var nm = mr("{{NAME_MODULE}}");
var ph = mr("{{PHONE_MODULE}}");

if (dob !== "") $runner.setObject("patientDateOfBirth", dob);
if (nm !== "") $runner.setObject("callerName", nm);
if (ph !== "") $runner.setObject("callerPhone", ph);

$runner.getLogger().info("[CONSULT-CONTACT] dob='" + dob + "' callerName='" + nm + "' callerPhone='" + ph + "'");
$runner.setResult("OK");
