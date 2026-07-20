# dob_reconfirmation（DOB Re-confirmation）

生年月日の決定論正規化＋`#data#` 復唱を行う custom-module 値スクリプト部品（OpenAI 不使用）。
`slot: date_of_birth` の決定論インライン展開で scaffold が自動配線する。

## 使い方

`build_dob_reconfirmation(name, source_module, success_next, invalid_next, retry_next)`。
正本 `module_value.js`（TZ 固定済み）を `openAI_prompt` に埋め込む。

## 構成

```
dob_reconfirmation/
├── REQUIREMENTS.md     仕様（正規化規則・TZ固定・ゲート扱い）
├── README.md           本ファイル
├── module_value.js     値スクリプト正本（Asia/Tokyo TZ 固定済み）
└── acceptance_test/    （oracle 収容は follow-up）
```

## 認定状況

- Brekeke モジュール型 `drjoy^TS Custom Module$DOB Re-confirmation`＝**P6 ハッシュゲート対象外**
  （ゲートは `@General$Script` のみスキャン）。詳細は REQUIREMENTS.md「ランタイム種別と認定ゲートの扱い」。
- 同等性の担保: 本番デプロイ済み JS とバイト一致（memory: project_dob_reconfirmation_acceptance, oracle 44/47）。
- repo 正本化（`~/Downloads` 依存の排除）= 2026-06-17（フラット化フェーズ2 / 2A）。
- **follow-up**: parity オラクル（oracle.py / test_oracle.py）の収容、custom-module 用ゲート照合経路。
