// Notes Plugin API Probe
// 目的: drjoy^...$Script モジュール (Nashorn JS) から Brekeke Notes plugin
//   (contains / matches / lookup / script) を呼べる API シグネチャを特定する。
//
// 各候補を try/catch でログ出力し、Brekeke ログから「どれが動くか」を判別する。
// 期待: $runner.getLogger().info() のログ行に [probe N] result=... type=...
//       例外時は [probe N] EXCEPTION: ReferenceError: "xxx" is not defined
//
// テスト Note 前提:
//   Note 名: test_holidays
//   内容: 行ごとに yyyy-MM-dd の祝日 (test_holidays_note.txt 参照、17 行)

var logger = $runner.getLogger();
var target = "2026-05-05";   // Note に含まれるはず
var miss   = "2026-12-25";   // Note に含まれないはず
var noteName = "test_holidays";
var tenant = "drjoy";
var qualifiedName = tenant + "." + noteName;  // multi-tenant 規約: <tenant>.<note_name>

function probe(label, fn) {
    try {
        var r = fn();
        logger.info("[probe " + label + "] OK result=" + r + " type=" + (typeof r));
    } catch (e) {
        logger.info("[probe " + label + "] EXCEPTION " + (e && e.message ? e.message : e));
    }
}

// --- A. グローバル関数として直接呼べるか (ARS と同じ syntax) ---
// A1-A4: 単純な note 名 (tenant prefix なし)
probe("A1-contains-global-hit",  function(){ return contains(noteName, target); });
probe("A2-contains-global-miss", function(){ return contains(noteName, miss); });
probe("A3-matches-global",       function(){ return matches(noteName, target); });
probe("A4-lookup-global",        function(){ return lookup(noteName, target, 1, 1); });
// A5-A8: multi-tenant 規約 <tenant>.<note_name> 形式 (浜口さん環境: drjoy.test_holidays)
probe("A5-contains-tenant-hit",  function(){ return contains(qualifiedName, target); });
probe("A6-contains-tenant-miss", function(){ return contains(qualifiedName, miss); });
probe("A7-matches-tenant",       function(){ return matches(qualifiedName, target); });
probe("A8-lookup-tenant",        function(){ return lookup(qualifiedName, target, 1, 1); });

// --- B. $pbx グローバル経由 ---
probe("B1-pbx-contains",  function(){ return $pbx.contains(noteName, target); });
probe("B2-pbx-notes",     function(){ return $pbx.notes.contains(noteName, target); });

// --- C. $runner / $ivr 経由 ---
probe("C1-runner-contains-plain",    function(){ return $runner.contains(noteName, target); });
probe("C2-ivr-contains-plain",       function(){ return $ivr.contains(noteName, target); });
probe("C1b-runner-contains-tenant",  function(){ return $runner.contains(qualifiedName, target); });
probe("C2b-ivr-contains-tenant",     function(){ return $ivr.contains(qualifiedName, target); });
// getNote 1 引数版 (qualified / plain 両パターン)
probe("C3-runner-getNote-plain",     function(){ return $runner.getNote(noteName); });
probe("C4-ivr-getNote-plain",        function(){ return $ivr.getNote(noteName); });
probe("C3b-runner-getNote-qual",     function(){ return $runner.getNote(qualifiedName); });
probe("C4b-ivr-getNote-qual",        function(){ return $ivr.getNote(qualifiedName); });
// getNote 2 引数版 (公式ドキュメント signature: getNote(tenant, name))
probe("C5-runner-getNote-drjoy",     function(){ return $runner.getNote(tenant, noteName); });
probe("C6-runner-getNote-empty",     function(){ return $runner.getNote("", noteName); });
probe("C7-runner-getNote-null",      function(){ return $runner.getNote(null, noteName); });
probe("C8-ivr-getNote-drjoy",        function(){ return $ivr.getNote(tenant, noteName); });
probe("C9-ivr-getNote-empty",        function(){ return $ivr.getNote("", noteName); });
// グローバル直呼び (関数名 getNote が露出している可能性)
probe("C10-getNote-global-1arg",     function(){ return getNote(noteName); });
probe("C11-getNote-global-2arg",     function(){ return getNote(tenant, noteName); });
probe("C12-getNote-global-qual",     function(){ return getNote(qualifiedName); });

// --- D. Java.type 経由 (推定) ---
probe("D1-com-brekeke-notes", function(){
    var Plg = Java.type("com.brekeke.pbx.notes.NotesPlugin");
    return Plg.contains(noteName, target);
});
probe("D2-jp-drjoy-notes", function(){
    var Plg = Java.type("jp.drjoy.pbx.notes.NotesPlugin");
    return Plg.contains(noteName, target);
});
probe("D3-com-brekeke-plugin", function(){
    var Mgr = Java.type("com.brekeke.pbx.plugin.PluginManager");
    return Mgr.invoke("contains", noteName, target);
});

// --- E. Brekeke の Plugin / NoteManager クラスを推定で叩く ---
probe("E1-NoteManager", function(){
    var NM = Java.type("com.brekeke.pbx.notes.NoteManager");
    return NM.contains(noteName, target);
});
probe("E2-Notes-static", function(){
    var N = Java.type("com.brekeke.pbx.Notes");
    return N.contains(noteName, target);
});

// --- F. FlowRunner 自体に notes アクセサがあるか反射的に列挙 ---
probe("F1-runner-methods", function(){
    var keys = [];
    for (var k in $runner) {
        keys.push(k);
    }
    return keys.join(",");
});
probe("F2-ivr-methods", function(){
    var keys = [];
    for (var k in $ivr) {
        keys.push(k);
    }
    return keys.join(",");
});

logger.info("[probe] all candidates attempted");
$runner.setResult("probe_done");
