import type { Edge, Node } from '@xyflow/react';
import type { FlowIR, FlowNode, NodeType } from '../ir/types';

// ─────────────────────────────────────────────────────────────────────────────
// Adapter 2 chiều giữa IR và React Flow. 2 hàm thuần, KHÔNG chứa logic UI.
//   irToReactFlow(ir)                  -> { nodes, edges } để render
//   reactFlowToIr(nodes, edges, prev)  -> FlowIR (dựng lại IR từ trạng thái canvas)
// ─────────────────────────────────────────────────────────────────────────────

// Dữ liệu gắn vào mỗi React Flow node (để component node đọc).
export interface RFNodeData {
  label: string;
  nodeType: NodeType;
  nodeData: Record<string, unknown>;
  [key: string]: unknown; // React Flow yêu cầu data thoả Record<string, unknown>
}

// Dữ liệu gắn vào mỗi React Flow edge.
export interface RFEdgeData {
  condition?: string;
  [key: string]: unknown;
}

export function irToReactFlow(ir: FlowIR): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = ir.nodes.map((n) => ({
    id: n.id,
    type: n.type, // khớp key trong nodeTypes map
    position: n.position,
    data: {
      label: n.label,
      nodeType: n.type,
      nodeData: n.data,
    } satisfies RFNodeData,
  }));

  const edges: Edge[] = ir.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    // Không truyền sourceHandle xuống React Flow: các node dùng 1 handle output
    // duy nhất, nhánh được thể hiện bằng label trên dây (đủ cho phase demo UI).
    type: 'deletable',
    label: e.label ?? e.condition,
    data: { condition: e.condition } satisfies RFEdgeData,
  }));

  return { nodes, edges };
}

export function reactFlowToIr(nodes: Node[], edges: Edge[], prev: FlowIR): FlowIR {
  const prevById = new Map(prev.nodes.map((n) => [n.id, n]));

  const irNodes: FlowNode[] = nodes.map((rf) => {
    const base = prevById.get(rf.id);
    const data = rf.data as Partial<RFNodeData> | undefined;
    return {
      id: rf.id,
      type: (base?.type ?? data?.nodeType ?? 'announce') as NodeType,
      label: data?.label ?? base?.label ?? rf.id,
      position: rf.position,
      data: data?.nodeData ?? base?.data ?? {},
    };
  });

  const irEdges = edges.map((e) => {
    const data = e.data as RFEdgeData | undefined;
    return {
      id: e.id,
      source: e.source,
      target: e.target,
      sourceHandle: e.sourceHandle ?? undefined,
      condition: data?.condition,
      label: typeof e.label === 'string' ? e.label : undefined,
    };
  });

  return {
    ...prev,
    nodes: irNodes,
    edges: irEdges,
    meta: { ...prev.meta, updatedAt: new Date().toISOString() },
  };
}
