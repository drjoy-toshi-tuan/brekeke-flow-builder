import { useEffect, useRef } from 'react';
import { useReactFlow, useStore, useStoreApi } from '@xyflow/react';
import { useFlowStore } from '../store/flowStore';
import { useT } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { HoverLabelButton } from '../components/HoverTip';

// ─────────────────────────────────────────────────────────────────────────────
// Thanh công cụ canvas (thay <Controls> mặc định của React Flow):
//   - 1 nút toggle (icon fluent:column-triple-20-filled) — bấm để TRƯỢT NGANG mở
//     dãy nút zoom / fit / lock / undo / redo (thay vì thanh dọc cũ).
//   - Mở/đóng qua store.canvasPanel === 'controls' nên TỰ loại trừ với panel
//     "Thêm node" / "Main-Sub Flow" (mở cái này thì cái kia đóng).
// Hover mỗi nút hiện tooltip (VI/JA theo ngôn ngữ hiện tại) qua HoverLabelButton.
// ─────────────────────────────────────────────────────────────────────────────

const BTN_CLASS =
  'flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface)] text-[var(--bk-text-muted)] shadow-[var(--bk-shadow)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--bk-accent)] hover:text-[var(--bk-accent)] hover:shadow-md active:translate-y-0 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:translate-y-0 disabled:hover:border-[var(--bk-border)] disabled:hover:text-[var(--bk-text-muted)] disabled:hover:shadow-[var(--bk-shadow)]';

export function CanvasControls() {
  // Mở/đóng qua store để loại trừ với các panel canvas khác (spec chung).
  const canvasPanel = useFlowStore((s) => s.canvasPanel);
  const setCanvasPanel = useFlowStore((s) => s.setCanvasPanel);
  const open = canvasPanel === 'controls';
  const setOpen = (v: boolean) => setCanvasPanel(v ? 'controls' : null);

  const undo = useFlowStore((s) => s.undo);
  const redo = useFlowStore((s) => s.redo);
  const canUndo = useFlowStore((s) => s.past.length > 0);
  const canRedo = useFlowStore((s) => s.future.length > 0);

  const { zoomIn, zoomOut, fitView } = useReactFlow();
  const store = useStoreApi();
  // Khoá tương tác = nodesDraggable && nodesConnectable && elementsSelectable (đồng
  // bộ với phím tắt Ctrl/⌘+Shift+L trong FlowCanvas). "Đang mở khoá" khi cả 3 bật.
  const interactive = useStore(
    (s) => s.nodesDraggable && s.nodesConnectable && s.elementsSelectable,
  );
  const toggleInteractivity = () => {
    const next = !interactive;
    store.setState({
      nodesDraggable: next,
      nodesConnectable: next,
      elementsSelectable: next,
    });
  };

  const t = useT();

  const wrapRef = useRef<HTMLDivElement>(null);
  // Click ra ngoài -> tự đóng (giống AddModulePanel/FlowsPanel). Đọc state mới nhất
  // để nút panel khác đổi canvasPanel ngay tại mousedown không bị ghi đè về null.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (useFlowStore.getState().canvasPanel !== 'controls') return;
      if (wrapRef.current && !e.composedPath().includes(wrapRef.current)) setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
    // setOpen ổn định (từ store) — không cần vào deps.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <div ref={wrapRef} className="bk-canvas-controls">
      <button
        type="button"
        // Toggle tại mousedown (tránh mất click khi panel khác đóng cùng lúc làm
        // React thay SVG dưới con trỏ); onClick giữ cho bàn phím (detail === 0).
        onMouseDown={() => setOpen(!open)}
        onClick={(e) => {
          if (e.detail === 0) setOpen(!open);
        }}
        className={`${BTN_CLASS} ${open ? 'border-[var(--bk-accent)] text-[var(--bk-accent)]' : ''}`}
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={t('ctrlTools')}
        title={t('ctrlTools')}
      >
        <Icon icon="fluent:column-triple-20-filled" width={17} height={17} />
      </button>

      {/* Dãy nút LUÔN mounted (inert khi đóng nhờ pointer-events) để trượt được cả 2 chiều. */}
      <div
        role="menu"
        aria-hidden={!open}
        className={`bk-canvas-controls-tray ${open ? 'bk-canvas-controls-tray--open' : ''}`}
      >
        <HoverLabelButton label={t('ctrlZoomIn')} className={BTN_CLASS} placement="top" onClick={() => void zoomIn({ duration: 200 })}>
          <Icon icon="fluent:zoom-in-20-filled" width={17} height={17} />
        </HoverLabelButton>
        <HoverLabelButton label={t('ctrlZoomOut')} className={BTN_CLASS} placement="top" onClick={() => void zoomOut({ duration: 200 })}>
          <Icon icon="fluent:zoom-out-20-filled" width={17} height={17} />
        </HoverLabelButton>
        <HoverLabelButton label={t('ctrlFitView')} className={BTN_CLASS} placement="top" onClick={() => void fitView({ padding: 0.2, duration: 250 })}>
          <Icon icon="fluent:arrow-fit-20-filled" width={17} height={17} />
        </HoverLabelButton>
        <HoverLabelButton
          label={interactive ? t('ctrlLock') : t('ctrlUnlock')}
          className={BTN_CLASS}
          placement="top"
          onClick={toggleInteractivity}
        >
          <Icon
            icon={interactive ? 'fluent:lock-open-20-filled' : 'fluent:lock-closed-20-filled'}
            width={17}
            height={17}
          />
        </HoverLabelButton>
        <HoverLabelButton label={t('undo')} className={BTN_CLASS} placement="top" disabled={!canUndo} onClick={() => undo()}>
          <Icon icon="fa7-solid:undo-alt" width={14} height={14} />
        </HoverLabelButton>
        <HoverLabelButton label={t('redo')} className={BTN_CLASS} placement="top" disabled={!canRedo} onClick={() => redo()}>
          <Icon icon="fa7-solid:redo-alt" width={14} height={14} />
        </HoverLabelButton>
      </div>
    </div>
  );
}
