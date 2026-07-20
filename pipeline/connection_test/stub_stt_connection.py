#!/usr/bin/env python3
"""連結テスト (Pattern 7) STTスタブ生成ツール — 一般化版。

指定した本番 .bivr の全 STT ノードを @General$Script スタブに置換し、本番フローを実機(電話)で
ハンズフリーに流せる形にする。正規化・配線・API連携を「STT認識」から切り離して検証する連結
(統合)テスト用。詳細仕様: REQUIREMENTS.md / 設計経緯: memory project_pattern_7_connection_test.md

使い方:
  python connection_test/stub_stt_connection.py \
      --bivr <落としてきた本番.bivr> \
      --cases connection_test/cases/<施設>_<flow>.json \
      [--facility <施設略称>] [--entry-flow <フロー短名>] [--out <出力.bivr>]

命名規則 (本番非衝突):
  グループ名は落としてきたまま温存し、シナリオ名(=フロー名)の先頭に「連結テスト_」を挿入する。
    例: ふ）福岡大学病院$Main｜診療 -> ふ）福岡大学病院$連結テスト_Main｜診療
  jump (Custom Jump to Flow の params.flowname) も同じ変換で追従。グループは自動検出。

機構 (2026-06-08 福岡大学病院 で v0/v1/v2 実機実証済):
  - STT -> @General$Script (setResult)。next/subs/matchingmethod=1 温存 -> 下流の正規化・CMR・終話はそのまま。
  - 冒頭に DTMF ケースセレクタを前置 -> $ivr.setObject("__tc_id", id)。
  - スタブ: $ivr.getObject("__tc_id")=tc、per-node カウンタ($ivr.get/setObject) で seq[min(n,len-1)]。
    値は TBL[tc] (case別 inject) 無ければ DEF (node既定 defaults) を使用。
    ※ 状態は $ivr.setObject/getObject (per-call 実証)。getSystemVariableValue+save2db は ad-hoc context を
      ラウンドトリップしないので使わない。
  - 採点は通話後のチェックポイントトレースを cases の expect と突合 (marker: [STT-STUB] ...)。
"""
import argparse, json, re, zipfile, copy, sys, io, hashlib, datetime
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
from urllib.parse import quote

TAG_DEFAULT = "T_"          # テスト印＋本番衝突回避の短縮プレフィックス（本番と同一グループに同居）
FILENAME_MAX = 255          # bivr zip エントリ名（URLエンコード後）のバイト上限
ENTRY_PREFIX, ENTRY_SUFFIX = "flows/@flow_", ".txt"
STT_TYPES = ("drjoy^AmiVoice$Speech to Text", "drjoy^External Integration$DTMF AmiVoice STT Input")
DTMF_TYPE = "drjoy^External Integration$DTMF AmiVoice STT Input"
JUMP_TYPE = "drjoy^Custom Module$Custom Jump to Flow"
SCRIPT_TYPE = "@General$Script"
TTS_TYPE = "drjoy^Text To Speech$Text to speech"
SELECTOR_NAME, SAVER_NAME, TC_CTX = "__テストセレクタ", "__保存tc", "__tc_id"
INCOMING_CLASSIFIER_TYPE = "drjoy^Incoming$incoming-classifier"
# --skip-tts: ネイティブモジュールを @General$Script で置換する型リスト。
# 元の params は保持し script キーを追加（$runner.getProperty() が元 params を読める）。
RETRY_COUNTER_TYPE = "drjoy^Text To Speech$Speech Retry Counter"
DOB_RECONFIRM_TYPE = "drjoy^TS Custom Module$DOB Re-confirmation"
PHONE_NORM_TYPE = "drjoy^TS Custom Module$Phone Normalization"
# incoming-classifier(着信電話番号分類)は実ANIを読み $ivr.setObject("telephoneNumber") では
# 上書き不可（厚木P7実機で確認）。よって STT と同様にモジュール出力をスタブ(@General$Script)し、
# ケース別に種別(固定/携帯/非通知/海外…)を setResult する。next(分岐条件)は温存。
# ケースが分類器ノードを inject しない場合の既定（テストは多くが携帯回線なので携帯に寄せる）。
CLASSIFIER_DEFAULT = ["携帯"]


def short(n): return n.split("$")[-1] if n else n
def group_of(n): return n.split("$")[0] if "$" in n else ""
def empty_next(): return {"condition": "", "label": "", "nextModuleName": ""}
def empty_subs(): return [{"moduleName": "", "label": ""} for _ in range(3)]
def pad_next(slots):
    s = list(slots)
    while len(s) < 10: s.append(empty_next())
    return s


def fn_bytes(name):
    """そのフロー名で bivr に書く zip エントリ名のバイト長。"""
    return len((ENTRY_PREFIX + quote(name, safe="") + ENTRY_SUFFIX).encode("utf-8"))


def fit_base(group, tag, base, used):
    """group$tag+base のファイル名が FILENAME_MAX 以内に収まるよう base を先頭から残して短縮。
    255B 制約は「足す」プレフィックスでは超えうるので、ベース名を budget から逆算して削る。
    先頭文字を残す＝内容ヒントは保持。短縮で衝突したら連番で一意化（テスト名は使い捨て前提）。"""
    def ok(cand):
        return fn_bytes(group + "$" + cand) <= FILENAME_MAX
    # グループ名自体が予算超 = base を空にしても収まらない → in-place 不能（本番も存在しえない長さ）
    if not ok(tag):
        raise SystemExit(
            f"ERROR: グループ名が長すぎて tag '{tag}' だけで 255B 超過 "
            f"(group$tag={fn_bytes(group + '$' + tag)}B)。同一グループ内テストは不能。"
            f"\n  → グループ名の短縮（デプロイ層の判断）が必要。本番シナリオ自体もこの長さでは 255B 制約に抵触します。")
    cand = tag + base
    if ok(cand) and cand not in used:
        return cand
    # base を先頭から詰める
    k = len(base)
    while k > 0 and not ok(tag + base[:k]):
        k -= 1
    cand = tag + base[:k]
    if cand not in used:
        return cand
    # 衝突 → 連番。末尾に数字を入れる余地を作るため必要なら更に1字削る
    i = 1
    while True:
        suff = str(i)
        kk = k
        while kk > 0 and not ok(tag + base[:kk] + suff):
            kk -= 1
        c2 = tag + base[:kk] + suff
        if c2 not in used:
            return c2
        i += 1


