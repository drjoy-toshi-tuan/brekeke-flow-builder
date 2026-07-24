import { Icon } from '../ui/icons';

// ─────────────────────────────────────────────────────────────────────────────
// Icon "AI" dùng CHUNG cho mọi chỗ AI (nút AI Generate ở node Logic/script,
// node OpenAI màn TS, lớp phủ loading, panel AI Chat). Dùng icon mingcute:ai-fill
// + hiệu ứng lấp lánh (twinkle) ở class .bk-ai-fill-twinkle (định nghĩa ở index.css).
// Trước đây là 2 ngôi sao tự vẽ; nay thống nhất 1 icon để đồng bộ toàn app.
// ─────────────────────────────────────────────────────────────────────────────

export function AiSparkleIcon({ size = 16 }: { size?: number }) {
  return (
    <Icon
      icon="mingcute:ai-fill"
      width={size}
      height={size}
      className="bk-ai-fill-twinkle"
      aria-hidden
    />
  );
}
