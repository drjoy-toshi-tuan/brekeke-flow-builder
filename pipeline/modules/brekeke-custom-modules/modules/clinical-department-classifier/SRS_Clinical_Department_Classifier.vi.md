# 🏥 Clinical Department Classifier

> 📄 Bản dịch tiếng Việt. Bản gốc tiếng Nhật: [SRS_Clinical_Department_Classifier.md](SRS_Clinical_Department_Classifier.md)

## 1. 🎯 Tổng quan (Giải thích đơn giản)

**Clinical Department Classifier** là module nhận **tên khoa khám (診療科名)** mà STT nhận diện được, phân loại chúng vào các **nhóm khoa khám (診療科グループ)** đã được định nghĩa trước, và xuất ra **tên kết quả (結果名)** dùng cho việc phân nhánh luồng. Đồng thời, module lưu tên khoa khám đã nhận diện vào một object, và lưu vào DB khi cần thiết.

Ba vai trò chính như sau:

- **Lấy tên khoa khám** từ module STT nguồn tham chiếu
- **Đối chiếu khớp hoàn toàn (完全一致)** tên khoa khám đã lấy được với các nhóm `clinical_department_1〜10`, và trả về `result_name_i` tương ứng bằng `setResult` (dùng cho phân nhánh luồng)
- **Lưu tên khoa khám** đã lấy được vào **object `clinical_department`**, và tùy chọn **lưu vào DB (`clinicalDepartment`)**

```
┌─────────────────────────────────────────────────┐
│  STT が診療科名を認識(例: 「整形外科」)          │
└─────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│  module から結果取得                              │
│   - TIMEOUT / ERROR → そのまま出力               │
│   - 空 / null      → NO_RESULT                  │
└─────────────────────────────────────────────────┘
             ↓ (有効な値)
┌─────────────────────────────────────────────────┐
│  clinical_department オブジェクトに格納           │
│  (saveDepartment2DB=yes なら DB 保存)            │
└─────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│  clinical_department_1〜10 と完全一致照合         │
│   - 最初にマッチしたグループの result_name を採用 │
│   - どれにもマッチしない → NOT_COVERED           │
└─────────────────────────────────────────────────┘
             ↓
     setResult(結果名 / group_N / NOT_COVERED ...)
```

> 💡 **Ví dụ thực tế:**
> - Đầu ra STT: *「整形外科」(khoa chỉnh hình)* → khớp với `clinical_department_2 = "整形外科;リハビリテーション科"` → xuất `result_name_2 = "orthopedics"`
> - Đầu ra STT: *「内科」(khoa nội)* → không thuộc bất kỳ nhóm nào → `NOT_COVERED`
> - Đầu ra STT: *「TIMEOUT」* → xuất trực tiếp `TIMEOUT` (không phân loại, không lưu)

---

## 2. 📋 Đặc tả (Đơn giản)

| Mục | Nội dung |
|---|---|
| **Tên module** | Clinical Department Classifier (tên log nội bộ: `ClinicalDeptClassifier`) |
| **Chức năng** | Phân loại tên khoa khám mà STT nhận diện vào các nhóm, xuất tên kết quả + lưu vào object + lưu vào DB (tùy chọn) |
| **Đầu vào** | Kết quả của module nguồn tham chiếu (`$runner.getModuleResult(module)`) |
| **Đầu ra (setResult)** | Tên kết quả (`result_name_i`), hoặc `group_N` / `NOT_COVERED` / `NO_RESULT` / `TIMEOUT` / `ERROR` |
| **Tác dụng phụ** | `$runner.setObject("clinical_department", giá trị)`<br>Lưu `clinicalDepartment` vào DB thông qua `save2db` (có điều kiện) |

### 🔁 Luồng xử lý

```
┌─────────────────────────────────────────────────────┐
│  開始                                                │
│    ↓                                                 │
│  module が空? → YES → setResult("NO_RESULT")        │
│                       + Error を throw(終了)        │
│    ↓ NO                                              │
│  getModuleResult(module) で結果取得                   │
│    ↓                                                 │
│  null / undefined? → YES → setResult("NO_RESULT")   │
│    ↓ NO                                              │
│  値を .trim()                                        │
│    ↓                                                 │
│  "TIMEOUT" / "ERROR"? → YES → setResult(その値)     │
│    ↓ NO                                              │
│  空文字? → YES → setResult("NO_RESULT")             │
│    ↓ NO(有効な診療科名)                            │
│  setObject("clinical_department", 値)                │
│  saveDepartment2DB = yes? → DB 保存                  │
│    ↓                                                 │
│  finalRes = "NOT_COVERED"(初期値)                  │
│  for i = 1..10:                                      │
│    clinical_department_i を ; で分割し完全一致照合    │
│    マッチ?                                           │
│      → result_name_i あり → finalRes = result_name_i │
│      → result_name_i なし → finalRes = "group_i"     │
│      → break(最初のマッチで確定)                    │
│    ↓                                                 │
│  setResult(finalRes)                                 │
└─────────────────────────────────────────────────────┘
```

