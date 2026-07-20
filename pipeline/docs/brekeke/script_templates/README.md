# Script Templates

scaffold_generator が `params.script` に埋め込む JavaScript テンプレート。
設計書の `script` ブロックに `script_template` を指定すると、対応するテンプレートが読み込まれてプレースホルダーが置換される。

## 利用可能なテンプレート

| テンプレート | 用途 | プレースホルダー | 出力値 |
|---|---|---|---|
| `future_date` | 入力日付が今日より未来か判定 | `{{INPUT_MODULE}}` | SUCCESS / FAIL |
| `phone_type` | 電話番号を携帯/固定/その他に分類 | `{{INPUT_MODULE}}` | 携帯 / 固定 / その他 |
| `day_of_week` | 現在の曜日判定 | （なし） | 平日 / 土曜 / 日曜祝日 |
| `business_hours` | 営業時間内か判定 (単純時刻範囲のみ、レガシー) | `{{START_HOUR}}` / `{{END_HOUR}}` | 営業時間内 / 営業時間外 |
| `business_hour_classifier` | **曜日別営業時間 + 固定休 + 祝日 (Brekeke Note 連携) + 過去日ガード 統合判定**（過去日は一律 営業時間外。基準日 REFERENCE_DATE は本番 "now" 固定）。詳細は [REQUIREMENTS.md](../../../modules/business_hour_classifier/REQUIREMENTS.md) | `{{WEEKDAY_SCHEDULE}}` / `{{CLOSED_DATES}}` / `{{NATIONAL_HOLIDAY}}` / `{{HOLIDAY_NOTE_NAME}}` / `{{TARGET_DATETIME}}` | 営業中 / 営業時間外 / 定休日 / 祝日 / 固定休 / ERROR |
| `current_appointment_date` | DTMF 4 桁 + 自由発話 (M月D日 / 相対日付 / 和暦 / ノイズ / わからない) を `yyyy-MM-dd` に正規化、context 保存 | （直書き、INPUT_MODULE は内部固定）| `result` (表示) / `dbValue` (DATE 型 context) |
| `condition_group` | 多段分岐のグループ分類 | `{{INPUT_MODULE}}` / `{{MAPPING}}` / `{{DEFAULT_GROUP}}` | グループ番号 ("1"〜"10") |
| `shinjuku_kenshin_date_gate` | **施設専用**: 新宿健診プラザ_健診 受診希望日の 3 ゲート判定（年度末超過→休館日→最短日） | `{{INPUT_MODULE}}` | 年度末エラー / 休館日エラー / 最短日エラー / OK |
| `inquiry_extractor` | **商談デモ フリー発話受付**: 自由発話 STT を直接解析し用件種別（新規/変更/キャンセル/問い合わせ）＋各スロット（診療科/予約日/氏名/連絡先/生年月日/診察券番号）＋用件概要文へ分解。OpenAI不使用・ベストエフォート抽出。詳細は [REQUIREMENTS.md](../../../modules/inquiry_extractor/REQUIREMENTS.md) | `{{INPUT_MODULE}}` / `{{CONTEXT_FIELD}}` | canonical `<用件種別>‖<slot>@<flag>‖…‖SUMMARY:<用件概要>`（＋context へ setObject 撒き出し）|
| `faq_matcher` | **横断FAQ（在slot質問検知）**: 直前 STT を Brekeke Note の FAQ 仮想DBに照合（NFKC+2-gram+BM25+coverage+idf-margin）。OpenAI不使用の決定論RAG。engine は認定済 `modules/faq_matcher/script.js` と verbatim 同期（config 2行のみ placeholder 化）| `{{INPUT_MODULE}}`（直前STTモジュール）/ `{{FAQ_NOTE}}`（FAQ Note名）| `<答え本文>` / `^NOT_FOUND$` / `^ERROR$`（横断: NOT_FOUND=スロット回答として次へ・答え=回答#data#後に同聴取へ復帰）|
| `drjoy_finalize` | **終端 正規化＋Dr.JOY再保存＋ダンプ**: 終話直前に置き、各フィールドを `getSystemVariableValue($runner=抽出値)優先・空ならgetModuleResult(STT=聴取値)` で読み、kind 別に正規化して **save2db＋$runner へ上書き**（聴取の生STTを抽出経路と同品質に揃える）→ トレースに1行出力（`[DRJOY-FINALIZE]`＋setResult）。フォーム=contextName upsert なので終端クリーン値が画面に残る。冪等（空なら raw 維持）。正規化は `modules/field_normalizer/`（oracle 33/33）と parity | `{{DUMP_MAP_JSON}}`（`[[label,contextName,sttModule,kind,displayType],...]`・kind=name/phone/card/birthday/department/date/raw）| `label=value \| …`（トレース表示用）|
| `yes_no_classifier` | **純ポーラ二択（はい・いいえ系）の決定論判定**。完全一致＋マーカー走査（否定優先）。普遍語彙ゆえ施設別 spec 不要・engine/spec 認定済（`79c580f1` / `5a9c53d8`）で `modules/yes_no_classifier/script.js` とバイト等価。詳細は [REQUIREMENTS.md](../../../modules/yes_no_classifier/REQUIREMENTS.md) | `{{INPUT_MODULE}}` | 肯定 / 否定 / NO_RESULT |
| `reservation_date_classifier` | **予約日/希望日の決定論正規化（期間制限なし版）**。STT/DTMF（M月D日・相対日付・曜日・和暦・8桁DTMF）を `yyyy-MM-dd 00:00` に正規化し context=reservationDate(+派生 _yMda/_Mda/_yMd/_Md) 保存。施設非依存（spec 無し・SOURCE_MODULE のみ wiring）・engine v1・JST 固定内蔵・oracle 48/48。**認定正本 `modules/reservation_date_classifier/script.js` を読む**（穴あきコピー不要＝正本一本化）。cert ゲート対象、`certified_hashes` 登録は P6 実機 PASS 後。詳細は [REQUIREMENTS.md](../../../modules/reservation_date_classifier/REQUIREMENTS.md) | `{{INPUT_MODULE}}` | `yyyy-MM-dd 00:00`（値・catch-all）/ 不明 / NO_RESULT |

