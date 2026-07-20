# モジュール命名規則

> **対象**: Brekeke フローデザイナー上のモジュール名  
> **生成元**: `scaffold_generator.py` が自動付与。手修正・設計書記述時も本規則に従う。  
> `{step}` = 設計書の `scenario_flow` に記載した step 名（例: `用件`、`変更_診療科`）

---

## 1. モジュール種別ごとの命名パターン

| モジュール種別 | Brekeke type | 命名パターン | 例 |
|---|---|---|---|
| **TTS 発話** | Text to speech | `{step}` | `用件`、`変更_診療科` |
| **STT 音声入力** | AmiVoice Speech to Text | `入力_{step}` | `入力_用件`、`入力_変更_診療科` |
| **STT DTMF+音声** | DTMF AmiVoice STT Input | `入力_{step}` | `入力_用件`、`入力_診察券番号` |
| **リトライカウンタ** | Speech Retry Counter | `リトライ_{step}` | `リトライ_用件`、`リトライ_変更_診療科` |
| **OpenAI 分類** | generate_by_OpenAI | `OpenAI_{step}` | `OpenAI_用件`、`OpenAI_診察券番号` |
| **OpenAI フォールバック** | @General$Script | `script_{step}_fallback` | `script_用件_fallback` |
| **エンティティ分類** | Entity Classifier | `Entity_{分類名}` | `Entity_YES/NO`、`Entity_用件` |
| **スクリプト処理** | @General$Script | `Scripts_{step}` または `Scripts-{step}` | `Scripts_FAQ`、`Scripts-診察券番号` |
| **save2db 保存** | save2db | `save-{step}` または `save-入力_{step}` | `save-用件`、`save-入力_患者名` |
| **saveContext** | saveContext2DB | `{分岐結果名}` | `変更`、`キャンセル`、`聴取失敗` |
| **saveContextModel** | saveContextModel2DB | `コンテキスト作成` | `コンテキスト作成` |
| **完了フラグ** | saveCompletionFlag2db | `Flag-{フラグ名}` | `Flag-予約_ワクチン`、`時間外status` |
| **コンテキストルーター** | ContextMatchRouter | `{step}_分岐` | `用件_分岐`、`終話_分岐` |
| **CMR チェーン** | ContextMatchRouter | `ContextMatchRouter_{step}_chain_{n}` | `ContextMatchRouter_用件_chain_0` |
| **CMR 群** | ContextMatchRouter | `ContextMatchRouter_{step}_群{n}` | `ContextMatchRouter_診療科_群1` |
| **Jump to Flow** | Custom Jump to Flow | `jump-{サブフロー名}` または `jump_{step}` | `jump-当日確認`、`jump_FAQ` |
| **受付時間判定** | acceptance_times | `営業時間チェック` | `営業時間チェック` |
| **着信分類** | incoming-classifier | `着信番号判定` または `着信_判定` | `着信番号判定`、`WEB_RTC_分岐` |
| **ヘッダー取得** | get-header | `Get-Header` | `Get-Header` |
| **RAG 照合** | AmiVoice RAG / External Integration RAG | `RAG-{step}` または `{step}_モジュール` | `RAG-用件`、`FAQ_モジュール` |
| **DOB 復唱** | DOB Re-confirmation | `DOB_{step}` | `DOB_生年月日` |
| **電話番号正規化** | Phone Normalization | `Phone_{step}` | `Phone_連絡先確認`、`Phone_番号再入力` |
| **再確認ノード** | Re-confirmation node data | `{step}` | `キャンセル_現在の予約日` |
| **復唱 OpenAI** | generate_by_OpenAI | `openAI_{step}_復唱` | `openAI_変更_診療科_復唱` |
| **待機** | Custom wait | `{step}待機` | `冒頭待機` |
| **切断** | @IVR$Disconnect | `{step}_切断` | `当日該当_切断`、`時間外切断` |
| **拒否** | @IVR$Reject | `{step}切断` | `時間外切断`、`通話完了` |

---

## 2. 命名の基本ルール

### 2-1. 区切り文字

| 用途 | 使う文字 | 例 |
|---|---|---|
| 単語区切り | `_`（アンダースコア） | `変更_診療科`、`入力_変更_診療科` |
| save2db 名 | `-`（ハイフン） | `save-用件`、`save-入力_患者名` |
| 英数とのつなぎ | `-` または `_` どちらも可 | `Scripts-診察券番号`、`Scripts_FAQ` |

