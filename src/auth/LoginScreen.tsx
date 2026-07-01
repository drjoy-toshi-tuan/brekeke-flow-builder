import { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from './useAuth';
import { ALLOWED_DOMAIN, GOOGLE_CLIENT_ID } from './config';
import { decodeJwt } from './jwt';

// ─────────────────────────────────────────────────────────────────────────────
// Màn hình đăng nhập. Chỉ tài khoản @drjoy.jp (claim hd) và email_verified mới vào.
// Nếu chưa cấu hình GOOGLE_CLIENT_ID -> cho vào "chế độ demo" để test UI ngay.
// ─────────────────────────────────────────────────────────────────────────────

export function LoginScreen() {
  const { authenticate } = useAuth();
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex h-full items-center justify-center bg-gradient-to-br from-slate-50 to-slate-200 p-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-lg">
        <div className="mb-6 text-center">
          <div className="text-3xl">📞</div>
          <h1 className="mt-2 text-xl font-bold text-slate-800">AI電話 Flow Builder</h1>
          <p className="mt-1 text-sm text-slate-500">
            Đăng nhập bằng tài khoản <span className="font-medium">@{ALLOWED_DOMAIN}</span>
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}

        {GOOGLE_CLIENT_ID ? (
          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={(res) => {
                setError(null);
                const claims = res.credential ? decodeJwt(res.credential) : null;
                if (!claims) {
                  setError('Không đọc được thông tin đăng nhập.');
                  return;
                }
                // Gate chính: hd === domain cho phép & email đã xác minh.
                if (claims.hd !== ALLOWED_DOMAIN || claims.email_verified !== true) {
                  setError(`Chỉ tài khoản @${ALLOWED_DOMAIN} mới truy cập được.`);
                  return;
                }
                authenticate({
                  name: claims.name ?? claims.email ?? 'User',
                  email: claims.email ?? '',
                  picture: claims.picture,
                  hd: claims.hd,
                });
              }}
              onError={() => setError('Đăng nhập Google thất bại. Thử lại.')}
            />
          </div>
        ) : (
          <div className="space-y-3">
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Chưa cấu hình <code>VITE_GOOGLE_CLIENT_ID</code>. Bạn đang xem bản demo UI —
              đăng nhập Google bị tắt.
            </div>
            <button
              type="button"
              className="w-full rounded-lg bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
              onClick={() =>
                authenticate({ name: 'Demo user', email: `demo@${ALLOWED_DOMAIN}`, demo: true })
              }
            >
              Vào chế độ demo (bỏ qua đăng nhập)
            </button>
          </div>
        )}

        <p className="mt-6 text-center text-[11px] leading-relaxed text-slate-400">
          Kiểm tra domain ở client-side chỉ là cổng UX cho nội bộ test UI, không phải
          bảo mật thật. Xem cảnh báo trong README.
        </p>
      </div>
    </div>
  );
}
