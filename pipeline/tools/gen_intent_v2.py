#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_intent_v2.py — intent_classifier_v2 の spec 充填ジェネレーター

modules/intent_classifier_v2/script.js（engine 正本）に spec JSON と wiring を
充填した実戦 Script を生成する。engine 本体は一切改変しない（hash 安定）。

使い方:
    python3 tools/gen_intent_v2.py --spec <spec.json> --step 用件確認 \
        --input-module 入力_用件確認 --context classification [-o out.js]

spec.json の形式は modules/intent_classifier_v2/script.js ヘッダ参照。
生成後の必須工程（標準 §6）:
    python3 modules/intent_classifier_v2/test_oracle.py   # oracle 全 PASS
    node   modules/intent_classifier_v2/test_parity.js    # JS↔Python parity
    → P6 実機受入 → certified_hashes 登録（人間ゲート）
"""

import argparse
import json
import re
import sys
from pathlib import Path

ENGINE_PATH = Path(__file__).resolve().parent.parent / "modules" / "intent_classifier_v2" / "script.js"

VALID_QUESTION_TYPES = {"menu", "yes_no", "open"}


def lower_legacy_spec(spec: dict) -> dict:
    """旧 v2 形式（intents[].strong/weak keyword 直結）を Evidence→Rule 形式へ機械変換。
    keyword → evidence 1:1、rule 1 条件。numbers は options[].number から生成。"""
    if "intents" not in spec or "evidences" in spec:
        return spec
    out = {k: v for k, v in spec.items() if k != "intents"}
    evidences, rules, numbers = [], [], dict(spec.get("numbers") or {})
    seen_labels: set = set()
    for idx, it in enumerate(spec.get("intents") or []):
        if not it.get("label"):
            raise SystemExit(f"[ERROR] intents[{idx}]: label がありません（legacy spec）")
        if it["label"] in seen_labels:
            raise SystemExit(f"[ERROR] intents[{idx}]: label '{it['label']}' が重複しています"
                             f"（evidence 名 kw_{it['label']} が衝突・numbers も上書きされる）")
        seen_labels.add(it["label"])
        name = f"kw_{it['label']}"
        kws = list(it.get("strong") or []) + list(it.get("weak") or [])
        ev = {"name": name, "keywords": kws,
              "patterns": list(it.get("patterns") or []), "negatable": True}
        evidences.append(ev)
        rule = {"intent": it["label"], "all": [name], "none": [f"{name}_neg"]}
        rules.append(rule)
        if it.get("negated_label"):
            rules.append({"intent": it["negated_label"], "all": [f"{name}_neg"]})
        if it.get("number") is not None:
            numbers[str(it["number"])] = it["label"]
    out["evidences"] = evidences
    out["events"] = spec.get("events") or []
    out["rules"] = rules
    if numbers:
        out["numbers"] = numbers
    return out


LABEL_VOCAB_PATH = ENGINE_PATH.parent / "label_vocab.json"


def _match_canonical(label: str, canon: dict) -> str | None:
    """施設ラベル → 正準ラベル。エイリアス完全一致を優先し、無ければ
    「正準名を含む」候補が一意のときだけ採用（予約確認 は 確認 が最長一致）。"""
    for cname, cdef in canon.items():
        if label == cname or label in (cdef.get("aliases") or []):
            return cname
    hits = [cname for cname in canon if cname in label]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        # 最長の正準名を採用（予約確認 → 確認[2字] vs 予約[2字] は同長 → 後方一致を優先）
        hits.sort(key=lambda c: (len(c), label.rfind(c)))
        return hits[-1]
    return None


def compose_intent_spec(options: list) -> dict | None:
    """label_vocab.json（認定 menu spec 由来のマスター語彙）から、施設の選択肢構成に
    合わせた spec を合成する。用件/区分メニューの 4 パターン
    （予約/変更/キャンセル/確認 の任意の部分集合・任意の番号割当）に対応:

      1. 各 option label を正準ラベルへ解決（エイリアス/包含一致）
      2. マスターの evidences/events は全量掲載（検出は無害・rules だけが出力を決める）
      3. rules は「選択された正準ラベルの intent + CLARIFY/TRANSFER + 同伴ルール
         （キャンセル取りやめ 等）」だけを選抜し、intent を施設ラベルへリネーム
      4. only_if_absent 付きルールは該当ラベル非選択時のみ採用（例: 確認 が無い
         メニューでは「確認したい」→ 問い合わせ の後方互換ルール）
      5. option.keywords は正準ラベルの primary_evidence へ追記（削除はしない）
      6. numbers は options[].number から構築

    正準解決できたラベルが 1 つも無ければ None（呼び元が legacy auto-lower へ）。
    未知ラベルは kw_ evidence + 単純 rule で共存させる。"""
    if not LABEL_VOCAB_PATH.exists():
        return None
    vocab = json.loads(LABEL_VOCAB_PATH.read_text(encoding="utf-8"))
    canon = vocab["canonical_labels"]

    resolved: dict = {}   # canonical -> facility label
    unknown: list = []
    numbers: dict = {}
    extra_kw: dict = {}   # canonical -> [user keywords]
    for idx, o in enumerate(options):
        if not isinstance(o, dict):
            o = {"label": str(o)}
        lbl = str(o.get("label") or "")
        if not lbl:
            continue
        c = _match_canonical(lbl, canon)
        if c and c not in resolved:
            resolved[c] = lbl
            if o.get("keywords"):
                extra_kw[c] = [str(k) for k in o["keywords"]]
        elif not c:
            unknown.append(o)
        # number 未指定（CSV の options は文字列 emit で number を持たない）は
        # 選択肢の並び順で 1 始まりの番号を割当てる（TTS の「1番、〇〇」列挙と同順）。
        # これが無いと L0 番号判定（「1です」「1番で」等）が全滅する。
        num = o.get("number")
        if num is None:
            num = idx + 1
        numbers.setdefault(str(num), lbl)
    if not resolved:
        return None

    base = vocab["spec"]
    spec = {
        "question_type": base.get("question_type", "menu"),
        "clarify_margin": base.get("clarify_margin", 1),
        "synonyms": dict(base.get("synonyms") or {}),
        "extractors": list(base.get("extractors") or []),
        "evidences": [dict(e) for e in base["evidences"]],
        "events": [dict(e) for e in base["events"]],
        "rules": [],
    }

    # 5. ユーザー keywords を primary_evidence へ追記
    ev_by_name = {e["name"]: e for e in spec["evidences"]}
    for c, kws in extra_kw.items():
        pe = canon[c].get("primary_evidence")
        if pe in ev_by_name:
            cur = list(ev_by_name[pe].get("keywords") or [])
            for k in kws:
                if k not in cur:
                    cur.append(k)
            ev_by_name[pe]["keywords"] = cur

    # 3-4. ルール選抜 + intent リネーム
    always = set(vocab.get("always_rules") or [])
    companion = vocab.get("companion_rules") or {}
    for r in base["rules"]:
        intent = r["intent"]
        absent_guard = r.get("only_if_absent")
        if absent_guard and absent_guard in resolved:
            continue
        rr = {k: v for k, v in r.items() if k != "only_if_absent"}
        if intent in resolved:
            rr["intent"] = resolved[intent]
            spec["rules"].append(rr)
        elif intent in always:
            spec["rules"].append(rr)
        elif intent in companion and companion[intent] in resolved:
            spec["rules"].append(rr)

    # 未知ラベル: kw_ evidence + 単純 rule で共存
    for o in unknown:
        lbl = str(o.get("label"))
        name = f"kw_{lbl}"
        kws = [lbl] + [str(k) for k in (o.get("keywords") or []) if str(k) != lbl]
        spec["evidences"].append({"name": name, "keywords": kws, "patterns": [],
                                  "negatable": True})
        spec["rules"].append({"intent": lbl, "all": [name], "none": [f"{name}_neg"]})

    if numbers:
        spec["numbers"] = numbers
    return spec


def validate_spec(spec: dict) -> list[str]:
    errs = []
    if "question_type" not in spec:
        errs.append("必須キーがありません: question_type")
        return errs
    if spec["question_type"] not in VALID_QUESTION_TYPES:
        errs.append(f"question_type '{spec['question_type']}' は {sorted(VALID_QUESTION_TYPES)} のいずれか")

    evidences = spec.get("evidences") or []
    events = spec.get("events") or []
    rules = spec.get("rules") or []
    if not rules and spec["question_type"] != "yes_no":
        errs.append("rules が空です（yes_no 以外は最低 1 rule 必要）")

    # 参照整合: evidence/event 名の解決
    ev_names = set()
    for i, ev in enumerate(evidences):
        if not ev.get("name"):
            errs.append(f"evidences[{i}]: name がありません")
            continue
        if ev["name"] in ev_names:
            errs.append(f"evidences[{i}]: name '{ev['name']}' が重複")
        ev_names.add(ev["name"])
        if not (ev.get("keywords") or ev.get("patterns")):
            errs.append(f"evidences[{i}] '{ev['name']}': keywords / patterns が両方空")
        # patterns は oracle（Python re）と engine（JS RegExp）の両方で解釈されるため、
        # 少なくとも Python 側で compile できることを生成時に検証する（実行時の
        # 「初回発話で SyntaxError → スクリプト全死」を防ぐ。Nashorn 固有差は P6 で捕捉）。
        for j, p in enumerate(ev.get("patterns") or []):
            try:
                re.compile(p)
            except re.error as e:
                errs.append(f"evidences[{i}] '{ev['name']}'.patterns[{j}]: 正規表現が不正です: {e}")
        if ev.get("negatable"):
            ev_names.add(ev["name"] + "_neg")
    ev_names |= set((spec.get("synonyms") or {}).keys())

    for i, ex in enumerate(spec.get("extractors") or []):
        try:
            re.compile(ex.get("regex") or "")
        except re.error as e:
            errs.append(f"extractors[{i}] '{ex.get('name', '?')}': 正規表現が不正です: {e}")

    # イベントは fixpoint ループ（engine buildEvents）で解決されるため定義順不問。
    # 前方参照を誤って弾かないよう、まず全 event 名を登録してから参照を検査する。
    known = set(ev_names)
    for i, evt in enumerate(events):
        if not evt.get("name"):
            errs.append(f"events[{i}]: name がありません")
            continue
        if evt["name"] in known:
            errs.append(f"events[{i}]: name '{evt['name']}' が evidence/event と重複")
        known.add(evt["name"])
    for i, evt in enumerate(events):
        if not evt.get("name"):
            continue
        for c in (evt.get("all") or []) + (evt.get("any") or []):
            if c not in known:
                errs.append(f"events[{i}] '{evt['name']}': 未定義の条件 '{c}' を参照")

    for i, r in enumerate(rules):
        if not r.get("intent"):
            errs.append(f"rules[{i}]: intent がありません")
        if not r.get("all"):
            errs.append(f"rules[{i}] '{r.get('intent', '?')}': all が空（無条件 rule は禁止）")
        for c in (r.get("all") or []) + (r.get("none") or []):
            if c not in known:
                errs.append(f"rules[{i}] '{r.get('intent', '?')}': 未定義の条件 '{c}' を参照")

    if spec["question_type"] == "yes_no":
        syn = spec.get("synonyms") or {}
        if "_YES_" not in syn or "_NO_" not in syn:
            errs.append("question_type=yes_no には synonyms._YES_ / _NO_ が必須（CLARIFY 判定用）")
    return errs


def main() -> None:
    ap = argparse.ArgumentParser(description="intent_classifier_v2 spec 充填ジェネレーター")
    ap.add_argument("--spec", required=True, help="spec JSON パス")
    ap.add_argument("--step", required=True, help="ステップ名（構造化結果の保存キー）")
    ap.add_argument("--input-module", required=True, help="入力（STT/DTMF）モジュール名")
    ap.add_argument("--context", default="", help="保存先 context 名（省略可）")
    ap.add_argument("-o", "--output", help="出力先（省略時は stdout）")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)

    spec = lower_legacy_spec(spec)
    errs = validate_spec(spec)
    if errs:
        print("❌ spec 検証エラー:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    # wiring 値は JS 文字列リテラルへ raw 埋め込みされるため、リテラルを壊す文字を拒否する
    # （これらは実在の Brekeke モジュール名/コンテキスト名と一致する必要があり、
    # エスケープして通すより設定ミスとして止める方が安全）。
    for label, val in (("--input-module", args.input_module),
                       ("--context", args.context), ("--step", args.step)):
        if any(c in val for c in ('"', "\\", "\n", "\r")):
            print(f"❌ {label} '{val}' に引用符/バックスラッシュ/改行は使えません", file=sys.stderr)
            sys.exit(1)

    engine = ENGINE_PATH.read_text(encoding="utf-8")
    # SPEC_JSON は最後に充填する: spec 内の文字列が偶然 {{INPUT_MODULE}} 等の
    # プレースホルダー文字列を含んでいても後続 replace で破壊されないようにする。
    script = (engine
              .replace("{{INPUT_MODULE}}", args.input_module)
              .replace("{{CONTEXT_NAME}}", args.context)
              .replace("{{STEP_NAME}}", args.step)
              .replace("{{SPEC_JSON}}", json.dumps(spec, ensure_ascii=False)))

    if args.output:
        Path(args.output).write_text(script, encoding="utf-8")
        print(f"✓ {args.output}")
        print("次: test_oracle.py / test_parity.js を実行し、P6 受入へ（本番投入は認定後）")
    else:
        print(script)


if __name__ == "__main__":
    main()
