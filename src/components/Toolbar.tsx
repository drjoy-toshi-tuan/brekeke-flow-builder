import { useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import { useAuth } from '../auth/useAuth';

// Thanh công cụ trên cùng: tên flow, nút Auto layout / Export YAML, thông tin user.
export function Toolbar() {
  const ir = useFlowStore((s) => s.ir);
  const autoLayout = useFlowStore((s) => s.autoLayout);
  const exportYaml = useFlowStore((s) => s.exportYaml);
  const { user, signOut } = useAuth();
  const [busy, setBusy] = useState(false);

  const handleAutoLayout = async () => {
    setBusy(true);
    try {
      await autoLayout();
    } finally {
      setBusy(false);
    }
  };

  const handleExport = () => {
    const yaml = exportYaml();
    const blob = new Blob([yaml], { type: 'text/yaml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${ir?.meta.id ?? 'flow'}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-2">
      <div className="flex items-center gap-3">
        <span className="text-lg">📞</span>
        <div>
          <div className="text-sm font-semibold text-slate-800">
            {ir?.meta.name ?? 'AI電話 Flow Builder'}
          </div>
          <div className="text-[11px] text-slate-400">
            {ir ? `${ir.nodes.length} nodes · ${ir.edges.length} edges` : '…'}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          onClick={handleAutoLayout}
          disabled={busy || !ir}
        >
          {busy ? 'Đang sắp xếp…' : '⤢ Auto layout'}
        </button>
        <button
          type="button"
          className="rounded-lg bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50"
          onClick={handleExport}
          disabled={!ir}
        >
          ⬇ Export YAML
        </button>

        <div className="ml-2 flex items-center gap-2 border-l border-slate-200 pl-3">
          {user?.picture && (
            <img src={user.picture} alt="" className="h-7 w-7 rounded-full" />
          )}
          <span className="max-w-[140px] truncate text-xs text-slate-500" title={user?.email}>
            {user?.name}
          </span>
          <button
            type="button"
            className="rounded-lg px-2 py-1 text-xs text-slate-400 hover:bg-slate-100 hover:text-slate-600"
            onClick={signOut}
          >
            Đăng xuất
          </button>
        </div>
      </div>
    </header>
  );
}
