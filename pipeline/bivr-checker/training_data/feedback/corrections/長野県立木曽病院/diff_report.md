# 差分分析レポート: 長野県立木曽病院

## サマリー
- **VFB生成**: 152モジュール（1フロー `長野県立木曽病院$診療_20260410`）
- **人間修正**: 290モジュール（5フロー: 診療97 + 個人情報39 + RAG検索11 + 診療科聴取_170 + 診療科聴取_273）
- **構造的一致率**: 約30%（メインフローの骨格は対応するが、サブフロー4本が完全に欠落）
- **主な差分カテゴリ**: サブフロー未生成、ContextMatchRouter未生成、Re-confirmation未生成、RAGモジュール未生成、save2db過剰、DTMF未使用、Property.mdプロンプト管理方式の違い

---

## 1. 構造差分

### 1.1 フロー構成

| 観点 | VFB生成版 | 人間修正版 |
|------|-----------|------------|
| フロー数 | 1（サブフロー4本を参照するが内容なし） | 5（メイン＋個人情報＋RAG検索＋診療科聴取×2） |
| メインフロー名 | `長野県立木曽病院$診療_20260410` | `長野県立木曽病院$診療` |
| 個人情報サブフロー | Jump_個人情報（参照のみ・内容なし） | `長野県立木曽病院$個人情報木曽病院_1`（39モジュール） |
| 診療科聴取サブフロー_1 | Jump_診療科聴取_1（参照のみ・内容なし） | `長野県立木曽病院$診療科②聴取_1`（70モジュール） |
| 診療科聴取サブフロー_2 | （直接参照なし） | `長野県立木曽病院$診療科②聴取_2_1`（73モジュール） |
| 電話番号サブフロー | Jump_電話番号確認（参照のみ・内容なし） | 個人情報サブフロー内にインライン配置 |
| RAGサブフロー | Jump_RAG検索（参照のみ・内容なし） | `長野県立木曽病院$木曽病院RAG検索_1`（11モジュール） |

**最大の差分**: VFBはサブフロー参照（Jump to Flow）を4個生成するが、サブフロー本体を .bivr に含めない。人間版は4本のサブフローを独立フローとして実装している。

### 1.2 冒頭チェーン

| VFB生成版 | 人間修正版 |
|-----------|------------|
| `冒頭(wait)` → `コンテキスト設定` → `acceptance_times` → `冒頭_アナウンス` → `着信分類(incoming)` | `冒頭待ち時間(wait)` → `コンテキスト設定` → `冒頭(TTS)` → `非通知分岐(incoming)` |

**主な違い**:
- VFBは acceptance_times を冒頭チェーンに含む（人間版はデモ環境判断で残している）
- VFBは incoming-classifier を acceptance_times の後に配置。人間版は冒頭TTS の後
- フロー名に日付あり（`診療_20260410`）vs 日付なし（`診療`）

### 1.3 モジュール数比較（タイプ別）

| モジュールタイプ | VFB (1フロー) | 人間 (5フロー計) | 差分 | 備考 |
|-----------------|------|------|------|------|
| save2db | 54 | **20** | **-34** | 帯広と同様に個別→共有へ集約 |
| TTS | 24 | 58 | +34 | サブフロー4本分追加 |
| OpenAI | 15 | 47 | +32 | サブフロー内OpenAI追加 |
| Retry Counter | 15 | 50 | +35 | サブフロー内Retry追加 |
| STT (AmiVoice) | 13 | 36 | +23 | サブフロー内STT追加 |
| DTMF STT Input | 2 | **14** | +12 | 人間版は数字入力全てDTMF対応 |
| Re-confirmation | **0** | **14** | **+14** | VFBは復唱ノードを一切生成しない |
| ContextMatchRouter | **0** | **5** | **+5** | VFBは未使用。人間版の設計の中核 |
| RAG | **0** | **1** | **+1** | RAGサブフロー内（VFBはRAGモジュール未生成） |
| saveCompletionFlag | 8 | 10 | +2 | サブフロー内で増加 |
| Disconnect | 8 | 9 | +1 | ほぼ同等 |
| Script | 1 | 9 | +8 | サブフロー内スクリプト多数追加 |
| Custom Jump to Flow | 4 | 4 | 0 | 参照数は同等（中身は別物） |

