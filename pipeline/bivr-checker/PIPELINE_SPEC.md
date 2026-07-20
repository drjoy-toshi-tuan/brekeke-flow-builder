# bivr-checker パイプライン仕様書

本文書は仕上げパイプラインが「毎回必ず同じ基準で実行する」ことを保証するための定義一覧です。

---

## パイプライン全体像（Stage 0〜8）

```
入力: input/{施設名}/*.bivr + properties_*.md + *.pdf/html
  ↓
Stage 0: EXTRACT        — .bivr → フローJSON展開
Stage 1: STRUCTURAL_FIX — 構造修正（learned_patterns + VFB既知パターン）
Stage 2: PROFILE_WORDS  — profile_words生成（@pw-generator準拠）
Stage 3: PROMPT_APPLY   — OpenAIプロンプト テンプレート適用（prompt_templates.json）
Stage 4: PROPERTY_FIX   — Property.md整合性修正
Stage 5: VERIFY         — 品質検証（80点以上で合格）
Stage 6: BUILD          — .bivrビルド（対象施設フローのみ）
Stage 7: CALL_TEST      — 模擬通話テスト（10パターン全PASS必須）
Stage 8: REPORT         — 修正レポート生成
  ↓
出力: output/{施設名}/{施設名}_fixed.bivr
```

---

## 各Stageの実行コマンドと品質ゲート

### Stage 0: EXTRACT
```bash
python scripts/extract_bivr.py input/{施設名}/*.bivr
```
- ゲート: JSONファイルが1つ以上生成されること

### Stage 1: STRUCTURAL_FIX
```bash
python scripts/structural_fixer.py output/{施設名}/*.json
```
**チェック定義一覧:**

| # | チェック | 参照定義 |
|---|---|---|
| 1 | Brekeke必須フィールド8つ | CLAUDE.md Section 7a「モジュール共通必須フィールド」 |
| 2 | matchingmethod = int型（"1"不可、1必須） | CLAUDE.md Section 7a |
| 3 | キー順序: layout→next→subs→name→description→matchingmethod→type→params | CLAUDE.md Section 7a |
| 4 | next/subsスロット数がモジュールタイプごとの固定値と一致 | CLAUDE.md Section 7a「スロット数テーブル」 |
| 5 | 空スロットは {"condition":"","label":"","nextModuleName":""} で埋める | CLAUDE.md Section 7a |
| 6 | ContextMatchRouter paramsキーは交互配置 | CLAUDE.md Section 7a |
| 7 | 丸数字・環境依存文字をモジュール名から除去 | CLAUDE.md N-001 |
| 8 | termdtmf="#", stop_play_when_speech="Yes", retry≥"2" | CLAUDE.md Section 4 DTMF規則 |
| 9 | detection_flag: 全STT/DTMFモジュールで `"デフォルト"` を明示設定（`"検出しない"` は禁止、空欄も禁止） | CLAUDE.md Section 7 AmiVoice設定 |
| 10 | incoming-classifier: フロー内1つのみ | CLAUDE.md 原則24 |
| 11 | サブフローに script_結果返却_xxx 必須 | CLAUDE.md SCR-002 |
| 12 | saveContextModel2DB fields: デフォルト12フィールド準拠。特に callId は `itemDefault=false`, `displayType=NUMBER`, `editable=true` であること（VFBが `itemDefault=true`, `displayType=TEXT`, `editable=false` を誤設定するため必ず修正） | CLAUDE.md Section 7「標準フィールド」 |
| 13 | リトライfalse: STT直後モジュールに具体的分岐あり→無限ループ（false=true遷移先）、分岐なし→次へ進む（false=catch-all遷移先） | CLAUDE.md Section 4 prompt_false体系 |
| 14 | リトライfalse「分岐あり」の判定対象: OpenAI/ContextMatchRouter/Script全て。STT直後が何であれ、具体的条件（^TIMEOUT$/^ERROR$/^NO_RESULT$/^.+$/^.*$/空 以外）があれば分岐ありと判定 | verify_fixes.py check_retry_false_consistency |
| 15 | リトライfalse「次へ進む」の遷移先: STT直後モジュールのwildcard(^.+$/^.*$)遷移先。TTS名ではなくSTT入力モジュール名になる場合がある | verify_fixes.py find_module_after_stt |
| 17 | レイアウト: モジュール重なり禁止（同一座標に複数モジュール配置しない。最低x:200px/y:150px間隔） | CLAUDE.md Section 7b |
| 18 | レイアウト: 終話モジュール（完了フラグ→END TTS→Disconnect）はフロー最下部に配置（非通知・時間外は例外可） | CLAUDE.md Section 7b |
| 16 | Retry→TTS日本語接続チェック: prompt_true末尾「再度、」+ 遷移先TTS先頭が不自然な場合、方法A(prompt_true修正)または方法B(STT直接指定)で修正 | CLAUDE.md Section 4 |
| 19 | 冒頭アナウンス存在チェック: 冒頭チェーン（wait→saveContextModel2DB→incoming-classifier→acceptance_times）の先にTTSモジュール（冒頭アナウンス）が必須 | CLAUDE.md FLOW-007 |

