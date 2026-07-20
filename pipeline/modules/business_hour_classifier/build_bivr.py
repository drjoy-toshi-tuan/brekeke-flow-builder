"""Build BusinessHour Classifier .bivr (zip of @module_template.txt).

Run with the system Python (no pip install).
Output: ./BusinessHourClassifier.bivr
"""
import json
import zipfile
from pathlib import Path

HERE = Path(__file__).parent

def main():
    script = (HERE / "script.js").read_text(encoding="utf-8")
    # Brekeke editor stores scripts with CRLF
    script_crlf = script.replace("\r\n", "\n").replace("\n", "\r\n")

    params = [
        {
            "name": "target_datetime",
            "variable": "",
            "rule": r"^(now|<%.*%>|\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?)$",
            "comment": "",
            "label": "判定対象日時 (now / yyyy-MM-dd[ HH:mm[:ss]] / <%var%>)",
            "type": 1,
        },
        {
            "name": "reference_date",
            "variable": "",
            "rule": r"^(now|<%.*%>|\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?)$",
            "comment": "",
            "label": "過去日判定の基準日 (now=着信時刻 / yyyy-MM-dd[ HH:mm[:ss]] / <%var%>)。過去日は営業時間外",
            "type": 1,
        },
        {
            "name": "weekday_schedule",
            "variable": "",
            "rule": r"^((mon|tue|wed|thu|fri|sat|sun)=(\d{2}:\d{2}-\d{2}:\d{2}|closed))(,(mon|tue|wed|thu|fri|sat|sun)=(\d{2}:\d{2}-\d{2}:\d{2}|closed))*$",
            "comment": "",
            "label": "曜日別営業時間 (例: mon=09:00-18:00,...,sat=closed,sun=closed)",
            "type": 1,
        },
        {
            "name": "closed_dates",
            "variable": "",
            "rule": r"^$|^(\d{2}-\d{2})(,\d{2}-\d{2})*$",
            "comment": "",
            "label": "固定休 mm-dd 列 (例: 12-29,12-30,12-31,01-02,01-03)",
            "type": 1,
        },
        {
            "name": "national_holiday",
            "variable": "",
            "rule": r"^(closed|open)$",
            "comment": "",
            "label": "国民の祝日扱い (closed = 休 / open = 平日扱い)",
            "type": 1,
        },
        {
            "name": "holiday_note_name",
            "variable": "",
            "rule": r"^[A-Za-z0-9_.\-]+$",
            "comment": "",
            "label": "祝日 Brekeke Note 名 (単一 Note に多年詰める、例: drjoy.holidays)",
            "type": 1,
        },
    ]

    jumps = [
        {"condition": "^営業中$",     "comment": "", "label": "営業中"},
        {"condition": "^営業時間外$", "comment": "", "label": "営業時間外"},
        {"condition": "^定休日$",     "comment": "", "label": "定休日"},
        {"condition": "^祝日$",       "comment": "", "label": "祝日"},
        {"condition": "^固定休$",     "comment": "", "label": "固定休"},
        {"condition": "^ERROR$",      "comment": "", "label": "ERROR"},
    ]

    module = {
        "color": 15764526,
        "subs": [{"comment": "", "label": ""} for _ in range(3)],
        "isSubModify": 0,
        "iconFile": "@jump.svg",
        "jumps": jumps,
        "matchingmethod": 1,
        "isConditionModify": 1,
        "type": "Incoming$BusinessHour Classifier",
        "params": params,
        "value": script_crlf,
        "isMatchingMethodModify": 1,
        "desc": "着信日時を曜日別営業時間/固定休/祝日と照合し 6 分岐に仕分ける。",
    }

    payload = {
        "categoryList": [
            {
                "moduleList": [module],
                "name": "Incoming",
                "type": 2,
            }
        ]
    }

    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    out = HERE / "BusinessHourClassifier.bivr"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("@module_template.txt", body)
    print(f"wrote {out} ({out.stat().st_size} bytes)")

if __name__ == "__main__":
    main()
