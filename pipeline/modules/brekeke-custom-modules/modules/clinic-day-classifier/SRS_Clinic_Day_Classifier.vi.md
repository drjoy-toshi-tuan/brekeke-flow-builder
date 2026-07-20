# 📅 Date Classifier (Clinic Day Classifier)

> 📄 Bản dịch tiếng Việt. Bản gốc tiếng Nhật: [SRS_Clinic_Day_Classifier.md](SRS_Clinic_Day_Classifier.md)

## 1. 🎯 Tổng quan (Giải thích đơn giản)

**Date Classifier** phân tích nội dung phát ngôn của khách hàng để **xác định ngày hẹn mong muốn**, và **đánh giá xem ngày đó có phải ngày nghỉ khám (休診日) của bệnh viện hay không**. Toàn bộ xử lý chạy **cục bộ (local)**, **không dùng LLM/OpenAI**.

### 🧠 Logic xử lý

```
Khách hàng phát ngôn / nhập ngày
        ↓
Step0: Phát hiện "không rõ / không nhớ" hoặc "không có nguyện vọng" → trả 不明
        ↓
Step1: Parser cục bộ (ngày cụ thể)
  - "yyyy年M月d日" / "M月d日"
  - "来週月曜日" / "来月15日"
  - DTMF 8 số / yyyy/M/d / yyyy-MM-dd
        ↓
  Có ngày cụ thể? ── CÓ ──┐
        ↓ KHÔNG           │
Step2: Chỉ định tháng mơ hồ?
  - "11月" / "来月"
  - "11月上旬/中旬/下旬"
    (nếu xác định được tháng → vague)
  - Chỉ có 旬 mà không có tháng → vô hiệu
        │vague   │none      │
        ▼        ▼          ▼
    business  NO_RESULT  Đánh giá ngày nghỉ
    (mơ hồ)              - Thứ 7 / CN?
                         - Ngày lễ (CSV Nội các)?
                         - Ngày nghỉ riêng của viện?
                         - Trong khoảng blockDays?
                              ↓
        Tất cả đều nghỉ → NON_BUSINESS_DAY / còn lại → business
                              ↓
        Output của business theo output_type
        (日時 → yyyy-MM-dd 00:00 / フリーテキスト → text gốc STT)
```

> 💡 **Ví dụ (hôm nay = 2026-07-06 Thứ 2, output_type=日時):**
> - *「来週の水曜日にお願いします」* → `2026-07-15` → ngày làm việc → **`2026-07-15 00:00`**
> - *「12月29日」* (ngày nghỉ riêng) → **`NON_BUSINESS_DAY`**
> - *「11月」* / *「11月上旬」* → không có ngày cụ thể + có tháng → business (mơ hồ). Nếu `日時` → **`NO_RESULT`**, nếu `フリーテキスト` → text gốc STT
> - *「上旬」* (không chỉ định tháng) → **`NO_RESULT`**
> - *「えーっと」* (không có ngày) → **`NO_RESULT`**

---

## 2. 📋 Đặc tả (Đơn giản)

| Mục | Nội dung |
|---|---|
| **Tên module** | Date Classifier (tên log nội bộ: `checkClosedDay`) |
| **Chức năng** | Phân tích ngày từ text, đánh giá ngày nghỉ khám (chỉ cục bộ, không LLM) |
| **Đầu vào** | Kết quả của module STT/DTMF (`$runner.getModuleResult(module)`) |
| **Đầu ra (setResult)** | `output_type=日時`: `yyyy-MM-dd 00:00` / `output_type=フリーテキスト`: text gốc STT / `NON_BUSINESS_DAY` / `NO_RESULT` / `不明` |
| **Tác dụng phụ** | Set biến `checked_dates`, `closed_dates` (`$runner.set`), `available_date_full`, `available_date_short` (`$runner.setObject`). Lưu DB khi có `contextName`+`contextDisplayType` |

### 📑 Các pattern parser cục bộ nhận diện

#### Ngày cụ thể (Step1)

