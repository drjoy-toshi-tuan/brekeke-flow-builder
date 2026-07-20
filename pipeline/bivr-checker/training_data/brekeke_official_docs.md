# Brekeke IVR Official Documentation Summary

Fetched from https://docs.brekeke.com/ on 2026-04-08.
This document summarizes the official Brekeke PBX documentation related to IVR Flow Designer,
module templates, classes, and .bivr file format.

---

## 1. Overview: Flow Designer

Source: https://docs.brekeke.com/pbx/flow-developers-guide

With Flow Designer, Brekeke PBX administrators can create graphic flows. The created flows can be
used for multiple purposes. One of the typical purposes is to define IVR behaviors with graphic flows.

Either the customized flows can be based on basic module templates, or administrators can create
their own module templates depending on their needs.

To use IVR Script or the Flow Designer feature, the IVR option is required to be added to the
Brekeke PBX license.

---

## 2. .bivr File Format

Source: Reverse-engineered from actual .bivr files + https://docs.brekeke.com/pbx/control-items-flow-designer

### 2.1 File Container

A `.bivr` file is a **ZIP archive** (PK header). It contains one or more flow definition files:

```
<filename>.bivr (ZIP)
  +-- flows/@flow_<url-encoded-flow-name>.txt    (JSON)
  +-- flows/@flow_<url-encoded-flow-name-2>.txt  (JSON)
  ...
```

Each `.txt` file inside is a **JSON document** representing a single flow.

### 2.2 Flow JSON Top-Level Structure

```json
{
  "layout": {},
  "resultValue": "",
  "postCallAction": "",
  "name": "<flow-name>",
  "start": "<start-module-name>",
  "modules": { ... },
  "desc": ""
}
```

| Key | Description |
|-----|-------------|
| `layout` | Visual layout metadata (empty object or coordinates) |
| `resultValue` | The result value returned by the flow when completed |
| `postCallAction` | Script executed after the flow completes (POST FLOW SCRIPT) |
| `name` | Flow name |
| `start` | Name of the first module to execute |
| `modules` | Dictionary of all modules keyed by module name |
| `desc` | Flow description |

### 2.3 Module JSON Structure

Each module in the `modules` dictionary has this structure:

```json
{
  "layout": { "x": -850, "y": -560 },
  "next": [
    {
      "condition": "^TIMEOUT$",
      "label": "timeout",
      "nextModuleName": "<target-module-name>"
    },
    {
      "condition": "^ERROR$",
      "label": "error",
      "nextModuleName": "<target-module-name>"
    },
    {
      "condition": "^.+$",
      "label": "success",
      "nextModuleName": "<target-module-name>"
    }
  ],
  "subs": [
    {
      "moduleName": "<sub-module-name>",
      "label": "<label>"
    }
  ],
  "name": "<module-name>",
  "description": "",
  "matchingmethod": 1,
  "type": "<category>^<subcategory>$<template-name>",
  "params": { ... }
}
```

| Key | Description |
|-----|-------------|
| `layout` | x/y position on the visual designer canvas |
| `next` | Array of conditional connections to other modules. Each entry has `condition` (regex), `label`, and `nextModuleName`. Up to 11 connections supported. |
| `subs` | Sub-module references (up to 3). Used for sub-flows or auxiliary processing. |
| `name` | Module instance name |
| `description` | Module description text |
| `matchingmethod` | How conditions in `next` are evaluated (0 or 1). 0 = first match, 1 = regex matching |
| `type` | Module template type in format `<category>^<subcategory>$<template>` |
| `params` | Dictionary of module-specific parameters |

### 2.4 Module Connection Logic

- Modules are connected via the `next` array.
- Each entry in `next` contains a regex `condition` that is matched against the module's result.
- Common conditions: `^TIMEOUT$`, `^ERROR$`, `^NO_RESULT$`, `^.+$` (any non-empty), `^.*$` (any), `true`, `false`, empty string (unused).
- `nextModuleName` specifies the next module to execute when the condition matches.
- Empty `nextModuleName` means the connection is not used.

