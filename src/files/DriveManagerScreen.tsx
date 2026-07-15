import { useCallback, useEffect, useMemo, useState } from 'react';
import { FileManagerMenu } from './FileManagerMenu';
import { DriveConnectPanel } from './DriveConnectPanel';
import { buildBlankFlow } from './FileManagerScreen';
import { useT, type TKey } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { BrandLockup } from '../ui/BrandLockup';
import { useToast } from '../ui/toast';
import { useAuth } from '../auth/useAuth';
import { GOOGLE_CLIENT_ID } from '../auth/config';
import { useFlowStore } from '../store/flowStore';
import { useFileStore } from '../store/fileStore';
import { useDriveAuth } from '../drive/useDriveAuth';
import {
  listChildren,
  getFileText,
  createYamlFile,
  ensureFolder,
  trashItem,
  isFolder,
  isYamlName,
  DriveApiError,
  type DriveItem,
} from '../drive/api';
import { gdErrorKey } from '../drive/errors';
import { DRIVE_ROOT_FOLDER_ID, parseVersionFromName, versionFileName } from '../drive/config';
import { formatDateTime } from '../ir/ivrProperty';

// ─────────────────────────────────────────────────────────────────────────────
// Màn quản lý flow PHÂN CẤP theo cấu trúc Google Drive:
//   病院 (grandparent folder) › シナリオ (parent folder) › バージョン (_V{N}.yaml)
//
// - Có GOOGLE_CLIENT_ID  -> chạy THẬT: xin access token Drive (1 click lần đầu),
//   load cả cây bằng ~3 request (list con theo lô), mở/tạo/khôi phục/xoá thật.
// - Không có (demo dev)  -> hiện MOCK DATA để review UI (badge プレビュー).
//
// Cột 適用中 đọc từ appProperties.appliedVersion trên folder シナリオ — phần chờ
// cho phase deploy (bot Selenium sẽ ghi giá trị này sau khi deploy thành công).
// ─────────────────────────────────────────────────────────────────────────────

export interface VersionNode {
  fileId: string;
  v: number;
  createdAt: string; // yyyy-MM-dd HH:mm — Drive createdTime
  updatedAt: string; // yyyy-MM-dd HH:mm — Drive modifiedTime (lưu đè -> tự nhảy)
  author: string; // lastModifyingUser
}

export interface ScenarioNode {
  id: string;
  name: string;
  appliedV: number | null; // version đang 適用 trên hệ thống AI電話 (null = chưa)
  versions: VersionNode[]; // sắp DESC theo v (mới nhất trước)
}

export interface FacilityNode {
  id: string;
  name: string;
  scenarios: ScenarioNode[];
}

// Mục tiêu xoá (đã qua modal xác nhận) — dùng chung cho cả 3 tầng.
interface DeleteTarget {
  kind: 'facility' | 'scenario' | 'version';
  id: string;
  label: string;
}

// Các hành động màn hình gọi ra ngoài — bản mock không truyền -> nút bị disable.
interface DriveActions {
  onRefresh?: () => void;
  onOpenLatest?: (f: FacilityNode, s: ScenarioNode) => void;
  onOpenVersion?: (f: FacilityNode, s: ScenarioNode, v: VersionNode) => void;
  onRestore?: (f: FacilityNode, s: ScenarioNode, v: VersionNode) => void;
  onDelete?: (target: DeleteTarget) => void;
  onCreateFlow?: (facility: string, scenario: string) => void;
}

// ── Helpers dẫn xuất ──
const latestOf = (s: ScenarioNode) => s.versions[0]?.v ?? 0;
const latestVersionOf = (s: ScenarioNode): VersionNode | undefined => s.versions[0];
const facilityUpdatedAt = (f: FacilityNode) => {
  const all = f.scenarios.flatMap((s) => s.versions.map((v) => v.updatedAt));
  return all.length ? all.reduce((a, b) => (a > b ? a : b)) : undefined;
};

// Chuẩn hoá chuỗi tìm kiếm (đồng bộ FileManagerScreen).
const normalizeSearch = (s: string) => s.normalize('NFKC').toLowerCase().trim();

// Các mức số dòng mỗi trang (đồng bộ FileManagerScreen).
const PAGE_SIZES = [20, 50] as const;

// ── Sort dùng chung cho cả 3 tầng ──
type SortDir = 'asc' | 'desc';
type SortState = { key: string; dir: SortDir } | null;

// So sánh 2 giá trị ô: số so số, chuỗi so theo locale; thiếu giá trị dồn cuối.
function compareCells(
  a: string | number | undefined,
  b: string | number | undefined,
  dir: SortDir,
): number {
  if (a === undefined && b === undefined) return 0;
  if (a === undefined) return 1;
  if (b === undefined) return -1;
  const sign = dir === 'asc' ? 1 : -1;
  if (typeof a === 'number' && typeof b === 'number') return sign * (a - b);
  return sign * String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
}

// ─────────────────────────────────────────────────────────────────────────────
// Mock data — chỉ dùng ở chế độ demo (chưa cấu hình GOOGLE_CLIENT_ID) để review UI.
// ─────────────────────────────────────────────────────────────────────────────

