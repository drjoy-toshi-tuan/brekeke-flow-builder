# 📘 Module Result Binder

> 📄 Bản dịch tiếng Việt. Bản gốc tiếng Nhật: [SRS_Module_Result_Binder.md](SRS_Module_Result_Binder.md)

## 1. 🎯 Tổng quan (mô tả đơn giản)

**Module Result Binder** là một module đóng vai trò "cầu nối" (bridge) để truyền dữ liệu giữa các module. Ba chức năng chính của nó như sau.

- **Lấy kết quả đầu ra** của module khác (hoặc **lấy giá trị của biến (object) đã có sẵn**)
- **Lưu kết quả đã lấy vào tên biến (object) được chỉ định** và cho phép tham chiếu ở các module sau dưới dạng `<%変数名%>`
- **Lưu kết quả đã lấy dưới dạng trường DB context** (tùy chọn)

> 💡 **Ví dụ đơn giản:**
> Trong trường hợp module A (STT) lấy được phản hồi "田中太郎", Module Result Binder sẽ lấy kết quả này và lưu vào biến `customer_name`. Sau đó, ở module phát âm thanh có thể sử dụng như *"`<%customer_name%>` 様、ご確認ありがとうございます" (Xin cảm ơn quý khách `<%customer_name%>` đã xác nhận)*. Hơn nữa, nếu thiết lập `contextName` và `contextDisplayType` thì cũng có thể lưu vào DB dưới dạng thông tin bệnh nhân.

> 🔁 **2 chế độ lấy dữ liệu:** Nguồn lấy dữ liệu sẽ thay đổi tùy theo cách chỉ định thuộc tính `module`.
> - **Chế độ kết quả module** (thông thường): Chỉ định Node Name như `module = stt_name` → lấy bằng `getModuleResult`
> - **Chế độ tham chiếu biến**: Chỉ định theo dạng `<%...%>` như `module = <%customer_name%>` → lấy giá trị của biến đã có sẵn bằng `getObject`

---

## 2. 📋 Đặc tả (đơn giản)

| Mục | Nội dung |
|---|---|
| **Tên module** | Module Result Binder |
| **Chức năng chính** | Lấy kết quả của module khác (hoặc giá trị của biến đã có sẵn) và truyền dưới dạng biến + lưu DB context (tùy chọn) |
| **Đầu vào** | Nguồn tham chiếu (`module`: Node Name hoặc `<%変数名%>`), tên biến đích để lưu (`variable`), thiết lập lưu DB (`contextName`, `contextDisplayType`) |
| **Đầu ra (setResult)** | Chuỗi kết quả, hoặc `NO_RESULT` / `time_out` / `error` |
| **Tác dụng phụ** | Lưu biến vào context bằng `$runner.setObject()`<br>Lưu trường context vào DB bằng `save2db` (có điều kiện) |

### 🔁 Luồng xử lý

```
┌─────────────────────────────────────────────────────┐
│  開始                                                │
│    ↓                                                 │
│  プロパティ読込:                                      │
│    module, variable,                                 │
│    contextName, contextDisplayType                   │
│    ↓                                                 │
│  module が <%変数名%> 形式?                           │
│    → YES → getObject(変数名) で取得 (変数参照モード)  │
│    → NO  → getModuleResult(module) で取得            │
│    ↓                                                 │
│  取得結果を .trim() で前後空白除去                     │
│    ↓                                                 │
│  module が空? → YES → setResult("NO_RESULT")        │
│    ↓ NO                                              │
│  結果が "time_out" または "error"?                   │
│    → YES → setResult(その値) ※変数格納・DB保存なし   │
│    ↓ NO                                              │
│  結果が空? → YES → setResult("NO_RESULT")           │
│    ↓ NO                                              │
│  variable が設定されている?                           │
│    → YES → setObject(variable, 結果)                 │
│    → NO  → 格納スキップ                              │
│    ↓                                                 │
│  contextName と contextDisplayType の両方が設定?     │
│   かつ IVR 接続中?                                    │
│    → YES → save2db で DB 保存                       │
│           (保存成功時) setObject(contextName, 結果)  │
│    → NO  → DB保存スキップ                            │
│    ↓                                                 │
│  setResult(結果)                                    │
└─────────────────────────────────────────────────────┘
```

### 📤 Giá trị trả về của setResult