def build_rename_map(flows, group, tag):
    """{旧フロー名(group$base): 新フロー名(group$tag+短縮base)} を作る。
    長い base から処理して短縮枠を安定させ、衝突は連番で解消。
    base が既に tag で始まる場合（再スタブ時）は既存 tag を剥がしてから付け直す（二重 tag 防止）。"""
    used, m = set(), {}
    for d in sorted(flows, key=lambda d: len(short(d.get("name", ""))), reverse=True):
        orig_base = short(d.get("name", ""))
        base = orig_base[len(tag):] if orig_base.startswith(tag) else orig_base
        old = group + "$" + orig_base
        if old in m:
            continue
        new_base = fit_base(group, tag, base, used)
        used.add(new_base)
        m[old] = group + "$" + new_base
    return m


def save_ctx_of(node, mods):
    """元 STT/DTMF ノードの save2db サブ（subs 参照先）から (contextName, displayType) を取得。
    contextName が空（= 下流の分類器が保存する hearing）または save2db サブが無ければ ("", "TEXT")。
    collect_only 聴取（受診施設名称聴取/到着時間/お問い合わせ内容/氏名聴取 等）は分類器を通らず
    save2db サブが唯一の保存経路なので、ここで context 名を拾ってスタブに自前保存させる。"""
    for s in node.get("subs", []):
        sm = mods.get(s.get("moduleName", ""))
        if sm and sm.get("type", "").endswith("save2db"):
            pr = sm.get("params", {})
            cn = pr.get("contextName", "")
            if cn:
                return cn, (pr.get("contextDisplayType", "TEXT") or "TEXT")
    return "", "TEXT"


def stub_script(node, akey, tbl, defseq, ctx_name="", ctx_dt="TEXT"):
    L = [
        f"// [STT-STUB] {node} : attempt-aware data-driven injection (TBL=case別 / DEF=既定)",
        f"var TBL = {json.dumps(tbl, ensure_ascii=False)};",
        f"var DEF = {json.dumps(defseq, ensure_ascii=False)};",
        f'var tc = $ivr.getObject("{TC_CTX}"); tc = (tc==null)?"":String(tc);',
        "var seq = TBL[tc]; if (!seq) { seq = DEF; }",
        f'var nkey = "__n_{akey}";',
        "var nv = $ivr.getObject(nkey);",
        "var n = parseInt((nv==null?\"0\":String(nv)),10); if (isNaN(n)) { n = 0; }",
        "var val = (n < seq.length) ? seq[n] : seq[seq.length-1];",
        "$ivr.setObject(nkey, String(n+1));",
        f'$runner.getLogger().info("[STT-STUB] node={node} tc="+tc+" n="+n+" inject="+val);',
    ]
    # @General$Script は subs の save2db を実行しない。
    # 実機 save2db サブフローと同じ形式（contextField + utterance を1回の save2db call）で保存する。
    # utteranceType: "MESSAGE"（実機に合わせる）、seq は call スコープの __utter_seq を使用。
    L += [
        '// [STT-STUB save] utterance + contextField を実機 save2db と同形式で保存',
        'try {',
        '  var _seq = $ivr.getObject("__utter_seq") ? parseInt(String($ivr.getObject("__utter_seq")), 10) : 1;',
        '  var _utt = { seq: _seq, messageType: 1, text: val, utteranceType: "MESSAGE", startMsec: 0, endMsec: 0 };',
    ]
    if ctx_name:
        L += [
            f'  var _ctx = (val != null && String(val) !== "") ? {{ contextName: "{ctx_name}", displayType: "{ctx_dt}", value: val }} : null;',
            f'  if (val != null && String(val) !== "") {{ $runner.setObject("{ctx_name}", val); }}',
        ]
    else:
        L += ['  var _ctx = null;']
    L += [
        '  var _payload = _ctx ? { contextField: _ctx, utterance: _utt } : { utterance: _utt };',
        '  var _ok = $ivr.exec("save2db", "save", JSON.stringify(_payload));',
        '  if (_ok) { $ivr.setObject("__utter_seq", String(_seq + 1)); }',
        f'  $runner.getLogger().info("[STT-STUB save] ok="+_ok+" seq="+_seq+" val="+val);',
        '} catch (e) { $runner.getLogger().error("[STT-STUB save] " + e); }',
    ]
    # 注入値をミラー object（__mr_<ノード名>）へ保存。後段の DOB/Phone（inline-native 変換）が
    # 「そのモジュールの処理結果」として #data# 置換に使う（@General$Script の結果は
    # getModuleResult で受け取れないため object 経由で渡す）。
    L += [f'$ivr.setObject("__mr_{node}", val);']
    # setResult は必ず最後（Brekeke では setResult がスクリプトを終了させる）
    L += ["$runner.setResult(val);"]
    return "\r\n".join(L) + "\r\n"


def saver_script():
    L = [
        f'var r = $runner.getModuleResult("{SELECTOR_NAME}");',
        'var id = "";',
        'if (r && typeof r === "object" && r.text) { id = String(r.text); }',
        "else if (r != null) { id = String(r); }",
        'id = id.replace(/[^0-9]/g, "");',
        'if (id === "") { id = "1"; }',
        f'$ivr.setObject("{TC_CTX}", id);',
        # __skip_tts を設定: DOB Re-confirmation / Phone Normalization 等のネイティブモジュールが
        # $ivr.play() をスキップしつつ utterance DB 保存（画面表示）を維持するための合図。
        '$ivr.setObject("__skip_tts", "1");',
        '$runner.getLogger().info("[STT-STUB] selected tc="+id);',
        "$runner.setResult(id);",
    ]
    return "\r\n".join(L) + "\r\n"


