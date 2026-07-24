import { NODE_TYPES, type NodeType } from '../ir/types';

// ─────────────────────────────────────────────────────────────────────────────
// Edit-ops: "tờ chỉ thị" AI trả về để sửa flow (Option 1 — human-in-the-loop).
// AI KHÔNG tự tay sửa IR; nó chỉ liệt kê các thao tác được phép ở đây, app validate
// rồi (khi người dùng bấm "Áp dụng") dispatch qua flowStore.applyAiOps.
//
// File THUẦN (không React). Tham chiếu node: dùng `id` node hiện có (lấy từ digest)
// hoặc `tempId` cho node mới tạo trong cùng lô ops (dùng lại ở addEdge).
// ─────────────────────────────────────────────────────────────────────────────

export type EditOp =
  | { op: 'addNode'; tempId?: string; nodeType: NodeType; label?: string; data?: Record<string, unknown> }
  | { op: 'updateNode'; id: string; label?: string; data?: Record<string, unknown> }
  | { op: 'removeNode'; id: string }
  | {
      op: 'addEdge';
      source: string;
      target: string;
      sourceHandle?: string;
      condition?: string;
      label?: string;
    }
  | { op: 'removeEdge'; source: string; target: string };

const NODE_TYPE_SET = new Set<string>(NODE_TYPES);

function asStr(v: unknown): string | undefined {
  return typeof v === 'string' && v.trim() ? v.trim() : undefined;
}

// Validate + coerce mảng ops thô (từ JSON của AI) -> EditOp[] an toàn. Bỏ op sai
// định dạng thay vì ném lỗi (AI có thể trả lẫn op lạ). data giữ nguyên nếu là object.
export function parseEditOps(raw: unknown): EditOp[] {
  if (!Array.isArray(raw)) return [];
  const out: EditOp[] = [];
  for (const item of raw) {
    if (!item || typeof item !== 'object') continue;
    const o = item as Record<string, unknown>;
    const kind = o.op;
    const data = o.data && typeof o.data === 'object' ? (o.data as Record<string, unknown>) : undefined;
    if (kind === 'addNode') {
      const nodeType = asStr(o.nodeType);
      if (!nodeType || !NODE_TYPE_SET.has(nodeType) || nodeType === 'start') continue;
      out.push({ op: 'addNode', tempId: asStr(o.tempId), nodeType: nodeType as NodeType, label: asStr(o.label), data });
    } else if (kind === 'updateNode') {
      const id = asStr(o.id);
      if (!id) continue;
      out.push({ op: 'updateNode', id, label: asStr(o.label), data });
    } else if (kind === 'removeNode') {
      const id = asStr(o.id);
      if (!id) continue;
      out.push({ op: 'removeNode', id });
    } else if (kind === 'addEdge') {
      const source = asStr(o.source);
      const target = asStr(o.target);
      if (!source || !target) continue;
      out.push({
        op: 'addEdge',
        source,
        target,
        sourceHandle: asStr(o.sourceHandle),
        condition: asStr(o.condition),
        label: asStr(o.label),
      });
    } else if (kind === 'removeEdge') {
      const source = asStr(o.source);
      const target = asStr(o.target);
      if (!source || !target) continue;
      out.push({ op: 'removeEdge', source, target });
    }
  }
  return out;
}

// ── Mô tả op cho thẻ "đề xuất thay đổi" (UI) ─────────────────────────────────
export type OpKind = 'add' | 'edit' | 'remove';

export interface OpDisplay {
  kind: OpKind; // -> chọn icon/màu (add=xanh/plus, edit=xanh dương/edit, remove=đỏ)
  key: string; // TKey i18n (aiOpAddNode…)
  params: Record<string, string>;
}

// labelOf: id (hoặc tempId) -> nhãn hiển thị (tên node). Với node mới, dùng label op.
export function describeOp(op: EditOp, labelOf: (ref: string) => string): OpDisplay {
  switch (op.op) {
    case 'addNode':
      return { kind: 'add', key: 'aiOpAddNode', params: { label: op.label || op.nodeType, type: op.nodeType } };
    case 'updateNode':
      return { kind: 'edit', key: 'aiOpUpdateNode', params: { label: labelOf(op.id) } };
    case 'removeNode':
      return { kind: 'remove', key: 'aiOpRemoveNode', params: { label: labelOf(op.id) } };
    case 'addEdge':
      return { kind: 'add', key: 'aiOpAddEdge', params: { from: labelOf(op.source), to: labelOf(op.target) } };
    case 'removeEdge':
      return { kind: 'remove', key: 'aiOpRemoveEdge', params: { from: labelOf(op.source), to: labelOf(op.target) } };
  }
}
