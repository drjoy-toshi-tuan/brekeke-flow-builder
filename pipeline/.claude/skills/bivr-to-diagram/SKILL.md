---
name: bivr-to-diagram
description: 既存 BIVR（完成フロー）から、(1) VFB 設計書 YAML（scaffold_extractor 経由）→ enriched drawio フロー図（yaml-to-drawio・round-trip 互換）、(2) 分岐ノード（OpenAI/ContextMatchRouter/Script）の発話キーワード〜行き先「分岐早見表（Markdown＋ブラウザ表示用 HTML）」を作る定型ワークフロー。施設の最新 BIVR を正本に図と早見表を再生成する用途。高木版 bivr-to-diagram（canva-to-drawio 系）の価値を VFB ネイティブ（yaml_to_drawio 基盤）へ移植したもの。新規スクリプトは作らず、既存 extract_bivr.py / scaffold_extractor.py / yaml-to-drawio ＋ python3 -c（読取専用・stdout 出力のみ）で実行する。
---

# bivr-to-diagram — BIVR → enriched drawio ＋ 分岐早見表（VFB ネイティブ）

既存 BIVR（手修正済みの完成フロー）を正本に、**round-trip 互換**の Draw.io 図と、分岐ノードの早見表を作る。
高木版（canva-to-drawio 系）の人間向け価値を VFB ネイティブツールに載せ替えたもの（#257）。

## なぜ VFB ネイティブか（round-trip 互換）

VFB の `yaml-to-drawio` が出す drawio は **enriched node_xml 契約**（drawio-templates 標準）で、
`scenario_from_drawio.py` で **設計書 YAML に戻せる**。よって本 skill が出す図は
`BIVR → 設計書YAML → drawio → 設計書YAML → scaffold+build → BIVR` の**双方向 SSoT** に乗る
（canva-to-drawio 系の図は pipeline に戻せない＝この点が高木版との違い）。

## 厳守ルール（このプロジェクト共通・例外なし）

- **新規 Python スクリプトを作らない。** `python3 -c` は**読取専用**（`open(...,'w')` 等の書込禁止）。
  結果は **stdout に print** し、保存は必ず **Write ツール**で行う。
- 成果物は **`output/scenarios/{施設名}_{flow名}/`** 配下に集約（CLAUDE.md 配置規約）。`output/` 直下に一時を残さない。
- 日本語パスは bash の `cd` で化ける。`cd` せずフルパスを引数に渡す。展開先は ASCII 作業ディレクトリを使う。

## 起動時の入力

1. **BIVR ファイル**（`.bivr` = ZIP）のパス。
2. **IVR プロパティ .md**（あれば）。TTS 発話文言の正本。`scaffold_extractor --properties` に渡すと
   設計書 YAML の `tts_announcement` に流し込まれ、drawio のアナウンス一覧タブに載る。

施設名・flow 名は BIVR のフロー名（`{施設}${flow}`）から決める。無ければユーザーに尋ねる。

## 依存ツール（すべて既存・VFB）

- `scripts/extract_bivr.py` … .bivr 展開（`--list` でフロー一覧）
- `scripts/scaffold_extractor.py` … 既存 BIVR JSON → **設計書 YAML**（`--full-spec` で tts/step_details/flow_structure 等も抽出。`--properties` で TTS 流し込み）
- `.claude/skills/yaml-to-drawio/yaml_to_drawio.py` … 設計書 YAML → **enriched drawio**（2 タブ: シナリオフロー図／アナウンス一覧＝発話文言入り）。描画は **`/yaml-to-drawio` スキルを呼ぶのが第一選択**

---

## 実行フロー（上から順に）

### 0. 展開とフロー一覧

```bash
python3 scripts/extract_bivr.py "<BIVR>" --list                      # フロー一覧（モジュール数・start 確認）
python3 scripts/extract_bivr.py "<BIVR>" -o output/json/<ascii>_v<日付>   # 全フロー展開（pretty）
```

