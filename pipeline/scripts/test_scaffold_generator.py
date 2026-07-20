#!/usr/bin/env python3
"""
test_scaffold_generator.py — Pattern 6 (テストフロー) 専用 scaffold

通常の scaffold_generator.py は本番 IVR フロー (聴取・OpenAI 分類・サブフロー・終話チェーン)
を前提にした生成器。Pattern 6 はそれとは別物で、Brekeke の特定モジュール動作を検証する
ためのテストフローを組み立てる。本番 scaffold には触らない方針 (将来統合の余地あり)。

【対応ブロック型 (scenario_flow)】
  - opening              : 冒頭 wait (固定 2 秒)
  - announcement         : TTS で文字列読み上げ (テスト開始ログ等)
  - inline_script        : 生 JS を Brekeke Script モジュールに展開
  - context_match_router : Brekeke CMR (module1Name/module2Name の出力値で分岐)
  - dtmf_date_test_matrix: 4桁DTMF日付正規化スクリプトの大量ケース検証 (1 entry → 5 modules/case)
  - script_test_matrix   : 任意の単体スクリプトを sidecar JS 読込で全ケース検証 (1 entry → 5 modules/case)
  - termination          : @IVR$Disconnect で切断

【入力 YAML 構造】
  version: "2.0"
  basic_info:
    facility_name: "テスト"
    group_name: "テスト$<テスト名>"
    flow_name: "テスト$<テスト名>"
  flow_structure:
    type: standalone
    flows:
      - name: "テスト$<テスト名>"
        role: main
    subflows: []
  scenario_flow:
    - step: <モジュール名>
      type: opening | announcement | inline_script | context_match_router | termination
      ...

【出力】
  output/json/scaffold_{stem}.json — 既存 scaffold と同じ場所・形式。build_bivr.py が拾える。

Usage:
    python3 scripts/test_scaffold_generator.py <yaml_path>
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

_JST = timezone(timedelta(hours=9))


def _resolve_date_token(value: str) -> str:
    """生成時の JST 現在日を基準に相対日付トークンを解決する。
    未来日/今日境界の受入ケースを「生成日に対して常に正しい」状態に保つ（固定日付の
    ドリフト防止: 例 2026-06-02 は作成時は未来でも後日には過去になり INVALID 期待が崩れる）。
      __TODAY__         → 生成日 YYYYMMDD      / __TOMORROW__ → 生成日+1（=常に未来）
      __FUTURE__        → 生成日+400日 YYYYMMDD（確実に未来）
      __FUTURE_WAREKI__ → 生成日+400日を「令和N年M月D日」に（元号表記の未来日）
    P6 は生成と同日に架電する前提（同日なら __TOMORROW__ は実機でも未来）。
    未来日を検証するケースは必ずこれらのトークンを使う（固定日付禁止＝再現性のルール）。"""
    if not value or "__" not in value:
        return value
    today = datetime.now(_JST).date()
    fut = today + timedelta(days=400)
    wareki = "令和%d年%d月%d日" % (fut.year - 2018, fut.month, fut.day)  # 令和元年=2019
    return (value
            .replace("__TODAY__", today.strftime("%Y%m%d"))
            .replace("__TOMORROW__", (today + timedelta(days=1)).strftime("%Y%m%d"))
            .replace("__FUTURE_WAREKI__", wareki)
            .replace("__FUTURE__", fut.strftime("%Y%m%d")))

try:
    import yaml
except ImportError:
    print("Error: PyYAML が必要です", file=sys.stderr)
    sys.exit(1)


# ─────────────────────────── 汎用ヘルパー (scaffold_generator.py と同等) ───────────────────────────

def _N(cond: str, label: str, next_module: str) -> dict:
    return {"condition": cond, "label": label, "nextModuleName": next_module}


def _E() -> dict:
    return {"condition": "", "label": "", "nextModuleName": ""}


def _S() -> dict:
    return {"moduleName": "", "label": ""}


def M(name: str, type_: str, params: dict, next_: list,
      subs: list | None = None, x: int = 0) -> tuple:
    if subs is None:
        subs = [_S(), _S(), _S()]
    data = {
        "layout": {"x": x, "y": 0},
        "next": next_,
        "subs": subs,
        "name": name,
        "description": "",
        "matchingmethod": 1,
        "type": type_,
        "params": params,
    }
    return (name, data)


def _pad_next(next_: list) -> list:
    while len(next_) < 10:
        next_.append(_E())
    return next_


# ─────────────────────────── ブロックビルダー ───────────────────────────

def build_opening(name: str, next_module: str) -> tuple:
    """冒頭 wait モジュール (Custom$wait 2 秒)"""
    return M(name, "Custom$wait", {"wait": "2000"},
             _pad_next([_N("^.*$", "next", next_module)]))


def build_announcement(name: str, prompt: str, next_module: str | None) -> tuple:
    """TTS announcement (drjoy^Text To Speech$Text to speech)"""
    next_list = []
    if next_module:
        next_list.append(_N("^.*$", "Next Module", next_module))
    params = {
        "prompt": prompt or "",
        "stop_by_dtmf": "No",
        "category_words": "",
    }
    return M(name, "drjoy^Text To Speech$Text to speech", params,
             _pad_next(next_list))


def build_inline_script(name: str, body: str, reference_module: str,
                        conditions: list, default_next: str = "") -> tuple:
    """生 JS を Brekeke Script (@General$Script) に展開

    body: JS の生コード。$runner.setResult(...) で setResult、logger.info(...) でログ
    reference_module: params.module に入る。CMR/script の入力参照に使う
    conditions: [{match, next}, ...] — setResult 値での分岐
    default_next: catch-all (^.*$) 用の next。conditions に該当しない値で進む先
    """
    next_ = []
    for cond in conditions:
        match = cond["match"]
        next_module = cond["next"]
        next_.append(_N(f"^{re.escape(match)}$", match, next_module))
    if default_next:
        next_.append(_N("^.*$", "Next Module", default_next))

    return M(name, "@General$Script",
             {"module": reference_module or "", "script": body},
             _pad_next(next_))


def build_context_match_router(name: str, module1: str, module2: str,
                               value_pairs: list, conditions: list) -> tuple:
    """Brekeke CMR (drjoy^Context Logic$ContextMatchRouter)

    module1, module2: module1Name / module2Name に入る (ユーザー定義 context は <%name%>、
                      モジュール名参照はそのまま文字列)
    value_pairs: [{value1, value2}, ...] — 各スロットの module1Value*/module2Value* 値
    conditions: [{match: "<label>", next: <module>}, ...] — ^1$, ^2$, ... の next ラベル
                 + match: "other" で ^0$ catch-all
    """
    params: dict = {
        "module1Name": module1,
        "module2Name": module2,
    }
    # 10 スロット
    for i in range(1, 11):
        if i <= len(value_pairs):
            pair = value_pairs[i - 1]
            params[f"module1Value{i}"] = pair.get("value1", "")
            params[f"module2Value{i}"] = pair.get("value2", "")
        else:
            params[f"module1Value{i}"] = ""
            params[f"module2Value{i}"] = ""

    next_ = []
    normal_conds = [c for c in conditions if c["match"] != "other"]
    other_conds = [c for c in conditions if c["match"] == "other"]

    for i, cond in enumerate(normal_conds, 1):
        next_.append(_N(f"^{i}$", cond["match"], cond["next"]))
    if other_conds:
        next_.append(_N("^0$", "other", other_conds[0]["next"]))
    else:
        next_.append(_N("^0$", "other", "TODO_other_target"))

    return M(name, "drjoy^Context Logic$ContextMatchRouter", params,
             _pad_next(next_))


def build_save_context2db(name: str, context_name: str, context_value: str,
                          context_display_type: str, next_module: str) -> tuple:
    """saveContext2DB モジュール (drjoy^Persistence$saveContext2DB)

    Brekeke ネイティブ。Script で `$ivr.exec("save2db", ...)` + `$runner.setObject()` を
    手書きする代わりに、このモジュールが内部で同等処理を行う (Medcity21 等で稼働実績あり)。
    """
    params = {
        "contextName": context_name,
        "contextValue": context_value,
        "contextDisplayType": context_display_type or "TEXT",
    }
    return M(name, "drjoy^Persistence$saveContext2DB", params,
             _pad_next([_N("^.*$", "next", next_module)]))


def build_null_check(name: str, key: str, true_next: str, false_next: str) -> tuple:
    """null-check モジュール (drjoy^Context Logic$null-check)

    key の値が null / 空文字 / 空白のみ / 空配列 / 空オブジェクト の場合 setResult="true"、
    それ以外は setResult="false" を返す Brekeke ネイティブモジュール。
    内部 JS で onlyVarMatch (`/^<%\\s*([\\w\\-]+)\\s*%>$/`) を判定して
    単独 `<% var %>` 形式なら getSystemVariableValue 経由で session variable を直読み、
    それ以外はモジュール名扱い (getModuleResult)。

    Args:
        name: モジュール名
        key: チェック対象。モジュール名 (例: "OpenAI_用件") or `<% varName %>` 形式
        true_next: setResult="true" 時の遷移先
        false_next: setResult="false" 時の遷移先
    """
    next_ = [
        _N("^true$", "true", true_next),
        _N("^false$", "false", false_next),
    ]
    return M(name, "drjoy^Context Logic$null-check", {"key": key},
             _pad_next(next_))


def build_termination(name: str) -> tuple:
    """切断モジュール (@IVR$Disconnect)"""
    return M(name, "@IVR$Disconnect", {}, _pad_next([]))


# ─────────────────────────── DTMF 日付正規化テスト (matrix) ───────────────────────────

# 焼き込み用テンプレート: 浜口さん本番スクリプト (4桁DTMF → MMDD or "NO_RESULT")
# 変更点:
#   - {{INPUT_MODULE}}: case ごとに入力モジュール名を置換
#   - maxDays[2] = 28 → 29 (2/29 を有効化、浜口さん指示 2026-05-26)
_DTMF_DATE_NORMALIZE_SCRIPT_TEMPLATE = r"""/**
 * 【Brekeke PBX Module Script】
 * スクリプト名：予約希望日入力（4桁DTMF）
 * 目的：4桁のDTMF入力（MMDD形式）から予約希望日を取得・保存
 * Input:  {{INPUT_MODULE}}
 * Output: yoyakukibobi（例：0415 → "04月15日"）
 */
