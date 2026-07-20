# IVRプロパティ — 小林病院 診療（デモ環境）

> 本ファイルはBrekeke IVR設定画面のプロパティ欄に貼り付けるための設定ファイルです。
> 本体フロー + 全サブフロー（氏名聴取・生年月日聴取・電話番号聴取・診察券番号聴取）の設定を1ファイルに統合しています。

---

## TTS発話内容

```
# === 小林病院$診療_20260407 ===
非通知_アナウンス={tts_g:恐れ入りますが、お電話番号の通知をお願いいたします。電話番号の前に186をつけて、おかけ直しください。}
冒頭_アナウンス={tts_g:お電話ありがとうございます。 小林病院の、予約専用、AI電話です。}
診療科_聴取={tts_g:初めに、問い合わせをしたい診療科名をお話ください。}
用件確認_整形={tts_g:ご用件を、次の3つのうちの、いずれかでお話ください。 「予約を取る」「予約を変更する」「予約をキャンセルする」、 それでは、お話ください。}
受診歴_確認={tts_g:診察のご予約ですね。当院でのご受診は初めてですか。}
END_代表案内_新規不可={tts_g:整形外科の新規予約については、AI電話では受付できませんので、代表電話の、0157-23-5171、へおかけ直しください。繰り返します。代表電話番号は、0157-23-5171、です。繰り返します。代表電話番号は、0157-23-5171、です。それでは失礼いたします。}
希望医師名_聴取={tts_g:受診を希望する医師の名前をお話ください。特にない場合は、「無い」とお答えください。}
日程確認_整形={tts_g:今回のお問い合わせは、本日または翌診療日の予約に関する内容ですか。「はい」または「いいえ」でお答えください。}
用件確認_健診={tts_g:ご用件を、次の3つのうちの、いずれかでお話ください。 「予約を取る」「予約を変更する」「予約をキャンセルする」、 それでは、お話ください。}
日程確認_健診={tts_g:今回のお問い合わせは、本日または翌診療日の予約に関する内容ですか。「はい」または「いいえ」でお答えください。}
用件確認_その他={tts_g:ご用件を、次の2つのうちの、いずれかでお話ください。 「予約を変更する」「予約をキャンセルする」、 それでは、お話ください。}
日程確認_その他={tts_g:今回のお問い合わせは、本日または翌診療日の予約に関する内容ですか。「はい」または「いいえ」でお答えください。}
予約日_聴取={tts_g:予約票に記載されている予約日を「4月1日」のように日付でお話ください。}
END_代表案内_当日翌日不可={tts_g:当日と翌診療日のご予約については、AI電話では受付できませんので、代表電話の、0157-23-5171、へおかけ直しください。繰り返します。代表電話番号は、0157-23-5171、です。繰り返します。代表電話番号は、0157-23-5171、です。それでは、失礼いたします。}

# === 小林病院$氏名聴取_20260407 ===
患者_氏名={tts_g:お名前をお話ください。}

# === 小林病院$生年月日聴取_20260407 ===
患者_生年月日={tts_g:生年月日を、西暦または和暦でお話ください。}

# === 小林病院$電話番号聴取_20260407 ===
患者_連絡先={tts_g:ご連絡先のお電話番号を教えてください。}
その他問い合わせ_確認={tts_g:そのほかに何かお問い合わせはありませんか。}
END_受付完了={tts_g:ご予約の受付が完了いたしました。担当者から折り返しご連絡いたします。それでは失礼いたします。}

# === 小林病院$診察券番号聴取_20260407 ===
患者_診察券番号={tts_g:診察券番号を数字でお話しいただくか、またはプッシュしてください。}
```

---

## 環境設定（デモ）

```
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