| `closed_period` | **毎年繰り返す休業期間**（GW・年末年始・夏季休診）に入電日が該当するか判定。年跨ぎ可・複数期間可。旧 custom（GW判定 / 年末年始判定 / 休診期間判定）の置き換え先 | `{{PERIODS}}`（例 `"04-29..05-06,12-29..01-03"`）/ `{{TARGET_DATETIME}}`（P6 用固定日。本番未指定 = now） | 期間内 / 期間外 / ERROR |
| `same_day_check` | context の日付が**今日から N 日以内**か判定（当日・直前の変更/キャンセルをスタッフ対応へ振り分け）。過去日・解釈不能は安全側（期限内/判定不能）へ。旧 custom（当日予約判定 / 当日翌日判定 / 予約日判定_変更・キャンセル）の置き換え先 | `{{CONTEXT_FIELD}}` / `{{DAYS_AHEAD}}`（0=当日のみ。未指定 0）/ `{{TARGET_DATETIME}}` | 期限内 / 期限外 / 判定不能 |
| `date_range_check` | context の日付が**絶対日付の受付範囲**（START..END 両端含む）内か判定。旧 custom（受診希望日N_範囲チェック / 変更希望日N_範囲チェック）の置き換え先。年度替わりは template_params を更新して再ビルド | `{{CONTEXT_FIELD}}` / `{{START_DATE}}` / `{{END_DATE}}`（YYYY-MM-DD） | 範囲内 / 範囲外 / 判定不能 / ERROR |
| `set_context` | **固定値を context に保存**して次へ進む（無音の分類保存）。TTS 不要な場合の announcement `save_to`/`save_value` 代替。旧 custom（予約_新規/再診_分類保存）の置き換え先 | `{{CONTEXT_NAME}}` / `{{FIXED_VALUE}}` / `{{DISPLAY_TYPE}}`（未指定 TEXT） | SUCCESS |

> **二択の使い分け**: `yes_no_classifier` は polar 回答（はい/いいえ・あり/なし・希望/希望しない・本人/代理…の「はい/いいえで答えられる」問い）専用で出力は固定の 肯定/否定。**本人/家族・個人/企業・検査/診察 のように「中身の語彙が選択肢ごとに可変」な二択は `n_choice`**（施設別 spec を著作）。

> **日付系 4 テンプレートのオラクル**: `closed_period` / `same_day_check` / `date_range_check` の判定ロジックは `tests/test_new_date_templates.py`（Python 写像・33 ケース）で機械検証できる。実機挙動の確認（P6 受入）は従来どおり人間が行うこと。`{{TARGET_DATETIME}}` に固定日を渡せば期間内/期限内ケースを実機で再現できる。

## 設計書での記述例

### future_date (シンプル)

```yaml
- step: 営業日判定
  type: script
  script_template: future_date
  reference_module: "OpenAI_変更希望日"  # {{INPUT_MODULE}} に置換
  conditions:
    - match: "SUCCESS"
      next: 予約確定
    - match: "FAIL"
      next: 営業日エラー案内
```

### business_hour_classifier (6 分岐の統合判定)

