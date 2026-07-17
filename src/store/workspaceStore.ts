import { create } from 'zustand';
import type { Department } from '../drive/permissions';

// ─────────────────────────────────────────────────────────────────────────────
// Chế độ làm việc theo BỘ PHẬN — quyết định biến thể UI của canvas:
//   ts: màn kỹ thuật đầy đủ (mặc định, giữ nguyên UI hiện tại)
//   cs: màn thiết kế diagram tối giản (node lùn, palette 4 loại node…)
// Đồng bộ với hash URL (#/cs | #/ts) để chia sẻ link/refresh giữ đúng màn:
//   - Hash có sẵn trên URL khi mở app -> hash thắng.
//   - Không có hash -> suy từ department trong access-log (applyDepartment).
// ─────────────────────────────────────────────────────────────────────────────

export type WorkspaceMode = Department; // 'cs' | 'ts'

function modeFromHash(): WorkspaceMode | null {
  const h = window.location.hash.replace(/^#\/?/, '').toLowerCase();
  return h === 'cs' || h === 'ts' ? h : null;
}

function writeHash(mode: WorkspaceMode) {
  // replaceState thay vì gán location.hash: không rải lịch sử back/forward.
  history.replaceState(null, '', `#/${mode}`);
}

interface WorkspaceState {
  mode: WorkspaceMode;
  // Người dùng (hoặc URL) đã chỉ định rõ -> đừng ghi đè theo department nữa.
  explicit: boolean;
  // Đổi màn chủ động (menu / gõ URL) — ghi hash + khoá không cho department đè.
  setMode: (mode: WorkspaceMode) => void;
  // Suy từ access-log sau đăng nhập — chỉ áp khi chưa có lựa chọn rõ ràng.
  applyDepartment: (department: Department) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  mode: modeFromHash() ?? 'ts',
  explicit: modeFromHash() !== null,
  setMode: (mode) => {
    writeHash(mode);
    set({ mode, explicit: true });
  },
  applyDepartment: (department) => {
    if (get().explicit) return;
    writeHash(department);
    set({ mode: department });
  },
}));

// Người dùng sửa hash trực tiếp trên URL -> đồng bộ lại store.
window.addEventListener('hashchange', () => {
  const mode = modeFromHash();
  if (mode && mode !== useWorkspaceStore.getState().mode) {
    useWorkspaceStore.setState({ mode, explicit: true });
  }
});
