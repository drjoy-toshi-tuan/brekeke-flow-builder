# IVRプロパティ生成ガイド

> propertiesエージェントがフローJSONとセットで生成する IVRプロパティの仕様。
> IVRプロパティは Brekeke PBX のフローに対して外部から値を注入する仕組みで、
> モジュールの `params` に設定された値よりも**常にIVRプロパティの値が優先される**。

---

## 1. TTSプロンプト

TTSモジュールの発話内容をIVRプロパティで定義する。

### 1.1 フォーマット

```
{モジュール名}.prompt={tts_g: 発話テキスト}
```

1つのTTSモジュールにつき `{モジュール名}.prompt=...` で1行。次のモジュールは改行して同じ形式で続ける。

```properties
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。こちらは〇〇病院の自動応答サービスです。}
用件.prompt={tts_g: ご用件をお話しください。}
時間外_アナウンス.prompt={tts_g: ただいまの時間は受付時間外となっております。}
```

**厳守ルール**:
- **`{モジュール名}.prompt=` から始まり、1行で完結する（途中改行禁止）**
- モジュール名とプロパティ名は完全一致が必須。不一致だとTTSが動作しない

### 1.2 指示書にガイダンス文がない場合の処理

generatorがTTSモジュールを生成したが、設計書（指示書）に対応するガイダンス文が見つからない場合は、プロパティファイル内に以下の警告コメントを出力する。

```properties
# [WARNING] 患者_氏名: 指示書に該当するTTSガイダンス文が見つかりませんでした。確認してください。
患者_氏名.prompt=
```

- 空のpromptを出力しつつ、`# [WARNING]` コメントで未設定であることを明示する
- propertiesエージェントはこの警告を検出し、人間にレビューを促す

### 1.2 SSMLによるイントネーション・ポーズ調整

