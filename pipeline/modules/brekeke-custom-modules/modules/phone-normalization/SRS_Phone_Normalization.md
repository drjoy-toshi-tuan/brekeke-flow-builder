# 📞 Phone Normalization

## 1. 🎯 概要(シンプルな説明)

**Phone Normalization** は、**日本の電話番号**を処理するモジュールで、主に2つの機能を持ちます。

### 🔹 CASE A: 参照元モジュールがある場合(STT/DTMF)
顧客が音声またはキー入力で電話番号を入力した場合、以下を実行します:
1. 番号を**正規化**(数字のみ抽出)
2. **妥当性チェック**(11桁系: 090/080/070/060/050、固定系 10桁)
3. **日本式ハイフンを挿入**(例: `090-1234-5678`、`03-1234-5678`)
4. 番号を**再生**して顧客に確認(prompt 内の `#data#` を置換)

### 🔹 CASE B: 参照元モジュールがない場合(着信番号処理)
通話の着信番号を取得し、以下を実行します:
1. **データベースに保存**(数字のみの形式で、`saveAdditionalPhoneNumber2DB = yes` 時)
2. 顧客に**再生**して確認(全桁読み上げ、または下4桁のみ読み上げ)

> 💡 **例:**
> - 入力: `09012345678` → 出力: `090-1234-5678`
> - 入力: `0312345678` → 出力: `03-1234-5678`
> - 入力: `0422123456` → 出力: `0422-12-3456`(武蔵野エリア)

> 📌 **`+81` について:** 国際形式(`+81...`)から国内形式(`0...`)への変換は**通常バックエンド側で処理済み**です。モジュール内では CASE B の着信番号取得時および `formatJapanesePhone` 内で先頭 `+81` の保険的変換を行いますが、CASE A のモジュール結果は国内形式で渡される前提です。

---

## 2. 📋 仕様(シンプル)

| 項目 | 内容 |
|---|---|
| **モジュール名** | Phone Normalization |
| **機能** | 日本の電話番号の正規化・フォーマット・確認再生 |
| **対応範囲** | 11桁番号(090/080/070/060/050)、固定電話(市外局番 2〜5 桁) |
| **参照データ** | 総務省の番号計画に基づく市外局番リスト(AREA_2、AREA_3、AREA_4、AREA_5) |
| **外部依存** | なし(LLM/外部 HTTP 呼び出しは行わない) |

### 📑 フォーマットルール

| 種別 | 桁数 | フォーマット例 | 区切り | `phone_type` |
|---|:---:|---|---|---|
| 携帯電話(090/080/070/060) | 11 | `090-1234-5678` | 3-4-4 | `mobile` |
| IP電話など(050) | 11 | `050-1234-5678` | 3-4-4 | `landline` |
| 固定(2桁市外局番: 03, 06) | 10 | `03-1234-5678` | 2-4-4 | `landline` |
| 固定(3桁市外局番: 011, 052...) | 10 | `052-123-4567` | 3-3-4 | `landline` |
| 固定(4桁市外局番: 0422...) | 10 | `0422-12-3456` | 4-2-4 | `landline` |
| 固定(5桁市外局番: 04992...) | 10 | `04992-1-2345` | 5-1-4 | `landline` |
| その他(AREA 不一致の10桁) | 10 | `XXX-XXX-XXXX` | 3-3-4(既定) | `landline` |

> 📌 **`phone_type` の判定(`getPhoneType`):** 先頭3桁が `090/080/070/060` のみ `"mobile"`、それ以外(`050` および固定電話を含む)はすべて `"landline"`。**`050` は固定電話(IP電話)扱い**です。
>
> 📌 **桁数チェックのグループ(CASE A):** 先頭が `090/080/070/060/050` → **11桁**必須、それ以外 → **10桁**必須。`050` は固定電話ですが桁数チェック上は 11桁グループに属します。
>
> 📌 **先頭が `0` でなければ INVALID(CASE A):** 日本の国内番号は必ず先頭が `0` です。先頭が `0` でない場合は、桁数が合っていても **INVALID** として扱います(例: `9012345678` は10桁ですが先頭0が無いため INVALID)。

