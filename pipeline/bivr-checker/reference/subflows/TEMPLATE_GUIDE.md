# サブフローテンプレート 使い方ガイド

> 最終更新: 2026-04-14

---

## テンプレート一覧

| ファイル | 内容 | モジュール数 | 状態 |
|---|---|---|---|
| `rag_search_standard.json` | RAG検索（問い合わせ受付→OpenAI要約→RAG→ループ応答） | 13 | ✅ 完成 |
| `phone_number_standard.json` | 電話番号聴取（DTMF→Phone Normalization→CMR→復唱→着信分岐） | 19 | ✅ 完成 |
| `patient_name_standard.json` | 氏名聴取（STT→OpenAIカタカナ変換→Re-confirmation→YES/NO） | 14 | ✅ 完成 |
| `patient_dob_standard.json` | 生年月日聴取（DTMF+STT→DOB Re-confirmation専用ノード） | 8 | ✅ 完成 |

---

## rag_search_standard.json の使い方

### 1. プレースホルダーを置換する

| プレースホルダー | 置換内容 | 例 |
|---|---|---|
| `{GROUP_NAME}` | 施設グループ名 | `帯広第一病院` |
| `{FLOW_DATE}` | フロー作成日付 | `20260414` |

### 2. RAGの質問テキストをカスタマイズする

`openAI_相談_問合せ` の `params.prompt` を施設に合わせて調整する。
基本的には標準テンプレートのままで動作するが、施設固有の情報（診療科名等）を
`# 施設固有コンテキスト` として追加すると精度が上がる。

### 3. 終了スクリプトを呼び出し元フローに合わせる

`script_質問無`・`script_FAQ失敗`・`script_リトライ失敗` の中の
`$runner.setModuleResult()` の戻り値を呼び出し元フローの分岐条件に合わせる。

```json
// 例: 呼び出し元が ^質問無$ で分岐している場合
$runner.setModuleResult('質問無');
```

### 4. Jump to Flow プロパティ設定

呼び出し元フローの `drjoy^Custom Module$Custom Jump to Flow` の `properties` に
以下を設定する（必要に応じてTTSプロンプトを上書き）:

```
相談_問合せ.prompt={tts_g:最後に何かお伝えしたいことがございましたら、お話しください。}
```

---

## 注意事項

- テンプレートの `save2db` モジュールは**全TTS/STT/Retryに必須**
- `script_*` モジュール名は `script_` プレフィックス必須（SCR-001）
- Jump先のフロー名は `{GROUP_NAME}$RAG検索_{FLOW_DATE}` 形式（FLOW-004）
- RAGモジュールの参照 `module` は直前の OpenAI モジュール名を指定

---

## 参照実装

- 帯広第一病院: `training_data/feedback/corrections/帯広第一病院/final_extracted/帯広第一病院_RAG検索.json`
- 長野県立木曽病院: `training_data/pair_03/` の人間版フロー