TTSエンジン（Google TTS）は [W3C Speech Synthesis Markup Language (SSML) 1.1](https://www.w3.org/TR/speech-synthesis11/) に基づくSSMLタグをサポートする。イントネーションやポーズの調整が必要な場合は `<speak>` タグ内でSSMLを使用する。

```properties
# SSMLなし（通常）
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。}

# SSMLあり（ポーズ・読み上げ制御）
患者_電話番号確認.prompt={tts_g: <speak>電話番号は、<say-as interpret-as="telephone">#data#</say-as>、<break time="300ms"/>でよろしいでしょうか。</speak>}

# SSMLあり（生年月日の復唱）
患者_生年月日確認.prompt={tts_g: <speak>#data#<break time="300ms"/>でよろしいでしょうか。</speak>}

# SSMLあり（DTMFガイダンス）
患者_生年月日.prompt={tts_g: <speak><break time="200ms"/>生年月日を、「<sub alias="いち きゅう なな ぜろ"><prosody rate="80%">1970</sub><break time="300ms"/><sub alias="ぜろ よん ぜろ いち"><prosody rate="80%">0401</prosody></sub>」のように、8桁の数字を続けて押してください。</speak>}
```

よく使うSSMLタグ:

| タグ | 用途 | 例 |
|---|---|---|
| `<break time="300ms"/>` | ポーズ挿入 | 復唱前の間 |
| `<say-as interpret-as="telephone">` | 電話番号を1桁ずつ読み上げ | `#data#` の読み上げ |
| `<say-as interpret-as="digits">` | 数字を1桁ずつ読み上げ | 診察券番号等 |
| `<sub alias="読み">表記</sub>` | 読み方の指定 | 数字の読み方ガイド |
| `<prosody rate="80%">` | 発話速度の調整 | ゆっくり読む箇所 |

> 詳細な SSML タグ一覧は `docs/ssml_guide.md` を参照。

### 1.3 生成すべきTTSプロンプト

設計書の「TTSガイダンス原案」セクションから、全TTSモジュールのプロンプトを生成する。

```properties
# 冒頭
冒頭_アナウンス.prompt={tts_g: お電話ありがとうございます。こちらは〇〇病院の自動応答サービスです。}

# 用件確認
用件.prompt={tts_g: ご用件をお話しください。診察のご予約、予約の変更、その他のお問い合わせ、のいずれかでお答えください。}

# 時間外
時間外_アナウンス.prompt={tts_g: ただいまの時間は受付時間外となっております。受付時間は平日の午前9時から午後5時です。}

# 非通知
非通知_アナウンス.prompt={tts_g: 恐れ入りますが、電話番号を通知のうえ、おかけ直しください。}

# 終話（携帯用 — SMS言及あり）
終話_予約.prompt={tts_g: ご予約を承りました。後ほどショートメッセージにて詳細をお送りいたします。お電話ありがとうございました。}

# 終話（固定用 — SMS言及なし）
終話_固定予約.prompt={tts_g: ご予約を承りました。お電話ありがとうございました。}
```

### 1.4 TTSテキストの作成ルール

| ルール | 内容 |
|---|---|
| **発話内容は指示書の記載をそのまま使う** | generatorが発話テキストを勝手に生成してはいけない。指示書にない場合は WARNING を出す（1.2参照） |
| **SSMLタグの付与は可能** | 指示書でイントネーション・ポーズの指示がある場合、発話テキストにSSMLタグを追加してよい |
| **1行で記述（改行禁止）** | IVRプロパティの制約。どれだけ長くても1行にまとめる |
| 敬語を使う | 「です」「ます」「ございます」調 |
| 40文字以内を目安 | 1文が長すぎると聞き取りにくい。分割を検討 |
| 数字の読み | 「1を押してください」→「いちを押してください」 |
| 略語を避ける | 「SMS」→「ショートメッセージ」、「TEL」→「お電話番号」 |
| 電話番号の復唱 | `<speak><say-as interpret-as="telephone">#data#</say-as></speak>` |

### 1.5 IVRプロパティ vs JSON直接記載の使い分け

| モジュール | TTS定義場所 | 理由 |
|---|---|---|
| **Text to speech** | IVRプロパティ | プロパティで一括管理。変更が容易 |
| **Re-confirmation node data** | JSON内のparams（`prompt`） | `#data#` を含む復唱テンプレートのためモジュール側で定義 |
| **Speech Retry Counter** | JSON内のparams（`prompt_true` / `prompt_false`） | リトライ/上限到達のテキストをモジュール側で定義 |

> **原則**: 通常の Text to speech モジュールはIVRプロパティで管理する。
> Re-confirmation node data と Speech Retry Counter はモジュール側に直接記載する。

---

## 2. 環境設定

デモ環境と本番環境で値が異なる。テンプレートを元に施設ごとにカスタマイズする。

### 2.1 デモ環境テンプレート

```properties
# wait
冒頭.wait=2000

# amivoice
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.6
amivoice.detection_flag=検出しない
amivoice.save_log=false

# Save2DB / PBX
office_id={施設ID}
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

# 転送（転送モジュールがある場合のみ）
転送.number={転送先電話番号}
```

### 2.2 本番環境テンプレート

```properties
# wait
冒頭.wait=2000

# amivoice
amivoice.uri=ws://speech.internal.assistant.com:8000/ws
amivoice.language=ja
amivoice.engine=入力汎用
amivoice.keep_filter_token=true
amivoice.silent_detection_ms=2000
amivoice.timeout_ms=30000
amivoice.probability=0.6
amivoice.detection_flag=検出しない
amivoice.save_log=false

# Save2DB / PBX
office_id={施設ID}
pbx.db.name=save.db
context.settings.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/pbx/context-model
acceptance_times.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/incoming-call-by-brekeke

# OpenAI SSML
rag_ssml.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/rag-ssml/process-text
openAI_generate.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/openai/generate-text

# RAG
speech.rag.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/rag-ssml/process-text

# 転送（転送モジュールがある場合のみ）
転送.number={転送先電話番号}
```

> **デモと本番の差異はURLのみ。** AmiVoice の probability（0.6）、detection_flag（検出しない）等のパラメータは両環境で共通。

### 2.3 施設固有の可変項目

| 項目 | 説明 | 取得方法 |
|---|---|---|
| `office_id` | Dr.JOY上の施設ID | 指示書で指定 |
| `転送.number` | 有人転送先の電話番号 | 指示書で指定（転送がある場合のみ） |
| `冒頭.wait` | 冒頭待機時間（ms） | 通常 `2000` 固定 |

> `office_id` と `転送.number` は指示書に明記される。指示書に記載がない場合は確認する。

---

## 3. サブフロー呼び出し時のプロパティ

新規作成では Custom Jump to Flow を使用するため、メインフローとサブフローそれぞれに独立してIVRプロパティを設定する。

メインフロー側の Jump モジュールの properties パラメータにサブフロー用の設定を渡す必要はない。

> **旧型（@General$Jump to Flow）の場合のみ**、呼び出し元の properties パラメータに環境設定を含めて全て渡す必要がある。既存フローの修正時に該当。

---

## 4. プロパティ生成の手順

### Step 1: TTSプロンプトを生成

```
設計書の「TTSガイダンス原案」セクションから:
1. 全TTSモジュール名を列挙
2. 各モジュールの発話テキストを {tts_g: ...} 形式で記述
3. モジュール名とプロパティ名の一致を確認
4. 携帯用と固定用で異なる終話TTSがある場合は両方生成
```

### Step 2: 環境設定を選択

```
Q: デモ環境か本番環境か？
  ├─ デモ → デモ環境テンプレートをベースに
  └─ 本番 → 本番環境テンプレートをベースに
→ office_id を指示書の値に置き換え
→ 転送がある場合は 転送.number を指示書の値に置き換え
```

### Step 3: サブフロー用プロパティを生成（該当する場合）

```
サブフロー分割型の場合:
- メインフローとサブフローそれぞれのIVRプロパティを個別に生成
```

---

## 5. 注意事項

| 注意事項 | 内容 |
|---|---|
| モジュール名の完全一致 | TTSプロパティ名とモジュール名が不一致だとTTSが動作しない |
| IVRプロパティ > JSON内設定 | プロパティの値が常に優先される |
| SSML共存 | `{tts_g: ...}` 内でSSMLタグを使用可能 |
| `{recstart}` | DTMFモジュールのpromptで使用する録音開始マーカー。**JSON内に直接記載し、IVRプロパティには記載しない**（プロパティ上書きで消失するため） |
