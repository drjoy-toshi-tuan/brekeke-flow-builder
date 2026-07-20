#!/usr/bin/env python3
"""
property_fixer.py — Property.md 整合性チェック＆自動修正ツール

フローJSONとProperty.mdの整合性をチェックし、--fix オプションで自動修正する。

Usage:
    python scripts/property_fixer.py output/施設_健診_YYYYMMDD.json input/施設/properties_施設_健診.md
    python scripts/property_fixer.py output/施設_健診_YYYYMMDD.json input/施設/properties_施設_健診.md --fix
    python scripts/property_fixer.py output/a.json output/b.json input/施設/properties.md
    python scripts/property_fixer.py output/a.json output/b.json input/施設/properties.md --fix
"""

import json
import sys
import re
import os
from pathlib import Path

# Windows cp932 環境での日本語出力対応
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ============================================================
# 定数
# ============================================================

TTS_TYPE = "drjoy^Text To Speech$Text to speech"

REQUIRED_KEYS = [
    "office_id",
    "pbx.db.name",
    "context.settings.url",
    "acceptance_times.url",
    "rag_ssml.url",
    "openAI_generate.url",
    "amivoice.uri",
    "amivoice.language",
    "amivoice.engine",
    "amivoice.keep_filter_token",
    "amivoice.silent_detection_ms",
    "amivoice.timeout_ms",
    "amivoice.probability",
    "amivoice.detection_flag",
    "amivoice.save_log",
    "speech.rag.url",
    "speech.rag.connect_timeout",
    "speech.rag.request_timeout",
    "speech.rag.credibility",
]

# デフォルト推奨値（--fix で欠落時に追加する値）
RECOMMENDED_DEFAULTS = {
    "amivoice.detection_flag": "検出しない",
}

DEMO_PATTERN = re.compile(r"demo-reserve\.famishare\.jp")
PROD_PATTERN = re.compile(r"reserve\.drjoy\.jp")

PLACEHOLDER_PATTERN = re.compile(r"^TODO")


# ============================================================
# パーサー
# ============================================================

def load_flow_json(path: str) -> dict:
    """フローJSONを読み込む"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_tts_modules_from_flow(flow: dict) -> list[str]:
    """フローJSON内のTTSモジュール名を抽出する"""
    modules = flow.get("modules", {})
    return [
        name for name, mod in modules.items()
        if mod.get("type") == TTS_TYPE
    ]


def is_subflow(flow: dict) -> bool:
    """フローがサブフローかどうかを判定する。
    サブフローの判定基準:
    - フロー名に「氏名聴取」「生年月日聴取」「電話番号聴取」等が含まれる
    - modules に Custom Jump to Flow の遷移先として使われるフロー
    ここでは引数として渡されたJSONがメインフローかサブフローかを区別する必要がある。
    メインフローのTTSのみを対象とするため、サブフロー判定は呼び出し側で行う。
    """
    return False


def parse_property_md(path: str) -> dict:
    """Property.mdを解析して全キー=値のペアを抽出する。

    Returns:
        {
            "prompts": {"モジュール名": "値", ...},
            "settings": {"キー名": "値", ...},
            "raw_lines": [行テキスト, ...],
            "code_block_range": (start_line, end_line),  # ``` の範囲
        }
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    prompts = {}       # モジュール名 -> prompt値
    settings = {}      # キー名 -> 値
    raw_lines = lines
    code_start = None
    code_end = None

    # コードブロック範囲を検出
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "```" or stripped.startswith("```"):
            if code_start is None:
                code_start = i
            else:
                code_end = i
                break

    # コードブロック内のキー=値を解析
    parse_start = code_start + 1 if code_start is not None else 0
    parse_end = code_end if code_end is not None else len(lines)

    for i in range(parse_start, parse_end):
        line = lines[i].strip()
        if not line or line.startswith("#") or line.startswith(">"):
            continue

        # key=value 形式を解析
        eq_pos = line.find("=")
        if eq_pos == -1:
            continue

        key = line[:eq_pos].strip()
        value = line[eq_pos + 1:].strip()

        # .prompt= で終わるキーはTTSプロンプト
        if key.endswith(".prompt"):
            module_name = key[:-len(".prompt")]
            prompts[module_name] = value
        else:
            settings[key] = value

    return {
        "prompts": prompts,
        "settings": settings,
        "raw_lines": raw_lines,
        "code_block_range": (code_start, code_end),
    }


# ============================================================
# チェッカー
# ============================================================

class CheckResult:
    def __init__(self):
        self.ok_items: list[str] = []
        self.miss_items: list[str] = []   # Property.mdにあるがフローにない
        self.lack_items: list[str] = []   # フローにあるがProperty.mdにない
        self.warn_items: list[str] = []
        self.required_ok: list[str] = []
        self.required_lack: list[str] = []
        self.required_warn: list[str] = []
        self.url_status: str = ""
        self.url_details: list[str] = []
        self.fix_candidates: list[str] = []


