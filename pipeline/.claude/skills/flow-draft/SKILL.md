---
name: flow-draft
description: director を呼ぶ前に「どの step でどの block type を使い、どこへ分岐するか」だけを抜き出した軽量MD表（構造ドラフト）を作成し、人間と壁打ちで確定する。customer_docs（pptx/MD優先、PDFは抽出精度に注意）とユーザーのテキスト説明の両方を入力に取れる。TTS文言の逐語チェックはこのskillの対象外（別途 properties 生成後に原資料と照合する）。プロジェクトローカル skill。
---

# flow-draft — シナリオ構造ドラフト（director 前の壁打ちチェックポイント）

## 目的

director は customer_doc を読んで「ブロック選定・分岐設計・YAML化」を一度にやってしまうため、
**構造（どの step / どの block type / どこへ分岐）の間違いが、詳細まで書き終わった YAML に埋もれて発見される**。
発見が遅れるほど手直しコストが上がる（YAML 全体の再検討 → JSON 再生成 → プロパティ再生成…）。

このスキルは、director を呼ぶ**前**に「構造だけ」を抜き出した簡易 MD 表を作り、
人間がその場で「このステップの block type おかしくない？」「この分岐、抜けてない？」を
数分で確認できるようにする。**TTS文言の一字一句や profile_words 等の細部はここでは書かない**
（表が肥大化して見づらくなる＆director がやる仕事を先取りしてしまう）。

## 起動時の入力

以下の**いずれか、または両方**を受け付ける（両方あれば両方使う）:

1. **施設名 + フロー名**（例: `/flow-draft すずな皮ふ科 疑義照会`）— `docs/reference/customer_docs/` を
   fuzzy match で検索する（`new-scenario` skill のステップ2と同じロジック）。
2. **その場で貼られたテキスト説明**（例: `/flow-draft` の後にユーザーが用件・分岐を口頭で書いた文章）。

### customer_doc の優先順位（重要）

- **MD（人間が整形済み）> PPTX > PDF**。
- PDF しかない場合は markitdown で変換するが、**表組み・矢印・フローチャート画像は崩れやすい**
  （`new-scenario` skill の "PowerPoint 系 PDF は表組みが崩れる" 警告と同じ問題）。
  PDF 由来の情報だけで作った行には **必ず「⚠️ PDF崩れの可能性」を メモ欄に書く**。
  可能なら「元資料の該当ページ番号」もメモ欄に記録し、人間が原本と見比べやすくする。
- PPTX/MD がある場合は PDF より優先して使う。PDF と PPTX/MD が両方あれば **PPTX/MD を正**とする。

### テキスト説明との統合

- ユーザーが口頭/テキストで補足した内容は、customer_doc から読み取った内容と**矛盾する場合は
  ユーザーの発言を優先**（客先資料が古い・不正確な可能性があるため）。
- 矛盾を検知したら黙って上書きせず、「資料には○○とありますが、ご説明では△△でした。どちらを採用しますか」
  と確認する。

## 出力: 構造ドラフト表

以下の形式で **1 つの MD** を出力する（ファイルには書かず、まずチャットに表示して壁打ちする）。

```markdown
# flow-draft: {施設名}_{フロー名}

## ステップ一覧

| # | step（日本語） | block type | 条件 → next | メモ |
|---|---|---|---|---|
| 1 | 冒頭 | opening | → 冒頭_アナウンス | |
| 2 | 冒頭_アナウンス | announcement | → 用件確認 | |
| 3 | 用件確認 | hearing (enum) | 予約→氏名聴取 / 変更→氏名聴取 / キャンセル→氏名聴取 / other→END_不明用件 | DTMF+音声。要確認: "other"の受け皿が資料に無い |
| 4 | 氏名聴取 | slot: patient_name | → 生年月日聴取 | 個人情報4種はGen3既定でslot直書き（モジュール選定ガイド§3.1.1） |
| 5 | 診療科確認 | script (A: script_template: department_classifier) ⚠️ | → 予約日確認 | 要確認: department正規化は4方式あり、どれを使うか確定が必要（Script系詳細早見表 参照） |
| 6 | 選定療養費同意確認 | script (A: script_template: yes_no_classifier) | はい→予約確定 / いいえ→END_同意なし | |
| ... | | | | |

## 分岐の網羅性チェック（漏れ探し用）

各 hearing / context_match_router について、明示した分岐 + catch-all("other"/"default") が
揃っているかを1行で確認する:

| step | 明示分岐 | catch-all あり? |
|---|---|---|
| 用件確認 | 予約/変更/キャンセル | ✅ other → END_不明用件 |
| チェック_診療科 | 未取得/取得済 | ✅（2値で網羅） |

## 要確認（人間の判断が必要）

- {block type の選択に迷った箇所、資料に記載がなく推測が必要な箇所を列挙}
```

