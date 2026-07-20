# 🎂 DOB Re-confirmation

> 📄 Bản dịch tiếng Việt. Bản gốc tiếng Nhật: [SRS_DOB_Re-confirmation.md](SRS_DOB_Re-confirmation.md)

## 1. 🎯 Tổng quan (giải thích đơn giản)

**DOB Re-confirmation** là module xử lý **ngày sinh (Date of Birth)** của bệnh nhân. Từ ngày sinh được nhập qua STT hoặc DTMF, module phân tích chính xác **chỉ bằng phương pháp phân tích cục bộ dựa trên code (code-based)** từ nhiều dạng biểu diễn khác nhau như **lịch Nhật (和暦), Dương lịch (西暦), số Hán tự (漢数字), số toàn hình (全角数字), nhận dạng sai niên hiệu (元号), và các lỗi nghe nhầm đặc thù của STT**, sau đó phát lại để xác nhận và lưu vào cơ sở dữ liệu.

> ⚠️ Module này **không gọi LLM bên ngoài (OpenAI)**. Toàn bộ việc phân tích được hoàn tất bằng bộ chuẩn hóa (normalize) + bộ phân tích (parser) cục bộ. Những phát ngôn không thể xác định được ở cục bộ sẽ được xử lý là `INVALID`.

### 🧠 Logic phân tích

```
┌─────────────────────────────────────────────────┐
│  患者が生年月日を発話 / DTMF 入力                │
└─────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│  前処理: 数字正規化 + 各種誤認識正規化            │
│  - 全角数字(１２３) → 半角(123)                  │
│  - 漢数字(三十二) → 数字(32)                     │
│  - 元号エイリアス(「唱和」→「昭和」など)          │
│  - 「じゅう」系誤認識 → 数字 (Rule 0-5)           │
│  - 数字間の no/NO → の (Rule 0-6)                │
│  - 野 → の (じゅう系/数字の直前のみ)             │
│  - 月日年 → 年月日 並び替え (Rule 0-7)           │
│  - 円 → 年 誤認識補正 (Rule 0-8)                 │
│  - 先頭ノイズ除去 (Rule 0-9)                     │
│  - 月日連結 年MMDD → 年MM月DD日 (Rule B3)        │
└─────────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────────┐
│  ローカルパーサー(コードベース解析)             │
│  - DTMF 8桁 (YYYYMMDD)                          │
│  - 和暦パターン (昭和54年3月12日)                │
│  - 西暦パターン (1979年3月12日)                  │
│  - 元号年範囲チェック                            │
│  - 妥当性チェック(実在日・120歳超・未来日)       │
└─────────────────────────────────────────────────┘
             ↓
     status = OK ── YES ──→ 結果を使用
             ↓ INVALID / UNCERTAIN
   (この単体解析が失敗しても即 INVALID とは限らず、
    フォールバックチェーンで nodeValue/cache/部分マージへ進む。
    最終的にすべて失敗した場合のみ INVALID。詳細は 3.3 / 4章参照)
             ↓ (status=OK の場合のみ)
┌─────────────────────────────────────────────────┐
│  フォーマット & DB 保存 & 再生 & キャッシュ保存   │
│  - 和暦 or 西暦で読み上げ                         │
│  - patientDateOfBirth に保存                     │
│  - 会話ログ(utterance)を保存                     │
│  - raw_dob_data に再入用キャッシュを保存          │
└─────────────────────────────────────────────────┘
```

> 💡 **Ví dụ thực tế:**
> - Phát ngôn của bệnh nhân: *「昭和54年3月12日」* → phân tích → `1979-03-12 00:00` → phát lại *「昭和54年3月12日でよろしいですか?」*
> - Phát ngôn của bệnh nhân: *「唱和ごじゅうよねん さんがつ じゅうににち」* → chuẩn hóa alias → chuyển đổi số Hán tự/じゅう → *「昭和54年3月12日」* → phân tích OK
> - Nhập DTMF: `19790312` → xác định trực tiếp thành `1979-03-12 00:00` (không cần STT/LLM)
> - Ở bước xác nhận, phát ngôn *「わかりません」* → đọc lại giá trị đã xác định lần trước từ cache

---

## 2. 📋 Đặc tả (đơn giản)

| Mục | Nội dung |
|---|---|
| **Tên module** | DOB Re-confirmation |
| **Chức năng** | Phân tích cục bộ các dạng biểu diễn đa dạng của ngày sinh, phát lại để xác nhận và lưu vào DB |
| **Đầu vào** | Kết quả của STT/DTMF (nodeValue) + văn bản phát ngôn gốc (rawText) |
| **Đầu ra (setResult)** | Giá trị đọc lên, hoặc `INVALID` |
| **Tác dụng phụ (side effect)** | Phát âm thanh, lưu `patientDateOfBirth` vào DB, lưu log utterance, lưu cache `raw_dob_data` |
| **Phụ thuộc bên ngoài** | Không (không thực hiện gọi LLM/HTTP) |