def skip_tts_script(node):
    """TTS音声再生をスキップし、テキストをログ出力・DB保存のみ行うスクリプト。
    $runner.getProperty("prompt") でプロパティから発話テキストを取得し、
    テンプレート変数展開 → ログ出力 → utterance DB保存 → setResult("OK")。
    $ivr.play() を呼ばないため即座に next へ進む。
    """
    L = [
        f"// [TTS-SKIP] {node} : 音声再生スキップ。テキストをログ・DB保存のみ。",
        'var prompt = $runner.getProperty("prompt");',
        'if (!prompt) { prompt = ""; }',
        'try { prompt = $ivr.exec("system-variable", "replaceTemplateVariables", prompt); } catch(e) {}',
        'var content = "";',
        'try { content = $ivr.exec("tts-prompt", "extractTaggedContent", JSON.stringify({ prompt: prompt, stripTags: true })); } catch(e) { content = prompt; }',
        '$runner.getLogger().info("[TTS-SKIP] ' + node + ' : " + content);',
        'try {',
        '  var seqNumber = $ivr.getObject("__utter_seq") ? parseInt(String($ivr.getObject("__utter_seq")), 10) : 1;',
        '  var utterance = { seq: seqNumber, messageType: 0, text: content, utteranceType: "MESSAGE", startMsec: 0, endMsec: 0 };',
        '  var ok = $ivr.exec("save2db", "save", JSON.stringify({ utterance: utterance }));',
        '  if (ok) { $ivr.setObject("__utter_seq", String(seqNumber + 1)); }',
        '} catch (e) { $runner.getLogger().error("[TTS-SKIP] save failed: " + e); }',
        '$runner.setResult("OK");',
    ]
    return "\r\n".join(L) + "\r\n"


def skip_retry_counter_script(node, key, params=None):
    """Speech Retry Counter を @General$Script へ変換。
    params から prompt_true / prompt_false / retry_count を取り出して
    スクリプト本文へ直接埋め込む（[TTS-SKIP-NATIVE] テンプレート）。
    カウンタ __rc_{key} で true/false を判定し utterance DB にテキスト保存。
    params が None の場合はデフォルト文言を使用。"""
    if params is None:
        params = {}
    p_true  = params.get("prompt_true",  "{tts_g:申し訳ございません。うまく聞き取りができませんでした。}")
    p_false = params.get("prompt_false", "")
    max_retry = params.get("retry_count", "2")
    # JSON 文字列リテラルとして埋め込む
    p_true_js  = json.dumps(str(p_true),  ensure_ascii=False)
    p_false_js = json.dumps(str(p_false), ensure_ascii=False)
    L = [
        f"// [TTS-SKIP-NATIVE] {node} : Speech Retry Counter (embedded)",
        f"var _pTrue  = {p_true_js}  || \"\";",
        f"var _pFalse = {p_false_js} || \"\";",
        f'var _maxRetry = parseInt(String({json.dumps(str(max_retry))} || "3"), 10);',
        'if (isNaN(_maxRetry) || _maxRetry <= 0) { _maxRetry = 3; }',
        f'var _ckey = "__rc_{key}";',
        'var _cnt = parseInt(String($ivr.getObject(_ckey) || "0"), 10);',
        'if (isNaN(_cnt)) { _cnt = 0; }',
        '_cnt++;',
        '$ivr.setObject(_ckey, String(_cnt));',
        'var _result = (_cnt <= _maxRetry) ? "true" : "false";',
        'var _prompt = (_result === "false" && _pFalse) ? _pFalse : _pTrue;',
        'try { _prompt = $ivr.exec("system-variable", "replaceTemplateVariables", _prompt); } catch(e) {}',
        'var _content = "";',
        'try { _content = $ivr.exec("tts-prompt", "extractTaggedContent", JSON.stringify({ prompt: _prompt, stripTags: true })); } catch(e) { _content = _prompt; }',
        f'$runner.getLogger().info("[TTS-SKIP-NATIVE] {node} : result="+_result+" cnt="+_cnt+"/"+_maxRetry+" text="+_content);',
        'if (_content && _content.trim() !== "") {',
        '  try {',
        '    var _seqN = $ivr.getObject("__utter_seq") ? parseInt(String($ivr.getObject("__utter_seq")), 10) : 1;',
        '    var _utt = { seq: _seqN, messageType: 0, text: _content, utteranceType: "MESSAGE", startMsec: 0, endMsec: 0 };',
        '    var _ok = $ivr.exec("save2db", "save", JSON.stringify({ utterance: _utt }));',
        '    if (_ok) { $ivr.setObject("__utter_seq", String(_seqN + 1)); }',
        '  } catch(e) { $runner.getLogger().error("[TTS-SKIP-NATIVE] save failed: " + e); }',
        '}',
        '$runner.setResult(_result);',
    ]
    return "\r\n".join(L) + "\r\n"


# ==================================================================
# --inline-native: getProperty 実値埋め込みパッチモード
#   @General$Script では $runner.getProperty("...") がモジュール params を
#   読めない（native module 専用）。スタブ化済み bivr の各ノードに温存された
#   params の実値をスクリプト本文へ直接埋め込む（JSON 文字列リテラル化）。
#   さらに native の Phone Normalization / DOB Re-confirmation を公式ソース
#   埋め込みの @General$Script へ変換し、$ivr.play() は __skipPlay ガードで
#   無音化する（utterance DB 保存・setResult 分岐は温存）。
#   "." 始まりのシステムプロパティ（例 .incomingPhone）は置換しない。
# ==================================================================
DOB_RECONF_TYPE = DOB_RECONFIRM_TYPE
_CUSTOM_SRC_DIR = Path(__file__).resolve().parent.parent / "modules" / "brekeke-custom-modules" / "modules"
PHONE_NORM_JS_PATH = _CUSTOM_SRC_DIR / "phone-normalization" / "Phone Normalization.js"
DOB_RECONF_JS_PATH = _CUSTOM_SRC_DIR / "dob-reconfirmation" / "DOB Re-confirmation.js"