### block type 早見表（実装済み全26種・2026-07-10 時点）

> **注意**: `CLAUDE.md` は「9ブロック型＋augment＝計10種」と書いているが、これは古い記述で
> 実際の allowlist（`schemas/qa_validator.py` の `KNOWN_BLOCK_TYPES` / `scripts/scaffold_generator.py`
> のディスパッチ）は既に **26種**まで増えている（2026-05〜07 に段階的追加）。このスキルは
> **実装済みの26種を正**として案内する（CLAUDE.md 側の更新は別件・要相談）。

**フロー骨格（必須系）**

| block type | 使う場面 |
|---|---|
| `opening` | フロー冒頭固定（wait+コンテキスト設定+着信分類）。必ず先頭 |
| `announcement` | 一方向のTTSアナウンスのみ（聞き返しなし） |
| `termination` | 終話（切断） |
| `call_transfer` | 有人転送 |
| ~~`date_of_call_classifier`~~ | **廃止（2026-07-13）。使用不可。時間帯・曜日分岐は `script` (script_template: custom) を使うこと** |

**聴取・分岐の基本形**

| block type | 使う場面 |
|---|---|
| `hearing` | 音声/DTMFで聴取して分岐・保存する（output_format: text/enum/datetime） |
| `context_match_router` | 既に確定した値（他モジュールの結果）で分岐するだけ。聴取はしない |
| `cmr_chain` | CMRは2択(YES/NO)しか出せないため、3値以上の分岐をCMRを直列に並べて表現する（Pattern C後段） |
| `null_check` | 値がnull/空文字/空配列かどうかだけで2分岐（WebRTC事前入力フォーム対応） |
| `script` | 決定論ロジックが必要な箇所。**具体的にどの script/template を使うかは下記「Script系 詳細早見表」で必ず確定させる**（「script」だけで済ませない） |
| `free_text` | 自由発話を **Scripts で正規化して保存**（全角→半角・スペース/句読点除去。OpenAI 不使用）。TTS→STT→Script(正規化)→save2db→next |
| 希望日・希望時期聴取 | `hearing` (output_format: text) + OpenAI（`docs/ai/skills/SKILL_希望日.md` の**固定プロンプトそのまま使用**。施設固有修正禁止） |
| `augment` | 上記のどれにも当てはまらない場合の暫定枠。**WARNING扱い・人間レビュー必須**。多用は設計見直しのサイン |

**個人情報4種（新規作成は `slot` が既定）**

| block type | 使う場面 |
|---|---|
| `slot` | 個人情報4種の決定論インライン展開。`slot: patient_name` / `date_of_birth` / `phone` / `card_number` |
| `patient_name` / `dob` / `phone` | `slot`のファーストクラスエイリアス（`type: patient_name` と書けば `type: slot, slot: patient_name` と同じ）。`dob`→date_of_birthスロットに対応 |
| `card_number` | 診察券番号正規化（TTS→STT→Script正規化→任意で復唱→Retry）。単独でも`slot`経由でも同じロジック |
| `subflow` | 個人情報4種を旧来のJump to Flowで呼ぶ場合（Gen2/Gen1移管や明示指定時のみ）、またはFAQ family・用件聴取のように複数箇所で共有するサブフロー |

**着信・電話番号系**

| block type | 使う場面 |
|---|---|
| `incoming_category_classifier` | 電話帳マッチによる送信元分類 |
| `phone2name` | 電話番号→氏名変換（found/not_found テンプレート分岐） |
| `phone_branch` | Module Result Binderで`<%additionalPhoneNumber%>`をregex分岐（携帯/固定など） |

**診療科系**

| block type | 使う場面 |
|---|---|
| `clinical_department` | 診療科名を聴取→正規化スクリプト(kamei_normalize)→分岐→Retry |
| `clinical_department_normalize` | 正規化のみ（TTSなし・リトライなし版） |
| `clinical_department_classifier` | Custom Module版の診療科分類（プロパティ駆動・同義語辞書内蔵） |

**用件・FAQ系**

