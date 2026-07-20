# 全9ペア クロス分析レポート

> 9組の訓練データ (PDF設計書 + .bivr + Property.md) を横断的に分析し、
> PDF → .bivr + Property.md 自動生成に必要な知見を体系化する。

---

## Section 1: シナリオ種別分類

### 1.1 分類一覧

| Pair | 施設名 | シナリオ種別 | フロー数 | メインフローモジュール数 | 特記 |
|------|--------|------------|---------|----------------------|------|
| 01 | 帯広第一病院 | **健診** | 3 | 120 | 個人/企業分岐、健保名・代行機関名・オプション等の健診固有項目 |
| 02 | 入間ハート病院 | **診療(複合)** | 14 | 60 | 診察/検査/予防接種/送迎の4種別×予約/変更/キャンセル/確認。最多フロー数 |
| 03 | 長野県立木曽病院 | **診療予約** | 5 | ~100 | 耳鼻科特別ルート、2つの診療科聴取、営業時間チェックあり |
| 04 | ガーデンシティ健診プラザ | **健診** | 3 | 79 | 受診票有無分岐、被保険者/特例退職者、予約受付のみ(変更/キャンセルなし) |
| 05 | JAとりで総合医療センター | **診療予約** | 4 | 91 | 通院歴(新規/再診)分岐、選定療養費案内、追加診療科、診療科対象判定 |
| 06 | 四谷メディカルキューブ | **診療** | 6 | 60 | 症状相談・緊急転送、遅刻対応(設計書にあるが未実装)、転送あり |
| 07 | 兵庫県立こども病院 | **診療(小児)** | 3 | 133 | 検診後受診(乳児/学校)、整形外科特別扱い、残薬確認 |
| 08 | 東京衛生アドベンチスト病院 | **診療予約** | 5 | 78 | 時間帯判定(早朝/通常)、地域連携室転送、氏名→生年月日→電話番号→用件の順序 |
| 09 | いまきいれ総合病院 | **診療予約** | 6 | 93 | 当日確認→代表案内、再診時の症状確認、紹介状有無分岐、次回受診予定日 |
| 11 | 帝京大学医学部附属みぞのくち病院 | **診療予約** | 6 | 186 | 過去最大フロー、31診療科・多段ContextMatchRouter分岐、3営業日計算Script、Re-confirmation node dataの非DOB用途活用、DOB二段階OpenAI正規化 |

### 1.2 シナリオ種別の構造的特徴

#### 診療予約型 (pair_02, 03, 05, 06, 07, 08, 09)
- **用件分岐**: 予約/変更/キャンセル/確認(+α)の基本4分岐
- **診療科聴取**: ほぼ必須。対象/対象外判定、復唱あり
- **受診歴(通院歴)**: 初診/再診分岐がある施設が多い(05, 06, 07, 08, 09)
- **紹介状有無**: 初診時の紹介状確認→なしの場合は代表案内or自己負担案内(03, 07, 08, 09)
- **個人情報聴取**: 氏名→生年月日→電話番号(+診察券番号)

#### 健診予約型 (pair_01, 04)
- **個人/企業分岐** (pair_01) or **受診票有無分岐** (pair_04)
- **健診固有項目**: 健保名、代行機関名、希望コース、オプション、受診者数、被保険者区分
- **変更/キャンセルフロー**: pair_01にはあり、pair_04は予約のみ
- **用件聴取の位置**: 個人情報聴取の後(pair_01)、または受診票分岐直後(pair_04)

---

## Section 2: 共通フローパターン (全シナリオ共通)

### 2.1 開始チェーン (9/9)

**全ペアに共通する開始シーケンス:**

```
冒頭待ち時間 (Custom$wait, 2000ms)
  → コンテキスト設定 (saveContextModel2DB)
    → [営業時間チェック (acceptance_times)] ← 任意
      → 冒頭アナウンス (TTS)
        → 非通知分岐 (incoming-classifier)
```

| 要素 | 使用ペア | 備考 |
|------|---------|------|
| wait 2000ms | 全9ペア | PDFには記載なし。通話接続安定化のための標準値 |
| saveContextModel2DB | 全9ペア | コンテキストフィールド定義。PDFの「詳細画面表示名」に対応 |
| acceptance_times | 03, 04, 08 (明示的) | 営業時間チェック。他ペアはAPI側で制御 |
| 冒頭TTS | 全9ペア | Property.md: `冒頭.prompt` |
| incoming-classifier | 全9ペア | 非通知→終話、携帯/固定/海外→次ステップ |

**パターン構造 (modules定義):**
```
type: "Custom$wait"           → params: { "wait": "" }  (Property.mdで冒頭.wait=2000)
type: "drjoy^Persistence$saveContextModel2DB" → params.fields: [コンテキスト定義JSON]
type: "drjoy^External Integration$acceptance_times" → params: {}
type: "drjoy^Text To Speech$Text to speech" → params: { "prompt": "" } (Property.md注入)
type: "drjoy^Incoming$incoming-classifier" → next: 非通知/固定/海外/携帯/その他
```

### 2.2 非通知対応パターン (9/9)

```
非通知分岐 →[非通知]→ 終話_非通知 (TTS) → completeflag (status=0) → Disconnect
```

- 全9ペアで非通知拒否が実装されている
- PDFの「非通知受入拒否: 設定する」に対応
- 終話_非通知のテキストは施設ごとにカスタム(施設名・186案内等)
- completeflagのstatus値は0(途中切断)が標準

### 2.3 個人情報聴取サブフロー (9/9)

全ペアが個人情報聴取をサブフロー化(Custom Jump to Flow)している。

**基本構造:**
```
患者_氏名 (TTS/STT)
  → 患者_生年月日 (TTS/DTMF+STT → DOB Re-confirmation)
    → [患者_診察券番号] (オプション、復唱あり)
      → 着信電話番号分岐 (incoming-classifier)
        → [携帯] → 着信番号確認(復唱) → 肯定→save / 否定→手動入力
        → [固定/非通知/海外] → 電話番号手動入力 → 正規化 → 復唱
```

| 要素 | 使用ペア | 入力方式 | 備考 |
|------|---------|---------|------|
| 氏名 | 全9ペア | STT (type=氏名カナ) | 復唱なし。openAI正規化 |
| 生年月日 | 全9ペア | DTMF+STT → DOB Re-confirmation | 復唱あり。西暦8桁DTMF対応 |
| 診察券番号 | 02,03,05,06,07,08,09 | DTMF+STT | 復唱あり。再診/変更/キャンセル時 |
| 電話番号 | 全9ペア | DTMF+STT + incoming-classifier | 携帯確認/固定入力の2パターン |

