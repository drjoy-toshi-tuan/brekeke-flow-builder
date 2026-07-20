import { useState, type ChangeEvent } from 'react';
import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useToast } from '../ui/toast';

// ─────────────────────────────────────────────────────────────────────────────
// Mở TRỰC TIẾP 1 file 設計書 YAML của pipeline (gen_flow, vd
// pipeline/output/scenarios/{施設}_{flow}/設計書.yaml) từ đĩa cục bộ — KHÔNG qua
// Google Drive. Dùng File System Access API (Chrome/Edge) để giữ được "handle"
// cho phép Lưu (useSaveFlow) ghi đè lại đúng file; trình duyệt không hỗ trợ
// (Firefox/Safari) thì fallback <input type=file> — vẫn xem/sửa được, chỉ
// không lưu tại chỗ (canSave=false, người dùng tự export rồi ghi đè thủ công).
//
// Đây là bước NỐI adapter fromDesignYaml/toDesignYaml (src/ir/designYaml/) vào
// UI — chưa browse được cây output/scenarios/ (cần chọn từng file bằng tay).
// ─────────────────────────────────────────────────────────────────────────────

// File System Access API chưa có trong lib.dom.d.ts ổn định ở mọi phiên bản TS —
// khai báo tối thiểu phần dùng tới thay vì @ts-expect-error rải rác.
interface FileSystemAccessWindow extends Window {
  showOpenFilePicker?: (opts?: {
    types?: { description: string; accept: Record<string, string[]> }[];
  }) => Promise<FileSystemFileHandle[]>;
}

function slugify(name: string): string {
  const slug = name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return slug || 'design-flow';
}

export function LocalDesignImportButton() {
  const loadDesignYaml = useFlowStore((s) => s.loadDesignYaml);
  const openFile = useFileStore((s) => s.openFile);
  const showToast = useToast((s) => s.show);
  const [loading, setLoading] = useState(false);

  const openFromHandle = async (handle: FileSystemFileHandle) => {
    const fileObj = await handle.getFile();
    const text = await fileObj.text();
    await loadDesignYaml(text, { id: slugify(fileObj.name), name: fileObj.name });
    openFile({ source: 'local-design', path: 'ローカル (pipeline)', name: fileObj.name, handle });
  };

  const handlePickerClick = async () => {
    const picker = (window as FileSystemAccessWindow).showOpenFilePicker;
    if (!picker) return; // input file fallback xử lý qua <label>/<input>
    setLoading(true);
    try {
      const [handle] = await picker({
        types: [{ description: '設計書 YAML', accept: { 'text/yaml': ['.yaml', '.yml'] } }],
      });
      if (handle) await openFromHandle(handle);
    } catch (e) {
      // AbortError khi người dùng huỷ chọn file -> im lặng, không phải lỗi.
      if (e instanceof DOMException && e.name === 'AbortError') return;
      showToast('設計書 YAML の読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = ''; // cho phép chọn lại đúng file lần sau
    if (!file) return;
    setLoading(true);
    try {
      const text = await file.text();
      await loadDesignYaml(text, { id: slugify(file.name), name: file.name });
      openFile({ source: 'local-design', path: 'ローカル (pipeline)', name: file.name, handle: null });
    } catch {
      showToast('設計書 YAML の読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const hasPicker = typeof (window as FileSystemAccessWindow).showOpenFilePicker === 'function';

  if (hasPicker) {
    return (
      <button
        type="button"
        onClick={handlePickerClick}
        disabled={loading}
        className="rounded-full border border-[var(--bk-border)] px-3 py-1.5 text-xs font-medium text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-bg)] disabled:opacity-50"
        title="pipeline/output/scenarios/{施設}_{flow}/ の設計書 YAML をローカルから開く"
      >
        設計書を開く（ローカル）
      </button>
    );
  }

  return (
    <label className="cursor-pointer rounded-full border border-[var(--bk-border)] px-3 py-1.5 text-xs font-medium text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-bg)]">
      設計書を開く（ローカル）
      <input type="file" accept=".yaml,.yml" className="hidden" onChange={handleInputChange} disabled={loading} />
    </label>
  );
}
