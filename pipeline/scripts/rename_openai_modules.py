#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rename_openai_modules.py — OpenAI_*/openAI_* と命名された決定論 Script モジュールを
`script_*` にリネームし、フロー内の全参照を追従させる決定論ユーティリティ（issue #236）。

背景:
    generate_by_OpenAI モジュールを決定論スクリプト（yes_no_classifier / n_choice /
    department_classifier / reservation_date_classifier 等）へ**手動で置換**した際、
    モジュール本体の type/params は `@General$Script` に変わるが、モジュール名と分岐側の
    参照名が `OpenAI_*` のまま残ってしまうケースがある（恵佑会札幌病院 260629 で発生）。
    factory-v2 の決定論生成器（scaffold_generator.py）は部品を `script_*` で正しく命名する
    ため本残骸を作らないが、既存 bivr の surgical な手動置換ではツールが無く手作業だった。

このモジュールが提供する決定論変換:
    検出: `@General$Script`（type に "Script"/"script" を含む）かつ名前が `OpenAI_` /
          `openAI_` で始まるモジュール。**generate_by_OpenAI 等の真の OpenAI モジュールは
          type に Script を含まないため対象外**（誤リネーム防止）。
    改名: `OpenAI_用件確認` → `script_用件確認`（接頭辞を `script_` へ）。
          付随する補助モジュール `saveDefault-OpenAI_用件確認` →
          `saveDefault-script_用件確認` も対で追従する。
    参照追従: modules キー / 各モジュールの `name` / `next[].nextModuleName` /
          `subs[].moduleName`,`label` / CMR `params.module1Name`,`module2Name` /
          `params.module`（clinical_department_classifier 等）/ `params.script` 本文中の
          引用参照（getModuleResult("OLD") 等）/ フローの `start`。

2 つの入口がこの核を共有する:
    - scripts/auto_fixer.py の op `rename_module`（パイプライン自動修復・validator SCR-001 が起票）
    - tools/rename_openai_to_script.py（手動編集 bivr/JSON 用 CLI）