def check_module_consistency(
    flow_tts_names: list[str],
    property_prompts: dict[str, str],
) -> tuple[list, list, list]:
    """モジュール名⇔Property.mdキー整合性チェック"""
    ok = []
    miss = []    # Property.mdにあるがフローにない
    lack = []    # フローにあるがProperty.mdにない

    flow_set = set(flow_tts_names)
    prop_set = set(property_prompts.keys())

    # フローにあるもの
    for name in sorted(flow_set):
        if name in prop_set:
            ok.append(name)
        else:
            lack.append(name)

    # Property.mdにあるがフローにないもの
    for name in sorted(prop_set):
        if name not in flow_set:
            miss.append(name)

    return ok, miss, lack


def check_required_sections(settings: dict[str, str]) -> tuple[list, list, list]:
    """必須セクション存在チェック"""
    ok = []
    lack = []
    warn = []

    for key in REQUIRED_KEYS:
        if key in settings:
            value = settings[key]
            if PLACEHOLDER_PATTERN.match(value):
                warn.append((key, f"{key}={value} — プレースホルダーのまま"))
            ok.append(key)
        else:
            lack.append(key)

    return ok, lack, warn


def check_wait_setting(settings: dict[str, str]) -> tuple[bool, str]:
    """wait設定チェック"""
    key = "冒頭.wait"
    if key in settings:
        if settings[key] == "2000":
            return True, f"{key}=2000"
        else:
            return False, f"{key}={settings[key]} — 推奨値は 2000"
    return False, f"{key} — 未設定"


def check_url_environment(settings: dict[str, str]) -> tuple[str, list[str]]:
    """URL環境チェック（demo/prod混在検出）"""
    demo_urls = []
    prod_urls = []
    details = []

    for key, value in settings.items():
        if DEMO_PATTERN.search(value):
            demo_urls.append(key)
        if PROD_PATTERN.search(value):
            prod_urls.append(key)

    if demo_urls and prod_urls:
        status = "MIXED"
        details.append("demo環境とprod環境のURLが混在しています:")
        for k in demo_urls:
            details.append(f"  [demo] {k}={settings[k]}")
        for k in prod_urls:
            details.append(f"  [prod] {k}={settings[k]}")
    elif demo_urls:
        status = "demo"
    elif prod_urls:
        status = "prod"
    else:
        status = "unknown"
        details.append("URLが検出されませんでした")

    return status, details


# ============================================================
# 修正（--fix）
# ============================================================

def fix_property_md(
    parsed: dict,
    lack_modules: list[str],
    required_lack: list[str],
) -> list[str]:
    """Property.mdを修正して新しい行リストを返す。

    修正内容:
    1. 欠落しているTTSプロンプトを追加
    2. 欠落している必須セクションを追加
    """
    lines = list(parsed["raw_lines"])
    code_start, code_end = parsed["code_block_range"]

    if code_end is None:
        # コードブロックが閉じていない場合は末尾に追加
        insert_pos = len(lines)
    else:
        insert_pos = code_end

    additions = []

    # 欠落プロンプトを追加
    if lack_modules:
        additions.append("\n")
        additions.append("# 追加: 欠落していたTTSプロンプト\n")
        for mod_name in sorted(lack_modules):
            additions.append(f"{mod_name}.prompt=\n")

    # 欠落必須セクションを追加
    if required_lack:
        additions.append("\n")
        additions.append("# 追加: 欠落していた必須設定\n")
        for key in required_lack:
            default_val = RECOMMENDED_DEFAULTS.get(key, "")
            additions.append(f"{key}={default_val}\n")

    if additions:
        for i, add_line in enumerate(additions):
            lines.insert(insert_pos + i, add_line)

    return lines


# ============================================================
# 出力
# ============================================================

def print_report(
    result: CheckResult,
    property_name: str,
    fix_mode: bool = False,
):
    """チェック結果をコンソール出力"""
    print("=" * 60)
    print(f"[PROPERTY_FIXER] Property.md 整合性チェック: {property_name}")
    print("=" * 60)
    print()

    # --- モジュール整合性 ---
    print("--- モジュール整合性 ---")
    for name in result.ok_items:
        print(f"  [OK]   {name} — Property.md に存在")
    for name in result.miss_items:
        print(f"  [MISS] {name} — Property.md に存在するがフローにモジュールなし（サブフロー用の可能性）")
    for name in result.lack_items:
        print(f"  [LACK] {name} — フローにあるがProperty.md に未定義")

    total = len(result.ok_items) + len(result.lack_items)
    print()
    print(f"  一致: {len(result.ok_items)}/{total}  "
          f"欠落: {len(result.lack_items)}  "
          f"不要: {len(result.miss_items)}")
    print()

    # --- 必須セクション ---
    print("--- 必須セクション ---")
    for name in result.required_ok:
        print(f"  [OK]   {name}")
    for key, msg in result.required_warn:
        print(f"  [WARN] {msg}")
    for name in result.required_lack:
        rec = RECOMMENDED_DEFAULTS.get(name, "")
        suffix = f"（推奨: {rec}）" if rec else ""
        print(f"  [LACK] {name} — 未設定{suffix}")
    print()

    # --- wait設定 ---
    print("--- wait設定 ---")
    wait_ok, wait_msg = result.wait_ok, result.wait_msg
    if wait_ok:
        print(f"  [OK]   {wait_msg}")
    else:
        print(f"  [LACK] {wait_msg}")
    print()

    # --- URL環境 ---
    print("--- URL環境 ---")
    if result.url_status == "MIXED":
        print("  [WARN] " + result.url_details[0])
        for d in result.url_details[1:]:
            print(f"         {d}")
    elif result.url_status in ("demo", "prod"):
        print(f"  [OK]   全URLが {result.url_status} 環境で統一")
    else:
        for d in result.url_details:
            print(f"  [WARN] {d}")
    print()

    # --- 修正候補 ---
    if result.fix_candidates:
        print("--- 修正候補 ---")
        for c in result.fix_candidates:
            print(f"  {c}")
        print()

    if fix_mode:
        print("--- 修正モード: --fix が有効 ---")
    else:
        print("--- チェックのみ（修正するには --fix を追加） ---")


