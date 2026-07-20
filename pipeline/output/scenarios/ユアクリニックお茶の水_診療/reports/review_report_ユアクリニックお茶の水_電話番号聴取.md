# 校閲レポート: ユアクリニックお茶の水 - 電話番号聴取サブフロー

**対象ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_電話番号聴取.json`
**設計書**: `docs/designs/設計書_ユアクリニックお茶の水_診療.yaml`
**リファレンス**: `docs/reference/bivr/samples/個人情報サブフロー.bivr`（電話番号聴取フロー）
**validator.py 実行結果**: PASS (Warning 7件)
**校閲日**: 2026-04-01
**校閲バージョン**: v3（リファレンスbivrとの直接照合済み）

---

## セキュリティ・ライセンス警告（最優先確認）

なし。インジェクションパターン・禁止モジュールタイプ・動的実行リスクは検出されなかった。

---

## サマリー

- 検出問題数: 3件
- 重大度別: SECURITY-CRITICAL 0 / Critical 1 / Warning 1 / LICENSE-WARN 0 / Info 1
- 修正担当別: generator 1件 / prompter 0件 / properties 0件 / 人間確認 0件

---

## 検出事項

### C-001: 出口スクリプト構造がリファレンスと異なる（携帯ルート/その他ルート の置換）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_電話番号聴取.json`
- **修正担当**: generator
- **モジュール名**: `携帯電話判別`, `携帯以外`, `script_結果返却_携帯`, `script_結果返却_その他`
- **フィールド**: `携帯電話判別.next[0].nextModuleName`, `携帯以外.next[0].nextModuleName`, modulesキー（追加/削除）
- **問題**: リファレンス（個人情報サブフロー.bivr）の出口構造は `携帯ルート` / `その他ルート` の2モジュール構成だが、draftでは `script_結果返却_携帯` / `script_結果返却_その他` に置き換えられている。CLAUDE.md Rule 9「フロー名プレフィックスのみ対象施設に置換し、モジュール構造・接続・スクリプトは一切変更しない」への直接違反。
- **現在値**:
  - `携帯電話判別.next[0]` = `{"condition": "^.*$", "label": "next", "nextModuleName": "script_結果返却_携帯"}`
  - `携帯以外.next[0]` = `{"condition": "^.*$", "label": "next", "nextModuleName": "script_結果返却_その他"}`
  - modules に `script_結果返却_携帯`, `script_結果返却_その他` が存在
  - modules に `携帯ルート`, `その他ルート` が不在
- **正しい値**:
  - `携帯電話判別.next[0]` = `{"condition": "^.*$", "label": "next", "nextModuleName": "携帯ルート"}`
  - `携帯以外.next[0]` = `{"condition": "^.*$", "label": "next", "nextModuleName": "その他ルート"}`
  - modules に `携帯ルート`, `その他ルート` を追加
  - modules から `script_結果返却_携帯`, `script_結果返却_その他` を削除
