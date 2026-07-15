import { useEffect, useMemo, useState } from 'react';
import { FileManagerMenu } from './FileManagerMenu';
import { useT, type TKey } from '../ui/i18n';
import { Icon } from '../ui/icons';
import { BrandLockup } from '../ui/BrandLockup';

// ─────────────────────────────────────────────────────────────────────────────
// Màn quản lý flow PHÂN CẤP theo cấu trúc Google Drive (PROTOTYPE — mock data):
//   病院 (grandparent folder) › シナリオ (parent folder) › バージョン (file V1, V2…)
//
// Đây là bản dựng UI để review trước khi nối Drive API thật:
//   - Điều hướng drill-down 3 tầng + breadcrumb.
//   - Sort ASC/DESC khi bấm tiêu đề cột (mọi tầng), tìm kiếm trong tầng hiện tại.
//   - Cột 適用中 & badge: chỗ chờ cho phase deploy (Selenium) — hiện đọc từ mock.
// Khi nối Drive thật: thay MOCK_FACILITIES bằng dữ liệu từ src/drive/api.ts,
// giữ nguyên toàn bộ phần render/điều hướng.
// ─────────────────────────────────────────────────────────────────────────────

interface MockVersion {
  v: number;
  createdAt: string; // yyyy-MM-dd HH:mm
  author: string;
}

interface MockScenario {
  id: string;
  name: string;
  appliedV: number | null; // version đang 適用 trên hệ thống AI電話 (null = chưa)
  versions: MockVersion[];
}

interface MockFacility {
  id: string;
  name: string;
  scenarios: MockScenario[];
}

// Dữ liệu mẫu — mô phỏng đúng cấu trúc folder sẽ tạo trên Drive.
const MOCK_FACILITIES: MockFacility[] = [
  {
    id: 'f1',
    name: '国立成育医療研究センター',
    scenarios: [
      {
        id: 's1',
        name: '診療予約',
        appliedV: 2,
        versions: [
          { v: 3, createdAt: '2026-07-14 18:22', author: 'Tuan Nguyen' },
          { v: 2, createdAt: '2026-07-10 09:41', author: 'Tuan Nguyen' },
          { v: 1, createdAt: '2026-07-02 14:05', author: '田中 花子' },
        ],
      },
      {
        id: 's2',
        name: '予約変更・キャンセル',
        appliedV: 1,
        versions: [{ v: 1, createdAt: '2026-07-08 11:30', author: '田中 花子' }],
      },
      {
        id: 's3',
        name: '休診日案内',
        appliedV: null,
        versions: [
          { v: 2, createdAt: '2026-07-15 08:12', author: 'Tuan Nguyen' },
          { v: 1, createdAt: '2026-07-12 16:48', author: '佐藤 健' },
        ],
      },
    ],
  },
  {
    id: 'f2',
    name: '聖路加国際病院',
    scenarios: [
      {
        id: 's4',
        name: '診療予約',
        appliedV: 4,
        versions: [
          { v: 4, createdAt: '2026-07-13 10:02', author: '佐藤 健' },
          { v: 3, createdAt: '2026-07-09 15:27', author: '佐藤 健' },
          { v: 2, createdAt: '2026-07-05 13:44', author: 'Tuan Nguyen' },
          { v: 1, createdAt: '2026-06-30 09:00', author: 'Tuan Nguyen' },
        ],
      },
      {
        id: 's5',
        name: '検査結果案内',
        appliedV: null,
        versions: [{ v: 1, createdAt: '2026-07-11 17:19', author: '田中 花子' }],
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
          { v: 2, createdAt: '2026-07-14 19:55', author: '田中 花子' },
          { v: 1, createdAt: '2026-07-06 10:33', author: '田中 花子' },
        ],
      },
    ],
  },
  { id: 'f4', name: '大阪母子医療センター', scenarios: [] },
];

