// ==========================================================================
// functions
function getContextValue() {
  var data = $runner.getProperty("contextValue");
  if (!data) return null;

  return $ivr.exec("system-variable", "replaceTemplateVariables", data);
}

// ==========================================================================
// function saveCheckpoint
function saveCheckpoint(value) {
  try {
    if (!$ivr.connected()) {
      $runner.getLogger().info("[saveContext2DB][" + $ivr.getRID() + "] skip checkpoint save (disconnected): " + value);
      return;
    }
    
    $ivr.exec("save2db", "save", JSON.stringify({
      contextField: {
        contextName: "checkpoint",
        displayType: "TEXT",
        value: value
      }
    }));

  } catch (e) {
    $runner.getLogger().error(
      "[CustomJump][" + $ivr.getRID() + "] Checkpoint save failed: " + e
    );
  }
}

function setCheckpointObject(key, value) {
  try {
    $ivr.setObject(key, value);

  } catch (e) {

    $runner.getLogger().error("[saveContext2DB][" + key + "] setObject failed: " + e);
  }
}

// ==========================================================================
// main
// CHECKPOINT IN
var rid = $ivr.getRID();
var saveContextKey = "saveContext." + rid;
var moduleName = $runner.getCurrentModuleName();
var checkpointKey = "checkpoint." + rid;
var value = moduleName + "_IN";
saveCheckpoint(value);
setCheckpointObject(checkpointKey, value);

var contextName = $runner.getProperty("contextName");
var contextDisplayType = $runner.getProperty("contextDisplayType");
var contextValue = getContextValue();

if (!contextName || !contextDisplayType || !contextValue) {
  setCheckpointObject(saveContextKey, true);
  $runner.getLogger().info("[saveContext2DB] invalid input data");
  return;
}

var contextField = {
  contextName: contextName,
  displayType: contextDisplayType,
  value: contextValue
};

var saveRequestData = JSON.stringify({
  contextField: contextField
});

$runner.getLogger().info("[saveContext2DB] start save context " + saveRequestData);

try {

  $ivr.exec("save2db", "save", saveRequestData);
  // Save the context value to the session
  $runner.setObject(contextName, contextValue);
  $runner.setResult(contextValue);

} catch (e) {

  $runner.getLogger().error(
    "[saveContext2DB][" + $ivr.getRID() + "] Error in execution: " + e
  );

  $runner.setResult(null);
}
// ==========================================================================
 // CHECKPOINT OUT
value = moduleName + "_OUT";
saveCheckpoint(value);
setCheckpointObject(checkpointKey, value);
setCheckpointObject(saveContextKey, true);