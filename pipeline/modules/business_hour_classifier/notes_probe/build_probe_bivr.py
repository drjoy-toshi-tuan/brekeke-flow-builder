"""Build a tiny probe .bivr that calls Notes plugin candidates and logs results.

The .bivr contains 1 flow with 1 module:
- @General$Script "notes_api_probe" → embeds probe_script.js
- jumps: ^probe_done$ → @IVR$Disconnect

Run by:
1. Brekeke 上で Note "test_holidays" を新規作成し、test_holidays_note.txt の中身をペースト
2. この probe .bivr を import
3. 着信を 1 回受けて (or Brekeke のテスト発信機能で) フローを通す
4. Brekeke 側のログから [probe XX] OK / EXCEPTION 行を回収

Output: ./NotesAPIProbe.bivr
"""
import json
import zipfile
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent

FLOW_NAME = "テスト$NotesAPIProbe"

def main():
    script = (HERE / "probe_script.js").read_text(encoding="utf-8")
    script_crlf = script.replace("\r\n", "\n").replace("\n", "\r\n")

    probe_module = {
        "name": "notes_api_probe",
        "type": "@General$Script",
        "matchingmethod": 1,
        "description": "Probe Brekeke Notes plugin from Nashorn JS",
        "layout": {"x": 200, "y": 200},
        "params": {"script": script_crlf},
        "jumps": [],
        "next": "切断",
        "subs": [],
    }

    disconnect_module = {
        "name": "切断",
        "type": "@IVR$Disconnect",
        "matchingmethod": 1,
        "description": "終話",
        "layout": {"x": 200, "y": 400},
        "params": {},
        "jumps": [],
        "next": "",
        "subs": [],
    }

    flow = {
        "name": FLOW_NAME,
        "desc": "Brekeke Notes plugin の Script モジュールからの呼び出し可否を確認する probe",
        "start": "notes_api_probe",
        "modules": {
            "notes_api_probe": probe_module,
            "切断": disconnect_module,
        },
        "layout": {"width": 800, "height": 600},
        "resultValue": "",
        "postCallAction": "",
    }

    out = HERE / "NotesAPIProbe.bivr"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(FLOW_NAME, safe="") + ".txt"
        zf.writestr(fname, json.dumps(flow, ensure_ascii=False, separators=(",", ":")))
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    print(f"   flow file inside zip: {fname}")

if __name__ == "__main__":
    main()