// ── Helpers dẫn xuất từ mock (sau này thay bằng field từ Drive API) ──
const latestOf = (s: MockScenario) => (s.versions.length ? Math.max(...s.versions.map((x) => x.v)) : 0);
const latestVersionOf = (s: MockScenario) =>
  s.versions.find((x) => x.v === latestOf(s));
const facilityUpdatedAt = (f: MockFacility) => {
  const all = f.scenarios.flatMap((s) => s.versions.map((v) => v.createdAt));
  return all.length ? all.reduce((a, b) => (a > b ? a : b)) : undefined;
};
// Tên file version theo quy ước [シナリオ名]_V{N}.yaml.
const versionFileName = (scenario: string, v: number) => `${scenario}_V${v}.yaml`;

// Chuẩn hoá chuỗi tìm kiếm (đồng bộ FileManagerScreen).
const normalizeSearch = (s: string) => s.normalize('NFKC').toLowerCase().trim();

// ── Sort dùng chung cho cả 3 tầng ──
type SortDir = 'asc' | 'desc';
type SortState = { key: string; dir: SortDir } | null;

// So sánh 2 giá trị ô: số so số, chuỗi so theo locale; thiếu giá trị dồn cuối.
function compareCells(a: string | number | undefined, b: string | number | undefined, dir: SortDir): number {
  if (a === undefined && b === undefined) return 0;
  if (a === undefined) return 1;
  if (b === undefined) return -1;
  const sign = dir === 'asc' ? 1 : -1;
  if (typeof a === 'number' && typeof b === 'number') return sign * (a - b);
  return sign * String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
}