// --- 1. 入力 ---
var rawInput = $runner.getModuleResult("{{INPUT_MODULE}}");
var text = "";
if (rawInput && typeof rawInput === "object" && rawInput.text) {
    text = String(rawInput.text).trim();
} else if (typeof rawInput === "string") {
    text = rawInput.trim();
}

// --- 2. 定義 ---
var result = "NO_RESULT";
var displayValue = "NO_RESULT";

// 月ごとの最大日数（うるう年対応で Feb=29）
var maxDays = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

// --- 3. ロジック ---
// DTMF最優先：4桁数字のみ（MMDD形式）
var dtmfPattern = /^(\d{2})(\d{2})$/;
var dtmfMatch = dtmfPattern.exec(text);

if (dtmfMatch) {
    var mm = parseInt(dtmfMatch[1], 10);
    var dd = parseInt(dtmfMatch[2], 10);

    // 月・日の妥当性チェック
    if (mm >= 1 && mm <= 12 && dd >= 1 && dd <= maxDays[mm]) {
        // ゼロ埋め正規化
        var mmStr = (mm < 10) ? ("0" + mm) : String(mm);
        var ddStr = (dd < 10) ? ("0" + dd) : String(dd);

        result = mmStr + ddStr;                      // 保存値：例 "0415"
        displayValue = mmStr + "月" + ddStr + "日";  // 表示値：例 "04月15日"
    } else {
        result = "NO_RESULT";
    }
} else {
    result = "NO_RESULT";
}

