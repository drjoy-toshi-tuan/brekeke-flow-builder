// ─────────────────────────────────────────────────────────────────────────────
// Kiểm tra "kỹ" các claim của ID token Google ở phía client (defense-in-depth).
//
// ⚠️ Đây KHÔNG phải verify chữ ký bằng khoá công khai của Google. Việc xác thực
// thật (chống giả mạo token hoàn toàn) BẮT BUỘC làm ở server-side (xem README
// §Bảo mật). Hàm này siết các điều kiện mà một client trung thực nên yêu cầu:
//   - iss ∈ ALLOWED_ISSUERS
//   - aud === GOOGLE_CLIENT_ID (token phát cho đúng app này)
//   - exp còn hạn, iat/nbf không ở tương lai (có clock-skew)
//   - hd === ALLOWED_DOMAIN VÀ email kết thúc bằng @ALLOWED_DOMAIN
//   - email_verified === true
//   - nonce khớp nonce đã sinh (chống replay)
//   - có sub (subject) — định danh người dùng
//
// Mục tiêu: chặn các kiểu bypass "rẻ" (đổi tài khoản Gmail thường, dùng lại token
// cấp cho app khác, phát lại token cũ) ngay ở client, đồng thời tách bạch để khi
// có backend chỉ cần gọi thêm 1 bước verify chữ ký, không phải sửa UI.
// ─────────────────────────────────────────────────────────────────────────────

import { decodeJwt, type GoogleIdTokenClaims } from './jwt';
import {
  ALLOWED_DOMAIN,
  ALLOWED_ISSUERS,
  CLOCK_SKEW_SECONDS,
  GOOGLE_CLIENT_ID,
} from './config';

// Lý do thất bại — ánh xạ sang key i18n để hiện thông báo phù hợp.
export type VerifyFailReason =
  | 'unreadable' // không decode được token
  | 'issuer' // iss sai
  | 'audience' // aud không khớp client id
  | 'expired' // token hết hạn / chưa hiệu lực
  | 'nonce' // nonce không khớp (nghi replay)
  | 'domain' // sai domain / email chưa xác minh
  | 'subject'; // thiếu sub

export type VerifyResult =
  | { ok: true; claims: GoogleIdTokenClaims }
  | { ok: false; reason: VerifyFailReason };

interface VerifyOptions {
  // nonce đã sinh trước khi đăng nhập (nếu có) — bắt buộc khớp nếu được truyền.
  expectedNonce?: string | null;
  // Cho phép ép thời điểm hiện tại (giây) khi test. Mặc định = now.
  nowSeconds?: number;
}

function isString(v: unknown): v is string {
  return typeof v === 'string' && v.length > 0;
}

export function verifyIdToken(token: string, options: VerifyOptions = {}): VerifyResult {
  const claims = decodeJwt(token);
  if (!claims) return { ok: false, reason: 'unreadable' };

  const now = options.nowSeconds ?? Math.floor(Date.now() / 1000);

  // iss — phải là Google.
  if (!isString(claims.iss) || !ALLOWED_ISSUERS.includes(claims.iss as never)) {
    return { ok: false, reason: 'issuer' };
  }

  // aud — token phải được phát cho đúng client id của app (nếu app có cấu hình).
  // aud có thể là string hoặc string[] theo chuẩn JWT.
  if (GOOGLE_CLIENT_ID) {
    const aud = claims.aud;
    const audOk = Array.isArray(aud)
      ? aud.includes(GOOGLE_CLIENT_ID)
      : aud === GOOGLE_CLIENT_ID;
    if (!audOk) return { ok: false, reason: 'audience' };
  }

  // exp / iat / nbf — kiểm tra thời hạn với clock-skew.
  if (typeof claims.exp !== 'number' || claims.exp + CLOCK_SKEW_SECONDS < now) {
    return { ok: false, reason: 'expired' };
  }
  if (typeof claims.iat === 'number' && claims.iat - CLOCK_SKEW_SECONDS > now) {
    return { ok: false, reason: 'expired' };
  }
  if (typeof claims.nbf === 'number' && claims.nbf - CLOCK_SKEW_SECONDS > now) {
    return { ok: false, reason: 'expired' };
  }

  // nonce — chống replay. Nếu app có sinh nonce thì token phải mang đúng nonce đó.
  if (isString(options.expectedNonce)) {
    if (claims.nonce !== options.expectedNonce) {
      return { ok: false, reason: 'nonce' };
    }
  }

  // Domain gating: vừa khớp hd (hosted domain Workspace) vừa khớp đuôi email,
  // và email đã được Google xác minh.
  const email = isString(claims.email) ? claims.email.toLowerCase() : '';
  const emailDomainOk = email.endsWith(`@${ALLOWED_DOMAIN.toLowerCase()}`);
  if (claims.hd !== ALLOWED_DOMAIN || !emailDomainOk || claims.email_verified !== true) {
    return { ok: false, reason: 'domain' };
  }

  // sub — định danh ổn định của người dùng.
  if (!isString(claims.sub)) return { ok: false, reason: 'subject' };

  return { ok: true, claims };
}

// Ánh xạ lý do -> key i18n (định nghĩa trong ui/i18n.ts).
export function reasonToMessageKey(reason: VerifyFailReason): string {
  switch (reason) {
    case 'domain':
      return 'loginDomainError';
    case 'nonce':
      return 'loginNonceError';
    case 'expired':
      return 'loginExpiredError';
    case 'audience':
    case 'issuer':
    case 'subject':
    case 'unreadable':
    default:
      return 'loginReadError';
  }
}
