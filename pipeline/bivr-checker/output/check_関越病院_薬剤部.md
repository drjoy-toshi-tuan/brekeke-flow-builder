# 品質検証レポート: 関越病院_薬剤部

- 対象ファイル: `output/関越病院_薬剤部_20260416.json`
- 設計書: `input/関越病院_薬剤部/【薬剤部1】：関越病院.md`
- Property.md: `input/関越病院_薬剤部/properties_関越病院_薬剤部.md`
- モジュール数: 70
- 検証日: 2026-04-22

---

## サマリー

| 重要度 | 件数 |
|--------|------|
| CRITICAL | 45 |
| WARNING | 37 |
| INFO | 9 |
| **合計** | **91** |

---

## CRITICAL (45件)

### Stage 1: 構造 — matchingmethod (8件)

全Retry Counterのmatchingmethodが1になっている。Retry Counterは0が必須。

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | R-MM / S1-MM | リトライ_薬局名 | matchingmethod=1 (0であるべき) |
| 2 | R-MM / S1-MM | リトライ_用件確認 | matchingmethod=1 (0であるべき) |
| 3 | R-MM / S1-MM | リトライ_担当者名 | matchingmethod=1 (0であるべき) |
| 4 | R-MM / S1-MM | リトライ_診療科 | matchingmethod=1 (0であるべき) |
| 5 | R-MM / S1-MM | リトライ_問い合わせ内容_疑義照会 | matchingmethod=1 (0であるべき) |
| 6 | R-MM / S1-MM | リトライ_問い合わせ内容_報告 | matchingmethod=1 (0であるべき) |
| 7 | R-MM / S1-MM | リトライ_折返し有無 | matchingmethod=1 (0であるべき) |
| 8 | R-MM / S1-MM | リトライ_問い合わせ内容_その他 | matchingmethod=1 (0であるべき) |

### Stage 1: 構造 — next/subsスロット数 (22件)

#### ContextMatchRouter: next=11 (期待: 10)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | S1-SLOTS | 用件分岐1 | nextスロット数=11 (期待: 10) |
| 2 | S1-SLOTS | 用件分岐2 | nextスロット数=11 (期待: 10) |
| 3 | S1-SLOTS | 終話分岐_電話種別 | nextスロット数=11 (期待: 10) |

#### save2db: subs=3 (期待: 0)

save2dbモジュールはsubs=0が規定値。12モジュール全てが不正。

| # | コード | モジュール |
|---|--------|------------|
| 4 | S1-SLOTS | save-END_非通知 |
| 5 | S1-SLOTS | save-END_時間外 |
| 6 | S1-SLOTS | save-END_聴取失敗 |
| 7 | S1-SLOTS | save-END_折返し不要 |
| 8 | S1-SLOTS | save-END_折返しあり_入電番号 |
| 9 | S1-SLOTS | save-END_折返しあり_聴取番号 |
| 10 | S1-SLOTS | save-clinicalDepartment2 |
| 11 | S1-SLOTS | save-classification |
| 12 | S1-SLOTS | save-Desiredreservation |
| 13 | S1-SLOTS | save-clinicalDepartment |
| 14 | S1-SLOTS | save-reason |
| 15 | S1-SLOTS | save-details |

#### Disconnect: subs=3 (期待: 0)

| # | コード | モジュール |
|---|--------|------------|
| 16 | S1-SLOTS | 切断_非通知 |
| 17 | S1-SLOTS | 切断_時間外 |
| 18 | S1-SLOTS | 切断_聴取失敗 |
| 19 | S1-SLOTS | 切断_折返し不要 |
| 20 | S1-SLOTS | 切断_折返しあり_入電番号 |
| 21 | S1-SLOTS | 切断_折返しあり_聴取番号 |

#### wait: subs=0 (期待: 3)

| # | コード | モジュール |
|---|--------|------------|
| 22 | S1-SLOTS | 冒頭 (Custom$wait) |