**ペア間のバリエーション:**
- pair_02: 個人情報聴取は1フロー(再診/新規共通)
- pair_05: 再診用(診察券番号あり)と新規用(なし)の2フロー
- pair_07: 新規用(連絡先入力あり)と再診用(簡略版)の2フロー
- pair_08: 氏名/生年月日/電話番号を個別サブフロー化(3フロー)
- pair_09: 氏名/生年月日/電話番号を個別サブフロー化(3フロー)

### 2.4 会話ステップパターン (TTS→STT→OpenAI→Retry) (9/9)

各聴取項目は以下の5モジュール1セットで構成:

```
TTS (質問読み上げ)
  → STT (音声入力)
    → OpenAI (正規化/分類)
      → [次ステップ or 復唱]
  → Retry (リトライカウンター)
    → [true] → TTS (再質問)
    → [false] → 次ステップ or 聴取不可処理
```

**共通パラメータ:**
- STT next: `^TIMEOUT$` / `^ERROR$` / `^NO_RESULT$` → リトライ, `^.+$` → OpenAI
- OpenAI next: `^TIMEOUT$` / `^ERROR$` / `^NO_RESULT$` → リトライ, + 個別分岐条件
- Retry: matchingmethod=0, retry_count=2(標準), prompt_true/prompt_false直接記述
- 全TTS/STT/Retryにsave2dbサブモジュール接続

### 2.5 復唱パターン (Re-confirmation) (9/9)

```
OpenAI結果 → 復唱TTS (Re-confirmation node data, prompt="#data# でよろしいですか")
  → 入力_復唱 (STT)
    → OpenAI_復唱 (肯定/否定判定)
      → [肯定] → 次ステップ
      → [否定] → 否定後再聴取TTS → 最初のSTTに戻る
```

**復唱が一般的な項目**: 生年月日、用件、診療科、電話番号(固定)、診察券番号
**復唱しない項目**: 氏名、症状、自由回答(確認内容、希望時期等)

### 2.6 終話チェーン (9/9)

```
saveCompletionFlag2db (status, smsFlag)
  → 終話TTS (ガイダンス)
    → Disconnect
```

**用件別の終話パターン:**
| 用件 | status | smsFlag | 備考 |
|------|--------|---------|------|
| 予約完了 | 1(未処理) | 1 | SMS送信あり |
| 変更完了 | 1(未処理) | 1 | SMS送信あり |
| キャンセル完了 | 1(未処理) | 2 | SMS送信あり(別テンプレ) |
| 確認/問い合わせ完了 | 1(未処理) | 1 or 3 | 施設による |
| 代表案内 | 2 | 0 | SMS送信なし |
| 転送成功 | 3 | 0 | 転送時 |
| 非通知/途中切断 | 0 | 0 | SMS送信なし |
| 時間外 | 6 | 0 | SMS送信なし |

**終話ガイダンス分岐**: 多くのペアでContextMatchRouterを使用し、用件(予約/変更/キャンセル等)に応じた終話アナウンスを選択。携帯/固定でSMS案内の有無を切り替えるペアもある(pair_01, 03)。

### 2.7 RAG/FAQ サブフロー (8/9)

pair_08以外の全ペアにRAG検索サブフローが存在。

```
相談_問合せ (TTS: "何かお伝えしたいことや質問はありますか")
  → 入力_相談_問合せ (STT)
    → openAI_相談_問合せ (要約/回答不要判定)
      → [回答不要] → 発話_かしこまりました → return
      → [回答あり] → rag-question (RAG検索)
        → [成功] → 相談_問合せループ (次の質問)
        → [NO_RESULT] → 相談_FAQ失敗 → return
```

**共通構造**: RAG検索は全てサブフロー(Custom Jump to Flow)として分離。property経由でプロンプトを注入。

### 2.8 save2dbパターン (9/9)

- 全TTS/STT/Retryモジュールにsave2dbサブモジュールを接続
- save2db: type=`drjoy^Persistence$save2db`, next=[] (subs経由のみ)
- save-冒頭, save-history_1/2/3 等のラベルで通話ログを段階的に保存

### 2.9 openAI_聴取不可パターン (7+/9)

リトライ上限到達時に「聴取不可」を固定出力するOpenAIモジュール:

```
リトライ →[false]→ openAI_聴取不可_X (prompt: "「聴取不可」と出力せよ")
  → save (contextValue="聴取不可") → 次ステップ
```

確認ペア: 02, 04, 05, 06, 07, 08, 09

---

## Section 3: PDF → bivr 変換ルール

### 3.1 施設名 → フロー名・グループ名

| PDF情報 | .bivr実装箇所 | 変換ルール | 例 |
|---------|-------------|----------|-----|
| 施設名 | フロー名のプレフィックス | `{施設名}${シナリオ名}-Demo` | 入間ハート病院$診療-Demo |
| 施設名 | サブフロー名のプレフィックス | `{施設名}${サブフロー名}` | 帯広第一病院$電話番号確認 |
| 施設名 | Property.mdのアナウンス文中 | 直接埋め込み | "お電話ありがとうございます。{施設名}の..." |
| 施設名 | 氏名聴取の例文 | 施設名から連想したカナ名 | 入間ハート病院→"イルマハナコ", ガーデンシティ→"ガーデンタロウ" |

### 3.2 冒頭アナウンス文 → TTS prompt + Property.md

**PDFの記載箇所**: シナリオフロー図の冒頭、アナウンス一覧表

**変換ルール**:
1. PDF記載のテキストをそのまま `{tts_g:テキスト}` 形式でProperty.mdに記載
2. .bivrの冒頭TTSモジュールのpromptは**空**(Property.mdから注入)
3. 施設名・代表電話番号・受付時間等はPDFから抽出して埋め込み
4. 「プーという音が鳴ってからお話しください」等の定型句はエキスパート判断で追加

**例 (pair_05)**:
- PDF: "お電話ありがとうございます。JAとりで総合医療センターの予約専用AI電話です..."
- Property.md: `冒頭.prompt={tts_g:お電話ありがとうございます。JAとりで総合医療センターの予約専用AI電話です...}`
- .bivr: 冒頭モジュール prompt="" (空)

### 3.3 聴取項目(質問) → TTS + STT + OpenAI + Retry チェーン

**PDFの記載箇所**: アナウンス一覧表(聴取項目名、復唱有無、発話文言)

