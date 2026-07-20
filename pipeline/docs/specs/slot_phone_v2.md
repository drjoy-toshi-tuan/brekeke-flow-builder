# slot: phone v2 — 電話番号スロットの改訂仕様（壁打ち確定用ドラフト）

> 状態: **実装済み（2026-07-14 承認 → scaffold/gen_properties/layout 反映）**。
> 実機 P6/P7 再受入は未実施（engine 変更 = 再受入対象・人間ゲート）。
> 根拠モジュール: `modules/phone_normalizer/module_value.js`（Phone Normalization）。

## v1 からの変更方針（4 点）

1. **ANI 路は Phone Normalization の CASE B（module 空）を使う**
   - v1: `save_context_fixed(ANI)` → Phone Normalization CASE A → Re-confirmation node data
   - v2: incoming-classifier(携帯) → **Phone Normalization（module 空・prompt 空）** → TTS 復唱
   - CASE B が着信番号の取得・DB 保存・`additionalPhoneNumber` / `incoming_phone` / `phone_type`
     の setObject までを 1 モジュールで行うため、save_context_fixed と Re-confirmation を削減できる。

2. **復唱はすべて「素の TTS ノード + オブジェクト参照」に統一（Re-confirmation node data 廃止）**
   - 読み上げ変数: **`<%additionalPhoneNumber%>`**（CASE A / CASE B とも setObject される — 統一参照）
   - GOOGLE TTS: `{tts_g:ご連絡先の電話番号は、<speak><say-as interpret-as="telephone"><%additionalPhoneNumber%></say-as></speak>、でよろしいですか？…}`
   - **TTS 文言はすべて IVR プロパティ側で定義**（scaffold にハードコードしない）。
     gen_properties.py が復唱行も含めて 1 ファイルに列挙 → 人間が一括点検できる。
   - Phone Normalization 自体の prompt は**空**にして発話させない
     （module は `prompt` 非空のときだけ play する実装 — module_value.js CASE A/B 共通）。

3. **はい/いいえ 不一致（NO_RESULT）時の「言い直し番号」1 回サルベージ**
   - yes_no_classifier が NO_RESULT のとき、同じ発話を Phone Normalization **CASE A**
     （module=確認 STT）に 1 回だけ通す:
     - 有効番号（0 始まり 10/11 桁）→ その番号で TTS 復唱 → はい/いいえ へ戻る
     - INVALID / NO_RESULT → 連絡先聴取路へ進む（ANI 路）/ 通常リトライ（連絡先路）
   - **ループは 1 回のみ**（フラグ管理）。2 回目以降の NO_RESULT は従来どおり retry を消費する。
   - 狙い: 「いいえ、090-XXXX-XXXX です」のように**復唱への返答で新しい番号を直接言う**
     患者を聞き直しなしで受ける。

4. **連絡先路の復唱も同一パターン**（STT → Phone Normalization(CASE A・prompt 空) →
   TTS `<%additionalPhoneNumber%>` → はい/いいえ → yes_no_classifier）。

5. **phone_type / phonetype の設定ロジックを廃止**
   - v1: 認定 `phone_type` script + `設定_phonetype携帯/その他`（saveContext 固定値）→ 終話分岐が `<%phonetype%>` を参照
   - v2: **携帯/固定の分岐が必要な箇所でだけ Module Result Binder + 正規表現で直接判定**する
     （対象 = `additionalPhoneNumber`。例: `^0[789]0` → 携帯 / catch-all → その他）。
   - 中間 context（phonetype）を持たない分だけモジュール・状態が減り、
     判定はいつでも実番号から再現できる（値のコピーを増やさない）。
   - module が setObject する `phone_type`（mobile/landline）は使わない（参照禁止ではないが、
     分岐正本は MRB regex とする — 判定ロジックを 1 か所に固定）。

## 必須条件（実装制約）

- Phone Normalization の `saveAdditionalPhoneNumber2DB` = **yes** 必須
  （no だと CASE A が `additionalPhoneNumber` を setObject しない → TTS が空読みになる）。
- **`#data#` は Phone Normalization モジュール内部変数**: module 自身の prompt の中でのみ
  置換・再生される（`prompt.replaceAll("#data#", ...)` → module 内 `$ivr.play`）。
  **外部 TTS ノードでは使えない**。したがって「module prompt 空 + 外部 TTS」構成では
  読み上げ変数はオブジェクト参照（`<%additionalPhoneNumber%>` / CASE B のみ `<%incoming_phone%>`）に限る。