### 2.5 Module Type Format

The `type` field uses the pattern: `<category>^<subcategory>$<template-name>`

Examples from actual files:
- `drjoy^External Integration$DTMF AmiVoice STT Input`
- `drjoy^Text To Speech$Speech Retry Counter`
- `drjoy^Persistence$save2db`
- Standard Brekeke types also exist (e.g., `Basic$Answer`, `Basic$Transfer`, etc.)

---

## 3. Flow Designer Control Buttons

Source: https://docs.brekeke.com/pbx/control-items-flow-designer

### Select Flows Screen

| Name | Description |
|------|-------------|
| NEW FLOW | Create a new flow |
| OPEN FLOWS | Show flow list; select flow(s) and open them in workspace |
| CLOSE ALL FLOWS | Close all flows on the current flow list |
| IMPORT | Import saved flows and modules |
| EXPORT | Show Module and Flow list; select and export to **.bivr file** |

### Flow Settings

| Name | Description |
|------|-------------|
| FLOW NAME | Current flow name |
| DESCRIPTION | Current flow's description |
| POST FLOW SCRIPT | Script executed after the flow is completed |
| RESULT VALUE | Set result value |

---

## 4. Default Module Templates

Source: https://docs.brekeke.com/pbx/module-templates-flow-designer

Module templates are organized into 5 categories:

### 4.1 General Module Templates

Source: https://docs.brekeke.com/pbx/general-module-templates-flow-designer

| Module Template | Description |
|----------------|-------------|
| **Script** | Execute JavaScript specified at the module settings. In Multi-Tenant Edition with "Safe mode", tenant admin cannot edit scripts. |
| **Background Script** | Execute JavaScript code in background |
| **Conditional Jump** | Jump to the next module depending on matched condition |
| **Retry Counter** | Count processing passes and determine if count reaches a set value |
| **Reset Retry Counter** | Clear retry counter |
| **Jump to Flow** | Jump to another flow |
| **Send Email** | Send an email |

### 4.2 Data Access Module Templates

Source: https://docs.brekeke.com/pbx/data-access-module-templates

| Module Template | Description |
|----------------|-------------|
| **SQL Query** | Query Database with SQL Statement (uses ConnectionManager class) |
| **SOAP** | SOAP Web Service |
| **HTTP** | HTTP Access to other web services |

### 4.3 IVR Module Templates

Source: https://docs.brekeke.com/pbx/ivr-module-templates

| Module Template | Description |
|----------------|-------------|
| **Prompt** | Play pre-recorded sound file(s). Uses method `play(string playlist, boolean ignoreDTMF)`. |
| **Voice Rec (File)** | Play sound file(s) and record voice, stored as file at specified location |
| **Voice Rec (Voicemail)** | Play sound file(s) and record voice, stored as voicemail under specified PBX user. Uses `recordVoicemail`. |
| **Voice Rec (Prompt)** | Play sound file(s) and record voice, stored as prompt file in Voice Prompt list. Uses `recordPrompt`. |
| **DTMF input** | Play sound file and retrieve DTMF input signals. Uses `playAndInput`. |
| **Answer** | Answer the call. Uses `answer()`. |
| **Response 18x** | Send 18x response before answering the call. Uses `response18x`. |
| **Call Transfer** | Start attended/blind transfer. Uses `transfer`. |
| **Cancel Call Transfer** | Cancel transfer and go back to conversation with original party. Uses `cancelTransfer`. |
| **Disconnect** | Drop current call. Uses `dropcall()`. |
| **Reject** | During receiving process, reject an incoming call. |

### 4.4 CCS Module Templates (Contact Center Suite)

Source: https://docs.brekeke.com/pbx/ccs-module-templates

