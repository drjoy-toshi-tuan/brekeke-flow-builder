---
name: part-p6-accept
description: VFB の Pattern 6「部品 単体実機受入」を、メンバーが自分の Claude Code で回すための手順スキル。oracle/lint を通し、部品の種別に応じた正しい経路で P6 受入 BIVR を生成し（統一ツール / spec 個別指定 / モジュール内 build スクリプト / in-flow script_test_matrix の 4 系統を吸収）、実機 PASS 後に certified_hashes.json 登録用の「全長 engine/spec ハッシュ」を読み取り専用で算出し、cert_request 起票ドラフトまで用意する。実機架電と certified_hashes.json への登録はオーナー専用（人間ゲート）。プロジェクトローカル skill。
---

# part-p6-accept — Pattern 6 部品受入＋認定登録ドラフト（VFB）

あなた（メンバーの Claude）は、認定部品（`modules/<part>/`）や施設フロー内 script の **単体実機受入（P6）**を準備し、
実機 PASS 後の **certified_hashes.json 登録依頼ドラフト**までを用意する。仕様の正本は
`docs/governance/part-certification-spec.md`（engine/spec 二段判定ゲート v2）。

> **人間ゲート（厳守・#249 起票キーストーン）**: メンバーがローカルで通せるのは
> oracle / lint / coverage / P6 受入 BIVR 生成 / 実機 P6 **まで**。
> `certified_hashes.json` 登録・`modules/README.md` 台帳追記・`parts_catalog.json` 棚入れは
> **オーナー専用の保護 SSoT**。あなたは cert_request ドラフト（全長ハッシュ入り）を作って起票するだけ。
> 実機架電そのものも Brekeke テナント依存＝オーナー/テスト番号保有者が行う。

## 二段判定の考え方（part-certification-spec.md）

- **engine_hash** = 部品種別の刻印（材質）。script.js からコメント・空行・wiring 行（`var <wiring>=`）を除いた残り。
  **engine が変わる = 別部品＝フル再認定**（`FAIL_ENGINE` で最優先ブロック。意図的改修かはオーナー判断）。
- **spec_hash** = 規格データ（呼び径）。`// @spec-begin`〜`// @spec-end` の中身。**spec だけ変わった = 新規格→受入要求**（実機 P6 で該当 spec のみ確認）。
- **wiring**（INPUT_MODULE / CONTEXT_NAME / ラベル等）= 配置。**hash に不寄与＝受入不要**。
- 純エンジン部品（spec データ無し）の spec_hash は空文字の SHA256 = `e3b0c44298fc...b7852b855`。

---

## 実行フロー（上から順に）

### Step 0. oracle と自己整合性 lint

```bash
python3 modules/<part>/test_oracle.py     # 全ケース PASS（oracle = 真値 or 全経路モデル）
python3 tools/lint_part_markers.py        # @part-id / @spec ブロック / placeholder 位置の自己整合。engine ドリフト検出
```
- lint が `engine_hash ドリフト` を出したら **engine を触っている**＝ spec 追加でなく別部品化。フル再認定になるので
  オーナーに `FAIL_ENGINE` 相当として相談（意図的なら certified_hashes.parts の更新も要る）。

### Step 1. P6 受入 BIVR を生成 — 部品種別で経路を選ぶ

部品の `acceptance_test/` 構成を見て 4 系統から選ぶ:

| 判定 | 経路 | コマンド |
|---|---|---|
| **単一 spec**（`acceptance_test/p6_acceptance.yaml` が 1 つ） | 統一ツール | `python3 tools/build_part_acceptance_bivr.py <part>` |
| **複数 spec**（`acceptance_test/<spec>/p6_acceptance.yaml` がサブディレクトリ別） | spec 個別指定 | 各 spec で `python3 tools/build_part_acceptance_bivr.py <part> --spec modules/<part>/acceptance_test/<spec>/p6_acceptance.yaml --out output/acceptance/<part>/<part>_<spec>.bivr` |
| **モジュール内 build あり**（business_hour_classifier / faq_matcher / faq_exact_match） | 専用スクリプト | `python3 modules/<part>/acceptance_test/build_test_flow_bivr.py`（faq_exact_match は `modules/faq_exact_match/build_test_flow_bivr.py`） |
| **in-flow script**（施設フロー内の script ブロック・modules 化しない） | script_test_matrix | 自由ゾーン `output/scenarios/{施設}_{flow}/p6/` に spec(YAML)＋cases.tsv＋本番 script.js を置き `test_scaffold_generator.py`→`layout_calculator.py`→`build_bivr.py`。実例: `output/scenarios/すずな皮ふ科クリニック_疑義照会/p6/` |

- 出力（統一ツール）: `output/acceptance/<part>/<part>_p6_acceptance.bivr`。
- spec の `cases` の **expected は内部 enum ではなく wiring 充填後の表示ラベル**と一致させる（#270）。
  例: yes_no は `YES_LABEL: 肯定 / NO_LABEL: 否定` を wiring に書き、cases.expected も「肯定」「否定」。
