import { create } from 'zustand';
import { AiError, chatComplete } from '../ai/openai';
import { buildChatMessages, parseChatReply } from '../ai/chatPrompt';
import { buildFlowDigest } from '../ai/flowDigest';
import type { EditOp } from '../ai/editOps';
import { useFlowStore } from './flowStore';

// ─────────────────────────────────────────────────────────────────────────────
// Store cho panel AI Chat (trợ lý sửa flow bằng hội thoại).
//   - Gửi yêu cầu -> proxy OpenAI (JSON edit-ops) -> gõ dần phần trả lời (typing).
//   - Mỗi câu trả lời có thể kèm "đề xuất thay đổi" (ops) chờ người dùng Áp dụng/Bỏ.
//   - "Dừng": abort fetch hoặc kết thúc typing ngay.
// Nội dung hiển thị bằng ngôn ngữ người dùng do AI tự sinh (reply). Thông báo lỗi
// giữ ở dạng errorKey (i18n) để component dịch — store không đụng i18n.
// ─────────────────────────────────────────────────────────────────────────────

export type ChatRole = 'user' | 'assistant';

export interface ChatMsg {
  id: string;
  role: ChatRole;
  text: string;
  ops?: EditOp[]; // assistant: đề xuất thay đổi
  opsState?: 'pending' | 'applied' | 'rejected';
  errorKey?: string; // assistant: lỗi (TKey) thay cho text
  typing?: boolean; // đang gõ dần
}

type Status = 'idle' | 'thinking' | 'typing';

interface AiChatState {
  open: boolean;
  status: Status;
  messages: ChatMsg[];
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;
  send: (text: string) => Promise<void>;
  stop: () => void;
  applyOps: (msgId: string) => Promise<void>;
  rejectOps: (msgId: string) => void;
  resetConversation: () => void;
}

// Trạng thái điều khiển ngoài React state (không cần re-render): fetch controller +
// timer typing + nội dung đầy đủ đang gõ (để "Dừng" ghi hết ngay).
let activeController: AbortController | null = null;
let typingTimer: ReturnType<typeof setTimeout> | null = null;
let msgSeq = 0;
const nextId = () => `m${++msgSeq}`;

// AiError.code -> TKey lỗi (đồng bộ với AiFieldExtras).
function errorKeyOf(e: unknown): string {
  if (e instanceof AiError) {
    if (e.code === 'no-config') return 'aiErrNoKey';
    if (e.code === 'no-auth' || e.code === 'unauthorized') return 'aiErrAuth';
  }
  return 'aiErrCall';
}

// Tên flow đang mở (main / tên sub flow) — cho digest.
function activeFlowName(): string {
  const { ir, activeFlowId } = useFlowStore.getState();
  if (activeFlowId === 'main') return 'Main Flow';
  return (ir?.subflows ?? []).find((s) => s.id === activeFlowId)?.name ?? activeFlowId;
}

export const useAiChatStore = create<AiChatState>((set, get) => {
  // Cập nhật 1 message theo id.
  const patchMsg = (id: string, patch: Partial<ChatMsg>) =>
    set({ messages: get().messages.map((m) => (m.id === id ? { ...m, ...patch } : m)) });

  // Gõ dần `full` vào message `id` (typing). Xong -> status idle.
  const typeOut = (id: string, full: string) => {
    set({ status: 'typing' });
    const chunk = Math.max(1, Math.round(full.length / 140));
    let shown = 0;
    const step = () => {
      shown = Math.min(full.length, shown + chunk);
      patchMsg(id, { text: full.slice(0, shown) });
      if (shown >= full.length) {
        patchMsg(id, { typing: false });
        set({ status: 'idle' });
        typingTimer = null;
        return;
      }
      typingTimer = setTimeout(step, 16);
    };
    step();
  };

  return {
    open: false,
    status: 'idle',
    messages: [],

    openPanel: () => set({ open: true }),
    closePanel: () => set({ open: false }),
    togglePanel: () => set({ open: !get().open }),

    send: async (raw) => {
      const text = raw.trim();
      if (!text || get().status !== 'idle') return;

      const userMsg: ChatMsg = { id: nextId(), role: 'user', text };
      set({ messages: [...get().messages, userMsg], status: 'thinking' });

      const ir = useFlowStore.getState().ir;
      if (!ir) {
        set({
          messages: [...get().messages, { id: nextId(), role: 'assistant', text: '', errorKey: 'aiChatNoFlow' }],
          status: 'idle',
        });
        return;
      }

      // Lịch sử hội thoại cho model: chỉ text user/assistant hợp lệ (bỏ message lỗi).
      const history = get()
        .messages.filter((m) => !m.errorKey && (m.role === 'user' || m.role === 'assistant'))
        .map((m) => ({ role: m.role, content: m.text }));

      const digest = buildFlowDigest(ir, activeFlowName());
      const messages = buildChatMessages(digest, history);

      activeController = new AbortController();
      try {
        const rawReply = await chatComplete(messages, { json: true, signal: activeController.signal });
        activeController = null;
        const parsed = parseChatReply(rawReply);
        if (!parsed) {
          set({
            messages: [...get().messages, { id: nextId(), role: 'assistant', text: '', errorKey: 'aiChatParseErr' }],
            status: 'idle',
          });
          return;
        }
        const id = nextId();
        const hasOps = parsed.ops.length > 0;
        const assistant: ChatMsg = {
          id,
          role: 'assistant',
          text: '',
          typing: true,
          ...(hasOps ? { ops: parsed.ops, opsState: 'pending' as const } : {}),
        };
        set({ messages: [...get().messages, assistant] });
        typeOut(id, parsed.reply || '');
      } catch (e) {
        activeController = null;
        // Bấm "Dừng" -> AbortError: dừng im lặng (đã đưa status idle ở stop()).
        if (e instanceof DOMException && e.name === 'AbortError') return;
        set({
          messages: [...get().messages, { id: nextId(), role: 'assistant', text: '', errorKey: errorKeyOf(e) }],
          status: 'idle',
        });
      }
    },

    stop: () => {
      // Đang gọi API -> abort fetch. Đang gõ -> ghi hết ngay & dừng timer.
      if (activeController) {
        activeController.abort();
        activeController = null;
      }
      if (typingTimer) {
        clearTimeout(typingTimer);
        typingTimer = null;
        const last = [...get().messages].reverse().find((m) => m.typing);
        if (last) patchMsg(last.id, { typing: false });
      }
      set({ status: 'idle' });
    },

    applyOps: async (msgId) => {
      const msg = get().messages.find((m) => m.id === msgId);
      if (!msg || !msg.ops || msg.opsState !== 'pending') return;
      try {
        const ok = await useFlowStore.getState().applyAiOps(msg.ops);
        if (ok) patchMsg(msgId, { opsState: 'applied' });
      } catch {
        // Áp lỗi -> giữ trạng thái pending để người dùng thử lại.
      }
    },

    rejectOps: (msgId) => {
      const msg = get().messages.find((m) => m.id === msgId);
      if (!msg || msg.opsState !== 'pending') return;
      patchMsg(msgId, { opsState: 'rejected' });
    },

    resetConversation: () => {
      if (activeController) {
        activeController.abort();
        activeController = null;
      }
      if (typingTimer) {
        clearTimeout(typingTimer);
        typingTimer = null;
      }
      set({ messages: [], status: 'idle' });
    },
  };
});
