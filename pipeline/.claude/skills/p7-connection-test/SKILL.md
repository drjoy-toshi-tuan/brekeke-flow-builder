---
name: p7-connection-test
description: VFB の Pattern 7「連結テスト」を、メンバーが自分の Claude Code で準備〜実機案内まで一気通貫で回すための手順スキル。本番 BIVR を一次ソース（--bivr・#244）にしてケース表を生成し、乖離検証（validate_bivr）と被覆検証（--coverage）を必ず走らせ、複数入口（別 DID）フローでセレクタが片方にしか付かない「恵佑会連携室が動かない」型の事故を機械的に潰し、STT スタブ BIVR を生成して実機インポート・発信・突合の手順を案内する。実機の駆動（インポート・発信・ログ突合）は人間。プロジェクトローカル skill。
---

# p7-connection-test — Pattern 7 連結テスト入口（VFB）

あなた（メンバーの Claude）は、単体受入済みの部品を繋いだ**本番フローが実機で意図通り繋がるか**を、
STT 認識の不確実性を切り離して検証する連結テスト（Pattern 7）を準備する。
仕様の正本は `connection_test/REQUIREMENTS.md`、所見台帳は `docs/governance/test-feedback-loop.md`（FB-1〜）。

> **スコープ（REQUIREMENTS.md）**: P7 が守るのは「正規化・配線・API 連携・終話が実機で繋がるか」。
> STT 認識精度・入力パターン耐性・TTS/データ連携の副作用は**スコープ外**（それは P6 と実運用側）。
> **実機の駆動（import・発信・ログ突合・PASS/FAIL 判定）は人間**。あなたは生成物を作り手順を案内するだけ。

作業は自由ゾーン `output/scenarios/{施設}_{flow}/` と `connection_test/cases/` `connection_test/golden/` に閉じる。
保護ゾーン（scripts/schemas/tools/.claude）は触らない。

## 起動時の引数

`施設名 フロー名`（sparring-intake / new-scenario と同じ命名規約）。
本番 BIVR（Brekeke で手修正された実運用フロー）のパスも確認する。**BIVR が一次ソース**（後述）。

---

## ⚠️ 先に読む — 複数入口（別 DID）フローの扱い

`connection_test/stub_stt_connection.py` は **複数入口対応済み**（`detect_entries()`・全入口にセレクタ自動前置）。

- 背景: 診療＋連携室のように**相互に jump しない別 DID 入口**を持つ施設で、旧実装（単一入口 `detect_entry()`）は
  セレクタを「jump 未参照フローのうちモジュール数最大の 1 本」にしか前置せず、もう片方の入口に発信すると
  `__tc_id` 未設定 → 全スタブが DEF に落ち、**その入口が「動かない」ように見えた**（恵佑会札幌 連携室の真因）。
- 現在: 既定で jump 未参照フロー（＝着信入口候補）を**全部**検出し、各入口にセレクタを前置する。
  `--entry-flow` で入口を明示的に絞った場合、未選択の入口候補があれば **`[ENTRY-WARNING]`** が
  「その入口に発信すると全 DEF に落ちる」と是正コマンド付きで警告する。Step 3 はこの警告の確認でよい。
- **入力は 1 施設・1 シナリオのまとまった BIVR** にすること。複数施設が混在した蓄積ダンプはグループ名一意検出で
  fail-fast する（`ERROR: グループ名を一意に検出できません`）。その場合は対象施設のフローだけを export し直す。

---

## 実行フロー（上から順に）

### Step 1. ケース表を生成 — 必ず `--bivr`（本番 BIVR 一次ソース・#244）

VFB 生成後に BIVR は Brekeke UI で手修正され設計書 YAML と乖離する。**実機 BIVR を正本にすれば
ケースは必ず実機と一致する**。YAML(`--spec`)単独生成は乖離を検知できないため使わない。