**変換ルール**:
1. 各聴取項目に対して5モジュール(TTS/STT/OpenAI/Retry/save2db)を生成
2. PDFの発話文言 → Property.mdの `{モジュール名}.prompt` に設定
3. PDFの「復唱: あり」→ Re-confirmation + 肯定否定判定を追加
4. PDFの入力方式(フリーワード/DTMF等) → STTモジュールタイプの選択
   - フリーワード → `Speech to Text` (STT only)
   - ダイヤルプッシュ対応 → `DTMF AmiVoice STT Input`
5. OpenAIプロンプトはPDFに直接記載されない(エキスパート知識)

**入力方式のマッピング:**
| PDF記載 | STTモジュールタイプ | DTMFパラメータ |
|--------|-------------------|---------------|
| フリーワード | Speech to Text | なし |
| ダイヤルプッシュ可能 | DTMF AmiVoice STT Input | max_dtmf_length=適切な桁数 |
| 数字N択(1,2,3...) | DTMF AmiVoice STT Input | max_dtmf_length=1 |
| 電話番号 | DTMF AmiVoice STT Input | max_dtmf_length=11 |
| 生年月日 | DTMF AmiVoice STT Input | max_dtmf_length=8 |

### 3.4 用件分岐 → OpenAI next条件

**PDFの記載箇所**: 用件一覧(用件1: 予約, 用件2: 変更 等)

**変換ルール**:
1. PDFの用件リスト → OpenAIプロンプトの出力選択肢
2. 各用件 → openAI nextの `^{用件名}$` 条件として設定
3. 分岐先 → 各用件のフローパスに対応するモジュールへ接続

**例 (pair_05)**:
- PDF用件: 予約/変更/キャンセル/その他問い合わせ
- OpenAI next: `^予約$`→確認_通院歴, `^変更$`→確認_診療科_2, `^キャンセル$`→確認_診療科_2, `^その他問い合わせ$`→確認_問い合わせ内容

### 3.5 診療科リスト → OpenAIプロンプト + profile_words

**PDFの記載箇所**: 診療科一覧表、ヒアリングシート

**変換ルール**:
1. PDF記載の診療科名 → OpenAI判定プロンプトの選択肢リスト
2. 対象/対象外の区分 → OpenAI判定結果の分岐(対象→次ステップ, 対象外→代表案内)
3. 診療科名の読み仮名/類義語 → profile_words辞書として登録
4. 診療科名 → saveContextModel2DBのclinicalDepartment.rangeValuesに設定

**例 (pair_06 四谷メディカルキューブ)**:
- PDF: 消化器外科・一般外科(しょうかきげか, いっぱんげか, げか)
- profile_words: `消化器外科 しょうかきげか\n一般外科 いっぱんげか\n外科 げか`
- OpenAI prompt: "...「消化器外科・一般外科」「減量・糖尿病外科」..."

### 3.6 転送先電話番号 → Call Transfer params

**PDFの記載箇所**: 転送設定、特殊用件設定

**変換ルール**:
1. PDF記載の転送先番号 → Call Transfer params.number
2. 転送タイプ → params.transfer_type (通常 "Blind Transfer")
3. 転送案内文 → 転送前TTSのprompt

確認ペア: pair_06(仮置き/番号未設定), pair_08(地域連携室転送あり)

### 3.7 SMS設定 → smsFlag値

**PDFの記載箇所**: SMS文言一覧表

**変換ルール**:
1. 用件ごとのSMS文言 → smsFlagの番号で管理(文言自体はサーバ側)
2. SMS送信あり → smsFlag=1 or 2 (テンプレート番号)
3. SMS送信なし → smsFlag=0 or 空

### 3.8 稼働時間 → acceptance_times

**PDFの記載箇所**: 基本設定(稼働曜日/時間)

**変換ルール**:
- 稼働時間は.bivrには直接含まれない
- acceptance_times APIで外部管理
- 時間外アナウンスもBrekeke PBX側で設定される場合が多い
- pair_03, 04, 08は.bivr内にacceptance_timesモジュールあり

### 3.9 状態フラグ → completeflag status値

**PDFの記載箇所**: 状態フラグ定義表

**変換ルール**:
1. PDF記載の状態フラグ番号をそのままsaveCompletionFlag2dbのstatus値に使用
2. 標準マッピング(全ペア共通):
   - 0: 途中切断
   - 1: 未処理
   - 2: 代表案内
   - 3: 転送
   - 6: 時間外
3. 各終話モジュールにどのstatusを割り当てるかはPDFのフロー構造から決定

---

## Section 4: デフォルト値 (PDFに記載がなく、人間が補完する情報)

### 4.1 AmiVoice設定

| パラメータ | 標準値 | ペア間変動 | 備考 |
|-----------|--------|----------|------|
| uri | ws://10.0.20.11:8000/ws | 全ペア同一 | デモ環境固定値 |
| language | ja | 全ペア同一 | 固定値 |
| engine | 入力汎用 | 全ペア同一 | 固定値 |
| keep_filter_token | true | 全ペア同一 | 固定値 |
| silent_detection_ms | 2000 | pair_01のみ1500 | PDFの「発話待機時間1.5秒」に対応する場合あり |
| timeout_ms | 30000 | pair_01のみ28000 | 基本固定 |
| probability | 0.6 | 0.57(pair_01,05), 0.6(多数), 0.63(pair_11), 0.7(pair_07 サブフロー) | 施設/フローにより微調整 |
| detection_flag | 検出しない | pair_07サブフローのみ「音声開始前から検出」 | 基本固定 |
| save_log | false | 全ペア同一 | 固定値 |

**結論**: AmiVoice設定は**ほぼハードコード可能**。probability(0.57-0.7)とsilent_detection_ms(1500-2000)のみ施設依存で微調整。

### 4.2 API URL群

| パラメータ | 標準値(デモ) | ペア間変動 |
|-----------|-------------|----------|
| context.settings.url | https://demo-reserve.famishare.jp/api/anonymous/dr/ha/pbx/context-model | 全ペア同一 |
| acceptance_times.url | https://demo-reserve.famishare.jp/api/anonymous/dr/ha/incoming-call-by-brekeke | 全ペア同一 |
| rag_ssml.url | https://demo-reserve.famishare.jp/api/anonymous/dr/ha/rag-ssml/process-text | 全ペア同一 |
| openAI_generate.url | https://demo-reserve.famishare.jp/api/anonymous/dr/ha/openai/generate-text | 全ペア同一 |
| speech.rag.url | http://10.0.20.11:8000/api/v1/rag | 全ペア同一 |
| speech.rag.connect_timeout | 2 | 全ペア同一 |
| speech.rag.request_timeout | 3 | 全ペア同一 |
| speech.rag.credibility | 0 | 全ペア同一 |
| pbx.db.name | save.db | 全ペア同一 |

