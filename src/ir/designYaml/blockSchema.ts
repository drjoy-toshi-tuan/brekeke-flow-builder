import type { DesignBlockType } from './blockTypeMap';

// ─────────────────────────────────────────────────────────────────────────────
// Field riêng của từng block type 設計書 (scenario_flow) — dùng để dựng form soạn
// trên webapp (DesignBlockPropertyTab). CHÍNH BẢN của field bắt buộc =
// `pipeline/schemas/qa_validator.py::BLOCK_REQUIRED_FIELDS` (cập nhật bảng này
// mỗi khi allowlist đó đổi). Nhánh/rẽ (conditions/next) KHÔNG nằm ở đây — đã có
// cơ chế edge/branch sẵn của canvas (xem fromDesignYaml.ts: data.branches).
//
// `optional` chỉ liệt kê field đã XÁC NHẬN gặp trong 設計書 thật (không đoán field
// chưa kiểm chứng) — field lạ khác vẫn sửa được qua khối "Field khác" (raw editor)
// trong DesignBlockPropertyTab, không bị mất khi lưu (round-trip qua node.data).
// ─────────────────────────────────────────────────────────────────────────────

export type DesignFieldKind = 'text' | 'textarea' | 'list' | 'select';

export interface DesignField {
  key: string;
  label: string;
  kind: DesignFieldKind;
  options?: string[]; // dùng khi kind: 'select'
}

interface DesignBlockSchema {
  required: DesignField[];
  optional: DesignField[];
}

const EMPTY: DesignBlockSchema = { required: [], optional: [] };

export const DESIGN_BLOCK_SCHEMA: Record<DesignBlockType, DesignBlockSchema> = {
  opening: { required: [], optional: [{ key: 'use_acceptance_times', label: '受付時間チェックを使う', kind: 'select', options: ['true', 'false'] }] },
  announcement: EMPTY,
  hearing: {
    required: [{ key: 'output_format', label: '出力形式', kind: 'select', options: ['text', 'enum', 'datetime'] }],
    optional: [{ key: 'output_labels', label: '選択肢一覧（output_format: enum のとき）', kind: 'list' }],
  },
  subflow: { required: [{ key: 'flowname', label: 'サブフロー名', kind: 'text' }], optional: [] },
  context_match_router: { required: [{ key: 'reference_module', label: '参照モジュール', kind: 'text' }], optional: [] },
  script: EMPTY,
  call_transfer: EMPTY,
  termination: { required: [{ key: 'termination_ref', label: '終話パターン名（termination_patterns参照）', kind: 'text' }], optional: [] },
  augment: {
    required: [],
    optional: [
      { key: 'augment_pattern', label: '暫定枠の種別', kind: 'select', options: ['new_module', 'none_applicable', 'director_handled'] },
      { key: 'augment_purpose', label: '暫定枠の目的（人間レビュー用メモ）', kind: 'textarea' },
    ],
  },
  incoming_category_classifier: EMPTY, // conditions は edge/branch で編集
  phone2name: { required: [{ key: 'found_template', label: '該当時テンプレート', kind: 'text' }], optional: [] },
  cmr_chain: {
    required: [
      { key: 'reference_modules', label: '参照モジュール一覧', kind: 'list' },
      { key: 'default_next', label: 'デフォルト遷移先（step名）', kind: 'text' },
    ],
    optional: [],
  },
  slot: {
    required: [{ key: 'slot', label: 'スロット種別', kind: 'select', options: ['patient_name', 'date_of_birth', 'phone', 'card_number'] }],
    optional: [{ key: 'save_to', label: '保存先（save_to）', kind: 'text' }],
  },
  clinical_department_classifier: { required: [{ key: 'reference_module', label: '参照モジュール', kind: 'text' }], optional: [] },
  dob: { required: [], optional: [{ key: 'save_to', label: '保存先（save_to）', kind: 'text' }] },
  phone: { required: [], optional: [{ key: 'save_to', label: '保存先（save_to）', kind: 'text' }] },
  patient_name: { required: [], optional: [{ key: 'save_to', label: '保存先（save_to）', kind: 'text' }] },
  intent: {
    required: [
      { key: 'options', label: '判定候補一覧', kind: 'list' },
      { key: 'save_to', label: '保存先（save_to）', kind: 'text' },
    ],
    optional: [],
  },
  phone_branch: EMPTY, // conditions は edge/branch で編集
  clinical_department: { required: [{ key: 'departments', label: '診療科一覧', kind: 'list' }], optional: [] },
  clinical_department_normalize: { required: [{ key: 'departments', label: '診療科一覧', kind: 'list' }], optional: [] },
  free_text: { required: [{ key: 'save_to', label: '保存先（save_to）', kind: 'text' }], optional: [] },
  faq: EMPTY, // conditions は edge/branch で編集
  card_number: { required: [{ key: 'save_to', label: '保存先（save_to）', kind: 'text' }], optional: [] },
  null_check: {
    required: [
      { key: 'key', label: 'チェック対象キー', kind: 'text' },
      { key: 'true_next', label: '真のとき遷移先（step名）', kind: 'text' },
      { key: 'false_next', label: '偽のとき遷移先（step名）', kind: 'text' },
    ],
    optional: [],
  },
  clinic_day_default: EMPTY,
};

export function fieldsFor(blockType: DesignBlockType): DesignBlockSchema {
  return DESIGN_BLOCK_SCHEMA[blockType] ?? EMPTY;
}

// Field đã có form riêng (không hiện lại ở khối "Field khác" để tránh trùng lặp).
export function modeledKeysFor(blockType: DesignBlockType): Set<string> {
  const schema = fieldsFor(blockType);
  return new Set([...schema.required, ...schema.optional].map((f) => f.key));
}