- **AI_TALK（SSML 非対応）施設の読み上げ**: `additionalPhoneNumber` は生数字連結
  （例: 09012345678）のため say-as なしでは不自然読みになる。AI_TALK では:
  - ANI 路（CASE B）: 整形済みオブジェクト `<%incoming_phone%>`（phoneReadingMode 整形）を外部 TTS で読む
  - 連絡先路（CASE A）: 整形済みオブジェクトが無いため、**module の prompt に文言を設定して
    `#data#` で module に読ませる**（この場合のみ module prompt 非空 = module 発話。
    文言はプロパティで module prompt を上書きして管理する）
  - GOOGLE は両路とも外部 TTS + `<%additionalPhoneNumber%>` + say-as telephone で統一（issue #217 踏襲）
- INVALID の扱い: CASE A は 0 始まりでない・桁数不正の番号を INVALID にする。
  サルベージ判定で INVALID の場合は「番号を言い直した」とみなさず通常フローへ。
- リトライ会計: サルベージ 1 回は retry_count と別枠のフラグで管理するが、
  **総発話ターン数が v1 + 2 を超えない**こと（1 コール 1000 モジュール上限・UX 3 回ルール）。

## モジュール鎖（v2 案）

```
着信分類 (incoming-classifier)
├─ 携帯 → PhoneNorm(CASE B, prompt空)            … additionalPhoneNumber/phone_type setObject
│          → TTS復唱 <%additionalPhoneNumber%> → STT(はい/いいえ)
│          → yes_no_classifier
│             ├ はい  → next
│             ├ いいえ → 連絡先聴取路へ
│             └ NO_RESULT → [1回のみ] PhoneNorm(CASE A, 対象=確認STT)
│                  ├ 有効 → TTS復唱(新番号) → STT(はい/いいえ) へ戻る
│                  └ INVALID/NO_RESULT → 連絡先聴取路へ
└─ 固定/非通知/海外/WebRTC/その他 → TTS聴取 → STT(番号 11桁 DTMF+音声)
       → PhoneNorm(CASE A, prompt空)
          ├ 成功 → TTS復唱 <%additionalPhoneNumber%> → STT(はい/いいえ) → yes_no_classifier
          │        ├ はい  → next
          │        ├ いいえ → 再聴取（リトライ枯渇 → ANI フォールバック）
          │        └ NO_RESULT → [1回のみ] 言い直し番号サルベージ（上と同じ）
          └ INVALID/NO_RESULT → [next_no_phone 指定時: なし判定 MRB] → リトライ

※ 携帯/固定で分岐したい箇所（SMS 可否の終話分岐等）は、その場で
   MRB(additionalPhoneNumber) + regex（^0[789]0 → 携帯 / ^.*$ → その他）を置く。
   phonetype context・phone_type script は生成しない。
```

## v1 から削減されるもの / 残るもの

| 削減 | 残る |
|---|---|
| save_context_fixed(ANI 転記) — CASE B が代替 | incoming-classifier（回線種別の入口分岐） |
| Re-confirmation node data ×2 — TTS+object で代替 | yes_no_classifier（認定部品） |
| scaffold ハードコードの復唱 SSML — property へ移動 | ANI フォールバック（リトライ枯渇時） / next_no_phone MRB |
| phone_type script + 設定_phonetype携帯/その他 — 必要箇所で MRB+regex 直判定 | 携帯/固定分岐が必要な箇所の MRB（additionalPhoneNumber 正規表現） |

## 影響範囲（実装時に同 PR で更新するもの）

- `scripts/scaffold_generator.py` `_build_slot` (phone) — 鎖の組み替え
- `scripts/gen_properties.py` — 復唱 TTS 行の property 出力（resolve_slot_tts_defaults 同期）
- `schemas/qa_validator.py` I-7 — slot phone の主要 TTS モジュール名の解決規則更新
- **終話分岐（SMS 可否）**: v1 の `context_match_router reference_module: phonetype`（`<%phonetype%>` 参照）は
  廃止 → `MRB(additionalPhoneNumber) + regex` に組み替え。既存設計書テンプレ・
  モジュール選定ガイドの該当例も追随更新（#303 dead slot チェックの参照先も確認）
- P6/P7: 変更後は連結テスト再実行（engine 変更 = 再受入対象）
