$runner.getLogger().info(">>> Save to database - ENHANCED VERSION WITH CALL-LEVEL CONNECTION MANAGEMENT");
var contextName = $runner.getProperty("contextName");
var contextDisplayType = $runner.getProperty("contextDisplayType");
var seqNumber = $runner.get("seq") ? $runner.get("seq") : 1; 

function parseTranscribeData() {
    var data = $runner.get("transcribe.save");
    if (!data) {
      $runner.getLogger().warn("No transcribe data found");
      return null;
    }
    
    try {
      return JSON.parse(data);
    } catch (e) {
      $runner.getLogger().error("Invalid JSON data: " + e);
      return null;
    }
  }
  
function getContextData(jsonObj) {
  if (!contextName || !jsonObj || jsonObj.actor === "AI") return null;

  var contextValue = jsonObj.data ? jsonObj.data : jsonObj.transcribe;

  if (contextDisplayType === "PHONE_NUMBER") {
    contextValue = contextValue.replace(/\D/g, ''); // Remove non-digit characters for phone numbers
  }

  // Save the context value to the session
  $runner.setObject(contextName, contextValue);

  return {
    contextName:contextName,
    displayType:contextDisplayType,
    value:contextValue
  };
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

function getUtteranceData(jsonObj, seqNumber) {
  if (!jsonObj) return null;

  var utteranceValue = jsonObj.transcribe ? jsonObj.transcribe : "";
  var messageType = jsonObj.actor === "AI" ? 0 : 1;
  var startMsec = 0;
  var endMsec = 0;
  
  if (jsonObj.start_ts) {
    startMsec = parseTimestampToMillis(jsonObj.start_ts);
  }
  
  if (jsonObj.end_ts) {
    endMsec = parseTimestampToMillis(jsonObj.end_ts);
  }

  return {
    seq:seqNumber,
    messageType:messageType,
    text:utteranceValue,
    utteranceType:"MESSAGE",
    startMsec:startMsec,
    endMsec:endMsec
  };
}

// ==================================================================
// MAIN EXECUTION WITH COMPREHENSIVE ERROR HANDLING AND MONITORING
var jsonObj = null;
var operationSuccess = false;

// Start timing
var startTime = new Date().getTime();
$runner.getLogger().info(">>> Starting ENHANCED database save operation");

try {
  // Step 1: Parse data
  jsonObj = parseTranscribeData();
  if (!jsonObj) {
    $runner.getLogger().warn("No valid transcribe data to save");
    return;
  }

  // Step 2: Prepare data for saving
  var contextField = getContextData(jsonObj);
  var utterance = getUtteranceData(jsonObj, seqNumber);
  if (!contextField && !utterance) {
    $runner.getLogger().warn("No context or utterance data to save");
    return;
  }

  // Step 3: Execute database operation with monitoring
  var saveRequestData = {
    contextField:contextField,
    utterance:utterance
  };
  operationSuccess = $ivr.exec("save2db", "save", JSON.stringify(saveRequestData));

  if (operationSuccess) {
    // Update sequence number only on success
    $runner.set("seq", (seqNumber + 1));
    
    var totalTime = new Date().getTime() - startTime;
    $runner.getLogger().info("DATABASE SAVE COMPLETED SUCCESSFULLY! Total time: " + totalTime + "ms");
  } else {
    $runner.getLogger().error("Database operation failed - sequence number not updated");
  }
  
} catch (e) {
  var errorTime = new Date().getTime() - startTime;
  $runner.getLogger().error("CRITICAL ERROR in database save operation after " + errorTime + "ms: " + e);
  
  // Log detailed error information
  if (e.stack) {
    $runner.getLogger().error("Error stack: " + e.stack);
  }
} finally {
  // NOTE: Connection is managed at call level - no need to close here
  // The call cleanup monitor will handle connection cleanup when call ends
  
  // Final timing and status
  var finalTotalTime = new Date().getTime() - startTime;
  var status = operationSuccess ? "SUCCESS" : "FAILED";
  $runner.getLogger().info(">>> Database save operation " + status + ". Total execution time: " + finalTotalTime + "ms");
  
  $runner.setModuleResult($runner.getLastModuleName(), jsonObj.data ? jsonObj.data : jsonObj.transcribe);
}