**結論**: API URLは環境ごとに**完全にハードコード可能**(デモ/本番の2テンプレート)。

### 4.3 office_id

| Pair | office_id |
|------|-----------|
| 01 | 5b8a537ed2122d061d51c31b |
| 02 | 5eecd4062c9faeddaddbcb00 |
| 03 | 5b8a536dd2122d061d4fe6c0 |
| 04 | 697b0ca78de92d000791576e |
| 05 | 5eecd4052c9faeddaddb9c87 |
| 06 | 5eecd40e2c9faeddaddc0dc4 |
| 07 | 5b8a5380d2122d061d5218bc |
| 08 | 5b8a5384d2122d061d527909 |
| 09 | 5b8a5383d2122d061d526547 |

**結論**: office_idは施設ごとに一意。PDFには記載されず、Dr.JOYシステムから取得する必要がある。**自動生成時は外部入力として必須**。

### 4.4 冒頭待ち時間

全ペアで `Custom$wait` の wait=2000ms。PDFに記載なし。**ハードコード可能**。

### 4.5 リトライ設定

| パラメータ | 標準値 | ペア間変動 |
|-----------|--------|----------|
| retry_count | 2 | pair_08のみ3(PDF指定) |
| prompt_true | "申し訳ございません。うまく聞き取りが出来ませんでした。再度、" | ほぼ統一 |
| prompt_false | "大変申し訳ございません。うまく聞き取ることができませんでした..." or "" | 施設により微調整 |

**結論**: retry_countはPDFの「リトライ回数」に対応。prompt_true/falseはテンプレート化可能。

### 4.6 OpenAIプロンプト

PDFに直接記載されない最大のエキスパート知識領域。以下のカテゴリがある:

1. **用件分類プロンプト**: 入力テキストを用件カテゴリに分類
2. **診療科判定プロンプト**: 入力テキストから診療科を抽出、対象/対象外を判定
3. **肯定否定判定プロンプト**: 復唱時の「はい/いいえ」判定
4. **日付正規化プロンプト**: 音声入力の日付をYYYYMMDD形式に変換
5. **氏名正規化プロンプト**: 音声入力の氏名をカタカナに変換
6. **聴取不可出力プロンプト**: リトライ上限時に「聴取不可」を強制出力
7. **プロンプトインジェクション対策**: 全プロンプトに防御セクション必須

### 4.7 profile_words (音声認識辞書)

STTモジュールの入力精度を向上させるための辞書。PDFには記載されない。

**共通辞書**: 肯定(はい/はーい/ええ等)、否定(いいえ/ちがいます等)、曜日、月名
**施設固有辞書**: 診療科名の読み仮名/類義語、検査名、ワクチン名、施設固有用語

### 4.8 レイアウト座標

.bivrのlayoutフィールド(x/y座標)はIVR動作に影響しないがGUI表示用。
VFBリファレンスに標準座標パターンが定義されている(Section 11参照)。

### 4.9 contextName英語名

コンテキストフィールドの英語名はPDFに記載されない(日本語名のみ)。

**共通マッピング:**
| PDF日本語名 | contextName | displayType |
|-----------|-------------|-------------|
| 氏名 | patientName | TEXT |
| 生年月日 | patientDateOfBirth | DATE_OF_BIRTH |
| 診療科 | clinicalDepartment | DEPARTMENT |
| 電話番号(着信) | telephoneNumber | PHONE_NUMBER_CALL |
| 連絡先電話番号 | additionalPhoneNumber | PHONE_NUMBER |
| 区分/用件 | classification | CLASSIFICATION |
| 状態 | status | STATUS |
| 診察券番号 | medicalCardNumber | NUMBER |
| 現在の予約日 | reservationDate | DATE |
| 通話ID | callId | NUMBER |
| 入電日時 | dateOfCall | DATE |

**施設固有フィールド**: 症状(diagnosis), 紹介状有無(introduction), 希望日(Preferreddateandtime), 問い合わせ内容(AppointmentConfirmation), 理由(reason) 等

---

## Section 5: Property.md パターン分析

### 5.1 共通構造

全ペアのProperty.mdは以下のセクションで構成:

```
# アナウンスプロンプト
{モジュール名}.prompt={tts_g:テキスト}

# AmiVoice設定
amivoice.uri=ws://10.0.20.11:8000/ws
amivoice.language=ja
...

# Save2DB / API設定
office_id={施設固有ID}
pbx.db.name=save.db
context.settings.url=https://...
...

# RAG設定
speech.rag.url=http://...
...
```

### 5.2 必須セクション (全ペア共通)

1. **冒頭.prompt**: 冒頭アナウンス
2. **終話_非通知.prompt**: 非通知終話
3. **終話_失敗.prompt**: 聴取失敗終話
4. **amivoice設定群**: uri, language, engine, silent_detection_ms, timeout_ms, probability, detection_flag, save_log, keep_filter_token
5. **API URL群**: office_id, pbx.db.name, context.settings.url, acceptance_times.url, rag_ssml.url, openAI_generate.url
6. **RAG設定群**: speech.rag.url, speech.rag.connect_timeout, speech.rag.request_timeout, speech.rag.credibility

### 5.3 シナリオ依存セクション

| セクション | 診療予約 | 健診 |
|-----------|---------|------|
| 確認_用件.prompt | あり(4-5択) | あり(4択) |
| 確認_診療科.prompt | あり | なし |
| 復唱_診療科.prompt | あり | なし |
| 終話_代表案内.prompt | あり(代表番号案内) | なし or あり |
| 確認_通院歴/受診歴.prompt | あり(初診/再診) | あり(初回/2回目) |
| 確認_現在の予約日.prompt | あり(変更/キャンセル時) | なし or あり |
| 確認_希望コース.prompt | なし | あり |
| 確認_健保名.prompt | なし | あり |

### 5.4 Property.mdとモジュール名の関係

**完全一致が必須**: Property.mdのキー名 = .bivrのモジュール名

- 正: `冒頭.prompt={tts_g:...}` ← モジュール名「冒頭」
- 正: `確認_用件.prompt={tts_g:...}` ← モジュール名「確認_用件」
- 誤: `tts_冒頭.prompt=...` (プレフィックス不一致)

**サブフロー内のプロンプト**: メインフローのJump to Flowモジュールの`params.properties`にインラインで定義。Property.mdには含まれない場合が多い(pair_05, 07, 09等)。

### 5.5 Property.mdに含まれない情報

- OpenAIプロンプト(.bivr内に直接記述)
- profile_words(.bivr内に直接記述)
- retry prompt_true / prompt_false(.bivr内に直接記述)
- サブフロー内のTTSプロンプト(Jump to Flow properties経由)

