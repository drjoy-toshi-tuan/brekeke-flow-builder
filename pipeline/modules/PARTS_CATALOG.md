# 部品カタログ（自動生成 — 手編集しない）

> `tools/generate_parts_catalog.py` が `certified_hashes.json` + 各 `part.json` から生成。工場長・壁打ち入口が「調達可能な認定部品」を引くための index。SSoT はあくまで certified_hashes.json + part.json。

**サマリ**: 総数 23 / 認定済（調達可） 16 / oracle有・part.json無（別経路） 7

| 部品 | status | engine_ver | 出力ラベル(branch surface) | 認定規格数 | 用途 |
|---|---|---|---|---|---|
| `ambiguity_gate` | 認定済（調達可） | v1 | — | 1 | ambiguity_gate — 紛れペア（最小対）の曖昧検出器（決定論分類 多段構成 Sta… |
| `business_hour_classifier` | 認定済（調達可） | v1 | — | 1 | BusinessHour Classifier 要件定義書 |
| `checkup_course_classifier` | 認定済（調達可） | v2 | — | 1 | 健診CC コース分類器（checkup_course_classifier）— 仕様 |
| `checkup_intent_classifier` | 認定済（調達可） | v2 | — | 2 | 健診CC 用件分類器（checkup_intent_classifier）— 仕様 |
| `checkup_menu_classifier` | 認定済（調達可） | v2 | — | 6 | 健診CC メニュー選択分類器（checkup_menu_classifier）— 仕様 |
| `checkup_option_classifier` | 認定済（調達可） | v2 | — | 1 | checkup_option_classifier — 受診オプション検査 抽出・正規化 |
| `department_classifier` | 認定済（調達可） | v1 | AMBIGUOUS、OUT_OF_SCOPE、登録なし、NO_RESULT | 1 | 診療科 決定論分類器（department_classifier）— 仕様 |
| `dob_normalizer` | 認定済（調達可） | v1 | — | 1 | — |
| `faq_matcher` | 認定済（調達可） | v2 | — | 1 | FAQ Matcher 要件定義書 |
| `inquiry_classifier` | 認定済（調達可） | v1 | — | 2 | inquiry_classifier — 要件定義（用件分類・自由発話・決定論） |
| `intent_classifier_v2` | 認定済（調達可） | v2-evidence | — | 3 | intent_classifier_v2 — 要求仕様（Evidence→Event→Rule） |
| `n_choice` | 認定済（調達可） | v4 | — | 14 | n_choice — 要件定義（N択分類 決定論エンジン） |
| `phone_type` | 認定済（調達可） | v1 | — | 2 | phone_type — 仕様（入出力・分岐・エッジケース） |
| `reservation_date_classifier` | 認定済（調達可） | v2 | 不明、NO_RESULT | 1 | reservation_date_classifier — 仕様（REQUIREMENTS） |
| `text_normalizer` | 認定済（調達可） | v2 | — | 1 | text_normalizer — 要件定義（REQUIREMENTS） |
| `yes_no_classifier` | 認定済（調達可） | v4 | 肯定、否定、NO_RESULT | 3 | Yes/No 決定論分類器（yes_no_classifier）— 仕様 |
| `faq_exact_match` | oracle有・part.json無（別経路） | — | — | 0 | faq_exact_match — 要件 (REQUIREMENTS) |
| `field_normalizer` | oracle有・part.json無（別経路） | — | — | 0 | field_normalizer — 聴取値の単独フィールド正規化 |
| `field_presence` | oracle有・part.json無（別経路） | — | — | 0 | field_presence — L1 答え取得判定モジュール 要件 |
| `go_back_classifier` | oracle有・part.json無（別経路） | — | — | 0 | go_back_classifier — L0 戻る/繰り返し検知モジュール 要件 |
| `inquiry_extractor` | oracle有・part.json無（別経路） | — | — | 0 | 用件抽出 決定論パーサ（inquiry_extractor）— 仕様 v2（全決定論・Open… |
| `scaffold_webrtc_dispatch` | oracle有・part.json無（別経路） | — | — | 0 | scaffold_generator.py 拡張 — null_check ブロック型 / g… |
| `triage_router` | oracle有・part.json無（別経路） | — | — | 0 | triage_router — 受診相談 決定論トリアージ（要件定義） |
