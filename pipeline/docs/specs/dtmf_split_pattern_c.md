# Pattern C: DTMF 分離 hearing 仕様

**ステータス**: ドラフト（2026-05-21 起草、浜口さん承認待ち）
**起点**: `~/Downloads/DTMF分離.bivr`（浜口さん 2026-05-21 共有）
**対象施設の一例**: 中東遠総合医療センター_健診（用件1/用件2/人数/予約確認/変更内容 等）

---

## 1. 目的と背景

これまでは DTMF 入力も発話 STT も **すべて OpenAI に流して** 分岐させていた。これは挙動が揺れる原因になるため（DTMF の "1" を OpenAI が誤分類する等）、**DTMF は OpenAI を通さず STT-DTMF.next の regex で直接振り分ける** 構成に切り替える。

参考: memory `feedback_branching_pattern_a_b`「OpenAI直後分岐(A) vs 後段ContextMatchRouter(B)」に **Pattern C: DTMF 分離** を追加する位置づけ。

---

## 2. 全体構造（DTMF 分離.bivr を一般化）

```
[step] TTS  ─→  [step] STT-DTMF
                     │
                     ├─ ^TIMEOUT$  → リトライ_[step]
                     ├─ ^ERROR$    → リトライ_[step]
                     ├─ ^NO_RESULT$→ リトライ_[step]
                     │
                     ├─ ^1$        → save_[step]_[label1]  (saveContext2DB)
                     ├─ ^2$        → save_[step]_[label2]
                     ├─ ^3$        → save_[step]_[label3]
                     │   …                     …
                     ├─ ^[loopback_dtmf]$ → TTS_[step]   ← 同ステップへ replay（retry カウンタを増やさない）
                     │
                     └─ ^.+$       → OpenAI_[step]   ← 発話のみ
                                       │
                                       ├─ TIMEOUT/ERROR/NO_RESULT → リトライ_[step]
                                       ├─ ^[label1]$  → save_[step]_[label1]
                                       ├─ ^[label2]$  → save_[step]_[label2]
                                       │   …                  …
                                       └─ (no catchall) 全 label にマッチしなければ NO_RESULT → retry

リトライ_[step] (Speech Retry Counter)
  ├─ true   → TTS_[step]   （retry 上限内）
  └─ false  → retry_failure 先（end_failure なら 完了フラグ_聴取失敗）
```

### 2.1 各 saveContext2DB の next（重要）

| 設計 | scaffold 出力 |
|---|---|
| `dtmf_options[i].next` を **個別に指定** している場合 | `save_[step]_[label_i].next` = その next（直接配線、CMR 不要） |
| `dtmf_options[i].next` 省略 + ブロック `next` のみ指定 | 全 save_..._next = 共通の next（合流） |

→ DTMF 分離直後の CMR は **生成しない**。直接配線する。

### 2.2 直結モード（save_to 省略時、2026-05-26 追加）

`save_to` を省略 or 空文字にすると **直結モード** になり、saveContext2DB を生成せず `STT-DTMF.next` を直接 `dtmf_options[i].next` に接続する。yes/no 二択など、コンテキスト保存が不要な hearing に使う。

```
[step] STT-DTMF
  ├─ ^1$ → (label1 の next 先)   ← save_[step]_label1 を経由しない
  ├─ ^2$ → (label2 の next 先)
  └─ ^.+$ → OpenAI_[step]
              └─ ^[label_i]$ → (label_i の next 先)
```

| `save_to` | 生成構造 | 用途 |
|---|---|---|
| **non-empty**（例: `classification`） | saveContext2DB 経由（既存挙動）。`save_[step]_[label]` を生成 | コンテキスト保存が必要、後段で参照される |
| **空 / 省略** | **直結モード**。saveContext2DB を生成せず STT-DTMF.next を opt.next に直結 | yes/no 二択、ルーティング目的のみで保存不要 |

> **背景**: 2026-05-26 すずな皮ふ科_診療 で発覚。`確認_手術内容` / `患者_携帯` の二択 hearing（元 OpenAI `params.contextName: ""`）に Pattern C を機械適用すると、`save_*_肯定/否定` モジュールが contextName 空で生成され、Brekeke VUI 上「保存先のないコンテキスト保存」状態になる。直結モードはこれを回避する。
>
> **判断ルール（dirlite agent 側）**: 既存 BIVR の `openAI_[step].params.contextName` を確認し、空なら Pattern 2 改修時に `save_to: ""` 相当（直結モード）を選ぶ。Pattern 1/3/4 で新規作成する場合は director / yaml 書き手が明示的に `save_to` を省略する。

### 2.2 loopback DTMF（「もう一度」）

`dtmf_options[i].action: replay` を指定すると、`STT-DTMF.next` で `^[dtmf]$ → TTS_[step]` を生成する。retry カウンタは increment しない。

