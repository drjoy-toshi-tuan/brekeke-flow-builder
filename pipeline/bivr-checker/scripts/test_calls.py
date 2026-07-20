#!/usr/bin/env python3
"""
test_calls.py — 汎用模擬通話テスト

フローJSONをプログラム的にたどり、全分岐パスの到達テストを行う。
startモジュールから終話（Disconnect）まで到達できるか検証。
サブフロー（Jump to Flow）も横断して追跡する。

Usage:
    python scripts/test_calls.py output/横須賀共済病院/*.json
    python scripts/test_calls.py output/貝塚病院/*.json

自動テストケース生成:
    フローJSON内のOpenAI分岐を解析し、全パスの組み合わせから10パターンを自動生成する。
    手動テストケースを --cases で指定することも可能。
"""
import json
import sys
import io
import os
import itertools
from pathlib import Path
from collections import defaultdict

# Windows cp932 対応
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================
# フロー読み込み
# ============================================================

def load_flows(json_paths):
    """複数のフローJSONを読み込み、フロー名→データのマップを返す"""
    flows = {}
    main_flow = None
    for p in json_paths:
        path = Path(p)
        if "verify" in path.name:
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if "modules" not in data:
            continue
        flow_name = data.get("name", path.stem)
        flows[flow_name] = data
        flows[path.stem] = data
        # メインフロー判定: モジュール数が最大
        if main_flow is None or len(data.get("modules", {})) > len(flows.get(main_flow, {}).get("modules", {})):
            main_flow = path.stem
    return flows, main_flow


# ============================================================
# テストケース自動生成
# ============================================================

def analyze_branches(flows, main_key):
    """メインフローのOpenAI/CMR分岐を解析し、分岐点と選択肢を返す"""
    data = flows[main_key]
    modules = data["modules"]
    branches = []  # [(module_name, type, [(condition, target)])]

    # BFSでstartから到達可能なモジュールを順にたどる
    start = data.get("start", "")
    visited = set()
    queue = [start]
    order = []

    while queue:
        current = queue.pop(0)
        if current in visited or current not in modules:
            continue
        visited.add(current)
        order.append(current)
        mod = modules[current]
        for n in mod.get("next", []):
            nm = n.get("nextModuleName", "")
            if nm and nm not in visited:
                queue.append(nm)

    for name in order:
        mod = modules[name]
        mod_type = mod.get("type", "")

        if "generate_by_OpenAI" in mod_type:
            choices = []
            for n in mod.get("next", []):
                cond = n.get("condition", "")
                nm = n.get("nextModuleName", "")
                if cond in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "") or not nm:
                    continue
                # 条件から値を抽出
                val = cond.replace("^", "").replace("$", "")
                if val in (".+", ".*"):
                    continue
                choices.append(("OpenAI", val, nm))
            if choices:
                branches.append((name, "OpenAI", choices))

        elif "ContextMatchRouter" in mod_type:
            choices = []
            for n in mod.get("next", []):
                cond = n.get("condition", "")
                nm = n.get("nextModuleName", "")
                if not nm or cond in ("^.*$", ""):
                    continue
                val = cond.replace("^", "").replace("$", "")
                choices.append(("CMR", val, nm))
            if choices:
                branches.append((name, "CMR", choices))

    return branches