// --- 4. 保存 ---
// 正規化コード値を保存（例："0415"）
var contextField = {
    contextName: "yoyakukibobi",
    displayType: "TEXT",
    value: result
};
try {
    $ivr.exec("save2db", "save", JSON.stringify({ contextField: contextField }));
} catch(e) { /* silent */ }

// 表示用文字列を保存（例："04月15日"）
var contextFieldDisp = {
    contextName: "yoyakukibobi_yomiage",
    displayType: "TEXT",
    value: displayValue
};
try {
    $ivr.exec("save2db", "save", JSON.stringify({ contextField: contextFieldDisp }));
} catch(e) { /* silent */ }

// Branch遷移
$runner.setResult(result);
"""


def _generate_valid_mmdd_366() -> list[str]:
    """maxDays Feb=29 を前提に MMDD 366 件を順序固定で生成"""
    max_days = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    out: list[str] = []
    for mm in range(1, 13):
        for dd in range(1, max_days[mm] + 1):
            out.append(f"{mm:02d}{dd:02d}")
    return out


def build_dtmf_date_test_matrix(matrix_step: dict) -> list[tuple]:
    """dtmf_date_test_matrix を 1 dispatch + 5 modules/case に展開

    YAML 仕様:
      - step: <matrix_name>
        type: dtmf_date_test_matrix
        auto_generate_valid: true        # 366 有効ケース自動生成 (id="v0101"..."v1231")
        valid_range:                     # [optional] 有効ケースを MMDD でレンジ絞り込み
          start: "0906"                  # この MMDD 以降のみ生成 (両端含む)
          end: "1231"                    # この MMDD 以前のみ生成
        additional_cases:                # 追加ケース (順番は valid の後)
          - {id: inv_0230, input: "0230", expected: "NO_RESULT"}
          ...
        final_next: <最終 case PASS/FAIL の遷移先>

    Brekeke の 1 コール ハード上限 1000 モジュール (Max execution of modules.1000) を踏まえ、
    実運用は 900 までに抑える。4 モジュール / case 設計なら 1 bivr 220 ケース目安
    (3 フレーム + 220 × 4 = 883)。それを超える場合は valid_range で分割する。

    出力モジュール (1 + 5×N):
      - <matrix_name>             : dispatch (pass-through inline_script → 最初の case)
      - <id>_in                   : inline_script で $runner.setResult("<input>")
      - <id>_norm                 : 正規化スクリプト (焼き込み、{{INPUT_MODULE}} 置換)
      - <id>_cmr                  : CMR (norm 出力 == expected) で PASS/FAIL 分岐
      - <id>_pass                 : PASS ログ (info)
      - <id>_fail                 : FAIL ログ (error)
      pass/fail とも次 case の <next_id>_in (最終 case のみ final_next) へ
    """
    matrix_name = matrix_step["step"]

    valid_range = matrix_step.get("valid_range") or {}
    range_start = valid_range.get("start", "0101")
    range_end = valid_range.get("end", "1231")

    cases: list[dict] = []
    if matrix_step.get("auto_generate_valid"):
        for mmdd in _generate_valid_mmdd_366():
            if mmdd < range_start or mmdd > range_end:
                continue
            cases.append({"id": f"v{mmdd}", "input": mmdd, "expected": mmdd})
    for extra in matrix_step.get("additional_cases", []) or []:
        cases.append(extra)

    final_next = matrix_step.get("final_next") or matrix_step.get("next") or ""

    if not cases:
        # matrix だけで何もない場合は dispatch を final_next にスルーさせる
        return [build_inline_script(
            name=matrix_name,
            body='$runner.setResult("ok");',
            reference_module="",
            conditions=[],
            default_next=final_next,
        )]

    modules: list[tuple] = []

    first_in = f"{cases[0]['id']}_in"
    modules.append(build_inline_script(
        name=matrix_name,
        body='$runner.setResult("ok");  // matrix dispatch',
        reference_module="",
        conditions=[],
        default_next=first_in,
    ))

    for i, case in enumerate(cases):
        case_id = case["id"]
        in_module = f"{case_id}_in"
        norm_module = f"{case_id}_norm"
        cmr_module = f"{case_id}_cmr"
        pass_module = f"{case_id}_pass"
        fail_module = f"{case_id}_fail"

        if i + 1 < len(cases):
            next_first = f"{cases[i + 1]['id']}_in"
        else:
            next_first = final_next

        input_val = case["input"]
        expected_val = case["expected"]

        # 1. 入力モジュール
        modules.append(build_inline_script(
            name=in_module,
            body=f'$runner.setResult("{input_val}");',
            reference_module="",
            conditions=[],
            default_next=norm_module,
        ))

        # 2. 正規化スクリプト (テンプレート置換で焼き込み)
        norm_body = _DTMF_DATE_NORMALIZE_SCRIPT_TEMPLATE.replace(
            "{{INPUT_MODULE}}", in_module
        )
        modules.append(build_inline_script(
            name=norm_module,
            body=norm_body,
            reference_module=in_module,
            conditions=[],
            default_next=cmr_module,
        ))

        # 3. CMR (norm 出力 == expected)
        modules.append(build_context_match_router(
            name=cmr_module,
            module1=norm_module,
            module2=norm_module,
            value_pairs=[{"value1": expected_val, "value2": expected_val}],
            conditions=[
                {"match": expected_val, "next": pass_module},
                {"match": "other", "next": fail_module},
            ],
        ))

        # 4. PASS ログ
        modules.append(build_inline_script(
            name=pass_module,
            body=(
                f'$runner.getLogger().info("[TEST PASS] {case_id} in={input_val} exp={expected_val}");\n'
                f'$runner.setResult("ok");'
            ),
            reference_module="",
            conditions=[],
            default_next=next_first,
        ))

        # 5. FAIL ログ
        modules.append(build_inline_script(
            name=fail_module,
            body=(
                f'$runner.getLogger().error("[TEST FAIL] {case_id} in={input_val} exp={expected_val}");\n'
                f'$runner.setResult("ok");'
            ),
            reference_module="",
            conditions=[],
            default_next=next_first,
        ))

    return modules


# ─────────────────────────── 汎用スクリプト単体テスト (matrix) ───────────────────────────

def build_script_test_matrix(matrix_step: dict, yaml_dir: "Path") -> list[tuple]:
    """script_test_matrix — 任意の単体スクリプト (分類器等) を全ケース実機検証する汎用 matrix。

    dtmf_date_test_matrix がケース固有 JS をテンプレ焼き込みするのに対し、こちらは検証対象
    スクリプトの JS を sidecar ファイル (`script_file`) から **そのまま** 読み込む
    (デプロイ正本とのバイト一致を保証 = 部品ポリシー DoD#4)。入力モジュール名
    (`input_placeholder`) を case ごとの <id>_in に置換して展開する。
    新モジュールのテスト追加は YAML に sidecar 参照＋ケース表を書くだけ (エンジン無編集)。

    YAML 仕様:
      - step: <matrix_name>
        type: script_test_matrix
        script_file: "<検証対象 JS への相対パス (YAML からの相対)>"
        input_placeholder: "入力_診療科"   # JS 内で入力を参照しているモジュール名
        cases:                              # インライン (cases_file と併用可、cases の後に連結)
          - {id: c001, input: "皮膚科", expected: "皮膚科"}
          ...
        cases_file: "<JSON 配列ファイル (任意)>"
        final_next: <最終 case 後の遷移先>

    出力モジュール (1 + 5×N):
      <matrix_name> : dispatch (pass-through inline_script → 最初の case)
      <id>_in   : inline_script  $runner.setResult("<input>")  (JSON エスケープで安全に埋込)
      <id>_clf  : inline_script  検証対象 JS (input_placeholder → <id>_in 置換、他は正本のまま)
      <id>_cmr  : CMR            clf 出力 == expected → ^1$ pass / ^0$ fail
      <id>_pass : inline_script  [TEST PASS] ログ → 次 case (最終は final_next)
      <id>_fail : inline_script  [TEST FAIL] ... got=<clf実出力> ログ → 次 case

    検証は Brekeke ログを grep "[TEST FAIL]" で件数 0 を確認 (dtmf_date_test_matrix と同様)。
    pass/fail とも次 case へ進むため、1 回の通話で全ケースの結果がログに残る。
    """
    matrix_name = matrix_step["step"]

    script_file = matrix_step.get("script_file")
    if not script_file:
        raise ValueError(f"script_test_matrix '{matrix_name}': script_file が必要です")
    js_path = (yaml_dir / script_file).resolve()
    if not js_path.exists():
        raise ValueError(
            f"script_test_matrix '{matrix_name}': script_file が見つかりません: {js_path}"
        )
    module_js = js_path.read_text(encoding="utf-8")

    placeholder = matrix_step.get("input_placeholder")
    if not placeholder:
        raise ValueError(f"script_test_matrix '{matrix_name}': input_placeholder が必要です")
    if placeholder not in module_js:
        raise ValueError(
            f"script_test_matrix '{matrix_name}': input_placeholder "
            f"'{placeholder}' が script_file 内に見つかりません"
        )

    cases: list[dict] = list(matrix_step.get("cases") or [])
    cases_file = matrix_step.get("cases_file")
    if cases_file:
        cf_path = (yaml_dir / cases_file).resolve()
        cases.extend(json.loads(cf_path.read_text(encoding="utf-8")))
    if not cases:
        raise ValueError(f"script_test_matrix '{matrix_name}': cases が空です")

    final_next = matrix_step.get("final_next") or matrix_step.get("next") or ""

    modules: list[tuple] = []

    first_in = f"{cases[0]['id']}_in"
    modules.append(build_inline_script(
        name=matrix_name,
        body='$runner.setResult("ok");  // script_test_matrix dispatch',
        reference_module="",
        conditions=[],
        default_next=first_in,
    ))

    for i, case in enumerate(cases):
        case_id = case["id"]
        in_module = f"{case_id}_in"
        clf_module = f"{case_id}_clf"
        cmr_module = f"{case_id}_cmr"
        pass_module = f"{case_id}_pass"
        fail_module = f"{case_id}_fail"

        next_first = f"{cases[i + 1]['id']}_in" if i + 1 < len(cases) else final_next

        input_val = "" if case.get("input") is None else str(case["input"])
        expected_val = str(case["expected"])

        # 1. 入力モジュール (入力文字列をそのまま setResult)
        modules.append(build_inline_script(
            name=in_module,
            body=f'$runner.setResult({json.dumps(input_val, ensure_ascii=False)});',
            reference_module="",
            conditions=[],
            default_next=clf_module,
        ))

        # 2. 検証対象スクリプト (input_placeholder → in_module 置換、それ以外は正本のまま)
        clf_body = module_js.replace(placeholder, in_module)
        modules.append(build_inline_script(
            name=clf_module,
            body=clf_body,
            reference_module=in_module,
            conditions=[],
            default_next=cmr_module,
        ))

        # 3. CMR (clf 出力 == expected)
        modules.append(build_context_match_router(
            name=cmr_module,
            module1=clf_module,
            module2=clf_module,
            value_pairs=[{"value1": expected_val, "value2": expected_val}],
            conditions=[
                {"match": expected_val, "next": pass_module},
                {"match": "other", "next": fail_module},
            ],
        ))

        # 4. PASS ログ
        pass_msg = f"[TEST PASS] {case_id} in={input_val} exp={expected_val}"
        modules.append(build_inline_script(
            name=pass_module,
            body=(
                f'$runner.getLogger().info({json.dumps(pass_msg, ensure_ascii=False)});\n'
                f'$runner.setResult("ok");'
            ),
            reference_module="",
            conditions=[],
            default_next=next_first,
        ))

        # 5. FAIL ログ (clf の実出力も残して原因究明を容易に)
        fail_msg = f"[TEST FAIL] {case_id} in={input_val} exp={expected_val} got="
        modules.append(build_inline_script(
            name=fail_module,
            body=(
                f'$runner.getLogger().error({json.dumps(fail_msg, ensure_ascii=False)} '
                f'+ String($runner.getModuleResult("{clf_module}")));\n'
                f'$runner.setResult("ok");'
            ),
            reference_module="",
            conditions=[],
            default_next=next_first,
        ))

    return modules


# 認定正本 dob_normalizer/script.js（scaffold が本番埋め込みする値スクリプト）。
# DOB Re-confirmation の P6 受入テストもこれを openAI_prompt に verbatim 埋め込み、
# 実機で「本番と同一バイトのエンジン」を検証する（cert ゲートの engine_hash と一致）。
DOB_NORMALIZER_JS_PATH = (
    Path(__file__).resolve().parent.parent / "modules" / "dob_normalizer" / "script.js"
)


def build_dob_reconfirmation_test_matrix(matrix_step: dict) -> list[tuple]:
    """DOB Re-confirmation (生年月日復唱) モジュールの受入テストマトリクス (Pattern 6)。

    検証対象: drjoy^TS Custom Module$DOB Re-confirmation（認定正本 dob_normalizer/script.js を
    openAI_prompt に verbatim 埋め込み）。STT/OpenAI を呼ばず、prime スクリプトで入力
    (raw_text / nodeValue / raw_dob_data cache) を直接注入し、DOB モジュールの setResult を
    期待値と突合する。OK ケースは #data# 置換 TTS を再生するので readback の読み（tts_ai 含む）も実機確認可。

    ★ DOB はカスタムモジュールでルーティングがジャンプラベル方式（timeout/error/invalid/success）。
       next は deployed 同一構造を厳守し、期待値照合は後段 CMR(getModuleResult) に委譲する。

    OK ケース (expect=読み上げ値) = 3 モジュール: <id>_prime → <id>_dob → <id>_chk(CMR)
    INVALID ケース (expect=INVALID) = 2 モジュール: <id>_prime → <id>_dob

    YAML 仕様:
      - step: <matrix_name>
        type: dob_reconfirmation_test_matrix
        prompt: "{tts_ai:#data# でよろしいでしょうか。}"  # 任意。tts_ai で readback 検証
        date_reading_mode: "自動"                         # 任意（既定 自動）
        save_dob2db: "no"                                  # 任意（既定 no）
        pass_terminal: 結果_全PASS
        fail_terminal: 結果_FAIL
        cases:
          - {id: R1, raw: "", node: "19790312", expect: "1979年3月12日"}
          - {id: M1, raw: "1979年3月12日", node: "", reading_mode: "和暦", expect: "昭和54年3月12日"}
    """
    matrix_name = matrix_step["step"]
    prompt = matrix_step.get("prompt", "{tts_g:#data# でよろしいでしょうか。}")
    default_mode = matrix_step.get("date_reading_mode", "自動")
    default_save = str(matrix_step.get("save_dob2db", "no"))
    pass_terminal = matrix_step.get("pass_terminal", "結果_全PASS")
    fail_terminal = matrix_step.get("fail_terminal", "結果_FAIL")
    cases = matrix_step.get("cases", []) or []

    # 認定正本を verbatim 埋め込み（scaffold build_dob_reconfirmation と同一・engine_hash 一致）。
    if not DOB_NORMALIZER_JS_PATH.exists():
        raise ValueError(f"dob_normalizer 正本が見つかりません: {DOB_NORMALIZER_JS_PATH}")
    dob_body = DOB_NORMALIZER_JS_PATH.read_text(encoding="utf-8")

    if not cases:
        return [build_inline_script(
            name=matrix_name, body='$runner.setResult("ok");',
            reference_module="", conditions=[], default_next=pass_terminal,
        )]

    modules: list[tuple] = []
    first_prime = f"{cases[0]['id']}_prime"
    modules.append(build_inline_script(
        name=matrix_name,
        body='$runner.setResult("ok");  // dob matrix dispatch',
        reference_module="", conditions=[], default_next=first_prime,
    ))

    for i, case in enumerate(cases):
        cid = case["id"]
        prime = f"{cid}_prime"
        dob = f"{cid}_dob"
        chk = f"{cid}_chk"
        raw = _resolve_date_token(case.get("raw", ""))
        node = _resolve_date_token(case.get("node", ""))
        cache = case.get("cache", "")
        expect = case["expect"]
        mode = case.get("reading_mode", default_mode)
        save = str(case.get("save", default_save))
        is_invalid = expect.strip().upper() == "INVALID"

        is_last = (i + 1 == len(cases))
        pass_next = pass_terminal if is_last else f"{cases[i + 1]['id']}_prime"

        # 1. prime: 入力注入（raw_text / raw_dob_data cache / setResult(node)）
        raw_lit = json.dumps(raw, ensure_ascii=False)
        node_lit = json.dumps(node, ensure_ascii=False)
        cache_lit = json.dumps(cache, ensure_ascii=False)
        prime_body = (
            f'$runner.setObject("raw_text", {raw_lit});\n'
            f'$runner.setObject("raw_dob_data", {cache_lit});\n'
            f'$runner.getLogger().info("[DOB-TEST] case={cid} | raw=" + {raw_lit} '
            f'+ " | node=" + {node_lit} + " | cache=" + {cache_lit});\n'
            f'$runner.setResult({node_lit});'
        )
        modules.append(build_inline_script(
            name=prime, body=prime_body,
            reference_module="", conditions=[], default_next=dob,
        ))

        # 2. DOB モジュール。next は deployed と同一構造（ラベル方式）。openAI_prompt に正本を埋込。
        if is_invalid:
            inv_dest, suc_dest = pass_next, fail_terminal
        else:
            inv_dest, suc_dest = fail_terminal, chk
        dob_next = [
            _N("^TIMEOUT$", "timeout", fail_terminal),
            _N("^ERROR$", "error", fail_terminal),
            _N("^INVALID$", "invalid", inv_dest),
            _N("^.*$", "success", suc_dest),
        ]
        modules.append(M(
            dob, "drjoy^TS Custom Module$DOB Re-confirmation",
            {"prompt": prompt, "module": prime, "dateReadingMode": mode,
             "saveDOB2db": save, "openAI_prompt": dob_body},
            dob_next,
        ))

        # 3. OK ケースのみ: CMR で DOB 出力(getModuleResult) を expect と一致確認
        if not is_invalid:
            modules.append(build_context_match_router(
                name=chk,
                module1=dob, module2=dob,
                value_pairs=[{"value1": expect, "value2": expect}],
                conditions=[
                    {"match": "ok", "next": pass_next},
                    {"match": "other", "next": fail_terminal},
                ],
            ))

    return modules


# ─────────────────────────── YAML パーサ → JSON 生成 ───────────────────────────

def _build_block(step: dict, yaml_dir: "Path | None" = None) -> list[tuple]:
    """1 ブロックを Brekeke モジュール tuple のリストに変換"""
    btype = step.get("type")
    name = step["step"]

    if btype == "opening":
        return [build_opening(name, step["next"])]

    if btype == "announcement":
        return [build_announcement(name, step.get("prompt", ""), step.get("next"))]

    if btype == "inline_script":
        return [build_inline_script(
            name=name,
            body=step.get("body", "// empty"),
            reference_module=step.get("reference_module", ""),
            conditions=step.get("conditions", []),
            default_next=step.get("default_next", "") or step.get("next", "") or "",
        )]

    if btype == "context_match_router":
        return [build_context_match_router(
            name=name,
            module1=step["module1"],
            module2=step.get("module2") or step["module1"],
            value_pairs=step.get("value_pairs", []),
            conditions=step["conditions"],
        )]

    if btype == "save_context2db":
        return [build_save_context2db(
            name=name,
            context_name=step["context_name"],
            context_value=step["context_value"],
            context_display_type=step.get("context_display_type", "TEXT"),
            next_module=step["next"],
        )]

    if btype == "null_check":
        return [build_null_check(
            name=name,
            key=step["key"],
            true_next=step["true_next"],
            false_next=step["false_next"],
        )]

    if btype == "termination":
        return [build_termination(name)]

    if btype == "dtmf_date_test_matrix":
        return build_dtmf_date_test_matrix(step)

    if btype == "script_test_matrix":
        if yaml_dir is None:
            raise ValueError("script_test_matrix には yaml_dir が必要です")
        return build_script_test_matrix(step, yaml_dir)

    if btype == "dob_reconfirmation_test_matrix":
        return build_dob_reconfirmation_test_matrix(step)

    raise ValueError(f"未対応の block type: {btype} (step={name})")


def generate(yaml_path: Path, output_path: Path) -> None:
    spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    basic = spec.get("basic_info", {})
    flow_structure = spec.get("flow_structure", {})
    flows = flow_structure.get("flows", [])
    main_flow_name = next((f["name"] for f in flows if f.get("role") == "main"),
                          flows[0]["name"] if flows else basic.get("flow_name", "test"))

    scenario_flow = spec.get("scenario_flow", [])
    if not scenario_flow:
        raise ValueError("scenario_flow が空です")

    start_module = scenario_flow[0]["step"]
    modules: dict = {}

    yaml_dir = yaml_path.parent
    # layout_roles: ブロック membership の正本サイドカー（scaffold_generator と同じ v2 形式）。
    # これが無いと layout_calculator が matrix 展開モジュール（<id>_in/_clf/_cmr/_pass/_fail）を
    # どのブロックにも分類できず ERROR 停止する（membership 自動記録の推測ゼロ化以降）。
    layout_roles: dict[str, dict[str, str]] = {}
    for step in scenario_flow:
        for module_name, module_data in _build_block(step, yaml_dir):
            modules[module_name] = module_data
            # termination ブロックは block_layout.py 側の sidecar_key 計算
            # （termination_module_ref = termination_ref or step）と一致させる。
            # 一致しないと termination_ref 明示指定ブロックの module が未分類に落ちる。
            if step.get("type") == "termination":
                sidecar_key = step.get("termination_ref") or step["step"]
            else:
                sidecar_key = step["step"]
            layout_roles.setdefault(sidecar_key, {}).setdefault(module_name, "")

    flow_json = {
        "layout": {},
        "resultValue": "",
        "postCallAction": "",
        "name": main_flow_name,
        "start": start_module,
        "modules": modules,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(flow_json, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[test_scaffold] wrote {output_path} ({len(modules)} modules)")

    # layout roles サイドカー（scaffold_<stem>.json → scaffold_layout_roles_<stem>.json）
    if output_path.name.startswith("scaffold_"):
        roles_path = output_path.parent / (
            "scaffold_layout_roles_" + output_path.name[len("scaffold_"):]
        )
        roles_path.write_text(
            json.dumps({"version": 2, "blocks": layout_roles}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[test_scaffold] layout roles sidecar: {roles_path.name}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python3 test_scaffold_generator.py <yaml_path> [output_path]",
              file=sys.stderr)
        return 1

    yaml_path = Path(sys.argv[1]).resolve()
    if not yaml_path.exists():
        print(f"Error: {yaml_path} が見つかりません", file=sys.stderr)
        return 1

    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2]).resolve()
    else:
        project_dir = Path(__file__).resolve().parent.parent
        stem = yaml_path.stem.replace("設計書_", "")
        output_path = project_dir / "output" / "json" / f"scaffold_{stem}.json"

    try:
        generate(yaml_path, output_path)
    except Exception as e:
        print(f"[test_scaffold] ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
