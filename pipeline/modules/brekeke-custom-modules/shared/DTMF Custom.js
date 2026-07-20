
//=============================================================================================
// Functions
var getProperty = function(key, defVal) {
    var value = $runner.getProperty(key);
    if (!value) {
        // Log a warning if the key is not set
        $runner.getLogger().warn("Property '" + key + "' is not set. Using default value: " + defVal);
    }
    return value ? value : defVal;
}

// Remove place tts_g: {tts_g:お名前をフルネームでおっしゃってください。}
function getTranscribe(prompt) {
	if (!prompt) {
	return "";
	}

	var match = prompt.match(/\{tts_g:([^}]*)\}/);
	if (!match) {
	return "";
	}
	var content = match[1];
	return content;
}

// Tìm sub-module
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

// Tạo utterance từ kết quả dtmf hoặc từ prompt
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

// Call save2db để lưu utterance và context của dtmf
function saveResultDtmf(val, startTime, endTime) {
	var msgType = 1; //person
	
	saveRequestData = {
		"transcribe": val, // nội dung câu thoại
		"data": val, // value của context
		"start_ts": startTime.toISOString(), // thời gian bắt đầu câu thoại
		"end_ts": endTime.toISOString() // thời gian kết thúc câu thoại
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


// Call save2db để lưu utterance của prompt
function savePrompt(prompt, startTime, endTime) {
    var msgType = 0; //bot
	// remove tts_g
	var content = getTranscribe(prompt);
	if (!content || content.length == 0) {
		return;
	}

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

// caculate start time dtmf time audio
function getStartTimeDtmfOfUser(endTime) {
	// Time in miliseconds was fixed 2s
	startInMilliSeconds = endTime.getTime() - 2000
	return new Date(startInMilliSeconds);
}

// Create a common log prefix to avoid duplication
var officeId = getProperty(".office_id");
var deployTo = $ivr.getMyNumber();
var tenantId = $ivr.getTenant();
var callId = $ivr.getRID();
var logPrefix = "[" + tenantId + "][" + officeId + "][" + deployTo + "][" + callId + "] ";

//=============================================================================================
// Main
var prompt = getProperty("prompt", "");
var max_dtmf_length = getProperty( "max_dtmf_length", 0);
var timeout = getProperty( "timeout", 0);
var idx = timeout.indexOf( "," );
var timeoutEx = -1;
if( idx > 0 ){
	timeoutEx = timeout.substring( idx + 1 ).trim();
	timeout = timeout.substring( 0, idx ).trim();
}var termdtmf = getProperty("termdtmf", "");
var removeTerm = !getProperty("remove_term", "").equalsIgnoreCase("no");
var val = "";
var retry = Number(getProperty("retry", 0) );
retry = isNaN( retry ) ? 0 : retry;
var condition = getProperty("condition", "");
var prompt_retry = getProperty("prompt_retry", "");
if( prompt_retry == null || prompt_retry.length() == 0 ){
    prompt_retry = prompt;
}

prompt = $ivr.exec("system-variable", "replaceTemplateVariables", prompt);               // access a variable from object
prompt_retry = $ivr.exec("system-variable", "replaceTemplateVariables", prompt_retry);   // access a variable from object

do{
 var startTime = new Date();
 val = $ivr.playAndInputEx(prompt,max_dtmf_length,timeout,timeoutEx,termdtmf,removeTerm);
 var endTime = new Date();
 
 // Save prompt in utterance
savePrompt(prompt, startTime, endTime);

// Save dtmf in utterance and context field
saveResultDtmf(val, startTime, endTime);

 val = "" + val;
 if( condition != null && condition.length() > 0 ){
    var b = eval( "" + condition );
	 if( b ){
		break;
	}else{
		val = "";
		if( retry == 0 ){
			break;
		} 
		retry--;
		prompt = prompt_retry;
	 }
 }else{
     break;
 }
}while( true );

$runner.setResult( val );
