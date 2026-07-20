# Brekeke Custom Modules (IVR)

**🇻🇳 Tiếng Việt** · [🇯🇵 日本語](#-日本語)

Bộ module tùy chỉnh cho Brekeke IVR dùng cho cơ sở y tế (phòng khám). Mỗi module là
JavaScript được dán vào node IVR của Brekeke PBX / CTI để chạy, dựa trên runtime API
của `$runner` (`getProperty` / `getLogger` / `getModuleResult`, ...).

## Module chính

| Module | Mô tả | Vị trí |
| --- | --- | --- |
| **Phone Normalization** | Chuẩn hóa số điện thoại Nhật dựa trên danh sách mã vùng | [`modules/phone-normalization/`](modules/phone-normalization/) |
| **Module Result Binder** | Lấy kết quả module khác, gán vào biến & lưu DB | [`modules/module-result-binder/`](modules/module-result-binder/) |
| **DOB Re-confirmation** | Chuẩn hóa & xác nhận lại ngày sinh (DTMF/giọng nói) | [`modules/dob-reconfirmation/`](modules/dob-reconfirmation/) |
| **Clinic Day Classifier** | Phân loại ngày khám/nghỉ (cuối tuần, ngày lễ, ngày nghỉ) | [`modules/clinic-day-classifier/`](modules/clinic-day-classifier/) |
| **Clinical Department Classifier** | Phân loại khoa khám từ lời nói của bệnh nhân | [`modules/clinical-department-classifier/`](modules/clinical-department-classifier/) |

Mỗi thư mục module chứa phần cài đặt (`.js`) và tài liệu đặc tả:
`SRS_*.md` (tiếng Nhật) và `SRS_*.vi.md` (tiếng Việt).

## Module phụ trợ

`shared/` chứa các module dùng chung/phụ trợ được các module trên gọi tới
(nhập DTMF, AmiVoice STT, Speech to Text / Text to Speech, bộ đếm retry, lưu DB, ...).

## Tài liệu

- [`docs/IVR_Modules_Full_Documentation.md`](docs/IVR_Modules_Full_Documentation.md) — đặc tả tổng thể
- [`docs/00_README.md`](docs/00_README.md) — README gốc của bộ tài liệu

## Kiểm thử

DOB Re-confirmation có unit test:

```bash
node "modules/dob-reconfirmation/dob-reconfirmation.test.js"
```

## ⚠️ Về thông tin bí mật

API key và các thông tin nhạy cảm **không** được đưa vào repo (đã loại qua `.gitignore`).
`OpenAI API.txt` chỉ nằm ở máy local, không commit.

---

## 🇯🇵 日本語

医療機関向け IVR 用の Brekeke カスタムモジュール集。各モジュールは Brekeke PBX / CTI の
IVR ノードに貼り付けて実行する JavaScript で、`$runner`（`getProperty` / `getLogger` /
`getModuleResult` など）のランタイム API を前提としています。

### 主要モジュール

| モジュール | 説明 | 場所 |
| --- | --- | --- |
| **Phone Normalization** | 日本の電話番号を市外局番リストに基づいて正規化 | [`modules/phone-normalization/`](modules/phone-normalization/) |
| **Module Result Binder** | 他モジュールの実行結果を変数へ束縛・DB保存 | [`modules/module-result-binder/`](modules/module-result-binder/) |
| **DOB Re-confirmation** | 生年月日（DTMF/音声）の正規化と再確認 | [`modules/dob-reconfirmation/`](modules/dob-reconfirmation/) |
| **Clinic Day Classifier** | 診療日/休診日（土日祝・休業日）の判定 | [`modules/clinic-day-classifier/`](modules/clinic-day-classifier/) |
| **Clinical Department Classifier** | 発話から診療科を分類 | [`modules/clinical-department-classifier/`](modules/clinical-department-classifier/) |

各モジュールフォルダには実装（`.js`）と仕様書 `SRS_*.md`（日本語）/ `SRS_*.vi.md`（ベトナム語）を同梱しています。

### 補助モジュール

`shared/` には上記から利用される共通・補助モジュール（DTMF入力、AmiVoice STT、
Speech to Text / Text to Speech、リトライカウンタ、DB保存など）を格納しています。

### ドキュメント

- [`docs/IVR_Modules_Full_Documentation.md`](docs/IVR_Modules_Full_Documentation.md) — 全体仕様
- [`docs/00_README.md`](docs/00_README.md) — 仕様資料の元 README

### テスト

```bash
node "modules/dob-reconfirmation/dob-reconfirmation.test.js"
```

### ⚠️ シークレットについて

API キー等の秘密情報はリポジトリに含めません（`.gitignore` で除外）。
`OpenAI API.txt` はローカル専用で、コミット対象外です。
