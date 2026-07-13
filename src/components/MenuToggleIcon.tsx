import { useRef } from 'react';
import { Icon } from '../ui/icons';

// ─────────────────────────────────────────────────────────────────────────────
// Icon cho nút mở/đóng panel menu, có transition mượt của line-md:
//   • Lần đầu load (chưa mở bao giờ): hamburger tĩnh `line-md:menu`.
//   • Khi mở panel: morph hamburger → X (`line-md:menu-to-close-transition`).
//   • Khi đóng panel (bấm lại hoặc click ra ngoài): morph X → hamburger
//     (`line-md:close-to-menu-transition`).
// Icon line-md chạy animation SMIL 1 lần lúc mount, nên dùng `key` = tên icon để
// React remount <svg> mỗi lần đổi trạng thái → animation luôn chạy lại, không kẹt.
// ─────────────────────────────────────────────────────────────────────────────

export function MenuToggleIcon({ open, size = 22 }: { open: boolean; size?: number }) {
  // Đánh dấu đã từng mở: trước lần mở đầu tiên hiển thị icon tĩnh (không morph).
  const openedOnce = useRef(false);
  if (open) openedOnce.current = true;

  const icon = !openedOnce.current
    ? 'line-md:menu'
    : open
      ? 'line-md:menu-to-close-transition'
      : 'line-md:close-to-menu-transition';

  return <Icon key={icon} icon={icon} width={size} height={size} />;
}
