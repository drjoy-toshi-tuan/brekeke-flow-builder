---
name: extract-yesno-synonyms
description: Brekeke ログから「はい/いいえ」意図のユーザー発話を 1 ヶ月分まとめて抽出し、エンティティ類義語辞書アップロード用 CSV を生成する skill。OpenAI 分類が荒れている問題に対して、生の文字起こしを大量に集めて類義語登録するためのデータ収集。Drive MCP で月別フォルダから日次 CSV をダウンロード → 正規表現で `save-dialogue` / `OpenAI_*` / `Script_*` ペア抽出 → ラベル + キーワードで 6 バケット分類 → 上位バケット (yes_confirmed / no_confirmed) を `/` 区切りで concatenate して 2 列 CSV (エンティティ名,類義語) を生成 (1 row 1 entity)。
---

# extract-yesno-synonyms — Brekeke ログ → 類義語辞書 CSV 生成

## このスキルが解決する問題

OpenAI の yes/no 分類が現場で荒れている。STT 文字起こしには「いいえ違います」「はいそうです」など多様な言い回しが存在し、それらを類義語辞書に登録すれば NLU 精度が改善する。だが手動で集めるのは現実的でない。**月単位の Brekeke ログから機械的に抽出 + 分類して、辞書アップロード CSV を 1 コマンドで生成する。**

## 起動例

```
/extract-yesno-synonyms 2026-04
/extract-yesno-synonyms 2026-04 1d57MCeYlldf91QW6DHWVSwWOqa6OK6qw
```

引数:
- 第 1 引数 (必須): 対象月 `YYYY-MM`
- 第 2 引数 (任意): Brekeke ログ親フォルダ ID。省略時は既定の Drive 親フォルダ `1d57MCeYlldf91QW6DHWVSwWOqa6OK6qw` (`202602_BrekekeLog` 等を含む親) を使う

対象は **本番 (`01.本番`) のみ**。デモは含めない。

## 入力データ仕様 (Brekeke ログ CSV)

- 親フォルダに `YYYYMM_BrekekeLog/` サブフォルダ
- その下に `01.本番/` `02.デモ/` サブフォルダ
- `01.本番/` 配下に日次 CSV が `YYYYMMDD.csv` 形式で並ぶ (約 30 ファイル/月、合計 ~30MB UTF-8)
- 各 CSV はヘッダー無し、1 行 = 1 通話
- 列 (列位置は不安定、**正規表現で位置に依存せず抽出**すること):
  - 通話 ID / シーケンス / 電話番号 / 内線番号 / シナリオパス / 日時 / 通話長 / モジュールトレース
- モジュールトレースは `;` 区切りで `key:value` ペアが並ぶ。重要キー:
  - `save-dialogue<N>:<ユーザー発話>` — STT 文字起こし (`OK`/`true`/`false` は status マーカー、スキップ)
  - `OpenAI_<module>:<label>` — OpenAI 分類結果
  - `Script_<module>:<label>` — CMR (正規表現/辞書) 分類結果

## 出力 (既定ディレクトリ: `C:/Users/hamaguchi.t/yes_no_analysis_<YYYYMM>/`)

| ファイル | 用途 |
|---|---|
| **`entity_synonyms_final_slash.csv`** | **辞書アップロード用 CSV**。これを そのまま エンティティ管理画面にアップする |
| `yes_confirmed.csv` | OpenAI=yes-family AND text=yes キーワード一致。辞書ネタ主材料 |
| `no_confirmed.csv` | OpenAI=no-family AND text=no キーワード一致。辞書ネタ主材料 |
| `yes_openai_only.csv` | OpenAI=yes だが text キーワード未一致。要レビュー |
| `no_openai_only.csv` | OpenAI=no だが text キーワード未一致。要レビュー |
| `disagree.csv` | text vs OpenAI 不一致。**OpenAI 誤分類の証跡集** |
| `unclear.csv` | OpenAI=`NO_RESULT` 等。大半は DTMF (1/2/3/4) 想定外データ |
| `all_pairs_raw.csv` | 全ペア生データ (date/call_id/scenario 付き、深掘り用) |
| `summary.md` | 全体統計 + 上位 20 発話/バケット + 観測事項 |
| `raw/` | ダウンロード済の原 CSV 30 ファイル |

## 分類規則

```python
YES_LABELS = {'あり', '該当', 'はい', 'yes', 'true', 'YES', 'TRUE'}
NO_LABELS  = {'なし', '非該当', 'いいえ', 'no', 'false', 'NO', 'FALSE'}

YES_KEYWORDS = ['はい', 'うん', 'ええ', 'そう', 'あります', 'お願い', '希望',
                'する', 'します', 'いい', '良い']
NO_KEYWORDS  = ['いいえ', 'いえ', '違', '結構', 'ありません', 'いりません',
                'やめ', '不要', '無し', 'なし']
```

`'いい'` キーワードは `いいえ` から発火しないよう `text_has_yes()` 内で先に `いいえ`/`いえ` を除去してから判定。

