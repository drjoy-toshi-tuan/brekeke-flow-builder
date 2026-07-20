# 📞 Phone Normalization

> 📄 Bản dịch tiếng Việt. Bản gốc tiếng Nhật: [SRS_Phone_Normalization.md](SRS_Phone_Normalization.md)

## 1. 🎯 Tổng quan (mô tả đơn giản)

**Phone Normalization** là module xử lý **số điện thoại Nhật Bản**, chủ yếu có 2 chức năng.

### 🔹 CASE A: Trường hợp có module tham chiếu nguồn (STT/DTMF)
Khi khách hàng nhập số điện thoại bằng giọng nói hoặc nhập phím, module thực hiện các bước sau:
1. **Chuẩn hóa** số (chỉ trích xuất các chữ số)
2. **Kiểm tra tính hợp lệ** (nhóm 11 chữ số: 090/080/070/060/050, số cố định 10 chữ số)
3. **Chèn dấu gạch nối theo kiểu Nhật** (ví dụ: `090-1234-5678`, `03-1234-5678`)
4. **Phát lại** số để khách hàng xác nhận (thay thế `#data#` trong prompt)

### 🔹 CASE B: Trường hợp không có module tham chiếu nguồn (xử lý số gọi đến)
Lấy số điện thoại gọi đến của cuộc gọi và thực hiện các bước sau:
1. **Lưu vào cơ sở dữ liệu** (ở dạng chỉ có chữ số, khi `saveAdditionalPhoneNumber2DB = yes`)
2. **Phát lại** cho khách hàng để xác nhận (đọc toàn bộ các chữ số, hoặc chỉ đọc 4 chữ số cuối)

> 💡 **Ví dụ:**
> - Đầu vào: `09012345678` → Đầu ra: `090-1234-5678`
> - Đầu vào: `0312345678` → Đầu ra: `03-1234-5678`
> - Đầu vào: `0422123456` → Đầu ra: `0422-12-3456` (khu vực Musashino)

> 📌 **Về `+81`:** Việc chuyển đổi từ định dạng quốc tế (`+81...`) sang định dạng trong nước (`0...`) **thông thường đã được xử lý ở phía backend**. Bên trong module, việc chuyển đổi dự phòng phần đầu `+81` được thực hiện khi lấy số gọi đến ở CASE B và bên trong `formatJapanesePhone`, nhưng kết quả module ở CASE A được giả định là truyền vào ở định dạng trong nước.

---

## 2. 📋 Đặc tả (đơn giản)

| Mục | Nội dung |
|---|---|
| **Tên module** | Phone Normalization |
| **Chức năng** | Chuẩn hóa, định dạng và phát lại xác nhận số điện thoại Nhật Bản |
| **Phạm vi hỗ trợ** | Số 11 chữ số (090/080/070/060/050), điện thoại cố định (mã vùng 2〜5 chữ số) |
| **Dữ liệu tham chiếu** | Danh sách mã vùng (市外局番) dựa trên kế hoạch đánh số của Bộ Nội vụ và Truyền thông (AREA_2, AREA_3, AREA_4, AREA_5) |
| **Phụ thuộc bên ngoài** | Không (không thực hiện lệnh gọi LLM/HTTP bên ngoài) |

### 📑 Quy tắc định dạng

| Loại | Số chữ số | Ví dụ định dạng | Dấu phân cách | `phone_type` |
|---|:---:|---|---|---|
| Điện thoại di động (090/080/070/060) | 11 | `090-1234-5678` | 3-4-4 | `mobile` |
| Điện thoại IP v.v. (050) | 11 | `050-1234-5678` | 3-4-4 | `landline` |
| Cố định (mã vùng 2 chữ số: 03, 06) | 10 | `03-1234-5678` | 2-4-4 | `landline` |
| Cố định (mã vùng 3 chữ số: 011, 052...) | 10 | `052-123-4567` | 3-3-4 | `landline` |
| Cố định (mã vùng 4 chữ số: 0422...) | 10 | `0422-12-3456` | 4-2-4 | `landline` |
| Cố định (mã vùng 5 chữ số: 04992...) | 10 | `04992-1-2345` | 5-1-4 | `landline` |
| Khác (số 10 chữ số không khớp AREA) | 10 | `XXX-XXX-XXXX` | 3-3-4 (mặc định) | `landline` |

