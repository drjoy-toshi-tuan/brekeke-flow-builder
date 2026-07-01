// Chỉ tài khoản Google thuộc domain này mới vào được app (client-side gating).
// Dễ đổi ở một chỗ duy nhất.
export const ALLOWED_DOMAIN = 'drjoy.jp';

// OAuth Client ID (Web) — KHÔNG phải secret. Lấy từ Google Cloud Console.
// Nếu để trống => app chạy ở "chế độ demo" (bỏ qua đăng nhập) để test UI.
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';