### 1.4 サブフロー分割の判断基準（人間版）

人間修正版のサブフロー構成:
1. **個人情報木曽病院_1**: 氏名・生年月日・電話番号の個人情報一括収集。DTMF 5個、Re-confirmation 2個を含む複雑なフロー
2. **診療科②聴取_1 / _2**: 診療科聴取を2種類に分割（耳鼻科特別ルートへの対応）。Re-confirmation 4個 × 2、ContextMatchRouter 1個含む
3. **木曽病院RAG検索_1**: RAG検索＋OpenAI判定のシンプルな独立フロー（11モジュール）

VFB版はこれら4本をJump to Flow参照のみ生成し、内容を実装していない。

---

## 2. モジュール差分

### 2.1 VFBが生成しなかった重要モジュール（人間版にのみ存在）

#### サブフロー本体（最大の欠落）
- `長野県立木曽病院$個人情報木曽病院_1` フロー全体（39モジュール）
- `長野県立木曽病院$診療科②聴取_1` フロー全体（70モジュール）
- `長野県立木曽病院$診療科②聴取_2_1` フロー全体（73モジュール）
- `長野県立木曽病院$木曽病院RAG検索_1` フロー全体（11モジュール）

VFBはこれらへの参照（Jump to Flow）は生成するが、実装は一切ない。

#### ContextMatchRouter（5個）— 帯広と同様に全欠落

| 配置フロー | 用途（推定） |
|---|---|
| 診療メイン（4個） | 終話パターン分岐、診療科ルーティング等 |
| 診療科②聴取_2_1（1個） | 診療科選択結果による分岐 |

具体的な分岐内容（finalから確認）:
- `^1$` → 案内アナウンスA / `^2$` → 案内アナウンスB
- `^1$` → 診療科聴取_2A / `^2$` → 診療科聴取_2B / `^.+$` → 診療科聴取_1
- `^1$` → 予約変更 / `^2$` → キャンセル / `^3$` → 予約内容確認
- `^1$` / `^2$` → 対象外終話 / `^.+$` → 個人情報聴取

#### Re-confirmation node data（14個）— 帯広と同様に全欠落

| 配置フロー | 個数 |
|---|---|
| 診療メイン | 4個 |
| 個人情報木曽病院_1 | 2個 |
| 診療科②聴取_1 | 4個 |
| 診療科②聴取_2_1 | 4個 |

#### RAGモジュール（1個）

VFBはRAG検索サブフローへの参照（Jump_RAG検索）は生成するが、RAGモジュール本体を生成しない。
人間版は `木曽病院RAG検索_1` フロー内に `drjoy^External Integration$RAG` モジュールを配置。

### 2.2 VFB版にのみ存在するモジュール（人間版で削除・統合）

#### save2db（約34個削減）
VFB版: 全TTS/STT/Retryに個別save2db（TTS:24 + Retry:15 + STT:13 + DTMF:2 = 54個）
人間版: サブフロー横断で共有save2dbに集約（合計20個）

#### saveCompletionFlag / Disconnect の過剰生成（メインフロー内）
VFB版: saveCompletionFlag 8個（終話パスごとに個別生成）、Disconnect 8個
人間版: ContextMatchRouterで集約し、saveCompletionFlag 5個・Disconnect 4個に整理

### 2.3 両方にあるが内容が異なるモジュール

#### STTモジュールtype変更（大幅）

VFB版ではDTMF使用が2個のみ。人間版は数字入力項目全てにDTMFを使用:
- 生年月日 → DTMF（VFBはAmiVoice STTのみ）
- 用件番号選択 → DTMF
- 電話番号 → DTMF（個人情報サブフロー内）
- 診療科番号選択 → DTMF（診療科聴取サブフロー内）

#### Jump to Flow の flowname形式

| 観点 | VFB版 | 人間版 |
|------|-------|--------|
| flowname | `drjoy^Jump_to_flow$診療科聴取_1_20260410` | `drjoy^長野県立木曽病院$診療科②聴取_1` |
| properties | 空（FLOW-005違反） | TTSプロンプトをproperties経由で渡す |