| block type | 使う場面 |
|---|---|
| `intent` | 用件判定スクリプト（TTS→STT→Script(intent_classifier)→分岐）。**youken(script_blocks)と同じ概念で実装が別。要確認対象** |
| `faq` | FAQ照合（TTS→STT→Script/OpenAI照合→分岐）。**script_blocksのfaqとも別実装。要確認対象** |

> **迷ったら augment にせず、まず `docs/brekeke/モジュール選定ガイド_v2.md` を見る。**
> このスキルの表と`docs/brekeke/`の内容が食い違う場合は、**より新しい方（追加日が新しい方）を優先**し、
> 「要確認」に矛盾を書いて人間に判断を委ねる。

### Script系 詳細早見表（37の入口・重複/孤立あり・2026-07-10 調査）

> **重要**: 「script」「intent」「faq」「clinical_department」等、Script系の block type を選ぶ際は、
> **どの入口（下表のA/B/C/Dのどれ）を使うかをドラフト表の block type 列に明記し、必ず人間に確認する**。
> 「script」だけで済ませて先に進んではならない（同じ概念に複数の実装が並存しており、選び間違えると
> 後で認定ゲート・oracleの対象部品が変わってしまう）。

**A. `type: script, script_template: <名前>`（17種・最も直接的な入口）**

| 分類 | template名 | 備考 |
|---|---|---|
| 認定正本（modules/から byte-exact読込・oracle/hashゲート対象） | `checkup_intent_classifier` `checkup_course_classifier` `checkup_menu_classifier` `yes_no_classifier` `reservation_date_classifier` | 最も信頼できる。迷ったらここから選ぶ |
| `docs/brekeke/script_templates/` 由来（予備。最新の認定版と一致しているか保証なし） | `business_hour_classifier` `business_hours` `condition_group` `current_appointment_date` `day_of_week` `department_classifier`⚠️ `desired_date_precompute` `future_date` `inquiry_classifier`⚠️ `n_choice`⚠️ `phone_type` `shinjuku_kenshin_date_gate` | ⚠️3つは`modules/`内の同名認定版と**内容が異なる**ことを確認済み（コード内コメントに"n_choiceで既に発生"と明記）。選ぶ前に「要確認」に上げる |
| — | `custom` | テンプレートではなく `// TODO_script` の手書き枠 |

**B. block type 専用の自前実装（`script_template`を経由しない）**

| block type | 使うscript | 備考 |
|---|---|---|
| `intent` | 自前 `_build_intent_script_body`（`modules/inquiry_classifier`とは**別物**） | |
| `faq`（method: script） | 自前生成 | method: openai も選べる（OpenAI併用） |
| `clinical_department` / `clinical_department_normalize` | 自前 `kamei_normalize`（施設ごとの科リストから都度生成） | |
| `clinical_department_classifier` | Custom Module（`@General$Script`ではない別モジュール種別） | |
| `card_number` | 自前の正規化Script | |
| `phone_branch` | Module Result Binder（`@General$Script`ではない） | |
| `null_check` / `cmr_chain` | 専用ロジック（分類器ではなく分岐専用） | |

**C. `script_blocks:`（scaffold後にgen_scripts.pyが後付けで埋め込む・A/Bと完全に独立）**

| script_blocks type | 対応する概念 | 備考 |
|---|---|---|
| `youken` | 用件判定 | **`intent`(B)と概念重複・実装は別** |
| `faq` | FAQ照合 | **`faq`(B)と概念重複・`faq_map`記法が別** |
| `department` | 診療科 | **`department_classifier`(A)・`clinical_department*`(B)と概念重複＝診療科だけで4つ目の実装** |
| `enum_classifier` | 汎用N択分類 | `docs/amivoice/keyword_presets.yaml` のpresetを使う |

**D. `modules/`に認定部品が存在するが、A/B/Cのどこからも呼ばれていない（孤立）**

| module | 状態 |
|---|---|
| `checkup_option_classifier` | 未接続 |
| `faq_exact_match` | 未接続 |
| `faq_matcher` | 個別シナリオ（横断FAQ方式）で手動埋め込みのみ。汎用入口なし |
| `ambiguity_gate` | 未接続 |
| `session_object_probe` | 診断用ツールで分類器ではない可能性 |
| `phone_normalizer` | `slot: phone`の実体は別のBrekeke純正モジュール（`drjoy^TS Custom Module$Phone Normalization`）。このファイルは使われていない |
| `dob_normalizer` / `dob_reconfirmation` | `slot: date_of_birth`が別経路で直接読む（`script_template`経由ではない） |

