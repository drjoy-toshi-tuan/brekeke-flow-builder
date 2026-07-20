#!/usr/bin/env python3
"""
report_generator.py -- 仕上げパイプライン最終レポート生成

施設の出力ディレクトリ内のフローJSONと品質検証結果から
Markdown形式のレポートを生成する。

Usage:
    python scripts/report_generator.py output/貝塚病院/ -o output/貝塚病院/fix_report.md
"""

import json
import sys
import os
import argparse
import io
import glob
import re

# Windows cp932 環境での日本語・特殊文字出力対応
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 定数
# ============================================================

STT_TYPE = "drjoy^AmiVoice$Speech to Text"
DTMF_TYPE = "drjoy^External Integration$DTMF AmiVoice STT Input"
TTS_TYPE = "drjoy^Text To Speech$Text to speech"
RETRY_TYPE = "drjoy^Text To Speech$Speech Retry Counter"
OAI_TYPE = "drjoy^External Integration$generate_by_OpenAI"

FILLER_TOP6 = ["あ", "え", "えー", "あの", "はい", "ま"]

# ============================================================
# ヘルパー
# ============================================================

def find_flow_jsons(directory):
    """ディレクトリ内のフローJSONファイルを検索"""
    results = []
    # 直下のJSONファイル
    for f in sorted(os.listdir(directory)):
        if f.endswith(".json") and not f.startswith("verify_") and f != "fix_log.json":
            full_path = os.path.join(directory, f)
            if os.path.isfile(full_path):
                results.append(full_path)
    return results


def find_flow_jsons_recursive(directory):
    """ディレクトリ以下のフローJSONファイルを再帰検索（直下優先）"""
    facility_name = os.path.basename(os.path.normpath(directory))

    # まず直下を探す
    direct = find_flow_jsons(directory)
    if direct:
        return direct

    # なければ再帰的に探す
    results = []
    for root, dirs, files in os.walk(directory):
        for f in sorted(files):
            if f.endswith(".json") and not f.startswith("verify_") and f != "fix_log.json":
                full_path = os.path.join(root, f)
                results.append(full_path)
    if results:
        return results

    # それでもなければ、親ディレクトリで施設名を含むJSONを探す
    parent = os.path.dirname(os.path.normpath(directory))
    if parent and os.path.isdir(parent):
        for f in sorted(os.listdir(parent)):
            if f.endswith(".json") and facility_name in f and not f.startswith("verify_"):
                full_path = os.path.join(parent, f)
                if os.path.isfile(full_path):
                    results.append(full_path)
    return results


