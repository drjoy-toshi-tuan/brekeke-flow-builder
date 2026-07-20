# 🏥 Clinical Department Classifier

## 1. 🎯 概要(シンプルな説明)

**Clinical Department Classifier** は、STT が認識した**診療科名**を受け取り、あらかじめ定義した**診療科グループ**に振り分けて、フロー分岐用の**結果名**を出力するモジュールです。同時に、認識した診療科名をオブジェクトに格納し、必要に応じて DB に保存します。

主な役割は以下の3点です。

- 参照元 STT モジュールから**診療科名を取得**する
- 取得した診療科名を `clinical_department_1〜10` のグループと**完全一致で照合**し、対応する `result_name_i` を `setResult` で返す(フロー分岐に使用)
- 取得した診療科名を**オブジェクト `clinical_department` に格納**し、オプションで **DB(`clinicalDepartment`)に保存**する

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

> 💡 **実例:**
> - STT 出力: *「整形外科」* → `clinical_department_2 = "整形外科;リハビリテーション科"` にマッチ → `result_name_2 = "orthopedics"` を出力
> - STT 出力: *「内科」* → どのグループにも該当しない → `NOT_COVERED`
> - STT 出力: *「TIMEOUT」* → そのまま `TIMEOUT` を出力(分類・保存なし)

---

## 2. 📋 仕様(シンプル)

| 項目 | 内容 |
|---|---|
| **モジュール名** | Clinical Department Classifier(内部ログ名: `ClinicalDeptClassifier`) |
| **機能** | STT で認識した診療科名をグループに振り分け、結果名を出力 + オブジェクト格納 + DB 保存(オプション) |
| **入力** | 参照元モジュールの結果(`$runner.getModuleResult(module)`) |
| **出力(setResult)** | 結果名(`result_name_i`)、または `group_N` / `NOT_COVERED` / `NO_RESULT` / `TIMEOUT` / `ERROR` |
| **副作用** | `$runner.setObject("clinical_department", 値)`<br>`save2db` により `clinicalDepartment` を DB 保存(条件付き) |

### 🔁 処理フロー

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

### 📤 setResult の戻り値

| 値 | 意味 |
|---|---|
| *(result_name_i の値)* | グループ `i` にマッチし、`result_name_i` が設定されている |
| `group_N` | グループ `N` にマッチしたが `result_name_N` が未設定(フォールバック) |
| `NOT_COVERED` | 有効な診療科名は取得できたが、どのグループにもマッチしない |
| `NO_RESULT` | `module` が未設定、または参照元が `null`/`undefined`/空文字を返した |
| `TIMEOUT` | 参照元モジュールが `TIMEOUT` を返した(そのまま通過) |
| `ERROR` | 参照元モジュールが `ERROR` を返した(そのまま通過) |

> 📌 `module` が未設定の場合は `setResult("NO_RESULT")` を行った後に **`Error` を throw して終了**します。

---

## 3. 🛠️ 使用方法(詳細)

### 3.1. プロパティ設定

| プロパティ名(日本語) | プロパティ名(コード) | 必須 | デフォルト | 説明 |
|---|---|:---:|---|---|
| **参照元モジュール名** | `module` | ✅ **必須** | *(空)* | 診療科名を取得する参照元 STT モジュールの Node Name。未設定の場合は `NO_RESULT` を出力後、例外終了。 |
| **DB保存フラグ** | `saveDepartment2DB` | ⚪ 任意 | `no` | `yes` = 診療科名を `clinicalDepartment`(displayType: `DEPARTMENT`)として DB 保存。`no` = 保存しない。 |
| **診療科グループ 1〜10** | `clinical_department_1` 〜 `clinical_department_10` | ⚪ 任意 | *(空)* | グループに含める診療科名。**セミコロン(`;`)区切り**で複数指定可(各要素は前後の空白を除去して照合)。 |
| **結果名 1〜10** | `result_name_1` 〜 `result_name_10` | ⚪ 任意 | *(空)* | 対応する `clinical_department_i` にマッチしたときに `setResult` で返す値。未設定の場合は `group_i` がフォールバックとして使用される。 |

> 📌 `clinical_department_i` と `result_name_i` は**同じ番号 `i`(1〜10)で対応**します。グループは番号順(1→10)にチェックされ、**最初にマッチしたグループで確定**(以降はチェックしません)。

### 3.2. 照合(マッチング)の仕組み

- STT の結果は **前後の空白を除去(`trim`)** した後に照合されます。
- 各グループは `;` で分割され、**各診療科名と完全一致(大文字小文字・表記ゆれを区別)**で比較されます。前方一致や部分一致ではありません。
- したがって、STT が返す可能性のある**表記ゆれ(別名・かな・英字など)**は、すべて同じグループ内に `;` で列挙しておく必要があります。