> 📌 **Xác định `phone_type` (`getPhoneType`):** Chỉ khi 3 chữ số đầu là `090/080/070/060` thì mới là `"mobile"`, các trường hợp còn lại (bao gồm `050` và điện thoại cố định) đều là `"landline"`. **`050` được xử lý như điện thoại cố định (điện thoại IP)**.
>
> 📌 **Nhóm kiểm tra số chữ số (CASE A):** Nếu phần đầu là `090/080/070/060/050` → bắt buộc **11 chữ số**, các trường hợp khác → bắt buộc **10 chữ số**. `050` là điện thoại cố định nhưng về mặt kiểm tra số chữ số thì thuộc nhóm 11 chữ số.
>
> 📌 **Nếu không bắt đầu bằng `0` thì INVALID (CASE A):** Số điện thoại trong nước của Nhật luôn bắt đầu bằng `0`. Nếu phần đầu không phải là `0` thì dù số chữ số có khớp cũng bị xử lý là **INVALID** (ví dụ: `9012345678` có 10 chữ số nhưng không có số 0 ở đầu nên là INVALID).

### 🔁 Luồng xử lý

```
┌──────────────────────────────────────────────────┐
│  プロパティ読込: prompt, module,                  │
│    phoneReadingMode, saveAdditionalPhoneNumber2DB │
│    ↓                                             │
│  module が設定されている?                          │
│  ├─ YES (CASE A: STT/DTMF から)                  │
│  │    ↓                                          │
│  │  モジュール結果取得 → 数字以外を除去           │
│  │    (moduleDigits)                            │
│  │    ↓                                          │
│  │  チェック: 先頭0? 11桁系(09/08/07/06/050)? 固定10桁?│
│  │    ├─ 空    → setResult("NO_RESULT")         │
│  │    ├─ 不正  → setResult("INVALID")           │
│  │    └─ 正常  → #data# 置換 + テンプレ変数展開   │
│  │               → prompt 再生 + utterance 保存  │
│  │               saveAdditionalPhoneNumber2DB?   │
│  │                 → yes なら DB 保存             │
│  │               setObject("phone_type", ...)    │
│  │               setResult(フォーマット済み番号)  │
│  │                                               │
│  └─ NO  (CASE B: 着信番号処理)                   │
│       ↓                                          │
│     着信番号を取得(.incomingPhone or IVR)       │
│       → 先頭 +81 を 0 に変換 → 数字以外を除去     │
│       ↓ (番号あり?)                              │
│       ├─ 空    → 何もしない(setResult なし)      │
│       └─ あり:                                   │
│            saveAdditionalPhoneNumber2DB?         │
│              → yes なら DB 保存                   │
│            phoneReadingMode に基づきフォーマット  │
│              (全桁 または 下4桁)                  │
│            setObject("incoming_phone", ...)      │
│            setObject("phone_type", ...)          │
│            テンプレ変数展開 → prompt 再生         │
│            → utterance 保存                       │
│            setResult("INCOMING_PROCESSED")       │
└──────────────────────────────────────────────────┘
```

### 📤 Giá trị trả về của setResult

| Giá trị | Ý nghĩa |
|---|---|
| *(số đã định dạng)* | Chuẩn hóa thành công (CASE A) |
| `INVALID` | Số không hợp lệ (không bắt đầu bằng `0` / số chữ số không thỏa điều kiện: nhóm 11 chữ số nhưng không đủ 11 chữ số / nhóm cố định nhưng không đủ 10 chữ số) |
| `NO_RESULT` | Module tham chiếu nguồn không trả về số (CASE A) |
| `INCOMING_PROCESSED` | Hoàn tất xử lý số gọi đến (CASE B) |
| *(không thiết lập)* | Trong CASE B, nếu không lấy được số gọi đến thì không thực hiện `setResult` |

### 🗂️ Tác dụng phụ (setObject / DB)

