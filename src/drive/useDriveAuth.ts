import { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuth } from '../auth/useAuth';
import { useDriveToken, validDriveToken } from './token';
import { DRIVE_SCOPE, DRIVE_ROOT_FOLDER_ID } from './config';
import { verifyDriveAccess } from './api';

// ─────────────────────────────────────────────────────────────────────────────
// Xin access token Google Drive bằng GIS token flow (implicit) — KHÔNG có client
// secret, hợp static site. Popup consent chỉ hiện LẦN ĐẦU mỗi tài khoản; các lần
// sau (token hết hạn ~1h) popup tự đóng ngay không cần bấm gì vì Google đã nhớ
// quyền. `hint` trỏ đúng tài khoản đang đăng nhập app để không phải chọn lại.
//
// LƯU Ý: requestAccess phải được gọi từ user gesture (click) để popup không bị
// trình duyệt chặn — vì vậy màn quản lý hiện panel "Kết nối Google Drive" với 1
// nút bấm thay vì tự bật popup lúc mount.
// ─────────────────────────────────────────────────────────────────────────────

export function useDriveAuth() {
  const { user } = useAuth();
  const store = useDriveToken();
  const [connecting, setConnecting] = useState(false);
  // Mã lỗi ngắn ('auth' | 'popup' | 'other'…) — UI ánh xạ i18n qua gdErrorKey.
  const [error, setError] = useState<string | null>(null);

  const login = useGoogleLogin({
    flow: 'implicit',
    scope: DRIVE_SCOPE,
    hint: user?.email,
    onSuccess: (res) => {
      void (async () => {
        try {
          // Xác nhận token với tới folder gốc (bắt sớm lỗi chưa được share).
          await verifyDriveAccess(res.access_token, DRIVE_ROOT_FOLDER_ID);
          store.setToken(res.access_token, res.expires_in);
          setError(null);
        } catch (e) {
          setError(e instanceof Error && 'code' in e ? String((e as { code: unknown }).code) : 'other');
        } finally {
          setConnecting(false);
        }
      })();
    },
    onError: () => {
      setConnecting(false);
      setError('auth');
    },
    onNonOAuthError: () => {
      // Popup bị chặn / người dùng đóng popup giữa chừng.
      setConnecting(false);
      setError('popup');
    },
  });

  const requestAccess = () => {
    if (connecting) return;
    setConnecting(true);
    setError(null);
    login();
  };

  return {
    token: validDriveToken(store),
    connecting,
    error,
    requestAccess,
    disconnect: store.clear,
  };
}
