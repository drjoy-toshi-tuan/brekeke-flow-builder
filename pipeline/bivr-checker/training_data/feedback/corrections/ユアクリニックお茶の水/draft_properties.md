# IVRプロパティ — ユアクリニックお茶の水 診療
# 生成日: 2026/04/02（設計書第3版に基づき更新）
# 環境: デモ
# 対象フロー: ユアCLお茶水$診療 + ユアCLお茶水$氏名聴取 + ユアCLお茶水$電話番号聴取
#
# 注意: BLOCKERあり（B-1: office_id未確定 / B-2: デモ050番号未定）
# 本番環境への切り替え時は env_prod.txt の設定値を使用してください。

---

## メインフロー (ユアCLお茶水$診療)

# --- 冒頭 ---
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。ユアクリニックお茶の水のAI電話です。全部で3つ質問をさせていただきます。}

# --- 時間外（AI聴取続行型）---
時間外_アナウンス.prompt={tts_g: ただいまのお時間は診療時間外です。救急の方は東京都医療機関案内サービス、ひまわり03-5272-0303におかけください。当院へお問い合わせの方は、この後にご用件をお伺いいたします。内容確認後、院内スタッフから翌営業日終了までにショートメッセージもしくはお電話にてご連絡いたします。全部で3つ質問をさせていただきます。}

# --- 非通知 ---
非通知_アナウンス.prompt={tts_g: 恐れ入りますが、電話番号を通知しておかけ直しください。}

# --- 代表転送（受付時間判定 true_transfer ルート）---
転送_アナウンス.prompt={tts_g: 只今のお時間は、スタッフへお繋ぎいたします。代表電話に転送いたしますのでそのままお待ちください。}

# --- 転送失敗（回線混雑）---
転送失敗_アナウンス.prompt={tts_g: 申し訳ございません。只今お電話が込み合っております。恐れ入りますが、お時間を空けて再度おかけなおしください。お電話ありがとうございました。それでは失礼いたします。}

# --- 問い合わせ内容聴取 ---
問い合わせ内容_聴取.prompt={tts_g: まずは1つ目の質問です。本日のお問い合わせ内容をお話ください。それではどうぞ。}

# --- リトライ失敗 → 代表転送（営業時間内）---
転送_リトライ失敗_アナウンス.prompt={tts_g: 申し訳ございません、うまく認識ができませんでした。代表電話に転送いたしますのでそのままお待ちください。}

# --- 終話: 受付完了（通常時間帯）---
END_受付完了.prompt={tts_g: ありがとうございます。質問は以上です。内容確認後、院内スタッフから土・日、祝日を除く2日以内にショートメッセージもしくはお電話にてご連絡いたします。}

# --- 終話: 時間外受付完了 ---
END_時間外受付完了.prompt={tts_g: ありがとうございます。質問は以上です。内容確認後、院内スタッフから翌営業日終了までにショートメッセージもしくはお電話にてご連絡いたします。}

# --- 終話: リトライ上限エラー（時間外）---
END_上限エラー.prompt={tts_g: 大変申し訳ございません。ご回答を聞き取ることができませんでした。恐れ入りますが、改めておかけなおしください。お電話ありがとうございました。それでは失礼いたします。}

---

## 氏名聴取サブフロー (ユアCLお茶水$氏名聴取)

# --- 氏名聴取 ---
患者_氏名.prompt={tts_g: かしこまりました。続いて2つ目の質問です。お名前をフルネームでお話ください。それではどうぞ。}

---

## 電話番号聴取サブフロー (ユアCLお茶水$電話番号聴取)

# --- 連絡先電話番号聴取 ---
患者_連絡先.prompt={tts_g: ありがとうございます。それでは、最後の質問です。ご連絡先のお電話番号をお伺いします。折返しの電話番号は、ただいまおかけいただいている番号でよろしいでしょうか？はいの場合は1を、いいえの場合は2を、ダイヤルプッシュで入力してください。}

# Re-confirmation node data モジュールは params.prompt に直接設定済み
# 患者_携帯: 「ご連絡先の電話番号は、今おかけいただいている、{電話番号}、でよろしいですか？」
# 復唱_患者_連絡先: 「ご連絡先の電話番号は、{電話番号}、でよろしいですか？」

---

## 環境設定 (デモ)

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