# ============================================================
# メイン
# ============================================================

def main():
    args = sys.argv[1:]

    if len(args) < 2:
        print("Usage: python scripts/property_fixer.py <flow_json>... <property.md> [--fix]")
        print()
        print("  flow_json:   フローJSON（複数指定可。サブフローJSONは指定しない）")
        print("  property.md: Property.md ファイル")
        print("  --fix:       修正を実行（デフォルトはチェックのみ）")
        sys.exit(1)

    fix_mode = "--fix" in args
    if fix_mode:
        args.remove("--fix")

    # 最後の引数が .md ファイル → Property.md
    # それ以外は全てフローJSON
    property_path = None
    flow_paths = []

    for arg in args:
        if arg.endswith(".md"):
            property_path = arg
        elif arg.endswith(".json"):
            flow_paths.append(arg)
        else:
            print(f"[ERROR] 不明なファイル形式: {arg}")
            sys.exit(1)

    if not property_path:
        print("[ERROR] Property.md ファイルが指定されていません（.md ファイル）")
        sys.exit(1)

    if not flow_paths:
        print("[ERROR] フローJSON が指定されていません（.json ファイル）")
        sys.exit(1)

    # ファイル存在確認
    for p in flow_paths + [property_path]:
        if not os.path.exists(p):
            print(f"[ERROR] ファイルが見つかりません: {p}")
            sys.exit(1)

    # --- フローJSON読み込み・TTS抽出 ---
    all_tts_names = []
    for fp in flow_paths:
        flow = load_flow_json(fp)
        tts_names = extract_tts_modules_from_flow(flow)
        all_tts_names.extend(tts_names)

    # 重複排除（複数フローに同名がある場合）
    all_tts_names = sorted(set(all_tts_names))

    # --- Property.md解析 ---
    parsed = parse_property_md(property_path)
    prompts = parsed["prompts"]
    settings = parsed["settings"]

    # --- チェック実行 ---
    result = CheckResult()

    # 1. モジュール整合性
    ok, miss, lack = check_module_consistency(all_tts_names, prompts)
    result.ok_items = ok
    result.miss_items = miss
    result.lack_items = lack

    # 2. 必須セクション
    req_ok, req_lack, req_warn = check_required_sections(settings)
    result.required_ok = req_ok
    result.required_lack = req_lack
    result.required_warn = req_warn

    # 3. wait設定
    result.wait_ok, result.wait_msg = check_wait_setting(settings)

    # 4. URL環境
    result.url_status, result.url_details = check_url_environment(settings)

    # --- 修正候補生成 ---
    for name in lack:
        result.fix_candidates.append(f"{name}.prompt= <- 追加が必要")
    for key in req_lack:
        rec = RECOMMENDED_DEFAULTS.get(key, "")
        if rec:
            result.fix_candidates.append(f"{key}={rec} <- 追加推奨")
        else:
            result.fix_candidates.append(f"{key}= <- 追加が必要")

    # --- Property名（表示用） ---
    property_name = Path(property_path).stem
    # "properties_貝塚病院_健診" -> "貝塚病院_健診"
    if property_name.startswith("properties_"):
        property_name = property_name[len("properties_"):]

    # --- レポート出力 ---
    print_report(result, property_name, fix_mode)

    # --- 修正実行 ---
    if fix_mode and (lack or req_lack):
        new_lines = fix_property_md(parsed, lack, req_lack)
        with open(property_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print(f"\n[FIXED] {property_path} を更新しました。")
        print(f"  追加プロンプト: {len(lack)} 件")
        print(f"  追加必須設定: {len(req_lack)} 件")
    elif fix_mode:
        print("\n[INFO] 修正対象がありませんでした。")

    # 終了コード: 欠落があれば1
    if lack or req_lack:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
