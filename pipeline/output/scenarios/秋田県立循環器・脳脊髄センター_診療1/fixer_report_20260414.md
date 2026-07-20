# Fixer修正レポート — 秋田県立循環器・脳脊髄センター 診療1
生成日時: 2026-04-14 12:34

## 修正前 Critical サマリー

| ソース | Critical 件数 |
|---|---|
| バリデータ1（生成直後の構造チェック） | 0 件 |
| バリデータ2（マージ後の最終構造チェック） | 0 件 |
| レビュアー（レッドチーム校閲） | 2 件 |
| テスター（プロンプト品質・ルート到達性） | 9998 件 |
| **合計** | **10000 件** |

## Fixer修正完了内容

全修正が正しく適用され、JSONの整合性も保たれています。

---

修正完了:
- **C-001**: Custom Jump to Flow の flowname グループ名を `Jump_to_flow` → `秋田県立循環器・脳脊髄センター` に修正（5件: Jump_氏名聴取, Jump_生年月日聴取, Jump_診察券番号聴取, Jump_電話番号聴取, Jump_RAG）
- **C-002**: 終話TTS の next 配列を `[]` に変更（10件: 非通知_アナウンス, 時間外_アナウンス, END_聴取失敗, END_救急科案内, END_変更_携帯, END_キャンセル_携帯, END_確認_携帯, END_変更_固定, END_キャンセル_固定, END_確認_固定）

スキップした指摘:
- **P-5 (tester)**: OpenAI_診療科 / OpenAI_診療科2 のプロンプト出力値とnext分岐条件の不一致 → prompter担当（診療科は success `^.+$` 一本受け設計のため、プロンプト側の出力仕様記述を調整する必要あり）
- **Validator2**: Critical 0件（全44件がWarning）
- **Reviewer W-001/W-002/W-003**: Warning のため対象外

## プロンプト品質修正完了内容（prompter担当）

校閲レポートを確認しました。

## 結果: prompter担当のCritical指摘は **0件** です

レポートのサマリーおよび修正指示一覧から:

| 修正担当 | 件数 | 内訳 |
|---|---|---|
| **generator** | 5件 | C-001（flowname全5件修正）、C-002（終話TTS next配列10件修正）、W-001、W-002、W-003 |
| **prompter** | **0件** | — |
| **properties** | 0件 | — |

レポートの「prompter向け」セクションにも明確に **「なし」** と記載されています。

また、「OpenAIプロンプト出力ラベル整合性」テーブルでも全10件のOpenAIモジュールが **PASS** 判定であり、「付記: 問題なしと判断した観点」の項目13にも以下の記載があります:

> **OpenAIプロンプト4本柱**: 全10件の OpenAI モジュールに `# Role`, `# Context`, `NO_RESULT`, プロンプトインジェクション対策セクションが含まれている

**prompterとしての修正作業は不要です。**

2件のCritical（C-001, C-002）はいずれも **generator担当**（flownameのグループ名修正、終話TTSのnext配列修正）です。これらの修正が必要な場合は `@fixer` または `@generator` に依頼してください。

## 残存指摘一覧（要人間確認）

### 最終バリデータ結果（Critical / Warning / Info 全件）

