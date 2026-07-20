# Context JSON 生成・検証プロンプト仕様（generate_context_spec）

**用途**: 施設ごとの Context 項目仕様（要求仕様テキスト、または既存の Context JSON）を入力すると、`saveContextModel2DB` 用の Context JSON 配列を生成・検証する。
**出力形式**: そのままコピー＆ペーストして使用可能な JSON コードブロック + Markdown 表形式の項目一覧。
**想定LLM**: Claude / ChatGPT 等（本リポジトリのパイプライン外・壁打ち時の入力プロンプトとして使用。director/scaffold の自動生成を置き換えるものではない）
**正本**: 標準12フィールドの定義・型・並び順は `bivr-checker/CLAUDE.md` §7「saveContextModel2DB — fields 構造」が正本。本プロンプトはその仕様をLLMへの指示文として書き起こしたもの。両者が食い違った場合は CLAUDE.md 側を優先し、本ファイルを追随修正する。

---

## プロンプト本文（LLMに貼り付けて使用）

````
入力内容が「要求仕様（テキスト）」か「既存のJSONコード」かによって、以下のいずれかのモードで開始してください。

# Constraints & Workflow

## A. 生成モード（要求仕様が入力された場合）

以下の2ステップで実行してください。

1. **Step 1: 項目確認**
   要求仕様を分析し、必要な項目を抽出してください。ユーザーに対して「抽出した項目（日本語名）のリストは以下でよろしいでしょうか？」と確認を求めてください。※この段階では JSON は出力しない。

2. **Step 2: JSON 出力**
   承認後、後述の【Technical Rules】に従って JSON と Markdown 表形式を出力してください。

## B. 検証モード（JSONコードが直接入力された場合）

提供された JSON を【Technical Rules】に照らして監査し、以下を出力してください。

1. **不備の指摘**: 命名、データ型、並び順、フラグ（itemDefault/deletable）の誤り
2. **修正済みJSON**: 仕様を完全に満たす正しい形式の JSON コード
3. **項目一覧**: Markdown 表形式でのリスト
4. **Context 名の再提示**
5. **完全な Context JSON データ**
6. **saveContextModel2DB 用の JSON 配列（リスト）**

# Technical Rules

1. **並び順**: `itemDefault: true`（標準コンテキスト）の項目を配列の先頭に配置し、その後にカスタム項目を配置すること。

2. **標準コンテキスト（itemDefault: true）**: 以下の項目が含まれる場合は必ず下表の定義に従うこと（順序もこの通り）。

   | contextName | contextNameJp | displayType |
   |---|---|---|
   | classification | 区分 | CLASSIFICATION |
   | patientName | 患者名 | TEXT |
   | medicalCardNumber | 診察券番号 | NUMBER |
   | clinicalDepartment | 診療科 | DEPARTMENT |
   | patientDateOfBirth | 生年月日(和暦) | DATE_OF_BIRTH |
   | reason | 理由 | TEXT |
   | reservationDate | 予約日 | DATE |
   | telephoneNumber | 電話番号 | PHONE_NUMBER_CALL |
   | additionalPhoneNumber | 連絡先電話番号 | PHONE_NUMBER |
   | status | 状態 | STATUS |
   | dateOfCall | 入電日時 | DATE |

3. **カスタム項目（itemDefault: false）**: 標準以外の項目を追加する場合、`deletable: true` と設定すること。

4. **DisplayType の厳守**:

   4-1. **標準コンテキストの displayType は変更禁止**。上表（TEXT / NUMBER / DATE / DATE_OF_BIRTH / CLASSIFICATION / DEPARTMENT / PHONE_NUMBER_CALL / PHONE_NUMBER / STATUS）の値をいかなる場合も変更しないこと。

   4-2. **新規作成するカスタム項目は、値の種類によらず一律 `displayType: "TEXT"` を使用すること**。NUMBER・DATE 等、他の displayType を新規カスタム項目に割り当てることは厳禁とする（標準コンテキストの再利用時のみ 4-1 の値を使う）。

5. **callId の固定フォーマット**: `callId` は `itemDefault: false` だが、案件によらず常に出力に含める（省略不可）。値は以下の形式で固定する。

   ```json
   {
     "contextName": "callId",
     "contextNameJp": "通話ID",
     "rangeValues": [],
     "displayType": "NUMBER",
     "editable": true,
     "deletable": true,
     "itemDefault": false
   }
   ```

6. **JSON形式**: そのままコピー＆ペーストして使用可能な純粋な JSON コードブロックのみを出力すること。解説や前置きは不要。

# 入力情報（要求仕様）

[ここに聴取したい項目やフローの概要を入力してください]

- 出力形式は **Markdown**
- JSON は **そのままコピーして使用できる形式** にすること

---

## 標準的なJSON構造の例（参考）

```json
[
  {
    "contextName": "classification",
    "contextNameJp": "区分",
    "rangeValues": [
      { "value": "新規", "order": 1 },
      { "value": "変更", "order": 2 },
      { "value": "キャンセル", "order": 3 }
    ],
    "displayType": "CLASSIFICATION",
    "editable": true,
    "deletable": false,
    "itemDefault": true
  },
  {
    "contextName": "patientName",
    "contextNameJp": "患者名",
    "rangeValues": [],
    "displayType": "TEXT",
    "editable": true,
    "deletable": false,
    "itemDefault": true
  },
  {
    "contextName": "custom_inquiry",
    "contextNameJp": "独自問い合わせ",
    "rangeValues": [],
    "displayType": "TEXT",
    "editable": true,
    "deletable": true,
    "itemDefault": false
  },
  {
    "contextName": "callId",
    "contextNameJp": "通話ID",
    "rangeValues": [],
    "displayType": "NUMBER",
    "editable": true,
    "deletable": true,
    "itemDefault": false
  }
]
```
````

---

## エンジニアとしてのヒント

`itemDefault: true` の項目は、システムが標準的に期待している挙動（ログ表示など）に直結している。LLM にJSONを生成させる際は、必ずこれらをリストの先頭に固めることで、管理画面での視認性とシステムの安定性を確保できる。

## 関連ファイル

| ファイル | 内容 |
|---|---|
| `bivr-checker/CLAUDE.md` §7 | 標準12フィールド定義・displayType制約・rangeValues形式の正本 |
| `bivr-checker/reference/context/context_fields_common.json` | 標準フィールドの実データ（本プロンプトのルール4-1が参照する値） |
| `bivr-checker/reference/context/context_fields_checkup.json` | 健診シナリオ向けの追加フィールド例 |
| `bivr-checker/reference/context/context_fields_medical.json` | 診療シナリオ向けの追加フィールド例 |
