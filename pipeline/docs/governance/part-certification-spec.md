# 部品規格 認定仕様（Part Certification Spec）— 二段判定ゲート v2

**確定日 2026-06-16（浜口さん承認）。** Pattern 6 認定ゲート（`scripts/orchestrator.py` の
`step_oracle_gate` / `step_p6_gate`）を、**部品種別（engine）と規格（spec）の二段判定**に作り替える設計仕様。
DoD は CLAUDE.md「モジュール / script 開発ポリシー」、認定台帳は `modules/README.md`、
置換ロードマップは `deterministic-replacement-roadmap.md`。

---

## 1. 背景 — 現状ゲートの盲点

現行 `_script_logic_hash`（`orchestrator.py:3382`）は **設定行を 2 prefix だけ除外**してハッシュする:

```python
_CONFIG_LINE_PREFIXES = ("var SOURCE_MODULE", "var MENU")
```

この前提は「インスタンス差は `var SOURCE_MODULE` 1 行だけ、分類データは正本にハードコード」。
checkup 系（`var SOURCE_MODULE` の 1 行のみ可変）には合うが、**ジェネリックなテンプレ部品**
（`n_choice` / `inquiry_classifier` 等＝データ自体が `{{DTMF_MAP}}` 等のテンプレ）には合わない。

### 実証（2026-06-16・亀田で計測）

| スクリプト | logic_hash[:12] |
|---|---|
| `n_choice` 正本（テンプレ `{{}}`） | `fc732bc2…` |
| `script_caller_type.js`（発信元充填・受入用） | `70b30b33…` |
| 亀田シナリオ bivr 内の `n_choice`（実配線充填） | `ee6c870b…` |

3 つすべて不一致 → 亀田シナリオ bivr 内の `@General$Script` は **n_choice 7 個＋inquiry 1 個＝8 個すべて
part 認識 0**。結果 `step_p6_gate` は `known=[]` → **`PASS_NO_SCRIPTS`（部品なし扱いで素通り）**。

**問題の本質**: 大元の正本から **中身（DTMF_MAP / KEYWORD / RULES 等）を少しだけ変えたケース**は
今後頻出する。その変更後も正規化・分岐が正しい保証は、**P6 を回さない限り取れない（＝ノー）**。
現行ゲートはこれを救出するどころか、テンプレ部品を認識すらできず素通りさせる。

---

## 2. 設計思想 — 部品規格と二段判定

工場の部品管理に倣う。**ネジはネジ、釘は釘。各々に規格がある。**

1. **同一種類の部品か（ネジか釘か）を判別する** ＝ 部品種別（engine）
2. **その上で、新しい規格として受け入れるべき部品かを判定する** ＝ 規格（spec）

「刻印を読む → 規格に適合するか検査する」を機構化する。

| 段 | 比喩 | 機構 | 判定 |
|---|---|---|---|
| 1a. 種別の刻印 | ネジか釘かの刻印 | スクリプトの `// @part-id:` マーカー | どの部品を名乗っているか |
| 1b. 種別の検査 | 刻印どおりか | **engine_hash** が登録 engine と一致するか | エンジン本体が改竄されていないか |
| 2. 規格の受入 | M3 か M4 か（新規格か） | **spec_hash** が認定済み spec か | この設定で受入を通したことがあるか |

---

## 3. engine / spec / wiring の 3 分類

スクリプトの全行を 3 つに区分し、各ハッシュへの寄与を決める。

| 区分 | 比喩 | 定義 | engine_hash | spec_hash |
|---|---|---|---|---|
| **engine** | 鋼材の材質・構造 | 全用途で**バイト不変**であるべきアルゴリズム（正規化・判定順・ループ・保存関数等） | ✅ 含む | ✖ |
| **spec** | 呼び径・ピッチ | 施設・設問ごとに正当に変わり、**変更時は受入必須**な分類データ | ✖ | ✅ 含む |
| **wiring** | どの穴に挿すか | 入力元モジュール・保存先 context・実行時刻など**正しさに無関係なデプロイ都合** | ✖ | ✖ |

- engine が変わる＝**部品種別の改変**（重大 → 再認定）。
- spec が変わる＝**新規格**（→ 受入を要求して救出）。
- wiring が変わる＝同一部品・同一規格の**別配置**（受入不要）。
- **コメントは engine_hash から全除外**（ビルドが placeholder をコメント内も全置換するため、不変でない）。

---

## 4. スクリプトのラベリング規約（マーカー）

