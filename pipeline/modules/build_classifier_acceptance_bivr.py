# -*- coding: utf-8 -*-
"""build_classifier_acceptance_bivr.py — 健診CC 決定論分類器4部品の Pattern 6 受入テストフロー .bivr 生成。

faq_matcher / business_hour_classifier の acceptance_test/build_test_flow_bivr.py と同型
（チェイン式・1 コール内直列実行）。各部品の acceptance_test/cases.tsv（テストの正本・oracle 一致済）
を読み、各ケースを @General$Script モジュールに展開する。

入力注入: 本番 script.js の入力取得行
    var r = $runner.getModuleResult(SOURCE_MODULE);
を
    var r = "<utterance>";
にリテラル差し替えするのみ。nrm() / decide() / setResult() は本番 script.js verbatim で実行されるので、
STT・配線（getModuleResult）に依存しない「分類ロジックの決定論ユニットテスト」になる。
（in-flow の getModuleResult 配線自体は P7 連結テストで網羅済み。P6 は decide() の全ケース網羅が責務。）

checkup_menu_classifier のみ MENU 設定行
    var MENU = "__MENU__";
も cases.tsv の menu 列でリテラル差し替えする（cases.tsv に menu 列があれば自動検出）。

期待ラベルに一致（^expected$）で次ケースへ、不一致（^.*$）で対応 FAIL 終話へ。
全ケースの期待 jump が連続発火すると PASS_全件PASS（@IVR$Disconnect）に到達 = 受入確定。

対象部品 / 出力:
    yes_no_classifier        -> acceptance_test/YesNoAcceptanceTest.bivr
    checkup_intent_classifier-> acceptance_test/CheckupIntentAcceptanceTest.bivr
    checkup_course_classifier-> acceptance_test/CheckupCourseAcceptanceTest.bivr
    checkup_menu_classifier  -> acceptance_test/CheckupMenuAcceptanceTest.bivr

使い方:
    python build_classifier_acceptance_bivr.py                    # 4 部品すべて生成
    python build_classifier_acceptance_bivr.py yes_no_classifier  # 指定部品のみ
"""
from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

MODULES_DIR = Path(__file__).resolve().parent

# 部品名 -> (FLOW_NAME, 出力 bivr ファイル名)。前例の命名規則 "テスト$<名前>受入" / "<Name>AcceptanceTest.bivr" に倣う
PARTS = {
    "yes_no_classifier":         ("テスト$YesNo受入",      "YesNoAcceptanceTest.bivr"),
    "checkup_intent_classifier": ("テスト$用件分類受入",   "CheckupIntentAcceptanceTest.bivr"),
    "checkup_course_classifier": ("テスト$コース分類受入", "CheckupCourseAcceptanceTest.bivr"),
    "checkup_menu_classifier":      ("テスト$メニュー分類受入",    "CheckupMenuAcceptanceTest.bivr"),
    "ambiguity_gate":               ("テスト$曖昧検出受入",        "AmbiguityGateAcceptanceTest.bivr"),
    "phone_type":                   ("テスト$電話種別受入",         "PhoneTypeAcceptanceTest.bivr"),
    "checkup_option_classifier":    ("テスト$オプション選択受入",   "CheckupOptionAcceptanceTest.bivr"),
    "intent_classifier_v2":         ("カレス記念病院_診療_20260716$用件分類v2受入", "IntentV2AcceptanceTest.bivr"),
}

# 本番 script.js が {{...}} テンプレート方式（gen_intent_v2.py 等で外部充填）の部品は、
# script.js（未充填テンプレート）でなく part.json の filled_script を base とする。
# 未指定の部品は従来通り script.js（spec がインラインの @spec-begin/@spec-end 方式）。
BASE_SCRIPT_FILE = {
    "intent_classifier_v2": "generated_menu.js",
}

MAX_MODULES_WARN = 900  # 1 コール 1000 モジュール上限（実運用バジェット 900）

# 本番 script.js の入力取得行（変数名を捕捉 → r / input など部品ごとの差異を吸収）。
# SOURCE_MODULE = 旧来の分類器群 / INPUT_MODULE = intent_classifier_v2（{{...}}テンプレート方式）
INPUT_LINE_RE = re.compile(r"var (\w+) = \$runner\.getModuleResult\((?:SOURCE_MODULE|INPUT_MODULE)\);")
# 設定列 → script.js の設定行 var 名。cases.tsv にこの列があればリテラル注入する（行末コメント温存）。
#   checkup_menu_classifier: menu 列 → var MENU / ambiguity_gate: group 列 → var GROUP
CONFIG_COLS = {"menu": "MENU", "group": "GROUP"}


