# Script Templates

scaffold_generator が `params.script` に埋め込む JavaScript テンプレート。
設計書の `script` ブロックに `script_template` を指定すると、対応するテンプレートが読み込まれてプレースホルダーが置換される。

## 利用可能なテンプレート

| テンプレート | 用途 | プレースホルダー | 出力値 |
|---|---|---|---|
| `future_date` | 入力日付が今日より未来か判定 | `{{INPUT_MODULE}}` | SUCCESS / FAIL |
| `phone_type` | 電話番号を携帯/固定/その他に分類 | `{{INPUT_MODULE}}` | 携帯 / 固定 / その他 |
| `day_of_week` | 現在の曜日判定 | （なし） | 平日 / 土曜 / 日曜祝日 |
| `business_hours` | 営業時間内か判定 | `{{START_HOUR}}` / `{{END_HOUR}}` | 営業時間内 / 営業時間外 |
| `condition_group` | 多段分岐のグループ分類 | `{{INPUT_MODULE}}` / `{{MAPPING}}` / `{{DEFAULT_GROUP}}` | グループ番号 ("1"〜"10") |

## 設計書での記述例

```yaml
- step: 営業日判定
  type: script
  script_template: future_date
  reference_module: "OpenAI_変更希望日"  # {{INPUT_MODULE}} に置換
  conditions:
    - match: "SUCCESS"
      next: 予約確定
    - match: "FAIL"
      next: 営業日エラー案内
```

## カスタムスクリプト

`script_template` を指定しない or `script_template: custom` の場合、scaffold_generator は `params.script` に `// TODO_script: ここにスクリプトを記述してください` のマーカーを残す。
人間 or fixer が後段で記述する。

## テンプレート追加方法

1. このディレクトリに `{name}.js` を作成
2. プレースホルダーは `{{NAME}}` 形式で記述
3. README の表に追加
