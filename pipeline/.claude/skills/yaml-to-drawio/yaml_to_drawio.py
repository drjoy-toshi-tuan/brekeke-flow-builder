"""
yaml-to-drawio: voicebot-flow-builder の設計書 YAML を drawio に変換する skill 本体。

使い方:
  python yaml_to_drawio.py <設計書.yaml> [出力.drawio]

視覚標準(配色 / ノード描画 / エッジ / 凡例 / アナウンス一覧)は drawio_style.py に集約。
drawio_style.py は drawio-templates/ プロジェクトの正本を vendoring した **編集禁止コピー**。
変更は正本(drawio-templates/drawio_style.py)に入れ、check_sync.py で再配布すること。

出力は 2 タブ:
  タブ1「シナリオフロー図」 … 冒頭/終話を中央軸に置く左右対称レイアウト。矢印は最背面。
                              hearing の聴取失敗(リトライ上限)は赤・破線エッジで遷移先へ。
  タブ2「アナウンス一覧」   … 聴取項目|復唱|リトライ|失敗時|発話文言(src_ref でタブ1と同期)

v2 (2026-06-05) の主な変更:
  - リトライ回数・聴取失敗時の挙動を自動描画(CSTS フィードバック)。
      タブ1: end_failure→END_聴取失敗 / disconnect→切断 を赤・破線エッジで接続。
      タブ2: 「リトライ」「失敗時」列を追加。
  - 中央寄せ対称レイアウト(冒頭/終話を中央軸、分岐を左右等間隔)。
  - 矢印を最背面に配置(タブ1 はエッジ→ノードの順に出力)。

詳細は SKILL.md を参照。
"""
import sys
import os
from collections import defaultdict, deque
from html import escape

try:
    import yaml
except ImportError:
    print("Error: PyYAML が必要です(本環境はインストール禁止のため pre-install 済みを前提)", file=sys.stderr)
    sys.exit(1)

# ─── 視覚標準(SSoT の vendored コピー) ───
from drawio_style import (
    resolve_type_color,
    sanitize_id,
    NODE_W,
    NODE_H,
    node_xml,
    edge_xml,
    build_legend,
    build_announce_page,
)

# バッジは付けないがレイアウト上の縦ピッチに使う(ノード高 + 余白)
NODE_H_SLOT = NODE_H


# ─── 終話パターンの分類 ───
def is_failure_termination(name: str, condition: str = "") -> bool:
    """「聴取失敗(リトライ上限到達)」系の終話かどうか。"""
    text = f"{name} {condition}"
    return any(k in text for k in ("聴取失敗", "リトライ", "retry", "聞き取", "聞取"))