### Stage 1: 構造 — saveContextModel2DB fields (3件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | CTX-CALLID | コンテキスト設定 | callId.itemDefault=True (falseであるべき) |
| 2 | CTX-CALLID | コンテキスト設定 | callId.displayType=TEXT (NUMBERであるべき) |
| 3 | CTX-STATUS | コンテキスト設定 | status.rangeValues=4個 (5個であるべき)。現在: 未処理/案内/聴取失敗/時間外。不足: 途中切断(id=0)。また "案内" は "代表案内"、"聴取失敗" は "転送" に修正が必要 |

### Stage 1: 構造 — 冒頭チェーン (2件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | FLOW-007 | (フロー全体) | 冒頭チェーンにTTSモジュールが存在しない。acceptance_times の true 遷移先が「薬局名」TTS（冒頭アナウンスではない）。設計書では「お電話ありがとうございます。関越病院の疑義紹介専用、AI電話です。まず初めに、薬局名をお話ください。」が冒頭で、これは1つのTTSだが冒頭アナウンスと薬局名聴取が一体化している |
| 2 | FLOW-007-NOTE | (フロー全体) | 本案件は冒頭アナウンスと薬局名聴取を「薬局名」TTSに一体化した設計のため、FLOW-007は設計意図としては許容可能。ただしProperty.mdの薬局名.promptが「まず初めに、薬局名をお話ください。」のみで、冒頭挨拶部分（お電話ありがとうございます...）が欠落している可能性がある |

### Stage 1: 構造 — ContextMatchRouterデフォルト遷移先 (3件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | CMR-DEFAULT | 用件分岐1 | ^.+$ (Other) の遷移先が空。デフォルト分岐時に遷移できない |
| 2 | CMR-DEFAULT | 用件分岐2 | ^.+$ (Other) の遷移先が空。デフォルト分岐時に遷移できない |
| 3 | CMR-DEFAULT | 終話分岐_電話種別 | ^.+$ (Other) の遷移先が空。デフォルト分岐時に遷移できない |

### Stage 1: 構造 — CompletionFlag status値 (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | COMP-STATUS | 完了フラグ_聴取失敗 | status="3" (転送)。聴取失敗の終話でstatus=3(転送)は不適切。status="2"(代表案内)が妥当 |

### Stage 1: 構造 — 用件確認DTMF設定 (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | DTMF-MAXLEN | 入力_用件確認 | 用件選択DTMFのmax_dtmf_lengthが適切か要確認。1桁入力（1/2/3）なのでmax_dtmf_length=1が推奨 |

### Stage 4: Property.md — 冒頭プロンプト不一致 (5件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | PROP-PROMPT | 薬局名 | Property.mdの薬局名.promptは「まず初めに、薬局名をお話ください。」だが、設計書では冒頭挨拶「お電話ありがとうございます。関越病院の疑義紹介専用、AI電話です。」を含むべき |
| 2 | PROP-001 | END_非通知 | Property.mdにTODO_発話内容を記入のまま |
| 3 | PROP-001 | END_時間外 | Property.mdにTODO_発話内容を記入のまま |
| 4 | PROP-001 | END_聴取失敗 | Property.mdにTODO_発話内容を記入のまま |
| 5 | PROP-002 | (フロー全体) | office_id=TODO_要確認 のまま |

---

## WARNING (37件)

### Stage 1: 構造 — prompt_true スペース不一致 (8件)

全Retryのprompt_trueに句点後のスペースがない。
- 現在: `{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}`
- 正解: `{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}`

| # | コード | モジュール |
|---|--------|------------|
| 1 | R-PT | リトライ_薬局名 |
| 2 | R-PT | リトライ_用件確認 |
| 3 | R-PT | リトライ_担当者名 |
| 4 | R-PT | リトライ_診療科 |
| 5 | R-PT | リトライ_問い合わせ内容_疑義照会 |
| 6 | R-PT | リトライ_問い合わせ内容_報告 |
| 7 | R-PT | リトライ_折返し有無 |
| 8 | R-PT | リトライ_問い合わせ内容_その他 |

### Stage 1: 構造 — 標準フィールド不足 (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | CTX-STD12 | コンテキスト設定 | 標準フィールド "reservationDate" なし。本案件は薬剤部で予約日不要のため設計意図としては妥当だが、標準12フィールド準拠からは逸脱 |

