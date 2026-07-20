# Skill: /gen-intent-spec — 質問ブロックの判定 spec を壁打ちで起草する

## いつ使う

設計書 YAML のある質問ステップ（用件確認・理由分類 等）に対し、
**Evidence→Event→Rule 形式の判定 spec**（intent_classifier_v2 用 DATA）と
テストケースを人間との壁打ちで起草するとき。

- ライン外（壁打ち）専用。パイプライン内で自動起動しない（keystone: ライン内 LLM ゼロ）
- 正本: `docs/governance/intent-engine-v2-design.md` / `script-authoring-standard.md` §2.5

## 起動方法

```
/gen-intent-spec {施設名} {フロー名} {ステップ名}
```

## Phase 0 — エンジン選定（v2 を使うべきか先に判定）

設計書から該当ブロックの TTS・choices を読み、**選定表**（design doc §0.5）で判定:

| 型 | engine |
|---|---|
| 複合 intent（文の組合せで意味が決まる） | intent_classifier_v2 ← このスキルの対象 |
| 単純 N 択 / yes,no / 日付 / FAQ / 自由文 | 認定済み部品（n_choice / yes_no_classifier / reservation_date_classifier / faq_matcher / free_text）→ **v2 を使わない**。ここで終了し部品を案内 |

## Phase 1 — Evidence 起草（壁打ち）

TTS の質問文と choices から:
1. **証拠（evidences）**: 発話に現れる素片。keywords（単語）と patterns（句）。
   否定され得るものは `negatable: true`
2. **同義語**: 実発話ゆれ（extract-yesno-synonyms の収集結果があれば取り込む）
3. ユーザーに提示し、施設固有語彙（診療科名・院内用語）を補ってもらう

## Phase 2 — Event / Rule 起草

- 複合意味は event に（例: reservation+cannot_visit → ReservationCannotVisit）
- rule は **evidence/event の集合**に対して書く（生テキスト参照は禁止）
- General rule には `none:` で Specific ケースを除外 or Specific rule を併記
  （specificity = 展開後の base 証拠数。Specific > General は自動）

## Phase 3 — テストケース起草（spec とセットで必須）

**各 intent につき最低 3 ケース**: ①直言（キーワードそのまま）②言い回し（句・複合文）
③否定形。加えて 拮抗→CLARIFY / 無関係→NO_RESULT / repeat→REPEAT を各 1。
期待値はユーザーが 1 行ずつ確認（ケースの出所を人間確定にする — 標準 §5-2）。

## Phase 4 — 機械検証（決定論・このスキル内で完結）

```bash
python3 tools/gen_intent_v2.py --spec {spec.json} --step {ステップ名} \
  --input-module 入力_{ステップ名} --context {save_to} -o /tmp/check.js
node --check /tmp/check.js
# ケースを modules/intent_classifier_v2/test_cases.json 形式で一時保存し
python3 modules/intent_classifier_v2/test_oracle.py
node modules/intent_classifier_v2/test_parity.js
```

全 PASS したら設計書ブロックに反映:

```yaml
- step: 用件確認
  type: intent
  engine: v2
  intent_spec:
    question_type: menu
    evidences: [...]
    events: [...]
    rules: [...]
  conditions:
    - {match: <intent>, next: <ルート>}
    - {match: CLARIFY, next: <聞き返し先>}   # 省略時 リトライTTS
```

## Phase 5 — 認定へ

- **P6 実機受入が完了するまで本番投入禁止**（oracle_gate fail-closed が機械的に担保）
- 受入後: certified_hashes.json 登録は人間ゲート（オーナー）

## 原則

- Rule は生テキストを読まない（Text → Evidence → Event → Intent → Output）
- 推測禁止: 判定不能=NO_RESULT / 拮抗=CLARIFY（聞き返し）
- ケースは人間確定 + 実発話由来を優先（自作自賛の遮断）
- 認定済み部品で足りる質問に v2 を使わない
