// Get properties from the IVR flow context.
var prompt = $runner.getProperty("prompt");
var ignore_dtmf = !$runner.getProperty("stop_by_dtmf").equalsIgnoreCase("yes");
var categoryWords = $runner.getProperty("category_words");

// ==================================================================
function getIntonationText(prompt) {
  if (!categoryWords || categoryWords.length == 0) {
    $runner.getLogger().warn("[TTS node data] No category words defined. Exiting.");
    return null
  }

  var apiUrl = $runner.getProperty(".get-intonation-from-drjoy.url");
  if (!apiUrl) {
    $runner.getLogger().warn("[TTS node data] No API URL defined for get-intonation-from-drjoy.");
    return null
  }

  var categoryNames = categoryWords.split("\n").map(function(item) {
        return item.trim();
    });
  var data = {
    apiUrl: apiUrl,
    requestPayload: {
      text: $ivr.exec("tts-prompt", "extractTaggedContent", JSON.stringify({ prompt: prompt, stripTags: true })),
      categoryNames: categoryNames
    }
  };

  return $ivr.exec("get-intonation-from-drjoy", "getIntonationText", JSON.stringify(data));
}

function parseTimestampToMillis(dateTime) {
  var millisecond = $ivr.exec("save2db", "parseTimestamp", dateTime);
  var callTransferTimeKey = "transfer_time_" + $ivr.getRID();
  var transferTime = $runner.getObject(callTransferTimeKey);

  // Subtract the transfer time from the total time in milliseconds, because sound contains no transfer.
  if (transferTime) {
    millisecond = millisecond - transferTime;
  }
  return millisecond;
}

// ==================================================================
// --- Main Execution Block ---
// Replace template variables in the prompt using system-variable module.
prompt = $ivr.exec("system-variable", "replaceTemplateVariables", prompt);
var content = $ivr.exec("tts-prompt", "extractTaggedContent", JSON.stringify({ prompt: prompt, stripTags: true }));
var intonationResult = getIntonationText(prompt);
intonationResult = intonationResult ? JSON.parse(intonationResult) : null;
$runner.getLogger().info("[TTS node data] prompt: " + prompt + " Intonation result: " + JSON.stringify(intonationResult));
if (!intonationResult) {
  $runner.getLogger().error("[TTS node data] Failed to get intonation text. Using original prompt.");
} else {
  prompt = "{tts_g:" + intonationResult.ssmlText + "}";
}

// Play the final prompt to the user and record start/end times.
var startTime = new Date();
$ivr.play(prompt,ignore_dtmf);
var endTime = new Date();

if (!content || content.length == 0) {
  $runner.getLogger().info("[TTS node data] No valid TTS content found in prompt. Skipping save operation.");
  return;
}

// --- Save Interaction to Database ---
try {
  var seqNumber = $runner.get("seq") ? $runner.get("seq") : 1;
  var utterance = {
      seq:seqNumber,
      messageType:0,
      text:content,
      utteranceType:"MESSAGE",
      startMsec:parseTimestampToMillis(startTime.toISOString()),
      endMsec:parseTimestampToMillis(endTime.toISOString())
  };
  var operationSuccess = $ivr.exec("save2db", "save", JSON.stringify({utterance:utterance}));
  if (!operationSuccess) {
      $runner.getLogger().error("[Re-confirmation node data] Failed to save utterance.");
  } else {
    $runner.set("seq", (seqNumber + 1));
    $runner.getLogger().info("[Re-confirmation node data] Successfully saved utterance and updated seq number to " + (seqNumber + 1));
  }
} catch (error) {
  $runner.getLogger().error("[Re-confirmation node data] Failed to save utterance: " + error);
}