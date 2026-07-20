# DOB Re-confirmation — 仕様（生年月日 復唱 / 決定論正規化）

生年月日を STT/DTMF で受け、和暦・西暦・漢数字・全角を決定論的に正規化し `#data#` 復唱する
**custom-module 値スクリプト**部品。OpenAI 不使用（`openAI_prompt` パラメータには決定論パーサ本文が入る＝命名は本番踏襲だが OpenAI は呼ばない）。

## ランタイム種別と認定ゲートの扱い（重要）

- Brekeke モジュール型: `drjoy^TS Custom Module$DOB Re-confirmation`（`@General$Script` ではない）
- 値スクリプトは `params.openAI_prompt` に入る。`getProperty` / `$ivr.play` / `$ivr.exec` を使う。
- **P6 ハッシュゲート（engine/spec 二段）の対象外**: `orchestrator._collect_flow_scripts` は
  `@General$Script` の `params.script` のみをスキャンするため、本モジュールはゲートに見えない。
  → `certified_hashes.json` の二段判定には登録しない（登録しても照合経路が無いため無意味）。
  → 同等性の担保は (a) 本番デプロイ済み JS とのバイト一致（memory: project_dob_reconfirmation_acceptance、
     oracle 44/47・デプロイ JS バイト一致）と (b) repo 正本 `module_value.js` の版管理で行う。
  → full delivery でゲート照合経路を足す場合は custom-module 値スクリプト用のスキャンを別途実装する（follow-up）。

## 入出力

- 入力: 直前の STT/DTMF モジュール（`module` パラメータで指定）の生年月日発話
- 正規化: DTMF 8 桁（YYYYMMDD）/ `YYYY-MM-DD HH:MM` / 和暦・漢数字・全角を半角西暦へ
- 出力（next の分岐キー）:
  - `^.*$`（success）→ 正規化成功（`#data#` に整形日付）。後段で復唱 STT（はい/いいえ）へ
  - `^INVALID$` → 形式不正（再入力）
  - `^TIMEOUT$` / `^ERROR$` → リトライ

## TZ 固定（Asia/Tokyo）

- 原本（VN 製）は無引数 `new Date()` で「現在年/今日」を取り 120 年超・未来日を判定する＝サーバ TZ 依存。
- Nashorn に `Intl` が無いため、`__jstNow()`（UTC+9h）ヘルパで JST に固定した版を repo 正本とする。
  - 置換箇所: `currentYear` / `maxReiwaYear`（令和上限）/ `today`（未来日判定）。
  - 生成: `scaffold_generator._pin_dob_tz(~/Downloads/_dob_bivr/module_value.js)`。
- memory: feedback_vn_scripts_jst_pin（深夜の 1 日ズレ対策）。

## 正本と組込

- 正本: `modules/dob_reconfirmation/module_value.js`（TZ 固定済み）。
- `scaffold_generator.build_dob_reconfirmation` がこの正本を読み `openAI_prompt` に埋め込む
  （`~/Downloads` 原本への実行時依存を排し再現性を確保。原本のみある環境では実行時 TZ 固定にフォールバック）。

## オラクル（follow-up）

- `oracle.py` / `test_oracle.py` は未収容。既存の 44/47（残 3 は仕様衝突として整理済み）は ad-hoc 実行で未コミット。
- full delivery では和暦/西暦/漢数字/DTMF/120年・未来日ガードを網羅する parity オラクルを収容する。