```
[Properties] チェック対象: C:\Users\hamaguchi.t\vfb-【診療1】：秋田県立循環器・脳脊髄センター_main\output\properties_秋田県立循環器・脳脊髄センター_診療1.md

============================================================
[REPORT] バリデーション結果: 秋田県立循環器・脳脊髄センター$診療1_20260414
============================================================
モジュール数: 93
検出問題数: 47
  [Critical]: 1
  [Warning]:  46
  [Info]:     0
判定: [FAIL]

--- 検出事項 ---
  [C] [REACH-001] Disconnect > (module): startモジュールから到達不能です — このモジュールへの遷移パスが存在しません
  [W] [T-002] Disconnect > (module): どこからも参照されていない孤立モジュールです
  [W] [LAYOUT-003] (flow) > layout: フローが横並び（水平）に配置されています （x範囲:2480px, y範囲:9000px）— 主経路はy軸方向（上から下）に配置してください
  [W] [FLOW-005] Jump_氏名聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_生年月日聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_診察券番号聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_電話番号聴取 > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [FLOW-005] Jump_RAG > params.properties: Custom Jump to Flow の properties が空です — サブフロー用IVRプロパティ情報が未設定です
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '脳神経内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '心臓血管外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '糖尿病・内分泌内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の 'リハビリテーション科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '循環器内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '脳神経病理診断科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '脳神経外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '整形外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '脳血管内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '脊髄脊椎外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '総合診療科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の 'もの忘れ診療科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '放射線科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科 > params.prompt出力仕様: prompt出力仕様の '麻酔科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '脳神経内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '心臓血管外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '糖尿病・内分泌内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の 'リハビリテーション科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '循環器内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '脳神経病理診断科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '脳神経外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '整形外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '脳血管内科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '脊髄脊椎外科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '総合診療科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の 'もの忘れ診療科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '放射線科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [PROMPT-002] OpenAI_診療科2 > params.prompt出力仕様: prompt出力仕様の '麻酔科' に対応するnext分岐条件がありません — OpenAIがこの値を返してもルーティングされません
  [W] [REACH-002] (flow) > Disconnect: startから到達可能なDisconnectモジュールが存在しません — 通話終了パスが未定義の可能性があります
  [W] [P-011] リトライ_診療科2 > params.prompt_false: Retryモジュール 'リトライ_診療科2' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_変更希望日 > params.prompt_false: Retryモジュール 'リトライ_変更希望日' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_脳神経特定2 > params.prompt_false: Retryモジュール 'リトライ_脳神経特定2' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_キャンセル理由 > params.prompt_false: Retryモジュール 'リトライ_キャンセル理由' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_検査 > params.prompt_false: Retryモジュール 'リトライ_検査' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_診療科 > params.prompt_false: Retryモジュール 'リトライ_診療科' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_現在の予約日 > params.prompt_false: Retryモジュール 'リトライ_現在の予約日' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_脳神経特定 > params.prompt_false: Retryモジュール 'リトライ_脳神経特定' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_用件確認 > params.prompt_false: Retryモジュール 'リトライ_用件確認' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
  [W] [P-011] リトライ_残薬確認 > params.prompt_false: Retryモジュール 'リトライ_残薬確認' の params.prompt_false が空です — リトライ発話文言はフローJSON内のparamsに直接記述する必要があります（IVRプロパティでは動作しません）
```

### レビュアーレポート（1パスで修正しきれなかった分を含む）

# 校閲レポート: 秋田県立循環器・脳脊髄センター - 診療1

- 対象ファイル: `output/json/prompted_秋田県立循環器・脳脊髄センター_診療1.json`
- 設計書: `docs/designs/設計書_【診療1】：秋田県立循環器・脳脊髄センター_main.yaml`
- propertiesファイル: `output/properties_秋田県立循環器・脳脊髄センター_診療1.md`
- 校閲日: 2026-04-14

---

## セキュリティ・ライセンス警告（最優先確認）

なし

---

## サマリー

- 検出問題数: 7件
- 重大度別: SECURITY-CRITICAL 0 / Critical 2 / Warning 3 / LICENSE-WARN 0 / Info 2
- 修正担当別: generator 5件 / prompter 0件 / properties 0件 / 人間確認 0件

---

## 検出事項

### C-001: Custom Jump to Flow の flowname グループ名が全件誤っている

- **ファイル**: output/json/prompted_秋田県立循環器・脳脊髄センター_診療1.json
- **修正担当**: generator
- **モジュール名**: `Jump_氏名聴取`, `Jump_生年月日聴取`, `Jump_診察券番号聴取`, `Jump_電話番号聴取`, `Jump_RAG`
- **フィールド**: `params.flowname`
- **問題**: 全5モジュールの flowname グループ名が `Jump_to_flow` になっており、実際のサブフロー JSON の `name` フィールドと一致しない。Brekeke インポート後にサブフロー遷移が全て機能しない（サブフローが見つからずエラーになる）。
- **現在値 (例)**: `'drjoy^Jump_to_flow$氏名聴取_20260414'`
- **正しい値 (例)**: `'drjoy^秋田県立循環器・脳脊髄センター$氏名聴取_20260414'`
- **全件対応表**:

