import { parse, stringify } from 'yaml';

// ─────────────────────────────────────────────────────────────────────────────
// Đọc NHANH phần metadata ở header của file YAML (không dựng cả IR) để hiển thị
// trong danh sách file: 施設名 / シナリオ名 / 作成日時 / 更新日時 / 作成者.
// Field vắng mặt -> undefined (UI hiện "—"). Hàm thuần, KHÔNG import React.
// ─────────────────────────────────────────────────────────────────────────────

export interface FlowMeta {
  facility?: string; // 施設名
  name?: string; // シナリオ名
  createdAt?: string; // 作成日時 (yyyy-MM-dd HH:mm)
  updatedAt?: string; // 更新日時 (yyyy-MM-dd HH:mm)
  author?: string; // 作成者
}

function str(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim() ? value.trim() : undefined;
}

export function parseFlowMeta(text: string): FlowMeta {
  try {
    const flow = (parse(text) as { flow?: Record<string, unknown> } | null)?.flow ?? {};
    return {
      facility: str(flow.facility),
      name: str(flow.name),
      createdAt: str(flow.createdAt),
      updatedAt: str(flow.updatedAt),
      author: str(flow.author),
    };
  } catch {
    return {};
  }
}

// Ghi đè metadata trong YAML (đổi 施設名/シナリオ名… từ màn quản lý file) mà KHÔNG
// đụng phần nodes/subflows — parse rồi gán field và stringify lại. Field trong
// patch là undefined -> giữ nguyên; chuỗi rỗng -> giữ nguyên (không xoá field).
export function updateFlowMeta(text: string, patch: FlowMeta): string {
  const doc = (parse(text) as { flow?: Record<string, unknown> } | null) ?? {};
  const flow = doc.flow ?? {};
  for (const key of ['facility', 'name', 'createdAt', 'updatedAt', 'author'] as const) {
    const value = patch[key];
    if (typeof value === 'string' && value.trim()) flow[key] = value.trim();
  }
  return stringify({ ...doc, flow }, { lineWidth: 0 });
}
