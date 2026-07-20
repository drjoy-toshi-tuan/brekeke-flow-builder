---
name: new-scenario
description: Pattern 1（新規作成）の定型フローを自動化。施設名とフロー名を引数に取り、customer_docs PDF を markitdown で MD 化 → Pattern 1 用軽量ノート起草 → /flow-draft で構造ドラフト壁打ち（block type / 分岐確認・人間承認必須）→ orchestrator 起動コマンド提示まで進める。Gen2/Gen1 からの移管ではなく、AI 電話設計書 PDF からの完全新規構築用。プロジェクトローカル skill。
---

# new-scenario — Pattern 1 新規作成 自動化 skill

## 起動時の引数

スペース or カンマ区切りで **施設名 と フロー名** の 2 つ。

例:
- `/new-scenario すずな皮ふ科 疑義照会`
- `/new-scenario ヘルスケアクリニック厚木 健診`
- `/new-scenario 中之島クリニック, 健診`

引数 0 個 → 「施設名とフロー名を教えてください」と聞く。
引数 1 個 → 「フロー名を教えてください」と聞く。
引数 3 個以上 → 最初の 2 つで進めるか確認。

## 命名規約（チェック必須）

- **半角スペース禁止**（memory: feedback_customer_docs_filename）
- **括弧 `(1)` 禁止**
- **施設名・フロー名のいずれにも `_` を含めない**（orchestrator extract_names() が `_` で分割するため）
- **group_name (`{施設名}_{flow名}`) の URL エンコード後 255 文字以内**（memory: feedback_group_name_url_length_limit。漢字 19 字目安、日付サフィックス前提）
- 既存 `output/scenarios/{施設名}_{flow名}/` が無いことを確認（既存なら上書き or 別 flow 名へ変更）

## 実行フロー（上から順に）

### ステップ1: 引数パース & 命名規約チェック

- 施設名・フロー名を取り出す
- 上記命名規約に違反していたら **即停止してユーザーに修正案を提示**
- ターゲットパス算出:
  - `customer_doc_dir = docs/reference/customer_docs/`
  - `raw_md = {customer_doc_dir}/{施設名}_{フロー名}_raw.md`
  - `note_md = docs/migration/{施設名}_{フロー名}.md`
  - `scenario_dir = output/scenarios/{施設名}_{フロー名}/`

### ステップ2: customer_doc の特定

`docs/reference/customer_docs/` 配下を fuzzy match で施設名にマッチする PDF/MD を探す:

- マッチ複数 → **表で候補一覧を提示してユーザー選択**
- マッチなし → 「customer_doc が見つかりません。docs/reference/customer_docs/ に配置してください」と停止
- マッチ単一 → そのファイルを採用

**fuzzy 例**:
- 候補=「すずな皮ふ科」→ 「すずな皮ふ科クリニック様_AI電話設計書・定例資料_.pdf」でヒット
- 候補=「ヘルスケアクリニック厚木」→ 「【要件定義】ヘルスケアクリニック厚木御中.pdf」でヒット

PDF と MD の両方が見つかった場合は **MD を優先**（既に人間が整形済みのケース）。

### ステップ3: PDF を markitdown で MD 化

**前提**: マシンに `markitdown` (Python パッケージ) がインストール済み。`python -c "import markitdown"` で確認できる。

- 既存 `{raw_md}` が存在 → 再利用（上書き確認は不要）
- 存在しない & customer_doc が PDF → markitdown で変換:

```bash
python -c "
import sys
sys.stdout.reconfigure(encoding='utf-8')
from markitdown import MarkItDown
md = MarkItDown()
result = md.convert(r'{customer_doc_path}')
with open(r'{raw_md}', 'w', encoding='utf-8') as f:
    f.write(result.text_content)
print('OK:', len(result.text_content.splitlines()), 'lines')
"
```

- customer_doc が MD → そのまま元資料として参照（`{raw_md}` は作らない）
- 変換失敗（pdfminer 例外・FontBBox 警告以外の致命エラー）→ ユーザーに報告して停止

