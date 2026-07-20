#!/usr/bin/env python3
"""
block_layout.py -- Stage A: ブロックトップ位置を決定する

scaffold_generator が生成した JSON と設計書 YAML から:
  1. 各「ブロック」を単位としたグラフを構築
  2. 主経路は縦に伸ばし、分岐は横に展開
  3. 各ブロックの (x_top, y_top) ピクセル座標を決定

出力: { block_step_name: (x_top, y_top) }

Stage B (layout_calculator.py) が、このトップ位置を基準にブロック内の各モジュールを配置する。
"""

from __future__ import annotations

import sys
from pathlib import Path

from block_layout_spec import (
    BLOCK_SPECS, HEARING_ECHO, HEARING_SIMPLE, TERMINATION, OPENING,
    SUBFLOW, ANNOUNCEMENT, SINGLE_BOX,
    CELL_WIDTH, CELL_HEIGHT, BLOCK_VPAD, BLOCK_HPAD, COLS_PER_BLOCK,
    get_block_spec, cell_to_px, BlockSpec,
)
from scaffold_generator import (
    _subflow_base_name, _INLINE_SUBFLOW_SLOT, _INLINE_SUBFLOW_SAVE_TO,
    call_transfer_auto_terminations, _ensure_opening_announcement,
)

# 個人情報4種のうち scaffold がインライン展開（type: slot 相当）するもの。
# _INLINE_SUBFLOW_SLOT (氏名/生年月日/電話番号) + 診察券番号（scaffold 側は
# _build_card_number_block で別関数だが、layout 上は slot_card_number 扱い）。
# scaffold_generator._inline_personal_info_subflow() の対象条件と同期させること。
_INLINE_SLOT_KIND = dict(_INLINE_SUBFLOW_SLOT)
_INLINE_SLOT_KIND["診察券番号聴取"] = "card_number"

# slot_kind → save_to（save2db モジュール名 save-{save_to} の判定に必要）。
# scaffold_generator._inline_personal_info_subflow() の synthetic block と同期させること。
_INLINE_SLOT_SAVE_TO = dict(_INLINE_SUBFLOW_SAVE_TO)
_INLINE_SLOT_SAVE_TO["card_number"] = "medicalCardNumber"

# 「個人情報聴取」wrapper 展開順序。scaffold_generator の chain_targets と同期させること。
_WRAPPER_CHAIN_TARGETS = ["診察券番号聴取", "氏名聴取", "生年月日聴取", "電話番号聴取"]


