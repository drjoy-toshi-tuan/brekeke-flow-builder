# 差分分析レポート: ユアクリニックお茶の水

## サマリー
- **VFB生成**: 48モジュール（1フロー `ユアCLお茶水$診療`）
- **人間修正**: 61モジュール（3フロー: 診療-Demo30 + 氏名7 + 電話番号24）
- **構造的一致率**: 約45%（3施設中最もシンプルな構成。メインフロー骨格は近いが冒頭チェーン順序・Script未生成・サブフロー欠落が大きな差分）
- **主な差分カテゴリ**: 冒頭チェーン順序、サブフロー未生成、Script未生成（業務ロジック）、ContextMatchRouter未生成、Re-confirmation未生成、save2db/CompletionFlag/Disconnect過剰生成

---

## 1. 構造差分

### 1.1 フロー構成

| 観点 | VFB生成版 | 人間修正版 |
|------|-----------|------------|
| フロー数 | 1（サブフロー2本を参照するが内容なし） | 3（診療-Demo + 氏名 + 電話番号） |
| メインフロー名 | `ユアCLお茶水$診療` | `ユアCLお茶水$診療-Demo` |
| 氏名サブフロー | Jump_氏名聴取（参照のみ・内容なし） | `ユアCLお茶水$氏名`（7モジュール） |
| 電話番号サブフロー | Jump_電話番号確認（参照のみ・内容なし） | `ユアCLお茶水$電話番号`（24モジュール） |

**VFB-011確認**: サブフロー2本のJump参照はあるが内容は空。実動作不可。

### 1.2 冒頭チェーン

| VFB生成版 | 人間修正版 |
|-----------|------------|
| `冒頭_wait` → `コンテキスト設定` → **`着信電話番号確認(incoming)`** → `受付時間判定(acceptance_times)` → `冒頭_アナウンス(TTS)` | `冒頭待ち時間(wait)` → `コンテキスト設定` → **`冒頭アナウンス(TTS)`** → `着信電話番号確認(incoming)` → `受付時間判定(acceptance_times)` |

**VFBの冒頭チェーン順序問題**（帯広・長野でも確認）:
- VFBは incoming-classifier を 冒頭TTS より**前**に配置する
- 人間版は 冒頭TTS → incoming-classifier の順（正しい順序）
- 結果: VFB版では非通知の場合も冒頭アナウンスが再生されない

### 1.3 モジュール数比較（タイプ別）

| モジュールタイプ | VFB (1フロー) | 人間 (3フロー計) | 差分 | 備考 |
|-----------------|------|------|------|------|
| Script | **1** | **10** | **+9** | 人間版: 時刻判定3+SMS1+リトライ制御2+電話番号変換3+ssml1 |
| save2db | 11 | 6 | **-5** | VFB-003確認 |
| saveCompletionFlag | **6** | **4** | **-2** | VFB-004確認。ContextMatchRouterで集約 |
| Disconnect | **6** | **3** | **-3** | VFB-004確認 |
| TTS | 11 | 10 | -1 | 近似 |
| STT (AmiVoice) | 1 | 2 | +1 | |
| OpenAI | 1 | 3 | +2 | |
| Retry Counter | 1 | 5 | +4 | サブフロー内Retry追加 |
| DTMF STT Input | **0** | **2** | **+2** | VFB-005確認。電話番号サブフロー内 |
| Re-confirmation | **0** | **3** | **+3** | VFB-002確認。電話番号サブフロー内 |
| ContextMatchRouter | **0** | **1** | **+1** | VFB-001確認。管理時間分岐 |
| Phone Normalization | 0 | 1 | +1 | 電話番号正規化 |
| saveContext2DB | 3 | 1 | -2 | 人間版はOpenAI自動保存を活用 |
| Call Transfer | 1 | 1 | 0 | 一致 |
| acceptance_times | 1 | 1 | 0 | 一致 |
| incoming-classifier | 1 | 2 | +1 | 電話番号サブフロー内にも配置 |

---

## 2. モジュール差分

### 2.1 VFBが生成しなかったモジュール（人間版にのみ存在）

