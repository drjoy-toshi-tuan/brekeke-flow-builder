// ─────────────────────────────────────────────────────────────────────────────
// 設計書 YAML (pipeline gen_flow) chứa nhiều section KHÔNG thuộc về đồ thị flow
// (basic_info, flow_structure, context_fields, hearing_items, termination_patterns…).
// FlowIR chỉ mô tả graph (nodes/edges), nên các section đó được giữ nguyên vẹn ở
// đây (passthrough) để fromDesignYaml -> toDesignYaml round-trip không mất field
// nào mà webapp chưa hiểu/chưa cần hiển thị.
// ─────────────────────────────────────────────────────────────────────────────

export interface DesignYamlPassthrough {
  version?: unknown;
  basic_info?: unknown;
  flow_structure?: unknown;
  purpose?: unknown;
  flow_diagrams?: unknown;
  context_fields?: unknown;
  hearing_items?: unknown;
  termination_patterns?: unknown;
  step_details?: unknown;
  phonebook?: unknown;
  // Field lạ khác (pipeline có thể thêm section mới) — giữ nguyên theo tên key.
  [key: string]: unknown;
}

// Các key đã được model hoá riêng (không rơi vào passthrough "field lạ").
export const KNOWN_TOP_LEVEL_KEYS = new Set(['scenario_flow']);
