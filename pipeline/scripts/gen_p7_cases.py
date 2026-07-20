# -*- coding: utf-8 -*-
"""gen_p7_cases.py — 設計書 YAML から Pattern 7（連結テスト）ケース表 JSON を生成する。

設計書 scenario_flow の hearing enum 分岐を全エッジ網羅する最小ケース集合の**下書き**を出す。
出力はそのまま connection_test/stub_stt_connection.py の --cases に渡せる。
人間がゴールデンログ観察後に expect/inject を調整する前提（connection_test/REQUIREMENTS.md 参照）。

生成するケース:
  1. enum エッジ: 各 hearing の各 condition ラベルを 1 ケース（inject=ラベル文字列）
  2. DTMF エッジ: --dtmf-steps で指定した hearing は数字注入ケースも生成（1始まり=conditions 順）
  3. リトライ true: 各 hearing で ["NO_RESULT", 既定ラベル]（1回リトライ後成功）
  4. リトライ exhaust: 各 hearing で ["NO_RESULT"]（聴取失敗終話へ。catch-all 欠落の検出を兼ねる）
  5. 不正入力（^.*$）: 各 hearing で enum ラベルに一致しない入力（"INVALID_INPUT"）を注入し、
     catch-all ルートを明示的にテスト（NO_RESULT と区別して routing 挙動を確認する）
  6. 2回リトライ後成功: ["NO_RESULT", "NO_RESULT", 既定ラベル]（retry_count>=2 の設定で機能。
     retry_count=1 の場合は exhaust になるため _note で人間確認を促す）

出力は JSON ケース表に加えて、**同じテスト項目を人間確認用に CSV でも必ず書き出す**
（--csv-out で出力先を指定可。既定は JSON と同じ stem の .csv）。CSV は実機で 1 ケース
ずつ叩いて PASS/FAIL を記入するワークシートを兼ねる（Excel 想定 = utf-8-sig / BOM 付き）。

使い方:
  # 生成（JSON + CSV を同時出力）
  python scripts/gen_p7_cases.py --spec <設計書.yaml> --facility <施設> --flow <フロー> \
      [--dtmf-steps "用件確認:4,コース選択:4"] [--out connection_test/cases/<施設>_<flow>.json] \
      [--csv-out output/scenarios/<施設>_<flow>/連結テストケース_<施設>_<flow>.csv]

  # 既存ケース表（人間調整済み JSON 含む）を CSV へ変換するだけ（再生成しない）
  python scripts/gen_p7_cases.py --to-csv <既存ケース表.json> --csv-out <出力.csv>
"""
import argparse
import csv
import io
import json
import sys
from pathlib import Path

import yaml

# サブフロー系 STT の既定注入（福岡大学病院ケース表の実証値を踏襲）
SUBFLOW_DEFAULTS = {
    "_order": ["復唱", "氏名", "患者", "生年月日", "連絡先", "電話番号", "診察券", "予約日", "希望日"],
    "復唱": ["はい"],
    "氏名": ["ヤマダ タロウ"],
    "患者": ["ヤマダ タロウ"],
    "生年月日": ["19800101"],
    "連絡先": ["はい"],
    "電話番号": ["はい"],
    "診察券": ["1234567"],
    "予約日": ["20260901"],
    "希望日": ["20260901"],
    "_fallback": ["NO_RESULT"],
}


def load_flow(spec_path):
    data = yaml.safe_load(io.open(spec_path, encoding="utf-8"))
    steps = data.get("scenario_flow") or []
    smap = {}
    for s in steps:
        if isinstance(s, dict) and s.get("step"):
            smap[s["step"]] = s
    start = steps[0]["step"] if steps else None
    return smap, start


def edges_of(step):
    """step の出エッジ [(label_or_None, next_step), ...]"""
    out = []
    for c in step.get("conditions") or []:
        if c.get("next"):
            out.append((str(c.get("match", "")), c["next"]))
    if not out and step.get("next"):
        out.append((None, step["next"]))
    return out


def hearings_in(smap):
    return [s for s in smap.values()
            if s.get("type") == "hearing" and s.get("output_format") == "enum"
            and (s.get("conditions") or [])]


# ─── フラット形（分岐は type:script の認定分類器が担い、hearing は STT のみ）対応 ───
# 認定分類器の出力ラベル → STT 注入発話の対応（ラベル＝キーワードで分類されるものはラベルそのまま）。
_YESNO_INJECT = {"肯定": "はい", "否定": "いいえ"}