#### サブフロー本体（VFB-011確認）
- `ユアCLお茶水$氏名` フロー全体（7モジュール）: STT + Retry + Script(リトライ制御) + save2db
- `ユアCLお茶水$電話番号` フロー全体（24モジュール）: DTMF×2 + Retry×3 + OpenAI×2 + Re-confirmation×3 + Phone Normalization + Script×6 + incoming-classifier + saveContext2DB + save2db×3

#### ContextMatchRouter（1個）— VFB-001確認
- `管理時間分岐` — 業務時間帯による案内分岐
  - `^1$` → 予約転送アナウンス（業務時間内）
  - `^.+$` → Flag_受付完了2（その他）

#### Re-confirmation node data（3個）— VFB-002確認（電話番号サブフロー内）
- `着信アナウンス` — 着信番号の復唱確認
- `確認_電話番号` — 入力電話番号の復唱確認
- `確認_着信_電話番号` — 着信番号の最終確認

#### Script群（9個）— 新規発見：業務ロジックScript未生成
- `script_日曜時間判定` — 日曜日の受付時間判定（JavaScript実装）
- `script_業務時間外判定` — 平日・土曜の業務時間外判定
- `script_ペナルティ時間判定` — 受付終了前後の判定
- `script_SMS送信` — SMS通知送信処理
- `script_電話番号` — 電話番号変換処理（電話番号サブフロー）
- `script_電話番号リトライ失敗2/3` — 電話番号リトライ制御
- `script_ssml` — 電話番号のSSML読み上げ
- `script_氏名リトライ失敗` — 氏名リトライ制御（氏名サブフロー）

#### Phone Normalization（1個）
- `正規化_着信_電話番号` — 電話番号フォーマット正規化

### 2.2 VFB版にのみ存在するモジュール（人間版で削除・統合）

#### save2db過剰（5個削減）
VFB版: TTS11個・STT1個・Retry1個 それぞれに個別save2db（11個）
人間版: 共有save2dbを活用し6個に集約（save_氏名_氏名, save_dialogue等）

#### saveCompletionFlag + Disconnectの過剰生成（各2〜3個削減）

VFB版の終話パス（6パターン）:
- 非通知 → CompletionFlag(status=2) → Disconnect
- 受付完了 → CompletionFlag(status=1) → Disconnect
- 時間外受付完了 → CompletionFlag(status=1) → Disconnect
- 転送 → CompletionFlag(status=3) → Disconnect
- 転送失敗 → CompletionFlag(status=2) → Disconnect
- 聴取エラー → CompletionFlag(status=2) → Disconnect

人間版: ContextMatchRouterで分岐し、saveCompletionFlag4個・Disconnect3個に集約

#### saveContext2DBの過剰生成（2個削減）

VFB版: `saveCtx_時間外ON`, `saveCtx_時間外OFF`（acceptance_times後の時間外フラグ保存）, `saveCtx_用件`（用件区分保存）
人間版: 電話番号サブフローの `save-電話番号` のみ。用件区分はOpenAIのcontextName自動保存機能を活用。

### 2.3 両方にあるが内容が異なるモジュール

#### acceptance_times の分岐設計

| 観点 | VFB版 | 人間版 |
|------|-------|--------|
| 分岐先数 | 5本（時間外×3、転送、冒頭） | 2本（時間外Script、通常ルート） |
| 時間外処理 | saveCtx_時間外ON → TTS → CompletionFlag → Disconnect | Script（JavaScript）で詳細な時間帯別判定 |
| 通常処理 | saveCtx_時間外OFF → 問い合わせTTS | 直接 問い合わせTTS へ |

VFBはsaveContextで時間外フラグを保存する設計だが、人間版はScript（JavaScript）で直接時間帯判定を実行する。これにより人間版では日曜日・平日・土曜ごとに異なる受付時間ロジックを実装している。

#### Jump to Flow のflowname形式（VFB-012確認）

| 観点 | VFB版 | 人間版 |
|------|-------|--------|
| Jump_氏名 flowname | `drjoy^Jump_to_flow$氏名聴取` | `drjoy^ユアCLお茶水$氏名` |
| Jump_電話番号 flowname | `drjoy^Jump_to_flow$電話番号確認` | `drjoy^ユアCLお茶水$電話番号` |
| properties | 空欄（FLOW-005違反） | TTS プロンプトを渡す |