**警告**: PowerPoint 系 PDF は表組みが崩れることが多い。raw.md の質に保証はないので、director には raw.md + 元 PDF の両方を読ませる前提でノートを書く（feedback_director_must_read_source_doc）。

### ステップ4: 既存ノートの確認

`{note_md}` が既にあるかチェック:

- 存在する → 「既にあります。上書き / スキップ / やめる」をユーザーに選択させる
- 存在しない → ステップ5 へ

### ステップ5: Pattern 1 軽量ノート起草

**原則: ノートは director に渡す「付箋」であり、「指示書」ではない**。director 自身が customer_doc を読んで Gen3 設計（ブロック選定、TTS 抽出等）を行えるので、**director がすでに知っている情報は書かない**。

`Agent` ツール（subagent_type=general-purpose、isolation=worktree は不要）を 1 つ起動。プロンプトには以下を必ず含める:

- **作業制約（絶対）**: ファイル書き込み・git 操作・スクリプト実行は一切禁止。read-only で内容テキストだけ返す
- **入力**:
  - customer_doc path（PDF or MD）
  - raw.md path（PDF を MD 化したもの。MD ソースのときは省略）
  - 施設名 / フロー名
  - 今日の日付
- **出力スコープ**: Pattern 1 用軽量ノート（30〜80 行、目安 50 行前後）
- **必須セクション**:
  1. ヘッダーコメント（HTML 形式 `<!-- ... -->`）。必須キー:
     - `施設: {施設名}`
     - `シナリオ: {フロー名}`
     - `環境: demo`
     - `元資料: docs/reference/customer_docs/{raw.md or 元 MD path}`
     - `補足元資料: docs/reference/customer_docs/{元 PDF path}`（PDF があれば）
     - `参考シナリオ:`（あれば既存 `output/scenarios/...` パスを 1 行で。ない場合は省略可）
     - `作成日: {YYYY-MM-DD}`
     - `作成者: hamaguchi`
     - `備考:`（Pattern 1 / 特殊事情があれば 1-2 行）
     - **元資料パスは必ずバッククォート無し**（orchestrator 内部処理の regex 要件）
  2. `### シナリオ概要` — 1〜2 文。誰が誰に何を問い合わせる電話か（director が customer_doc 1 周読んだだけでは取りこぼしやすい高レベル文脈）
  3. `### 設計方針` — フロー設計の高レベル判断:
     - 1flow / multiflow（subflow 分割の要否）
     - 入電者の種別（患者本人 / 家族 / 薬局 / 他施設等）と、それに伴う標準サブフロー（PatientName/Phone/MedicalCard/DateOfBirth）の使用可否
     - 用件分岐方式（Pattern A: OpenAI 直後 / Pattern B: 後段 ContextMatchRouter）の判断材料
     - 受付時間判定の分岐方式（acceptance_times による opening 自動判定で十分か、追加 script ブロックが必要か）
  4. `### 施設固有の特殊ルール` — customer_doc から読み取った非自明なルール（例: 特定診療科の受付終了、時間帯別の分岐、SMS 文言条件、登録番号マッチ等）
  5. `### director が見落としやすいポイント` — raw.md の表崩れ箇所、元 PDF にしかない図表情報、推測禁止項目（status 番号・SMS 文面・非通知時の挙動 等は不明なら BLOCKER 行きを明示）
  6. `### 詳細は元資料を参照` — customer_doc / raw.md / 参考シナリオへの参照パス（バッククォート無し）

- **書かないこと（director が直接 customer_doc から抽出する）**:
  - フロー設計の全体 ASCII ツリー（director が `flow_diagrams` で起草）
  - 全聴取項目テーブル（director がアナウンス一覧から拾う）
  - 全 TTS 文言原文転記（特殊ルールに関わる文言のみ引用）
  - 終話パターン全件（director が `termination_patterns` で定義）
  - 列挙系（診療科リスト・薬局リスト・コースリスト等の全件転記禁止）

