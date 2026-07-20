# FAQ Matcher

患者の発話 (直前 STT の文字起こし) を **Brekeke Note 内の FAQ 仮想 DB** に照合し、
答えるべき FAQ があれば答え本文を、無ければ `NOT_FOUND` を返す **OpenAI / 外部 API /
エンベディング不使用の決定論 RAG** モジュール (`@General$Script`)。

設計の発端: 「Business Hour Classifier と同じ Note 機能に FAQ をまとめて置き、Script から
読んで検索する」構想 (2026-06-04)。最大 1,000 件規模を想定。

## 一言でいうと

> STT の文字起こしを **NFKC 正規化 → 文字 2-gram → BM25 → coverage しきい値**で FAQ Note に照合し、
> **しきい値以上なら答え本文を、未満なら NOT_FOUND を**返す。「質問か」「答えを持つか」を
> スコア 1 本で同時判定するので、OpenAI のインテント分類が要らない。

## 入出力

| | 内容 |
|---|---|
| **入力** | `QUESTION_SOURCE` = `"module:<STT名>"`（本番）or リテラル質問（テスト注入） |
| **FAQ DB** | Brekeke Note `drjoy.faq`（JSON 配列、管理画面で直編集・即時反映） |
| **出力** | 答え本文（FOUND）/ `NOT_FOUND` / `ERROR` を `$runner.setResult()` |

### jumps（モジュール UI 側で登録。順序が重要）

```
^ERROR$      → 異常時フォールバック（Note 不在・JSON 破損・内部例外）
^NOT_FOUND$  → 該当なしフォールバック（既定: 有人/受付へ転送）
^.+$         → 回答読み上げ（catch-all = 答え本文）。必ず最後に置く
```

回答の発話は **`drjoy^Text To Speech$Re-confirmation node data`**（`module` = 本 Script
モジュール名、`prompt` = `{tts_g: #data# }`）で `#data#` に答え本文を差し込む。

### 本番フロー配置イメージ

```
… → [STT 入力_FAQ質問] ── success ^.+$ ──→ [FAQ Matcher script]
                                              ├ ^ERROR$     → 代表転送 等
                                              ├ ^NOT_FOUND$ → 有人転送 / 「お調べして折返し」等
                                              └ ^.+$        → [Re-confirmation #data#] → 終話/ループ
```

## FAQ Note (`drjoy.faq`) 形式

```json
[
  {"id": "parking", "q": ["駐車場はありますか", "車で行けますか"], "a": "駐車場は本館の地下にございます。"},
  {"id": "hours",   "q": ["受付時間を教えて"],                    "a": "診療時間は平日九時から五時です。"}
]
```

- `id`: 一意キー（ログ識別用）
- `q`: 質問の言い回し（文字列 or 配列）。各バリアントが独立 doc としてスコア対象
- `a`: 答え本文。**1 行**（改行を含めない。TTS / 完全一致 assert のため）
- サンプル: `faq_sample.json`（受入テストはこれを Note **`drjoy.faq_acceptance`** に貼って使う）
- **Note 名の使い分け（衝突回避）**: 商談デモ/本番=`drjoy.faq` / 受入テスト=`drjoy.faq_acceptance`（=faq_sample.json）/ 実践テスト=`drjoy.faq_practice`（=faq_note.json）。`FAQ_NOTE_NAME` は wiring 変数なのでデプロイ/テストごとに差し替える（`drjoy.` 固定・サフィックスはシナリオ可変）。同一 Note を共有すると受入と実践/デモが上書き衝突するため必ず別名にする。

## CONFIG（script.js 冒頭）

| 定数 | 既定 | 説明 |
|---|---|---|
| `QUESTION_SOURCE` | `"module:入力_FAQ質問"` | 質問の取得元。本番は STT 名、テストはリテラル |
| `FAQ_NOTE_NAME` | `"drjoy.faq"` | FAQ DB の Note 名。**wiring 変数**（デプロイ/テストで差替＝engine_hash 不変）。テストは `drjoy.faq_acceptance`/`drjoy.faq_practice` |
| `SYNONYM_NOTE_NAME` | `""` | 任意のシノニム辞書 Note（未実装枠、`""` で無効） |
| `MIN_COVERAGE` | `"0.5"` | 質問 bigram のうちマッチ FAQ に含まれる割合の下限。**答える/答えないの安全弁** |
| `MIN_QUERY_CHARS` | `"3"` | 正規化後この文字数未満は NOT_FOUND |
| `BM25_K1` / `BM25_B` | `"1.2"` / `"0.75"` | BM25 パラメータ |

## 実証済み API（流用元: Business Hour Classifier）

| 用途 | API |
|---|---|
| Note 読み | `Java.type("com.brekeke.pbx.common.NoteUtils").read("drjoy.faq")` / `.exists()` |
| STT 結果読み | `$runner.getModuleResult("<STT名>")`（`module:` 接頭辞時。要 input_probe 確認） |
| 結果返却 | `$runner.setResult(String)` |
| NFKC 正規化 | `Java.type("java.text.Normalizer").normalize(s, Java.type("java.text.Normalizer$Form").NFKC)` |

## ファイル構成

```
modules/faq_matcher/
├── README.md            このファイル
├── REQUIREMENTS.md      仕様（入出力・分岐・エッジケース・しきい値根拠）
├── script.js            Brekeke IVR Script 本体（正本）
├── oracle.py            Python オラクル（検索ロジックの独立実装＝期待値の正本）
├── test_oracle.py       オラクル単体テスト（24/24 PASS）
├── faq_sample.json      サンプル FAQ DB（受入テスト用。Note drjoy.faq に貼る）
├── input_probe/         STT 結果の読み取り API を実機確定する probe（getModuleResult の戻り）
└── acceptance_test/     受入テストフロー（14 ケース、Pattern 6 チェイン）+ 生成器
```

## 受入状況（DoD: CLAUDE.md「決定論優先・受入テスト必須」）

| 項目 | 状態 |
|---|---|
| REQUIREMENTS.md | ✅ |
| Python オラクル + 単体テスト | ✅ `test_oracle.py` 24/24 PASS |
| 受入テストフロー bivr | ✅ `acceptance_test/FAQAcceptanceTest.bivr`（14 ケース） |
| **Brekeke 実機受入** | ⏳ **未実施**（本コミットで bivr 用意済み、これから実機） |
| 入力読み API（getModuleResult の戻り） | ⏳ `input_probe/` で確定待ち |
| `modules/README.md` 認定登録 | ⏳ 実機受入 PASS 後に登録 |

> **受入テストを通過するまで本番シナリオに組み込まないこと**（CLAUDE.md）。
> アルゴリズムを 1 文字でも変えたら `oracle.py` を同期し、`test_oracle.py` + 実機受入を再実行。

## 既知の制約・今後

- 〜1,000 件想定。それ以上はオフライン事前インデックス + Note シャーディングを検討（毎コール
  `JSON.parse` + index 構築のコストが効いてくるため）。
- シノニム辞書 (`SYNONYM_NOTE_NAME`) は枠のみ。表記揺れは現状 2-gram 一致で吸収。
- `java.text.Normalizer` NFKC と Python `unicodedata` NFKC は通常一致するが、境界 coverage の
  ケースのみ実機とオラクルで差が出る可能性 → しきい値ちょうどのケースは避けて運用。
- ERROR 経路（Note 不在/破損）は受入チェインに入らない（グローバル状態のため）。コードと live flow で確認。