メインフロー（最大モジュール数）とサブフロー（氏名/生年月日/診察券番号/電話番号 等）を把握し、
出力先 `output/scenarios/{施設}_{flow}/` を決定（フルパスで `mkdir -p`）。

### 1. BIVR → 設計書 YAML（scaffold_extractor）

```bash
python3 scripts/scaffold_extractor.py "<MAIN_JSON>" --full-spec \
  [--properties "<IVRプロパティ.md>"] -o "output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml"
```

- `--full-spec`: scenario_flow に加え tts_modules / termination_patterns / step_details / flow_structure /
  hearing_items / amivoice_dictionary も抽出（TTS 発話を YAML に取り込む）。
- `--properties` があれば TTS 文言が `tts_announcement` に入り、図のアナウンス一覧に反映される。
- 出力 YAML を Read して `flow_type`（subflow/1flow）・subflows・分岐を確認。

### 2. 設計書 YAML → enriched drawio（yaml-to-drawio）

**`/yaml-to-drawio` スキルを呼ぶ**（自身の描画ロジックを知っている）。フォールバック:

```bash
python3 .claude/skills/yaml-to-drawio/yaml_to_drawio.py \
  "output/scenarios/{施設}_{flow}/設計書_{施設}_{flow}.yaml" \
  "output/scenarios/{施設}_{flow}/{施設}_{flow}.drawio"
```

- 出力は 2 タブ: **シナリオフロー図**（左右対称レイアウト）＋ **アナウンス一覧**（聴取項目｜復唱｜リトライ｜失敗時｜**発話文言**）。
  → 高木版の「文言入り台本」は、この**アナウンス一覧タブ**で代替（発話文言が src_ref でフロー図と同期）。
- この drawio は **enriched node_xml** ゆえ `scenario_from_drawio.py` で設計書 YAML に戻せる（round-trip）。
  2026-07-01・#257 Path A で writer（`yaml_to_drawio` + SSoT `drawio_style.py` 2026-06-19.1）が
  `conditions_json` / `output_format` / `save_to` / `reference_module` を出力するよう配線され、
  分岐条件・意味属性の往復保存を `scripts/test_roundtrip_drawio.py` で検証済（ロスレス）。

### 3. 分岐早見表（Markdown）— 本 skill の主価値

分岐ノードの**発話キーワード〜最終行き先**を 1 枚にする（出典は BIVR の実プロンプト＝正本）。

**対象検出**（読取専用ダンプ）: `generate_by_OpenAI` / `ContextMatchRouter` / `Script`（@General$Script）で
意味のある分岐が 3 本以上、または多段（OpenAI→Script→Router 連鎖）のものを対象にする。

```bash
# 対象候補の列挙（型・分岐数）
python3 -c "
import json
d=json.load(open(r'<MAIN_JSON>',encoding='utf-8')); m=d['modules']
SKIP={'^TIMEOUT$','^ERROR$','^NO_RESULT$','','^.+$','^.*$'}
for nm,v in m.items():
    t=v.get('type','')
    if any(k in t for k in ('generate_by_OpenAI','ContextMatchRouter')) or t=='@General\$Script':
        conds=[n.get('condition') for n in v.get('next',[]) if n.get('condition') and n.get('condition') not in SKIP]
        if len(conds)>=2: print(nm,'|',t.split(chr(36))[-1],'|',conds)
"
# OpenAI プロンプト全文 / Script 本体 / CMR の値→分岐（行き先の正本）
python3 -c "import json;d=json.load(open(r'<MAIN_JSON>',encoding='utf-8'));print(d['modules']['<OpenAIノード>']['params']['prompt'])"
python3 -c "import json;d=json.load(open(r'<MAIN_JSON>',encoding='utf-8'));print(d['modules']['<scriptノード>']['params']['script'])"
python3 -c "import json;d=json.load(open(r'<MAIN_JSON>',encoding='utf-8'));p=d['modules']['<routerノード>']['params'];[print(k,'=',repr(p[k])) for k in sorted(p) if k.startswith('module1Value') or 'Name' in k]"
```