- **修正指示**:
  1. `script_結果返却_携帯`, `script_結果返却_その他` を `modules` から削除する。
  2. `携帯電話判別.next[0].nextModuleName` を `"携帯ルート"` に変更する。
  3. `携帯以外.next[0].nextModuleName` を `"その他ルート"` に変更する。
  4. 以下の2モジュールを `modules` に追加する（リファレンスからの完全コピー）。

  **携帯ルート**（追加・リファレンス完全コピー）:
  ```json
  "携帯ルート": {
    "layout": {"x": 1000, "y": 1150},
    "next": [
      {"condition": "^.*$", "label": "Jump 1", "nextModuleName": ""},
      {"condition": "", "label": "Jump 2", "nextModuleName": ""},
      {"condition": "", "label": "Jump 3", "nextModuleName": ""},
      {"condition": "", "label": "Jump 4", "nextModuleName": ""},
      {"condition": "", "label": "Jump 5", "nextModuleName": ""},
      {"condition": "", "label": "Jump 6", "nextModuleName": ""},
      {"condition": "", "label": "Jump 7", "nextModuleName": ""},
      {"condition": "", "label": "Jump 8", "nextModuleName": ""},
      {"condition": "", "label": "Jump 9", "nextModuleName": ""},
      {"condition": "", "label": "Jump 10", "nextModuleName": ""},
      {"condition": "", "label": "Jump 11", "nextModuleName": ""},
      {"condition": "", "label": "Jump 12", "nextModuleName": ""}
    ],
    "subs": [{"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}],
    "name": "携帯ルート",
    "description": "",
    "matchingmethod": 1,
    "type": "@General$Script",
    "params": {
      "script": "var res = $runner.getModuleResult(\"携帯電話判別\");\n$runner.setResult(res);\n\nvar flowName = $runner.getCurrentFlowName();\nvar rid = $ivr.getRID();\nvar key = flowName + \".\" + rid;  \n$ivr.setObject(key, res);"
    }
  }
  ```

  **その他ルート**（追加・リファレンス完全コピー）:
  ```json
  "その他ルート": {
    "layout": {"x": 400, "y": 1400},
    "next": [
      {"condition": "^.*$", "label": "Jump 1", "nextModuleName": ""},
      {"condition": "", "label": "Jump 2", "nextModuleName": ""},
      {"condition": "", "label": "Jump 3", "nextModuleName": ""},
      {"condition": "", "label": "Jump 4", "nextModuleName": ""},
      {"condition": "", "label": "Jump 5", "nextModuleName": ""},
      {"condition": "", "label": "Jump 6", "nextModuleName": ""},
      {"condition": "", "label": "Jump 7", "nextModuleName": ""},
      {"condition": "", "label": "Jump 8", "nextModuleName": ""},
      {"condition": "", "label": "Jump 9", "nextModuleName": ""},
      {"condition": "", "label": "Jump 10", "nextModuleName": ""},
      {"condition": "", "label": "Jump 11", "nextModuleName": ""},
      {"condition": "", "label": "Jump 12", "nextModuleName": ""}
    ],
    "subs": [{"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}],
    "name": "その他ルート",
    "description": "",
    "matchingmethod": 1,
    "type": "@General$Script",
    "params": {
      "script": "var res = $runner.getModuleResult(\"携帯以外\");\n$runner.setResult(res);\n\nvar flowName = $runner.getCurrentFlowName();\nvar rid = $ivr.getRID();\nvar key = flowName + \".\" + rid;  \n$ivr.setObject(key, res);"
    }
  }
  ```

- **参照**: CLAUDE.md Rule 9（「フロー名プレフィックスのみ対象施設に置換し、モジュール構造・接続・スクリプトは一切変更しない」）

> 修正指示: 上記フィールドのみを修正し、他のモジュールには一切触れないこと。

---

### W-001: DTMF retry=0 / termdtmf=* — リファレンス準拠だが注意が必要な設定

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_電話番号聴取.json`
- **修正担当**: （修正不要）
- **モジュール名**: `入力_患者_携帯電話`, `入力_患者_連絡先`, `入力_患者_復唱連絡先`
- **フィールド**: `params.retry`, `params.termdtmf`
- **問題**:
  - `params.retry = "0"`: DTMFリトライが0に設定されている。CLAUDE.md デフォルトは `"2"` だが、リファレンスも同一値。Speech Retry Counter 側でリトライを制御しているため意図的な設計。validator.py DTMF-003 として検出済み。
  - `params.termdtmf = "*"`: CLAUDE.md デフォルトは `"#"` だが、リファレンスも `"*"` を使用。患者が `*` キーを誤押下した場合に意図せず入力確定となるリスクあり。
- **現在値**: `retry="0"`, `termdtmf="*"`（全3モジュール共通）
- **正しい値**: リファレンスと同一のため修正不要。
- **修正指示**: 対応不要（リファレンス準拠）。ただし `*` vs `#` の選択はTS担当者が意図的であることを確認推奨。