| Pattern | Ví dụ input | Output |
|---|---|---|
| DTMF 8 số (yyyyMMdd) | `20261215` | `2026-12-15` (ngày không tồn tại → `NO_RESULT`; ngày quá khứ phụ thuộc `acceptPastDay`) |
| DTMF 4 số (MMdd) | `1215` | `2026-12-15`… (năm được fill theo `acceptPastDay`) |
| yyyy-MM-dd hh:mm | `2026-12-15 09:30` | `2026-12-15` |
| yyyy/M/d | `2026/12/15` | `2026-12-15` |
| yyyy年M月d日 | `2026年12月15日` | `2026-12-15` |
| M月d日 (không năm) | `12月15日` | `2026-12-15`… (năm được fill theo `acceptPastDay` — giống DTMF 4 số) |
| 来月/再来月 + ngày | `来月15日`, `再来月3日と5日` | `2026-08-15`, `2026-09-03`, `2026-09-05` |
| 今週/来週/再来週 + thứ | `来週月曜日`, `再来週水曜と木曜` | ngày tương ứng |
| Thứ đơn lẻ | `月曜日に` | Thứ 2 gần nhất sau hôm nay |

> 📌 Tuần tính theo **bắt đầu từ Thứ 2**. Nhiều ngày (phân cách と/や/、/・) tối đa 3 ngày.

#### Chỉ định tháng mơ hồ (Step2 — chỉ khi Step1 không ra ngày cụ thể)

| Ví dụ input | Kết quả | Ghi chú |
|---|---|---|
| `11月`, `来月`, `再来月`, `今月` | **business (mơ hồ)** | Hiểu là "ngày nào trong tháng cũng được" |
| `11月上旬`, `来月中旬`, `今月下旬` | **business (mơ hồ)** | Xác định được tháng → business |
| `上旬`, `中旬`, `下旬` (không có tháng) | **NO_RESULT** | 旬 bắt buộc phải có ngữ cảnh tháng |

> 📌 Với input mơ hồ, do không xác định được ngày cụ thể nên **KHÔNG đánh giá ngày nghỉ / lead-time**, coi là business (giả định khách có thể linh động trong tháng). Giá trị output theo `output_type` (xem dưới).

### 📑 Chế độ lọc ngày nghỉ (closedDayMode)

| Mode | Coi là ngày nghỉ |
|---|---|
| `なし` | Không lọc (chỉ ngày nghỉ riêng của viện) |
| `土日祝日` | Thứ 7 + Chủ nhật + ngày lễ |
| `祝日` | Chỉ ngày lễ quốc gia |
| `土日` | Thứ 7 + Chủ nhật |
| `日祝日` | Chủ nhật + ngày lễ (Thứ 7 là ngày làm việc) |
| `土` | Chỉ Thứ 7 |
| `日` | Chỉ Chủ nhật |

> ℹ️ Ngày trong **customHoliday CSV** luôn được coi là ngày nghỉ bất kể `closedDayMode`.
> 📌 `closedDayMode` dùng chung cho **cả** việc xác định ngày nghỉ **và** đếm ngày nghiệp vụ của `blockDays` (gộp từ `dateFilterMode` + `blockDaysSkip` cũ).

### 📤 Giá trị trả về của setResult

| Giá trị | Ý nghĩa |
|---|---|
| `yyyy-MM-dd 00:00` | Ngày làm việc (`output_type=日時`). Trả ngày cụ thể đầu tiên |
| *(text gốc STT)* | Ngày làm việc (`output_type=フリーテキスト`). Trả nguyên input |
| `NON_BUSINESS_DAY` | TẤT CẢ ngày cụ thể được chỉ định đều là ngày nghỉ / khoảng không nhận |
| `PAST_DAY` | Có chứa ngày quá khứ (chỉ khi `acceptPastDay=no`; nếu `yes` thì coi là business) |
| `不明` | Phát ngôn kiểu "không rõ / chưa quyết / không nhớ", hoặc **từ chối / không có nguyện vọng** ("希望なし" / "希望がない" / "希望しません" / "特にない" / "ありません") |
| `NO_RESULT` | Không parse được ngày / ngày không tồn tại / chỉ có 旬 mà thiếu tháng / mơ hồ + `日時` không trả được ngày cụ thể |