### Stage 2: PROFILE_WORDS — ⚠️ @pw-generator 必須
```
【必須手順】以下を順に実行する。ハードコード辞書での代用は禁止。

Step 2a: python scripts/pw_analyzer.py output/{施設名}/fixed/flows/*.json
  → 分析結果JSONが出力される

Step 2b: @pw-generator に分析結果JSONとフローJSONを渡す
  → エージェントが教師データ水準の辞書を生成（100-200語/モジュール）

Step 2c: verify で A-1〜A-5 が全て OK/WARN であることを確認
  → A-1(空)が FAIL なら Step 2b をやり直す
```

> **⛔ 禁止事項**: fix_xxx_stage2.py 等のアドホックスクリプトでハードコード辞書を貼り付けることは禁止。
> 必ず @pw-generator エージェントを呼び出し、教師データ水準（フィラーTOP6/語尾TOP8/頭切れ/100-200語）の辞書を生成すること。

**品質ゲート（verify_fixes.py が自動検証）:**

| # | チェック | 合格基準 | 不合格時 |
|---|---|---|---|
| A-1 | 空モジュール | 0件 | **BLOCKER — Stage 3 に進めない** |
| A-2 | 語数範囲 100-200語（phone/freetext除く） | 80%以上 | @pw-generator 再実行 |
| A-3 | フィラーTOP6含有（freetext除く） | 80%以上 | @pw-generator 再実行 |
| A-4 | 頭切れパターン含有 | 50%以上 | @pw-generator 再実行 |
| A-5 | 「まー」不在 | 0件 | 手動削除 |
| A-6 | 半角数字のみ | 全角0件 | 手動修正 |

### Stage 3: PROMPT_APPLY — ⚠️ @prompt-enhancer 併用必須
```
【必須手順】以下を順に実行する。

Step 3a: python scripts/apply_prompt_templates.py output/{施設名}/fixed/flows/*.json --properties input/{施設名}/properties_*.md
  → テンプレート自動適用

Step 3b: @prompt-enhancer に全フローJSONを渡す
  → 施設固有情報の反映・7セクション品質確認
  → 元プロンプトの施設固有ロジック（特殊分岐等）がテンプレートで上書きされていないか確認

Step 3c: verify で B-1〜B-8 が全て OK であることを確認
```

> **⛔ 禁止事項**: apply_prompt_templates.py の実行だけで Stage 3 完了としない。
> 必ず @prompt-enhancer でテンプレート適用結果を検証し、施設固有情報の欠落がないことを確認すること。

**品質ゲート（verify_fixes.py が自動検証）:**

