import { useRef, type UIEvent } from 'react';

// ─────────────────────────────────────────────────────────────────────────────
// Editor code có tô sáng cú pháp — KHÔNG thêm thư viện (tech stack khoá cứng).
// Kỹ thuật: <textarea> trong suốt đặt CHỒNG lên <pre> đã highlight; cuộn đồng bộ.
// Bộ tô sáng là tokenizer JS tối giản bằng regex (đủ cho script Brekeke ES2021+).
// ─────────────────────────────────────────────────────────────────────────────

const KEYWORDS = new Set([
  'const', 'let', 'var', 'function', 'return', 'if', 'else', 'for', 'while', 'do',
  'switch', 'case', 'break', 'continue', 'new', 'typeof', 'instanceof', 'in', 'of',
  'this', 'class', 'extends', 'super', 'import', 'from', 'export', 'default', 'try',
  'catch', 'finally', 'throw', 'async', 'await', 'yield', 'void', 'delete',
]);
const LITERALS = new Set(['true', 'false', 'null', 'undefined']);

function escapeHtml(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Token: comment | chuỗi | số | định danh (để phân biệt keyword/literal). Phần còn
// lại (dấu, khoảng trắng) giữ nguyên (đã escape). Bắt theo thứ tự ưu tiên bằng | .
const TOKEN =
  /(\/\/[^\n]*|\/\*[\s\S]*?\*\/)|('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`)|(\b\d[\d_]*\.?\d*(?:e[+-]?\d+)?\b)|([A-Za-z_$][\w$]*)/gi;

function highlight(code: string): string {
  let out = '';
  let last = 0;
  for (let m = TOKEN.exec(code); m; m = TOKEN.exec(code)) {
    out += escapeHtml(code.slice(last, m.index));
    const [full, comment, str, num, ident] = m;
    if (comment != null) out += `<span class="tok-comment">${escapeHtml(full)}</span>`;
    else if (str != null) out += `<span class="tok-string">${escapeHtml(full)}</span>`;
    else if (num != null) out += `<span class="tok-number">${escapeHtml(full)}</span>`;
    else if (ident != null) {
      const cls = KEYWORDS.has(ident) ? 'tok-keyword' : LITERALS.has(ident) ? 'tok-literal' : '';
      out += cls ? `<span class="${cls}">${escapeHtml(full)}</span>` : escapeHtml(full);
    }
    last = m.index + full.length;
  }
  out += escapeHtml(code.slice(last));
  // Ký tự cuối là newline -> thêm khoảng trắng để dòng cuối vẫn cao đúng.
  return out + (code.endsWith('\n') || code === '' ? ' ' : '');
}

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  rows?: number;
}

export function CodeEditor({ value, onChange, rows = 12 }: CodeEditorProps) {
  const preRef = useRef<HTMLPreElement>(null);

  // Đồng bộ cuộn: textarea (trên) cuộn -> <pre> highlight (dưới) cuộn theo.
  const onScroll = (e: UIEvent<HTMLTextAreaElement>) => {
    const pre = preRef.current;
    if (!pre) return;
    pre.scrollTop = e.currentTarget.scrollTop;
    pre.scrollLeft = e.currentTarget.scrollLeft;
  };

  return (
    <div className="bk-code" style={{ height: `${rows * 1.5 + 1}em` }}>
      <pre ref={preRef} className="bk-code-pre" aria-hidden="true">
        <code dangerouslySetInnerHTML={{ __html: highlight(value) }} />
      </pre>
      <textarea
        className="bk-code-ta"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onScroll={onScroll}
        spellCheck={false}
        autoCapitalize="off"
        autoCorrect="off"
        wrap="off"
      />
    </div>
  );
}
