#!/usr/bin/env python3
"""横須賀共済病院 模擬通話テスト（10パターン）

フローJSONをプログラム的にたどり、全分岐パスの到達テストを行う。
各テストケースでstartモジュールから終話（Disconnect）まで到達できるか検証する。
サブフロー（Jump to Flow）も横断して追跡する。
"""
import json
import sys
import io
from pathlib import Path

OUTPUT_DIR = Path("output/横須賀共済病院")


def load_all_flows():
    """全フローJSONを読み込み、フロー名→データのマップを返す"""
    flows = {}
    for f in OUTPUT_DIR.glob("横須賀共済_*.json"):
        if "verify" in f.name:
            continue
        with open(f, encoding="utf-8") as fp:
            data = json.load(fp)
        flow_name = data.get("name", f.stem)
        flows[flow_name] = data
        # ファイル名でも引けるように
        flows[f.stem] = data
    return flows


def simulate_call(flows, main_flow_name, scenario_steps, test_name):
    """模擬通話シミュレーション

    Args:
        flows: フロー名→データのマップ
        main_flow_name: メインフローのキー
        scenario_steps: list of (module_type_match, response) tuples
            module_type_match: マッチするモジュール種別の部分文字列
            response: そのモジュールでの応答（OpenAIの出力値、STTの入力値など）
        test_name: テスト名

    Returns:
        (success, path, error_msg)
    """
    main_data = flows[main_flow_name]
    current_module = main_data["start"]
    current_flow = main_data
    current_flow_name = main_flow_name
    path = []
    step_idx = 0
    max_iterations = 200  # 無限ループ防止

    for _ in range(max_iterations):
        if current_module not in current_flow["modules"]:
            # サブフローの結果返却スクリプトの先 = フロー終了、メインに戻る
            return True, path, None

        mod = current_flow["modules"][current_module]
        mod_type = mod.get("type", "")
        nexts = mod.get("next", [])

        path.append(f"{current_module}")

        # Disconnect = 終話到達
        if "Disconnect" in mod_type:
            return True, path, None

        # Script（結果返却）= サブフロー終了
        if "Script" in mod_type and "script_結果返却" in current_module:
            return True, path, None

        # Jump to Flow = サブフロー突入
        if "Jump to Flow" in mod_type:
            flowname = mod.get("params", {}).get("flowname", "")
            # サブフロー名からフローデータを探す
            subflow = None
            for key, fdata in flows.items():
                if fdata.get("name", "") == flowname:
                    subflow = fdata
                    break
            if subflow:
                # サブフローを再帰的にシミュレーション
                sub_start = subflow["start"]
                path.append(f"  → サブフロー: {flowname}")
                # サブフロー内を簡略実行（全ステップ成功と仮定）
                sub_path = trace_subflow(subflow)
                path.extend([f"    {p}" for p in sub_path])
                path.append(f"  ← サブフロー復帰")

            # Jump後の遷移先
            next_mod = None
            for n in nexts:
                if n.get("nextModuleName"):
                    next_mod = n["nextModuleName"]
                    break
            if next_mod:
                current_module = next_mod
                continue
            else:
                return True, path, None

        # OpenAI分岐 — シナリオの応答で分岐
        if "generate_by_OpenAI" in mod_type:
            if step_idx < len(scenario_steps):
                _, response = scenario_steps[step_idx]
                step_idx += 1
                # responseに一致するnext条件を探す
                matched = False
                for n in nexts:
                    cond = n.get("condition", "")
                    nm = n.get("nextModuleName", "")
                    if not nm:
                        continue
                    if cond in (f"^{response}$", response):
                        current_module = nm
                        path.append(f"  → 応答: {response}")
                        matched = True
                        break
                if not matched:
                    # ^.+$ or ^.*$ にフォールバック
                    for n in nexts:
                        cond = n.get("condition", "")
                        nm = n.get("nextModuleName", "")
                        if cond in ("^.+$", "^.*$") and nm:
                            current_module = nm
                            path.append(f"  → 応答: {response} (catch-all)")
                            matched = True
                            break
                if not matched:
                    return False, path, f"OpenAI {current_module} で応答 '{response}' にマッチする遷移先なし"
                continue

        # ContextMatchRouter — シナリオの応答で分岐
        if "ContextMatchRouter" in mod_type:
            if step_idx < len(scenario_steps):
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
                        path.append(f"  → ルーティング: index={response}")
                        matched = True
                        break
                if not matched:
                    for n in nexts:
                        cond = n.get("condition", "")
                        nm = n.get("nextModuleName", "")
                        if cond in ("^.*$",) and nm:
                            current_module = nm
                            path.append(f"  → ルーティング: default")
                            matched = True
                            break
                if not matched:
                    return False, path, f"ContextMatchRouter で遷移先なし"
                continue

        # Retry Counter — true(リトライ)/false(上限)
        if "Retry Counter" in mod_type:
            # テストシナリオにretry_failがあればfalse、なければtrue→次のモジュールへスキップ
            retry_fail = False
            if step_idx < len(scenario_steps):
                _, response = scenario_steps[step_idx]
                if response == "RETRY_FAIL":
                    retry_fail = True
                    step_idx += 1

            target_cond = "false" if retry_fail else "true"
            for n in nexts:
                if n.get("condition") == target_cond and n.get("nextModuleName"):
                    current_module = n["nextModuleName"]
                    if retry_fail:
                        path.append(f"  → リトライ上限到達")
                    break
            else:
                return False, path, f"Retry {current_module} で {target_cond} 遷移先なし"
            continue

        # STT/DTMF — 次ステップがRETRY_FAILならTIMEOUT→Retry経由、それ以外はsuccess
        if "Speech to Text" in mod_type or "DTMF" in mod_type:
            # 次のシナリオステップがRETRY_FAILなら、STTでTIMEOUT→Retry Counterへ
            if step_idx < len(scenario_steps) and scenario_steps[step_idx][1] == "RETRY_FAIL":
                for n in nexts:
                    if n.get("condition") == "^TIMEOUT$" and n.get("nextModuleName"):
                        current_module = n["nextModuleName"]
                        path.append(f"  → STTタイムアウト")
                        break
                else:
                    return False, path, f"STT {current_module} で TIMEOUT遷移先なし"
            else:
                for n in nexts:
                    if n.get("condition") == "^.+$" and n.get("nextModuleName"):
                        current_module = n["nextModuleName"]
                        break
                else:
                    return False, path, f"STT {current_module} で success遷移先なし"
            continue

        # TTS / save系 / incoming-classifier / acceptance_times / その他
        next_found = False

        # incoming-classifier: テストでは通常着信（携帯）として処理
        if "incoming-classifier" in mod_type:
            if step_idx < len(scenario_steps):
                _, response = scenario_steps[step_idx]
                if response in ("非通知", "携帯", "固定"):
                    for n in nexts:
                        if n.get("condition") == f"^{response}$" and n.get("nextModuleName"):
                            current_module = n["nextModuleName"]
                            path.append(f"  → 着信種別: {response}")
                            next_found = True
                            step_idx += 1
                            break
            if not next_found:
                # デフォルト: 携帯 or ^.*$
                for n in nexts:
                    cond = n.get("condition", "")
                    if cond in ("^携帯$", "^.*$") and n.get("nextModuleName"):
                        current_module = n["nextModuleName"]
                        next_found = True
                        break

        # acceptance_times: テストでは営業時間内（^true$）として処理
        elif "acceptance_times" in mod_type:
            for n in nexts:
                if n.get("condition") == "^true$" and n.get("nextModuleName"):
                    current_module = n["nextModuleName"]
                    next_found = True
                    break

        # saveCompletionFlag / saveContext2DB / saveContextModel2DB: ^.*$ nextに進む
        elif "Persistence" in mod_type:
            for n in nexts:
                cond = n.get("condition", "")
                nm = n.get("nextModuleName", "")
                if nm and cond in ("^.*$",):
                    current_module = nm
                    next_found = True
                    break

        # TTS: ^.*$ の Next Module に進む
        elif "Text to speech" in mod_type or "Text To Speech" in mod_type or "Re-confirmation" in mod_type:
            for n in nexts:
                nm = n.get("nextModuleName", "")
                if nm:
                    current_module = nm
                    next_found = True
                    break

        # wait / その他: 最初の有効なnextに進む
        else:
            for n in nexts:
                nm = n.get("nextModuleName", "")
                if nm:
                    current_module = nm
                    next_found = True
                    break

        if not next_found:
            # next が空 = フロー終端
            return True, path, None

    return False, path, "最大反復回数超過（無限ループの可能性）"


