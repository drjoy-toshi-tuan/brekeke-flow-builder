# faq_exact_match

STT 補正済みテキストを **FAQ 質問文と完全一致**で照合し、回答本文（`setObject`）と分岐
`ANSWER`/`NO_RESULT`（`setResult`）を返す決定論 script（Brekeke `@General$Script`、スクリプト名 `scripts-faq`）。
照合辞書 `faqMap`（施設固有 54 件）は `script.js` に埋め込み。BM25/RAG ではなく**辞書の完全一致**。

- 言い換え・部分一致は拾わない（自信がないものは答えない＝医療文脈の安全弁）。言い換え吸収が必要なら `modules/faq_matcher/`。
- 仕様の詳細・分岐・エッジケース: `REQUIREMENTS.md`

## 構成

```
modules/faq_exact_match/
├── REQUIREMENTS.md            仕様（入出力・分岐・エッジケース・堅牢化）
├── README.md                  このファイル
├── script.js                  Brekeke IVR Script 本体（正本・faqMap 埋め込み）
├── oracle.py                  Python オラクル（script.js から faqMap を抽出して完全一致を独立実装）
├── test_oracle.py             オラクルの単体テスト（26 ケース）
├── build_test_flow_bivr.py    受入テスト用 bivr 生成器
└── acceptance_test/
    ├── README.md              実機受入の手順・ケース表・ログ判定
    └── FaqExactMatchAcceptanceTest.bivr   Pattern 6 受入フロー（28 ケース / 57 modules）
```

> `oracle.py` は `script.js` の `faqMap` を**抽出して**使う（辞書の二重管理なし）。`script.js` を直したら
> `test_oracle.py` と `build_test_flow_bivr.py` を再実行すること。

## オラクル

```bash
cd modules/faq_exact_match
python oracle.py "駐車場はありますか"   # 1 件判定（JSON）
python oracle.py --probe                 # プローブ一覧（期待値設計用）
python test_oracle.py                    # オラクル単体テスト → PASS 26/26
```

## 受入テスト bivr の再生成

```bash
cd modules/faq_exact_match
python build_test_flow_bivr.py
# → acceptance_test/FaqExactMatchAcceptanceTest.bivr が更新される
```

## 堅牢化（原スクリプトからの差分）

照合を素の `faqMap[text]` から **`Object.prototype.hasOwnProperty.call(faqMap, text)`** に変更。
`"toString"`/`"constructor"`/`"__proto__"` 等のプロトタイプ継承プロパティを誤って `ANSWER` にしないため。
詳細・理由は `REQUIREMENTS.md` の「堅牢化」節。

## 受入結果サマリ

| 項目 | 状態 |
|---|---|
| Python オラクル `test_oracle.py` | **PASS 26/26**（2026-06-19）|
| 受入 bivr 生成 | **完了**（28 ケース＝完全一致12 / trim2 / object2 / 非マッチ5 / 空2 / 継承5、57 modules）|
| Brekeke 実機受入（Pattern 6） | **PENDING**（`acceptance_test/` 参照）|
| `modules/README.md` 認定登録 | 未（実機 PASS 後）|

> このモジュールは実機受入が PASS するまで本番シナリオに組み込んではならない（CLAUDE.md「モジュール / script 開発ポリシー」）。