# ─── YAML → ブロック抽出 ───
def extract_blocks(spec: dict):
    """設計書 YAML から scenario_flow + 暗黙 termination を抽出。

    各ブロック:
      step, type, is_branch
      edges: [{"to": step名, "label": str, "kind": "flow"|"failure"}]
      hearing_meta: hearing のみ {retry_count, echo_back, retry_failure, no_result_default}
    """
    sf = spec.get("scenario_flow", []) or []

    hi_by_name = {}
    for h in (spec.get("hearing_items") or []):
        nm = (h.get("name") or "").strip()
        if nm:
            hi_by_name[nm] = h
    sd_by_name = {}
    for d in (spec.get("step_details") or []):
        nm = (d.get("step_name") or "").strip()
        if nm:
            sd_by_name[nm] = d

    # 失敗終話の遷移先名を決定
    failure_term_name = None
    for t in (spec.get("termination_patterns") or []):
        nm = (t.get("name") or "").strip()
        if nm and is_failure_termination(nm, t.get("condition", "")):
            failure_term_name = nm
            break
    if failure_term_name is None:
        failure_term_name = "END_聴取失敗"

    blocks = []
    needs_disconnect_node = False
    failure_term_used = False
    for b in sf:
        step = b.get("step", "")
        btype = b.get("type", "")
        if not step or not btype:
            continue

        edges = []
        if b.get("next"):
            edges.append({"to": b["next"], "label": "", "kind": "flow"})
        for cond in (b.get("conditions") or []):
            n = cond.get("next", "")
            label = cond.get("match", "")
            if n:
                edges.append({"to": n, "label": label, "kind": "flow"})
        is_branch = len(b.get("conditions") or []) > 0

        block = {
            "step": step, "type": btype, "is_branch": is_branch,
            "edges": edges, "hearing_meta": None,
        }

        if btype == "hearing":
            hi = hi_by_name.get(step, {})
            sd = sd_by_name.get(step, {})
            retry_failure = (b.get("retry_failure") or sd.get("retry_failure") or "end_failure")
            block["hearing_meta"] = {
                "retry_count": hi.get("retry_count", 2),
                "echo_back": bool(hi.get("echo_back", False)),
                "retry_failure": retry_failure,
                "no_result_default": b.get("no_result_default", ""),
            }
            if retry_failure == "end_failure":
                edges.append({"to": failure_term_name, "label": "聴取失敗", "kind": "failure"})
                failure_term_used = True
            elif retry_failure == "disconnect":
                edges.append({"to": "切断", "label": "聴取失敗", "kind": "failure"})
                needs_disconnect_node = True
            # skip は次へ進む(タブ2 の失敗時列で表記、エッジは引かない)

        blocks.append(block)

    existing = {b["step"] for b in blocks}

    for t in (spec.get("termination_patterns") or []):
        name = (t.get("name") or "").strip()
        if name and name not in existing:
            blocks.append({"step": name, "type": "termination", "is_branch": False,
                           "edges": [], "hearing_meta": None})
            existing.add(name)

    # 失敗終話ノードは実際に参照される場合のみ合成(未使用の孤立ノードを作らない)
    if failure_term_used and failure_term_name not in existing:
        blocks.append({"step": failure_term_name, "type": "termination", "is_branch": False,
                       "edges": [], "hearing_meta": None})
        existing.add(failure_term_name)
    if needs_disconnect_node and "切断" not in existing:
        blocks.append({"step": "切断", "type": "termination", "is_branch": False,
                       "edges": [], "hearing_meta": None})
        existing.add("切断")

    # edges に書かれているが blocks に無い step を補完
    referenced = set()
    for b in blocks:
        for e in b["edges"]:
            referenced.add(e["to"])
    for ref in referenced - existing:
        blocks.append({
            "step": ref,
            "type": "termination" if ref.startswith("END_") or "終話" in ref else "item",
            "is_branch": False, "edges": [], "hearing_meta": None,
        })

    return blocks


# ─── レイアウト計算(層別 longest-path + バリセンター整列 + 中央寄せ) ───
X_GAP = 240
Y_PITCH = 130
X_LEFT_MARGIN = 80
Y_OFFSET = 120


