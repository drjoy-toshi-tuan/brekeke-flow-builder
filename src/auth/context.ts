import { createContext } from 'react';

export interface AuthUser {
  name: string;
  email: string;
  picture?: string;
  hd?: string;
  // sub (subject) — định danh ổn định của tài khoản Google.
  sub?: string;
  // exp của ID token (epoch giây) — dùng để tự đăng xuất khi token hết hạn.
  exp?: number;
  // true nếu vào bằng "chế độ demo" (chưa cấu hình Google Client ID).
  demo?: boolean;
}

export interface AuthContextValue {
  user: AuthUser | null;
  authenticate: (user: AuthUser) => void;
  signOut: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
