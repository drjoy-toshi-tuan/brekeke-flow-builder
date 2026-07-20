#!/usr/bin/env python3
"""
TTS 発話確認用 bivr 生成ツール (gen_tts_preview_bivr.py)

各 STT/DTMF-AmiVoice ノードを「inject + $ivr.play() で直接発話」するスクリプトに置換する。
グラフ構造は変更しない（読み返し TTS ノードの挿入不要）。

  [Bot TTS 発話]
  → [STT スタブ Script: 固定テキスト inject + $ivr.play() で発話 + save2db]
  → [downstream: 正規化・分類・context保存… そのまま動く]

$ivr.play("{tts_g:" + val + "}") を Script 内で呼ぶことで、
「ユーザーが言ったことを IVR が読み上げる」を実現する。
DOB Re-confirmation / Phone Normalization と同じ仕組みを利用。

properties ファイル不要。グラフ変更なし。
P7 連結テスト bivr (stub_stt_connection.py) とは別ファイル（tts_preview_*.bivr）。

Usage:
    python3 tools/gen_tts_preview_bivr.py \\
        --bivr  output/scenarios/{施設}_{flow}/{施設}_{flow}.bivr \\
        --cases connection_test/cases/{施設}_{flow}.json \\
        [--out  output/scenarios/{施設}_{flow}/tts_preview_{施設}_{flow}.bivr] \\
        [--tag  TTS_]
"""

import argparse
import copy
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── 定数 ──────────────────────────────────────────────────────────────────────

STT_TYPES = (
    "drjoy^AmiVoice$Speech to Text",
    "drjoy^External Integration$DTMF AmiVoice STT Input",
)
DTMF_TYPE   = "drjoy^External Integration$DTMF AmiVoice STT Input"
JUMP_TYPE   = "drjoy^Custom Module$Custom Jump to Flow"
SCRIPT_TYPE = "@General$Script"
TTS_TYPE    = "drjoy^Text To Speech$Text to speech"

TC_CTX    = "__tc_id"
SELECTOR_NAME = "__tts_セレクタ"
SAVER_NAME    = "__tts_保存tc"
TAG_DEFAULT   = "TTS_"

ENTRY_PREFIX = "flows/@flow_"
ENTRY_SUFFIX = ".txt"
FILENAME_MAX = 255


# ── ユーティリティ（stub_stt_connection.py と共通） ───────────────────────────

def short(n): return n.split("$")[-1] if n else n
def group_of(n): return n.split("$")[0] if "$" in n else ""
def fn_bytes(name): return len((ENTRY_PREFIX + quote(name, safe="") + ENTRY_SUFFIX).encode("utf-8"))
def empty_next(): return {"condition": "", "label": "", "nextModuleName": ""}
def empty_subs(): return [{"moduleName": "", "label": ""} for _ in range(3)]


def pad_next(slots):
    s = list(slots)
    while len(s) < 10:
        s.append(empty_next())
    return s


def fit_base(group, tag, base, used):
    def ok(c): return fn_bytes(group + "$" + c) <= FILENAME_MAX
    if not ok(tag):
        raise SystemExit(f"ERROR: グループ名が長すぎます: {group}")
    cand = tag + base
    if ok(cand) and cand not in used:
        return cand
    k = len(base)
    while k > 0 and not ok(tag + base[:k]):
        k -= 1
    cand = tag + base[:k]
    if cand not in used:
        return cand
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


def detect_group(flows):
    gs = {group_of(d.get("name", "")) for d in flows}
    gs.discard("")
    if len(gs) != 1:
        raise SystemExit(f"ERROR: グループ名を一意に検出できません: {sorted(gs)}")
    return gs.pop()


def detect_entry(flows):
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
    order = sorted(flows, key=lambda d: 0 if short(d.get("name", "")) == entry_short else 1)
    for d in order:
        for m in d.get("modules", {}).values():
            if m.get("type") == DTMF_TYPE:
                return copy.deepcopy(m)
    raise SystemExit("ERROR: DTMF モジュールが見つかりません")


def make_script_module(name, script, layout, next_slots, desc=""):
    return {
        "name": name, "type": SCRIPT_TYPE, "matchingmethod": 1, "description": desc,
        "layout": layout, "params": {"script": script},
        "next": pad_next(next_slots), "subs": empty_subs(),
    }