"""

import json
from collections import OrderedDict

# validator.py SCR-001 と同一判定（type に "Script"/"script" を含む = @General$Script 等）
_SCRIPT_TYPE_MARKERS = ("Script", "script")
# OpenAI 残骸の接頭辞（本番では OpenAI_ が主、復唱系で openAI_ も使われる）
_OPENAI_PREFIXES = ("OpenAI_", "openAI_")
# 補助モジュールの接頭辞（本体名を内包するもの）。本体 OLD→NEW に対し PREFIX+OLD→PREFIX+NEW を対で追従。
_AUX_PREFIXES = ("saveDefault-",)
# モジュール名を保持しうる params フィールド（参照）
# nodeName: drjoy^Text To Speech$Re-confirmation node data が復唱対象モジュール名を持つ参照サイト
# （#348・追従漏れで復唱が旧名を指し壊れる。厚木/西宮パッチが自前追従していた核の欠落を是正）。
_PARAM_REF_KEYS = ("module1Name", "module2Name", "module", "nodeName")


def _is_script_type(mod_type: str) -> bool:
    return any(m in (mod_type or "") for m in _SCRIPT_TYPE_MARKERS)


def _strip_openai_prefix(name: str) -> str | None:
    """OpenAI_/openAI_ 接頭を script_ に置換した新名を返す。接頭が無ければ None。"""
    for pfx in _OPENAI_PREFIXES:
        if name.startswith(pfx):
            return "script_" + name[len(pfx):]
    return None


def detect_openai_script_renames(flow: dict) -> "OrderedDict[str, str]":
    """1 フロー（modules を持つ JSON）から OpenAI_* な Script モジュールの old→new 写像を作る。

    付随する saveDefault-OpenAI_* 補助モジュールも対で写像に含める。
    new 名が既存モジュールと衝突する（かつその既存が別途リネームされない）場合は
    その 1 件をスキップする（決定論・安全側）。
    戻り値は挿入順を保つ OrderedDict。
    """
    modules = flow.get("modules", {})
    mapping: "OrderedDict[str, str]" = OrderedDict()
    if not isinstance(modules, dict):
        return mapping

    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        if not _is_script_type(mod.get("type", "")):
            continue
        new_name = _strip_openai_prefix(name)
        if new_name and new_name != name:
            mapping[name] = new_name

    # 補助モジュールの対追従（本体が改名される場合のみ）
    for old, new in list(mapping.items()):
        for pfx in _AUX_PREFIXES:
            aux_old = pfx + old
            if aux_old in modules:
                mapping[aux_old] = pfx + new

    # 衝突ガード: new がフロー内に既存しており、その既存が別途改名で消えるのでなければスキップ
    safe: "OrderedDict[str, str]" = OrderedDict()
    removed = set(mapping.keys())
    for old, new in mapping.items():
        if new in modules and new not in removed:
            continue  # 衝突 → スキップ
        if new in safe.values():
            continue  # 同一 new への二重写像を防ぐ
        safe[old] = new
    return safe


def _rename_in_script_body(body: str, mapping: dict) -> str:
    """script 本文中の引用参照（"OLD" / 'OLD'）を NEW に置換する。

    自由テキストの全置換は過剰一致の恐れがあるため、**引用符で囲まれたトークン**のみを
    対象にする（getModuleResult("OLD") / getObject('OLD.'+rid) 等の参照を想定）。
    """
    if not isinstance(body, str) or not body:
        return body
    for old, new in mapping.items():
        body = body.replace('"' + old + '"', '"' + new + '"')
        body = body.replace("'" + old + "'", "'" + new + "'")
    return body


def apply_rename_mapping(flow: dict, mapping: dict) -> list[str]:
    """old→new 写像をフロー全体に決定論的に適用する。変更内容の説明リストを返す。

    冪等: 写像が空、または対象が無ければ何も変更しない。
    """
    changes: list[str] = []
    if not mapping:
        return changes
    modules = flow.get("modules", {})
    if not isinstance(modules, dict):
        return changes

    # 1) modules キーの張り替え（順序保持）
    new_modules: "OrderedDict[str, dict]" = OrderedDict()
    for name, mod in modules.items():
        new_key = mapping.get(name, name)
        new_modules[new_key] = mod
    if list(new_modules.keys()) != list(modules.keys()):
        changes.append(f"modules キー: {sum(1 for k in modules if k in mapping)} 件改名")
    # 元 dict を入れ替え（dict のまま保つ）
    flow["modules"] = dict(new_modules)
    modules = flow["modules"]

    # 2) start 参照
    if flow.get("start") in mapping:
        old = flow["start"]
        flow["start"] = mapping[old]
        changes.append(f"start: '{old}' → '{flow['start']}'")

    # 3) 各モジュール内の参照
    for key, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        # name フィールド（modules キーと一致する内部名）
        if mod.get("name") in mapping:
            mod["name"] = mapping[mod["name"]]
        # next[].nextModuleName
        for nxt in mod.get("next", []) or []:
            if isinstance(nxt, dict) and nxt.get("nextModuleName") in mapping:
                nxt["nextModuleName"] = mapping[nxt["nextModuleName"]]
        # subs[].moduleName / label
        for sub in mod.get("subs", []) or []:
            if not isinstance(sub, dict):
                continue
            if sub.get("moduleName") in mapping:
                sub["moduleName"] = mapping[sub["moduleName"]]
            if sub.get("label") in mapping:
                sub["label"] = mapping[sub["label"]]
        # params 参照フィールド + script 本文
        params = mod.get("params")
        if isinstance(params, dict):
            for pk in _PARAM_REF_KEYS:
                if params.get(pk) in mapping:
                    params[pk] = mapping[params[pk]]
            if isinstance(params.get("script"), str):
                new_body = _rename_in_script_body(params["script"], mapping)
                if new_body != params["script"]:
                    params["script"] = new_body

    for old, new in mapping.items():
        changes.append(f"'{old}' → '{new}'")
    return changes


def expand_mapping_with_aux(flow: dict, single: dict) -> "OrderedDict[str, str]":
    """単一 old→new（auto_fixer の fix_action 由来）に補助モジュール対を足して返す。"""
    modules = flow.get("modules", {})
    mapping: "OrderedDict[str, str]" = OrderedDict()
    for old, new in single.items():
        mapping[old] = new
        for pfx in _AUX_PREFIXES:
            aux_old = pfx + old
            if isinstance(modules, dict) and aux_old in modules:
                mapping[aux_old] = pfx + new
    return mapping


def rename_openai_scripts_in_flow(flow: dict) -> list[str]:
    """1 フローに対し自動検出 → 適用までを行う高水準 API（CLI/テスト用）。"""
    mapping = detect_openai_script_renames(flow)
    if not mapping:
        return []
    return apply_rename_mapping(flow, mapping)


# ---------------------------------------------------------------------------
# 整合性検証（issue #273）
#
# 手動サージカルパッチ（.bivr 直編集）はパイプライン（validator SCR-001 / auto_fixer /
# T-001 / T-003 / CMR-001）を通らないため、置換後に「残骸ゼロ・参照ズレゼロ」を機械的に
# 確認する手段が無かった（つくばセントラル 260626 で再発）。以下はその独立チェック核。
# validator.py の T-001/T-003/CMR-001/OAI と同一の「参照先実在」判定を rename 核と同居させ、
# 手動フロー JSON に単独適用（CLI `--verify`）できるようにしたもの。
# ---------------------------------------------------------------------------

# モジュール名を要求する参照サイトの params キー（validator CMR-001/OAI と同一）
# nodeName: Re-confirmation node data の復唱対象モジュール参照（#348・ダングリング検出の穴を塞ぐ）。
_REF_PARAM_KEYS = ("module1Name", "module2Name", "module", "nodeName")


def _is_variable_ref(value) -> bool:
    """Brekeke の変数フォーマット `<%var%>` はモジュール名でないため参照検査から除外。"""
    return isinstance(value, str) and value.startswith("<%") and value.endswith("%>")


def detect_openai_residue(flow: dict) -> list[str]:
    """`@General$Script` 型なのに OpenAI_*/openAI_* 命名のまま残っているモジュール名を返す。

    validator SCR-001 と同一ドメイン（type に Script を含む × OpenAI_/openAI_ 接頭）。
    generate_by_OpenAI 本体（type に Script を含まない）は対象外＝誤検出しない。
    空リストなら残骸なし。挿入順を保つ。
    """
    residue: list[str] = []
    modules = flow.get("modules", {})
    if not isinstance(modules, dict):
        return residue
    for name, mod in modules.items():
        if isinstance(mod, dict) and _is_script_type(mod.get("type", "")) and _strip_openai_prefix(name):
            residue.append(name)
    return residue


def detect_dangling_references(flow: dict) -> list[dict]:
    """モジュール名を要求する全参照サイトのうち、実在しないモジュールを指すものを返す。

    参照サイト（validator T-001/T-003/CMR-001/OAI と同一集合）:
      - flow['start']
      - modules[*].next[].nextModuleName
      - modules[*].subs[].moduleName
      - modules[*].params.module1Name / module2Name / module / nodeName
    `<%var%>` 形式と空文字はスキップ（Brekeke 仕様上モジュール名でない）。
    部分リネーム（本体は改名したが参照を取りこぼした）を機械的に捕捉する。
    戻り値の各要素: {"module": 起点（or "(flow)"）, "field": 参照サイト, "target": 壊れた参照先}
    """
    dangling: list[dict] = []
    modules = flow.get("modules", {})
    if not isinstance(modules, dict):
        return dangling
    names = set(modules.keys())

    def _check(owner: str, field: str, target) -> None:
        if not target or not isinstance(target, str) or _is_variable_ref(target):
            return
        if target not in names:
            dangling.append({"module": owner, "field": field, "target": target})

    _check("(flow)", "start", flow.get("start", ""))
    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        for i, nxt in enumerate(mod.get("next", []) or []):
            if isinstance(nxt, dict):
                _check(name, f"next[{i}].nextModuleName", nxt.get("nextModuleName", ""))
        for i, sub in enumerate(mod.get("subs", []) or []):
            if isinstance(sub, dict):
                _check(name, f"subs[{i}].moduleName", sub.get("moduleName", ""))
        params = mod.get("params")
        if isinstance(params, dict):
            for pk in _REF_PARAM_KEYS:
                _check(name, f"params.{pk}", params.get(pk, ""))
    return dangling


def verify_flow_integrity(flow: dict) -> dict:
    """1 フローの整合性検証。{"residue": [...], "dangling": [...]} を返す。

    両方空なら健全。CLI（--verify）と受入テストが共有する高水準 API。
    """
    return {
        "residue": detect_openai_residue(flow),
        "dangling": detect_dangling_references(flow),
    }
