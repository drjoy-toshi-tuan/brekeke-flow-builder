// ==================================================================
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

function speechRetryCounter(propertyKey) {
  if(!propertyKey) return;
  var prompt = $runner.getProperty(propertyKey);
  prompt = $ivr.exec("system-variable", "replaceTemplateVariables", prompt); // access a variable from object
  if( ( typeof $ivr ) == 'object' && prompt.length() > 0 ){
    var startTime = new Date();
    $ivr.play( prompt, false );
    var endTime = new Date();
    try {
      var save = findSubModule("save-");
      if (save > 0) {
        var transcribeText = getTranscribe(prompt);
        $runner.getLogger().info("TTS/save text=" + transcribeText);
        var data = {
          transcribe:transcribeText, 
          actor:"AI",
          start_ts:startTime.toISOString(),
          end_ts:endTime.toISOString()
        };
        $runner.getLogger().info("transcribe.save : " + JSON.stringify(data));
        $runner.set("transcribe.save", JSON.stringify(data));
        $runner.execSub(save);
      }
    } finally {
        $runner.remove("transcribe.save");
    }
  }
}
// ==================================================================

var m = $runner.getCurrentModule();
var name = m.name;
var c = Number($runner.getObject("Counter-" + name));
c = isNaN( c ) ? 0 : c;
var max = Number($runner.getProperty("retry_count")); 
if( c >= max ){
  speechRetryCounter("prompt_false");
  $runner.setResult( "false" );
}else{
  c++;
  $runner.setObject( "Counter-" + name, c );
  speechRetryCounter("prompt_true");
  $runner.setResult( "true" );
}
