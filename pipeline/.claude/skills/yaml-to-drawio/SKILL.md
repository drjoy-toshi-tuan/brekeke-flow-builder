---
name: yaml-to-drawio
description: voicebot-flow-builder の設計書 YAML (scenario_flow ブロック構造) から diagrams.net 形式の drawio (2タブ=フロー図/アナウンス一覧) を完全自動生成する。pptx ベースの canva-to-drawio と違い next/conditions が完全構造化されているため**エッジまで含めて 100% 自動**。v2 (2026-06-05) でリトライ/聴取失敗の自動描画(赤破線+表列)・冒頭/終話を中央軸に置く左右対称レイアウト・矢印の最背面化に対応。視覚標準は drawio-templates/ の drawio_style.py が SSoT。CS Ops PoC の主軸 skill。
---

# yaml-to-drawio — 設計書 YAML → drawio 変換 skill

> **視覚標準は `C:/Users/hamaguchi.t/drawio-templates/` が SSoT。**
> このフォルダの `drawio_style.py` は SSoT の **vendored コピー(編集禁止)**。
> 配色 / 凡例 / アナウンス表の挙動を変えたい場合は SSoT 側を直し、
> `python C:/Users/hamaguchi.t/drawio-templates/check_sync.py --resync` で再配布する。

## このスキルが解決する問題

[[canva-to-drawio]] は pptx からノード位置・ラベル・種別を取れるが、**エッジ(接続)は線形状の解析が困難で人間補完が必要**だった。

一方、voicebot-flow-builder の設計書 YAML は `scenario_flow` に **9 ブロック型 + next/conditions** が完全構造化されており、**ノードもエッジも 100% 自動生成**できる。新規シナリオ作成・既存テンプレート流用の双方で「Claude が一発で完成形を出す」が成立する。

## 使い方

```bash
python C:/Users/hamaguchi.t/voicebot-flow-builder/.claude/skills/yaml-to-drawio/yaml_to_drawio.py <設計書.yaml> [出力.drawio]
```

- 出力省略時: 入力 YAML と同階層に `<基本名>_drawio.drawio`
- 複数フロー(メイン + サブフロー)が定義されていても、`scenario_flow` のメインフローのみを変換(サブフローはノードに集約)

## 入出力

### 入力: 設計書 YAML

参考: `voicebot-flow-builder/docs/specs/設計書テンプレート.yaml`

期待される構造:
- `basic_info.facility_name` / `basic_info.scenario_name` — タイトル生成に使用
- `scenario_flow` — 9 ブロック型 + augment の配列(必須)
- `termination_patterns` — 終話パターン定義(任意、scenario_flow に無い終話を補完)
- `step_details` — TTS 発話文言(任意、アナウンス一覧テーブル生成に使用)

### 出力: drawio XML(**2 タブ構成** = 銚子市立病院 改善版 2page フォーマット)

**タブ1「シナリオフロー図」**(フローのみ):
- ノード: scenario_flow の各 step → 4 種別色で配置。各ノードに `type` / `announce` / `repeat` 属性を埋め込み(タブ2 がこれを参照)
- エッジ: next(単線) + conditions(分岐、match 値ラベル付き)。**hearing の聴取失敗(リトライ上限到達)は赤・破線エッジ**で遷移先(`END_聴取失敗` / `切断`)へ接続(v2)
- レイアウト: **冒頭/終話を中央軸に置き、分岐後のフローを左右対称・等間隔に整列**(v2)
- **矢印は最背面、ノードが最前面**(v2)
- 凡例: 配色ルール表示(最下段ノードの下・左寄せ。中央寄せを崩さない)