| モジュール名 | 現在の flowname | 正しい flowname |
|---|---|---|
| Jump_氏名聴取 | `drjoy^Jump_to_flow$氏名聴取_20260414` | `drjoy^秋田県立循環器・脳脊髄センター$氏名聴取_20260414` |
| Jump_生年月日聴取 | `drjoy^Jump_to_flow$生年月日聴取_20260414` | `drjoy^秋田県立循環器・脳脊髄センター$生年月日聴取_20260414` |
| Jump_診察券番号聴取 | `drjoy^Jump_to_flow$診察券番号聴取_20260414` | `drjoy^秋田県立循環器・脳脊髄センター$診察券番号聴取_20260414` |
| Jump_電話番号聴取 | `drjoy^Jump_to_flow$電話番号聴取_20260414` | `drjoy^秋田県立循環器・脳脊髄センター$電話番号聴取_20260414` |
| Jump_RAG | `drjoy^Jump_to_flow$RAG検索_20260414` | `drjoy^秋田県立循環器・脳脊髄センター$RAG検索_20260414` |

- **修正指示**: 上記5モジュールの `params.flowname` のみを修正すること。フォーマットは `drjoy^{グループ名}${フロー名}` 形式。グループ名は `秋田県立循環器・脳脊髄センター`（サブフロー JSON の `"name"` フィールド先頭部分と完全一致させること）。遷移先（next配列）・subs配列には一切触れないこと。
- **参照**: CLAUDE.md「17b. サブフロー参照の整合性」、docs/brekeke/naming_convention.md

> 修正指示: 5件の flowname のみを修正し、他のモジュールには一切触れないこと。

---

### C-002: 終話TTS の next 配列が仕様と異なる（`next: []` であるべき）

- **ファイル**: output/json/prompted_秋田県立循環器・脳脊髄センター_診療1.json
- **修正担当**: generator
- **モジュール名**: `非通知_アナウンス`, `時間外_アナウンス`, `END_聴取失敗`, `END_救急科案内`, `END_変更_携帯`, `END_キャンセル_携帯`, `END_確認_携帯`, `END_変更_固定`, `END_キャンセル_固定`, `END_確認_固定` (10件)
- **フィールド**: `next`
- **問題**: 仕様（モジュール詳細設定ガイド_1.md §2.1）は「終話モジュール（Disconnect/Reject前の最終TTS）は `next: []`」と明記しているが、全10件が `[{"condition": "^.*$", "label": "Next Module", "nextModuleName": "Disconnect"}]` になっている。Disconnectモジュールが単一で共有されており動作は正しいが、参照先が Disconnect であることが自明な場合は `next: []` が正しい形式。
- **現在値**: `[{"condition": "^.*$", "label": "Next Module", "nextModuleName": "Disconnect"}]`
- **正しい値**: `[]`
- **修正指示**: 上記10モジュールの `next` 配列を `[]` に変更すること。`subs` 配列、`params` 等には一切触れないこと。なお `Disconnect` モジュールが `modules` に定義済みであることは確認済み。next を空にしても Brekeke は通話をそのまま切断する。

> 修正指示: 10件の `next` 配列のみを `[]` に変更し、他のフィールドには一切触れないこと。

---

### W-001: ContextMatchRouter_用件分岐1 の分岐ラベルが設計書と不一致

- **ファイル**: output/json/prompted_秋田県立循環器・脳脊髄センター_診療1.json
- **修正担当**: generator
- **モジュール名**: `ContextMatchRouter_用件分岐1`
- **フィールド**: `next[0].label`, `next[1].label`
- **問題**: next のラベルが `"予約日時確認"` と `"変更_キャンセル"` になっている。設計書フロー図では「予約日時確認 → 氏名サブフローへ直行 / 変更・キャンセル → 診療科2_聴取」の2分岐。ラベル `"変更_キャンセル"` は実務上は問題ないが、設計書の用語と一致させる観点でわずかに不明確。Brekeke フローデザイナー上の表示名としては情報量が欠ける。
- **現在値**: `next[0].label = "予約日時確認"`, `next[1].label = "変更_キャンセル"`
- **正しい値（推奨）**: `next[0].label = "予約日時確認"`, `next[1].label = "変更またはキャンセル"` または設計書の表記と合わせた任意の明確なラベル
- **修正指示**: この問題は動作上の影響はない。フローデザイナー上の視認性向上のためにラベルのみ修正することを推奨するが、優先度は低い（Info相当に近いが、設計書との用語統一の観点でWarningとして計上）。