### Stage 1: 構造 — acceptance_times label (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | AT-LABEL | 受付時間判定 | true遷移のlabelが "acceptable" (標準は "true")。Brekekeは動作するが標準形式との差異あり |

### Stage 2: profile_words — 空欄 (5件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | PW-EMPTY | 入力_薬局名 | profile_words が空。薬局名の音声認識精度に影響 |
| 2 | PW-EMPTY | 入力_担当者名 | profile_words が空。人名の音声認識精度に影響 |
| 3 | PW-EMPTY | 入力_問い合わせ内容_疑義照会 | profile_words が空 |
| 4 | PW-EMPTY | 入力_問い合わせ内容_報告 | profile_words が空 |
| 5 | PW-EMPTY | 入力_問い合わせ内容_その他 | profile_words が空 |

### Stage 3: OpenAI — next条件 (3件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | PROMPT-001 | OpenAI_用件確認 | next条件 `^.*$` (デフォルト) がprompt出力仕様との対応不明 |
| 2 | PROMPT-001 | OpenAI_診療科 | next条件 `^.*$` (デフォルト) がprompt出力仕様との対応不明 |
| 3 | PROMPT-001 | OpenAI_折返し有無 | next条件 `^.*$` (デフォルト) がprompt出力仕様との対応不明 |

### Stage 4: Property.md — TODO残存 (12件)

| # | コード | 内容 |
|---|--------|------|
| 1 | PROP-TODO | `TODO_` で始まる値は実際の値に置き換えてから使用してください (ヘッダー注記) |
| 2 | PROP-TODO | END_非通知.prompt=TODO_発話内容を記入 |
| 3 | PROP-TODO | END_時間外.prompt=TODO_発話内容を記入 |
| 4 | PROP-TODO | END_聴取失敗.prompt=TODO_発話内容を記入 |
| 5 | PROP-TODO | 患者_診察券番号.prompt=TODO_発話内容を記入 |
| 6 | PROP-TODO | 患者_氏名.prompt=TODO_発話内容を記入 |
| 7 | PROP-TODO | 患者_連絡先.prompt=TODO_発話内容を記入 |
| 8 | PROP-TODO | 相談_問合せ.prompt=TODO_発話内容を記入 |
| 9 | PROP-TODO | 相談_問合せループ.prompt=TODO_発話内容を記入 |
| 10 | PROP-TODO | 相談_FAQ失敗.prompt=TODO_発話内容を記入 |
| 11 | PROP-TODO | 終話_失敗.prompt=TODO_発話内容を記入 |
| 12 | PROP-TODO | office_id=TODO_要確認 |

### Stage 4: Property.md — detection_flag (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | PROP-DF | (フロー全体) | Property.md amivoice.detection_flag=音声開始前から検出。CLAUDE.md標準は "検出しない"。要確認 |

### Stage 1: 構造 — Retry日本語接続 (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | R-TTS-JP | リトライ_用件確認 | 「再度、」+「ご用件を、次の3つのうち、いずれかでお話ください。1、疑義照会...」は自然だが、DTMF選択式の質問に対して「再度、」で始まるリトライが最適か要検討 |

### Stage 1: 構造 — ContextMatchRouter用件分岐 value="default" (2件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | CMR-VAL-DESIGN | 用件分岐1 | module1Value2="default" — OpenAI出力値に "default" が含まれるか要確認。通常は具体的な値（疑義照会/報告等）を設定 |
| 2 | CMR-VAL-DESIGN | 用件分岐2 | module1Value2="default" — 同上 |

### Stage 4: Property.md — rag_ssml.url (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | PROP-003 | (フロー全体) | rag_ssml.url がdemo環境URL (demo-reserve.famishare.jp)。本番デプロイ前にprod URLへの変更が必要 |

### Stage 1: 構造 — Retryリトライ用件確認接続先 (1件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | R-TTS-TARGET | リトライ_用件確認 | Retry true遷移先が「用件確認」TTS。用件確認のpromptがProperty.md管理でインライン空のため、Property.md設定が完了していれば問題なし |

---

## INFO (9件)

### Stage 4: Property.md — サブフロー用キー (7件)

以下はメインフロー内のTTSには存在しないが、サブフロー用として正常。