- **書き方のポイント**:
  - Gen3 語彙を使う（「scenario_flow ブロック」「ContextMatchRouter」「subflow」「hearing/announcement/opening」等）
  - URL・Google Sheets リンク・ヒアリングシートは無視（memory: feedback_gen2_customer_doc_priority に準ずる方針）
  - PDF の改訂履歴（更新日：x/y）に該当する変更点があれば「設計方針」または「施設固有の特殊ルール」に反映
  - 判断に迷う箇所は「director 判断」と明記して委ねる
  - 不明な数値（status 番号・SMS 文字数等）は推測せず「確認レポートで BLOCKER 化」を指示

- **返答フォーマット**: `---BEGIN---` と `---END---` の間に軽量ノート markdown 全文

### ステップ6: ファイル書き出し

エージェントの `---BEGIN---` / `---END---` 間のテキストを抽出して:
1. HTML エスケープされた `&lt;` `&gt;` を `<` `>` に unescape
2. `{note_md}` に Write

### ステップ6.5: /flow-draft による構造ドラフト壁打ち（必須・HITL）

> **⚠️ ここで必ず人間確認を取る。確認なしに orchestrator を起動してはならない。**

軽量ノート（ステップ5）を書き終えた後、**director を呼ぶ前に** `/flow-draft` で構造ドラフトを作成し、
人間と壁打ちで block type・分岐先を確定する。

```
/flow-draft {施設名} {フロー名}
```

壁打ちで確認すること:
- 各 step の block type が正しいか（date_of_call_classifier は廃止・使用不可）
- N択 enum hearing に `choices:` の宣言があるか（ない → n_choice 化されず OpenAI のまま）
- polar hearing（はい/いいえ系）は自動で yes_no_classifier になる（choices: 不要）
- 分岐の抜け・漏れがないか（`match: other` の行き先含む）
- サブフロー（FAQ / 用件等）の Jump to Flow が必要か

**人間が「OK」を出してから次のステップへ進む**。修正が必要なら流-draft の結果を踏まえてノートを更新し、director への指示に反映する。

### ステップ7: orchestrator 起動コマンド提示

ユーザーに **P1 と P1+1 の両方** を選択肢として提示する:

**P1（標準・Opus）** — director が customer_doc 全量を読んで YAML を一から生成。品質は高いがトークン消費大（Opus 20〜40k tokens 程度）。

```bash
cd ~/voicebot-flow-builder
python3 scripts/orchestrator.py --pattern 1 \
  --spec docs/migration/{施設名}_{フロー名}.md \
  --assignee hamaguchi --env demo
```

**P1+1（トークン節約版・Sonnet）** — /flow-draft の MD 表から決定論スケルトンを生成し、Sonnet が TTS 文言等の「文言系」のみを埋める。Opus 呼び出し不要でトークン消費が少ない。flow-draft 壁打ちで構造が確定している前提。

> **前提条件**: /flow-draft の出力を `output/scenarios/{施設名}_{フロー名}/flow_draft_YYYYMMDD.md` として保存しておくこと。

```bash
cd ~/voicebot-flow-builder
python3 scripts/orchestrator.py --pattern 11 \
  --spec docs/migration/{施設名}_{フロー名}.md \
  --assignee hamaguchi --env demo
```

> P1+1 では `--spec` はオプション（顧客資料パスを Sonnet に渡すために使用）。
> flow_draft MD は `output/scenarios/{施設名}_{フロー名}/` 内を自動検索する。

**所要時間目安（P1）**: director 10〜20 分 + 全工程 30〜60 分。途中失敗時は `--resume` で再開可能。
**所要時間目安（P1+1）**: スケルトン生成 1 分 + Sonnet 補完 3〜5 分 + 全工程 15〜30 分。

### ステップ8: ユーザー確認で自動起動（オプション）