export function DriveManagerScreen() {
  const t = useT();

  // Vị trí đang đứng trong cây: rỗng = tầng 病院; có facility = tầng シナリオ;
  // có cả scenario = tầng バージョン.
  const [path, setPath] = useState<{ facilityId?: string; scenarioId?: string }>({});
  const facility = MOCK_FACILITIES.find((f) => f.id === path.facilityId) ?? null;
  const scenario = facility?.scenarios.find((s) => s.id === path.scenarioId) ?? null;
  const level: 1 | 2 | 3 = scenario ? 3 : facility ? 2 : 1;

  // Tìm kiếm + sort áp cho tầng hiện tại; đổi tầng thì reset.
  const [query, setQuery] = useState('');
  const [sort, setSort] = useState<SortState>(null);
  useEffect(() => {
    setQuery('');
    setSort(null);
  }, [path]);

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
    'flex h-8 w-8 items-center justify-center rounded-lg text-[var(--bk-text-faint)] transition hover:bg-[var(--bk-accent-soft)] hover:text-[var(--bk-accent)]';

  // ── Dữ liệu từng tầng sau lọc + sort ──
  const q = normalizeSearch(query);

  const facilityRows = useMemo(() => {
    let rows = MOCK_FACILITIES;
    if (q) rows = rows.filter((f) => normalizeSearch(f.name).includes(q));
    if (!sort) return rows;
    return [...rows].sort((a, b) =>
      compareCells(
        sort.key === 'count' ? a.scenarios.length : sort.key === 'updatedAt' ? facilityUpdatedAt(a) : a.name,
        sort.key === 'count' ? b.scenarios.length : sort.key === 'updatedAt' ? facilityUpdatedAt(b) : b.name,
        sort.dir,
      ),
    );
  }, [q, sort]);

  const scenarioRows = useMemo(() => {
    let rows = facility?.scenarios ?? [];
    if (q)
      rows = rows.filter((s) =>
        [s.name, latestVersionOf(s)?.author ?? ''].some((h) => normalizeSearch(h).includes(q)),
      );
    if (!sort) return rows;
    const val = (s: MockScenario): string | number | undefined => {
      switch (sort.key) {
        case 'latest':
          return latestOf(s) || undefined;
        case 'applied':
          return s.appliedV ?? undefined;
        case 'updatedAt':
          return latestVersionOf(s)?.createdAt;
        case 'author':
          return latestVersionOf(s)?.author;
        default:
          return s.name;
      }
    };
    return [...rows].sort((a, b) => compareCells(val(a), val(b), sort.dir));
  }, [facility, q, sort]);

  const versionRows = useMemo(() => {
    // Mặc định: bản mới nhất ở trên (DESC theo số version).
    let rows = [...(scenario?.versions ?? [])].sort((a, b) => b.v - a.v);
    if (q) rows = rows.filter((v) => normalizeSearch(v.author).includes(q));
    if (!sort) return rows;
    const val = (x: MockVersion): string | number =>
      sort.key === 'createdAt' ? x.createdAt : sort.key === 'author' ? x.author : x.v;
    return rows.sort((a, b) => compareCells(val(a), val(b), sort.dir));
  }, [scenario, q, sort]);

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

          {/* Tiêu đề + chip prototype */}
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <h1 className="text-lg font-bold tracking-tight text-[var(--bk-text)]">{t('fmTitle')}</h1>
              <p className="text-sm text-[var(--bk-text-muted)]">{t(subtitleKey)}</p>
            </div>
            <span className="flex shrink-0 items-center gap-1.5 rounded-full border border-amber-300 bg-amber-50 px-2.5 py-1 text-[11px] font-semibold text-amber-700">
              <Icon icon="lucide:triangle-alert" width={12} height={12} />
              {t('dmPreviewBadge')}
            </span>
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

          {/* ── Thanh hành động: Upload / Tạo mới / Làm mới / Tìm kiếm ── */}
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="flex items-center gap-1.5 rounded-lg bg-[var(--bk-accent)] px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:scale-95"
            >
              <Icon icon="line-md:upload-loop" width={17} height={17} />
              {t('fmUpload')}
            </button>
            <button
              type="button"
              className="flex items-center gap-1.5 rounded-lg bg-[#16a34a] px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md active:translate-y-0 active:scale-95"
            >
              <Icon icon="line-md:plus" width={17} height={17} />
              {t('fmNew')}
            </button>
            <button type="button" title={t('fmRefresh')} aria-label={t('fmRefresh')} className={`${iconBtn} h-9 w-9`}>
              <Icon icon="lucide:refresh-cw" width={18} height={18} />
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
            <span className="ml-auto whitespace-nowrap text-xs text-[var(--bk-text-faint)]">
              {t('fmResultCount', {
                n: level === 1 ? facilityRows.length : level === 2 ? scenarioRows.length : versionRows.length,
              })}
            </span>
          </div>

          {/* ── Bảng theo tầng ── */}
          <div className="overflow-x-auto rounded-xl border border-[var(--bk-border)] bg-[var(--bk-surface)]">
            {level === 1 && (
              facilityRows.length === 0 ? (
                <EmptyState icon="lucide:folder" text={t('dmEmptyFacilities')} />
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
                    {facilityRows.map((f) => (
                      <tr key={f.id} className="border-b border-[var(--bk-border)] transition last:border-0 hover:bg-[var(--bk-surface-2)]">
                        <td className={cell}>
                          <button
                            type="button"
                            onClick={() => setPath({ facilityId: f.id })}
                            className="flex min-w-0 items-center gap-2 text-left font-medium text-[var(--bk-text)] transition hover:text-[var(--bk-accent)]"
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
                              className={`${iconBtn} text-[var(--bk-accent)]`}
                              title={t('fmOpen')}
                            >
                              <Icon icon="lucide:folder-open" width={17} height={17} />
                            </button>
                            <button type="button" className={`${iconBtn} hover:!bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:!text-rose-500`} title={t('fmDeleteTitle')}>
                              <Icon icon="lucide:trash-2" width={16} height={16} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )
            )}

            {level === 2 && facility && (
              scenarioRows.length === 0 ? (
                <EmptyState icon="lucide:folder" text={t('dmEmptyScenarios')} />
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
                    {scenarioRows.map((s) => {
                      const latest = latestOf(s);
                      const lv = latestVersionOf(s);
                      return (
                        <tr key={s.id} className="border-b border-[var(--bk-border)] transition last:border-0 hover:bg-[var(--bk-surface-2)]">
                          <td className={cell}>
                            {/* Bản thật: click = mở bản mới nhất trên canvas. Prototype: vào tầng version. */}
                            <button
                              type="button"
                              onClick={() => setPath({ facilityId: facility.id, scenarioId: s.id })}
                              className="flex min-w-0 items-center gap-2 text-left font-medium text-[var(--bk-text)] transition hover:text-[var(--bk-accent)]"
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
                          <td className={`${cell} whitespace-nowrap text-[var(--bk-text-muted)]`}>{lv?.createdAt ?? '—'}</td>
                          <td className={`${cell} text-[var(--bk-text-muted)]`}>{lv?.author ?? '—'}</td>
                          <td className={cell}>
                            <div className="flex items-center justify-end gap-1">
                              <button type="button" className={`${iconBtn} text-[var(--bk-accent)]`} title={t('dmOpenLatest')}>
                                <Icon icon="fluent:open-16-filled" width={18} height={18} />
                              </button>
                              <button
                                type="button"
                                onClick={() => setPath({ facilityId: facility.id, scenarioId: s.id })}
                                className={iconBtn}
                                title={t('dmHistory')}
                              >
                                <Icon icon="lucide:history" width={16} height={16} />
                              </button>
                              <button type="button" className={iconBtn} title={t('fmDuplicate')}>
                                <Icon icon="lucide:copy" width={16} height={16} />
                              </button>
                              <button type="button" className={`${iconBtn} hover:!bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:!text-rose-500`} title={t('fmDeleteTitle')}>
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
            )}

            {level === 3 && scenario && (
              versionRows.length === 0 ? (
                <EmptyState icon="lucide:file-text" text={t('dmEmptyVersions')} />
              ) : (
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--bk-border)]">
                      {renderSortTh('v', 'colVersion', 'w-[320px] min-w-[260px]')}
                      {renderSortTh('createdAt', 'colCreatedAt')}
                      {renderSortTh('author', 'colAuthor')}
                      <th className={`${th} text-right`}>{t('colActions')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {versionRows.map((ver) => {
                      const isLatest = ver.v === latestOf(scenario);
                      const isApplied = scenario.appliedV === ver.v;
                      return (
                        <tr key={ver.v} className="border-b border-[var(--bk-border)] transition last:border-0 hover:bg-[var(--bk-surface-2)]">
                          <td className={cell}>
                            <div className="flex items-center gap-2.5">
                              <button
                                type="button"
                                className="flex min-w-0 items-center gap-2 text-left font-semibold text-[var(--bk-text)] transition hover:text-[var(--bk-accent)]"
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
                          <td className={`${cell} text-[var(--bk-text-muted)]`}>{ver.author}</td>
                          <td className={cell}>
                            <div className="flex items-center justify-end gap-1">
                              <button type="button" className={`${iconBtn} text-[var(--bk-accent)]`} title={t('fmOpen')}>
                                <Icon icon="fluent:open-16-filled" width={18} height={18} />
                              </button>
                              {/* Khôi phục = tạo V{N+1} với nội dung bản này (không sửa lịch sử). */}
                              {!isLatest && (
                                <button type="button" className={iconBtn} title={t('dmRestore')}>
                                  <Icon icon="lucide:rotate-ccw" width={16} height={16} />
                                </button>
                              )}
                              <button type="button" className={`${iconBtn} hover:!bg-[color-mix(in_srgb,#dc2626_12%,transparent)] hover:!text-rose-500`} title={t('fmDeleteTitle')}>
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
            )}
          </div>
        </div>
      </main>
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
