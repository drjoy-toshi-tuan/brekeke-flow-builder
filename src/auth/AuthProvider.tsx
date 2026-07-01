import { useCallback, useMemo, useState, type ReactNode } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthContext, type AuthUser } from './context';
import { GOOGLE_CLIENT_ID } from './config';

const STORAGE_KEY = 'brekeke-flow-builder.auth';

function loadStoredUser(): AuthUser | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// AuthProvider bao toàn app. Nếu có GOOGLE_CLIENT_ID -> bọc thêm GoogleOAuthProvider
// để dùng nút đăng nhập Google. Nếu không -> vẫn chạy (chế độ demo, xem LoginScreen).
// ─────────────────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(loadStoredUser);

  const authenticate = useCallback((next: AuthUser) => {
    setUser(next);
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // sessionStorage không khả dụng — bỏ qua, giữ state trong bộ nhớ.
    }
  }, []);

  const signOut = useCallback(() => {
    setUser(null);
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {
      // ignore
    }
  }, []);

  const value = useMemo(
    () => ({ user, authenticate, signOut }),
    [user, authenticate, signOut],
  );

  const tree = <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;

  if (GOOGLE_CLIENT_ID) {
    return <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>{tree}</GoogleOAuthProvider>;
  }
  return tree;
}
