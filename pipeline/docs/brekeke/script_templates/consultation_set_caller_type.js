// Script Template: consultation_set_caller_type — callerType を setObject + save2db
// Nashorn(ES5.1): arrow/let/const 不使用。
// プレースホルダー:
//   {{CALLER_TYPE}} = "本人" または "家族"

$runner.setObject("callerType", "{{CALLER_TYPE}}");
$ivr.exec("save2db", "save", JSON.stringify({
  contextField: {
    contextName: "callerType",
    displayType: "TEXT",
    value: "{{CALLER_TYPE}}"
  }
}));
$runner.getLogger().info("[SET-CALLER-TYPE] callerType={{CALLER_TYPE}}");
$runner.setResult("OK");
