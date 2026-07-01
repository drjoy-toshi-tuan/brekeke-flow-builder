import ELK, { type ElkNode } from 'elkjs/lib/elk.bundled.js';
import type { FlowIR } from './types';

// ─────────────────────────────────────────────────────────────────────────────
// Auto-layout deterministic bằng ELK: điền lại `position` cho mọi node từ IR.
// Hướng top-down (DOWN), thuật toán 'layered' — cho ra sơ đồ dạng cây gọn gàng.
// Hàm thuần (async): nhận IR, trả IR mới với position đã tính, không đụng React.
// ─────────────────────────────────────────────────────────────────────────────

const elk = new ELK();

// Kích thước node ước lượng để ELK chừa khoảng cách hợp lý (khớp UI ~ min-w node).
const NODE_WIDTH = 220;
const NODE_HEIGHT = 76;

export async function layout(ir: FlowIR): Promise<FlowIR> {
  if (ir.nodes.length === 0) return ir;

  const graph: ElkNode = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'DOWN',
      'elk.layered.spacing.nodeNodeBetweenLayers': '80',
      'elk.spacing.nodeNode': '60',
      'elk.layered.considerModelOrder.strategy': 'NODES_AND_EDGES',
    },
    children: ir.nodes.map((n) => ({
      id: n.id,
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
    })),
    edges: ir.edges.map((e) => ({
      id: e.id,
      sources: [e.source],
      targets: [e.target],
    })),
  };

  const laidOut = await elk.layout(graph);

  const positions = new Map<string, { x: number; y: number }>();
  for (const child of laidOut.children ?? []) {
    positions.set(child.id, { x: child.x ?? 0, y: child.y ?? 0 });
  }

  return {
    ...ir,
    nodes: ir.nodes.map((n) => ({
      ...n,
      position: positions.get(n.id) ?? n.position,
    })),
  };
}
