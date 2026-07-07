import { create } from 'zustand';
import { verifyToken } from './api';

// ─────────────────────────────────────────────────────────────────────────────
// Lưu GitHub fine-grained token để ghi file YAML vào repo.
//
// Bảo mật: token CHỈ lưu trong sessionStorage (mất khi đóng tab) — không dùng
// localStorage để giảm rủi ro token nằm lại lâu trên máy dùng chung. Token vẫn là
// bí mật của người dùng; hãy cấp quyền tối thiểu (Contents: Read/Write đúng repo).
// ─────────────────────────────────────────────────────────────────────────────

const TOKEN_KEY = 'brekeke-flow-builder.github.token';
const LOGIN_KEY = 'brekeke-flow-builder.github.login';

function load(key: string): string | null {
  try {
    return sessionStorage.getItem(key);
  } catch {
    return null;
  }
}

interface GithubTokenState {
  token: string | null;
  login: string | null; // tên đăng nhập GitHub (hiển thị khi đã kết nối).
  connecting: boolean;
  error: string | null;
  // Xác thực token rồi lưu nếu hợp lệ. Trả true nếu kết nối thành công.
  connect: (token: string) => Promise<boolean>;
  disconnect: () => void;
  clearError: () => void;
}

export const useGithubToken = create<GithubTokenState>((set) => ({
  token: load(TOKEN_KEY),
  login: load(LOGIN_KEY),
  connecting: false,
  error: null,

  connect: async (raw) => {
    const token = raw.trim();
    if (!token) {
      set({ error: 'empty' });
      return false;
    }
    set({ connecting: true, error: null });
    try {
      const { login } = await verifyToken(token);
      try {
        sessionStorage.setItem(TOKEN_KEY, token);
        sessionStorage.setItem(LOGIN_KEY, login);
      } catch {
        // sessionStorage không khả dụng — vẫn giữ trong bộ nhớ phiên này.
      }
      set({ token, login, connecting: false, error: null });
      return true;
    } catch (e) {
      // Ánh xạ lỗi API -> mã ngắn cho UI (auth/notfound/network…).
      const code =
        typeof e === 'object' && e && 'code' in e ? String((e as { code: unknown }).code) : 'other';
      set({ connecting: false, error: code });
      return false;
    }
  },

  disconnect: () => {
    try {
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(LOGIN_KEY);
    } catch {
      // ignore
    }
    set({ token: null, login: null, error: null });
  },

  clearError: () => set({ error: null }),
}));