### 📑 Các mẫu đầu vào được hỗ trợ

| Mẫu | Ví dụ đầu vào | Kết quả phân tích |
|---|---|---|
| DTMF 8 chữ số | `19790312` | `1979-03-12 00:00` |
| Lịch Nhật (chuẩn) | `昭和54年3月12日` | `1979-03-12 00:00` |
| Lịch Nhật (năm nguyên/元年) | `令和元年5月1日` | `2019-05-01 00:00` |
| Lịch Nhật (dấu phân cách đa dạng) | `昭和58の3月の12日` / `昭和58 3月 12日` / `昭和58年、3月、12日` | `1983-03-12 00:00` |
| Dương lịch (có năm) | `1979年3月12日` | `1979-03-12 00:00` |
| Dương lịch (năm 2 chữ số) ⚠️ | `79年3月12日` | `INVALID` (năm dưới 4 chữ số và không có niên hiệu thì không thể xác định thuộc niên đại nào như Chiêu Hòa/Bình Thành v.v. nên phải hỏi lại. Chi tiết xem phần sau) |
| Dương lịch (năm 3 chữ số) | `079年3月12日` | `1979-03-12 00:00` (bổ sung thập niên 1900 dựa vào 2 chữ số cuối. Được duy trì như biện pháp cứu vãn khi STT làm rơi chữ số đầu) |
| Số toàn hình (全角) | `１９７９年３月１２日` | `1979-03-12 00:00` |
| Số Hán tự | `千九百七十九年三月十二日` | `1979-03-12 00:00` |
| Alias nhận dạng sai | `唱和54年3月12日`、`今日は54年...` | Diễn giải là 「昭和」 |
| Nhận dạng sai じゅう | `昭和じゅうよ年...` (= năm 14) | Sửa じゅう → thành số |
| Thứ tự sắp xếp | `3月12日昭和54年` | Sắp xếp lại thành `昭和54年3月12日` |
| Nhận dạng sai 円→年 | `1947円7月10日` | Diễn giải là `1947年7月10日` → `1947-07-10 00:00` |
| Trợ từ, ngập ngừng (の/です) | `平成12年の5月12日です。` | `2000-05-12 00:00` |
| Nối liền tháng-ngày (MMDD) | `1952年0203` / `昭和61年0203` | `1952-02-03 00:00` / `1986-02-03 00:00` |
| Loại bỏ nhiễu ở đầu | `1909、66年10月17日` | Loại bỏ `1909、` ở đầu → phân tích `66年10月17日` → do là năm 2 chữ số không niên hiệu nên `INVALID` |

### 🏛️ Các niên hiệu được hỗ trợ

| Niên hiệu | Ngày bắt đầu | Quy đổi Dương lịch | Phạm vi năm niên hiệu hợp lệ |
|---|---|---|---|
| Lệnh Hòa (令和) | 2019/05/01 | `2018 + năm niên hiệu` | 1〜(năm hiện tại − 2018) |
| Bình Thành (平成) | 1989/01/08 | `1988 + năm niên hiệu` | 1〜31 |
| Chiêu Hòa (昭和) | 1926/12/25 | `1925 + năm niên hiệu` | 1〜64 |
| Đại Chính (大正) | 1912/07/30 | `1911 + năm niên hiệu` | 1〜15 |
| Minh Trị (明治) | 1868/01/25 | `1867 + năm niên hiệu` | 1〜45 |

> 📌 Nếu năm niên hiệu nằm ngoài phạm vi ở bảng trên (ví dụ: Chiêu Hòa năm 70) thì là `INVALID`.

> 📌 **Ngày trước ngày bắt đầu Minh Trị (1868/01/25):** Hàm đọc theo lịch Nhật (`toWareki`) trả về chuỗi **`"明治以前"`** (nghĩa là "trước Minh Trị") đối với ngày cũ không rơi vào ngày bắt đầu của bất kỳ niên hiệu nào trong 5 niên hiệu trên. Trong vận hành thực tế trường hợp này hầu như không xảy ra vì thường đã bị `INVALID` trước đó bởi kiểm tra tính hợp lệ (kiểm tra vượt 120 tuổi v.v.), nhưng về mặt đặc tả của việc chuyển đổi lịch Nhật thì thiết kế là trả về "明治以前".