> 📌 **Quy tắc đánh giá (đã bỏ `partialClosedDayMode`):** Khi chỉ định nhiều ngày cụ thể, **chỉ khi TẤT CẢ đều là ngày nghỉ / không nhận** mới trả `NON_BUSINESS_DAY`. Chỉ cần 1 ngày là ngày làm việc thì coi là business.

---

## 3. 🛠️ Cách sử dụng (Chi tiết)

### 3.1. Thiết lập property

| Tên property (JP) | Tên property (code) | Bắt buộc | Mặc định | Mô tả |
|---|---|:---:|---|---|
| **Module tham chiếu** | `module` | ⚪ | `stt` | Tên module STT/DTMF chứa phát ngôn khách hàng |
| **Nguồn ngày lễ (CSV)** | `holidaySource` | ⚪ | *(rỗng)* | URL CSV ngày lễ (định dạng Nội các, Shift_JIS, `yyyy/M/d,tên lễ`). **Chỉ load từ năm nay trở đi**. Không set → bỏ qua đánh giá ngày lễ |
| **Nguồn ngày nghỉ riêng (CSV)** | `customHoliday` | ⚪ | *(rỗng)* | URL CSV ngày nghỉ riêng (UTF-8, `yyyy-MM-dd,tên` hoặc chỉ `yyyy-MM-dd`). Tháng/ngày được chuẩn hóa 0-pad |
| **Service account key** | `serviceAccountKey` | ⚪ | *(rỗng)* | Toàn bộ JSON key của Google service account. Khi set, module tải `holidaySource` / `customHoliday` qua Drive API kể cả khi link Drive không còn public (xem "Tải file Drive không public" bên dưới) |
| **Chế độ loại trừ** | `closedDayMode` | ⚪ | `土日祝日` | Chế độ chung cho ngày nghỉ + đếm ngày nghiệp vụ: `土日祝日` / `祝日` / `日祝日` / `土日` / `土` / `日` / `なし` |
| **Số ngày nghiệp vụ tới khi nhận**<br>(0=hôm nay, 1=ngày khám kế…) | `blockDays` | ⚪ | `0` | Số ngày không nhận tính từ hôm nay (lead-time). `0`=nhận từ hôm nay. Không phải số → coi là `0` |
| **Định dạng kết quả xuất** | `output_type` | ⚪ | `日時` | Output khi business: `日時` = `yyyy-MM-dd 00:00`, `フリーテキスト` = text gốc STT |
| **去日受付 (nhận ngày quá khứ)** | `acceptPastDay` | ⚪ | `no` | Có nhận ngày quá khứ không. `no` = ngày quá khứ → `PAST_DAY`. `yes` = coi ngày quá khứ là business (vẫn check ngày nghỉ/`closedDayMode`) |
| **Tên context** | `contextName` | ⚪ | *(rỗng)* | Tên field context khi lưu DB. Chỉ lưu DB khi set **cả hai** với `contextDisplayType` |
| **Kiểu hiển thị context** | `contextDisplayType` | ⚪ | *(rỗng)* | Display type trên DB (vd `Text`, `Date`). Chỉ lưu DB khi set **cả hai** với `contextName` |

> 📌 Việc đếm ngày nghiệp vụ của `blockDays` sẽ bỏ qua (skip) các ngày nghỉ theo `closedDayMode` (bao gồm ngày nghỉ riêng). Nếu `closedDayMode=なし` thì gần như đếm theo ngày lịch (chỉ skip ngày nghỉ riêng).

### 3.2. Hiểu về `blockDays` và `closedDayMode`

