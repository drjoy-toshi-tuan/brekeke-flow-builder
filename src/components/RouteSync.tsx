import { useEffect } from 'react';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useFileStore } from '../store/fileStore';
import { useFlowStore, normalizeCanvasTab } from '../store/flowStore';

// ─────────────────────────────────────────────────────────────────────────────
// Đồng bộ URL ↔ trạng thái app (một chiều URL→app, phần app→URL do các điểm hành
// động tự gọi navigate()). Chỉ xử lý ĐÓNG/CHUYỂN file + tab; việc MỞ file theo id
// (deep-link) cần token + cây Drive nên nằm ở DriveManagerScreen.
//
// Không có standing effect app→URL cho file để tránh đua với trạng thái "đang mở
// dở" (route trỏ file nhưng fileStore chưa kịp set). Các write của app dùng
// replaceState nên KHÔNG phát hashchange -> reconciler dưới đây chỉ chạy thật sự
// khi user sửa hash tay (hoặc deep-link lúc nạp).
// ─────────────────────────────────────────────────────────────────────────────
export function RouteSync() {
  const screen = useWorkspaceStore((s) => s.screen);
  const fileId = useWorkspaceStore((s) => s.fileId);
  const tab = useWorkspaceStore((s) => s.tab);
  const mode = useWorkspaceStore((s) => s.mode);
  const currentFile = useFileStore((s) => s.current);
  const closeFile = useFileStore((s) => s.closeFile);
  const canvasTab = useFlowStore((s) => s.canvasTab);
  const setCanvasTab = useFlowStore((s) => s.setCanvasTab);

  // URL -> đóng/chuyển file khi route lệch với file đang mở. Chuyển file khác =
  // đóng file hiện tại; DriveManagerScreen (hiện lại khi không còn file) sẽ mở id mới.
  useEffect(() => {
    if (!currentFile) return;
    if (screen === 'flow-management') {
      closeFile();
      return;
    }
    if (screen === 'file' && fileId && fileId !== currentFile.driveFileId) {
      closeFile();
    }
  }, [screen, fileId, currentFile, closeFile]);

  // app -> URL: đổi tab canvas thì cập nhật segment tab (chỉ CS mới có tab). Đọc
  // route qua getState (không để trong deps) để không thành vòng với effect dưới.
  useEffect(() => {
    if (!currentFile || mode !== 'cs') return;
    const want = canvasTab === 'flow' ? null : canvasTab;
    if (useWorkspaceStore.getState().tab !== want) {
      useWorkspaceStore.getState().navigate({ tab: want });
    }
  }, [canvasTab, currentFile, mode]);

  // URL -> tab: sửa hash tab tay thì đổi canvas. Đọc canvasTab qua getState (không
  // để trong deps) để không đua với effect app->URL ở trên.
  useEffect(() => {
    if (!currentFile || mode !== 'cs') return;
    const desired = normalizeCanvasTab(tab);
    if (desired !== useFlowStore.getState().canvasTab) setCanvasTab(desired);
  }, [tab, currentFile, mode, setCanvasTab]);

  return null;
}
