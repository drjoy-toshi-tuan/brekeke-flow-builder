# Intent Engine v2 設計書 — Evidence→Event→Rule 推論パイプライン（LLM 近似・決定論）

> **目的**: rule-based 判定を「キーワードが有れば intent」から、LLM の推論過程を
> 決定論的に模倣する多層パイプラインへ引き上げる。狭いドメイン（IVR/AI電話）では
> これで LLM 同等精度＋完全再現性＋監査可能な理由列を得る。
>
> **大原則（2026-07-16 確定）: Rule は生テキストを読まない。**
> `Text → Evidence → Event → Intent → Output` — 最終判定は常に「証拠の集合」に
> 対して行い、単一キーワードでは行わない。QA はどの層で誤ったか（証拠検出 /
> イベント合成 / ルール選択）を trace（reason 配列）で特定できる。
>
> 状態: **実装済み（2026-07-16・`modules/intent_classifier_v2/`）**。
> oracle 40/40 PASS・JS parity 40/40 PASS。**P6 実機受入は未 = 本番投入禁止**
> （oracle_gate fail-closed）。v1（scaffold `_build_intent_script_body`）は併存。
> v2 は設計書ブロックの `engine: v2` 宣言で opt-in。

## 0. パイプライン全体像

```
入力（STT text / DTMF）
  → 1. Normalize        trim/全半角/かな化/記号除去 + FILLER除去（えっと等）
  → 2. Detect Evidence  spec.evidences: keywords/patterns → 証拠フラグ。
                        否定スコープ(12字)内 → "{name}_neg" として成立（否定=証拠の属性）
                        同義語トークン（_YES_/_NO_）も証拠として合流
  → 3. Build Events     spec.events: 証拠の組合せ → 上位イベント（fixpoint 反復・入れ子可）
                        例: reservation+cannot_visit → ReservationCannotVisit
                            +future_date → WantAnotherDate
  → 4. Apply Rules      spec.rules: {intent, all:[証拠|イベント], none:[...]}
  → 5. Resolve Conflict specificity = all を base 証拠まで展開した集合サイズ。
                        Specific > General。異 intent が margin 未満で拮抗 → CLARIFY
  → 6. Output           setResult = 1 テキスト（intents ∪ {CLARIFY, REPEAT, NO_RESULT}）
                        setObject = trace（evidences/events/rule/reason/confidence）
```

代表例:「7月26日に予約してるんだけど、都合がつかないので、来月で大丈夫ですか」
→ Evidence: reservation, cannot_visit, future_date
→ Event: ReservationCannotVisit → WantAnotherDate
→ Rule: 変更 (spec=3) / 予約 rule は none:[cannot_visit] でブロック
→ Output: **変更**（単キーワード方式なら 予約 に誤爆していた）

## 0.5 エンジン選定表 — v2 は「複雑 intent」専用（認定済み部品を再発明しない）

| 質問の型 | 例 | 使う engine |
|---|---|---|
| 複合 intent（文の組合せで意味が決まる） | ご用件をお話しください | **intent_classifier_v2** |
| 単純 N 択 | 企業か個人か / コース選択 | n_choice / checkup_course_classifier（認定済み） |
| yes/no | 7月18日以降のご予約ですか | yes_no_classifier v4（認定済み）/ v2 preset yes_no（P6 後） |
| 日付 | 現在の予約日 | reservation_date_classifier（認定済み） |
| 自由テキスト | キャンセル理由（原文保存） | free_text |
| FAQ | お問い合わせ内容 | faq_matcher（認定済み） |

spec の起草は `/gen-intent-spec` skill（壁打ち・ライン外）、compile は
`tools/gen_intent_v2.py`（決定論）、scaffold 統合は設計書ブロックの
`engine: v2`（`intent_spec:` inline か options[] からの auto-lower）。

## 1. 各層の仕様（日本語 IVR 実例つき）

> 注: 本節の L1〜L10 は起案時の層番号。実装では §0 の 6 ステップに統合された
> （L2 同義語=Evidence の一部 / L6 否定=Evidence の `_neg` 属性 / L7 優先度=Resolve の
> specificity / L9 confidence=Resolve のマージン）。個別の意味論は下記の通り有効。

### L1 正規化 — v1 §2 をそのまま継承（変更なし）

### L2 同義語写像（SYNONYM_MAP・spec DATA）
```
「ええ」「はい」「うん」「そうです」「お願いします」「大丈夫です」 → _YES_
「いいえ」「いや」「結構です」「やめて」「いらない」「なしで」   → _NO_
「オペレーター」「担当者」「人間」「窓口」「係の人」             → _OPERATOR_
```
- 写像は**正準トークン**（`_YES_` 等）へ。以降の層はトークンに対して判定
- spec DATA（施設別に拡張可）。実通話ログ由来の類義語を継続追加
  （`extract-yesno-synonyms` skill の収集結果が供給源）

### L3 パターン照合（PATTERNS・spec DATA）
単語でなく**句**で判定する:
```
「_OPERATOR_ (に|へ)?(つないで|かわって|お願い)」 → TRANSFER_OPERATOR
「(人|ひと)と (話|はな)したい」                    → TRANSFER_OPERATOR
```
- v1 の keywords 単語一致は L3 の退化形として残す（互換）