---

## Section 6: バリエーション & エッジケース

### 6.1 施設固有の特殊機能

| Pair | 特殊機能 | 詳細 |
|------|---------|------|
| 01 | 個人/企業分岐 | 個人→氏名、企業→企業名+担当者名。健診特有 |
| 02 | 4種別×4用件の組み合わせ | 診察/検査/予防接種/送迎 × 予約/変更/キャンセル/確認 → 12サブフロー |
| 03 | 耳鼻科特別ルート | 耳鼻科のみ独自フロー(予約有無→調整日承認→希望時期→症状) |
| 03 | 2つの診療科聴取 | 1つ目の診療科の後に「他の診療科はありますか」→2つ目聴取 |
| 04 | 受診票有無分岐 | 受診票あり→日程/オプション変更、なし→詳細質問。健診特有 |
| 04 | 被保険者/特例退職者 | 健診特有の保険区分確認 |
| 05 | 選定療養費案内 | 新規患者に選定療養費の説明(7,700円/5,500円) |
| 05 | 追加診療科 | 変更/キャンセル時に追加の診療科を聴取 |
| 06 | 症状相談・緊急判定 | 緊急→転送、通常→相談内容聴取 |
| 06 | 遅刻対応(設計書のみ) | 15分以内→順番変更案内、15分超→変更提案/転送 |
| 07 | 検診後受診(乳児/学校) | 小児病院特有。乳児検診→年齢/区役所、学校検診→学校名 |
| 07 | 整形外科の特別扱い | 再診予約時、整形外科のみ「装具の調整」確認 |
| 08 | 時間帯判定(2段階) | 紹介状あり:8:30境界、紹介状なし+当日:10:30境界 |
| 08 | 地域連携室転送 | 初診+紹介状あり→地域連携室へAttended Transfer |
| 08 | 氏名→生年月日→電話番号→用件の順 | 他施設は冒頭→用件→個人情報の順が多いが、ここは個人情報先行 |
| 09 | 当日確認→代表案内 | 冒頭の次に「明日以降のお問い合わせですか」→当日なら代表番号案内 |
| 09 | 再診時の症状確認 | 再診→「前回と同じ症状ですか」→違う→紹介状確認 |
| 09 | キャンセル時の次回受診予定日 | キャンセル→「次回の受診予定日は決まっていますか」→希望予約日聴取 |
| 11 | 3営業日後の動的日付アナウンス | script_日付取得で祝日API呼び出し→3営業日後計算→冒頭_アナウンス2でRe-confirmation node data読み上げ |
| 11 | 当日/翌日/翌々日の変更は代表案内に誘導 | openAI_現在の予約日→script_3days分岐で比較→代表案内 or 理由聴取に分岐 |
| 11 | 31診療科の多段ContextMatchRouter | 同一openAI_診療科出力を6つのCMRが参照（フェーズ/用件別の異なる遷移先） |
| 11 | 診察券確認→初めて/あり/なし の三択分岐 | 初めて→診察券番号不要で氏名聴取へ、あり→診察券番号聴取へ、なし→終話 |
| 11 | 生年月日二段階OpenAI正規化 | DOB Re-confirmation未使用。2つのOpenAIでSTT→日付フォーマット→日本語表記変換 |
| 11 | status=7（診察券なし）・status=22（直接来院）の施設固有statusコード | 標準の0/1/2/3/6以外のstatusが使用される |

### 6.2 非標準モジュール使用

| Pair | モジュール | 用途 |
|------|----------|------|
| 08 | acceptance_times内でのopenAI_時間判定 | 時間帯による分岐(7:30-8:29/8:30-16:10) |
| 06 | Call Transfer(仮置き) | 転送先番号未設定 |
| 08 | Call Transfer(Attended) | 地域連携室への有人転送 |
| 02 | DateOfCall Classifier相当 | 時間帯による冒頭アナウンス分岐(未反映) |

### 6.3 フロー分割パターンのバリエーション

| パターン | 使用ペア | フロー数 | 特徴 |
|---------|---------|---------|------|
| メイン+電話番号+RAG | 01 | 3 | 電話番号を独立サブフロー化 |
| メイン+個人情報+RAG | 04 | 3 | 個人情報(氏名/生年月日/電話番号)を1フロー |
| メイン+個人情報+個人情報2+RAG | 05, 07 | 4/3 | 新規/再診で個人情報フローを分離 |
| メイン+用件+氏名+生年月日+電話番号+RAG | 08, 09 | 5/6 | 各聴取項目を個別サブフロー |
| メイン+診療科×3+個人情報+RAG | 06 | 6 | 用件別に診療科聴取を3フロー |
| メイン+診療科②×2+個人情報+RAG | 03 | 5 | 2つ目の診療科用に2フロー |
| メイン+12サブフロー+個人情報+RAG | 02 | 14 | 種別×用件の組み合わせ全展開 |

### 6.4 自動化が困難なケース

1. **pair_02の12サブフロー**: 種別(4)×用件(4)の組み合わせでサブフローが爆発。テンプレートだけでは対応困難
2. **pair_03の耳鼻科特別ルート**: 特定診療科のみ独自フロー。PDF内の自然言語記述から機械的に抽出が困難
3. **pair_06の遅刻対応**: 設計書に記載があるが実装されていないケース。設計変更の追跡が必要
4. **pair_07の検診後受診**: 小児病院特有の分岐。テンプレートに含まれない独自フロー
5. **pair_08の時間帯判定**: 2段階のOpenAI時間判定。施設固有のビジネスロジック
6. **OpenAIプロンプトの生成**: プロンプトインジェクション対策、出力形式指定、分類ロジック等

---

## Section 7: 自動化可能性評価

### 7.1 出力要素の自動化分類

| 要素 | 全体比率 | 自動化方法 | 難易度 |
|------|---------|----------|--------|
| **開始チェーン** (wait→context→classifier) | ~5% | テンプレート固定 | 低 |
| **AmiVoice設定** | ~3% | テンプレート固定(probability微調整) | 低 |
| **API URL群** | ~3% | 環境テンプレート固定 | 低 |
| **TTS prompt** (Property.md) | ~15% | PDF抽出→直接コピー | 低-中 |
| **STTモジュール構造** | ~10% | 入力方式に基づくテンプレート | 低 |
| **Retryモジュール** | ~8% | テンプレート固定(retry_count可変) | 低 |
| **save2dbモジュール** | ~5% | テンプレート固定 | 低 |
| **completeflag/終話チェーン** | ~5% | PDF状態フラグ表→テンプレート | 低-中 |
| **非通知対応** | ~3% | テンプレート固定(テキストのみPDF) | 低 |
| **RAGサブフロー** | ~5% | テンプレート固定 | 低 |
| **個人情報聴取サブフロー** | ~10% | テンプレート(診察券有無で2パターン) | 中 |
| **用件分岐ロジック** | ~8% | PDFフロー図→ルールベース生成 | 中 |
| **OpenAIプロンプト** | ~10% | LLM生成+テンプレート | 高 |
| **profile_words辞書** | ~5% | 診療科リスト→辞書テンプレート+LLM | 中-高 |
| **施設固有フロー分岐** | ~5% | LLM理解+人間レビュー必須 | 高 |