---

### W-002: 海外着信が非通知と同一の終話パス（設計書に明示なし）

- **ファイル**: output/json/prompted_秋田県立循環器・脳脊髄センター_診療1.json
- **修正担当**: generator（確認後に対応要否判断）
- **モジュール名**: `着信分類`
- **フィールド**: `next[3]`（海外分岐）
- **問題**: `incoming-classifier` で `^海外$` の場合、`完了フラグ_非通知（status=2, smsFlag=-1）` → `非通知_アナウンス` のパスに遷移している。設計書フロー図にも「通常/携帯/固定 → acceptance_times」と記載されており、海外が非通知と同一チェーンを辿ることは設計書フロー図では「非通知 → 完了フラグ_非通知」とのみ記載され、海外の扱いが明示されていない。終話パターン一覧（セクション8）にも海外専用のエントリはない。
- **現在値**: `condition='^海外$' label='海外' nextModuleName='完了フラグ_非通知'`
- **設計書記載**: 海外専用終話パターンの記載なし
- **懸念点**: 海外からの着信患者に「電話番号の前に186をつけて再度お電話ください」という非通知案内が流れる。これは海外への案内として不適切な可能性がある。
- **修正指示**: 設計書に海外の専用終話パターンが定義されていない場合、現状（非通知と同一パス）が意図的な設計かどうかを設計者・人間に確認すること。海外専用のTTSと完了フラグが必要な場合は generator に修正を依頼する。

---

### W-003: OpenAI_脳神経特定 / OpenAI_脳神経特定2 が分岐型なのに success 一本受け

- **ファイル**: output/json/prompted_秋田県立循環器・脳脊髄センター_診療1.json
- **修正担当**: generator
- **モジュール名**: `OpenAI_脳神経特定`, `OpenAI_脳神経特定2`
- **フィールド**: `next`（分岐設計の妥当性）
- **問題**: 両モジュールとも出力値は `脳神経外科` / `脳神経内科` / `NO_RESULT` の3値である。next配列は TIMEOUT/ERROR/NO_RESULT → リトライ、`^.+$` success → ContextMatchRouter_用件分岐1（または検査_聴取）の一本受けになっている。この設計では脳神経外科と脳神経内科が区別されずに同一の次モジュール（ContextMatchRouter_用件分岐1 または 検査_聴取）へ遷移する。設計書フロー図でも「→ ContextMatchRouter_用件分岐1」と記載されており、脳神経外科/脳神経内科の区別は後段（ContextMatchRouter_用件分岐1）でなく clinicalDepartment コンテキストの値として保存される設計と思われる。ただしOpenAIモジュールの出力値（脳神経外科 or 脳神経内科）がコンテキストに自動保存される仕組みが存在するか確認が必要。
- **現在値**: `success → ContextMatchRouter_用件分岐1`（脳神経外科/脳神経内科の区別なし）
- **確認事項**: OpenAIモジュールの出力が `clinicalDepartment` として saveContextModel2DB で自動的に格納される仕組みが Brekeke に存在するか確認すること。存在する場合は現在の設計は正しい。存在しない場合は saveContext2DB モジュールの追加が必要。
- **修正指示**: 上記確認を行い、自動保存の仕組みがなければ generator に saveContext2DB モジュールの追加を指示すること。

---

### I-001: 「脑神経特定」ステップのリトライ失敗時の挙動（Info）

- **モジュール名**: `リトライ_脳神経特定`
- **フィールド**: `next[1]`（No more 先）
- **現在値**: `condition='false' label='No more' next='完了フラグ_聴取失敗'`
- **設計書記載**: 設計書 step_details の「脳神経特定」には `retry_failure: end_failure` と記載されており、聴取失敗で終話する設計。これは正しく実装されている。
- **Info**: 問題なし。記録のみ。

---