**このスキルでの運用方針**:
1. ドラフト表で block type が script系になったら、**メモ欄に「A/B/C/Dのどれ・具体的な名前」を必ず書く**
   （例:「script (A: script_template: yes_no_classifier)」「intent (B)」「youken (C: script_blocks)」）。
2. **重複がある概念**（用件判定=intent/youken、FAQ=faq(B)/faq(C)、診療科=4種）に該当したら、
   その場で人間に選択肢を提示して確認する。黙って1つを選ばない。
3. **孤立モジュール（D）を新規に使いたい場合**は、まだ配線されていない旨を伝え、
   「scaffold_generator.py側の対応が別途必要」と明記して「要確認」に上げる（このスキルではコードを書かない）。

## 壁打ちの進め方

1. 上記フォーマットで表を**チャットに直接表示**する（ファイルにはまだ書かない）。
2. ユーザーの指摘を反映して表を更新する。この往復を収束するまで繰り返す（下記「表の修正ルール」参照）。
3. ユーザーが「これで確定」と言ったら、`output/scenarios/{施設名}_{フロー名}/flow_draft_{施設名}_{フロー名}.md`
   に書き出す（自由ゾーン）。
4. 書き出し後、`/new-scenario` または director への引き渡しを提示する。
   **この確定済み表は director への「付箋」に、構造情報（block type・分岐）を追加したものとして渡せる**
   （`new-scenario` skill のステップ5「軽量ノート起草」に構造ドラフトを添付する形。ノート本文自体は書き換えない）。

### 表の修正ルール（ユーザーが指摘 → Claude が正しく反映するための手順）

**ユーザー側の指摘方法（推奨・どれでもOK、複数指摘も1メッセージでまとめてよい）**:
- 行番号 or step名 を必ず含める。例:「#3 用件確認、block typeがhearingじゃなくintentのはず」
  「氏名聴取の後、生年月日聴取に行く前に本人確認を1個挟みたい」
- 表自体を直接編集して貼り返してもよい（Claude側は差分を検出して反映する）。
- 「この資料のp.5にある通り」等、根拠（資料のページ/スライド番号）を付けると精度が上がる。

**Claude側の反映ルール（必須・省略しない）**:
1. **指摘対象の行/挿入位置が曖昧なときは、絶対に推測で直さず先に聞き返す**
   （例:「『生年月日のところ』とは #4 氏名聴取 と #5 生年月日聴取 のどちらですか？」）。
2. 反映したら **表全体を毎回まるごと再掲する**（差分だけの説明文で済ませない — 見た目で確認できないと
   誤解が蓄積する）。
3. 再掲した表の直後に **「変更点」を箇条書きで明示**する（例: 「#3 block type: hearing → intent」
   「#4.5 として『本人確認』(context_match_router) を新規挿入、氏名聴取の next を変更」）。
   これにより、ユーザーは "変更点" の1〜2行だけ読めば意図通りか即判定できる。
4. 1つの指摘が複数行に影響する場合（例: 分岐先を変えたら他のstepのnext番号もズレる）は、
   影響範囲を「変更点」に全て列挙する。省略して後から矛盾が発覚するのを避ける。
5. ユーザーの指摘が既存の block type早見表と矛盾する場合（例: 個人情報を`subflow`で明示指定したいのに
   理由が書かれていない）は、黙って従うか黙って拒否するかの二択にせず、**一度だけ確認を挟む**
   （「新規作成なのでslot推奨ですが、subflowにする理由があれば教えてください。無ければslotのままにします」）。
   確認後はユーザーの回答に従う（二度目は聞き直さない）。

## このスキルのスコープ外

- **TTS文言の逐語チェック**（発話文言は原資料と100%一致が必須）は別工程 → `tts-doc-check` skill。
  `properties_*.md` 生成後に元資料（PPTX優先。PDFは抽出精度に注意）と1行ずつ照合する。
  このskillでは「発話の要旨（何を聞くか）」だけをメモ欄に書き、文言そのものは書かない。
- 設計書 YAML の実際の書き起こし（director の仕事）。
- 保護ゾーンのファイル編集（`scripts/` `schemas/` `tools/` 等）。

## エラー処理

- customer_doc が見つからない & テキスト説明もない → 「資料またはご説明のどちらかが必要です」と停止
- PDF しか無く markitdown 変換が崩れて構造が読み取れない → 崩れた箇所を明示し、
  「この部分は元のPPTX/画像を見せていただけますか」とユーザーに確認
- 分岐の catch-all が資料に明記されていない → 推測せず「要確認」に列挙する（黙って other を仮置きしない）
