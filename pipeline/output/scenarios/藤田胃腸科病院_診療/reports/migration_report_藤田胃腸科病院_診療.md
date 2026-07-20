# 移行レポート — 藤田胃腸科病院 診療フロー

**生成日**: 2026/04/03  
**エージェント**: @migrator  
**環境**: デモ  
**移行元**: docs/migration/gen2_藤田胃腸科病院_診療.md  
**設計書**: docs/designs/設計書_藤田胃腸科病院_診療.yaml

---

## 出力ファイル一覧

| ファイル | フロー名 | モジュール数 |
|---|---|---|
| draft_藤田胃腸科病院_診療.json | す_諏訪$診療1_M_藤田_20260403 | 149 |
| draft_藤田胃腸科病院_氏名聴取.json | す_諏訪$診療1_氏名聴取_藤田_20260403 | 6 |
| draft_藤田胃腸科病院_生年月日聴取.json | す_諏訪$診療1_生年月日聴取_藤田_20260403 | 10 |
| draft_藤田胃腸科病院_電話番号聴取.json | す_諏訪$診療1_電話番号聴取_藤田_20260403 | 23 |
| properties_demo.md | — | — |

---

## フロー構成

### メインフロー構成

```
冒頭チェーン:
  Custom$wait (2000ms)
  → saveContextModel2DB（29フィールド）
  → incoming-classifier（非通知を含む全着信を acceptance_times へ）
  → acceptance_times
      ├─ TIMEOUT/ERROR/false → 終話_時間外 → 完了フラグ(status=6) → 切断
      └─ true → 冒頭_アナウンス

本人確認:
  冒頭_アナウンス → 本人確認(TTS) → 入力_本人確認(STT) → OpenAI_本人確認
      ├─ 本人 → サブフロー_氏名聴取
      └─ 代理 → 入電者氏名(TTS+STT+OpenAI) → サブフロー_氏名聴取

個人情報サブフロー:
  サブフロー_氏名聴取 → サブフロー_生年月日聴取 → サブフロー_電話番号聴取

用件1分岐:
  用件1(TTS+STT+OpenAI)
      ├─ 診察 → 通院歴
      ├─ 健診検査 → 用件2
      └─ 変更キャンセル → 用件3

診察予約ルート:
  通院歴(TTS+STT+OpenAI)
      ├─ 初診 → classification=新規 → 診察_予約希望日 → checkpoint=1/smsFlag=1 → その他問い合わせ
      └─ 再診 → classification=再診/smsFlag=0 → 終話_再診案内(status=2) → 切断

健診・検査等予約ルート:
  用件2(TTS+STT+OpenAI)
      ├─ 検査 → classification=予約 → 検査_受診希望日 → 検査_内容 → その他問い合わせ
      ├─ ドック → ドック_受診希望人数_希望日 → ドック_受診希望コース → その他問い合わせ
      └─ 健診 → 健診_受診希望日 → 健診_予約希望内容 → その他問い合わせ

変更・キャンセルルート:
  用件3(TTS+STT+OpenAI)
      ├─ 変更 → classification=変更 → 変更_予約日 → 変更用_予約希望時期 → その他問い合わせ
      ├─ キャンセル → classification=キャンセル → キャンセル_予約日 → その他問い合わせ
      └─ 問い合わせ → classification=確認 → 連絡事項_問い合わせ内容 → その他問い合わせ

共通終話:
  その他問い合わせ(TTS+STT+OpenAI) → script_終話判定
      ├─ キャンセル → 終話_キャンセル → 完了フラグ(status=5,smsFlag=2) → 切断
      ├─ 診察予約 → 終話_診察予約 → 完了フラグ(status=1,smsFlag=0) → 切断
      ├─ 健診等_携帯 → 終話_健診等_携帯 → 完了フラグ(status=1,smsFlag=1) → 切断
      └─ 健診等_固定 → 終話_健診等_固定 → 完了フラグ(status=1,smsFlag=1) → 切断
```

---

## 実装上の決定事項

### 非通知受入
- 設計書の指示通り、incoming-classifierでは非通知分岐を設けない
- 非通知・固定・海外・携帯・その他の全着信が acceptance_times に流れる

### acceptance_times
- 稼働時間未定のため、パラメータは TODO プレースホルダー
- true のみ冒頭アナウンスへ進む
- TIMEOUT/ERROR/false はすべて時間外アナウンスへ

### 本人確認
- メインフロー上に直接配置（サブフロー外）
- CLAUDE.md Rule 7 準拠

### サブフロー
- 氏名・生年月日・電話番号の3本
- 診察券番号聴取は設計書に含まれていないため除外
- CLAUDE.md Rule 9 準拠: 個人情報サブフロー.bivr をベースに生成

### saveCompletionFlag2db ステータス値
| 終話パス | status | smsFlag |
|---|---|---|
| 診察予約（新規） | 1（未処理） | 0 |
| 健診等予約 | 1（未処理） | 1 |
| キャンセル | 5（処理済み） | 2 |
| 再診案内 | 2（代表案内） | 0 |
| 時間外 | 6（時間外） | 0 |
| 失敗・リトライ上限 | 0（途中切断） | 0 |

### OpenAIプロンプト
- メインフロー内の全OpenAIモジュールのpromptは空文字（後から @prompter エージェントが記述）
- サブフローのOpenAIプロンプトは個人情報サブフロー.bivr から移植

### 終話判定スクリプト
- script_終話判定: classification と phonetype（電話番号聴取サブフロー結果）を組み合わせて終話TTSを振り分け
- smsFlag=2 → キャンセル終話
- classification=診察 かつ phonetype≠携帯 → 診察予約終話
- phonetype=携帯 → 健診等_携帯終話
- それ以外 → 健診等_固定終話

---

## 既知の TODO・BLOCKER

| 項目 | 状態 | 担当 |
|---|---|---|
| acceptance_timesの稼働時間設定 | TODO（稼働時間未定） | CS |
| 終話_時間外 のTTS文言 | TODO（稼働時間確定後） | CS |
| office_id設定 | TODO（ARS設定後） | CS |
| 全OpenAIモジュールのprompt記述 | TODO | @prompter |
| OpenAI URL・APIキー設定 | TODO | CS |
| IVRプロパティ全TTS文言の設定 | TODO | CS |
| clinicalDepartment enum最終確認 | BLOCKER指定（設計書注記） | CS |
| status=7（電話案内）の使用タイミング | BLOCKER指定（設計書注記） | CS |

---

## 品質チェック結果

| チェック項目 | 結果 |
|---|---|
| 全next参照の整合性 | OK（全4フロー） |
| 全subs参照の整合性 | OK（全4フロー） |
| save2dbがnextに登場しないこと | OK |
| Retryのcondition/label形式 | true/false / Retry/No more で統一 |
| STT successが `^.+$` 1本受け | OK |
| TTS next labelが `Next Module` | OK |
| acceptance_timesのtrue/false/TIMEOUT/ERROR分岐 | OK |
| 非通知分岐なし（incoming-classifier） | OK（全着信をacceptance_timesへ） |
| 冒頭wait(Custom$wait) | OK |
| saveContextModel2DB（冒頭チェーン内） | OK（29フィールド定義） |
| サブフロー出口の script_結果返却 | OK（全3サブフロー） |
| stop_by_dtmf値が "No"/"Yes" | OK |