| Giá trị | Ý nghĩa |
|---|---|
| `NO_RESULT` | Thuộc tính `module` chưa được thiết lập, hoặc đầu ra của nguồn lấy dữ liệu (kết quả module / biến tham chiếu) rỗng |
| `time_out` | Module nguồn tham chiếu bị timeout |
| `error` | Module nguồn tham chiếu bị lỗi |
| *(chuỗi kết quả)* | Kết quả bình thường từ nguồn lấy dữ liệu (đã loại bỏ khoảng trắng đầu/cuối) |

---

## 3. 🛠️ Cách sử dụng (chi tiết)

### 3.1. Thiết lập thuộc tính

Thiết lập các mục sau ở tab **Thiết lập thuộc tính** (プロパティ設定).

| Tên thuộc tính (tiếng Nhật) | Tên thuộc tính (mã code) | Bắt buộc | Mô tả | Ví dụ |
|---|---|:---:|---|---|
| **Nguồn tham chiếu** | `module` | ✅ **Bắt buộc** | Chỉ định nguồn lấy dữ liệu. Nếu chỉ định **Node Name** thì lấy bằng `getModuleResult` (chế độ kết quả module). Nếu chỉ định theo dạng `<%変数名%>` thì lấy giá trị của biến đã có sẵn bằng `getObject` (chế độ tham chiếu biến). Nếu chưa thiết lập thì trả về `NO_RESULT`. | `stt_name`, `dtmf_birthday`, `<%customer_name%>` |
| **Tên biến** | `variable` | ⚪ Tùy chọn | Tên biến đích để lưu. Nếu chưa thiết lập thì bỏ qua việc lưu vào biến, chỉ thực thi `setResult`. | `customer_name`, `birth_date` |
| **Tên context** | `contextName` | ⚪ Tùy chọn | Tên trường context khi lưu vào DB. Việc lưu DB chỉ được thực thi khi **cả hai** `contextName` và `contextDisplayType` đều được thiết lập. | `patientName`, `phoneNumber` |
| **Định dạng context** | `contextDisplayType` | ⚪ Tùy chọn | Kiểu hiển thị trên DB. Việc lưu DB chỉ được thực thi khi **cả hai** `contextName` và `contextDisplayType` đều được thiết lập. | `Text`, `PHONE_NUMBER`, `Date` |

> 📌 **Điều kiện xác định chế độ tham chiếu biến:** Chỉ khi giá trị của `module` **hoàn toàn** ở dạng `<%...%>` (ví dụ: `<%customer_name%>`) thì mới chuyển sang chế độ tham chiếu biến. Nếu có lẫn các ký tự khác ở đầu hoặc cuối (ví dụ: `<%a%>b`) thì được xử lý như chế độ kết quả module.

### 3.2. Cách sử dụng kết quả đã lưu

Sau khi Module Result Binder thực thi, có thể sử dụng kết quả theo các cách sau.

**Cách 1: Sử dụng như biến (trong trường hợp đã thiết lập `variable`)**
Có thể sử dụng trong prompt, guidance, thuộc tính, v.v. của các module sau:
```
こんにちは、<%customer_name%> 様
```

**Cách 2: Phân nhánh luồng bằng setResult**
Phân nhánh luồng tùy theo giá trị:
- `result = "NO_RESULT"` → sang nhánh "hỏi lại"
- `result = "time_out"` → sang nhánh "thử lại"
- Giá trị bình thường → sang nhánh "xác nhận"

### 3.3. Ví dụ sử dụng

#### Kịch bản 1: Lưu tên khách hàng thành biến (không lưu DB)

Lấy tên khách hàng từ module STT và tái sử dụng ở nhiều nơi.

| Bước | Module | Thiết lập thuộc tính |
|---|---|---|
| 1 | STT (Node Name = `stt_name`) | *(lấy tên khách hàng từ giọng nói)* |
| 2 | Module Result Binder | `module = stt_name`<br>`variable = customer_name` |
| 3 | Phát âm thanh | `prompt = <%customer_name%> 様、ありがとうございます` |
| 4 | Phát âm thanh (cuối luồng) | `prompt = <%customer_name%> 様、またお電話お待ちしております` |

#### Kịch bản 2: Lưu tên khách hàng vào cả biến và DB

Lấy tên khách hàng từ module STT, vừa lưu thành biến để tham chiếu ở xử lý sau, vừa ghi vào DB dưới dạng thông tin bệnh nhân.

