import { create } from 'zustand';

// ─────────────────────────────────────────────────────────────────────────────
// Trạng thái "file đang mở" — điều hướng giữa màn quản lý file (FileManager) và
// canvas. Có file đang mở -> vào canvas; không có -> ở màn quản lý file.
//
// `sha` giữ phiên bản blob GitHub của file đang mở để nút "Lưu về repo" cập nhật
// đúng phiên bản (tránh ghi đè nhầm). File tạo mới chưa có trên repo -> sha rỗng.
// ─────────────────────────────────────────────────────────────────────────────

export interface OpenFile {
  path: string; // flows/xxx.yaml (GitHub) hoặc "施設名/シナリオ名" (Drive — chỉ để hiển thị)
  name: string; // xxx.yaml
  sha: string | null; // sha blob hiện tại trên repo; null nếu chưa từng lưu / file Drive
  // ── Nguồn lưu trữ: 'github' (mặc định, file cũ) hoặc 'drive' ──
  storage?: 'github' | 'drive';
  driveFileId?: string; // id file version đang mở trên Drive
  driveFolderId?: string; // id folder シナリオ chứa các version (tạo version mới vào đây)
  version?: number; // số version đang mở (V{N})
}

interface FileState {
  current: OpenFile | null;
  openFile: (file: OpenFile) => void;
  closeFile: () => void; // quay lại màn quản lý file
  setSha: (sha: string) => void; // cập nhật sha sau khi lưu thành công
  setPath: (path: string, name: string) => void; // sau khi "lưu thành" file mới
}

export const useFileStore = create<FileState>((set) => ({
  current: null,
  openFile: (file) => set({ current: file }),
  closeFile: () => set({ current: null }),
  setSha: (sha) => set((s) => (s.current ? { current: { ...s.current, sha } } : s)),
  setPath: (path, name) => set((s) => (s.current ? { current: { ...s.current, path, name } } : s)),
}));
