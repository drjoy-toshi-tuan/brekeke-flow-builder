import { useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import { useAuth } from '../auth/useAuth';
import { useTheme } from '../ui/theme';
import { Icon } from '../ui/icons';

// Thanh công cụ trên cùng: tên flow, nút Auto layout / Export YAML, toggle theme, user.
export function Toolbar() {
  const ir = useFlowStore((s) => s.ir);
  const autoLayout = useFlowStore((s) => s.autoLayout);
  const exportYaml = useFlowStore((s) => s.exportYaml);
  const { user, signOut } = useAuth();
  const { theme, toggle } = useTheme();
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
    <header className="flex items-center justify-between border-b border-[var(--bk-border)] bg-[var(--bk-surface)] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--bk-accent-soft)] text-lg text-[var(--bk-accent)]">
          <Icon icon="lucide:phone" />
        </span>
        <div>
          <div className="text-sm font-semibold text-[var(--bk-text)]">
            {ir?.meta.name ?? 'AI電話 Flow Builder'}
          </div>
          <div className="text-[11px] text-[var(--bk-text-faint)]">
            {ir ? `${ir.nodes.length} nodes · ${ir.edges.length} edges` : '…'}
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          className="flex items-center gap-1.5 rounded-lg border border-[var(--bk-border)] px-3 py-1.5 text-sm font-medium text-[var(--bk-text)] transition hover:border-[var(--bk-accent)] hover:text-[var(--bk-accent)] disabled:opacity-50"
          onClick={handleAutoLayout}
          disabled={busy || !ir}
        >
          <Icon icon="lucide:layout-dashboard" width={16} height={16} />
          {busy ? 'Đang sắp xếp…' : 'Auto layout'}
        </button>
        <button
          type="button"
          className="flex items-center gap-1.5 rounded-lg bg-[var(--bk-accent)] px-3 py-1.5 text-sm font-semibold text-white shadow-sm transition hover:opacity-90 disabled:opacity-50"
          onClick={handleExport}
          disabled={!ir}
        >
          <Icon icon="lucide:download" width={16} height={16} />
          Export YAML
        </button>

        <button
          type="button"
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--bk-border)] text-[var(--bk-text-muted)] transition hover:border-[var(--bk-accent)] hover:text-[var(--bk-accent)]"
          onClick={toggle}
          title={theme === 'dark' ? 'Chuyển sang Light mode' : 'Chuyển sang Dark mode'}
          aria-label="Đổi chế độ sáng/tối"
        >
          <Icon icon={theme === 'dark' ? 'lucide:sun' : 'lucide:moon'} width={17} height={17} />
        </button>

        <div className="ml-1 flex items-center gap-2 border-l border-[var(--bk-border)] pl-3">
          {user?.picture && <img src={user.picture} alt="" className="h-7 w-7 rounded-full" />}
          <span
            className="max-w-[140px] truncate text-xs text-[var(--bk-text-muted)]"
            title={user?.email}
          >
            {user?.name}
          </span>
          <button
            type="button"
            className="flex items-center gap-1 rounded-lg px-2 py-1 text-xs text-[var(--bk-text-faint)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
            onClick={signOut}
          >
            <Icon icon="lucide:log-out" width={14} height={14} />
            Đăng xuất
          </button>
        </div>
      </div>
    </header>
  );
}
