# IVRプロパティ: イーストMC 健診フロー

> デモ環境設定

## メインフロー (イーストMC$健診_20260406)

非通知_アナウンス=TODO_発話内容を記入
時間外_アナウンス=TODO_発話内容を記入
冒頭_アナウンス=TODO_発話内容を記入
用件_確認=TODO_発話内容を記入
END_聴取失敗=TODO_発話内容を記入
健保_組合=TODO_発話内容を記入
受診コース=TODO_発話内容を記入
予約希望_時期=TODO_発話内容を記入
追加_質問_予約=TODO_発話内容を記入
予約日_変更=TODO_発話内容を記入
変更_内容=TODO_発話内容を記入
追加_質問_変更=TODO_発話内容を記入
予約日_キャンセル=TODO_発話内容を記入
追加_質問_キャンセル=TODO_発話内容を記入
問合せ_内容=TODO_発話内容を記入
追加_質問_問合せ=TODO_発話内容を記入
END_企業案内=TODO_発話内容を記入
END_予約等=TODO_発話内容を記入
END_キャンセル=TODO_発話内容を記入

## 氏名聴取サブフロー (イーストMC$氏名聴取_20260406)

患者_氏名=TODO_発話内容を記入

## 生年月日聴取サブフロー (イーストMC$生年月日聴取_20260406)

患者_生年月日=TODO_発話内容を記入

## 電話番号聴取サブフロー (イーストMC$電話番号聴取_20260406)

復唱_患者_連絡先=prompt={tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone">#data#</say-as></speak>、でよろしいですか？}
患者_連絡先=TODO_発話内容を記入
患者_携帯=prompt={tts_g:ご連絡先の電話番号は、今おかけいただいている、<speak><say-as interpret-as="telephone">#data#</say-as></speak>、でよろしいですか？}

---

# 環境設定 (デモ)

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