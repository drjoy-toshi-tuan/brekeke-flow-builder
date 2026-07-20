# go_back_classifier — L0 戻る/繰り返し検知モジュール 要件

## 目的
商談デモ「フリー発話受付」の各聴取STT入力ゲートで、**L1（field_presence）が ABSENT** の
ときに走る **L0**。入力STTテキストを検査し、前工程へ戻す要望（気が変わった）か、直前TTSの
再生要望か、いずれでもないか（→FAQ）を判定する。

下流カスケード:
```
入力_X(STT) → L1_X(field_presence):
    PRESENT → 通常処理
    ABSENT  → L0_X(go_back_classifier) → 分岐_L0_X(CMR):
        戻る     → 用件フリー聴取（intake再実行・既定）
        繰り返し → 聴取_X（当該TTS再生）
        NONE(^0$ other) → FAQ_X(faq_matcher)
```

## 入出力
- 入力: `getModuleResult({{INPUT_MODULE}})`（本番）または保存 context `{{CONTEXT_FIELD}}`（優先）。
- 出力（`$runner.setResult`）: `戻る` / `繰り返し` / `NONE`。

## 判定ロジック
- **戻る**（強い意図語を優先）: やっぱり/別の用件/最初から/やり直し/前に戻/違う用件/変更したい/キャンセルしたい/取り消して 等。
- **繰り返し**: もう一回/もう一度/もっかい/聞こえなかった/聞き取れ/なんて言った/言ってください/繰り返し 等。
- 複合（例「もう一回最初から」）は **戻る** 優先。
- いずれでもなければ **NONE**。

## 前提（安全性）
- L0 は L1=ABSENT 後にのみ走る＝入力は既に「当該フィールド回答ではない発話」に限定される。
  そのため戻る/繰り返し語彙の誤検知リスクは低い。
- 用件確認(はい/いいえ)では L1=yes_no_classifier が 否定 を拾うため、「違います」等は L0 に到達しない。

## 戻り先（既定・調整可）
- 戻る → `用件フリー聴取`（用件から取り直す）。
- 繰り返し → `聴取_X`（当該聴取の TTS を再生）。
- 実機UXで調整余地（特に変更/キャンセルフロー中の「変更したい」の扱い）。

## 正本・parity
- Python オラクル: `modules/go_back_classifier/oracle.py`
- JS テンプレート（正本）: `docs/brekeke/script_templates/go_back_classifier.js`（Nashorn ES5.1・同一辞書/同一手順）

## DoD 進捗
1. REQUIREMENTS.md — 本書 ✅
2. Python オラクル + test_oracle.py — **20/20 PASS** ✅
3. Brekeke 実機受入（Pattern 6） — ✅ **20/20 PASS**（2026-06-17・call 09065765660・戻る9/繰り返し6/NONE5・`[TEST FAIL]` 0・`終了:OK`）
4. オラクル↔Nashorn パリティ確認 — ✅ 全20一致（実機 clf 出力 == oracle 期待）
5. `modules/README.md` 認定登録 — ✅ 登録済（2026-06-17）