#### Retry Counter の挙動

VFB版: 問い合わせ内容に対してRetryを1個のみ配置。false遷移先は `終話_聴取エラー`
人間版: サブフロー（氏名・電話番号）内にRetryを合計5個配置。一部はScript経由でリトライ制御

---

## 3. Property.md差分

### 3.1 行数比較

| 観点 | VFB版 | 人間版 |
|------|-------|--------|
| 総行数 | 89行 | 44行 |
| TTSプロンプトキー数 | 12（VFBのみ） | 9（人間版のみ） |
| 共通キー数 | 18 | 18 |

### 3.2 office_id
両バージョンに存在・同値。VFB-008は今回も非確認。

### 3.3 VFB版にのみ存在するキー（12個）

VFBの命名規則によるプロンプトキー群:
- `冒頭_アナウンス.prompt` → 人間版では `冒頭アナウンス.prompt`
- `END_受付完了.prompt`, `END_聴取エラー.prompt`, `END_時間外受付完了.prompt` → 人間版では `受付完了アナウンス.prompt` 等
- `転送_アナウンス.prompt`, `転送_リトライ失敗_アナウンス.prompt`, `転送失敗_アナウンス.prompt` → 人間版では `予約転送アナウンス.prompt` 等
- `時間外_アナウンス.prompt` → 人間版は `時間外アナウンス.prompt`
- `非通知_アナウンス.prompt` → 人間版は `非通知アナウンス.prompt`

### 3.4 人間版にのみ存在するキー（9個）

- `確認_問い合わせ内容.prompt` — 人間版命名規則
- `冒頭アナウンス.prompt`, `冒頭アナウンス2.prompt` — 時間帯別の冒頭TTS2種
- `時間外アナウンス.prompt`, `非通知アナウンス.prompt`
- `受付完了アナウンス.prompt`, `受付完了アナウンス2.prompt`
- `予約転送アナウンス.prompt`
- `終話アナウンス.prompt`

### 3.5 Re-confirmation プロンプトの扱い

人間版Property.mdに特徴的な記述:
```
## Re-confirmation node data モジュールの params.prompt に直接設定済み
### 確認_着信: 「…{電話番号}…」
### 確認_着信_アナウンス: 「…{電話番号}…」
```

Re-confirmationのプロンプトはProperty.mdではなくフローJSON内params.promptに直接記述済みであることをコメントで明示。VFBがRe-confirmationを生成しないため、この差分は確認のみ。

---

## 4. パターン分類集計

| カテゴリ | 件数 | 代表例 |
|---|---|---|
| **logic_gap** | 4 | ContextMatchRouter未生成(1)、Re-confirmation未生成(3)、冒頭チェーン順序誤り |
| **subflow_design** | 2 | サブフロー2本が完全未生成（氏名・電話番号） |
| **unnecessary** | 9 | save2db過剰(5)、saveCompletionFlag過剰(2)、Disconnect過剰(3)、saveContext2DB過剰(2) |
| **type_mismatch** | 2 | DTMF未使用（電話番号サブフロー内）|
| **naming_issue** | 12+ | TTS命名不統一、flowname形式誤り |
| **script_missing** | 9 | 業務ロジックScript（時刻判定・SMS・電話番号変換）を一切生成しない |
| **property_mismatch** | 12 | 命名規則の違いによるキー差分 |

---

## 5. 確認されたVFBパターン（3施設比較）

| パターンID | 帯広 | 長野 | ユアクリ | 状態 |
|---|---|---|---|---|
| VFB-001 ContextMatchRouter未生成 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-002 復唱ノード未生成 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-003 save2db過剰 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-004 Disconnect/CompletionFlag過剰 | ✓ | ✓(部分) | ✓ | **frequency=3** |
| VFB-005 DTMF未使用 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-006 Retry prompt_false空欄 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-007 Retry save2db未接続 | ✓ | ✗ | 要確認 | frequency=1 |
| VFB-008 office_id未設定 | ✓ | ✗ | ✗ | frequency=1 |
| VFB-009 TTS命名規則不統一 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-010 Retry prompt_true文言 | ✓ | ✓ | ✓ | **frequency=3** |
| VFB-011 サブフロー未生成 | ✗(帯広は別) | ✓ | ✓ | **frequency=2** |
| VFB-012 flowname形式誤り | ✗ | ✓ | ✓ | **frequency=2** |
| VFB-013 サブフロープロンプトをProperty.md直書き | ✗ | ✓ | ✓(部分) | frequency=2 |

