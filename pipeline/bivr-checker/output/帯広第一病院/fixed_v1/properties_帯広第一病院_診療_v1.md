# IVRプロパティ — 帯広第一病院 診療予約
# 環境: デモ
# 生成日: 2026-04-15
# 対象: 本体フロー + サブフロー4本（診察券番号・氏名・生年月日・電話番号）統合

```

# === メインフロー TTS ===
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。帯広第一病院の外来予約専用AI電話です。}
用件確認.prompt={tts_g:はじめに次の4つのうちのいずれかで、ご用件をお話しください。予約の方は1番、変更の方は2番、キャンセルの方は3番、確認は4番、それではお話ください。プッシュボタンでも操作可能です。}
用件確認_再聴取.prompt={tts_g:再度お伺いします。ご用件を、次の4つからお話ください。予約の方は1番、変更の方は2番、キャンセルの方は3番、確認は4番、それではお話ください。プッシュボタンでも操作可能です。}
通院歴確認.prompt={tts_g:今まで当院で受診されたことはありますか？「はい、あります。」「いいえ、ありません。」のようにお話しください。}
診療科聴取.prompt={tts_g:それでは、診療科をお話しください。分からない場合は「分からない」とお話ください。}
診療科_再聴取.prompt={tts_g:正確な診療科名称を聞き取る事ができませんでした。恐れ入りますが、診療科名を再度お話ください。}
追加診療科確認.prompt={tts_g:ほかに同日の予約を希望される診療科はございますか？ない場合は「ありません」とお話しください。}
現在の予約日.prompt={tts_g:現在の予約日をお話ください。分からない場合は「分からない」とお話ください。}
予約希望日.prompt={tts_g:予約を希望する日付を「7月1日」のようにお話ください。ない場合は「ありません」とお話しください。}
理由聴取.prompt={tts_g:変更の理由を簡潔にお話しください。}
内容確認.prompt={tts_g:確認したい内容を簡潔にお話しください。}
症状聴取.prompt={tts_g:症状について、簡潔にお話しください。}
最終確認.prompt={tts_g:その他確認事項がございましたら、お話しください。}
非通知_アナウンス.prompt={tts_g:帯広第一病院の外来予約専用AI電話です。申し訳ございません。非通知でのお電話は受付できません。発信者番号を通知するか、頭に186をつけて、再度おかけ直しください。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_携帯.prompt={tts_g:申し込みを受付いたしました。3診療日以内に、折り返しお電話、もしくはショートメールにてご連絡いたします。携帯電話でおかけの方はこのあと、ショートメッセージをお送りしますので、内容確認と修正をお願いいたします。お電話ありがとうございました。それでは失礼いたします。}
END_受付完了_固定.prompt={tts_g:申し込みを受付いたしました。3診療日以内に、折り返しお電話にてご連絡いたします。お電話ありがとうございました。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:キャンセルを受付いたしました。内容により、担当者からご連絡差し上げる可能性があります。お電話ありがとうございました。それでは失礼いたします。}
END_新規受診.prompt={tts_g:恐れ入りますが、新規のご受診については直接ご来院くださいますようお願いいたします。お電話ありがとうございました。それでは失礼いたします。}
END_脳神経外科.prompt={tts_g:脳神経外科は現在、当院では受け付けておりません。お電話ありがとうございました。それでは失礼いたします。}
END_代表案内.prompt={tts_g:ご希望の診療科は代表番号へお電話いただくようお願いいたします。お電話ありがとうございました。それでは失礼いたします。}
END_2診療日以内.prompt={tts_g:ご希望のお日にちについては、恐れ入りますが、代表番号へおかけ直しください。お電話ありがとうございました。それでは失礼いたします。}
END_聴取失敗.prompt={tts_g:ご回答の確認ができませんでしたので、こちらからお電話失礼させていただきます。それでは失礼いたします。}

# === サブフロー必須TTS（各サブフロー専用 Properties.md で管理）===

# === 環境設定（デモ） ===
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
office_id=
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