// Script Template: consultation_loop_control — 受診相談 LLM問診ループ制御（決定論）
// 患者の発話を「完了 / 中断 / 上限 / 継続」に分類し、会話履歴の累積とループ回数を管理する。
// OpenAI には終了判断をさせない（[END]/[URGENT]タグ廃止）。区切りは患者の「以上です」を本scriptが決定論で検知する。
//   完了: 患者が「以上です」等で聴取終了を宣言 → 個人情報聴取へ
//   中断: 患者が「やめる/結構です」等で中止を希望 → 個人情報聴取へ
//   上限: loopCount >= MAX_LOOPS → 強制的に個人情報聴取へ
//   継続: それ以外（無音=空入力も継続。次ターンの generate_by_OpenAI が NO_RESULT を返し案内へ）
// 副作用: consultationHistory に "AI: <応答>\n患者: <入力>\n" を累積し、loopCount をインクリメント。
// parity なし（履歴は LLM 出力依存のため Python oracle 不要。分類ロジックのみ決定論）。
// プレースホルダー:
//   {{LLM_MODULE}}   = LLM応答モジュール名（generate_by_OpenAI の script_ 名、例: script_受診相談_LLM問診）
//   {{INPUT_MODULE}} = 患者STT入力モジュール名（hearing の 入力_ 名、例: 入力_LLM問診応答）
//   {{MAX_LOOPS}}    = 最大ループ回数（例: 10）
// Nashorn(ES5.1)想定: arrow / let / const / includes / テンプレート文字列 不使用。

var llmResponse = "";
try { llmResponse = String($runner.getModuleResult("{{LLM_MODULE}}") || ""); } catch (e) { llmResponse = ""; }

var patientInput = "";
try { patientInput = String($runner.getModuleResult("{{INPUT_MODULE}}") || ""); } catch (e) { patientInput = ""; }

// 履歴累積（初回は第1問が決定論アナウンス＝LLM出力が空なので "AI:" 行はスキップ）
var history = String($runner.getObject("consultationHistory") || "");
if (llmResponse) {
  history = history + "AI: " + llmResponse + "\n";
}
history = history + "患者: " + patientInput + "\n";
$runner.setObject("consultationHistory", history);

// ループ回数
var loopCount = 0;
try { loopCount = parseInt(String($runner.getObject("loopCount") || "0"), 10); } catch (e2) { loopCount = 0; }
if (isNaN(loopCount)) loopCount = 0;
loopCount = loopCount + 1;
$runner.setObject("loopCount", String(loopCount));

var maxLoops = parseInt("{{MAX_LOOPS}}", 10);
if (isNaN(maxLoops) || maxLoops <= 0) maxLoops = 10;

// NFKC 風の軽い正規化（全角空白除去）。判定は indexOf ベース。
var t = patientInput.replace(/　/g, "").replace(/\s+/g, "");

// 完了マーカー（患者が聴取終了を宣言）
var doneMarkers = ["以上", "おわり", "終わり", "終了", "特にな", "特にありません", "他にな", "他にありません",
                   "全部です", "全部で", "ぜんぶです", "ぜんぶで", "で全部", "もうない", "もう無い",
                   "もうありません", "もうないです", "それだけ", "これだけ", "それで全部", "これで全部"];
// 中断マーカー（患者が中止を希望）
var abortMarkers = ["やめ", "中断", "もういい", "もう結構", "結構です", "けっこうです", "やめます", "やめたい"];

function hasAny(str, arr) {
  var i;
  for (i = 0; i < arr.length; i++) {
    if (str.indexOf(arr[i]) >= 0) return true;
  }
  return false;
}

var result;
if (hasAny(t, doneMarkers)) {
  result = "完了";
} else if (hasAny(t, abortMarkers)) {
  result = "中断";
} else if (loopCount >= maxLoops) {
  result = "上限";
} else {
  result = "継続";
}

$runner.getLogger().info("[CONSULT-LOOP] loop=" + loopCount + "/" + maxLoops + " result=" + result + " input='" + patientInput + "'");
$runner.setResult(result);
