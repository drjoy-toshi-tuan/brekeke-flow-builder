import { useFlowStore } from '../store/flowStore';
import { useT } from '../ui/i18n';
import { Icon } from '../ui/icons';

// ─────────────────────────────────────────────────────────────────────────────
// Modal xác nhận khi xoá node (nút "Xoá" trên node chỉ đặt pendingDelete).
// Xoá xong vẫn Undo được (removeNode có ghi lịch sử).
// ─────────────────────────────────────────────────────────────────────────────
export function ConfirmDeleteModal() {
  const t = useT();
  const pendingDelete = useFlowStore((s) => s.pendingDelete);
  const node = useFlowStore((s) => s.ir?.nodes.find((n) => n.id === s.pendingDelete) ?? null);
  const confirmDeleteNode = useFlowStore((s) => s.confirmDeleteNode);
  const cancelDeleteNode = useFlowStore((s) => s.cancelDeleteNode);

  if (!pendingDelete) return null;

  return (
    <div className="bk-modal-overlay bk-modal-overlay--fixed" role="dialog" aria-modal="true" onClick={cancelDeleteNode}>
      <div className="bk-modal" onClick={(e) => e.stopPropagation()}>
        <div className="mb-1 flex items-center gap-2 text-sm font-bold text-[var(--bk-text)]">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[color-mix(in_srgb,#dc2626_14%,transparent)] text-[#dc2626]">
            <Icon icon="lucide:trash-2" width={15} height={15} />
          </span>
          {t('deleteNodeTitle')}
        </div>
        <p className="mb-4 text-sm leading-relaxed text-[var(--bk-text-muted)]">
          {t('confirmDeleteMessage')}
          {node ? ` (${node.label})` : ''}
        </p>
        <div className="flex justify-end gap-2">
          <button
            type="button"
            onClick={cancelDeleteNode}
            className="rounded-lg border border-[var(--bk-border)] px-4 py-2 text-sm font-semibold text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
          >
            {t('btnCancel')}
          </button>
          <button
            type="button"
            onClick={confirmDeleteNode}
            className="rounded-lg bg-[#dc2626] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95"
          >
            {t('delete')}
          </button>
        </div>
      </div>
    </div>
  );
}
