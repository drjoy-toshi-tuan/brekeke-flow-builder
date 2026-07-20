import type { NodeType } from '../types';

// ─────────────────────────────────────────────────────────────────────────────
// Bảng map 26 block type của 設計書 YAML (scenario_flow, pipeline gen_flow)
// <-> NodeType của FlowIR (webapp). Chính bản = schemas/qa_validator.py::KNOWN_BLOCK_TYPES
// (pipeline/CLAUDE.md — cập nhật bảng này mỗi khi allowlist đó đổi).
//
// Đây CHỈ là map hiển thị/mặc định (chọn icon, màu, nhóm panel trên canvas).
// Giá trị `type` gốc của 設計書 luôn được giữ nguyên ở node.data.blockType — đó mới
// là nguồn sự thật khi ghi lại YAML (xem toDesignYaml.ts), nên map lệch không làm mất dữ liệu.
// ─────────────────────────────────────────────────────────────────────────────

export const DESIGN_BLOCK_TYPES = [
  'opening',
  'announcement',
  'hearing',
  'subflow',
  'context_match_router',
  'script',
  'call_transfer',
  'termination',
  'augment',
  'incoming_category_classifier',
  'phone2name',
  'cmr_chain',
  'slot',
  'clinical_department_classifier',
  'dob',
  'phone',
  'patient_name',
  'intent',
  'phone_branch',
  'clinical_department',
  'clinical_department_normalize',
  'free_text',
  'faq',
  'card_number',
  'null_check',
  'clinic_day_default',
] as const;

export type DesignBlockType = (typeof DESIGN_BLOCK_TYPES)[number];

export const BLOCK_TO_NODE_TYPE: Record<DesignBlockType, NodeType> = {
  opening: 'announce',
  announcement: 'announce',
  hearing: 'interaction',
  subflow: 'jump',
  context_match_router: 'nexus',
  script: 'logic',
  call_transfer: 'transfer',
  termination: 'hangup',
  augment: 'logic',
  incoming_category_classifier: 'classifier',
  phone2name: 'normalization',
  cmr_chain: 'nexus',
  slot: 'interaction',
  clinical_department_classifier: 'classifier',
  dob: 'interaction',
  phone: 'interaction',
  patient_name: 'interaction',
  intent: 'openai',
  phone_branch: 'nexus',
  clinical_department: 'interaction',
  clinical_department_normalize: 'normalization',
  free_text: 'interaction',
  faq: 'faq',
  card_number: 'interaction',
  null_check: 'nexus',
  clinic_day_default: 'logic',
};

// Dùng khi 1 node được TẠO MỚI trên canvas (chưa từng có blockType gốc) và cần
// xuất ra 設計書 YAML — chọn block type mặc định hợp lý nhất cho mỗi NodeType.
export const DEFAULT_BLOCK_BY_NODE_TYPE: Partial<Record<NodeType, DesignBlockType>> = {
  announce: 'announcement',
  interaction: 'hearing',
  nexus: 'context_match_router',
  logic: 'script',
  classifier: 'incoming_category_classifier',
  normalization: 'phone2name',
  openai: 'intent',
  faq: 'faq',
  transfer: 'call_transfer',
  jump: 'subflow',
  save: 'script',
  hangup: 'termination',
  start: 'opening',
};

export function isDesignBlockType(value: string): value is DesignBlockType {
  return (DESIGN_BLOCK_TYPES as readonly string[]).includes(value);
}
