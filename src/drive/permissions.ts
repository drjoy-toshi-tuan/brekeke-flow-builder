// ─────────────────────────────────────────────────────────────────────────────
// Phân quyền app (owner / admin / user) — KHÔNG có backend nên dữ liệu quyền lưu
// trong file `permissions.json` ở folder gốc của kho Drive (mọi người dùng app
// đều có quyền Editor trên kho nên đọc/ghi được; đây là cổng UX, không phải
// hàng rào bảo mật tuyệt đối — xem README §Bảo mật).
//
// - OWNER cố định theo email; admin do owner chỉ định (mảng `admins`).
// - `members` = danh sách tài khoản ĐÃ TRUY CẬP app (mỗi lần vào màn quản lý
//   Drive sẽ tự ghi nhận email + thời điểm) — nguồn cho owner chọn người để
//   phân quyền.
// - Chỉ owner/admin mới thấy nút Xoá trên màn quản lý flow.
// ─────────────────────────────────────────────────────────────────────────────

import { findChildFile, getFileText, createJsonFile, updateFileContent } from './api';
import { DRIVE_ROOT_FOLDER_ID } from './config';

// Tài khoản owner của app (cố định theo yêu cầu vận hành).
export const OWNER_EMAIL = 'tuan.nguyen4@drjoy.jp';

// Tên file phân quyền trong folder gốc kho Drive.
const PERMISSIONS_FILE = 'permissions.json';

export type PermRole = 'owner' | 'admin' | 'user';

export interface PermMember {
  email: string;
  name: string;
  lastAccessAt: string; // ISO 8601 — UI tự format theo múi giờ máy
}

export interface PermissionsData {
  admins: string[]; // email các tài khoản được owner cấp quyền Admin
  members: PermMember[]; // tài khoản đã truy cập app (tự ghi nhận)
}

export interface PermissionsFile {
  fileId: string;
  data: PermissionsData;
}

const EMPTY: PermissionsData = { admins: [], members: [] };

const normEmail = (e: string) => e.trim().toLowerCase();

// Parse an toàn: file bị sửa tay/hỏng -> coi như rỗng thay vì crash màn quản lý.
function parsePermissions(text: string): PermissionsData {
  try {
    const raw = JSON.parse(text) as Partial<PermissionsData>;
    return {
      admins: Array.isArray(raw.admins) ? raw.admins.filter((x): x is string => typeof x === 'string') : [],
      members: Array.isArray(raw.members)
        ? raw.members.filter(
            (m): m is PermMember =>
              !!m && typeof m === 'object' && typeof (m as PermMember).email === 'string',
          )
        : [],
    };
  } catch {
    return { ...EMPTY };
  }
}

export function resolveRole(email: string | undefined, data: PermissionsData | null): PermRole {
  if (!email) return 'user';
  const e = normEmail(email);
  if (e === OWNER_EMAIL) return 'owner';
  return data?.admins.some((a) => normEmail(a) === e) ? 'admin' : 'user';
}

// Đọc file phân quyền; chưa có thì tạo file rỗng để các lần ghi sau chỉ cần PATCH.
export async function loadPermissions(token: string): Promise<PermissionsFile> {
  const existing = await findChildFile(token, DRIVE_ROOT_FOLDER_ID, PERMISSIONS_FILE);
  if (existing) {
    return { fileId: existing.id, data: parsePermissions(await getFileText(token, existing.id)) };
  }
  const created = await createJsonFile(
    token,
    DRIVE_ROOT_FOLDER_ID,
    PERMISSIONS_FILE,
    JSON.stringify(EMPTY, null, 2),
  );
  return { fileId: created.id, data: { ...EMPTY } };
}

export async function savePermissions(token: string, fileId: string, data: PermissionsData): Promise<void> {
  await updateFileContent(token, fileId, JSON.stringify(data, null, 2), 'application/json');
}

// Ghi nhận "tài khoản này vừa truy cập app": upsert vào members + cập nhật
// lastAccessAt, rồi lưu lại. Trả về bản mới nhất để UI dùng luôn.
export async function recordAccess(
  token: string,
  user: { email: string; name?: string },
): Promise<PermissionsFile> {
  const file = await loadPermissions(token);
  const email = normEmail(user.email);
  const rest = file.data.members.filter((m) => normEmail(m.email) !== email);
  const data: PermissionsData = {
    ...file.data,
    members: [...rest, { email, name: user.name ?? '', lastAccessAt: new Date().toISOString() }],
  };
  await savePermissions(token, file.fileId, data);
  return { fileId: file.fileId, data };
}

// Cấp/thu quyền Admin cho 1 email (owner thao tác trong modal 権限管理).
export function withAdmin(data: PermissionsData, email: string, makeAdmin: boolean): PermissionsData {
  const e = normEmail(email);
  const admins = data.admins.filter((a) => normEmail(a) !== e);
  return { ...data, admins: makeAdmin ? [...admins, e] : admins };
}
