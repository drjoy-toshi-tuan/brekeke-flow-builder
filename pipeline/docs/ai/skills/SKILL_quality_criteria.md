# SKILL_quality_criteria — 品質基準チェックリスト（共有スキル）

> **対象エージェント**: reviewer / fixer / tester  
> **読むタイミング**: 校閲・修正・テスト実行前に参照すること

---

## 品質基準（validator.py 検証項目）

1. **全モジュールに遷移先が定義されていること**（終話モジュール/切断モジュールは除く）
2. **全TTS/STTに save2db サブモジュールが接続されていること**
3. **STT の success が `^.+$` 1本受けであること**（個別パターン禁止）
4. **Retry の condition が `true`/`false`、label が `Retry`/`No more` であること**
5. **TTS の next label が `Next Module` であること**
6. **`stop_by_dtmf` が `"No"`/`"Yes"` であること**
7. **モジュール名に環境依存文字・括弧が含まれていないこと**
8. **リトライ回数が設定されていること**（デフォルト2回）
9. **DTMFモジュールの `params.prompt`（JSON内）に `{recstart}` が含まれていること**（DTMF-001。IVRプロパティではなくJSON内に直接記載必須）
10. **DTMFモジュールの `max_dtmf_length` が設定されていること**（DTMF-002）
11. **DTMFモジュールの `retry` が設定されていること**（DTMF-003）
12. **DTMFモジュールに `termdtmf`/`remove_term`/`stop_play_when_speech` が設定されていること**（DTMF-004）
13. **`saveContextModel2DB` の `params.fields` がJSON文字列（`"[...]"`）であること**（CTX-001〜004）
14. **各フィールド定義に `contextName`/`contextNameJp`/`displayType`/`rangeValues`/`editable`/`deletable`/`itemDefault` が揃っていること**（CTX-006）
15. **`displayType` が既定値のいずれかであること**（CTX-007）
16. **`rangeValues` 各要素に `id`/`order`/`value` が揃っていること**（CTX-008）
17. **OpenAIモジュールの `next` 分岐ラベルと `params.prompt` 内の出力仕様が完全一致していること**（PROMPT-001）
18. **OpenAIモジュールの `params.prompt` が空欄のまま残っていないこと**（PROMPT-003。個人情報サブフローはリファレンスからコピー済みのため対象外）
19. **全TTSモジュールに対応する `.prompt=` エントリがpropertiesファイルに存在すること**（P-010、CRITICAL。欠如するとTTS発話が全て無音になる）
20. **Custom Jump to Flowで遷移するサブフロータイプ別の必須TTSエントリが全てpropertiesに存在すること**（P-016、CRITICAL。テンプレート定義: `docs/specs/subflow_property_templates.json`）

---

## tester.py 品質基準（構造監査）

以下は `schemas/tester.py` が自動検証する項目。prompter実行後に実行される（サブフローをフラット化してから監査）。

21. **ContextMatchRouter に無一致(0)の受け皿が存在すること**（AUD-1、CRITICAL。`^0$`/`^.*$` いずれかで silent mis-route を防ぐ）
22. **@General$Script 分類器に catch-all（`^.*$`）が存在すること**（AUD-2、WARNING）
23. **全モジュールが終端（Disconnect/Transfer/Reject）へのパスを持つこと**（R-1、CRITICAL。dead-end/trap ゼロ）
24. **jump 先サブフロー参照がすべて解決できること**（R-2、CRITICAL。broken ref ゼロ）
25. **フラット化後のカバレッジが十分であること**（R-3、WARNING。未到達モジュールの確認）

---

> **OpenAI プロンプト品質ガイド（tester.py 自動検証対象外）**: OpenAI モジュールを使う場合は `docs/ai/openai_prompt_design_guide.md` の4本柱（# Role / # Context / NO_RESULT / インジェクション防御）に従うこと。tester.py は構造監査のみを担い、プロンプト内容は自動検証しない。
