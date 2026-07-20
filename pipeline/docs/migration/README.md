# 第2世代→第3世代 移管手順書

## 概要

第2世代（OpenAI全プロンプト型）のボイスボットを第3世代（Brekekeフローデザイナー型）に移管するための手順書。

---

## 移管フロー

```
Step 1: 第2世代プロンプトの取得
Step 2: migration ディレクトリへ配置
Step 3: @director で設計書を作成（必須・省略禁止）
Step 4: @generator でフロー生成
Step 5: @reviewer で校閲（6観点）
Step 6: validator.py で検品
Step 7: build_bivr.py で .bivr 生成
Step 8: IVRプロパティ設定（人間作業）
Step 9: Dr.JOY側設定（人間作業）
Step 10: Brekeke インポート → 実機テスト
```

---

## 各ステップの詳細

### Step 1: Google Driveから第2世代プロンプトをコピー

1. Google Drive の該当案件フォルダを開く
2. OpenAI Assistant の設定画面からシステムプロンプトをコピー
3. function定義（JSON部分）もあわせてコピー

### Step 2: docs/migration/ に配置

ファイル名規則: `gen2_{施設名}_{シナリオ名}.txt`

```
docs/migration/
├── gen2_羽生総合病院_診療.txt      ← サンプル
├── gen2_〇〇病院_受付.txt
└── gen2_〇〇クリニック_予約.txt
```

メタ情報はファイル先頭にコメントで記載することを推奨（`docs/migration/gen2_template.md` 参照）。

### Step 3: @director で設計書を作成（必須・省略禁止）

> **🚫 絶対遵守: @director による設計書生成はいかなる場合も省略禁止**
>
> Gen1/Gen2 の顧客資料・プロンプト・YAMLには第3世代固有の設計（冒頭チェーン・サブフロー分割・save2db等）が一切含まれていない。
> @director を通して初めて第3世代の設計書として翻訳される。
> **顧客資料にYAMLが含まれていても @director をスキップしてはならない。**

directorが第2世代プロンプト（または第1世代HTML）を解析し、第3世代の設計書フォーマットに変換する。確認レポートで不足情報（営業時間、非通知アナウンス文言等）を洗い出せる。

```bash
@director docs/migration/gen2_〇〇病院_診療.txt を読んで、第3世代フローの設計書を作成して
```

出力ファイル:
- `output/scenarios/〇〇病院_診療/確認レポート_〇〇病院_診療_{日付}.md` — 確認レポート（不足情報・Dr.JOY側設定事項を含む）
- `output/scenarios/〇〇病院_診療/設計書_〇〇病院_診療.{yaml,md}` — 設計書（サブフロー分割型で構成）

> **確認レポートのBLOCKERを解消してからStep 4に進むこと。**
> 第2世代プロンプトには時間外アナウンス・非通知アナウンスの文言が記載されていないことが多い。

### Step 4: @generator でフロー生成

```bash
# 設計書（Step 3で @director が生成）を入力として使用する
@generator output/scenarios/〇〇病院_診療/設計書_〇〇病院_診療.{yaml,md} を元にフローJSONを生成して
```

出力ファイル（`output/scenarios/{施設名}_{フロー名}/` 配下）:
- `json/draft_{施設名}_{フロー名}.json` — メインフローJSON
- `json/draft_{施設名}_氏名聴取.json` 等 — サブフロー（サブフロー分割型の場合）
- `properties_{施設名}_{フロー名}.md` — IVRプロパティ

> **移管時はサブフロー分割型がデフォルト。** 氏名・生年月日・電話番号・診察券番号はそれぞれ個別サブフローとして `drjoy^Custom Module$Custom Jump to Flow` で遷移する（「個人情報」一括は不可）。電話番号聴取サブフローは `incoming-classifier` で着信番号を分岐した上で、聴取番号の携帯/その他判定はスクリプト（`script_携帯判別`）で行い、集約スクリプト経由でメインフローに返却する。
>
> **saveContextModel2DB のコンテキスト定義**: Gen2 の `endpoint`・`smsFlag`、Gen1 の `checkpoint` はコンテキストフィールドとして含めない。これらは `saveCompletionFlag2db` のパラメータとして管理する。`status` は STATUS 型として必ず含める。