def _feeding_hearing(smap, script_step):
    """この script ブロックへ流入する hearing の step 名（inject 先 = 入力_<それ>）を返す。
    flat 形では hearing X(next→X_分類) のペア。見つからなければ reference_module から 入力_ を剥がす。"""
    for s in smap.values():
        if s.get("type") == "hearing" and s.get("next") == script_step:
            return s["step"]
    ref = str(smap.get(script_step, {}).get("reference_module", "") or "")
    if ref.startswith("入力_"):
        return ref[len("入力_"):]
    return script_step


# catch-all カテゴリのラベルは音声キーワードを持たず（"その他"/"その他の健診" は DTMF 専用区分）、
# 音声で当該ラベルを注入すると分類器が NO_RESULT を返す。これらは DTMF 数字を注入して到達させる。
# （実機 P7 tc28 で発覚: 用件確認 に音声「その他」→ checkup_intent NO_RESULT → 聴取失敗）。
_DTMF_INJECT = {
    ("checkup_intent_classifier", "その他"): "4",      # 用件確認 DTMF 4=その他
    ("checkup_course_classifier", "その他の健診"): "4",  # コース選択 DTMF 4=その他の健診
}

# reservation_date_classifier は DATE文字列 / "不明" / "NO_RESULT" を返す（"other" は返さない）。
# catch-all "other"(=^.*$) は有効日付の発話/DTMF で駆動する（リテラル "other" だと非日付→NO_RESULT に倒れる）。
# "不明"/"NO_RESULT" はラベルそのままで駆動（不明=UNKNOWN_RE一致 / NO_RESULT=非日付フォールスルー）。
_RESV_INJECT = {
    "other": "20260901",
}


def _inject_for(part, label):
    """分類器の出力ラベルを得るための STT 注入発話。yes_no は はい/いいえ、
    catch-all 区分(その他/その他の健診)は DTMF 数字、他はラベルそのまま（=音声キーワード）。"""
    if (part, label) in _DTMF_INJECT:
        return _DTMF_INJECT[(part, label)]
    if part == "yes_no_classifier":
        return _YESNO_INJECT.get(label, label)
    if part == "reservation_date_classifier":
        return _RESV_INJECT.get(label, label)
    return label


def decisions_in(smap):
    """分岐点（ケースを起こす単位）を列挙。
    enum hearing（旧 OpenAI 形）と、conditions を持つ type:script（フラット形の認定分類器）の両方。
    type:intent / type:phone_branch / type:faq / type:clinical_department も条件分岐として扱う。
    返り値: {step, node(inject先), conds[(label,next)], part}"""
    out = []
    for s in smap.values():
        t = s.get("type", "")
        if t == "hearing" and s.get("output_format") == "enum" and (s.get("conditions") or []):
            out.append({"step": s["step"], "node": "入力_" + s["step"],
                        "conds": [(str(c.get("match", "")), c.get("next", "")) for c in s["conditions"]],
                        "part": None})
        elif t == "script" and (s.get("conditions") or []):
            feeder = _feeding_hearing(smap, s["step"])
            out.append({"step": s["step"], "node": "入力_" + feeder,
                        "conds": [(str(c.get("match", "")), c.get("next", "")) for c in s["conditions"]],
                        "part": s.get("script_template")})
        elif t == "intent" and (s.get("conditions") or s.get("options")):
            # intent: conditions から分岐先を収集。NO_RESULT / REPEAT は除外（内部ループ）
            conds = [(str(c.get("match", "")), c.get("next", ""))
                     for c in (s.get("conditions") or [])
                     if c.get("match") not in ("NO_RESULT", "REPEAT")]
            if not conds:
                conds = [(str(o.get("label", "")), "")
                         for o in (s.get("options") or [])]
            out.append({"step": s["step"], "node": "入力_" + s["step"],
                        "conds": conds, "part": "intent"})
        elif t in ("phone_branch", "faq") and (s.get("conditions") or []):
            conds = [(str(c.get("match", c.get("label", ""))), c.get("next", ""))
                     for c in s["conditions"]
                     if c.get("match") not in ("NO_RESULT",)]
            if conds:
                node = s["step"] if t == "phone_branch" else "入力_" + s["step"]
                out.append({"step": s["step"], "node": node,
                            "conds": conds, "part": t})
        elif t == "card_number":
            # 不明か未所持 / 番号あり の2分岐
            next_found   = str(s.get("next_found", s.get("next", "")))
            next_unknown = str(s.get("next_unknown", s.get("next", "")))
            conds = []
            if next_found:
                conds.append(("12345678", next_found))
            if next_unknown and next_unknown != next_found:
                conds.append(("不明か未所持", next_unknown))
            if conds:
                out.append({"step": s["step"], "node": "入力_" + s["step"],
                            "conds": conds, "part": "card_number"})
            # echo_back: true → 復唱確認分岐（はい=next_found / いいえ=TTS再生）
            if s.get("echo_back"):
                echo_node = "入力_%s_復唱" % s["step"]
                echo_conds = []
                if next_found:
                    echo_conds.append(("はい", next_found))
                echo_conds.append(("いいえ", s["step"]))  # いいえ → TTS 冒頭へ戻る
                out.append({"step": s["step"] + "_復唱確認", "node": echo_node,
                            "conds": echo_conds, "part": "card_number_echo"})
        elif t == "clinical_department" and (s.get("conditions") or []):
            conds = [(str(c.get("match", "")), c.get("next", ""))
                     for c in s["conditions"]
                     if c.get("match") not in ("NO_RESULT",)]
            if conds:
                out.append({"step": s["step"], "node": "入力_" + s["step"],
                            "conds": conds, "part": "clinical_department"})
    return out


