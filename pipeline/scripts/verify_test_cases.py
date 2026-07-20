#!/usr/bin/env python3
"""P7 連結テスト cases.json の事前妥当性チェック（Issue #304）。

実機テストを流す前に、cases.json が本体 BIVR と整合しているかを機械検証する。
実機で「大量 FAIL → cases 修正 → 再架電」を繰り返す時間コストを、架電前に潰すためのツール。

使い方:
  python3 scripts/verify_test_cases.py --cases connection_test/cases/<施設>_<flow>.json \
                                       --bivr output/scenarios/<施設>_<flow>/<本体>.bivr

判定（確信が持てる時だけ FAIL。曖昧なものは [UNVERIFIED] で列挙し exit 0 のまま）:
  [INJECT-UNKNOWN-MODULE]  inject キーが BIVR に実在しない STT/分類器ノード（typo・stale）           … FAIL
  [INJECT-OFF-DICT]        注入発話が分類器 spec で当該ラベルに分類されず NO_RESULT に倒れる（辞書外）… FAIL
  [INJECT-MISSING-ON-PATH] ケースの経路上の STT ノードが inject にも既定にも無く聴取失敗する（抜け）  … FAIL
  [TERMINAL-DIFF]          期待終端が正準経路の終端と相違（命名空間差や分岐選択差もあり得る）          … 情報
  [ORPHAN-CASE]            正準ケースに対応が無い（人手追加ケースかも）                                … 情報
  [UNVERIFIED]             経路自動解決不能などで確定できず（正準側 _note ★ 等）                        … 情報

注意: 強い検査は UNKNOWN-MODULE / OFF-DICT（辞書外発話=#304 問題C）と、経路が正準側で
解決できた場合の MISSING-ON-PATH（既定注入でも救えない STT 抜け=#304 問題A の確実分）。
正準 walker が経路を解決できない施設では A/B は UNVERIFIED に落ちる（OFF-DICT/UNKNOWN は常に有効）。

設計: 手書き BIVR インタプリタは作らず、gen_p7_cases の信頼できる BIVR walker
(_build_bivr_cases) で「正準ケース」を再生成し、提供 cases.json と突合する。分類は
_classify_value を再利用する。誤検知を避けるため、正準側で経路を解決できないケース
(_note に ★) は UNVERIFIED に落として A/B 判定を出さない。
"""
import argparse
import json
import sys
from pathlib import Path

# Windows cp932 化け対策（gen_p7_cases と同様）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_p7_cases as G  # noqa: E402  信頼できる BIVR walker / 分類器 spec を再利用


_LOG_OBSERVE = ("ログ観察", "")   # 終端を確定できない印（提供側がこれなら terminal 判定は UNVERIFIED）
# catch-all/sentinel 注入値: 辞書に無くて当然（NO_RESULT→catch-all を意図した注入）＝ OFF-DICT の対象外
_CATCHALL_VALUES = {"other", "default", "*", ".*", ".+", "", "NO_RESULT", "TIMEOUT", "ERROR", "false"}
# 終端名の命名空間差（人手 cases は END_ 表記・BIVR 実終端は 完了フラグ_/切断_）を吸収する接頭辞
_TERM_PREFIXES = ("END_", "完了フラグ_", "切断_", "終話_")


def _inject_keys(case):
    return set((case.get("inject") or {}).keys())


def _values(seq):
    """inject 値列から実発話値のみ（NO_RESULT/TIMEOUT/ERROR 等のリトライ sentinel を除く）。"""
    out = []
    for v in (seq if isinstance(seq, list) else [seq]):
        s = str(v)
        if s in ("NO_RESULT", "TIMEOUT", "ERROR", "false"):
            continue
        out.append(s)
    return out


def _norm_terminal(name):
    """終端名の命名空間差（END_ / 完了フラグ_ / 切断_）を剥がして比較用に正規化する。"""
    s = str(name or "")
    for p in _TERM_PREFIXES:
        if s.startswith(p):
            return s[len(p):]
    return s