### 2-2. プレフィックス対応表

| プレフィックス | 意味 |
|---|---|
| `入力_` | ユーザーの発話を受け取る STT/DTMF ノード |
| `リトライ_` | リトライカウンタ（無応答・誤入力時） |
| `OpenAI_` | OpenAI による分類・判定 |
| `script_` | スクリプト処理（小文字。OpenAI フォールバックは `script_{step}_fallback`） |
| `Scripts_` / `Scripts-` | スクリプト処理（大文字。既存フローの慣習） |
| `save-` | save2db への保存 |
| `Entity_` | エンティティ分類器 |
| `jump-` / `jump_` | Jump to Flow |
| `ContextMatchRouter_` | コンテキストマッチルーター（チェーン・群） |
| `Flag-` | 完了フラグ保存 |
| `DOB_` | 生年月日復唱モジュール |
| `Phone_` | 電話番号正規化モジュール |
| `RAG-` | RAG 照合 |

### 2-3. TTS ノード名 = step 名（プレフィックスなし）

TTS は「そのまま読む」ノードなので、step 名をそのまま使う。  
`変更_診療科` → TTS 名も `変更_診療科`

### 2-4. 禁止事項

| NG | 理由 |
|---|---|
| スペースを含む名前 | URL エンコード後にファイル名が壊れる |
| `(` `)` などの括弧 | URL エンコード非対応 |
| 同一フロー内での重複名 | Brekeke がモジュールを識別できなくなる |
| 255 バイト超（URL エンコード後） | ファイル名の OS 制限 |

---

## 3. よく使うパターン（セット）

### hearing（音声聴取）の基本セット

```
{step}               ← TTS 発話
入力_{step}          ← STT / DTMF 入力
リトライ_{step}      ← リトライカウンタ
OpenAI_{step}        ← 分類・判定
script_{step}_fallback ← OpenAI TIMEOUT/ERROR フォールバック
save-{step}          ← save2db 保存
```

### 復唱確認の追加セット

```
復唱_{step}          ← 復唱 TTS
入力復唱_{step}      ← 復唱 STT
openAI_{step}_復唱   ← 復唱 YES/NO 判定
save-{step}_復唱     ← 復唱結果の保存
リトライ_復唱_{step} ← 復唱リトライ
```

### 個人情報聴取（scaffold 自動展開）

```
氏名                 ← TTS
入力_患者名          ← STT
リトライ_患者名      ← リトライ
生年月日             ← TTS
入力_生年月日        ← DTMF STT
DOB_生年月日         ← DOB 復唱
診察券番号           ← TTS
入力_診察券番号      ← DTMF STT
患者_連絡先_聴取     ← TTS
入力_連絡先番号2     ← DTMF STT
Phone_連絡先確認     ← 電話番号正規化
```

---

## 4. フロー名の命名規則

| 種別 | パターン | 例 |
|---|---|---|
| メインフロー | `{施設名}$M｜{フロー名}` | `東京クリニック$M｜診療` |
| サブフロー | `{施設名}$S｜{サブフロー名}` | `東京クリニック$S｜用件` |
| テストフロー（P6） | `{施設名}$T｜{テスト名}` | `東京クリニック$T｜診察券番号` |
| TTS Preview | `{施設名}$TTS_M｜{フロー名}` | `東京クリニック$TTS_M｜診療` |
| 連結テスト | `{施設名}$P7_M｜{フロー名}` | `東京クリニック$P7_M｜診療` |

`M`=Main / `S`=Sub / `T`=Test / `｜` は全角縦棒（U+FF5C）

---

## 5. 設計書 YAML での step 名 → モジュール名の自動変換

`scaffold_generator.py` が以下の変換を自動実行する。

```
scenario_flow の step 名: 変更_診療科

自動生成されるモジュール名:
  変更_診療科              (TTS)
  入力_変更_診療科         (STT)
  リトライ_変更_診療科     (Retry)
  OpenAI_変更_診療科       (OpenAI)
  script_変更_診療科_fallback  (フォールバック Script)
  save-変更_診療科         (save2db)
```

手動でモジュール名を指定する場合は設計書の `step_details.{step}.module_name` で上書き可能。
