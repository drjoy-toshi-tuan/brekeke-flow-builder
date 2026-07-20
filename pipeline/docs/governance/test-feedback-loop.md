# テスト所見フィードバックループ — 台帳と運用

P7（連結・実機）/ P6（単体・実機）/ oracle で見つかった不具合を **VoiceBot Flow Builder 本体へ
フィードバックして恒久化する**ためのルーティング規約と台帳（2026-06-10 厚木統合CC で運用開始）。

> 思想: ループの価値はシナリオを直すことではなく「**同じクラスのバグが二度と黙って通らなくなること**」。
> 所見は「どの層が防ぐべきだったか」で分類し、上流の防御（ルール/回帰テスト）が入った時点で close する。

## ルーティング 5 レーン

| レーン | 対象 | 行き先 | close 条件 |
|---|---|---|---|
| **A 部品** | 発話揺れの誤分類（責任境界の不足） | `modules/<部品>/acceptance_test/cases.tsv` 追補 → 再受入（ハッシュ更新） | oracle + P6 実機 再PASS、認定レジストリ更新 |
| **B シナリオ** | 当該施設固有の設計ミス | 設計書 YAML 修正 → Pattern 2 / `--resume` | 当該シナリオ P7 再PASS |
| **C 生成器** | scaffold / gen_properties / orchestrator 等のバグ | `scripts/` 修正 ＋ **再発検知テスト** | 修正＋回帰テストが master に入る |
| **D ルール昇格** | 一般化可能な構造欠陥 | qa_validator（設計時）/ validator.py（JSON 時）へ E/T ルール新設 | 新ルールが CRITICAL/WARNING として稼働 |
| **E ハーネス** | P7/P6 テスト機構自体のバグ | `gen_p7_cases.py` / `stub_stt_connection.py` 修正 | ハーネス修正＋ケース表再生成で再PASS |

### 運用

- 所見の発生源: p7_acceptance / p6_gate で FAIL・違和感が出たら、この台帳に 1 行起票してから直す
  （30 分以上の調査になりそうなら `/incident-register` で RCA プロセスへ）。
- 起票者は「どのレーンか」を仮置きでよい。レーン C は**回帰テストなしで close しない**。
- 週次 optimizer / 監査がこの台帳の OPEN を巡回する。

## 台帳