def _stt_to_classifier_maps(flows, nodes, preds):
    """注入先 STT/incoming ノード名 → その下流分類器の spec maps。
    _classifier_specs の各分類器の制御入力(_controlling_input)を注入点として引く。"""
    stt2maps = {}
    for mn, maps, _labels in G._classifier_specs(flows):
        ctrl = G._controlling_input(mn, nodes, preds)
        if ctrl and maps:
            # 同一注入点に複数分類器が紐づく場合は先勝ち（通常 1:1）
            stt2maps.setdefault(ctrl, maps)
    return stt2maps


def _canon_index(canon_cases):
    """正準ケースを checkpoints[0]（"decision:label" 形式）→ [case,...] で索引。"""
    idx = {}
    for c in canon_cases:
        cps = (c.get("expect") or {}).get("checkpoints") or []
        key = cps[0] if cps else None
        if key:
            idx.setdefault(key, []).append(c)
    return idx


def _pinned_keys(case, decisions_by_node, stt2maps, ctrl2decision):
    """提供ケースが pin する (decision:label) 集合を inject から推定する。
    inject 値を分類器 spec で分類し、正準 checkpoints と同じ "decision:label" 文字列を作る。"""
    pins = set()
    for node, seq in (case.get("inject") or {}).items():
        dnode = ctrl2decision.get(node) or (node if node in decisions_by_node else None)
        if not dnode:
            continue
        vals = _values(seq)
        if not vals:
            continue
        maps = stt2maps.get(node)
        for v in vals:
            label = G._classify_value(maps, v) if maps else v
            if label and label != "NO_RESULT":
                pins.add("%s:%s" % (dnode, label))
    return pins


