import { create } from 'zustand';

// ─────────────────────────────────────────────────────────────────────────────
// Giữ access token Google Drive (sống ~1 giờ). Lưu sessionStorage để reload
// trang trong phiên không phải xin lại; đóng tab là hết (an toàn hơn PAT GitHub
// nằm localStorage). Việc XIN token nằm ở useDriveAuth.ts (popup GIS).
// ─────────────────────────────────────────────────────────────────────────────

const KEY = 'brekeke-flow-builder.drive.token';

// Biên an toàn: coi token là hết hạn sớm 60s để không chết giữa thao tác lưu.
const EXPIRY_MARGIN_MS = 60_000;

interface Stored {
  token: string;
  expiresAt: number; // epoch ms
}

function load(): Stored | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as Stored;
    if (!data.token || data.expiresAt <= Date.now() + EXPIRY_MARGIN_MS) {
      sessionStorage.removeItem(KEY);
      return null;
    }
    return data;
  } catch {
    return null;
  }
}

interface DriveTokenState {
  token: string | null;
  expiresAt: number;
  setToken: (token: string, expiresInSec: number) => void;
  clear: () => void;
}

export const useDriveToken = create<DriveTokenState>((set) => {
  const stored = load();
  return {
    token: stored?.token ?? null,
    expiresAt: stored?.expiresAt ?? 0,

    setToken: (token, expiresInSec) => {
      const expiresAt = Date.now() + expiresInSec * 1000;
      try {
        sessionStorage.setItem(KEY, JSON.stringify({ token, expiresAt } satisfies Stored));
      } catch {
        // sessionStorage không khả dụng — vẫn giữ trong bộ nhớ.
      }
      set({ token, expiresAt });
    },

    clear: () => {
      try {
        sessionStorage.removeItem(KEY);
      } catch {
        // ignore
      }
      set({ token: null, expiresAt: 0 });
    },
  };
});

// Token còn hạn dùng được không (kèm biên an toàn) — selector thuần cho cả
// component React lẫn code ngoài React (useDriveToken.getState()).
export function validDriveToken(state: { token: string | null; expiresAt: number }): string | null {
  return state.token && state.expiresAt > Date.now() + EXPIRY_MARGIN_MS ? state.token : null;
}
