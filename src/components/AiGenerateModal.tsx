import { useEffect, useMemo, useRef, useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import {
  buildGenerateSystemPrompt,
  detectQuestionNodeId,
  questionCandidates,
  type GenerateKind,
  type QuestionCandidate,
} from '../ai/context';
import { useT } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { AiSparkleIcon } from './AiSparkleIcon';

// ─────────────────────────────────────────────────────────────────────────────
// Modal "AI Generate" cho script (node Logic) / prompt (node OpenAI).
// Bố cục:
//   1. Chọn node có announce tương ứng để tạo Question Context — tự phát hiện, đổi được.
//   2. Ô bối cảnh read-only: #Role -> #Scenario Flow Context -> #Question Context
//      (announce tự fill + highlight để thấy nó liên động khi đổi node).
//   3. Ô chỉ thị của người dùng (phần chính) + nút Generate.
// Bấm Generate: modal ĐÓNG NGAY, việc gọi OpenAI + gõ chữ vào ô code/prompt do
// component field (AiFieldExtras) lo — nên modal chỉ dựng request rồi trao đi.
// Modal cao tối đa 88vh, thân cuộn được -> kéo textarea cao vẫn không đẩy footer.
// Màu chủ đạo tím #d946ef (đồng bộ với nút AI Generate).
// ─────────────────────────────────────────────────────────────────────────────

const AI_PURPLE = '#d946ef';

// Yêu cầu sinh gửi cho field xử lý (system prompt đã dựng + chỉ thị người dùng).
export interface AiGenerateRequest {
  system: string;
  user: string;
}

interface AiGenerateModalProps {
  kind: GenerateKind;
  nodeId: string; // node logic/openai đang sửa
  current: string; // code/prompt hiện có trong draft
  onGenerate: (req: AiGenerateRequest) => void; // trao request cho field (đóng modal + tự gõ)
  onClose: () => void;
}

export function AiGenerateModal({ kind, nodeId, current, onGenerate, onClose }: AiGenerateModalProps) {
  const t = useT();
  const ir = useFlowStore((s) => s.ir);
  const exportYaml = useFlowStore((s) => s.exportYaml);
  // Tài liệu đầy đủ (main + sub flow) — ứng viên câu hỏi lấy xuyên flow.
  const doc = useMemo(() => useFlowStore.getState().assembleDoc(), [ir]); // eslint-disable-line react-hooks/exhaustive-deps
  const candidates = useMemo(() => questionCandidates(doc), [doc]);

  // Node câu hỏi: tự phát hiện (nối trực tiếp hoặc qua nexus) — người dùng đổi được.
  const [questionId, setQuestionId] = useState<string>(() => detectQuestionNodeId(doc, nodeId) ?? '');
  const question = candidates.find((c) => c.id === questionId) ?? null;
  const announce = question?.announce.trim() ?? '';

  const [userPrompt, setUserPrompt] = useState('');

  // Bấm Generate: dựng system prompt rồi TRAO cho field xử lý (gọi OpenAI + gõ chữ),
  // đóng modal ngay. Không tự gọi API ở đây nữa.
  const handleGenerate = () => {
    if (!userPrompt.trim()) return;
    const system = buildGenerateSystemPrompt(kind, {
      yaml: exportYaml(),
      questionAnnounce: announce,
      current,
    });
    onGenerate({ system, user: userPrompt.trim() });
    onClose();
  };

  const roleKey = kind === 'script' ? 'aiRoleScript' : 'aiRolePrompt';

  return (
    <div className="bk-modal-overlay bk-modal-overlay--fixed" role="dialog" aria-modal="true" onClick={onClose}>
      {/* Flex-col + max-h: thân cuộn, footer luôn cố định (không bị textarea đẩy khỏi màn hình). */}
      <div
        className="flex max-h-[88vh] w-full max-w-[620px] flex-col overflow-hidden rounded-2xl border border-[var(--bk-border)] bg-[var(--bk-surface)] shadow-[var(--bk-shadow)]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex shrink-0 items-center gap-2 border-b border-[var(--bk-border)] px-5 py-3.5 text-sm font-bold text-[var(--bk-text)]">
          <span
            className="flex h-7 w-7 items-center justify-center rounded-lg"
            style={{ color: AI_PURPLE, background: `color-mix(in srgb, ${AI_PURPLE} 16%, transparent)` }}
          >
            <AiSparkleIcon size={18} />
          </span>
          {t('aiGenerate')}
        </div>

        {/* Thân cuộn được */}
        <div className="flex-1 space-y-3 overflow-y-auto px-5 py-4">
          {/* 1. Node câu hỏi (trên cùng) — bộ chọn tự vẽ để hiện icon Main/Sub flow. */}
          <label className="block">
            <span className="text-xs font-medium text-[var(--bk-text-muted)]">{t('aiQuestionNode')}</span>
            <QuestionNodeSelect
              candidates={candidates}
              value={questionId}
              onChange={setQuestionId}
            />
          </label>

          {/* 2. Bối cảnh read-only. Thứ tự: #Role -> #Scenario Flow Context -> #Question Context. */}
          <div className="space-y-2 rounded-xl border border-[var(--bk-border)] bg-[var(--bk-surface-2)] p-3 text-xs leading-relaxed">
            <div>
              <div className="font-mono font-bold text-[var(--bk-text-muted)]">#Role</div>
              <p className="mt-0.5 text-[var(--bk-text-muted)]">{t(roleKey)}</p>
            </div>
            <div>
              <div className="font-mono font-bold text-[var(--bk-text-muted)]">#Scenario Flow Context</div>
              <p className="mt-0.5 text-[var(--bk-text-muted)]">{t('aiScenarioContext')}</p>
            </div>
            <div>
              <div className="font-mono font-bold text-[var(--bk-text-muted)]">#Question Context</div>
              <div className="mt-1">
                {announce ? (
                  // Highlight (nền tím nhạt) để thấy nội dung liên động theo node đã chọn.
                  <span
                    className="whitespace-pre-wrap rounded px-1.5 py-0.5 font-medium text-[var(--bk-text)]"
                    style={{ background: `color-mix(in srgb, ${AI_PURPLE} 16%, transparent)` }}
                  >
                    {announce}
                  </span>
                ) : (
                  <span className="italic text-[var(--bk-text-faint)]">{t('aiContextNone')}</span>
                )}
              </div>
            </div>
          </div>

          {/* 3. Chỉ thị của người dùng (phần chính) */}
          <label className="block">
            <span className="text-xs font-medium text-[var(--bk-text-muted)]">{t('aiUserPrompt')}</span>
            <textarea
              autoFocus
              className="mt-1 max-h-[40vh] w-full resize-y rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-sm text-[var(--bk-text)] outline-none transition focus:border-[var(--bk-accent)]"
              rows={5}
              value={userPrompt}
              placeholder={t('aiUserPromptPh')}
              onChange={(e) => setUserPrompt(e.target.value)}
            />
          </label>
        </div>

        {/* Footer cố định */}
        <div className="flex shrink-0 justify-end gap-2 border-t border-[var(--bk-border)] px-5 py-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-[var(--bk-border)] px-4 py-2 text-sm font-semibold text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
          >
            {t('btnCancel')}
          </button>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={!userPrompt.trim()}
            className="flex items-center gap-2 rounded-lg px-5 py-2 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
            style={{ background: AI_PURPLE }}
          >
            <AiSparkleIcon size={16} />
            {t('aiGenerateBtn')}
          </button>
        </div>
      </div>
    </div>
  );
}

// Icon Main/Sub flow — cùng bộ với panel cài đặt flow (FlowsPanel).
const FLOW_ICON_MAIN = 'tabler:square-rounded-letter-m-filled';
const FLOW_ICON_SUB = 'tabler:square-rounded-letter-s-filled';

// Bộ chọn node câu hỏi. Native <select> không render được icon, nên tự vẽ dropdown:
//   - Option "không chọn" -> chỉ 1 dấu gạch "—".
//   - Các option khác -> tên node + icon Main/Sub flow (bỏ text "— <flow>").
function QuestionNodeSelect({
  candidates,
  value,
  onChange,
}: {
  candidates: QuestionCandidate[];
  value: string;
  onChange: (id: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const selected = candidates.find((c) => c.id === value) ?? null;

  // Click ra ngoài -> đóng dropdown.
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open]);

  return (
    <div className="relative mt-1" ref={wrapRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface-2)] px-3 py-2 text-left text-sm text-[var(--bk-text)] outline-none transition focus:border-[var(--bk-accent)]"
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        {selected ? (
          <>
            <span className="min-w-0 flex-1 truncate">{selected.label}</span>
            <Icon
              icon={selected.isMain ? FLOW_ICON_MAIN : FLOW_ICON_SUB}
              width={16}
              height={16}
              className="shrink-0 text-[var(--bk-text-muted)]"
            />
          </>
        ) : (
          <span className="flex-1 text-[var(--bk-text-muted)]">—</span>
        )}
        <Icon icon="lucide:chevron-down" width={16} height={16} className="shrink-0 text-[var(--bk-text-faint)]" />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute left-0 right-0 top-full z-30 mt-1 max-h-56 overflow-y-auto rounded-lg border border-[var(--bk-border)] bg-[var(--bk-surface)] p-1 shadow-[var(--bk-shadow)]"
        >
          {/* Không chọn: chỉ 1 dấu gạch. */}
          <button
            type="button"
            role="option"
            aria-selected={value === ''}
            onClick={() => {
              onChange('');
              setOpen(false);
            }}
            className={`flex w-full items-center rounded-md px-2.5 py-1.5 text-left text-sm transition hover:bg-[var(--bk-surface-2)] ${
              value === '' ? 'text-[var(--bk-accent)]' : 'text-[var(--bk-text-muted)]'
            }`}
          >
            —
          </button>
          {candidates.map((c) => (
            <button
              key={c.id}
              type="button"
              role="option"
              aria-selected={value === c.id}
              onClick={() => {
                onChange(c.id);
                setOpen(false);
              }}
              className={`flex w-full items-center gap-2 rounded-md px-2.5 py-1.5 text-left text-sm transition hover:bg-[var(--bk-surface-2)] ${
                value === c.id ? 'bg-[var(--bk-accent-soft)] font-semibold text-[var(--bk-accent)]' : 'text-[var(--bk-text)]'
              }`}
              title={`${c.label} · ${c.flowName}`}
            >
              <span className="min-w-0 flex-1 truncate">{c.label}</span>
              <Icon
                icon={c.isMain ? FLOW_ICON_MAIN : FLOW_ICON_SUB}
                width={16}
                height={16}
                className={`shrink-0 ${value === c.id ? 'text-[var(--bk-accent)]' : 'text-[var(--bk-text-muted)]'}`}
              />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
