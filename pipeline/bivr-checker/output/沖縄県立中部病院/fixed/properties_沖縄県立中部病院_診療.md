# IVRプロパティ — 沖縄県立中部病院 診療

> 環境: demo
> 生成日: 2026-04-09
> 対象フロー: 沖縄県立中部病院$診療_20260409 および全サブフロー

---

## TTS発話テキスト

### メインフロー — 沖縄県立中部病院$診療_20260409

```
非通知_アナウンス=TODO_発話内容を記入
時間外_アナウンス=TODO_発話内容を記入
冒頭_アナウンス=TODO_発話内容を記入
通院確認=TODO_発話内容を記入
通院中以外受付不可_アナウンス=TODO_発話内容を記入
本人確認=TODO_発話内容を記入
診療科=TODO_発話内容を記入
用件確認=TODO_発話内容を記入
現在の予約日_変更=TODO_発話内容を記入
理由_変更=TODO_発話内容を記入
確認事項=TODO_発話内容を記入
END_予約日の確認=TODO_発話内容を記入
理由_キャンセル=TODO_発話内容を記入
現在の予約日_キャンセル=TODO_発話内容を記入
キャンセル時案内=TODO_発話内容を記入
END_予約のキャンセル=TODO_発話内容を記入
前回の予約日=TODO_発話内容を記入
取り直し受付不可_アナウンス=TODO_発話内容を記入
予約希望日=TODO_発話内容を記入
都合悪い日=TODO_発話内容を記入
その他共有事項=TODO_発話内容を記入
END_再診予約の変更=TODO_発話内容を記入
END_予約の取り直し=TODO_発話内容を記入
END_聴取失敗=TODO_発話内容を記入
```

### 診察券番号聴取サブフロー — 沖縄県立中部病院$診察券番号聴取_20260409

```
患者_診察券番号=TODO_発話内容を記入
```

### 氏名聴取サブフロー — 沖縄県立中部病院$氏名聴取_20260409

```
患者_氏名=TODO_発話内容を記入
```

### 生年月日聴取サブフロー — 沖縄県立中部病院$生年月日聴取_20260409

```
患者_生年月日=TODO_発話内容を記入
```

### 電話番号聴取サブフロー — 沖縄県立中部病院$電話番号聴取_20260409

```
患者_連絡先=TODO_発話内容を記入
```

### RAG検索サブフロー — 沖縄県立中部病院$RAG検索_20260409

```
相談_FAQ失敗=TODO_発話内容を記入
終話_失敗=TODO_発話内容を記入
相談_問合せ=TODO_発話内容を記入
相談_問合せループ=TODO_発話内容を記入
```

---

## 環境設定 (demo)

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
