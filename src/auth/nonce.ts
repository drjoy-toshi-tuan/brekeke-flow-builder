// Nonce chống replay cho luồng đăng nhập Google (OpenID Connect).
// Sinh 1 chuỗi ngẫu nhiên trước khi hiện nút đăng nhập, gắn vào request
// (prop `nonce` của <GoogleLogin>), rồi khi nhận ID token phải kiểm tra
// claim `nonce` khớp giá trị đã sinh. Nhờ vậy một ID token cũ/bị bắt lại
// không dùng lại được cho phiên đăng nhập khác.

const NONCE_KEY = 'brekeke-flow-builder.auth.nonce';

// Sinh nonce ngẫu nhiên bằng Web Crypto (đủ mạnh cho mục đích chống replay).
export function createNonce(): string {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  const nonce = Array.from(bytes, (b) => b.toString(16).padStart(2, '0')).join('');
  try {
    sessionStorage.setItem(NONCE_KEY, nonce);
  } catch {
    // sessionStorage không khả dụng — vẫn trả nonce để dùng trong bộ nhớ.
  }
  return nonce;
}

// Lấy nonce đã lưu (để so khớp với claim trong ID token).
export function peekNonce(): string | null {
  try {
    return sessionStorage.getItem(NONCE_KEY);
  } catch {
    return null;
  }
}

// Xoá nonce sau khi đã dùng (dùng-một-lần).
export function clearNonce(): void {
  try {
    sessionStorage.removeItem(NONCE_KEY);
  } catch {
    // ignore
  }
}
