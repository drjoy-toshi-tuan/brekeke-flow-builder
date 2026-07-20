# saveCompletionFlag2db — status / smsFlag 規格（SSoT）

> このファイルは `saveCompletionFlag2db`（および転送パターンにおける SMS 制御）の
> **status / smsFlag の唯一の定義元（Single Source of Truth）**である。
> `scripts/scaffold_generator.py`・`schemas/validator.py`・`schemas/qa_validator.py`・
> 他の brekeke ドキュメント（`モジュール詳細設定ガイド_1.md` / `brekeke_module_reference.md` /
> `brekeke_flow_reference.md`）は、値の定義についてすべて本ファイルに従う。
> 齟齬を見つけたら本ファイルを正として直すこと。
>
> 制定: 2026-07-03（浜口さん規格提供）。バグ防止のため値定義を一元化。

---

## 1. モジュール

- **type**: `drjoy^Persistence$saveCompletionFlag2db`
- 通常モジュールとして配置（subs 接続不可）。通話完了ステータス（`status`）と SMS フラグ（`smsFlag`）を Dr.JOY に保存する。
- 配置: 終話ガイダンス（TTS）の**直前**。順序 `saveCompletionFlag2db → TTS（終話）→ Disconnect`。
- **status / smsFlag はどちらも空欄にしない。** 置くなら必ず値を設定する（空欄はバグの原因）。

---

## 2. status（通話ステータス）

### 規定値は 0〜6。7 以上は施設オリジナル。

| status | 意味 | 区分 | 備考 |
|---|---|---|---|
| `0` | 途中切断 | **システム自動** | 通話が途中で切れると自動送信される。**モジュールを置かない**（例外は §4 転送失敗→継続）|
| `1` | 未処理（正常終話）| 規定 | 通常の聴取完了 |
| `2` | 代表案内 | 規定 | 非通知・海外・転送失敗（終話時）等の代表誘導。既定のフォールバック値 |
| `3` | 転送 | 規定 | **有人転送の成功時のみ**。§3 参照 |
| `4` | 処理中 | 規定 | IVR 側で設定するのは稀（pipeline は WARNING で意図確認）|
| `5` | 処理済み | 規定 | IVR 側で設定するのは稀。**⚠ `5` にすると SMS 送信後に患者側から返信を受け付けなくなる**（特殊挙動）。pipeline は WARNING |
| `6` | 時間外 | 規定 | 営業時間外で切断 |
| `7` 以上 | 施設オリジナル | **原則作らない** | 明確な指示がない限り生成しない。使う場合は人間レビュー必須（pipeline は WARNING）|

> **IVR（電話側）が通常配置するのは `1` / `2` / `3` / `6`。** `4`(処理中) / `5`(処理済み) は Dr.JOY 側の処理状態で、IVR が設定するのは稀（設定する場合は上記の特殊挙動に注意）。`0` は自動送信のため終話に置かない。

### 3（転送）の絶対ルール — 課金安全

> **転送でないフローで `status=3` を絶対に使わない。**
> `status=3` は転送料金の集計に直結するため、`call_transfer` ブロックが存在しないシナリオで
> `3` を設定すると、実際には転送していないのに転送料金が計上されうる。
>
> - 転送成功のときだけ `3`。
> - 聴取失敗など「転送でない終話」を誤って `3` にしない（scaffold は聴取失敗の `3` を `2` に矯正する / #231）。
> - pipeline（qa_validator E-17）は「`call_transfer` ブロックが無いのに `status=3` の終話がある」を CRITICAL で弾く。

---

## 3. smsFlag（SMS 送信フラグ）

| smsFlag | 動作 | 用途 |
|---|---|---|
| `1`〜`9` | Dr.JOY 側で定義された該当番号の SMS テンプレートを送信 | **送るときは基本 `1` から順に採番。最大 `9`** |
| `0` | SMS を送らない（積極的に設定しない場合の既定）| **一般的に「送りたくない」ときはこれ**。録音は正常に分割される |
| `-1` | SMS を送らない（**転送パターン専用**）| §4 参照。SaveDataToDrJoy を転送前に置く場合に限る |
| `-2` / `10` 以上 | **SMS が飛ばなくなる（誤設定）** | 使用禁止。範囲外の値を入れると送信されない |

### 重要な注意

- **一般の「SMS を送らない」に `-1` を使わない。** `-1` は SMS 非送信に加えて**録音の分割も止める**ため、
  通常の終話で `-1` を使うと録音データが取得できなくなる（録音分割バグ）。通常の非送信は `0`。
- `-1` は §4 の転送パターンでのみ使う正当値。

---

## 4. 転送パターンの status / smsFlag シーケンス（scaffold が自動配置）

転送では「転送前に情報だけ Dr.JOY へ確定させ、転送完了後に SMS を出す」制御を行う。
**scaffold が `call_transfer` ブロックから以下を機械配置する**（手書きで status=0 / smsFlag=-1 を置かせない）。

- **モジュール**: `saveData2DrJOY`（型 `drjoy^External Integration$saveData2DrJOY`。転送直前に Dr.JOY へ
  データ確定を促す POST トリガ。値の運び屋ではなくタイミング保証。params=`url`（人間が IVR プロパティで設定・空で生成）
  / `connect_timeout`=2 / `request_timeout`=3）。詳細は memory `reference_brekeke_savedatatodrjoy`。
  ※ 通称「SaveDataToDrJoy」だが Brekeke パレットの正式名は **`saveData2DrJOY`**。

