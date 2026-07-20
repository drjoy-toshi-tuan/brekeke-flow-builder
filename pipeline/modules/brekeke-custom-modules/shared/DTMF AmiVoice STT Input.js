//=============================================================================================
// Imports
var Thread = Java.type("java.lang.Thread");
var Runnable = Java.type("java.lang.Runnable");
var HashMap = Java.type("java.util.HashMap");
var AtomicReference = Java.type("java.util.concurrent.atomic.AtomicReference");

// ============================================================================================
// Speech Recognition Constants and Helpers
// ============================================================================================

var SPEECH_LANGUAGES = {
	"日本語": "ja",
	"英語": "en",
	"中国語": "zh",
	"韓国語": "ko",
};

var SPEECH_RECOGNITION_FLAGS = {
	"検出しない": 0,
	"音声開始前から検出": 1,
	"音声開始から検出": 2,
};

var SPEECH_ENGINES = {
	"会話汎用": 0,
	"会話医療": 1,
	"入力汎用": 2,
	"入力医療": 3,
};

var SPEECH_TYPES = {
	"テキスト": 0,
	"診療科": 1,
	"氏名": 2,
	"氏名カナ": 3,
	"数値": 4,
	"電話番号": 5,
	"日時": 6,
};

//=============================================================================================
// Functions
var getProperty = function(key, defVal) {
    var value = $runner.getProperty(key);
	if (!value || value === "デフォルト") {
        value = $runner.getProperty(".amivoice." + key);
    }
    return value ? value : defVal;
}

