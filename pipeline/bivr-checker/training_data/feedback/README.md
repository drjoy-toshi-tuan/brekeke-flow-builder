# feedback/ — 品質向上用フィードバックデータ

## フォルダ構成

```
feedback/
├── corrections/              # VFB生成→人手修正の差分ペア【最優先】
│   └── {施設名}/
│       ├── draft_xxx.json    # VFB生成直後のフローJSON
│       ├── final_xxx.json    # 人手修正後の最終版フローJSON
│       └── notes.md          # 何を・なぜ直したかのメモ（任意）
│
├── review_reports/           # VFBの校閲レポート
│   └── review_report_xxx.md  # @reviewer が出力したレポート
│
├── prompts_reference/        # OpenAIプロンプトの実例
│   └── {種別}_xxx.txt        # 用件分類、診療科判定、氏名正規化 等
│
├── subflow_references/       # サブフローのリファレンス.bivr
│   ├── 個人情報サブフロー.bivr
│   └── サブフローRAG.bivr
│
└── production_feedback/      # 本番稼働後のフィードバック
    └── {施設名}_feedback.md  # 運用で発見された問題・改善点
```

## 格納方法

### corrections/（最も品質向上に効く）
1. 施設名のフォルダを作成（例: `corrections/琉球大学病院/`）
2. VFB生成直後のJSON（`draft_` or `prompted_` プレフィックス）を配置
3. 人手修正後の最終版JSON（`final_` or `reviewed_` プレフィックス）を配置
4. 可能であれば `notes.md` に修正理由を記載

### その他
- ファイルを該当フォルダに置くだけでOK
- ファイル名の規則は自由（施設名が含まれていれば十分）
