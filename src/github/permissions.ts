// ─────────────────────────────────────────────────────────────────────────────
// Danh sách ADMIN của app lưu TRÊN REPO (config/permissions.json) thay vì Drive:
// chỉ ai có quyền push repo (hoặc token Contents: Read/Write) mới sửa được —
// chặt hơn hẳn file trên kho Drive chung (mọi Editor đều ghi được).
//
// - ĐỌC: repo public nên fetch thẳng raw.githubusercontent.com, KHÔNG cần token
//   (mọi người dùng màn Drive đều đọc được quyền dù chưa kết nối GitHub).
// - GHI: owner đổi quyền trong app bằng GitHub token đã lưu (github/token.ts).
// Danh sách "ai đã truy cập app" vẫn tự ghi trên Drive — xem drive/permissions.ts.
// ─────────────────────────────────────────────────────────────────────────────

import { getFlow, putFlow, GithubApiError } from './api';
import { GITHUB_OWNER, GITHUB_REPO, GITHUB_BRANCH } from './config';

export const REPO_PERMISSIONS_PATH = 'config/permissions.json';

// Đọc danh sách admin từ repo (không cần token). Mọi lỗi (404 khi file chưa có,
// mạng, JSON hỏng…) đều trả [] — phân quyền là tiện ích, không chặn màn hình.
export async function fetchAdmins(): Promise<string[]> {
  // Cache-buster: raw.githubusercontent cache qua CDN (~5 phút) — thêm query để
  // lần "Làm mới"/vào lại thấy quyền mới sớm nhất có thể.
  const url = `https://raw.githubusercontent.com/${GITHUB_OWNER}/${GITHUB_REPO}/${GITHUB_BRANCH}/${REPO_PERMISSIONS_PATH}?t=${Date.now()}`;
  try {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return [];
    const body = (await res.json()) as { admins?: unknown };
    return Array.isArray(body.admins)
      ? body.admins.filter((x): x is string => typeof x === 'string')
      : [];
  } catch {
    return [];
  }
}

// Ghi danh sách admin lên repo (commit vào GITHUB_BRANCH). Cần token có quyền
// Contents: Read/Write — lấy sha hiện tại trước để không ghi đè mù.
export async function saveAdmins(token: string, admins: string[]): Promise<void> {
  let sha: string | undefined;
  try {
    sha = (await getFlow(token, REPO_PERMISSIONS_PATH)).sha;
  } catch (e) {
    // File chưa tồn tại -> tạo mới (không truyền sha); lỗi khác ném tiếp.
    if (!(e instanceof GithubApiError && e.code === 'notfound')) throw e;
  }
  await putFlow(
    token,
    REPO_PERMISSIONS_PATH,
    `${JSON.stringify({ admins }, null, 2)}\n`,
    'Cập nhật danh sách admin (phân quyền app)',
    sha,
  );
}