const pad2 = (n: number) => String(n).padStart(2, '0');
function mockDate(day: number, hm: string): string {
  const d = new Date(2026, 4, 1 + day);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())} ${hm}`;
}

// 24 version cho 1 kịch bản — đủ nhiều để xem phân trang ở tầng バージョン.
const MANY_VERSIONS: VersionNode[] = Array.from({ length: 24 }, (_, i) => {
  const v = 24 - i; // DESC: mới nhất trước
  const authors = ['佐藤 健', 'Tuan Nguyen', '田中 花子'];
  return {
    fileId: `mock-v${v}`,
    v,
    createdAt: mockDate(v * 3, '09:30'),
    updatedAt: mockDate(v * 3 + (v % 3), v % 2 ? '16:45' : '09:30'),
    author: authors[v % 3],
  };
});

const MOCK_FACILITIES: FacilityNode[] = [
  {
    id: 'f1',
    name: '国立成育医療研究センター',
    scenarios: [
      {
        id: 's1',
        name: '診療予約',
        appliedV: 2,
        versions: [
          { fileId: 'm1', v: 3, createdAt: '2026-07-14 18:22', updatedAt: '2026-07-15 10:05', author: 'Tuan Nguyen' },
          { fileId: 'm2', v: 2, createdAt: '2026-07-10 09:41', updatedAt: '2026-07-12 14:20', author: 'Tuan Nguyen' },
          { fileId: 'm3', v: 1, createdAt: '2026-07-02 14:05', updatedAt: '2026-07-02 14:05', author: '田中 花子' },
        ],
      },
      {
        id: 's2',
        name: '予約変更・キャンセル',
        appliedV: 1,
        versions: [
          { fileId: 'm4', v: 1, createdAt: '2026-07-08 11:30', updatedAt: '2026-07-08 11:30', author: '田中 花子' },
        ],
      },
      {
        id: 's3',
        name: '休診日案内',
        appliedV: null,
        versions: [
          { fileId: 'm5', v: 2, createdAt: '2026-07-15 08:12', updatedAt: '2026-07-15 08:12', author: 'Tuan Nguyen' },
          { fileId: 'm6', v: 1, createdAt: '2026-07-12 16:48', updatedAt: '2026-07-13 09:02', author: '佐藤 健' },
        ],
      },
    ],
  },
  {
    id: 'f2',
    name: '聖路加国際病院',
    scenarios: [
      { id: 's4', name: '診療予約', appliedV: 22, versions: MANY_VERSIONS },
      {
        id: 's5',
        name: '検査結果案内',
        appliedV: null,
        versions: [
          { fileId: 'm7', v: 1, createdAt: '2026-07-11 17:19', updatedAt: '2026-07-11 17:19', author: '田中 花子' },
        ],
      },
    ],
  },
  {
    id: 'f3',
    name: '東京慈恵会医科大学附属病院',
    scenarios: [
      {
        id: 's6',
        name: '診療時間案内',
        appliedV: 1,
        versions: [
          { fileId: 'm8', v: 2, createdAt: '2026-07-14 19:55', updatedAt: '2026-07-14 19:55', author: '田中 花子' },
          { fileId: 'm9', v: 1, createdAt: '2026-07-06 10:33', updatedAt: '2026-07-07 15:41', author: '田中 花子' },
        ],
      },
    ],
  },
  { id: 'f4', name: '大阪母子医療センター', scenarios: [] },
];

// ─────────────────────────────────────────────────────────────────────────────
// Entry: có Client ID -> bản thật (OAuth + Drive API); không -> mock để review UI.
// ─────────────────────────────────────────────────────────────────────────────

export function DriveManagerScreen() {
  if (!GOOGLE_CLIENT_ID) {
    return <DriveInner facilities={MOCK_FACILITIES} mock loading={false} busy={false} listErrorKey={null} actionError={null} actions={{}} />;
  }
  return <DriveReal />;
}

// ── Bản thật: cổng token -> load cây -> hành động thật ──

function DriveReal() {
  const { token, connecting, error, requestAccess, disconnect } = useDriveAuth();

  if (!token) {
    // Chưa có access token trong phiên -> panel kết nối (1 click; lần đầu mỗi
    // tài khoản mới phải chấp thuận, về sau popup tự đóng).
    return (
      <div className="relative flex h-full flex-col bg-[var(--bk-bg)]">
        <header className="flex items-center justify-between border-b border-[var(--bk-border)] bg-[var(--bk-surface)] px-4 py-2.5">
          <BrandLockup logoClass="h-8 w-8" textClass="text-xl" />
          <FileManagerMenu />
        </header>
        <div className="relative flex flex-1 items-center justify-center overflow-hidden p-6">
          <div
            aria-hidden
            className="pointer-events-none absolute left-1/2 top-1/2 h-[460px] w-[460px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[var(--bk-accent)] opacity-[0.08] blur-[100px]"
          />
          <DriveConnectPanel connecting={connecting} error={error} onConnect={requestAccess} />
        </div>
      </div>
    );
  }
  return <DriveLoaded token={token} onAuthInvalid={disconnect} />;
}

// Đổi RFC3339 của Drive -> 'yyyy-MM-dd HH:mm' (múi giờ máy người dùng).
const fmtTime = (rfc3339: string) => formatDateTime(new Date(rfc3339));

// Ghép 3 danh sách phẳng (folder 施設 / folder シナリオ / file version) thành cây.
function buildTree(fac: DriveItem[], scen: DriveItem[], files: DriveItem[]): FacilityNode[] {
  const byName = (a: { name: string }, b: { name: string }) => a.name.localeCompare(b.name);

  const versByParent = new Map<string, VersionNode[]>();
  for (const f of files) {
    const parent = f.parents?.[0];
    const v = isYamlName(f.name) ? parseVersionFromName(f.name) : null;
    // File không theo quy ước _V{N}.yaml (thả tay vào folder) -> bỏ qua.
    if (!parent || v == null) continue;
    const node: VersionNode = {
      fileId: f.id,
      v,
      createdAt: fmtTime(f.createdTime),
      updatedAt: fmtTime(f.modifiedTime),
      author: f.lastModifyingUser?.displayName ?? '',
    };
    versByParent.set(parent, [...(versByParent.get(parent) ?? []), node]);
  }

  const scenByParent = new Map<string, ScenarioNode[]>();
  for (const s of scen) {
    const parent = s.parents?.[0];
    if (!parent) continue;
    const applied = Number(s.appProperties?.appliedVersion);
    const node: ScenarioNode = {
      id: s.id,
      name: s.name,
      appliedV: Number.isFinite(applied) && applied > 0 ? applied : null,
      versions: (versByParent.get(s.id) ?? []).sort((a, b) => b.v - a.v),
    };
    scenByParent.set(parent, [...(scenByParent.get(parent) ?? []), node]);
  }

  return fac
    .map((f) => ({ id: f.id, name: f.name, scenarios: (scenByParent.get(f.id) ?? []).sort(byName) }))
    .sort(byName);
}

function DriveLoaded({ token, onAuthInvalid }: { token: string; onAuthInvalid: () => void }) {
  const t = useT();
  const { user } = useAuth();
  const showToast = useToast((s) => s.show);
  const loadYaml = useFlowStore((s) => s.loadYaml);
  const openFile = useFileStore((s) => s.openFile);

  const [facilities, setFacilities] = useState<FacilityNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [listErrorKey, setListErrorKey] = useState<TKey | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  // Token bị Drive từ chối giữa chừng (hết hạn/thu quyền) -> về panel kết nối.
  const handledAsExpired = (e: unknown): boolean => {
    if (e instanceof DriveApiError && e.code === 'auth') {
      onAuthInvalid();
      return true;
    }
    return false;
  };

  // Load CẢ CÂY 3 tầng bằng 3 lượt list theo lô (mỗi lượt gom nhiều folder cha).
  const load = useCallback(async () => {
    setLoading(true);
    setListErrorKey(null);
    try {
      const facFolders = (await listChildren(token, [DRIVE_ROOT_FOLDER_ID])).filter(isFolder);
      const scenFolders = facFolders.length
        ? (await listChildren(token, facFolders.map((x) => x.id))).filter(isFolder)
        : [];
      const files = scenFolders.length
        ? await listChildren(token, scenFolders.map((x) => x.id))
        : [];
      setFacilities(buildTree(facFolders, scenFolders, files));
    } catch (e) {
      if (!handledAsExpired(e)) setListErrorKey(gdErrorKey(e));
    } finally {
      setLoading(false);
    }
    // onAuthInvalid là action zustand ổn định — giữ deps [token] (xem FileManagerScreen).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  // Mở 1 version lên canvas. Giữ busy=true khi thành công (đang điều hướng đi).
  const openVersion = async (f: FacilityNode, s: ScenarioNode, ver: VersionNode) => {
    if (busy) return;
    setBusy(true);
    setActionError(null);
    try {
      const text = await getFileText(token, ver.fileId);
      await loadYaml(text);
      openFile({
        storage: 'drive',
        path: `${f.name}/${s.name}`,
        name: versionFileName(s.name, ver.v),
        sha: null,
        driveFileId: ver.fileId,
        driveFolderId: s.id,
        version: ver.v,
      });
    } catch (e) {
      setBusy(false);
      if (handledAsExpired(e)) return;
      setActionError(e instanceof DriveApiError ? t(gdErrorKey(e)) : t('fmUploadInvalid'));
    }
  };

  // Khôi phục bản cũ = tạo version MỚI (V{max+1}) với nội dung bản đó — không sửa lịch sử.
  const restore = async (_f: FacilityNode, s: ScenarioNode, ver: VersionNode) => {
    if (busy) return;
    setBusy(true);
    setActionError(null);
    try {
      const text = await getFileText(token, ver.fileId);
      const nextV = latestOf(s) + 1;
      await createYamlFile(token, s.id, versionFileName(s.name, nextV), text);
      showToast(t('dmRestored', { n: nextV }));
      await load();
    } catch (e) {
      if (!handledAsExpired(e)) setActionError(t(gdErrorKey(e)));
    } finally {
      setBusy(false);
    }
  };

  // Xoá (đã xác nhận ở modal) = đưa vào Thùng rác Drive (khôi phục được ~30 ngày).
  const remove = async (target: DeleteTarget) => {
    if (busy) return;
    setBusy(true);
    setActionError(null);
    try {
      await trashItem(token, target.id);
      await load();
    } catch (e) {
      if (!handledAsExpired(e)) setActionError(t(gdErrorKey(e)));
    } finally {
      setBusy(false);
    }
  };

  // Tạo flow mới: tự dựng cây 施設名/シナリオ名 (tìm-hoặc-tạo folder) rồi ghi V1
  // (folder シナリオ đã tồn tại thì ghi V{max+1}) và mở luôn lên canvas.
  const createFlow = async (facility: string, scenario: string) => {
    if (busy) return;
    setBusy(true);
    setActionError(null);
    try {
      const fac = await ensureFolder(token, DRIVE_ROOT_FOLDER_ID, facility);
      const scen = await ensureFolder(token, fac.id, scenario);
      const existing = await listChildren(token, [scen.id]);
      const maxV = existing.reduce((m, x) => Math.max(m, parseVersionFromName(x.name) ?? 0), 0);
      const now = formatDateTime(new Date());
      const content = buildBlankFlow({
        facility,
        name: scenario,
        author: user?.name ?? user?.email ?? '',
        createdAt: now,
      });
      const file = await createYamlFile(token, scen.id, versionFileName(scenario, maxV + 1), content);
      await loadYaml(content);
      openFile({
        storage: 'drive',
        path: `${facility}/${scenario}`,
        name: file.name,
        sha: null,
        driveFileId: file.id,
        driveFolderId: scen.id,
        version: maxV + 1,
      });
    } catch (e) {
      setBusy(false);
      if (handledAsExpired(e)) return;
      setActionError(t(gdErrorKey(e)));
    }
  };

  return (
    <DriveInner
      facilities={facilities}
      mock={false}
      loading={loading}
      busy={busy}
      listErrorKey={listErrorKey}
      actionError={actionError}
      actions={{
        onRefresh: () => void load(),
        onOpenLatest: (f, s) => {
          const latest = latestVersionOf(s);
          if (latest) void openVersion(f, s, latest);
        },
        onOpenVersion: (f, s, v) => void openVersion(f, s, v),
        onRestore: (f, s, v) => void restore(f, s, v),
        onDelete: (target) => void remove(target),
        onCreateFlow: (facility, scenario) => void createFlow(facility, scenario),
      }}
    />
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Phần trình bày dùng chung (real + mock): drill-down, sort, tìm kiếm, phân trang,
// modal tạo mới / xác nhận xoá.
// ─────────────────────────────────────────────────────────────────────────────

function DriveInner({
  facilities,
  mock,
  loading,
  busy,
  listErrorKey,
  actionError,
  actions,
}: {
  facilities: FacilityNode[];
  mock: boolean;
  loading: boolean;
  busy: boolean;
  listErrorKey: TKey | null;
  actionError: string | null;
  actions: DriveActions;
}) {
  const t = useT();

  // Vị trí đang đứng trong cây: rỗng = tầng 病院; có facility = tầng シナリオ;
  // có cả scenario = tầng バージョン.
  const [path, setPath] = useState<{ facilityId?: string; scenarioId?: string }>({});
  const facility = facilities.find((f) => f.id === path.facilityId) ?? null;
  const scenario = facility?.scenarios.find((s) => s.id === path.scenarioId) ?? null;
  const level: 1 | 2 | 3 = scenario ? 3 : facility ? 2 : 1;

  // Tìm kiếm + sort + phân trang áp cho tầng hiện tại; đổi tầng thì reset.
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<SortState>(null);
  const [pageSize, setPageSize] = useState<number>(PAGE_SIZES[0]);
  const [page, setPage] = useState(1);
  useEffect(() => {
    setQuery('');
    setSort(null);
    setPage(1);
  }, [path]);
  useEffect(() => {
    setPage(1);
  }, [query, sort, pageSize]);

  // Modal tạo flow mới / xác nhận xoá.
  const [showNew, setShowNew] = useState(false);
  const [newFacility, setNewFacility] = useState('');
  const [newScenario, setNewScenario] = useState('');
  const [createErrorKey, setCreateErrorKey] = useState<TKey | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<DeleteTarget | null>(null);

  const openNewModal = () => {
    setCreateErrorKey(null);
    // Đang đứng trong 1 bệnh viện -> prefill tên bệnh viện đó.
    setNewFacility(facility?.name ?? '');
    setNewScenario(scenario?.name ?? '');
    setShowNew(true);
  };

  const handleCreate = () => {
    const fac = newFacility.trim();
    const scen = newScenario.trim();
    if (!fac) {
      setCreateErrorKey('fmFacilityRequired');
      return;
    }
    if (!scen) {
      setCreateErrorKey('fmScenarioRequired');
      return;
    }
    setShowNew(false);
    actions.onCreateFlow?.(fac, scen);
  };

  const toggleSort = (key: string) =>
    setSort((s) =>
      !s || s.key !== key ? { key, dir: 'asc' } : s.dir === 'asc' ? { key, dir: 'desc' } : null,
    );

  const cell = 'px-4 py-3 text-sm text-[var(--bk-text)]';
  const th = 'px-4 py-2.5 text-left text-[11px] font-bold uppercase tracking-wide text-[var(--bk-text-faint)]';

  // Tiêu đề cột sort được (đồng bộ hành vi với FileManagerScreen).
  const renderSortTh = (key: string, label: TKey, extraClass = '') => {
    const dir = sort && sort.key === key ? sort.dir : null;
    return (
      <th
        className={`${th} ${extraClass}`}
        aria-sort={dir ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}
      >
        <button
          type="button"
          onClick={() => toggleSort(key)}
          className={`group inline-flex items-center gap-1 uppercase tracking-wide transition hover:text-[var(--bk-accent)] ${
            dir ? 'text-[var(--bk-accent)]' : ''
          }`}
        >
          {t(label)}
          <Icon
            icon={dir === 'desc' ? 'lucide:arrow-down' : 'lucide:arrow-up'}
            width={12}
            height={12}
            className={dir ? '' : 'opacity-0 transition group-hover:opacity-50'}
          />
        </button>
      </th>
    );
  };

  const iconBtn =
    'flex h-8 w-8 items-center justify-center rounded-lg text-[var(--bk-text-faint)] transition hover:bg-[var(--bk-accent-soft)] hover:text-[var(--bk-accent)] disabled:pointer-events-none disabled:opacity-40';

  // ── Dữ liệu từng tầng sau lọc + sort ──
  const q = normalizeSearch(query);

  const facilityRows = useMemo(() => {
    let rows = facilities;
    if (q) rows = rows.filter((f) => normalizeSearch(f.name).includes(q));
    if (!sort) return rows;
    return [...rows].sort((a, b) =>
      compareCells(
        sort.key === 'count' ? a.scenarios.length : sort.key === 'updatedAt' ? facilityUpdatedAt(a) : a.name,
        sort.key === 'count' ? b.scenarios.length : sort.key === 'updatedAt' ? facilityUpdatedAt(b) : b.name,
        sort.dir,
      ),
    );
  }, [facilities, q, sort]);

  const scenarioRows = useMemo(() => {
    let rows = facility?.scenarios ?? [];
    if (q)
      rows = rows.filter((s) =>
        [s.name, latestVersionOf(s)?.author ?? ''].some((h) => normalizeSearch(h).includes(q)),
      );
    if (!sort) return rows;
    const val = (s: ScenarioNode): string | number | undefined => {
      switch (sort.key) {
        case 'latest':
          return latestOf(s) || undefined;
        case 'applied':
          return s.appliedV ?? undefined;
        case 'updatedAt':
          return latestVersionOf(s)?.updatedAt;
        case 'author':
          return latestVersionOf(s)?.author;
        default:
          return s.name;
      }
    };
    return [...rows].sort((a, b) => compareCells(val(a), val(b), sort.dir));
  }, [facility, q, sort]);

  const versionRows = useMemo(() => {
    // Mặc định: bản mới nhất ở trên (dữ liệu đã DESC sẵn theo v).
    let rows = scenario?.versions ?? [];
    if (q) rows = rows.filter((v) => normalizeSearch(v.author).includes(q));
    if (!sort) return rows;
    const val = (x: VersionNode): string | number =>
      sort.key === 'createdAt'
        ? x.createdAt
        : sort.key === 'updatedAt'
          ? x.updatedAt
          : sort.key === 'author'
            ? x.author
            : x.v;
    return [...rows].sort((a, b) => compareCells(val(a), val(b), sort.dir));
  }, [scenario, q, sort]);

  // Phân trang trên tầng đang xem (áp sau lọc + sort).
  const activeCount =
    level === 1 ? facilityRows.length : level === 2 ? scenarioRows.length : versionRows.length;
  const totalPages = Math.max(1, Math.ceil(activeCount / pageSize));
  const safePage = Math.min(page, totalPages);
  const pageSlice = <T,>(rows: T[]): T[] =>
    rows.slice((safePage - 1) * pageSize, safePage * pageSize);

  const subtitleKey: TKey =
    level === 1 ? 'dmSubtitleFacilities' : level === 2 ? 'dmSubtitleScenarios' : 'dmSubtitleVersions';

  return (
    <div className="relative flex h-full flex-col bg-[var(--bk-bg)]">
      {/* ── Top bar (đồng bộ FileManagerScreen) ── */}
      <header className="flex items-center justify-between border-b border-[var(--bk-border)] bg-[var(--bk-surface)] px-4 py-2.5">
        <BrandLockup logoClass="h-8 w-8" textClass="text-xl" />
        <FileManagerMenu />
      </header>

      <main className="relative mx-auto w-full max-w-7xl flex-1 overflow-auto p-6">
        <div
          aria-hidden
          className="pointer-events-none absolute left-1/2 top-24 h-[420px] w-[640px] -translate-x-1/2 rounded-full bg-[var(--bk-accent)] opacity-[0.07] blur-[110px]"
        />

        <div className="relative overflow-hidden rounded-3xl border border-[var(--bk-border)] bg-[var(--bk-surface)] p-6 shadow-[var(--bk-shadow)]">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-transparent via-[var(--bk-accent)] to-transparent opacity-70"
          />

          {/* Tiêu đề (+ chip prototype khi chạy mock) */}
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <h1 className="text-lg font-bold tracking-tight text-[var(--bk-text)]">{t('fmTitle')}</h1>
              <p className="text-sm text-[var(--bk-text-muted)]">{t(subtitleKey)}</p>
            </div>
            {mock && (
              <span className="flex shrink-0 items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700">
                <Icon icon="lucide:triangle-alert" width={12} height={12} />
                {t('dmPreviewBadge')}
              </span>
            )}
          </div>

          {/* ── Breadcrumb: 病院一覧 › 病院 › シナリオ ── */}
          <nav className="mb-4 flex flex-wrap items-center gap-1 text-sm">
            <button
              type="button"
              onClick={() => setPath({})}
              className={`rounded-md px-1.5 py-0.5 transition ${
                level === 1
                  ? 'font-bold text-[var(--bk-text)]'
                  : 'font-medium text-[var(--bk-accent)] hover:bg-[var(--bk-accent-soft)]'
              }`}
            >
              {t('dmRootCrumb')}
            </button>
            {facility && (
              <>
                <Icon icon="lucide:chevron-right" width={14} height={14} className="text-[var(--bk-text-faint)]" />
                <button
                  type="button"
                  onClick={() => setPath({ facilityId: facility.id })}
                  className={`rounded-md px-1.5 py-0.5 transition ${
                    level === 2
                      ? 'font-bold text-[var(--bk-text)]'
                      : 'font-medium text-[var(--bk-accent)] hover:bg-[var(--bk-accent-soft)]'
                  }`}
                >
                  {facility.name}
                </button>
              </>
            )}
            {scenario && (
              <>
                <Icon icon="lucide:chevron-right" width={14} height={14} className="text-[var(--bk-text-faint)]" />
                <span className="px-1.5 py-0.5 font-bold text-[var(--bk-text)]">{scenario.name}</span>
              </>
            )}
          </nav>

          {/* ── Thanh hành động: Tạo mới / Làm mới / Tìm kiếm / Phân trang ── */}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={openNewModal}
              disabled={busy || (!mock && !actions.onCreateFlow)}
              className="flex items-center gap-1.5 rounded-lg bg-[#16a34a] px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:scale-95 disabled:pointer-events-none disabled:opacity-60"
            >
              <Icon icon="line-md:plus" width={17} height={17} />
              {t('fmNew')}
            </button>
            <button
              type="button"
              onClick={() => actions.onRefresh?.()}
              disabled={loading || busy || !actions.onRefresh}
              title={t('fmRefresh')}
              aria-label={t('fmRefresh')}
              className={`${iconBtn} h-9 w-9`}
            >
              <Icon icon="lucide:refresh-cw" width={18} height={18} className={loading ? 'animate-spin' : ''} />
            </button>
            {/* Ô tìm kiếm (áp cho tầng đang xem) */}
            <div className="relative ml-0.5 min-w-[200px] max-w-sm flex-1">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--bk-text-faint)]">
                <Icon icon="line-md:search" width={15} height={15} />
              </span>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t('fmSearch')}
                aria-label={t('fmSearch')}
                className="w-full rounded-lg border border-[var(--bk-border)] bg-[var(--bk-bg)] py-2 pl-9 pr-3 text-sm text-[var(--bk-text)] outline-none transition focus:border-[var(--bk-accent)] focus:ring-2 focus:ring-[var(--bk-accent-soft)]"
              />
            </div>

            {/* ── Phần trang: số kết quả · số dòng mỗi trang · điều hướng ── */}
            <div className="ml-auto flex flex-wrap items-center justify-end gap-2">
              <span className="hidden whitespace-nowrap text-xs text-[var(--bk-text-faint)] lg:inline">
                {t('fmResultCount', { n: activeCount })}
              </span>
              <div className="flex shrink-0 items-center gap-1.5 text-sm text-[var(--bk-text-muted)]">
                <span className="hidden sm:inline">{t('fmPerPage')}</span>
                <div className="relative inline-flex shrink-0 items-center">
                  <select
                    value={pageSize}
                    onChange={(e) => setPageSize(Number(e.target.value))}
                    aria-label={t('fmPerPage')}
                    className="cursor-pointer appearance-none rounded-lg border border-[var(--bk-border)] bg-[var(--bk-bg)] py-1.5 pl-2 pr-6 text-sm font-medium text-[var(--bk-text)] outline-none transition hover:border-[var(--bk-accent)] focus:border-[var(--bk-accent)]"
                  >
                    {PAGE_SIZES.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                  <Icon
                    icon="lucide:chevron-down"
                    width={14}
                    height={14}
                    className="pointer-events-none absolute right-1.5 text-[var(--bk-text-muted)]"
                  />
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={safePage <= 1}
                  title={t('fmPrevPage')}
                  aria-label={t('fmPrevPage')}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-accent-soft)] hover:text-[var(--bk-accent)] disabled:pointer-events-none disabled:opacity-40"
                >
                  <Icon icon="lucide:chevron-left" width={18} height={18} />
                </button>
                <span className="min-w-[84px] whitespace-nowrap text-center text-xs font-medium text-[var(--bk-text-muted)]">
                  {t('fmPageOf', { page: safePage, total: totalPages })}
                </span>
                <button
                  type="button"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={safePage >= totalPages}
                  title={t('fmNextPage')}
                  aria-label={t('fmNextPage')}
                  className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-accent-soft)] hover:text-[var(--bk-accent)] disabled:pointer-events-none disabled:opacity-40"
                >
                  <Icon icon="lucide:chevron-right" width={18} height={18} />
                </button>
              </div>
            </div>
          </div>

          {(actionError || listErrorKey) && (
            <div className="mb-3 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
              <Icon icon="lucide:triangle-alert" className="mt-0.5 shrink-0" />
              <span>{actionError ?? (listErrorKey ? t(listErrorKey) : null)}</span>
            </div>
          )}

          {/* ── Bảng theo tầng ── */}
          <div className="overflow-x-auto rounded-xl border border-[var(--bk-border)] bg-[var(--bk-surface)]">
            {loading ? (
              <div className="flex items-center justify-center gap-2 p-8 text-sm text-[var(--bk-text-muted)]">
                <Icon icon="lucide:loader-circle" className="animate-spin" />
                {t('fmLoading')}
              </div>
            ) : level === 1 ? (
              facilityRows.length === 0 ? (
                <EmptyState icon="lucide:folder" text={q ? t('fmNoResults') : t('dmEmptyFacilities')} />
              ) : (
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--bk-border)]">
                      {renderSortTh('name', 'colFacility', 'w-[380px] min-w-[300px]')}
                      {renderSortTh('count', 'colScenarioCount')}
                      {renderSortTh('updatedAt', 'colUpdatedAt')}
                      <th className={`${th} text-right`}>{t('colActions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageSlice(facilityRows).map((f) => (
                      <tr key={f.id} className="border-b border-[var(--bk-border)] transition last:border-0 hover:bg-[var(--bk-surface-2)]">
                        <td className={cell}>
                          <button
                            type="button"
                            onClick={() => setPath({ facilityId: f.id })}
                            disabled={busy}
                            className="flex min-w-0 items-center gap-2 text-left font-medium text-[var(--bk-text)] transition hover:text-[var(--bk-accent)] disabled:opacity-60"
                          >
                            <Icon icon="lucide:folder" width={16} height={16} className="shrink-0 text-[var(--bk-accent)]" />
                            <span className="truncate">{f.name}</span>
                          </button>
                        </td>
                        <td className={`${cell} text-[var(--bk-text-muted)]`}>{f.scenarios.length}</td>
                        <td className={`${cell} whitespace-nowrap text-[var(--bk-text-muted)]`}>
                          {facilityUpdatedAt(f) ?? '—'}
                        </td>
                        <td className={cell}>
                          <div className="flex items-center justify-end gap-1">
                            <button
                              type="button"
                              onClick={() => setPath({ facilityId: f.id })}
                              disabled={busy}
                              className={`${iconBtn} text-[var(--bk-accent)]`}
                              title={t('fmOpen')}
                            >
                              <Icon icon="lucide:folder-open" width={17} height={17} />
                            </button>
                            <button
                              type="button"
                              onClick={() => setDeleteTarget({ kind: 'facility', id: f.id, label: f.name })}
                              disabled={busy || (!mock && !actions.onDelete)}
                              className={`${iconBtn} hover:!bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:!text-rose-500`}
                              title={t('fmDeleteTitle')}
                            >
                              <Icon icon="lucide:trash-2" width={16} height={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            ) : level === 2 && facility ? (
              scenarioRows.length === 0 ? (
                <EmptyState icon="lucide:folder" text={q ? t('fmNoResults') : t('dmEmptyScenarios')} />
              ) : (
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--bk-border)]">
                      {renderSortTh('name', 'colScenario', 'w-[300px] min-w-[240px]')}
                      {renderSortTh('latest', 'colLatestVersion')}
                      {renderSortTh('applied', 'colAppliedVersion')}
                      {renderSortTh('updatedAt', 'colUpdatedAt')}
                      {renderSortTh('author', 'colAuthor')}
                      <th className={`${th} text-right`}>{t('colActions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageSlice(scenarioRows).map((s) => {
                      const latest = latestOf(s);
                      const lv = latestVersionOf(s);
                      const goHistory = () => setPath({ facilityId: facility.id, scenarioId: s.id });
                      return (
                        <tr key={s.id} className="border-b border-[var(--bk-border)] transition last:border-0 hover:bg-[var(--bk-surface-2)]">
                          <td className={cell}>
                            {/* Bản thật: click = mở bản mới nhất trên canvas. Mock: vào tầng version. */}
                            <button
                              type="button"
                              onClick={() => (actions.onOpenLatest ? actions.onOpenLatest(facility, s) : goHistory())}
                              disabled={busy}
                              className="flex min-w-0 items-center gap-2 text-left font-medium text-[var(--bk-text)] transition hover:text-[var(--bk-accent)] disabled:opacity-60"
                              title={t('dmOpenLatest')}
                            >
                              <Icon icon="lucide:file-text" width={16} height={16} className="shrink-0 text-[var(--bk-accent)]" />
                              <span className="truncate">{s.name}</span>
                            </button>
                          </td>
                          <td className={`${cell} font-semibold`}>{latest ? `V${latest}` : '—'}</td>
                          <td className={cell}>
                            {s.appliedV == null ? (
                              <span className="text-[var(--bk-text-faint)]">— {t('dmNotApplied')}</span>
                            ) : (
                              <span
                                className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
                                  s.appliedV === latest
                                    ? 'bg-[color-mix(in_srgb,#16a34a_14%,transparent)] text-[#16a34a]'
                                    : 'bg-amber-100 text-amber-700'
                                }`}
                                title={s.appliedV === latest ? t('dmAppliedBadge') : t('dmNotApplied')}
                              >
                                <Icon icon="lucide:circle-check" width={12} height={12} />
                                V{s.appliedV}
                              </span>
                            )}
                          </td>
                          <td className={`${cell} whitespace-nowrap text-[var(--bk-text-muted)]`}>{lv?.updatedAt ?? '—'}</td>
                          <td className={`${cell} text-[var(--bk-text-muted)]`}>{lv?.author ?? '—'}</td>
                          <td className={cell}>
                            <div className="flex items-center justify-end gap-1">
                              <button
                                type="button"
                                onClick={() => actions.onOpenLatest?.(facility, s)}
                                disabled={busy || !actions.onOpenLatest || !lv}
                                className={`${iconBtn} text-[var(--bk-accent)]`}
                                title={t('dmOpenLatest')}
                              >
                                <Icon icon="fluent:open-16-filled" width={18} height={18} />
                              </button>
                              <button type="button" onClick={goHistory} disabled={busy} className={iconBtn} title={t('dmHistory')}>
                                <Icon icon="lucide:history" width={16} height={16} />
                              </button>
                              <button
                                type="button"
                                onClick={() => setDeleteTarget({ kind: 'scenario', id: s.id, label: s.name })}
                                disabled={busy || (!mock && !actions.onDelete)}
                                className={`${iconBtn} hover:!bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:!text-rose-500`}
                                title={t('fmDeleteTitle')}
                              >
                                <Icon icon="lucide:trash-2" width={16} height={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )
            ) : level === 3 && facility && scenario ? (
              versionRows.length === 0 ? (
                <EmptyState icon="lucide:file-text" text={q ? t('fmNoResults') : t('dmEmptyVersions')} />
              ) : (
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--bk-border)]">
                      {renderSortTh('v', 'colVersion', 'w-[320px] min-w-[260px]')}
                      {renderSortTh('createdAt', 'colCreatedAt')}
                      {renderSortTh('updatedAt', 'colUpdatedAt')}
                      {renderSortTh('author', 'colAuthor')}
                      <th className={`${th} text-right`}>{t('colActions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageSlice(versionRows).map((ver) => {
                      const isLatest = ver.v === latestOf(scenario);
                      const isApplied = scenario.appliedV === ver.v;
                      return (
                        <tr key={ver.fileId} className="border-b border-[var(--bk-border)] transition last:border-0 hover:bg-[var(--bk-surface-2)]">
                          <td className={cell}>
                            <div className="flex items-center gap-2.5">
                              <button
                                type="button"
                                onClick={() => actions.onOpenVersion?.(facility, scenario, ver)}
                                disabled={busy || (!mock && !actions.onOpenVersion)}
                                className="flex min-w-0 items-center gap-2 text-left font-semibold text-[var(--bk-text)] transition hover:text-[var(--bk-accent)] disabled:opacity-60"
                                title={t('fmOpen')}
                              >
                                <Icon icon="lucide:file-text" width={16} height={16} className="shrink-0 text-[var(--bk-accent)]" />
                                <span>V{ver.v}</span>
                              </button>
                              <span className="truncate text-xs text-[var(--bk-text-faint)]">
                                {versionFileName(scenario.name, ver.v)}
                              </span>
                              {isApplied && (
                                <span className="inline-flex shrink-0 items-center gap-1 rounded-full bg-[color-mix(in_srgb,#16a34a_14%,transparent)] px-2 py-0.5 text-xs font-semibold text-[#16a34a]">
                                  <Icon icon="lucide:circle-check" width={12} height={12} />
                                  {t('dmAppliedBadge')}
                                </span>
                              )}
                              {isLatest && (
                                <span className="inline-flex shrink-0 items-center rounded-full border border-[var(--bk-accent)] px-2 py-0.5 text-[11px] font-semibold text-[var(--bk-accent)]">
                                  最新
                                </span>
                              )}
                            </div>
                          </td>
                          <td className={`${cell} whitespace-nowrap text-[var(--bk-text-muted)]`}>{ver.createdAt}</td>
                          <td className={`${cell} whitespace-nowrap text-[var(--bk-text-muted)]`}>{ver.updatedAt}</td>
                          <td className={`${cell} text-[var(--bk-text-muted)]`}>{ver.author}</td>
                          <td className={cell}>
                            <div className="flex items-center justify-end gap-1">
                              <button
                                type="button"
                                onClick={() => actions.onOpenVersion?.(facility, scenario, ver)}
                                disabled={busy || (!mock && !actions.onOpenVersion)}
                                className={`${iconBtn} text-[var(--bk-accent)]`}
                                title={t('fmOpen')}
                              >
                                <Icon icon="fluent:open-16-filled" width={18} height={18} />
                              </button>
                              {/* Khôi phục = tạo V{N+1} với nội dung bản này (không sửa lịch sử). */}
                              {!isLatest && (
                                <button
                                  type="button"
                                  onClick={() => actions.onRestore?.(facility, scenario, ver)}
                                  disabled={busy || (!mock && !actions.onRestore)}
                                  className={iconBtn}
                                  title={t('dmRestore')}
                                >
                                  <Icon icon="lucide:rotate-ccw" width={16} height={16} />
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() =>
                                  setDeleteTarget({
                                    kind: 'version',
                                    id: ver.fileId,
                                    label: versionFileName(scenario.name, ver.v),
                                  })
                                }
                                disabled={busy || (!mock && !actions.onDelete)}
                                className={`${iconBtn} hover:!bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:!text-rose-500`}
                                title={t('fmDeleteTitle')}
                              >
                                <Icon icon="lucide:trash-2" width={16} height={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )
            ) : null}
          </div>
        </div>
      </main>

      {/* Overlay "đang xử lý" */}
      {busy && (
        <div className="absolute inset-0 z-40 flex items-center justify-center bg-[color-mix(in_srgb,var(--bk-bg)_55%,transparent)]">
          <Icon icon="lucide:loader-circle" width={28} height={28} className="animate-spin text-[var(--bk-accent)]" />
        </div>
      )}

      {/* Modal: tạo flow mới (施設名 + シナリオ名 -> tự dựng cây folder + V1) */}
      {showNew && (
        <div className="bk-modal-overlay bk-modal-overlay--fixed" role="dialog" aria-modal="true" onClick={() => setShowNew(false)}>
          <div className="bk-modal" onClick={(e) => e.stopPropagation()}>
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-[var(--bk-text)]">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[var(--bk-accent-soft)] text-[var(--bk-accent)]">
                <Icon icon="lucide:file-plus" width={15} height={15} />
              </span>
              {t('fmNew')}
            </div>

            <label className="mb-1 block text-xs font-semibold text-[var(--bk-text-muted)]">
              {t('colFacility')}
            </label>
            <input
              autoFocus
              value={newFacility}
              onChange={(e) => setNewFacility(e.target.value)}
              placeholder={t('fmFacilityPlaceholder')}
              className="mb-3 w-full rounded-lg border border-[var(--bk-border)] bg-[var(--bk-bg)] px-3 py-2 text-sm text-[var(--bk-text)] outline-none focus:border-[var(--bk-accent)]"
            />

            <label className="mb-1 block text-xs font-semibold text-[var(--bk-text-muted)]">
              {t('colScenario')}
            </label>
            <input
              value={newScenario}
              onChange={(e) => setNewScenario(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') handleCreate();
              }}
              placeholder={t('fmScenarioPlaceholder')}
              className="mb-4 w-full rounded-lg border border-[var(--bk-border)] bg-[var(--bk-bg)] px-3 py-2 text-sm text-[var(--bk-text)] outline-none focus:border-[var(--bk-accent)]"
            />

            {createErrorKey && <div className="mb-3 text-xs text-rose-500">{t(createErrorKey)}</div>}

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowNew(false)}
                className="rounded-lg border border-[var(--bk-border)] px-4 py-2 text-sm font-semibold text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
              >
                {t('btnCancel')}
              </button>
              <button
                type="button"
                onClick={handleCreate}
                className="rounded-lg bg-[var(--bk-accent)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
              >
                {t('fmCreate')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: xác nhận xoá (đưa vào Thùng rác Drive) */}
      {deleteTarget && (
        <div className="bk-modal-overlay bk-modal-overlay--fixed" role="dialog" aria-modal="true" onClick={() => setDeleteTarget(null)}>
          <div className="bk-modal" onClick={(e) => e.stopPropagation()}>
            <div className="mb-1 flex items-center gap-2 text-sm font-bold text-[var(--bk-text)]">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-[color-mix(in_srgb,#dc2626_14%,transparent)] text-[#dc2626]">
                <Icon icon="lucide:trash-2" width={15} height={15} />
              </span>
              {t('fmDeleteTitle')}
            </div>
            <p className="mb-4 text-sm leading-relaxed text-[var(--bk-text-muted)]">
              {t('fmDeleteConfirm', { name: deleteTarget.label })}
            </p>
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setDeleteTarget(null)}
                className="rounded-lg border border-[var(--bk-border)] px-4 py-2 text-sm font-semibold text-[var(--bk-text-muted)] transition hover:bg-[var(--bk-surface-2)] hover:text-[var(--bk-text)]"
              >
                {t('btnCancel')}
              </button>
              <button
                type="button"
                onClick={() => {
                  const target = deleteTarget;
                  setDeleteTarget(null);
                  actions.onDelete?.(target);
                }}
                className="rounded-lg bg-[#dc2626] px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95"
              >
                {t('delete')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function EmptyState({ icon, text }: { icon: string; text: string }) {
  return (
    <div className="flex flex-col items-center gap-2 p-10 text-center text-[var(--bk-text-muted)]">
      <Icon icon={icon} width={28} height={28} className="text-[var(--bk-text-faint)]" />
      <span className="text-sm">{text}</span>
    </div>
  );
}