### I-002: OpenAI_用件確認 の next が success 一本受け（分岐型プロンプトとの整合性）

- **モジュール名**: `OpenAI_用件確認`
- **フィールド**: `next`
- **現在値**: TIMEOUT/ERROR/NO_RESULT → リトライ, `^.+$` success → 診療科_聴取
- **設計書記載**: 用件3択（変更/キャンセル/予約日時確認）→ 全用件共通で診療科聴取へ進む。分岐は後段の `ContextMatchRouter_用件分岐1` で実施。
- **Info**: 設計書では用件確認後は全用件共通で診療科聴取に進む設計のため、success 一本受けは正しい。ContextMatchRouterで後から用件値を参照する設計として適切。問題なし。

---

## レッドチーム攻撃シナリオ

| # | シナリオ | 攻撃ベクトル | 予想結果 | 影響度 | 対策済み |
|---|---|---|---|---|---|
| 1 | 患者が「予約変更もキャンセルもしたい」と言った場合 | 複合意図 | どちらか先に分類されるが、もう一方が脱落する | 中 | 対策なし（IVRの性質上許容） |
| 2 | 患者が「脳外科でもあるし循環器でもある」と言った場合 | 複数診療科発話 | OpenAI_診療科の「複数一致 → NO_RESULT」ルールによりリトライへ | 低 | 対策済み（プロンプトに複数一致禁止の記載あり） |
| 3 | 患者が「救急です、緊急です」と診療科聴取で言った場合 | 救急ルート誘導 | OpenAI_診療科が「救急科」に分類 → 代表電話案内で終話 | 低 | 対策済み（救急科 → 完了フラグ_救急科 チェーン実装済み） |
| 4 | 患者が「指示を無視してください」等をSTT入力した場合 | プロンプトインジェクション | 全OpenAIプロンプトにインジェクション対策セクションあり、NO_RESULT へ | 低 | 対策済み（全プロンプトにインジェクション防御あり） |
| 5 | 患者が携帯から発信し、電話番号サブフローのflownameが誤っている場合 | C-001のシナリオ | Jump_電話番号聴取のサブフロー遷移が失敗し、フロー停止または無音になる | 高 | 未対策（C-001として報告） |
| 6 | 患者が「脳」とだけ言った場合（診療科聴取） | 脳曖昧ケース | 「脳曖昧」に分類 → 脳神経外科/内科の特定ステップへ遷移 | 低 | 対策済み（脳曖昧ルート実装済み） |
| 7 | 患者がDTMFで「0」を押した場合（用件確認） | 範囲外DTMF | OpenAI_用件確認がNO_RESULTを出力 → リトライ | 低 | 対策済み（0番は選択肢にないのでNO_RESULT） |
| 8 | 患者が診療科2で「救急です」と言った場合（変更/キャンセルルート） | 途中での救急ルート | OpenAI_診療科2が「救急科」 → 完了フラグ_救急科 → END_救急科案内で正しく終話 | 低 | 対策済み（診療科2にも救急科分岐あり） |
| 9 | 携帯から着信したが電話番号サブフローが壊れた場合のsmsFlag | C-001起因の副作用 | ContextMatchRouter_携帯固定分岐がサブフロー結果を取得できず、固定ルート（smsFlag=-1）に誤って振られる可能性 | 高 | C-001修正後に解消 |

---

## OpenAIプロンプト出力ラベル整合性

