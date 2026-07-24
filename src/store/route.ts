import type { Department } from '../drive/permissions';

// ─────────────────────────────────────────────────────────────────────────────
// Chuyển đổi hash URL ↔ Route THUẦN (không đụng window/history) để test độc lập.
// Grammar: #/{mode}/flow-management | #/{mode}/file/{driveFileId}[/{tab}].
// Hash cũ #/cs | #/ts vẫn parse được (→ flow-management). mode = cs | ts.
// ─────────────────────────────────────────────────────────────────────────────

export type WorkspaceMode = Department; // 'cs' | 'ts'
export type ScreenName = 'flow-management' | 'file';

export interface RouteState {
  mode: WorkspaceMode;
  screen: ScreenName;
  fileId: string | null; // id file Drive khi screen === 'file'
  tab: string | null; // tab canvas (chỉ có nghĩa khi mở file ở mode cs); null = flow
}

function decode(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

// "#/cs/file/abc/announce" -> { mode:'cs', screen:'file', fileId:'abc', tab:'announce' }.
// Chuỗi rỗng / lạ -> { mode:'ts', screen:'flow-management', ... }.
export function parseHash(hash: string): RouteState {
  const raw = hash.replace(/^#\/?/, '');
  const seg = raw.split('/').filter(Boolean).map(decode);
  const m = seg[0]?.toLowerCase();
  const mode: WorkspaceMode = m === 'cs' || m === 'ts' ? (m as WorkspaceMode) : 'ts';
  if (seg[1]?.toLowerCase() === 'file' && seg[2]) {
    return { mode, screen: 'file', fileId: seg[2], tab: seg[3] ?? null };
  }
  return { mode, screen: 'flow-management', fileId: null, tab: null };
}

export function serializeRoute(r: RouteState): string {
  const base = `#/${r.mode}`;
  if (r.screen === 'file' && r.fileId) {
    const f = `${base}/file/${encodeURIComponent(r.fileId)}`;
    return r.tab ? `${f}/${encodeURIComponent(r.tab)}` : f;
  }
  return `${base}/flow-management`;
}