# ─── scenario_flow からブロック情報を抽出 ────────────────────────
def extract_blocks_from_spec(spec: dict) -> list[dict]:
    """設計書 YAML から scenario_flow を読み、ブロック情報のリストを返す。
    各要素: {step, type, echo_back, next_blocks, is_terminal}

    opening ブロックには暗黙の子として以下を追加する:
      - 非通知系 termination（incoming-classifier から自動接続）
      - 時間外系 termination（acceptance_times から自動接続）
    これにより opening 付近に横展開される。
    """
    # Safety net: 冒頭_アナウンス 欠落時の自動補完（scaffold_generator.generate_scaffold_v2 と同一処理）。
    # scaffold_generator はこれを in-memory で spec に挿入するだけで YAML には書き戻さないため、
    # block_layout.py が別プロセスで YAML を独立に読み直す際は同じ補完をしないと、
    # 自動挿入された 冒頭_アナウンス（+save2db）が scenario_flow に存在せず所属不明フォールバックに落ちる。
    _ensure_opening_announcement(spec)

    scenario_flow = spec.get("scenario_flow", []) or []
    hearing_items = {h.get("name"): h for h in (spec.get("hearing_items") or [])}

    # termination_patterns を先に読む（termination ブロックの completion_flag_name 解決に必要）。
    # completion_flag_name は director が termination_patterns で自由に指定するフィールドであり、
    # name（例: "END_予約"）から機械的に導出できるとは限らない（scaffold_generator.py も
    # term["completion_flag_name"] をそのまま使う。文字列操作での推測はしない）。
    term_patterns = list(spec.get("termination_patterns") or [])
    if any(b.get("type") == "call_transfer" for b in scenario_flow):
        _existing_tp_names = {tp.get("name", "") for tp in term_patterns}
        for auto_term in call_transfer_auto_terminations():
            if auto_term["name"] not in _existing_tp_names:
                term_patterns.append(auto_term)
    term_index = {tp.get("name", ""): tp for tp in term_patterns if tp.get("name")}

    blocks: list[dict] = []
    for b in scenario_flow:
        step  = b.get("step", "")
        btype = b.get("type", "")
        if not step or not btype:
            continue

        echo_back = False
        save_to = ""
        # ファーストクラスエイリアス（type: dob/phone/patient_name/card_number を
        # subflow を介さず直に書く、新規作成の既定パターン）は build_module_to_block_map /
        # get_block_spec が "slot" + slot_kind を前提にしているため正規化する。
        # _INLINE_SLOT_KIND と同じ対応表（scaffold_generator._inline_personal_info_subflow
        # と同期させること）。
        _FIRST_CLASS_SLOT_KIND = {
            "dob": "date_of_birth", "phone": "phone",
            "patient_name": "patient_name", "card_number": "card_number",
        }
        if btype == "hearing":
            h = hearing_items.get(step) or hearing_items.get(step.rsplit("_", 1)[0])
            if h:
                echo_back = bool(h.get("echo_back", False))
                save_to = h.get("save_to", "")
        elif btype in _FIRST_CLASS_SLOT_KIND:
            # slot 型（およびファーストクラスエイリアス）は save_to を YAML から直接持つ
            # （hearing_items 経由ではない）。save-{save_to} 共有モジュールの分類に必要。
            save_to = b.get("save_to", "")
            b = dict(b)
            b["slot"] = _FIRST_CLASS_SLOT_KIND[btype]
            btype = "slot"
        elif btype == "slot":
            save_to = b.get("save_to", "")
        elif btype in ("intent", "free_text", "clinical_department", "faq"):
            # これらも hearing と同じ TTS→STT→(script|OpenAI)→Retry→save2db 構造を
            # scaffold_generator.py が生成するため、layout 上は hearing 系として扱う。
            save_to = b.get("save_to", "")

        # 次ブロック名を抽出: next (単線) or conditions (分岐)
        next_blocks: list[str] = []
        if b.get("next"):
            next_blocks.append(b["next"])
        for cond in (b.get("conditions") or []):
            nxt = cond.get("next", "")
            if nxt:
                next_blocks.append(nxt)

        # 個人情報4種の subflow は scaffold が Jump to Flow を使わず決定論インライン展開する
        # （scaffold_generator._inline_personal_info_subflow）。layout も実際に生成される
        # モジュール名（slot 型の命名規則）に合わせて type を "slot" 相当へ読み替える。
        # そうしないと _classify_module_in_block が "jump_" prefix しか見ないため、
        # インライン展開された全モジュールが「所属不明」フォールバックに落ちる。
        if btype == "subflow":
            flowname = b.get("flowname", "") or ""
            if "個人情報聴取" in flowname:
                # wrapper: 1 YAML ブロックを 4 連チェーン（診察券番号→氏名→生年月日→電話番号）に展開
                chain_modules = [step] + [f"jump_{t}" for t in _WRAPPER_CHAIN_TARGETS[1:]]
                for i, (mname, target_name) in enumerate(zip(chain_modules, _WRAPPER_CHAIN_TARGETS)):
                    chain_next = [chain_modules[i + 1]] if i + 1 < len(chain_modules) else next_blocks
                    slot_kind = _INLINE_SLOT_KIND[target_name]
                    blocks.append({
                        "step":         mname,
                        "type":         "slot",
                        "echo_back":    False,
                        "save_to":      _INLINE_SLOT_SAVE_TO[slot_kind],
                        "next_blocks":  chain_next,
                        "is_terminal":  False,
                        "slot":         slot_kind,
                        "input_method": "voice_only",
                    })
                continue
            base_name = _subflow_base_name(flowname)
            if base_name in _INLINE_SLOT_KIND:
                btype = "slot"
                b = dict(b)
                b["slot"] = _INLINE_SLOT_KIND[base_name]
                save_to = _INLINE_SLOT_SAVE_TO[b["slot"]]

        is_terminal = (btype == "termination")
        completion_flag_name = ""
        termination_module_ref = ""
        if is_terminal:
            # termination_ref が step と異なる名前を指す場合、scaffold_generator は
            # 実際のモジュール名を termination_ref（term_patterns の name）から生成する
            # （scenario_flow の termination エントリ自体は参照専用の no-op）。
            # "step" はグラフ traversal（next_blocks からの参照）のためだけに残し、
            # モジュール名判定には termination_module_ref を使う。
            ref = b.get("termination_ref", step)
            completion_flag_name = term_index.get(ref, {}).get("completion_flag_name", "")
            termination_module_ref = ref
        blocks.append({
            "step":                     step,
            "type":                     btype,
            "echo_back":                echo_back,
            "save_to":                  save_to,
            "next_blocks":              next_blocks,
            "is_terminal":              is_terminal,
            "completion_flag_name":     completion_flag_name,
            "termination_module_ref":   termination_module_ref,
            # spec selection fields — must be forwarded for get_block_spec() to resolve correctly
            "slot":         b.get("slot", ""),
            "input_method": b.get("input_method", "voice_only"),
        })

    # termination_patterns に定義されているが scenario_flow に termination ブロックとして
    # 未記載の termination を暗黙ブロックとして追加（scaffold は termination_patterns から
    # 全件モジュールを生成するため、block_layout もカバーする必要がある）。
    # 「未記載」判定は termination_module_ref（実モジュール名の元になる ref）で行う。
    # step（例: "END_受付完了"）と ref（例: "受付完了"）が異なる場合、step だけを見ると
    # 既にカバー済みの ref を再び暗黙ブロックとして重複追加してしまう。
    existing_term_refs = {
        (b.get("termination_module_ref") or b["step"])
        for b in blocks if b["type"] == "termination"
    }
    for tp in term_patterns:
        tp_name = tp.get("name", "")
        if tp_name and tp_name not in existing_term_refs:
            blocks.append({
                "step":                   tp_name,
                "type":                   "termination",
                "echo_back":              False,
                "next_blocks":            [],
                "is_terminal":            True,
                "completion_flag_name":   tp.get("completion_flag_name", ""),
                "termination_module_ref": tp_name,
            })

    # opening ブロックに暗黙の子（非通知/時間外の system termination）を注入
    # これにより DFS で opening の隣に横展開される
    OPENING_ADJACENT_KEYWORDS = ["非通知", "時間外"]
    term_steps = [b["step"] for b in blocks if b["type"] == "termination"]
    opening_block = next((b for b in blocks if b["type"] == "opening"), None)
    if opening_block:
        for kw in OPENING_ADJACENT_KEYWORDS:
            for t in term_steps:
                if kw in t and t not in opening_block["next_blocks"]:
                    opening_block["next_blocks"].append(t)

    return blocks


