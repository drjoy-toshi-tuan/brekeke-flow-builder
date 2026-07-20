#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
intent_classifier_v2 oracle — Evidence→Event→Rule engine の独立 Python 再実装

仕様正本: docs/governance/intent-engine-v2-design.md
大原則: Rule は生テキストを読まない。Text → Evidence → Event → Intent → Output
JS 実装との parity は test_parity.js（node）で機械検証する。
"""

import json
import re
import sys

FILLERS = ["えっとー", "えっと", "えーとー", "えーと", "ええとー", "ええと", "あのー", "あの", "えー", "うーんと", "えとー", "えっ"]
NEG_MARKERS = ["ない", "なくて", "ません", "不要", "結構", "やめ", "なしで"]
# 依頼形「〜てもらえませんか」「〜できませんか」は否定ではなく丁寧な依頼。除外する。
NEG_REQUEST_EXCLUDES = ["てもらえ", "もらえ", "てくれ", "てもらい", "ていただけ", "できます", "いただけ"]
NEG_WINDOW = 12
REPEAT_MARKERS = ["もう一度", "もういちど", "聞こえ", "きこえ", "繰り返", "くりかえ", "もっかい"]

_PUNCT_RE = re.compile(r"[。、，．！？!?「」『』【】（）()・…]")


def normalize(s) -> str:
    if s is None:
        return ""
    n = str(s)
    n = re.sub(r"[\r\n\t]", "", n)
    n = "".join(chr(ord(c) - 0xFF10 + 0x30) if "０" <= c <= "９" else c for c in n)
    n = "".join(chr(ord(c) - 0xFEE0) if ("Ａ" <= c <= "Ｚ" or "ａ" <= c <= "ｚ") else c for c in n)
    n = n.lower()
    n = "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in n)
    n = re.sub(r"[\s　]", "", n)
    n = _PUNCT_RE.sub("", n)
    for f in FILLERS:
        while f in n:
            n = n.replace(f, "", 1)
    return n


def _has_negation_after(t: str, idx: int) -> bool:
    win = t[idx:idx + NEG_WINDOW]
    for m in NEG_MARKERS:
        pos = win.find(m)
        if pos < 0:
            continue
        prefix = win[:pos]
        if m == "ません":
            if any(prefix.endswith(ex) for ex in NEG_REQUEST_EXCLUDES):
                continue
        if m in ("ない", "なくて") and prefix.endswith("しか"):
            continue  # しかない = affirmative "have no choice but to"
        return True
    return False


def _detect_evidence(spec: dict, t: str, reason: list) -> dict:
    facts: dict = {}
    for ev in spec.get("evidences") or []:
        match_end = -1
        hit = None
        for kw_raw in ev.get("keywords") or []:
            kw = normalize(kw_raw)
            pos = t.find(kw) if kw else -1
            if pos >= 0:
                match_end = pos + len(kw)
                hit = kw_raw
                break
        if match_end < 0:
            for p in ev.get("patterns") or []:
                m = re.search(p, t)
                if m:
                    match_end = m.end()
                    hit = p
                    break
        if match_end < 0:
            continue
        if ev.get("negatable") and _has_negation_after(t, match_end):
            facts[ev["name"] + "_neg"] = True
            reason.append(f"L2:evidence:{ev['name']}_neg({hit})")
        else:
            facts[ev["name"]] = True
            reason.append(f"L2:evidence:{ev['name']}({hit})")
    for tok, syns in (spec.get("synonyms") or {}).items():
        for syn_raw in syns:
            syn = normalize(syn_raw)
            if syn and syn in t:
                facts[tok] = True
                reason.append(f"L2:token:{syn_raw}->{tok}")
                break
    return facts


def _build_events(spec: dict, facts: dict, reason: list) -> dict:
    events = spec.get("events") or []
    changed = True
    guard = len(events) + 1
    while changed and guard > 0:
        changed = False
        guard -= 1
        for evt in events:
            if facts.get(evt["name"]):
                continue
            ok = all(facts.get(c) for c in evt.get("all") or [])
            any_list = evt.get("any") or []
            if ok and any_list:
                ok = any(facts.get(c) for c in any_list)
            if ok:
                facts[evt["name"]] = True
                reason.append(f"L3:event:{evt['name']}")
                changed = True
    return facts


def _base_evidence_set(cond: str, events_by_name: dict, seen: set) -> set:
    if cond in seen:
        return set()
    seen.add(cond)
    evt = events_by_name.get(cond)
    if evt is None:
        return {cond}
    out: set = set()
    for dep in (evt.get("all") or []) + (evt.get("any") or []):
        out |= _base_evidence_set(dep, events_by_name, seen)
    return out


def _rule_specificity(rule: dict, events_by_name: dict) -> int:
    acc: set = set()
    for cond in rule.get("all") or []:
        acc |= _base_evidence_set(cond, events_by_name, set())
    return len(acc)


def _apply_rules(spec: dict, facts: dict, reason: list) -> list:
    events_by_name = {e["name"]: e for e in spec.get("events") or []}
    fired = []
    for order, r in enumerate(spec.get("rules") or []):
        all_ = r.get("all") or []
        ok = all(facts.get(c) for c in all_)
        if ok:
            ok = not any(facts.get(c) for c in r.get("none") or [])
        if ok:
            sp = _rule_specificity(r, events_by_name)
            fired.append({"intent": r["intent"], "spec": sp, "order": order, "all": all_})
            reason.append(f"L4:rule:{r['intent']}[{'+'.join(all_)}](spec={sp})")
    return fired


def _resolve_conflict(spec: dict, fired: list, result: dict) -> dict:
    by_intent: dict = {}
    for f in fired:
        cur = by_intent.get(f["intent"])
        if cur is None or f["spec"] > cur["spec"] or (f["spec"] == cur["spec"] and f["order"] < cur["order"]):
            by_intent[f["intent"]] = f
    lst = sorted(by_intent.values(), key=lambda c: (-c["spec"], c["order"]))
    top1 = lst[0]
    top2 = lst[1] if len(lst) > 1 else None
    margin = spec.get("clarify_margin")
    margin = 1 if margin is None else margin
    if top1["intent"] == "CLARIFY":
        result["intent"] = "CLARIFY"
        result["need_clarification"] = True
        result["reason"].append(f"L5:CLARIFY rule(spec={top1['spec']}) → 聞き返し")
        return result
    if top2 is not None and (top1["spec"] - top2["spec"]) < margin:
        result["intent"] = "CLARIFY"
        result["need_clarification"] = True
        result["reason"].append(
            f"L5:拮抗 {top1['intent']}(spec={top1['spec']}) vs "
            f"{top2['intent']}(spec={top2['spec']}) → 聞き返し")
        return result
    result["intent"] = top1["intent"]
    result["negation"] = any(c.endswith("_neg") for c in top1["all"])
    result["confidence"] = (1 if top2 is None
                            else round(top1["spec"] / (top1["spec"] + top2["spec"]) * 100)
                            / 100)
    result["reason"].append(f"L5:採用 {top1['intent']}(spec={top1['spec']})")
    return result


def classify(spec: dict, raw_input) -> dict:
    raw = "" if raw_input is None else str(raw_input)
    result = {"intent": "NO_RESULT", "confidence": 0, "entities": {}, "variables": {},
              "negation": False, "reason": [], "evidences": [], "events": [],
              "need_clarification": False}
    t = normalize(raw)
    if t == "":
        return result

    # L0: DTMF / 番号発話 → label 直結
    numbers = spec.get("numbers") or {}
    if re.fullmatch(r"[0-9]+", t) and t in numbers:
        result["intent"] = numbers[t]
        result["confidence"] = 1
        result["reason"].append(f"L0:DTMF={t}")
        return result
    # 部分一致の N番/Nばん は「安全な継続」限定: 文末 / で(お願い…) / です / だ(よ|ね) /
    # ね / よ / かな / を / ください。これが無いと 2番目(順序)・2番線・一番早い(最上級) 等の
    # 非選択用法が誤って選択肢に化ける（AmiVoice 複数文連結ノイズで特に危険・2026-07-17）。
    _BAN_CONT = r"(?=$|で|です|だ|ね|よ|かな|を|ください|おねがい|お願い)"
    # 全文一致（^…$ アンカー）限定の許容サフィックス。「1番の」「1の」「1番ので」等の
    # 助詞「の」継続は全文一致のみで許可する（部分一致に入れると「2の予定で…」等を誤選択するため）。
    _NUM_SUFFIX = (r"(で(おねがい|お願い|よろしく)?(します)?|を(おねがい|お願い)?(します)?"
                   r"|の(ほう)?(で(おねがい|お願い)?(します)?|を(おねがい|お願い)?(します)?)?"
                   r"|です|だ(よ|ね)?|よ|かな(あ)?|ね)?")
    for num, label in numbers.items():
        if (re.search(rf"(^|[^0-9]){num}(ばん|番){_BAN_CONT}", t)
                or re.search(rf"^{num}(ばん|番)?{_NUM_SUFFIX}$", t)):
            result["intent"] = label
            result["confidence"] = 1
            result["reason"].append(f"L0:number:{num}")
            return result
    _KANJI_NUM = [("一", "1"), ("二", "2"), ("三", "3"), ("四", "4"), ("五", "5"),
                  ("六", "6"), ("七", "7"), ("八", "8"), ("九", "9"),
                  ("いち", "1"), ("に", "2"), ("さん", "3"), ("よん", "4"), ("ご", "5"),
                  ("ろく", "6"), ("なな", "7"), ("はち", "8"), ("きゅう", "9"), ("く", "9")]
    for kanji, digit in _KANJI_NUM:
        if digit not in numbers:
            continue
        if (re.search(rf"(^|[^一二三四五六七八九]){kanji}(ばん|番){_BAN_CONT}", t)
                or re.search(rf"^{kanji}(ばん|番)?{_NUM_SUFFIX}$", t)):
            result["intent"] = numbers[digit]
            result["confidence"] = 1
            result["reason"].append(f"L0:kanji_num:{kanji}")
            return result

    # L1.5: エンティティ抽出
    for ex in spec.get("extractors") or []:
        m = re.search(ex["regex"], t)
        if m:
            g = 1 if ex.get("group") is None else ex["group"]
            result["entities"][ex["name"]] = m.group(g)
            result["reason"].append(f"L1.5:{ex['name']}={m.group(g)}")

    facts = _detect_evidence(spec, t, result["reason"])
    facts = _build_events(spec, facts, result["reason"])
    result["evidences"] = [k for k in facts]
    fired = _apply_rules(spec, facts, result["reason"])

    if not fired:
        if len(t) <= 15:
            for m in REPEAT_MARKERS:
                if m in t:
                    result["intent"] = "REPEAT"
                    result["reason"].append(f"L5:repeat_marker:{m}")
                    return result
        qt = spec.get("question_type") or "menu"
        if qt == "yes_no":
            if facts.get("_YES_") and facts.get("_NO_"):
                result["intent"] = "CLARIFY"
                result["need_clarification"] = True
                result["reason"].append("L5:yes_no両トークン検出")
                return result
            if facts.get("_YES_"):
                result["intent"] = spec.get("yes_label") or "YES"
                result["confidence"] = 1
                result["reason"].append("L5:yes_no文脈でYES")
                return result
            if facts.get("_NO_"):
                result["intent"] = spec.get("no_label") or "NO"
                result["confidence"] = 1
                result["reason"].append("L5:yes_no文脈でNO")
                return result
        if qt == "menu" and (facts.get("_YES_") or facts.get("_NO_")):
            result["intent"] = "CLARIFY"
            result["need_clarification"] = True
            result["reason"].append("L5:menu文脈でyes/no単独 → 選択肢を特定できない")
            return result
        result["reason"].append("L6:rule不発 → NO_RESULT（推測禁止）")
        return result

    if (spec.get("question_type") or "menu") == "yes_no" \
            and facts.get("_YES_") and facts.get("_NO_"):
        result["intent"] = "CLARIFY"
        result["need_clarification"] = True
        result["reason"].append("L5:yes_no両トークン検出")
        return result

    return _resolve_conflict(spec, fired, result)


def main() -> None:
    if len(sys.argv) != 3:
        print("使い方: python3 oracle.py <spec.json> <発話テキスト>")
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    print(json.dumps(classify(spec, sys.argv[2]), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
