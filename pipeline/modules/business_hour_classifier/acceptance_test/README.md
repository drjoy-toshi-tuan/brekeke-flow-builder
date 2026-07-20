# BusinessHour Classifier 受入テストシナリオフロー

Python オラクル test_oracle.py と同等の **35 ケース** を Pattern 6 形式 (チェイン式) で
**1 コール内に直列実行** する Brekeke flow。期待 jump が連続発火すれば PASS、いずれかで
不一致なら対応 FAIL 終話で停止。各ケースは TARGET_DATETIME / REFERENCE_DATE に加え
WEEKDAY_SCHEDULE / CLOSED_DATES / NATIONAL_HOLIDAY も自由に上書きできるので、施設バリエーション
(水曜午後休 / 24h 無休 / 祝日 open 設定 等) も網羅。

> **REFERENCE_DATE 固定注入**: 受入テストを実行時刻 (timeStart) に依存させないため、
> 生成スクリプトは全ケースに `REFERENCE_DATE` を固定注入する。レガシー BH-01〜25 は
> 全 target より前の `2026-01-01 00:00:00` を使い過去日ガードを発火させず、過去日ケース
> BH-26〜34 は基準日 `2026-06-04 15:00:00` を注入する (test_oracle.py の TEST_NOW と一致)。

## 同梱物

| ファイル | 役割 |
|---|---|
| `BusinessHourAcceptanceTest.bivr` | Brekeke にインポートする flow (**71 modules** = 35 ケース + 35 FAIL + 1 PASS) |
| `build_test_flow_bivr.py` | 上記 bivr の生成スクリプト (`script.js` をベースに 35 ケース分の CONFIG 上書きを注入) |
| `README.md` | このファイル |

## カバーする 35 ケース

| ID | 内容 | 期待 |
|---|---|---|
| BH-01〜05 | 平日営業中/前/後/開店境界/閉店境界 (既定スケジュール) | 営業中/営業時間外/営業時間外/営業中/営業時間外 |
| BH-06〜07 | 土曜・日曜の定休 | 定休日/定休日 |
| BH-08〜09 | 元日・こどもの日 (祝日) | 祝日/祝日 |
| BH-10〜11 | 年末12-31・年始01-02 (固定休) | 固定休/固定休 |
| BH-12 | 祝日 open 設定 (ER対応病院想定) | 営業中 |
| BH-13〜14 | 水曜午後休クリニック (午前/午後) | 営業中/営業時間外 |
| BH-15 | 24h 無休病院 | 営業中 |
| BH-16〜17 | 不正 target / 不正 schedule | ERROR/ERROR |
| BH-17b | 未指定曜日は定休扱い | 定休日 |
| BH-18 | 振替休日 (5/6) | 祝日 |
| BH-19 | 水曜全休クリニック | 定休日 |
| BH-20 | 土曜午前のみ営業 | 営業中 |
| BH-21〜25 | DATE 型 context / yyyy-MM-dd リテラル (時刻 00:00 = date-only 入力) | 営業中/定休日/祝日/固定休/営業中 |
| BH-26〜27 | 過去日 (昨日) 平日営業内 / date-only — 過去日ガード | 営業時間外/営業時間外 |
| BH-28〜29 | 当日 (今日) の過ぎた朝枠 / date-only — 日付単位なので過去扱いしない | 営業中/営業中 |
| BH-30〜31 | 翌日 (平日営業内) / 明後日 (土曜) — 未来は通常判定 | 営業中/定休日 |
| BH-32〜33 | 過去日は固定休 (1/2) / 祝日 (5/5) より優先 | 営業時間外/営業時間外 |
| BH-34 | 過去年の祝日 (Note 未登録) — 過去ガードが Note 抜けを救う | 営業時間外 |

## フロー構造

> 注: 以下はチェイン方式の**模式図** (旧 T1〜T8 表記)。実際の case ID / 日付は上記
> 「カバーする 35 ケース」表 (BH-01〜34) を参照。チェインの仕組み自体は同じ。

```
[テストBH-T1_平日営業中]  TARGET_DATETIME="2026-05-29 12:00:00"
   │ ^営業中$ ─────────────────────→ 次へ
   │ ^.*$    ─────→ [FAIL_BH-T1_期待:営業中]
   ▼
[テストBH-T2_平日営業時間外]  TARGET_DATETIME="2026-05-29 20:00:00"
   │ ^営業時間外$ ─────────────────→ 次へ
   │ ^.*$        ──→ [FAIL_BH-T2_期待:営業時間外]
   ▼
[テストBH-T3_土曜定休]         TARGET_DATETIME="2026-05-30 10:00:00"  → ^定休日$
   ▼
[テストBH-T4_祝日]            TARGET_DATETIME="2026-05-05 10:00:00"  → ^祝日$
   ▼
[テストBH-T5_固定休]          TARGET_DATETIME="2026-12-31 10:00:00"  → ^固定休$
   ▼
[テストBH-T6_不正入力]         TARGET_DATETIME="2026/05/29 12:00"     → ^ERROR$
   ▼
[テストBH-T7_営業開始境界]     TARGET_DATETIME="2026-05-29 09:00:00"  → ^営業中$
   ▼
[テストBH-T8_営業終了境界]     TARGET_DATETIME="2026-05-29 18:00:00"  → ^営業時間外$
   ▼
[PASS_全件PASS]   ← ここに到達したら受入確定
```

