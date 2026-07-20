# BusinessHour Classifier

着信日時を施設の営業ルール (曜日別営業時間 + 固定休 + 祝日扱い) と照合し、6 分岐に仕分ける Brekeke モジュール。

`Incoming$DateOfCall Classifier` (時刻 hh:mm:ss 比較のみ) の後継として、曜日 × 時間帯 × 祝日 × 固定休を 1 モジュールに統合した設計。設計議論経緯: [[project_4layer_responsibility_model]] 分岐層。

## ファイル

| ファイル | 役割 |
|---|---|
| `script.js` | Brekeke (Nashorn) で動作する本体ロジック |
| `build_bivr.py` | params/jumps を組み込んで `BusinessHourClassifier.bivr` (zip) を生成 |
| `BusinessHourClassifier.bivr` | Brekeke にインポートするモジュール本体 |
| `oracle.py` | 同等ロジックの Python ポート (テストオラクル) |
| `test_oracle.py` | 21 受け入れケース |

## モジュール仕様

- **type**: `drjoy^Incoming$BusinessHour Classifier`
- **params**:
  - `target_datetime`: `now` (既定) / `<%var%>` / `yyyy-MM-dd[ HH:mm[:ss]]`
  - `weekday_schedule`: 曜日別営業時間 (既定: 平日 9-18 / 土日 closed)
  - `closed_dates`: 固定休 mm-dd 列 (既定: `12-29,12-30,12-31,01-02,01-03`)
  - `national_holiday`: `closed` (既定) / `open`
  - `holiday_note_name`: Brekeke Note 名 (既定: `drjoy.holidays`、単一 Note 多年構造)
- **祝日データソース**: Brekeke 管理画面の **単一 Note** に **多年分を 1 行 1 件 yyyy-MM-dd** で記載。例: テナント `drjoy` 配下に Note `holidays` を新規作成 → 当年 + 翌年の祝日を貼る (Note 名は外部から `drjoy.holidays` で参照)。外部 HTTP 通信ゼロ
- **なぜ単一 Note 多年構造か**: 「翌年の予約電話が当年中に普通に入ってくる」業務特性 ([[project_business_hour_classifier]] 2026-05-29 確定)。年単位に分けると「来年分の Note を作り忘れる事故」のリスクが残るが、単一 Note なら「年初に末尾追記」のみで構造的に防げる
- **jumps** (6): `^営業中$` / `^営業時間外$` / `^定休日$` / `^祝日$` / `^固定休$` / `^ERROR$`

## ローカル検証

```
PYTHONIOENCODING=utf-8 python test_oracle.py
```

21/21 PASS で全 6 分岐到達と境界値 (open 包含 / close 排他) を確認。

## Brekeke 実機検証手順

1. **本番 Note 作成**: Brekeke 管理画面でテナント `drjoy` 配下に Note `holidays` を新規作成し、当年 + 翌年の祝日を 1 行 1 件 yyyy-MM-dd 形式で貼り付け。外部参照名は `drjoy.holidays`
2. `BusinessHourClassifier.bivr` を Brekeke の Module パレットに import
3. 任意のテストフローに 1 モジュール配置、`target_datetime` を順次切り替え
4. 6 jumps の遷移先を観測 (Termination モジュールにそれぞれ接続するか、Script で `$runner.getLogger().info()` を仕掛けて log で確認)
5. 必要なら Pattern 6 ([[project_pattern_6_test_flow]]) に block 型として組み込み、21 ケース自動化

## 年次運用フロー (祝日 Note の更新、3 月実施)

**データソース**: 内閣府公式 CSV (CC-BY ライセンス、責任: 内閣府大臣官房総務課、更新頻度: 1 年)
- CSV URL: `https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv` (Shift_JIS, yyyy/m/d 形式, 1955-翌年分まで)
- CKAN メタデータ: `https://data.e-gov.go.jp/data/api/action/package_show?id=cao_20190522_0002`

**運用ステップ (毎年 3 月初旬)**:

```bash
# 1. CSV を取得して 当年 + 翌年分を yyyy-MM-dd 形式に整形してファイル出力
cd voicebot-flow-builder/modules/business_hour_classifier
python fetch_jp_holidays.py -o holidays.txt
#   → holidays.txt に 35 行前後 (当年 17-18 + 翌年 17-18)

# 2. holidays.txt をエディタで開いて全文選択コピー
#    (Windows なら一気にクリップボードに乗せる経路もある:)
python fetch_jp_holidays.py | clip

# 3. Brekeke 管理画面で Note `drjoy.holidays` を開く → 末尾に追記 → 保存
#    既存の古い年データは当面残置 (過去予約照会対応のため)。3-5 年以上経過した行は手動削除可
```

**スクリプト挙動**:

```bash
python fetch_jp_holidays.py                 # 当年 + 翌年 (既定、3 月の標準運用)
python fetch_jp_holidays.py 2027            # 指定年のみ
python fetch_jp_holidays.py 2026 2027       # 範囲指定 (両端含む)
python fetch_jp_holidays.py --all           # CSV 全件 (1955-翌年)
python fetch_jp_holidays.py --with-name     # 祝日名併記 (yyyy-MM-dd,元日)
```

**実行タイミング**:
- 内閣府が翌年分を CSV に追記して公開するのは **毎年 2 月**
- **3 月実施で前年中の翌年予約対応に余裕** (実際は前年 11-12 月までに準備しておく方が安全)
- 「年初に当年分から追記しはじめる」では翌年予約が祝日扱いされず通り抜けバグ発生

**含まれるもの (内閣府 CSV ベースの法律完全準拠)**:
- 通常祝日 (元日, 成人の日, 建国記念の日, ...)
- 振替休日 (祝日が日曜の翌平日)
- 国民の休日 (祝日に挟まれた平日、例: 2026-09-22 = 敬老の日 9/21 月 と 秋分の日 9/23 水 の間の火曜日)
- 春分/秋分の日 (国立天文台が前年 2 月に確定)

**SSL 検証 (社内 TLS インスペクション環境向け)**:
fetch_jp_holidays.py は Windows 証明書ストア + `VERIFY_X509_STRICT` 解除を内蔵 ([[feedback_tls_inspection_corp_pc]] 準拠)。会社 PC でそのまま動く。本番 CCR/Linux でも no-op フォールバックで certifi のみ使用に倒れる

## 既知の制約

- 祝日リストは Brekeke Note `drjoy.holidays` (単一、多年同居) を `com.brekeke.pbx.common.NoteUtils.read` 経由で取得。外部 HTTP 依存なし。年初に Brekeke 管理画面 UI で **末尾に翌年分 17 行を追記** すれば全フローに即時反映 (古い年の行は当面残置 OK、過去予約照会に対応可能)
- Note 不在/読取り失敗時は **fail-open** で曜日判定にフォールバックする (= ERROR にしない)。Note 不在は `WARN` ログのみ
- Brekeke 1 コール 1000 モジュール上限 ([[feedback_brekeke_max_module_execution_1000]]) に注意。本モジュール自体は 1 module。Pattern 6 全 21 ケース連結時は終端含めて ~80 modules 前後の見込み
- Brekeke Module Output は string 化される ([[feedback_brekeke_module_output_stringified]]) が、本モジュールは元々 string を返すので影響なし
- NoteUtils API シグネチャは `Notes API Probe` で empirical 検証済み (2026-05-29): `Java.type("com.brekeke.pbx.common.NoteUtils").read("<tenant>.<note_name>")` が動作。`notes_probe/` 配下に当時の証跡保存
