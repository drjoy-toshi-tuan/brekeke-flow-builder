# 📘 Module Result Binder

## 1. 🎯 概要(シンプルな説明)

**Module Result Binder** は、モジュール間でデータを受け渡すための「ブリッジ」モジュールです。主な機能は以下の3点です。

- 他のモジュールの**出力結果を取得**する(または既存の**変数(オブジェクト)の値を取得**する)
- 取得した結果を**指定した変数名(オブジェクト)に格納**し、以降のモジュールで `<%変数名%>` として参照可能にする
- 取得した結果を**DBコンテキストフィールドとして保存**する(オプション)

> 💡 **簡単な例:**
> モジュール A(STT)が「田中太郎」という応答を取得した場合、Module Result Binder はこの結果を取得して `customer_name` という変数に格納します。その後、音声再生モジュールで *「`<%customer_name%>` 様、ご確認ありがとうございます」* のように使用できます。さらに `contextName` と `contextDisplayType` を設定すれば、患者情報として DB にも保存できます。

> 🔁 **2種類の取得モード:** `module` プロパティの指定方法によって取得元が切り替わります。
> - **モジュール結果モード**(通常): `module = stt_name` のように Node Name を指定 → `getModuleResult` で取得
> - **変数参照モード**: `module = <%customer_name%>` のように `<%...%>` 形式で指定 → `getObject` で既存変数の値を取得

---

## 2. 📋 仕様(シンプル)

| 項目 | 内容 |
|---|---|
| **モジュール名** | Module Result Binder |
| **主な機能** | 他モジュールの結果(または既存変数の値)を取得し、変数として受け渡す + DB コンテキスト保存(オプション) |
| **入力** | 参照元(`module`: Node Name または `<%変数名%>`)、格納先変数名(`variable`)、DB保存設定(`contextName`、`contextDisplayType`) |
| **出力(setResult)** | 結果文字列、または `NO_RESULT` / `time_out` / `error` |
| **副作用** | `$runner.setObject()` により変数をコンテキストに格納<br>`save2db` により DB へコンテキストフィールド保存(条件付き) |

### 🔁 処理フロー

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

### 📤 setResult の戻り値

| 値 | 意味 |
|---|---|
| `NO_RESULT` | `module` プロパティが未設定、または取得元(モジュール結果 / 参照変数)の出力が空 |
| `time_out` | 参照元モジュールがタイムアウト |
| `error` | 参照元モジュールがエラー |
| *(結果文字列)* | 取得元の正常な結果(前後空白除去済み) |

---

## 3. 🛠️ 使用方法(詳細)

### 3.1. プロパティ設定

**プロパティ設定** タブで以下を設定します。

| プロパティ名(日本語) | プロパティ名(コード) | 必須 | 説明 | 例 |
|---|---|:---:|---|---|
| **参照元** | `module` | ✅ **必須** | 取得元の指定。**Node Name** を指定すると `getModuleResult` で取得(モジュール結果モード)。`<%変数名%>` 形式を指定すると `getObject` で既存変数の値を取得(変数参照モード)。未設定の場合は `NO_RESULT`。 | `stt_name`, `dtmf_birthday`, `<%customer_name%>` |
| **変数名** | `variable` | ⚪ 任意 | 格納先変数名。未設定の場合は変数への格納はスキップされ、`setResult` のみ実行されます。 | `customer_name`, `birth_date` |
| **コンテキスト名** | `contextName` | ⚪ 任意 | DB に保存する際のコンテキストフィールド名。`contextDisplayType` と**両方**設定された場合のみ DB 保存が実行されます。 | `patientName`, `phoneNumber` |
| **コンテキスト形式** | `contextDisplayType` | ⚪ 任意 | DB 上での表示タイプ。`contextName` と**両方**設定された場合のみ DB 保存が実行されます。 | `Text`, `PHONE_NUMBER`, `Date` |

> 📌 **変数参照モードの判定:** `module` の値が**完全に** `<%...%>` の形(例: `<%customer_name%>`)である場合のみ変数参照モードになります。前後に他の文字が混ざる場合(例: `<%a%>b`)はモジュール結果モードとして扱われます。

### 3.2. 格納した結果の使用方法

Module Result Binder 実行後、以下の方法で結果を使用できます。

**方法1: 変数として使用(`variable` を設定した場合)**
後続モジュールの prompt、ガイダンス、プロパティなどで使用可能:
```
こんにちは、<%customer_name%> 様
```

**方法2: setResult でフロー分岐**
値に応じてフローを分岐:
- `result = "NO_RESULT"` → 「再質問」ブランチへ
- `result = "time_out"` → 「リトライ」ブランチへ
- 正常な値 → 「確認」ブランチへ

