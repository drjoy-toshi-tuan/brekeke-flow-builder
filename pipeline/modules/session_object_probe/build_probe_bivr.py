"""Build a tiny probe .bivr that tests cross-call persistence of the session object store.

モジュール JSON スキーマは実機 import 実績のある
modules/business_hour_classifier/acceptance_test/build_test_flow_bivr.py に合わせる
(next=10スロット配列 / subs=3スロット配列 / jumps フィールドなし)。

The .bivr contains 1 flow with 2 modules:
- @General$Script "session_object_probe" → embeds probe_script.js
- @IVR$Disconnect "切断"

Run by:
1. この probe .bivr を Brekeke に import
2. 1 回目の架電: 「けっかは、オーケーです」(残骸なし) を確認して切る
3. 2 回目の架電:
   - 「けっかは、オーケーです」 → ストアは per-call。rid 動的キーは無害 (シロ確定)
   - 「けっかは、エヌジーです」 → コール越境ストア実在。generator イディオムの
     flowName.rid キーが溜まり続けている = メモリリーク候補として Dev 報告
4. 詳細は Brekeke ログの [LEAK-PROBE] 行で確認 (どのキーが残っていたかまで出る)

Output: ./SessionObjectProbe.bivr
"""
import json
import zipfile
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent

FLOW_NAME = "テスト$SessionObjectProbe"


def empty_next_slot() -> dict:
    return {"condition": "", "label": "", "nextModuleName": ""}


def empty_subs() -> list:
    return [{"moduleName": "", "label": ""} for _ in range(3)]


def main():
    script = (HERE / "probe_script.js").read_text(encoding="utf-8")
    script_crlf = script.replace("\r\n", "\n").replace("\n", "\r\n")

    # probe → 切断 は catch-all 1 スロットで配線 (結果値は probe_done 固定)
    probe_next = [{"condition": "^.*$", "label": "終話", "nextModuleName": "切断"}]
    while len(probe_next) < 10:
        probe_next.append(empty_next_slot())

    probe_module = {
        "name": "session_object_probe",
        "type": "@General$Script",
        "matchingmethod": 1,
        "description": "setObject のコール越境有無を判定する probe",
        "layout": {"x": 300, "y": 100},
        "params": {"script": script_crlf},
        "next": probe_next,
        "subs": empty_subs(),
    }

    disconnect_module = {
        "name": "切断",
        "type": "@IVR$Disconnect",
        "matchingmethod": 1,
        "description": "終話",
        "layout": {"x": 300, "y": 300},
        "params": {},
        "next": [empty_next_slot() for _ in range(10)],
        "subs": empty_subs(),
    }

    flow = {
        "name": FLOW_NAME,
        "desc": "$ivr/$runner setObject がコールを跨いで残るかを 2 回架電で判定する probe",
        "start": "session_object_probe",
        "modules": {
            "session_object_probe": probe_module,
            "切断": disconnect_module,
        },
        "layout": {"width": 800, "height": 600},
        "resultValue": "",
        "postCallAction": "",
    }

    out = HERE / "SessionObjectProbe.bivr"
    body = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(FLOW_NAME, safe="") + ".txt"
        zf.writestr(fname, body)
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    print(f"   flow file inside zip: {fname}")


if __name__ == "__main__":
    main()
