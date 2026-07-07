import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { GoogleOAuthProvider } from '@react-oauth/google';
import { AuthContext, type AuthUser } from './context';
import { GOOGLE_CLIENT_ID } from './config';

const STORAGE_KEY = 'brekeke-flow-builder.auth';

// Session còn hợp lệ không? Nếu ID token đã hết hạn (exp) thì coi như hết phiên.
function isStillValid(user: AuthUser): boolean {
  if (user.demo) return true; // chế độ demo không có exp.
  if (typeof user.exp !== 'number') return true; // token cũ trước khi lưu exp — chấp nhận.
  return user.exp * 1000 > Date.now();
}

function loadStoredUser(): AuthUser | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const user = JSON.parse(raw) as AuthUser;
    // Token hết hạn -> bỏ, buộc đăng nhập lại.
    if (!isStillValid(user)) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return user;
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

  // Tự đăng xuất đúng thời điểm ID token hết hạn (không chờ tới lần load sau).
  useEffect(() => {
    if (!user || user.demo || typeof user.exp !== 'number') return;
    const msLeft = user.exp * 1000 - Date.now();
    if (msLeft <= 0) {
      signOut();
      return;
    }
    const timer = setTimeout(signOut, msLeft);
    return () => clearTimeout(timer);
  }, [user, signOut]);

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