def find_path(smap, dmap, start, target, _seen=None):
    """start から target step までの (inject_node, 注入発話) 列を DFS で探す。
    分岐点(dmap=enum hearing / script 認定分類器)は label エッジを辿りながら注入を記録、
    それ以外（announcement/CMR/text hearing 等）は定義順の先頭エッジを辿る（下書き・人間確認前提）。"""
    _seen = _seen or set()
    if start == target:
        return []
    if start in _seen or start not in smap:
        return None
    _seen = _seen | {start}
    if start in dmap:
        d = dmap[start]
        for label, nxt in d["conds"]:
            sub = find_path(smap, dmap, nxt, target, _seen)
            if sub is None:
                continue
            return [(d["node"], _inject_for(d["part"], label))] + sub
        return None
    for label, nxt in edges_of(smap[start]):
        sub = find_path(smap, dmap, nxt, target, _seen)
        if sub is not None:
            return sub
    return None


def default_label(step):
    conds = step.get("conditions") or []
    return str(conds[0].get("match", "")) if conds else None


def _default_edge(step):
    """既定経路で選ぶ出エッジ。CMR は other/default を優先（上流注入なしの素通り想定）。"""
    es = edges_of(step)
    if not es:
        return None
    if step.get("type") == "context_match_router":
        for label, nxt in es:
            if label in ("other", "default", "^.*$"):
                return (label, nxt)
    return es[0]


def nearest_terminal(smap, start, hops=30):
    """start から既定経路を辿って最初の termination step 名を返す（見つからなければログ観察）"""
    cur = start
    for _ in range(hops):
        if cur not in smap:
            return "ログ観察"
        step = smap[cur]
        if step.get("type") == "termination" or step.get("termination_ref"):
            return cur
        e = _default_edge(step)
        if e is None:
            return cur
        cur = e[1]
    return "ログ観察"


