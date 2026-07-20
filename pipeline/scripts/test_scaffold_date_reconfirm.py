# -*- coding: utf-8 -*-
"""test_scaffold_date_reconfirm.py — 決定論 date 経路の Re-confirmation 復唱ガード（#296）。

背景（#296）: reservationDate の date script 経路は echo_back=true だと従来 OpenAI 経路へ
退避していた。#296 で「date script 成功 → Re-confirmation node data（nodeName=正規化script・
dateReadingMode=Seireki/skipReadHour=Yes）→ はい/いいえ STT → 認定 yes_no_classifier」の
復唱チェーンを決定論のまま生成するようにした（OpenAI ゼロ維持）。

本テストは最小合成 spec（reservationDate hearing・output_format=datetime）で機序をピン留めする:
  Test 1: echo_back=true で予約日ステップに Re-confirmation node data が生成される
  Test 2: その nodeName が日付正規化 script・dateReadingMode=Seireki・skipReadHour=Yes
  Test 3: 予約日ステップに generate_by_OpenAI が生成されない（完全決定論）
  Test 4: echo_back=false では Re-confirmation 復唱チェーンが出ない（差分の局所性）

stdlib のみ・standalone 実行:
  python scripts/test_scaffold_date_reconfirm.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scaffold_generator import generate_scaffold_v2  # noqa: E402

RECONF_TYPE = "Re-confirmation node data"
OPENAI_TYPE = "generate_by_OpenAI"


def _spec(echo_back: bool) -> dict:
    return {
        "basic_info": {
            "facility_name": "テスト",
            "group_name": "テスト$予約日",
            "flow_name": "テスト$予約日",
        },
        "flow_structure": {
            "type": "standalone",
            "flows": [{"name": "テスト$予約日", "role": "main"}],
            "subflows": [],
        },
        "context_fields": [{"context_name": "reservationDate", "display_type": "TEXT"}],
        "termination_patterns": [{
            "name": "END_完了", "condition": "完了",
            "tts_announcement": "ありがとうございました",
            "status": "1", "sms_flag": "0",
            "completion_flag_name": "完了フラグ_完了",
        }],
        "hearing_items": [{
            "name": "予約日", "stt_type": "AmiVoice_STT", "retry_count": 3,
            "echo_back": echo_back, "save_to": "reservationDate",
            "output_format": "datetime",
        }],
        "scenario_flow": [
            {"step": "冒頭_アナウンス", "type": "announcement", "next": "予約日"},
            {"step": "予約日", "type": "hearing", "output_format": "datetime",
             "save_to": "reservationDate", "next": "END_完了"},
            {"step": "END_完了", "type": "termination"},
        ],
    }


def _modules(echo_back: bool) -> dict:
    return generate_scaffold_v2(_spec(echo_back), stem="テスト")["modules"]


def run():
    results = []
    m = _modules(True)

    # ── Test 1: 予約日ステップに Re-confirmation node data が生成される ──
    reconf = [n for n, mm in m.items()
              if RECONF_TYPE in mm.get("type", "") and "予約日" in n]
    ok1 = len(reconf) == 1
    print(f"[Test 1] 予約日 Re-confirmation module = {reconf} -> {'PASS' if ok1 else 'FAIL'}")
    results.append(ok1)

    # ── Test 2: nodeName=正規化script・dateReadingMode=Seireki・skipReadHour=Yes ──
    ok2 = False
    if reconf:
        p = m[reconf[0]].get("params", {})
        node = p.get("nodeName", "")
        ok2 = ("日付正規化" in node
               and p.get("dateReadingMode") == "Seireki"
               and p.get("skipReadHour") == "Yes")
        print(f"[Test 2] nodeName={node!r} dateReadingMode={p.get('dateReadingMode')!r} "
              f"skipReadHour={p.get('skipReadHour')!r} -> {'PASS' if ok2 else 'FAIL'}")
    else:
        print("[Test 2] Re-confirmation 不在のため判定不能 -> FAIL")
    results.append(ok2)

    # ── Test 3: 予約日ステップに OpenAI が生成されない（完全決定論）──
    oa = [n for n, mm in m.items()
          if OPENAI_TYPE in mm.get("type", "") and "予約日" in n]
    ok3 = not oa
    print(f"[Test 3] 予約日 OpenAI module = {oa or 'なし'} -> {'PASS' if ok3 else 'FAIL'}")
    results.append(ok3)

    # ── Test 4: echo_back=false では Re-confirmation 復唱チェーンが出ない ──
    m0 = _modules(False)
    reconf0 = [n for n, mm in m0.items()
               if RECONF_TYPE in mm.get("type", "") and "予約日" in n]
    ok4 = not reconf0
    print(f"[Test 4] echo_back=false の 予約日 Re-confirmation = {reconf0 or 'なし'} "
          f"-> {'PASS' if ok4 else 'FAIL'}")
    results.append(ok4)

    npass = sum(1 for r in results if r)
    print("-" * 60)
    print(f"{npass}/{len(results)} PASS")
    return npass == len(results)


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    sys.exit(0 if run() else 1)
