# n_choice — 要件定義（N択分類 決定論エンジン）

## 目的
DTMF（プッシュ番号）または音声キーワードで N 択メニューを**決定論的に**判定する汎用 Script。
OpenAI（generate_by_OpenAI）を使わずに「発信元区分」「患者区分」「相談種別」等の選択式聴取を解く。

> 注: 本リポジトリの成果物は **Script モジュールに入れる JS 本体（`script.js`）＋ oracle 認定**まで。
> Brekeke 上の実モジュール化（@General$Script の構築・フロー組込）は人手の別工程。

## 入出力
- **入力**: 直前の STT / DTMF 入力モジュールの結果（`$runner.getResult(INPUT_MODULE)`）。
- **出力**: 設定した選択肢ラベルのいずれか、または `NO_RESULT`（再質問へ）。
- **副作用**: `CONTEXT_NAME` に結果を saveContext2DB + setObject、checkpoint を IN/OUT で記録。

## 設定（テンプレート＝設問ごとに充填する「設定行」。hash 認定では除外対象）
| トークン | 内容 |
|---|---|
| `{{INPUT_MODULE}}` | 直前の入力モジュール名 |
| `{{CONTEXT_NAME}}` / `{{CONTEXT_DISPLAY_TYPE}}` | 保存先 context 名 / displayType |
| `{{DTMF_MAP}}` | `{"1":"ラベルA",...}` 数字→ラベル |
| `{{TOKEN_MAP}}` | `[{regex,result},...]` 完全一致トークン |
| `{{DIGIT_KEYWORD_PATTERNS}}` | `[{digit,regex,result},...]` 先頭数字＋語 |
| `{{COMPOUND_PATTERNS}}` | `[{regex,result},...]` 複合語（keyword より先に評価）|
| `{{KEYWORD_PATTERNS}}` | `[{regex,result},...]` 単独キーワード |

## 判定順（script.js / oracle.py 共通・厳守）
1. 入力が空 → `NO_RESULT`
2. **正規化**（下記）→ 空になれば `NO_RESULT`
3. 正規化後が単一数字 → `DTMF_MAP`（未定義の数字は `NO_RESULT`）
4. `TOKEN_MAP` 完全一致
5. 先頭数字 ＋ `DIGIT_KEYWORD_PATTERNS`
6. `COMPOUND_PATTERNS`（複合語を keyword より先に）
7. `KEYWORD_PATTERNS`（**配列順で先勝ち**＝優先度は配列順で表現）
8. フィラーのみ → `NO_RESULT`
9. いずれも不一致 → `NO_RESULT`

## 正規化（script.js と 1:1）
- 全角数字 `０-９` → 半角
- 記号・空白除去 `、。,.:;!?！？「」『』（）()`＋空白類
- 先頭・末尾のフィラー除去（えーと/あのー/うーん 等）
- 方言・敬語・タメ口の接尾辞除去（〜けん/〜やん/〜です/〜お願いします 等）
- AmiVoice カテゴリ重複正規化（「再診再診」→「再診」）
- 数字＋語尾 trim（「1です」→「1」）

## エッジケース
- 空 / 正規化後空 → `NO_RESULT`
- 無効数字（DTMF_MAP に無い数字）→ `NO_RESULT`
- フィラーのみ / 無関連発話 → `NO_RESULT`
- 同一カテゴリ語の AmiVoice 重複 → 1 回に畳んで判定
- 複数ラベルに該当しうる語 → **配列順で先勝ち**（設定側で優先度を順序で表現する）

## 既定シノニム注入（生成側・#279 ①③）

n_choice はエンジンにデフォルト辞書を持たず設定を毎回充填するため、施設ごとに同じ取りこぼしが再発した
（恵佑会札幌 診療: 「2番」→NO_RESULT / 「持ってます」→NO_RESULT）。`scaffold_generator._enrich_nchoice_config`
が n_choice ブロック生成時に **spec（template_params）を決定論的に既定拡張**する（**engine は無改変**・追記のみ・冪等）:
- **③ 数字選択の音声表記**: DTMF_MAP の数字キー（1-9）→ TOKEN_MAP に `N番 / 音読み / 漢数字（+番）` を自動付与。
  DTMF branch と別経路の音声「2番 / にばん / 二番 / 二」等を回収（全角「２」は既に DTMF branch で解決済み）。
- **① 所持表現**: KEYWORD/COMPOUND_PATTERNS の `result` が有無ラベル（あり/有/有り/ある ・ なし/無/無し/ない）
  → regex に `持ってます|もってます`（あり側）/`持ってません|もってません`（なし側）を追記（result ラベル駆動＝推論なし）。
- author が既に同等を書いた選択肢は skip（冪等・上書きしない）。JSON パース不能な spec は触らない（安全側）。
- **spec_hash 影響**: 既存施設の n_choice を再 scaffold すると spec が変わる＝新 spec_hash → 施設別に再 P6（オーナーゲート）。engine_hash は不変。
- テスト: `scripts/test_enrich_nchoice_config.py`（enrich 単体＋enrich 後の oracle 分類 end-to-end）。

## 受入
- Python オラクル `oracle.py` ＋ `test_oracle.py`（`acceptance_test/cases.tsv`）全 PASS。
- Brekeke 実機受入（Pattern 6 テストフロー）＝**人手**。Nashorn↔Python パリティ確認込み（department_classifier と同手順）。
- 設定（DTMF_MAP/KEYWORD 等）は設問ごとに異なるため、**設定行を除外したエンジン部の hash で認定**し、各設問の充填済みケースは P6 で検証する。

## 由来
髙橋 VFB-Script `reference/scripts/n_choice.js`（v4）を VFB の DoD に載せた正本。
