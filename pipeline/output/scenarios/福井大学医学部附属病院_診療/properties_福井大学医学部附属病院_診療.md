# IVR プロパティ — 福井大学医学部附属病院 診療

> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。
> `TODO_` で始まる値は実際の値に置き換えてから使用してください。

```
# アナウンス（TTS prompt）
END_非通知.prompt={tts_g:TODO_発話内容を記入}
END_時間外.prompt={tts_g:TODO_発話内容を記入}
END_聴取失敗.prompt={tts_g:TODO_発話内容を記入}
END_別窓口案内.prompt={tts_g:TODO_発話内容を記入}
END_変更.prompt={tts_g:TODO_発話内容を記入}
END_キャンセル.prompt={tts_g:TODO_発話内容を記入}
END_取得不可.prompt={tts_g:TODO_発話内容を記入}
冒頭_アナウンス.prompt={tts_g:福井大学医学部附属病院の、予約専用AI電話です。お手元に診察券をご準備の上、お話しください。}
用件確認.prompt={tts_g:ご用件を、次のいずれかでお話ください。1、予約の変更、2、予約のキャンセル。それではお話しください。}
用件再聴取.prompt={tts_g:申し訳ございません。うまく聞き取ることができませんでした。今回お電話いただいたご用件をお話しください。}
変更_4診療日以降確認.prompt={tts_g:変更される予約日は、本日から、土日祝を除く、4日後以降でしょうか。はい、もしくは、いいえ、でお答えください。わからない場合は、「わからない」とお話しください。}
変更_予約日.prompt={tts_g:次に、現在の予約日をお話しください。}
変更_変更希望日.prompt={tts_g:次に、変更希望日をお伺いいたします。ご都合の良い日付や曜日をお話しください。決まっていない場合は、決まっていない、とお話しください。}
変更_理由.prompt={tts_g:変更の理由をお話しください。}
キャンセル_予約日.prompt={tts_g:次に、現在の予約日をお話しください。}
キャンセル_理由.prompt={tts_g:キャンセルの理由をお話しください。}
診療科_共通.prompt={tts_g:次に、診療科をお話しください。わからない場合は、「わからない」とお話しください。}
折返し希望時間聴取.prompt={tts_g:折返しを希望される時間帯があればお話しください。なお、折り返しは、平日13時から17時のみの対応となります。特に希望がなければ、「特にないです」とお話しください。}
その他聴取.prompt={tts_g:その他に何かお問い合わせはありませんか？}

# サブフローTTS
患者_診察券番号.prompt={tts_g:診察券番号をお伝えください。}
患者_氏名.prompt={tts_g:お名前をフルネームでお伝えください。}
患者_生年月日.prompt={tts_g:生年月日を西暦でお伝えください。}
患者_連絡先.prompt={tts_g:ご連絡先の電話番号をお伝えください。}
相談_問合せ.prompt={tts_g:ご質問内容をお話しください。}
相談_問合せループ.prompt={tts_g:他にご質問はございますか。ご質問がなければ「ありません」とお伝えください。}
相談_FAQ失敗.prompt={tts_g:申し訳ございません。お調べすることができませんでした。}
終話_失敗.prompt={tts_g:TODO_発話内容を記入}

# wait
冒頭.wait=2000

# 施設固有（要編集）
office_id=TODO_要確認

# 環境設定
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

## TODO リスト

- [ ] `office_id` を設定する
- [ ] 以下のモジュールにアナウンス文言を記入する:
  - `END_非通知`
  - `END_時間外`
  - `END_聴取失敗`
  - `END_別窓口案内`
  - `END_変更`
  - `END_キャンセル`
  - `END_取得不可`
  - `終話_失敗`

> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` はIVRプロパティには記述しない。フローJSON内の params に直接記述すること。
