# 明治安田新宿健診 — OpenAI→Azure 置換 + 連結テスト

VN ハンドメイドの本番 .bivr（VoiceBot Flow Builder 非経由）に対して、
OpenAI 分岐モジュールを Azure 版へ差し替え、連結テスト（Pattern 7）まで作成した記録。

## 成果物（output/）

> **グループ名 = `明治安田新宿健診_20260616`**（インポート時に本番グループ `明治安田新宿健診`
> と衝突しないよう日付サフィックスを付与済み）。フロー名は素のまま、jump 参照も追従済み
> （規約: 日付は group_name のみ）。インポート対象は下記の `_20260616` 付き 2 本。

| ファイル | 内容 |
|---|---|
| `明治安田新宿健診_Azure_20260616.bivr` | **本体**。OpenAI モジュール 16 箇所を Azure へ置換。プロンプト/分岐/params/layout は完全保存（type 文字列のみ変更）。グループ名に日付付与 |
| `明治安田新宿健診_連結テスト_20260616.bivr` | 連結テスト用。Azure bivr の全 STT(17)＋着信分類器(2)を @General$Script スタブ化し、冒頭に DTMF ケースセレクタを前置。**Azure 16 モジュールは温存**＝推論エンジンを実機で検証できる。グループ名に日付付与・フロー名は `T_` タグ付き |
| `明治安田新宿健診_連結テスト_パターン7.csv` | **Pattern 7 ケース表（CSV）**。27 ケース。`判定(PASS/FAIL)` / `実機ログ・メモ` 列は実機実行後に人間が記入 |
| `明治安田新宿健診_連結テスト_cases.json` | 上記 CSV / 連結テスト bivr の生成元（SSoT）。inject/expect/covers |

（日付サフィックス付与前の bivr は `work/pre_date_suffix/` に退避。誤インポート防止のため output/ には日付付きのみ残す。）

## 置換の中身（中身を変えていない担保）

- 置換対象 type: `drjoy^External Integration$generate_by_OpenAI`（16 箇所）
  → `drjoy^External Integration$AzureOpenAI_Gen_Text_V1`
- OpenAI/Azure 両モジュールの params キーは完全一致（module / prompt / functionCall /
  promptTTS / contextName / contextDisplayType）。本ファイルに `addCurrentDate` は 0 箇所
  のため params 調整も不要。
- 手法は **type 文字列の生テキスト置換**（JSON round-trip なし）。各フロー差分を逆変換して
  原本とバイト一致することを検証済み＝プロンプト・分岐は一切変わっていない。

### ⚠ 要確認: Azure の type 文字列

Azure 版モジュールは社内に**まだ実フロー実体が無い**ため、type 文字列は規約からの推定です。
- 根拠: `0423仕様変更追加module.bivr` のモジュールテンプレートに `External Integration$AzureOpenAI_Gen_Text_V1`
  が定義済み。実フローでは全カスタム部品が `drjoy^` 名前空間接頭辞を持つ
  （`SKILL_JSON_rules.md` / generate_by_OpenAI もテンプレ=接頭辞なし→実フロー=`drjoy^`付き）。
  同じ規則で Azure も `drjoy^External Integration$AzureOpenAI_Gen_Text_V1` と判断。
- **Brekeke サーバに登録済みの Azure モジュール名と一致するか、インポート前に必ず照合してください。**
  異なる場合は `tools/convert_openai_to_azure.py` の `DST_TYPE` を1行直して再実行すれば済みます。

## 連結テストの回し方（人間オペレーション）

1. （前提）Brekeke に Azure モジュール（`AzureOpenAI_Gen_Text_V1`）と本テナント設定が入っていること
2. `明治安田新宿健診_連結テスト.bivr` をインポート（グループ名は本番と同一・シナリオ名に `T_` 付き＝本番非衝突）
3. 発信 → ガイダンスに従い「ケース番号 + #」を入力（CSV の ケースID = DTMF 番号）
4. CSV の各行の inject / 期待終端 / チェックポイントと実機ログ（`[STT-STUB] node=… inject=…` マーカー）を突合し PASS/FAIL を記入

### 実機実行の注意

- **営業時間チェック（acceptance_times）はスタブ化されず実時刻判定が走る**。営業時間外に回すと
  `time外切断` 等へ短絡する。営業時間内に実行するか、テナントの営業時間設定を確認のこと。
- 着信分類器（incoming-classifier）は 1 ケース以上で inject したため全コールでスタブ化。
  分類器を inject しないケースは既定で「携帯」ルート（=実機 ANI 相当）＝既存挙動と等価。
- expect は**下書き**。初回ゴールデンログ観察後に人間が確定させる前提（連結テスト標準運用）。

## 再生成手順（スクリプト）

