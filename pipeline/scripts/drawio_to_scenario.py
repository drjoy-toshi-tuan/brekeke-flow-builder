# -*- coding: utf-8 -*-
"""drawio_to_scenario.py — enriched/不完全 drawio → scenario_flow 寛容パーサ + surfacing。

VFB 工場 v2（director 廃止）の入口コンポーネント。CS が scenario-composer / 手編集で
作った業務 drawio を取り込み、(1) 寛容に scenario_flow を復元し、(2) 分岐ブロックの
ラベル集合を認定部品の output_labels（part.json）と決定論照合して **surfacing**
（未配線 / 未知 / 該当部品なし を CRITICAL 列挙）し、(3) 病院セーフティ lint をかける。

設計: project-governance/initiatives/vfb-factory-restructure.md §2-1（2026-06-22 設計確定）。
  - drawio はビジネス view（ロッシー前提）／工場が実現知識の SSoT。
  - **ラベルがセレクタ**: 分岐ブロックの conditions[].match 集合 ⇔ part.json output_labels。
    一致＝部品選定成立 / 部品が出すのに未配線＝CRITICAL / 該当部品なし＝CRITICAL。
  - 完全性判定は寛容パーサでなく surfacing が持つ（クリーンでない入口で多数 CRITICAL になる想定）。

stdlib のみ（PyYAML 不要・インストール禁止方針）。
使い方:
  python drawio_to_scenario.py <設計.drawio> [--json] [--modules <dir>]
"""
import sys
import os
import json
import xml.etree.ElementTree as ET

CATCHALL = {"other", "default", "*", "その他問合せ"}  # 用途別の受け皿ラベル → NO_RESULT 相当に正規化
# 注: 「その他問合せ」は用件メニューの“その他に流す”枝。分類部品の no-match(NO_RESULT)とは別概念だが
#     部品ラベル照合では受け皿扱いにする（部品の核ラベルに数えない）。「その他」(checkup_intent の実カテゴリ)
#     とは別文字列なので衝突しない。

# slot_type（catalog feature.id）→ 想定する認定部品（正規化選定の素・1-4 で拡張）
SLOT_PART_MAP = {
    "生年月日": "dob_normalizer",   # modules/ の実体は dob_normalizer（旧 dob_reconfirmation はディレクトリ非存在）
    "電話番号": "phone_type",
    "診療科": "department_classifier",
    "希望日": "reservation_date_classifier",
}


# ───────────────────────── 1. drawio パース ─────────────────────────
def _hardened_parser():
    """XXE / billion-laughs ガード（defusedxml は pip 禁止のため stdlib expat を硬化）。
    DTD / カスタムエンティティ宣言 / 外部エンティティ参照を拒否する。drawio は定義済み
    エンティティ（&quot; 等）と数値文字参照しか使わないので非破壊。"""
    parser = ET.XMLParser()

    def _forbid(*_a, **_k):
        raise ValueError("XML DTD/エンティティ宣言は許可されていません（XXE/billion-laughs ガード）")

    expat = getattr(parser, "parser", None)
    if expat is not None:
        try:
            expat.StartDoctypeDeclHandler = _forbid
            expat.EntityDeclHandler = _forbid
            expat.UnparsedEntityDeclHandler = _forbid
            expat.ExternalEntityRefHandler = _forbid
        except AttributeError:
            pass
    return parser


def _flow_diagram(mxfile):
    """フロー図 diagram を返す（id に 'flow' を含むもの優先、無ければ先頭）。"""
    diagrams = mxfile.findall("diagram")
    for d in diagrams:
        if "flow" in (d.get("id") or "").lower():
            return d
    return diagrams[0] if diagrams else None