### 📤 Giá trị trả về của setResult

| Giá trị | Ý nghĩa |
|---|---|
| *(giá trị của result_name_i)* | Khớp với nhóm `i`, và `result_name_i` đã được thiết lập |
| `group_N` | Khớp với nhóm `N` nhưng `result_name_N` chưa được thiết lập (fallback) |
| `NOT_COVERED` | Lấy được tên khoa khám hợp lệ, nhưng không khớp với bất kỳ nhóm nào |
| `NO_RESULT` | `module` chưa được thiết lập, hoặc nguồn tham chiếu trả về `null`/`undefined`/chuỗi rỗng |
| `TIMEOUT` | Module nguồn tham chiếu trả về `TIMEOUT` (đi qua trực tiếp) |
| `ERROR` | Module nguồn tham chiếu trả về `ERROR` (đi qua trực tiếp) |

> 📌 Trong trường hợp `module` chưa được thiết lập, sau khi thực hiện `setResult("NO_RESULT")`, module sẽ **throw `Error` và kết thúc**.

---

## 3. 🛠️ Cách sử dụng (Chi tiết)

### 3.1. Thiết lập thuộc tính

| Tên thuộc tính (tiếng Nhật) | Tên thuộc tính (mã code) | Bắt buộc | Mặc định | Mô tả |
|---|---|:---:|---|---|
| **Tên module nguồn tham chiếu** | `module` | ✅ **Bắt buộc** | *(rỗng)* | Node Name của module STT nguồn tham chiếu để lấy tên khoa khám. Nếu chưa thiết lập, sẽ xuất `NO_RESULT` rồi kết thúc bằng ngoại lệ (exception). |
| **Cờ lưu DB** | `saveDepartment2DB` | ⚪ Tùy chọn | `no` | `yes` = lưu tên khoa khám vào DB dưới dạng `clinicalDepartment` (displayType: `DEPARTMENT`). `no` = không lưu. |
| **Nhóm khoa khám 1〜10** | `clinical_department_1` 〜 `clinical_department_10` | ⚪ Tùy chọn | *(rỗng)* | Tên các khoa khám thuộc nhóm. Có thể chỉ định nhiều giá trị bằng **dấu phân cách chấm phẩy (`;`)** (mỗi phần tử được loại bỏ khoảng trắng trước và sau khi đối chiếu). |
| **Tên kết quả 1〜10** | `result_name_1` 〜 `result_name_10` | ⚪ Tùy chọn | *(rỗng)* | Giá trị được trả về bằng `setResult` khi khớp với `clinical_department_i` tương ứng. Nếu chưa thiết lập, `group_i` sẽ được dùng làm fallback. |

> 📌 `clinical_department_i` và `result_name_i` **tương ứng với nhau qua cùng một số `i` (1〜10)**. Các nhóm được kiểm tra theo thứ tự số (1→10), và **được xác định ở nhóm khớp đầu tiên** (các nhóm sau đó không được kiểm tra).

### 3.2. Cơ chế đối chiếu (matching)

- Kết quả của STT được đối chiếu sau khi **loại bỏ khoảng trắng trước và sau (`trim`)**.
- Mỗi nhóm được tách bằng `;`, và được so sánh với từng tên khoa khám theo **khớp hoàn toàn (完全一致) (phân biệt chữ hoa/chữ thường và cách viết khác nhau)**. Không phải khớp phần đầu hay khớp một phần.
- Do đó, tất cả các **cách viết khác nhau (biệt danh, chữ kana, chữ latin, v.v.)** mà STT có thể trả về cần được liệt kê bằng `;` trong cùng một nhóm.

Ví dụ:
```
clinical_department_1 = 内科;一般内科;ないか
result_name_1         = general_medicine
```
→ Dù STT trả về `内科` / `一般内科` / `ないか`, tất cả đều được phân loại thành `general_medicine`.

### 3.3. Ví dụ sử dụng

#### 🎬 Kịch bản 1: Phân loại khoa khám vào các nhóm (phân nhánh luồng)

| Thuộc tính | Giá trị |
|---|---|
| `module` | `stt_department` |
| `clinical_department_1` | `内科;呼吸器内科;消化器内科` |
| `result_name_1` | `general_medicine` |
| `clinical_department_2` | `整形外科;リハビリテーション科` |
| `result_name_2` | `orthopedics` |

**Thực thi:**
- Đầu ra STT: `整形外科`
- Object `clinical_department` = `整形外科`
- Khớp với nhóm 2 → `setResult`: `orthopedics`
- Ở node kế tiếp, phân nhánh sang nhánh `orthopedics`

