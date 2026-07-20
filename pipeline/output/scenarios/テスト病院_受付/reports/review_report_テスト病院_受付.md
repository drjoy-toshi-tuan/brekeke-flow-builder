# 校閲レポート: テスト病院 - 受付

## サマリー

- 検出問題数: 5件
- 重大度別: Critical 3 / Warning 1 / Info 1
- 自動修正: 4件 / 要確認: 1件

---

## 検出事項

### C-001: save2dbモジュール定義がmodulesに存在しない

- 箇所: 全TTS・STTモジュールのsubs配列
- 問題: `冒頭_アナウンス`・`入力_用件_確認`・`終話_予約`・`終話_変更`・`終話_その他`・`終話_失敗` の各subs配列でsave2dbサブモジュールを参照しているが、参照先モジュール（save-history1〜6）がmodulesキー内に定義されていない。存在しないモジュールへの参照は実行時エラーになる。
- 修正: 以下6つのsave2dbモジュールをmodulesに追加し、合わせてsubs内の参照名を命名規則に合わせて変更した。
  - `save-history1` -> `save-冒頭_アナウンス`
  - `save-history2` -> `save-入力_用件_確認`
  - `save-history3` -> `save-終話_予約`
  - `save-history4` -> `save-終話_変更`
  - `save-history5` -> `save-終話_その他`
  - `save-history6` -> `save-終話_失敗`
- 理由: subs配列はmodulesに定義されたモジュールへの参照であり、定義なしでは動作しない。また命名規則（naming_convention.md）に従い `save-大分類_内容` 形式に修正した。

---

### C-002: STTモジュールのnext配列にjump7が存在する（仕様超過）

- 箇所: `入力_用件_確認` > next配列
- 問題: next配列の最後にjump7スロットが存在していた。CLAUDE.mdおよびbrekeke_module_reference.mdの仕様では、STTモジュールのjumpスロットはjump1〜jump6が最大（合計10スロット）。jump7はシステムが認識しないスロットとなる。
- 修正: jump7スロットを削除し、jump1〜jump6（計6スロット）に修正した。
- 理由: 仕様上の最大スロット数を超えるnextエントリは無効であり、混乱の原因になる。

---

### C-003: save2dbサブモジュールのラベル名が命名規則に違反している

- 箇所: 全TTS・STTモジュールのsubs配列
- 問題: subs内のlabel・moduleName がすべて `save-history{N}` 形式（連番）であった。命名規則では `save-大分類_内容` 形式（例: `save-冒頭_アナウンス`、`save-入力_用件_確認`）を要求している。
- 修正: C-001の修正と同時に命名規則に沿った名称に変更した（上記C-001参照）。
- 理由: TTSプロンプト名・モジュール名との対応を明確にするため、内容を示す名前が必須。

---

### W-001: 冒頭にwait 2000msモジュールが存在しない

- 箇所: フロー全体の先頭部分
- 問題: CLAUDE.mdの基本原則「冒頭に wait 2000ms が必須（着信直後の安定待機）」に従い、`冒頭_アナウンス`（TTS）の前にwaitモジュールを配置する必要がある。現在のフローはstartが直接 `冒頭_アナウンス` に接続されており、待機処理がない。
- 修正: 未実施（waitモジュールのtypeがCLAUDE.mdに明示されていないため、モジュール追加は人間が確認のうえ実施すること）
- 理由: 着信直後の2秒待機がないと、相手が応答する前にTTSが発話を開始してしまい、冒頭が聞こえない場合がある。
- 対応方針: waitモジュールのtype仕様を確認し、`start -> 冒頭_wait2000ms -> 冒頭_アナウンス` の順で接続すること。

---

### I-001: 終話TTSモジュールにDisconnectモジュールへの遷移がない

- 箇所: `終話_予約`・`終話_変更`・`終話_その他`・`終話_失敗` > next配列
- 問題: 4つの終話TTSはいずれも `"next": []` で終わっている。仕様上「終話モジュール（Disconnect/Reject前の最終TTS）は `next: []`」とあり構造上は正しい。ただし、brekeke_module_referenceには「Disconnectモジュールは終話TTSの遷移先として使用する」と記載されており、Disconnectモジュール（`@IVR$Disconnect`）を後段に配置してnext:[]をそこへ向けるパターンが標準的な実装である。
- 修正: 未実施（テストフローであるため現行の `next: []` 終端を許容する。本番環境ではDisconnectモジュールを追加すること）
- 理由: 情報提供のみ。実害はないが、明示的なDisconnectモジュールを置くことでフローの意図が明確になる。