### 7.2 定量的評価

| カテゴリ | 比率 | 内容 |
|---------|------|------|
| **PDFから決定論的に生成可能** | ~40% | TTS prompt、基本フロー構造、終話チェーン、分岐条件 |
| **テンプレート/デフォルトで補完可能** | ~35% | AmiVoice設定、API URL、wait、Retry、save2db、RAGフロー、個人情報聴取 |
| **LLM支援で生成可能** | ~15% | OpenAIプロンプト、profile_words、施設固有分岐のモジュール化 |
| **人間の判断が必須** | ~10% | 特殊フロー設計、複雑な分岐ロジック、転送先選定、PDF曖昧記述の解釈 |

### 7.3 最もリスクの高い領域

1. **OpenAIプロンプト生成**: 分類精度・インジェクション対策・出力形式に直接影響。テスト不足だと分岐ミスで通話が切断される
2. **用件分岐のモジュール接続**: next配列の条件とnextModuleNameの整合性。1つのミスでフロー全体が破綻
3. **サブフロー間のproperties受け渡し**: Jump to Flowのproperties内にサブフロー用プロンプトをインラインで定義する必要がある
4. **施設固有フロー**: 耳鼻科特別ルート(pair_03)、検診後受診(pair_07)、時間帯判定(pair_08)等
5. **contextName / displayTypeの一貫性**: saveContextModel2DBの定義とopenAIモジュールのcontextName/displayTypeが一致しないとデータが保存されない

### 7.4 推奨アプローチ

**ハイブリッド方式**: テンプレート + ルールベース + LLM

#### Phase 1: テンプレートベース生成 (自動化率 ~75%)
- 開始チェーン、AmiVoice設定、API URL、非通知対応、RAGフロー → 固定テンプレート
- 個人情報聴取 → パラメータ化テンプレート(診察券番号有無)
- 終話チェーン → 用件数に基づくテンプレート展開
- Property.md → PDF抽出テキスト + 環境テンプレート

#### Phase 2: ルールベース変換 (自動化率 +10%)
- PDFの聴取項目リスト → TTS/STT/OpenAI/Retryチェーンの自動生成
- PDFの用件リスト → 用件分岐(ContextMatchRouter)の生成
- PDFの診療科リスト → profile_wordsの基本辞書生成
- PDFの復唱設定(有/無) → Re-confirmationモジュールの自動追加

#### Phase 3: LLM支援生成 (自動化率 +10%)
- OpenAIプロンプトの生成(分類ルール、出力形式、インジェクション防御)
- profile_wordsの類義語展開
- 施設固有の分岐ロジックの解釈
- アナウンス文言の微調整(例文のカスタマイズ等)

#### Phase 4: 人間レビュー (残り ~5%)
- 特殊フローの設計判断
- 転送先電話番号の確認
- PDF曖昧記述の解釈
- 全体的な整合性チェック

### 7.5 推奨ツールチェーン

```
PDF → [PDF Parser] → 構造化データ(JSON)
  → [Template Engine] → 基本.bivr構造 + Property.md雛形
    → [Rule Engine] → 聴取項目チェーン生成、分岐ロジック生成
      → [LLM (Claude/GPT)] → OpenAIプロンプト生成、profile_words生成
        → [Validator (bivr-checker)] → 構造検証、整合性チェック
          → [Human Review] → 最終確認、特殊ケース対応
```

### 7.6 期待される効果

| 指標 | 現在(手動) | 自動化後(推定) |
|------|----------|--------------|
| 1フロー生成時間 | 4-8時間 | 30分-1時間(LLM生成+レビュー) |
| 構造的ミス率 | ~5% | <1%(Validator自動検出) |
| プロンプト品質 | ばらつきあり | テンプレート+レビューで安定化 |
| Property.md整合性 | 手動確認 | 自動検証で100%保証 |

---

## Section 8: Pair_11 個別分析 — 帝京大学医学部附属みぞのくち病院

### 8.1 フロー概要

| 項目 | 値 |
|---|---|
| 施設名 | 帝京大学医学部附属みぞのくち病院 |
| フロー種別 | 診療予約（予約/変更/キャンセル/確認/その他問合せ） |
| メインフロー名 | 帝京溝口$診療 |
| メインフローモジュール数 | **186**（全ペア最大） |
| サブフロー | 氏名聴取(4), 生年月日聴取(12), 診察券番号聴取(9), 電話番号聴取(24), RAG検索(9) |
| 総モジュール数 | ~244 |
| acceptance_times | あり（メインフロー内） |

### 8.2 コンテキストスキーマ

以下の施設固有フィールドが含まれる（標準フィールド以外）：

| contextName | contextNameJp | displayType | 備考 |
|---|---|---|---|
| multipleDepartments | 複数診療科 | TEXT | 新規（複数科受診ケース） |
| appointmentDate | 予約日 | DATE | 新規（reservationDateとは別） |
| desiredAppointmentDate | 予約希望日 | TEXT | 新規 |
| address | 住所 | TEXT | 新規（住所聴取）  |
| Previousvisits | 受診歴 | TEXT | 非標準命名（先頭大文字） |
| SameAsLastTime | 前回と同じ | TEXT | 非標準命名 |
| Referral | 紹介状の有無 | TEXT | 非標準命名 |
| Areferraltous | 当院宛 | TEXT | 非標準命名 |
| Mydoctor | 担当医 | TEXT | 非標準（規則上は inquiry を使用すべき） |
| Injection | 注射・装具 | TEXT | 非標準命名 |
| Test | 検査有無 | TEXT | 短縮形 |
| Test22 | 術前検査 | TEXT | 非標準命名 |
| Scheduledtime | 時間指定 | TEXT | 非標準命名 |
| Testditail | 検査内容 | TEXT | タイポ（TestDetail が正しい） |

> **注意**: pair_11 は非標準命名フィールドが多い。これらはVFBが生成した非推奨パターンであり、新規実装では inquiry / reason / diagnosis 等の標準名を使うべき。

### 8.3 主要フロー構造