def inline_getproperty(script, params):
    """script 内の $runner.getProperty("key") を params[key] の実値リテラルへ置換する。
    key が params に無い場合と "." 始まり（システムプロパティ）は置換しない。"""
    def repl(m):
        key = m.group(1)
        if key.startswith(".") or key not in params:
            return m.group(0)
        return json.dumps(str(params[key]), ensure_ascii=False)
    return re.sub(r'\$runner\.getProperty\("([^"]*)"\)', repl, script)


def adapt_script_runtime(script):
    """native ソースを @General$Script 実行文脈へ適合させる。
    - $runner.get/set("seq") は @General$Script では機能しない（getProperty と同根）
      → [TTS-SKIP] スタブと同一の共有カウンタ __utter_seq（$ivr.get/setObject）へ置換。
        seq が常に 1 になる → utterance 保存が弾かれテキストが表示されない問題の修正。
    - #data# の置換元 = 入力モジュールの処理結果。入力は [STT-STUB]（@General$Script）なので
      getModuleResult ではなくスタブが保存するミラー object（__mr_<ノード名>）を優先して読む。
    - String.prototype.replaceAll は Nashorn(ES5.1) に無い → split/join へ置換。
    - parseTimestamp 依存を除去し startMsec/endMsec=0（[TTS-SKIP] と同形式・表示実証済み）。"""
    script = script.replace('$runner.get("seq")', '$ivr.getObject("__utter_seq")')
    script = re.sub(r'\$runner\.set\("seq",\s*([^)]+)\)',
                    r'$ivr.setObject("__utter_seq", String(\1))', script)
    script = script.replace(
        '$runner.getModuleResult(moduleName)',
        '($ivr.getObject("__mr_" + moduleName) || $runner.getModuleResult(moduleName))')
    script = re.sub(r'\.replaceAll\(([^,]+),\s*([^)]+)\)', r'.split(\1).join(\2)', script)
    # 引数内の () 入れ子（例 startTime.toISOString()）を1段まで許容してマッチさせる
    script = re.sub(r'\$ivr\.exec\("save2db",\s*"parseTimestamp",\s*(?:[^()]|\([^()]*\))*\)', '0', script)
    return script


def guard_plays(script, node):
    """$ivr.play(...) を __skipPlay ガードで包み無音化する（skip-tts テスト用）。
    utterance の save2db は素通し＝発話テキストの記録は維持される。"""
    if "$ivr.play(" not in script or "__skipPlay" in script:
        return script
    script = re.sub(r'(\$ivr\.play\([^;]*?\);)', r'if (!__skipPlay) { \1 }', script)
    return f"var __skipPlay = true; // [TTS-SKIP-GUARD] {node}\r\n" + script


def native_inline_script(node, mtype, params):
    """native Phone Normalization / DOB Re-confirmation の公式ソースに
    params 実値を埋め込み、play をガードした @General$Script 本文を返す。"""
    if mtype == PHONE_NORM_TYPE:
        if not PHONE_NORM_JS_PATH.exists():
            raise SystemExit(f"ERROR: Phone Normalization 公式ソースが見つかりません: {PHONE_NORM_JS_PATH}")
        body = PHONE_NORM_JS_PATH.read_text(encoding="utf-8")
        label = "Phone Normalization"
    else:
        # DOB はノード自身が openAI_prompt に値スクリプト本文を持つ場合そちらを正とする
        body = params.get("openAI_prompt", "")
        if not body:
            if not DOB_RECONF_JS_PATH.exists():
                raise SystemExit(f"ERROR: DOB Re-confirmation 公式ソースが見つかりません: {DOB_RECONF_JS_PATH}")
            body = DOB_RECONF_JS_PATH.read_text(encoding="utf-8")
        label = "DOB Re-confirmation"
    body = inline_getproperty(body, params)
    body = adapt_script_runtime(body)
    body = guard_plays(body, node)
    return f"// [NATIVE-INLINE] {node} : {label} (公式ソース埋め込み・params実値インライン)\r\n" + body