各正本 `modules/<part>/script.js` に以下を埋める。マーカーはコメント行なのでビルド後も保存される。

```javascript
// @part-id: n_choice
// @engine-version: v4

// --- wiring（part.json で var 名宣言・両ハッシュから除外）---
var INPUT_MODULE = "{{INPUT_MODULE}}";
var CONTEXT_NAME = "{{CONTEXT_NAME}}";
var CONTEXT_DISPLAY_TYPE = "{{CONTEXT_DISPLAY_TYPE}}";

// @spec-begin
var DTMF_MAP = {{DTMF_MAP}};
var KEYWORD_PATTERNS = {{KEYWORD_PATTERNS}};
// ...spec データ（複数 @spec ブロック可・順序維持で連結）
// @spec-end

// （ここから下は engine。@spec ブロック・wiring 行・コメントを除いた残り全部が engine_hash）
var logger = $runner.getLogger();
// ...正規化・判定・保存関数...
```

**不変条件（正本リンタで機械検査）**: `{{...}}` / `__...__` placeholder は **必ず wiring 行または
`@spec` ブロック内にのみ**置く。engine 領域に placeholder があってはならない（あると充填で
engine_hash が変わり種別判定が壊れる）。

---

## 5. ハッシュ計算

```
spec_hash   = sha256( normalize( 全 @spec ブロックの連結 ) )
engine_hash = sha256( normalize( script − @spec ブロック − wiring 行 − 全コメント − 空行 ) )
```

- `normalize` = 改行を `\n` 統一、各行 rstrip、連続空行畳み込み。**意味のあるデータ変更は必ずハッシュに反映**
  （= 保守的。整形しただけでも再受入が走るが無害）。
- wiring 行の除去は part.json の `wiring_vars` に挙げた var 名で `^\s*var <name>\s*=` 行を落とす（単一行前提）。
- `@spec` ブロックは `// @spec-begin` 〜 `// @spec-end` の範囲削除（複数可・多行データもこれで吸収）。

---

## 6. レジストリ / メタデータ スキーマ

### 6.1 `modules/certified_hashes.json`（認定台帳・機械が読む）

```jsonc
{
  "parts": {
    "n_choice": { "engine_hash": "…64hex…", "engine_version": "v4" }
  },
  "specs": {
    "<engine_hash>:<spec_hash>": {
      "part": "n_choice",
      "spec_label": "発信元3分類",
      "cases": "modules/n_choice/acceptance_test/発信元/cases.tsv",
      "certified_date": "2026-06-16",
      "scenario": "亀田総合病院_総合相談室"
    }
  }
}
```

- `parts` = 既知の部品種別（engine 刻印の正）。stage 1b で照合。
- `specs` = 認定済み規格。キーは `engine_hash:spec_hash` の複合。stage 2 で照合。

### 6.2 `modules/<part>/part.json`（部品の規格表・静的メタ）

```jsonc
{
  "part_id": "n_choice",
  "engine_version": "v4",
  "wiring_vars": ["INPUT_MODULE", "CONTEXT_NAME", "CONTEXT_DISPLAY_TYPE"],
  "specs": {
    "発信元3分類": {
      "cases": "acceptance_test/発信元/cases.tsv",
      "filled_script": "acceptance_test/発信元/script_caller_type.js"
    }
  }
}
```

- `wiring_vars` = ハッシュ除外する var 名（spec は `@spec` マーカーで構造的に表現するので列挙不要）。
- `specs` = この部品で受入済み/受入予定の規格カタログ。新規 spec はここに 1 エントリ追加してセットを置く。

---

## 7. ゲート v2 のフロー

`_collect_flow_scripts` を改修し、各 `@General$Script` インスタンスに
`{part, engine_hash, spec_hash, engine_ok, spec_certified}` を付与する。

`step_p6_gate` の分岐:

1. **engine 既知 ＆ (engine,spec) 認定済み** → `PASS_CERTIFIED`（自動スキップ）。＝同一規格の再利用。
2. **engine 既知だが spec 未認定（＝新規格）** → **P6 受入を要求**。
   - `part.json.specs` に該当 spec のセット（`cases.tsv` ＋充填JS）があれば、その bivr 実機 PASS を要求 → PASS で `specs` 登録。
   - **セットが無ければ即ブロック**: 「規格未定義。`acceptance_test/<spec>/` に受入セットを作成せよ」。
     ← **これが救出機構**。config を少し変えただけのケースを、テスト無しでは絶対に通さない。