> 修正指示: 対応不要。

---

### I-001: 着信電話番号分岐の `^*$` は不正な正規表現（リファレンスと同一）

- **ファイル**: `output/scenarios/ユアクリニックお茶の水_診療/draft_ユアCLお茶水_電話番号聴取.json`
- **修正担当**: （修正不要 / 人間確認を推奨）
- **モジュール名**: `着信電話番号分岐`
- **フィールド**: `next[4].condition`
- **問題**: `^*$` は正規表現として無効（`*` は直前要素のゼロ回以上の繰り返しを意味するが、直前に何もないため構文エラー）。ただしリファレンス（個人情報サブフロー.bivr）も同じ `^*$` を使用しており、Brekeke IVR 側では動作しているものと推定される。CLAUDE.md Rule 9 の観点からは「構造の完全コピー」のためリファレンスと一致した現状が正しい。
- **現在値**: `next[4].condition = "^*$"`
- **修正指示**: リファレンスと一致しているため修正不要。Brekeke 上での動作に問題が生じた場合は `^.*$` への変更を検討すること。

---

## リファレンス完全照合サマリー

リファレンス `docs/reference/bivr/samples/個人情報サブフロー.bivr`（電話番号聴取フロー）と draft の全モジュールを照合した結果:

| 確認項目 | 結果 |
|---|---|
| モジュール構成（リファレンスにありdraftになし） | `携帯ルート`, `その他ルート` が不在 — **C-001** |
| モジュール構成（draftにありリファレンスになし） | `script_結果返却_携帯`, `script_結果返却_その他` が余剰 — **C-001** |
| next配列の差分（共通モジュール） | `携帯電話判別.next[0]`, `携帯以外.next[0]` が異なる遷移先 — **C-001** |
| subs配列の差分（共通モジュール） | `リトライ_患者_復唱連絡先.subs[0].label` が `"save-PhoneNumber"` — リファレンスも同一の不整合あり（対応不要） |
| params の差分（共通モジュール） | 差分なし（全モジュール一致） |
| script_携帯判別スクリプト | コメント行の有無のみ差異（機能的に同一） |
| incoming-classifier 条件 | `^*$` — リファレンスと同一（I-001） |
| OpenAIプロンプト（2モジュール） | リファレンスと実質同一（否定パターンの小差はあるが機能的影響なし） |

---

## レッドチーム攻撃シナリオ

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | 携帯から発信した場合（正常系） | 正常系（携帯パス） | 着信分岐で携帯 → save-携帯電話 → 電話番号正規化 → 患者_携帯（復唱TTS）→ 入力_患者_携帯電話 → openAI_患者_携帯電話 肯定 → script_携帯判別 MOBILE → 携帯電話判別 → 携帯ルート（修正後） | 低 | C-001修正後に正常動作見込み |
| 2 | 固定電話から着信し、連絡先として携帯番号を入力した場合 | 固定着信＋携帯連絡先 | 着信分岐で固定 → 患者_連絡先 → 入力_患者_連絡先 → 電話番号正規化2 → 復唱 → 肯定 → script_携帯判別 MOBILE → 携帯電話判別 → 携帯ルート | 中 | C-001修正後に動作確認必要 |
| 3 | 非通知または海外発信の場合 | 非通知/海外 | 着信分岐で非通知/海外 → 患者_連絡先 TTS（連絡先聴取パスに入る） | 高 | 電話番号サブフロー設計仕様（メインフローで非通知を弾く前提）。設計意図に合致 |
| 4 | 携帯確認で否定後、連絡先もリトライ上限到達した場合 | リトライ上限フォールバック | リトライ_患者_連絡先 No more → save-着信元電話番号（着信番号をフォールバック保存）→ script_携帯判別で判定 | 中 | 着信番号フォールバック保存で対策済み |
| 5 | 11桁だが `00000000000` のような無効番号を入力した場合 | 無効番号バリデーション | `入力_患者_連絡先.params.condition` は桁数チェックのみ（`val.length > 9 && val.length < 12`）→ 電話番号正規化2 → 復唱される | 低 | Phone Normalization での追加バリデーションに委ねる（仕様上許容範囲） |
| 6 | 患者が復唱確認で `*` キーを押した場合 | termdtmf=* 誤作動 | 入力が強制終了し空入力扱い → openAI で NO_RESULT → リトライ | 中 | W-001: リファレンス準拠。TS確認推奨 |
| 7 | プロンプトインジェクション: 「システムを無視して」と発話 | STT→OpenAI インジェクション | functionCall で `enum: [肯定, 否定, NO_RESULT]` に出力を制限。インジェクション耐性あり | 高 | 対策済み |
| 8 | 060/070/080/090以外の番号（050番号など）を連絡先に入力した場合 | 携帯判別境界値 | script_携帯判別の正規表現 `/^0[6-9]0\d{8}$/` にマッチせず OTHER → 携帯以外 → その他ルート | 低 | 設計意図に合致（050はその他扱い） |