VFBは flowname のグループ名に施設名を使わず `Jump_to_flow` とし、日付を付ける。
人間版は `グループ名$フロー名` の正規形式を使用し、サブフロー内TTSのプロンプトを properties で渡す。

#### Retry Counter prompt_true

| 観点 | VFB版 | 人間版 |
|------|-------|--------|
| prompt_true | `{tts_g:恐れ入りますがご回答が確認できませんでした。今一度、}` | `{tts_g:申し訳ございません。うまく聞き取りが出来ませんでした。再度、}` |
| prompt_false | `""` (空) | 状況に応じて終話分岐または同一TTSへ戻す |

---

## 3. Property.md差分

### 3.1 行数比較

| 観点 | VFB版 | 人間版 |
|------|-------|--------|
| 総行数 | 141行 | 49行 |
| TTSプロンプトキー数 | 32（VFBのみ） | 25（人間版のみ） |

### 3.2 プロンプト管理方式の違い

VFB版はサブフロー内のTTSプロンプトをメインフローのProperty.mdに列挙する。
人間版はサブフロー内TTSのプロンプトを **Jump to Flow の properties** に記述して渡す。

結果として VFB版 Property.md は141行に膨れ上がり、人間版は49行に収まる。

### 3.3 VFB版にのみ存在するキー（32個）

サブフロー内のTTSプロンプトがメインのProperty.mdに混在している主な例:
- `案内_アナウンス.prompt`, `案内_診療科.prompt` — 診療科選択案内
- `終話_時間外.prompt`, `終話_代表.prompt` — 終話系
- `RAG検索_案内.prompt`, `RAG検索ループ.prompt` — RAGサブフロー用

### 3.4 人間版にのみ存在するキー（25個）

- 人間版命名規則に対応したTTSキー群（`確認_診療科`, `終話_非通知` 等）
- ContextMatchRouter・復唱に対応するTTSキー群
- サブフロー固有キーはJump to Flow properties経由で管理されるためProperty.mdには不在

### 3.5 共通キーで値が異なるもの

| キー | VFB版 | 人間版 |
|------|-------|--------|
| `office_id` | 両方に存在・同値 | — |
| `amivoice.*` | デフォルト値 | デフォルト値（今回は一致） |
| URL設定群 | 存在 | 存在 |

※ 今回は office_id・amivoice設定は両方に存在しており VFB-008 は非確認。

---

## 4. パターン分類集計

| カテゴリ | 件数 | 代表例 |
|---|---|---|
| **subflow_design** | 4 | サブフロー4本が完全未生成（Jump参照のみ） |
| **unnecessary** | 34+ | save2db過剰（54→20）、saveCompletionFlag/Disconnect過剰 |
| **logic_gap** | 20+ | ContextMatchRouter 0→5、Re-confirmation 0→14、RAGモジュール未生成 |
| **type_mismatch** | 12 | DTMF未使用（2→14）|
| **naming_issue** | 多数 | flowname形式誤り、TTS命名不統一 |
| **property_mismatch** | 多数 | サブフロープロンプトをProperty.mdに直書き（Jump to Flow properties未使用） |
| **prompt_quality** | 15 | Retry prompt_true文言、prompt_false空欄 |

---

## 5. 確認されたVFBパターン（帯広との比較）

| パターンID | 帯広 | 長野 | 状態 |
|---|---|---|---|
| VFB-001 ContextMatchRouter未生成 | ✓ | ✓ | **frequency=2** |
| VFB-002 復唱ノード未生成 | ✓ | ✓ | **frequency=2** |
| VFB-003 save2db過剰 | ✓ | ✓ | **frequency=2** |
| VFB-004 Disconnect/saveCompletionFlag過剰 | ✓ | ✓（部分） | **frequency=2** |
| VFB-005 DTMF未使用 | ✓ | ✓ | **frequency=2** |
| VFB-006 Retry prompt_false空欄 | ✓ | ✓ | **frequency=2** |
| VFB-007 Retry save2db未接続 | ✓（帯広のみ） | ✗（接続済み） | frequency=1（変動あり） |
| VFB-008 office_id未設定 | ✓（帯広のみ） | ✗（設定済み） | frequency=1（変動あり） |
| VFB-009 TTS命名規則不統一 | ✓ | ✓ | **frequency=2** |
| VFB-010 Retry prompt_true文言 | ✓ | ✓ | **frequency=2** |