---

## 3. 設計書 YAML 記述形式

### 3.1 hearing ブロック拡張（新フィールド: `input_method`, `dtmf_options`）

#### 3.1.a saveContext2DB 経由パターン（コンテキスト保存あり）

```yaml
- step: 用件1聴取
  type: hearing
  input_method: dtmf_split          # 新規。"voice_only"（既定）| "dtmf_split" | "dtmf_only"
  output_format: enum
  save_to: classification           # contextName を明示 → save_用件1聴取_予約 等を生成
  retry_failure: end_failure
  dtmf_options:                      # input_method: dtmf_split のとき必須
    - dtmf: "1"
      label: "予約"
      next: 受診希望コース分岐
    - dtmf: "2"
      label: "変更"
      next: 現在の予約日聴取_変更
    - dtmf: "3"
      label: "キャンセル"
      next: 現在の予約日聴取_キャンセル
    - dtmf: "4"
      label: "問い合わせ"
      next: 予約確認
    - dtmf: "5"
      label: "もう一度"
      action: replay                 # 同ステップへ loopback
  # output_labels は dtmf_options[].label から自動算出（action=replay は除く）
```

#### 3.1.b 直結パターン（コンテキスト保存なし、yes/no 二択など）

```yaml
- step: 確認_手術内容
  type: hearing
  input_method: dtmf_split
  output_format: enum
  # save_to を省略 → 直結モード（saveContext2DB を生成せず STT-DTMF.next を opt.next に直結）
  retry_failure: end_failure
  dtmf_options:
    - {dtmf: "1", label: "肯定", next: 変更_予約内容}
    - {dtmf: "2", label: "否定", next: 状態_sms2}
```

### 3.2 既存 `conditions` との関係

- `input_method: dtmf_split` 指定時は **`conditions` を書かない**（dtmf_options に統合）。
- 既存 `conditions` 形式（音声のみ）は `input_method: voice_only`（既定）として変更なし、後方互換維持。
- qa_validator は `dtmf_split` + `conditions` 併存を CRITICAL でブロックする。

### 3.3 hearing_items の `stt_type`

- `input_method: dtmf_split` のとき `stt_type` は **`"DTMF_AmiVoice"` 固定**（自動補正 or qa_validator で警告）。
- `dtmf_max_length` は dtmf_options の最大 dtmf 桁数から自動算出（既定 1）。

### 3.4 サンプル（中東遠 用件1）

```yaml
- step: 用件1聴取
  type: hearing
  input_method: dtmf_split
  output_format: enum
  save_to: classification
  retry_failure: end_failure
  dtmf_options:
    - {dtmf: "1", label: "予約",       next: 受診希望コース分岐}
    - {dtmf: "2", label: "変更",       next: 現在の予約日聴取_変更}
    - {dtmf: "3", label: "キャンセル", next: 現在の予約日聴取_キャンセル}
    - {dtmf: "4", label: "問い合わせ", next: 予約確認}
    - {dtmf: "5", label: "もう一度",   action: replay}
```

---

## 4. モジュール命名規則

| 役割 | 命名 |
|---|---|
| TTS | `TTS_[step]`（既存と同一: `build_tts(step, ...)` の `name = step`） |
| STT-DTMF | `入力_[step]`（既存 `build_stt` と同名、ただし `stt_type: DTMF_AmiVoice`） |
| OpenAI（発話路） | `OpenAI_[step]`（既存と同一） |
| Speech Retry Counter | `リトライ_[step]`（既存と同一） |
| saveContext2DB（DTMF 直接） | **新規** `save_[step]_[label]`（例 `save_用件1聴取_予約`） |
| save2db（録音用、共有） | `save-[save_to]` または `save-[step]`（既存規則踏襲） |

> `save_` プレフィックス（アンダースコア）= Pattern C 専用の saveContext2DB 群。`save-` プレフィックス（ハイフン）= 既存の録音 sub モジュール。命名で区別する。

---

## 5. CMR 直列ヘルパー（後段で saveContext2DB 群を参照する場合のみ）

DTMF 分離直後の合流は CMR 不要だが、**もっと後段で「どの saveContext2DB を通ったか」を判定したい** 合流型分岐では CMR 直列が必要。

### 5.1 利用ケース

例: 終話判定で `classification × phonetype` で分岐したいが、`classification` は DTMF 分離で saveContext2DB が 4 つに分かれているため、**reference_module を 1 つに絞れない**。
→ Brekeke CMR は YES/NO 二択しか出せないので、N 分岐は CMR×(N−1) を直列、最後は CMR の NO（catchall）。

### 5.2 設計書 YAML 表現（新ブロック型: `cmr_chain`）

