#!/usr/bin/env python3
"""
block_mapper.py -- モジュール名 → ブロック名の逆引きマッピング

設計書 YAML の scenario_flow から各ブロックに含まれるモジュール名を計算し、
モジュール名 → ブロック名 の辞書を生成する。
fixer がブロック単位で修正範囲を絞るために使用。

Usage:
    from block_mapper import build_module_to_block_map
    mapping = build_module_to_block_map(yaml_path)
    block_name = mapping.get("OpenAI_用件確認", None)  # → "用件確認"
"""

import sys
from pathlib import Path

try:
    import yaml as _yaml
except ImportError:
    print("Error: PyYAML が必要です", file=sys.stderr)
    sys.exit(1)


# 各ブロック型に含まれるモジュール名のテンプレート（{step} を置換して使用）
BLOCK_MODULE_TEMPLATES = {
    "opening": [
        "冒頭",
        "コンテキスト設定",
        "着信電話番号分類",
        "受付時間判定",  # use_acceptance_times の場合のみ
    ],
    "announcement": [
        "{step}",
        "save-{step}",
    ],
    "hearing": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "save-入力_{step}",
        "OpenAI_{step}",
        "リトライ_{step}",
        "save-リトライ_{step}",
        # echo_back: true の場合
        "復唱_{step}",
        "入力_{step}_復唱",
        "save-入力_{step}_復唱",
        "openAI_{step}_復唱",
        "リトライ_{step}_復唱",
        "save-リトライ_{step}_復唱",
        "ContextMatchRouter_{step}_復唱後",  # enum + echo_back の場合
        # 多段分岐（条件数 > スロット上限の場合）
        "script_{step}_群分類",
    ] + [f"ContextMatchRouter_{{step}}_群{i}" for i in range(1, 11)],
    "subflow": [
        "{step}",
    ],
    "context_match_router": [
        "{step}",
    ],
    "script": [
        "{step}",
    ],
    "date_of_call_classifier": [
        "{step}",
    ],
    "call_transfer": [
        "{step}",
    ],
    "termination": [
        # termination_ref から導出（後段で処理）
    ],
    # Pattern C: DTMF 分離 hearing で生成される saveContext2DB 群はブロック側で動的計算
    # （dtmf_options[].label に依存するためテンプレ展開不可）
    "cmr_chain": [
        # 直列 CMR は後段で _cmr_chain_module_names() で動的生成
    ],
    # ファーストクラス slot エイリアス (2026-07-09 追加)
    "patient_name": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "save-入力_{step}",
        "リトライ_{step}",
        "save-リトライ_{step}",
    ],
    "dob": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "save-入力_{step}",
        "復唱_{step}",
        "入力_{step}_確認",
        "save-入力_{step}_確認",
        "リトライ_{step}",
        "save-リトライ_{step}",
        "リトライ_{step}_確認",
        "save-リトライ_{step}_確認",
        "script_{step}_確認分類",
    ],
    "phone": [
        "着信分類_{step}",
        "設定_{step}_ANI番号",
        "正規化_{step}_ANI",
        "復唱_{step}_ANI",
        "入力_{step}_ANI確認",
        "save-{step}_ANI復唱",
        "リトライ_{step}_ANI確認",
        "script_{step}_ANI確認分類",
        "聴取_{step}_連絡先",
        "入力_{step}_連絡先",
        "save-{step}_連絡先",
        "正規化_{step}_連絡先",
        "復唱_{step}_連絡先",
        "入力_{step}_連絡先確認",
        "save-{step}_連絡先復唱",
        "リトライ_{step}_連絡先",
        "リトライ_{step}_連絡先確認",
        "script_{step}_連絡先確認分類",
        "script_{step}_種別判別",
        "設定_{step}_ANIフォールバック",
        "設定_{step}_phonetype携帯",
        "設定_{step}_phonetypeその他",
        "script_{step}_連絡先なし判定",  # next_no_phone 指定時のみ生成
    ],
    # 新規ブロック型 (2026-07-09 追加)
    "intent": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "リトライ_{step}",
        "script_{step}",
    ],
    "phone_branch": [
        "{step}",
    ],
    "clinical_department": [
        "{step}",
        "save-clinicalDepartment",
        "入力_{step}",
        "リトライ_{step}",
        "script_{step}",
    ],
    "clinical_department_normalize": [
        "script_{step}",
    ],
    "free_text": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "リトライ_{step}",
    ],
    "faq": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "リトライ_{step}",
        "script_{step}",
    ],
    "card_number": [
        "{step}",
        "save-{step}",
        "入力_{step}",
        "save-入力_{step}",
        "script_{step}",
        "リトライ_{step}",
        "save-リトライ_{step}",
        # echo_back: true の場合
        "復唱_{step}",
        "入力_{step}_復唱",
        "save-入力_{step}_復唱",
        "save-{step}_復唱",
        "script_{step}_復唱確認",
        "リトライ_{step}_復唱",
        "save-リトライ_{step}_復唱",
    ],
}


