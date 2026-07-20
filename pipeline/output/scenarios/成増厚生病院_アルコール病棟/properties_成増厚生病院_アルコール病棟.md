# IVRプロパティ — 成増厚生病院 アルコール病棟（デモ環境）

> 生成日: 2026-04-13
> 対象フロー: な_成増厚生病院$アルコール病棟_20260413
> 環境: デモ
> サブフロー: な_成増厚生病院$電話番号聴取_20260413 / な_成増厚生病院$RAG検索_20260413

---

## 環境設定

```properties
# wait
冒頭.wait=2000

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.7
amivoice.detection_flag=音声開始前から検出
amivoice.save_log=false

# Save2DB / PBX
office_id=TODO_要確認
pbx.db.name=save.db
context.settings.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/incoming-call-by-brekeke

# OpenAI SSML
rag_ssml.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text

# RAG
speech.rag.url=http://10.0.20.11:8000/api/v1/rag
speech.rag.connect_timeout=2
speech.rag.request_timeout=3
speech.rag.credibility=0
```

---

## TTSプロンプト — メインフロー

```properties
# 冒頭アナウンス
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。成増厚生病院東京アルコール医療総合センターです。この電話はAI電話で対応させていただきます。ご用件をお伺いしたあと、折り返しご連絡させていただきます。}

# 非通知案内
非通知_アナウンス.prompt={tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}

# 時間外案内
時間外_アナウンス.prompt={tts_g:お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。}

# 電話口氏名聴取
電話口氏名.prompt={tts_g:お電話口の方のお名前を、フルネームでお話しください。}

# 患者本人確認
患者本人確認.prompt={tts_g:お電話口の方は患者様ご本人ですか？}

# 患者名聴取（代理人の場合のみ）
患者名.prompt={tts_g:患者さんのお名前を、フルネームでお話しください。}

# 受診歴入院歴確認
受診歴入院歴.prompt={tts_g:当院に受診歴や入院歴はありますか？}

# 用件確認
用件確認.prompt={tts_g:本日のご用件は、入院治療に関するご相談でしょうか？お問い合わせでしょうか？}

# 新規/継続確認（入院治療ルートのみ）
新規継続.prompt={tts_g:新規のご相談ですか？継続中のご相談ですか？}

# 受付完了終話（携帯）
END_受付完了.prompt={tts_g:相談員から折り返しご連絡させていただきます。平日10時から17時の間に折り返します。お電話ありがとうございました。それでは失礼いたします。}

# 受付完了終話（固定電話・その他）
END_受付完了_SMS無し.prompt={tts_g:相談員から折り返しご連絡させていただきます。平日10時から17時の間に折り返します。お電話ありがとうございました。それでは失礼いたします。}

# 聴取失敗終話
END_聴取失敗.prompt={tts_g:申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}
```

---

## TTSプロンプト — 電話番号聴取サブフロー（な_成増厚生病院$電話番号聴取_20260413）

```properties
# 連絡先電話番号聴取（固定/海外/その他パス）
患者_連絡先.prompt={tts_g:ご連絡先のお電話番号を教えてください。}
```

---

## TTSプロンプト — RAG検索サブフロー（な_成増厚生病院$RAG検索_20260413）

```properties
# 問い合わせ内容の聴取（初回発話）
# パターン3 inquiry: 問い合わせルートの初回案内
相談_問合せ.prompt={tts_g:お問い合わせ内容をご自由におっしゃってください。}

# ループ時（RAG回答後の再質問）
相談_問合せループ.prompt={tts_g:その他に何かご質問はございますか？ない場合は「ありません」のようにお話しください。}

# FAQ失敗時
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お答えできる情報が見つかりませんでした。}

# 失敗終話
終話_失敗.prompt={tts_g:申し訳ございません。正しくお聞き取りできませんでした。恐れ入りますが、おかけ直しください。}
```

---

> ⚠️ **要確認事項（人間が解消してください）**
> - `office_id`: TODO_要確認。設計書の confirmation_items 参照。
> - `acceptance_times` の受付時間帯: 設計書 Section 12 参照（business_hours = TODO_要確認）。
> - RAG検索サブフローの `相談_問合せ.prompt`: パターン3の2箇所目（終話前呼び出し）では「何かご質問はございますか？」に変更してもよい。サブフローを共用しているため現時点では統一テキストを設定。
