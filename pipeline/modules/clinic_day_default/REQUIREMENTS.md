# clinic_day_default — 要件定義

## 目的

ユーザー発話（STT）を必要とせず、**今日の日付 + 診療日カレンダー**から
「N診療日後」の日付を機械的に計算し、`available_date_full` / `available_date_short`
をセッション変数として設定する。冒頭アナウンス直後など、聴取前の任意の位置に
配置してTTS文言の日付プレースホルダー（例:「〇月〇日以降の受診」）を
実データに置き換えるために使う。

元実装: 配布版 Clinic Day Classifier 最新（lazy CSV load / PAST_DAY / STT聞き間違い補正 /
stripFillers / `<%today%>` センチネル対応版・2026-07-17 取り込み）。
SRS: `modules/brekeke-custom-modules/modules/clinic-day-classifier/SRS_Clinic_Day_Classifier.md`
（休診日判定・blockDaysリードタイム計算の詳細仕様はそちらが正・ただし旧版準拠のため
lazy load / PAST_DAY 等は本 fork の script.js コメントを参照）。

fork 追加分:
- `noInputMode` プロパティ（`"yes"` で入力パース全スキップ・available_date 算出のみ。
  scaffold の `type: clinic_day_default` ブロックは常に `noInputMode: yes` で配線する）
- noInputMode / `<%today%>` センチネル時に contextName 設定なら受付可能初日を DB 保存
- setResult は算出成功で `OK`、失敗で `NO_RESULT`（wiring は `^.*$` → next の無条件遷移）

## 入出力仕様

### 入力（設計書 YAML block properties）

| フィールド | 必須 | 既定値 | 説明 |
|---|:---:|---|---|
| `block_days` | ⚪ | `0` | 受付開始までの診療日数（0=当日、1=翌診療日、2=翌々診療日、3=3診療日後…） |
| `closed_day_mode` | ⚪ | `土日祝日` | 休診日区分: `土日祝日`/`祝日`/`土日`/`日祝日`/`土`/`日`/`なし` |
| `holiday_source` | ⚪ | *(空)* | 祝日CSV URL（内閣府形式）。未設定なら祝日判定スキップ |
| `custom_holiday` | ⚪ | *(空)* | 独自休診日CSV URL |
| `save_to` | ⚪ | `availableDateFull` | `available_date_full` を保存する context 名 |

### 出力（setObject・毎回計算・STT不要）

| 変数 | 内容 |
|---|---|
| `available_date_full` | 受付可能な最初の診療日（例: "2026年7月20日"） |
| `available_date_short` | 同・短縮形（例: "7月20日"） |
| `<save_to>` | `available_date_full` と同値（DB保存・TTS `<%save_to%>` 参照用） |

## 分岐

分岐なし。単一の `next` のみ（聴取モジュールではないため choice/条件分岐を持たない）。

## エッジケース

- `block_days=0` かつ今日が休診日 → 次の診療日を返す
- 祝日CSV/独自休診日CSVの取得失敗 → その CSV をスキップして続行（他方は考慮）
- カレンダーが366日以内に診療日を見つけられない場合 → `available_date_full` は空
  （呼び元 TTS は `<%available_date_full%>` が空になるため、この異常系は別途検討要）

## 未完了（Definition of Done 未達）

> ⚠️ 本部品は **P6 実機受入・oracle テスト未整備**。`docs/governance/deterministic-replacement-roadmap.md`
> の Definition of Done（REQUIREMENTS.md 詳細化・oracle.py + test_oracle.py・P6実機受入・
> modules/README.md 認定登録）を完了するまで、本番シナリオへの組み込みは
> oracle_gate が未認定部品としてブロックする（scaffold 生成は可能・P6ゲートで停止）。

- [ ] oracle.py（Python 独立再実装）+ test_oracle.py
- [ ] P6 実機受入テストケース（block_days 0/1/2/3 × closed_day_mode 各種の組み合わせ）
- [ ] modules/README.md 認定登録
- [ ] 別件: script.js 内のハードコード private_key を環境変数/シークレット管理へ切り出し
