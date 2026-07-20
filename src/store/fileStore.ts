import { create } from 'zustand';

// ─────────────────────────────────────────────────────────────────────────────
// Trạng thái "file đang mở" — điều hướng giữa màn quản lý flow (Drive) và canvas.
// Có file đang mở -> vào canvas; không có -> ở màn quản lý flow.
// Flow lưu trên Google Drive theo cây 施設名/シナリオ名/<シナリオ名>_V{N}.yaml.
// ─────────────────────────────────────────────────────────────────────────────

export interface DriveOpenFile {
  source: 'drive';
  path: string; // "施設名/シナリオ名" — chỉ để hiển thị
  name: string; // <シナリオ名>_V{N}.yaml
  driveFileId: string; // id file version đang mở trên Drive
  driveFolderId: string; // id folder シナリオ chứa các version (tạo version mới vào đây)
  version: number; // số version đang mở (V{N})
}

// File 設計書 YAML của pipeline (gen_flow) mở TRỰC TIẾP từ đĩa qua File System
// Access API — không đi qua Drive. `handle` null khi trình duyệt không hỗ trợ
// (Firefox/Safari): vẫn xem/sửa được trên canvas, chỉ không "Lưu" tại chỗ được
// (useSaveFlow báo canSave=false, người dùng tự export YAML rồi ghi đè thủ công).
export interface LocalDesignOpenFile {
  source: 'local-design';
  path: string; // tên thư mục cha (vd "output/scenarios/水府病院_診療") — chỉ để hiển thị
  name: string; // tên file (vd "設計書.yaml")
  handle: FileSystemFileHandle | null;
}

export type OpenFile = DriveOpenFile | LocalDesignOpenFile;

interface FileState {
  current: OpenFile | null;
  openFile: (file: OpenFile) => void;
  closeFile: () => void; // quay lại màn quản lý flow
}

export const useFileStore = create<FileState>((set) => ({
  current: null,
  openFile: (file) => set({ current: file }),
  closeFile: () => set({ current: null }),
}));