```bash
# 1. OpenAI→Azure 置換
python3 tools/convert_openai_to_azure.py

# 2. Pattern 7 ケース表 JSON 生成
python3 tools/build_p7_cases.py

# 3. 連結テスト bivr 生成（entry=Main を先頭にした入力を渡す。tool 制約=entryにDTMFが無く
#    DTMF含むフローが先行すると先にスタブ化されセレクタ雛形を失うため）
python3 -c "...work/azure_entry_first.bivr を作る..."   # 詳細は work/ 参照
python3 ~/voicebot-flow-builder/connection_test/stub_stt_connection.py \
    --bivr work/azure_entry_first.bivr \
    --cases output/明治安田新宿健診_連結テスト_cases.json \
    --entry-flow "Main｜健診" --out output/明治安田新宿健診_連結テスト.bivr

# 4. Pattern 7 CSV 書き出し
python3 ~/voicebot-flow-builder/scripts/gen_p7_cases.py \
    --to-csv output/明治安田新宿健診_連結テスト_cases.json \
    --csv-out output/明治安田新宿健診_連結テスト_パターン7.csv

# 5. グループ名に日付サフィックス付与（インポート時の本番衝突回避）
python3 tools/add_group_date_suffix.py \
    output/明治安田新宿健診_Azure.bivr \
    output/明治安田新宿健診_Azure_20260616.bivr 明治安田新宿健診 20260616
python3 tools/add_group_date_suffix.py \
    output/明治安田新宿健診_連結テスト.bivr \
    output/明治安田新宿健診_連結テスト_20260616.bivr 明治安田新宿健診 20260616

# 6. テストセレクタの params 修正（必須）
#    stub tool はセレクタ雛形を 入力_生年月日(8桁DTMF) から複製するため、8桁検証condition
#    と終端キー'*'を継承してしまい、1〜2桁のケース番号を弾く（NO_RESULT→tc=1固定）。
#    condition=''/termdtmf='#' 等へ修正する。
python3 tools/fix_selector_params.py \
    output/明治安田新宿健診_連結テスト_20260616.bivr /tmp/_sel.bivr && \
    mv /tmp/_sel.bivr output/明治安田新宿健診_連結テスト_20260616.bivr
```

## 既知の落とし穴（連結テスト生成）

`stub_stt_connection.py` は DTMF ケースセレクタの雛形を「フロー内の既存 DTMF モジュール」から
複製する。明治安田では 入力_生年月日(8桁DTMF) が雛形になり、`condition='val.length>7&&val.length<9'`
（8桁限定）と `termdtmf='*'` を継承 → ケース番号(1〜2桁)が検証で落ち、`__保存tc` の安全弁で
tc=1 に固定される（＝ケース2以降を選べない）。`tools/fix_selector_params.py` で
`condition=''`/`termdtmf='#'` へ修正して解消（実機ログ 2026-06-16 で発覚）。

## 実機テスト結果（2026-06-16 全27ケース完了）

**26 PASS / 1 FAIL**。Azure 置換は全分類器で正常動作を実証（用件4分類・生年月日 西暦/和暦変換・
復唱はい/いいえ・リトライ復帰/枯渇・変更/キャンセルの日付・FAQ 要対応RAG実回答/対応不要・
着信種別 非通知拒否/固定受付）。唯一の FAIL=ケース12 は下記の既存フローバグ（移管起因でない）。
各ケースの判定・実機ログは `output/明治安田新宿健診_連結テスト_パターン7.csv` 参照。

## 実機テスト所見（連結テスト実行中に判明・2026-06-16）

1. **【既存フローバグ／移管起因でない】連絡先番号の別番号入力経路が不全**（ケース12で検出）
   - 経路: 携帯確認=いいえ → `連絡先番号_確認:NG` → 別番号を DTMF 入力 → `Scripts-電話番号`
   - `Scripts-電話番号`（素 Script・Azure 変換対象外）は冒頭で `r2=getModuleResult("連絡先番号_確認")`
     を**優先参照**する。直前の `連絡先番号_確認` 結果が "NG" のため `r2="NG"` を読み、DTMF 入力(r1)を
     無視 → 数字抽出ゼロ → 常に NG → リトライ枯渇 → `電話番号_判定②` へ素通り。
   - = 「登録番号が違う→別番号を入力」が実質機能しない。**OpenAI 版でも同じ**（Script 未変更・
     `連絡先番号_確認` の NG 出力はプロンプトどおりの正常動作）。回避テスト=着信分類=固定経由なら r2 が無く正常。
   - **方針（2026-06-16 浜口判断）：フローは変更せず、本所見として記録のみ。** ケース12 は FAIL（既存バグ）
     のまま据え置き。本番修正が必要なら別タスクで扱う（「中身は変えない」方針を優先）。

2. **【要確認】「現在の予約日」パーサが年を 2024 と解釈**（ケース2/3/16/17）
   - `OpenAI_現在の予約日`/`openAI_確認_現在の予約日` が「10月1日」→ `2024-10-01`。今日(2026-06-16)
     基準だと過去年。分岐は日付フォーマット一致のみ見るので通話は正常完走（テストは通る）。
     既存予約日なので過去自体はあり得るが、年の相対計算が Azure で想定どおりか本番前に確認推奨。
   - 生年月日パーサ（西暦/和暦）は正しい年を返している（年ズレは現在の予約日パーサ限定）。

3. **【無害】`入力_VALID:なし`**: 追加オプション判定が `VALID` でなく `なし` を返すが `^.*$` で吸収。

## カバレッジ（27 ケース）

- A 用件分類(Main): 健診の予約/変更/キャンセル/その他 + NO_RESULT リトライ復帰/枯渇 = 6
- B 生年月日(個人): WESTERN / JAPANESE / 復唱いいえ再聴取 / NO_RESULT = 4
- C 連絡先電話番号(個人): 携帯確認OK / NG→再入力→復唱OK = 2
- D 予約: 希望コース / 追加オプション / 希望日程 の各 NO_RESULT 復帰 = 3
- E 変更: 正常 / 現在の予約日 NO_RESULT / 非日付 / 変更内容① NO_RESULT = 4
- F キャンセル: 正常 / 現在の予約日 NO_RESULT / 理由 NO_RESULT = 3
- G FAQ: 要対応(RAG) / 対応不要 / NO_RESULT = 3
- H 着信種別: 非通知→拒否 / 固定→受付 = 2
