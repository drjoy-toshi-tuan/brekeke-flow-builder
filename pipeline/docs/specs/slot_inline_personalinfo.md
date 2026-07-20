# slot: 宣言的個人情報の決定論インライン展開（プロトタイプ）

ブランチ `proto/flat-inline-personalinfo` のプロトタイプ仕様。設計書 YAML の `type: slot`
ブロックを、Jump to Flow サブフローも OpenAI も使わず、**認定済み決定論部品だけ**でインラインの
ノード鎖に展開する。部品選択はヒューリスティック推論をせず **FIXED EXPLICIT MAPPING**（"scaffold 決定"）。

実装: `scripts/scaffold_generator.py`
- 部品ビルダー: `build_yes_no_script` / `build_dob_reconfirmation` / `build_phone_type_script`
- 展開器: `_build_slot()`（dispatch から `elif btype == "slot":` で呼ぶ）
- pre-pass: `step_to_entry` に `slot` 分岐（phone は incoming-classifier、他は TTS が entry）

## FIXED MAPPING TABLE

### `slot: patient_name`
```
TTS → STT(氏名カナ) → save2db(patientName)
```
- 復唱なし。OpenAI なし。STT success → 次ステップへ直結（氏名カナはそのまま context 保存）。

### `slot: date_of_birth`
```
TTS → STT/DTMF → DOB Re-confirmation(決定論正規化 + #data# 復唱) → STT(はい/いいえ)
    → yes_no_classifier → 肯定: next / 否定: TTS へ loop / NO_RESULT: 確認 retry
```
- DOB ノード: `drjoy^TS Custom Module$DOB Re-confirmation`（本番 厚木 統合CC と同 type）。
  params = `{module, dateReadingMode, saveDOB2db, prompt, openAI_prompt}`。
  `openAI_prompt` には決定論パーサ本文（`~/Downloads/_dob_bivr/module_value.js`）を埋め込む。
  名前は本番踏襲だが **OpenAI は呼ばない**（中身は純ローカルの和暦/西暦/DTMF パーサ）。
- next: `^TIMEOUT$`/`^ERROR$` → retry, `^INVALID$` → 再入力(TTS), `^.*$`(success) → 確認 STT。
- TZ 固定: `module_value.js` は無引数 `new Date()` で「現在年/今日」を取り 120 年超/未来日を判定する。
  Nashorn には Intl が無いため `_pin_dob_tz()` が UTC+9h の `__jstNow()` ヘルパに置換して JST 固定する。

### `slot: phone`
```
incoming-classifier
  ├─ 携帯 → phone_type(ANI=着信電話番号分類 を入力) → next        # ANI 既知ゆえ番号聴取不要
  └─ 固定/海外/非通知/その他/WebRTC → TTS(番号聴取) → STT → 正規化復唱
        → STT(はい/いいえ) → yes_no_classifier
        → 肯定: phone_type / 否定: TTS へ loop / NO_RESULT: retry
     phone_type(携帯/固定/その他) → next
```
- `phone_type`: `@General$Script`。`docs/brekeke/script_templates/phone_type.js` 由来だが
  **050 = その他**（本番 `script_携帯判別` 準拠。テンプレの 050=携帯 を上書き）。
- 後段の context_match_router が `phone_type` の module-result（携帯/固定/その他）で分岐できるよう
  setResult する。最小プロトでは phone_type の next を直接 3 値分岐させている。

## 制約（CLAUDE.md / memory 由来）

- モジュール間の値受け渡しは **module-result + getModuleResult / ContextMatchRouter**。
  `<%key%>`（resolver store）はスクリプトから書けないため使わない。
- **context 名は ASCII**（saveContextModel2DB が日本語 contextName でこける）。モジュール名は日本語可。
- save2db / retry / REACH / LAYOUT 規約は hearing 経路と同一 builder を流用。
- yes_no_classifier は認定正本 `modules/yes_no_classifier/script.js`（@part-id / engine v2）を
  wiring 変数 `__SOURCE_MODULE__` のみ差し替えて注入。**spec 行は一切触らない**（1 文字改変で再受入）。

## `output_format: enum` → `type: script` (n_choice / checkup_*) のマッピング（document-only・未実装）

slot 以外の「列挙値を返す聴取」は本プロトの対象外だが、同じ決定論方針で以下のように展開する想定。
- 設計書 hearing ブロックに `output_format: enum` + `conditions:` がある場合、現状は OpenAI 分類器を生成する。
- 決定論化する場合は `type: script` + `script_template: n_choice`（または `checkup_intent_classifier` /
  `checkup_course_classifier` / `checkup_menu_classifier`）に置換し、認定済み Script が
  STT module-result を列挙ラベルに分類 → ContextMatchRouter で分岐する。
- いずれも `modules/certified_hashes.json` に登録済みの認定部品（`n_choice` v4 / `checkup_*` v2）。
- slot 化はしない（slot は氏名/DOB/電話の 3 種のみ。enum は script ブロックの守備範囲）。

## 既知の制約 / フォローアップ（full delivery で必要）

1. **qa_validator allowlist**: `schemas/qa_validator.py:1121 KNOWN_BLOCK_TYPES` に `slot` が無いため
   F-3 CRITICAL になる。full delivery では `slot` を追加し、`F-4`/`I-1`（hearing step_details 紐付け）
   の slot 版整合チェックも足す必要がある。本プロトでは保護ゾーンのため未パッチ（scaffold dispatch は対応済み）。
2. **DOB ノードの認定**: `drjoy^TS Custom Module$DOB Re-confirmation` は `@General$Script` ではなく
   getProperty/$ivr.play/$ivr.exec を使う値スクリプト。`modules/dob_*` 認定フォルダが未収容
   （`modules/README.md` に「TODO: リポジトリへ収容」）。P6 ハッシュゲート（engine/spec 二段）の
   対象外なので、full delivery では oracle.py/test_oracle.py/REQUIREMENTS.md を `modules/` に収容して
   certified_hashes に登録するか、ゲートに custom-module 値スクリプト用の照合経路を足す。
3. **phone_type の認定**: `phone_type` は script_template であって `modules/` 認定部品ではない
   （certified_hashes に未登録）。050=その他 へ寄せた版を `modules/phone_type/` として oracle 付きで
   認定するのが full delivery の前提。
4. **検証で出る WARNING（許容）**: DOB チェーンは FLOW-006（確認 STT の直前が DOB ノードで TTS でない＝
   読み上げは DOB ノードの `$ivr.play` が担う）と REACH-003（否定/INVALID の再聴取 loop）を出すが、
   いずれも本番 厚木 と同じ意図的構造で Critical ではない。