```bash
python3 scripts/gen_p7_cases.py \
  --bivr <本番.bivr> \
  --facility <施設名> --flow <フロー名> \
  --spec output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml   # 併用で YAML↔BIVR 乖離検証(validate_bivr)
  # [--dtmf-steps "用件確認:4,コース選択:4"]  DTMF 併用 hearing の数字注入ケース(step:選択肢数)
  # [--entry-flow <入口フロー>]               セレクタ前置先（省略時 flow）
```
- 出力: `connection_test/cases/{施設}_{flow}.json` ＋ Excel 用 CSV（`output/scenarios/{施設}_{flow}/連結テストケース_*.csv`・BOM 付き）。
- `--spec` 併用時に走る乖離検証 `validate_bivr()`（#223）が出す警告を**必ず解消**する:
  - `STT-DEFAULT-MISSING` … 既定注入が引けない STT ＝そのノードが全ケース NO_RESULT に落ちる。
  - `START-NOT-ENTRY` / `ORPHAN-NODES` … 入口の入次数・到達性の異常。
  - `ORDER-SHADOW` … `_order` の substring 衝突（「患者」が「生年月日」を隠す等・FB-9/11）。専用キーを長い順に前置。
  - `NONSPEAKABLE-LABEL` … 分類器の非発話ラベルに inject 未指定（#239）。設計書 YAML の condition に
    `inject:` を SSoT として書く（例: 「受付不可→総合内科」）。書かないと全ケース NO_RESULT→聴取失敗に倒れる。

### Step 2. 被覆検証 — trim された受入を検出

```bash
python3 scripts/gen_p7_cases.py --coverage connection_test/cases/{施設}_{flow}.json \
  --spec output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml
```
- content 分岐母集合に対する被覆率を出し、**100% 未満なら未カバー分岐を列挙して exit 1**。
- 未カバーが出たら cases.json に不足ケースを足す（分岐ラベル 1 本＋DTMF エッジ＋リトライ true/exhaust）。
- ⚠️ orchestrator の `step_p7_generate` は `--spec` 生成のみで **`--bivr` 検証も `--coverage` も呼ばない**
  （#304/#297 の実態）。この Step 1〜2 を**手で回す**のがメンバーの責務。既存 cases.json があると
  step_p7_generate は再利用し再生成しないので、**BIVR 差し替え後は cases が古いまま乖離する**点に注意。

### Step 3. 入口の確認（恵佑会型の罠を潰す）

stub 生成（Step 4）は既定で jump 未参照フロー（＝着信入口候補）を**全部**検出し各入口にセレクタを前置する。
実行後に出力される `Entry :` 行と `[SELECTOR] OK (N エントリに前置: …)` で、想定した入口が全部含まれるか確認する。
- 入口が **1 つ** → そのまま（`--entry-flow` 省略で自動検出）。
- 入口が **複数**（診療＋連携室 等）→ 既定で両方にセレクタが付く。`--entry-flow` で絞ると、外した入口が
  `[ENTRY-WARNING]` で列挙される（その入口に発信すると全 DEF に落ちる）。意図的に絞る場合を除き**全入口を対象にする**。
  複数入口は同じ `__tc_id` 空間を共有するため、入口間でケース番号帯を重複させない。
- 事前に入口を把握したいときは `read-bivr` skill か Brekeke UI で「どのフローも Jump to Flow の宛先でない＝入口」を確認。

### Step 4. STT スタブ BIVR を生成

```bash
python3 connection_test/stub_stt_connection.py \
  --bivr <本番.bivr> \
  --cases connection_test/cases/{施設}_{flow}.json \
  --facility <施設名> \
  # [--entry-flow 診療,連携室]  入口を明示（カンマ区切りで複数可）。省略時は jump 未参照フロー全部を自動検出
  # [--tag T_]                   テスト印プレフィックス（本番と同一グループに同居・衝突回避）
  --out connection_test/stub_{施設}_{flow}.bivr
```