def parse_drawio(path):
    """drawio → (nodes, edges)。
    nodes: [{id, step, display_type, announce, repeat, slot_type, output_format,
             save_to, reference_module, conditions:[{match,next}]}]
    edges: [{source, target, label}]
    """
    tree = ET.parse(path, parser=_hardened_parser())
    mxfile = tree.getroot()
    diagram = _flow_diagram(mxfile)
    if diagram is None:
        raise ValueError(f"diagram が見つからない: {path}")
    model = diagram.find("mxGraphModel")
    root = model.find("root") if model is not None else None
    if root is None:
        raise ValueError(f"mxGraphModel/root が見つからない: {path}")

    nodes, edges = [], []
    for el in list(root):
        if el.tag == "object":
            cond = []
            cj = el.get("conditions_json")
            if cj:
                try:
                    cond = json.loads(cj)
                except (ValueError, TypeError):
                    cond = []
            nodes.append({
                "id": el.get("id", ""),
                "step": el.get("label", ""),
                "display_type": el.get("type", ""),
                "announce": el.get("announce", ""),
                "repeat": el.get("repeat", "無し"),
                "slot_type": el.get("slot_type", ""),
                "output_format": el.get("output_format", ""),
                "save_to": el.get("save_to", ""),
                "reference_module": el.get("reference_module", ""),
                "conditions": cond,
            })
        elif el.tag == "mxCell" and el.get("edge") == "1":
            edges.append({
                "source": el.get("source", ""),
                "target": el.get("target", ""),
                "label": el.get("value", ""),
                "style": el.get("style", ""),
            })
    return nodes, edges


FAILURE_EDGE_COLOR = "E53935"  # drawio_style.FAILURE_EDGE_COLOR（聴取失敗＝赤・破線）


def _is_failure_edge(e):
    """聴取失敗（リトライ上限到達）の遷移エッジか。業務分岐ではない。"""
    style = e.get("style", "")
    return (e.get("label", "").strip() == "聴取失敗"
            or ("dashed=1" in style and FAILURE_EDGE_COLOR in style))


# ───────────────────────── 2. scenario_flow 復元（寛容） ─────────────────────────
def build_scenario_flow(nodes, edges):
    """nodes/edges → scenario_flow ブロック列（best-effort）。
    enriched 属性が無くても落ちない。type は表示種別＋属性からの best-effort 推定。
    """
    id2step = {n["id"]: n["step"] for n in nodes}
    out_edges = {}
    for e in edges:
        out_edges.setdefault(e["source"], []).append(e)

    blocks = []
    for n in nodes:
        b = {"step": n["step"]}
        # type 推定（9 種への best-effort。確定は 1-4/scaffold へ委譲）
        if n["display_type"] == "end":
            b["type"] = "termination"
        elif n["reference_module"]:
            b["type"] = "context_match_router"
        elif n["conditions"]:
            b["type"] = "context_match_router"
        elif n["output_format"]:
            b["type"] = "hearing"
        else:
            b["type"] = "announcement"
        for k in ("slot_type", "output_format", "save_to", "reference_module"):
            if n[k]:
                b[k] = n[k]
        # 失敗エッジ（聴取失敗）は業務分岐から分離して retry_failure として記録
        es = out_edges.get(n["id"], [])
        flow_es = [e for e in es if not _is_failure_edge(e)]
        if any(_is_failure_edge(e) for e in es):
            b["retry_failure"] = "end_failure"
        if n["conditions"]:
            b["conditions"] = n["conditions"]
        else:
            # 単一の後続エッジを next として復元（失敗エッジは除外済み）
            nxts = [id2step.get(e["target"], "") for e in flow_es if e["target"]]
            nxts = [x for x in nxts if x]
            if len(nxts) == 1:
                b["next"] = nxts[0]
            elif len(nxts) > 1:
                # 条件無しで多分岐エッジ＝drawio 側に隠れ分岐（surfacing 対象）
                b["_unlabeled_targets"] = nxts
        blocks.append(b)
    return blocks


# ───────────────────────── 3. 認定部品の branch surface ロード ─────────────────────────
def load_part_surfaces(modules_dir):
    """modules/*/part.json から output_labels を読み、surface 一覧を返す。
    surface: {part_id, spec, scope, labels:set}
    - top-level output_labels（固定ラベル部品）→ spec=None
    - specs.<name>.output_labels（per-spec）: list か {scope:[...]} を展開
    """
    surfaces = []
    if not os.path.isdir(modules_dir):
        return surfaces
    for name in sorted(os.listdir(modules_dir)):
        pj = os.path.join(modules_dir, name, "part.json")
        if not os.path.isfile(pj):
            continue
        try:
            with open(pj, encoding="utf-8") as f:
                data = json.load(f)
        except (ValueError, OSError):
            continue
        pid = data.get("part_id", name)
        # part 側ラベルも drawn 側と同じ正規化（CATCHALL 受け皿→NO_RESULT）を掛ける。
        # 非対称（drawn だけ正規化）だと、その他問合せ 等の受け皿を出力する部品が
        # 常に UNWIRED_LABEL 扱いになるため（_norm_label と対称化）。
        def _nl(labels):
            return {_norm_label(l) for l in labels}
        if isinstance(data.get("output_labels"), list):
            surfaces.append({"part_id": pid, "spec": None, "scope": None,
                             "labels": _nl(data["output_labels"])})
        for spec_name, spec in (data.get("specs") or {}).items():
            ol = spec.get("output_labels") if isinstance(spec, dict) else None
            if isinstance(ol, list):
                surfaces.append({"part_id": pid, "spec": spec_name, "scope": None,
                                 "labels": _nl(ol)})
            elif isinstance(ol, dict):
                for scope, labels in ol.items():
                    surfaces.append({"part_id": pid, "spec": spec_name, "scope": scope,
                                     "labels": _nl(labels)})
    return surfaces


