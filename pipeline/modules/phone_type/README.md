# phone_type

電話番号 → 回線種別（携帯 / 固定 / その他）の決定論判定 `@General$Script` 部品（050=その他）。

## 使い方

`slot: phone` の決定論インライン展開で scaffold が自動配線する（携帯路 = ANI 直、手入力路 = 復唱後）。
直接組み込む場合は `build_phone_type_script(name, source_module, mobile_next, fixed_next, other_next)`。

- 入力: 直前の番号入力モジュール（`SOURCE_MODULE`）の module-result
- 出力: `"携帯"` / `"固定"` / `"その他"` を setResult → 後段で分岐

## 構成

```
phone_type/
├── REQUIREMENTS.md   仕様（判定規則・エッジケース）
├── README.md         本ファイル
├── script.js         Brekeke IVR Script 本体（正本・@part-id マーカー付き）
├── oracle.py         Python オラクル（判定規則の独立実装）
├── test_oracle.py    oracle ↔ cases.tsv 照合テスト
└── acceptance_test/
    └── cases.tsv     受入ケース（テストが正）
```

## テスト

```
python modules/phone_type/test_oracle.py   # oracle 受入 20/20 PASS
```

## 受入実績

- oracle 受入 **20/20 PASS**（2026-06-17・050=その他 / フリーダイヤル / 国際表記 / 桁不足 含む）
- 認定（二段判定ゲート v2）: engine_version v1、spec_label `050=その他` を `certified_hashes.json` に登録
- 実機受入（Pattern 6 単体）: **未実施**（フラット化 2C の厚木 1flow 再生成時に実機照合予定）