def build_defaults(smap):
    """メインフロー全 hearing の既定注入を生成し、サブフロー既定とマージする。
    ケースの inject に無いノードは stub がここへフォールバックして完走する（完走させるための最善推定）。
    enum=先頭 condition ラベル / datetime=20260901 / それ以外（自由発話等）=テスト文言。"""
    defaults = dict(SUBFLOW_DEFAULTS)
    # フラット形: text hearing が養う script（認定分類器）の先頭ラベルへ前進させる既定注入を引く
    feed = {}  # hearing step -> (part, first_label)
    for s in smap.values():
        if s.get("type") == "script" and (s.get("conditions") or []):
            feeder = _feeding_hearing(smap, s["step"])
            feed[feeder] = (s.get("script_template"), str(s["conditions"][0].get("match", "")))
    main_keys = []
    for s in smap.values():
        t = s.get("type", "")
        # intent / clinical_department / free_text / faq もデフォルト発話を生成する
        if t == "intent" and not s.get("step") in defaults:
            opts = s.get("options") or []
            defaults[s["step"]] = [str(opts[0].get("label", "テスト")) if opts else "テスト"]
            main_keys.append(s["step"])
        elif t in ("clinical_department",) and s["step"] not in defaults:
            depts = s.get("departments") or []
            first_key = depts[0].get("canonical", "内科") if depts and isinstance(depts[0], dict) else "内科"
            defaults[s["step"]] = [first_key]
            main_keys.append(s["step"])
        elif t == "free_text" and s["step"] not in defaults:
            defaults[s["step"]] = ["テストの問い合わせです"]
            main_keys.append(s["step"])
        elif t == "faq" and s["step"] not in defaults:
            defaults[s["step"]] = ["テストの問い合わせです"]
            main_keys.append(s["step"])
        elif t == "card_number" and s["step"] not in defaults:
            defaults[s["step"]] = ["12345678"]
            main_keys.append(s["step"])
        if t != "hearing":
            continue
        name = s["step"]
        if name in feed:                       # 分類器を養う text hearing → 先頭ラベル相当の発話
            part, first_label = feed[name]
            defaults[name] = [_inject_for(part, first_label)]
        elif s.get("output_format") == "enum" and (s.get("conditions") or []):
            defaults[name] = [default_label(s)]
        elif s.get("output_format") == "datetime" or s.get("stt_success_condition") \
                or "予約日" in name:
            defaults[name] = ["20260901"]
        else:
            defaults[name] = ["テストの問い合わせです"]
        main_keys.append(name)
    # フラット形 slot（type:slot）内部の自動生成ノードの既定注入。
    # 復唱確認(はい/いいえ)・手入力番号など。汎用語(生年月日/電話番号)に shadow されないよう
    # より長い専用キーを _order の先頭側に置く（FB-9 系の汎用語シャドウ対策）。
    slot_keys = []
    for s in smap.values():
        t = s.get("type", "")
        slot_val = s.get("slot", "")
        is_dob   = (t == "dob") or (t == "slot" and slot_val == "date_of_birth")
        is_phone = (t == "phone") or (t == "slot" and slot_val == "phone")
        if t not in ("slot", "dob", "phone", "patient_name"):
            continue
        st = s["step"]
        if is_dob:
            defaults["%s_確認" % st] = ["はい"]      # 入力_<step>_確認 = DOB 復唱の はい/いいえ
            slot_keys.append("%s_確認" % st)
        elif is_phone:
            # 忠実版 phone slot の内部ノード: ANI確認 / 連絡先確認 = はい/いいえ、連絡先 = 番号。
            defaults["%s_ANI確認" % st] = ["はい"]     # 入力_<step>_ANI確認
            defaults["%s_連絡先確認" % st] = ["はい"]   # 入力_<step>_連絡先確認
            defaults["%s_連絡先" % st] = ["09012345678"]  # 入力_<step>_連絡先 = 連絡先番号(固定/別番号路)
            slot_keys.append("%s_ANI確認" % st)
            slot_keys.append("%s_連絡先確認" % st)
            slot_keys.append("%s_連絡先" % st)
    # 専用キー(slot) → main_keys → サブフロー汎用 の順。各群内は長い順（部分文字列衝突回避）。
    slot_keys.sort(key=len, reverse=True)
    main_keys.sort(key=len, reverse=True)
    defaults["_order"] = slot_keys + main_keys + SUBFLOW_DEFAULTS["_order"]
    return defaults


def _strip_anchors(pat: str) -> str:
    """^ラベル$ 形式の regex から素のラベルを取り出す（完全一致 regex のみ想定）。"""
    return pat.lstrip("^").rstrip("$")


def _cmr_ref_step(smap, ref: str) -> str | None:
    """CMR の reference_module（例: OpenAI_用件確認 / 入力_用件確認 / 用件確認）から
    設計書上の step 名を解決する。見つからなければ None。"""
    if not ref:
        return None
    for prefix in ("OpenAI_", "入力_", "script_", ""):
        cand = ref[len(prefix):] if prefix and ref.startswith(prefix) else (ref if not prefix else None)
        if cand and cand in smap:
            return cand
    # 部分一致フォールバック（reference_module にサフィックスが付くケース）
    for stp in smap:
        if stp and stp in ref:
            return stp
    return None


