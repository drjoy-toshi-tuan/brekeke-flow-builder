# IVRプロパティ — 朝日大学病院 診療フロー（デモ環境）
# 生成日: 2026-04-07
# 対象フロー: 朝日大学病院$診療_20260407 + サブフロー4本
# NOTE: office_id は TODO_要確認。確定後に context.settings.url の office_id パラメータを更新すること

## 朝日大学病院$診療_20260407

非通知_アナウンス.prompt={tts_g:お手数をおかけしますが、発信者番号を通知して再度お電話ください。電話番号の前に186を追加いただくことで発信者番号を通知していただくことができます。それでは失礼いたします。}
冒頭_アナウンス.prompt={tts_g:お電話ありがとうございます。朝日大学病院の予約専用AI電話です。}
用件確認.prompt={tts_g:ご用件を、「変更」「キャンセル」「予約確認」の中から1つ選んでお答えください。どうぞ。}
診療科_変更.prompt={tts_g:診療科をお話しください。わからない場合はわからないとお話しください。どうぞ。}
予約日_変更.prompt={tts_g:現在の予約日をお伺いいたします。それではお話しください。どうぞ。}
予約希望日.prompt={tts_g:予約希望日をお伺いいたします。本日より7診療日以降で担当医が診察する曜日の中からご都合のいいお日にちやお時間帯をお話しください。複数ある場合は複数お話しください。どうぞ。}
薬処方確認_変更.prompt={tts_g:病院からお薬を処方されている方は、「はい、飲んでいます」、と、されていない方は、「いいえ、飲んでいません」、とお答えください。どうぞ。}
残薬確認_変更.prompt={tts_g:残薬について確認をいたします。変更を希望するお日にちまでの残薬がある場合は「はい、あります」、無い場合は、「いいえ、ありません」、とお答えください。どうぞ。}
診療科_キャンセル.prompt={tts_g:診療科をお話しください。わからない場合はわからないとお話しください。どうぞ。}
予約日_キャンセル.prompt={tts_g:キャンセルを希望される予約日をお伺いいたします。どうぞ。}
薬処方確認_キャンセル.prompt={tts_g:病院からお薬を処方されている方は、「はい、飲んでいます」、と、されていない方は、「いいえ、飲んでいません」、とお答えください。どうぞ。}
残薬確認_キャンセル.prompt={tts_g:残薬について確認をいたします。残薬がある場合は「はい、あります」、無い場合は「いいえ、ありません」、とお答えください。どうぞ。}
キャンセル理由.prompt={tts_g:キャンセル理由をお話しください。どうぞ。}
内容確認.prompt={tts_g:本日より3営業日以内の予約に関するお問い合わせは、当院の代表電話へおかけ直しください。それでは、確認をしたい事項に関して、「次回の予約日を確認したい」など簡潔にお話しください。どうぞ。}
内容確認_受付.prompt={tts_g:ご質問いただいた内容は、折り返しでご確認させていただきます。}
携帯用の質問.prompt={tts_g:折り返しのご連絡方法に関して、ショートメールとお電話どちらをご希望でしょうか。お話しください。}
END_初診不可.prompt={tts_g:恐れ入りますが、初診の予約は受け付けておりません。診療時間内に直接お越し下さいませ。それでは失礼いたします。}
END_代表案内.prompt={tts_g:代表番号までお電話をお願いいたします。代表電話番号は、058-253-8001です。繰り返します。代表電話番号は、058-253-8001です。お電話ありがとうございました。それでは失礼いたします。}
END_代表案内2.prompt={tts_g:恐れ入りますが、残薬が無い方に関しては、こちらのお電話で受け付けることができません。当院の代表電話番号へおかけなおしくださいませ。それでは失礼いたします。}
END_キャンセル.prompt={tts_g:キャンセルの申し込みを受付しました。お電話ありがとうございました。それでは失礼いたします。}
END_変更_確認.prompt={tts_g:予約申し込みを受付いたしました。申込日から3診療日以内に担当者からショートメール、もしくは電話にてご連絡いたします。病院からの連絡を必ずご確認ください。それでは失礼いたします。}

## 朝日大学病院$氏名聴取_20260407

患者_氏名.prompt={tts_g:お名前をお伺いします。<break time="700ms"/>名前は朝日太郎です、<break time="700ms"/>のようにお答えください。どうぞ。}

## 朝日大学病院$生年月日聴取_20260407

患者_生年月日.prompt={tts_g:患者さんの生年月日を西暦からお話しください。}

## 朝日大学病院$診察券番号聴取_20260407

患者_診察券番号.prompt={tts_g:診察券番号をお話しください。番号がわからない場合は、「わからない」とお話しください。}

## 朝日大学病院$電話番号聴取_20260407

患者_連絡先.prompt={tts_g:ご連絡先のお電話番号を教えてください。どうぞ。}

# ========== 環境設定（デモ）==========
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