3. **`@part-id` マーカーあり・engine_hash 不一致 / マーカーなし / engine 未登録** → **ブロック**（人手レビュー）。
   「n_choice を名乗るが engine が改竄されている」「未知の部品種別」。**エンジン事故を最大に鳴らす。**

`step_oracle_gate` も同様に part 認識を二段化（engine で part 特定 → その part の `test_oracle.py` 実行）。

---

## 8. 全 9 部品の規格表（移行）

| 部品 | wiring_vars | spec_vars（`@spec` で囲う） | 規格 | 備考 |
|---|---|---|---|---|
| `n_choice` | INPUT_MODULE, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE | DTMF_MAP, TOKEN_MAP, DIGIT_KEYWORD_PATTERNS, COMPOUND_PATTERNS, KEYWORD_PATTERNS | 設問ごと（発信元/患者区分/担当者…） | テンプレ `{{}}`。複数 spec |
| `inquiry_classifier` | INPUT_MODULE, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE | RULES, NO_QUESTION, FILLER_ONLY | 亀田 総合相談室 | データ内蔵・単一 spec |
| `yes_no_classifier` | SOURCE_MODULE | EXACT_YES, EXACT_NO, WAKARANAI_MARKERS, NO_MARKERS, YES_MARKERS | 標準 | |
| `department_classifier` | （入力配線・実装時に確認） | WAKARANAI, DEPARTMENTS, TRAILERS | 公式30科 | 単一 spec |
| `business_hour_classifier` | TARGET_DATETIME, REFERENCE_DATE | WEEKDAY_SCHEDULE, CLOSED_DATES, NATIONAL_HOLIDAY, HOLIDAY_NOTE_NAME | 施設の営業時間 | 施設ごと spec |
| `checkup_intent_classifier` | SOURCE_MODULE | FOLDINGS, WAKARANAI_MARKERS, CATEGORIES | 健診CC 6施設共通 | 単一 spec |
| `checkup_course_classifier` | SOURCE_MODULE | FOLDINGS, WAKARANAI_MARKERS, CATEGORIES | 健診CC | |
| `checkup_menu_classifier` | SOURCE_MODULE | MENU, MENUS, WAKARANAI_MARKERS | エリア別メニュー | MENU は spec 選択子 |
| `faq_matcher` | QUESTION_SOURCE, SYNONYM_NOTE_NAME | STRIP, NOQ_MAX_NORM_LEN, NO_QUESTION_PHRASES/SUFFIXES/FILLERS/TRAILERS, SENTENCE_SPLIT, CORRECTION_MARKERS, CONJUNCTION_MARKERS | 施設ごと | FAQ本体はNote/データ。派生（NOQ_SET 等）は engine |

> 非テンプレ部品（checkup 系・department・yes_no 等）は spec が現状 1 個でも、データを `@spec` で囲うことで
> **将来データを触ったら自動で「新規格→受入要求」に倒れる**。特例コード不要で統一できる。

---

## 9. acceptance_test ディレクトリ規約

規格ごとにサブディレクトリ化（承認決定 2）。

```
modules/n_choice/acceptance_test/
  発信元/
    cases.tsv
    script_caller_type.js          # 発信元 spec の充填版
    設計書_テスト_発信元分類.yaml
    テスト_発信元分類_<日付>.bivr
  患者区分/                          # 将来 spec を足すときはここに 1 ディレクトリ
    ...
```

現行 `acceptance_test/` 直下（＝発信元 spec）は `発信元/` へ移設。`inquiry_classifier` は
`acceptance_test/亀田総合相談室/` 等、単一 spec でも spec 名サブディレクトリに統一。

### 9.1 P6 受入 BIVR の生成（統一導線）

engine 変更後の再認定（実機 P6）のたびに過去 bivr を探す運用を禁止する。**P6 受入仕様は
部品配下に置き、1コマンドでスクラッチ生成する**。

- **置き場所**: `modules/<part_id>/acceptance_test/p6_acceptance.yaml`（part.json の `p6_spec` で参照）。
  output/ ではなく部品配下に置く（version 管理で部品と一体・output 掃除で消えない）。
- **生成**: `python tools/build_part_acceptance_bivr.py <part_id>`
  → `output/acceptance/<part_id>/<part_id>_p6_acceptance.bivr` を生成。Brekeke import→架電で受入。
  spec 内の matrix ブロック型（`script_test_matrix`＝分類器 / `dob_reconfirmation_test_matrix`＝
  custom-module 復唱 等）で部品種別を吸収するため、ツールは種別非依存。
