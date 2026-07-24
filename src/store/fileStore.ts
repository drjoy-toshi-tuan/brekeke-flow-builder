import { create } from 'zustand';

// ─────────────────────────────────────────────────────────────────────────────
// Trạng thái "file đang mở" — điều hướng giữa màn quản lý flow (Drive) và canvas.
// Có file đang mở -> vào canvas; không có -> ở màn quản lý flow.
// Flow lưu trên Google Drive theo cây 施設名/シナリオ名/<シナリオ名>_V{N}.yaml.
// ─────────────────────────────────────────────────────────────────────────────

export interface OpenFile {
  path: string; // "施設名/シナリオ名" — chỉ để hiển thị
  name: string; // <シナリオ名>_V{N}.yaml
  driveFileId: string; // id file version đang mở trên Drive
  driveFolderId: string; // id folder シナリオ chứa các version (tạo version mới vào đây)
  version: number; // số version đang mở (V{N})
}

interface FileState {
  current: OpenFile | null;
  openFile: (file: OpenFile) => void;
  closeFile: () => void; // quay lại màn quản lý flow
  // Trạng thái lưu file hiện tại — CHUNG cho mọi nơi gọi useSaveFlow (nút Lưu trên
  // dải tab + phím tắt Ctrl/⌘+Shift+S trong HeaderMenu) để bấm tắt cũng làm nút
  // hiện icon loading, không còn mỗi nơi 1 state riêng.
  saving: boolean;
  savedAt: string | null; // thời điểm lưu thành công gần nhất (yyyy-MM-dd HH:mm)
  saveError: string | null; // key i18n nếu lưu thất bại (null = không lỗi)
  setSaving: (saving: boolean) => void;
  setSavedAt: (savedAt: string | null) => void;
  setSaveError: (saveError: string | null) => void;
}

export const useFileStore = create<FileState>((set) => ({
  current: null,
  openFile: (file) => set({ current: file }),
  closeFile: () => set({ current: null }),
  saving: false,
  savedAt: null,
  saveError: null,
  setSaving: (saving) => set({ saving }),
  setSavedAt: (savedAt) => set({ savedAt }),
  setSaveError: (saveError) => set({ saveError }),
}));
