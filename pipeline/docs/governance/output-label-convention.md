# 出力表示ラベル規約（Output Label Convention）— 全エンジン共通

**起票 #270（2026-07-02）。** 分類器エンジンの**出力"表示"ラベル**（Dr.JOY 画面に保存・表示され、
CMR 分岐がマッチする文字列）を **wiring** として扱い、施設ごとのラベル差し替え（`あり/なし`・
`はい/いいえ` 等）を **engine 再認定なし**で可能にするための、部品横断の設計規約。

認定モデルの土台は `part-certification-spec.md`（engine / spec / wiring の 3 分類）。本書はその
§3 を「出力ラベル」について具体化する。

---

## 1. 問題（#270）

`yes_no_classifier` は `decide()` が `"肯定"/"否定"` を**直接 return**していた。この文字列は
engine 領域（`@spec` 外・wiring 外・非コメント）にあるため engine_hash に寄与する。結果:

- Dr.JOY 表示は施設ごとに `あり/なし`・`はい/いいえ` 等にしたいのに、部品は `肯定/否定` を固定出力。
- ラベルを変えるには `decide()` を編集するしかなく、**engine_hash が変わる＝施設ごとにフル再認定**。
- 実際つくばセントラル病院で `decide()` を**都度手パッチ**して回避 → **未認定 engine フォーク**が量産され、
  oracle_gate の engine_hash 照合を潜脱するガバナンス穴になっていた。

これは yes_no 固有ではなく、**全分類器エンジンに共通する「内部判定」と「表示ラベル」の混同**である。

---

## 2. 原則 — 内部判定enum ≠ 表示ラベル

| 概念 | 例 | 認定分類 | 変更時 |
|---|---|---|---|
| **内部判定enum** | 肯定 / 否定 / NO_RESULT | **engine**（バイト不変） | engine 再認定（重大） |
| **表示/保存ラベル** | あり/なし・はい/いいえ | **wiring**（両ハッシュ除外） | 受入不要（別配置） |

- エンジンは**内部enum**で判定し、判定ロジックは全施設でバイト不変（＝engine）。
- **表示ラベルは「正しさに無関係なデプロイ都合」＝ wiring**。判定の正誤はラベル文字列に依存しない。
- 写像（内部enum → 表示ラベル）は**出力境界（setResult / saveContext）で一度だけ**行う。
- **`NO_RESULT` は内部 sentinel（再質問を誘発する制御値）ゆえ非ラベル化**。表示ラベルにしない。

---

## 3. 実装パターン（yes_no v4 が第1適用）

### 3.1 エンジン（`modules/<part>/script.js`）
- 表示ラベルを **wiring var** として宣言（`part.json.wiring_vars` に登録＝engine_hash から除外）:
  ```javascript
  // @template YES_LABEL: 肯定側の表示/保存ラベル（wiring・既定 肯定）
  var YES_LABEL = "__YES_LABEL__";
  var NO_LABEL  = "__NO_LABEL__";
  ```
- `decide()` は**内部enumを返したまま**。出力境界でのみ写像:
  ```javascript
  var out   = decide(norm);                    // 内部enum（肯定/否定/NO_RESULT）
  var label = (out === "肯定") ? YES_LABEL : ((out === "否定") ? NO_LABEL : out);
  $runner.setResult(label);
  saveContext(label, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
  ```
- `@engine-version` を上げる（**一度だけフル再認定**）。以後の施設別ラベルは wiring 変更＝受入不要。
- 不変条件（`tools/lint_part_markers.py`）: placeholder は wiring 行 or `@spec` 内のみ。`return YES_LABEL`
  のような**識別子参照は engine 領域で合法**（placeholder トークンを含まないため）。