ユーザーが「そのまま起動して」「実行して」等を明示した場合のみ、Bash ツールで orchestrator を起動する。明示されない場合は **コマンド提示で停止**。

未指定時は提示まで。

## 依存する memory（起動時の前提）

- `feedback_customer_docs_filename` — ファイル名規約（スペース/括弧禁止、`元資料:` パスはバッククォート無し）
- `feedback_director_must_read_source_doc` — ノートだけで director に起草させない、必ず元資料も読ませる
- `feedback_slot_gen3_default` — 新規作成は Gen 3 slot型（`type: slot`）が既定。氏名=`slot: patient_name`/生年月日=`slot: date_of_birth`/電話=`slot: phone`/診察券=`slot: card_number`。RAG/FAQのみ subflow。Gen2/Gen1移管・明示指定時のみ `type: subflow`
- `feedback_brekeke_catchall_pattern` — incoming-classifier の catch-all は `^*$`
- `feedback_tts_ai_no_ssml` — `{tts_g:...}` 小文字、SSML 禁止
- `feedback_opening_block_composition` — 冒頭 = opening + 冒頭_アナウンス の 2 ブロック 1 セット必須
- `feedback_group_name_url_length_limit` — group_name は URL エンコード 255 文字制限
- `feedback_platform_flags_framework` — 施設単位 / モジュール単位の 2 軸を分離
- `feedback_add_current_date_scaffold_decision` — addCurrentDate は scaffold 判定（director/prompter は触らない）
- `feedback_png_misread` — PNG/PDF 表崩れによる架空ステップ生成リスク → director に確認レポート BLOCKER 化を促す

## エラー処理

- 施設名が customer_doc にマッチしない → 候補リスト表示 → ユーザー選択 or 中断
- markitdown が import エラー → 「markitdown が見つかりません」と停止（インストール禁止ルール）
- PDF が壊れていて変換失敗 → ユーザーに報告、別 PDF 提供 or 手動 MD 化を依頼
- raw.md が空 or 数行しかない → 警告（白紙スキャン PDF の疑い）
- `{note_md}` が既存 → 上書き / スキップ / 中止を選択
- `output/scenarios/{施設名}_{flow}/` が既存 → 警告（別 flow 名 or 既存削除を確認）
- サブエージェントが `---BEGIN---` / `---END---` を返さない → 再実行（最大 1 回）、それでもダメなら人間に切替

## このスキルのスコープ外

- Pattern 2（既存修正）対応 → 別 skill 予定（将来 `fix-scenario` として分離）
- Pattern 3/4（Gen2/Gen1 移管）→ `migrate-gen2` skill / 過去 `migrate-gen1` skill（アーカイブ済）
- orchestrator 起動の完全自動化 → コマンド提示まで（ユーザー判断で起動）
- raw.md の人間レビュー / 修正 → skill ではやらない。必要なら人間が編集してから skill 再起動
- PR 作成 → orchestrator 完走後の最終ステップで人間が実施

## ノート品質の curation について

このノートテンプレートは **director の起草失敗を観察して育てる前提**で、初期版は意図的にミニマル。
今後 director が躓いたパターンが見つかったら、**`### director が見落としやすいポイント` セクションに具体的な注意項目を追加**していく。
逆に「ここまで書かなくても director が拾える」と分かった項目は削る。

**curation の作業ガイド**: 過去施設で director が確認レポートに BLOCKER として上げた頻出項目、または fixer が同一パターンで何度も修正している項目は、テンプレートに「director が見落としやすいポイント」のフォーマット例として追加する。逆に、書かれていても director が customer_doc から正しく拾えていた項目は削除候補。

## 撤去方法

Pattern 1 新規作成業務が定常化して skill 不要になった場合:
```bash
rm -rf .claude/skills/new-scenario
```

ただし Pattern 1 は今後も継続発生する想定なので、`migrate-gen2`（Gen2→Gen3 期間限定）のような撤去予定はない。
