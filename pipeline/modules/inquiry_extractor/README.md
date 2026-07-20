# inquiry_extractor — 用件抽出 決定論パーサ v2（OpenAI不使用）

商談デモ「フリー発話受付」シナリオ（`output/scenarios/商談デモ_フリー発話受付/`）の `用件抽出`（`type: script`）の部品。
**自由発話の STT テキストを直接解析**し、用件種別＋各スロット値＋取得有無フラグ＋復唱用の用件概要文へ
決定論的に分解する。**OpenAI は一切使わない**（自由発話の抽出そのものを script で行う）。

詳細仕様は [REQUIREMENTS.md](REQUIREMENTS.md)。

> **正本 = `docs/brekeke/script_templates/inquiry_extractor.js`**（テンプレート。scaffold が `用件抽出` ブロックに埋め込む）。
> 本ディレクトリは Python オラクル＋受入テストを保持。`script.js` 単体は廃止（テンプレが production 正本）。

## 何を決定論化したか（責任境界）
- **本部品（決定論 script）**: STT 生テキストのパース・用件種別分類・各スロットのベストエフォート抽出・
  取得フラグ付け・用件概要文の組み立て・context 撒き出し。OpenAI 不使用。
- **OpenAI が残るのは「こぼれたもの＝問い合わせ」の FAQ 対話のみ**（本部品のスコープ外）。
  用件種別が 新規/変更/キャンセル のいずれにも分類できない発話を `問い合わせ` とし、シナリオ側で FAQ-OpenAI へ流す。

## 設計原則
- **高精度優先・ベストエフォート**: 確信が持てる時だけ抽出（誤抽出回避＞recall）。抜けは下流の個人情報順次回収で取得。
- **氏名は「言い方」マーカー依存**（辞書ではない）: 「私は〇〇です」「〇〇と申します」等の自己紹介語法のみ。
  第三者名（「〇〇先生」）は患者氏名にしない。

## 入出力（要約）
- 入力: 用件フリー聴取（hearing/text・**OpenAIなし**）の STT 結果。テンプレは context（`{{CONTEXT_FIELD}}`=save_to）優先で読み、
  fallback で `getModuleResult({{INPUT_MODULE}})`（受入テストはこの fallback 経路でパーサを検証）。
- 出力1 `setResult`: canonical `<用件種別>‖<診療科>@<flag>‖…‖<診察券番号>@<flag>‖SUMMARY:<用件概要文>`。
- 出力2 `setObject`: `用件種別`/`用件概要`＋値7キー＋取得フラグ7キー（`<slot>_取得`）。

## シナリオ配線（商談デモ フリー発話受付 v2）
```
用件フリー聴取(hearing/text・OpenAIなし) → 用件抽出(本部品)
  → 用件概要復唱 → 確認(YES/NO)：NO=用件フリー聴取へ戻る（再聴取ループ）
  → YES → 用件種別分岐(<% 用件種別 %>)
        新規 → チェック_診療科 → チェック_予約希望日 → 個人情報回収
        変更 / キャンセル → チェック_予約日時 → 個人情報回収
        other(問い合わせ=こぼれ) → FAQ-OpenAI 対話（問合せ対応）
  → 個人情報回収（未取得のみ順次: 氏名→連絡先→生年月日→診察券番号）→ 最終確認 → 終話
```

## テスト
- オラクル: `python modules/inquiry_extractor/test_oracle.py` → **26/26 PASS**（2026-06-16）。
- 実機受入（Pattern 6 単体）: `acceptance_test/`（26 ケース、bivr `テスト_用件抽出_20260616.bivr` 135 modules、正本テンプレを sidecar 読込）→ **実機 26/26 PASS（2026-06-16）**。

## DoD 状況（認定済み 2026-06-16）
- [x] REQUIREMENTS.md v2
- [x] Python オラクル全 PASS（26/26, 2026-06-16）
- [x] 受入 bivr 生成（Pattern 6, 135 modules・構造検証 OK・正本テンプレ埋め込み確認）
- [x] **Brekeke 実機受入 PASS（26/26, 2026-06-16・全 `_cmr:1`/`_pass:ok`・`[TEST FAIL]` 0・`終了:OK` 到達）**
- [x] オラクル↔実機パリティ確認（Nashorn↔Python 全26バイト一致）
- [x] `modules/README.md` 認定レジストリ「認定済み」昇格（2026-06-16）

## パリティ（Python ↔ Brekeke JS）
- `oracle.py` と `docs/brekeke/script_templates/inquiry_extractor.js` は同一辞書・同一手順・同順で実装。
- 区切り除去は明示文字リスト（regex 範囲不使用）で JS↔Py 一致。使用記号は全て BMP。Nashorn(ES5.1) 想定で
  `String.normalize`/`includes`/arrow/テンプレート文字列 不使用。

## 注意・既知の制約
- ベストエフォート抽出。抽出 0 件でもフロー上は正常（再聴取/順次回収で吸収）。
- 連絡先=10〜11桁・診察券=ラベル必須 で数字列衝突を分離。氏名は STT 精度依存・recall 割り切り。
- 1 文字でも改変したら再受入（CLAUDE.md 部品ポリシー）。