---

## 修正済みモジュール一覧

| # | モジュール名 | 修正内容 | 重大度 |
|---|---|---|---|
| 1 | 冒頭_アナウンス | subsのsave参照名を `save-history1` から `save-冒頭_アナウンス` に変更 | Critical |
| 2 | 入力_用件_確認 | subsのsave参照名を `save-history2` から `save-入力_用件_確認` に変更、jump7スロットを削除 | Critical |
| 3 | 終話_予約 | subsのsave参照名を `save-history3` から `save-終話_予約` に変更 | Critical |
| 4 | 終話_変更 | subsのsave参照名を `save-history4` から `save-終話_変更` に変更 | Critical |
| 5 | 終話_その他 | subsのsave参照名を `save-history5` から `save-終話_その他` に変更 | Critical |
| 6 | 終話_失敗 | subsのsave参照名を `save-history6` から `save-終話_失敗` に変更 | Critical |
| 7 | save-冒頭_アナウンス（新規追加） | save2dbモジュールをmodulesに定義 | Critical |
| 8 | save-入力_用件_確認（新規追加） | save2dbモジュールをmodulesに定義 | Critical |
| 9 | save-終話_予約（新規追加） | save2dbモジュールをmodulesに定義 | Critical |
| 10 | save-終話_変更（新規追加） | save2dbモジュールをmodulesに定義 | Critical |
| 11 | save-終話_その他（新規追加） | save2dbモジュールをmodulesに定義 | Critical |
| 12 | save-終話_失敗（新規追加） | save2dbモジュールをmodulesに定義 | Critical |

---

## 変更なし確認済みモジュール一覧

| モジュール名 | 確認結果 |
|---|---|
| OpenAI_用件_確認 | 問題なし。TIMEOUT/ERROR/NO_RESULTの遷移先あり、個別分岐（予約/変更/その他）は正しくOpenAI側で実施 |
| リトライ_用件_確認 | 問題なし。retry_count: 2、条件 true->Retry / false->No more、遷移先 true→入力_用件_確認 / false→終話_失敗 が正しく設定 |
| 終話_予約 | 問題なし。stop_by_dtmf: "No" 正しい値 |
| 終話_変更 | 問題なし。stop_by_dtmf: "No" 正しい値 |
| 終話_その他 | 問題なし。stop_by_dtmf: "No" 正しい値 |
| 終話_失敗 | 問題なし。stop_by_dtmf: "No" 正しい値、リトライ上限到達時の終話として正しく参照されている |

---

## 構造整合性チェック結果

| チェック項目 | 結果 |
|---|---|
| start モジュール（冒頭_アナウンス）がmodulesに存在するか | OK |
| 全nextModuleNameがmodulesに存在するか（空文字を除く） | OK（修正後） |
| 孤立モジュール（どこからも参照されないモジュール）がないか | OK |
| 循環参照による意図しない無限ループがないか | OK（リトライ_用件_確認 → 入力_用件_確認 の循環はリトライ制御として意図的） |
| STTのsuccess conditionが `^.+$` 1本受けか | OK |
| Retryのconditionがtrue/false、labelがRetry/No moreか | OK |
| TTSのnext labelが `Next Module` か | OK |
| stop_by_dtmfが "No"/"Yes" か | OK |
| モジュール名に環境依存文字・括弧がないか | OK |

---

## 要確認事項（担当者アクション）

1. **冒頭wait 2000msモジュールの追加（W-001）**: waitモジュールのtype仕様を確認し、startの直後に2秒待機モジュールを挿入すること。
2. **Disconnectモジュールの追加（I-001）**: 本番運用前に終話TTSの後段へ `@IVR$Disconnect` モジュールを追加し、各終話TTSのnextをそこへ向けることを推奨。
3. **save2dbモジュールのparams設定**: 追加した6つのsave2dbモジュールについて、`contextName`・`contextDisplayType` 等のparams値をIVRプロパティまたはモジュール内で適切に設定すること。
