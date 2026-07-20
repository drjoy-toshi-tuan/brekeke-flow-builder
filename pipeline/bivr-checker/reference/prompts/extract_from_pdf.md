# PDF構造化パーサー プロンプトテンプレート

**用途**: 設計書PDFを読んで、VFBフロー生成に必要な情報を構造化JSONとして抽出する。
**想定LLM**: Claude（PDFアップロード対応のもの）
**出力**: 後続の `build_bivr.py` や手動フロー設計に直接使える構造化データ

---

## プロンプト（LLMに貼り付けて使用）

````
添付のPDFは医療機関の電話応対システム（ボイスボット）設計書です。
以下の構造化JSONを抽出・推定してください。

## 抽出ルール

### 原則
- PDF記載の情報を**そのまま抽出**する。推測・補完は禁止。
- 記載がない項目は `null` とする。
- 複数の解釈が可能な場合は `"ambiguous"` フィールドに理由を記載する。
- 診療科・用件など「一覧」として記載された情報はすべて配列で出力する。

### 抽出対象
以下の7セクションを順番に抽出する。

---

## 出力JSON仕様

```json
{
  "meta": {
    "facility_name": "施設名（PDFの表紙・ヘッダから抽出）",
    "facility_location": "所在地（都道府県・市区町村）",
    "flow_type": "診療 | 健診 | ワクチン | 問い合わせ | その他",
    "pdf_version": "PDF内のバージョン・日付（記載があれば）",
    "extracted_at": "今日の日付（YYYY-MM-DD形式）",
    "ambiguous": []
  },

  "acceptance_times": {
    "description": "受付時間の説明（PDFの文言そのまま）",
    "schedules": [
      {
        "days": ["月", "火", "水", "木", "金"],
        "start": "09:00",
        "end": "17:00",
        "note": "特記事項（祝日除く等）"
      }
    ],
    "outside_hours_action": "受付時間外のアクション（TTS文言またはアクション名）",
    "ambiguous": []
  },

  "classifications": {
    "description": "用件分岐の概要（予約/変更/キャンセル等）",
    "items": [
      {
        "label": "予約",
        "dtmf_key": "1",
        "keywords": ["よやく", "しんさつ"],
        "subflow": "診療予約フロー"
      }
    ],
    "input_method": "DTMF | STT | DTMF+STT",
    "ambiguous": []
  },

  "collection_fields": [
    {
      "context_name": "patientName",
      "label": "氏名",
      "required": true,
      "input_method": "STT",
      "retry_count": 2,
      "retry_failure_action": "next | hangup | loop",
      "reconfirm": false,
      "notes": "PDF記載の特記事項"
    },
    {
      "context_name": "patientDateOfBirth",
      "label": "生年月日",
      "required": true,
      "input_method": "STT",
      "retry_count": 2,
      "retry_failure_action": "next",
      "reconfirm": true,
      "notes": null
    },
    {
      "context_name": "clinicalDepartment",
      "label": "診療科",
      "required": true,
      "input_method": "DTMF+STT",
      "retry_count": 2,
      "retry_failure_action": "loop",
      "reconfirm": false,
      "notes": null
    },
    {
      "context_name": "medicalCardNumber",
      "label": "診察券番号",
      "required": false,
      "input_method": "DTMF+STT",
      "retry_count": 2,
      "retry_failure_action": "next",
      "reconfirm": true,
      "notes": "初診は不要"
    },
    {
      "context_name": "additionalPhoneNumber",
      "label": "連絡先電話番号",
      "required": false,
      "input_method": "STT",
      "retry_count": 2,
      "retry_failure_action": "next",
      "reconfirm": true,
      "notes": null
    }
  ],

  "clinical_departments": {
    "in_scope": [
      {
        "name": "内科",
        "reading": "ないか",
        "abbreviations": ["一般内科"],
        "note": null
      }
    ],
    "out_of_scope": [
      {
        "name": "救急科",
        "reading": "きゅうきゅうか",
        "reason": "電話受付対象外"
      }
    ],
    "ambiguous": []
  },

  "tts_scripts": {
    "opening": "冒頭アナウンスのTTS文言（PDFの文言そのまま）",
    "outside_hours": "受付時間外アナウンスのTTS文言",
    "classification_prompt": "用件を聞くTTS文言（例: ご用件をお聞かせください）",
    "retry_prompt_true": "リトライ時の固定文言（通常: 申し訳ございません。うまく聞き取りが出来ませんでした。再度、）",
    "retry_failed_message": "リトライ上限時のアナウンス文言",
    "closing_success": "正常終話のTTS文言",
    "closing_failure": "失敗終話のTTS文言",
    "transfer_announcement": "有人転送時のアナウンス文言",
    "custom": [
      {
        "label": "その他のTTS文言のラベル",
        "text": "TTS文言"
      }
    ]
  },

  "business_rules": {
    "retry_default": 2,
    "has_sms": null,
    "has_transfer": null,
    "transfer_number": null,
    "new_patient_flow": "初診の受付可否・フロー（null=不明）",
    "existing_patient_flow": "再診の受付フロー概要（null=不明）",
    "special_rules": [
      "PDF記載の特殊業務ルールをそのまま列挙"
    ],
    "ambiguous": []
  }
}
```