def _cmr_chain_module_names(step: str, num_refs: int) -> list[str]:
    """cmr_chain ブロックが生成する CMR モジュール名（直列 N 個）"""
    return [f"ContextMatchRouter_{step}_chain_{i}" for i in range(num_refs)]


def _dtmf_split_save_module_names(step: str, labels: list[str]) -> list[str]:
    """Pattern C: DTMF 分離 hearing が生成する save_{step}_{label} モジュール名"""
    def _safe(s: str) -> str:
        return s.replace(" ", "_").replace("　", "_")
    return [f"save_{step}_{_safe(label)}" for label in labels]


def _termination_module_names(termination_ref: str) -> list[str]:
    """termination_ref から関連モジュール名を生成"""
    # termination_ref は通常 "END_xxx" 形式。完了フラグ_xxx, save-END_xxx, 切断_xxx を生成
    short = termination_ref
    if short.startswith("END_"):
        short = short[4:]
    return [
        f"完了フラグ_{short}",
        termination_ref,                # END_xxx (TTS モジュール)
        f"save-{termination_ref}",
        f"切断_{short}",
    ]


def build_module_to_block_map(yaml_path: str) -> dict[str, str]:
    """設計書 YAML からモジュール名 → ブロック名（step）の逆引き辞書を生成"""
    with open(yaml_path, encoding="utf-8") as f:
        spec = _yaml.safe_load(f)

    scenario_flow = spec.get("scenario_flow", [])
    mapping: dict[str, str] = {}

    for block in scenario_flow:
        btype = block.get("type", "")
        step  = block.get("step", "")
        if not btype or not step:
            continue

        templates = BLOCK_MODULE_TEMPLATES.get(btype, [])

        if btype == "termination":
            ref = block.get("termination_ref", step)
            for mod_name in _termination_module_names(ref):
                mapping[mod_name] = step
        elif btype == "cmr_chain":
            refs = block.get("reference_modules", []) or []
            for mod_name in _cmr_chain_module_names(step, len(refs)):
                mapping[mod_name] = step
        else:
            for tmpl in templates:
                mod_name = tmpl.replace("{step}", step)
                mapping[mod_name] = step
            # Pattern C: hearing with input_method=dtmf_split → save_{step}_{label} 群を追加
            if btype == "hearing" and block.get("input_method") == "dtmf_split":
                labels = [opt.get("label", "") for opt in (block.get("dtmf_options") or [])
                          if isinstance(opt, dict) and opt.get("action", "save") != "replay"
                          and opt.get("label")]
                for mod_name in _dtmf_split_save_module_names(step, labels):
                    mapping[mod_name] = step

    return mapping


def build_block_type_map(yaml_path: str) -> dict[str, str]:
    """設計書 YAML からブロック名（step）→ ブロック型（type）の辞書を生成"""
    with open(yaml_path, encoding="utf-8") as f:
        spec = _yaml.safe_load(f)
    return {block["step"]: block["type"]
            for block in spec.get("scenario_flow", [])
            if block.get("step") and block.get("type")}


def group_issues_by_block(issues: list[dict], yaml_path: str) -> dict[str, list[dict]]:
    """検出項目（{module: ..., ...}）をブロックごとにグルーピング。
    どのブロックにも属さない項目は "_unmapped" キーに入る。
    """
    mapping = build_module_to_block_map(yaml_path)
    grouped: dict[str, list[dict]] = {}

    for issue in issues:
        mod = issue.get("module", "") or issue.get("module_name", "")
        block = mapping.get(mod, "_unmapped")
        grouped.setdefault(block, []).append(issue)

    return grouped


def main():
    """CLI: 設計書 YAML から module → block マッピングを表示"""
    if len(sys.argv) < 2:
        print("Usage: block_mapper.py <yaml_path>", file=sys.stderr)
        sys.exit(1)

    mapping = build_module_to_block_map(sys.argv[1])
    # ブロック単位でグルーピングして表示
    by_block: dict[str, list[str]] = {}
    for mod, blk in mapping.items():
        by_block.setdefault(blk, []).append(mod)

    for blk in sorted(by_block.keys()):
        print(f"[{blk}]")
        for mod in sorted(by_block[blk]):
            print(f"  {mod}")
        print()


if __name__ == "__main__":
    main()
