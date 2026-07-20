#!/usr/bin/env python3
"""
route_walker.py — フロー全ルート列挙 + 到達性検証

フローJSONの start モジュールから DFS で全ルートを列挙し、
全ルートが終端（Disconnect/Transfer/Jump to Flow）に到達するか検証する。
サブフローJSONを指定すると、Custom Jump to Flow 経由で連結走査する。

Usage (単体テスト用):
    python schemas/route_walker.py output/json/merged_xxx.json \
        --subflows output/json/draft_xxx_氏名聴取.json output/json/draft_xxx_電話番号聴取.json
"""

import json
import sys
from dataclasses import dataclass, field


# ============================================================
# データモデル
# ============================================================

@dataclass
class RouteStep:
    flow_name: str
    module_name: str
    condition: str = ""  # このモジュールに入った条件（表示用）

    def __repr__(self):
        if self.condition:
            return f"{self.module_name} [{self.condition}]"
        return self.module_name


@dataclass
class Route:
    path: list = field(default_factory=list)     # list[RouteStep]
    terminal: str = ""                           # 終端モジュール名
    terminal_type: str = ""                      # disconnect, transfer, jump_to_flow, dead_end, broken_ref, script_return
    classification: str = ""                     # 正常, 時間外, 非通知, リトライ上限, etc.


@dataclass
class RouteIssue:
    code: str       # R-1, R-2, etc.
    severity: str   # CRITICAL, WARNING
    message: str


@dataclass
class WalkResult:
    routes: list = field(default_factory=list)     # list[Route]
    issues: list = field(default_factory=list)     # list[RouteIssue]
    total_modules: int = 0
    reached_modules: set = field(default_factory=set)
    unreached_modules: list = field(default_factory=list)

    @property
    def coverage(self) -> float:
        if self.total_modules == 0:
            return 0.0
        return len(self.reached_modules) / self.total_modules * 100


# ============================================================
# ヘルパー
# ============================================================

def is_disconnect(mod: dict) -> bool:
    return "Disconnect" in mod.get("type", "")


def is_call_transfer(mod: dict) -> bool:
    return "Call Transfer" in mod.get("type", "")


def is_retry(mod_type: str) -> bool:
    return "Retry Counter" in mod_type


def is_jump_to_flow(mod: dict) -> bool:
    return "Jump to Flow" in mod.get("type", "")


def is_script(mod: dict) -> bool:
    return "$Script" in mod.get("type", "") or "@General$Script" in mod.get("type", "")


def is_save2db(mod: dict) -> bool:
    return "Persistence$save2db" in mod.get("type", "")


def resolve_flowname(mod: dict) -> str:
    """params.flowname から 'drjoy^' を除去してフロー名を返す"""
    raw = mod.get("params", {}).get("flowname", "")
    return raw.replace("drjoy^", "")


_ERROR_CONDITIONS = frozenset({"^TIMEOUT$", "^ERROR$", "^NO_RESULT$"})


def get_active_nexts(mod: dict) -> list[tuple[str, str]]:
    """(condition, nextModuleName) のリスト。空スロットは除外。
    業務パス（success/個別分岐）を先に、エラーパスを後に並べることで
    DFS探索で業務ルートが優先的に探索される。"""
    business = []
    errors = []
    for nxt in mod.get("next", []):
        target = nxt.get("nextModuleName", "")
        condition = nxt.get("condition", "")
        if target:
            if condition in _ERROR_CONDITIONS:
                errors.append((condition, target))
            else:
                business.append((condition, target))
    return business + errors


def get_retry_target(mod: dict, condition: str) -> str | None:
    """Retry Counter の true/false 遷移先を返す"""
    for nxt in mod.get("next", []):
        if nxt.get("condition", "") == condition:
            return nxt.get("nextModuleName", "") or None
    return None


def classify_route(route: Route) -> str:
    """ルートの分類ラベルを推定する"""
    path_names = [step.module_name for step in route.path]
    path_str = " ".join(path_names)

    if route.terminal_type == "dead_end":
        return "dead_end"
    if route.terminal_type == "broken_ref":
        return "broken_ref"

    # パス内のキーワードで分類
    if "時間外" in path_str:
        return "時間外"
    if "非通知" in path_str:
        return "非通知"

    # リトライ上限（No more パスを通っている）
    for step in route.path:
        if "リトライ" in step.module_name and step.condition == "false":
            return "リトライ上限"

    # リトライ経由の正常復帰
    for step in route.path:
        if "リトライ" in step.module_name and step.condition == "true":
            return "リトライ復帰"

    return "正常"


