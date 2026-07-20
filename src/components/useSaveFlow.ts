import { useState } from 'react';
import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useDriveToken, validDriveToken } from '../drive/token';
import { updateYamlContent } from '../drive/api';
import { gdErrorKey } from '../drive/errors';
import { formatDateTime } from '../ir/ivrProperty';
import { useAuth } from '../auth/useAuth';
import { useT } from '../ui/i18n';
import { useToast } from '../ui/toast';

// ─────────────────────────────────────────────────────────────────────────────
// Hook lưu flow hiện tại (export IR -> YAML) — 2 nguồn tuỳ currentFile.source:
//   - 'drive'         : ghi đè nội dung file version đang mở trên Google Drive
//                       (như trước). 更新日時 (modifiedTime) tự nhảy.
//   - 'local-design'  : ghi đè TRỰC TIẾP file 設計書 YAML trên đĩa qua File System
//                       Access API (handle mở từ LocalDesignImportButton). Trình
//                       duyệt không hỗ trợ (handle=null) -> canSave=false, người
//                       dùng tự export rồi ghi đè thủ công (chưa làm UI export tay).
// Dùng chung cho HeaderMenu (nút Lưu + Ctrl/⌘+Shift+S) và FlowsPanel.
// Mỗi component gọi hook có state saving/savedAt/saveError riêng — độc lập nhau.
// ─────────────────────────────────────────────────────────────────────────────
export function useSaveFlow() {
  const ir = useFlowStore((s) => s.ir);
  const exportYaml = useFlowStore((s) => s.exportYaml);
  const exportDesignYaml = useFlowStore((s) => s.exportDesignYaml);
  const setMeta = useFlowStore((s) => s.setMeta);
  const currentFile = useFileStore((s) => s.current);
  const driveTokenState = useDriveToken();
  const { user } = useAuth();
  const t = useT();
  const showToast = useToast((s) => s.show);
  const [saving, setSaving] = useState(false);
  // Thời điểm lưu thành công gần nhất (yyyy-MM-dd HH:mm) — hiện cạnh dấu tích.
  const [savedAt, setSavedAt] = useState<string | null>(null);
  // Key lỗi i18n nếu lưu thất bại (null = không lỗi).
  const [saveError, setSaveError] = useState<string | null>(null);

  const driveToken = validDriveToken(driveTokenState);

  // Có đủ điều kiện để lưu: Drive cần token còn hạn; local-design cần có handle
  // (trình duyệt hỗ trợ File System Access API và đã mở qua picker, không phải
  // fallback <input type=file>).
  const canSave = !!(
    ir &&
    currentFile &&
    (currentFile.source === 'local-design' ? currentFile.handle : driveToken)
  );

  // Trả về true khi lưu thành công (nút điều hướng dựa vào đây để đi tiếp/ở lại).
  const saveToRepo = async (): Promise<boolean> => {
    if (!currentFile || saving) return false;

    if (currentFile.source === 'local-design') {
      const handle = currentFile.handle;
      if (!handle) {
        setSaveError('gdErrAuth'); // chưa có key riêng — tái dùng thông báo "không lưu được"
        return false;
      }
      setSaving(true);
      setSaveError(null);
      try {
        const yaml = exportDesignYaml();
        const writable = await handle.createWritable();
        await writable.write(yaml);
        await writable.close();
        const now = formatDateTime(new Date());
        setSavedAt(now);
        showToast(t('fmSaved'));
        return true;
      } catch {
        setSaveError('gdErrAuth');
        return false;
      } finally {
        setSaving(false);
      }
    }

    if (!driveToken) {
      // Token Drive hết hạn/chưa có — báo lỗi thay vì im lặng.
      setSaveError('gdErrAuth');
      return false;
    }
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
      await updateYamlContent(driveToken, currentFile.driveFileId, yaml);
      setSavedAt(now);
      showToast(t('fmSaved')); // thông báo nổi, tự biến mất
      return true;
    } catch (e) {
      setSaveError(gdErrorKey(e));
      return false;
    } finally {
      setSaving(false);
    }
  };

  return { saving, savedAt, saveError, canSave, saveToRepo };
}
