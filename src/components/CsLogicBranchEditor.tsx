import { useFlowStore } from '../store/flowStore';
import type { FlowNode } from '../ir/types';
import { DAY_KEYS, type DayKey } from '../ir/types';
import {
  csProductBranches,
  csSlotsToDataBranches,
  dayRemainder,
  defaultSlot,
  hearingNodeLabel,
  hearingSourceOptions,
  phoneValuesFor,
  readCsCount,
  readCsSlots,
  timeRemainderRanges,
  CS_DAY_LABELS,
  CS_ELSE_LABEL,
  MAX_CS_CONDITIONS,
  type CsRange,
  type CsSlot,
  type CsSlotKind,
} from '../ui/csLogic';
import { Icon } from '../ui/icons';
import { useLang, useT } from '../ui/i18n';

// ─────────────────────────────────────────────────────────────────────────────
// Node 分岐ロジック (CS). 2 tab:
//   - プロパティ設定: CsLogicPropertyEditor — số điều kiện (1/2/3) + mỗi điều kiện
//     (聴取内容 / 電話番号 / 着信日時) với tập giá trị.
//   - 分岐設定: CsLogicBranchList — liệt kê nhánh = tích các tập giá trị.
// ─────────────────────────────────────────────────────────────────────────────

const inputClass =
  'w-full rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-2.5 py-1.5 text-sm text-[var(--bk-text)] outline-none transition focus:border-[var(--bk-accent)]';

function useCsState(node: FlowNode) {
  const draft = useFlowStore((s) => s.draft);
  const setDraftField = useFlowStore((s) => s.setDraftField);
  const data = draft?.data ?? node.data;
  const count = readCsCount(data);
  const slots = readCsSlots(data);
  const commit = (nextSlots: CsSlot[], nextCount = nextSlots.length) => {
    setDraftField('csCount', nextCount);
    setDraftField('csSlots', nextSlots);
    setDraftField('branches', csSlotsToDataBranches(nextSlots));
  };
  return { count, slots, commit };
}

export function CsLogicPropertyEditor({ node }: { node: FlowNode }) {
  const t = useT();
  const ir = useFlowStore((s) => s.ir);
  const { count, slots, commit } = useCsState(node);

  const setCount = (n: number) => {
    if (n === slots.length) return;
    const next = slots.slice(0, n);
    while (next.length < n) next.push(defaultSlot('hearing', ir, node.id));
    commit(next, n);
  };
  const updateSlot = (i: number, slot: CsSlot) => commit(slots.map((s, j) => (j === i ? slot : s)), count);

  return (
    <div className="space-y-3">
      {/* 条件の数 — nút on/off, to. */}
      <div>
        <span className="mb-1.5 block text-xs font-semibold text-[var(--bk-text-muted)]">{t('clCondCount')}</span>
        <div className="flex gap-2">
          {Array.from({ length: MAX_CS_CONDITIONS }, (_, k) => k + 1).map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => setCount(n)}
              className={[
                'flex-1 rounded-xl border px-3 py-2.5 text-sm font-bold transition',
                count === n
                  ? 'border-[var(--bk-accent)] bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]'
                  : 'border-[var(--bk-border)] text-[var(--bk-text-muted)] hover:border-[var(--bk-accent)]',
              ].join(' ')}
            >
              {n}
            </button>
          ))}
        </div>
      </div>

      {slots.map((slot, i) => (
        <div key={i} className="overflow-hidden rounded-xl border border-[var(--bk-border)]">
          <div className="border-b border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-sm font-bold text-[var(--bk-text)]">
            <span className="mr-1.5 inline-flex h-5 min-w-5 items-center justify-center rounded-md bg-[var(--bk-accent-soft)] px-1.5 text-[11px] font-bold text-[var(--bk-accent)]">
              {i + 1}
            </span>
            {t('clCondition')} {i + 1}
          </div>
          <div className="space-y-2.5 p-3">
            <SlotEditor node={node} slot={slot} onChange={(s) => updateSlot(i, s)} />
          </div>
        </div>
      ))}
    </div>
  );
}

const CATEGORY_META: { id: CsSlotKind; key: 'clHearing' | 'clPhone' | 'clDatetime'; icon: string }[] = [
  { id: 'hearing', key: 'clHearing', icon: 'lucide:headphones' },
  { id: 'phone', key: 'clPhone', icon: 'lucide:phone' },
  { id: 'datetime', key: 'clDatetime', icon: 'lucide:calendar-clock' },
];

