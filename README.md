# AI電話 Flow Builder — Phase 1 (UI demo)

Webapp visualize flow của hệ thống **AI電話** (Brekeke-based) dưới dạng sơ đồ node giống
[n8n](https://n8n.io), đọc/ghi từ file YAML. **IR** (Intermediate Representation) là source
of truth duy nhất; YAML chỉ là adapter import/export.

> Phase 1 tập trung **test UI online trên GitHub Pages**, có đăng nhập Google giới hạn
> domain `drjoy.jp`. Chưa sinh `.bivr`, chưa có AI, chưa có backend.

![node types](https://img.shields.io/badge/nodes-9%20types-blue) ![phase](https://img.shields.io/badge/phase-1%20(UI%20demo)-green)

---

## Tính năng phase 1

- 📥 Đọc YAML flow → **IR** → **auto-layout ELK** (top-down) → canvas React Flow.
- 🖱️ Kéo-thả node, chọn nhiều node (rê vùng), zoom/pan, minimap, fit-view.
- 🔌 Nối dây (kéo từ output → input), **xoá dây** bằng icon 🗑 hiện khi hover.
- ✏️ **Double-click node** mở panel sửa `label` và các field trong `data`.
- 📤 **Export YAML** (round-trip IR ↔ YAML) để kiểm chứng.
- 🔐 Đăng nhập Google, chỉ tài khoản `@drjoy.jp` (client-side gating — xem [Bảo mật](#-bảo-mật)).
- 🚀 Deploy GitHub Pages qua GitHub Actions.

9 loại node: `start · announce · input · condition · script · llm · transfer · hangup · end`.

---

## Chạy local

```bash
npm install
npm run dev        # mở http://localhost:5173
```

App tự nạp `fixtures/sample-flow.yaml` khi khởi động — thấy sơ đồ ngay.

> **Chế độ demo:** nếu chưa set `VITE_GOOGLE_CLIENT_ID`, màn login có nút
> **“Vào chế độ demo (bỏ qua đăng nhập)”** để xem UI ngay mà không cần Google.

Các lệnh khác:

```bash
npm run build      # tsc -b && vite build  -> dist/
npm run preview    # xem thử bản build
npm test           # unit test cho fromYaml / toYaml (round-trip)
```

---

## Biến môi trường

Tạo `.env` (xem `.env.example`):

```
VITE_GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
```

Client ID **không phải secret** — an toàn để nằm trong bundle SPA. **Không** dùng client
secret cho SPA.

---

## Thiết lập Google Cloud Console (việc con người phải làm)

Claude Code không làm được các bước này — bạn (Tuan) cần tự làm trên
[Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. Tạo **OAuth 2.0 Client ID** loại **Web application**.
2. **Authorized JavaScript origins**, thêm:
   - `http://localhost:5173`
   - `https://drjoy-toshi-tuan.github.io`
3. Copy Client ID → dùng cho `VITE_GOOGLE_CLIENT_ID` (local `.env` và GitHub Actions secret).

---

## Deploy GitHub Pages

1. **Bật Pages:** repo → **Settings → Pages → Build and deployment → Source: GitHub Actions**.
2. **Thêm secret:** repo → **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `VITE_GOOGLE_CLIENT_ID`
   - Value: Client ID ở trên.
3. **Push `main`** → workflow `.github/workflows/deploy.yml` build & deploy.
4. URL: `https://drjoy-toshi-tuan.github.io/brekeke-flow-builder/`

> `vite.config.ts` đã set `base: '/brekeke-flow-builder/'` khớp tên repo.

---

## 🔒 Bảo mật

> ⚠️ **Kiểm tra domain ở client-side KHÔNG phải bảo mật thật.**
>
> Bundle JS là công khai; người dùng kỹ thuật có thể fork/chạy local để bypass, và tham số
> `hd` không đủ tin cậy nếu chỉ dựa vào nó. Cơ chế hiện tại (decode ID token, kiểm tra
> `hd === 'drjoy.jp'` và `email_verified === true`) chỉ là **cổng UX cho nội bộ test UI**.
> Vì phase này chỉ dùng YAML mẫu (không dữ liệu thật), mức này chấp nhận được.
>
> **Khi có API/dữ liệu thật:** BẮT BUỘC verify claim `hd` của ID token **ở server-side**
> (Vercel/Cloudflare Functions) trước khi trả bất kỳ dữ liệu nào. Module `auth/` được thiết
> kế tách rời để bước nâng cấp này không phải sửa UI.

`ALLOWED_DOMAIN` nằm ở [`src/auth/config.ts`](src/auth/config.ts).

---

## Kiến trúc

Xem [`CLAUDE.md`](CLAUDE.md) — IR là source of truth; `ir/` thuần (không React); `canvas/`
render từ IR; `irAdapter.ts` là 2 hàm thuần IR ↔ React Flow.

```
YAML ──fromYaml──► IR ──layout(ELK)──► IR(+position) ──irToReactFlow──► Canvas
                    ▲                                                      │
                    └──────────── reactFlowToIr / store actions ◄──────────┘
IR ──toYaml──► YAML (Export)
```
