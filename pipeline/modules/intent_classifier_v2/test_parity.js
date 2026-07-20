// intent_classifier_v2 JS↔Python parity harness（node で実行）
// script.js（本物の engine）を SPEC 注入して全 test_cases.json を実行し、
// 期待値と照合する。oracle（Python）と同一ケースを共有 = 二重実装の一致を機械検証。
// 使い方: node modules/intent_classifier_v2/test_parity.js
"use strict";
var fs = require("fs");
var path = require("path");

var dir = __dirname;
var data = JSON.parse(fs.readFileSync(path.join(dir, "test_cases.json"), "utf8"));
var template = fs.readFileSync(path.join(dir, "script.js"), "utf8");

var failures = [];
var total = 0;

Object.keys(data.specs).forEach(function (specName) {
    var spec = data.specs[specName];
    var cases = data.cases.filter(function (c) { return c.spec === specName; });
    if (cases.length === 0) return;

    // SPEC 注入（wiring placeholder はダミー値）
    var code = template
        .split("{{SPEC_JSON}}").join(JSON.stringify(spec))
        .split("{{INPUT_MODULE}}").join("入力_test")
        .split("{{CONTEXT_NAME}}").join("testContext")
        .split("{{STEP_NAME}}").join("test");

    cases.forEach(function (c) {
        total += 1;
        var captured = { result: null, objects: {} };
        var $runner = {
            getLogger: function () { return { error: function () {} }; },
            getModuleResult: function () { return c.input; },
            setResult: function (v) { captured.result = v; },
            setObject: function (k, v) { captured.objects[k] = v; }
        };
        /* eslint-disable no-new-func */
        var fn = new Function("$runner", code + "\nreturn classify($runner.getModuleResult(''));");
        var got = fn($runner);

        var ok = true;
        Object.keys(c.expect).forEach(function (k) {
            if (k === "entities") {
                Object.keys(c.expect.entities).forEach(function (ek) {
                    if (got.entities[ek] !== c.expect.entities[ek]) ok = false;
                });
            } else if (got[k] !== c.expect[k]) {
                ok = false;
            }
        });
        // setResult がclassify結果と一致しているか（実行部の配線検証）
        if (captured.result !== got.intent) ok = false;

        console.log("[" + (ok ? "PASS" : "FAIL") + "] " + c.desc + ": 「" + c.input
            + "」 → " + got.intent);
        if (!ok) failures.push({ c: c, got: got, setResult: captured.result });
    });
});

console.log("\n=== " + (total - failures.length) + "/" + total + " PASS (JS engine) ===");
if (failures.length > 0) {
    failures.forEach(function (f) {
        console.log("\nFAIL: " + f.c.desc);
        console.log("  期待: " + JSON.stringify(f.c.expect));
        console.log("  実際: " + JSON.stringify(f.got) + " / setResult=" + f.setResult);
    });
    process.exit(1);
}
