# 📚 IVRモジュール技術ドキュメント

本ドキュメントは、IVRシステムで使用される **4つの独立したモジュール** について説明します。各モジュールはそれぞれ独立した機能を持ち、単体で使用されます。

---

## 🗂️ モジュール一覧

| # | モジュール名 | 主な機能 | 複雑度 |
|:-:|---|---|:-:|
| 1 | **Module Result Binder** | 他のモジュールの結果を取得し、変数として格納 + DB 保存(オプション) | ⭐ |
| 2 | **Phone Normalization** | 電話番号を正規化・フォーマット・確認再生・DB 保存 | ⭐⭐ |
| 3 | **DOB Re-confirmation** | 生年月日の多様な表現を解析・確認再生・DB 保存 | ⭐⭐⭐⭐ |
| 4 | **Date Classifier** | 発話から日付を抽出し、休診日判定 | ⭐⭐⭐⭐ |

---

## 📋 各モジュールのプロパティ一覧(早見表)

### Module Result Binder
| プロパティ名(日本語) | プロパティ名(コード) | 説明 |
|---|---|---|
| **参照元モジュール名** | `module` | 結果を取得したい参照元モジュール名 |
| **変数名** | `variable` | 格納先変数名(以降のモジュールで `<%変数名%>` として参照可能) |
| **コンテキスト名** | `contextName` | DB に保存する際のコンテキストフィールド名(`contextDisplayType` と両方設定で有効) |
| **コンテキスト表示タイプ** | `contextDisplayType` | DB 上での表示タイプ(`Text` / `PHONE_NUMBER` / `Date` など) |

### Phone Normalization
| プロパティ名(日本語) | プロパティ名(コード) | 説明 |
|---|---|---|
| **参照元モジュール名** | `module` | 参照元モジュール名(設定時: CASE A、未設定時: CASE B) |
| **ガイダンス** | `prompt` | 再生ガイダンス(`#data#` または `<%incoming_phone%>` を使用) |
| **読み上げモード** | `phoneReadingMode` | `全桁` / `下4桁`(CASE B で使用) |
| **コンテキスト保存** | `saveAdditionalPhoneNumber2DB` | `yes` = `additionalPhoneNumber` として DB 保存 |
| *(外部変数)* | `.incomingPhone` | 外部から渡される着信番号(オプション) |

### DOB Re-confirmation
| プロパティ名(日本語) | プロパティ名(コード) | 説明 |
|---|---|---|
| **ガイダンス** | `prompt` | 再生ガイダンス(`#data#` で日付を挿入) |
| **参照元モジュール名** | `module` | 参照元 STT/DTMF モジュール名 |
| **生年読み上げモード** | `dateReadingMode` | `和暦` / `西暦` / `自動`(デフォルト、入力に従って読み上げ) |
| **コンテキスト保存** | `saveDOB2db` | `yes` = `patientDateOfBirth` として DB 保存 |
| *(外部変数)* | `.openAI_generate.url` | OpenAI proxy エンドポイント(LLM フォールバック用) |

### Date Classifier
| プロパティ名(日本語) | プロパティ名(コード) | 説明 |
|---|---|---|
| **参照元モジュール名** | `module` | STT/DTMF の参照元モジュール名 |
| **祝日ソース(CSVのみ)** | `holidaySource` | 祝日CSVのURL(内閣府形式、Shift_JIS) |
| **カスタム休業日ソース(CSVのみ)** | `customHoliday` | 独自休診日CSVのURL(UTF-8) |
| *(外部変数)* | `.openAI_generate.url` | OpenAI proxy エンドポイント |
| **除外モード** | `dateFilterMode` | `土日祝日` / `祝日` / `土日` / `日祝日` / `土` / `日` / `なし` |
| **受付開始までの診療日数**<br>(0=当日、1=翌診療日…) | `blockDays` | 受付不可日数 |
| **診療日カウント除外モード** | `blockDaysSkip` | 診療日カウント時のスキップモード |
| **複数日指定時、1件でも休診日ならNGにする** | `partialClosedDayMode` | `yes` = 1件でも休診ならNG、`no` = 全件休診のみNG |

---

## 📁 各モジュールの詳細

- [01. Module Result Binder](./01_Module_Result_Binder.md)
- [02. Phone Normalization](./02_Phone_Normalization.md)
- [03. DOB Re-confirmation](./03_DOB_Re-confirmation.md)
- [04. Date Classifier](./04_Date_Classifier.md)