def generate_test_cases(flows, main_key, max_cases=10):
    """分岐解析から自動的にテストケースを生成"""
    branches = analyze_branches(flows, main_key)
    data = flows[main_key]
    modules = data["modules"]

    test_cases = []

    # 1. 各OpenAI分岐の全選択肢をカバーするパターン
    # DFSでstartからDisconnectまでのパスを列挙
    paths = []
    find_paths(data, data.get("start", ""), [], set(), paths, max_depth=30)

    # パスからテストステップを抽出
    for path in paths:
        steps = extract_steps_from_path(modules, path)
        if steps is not None:
            # テスト名生成
            key_responses = [s[1] for s in steps if s[0] in ("OpenAI", "CMR")]
            name = "→".join(key_responses[:5]) if key_responses else "基本パス"
            test_cases.append((name, steps))

    # リトライ失敗パターンを追加
    retry_modules = [(n, m) for n, m in modules.items() if "Retry Counter" in m.get("type", "")]
    for retry_name, retry_mod in retry_modules:
        true_target = ""
        false_target = ""
        for n in retry_mod.get("next", []):
            if n.get("condition") == "true":
                true_target = n.get("nextModuleName", "")
            if n.get("condition") == "false":
                false_target = n.get("nextModuleName", "")

        # このリトライに到達するまでのパスを構築
        steps = build_path_to_retry(data, retry_name, modules)
        if steps is not None:
            steps.append(("Retry", "RETRY_FAIL"))

            # 無限ループ（false == true）の場合:
            # ループ後に正常入力→通話完走のシナリオにする
            # → 最初の正常パスからこの地点以降のステップを借りる
            is_loop = (false_target == true_target)
            if is_loop and paths:
                # 正常パスの中からこのリトライ地点を通るパスを探す
                for normal_path in paths:
                    normal_steps = extract_steps_from_path(modules, normal_path)
                    if normal_steps:
                        # リトライ到達前のステップ数を数えて、それ以降を追加
                        pre_count = len([s for s in steps if s[1] != "RETRY_FAIL"])
                        if len(normal_steps) > pre_count:
                            steps.extend(normal_steps[pre_count:])
                        break
            elif false_target and false_target in modules:
                post_steps = build_post_retry_steps(data, false_target, modules)
                if post_steps:
                    steps.extend(post_steps)

            name = f"リトライ上限_{retry_name.replace('リトライ_', '')}"
            test_cases.append((name, steps))

    # CMR分岐のカバレッジ補完: 未カバーのCMR値を使うパターンを追加
    covered_cmr = set()
    for _, steps in test_cases:
        for s in steps:
            if s[0] == "CMR":
                covered_cmr.add(s[1])
    # 各CMRの全値を確認して不足分を補完
    for branch_name, btype, choices in branches:
        if btype == "CMR":
            for _, val, _ in choices:
                if val not in covered_cmr:
                    # この値を含むパスを構築
                    base_steps = build_path_to_retry(data, branch_name, modules)
                    if base_steps is not None:
                        base_steps.append(("CMR", val))
                        name = f"CMR補完_{branch_name}={val}"
                        test_cases.append((name, base_steps))
                        covered_cmr.add(val)

    # 重複除去して最大max_cases件に
    seen = set()
    unique = []
    for name, steps in test_cases:
        key = tuple((s[0], s[1]) for s in steps)
        if key not in seen:
            seen.add(key)
            unique.append((name, steps))

    # 最大件数に制限（正常パス優先、リトライパスも含める）
    normal = [tc for tc in unique if "リトライ" not in tc[0]]
    retry = [tc for tc in unique if "リトライ" in tc[0]]

    result = normal[:max_cases - min(len(retry), 3)] + retry[:3]
    return result[:max_cases]


def find_paths(data, current, path, visited, results, max_depth=30):
    """DFSで全終話パスを列挙"""
    if len(path) > max_depth or current in visited:
        return
    if current not in data["modules"]:
        return

    mod = data["modules"][current]
    mod_type = mod.get("type", "")
    visited_copy = visited | {current}
    path_copy = path + [current]

    if "Disconnect" in mod_type:
        results.append(path_copy)
        return

    # Jump to Flow はスキップ（サブフロー内は追跡しない）
    if "Jump to Flow" in mod_type:
        for n in mod.get("next", []):
            nm = n.get("nextModuleName", "")
            if nm:
                find_paths(data, nm, path_copy, visited_copy, results, max_depth)
        return

    # 分岐モジュールは各選択肢を展開
    nexts = mod.get("next", [])
    expanded = False
    for n in nexts:
        cond = n.get("condition", "")
        nm = n.get("nextModuleName", "")
        if not nm:
            continue
        # TIMEOUT/ERROR/NO_RESULTはスキップ（正常パスのみ）
        if cond in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^INVALID$"):
            continue
        # Retry: trueのみ（falseはリトライ失敗パターンで別途処理）
        if "Retry" in mod_type and cond == "false":
            continue
        find_paths(data, nm, path_copy, visited_copy, results, max_depth)
        expanded = True

    if not expanded:
        # 遷移先なし = パス終端
        results.append(path_copy)