---

## 6. 新規発見パターン

### VFB-014: 冒頭チェーン順序誤り（incoming-classifier が冒頭TTS より前）

**カテゴリ**: structural_error / **重要度**: CRITICAL

**内容**: VFBは冒頭チェーンで incoming-classifier を 冒頭TTS より前に配置する。正しい順序は 冒頭TTS → incoming-classifier。VFB版では非通知着信でも冒頭アナウンスが再生されない問題がある。

**観察内容**:
- 帯広: VFBは incoming-classifier を acceptance_times の前に配置（同様の問題）
- ユアクリ: wait → saveContextModel2DB → **incoming** → acceptance_times → 冒頭TTS
- 人間版: wait → saveContextModel2DB → **冒頭TTS** → incoming → acceptance_times

**修正方針**: 冒頭チェーンの正しい順序 = wait → saveContextModel2DB → 冒頭TTS → incoming-classifier → [acceptance_times]

### VFB-015: 業務ロジックScript（JavaScript）を生成しない

**カテゴリ**: logic_gap / **重要度**: WARNING

**内容**: VFBは業務ロジックを実装するScriptモジュール（JavaScript）を生成しない。人間版では以下のスクリプトを手書き実装している:
- **時刻判定スクリプト**: 日曜日・平日・土曜の受付時間帯別判定（acceptance_timesでは表現できない細かいロジック）
- **SMS送信スクリプト**: 受付完了時のSMS通知処理
- **電話番号変換スクリプト**: 国際番号形式・SSML形式への変換
- **リトライ制御スクリプト**: サブフロー内のリトライ回数管理

VFBは acceptance_times + saveContext2DB の組み合わせで時間外判定を行おうとするが、細かい時間帯別ロジックは実装できない。

**影響**: 業務要件に合わせた時間帯ロジック欠落、SMS通知なし

---

## 7. VFBへのフィードバック提案（優先度更新）

### 最優先（frequency=3確定）

1. **ContextMatchRouter生成** (VFB-001): 3施設全てで未生成確認
2. **復唱ノード生成** (VFB-002): 3施設全てで未生成確認
3. **save2db共有パターン** (VFB-003): 3施設全てで個別生成確認
4. **冒頭チェーン順序修正** (VFB-014新規): 帯広・ユアクリで確認。TTS → incoming の順に

### 優先（frequency=2以上）

5. **サブフロー本体生成** (VFB-011): 長野・ユアクリで確認
6. **flowname形式修正** (VFB-012): 長野・ユアクリで確認
7. **CompletionFlag/Disconnect集約** (VFB-004): 3施設で確認

### 中優先

8. **DTMF使用** (VFB-005): 3施設で確認
9. **Scriptモジュール生成** (VFB-015新規): ユアクリで確認（業務固有のため難易度高）
10. **TTS命名規則統一** (VFB-009): 3施設で確認

---

## 付録: VFB版の主要エラー

| コード | 件数 | 内容 |
|--------|------|------|
| FLOW-004 | 2 | Jump to Flow の flowname が正規形式でない |
| FLOW-005 | 2 | Jump to Flow の properties が空 |
| REACH-001 | 多数 | Jump先フローが存在しない（実動作不可） |
| STT-TYPE | 2 | 電話番号入力にDTMF未使用 |
| R-006 | 1 | Retry prompt_false空欄 |
| LAYOUT-001 | 要確認 | レイアウト未設定 |

---

*生成日: 2026-04-10*
*分析対象: VFB版 ユアCLお茶水$診療 vs 人間修正版 ユアCLお茶水$診療-Demo + 氏名 + 電話番号*