> ⚠️⚠️ **【Thiết kế an toàn】Không tự động bổ sung cho năm 1〜2 chữ số không có niên hiệu (phòng chống nhầm lẫn bệnh nhân):**
> Với đầu vào qua rawText/STT, năm gồm 1〜2 chữ số mà không kèm niên hiệu và cũng không phải Dương lịch 4 chữ số
> (ví dụ: `57年`), phía code hoàn toàn không thể phân biệt được đó là `1957年` hay `昭和57年 (1982年)`, hay là một niên hiệu khác.
> Nếu bổ sung một cách máy móc bằng `1900 + năm`, sẽ
> **dẫn đến sự cố nghiêm trọng là nhầm lẫn ngày sinh của bệnh nhân**, do đó trường hợp này luôn được xác định là `INVALID`
> và hệ thống sẽ hỏi lại (yêu cầu người dùng xác nhận lại). Còn năm 3 chữ số (`079年` v.v.)
> là mẫu nhận dạng sai rõ ràng thuộc dạng "Dương lịch 4 chữ số bị STT làm rơi chữ số đầu", nên
> vẫn được cứu vãn như trước theo `1900 + 2 chữ số cuối` (căn cứ để phân biệt là "số lượng chữ số", không phải độ lớn nhỏ của giá trị).
>
> Ngoài ra, quy tắc an toàn này **chỉ áp dụng cho luồng phân tích rawText/STT (Priority A / A2, `parseDateByCode` /
> `parsePartialDate`)**. Đối với `nodeValue` (Priority B) qua DTMF (nhập nút trên điện thoại), vì về nguyên lý
> không có phương tiện nào để truyền thông tin niên hiệu, nên vẫn bổ sung năm 2/3 chữ số thành thập niên 1900 như trước (chi tiết xem mục 3.4).

### 🗣️ Hỗ trợ alias nhận dạng sai niên hiệu

Những cách biểu đạt mà STT dễ nhận dạng sai cũng được tự động chuyển đổi về đúng niên hiệu.

| Niên hiệu đúng | Các mẫu nhận dạng sai tương ứng |
|---|---|
| **昭和 (Chiêu Hòa)** | しょうわ、ショウワ、唱和、社長は、少和、名所、正和、うわー、うわ、今日は |
| **平成 (Bình Thành)** | へいせい、ヘイセイ、平静、閉成、平清 |
| **令和 (Lệnh Hòa)** | れいわ、レイワ、例は、冷和、例話 |
| **大正 (Đại Chính)** | たいしょう、タイショウ、対象、大将、大賞、大勝、対照 |
| **明治 (Minh Trị)** | めいじ、メイジ、命じ、銘じ、明示 |

### 🔧 Chuẩn hóa nhận dạng sai số/trợ từ (quy tắc hiệu chỉnh STT)

| Quy tắc | Nội dung | Ví dụ |
|---|---|---|
| **Toàn hình→Nửa hình** | Chuyển `０〜９` thành `0〜9` | `１９７９` → `1979` |
| **Số Hán tự→Số** | Chuyển đổi số Hán tự có xử lý hàng chục | `三十二` → `32`、`五` → `5` |
| **Rule 0-5 (hiệu chỉnh じゅう)** | Chuyển nhận dạng sai dạng 「じゅう」 trong ngữ cảnh tháng-ngày thành số. Có 1 chữ số theo sau → nối thành 2 chữ số, không có → 10. Xử lý trước từ ghép 「重要」→14. Cũng hiệu chỉnh `10号`→15 / `20号`→25 | `じゅうに` → `12` |
| **Rule 0-6 (no→の)** | Chỉ chuyển thành 「の」 với dạng **số + no/No/NO(.?) + số** (cấm chuyển đổi no ở các trường hợp khác) | `58 No 3` → `58の3` |
| **Hiệu chỉnh 野→の** | Chỉ chuyển `野` → `の` khi đứng ngay trước dạng じゅう hoặc số (phòng chống chuyển đổi quá mức) | `野重さん` → `の重さん` |
| **Rule 0-7 (hiệu chỉnh thứ tự)** | Chỉ sắp xếp lại 月日年 → 年月日 khi có năm (hỗ trợ cả Dương lịch lẫn lịch Nhật) | `3月12日昭和54年` → `昭和54年3月12日` |
| **Rule 0-8 (hiệu chỉnh 円→年)** | Hiệu chỉnh trường hợp STT nhận dạng sai 「年」 thành 「円」 (an toàn vô điều kiện vì trong module này không xuất hiện biểu thức tiền tệ) | `1947円7月10日` → `1947年7月10日` |
| **Rule 0-9 (loại bỏ nhiễu ở đầu)** | Khi có số vô quan kèm dấu chấm câu/dấu phẩy lẫn vào trước ngày tháng thực sự, chỉ loại bỏ rồi phân tích khi ngay sau đó là 「số+年」 hoặc tên niên hiệu (nếu nhiễu ở đầu nối tiếp nhiều lần thì loại bỏ lặp lại) | `1909、66年10月17日` → phân tích thành `66年10月17日` |
| **Rule B3 (hiệu chỉnh nối liền tháng-ngày)** | Khi ngay sau 「年」 là 4 chữ số liền không có dấu phân cách, tách thành `MMDD` thành `MM月DD日` (không áp dụng nếu phía sau còn có số/tháng/ngày). ※Tên hàm trong code là `normalizeConcatenatedMMDD`, mã định danh quy tắc là **Rule B3** (trong pipeline `normalizeAll`) | `1952年0203` → `1952年02月03日` |

### ✅ Kiểm tra tính hợp lệ

