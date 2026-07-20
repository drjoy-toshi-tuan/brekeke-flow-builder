// Script Template: consultation_current_utterance — 受診相談 現発話ピッカー
// generate_by_OpenAI は入力(params.module)が空だと「No recognized text→Failed to create payload」で落ちる。
// そこで OpenAI 呼び出しの直前にこのスクリプトを置き、「今ターンの患者発話」を選んで setResult する:
//   - ループ応答({{INPUT_MODULE}}=入力_LLM問診応答) があればそれ
//   - 無ければ 用件フリー聴取({{SEED_MODULE}}=入力_用件フリー聴取) ＝通話冒頭の主訴
// これで初回は free-speech の主訴を入力に取り、AI が「本日いかが」を聞き直さず確認・深掘りから始められる。
// OpenAI の params.module はこのスクリプトモジュール(script_現発話)を指す。
// Nashorn(ES5.1)想定: arrow / let / const / includes / テンプレート文字列 不使用。

var ans = "";
try { ans = String($runner.getModuleResult("{{INPUT_MODULE}}") || ""); } catch (e) { ans = ""; }
var free = "";
try { free = String($runner.getModuleResult("{{SEED_MODULE}}") || ""); } catch (e2) { free = ""; }

var cur = (ans !== "") ? ans : free;
$runner.getLogger().info("[CONSULT-UTTER] source=" + ((ans !== "") ? "answer" : "freeSpeech") + " text='" + cur + "'");
$runner.setResult(cur);