def build_valid_e2e_cases(smap, start, dmap, add, max_hops=80):
    """正常系を end-to-end（開始→終端の完走 1 本 = 1 ケース）で列挙する。
    - 判定ノード（enum hearing / intent / faq / script 等）で正しいラベルごとに分岐を fork
    - context_match_router は上流で注入したラベルから決定論的にエッジを解決
      （一致エッジ無し→catch-all。上流未注入→既定エッジ + 人間確認ノート）
    - ループ（faq の再質問等）は同一判定ノードの再訪で打ち切り、その時点の既定終端で確定
    ケース数 = 正常入力で辿れる完走ルート数。"""
    results = []

    def walk(step, inject, chosen, checkpoints, covers, note, hops):
        if hops > max_hops:
            results.append((inject, checkpoints, covers,
                            "ログ観察", (note or "") + "★hop 上限で打ち切り"))
            return
        if not step or step not in smap:
            results.append((inject, checkpoints, covers, step or "ログ観察", note))
            return
        s = smap[step]
        if s.get("type") == "termination" or s.get("termination_ref"):
            results.append((inject, checkpoints, covers, step, note))
            return

        if s.get("type") == "context_match_router":
            conds = [(str(c.get("match", "")), c.get("next", ""))
                     for c in (s.get("conditions") or [])]
            ref_step = _cmr_ref_step(smap, str(s.get("reference_module", "")))
            val = chosen.get(ref_step) if ref_step else None
            edge = None
            if val is not None:
                edge = next(((l, n) for l, n in conds if _strip_anchors(l) == val), None)
            if edge is None:
                edge = next(((l, n) for l, n in conds
                             if l in ("^.*$", ".*", "^*$", "other", "default")), None)
            if edge is None and conds:
                edge = conds[0]
                note = (note or "") + f"★CMR {step}: 上流値未解決のため先頭エッジを仮採用（人間確認）"
            if edge is None:
                results.append((inject, checkpoints, covers, step, note))
                return
            walk(edge[1], inject, chosen,
                 checkpoints + [f"{step}:{_strip_anchors(edge[0])}"],
                 covers + [f"{step}(CMR) {edge[0]}→{edge[1]}"],
                 note, hops + 1)
            return

        d = dmap.get(step)
        if d:
            if step in chosen:
                # ループ再訪（faq 再質問等）: これ以上 fork せず既定終端で確定
                results.append((inject, checkpoints + [f"{step}:再訪打ち切り"],
                                covers, nearest_terminal(smap, step), note))
                return
            fwd = [(l, n) for l, n in d["conds"]
                   if l not in ("NO_RESULT",) and not l.startswith("リトライ_")
                   and l not in ("^.*$", ".*", "^*$")]
            if not fwd:
                e = _default_edge(s)
                walk(e[1] if e else "", inject, chosen, checkpoints, covers, note, hops + 1)
                return
            for label, nxt in fwd:
                inj2 = dict(inject)
                inj2[d["node"]] = [_inject_for(d["part"], label)]
                ch2 = dict(chosen)
                ch2[step] = _strip_anchors(label)
                walk(nxt, inj2, ch2,
                     checkpoints + [f"{step}:{_strip_anchors(label)}"],
                     covers + [f"{d['node']}({d['part'] or 'enum'}) ^{label}$→{nxt}"],
                     note, hops + 1)
            return

        e = _default_edge(s)
        if e is None:
            results.append((inject, checkpoints, covers, step, note))
            return
        walk(e[1], inject, chosen, checkpoints, covers, note, hops + 1)

    walk(start, {}, {}, [], [], None, 0)
    return [add(inj, terminal, cps, cov, note or None, tier="valid")
            for inj, cps, cov, terminal, note in results]


def build_cases(smap, start, dtmf_steps):
    cases = []
    cid = 0
    dmap = {d["step"]: d for d in decisions_in(smap)}

    def add(inject, expect_end, checkpoints, covers, note=None, tier="valid"):
        nonlocal cid
        cid += 1
        c = {"id": str(cid), "dtmf": str(cid),
             "inject": inject,
             "expect": {"終端": expect_end, "checkpoints": checkpoints},
             "covers": covers,
             # tier: "valid"=正常系（spec 準拠入力・正しい分岐）/ "invalid"=異常系
             # （NO_RESULT リトライ・exhaust・catch-all 不正入力）。
             # TTS プレビューは valid のみ、STT スタブ連結は valid+invalid 全部を使う。
             "tier": tier}
        if note:
            c["_note"] = note
        return c

    # 1. 正常系: end-to-end 完走ルート列挙（開始→終端 1 本 = 1 ケース。
    #    CMR は上流注入ラベルから決定論解決・catch-all 含む）
    cases.extend(build_valid_e2e_cases(smap, start, dmap, add))

    for d in decisions_in(smap):
        name = d["step"]
        node = d["node"]
        part = d["part"]
        conds = d["conds"]
        path = find_path(smap, dmap, start, name)
        if path is None:
            path = []
            note_path = "★start から %s への経路を自動解決できず。inject を人間調整のこと" % name
        else:
            note_path = None
        base_inject = {n: [v] for n, v in path}

        # 2. リトライ true（1回 NO_RESULT 後に既定ラベルで成功）
        fwd = [(l, n) for l, n in conds if l not in ("NO_RESULT",) and not l.startswith("リトライ_")]
        if fwd:
            dflt_label, dflt_nxt = fwd[0]
            inj = dict(base_inject)
            inj[node] = ["NO_RESULT", _inject_for(part, dflt_label)]
            cases.append(add(
                inj, nearest_terminal(smap, dflt_nxt),
                ["リトライ_%s:true" % name, "%s:%s" % (name, dflt_label)],
                ["リトライ_%s true（1回戻り→成功）" % name],
                note_path, tier="invalid"))
        # 3. リトライ exhaust（聴取失敗終話 or デッドエンド検出）
        inj = dict(base_inject)
        inj[node] = ["NO_RESULT"]
        cases.append(add(
            inj, "完了フラグ_聴取失敗",
            ["リトライ_%s:false" % name],
            ["リトライ_%s false（exhaust）。デッドエンドが出たら構造監査所見として記録" % name],
            note_path, tier="invalid"))

        # 4. 不正入力（catch-all ^.*$ ルート）: enum ラベルに一致しない文字列を注入
        #    NO_RESULT は STT 認識失敗（リトライ）と同義。不正入力は認識できたが enum 外の値。
        #    catch-all の遷移先（前進 or ループ）を明示的にテストする。
        inj = dict(base_inject)
        inj[node] = ["INVALID_INPUT"]
        catchall_nxt = next((n for l, n in conds if l in ("^.*$", ".*", "^*$")), None)
        catchall_term = nearest_terminal(smap, catchall_nxt) if catchall_nxt else "★catch-all未設定（要確認）"
        cases.append(add(
            inj, catchall_term,
            ["%s:catch-all" % name, catchall_nxt or "未設定"],
            ["%s ^.*$（不正入力→catch-all ルート検証）" % node],
            (note_path or "") + ("★ catch-all 未設定: no ^.*$ in conditions。E-16 catch-all 欠落を確認"
                                 if not catchall_nxt else None),
            tier="invalid"))

        # 5. 2回リトライ後成功（retry_count>=2 の設定で意味を持つ）
        if fwd:
            dflt_label, dflt_nxt = fwd[0]
            inj = dict(base_inject)
            inj[node] = ["NO_RESULT", "NO_RESULT", _inject_for(part, dflt_label)]
            cases.append(add(
                inj, nearest_terminal(smap, dflt_nxt),
                ["リトライ_%s:true" % name, "リトライ_%s:true" % name, "%s:%s" % (name, dflt_label)],
                ["リトライ_%s 2回失敗→3回目成功（retry_count>=2 の場合のみ有効）" % name],
                (note_path or "") + "retry_count=1 の設定ではこのケースは exhaust になる（設計書と突合のこと）",
                tier="invalid"))

    return cases