### Step 5: @reviewer で校閲

```bash
@reviewer output/migrated_〇〇病院_診療.json を校閲して
```

### Step 6: validator.py で検品

```bash
python schemas/validator.py output/migrated_〇〇病院_診療.json
```

PASS になるまで修正を繰り返す。

### Step 7: build_bivr.py で .bivr 生成

```bash
python3 scripts/build_bivr.py output/migrated_〇〇病院_診療.json
```

### Step 8: IVRプロパティ設定（人間作業）

`output/scenarios/{施設名}_{フロー名}/properties_{施設名}_{フロー名}.md` を開き、`TODO_` で始まる値を実際の値に置き換えてBrekekeに設定する。

### Step 9: Dr.JOY側設定（人間作業）

確認レポートの「Dr.JOY側設定事項」セクションに記載された項目（SMS文面、営業時間、認証設定等）を設定する。

### Step 10: Brekeke インポート → 実機テスト

1. Brekeke 管理画面からフローをインポート
2. 通話テストを実施
3. 全聴取項目・全分岐パターンを動作確認

---

## ディレクトリ構成

```
docs/migration/
├── README.md              # この手順書
├── gen2_template.md       # 第2世代プロンプトのメタ情報テンプレート
└── gen2_{施設名}_{シナリオ名}.txt  # 第2世代プロンプト（案件ごと）
```

---

## よくある移管パターン

### パターン A: 標準診療予約フロー

```
冒頭(wait) → コンテキスト設定 → 着信分類
  ├── 非通知 → 非通知アナウンス → 切断
  └── 通常 → 冒頭アナウンス
        → 用件振り分け
        → 診療科
        → [Jump: 氏名聴取] → [Jump: 生年月日聴取] → [Jump: 電話番号聴取]
        → 終話
```

### パターン B: 診療科別分岐フロー

```
冒頭(wait) → コンテキスト設定 → 着信分類
  └── 通常 → 冒頭アナウンス → 診療科確認
        ├── 健診センター → 終話_健診案内
        ├── 美容科 → 終話_美容案内
        └── 通常科 → 通常フロー継続
```

### パターン C: 時間外フロー込み

```
冒頭(wait) → コンテキスト設定 → 着信分類
  ├── 非通知 → 非通知アナウンス → 切断
  └── 通常 → 受付時間判定（acceptance_times）
        ├── 時間外 → 時間外アナウンス → 切断
        └── 時間内 → 通常フロー
```

---

## 注意事項

- 第2世代の「聞き直し禁止」「復唱禁止」ロジックは第3世代では **1回のみ聴取するモジュール構成** で実現
- `<speak type="telephone">` / `<speak type="digits">` パターンは **Re-confirmation モジュール** に変換
- `<forward department="..." username="..."/>` パターンは **電話転送モジュール** に変換（要確認）
- status/smsFlag の判定ロジックは **saveCompletionFlag2db のパラメータ** で管理
- **冒頭チェーン（wait → saveContextModel2DB → incoming-classifier）は必須**。第2世代にはない第3世代固有のモジュール
- **個人情報聴取は項目ごとに個別サブフローとして構築する**（氏名・生年月日・電話番号・診察券番号）。`drjoy^Custom Module$Custom Jump to Flow` を使用。電話番号サブフローは `incoming-classifier` + `script_携帯判別` + 集約スクリプトの二段構成で携帯/その他を判定
- **時間外・非通知アナウンスの文言**は第2世代プロンプトに記載がないことが多い。directorの確認レポートで検出される
