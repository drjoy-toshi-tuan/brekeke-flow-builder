# 移管レポート — 恵佑会札幌病院 診療

> 作業種別: Gen2→Gen3移管
> 生成日: 2026-03-30
> 担当エージェント: @migrator

---

## 1. 作業概要

| 項目 | 内容 |
|---|---|
| 施設名 | 恵佑会札幌病院（歯科口腔外科） |
| フロー名 | `恵佑会札幌$診療` |
| 作業種別 | Gen2→Gen3移管 |
| ソース | `docs/migration/gen2_恵佑会札幌病院_診療.md` |
| 設計書 | `docs/designs/設計書_恵佑会札幌病院_診療.md` |
| 対象環境 | デモ（仮設定） |

---

## 2. 生成成果物

| ファイル | 内容 | モジュール数 | 状態 |
|---|---|---|---|
| `output/json/draft_恵佑会札幌病院_診療.json` | メインフロー JSON | 154 | PASS（警告2件） |
| `output/json/draft_恵佑会札幌病院_氏名聴取.json` | 氏名聴取サブフロー | 5 | リファレンスコピー |
| `output/json/draft_恵佑会札幌病院_生年月日聴取.json` | 生年月日聴取サブフロー | 9 | リファレンスコピー |
| `output/json/draft_恵佑会札幌病院_電話番号聴取.json` | 電話番号聴取サブフロー | 24 | リファレンスコピー |
| `output/json/draft_恵佑会札幌病院_診察券番号聴取.json` | 診察券番号聴取サブフロー | 41 | リファレンスコピー |
| `output/properties_恵佑会札幌病院_診療_demo.md` | IVRプロパティ（デモ環境） | --- | 生成済み |
| `output/properties_恵佑会札幌病院_診療_prod.md` | IVRプロパティ（本番環境） | --- | 生成済み |
| `output/properties_恵佑会札幌病院_診療.md` | IVRプロパティ（バリデーター参照用、デモと同内容） | --- | 生成済み |

---

## 3. バリデーション結果

```
[REPORT] バリデーション結果: 恵佑会札幌$診療
モジュール数: 154
検出問題数: 2
  [Critical]: 0
  [Warning]:  2
判定: [PASS]

[W] [T-002] END_上限エラー > (module): どこからも参照されていない孤立モジュールです
[W] [P-030] (properties) > TODO: propertiesに TODO_ が残っています: office_id=TODO_office_id
```

### 警告の詳細

| コード | モジュール | 説明 | 対応 |
|---|---|---|---|
| T-002 | END_上限エラー | 孤立モジュール（メインフローからの直接参照なし） | 意図的。電話番号聴取サブフローの上限到達エンドポイントとして定義。サブフロー側ロジックから参照される想定 |
| P-030 | office_id | `TODO_office_id` プレースホルダー | BLOCKER。施設ID確定後に置き換えること（`output/properties_恵佑会札幌病院_診療_demo.md` および `_prod.md` 両方） |

---

## 4. フロー構成

### 4.1 メインフロー（154モジュール）

```
冒頭(wait 2000ms)
  → コンテキスト設定(saveContextModel2DB, 18フィールド)
    → 着信分類(incoming-classifier)
      ├── 非通知/海外 → 非通知_アナウンス → 完了フラグ_非通知(status=2, smsFlag=-1) → 切断
      └── 通常/携帯/固定 → 営業時間チェック(acceptance_times)
            ├── 時間外 → 時間外_アナウンス → 完了フラグ_時間外(status=6, smsFlag=-1) → 切断
            └── 受付可 → 冒頭_アナウンス
                  → 申し込み方法確認（DTMF+音声、max_dtmf_length=1）
                        ├── ネット(1) → SMS電話番号種別判定
                        │       ├── 携帯 → TTS_SMS_連絡先携帯（復唱確認）
                        │       │       ├── 肯定 → END_SMS送信案内(status=8, smsFlag=3)
                        │       │       └── 否定 → TTS_SMS_連絡先固定
                        │       └── 固定 → TTS_SMS_連絡先固定（携帯番号聴取）
                        │               → TTS_SMS_連絡先固定_復唱確認
                        │                   ├── 肯定 → END_SMS送信案内
                        │                   └── 否定 → TTS_SMS_連絡先固定
                        └── 電話(2) → 用件確認（DTMF+音声、max_dtmf_length=1）
                                ├── 受付不可 → END_受付不可診療科(status=2, smsFlag=0)
                                ├── 予約(1) → 受診歴確認
                                │     ├── 初診 → 紹介状確認
                                │     │     ├── 有り → 医師名確認 → [共通A]
                                │     │     ├── 無し → 希望医師確認 → [共通A]
                                │     │     └── その他 → [共通A]
                                │     └── 再診 → 予約希望日_再診 → [共通B]
                                ├── 変更(2) → 予約日_変更 → 予約希望日_変更 → [共通B]
                                ├── キャンセル(3) → 予約日_キャンセル → キャンセル理由 → [共通B]
                                └── その他(4) → 内容確認 → [共通B]

[共通A] 氏名聴取(サブフロー) → 生年月日聴取(サブフロー) → 電話番号聴取(サブフロー)
          → 最終問い合わせ確認 → script_終話分岐

[共通B] 診察券番号聴取(サブフロー) → 氏名聴取(サブフロー) → 生年月日聴取(サブフロー) → 電話番号聴取(サブフロー)
          → 最終問い合わせ確認 → script_終話分岐

終話分岐 → 用件×電話種別(8パターン) + SMS + 受付不可 + 代表案内 = 計14終話パターン
```