```
wait(2000)
  → コンテキスト設定(saveContextModel2DB)
    → 営業時間チェック(acceptance_times)
      → [false/TIMEOUT/ERROR] → 完了フラグ_時間外(status=6) → 切断_時間外
      → [true] → 冒頭_アナウンス(TTS)
        → script_日付取得 ←(注: 冒頭_アナウンスのnextはscript_日付取得 → 冒頭_アナウンス2へ)
          → 冒頭_アナウンス2(Re-confirmation node data: nodeName=script_日付取得)
            → 診察券確認(TTS) → 入力_診察券確認(DTMF) → OpenAI_診察券確認
              → [ない] → 完了フラグ_診察券なし(status=7) → 診察券なし_アナウンス → 切断
              → [初めて] → 分岐1(CMR) → Jump_氏名聴取
              → [ある] → 分岐1(CMR) → Jump_診察券番号聴取
              → [success] → 着信電話番号分類(incoming-classifier)
                → 用件確認(TTS) → 入力_用件確認(DTMF) → OpenAI_用件確認
                  → [予約] → 受診歴確認 → ... → 診療科_聴取 → openAI_診療科
                              → 診療科分岐_2(CMR) → 各種終話/ルート分岐
                  → [変更/キャンセル] → 診療科_聴取 → openAI_診療科
                              → 診療科分岐_4(CMR) → 各種終話/ルート分岐
                  → [確認] → Flag_確認(status=1) → 終話_確認
                  → [その他問合せ] → Flag_確認(status=1) → 終話_問合せ
```

### 8.4 診療科分岐パターン（多段ContextMatchRouter）

同一の `openAI_診療科` 出力を、用件/フェーズ別に6つのContextMatchRouterで参照：

| CMR名 | 用途 | 主な分岐 |
|---|---|---|
| 診療科分岐 | 変更・検査ルート | 代表案内3科 → 診察日変更 |
| 診療科分岐_2 | 予約ルート | 直接来院2科, 予約不可1科, 代表午後3科, 再診2科, その他→受診歴確認 |
| 診療科分岐_3 | 紹介状確認後の予約 | 初診担当医聴取 → 紹介状確認(当院宛か否か) |
| 診療科分岐_4 | 変更/キャンセルルート | 代表案内3科, 再診担当医1科 → 注射装具確認 |
| 診療科分岐_5 | 担当医後の用件分岐 | 代表案内 or 予約希望日 |
| 診療科分岐_6 | 担当医分岐後の検査確認 | 検査有無確認 or 予約希望日 |

### 8.5 Script モジュール（新パターン）

#### script_日付取得
- **役割**: 今日から3営業日後の日付を計算し `$runner.setResult()` で返す
- **方法**: 外部API `https://holidays-jp.github.io/api/v1/{year}/date.json` を呼び出して祝日を取得
- **注意**: `HttpClient` / `URI` 等の Java型を使用する（Brekekeのランタイム依存）
- **出力形式**: `m月d日`（例: `5月15日`）

#### script_3days分岐
- **役割**: `openAI_現在の予約日` の出力（`yyyy-MM-dd 00:00:00` 形式）を取得し、今日/明日/明後日と比較
- **方法**: `$runner.getModuleResult("openAI_現在の予約日")` で他モジュール結果を参照
- **出力**: `代表案内`（当日/翌日/翌々日の場合）または `success`（それ以外）
- **遷移**: `^代表案内$` → Flag_代表案内 / `^.*$` → 理由_聴取（理由聴取へ）

### 8.6 Re-confirmation node data の非DOB活用

pair_11では `Re-confirmation node data` を通常の復唱（#data#）以外の用途で2箇所使用：

1. **冒頭_アナウンス2**: `nodeName=script_日付取得` → script_日付取得が返した `m月d日` をProperty.mdのプロンプト内の `#data#` に埋め込んで読み上げ
   - 効果: 毎日自動的に「X月X日以降のご予約〜」と日付が変わるアナウンスを実現

2. **理由_聴取**: `nodeName=OpenAI_用件確認` → 用件分類結果（変更/キャンセル等）を `#data#` で読み上げ
   - Property.mdの `理由_聴取.prompt={tts_g:#data# の理由を、簡潔にお話しください。}` で動的読み上げ

### 8.7 生年月日聴取 — 二段階OpenAI正規化（非標準パターン）

標準の `DOB Re-confirmation` モジュールを使わず、2つのOpenAIモジュールを連結：

```
入力_患者_生年月日(DTMF+STT)
  → openAI_患者_生年月日（STT/DTMFを「yyyy-MM-dd 00:00」に正規化）
    → openAI_生年月日正規化（「yyyy-MM-dd 00:00」→「yyyy年m月d日」に変換、TTS読み上げ用）
      → 復唱_患者_生年月日(Re-confirmation node data: module=openAI_生年月日正規化)
        → 入力_復唱_患者生年月日(DTMF+STT: "1番はい/2番いいえ")
          → openAI_復唱_患者生年月日（肯定/否定判定 → 肯定$/否定$）
```

- `openAI_患者_生年月日` プロンプトは DTMF8桁・西暦・和暦・STT先頭欠落補完の全ケースに対応する詳細アルゴリズム形式
- 標準の `DOB Re-confirmation`（`drjoy^TS Custom Module$DOB Re-confirmation`）と異なり、復唱確認後の肯定/否定判定まで明示的に実装

### 8.8 retry_count=1 パターン（多用）

本フローの多くのRetry Counterが `retry_count=1`（1回リトライ）を使用：

| retry_count | 該当モジュール数 | 用途 |
|---|---|---|
| 1 | 15 | 担当医、受診歴、紹介状、注射装具、検査等の任意聴取項目 |
| 2 | 2 | 用件確認、診察券確認（重要な必須聴取項目） |

`prompt_false` は全て `{tts_g: かしこまりました。折り返しの際に確認させていただきます。}` で統一（パターンA: 任意聴取→次へ進む）。

### 8.9 新status値・smsFlag値

| status | smsFlag | 意味 | 使用箇所 |
|---|---|---|---|
| 7 | -1 | 診察券なし/番号不明終話 | 完了フラグ_診察券なし |
| 22 | -1 | 直接来院案内 | 完了フラグ_直接来院 |
| 2 | -1 | 代表案内（SMS無効） | 非通知、各代表案内 |
| 1 | -1 | 宛先不一致（当院以外） | Flag_当院以外 |

> **smsFlag=-1** は「SMS送信をシステムレベルで無効化」を意味する。0との違いは施設側の設計次第だが、pair_11ではSMS不要な代表案内系に一律 -1 を使用。

### 8.10 OpenAIプロンプトスタイル — アルゴリズム形式

