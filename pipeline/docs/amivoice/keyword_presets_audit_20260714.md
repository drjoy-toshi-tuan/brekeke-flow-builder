# keyword_presets.yaml 監査レポート（2026-07-14）

> 基準: `docs/specs/script-input-handling.md`（標準判定ラダー B1〜B7・risk 区分）
> 対象: `docs/amivoice/keyword_presets.yaml` + 消費側 `tools/gen_scripts.py`

## 判定サマリ

| # | 重大度 | 所在 | 内容 | 対応 |
|---|---|---|---|---|
| 1 | **CRITICAL** | gen_scripts.py `build_branches` | **部分一致 + 定義順先勝ち**で分岐を生成（完全一致段・最長一致・否定優先なし）。「予約をキャンセルしたい」が option 順次第で 予約 に確定する — B2/B5/B6 違反・インシデント級 | **engine 改修が必要（別 PR）**: 完全一致段 → 複合/最長一致 → 部分一致の 2 段生成 + 生成時 lint（ラベル間キーワード衝突・2 文字以下の部分一致を CRITICAL） |
| 2 | **CRITICAL** | preset `hai` | `結構です` を肯定に登録（`sentei_ryoyouhi_disagree` では同じ語が拒否側 — 両義語）。認定部品 yes_no_classifier v4 は意図的に不採用 | **本監査で削除済み**（両義語は確定させず聞き直しに倒す） |
| 3 | MEDIUM | preset `dansei`/`josei`/`gozen` | 1 文字語 `男`/`女`/`朝` が部分一致に乗る（「長男」「朝以外」等で誤爆） | 部分一致では使わない旨の注記を追加（#1 の完全一致段実装後にそちらへ移す） |
| 4 | MEDIUM | `yoken_yoyaku` vs `yoken_kakunin` | 「予約の確認」が両ヒット・定義順勝ち | #1 の複合/最長一致で解消（それまで設計書側で 確認 option を先頭に置く運用回避を注記） |
| 5 | MEDIUM | `kojin` vs `kigyo_hojin` | `一般` ⊂ `一般社団法人` の部分一致衝突 | 同上（最長一致で解消）。注記追加 |
| 6 | LOW | `shinsatsuken_nashi` | `わかりません` を なし に写像（B3 は わからない 系へ、が原則） | 診察券は「不明=未所持扱い」が運用上正 — 意図的例外として注記 |
| 7 | LOW | `shinsatsuken_ari` / `iie` | `あります` 重複 / `違いますね` 冗長（`違います` が包含） | 本監査で削除済み |
| 8 | LOW | ファイル全体 | 語彙の出典（実ログ/受入ケース）記載なし | ヘッダに出典義務ルールを追記（既存語は「認定部品/テストケース由来」と包括注記、以後の追加は個別出典必須） |

## 推奨ロードマップ

1. **（本 PR）** preset 内容の安全修正 + 注記（#2/#3/#6/#7/#8）
2. **（対応済み 2026-07-14・本 PR）** 案(b)を採用: enum_classifier / youken ブロックを
   認定部品 `modules/n_choice` engine への spec 充填配線に置換（gen_scripts の自前分岐生成は退役）。
   キーワードは engine 正規化を通した形で登録、部分一致は最長一致・1 文字語は完全一致のみ、
   生成時に n_choice oracle の lint_config + ラベル間衝突検査で fail-closed。
   （参考・不採用となった案(a)）`build_branches` の 2 段生成改修:
   - 第 1 段: 完全一致（`^(kw1|kw2)$`）— 短い語・両義語はここのみ
   - 第 2 段: 複合パターン → 最長一致 → 部分一致（STRONG のみ）
   - 生成時 lint: ①同一ブロック内で同じキーワードが複数ラベルに載る → ERROR
     ②2 文字以下が部分一致に載る → ERROR ③risk: high 項目で WEAK 相当 → ERROR
   - もしくは enum_classifier / youken ブロックを認定部品 `modules/n_choice`
     （TOKEN/COMPOUND/KEYWORD 3 段 + NO_RESULT 固定）への配線に置換して gen_scripts の
     自前分岐生成を退役させる（決定論置換ロードマップと整合・推奨）
3. **（継続）** 実ログ月次収集（extract-yesno-synonyms 方式）を preset 全カテゴリへ展開し、
   追加語彙は出典つき PR のみ受け付ける