# ============================================================
# DFS ルート列挙
# ============================================================

def enumerate_routes(
    flows: dict[str, dict],
    start_flow_name: str,
    max_depth: int = 200,
    max_routes: int = 10000,
) -> list[Route]:
    """全ルートをDFSで列挙する

    Args:
        flows: {flow_name: flow_data} のマッピング
        start_flow_name: 開始フローの名前（flows のキー）
        max_depth: 最大探索深度（無限ループ防止）
        max_routes: 最大ルート数（組み合わせ爆発防止）
    """
    routes = []

    def dfs(
        flow_name: str,
        module_name: str,
        path: list,
        retry_counts: dict,
        flow_stack: list,
        entry_condition: str,
        visited: frozenset = frozenset(),
    ):
        # ルート数上限
        if len(routes) >= max_routes:
            return

        flow = flows.get(flow_name)
        if not flow:
            routes.append(Route(
                path=path,
                terminal=f"{flow_name}(フロー未検出)",
                terminal_type="broken_ref",
            ))
            return

        modules = flow.get("modules", {})

        # サイクル検出: 同一 (flow, module, retry_state) を再訪したらサイクル
        state_key = (flow_name, module_name, tuple(sorted(retry_counts.items())))
        if state_key in visited:
            routes.append(Route(
                path=path + [RouteStep(flow_name, module_name, entry_condition)],
                terminal=module_name,
                terminal_type="cycle",
            ))
            return
        visited = visited | {state_key}

        # 深度制限
        if len(path) >= max_depth:
            routes.append(Route(
                path=path,
                terminal=module_name,
                terminal_type="max_depth",
            ))
            return

        # モジュール存在チェック
        if module_name not in modules:
            routes.append(Route(
                path=path + [RouteStep(flow_name, module_name, entry_condition)],
                terminal=module_name,
                terminal_type="broken_ref",
            ))
            return

        mod = modules[module_name]
        step = RouteStep(flow_name, module_name, entry_condition)
        new_path = path + [step]

        # --- 終端: Disconnect ---
        if is_disconnect(mod):
            routes.append(Route(
                path=new_path,
                terminal=module_name,
                terminal_type="disconnect",
            ))
            return

        # --- 終端: Call Transfer ---
        if is_call_transfer(mod):
            routes.append(Route(
                path=new_path,
                terminal=module_name,
                terminal_type="transfer",
            ))
            return

        # --- Script（サブフロー結果返却 or 中間スクリプト）---
        if is_script(mod):
            is_return = flow_stack and module_name.startswith("script_結果返却")
            if is_return:
                # サブフロー完了 → メインフローに戻る
                parent_flow, parent_jump = flow_stack[-1]
                parent_modules = flows.get(parent_flow, {}).get("modules", {})
                parent_mod = parent_modules.get(parent_jump)
                if parent_mod:
                    parent_nexts = get_active_nexts(parent_mod)
                    if parent_nexts:
                        for cond, target in parent_nexts:
                            dfs(parent_flow, target, new_path,
                                retry_counts, flow_stack[:-1], cond, visited)
                    else:
                        routes.append(Route(
                            path=new_path,
                            terminal=parent_jump,
                            terminal_type="jump_to_flow",
                        ))
                return
            else:
                # メインフロー内のスクリプト or サブフロー内の中間スクリプト → 通常のnext遷移
                active = get_active_nexts(mod)
                if not active:
                    routes.append(Route(
                        path=new_path,
                        terminal=module_name,
                        terminal_type="script_return",
                    ))
                    return
                for cond, target in active:
                    dfs(flow_name, target, new_path, retry_counts, flow_stack, cond, visited)
                return

        # --- Custom Jump to Flow ---
        # サブフローは静的コピーで品質保証済みのため内部は走査しない。
        # flowname の解決可否（broken_ref）だけ確認し、
        # メインフロー側の next 接続を辿る（サブフロー経由ルートの到達性確認のみ）。
        if is_jump_to_flow(mod):
            subflow_name = resolve_flowname(mod)
            # flowname が解決できない場合は broken_ref
            if not subflow_name:
                routes.append(Route(
                    path=new_path,
                    terminal=f"{module_name}(flowname未設定)",
                    terminal_type="broken_ref",
                ))
                return
            # flowname が解決できるが登録されていない場合も broken_ref
            if flows and subflow_name not in flows:
                routes.append(Route(
                    path=new_path,
                    terminal=f"{subflow_name}(subflow未登録)",
                    terminal_type="broken_ref",
                ))
                return
            # サブフロー内部はスキップ → メインフローの next を辿る
            active = get_active_nexts(mod)
            if active:
                for cond, target in active:
                    dfs(flow_name, target, new_path, retry_counts, flow_stack, cond, visited)
            else:
                routes.append(Route(
                    path=new_path,
                    terminal=module_name,
                    terminal_type="jump_to_flow",
                ))
            return

        # --- Retry Counter ---
        if is_retry(mod.get("type", "")):
            key = (flow_name, module_name)
            count = retry_counts.get(key, 0)

            if count >= 1:
                # 2回目到達 → false（No more）のみ
                false_target = get_retry_target(mod, "false")
                if false_target:
                    dfs(flow_name, false_target, new_path,
                        retry_counts, flow_stack, "false", visited)
                else:
                    routes.append(Route(
                        path=new_path,
                        terminal=module_name,
                        terminal_type="dead_end",
                    ))
            else:
                # 初回 → false（上限到達）と true（リトライ）の両方を探索
                # false を先に探索することで終端パスを優先的に発見する
                new_counts = {**retry_counts, key: count + 1}
                false_target = get_retry_target(mod, "false")
                true_target = get_retry_target(mod, "true")
                if false_target:
                    dfs(flow_name, false_target, new_path,
                        retry_counts, flow_stack, "false", visited)
                if true_target:
                    dfs(flow_name, true_target, new_path,
                        new_counts, flow_stack, "true", visited)
                if not true_target and not false_target:
                    routes.append(Route(
                        path=new_path,
                        terminal=module_name,
                        terminal_type="dead_end",
                    ))
            return

        # --- 通常モジュール ---
        active = get_active_nexts(mod)
        if not active:
            # next が空配列 → 終端（Disconnect前の最終TTSなど）
            routes.append(Route(
                path=new_path,
                terminal=module_name,
                terminal_type="dead_end",
            ))
            return

        for cond, target in active:
            dfs(flow_name, target, new_path, retry_counts, flow_stack, cond, visited)

    # 開始
    start_mod = flows[start_flow_name].get("start", "")
    dfs(start_flow_name, start_mod, [], {}, [], "", frozenset())
    return routes


