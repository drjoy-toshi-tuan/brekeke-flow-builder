// Chỉ tài khoản Google thuộc domain này mới vào được app (client-side gating).
// Dễ đổi ở một chỗ duy nhất.
export const ALLOWED_DOMAIN = 'drjoy.jp';

// OAuth Client ID (Web) — KHÔNG phải secret. Lấy từ Google Cloud Console.
// Nếu để trống => app chạy ở "chế độ demo" (bỏ qua đăng nhập) để test UI.
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? '';

// Issuer hợp lệ của ID token do Google phát hành. Phải khớp claim `iss`.
export const ALLOWED_ISSUERS = ['accounts.google.com', 'https://accounts.google.com'] as const;

// Độ lệch đồng hồ cho phép (giây) khi kiểm tra exp/iat — tránh loại nhầm token
// hợp lệ do lệch giờ nhẹ giữa client và Google.
export const CLOCK_SKEW_SECONDS = 60;
