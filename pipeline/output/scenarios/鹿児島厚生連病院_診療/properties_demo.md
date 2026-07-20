# IVRプロパティ — 鹿厚連_診療 (デモ環境)

> 環境: デモ

## 本体フロー (鹿厚連$診療_20260403)

非通知_アナウンス={{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。}}

時間外_アナウンス={{tts_g:お電話ありがとうございます。鹿児島厚生連病院、診療予約専用、AI電話です。ただ今のお時間は、予約受付時間外となっております。7時から20時までにおかけ直しください。お電話ありがとうございました。}}

冒頭_アナウンス={{tts_g:お電話ありがとうございます。 鹿児島厚生連病院、診療予約専用、AI電話です。<break time="500ms"/>ただし本日の受診に関するお問い合わせは、代表電話へ、おかけ直しください。<break time="600ms"/>}}

診療科_アナウンス={{tts_g:診療科をお話しください。}}

用件_アナウンス={{tts_g:ご用件を次の4つのうちからお選びください。「1、予約」「2、予約変更」「3、予約キャンセル」「4、その他問い合わせ」。}}

予約希望時期_アナウンス={{tts_g:予約を希望する日程をお話しください。}}

変更_予約日_アナウンス={{tts_g:現在の予約日をお話しください。}}

変更_希望時期_アナウンス={{tts_g:予約を希望する日程をお話しください。}}

キャンセル_予約日_アナウンス={{tts_g:現在の予約日をお話しください。}}

キャンセル理由_アナウンス={{tts_g:キャンセル理由をお話しください。}}

次回予約希望_アナウンス={{tts_g:次回の予約希望はありますか。}}

キャンセル_変更_希望時期_アナウンス={{tts_g:予約を希望する日程をお話しください。}}

確認内容_アナウンス={{tts_g:お問い合わせの内容をお話しください。}}

FAQ確認_アナウンス={{tts_g:ほかにご用件やお問い合わせはございますか？}}

FAQ回答_アナウンス={{tts_g:TODO_発話内容を記入}}

FAQ非該当_アナウンス={{tts_g:TODO_発話内容を記入}}

終話_予約_アナウンス={{tts_g:依頼された内容は、まだ確定ではありません。お話していただいた内容を予約担当が確認し、土日祝日を除く3営業日以内にご連絡いたします。当院からのご連絡をお待ちください。お電話ありがとうございました。}}

終話_変更_アナウンス={{tts_g:依頼された内容は、まだ確定ではありません。お話していただいた内容を予約担当が確認し、土日祝日を除く3営業日以内にご連絡いたします。当院からのご連絡をお待ちください。お電話ありがとうございました。}}

終話_キャンセル_アナウンス={{tts_g:依頼された内容は、まだ確定ではありません。お話していただいた内容を予約担当が確認し、土日祝日を除く3営業日以内にご連絡いたします。当院からのご連絡をお待ちください。お電話ありがとうございました。}}

終話_その他問合せ_アナウンス={{tts_g:問い合わせの内容しだいで、土日祝日をのぞく3営業日以内に担当者から折り返しショートメールもしくは電話にてご連絡いたします。お電話ありがとうございました。}}

終話_失敗_アナウンス={{tts_g:申し訳ございません。うまく聞き取りができませんでした。恐れ入りますがおかけ直しください。お電話ありがとうございました。}}

## 診察券番号聴取 (鹿厚連$診察券番号聴取_20260403)

終話_失敗={{tts_g:TODO_発話内容を記入}}

患者_診察券番号={{tts_g:TODO_発話内容を記入}}

患者_生年月日={{tts_g:TODO_発話内容を記入}}

患者_連絡先={{tts_g:TODO_発話内容を記入}}

患者_氏名={{tts_g:TODO_発話内容を記入}}

## 氏名聴取 (鹿厚連$氏名聴取_20260403)

患者_氏名={{tts_g:TODO_発話内容を記入}}

## 生年月日聴取 (鹿厚連$生年月日聴取_20260403)

患者_生年月日={{tts_g:TODO_発話内容を記入}}

## 電話番号聴取 (鹿厚連$電話番号聴取_20260403)

患者_連絡先={{tts_g:TODO_発話内容を記入}}


---

## 環境設定 (デモ)

```
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
```