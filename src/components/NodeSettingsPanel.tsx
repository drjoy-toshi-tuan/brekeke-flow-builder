import { useEffect, useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import type { FlowNode, NodeType } from '../ir/types';
import { NODE_CONFIG } from '../ui/nodeConfig';
import {
  PROPERTY_FIELDS,
  BRANCH_SCHEMA,
  readBranches,
  type PropertyField,
} from '../ui/nodeSchema';
import { Icon } from '../ui/icons';
import { useT, type TKey } from '../ui/i18n';
import { CodeEditor } from './CodeEditor';
import { RegexBranchInput } from './RegexBranchInput';

// Key giải thích ý nghĩa loại node trong từ điển i18n (exStart, exAnnounce, …).
function explainKey(type: NodeType): TKey {
  return ('ex' + type.charAt(0).toUpperCase() + type.slice(1)) as TKey;
}

// ─────────────────────────────────────────────────────────────────────────────
// Panel setting: 3 tab chọn từ header —
//   General  (基本設定)    : tên node + mô tả.
//   Property (プロパティ設定): tham số riêng theo loại node (nodeSchema).
//   Branch   (分岐設定)     : điều kiện rẽ nhánh (thêm/bớt cho condition/script).
// Panel luôn mount, TRƯỢT vào/ra từ phải; giữ node cuối trong lúc trượt ra.
// ─────────────────────────────────────────────────────────────────────────────

const inputClass =
  'mt-1 w-full rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-sm text-[var(--bk-text)] outline-none transition focus:border-[var(--bk-accent)]';

type Tab = 'general' | 'property' | 'branch';

export function NodeSettingsPanel() {
  const ir = useFlowStore((s) => s.ir);
  const selectedNodeId = useFlowStore((s) => s.selectedNodeId);
  const selectNode = useFlowStore((s) => s.selectNode);

  const node = ir?.nodes.find((n) => n.id === selectedNodeId) ?? null;
  const open = !!node;

  // Giữ node cuối để nội dung còn hiển thị trong lúc panel trượt ra.
  const [shownNode, setShownNode] = useState<FlowNode | null>(node);
  useEffect(() => {
    if (node) setShownNode(node);
  }, [node]);

  const display = node ?? shownNode;

  return (
    <aside
      className={[
        'absolute right-0 top-0 z-10 flex h-full w-[560px] max-w-[85vw] flex-col border-l border-[var(--bk-border)] bg-[var(--bk-surface)] shadow-[var(--bk-shadow)]',
        'transition-transform duration-300 ease-out will-change-transform',
        open ? 'translate-x-0' : 'translate-x-full pointer-events-none',
      ].join(' ')}
      aria-hidden={!open}
    >
      {display && <PanelContent key={display.id} node={display} onClose={() => selectNode(null)} />}
    </aside>
  );
}

function PanelContent({ node, onClose }: { node: FlowNode; onClose: () => void }) {
  const t = useT();
  const cfg = NODE_CONFIG[node.type];

  const hasProperty = PROPERTY_FIELDS[node.type].length > 0;
  const hasBranch = BRANCH_SCHEMA[node.type].mode !== 'none';

  const [tab, setTab] = useState<Tab>('general');
  // Nếu tab đang chọn không khả dụng cho node này -> lùi về General.
  useEffect(() => {
    if ((tab === 'property' && !hasProperty) || (tab === 'branch' && !hasBranch)) {
      setTab('general');
    }
  }, [tab, hasProperty, hasBranch]);

  return (
    <div className="bk-panel-content flex h-full flex-col">
      <header className="border-b border-[var(--bk-border)]">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <span
              className="flex h-9 w-9 flex-none items-center justify-center rounded-xl text-lg"
              style={{ color: cfg.color, background: `color-mix(in srgb, ${cfg.color} 15%, transparent)` }}
            >
              <Icon icon={cfg.icon} />
            </span>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wide" style={{ color: cfg.color }}>
                {cfg.typeLabel}
              </div>
              <div className="text-sm font-medium text-[var(--bk-text-muted)]">
                {t(explainKey(node.type))}
              </div>
            </div>
          </div>
          <button
            type="button"
            className="flex h-7 w-7 items-center justify-center rounded-lg text-[var(--bk-text-faint)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
            onClick={onClose}
            aria-label={t('close')}
          >
            <Icon icon="lucide:x" width={16} height={16} />
          </button>
        </div>

        {/* Tab chọn từ header. Property/Branch mờ đi (disabled) nếu node không có. */}
        <div className="flex gap-1 px-3">
          <TabButton label={t('tabGeneral')} active={tab === 'general'} onClick={() => setTab('general')} />
          <TabButton
            label={t('tabProperty')}
            active={tab === 'property'}
            disabled={!hasProperty}
            onClick={() => setTab('property')}
          />
          <TabButton
            label={t('tabBranch')}
            active={tab === 'branch'}
            disabled={!hasBranch}
            onClick={() => setTab('branch')}
          />
        </div>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {tab === 'general' && <GeneralTab node={node} />}
        {tab === 'property' && <PropertyTab node={node} />}
        {tab === 'branch' && <BranchTab node={node} />}
      </div>
    </div>
  );
}

function TabButton({
  label,
  active,
  disabled,
  onClick,
}: {
  label: string;
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        'relative -mb-px border-b-2 px-3 py-2 text-xs font-semibold transition',
        active
          ? 'border-[var(--bk-accent)] text-[var(--bk-accent)]'
          : 'border-transparent text-[var(--bk-text-muted)] hover:text-[var(--bk-text)]',
        disabled ? 'cursor-not-allowed opacity-35 hover:text-[var(--bk-text-muted)]' : '',
      ].join(' ')}
    >
      {label}
    </button>
  );
}

