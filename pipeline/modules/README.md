# modules/ — 認定モジュール・script レジストリ

OpenAI プロンプト層から決定論へ置き換える部品の置き場と認定台帳。
**受入テスト通過が全部品の必須要件**（CLAUDE.md「モジュール / script 開発ポリシー」参照）。
置き換えの優先順位: `docs/governance/deterministic-replacement-roadmap.md`

> **認定ゲートは engine/spec 二段判定 v2**（`docs/governance/part-certification-spec.md`）。
> 各部品を **engine**（部品種別の刻印＝全用途で不変のアルゴリズム）/ **spec**（受入必須の分類データ）/
> **wiring**（入力元・保存先＝除外）に分け、`certified_hashes.json` の `parts`（engine の正）と
> `specs`（`engine_hash:spec_hash` の認定台帳）で照合する。**engine 不一致はブロック・新規 spec は受入要求**。
> 旧「設定行除外ハッシュ」（単一ハッシュ）は廃止。

## 認定済み部品（受入テスト通過）

| 部品 | 置き換えた判定 | テスト実績 | 認定日 | 正本の場所 |
|---|---|---|---|---|
| BusinessHour Classifier | 曜日別営業時間 + 祝日 + 固定休（6 分岐）+ 過去日ガード | oracle 35/35 + **実機受入 35/35（2026-06-04、過去日ガード BH-26〜34 含む、PASS_全件PASS 到達）** | 2026-05-29（過去日ガード改訂・実機再受入 2026-06-04） | `modules/business_hour_classifier/` |
| FAQ Matcher | FAQ 照合（OpenAI 不使用の決定論 RAG。NFKC + 文字 2-gram + BM25 + coverage、+ **exact-match 短絡** + **IDF-coverage マージンゲート**で STT 誤認識・総論曖昧・真重複を安全に転送。+ **NO_QUESTION 前段ゲート**で否定/終了応答を分離。+ **発話の揺れフォールバック**（反復畳み込み・文/言い直し/逆接の節分割→exact-match優先で再照合）で会話的前置き・言い直し・反復を吸収）| oracle **69/69**（NO_QUESTION 26 + 節分割/反復 6 + 本番コーパス揺れ吸収 10 込）+ 実コーパス 429 q-variant 自己検索回帰 0（NOT_FOUND は既知の真重複 送迎バス 2 件のみ）。検索本体 実機 検索 14/14・実践 32/32（2026-06-05）。**NO_QUESTION 前段ゲート + 揺れフォールバック + コーパス変種追加分の実機再受入（Nashorn）は未実施** | 2026-06-05（NO_QUESTION 前段ゲート 2026-06-10 / 揺れフォールバック+口語変種 2026-06-10・実機再受入待ち） | `modules/faq_matcher/` |
| DOB Re-confirmation | 生年月日復唱（openAI_prompt 削除済） | oracle 44/47（残 3 件は仕様上の衝突として整理済）+ デプロイ済 JS バイト一致 | 2026-06-01（repo 収容 2026-06-17） | `modules/dob_reconfirmation/`（TZ 固定済み正本 `module_value.js`。custom-module 型ゆえ P6 ハッシュゲート対象外＝二段判定未登録。parity オラクル収容は follow-up） |
| 現在の予約日 script | 相対日付解決（あした / 今週X曜 / 昨日等） | Part 1+2 439/439 + Part 3 11 ケース | 2026-05-28 | テンプレ修正済（**TODO: リポジトリへ収容。本番 現在の予約日.txt は未反映**） |
| Department Classifier | 診療科分類（OpenAI_診療科 置換。公式30科辞書・最長一致・NFKC実効サブセット正規化。出力 = 科名 / 登録なし(わからない) / NO_RESULT(再質問)）| oracle 89/89 + **実機受入 89/89（Pattern 6 単体、2026-06-09、`[TEST FAIL]` 0・`[TEST DONE]` 到達。皮膚科誤分類 0）**。Nashorn↔Python パリティ全89一致 | 2026-06-09 | `modules/department_classifier/` |
| Reservation Date Classifier | 変更/キャンセル時の予約日パーサ（自由発話・DTMF → `YYYY-MM-DD 00:00` / `不明` / `NO_RESULT`。期間制限なし版。OpenAI 不使用。`new Date()`→Asia/Tokyo 固定。来週/今週=暦週・月曜始まり、明示的相対は過去でも翌年送りせず literal。**v2(#265): has_月回収 Rule A/B + 事故①曖昧時期→不明**）| oracle **63/63** + **実機受入 29/29 PASS（Pattern 6 単体・日付非依存ケース、2026-07-02、`[TEST FAIL]` 0・`[TEST DONE]` 到達）**。相対日付/月末/補正/STT補正は oracle（today パラメタ化）で網羅。`certified_hashes` 登録 engine v2 `22cc6f12`（spec空） | 2026-07-02（engine v2・#265）| `modules/reservation_date_classifier/`（engine 22cc6f12 v2）|
| n_choice（N択エンジン）| DTMF/音声キーワードの N 択選択（発信元/患者区分/相談種別 等。OpenAI 不使用の汎用エンジン。`{{…}}` を設問ごとに充填）| oracle **29/29**（2026-06-12、config=亀田・発信元3分類）+ **実機受入 29/29（Pattern 6 単体、2026-06-16、全 case `_cmr:1`/`_pass:ok`・`_fail` 0・`ログ_終了:done` 完走。Nashorn↔Python パリティ全29一致、bivr埋込↔正本バイト一致確認済）**。engine/spec 二段判定ゲートで認定（engine 67276506 / spec 682a9b04）。**カレス記念病院_診療 3spec追加認定（2026-07-16）**: 受診歴_はいいいえわからない（実機33/33）/服薬有無（実機21/21）/残薬確認2択版（実機19/19）、計73/73 PASS・engine不変（spec c368c694/7d92a284/6e0f924f） | 2026-06-16（oracle+実機受入 完了）／カレス3spec追加 2026-07-16 | `modules/n_choice/`（髙橋 VFB-Script 由来）|
| inquiry_classifier（用件分類）| 総合相談室の用件自由発話分類（`OpenAI_用件確認` 置換。相談/予約/大代表/定型案内/その他/NO_RESULT。顧客大原則=相談優先・予約弾き）| oracle **30/30**（2026-06-12）+ **実機受入 30/30（Pattern 6 単体、2026-06-16、全 case `_cmr:1`/`_pass:ok`・`_fail` 0・`ログ_終了:done` 完走。Nashorn↔Python パリティ全30一致、bivr埋込↔正本バイト一致確認済）**。`その他`/`NO_RESULT` は決定論ポリシー（安全側）、語彙重複（外来時間等）は既知の限界で実データ調整前提 | 2026-06-16（oracle+実機受入 完了）| `modules/inquiry_classifier/`（髙橋 VFB-Script エンジン＋亀田語彙）|
| phone_type（電話種別判定）| 電話番号文字列 → 携帯/固定/その他（`slot: phone` の決定論インライン展開。050=その他＝本番 `script_携帯判別` 準拠。テンプレ 050=携帯 を上書き）| oracle **20/20**（2026-06-17・050/フリーダイヤル/国際表記/桁不足 含む）。bivr 埋込↔正本バイト一致（wiring=SOURCE_MODULE のみ）。**実機受入 20/20（Pattern 6 単体、2026-06-17・厚木1flow・`PASS_全件PASS:OK` 到達、Nashorn↔Python パリティ全20一致）。engine+spec 認定済** | 2026-06-17（oracle+実機受入 完了）| `modules/phone_type/` |
| checkup_intent_classifier（用件分類）| 健診CC の用件自由発話分類（`OpenAI_用件確認` 置換。新規/変更/キャンセル/問い合わせ等＋遅刻種別。NFKC 正規化・SCOPE=full/lateness を wiring で切替）| oracle **full 65/65 + lateness 14/14**。**実機受入: 厚木統合CC P6 単体（共通生成器 `build_classifier_acceptance_bivr.py`、2026-06-16／WS2 語彙〔その他・そのほか・時刻・番正規化〕追加 2026-06-18）で認定（`certified_hashes.json` 登録済 e6a11b53 / 636a6b45）** | 2026-06-16（WS2 spec 2026-06-18）| `modules/checkup_intent_classifier/`（engine 2a3af7da v2）|
| checkup_course_classifier（コース分類）| 健診CC のコース分類（NFKC 正規化・FOLDINGS/CATEGORIES）| oracle **52/52**。**実機受入: 厚木統合CC P6 単体（2026-06-16）で認定（`certified_hashes.json` 登録済 b132fd2e）** | 2026-06-16 | `modules/checkup_course_classifier/`（engine da49f5e6 v2）|
| checkup_menu_classifier（メニュー分類）| 健診CC のエリア別メニュー分類（MENU=spec 選択子。area / shinjuku_shibuya / tokyo_shinagawa の 3 エリア spec）| oracle **43/43**。**実機受入: 厚木統合CC P6 単体（2026-06-16／WS2 語彙〔番・広岡・west・ウェスト〕追加 2026-06-18）で認定（`certified_hashes.json` に 3 エリア spec を WS2 版含め登録済）** | 2026-06-16（WS2 spec 2026-06-18）| `modules/checkup_menu_classifier/`（engine 708d4898 v2）|
| text_normalizer（自由テキスト正規化）| 自由テキスト聴取値のクリーン化（分類ではなく変換器。フィラー除去・全角→半角・句読点正規化・連続空白圧縮・文末丁寧体コピュラ除去〔です/でした/ですね/ですよ/ですわ・v2〕。「ます」系は語幹/否定の意味を壊すため対象外）| oracle **33/33** + **実機受入 24/24 PASS（カレス記念病院_診療、group カレス記念病院_診療_20260716$テキスト正規化v1、2026-07-16）**。初回実機で4件FAIL（T04/T12/T14/T16）は p6_acceptance.yaml の期待値が v2 コピュラ除去未反映の誤りと判明・修正後再実機で24/24 PASS | 2026-07-16 | `modules/text_normalizer/`（engine 194e1f98 v2）|
| yes_no_classifier（Yes/No 判定）| Yes/No 自由発話判定。2 spec: **同意質問**（これでよろしいですか）/ **存在質問**（ご相談はありますか・#254）。存在質問では 問題ありません/大丈夫/結構です/特になし は否定（用件なし）| oracle 同意 **243/243** + 存在 **45/45**。**実機受入 P6: 同意 243/243（part1+part2）+ 存在 45/45（2026-07-02・engine v3 フル再認定）。`certified_hashes.json` 登録済 spec d0d533bf（同意）/ 2b1fe1bb（存在）** | 2026-07-02（engine v3・#254/#256）| `modules/yes_no_classifier/`（engine ce3c09f5 v3）|
| 用件抽出 パーサ（inquiry_extractor, v2 全決定論）| 自由発話 STT を**直接**解析（OpenAI不使用）→ 用件種別（新規/変更/キャンセル/問い合わせ）＋各スロット（診療科/予約希望日/予約日時/氏名=常に空/連絡先/生年月日/診察券番号）＋用件概要文へ分解。**氏名は inquiry_extractor で抽出しない（STT誤認識リスク→氏名聴取ステップで後段回収）**。商談デモ フリー発話受付の `用件抽出`。正本=`docs/brekeke/script_templates/inquiry_extractor.js`（テンプレ）| oracle 26/26 + 実機受入 26/26（2026-06-16）+ 再cert 26/26 PASS（2026-06-17）。**再々cert 26/26 PASS（2026-06-18・call 09065765660・氏名抽出除去版・全 `_cmr:1`/`_pass:ok`・`[TEST FAIL]` 0・`終了:OK` 6秒完走）。Nashorn↔Python パリティ全26バイト一致** | 2026-06-16（再cert 2026-06-17・再々cert 2026-06-18）| `modules/inquiry_extractor/`（oracle/test/受入）|
| field_normalizer（聴取値の単独フィールド正規化）| 聴取経路の生STTを kind 別に正規化（name=前置/丁寧/敬称除去・phone/card=数字抽出・birthday=和暦/西暦→YYYY-MM-DD 00:00:00変換(DATE_OF_BIRTHウィジェット形式)・department=辞書最長一致・date=末尾丁寧除去・raw=無変換）。商談デモ 終端 `drjoy_finalize` が save2db 前に適用し抽出経路と品質を揃える。正本=`docs/brekeke/script_templates/drjoy_finalize.js`（テンプレ）| oracle 33/33 + **実機受入 PASS（連結テスト case2 全聴取、2026-06-17、call 202000006723 `[DRJOY-FINALIZE]`: 氏名=山田太郎/診察券番号=12345/生年月日=昭和60年4月1日 等・save2db クリーン値で確定）。Nashorn↔Python パリティ一致** | 2026-06-17 | `modules/field_normalizer/`（oracle/test）|
| field_presence（L1 答え取得判定）| 各聴取STT直後の入力ゲート L1。kind(department/date/phone/birthday/card)別に当該フィールドの答えが含まれるか判定し PRESENT/ABSENT（雑音質問混在でも答え優先・診察券は no-card 表明も PRESENT）。商談デモ 全STT入力ゲートの「取得→次へ / 未取得→L0」。正本=`docs/brekeke/script_templates/field_presence.js`（テンプレ）| oracle 33/33 + **実機受入 32/32 PASS（Pattern 6 単体・5 KIND、2026-06-17、call 09065765660、全 `_cmr:1`/`_pass:ok`・`[TEST FAIL]` 0・`終了:OK` 到達）。Nashorn↔Python パリティ全32一致** | 2026-06-17 | `modules/field_presence/` |
| go_back_classifier（L0 戻る/繰り返し検知）| 各聴取STT入力ゲートの L0（L1=ABSENT 時）。戻る（やっぱり変更/キャンセル/別の用件/最初から/やり直し）・繰り返し（もう一回言って/もう一度/聞こえなかった）・NONE に分類。**「変更したい/キャンセルしたい」単独は用件語なので NONE（"やっぱり〜" で戻る）**。商談デモ「戻る→用件フリー聴取 / 繰り返し→当該聴取 / NONE→FAQ」。正本=`docs/brekeke/script_templates/go_back_classifier.js`（テンプレ）| oracle **24/24**（戻る9/繰り返し6/NONE9、用件語負例 nn06-09 追加 2026-06-18）。**P6 再cert 24/24 PASS（2026-06-18・call 09065765660・全 `_cmr:1`/`_pass:ok`・`[TEST FAIL]` 0・`終了:OK` 2秒完走）。Nashorn↔Python パリティ全24バイト一致** | 2026-06-17（P6再cert 2026-06-18） | `modules/go_back_classifier/` |
| triage_router（受診相談 決定論トリアージ）| 受診相談パスCの `受診相談_LLM問診`（generate_by_OpenAI）置換。主訴(用件フリー聴取)＋症状詳細聴取 の自由発話を A→B→C→D Top-Down Exclusion で走査（CPA/共通致死語/カテゴリ別RedFlag/修飾因子・over-triage bias・機械ランクダウン禁止）し **GOAL1_救急/GOAL2_看護師/GOAL3_通常** を判定→CMR で END 3種を選択。閉じた質問は冒頭の緊急度確認1問のみ（実データ=患者86%自由発話・純yes/no回答者0）。JTAS＋消防庁「電話相談」プロトコル準拠。正本=`docs/brekeke/script_templates/triage_router.js`（テンプレ）| oracle **39/39 PASS**（A0/ABCD/B各カテゴリ/共通致死語/C修飾因子/D/優先順位＋分類7＋決定論）。**実機 P6 受入 27/27 PASS（2026-07-06・call 09065765660・全 `_clf` 期待一致・全 `_cmr:1`/`_pass:ok`・`[TEST FAIL]` 0・`切断:OK` 6秒完走）。Nashorn↔Python パリティ全27一致**（受入 spec: `modules/triage_router/acceptance_test/p6_acceptance.yaml`〔abcd非依存の自由発話分〕・bivr: `tools/build_part_acceptance_bivr.py triage_router`） | 2026-07-06（oracle＋P6実機認定） | `modules/triage_router/`（oracle/test/受入・engine ハッシュ台帳未登録＝他demo部品と同運用） |
| ambiguity_gate（曖昧検出ゲート）| 紛れペア（最小対）の曖昧検出器（決定論分類・多段構成）| oracle **18/18**。**実機受入 18/18 PASS（Pattern 6 単体・ふ）福岡大学 テスト回線、2026-07-15、全 `テストAG001〜018` 期待一致・`PASS_全件PASS:OK` 到達）**。`certified_hashes.json` 登録済み（engine 2c7a2fc2 / spec 61e8f75e）| 2026-07-15 | `modules/ambiguity_gate/` |
| intent_classifier_v2（Evidence→Event→Rule 推論エンジン）| 決定論の複合意図判定（正規化+filler除去 → Evidence検出(否定=`_neg`属性) → Event合成(fixpoint) → Rule適用 → 競合解消(Specific>General・拮抗=CLARIFY) → 1テキスト出力。generate_by_OpenAI の用件確認等を置換する汎用エンジン。`tools/gen_intent_v2.py` で spec(JSON) を充填）| oracle **49/49 PASS**（実発話corpus regression 2回・計約3600ペアの実ログで「いいです」「希望します」「ありません」の語彙欠落を発見・修正済み）。**実機受入 27/27 PASS（Pattern 6 単体・group カレス記念病院_診療_20260716$用件分類v2受入、2026-07-17、`menu_代表spec`＝DTMF/番号発話/否定2方向/CLARIFY/REPEAT/複合文/filler除去/問い合わせ(4番)を1specで網羅）**。`certified_hashes.json` 登録済み（engine f04f6adf / spec 80ae3714）。~~追加spec `カレス記念病院_診療_用件確認`（4択メニュー・menu_代表specの部分集合） 実機受入 20/20 PASS（2026-07-17）+ oracle 20/20（engine f04f6adf / spec d9f5b945）~~ → **同日中にv2へ置換（未使用・登録記録のみ残存）**。**現行spec `カレス記念病院_診療_用件確認_v2`（4択メニュー: 予約/変更/キャンセル/その他お問い合わせ、menu_代表specの語彙・event・ruleを移植し実発話揺れへの耐性を強化） 実機受入 24/24 PASS（2026-07-17）+ oracle 24/24。`certified_hashes.json` 登録済み（engine f04f6adf / spec 2c22a71b）** | 2026-07-17（初回受入・カレス記念病院_診療 / 同日 用件確認spec追加→v2へ強化） | `modules/intent_classifier_v2/`（engine f04f6adf v2-evidence）|

> 注: field_presence / go_back_classifier は商談デモ「全STT入力ゲート(L1→L0→FAQ)」用の新規部品。field_presence 32/32 PASS（2026-06-17）。go_back_classifier P6 再cert 24/24 PASS（2026-06-18）。
> 注: triage_router は受診相談の LLM問診（generate_by_OpenAI）を決定論置換した新規部品（Phase 2・2026-07-06）。oracle 39/39＋**実機 P6 27/27 PASS（2026-07-06 認定成立）**。engine/spec ハッシュ（certified_hashes.json）は他 demo 部品（inquiry_extractor/field_presence/go_back/field_normalizer）と同様、README 認定のみで台帳未登録の運用（据置）。

## v2 spec 認定待ち（engine 登録済み・spec 実機受入待ち）

engine（部品種別）は `certified_hashes.json` の `parts` に登録済みだが、**spec（規格データ）の実機受入が未了**の部品。
（旧ここに並んでいた checkup_intent / checkup_course / checkup_menu / yes_no は厚木統合CC P6 で spec 認定済み＝上の「認定済み部品」表へ移動。`certified_hashes.json` の `specs` に登録済み。README の更新漏れを解消。ambiguity_gate も同様に 2026-07-15 実機受入 18/18 PASS で上の「認定済み部品」表へ移動済み。）

| 部品 | engine_hash[:8] | oracle | spec（認定待ち） | 正本 |
|---|---|---|---|---|

受入手順: 各 `acceptance_test/*AcceptanceTest.bivr`（生成器 `build_classifier_acceptance_bivr.py`・NFKC=v2版）を Brekeke へ import→1 コール実行→`PASS_全件PASS` 到達。
シナリオ bivr 側は `part.json.specs` に受入セット（filled_script）を配線すると `step_p6_gate` が have_set 成立で実機要求→`y` で `specs` 自動登録。

## 動作仕様確定済みの Brekeke 標準モジュール

自作部品ではないが、Pattern 6 で実機検証し動作仕様を確定したもの。

| モジュール | 検証 | 確定した仕様の例 |
|---|---|---|
| ContextMatchRouter | 19 ケース実機 PASS（2026-05-26） | 10 組目まで有効 / 部分テンプレ展開 / `==` は厳密一致 |
| null-check（drjoy^Context Logic$null-check） | 20 ケース（NC-206 のみ Module 経由制約で再現不可） | boolean false は「空ではない」/ 空配列・空オブジェクトは true |

## scaffold_generator.py 拡張（scenario_flow ブロック型 dispatch の DoD 記録）

モジュール本体ではなく `scripts/scaffold_generator.py` 側の組み立てロジック（新ブロック型の
Brekeke JSON 生成・自動配置）を対象にした DoD 記録。対象モジュール自体は上表で動作仕様確定済み。

| 拡張 | 対象ブロック型 / フラグ | オラクル | 正本の場所 |
|---|---|---|---|
| WebRTC 事前入力フォーム対応（東京都立豊島病院 診療・BLOCKER B-3、2026-07-10） | `null_check` ブロック型 / `opening.webrtc_prefill` フラグ（get-header 自動配置） | oracle **8/8**（2026-07-10） | `modules/scaffold_webrtc_dispatch/` |

## 調査ツール（本番部品ではない）

| ツール | 用途 |
|---|---|
| `modules/session_object_probe/` | setObject の保存先寿命判定（2026-06-03 実機: per-call 確定） |

## 標準構成（business_hour_classifier 準拠）

```
modules/{部品名}/
├── REQUIREMENTS.md      仕様（入出力・分岐・エッジケース）
├── README.md            概要・使い方・受入結果サマリ
├── script.js            Brekeke IVR Script 本体（正本）
├── oracle.py            Python オラクル（期待値の独立実装）
├── test_oracle.py       オラクル自体の単体テスト
├── build_bivr.py        受入テスト用 bivr 生成
├── acceptance_test/     受入テストのケース定義・実機結果
└── golden/ fixtures/    ゴールデン・フィクスチャ
```

## テスト設計の制約（実機実測済み）

- **1 コール 1000 モジュール上限**（実運用バジェット 900）→ 受入 bivr は 4 モジュール/case 設計なら **220 ケース/bivr 目安**。超える場合は part 分割
- **Module Output は常に string 化**（`$runner.setResult()` は String）: `{}`→`"[object Object]"`、`[]`→`""`、`false`→`"false"`。Object/boolean を返す分岐は session 経由でしか検証できない
- **saveContext2DB は空文字 value を拒否**（save スキップ）。空文字保存のテストは setObject 経由
- **setObject は per-call**。コールをまたぐ状態は Note（`NoteUtils.read`）等で永続化
- 受入 bivr のスキーマは import 実績のある acceptance_test 形式（next=10 スロット配列 / subs=3 スロット配列 / jumps なし）
