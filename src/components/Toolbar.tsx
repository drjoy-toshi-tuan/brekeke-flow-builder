import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useT } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { HeaderMenu } from './HeaderMenu';
import { FlowsPanel } from './FlowsPanel';

// Thanh công cụ trên cùng: nút Main/Sub Flow + tên flow bên trái, menu (icon) bên phải.
export function Toolbar() {
  const ir = useFlowStore((s) => s.ir);
  const activeFlowId = useFlowStore((s) => s.activeFlowId);
  const currentFile = useFileStore((s) => s.current);
  const t = useT();

  // Tiêu đề = tên flow đang mở: main flow lấy tên file flow, sub flow lấy tên sub flow.
  const activeSub =
    activeFlowId !== 'main' ? ir?.subflows?.find((s) => s.id === activeFlowId) : undefined;
  const title = activeSub?.name ?? ir?.meta.name ?? 'Brekeke Flow Builder';

  return (
    <header className="flex items-center justify-between border-b border-[var(--bk-border)] bg-[var(--bk-surface)] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <FlowsPanel />
        <div>
          <div className="flex items-center gap-1.5 text-sm font-semibold text-[var(--bk-text)]">
            <span className="max-w-[280px] truncate" title={title}>{title}</span>
            {activeSub && (
              <span className="rounded-md bg-[var(--bk-accent-soft)] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--bk-accent)]">
                {t('subFlowBadge')}
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-[var(--bk-text-faint)]">
            {currentFile && (
              <>
                <Icon icon="lucide:file-text" width={12} height={12} />
                <span className="max-w-[180px] truncate" title={currentFile.name}>
                  {currentFile.name}
                </span>
                <span>·</span>
              </>
            )}
            <span>{ir ? t('stats', { n: ir.nodes.length, e: ir.edges.length }) : '…'}</span>
          </div>
        </div>
      </div>

      <HeaderMenu />
    </header>
  );
}
