#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_bivr.py — ビルド済みシナリオを 4 層責任モデルで採点する薄いアグリゲータ。

4 層 verifier レジストリ (ai-phone-standards/02_quality_standards/LAYER_VERIFIER_REGISTRY.md) の
内側ループ (設計時・出荷前) を実体化する採点機構。既存の層別 verifier を呼ぶだけで、
判定ロジックは一切持たない (= scorer は枠・cert 保護・HQ のみ編集の不変条件を守る)。

中心思想: 4 層は対称に採点できない。ゲートの種別は層の本質でなく verifier 成熟度 (M0→M2) の関数。
  第1 誘導(TTS文言)  M2  qa_validator                    → 自動差し戻し可
  第2 文字起こし(STT) M0  artifact からは測れない (presence のみ・品質は稼働KPI) → 人
  第3 正規化          M2  audit_openai_residual(det率) + 認定部品照合 → 自動 / OpenAI残は M0
  第4 分岐            M2  sim_connection.structural_audit → 自動差し戻し可
層を 1 つの数字に潰すと測れていない STT が隠れて Goodhart になるため、層別カードで出す。

入力はシナリオ成果物ディレクトリ (output/scenarios/{施設}_{flow}/) を既定とする。
  - 設計書 YAML  → 第1 (qa_validator) / 第3 前半 (det率) は YAML が要る (.bivr 非対応)
  - .bivr        → 第4 (構造監査) / 第3 後半 (部品認定) は .bivr から取れる

使い方:
  python3 tools/score_bivr.py --scenario-dir output/scenarios/亀田総合病院_相談室/
  python3 tools/score_bivr.py --yaml <設計書.yaml> --bivr <flow.bivr> [--entry <短名>]
  オプション: --json-report <out.json>  --md-report <out.md>
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import asdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
for _d in ("scripts", "connection_test", "schemas"):
    p = str(REPO / _d)
    if p not in sys.path:
        sys.path.insert(0, p)

import yaml  # noqa: E402  (パイプライン既存依存)

# ── scorecard を既に持つ認定部品 (被覆スコアカード PJ の成果物) ──────────────
# parts_catalog.json には現状 has_scorecard 列が無いので暫定でここに持つ。
# 北極星「カタログ掲載⟹成績表あり」が機械化されたら generate_parts_catalog.py の列へ移す。
PARTS_WITH_SCORECARD = {
    "yes_no_classifier",
    "reservation_date_classifier",
    "current_appointment_date",
}
DATE_PART_FAMILY = {"reservation_date_classifier", "current_appointment_date"}