| Module Template | Description |
|----------------|-------------|
| **Call Transfer from Queue** | Transfer a customer's call to another destination when in queue |
| **Position in Queue** | Check order of a call in queue |
| **Wait for Silence (AMD)** | When Answering Machine detected, wait to play guidance till recording starts |
| **Set Callback in Queue** | Set callback items into the Queue |
| **Get Call Parameters** | Get call parameters |
| **Set Call Parameters** | Set call parameters |

### 4.5 UC Chatbot Module Templates (Beta)

Source: https://docs.brekeke.com/pbx/uc-chatbot-module-templates

| Module Template | Description |
|----------------|-------------|
| **Buttons** | Place buttons |
| **Leave** | Leave the chat |
| **IBM Watson** | Connect to IBM Watson |
| **Send/Recv** | Send / Receive messages |
| **Transfer** | Transfer a chat |
| **Tag** | Add Tag |

---

## 5. Reference Classes

### 5.1 IVR Class

Source: https://docs.brekeke.com/pbx/ivr-class-flow

Accessed as `$ivr` in flow scripts (v3.10+). Previously `ivr` (deprecated).

#### Methods

| Method | Description |
|--------|-------------|
| `void answer()` | Answer the call. Needed when extension Auto Answer is "no". |
| `void cancelTransfer()` | Back to the original party |
| `String clearDTMFBuffer()` | Get DTMF signals from the signal buffer |
| `boolean connected()` | Check if session is connected |
| `void dropcall()` | Drop current call |
| `void exec(String note, String function, String param)` | Execute another JavaScript function in another note |
| `ConnectionManager getDb(String name)` | Return ConnectionManager for JDBC connection pool |
| `FlowRunner getFlowRunner()` | Return FlowRunner object. Returns null if IVR type is not Flow. |
| `String getLanguage()` | Get current language code ("en", "ja", etc.) |
| `Logger getLogger()` | Return Log4j Logger for debug logging |
| `String getMyNumber()` | Get phone number used for current call |
| `Object getObject(String objectName)` | Get object bound to session |
| `String getOtherNumber()` | Get other party's phone number |
| `String getParameter()` | Get call parameter (passed as `ivr<ext>*<param>`) |
| `String getProperty(String key)` | Retrieve property from Brekeke PBX (set at Options > Advanced) |
| `String getTempDir()` | Get temporary folder pathname |
| `String getTenant()` | Get tenant name (or "-" for non-multi-tenant) |
| `String getUserProperty(String key)` | Retrieve user property value |
| `Boolean isMultitenant()` | Whether PBX is multi-tenant edition |
| `String play(String playlist)` | Play sequence of sound files |
| `String play(String playlist, boolean ignoreDTMF)` | Play sound files, optionally ignoring DTMF |
| `String playAndInput(String playlist, int maxDtmfLength, int timeout, String terminateDtmf, boolean removeTerm)` | Play sound and retrieve DTMF input |
| `void record(String file, int timeout, String terminateDtmf)` | Record sound data |
| `void recordVoicemail(String user, int timeout, String terminateDtmf, Properties prop)` | Record voicemail |
| `void recordPrompt(String lang, String name, int timeout, String terminateDtmf, String filedesc)` | Record prompt file |
| `void response18x(int rescode)` | Send 18x response without SDP |
| `void response18x(int rescode, boolean bSDP)` | Send 18x response with optional SDP |
| `void setLanguage(String lang)` | Set language code |
| `void setObject(String objectName, Object anObject)` | Bind object to session |
| `boolean transfer(String number, int timeout)` | Start attended transfer |

#### Playlist Format (for play/playAndInput methods)

```
playlist = *play-resource
play-resource = dtmf-character / prompt / voice-lib / ulaw-file
dtmf-character = DIGIT / "A" / "B" / "C" / "D" / "*" / "#"
prompt = "{" prompt-name "}"
voice-lib = "{" voice-lib-name ":" voice-lib-param "}"
voice-lib-name = "name" / "date" / "time" / "number"
voice-lib-param = 1*(ALPHA / DIGIT)
ulaw-file = "(" fullpath-ulaw-file ")"
```

Example: `ivr.play("{ring}1234");` plays the file named "ring" from VoicePrompts, then plays 1234 as DTMF.

