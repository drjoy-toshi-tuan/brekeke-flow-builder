// Script Template: consultation_init — 受診相談 LLM問診ループ 初期化＋主訴シード
// loopCount=0 で初期化し、consultationHistory に「通話冒頭の主訴（用件フリー聴取）」をシードする。
// generate_by_OpenAI はステートレスのため、毎ターン consultationHistory を注入して文脈を保つ。
// 主訴を最初の患者発話としてシードしておくことで、問診は「本日いかが」を聞き直さず確認・深掘りから始まる。
// プレースホルダー: {{SEED_MODULE}} = 用件フリー聴取STT（例: 入力_用件フリー聴取）
// Nashorn(ES5.1)想定。

var seed = "";
try { seed = String($runner.getModuleResult("{{SEED_MODULE}}") || ""); } catch (e) { seed = ""; }

$runner.setObject("loopCount", "0");
$runner.setObject("consultationHistory", (seed !== "") ? ("患者: " + seed + "\n") : "");
$runner.getLogger().info("[CONSULT-INIT] loopCount=0 seeded='" + seed + "'");
$runner.setResult("OK");
