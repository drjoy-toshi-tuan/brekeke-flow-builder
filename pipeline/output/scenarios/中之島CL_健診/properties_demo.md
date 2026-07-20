# IVRプロパティ — 中之島CL$健診 (デモ環境)
# 生成日: 2026-03-31
# 対象フロー: 中之島CL$健診 + サブフロー2本（氏名聴取・電話番号聴取）
# 環境: デモ
# 設計書: 設計書_中之島CL_健診.md v2

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
amivoice.probability=0.6
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

## TTSプロンプト — メインフロー（中之島CL$健診）

```properties
# 冒頭チェーン
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。お問い合わせの施設をお選びください。}

# 施設選択
施設_選択.prompt={tts_g: 中之島クリニックの方は1を、中之島クリニックレディースプラザの方は2を押してください。}
リトライ_施設_選択.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_施設_選択.prompt_false={tts_g: 申し訳ございません。正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}

# 用件選択
用件_選択.prompt={tts_g: この電話は1分程度で終わります。内容を正確に把握するために3点の質問にご協力ください。まず、ご用件をお選びください。人間ドックや健診のご予約は1を、それ以外のお問い合わせは2を押してください。}
リトライ_用件_選択.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_用件_選択.prompt_false={tts_g: 申し訳ございません。正しく聞き取ることができませんでした。}

# 問合せ内容（その他ルート）
問合せ_内容.prompt={tts_g: 改めて内容を確認のうえ、のちほど折り返しご連絡いたしますが、本日はどのようなご用件でしょうか。}
リトライ_問合せ_内容.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_問合せ_内容.prompt_false={tts_g: 申し訳ございません。正しく聞き取ることができませんでした。}

# 時間外・非通知
時間外_アナウンス.prompt={tts_g: 申し訳ございませんが、ただいまの時間は受付時間外となっております。受付時間は、祝日を除く月曜から土曜の9時から15時です。恐れ入りますが、受付時間内におかけ直しください。お電話ありがとうございました。}
# [WARNING] 非通知_アナウンス: 設計書に文言未確定（TODO_要確認）。仮文言を設定。
非通知_アナウンス.prompt={tts_g: 恐れ入りますが、電話番号を通知しておかけ直しください。}
```

---

## TTSプロンプト — 氏名聴取サブフロー（中之島CL$氏名聴取）

```properties
氏名_聴取.prompt={tts_g: 予約内容を正確に把握するため、お名前をお話しください。}
リトライ_氏名.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_氏名.prompt_false={tts_g: 申し訳ございません。正しく聞き取ることができませんでした。}
```

---

## TTSプロンプト — 電話番号聴取サブフロー（中之島CL$電話番号聴取）

```properties
# 携帯パス — 着信番号復唱確認
# [NOTE] 携帯_確認 (Re-confirmation) の prompt はJSONのparams内に直接定義済み:
# {tts_g: <speak>ご連絡先の電話番号は、今おかけいただいている、<say-as interpret-as="telephone">#data#</say-as>、でよろしいでしょうか。1、はい。2、いいえ。</speak>}
リトライ_携帯_確認.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_携帯_確認.prompt_false={tts_g: 申し訳ございません。正しく聞き取ることができませんでした。}

# その他パス — 電話番号聴取
電話番号_聴取.prompt={tts_g: 折り返しご連絡のため、電話番号をお話ください。}
リトライ_電話番号.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_電話番号.prompt_false={tts_g: 申し訳ございません。折り返し先のお電話番号を聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。}

# 電話番号確認（Re-confirmation）
# [NOTE] 電話番号_確認 (Re-confirmation) の prompt はJSONのparams内に直接定義済み:
# {tts_g: <speak>連絡先の電話番号は、<say-as interpret-as="telephone">#data#</say-as>、でよろしいでしょうか。1、はい。2、いいえでお答えください。</speak>}
リトライ_電話番号_確認.prompt_true={tts_g: 申し訳ございません。うまく聞き取りができませんでした。再度、}
リトライ_電話番号_確認.prompt_false={tts_g: かしこまりました。}

# 電話番号訂正
電話番号_訂正.prompt={tts_g: 正しい電話番号を再度お話しください。}

# ─── 終話チェーン ───

# 正常終話（人間ドック — 中之島CL/レディース共通TTS）
END_人間ドック.prompt={tts_g: 人間ドックのご連絡を承りました。担当者からの連絡にて確定となります。なお、この後届くショートメッセージのURLから項目の入力をお願いいたします。お電話ありがとうございました。}

# 正常終話（その他 — 中之島CL/レディース共通TTS）
END_その他.prompt={tts_g: ご用件をお預かりいたしました。担当者から折り返し電話、もしくはショートメッセージにてご連絡いたします。お電話ありがとうございました。}

# 異常終話（電話番号リトライ上限到達）
END_上限到達エラー.prompt={tts_g: 申し訳ございません。折り返し先のお電話番号を聞き取ることができませんでした。恐れ入りますが、コールセンターへおかけ直しください。お電話ありがとうございました。}
```

---

## 要設定項目（人間が設定すること）

- [ ] `office_id` を実際の施設IDに置換（現在: `TODO_要確認`）
- [ ] `非通知_アナウンス` の文言確認（設計書に未確定。仮文言を設定済み）
- [ ] `smsFlag` の 1,2,4,5 割り当てが本番環境と一致しているか確認
- [ ] `classification` が全ケースで「問合せ」で正しいか確認