def load_flow(path):
    """フローJSONを読み込む"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def is_flow_json(data):
    """フローJSON構造かどうかを判定"""
    return all(k in data for k in ("name", "modules", "start"))


def get_word_count(profile_words):
    """profile_wordsの語数をカウント"""
    if not profile_words:
        return 0
    return len([line for line in profile_words.split("\n") if line.strip()])


def extract_facility_name(directory):
    """ディレクトリ名から施設名を推定"""
    return os.path.basename(os.path.normpath(directory))


def load_verify_result(directory):
    """verify_result.json を読み込む"""
    # 直下
    verify_path = os.path.join(directory, "verify_result.json")
    if os.path.exists(verify_path):
        with open(verify_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # 親ディレクトリ
    parent = os.path.dirname(os.path.normpath(directory))
    if parent:
        verify_path2 = os.path.join(parent, "verify_result.json")
        if os.path.exists(verify_path2):
            with open(verify_path2, "r", encoding="utf-8") as f:
                return json.load(f)
    # reports サブディレクトリ
    reports_path = os.path.join(directory, "reports", "verify_result.json")
    if os.path.exists(reports_path):
        with open(reports_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def load_fix_log(directory):
    """fix_log.json を読み込む（存在すれば）"""
    fix_log_path = os.path.join(directory, "fix_log.json")
    if os.path.exists(fix_log_path):
        with open(fix_log_path, "r", encoding="utf-8") as f:
            return json.load(f)
    # reports サブディレクトリも探す
    reports_path = os.path.join(directory, "reports", "fix_log.json")
    if os.path.exists(reports_path):
        with open(reports_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ============================================================
# レポート生成
# ============================================================

def generate_report(directory, output_path=None):
    """Markdownレポートを生成"""
    facility_name = extract_facility_name(directory)
    flow_paths = find_flow_jsons_recursive(directory)

    if not flow_paths:
        print(f"[ERROR] フローJSONが見つかりません: {directory}", file=sys.stderr)
        return None

    # フローデータ読み込み
    flows = []
    invalid_paths = []
    for path in flow_paths:
        try:
            data = load_flow(path)
            if is_flow_json(data):
                flows.append((path, data))
            else:
                invalid_paths.append(path)
        except (json.JSONDecodeError, KeyError) as e:
            invalid_paths.append(path)

    if not flows:
        print(f"[ERROR] 有効なフローJSONがありません: {directory}", file=sys.stderr)
        return None

    # 検証結果読み込み
    verify_result = load_verify_result(directory)
    fix_log = load_fix_log(directory)

    # 統計収集
    total_modules = 0
    stt_dtmf_modules = []
    openai_modules = []
    retry_modules = []
    tts_modules = []
    flow_names = []

    for path, data in flows:
        modules = data.get("modules", {})
        total_modules += len(modules)
        flow_names.append(data.get("name", os.path.basename(path)))

        for name, mod in modules.items():
            mod_type = mod.get("type", "")
            if mod_type in (STT_TYPE, DTMF_TYPE):
                stt_dtmf_modules.append((name, mod, path))
            elif mod_type == OAI_TYPE:
                openai_modules.append((name, mod, path))
            elif mod_type == RETRY_TYPE:
                retry_modules.append((name, mod, path))
            elif mod_type == TTS_TYPE:
                tts_modules.append((name, mod, path))

    # レポート生成開始
    lines = []

    # ヘッダ
    lines.append(f"# 仕上げレポート: {facility_name}")
    lines.append("")

    # 概要
    score_str = "N/A"
    judgment_str = "N/A"
    if verify_result:
        score_str = f"{verify_result.get('score', 'N/A')}/{verify_result.get('max_score', 100)}"
        judgment_str = verify_result.get("judgment", "N/A")

    lines.append("## 概要")
    lines.append("")
    lines.append("| 項目 | 値 |")
    lines.append("|------|-----|")
    lines.append(f"| 施設名 | {facility_name} |")
    lines.append(f"| フロー数 | {len(flows)} |")
    lines.append(f"| 総モジュール数 | {total_modules} |")
    lines.append(f"| STT/DTMFモジュール数 | {len(stt_dtmf_modules)} |")
    lines.append(f"| OpenAIモジュール数 | {len(openai_modules)} |")
    lines.append(f"| 品質スコア | {score_str} |")
    lines.append(f"| 判定 | {judgment_str} |")
    lines.append("")

    # フロー一覧
    lines.append("### フロー一覧")
    lines.append("")
    for i, (path, data) in enumerate(flows, 1):
        fname = data.get("name", os.path.basename(path))
        mod_count = len(data.get("modules", {}))
        lines.append(f"{i}. `{fname}` ({mod_count}モジュール)")
    lines.append("")

    # Stage別修正サマリー
    lines.append("## Stage別修正サマリー")
    lines.append("")

    # fix_log がある場合はそこから詳細を取得
    if fix_log and isinstance(fix_log, dict):
        _generate_stage_from_fix_log(lines, fix_log)
    else:
        # fix_log なし: 現在のフローJSONの状態からサマリーを生成
        _generate_stage_from_current(lines, stt_dtmf_modules, openai_modules, retry_modules, tts_modules)

    # 品質検証詳細
    if verify_result:
        lines.append("## 品質検証詳細")
        lines.append("")
        checks = verify_result.get("checks", {})
        for section_key in ["profile_words", "openai_prompt", "structure"]:
            section = checks.get(section_key, {})
            section_label = section.get("label", section_key)
            section_score = section.get("score", "?")
            section_max = section.get("max_score", "?")
            lines.append(f"### {section_label} ({section_score}/{section_max})")
            lines.append("")
            lines.append("| チェック項目 | 結果 | スコア |")
            lines.append("|------------|------|--------|")
            items = section.get("items", {})
            for item_key, item in items.items():
                status = item.get("status", "?")
                label = item.get("label", "?")
                score = item.get("score", "?")
                max_s = item.get("max_score", "?")
                if "rate" in item:
                    detail = f"{item['pass_count']}/{item['total']} ({item['rate']}%)"
                elif "fail_count" in item and item.get("fail_count", 0) >= 0:
                    detail = f"{item['fail_count']}件"
                elif "pass_count" in item:
                    detail = f"{item['pass_count']}/{item['total']}"
                else:
                    detail = ""
                lines.append(f"| {label} | {status} {detail} | {score}/{max_s} |")
            lines.append("")

    # 残存警告
    lines.append("## 残存警告")
    lines.append("")
    warnings = _collect_warnings(stt_dtmf_modules, openai_modules, retry_modules, verify_result)
    if warnings:
        lines.append("| 重要度 | 内容 |")
        lines.append("|--------|------|")
        for sev, msg in warnings:
            lines.append(f"| {sev} | {msg} |")
    else:
        lines.append("残存警告はありません。")
    lines.append("")

    # 出力ファイル
    lines.append("## 出力ファイル")
    lines.append("")
    _list_output_files(lines, directory)

    report = "\n".join(lines)

    # 出力
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"[INFO] レポートを生成しました: {output_path}")
    else:
        print(report)

    return report


def _generate_stage_from_fix_log(lines, fix_log):
    """fix_log.json からStage別サマリーを生成"""
    stages = fix_log.get("stages", {})

    for stage_key, stage_label in [
        ("stage1", "Stage 1: 構造修正"),
        ("stage2", "Stage 2: profile_words"),
        ("stage3", "Stage 3: OpenAIプロンプト"),
        ("stage4", "Stage 4: Property.md"),
    ]:
        stage_data = stages.get(stage_key, {})
        lines.append(f"### {stage_label}")
        lines.append("")

        fixes = stage_data.get("fixes", [])
        if fixes:
            if stage_key == "stage1":
                lines.append("| 修正ID | 対象モジュール | 修正内容 |")
                lines.append("|--------|-------------|---------|")
                for fix in fixes:
                    lines.append(f"| {fix.get('id', '-')} | {fix.get('module', '-')} | {fix.get('description', '-')} |")
            elif stage_key == "stage2":
                lines.append("| モジュール | 修正前語数 | 修正後語数 | アクション |")
                lines.append("|-----------|-----------|-----------|-----------|")
                for fix in fixes:
                    lines.append(f"| {fix.get('module', '-')} | {fix.get('before_count', '-')} | {fix.get('after_count', '-')} | {fix.get('action', '-')} |")
            elif stage_key == "stage3":
                lines.append("| モジュール | 修正前文字数 | 修正後文字数 | 追加セクション |")
                lines.append("|-----------|------------|------------|--------------|")
                for fix in fixes:
                    lines.append(f"| {fix.get('module', '-')} | {fix.get('before_chars', '-')} | {fix.get('after_chars', '-')} | {fix.get('added_sections', '-')} |")
            elif stage_key == "stage4":
                lines.append("| 項目 | アクション |")
                lines.append("|------|-----------|")
                for fix in fixes:
                    lines.append(f"| {fix.get('item', '-')} | {fix.get('action', '-')} |")

            lines.append("")
            lines.append(f"合計: {len(fixes)}件")
        else:
            lines.append("修正なし")
        lines.append("")


def _generate_stage_from_current(lines, stt_dtmf_modules, openai_modules, retry_modules, tts_modules):
    """現在のフローJSON状態からサマリーを生成（簡易版）"""

    # Stage 1: 構造修正（現状サマリー）
    lines.append("### Stage 1: 構造修正")
    lines.append("")
    lines.append("*修正ログなし -- 現在の状態を表示*")
    lines.append("")

    retry_with_pf = 0
    retry_total = len(retry_modules)
    for name, mod, _ in retry_modules:
        pf = mod.get("params", {}).get("prompt_false", "")
        if pf.strip():
            retry_with_pf += 1

    lines.append(f"- Retry Counter: {retry_total}個 (prompt_false設定済み: {retry_with_pf}個)")
    lines.append(f"- TTSモジュール: {len(tts_modules)}個")
    lines.append("")

    # Stage 2: profile_words（現状サマリー）
    lines.append("### Stage 2: profile_words")
    lines.append("")
    lines.append("| モジュール | 語数 | ステータス |")
    lines.append("|-----------|------|----------|")

    for name, mod, _ in stt_dtmf_modules:
        pw = mod.get("params", {}).get("profile_words", "")
        wc = get_word_count(pw)
        if wc == 0:
            status = "EMPTY"
        elif wc < 50:
            status = "不足"
        elif wc <= 300:
            status = "OK"
        else:
            status = "過多"
        lines.append(f"| {name} | {wc} | {status} |")
    lines.append("")

    # Stage 3: OpenAIプロンプト（現状サマリー）
    lines.append("### Stage 3: OpenAIプロンプト")
    lines.append("")
    lines.append("| モジュール | 文字数 | Role | Context | セキュリティ | Few-Shot | NO_RESULT |")
    lines.append("|-----------|--------|------|---------|------------|---------|-----------|")

    for name, mod, _ in openai_modules:
        prompt = mod.get("params", {}).get("prompt", "")
        char_count = len(prompt)
        has_role = "o" if re.search(r"#\s*Role", prompt) else "x"
        has_ctx = "o" if re.search(r"#\s*Context", prompt) else "x"
        has_sec = "o" if re.search(r"(インジェクション|セキュリティ|injection)", prompt, re.IGNORECASE) else "x"
        has_fs = "o" if re.search(r"#\s*Few-Shot|#\s*Few\s*Shot|入力[「『]|## 例|# 例|例[：:]|「.+?」\s*→", prompt) else "x"
        has_nr = "o" if "NO_RESULT" in prompt else "x"
        lines.append(f"| {name} | {char_count} | {has_role} | {has_ctx} | {has_sec} | {has_fs} | {has_nr} |")
    lines.append("")

    # Stage 4: Property.md
    lines.append("### Stage 4: Property.md")
    lines.append("")
    lines.append("*修正ログなし*")
    lines.append("")


def _collect_warnings(stt_dtmf_modules, openai_modules, retry_modules, verify_result):
    """残存警告を収集"""
    warnings = []

    # profile_words 空モジュール
    for name, mod, _ in stt_dtmf_modules:
        pw = mod.get("params", {}).get("profile_words", "")
        wc = get_word_count(pw)
        if wc == 0:
            warnings.append(("WARNING", f"profile_words 空: {name}"))
        elif wc < 50:
            warnings.append(("WARNING", f"profile_words 不足 ({wc}語): {name}"))
        elif wc > 300:
            warnings.append(("WARNING", f"profile_words 過多 ({wc}語): {name}"))

    # OpenAI プロンプト警告
    for name, mod, _ in openai_modules:
        prompt = mod.get("params", {}).get("prompt", "")
        if not prompt:
            warnings.append(("CRITICAL", f"OpenAIプロンプト空: {name}"))
        elif len(prompt) < 500:
            warnings.append(("WARNING", f"OpenAIプロンプト短い ({len(prompt)}字): {name}"))

    # verify_result の CRITICAL
    if verify_result:
        checks = verify_result.get("checks", {})
        struct = checks.get("structure", {}).get("items", {})
        critical_item = struct.get("critical", {})
        fail_count = critical_item.get("fail_count", 0)
        if fail_count and fail_count > 0:
            warnings.append(("CRITICAL", f"validator.py CRITICAL: {fail_count}件"))

    return warnings


def _list_output_files(lines, directory):
    """出力ディレクトリ内のファイルを列挙"""
    for root, dirs, files in os.walk(directory):
        for f in sorted(files):
            rel_path = os.path.relpath(os.path.join(root, f), directory)
            ext = os.path.splitext(f)[1].lower()
            if ext in (".bivr", ".json", ".md", ".txt"):
                lines.append(f"- `{rel_path}`")
    lines.append("")


# ============================================================
# メイン
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="仕上げパイプラインの最終レポートをMarkdown形式で生成"
    )
    parser.add_argument(
        "directory",
        help="施設の出力ディレクトリ (例: output/貝塚病院/)",
    )
    parser.add_argument(
        "--output", "-o",
        help="出力ファイルパス (省略時はコンソール出力)",
        default=None,
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"[ERROR] ディレクトリが見つかりません: {args.directory}", file=sys.stderr)
        sys.exit(1)

    generate_report(args.directory, args.output)


if __name__ == "__main__":
    main()
