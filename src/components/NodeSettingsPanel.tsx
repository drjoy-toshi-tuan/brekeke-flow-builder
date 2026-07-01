import { useFlowStore } from '../store/flowStore';

// ─────────────────────────────────────────────────────────────────────────────
// Panel setting (phase 1): sửa `label` và các field chuỗi trong `data`.
// Mở khi double-click node. Mọi thay đổi cập nhật thẳng vào IR store.
// ─────────────────────────────────────────────────────────────────────────────

export function NodeSettingsPanel() {
  const ir = useFlowStore((s) => s.ir);
  const selectedNodeId = useFlowStore((s) => s.selectedNodeId);
  const selectNode = useFlowStore((s) => s.selectNode);
  const updateNode = useFlowStore((s) => s.updateNode);

  const node = ir?.nodes.find((n) => n.id === selectedNodeId);
  if (!node) return null;

  // Chỉ cho sửa các field data có giá trị chuỗi (đủ cho phase demo).
  const editableEntries = Object.entries(node.data).filter(
    ([, v]) => typeof v === 'string',
  ) as [string, string][];

  return (
    <aside className="absolute right-0 top-0 z-10 flex h-full w-80 flex-col border-l border-slate-200 bg-white shadow-xl">
      <header className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div>
          <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            {node.type}
          </div>
          <div className="text-sm font-semibold text-slate-800">Node: {node.id}</div>
        </div>
        <button
          type="button"
          className="rounded p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          onClick={() => selectNode(null)}
          aria-label="Đóng"
        >
          ✕
        </button>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        <label className="block">
          <span className="text-xs font-medium text-slate-600">Label</span>
          <input
            className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            value={node.label}
            onChange={(e) => updateNode(node.id, { label: e.target.value })}
          />
        </label>

        {editableEntries.length === 0 ? (
          <p className="text-xs text-slate-400">Node này không có field data để sửa.</p>
        ) : (
          editableEntries.map(([key, value]) => (
            <label key={key} className="block">
              <span className="text-xs font-medium text-slate-600">{key}</span>
              <textarea
                className="mt-1 w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                rows={key === 'text' || key === 'prompt' ? 3 : 1}
                value={value}
                onChange={(e) => updateNode(node.id, { data: { [key]: e.target.value } })}
              />
            </label>
          ))
        )}
      </div>
    </aside>
  );
}