## 実行手順

### 前提

- 本番デプロイで使う `script.js` の **CONFIG ブロック既定値** を変更していないこと (テストケースの期待値は既定値前提)。変更している場合は `build_test_flow_bivr.py` を再実行して bivr を作り直す
- Brekeke の **テナント `drjoy` 配下に Note `drjoy.holidays`** が存在し、本番運用と同じ祝日リストが入っていること (BH-08/09/18/23 の祝日判定で参照)。**2026 年分** (BH-08/09/18) と **2027 年分** (BH-23) の両方が必要
- 過去日ケース (BH-26〜34) は `REFERENCE_DATE` を固定注入しているため、実行時刻に関係なく決定論で判定される (Note の祝日抜けに依存しない)

### Brekeke 投入

1. `BusinessHourAcceptanceTest.bivr` を Brekeke 管理画面で flow としてインポート (テナント drjoy 配下)
2. テスト発信用の番号 or 「フロー実行」機能で **1 コールだけ** 実行
3. Brekeke ログ画面で結果を観察

### ログから結果判定

各テストケースの実行時に下記が記録される:

```
[BH-T1] expected=営業中 target=2026-05-29 12:00:00 label=テストBH-T1
[BusinessHour] params target=2026-05-29 12:00:00 ...
[BusinessHour] resolved 2026-05-29 12:00 dow=fri
[BusinessHour] => 営業中 (09:00-18:00)
Module.exec() name=テストBH-T2_平日営業時間外    ← 次テストへ
```

**全件 PASS の判定**:
```
Module.exec() name=PASS_全件PASS
```
↑ このログ行が出れば 8 ケース全パス。

**いずれかで FAIL の判定**:
```
Module.exec() name=FAIL_BH-T3_期待:定休日
```
↑ ここで停止。直前の `[BH-T3] expected=... [BusinessHour] =>...` ログを見れば不一致内容が分かる。

### grep 推奨コマンド

```
# テスト進捗を順番に観察
grep -E '\[BH-T[0-9]+\]|\[BusinessHour\] =>|Module\.exec\(\) name=(テストBH|FAIL|PASS)' brekeke.log
```

## 期待される全件 PASS 時のログ概略 (旧 8 ケース模式・参考)

> 注: 下表も旧 T1〜T8 の参考。現行は BH-01〜34 が同じ要領で直列実行され、最後に `PASS_全件PASS` 到達で受入確定。

| ケース | [BH-Tn] expected | [BusinessHour] => | 次に Module.exec する name |
|---|---|---|---|
| T1 | 営業中 | 営業中 | テストBH-T2_平日営業時間外 |
| T2 | 営業時間外 | 営業時間外 | テストBH-T3_土曜定休 |
| T3 | 定休日 | 定休日 | テストBH-T4_祝日 |
| T4 | 祝日 | 祝日 | テストBH-T5_固定休 |
| T5 | 固定休 | 固定休 | テストBH-T6_不正入力 |
| T6 | ERROR | ERROR | テストBH-T7_営業開始境界 |
| T7 | 営業中 | 営業中 | テストBH-T8_営業終了境界 |
| T8 | 営業時間外 | 営業時間外 | **PASS_全件PASS** |

## FAIL 時の対応

FAIL_BH-Tn 終話のいずれかで停止 = REQUIREMENTS.md §11 のケース n に回帰あり。原因切り分けの観点:

| Fail ケース | 主な疑い |
|---|---|
| **T1 (営業中) / T7 (境界 09:00)** | WEEKDAY_SCHEDULE が編集されてる、または時刻 parse 異常 |
| **T2 (営業時間外) / T8 (境界 18:00)** | 営業終了の境界が排他扱いになっていない (close 包含してる) |
| **T3 (土曜定休)** | sat=closed が外れてる |
| **T4 (祝日)** | Brekeke Note `drjoy.holidays` が空 / 不在 / 2026-05-05 が含まれてない |
| **T5 (固定休)** | CLOSED_DATES から 12-31 が外れてる |
| **T6 (ERROR)** | parse エラー扱いが甘い (slash 区切りを許容してしまっている) |

## 既知の制約

- このフローは `script.js` の既定値での回帰確認用。施設個別の WEEKDAY_SCHEDULE や CLOSED_DATES を変更した場合は、本テストフローを再生成 (build_test_flow_bivr.py を再実行) して施設固有値に追従させる必要あり
- Brekeke 1 コール 1000 モジュール上限 ([[feedback_brekeke_max_module_execution_1000]]) 内 (本 flow は 71 modules = 35 ケース + 35 FAIL + 1 PASS)
- 本 flow の 35 ケースは Python オラクル ([[project_business_hour_classifier]] の test_oracle.py) と 1:1 対応。algorithm の境界網羅・過去日ガードはオラクル側 35/35 で担保済み

## bivr 再ビルド (script.js 修正時)

```bash
cd voicebot-flow-builder/modules/business_hour_classifier/acceptance_test
python build_test_flow_bivr.py
# → BusinessHourAcceptanceTest.bivr が更新される
```
