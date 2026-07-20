// Script Template: go_back_classifier （L0 戻る/繰り返し検知・OpenAI不使用）
// 商談デモ「フリー発話受付」の各聴取STT入力ゲートで、L1=ABSENT のとき走る L0。
// 入力STTテキストを検査し "戻る" / "繰り返し" / "NONE" を setResult する。
//   戻る     … やっぱり変更したい/キャンセルしたい/別の用件/最初から/やり直し 等＝前工程へ戻す
//   繰り返し … もう一回言って/もう一度/聞こえなかった/なんて言った 等＝直前TTS再生
//   NONE     … いずれでもない（→FAQ へ）
// parity: modules/go_back_classifier/oracle.py（同一辞書・同一手順）。Note 非依存。
// プレースホルダー:
//   {{INPUT_MODULE}}  = 入力元モジュール名（聴取の STT。getModuleResult フォールバック）
//   {{CONTEXT_FIELD}} = STT 結果が保存される context 名（本命の読み取り元）
// Nashorn(ES5.1)想定: String.normalize / includes / arrow / let / const / テンプレート文字列 不使用。

var GO_BACK_PHRASES = [
  "やっぱり", "やはり", "別の用件", "別件", "ほかの用件", "他の用件",
  "最初から", "最初に戻", "はじめから", "一から", "やり直し", "やりなおし",
  "前に戻", "戻して", "戻りたい", "違う用件",
  "取り消して", "取消して"
  // "変更したい"/"キャンセルしたい"は用件発話でも使われるため除外。"やっぱり"で拾われる。
];
var REPEAT_PHRASES = [
  "もう一回", "もう一度", "もういちど", "もっかい", "もう１回",
  "聞こえなかった", "聞こえません", "聞こえなくて", "聞こえづらい", "聞き取れ",
  "なんて言った", "なんて言いました", "なんと言った", "何て言った",
  "言ってください", "言って下さい", "もう一度言って", "繰り返し", "くりかえし"
];

function hasAny(s, arr) {
  for (var i = 0; i < arr.length; i++) { if (s.indexOf(arr[i]) >= 0) return true; }
  return false;
}

function classify(raw) {
  if (raw == null) return "NONE";
  if (typeof raw === "object" && raw.text != null) raw = raw.text;
  var s = String(raw).replace(/^\s+|\s+$/g, "");
  if (s === "") return "NONE";
  if (hasAny(s, GO_BACK_PHRASES)) return "戻る";   // 複合（もう一回最初から）は戻る優先
  if (hasAny(s, REPEAT_PHRASES)) return "繰り返し";
  return "NONE";
}

// ── 入力取得: STT 保存 context（{{CONTEXT_FIELD}}）優先 → getModuleResult（{{INPUT_MODULE}}）fallback ──
var rawIn = null;
try {
  if (typeof $runner.getContextModel === "function") {
    var cm = $runner.getContextModel();
    if (cm) {
      if (typeof cm.get === "function") rawIn = cm.get("{{CONTEXT_FIELD}}");
      else if (cm["{{CONTEXT_FIELD}}"] != null) rawIn = cm["{{CONTEXT_FIELD}}"];
    }
  }
} catch (e) { /* fallthrough */ }
try { if ((rawIn == null || rawIn === "") && typeof $runner.getContext === "function") rawIn = $runner.getContext("{{CONTEXT_FIELD}}"); } catch (e) { /* fallthrough */ }
if (rawIn == null || rawIn === "") { try { rawIn = $runner.getModuleResult("{{INPUT_MODULE}}"); } catch (e) { rawIn = null; } }

var out = classify(rawIn);
$runner.getLogger().info("[GO-BACK] in=" + rawIn + " => " + out);
$runner.setResult(out);
