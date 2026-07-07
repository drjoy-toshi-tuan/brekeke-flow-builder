import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useT } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { HeaderMenu } from './HeaderMenu';

// Thanh công cụ trên cùng: tên flow bên trái, menu (icon) gom mọi chức năng bên phải.
export function Toolbar() {
  const ir = useFlowStore((s) => s.ir);
  const currentFile = useFileStore((s) => s.current);
  const t = useT();

  return (
    <header className="flex items-center justify-between border-b border-[var(--bk-border)] bg-[var(--bk-surface)] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--bk-accent-soft)] text-lg text-[var(--bk-accent)]">
          <Icon icon="hugeicons:workflow-square-10" />
        </span>
        <div>
          <div className="text-sm font-semibold text-[var(--bk-text)]">
            {ir?.meta.name ?? 'Brekeke Flow Builder'}
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
