// Script Template: consultation_caller_type — 本人/家族/NO_RESULT 分類
// Nashorn(ES5.1): arrow/let/const/includes/テンプレート文字列 不使用。
// プレースホルダー:
//   {{INPUT_MODULE}} = STT聴取モジュール名（例: 入力_相談_本人家族聴取）

var input = "";
try { input = String($runner.getModuleResult("{{INPUT_MODULE}}") || ""); } catch (e) { input = ""; }

var result;
if (/本人|私|自分|わたし|僕|ぼく|わし/.test(input)) {
  result = "本人";
} else if (/家族|息子|娘|妻|夫|母|父|子供|こども|兄|弟|姉|妹|孫|かぞく/.test(input)) {
  result = "家族";
} else {
  result = "NO_RESULT";
}

$runner.getLogger().info("[CALLER-TYPE] in=" + input + " => " + result);
$runner.setResult(result);
