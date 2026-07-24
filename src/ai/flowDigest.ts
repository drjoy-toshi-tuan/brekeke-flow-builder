import type { FlowIR, FlowNode, FlowEdge } from '../ir/types';

// ─────────────────────────────────────────────────────────────────────────────
// "Flow digest" — biểu diễn GỌN của flow đang mở để gửi cho AI (memory ảo).
// Thay vì nhét cả YAML dài dòng, chỉ tóm tắt: danh sách node (id · type · label ·
// nội dung chính) + danh sách dây (nguồn → đích [handle/điều kiện]). Ít token hơn
// YAML nhiều lần mà vẫn đủ để AI hiểu cấu trúc và tham chiếu node theo id.
//
// Hàm THUẦN (không React). buildFlowDigest tính lại rẻ; caller có thể memoize theo
// version IR nếu cần.
// ─────────────────────────────────────────────────────────────────────────────

const MAX_TEXT = 120; // cắt bớt announce/prompt/script dài cho gọn token

function clip(v: unknown): string {
  if (typeof v !== 'string') return '';
  const s = v.replace(/\s+/g, ' ').trim();
  return s.length > MAX_TEXT ? `${s.slice(0, MAX_TEXT)}…` : s;
}

// Nội dung "chính" của 1 node theo loại — chỉ field đáng để AI biết.
function nodeBrief(n: FlowNode): string {
  const d = n.data ?? {};
  switch (n.type) {
    case 'announce':
      return clip(d.text);
    case 'interaction':
      return clip(d.announce);
    case 'openai':
      return clip(d.prompt);
    case 'logic':
    case 'classifier':
    case 'normalization':
      return clip((d.moduleType as string) || (d.script as string) || (d.description as string));
    case 'jump':
      return typeof d.subflow === 'string' ? `→ ${d.subflow}` : '';
    case 'transfer':
      return clip(d.number || d.destination);
    default:
      return '';
  }
}

function digestGraph(nodes: FlowNode[], edges: FlowEdge[]): string {
  const lines: string[] = [];
  lines.push('NODES:');
  for (const n of nodes) {
    const brief = nodeBrief(n);
    lines.push(`- ${n.id} [${n.type}] "${n.label}"${brief ? ` :: ${brief}` : ''}`);
  }
  lines.push('EDGES:');
  if (edges.length === 0) lines.push('- (none)');
  for (const e of edges) {
    const parts: string[] = [];
    if (e.sourceHandle) parts.push(`handle=${e.sourceHandle}`);
    if (e.condition) parts.push(`cond=${clip(e.condition)}`);
    const meta = parts.length ? ` (${parts.join(', ')})` : '';
    lines.push(`- ${e.source} -> ${e.target}${meta}`);
  }
  return lines.join('\n');
}

// Digest của flow ĐANG MỞ (ir.nodes/edges = graph active). Kèm tên flow + danh sách
// tên sub flow để AI biết bối cảnh (node Jump trỏ theo tên).
export function buildFlowDigest(ir: FlowIR, activeFlowName: string): string {
  const head: string[] = [];
  head.push(`SCENARIO: ${ir.meta.name}${ir.meta.facility ? ` (facility: ${ir.meta.facility})` : ''}`);
  head.push(`OPEN FLOW: ${activeFlowName}`);
  const subNames = (ir.subflows ?? []).map((s) => s.name).filter(Boolean);
  if (subNames.length) head.push(`SUB FLOWS: ${subNames.join(', ')}`);
  return `${head.join('\n')}\n\n${digestGraph(ir.nodes, ir.edges)}`;
}
