import { useFlowStore } from '../store/flowStore';
import { BrekekeLogo } from '../ui/BrekekeLogo';
import { WorkspaceStamp } from '../ui/WorkspaceStamp';
import { HeaderMenu } from './HeaderMenu';

// Thanh công cụ trên cùng: logo app + tên bệnh viện / scenario bên trái, stamp bộ
// phận + menu cài đặt bên phải. Dùng CHUNG cho cả màn CS lẫn TS — thao tác flow
// (Main/Sub Flow, Auto Layout, Lưu, Export) đã chuyển xuống dải tab dưới header.
export function Toolbar() {
  const ir = useFlowStore((s) => s.ir);

  const flowName = ir?.meta.name ?? 'Scenario Flow Builder';
  const facility = ir?.meta.facility ?? '';

  return (
    <header className="flex items-center justify-between border-b border-[var(--bk-border)] bg-[var(--bk-surface)] px-4 py-2.5">
      <div className="flex items-center gap-3">
        <BrekekeLogo className="h-9 w-9 shrink-0" />
        <div>
          {/* Trên: 施設名 (thiếu thì hiện luôn tên scenario); dưới: tên scenario. */}
          <div
            className="max-w-[420px] truncate text-base font-bold text-[var(--bk-text)]"
            title={facility || flowName}
          >
            {facility || flowName}
          </div>
          {facility && (
            <div className="mt-0.5 max-w-[420px] truncate text-[11px] text-[var(--bk-text-muted)]" title={flowName}>
              {flowName}
            </div>
          )}
        </div>
      </div>
      <div className="flex items-center gap-3">
        <WorkspaceStamp />
        <HeaderMenu />
      </div>
    </header>
  );
}