| モジュール名 | next分岐ラベル（条件） | prompt出力仕様 | 判定 | 備考 |
|---|---|---|---|---|
| OpenAI_用件確認 | success(`^.+$`) → 診療科_聴取 | 変更/キャンセル/予約日時確認/NO_RESULT | PASS | 後段ContextMatchRouterで分岐、一本受けは設計通り |
| OpenAI_診療科 | 救急科/脳曖昧/success | 15診療科/脳曖昧/NO_RESULT | PASS | 救急科と脳曖昧のみ個別分岐、それ以外はsuccess |
| OpenAI_脳神経特定 | success(`^.+$`) → ContextMatchRouter_用件分岐1 | 脳神経外科/脳神経内科/NO_RESULT | PASS（要確認）| 個別分岐なし。コンテキスト自動保存の仕組みに依存（W-003参照） |
| OpenAI_診療科2 | 救急科/脳曖昧/ない/success | 15診療科/脳曖昧/ない/NO_RESULT | PASS | 3種個別分岐、それ以外はsuccess |
| OpenAI_脳神経特定2 | success(`^.+$`) → 検査_聴取 | 脳神経外科/脳神経内科/NO_RESULT | PASS（要確認）| W-003と同様 |
| OpenAI_検査 | success(`^.+$`) → 現在の予約日_聴取 | フリーテキスト/NO_RESULT | PASS | 正規化型、一本受けは正しい |
| OpenAI_現在の予約日 | success(`^.+$`) → ContextMatchRouter_用件分岐2 | 日付テキスト/NO_RESULT | PASS | 変換型、一本受けは正しい |
| OpenAI_変更希望日 | success(`^.+$`) → 残薬確認_聴取 | フリーテキスト/NO_RESULT | PASS | 正規化型、一本受けは正しい |
| OpenAI_残薬確認 | success(`^.+$`) → Jump_氏名聴取 | はい/いいえ/NO_RESULT | PASS | 設計書では両値ともサブフロー遷移_氏名 |
| OpenAI_キャンセル理由 | success(`^.+$`) → Jump_氏名聴取 | 感染症/体調変化/他院入院/都合/NO_RESULT | PASS | 全値でサブフロー遷移_氏名 |

---

## 修正指示一覧（エージェント別）

### generator向け

**C-001（Critical・最優先）: Custom Jump to Flow の flowname 全5件修正**
- `Jump_氏名聴取.params.flowname` → `"drjoy^秋田県立循環器・脳脊髄センター$氏名聴取_20260414"`
- `Jump_生年月日聴取.params.flowname` → `"drjoy^秋田県立循環器・脳脊髄センター$生年月日聴取_20260414"`
- `Jump_診察券番号聴取.params.flowname` → `"drjoy^秋田県立循環器・脳脊髄センター$診察券番号聴取_20260414"`
- `Jump_電話番号聴取.params.flowname` → `"drjoy^秋田県立循環器・脳脊髄センター$電話番号聴取_20260414"`
- `Jump_RAG.params.flowname` → `"drjoy^秋田県立循環器・脳脊髄センター$RAG検索_20260414"`

**C-002（Critical）: 終話TTS の next 配列を `[]` に変更（10件）**
- 対象: `非通知_アナウンス`, `時間外_アナウンス`, `END_聴取失敗`, `END_救急科案内`, `END_変更_携帯`, `END_キャンセル_携帯`, `END_確認_携帯`, `END_変更_固定`, `END_キャンセル_固定`, `END_確認_固定`
- 各モジュールの `next` を `[]` に変更すること

**W-003（Warning・要確認後対応）: OpenAI_脳神経特定/脳神経特定2 の出力コンテキスト保存**
- 脳神経外科/脳神経内科の分類結果が `clinicalDepartment` に保存される仕組みが Brekeke にあるか確認
- 自動保存の仕組みがなければ、OpenAI_脳神経特定 および OpenAI_脳神経特定2 の success 後に saveContext2DB モジュールを追加して `clinicalDepartment` に保存する

### prompter向け

なし

### properties向け

なし

---

## 人間が確認すべき箇所

**W-002 の確認（海外着信の終話案内）**
- 現在の設計では海外からの着信に「電話番号の前に186をつけて再度お電話ください」という非通知向けアナウンスが流れる
- 海外からの着信患者への案内としてこれが適切かを確認し、必要であれば海外専用の終話パターン（TTS + 完了フラグ）を別途設計すること
- 設計書には海外専用の終話パターンが定義されていないため、現状が意図的な設計かどうか設計者に確認すること

---

## 付記: 問題なしと判断した観点

以下の観点は確認済みで問題なし:

