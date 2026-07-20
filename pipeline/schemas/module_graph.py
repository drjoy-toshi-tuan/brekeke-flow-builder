"""モジュール参照グラフユーティリティ

Brekeke フロー JSON 内で「あるモジュール名が他モジュールのどこに現れているか」を
generic にスキャンする汎用ヘルパー。validator (PROMPT-005)、orchestrator
(prompter contract 構築) 等から共通利用する。

設計方針 (memory `project_4layer_responsibility_model.md` 参照):
- 参照種別を enum でハードコードしない（CMR / script / OpenAI 連結 / RAG / save2db
  等のパターンが将来増えても自動的に拾えるように）
- caller モジュールのタイプとフィールド名を生記録、消費側 (prompter SKILL / validator)
  が解釈する
- 名前完全一致と部分一致 (script 本文に getModuleResult("OpenAI_xxx") として埋め込まれた
  ケース等) を両方拾う
"""
from __future__ import annotations

from typing import Any


def find_module_references(json_data: dict, target_name: str) -> list[dict]:
    """target_name が他モジュールのどこに現れているかを全件抽出。

    Args:
        json_data: フロー JSON (modules キーを持つ dict)
        target_name: 参照を探したいモジュール名（例: "OpenAI_受診希望日聴取_変更"）

    Returns:
        参照箇所のリスト。各要素は dict:
          - caller: 参照元モジュール名
          - caller_type: 参照元モジュールの type 文字列
          - ref_kind: 参照種別（生記録、enum 化しない）
              "next_transition"           - caller の next 配列の nextModuleName
              "params.<field>"            - caller の params の値として完全一致
              "params.<field>.embedded"   - caller の params の値（文字列）に部分一致
                                           （script 本文の getModuleResult("xxx") 等）
              "subs.moduleName"           - caller の subs[].moduleName
          - condition: next 経由の場合の condition 文字列（それ以外は None）

    Examples:
        >>> refs = find_module_references(json_data, "OpenAI_受診希望日聴取_変更")
        >>> # [{"caller": "script_受診希望日_ゲート判定_変更",
        >>> #   "caller_type": "@General$Script",
        >>> #   "ref_kind": "params.module"}, ...]
    """
    refs: list[dict] = []
    modules = json_data.get("modules", {})
    if not isinstance(modules, dict):
        return refs

    for caller_name, caller in modules.items():
        if caller_name == target_name:
            continue
        if not isinstance(caller, dict):
            continue
        caller_type = caller.get("type", "")

        # ① next 経由の遷移先として参照
        for n in caller.get("next") or []:
            if not isinstance(n, dict):
                continue
            if n.get("nextModuleName") == target_name:
                refs.append({
                    "caller": caller_name,
                    "caller_type": caller_type,
                    "ref_kind": "next_transition",
                    "condition": n.get("condition"),
                })

        # ② params 値として参照
        params = caller.get("params") or {}
        if isinstance(params, dict):
            for k, v in params.items():
                if v == target_name:
                    refs.append({
                        "caller": caller_name,
                        "caller_type": caller_type,
                        "ref_kind": f"params.{k}",
                        "condition": None,
                    })
                elif isinstance(v, str) and v != target_name and target_name in v:
                    # script 本文に getModuleResult("OpenAI_xxx") のように埋まっているケース
                    refs.append({
                        "caller": caller_name,
                        "caller_type": caller_type,
                        "ref_kind": f"params.{k}.embedded",
                        "condition": None,
                    })

        # ③ subs 値として参照
        for sub in caller.get("subs") or []:
            if isinstance(sub, dict) and sub.get("moduleName") == target_name:
                refs.append({
                    "caller": caller_name,
                    "caller_type": caller_type,
                    "ref_kind": "subs.moduleName",
                    "condition": None,
                })

    return refs


def find_cmr_consumers(json_data: dict, target_name: str) -> list[dict]:
    """target_name を `module1Name` / `module2Name` で参照する CMR を抽出。

    PROMPT-005 など、CMR の slot 値 vs OpenAI 出力仕様の整合検証で使用。
    返り値は CMR モジュール本体に CMR 視点の追加情報を載せた dict のリスト。

    Returns:
        各要素:
          - cmr_name: CMR モジュール名
          - cmr_module: CMR モジュールの dict 全体
          - module_index: 1 or 2 (module1Name / module2Name どちらで参照されたか)
          - slot_values: [(idx, value), ...] 非空の moduleXValue1〜10
          - other_branch: ^0$ next の dict (label / nextModuleName)、無ければ None
    """
    consumers: list[dict] = []
    modules = json_data.get("modules", {})
    if not isinstance(modules, dict):
        return consumers

    for cmr_name, cmr in modules.items():
        if not isinstance(cmr, dict):
            continue
        if "ContextMatchRouter" not in cmr.get("type", ""):
            continue
        params = cmr.get("params") or {}
        if not isinstance(params, dict):
            continue

        for idx in (1, 2):
            ref_field = f"module{idx}Name"
            if params.get(ref_field) != target_name:
                continue

            slot_values: list[tuple[int, str]] = []
            for slot in range(1, 11):
                v = params.get(f"module{idx}Value{slot}", "")
                if v:
                    slot_values.append((slot, v))

            other_branch = None
            for n in cmr.get("next") or []:
                if isinstance(n, dict) and n.get("condition") == "^0$":
                    other_branch = {
                        "label": n.get("label", ""),
                        "nextModuleName": n.get("nextModuleName", ""),
                    }
                    break

            consumers.append({
                "cmr_name": cmr_name,
                "cmr_module": cmr,
                "module_index": idx,
                "slot_values": slot_values,
                "other_branch": other_branch,
            })

    return consumers
