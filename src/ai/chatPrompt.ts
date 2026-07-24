import type { ChatMessage } from './openai';
import { parseEditOps, type EditOp } from './editOps';

// ─────────────────────────────────────────────────────────────────────────────
// Prompt cho AI Chat (trợ lý sửa flow). Bố trí để TẬN DỤNG prompt caching của
// OpenAI: phần BẤT BIẾN (role + glossary + hợp đồng ops) đặt LÊN ĐẦU làm prefix cố
// định → các lượt sau tính rẻ hơn. Phần thay đổi (digest flow) là message riêng.
// ─────────────────────────────────────────────────────────────────────────────

// Prefix cố định — KHÔNG chèn dữ liệu động vào đây (giữ nguyên để cache-hit).
export const CHAT_SYSTEM_PREFIX = `You are an assistant that edits an "AI電話" (Brekeke-based) call flow (IVR) shown as a node graph.
The user describes changes in Vietnamese or Japanese. You DO NOT edit anything directly — you return a JSON object describing the change as a list of edit operations that the app applies after the user reviews them.

NODE TYPES:
- start: entry point (exactly one, only in the main flow). NEVER add or remove it.
- announce: plays TTS/audio. Main text in data.text.
- interaction: asks the caller and collects DTMF/speech. Question text in data.announce.
- nexus: branches by condition.
- logic / classifier / normalization: logic modules (script / classifiers / phone·DOB normalization).
- openai: calls an LLM. Prompt in data.prompt.
- faq: FAQ answering. transfer: transfer the call (data.number). save: save data / set status flag. jump: jump to a sub flow (data.subflow = sub flow name). hangup: end the call.

OUTPUT — return ONLY a single JSON object, no markdown, no prose outside it:
{
  "reply": "<a short, friendly explanation in the SAME language the user used>",
  "ops": [ <edit operations, may be empty> ]
}

EDIT OPERATIONS:
- {"op":"addNode","tempId":"t1","nodeType":"interaction","label":"電話番号の確認","data":{"announce":"..."}}
- {"op":"updateNode","id":"<existing node id>","label":"<optional>","data":{<fields to merge>}}
- {"op":"removeNode","id":"<existing node id>"}
- {"op":"addEdge","source":"<id or tempId>","target":"<id or tempId>","condition":"<optional>","label":"<optional>"}
- {"op":"removeEdge","source":"<id>","target":"<id>"}

RULES:
- Reference existing nodes by the exact id shown in the flow digest.
- For nodes you create, set a tempId and reference that tempId in edges within the same response.
- Set announce/interaction wording in data.text / data.announce as appropriate.
- Keep ops MINIMAL — only what the request needs. Do not restructure unrelated parts.
- If the request needs no change, return "ops": [] and explain why in "reply".
- Node positions are computed automatically — never include positions.`;

// Dựng danh sách message gửi proxy: [prefix cố định] + [digest flow] + [lịch sử hội thoại].
// history: các lượt user/assistant trước (assistant chỉ nên là phần reply, không kèm ops JSON).
export function buildChatMessages(
  digest: string,
  history: { role: 'user' | 'assistant'; content: string }[],
): ChatMessage[] {
  return [
    { role: 'system', content: CHAT_SYSTEM_PREFIX },
    { role: 'system', content: `CURRENT FLOW (digest):\n${digest}` },
    ...history,
  ];
}

export interface ParsedChatReply {
  reply: string;
  ops: EditOp[];
}

// Lấy object JSON đầu tiên trong chuỗi (phòng khi model kèm text thừa quanh JSON).
function extractJsonObject(text: string): string | null {
  const start = text.indexOf('{');
  if (start < 0) return null;
  let depth = 0;
  let inStr = false;
  let esc = false;
  for (let i = start; i < text.length; i++) {
    const ch = text[i];
    if (inStr) {
      if (esc) esc = false;
      else if (ch === '\\') esc = true;
      else if (ch === '"') inStr = false;
    } else if (ch === '"') inStr = true;
    else if (ch === '{') depth++;
    else if (ch === '}') {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}

// Parse phản hồi AI -> { reply, ops }. Trả null nếu không đọc được JSON.
export function parseChatReply(raw: string): ParsedChatReply | null {
  const json = extractJsonObject(raw);
  if (!json) return null;
  let obj: unknown;
  try {
    obj = JSON.parse(json);
  } catch {
    return null;
  }
  if (!obj || typeof obj !== 'object') return null;
  const o = obj as Record<string, unknown>;
  const reply = typeof o.reply === 'string' ? o.reply.trim() : '';
  const ops = parseEditOps(o.ops);
  return { reply, ops };
}
