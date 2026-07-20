# FAQ Matcher 受入テストシナリオフロー

Python オラクル `oracle.py` と同等の **14 ケース** を Pattern 6 形式 (チェイン式) で
**1 コール内に直列実行** する Brekeke flow。各ケースは `QUESTION_SOURCE` にリテラル質問を
注入するので、**STT / AmiVoice 設定・入力読みの不確実性から独立した「検索エンジン本体の
決定論テスト」**になる (入力読みの確定は `../input_probe/` が担当)。

期待 jump が連続発火すれば PASS、いずれかで不一致なら対応 FAIL 終話で停止。

> **assert 強度**: FOUND ケースの期待条件は「正解の答え本文そのもの」(`^<答え>$`)。
> 単に「何か答えた」ではなく「**正しい FAQ の答えを返したか**」まで実機で検証する。
> NOT_FOUND ケースは `^NOT_FOUND$` を期待条件にする。

## 同梱物

| ファイル | 役割 |
|---|---|
| `FAQAcceptanceTest.bivr` | Brekeke にインポートする flow (**29 modules** = 14 ケース + 14 FAIL + 1 PASS) |
| `build_test_flow_bivr.py` | 上記 bivr の生成器 (`../script.js` をベースに、`oracle.search()` で期待値を実測して条件化) |
| `README.md` | このファイル |

## カバーする 14 ケース

| ID | 質問 (リテラル注入) | 期待 | 根拠 |
|---|---|---|---|
| FAQ-01 | 駐車場はありますか | FOUND:parking | 完全一致 cov=1.0 |
| FAQ-02 | 駐車場の場所を教えてください | FOUND:parking | 言い換え cov=0.69 |
| FAQ-03 | 受付時間を教えて | FOUND:hours | 完全一致 |
| FAQ-04 | 保険証は必要ですか | FOUND:insurance | 完全一致 |
| FAQ-05 | クレジットカードは使えますか | FOUND:payment | 完全一致 |
| FAQ-06 | カードで支払えますか | FOUND:payment | 言い換え cov=0.56 |
| FAQ-07 | 面会時間を教えて | FOUND:visiting | 完全一致 |
| FAQ-08 | 子供を診てもらえますか | FOUND:pediatrics | 完全一致 |
| FAQ-09 | 紹介状はいりますか | FOUND:referral | **境界 cov=0.50**（しきい値ちょうど→採用） |
| FAQ-10 | 車を停めるところはありますか | NOT_FOUND | 弱い言い換え cov=0.39 < 0.5（自信なし→答えない） |
| FAQ-11 | 診療は何時までですか | NOT_FOUND | 弱い言い換え cov=0.33 < 0.5 |
| FAQ-12 | 今日の天気はどうですか | NOT_FOUND | 無関係 |
| FAQ-13 | あのー、えっと | NOT_FOUND | フィラーのみ |
| FAQ-14 | はい | NOT_FOUND | 正規化後 < 3 文字 |

> FAQ-10/11 は「言い換えだが自信が持てないので答えない」= **医療文脈の安全弁**が効いていることの確認ケース。しきい値 `MIN_COVERAGE=0.5` を緩めれば FOUND 側に倒せる（運用で調整）。

## フロー構造 (チェイン式)

```
[テストFAQ-01_駐車場_完全一致]  QUESTION_SOURCE="駐車場はありますか"
   │ ^駐車場は本館の地下に…$ ──→ 次のケースへ (PASS)
   │ ^.*$                  ──→ [FAIL_FAQ-01_期待:FOUND:parking]
   ▼
[テストFAQ-02 …]  → … → [テストFAQ-14_短すぎ_はい] → ^NOT_FOUND$ → [PASS_全件PASS]
```

## 実行手順

### 前提 (重要)

1. **テナント `drjoy` 配下に Note `drjoy.faq` を作成**し、**`../faq_sample.json` の全文をそのまま貼り付ける**。
   - 期待値 (FOUND の答え本文) は `faq_sample.json` の `a` と**バイト一致前提**。Note 側を 1 文字でも変えると FOUND ケースが FAIL する。
   - JSON 形式: `[{"id": "...", "q": ["質問1","質問2"], "a": "答え（1 行）"}, ...]`
2. `../script.js` の CONFIG 既定値 (`MIN_COVERAGE=0.5` 等) を変更していないこと。変えたら `build_test_flow_bivr.py` を再実行して bivr を作り直す。

### Brekeke 投入

1. `FAQAcceptanceTest.bivr` を Brekeke 管理画面で flow として import (テナント drjoy 配下)
2. テスト発信 or「フロー実行」で **1 コールだけ**実行
3. Brekeke ログ画面で結果を観察

### ログから結果判定

各ケースで下記が記録される:

```
[FAQ-01] expected=FOUND:parking q=駐車場はありますか
[FAQ] question=[駐車場はありますか] note=drjoy.faq minCov=0.5 minChars=3
[FAQ] top: parking(16.18/1.00), parking(7.89/0.38), access(...)
[FAQ] => FOUND id=parking score=16.177 cov=1.000
Module.exec() name=テストFAQ-02_駐車場_言い換え   ← 次ケースへ
```

**全件 PASS の判定**:
```
Module.exec() name=PASS_全件PASS
```
↑ この行が出れば 14 ケース全パス → 検索エンジン受入確定。

**いずれかで FAIL**:
```
Module.exec() name=FAIL_FAQ-06_期待:FOUND:payment
```
↑ ここで停止。直前の `[FAQ] top:` / `[FAQ] =>` ログで不一致内容が分かる。

### grep 推奨

```
grep -E '\[FAQ-[0-9]+\]|\[FAQ\] (top|=>)|Module\.exec\(\) name=(テストFAQ|FAIL|PASS)' brekeke.log
```

## FAIL 時の切り分け

| 症状 | 主な疑い |
|---|---|
| 全 FOUND ケースが FAIL（NOT_FOUND になる） | Note `drjoy.faq` 未作成 / JSON 破損 → `[FAQ] => ERROR` か空 top が出ているはず |
| 特定 FOUND ケースだけ FAIL | Note の `a`（答え本文）が `faq_sample.json` と不一致（全角/半角・句点違い）。`[FAQ] => FOUND id=...` は出るが条件 `^答え$` に一致しない |
| NOT_FOUND ケースが FAIL（FOUND になる） | しきい値 `MIN_COVERAGE` が下げられている / FAQ が増えて衝突 |
| `[FAQ] => ERROR` | Note 不在・JSON 構文エラー・`Java.type` 例外 → 文言を確認 |
| Py と実機で判定がズレる | `java.text.Normalizer` NFKC と Python `unicodedata` NFKC の差（通常一致）。境界 cov のケースのみ要注意 |

## 既知の制約

- このフローは `script.js` の既定 CONFIG + `faq_sample.json` での回帰確認用。本番 FAQ (drjoy.faq) や しきい値を変えたら再生成すること。
- **ERROR ケースはチェインに含めない**（Note 不在/破損はテナント全体のグローバル状態で、ケース単位に注入できないため）。ERROR 経路は `script.js` のコードと live flow で確認する。
- Brekeke 1 コール 1000 モジュール上限内（本 flow 29 modules）。
- 14 ケースは Python オラクル (`../test_oracle.py` 24/24 PASS) と 1:1。アルゴリズムの正しさはオラクル側で担保。

## bivr 再ビルド (script.js / faq_sample.json / しきい値 変更時)

```bash
cd voicebot-flow-builder/modules/faq_matcher/acceptance_test
python build_test_flow_bivr.py
# → FAQAcceptanceTest.bivr が更新される
```
