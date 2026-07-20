# -*- coding: utf-8 -*-
"""inquiry_classifier 用件分類 spec コンポーザ（factory-v2・分岐集合からの決定論合成）。

【設計（2026-06-22 浜口さん壁打ち）】用件分類 RULES は1施設固定でなく、シナリオの
分岐集合（drawio conditions[].match）から決定論で合成する＝「半分動的」。
  - アクション分岐（予約確認 / 予約変更 / 予約キャンセル）を持つシナリオ → その発話はそのラベルへ
  - 持たない施設 → その発話は 予約(新規) から exclude され catch-all（その他問合せ=FAQ）へ
キモ: 予約(新規) は全アクション信号（取消/変更/確認の全語彙）を常に exclude する純・新規枠。
  これで「いつ予約できますか」「予約を確認したい」「予約を変更」等は、対応分岐があればそこへ／
  無ければ FAQ へ、と分岐集合だけで動的に決まる（ランタイム動的でなく生成時の決定論）。

engine（script.js）は不変。本コンポーザは @spec ブロック（RULES / NO_QUESTION / FILLER_ONLY）を
合成・レンダリングするだけ＝同 engine_hash・プロファイルごとに新 spec_hash。

oracle_classify は engine（script.js / oracle.py）と 1:1 のパリティ参照。
"""
import re

# ── アクション・ブロック（label → groups(AND の OR 集合)）。先勝ち優先順位＝この並び。
ACTION_BLOCKS = [
    ("予約キャンセル", [r"キャンセル|取り消し|取消|取りやめ|取り止め|やめたい|止めたい|中止"]),
    ("予約変更",       [r"変更|変えたい|変える|ずらし|ずらす|別の日|日にち.*変|日程.*変|時間.*変|振替|振り替え|繰り上げ|繰り下げ|早めたい|遅らせ"]),
    ("予約確認",       [r"確認|予約状況|取れて|入ってます|入ってる|合ってます|できてますか|いつ.*予約|予約.*いつ|予約.*でした|いつ.*でした"]),
]
RESERVE_LABEL = "予約"
RESERVE_GROUPS = [r"予約|ご予約|受診|診察|外来|診てもらい|診てほしい|みてもらい|みてほしい|初診|かかりたい|受けたい"]
CATCHALL_LABEL = "その他問合せ"  # FAQ。分岐に存在する前提。無ければ catch-all 無し＝engine の "その他" fallthrough。

# 予約(新規) の exclude = 全アクション信号の和（present 有無に依らず常に弾く）。
ALL_ACTION_SIGNALS = "|".join(g for _, groups in ACTION_BLOCKS for g in groups)

# NO_QUESTION / FILLER_ONLY は engine 既定（亀田 spec と同一）を流用（汎用・施設非依存）。
NO_QUESTION_SRC = r"^(特にありません|特にないです|特にない|ないです|ありません|なし|無し|大丈夫です|だいじょうぶです|結構です|けっこうです|以上です|いじょうです)$"
FILLER_ONLY_SRC = r"^(えー[っとー]*|えっと|えーっと|あのー?|うーん?|まあ|その|はい|うん|ん+)+$"

_NO_QUESTION = re.compile(NO_QUESTION_SRC)
_FILLER_ONLY = re.compile(FILLER_ONLY_SRC)
_PUNCT = re.compile(r"[、。,.!?！？\s\r\n\t]")
_DIGITS_ONLY = re.compile(r"^[0-9０-９]+$")

_SPEC_BEGIN = "// @spec-begin"
_SPEC_END = "// @spec-end"


def compose_rules(present_labels):
    """シナリオの分岐集合 → RULES list（@spec に充填される実体・engine と同じ構造）。"""
    present = set(present_labels)
    rules = []
    for label, groups in ACTION_BLOCKS:
        if label in present:
            rules.append({"label": label, "groups": list(groups), "exclude": ""})
    if RESERVE_LABEL in present:
        rules.append({"label": RESERVE_LABEL, "groups": list(RESERVE_GROUPS),
                      "exclude": ALL_ACTION_SIGNALS})
    if CATCHALL_LABEL in present:
        rules.append({"label": CATCHALL_LABEL, "groups": [r"."], "exclude": ""})
    return rules


def output_labels(present_labels):
    """合成 spec が出力しうるラベル集合（part.json 登録用・NO_RESULT 込み）。"""
    present = set(present_labels)
    labels = [lb for lb, _ in ACTION_BLOCKS if lb in present]
    if RESERVE_LABEL in present:
        labels.append(RESERVE_LABEL)
    if CATCHALL_LABEL in present:
        labels.append(CATCHALL_LABEL)
    labels.append("NO_RESULT")
    return labels


def oracle_classify(input_text, rules):
    """engine（script.js）と 1:1 の Python 参照。"""
    if input_text is None or input_text == "":
        return "NO_RESULT"
    normalized = _PUNCT.sub("", str(input_text))
    if normalized == "":
        return "NO_RESULT"
    if _NO_QUESTION.match(normalized):
        return "NO_RESULT"
    if _FILLER_ONLY.match(normalized):
        return "NO_RESULT"
    if _DIGITS_ONLY.match(normalized):
        return "NO_RESULT"
    for rule in rules:
        if rule["exclude"] and re.search(rule["exclude"], normalized):
            continue
        if all(re.search(g, normalized) for g in rule["groups"]):
            return rule["label"]
    return "NO_RESULT"


def _js_str(s):
    """JS 文字列リテラル化（regex source 用。" と \\ をエスケープ）。"""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def render_spec_block(rules):
    """RULES list → @spec ブロック JS テキスト（マーカー込み・Nashorn ES5）。"""
    lines = [_SPEC_BEGIN,
             "// 用件分類ルール（配列順＝優先順位。groups は AND、exclude は排他。先勝ち）",
             "// compose_spec.py が分岐集合から決定論合成（factory-v2）。",
             "var RULES = ["]
    for i, r in enumerate(rules):
        groups_js = ", ".join(_js_str(g) for g in r["groups"])
        comma = "," if i < len(rules) - 1 else ""
        lines.append("    { label: %s, groups: [%s], exclude: %s }%s"
                     % (_js_str(r["label"]), groups_js, _js_str(r["exclude"]), comma))
    lines.append("];")
    lines.append("var NO_QUESTION = /%s/;" % NO_QUESTION_SRC)
    lines.append("var FILLER_ONLY = /%s/;" % FILLER_ONLY_SRC)
    lines.append(_SPEC_END)
    return "\n".join(lines)


def render_full_script(template_text, present_labels):
    """engine テンプレ（script.js）の @spec 領域を合成ブロックで差し替えた filled script。"""
    spec_block = render_spec_block(compose_rules(present_labels))
    out, in_spec, replaced = [], False, False
    for ln in template_text.replace("\r\n", "\n").split("\n"):
        s = ln.strip()
        if s.startswith(_SPEC_BEGIN):
            in_spec = True
            if not replaced:
                out.append(spec_block)
                replaced = True
            continue
        if s.startswith(_SPEC_END):
            in_spec = False
            continue
        if in_spec:
            continue
        out.append(ln)
    if not replaced:
        raise ValueError("template に @spec-begin/@spec-end が見つかりません")
    return "\n".join(out)