# ── 第1 誘導 (TTS 文言) ─ M2 ─ qa_validator ────────────────────────────────
def score_layer1_tts(yaml_path: Path) -> dict:
    """設計書 YAML を qa_validator に通し、TTS 文言・配置の決定論チェックを層1スコアにする。
    無言ノード/着信冒頭欠落/TTS 偽プレースホルダ混入 (E-15 等) が CRITICAL。
    """
    blind = ["音声品質 (声質・抑揚) は測れない＝第1の『音』は M0 (proxy 無し)・別途 KPI",
             "qa_validator のルール網羅範囲外の文言品質は不可視"]
    if yaml_path is None or not yaml_path.exists():
        return {"layer": 1, "component": "誘導(TTS文言)", "gate": "M2", "lane": "C/D",
                "status": "SKIP", "reason": "設計書 YAML 不在", "blind_spots": blind}
    with tempfile.NamedTemporaryFile("r", suffix=".json", delete=False, encoding="utf-8") as tf:
        rep_path = tf.name
    try:
        subprocess.run([sys.executable, str(REPO / "schemas" / "qa_validator.py"),
                        str(yaml_path), "--json-report", rep_path],
                       cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
        rep = json.loads(Path(rep_path).read_text(encoding="utf-8"))
    finally:
        try:
            Path(rep_path).unlink()
        except OSError:
            pass
    c = rep.get("counts", {})
    crit = [i for i in rep.get("issues", []) if i.get("severity") == "CRITICAL"]
    return {
        "layer": 1, "component": "誘導(TTS文言)", "gate": "M2", "lane": "C/D",
        "status": "PASS" if c.get("critical", 0) == 0 else "FAIL",
        "critical": c.get("critical", 0), "warning": c.get("warning", 0),
        "auto_fixable": c.get("auto_fixable", 0),
        "critical_codes": [f"{i.get('code')}: {i.get('message')}" for i in crit][:20],
        "blind_spots": blind,
    }


# ── 第2 文字起こし (STT 辞書) ─ M0 ─ artifact からは品質測定不能 ────────────
def score_layer2_stt(spec: dict) -> dict:
    """STT 辞書は artifact から品質を採点できない (M0)。
    静的に言えるのは『各 hearing が辞書テンプレを参照しているか』の presence のみ。
    品質 (一発取得率・誤認識) は稼働ログ KPI / 音声注入レーンの管轄 (no silent cap で明示)。
    """
    # 辞書はトップレベル amivoice_dictionary セクション、STT 種別は hearing_items の stt_type に載る。
    has_dict_section = bool(spec.get("amivoice_dictionary"))
    hearings = sum(1 for b in (spec.get("scenario_flow", []) or [])
                   if isinstance(b, dict) and b.get("type") == "hearing")
    with_stt = sum(1 for s in ((spec.get("hearing_items", []) or []) +
                               (spec.get("step_details", []) or []))
                   if isinstance(s, dict) and s.get("stt_type"))
    return {
        "layer": 2, "component": "文字起こし(STT辞書)", "gate": "M0", "lane": "人(KPI-signal)",
        "status": "UNMEASURED",
        "presence": {"hearing_blocks": hearings, "with_stt_type": with_stt,
                     "has_dictionary_section": has_dict_section},
        "note": "STT 品質は artifact から測れない (M0)。これは presence チェックのみ。"
                "品質は稼働ログ KPI (一発取得率) / 音声注入レーン (Twilio+WAV・整備中) の管轄。",
        "blind_spots": ["誤認識率・一発取得率・低信頼/NO_RESULT 計数は本採点の対象外＝稼働KPIを見よ",
                        "辞書の語彙被覆の十分性は静的には判定不能"],
    }


# ── 第3 正規化 (Script / entity) ─ M2(決定論)/M0(OpenAI残) ──────────────────
def _part_id_from_detail(backend: str, detail: str) -> str | None:
    """audit_openai_residual の (backend, detail) から認定部品 ID を最善努力で取り出す。"""
    if backend != "deterministic":
        return None
    if detail == "date":
        return "reservation_date_classifier"  # date family の代表
    tok = detail.split(":", 1)[0]
    if tok.endswith("-block"):
        tok = tok[:-len("-block")]
    return tok or None


def score_layer3_normalization(spec: dict, catalog: dict) -> dict:
    """audit_openai_residual で det 率を出し、決定論点を認定部品 (parts_catalog) に照合する。
    各 det 点: certified か / scorecard を持つか (北極星フラグ)。OpenAI 残は M0 フラグ。
    """
    from scaffold_generator import audit_openai_residual  # type: ignore
    blind = [".bivr の実 script ハッシュ照合 (engine/spec) は oracle_gate/p6_gate の管轄＝本採点は設計レベルの det 解決のみ",
             "scorecard 存在は暫定ハードコード (PARTS_WITH_SCORECARD)・カタログ列化が北極星",
             "subflow 内部の判定点は本監査では opaque (別フロー)"]
    if not spec:
        return {"layer": 3, "component": "正規化(Script/entity)", "gate": "M2/M0",
                "lane": "A", "status": "SKIP", "reason": "設計書 YAML 不在", "blind_spots": blind}
    rep = audit_openai_residual(spec)
    cat_status = {p["part_id"]: p.get("status") for p in catalog.get("parts", [])}
    det_points, openai_points, block_none, block_known = [], [], [], []
    for r in rep.get("rows", []):
        be = r.get("backend")
        if be == "deterministic":
            pid = _part_id_from_detail(be, r.get("detail", ""))
            det_points.append({
                "step": r.get("step"), "part": pid,
                "catalog_status": cat_status.get(pid) if pid else None,
                "certified": cat_status.get(pid) == "certified" if pid else None,
                "has_scorecard": (pid in PARTS_WITH_SCORECARD) if pid else False,
                "detail": r.get("detail"),
            })
        elif be == "openai":
            openai_points.append({"step": r.get("step"), "detail": r.get("detail")})
        elif be == "block":
            (block_none if str(r.get("detail", "")).startswith("none") or r.get("detail") == "none"
             else block_known).append({"step": r.get("step"), "detail": r.get("detail")})
    n_det = len(det_points)
    n_sc = sum(1 for d in det_points if d["has_scorecard"])
    n_cert = sum(1 for d in det_points if d["certified"])
    return {
        "layer": 3, "component": "正規化(Script/entity)", "gate": "M2/M0", "lane": "A",
        "status": "INFO",  # det 率は KPI であり hard pass/fail ではない (flip 基準でも block(none) は別枠)
        "det_rate": round(rep.get("rate", 0.0), 4),
        "counts": rep.get("counts", {}),
        "deterministic_points": n_det,
        "certified_points": n_cert,
        "with_scorecard_points": n_sc,
        "openai_residual": openai_points,            # M0・人ゲート
        "block_none": block_none,                    # 未解決の判定点 (要設計)
        "block_known": block_known,                  # 部品はあるが未 surface
        "det_detail": det_points,
        "blind_spots": blind,
    }


# ── 第4 分岐 (CMR / script) ─ M2 ─ sim_connection 構造監査 ──────────────────
def _base(name: str) -> str:
    """末尾の日付サフィックス (_YYYYMMDD / _YYMMDD) を落とした基底名。
    jump 参照名 (サフィックス無し) と フロー名 (サフィックス有り) の不一致を吸収する。
    """
    import re
    return re.sub(r"_\d{6,8}$", "", name)


def _detect_main(flows: dict) -> str | None:
    """jump ターゲットにならないフロー (= ルート) を main とみなす。一意なら採用。
    日付サフィックス不一致 (混成在庫アーティファクト) を吸収するため基底名で照合する。
    """
    from sim_connection import short  # type: ignore
    targets = set()
    for d in flows.values():
        for m in (d.get("modules", {}) or {}).values():
            if "Jump to Flow" in (m.get("type", "") or ""):
                raw = (m.get("params", {}) or {}).get("flowname", "")
                full = raw.split("^", 1)[-1] if "^" in raw else raw
                targets.add(_base(short(full)))
    roots = [full for full in flows if _base(short(full)) not in targets]
    return roots[0] if len(roots) == 1 else None


def _main_only_opaque(flows: dict, main_full: str) -> dict:
    """main フローだけを残し、Jump to Flow を不透明化した 1 フロー dict を返す。
    サブフローは評価対象から外す (内部構造の健全性は見ない)。jump はその場の制御移譲として:
      - 継続(next)あり → パススルー (__SUBFLOW_OPAQUE__・next=継続) ＝ gosub 戻りを近似
      - 継続なし(末尾jump) → 終端 (Disconnect 相当) ＝ サブフロー側で終話
    これで suffix 不一致由来の broken jump / subflow 未到達ノイズが出ず、main の分岐健全性のみ採る。
    """
    main = flows[main_full]
    mods = {}
    for mn, m in (main.get("modules", {}) or {}).items():
        if "Jump to Flow" in (m.get("type", "") or ""):
            nx = [n for n in (m.get("next", []) or []) if n.get("nextModuleName")]
            if nx:
                mods[mn] = {"type": "__SUBFLOW_OPAQUE__", "params": {}, "next": nx, "subs": []}
            else:
                mods[mn] = {"type": "Disconnect(opaque subflow)", "params": {}, "next": [], "subs": []}
        else:
            mods[mn] = m
    return {main_full: {"name": main["name"], "start": main.get("start"), "modules": mods}}


def _audit_once(audit_flows: dict, main_full: str):
    """structural_audit を1回走らせ、(res, 未解決jump, 循環jump, 構造CRITICAL) を返す。
    未解決/循環 jump (梱包不整合) は本物の構造欠陥と分けて取り出す。"""
    from sim_connection import structural_audit  # type: ignore
    res, flat = structural_audit(audit_flows, main_full)
    fm = flat.get("modules", {})
    reached = res.reached_modules
    unresolved = sorted({fm[n]["params"].get("_ref", "?") for n in fm
                         if fm[n].get("type") == "__BROKEN_JUMP__" and n in reached})
    cyclic = sorted({fm[n]["params"].get("_ref", "?") for n in fm
                     if fm[n].get("type") == "__CYCLIC_JUMP__" and n in reached})
    struct = [i for i in res.issues
              if not (i.code == "R-2" and i.message.startswith(("jump 先未解決", "循環 jump")))]
    struct_crit = [i for i in struct if i.severity == "CRITICAL"]
    return res, unresolved, cyclic, struct, struct_crit


def score_layer4_branching(bivr_path: Path, entry: str | None,
                           opaque_subflows: bool = False) -> dict:
    """.bivr を採点する。共通仕様は『サブフローは評価しない』。盲点を消すため、まず
    全展開フラット化を試み、整合が取れれば本採点する (R-1/R-2/R-3/AUD-1/AUD-2)。

    展開で整合が取れない (未解決/循環 jump) ときは **ハード halt しない**。テスト採点 (暫定) に
    留め WARNING を出す = PROVISIONAL。盲点 (サブフロー内部+戻り経路) を明示し、main フローのみの
    構造読みを暫定値として供給する。状態:
      - PASS … 展開成功・本物の構造欠陥なし
      - FAIL … 展開成功・本物の構造欠陥あり (死に枝/参照先不在/catch-all欠落) → 出荷ブロック
      - PROVISIONAL … 展開で整合取れず → WARNING・暫定・ブロックしない (盲点が残る)
    --opaque-subflows で最初から main のみ評価する診断モード。
    """
    from sim_connection import load_bivr, short  # type: ignore
    blind_full = ["フラット化は全サブフローが同一バンドルに揃い名前解決できること前提",
                  "実 JS (Nashorn) パリティは要 JS エンジン (当 PC 不可)＝本監査は Python シム計算",
                  "OpenAI/Entity 等の RECORDED 出力は検証対象外 (記録サイドカー方式)"]
    blind_provisional = ["サブフロー内部と戻り経路は未評価 (展開で整合が取れず＝盲点が残る・暫定採点)",
                         "main フローのみの構造読みを暫定値として供給"]
    if bivr_path is None or not bivr_path.exists():
        return {"layer": 4, "component": "分岐(CMR/script)", "gate": "M2", "lane": "B/D",
                "status": "SKIP", "reason": ".bivr 不在", "blind_spots": blind_full}
    flows = load_bivr(str(bivr_path))
    main_full = None
    if entry:
        for full in flows:
            if short(full) == entry or entry in short(full):
                main_full = full
                break
    if not main_full:
        main_full = _detect_main(flows)
    n_jumps = (sum(1 for m in (flows[main_full].get("modules", {}) or {}).values()
                   if "Jump to Flow" in (m.get("type", "") or "")) if main_full else 0)
    base = {"layer": 4, "component": "分岐(CMR/script)", "gate": "M2",
            "entry": short(main_full) if main_full else None, "subflow_jumps": n_jumps}
    if not main_full:
        # entry 未特定 (orphan 重複/混成在庫) も整合不全＝暫定 WARNING。ハード halt しない。
        return {**base, "lane": "B/D", "status": "PROVISIONAL", "severity": "WARNING",
                "reason": f"entry フロー未特定 (orphan 重複/混成在庫の疑い)。候補={[short(f) for f in flows]}",
                "unresolved_subflows": [], "cyclic_subflows": [], "blind_spots": blind_provisional}

    # ── 診断モード: 最初から main のみ (サブフロー不透明) ──
    if opaque_subflows:
        res, _u, _c, _st, scrit = _audit_once(_main_only_opaque(flows, main_full), main_full)
        return {**base, "lane": "B/D", "status": "FAIL" if scrit else "PASS",
                "subflows_evaluated": False, "coverage_pct": round(res.coverage, 1),
                "critical": len(scrit), "warning": len([i for i in res.issues if i.severity == "WARNING"]),
                "issues": [{"severity": i.severity, "code": i.code, "message": i.message} for i in res.issues][:40],
                "blind_spots": ["サブフロー内部は評価しない (jump 不透明・診断モード)"] + blind_full[1:]}

    # ── 既定: まず全展開フラット化を試みる ──
    res, unresolved, cyclic, _st, scrit = _audit_once(flows, main_full)
    if unresolved or cyclic:
        # 展開で整合取れず → テスト採点(暫定)+WARNING。main のみで暫定構造読みを供給。
        res2, _u2, _c2, _st2, scrit2 = _audit_once(_main_only_opaque(flows, main_full), main_full)
        return {**base, "lane": "B/D", "status": "PROVISIONAL", "severity": "WARNING",
                "subflows_evaluated": False,
                "reason": "サブフロー展開で整合が取れず (未解決/循環 jump)→ テスト採点(暫定)・WARNING (halt しない)",
                "unresolved_subflows": unresolved, "cyclic_subflows": cyclic,
                "coverage_pct": round(res2.coverage, 1),
                "main_only_critical": len(scrit2),
                "issues": [{"severity": i.severity, "code": i.code, "message": i.message} for i in res2.issues][:40],
                "blind_spots": blind_provisional}
    # 展開成功 → 本採点
    return {**base, "lane": "B/D", "status": "FAIL" if scrit else "PASS",
            "subflows_evaluated": True, "coverage_pct": round(res.coverage, 1),
            "unresolved_subflows": [], "cyclic_subflows": [],
            "critical": len(scrit), "warning": len([i for i in res.issues if i.severity == "WARNING"]),
            "issues": [{"severity": i.severity, "code": i.code, "message": i.message} for i in res.issues][:40],
            "blind_spots": blind_full}


# ── 成果物ディレクトリの解決 ────────────────────────────────────────────────
def _find_inputs(scenario_dir: Path) -> tuple[Path | None, Path | None]:
    yamls = sorted(scenario_dir.glob("設計書_*.yaml")) or sorted(scenario_dir.glob("*.yaml"))
    yaml_path = None
    for y in yamls:
        try:
            d = yaml.safe_load(y.read_text(encoding="utf-8"))
            if isinstance(d, dict) and d.get("scenario_flow"):
                yaml_path = y
                break
        except Exception:
            continue
    bivrs = sorted(scenario_dir.glob("*.bivr"))
    return yaml_path, (bivrs[0] if bivrs else None)


def _render_md(report: dict) -> str:
    L = report["layers"]
    _l4 = next((x for x in L if x["layer"] == 4), {})
    sub = "全展開 (フラット採点)" if _l4.get("subflows_evaluated") else "未評価 (展開で整合取れず＝暫定)"
    out = [f"# シナリオ採点カード — {report['target']}", "",
           "> 4 層責任モデルの内側ループ採点。**層を 1 点に潰さない**＝STT(M0) は品質未測定。",
           f"> サブフロー: **{sub}**。", ""]
    if report.get("provisional"):
        out += ["> ⚠ **暫定 (テスト採点)**: サブフローを main へ展開しきれず (整合不全)、"
                "main フローのみの構造読みです。出荷判定は保留＝WARNING。", ""]
    out.append("| 層 | コンポーネント | ゲート | 状態 | 主指標 |")
    out.append("|---|---|---|---|---|")
    rows = {x["layer"]: x for x in L}
    out.append(f"| 1 | 誘導(TTS文言) | M2 | {rows[1]['status']} | "
               f"CRITICAL {rows[1].get('critical','-')} / WARN {rows[1].get('warning','-')} |")
    p = rows[2].get("presence", {})
    out.append(f"| 2 | 文字起こし(STT辞書) | M0 | {rows[2]['status']} | "
               f"stt付与 {p.get('with_stt_type','-')}/{p.get('hearing_blocks','-')} / "
               f"辞書節 {'有' if p.get('has_dictionary_section') else '無'} (品質は稼働KPI) |")
    out.append(f"| 3 | 正規化(Script/entity) | M2/M0 | {rows[3]['status']} | "
               f"det率 {rows[3].get('det_rate','-')} / 認定 {rows[3].get('certified_points','-')} / "
               f"成績表有 {rows[3].get('with_scorecard_points','-')} / OpenAI残 {len(rows[3].get('openai_residual',[]))} |")
    _unres = rows[4].get("unresolved_subflows") or []
    _l4extra = (f"未解決subflow {len(_unres)}件: {', '.join(_unres[:3])}"
                if _unres else f"subflow jump {rows[4].get('subflow_jumps','-')}(展開済)")
    _l4crit = rows[4].get("critical", rows[4].get("main_only_critical", "-"))
    _l4cov = rows[4].get("coverage_pct", "-")
    _l4cov = f"{_l4cov}{'(main暫定)' if rows[4].get('status') == 'PROVISIONAL' else ''}"
    out.append(f"| 4 | 分岐(CMR/script) | M2 | {rows[4]['status']} | "
               f"coverage {_l4cov}% / CRITICAL {_l4crit} / {_l4extra} |")
    out += ["", f"**出荷ゲート (M2 層のみ判定)**: {report['ship_gate']}",
            "  ※ 第3 det率は KPI、第2 STT は M0 のため出荷ゲートには含めない (Goodhart 回避)。", ""]
    for x in L:
        out.append(f"## 第{x['layer']} {x['component']} — {x['status']}")
        if x.get("status") == "PROVISIONAL":
            for r in x.get("unresolved_subflows", []):
                out.append(f"- 整合不全(未解決jump): {r} ← このサブフローがバンドルに無い/名前不一致")
            for r in x.get("cyclic_subflows", []):
                out.append(f"- 整合不全(循環jump): {r}")
            if x.get("reason"):
                out.append(f"- {x['reason']}")
        for bs in x.get("blind_spots", []):
            out.append(f"- 盲点: {bs}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description="ビルド済みシナリオを 4 層で採点する薄いアグリゲータ")
    ap.add_argument("--scenario-dir", help="output/scenarios/{施設}_{flow}/ (YAML+.bivr 自動探索)")
    ap.add_argument("--yaml", help="設計書 YAML を明示")
    ap.add_argument("--bivr", help=".bivr を明示")
    ap.add_argument("--entry", help="第4 監査の entry フロー短名 (自動検出失敗時)")
    ap.add_argument("--opaque-subflows", action="store_true",
                    help="サブフローを不透明化し main フローのみ監査する診断モード "
                         "(既定は全展開フラット化＝盲点を残さない)")
    ap.add_argument("--json-report", help="JSON レポート出力先")
    ap.add_argument("--md-report", help="Markdown レポート出力先")
    args = ap.parse_args()

    yaml_path = Path(args.yaml) if args.yaml else None
    bivr_path = Path(args.bivr) if args.bivr else None
    target = args.scenario_dir or args.yaml or args.bivr or "?"
    if args.scenario_dir:
        sd = Path(args.scenario_dir)
        y, b = _find_inputs(sd)
        yaml_path = yaml_path or y
        bivr_path = bivr_path or b

    spec = {}
    if yaml_path and yaml_path.exists():
        spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    catalog = {}
    cat_path = REPO / "modules" / "parts_catalog.json"
    if cat_path.exists():
        catalog = json.loads(cat_path.read_text(encoding="utf-8"))

    layers = [
        score_layer1_tts(yaml_path),
        score_layer2_stt(spec),
        score_layer3_normalization(spec, catalog),
        score_layer4_branching(bivr_path, args.entry, opaque_subflows=args.opaque_subflows),
    ]
    # 出荷ゲートは M2 層 (第1 文言・第4 分岐) のみで判定。
    # PROVISIONAL (サブフロー展開で整合取れず) は halt せず WARNING＝暫定(テスト採点)扱い。
    l1 = next(x for x in layers if x["layer"] == 1)
    l4 = next(x for x in layers if x["layer"] == 4)
    provisional = (l4["status"] == "PROVISIONAL")
    if (l1["status"] == "FAIL") or (l4["status"] == "FAIL"):
        ship = "BLOCK (M2 層に本物の欠陥: 文言 CRITICAL or 分岐構造欠陥)"
    elif (l1["status"] == "SKIP") or (l4["status"] == "SKIP"):
        ship = "INCOMPLETE (M2 層に SKIP)"
    elif provisional:
        ship = "PASS_WITH_WARNINGS (暫定: サブフロー展開で整合取れず＝テスト採点・要梱包是正)"
    else:
        ship = "PASS"
    m2_fail = ship.startswith("BLOCK")

    report = {
        "target": str(target),
        "inputs": {"yaml": str(yaml_path) if yaml_path else None,
                   "bivr": str(bivr_path) if bivr_path else None},
        "ship_gate": ship,
        "provisional": provisional,
        "layers": layers,
    }
    if args.json_report:
        Path(args.json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
    md = _render_md(report)
    if args.md_report:
        Path(args.md_report).write_text(md, encoding="utf-8")
    print(md)
    return 1 if m2_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