def inline_native_main(args):
    """--inline-native: スタブ化済み bivr を後処理し、getProperty 依存を実値埋め込みに直す。
    フロー名・セレクタ・STT スタブの注入表には触れない（純粋なモジュール本文パッチ）。"""
    src = Path(args.bivr)
    out = Path(args.out) if args.out else src.with_name(src.stem + "_inline.bivr")
    _src_bytes = src.read_bytes()  # read into memory first so src==out in-place write is safe
    with zipfile.ZipFile(io.BytesIO(_src_bytes)) as z:
        entries = [(n, json.loads(z.read(n).decode("utf-8"))) for n in z.namelist()]

    inl_log, conv_log = [], []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries:
            fl = short(data.get("name", ""))
            for mn, m in data.get("modules", {}).items():
                mtype = m.get("type", "")
                params = m.get("params", {})
                if mtype == SCRIPT_TYPE:
                    sc = params.get("script", "")
                    # [STT-STUB]: 注入値をミラー object（__mr_<ノード名>）へも保存する。
                    # 後段の DOB/Phone が「そのモジュールの処理結果」として #data# 置換に使う。
                    if sc.startswith("// [STT-STUB]") and "__mr_" not in sc:
                        mirror = f'$ivr.setObject("__mr_{mn}", val);\r\n$runner.setResult(val);'
                        new_sc = sc.replace("$runner.setResult(val);", mirror, 1)
                        if new_sc != sc:
                            params["script"] = sc = new_sc
                            inl_log.append((fl, mn + " (+__mr_)"))
                        continue
                    if '$runner.getProperty("' not in sc and '$runner.get("seq")' not in sc:
                        continue
                    new_sc = inline_getproperty(sc, params)
                    new_sc = adapt_script_runtime(new_sc)
                    new_sc = guard_plays(new_sc, mn)
                    if new_sc != sc:
                        params["script"] = new_sc
                        inl_log.append((fl, mn))
                elif mtype in (PHONE_NORM_TYPE, DOB_RECONF_TYPE):
                    params["script"] = native_inline_script(mn, mtype, params)
                    params.pop("openAI_prompt", None)
                    m["type"] = SCRIPT_TYPE
                    m["matchingmethod"] = 1
                    conv_log.append((fl, mn, mtype.split("$")[-1]))
            zout.writestr(name, json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))

    print(f"Source   : {src}\nTarget   : {out}\n")
    print(f"[INLINE] {len(inl_log)} スクリプトの getProperty を params 実値へ置換:")
    for fl, mn in inl_log:
        print(f"   {fl} : {mn}")
    print(f"[CONVERT] {len(conv_log)} native モジュールを @General$Script へ変換（公式ソース埋め込み）:")
    for fl, mn, t in conv_log:
        print(f"   {fl} : {mn}  ({t})")

    # 検証: params にある key の getProperty が残っていない / native Phone・DOB が残っていない /
    #       ガード無しの $ivr.play / runner.seq / replaceAll / getModuleResult 直読みが残っていない
    bad = []
    with zipfile.ZipFile(out) as z:
        for n in z.namelist():
            d = json.loads(z.read(n).decode("utf-8"))
            for mn, m in d.get("modules", {}).items():
                mtype = m.get("type", "")
                params = m.get("params", {})
                if mtype in (PHONE_NORM_TYPE, DOB_RECONF_TYPE):
                    bad.append((short(d.get("name", "")), f"native残存:{mn}"))
                if mtype == SCRIPT_TYPE:
                    sc = params.get("script", "")
                    for key in re.findall(r'\$runner\.getProperty\("([^".][^"]*)"\)', sc):
                        if key in params:
                            bad.append((short(d.get("name", "")), f"getProperty残存:{mn}:{key}"))
                    if "$ivr.play(" in sc and "__skipPlay" not in sc:
                        bad.append((short(d.get("name", "")), f"playガード無し:{mn}"))
                    if '$runner.get("seq")' in sc or '$runner.set("seq"' in sc:
                        bad.append((short(d.get("name", "")), f"runner.seq残存:{mn}"))
                    if ".replaceAll(" in sc:
                        bad.append((short(d.get("name", "")), f"replaceAll残存:{mn}"))
                    if sc.startswith("// [STT-STUB]") and "__mr_" not in sc:
                        bad.append((short(d.get("name", "")), f"__mr_ミラー無し:{mn}"))
                    if "$runner.getModuleResult(moduleName)" in sc and "__mr_" not in sc:
                        bad.append((short(d.get("name", "")), f"getModuleResult直読み:{mn}"))
    if bad:
        print(f"\n!! VERIFICATION FAILED: {bad}"); sys.exit(1)
    print(f"\nVerification OK. Output: {out}")


def make_script_module(name, script, layout, next_slots, desc=""):
    return {"name": name, "type": SCRIPT_TYPE, "matchingmethod": 1, "description": desc,
            "layout": layout, "params": {"script": script},
            "next": pad_next(next_slots), "subs": empty_subs()}


def detect_group(flows):
    gs = {group_of(d.get("name", "")) for d in flows}
    gs.discard("")
    if len(gs) != 1:
        raise SystemExit(f"ERROR: グループ名を一意に検出できません: {sorted(gs)}")
    return gs.pop()


def detect_entry(flows):
    """jump で参照されないフロー候補のうち、モジュール数が最大のものを entry とみなす。"""
    targets = set()
    for d in flows:
        for m in d.get("modules", {}).values():
            if m.get("type") == JUMP_TYPE:
                fn = m.get("params", {}).get("flowname", "")
                if "$" in fn:
                    targets.add(short(fn))
    cands = [d for d in flows if short(d.get("name", "")) not in targets]
    if not cands:
        cands = flows
    cands.sort(key=lambda d: len(d.get("modules", {})), reverse=True)
    return short(cands[0].get("name", ""))


