// Session Object Store Cross-Call Probe
// 目的: $ivr.setObject / $runner.setObject の保存先がコール (セッション) 終了で
//   破棄されるか、コールを跨いで残るかを実機で判定する。
//
// 背景: generator 標準イディオム (script_結果返却_*) は
//   $ivr.setObject(flowName + "." + rid, res) と RID 入り動的キーで保存しており、
//   ストアがコール越境で生きる実装だった場合、キーが削除されないまま
//   コール数に比例して増える = スローリークになる。
//   (current_appointment_date.js の checkpoint.{rid} / saveContext.{rid} も同型)
//
// 手順: この probe を import して 2 回架電する。
//   1 コール目: 残骸なし → 「けっかは、オーケーです」+ 各キーを書いて終了
//   2 コール目: 1 コール目の値が読めたら「けっかは、エヌジーです」 = コール越境あり
// 判定はアナウンスと Brekeke ログ [LEAK-PROBE] 行の両方で確認できる。

var logger = $runner.getLogger();

function tryGet(label, fn) {
    try {
        var r = fn();
        var s = (r === null || r === undefined) ? "" : String(r);
        logger.info("[LEAK-PROBE] read " + label + " = '" + s + "'");
        return s;
    } catch (e) {
        logger.info("[LEAK-PROBE] read " + label + " EXCEPTION " + (e && e.message ? e.message : e));
        return "";
    }
}
function trySet(label, fn) {
    try {
        fn();
        logger.info("[LEAK-PROBE] write " + label + " OK");
    } catch (e) {
        logger.info("[LEAK-PROBE] write " + label + " EXCEPTION " + (e && e.message ? e.message : e));
    }
}

var rid = "";
try { rid = String($ivr.getRID()); } catch (e) {
    logger.info("[LEAK-PROBE] getRID EXCEPTION " + (e && e.message ? e.message : e));
}

// ---------- Phase 1: read (必ず write より先。前回コールの残骸が見えるか) ----------
var ivrMarker    = tryGet("ivr_marker (fixed, $ivr)",       function(){ return $ivr.getObject("leak_probe.ivr_marker"); });
var runnerMarker = tryGet("runner_marker (fixed, $runner)", function(){ return $runner.getObject("leak_probe.runner_marker"); });
var crossApi     = tryGet("ivr_marker (via $runner)",       function(){ return $runner.getObject("leak_probe.ivr_marker"); });
var counterStr   = tryGet("counter (fixed, $ivr)",          function(){ return $ivr.getObject("leak_probe.counter"); });
var lastRid      = tryGet("last_rid (fixed, $ivr)",         function(){ return $ivr.getObject("leak_probe.last_rid"); });

// 前回コールの RID 動的キー (= generator イディオムと同型) が読めるか
var ridPayload = "";
if (lastRid && lastRid !== rid) {
    ridPayload = tryGet("rid_payload (dynamic, $ivr)", function(){ return $ivr.getObject("leak_probe." + lastRid); });
}

var found = [];
if (ivrMarker)    found.push("ivr_marker");
if (runnerMarker) found.push("runner_marker");
if (crossApi)     found.push("cross_api");
if (counterStr)   found.push("counter");
if (lastRid && lastRid !== rid) found.push("last_rid");
if (ridPayload)   found.push("rid_payload(dynamic)");

var persistent = found.length > 0;
var counter = 1;
if (counterStr && !isNaN(parseInt(counterStr, 10))) counter = parseInt(counterStr, 10) + 1;

logger.info("[LEAK-PROBE] rid=" + rid
    + " | found=[" + found.join(",") + "]"
    + " | verdict=" + (persistent
        ? "CROSS_CALL_PERSISTENT (NG: コール越境あり = rid動的キーはスローリーク)"
        : "PER_CALL_ONLY (OK: コール終了で破棄)"));

// ---------- Phase 2: アナウンス ----------
var speech;
if (persistent) {
    speech = "{tts_g:けっかは、エヌジーです。オブジェクトが、コールをまたいで、のこっています。これは、" + counter + "かいめの、コールです。}";
} else {
    speech = "{tts_g:けっかは、オーケーです。まえのコールの、オブジェクトは、きえています。}";
}
try { $ivr.play(speech, true); } catch (e) {
    logger.info("[LEAK-PROBE] play EXCEPTION " + (e && e.message ? e.message : e));
}

// ---------- Phase 3: write (今回の値を保存。次回コールの read で検証される) ----------
trySet("ivr_marker (fixed, $ivr)",       function(){ $ivr.setObject("leak_probe.ivr_marker", "from_rid_" + rid); });
trySet("runner_marker (fixed, $runner)", function(){ $runner.setObject("leak_probe.runner_marker", "from_rid_" + rid); });
trySet("counter (fixed, $ivr)",          function(){ $ivr.setObject("leak_probe.counter", String(counter)); });
trySet("rid_payload (dynamic, $ivr)",    function(){ $ivr.setObject("leak_probe." + rid, "payload_of_" + rid); });
trySet("last_rid (fixed, $ivr)",         function(){ $ivr.setObject("leak_probe.last_rid", rid); });

// ---------- Phase 4: 同一コール内読み戻し (write 自体が効いているかのセルフチェック) ----------
var selfCheck = tryGet("self_check (ivr_marker)", function(){ return $ivr.getObject("leak_probe.ivr_marker"); });
logger.info("[LEAK-PROBE] self_check=" + (selfCheck ? "WRITE_OK" : "WRITE_MISSING (setObject が効いていない可能性)"));

logger.info("[LEAK-PROBE] done");
$runner.setResult("probe_done");