def save_ctx_of(node, mods):
    """元 STT ノードの save2db サブから (contextName, displayType) を取得。"""
    for s in node.get("subs", []):
        sm = mods.get(s.get("moduleName", ""))
        if sm and sm.get("type", "").endswith("save2db"):
            pr = sm.get("params", {})
            cn = pr.get("contextName", "")
            if cn:
                return cn, (pr.get("contextDisplayType", "TEXT") or "TEXT")
    return "", "TEXT"


# ── スタブ スクリプト生成 ─────────────────────────────────────────────────────

def stub_script(node, akey, tbl, defseq, ctx_name="", ctx_dt="TEXT"):
    """P7 フルロジック（save2db・utterance DB）+ $ivr.play() で注入テキストを発話。

    グラフ変更不要・properties 不要。
    Script 内で $ivr.play("{tts_g:" + val + "}") を呼ぶことで
    「ユーザーが言ったこと」を IVR が読み上げる。
    """
    L = [
        f"// [TTS-PREVIEW-STUB] {node}",
        f"var TBL = {json.dumps(tbl, ensure_ascii=False)};",
        f"var DEF = {json.dumps(defseq, ensure_ascii=False)};",
        f'var tc = $ivr.getObject("{TC_CTX}"); tc = (tc==null)?"":String(tc);',
        "var seq = TBL[tc]; if (!seq) { seq = DEF; }",
        f'var nkey = "__n_{akey}";',
        "var nv = $ivr.getObject(nkey);",
        'var n = parseInt((nv==null?"0":String(nv)),10); if (isNaN(n)) { n = 0; }',
        "var val = (n < seq.length) ? seq[n] : seq[seq.length-1];",
        "$ivr.setObject(nkey, String(n+1));",
        f'$runner.getLogger().info("[TTS-PREVIEW] node={node} tc="+tc+" val="+val);',
        "",
        "// ▼ 注入テキストを TTS で直接発話（グラフ変更不要）",
        'try { $ivr.play("{tts_g:" + val + "}"); }',
        'catch(e) { $runner.getLogger().warn("[TTS-PREVIEW] play failed: " + e); }',
        "",
        "// save2db（utterance DB・画面表示）",
        "try {",
        '  var _seq = $ivr.getObject("__utter_seq") ? parseInt(String($ivr.getObject("__utter_seq")), 10) : 1;',
        '  var _utt = { seq: _seq, messageType: 1, text: val, utteranceType: "MESSAGE", startMsec: 0, endMsec: 0 };',
    ]
    if ctx_name:
        L += [
            f'  var _ctx = {{ contextName: "{ctx_name}", displayType: "{ctx_dt}", value: val }};',
            f'  $runner.setObject("{ctx_name}", val);',
            '  var _ok = $ivr.exec("save2db", "save", JSON.stringify({ contextField: _ctx, utterance: _utt }));',
        ]
    else:
        L += [
            '  var _ok = $ivr.exec("save2db", "save", JSON.stringify({ utterance: _utt }));',
        ]
    L += [
        '  if (_ok) { $ivr.setObject("__utter_seq", String(_seq + 1)); }',
        "} catch(e) { $runner.getLogger().error(\"[TTS-PREVIEW save] \" + e); }",
        "",
        f'$ivr.setObject("__mr_{node}", val);',
        "$runner.setResult(val);",
    ]
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
        '$runner.getLogger().info("[TTS-PREVIEW] selected tc="+id);',
        "$runner.setResult(id);",
    ]
    return "\r\n".join(L) + "\r\n"


