// Decode phần payload của một JWT (ID token) — KHÔNG verify chữ ký.
// Ở phase này chỉ để đọc claim hiển thị & gating UX phía client.
// ⚠️ Không dùng cho quyết định bảo mật thật (xem README §Bảo mật).

export interface GoogleIdTokenClaims {
  email?: string;
  email_verified?: boolean;
  name?: string;
  picture?: string;
  hd?: string; // hosted domain (Google Workspace)
  [key: string]: unknown;
}

export function decodeJwt(token: string): GoogleIdTokenClaims | null {
  try {
    const payload = token.split('.')[1];
    if (!payload) return null;
    const base64 = payload.replace(/-/g, '+').replace(/_/g, '/');
    const binary = atob(base64);
    // Giải UTF-8 đúng cho ký tự nhiều byte (tên tiếng Nhật, v.v.)
    const json = decodeURIComponent(
      Array.prototype.map
        .call(binary, (c: string) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join(''),
    );
    return JSON.parse(json) as GoogleIdTokenClaims;
  } catch {
    return null;
  }
}
