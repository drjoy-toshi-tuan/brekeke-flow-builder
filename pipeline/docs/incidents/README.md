# docs/incidents — 事故・不具合台帳

> 方針: **エラーは1回だけ。2回目は無い。**（session-kaizen skill 参照）

各事故は 1 ファイル `{YYMMDD}_{短い名前}.md`、ID は `INC-{YYMMDD}-{連番}`。
対策は必ず「着地階層」を明記する:

| 階層 | 内容 | 強さ |
|---|---|---|
| ① 機械ゲート | validator ルール / verify ツール / auto_fixer | 人が忘れても機械が防ぐ |
| ② データ | 辞書 / テンプレート / 部品 spec | 機械が使う |
| ③ Skill | SKILL.md の手順・禁止事項 | Claude が毎回読む |
| ④ 文書 | CLAUDE.md / ガイド | 参考情報（最弱） |

**①に着地できない場合は理由を明記する。** 対策コード側にも INC-ID を逆参照で書く。