`blockDays` = **số ngày nghiệp vụ (lead-time) tới khi bắt đầu nhận**.
- `0` = nhận từ hôm nay (không chặn)
- `1` = nhận từ ngày khám kế tiếp
- `2` = nhận từ ngày khám thứ hai…

> 📌 **Quan trọng:** Nếu hôm nay là ngày khám (không thuộc ngày nghỉ theo `closedDayMode`) thì **hôm nay cũng được tính là ngày thứ 1**.

Ví dụ: `closedDayMode=土日祝日`

| Hôm nay | `blockDays` | Xử lý | Ngày đặt sớm nhất |
|---|---|---|---|
| Thứ 2 (10/20) | `1` | hôm nay=ngày 1 → ngày khám kế | Thứ 3 (10/21) |
| Thứ 6 (10/24) | `1` | hôm nay=ngày 1 → ngày khám kế (skip T7/CN) | Thứ 2 (10/27) |
| Thứ 7 (10/25) | `1` | hôm nay T7=skip → Thứ 2=ngày 1 → ngày kế | Thứ 3 (10/28) |

> 🔁 Nếu khách chỉ định **ngày quá khứ**, luôn bị chặn bất kể `blockDays`.

### 3.3. Ví dụ sử dụng

#### 🎬 Kịch bản 1: Ngày làm việc (output 日時)

**Node trước:** STT lấy *「来週の月曜日にお願いします」* (hôm nay = Thứ 5 10/17)

| Property | Giá trị |
|---|---|
| `closedDayMode` | `土日祝日` |
| `blockDays` | `0` |
| `output_type` | `日時` |

**Kết quả:**
- Parse: `[2024-10-21]` (Thứ 2 tuần sau) → ngày làm việc
- setResult = `2024-10-21 00:00`
- `checked_dates` = `["2024-10-21"]`, `closed_dates` = *""*

#### 🎬 Kịch bản 2: Nhiều ngày (không phải tất cả đều nghỉ → business)

**Node trước:** STT lấy *「来月の3日と4日」*

**Kết quả:**
- Parse: `[2024-11-03, 2024-11-04]`
- `11-03`=Chủ nhật (nghỉ), `11-04`=Thứ 2 (làm việc) → **không phải tất cả nghỉ** → business
- `output_type=日時` → `2024-11-03 00:00` (ngày đầu tiên)
- `closed_dates` = `"2024-11-03(日曜日)"`

> ※ Chỉ khi TẤT CẢ ngày đều nghỉ mới trả `NON_BUSINESS_DAY`.

#### 🎬 Kịch bản 3: Lead-time (khoảng không nhận)

**Node trước:** STT lấy *「明日お願いします」* (hôm nay = Thứ 4 10/16)

| Property | Giá trị |
|---|---|
| `blockDays` | `2` |
| `closedDayMode` | `土日祝日` |

**Kết quả:**
- Parse: `[2024-10-17]` (Thứ 5 ngày mai)
- Hôm nay (T4)=ngày 1, mai (T5)=ngày 2 → nhận từ Thứ 6 → Thứ 5 không nhận
- Tất cả không nhận → `NON_BUSINESS_DAY`
- `closed_dates` = `"2024-10-17(受付不可期間)"`
- `available_date_full` = `"2024年10月18日"`, `available_date_short` = `"10月18日"`

#### 🎬 Kịch bản 4: Chỉ định tháng mơ hồ

**Node trước:** STT lấy *「11月上旬でお願いします」*

| Property | Giá trị |
|---|---|
| `output_type` | `フリーテキスト` (hoặc `日時`) |

**Kết quả:**
- Không có ngày cụ thể + có tháng → business (mơ hồ)
- `output_type=フリーテキスト` → setResult = `"11月上旬でお願いします"` (text gốc)
- `output_type=日時` → setResult = `NO_RESULT` (không trả được ngày cụ thể)

#### 🎬 Kịch bản 5: Lưu DB

**Node trước:** STT lấy *「2026年8月20日」*

| Property | Giá trị |
|---|---|
| `output_type` | `日時` |
| `contextName` | `appointment_date` |
| `contextDisplayType` | `Date` |

