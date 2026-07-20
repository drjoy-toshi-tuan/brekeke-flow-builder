# Context Read API Probe

saveContext2DB で保存した session context (例: `currentAppointmentDate=2027-01-01 00:00:00`)
を Brekeke Nashorn script 内から **読み取る API を empirical 特定** するための probe。

`<%currentAppointmentDate%>` 形式の Brekeke 変数置換は **script 本文には適用されない** こと
が 2026-05-29 の実機テストで判明したため、Java/JS API での読み取りに切り替える。

## 前提

このフローが既に動作していること:
- DTMF or 発話 → date_current script で正規化 → `saveContext2DB` で `currentAppointmentDate` を DATE 型保存
- 直近の実機ログで `currentAppointmentDate=2027-01-01 00:00:00` がセーブされたことを確認

## 使い方

1. Brekeke で BusinessHour Classifier の **直前 (date_current → saveContext2DB の直後)** に
   `@General$Script` モジュールを 1 個追加
2. その script 欄に `probe_script.js` の全文をペースト
3. テスト発信 (or 既存の flow で 1 コール)
4. Brekeke ログから `[ctx-probe ...]` 行を grep して全件回収 → 共有

または **既存の BusinessHour Classifier モジュールを一時的にこの probe で上書き**してもよい
(script 全文を probe に置き換えるだけ)。

## 評価

| 出力 | 解釈 |
|---|---|
| `[ctx-probe XX] OK result=2027-01-01 00:00:00 type=string` | **これが正解** → script.js を XX の API に書き換える |
| `[ctx-probe XX] OK result=null type=object` | API は存在するが指定 context 名が見えていない (スコープ違い) |
| `[ctx-probe XX] OK result=2027-01-01 00:00:00.0 type=object` | java.sql.Timestamp 等のオブジェクト → `.toString()` 変換要 |
| `[ctx-probe D1-ex-keys] OK result=...` | $ivr.getEx() に何のキーがあるか反射列挙 → 設計推測の材料 |
| 全件 EXCEPTION | candidates 全滅 → 別経路 (DB クエリ等) を検討 |

## 期待される候補

`A2-runner-getContextValue` / `B2-ivr-getContextValue` あたりが第一候補。Brekeke の AmiVoice/Soniox
等が `$ivr.getEx().ivr.timeStart` で IVR 内部状態を読んでいる前例から、`C` 系列の `getEx()`
経由もありえる。

NoteUtils が `com.brekeke.pbx.common.NoteUtils` だったことから、Context にも対称的に
`com.brekeke.pbx.common.ContextUtils` 等が存在する可能性が高い (G 系列で probe 済)。

## 次のステップ

1. probe 結果から正解 API を確定
2. script.js の CONFIG 部に `TARGET_DATETIME = "context:<contextName>"` prefix 対応を追加
3. 受入テストフローに「context 経由の判定」ケースを 1 ケース追加