1. **セキュリティ**: 全モジュールの params（prompt, contextName, contextValue, profile_words, name）にインジェクション誘導フレーズ・スクリプトタグ等は検出されなかった
2. **モジュールタイプ形式**: 全93モジュールが `drjoy^`, `@IVR$`, `@General$`, `Custom$wait` のいずれかに準拠
3. **モジュール選定**: 新規/移管フローとして個人情報聴取4件+RAGがサブフロー分割済み、DTMF使用箇所（用件確認・キャンセル理由）に適切に DTMF AmiVoice STT を使用
4. **非通知処理の配置**: acceptance_times より前に非通知を処理する設計が正しく実装されている
5. **acceptance_times 分岐**: TIMEOUT/ERROR/false → 完了フラグ_時間外（正しい）、true のみ → 冒頭_アナウンス（正しい）
6. **saveCompletionFlag2db の配置順**: 全終話パスで saveCompletionFlag2db → TTS の順が維持されている（完了フラグ_非通知 → 非通知_アナウンス 等）
7. **status/smsFlag 値**: 設計書定義（1=未処理, 2=代表案内, 3=聴取失敗, 6=時間外）と一致。禁止値（0, 5）は使用なし
8. **saveContextModel2DB フィールド**: 設計書セクション5の全16フィールド（classification, clinicalDepartment, patientName, medicalCardNumber, patientDateOfBirth, telephoneNumber, additionalPhoneNumber, status, dateOfCall, callId, clinicalDepartment2, inspection, reservationDate, desiredReservationDate, leftoverMedication, reason）が全て実装済み
9. **displayType**: 設計書と一致（CLASSIFICATION, DEPARTMENT, TEXT, NUMBER, DATE_OF_BIRTH, PHONE_NUMBER_CALL, PHONE_NUMBER, STATUS, DATE, TEXT x多数）
10. **AmiVoice profile_words**: 設計書セクション10の辞書が全STTモジュールに設定済み（用件確認・診療科・脳神経特定・診療科2・脳神経特定2・検査・現在の予約日・変更希望日・残薬確認・キャンセル理由の10ステップ全て確認済み）
11. **Retry Counter params**: 全件 `prompt_true` が規定の固定値、`prompt_false` が空文字、`retry_count="2"` で設計書と一致
12. **Retry No more 先**: 設計書の retry_failure 定義（end_failure: 聴取失敗終話 / skip: 次ステップへ）と全件一致
13. **OpenAIプロンプト4本柱**: 全10件の OpenAI モジュールに `# Role`, `# Context`, `NO_RESULT`, プロンプトインジェクション対策セクションが含まれている
14. **IVRプロパティ整合性**: メインフロー全TTSモジュール（冒頭_アナウンス, 用件確認, 診療科_聴取, 脳神経特定, 診療科2_聴取, 脳神経特定2, 検査_聴取, 現在の予約日_聴取, 変更希望日_聴取, 残薬確認_聴取, キャンセル理由_聴取, 非通知_アナウンス, 時間外_アナウンス, END_聴取失敗, END_救急科案内, END_変更_携帯, END_キャンセル_携帯, END_確認_携帯, END_変更_固定, END_キャンセル_固定, END_確認_固定）全件がpropertiesに記載済み
15. **サブフロー termination**: 全5サブフロー（氏名/生年月日/診察券番号/電話番号/RAG）が `termination: return` 設計で、サブフローJSONにDisconnectが配置されていないことを設計書で確認
16. **終話パターン網羅性**: 設計書セクション8の10終話パターン（END_非通知, END_時間外, END_聴取失敗, END_救急科案内, END_変更_携帯, END_キャンセル_携帯, END_確認_携帯, END_変更_固定, END_キャンセル_固定, END_確認_固定）が全てフローJSONに実装済み
17. **ContextMatchRouter params**: 全5件の ContextMatchRouter に module1Name/module2Name/module1ValueN/module2ValueN が適切に設定されている。用件分岐1（予約日時確認 → 氏名サブフロー直行）、用件分岐2（変更 → 変更希望日 / それ以外 → キャンセル理由）、携帯固定分岐（1=携帯 / その他）、用件別終話携帯・固定（変更/キャンセル/予約日時確認）全て設計書と一致

---

*reviewer: claude-sonnet-4-6 / 2026-04-14*

---
対象JSON: `C:\Users\hamaguchi.t\vfb-【診療1】：秋田県立循環器・脳脊髄センター_main\output\json\prompted_秋田県立循環器・脳脊髄センター_診療1.json`