| Bước | Module | Thiết lập thuộc tính |
|---|---|---|
| 1 | STT (Node Name = `stt_name`) | *(lấy tên khách hàng từ giọng nói)* |
| 2 | Module Result Binder | `module = stt_name`<br>`variable = customer_name`<br>`contextName = patientName`<br>`contextDisplayType = Text` |
| 3 | Phát âm thanh | `prompt = <%customer_name%> 様、ご確認ありがとうございます` |

**Kết quả:**
- Có thể tham chiếu bằng biến `<%customer_name%>`
- Lưu vào trường `patientName` của DB (displayType: Text)

#### Kịch bản 3: Lấy giá trị của biến đã có sẵn và lưu vào DB (chế độ tham chiếu biến)

Dùng Module Result Binder để lấy ra giá trị đã được lưu vào biến (object) ở module trước, rồi lưu vào DB. Hoặc sao chép sang một biến tên khác.

| Bước | Module | Thiết lập thuộc tính |
|---|---|---|
| 1 | *(đã lưu `customer_name` ở xử lý trước)* | — |
| 2 | Module Result Binder | `module = <%customer_name%>`<br>`contextName = patientName`<br>`contextDisplayType = Text` |

**Kết quả:**
- Lấy giá trị bằng `getObject("customer_name")`
- Lưu vào trường `patientName` của DB (displayType: Text)
- Khi lưu thành công, cũng có thể tham chiếu bằng `<%patientName%>`

### 3.4. Các lưu ý quan trọng

> ⚠️ **`module` có 2 chế độ** — Chỉ định Node Name thì lấy bằng `getModuleResult`, chỉ định `<%変数名%>` thì lấy bằng `getObject`.
>
> ⚠️ **Kết quả được `.trim()`** — Khoảng trắng đầu/cuối được tự động loại bỏ (việc xác định `time_out`/`error` cũng thực hiện trên giá trị sau khi trim).
>
> ⚠️ **Khuyến nghị dùng snake_case cho tên biến** (ví dụ: `customer_name`, `birth_date`). Việc thống nhất trong toàn bộ luồng giúp tránh nhầm lẫn.
>
> ⚠️ **Khi nguồn lấy dữ liệu không tồn tại/rỗng** — Nếu `getModuleResult` hoặc `getObject` trả về null/rỗng, kết quả sẽ là `NO_RESULT`.
>
> ⚠️ **`time_out` và `error` được truyền qua nguyên trạng** — Không được lưu vào biến, cũng không được lưu vào DB. Các trường hợp này cần được xử lý ở nhánh luồng khác.
>
> ⚠️ **Việc lưu DB cần cả `contextName` và `contextDisplayType`** — Nếu chỉ thiết lập một trong hai thì việc lưu DB sẽ bị bỏ qua.
>
> ⚠️ **Việc lưu DB cần có kết nối IVR** — Nếu `$ivr.connected()` là false thì việc lưu DB sẽ bị bỏ qua (việc lưu biến và `setResult` vẫn được thực thi).
>
> ⚠️ **Tự động thiết lập biến khi lưu DB** — Khi lưu DB thành công, một biến có cùng tên với `contextName` sẽ được tự động thiết lập (ví dụ: nếu `contextName = patientName` thì cũng có thể tham chiếu bằng `<%patientName%>`).
>
> ⚠️ **Việc lưu DB không được thực thi trong trường hợp `time_out` / `error` / kết quả rỗng** — Chỉ có kết quả bình thường mới được lưu vào DB.

---

## 4. 📊 Các mẫu sử dụng thường gặp

| Trường hợp sử dụng | Cách thiết lập |
|---|---|
| Chỉ ghi kết quả của module khác vào log | `module = xxx`, không thiết lập `variable` |
| Lưu tên khách hàng, dùng để đọc lên sau này | `module = stt_name`, `variable = customer_name` |
| Lưu số điện thoại đã chuẩn hóa | `module = phone_norm`, `variable = phone_number` |
| Lưu ngày hẹn đã được phân tích (parse) | `module = date_classifier`, `variable = appointment_date` |
| Lưu tên khách hàng vào cả biến và DB | `module = stt_name`, `variable = customer_name`, `contextName = patientName`, `contextDisplayType = Text` |
| Chỉ lưu số điện thoại vào DB | `module = phone_norm`, `contextName = phoneNumber`, `contextDisplayType = PHONE_NUMBER` |
| Lấy ra giá trị của biến đã có sẵn để lưu DB / sao chép sang tên khác | `module = <%customer_name%>`, `contextName = patientName`, `contextDisplayType = Text` (chế độ tham chiếu biến) |