### 3.2 scaffold（単一ソース生成でドリフト不能）
`scripts/scaffold_generator.py: build_yes_no_script(..., yes_label, no_label)` が、
**同一の `yes_label`/`no_label` から** ① script の `__YES_LABEL__/__NO_LABEL__` 充填 と
② CMR の `next` マッチャ（`^{yes_label}$` / `^{no_label}$`）を生成する。両者が同一ソースゆえ
**ラベルとマッチャは構造的にドリフトしない**。充填漏れは生成時 assert で機械検出。

### 3.3 設計 YAML（著者が指定する場所）
`hearing` ブロックに任意の `yes_label` / `no_label` を置く（未指定は既定 `肯定/否定`＝後方互換）:
```yaml
  - step: 受診券所持確認
    type: hearing
    output_format: enum
    save_to: "medicalTicket"
    yes_label: "あり"      # Dr.JOY 保存/表示 ＋ CMR マッチ（affirm 分岐）
    no_label:  "なし"
    conditions:
      - {match: "はい",   next: 予約希望日聴取}   # match はルーティング意図（どちらが affirm か）
      - {match: "いいえ", next: 自費確認}
```
- `conditions[].match`（はい/いいえ）＝**どの分岐が affirm/deny か**を決めるルーティング意図（従来どおり）。
- `yes_label`/`no_label`＝**保存・表示・CMR マッチに使う実ラベル**（新設）。両者は別概念。

### 3.4 受入（P6）でのラベル充填
`script_test_matrix` は `input_placeholder` 以外の wiring placeholder を `wiring:` マップで既定充填する
（`scripts/test_scaffold_generator.py`）。yes_no の P6 受入 yaml は既定 `肯定/否定` を充填し、
**既存 243+45 スイートを無改変で通す**（＝engine parity 証明）:
```yaml
    type: script_test_matrix
    input_placeholder: "__SOURCE_MODULE__"
    wiring:
      __YES_LABEL__: "肯定"
      __NO_LABEL__:  "否定"
```

### 3.5 整合の機械ガード（多層）
1. **scaffold 単一ソース生成**（本質）— ラベルとマッチャが同一引数由来でドリフト不能。
2. **scaffold assert** — ラベル空/重複・wiring 充填漏れ（未置換 placeholder が setResult に漏れる #270 の失敗）を検出。
3. **qa_validator L-10** — 設計 YAML 層で片方のみ/空/重複/予約語 `NO_RESULT` を早期に CRITICAL。

---

## 4. 他エンジンへの一般化

- **二値エンジン（yes_no）**: 内部enum固定・表示ラベル=wiring。→ 本書 §3、v4 で適用済み。
- **多値エンジン（n_choice 等）**: 出力ラベルは現状 `@spec`（DTMF_MAP / KEYWORD の `result`）で持つ＝
  ラベル変更＝新 spec_hash＝spec 受入（単体 P6）。**分類は同一で表示文字列だけ変えたい**場合は、
  将来 §2 に倣い「内部キー=spec / 表示ラベル=wiring マッピング」を任意導入できる（本書準拠の後日適用）。
- 各エンジンの適用状況は `part.json`（`wiring_vars` に表示ラベル var があるか）で判別する。

---

## 5. yes_no v4 再認定メモ（オーナーゲート）

- engine v3 `ce3c09f5…` → **v4 `7fa2756b…`**（`decide()` は不変・出力境界の写像追加ゆえ engine_hash 変化）。
- **spec_hash は不変**（`@spec` 未変更）: 同意 `d0d533bf…` / 存在 `2b1fe1bb…`。
- `certified_hashes.json` は**オーナー専用 SSoT**（本 PR では未編集）。実機フル再認定 PASS 後にオーナーが:
  - `parts.yes_no_classifier` を engine v4 hash に更新、
  - `specs` の 2 キーを新 engine_hash 複合キー（`7fa2756b…:d0d533bf…` / `7fa2756b…:2b1fe1bb…`）へ再登録。
- oracle は内部enumを検証するため**改変不要**（243/243 parity 維持）。P6 は既定ラベルで既存スイートを再実行。