function SlotEditor({ node, slot, onChange }: { node: FlowNode; slot: CsSlot; onChange: (s: CsSlot) => void }) {
  const t = useT();
  const ir = useFlowStore((s) => s.ir);
  const changeKind = (kind: CsSlotKind) => {
    if (kind === slot.kind) return;
    onChange(defaultSlot(kind, ir, node.id));
  };
  return (
    <>
      <div className="flex gap-1.5">
        {CATEGORY_META.map((c) => (
          <button
            key={c.id}
            type="button"
            onClick={() => changeKind(c.id)}
            className={[
              'flex flex-1 items-center justify-center gap-1.5 rounded-lg border px-2 py-1.5 text-[11.5px] font-semibold transition',
              slot.kind === c.id
                ? 'border-[var(--bk-accent)] bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]'
                : 'border-[var(--bk-border)] text-[var(--bk-text-muted)] hover:border-[var(--bk-accent)]',
            ].join(' ')}
          >
            <Icon icon={c.icon} width={13} height={13} />
            {t(c.key)}
          </button>
        ))}
      </div>
      {slot.kind === 'hearing' && <HearingSlot node={node} slot={slot} onChange={onChange} />}
      {slot.kind === 'phone' && <PhoneSlot slot={slot} onChange={onChange} />}
      {slot.kind === 'datetime' && <DatetimeSlot slot={slot} onChange={onChange} />}
    </>
  );
}

// 聴取内容: node + danh sách giá trị tự nhập (thêm/bớt, không toán tử).
function HearingSlot({ node, slot, onChange }: { node: FlowNode; slot: CsSlot; onChange: (s: CsSlot) => void }) {
  const t = useT();
  const ir = useFlowStore((s) => s.ir);
  const options = hearingSourceOptions(ir, node.id);
  const values = slot.values ?? [''];
  const setValues = (v: string[]) => onChange({ ...slot, values: v });
  return (
    <div className="space-y-2">
      <div>
        <span className="mb-1 block text-[11px] font-semibold text-[var(--bk-text-muted)]">{t('clWhichHearing')}</span>
        <select
          className={inputClass}
          value={slot.nodeId ?? ''}
          aria-label={t('clWhichHearing')}
          onChange={(e) => onChange({ ...slot, nodeId: e.target.value })}
        >
          {options.length === 0 && <option value="">—</option>}
          {options.map((o) => (
            <option key={o.id} value={o.id}>
              {o.label}
            </option>
          ))}
        </select>
      </div>
      <div>
        <span className="mb-1 block text-[11px] font-semibold text-[var(--bk-text-muted)]">{t('clValues')}</span>
        <div className="space-y-1.5">
          {values.map((v, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <input
                type="text"
                className={inputClass}
                value={v}
                placeholder={t('clValues')}
                aria-label={`${t('clValues')} ${i + 1}`}
                onChange={(e) => setValues(values.map((x, j) => (j === i ? e.target.value : x)))}
              />
              <IconBtn
                icon="lucide:x"
                title="×"
                danger
                disabled={values.length <= 1}
                onClick={() => setValues(values.filter((_, j) => j !== i))}
              />
            </div>
          ))}
          <AddButton label={t('clAddValue')} onClick={() => setValues([...values, ''])} />
        </div>
      </div>
    </div>
  );
}

// 電話番号: 着信/聴取 → liệt kê TẤT CẢ 種別 (cố định, read-only).
function PhoneSlot({ slot, onChange }: { slot: CsSlot; onChange: (s: CsSlot) => void }) {
  const t = useT();
  const kind = slot.phoneKind ?? 'incoming';
  const values = phoneValuesFor(kind);
  return (
    <div className="space-y-2">
      <div className="flex gap-1.5">
        <SubToggle label={t('clIncoming')} on={kind === 'incoming'} onClick={() => onChange({ ...slot, phoneKind: 'incoming' })} />
        <SubToggle label={t('clAnswered')} on={kind === 'answered'} onClick={() => onChange({ ...slot, phoneKind: 'answered' })} />
      </div>
      <div className="flex items-center gap-1.5 text-[10.5px] font-semibold text-[var(--bk-text-faint)]">
        <Icon icon="lucide:lock" width={11} height={11} />
        {t('clPhoneAllNote')}
      </div>
      <div className="flex flex-wrap gap-1.5">
        {values.map((v) => (
          <span
            key={v}
            className="rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-2.5 py-1 text-xs font-semibold text-[var(--bk-text)]"
          >
            {v}
          </span>
        ))}
      </div>
    </div>
  );
}