**Kết quả:**
- Ngày làm việc → setResult = `2026-08-20 00:00`
- Lưu vào field `appointment_date` (displayType: Date) giá trị `2026-08-20 00:00`
- Khi lưu thành công, tham chiếu được qua `<%appointment_date%>`

### 3.4. Tham khảo định dạng CSV

#### holidaySource (định dạng Nội các — Shift_JIS)
```
国民の祝日・休日月日,国民の祝日・休日名称
2026/1/1,元日
2026/1/12,成人の日
2026/2/11,建国記念の日
```
> Dòng header (chứa `国民の祝日` hoặc `月日`) và dòng của năm trước năm nay sẽ bị bỏ qua.

#### customHoliday (UTF-8)
```
2026-12-29,年末休診
2026-12-30,年末休診
2027-01-02
2027-01-03,年始休診
```
> Dòng không có tên được đăng ký là `病院休診日`.

#### Tải file Drive không public (service account)
Khi chính sách chia sẻ của Drive tắt "Bất kỳ ai có link" và không thể tải trực tiếp từ URL public nữa, hãy set `serviceAccountKey` để tải file không public qua Drive API.

1. Tạo service account trên GCP và tải file JSON key.
2. Chia sẻ file CSV (hoặc folder cha) cho `client_email` trong key với quyền **Viewer**.
3. Dán toàn bộ JSON key vào property `serviceAccountKey`. `holidaySource` / `customHoliday` vẫn để URL chia sẻ Drive như cũ (dạng `.../file/d/<ID>/view` hoặc `...?id=<ID>`).

Hành vi khi đã set:
- Nếu URL là của Drive và có `serviceAccountKey`: module trích `fileId`, tự ký JWT (RS256, scope=`drive.readonly`), đổi lấy `access_token` tại `oauth2.googleapis.com/token`, rồi tải `https://www.googleapis.com/drive/v3/files/<fileId>?alt=media` kèm Bearer token.
- URL không phải Drive, hoặc chưa set `serviceAccountKey`: vẫn dùng GET thường (cho URL public). Nếu lấy token thất bại cũng fallback về GET thường.
- ⚠️ Private key được lưu trong property, nên hãy chú ý quyền xem cấu hình module.

### 3.5. Lưu ý quan trọng

