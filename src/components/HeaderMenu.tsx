import { useEffect, useRef, useState } from 'react';
import { useFileStore } from '../store/fileStore';
import { useWorkspaceStore } from '../store/workspaceStore';
import { useAuth } from '../auth/useAuth';
import { useTheme } from '../ui/theme';
import { useLang, useT } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { RoleBadge } from '../ui/RoleBadge';
import { SlideToggle } from './SlideToggle';
import { MenuBrandHeader } from './MenuBrandHeader';
import { MenuToggleIcon } from './MenuToggleIcon';
import { useSaveFlow } from './useSaveFlow';
import { usePermStore } from '../store/permStore';
import { resolveRole } from '../drive/permissions';

// ─────────────────────────────────────────────────────────────────────────────
// Menu dọc trên header (đóng/mở, animation giống "Thêm node"). Gom mọi chức năng
// từng nằm rời trên header: ngôn ngữ, theme, tự sắp xếp, xuất YAML, đăng xuất.
// (Cài đặt IVR Property đã chuyển sang panel Main/Sub Flow — xem FlowsPanel.)
// ─────────────────────────────────────────────────────────────────────────────

export function HeaderMenu() {
  const [open, setOpen] = useState(false);
  // Giữ menu mounted trong lúc chạy animation ĐÓNG.
  const [render, setRender] = useState(false);
  // Xác nhận đăng xuất (tránh bấm nhầm 1 phát là văng ra ngoài).
  const [confirmLogout, setConfirmLogout] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (open) setRender(true);
  }, [open]);
  // Click ra ngoài panel -> tự đóng menu (không cần bấm lại nút menu).
  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [open]);

  const currentFile = useFileStore((s) => s.current);
  const closeFile = useFileStore((s) => s.closeFile);
  const { user, signOut } = useAuth();
  // Quyền của user (owner/admin/user) để hiện badge dưới tên trong menu tài khoản.
  const admins = usePermStore((s) => s.admins);
  const role = resolveRole(user?.email, { admins });
  // Màn CS: nút quay về đọc là "シナリオ設計書管理へ戻る" (quản lý file thiết kế).
  const csMode = useWorkspaceStore((s) => s.mode === 'cs');
  const { theme, setTheme } = useTheme();
  const { lang, setLang } = useLang();
  const t = useT();
  // Lưu flow về repo — logic dùng chung (xem useSaveFlow). Nút Lưu đã chuyển xuống
  // dải tab (FlowActionsBar); menu này chỉ còn dùng để TỰ LƯU khi quay về màn quản lý.
  const { saving, canSave, saveToRepo: handleSaveToRepo } = useSaveFlow();

  // Phím tắt Ctrl/Cmd + Shift + S = lưu về repo (dùng ref để luôn gọi handler mới nhất).
  const saveRef = useRef(handleSaveToRepo);
  saveRef.current = handleSaveToRepo;
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.code === 'KeyS') {
        e.preventDefault();
        void saveRef.current();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  // "Về màn quản lý flow" = TỰ LƯU về repo rồi mới điều hướng; lưu lỗi thì ở lại
  // (hiện lỗi trong menu). Ở màn CS đây là đường quay về DUY NHẤT (không có panel
  // Main/Sub Flow); màn TS có cả 2 chỗ.
  const handleBackToManager = async () => {
    if (saving) return;
    if (canSave) {
      const ok = await handleSaveToRepo();
      if (!ok) return;
    }
    closeFile();
    useWorkspaceStore.getState().navigate({ screen: 'flow-management', fileId: null, tab: null });
    setOpen(false);
  };

  return (
    <div className="relative" ref={wrapRef}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="group flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--bk-border)] bg-[var(--bk-surface)] text-[var(--bk-text)] shadow-[var(--bk-shadow)] transition-all duration-200 hover:-translate-y-0.5 hover:border-[var(--bk-accent)] hover:text-[var(--bk-accent)] hover:shadow-md active:translate-y-0 active:scale-95"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-label={t('menu')}
        title={t('menu')}
      >
        <MenuToggleIcon open={open} />
      </button>

      {render && (
        <div
          role="menu"
          onAnimationEnd={(e) => {
            if (e.target === e.currentTarget && !open) setRender(false);
          }}
          className={`bk-addmenu bk-headermenu ${open ? 'bk-addmenu--in' : 'bk-addmenu--out'} absolute right-0 top-full z-30 mt-2 w-72 overflow-hidden rounded-2xl border border-[var(--bk-border)] bg-[var(--bk-surface)] p-2 shadow-[var(--bk-shadow)]`}
        >
          <MenuBrandHeader />
          {/* ── Cài đặt giao diện ── */}
          <MenuSection title={t('secInterface')} />
          <div className="bk-menu-row">
            <span className="bk-menu-row-label">{t('mLanguage')}</span>
            <SlideToggle
              value={lang}
              options={[
                { key: 'vi', icon: 'twemoji:flag-vietnam', title: 'Tiếng Việt' },
                { key: 'ja', icon: 'twemoji:flag-japan', title: '日本語' },
              ]}
              onChange={(k) => setLang(k as 'vi' | 'ja')}
              ariaLabel="Language"
            />
          </div>
          <div className="bk-menu-row">
            <span className="bk-menu-row-label">{t('mTheme')}</span>
            <SlideToggle
              value={theme}
              options={[
                { key: 'light', icon: 'line-md:sunny-loop' },
                { key: 'dark', icon: 'line-md:moon-alt-loop' },
              ]}
              onChange={(k) => setTheme(k as 'light' | 'dark')}
              ariaLabel="Theme"
              title={theme === 'dark' ? t('themeDark') : t('themeLight')}
            />
          </div>

          {/* ── Về màn quản lý flow — tự lưu về repo rồi mới điều hướng. ── */}
          {currentFile && (
            <>
              <div className="bk-menu-sep" />
              <button
                type="button"
                role="menuitem"
                className="bk-menu-item"
                onClick={() => void handleBackToManager()}
                disabled={saving}
              >
                <Icon
                  icon={saving ? 'lucide:loader-circle' : 'line-md:list-3-filled'}
                  width={16}
                  height={16}
                  className={`text-[var(--bk-accent)] ${saving ? 'animate-spin' : ''}`}
                />
                <span>{t(csMode ? 'csBackToManager' : 'fmBackToManager')}</span>
              </button>
            </>
          )}

          {/* ── Tài khoản / Đăng xuất — tách xa nút điều hướng để không bấm nhầm. ── */}
          <div className="bk-menu-sep mt-3" />
          <div className="bk-menu-account mt-1">
            {user?.picture && <img src={user.picture} alt="" className="h-9 w-9 rounded-full" />}
            {/* Tên (trên) + badge quyền (dưới) — 2 dòng canh giữa theo chiều cao avatar. */}
            <div className="flex min-w-0 flex-1 flex-col justify-center gap-1">
              {/* Tên: Noto Sans JP 600 — ưu tiên tiếng Nhật (氏名), nét gọn dày. */}
              <span
                className="truncate text-xs font-semibold text-[var(--bk-text)]"
                style={{ fontFamily: "'Noto Sans JP', 'Noto Sans', sans-serif" }}
                title={user?.email}
              >
                {user?.name}
              </span>
              <RoleBadge role={role} />
            </div>
            <button
              type="button"
              className="bk-menu-logout"
              onClick={() => {
                setConfirmLogout(true);
                setOpen(false);
              }}
              title={t('logout')}
            >
              <Icon icon="line-md:logout" width={14} height={14} />
              <span>{t('logout')}</span>
            </button>
          </div>
        </div>
      )}

      {/* Modal xác nhận đăng xuất (thay vì đăng xuất ngay 1 click). */}
      {confirmLogout && (
        <div className="bk-modal-overlay bk-modal-overlay--fixed" role="dialog" aria-modal="true" onClick={() => setConfirmLogout(false)}>
          <div className="bk-modal" onClick={(e) => e.stopPropagation()}>
            <div className="mb-1 flex items-center gap-2 text-sm font-bold text-[var(--bk-text)]">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[color-mix(in_srgb,#dc2626_14%,transparent)] text-[#dc2626]">
                <Icon icon="line-md:logout" width={15} height={15} />
              </span>
              {t('logoutConfirmTitle')}
            </div>
            <p className="mb-4 text-sm leading-relaxed text-[var(--bk-text-muted)]">{t('logoutConfirmMessage')}</p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setConfirmLogout(false)}
                className="rounded-lg border border-[var(--bk-border)] px-4 py-2 text-sm font-semibold text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
              >
                {t('btnCancel')}
              </button>
              <button
                type="button"
                onClick={signOut}
                className="rounded-lg bg-[#dc2626] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95"
              >
                {t('logout')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function MenuSection({ title }: { title: string }) {
  return (
    <div className="px-2 pb-1 pt-2 text-[10px] font-bold uppercase tracking-wide text-[var(--bk-text-faint)]">
      {title}
    </div>
  );
}