# ───────────────────────── 4. 部品選定 + surfacing ─────────────────────────
def _norm_label(lbl):
    return "NO_RESULT" if lbl in CATCHALL else lbl


def _surface_name(s):
    parts = [s["part_id"]]
    if s["spec"]:
        parts.append(s["spec"])
    if s["scope"]:
        parts.append(s["scope"])
    return ":".join(parts)


def best_surface(drawn_core, surfaces):
    """drawn ラベル core 集合（NO_RESULT 除外済）に最もマッチする surface を返す（無ければ None）。
    閾値: drawn 側 or part 側の 50% 被覆。overlap 最大を採る。surface_branches と scaffold の
    決定論部品選定が同一ロジックを共有するための SSoT（surfacing の核）。"""
    best, best_ov = None, 0
    for s in surfaces:
        part_core = s["labels"] - {"NO_RESULT"}
        ov = len(drawn_core & part_core)
        if ov == 0:
            continue
        cover_drawn = ov / len(drawn_core) if drawn_core else 0
        cover_part = ov / len(part_core) if part_core else 0
        if (cover_drawn >= 0.5 or cover_part >= 0.5) and ov > best_ov:
            best, best_ov = s, ov
    return best


def surface_branches(blocks, surfaces, present_parts):
    """各分岐ブロックを output_labels と照合 → findings。
    finding: {severity, code, step, message}
    """
    findings = []
    for b in blocks:
        conds = b.get("conditions")
        if not conds:
            if b.get("_unlabeled_targets"):
                findings.append({
                    "severity": "CRITICAL", "code": "UNLABELED_BRANCH", "step": b["step"],
                    "message": "条件ラベルの無い多分岐エッジ（隠れ分岐）。各遷移の match を drawio に記載してください。",
                })
            continue

        drawn = [c.get("match", "") for c in conds]
        drawn_norm = {_norm_label(x) for x in drawn if x}
        drawn_core = drawn_norm - {"NO_RESULT"}

        # 最良 surface を core overlap で選ぶ（閾値: drawn or part の 50% 被覆）
        best = best_surface(drawn_core, surfaces)

        if best is None:
            findings.append({
                "severity": "CRITICAL", "code": "NO_CERTIFIED_PART", "step": b["step"],
                "message": "この分岐のラベル集合 {%s} に一致する認定部品（output_labels）が見つかりません。"
                           "壁打ちで部品/spec を確定するか、新規 spec を人ゲートに上げてください。"
                           % "、".join(sorted(drawn_core)),
            })
            continue

        missing = best["labels"] - drawn_norm
        extra = drawn_norm - best["labels"]
        sel = _surface_name(best)
        if missing:
            findings.append({
                "severity": "CRITICAL", "code": "UNWIRED_LABEL", "step": b["step"],
                "message": "部品 %s は {%s} を出力しますが、未配線のラベルがあります: {%s}。遷移先を drawio に記載してください。"
                           % (sel, "、".join(sorted(best["labels"])), "、".join(sorted(missing))),
            })
        if extra:
            findings.append({
                "severity": "WARN", "code": "UNKNOWN_LABEL", "step": b["step"],
                "message": "部品 %s が出力しないラベルが配線されています: {%s}（業務ラベル↔部品カテゴリのマッピング要確認）。"
                           % (sel, "、".join(sorted(extra))),
            })
        if not missing and not extra:
            note = "" if best["part_id"] in present_parts else "（注: 本ブランチに部品ディレクトリ未存在）"
            findings.append({
                "severity": "OK", "code": "PART_SELECTED", "step": b["step"],
                "message": "部品選定: %s%s" % (sel, note),
            })
    return findings


