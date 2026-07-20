# INC-260716-2: BIVR出力レビューで判明したscaffold_generator.py設計課題（施設担当者フィードバック）

## 症状 / 影響
カレス記念病院_診療のビルド済みBIVRを施設担当者がレビューし、以下4点の実装課題を発見。
いずれも「エラーにはならないが実運用で不都合」なクラスの問題で、機械チェックでは検出できない。

1. **phone slotを2ブロックに分けると分岐一式が二重生成される**: 設計書で
   `連絡先番号（携帯電話）`/`連絡先番号（固定電話）`のように`type: phone`を2つ書くと、
   phone slotが内部で持つ着信分類（携帯→ANI路 / 固定・その他→連絡先路）が
   **それぞれのブロックに独立生成**され、BIVR上でphone分岐一式が2回登場していた。
2. **電話番号ANI再確認チェーンの否定応答で新番号が握りつぶされる**: 「いいえ、08012345678です」
   のように否定語＋新番号が同一発話に含まれる場合、yes_no_classifierが「否定」を確信を持って
   判定し即座に連絡先聴取路（ゼロから聴取）へ分岐してしまい、発話に含まれていた新番号を
   スキップしていた。正しい優先順位は「まず番号抽出を試みる→取れなければ連絡先路」。
3. **announcementブロックにsave2dbが不要生成されていた**: TTSのみ（STTを伴わない）の
   announcementブロックで、どこからも参照されない`save-{step}`のsave2dbモジュールが
   毎回生成されていた（build_ttsにsave_subを渡していないため誰も参照しない死にモジュール）。
4. **FAQ/OpenAIフォールバックのプレースホルダに文字通り"TODO_scaffold"が残っていた**:
   希望日系・FAQ未整備時のOpenAIフォールバックスクリプトが、分岐ラベルの無い単純ケースでも
   一律「TODO_scaffold」を埋め込んでおり、実際には安全なNO_RESULT固定という正しい既定動作
   なのにvalidator.py SCR-007がCRITICAL誤検知していた（INC-260716-1にも一部関連）。

## 原因
- phone slotの「1ブロックで携帯/固定両方を内部分岐する」設計仕様が、
  `docs/brekeke/モジュール選定ガイド_v2.md`等のドキュメントに明記されておらず、
  新規シナリオ作成時に「携帯用」「固定用」と誤って2ブロックに分けやすい構造だった。
- yes_no_classifierの否定判定を「即終了」として扱っており、同一発話内の追加情報
  （新しい電話番号）を後続で拾う設計になっていなかった。
- announcementのsave2dbはコピペ由来の過剰生成（他のブロック型ではsave_subとして
  実際に参照されるが、announcementでは参照元が無い）。
- OpenAI/Scriptフォールバックのテンプレート文言が「常にprompterが埋める前提」で
  書かれており、「分岐ラベルが無い＝そもそも埋める作業が発生しない」ケースを
  区別していなかった。

## 対策（着地先と階層）
- **① 機械ゲート**:
  1. `schemas/qa_validator.py` に **F-10** を新設: `type: phone/dob/patient_name/
     card_number` が同一 save_to（または同型で複数）scenario_flow に存在する場合 WARNING。
     カレス記念病院_診療は1ブロックに統合済み（本チェックで0件を確認）。
  2. `scripts/scaffold_generator.py` slot phone: `ani_yes_no`/`contact_yes_no`の
     `deny_next`を`contact_tts`直行から`ani_sv_norm`/`contact_sv_norm`（言い直し番号
     サルベージ）経由に変更。NO_RESULTと同じ扱いにして番号抽出を先に試みる。
  3. `scripts/scaffold_generator.py` `_build_announcement`相当（`btype=="announcement"`）:
     素のTTSのみのケースで`build_save2db(f"save-{step}")`の生成を削除。
  4. `scripts/scaffold_generator.py` `_build_free_text_block`/`_build_faq_block`（method:
     script/openai両方）/`build_openai`: フォールバック本体・OpenAIプロンプトの
     「TODO_scaffold」プレースホルダを、分岐ラベルが無い/FAQデータが空の場合は
     「意図した安全な既定動作」である旨を明記したコメント・デフォルトプロンプトへ差し替え。
- **④ 文書（フォローアップ推奨）**: `docs/brekeke/モジュール選定ガイド_v2.md`に
  「phone slotは1ブロックで携帯/固定両方を内部分岐する。2ブロックに分けない」旨を明記する
  余地あり（本セッションでは未実施）。

## 再発防止ゲート
あり（全項目）。
- 項目1: `schemas/qa_validator.py` F-10（新設）。
- 項目2〜4: `scripts/scaffold_generator.py` 本体修正のため、次回以降のシナリオで自動的に正しく動作する。