> ⚠️ **Không dùng LLM:** Module chỉ phân tích cục bộ (đã bỏ gọi OpenAI). Phát ngôn không parse được sẽ trả `NO_RESULT`.
>
> ⚠️ **DTMF 8 số (yyyyMMdd):** Chỉ nhận ngày lịch có thật (có xét năm nhuận; `20260230` / `20260631` / `20263041`… ngày không tồn tại → `NO_RESULT`). Ngày quá khứ: `acceptPastDay=no` → `PAST_DAY`, `yes` → business (vẫn check ngày nghỉ).
>
> ⚠️ **DTMF 4 số (MMdd):** Năm được fill theo `acceptPastDay`.
>   - `no` : ngày **tương lai gần nhất** (năm nay nếu chưa qua, đã qua thì năm sau). ※Không bao giờ ra ngày quá khứ nên cũng không phát sinh `PAST_DAY`.
>   - `yes`: chọn năm nay / năm sau — cái nào **gần hôm nay hơn** (cho phép quá khứ). VD: hôm nay=07-06, `0106` → `2026-01-06` (gần hơn 2027).
>
> ⚠️ **去日受付 (`acceptPastDay`):** Điều khiển hành vi khi ngày cụ thể là ngày quá khứ.
>   - `no` (mặc định): chỉ cần 1 ngày quá khứ → trả `PAST_DAY` (ưu tiên hơn đánh giá ngày nghỉ).
>   - `yes`: coi ngày quá khứ là business, **vẫn đánh giá ngày nghỉ / `closedDayMode` / customHoliday** (ngày quá khứ không bị áp lead-time `blockDays`). Output business theo `output_type`.
>
> ⚠️ **Giới hạn tối đa 3 ngày:** Nếu chỉ định từ 4 ngày cụ thể trở lên, chỉ xử lý 3 ngày đầu.
>
> ⚠️ **Fill năm cho `M月d日` (không năm):** giống DTMF 4 số (MMdd), năm được fill theo `acceptPastDay`.
>   - `no` (mặc định): ngày **tương lai gần nhất** (từ hôm nay trở đi giữ năm nay; đã qua thì năm sau).
>   - `yes`: chọn năm nay / năm sau — cái nào **gần hôm nay hơn** (cho phép quá khứ). VD: hôm nay=07-08, `6月30日` → `2026-06-30` (gần hơn 2027).
>
> ⚠️ **Xử lý tháng mơ hồ:** `11月` / `来月` / `11月上旬`… không xác định ngày cụ thể nên không đánh giá ngày nghỉ, coi là business. `output_type=日時` không trả được ngày cụ thể → `NO_RESULT`; `フリーテキスト` → text gốc STT. Nếu chỉ có 旬 (`上旬`…) mà thiếu tháng → `NO_RESULT`.
>
> ⚠️ **Encoding CSV:** holidaySource là **Shift_JIS**, customHoliday là **UTF-8**. HTTP timeout 10 giây (lỗi thì bỏ qua CSV đó và tiếp tục).
>
> ⚠️ **Biến được set sau khi chạy:**
> - `checked_dates`: mảng JSON ngày cụ thể đã parse (khi có ngày cụ thể)
> - `closed_dates`: chuỗi ngày nghỉ kèm lý do (khi có ngày cụ thể)
> - `available_date_full` / `available_date_short`: ngày khám nhận được sớm nhất (luôn tính, `$runner.setObject`)
>
> 📌 **`available_date_full` / `available_date_short`:** Ngày đầu tiên từ hôm nay trở đi thỏa mãn `isClosedDay` (không nghỉ) **và** `isBlockedByLeadTime` (không trong khoảng chặn). Có tính đến `closedDayMode`, `blockDays`, customHoliday (customHoliday luôn bị loại bất kể `closedDayMode`). **Luôn được tính bất kể kết quả parse.**
>
> 📌 **Lưu DB:** Chỉ chạy khi set **cả** `contextName` và `contextDisplayType`, và IVR đang kết nối. Đối tượng lưu là **giá trị output của business** (日時 hoặc text gốc). Không lưu với `NON_BUSINESS_DAY` / `NO_RESULT` / `不明`. Khi lưu thành công, biến cùng tên `contextName` được set.

---

## 4. 📊 Tổng quan luồng đánh giá

```
Text input từ STT/DTMF
        │
        ▼
  Kiểu "không rõ" / "không có nguyện vọng"? ── CÓ → 不明
        │ KHÔNG
        ▼
┌───────────────────────┐
│ Parse ngày cụ thể      │──── có ngày cụ thể ──┐
│ (Step1)                │                       │
└───────────────────────┘                       │
        │ không có                               │
        ▼                                        │
┌───────────────────────┐                        │
│ Chỉ định tháng mơ hồ?  │                        │
│ (Step2)                │                        │
└───────────────────────┘                        │
    │vague       │none                            │
    ▼            ▼                                ▼
 business    NO_RESULT              ┌─────────────────────────┐
 (mơ hồ)                            │ Phân loại (classifyDate) │
    │                               │ - Quá khứ+no → PAST_DAY  │
    │                               │ - isClosedDay?          │
    │                               │ - isBlockedByLeadTime?  │
    │                               │ - Tất cả nghỉ → NON_BUS  │
    │                               └─────────────────────────┘
    │                                         │
    └──────────────┬──────────────────────────┤
                   ▼ (business)               ▼ (tất cả nghỉ)
        Output theo output_type          NON_BUSINESS_DAY
        (日時 → yyyy-MM-dd 00:00
         フリーテキスト → text gốc STT)
                   │
                   ▼
   available_date_full / short luôn được tính & set
```
