# INC-260716-1: CSV入口パイプライン（csv_to_yaml.py/raw_to_spec.py/scaffold_generator.py/layout）の複合バグ

## 症状 / 影響
カレス記念病院_診療（Pattern 1新規、CSV入口経由）のパイプラインで、qa_validator/validator.py
CRITICALが最終的に107件検出された。個々の原因は以下の通り複数の独立したバグの積み重ね。

1. **office_id/phone_number/business_hours反映漏れ**: csv_to_yaml.pyがSheet_Settings.csvの
   settings dictを読み込みながら、basic_info生成時にハードコードでTODOを上書きしていた。
2. **canonical_name衝突**: raw_to_spec.pyの辞書マッチが同一エントリに複数行がマッチすると、
   異なる意味のステップ（代表案内と通話切断ガイダンス、携帯/固定の連絡先番号等）が同一の
   canonical_nameになり、scenario_flow上で上書き事故になる。
3. **step_details.retry_failureの不正値**: csv_to_yaml.pyが`_retry_failure_target`をstep_details
   にも流用し、実ステップ名を返していた（許容値はskip/end_failure/disconnectのみ）。
4. **hearing_itemsにoutput_labels/save_toが欠落**: prompter（gen_prompts.py）はhearing_items
   経由でOpenAIプロンプトのラベルを埋めるが、csv_to_yaml.pyのhearing_items生成部がこの2フィールドを
   出力しておらず、enum hearingのOpenAIプロンプトが常に「0択」の空テンプレになっていた。
5. **layout_calculator.py/block_layout.py/block_layout_specがscenario_flowの新規既定パターンに
   未対応**: `type: intent/free_text/clinical_department/faq`や、`type: phone/dob/patient_name/
   card_number`をsubflowを介さず直書きするパターン（＝新規作成の既定）で、モジュールの94%超が
   「所属不明」になっていた。加えて前日追加されたREPEATフィルタ（script_repeat_filter_{step}）も
   layout未対応だった。
6. **scaffold_generator.py `_build_free_text_block`のdead end**: 正規化Scriptの「matched」分岐が
   save2db（次を持たない副層専用モジュール）をnextに指定しており、以降フローが止まっていた
   （score_bivr.py R-1で検出）。
7. **OpenAI TIMEOUT/ERRORフォールバックscriptの誤検知**: 分岐ラベルが無い単純ケース
   （希望日系・FAQ未整備時）でも一律「TODO_scaffold」コメントを埋め込んでおり、
   実際には安全なNO_RESULT固定という正しい既定動作なのにCRITICAL誤検知していた。

## 原因
- CSV入口経路（raw_to_spec.py → csv_to_yaml.py）は2026-07-15に導入されたばかりで、
  scaffold_generator.py / layout_calculator.py 側の「新規作成の既定パターン」対応が
  追いついていなかった（従来はdirector生成 or 個人情報4種のsubflow wrapper経由が主流だったため）。
- 個々の生成物は「エラーなく完走」するため、qa_validator/validator.pyのようなCRITICALベースの
  機械チェックを実際に走らせるまで発覚しなかった。

## 対策（着地先と階層）
- **① 機械ゲート**: 上記1〜7はすべて `tools/csv_to_yaml.py` / `tools/raw_to_spec.py` /
  `scripts/scaffold_generator.py` / `scripts/layout_calculator.py` / `scripts/block_layout.py` /
  `scripts/block_layout_spec.py` の本体修正で解消済み（feature/カレス記念病院_診療ブランチ、
  複数コミット）。138シナリオに対する回帰スイープ実施済み（別バグの検出はあったが本修正とは無関係と確認済み）。
- **④ 文書**: `tools/spec_template/記入ガイド.md` にUTF-8保存の注意・
  `csv_to_yaml.py --input`には`raw_to_spec.py`生成後のファイルを渡す旨・
  Sheet2_flowを使うべきでないケースの判断基準を追記済み。

## 再発防止ゲート
あり（②③⑤⑥⑦は次回csv入口シナリオで自動的に正しく動く。①④は138シナリオ回帰テストで
既存動作に影響なしを確認済み）。ただし今回のCSV入口シナリオ第1号での発見であり、
今後別施設で新しいブロック型の組み合わせが出た場合、同種の「未対応パターン」が
再発する可能性は残る（layout側は現状 hearing/intent/free_text/clinical_department/faq/
slot系のみカバー。新しいブロック型を追加する際はlayout側の対応漏れがないか要確認）。

## 別途記録した学び
- **エディタのUTF-8保存漏れによるデータ消失**（本セッション中に2回発生）: 恒久対策として
  `tools/spec_template/記入ガイド.md` に警告を追記済み。機械ゲート化（保存時の文字化け検出）は
  今回未着手 — 今後の検討課題。
