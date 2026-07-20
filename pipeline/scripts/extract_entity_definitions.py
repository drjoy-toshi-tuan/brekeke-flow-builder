#!/usr/bin/env python3
"""
extract_entity_definitions.py

Gen1 (commubo) YAML のエンティティ定義を Gen3 の STT 辞書 / OpenAI 類義語に決定論的に振り分ける。

責任境界が曖昧なエントリは全て OpenAI 側にフォールバックする
（memory: feedback_entity_classification_default_openai）。

入力:
  commubo抽出/{施設}/{flow}/main.yaml に書かれた `エンティティ定義:` セクション
  サブ yaml にエンティティが記載されている場合も拾う

出力 (各 flow の元資料ディレクトリ直下、yaml と同居):
  commubo抽出/{施設}/{flow}/entity_classification.md      director 参照用サマリ
  commubo抽出/{施設}/{flow}/entity_stt_patch.json         STT additional_words / use_template 候補
  commubo抽出/{施設}/{flow}/entity_openai_synonyms.md     prompter サイドカー追記用の類義語例

bulk run summary:
  commubo抽出/entity_audit_summary.json                   全 flow の処理サマリ

ヒューリスティック振り分けルール (高信頼 STT のみ、それ以外 OpenAI):
  R1 STT_HOMOPHONE       同一 yomi に複数 surface (kanji 表記揺れ含む)
  R2 STT_TEMPLATE_REUSE  既存 STT テンプレ (9 カテゴリ) に hit
  R3 STT_PROPER_NOUN     医療固有名詞辞書 hit (診療科 / 薬剤名 / 施設名)
  R4 OPENAI_SYNONYM      上記いずれにも該当しない (デフォルト)
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMUBO_DIR = REPO_ROOT / "commubo抽出"
STT_TEMPLATE_FILE = REPO_ROOT / "docs" / "specs" / "stt_dictionary_templates.json"

SYSTEM_ENTITY_NAMES = {"日付", "時刻", "数字", "人名", "月日", "年月日", "電話番号"}

# 「これが含まれていたら医療固有名詞グループ」と判定するマーカー
PROPER_NOUN_MARKERS = (
    "科",
    "外来",
    "センター",
    "ドック",
    "検診",
    "健診",
    "コース",
    "病院",
    "クリニック",
    "オプション",
    "検査",
    "ワクチン",
    "予防接種",
)

# entity 名・テンプレ対応（surface が hit しなくても entity 名で吸い込む補助）
ENTITY_NAME_TO_TEMPLATE = {
    "新規予約": "hearing_yoken_common",
    "予約変更": "hearing_yoken_common",
    "予約キャンセル": "hearing_yoken_common",
    "用件": "hearing_yoken_common",
    "診療科": "hearing_shinryoka_basic",
    "わからない": "hearing_unknown",
    "分からない": "hearing_unknown",
    "肯定": "hearing_yesno_common",
    "否定": "hearing_yesno_common",
    "肯定単語": "hearing_yesno_common",
    "否定単語": "hearing_yesno_common",
    "肯定否定": "hearing_yesno_common",
    "復唱肯定": "echo_back_yesno",
    "復唱否定": "echo_back_yesno",
}


def has_proper_noun_marker(text: str) -> bool:
    return any(m in text for m in PROPER_NOUN_MARKERS)


@dataclass
class EntityValue:
    entity_name: str
    canonical_key: str
    surface: str
    source_yaml: str

    @property
    def is_canonical(self) -> bool:
        return self.surface == self.canonical_key


@dataclass
class Classification:
    rule: str
    target: str  # "stt" or "openai"
    template: str | None = None
    rationale: str = ""


@dataclass
class ClassifiedEntry:
    value: EntityValue
    classification: Classification


def load_stt_templates() -> dict[str, set[str]]:
    """STT テンプレ辞書から「表記」セットを取り出す（よみは捨てて表記のみキーにする）"""
    with STT_TEMPLATE_FILE.open(encoding="utf-8") as f:
        spec = json.load(f)
    out: dict[str, set[str]] = {}
    for tmpl_name, tmpl in spec.get("templates", {}).items():
        words = set()
        for line in tmpl.get("words", "").split("\n"):
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if parts:
                words.add(parts[0])
        out[tmpl_name] = words
    return out


def template_hit(surface: str, templates: dict[str, set[str]]) -> str | None:
    """surface がいずれかのテンプレに登場するなら、最初に hit したテンプレ名を返す"""
    for name, words in templates.items():
        if surface in words:
            return name
    return None


def is_proper_noun_group(entity_name: str, canonical_key: str) -> bool:
    """
    エンティティグループ単位で「医療固有名詞グループ」と判定する。
    True なら配下の全 surfaces (canonical + synonyms) を STT 扱いにする。
    """
    if has_proper_noun_marker(canonical_key):
        return True
    if has_proper_noun_marker(entity_name):
        return True
    return False


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def extract_entity_def(yaml_path: Path) -> tuple[list[dict], list[dict]]:
    """yaml から エンティティ定義 を取り出す。(system_list, custom_list) を返す。無ければ空リスト"""
    data = load_yaml(yaml_path)
    flow = data.get("flow", {}) if isinstance(data, dict) else {}
    if not isinstance(flow, dict):
        return [], []
    ent = flow.get("エンティティ定義") or {}
    if not isinstance(ent, dict):
        return [], []
    sys_list = ent.get("システム") or []
    custom_list = ent.get("カスタム") or []
    return (sys_list if isinstance(sys_list, list) else []), (
        custom_list if isinstance(custom_list, list) else []
    )


def _to_str(v) -> str | None:
    """yaml が int / bool / None として読んでしまった値を文字列に正規化。空は None"""
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s or None
    if isinstance(v, bool):
        return None  # bool 単独は entity 値としては無意味
    return str(v).strip() or None


def collect_values(custom_list: list, yaml_rel: str) -> list[EntityValue]:
    """カスタム配列から (entity_name, canonical_key, surface) の組を全列挙。
    yaml の自動型変換 (int/bool/None) で str 以外が来ても落ちないように防御的に str 化する。"""
    out: list[EntityValue] = []
    if not isinstance(custom_list, list):
        return out
    for ent in custom_list:
        if not isinstance(ent, dict):
            continue
        name = _to_str(ent.get("名前"))
        if not name:
            continue
        vals = ent.get("値")
        if not isinstance(vals, dict):
            continue
        for canonical_key_raw, syns in vals.items():
            canonical_key = _to_str(canonical_key_raw)
            if not canonical_key:
                continue
            # canonical_key そのものも 1 surface として扱う (proper noun 検出用)
            out.append(EntityValue(name, canonical_key, canonical_key, yaml_rel))
            if isinstance(syns, list):
                for s in syns:
                    surface = _to_str(s)
                    if surface:
                        out.append(EntityValue(name, canonical_key, surface, yaml_rel))
    return out


KANA_RE = re.compile(r"^[぀-ゟ゠-ヿー]+$")
KANJI_RE = re.compile(r"[一-鿿]")


def kana_only(s: str) -> bool:
    return bool(KANA_RE.match(s))


def has_kanji(s: str) -> bool:
    return bool(KANJI_RE.search(s))


def detect_kana_variants(values: list[EntityValue]) -> set[str]:
    """
    同一 (entity_name, canonical_key) 配下に kanji を含む surface が存在する場合、
    その配下のカナ surface (=yomi 表記) を STT 対象として返す。
    """
    by_group: dict[tuple[str, str], list[EntityValue]] = {}
    for v in values:
        by_group.setdefault((v.entity_name, v.canonical_key), []).append(v)
    out: set[str] = set()
    for group_key, group in by_group.items():
        has_kanji_surface = any(has_kanji(v.surface) for v in group)
        if not has_kanji_surface:
            continue
        for v in group:
            if kana_only(v.surface):
                out.add(v.surface)
    return out


def is_proper_noun_group_for_value(v: EntityValue, group_proper_noun: set[tuple[str, str]]) -> bool:
    return (v.entity_name, v.canonical_key) in group_proper_noun


def precompute_proper_noun_groups(values: list[EntityValue]) -> set[tuple[str, str]]:
    out: set[tuple[str, str]] = set()
    seen: set[tuple[str, str]] = set()
    for v in values:
        key = (v.entity_name, v.canonical_key)
        if key in seen:
            continue
        seen.add(key)
        if is_proper_noun_group(v.entity_name, v.canonical_key):
            out.add(key)
    return out


def classify(
    values: list[EntityValue],
    templates: dict[str, set[str]],
    proper_noun_groups: set[tuple[str, str]],
    kana_variants: set[str],
) -> list[ClassifiedEntry]:
    out: list[ClassifiedEntry] = []
    seen_keys: set[tuple[str, str, str]] = set()

    for v in values:
        # システムエンティティ名の単純参照は無視（Gen3 では generate_by_OpenAI output_format で吸収）
        if v.entity_name in SYSTEM_ENTITY_NAMES:
            continue

        dedup_key = (v.entity_name, v.canonical_key, v.surface)
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        mapped_tmpl = ENTITY_NAME_TO_TEMPLATE.get(v.entity_name)

        # R1: グループ単位で proper noun と判定された配下は全て STT
        if (v.entity_name, v.canonical_key) in proper_noun_groups:
            out.append(
                ClassifiedEntry(
                    v,
                    Classification(
                        rule="R1_STT_PROPER_NOUN_GROUP",
                        target="stt",
                        template=mapped_tmpl,
                        rationale=(
                            f"canonical '{v.canonical_key}' / entity '{v.entity_name}' は"
                            f" 医療固有名詞マーカー含み → グループ全体を STT 救済対象"
                        ),
                    ),
                )
            )
            continue

        # R2: 既存 STT テンプレに surface が hit
        tmpl = template_hit(v.surface, templates)
        if tmpl:
            out.append(
                ClassifiedEntry(
                    v,
                    Classification(
                        rule="R2_STT_TEMPLATE_REUSE",
                        target="stt",
                        template=tmpl,
                        rationale=f"既存 STT テンプレ '{tmpl}' に登録済み",
                    ),
                )
            )
            continue

        # R2': entity 名 → テンプレ写像で hit
        if mapped_tmpl and v.surface in templates.get(mapped_tmpl, set()):
            out.append(
                ClassifiedEntry(
                    v,
                    Classification(
                        rule="R2_STT_TEMPLATE_REUSE",
                        target="stt",
                        template=mapped_tmpl,
                        rationale=f"entity '{v.entity_name}' のテンプレ '{mapped_tmpl}' に登録済み",
                    ),
                )
            )
            continue

        # R3: kanji 表記が同グループに併存しているカナ surface は yomi 扱いで STT
        if v.surface in kana_variants and kana_only(v.surface):
            out.append(
                ClassifiedEntry(
                    v,
                    Classification(
                        rule="R3_STT_KANA_VARIANT",
                        target="stt",
                        template=mapped_tmpl,
                        rationale=(
                            f"同 canonical '{v.canonical_key}' 配下に漢字表記が併存 → カナは yomi 用 STT エントリ"
                        ),
                    ),
                )
            )
            continue

        # R4: 上記以外は全て OpenAI フォールバック (memory: feedback_entity_classification_default_openai)
        out.append(
            ClassifiedEntry(
                v,
                Classification(
                    rule="R4_OPENAI_SYNONYM",
                    target="openai",
                    rationale="高信頼 STT ルールに該当せず → OpenAI 正規化層に委譲",
                ),
            )
        )
    return out


def emit_stt_patch(entries: list[ClassifiedEntry]) -> dict:
    """STT パッチ JSON を生成。gen_properties.py 等が消費する形式（暫定）"""
    by_template: dict[str, set[str]] = {}
    additional: list[dict] = []
    for e in entries:
        if e.classification.target != "stt":
            continue
        if e.classification.template:
            by_template.setdefault(e.classification.template, set()).add(e.value.surface)
        additional.append(
            {
                "entity_name": e.value.entity_name,
                "canonical": e.value.canonical_key,
                "surface": e.value.surface,
                "rule": e.classification.rule,
                "template": e.classification.template,
                "rationale": e.classification.rationale,
                "source": e.value.source_yaml,
            }
        )
    return {
        "use_templates": sorted(by_template.keys()),
        "additional_words_candidates": additional,
        "by_template_summary": {k: sorted(v) for k, v in by_template.items()},
    }


def emit_openai_md(entries: list[ClassifiedEntry], facility: str, flow: str) -> str:
    """prompter サイドカー追記用 Markdown"""
    lines = [
        f"# OpenAI Synonym Examples — {facility} / {flow}",
        "",
        "Gen1 commubo エンティティ定義から抽出した、OpenAI 正規化層で吸収すべき類義語例。",
        "prompter は generate_by_OpenAI モジュールの prompt の `## 類義語例` 等のセクションに反映する。",
        "",
    ]
    by_entity: dict[str, list[ClassifiedEntry]] = {}
    for e in entries:
        if e.classification.target != "openai":
            continue
        by_entity.setdefault(e.value.entity_name, []).append(e)

    for name in sorted(by_entity.keys()):
        lines.append(f"## {name}")
        lines.append("")
        by_canon: dict[str, list[str]] = {}
        for e in by_entity[name]:
            if e.value.canonical_key == e.value.surface:
                by_canon.setdefault(e.value.canonical_key, [])
            else:
                by_canon.setdefault(e.value.canonical_key, []).append(e.value.surface)
        for canon, syns in by_canon.items():
            if syns:
                lines.append(f"- **{canon}**: {', '.join(syns)}")
            else:
                lines.append(f"- **{canon}** (synonyms: なし)")
        lines.append("")
    return "\n".join(lines)


def emit_summary_md(
    entries: list[ClassifiedEntry],
    facility: str,
    flow: str,
    yaml_files_inspected: list[str],
    system_entities: list[str],
) -> str:
    by_rule: dict[str, int] = {}
    for e in entries:
        by_rule[e.classification.rule] = by_rule.get(e.classification.rule, 0) + 1

    lines = [
        f"# Entity Classification Summary — {facility} / {flow}",
        "",
        f"対象 yaml: {len(yaml_files_inspected)} 本",
        "",
    ]
    for f in yaml_files_inspected:
        lines.append(f"  - `{f}`")
    lines.extend(
        [
            "",
            "## システムエンティティ (Gen3 では generate_by_OpenAI の output_format で吸収)",
            "",
        ]
    )
    if system_entities:
        for s in system_entities:
            lines.append(f"- {s}")
    else:
        lines.append("- (なし)")
    lines.extend(
        [
            "",
            "## ルール別件数",
            "",
            "| ルール | 件数 | 行き先 |",
            "| --- | ---: | --- |",
        ]
    )
    rule_targets = {
        "R1_STT_PROPER_NOUN_GROUP": "STT 辞書 (additional_words)",
        "R2_STT_TEMPLATE_REUSE": "STT 辞書 (use_template)",
        "R3_STT_KANA_VARIANT": "STT 辞書 (yomi)",
        "R4_OPENAI_SYNONYM": "OpenAI 正規化",
    }
    for rule in [
        "R1_STT_PROPER_NOUN_GROUP",
        "R2_STT_TEMPLATE_REUSE",
        "R3_STT_KANA_VARIANT",
        "R4_OPENAI_SYNONYM",
    ]:
        lines.append(f"| {rule} | {by_rule.get(rule, 0)} | {rule_targets[rule]} |")

    lines.extend(["", "## 詳細 (entity 単位)", ""])
    by_entity: dict[str, list[ClassifiedEntry]] = {}
    for e in entries:
        by_entity.setdefault(e.value.entity_name, []).append(e)
    for name in sorted(by_entity.keys()):
        group = by_entity[name]
        stt = [e for e in group if e.classification.target == "stt"]
        oai = [e for e in group if e.classification.target == "openai"]
        lines.append(f"### {name}")
        lines.append(f"- STT: {len(stt)} surfaces, OpenAI: {len(oai)} surfaces")
        if stt:
            lines.append("- STT サンプル:")
            for e in stt[:5]:
                lines.append(
                    f"  - `{e.value.surface}` ({e.classification.rule}"
                    + (f" → {e.classification.template}" if e.classification.template else "")
                    + ")"
                )
        if oai:
            lines.append("- OpenAI サンプル:")
            for e in oai[:5]:
                lines.append(f"  - `{e.value.surface}`")
        lines.append("")
    return "\n".join(lines)


def find_facility_dirs(facility_name: str | None) -> list[Path]:
    """commubo抽出 配下の施設ディレクトリ。facility_name 指定時は fuzzy match"""
    all_dirs = [
        d for d in COMMUBO_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
    ]
    if not facility_name:
        return sorted(all_dirs)
    needle = facility_name
    matches = [d for d in all_dirs if needle in d.name]
    return sorted(matches)


def find_flow_dirs(facility_dir: Path) -> list[Path]:
    return sorted(
        d for d in facility_dir.iterdir() if d.is_dir() and (d / "main.yaml").exists()
    )


def derive_names(facility_dir: Path, flow_dir: Path) -> tuple[str, str]:
    """
    出力先ファイル名のための (facility, flow) を推測。
    facility: ディレクトリ名から番号プレフィクス [...] を剥がす
    flow: flow_dir 名末尾を雑に切る
    """
    fac_raw = facility_dir.name
    fac = re.sub(r"^【\d+[^】]*】", "", fac_raw)
    fac = re.sub(r"｜.*$", "", fac)  # 複数施設併記の場合は最初のみ採用
    flow_raw = flow_dir.name
    flow = re.sub(r"^【[^】]+】", "", flow_raw)
    flow = re.sub(r"\d+_M_本番$", "", flow).strip("_")
    flow = re.sub(r"_M_本番$", "", flow)
    return fac, flow


def process_flow(
    facility_dir: Path,
    flow_dir: Path,
    templates: dict[str, set[str]],
) -> dict:
    facility, flow = derive_names(facility_dir, flow_dir)
    # 元資料 yaml と同居させる (director が単一ディレクトリで全部見られるように)
    out_dir = flow_dir

    yaml_files = sorted(flow_dir.glob("*.yaml"))
    all_values: list[EntityValue] = []
    system_names: list[str] = []
    inspected: list[str] = []
    skipped: list[tuple[str, str]] = []  # [(rel, reason)]

    for yp in yaml_files:
        rel = f"{facility_dir.name}/{flow_dir.name}/{yp.name}"
        try:
            sys_list, custom_list = extract_entity_def(yp)
        except Exception as exc:  # noqa: BLE001
            skipped.append((rel, f"parse: {type(exc).__name__}: {exc}"))
            continue
        if not sys_list and not custom_list:
            continue
        inspected.append(rel)
        for s in sys_list:
            n = s.get("名前") if isinstance(s, dict) else None
            if n:
                system_names.append(str(n))
        all_values.extend(collect_values(custom_list, rel))

    proper_noun_groups = precompute_proper_noun_groups(all_values)
    kana_variants = detect_kana_variants(all_values)
    entries = classify(all_values, templates, proper_noun_groups, kana_variants)

    stt_patch = emit_stt_patch(entries)
    (out_dir / "entity_stt_patch.json").write_text(
        json.dumps(stt_patch, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "entity_openai_synonyms.md").write_text(
        emit_openai_md(entries, facility, flow), encoding="utf-8"
    )
    (out_dir / "entity_classification.md").write_text(
        emit_summary_md(entries, facility, flow, inspected, sorted(set(system_names))),
        encoding="utf-8",
    )

    return {
        "facility": facility,
        "flow": flow,
        "facility_dir": facility_dir.name,
        "flow_dir": flow_dir.name,
        "out_dir": str(out_dir.relative_to(REPO_ROOT)).replace("\\", "/"),
        "yaml_inspected": len(inspected),
        "yaml_skipped": [{"file": r, "reason": why} for r, why in skipped],
        "entity_values_total": len(all_values),
        "stt_count": sum(1 for e in entries if e.classification.target == "stt"),
        "openai_count": sum(1 for e in entries if e.classification.target == "openai"),
        "no_entity_def": len(inspected) == 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--facility",
        default=None,
        help="施設ディレクトリ名の部分一致 (例: '湘南鎌倉', 'さやま')。省略時は全施設",
    )
    parser.add_argument(
        "--flow",
        default=None,
        help="flow ディレクトリ名の部分一致 (例: '診療1', '健診')。省略時は当該施設の全 flow",
    )
    parser.add_argument(
        "--list-only", action="store_true", help="対象施設/flow を列挙するのみ (出力しない)"
    )
    args = parser.parse_args()

    facility_dirs = find_facility_dirs(args.facility)
    if not facility_dirs:
        print(
            f"[ERROR] commubo抽出 で施設が見つかりません: '{args.facility}'", file=sys.stderr
        )
        sys.exit(2)

    templates = load_stt_templates()

    targets: list[tuple[Path, Path]] = []
    for fd in facility_dirs:
        for fl in find_flow_dirs(fd):
            if args.flow and args.flow not in fl.name:
                continue
            targets.append((fd, fl))

    if args.list_only:
        for fd, fl in targets:
            print(f"{fd.name} / {fl.name}")
        print(f"\n合計 {len(targets)} flow")
        return

    if not targets:
        print("[ERROR] マッチする flow がありません", file=sys.stderr)
        sys.exit(2)

    summary: list[dict] = []
    for fd, fl in targets:
        try:
            r = process_flow(fd, fl, templates)
            summary.append(r)
            tag = "EMPTY" if r["no_entity_def"] else "OK"
            skip_note = f" skipped={len(r['yaml_skipped'])}" if r["yaml_skipped"] else ""
            print(
                f"[{tag}] {r['facility']}_{r['flow']}  "
                f"yaml={r['yaml_inspected']} stt={r['stt_count']} oai={r['openai_count']}{skip_note}"
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] {fd.name} / {fl.name}: {exc}", file=sys.stderr)

    summary_path = COMMUBO_DIR / "entity_audit_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n各 flow の出力: commubo抽出/<施設>/<flow>/entity_*")
    print(f"集約サマリ: {summary_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