// find sub-module
function findSubModule(name) {
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

// create utterance from dtmf result or prompt
function createUtterance(contentStr, msgType, startInMsec, endInMsec) {
	var seqNumber = $runner.get("seq") ? $runner.get("seq") : 1;
	$runner.set("seq", (seqNumber + 1));
	return {
			seq: seqNumber,
			messageType: msgType,
			text: contentStr,
			utteranceType: "MESSAGE",
			startMsec: startInMsec,
			endMsec:endInMsec
		};
}

// call save2db to save utterance and context of dtmf
function saveResultDtmf(transcribe, data, startTime, endTime) {
	var saveRequestData = {
		"transcribe": transcribe, // utterance content
		"data": data, // value of context
		"start_ts": startTime, // start time of utterance
		"end_ts": endTime // end time of utterance
	}
	
	try {
		var save = findSubModule("save-");
		if (save > 0) {
			$runner.set("transcribe.save", JSON.stringify(saveRequestData));
			$runner.execSub(save);
		}
	} finally {
		$runner.remove("transcribe.save");
	}
}

// call save2db to save utterance of prompt
function savePrompt(prompt, startTime, endTime) {
    var msgType = 0; //bot
	var content = $ivr.exec("tts-prompt", "extractTaggedContent", JSON.stringify({ prompt: prompt, stripTags: true }));
	if (!content || content.length == 0) {
		return;
	}
	
	// save prompt as utterance
	var startInMsec= $ivr.exec("save2db", "parseTimestamp", startTime.toISOString())
	var endInMsec = $ivr.exec("save2db", "parseTimestamp", endTime.toISOString())
	var saveRequestData = {
			utterance: createUtterance(content, msgType, startInMsec, endInMsec)
	};
	
	var operationSuccess = $ivr.exec("save2db", "save", JSON.stringify(saveRequestData));
	if (!operationSuccess) {
		$runner.getLogger().error(logPrefix + "Failed to save result prompt as utterance.");
	} else {
		$runner.getLogger().info(logPrefix + "Successfully saved result prompt as utterance.");
	}
}

// get speech language from property
function getSpeechLanguage(key) {
	var language = getProperty(key, "");
	if (language && SPEECH_LANGUAGES[language]) {
		return SPEECH_LANGUAGES[language];
	}
	return $ivr.getLanguage();
}

// setup speech recognition parameters
function setupSpeechParams() {
	var params = new HashMap();
	params.put("from", $ivr.getOtherNumber());
	params.put("to", $ivr.getMyNumber());
	params.put("language", getSpeechLanguage("language"));
	params.put("uri", getProperty("uri", ""));
	params.put("engine", SPEECH_ENGINES[getProperty("engine", "会話汎用")] || 0);
	params.put("keep_filter_token", getProperty("keep_filter_token", "no").equalsIgnoreCase("yes"));
	params.put("silent_detection_ms", getProperty("silent_detection_ms", 1500));
	params.put("timeout_ms", getProperty("timeout_ms", 30000));
	params.put("profile_words", getProperty("profile_words", ""));
	params.put("type", SPEECH_TYPES[getProperty("type", "テキスト")] || 0);
	params.put("probability", getProperty("probability", 0.7));
	params.put("save_log", getProperty("save_log", "no").equalsIgnoreCase("yes"));
	params.put("stop_play_when_speech", getProperty("stop_play_when_speech", "yes").equalsIgnoreCase("yes"));
	return params;
}

// get speech detection flag
function getSpeechDetectionFlag() {
	return SPEECH_RECOGNITION_FLAGS[getProperty("detection_flag", "音声開始前から検出")] || 1;
}

// create DTMF input configuration object
function createDtmfConfig() {
	// get timeout and timeoutEx from property
	var timeout = getProperty( "timeout", 0);
	var idx = timeout.indexOf( "," );
	var timeoutEx = -1;
	if( idx > 0 ){
		timeoutEx = timeout.substring( idx + 1 ).trim();
		timeout = timeout.substring( 0, idx ).trim();
	}

	// get removeTerm from property
	var removeTerm = !getProperty("remove_term", "").equalsIgnoreCase("no");

	return {
		maxLength: getProperty( "max_dtmf_length", 0),
		timeout: timeout,
		timeoutEx: timeoutEx,
		termChars: getProperty("termdtmf", ""),
		removeTerm: removeTerm
	};
}

// ============================================================================================
// Main Input Function
// ============================================================================================

// function to get DTMF or speech (priority to the first to come)
function mainGetInputDtmfOrSpeech(prompt, retryDtmf) {
	// create DTMF configuration object
	var dtmfConfig = createDtmfConfig();
	// if retryDtmf is true, only get DTMF without starting audio plugin
	if (retryDtmf) {
		return {
			value: $ivr.playAndInputEx(prompt, dtmfConfig.maxLength, dtmfConfig.timeout, dtmfConfig.timeoutEx, dtmfConfig.termChars, dtmfConfig.removeTerm),
			type: "DTMF"
		};
	}
	
	// setup speech recognition parameters
	var speechParams = setupSpeechParams();
	var detectionFlag = getSpeechDetectionFlag();
	var assi = $ivr.startAudioPlugin("amivoice", speechParams, detectionFlag);
	
	if (!assi) {
		// if audio plugin cannot be started, only get DTMF
		return {
			value: $ivr.playAndInputEx(prompt, dtmfConfig.maxLength, dtmfConfig.timeout, dtmfConfig.timeoutEx, dtmfConfig.termChars, dtmfConfig.removeTerm),
			type: "DTMF"
		};
	}
	
	return runParallelInput(prompt, dtmfConfig, assi, speechParams);
}

// ============================================================================================
// Parallel Input Processing
// ============================================================================================

// run parallel DTMF and speech input processing
function runParallelInput(prompt, dtmfConfig, assi, speechParams) {
	// use object to store results from threads
	var threadResults = {
		results: null,
		error: null,
		dtmfResult: null
	};
	var inputTypeRef = new AtomicReference(null);
	
	// cache telephone event manager to avoid calling multiple times
	var tm = $ivr.getEx().phone.getTelephoneEventManager();
	
	// create speech recognition runner
	var stopPlayWhenSpeech = speechParams.get("stop_play_when_speech");
	var speechRunner = createSpeechRunner(assi, tm, inputTypeRef, threadResults, stopPlayWhenSpeech);
	
	// create DTMF input runner
	var dtmfRunner = createDtmfRunner(prompt, dtmfConfig, assi, inputTypeRef, threadResults);
	
	// start threads with descriptive names
	var speechWorker = new Thread(speechRunner, "DTMF-Speech-Input-Speech");
	var dtmfWorker = new Thread(dtmfRunner, "DTMF-Speech-Input-DTMF");
	
	// record start time to calculate remaining timeout for speechWorker
	var startTime = Date.now();
	var timeoutMs = speechParams.get("timeout_ms") || 30000;
	
	speechWorker.start();
	dtmfWorker.start();
	
	// wait for threads to complete
	// Strategy: 
	// 1. Wait for dtmfWorker with timeoutMs limit (if it finishes early, good)
	// 2. If dtmfWorker is still running after timeoutMs, stop speechWorker but let dtmfWorker continue
	// 3. Then wait for dtmfWorker to complete (it has its own timeout)
	dtmfWorker.join(timeoutMs);
	
	// calculate elapsed time and remaining timeout for speechWorker
	var elapsedMs = Date.now() - startTime;
	var remainingTimeoutMs = Math.max(0, timeoutMs - elapsedMs);
	$runner.getLogger().info(logPrefix + "Remaining timeout: " + remainingTimeoutMs);

	// if speechWorker has exceeded timeout, stop it immediately
	if (remainingTimeoutMs === 0) {
		if (assi.isRunning()) {
			$runner.getLogger().info(logPrefix + "Stopping assi because of timeout");
			assi.stop();
		}
	}
	
	// wait for speechWorker with remaining timeout (if any)
	speechWorker.join(remainingTimeoutMs);
	
	// if dtmfWorker is still running (timeoutMs < dtmfTimeout), wait for it to complete
	// dtmfWorker has its own timeout in playAndInputEx(), so allow it to finish naturally
	if (dtmfWorker.isAlive()) {
		$runner.getLogger().info(logPrefix + "DTMF worker is still running, waiting for it to complete");
		dtmfWorker.join();
	}
	
	// process and return result
	return processInputResult(inputTypeRef, threadResults.dtmfResult, threadResults.results, threadResults.error);
}

// create speech recognition runner
function createSpeechRunner(assi, tm, inputTypeRef, threadResults, stopPlayWhenSpeech) {
	return new Runnable({
		run: function() {
			try {
				$runner.getLogger().info(logPrefix + "[Speech Runnable] start");
				var stopPlaying = stopPlayWhenSpeech;
				// condition while has checked DTMF buffer, so no need to check again in loop
				while (assi.isRunning() && tm.getDtmfBuffer().length() == 0) {
					if (stopPlaying && assi.obj.get("transcribe.start") === true) {
					  	$runner.getLogger().info(logPrefix + "[Speech Runnable] stop playing");
						$ivr.stopPlaying();
						stopPlaying = false;  
					}

					// check if DTMF input is available, if so give DTMF priority 
					if (tm.getDtmfBuffer().length() > 0) {
						$runner.getLogger().info(logPrefix + "[Speech Runnable] DTMF buffer has data, DTMF priority");
						break;
					}
					
					var transcribeData = assi.obj.get("transcribe.data");
					if (transcribeData && inputTypeRef.compareAndSet(null, "SPEECH")) {
						threadResults.results = transcribeData;
						$ivr.stop();
						$runner.getLogger().info(logPrefix + "Transcribed data: " + JSON.stringify(transcribeData));
						break;
					}
				}
				$runner.getLogger().info(logPrefix + "[Speech Runnable] end while with DTMF buffer: " + tm.getDtmfBuffer().length() + " and assi running: " + assi.isRunning());
			} catch (e) {
				threadResults.error = e;
				$runner.getLogger().error(logPrefix + "Speech recognition error: " + e);
			} finally {
				if (assi.isRunning()) {
					assi.stop();
				}
			}
		}
	});
}

// create DTMF input runner
// DTMF always has priority, so set result even if SPEECH was set first
function createDtmfRunner(prompt, dtmfConfig, assi, inputTypeRef, threadResults) {
	return new Runnable({
		run: function() {
			try {
				$runner.getLogger().info(logPrefix + "[DTMF Runnable] start");
				// play prompt and wait for DTMF (prompt is empty because it has been played in main thread)
				var val = $ivr.playAndInputEx(prompt, dtmfConfig.maxLength, dtmfConfig.timeout, dtmfConfig.timeoutEx, dtmfConfig.termChars, dtmfConfig.removeTerm);
				
				if (val && val.length() > 0) {
					// Always set DTMF result (DTMF has priority over SPEECH)
					threadResults.dtmfResult = val;
					
					// Try to set inputTypeRef to DTMF (may fail if already set to SPEECH, but DTMF still has priority)
					var wasSet = inputTypeRef.compareAndSet(null, "DTMF");
					var logMsg = wasSet ? "DTMF received and set: " : "DTMF received (overriding previous input): ";
					$runner.getLogger().info(logPrefix + logMsg + val);

					$ivr.stop();
					if (assi.isRunning()) {
						assi.stop();
					}
				}
			} catch (e) {
				threadResults.error = e;
				$runner.getLogger().error(logPrefix + "DTMF thread error: " + e);
			}
		}
	});
}

// process input result and return
// Always prioritize DTMF if available
function processInputResult(inputTypeRef, dtmfResult, results, error) {
	// Always check DTMF first - DTMF has highest priority
	if (dtmfResult && dtmfResult.length() > 0) {
		$runner.getLogger().info(logPrefix + "[processInputResult] DTMF has priority, returning DTMF: " + dtmfResult);
		return {
			value: dtmfResult,
			type: "DTMF"
		};
	}
	
	// Only return SPEECH if no DTMF input
	if (inputTypeRef.get() === "SPEECH") {
		if (error) {
			return {
				value: "ERROR",
				type: "SPEECH"
			};
		} else if (results && results.transcribe) {
		  $runner.setObject("raw_text", results.transcribe); // Set transbribe to variable
			return {
				transcribe: results.transcribe,
				value: results.data ? results.data : results.transcribe,
				type: "SPEECH",
				startTime: results.start_ts,
				endTime: results.end_ts
			};
		} else {
			return {
				value: "NO_RESULT",
				type: "SPEECH"
			};
		}
	} else {
		// timeout or no input
		return {
			value: "TIMEOUT",
			type: ""
		};
	}
}

//=============================================================================================
// Main Function
//=============================================================================================

// create a common log prefix to avoid duplication
var officeId = getProperty(".office_id");
var deployTo = $ivr.getMyNumber();
var tenantId = $ivr.getTenant();
var callId = $ivr.getRID();
var logPrefix = "[" + tenantId + "][" + officeId + "][" + deployTo + "][" + callId + "] ";

var prompt = getProperty("prompt", "");
var val = "";
var retry = Number(getProperty("retry", 0) );
retry = isNaN( retry ) ? 0 : retry;
var condition = getProperty("condition", "");
var prompt_retry = getProperty("prompt_retry", "");
if( prompt_retry == null || prompt_retry.length() == 0 ){
    prompt_retry = prompt;
}

prompt = $ivr.exec("system-variable", "replaceTemplateVariables", prompt);             // access a variable from object
prompt_retry = $ivr.exec("system-variable", "replaceTemplateVariables", prompt_retry); // access a variable from object

var retryDtmf = false;

do{
 var startTime = new Date();
 var inputResult = mainGetInputDtmfOrSpeech(prompt, retryDtmf);
 var endTime = new Date();
 $runner.getLogger().info(logPrefix + "[processInputResult] inputResult: " + JSON.stringify(inputResult));
 val = inputResult.value;
 
 // Save prompt in utterance
 savePrompt(prompt, startTime, endTime);
if( val != "ERROR" && val != "NO_RESULT" && val != "TIMEOUT" ){
    saveResultDtmf(
		inputResult.transcribe ? inputResult.transcribe : val,
		val, 
		inputResult.startTime ? inputResult.startTime : startTime.toISOString(), 
		inputResult.endTime ? inputResult.endTime : endTime.toISOString()
	);
}

 val = "" + val;
 if( inputResult.type === "DTMF" && condition != null && condition.length() > 0 ){
    var b = eval( "" + condition );
	 if( b ){
		break;
	}else{
		val = "NO_RESULT";
		if( retry == 0 ){
			break;
		}
		retryDtmf = true;
		retry--;
		prompt = prompt_retry;
	 }
 }else{
     break;
 }
}while( true );

$runner.setResult( val );