### 🔁 処理フロー

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

### 📤 setResult の戻り値

| 値 | 意味 |
|---|---|
| *(フォーマット済み番号)* | 正規化成功(CASE A) |
| `INVALID` | 不正な番号(先頭が `0` でない / 桁数が条件を満たさない: 11桁系で11桁でない / 固定系で10桁でない) |
| `NO_RESULT` | 参照元モジュールが番号を返さなかった(CASE A) |
| `INCOMING_PROCESSED` | 着信番号の処理完了(CASE B) |
| *(設定なし)* | CASE B で着信番号が取得できなかった場合は `setResult` を行いません |

### 🗂️ 副作用(setObject / DB)

| 対象 | 設定タイミング | 内容 |
|---|---|---|
| `phone_type` (object) | CASE A 正常時 / CASE B 番号あり時 | `"mobile"`(先頭 090/080/070/060)または `"landline"`(050 および固定) |
| `incoming_phone` (object) | CASE B のみ | 読み上げ用の整形値(全桁=ハイフン付き、下4桁=スペース区切り)。`<%incoming_phone%>` で参照 |
| `additionalPhoneNumber` (object) | DB 保存成功時(両 CASE) | 数字のみの番号(DB 保存と同値) |
| `additionalPhoneNumber` (DB context) | `saveAdditionalPhoneNumber2DB = yes` 時(両 CASE) | `contextName=additionalPhoneNumber` / `displayType=PHONE_NUMBER` / `value=`数字のみ |
| `seq` (variable) | utterance 保存成功時 | 発話順序番号をインクリメント |

---

## 3. 🛠️ 使用方法(詳細)

### 3.1. プロパティ設定

| プロパティ名(日本語) | プロパティ名(コード) | 必須 | 説明 | 例 |
|---|---|:---:|---|---|
| **参照元モジュール名** | `module` | ⚪ 任意 | 参照元 STT/DTMF モジュール名。設定あり → CASE A、未設定 → CASE B。 | `stt_phone`, `dtmf_phone` |
| **ガイダンス** | `prompt` | ✅ 必須 | 確認用ガイダンス。`#data#`(CASE A)または `<%incoming_phone%>`(CASE B)をプレースホルダーとして使用。`<%...%>` 系のテンプレート変数は両 CASE で展開される。 | `お電話番号は #data# でよろしいでしょうか?` |
| **読み上げモード** | `phoneReadingMode` | ⚪ 任意 | 読み上げモード(**CASE B のみ有効**)。`下4桁` = 下4桁のみ(1文字ずつスペース区切り)、それ以外(未設定含む)= 全桁(ハイフン付き)。 | `下4桁` |
| **コンテキスト保存** | `saveAdditionalPhoneNumber2DB` | ⚪ 任意 | `yes` = `additionalPhoneNumber` として DB 保存、`no`(デフォルト)= DB 保存しない。CASE A / CASE B の両方に適用。 | `yes` |
| *(外部変数)* | `.incomingPhone` | ⚪ 任意 | 外部から渡される着信番号(CASE B)。未設定の場合は `$ivr.getOtherNumber()` から取得。 | `09012345678` |

> 📌 CASE A では `phoneReadingMode` は参照されません(常に全桁のハイフン付きで読み上げ)。

### 3.2. 使用例

#### 🎬 シナリオ1: 顧客が発話した番号の確認(CASE A)

**状況:** 顧客が電話番号を発話し、確認および DB 保存が必要な場合。

| ステップ | モジュール | プロパティ設定 |
|---|---|---|
| 1 | STT(Node Name = `stt_phone`) | 音声から電話番号を認識 |
| 2 | Phone Normalization | `module = stt_phone`<br>`prompt = お客様のお電話番号は #data# でよろしいでしょうか?`<br>`saveAdditionalPhoneNumber2DB = yes` |

