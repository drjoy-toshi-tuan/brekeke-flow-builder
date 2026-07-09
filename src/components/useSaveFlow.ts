import { useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useGithubToken } from '../github/token';
import { putFlow } from '../github/api';
import { ghErrorKey } from '../github/errors';
import { formatDateTime } from '../ir/ivrProperty';
import { useAuth } from '../auth/useAuth';
import { useT } from '../ui/i18n';
import { useToast } from '../ui/toast';

// ─────────────────────────────────────────────────────────────────────────────
// Hook lưu flow hiện tại (export IR -> YAML) về đúng file trên repo (GitHub
// Contents API, cập nhật theo sha). Dùng chung cho:
//   - HeaderMenu: nút "Lưu flow" + phím tắt Ctrl/⌘+Shift+S.
//   - FlowsPanel: nút "Về màn quản lý file" (tự lưu rồi mới điều hướng).
// Mỗi component gọi hook có state saving/savedAt/saveError riêng — độc lập nhau.
// ─────────────────────────────────────────────────────────────────────────────
export function useSaveFlow() {
  const ir = useFlowStore((s) => s.ir);
  const exportYaml = useFlowStore((s) => s.exportYaml);
  const setMeta = useFlowStore((s) => s.setMeta);
  const currentFile = useFileStore((s) => s.current);
  const setSha = useFileStore((s) => s.setSha);
  const token = useGithubToken((s) => s.token);
  const { user } = useAuth();
  const t = useT();
  const showToast = useToast((s) => s.show);
  const [saving, setSaving] = useState(false);
  // Thời điểm lưu về repo thành công gần nhất (yyyy-MM-dd HH:mm) — hiện cạnh dấu tích.
  const [savedAt, setSavedAt] = useState<string | null>(null);
  // Key lỗi i18n nếu lưu thất bại (null = không lỗi).
  const [saveError, setSaveError] = useState<string | null>(null);

  // Có đủ điều kiện để lưu (đã mở file + có token + có IR).
  const canSave = !!(ir && token && currentFile);

  // Trả về true khi lưu thành công (nút điều hướng dựa vào đây để đi tiếp/ở lại).
  const saveToRepo = async (): Promise<boolean> => {
    if (!currentFile || !token || saving) return false;
    setSaving(true);
    setSaveError(null);
    try {
      // Đóng dấu 更新日時 (và 作成者/作成日時 nếu file cũ chưa có) trước khi export.
      const now = formatDateTime(new Date());
      setMeta({
        updatedAt: now,
        ...(ir?.meta.createdAt ? {} : { createdAt: now }),
        ...(ir?.meta.author ? {} : { author: user?.name ?? user?.email ?? '' }),
      });
      const yaml = exportYaml();
      const res = await putFlow(
        token,
        currentFile.path,
        yaml,
        t('commitSave', { name: currentFile.name }),
        currentFile.sha ?? undefined,
      );
      setSha(res.sha);
      setSavedAt(now);
      showToast(t('fmSaved')); // thông báo nổi, tự biến mất
      return true;
    } catch (e) {
      setSaveError(ghErrorKey(e));
      return false;
    } finally {
      setSaving(false);
    }
  };

  return { saving, savedAt, saveError, canSave, saveToRepo };
}