```yaml
- step: 営業判定
  type: script
  script_template: business_hour_classifier
  template_params:
    WEEKDAY_SCHEDULE: "mon=09:00-18:00,tue=09:00-18:00,wed=09:00-18:00,thu=09:00-18:00,fri=09:00-18:00,sat=closed,sun=closed"
    CLOSED_DATES: "12-29,12-30,12-31,01-02,01-03"
    NATIONAL_HOLIDAY: "closed"
    HOLIDAY_NOTE_NAME: "drjoy.holidays"
    TARGET_DATETIME: "now"             # or "<%currentAppointmentDate%>" 等
  conditions:
    - match: "営業中"      ; next: 通常受付
    - match: "営業時間外"  ; next: 時間外案内
    - match: "定休日"      ; next: 休診案内
    - match: "祝日"        ; next: 祝日休案内
    - match: "固定休"      ; next: 年末年始案内
    - match: "ERROR"       ; next: 安全側fallback
```

**前提**: Brekeke 管理画面のテナント `drjoy` 配下に Note `holidays` を作成し、内閣府公式 CSV から年次更新した祝日リストを保存しておくこと。詳細は [REQUIREMENTS.md §7](../../../modules/business_hour_classifier/REQUIREMENTS.md)

### yes_no_classifier (純ポーラ二択)

`reference_module` は直前の STT/DTMF 入力モジュールを指す（`{{INPUT_MODULE}}` に充填）。出力は固定で 肯定/否定/NO_RESULT。設計書の分岐ラベルは 肯定/否定 で書き、NO_RESULT は聴取リトライへ。

```yaml
- step: 明日以降確認
  type: script
  script_template: yes_no_classifier
  reference_module: "聴取_明日以降確認"   # 直前の STT 入力モジュール → {{INPUT_MODULE}}
  conditions:
    - match: "肯定"       ; next: エリア選択
    - match: "否定"       ; next: 遅刻種別確認
    - match: "NO_RESULT"  ; next: リトライ_明日以降確認
```

> あり/なし・希望/希望しない 等の業務ラベルで設計したい場合も、polar 回答である限り判定は本テンプレで可能。分岐ラベルを 肯定/否定 に寄せる（surfacing が `part.json output_labels` と照合するため）。業務ラベルのまま出力したい昇華（POSITIVE/NEGATIVE_LABEL 化）は engine 変更＝再 P6 を伴うため別判断。

## 診療科分類（department）の 2 方式

診療科分類は 2 つの実装がある。**新規は B（Custom Module）推奨**。

| | A: `department_classifier.js`（@General$Script） | B: `clinical_department_classifier`（Custom Module・**推奨**）|
|---|---|---|
| 形 | script_template（穴あき・本ディレクトリ） | `type: clinical_department_classifier` ブロック（`drjoy^TS Custom Module$Clinical Department Classifier`）|
| 同義語/読み | `{{DEPARTMENTS}}` spec に施設別に著作 | **モジュール内蔵**（施設は正準科名を選ぶだけ）|
| 施設別設定 | DEPARTMENTS spec（@spec・hash 対象）| `clinical_department_N`/`result_name_N` **プロパティ**（hash 対象外）|
| 認定 | engine v2 + **施設ごとに spec 再 P6** | **engine 1 回のみ**・施設別 P6 不要 |
| 使い分け | マスター辞書に無い特殊科を持つ施設の fallback | 通常はこちら。最大 10 グループ |

B の設計記法（`build_clinical_department_classifier`）— 診療科を最大 10 グループに束ね、`departments`（";" 区切り正準科名・省略時は `match` を単一科）→ `match`（出力名）：

```yaml
- step: 診療科聴取        # 先に STT で聴取（output_format: text）
  type: hearing
  output_format: text
  save_to: ""
- step: 診療科分類
  type: clinical_department_classifier
  reference_module: "入力_診療科聴取"   # → params.module（直前の入力）
  save_to: clinicalDepartment           # 指定で saveDepartment2DB: Yes
  conditions:
    - match: "内科系"   ; departments: "循環器内科;消化器内科;呼吸器内科" ; next: 予約_内科
    - match: "整形外科" ; departments: "整形外科"                       ; next: 予約_整形
    - match: "対象外"   ; next: 対象外案内      # 辞書外 → ^NOT_COVERED$
    - match: "NO_RESULT"; next: リトライ_診療科  # TIMEOUT/ERROR も同様に任意指定
```

> 正準科名のマスター語彙は `department_classifier.js`（A）の DEPARTMENTS／Downloads の診療科辞書（標榜科マスター ~30 科）と同一。施設の科がマスターに無い場合は Custom Module 内蔵辞書の拡張（中央で再デプロイ）か A 方式の fallback を検討。engine/施設 spec の認定（certified_hashes）は Brekeke 実機 P6 後。

## カスタムスクリプト

`script_template` を指定しない or `script_template: custom` の場合、scaffold_generator は `params.script` に `// TODO_script: ここにスクリプトを記述してください` のマーカーを残す。
人間 or fixer が後段で記述する。

## テンプレート追加方法

1. このディレクトリに `{name}.js` を作成
2. プレースホルダーは `{{NAME}}` 形式で記述
3. README の表に追加