### 5.2 ConnectionManager Class

Source: https://docs.brekeke.com/pbx/connectionmanager-class-flow

Implements JDBC connection pool. Instance obtained via `ivr.getDb()`.

#### Configuration (at Options > Advanced):
```
db1.driver=com.mysql.jdbc.Driver
db1.url=jdbc:mysql://localhost:3306/dbname?useUnicode=true&characterEncoding=UTF-8
db1.user=root
db1.password=root
```

#### Methods

| Method | Description |
|--------|-------------|
| `void close(Connection con)` | Close JDBC connection (may be recycled if pooled) |
| `void close(Statement st)` | Close JDBC Statement |
| `void close(ResultSet rs)` | Close JDBC ResultSet |
| `Connection getConnection()` | Get JDBC connection from pool |

### 5.3 FlowRunner Class

Source: https://docs.brekeke.com/pbx/flowrunner-class-flow

Provides access to current Flow and Module. Passed as `$runner` variable (v3.10+).
For v3.9 or older: `ivr.getFlowRunner().<method_name>`.

#### Methods

| Method | Description |
|--------|-------------|
| `void exec(String flow, String[] params)` | Execute another flow |
| `String getModuleProperty(String module, String key)` | Get a module property value |
| `String getResult(String module)` | Get result value of a module (null = current module) |
| `void setModuleProperty(String module, String key, String value)` | Set a module property |
| `void setResult(String res)` | Set result of current module |
| `String replaceWithPropertiesAndResults(String str)` | Replace placeholders with module properties/results |

#### Placeholder Syntax (replaceWithPropertiesAndResults)

- `[moduleName]` - Replaced with the result value of the named module
- `<moduleName.propertyName>` - Replaced with a property value of the named module

Example from tutorial:
- `[input]` gets the result (DTMF input) from module named "input"
- `<input.timeout>` gets the "timeout" property from module named "input"

---

## 6. Tutorial: Creating an IVR Flow

Source: https://docs.brekeke.com/pbx/create-an-ivr-flow

### Flow Scenario

Create an IVR flow to make Brekeke PBX perform:

1. Send 180 reply to the incoming call
2. Answer the call
3. Play voice prompt asking caller to input transfer extension, then wait for input
   - If no input within DTMF timeout: play voice prompt again
   - Otherwise: go to next module
4. Transfer the call to the input user extension
5. If call answered within transfer timeout: flow ends
6. If not: go back to Step 3

### Step-by-Step

1. Create new flow named "test" from Flow Designer
2. Click [Basic] folder to show default IVR module templates
3. Drag **Response 18x** module ("18x"):
   - Response Code: 180
   - Add SDP: yes
4. Drag **Answer** module ("ans")
5. Connect "18x" -> "ans"
6. Drag **DTMF Input** module ("input"):
   - Prompt: `{inputprompt}` (voice prompt name from Voice Prompts)
   - Max DTMF Length: 10
   - Timeout: 10000 (ms)
   - Terminator DTMF: #
7. Connect "ans" -> "input"
8. Drag **Transfer** module ("xfer"):
   - Number: `[input]` (gets result from "input" module)
   - Timeout: `<input.timeout>` (gets timeout property from "input" module)
9. Connect "input" -> "xfer"
10. Drag **Disconnect** module ("end")
11. Connect "xfer" -> Succeeded -> "end"
12. Connect "xfer" -> Failed -> "input" (retry)
13. Save the flow

---

## 7. Setting Up IVR Extensions

Source: https://docs.brekeke.com/pbx/setting-up-ivr-extensions

### IVR Flow Extension Settings

| Name | Default | Description |
|------|---------|-------------|
| Extension | | Extension Number |
| Type | Flow | IVR type |
| Description | | Extension description |
| Flow Name | | Name of flow created in IVR Designer |
| Properties | | Overwrite module properties. Format: `<module>.<property>=<value>` |
| Auto Answer | yes | Whether to auto-answer. If "no", Answer module must be used. |
| Sound Files | | Upload customized sound files |