例:
```
clinical_department_1 = 内科;一般内科;ないか
result_name_1         = general_medicine
```
→ STT が `内科` / `一般内科` / `ないか` のいずれを返しても `general_medicine` に分類されます。

### 3.3. 使用例

#### 🎬 シナリオ1: 診療科をグループに振り分け(フロー分岐)

| プロパティ | 値 |
|---|---|
| `module` | `stt_department` |
| `clinical_department_1` | `内科;呼吸器内科;消化器内科` |
| `result_name_1` | `general_medicine` |
| `clinical_department_2` | `整形外科;リハビリテーション科` |
| `result_name_2` | `orthopedics` |

**実行:**
- STT 出力: `整形外科`
- `clinical_department` オブジェクト = `整形外科`
- グループ2にマッチ → `setResult`: `orthopedics`
- 後続ノードで `orthopedics` ブランチへ分岐

#### 🎬 シナリオ2: グループ未該当(NOT_COVERED)

| プロパティ | 値 |
|---|---|
| `module` | `stt_department` |
| `clinical_department_1` | `整形外科;リハビリテーション科` |
| `result_name_1` | `orthopedics` |

**実行:**
- STT 出力: `皮膚科`
- `clinical_department` オブジェクト = `皮膚科`
- どのグループにもマッチしない → `setResult`: `NOT_COVERED`
- 「対応していない診療科です」案内ブランチへ分岐

#### 🎬 シナリオ3: result_name 未設定(group_N フォールバック)

| プロパティ | 値 |
|---|---|
| `module` | `stt_department` |
| `clinical_department_3` | `小児科` |
| `result_name_3` | *(未設定)* |

**実行:**
- STT 出力: `小児科`
- グループ3にマッチするが `result_name_3` が空 → `setResult`: `group_3`(警告ログ出力)

#### 🎬 シナリオ4: 診療科名を DB に保存

| プロパティ | 値 |
|---|---|
| `module` | `stt_department` |
| `saveDepartment2DB` | `yes` |
| `clinical_department_1` | `内科` |
| `result_name_1` | `general_medicine` |

**実行:**
- STT 出力: `内科`
- DB 保存: `clinicalDepartment = 内科`(displayType: `DEPARTMENT`)
- `clinical_department` オブジェクト = `内科`
- `setResult`: `general_medicine`

> 📌 DB 保存とオブジェクト格納は、有効な診療科名が取得できた時点で実行されます(グループにマッチしない `NOT_COVERED` の場合でも実行されます)。

### 3.4. 重要な注意事項

> ⚠️ **`module` は必須** — 未設定の場合、`setResult("NO_RESULT")` の後に `Error`(`module property is required`)を throw して処理を終了します。
>
> ⚠️ **完全一致での照合** — STT 結果は `trim` 後に各診療科名と**完全一致**で比較されます。表記ゆれは `clinical_department_i` 内に `;` 区切りですべて列挙してください。
>
> ⚠️ **最初のマッチが優先** — グループは番号順(1→10)に評価され、最初にマッチした時点で確定します。同じ診療科名を複数グループに重複登録した場合、若い番号のグループが優先されます。
>
> ⚠️ **`clinical_department` には生の STT 値が入る** — オブジェクトに格納されるのは分類結果(`result_name`)ではなく、STT が返した診療科名そのものです。後続で `<%clinical_department%>` として参照できます。
>
> ⚠️ **`TIMEOUT` / `ERROR` はそのまま通過** — この場合、オブジェクト格納・DB 保存・分類処理は行われません。別のフローブランチで処理してください。
>
> ⚠️ **DB 保存の値は診療科名そのもの** — `contextName = clinicalDepartment`、`displayType = DEPARTMENT`、`value =` 取得した診療科名(`result_name` ではない)。

---

## 4. 📊 よくある使用パターン

| ユースケース | 設定方法 |
|---|---|
| 診療科を数グループに分けてフロー分岐 | `clinical_department_1〜N` + `result_name_1〜N` を設定 |
| 表記ゆれ・別名を1グループに集約 | 1つの `clinical_department_i` に `;` 区切りで列挙(例: `内科;一般内科;ないか`) |
| 認識した診療科名を後続で読み上げ・再利用 | `<%clinical_department%>` を参照(設定不要、有効値時に自動格納) |
| 診療科名を患者情報として DB 保存 | `saveDepartment2DB = yes` |
| 対応外の診療科を専用ブランチへ | `NOT_COVERED` の戻り値で分岐 |
| 異常(タイムアウト/エラー)時のリトライ | `TIMEOUT` / `ERROR` の戻り値で分岐 |