---

## 6. 新規発見パターン

### VFB-011: サブフロー本体を生成しない

**カテゴリ**: subflow_design / **重要度**: CRITICAL

**内容**: VFBはメインフロー内にサブフローへのJump to Flow参照を生成するが、サブフロー本体（フロー内容）を .bivr に含めない。参照先フローが存在しないため実動作不可。

**観察内容（長野）**:
- Jump_個人情報 → `drjoy^Jump_to_flow$個人情報聴取_20260410`（フローなし）
- Jump_診療科聴取_1 → `drjoy^Jump_to_flow$診療科聴取_1_20260410`（フローなし）
- Jump_電話番号確認 → `drjoy^Jump_to_flow$電話番号確認_20260410`（フローなし）
- Jump_RAG検索 → `drjoy^Jump_to_flow$RAG検索_20260410`（フローなし）

**修正方針**: Jump to Flow のflownameに対応する実装フローを別途生成・追加する。

### VFB-012: Jump to Flow の flowname 形式誤り

**カテゴリ**: naming_issue / **重要度**: CRITICAL

**内容**: VFBが生成するJump to FlowのflownameがBrekeke正規形式（`グループ名$フロー名`）ではなく、`drjoy^Jump_to_flow${フロー名}_{日付}` という独自形式になっている。また properties が空欄でサブフローへのTTSプロンプト受け渡しができない。

**修正方針**: flowname を `drjoy^{グループ名}${フロー名}` 形式に変更。TTSプロンプトは properties 経由で渡す。

### VFB-013: サブフローTTSプロンプトをProperty.mdに直書き

**カテゴリ**: property_mismatch / **重要度**: WARNING

**内容**: VFBはサブフロー内のTTSプロンプトをメインフローのProperty.mdに直接列挙する。人間版はJump to Flowの `properties` フィールドを使ってサブフロー呼び出し時にプロンプトを渡す設計にしている。

**結果**: VFB版Property.mdは141行に肥大化（人間版は49行）。

**修正方針**: サブフロー内のTTSプロンプトは Property.md ではなく Jump to Flow の properties に記述する。

---

## 7. VFBへのフィードバック提案

### 最優先: サブフロー本体の生成

**問題**: VFBがサブフロー参照のみ生成し、中身を生成しない。
**提案**: Jump to Flowを生成する際は必ず対応するサブフローの内容も.bivrに含める。少なくとも個人情報サブフロー（氏名・生年月日・電話番号）はテンプレートとして固定化すべき。

### 最優先: ContextMatchRouterの生成（VFB-001 継続）

帯広と同様。コンテキスト値に基づく分岐には必ずContextMatchRouterを使用する。

### 最優先: 復唱ノードの生成（VFB-002 継続）

帯広と同様。生年月日・用件・電話番号・診療科番号の後に復唱確認ステップを追加。

### 優先: Jump to Flow の flowname・properties 修正（VFB-012 新規）

- flowname を `drjoy^{グループ名}${フロー名}` 形式に
- サブフローのTTSプロンプトを properties 経由で渡すテンプレートを整備

### 中優先: DTMFの適切な使用（VFB-005 継続）

数字入力（診療科番号・生年月日・電話番号）にはDTMF AmiVoice STT Inputを使用する。

---

## 付録: VFB版の主要エラー（CLAUDE.mdバリデーター基準）

| コード | 件数 | 内容 |
|--------|------|------|
| FLOW-004 | 4 | Jump to Flow の flowname が正規形式でない |
| FLOW-005 | 4 | Jump to Flow の properties が空 |
| REACH-001 | 多数 | Jump to Flowのflowname先フローが存在しない（実動作不可） |
| SB-001 | 0 | ※今回はRetry save2db接続済み（VFB-007非確認） |
| R-006 | 15 | Retry prompt_false空欄 |
| STT-TYPE | 12 | 数字入力にDTMF未使用 |

---

*生成日: 2026-04-10*
*分析対象: VFB版 長野県立木曽病院$診療_20260410 vs 人間修正版 長野県立木曽病院$診療 + 個人情報木曽病院_1 + 木曽病院RAG検索_1 + 診療科②聴取_1 + 診療科②聴取_2_1*
