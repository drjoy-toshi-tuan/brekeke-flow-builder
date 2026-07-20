// ==================================================================
/**
 * Extracts the content from a Google TTS tag {tts_g:...} within a prompt string.
 * @param {string} prompt The full prompt string containing the TTS tag.
 * @returns {string} The content inside the TTS tag, or an empty string if not found.
 */
function getTranscribe (prompt) {
  if(!prompt) {
    return "";
  }
  
  var match = prompt.match(/\{tts_g:([^}]*)\}/);
  if (!match) {
    return "";
  }
  var content = match[1];
  return content;
}

/**
 * Checks if a string value is a valid date in "yyyy-mm-dd hh:mm" format.
 * @param {string} value The string to validate.
 * @returns {boolean} True if the value is a valid date in the specified format, false otherwise.
 */
function isFormatDate(value) {
  var pattern = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/;
  if (!pattern.test(value)) {
    $runner.getLogger().info(value + " is not in the correct date format yyyy-mm-dd hh:mm");
    return false;
  }
  
  var date = new Date(value.replace(" ", "T"));
  if (isNaN(date.getTime())) {
     $runner.getLogger().info(value + " is not a valid date");
     return false;
  }
  
  return true;
}

/**
 * Converts a date string from Gregorian format (e.g., "2024-08-23 15:30")
 * to the Japanese Imperial Era (Wareki) format (e.g., "令和6年8月23日 15時30分").
 * @param {string} dateStr The date string in "yyyy-mm-dd" or "yyyy-mm-dd hh:mm" format.
 * @returns {string|null} The converted Wareki date string, "明治以前" for dates before Meiji, or null if the format is invalid.
 */
function toWareki(dateStr) {
  var pattern = /^\d{4}-\d{2}-\d{2}( \d{2}:\d{2})?$/;
  if (!pattern.test(dateStr)) {
    return null;
  }

  // Tách phần ngày và giờ (nếu có)
  var parts = dateStr.split(" ");
  var datePart = parts[0];
  var timePart = parts.length > 1 ? parts[1] : null;

  var dateBits = datePart.split("-");
  var y = parseInt(dateBits[0], 10);
  var m = parseInt(dateBits[1], 10);
  var d = parseInt(dateBits[2], 10);

  var date = new Date(y, m - 1, d);

  // Danh sách các niên hiệu Nhật
  var eras = [
    { name: "令和", start: new Date(2019, 4 - 1, 1) },  // 2019-05-01
    { name: "平成", start: new Date(1989, 0, 8) },      // 1989-01-08
    { name: "昭和", start: new Date(1926, 11, 25) },    // 1926-12-25
    { name: "大正", start: new Date(1912, 6, 30) },     // 1912-07-30
    { name: "明治", start: new Date(1868, 0, 25) }      // 1868-01-25
  ];

  // Xác định niên hiệu phù hợp
  for (var i = 0; i < eras.length; i++) {
    if (date >= eras[i].start) {
      var era = eras[i];
      var eraYear = y - era.start.getFullYear() + 1;
      var yearStr = (eraYear === 1) ? "元" : eraYear;

      var wareki = era.name + yearStr + "年" + m + "月" + d + "日";

      // check if has time
      if (timePart) {
        var hm = timePart.split(":");
        var hh = hm[0];
        var mm = hm[1];
        wareki += " " + hh + "時" + mm + "分";
      }

      return wareki;
    }
  }

  return "明治以前";
}

/**
 * Processes a value for re-confirmation. If the value is a date, it formats it
 * based on the 'skipReadHour' and 'dateReadingMode' properties.
 * @param {string} value The input value to process.
 * @returns {string} The processed value, ready for TTS playback.
 */
function getReConfirmValue(value) {
  if (!isFormatDate(value)) {
    return value;
  }

  // Check if we need to skip reading the hour
  var skipReadHour = $runner.getProperty("skipReadHour").equalsIgnoreCase("yes");
  var parts = value.split(" ");
  var datePart = parts[0];
  var timePart = parts.length > 1 ? parts[1] : null;
  if (skipReadHour) {
    timePart = null;
  }
  
  var skipReadYear = $runner.getProperty("skipReadYear").equalsIgnoreCase("yes");
  var dateReadingMode = $runner.getProperty("dateReadingMode");
  if(dateReadingMode == "Wareki") {
    var forWareki = timePart ? (datePart + " " + timePart) : datePart;
    var wareki = toWareki(forWareki);
    if (skipReadYear) {
      // Remove the first year part of the string: "<Year>年"
      wareki = wareki.replace(/^[^年]*年/, "");
    }
    return wareki;
  }
  
  // Read Gregorian: split date/time and format with 月/日 when skipping year
  var dateBits = datePart.split("-");
  var mm = dateBits.length > 1 ? dateBits[1] : "";
  var dd = dateBits.length > 2 ? dateBits[2] : "";
  if (skipReadYear) {
    var formattedDate = mm + "月" + dd + "日";
    return timePart ? (formattedDate + " " + timePart) : formattedDate;
  }
  return timePart ? (datePart + " " + timePart) : datePart;
}
// ==================================================================
// --- Main Execution Block ---

// Get properties from the IVR flow context.
var prompt = $runner.getProperty("prompt");
var nodeName = $runner.getProperty("nodeName");

// If a nodeName is specified, get its result and replace the #data# placeholder in the prompt.
if(nodeName) {
  var nodeValue = $runner.getModuleResult(nodeName).replaceAll("null", "");
  $runner.getLogger().info("[Re-confirmation node data] node name: " + nodeName + " node value: "+nodeValue);
  // Process the value (e.g., format date) before inserting it into the prompt.
  var reConfirmValue = getReConfirmValue(nodeValue);
  prompt = prompt.replaceAll("#data#", reConfirmValue);
}

prompt = $ivr.exec("system-variable", "replaceTemplateVariables", prompt); // access a variable from object

// Play the final prompt to the user and record start/end times.
var startTime = new Date();
$ivr.play(prompt,true);
var endTime = new Date();

// --- Save Interaction to Database ---
try {
  var seqNumber = $runner.get("seq") ? $runner.get("seq") : 1;
  var utterance = {
      seq:seqNumber,
      messageType:0,
      text:getTranscribe(prompt),
      utteranceType:"MESSAGE",
      startMsec:$ivr.exec("save2db", "parseTimestamp", startTime.toISOString()),
      endMsec:$ivr.exec("save2db", "parseTimestamp", endTime.toISOString())
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