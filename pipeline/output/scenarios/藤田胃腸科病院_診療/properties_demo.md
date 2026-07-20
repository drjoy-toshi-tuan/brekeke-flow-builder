# IVRプロパティ — 藤田胃腸科病院_診療（デモ環境）

> 生成日: 2026-04-08
> 環境: デモ

---

```
# --- フロー: 藤田胃腸科病院$診療_20260408 ---
冒頭.wait=2000
END_非通知.prompt=TODO_発話内容を記入
END_時間外.prompt=TODO_発話内容を記入
冒頭_アナウンス.prompt=TODO_発話内容を記入
本人確認.prompt=TODO_発話内容を記入
入電者_氏名.prompt=TODO_発話内容を記入
用件1.prompt=TODO_発話内容を記入
通院歴.prompt=TODO_発話内容を記入
診察_予約希望日.prompt=TODO_発話内容を記入
END_再診.prompt=TODO_発話内容を記入
用件2.prompt=TODO_発話内容を記入
検査_受診希望日.prompt=TODO_発話内容を記入
検査_内容.prompt=TODO_発話内容を記入
ドック_受診希望人数_希望日.prompt=TODO_発話内容を記入
ドック_受診希望コース.prompt=TODO_発話内容を記入
健診_受診希望日.prompt=TODO_発話内容を記入
健診_予約希望内容.prompt=TODO_発話内容を記入
用件3.prompt=TODO_発話内容を記入
変更_予約日.prompt=TODO_発話内容を記入
変更_予約希望日.prompt=TODO_発話内容を記入
キャンセル_予約日.prompt=TODO_発話内容を記入
確認_内容確認.prompt=TODO_発話内容を記入
その他_問い合わせ.prompt=TODO_発話内容を記入
END_上限エラー.prompt=TODO_発話内容を記入
END_キャンセル.prompt=TODO_発話内容を記入
END_診察予約.prompt=TODO_発話内容を記入
END_健診等_携帯.prompt=TODO_発話内容を記入
END_健診等_固定.prompt=TODO_発話内容を記入

# --- フロー: 藤田胃腸科病院$氏名聴取_20260408 ---
患者_氏名.prompt=TODO_発話内容を記入

# --- フロー: 藤田胃腸科病院$生年月日聴取_20260408 ---
患者_生年月日.prompt=TODO_発話内容を記入

# --- フロー: 藤田胃腸科病院$電話番号聴取_20260408 ---
患者_連絡先.prompt=TODO_発話内容を記入

# --- 環境設定（デモ）---
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