def _config_line_re(var_name: str):
    return re.compile(r'var %s\s*=\s*"[^"]*"\s*;' % var_name)


def regex_escape(s: str) -> str:
    """Brekeke condition (regex) 用に正規表現メタ文字をエスケープ。"""
    return re.sub(r"([.^$*+?()\[\]{}|\\/])", r"\\\1", s)


def js_str(s: str) -> str:
    """JS 文字列リテラルを安全に生成（" \\ 改行 unicode をエスケープ）。json.dumps の出力は妥当な JS 文字列。"""
    return json.dumps(s, ensure_ascii=False)


def empty_next_slot() -> dict:
    return {"condition": "", "label": "", "nextModuleName": ""}


def empty_subs() -> list:
    return [{"moduleName": "", "label": ""} for _ in range(3)]


def load_cases(tsv_path: Path):
    """cases.tsv を test_oracle.py と同一手順で読む（先頭行ヘッダ、空行・#コメント行スキップ）。"""
    cases = []
    with io.open(tsv_path, "r", encoding="utf-8") as f:
        header = f.readline().rstrip("\r\n").split("\t")
        for lineno, line in enumerate(f, start=2):
            line = line.rstrip("\r\n")
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split("\t")
            row = dict(zip(header, cols))
            row["_lineno"] = lineno
            cases.append(row)
    return header, cases


def build_script_for_case(base_script: str, cid: str, utterance: str,
                          expected: str, config) -> str:
    """script.js の入力取得行をリテラル注入に差し替え、先頭にマーカーログを足す。
    config = None または (var_name, value)（menu→MENU / group→GROUP の設定行注入）。"""
    if not INPUT_LINE_RE.search(base_script):
        raise SystemExit(
            "ERROR: 入力取得行 (var <name> = $runner.getModuleResult(SOURCE_MODULE);) が見つからない。"
            " script.js が想定外フォーマット"
        )
    # 関数置換にすると json.dumps 由来のバックスラッシュが re の置換特殊扱いを受けない
    # m.group(1) で変数名（r / input 等）を保持したまま差し替え
    s = INPUT_LINE_RE.sub(lambda m: "var " + m.group(1) + " = " + js_str(utterance) + ";",
                          base_script, count=1)

    extra = ""
    if config is not None:
        var_name, value = config
        cre = _config_line_re(var_name)
        if not cre.search(s):
            raise SystemExit(
                f"ERROR: var {var_name} 行が見つからない ({cid})。設定列ありだが script に {var_name} 設定行が無い"
            )
        s = cre.sub(lambda m: "var %s = %s;" % (var_name, js_str(value)), s, count=1)
        extra = " %s=%s" % (var_name.lower(), value)

    marker_text = "[%s] expected=%s%s in=%s" % (cid, expected, extra, utterance)
    marker = "$runner.getLogger().info(" + js_str(marker_text) + ");\n\n"
    return marker + s


def make_script_module(name: str, script: str, layout: dict, expected_label: str,
                       on_match_next: str, on_fail_next: str, description: str) -> dict:
    """テストケース用 @General$Script モジュール（期待ジャンプ + catch-all FAIL）。"""
    next_slots = [
        {"condition": "^" + regex_escape(expected_label) + "$", "label": "PASS→次", "nextModuleName": on_match_next},
        {"condition": "^.*$", "label": "FAIL", "nextModuleName": on_fail_next},
    ]
    while len(next_slots) < 10:
        next_slots.append(empty_next_slot())
    return {
        "name": name,
        "type": "@General$Script",
        "matchingmethod": 1,
        "description": description,
        "layout": layout,
        "params": {"script": script.replace("\r\n", "\n").replace("\n", "\r\n")},
        "next": next_slots,
        "subs": empty_subs(),
    }


def make_disconnect_module(name: str, layout: dict, description: str) -> dict:
    return {
        "name": name,
        "type": "@IVR$Disconnect",
        "matchingmethod": 1,
        "description": description,
        "layout": layout,
        "params": {},
        "next": [empty_next_slot() for _ in range(10)],
        "subs": empty_subs(),
    }


