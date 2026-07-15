// ─────────────────────────────────────────────────────────────────────────────
// Phân quyền app (owner / admin / user) — mô hình HYBRID:
//
// - Danh sách ADMIN nằm TRÊN REPO (config/permissions.json — chỉ ai có quyền
//   push/token Contents write mới sửa được). Xem github/permissions.ts.
// - File này lo phần còn lại: NHẬT KÝ TRUY CẬP `access-log.json` ở folder gốc
//   kho Drive — mỗi lần vào màn quản lý, app tự upsert email + thời điểm của
//   người dùng (ai cũng có quyền Editor kho Drive nên ghi được). Đây là nguồn
//   danh sách để owner chọn người phân quyền trong modal 権限管理.
// - Chỉ owner/admin mới thấy nút Xoá trên màn quản lý flow. App là static site
//   không backend nên đây là cổng UX, không phải hàng rào bảo mật tuyệt đối.
// ─────────────────────────────────────────────────────────────────────────────

import { findChildFile, getFileText, createJsonFile, updateFileContent } from './api';
import { DRIVE_ROOT_FOLDER_ID } from './config';

// Tài khoản owner của app (cố định theo yêu cầu vận hành).
export const OWNER_EMAIL = 'tuan.nguyen4@drjoy.jp';

// Tên file nhật ký truy cập trong folder gốc kho Drive.
const DRIVE_LOG_FOLDER = '18BNSBl_wMneoUdwYevmtnAoHbDdAlqn6';
const ACCESS_LOG_FILE = 'access-log.json';

export type PermRole = 'owner' | 'admin' | 'user';

export interface PermMember {
  email: string;
  name: string;
  lastAccessAt: string; // ISO 8601 — UI tự format theo múi giờ máy
}

// Góc nhìn gộp cho UI (modal 権限管理): admins từ repo + members từ Drive.
export interface PermissionsData {
  admins: string[];
  members: PermMember[];
}

export interface AccessLog {
  fileId: string;
  members: PermMember[];
}

const normEmail = (e: string) => e.trim().toLowerCase();

// Parse an toàn: file bị sửa tay/hỏng -> coi như rỗng thay vì crash màn quản lý.
function parseMembers(text: string): PermMember[] {
  try {
    const raw = JSON.parse(text) as { members?: unknown };
    return Array.isArray(raw.members)
      ? raw.members.filter(
          (m): m is PermMember =>
            !!m && typeof m === 'object' && typeof (m as PermMember).email === 'string',
        )
      : [];
  } catch {
    return [];
  }
}

export function resolveRole(email: string | undefined, data: Pick<PermissionsData, 'admins'> | null): PermRole {
  if (!email) return 'user';
  const e = normEmail(email);
  if (e === OWNER_EMAIL) return 'owner';
  return data?.admins.some((a) => normEmail(a) === e) ? 'admin' : 'user';
}

// Đọc nhật ký truy cập; chưa có thì tạo file rỗng để các lần ghi sau chỉ cần PATCH.
export async function loadAccessLog(token: string): Promise<AccessLog> {
  const existing = await findChildFile(token, DRIVE_LOG_FOLDER, ACCESS_LOG_FILE);
  if (existing) {
    return { fileId: existing.id, members: parseMembers(await getFileText(token, existing.id)) };
  }
  const created = await createJsonFile(
    token,
    DRIVE_LOG_FOLDER,
    ACCESS_LOG_FILE,
    JSON.stringify({ members: [] }, null, 2),
  );
  return { fileId: created.id, members: [] };
}

// Ghi nhận "tài khoản này vừa truy cập app": upsert vào members + cập nhật
// lastAccessAt, rồi lưu lại. Trả về bản mới nhất để UI dùng luôn.
export async function recordAccess(
  token: string,
  user: { email: string; name?: string },
): Promise<AccessLog> {
  const log = await loadAccessLog(token);
  const email = normEmail(user.email);
  const rest = log.members.filter((m) => normEmail(m.email) !== email);
  const members = [...rest, { email, name: user.name ?? '', lastAccessAt: new Date().toISOString() }];
  await updateFileContent(
    token,
    log.fileId,
    JSON.stringify({ members }, null, 2),
    'application/json',
  );
  return { fileId: log.fileId, members };
}