def calc_layout(blocks):
    """各ノードに (x, y)=左上座標 を割り振り、(coords, center_x) を返す。

    - 層(縦位置)= root からの longest-path(合流は全親より下)
    - 同層の並び = バリセンター法(交差抑制)
    - 各層を共通の中央軸 center_x を中心に左右対称・等間隔配置
      → 冒頭(root 単独層)/主終話(単独層)は自然と中央軸に乗る
    - root から到達できない孤立終話(非通知/時間外等)は最下段にまとめる
    """
    by_name = {b["step"]: b for b in blocks}
    names = [b["step"] for b in blocks]
    order_index = {b["step"]: i for i, b in enumerate(blocks)}

    adj = defaultdict(list)
    indeg = defaultdict(int)
    for b in blocks:
        for e in b["edges"]:
            if e["to"] in by_name:
                adj[b["step"]].append(e["to"])
                indeg[e["to"]] += 1
    for n in names:
        indeg.setdefault(n, 0)

    roots = sorted([n for n in names if indeg[n] == 0], key=lambda n: order_index[n])
    indeg2 = dict(indeg)
    q = deque(roots)
    topo, seen = [], set()
    while q:
        n = q.popleft()
        if n in seen:
            continue
        seen.add(n)
        topo.append(n)
        for m in adj[n]:
            indeg2[m] -= 1
            if indeg2[m] <= 0 and m not in seen:
                q.append(m)
    if len(topo) < len(names):
        topo += sorted([n for n in names if n not in seen], key=lambda n: order_index[n])

    primary_root = roots[0] if roots else (names[0] if names else None)
    reachable = set()
    if primary_root is not None:
        stack = [primary_root]
        while stack:
            n = stack.pop()
            if n in reachable:
                continue
            reachable.add(n)
            stack.extend(adj[n])

    depth = {n: 0 for n in names}
    for n in topo:
        if n not in reachable:
            continue
        for m in adj[n]:
            if m in reachable and depth[m] < depth[n] + 1:
                depth[m] = depth[n] + 1

    # 孤立ノード(root=冒頭 から到達不能。非通知/時間外 等は冒頭ブロック内部から自動配線され、
    # ブロック単位のエッジを持たない)は層レイアウトから除外し、後段で「冒頭の右側」カラムにまとめる。
    orphans = [n for n in names if n not in reachable]

    by_depth = defaultdict(list)
    for n in names:
        if n in reachable:
            by_depth[depth[n]].append(n)
    for d in by_depth:
        by_depth[d].sort(key=lambda n: order_index[n])

    parents = defaultdict(list)
    children = defaultdict(list)
    for b in blocks:
        for e in b["edges"]:
            if e["to"] in by_name:
                children[b["step"]].append(e["to"])
                parents[e["to"]].append(b["step"])

    depths_sorted = sorted(by_depth.keys())

    def pos_index(layer):
        return {name: i for i, name in enumerate(by_depth[layer])}

    for _ in range(4):
        for d in depths_sorted:
            if d == 0:
                continue
            above = pos_index(d - 1)
            def bary(n):
                ps = [above[p] for p in parents[n] if p in above]
                return sum(ps) / len(ps) if ps else order_index[n] / 1000.0
            by_depth[d].sort(key=lambda n: (bary(n), order_index[n]))
        for d in reversed(depths_sorted):
            below = pos_index(d + 1) if (d + 1) in by_depth else {}
            def bary_c(n):
                cs = [below[c] for c in children[n] if c in below]
                return sum(cs) / len(cs) if cs else order_index[n] / 1000.0
            by_depth[d].sort(key=lambda n: (bary_c(n), order_index[n]))

    max_in_layer = max((len(v) for v in by_depth.values()), default=1)
    half_widest = (max_in_layer - 1) * X_GAP / 2.0
    center_x = X_LEFT_MARGIN + half_widest + NODE_W / 2.0

    coords = {}
    for d in depths_sorted:
        layer = by_depth[d]
        n = len(layer)
        start = center_x - (n - 1) * X_GAP / 2.0
        y = Y_OFFSET + d * Y_PITCH
        for i, name in enumerate(layer):
            slot_center = start + i * X_GAP
            coords[name] = (int(round(slot_center - NODE_W / 2.0)), int(y))

    # 孤立終話(非通知/時間外 等)を「冒頭の右側」の専用カラムに縦に並べる。
    # ブロック単位ビューでは冒頭内部からの配線が線で出ず最下段で孤立して見えるが .bivr では配線済み。
    # CS が誤ってエッジを引かないよう、右側へどかして注釈(build_drawio 側)を添える。
    orphan_col_x = None
    if orphans:
        reach_max_x = max((x for x, _ in coords.values()), default=int(center_x))
        orphan_col_x = int(reach_max_x + X_GAP + X_GAP // 2)
        for i, name in enumerate(orphans):
            coords[name] = (orphan_col_x, int(Y_OFFSET + i * Y_PITCH))

    return coords, center_x, orphans, orphan_col_x


# ─── アナウンス一覧の行データ(YAML 固有) ───
def _failure_label(policy: str) -> str:
    return {"skip": "スキップ", "disconnect": "切断", "end_failure": "終話"}.get(policy, "終話")


def build_announce_rows(spec, blocks, name_to_id):
    """ページ2 の行データ。
    戻り値: [(聴取項目名, 復唱, リトライ, 失敗時, 発話文言, fill, stroke, src_id), ...]
    step_details の登場順を優先し、最後に termination_patterns を足す。
    """
    step_details = spec.get("step_details") or []
    terminations = spec.get("termination_patterns") or []

    type_by_step = {b["step"]: (b["type"], b["is_branch"]) for b in blocks}
    meta_by_step = {b["step"]: b["hearing_meta"] for b in blocks if b["hearing_meta"]}

    echo_by_name = {}
    retry_by_name = {}
    for h in (spec.get("hearing_items") or []):
        nm = h.get("name", "")
        if nm:
            echo_by_name[nm] = "あり" if h.get("echo_back") else "無し"
            retry_by_name[nm] = h.get("retry_count", None)

    rows = []
    for sd in step_details:
        name = sd.get("step_name", "")
        if not name:
            continue
        text = sd.get("tts_announcement", "") or ""
        btype, is_branch = type_by_step.get(name, ("announcement", False))
        _, fill, stroke, _ = resolve_type_color(btype, is_branch)
        meta = meta_by_step.get(name)
        echo = echo_by_name.get(name, ("あり" if (meta and meta["echo_back"]) else "無し"))
        if meta:
            rc = retry_by_name.get(name)
            rc = meta["retry_count"] if rc is None else rc
            retry = f"×{rc}"
            failure = _failure_label(meta["retry_failure"])
        else:
            retry, failure = "-", "-"
        rows.append((name, echo, retry, failure, text, fill, stroke, name_to_id.get(name, "")))
    for t in terminations:
        name = t.get("name", "")
        if not name:
            continue
        text = t.get("tts_announcement", "") or ""
        rows.append((name, "無し", "-", "-", text, "#FFEBEE", "#E53935", name_to_id.get(name, "")))
    return rows


# ─── drawio XML 生成(2 タブ: シナリオフロー図 / アナウンス一覧) ───
def build_drawio(spec, blocks, coords, center_x, orphans=None, orphan_col_x=None):
    basic = spec.get("basic_info", {}) or {}
    title_text = f"{basic.get('facility_name', '')}  {basic.get('scenario_name', '')}".strip()
    if not title_text:
        title_text = "シナリオフロー図"

    # ID テーブル
    used_ids = {}
    name_to_id = {}
    for b in blocks:
        name_to_id[b["step"]] = sanitize_id(b["step"], used_ids)

    # ノードに埋め込む announce / repeat
    announce_by_step = {}
    for sd in (spec.get("step_details") or []):
        nm = sd.get("step_name", "")
        if nm:
            announce_by_step[nm] = sd.get("tts_announcement", "") or ""
    for t in (spec.get("termination_patterns") or []):
        nm = t.get("name", "")
        if nm and nm not in announce_by_step:
            announce_by_step[nm] = t.get("tts_announcement", "") or ""
    repeat_by_step = {}
    for h in (spec.get("hearing_items") or []):
        nm = h.get("name", "")
        if nm:
            repeat_by_step[nm] = "あり" if h.get("echo_back") else "無し"

    # ノード XML
    nodes_xml = []
    for b in blocks:
        x, y = coords.get(b["step"], (int(center_x), 60))
        nodes_xml.append(node_xml(
            name_to_id[b["step"]], x, y, b["step"], b["type"], b["is_branch"],
            announce=announce_by_step.get(b["step"], ""),
            repeat=repeat_by_step.get(b["step"], "無し"),
        ))

    # 孤立終話カラムの注釈。CS が「線が無い＝繋ぎ忘れ」と誤解して引こうとするのを防ぐ。
    if orphans and orphan_col_x is not None:
        note_y = Y_OFFSET - 46
        nodes_xml.append(
            f'        <mxCell id="orphan_note" parent="1" '
            f'style="text;html=1;strokeColor=#F9A825;fillColor=#FFFDE7;align=center;'
            f'verticalAlign=middle;whiteSpace=wrap;rounded=1;fontSize=10;fontColor=#795548;dashed=1;" '
            f'value="{escape("冒頭・失敗から自動配線（線は省略）")}" vertex="1">'
            f'<mxGeometry height="36" width="{NODE_W}" x="{orphan_col_x}" y="{note_y}" as="geometry" /></mxCell>'
        )

    # エッジ XML(failure は赤・破線)
    edges_xml = []
    for b in blocks:
        src = name_to_id.get(b["step"])
        if not src:
            continue
        for e in b["edges"]:
            tgt = name_to_id.get(e["to"])
            if not tgt:
                continue
            if e["kind"] == "failure":
                edges_xml.append(edge_xml(src, tgt, e["label"], kind="failure"))
            else:
                edges_xml.append(edge_xml(src, tgt, e["label"]))

    # バウンディングボックス
    if coords:
        node_max_x = max(x for x, _ in coords.values()) + NODE_W
        node_max_y = max(y for _, y in coords.values()) + NODE_H
        node_min_x = min(x for x, _ in coords.values())
    else:
        node_max_x, node_max_y, node_min_x = 1200, 700, 80

    # 凡例は最下段ノードの下・左寄せ(中央寄せレイアウトを崩さない)
    legend_x = max(int(node_min_x), 40)
    legend_y = int(node_max_y) + 70
    legend = build_legend(legend_x, legend_y)

    # ページ1: 中央軸 center_x = ページ中央 になるよう pageWidth=2*center_x
    p1_w = max(int(round(center_x * 2)), legend_x + 320, int(node_max_x) + 80)
    p1_h = max(legend_y + 240 + 40, int(node_max_y) + 80)

    # 出力順: title → subtitle → エッジ(最背面) → ノード(最前面) → 凡例
    flow_page = f'''  <diagram name="シナリオフロー図" id="yaml_to_drawio_flow">
    <mxGraphModel dx="1885" dy="991" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{p1_w}" pageHeight="{p1_h}" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="title" parent="1" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;fontColor=#212121;" value="{escape(title_text)}" vertex="1">
          <mxGeometry height="30" width="800" x="40" y="20" as="geometry" />
        </mxCell>
        <mxCell id="subtitle" parent="1" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=11;fontColor=#9E9E9E;" value="設計書 YAML から自動生成: ノード{len(blocks)}個 / エッジ{len(edges_xml)}本(うち赤破線=聴取失敗時の遷移)" vertex="1">
          <mxGeometry height="20" width="900" x="40" y="50" as="geometry" />
        </mxCell>
{chr(10).join(edges_xml)}
{chr(10).join(nodes_xml)}
{legend}
      </root>
    </mxGraphModel>
  </diagram>'''

    # ページ2(アナウンス一覧)
    rows = build_announce_rows(spec, blocks, name_to_id)
    announce_page = build_announce_page(rows, title_text) if rows else ""

    pages = flow_page
    if announce_page:
        pages += "\n" + announce_page

    return (
        '<mxfile host="app.diagrams.net" agent="Claude (yaml-to-drawio skill v2)">\n'
        + pages
        + "\n</mxfile>\n"
    )


def convert(yaml_path: str, out_path: str | None = None) -> str:
    with open(yaml_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    if not isinstance(spec, dict):
        raise ValueError(f"設計書 YAML の構造が不正: {yaml_path}")

    blocks = extract_blocks(spec)
    if not blocks:
        raise ValueError(f"scenario_flow が空: {yaml_path}")

    coords, center_x, orphans, orphan_col_x = calc_layout(blocks)
    drawio = build_drawio(spec, blocks, coords, center_x, orphans, orphan_col_x)

    if out_path is None:
        base = os.path.splitext(os.path.basename(yaml_path))[0]
        out_path = os.path.join(os.path.dirname(yaml_path), f"{base}_drawio.drawio")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(drawio)

    return out_path


def main():
    if len(sys.argv) < 2:
        print("usage: python yaml_to_drawio.py <設計書.yaml> [出力.drawio]", file=sys.stderr)
        sys.exit(2)
    yaml_path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) >= 3 else None
    if not os.path.exists(yaml_path):
        print(f"input not found: {yaml_path}", file=sys.stderr)
        sys.exit(1)
    try:
        out_path = convert(yaml_path, out)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
