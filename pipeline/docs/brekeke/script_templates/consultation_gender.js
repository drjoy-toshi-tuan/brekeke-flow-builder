// Script Template: consultation_gender — 性別検出 + setObject(consultationGender) + save2db
// Nashorn(ES5.1): arrow/let/const 不使用。
// プレースホルダー:
//   {{INPUT_MODULE}} = STT聴取モジュール名（例: 入力_相談_性別聴取）

var input = "";
try { input = String($runner.getModuleResult("{{INPUT_MODULE}}") || ""); } catch (e) { input = ""; }

var result;
if (/女/.test(input)) {
  result = "女性";
} else if (/男/.test(input)) {
  result = "男性";
} else {
  result = "未回答";
}

$runner.setObject("consultationGender", result);
$ivr.exec("save2db", "save", JSON.stringify({
  contextField: {
    contextName: "consultationGender",
    displayType: "TEXT",
    value: result
  }
}));
$runner.getLogger().info("[CONSULT-GENDER] in=" + input + " => " + result);
$runner.setResult(result);