| Mục kiểm tra | Nội dung |
|---|---|
| **Kiểm tra ngày tồn tại thực** | Ngày không tồn tại thực như 30/2, tháng 13 v.v. là INVALID (có xét cả năm nhuận) |
| **Kiểm tra phạm vi năm niên hiệu** | Ngoài phạm vi năm hợp lệ của từng niên hiệu là INVALID (xem bảng trên) |
| **Kiểm tra vượt quá 120 tuổi** | Năm hiện tại − năm sinh > 120 là INVALID (năm dưới 4 chữ số cũng bị xử lý là INVALID) |
| **Kiểm tra ngày tương lai** | Ngày sau hôm nay là INVALID |

### 📤 Giá trị trả về của setResult

| Giá trị | Ý nghĩa |
|---|---|
| *(giá trị đọc lên)* | Giá trị cuối cùng khi phân tích thành công (ví dụ: `昭和54年3月12日` hoặc `1979年3月12日`) |
| `RAW_INPUT:...` | Log trung gian ghi raw_text ngay đầu quá trình xử lý (luôn được thiết lập đầu tiên) |
| `LOCAL_RESULT:...` | Log trung gian khi phân tích nodeValue (nhánh **Priority B** trong code, đầu vào mới) và khi merge ngày một phần (`tryPartialMergeAndSave`, **Priority A2 / B2**) (cuối cùng bị ghi đè bằng giá trị đọc lên) |
| `INVALID` | Không thể diễn giải thành ngày tháng, không đạt kiểm tra tính hợp lệ, hoặc không có đầu vào |

> 📌 `LLM_RESULT` / `TIMEOUT` / `ERROR` **không được sử dụng trong phiên bản này** (do đã bỏ cơ chế fallback sang LLM).

---

## 3. 🛠️ Cách sử dụng (chi tiết)

### 3.1. Thiết lập thuộc tính (property)

| Tên thuộc tính (tiếng Nhật) | Tên thuộc tính (code) | Bắt buộc | Mặc định | Mô tả |
|---|---|:---:|---|---|
| **Hướng dẫn (ガイダンス)** | `prompt` | ✅ Bắt buộc | *(trống)* | Hướng dẫn để xác nhận. `#data#` được thay bằng giá trị đọc lên. |
| **Tên module nguồn tham chiếu** | `module` | ✅ Bắt buộc | *(trống)* | Tên module STT/DTMF nguồn tham chiếu |
| **Chế độ đọc năm sinh** | `dateReadingMode` | ⚪ Tùy chọn | *(chưa thiết lập = tự động)* | `和暦` = đọc theo lịch Nhật, `西暦` = đọc theo Dương lịch, chưa thiết lập/khác = đọc theo đầu vào (đọc lịch Nhật khi phát hiện niên hiệu, còn lại đọc Dương lịch) |
| **Lưu context** | `saveDOB2db` | ⚪ Tùy chọn | `no` | `yes` = lưu vào DB dưới dạng `patientDateOfBirth`, `no` = không lưu vào DB |

> 📌 Các mục `.openAI_generate.url` / `.office_id` có trong đặc tả cũ **không cần thiết trong phiên bản này** (do không thực hiện gọi LLM).

### 3.2. Nguồn dữ liệu đầu vào (2 hệ thống)

Module này tham chiếu **2 loại đầu vào**:

| Nguồn đầu vào | Nơi lấy | Công dụng |
|---|---|---|
| **nodeValue** | `$runner.getModuleResult(module)` → chỉnh thành `baseDate` bằng `normalizeInput` | Ngày đã được STT định dạng (ví dụ: `1979-03-12 00:00`) hoặc DTMF 8 chữ số |
| **rawText** | `$runner.getObject("raw_text")` → `$runner.get("raw_text")` → `$runner.get("GLOBAL_RAW_TEXT")` | Văn bản phát ngôn gốc (ví dụ: `昭和54年3月12日`) |

> 📌 **Vai trò của rawText:** Ngay cả khi STT trả về ngày đã được định dạng, việc xem phát ngôn gốc vẫn giúp xác định **thông tin niên hiệu** và **lỗi nhận dạng sai của STT**.
>
> 📌 **Phát ngôn DTMF / không phải ngày tháng:** rawText không giống ngày tháng và baseDate hợp lệ →采用 trực tiếp nodeValue (không cần STT/LLM).

### 3.3. Nhánh quyết định của luồng xử lý (thiết kế thứ tự ưu tiên)

Trên tiền đề luồng hội thoại (TTS → STT/DTMF → module này → xác nhận có/không → tùy trường hợp quay lại module này), module diễn giải đầu vào theo thứ tự ưu tiên sau.

> 📌 **Nhãn thứ tự ưu tiên tuân theo tên nhánh trong code.** Trong code, thứ tự từ trên xuống được cài đặt thành chuỗi fallback 6 tầng: `Priority A` → `Priority A2` → `Priority B` → `Priority B2` → `Priority C` → `INVALID` (lưu ý `Priority B` xử lý `nodeValue` được thực hiện **trước** `Priority C` xử lý re-entry `cache`).