| # | コード | モジュール |
|---|--------|------------|
| 1 | PROP-SUBFLOW | 患者_診察券番号 |
| 2 | PROP-SUBFLOW | 患者_氏名 |
| 3 | PROP-SUBFLOW | 患者_連絡先 |
| 4 | PROP-SUBFLOW | 相談_問合せ |
| 5 | PROP-SUBFLOW | 相談_問合せループ |
| 6 | PROP-SUBFLOW | 相談_FAQ失敗 |
| 7 | PROP-SUBFLOW | 終話_失敗 |

### Stage 2: profile_words — フィラー不足 (2件)

| # | コード | モジュール | 内容 |
|---|--------|------------|------|
| 1 | PW-FILLER | 入力_折返し有無 | フィラー10種不足 (あ, あー, あの, あのー, え...) |
| 2 | PW-FILLER | 入力_診療科 | フィラー10種不足 (あ, あー, あの, あのー, えー...) |

---

## 正常確認済み項目

以下の項目は問題なし:

| 検証項目 | 結果 |
|----------|------|
| 冒頭チェーン順序 (wait -> SCM2DB -> IC -> AT) | OK |
| incoming-classifier 数 | 1個 (正常) |
| detection_flag (全STT/DTMF) | 全て "デフォルト" (正常) |
| STT next (TIMEOUT/ERROR/NO_RESULT/success) | 全STT/DTMFで正常 |
| OpenAI params.module | 全て実在モジュール参照 (正常) |
| OpenAI promptTTS | 全て空欄 (正常) |
| OpenAI prompt 4セクション | 全て # Role / # Context / 出力仕様 / セキュリティ あり |
| TTS next label | 全て "Next Module" (正常) |
| TTS stop_by_dtmf | 全て "Yes" or "No" (正常) |
| Retry condition/label | 全て true/Retry, false/No more (正常) |
| save2db next遷移 | 全てnext=0 (正常、next遷移なし) |
| Custom Jump to Flow flowname | 全て設定済み |
| saveContext2DB contextName/Value | 全て設定済み |
| 遷移先存在確認 | 全nextModuleName/subs参照先が実在 |
| 到達可能性 | 全モジュールがstartから到達可能 |
| モジュール命名 | 環境依存文字・括弧・スペースなし |
| CompletionFlag status 0/5 | 未使用 (正常) |
| Property.md 必須セクション | amivoice設定群/API URL群/RAG設定群 全て存在 |
| ContextMatchRouter module1Name==module2Name | 全て一致 (正常) |
| ContextMatchRouter module1ValueN==module2ValueN | 全て一致 (正常) |
| ContextMatchRouter paramsキー交互配置 | 正常 |

---

## 修正優先度

### 即時対応必須 (Brekekeアップロード失敗の可能性)

1. **全Retry matchingmethod: 1 -> 0** (8モジュール)
2. **ContextMatchRouter nextスロット: 11 -> 10** (用件分岐1, 用件分岐2, 終話分岐_電話種別)
3. **save2db subsスロット: 3 -> 0** (12モジュール)
4. **Disconnect subsスロット: 3 -> 0** (6モジュール)
5. **冒頭 (wait) subsスロット: 0 -> 3** (1モジュール)
6. **ContextMatchRouter デフォルト遷移先空**: 3モジュールに適切な遷移先を設定

### 早期対応 (データ品質)

7. **callId fields修正**: itemDefault=false, displayType=NUMBER
8. **status rangeValues**: 5値に修正 (途中切断/未処理/代表案内/転送/時間外)
9. **完了フラグ_聴取失敗 status**: "3" -> "2" (聴取失敗は代表案内扱いが妥当)
10. **prompt_true スペース追加**: 句点後にスペース挿入 (8モジュール)
11. **Property.md TODO解消**: 11箇所のTODO_を実際の値に置換
12. **Property.md 薬局名.prompt**: 冒頭挨拶を含める

### 品質向上 (音声認識精度)

13. **profile_words設定**: 入力_薬局名, 入力_担当者名, 問い合わせ内容系3モジュール
14. **フィラー追加**: 入力_折返し有無, 入力_診療科
