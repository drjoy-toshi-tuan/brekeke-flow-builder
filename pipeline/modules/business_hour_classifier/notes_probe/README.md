# Notes API Probe

Brekeke の `drjoy^...$Script` モジュール (Nashorn JS) から Notes plugin
(contains / matches / lookup / script) を呼べる API シグネチャを **empirical** に特定するための probe。

調査結果: WebFetch では Notes plugin の Script 経路 syntax が見つからず (Soniox/AmiVoice 風 AudioStreamScript は別経路で Note を読んでいる)、最短の答え合わせは Brekeke 実機での 1 コールで全候補を試すこと。

## 同梱物

| ファイル | 用途 |
|---|---|
| `test_holidays_note.txt` | Brekeke Note 「test_holidays」に貼り付ける本文 (2026 年祝日 17 行) |
| `probe_script.js` | 各 API 候補を try/catch で呼ぶ JavaScript |
| `build_probe_bivr.py` | probe_script.js を埋め込んで .bivr を組み立てる |
| `NotesAPIProbe.bivr` | Brekeke に import するテストフロー |

## 試す API 候補

| ID | 候補 | 説明 |
|---|---|---|
| A1-A4 | `contains() / matches() / lookup()` グローバル関数 | ARS と同じ syntax がそのまま使えるか |
| B1-B2 | `$pbx.contains()` / `$pbx.notes.contains()` | $pbx グローバル経由 |
| C1-C4 | `$runner.contains()` / `$ivr.contains()` / `$runner.getNote()` / `$ivr.getNote()` | コンテキストオブジェクト経由 |
| D1-D3 | `Java.type("com.brekeke.pbx.notes.NotesPlugin").contains()` 等 | Java type 直接呼び出し (推測) |
| E1-E2 | `NoteManager.contains()` / `Notes.contains()` | 別の Java type 名候補 |
| F1-F2 | `for (var k in $runner)` / `$ivr` | reflection で利用可能メソッドを列挙 |

F1/F2 が特に有益 — `$runner` / `$ivr` のメソッド名を全部出すので、ドキュメント未記載 API が見える可能性がある。

## 実行手順

1. Brekeke 管理画面で **Note「test_holidays」を新規作成**し、`test_holidays_note.txt` の中身を貼り付け
2. **`NotesAPIProbe.bivr` を Brekeke に import** (Flow としてインポート、テスト$NotesAPIProbe という名前で登録される想定)
3. テスト$NotesAPIProbe フローに **テスト発信 (社内番号で 1 コール) または「フロー実行」**
4. Brekeke ログ画面で `[probe ...]` を含む行を grep (約 17 行出るはず)
5. 結果を浜口さん側でメモ → こちらにコピペ

## 結果の読み方

- **`[probe A1-contains-global-hit] OK result=true type=boolean`** → A 系列 (グローバル関数) が動く。これがベスト
- **`[probe X] EXCEPTION ReferenceError ...`** → その候補は使えない
- **`[probe F1-runner-methods] OK result=method1,method2,...`** → $runner にあるメソッド名がわかる
- **どれも EXCEPTION** → Notes plugin は Script モジュールからは呼べない → Property 集中管理 (env_*.txt) ルートに切り戻し

## 注意事項

- probe_script.js は Brekeke ログに値を出すだけで副作用なし。試行中の例外は全部 catch しているので 1 コール内で全候補が実行される
- フローの最後で `$runner.setResult("probe_done")` を返して `@IVR$Disconnect` に流して切断するので、テスト発信者側は数秒で切れる
- ログ収集後は Note と Flow は削除して構わない