def main():
    ap = argparse.ArgumentParser(description="P7 連結テスト cases.json の事前妥当性チェック（#304）")
    ap.add_argument("--cases", required=True, help="検証する cases.json")
    ap.add_argument("--bivr", required=True, help="本体 BIVR（正本）")
    args = ap.parse_args()

    cases_path, bivr_path = Path(args.cases), Path(args.bivr)
    if not cases_path.exists():
        raise SystemExit(f"[ERROR] cases が見つかりません: {cases_path}")
    if not bivr_path.exists():
        raise SystemExit(f"[ERROR] BIVR が見つかりません: {bivr_path}")

    cfg = json.loads(cases_path.read_text(encoding="utf-8"))
    provided = cfg.get("cases", [])
    cfg_defaults = cfg.get("defaults", {}) or {}
    order = cfg_defaults.get("_order", []) or []

    def has_working_default(node):
        """cases defaults の _order にこのノードのキーワードが載っていれば、inject 無しでも
        stub が既定値を注入して完走できる（= 抜けても NO_RESULT にならない）。stub の def_for と同判定。"""
        return any(kw in node for kw in order)

    flows = G._read_bivr_flows(bivr_path)
    nodes, jump_starts, entry_start, _entry_short = G._bivr_index(flows)
    preds = G._build_preds(nodes, jump_starts)
    decisions = G._decisions_bivr(nodes, jump_starts)
    decisions_by_node = {d["node"]: d for d in decisions}
    stt_names = {mn for _fn, mn in G._stt_modules(flows)}
    incoming_names = {mn for mn, m in nodes.items() if G._short_type(m) == G._INCOMING_SHORT}
    valid_inject_targets = stt_names | incoming_names
    stt2maps = _stt_to_classifier_maps(flows, nodes, preds)
    # 注入点 → その注入点が制御する decision（controlling_input の逆引き）
    ctrl2decision = {}
    for d in decisions:
        ci = G._controlling_input(d["node"], nodes, preds)
        if ci:
            ctrl2decision.setdefault(ci, d["node"])
        # STT/incoming が直接 decision（自身が分岐点）の場合
        if d["kind"] in ("stt", "incoming"):
            ctrl2decision.setdefault(d["node"], d["node"])

    # 正準ケース再生成（信頼できる BIVR walker）
    _defaults_c, canon_cases, _entry = G._build_bivr_cases(flows)
    canon_idx = _canon_index(canon_cases)

    fails, infos = [], []

    def fail(code, cid, msg):
        fails.append(f"[{code}] case {cid}: {msg}")

    def info(code, cid, msg):
        infos.append(f"[{code}] case {cid}: {msg}")

    for c in provided:
        cid = c.get("id", "?")
        inj = c.get("inject") or {}

        # 1) INJECT-UNKNOWN-MODULE
        for node in inj:
            if node not in valid_inject_targets:
                fail("INJECT-UNKNOWN-MODULE", cid,
                     f"inject キー '{node}' は BIVR に STT/分類器ノードとして存在しません（typo/stale）")

        # 2) INJECT-OFF-DICT（辞書外発話 → NO_RESULT）。catch-all 値（other 等）は
        #    NO_RESULT→catch-all を意図した注入なので対象外にして誤検知を避ける。
        for node, seq in inj.items():
            maps = stt2maps.get(node)
            if not maps:
                continue
            for v in _values(seq):
                if v in _CATCHALL_VALUES:
                    continue
                if G._classify_value(maps, v) == "NO_RESULT":
                    fail("INJECT-OFF-DICT", cid,
                         f"'{node}' への注入 '{v}' は分類器 spec でどのラベルにも分類されず NO_RESULT に倒れます")

        # 3) INJECT-MISSING-ON-PATH / TERMINAL-MISMATCH（正準ケースと突合）
        pins = _pinned_keys(c, decisions_by_node, stt2maps, ctrl2decision)
        matched = []
        for key in pins:
            matched.extend(canon_idx.get(key, []))
        if not matched:
            info("ORPHAN-CASE", cid,
                 f"正準ケースに対応が見つかりません（pin={sorted(pins) or 'なし'}）。人手追加ケースなら想定内")
            continue
        # 最も具体的（inject キー集合が最大）な正準ケースを代表に
        rep = max(matched, key=lambda x: len(_inject_keys(x)))
        if str(rep.get("_note", "")).find("★") >= 0:
            info("UNVERIFIED", cid, f"正準側で経路を自動解決できず（{rep.get('_note')}）→ A/B 判定を保留")
            continue
        missing = _inject_keys(rep) - _inject_keys(c)
        # inject 抜けが「確実に聴取失敗」になるのは、STT ノード（incoming-classifier は
        # 既定=携帯があり NO_RESULT しない）かつ cases defaults に既定注入が無いノードだけ。
        # それ以外（既定で救える／incoming）は抜けても完走するので FAIL にしない。
        missing_stt = [m for m in missing
                       if m in stt_names and m not in incoming_names and not has_working_default(m)]
        if missing_stt:
            fail("INJECT-MISSING-ON-PATH", cid,
                 f"経路上の {', '.join(sorted(missing_stt))} が inject にも既定注入にも無く、"
                 f"到達時に NO_RESULT→聴取失敗に倒れます")
        # 終端は「マッチした正準ケースの分岐選択」に依存し、命名空間差（END_ vs 完了フラグ_）も
        # あるため、確定情報として FAIL にはせず参考として出す（接頭辞を剥がして実差だけ列挙）。
        exp = (c.get("expect") or {}).get("終端", "")
        canon_term = (rep.get("expect") or {}).get("終端", "")
        if exp not in _LOG_OBSERVE and canon_term not in _LOG_OBSERVE \
                and _norm_terminal(exp) != _norm_terminal(canon_term):
            info("TERMINAL-DIFF", cid,
                 f"期待終端 '{exp}' と正準経路の終端 '{canon_term}' が相違（要人手確認・"
                 f"分岐選択やマッチング差の可能性）")

    print(f"=== verify_test_cases: {cases_path.name} × {bivr_path.name} ===")
    print(f"提供ケース {len(provided)} 件 / 正準ケース {len(canon_cases)} 件")
    print(f"FAIL {len(fails)} 件  参考(UNVERIFIED/ORPHAN) {len(infos)} 件\n")
    for line in fails:
        print(line)
    if infos:
        print("\n--- 参考（FAIL ではない・人手確認用）---")
        for line in infos:
            print(line)
    if fails:
        print(f"\n!! 妥当性 NG: {len(fails)} 件の問題を検出しました。cases.json を修正してから架電してください。")
        sys.exit(1)
    print("\nOK: 事前妥当性チェックを通過しました。")


if __name__ == "__main__":
    main()