読んだ実プロンプト/spec/CMR 値から早見表を Write で保存（テンプレ）:

- **① 認識キーワード早見表**: 発話例 → 正規化される正式名（OpenAI/script の分類ルールを全件転記）
- **② 対象外（AI 電話 非対応）**: 「登録なし」等に倒れる選択肢
- **③ カテゴリ集約キーワード**: 上から優先の一致ルール（NO_MARKERS/EXACT 等の評価順）
- **④ 最終分岐表**: 値 → 行き先ノード → 区分（✅進める / 📞代表案内 / ➡通常予約 等）
- 末尾に「本表は BIVR の各プロンプト/spec を正本に抽出。プロンプト改訂時は要更新」と明記。

保存先: `output/scenarios/{施設}_{flow}/{施設}_{flow}_分岐_早見表.md`（分岐が複数なら節 or ファイルを分ける）。

### 4. 早見表の HTML 版（ブラウザ表示用・必須）

早見表 Markdown は Windows でダブルクリックするとメモ帳で崩れる。CS/他メンバーが配布物として
ブラウザで見られるよう **同名 `.html` を必ずペア出力**する（Write ツールで保存。`python3 -c` での書込は禁止）。

- Markdown → HTML 変換は手作業（`#`→`<h1/h2/h3>`、`| … |`→`<table>`、`**`→`<strong>`、`` ` ``→`<code>`）。
- **`<meta charset="UTF-8">` 必須**（日本語化け防止）。
- **テーブル内容は早見表 MD と 1 文字も変えない**（正本は BIVR プロンプト。HTML 化は見た目だけ）。
- CSS は GitHub 風（`max-width:900px; line-height:1.7;` 等）で固定。`drawio-templates` の配布物トーンに合わせる。

---

## 成果物まとめ（output/scenarios/{施設}_{flow}/ 配下）

| 成果物 | ファイル | ツール |
|---|---|---|
| 設計書 YAML（round-trip 軸） | `設計書_{施設}_{flow}.yaml` | scaffold_extractor |
| enriched drawio（フロー図＋アナウンス一覧） | `{施設}_{flow}.drawio` | yaml-to-drawio |
| 分岐早見表 | `{施設}_{flow}_分岐_早見表.md` | python3 -c 読取＋Write |
| 分岐早見表 HTML | `{施設}_{flow}_分岐_早見表.html` | Write |

## round-trip との関係（#257）

本 skill の drawio は VFB enriched 標準ゆえ、編集後に `scenario_from_drawio.py` で設計書 YAML に戻し、
scaffold+build で BIVR を再生成できる（drawio を双方向 SSoT に）。早見表/設計書 YAML は drawio の
理解・レビューを助ける副成果物。高木版の canva-to-drawio 系作図は pipeline に戻せないため不採用とした。

**round-trip 保存の到達点（2026-07-01・#257 Path A）**: `YAML→drawio→YAML` は分岐条件（`conditions_json`）・
`output_format` / `save_to` / `reference_module` を保存する（`scripts/test_roundtrip_drawio.py` で assert）。
以前の「edges 21→13 に落ちる」ロスは解消。ただし **ブロック型の完全復元は工場レイヤの責務**で、
parser（`drawio_to_scenario`）は意図的に型を termination/CMR/hearing/announcement へ粗視化する
（`subflow` / `opening` / `script` 等の細分は工場デフォルトが SSoT）。細型の往復は本 skill でなく
`scenario_from_drawio` 側の課題（設計書 YAML が subflow に `slot_type` を持たない点）として残る。

## 関連

- 高木版 bivr-to-diagram（canva-to-drawio 系・原典）/ #257（BIVR・プロパティ → drawio round-trip）
- `scripts/scaffold_extractor.py` / `.claude/skills/yaml-to-drawio/` / `scripts/scenario_from_drawio.py`
- `drawio-templates`（enriched node_xml 視覚標準 SSoT）