- 相対日付トークン（`__TODAY__/__TOMORROW__/__FUTURE__/__FUTURE_WAREKI__`）は生成日基準で解決される。
- ⚠️ **n_choice 7 spec は「代表 P6 + oracle 登録」でオーナーが実機 P6 を省略**する裁量がある（同一 engine・config データ差のみ）。
  この省略判断はオーナー限定。メンバーは全 spec の oracle PASS を根拠に提示するところまで。

### Step 2. 実機 P6（人間の手作業）

1. 生成 BIVR を Brekeke テスト番号へインポート → 発信。
2. ログを確認: **PASS 基準 = `[TEST FAIL]` が 0 件**（全 `<id>_cmr:1` / pass:ok）＋末尾 `[TEST DONE]`/`結果_完了` へ到達完走。
3. `docs/governance/part-certification-spec.md` §9.2: **落ちるケースを外して合格にするのは禁止**。必ず spec/script を直す。

### Step 3. 全長 engine/spec ハッシュを算出（読み取り専用）

certified_hashes.json のキーは `<engine_hash>:<spec_hash>` の**64hex 全長**が要る（lint は先頭 12 桁のみ表示）。
以下は読み取り専用の `python -c`（作業スクリプトは残さない・CLAUDE.md 準拠）。**単一/複数 spec 両対応**:

```bash
python3 -c "
import sys,json; sys.path.insert(0,'scripts')
import orchestrator as o
part='<part>'
p=json.load(open(f'modules/{part}/part.json',encoding='utf-8'))
wiring=p['wiring_vars']
specs=p.get('specs') or {}
if specs:                                   # 複数/宣言 spec 部品: 各 filled_script を hash
    for label,sp in specs.items():
        fs=sp['filled_script']
        path=fs if fs.startswith('modules') else f'modules/{part}/{fs}'
        eh,sh=o._engine_spec_hashes(open(path,encoding='utf-8').read(),wiring)
        print(f'{label}\t{eh}:{sh}')
else:                                        # 単一 script 部品: canonical script.js を hash
    txt=open(f'modules/{part}/script.js',encoding='utf-8').read()
    eh,sh=o._engine_spec_hashes(txt,wiring)
    print(f'(single)\t{eh}:{sh}')
"
```
- engine_hash が `tools/lint_part_markers.py` の先頭 12 桁および `certified_hashes.parts.<part>.engine_hash` と一致することを確認（engine 不変の裏取り）。
- 別解: `orchestrator.py` の p6_gate を resume で回すと `test_gate_*.json` に全長ハッシュが載る（登録は無人モードでは PENDING）。

### Step 4. 認定登録依頼ドラフトを起票（certified_hashes 登録はオーナー）

`gh issue create` が使える環境:
```bash
gh issue create --template cert_request.md   # [Cert] <施設>_<flow> — <part> spec P6登録依頼
```
`gh` 不可環境のフォールバック（`cert_requests/README.md`）: `cert_requests/{施設}_{flow}.md` に
`.github/ISSUE_TEMPLATE/cert_request.md` と同項目で本文を書き、feature ブランチに commit → push → PR。

ドラフトに必ず入れる:
- 未認定 spec 一覧の表（モジュール名 / spec ラベル案 / **engine_hash 全長 / spec_hash 全長 / key = engine:spec**）。
- 実機 P6 結果（`[TEST FAIL]` 0 件・完走ログの要点）。engine 不変（＝再認定カスケード無し）である旨。
- 対象 bivr / feature ブランチ / 関連 PR。

> オーナーが実機 P6 PASS を確認 → `certified_hashes.json.specs["<engine>:<spec>"]` に
> `{part, spec_label, cases, certified_date, scenario}` を追記 → `modules/README.md` 台帳追記 →
> `python3 tools/generate_parts_catalog.py` で棚入れ、までを行う。**spec_label/cases は自動登録されない手作業**。

---

## よくある詰まり（このスキルが埋める暗黙知）

- ハッシュは手計算不可（spec 連結・wiring 除去・コメント/空行畳み込みの正規化が絡む）→ Step 3 のレシピで出す。
- P6 素材が 3 系統に散在（統一ツール / モジュール内 build / 手動プリビルド bivr）→ Step 1 の表で経路を選ぶ。
  `p6_acceptance.yaml` を既定パスに持つのは一部部品のみ。無ければ spec 個別指定か専用スクリプト。
- `expected` は表示ラベル（#270）。内部 enum を書くと実機で不一致になる。
- engine が変わったら spec 追加でなく別部品＝フル再認定（オーナー相談）。
- 登録はオーナー専用 SSoT。メンバーは cert_request ドラフトまで。

関連: `docs/governance/part-certification-spec.md` / `docs/governance/p6-batch-runbook-2026-07-06.md`（バッチ手順の実例）/
`.github/ISSUE_TEMPLATE/cert_request.md` / `cert_requests/README.md` / `procure-part` skill（未認定部品の調達）/
`p7-connection-test` skill（連結側）。