```
入力: nodeValue(→baseDate) + rawText + キャッシュ(raw_dob_data)
        │
        ▼
【A】rawText が完全な日付?  ── YES ──→ rawText を最優先で解析(handleRawTextFlow)
        │  (解析OK: cache と一致・不一致に関わらず rawText を採用)
        │  (解析NG: INVALID にせず【A2】へフォールバック)
        ▼
【A2】rawText が部分日付(年のみ/月のみ/日のみ/月日)+ キャッシュあり?
        │  ── YES ──→ キャッシュ済み確定日付に変更部分のみ上書きしてマージ(tryPartialMergeAndSave)
        │             (マージ結果が実在しない日付なら INVALID で確定・フォールバックしない)
        ▼
【B】baseDate(nodeValue)が有効?  ── YES ──→ nodeValue を処理(主に DTMF/元号なし STT)
        │  NO                                  ├─ 妥当性NG    → INVALID にせず【B2】へフォールバック
        │                                      ├─ 再入(baseDate===sourceBaseDate) → キャッシュの読み上げを保持
        │                                      └─ 新規入力    → 西暦で読み上げ(2/3桁年は 1900 年代補完)
        ▼
【B2】nodeValue が部分日付 + キャッシュあり?  ── YES ──→ 【A2】同様にマージ(STT が部分テキストを返した場合の保険)
        │
        ▼
【C】再入(cached かつ baseDate が前回と同一)?  ── YES ──→ キャッシュ値を復唱(resolveAndSave)
        │  NO                                                (確認段階で parse 不能発話があり復唱に戻ったケース)
        ▼
【D】それ以外 → INVALID
```

> 📌 **Lý do ưu tiên 【A】:** Khi người dùng phát ngôn ngày mới, nó chắc chắn nằm trong rawText, nên tin cậy rawText hơn là cache hay nodeValue đã cũ.
>
> 📌 **Lý do xử lý 【B】(nodeValue) trước 【C】(cache):** Để lấy **đầu vào mới nhất** của STT/DTMF, nodeValue được ưu tiên hơn cache (`sourceBaseDate`). Tuy nhiên chỉ khi nodeValue trùng với `sourceBaseDate` (= đọc lại cùng một ngày) thì mới giữ lại giá trị đọc lên của cache (niên hiệu v.v.) (xem chú thích trong code).
>
> 📌 **Lý do ưu tiên hiệu chỉnh một phần hơn nodeValue đã cũ (【A2】):** Phát ngôn của người dùng sau khi nói "không" để sửa lại một phần như "chỉ năm", "chỉ tháng" sẽ xuất hiện trong rawText, nên được merge trước nodeValue cũ (【B】).

### 3.4. Logic phán đoán đặc biệt

#### 🔍 Phán đoán rawText có giống ngày tháng không (looksLikeDateUtterance)
Nếu rawText sau khi chuẩn hóa thỏa mãn một trong các điều kiện sau thì được phán đoán là "giống ngày tháng" và đi vào Priority A:
- Chứa từ khóa niên hiệu (明治/大正/昭和/平成/令和)
- Chứa số + marker 年/月/日
- Chứa chuỗi số 6〜8 chữ số (kiểu DTMF)
- Định dạng ISO `yyyy-MM-dd` hoặc `yyyy-MM-dd HH:mm`

#### 🔍 Phán đoán quay lại (re-entry) và cache (raw_dob_data)
Khi xác định, lưu `{ dbValue, readingValue, sourceBaseDate(= baseDate lúc xác định) }` vào `raw_dob_data`. Ở lần khởi động tiếp theo, nếu baseDate giống với giá trị đã lưu lần trước thì coi là "quay lại (tình huống nên đọc lại cùng một DOB)" và phát lại giá trị cache (Priority C. Tuy nhiên nếu nodeValue hợp lệ và cùng ngày thì giá trị đọc của cache đã được giữ lại sớm hơn tại nhánh re-entry của Priority B).

Ví dụ: Ở bước xác nhận, phát ngôn 「わかりません」 → rawText không phải ngày tháng + baseDate không đổi → đọc lại `昭和58年4月25日` của lần trước từ cache.

#### 🔍 Merge ngày một phần (partial date merge / Priority A2・B2)
Đây là cơ chế xử lý phát ngôn khi người dùng sau khi nói "không" chỉ sửa lại **một phần** (chỉ năm・chỉ tháng・chỉ ngày・tháng-ngày v.v.). Chỉ ghi đè thành phần được sửa lên ngày đã xác định trong cache, các thành phần còn lại lấy từ giá trị cache để merge.