# ---------------------------------------------------------------------------
# CSV 書き出し（テスト項目を人間確認/結果記入用に必ず出す）
# ---------------------------------------------------------------------------

# 列順は SSoT。stub_stt_connection.py が消費する JSON とは別物（人間が読む/記入する表）。
# 着信種別(固定/携帯/非通知…)のケースは inject に分類器ノードを入れるため、注入STT列に現れる。
CSV_HEADER = [
    "ケースID",          # id（= 発信後に押す DTMF）
    "優先",             # --touched 指定時: 修正箇所を通るケース=高（先に実行）/ それ以外は空欄
    "区分",             # tier: 正常系（spec準拠入力・正しい分岐）/ 異常系（リトライ/exhaust/catch-all）
    "DTMF入力",          # dtmf + #（ケース選択）
    "注入STT（発話/入力）",  # inject: ノード=試行1→試行2 ...（分類器ノードもここに出る）
    "期待終端",          # expect.終端
    "チェックポイント",    # expect.checkpoints
    "カバレッジ",         # covers
    "備考",             # _note（経路自動解決失敗の人間調整フラグ等）
    "判定(PASS/FAIL)",   # 実機実行後に人間が記入（空欄で出力）
    "実機ログ・メモ",      # 同上（空欄で出力）
]


def _inject_to_text(inject) -> str:
    """inject dict を人間可読な文字列へ。配列は試行順を → でつなぐ（attempt-aware）。"""
    if not isinstance(inject, dict):
        return str(inject or "")
    parts = []
    for node, vals in inject.items():
        if isinstance(vals, (list, tuple)):
            joined = "→".join(str(v) for v in vals)
        else:
            joined = str(vals)
        parts.append(f"{node}: {joined}")
    return " / ".join(parts)


def cases_csv_rows(obj: dict) -> list:
    """ケース表 obj（JSON）からヘッダー込みの CSV 行リストを生成する。
    gen_p7_cases.py 自動生成・人間調整済みのどちらの JSON でも壊れないよう防御的に読む。"""
    rows = [list(CSV_HEADER)]
    for c in obj.get("cases") or []:
        if not isinstance(c, dict):
            continue
        expect = c.get("expect") or {}
        if isinstance(expect, dict):
            terminal = str(expect.get("終端", "") or "")
            checks = expect.get("checkpoints") or []
        else:
            terminal, checks = str(expect), []
        covers = c.get("covers") or []
        rows.append([
            str(c.get("id", "")),
            "高" if c.get("priority") == "high" else "",
            "正常系" if c.get("tier", "valid") == "valid" else "異常系",
            str(c.get("dtmf", "")),
            _inject_to_text(c.get("inject")),
            terminal,
            " / ".join(str(x) for x in checks) if isinstance(checks, (list, tuple)) else str(checks),
            " / ".join(str(x) for x in covers) if isinstance(covers, (list, tuple)) else str(covers),
            str(c.get("_note", "") or ""),
            "",  # 判定（人間記入）
            "",  # 実機ログ・メモ（人間記入）
        ])
    return rows


