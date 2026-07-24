import { create } from 'zustand';
import type { Department } from '../drive/permissions';
import { parseHash, serializeRoute, type RouteState } from './route';

export type { WorkspaceMode, ScreenName, RouteState } from './route';

// ─────────────────────────────────────────────────────────────────────────────
// Router + chế độ làm việc theo BỘ PHẬN. Đây là NƠI DUY NHẤT đụng tới URL (hash)
// — mọi thay đổi màn hình phản chiếu vào hash và ngược lại. Parse/serialize thuần
// nằm ở ./route (test độc lập).
//
// Grammar hash (SPA, GitHub Pages):
//   #/{mode}/flow-management            màn quản lý flow/file
//   #/{mode}/file/{driveFileId}         màn thao tác 1 file (mặc định tab flow)
//   #/{mode}/file/{driveFileId}/{tab}   deep-link tới đúng tab (announce/general/…)
//   mode = cs | ts (tiền tố bộ phận). Hash cũ #/cs | #/ts vẫn đọc được (→ flow-management).
//
// DEPARTMENT LÀ BẮT BUỘC: sau đăng nhập, bộ phận của user trong access-log KHOÁ
// mode — user không nhảy mode khác được, kể cả gõ tay hash. CS và TS dùng 2 kho
// Drive KHÁC nhau nên đổi mode = huỷ file đang mở (về flow-management).
//
// File này KHÔNG import flowStore/fileStore (flowStore đã import store này — tránh
// vòng lặp). Việc đồng bộ với các store khác nằm ở component RouteSync.
// ─────────────────────────────────────────────────────────────────────────────

// pathname + hash (KHÔNG kèm location.search): URL luôn ở dạng gọn, đồng thời DỌN
// query string rác cũ. replaceState thay vì gán location.hash: không rải lịch sử
// back/forward và KHÔNG phát lại hashchange (nên write của app không tự kích lại).
function writeHash(r: RouteState) {
  history.replaceState(null, '', `${window.location.pathname}${serializeRoute(r)}`);
}

interface WorkspaceState extends RouteState {
  // Bộ phận bị KHOÁ của user (từ access-log). null = chưa biết / không gán (owner).
  locked: Department | null;
  // Đổi mode (nếu có UI/URL). Bị chặn nếu đã khoá vào bộ phận khác.
  setMode: (mode: Department) => void;
  // Suy từ access-log sau đăng nhập — KHOÁ cứng vào bộ phận này.
  applyDepartment: (department: Department) => void;
  // Điều hướng: merge route mới rồi ghi URL (tôn trọng khoá bộ phận).
  navigate: (partial: Partial<RouteState>) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set, get) => ({
  ...parseHash(window.location.hash),
  locked: null,
  setMode: (mode) => get().navigate({ mode }),
  navigate: (partial) => {
    const cur = get();
    let next: RouteState = {
      mode: partial.mode ?? cur.mode,
      screen: partial.screen ?? cur.screen,
      fileId: partial.fileId !== undefined ? partial.fileId : cur.fileId,
      tab: partial.tab !== undefined ? partial.tab : cur.tab,
    };
    // Đổi mode = đổi kho Drive -> file cũ không còn hợp lệ, về flow-management.
    if (next.mode !== cur.mode) {
      next = { mode: next.mode, screen: 'flow-management', fileId: null, tab: null };
    }
    // Đã khoá bộ phận -> không cho rời khỏi mode đã khoá.
    if (cur.locked && next.mode !== cur.locked) {
      next = { mode: cur.locked, screen: 'flow-management', fileId: null, tab: null };
    }
    writeHash(next);
    set(next);
  },
  applyDepartment: (department) => {
    const cur = get();
    // Cùng mode -> giữ nguyên route (bảo toàn deep-link cùng bộ phận). Khác mode ->
    // huỷ file đang trỏ (khác kho Drive) và về flow-management đúng bộ phận.
    const next: RouteState =
      cur.mode === department
        ? { mode: department, screen: cur.screen, fileId: cur.fileId, tab: cur.tab }
        : { mode: department, screen: 'flow-management', fileId: null, tab: null };
    writeHash(next);
    set({ ...next, locked: department });
  },
}));

// Dọn URL ngay khi nạp app: chuẩn hoá về dạng gọn (vd hash cũ `#/cs` -> `#/cs/flow-management`,
// hoặc còn `?query` rác). replaceState không phát hashchange nên an toàn.
writeHash(useWorkspaceStore.getState());

// Người dùng sửa hash trực tiếp trên URL (nguồn hashchange DUY NHẤT — write của app
// dùng replaceState nên không phát sự kiện này):
//   - Đã khoá bộ phận & mode sai -> kéo về flow-management đúng bộ phận.
//   - Còn lại -> đồng bộ route theo hash (RouteSync sẽ reconcile màn/file/tab).
window.addEventListener('hashchange', () => {
  const parsed = parseHash(window.location.hash);
  const { locked } = useWorkspaceStore.getState();
  if (locked && parsed.mode !== locked) {
    const fixed: RouteState = { mode: locked, screen: 'flow-management', fileId: null, tab: null };
    writeHash(fixed);
    useWorkspaceStore.setState(fixed);
    return;
  }
  useWorkspaceStore.setState(parsed);
});