- **`parsePartialDate(rawText)`**: Trích xuất đầu vào **chỉ một phần có kèm marker (年・月・日)** của năm/tháng/ngày. Vì bắt buộc có marker nên chỉ số không của DTMF (mơ hồ) không thuộc phạm vi. Năm hỗ trợ dạng có niên hiệu / Dương lịch (2〜4 chữ số) (2 chữ số → coi là không hợp lệ = none, 3 chữ số → 1900+(yyy%100), 4 chữ số → giữ nguyên). Nếu năm niên hiệu・tháng・ngày ngoài phạm vi thì trả về `none`. Giá trị trả về là `{ has, year, month, day, eraDetected }`.
- **`mergePartialWithCache(partial, cacheDbValue)`**: Chỉ ghi đè thành phần được chỉ định trong partial, các thành phần còn lại lấy từ cache. Nếu là ngày không tồn tại thực (ví dụ: 31/1 + 「tháng 2」 → 31/2)・ngày tương lai・vượt 120 tuổi thì trả về `null`.
- **`tryPartialMergeAndSave(sourceText, label)`**: Entry để thực thi các hàm trên. **Nếu không có cache・không phải ngày một phần・hoặc năm-tháng-ngày đã đủ hoàn chỉnh (= là ngày hoàn chỉnh nên để phân tích thông thường xử lý) thì bỏ qua và trả về `false`(fallback sang tầng sau)**. Nếu merge thành công thì `setResult("LOCAL_RESULT:...")` → `resolveAndSave` để xác định. Nếu kết quả merge là ngày không tồn tại thực thì **`setResult("INVALID")` để xác định (không fallback)**.

Vị trí áp dụng:
- **Priority A2**: rawText là ngày một phần + có cache (`tryPartialMergeAndSave(rawText, "Priority A2")`). Ưu tiên hơn nodeValue đã cũ (Priority B).
- **Priority B2**: nodeValue là ngày một phần + có cache (`tryPartialMergeAndSave(nodeValue, "Priority B2")`). Thông thường nodeValue được chuẩn hóa thành ngày hoàn chỉnh nên hiếm khi kích hoạt, nhưng là biện pháp dự phòng khi STT trả về văn bản một phần.

Ví dụ: Lần trước đã xác định `1983-03-12` (昭和58年3月12日) → "không" → chỉ phát ngôn 「4月」 → chỉ ghi đè tháng → merge thành `1983-04-12`.

#### 🔍 Kiểm tra tính đầy đủ của các thành phần ngày tháng
Nếu **cả 3 thành phần** năm・tháng・ngày không đủ thì phân tích cục bộ sẽ không thành `OK`. Chỉ cần thiếu 1 thành phần → `UNCERTAIN` (→ trong phiên bản này được xác định là `INVALID`).

Ví dụ: `昭和54年3月` → thiếu ngày → UNCERTAIN → INVALID

#### 🔍 Chi tiết nhánh nodeValue (Priority B)
Khi `baseDate` (nodeValue) hợp lệ, việc xử lý (nhánh `Priority B` trong code) không phải là "OK→xác định / NG→INVALID" đơn giản, mà phân thành 3 trường hợp sau:

1. **Không đạt tính hợp lệ** (ngày không tồn tại thực・ngày tương lai・vượt 120 tuổi) → **không** thành `INVALID` mà **fallback sang cache** (xử lý ở Priority B2 / C phía sau).
2. **Quay lại** (`baseDate === sourceBaseDate` = đọc lại cùng một ngày) → vì bản thân ngày trùng với nodeValue nên **giữ lại giá trị đọc lên của cache** (niên hiệu v.v.) để xác định (`resolveAndSave(cache.dbValue, cache.readingValue)`).
3. **Đầu vào mới** → trên tiền đề rawText không có thông tin niên hiệu nên **đọc theo Dương lịch**. `setResult("LOCAL_RESULT:...")` → `resolveAndSave` để xác định.

**Tự động bổ sung năm 2/3 chữ số (chỉ Priority B):** Chỉ ở Priority B này (采用 nodeValue, chủ yếu là DTMF), năm 2〜3 chữ số mới được bổ sung thành thập niên 1900. Vì DTMF chỉ nhập bằng nút và không thể truyền niên hiệu, nên chỉ duy trì việc bổ sung như cũ ở luồng này.
- 2 chữ số: `79` → `1979`
- 3 chữ số: `079` → `1979` (dùng 2 chữ số cuối)

> ⚠️ Đây là hành vi chỉ dành riêng cho Priority B (nodeValue/DTMF). Ở phía Priority A (rawText/STT),
> năm 1〜2 chữ số không có niên hiệu sẽ thành `INVALID` theo 【Thiết kế an toàn】nêu trên, và không thực hiện tự động bổ sung này.

### 3.5. Ví dụ sử dụng

#### 🎬 Kịch bản 1: Nhập lịch Nhật chuẩn (phân tích cục bộ・Priority A)

| Thuộc tính | Giá trị |
|---|---|
| `prompt` | `生年月日は #data# でよろしいですか?` |
| `module` | `stt_dob` |
| `dateReadingMode` | *(chưa thiết lập = tự động)* |
| `saveDOB2db` | `yes` |