# ── メイン ───────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="TTS 発話確認用 bivr 生成ツール")
    ap.add_argument("--bivr",       required=True, help="ソース .bivr ファイルのパス")
    ap.add_argument("--cases",      required=True, help="P7 cases JSON ファイルのパス")
    ap.add_argument("--out",        default="",    help="出力 .bivr パス（省略時: tts_preview_*.bivr）")
    ap.add_argument("--tag",        default=TAG_DEFAULT, help=f"フロー名プレフィックス（デフォルト: {TAG_DEFAULT}）")
    ap.add_argument("--entry-flow", default="",    help="エントリーフロー短名（省略時: 自動検出）")
    args = ap.parse_args()

    src = Path(args.bivr)
    out = Path(args.out) if args.out else src.parent / f"tts_preview_{src.name}"
    tag = args.tag

    if not src.exists():
        print(f"ERROR: .bivr が見つかりません: {src}", file=sys.stderr); sys.exit(1)

    cfg     = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases   = cfg.get("cases", [])
    defaults = cfg.get("defaults", {})
    meta    = cfg.get("meta", {})
    order   = defaults.get("_order", [])
    fallback = defaults.get("_fallback", ["NO_RESULT"])

    if not cases:
        cases = [{"id": "1", "dtmf": "1", "label": "デフォルト", "inject": {}}]

    def tbl_for(node):
        return {c["dtmf"]: c["inject"][node] for c in cases if node in c.get("inject", {})}

    def def_for(node):
        for kw in order:
            if kw in node and kw in defaults:
                return defaults[kw]
        return fallback

    _src_bytes = src.read_bytes()
    with zipfile.ZipFile(io.BytesIO(_src_bytes)) as z:
        entries = [(n, json.loads(z.read(n).decode("utf-8"))) for n in z.namelist()]
    flows = [d for _, d in entries]

    group = detect_group(flows)
    flow_shorts = {short(d.get("name", "")) for d in flows}
    meta_entry  = meta.get("entry_flow", "")

    if args.entry_flow:
        entry_flow = args.entry_flow
    elif meta_entry and meta_entry in flow_shorts:
        entry_flow = meta_entry
    else:
        if meta_entry:
            print(f"WARN: meta.entry_flow '{meta_entry}' がこの bivr に存在しません → 自動検出", file=sys.stderr)
        entry_flow = detect_entry(flows)

    rename_map     = build_rename_map(flows, group, tag)
    entry_old      = group + "$" + entry_flow
    entry_new_short = short(rename_map.get(entry_old, entry_old))

    print(f"Source : {src}")
    print(f"Target : {out}")
    print(f"Group  : {group}  Entry: {entry_flow} -> {entry_new_short}  Cases: {len(cases)}\n")

    stub_log, sel_added, akey_i = [], False, 0

    # flows は後続ループで in-place 書き換えされるため、先に DTMF テンプレを取得しておく
    dtmf_template = find_dtmf_template(flows, entry_flow)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for name, data in entries:
            fl   = short(data.get("name", ""))
            mods = data.get("modules", {})
            sel_src = copy.deepcopy(dtmf_template) if fl == entry_flow else None

            for mn, m in list(mods.items()):
                if m.get("type", "") in STT_TYPES and not mn.startswith("__"):
                    akey_i += 1
                    cn, cdt = save_ctx_of(m, mods)
                    m["type"] = SCRIPT_TYPE
                    m["matchingmethod"] = 1
                    m["params"] = {
                        "script": stub_script(mn, f"k{akey_i}", tbl_for(mn), def_for(mn), cn, cdt)
                    }
                    stub_log.append((fl, mn, "case" if tbl_for(mn) else "DEF"))

            if fl == entry_flow:
                if SELECTOR_NAME in mods and data.get("start") == SELECTOR_NAME:
                    sel_added = True
                else:
                    orig_start = data["start"]
                    sel = sel_src
                    sel["name"], sel["matchingmethod"] = SELECTOR_NAME, 1
                    sel["params"]["max_dtmf_length"] = "2"
                    sel["params"]["prompt"] = (
                        "{tts_g:TTS確認モードです。テストケースの番号を入力し、シャープを押してください。}"
                    )
                    sel["params"]["prompt_retry"] = ""
                    sel["next"] = pad_next([
                        {"condition": "^.*$", "label": "→保存", "nextModuleName": SAVER_NAME}
                    ])
                    sel["subs"] = empty_subs()
                    sel["layout"] = {"x": 40, "y": 40}
                    mods[SELECTOR_NAME] = sel
                    mods[SAVER_NAME] = make_script_module(
                        SAVER_NAME, saver_script(), {"x": 40, "y": 160},
                        [{"condition": "^.*$", "label": "→開始", "nextModuleName": orig_start}],
                        "tc_id保存→本来のstartへ",
                    )
                    data["start"] = SELECTOR_NAME
                    sel_added = True

            text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
            new_text = text
            for old in sorted(rename_map, key=len, reverse=True):
                new_text = new_text.replace(old, rename_map[old])
            new_name = json.loads(new_text).get("name", "")
            zout.writestr(
                ENTRY_PREFIX + quote(new_name, safe="") + ENTRY_SUFFIX,
                new_text.encode("utf-8"),
            )

    print(f"[SELECTOR] {'OK' if sel_added else '!! entry フロー未検出'}")
    print(f"[STUB]     {len(stub_log)} STT をスタブ化（inject + $ivr.play() で直接発話）")
    for fl, mn, kind in stub_log:
        print(f"           {fl} : {mn}  ({kind})")
    print(f"\nOK: {out}")


if __name__ == "__main__":
    main()