6 バケット決定木:

```
OpenAI=NO_RESULT or other  → unclear
OpenAI=yes-family:
  text=yes only             → yes_confirmed
  text=no only              → disagree
  text=yes & no             → disagree
  text neither              → yes_openai_only
OpenAI=no-family:
  text=no only              → no_confirmed
  text=yes only             → disagree
  text=yes & no             → disagree
  text neither              → no_openai_only
```

## 辞書アップロード CSV の正確な仕様 (検証済 2026-05-22)

エンティティ管理画面のアップロード仕様:

- **2 列固定** `エンティティ名,類義語` (ヘッダー必須、完全一致)
- **1 行 1 エンティティ**。同一エンティティ名の重複行は 2 行目以降が無視される
- col 2 (類義語) 内に**複数類義語を packing する場合の区切り文字は `/` (スラッシュ)**
  - 半角スペース・セミコロン区切りは取り込み 0 件になる (検証済)
  - 列を 3 つ以上にして並べると col 2 だけ拾われる (検証済)
- 全フィールドを **二重引用符で囲む** (システムのエクスポート形式に準拠)
- 既存エンティティ名と一致する場合は **新 CSV で上書きされる** ので、既存類義語を残したい場合は事前にエクスポート + マージ
- 1 回最大 1000 行、ファイル 10MB 以下
- 句末 `。` は除去 (本 skill 内で自動)、中間 `。` は保持

例:

```csv
"エンティティ名","類義語"
"はい","はいそうです/はい/はい、そうです/そうです/..."
"いいえ","いいえ違います/いいえ/いいえ、違います/違います/..."
```

## 実行フロー

### Step 1: 月 → フォルダ ID 解決

引数の `YYYY-MM` を `YYYYMM_BrekekeLog` 形式に変換。親フォルダ配下を Drive MCP `search_files` で探す。

```
mcp__claude_ai_Google_Drive__search_files(
  query="parentId = '<parent_folder_id>'",
  pageSize=20
)
```

該当する `YYYYMM_BrekekeLog` フォルダ ID を取得。さらにその下の `01.本番` フォルダ ID を取得。

### Step 2: 日次 CSV 列挙 + ID 一覧化

```
mcp__claude_ai_Google_Drive__search_files(
  query="parentId = '<honban_folder_id>'",
  pageSize=100
)
```

戻り値が context overflow するので `tool-results/` に自動保存される。Python で読み直して 30 件の `(date, fileId)` ペアを得る。

### Step 3: subagent に download + parse + 生成を委譲 (推奨)

30 ファイル分の Drive MCP `download_file_content` 呼び出しは context を圧迫するので、`general-purpose` subagent に丸投げする。subagent プロンプトには以下を渡す:

- 30 件の `(date, fileId)` ペア
- 出力ディレクトリ: `C:/Users/hamaguchi.t/yes_no_analysis_<YYYYMM>/`
- `process.py` の絶対パス: `C:/Users/hamaguchi.t/voicebot-flow-builder/.claude/skills/extract-yesno-synonyms/process.py`
- 制約: pip install 禁止、stdlib のみ、他の Drive ファイル ID は触らない
- 期待出力: 200 語以内のレポート (バケット件数 / 上位 5 発話 / 出力パス)

### Step 4: 結果サマリを表示

subagent 戻り値からバケット件数と上位 5 発話を抽出してユーザーに表示。`entity_synonyms_final_slash.csv` のパスを最後に明記。

## 制約

- **pip install 禁止** (`~/.claude/CLAUDE.md` Package Install Policy)。Python 3.14.3 stdlib (`csv`, `re`, `base64`, `json`, `collections`, `os`, `glob`, `io`, `sys`) のみで完結
- **WebFetch / 他フォルダ参照禁止**。引数で渡されたフォルダ ID 配下のみ触る
- スクリプトの YES/NO ラベル定義・キーワードリストはハードコード (将来必要なら process.py を編集して拡張)
- 1 ファイル失敗時も残りで処理継続 (subagent 側で例外捕捉)
- 出力 CSV は UTF-8 BOM 付き (Excel 対応)、辞書アップロード CSV は UTF-8 BOM **無し** (システム側仕様要確認、現状 BOM 無しで成功)

## 他カテゴリへの拡張

「あり/なし」や「予約あり/予約なし」など別の binary classification を抽出したい場合:

1. `process.py` の `YES_LABELS` / `NO_LABELS` / `YES_KEYWORDS` / `NO_KEYWORDS` を編集
2. 出力 CSV の entity 名 (`はい` / `いいえ`) を該当エンティティ名に変更
3. それ以外のロジックはそのまま再利用可

## 関連 memory

- [[feedback-pip-install-forbidden]] — stdlib のみで実装
- [[reference-drjoy-es-fetch-strategy]] — Drive MCP 経由のデータ取得パターン
- [[project-collect-voice-quality-issues]] — 同系統の声品質ログ分析 skill (近接位置)
- [[feedback-drive-mcp-xlsx-path]] — Drive MCP base64 download パターン