`openAI_診療科` は STEP_A〜STEP_G の詳細アルゴリズムを明示した形式：

```
## ■ Role / セキュリティ（最優先）
## ■ Context
## ■ 出力仕様
# ⚠ 絶対ルール（意味推測禁止・症状から推測禁止）
# 判定アルゴリズム
  ## 【STEP_A: 不明明示判定】
  ## 【STEP_B: 入力正規化】
  ## 【STEP_C: DTMF入力 → NO_RESULT】
  ## 【STEP_D: 完全一致判定】
  ## 【STEP_E: 部分一致判定（長い語優先）】
  ## 【STEP_F: 症状のみ → NO_RESULT】
  ## 【STEP_G: 該当なし → NO_RESULT】
# Few-shot出力例（表形式）
```

このアルゴリズム形式は複数の診療科が存在する大病院向けの詳細な診療科判定に有効。

### 8.11 Property.md 新URLフィールド

pair_11の Property_fix.md には3つの新規URLフィールドが追加されている：

```
drjoy.save.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/brekeke-booking-ai
get-intonation-from-drjoy.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/brekeke-replace-intonation
phone_2_name.url=https://reserve.drjoy.jp/api/anonymous/dr/ha/phone-to-name
```

また `speech.rag.url` が以前のペアと異なる形式：
```
speech.rag.url=https://develop-speech.famishare.jp/api/v1/rag  # pair_11 固有（開発環境）
```

> **注意**: `amivoice.uri=ws://speech.internal.assistant.com:8000/ws` はIPアドレスではなくホスト名形式。これは施設固有の内部DNS設定によるもの。

---

## 付録A: 全ペアのフロー構成サマリー

| Pair | メインフロー | サブフロー | 総モジュール数 |
|------|------------|-----------|-------------|
| 01 | 健診Demo(120) | 電話番号確認(19), RAG検索(13) | ~152 |
| 02 | 診療-Demo(60) | 個人情報(32), 診察予約(~40), 診察変更(~24), 診察キャンセル(~18), 検査変更(~24), 検査キャンセル(~18), 予防接種予約(~19), 予防接種変更(~24), 予防接種キャンセル(18), 送迎予約(~13), 送迎変更(~18), 送迎キャンセル(~13), RAG(10) | ~330+ |
| 03 | 診療(~100) | 診療科②聴取_1(70), 診療科②聴取_2_1(73), 個人情報(39), RAG検索(11) | ~293 |
| 04 | 健診(79) | 個人情報(36), RAG検索(13) | 128 |
| 05 | 診療Demo(91) | 個人情報(44), 個人情報_2(34), RAG検索(10) | ~179 |
| 06 | 診療-Demo(60) | 個人情報-ymc(47), 診療科聴取(11)×3, RAG検索(9) | ~160 |
| 07 | 診療-Demo(133) | 個人情報-1(49), 個人情報-2(23) | ~205 |
| 08 | 診療-Demo(78) | 用件(19), 電話番号(18), 生年月日(8), 氏名(5) | ~128 |
| 09 | 診療-Demo(93) | 用件(14), 氏名(5), 生年月日(8), 電話番号(19), RAG検索(10) | ~149 |
| 11 | 診療(186) | 氏名聴取(4), 生年月日聴取(12), 診察券番号聴取(9), 電話番号聴取(24), RAG検索(9) | ~244 |

## 付録B: コンテキストフィールド出現頻度

| contextName | 出現ペア数 | displayType | 備考 |
|-------------|----------|-------------|------|
| patientName | 10/10 | TEXT | |
| patientDateOfBirth | 10/10 | DATE_OF_BIRTH | |
| telephoneNumber | 10/10 | PHONE_NUMBER_CALL | |
| additionalPhoneNumber | 10/10 | PHONE_NUMBER | |
| classification | 10/10 | CLASSIFICATION | |
| status | 10/10 | STATUS | |
| clinicalDepartment | 8/10 (診療のみ) | DEPARTMENT | |
| medicalCardNumber | 8/10 | NUMBER | |
| reservationDate / currentAppointmentDate | 8/10 | DATE | pair_11は currentAppointmentDate |
| question | 9/10 | TEXT | |
| reason | 5/10 | TEXT | |
| diagnosis / Condition | 4/10 | TEXT | |
| introduction / Referral | 4/10 | TEXT | pair_11は Referral（非標準命名） |
| phonetype | 3/10 | TEXT | |
| inquiry | 2/10 | TEXT | 担当医名格納（CLAUDE.md推奨） |
| appointmentDate | 1/10 | DATE | pair_11 固有（予約日） |
| desiredAppointmentDate | 1/10 | TEXT | pair_11 固有（予約希望日） |
| multipleDepartments | 1/10 | TEXT | pair_11 固有（複数診療科） |
| address | 1/10 | TEXT | pair_11 固有（住所） |

## 付録C: モジュールタイプ使用頻度

| モジュールタイプ | 全ペア使用 | 備考 |
|---------------|----------|------|
| Text to speech | 10/10 | 最多使用。全聴取項目に必須 |
| Speech to Text (AmiVoice) | 10/10 | フリーワード入力用 |
| DTMF AmiVoice STT Input | 10/10 | 生年月日・電話番号・数値入力 |
| generate_by_OpenAI | 10/10 | 全分類・正規化に使用 |
| Speech Retry Counter | 10/10 | 全入力にリトライ必須 |
| save2db | 10/10 | 全TTS/STTにsubs接続 |
| saveCompletionFlag2db | 10/10 | 終話フラグ |
| saveContextModel2DB | 10/10 | コンテキスト定義(開始チェーン) |
| incoming-classifier | 10/10 | 非通知分岐 + 電話番号サブフロー |
| Custom$wait | 10/10 | 冒頭待ち時間 |
| @IVR$Disconnect | 10/10 | 終話切断 |
| Custom Jump to Flow | 10/10 | サブフロー遷移 |
| ContextMatchRouter | 9/10 | 用件分岐、終話分岐 |
| Re-confirmation node data | 9/10 | 復唱(#data#)。pair_11では非DOB用途でも使用（動的日付・分類結果の読み上げ） |
| DOB Re-confirmation | 7/10 | 生年月日復唱。pair_11は使わず二段階OpenAI方式を採用 |
| Phone Normalization | 7/10 | 電話番号正規化 |
| RAG | 9/10 | FAQ応答 |
| @General$Script | 9/10 | SSML化、バリデーション、業務ロジック |
| acceptance_times | 4/10 | 営業時間チェック（pair_03,04,08,11） |
| @IVR$Call Transfer | 2/10 | 有人転送 |
