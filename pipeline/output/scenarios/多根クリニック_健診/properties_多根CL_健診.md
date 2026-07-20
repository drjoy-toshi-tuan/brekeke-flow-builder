# IVRプロパティ — 多根CL 健診_20260407

> 環境: デモ

## メインフロー (多根CL$健診_20260407)

tts_非通知_アナウンス={tts_g:TODO_発話内容を記入}
tts_時間外_アナウンス={tts_g:TODO_発話内容を記入}
tts_冒頭_アナウンス={tts_g:TODO_発話内容を記入}
tts_強制伝言_アナウンス={tts_g:TODO_発話内容を記入}
tts_復唱_予約={tts_g:TODO_発話内容を記入}
tts_予約案内={tts_g:TODO_発話内容を記入}
tts_復唱_変更キャンセル={tts_g:TODO_発話内容を記入}
tts_サブ選択_変更キャンセル={tts_g:TODO_発話内容を記入}
tts_復唱_紹介状受診結果={tts_g:TODO_発話内容を記入}
tts_サブ選択_紹介状受診結果={tts_g:TODO_発話内容を記入}
tts_紹介状案内={tts_g:TODO_発話内容を記入}
tts_医療機関名={tts_g:TODO_発話内容を記入}
tts_医師への質問={tts_g:TODO_発話内容を記入}
tts_復唱_問い合わせ={tts_g:TODO_発話内容を記入}
tts_個人企業分岐={tts_g:TODO_発話内容を記入}
tts_問い合わせ内容_個人={tts_g:TODO_発話内容を記入}
tts_問い合わせ内容_企業={tts_g:TODO_発話内容を記入}
tts_企業名={tts_g:TODO_発話内容を記入}
tts_保険者情報={tts_g:TODO_発話内容を記入}
tts_希望コース={tts_g:TODO_発話内容を記入}
tts_希望時期_人数={tts_g:TODO_発話内容を記入}
tts_その他_追加オプション={tts_g:TODO_発話内容を記入}
tts_END_予約={tts_g:TODO_発話内容を記入}
tts_予約日={tts_g:TODO_発話内容を記入}
tts_希望日={tts_g:TODO_発話内容を記入}
tts_END_日程変更={tts_g:TODO_発話内容を記入}
tts_予約日_キャンセル={tts_g:TODO_発話内容を記入}
tts_END_キャンセル={tts_g:TODO_発話内容を記入}
tts_END_受診結果_平日={tts_g:TODO_発話内容を記入}
tts_END_受診結果_土日={tts_g:TODO_発話内容を記入}
tts_END_紹介状={tts_g:TODO_発話内容を記入}
tts_END_問い合わせ={tts_g:TODO_発話内容を記入}

## 氏名聴取サブフロー (多根CL$氏名聴取_20260407)

tts_患者_氏名={tts_g:TODO_発話内容を記入}

## 生年月日聴取サブフロー (多根CL$生年月日聴取_20260407)

tts_患者_生年月日={tts_g:TODO_発話内容を記入}

## 電話番号聴取サブフロー (多根CL$電話番号聴取_20260407)

tts_患者_連絡先={tts_g:TODO_発話内容を記入}


---
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