**Thực thi:**
- Phát ngôn của bệnh nhân: 「昭和54年3月12日」
- rawText = `昭和54年3月12日` → looksLikeDate = true → Priority A
- Phân tích code: status = OK, phát hiện niên hiệu = true → `1979-03-12 00:00`
- Do là chế độ tự động, phát hiện niên hiệu → đọc theo lịch Nhật
- Phát lại: *「生年月日は 昭和54年3月12日 でよろしいですか?」*
- Lưu DB: `patientDateOfBirth = 1979-03-12 00:00`

#### 🎬 Kịch bản 2: Nhập DTMF 8 chữ số (Priority B)

| Thuộc tính | Giá trị |
|---|---|
| `prompt` | `生年月日は #data# でよろしいですか?` |
| `module` | `dtmf_dob` |
| `dateReadingMode` | `西暦` |
| `saveDOB2db` | `yes` |

**Thực thi:**
- Đầu vào của bệnh nhân: `19790312`
- rawText = trống (ở chế độ DTMF, rawText không được tạo ra) → looksLikeDate = false
- nodeValue = `1979-03-12 00:00` (đã được định dạng bởi normalizeInput) → baseDate hợp lệ → Priority B (đầu vào mới)
- Phát lại: *「生年月日は 1979年3月12日 でよろしいですか?」*

#### 🎬 Kịch bản 3: Alias nhận dạng sai + số Hán tự (phân tích cục bộ・Priority A)

| Thuộc tính | Giá trị |
|---|---|
| `prompt` | `生年月日は #data# でよろしいですか?` |
| `module` | `stt_dob` |
| `dateReadingMode` | `和暦` |

**Thực thi:**
- Phát ngôn của bệnh nhân: 「唱和五十四年三月十二日」 (「昭和」 bị nhận dạng sai thành 「唱和」)
- Chuẩn hóa alias niên hiệu: `昭和五十四年三月十二日`
- Chuẩn hóa số Hán tự: `昭和54年3月12日`
- Phân tích code: status = OK → `1979-03-12 00:00`
- Phát lại: *「生年月日は 昭和54年3月12日 でよろしいですか?」*

#### 🎬 Kịch bản 4: Phát ngôn không thể parse ở bước xác nhận (quay lại)

**Tiền đề:** Lần trước đã xác định `昭和54年3月12日` (= `1979-03-12 00:00`) (đã lưu cache).

**Thực thi:**
- Đối với xác nhận, bệnh nhân phát ngôn không phải ngày tháng như 「うーん、どうだろう」
- rawText không giống ngày tháng (bỏ qua Priority A/A2)
- baseDate giống lần trước (`baseDate === sourceBaseDate`):
  - **Nếu nodeValue hợp lệ** → giữ lại giá trị đọc lên của cache để xác định tại **nhánh re-entry của Priority B**.
  - **Nếu nodeValue không hợp lệ / không lấy được** → đọc lại giá trị cache tại **Priority C (fallback cache)**.
- Cả hai trường hợp đều đọc lại `昭和54年3月12日` từ cache
- Phát lại: *「生年月日は 昭和54年3月12日 でよろしいですか?」*

#### 🎬 Kịch bản 5: Phát ngôn mơ hồ (không thể phân tích cục bộ)

**Thực thi:**
- Phát ngôn của bệnh nhân: 「54年の3月頃だったかな...12日かな」
- 3 thành phần không đủ rõ ràng / dấu phân cách không rõ → UNCERTAIN
- Trong phiên bản này không có fallback LLM → `INVALID`
- Không phát lại, không lưu DB

#### 🎬 Kịch bản 6: Không đạt kiểm tra tính hợp lệ

**Thực thi:**
- Phát ngôn của bệnh nhân: 「令和10年3月12日」
- 令和10年 = năm 2028 → không đạt kiểm tra ngày tương lai → INVALID
- setResult: `INVALID`
- Không phát lại, không lưu DB

### 3.6. Cơ chế lưu DB

Trong trường hợp `saveDOB2db = yes`, những thứ sau được lưu (trước khi lưu sẽ kiểm tra xem có đúng định dạng `yyyy-MM-dd HH:mm` hay không):

| Trường | Giá trị |
|---|---|
| `contextName` | `patientDateOfBirth` |
| `displayType` | `Date` |
| `value` | Ngày ở định dạng `yyyy-MM-dd HH:mm` (ví dụ: `1979-03-12 00:00`) |

Đồng thời, **log utterance** (log hội thoại) cũng được tự động lưu:

| Trường | Ý nghĩa |
|---|---|
| `seq` | Số thứ tự phát ngôn (tăng lên khi lưu thành công) |
| `messageType` | `0` (cố định) |
| `text` | Nội dung bên trong `{tts_g:...}`, hoặc văn bản đã loại bỏ `{}` từ prompt |
| `utteranceType` | `MESSAGE` |
| `startMsec` / `endMsec` | Thời điểm lưu (epoch mili giây) |

