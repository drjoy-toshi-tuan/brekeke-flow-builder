// FAQ Matcher — Input Read API Probe
// =============================================================================
// 目的:
//   OpenAI を一切使わない RAG 検索フローで、@General$Script から
//   「直前の STT モジュールの文字起こし(生テキスト)」を読む API を実機で確定する。
//
// 背景 (なぜ probe が要るか):
//   $runner.getModuleResult(<name>) は「マッチした next 条件の label」を返すことがある
//   (2026-04-22 大分赤十字病院_診療, 入力=OpenAIモジュール で判明 → docs/brekeke/
//    script_templates/future_date.js)。
//   本フローは OpenAI を使わず入力源は常に STT だが、STT の success 分岐 label は "success"
//   (next: {"condition":"^.+$", "label":"success"}) なので、getModuleResult が
//     ・文字起こし全文 ("駐車場はありますか")  ← 欲しいのはこれ
//     ・"success" という label 文字列          ← これだと検索クエリが壊れる
//   のどちらを返すかが未確定。推測で書くと「"success" を FAQ 検索にかける」事故になるため、
//   ここを 1 コールで実機確定させる。
//
// 使い方:
//   1. 実在する 問い合わせ系 STT (例: 入力_相談_問合せ) の **直後** に @General$Script を
//      1 個追加し、この全文をペーストする。
//   2. 下の CONFIG の STT_MODULE_NAME を、その直前 STT のモジュール名に差し替える。
//   3. このモジュールの jumps に `^in-probe-done$` (または `^.+$`) を 1 本登録し、
//      その先を「テスト完了」TTS → Disconnect に繋いでおく (通話が綺麗に終わるように)。
//   4. テスト発信し、STT で **既知のはっきりしたフレーズ** を発話する
//      (推奨例: 「ちゅうしゃじょうはありますか」)。何と言ったかを必ずメモしておく。
//   5. Brekeke ログを文字列 "[in-probe" で grep して全行回収 → 共有。
//   6. 手順 4 で発話したフレーズを OK で返した probe が「正解 API」。
//      "success" / null / EXCEPTION の解釈は README.md の評価表を参照。
//
// 安全性: このスクリプトはログ出力と setResult のみで、保存・外部通信・状態変更を一切しない
//         (非破壊)。確定後は速やかに本 probe を撤去 / FAQ Matcher 本体に差し替えること。
// =============================================================================

// =============================================================================
// CONFIG — テスト対象に合わせて差し替え
// =============================================================================
var STT_MODULE_NAME = "入力_相談_問合せ";   // ← 直前の STT モジュール名に差し替える

// =============================================================================
// PROBE — 編集不要
// =============================================================================
var logger = $runner.getLogger();
var STT = STT_MODULE_NAME;

// 値を見やすい文字列に (長すぎる場合は切り詰め)
function show(r) {
    if (r === null || r === undefined) return String(r);
    var s = "" + r;
    if (s.length > 300) s = s.substring(0, 300) + "...(truncated)";
    return s;
}

// 1 候補ずつ試して結果をログ。例外は握りつぶして次へ。
function probe(label, fn) {
    try {
        var r = fn();
        logger.info("[in-probe " + label + "] OK value=[" + show(r) + "] type=" + (typeof r));
    } catch (e) {
        logger.info("[in-probe " + label + "] EXCEPTION " + (e && e.message ? e.message : e));
    }
}

logger.info("[in-probe] start STT_MODULE_NAME=" + STT);

// === A. $runner.getModuleResult 系 (本命) ===
//   A1 が文字起こしを返せば最良 (CONFIG に STT 名を書くだけで本体が完成する)。
//   A1 が "success" を返したら label が返る挙動 → B / saveContext2DB 経路に切替。
probe("A1-getModuleResult(name)", function(){ return $runner.getModuleResult(STT); });
probe("A2-getModuleResult()",     function(){ return $runner.getModuleResult(); });

// === B. system-variable 経由 (モジュール名をそのまま変数名として読む) ===
//   context 読みの正式 API ($ivr.exec system-variable) で STT 名を引いてみる。
//   STT 結果が同名 system variable として露出していれば、saveContext2DB なしで読める。
probe("B1-sysvar(name)",          function(){ return $ivr.exec("system-variable", "getSystemVariableValue", STT); });
probe("B2-sysvar(name.result)",   function(){ return $ivr.exec("system-variable", "getSystemVariableValue", STT + ".result"); });

// === C. $ivr.getEx() 反射 — STT 結果がどのキーに居るか探索 (context_probe D 系と同手法) ===
probe("C1-ex-keys", function(){
    var ex = $ivr.getEx();
    var keys = [];
    for (var k in ex) keys.push(k);
    return "ex keys: " + keys.join(",");
});
probe("C2-ex-ivr-keys", function(){
    var ex = $ivr.getEx();
    if (!ex || !ex.ivr) return "ex.ivr is null";
    var keys = [];
    for (var k in ex.ivr) keys.push(k);
    return "ex.ivr keys: " + keys.join(",");
});

// === D. その他 getter 候補 (存在すれば) ===
probe("D1-runner-getResult(name)",  function(){ return $runner.getResult(STT); });
probe("D2-runner-getContext(name)", function(){ return $runner.getContext(STT); });

logger.info("[in-probe] all candidates attempted");
$runner.setResult("in-probe-done");