| Đối tượng | Thời điểm thiết lập | Nội dung |
|---|---|---|
| `phone_type` (object) | Khi CASE A thành công / khi CASE B có số | `"mobile"` (phần đầu 090/080/070/060) hoặc `"landline"` (050 và cố định) |
| `incoming_phone` (object) | Chỉ CASE B | Giá trị được định dạng để đọc (toàn bộ chữ số = có dấu gạch nối, 4 chữ số cuối = phân cách bằng khoảng trắng). Tham chiếu bằng `<%incoming_phone%>` |
| `additionalPhoneNumber` (object) | Khi lưu DB thành công (cả hai CASE) | Số chỉ gồm chữ số (bằng với giá trị lưu DB) |
| `additionalPhoneNumber` (DB context) | Khi `saveAdditionalPhoneNumber2DB = yes` (cả hai CASE) | `contextName=additionalPhoneNumber` / `displayType=PHONE_NUMBER` / `value=` chỉ gồm chữ số |
| `seq` (variable) | Khi lưu utterance thành công | Tăng số thứ tự phát ngôn |

---

## 3. 🛠️ Cách sử dụng (chi tiết)

### 3.1. Thiết lập thuộc tính

| Tên thuộc tính (tiếng Nhật) | Tên thuộc tính (mã) | Bắt buộc | Mô tả | Ví dụ |
|---|---|:---:|---|---|
| **Tên module tham chiếu nguồn** | `module` | ⚪ Tùy chọn | Tên module STT/DTMF tham chiếu nguồn. Có thiết lập → CASE A, không thiết lập → CASE B. | `stt_phone`, `dtmf_phone` |
| **Hướng dẫn** | `prompt` | ✅ Bắt buộc | Hướng dẫn xác nhận. Sử dụng `#data#` (CASE A) hoặc `<%incoming_phone%>` (CASE B) làm placeholder. Các biến template dạng `<%...%>` được triển khai ở cả hai CASE. | `お電話番号は #data# でよろしいでしょうか?` |
| **Chế độ đọc** | `phoneReadingMode` | ⚪ Tùy chọn | Chế độ đọc (**chỉ có hiệu lực ở CASE B**). `下4桁` = chỉ 4 chữ số cuối (phân cách từng ký tự bằng khoảng trắng), các trường hợp khác (bao gồm không thiết lập) = toàn bộ chữ số (có dấu gạch nối). | `下4桁` |
| **Lưu context** | `saveAdditionalPhoneNumber2DB` | ⚪ Tùy chọn | `yes` = lưu vào DB dưới dạng `additionalPhoneNumber`, `no` (mặc định) = không lưu vào DB. Áp dụng cho cả CASE A và CASE B. | `yes` |
| *(biến bên ngoài)* | `.incomingPhone` | ⚪ Tùy chọn | Số gọi đến được truyền từ bên ngoài (CASE B). Nếu không thiết lập thì lấy từ `$ivr.getOtherNumber()`. | `09012345678` |

> 📌 Ở CASE A, `phoneReadingMode` không được tham chiếu (luôn đọc toàn bộ chữ số có dấu gạch nối).

### 3.2. Ví dụ sử dụng

#### 🎬 Kịch bản 1: Xác nhận số do khách hàng phát âm (CASE A)

**Tình huống:** Trường hợp khách hàng phát âm số điện thoại, cần xác nhận và lưu vào DB.

| Bước | Module | Thiết lập thuộc tính |
|---|---|---|
| 1 | STT (Node Name = `stt_phone`) | Nhận dạng số điện thoại từ giọng nói |
| 2 | Phone Normalization | `module = stt_phone`<br>`prompt = お客様のお電話番号は #data# でよろしいでしょうか?`<br>`saveAdditionalPhoneNumber2DB = yes` |

**Kết quả:**
- Khách hàng phát âm: "ぜろきゅう ぜろ いち に さん よん..."
- Đầu ra STT: `09012345678`
- IVR phát lại: *「お客様のお電話番号は 090-1234-5678 でよろしいでしょうか?」*
- Lưu DB: `additionalPhoneNumber = 09012345678` (chỉ chữ số)
- `phone_type` = `mobile`
- `setResult`: `090-1234-5678`

#### 🎬 Kịch bản 2: Xác nhận số gọi đến (đọc toàn bộ chữ số + lưu DB) (CASE B)