// 着信日時: 日付 / 曜日 / 時間.
function DatetimeSlot({ slot, onChange }: { slot: CsSlot; onChange: (s: CsSlot) => void }) {
  const t = useT();
  const lang = useLang((s) => s.lang);
  const dtKind = slot.dtKind ?? 'time';
  const ranges = slot.ranges ?? [];
  const days = slot.days ?? [];

  const setRanges = (r: CsRange[]) => onChange({ ...slot, ranges: r });
  const setDays = (d: DayKey[]) => onChange({ ...slot, days: d });

  return (
    <div className="space-y-2">
      <div className="flex gap-1.5">
        <SubToggle label={t('clDate')} on={dtKind === 'date'} onClick={() => onChange({ kind: 'datetime', dtKind: 'date', ranges: [{ from: '', to: '' }], days: [] })} />
        <SubToggle label={t('clDay')} on={dtKind === 'day'} onClick={() => onChange({ kind: 'datetime', dtKind: 'day', ranges: [], days: [] })} />
        <SubToggle label={t('clTime')} on={dtKind === 'time'} onClick={() => onChange({ kind: 'datetime', dtKind: 'time', ranges: [{ from: '09:00', to: '17:00' }], days: [] })} />
      </div>

      {dtKind === 'date' && (
        <div className="space-y-1.5">
          {ranges.map((r, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <Icon icon="lucide:clock" width={14} height={14} className="shrink-0 text-[var(--bk-text-faint)]" />
              <input
                type="date"
                className={`${inputClass} min-w-0 flex-1`}
                value={r.from}
                aria-label="from"
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, from: e.target.value } : x)))}
              />
              <span className="shrink-0 text-xs text-[var(--bk-text-faint)]">〜</span>
              <input
                type="date"
                className={`${inputClass} min-w-0 flex-1`}
                value={r.to}
                aria-label="to"
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, to: e.target.value } : x)))}
              />
              <IconBtn icon="lucide:x" title="×" danger onClick={() => setRanges(ranges.filter((_, j) => j !== i))} />
            </div>
          ))}
          <AddButton label={t('clAddRange')} onClick={() => setRanges([...ranges, { from: '', to: '' }])} />
        </div>
      )}

      {dtKind === 'day' && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-1.5">
            {DAY_KEYS.map((d) => {
              const on = days.includes(d);
              return (
                <button
                  key={d}
                  type="button"
                  onClick={() => setDays(on ? days.filter((x) => x !== d) : [...days, d])}
                  className={[
                    'h-8 w-9 rounded-lg border text-xs font-bold transition',
                    on
                      ? 'border-[var(--bk-accent)] bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]'
                      : 'border-[var(--bk-border)] text-[var(--bk-text-muted)] hover:border-[var(--bk-accent)]',
                  ].join(' ')}
                >
                  {CS_DAY_LABELS[d][lang]}
                </button>
              );
            })}
          </div>
          <RemainderRow label={t('clRemainder')} text={dayRemainder(days).map((d) => CS_DAY_LABELS[d][lang]).join('・') || '—'} />
        </div>
      )}

      {dtKind === 'time' && (
        <div className="space-y-1.5">
          {ranges.map((r, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <input
                type="time"
                className={`${inputClass} min-w-0 flex-1`}
                value={r.from}
                aria-label="from"
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, from: e.target.value } : x)))}
              />
              <span className="shrink-0 text-xs text-[var(--bk-text-faint)]">〜</span>
              <input
                type="time"
                className={`${inputClass} min-w-0 flex-1`}
                value={r.to}
                aria-label="to"
                onChange={(e) => setRanges(ranges.map((x, j) => (j === i ? { ...x, to: e.target.value } : x)))}
              />
              <IconBtn icon="lucide:x" title="×" danger onClick={() => setRanges(ranges.filter((_, j) => j !== i))} />
            </div>
          ))}
          <AddButton label={t('clAddRange')} onClick={() => setRanges([...ranges, { from: '', to: '' }])} />
          {timeRemainderRanges(ranges).map((r, i) => (
            <RemainderRow key={i} label={t('clRemainder')} text={`${r.from} 〜 ${r.to}`} />
          ))}
        </div>
      )}
    </div>
  );
}