### Properties Format

```
<module_a>.<property1>=<value>
<module_a>.<property2>=<value>
<module_b>.<property1>=<value>
```

Example: For a "prompt" module named "prom", set `prom.stop_by_dtmf=yes`.

---

## 8. Key Concepts Summary

### How .bivr Files Are Structured
- ZIP archive containing JSON flow definition files
- Each file is a complete flow with modules, connections, and layout
- Files named as `flows/@flow_<url-encoded-name>.txt`

### What Modules Are Available
- **General**: Script, Background Script, Conditional Jump, Retry Counter, Reset Retry Counter, Jump to Flow, Send Email
- **Data Access**: SQL Query, SOAP, HTTP
- **IVR**: Prompt, Voice Rec (File/Voicemail/Prompt), DTMF Input, Answer, Response 18x, Call Transfer, Cancel Call Transfer, Disconnect, Reject
- **CCS**: Call Transfer from Queue, Position in Queue, Wait for Silence (AMD), Set Callback in Queue, Get/Set Call Parameters
- **UC Chatbot**: Buttons, Leave, IBM Watson, Send/Recv, Transfer, Tag
- **Custom**: Organizations can create custom module templates (e.g., `drjoy^External Integration$DTMF AmiVoice STT Input`)

### What Parameters Each Module Accepts
Parameters are module-specific and stored in the `params` dictionary. Common parameters include:
- **DTMF Input**: `prompt`, `max_dtmf_length`, `timeout`, `termdtmf`, `remove_term`, `retry`
- **Transfer**: `number`, `timeout`
- **Response 18x**: `rescode` (180/183), `bSDP` (yes/no)
- **Prompt**: `playlist`, `ignoreDTMF`
- **Voice Rec**: `file`/`user`, `timeout`, `terminateDtmf`
- **Script**: JavaScript code in the script property
- **HTTP**: URL, method, headers, body
- **SQL Query**: SQL statement, database connection name

### How Flows Connect
- Each module has a `next` array with up to 11 conditional connections
- Connections use regex patterns matched against the module's result value
- Common patterns: `^TIMEOUT$`, `^ERROR$`, `^NO_RESULT$`, `^.+$` (success), `true`/`false`
- The `start` field in the flow JSON identifies the entry-point module
- The `subs` array provides sub-module references (up to 3 per module)
- Cross-module data passing uses `[moduleName]` for results and `<module.property>` for properties

---

## Source URLs

- Main docs: https://docs.brekeke.com/
- Flow Developer's Guide: https://docs.brekeke.com/pbx/flow-developers-guide
- Flow Designer Control Buttons: https://docs.brekeke.com/pbx/control-items-flow-designer
- Default Module Templates: https://docs.brekeke.com/pbx/module-templates-flow-designer
- General Module Templates: https://docs.brekeke.com/pbx/general-module-templates-flow-designer
- Data Access Module Templates: https://docs.brekeke.com/pbx/data-access-module-templates
- IVR Module Templates: https://docs.brekeke.com/pbx/ivr-module-templates
- CCS Module Templates: https://docs.brekeke.com/pbx/ccs-module-templates
- UC Chatbot Module Templates: https://docs.brekeke.com/pbx/uc-chatbot-module-templates
- Tutorial - Flow for IVR: https://docs.brekeke.com/pbx/flow-for-ivr
- Create an IVR Flow: https://docs.brekeke.com/pbx/create-an-ivr-flow
- Setting Up IVR Extensions: https://docs.brekeke.com/pbx/setting-up-ivr-extensions
- IVR Class: https://docs.brekeke.com/pbx/ivr-class-flow
- ConnectionManager Class: https://docs.brekeke.com/pbx/connectionmanager-class-flow
- FlowRunner Class: https://docs.brekeke.com/pbx/flowrunner-class-flow
- Sample Flows: https://docs.brekeke.com/pbx/sample-flows-flow-designer