# ============================================================
# 検証
# ============================================================

def validate_routes(
    routes: list[Route],
    flows: dict[str, dict],
    max_routes: int = 10000,
) -> WalkResult:
    """列挙済みルートに対して到達性・カバレッジ等を検証する"""

    result = WalkResult(routes=routes)

    # 全モジュール数の算出（save2dbサブモジュールを除外）
    all_modules = set()
    for flow_name, flow_data in flows.items():
        for mod_name, mod in flow_data.get("modules", {}).items():
            if not is_save2db(mod):
                all_modules.add((flow_name, mod_name))
    result.total_modules = len(all_modules)

    # 到達モジュールの集計
    for route in routes:
        for step in route.path:
            result.reached_modules.add((step.flow_name, step.module_name))

    # ルート分類
    for route in routes:
        route.classification = classify_route(route)

    # --- R-1: dead end チェック ---
    for i, route in enumerate(routes):
        if route.terminal_type == "dead_end":
            result.issues.append(RouteIssue(
                code="R-1",
                severity="CRITICAL",
                message=f"ルート#{i+1}: dead end at「{route.terminal}」（nextが未接続または終端モジュールなし）",
            ))

    # --- R-2: broken ref チェック ---
    for i, route in enumerate(routes):
        if route.terminal_type == "broken_ref":
            result.issues.append(RouteIssue(
                code="R-2",
                severity="CRITICAL",
                message=f"ルート#{i+1}: 参照先が存在しない「{route.terminal}」",
            ))

    # --- R-3: モジュールカバレッジ ---
    unreached = all_modules - result.reached_modules
    result.unreached_modules = sorted(
        [f"{fn}:{mn}" for fn, mn in unreached],
    )
    if unreached:
        result.issues.append(RouteIssue(
            code="R-3",
            severity="WARNING",
            message=f"未到達モジュール {len(unreached)}件: "
                    + ", ".join(result.unreached_modules[:10])
                    + ("..." if len(unreached) > 10 else ""),
        ))

    # --- R-4: max_depth チェック ---
    for i, route in enumerate(routes):
        if route.terminal_type == "max_depth":
            result.issues.append(RouteIssue(
                code="R-4",
                severity="CRITICAL",
                message=f"ルート#{i+1}: 探索深度上限に到達（無限ループの可能性）",
            ))

    # --- R-5: サイクル検出 ---
    for i, route in enumerate(routes):
        if route.terminal_type == "cycle":
            result.issues.append(RouteIssue(
                code="R-5",
                severity="WARNING",
                message=f"ルート#{i+1}: サイクル検出 at「{route.terminal}」（同一状態で再訪）",
            ))

    # --- R-6: 探索打ち切り ---
    if len(routes) >= max_routes:
        result.issues.append(RouteIssue(
            code="R-6",
            severity="WARNING",
            message=f"探索ルート数が上限({max_routes})に到達したため打ち切り。"
                    f"カバレッジが実際より低く表示されている可能性があります。"
                    f"--max-routes で上限を引き上げてください。",
        ))

    return result