### L4 エンティティ抽出（EXTRACTORS・engine 内蔵）
```
「1992年生まれです」   → entities: {birth_year: 1992}
「らいしゅうの月曜」   → entities: {relative_date: "next_monday"}
```
- 既存認定部品（dob_normalizer / reservation_date_classifier / phone_normalizer）の
  抽出ロジックを**呼び出さず再実装もしない** — v2 は「抽出対象がある」ことだけ
  マークし、実抽出は既存認定部品へ配線（部品の再利用・二重実装禁止）

### L5 変数分離
```
「予約を変更したい、来週火曜に」
→ intent: CHANGE / variables: {desired_date_raw: "来週火曜"}
```
- intent 判定と変数は独立して返す（v1 は intent しか返せない）

### L6 否定処理（NEGATION — v1 に無い最重要層）
否定マーカー（engine 固定）: `ない/しない/じゃない/ではない/いらない/不要/結構/やめ/なしで/しなくて`
- **スコープ**: マッチした intent キーワードの直後〜文末 12 文字以内に否定マーカー
  → その intent マッチを**反転タグ** `NEG(intent)` に変える
```
「キャンセルはしないでください」 → NEG(キャンセル)
「変更しなくていいです」         → NEG(変更)
「もう電話しないで」             → NEG(_CALL_)
```

### L7 優先度解決
```
優先度: NEG(X) > X（STRONG） > X（WEAK） > REPEAT
```
- 「もうキャンセルしなくていい」= `不要`+`キャンセル` 共起
  → NEG(キャンセル) が勝ち → intent は KEEP_CURRENT（キャンセルしない）
- NEG のみで肯定 intent が無い場合 → `NO_ACTION` 系 label（spec で定義）

### L8 文脈適用（QUESTION_TYPE・生成時に焼き込む spec DATA）
engine パラメータ `QUESTION_TYPE ∈ {yes_no, menu, open}`:
- `yes_no`: `_YES_`/`_NO_` トークンを YES/NO label へ直結（「はい」単独が意味を持つ）
- `menu`  : `_YES_` 単独は AMBIGUOUS（「はい」だけでは選べない → CLARIFY）
- `open`  : トークンでなく L3/L4 の結果を優先
- 文脈 = 直前 TTS の質問タイプ。scaffold がブロック生成時に静的に埋める
  （実行時の動的文脈参照は不要 — 各ブロックは自分の質問を知っている）

### L9 confidence とマージン
```
score(intent) = Σ(マッチ層の重み)   L3句=3 / STRONG語=2 / WEAK語=1 / 同義トークン=2
confidence    = top1 / (top1 + top2 + ε)
```
- `top1 - top2 < CLARIFY_MARGIN`（既定 1）→ **CLARIFY**（聞き返し）
- 閾値・重みは spec DATA（施設別調整可・ハッシュ対象）

### L10 出力契約
- **setResult**: ルーティング label（閉集合）
  `labels ∪ {CLARIFY, NO_RESULT, REPEAT}` — CLARIFY が新規（聞き返し TTS へ配線）
- **setObject("intent_result_<step>", {...})**: 監査用構造化結果（LLM 風出力）
```json
{
  "intent": "TRANSFER_OPERATOR",
  "confidence": 0.94,
  "entities": {},
  "variables": {},
  "negation": false,
  "reason": ["L3: _OPERATOR_につないで", "L2: 窓口→_OPERATOR_"],
  "need_clarification": false
}
```
- `reason` 配列 = どの層の何がマッチしたか。**P7 突合・INC 調査がログだけで完結**する
- fallback は v1 同様 NO_RESULT（推測禁止）。CLARIFY と NO_RESULT は区別する
  （CLARIFY=候補が拮抗 / NO_RESULT=候補なし）

## 2. Brekeke 制約への適合

- ES5.1/Nashorn のみ（標準 §4）。JSON 出力は `JSON.stringify`（Nashorn 対応）
- setResult は文字列 1 値 → ルーティングは label、リッチ結果は setObject に分離
- CLARIFY の受け皿: scaffold が「聞き返し TTS →同 STT」を自動配線
  （REPEAT と同型 wiring・engine 変更なしで追加可能）

## 3. 認定パス（自作自賛の遮断込み）

1. engine 骨格を `tools/new_part_skeleton.py` で `modules/intent_classifier_v2/` に起票
2. **oracle.py**: 仕様からの独立再実装（本書 §1 が仕様正本）
3. **テストケース出所**（標準 §5-2）:
   - 人間確定の spec 表（否定・拮抗・文脈の各層 × 施設語彙）
   - 実通話ログ実発話 corpus（extract-yesno-synonyms 経路）
4. mutation testing: L6 否定スコープ・L7 優先度・L9 マージンを機械改変し
   oracle FAIL を確認（テストの強度検証）
5. P6 実機受入 → certified_hashes 登録（人間ゲート）

## 4. 移行方針

- v1 は現行シナリオで継続（再受入コストゼロ）
- 設計書 YAML で `engine: intent_v2` を宣言したブロックのみ v2
- 新規施設のうち「否定・聞き返しの品質要求が高いフロー」から段階導入
- v2 が P6 通過するまで本番投入禁止（fail-closed は oracle_gate が既に担保）
