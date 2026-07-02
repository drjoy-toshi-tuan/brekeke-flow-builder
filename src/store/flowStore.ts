import { create } from 'zustand';
import type { FlowIR, FlowEdge, FlowNode, NodeType } from '../ir/types';
import { fromYaml } from '../ir/fromYaml';
import { toYaml } from '../ir/toYaml';
import { layout } from '../ir/layout';
import { NODE_CONFIG } from '../ui/nodeConfig';
import { defaultDataFor, readBranches, type DataBranch } from '../ui/nodeSchema';

// ─────────────────────────────────────────────────────────────────────────────
// Zustand store: giữ FlowIR (source of truth) + các action cập nhật IR.
// Canvas render TỪ IR (state -> view). Mọi thao tác người dùng gọi action ở đây,
// không giữ state flow riêng lẻ trong React Flow.
// ─────────────────────────────────────────────────────────────────────────────

interface FlowState {
  ir: FlowIR | null;
  selectedNodeId: string | null;
  // Đang kéo/di chuyển canvas (pan/zoom) -> ẩn thanh công cụ nổi trên node.
  isPanning: boolean;
  setPanning: (value: boolean) => void;

  // Nạp YAML -> IR -> auto-layout, rồi set vào store.
  loadYaml: (text: string) => Promise<void>;
  // Chạy lại ELK trên IR hiện tại.
  autoLayout: () => Promise<void>;
  // Xuất IR hiện tại ra chuỗi YAML (round-trip).
  exportYaml: () => string;

  // Cập nhật vị trí sau khi kéo-thả (commit vào IR).
  setNodePositions: (positions: Record<string, { x: number; y: number }>) => void;
  // Sửa label / data của 1 node (panel setting).
  updateNode: (id: string, patch: { label?: string; data?: Record<string, unknown> }) => void;

  // Thêm 1 module (node) mới vào flow tại vị trí cho trước; trả về id vừa tạo.
  addNode: (type: NodeType, position: { x: number; y: number }) => string;
  // Xoá 1 module (node) + mọi dây nối tới/từ nó.
  removeNode: (id: string) => void;

  // Nối / xoá dây.
  addEdge: (edge: FlowEdge) => void;
  removeEdge: (id: string) => void;

  // Nhánh tự do (condition/script): thêm / sửa giá trị / xoá 1 nhánh.
  addBranch: (nodeId: string) => void;
  updateBranch: (nodeId: string, branchId: string, value: string) => void;
  removeBranch: (nodeId: string, branchId: string) => void;

  // Chọn node để mở panel setting (double-click).
  selectNode: (id: string | null) => void;
}