// ── General ─────────────────────────────────────────────────────────────────
function GeneralTab({ node }: { node: FlowNode }) {
  const t = useT();
  const updateNode = useFlowStore((s) => s.updateNode);
  const description = typeof node.data.description === 'string' ? node.data.description : '';

  return (
    <>
      <label className="block">
        <span className="text-xs font-medium text-[var(--bk-text-muted)]">{t('nodeName')}</span>
        <input
          className={inputClass}
          value={node.label}
          onChange={(e) => updateNode(node.id, { label: e.target.value })}
        />
      </label>
      <label className="block">
        <span className="text-xs font-medium text-[var(--bk-text-muted)]">{t('description')}</span>
        <input
          type="text"
          className={inputClass}
          placeholder={t('descriptionPlaceholder')}
          value={description}
          onChange={(e) => updateNode(node.id, { data: { description: e.target.value } })}
        />
      </label>
    </>
  );
}

// ── Property ──────────────────────────────────────────────────────────────────
function PropertyTab({ node }: { node: FlowNode }) {
  const t = useT();
  const fields = PROPERTY_FIELDS[node.type].filter((f) => !f.showIf || f.showIf(node.data));
  if (fields.length === 0) {
    return <p className="text-sm text-[var(--bk-text-faint)]">{t('noPropertyNote')}</p>;
  }
  return (
    <div className="space-y-4">
      {fields.map((f) => (
        <FieldControl key={f.key} node={node} field={f} />
      ))}
    </div>
  );
}

function FieldControl({ node, field }: { node: FlowNode; field: PropertyField }) {
  const t = useT();
  const updateNode = useFlowStore((s) => s.updateNode);
  const raw = node.data[field.key];
  // YAML có thể trả số (retryCount: 2) -> ép về chuỗi để hiển thị/sửa nhất quán.
  const value =
    typeof raw === 'string' ? raw : typeof raw === 'number' ? String(raw) : field.default ?? '';
  const set = (v: string) => updateNode(node.id, { data: { [field.key]: v } });
  const label = <span className="text-xs font-medium text-[var(--bk-text-muted)]">{t(field.labelKey)}</span>;

  switch (field.kind) {
    case 'text':
      return (
        <label className="block">
          {label}
          {/* Text 1 dòng: chặn xuống dòng (dán nhiều dòng -> gộp về 1 dòng). */}
          <input
            type="text"
            className={inputClass}
            value={value}
            onChange={(e) => set(e.target.value.replace(/[\r\n]+/g, ' '))}
          />
        </label>
      );
    case 'number':
      return (
        <label className="block">
          {label}
          <input
            type="text"
            inputMode="numeric"
            className={inputClass}
            value={value}
            onChange={(e) => set(e.target.value.replace(/[^0-9]/g, ''))}
          />
        </label>
      );
    case 'textarea':
      return (
        <label className="block">
          {label}
          <textarea
            className={`${inputClass} resize-y`}
            rows={field.rows ?? 3}
            value={value}
            onChange={(e) => set(e.target.value)}
          />
        </label>
      );
    case 'select':
      return (
        <label className="block">
          {label}
          <select className={inputClass} value={value} onChange={(e) => set(e.target.value)}>
            {field.options?.map((o) => (
              <option key={o.value} value={o.value}>
                {o.labelKey ? t(o.labelKey) : o.label}
              </option>
            ))}
          </select>
        </label>
      );
    case 'yesno':
      return (
        <div className="block">
          {label}
          <div className="mt-1 flex gap-2">
            {field.options?.map((o) => {
              const on = value === o.value;
              return (
                <button
                  key={o.value}
                  type="button"
                  onClick={() => set(o.value)}
                  className={[
                    'flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition',
                    on
                      ? 'border-[var(--bk-accent)] bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]'
                      : 'border-[var(--bk-border)] bg-[var(--bk-surface-2)] text-[var(--bk-text-muted)] hover:text-[var(--bk-text)]',
                  ].join(' ')}
                >
                  {o.labelKey ? t(o.labelKey) : o.label}
                </button>
              );
            })}
          </div>
        </div>
      );
    case 'code':
      return (
        <div className="block">
          {label}
          <div className="mt-1">
            <CodeEditor value={value} onChange={set} rows={field.rows ?? 12} />
          </div>
        </div>
      );
    case 'collapsibleTextarea':
      return <CollapsibleField node={node} field={field} value={value} onChange={set} />;
  }
}

