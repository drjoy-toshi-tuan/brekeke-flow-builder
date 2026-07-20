import { stringify } from 'yaml';
import type { FlowIR, FlowEdge } from '../types';
import { DEFAULT_BLOCK_BY_NODE_TYPE, isDesignBlockType } from './blockTypeMap';
import type { DesignYamlPassthrough } from './types';

// ─────────────────────────────────────────────────────────────────────────────
// FlowIR -> 設計書 YAML (round-trip với fromDesignYaml.ts). Hàm thuần.
//
// Nguyên tắc giống toYaml.ts: EDGES là nguồn sự thật cho next/conditions (không
// phải node.data.conditions cũ) — người dùng sửa dây trên canvas phải phản ánh
// đúng khi ghi lại. node.data.conditions (nếu còn khớp source/target) chỉ được
// dùng để khôi phục field phụ (label, field lạ trong từng nhánh cũ).
// ─────────────────────────────────────────────────────────────────────────────

interface OutCondition {
  match?: string;
  next: string;
  label?: string;
  [key: string]: unknown;
}

interface OutStep {
  step: string;
  type: string;
  next?: string;
  conditions?: OutCondition[];
  [key: string]: unknown;
}

function outgoing(edges: FlowEdge[], nodeId: string): FlowEdge[] {
  return edges.filter((e) => e.source === nodeId);
}

// Map handle -> field lạ của nhánh cũ (label, …), đọc từ node.data.conditions gốc.
function readOldConditionsByTarget(data: Record<string, unknown>): Map<string, RawConditionLike> {
  const map = new Map<string, RawConditionLike>();
  const raw = data.conditions;
  if (Array.isArray(raw)) {
    for (const c of raw as RawConditionLike[]) {
      if (c && typeof c.next === 'string') map.set(c.next, c);
    }
  }
  return map;
}

interface RawConditionLike {
  match?: string;
  next?: string;
  label?: string;
  [key: string]: unknown;
}

export function toDesignYaml(ir: FlowIR, passthrough: DesignYamlPassthrough): string {
  const scenario_flow: OutStep[] = [];

  for (const node of ir.nodes) {
    const blockType =
      typeof node.data.blockType === 'string' && isDesignBlockType(node.data.blockType)
        ? node.data.blockType
        : (DEFAULT_BLOCK_BY_NODE_TYPE[node.type] ?? 'augment');

    const out: OutStep = { step: node.id, type: blockType };
    // Trải phẳng data (output_format/save_to/slot/termination_ref/…) trở lại cấp
    // step. Bỏ blockType/conditions vì đó là dữ liệu cấu trúc, dựng lại bên dưới.
    for (const [key, value] of Object.entries(node.data)) {
      if (key === 'blockType' || key === 'conditions') continue;
      out[key] = value;
    }

    const edges = outgoing(ir.edges, node.id);
    const oldByTarget = readOldConditionsByTarget(node.data);
    const hasBranching = edges.some((e) => (e.sourceHandle ?? 'default') !== 'default') || edges.length > 1;

    if (hasBranching) {
      out.conditions = edges.map((e): OutCondition => {
        const old = oldByTarget.get(e.target);
        const match = e.condition ?? old?.match ?? (e.sourceHandle === 'default' ? 'default' : '');
        const extra = old ? Object.fromEntries(Object.entries(old).filter(([k]) => k !== 'match' && k !== 'next' && k !== 'label')) : {};
        return {
          ...extra,
          match: match || 'default',
          next: e.target,
          ...(e.label ? { label: e.label } : {}),
        };
      });
    } else if (edges[0]) {
      out.next = edges[0].target;
    }

    scenario_flow.push(out);
  }

  const doc = {
    ...passthrough,
    scenario_flow,
  };

  return stringify(doc, { lineWidth: 0 });
}