---

## フィールド補足説明

### `collection_fields[].context_name` の候補値

| context_name | 意味 |
|---|---|
| `patientName` | 氏名 |
| `patientDateOfBirth` | 生年月日 |
| `clinicalDepartment` | 診療科 |
| `medicalCardNumber` | 診察券番号 |
| `additionalPhoneNumber` | 連絡先電話番号 |
| `inquiry` | 問い合わせ内容・担当医名等 |
| `classification` | 用件区分 |
| `checkupCourse` | 健診コース（健診フローのみ） |
| `vaccinationType` | ワクチン種別（ワクチンフローのみ） |

### `collection_fields[].retry_failure_action` の意味

| 値 | 意味 |
|---|---|
| `next` | リトライ上限後、次の質問へ進む（任意項目に多い） |
| `hangup` | リトライ上限後、終話する |
| `loop` | リトライ上限後、同じ質問に戻る無限ループ（必須項目に多い） |

---

## 出力上の注意

1. JSON以外の説明文は不要。JSON本体のみ出力する。
2. PDFに記載がない項目は必ず `null`（文字列の "null" ではなく JSON の null）を使う。
3. `ambiguous` 配列には、複数の解釈があり判断できなかった箇所を日本語で記述する。
4. TTS文言は「{}や#data#等のテンプレート変数」も含めてPDF記載のまま抽出する。
5. 診療科は対象外のものも含めてすべて列挙する。
````

---

## 使い方

1. Claude.ai にPDF（設計書）をアップロードする
2. 上記プロンプトを貼り付けて送信する
3. 出力JSONを `input/{施設名}/spec.json` として保存する
4. `ambiguous` フィールドの内容を人間が確認し、追記・修正する
5. `spec.json` をもとにVFBへの入力・手動フロー設計・`profile_words` 生成を行う

## spec.json の活用先

| セクション | 活用先 |
|---|---|
| `acceptance_times` | `acceptance_times` モジュールの設定値 |
| `classifications` | 用件分岐のDTMF設定・OpenAIプロンプト |
| `collection_fields` | 聴取順序・リトライ設計・サブフロー選択 |
| `clinical_departments.in_scope` | `generate_profile_words.md` への入力 |
| `tts_scripts` | 各TTSモジュールの `prompt` 値 |
| `business_rules` | フロー設計の基本方針（転送番号・SMS有無等） |

## 注意事項

- PDFフォーマットは施設ごとに大きく異なるため、LLMの抽出精度にばらつきがある
- `ambiguous` が多い場合は設計者に確認してから進める
- 抽出結果はあくまで**ドラフト**。必ず人間がレビューしてから `.bivr` 生成に使用する
- TTS文言にPDFのページ番号・注釈が混入しないよう注意