| # | チェック | 参照定義 |
|---|---|---|
| 1 | 入力種別の自動判定: classification/yes_no/date/normalization/freetext | prompt_templates.json |
| 2 | 7セクション必須: Role/Context/出力仕様/セキュリティ/判定アルゴリズム/Few-Shot/重要原則 | prompt-enhancer.md |
| 3 | 判定アルゴリズム: STEP1入力正規化→STEP2 DTMF→STEP3語句一致→STEP4フォールバック | prompt_templates.json |
| 4 | Few-Shot 15-25例 | prompt-enhancer.md |
| 5 | セキュリティ: プロンプトインジェクション対策定型文 | prompt_templates.json |
| 6 | NO_RESULT: 全プロンプトに含む | CLAUDE.md Section 8 |
| 7 | params.module: 既存値保持（出力元STT/OpenAIモジュール名） | CLAUDE.md 原則14 |
| 8 | params.promptTTS: 空のまま | CLAUDE.md Section 8 |
| 9 | 施設固有ロジック保持: テンプレート適用で元プロンプトの特殊分岐が消えていないこと | @prompt-enhancer 確認 |

### Stage 4: PROPERTY_FIX
```bash
python scripts/property_fixer.py output/{施設名}/ input/{施設名}/properties_*.md
```
**チェック定義一覧:**

| # | チェック | 参照定義 |
|---|---|---|
| 1 | Property.mdキー名とモジュール名の完全一致（メインフロー＋サブフロー両方を照合対象とする。メインフローのProperty.mdはサブフローにも反映される） | CLAUDE.md PROP-001/CROSS-001 |
| 2 | amivoice設定群（uri/language/engine等）存在 | CLAUDE.md Section 5 |
| 3 | API URL群存在 | CLAUDE.md Section 5 |

### Stage 5: VERIFY
```bash
python scripts/verify_fixes.py output/{施設名}/*.json
```
**品質スコア（100点満点、80点以上で合格）:**

| カテゴリ | 配点 | チェック項目 |
|---|---|---|
| A. profile_words | 40点 | 空0件(10) + 語数範囲(10) + フィラー含有(10) + 頭落ち(5) + まー不在(5) |
| B. OpenAIプロンプト | 40点 | Role(4) + Context(4) + 出力仕様(4) + セキュリティ(4) + 判定アルゴリズム+STEP(8) + Few-Shot15例+(8) + 重要原則(4) + NO_RESULT(4) |
| C. 構造 | 20点 | CRITICAL 0件(8) + prompt_false非空(4) + TTS label(4) + **リトライfalse整合性(4)** |

### Stage 6: BUILD
```bash
python scripts/build_bivr.py output/{施設名}/*.json -o output/{施設名}/{施設名}_fixed.bivr
```
**チェック定義一覧:**

| # | チェック | 参照定義 |
|---|---|---|
| 1 | 対象施設のフローのみ含む（他施設フロー混入禁止） | 本文書 |
| 2 | 古いフロー（日付なし版等の重複）を除外 | 本文書 |
| 3 | メインフロー + Jump to Flow参照先サブフローのみ | 本文書 |
| 4 | ZIP形式: flows/@flow_{URLエンコード名}.txt | CLAUDE.md Section 4 |
| 5 | JSON: minified 1行 | CLAUDE.md Section 4 |

### Stage 7: CALL_TEST
```bash
python scripts/test_calls.py output/{施設名}/*.json
```
**チェック定義一覧:**

| # | チェック | 参照定義 |
|---|---|---|
| 1 | 10パターン自動生成（正常パス + リトライ上限 + CMR補完） | test_calls.py |
| 2 | 全パスがstart→Disconnect到達（終話まで完走） | 本文書 |
| 3 | サブフロー横断追跡 | test_calls.py |
| 4 | exit code 0 = 全PASS必須 | 本文書 |

### Stage 8: REPORT
```bash
python scripts/report_generator.py output/{施設名}/
```