def find_dtmf_template(flows, entry_short):
    """セレクタの雛形にする DTMF モジュールを探す (entry 優先、無ければ全フロー)。"""
    order = sorted(flows, key=lambda d: 0 if short(d.get("name", "")) == entry_short else 1)
    for d in order:
        for m in d.get("modules", {}).values():
            if m.get("type") == DTMF_TYPE:
                return copy.deepcopy(m)
    raise SystemExit("ERROR: DTMF モジュールが見つからずセレクタを作れません (--entry-flow 等を確認)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bivr", required=True)
    ap.add_argument("--cases", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--facility", default="")
    ap.add_argument("--entry-flow", default="")
    ap.add_argument("--tag", default=TAG_DEFAULT,
                    help="テスト印プレフィックス（既定 'T_'）。本番と同一グループに同居・衝突回避。長い施設はサブフロー名を自動短縮")
    ap.add_argument("--skip-tts", action="store_true",
                    help="TTS音声再生をスキップ。テキストはBrekekeログ・utterance DBに保存し即座にnextへ進む。"
                         "フロー進行・context保存の確認テスト用（架電後すぐ自動切断）。")
    ap.add_argument("--no-stub-stt", action="store_true",
                    help="STTノードをスタブ化しない。実機AmiVoiceをそのまま使う。"
                         "--skip-tts と組み合わせると TTS スキップのみ適用（実音声入力で動作確認）。")
    ap.add_argument("--inline-native", action="store_true",
                    help="スタブ化済み bivr の後処理パッチモード。@General$Script 内の "
                         "$runner.getProperty を params 実値へ置換し、native の Phone Normalization / "
                         "DOB Re-confirmation を公式ソース埋め込み Script へ変換、$ivr.play を無音ガード。"
                         "--cases 不要。フロー名・セレクタ・STT スタブの注入表には触れない。")
    args = ap.parse_args()
    tag = args.tag

    if args.inline_native:
        inline_native_main(args)
        return

    if not args.cases:
        ap.error("--cases は必須です（--inline-native モードを除く）")
    cfg = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases, defaults, meta = cfg["cases"], cfg["defaults"], cfg.get("meta", {})
    order, fallback = defaults["_order"], defaults.get("_fallback", ["NO_RESULT"])
    src = Path(args.bivr)
    out = Path(args.out) if args.out else src.with_name(src.stem + "_連結テスト.bivr")

    def tbl_for(node): return {c["dtmf"]: c["inject"][node] for c in cases if node in c.get("inject", {})}
    def def_for(node):
        for kw in order:
            if kw in node and kw in defaults: return defaults[kw]
        return fallback
    def def_for_classifier(node):
        # 分類器の既定: cases defaults にキーワード一致があればそれ、無ければ CLASSIFIER_DEFAULT(携帯)。
        # → 分類器ノードを inject しない既存ケースは従来どおり携帯ルートを通る（回帰なし）。
        for kw in order:
            if kw in node: return defaults[kw]
        return CLASSIFIER_DEFAULT

    _src_bytes = src.read_bytes()  # read into memory first so src==out in-place write is safe
    with zipfile.ZipFile(io.BytesIO(_src_bytes)) as z:
        entries = [(n, json.loads(z.read(n).decode("utf-8"))) for n in z.namelist()]
    flows = [d for _, d in entries]
    group = detect_group(flows)
    entry_flow = args.entry_flow or meta.get("entry_flow") or detect_entry(flows)
    # 再スタブ時: meta の entry_flow が tag 無し (例 M｜診療) でも source には T_M｜診療 が存在する場合を補正
    if entry_flow and not any(short(d.get("name", "")) == entry_flow for d in flows):
        tagged_ef = tag + entry_flow
        if any(short(d.get("name", "")) == tagged_ef for d in flows):
            entry_flow = tagged_ef
    # meta の entry_flow がフロー短名と完全一致しない場合 (例 「診療」 vs 実フロー「M｜診療」)、
    # 部分一致が一意ならそれを採用。決まらなければ fail-fast（セレクタ無し bivr を黙って出さない）。
    if not any(short(d.get("name", "")) == entry_flow for d in flows):
        hits = [short(d.get("name", "")) for d in flows if entry_flow in short(d.get("name", ""))]
        if len(hits) == 1:
            print(f"[ENTRY] '{entry_flow}' は完全一致するフローが無いため部分一致 '{hits[0]}' を entry に採用")
            entry_flow = hits[0]
        else:
            raise SystemExit(
                f"ERROR: entry フロー '{entry_flow}' が bivr 内に見つかりません（部分一致 {len(hits)} 件）。"
                f"\n  候補: {sorted(short(d.get('name', '')) for d in flows)}"
                f"\n  → --entry-flow で実在するフロー短名を指定してください。")
    # incoming-classifier の出力スタブは「分類器ノードを inject するケースが1件でもあるとき」だけ有効化。
    # 種別ケースが無い施設では分類器を素のまま残す（実ANI判定を変えない）。
    classifier_nodes = {mn for d in flows for mn, m in d.get("modules", {}).items()
                        if m.get("type") == INCOMING_CLASSIFIER_TYPE}
    stub_classifiers = any(node in c.get("inject", {}) for c in cases for node in classifier_nodes)
    # 旧フロー名 -> 新フロー名（同一グループ・tag付き・255B に収まるよう base 自動短縮）
    rename_map = build_rename_map(flows, group, tag)
    entry_old = group + "$" + entry_flow
    entry_new_short = short(rename_map.get(entry_old, entry_old))

    print(f"Source   : {src}\nTarget   : {out}")
    print(f"Group    : {group}  (温存) -> 同一グループ内に tag '{tag}' で同居（255B 超過分はサブフロー名を短縮）")
    print(f"Entry    : {entry_flow} -> {entry_new_short}\nCases    : {len(cases)}\n")

    stub_log, renames, sel_added, akey_i, rakey_i, clf_log, tts_skip_log, tts_patch_log = [], [], False, 0, 0, [], [], []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries:
            fl = short(data.get("name", ""))
            mods = data.get("modules", {})
            sel_src = find_dtmf_template(flows, entry_flow) if fl == entry_flow else None

            for mn, m in list(mods.items()):
                mtype = m.get("type", "")
                if mtype in STT_TYPES and not mn.startswith("__") and not args.no_stub_stt:
                    akey_i += 1
                    cn, cdt = save_ctx_of(m, mods)  # 元ノードの save2db サブから保存先 context を取得
                    m["type"] = SCRIPT_TYPE
                    m["matchingmethod"] = 1
                    m["params"] = {"script": stub_script(mn, "k%d" % akey_i, tbl_for(mn), def_for(mn), cn, cdt)}
                    stub_log.append((fl, mn, "case" if tbl_for(mn) else "DEF"))
                elif mtype == SCRIPT_TYPE and not mn.startswith("__") and not args.no_stub_stt:
                    # 再スタブ: 既存 [STT-STUB] スクリプトの TBL/DEF を新ケース表で更新
                    existing = m.get("params", {}).get("script", "")
                    if existing.startswith("// [STT-STUB]"):
                        akey_i += 1
                        nkey_m = re.search(r'var nkey = "__n_(\w+)"', existing)
                        akey_str = nkey_m.group(1) if nkey_m else "k%d" % akey_i
                        ctx_m = re.search(r'contextName: "([^"]*)"', existing)
                        ctx_name = ctx_m.group(1) if ctx_m else ""
                        ctx_dt_m = re.search(r'displayType: "([^"]*)"', existing)
                        ctx_dt = ctx_dt_m.group(1) if ctx_dt_m else "TEXT"
                        m["params"]["script"] = stub_script(mn, akey_str, tbl_for(mn), def_for(mn), ctx_name, ctx_dt)
                        stub_log.append((fl, mn, "case" if tbl_for(mn) else "DEF"))
                    elif existing.startswith("// [NATIVE-INLINE]"):
                        # NATIVE-INLINE スクリプト（DOB Re-confirmation 等）は内部で getRawResult() を
                        # 呼ぶため STT がないと RAW_INPUT:EMPTY になる。STT と同様にスタブ化する。
                        akey_i += 1
                        m["params"]["script"] = stub_script(mn, "k%d" % akey_i, tbl_for(mn), def_for(mn))
                        stub_log.append((fl, mn, "case" if tbl_for(mn) else "DEF-NATIVE"))
                    elif args.skip_tts and "$ivr.play(" in existing:
                        # スタブ対象外の素の Script が $ivr.play を呼ぶ場合の無音化。
                        # （この elif 節が Script 型を先取りするため、後段の skip_tts 節には届かない）
                        patched = guard_plays(existing, mn)
                        if patched != existing:
                            m["params"]["script"] = patched
                            tts_patch_log.append((fl, mn))
                elif args.skip_tts and mtype == TTS_TYPE and not mn.startswith("__"):
                    m["type"] = SCRIPT_TYPE
                    m["matchingmethod"] = 1
                    m["params"] = {"script": skip_tts_script(mn)}
                    tts_skip_log.append((fl, mn))
                elif args.skip_tts and mtype == RETRY_COUNTER_TYPE and not mn.startswith("__"):
                    # Speech Retry Counter: Script に置換。
                    # prompt_true/prompt_false/retry_count を埋め込んだ [TTS-SKIP-NATIVE] スクリプト生成。
                    rakey_i += 1
                    orig_params = dict(m.get("params", {}))
                    m["type"] = SCRIPT_TYPE
                    m["matchingmethod"] = 1
                    m["params"] = {"script": skip_retry_counter_script(mn, "r%d" % rakey_i, orig_params)}
                    tts_skip_log.append((fl, mn))
                elif args.skip_tts and mtype == DOB_RECONFIRM_TYPE and not mn.startswith("__"):
                    # DOB Re-confirmation: native_inline_script で公式ソース埋め込み Script 化。
                    try:
                        m["type"] = SCRIPT_TYPE
                        m["matchingmethod"] = 1
                        m["params"]["script"] = native_inline_script(mn, mtype, m["params"])
                        tts_skip_log.append((fl, mn))
                    except SystemExit:
                        tts_patch_log.append((fl, mn))
                elif args.skip_tts and mtype == PHONE_NORM_TYPE and not mn.startswith("__"):
                    # Phone Normalization: native_inline_script で公式ソース埋め込み Script 化。
                    try:
                        m["type"] = SCRIPT_TYPE
                        m["matchingmethod"] = 1
                        m["params"]["script"] = native_inline_script(mn, mtype, m["params"])
                        tts_skip_log.append((fl, mn))
                    except SystemExit:
                        tts_patch_log.append((fl, mn))
                elif args.skip_tts and mtype == SCRIPT_TYPE and not mn.startswith("__"):
                    # Retry / DOB Re-confirmation / Phone normalize 等の Script モジュールが
                    # $ivr.play() を呼んでいる場合、__skipPlay ガードで包んで TTS を無音化する
                    # （guard_plays は STT-STUB / ガード済みスクリプトには手を付けない=冪等）。
                    existing = m.get("params", {}).get("script", "")
                    if not existing.startswith("// [STT-STUB]") and "$ivr.play(" in existing:
                        patched = guard_plays(existing, mn)
                        if patched != existing:
                            m["params"]["script"] = patched
                            tts_patch_log.append((fl, mn))
                elif mtype == INCOMING_CLASSIFIER_TYPE and stub_classifiers and not mn.startswith("__"):
                    # 分類器の出力をスタブ。next(^固定$/^携帯$/^非通知$… 分岐)は温存し、
                    # setResult(種別) でケース別に分岐させる。番号→種別マッピング自体は
                    # ネイティブ部品の責務なので検証外（実回線スポットで別途確認）。
                    akey_i += 1
                    m["type"] = SCRIPT_TYPE
                    m["matchingmethod"] = 1
                    m["params"] = {"script": stub_script(mn, "c%d" % akey_i, tbl_for(mn), def_for_classifier(mn))}
                    clf_log.append((fl, mn, "case" if tbl_for(mn) else "DEF"))

            if fl == entry_flow:
                # 再スタブ: セレクタが既に存在し start が設定済みならセレクタ追加をスキップ
                if SELECTOR_NAME in mods and data.get("start") == SELECTOR_NAME:
                    sel_added = True
                else:
                    orig_start = data["start"]
                    sel = sel_src
                    sel["name"], sel["matchingmethod"] = SELECTOR_NAME, 1
                    # ケース番号の最大桁に合わせる（固定 "2" だと 100 ケース以上で選択不能）
                    sel["params"]["max_dtmf_length"] = str(max(2, max(len(str(c["dtmf"])) for c in cases)))
                    sel["params"]["prompt"] = "{tts_g:テストケースの番号を入力し、シャープを押してください。}"
                    sel["params"]["prompt_retry"] = ""
                    sel["next"] = pad_next([{"condition": "^.*$", "label": "→保存", "nextModuleName": SAVER_NAME}])
                    sel["subs"] = empty_subs()
                    sel["layout"] = {"x": 40, "y": 40}
                    mods[SELECTOR_NAME] = sel
                    mods[SAVER_NAME] = make_script_module(
                        SAVER_NAME, saver_script(), {"x": 40, "y": 160},
                        [{"condition": "^.*$", "label": "→開始", "nextModuleName": orig_start}],
                        "テストケースID(__tc_id)保存→本来のstartへ")
                    data["start"] = SELECTOR_NAME
                    sel_added = True

            text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            # フロー名・jump 参照を rename_map で一括置換（長い旧名から＝部分一致衝突を回避）
            new_text = text
            for old in sorted(rename_map, key=len, reverse=True):
                new_text = new_text.replace(old, rename_map[old])
            old_name = data.get("name", "")
            new_name = json.loads(new_text).get("name", "")
            if new_name != old_name: renames.append((old_name, new_name))
            zout.writestr(ENTRY_PREFIX + quote(new_name, safe="") + ENTRY_SUFFIX, new_text.encode("utf-8"))

        # 生成時ソース情報を zip comment に埋め込む（Brekeke import には影響しない・
        # verify_test_bivr.py が実機投入前に「どの本体から生成されたか」を突合できる）
        zout.comment = json.dumps({
            "source_file": src.name,
            "source_sha256": hashlib.sha256(_src_bytes).hexdigest(),
            "cases_file": Path(args.cases).name,
            "cases_sha256": hashlib.sha256(Path(args.cases).read_bytes()).hexdigest(),
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "generator": "stub_stt_connection.py",
            "options": {"skip_tts": bool(args.skip_tts), "no_stub_stt": bool(args.no_stub_stt), "tag": tag},
        }, ensure_ascii=False).encode("utf-8")

    new_names = set(rename_map.values())
    # inject キーの実在検証: ケース表の inject キーがスタブ化されたノード名と一致しないと
    # 黙って捨てられ defaults で完走してしまう（テストしたつもり事故）。ここで機械検出する。
    stubbed_nodes = {mn for _, mn, _ in stub_log} | {mn for _, mn, _ in clf_log}
    inject_bad, inject_warn = [], []
    if not args.no_stub_stt:
        for c in cases:
            keys = [k for k in c.get("inject", {}) if not k.startswith("_")]
            unmatched = [k for k in keys if k not in stubbed_nodes]
            if unmatched:
                inject_warn.append((c["dtmf"], unmatched))
            if keys and len(unmatched) == len(keys):
                inject_bad.append((c["dtmf"], f"inject キーが全滅（1つもノードに一致しない）: {unmatched}"))
    print("[SELECTOR]", "OK" if sel_added else "!! entry フロー未検出")
    if inject_warn:
        print(f"[INJECT] !! {len(inject_warn)} ケースに未一致 inject キー（該当ノードは defaults 動作）:")
        for dtmf, ks in inject_warn:
            print(f"   case {dtmf}: {', '.join(ks)}")
    if args.no_stub_stt:
        print(f"[STUB] STTスタブ無効 (--no-stub-stt)。実機AmiVoiceで動作。")
    else:
        print(f"[STUB] {len(stub_log)} STT ノードをスタブ ({sum(1 for x in stub_log if x[2]=='case')} case / {sum(1 for x in stub_log if x[2]=='DEF')} DEF)")
    if stub_classifiers:
        print(f"[CLASSIFIER-STUB] {len(clf_log)} incoming-classifier をスタブ "
              f"({sum(1 for x in clf_log if x[2]=='case')} case / {sum(1 for x in clf_log if x[2]=='DEF')} DEF) "
              f"— 出力をケース別 setResult、分岐(next)温存 ({', '.join(f'{fl}:{mn}' for fl, mn, _ in clf_log)})")
    elif classifier_nodes:
        print(f"[CLASSIFIER-STUB] スキップ（種別を inject するケースが無いため分類器は素のまま=実ANI判定）")
    if args.skip_tts:
        print(f"[TTS-SKIP] モジュール置換(TTS/DOB/Phone/Retry): {len(tts_skip_log)}件 / $ivr.playパッチ: {len(tts_patch_log)}件")
        print("   音声なし・テキストはログ+utterance DB保存 — 架電後フローが自動進行して即切断")
        for fl, mn in tts_skip_log:
            print(f"   [replace] {fl} : {mn}")
        for fl, mn in tts_patch_log:
            print(f"   [patch  ] {fl} : {mn}")
    print(f"[RENAME] {len(renames)} フロー -> tag '{tag}' 付与（255B 超過分はサブフロー名を短縮）")
    for o, nw in renames:
        truncated = short(nw) != (tag + short(o))
        print(f"   {short(o)} -> {short(nw)}  ({fn_bytes(nw)}B){'  ⚠短縮(内容ヒントは先頭保持)' if truncated else ''}")

    # 検証: 255B 以内 / 未スタブ STT なし / 全 jump が実在フローに解決 / entry にセレクタ
    bad = []
    if not sel_added:
        bad.append((entry_flow, "セレクタ未追加（entry フロー未検出のまま出力された）"))
    for dtmf, msg in inject_bad:
        bad.append((f"case {dtmf}", msg))
    with zipfile.ZipFile(out) as z:
        for n in z.namelist():
            d = json.loads(z.read(n).decode("utf-8"))
            nm = d.get("name", "")
            if fn_bytes(nm) > FILENAME_MAX:
                bad.append((nm, f"ファイル名 {fn_bytes(nm)}B > {FILENAME_MAX}"))
            if not nm.startswith(group + "$" + tag):
                bad.append((nm, f"tag '{tag}' 未付与"))
            for mmn, m in d.get("modules", {}).items():
                if (m.get("type", "") in STT_TYPES and not mmn.startswith("__")
                        and not args.no_stub_stt):  # --no-stub-stt では STT 温存が正
                    bad.append((nm, f"未スタブSTT残存:{mmn}"))
                fn = m.get("params", {}).get("flowname", "")
                if isinstance(fn, str) and "$" in fn:
                    stripped = fn.split("^", 1)[1] if "^" in fn else fn
                    if stripped not in new_names:
                        bad.append((nm, f"jump解決不能:{fn}"))
            if short(nm) == entry_new_short:
                if d.get("start") != SELECTOR_NAME: bad.append((nm, f"start={d.get('start')}"))
                for req in (SELECTOR_NAME, SAVER_NAME):
                    if req not in d.get("modules", {}): bad.append((nm, f"{req}欠落"))
    if bad:
        print(f"\n!! VERIFICATION FAILED: {bad}"); sys.exit(1)

    # 本体 ⇄ テストBIVR の参照整合性チェック（CMR params / next / subs / jump）。
    # 恵佑会札幌 260629: テストBIVR の CMR module1Name だけが古い状態で保存され
    # 全ケースが その他_FIXED に倒れた事故の再発防止。乖離があれば fail-fast。
    sys.path.insert(0, str(Path(__file__).parent))
    from verify_test_bivr import compare_bivr
    diffs = compare_bivr(_src_bytes, out, tag)
    if diffs:
        print(f"\n!! SOURCE-CONSISTENCY FAILED: 本体BIVRとの乖離 {len(diffs)} 件")
        for d in diffs:
            print(f"  {d}")
        sys.exit(1)
    print(f"[CONSISTENCY] 本体BIVRとの CMR/next/subs/jump 整合 OK")
    print(f"\nVerification OK. Output: {out}")


if __name__ == "__main__":
    main()
