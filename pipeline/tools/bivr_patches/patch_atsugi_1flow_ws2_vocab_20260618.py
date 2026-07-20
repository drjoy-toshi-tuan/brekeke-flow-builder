# -*- coding: utf-8 -*-
"""厚木統合CC 1flow WS2 語彙バグ修正パッチ（bivr_patches 規約）。

実行: python tools/bivr_patches/patch_atsugi_1flow_ws2_vocab_20260618.py
入力: output/scenarios/ヘルスケアクリニック厚木_統合CC_1flow/ヘルスケアクリニック厚木_統合CC_1flow.bivr
出力: 同ディレクトリ ..._ws2.bivr

差し替え対象 (WS2 A/C/D/F/G):
  checkup_intent_classifier  — FOLDINGS 番正規化/その他/そのほか/時刻 追加
  yes_no_classifier          — はあい/はぁい/はーい 追加
  checkup_menu_classifier    — 広岡/west/ウェスト/番 追加

手順:
  各 @General$Script を SCRIPT_MARKER で判別 → SOURCE_MODULE / SCOPE / MENU を抽出
  → 最新 modules/*.js を読み込み → 同じ値を再注入 → 差し替え。
"""
import io
import json
import os
import re
import sys
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCN_DIR = os.path.join(ROOT, "output", "scenarios", "ヘルスケアクリニック厚木_統合CC_1flow")
SRC_BIVR = os.path.join(SCN_DIR, "ヘルスケアクリニック厚木_統合CC_1flow.bivr")
DST_BIVR = os.path.join(SCN_DIR, "ヘルスケアクリニック厚木_統合CC_1flow_ws2.bivr")
SRC_RENKETSU = os.path.join(SCN_DIR, "連結テスト_ヘルスケアクリニック厚木_統合CC_1flow.bivr")
DST_RENKETSU = os.path.join(SCN_DIR, "連結テスト_ヘルスケアクリニック厚木_統合CC_1flow_ws2.bivr")
MODULES_DIR = os.path.join(ROOT, "modules")

# @part-id で使うマーカー文字列: スクリプト本文から判別
MARKERS = {
    "[SCRIPT-INTENT]": "checkup_intent_classifier",
    "[SCRIPT-YESNO]": "yes_no_classifier",
    "[SCRIPT-MENU]": "checkup_menu_classifier",
}

SOURCE_MODULE_RE = re.compile(r'var SOURCE_MODULE\s*=\s*"([^"]*)"')
SCOPE_RE = re.compile(r'var SCOPE\s*=\s*"([^"]*)"')
MENU_RE = re.compile(r'var MENU\s*=\s*"([^"]*)"')


def detect_part(script_text):
    for marker, part in MARKERS.items():
        if marker in script_text:
            return part
    return None


def extract_wiring(script_text, part):
    sm = SOURCE_MODULE_RE.search(script_text)
    source = sm.group(1) if sm else None
    scope = menu = None
    if part == "checkup_intent_classifier":
        m = SCOPE_RE.search(script_text)
        scope = m.group(1) if m else None
    if part == "checkup_menu_classifier":
        m = MENU_RE.search(script_text)
        menu = m.group(1) if m else None
    return source, scope, menu


def load_new_script(part, source, scope=None, menu=None):
    path = os.path.join(MODULES_DIR, part, "script.js")
    body = io.open(path, "r", encoding="utf-8").read()
    if source is not None:
        body = body.replace("__SOURCE_MODULE__", source)
    if scope is not None:
        body = body.replace("__SCOPE__", scope)
    if menu is not None:
        body = body.replace("__MENU__", menu)
    return body


def patch_modules(mods):
    patched = 0
    for mod_name, mod in mods.items():
        if mod.get("type") != "@General$Script":
            continue
        old_script = mod.get("params", {}).get("script", "")
        part = detect_part(old_script)
        if part is None:
            continue
        source, scope, menu = extract_wiring(old_script, part)
        new_script = load_new_script(part, source, scope, menu)
        # normalize to LF for comparison (json.loads gives LF; io.open universal mode gives LF)
        old_norm = old_script.replace("\r\n", "\n")
        new_norm = new_script.replace("\r\n", "\n")
        if old_norm != new_norm:
            mod["params"]["script"] = new_script
            label = "scope=" + scope if scope else ("menu=" + menu if menu else "")
            print("  [PATCH] %s (%s%s)" % (mod_name, part, (", " + label) if label else ""))
            patched += 1
        else:
            print("  [SKIP]  %s (%s) -- 変更なし" % (mod_name, part))
    return patched


def patch_bivr(src, dst):
    if not os.path.exists(src):
        print("[SKIP] 存在しない: %s" % src)
        return 0
    with zipfile.ZipFile(src, "r") as zin:
        flows = {}
        for name in zin.namelist():
            flows[name] = json.loads(zin.read(name).decode("utf-8"))
    total = 0
    for fname, flow in flows.items():
        mods = flow.get("modules")
        if not mods:
            continue
        print("\n[FLOW] %s" % flow.get("name", fname))
        total += patch_modules(mods)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for fname, flow in flows.items():
            zout.writestr(fname, json.dumps(flow, ensure_ascii=False, separators=(",", ":")))
    print("\n[DONE] %d スクリプト差し替え → %s" % (total, os.path.basename(dst)))
    return total


def main():
    total = 0
    print("=== 1flow bivr ===")
    total += patch_bivr(SRC_BIVR, DST_BIVR)
    print("\n=== 連結テスト bivr ===")
    total += patch_bivr(SRC_RENKETSU, DST_RENKETSU)
    print("\n[ALL DONE] 合計 %d スクリプト差し替え" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
