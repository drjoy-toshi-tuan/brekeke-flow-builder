# Script 作成標準（Script Authoring Standard）

> **すべての判定 Script（@General$Script / modules/ 部品 / script_templates）が従う共通契約。**
> 個別スクリプト型の詳細は各 SKILL（用件/診療科/FAQ 等）が正本。本書は「型を問わず
> 破ってはならない不変条件」だけを定義する。ゲートとの対応を併記し、
> 「文書にしかないルール」を作らない（防ぐが勝ち）。
>
> 制定: 2026-07-16（本セッションの品質議論より）/ 関連: part-certification-spec.md

## 0. 大原則 — engine と spec の分離

| 層 | 内容 | 変更時 |
|---|---|---|
| **engine** | 判定ロジックの構造（正規化・判定順・出力契約） | ハッシュ対象。1文字でも改変 = 再受入（P6） |
| **spec (DATA)** | keywords / labels / 辞書 / 閾値 | ハッシュ対象。人間が壁打ちで確定 |
| **wiring** | 入力元モジュール名・保存先・next 配線 | ハッシュ対象外。scaffold が機械配線 |

新しい判定が必要なとき、まず問うのは「**既存 engine の spec 差し替えで済むか**」。
engine を新造するのは spec 差し替えで表現できない場合のみ（`/script-gen` skill・ライン外壁打ち）。

## 1. 入出力契約（I/O Contract）

- **入力**: `$runner.getModuleResult("<source>")` のみ。text 抽出は object/string 両対応の定型で行う
- **出力**: `$runner.setResult(<label>)`。label は **宣言済み閉集合**
  `options[].label ∪ {NO_RESULT, REPEAT}` 以外を返してはならない
  → 下流の next regex / CMR match と 1:1 対応（ゲート: S-1-5 / AUD-1 / AUD-2）
- **保存**: 業務値の保存は `$runner.setObject("<save_to>", value)`。
  setObject しない値を `<%変数%>` で参照させない（ゲート: V-2）
- **失敗の既定**: 判定できない入力は**必ず NO_RESULT**。推測で label を返さない（fail-safe）

## 2. 正規化パイプライン（固定順序）

```
trim → 改行/タブ除去 → 全角数字→半角 → 全角英字→半角 → カタカナ→ひらがな
     → 空白除去 → 記号除去（。、！？「」等）
```
- 順序を入れ替えない・省略しない（engine 共通部。scaffold `_build_intent_script_body` が正本）
- keywords は「正規化後の文字列」に対して書く（ひらがな化済み前提）

## 2.5 新規 engine の判定アーキテクチャ — Evidence→Event→Rule（2026-07-16〜）

> **Rule は生テキストを読まない。** `Text → Evidence → Event → Intent → Output`。
> 新規に作る判定 engine はこの構造に従う（正本: `intent-engine-v2-design.md`）。
> 単一キーワード直結（下記 §3 の v1 方式）は既存認定 engine の維持のみ許容し、
> 新規 engine では evidence 集合に対する rule で判定する。
> 否定は evidence の属性（`{name}_neg`）、競合は specificity（Specific > General）、
> 拮抗は CLARIFY（聞き返し・推測禁止）で解決する。

## 3. 判定順序（固定優先度）

```
1. DTMF 完全一致          rawText === "1" 等
2. 番号発話               「1ばん」「いちばん」+ SUFFIX（です/でお願いします…）
3. STRONG keywords        具体動詞。他 option と重複禁止
4. WEAK keywords          汎用語（その他/新規予約等）。STRONG の後
5. REPEAT（最弱）         何もマッチせず・正規化後15文字以内の repeat/wait 句のみ
6. NO_RESULT              上記すべて不成立
```
- **REPEAT は最弱**: 実内容を含む長い発話を REPEAT に食わせない
- STRONG keyword の **option 間重複は禁止**（重複したら WEAK に落とすか語彙を分割）
- label 自身は必ず自 option の keywords に含める（ゲート: S-1-4）
- DTMF「*」単独 → TTS 再生は **script でなく STT wiring**（`^[*＊]$` → repeat_star）で受ける

## 4. 実行環境ハードルール（ES5.1 / Nashorn）

| 禁止 | 代替 |
|---|---|
| `let` / `const` | `var` |
| アロー関数 | `function() {}` |
| `String.includes` / template literal | `indexOf` / 文字列連結 |
| regex lookbehind / named group | 使わない |

## 5. テスト契約 — 「自作自賛」を破る 3 点セット

1. **oracle.py**: Python で独立再実装（JS の翻訳でなく仕様からの再実装）→ 全ケース PASS
2. **ケースの出所**: AI の想像でなく、**人間が確定した spec 表（input → expected）**
   と**実通話ログの実発話**（regression corpus）から機械生成する
3. **P6 実機受入**: Brekeke 実機で oracle と同一判定を確認（Nashorn↔Python parity）

将来拡張（roadmap）: mutation testing（engine を機械改変 → oracle が FAIL しなければ
テストが弱い）で「テストのテスト」を機械化する。

## 6. Definition of Done（新規 script / spec 変更共通）

- [ ] REQUIREMENTS.md（入出力・分岐・エッジケース）
- [ ] oracle.py + test_oracle.py 全 PASS（ケース出所は §5-2 準拠）
- [ ] P6 実機受入 PASS → certified_hashes.json 登録（**人間ゲート**）
- [ ] 本標準 §1〜§4 準拠（機械ゲート: S-1/S-2/V-1/V-2/AUD/SCR-007 通過）
- [ ] 未実装スタブ（TODO_script / TODO_scaffold / ERROR:）が成果物に残っていない

## 対応ゲート一覧（本標準の機械化状況）

| 標準条項 | 機械ゲート | 状態 |
|---|---|---|
| §1 出力閉集合 ↔ 下流一致 | qa_validator S-1-5 / tester AUD-1・AUD-2 | 済 |
| §1 setObject / <%変数%> | qa_validator V-2 | 済 |
| §3 label ∈ keywords | qa_validator S-1-4 | 済 |
| §3 TTS 列挙 ↔ options | qa_validator S-1-1/2/3・S-2 | 済 |
| §0 engine/spec 改変検知 | oracle_gate + certified_hashes | 済 |
| §6 スタブ残存 | validator SCR-007（4 マーカー） | 済 |
| §5-2 実発話 corpus / §5 mutation | — | **未・roadmap** |
