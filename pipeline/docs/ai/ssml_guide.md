# SSML（音声合成マークアップ言語）ガイド

> 出典: [W3C Speech Synthesis Markup Language (SSML) Version 1.0](https://www.w3.org/TR/speech-synthesis/)
>
> **スコープ**: IVRプロパティの TTS 発話テキスト内でSSMLタグを使い、イントネーション・ポーズ・発音を調整する方法。
> SSML対応はTTSエンジン依存。利用前に使用エンジンの対応状況を確認すること。

---

## SSML を使う場所

```
IVRプロパティ → TTS発話テキスト（{tts_g:...} で参照される文章）
```

TTSエンジンがSSMLをサポートしている場合、発話テキストにXMLタグを埋め込むことで読み上げを細かく制御できる。

---

## 1. ポーズ（間）の挿入: `<break>`

自然な間・間を空けたい場所に使う。

```xml
<!-- 時間指定 -->
<break time="500ms"/>   <!-- 0.5秒の間 -->
<break time="1s"/>      <!-- 1秒の間 -->
<break time="2s"/>      <!-- 2秒の間（長めの間） -->

<!-- 強度指定 -->
<break strength="x-weak"/>    <!-- ほぼ間なし -->
<break strength="weak"/>      <!-- 弱い間 -->
<break strength="medium"/>    <!-- 通常の間 -->
<break strength="strong"/>    <!-- 強い間（文と文の間に） -->
<break strength="x-strong"/>  <!-- 最も強い間（段落間に） -->
```

**病院ボイスボットでの活用例**:
```xml
<!-- 案内文で番号を読み上げる前に間を入れる -->
予約の方は1番、<break time="300ms"/>変更・キャンセルの方は2番、<break time="300ms"/>その他のお問い合わせは3番を押してください。

<!-- 重要な情報の前後に間を入れる -->
お待ちしております。<break time="1s"/>なお、診察券をお手元にご用意ください。
```

---

## 2. 発話速度・音程・音量の調整: `<prosody>`

```xml
<!-- 発話速度 -->
<prosody rate="slow">ゆっくり読み上げます</prosody>       <!-- 遅い（約0.64倍） -->
<prosody rate="medium">標準速度</prosody>                 <!-- 標準（デフォルト） -->
<prosody rate="fast">速く読み上げます</prosody>           <!-- 速い（約1.55倍） -->
<prosody rate="0.8">少しゆっくり（80%）</prosody>
<prosody rate="-20%">20%遅く</prosody>
<prosody rate="+30%">30%速く</prosody>

<!-- 音程（ピッチ） -->
<prosody pitch="high">高い音程</prosody>
<prosody pitch="low">低い音程</prosody>
<prosody pitch="+2st">2半音上げる</prosody>
<prosody pitch="-2st">2半音下げる</prosody>
<prosody pitch="+20%">20%高く</prosody>

<!-- 音量 -->
<prosody volume="loud">大きめ</prosody>
<prosody volume="soft">小さめ</prosody>
<prosody volume="+20%">20%大きく</prosody>
<prosody volume="-10%">10%小さく</prosody>

<!-- 複数属性の組み合わせ -->
<prosody rate="slow" pitch="-1st">大事な箇所をゆっくり低めに</prosody>
```

**病院ボイスボットでの活用例**:
```xml
<!-- リトライ時のアナウンスを少し遅めに -->
<prosody rate="0.85">恐れ入りますが、もう一度おっしゃっていただけますか。</prosody>

<!-- 終話アナウンスを落ち着いたトーンで -->
<prosody rate="slow" pitch="-1st">お電話ありがとうございました。またのお電話をお待ちしております。</prosody>

<!-- 注意事項を強調するために音量を上げる -->
<prosody volume="+15%">診察は予約の方のみとなっております。</prosody>
```

---

## 3. 強調: `<emphasis>`

```xml
<emphasis level="strong">強く強調</emphasis>      <!-- 音量・速度ともに変化 -->
<emphasis level="moderate">中程度の強調</emphasis>  <!-- デフォルトの強調 -->
<emphasis level="reduced">弱め</emphasis>           <!-- 軽い強調 -->
<emphasis level="none">強調なし</emphasis>          <!-- 通常に戻す -->
```

**病院ボイスボットでの活用例**:
```xml
ご予約は<emphasis level="strong">前日の午後5時まで</emphasis>に承っております。

<!-- 営業時間外アナウンスでの強調 -->
ただいまの時間は<emphasis level="moderate">受付時間外</emphasis>となっております。
```

---

## 4. 発音の明示指定: `<phoneme>`

医療用語・地名・人名など、TTSエンジンが誤読しやすい単語に使う。

```xml
<!-- IPA（国際音声記号）で指定 -->
<phoneme alphabet="ipa" ph="ないか">内科</phoneme>
<phoneme alphabet="ipa" ph="げか">外科</phoneme>

<!-- X-SAMPA形式 -->
<phoneme alphabet="x-sampa" ph="naika">内科</phoneme>
```

> **注意**: `phoneme` の対応はTTSエンジン・言語ロケール依存。日本語での動作確認が必要。
> 代替手段として `<sub>` 要素によるひらがな置換が有効な場合がある。

---

## 5. 読み方の置き換え: `<sub>`

表記と読み方を明示的に分ける。`phoneme` より対応エンジンが広い。

```xml
<sub alias="ないか">内科</sub>
<sub alias="げか">外科</sub>
<sub alias="さんがいじゅしんか">3階受診科</sub>

<!-- 略語の展開 -->
<sub alias="デーエムアール">DMR</sub>
<sub alias="しーてぃー">CT</sub>
```

**病院ボイスボットでの活用例**:
```xml
<sub alias="えむあーるあい">MRI</sub>の検査予約は、こちらの番号へお電話ください。
本日の<sub alias="にゅういんかんじゃ">入院患者</sub>様のご面会時間は午後2時から4時です。
```

---

## 6. 数値・日付・電話番号の読み上げ制御: `<say-as>`

```xml
<!-- 数字を1桁ずつ読む（電話番号・診察券番号） -->
<say-as interpret-as="characters">0120</say-as>    <!-- "ゼロイチニーゼロ" -->
<say-as interpret-as="telephone">03-1234-5678</say-as>

<!-- 日付 -->
<say-as interpret-as="date" format="ymd">2026/03/24</say-as>

<!-- 序数 -->
<say-as interpret-as="ordinal">1</say-as>   <!-- "1番目" など -->
```

---

## 7. 複合例（病院ボイスボット向け）

### 冒頭アナウンス（受付時間外）

```xml
ただいまの時間は<emphasis level="moderate">受付時間外</emphasis>となっております。
<break time="500ms"/>
受付時間は<prosody rate="0.85">平日の午前9時から午後5時</prosody>です。
<break time="300ms"/>
お急ぎの場合は、<say-as interpret-as="telephone">03-1234-5678</say-as>へお電話ください。
```

### リトライアナウンス

```xml
<prosody rate="0.85">恐れ入りますが、ご回答が確認できませんでした。</prosody>
<break time="400ms"/>
もう一度、<emphasis level="moderate">おっしゃっていただけますか。</emphasis>
```

### 予約確認の復唱

```xml
ご予約内容を確認いたします。<break time="500ms"/>
<prosody rate="0.8">
  お名前：<sub alias="やまだたろう">山田太郎</sub>様、
  <break time="300ms"/>
  診察日：<say-as interpret-as="date" format="ymd">2026/03/25</say-as>、
  <break time="300ms"/>
  診療科：<sub alias="ないか">内科</sub>
</prosody>
<break time="500ms"/>
よろしければ1番を、修正がある場合は2番を押してください。
```

---

## 対応確認チェックリスト

TTSエンジンへのSSML導入前に確認すること:

- [ ] 使用しているTTSエンジン（AmiVoice TTS / その他）がSSMLをサポートするか
- [ ] `<break>` の `time` 属性が日本語ロケールで動作するか
- [ ] `<prosody rate>` の数値範囲が仕様通りに動作するか（0.5〜2.0）
- [ ] `<sub>` によるひらがな置換が正しく機能するか
- [ ] `<say-as interpret-as="telephone">` が日本語電話番号で正しく動作するか
- [ ] 既存の `{tts_g:...}` テンプレート変数とSSMLタグの共存が可能か

---

## 非推奨・未確認要素

以下はW3C仕様には含まれるが、**このプロジェクトのTTSエンジンでの動作が未確認**のため原則使用しない:

| 要素 | 理由 |
|---|---|
| `<phoneme alphabet="ipa">` | 日本語IPAのエンジン対応が不明 |
| `<mstts:express-as>` | Microsoft Azure Speech 専用拡張 |
| `<audio src="...">` | Brekeke IVRでの動作未確認 |
| `<voice name="...">` | 音声切替がBrekeke設定と競合する可能性 |

---

## 参考

- [W3C SSML 1.0 仕様](https://www.w3.org/TR/speech-synthesis/)
- [W3C SSML 1.1 仕様](https://www.w3.org/TR/speech-synthesis11/)
- 関連ドキュメント: `docs/brekeke_tips.md` — TTS関連の実運用Tips