def write_cases_csv(obj: dict, csv_path) -> int:
    """ケース表 obj を CSV へ書き出す。Excel(Windows) 想定で utf-8-sig（BOM 付き）。
    戻り値はデータ行数（ヘッダー除く）。"""
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    rows = cases_csv_rows(obj)
    with io.open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(rows)
    return max(0, len(rows) - 1)


def _default_csv_path(facility: str, flow: str, json_out: Path) -> Path:
    """CSV 既定出力先。施設/フローが分かれば成果物ディレクトリ、無ければ JSON と同じ stem。"""
    if facility and flow:
        return (Path("output") / "scenarios" / f"{facility}_{flow}"
                / f"連結テストケース_{facility}_{flow}.csv")
    return json_out.with_suffix(".csv")


def compute_coverage(smap, cases):
    """設計書の全エッジ数と、生成ケースで網羅されたエッジ数を計算して dict を返す。
    covers フィールドから "step(part) ^label$→next" 形式のエントリを数える。"""
    # 全エッジ: decisions_in の全 conds から NO_RESULT/リトライ除く
    total_edges = 0
    covered_labels = set()
    for d in decisions_in(smap):
        for label, nxt in d["conds"]:
            if label not in ("NO_RESULT",) and not label.startswith("リトライ_"):
                total_edges += 1
    # カバーされたエッジ: cases の covers から抽出
    for c in cases:
        for cov in (c.get("covers") or []):
            cov_str = str(cov)
            # "node(part) ^label$→next" または "node(enum) ^label$→next" 形式
            if "^" in cov_str and "→" in cov_str:
                covered_labels.add(cov_str)
    covered = len(covered_labels)
    pct = int(100 * covered / total_edges) if total_edges else 100
    # failure paths: リトライ exhaust ケース数
    retry_exhaust = sum(1 for c in cases
                        for cp in (c.get("expect", {}).get("checkpoints") or [])
                        if isinstance(cp, str) and cp.startswith("リトライ_") and cp.endswith(":false"))
    return {
        "total_decision_edges": total_edges,
        "covered_edges": covered,
        "coverage_pct": pct,
        "retry_exhaust_cases": retry_exhaust,
        "unresolved_paths": sum(1 for c in cases if c.get("_note")),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=None, help="設計書 YAML（生成モードで必須）")
    ap.add_argument("--facility", default=None)
    ap.add_argument("--flow", default=None)
    ap.add_argument("--entry-flow", default=None, help="セレクタ前置フロー短名（省略時 flow）")
    ap.add_argument("--dtmf-steps", default="", help="例: 用件確認:4,コース選択:4（step:選択肢数）")
    ap.add_argument("--out", default=None)
    ap.add_argument("--csv-out", default=None, help="テスト項目 CSV の出力先（省略時は既定パス）")
    ap.add_argument("--to-csv", default=None,
                    help="既存ケース表 JSON を CSV へ変換するだけ（再生成しない）。--csv-out 推奨")
    ap.add_argument("--touched", default="",
                    help="Pattern 2 patch 適用後の優先マーキング: 変更されたモジュール名を"
                         "カンマ区切りで指定（bivr_patch の touched 出力）。inject/checkpoints/"
                         "covers がこれらに触れるケースを 優先=高 として CSV 先頭列に表示する")
    ap.add_argument("--tier", default="all", choices=["all", "tts_preview", "stt_stub"],
                    help="all=全件（既定・後方互換） / tts_preview=正常系のみ"
                         "（spec準拠入力・正しい分岐 = 正しい luồng 数だけ。TTS 試聴用）/ "
                         "stt_stub=正常系+異常系 全件（TTS/AmiVoice をスキップする STT スタブ連結用。"
                         "異常系 = 不正入力を処理する全ルート: リトライ/exhaust/catch-all）")
    args = ap.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    # ── 変換専用モード: 既存 JSON（人間調整済み含む）→ CSV ──
    if args.to_csv:
        src = Path(args.to_csv)
        if not src.exists():
            raise SystemExit(f"[ERROR] ケース表 JSON が見つかりません: {src}")
        obj = json.loads(io.open(src, encoding="utf-8").read())
        meta = obj.get("meta") or {}
        csv_path = Path(args.csv_out) if args.csv_out else _default_csv_path(
            args.facility or meta.get("facility", ""),
            args.flow or meta.get("flow", ""), src)
        n = write_cases_csv(obj, csv_path)
        print("[OK] %d ケースを CSV へ書き出し → %s" % (n, csv_path))
        return

    # ── 生成モード: --spec/--facility/--flow が必須 ──
    missing = [n for n, v in (("--spec", args.spec), ("--facility", args.facility),
                              ("--flow", args.flow)) if not v]
    if missing:
        raise SystemExit("[ERROR] 生成モードでは %s が必須です（--to-csv 変換モードを除く）"
                         % ", ".join(missing))

    dtmf_steps = {}
    for tok in [t for t in args.dtmf_steps.split(",") if t.strip()]:
        k, _, v = tok.partition(":")
        dtmf_steps[k.strip()] = int(v or "0")

    smap, start = load_flow(args.spec)
    if not start:
        raise SystemExit("[ERROR] scenario_flow が空")
    cases = build_cases(smap, start, dtmf_steps)
    # tier フィルタ: tts_preview は正常系のみ（ID は振り直す — DTMF セレクタ番号の欠番を防ぐ）。
    # stt_stub / all は正常系+異常系の全件（stt_stub は用途ラベルのみ異なる）。
    if args.tier == "tts_preview":
        cases = [c for c in cases if c.get("tier") == "valid"]
        for i, c in enumerate(cases, 1):
            c["id"] = str(i)
            c["dtmf"] = str(i)
    # --touched: 修正箇所（bivr_patch の touched モジュール）を通るケースを 優先=high にマーク。
    # 判定は inject のノード名 / checkpoints / covers の文字列に touched 名が現れるか（部分一致）。
    touched = [t.strip() for t in (args.touched or "").split(",") if t.strip()]
    if touched:
        n_pri = 0
        for c in cases:
            hay = " ".join(
                list((c.get("inject") or {}).keys())
                + [str(x) for x in (c.get("expect", {}) or {}).get("checkpoints", [])]
                + [str(x) for x in (c.get("covers") or [])]
                + [str((c.get("expect", {}) or {}).get("終端", ""))])
            if any(t in hay for t in touched):
                c["priority"] = "high"
                n_pri += 1
        print("[OK] 優先マーキング: touched=%s に触れるケース %d 件を 優先=高 に設定"
              % (touched, n_pri))
        if n_pri == 0:
            print("[WARN] touched モジュールを通るケースが 0 件 — 修正箇所がケース表で"
                  "被覆されていない可能性（extract_scaffold の抽出漏れ or 手動ケース追加を検討）")

    n_valid = sum(1 for c in cases if c.get("tier") == "valid")
    n_invalid = len(cases) - n_valid
    coverage = compute_coverage(smap, cases)

    out = {
        "_about": ("連結(実機統合)テスト ケース表（gen_p7_cases.py 自動生成の下書き）。"
                   "STTを定数注入し本番フローを実機ハンズフリー実行。冒頭でDTMFケース番号を選択。"
                   "inject値は配列=試行回数依存(attempt-aware)。expect はログ観察後に人間が確定させる。"),
        "meta": {"facility": args.facility, "flow": args.flow,
                 "entry_flow": args.entry_flow or args.flow,
                 "generated_by": "scripts/gen_p7_cases.py",
                 "tier": args.tier,
                 "case_counts": {"valid": n_valid, "invalid": n_invalid,
                                 "total": n_valid + n_invalid},
                 "spec": str(args.spec)},
        "coverage": coverage,
        "selector": {"context": "__tc_id", "module": "__テストセレクタ", "usage": "発信→ケース番号+#"},
        "defaults": build_defaults(smap),
        "cases": cases,
    }

    out_path = Path(args.out) if args.out else \
        Path("connection_test") / "cases" / ("%s_%s.json" % (args.facility, args.flow))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    io.open(out_path, "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print("[OK] %d ケース生成（tier=%s: 正常系 %d / 異常系 %d）→ %s"
          % (len(cases), args.tier, n_valid, n_invalid, out_path))
    print("[COV] エッジ網羅率: %d/%d (%d%%)  リトライ exhaust: %d件  経路未解決: %d件" % (
        coverage["covered_edges"], coverage["total_decision_edges"],
        coverage["coverage_pct"], coverage["retry_exhaust_cases"],
        coverage["unresolved_paths"]))

    # テスト項目 CSV を必ず書き出す（人間確認/結果記入用ワークシート）
    csv_path = Path(args.csv_out) if args.csv_out else \
        _default_csv_path(args.facility, args.flow, out_path)
    n_csv = write_cases_csv(out, csv_path)
    print("[OK] テスト項目 CSV %d 行 → %s" % (n_csv, csv_path))

    if coverage["unresolved_paths"]:
        print("[WARN] 経路自動解決できず人間調整が必要なケース: %d 件（_note 参照）" % coverage["unresolved_paths"])


if __name__ == "__main__":
    main()
