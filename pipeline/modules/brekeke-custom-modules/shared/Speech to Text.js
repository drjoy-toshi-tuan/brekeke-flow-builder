// noinspection JSUnresolvedReference,JSUnusedGlobalSymbols,ES6ConvertVarToLetConst

// ==================================================================

var Thread = Java.type("java.lang.Thread");
var Runnable = Java.type("java.lang.Runnable");
var HashMap = Java.type("java.util.HashMap");
var PlayParam = Java.type("com.brekeke.tel.PlayParam");

// ==================================================================

var languages = {
    "日本語": "ja",
    "英語": "en",
    "中国語": "zh",
    "韓国語": "ko",
}

var speechRecognitionFlags = {
    "検出しない": 0,
    "音声開始前から検出": 1,
    "音声開始から検出": 2,
};

var engines = {
    "会話汎用": 0,
    "会話医療": 1,
    "入力汎用": 2,
    "入力医療": 3,
};

var types = {
    "テキスト": 0,
    "診療科": 1,
    "氏名": 2,
    "氏名カナ": 3,
    "数値": 4,
    "電話番号": 5,
    "日時": 6,
    "氏名エンジン": 7
}

// ==================================================================

var getProperty = function(key, defVal) {
    var value = $runner.getProperty(key);
    if (!value || value === "デフォルト") {
        value = $runner.getProperty(".amivoice." + key);
    }
    return value ? value : defVal;
}

var getLanguage = function(key) {
    var language = getProperty(key, "");
    if (language) {
        return languages[language];
    }
    return $ivr.getLanguage();
}

var findSubModule = function(name) {
    var module = $runner.getCurrentModule();
    if (module) {
        for (var i = 0; i < module.subs.size(); i++) {
            var submod = module.subs.get(i);
            if (submod.label && submod.label.startsWith(name)) {
                return i + 1;
            }
        }
    }
    return 0;
}

// ==================================================================

var params = new HashMap();
params.put("from", $ivr.getOtherNumber());
params.put("to", $ivr.getMyNumber());
params.put("call_id", $ivr.getRID());
params.put("language", getLanguage("language"));
params.put("uri", getProperty("uri", ""));
params.put("engine", engines[getProperty("engine", "会話汎用")]);
params.put("keep_filter_token", $runner.getProperty("keep_filter_token").equalsIgnoreCase("yes"));
params.put("silent_detection_ms", getProperty("silent_detection_ms", 1500));
params.put("timeout_ms", getProperty("timeout_ms", 30000));
params.put("profile_name", $runner.getProperty("profile_name"));
params.put("profile_words", $runner.getProperty("profile_words"));
params.put("type", types[getProperty("type", "テキスト")]);
params.put("probability", getProperty("probability", 0.7));
params.put("save_log", $runner.getProperty("save_log").equalsIgnoreCase("yes"));
params.put("detection_flag", speechRecognitionFlags[getProperty("detection_flag", "音声開始前から検出")]);

// @debug
$runner.getLogger().debug(">>> Amivoice Property: " + params);

// ==================================================================

var detectionFlag = params.get("detection_flag");
var assi = $ivr.startAudioPlugin("amivoice", params, detectionFlag);

// ==================================================================

if (assi) {
    var playParam = new PlayParam();
    playParam.setFileName($ivr.getEx().ivr.userinfo.getPrivateOrSystemPlayFileName("ja", "recstart"));
    $ivr.getEx().ivr.ply.playDtmfIgnore(playParam);

    var results;
    var error;

    var runner = new Runnable({
        run: function() {
            try {
                var stopPlaying = false;
                while (assi.isRunning()) {
                    assi.waitResult();

                    if (!stopPlaying) {
                        $ivr.stopPlaying();
                        stopPlaying = true;
                    }
                    results = assi.obj.get("transcribe.data");

                    if (results) {
                        $ivr.stop();
                        $runner.getLogger().info(">>> Transcribed data: " + JSON.stringify(results));
                        break;
                    }
                }
            } catch (e) {
                error = e;
                $runner.getLogger().error(e);
                if (e instanceof java.lang.InterruptedException) {
                    Thread.currentThread().interrupt();
                }
            } finally {
                $runner.getLogger().info(">>> Transcribed finished");
                assi.stop();
            }
        }
    });

    var worker = new Thread(runner);
    worker.start();

    var timeoutMs = getProperty("timeout_ms", 30000);
    worker.join(timeoutMs);

    assi.stop();

    if (worker.isAlive()) {
        $runner.setResult("TIMEOUT");
    } else if (error || (results && results.error)) {
        $runner.setResult("ERROR");
    } else {
        if (results && results.transcribe) {
            $runner.setObject("raw_text", results.transcribe); // Set transbribe to variable
            if (params.get("type") === 0) {
                // 音声タイプがテキストの時、RAG検索が必要なら実行.
                try {
                    var rag = findSubModule("rag-");
                    if (rag > 0) {
                        $runner.set("transcribe.data", JSON.stringify(results));
                        $runner.execSub(rag);
                        var ragData = $runner.get("transcribe.rag");
                        if (ragData) {
                            var ragJson = JSON.parse(ragData);
                            results.data = ragJson.word;
                            $runner.getLogger().info(">>> RAG module: " + JSON.stringify(results));
                        }
                    }
                } finally {
                    $runner.remove("transcribe.data");
                    $runner.remove("transcribe.rag");
                }
            }
            // 結果をDBに保存する必要がある場合は実行.
            try {
                var save = findSubModule("save-");
                if (save > 0) {
                    $runner.set("transcribe.save", JSON.stringify(results));
                    $runner.execSub(save);
                }
            } finally {
                $runner.remove("transcribe.save");
            }
            // 結果を設定.
            // [DEBUG] transcribe と data の両方を確認用に出力
            $runner.setResult("[transcribe]" + results.transcribe + " [data]" + (results.data || "null"));
        } else {
            // 結果なしの時.
            $runner.setResult("NO_RESULT");
        }
    }
} else {
    $runner.setResult("ERROR");
}