- **未来日など時刻依存ケースは固定日付を禁止**。spec で相対トークン（`__TODAY__`/`__TOMORROW__`/
  `__FUTURE__`/`__FUTURE_WAREKI__`）を使う。`test_scaffold_generator` が生成日（JST）基準で解決する
  ので、いつ再生成しても期待値がドリフトしない（固定日付は後日 INVALID/有効が反転して誤 FAIL する）。

---

## 10. 新規 spec 追加の運用フロー

1. 正本 `script.js` の `@spec` 内データを新設定で充填した `filled_script` を `acceptance_test/<spec>/` に置く。
2. その spec の `cases.tsv`（テストが正）を書き、`python test_oracle.py`（または spec 指定）で oracle PASS。
3. Pattern 6 bivr を生成 → Brekeke 実機で `[TEST FAIL]`=0。
4. `part.json.specs` に spec エントリ追加。ゲートが PASS で `certified_hashes.json` の `specs` に登録。
5. `modules/README.md` 認定台帳へ spec 行を追記。

---

## 11. 後方互換・移行ステップ

1. `_script_logic_hash` を engine/spec 二重ハッシュ関数に置換（`_CONFIG_LINE_PREFIXES` は廃止）。
2. 9 部品の正本に `@part-id` / `@engine-version` / `@spec` マーカーと `part.json` を追加（**oracle 再 PASS で挙動不変を確認**）。
3. `acceptance_test/` を `<spec>/` サブディレクトリへ移設。
4. `certified_hashes.json` を新スキーマで初期化。既存の実機 PASS 済み spec
   （n_choice=発信元 / inquiry=亀田 / department / business_hour / checkup_intent 等）を `specs` に手登録。
5. `_collect_flow_scripts` / `step_oracle_gate` / `step_p6_gate` を二段判定に改修。
6. 正本リンタ（engine 領域に placeholder が無いことを検査）を追加。

> 移行中も既存挙動を壊さないため、レジストリ未整備の間は「未認定＝手動 P6」に倒す（現行と同じ安全側）。

---

## 12. 関連

- `scripts/orchestrator.py`：`_script_logic_hash` / `_collect_flow_scripts` / `step_oracle_gate` / `step_p6_gate`
- `modules/README.md`：認定台帳（part × spec で行を持つ）
- `docs/governance/deterministic-replacement-roadmap.md`：置換ロードマップ
- CLAUDE.md「モジュール / script 開発ポリシー — 決定論優先・受入テスト必須」

---

## 13. 厚木（健診CC）統合と移行（2026-06-16）

亀田 v2 を共通基盤の正本に確定し、厚木セッションの分類器アップグレードを v2 へ一本化した。

- **共有インフラ衝突の解決**: orchestrator（ゲート）/ certified_hashes は **v2 を採用**。
  厚木の旧ゲート（単一ハッシュ certified_hashes・gap② 未完）は破棄。
- **厚木の設計を adopt（commit 520a010 → 亀田）**: checkup_intent/course/menu/yes_no の三点セット
  （script/oracle/cases）＋ cases_lateness ＋ **ambiguity_gate（新規共有部品）** ＋
  build_classifier_acceptance_bivr.py。path 限定 checkout で取り込み、v2 マーカー/part.json を再付与。
- **engine 変化 → 再受入**: NFKC正規化（全4分類器）と SCOPE/lateness（checkup_intent）は engine を変える。
  engine_version を v2 に上げ、certified_hashes.parts を新 engine へ更新。
  **新 engine の spec は v2 での P6 実機まで未認定**（厚木の旧版 326 認定は旧 engine のもの＝記録）。
- **SCOPE / GROUP は wiring**: checkup_intent の `SCOPE`（full/lateness）、ambiguity_gate の `GROUP` は
  per-instance 設定行＝wiring。1認定で全インスタンスをカバー（受入は全 SCOPE/GROUP を網羅すること）。
- **厚木ローカルは独立継続**: output/scenarios 成果物・P7 資産は厚木ブランチで継続（衝突なし）。
  厚木は v2 ベースへリベースすれば自分の分類器 work は既に亀田へ移植済み＝重複コミットは破棄でよい。
- **残**: 上記5部品（checkup×3 / yes_no / ambiguity_gate）の v2 実機受入 → spec 認定登録。