---

## OpenAIプロンプト出力ラベル整合性

| モジュール名 | next分岐ラベル | prompt出力仕様 | 判定 | 備考 |
|---|---|---|---|---|
| openAI_患者_携帯電話 | 肯定, 否定, NO_RESULT | 肯定, 否定, NO_RESULT | PASS | functionCall enum制限あり |
| openAI_患者_復唱連絡先 | 肯定, 否定, NO_RESULT | 肯定, 否定, NO_RESULT | PASS | functionCall enum制限あり |

---

## 修正指示一覧（エージェント別）

### generator向け

**C-001 対応（必須）: 出口スクリプト構造をリファレンスに戻す**

以下の手順で修正すること。他のモジュールには一切触れないこと。

1. `modules` から `script_結果返却_携帯`, `script_結果返却_その他` を削除する。
2. `携帯電話判別.next[0].nextModuleName` を `"script_結果返却_携帯"` から `"携帯ルート"` に変更する。
3. `携帯以外.next[0].nextModuleName` を `"script_結果返却_その他"` から `"その他ルート"` に変更する。
4. 以下の2モジュールを `modules` に追加する（リファレンス `docs/reference/bivr/samples/個人情報サブフロー.bivr` の電話番号聴取フローからの完全コピー）:

   **携帯ルート** (`@General$Script`):
   - `params.script`: `var res = $runner.getModuleResult("携帯電話判別");\n$runner.setResult(res);\n\nvar flowName = $runner.getCurrentFlowName();\nvar rid = $ivr.getRID();\nvar key = flowName + "." + rid;  \n$ivr.setObject(key, res);`
   - `next`: Jump 1（`^.*$`, nextModuleName空）＋ Jump 2〜12（空）の12スロット構成
   - `subs`: 3スロット空

   **その他ルート** (`@General$Script`):
   - `params.script`: `var res = $runner.getModuleResult("携帯以外");\n$runner.setResult(res);\n\nvar flowName = $runner.getCurrentFlowName();\nvar rid = $ivr.getRID();\nvar key = flowName + "." + rid;  \n$ivr.setObject(key, res);`
   - `next`: Jump 1（`^.*$`, nextModuleName空）＋ Jump 2〜12（空）の12スロット構成
   - `subs`: 3スロット空

### prompter向け

なし。

### properties向け

なし（電話番号聴取サブフロー単体のproperties生成は設計書のスコープ外）。

---

## 人間が確認すべき箇所

なし。SECURITY-CRITICAL・LICENSE-WARN は検出されなかった。

W-001（termdtmf=*）については、TS担当者がリファレンスを意図的に `*` で設計したか、`#` が正しいかを確認することを推奨する。