```yaml
- step: 終話判定_classification
  type: cmr_chain
  reference_modules:                 # 直列の各 CMR が参照する saveContext2DB 群
    - module: save_用件1聴取_予約
      next: END_予約系
    - module: save_用件1聴取_変更
      next: END_変更系
    - module: save_用件1聴取_キャンセル
      next: END_キャンセル
    - module: save_用件1聴取_問い合わせ
      next: END_問合せ系
  default_next: END_エラー           # 全部 NO だった場合の catchall（必須）
```

scaffold は以下を組む：

```
CMR_終話判定_classification_0 (ref=save_用件1聴取_予約)
  ├─ YES → END_予約系
  └─ NO  → CMR_終話判定_classification_1
CMR_終話判定_classification_1 (ref=save_用件1聴取_変更)
  ├─ YES → END_変更系
  └─ NO  → CMR_終話判定_classification_2
…
CMR_終話判定_classification_(N-1) (ref=save_用件1聴取_問い合わせ)
  ├─ YES → END_問合せ系
  └─ NO  → END_エラー        ← default_next
```

> 中東遠の MD には「用件1_分岐判定」のような内部判定ステップがあるが、案 A（save2DB.next 直接配線）で十分なので **このケースでは cmr_chain は使わない**。cmr_chain は「合流後の遅い分岐」用。

---

## 6. パイプライン各コンポーネントへの影響

| コンポーネント | 変更点 |
|---|---|
| **scaffold_generator.py** | hearing builder に `input_method == "dtmf_split"` 分岐を追加。新ヘルパー `build_dtmf_split_stt()` + `build_save_context_fixed()` 流用。新ブロック型 `cmr_chain` の builder 追加 |
| **qa_validator.py** | 新 D 系チェック追加: D-1 dtmf 値重複 / D-2 conditions と併存禁止 / D-3 replay action ≥1個まで / D-4 cmr_chain.reference_modules 全部 `save_` プレフィックス確認 |
| **gen_properties.py** | `save_[step]_[label]` モジュールの contextValue（label 値）を `displayProperty` に書き出し |
| **block_mapper.py** | 新モジュール `save_[step]_[label]` をマッピング辞書に追加（fixer のブロック範囲解決用） |
| **layout_calculator.py** | DTMF 分離直後の `save_..._[label]` 群を STT-DTMF 直下に横並びレイアウト |
| **prompter** | OpenAI（発話路）の `output_labels` は dtmf_options[].label から自動算出されるので、prompter は dtmf 値を意識せず通常通り label 群でプロンプトを書く。**追記指示なし** |

---

## 7. 既存 hearing との後方互換

- `input_method` 未指定 = `voice_only` = 既存挙動（STT.next の `^.+$` で OpenAI に流す）。
- 既存 YAML は一切変更不要。
- regression テスト: smoke test で「DTMF 分離なしの hearing」が壊れていないことを確認（step 6）。

---

## 8. 中東遠 健診 への適用予定マッピング

| 新 MD のステップ | 設計書 YAML 表現 |
|---|---|
| 用件1（プッシュ1-5: 予約/変更/キャンセル/問い合わせ/もう一度） | `input_method: dtmf_split`, options 5 件（5=replay）|
| 用件2（プッシュ1-6: 人間ドック/協会けんぽ/健康診断/精密検査/その他/もう一度） | `input_method: dtmf_split`, options 6 件（6=replay）|
| 人数（プッシュ1-2: 1or2/3以上） | `input_method: dtmf_split`, options 2 件 |
| 予約確認（プッシュ1-2: あり/なし） | `input_method: dtmf_split`, options 2 件 |
| 変更内容（プッシュ1-3: 日程/オプション/その他） | `input_method: dtmf_split`, options 3 件 |
| 生年月日（DTMF 8 桁、復唱あり） | 既存 datetime + dtmf_max_length: 8（**dtmf_split ではない**: 値が固定でないため）|
| 電話確認/依頼（DTMF 11 桁） | 既存 text + dtmf_max_length: 11（同上）|

---

## 9. 残課題 / 未確定事項

- **`<dtmf digit='X'/>` SSML の扱い**: TTS 発話文言から strip して、IVR プロパティ側で digit ヒント設定する（memory `feedback_tts_dynamic_value_syntax` 経由で gen_properties が処理予定 — Pattern C 専用拡張も必要か検証）。
- **DTMF only モード（発話を無視）**: 今回は `dtmf_split`（DTMF + 発話 OpenAI）のみ実装。完全 DTMF only は将来追加可能（STT.next の `^.+$ → OpenAI` を削るだけ）。
- **OpenAI 発話路で NO_RESULT が頻発する施設**: dtmf_split が浸透して発話ユーザーが減れば自然に解決する想定。
