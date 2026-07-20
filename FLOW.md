# FLOW.md — Luồng chạy hiện tại của repo (sau khi copy `pipeline/`)

> Trạng thái tại thời điểm viết: **2 hệ thống nằm chung 1 repo nhưng CHƯA kết nối với nhau.**
> `pipeline/` (gen_flow) và phần webapp (`src/`) là 2 luồng độc lập, đọc/ghi 2 định dạng YAML khác nhau.
> Tài liệu này mô tả từng luồng riêng, rồi chỉ rõ khoảng trống cần nối (adapter) cho bước chỉnh sửa sâu hơn.

---

## 1. Luồng Webapp (`src/`) — visual flow editor

Chạy hoàn toàn trên trình duyệt (static site, không backend). Thứ tự màn hình do `src/App.tsx` (`Gate`) quyết định:

```
Mở app
  │
  ▼
[1] LoginScreen (auth/)
  - Google Identity Services, domain check ở client (chỉ là cổng UX)
  - verifyIdToken.ts siết claim (iss/aud/exp/nonce/hd/email_verified) — defense-in-depth
  │  (chưa login / sai domain → dừng ở đây)
  ▼
[2] DriveManagerScreen (files/)
  - Cây thư mục 施設名/シナリオ名/<シナリオ名>_V{N}.yaml trên Google Drive
  - Google Drive REST v3 qua access token OAuth người dùng
  - DriveTokenKeeper (drive/) tự gia hạn token nền:
      ưu tiên token proxy Vercel (auth-code flow + refresh token AES-GCM)
      → fallback implicit flow (popup GIS) nếu không có proxy
  - Phân quyền owner/admin/user đọc từ access-log.json trên Drive
  │  (chọn 1 file YAML → nạp vào flowStore dưới dạng FlowIR)
  ▼
[3] FlowCanvas (canvas/) — màn chính
  - React Flow (@xyflow/react) render FlowIR: irAdapter.irToReactFlow(ir)
  - Auto-layout cây tự viết (ir/layout.ts) — không dùng elkjs
  - Người dùng sửa node/edge trên canvas
      → mọi thao tác gọi action cập nhật IR trong zustand (flowStore)
      → irAdapter.reactFlowToIr(nodes, edges, prev) đồng bộ ngược
  - Toolbar / NodeSettingsPanel / CanvasTabs (Flow Diagram, Announce List, General, Status)
  │  (lưu)
  ▼
[4] Save
  - ir/toYaml.ts serialize FlowIR → YAML (schema riêng: FlowIR — xem §3 dưới)
  - Ghi lại lên Google Drive (Drive REST API, cùng token ở bước [2])
```

**Schema dữ liệu của webapp (FlowIR)** — định nghĩa tại `src/ir/types.ts`:
- `NodeType`: `start | announce | interaction | nexus | logic | openai | faq | transfer | save | jump | hangup`
- `FlowNode { id, type, label, position, data }`, `FlowEdge { id, source, target, sourceHandle?, condition?, label? }`
- Nguyên tắc bắt buộc: `ir/` là code thuần (không import React); mọi sửa canvas phải qua IR → React Flow chỉ render.

---

## 2. Luồng Pipeline (`pipeline/`, gen_flow gốc) — sinh/kiểm BIVR

Chạy bằng Python + Claude agents, không có UI, input là **設計書 YAML** (khác hẳn FlowIR ở trên):