**タブ2「アナウンス一覧」**(別ページ):
- 「聴取項目｜復唱｜**リトライ｜失敗時**｜発話文言」の5列テーブル(step_details / termination_patterns 由来。リトライ/失敗時列は v2 追加)
- ヘッダーは薄灰(#EEEEEE)、聴取項目セルはブロック型の配色
- 各行は `src_ref` でタブ1の対応ノード id を指す(銚子 改善版と同じ同期構造)
- 復唱列は hearing_items の echo_back を「あり/無し」、リトライ列は retry_count(例「×2」)、失敗時列は retry_failure(終話/スキップ/切断)を表示

> 銚子市立病院_健診 改善版 drawio は「1タブ目=フロー / 2タブ目=アナウンス」の 2 ページ構成。
> 旧実装は 1 ページに右カラム併設だったため不一致だった → 2026-05-28 に 2 タブ分離へ修正。
> 2026-06-05 (v2): リトライ/聴取失敗の自動描画・中央寄せ対称レイアウト・矢印最背面に対応。

## ブロック型 → 色マッピング

| ブロック type | drawio 種別 | 配色 |
|---|---|---|
| `opening` | アナウンス | 薄橙 + 橙枠 |
| `announcement` | アナウンス | 薄橙 + 橙枠 |
| `hearing` (conditions なし) | 項目(聴取) | 薄グレー + グレー枠 |
| `hearing` (conditions あり) | 質問(分岐あり) | 薄青 + 青枠 |
| `subflow` | 項目(聴取) | 薄グレー + グレー枠 |
| `context_match_router` | 質問(分岐あり) | 薄青 + 青枠 |
| `script` | 質問(分岐あり) | 薄青 + 青枠 |
| `date_of_call_classifier` | 質問(分岐あり) | 薄青 + 青枠 |
| `call_transfer` | 項目(聴取) | 薄グレー + グレー枠 |
| `termination` | 終話 | 薄ピンク + 赤枠 |
| `augment` | 項目(placeholder) | 薄黄 + 灰枠 |

## エッジ色のヒューリスティック

`conditions[].match` の値からエッジ色を推定:

| match キーワード | エッジ色 |
|---|---|
| 「予約」「新規」「定期受診」 | 🔵 青 |
| 「変更」 | 🟠 橙 |
| 「キャンセル」 | 🔴 赤 |
| 「健康診断」「がん健診」「予防接種」 等の種類分岐 | 🟢 緑 |
| 「other」「default」「unknown」 | ⚪ 灰 |
| その他 | ⚪ 灰 |

= [[project_cs_agent_poc_2026Q3]] の銚子サンプルと同じ配色ルール。

## リトライ / 聴取失敗時の挙動の自動描画(v2・CSTS フィードバック)

hearing ブロックの **リトライ回数・復唱有無・聴取失敗時の遷移先** を自動描画する。CS / CSTS が顧客に見せる際、「聞き取れなかったときの挙動」まで一目で分かるようにするための機能。

- **タブ1(フロー図)**: 聴取失敗(リトライ上限到達)の遷移先を**赤・破線エッジ**で接続。
  - `retry_failure: end_failure` → `END_聴取失敗`(termination_patterns から「聴取失敗/リトライ/聞き取」を含む終話名を自動検出、無ければ `END_聴取失敗` を合成。実際に参照される時のみ)
  - `retry_failure: disconnect` → 合成した `切断` 終端ノードへ
  - `retry_failure: skip` → エッジは引かない(次へ進むためタブ2 失敗時列に「スキップ」とだけ表記)
  - これで従来 `termination_patterns` にしか無く**接続されず宙に浮いていた `END_聴取失敗`** が結線される。
- **タブ2(アナウンス一覧)**: 各 hearing 行に「リトライ(×N)」「失敗時(終話/スキップ/切断)」列を表示。
- データ源: `retry_count`/`echo_back` は `hearing_items[].name` 一致、`retry_failure` は scenario_flow ブロック → step_details の順にフォールバック(既定 end_failure)。
- subflow(氏名/生年月日/電話番号/診察券番号聴取)は内部に独自のリトライ/失敗ロジックを持つためバッジ・失敗エッジを付けない(個人情報サブフロー .bivr 側の責務)。

## レイアウト計算(v2・中央寄せ + 左右対称)

「**冒頭/終話をページ中央軸に置き、分岐後のフローを左右等間隔・対称に整列**」という浜口さんのフィードバックに対応。

1. **層(縦位置)= root からの longest-path**(合流ノードは全親より下)。DAG をトポロジカル順(Kahn 法・scenario 順で安定化)に走査。
2. **同層の並び = バリセンター法**(down/up スイープ 4 回)で交差抑制。
3. **X 座標 = 共通の中央軸 `center_x` を中心に左右対称・等間隔**(スロット間隔 240)。単独ノード層(冒頭/冒頭_アナウンス/主終話)は自動的に `center_x` に乗る。
4. **`pageWidth = 2 × center_x`** で中央軸 = ページ中央に一致。
5. **root から到達できない孤立終話**(`END_非通知`/`END_時間外` 等、冒頭ブロック内部の incoming-classifier / acceptance_times で分岐するため scenario_flow に遷移元が現れない)は**最下段**にまとめ、主終話の中央性を保つ。

## 矢印の z-order(v2)

**矢印(エッジ)は最背面、オブジェクト(ノード)は最前面。** drawio は XML 中で後に書かれた要素が前面に来るため、タブ1 の出力順を `エッジ → ノード → 凡例` として実現。

## テンプレート起点ワークフロー(推奨運用)

CS 担当者の典型ワークフロー:

1. 類似施設の設計書 YAML を **テンプレート**として選ぶ([[project_cs_agent_poc_2026Q3]] の Week 2-3 でテンプレート集を整備予定)
2. YAML を施設名・分岐ルール等で書き換え
3. `yaml-to-drawio` で drawio 化 → diagrams.net で確認
4. 顧客提示 → フィードバック反映 → YAML 修正 → drawio 再生成

= 「ゼロから書く」より「**既存パターンを修正する**」方が安全・速い・整合性高い、という浜口さん判断(2026-05-14)に沿う。

## テンプレート候補(Week 2-3 で選定予定)

| パターン | 候補施設 |
|---|---|
| **健診(個人 + 企業)** | 銚子市立病院、福岡新水巻病院、Medcity21 |
| **診療(基本)** | 中頭病院、ユアクリニックお茶の水 |
| **診療(複雑分岐)** | 湘南鎌倉総合病院、佐賀大学医学部附属病院 |
| **病診連携** | 浦添総合病院、信州大学医学部附属病院 |
| **疑義照会** | すずな皮ふ科 |
| **薬剤部** | 小山記念病院 |

## 今後の改善候補

- ~~中央寄せ + 左右対称レイアウト~~ → **v2 で対応済み**
- ~~リトライ / 聴取失敗時の挙動の自動描画~~ → **v2 で対応済み(CSTS フィードバック)**
- ~~矢印を最背面に~~ → **v2 で対応済み**
- `call_transfer` の `END_転送成功 / END_転送失敗`(scaffold が自動生成するが scenario_flow には現れない)を自動結線する
- 冒頭ブロック内部の分岐(非通知→`END_非通知` / 時間外→`END_時間外`)を冒頭ノードから結線して孤立を解消(冒頭_アナウンスの中央性とトレードオフ。現状は孤立終話を最下段に隔離し中央性を優先)
- 複数フロー(メイン + サブフロー)を 1 drawio に複数 diagram として出力

## 既知の制約

- **augment** ブロックは placeholder 扱いで暫定色(薄黄)
- `END_非通知` / `END_時間外` など冒頭ブロック内部でしか分岐しない終話は遷移元が scenario_flow に現れないため**最下段に隔離配置**(線は引かれない)。聴取失敗系は v2 で結線済み
- subflow の内部リトライ/失敗はメインフロー図には出さない(個人情報サブフロー .bivr 側の責務)
- `scenario_flow` 以外の構造(例: 旧式 `routing_map` 形式)には未対応 — director が出した新形式 YAML 専用

## 検証実績

- 2026-05-14: skill v1 リリース
- 2026-05-27: アナウンス一覧テーブル生成を実装(初版は 1 ページに右カラム併設)。docs/specs/templates/ の 6 シナリオテンプレート(診療/健診/地域連携/疑義照会/受診相談/訪問看護)を drawio 化
- 2026-05-28: 銚子 改善版 2page との不一致指摘を受け 2 タブ分離に修正(ただし `NODE_H` import 漏れで実シナリオは生成不可の未完成状態だった)
- 2026-06-05: **v2** — `NODE_H` バグ修正 + リトライ/聴取失敗の自動描画(タブ1赤破線 + タブ2 リトライ/失敗時列)+ 中央寄せ対称レイアウト + 矢印最背面。
  視覚語彙の追加(`edge_xml(kind="failure")` / `build_legend` / `build_announce_page` 5列化)は SSoT 正本 `drawio-templates/drawio_style.py`(STYLE_VERSION 2026-06-05.1)に入れ check_sync で再配布。
  全 139 設計書 YAML で生成 PASS(XML well-formed・2タブ・dangling edge ゼロ・全層中央軸対称)。ユア(赤破線1)・中頭(赤破線10・skip混在)・Medcity21(全skip→赤破線0)で確認

## 関連

- [[project_cs_agent_poc_2026Q3]] — 本 skill が乗る PoC 全体
- [[reference_canva_to_drawio_skill]] — 姉妹 skill(pptx 入力経路)。エッジ自動生成は本 skill のみ
- [[project_block_architecture]] — 9 ブロック型アーキテクチャの設計メモリ
- voicebot-flow-builder/scripts/block_layout.py — レイアウト参考実装
- voicebot-flow-builder/scripts/gen_spec_html.py — YAML → HTML 仕様書(参考実装)