# ============================================================
# フローデータ読み込み
# ============================================================

def load_flows(main_path: str, subflow_paths: list[str] = None) -> tuple[dict, str]:
    """メインフロー + サブフローを読み込み、{flow_name: flow_data} を返す

    Returns:
        (flows_dict, main_flow_name)
    """
    flows = {}

    with open(main_path, encoding="utf-8") as f:
        main_data = json.load(f)
    main_name = main_data.get("name", "main")
    flows[main_name] = main_data

    for path in (subflow_paths or []):
        with open(path, encoding="utf-8") as f:
            sub_data = json.load(f)
        sub_name = sub_data.get("name", path)
        flows[sub_name] = sub_data

    return flows, main_name


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python schemas/route_walker.py <flow.json> [--subflows sub1.json sub2.json ...]")
        sys.exit(1)

    main_path = sys.argv[1]
    subflow_paths = []
    if "--subflows" in sys.argv:
        idx = sys.argv.index("--subflows")
        for i in range(idx + 1, len(sys.argv)):
            if sys.argv[i].startswith("--"):
                break
            subflow_paths.append(sys.argv[i])

    flows, main_name = load_flows(main_path, subflow_paths)
    print(f"読み込みフロー: {list(flows.keys())}")

    routes = enumerate_routes(flows, main_name)
    walk_result = validate_routes(routes, flows)

    print(f"\n=== ルート走査結果 ===")
    print(f"ルート数: {len(routes)}")
    print(f"カバレッジ: {len(walk_result.reached_modules)}/{walk_result.total_modules} "
          f"({walk_result.coverage:.1f}%)")
    print()

    for i, route in enumerate(routes):
        path_summary = " → ".join(str(step) for step in route.path[-8:])
        if len(route.path) > 8:
            path_summary = "... → " + path_summary
        icon = "✓" if route.terminal_type in ("disconnect", "transfer", "jump_to_flow", "script_return") else "✗"
        print(f"  {icon} Route {i+1} [{route.classification}]: {path_summary}")
        print(f"      終端: {route.terminal} ({route.terminal_type})")

    if walk_result.issues:
        print(f"\n--- 問題検出 ({len(walk_result.issues)}件) ---")
        for issue in walk_result.issues:
            print(f"  [{issue.severity}] {issue.code}: {issue.message}")

    if walk_result.unreached_modules:
        print(f"\n--- 未到達モジュール ---")
        for m in walk_result.unreached_modules:
            print(f"  - {m}")

    sys.exit(0 if not any(i.severity == "CRITICAL" for i in walk_result.issues) else 1)
