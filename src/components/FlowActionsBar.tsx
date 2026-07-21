import { useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useT } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { HoverLabelButton } from './HoverTip';
import { useSaveFlow } from './useSaveFlow';

// ─────────────────────────────────────────────────────────────────────────────
// Cụm thao tác flow (Auto Layout · Lưu flow · Export) đặt ở GÓC PHẢI dải tab —
// dùng chung cho cả màn TS lẫn CS. Trước đây nằm trong panel menu (HeaderMenu) có
// cả text + icon; nay xuống bar chỉ còn ICON, không viền/nền dạng nút, hover hiện
// tooltip hướng dẫn. Kích thước đủ lớn cho dễ bấm.
//
// Export: màn CS mở modal chọn YAML / XML Draw.io; màn TS tải YAML luôn.
// ─────────────────────────────────────────────────────────────────────────────

// Nút icon vuông, kích thước dễ bấm, không viền: icon màu cam (accent), hover hiện
// nền xám giống mục trong panel menu (bk-menu-item).
const ACTION_BTN =
  'flex h-9 w-9 items-center justify-center rounded-lg text-[var(--bk-accent)] transition hover:bg-[var(--bk-surface-2)] disabled:pointer-events-none disabled:opacity-40';

export function FlowActionsBar() {
  const ir = useFlowStore((s) => s.ir);
  const autoLayout = useFlowStore((s) => s.autoLayout);
  const exportYaml = useFlowStore((s) => s.exportYaml);
  const exportDrawio = useFlowStore((s) => s.exportDrawio);
  const canvasTab = useFlowStore((s) => s.canvasTab);
  const currentFile = useFileStore((s) => s.current);
  const csMode = useWorkspaceStore((s) => s.mode === 'cs');
  const t = useT();

  const [busy, setBusy] = useState(false);
  const { saving, saveError, canSave, saveToRepo } = useSaveFlow();

  const handleAutoLayout = async () => {
    setBusy(true);
    try {
      await autoLayout();
    } finally {
      setBusy(false);
    }
  };

  // Auto Layout thao tác trên canvas -> màn CS chỉ bật ở tab Flow Diagram.
  const autoLayoutDisabled = busy || !ir || (csMode && canvasTab !== 'flow');

  // ── Export ──
  const [showExportModal, setShowExportModal] = useState(false);

  // Tên file export = "施設名_シナリオ名"; bỏ facility nếu trống.
  const exportBaseName = () => {
    const facility = ir?.meta.facility?.trim();
    const scenario = ir?.meta.name?.trim() || 'flow';
    const base = facility ? `${facility}_${scenario}` : scenario;
    const safe = base.replace(/[/\\:*?"<>| -]/g, '').trim() || 'flow';
    return safe;
  };

  const downloadFile = (content: string, filename: string, mime: string) => {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportYaml = () => {
    downloadFile(exportYaml(), `${exportBaseName()}.yaml`, 'text/yaml;charset=utf-8');
    setShowExportModal(false);
  };

  const handleExportDrawio = () => {
    downloadFile(exportDrawio(), `${exportBaseName()}.xml`, 'application/xml;charset=utf-8');
    setShowExportModal(false);
  };

  // Màn TS: tải YAML luôn; màn CS: mở modal chọn YAML / XML Draw.io.
  const handleExport = () => {
    if (csMode) setShowExportModal(true);
    else handleExportYaml();
  };

  // Nhãn nút Lưu đổi theo trạng thái (đang lưu / bình thường).
  const saveLabel = saving ? t('fmSaving') : t('fmSaveToRepo');

  return (
    <div className="flex items-center gap-0.5">
      <HoverLabelButton
        label={busy ? t('autoLayoutBusy') : t('autoLayout')}
        className={ACTION_BTN}
        disabled={autoLayoutDisabled}
        onClick={() => void handleAutoLayout()}
      >
        <Icon
          icon={busy ? 'lucide:loader-circle' : 'tabler:layout-filled'}
          width={20}
          height={20}
          className={busy ? 'animate-spin' : ''}
        />
      </HoverLabelButton>

      {currentFile && (
        <HoverLabelButton
          label={saveLabel}
          className={`${ACTION_BTN} ${saveError && !saving ? 'text-rose-500 hover:text-rose-500' : ''}`}
          disabled={!canSave || saving}
          onClick={() => void saveToRepo()}
        >
          <Icon
            icon={saving ? 'lucide:loader-circle' : 'fluent:save-24-filled'}
            width={20}
            height={20}
            className={saving ? 'animate-spin' : ''}
          />
        </HoverLabelButton>
      )}

      <HoverLabelButton
        label={csMode ? t('csExportMenu') : t('exportYaml')}
        className={ACTION_BTN}
        disabled={!ir}
        onClick={handleExport}
      >
        <Icon icon="tabler:file-download-filled" width={20} height={20} />
      </HoverLabelButton>

      {/* Modal chọn định dạng export (màn CS): YAML cho hệ thống / XML mở bằng Draw.io. */}
      {showExportModal && (
        <div
          className="bk-modal-overlay bk-modal-overlay--fixed"
          role="dialog"
          aria-modal="true"
          onClick={() => setShowExportModal(false)}
        >
          <div className="bk-modal" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-[var(--bk-text)]">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]">
                <Icon icon="lucide:download" width={15} height={15} />
              </span>
              {t('exportModalTitle')}
            </div>
            <div className="flex flex-col gap-2">
              <button
                type="button"
                onClick={handleExportYaml}
                className="flex items-center gap-3 rounded-xl border border-[var(--bk-border)] px-3.5 py-3 text-left transition hover:border-[var(--bk-accent)] hover:bg-[var(--bk-accent-soft)]"
              >
                <Icon icon="lucide:file-code" width={20} height={20} className="shrink-0 text-[var(--bk-accent)]" />
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-[var(--bk-text)]">{t('exportOptYaml')}</span>
                  <span className="block text-[11px] text-[var(--bk-text-muted)]">{t('exportOptYamlDesc')}</span>
                </span>
              </button>
              <button
                type="button"
                onClick={handleExportDrawio}
                className="flex items-center gap-3 rounded-xl border border-[var(--bk-border)] px-3.5 py-3 text-left transition hover:border-[var(--bk-accent)] hover:bg-[var(--bk-accent-soft)]"
              >
                <Icon icon="lucide:git-fork" width={20} height={20} className="shrink-0 text-[var(--bk-accent)]" />
                <span className="min-w-0">
                  <span className="block text-sm font-semibold text-[var(--bk-text)]">{t('exportOptXml')}</span>
                  <span className="block text-[11px] text-[var(--bk-text-muted)]">{t('exportOptXmlDesc')}</span>
                </span>
              </button>
            </div>
            <div className="mt-4 flex justify-end">
              <button
                type="button"
                onClick={() => setShowExportModal(false)}
                className="rounded-lg border border-[var(--bk-border)] px-4 py-2 text-sm font-semibold text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
              >
                {t('btnCancel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