def surface_slots(blocks, present_parts):
    """slot_type ブロックの正規化選定（slot_type → 部品）。本ブランチでの部品存否を注記。"""
    findings = []
    for b in blocks:
        st = b.get("slot_type")
        if not st:
            continue
        part = SLOT_PART_MAP.get(st)
        if part is None:
            findings.append({"severity": "OK", "code": "SLOT_INLINE", "step": b["step"],
                             "message": "slot_type=%s → インライン聴取（標準構成）" % st})
        elif part in present_parts:
            findings.append({"severity": "OK", "code": "SLOT_PART", "step": b["step"],
                             "message": "slot_type=%s → 部品 %s" % (st, part)})
        else:
            findings.append({"severity": "WARN", "code": "SLOT_PART_ABSENT", "step": b["step"],
                             "message": "slot_type=%s → 部品 %s が本ブランチに未存在（別ブランチで認定済の可能性）" % (st, part)})
    return findings


# ───────────────────────── 5. 病院セーフティ lint ─────────────────────────
def safety_lint(nodes):
    """可視 label（step 名）に Brekeke 技術データ（save_to / reference_module 値）が
    漏れていないかを機械チェック。漏れ＝CRITICAL。"""
    findings = []
    secret_tokens = set()
    for n in nodes:
        if n["save_to"]:
            secret_tokens.add(n["save_to"])
        if n["reference_module"]:
            secret_tokens.add(n["reference_module"])
    for n in nodes:
        label = n["step"]
        for tok in secret_tokens:
            # reference_module は step 名を指すこともある（CMR）ので、label==tok は許容し substring 漏れのみ検出
            if tok and tok != label and tok in label:
                findings.append({
                    "severity": "CRITICAL", "code": "LABEL_LEAK", "step": label,
                    "message": "可視ラベルに Brekeke 内部トークン '%s' が漏れています。" % tok,
                })
    return findings


# ───────────────────────── レポート / CLI ─────────────────────────
def analyze(drawio_path, modules_dir):
    nodes, edges = parse_drawio(drawio_path)
    blocks = build_scenario_flow(nodes, edges)
    surfaces = load_part_surfaces(modules_dir)
    present_parts = set()
    if os.path.isdir(modules_dir):
        present_parts = {d for d in os.listdir(modules_dir)
                         if os.path.isfile(os.path.join(modules_dir, d, "part.json"))}
    findings = []
    findings += surface_branches(blocks, surfaces, present_parts)
    findings += surface_slots(blocks, present_parts)
    findings += safety_lint(nodes)
    return {"scenario_flow": blocks, "findings": findings,
            "n_surfaces": len(surfaces), "n_nodes": len(nodes)}


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    try:  # Windows コンソール(cp932)での日本語/記号化け回避
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    args = sys.argv[1:]
    if not args:
        print("usage: python drawio_to_scenario.py <設計.drawio> [--json] [--modules <dir>]",
              file=sys.stderr)
        sys.exit(2)
    as_json = "--json" in args
    modules_dir = os.path.join(_repo_root(), "modules")
    if "--modules" in args:
        modules_dir = args[args.index("--modules") + 1]
    drawio_path = next(a for a in args if not a.startswith("--")
                       and a != modules_dir)
    if not os.path.exists(drawio_path):
        print(f"input not found: {drawio_path}", file=sys.stderr)
        sys.exit(1)

    result = analyze(drawio_path, modules_dir)

    if as_json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        sev_order = {"CRITICAL": 0, "WARN": 1, "OK": 2}
        f = sorted(result["findings"], key=lambda x: sev_order.get(x["severity"], 9))
        n_crit = sum(1 for x in result["findings"] if x["severity"] == "CRITICAL")
        n_warn = sum(1 for x in result["findings"] if x["severity"] == "WARN")
        print(f"=== {os.path.basename(drawio_path)} ===")
        print(f"ノード {result['n_nodes']} / 復元ブロック {len(result['scenario_flow'])} "
              f"/ 認定 surface {result['n_surfaces']}")
        print(f"surfacing: CRITICAL {n_crit} / WARN {n_warn}")
        print("-" * 60)
        for x in f:
            mark = {"CRITICAL": "[X ]", "WARN": "[! ]", "OK": "[OK]"}.get(x["severity"], "[? ]")
            print(f"{mark} [{x['code']}] {x['step']}: {x['message']}")

    n_crit = sum(1 for x in result["findings"] if x["severity"] == "CRITICAL")
    sys.exit(1 if n_crit else 0)


if __name__ == "__main__":
    main()