export const useFlowStore = create<FlowState>((set, get) => ({
  ir: null,
  selectedNodeId: null,
  isPanning: false,
  setPanning: (value) => set({ isPanning: value }),

  loadYaml: async (text) => {
    const ir = fromYaml(text);
    const laidOut = await layout(ir);
    set({ ir: laidOut, selectedNodeId: null });
  },

  autoLayout: async () => {
    const { ir } = get();
    if (!ir) return;
    const laidOut = await layout(ir);
    set({ ir: laidOut });
  },

  exportYaml: () => {
    const { ir } = get();
    return ir ? toYaml(ir) : '';
  },

  setNodePositions: (positions) => {
    const { ir } = get();
    if (!ir) return;
    set({
      ir: {
        ...ir,
        nodes: ir.nodes.map((n) =>
          positions[n.id] ? { ...n, position: positions[n.id] } : n,
        ),
      },
    });
  },

  updateNode: (id, patch) => {
    const { ir } = get();
    if (!ir) return;
    set({
      ir: {
        ...ir,
        meta: { ...ir.meta, updatedAt: new Date().toISOString() },
        nodes: ir.nodes.map((n) =>
          n.id === id
            ? {
                ...n,
                label: patch.label ?? n.label,
                data: patch.data ? { ...n.data, ...patch.data } : n.data,
              }
            : n,
        ),
      },
    });
  },

  addNode: (type, position) => {
    const { ir } = get();
    if (!ir) return '';
    // Start là điểm bắt đầu duy nhất — chỉ cho phép 1 node start trong flow.
    if (type === 'start' && ir.nodes.some((n) => n.type === 'start')) return '';
    // id duy nhất theo loại: announce_1, announce_2, …
    const existing = new Set(ir.nodes.map((n) => n.id));
    let i = 1;
    let id = `${type}_${i}`;
    while (existing.has(id)) id = `${type}_${++i}`;

    const node: FlowNode = {
      id,
      type,
      label: `${NODE_CONFIG[type].typeLabel} ${i}`,
      position,
      // Tham số + nhánh mặc định theo loại node (xem nodeSchema.defaultDataFor).
      data: defaultDataFor(type),
    };
    set({
      ir: {
        ...ir,
        meta: { ...ir.meta, updatedAt: new Date().toISOString() },
        nodes: [...ir.nodes, node],
      },
      selectedNodeId: id,
    });
    return id;
  },

  removeNode: (id) => {
    const { ir, selectedNodeId } = get();
    if (!ir) return;
    set({
      ir: {
        ...ir,
        meta: { ...ir.meta, updatedAt: new Date().toISOString() },
        nodes: ir.nodes.filter((n) => n.id !== id),
        // Xoá luôn các dây nối liên quan để không còn edge "treo".
        edges: ir.edges.filter((e) => e.source !== id && e.target !== id),
      },
      selectedNodeId: selectedNodeId === id ? null : selectedNodeId,
    });
  },

  addEdge: (edge) => {
    const { ir } = get();
    if (!ir) return;
    // Tránh trùng: bỏ qua nếu đã có edge cùng source+target+handle.
    const exists = ir.edges.some(
      (e) =>
        e.source === edge.source &&
        e.target === edge.target &&
        (e.sourceHandle ?? '') === (edge.sourceHandle ?? ''),
    );
    if (exists) return;
    set({ ir: { ...ir, edges: [...ir.edges, edge] } });
  },

  removeEdge: (id) => {
    const { ir } = get();
    if (!ir) return;
    set({ ir: { ...ir, edges: ir.edges.filter((e) => e.id !== id) } });
  },

  selectNode: (id) => set({ selectedNodeId: id }),

  addBranch: (nodeId) => {
    const { ir } = get();
    if (!ir) return;
    set({
      ir: {
        ...ir,
        meta: { ...ir.meta, updatedAt: new Date().toISOString() },
        nodes: ir.nodes.map((n) => {
          if (n.id !== nodeId) return n;
          const branches = readBranches(n.data);
          // id nhánh duy nhất theo node: b<max+1> để không đụng handle/edge cũ.
          const used = new Set(branches.map((b) => b.id));
          let i = branches.length;
          let id = `b${i}`;
          while (used.has(id)) id = `b${++i}`;
          const next: DataBranch[] = [...branches, { id, value: '' }];
          return { ...n, data: { ...n.data, branches: next } };
        }),
      },
    });
  },

  updateBranch: (nodeId, branchId, value) => {
    const { ir } = get();
    if (!ir) return;
    set({
      ir: {
        ...ir,
        meta: { ...ir.meta, updatedAt: new Date().toISOString() },
        nodes: ir.nodes.map((n) => {
          if (n.id !== nodeId) return n;
          const branches = readBranches(n.data).map((b) =>
            b.id === branchId ? { ...b, value } : b,
          );
          return { ...n, data: { ...n.data, branches } };
        }),
      },
      // Đồng bộ giá trị nhánh -> condition của các edge xuất phát từ handle này
      // (để export YAML giữ đúng biểu thức when).
    });
    const cur = get().ir;
    if (!cur) return;
    set({
      ir: {
        ...cur,
        edges: cur.edges.map((e) =>
          e.source === nodeId && (e.sourceHandle ?? 'default') === branchId
            ? { ...e, condition: value || undefined, label: value || undefined }
            : e,
        ),
      },
    });
  },

  removeBranch: (nodeId, branchId) => {
    const { ir } = get();
    if (!ir) return;
    set({
      ir: {
        ...ir,
        meta: { ...ir.meta, updatedAt: new Date().toISOString() },
        nodes: ir.nodes.map((n) => {
          if (n.id !== nodeId) return n;
          // Không cho xoá nhánh đầu tiên (idx 0).
          const next = readBranches(n.data).filter(
            (b, idx) => idx === 0 || b.id !== branchId,
          );
          return { ...n, data: { ...n.data, branches: next } };
        }),
        // Xoá luôn các dây xuất phát từ handle nhánh bị xoá.
        edges: ir.edges.filter(
          (e) => !(e.source === nodeId && (e.sourceHandle ?? 'default') === branchId),
        ),
      },
    });
  },
}));