> **⚠ 2026-07-16〜: P7 出力は常に以下 2 種を揃えること**（orchestrator.py `step_p7_generate` が
> 自動生成。手動実行時も同様に2回呼ぶこと）:
> 1. **stub 版**（上記コマンドそのまま・引数無し）: STT はスタブ、TTS は再生あり。
>    実際の読み上げ音声を耳で確認したい場合はこの版で聞ける（人手なしで STT も進む）。
> 2. **skip_tts 版**（`--skip-tts` 追加）: TTS 再生なし・即切断。フロー進行/context保存の高速確認用。
>
> `--no-stub-stt`（STT スタブ無効・実機 AmiVoice 駆動）は「実音声版」として標準出力に含めない
> （2026-07-16 一度追加したが撤回）。これは実機 AmiVoice に**生身の話者が実際に喋る必要がある**版で、
> 「人手を介さず音声を注入して AmiVoice に聞かせる」ニーズとは別物。後者に相当する音声注入レーン
> （Twilio+WAV）は本リポジトリ未整備（`connection_test/REQUIREMENTS.md` 参照・スコープ外）。
> 生身の話者による実機確認は Step 5（人間の手動実機テスト）でカバーする。

- STT ノードを `@General$Script`（`$runner.setResult(注入値)`）に置換。`next/subs/matchingmethod` は温存
  ＝下流の正規化・CMR・終話はそのまま動く。冒頭に DTMF ケースセレクタを前置し `$ivr.setObject("__tc_id", id)`。
- 生成後の検証（255B 以内 / 未スタブ STT なし / 全 jump 解決 / entry にセレクタ）で NG なら
  `VERIFICATION FAILED` exit 1。`[STT-DEFAULT-FALLBACK]` が出たノードは注入が引けない＝Step 1 の
  `_order`/inject を直す。
- **本体整合チェックが自動で走る**（`SOURCE-CONSISTENCY`）: 生成した stub BIVR と入力の本体 BIVR で
  CMR params / next / subs / jump を突合し、乖離があれば exit 1。生成元の sha256・cases ハッシュ・生成日時は
  zip comment に埋め込まれる（恵佑会札幌 260629: テストBIVR の CMR `module1Name` だけが古い状態で
  全ケースが その他_FIXED に倒れた事故の再発防止）。

> **⚠ 本体 BIVR は一時的にも編集しないこと（subagent 含む）。** stub_stt_connection.py には常に
> 「変更のない本体 BIVR のファイルパス」を渡す。ケース補完・再生成を挟んだ場合は必ず本体から再生成する。

### Step 4.5. 実機投入前の一発検証（時間が経った stub を使い回す場合は必須）

```bash
python3 connection_test/verify_test_bivr.py \
  --test-bivr connection_test/stub_{施設}_{flow}.bivr \
  --source-bivr <本番.bivr>
```
- 生成元 sha256 の一致確認 + CMR/next/subs/jump の diff。乖離 0 でなければ**実機投入せず再生成**。
- skip-tts 版・no-stub-stt（実 AmiVoice）版など複数の出力すべてに同じ検証が使える。

### Step 5. 実機（人間の手作業）

`connection_test/REQUIREMENTS.md` の手順に従い、以下を人間が行う:
1. Brekeke テスト番号へ stub BIVR をインポート（複数入口なら各入口の DID にそれぞれ）。
2. 発信 → ケース番号＋`#` を入力（ハンズフリー）。
3. Brekeke ログを cases.json の `expect` と突合（`[STT-STUB]` マーカーが手がかり。callId 混在は人が判別＝FB-6）。
   PASS 基準 = 期待終端に到達＋途中チェックポイント一致。
4. CSV に PASS/FAIL を記入。
5. 完走トレースを `connection_test/golden/{施設}_{flow}/` へ保存。

> **expect は「下書き」**（REQUIREMENTS 明記）。ゴールデンログ観察後に人間が確定させる。
> 生成物の期待値の正誤は機械検証されないので、初回は golden を取ってから expect を確定する。

---

## テスト後の残差の行き先

- 実機 NG の分類（配線ミス / 正規化バグ / 期待値誤り / STT 注入漏れ）と起票は **@工場長**（ライン外）へ。
- 生成物（stub / cases）は直接いじらず、**設計書 YAML か本番 BIVR（生成器）を直して再生成**する。
- P7 は認定ゲートではない（認定は P6＝`part-p6-accept` skill）。P7 は「繋がるか」の保持テスト。

関連: `connection_test/REQUIREMENTS.md` / `docs/governance/test-feedback-loop.md` / `read-bivr` skill /
`part-p6-accept` skill（P6 側）/ `procure-part` skill（未認定部品に当たったとき）。