### 配置順（scaffold 生成）

1. **入口＝送信保留フラグ**（`saveCompletionFlag2db` `status=0, smsFlag=-1`）。他ブロックからの遷移はここに入る。
   `smsFlag=-1` はここが**唯一の配置箇所**（転送完了まで SMS 送信／録音分割を保留する）。
2. **`saveData2DrJOY`**（Dr.JOY データ確定 POST）。
3. **`call-transfer`**（有人転送本体）。
4. **転送後の status 上書き**（終話の完了フラグが担う）:
   - **転送成功** → `status=3`（`END_転送成功`）。smsFlag は終話定義の値（`0`〜`9`）で保留の `-1` を解除。
   - **転送失敗 → 終話** → `status=2`（`END_転送失敗`・明示があればそれ）。smsFlag は `0`〜`9`。
   - **転送失敗 → シナリオ継続**（`next_failure` が終話でない場合）→ scaffold が
     **`status=0, smsFlag=0` の上書きフラグ（名前に「転送継続」）を挟んでから継続先へ**。
     保留していた `smsFlag=-1` を打ち消し、以降の録音が正常に送られるようにする。

> **status / smsFlag はどちらも空欄にするとバグる。** 上記はすべて明示値で生成される。

### status=0 上書きの扱い（方針・2026-07-03 確定 / 実装済）

- **基本方針（機械配置・実装済）**: 上記 1〜4 を **scaffold（`build_transfer_flag` / `build_save_data_to_drjoy`）が自動生成**。
  資料に「status を 0 にせよ」と書く箇所は作らない。
- **validator 対応（実装済）**: COMP-001 は `status=0` を、**(a) `smsFlag=-1`（＝転送前の送信保留）** または
  **(b) 完了フラグ名に「転送」かつ「継続」を含む（＝転送失敗→継続の上書き）** の場合のみ許容。
  それ以外の `status=0`（終話への誤配置等）は従来どおり CRITICAL（→`2` に auto-fix）。
- **例外対応**: 上記の目印に当てはまらない特殊な status=0 が要るケースは **patch_box** で COMP-001 を skip して対応する。

---

## 5. 典型パターン早見表

| 終了ルート | status | smsFlag | 説明 |
|---|---|---|---|
| 正常終話（携帯・SMS送る）| `1` | `1`〜`9` | 未処理 + SMS 送信 |
| 正常終話（固定・SMS送らない）| `1` | `0` | 未処理 + 非送信（固定電話は SMS 受信不可）|
| 非通知・海外で切断 | `2` | `0` | 代表案内 + 非送信 |
| 時間外で切断 | `6` | `0` | 時間外 + 非送信 |
| 転送前 送信保留（scaffold自動）| `0` | `-1` | 入口フラグ → `saveData2DrJOY` → 転送（§4）|
| 有人転送 成功 | `3` | 成功後 `0`〜`9` | 保留 `-1` を解除（§4 のシーケンス）|
| 有人転送 失敗（終話）| `2` | `0`〜`9` | 明示なければ `2` |
| 有人転送 失敗（継続・scaffold自動）| `0` | `0` | 継続地点で `-1` を上書き（名前に「転送継続」・§4）|
| 途中切断 | （置かない）| （置かない）| システムが自動で `status=0` |

---

## 6. pipeline での強制（このファイルに追従する実装）

| チェック | 場所 | 内容 |
|---|---|---|
| CTX-012 | `validator.py` | `status` 空 → CRITICAL |
| COMP-001 | `validator.py` | `status` が `0` → CRITICAL（auto-fix: `2`）。ただし **(a) `smsFlag=-1`（転送前保留）** または **(b) 名前に「転送」かつ「継続」（転送失敗→継続の上書き）** は許容（§4）。他の特殊ケースは patch_box で skip |
| 転送シーケンス生成 | `scaffold_generator.py` | `call_transfer` から 保留フラグ(`status0/smsFlag-1`)→`saveData2DrJOY`→転送 を自動配置。転送失敗→継続時は `status0/smsFlag0`（名前「転送継続」）を挿入（§4）|
| COMP-004 | `validator.py` | `smsFlag` が `{-1,0,1,…,9}` 以外（`-2`・`10`+ 等）→ CRITICAL |
| COMP-005 | `validator.py` | `smsFlag` 空 → CRITICAL（送らないなら `0` を明示）|
| E-8 | `qa_validator.py` | termination の `status`: `0` → CRITICAL / `1`/`2`/`3`/`6` → OK / `4`・`5` → WARNING（処理中/処理済み・IVR設定は稀）/ `7`+ → WARNING（施設オリジナル）/ 不明値 → CRITICAL |
| E-17 | `qa_validator.py` | `call_transfer` が無いのに `status=3` の終話 → CRITICAL（課金安全。聴取失敗は #231 矯正のため除外）|
| smsFlag 矯正 | `scaffold_generator.py` | `saveCompletionFlag2db` の `smsFlag=-1` → `0` に矯正（§3 一般ルール。転送前 `-1` は SaveDataToDrJoy 側で別扱い）|
| status 矯正 | `scaffold_generator.py` | `status` `0` → `2` に矯正（`4`/`5` は矯正しない）。聴取失敗の `3` → `2` に矯正（#231）|