| ID | 発見日 | 発見手段 | 事象 | レーン | 状態 | 対応 |
|---|---|---|---|---|---|---|
| FB-1 | 2026-06-08 | P7（福岡大学病院） | 用件_分岐(CMR) catch-all 欠落 → classification 空でデッドエンド（AUD-1） | **D** | OPEN | qa_validator に「CMR 全分岐に catch-all or NO_RESULT 経路必須」E ルール新設を提案。担当者調整中（connection_test/README 参照） |
| FB-2 | 2026-06-10 | P7 実機（厚木 tc=1） | gen_p7_cases がメインフロー hearing の defaults を生成せず、注入なしノードが NO_RESULT フォールバック → リトライ枯渇 | **E** | **CLOSED**（387cc0c） | defaults を設計書から自動導出（enum=先頭ラベル/datetime/自由発話）。CMR 終端予測も other 優先化 |
| FB-3 | 2026-06-10 | パイプライン実行観察 | リポジトリ直下に `-o` ファイル（フロー JSON ダンプ）が生成される。どこかの step が出力先引数を取りこぼしている | **C** | OPEN | 発生 step の特定から。close には「リポ直下への意図しないファイル生成を検知する後処理チェック」もセットで |
| FB-4 | 2026-06-10 | パイプライン実行観察 | gen_properties が `{施設}_{日付}_{flow}` を施設名として解釈し `output/scenarios/` に重複ディレクトリを生成 | **C** | OPEN | add_date 後の施設名と gen_properties の出力先解決の不整合。修正＋出力先の単体テスト |
| FB-5 | 2026-06-10 | 実機レビュー（浜口） | scaffold の既定が generate_by_OpenAI 一色で、DTMF 指定質問でも STT 直接分岐/Script を生成しない | **C/D** | OPEN | deterministic-replacement-roadmap step 5（scaffold builder 切替）。認定部品を scaffold が直接 emit できるようにする。厚木は bivr_patches で暫定対応済み |
| FB-6 | 2026-06-10 | 実機レビュー（浜口） | 連結テストのログに他テナントのコールが混在し判定しづらい | **E** | OPEN | 採点を callId でフィルタする log 突合スクリプト（P7 自動採点）の整備。stub の `[STT-STUB]` marker + checkpoint context を機械突合する形が本命 |
| FB-7 | 2026-06-10 | （仮説）P7 サブフロー復帰停止 | 当初「スタブ置換で空ターゲット復帰エッジが復帰しない」と推測 | E | **WONTFIX（誤診）** | 生ログで反証: `入力_患者_氏名` スタブ実行直後に `Module.exec name=生年月日聴取` へ正常復帰していた。空エッジ復帰は機能する。真因は FB-8 |
| FB-8 | 2026-06-10 | P7 実機（厚木、生ログ） | `生年月日聴取` Jump で `FlowException: Flow not found: drjoy^…$連結テスト_生年月日聴取` → dropCall。真因＝**bivr zip エントリ名（URLエンコード後）の 255B 上限超過**。日本語1字=9B、`連結テスト_`(46B)を長いグループ名に積み `連結テスト_生年月日聴取`=257B で 2B 超過しインポート時に取りこぼし（`氏名聴取`=239B は収まる非対称が証拠）。bivr 内部は整合 | **E** | **CLOSED（2026-06-10）** | stub_stt_connection.py を改修: ①テストタグを短縮（既定 `連結テスト_`→`T_`、`--tag` 可変）②**ファイル名 255B から逆算してサブフロー名を先頭優先で自動短縮**（内容ヒント保持・衝突は連番）③グループ自体が予算超なら fail-fast 明示 ④rename を blunt string-replace から旧→新フロー名マップに置換し jump 整合 ⑤検証に「fn_bytes≤255／全 jump 解決」追加。**別グループ案は却下**＝Brekeke 投入が目視手作業のため別グループ大量フローは確認ロングランで破綻（本番と同一グループ同居が必須） |
| FB-9 | 2026-06-15 | P7 実機（厚木 subflow形） | SUBFLOW defaults の汎用語「患者」shadow で 生年月日/携帯枠に氏名が注入された | **E** | **CLOSED** | gen_p7_cases の defaults 照合を専用キー優先化（汎用語より長いキーを先に当てる）。memory [[project_atsugi_integrated_cc]] 記録 |
| FB-10 | 2026-06-16 | P7 実機（厚木 subflow形） | **本番実バグ**: 終話分岐_電話種別 CMR 照合値="1" だが電話番号サブフロー返り値は "携帯" → 携帯発信が固定終話に倒れ SMS 不達 | **B**＋**D** | B=**CLOSED**（YAML/patch 修正）／D=OPEN | B: 照合値を返り値に整合。D: qa_validator に「CMR 照合値と上流モジュール返り値の型整合」ルール化を提案（OPEN） |
| FB-11 | 2026-06-17 | P7 実機（厚木 1flow case1） | フラット slot 内部の DOB 復唱確認ノード（入力_生年月日聴取_確認=はい/いいえ）に既定注入が汎用語「生年月日」shadow で `19800101` → yes_no NO_RESULT → リトライ枯渇で聴取失敗終話 | **E** | **CLOSED（76ef104）** | gen_p7_cases.build_defaults に type:slot 内部ノード専用既定（生年月日聴取_確認/電話番号聴取_*確認=はい・連絡先=番号）を追加し _order 先頭側へ。FB-9 の slot 版 |
| FB-12 | 2026-06-17 | P7 実機（厚木 1flow case1） | フラット phone slot 携帯路の phone_type が incoming-classifier の種別ラベル（"携帯"）を入力に取り誤判定（数字なし→その他→固定終話）。真因＝**着信元 ANI と連絡先電話番号が別になりうる前提が欠落**（proto で phone slot を推測簡略実装していた） | **B**（設計）＋**C**（生成器） | **CLOSED（7e4ad03）** | `_build_slot(phone)` を元 電話番号聴取 サブフローに忠実複元（携帯=ANI採用→「今おかけの番号でよいか」確認→はい:phonetype=携帯/いいえ:連絡先聴取、固定/別番号=聴取→正規化→確認→phone_type(番号)）。新ヘルパ build_phone_normalization、build_reconfirmation に prompt/読み上げ引数。OpenAI 復唱判定→認定 yes_no_classifier |
| FB-13 | 2026-06-17 | P7 実機（厚木 1flow case1） | フラット phone slot で携帯回線が ANI 確認路でなく連絡先聴取路へ誤遷移。真因＝**incoming-classifier は next を regex ラベルでなく固定スロット位置で振り分ける**ため、携帯を先頭スロットに置いたことで「携帯」結果が3番目スロット（海外の遷移先）へ流れていた | **C** | **CLOSED（914d139）** | incoming-classifier の next を build_incoming_classifier と同一順序（非通知/固定/海外/携帯/WebRTC/その他・catch-all `^*$`）へ修正。知見を memory [[reference_incoming_classifier_ani_override]] に追記（再利用ガード） |
| FB-14 | 2026-06-17 | P7 実機（厚木 1flow case1） | フラット phone slot で ANI 正規化後に切断（復唱_ANI 未到達）。真因＝**custom モジュール（Phone Normalization）の TIMEOUT/ERROR/NO_RESULT/INVALID は `^.*$` では拾われずデッドエンド→切断**。build_phone_normalization が ^.*$ 1分岐のみだった | **C** | **CLOSED（90232cc）** | build_phone_normalization が全5分岐（TIMEOUT/ERROR/NO_RESULT/INVALID/^.*$）を明示。retry_next 省略時（ANI路）は全分岐を success(復唱)へ＝元 電話番号正規化 の挙動踏襲 |

## 関連

- 連結テストの機構・台帳: `connection_test/README.md` / `REQUIREMENTS.md`
- 完成品ゲートの定義: `CLAUDE.md`（パイプライン全体像）
- 部品の認定: `modules/README.md` + `modules/certified_hashes.json`
- 置換ロードマップ: `docs/governance/deterministic-replacement-roadmap.md`