function RemainderRow({ label, text }: { label: string; text: string }) {
  return (
    <div className="flex items-center gap-2 rounded-lg border border-dashed border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-2.5 py-1.5 text-xs text-[var(--bk-text-faint)]">
      <span className="rounded bg-[var(--bk-border)] px-1.5 py-0.5 text-[10px] font-bold text-[var(--bk-text-muted)]">
        {label}
      </span>
      <span className="text-[var(--bk-text)]">{text}</span>
    </div>
  );
}

// ── Tab 分岐設定: danh sách nhánh = tích các điều kiện ────────────────────────
export function CsLogicBranchList({ node }: { node: FlowNode }) {
  const t = useT();
  const draft = useFlowStore((s) => s.draft);
  const ir = useFlowStore((s) => s.ir);
  const data = draft?.data ?? node.data;
  const slots = readCsSlots(data);
  const branches = csProductBranches(slots);

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2 rounded-lg border border-dashed border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-xs text-[var(--bk-text-muted)]">
        <Icon icon="lucide:git-fork" width={14} height={14} className="shrink-0 text-[var(--bk-accent)]" />
        {t('clBranchAuto')}
      </div>

      {branches.length === 0 ? (
        <p className="px-1 text-sm text-[var(--bk-text-faint)]">{t('clNoValue')}</p>
      ) : (
        <div className="space-y-1.5">
          {branches.map((b, i) => (
            <div
              key={b.id}
              className="flex items-start gap-2 rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface)] px-2.5 py-2"
            >
              <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-md bg-[var(--bk-accent-soft)] px-1 text-[11px] font-bold text-[var(--bk-accent)]">
                {i + 1}
              </span>
              <span className="flex flex-wrap items-center gap-1.5 text-sm text-[var(--bk-text)]">
                {b.parts.map((p, j) => (
                  <span key={j} className="inline-flex items-center gap-1.5">
                    {j > 0 && <span className="text-[var(--bk-text-faint)]">×</span>}
                    <span className="rounded-md border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-2 py-0.5 text-xs font-semibold">
                      {p}
                    </span>
                  </span>
                ))}
              </span>
            </div>
          ))}
          <div className="flex items-center gap-2 rounded-lg border border-dashed border-[var(--bk-border)] px-2.5 py-2 text-sm text-[var(--bk-text-muted)]">
            <span className="flex h-5 min-w-5 shrink-0 items-center justify-center rounded-md bg-[var(--bk-surface-2)] px-1 text-[11px] font-bold text-[var(--bk-text-faint)]">
              {branches.length + 1}
            </span>
            {CS_ELSE_LABEL}
          </div>
        </div>
      )}

      {/* Nhắc: 聴取ノード đã bị xoá → tên node trong điều kiện có thể lệch. */}
      {slots.some((s) => s.kind === 'hearing' && s.nodeId && !ir?.nodes.some((n) => n.id === s.nodeId)) && (
        <p className="px-1 text-xs text-rose-500">
          {slots
            .filter((s) => s.kind === 'hearing' && s.nodeId)
            .map((s) => hearingNodeLabel(s.nodeId ?? '', ir))
            .join(', ')}
        </p>
      )}
    </div>
  );
}

// ── UI phụ ───────────────────────────────────────────────────────────────────
function SubToggle({ label, on, onClick }: { label: string; on: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        'flex-1 rounded-lg border px-2 py-1.5 text-[11.5px] font-bold transition',
        on
          ? 'border-[var(--bk-accent)] bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]'
          : 'border-[var(--bk-border)] text-[var(--bk-text-muted)] hover:border-[var(--bk-accent)]',
      ].join(' ')}
    >
      {label}
    </button>
  );
}

function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 rounded-lg border border-dashed border-[var(--bk-border)] px-3 py-1.5 text-xs font-semibold text-[var(--bk-text-muted)] transition hover:border-[var(--bk-accent)] hover:text-[var(--bk-accent)]"
    >
      <Icon icon="lucide:plus" width={12} height={12} />
      {label}
    </button>
  );
}

function IconBtn({
  icon,
  title,
  onClick,
  disabled,
  danger,
}: {
  icon: string;
  title: string;
  onClick: () => void;
  disabled?: boolean;
  danger?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      title={title}
      aria-label={title}
      className={[
        'flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[var(--bk-text-faint)] transition',
        disabled
          ? 'cursor-not-allowed opacity-30'
          : danger
            ? 'hover:bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:text-rose-500'
            : 'hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]',
      ].join(' ')}
    >
      <Icon icon={icon} width={14} height={14} />
    </button>
  );
}