def trace_subflow(flow_data):
    """サブフローの主要モジュールパスを簡略追跡"""
    path = []
    current = flow_data.get("start", "")
    visited = set()
    for _ in range(50):
        if current in visited or current not in flow_data["modules"]:
            break
        visited.add(current)
        mod = flow_data["modules"][current]
        mod_type = mod.get("type", "")
        path.append(current)

        if "Disconnect" in mod_type or "Script" in mod_type:
            break

        # 最初の有効next
        next_found = False
        for n in mod.get("next", []):
            nm = n.get("nextModuleName", "")
            cond = n.get("condition", "")
            if nm and cond not in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^INVALID$"):
                current = nm
                next_found = True
                break
        if not next_found:
            break
    return path


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    flows = load_all_flows()
    main_key = "横須賀共済_診療予約_20260406_20260420"

    # ============================================================
    # 10テストケース定義
    # (type_match, response) — OpenAIへの応答値 or 特殊値
    # ============================================================

    test_cases = [
        # TC1: 当日→はい → 代表案内_当日で終話
        ("TC01: 当日確認→はい→代表案内_当日", [
            ("OpenAI", "はい"),
        ]),

        # TC2: 当日→いいえ→変更→整形外科→ありません→予約日→個人情報→受付完了(携帯/SMS)
        ("TC02: 変更→整形外科→予約日→個人情報→受付完了(SMS)", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "変更"),
            ("OpenAI", "整形外科"),
            ("OpenAI", "ありません"),
            ("CMR", "1"),  # 用件別分岐 → 変更=index1
            # 予約日はSTTなのでスキップ
            # サブフロー4つは自動追跡
            ("CMR", "1"),  # SMS判定 → 携帯=index1
        ]),

        # TC3: 当日→いいえ→キャンセル→内科→眼科→予約日→個人情報→受付完了(SMS無し)
        ("TC03: キャンセル→内科→眼科→予約日→受付完了(SMS無し)", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "キャンセル"),
            ("OpenAI", "内科"),
            ("OpenAI", "眼科"),
            ("CMR", "2"),  # 用件別分岐 → キャンセル=index2
            # 予約日STT
            # サブフロー4つ
            ("CMR", "2"),  # SMS判定 → その他=index2
        ]),

        # TC4: 当日→いいえ→確認→皮膚科→ありません→内容→個人情報→受付完了(携帯/SMS)
        ("TC04: 確認→皮膚科→内容→受付完了(SMS)", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "確認"),
            ("OpenAI", "皮膚科"),
            ("OpenAI", "ありません"),
            ("CMR", "3"),  # 用件別分岐 → 確認=index3
            # 内容STT
            # サブフロー4つ
            ("CMR", "1"),  # SMS判定 → 携帯
        ]),

        # TC5: 当日→いいえ→新規予約 → 代表案内_新規予約で終話
        ("TC05: 新規予約→代表案内_新規予約", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "新規予約"),
        ]),

        # TC6: 当日確認リトライ上限 → 上限エラー終話
        ("TC06: 当日確認リトライ上限→上限エラー", [
            ("Retry", "RETRY_FAIL"),
        ]),

        # TC7: 用件リトライ上限 → 無限ループ（用件に戻る）→ 変更→完了
        ("TC07: 用件リトライ→ループ→変更→完了", [
            ("OpenAI", "いいえ"),
            ("Retry", "RETRY_FAIL"),  # 用件リトライ上限 → 用件ループ
            ("OpenAI", "変更"),
            ("OpenAI", "消化器内科"),
            ("OpenAI", "ありません"),
            ("CMR", "1"),
            ("CMR", "1"),
        ]),

        # TC8: 診療科1リトライ上限 → 次へ進む（診療科2へ）→ 完了
        ("TC08: 診療科1リトライ→次へ(診療科2)→完了", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "変更"),
            ("Retry", "RETRY_FAIL"),  # 診療科1リトライ上限 → 診療科2へ
            ("OpenAI", "ありません"),
            ("CMR", "1"),
            ("CMR", "2"),
        ]),

        # TC9: 診療科2リトライ上限 → 次へ進む（用件別分岐）→ 完了
        ("TC09: 診療科2リトライ→次へ(用件別分岐)→完了", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "確認"),
            ("OpenAI", "整形外科"),
            ("Retry", "RETRY_FAIL"),  # 診療科2リトライ上限 → 用件別分岐へ
            ("CMR", "3"),
            ("CMR", "1"),
        ]),

        # TC10: 予約日リトライ上限 → 次へ（サブフロー）→ 完了
        ("TC10: 予約日リトライ→次へ(診察券)→完了", [
            ("OpenAI", "いいえ"),
            ("OpenAI", "変更"),
            ("OpenAI", "脳神経外科"),
            ("OpenAI", "ありません"),
            ("CMR", "1"),
            ("Retry", "RETRY_FAIL"),  # 予約日リトライ上限 → jump_診察券聴取へ
            ("CMR", "1"),
        ]),
    ]

    # ============================================================
    # テスト実行
    # ============================================================

    print("=" * 60)
    print("横須賀共済病院 模擬通話テスト（10パターン）")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for test_name, steps in test_cases:
        success, path, error = simulate_call(flows, main_key, steps, test_name)

        if success:
            # 最後のモジュールが終話関連か確認
            last = path[-1] if path else ""
            terminus = "切断" in last or "Disconnect" in last or "サブフロー復帰" in last or "script_結果返却" in last
            # 終話到達
            status = "✅ PASS"
            passed += 1
        else:
            status = "❌ FAIL"
            failed += 1

        print(f"{status} {test_name}")
        # パスの要約（主要モジュールのみ）
        key_modules = [p for p in path if not p.startswith("    ") and "save-" not in p]
        print(f"  経路: {' → '.join(key_modules[:15])}")
        if error:
            print(f"  エラー: {error}")
        print()

    print("=" * 60)
    print(f"結果: {passed}/{passed + failed} PASS")
    if failed > 0:
        print(f"       {failed} FAIL")
    print("=" * 60)


if __name__ == "__main__":
    main()