| Bước | Module | Thiết lập thuộc tính |
|---|---|---|
| 1 | Phone Normalization | `module =` *(không thiết lập)*<br>`prompt = 発信番号 <%incoming_phone%> からのお電話でよろしいでしょうか?`<br>`phoneReadingMode = 全桁`<br>`saveAdditionalPhoneNumber2DB = yes` |

**Kết quả:**
- IVR phát lại: *「発信番号 090-1234-5678 からのお電話で...」*
- Lưu DB: `additionalPhoneNumber = 09012345678` (chỉ chữ số)
- `setResult`: `INCOMING_PROCESSED`

#### 🎬 Kịch bản 3: Chỉ xác nhận 4 chữ số cuối (mục đích bảo mật) (CASE B)

| Bước | Module | Thiết lập thuộc tính |
|---|---|---|
| 1 | Phone Normalization | `module =` *(không thiết lập)*<br>`prompt = 下4桁が <%incoming_phone%> のお電話でよろしいでしょうか?`<br>`phoneReadingMode = 下4桁` |

**Kết quả:**
- Số gọi đến: `09012345678`
- Biến `incoming_phone` = `"5 6 7 8"` (phân cách bằng khoảng trắng để AmiVoice đọc từng ký tự một)
- IVR phát lại: *「下4桁が 5 6 7 8 のお電話で...」*
- `setResult`: `INCOMING_PROCESSED`

### 3.3. Xử lý đặc biệt

> 🔍 **Nhận diện nhóm 11 chữ số:** Phần đầu `090`, `080`, `070`, `060`, `050` được kiểm tra số chữ số theo nhóm 11 chữ số. Định dạng là 3-4-4 (ví dụ: `050-1234-5678`).
>
> 🔍 **Phân loại `phone_type`:** Chỉ `090/080/070/060` là `mobile`, `050` và điện thoại cố định là `landline`.
>
> 🔍 **Nhận diện mã vùng của điện thoại cố định:** Kiểm tra theo thứ tự 5 chữ số → 4 chữ số → 3 chữ số → 2 chữ số. Ví dụ: `04992` khớp AREA_5 → định dạng `04992-X-XXXX`.
>
> 🔍 **Trường hợp mã vùng không khớp:** Số 10 chữ số không khớp với bất kỳ AREA nào sẽ được định dạng mặc định là `XXX-XXX-XXXX` (3-3-4).
>
> 🔍 **Chế độ "4 chữ số cuối" (CASE B):** **Chèn khoảng trắng giữa từng chữ số** để engine giọng nói (AmiVoice) đọc từng ký tự một. Nhờ đó tránh được cách đọc kiểu "ごせんろっぴゃくななじゅうはち".

### 3.4. Lưu ý

> ⚠️ **Việc chuẩn hóa `+81` đã được thực hiện ở backend** — số truyền vào module được giả định là định dạng trong nước (bắt đầu bằng `0`). Việc lấy số gọi đến ở CASE B và bên trong `formatJapanesePhone` vẫn còn giữ lại phần chuyển đổi dự phòng `+81 → 0` ở đầu, nhưng không áp dụng cho kết quả module ở CASE A.
>
> ⚠️ **Chỉ lưu DB khi `saveAdditionalPhoneNumber2DB = yes`** — áp dụng cho cả CASE A và CASE B. Tên context lưu là `additionalPhoneNumber`, `displayType = PHONE_NUMBER`, giá trị lưu là **chỉ gồm chữ số, không có dấu gạch nối**.
>
> ⚠️ **Ở CASE A, biến `incoming_phone` không được thiết lập** — biến này chỉ dành riêng cho CASE B (`phone_type` được thiết lập ở cả hai CASE).
>
> ⚠️ **Trường hợp `prompt` rỗng**, quá trình xử lý vẫn được thực hiện nhưng **không phát âm thanh** (văn bản phát ngôn được trích xuất từ prompt bằng `$ivr.exec("tts-prompt", "extractTaggedContent", { stripTags: true })`, nhưng kết quả này cũng rỗng nên log utterance cũng không được lưu).
>
> ⚠️ **Ở CASE B, khi không lấy được số gọi đến**, không thực hiện bất kỳ thao tác nào trong số lưu DB, phát lại, `setResult` (`setResult` vẫn giữ trạng thái chưa thiết lập).
