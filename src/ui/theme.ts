import { create } from 'zustand';

// ─────────────────────────────────────────────────────────────────────────────
// Theme store (Light / Dark). Toggle .dark trên <html> để Tailwind + token CSS
// đổi màu; lưu lựa chọn vào localStorage, mặc định theo prefers-color-scheme.
// ─────────────────────────────────────────────────────────────────────────────

export type Theme = 'light' | 'dark';

const STORAGE_KEY = 'bk-theme';

function getInitialTheme(): Theme {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === 'light' || saved === 'dark') return saved;
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme: Theme) {
  document.documentElement.classList.toggle('dark', theme === 'dark');
  localStorage.setItem(STORAGE_KEY, theme);
}

interface ThemeState {
  theme: Theme;
  toggle: () => void;
  setTheme: (theme: Theme) => void;
}

export const useTheme = create<ThemeState>((set, get) => {
  const initial = getInitialTheme();
  applyTheme(initial); // áp dụng ngay khi store khởi tạo (trước lần render đầu)
  return {
    theme: initial,
    toggle: () => {
      const next: Theme = get().theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      set({ theme: next });
    },
    setTheme: (theme) => {
      applyTheme(theme);
      set({ theme });
    },
  };
});
