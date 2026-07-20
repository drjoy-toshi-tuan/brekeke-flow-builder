# Session Object Probe — setObject のコール越境判定

`$ivr.setObject` / `$runner.setObject` の保存先が **コール終了で破棄されるか、コールを跨いで残るか** を実機 2 コールで判定する probe。

## 背景 (なぜ調べるか)

generator 標準イディオム (`.claude/agents/generator.md` の `script_結果返却_*`) は

```javascript
var key = flowName + "." + rid;   // ← コールごとに違うキー
$ivr.setObject(key, res);
```

と **RID 入り動的キー**で保存しており、ほぼ全シナリオのサブフロー返却に展開されている
(`current_appointment_date.js` の `checkpoint.{rid}` / `saveContext.{rid}` も同型)。

- ストアが **per-call (コール終了で破棄)** なら無害 — rid はコール内で一定なので実質固定キー
- ストアが **コール越境で生存**する実装なら、誰も削除しない rid キーがコール数に比例して増える = **スローリーク**

スクリプト側からはストアの寿命が見えないため、実機で白黒つける (2026-06-03 メモリリーク調査の続き)。

## 検証マトリックス (probe が一度に見るもの)

| キー | 書き込み API | 何を検証するか |
|---|---|---|
| `leak_probe.ivr_marker` | `$ivr.setObject` (固定キー) | $ivr ストアの越境有無 |
| `leak_probe.runner_marker` | `$runner.setObject` (固定キー) | $runner ストアの越境有無 |
| `leak_probe.ivr_marker` を `$runner.getObject` で読む | — | 2 つの API が同一ストアか |
| `leak_probe.counter` | `$ivr.setObject` | 越境時に何コール分蓄積するか (1,2,3,... と増える) |
| `leak_probe.{rid}` | `$ivr.setObject` (**rid 動的キー**) | generator イディオムそのものの越境有無 (`last_rid` 経由で前回の rid を引く) |

## 手順

```
python build_probe_bivr.py     # → SessionObjectProbe.bivr 生成
```

1. `SessionObjectProbe.bivr` を Brekeke に import (フロー名: `テスト$SessionObjectProbe`)
2. **1 回目の架電**: 「けっかは、オーケーです」(残骸なし) を確認して切る
3. **2 回目の架電**: アナウンスで判定

| 2 回目のアナウンス | 意味 | 次のアクション |
|---|---|---|
| けっかは、**オーケー**です | ストアは per-call。**rid 動的キーは無害、スクリプト層はシロ確定** | 調査クローズ。リーク疑いは Brekeke 本体 (Jump to flow_Custom 等) 側へ |
| けっかは、**エヌジー**です。これは、N かいめの、コールです | **コール越境ストア実在**。全シナリオの `flowName.rid` キーが溜まり続けている | Dev チームへ報告 (generator イディオム + checkpoint パターンの削除 API 追加 or 設計変更) |

4. 詳細は Brekeke ログの `[LEAK-PROBE]` 行で確認:
   - `read <key> = '<value>'` — どのキーが残っていたか個別に分かる
   - `verdict=CROSS_CALL_PERSISTENT / PER_CALL_ONLY` — 機械判定
   - `self_check=WRITE_OK` — write 自体が効いているか (1 回目で必ず確認すること。
     `WRITE_MISSING` の場合は probe 自体が成立していないので結果無効)

## 注意

- 2 回の架電は**同一テナント・同一フロー**に対して行う (別テナントだとストアが分かれている可能性)
- 越境が確認された場合、この probe 自体が書いたキー (固定 4 + rid 1/コール) も残る。
  それ自体が「削除手段がない」という問題の実証なので、レポートにそのまま使える
- 連続架電の間隔は数十秒空ける必要なし。ただし「サーバー再起動でクリアされるか」も
  切り分けたい場合は、2 回目の前に再起動を挟むバリアントも有効