### 3.3. 使用例

#### シナリオ1: 顧客名を変数として保存(DB保存なし)

STT モジュールから顧客名を取得し、複数箇所で再利用する。

| ステップ | モジュール | プロパティ設定 |
|---|---|---|
| 1 | STT(Node Name = `stt_name`) | *(音声から顧客名を取得)* |
| 2 | Module Result Binder | `module = stt_name`<br>`variable = customer_name` |
| 3 | 音声再生 | `prompt = <%customer_name%> 様、ありがとうございます` |
| 4 | 音声再生(フロー末尾) | `prompt = <%customer_name%> 様、またお電話お待ちしております` |

#### シナリオ2: 顧客名を変数+DBの両方に保存

STT モジュールから取得した顧客名を、後続処理での参照用に変数として保存しつつ、患者情報として DB にも記録する。

| ステップ | モジュール | プロパティ設定 |
|---|---|---|
| 1 | STT(Node Name = `stt_name`) | *(音声から顧客名を取得)* |
| 2 | Module Result Binder | `module = stt_name`<br>`variable = customer_name`<br>`contextName = patientName`<br>`contextDisplayType = Text` |
| 3 | 音声再生 | `prompt = <%customer_name%> 様、ご確認ありがとうございます` |

**結果:**
- 変数 `<%customer_name%>` で参照可能
- DB の `patientName` フィールドに保存(displayType: Text)

#### シナリオ3: 既存変数の値を取得して DB に保存(変数参照モード)

先行モジュールで既に変数(オブジェクト)に格納済みの値を、Module Result Binder で取り出して DB に保存する。あるいは別名の変数へコピーする。

| ステップ | モジュール | プロパティ設定 |
|---|---|---|
| 1 | *(先行処理で `customer_name` を格納済み)* | — |
| 2 | Module Result Binder | `module = <%customer_name%>`<br>`contextName = patientName`<br>`contextDisplayType = Text` |

**結果:**
- `getObject("customer_name")` で値を取得
- DB の `patientName` フィールドに保存(displayType: Text)
- 保存成功時、`<%patientName%>` でも参照可能

### 3.4. 重要な注意事項

> ⚠️ **`module` は2モード** — Node Name 指定は `getModuleResult`、`<%変数名%>` 指定は `getObject` で取得します。
>
> ⚠️ **結果は `.trim()` される** — 前後の空白は自動的に除去されます(`time_out`/`error` 判定もトリム後の値で行われます)。
>
> ⚠️ **変数名は snake_case 推奨**(例: `customer_name`, `birth_date`)。フロー全体で統一することで、混乱を防げます。
>
> ⚠️ **取得元が存在しない/空の場合** — `getModuleResult` または `getObject` が null/空を返すと、結果は `NO_RESULT` になります。
>
> ⚠️ **`time_out` と `error` はそのまま通過** — 変数には格納されず、DB にも保存されません。これらのケースは別のフローブランチで処理する必要があります。
>
> ⚠️ **DB 保存は `contextName` と `contextDisplayType` の両方が必要** — 片方だけ設定しても DB 保存はスキップされます。
>
> ⚠️ **DB 保存には IVR 接続が必要** — `$ivr.connected()` が false の場合、DB 保存はスキップされます(変数格納と `setResult` は実行されます)。
>
> ⚠️ **DB 保存時の自動変数セット** — DB 保存が成功すると、`contextName` と同名の変数が自動的にセットされます(例: `contextName = patientName` なら `<%patientName%>` でも参照可能)。
>
> ⚠️ **DB 保存は `time_out` / `error` / 空結果の場合は実行されない** — 正常な結果のみ DB に保存されます。

---

## 4. 📊 よくある使用パターン

| ユースケース | 設定方法 |
|---|---|
| 他モジュールの結果をログに残すだけ | `module = xxx`、`variable` は未設定 |
| 顧客名を保存し、後で読み上げに使用 | `module = stt_name`、`variable = customer_name` |
| 正規化済みの電話番号を保存 | `module = phone_norm`、`variable = phone_number` |
| パース済みの予約日を保存 | `module = date_classifier`、`variable = appointment_date` |
| 顧客名を変数+DBの両方に保存 | `module = stt_name`、`variable = customer_name`、`contextName = patientName`、`contextDisplayType = Text` |
| 電話番号を DB のみに保存 | `module = phone_norm`、`contextName = phoneNumber`、`contextDisplayType = PHONE_NUMBER` |
| 既存変数の値を取り出して DB 保存 / 別名コピー | `module = <%customer_name%>`、`contextName = patientName`、`contextDisplayType = Text`(変数参照モード) |
