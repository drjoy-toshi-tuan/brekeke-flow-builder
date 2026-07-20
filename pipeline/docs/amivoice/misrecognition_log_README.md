# misrecognition_log.csv — 実ログ由来の誤認識補正

AmiVoice STT が実通話で誤認識したペアを蓄積するマスターファイル。  
`tools/gen_amivoice_dict.py --log` で読み込み、単語登録 CSV に反映される。

## カラム

| カラム | 必須 | 説明 |
|---|---|---|
| `wrong` | ✓ | AmiVoice が誤認識した結果（STT ログの actual 値） |
| `correct` | ✓ | 本来認識されるべき正しい単語 |
| `count` | ✓ | 誤認識件数（5件以上で priority=high に自動昇格） |
| `note` | | 備考（音響的混同理由・発生条件など） |
| `target_nodes` | | 配布先ノード名（`\|` 区切り。省略時は全ノードに配布） |

## ログの集め方

1. `tools/extract-yesno-synonyms` スキル → 実通話ログから wrong/correct ペアを抽出
2. このファイルに追記
3. `tools/gen_amivoice_dict.py --log docs/amivoice/misrecognition_log.csv` で再生成

## 施設固有の上書き

施設ごとの例外キーワードは `output/scenarios/{施設}_{flow}/keyword_custom.json` に記述する。  
このファイルは共通マスターなので施設依存情報は書かない。
