#!/bin/bash
# run_pipeline.sh — 生成→校閲→検品の一括実行スクリプト
#
# Usage:
#   ./scripts/run_pipeline.sh docs/設計書_〇〇病院_診療.md
#
# 処理フロー:
#   1. generator エージェントでJSON生成
#   2. reviewer エージェントで校閲
#   3. validator.py で自動検品
#   4. 成果物を Git コミット

set -euo pipefail

# ============================================================
# 設定
# ============================================================
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$PROJECT_DIR/output"

# 色付きログ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info()  { echo -e "${BLUE}[INFO]${NC}  $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================
# 引数チェック
# ============================================================
if [ $# -lt 1 ]; then
    echo "Usage: $0 <設計書.md>"
    echo ""
    echo "Example:"
    echo "  $0 docs/設計書_〇〇病院_診療.md"
    exit 1
fi

SPEC_FILE="$1"

if [ ! -f "$SPEC_FILE" ]; then
    log_error "設計書が見つかりません: $SPEC_FILE"
    exit 1
fi

# ============================================================
# Step 1: JSON生成
# ============================================================
log_info "Step 1/3: フローJSON生成中..."
log_info "設計書: $SPEC_FILE"

# Claude Code でgeneratorエージェントを実行
# ※ 実際のclaude コマンドの引数はClaude Codeのバージョンに依存
claude --agent generator \
    "docs/共通作業手順書.md と $SPEC_FILE を読み、examples/ を参考にフローJSONを生成して output/draft_ で始まるファイル名で保存してください" \
    2>&1 || {
    log_error "JSON生成に失敗しました"
    exit 1
}

# 生成されたdraftファイルを検出
DRAFT_FILE=$(ls -t "$OUTPUT_DIR"/draft_*.json 2>/dev/null | head -1)
if [ -z "$DRAFT_FILE" ]; then
    log_error "draft_*.json が生成されませんでした"
    exit 1
fi
log_ok "初稿生成完了: $DRAFT_FILE"

# ============================================================
# Step 2: 校閲
# ============================================================
log_info "Step 2/3: 校閲中..."

claude --agent reviewer \
    "$DRAFT_FILE を校閲して、修正済みファイルを output/reviewed_ で始まるファイル名で保存し、校閲レポートも output/review_report_ で保存してください。元の設計書は $SPEC_FILE です" \
    2>&1 || {
    log_error "校閲に失敗しました"
    exit 1
}

REVIEWED_FILE=$(ls -t "$OUTPUT_DIR"/reviewed_*.json 2>/dev/null | head -1)
if [ -z "$REVIEWED_FILE" ]; then
    log_warn "reviewed_*.json が見つかりません。draftファイルで検品を続行します"
    REVIEWED_FILE="$DRAFT_FILE"
fi
log_ok "校閲完了: $REVIEWED_FILE"

# ============================================================
# Step 3: バリデーション
# ============================================================
log_info "Step 3/3: バリデーション実行中..."

python3 "$PROJECT_DIR/schemas/validator.py" "$REVIEWED_FILE"
VALIDATION_RESULT=$?

if [ $VALIDATION_RESULT -ne 0 ]; then
    log_error "バリデーション失敗。上記のCriticalエラーを確認してください。"
    log_warn "修正後に再度実行するか、手動で修正してください。"
    exit 1
fi

log_ok "バリデーション通過！"

# ============================================================
# Step 4: Git コミット（リポジトリ内の場合）
# ============================================================
if git -C "$PROJECT_DIR" rev-parse --git-dir > /dev/null 2>&1; then
    log_info "Git コミット中..."

    cd "$PROJECT_DIR"
    git add "$REVIEWED_FILE"

    # 校閲レポートがあればコミット
    REPORT_FILE=$(ls -t "$OUTPUT_DIR"/review_report_*.md 2>/dev/null | head -1)
    if [ -n "$REPORT_FILE" ]; then
        git add "$REPORT_FILE"
    fi

    FLOW_NAME=$(python3 -c "
import json, sys
with open('$REVIEWED_FILE') as f:
    d = json.load(f)
print(d.get('name', 'unknown'))
" 2>/dev/null || echo "unknown")

    git commit -m "[pipeline] $FLOW_NAME 生成・校閲・検品完了"
    log_ok "Git コミット完了"
else
    log_warn "Gitリポジトリではないため、コミットをスキップしました"
fi

# ============================================================
# 完了
# ============================================================
echo ""
echo "=========================================="
echo -e "${GREEN}✅ パイプライン完了${NC}"
echo "=========================================="
echo "成果物: $REVIEWED_FILE"
if [ -n "${REPORT_FILE:-}" ]; then
    echo "レポート: $REPORT_FILE"
fi
echo ""
echo "次のステップ:"
echo "  1. 成果物を確認してください"
echo "  2. 問題なければ git push で共有"
echo "  3. 修正が必要な場合は設計書を更新して再実行"