Thêm nữa, cache dùng cho phán đoán quay lại **`raw_dob_data`** cũng được lưu `{ dbValue, readingValue, sourceBaseDate }` (lưu bất kể thiết lập của `saveDOB2db`).

### 3.7. Lưu ý quan trọng

> ⚠️ **`prompt` cần có `#data#`** — placeholder này được thay bằng ngày đã phân tích.
>
> ⚠️ **rawText được lấy từ context biến** — thông thường module STT ở phía trước cần đã lưu vào biến `raw_text`.
>
> ⚠️ **Khi `dateReadingMode` chưa thiết lập thì là tự động** — đầu vào có phát hiện niên hiệu sẽ được đọc theo lịch Nhật, còn lại đọc theo Dương lịch.
>
> ⚠️ **Ở chế độ DTMF, rawText không được tạo ra** — vì vậy ở Priority B dùng trực tiếp baseDate (nodeValue). Năm 2/3 chữ số được tự động bổ sung thành thập niên 1900.
>
> ⚠️ **Kiểm tra phạm vi năm niên hiệu** — nếu ra ngoài năm hợp lệ của từng niên hiệu (ví dụ: Chiêu Hòa là 1〜64) thì INVALID.
>
> ⚠️ **Kiểm tra vượt quá 120 tuổi** — năm hiện tại − năm sinh > 120, hoặc năm dưới 4 chữ số thì tự động INVALID.
>
> ⚠️ **Kiểm tra ngày tương lai** — ngày sau hôm nay tự động INVALID (để phòng chống diễn giải sai năm niên hiệu).
>
> ⚠️ **Không có fallback LLM** — phát ngôn không thể xác định ở cục bộ (UNCERTAIN) được xử lý là `INVALID` (thống nhất với thiết lập Jump của module). Không thực hiện gọi HTTP/OpenAI bên ngoài.
>
> ⚠️ **Khi INVALID thì không lưu DB・không phát lại** — ngày không hợp lệ chỉ có `setResult("INVALID")`, không thực hiện lưu DB hay phát âm thanh.

---

## 4. 📊 Tổng quan luồng phán đoán

> 📌 Nhãn tuân theo tên nhánh trong code (`Priority A / A2 / B / B2 / C`). Chuỗi fallback theo thứ tự
> **rawText (hoàn chỉnh) → rawText (một phần) → nodeValue → nodeValue (một phần) → cache (re-entry) → INVALID**.
> `nodeValue` (【B】) được xử lý **trước** re-entry `cache` (【C】).

```
入力: nodeValue(→baseDate) + rawText + raw_dob_data キャッシュ
        │
        ▼  setResult("RAW_INPUT:...")  ← 冒頭で必ずログ
        │
┌────────────────────────────────────┐
│【A】rawText が日付らしい?           │
└────────────────────────────────────┘
        │ YES → 前処理(正規化) → コードベース解析(DTMF/和暦/西暦)
        │        ├─ status=OK        → 読み上げ値で確定 → resolveAndSave → _resolved=true
        │        └─ status=INVALID/UNCERTAIN → INVALID にせず _resolved=false のまま次段へ
        │ NO(または上記フォールバック)
        ▼
┌────────────────────────────────────┐
│【A2】rawText が部分日付 + cache?    │  tryPartialMergeAndSave(rawText,"Priority A2")
└────────────────────────────────────┘
        │ YES → キャッシュにマージ
        │        ├─ マージOK   → LOCAL_RESULT → resolveAndSave → _resolved=true
        │        └─ マージNG   → setResult("INVALID") で確定(_resolved=true)
        │ NO
        ▼
┌────────────────────────────────────┐
│【B】baseDate(nodeValue)有効?      │
└────────────────────────────────────┘
        │ YES → 2/3桁年補完 → 妥当性チェック
        │        ├─ 妥当性NG              → INVALID にせず【B2】へフォールバック
        │        ├─ 再入(baseDate===src) → キャッシュの読み上げを保持 → resolveAndSave
        │        └─ 新規入力              → 西暦で LOCAL_RESULT → resolveAndSave
        │ NO
        ▼
┌────────────────────────────────────┐
│【B2】nodeValue が部分日付 + cache?  │  tryPartialMergeAndSave(nodeValue,"Priority B2")
└────────────────────────────────────┘
        │ YES → 【A2】同様にマージ(マージNG は INVALID で確定)
        │ NO
        ▼
┌────────────────────────────────────┐
│【C】再入(cached & baseDate 同一)?  │
└────────────────────────────────────┘
        │ YES → キャッシュ値を復唱 → resolveAndSave
        │ NO
        ▼
┌────────────────────────────────────┐
│【D】INVALID                          │  setResult("INVALID")
└────────────────────────────────────┘

resolveAndSave:
  - setResult(読み上げ値)
  - 音声再生(prompt の #data# を置換)
  - raw_dob_data キャッシュ保存(sourceBaseDate = 確定時の baseDate)
  - (saveDOB2db=yes なら)patientDateOfBirth を DB 保存
  - utterance ログ保存
```