def build_part(part: str) -> tuple:
    flow_name, out_name = PARTS[part]
    part_dir = MODULES_DIR / part
    base_script = (part_dir / BASE_SCRIPT_FILE.get(part, "script.js")).read_text(encoding="utf-8")
    # 内蔵 saveContext 部品は CONTEXT_NAME を空にする＝ユニット受入では context 保存を no-op に
    # （受入は decide() の分類出力のみ検証。in-flow の保存は P7 連結＋実機で担保）。
    base_script = base_script.replace("__CONTEXT_NAME__", "").replace("__CONTEXT_DISPLAY_TYPE__", "TEXT")
    tsv = part_dir / "acceptance_test" / "cases.tsv"
    header, cases = load_cases(tsv)
    for col in ("id", "utterance", "expected"):
        if col not in header:
            raise SystemExit(f"{part}: cases.tsv に必須列 '{col}' が無い (header={header})")
    config_col = next((c for c in CONFIG_COLS if c in header), None)  # menu / group / なし

    modules: dict[str, dict] = {}
    x_test, x_fail = 300, 820
    y_step, y0 = 160, 100
    n = len(cases)

    pass_name = "PASS_全件PASS"
    modules[pass_name] = make_disconnect_module(
        pass_name,
        layout={"x": x_test, "y": y0 + (n + 1) * y_step},
        description=f"全 {n} ケースの期待 jump が連続発火 → 受入テスト PASS",
    )

    next_module = pass_name
    for idx, c in reversed(list(enumerate(cases))):
        i = idx + 1
        cid, utt, exp = c["id"], c["utterance"], c["expected"]
        config = (CONFIG_COLS[config_col], c.get(config_col)) if config_col else None
        cfg_desc = f" {config_col}={c.get(config_col)}" if config_col else ""
        fail_name = f"FAIL_{cid}_期待:{exp}"
        modules[fail_name] = make_disconnect_module(
            fail_name,
            layout={"x": x_fail, "y": y0 + i * y_step},
            description=f"{cid} で期待 '{exp}' と異なる結果。回帰 (cases.tsv L{c['_lineno']})",
        )
        test_name = f"テスト{cid}"
        script = build_script_for_case(base_script, cid, utt, exp, config)
        modules[test_name] = make_script_module(
            test_name,
            script=script,
            layout={"x": x_test, "y": y0 + i * y_step},
            expected_label=exp,
            on_match_next=next_module,
            on_fail_next=fail_name,
            description=f"受入ケース {cid}: in={utt!r} expected={exp}{cfg_desc}",
        )
        next_module = test_name

    start_name = next_module
    menu_note = f"（{config_col} 列を {CONFIG_COLS[config_col]} 設定行に注入）" if config_col else ""
    flow = {
        "name": flow_name,
        "desc": f"{part} 受入テスト {n} ケース (Pattern 6 チェイン式)。cases.tsv と 1:1・oracle 一致済。"
                f"入力をリテラル注入し STT 非依存{menu_note}。1 コールで全件直列実行、"
                f"PASS_全件PASS 到達で受入確定。",
        "start": start_name,
        "modules": modules,
        "layout": {"width": 1400, "height": y0 + (n + 2) * y_step},
        "resultValue": "",
        "postCallAction": "",
    }

    out = part_dir / "acceptance_test" / out_name
    body = json.dumps(flow, ensure_ascii=False, separators=(",", ":"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        fname = "flows/@flow_" + quote(flow_name, safe="") + ".txt"
        zf.writestr(fname, body)

    n_modules = len(modules)
    warn = "  ⚠ モジュール上限注意" if n_modules > MAX_MODULES_WARN else ""
    print(f"[{part}] wrote {out_name}: {n} cases, {n_modules} modules "
          f"({n} test + {n} FAIL + 1 PASS), {out.stat().st_size} bytes{warn}")
    print(f"    flow={fname}  start={start_name}  config_col={config_col or 'none'}")
    return n, n_modules


def main(argv) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    targets = argv[1:] if len(argv) > 1 else list(PARTS.keys())
    for t in targets:
        if t not in PARTS:
            raise SystemExit(f"未知の部品: {t} (対象: {', '.join(PARTS)})")
    total_cases = total_modules = 0
    for t in targets:
        n, m = build_part(t)
        total_cases += n
        total_modules += m
    print(f"\n合計: {len(targets)} 部品 / {total_cases} ケース / {total_modules} モジュール")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