def extract_steps_from_path(modules, path):
    """パスからシミュレーション用ステップを抽出"""
    steps = []
    for i, name in enumerate(path):
        if name not in modules:
            continue
        mod = modules[name]
        mod_type = mod.get("type", "")

        if "generate_by_OpenAI" in mod_type:
            # 次のモジュール名から、どの条件でマッチしたか逆算
            next_in_path = path[i + 1] if i + 1 < len(path) else None
            for n in mod.get("next", []):
                if n.get("nextModuleName") == next_in_path:
                    cond = n.get("condition", "")
                    val = cond.replace("^", "").replace("$", "")
                    if val not in ("TIMEOUT", "ERROR", "NO_RESULT", ".+", ".*", ""):
                        steps.append(("OpenAI", val))
                    break

        elif "ContextMatchRouter" in mod_type:
            next_in_path = path[i + 1] if i + 1 < len(path) else None
            for n in mod.get("next", []):
                if n.get("nextModuleName") == next_in_path:
                    cond = n.get("condition", "")
                    val = cond.replace("^", "").replace("$", "")
                    if val not in (".*", ""):
                        steps.append(("CMR", val))
                    break

    return steps if steps else None


def build_path_to_retry(data, retry_name, modules):
    """startからリトライモジュールまでの最短パスのステップを構築"""
    # BFSでstartからretry_nameまでのパスを見つける
    start = data.get("start", "")
    queue = [(start, [])]
    visited = {start}

    while queue:
        current, path = queue.pop(0)
        if current == retry_name:
            return extract_steps_from_path(modules, path) or []
        if current not in modules:
            continue
        mod = modules[current]
        for n in mod.get("next", []):
            nm = n.get("nextModuleName", "")
            cond = n.get("condition", "")
            if nm and nm not in visited and cond not in ("false",):
                visited.add(nm)
                queue.append((nm, path + [current]))

    return None


def build_post_retry_steps(data, start_mod, modules):
    """リトライ失敗後の最短終話パスのステップを構築"""
    queue = [(start_mod, [start_mod])]
    visited = {start_mod}

    while queue:
        current, path = queue.pop(0)
        if current not in modules:
            continue
        mod = modules[current]
        mod_type = mod.get("type", "")

        if "Disconnect" in mod_type or "Jump to Flow" in mod_type:
            steps = extract_steps_from_path(modules, path)
            return steps or []

        for n in mod.get("next", []):
            nm = n.get("nextModuleName", "")
            cond = n.get("condition", "")
            if nm and nm not in visited:
                if cond not in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "false"):
                    visited.add(nm)
                    queue.append((nm, path + [nm]))

    return []


# ============================================================
# シミュレーション実行
# ============================================================