---

## レイアウト定義（CLAUDE.md Section 7b）

| 項目 | 基準値 |
|---|---|
| 冒頭チェーン | 冒頭(0,0) → CTX設定(0,240) → 着信分類(0,480) → 受付時間(0,720) → 冒頭TTS(0,960) |
| ステップ内 TTS基準 | TTS(0,0) → STT(0,+220) → OpenAI(0,+460) → Retry(-280,+460) → save2db(-280,+220) |
| ステップ間隔 | Δy = 800（TTS→次TTS） |
| Re-confirmation含む | Δy = 1200以上 |
| y_range | ≥ modules × 100 |
| LAYOUT-003判定 | x_range > 2000px AND y_range < modules×100px → 警告 |

---

## 絶対遵守事項（全Stage共通）

1. **matchingmethod は int型**（文字列 "1" は不可）
2. **キー順序**: layout → next → subs → name → description → matchingmethod → type → params
3. **detection_flag = "デフォルト"**: 全STT/DTMFモジュールで明示設定。空欄・"検出しない"は禁止（structural_fixer.pyで自動修正）
4. **incoming-classifier**: フロー内1つのみ
5. **SMS判定**: ContextMatchRouter で phonetype 返り値を参照
6. **プロンプト**: prompt_templates.json のテンプレートを使用
7. **profile_words**: 「まー」使用禁止
8. **bivrビルド**: 対象施設フローのみ（他施設混入禁止）
9. **模擬通話テスト**: 10パターン全PASS必須（Stage 7 をスキップしない）
10. **saveContextModel2DB**: デフォルト12フィールド準拠（赤字部分のみ変更可）
11. **リトライfalse**: STT直後モジュールに具体的分岐あり→無限ループ（false=true遷移先, prompt_false空）、分岐なし→次へ進む（false=catch-all遷移先, prompt_false設定）。例外なし
12. **Retry→TTS日本語接続**: prompt_true末尾と遷移先TTS先頭を連結して自然な日本語になるか必ず確認。不自然な場合は方法A(prompt_true修正)または方法B(STT直接指定)で修正
13. **ルール反映の徹底**: 新しいルール・FBが確定した時点で、CLAUDE.md / PIPELINE_SPEC.md / verify_fixes.py の3箇所に必ず反映する。定義だけして検証に組み込まないことを禁止する
14. **detection_flag = `"デフォルト"`**: 全STT/DTMFモジュールで明示設定。`"検出しない"` は禁止、空欄も禁止
15. **profile_words の数字は半角のみ**: 全角数字（１２３）使用禁止。半角（123）に統一
16. **レイアウト: モジュール重なり禁止**: 同一座標に複数配置しない（最低x:200px/y:150px間隔）
17. **レイアウト: 終話はフロー最下部**: 完了フラグ→END TTS→Disconnectはy座標最大付近に配置（非通知・時間外は例外可）
18. **Stage 3（テンプレート適用）をスキップしない**: 全OpenAIプロンプトにprompt_templates.jsonのテンプレートを適用。場当たり的なプロンプト生成は禁止
19. **⛔ Stage 2 は @pw-generator 必須**: profile_words の生成にはハードコード辞書を使わず、必ず `@pw-generator` エージェントを呼び出すこと。教師データ水準（フィラーTOP6/語尾TOP8/頭切れ/100-200語）を満たさない辞書はBLOCKER
20. **⛔ Stage 3 は @prompt-enhancer 併用必須**: `apply_prompt_templates.py` 実行後、必ず `@prompt-enhancer` で施設固有情報の保持・7セクション品質を確認。テンプレート適用だけで完了としない
21. **self_contained サブフロー**: サブフロー内で終話する設計（Disconnect配置あり）の場合、`desc` フィールドに `termination:self_contained` を設定すること。未設定だと SF-TERM-001 CRITICAL が発生する
