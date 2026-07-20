#!/bin/bash
# tools/run_csv_to_yaml.sh <facility> <flow>
# csv_to_yaml.py の引数を自動組み立てして実行するラッパー
# VS Code tasks.json または /new-flow skill から呼ばれる

set -euo pipefail

FACILITY="${1:-}"
FLOW="${2:-}"

if [ -z "$FACILITY" ] || [ -z "$FLOW" ]; then
  echo "使い方: bash tools/run_csv_to_yaml.sh <施設名> <フロー名>"
  echo "例:     bash tools/run_csv_to_yaml.sh カレス記念病院 診療"
  exit 1
fi

SCENARIO_DIR="output/scenarios/${FACILITY}_${FLOW}"

# フォルダ確認
if [ ! -d "$SCENARIO_DIR" ]; then
  echo "❌ フォルダが見つかりません: $SCENARIO_DIR"
  echo "   → /new-flow ${FACILITY} ${FLOW} を先に実行してください"
  exit 1
fi

# Sheet1 (必須)
SHEET1=$(ls "${SCENARIO_DIR}"/spec_*_Sheet1_input.csv \
             "${SCENARIO_DIR}"/sheet1_input.csv 2>/dev/null | head -1 || true)
if [ -z "$SHEET1" ]; then
  echo "❌ Sheet1_input.csv が見つかりません"
  echo "   探した場所: ${SCENARIO_DIR}/spec_*_Sheet1_input.csv"
  echo "              ${SCENARIO_DIR}/sheet1_input.csv"
  exit 1
fi

# オプションシートを自動検出
SHEET2=$(ls "${SCENARIO_DIR}"/spec_*_Sheet2_flow.csv 2>/dev/null | head -1 || true)
SHEET_TERM=$(ls "${SCENARIO_DIR}"/spec_*_Sheet_Termination.csv 2>/dev/null | head -1 || true)
SHEET_DEPT=$(ls "${SCENARIO_DIR}"/sheet_department.csv \
                "${SCENARIO_DIR}"/spec_*_sheet_department.csv 2>/dev/null | head -1 || true)
SHEET_FAQ=$(ls "${SCENARIO_DIR}"/sheet_faq.csv \
               "${SCENARIO_DIR}"/spec_*_sheet_faq.csv 2>/dev/null | head -1 || true)
SHEET_SETTINGS=$(ls "${SCENARIO_DIR}"/spec_*_Sheet_Settings.csv \
                    "${SCENARIO_DIR}"/Sheet_Settings.csv 2>/dev/null | head -1 || true)
SHEET_SCRIPT=$(ls "${SCENARIO_DIR}"/spec_*_Sheet_Script.csv 2>/dev/null | head -1 || true)

# 実行サマリー表示
echo "========================================"
echo "  VFB: CSV → YAML"
echo "  施設: ${FACILITY} / フロー: ${FLOW}"
echo "========================================"
echo "  Sheet1:      ${SHEET1}"
[ -n "$SHEET2" ]        && echo "  Sheet2:      ${SHEET2} ✓" \
                        || echo "  Sheet2:      なし（直線フロー）"
[ -n "$SHEET_TERM" ]    && echo "  終話:        ${SHEET_TERM} ✓"
[ -n "$SHEET_DEPT" ]    && echo "  診療科:      ${SHEET_DEPT} ✓"
[ -n "$SHEET_FAQ" ]     && echo "  FAQ:         ${SHEET_FAQ} ✓"
[ -n "$SHEET_SETTINGS" ] && echo "  Settings:    ${SHEET_SETTINGS} ✓"
[ -n "$SHEET_SCRIPT" ]  && echo "  Script:      ${SHEET_SCRIPT} ✓"
echo "========================================"
echo ""

# 引数を組み立て
ARGS=(
  "--input" "$SHEET1"
  "--facility" "$FACILITY"
  "--flow" "$FLOW"
)
[ -n "$SHEET2" ]         && ARGS+=("--sheet2" "$SHEET2")
[ -n "$SHEET_TERM" ]     && ARGS+=("--sheet-termination" "$SHEET_TERM")
[ -n "$SHEET_DEPT" ]     && ARGS+=("--sheet-department" "$SHEET_DEPT")
[ -n "$SHEET_FAQ" ]      && ARGS+=("--sheet-faq" "$SHEET_FAQ")
[ -n "$SHEET_SETTINGS" ] && ARGS+=("--sheet-settings" "$SHEET_SETTINGS")
[ -n "$SHEET_SCRIPT" ]   && ARGS+=("--sheet-script" "$SHEET_SCRIPT")

# 実行
python3 tools/csv_to_yaml.py "${ARGS[@]}"
EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ 完了!"
  echo "   出力: ${SCENARIO_DIR}/設計書_${FACILITY}_${FLOW}.yaml"
  echo ""
  echo "次のステップ:"
  echo "  QA検証: python3 schemas/qa_validator.py \"${SCENARIO_DIR}/設計書_${FACILITY}_${FLOW}.yaml\""
  echo "  ビルド: python3 scripts/orchestrator.py --pattern 1 --spec \"${SCENARIO_DIR}/設計書_${FACILITY}_${FLOW}.yaml\""
else
  echo "❌ エラーで終了 (exit ${EXIT_CODE})"
  echo ""
  echo "Claude Code に上記エラーを貼り付けて修正を依頼できます:"
  echo "  例: 「このエラーを直してください: [エラー内容]」"
fi

exit $EXIT_CODE