#### 🎬 Kịch bản 2: Không thuộc nhóm nào (NOT_COVERED)

| Thuộc tính | Giá trị |
|---|---|
| `module` | `stt_department` |
| `clinical_department_1` | `整形外科;リハビリテーション科` |
| `result_name_1` | `orthopedics` |

**Thực thi:**
- Đầu ra STT: `皮膚科`
- Object `clinical_department` = `皮膚科`
- Không khớp với bất kỳ nhóm nào → `setResult`: `NOT_COVERED`
- Phân nhánh sang nhánh hướng dẫn "Đây là khoa khám không được hỗ trợ"

#### 🎬 Kịch bản 3: result_name chưa được thiết lập (fallback group_N)

| Thuộc tính | Giá trị |
|---|---|
| `module` | `stt_department` |
| `clinical_department_3` | `小児科` |
| `result_name_3` | *(chưa thiết lập)* |

**Thực thi:**
- Đầu ra STT: `小児科`
- Khớp với nhóm 3 nhưng `result_name_3` rỗng → `setResult`: `group_3` (xuất log cảnh báo)

#### 🎬 Kịch bản 4: Lưu tên khoa khám vào DB

| Thuộc tính | Giá trị |
|---|---|
| `module` | `stt_department` |
| `saveDepartment2DB` | `yes` |
| `clinical_department_1` | `内科` |
| `result_name_1` | `general_medicine` |

**Thực thi:**
- Đầu ra STT: `内科`
- Lưu DB: `clinicalDepartment = 内科` (displayType: `DEPARTMENT`)
- Object `clinical_department` = `内科`
- `setResult`: `general_medicine`

> 📌 Việc lưu DB và lưu vào object được thực hiện tại thời điểm lấy được tên khoa khám hợp lệ (được thực hiện ngay cả trong trường hợp `NOT_COVERED` khi không khớp với nhóm nào).

### 3.4. Lưu ý quan trọng

> ⚠️ **`module` là bắt buộc** — Trong trường hợp chưa thiết lập, sau khi `setResult("NO_RESULT")`, module sẽ throw `Error` (`module property is required`) và kết thúc xử lý.
>
> ⚠️ **Đối chiếu bằng khớp hoàn toàn** — Kết quả STT được so sánh **khớp hoàn toàn** với từng tên khoa khám sau khi `trim`. Hãy liệt kê tất cả các cách viết khác nhau trong `clinical_department_i`, phân cách bằng `;`.
>
> ⚠️ **Khớp đầu tiên được ưu tiên** — Các nhóm được đánh giá theo thứ tự số (1→10), và được xác định tại thời điểm khớp đầu tiên. Nếu cùng một tên khoa khám được đăng ký trùng lặp ở nhiều nhóm, nhóm có số nhỏ hơn sẽ được ưu tiên.
>
> ⚠️ **`clinical_department` chứa giá trị STT thô** — Giá trị được lưu vào object không phải là kết quả phân loại (`result_name`), mà chính là tên khoa khám mà STT trả về. Ở phần kế tiếp có thể tham chiếu dưới dạng `<%clinical_department%>`.
>
> ⚠️ **`TIMEOUT` / `ERROR` đi qua trực tiếp** — Trong trường hợp này, việc lưu vào object, lưu DB và xử lý phân loại đều không được thực hiện. Hãy xử lý ở một nhánh luồng khác.
>
> ⚠️ **Giá trị lưu DB chính là tên khoa khám** — `contextName = clinicalDepartment`, `displayType = DEPARTMENT`, `value =` tên khoa khám đã lấy được (không phải `result_name`).

---

## 4. 📊 Các mẫu sử dụng thường gặp

| Trường hợp sử dụng | Cách thiết lập |
|---|---|
| Chia khoa khám thành vài nhóm để phân nhánh luồng | Thiết lập `clinical_department_1〜N` + `result_name_1〜N` |
| Gộp các cách viết khác nhau, biệt danh vào 1 nhóm | Liệt kê trong một `clinical_department_i` phân cách bằng `;` (ví dụ: `内科;一般内科;ないか`) |
| Đọc lại, tái sử dụng tên khoa khám đã nhận diện ở phần kế tiếp | Tham chiếu `<%clinical_department%>` (không cần thiết lập, tự động lưu khi có giá trị hợp lệ) |
| Lưu tên khoa khám vào DB dưới dạng thông tin bệnh nhân | `saveDepartment2DB = yes` |
| Chuyển khoa khám không được hỗ trợ sang nhánh chuyên dụng | Phân nhánh bằng giá trị trả về `NOT_COVERED` |
| Thử lại (retry) khi bất thường (timeout/lỗi) | Phân nhánh bằng giá trị trả về `TIMEOUT` / `ERROR` |