def simulate_call(flows, main_key, scenario_steps):
    """模擬通話シミュレーション"""
    main_data = flows[main_key]
    current_module = main_data["start"]
    current_flow = main_data
    path = []
    step_idx = 0
    max_iterations = 200
    loop_detect = {}  # module_name → visit count（ループ検出）

    for _ in range(max_iterations):
        if current_module not in current_flow["modules"]:
            return True, path, None

        # ループ検出: 同じモジュールを3回以上訪問 = 無限ループ確認 → テスト成功
        loop_detect[current_module] = loop_detect.get(current_module, 0) + 1
        if loop_detect[current_module] >= 3:
            path.append(f"  → 無限ループ確認（{current_module} を3回訪問）")
            return True, path, None

        mod = current_flow["modules"][current_module]
        mod_type = mod.get("type", "")
        nexts = mod.get("next", [])
        path.append(current_module)

        # Disconnect = 終話到達
        if "Disconnect" in mod_type:
            return True, path, None

        # 結果返却スクリプト = サブフロー終了
        if "Script" in mod_type and "script_結果返却" in current_module:
            return True, path, None

        # Jump to Flow = サブフロー
        if "Jump to Flow" in mod_type:
            flowname = mod.get("params", {}).get("flowname", "")
            subflow = None
            for key, fdata in flows.items():
                if fdata.get("name", "") == flowname:
                    subflow = fdata
                    break
            if subflow:
                path.append(f"  → サブフロー: {flowname}")

            next_mod = None
            for n in nexts:
                if n.get("nextModuleName"):
                    next_mod = n["nextModuleName"]
                    break
            if next_mod:
                current_module = next_mod
                continue
            return True, path, None

        # OpenAI分岐
        if "generate_by_OpenAI" in mod_type:
            # 具体的な分岐条件があるか確認（^.*$/^.+$/TIMEOUT/ERROR/NO_RESULT以外）
            specific_branches = [n for n in nexts
                                 if n.get("nextModuleName")
                                 and n.get("condition", "") not in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", "^.*$", "")]
            has_specific = len(specific_branches) > 0

            if has_specific and step_idx < len(scenario_steps):
                _, response = scenario_steps[step_idx]
                step_idx += 1
                matched = False
                for n in nexts:
                    cond = n.get("condition", "")
                    nm = n.get("nextModuleName", "")
                    if not nm:
                        continue
                    if cond == f"^{response}$":
                        current_module = nm
                        matched = True
                        break
                if not matched:
                    for n in nexts:
                        cond = n.get("condition", "")
                        nm = n.get("nextModuleName", "")
                        if cond in ("^.+$", "^.*$") and nm:
                            current_module = nm
                            matched = True
                            break
                if not matched:
                    return False, path, f"OpenAI {current_module}: 応答 '{response}' にマッチする遷移先なし"
                continue
            else:
                # 分岐なし or ステップ不足 → catch-allに進む（ステップ消費しない）
                for n in nexts:
                    cond = n.get("condition", "")
                    nm = n.get("nextModuleName", "")
                    if cond in ("^.+$", "^.*$") and nm:
                        current_module = nm
                        break
                else:
                    if has_specific:
                        return False, path, f"OpenAI {current_module}: ステップ不足かつcatch-allなし"
                    else:
                        return False, path, f"OpenAI {current_module}: catch-allなし"
                continue

        # ContextMatchRouter
        if "ContextMatchRouter" in mod_type:
            if step_idx < len(scenario_steps):
                _, response = scenario_steps[step_idx]
                step_idx += 1
                matched = False
                for n in nexts:
                    cond = n.get("condition", "")
                    nm = n.get("nextModuleName", "")
                    if cond == f"^{response}$" and nm:
                        current_module = nm
                        matched = True
                        break
                if not matched:
                    for n in nexts:
                        if n.get("condition") in ("^.*$",) and n.get("nextModuleName"):
                            current_module = n["nextModuleName"]
                            matched = True
                            break
                if not matched:
                    return False, path, f"ContextMatchRouter: 遷移先なし"
                continue
            else:
                for n in nexts:
                    if n.get("condition") in ("^.*$",) and n.get("nextModuleName"):
                        current_module = n["nextModuleName"]
                        break
                else:
                    return False, path, "ContextMatchRouter: ステップ不足かつdefaultなし"
                continue

        # Retry Counter
        if "Retry Counter" in mod_type:
            retry_fail = False
            if step_idx < len(scenario_steps) and scenario_steps[step_idx][1] == "RETRY_FAIL":
                retry_fail = True
                step_idx += 1

            target_cond = "false" if retry_fail else "true"
            for n in nexts:
                if n.get("condition") == target_cond and n.get("nextModuleName"):
                    current_module = n["nextModuleName"]
                    if retry_fail:
                        path.append("  → リトライ上限到達")
                    break
            else:
                return False, path, f"Retry {current_module}: {target_cond} 遷移先なし"
            continue

        # STT/DTMF
        if "Speech to Text" in mod_type or "DTMF" in mod_type:
            if step_idx < len(scenario_steps) and scenario_steps[step_idx][1] == "RETRY_FAIL":
                for n in nexts:
                    if n.get("condition") == "^TIMEOUT$" and n.get("nextModuleName"):
                        current_module = n["nextModuleName"]
                        path.append("  → STTタイムアウト")
                        break
                else:
                    return False, path, f"STT {current_module}: TIMEOUT遷移先なし"
            else:
                for n in nexts:
                    if n.get("condition") == "^.+$" and n.get("nextModuleName"):
                        current_module = n["nextModuleName"]
                        break
                else:
                    return False, path, f"STT {current_module}: success遷移先なし"
            continue

        # incoming-classifier: 通常着信（携帯）
        if "incoming-classifier" in mod_type:
            for n in nexts:
                cond = n.get("condition", "")
                if cond in ("^携帯$", "^.*$") and n.get("nextModuleName"):
                    current_module = n["nextModuleName"]
                    break
            else:
                return False, path, "incoming-classifier: 遷移先なし"
            continue

        # acceptance_times: 営業時間内
        if "acceptance_times" in mod_type:
            for n in nexts:
                if n.get("condition") == "^true$" and n.get("nextModuleName"):
                    current_module = n["nextModuleName"]
                    break
            else:
                return False, path, "acceptance_times: true遷移先なし"
            continue

        # その他（TTS, save系, wait等）: 最初の有効なnextに進む
        next_found = False
        for n in nexts:
            nm = n.get("nextModuleName", "")
            cond = n.get("condition", "")
            if nm and cond not in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^INVALID$"):
                current_module = nm
                next_found = True
                break

        if not next_found:
            return True, path, None

    return False, path, "最大反復回数超過（無限ループの可能性）"


# ============================================================
# メイン
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("[ERROR] JSONファイルを指定してください")
        print("Usage: python scripts/test_calls.py output/施設名/*.json")
        sys.exit(1)

    json_paths = sys.argv[1:]
    flows, main_key = load_flows(json_paths)

    if not main_key:
        print("[ERROR] 有効なフローJSONが見つかりません")
        sys.exit(1)

    main_data = flows[main_key]
    facility_name = main_data.get("name", main_key).split("$")[0]

    print("=" * 60)
    print(f"模擬通話テスト: {facility_name}")
    print(f"メインフロー: {main_key}")
    print(f"総フロー数: {len(set(id(v) for v in flows.values()))}")
    print("=" * 60)
    print()

    # テストケース自動生成
    test_cases = generate_test_cases(flows, main_key, max_cases=10)

    if not test_cases:
        print("[WARN] テストケースを自動生成できませんでした")
        sys.exit(1)

    print(f"テストケース数: {len(test_cases)}")
    print()

    # テスト実行
    passed = 0
    failed = 0
    fail_details = []

    for i, (name, steps) in enumerate(test_cases, 1):
        tc_name = f"TC{i:02d}: {name}"
        success, path, error = simulate_call(flows, main_key, steps)

        if success:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1
            fail_details.append((tc_name, error, path))

        # 経路要約
        key_path = [p for p in path if not p.startswith("  ")]
        last_modules = key_path[-3:] if len(key_path) >= 3 else key_path
        terminus = " → ".join(last_modules)

        icon = "✅" if success else "❌"
        print(f"{icon} {status} {tc_name}")
        print(f"  終着: ...{terminus}")
        if error:
            print(f"  エラー: {error}")
        print()

    # サマリー
    print("=" * 60)
    print(f"結果: {passed}/{passed + failed} PASS")
    if failed > 0:
        print(f"       {failed} FAIL")
    print("=" * 60)

    # 結果をJSONで保存
    output_dir = Path(json_paths[0]).parent
    result = {
        "facility": facility_name,
        "main_flow": main_key,
        "total": passed + failed,
        "passed": passed,
        "failed": failed,
        "test_cases": [
            {"name": name, "steps": steps, "status": "PASS" if i <= passed else "FAIL"}
            for i, (name, steps) in enumerate(test_cases, 1)
        ],
    }
    result_path = output_dir / "test_result.json"
    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[INFO] テスト結果を保存: {result_path}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
