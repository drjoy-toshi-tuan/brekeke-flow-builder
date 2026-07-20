// Context Read API Probe
// 目的: Brekeke Nashorn Script から saveContext2DB で保存した session context
//   (例: currentAppointmentDate=2027-01-01 00:00:00) を読む API シグネチャを empirical 特定。
//
// 前提: このモジュールを date_current + saveContext2DB の **後段** に配置すること。
//   上流で currentAppointmentDate context が DB に DATE 型で保存されている状態で実行する。
// 期待: いずれかの probe が "2027-01-01 00:00:00" 等の文字列を OK で返す。
//   どれも EXCEPTION なら Java 直接アクセスや別 API 名を継続調査。

var logger = $runner.getLogger();
var ctxName = "currentAppointmentDate";

function probe(label, fn) {
    try {
        var r = fn();
        var s = (r === null || r === undefined) ? String(r) : ("" + r);
        // 長すぎるオブジェクトは切る
        if (s.length > 200) s = s.substring(0, 200) + "...(truncated)";
        logger.info("[ctx-probe " + label + "] OK result=" + s + " type=" + (typeof r));
    } catch (e) {
        logger.info("[ctx-probe " + label + "] EXCEPTION " + (e && e.message ? e.message : e));
    }
}

// === A. $runner メソッド ===
probe("A1-runner-getContext",        function(){ return $runner.getContext(ctxName); });
probe("A2-runner-getContextValue",   function(){ return $runner.getContextValue(ctxName); });
probe("A3-runner-getSessionContext", function(){ return $runner.getSessionContext(ctxName); });
probe("A4-runner-getModuleResult",   function(){ return $runner.getModuleResult(ctxName); });
probe("A5-runner-getVariable",       function(){ return $runner.getVariable(ctxName); });
probe("A6-runner-getValue",          function(){ return $runner.getValue(ctxName); });

// === B. $ivr メソッド ===
probe("B1-ivr-getContext",       function(){ return $ivr.getContext(ctxName); });
probe("B2-ivr-getContextValue",  function(){ return $ivr.getContextValue(ctxName); });
probe("B3-ivr-getParameter",     function(){ return $ivr.getParameter(ctxName); });
probe("B4-ivr-getVariable",      function(){ return $ivr.getVariable(ctxName); });

// === C. $ivr.getEx() 系 (AmiVoice/Soniox の $ivr.getEx().ivr.timeStart と同じ経路) ===
probe("C1-ex-context-key",       function(){ return $ivr.getEx().context[ctxName]; });
probe("C2-ex-session-key",       function(){ return $ivr.getEx().session[ctxName]; });
probe("C3-ex-ctx-key",           function(){ return $ivr.getEx().ctx[ctxName]; });
probe("C4-ex-vars-key",          function(){ return $ivr.getEx().vars[ctxName]; });
probe("C5-ex-ivr-context-key",   function(){ return $ivr.getEx().ivr.context[ctxName]; });
probe("C6-ex-getCtx",            function(){ return $ivr.getEx().getContext(ctxName); });

// === D. $ivr.getEx() の reflection で何が入っているか調査 ===
probe("D1-ex-keys", function(){
    var ex = $ivr.getEx();
    var keys = [];
    for (var k in ex) keys.push(k);
    return "ex top-level keys: " + keys.join(",");
});
probe("D2-ex-ivr-keys", function(){
    var ex = $ivr.getEx();
    if (!ex || !ex.ivr) return "ex.ivr is null";
    var keys = [];
    for (var k in ex.ivr) keys.push(k);
    return "ex.ivr keys: " + keys.join(",");
});

// === E. $ivr.getDb() (IVR class doc に存在記載あり、ConnectionManager 返却) ===
probe("E1-getDb-getContext",  function(){ return $ivr.getDb().getContext(ctxName); });
probe("E2-getDb-get",          function(){ return $ivr.getDb().get(ctxName); });
probe("E3-getDb-keys",         function(){
    var db = $ivr.getDb();
    var keys = [];
    for (var k in db) keys.push(k);
    return "db keys: " + keys.join(",");
});

// === F. Java 直接 (推測候補) ===
probe("F1-com-brekeke-SessionContext", function(){
    var SC = Java.type("com.brekeke.pbx.context.SessionContext");
    return SC.get(ctxName);
});
probe("F2-com-brekeke-ContextManager", function(){
    var CM = Java.type("com.brekeke.pbx.context.ContextManager");
    return CM.get(ctxName);
});
probe("F3-jp-drjoy-ContextManager", function(){
    var CM = Java.type("jp.drjoy.pbx.context.ContextManager");
    return CM.get(ctxName);
});
probe("F4-com-brekeke-Session", function(){
    var S = Java.type("com.brekeke.pbx.Session");
    return S.get(ctxName);
});
probe("F5-jp-drjoy-Context", function(){
    var C = Java.type("jp.drjoy.pbx.Context");
    return C.get(ctxName);
});

// === G. saveContext2DB 系 (NoteUtils と同じパッケージで読み API があるか) ===
probe("G1-com-brekeke-common-ContextUtils", function(){
    var CU = Java.type("com.brekeke.pbx.common.ContextUtils");
    return CU.read(ctxName);
});
probe("G2-com-brekeke-common-Context", function(){
    var C = Java.type("com.brekeke.pbx.common.Context");
    return C.get(ctxName);
});
probe("G3-com-brekeke-common-DbUtils", function(){
    var D = Java.type("com.brekeke.pbx.common.DbUtils");
    return D.read(ctxName);
});

logger.info("[ctx-probe] all candidates attempted");
$runner.setResult("ctx-probe-done");
