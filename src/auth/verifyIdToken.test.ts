import { describe, it, expect } from 'vitest';
import { verifyIdToken } from './verifyIdToken';
import { GOOGLE_CLIENT_ID, ALLOWED_DOMAIN } from './config';

// Dựng 1 JWT giả (chỉ phần payload có ý nghĩa — verifyIdToken không verify chữ ký).
function b64url(obj: unknown): string {
  const bytes = new TextEncoder().encode(JSON.stringify(obj));
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}
function makeToken(payload: Record<string, unknown>): string {
  return `${b64url({ alg: 'RS256' })}.${b64url(payload)}.signature`;
}

const NOW = 1_700_000_000; // mốc thời gian cố định (giây)

// Payload hợp lệ cơ bản. aud để trống nếu app không cấu hình client id.
function validPayload(over: Record<string, unknown> = {}) {
  return {
    iss: 'https://accounts.google.com',
    aud: GOOGLE_CLIENT_ID || 'test-client',
    sub: '1234567890',
    exp: NOW + 3600,
    iat: NOW - 10,
    email: `alice@${ALLOWED_DOMAIN}`,
    email_verified: true,
    hd: ALLOWED_DOMAIN,
    nonce: 'abc123',
    ...over,
  };
}

// Chỉ kiểm tra aud khi app có cấu hình GOOGLE_CLIENT_ID; nếu không, aud tuỳ ý.
const opts = { nowSeconds: NOW, expectedNonce: 'abc123' as string | null };

describe('verifyIdToken', () => {
  it('chấp nhận token hợp lệ', () => {
    const res = verifyIdToken(makeToken(validPayload()), opts);
    expect(res.ok).toBe(true);
  });

  it('từ chối token không decode được', () => {
    const res = verifyIdToken('not-a-jwt', opts);
    expect(res).toEqual({ ok: false, reason: 'unreadable' });
  });

  it('từ chối issuer sai', () => {
    const res = verifyIdToken(makeToken(validPayload({ iss: 'https://evil.example' })), opts);
    expect(res).toEqual({ ok: false, reason: 'issuer' });
  });

  it('từ chối token hết hạn', () => {
    const res = verifyIdToken(makeToken(validPayload({ exp: NOW - 3600 })), opts);
    expect(res).toEqual({ ok: false, reason: 'expired' });
  });

  it('từ chối iat ở tương lai', () => {
    const res = verifyIdToken(makeToken(validPayload({ iat: NOW + 3600 })), opts);
    expect(res).toEqual({ ok: false, reason: 'expired' });
  });

  it('từ chối nonce không khớp (nghi replay)', () => {
    const res = verifyIdToken(makeToken(validPayload({ nonce: 'other' })), opts);
    expect(res).toEqual({ ok: false, reason: 'nonce' });
  });

  it('từ chối sai hosted domain', () => {
    const res = verifyIdToken(
      makeToken(validPayload({ hd: 'gmail.com', email: 'x@gmail.com' })),
      opts,
    );
    expect(res).toEqual({ ok: false, reason: 'domain' });
  });

  it('từ chối email chưa xác minh', () => {
    const res = verifyIdToken(makeToken(validPayload({ email_verified: false })), opts);
    expect(res).toEqual({ ok: false, reason: 'domain' });
  });

  it('từ chối khi hd đúng nhưng đuôi email khác domain', () => {
    const res = verifyIdToken(makeToken(validPayload({ email: `bob@evil.com` })), opts);
    expect(res).toEqual({ ok: false, reason: 'domain' });
  });

  it('từ chối khi thiếu sub', () => {
    const p = validPayload();
    delete (p as Record<string, unknown>).sub;
    const res = verifyIdToken(makeToken(p), opts);
    expect(res).toEqual({ ok: false, reason: 'subject' });
  });

  it('bỏ qua kiểm tra nonce nếu không truyền expectedNonce', () => {
    const res = verifyIdToken(makeToken(validPayload({ nonce: 'whatever' })), { nowSeconds: NOW });
    expect(res.ok).toBe(true);
  });
});