```
Khách hàng nêu yêu cầu (họp/chat/nói)
  │
  ▼
director (AI, Opus) ── giải yêu cầu → sinh 設計書 YAML
  (scenario_flow blocks: 26 loại, allowlist chính = schemas/qa_validator.py::KNOWN_BLOCK_TYPES)
  │
  ▼
qa_validator.py ── kiểm máy 40 mục (T/L/E/I/F/M)
  │  CRITICAL? → yaml_auto_fixer.py sửa tự động (fix_category=auto) → validate lại
  │  còn CRITICAL sau đó → HALT, trả về người (壁打ち = trao đổi trực tiếp), director KHÔNG tự retry
  ▼
copy_subflows.py ── copy sẵn các subflow chuẩn (FAQ family, 用件聴取…)
  ▼
scaffold_generator.py ── sinh JSON hoàn chỉnh từ scenario_flow (builder function theo 26 block type)
  (4 loại thông tin cá nhân: 氏名/生年月日/điện thoại/số thẻ khám → inline, KHÔNG dùng Jump to Flow)
  ▼
gen_scripts.py ── sinh ES5 Scripts từ script_blocks (nếu có)
  ▼
layout_calculator.py ── tính layout dạng cây dọc (DAG-based)
  ▼
generator (AI) ── bỏ qua nếu đã có scenario_flow (chỉ dùng cho format routing_map cũ)
  ▼
[song song] prompter (AI, Opus, viết params.prompt cho generate_by_OpenAI)
           + gen_properties.py (sinh TTS properties, không dùng LLM)
  ▼
merge → validator.py ── kiểm cấu trúc JSON
  │  CRITICAL fix_category=auto → auto_fixer.py sửa máy (CTX-017, status, LAYOUT...)
  │  còn lại → người xử lý (fixer AI đã retire cho luồng build mới, 2026-06-24)
  ▼
add_date + [song song] tester.py (audit cấu trúc) + build
  ▼
collect_scenario → phonebook_csv (nếu có) → commit
  ▼
oracle_gate ── đối chiếu @General$Script trong bivr với modules/ chính chủ (engine+spec hash)
  ▼
gen_p7_cases.py + stub_stt_connection.py ── sinh ca test kết nối (P7)
  ▼
p7_acceptance (người: chạy máy thật, import + gọi thử)
  ▼
p6_gate (engine/spec 2 tầng) → commit_evidence
  ▼
score_gate (chấm điểm 4 lớp) → approve (chỉ push khi oracle + P7 + P6 đều PASS)
```

**Schema dữ liệu của pipeline (設計書 YAML)** — khác FlowIR:
- `scenario_flow` blocks (26 loại — xem bảng đầy đủ trong `pipeline/CLAUDE.md` mục "AIの担当スコープ")
- Output cuối là BIVR JSON (Brekeke IVR format), không phải FlowIR

---

## 3. Khoảng trống — vì sao 2 luồng CHƯA nối được

| | Webapp (FlowIR) | Pipeline (設計書 YAML) |
|---|---|---|
| Schema | 11 `NodeType`, phẳng (nodes+edges) | 26 block type, lồng nhau (`scenario_flow` + `step_details` + `termination_patterns`) |
| Định dạng lưu | YAML riêng trên Google Drive | YAML trên filesystem (`output/scenarios/{施設}_{flow}/`), rồi build ra `.bivr` |
| Ai đọc/ghi | Trình duyệt, qua Drive REST API | Script Python + Claude agent, local CLI |

→ **Chưa có adapter** đọc 設計書 YAML thành FlowIR (để hiển thị lên canvas) hay ngược lại (để pipeline
tiêu thụ file người dùng vẽ trên webapp). Đây chính là phần "Phase 4" đã ghi trong `MERGE_PLAN.md`
(`fromDesignYaml.ts` / `toDesignYaml.ts`, bảng map 26 block type → 11 NodeType, yêu cầu round-trip
lossless — diff = 0 hoặc `qa_validator.py` PASS như nhau trước/sau).

---

## 4. Việc cần làm trước khi chỉnh sâu (theo yêu cầu hiện tại)

Tài liệu này dừng ở mô tả — **chưa đổi code**. Bước tiếp theo đề xuất (chờ xác nhận):
1. Chốt bảng map 26 block type ↔ 11 NodeType (đã có nháp trong `MERGE_PLAN.md` §Phase 4.1).
2. Viết `fromDesignYaml.ts` / `toDesignYaml.ts` là hàm thuần trong `src/ir/`.
3. Test round-trip bằng dữ liệu thật trong `pipeline/output/scenarios/`.
4. Sau khi round-trip ổn, chỉnh `files/` để browse được `pipeline/output/scenarios/{施設}_{flow}/`.
