# AmiVoice STT 辞書 (SSoT)

このディレクトリは AmiVoice 音声認識用の `profile_words` 辞書を、**全カテゴリで単一の真実の源 (Single Source of Truth)** として管理する場所。

## ファイル一覧

| ファイル | カテゴリ | 用途 |
|---|---|---|
| `name.txt`            | 氏名（姓・名・カナ）| PatientName サブフロー、入電者氏名等 |
| `datetime.txt`        | 日付（月+日+相対表現）| 予約日・受診希望日等 |
| `time.txt`            | 時刻 | 午前/午後等 |
| `shinryoka.txt`       | 診療科 | 診療科聴取 |
| `kenshin.txt`         | 健診コース | 健診コース聴取 |
| `yoken.txt`           | 用件 | 用件聴取 (予約/変更/キャンセル等) |
| `yesno.txt`           | 肯定否定（一般）| 一般 Yes/No hearing |
| `echo_back_yesno.txt` | 復唱用 Yes/No | 復唱確認モジュール |
| `unknown.txt`         | わからない | 「わからない」回答パターン |
| `phone_number.txt`    | 電話番号 | 電話番号聴取の数字読み |

## フォーマット

```
表記 よみがな
表記 よみがな
```

- 1 行 1 エントリ、半角スペースで表記とよみがなを区切る
- 改行は `\n`（CRLF にしない）
- 空行・コメント行は不可（profile_words の raw 文字列がそのまま使われるため）
- 同一単語を複数のよみがなで登録可（AmiVoice が候補として使用）

## 編集ワークフロー

1. **辞書を編集**: 該当 `.txt` ファイルを `Edit` / `Write` ツールで直接編集（追加・修正・削除）
2. **派生ファイル再生成**:
   ```bash
   python3 scripts/build_dictionaries.py
   ```
   これで以下が更新される:
   - `docs/specs/stt_dictionary_templates.json` の各テンプレ `words` フィールド
   - `docs/reference/bivr/samples/json/氏名聴取.json` の `入力_患者_氏名.params.profile_words`
3. **動作確認** (任意):
   ```bash
   python3 scripts/build_dictionaries.py --dry-run
   ```
4. **コミット**: `.txt` と派生ファイル両方を一緒にコミット（drift 防止）

## 派生ファイル

派生ファイルは `build_dictionaries.py` が自動生成するため **直接編集しない**。

| 派生ファイル | 元の `.txt` |
|---|---|
| `docs/specs/stt_dictionary_templates.json` :: `templates.hearing_*.words` | 全 10 カテゴリ |
| `docs/specs/stt_dictionary_templates.json` :: `templates.hearing_name.words` | `name.txt` |
| `docs/specs/stt_dictionary_templates.json` :: `templates.echo_back_yesno.words` | `echo_back_yesno.txt` |
| `docs/reference/bivr/samples/json/氏名聴取.json` :: `入力_患者_氏名.params.profile_words` | `name.txt` |

## yaml からの参照

設計書 yaml の `amivoice_dictionary` セクションで `use_template` でテンプレ名を指定する:

```yaml
amivoice_dictionary:
  - step_name: "入電者氏名聴取"
    use_template: [hearing_name]
    additional_words: |
      （施設個別の追加語彙）
  - step_name: "受診希望日聴取"
    use_template: [hearing_datetime]
    additional_words: |
      早朝 そうちょう
```

scaffold_generator がテンプレ + additional_words を結合して `profile_words` を組み立てる。

## DOCX 辞書 (legacy)

`docs/reference/manuals/0_Amivoice辞書-*.zip` 内の DOCX ファイル群は **AmiVoice サーバ側登録用の人間向けドキュメント**で、ランタイムの STT には**使用されない**。

歴史的経緯で残しているが、今後は本 SSoT 側を編集する。AmiVoice サーバ登録が必要なタイミングで CSV / DOCX へのエクスポートを別途検討する（未実装）。

## 関連

- `docs/ai/amivoice_dictionary.md` -- AmiVoice 辞書の概念・運用ガイド
- `scripts/build_dictionaries.py` -- 派生ファイル再生成スクリプト
- `scripts/scaffold_generator.py:get_profile_words` -- yaml の use_template / additional_words を組み立てる本体
- `scripts/copy_subflows.py` -- subflow JSON サンプルを施設別 draft にコピー（profile_words はサンプル時点のものが入る）
