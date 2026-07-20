# 連結テスト (Pattern 7) — 仕様

## 目的・位置づけ

**単体受入を通したモジュール群を繋いで作られた本番フロー(STT 経由)が「正常に動いたときどうなるか」を実機で保持する**テスト。STT 認識の不確実性を切り離し、**正規化・配線・API 連携**が実機で意図どおり動くかを検証する。

確認するのは次の3点だけ（余計なことはしない）:
1. **連結で全処理を通過するか**（全エッジ・全モジュール通過＝カバレッジ）
2. **実機の挙動**
3. **吐き出すログ（＝ゴールデンログ資産）**

### スコープ外
- **入力パターン耐性**（分岐モジュールが何パターンに耐えるか）→ 単体受入(Pattern 6 / `modules/`)の担当。
- **STT 認識精度**（音声→文字起こし）→ 音声注入レーン(Twilio+WAV)の担当。
- **TTS / プロパティ / データ連携 side-effect** → 別レイヤ（未整備、別途）。

## 機構（2026-06-08 福岡大学病院で v0/v1/v2 実機実証済）

| 要素 | 実装 |
|---|---|
| STT スタブ | STTノード(`drjoy^AmiVoice$Speech to Text` / `…$DTMF AmiVoice STT Input`)を `@General$Script` に置換し `$runner.setResult(注入値)`。`next`/`subs`/`matchingmethod=1` 温存 → 下流の正規化(`getModuleResult`読取)・CMR・終話はそのまま動く |
| ケース選択 | 冒頭に **DTMF ケースセレクタ**を前置 → `$ivr.setObject("__tc_id", id)`。1 bivr で全ケース（発信時に番号+#） |
| attempt-aware | per-node カウンタ(`$ivr.get/setObject`)で試行回数依存に出し分け `seq[min(n,len-1)]`。`["NO_RESULT","1"]`=1回リトライ後成功 / `["NO_RESULT"]`=exhaust |
| 状態保持 | **`$ivr.setObject` / `$ivr.getObject`（per-call・同一コール read-back 実証）**。`getSystemVariableValue`+`save2db` は ad-hoc context をラウンドトリップしないので使わない |
| 命名(本番非衝突) | **グループ名は温存し本番と同一グループに同居**（Brekeke 投入が目視手作業＝別グループ大量フローは確認ロングランで破綻するため必須）。シナリオ名先頭に短縮タグ `T_`（`--tag` 可変）を付与。jump も rename マップで追従、グループは自動検出。**bivr zip エントリ名は URLエンコード後 255B 上限**（日本語1字=9B）。タグ付与で超過する場合は **255B から逆算してサブフロー名を先頭優先で自動短縮**（内容ヒント保持・衝突は連番。テスト名は使い捨て前提）。グループ名自体が予算超なら fail-fast（同一グループ内テスト不能＝デプロイ層でのグループ名短縮が必要） |
| 採点 | 通話後のチェックポイントトレースを cases の `expect` と突合（marker `[STT-STUB] …`）。完走トレースは `golden/` に資産化 |

## カバレッジ設計（構造監査を内包）

復元グラフから**全エッジ（リトライ true/false 含む）を1回ずつ通る最小ケース集合**を設計する。
- リトライ exhaust エッジを踏むケースで、**catch-all 欠落のデッドエンド（例: 用件_分岐に classification 空で到達）が自動で1ケースとして現れる**（＝静的監査を別工程にしなくてよい）。
- 到達不能・孤立ノードの検出だけはグラフ静的解析の固有領域。

## 使い方

```
python connection_test/stub_stt_connection.py \
    --bivr <落としてきた本番.bivr> \
    --cases connection_test/cases/<施設>_<flow>.json \
    [--facility <施設略称>] [--entry-flow <フロー短名>] [--out <出力.bivr>]
```
出力 bivr を Brekeke のテスト番号にアップ → 発信して**ケース番号+#**を押す（ハンズフリー）。ログを cases の expect と突合。

## ケース表スキーマ (`cases/*.json`)
- `meta.entry_flow`: セレクタを前置するフロー短名（省略時はツールが推定）
- `defaults`: サブフロー系STTの既定注入。`_order` のキーワード先頭一致で node に割当
- `cases[].dtmf`: 選択番号 / `cases[].inject`: `{ノード名: [試行列]}` / `cases[].expect`: 期待終端・チェックポイント

## 制約（実機実測済）
- 1 コール 1000 モジュール上限（実運用 900）。DTMF 分岐で1通話1ケースなら実行モジュールは1ケース分のみ＝ケース数は上限に縛られない。
- `setObject` は per-call（コール跨ぎ不可）。カウンタ・__tc_id はコール内のみ有効。
- DTMF セレクタは同一数字連打（例 "11"）が稀に timeout → `__保存tc` の「空なら "1"」フォールバックで graceful（再試行で解消）。
- **Entity の string-result 受理は未検証**（case 3/4 = 声→Entity 経路。DTMF 経路は検証済）。

## DoD
- 対象フローの全エッジをカバーするケース集合を `cases/` に定義。
- 実機で完走パスが「通話完了」到達 or 意図した終端に到達し、トレースを `golden/` に保持。
- `README.md` 台帳に施設・実施日・結果を登録。