// Textarea dài -> ẩn/hiện bằng nút bấm (giống cơ chế mở panel thêm node).
function CollapsibleField({
  field,
  value,
  onChange,
}: {
  node: FlowNode;
  field: PropertyField;
  value: string;
  onChange: (v: string) => void;
}) {
  const t = useT();
  const [open, setOpen] = useState(false);
  return (
    <div className="block">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-left text-xs font-medium text-[var(--bk-text-muted)] transition hover:text-[var(--bk-text)]"
        aria-expanded={open}
      >
        <span>
          {t(field.labelKey)}
          {value.trim() && !open ? ' •' : ''}
        </span>
        <Icon
          icon="lucide:chevron-down"
          width={15}
          height={15}
          className={`transition-transform ${open ? 'rotate-180' : ''}`}
        />
      </button>
      {open && (
        <textarea
          className={`${inputClass} resize-y font-mono`}
          rows={field.rows ?? 6}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          autoFocus
        />
      )}
    </div>
  );
}

// ── Branch ────────────────────────────────────────────────────────────────────
function BranchTab({ node }: { node: FlowNode }) {
  const t = useT();
  const schema = BRANCH_SCHEMA[node.type];
  const addBranch = useFlowStore((s) => s.addBranch);
  const updateBranch = useFlowStore((s) => s.updateBranch);
  const removeBranch = useFlowStore((s) => s.removeBranch);

  if (schema.mode === 'none') {
    return <p className="text-sm text-[var(--bk-text-faint)]">{t('branchNoneNote')}</p>;
  }

  if (schema.mode === 'fixed') {
    // Nhánh cố định (FAILED / NEXT …): chỉ xem, không sửa được.
    return (
      <div className="space-y-3">
        <p className="text-xs text-[var(--bk-text-faint)]">{t('branchFixedNote')}</p>
        <div className="space-y-2">
          {(schema.fixed ?? []).map((b) => (
            <div
              key={b.id}
              className="flex items-center gap-2 rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-sm font-medium text-[var(--bk-text-muted)]"
            >
              <span className="h-2 w-2 flex-none rounded-full bg-[var(--bk-text-faint)]" />
              {b.label ?? b.id}
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Nhánh tự do (condition/script): thêm/sửa/xoá. Nhánh đầu không xoá được.
  const branches = readBranches(node.data);
  return (
    <div className="space-y-3">
      <div className="space-y-2">
        {branches.map((b, i) => (
          <div key={b.id} className="flex items-center gap-2">
            <RegexBranchInput
              className={`${inputClass} !mt-0 flex-1 font-mono`}
              value={b.value}
              placeholder={t('branchConditionPlaceholder')}
              onChange={(v) => updateBranch(node.id, b.id, v)}
            />
            <button
              type="button"
              disabled={i === 0}
              onClick={() => removeBranch(node.id, b.id)}
              title={t('deleteBranch')}
              aria-label={t('deleteBranch')}
              className={[
                'flex h-9 w-9 flex-none items-center justify-center rounded-lg border border-[var(--bk-border)] transition',
                i === 0
                  ? 'cursor-not-allowed opacity-30'
                  : 'text-[var(--bk-text-muted)] hover:border-[#fca5a5] hover:bg-[#fee2e2] hover:text-[#dc2626]',
              ].join(' ')}
            >
              <Icon icon="lucide:trash-2" width={15} height={15} />
            </button>
          </div>
        ))}
      </div>
      <button
        type="button"
        onClick={() => addBranch(node.id)}
        className="flex items-center gap-2 rounded-lg border border-dashed border-[var(--bk-border)] px-3 py-2 text-sm font-medium text-[var(--bk-text-muted)] transition hover:border-[var(--bk-accent)] hover:text-[var(--bk-accent)]"
      >
        <Icon icon="lucide:plus" width={16} height={16} />
        {t('addBranch')}
      </button>
    </div>
  );
}
