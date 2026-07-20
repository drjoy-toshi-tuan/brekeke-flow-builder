# IVRプロパティ — 海老名病院$個人情報聴取 (デモ)
# 生成日: 2026-03-26

## TTSプロンプト
```
診察券番号.prompt={tts_g: 診察券番号をお伺いします。10桁以内の診察券番号をお話ください。番号がわからない場合は、「わからない」とお話ください。}
診察券番号_再聴取.prompt={tts_g: 恐れ入りますが再度、診察券番号をお伺いします。10桁以内の診察券番号をお話ください。番号がわからない場合は、「わからない」とお話ください。}
患者名.prompt={tts_g: 患者さんのお名前を、フルネームでお話ください。}
生年月日.prompt={tts_g: 患者さんの、生年月日をお話ください。ダイヤルプッシュの場合は、8桁で入力してください。}
生年月日_再聴取.prompt={tts_g: 恐れ入りますが再度、患者さんの、生年月日をお話ください。ダイヤルプッシュの場合は、8桁で入力してください。}
生年月日_00_07確認.prompt={tts_g: 令和ですか？平成ですか？}
生年月日_08_31確認.prompt={tts_g: 西暦ですか？または昭和、平成ですか？}
生年月日_32_63確認.prompt={tts_g: 西暦ですか？昭和ですか？}
連絡先電話番号_確認.prompt={tts_g: ご連絡先のお電話番号は、今おかけいただいている<speak type="telephone" breakc="300ms">{telephoneNumber}</speak>でよろしいですか？}
連絡先電話番号_確認_再聴取.prompt={tts_g: ご連絡先のお電話番号は、今おかけいただいている<speak type="telephone" breakc="300ms">{telephoneNumber}</speak>でよろしいですか？}
連絡先電話番号_手動聴取.prompt={tts_g: ご連絡先の電話番号を、0から始まる市外局番から、または携帯番号でお話ください。}
連絡先電話番号_手動再聴取.prompt={tts_g: 再度電話番号をお話ください。}
最後の問い合わせ.prompt={tts_g: 他にご用件はございますか？}
END_電話番号聴取失敗.prompt={tts_g: ご回答の確認ができませんでしたのでこちらからお電話失礼させていただきます。それでは失礼いたします。}
END_受付完了.prompt={tts_g: 受付いたしました。3営業日以内に担当者から折り返し電話、もしくは、ショートメールにてご連絡いたします。ご連絡がいくまでは確定ではありません。お電話ありがとうございました。それでは失礼いたします。}
```

## Retry Counterプロンプト
```
リトライ_診察券番号.prompt_true={tts_g: もう一度、診察券番号をお話ください。}
リトライ_診察券番号.prompt_false={tts_g: }
リトライ_診察券番号_再聴取.prompt_true={tts_g: もう一度、診察券番号をお話ください。}
リトライ_診察券番号_再聴取.prompt_false={tts_g: }
リトライ_患者名.prompt_true={tts_g: もう一度、患者さんのお名前をフルネームでお話ください。}
リトライ_患者名.prompt_false={tts_g: }
リトライ_生年月日.prompt_true={tts_g: もう一度、生年月日をお話ください。}
リトライ_生年月日.prompt_false={tts_g: }
リトライ_生年月日_再聴取.prompt_true={tts_g: もう一度、生年月日をお話ください。}
リトライ_生年月日_再聴取.prompt_false={tts_g: }
リトライ_生年月日_00_07確認.prompt_true={tts_g: もう一度、令和ですか？平成ですか？}
リトライ_生年月日_00_07確認.prompt_false={tts_g: }
リトライ_生年月日_08_31確認.prompt_true={tts_g: もう一度、西暦ですか？または昭和、平成ですか？}
リトライ_生年月日_08_31確認.prompt_false={tts_g: }
リトライ_生年月日_32_63確認.prompt_true={tts_g: もう一度、西暦ですか？昭和ですか？}
リトライ_生年月日_32_63確認.prompt_false={tts_g: }
リトライ_連絡先電話番号_確認.prompt_true={tts_g: もう一度、着信番号でよろしいですか？}
リトライ_連絡先電話番号_確認.prompt_false={tts_g: }
リトライ_連絡先電話番号_確認_再聴取.prompt_true={tts_g: もう一度、着信番号でよろしいですか？}
リトライ_連絡先電話番号_確認_再聴取.prompt_false={tts_g: }
リトライ_連絡先電話番号_手動聴取.prompt_true={tts_g: もう一度、電話番号をお話ください。}
リトライ_連絡先電話番号_手動聴取.prompt_false={tts_g: }
リトライ_連絡先電話番号_手動再聴取.prompt_true={tts_g: もう一度、電話番号をお話ください。}
リトライ_連絡先電話番号_手動再聴取.prompt_false={tts_g: }
リトライ_最後の問い合わせ.prompt_true={tts_g: 他にご用件はございますか？}
リトライ_最後の問い合わせ.prompt_false={tts_g: }
```

## 環境設定
```
amivoice.uri=ws://10.0.20.11:8000/ws
office_id={TBD}
context.settings.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model
rag_ssml.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text
speech.rag.url=http://10.0.20.11:8000/api/v1/rag
```