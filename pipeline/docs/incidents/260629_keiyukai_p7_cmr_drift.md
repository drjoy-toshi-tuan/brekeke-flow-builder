# INC-260629-1: P7 連結テストBIVR が本体BIVR と乖離（恵佑会札幌病院）

## 症状 / 影響
- 本体 BIVR の CMR `終話分岐_用件` は `module1Name="script_用件確認"`（正）だが、
  実機テストに使った連結テスト BIVR では `module1Name="用件確認"`（古い TTS 参照）のまま。
- 「予約」「変更」判定は正しく出ているのに CMR が拾えず、ケース5/13 等が全て `その他_FIXED` 終端に倒れた。
- **実運用と異なる挙動をテストしていた** = テスト合格が品質保証にならない状態。

## 原因
- P7 ケース補完（subagent 経由の複雑処理）の中で、本体 BIVR の一時状態から
  テスト BIVR が再生成された、または生成後に CMR 部分だけ古い状態に書き戻された（正確な発生点は不明）。
- テスト BIVR と本体 BIVR の整合を機械検証する仕組みが無かった。

## 対策（着地先と階層）
- **① 機械ゲート**: `connection_test/verify_test_bivr.py` 新設
  - CMR params / next / subs / jump の突合。乖離で exit 1。
  - `stub_stt_connection.py` が生成直後に自動実行（SOURCE-CONSISTENCY）— 乖離した bivr は保存段階で fail。
  - 生成元 sha256 / cases sha256 / 生成日時を zip comment に埋め込み（出所追跡）。
- **③ Skill**: `p7-connection-test/SKILL.md` に Step 4.5（実機投入前の一発検証）と
  「本体 BIVR は一時的にも編集しない（subagent 含む）」を明記。

## 再発防止ゲート
あり — stub_stt_connection.py 内蔵の自動整合チェック + verify_test_bivr.py 単体実行。
CMR `module1Name` 改変を注入する再現テストで検出を確認済み（2026-07-15）。