# ─── ブロックグラフ → トップ位置決定 ───────────────────────────
def assign_block_tops(blocks: list[dict]) -> dict[str, tuple[int, int]]:
    """各ブロックの (x_top, y_top) をピクセル単位で決定して返す。

    アルゴリズム（centered tree layout）:
      Pass 1 (bottom-up): 各サブツリーの横幅（px）を再帰的に計算。
        - 葉・合流ノード・終話ノードは自身のブロック幅のみ。
        - 分岐ノードは子サブツリー幅の合計 + 隙間。
      Pass 2 (top-down): エントリから top-down でピクセル座標を確定。
        - 単一子: 親と同じ x_center。
        - 複数子: 子サブツリーを横に並べ、親は子全体の中心に配置。
        - 合流ノード（複数親）: 親全員が確定してから親の x_center 平均に配置。
        - 終話ノード: 主経路の配置完了後、親の横に並べる。

    出力: step_name → (x_top_px, y_top_px)
    """
    from collections import deque

    block_map = {b["step"]: b for b in blocks}
    children = {b["step"]: list(dict.fromkeys(b["next_blocks"])) for b in blocks}
    parents: dict[str, list[str]] = {b["step"]: [] for b in blocks}
    for b in blocks:
        for child in b["next_blocks"]:
            if child in parents and b["step"] not in parents[child]:
                parents[child].append(b["step"])

    # ── ユーティリティ ────────────────────────────────────────────
    UNIT_W = COLS_PER_BLOCK * (CELL_WIDTH + BLOCK_HPAD)  # 1ブロック単位幅 (px)

    def block_h(step: str) -> int:
        """ブロックの縦消費量 (px) = spec.size[1] * CELL_HEIGHT + BLOCK_VPAD"""
        b = block_map.get(step)
        if not b:
            return CELL_HEIGHT + BLOCK_VPAD
        spec = get_block_spec(b["type"], b.get("echo_back", False),
                              slot_kind=b.get("slot", ""))
        return spec.size[1] * CELL_HEIGHT + BLOCK_VPAD

    def block_w(step: str) -> int:
        """ブロックの横幅 (px) = spec.size[0] * (CELL_WIDTH + BLOCK_HPAD)"""
        b = block_map.get(step)
        if not b:
            return UNIT_W
        spec = get_block_spec(b["type"], b.get("echo_back", False),
                              slot_kind=b.get("slot", ""))
        return spec.size[0] * (CELL_WIDTH + BLOCK_HPAD)

    def is_terminal(step: str) -> bool:
        return block_map.get(step, {}).get("is_terminal", False)

    def is_convergence(step: str) -> bool:
        """複数の親を持つ = 合流ノード"""
        return len(parents.get(step, [])) > 1

    # ── Pass 1: サブツリー幅を bottom-up で計算 ────────────────────
    # 終話ノード・合流ノードは自身の幅のみ（親の中心に寄せるので展開しない）
    subtree_w_cache: dict[str, int] = {}

    def subtree_width(step: str, visiting: frozenset = frozenset()) -> int:
        if step in subtree_w_cache:
            return subtree_w_cache[step]
        if step in visiting or is_terminal(step) or is_convergence(step):
            w = block_w(step)
            subtree_w_cache[step] = w
            return w

        non_term_kids = [k for k in children.get(step, []) if not is_terminal(k)]
        # 合流先は展開しない（自身の幅のみカウント）
        expandable = [k for k in non_term_kids if not is_convergence(k)]

        if not expandable:
            w = block_w(step)
            subtree_w_cache[step] = w
            return w

        new_vis = visiting | {step}
        kids_total = sum(subtree_width(k, new_vis) for k in expandable)
        # 子間の横余白
        kids_total += (len(expandable) - 1) * BLOCK_HPAD
        w = max(block_w(step), kids_total)
        subtree_w_cache[step] = w
        return w

    # ── エントリブロック ──────────────────────────────────────────
    entry_candidates = [b["step"] for b in blocks if not parents.get(b["step"], [])]
    entry = next((s for s in entry_candidates if block_map[s]["type"] == "opening"),
                 entry_candidates[0] if entry_candidates else (blocks[0]["step"] if blocks else None))
    if not entry:
        return {}

    # ── Pass 2: top-down BFS でピクセル座標を確定 ─────────────────
    result: dict[str, tuple[int, int]] = {}   # step → (x_center_px, y_top_px)
    # x_center = ブロック中心の x 座標。layout_calculator は block_tops を左上として使うため
    # 最後に x_left = x_center - block_w/2 に変換する。
    # ここでは計算の便宜上 x_center で管理し、最後に変換する。
    x_center_map: dict[str, float] = {}

    # (step, x_center, y_top) のキュー
    queue: deque[tuple[str, float, int]] = deque([(entry, 0.0, 0)])
    # 合流ノード: 全親配置待ちのキャッシュ
    pending_convergence: dict[str, list[tuple[float, int]]] = {}

    def try_place_convergence(step: str) -> None:
        """合流ノードの全親が確定済みなら配置してキューに投入する"""
        plist = parents.get(step, [])
        if not plist or not all(p in x_center_map for p in plist):
            return
        if step in x_center_map:
            return
        cx = sum(x_center_map[p] for p in plist) / len(plist)
        y = max(result[p][1] + block_h(p) for p in plist)
        queue.append((step, cx, y))

    while queue:
        step, cx, y = queue.popleft()

        if step in x_center_map:
            continue

        # 合流ノードは全親が確定してから（BFS で一部未確定の場合はスキップ）
        if is_convergence(step):
            plist = parents.get(step, [])
            unplaced = [p for p in plist if p not in x_center_map]
            if unplaced:
                pending_convergence.setdefault(step, []).append((cx, y))
                continue
            # 全親確定: 親の x_center 平均・最大 y に配置
            cx = sum(x_center_map[p] for p in plist) / len(plist)
            y = max(result[p][1] + block_h(p) for p in plist)

        x_center_map[step] = cx
        # layout_calculator は block_top の左上 (x, y) を使うので左端に変換
        x_left = int(cx - block_w(step) / 2)
        result[step] = (x_left, y)

        # 子の合流ノードを再試行（この親が確定したことで条件が満たされた可能性）
        for kid in children.get(step, []):
            if is_convergence(kid) and kid not in x_center_map:
                try_place_convergence(kid)

        # 子を配置（終話ノードは後回し）
        non_term_kids = [k for k in children.get(step, []) if not is_terminal(k)]
        y_next = y + block_h(step)

        if len(non_term_kids) == 0:
            pass  # 子なし: 終話のみか末端
        elif len(non_term_kids) == 1:
            kid = non_term_kids[0]
            if kid not in x_center_map:
                queue.append((kid, cx, y_next))
        else:
            # 複数子: サブツリー幅に応じて均等配置、親は中心に
            widths = [subtree_width(k) for k in non_term_kids]
            total_w = sum(widths) + (len(non_term_kids) - 1) * BLOCK_HPAD
            x_start = cx - total_w / 2
            for kid, w in zip(non_term_kids, widths):
                kid_cx = x_start + w / 2
                if kid not in x_center_map:
                    queue.append((kid, kid_cx, y_next))
                x_start += w + BLOCK_HPAD

    # 合流ノードの残り（BFS で訪問されなかった場合のフォローアップ）
    for _ in range(30):
        placed_any = False
        for step in list(block_map.keys()):
            if step in x_center_map:
                continue
            try_place_convergence(step)
            if step in x_center_map:
                placed_any = True
                # 子も配置
                non_term_kids = [k for k in children.get(step, []) if not is_terminal(k)]
                y_next = result[step][1] + block_h(step)
                cx = x_center_map[step]
                if len(non_term_kids) == 1:
                    kid = non_term_kids[0]
                    if kid not in x_center_map:
                        queue.append((kid, cx, y_next))
                elif len(non_term_kids) > 1:
                    widths = [subtree_width(k) for k in non_term_kids]
                    total_w = sum(widths) + (len(non_term_kids) - 1) * BLOCK_HPAD
                    x_start = cx - total_w / 2
                    for kid, w in zip(non_term_kids, widths):
                        if kid not in x_center_map:
                            queue.append((kid, x_start + w / 2, y_next))
                        x_start += w + BLOCK_HPAD
                # キューを処理
                while queue:
                    s2, cx2, y2 = queue.popleft()
                    if s2 not in x_center_map:
                        x_center_map[s2] = cx2
                        x_left2 = int(cx2 - block_w(s2) / 2)
                        result[s2] = (x_left2, y2)
        if not placed_any:
            break

    # ── 終話ノード配置: 主経路確定後、親の右横に並べる ───────────────
    # 各親ごとに終話子をグループ化し、親の右から順に配置
    term_right_margin = BLOCK_HPAD
    for step in list(block_map.keys()):
        if step not in x_center_map:
            continue
        term_kids = [k for k in children.get(step, []) if is_terminal(k) and k not in result]
        if not term_kids:
            continue
        parent_x, parent_y = result[step]
        parent_cx = x_center_map[step]
        parent_right = parent_x + block_w(step)
        # 終話ノードは親の右横に置くが、隣接ブロックとのY衝突を避けるため
        # 親の中段（y + block_h/2）を中心に配置
        y_term = parent_y + block_h(step) // 2

        # 親の右横から横に並べる
        cur_x = parent_right + term_right_margin
        for kid in term_kids:
            x_center_map[kid] = cur_x + block_w(kid) / 2
            result[kid] = (cur_x, y_term)
            cur_x += block_w(kid) + BLOCK_HPAD

    # ── 孤立ブロック（グラフから切り離されたもの）を右端に縦積み ────
    placed_x_values = [x for x, _ in result.values()]
    orphan_x = (max(placed_x_values) if placed_x_values else 0) + UNIT_W + BLOCK_HPAD
    orphan_y = 0
    for b in blocks:
        step = b["step"]
        if step not in result:
            result[step] = (orphan_x, orphan_y)
            x_center_map[step] = orphan_x + block_w(step) / 2
            orphan_y += block_h(step)

    # ── x 座標を正規化（最小 x が 0 になるように全体をシフト）────────
    if result:
        min_x = min(x for x, _ in result.values())
        if min_x != 0:
            result = {s: (x - min_x, y) for s, (x, y) in result.items()}

    return result


# ─── CLI エントリ（debug 用）─────────────────────────────────────
def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: block_layout.py <設計書.yaml>", file=sys.stderr)
        sys.exit(1)
    import yaml
    with open(sys.argv[1], encoding="utf-8") as f:
        spec = yaml.safe_load(f)
    blocks = extract_blocks_from_spec(spec)
    print(f"Blocks: {len(blocks)}", file=sys.stderr)
    tops = assign_block_tops(blocks)
    for b in blocks:
        pos = tops.get(b["step"], (None, None))
        print(f"  [{b['type']:10s}] {b['step']:30s} → {pos}")


if __name__ == "__main__":
    main()