**結果:**
- 顧客発話: 「ぜろきゅう ぜろ いち に さん よん...」
- STT 出力: `09012345678`
- IVR 再生: *「お客様のお電話番号は 090-1234-5678 でよろしいでしょうか?」*
- DB 保存: `additionalPhoneNumber = 09012345678`(数字のみ)
- `phone_type` = `mobile`
- `setResult`: `090-1234-5678`

#### 🎬 シナリオ2: 着信番号の確認(全桁読み上げ + DB 保存)(CASE B)

| ステップ | モジュール | プロパティ設定 |
|---|---|---|
| 1 | Phone Normalization | `module =` *(未設定)*<br>`prompt = 発信番号 <%incoming_phone%> からのお電話でよろしいでしょうか?`<br>`phoneReadingMode = 全桁`<br>`saveAdditionalPhoneNumber2DB = yes` |

**結果:**
- IVR 再生: *「発信番号 090-1234-5678 からのお電話で...」*
- DB 保存: `additionalPhoneNumber = 09012345678`(数字のみ)
- `setResult`: `INCOMING_PROCESSED`

#### 🎬 シナリオ3: 下4桁のみ確認(セキュリティ用途)(CASE B)

| ステップ | モジュール | プロパティ設定 |
|---|---|---|
| 1 | Phone Normalization | `module =` *(未設定)*<br>`prompt = 下4桁が <%incoming_phone%> のお電話でよろしいでしょうか?`<br>`phoneReadingMode = 下4桁` |

**結果:**
- 着信番号: `09012345678`
- 変数 `incoming_phone` = `"5 6 7 8"`(AmiVoice が1文字ずつ読むようスペース区切り)
- IVR 再生: *「下4桁が 5 6 7 8 のお電話で...」*
- `setResult`: `INCOMING_PROCESSED`

### 3.3. 特殊な処理

> 🔍 **11桁系の識別:** 先頭 `090`, `080`, `070`, `060`, `050` は 11桁グループとして桁数チェックされます。フォーマットは 3-4-4(例: `050-1234-5678`)。
>
> 🔍 **`phone_type` の分類:** `090/080/070/060` のみ `mobile`、`050` および固定電話は `landline`。
>
> 🔍 **固定電話の市外局番識別:** 5桁 → 4桁 → 3桁 → 2桁 の順にチェック。例: `04992` は AREA_5 に一致 → `04992-X-XXXX` 形式。
>
> 🔍 **市外局番が不一致の場合:** どの AREA にも一致しない 10桁番号は、既定で `XXX-XXX-XXXX`(3-3-4)形式になります。
>
> 🔍 **「下4桁」モード(CASE B):** 音声エンジン(AmiVoice)が1文字ずつ読み上げるよう、**各数字の間にスペース**を挿入します。これにより「ごせんろっぴゃくななじゅうはち」のような読み方を回避します。

### 3.4. 注意事項

> ⚠️ **`+81` の正規化はバックエンドで実施済み** — モジュールに渡る番号は国内形式(`0` 始まり)が前提。CASE B の着信番号取得および `formatJapanesePhone` 内には先頭 `+81 → 0` の保険的変換が残っていますが、CASE A のモジュール結果には適用されません。
>
> ⚠️ **DB 保存は `saveAdditionalPhoneNumber2DB = yes` の場合のみ** — CASE A / CASE B の両方で適用。保存先コンテキスト名は `additionalPhoneNumber`、`displayType = PHONE_NUMBER`、保存値は**ハイフンなしの数字のみ**。
>
> ⚠️ **CASE A では `incoming_phone` 変数は設定されません** — この変数は CASE B 専用です(`phone_type` は両 CASE で設定)。
>
> ⚠️ **`prompt` が空の場合**、処理は実行されますが**音声再生は行われません**(発話テキストは `$ivr.exec("tts-prompt", "extractTaggedContent", { stripTags: true })` でプロンプトから抽出しますが、その結果も空になるため utterance ログも保存されません)。
>
> ⚠️ **CASE B で着信番号が取得できない場合**、DB 保存・再生・`setResult` のいずれも行われません(`setResult` は未設定のまま)。
