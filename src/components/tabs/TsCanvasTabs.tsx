import { useFlowStore } from '../../store/flowStore';
import { useT } from '../../ui/i18n';
import { Icon } from '../../ui/icons';
import { FlowGlyph } from '../../ui/FlowGlyph';
import { FlowsPanel } from '../FlowsPanel';
import { FlowActionsBar } from '../FlowActionsBar';

// ─────────────────────────────────────────────────────────────────────────────
// Dải tab màn TS (kiểu tab browser, giống màn CS). Tạm thời chỉ 1 tab
// "Flow Designer". Bên phải tab:
//   • Logo Main/Sub Flow — cho biết đang sửa graph nào.
//   • Nút mở panel flow settings (FlowsPanel: Main/Sub Flow + IVR Property).
// Góc phải ngoài cùng: cụm thao tác flow (Auto Layout · Lưu · Export).
// ─────────────────────────────────────────────────────────────────────────────

export function TsCanvasTabs() {
  const t = useT();
  const activeFlowId = useFlowStore((s) => s.activeFlowId);
  const isMain = activeFlowId === 'main';

  return (
    <div className="flex items-end gap-1 border-b border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 pt-1.5">
      {/* Tab Flow Designer — luôn active (chưa có tab thứ 2). */}
      <div className="-mb-px flex items-center rounded-t-lg border border-b-0 border-[var(--bk-border)] bg-[var(--bk-canvas)] text-[12.5px] font-semibold text-[var(--bk-accent)]">
        <span className="flex items-center gap-2 py-2 pl-4 pr-4" aria-current="page">
          <Icon icon="lucide:git-fork" width={14} height={14} />
          <span>{t('tabFlowDesigner')}</span>
        </span>
      </div>

      {/* Logo main/sub flow + nút mở panel flow settings — ngang hàng với tab. */}
      <div className="mb-1 flex items-center gap-1.5 self-end pl-1">
        <FlowGlyph isMain={isMain} size={18} />
        <FlowsPanel />
      </div>

      {/* Cụm thao tác flow, góc phải ngoài cùng. */}
      <div className="mb-1 ml-auto self-end">
        <FlowActionsBar />
      </div>
    </div>
  );
}