### 4.2 サブフロー（リファレンスコピー）

| サブフロー名 | ソース | フロー名変更 |
|---|---|---|
| `恵佑会札幌$氏名聴取` | `TSHamaguchi_demo$氏名聴取` | プレフィックスのみ変更 |
| `恵佑会札幌$生年月日聴取` | `TSHamaguchi_demo$生年月日聴取` | プレフィックスのみ変更 |
| `恵佑会札幌$電話番号聴取` | `TSHamaguchi_demo$電話番号聴取` | プレフィックスのみ変更 |
| `恵佑会札幌$診察券番号聴取` | `TSHamaguchi_demo$診察券番号聴取` | プレフィックスのみ変更 |

モジュール構造・接続・スクリプトは一切変更なし（CLAUDE.md 原則9に準拠）。

---

## 5. Gen2→Gen3変換サマリー

### 5.1 主要な変換内容

| Gen2の定義 | Gen3の実装 |
|---|---|
| OpenAIプロンプト関数（多段if/else） | DTMF AmiVoice STT Input + generate_by_OpenAI モジュール |
| 受診歴・紹介状・医師名等の音声ヒアリング | AmiVoice Speech to Text + generate_by_OpenAI モジュール |
| 申し込み方法判定（ネット/電話） | DTMF max_dtmf_length=1 + OpenAI正規化 |
| SMS送信ルート | script_SMS_電話番号種別判定 → 2分岐 |
| 受付不可診療科検知（17診療科） | 用件確認OpenAIの受付不可パターンマッチ |
| 終話パターン（14種） | script_終話分岐 → 14 TTS_END → saveCompletionFlag2db → Disconnect |
| 個人情報聴取（氏名/生年月日/電話/診察券） | Custom Jump to Flow → サブフロー |
| 患者名カタカナ変換指示 | 氏名聴取サブフロー内のOpenAIプロンプトで処理（リファレンス準拠） |

### 5.2 AmiVoice辞書（profile_words）の設定

設計書の辞書定義に従い、以下のSTTモジュールに辞書単語を設定済み：

| STTモジュール | 辞書種別 |
|---|---|
| 入力_申し込み方法確認 | 申し込み方法用語辞書 |
| 入力_用件確認 | 用件・診療科名辞書（受付不可診療科17種含む） |
| 入力_受診歴確認 | 初診/再診判定用語辞書 |
| 入力_紹介状確認 | 紹介状関連用語辞書 |
| 入力_予約日系（4モジュール） | 日付辞書（空：和暦+month+day辞書を参照） |
| 入力_医師名確認 / 希望医師確認 | 空（フリーテキスト） |
| 入力_キャンセル理由 / 内容確認 / 最終問い合わせ | 空（フリーテキスト） |
| 入力_SMS_連絡先系 | 空（DTMFメイン） |

---

## 6. BLOCKER・要確認事項

### BLOCKER（移管後に必ず対応）

| # | 内容 | 対応先ファイル |
|---|---|---|
| 1 | `office_id` 施設IDが未確定（`TODO_office_id`） | `output/properties_恵佑会札幌病院_診療_demo.md`<br>`output/properties_恵佑会札幌病院_診療_prod.md`<br>`output/properties_恵佑会札幌病院_診療.md` |

### 要確認事項（設計書 §9 より）

| # | 内容 | 影響箇所 |
|---|---|---|
| 2 | 営業時間の曜日・時間帯（平日8:45-17:00で正しいか） | `acceptance_times` モジュール設定 |
| 3 | 非通知アナウンスの文言確認（仮設定） | `非通知_アナウンス.prompt` |
| 4 | 時間外アナウンスの文言確認（仮設定） | `時間外_アナウンス.prompt` |
| 5 | 対応電話番号の確認 | Brekeke PBX側の着信ルーティング設定 |
| 6 | FAQサブフロー（RAG検索）を使用するかどうか | フロー構成 |
| 7 | Brekeke上のグループ名（「恵佑会札幌」で正しいか） | フロー名 `恵佑会札幌$診療` |
| 8 | 対象環境の確認（デモ/本番） | プロパティファイルの選択 |

---

## 7. 次のステップ

```bash
# Step 1: 校閲
# @reviewer output/json/draft_恵佑会札幌病院_診療.json を校閲して

# Step 2: 再検品
python3 schemas/validator.py output/json/draft_恵佑会札幌病院_診療.json

# Step 3: BLOCKER解消後、office_idを置換
# sed -i 's/TODO_office_id/実際のID/g' output/properties_恵佑会札幌病院_診療_demo.md
# sed -i 's/TODO_office_id/実際のID/g' output/properties_恵佑会札幌病院_診療_prod.md
# sed -i 's/TODO_office_id/実際のID/g' output/properties_恵佑会札幌病院_診療.md

# Step 4: .bivr生成（メインフロー + 4サブフロー）
python3 scripts/build_bivr.py \
  output/json/draft_恵佑会札幌病院_診療.json \
  output/json/draft_恵佑会札幌病院_氏名聴取.json \
  output/json/draft_恵佑会札幌病院_生年月日聴取.json \
  output/json/draft_恵佑会札幌病院_電話番号聴取.json \
  output/json/draft_恵佑会札幌病院_診察券番号聴取.json \
  -o output/bivr/恵佑会札幌病院_診療.bivr
```
