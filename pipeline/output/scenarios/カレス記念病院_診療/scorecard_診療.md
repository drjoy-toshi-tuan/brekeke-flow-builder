# シナリオ採点カード — C:\Users\dong.nguyen\gen_flow\output\scenarios\カレス記念病院_診療

> 4 層責任モデルの内側ループ採点。**層を 1 点に潰さない**＝STT(M0) は品質未測定。
> サブフロー: **全展開 (フラット採点)**。

| 層 | コンポーネント | ゲート | 状態 | 主指標 |
|---|---|---|---|---|
| 1 | 誘導(TTS文言) | M2 | PASS | CRITICAL 0 / WARN 3 |
| 2 | 文字起こし(STT辞書) | M0 | UNMEASURED | stt付与 0/8 / 辞書節 有 (品質は稼働KPI) |
| 3 | 正規化(Script/entity) | M2/M0 | INFO | det率 0.8571 / 認定 4 / 成績表有 4 / OpenAI残 0 |
| 4 | 分岐(CMR/script) | M2 | PASS | coverage 100.0% / CRITICAL 0 / subflow jump 0(展開済) |

**出荷ゲート (M2 層のみ判定)**: PASS
  ※ 第3 det率は KPI、第2 STT は M0 のため出荷ゲートには含めない (Goodhart 回避)。

## 第1 誘導(TTS文言) — PASS
- 盲点: 音声品質 (声質・抑揚) は測れない＝第1の『音』は M0 (proxy 無し)・別途 KPI
- 盲点: qa_validator のルール網羅範囲外の文言品質は不可視

## 第2 文字起こし(STT辞書) — UNMEASURED
- 盲点: 誤認識率・一発取得率・低信頼/NO_RESULT 計数は本採点の対象外＝稼働KPIを見よ
- 盲点: 辞書の語彙被覆の十分性は静的には判定不能

## 第3 正規化(Script/entity) — INFO
- 盲点: .bivr の実 script ハッシュ照合 (engine/spec) は oracle_gate/p6_gate の管轄＝本採点は設計レベルの det 解決のみ
- 盲点: scorecard 存在は暫定ハードコード (PARTS_WITH_SCORECARD)・カタログ列化が北極星
- 盲点: subflow 内部の判定点は本監査では opaque (別フロー)

## 第4 分岐(CMR/script) — PASS
- 盲点: フラット化は全サブフローが同一バンドルに揃い名前解決できること前提
- 盲点: 実 JS (Nashorn) パリティは要 JS エンジン (当 PC 不可)＝本監査は Python シム計算
- 盲点: OpenAI/Entity 等の RECORDED 出力は検証対象外 (記録サイドカー方式)
