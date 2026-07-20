# 作業レポート: 中之島CL$健診 フロー生成

## 実施日
2026-03-24

## 概要
中之島クリニック 健診フローのIVR JSON をゼロから生成し、検証・BIVRビルドまで完了した。

---

## 成果物

| ファイル | 説明 |
|---|---|
| `output/中之島CL_健診_draft.json` | フローJSON（minified 1行） |
| `output/中之島CL.bivr` | Brekekeインポート用BIVRパッケージ |

---

## フロー構成サマリー

- **フロー名**: `中之島CL$健診`
- **startモジュール**: `冒頭`
- **総モジュール数**: 82

### モジュール内訳

| タイプ | 数 |
|---|---|
| TTS (Text to speech) | 14 |
| DTMF AmiVoice STT Input | 8 |
| AmiVoice Speech to Text | 4 |
| generate_by_OpenAI | 12 |
| Speech Retry Counter | 12 |
| saveContext2DB | 10 |
| saveCompletionFlag2db | 3 |
| saveContextModel2DB | 1 |
| acceptance_times | 1 |
| incoming-classifier | 1 |
| save2db (サブモジュール) | 13 |
| Disconnect | 4 |
| wait | 1 |
| **合計** | **82** |

---

## フロー設計の主要決定事項

### 1. saveContextModel2DB の fields
設計書指定の7コンテキスト（clinicalDepartment, classification, full-body_checkup, patientName, additionalPhoneNumber, reason, status）を定義した。

### 2. 営業時間チェック (acceptance_times)
設計書に従い `^open$` / `^closed$` の2分岐で実装した（参照ドキュメントでは `^true$`/`^false$` だが設計書指定を優先）。

### 3. incoming-classifier の分岐
- `^非通知$` → 非通知_アナウンス → 切断_非通知
- `^固定$`, `^携帯$`, `^.*$` → 施設_案内（通常フロー）
（設計書の「非通知 / 通常・携帯・固定」に対応）

### 4. saveContext_classification の役割
OpenAI_用件の結果（classification コンテキスト）を参照して、人間ドック / その他 の2ルートに分岐する saveContext2DB モジュールとして実装した。contextValue に `<%classification%>` を設定し、next条件で `^人間ドック$` / `^その他$` を分岐させている。

### 5. 電話番号リトライ回数
設計書指定通り `retry_count="2"`（計3回チャンス）を全電話番号系リトライに設定した。

### 6. completeflag の smsFlag
- `completeflag_ドック`: status="1", smsFlag="" （IVRプロパティで施設ごとに設定）
- `completeflag_その他`: status="1", smsFlag="" （IVRプロパティで施設ごとに設定）
- `END_上限エラー`（saveCompletionFlag2db）: status="2", smsFlag="0"

### 7. 電話番号訂正フロー
否定回答後は電話番号訂正TTS → STT → OpenAI → saveContext2DB → 電話番号確認_案内（ループ）の構成とした。
ループポイントは `電話番号確認_案内_ドック` / `電話番号確認_案内_その他` への直接戻りで実現。

### 8. save2db サブモジュール
全TTS・STT・Retry Counterモジュールに save2db を subs 経由で接続した（13種類）。
subs接続のルール（next連鎖禁止）を遵守し、modules に全定義を記載した。

### 9. 氏名・問合せ入力 STT タイプ
数字入力の不要な氏名・問合せ内容は `drjoy^AmiVoice$Speech to Text`、数字入力がある施設・用件・電話番号は `drjoy^External Integration$DTMF AmiVoice STT Input` を使用した。

---

## バリデーション結果

```
[REPORT] バリデーション完了: 中之島CL$健診
モジュール数: 82
問題発見数: 0
  [Critical]: 0
  [Warning]:  0
  [Info]:     0
判定: [PASS]
```

---

## BIVRビルド結果

```
[OK] 出力完了: output/中之島CL.bivr
     フロー数: 1
     - 中之島CL$健診 (82 modules)
```

---

## 注意事項・次のステップ

1. **IVRプロパティの設定が必要**: TTS発話テキスト、APIエンドポイントURL、AmiVoice設定はすべてIVRプロパティ側で設定すること。
2. **smsFlag の施設別設定**: completeflag_ドック / completeflag_その他 の smsFlag は IVRプロパティで施設ごとに設定する（6パターン対応）。
3. **acceptance_times の時間帯設定**: IVRプロパティ側で営業時間を設定すること。
4. **テスト推奨項目**:
   - 各施設選択（1/2/3 + 音声）の正常分岐
   - 人間ドック / その他 の用件分岐
   - 電話番号リトライ3回→上限エラーへの遷移
   - 電話番号確認で否定→訂正→再確認のループ
   - 非通知からの入電遮断
   - 時間外からの入電案内
