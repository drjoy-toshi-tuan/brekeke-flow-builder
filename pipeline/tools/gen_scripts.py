#!/usr/bin/env python3
"""
設計書 YAML の script_blocks から ES5 Scripts コードを生成し、
scaffold JSON の該当モジュールに埋め込むツール。

使い方:
  python tools/gen_scripts.py \
      --yaml output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml \
      --scaffold output/json/scaffold_東京都立豊島病院_診療.json \
      --out output/json/scaffold_東京都立豊島病院_診療_scripted.json

  # キーワードプリセットは docs/amivoice/keyword_presets.yaml から自動読み込み
  # --presets で別パスを指定可能（省略時は本ツールと同リポジトリの標準パスを探す）
"""
import argparse
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が必要です。requirements.txt を確認してください。", file=sys.stderr)
    sys.exit(1)


# ---- キーワードプリセット読み込み ----

_PRESETS = {}  # { preset_name: [keyword, ...] }
_PRESET_COMPOUNDS = {}  # { preset_name: [regex, ...] } — 複合発話（keyword より先に評価）

DEFAULT_PRESETS_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "amivoice", "keyword_presets.yaml"
)


def load_presets(path=None):
    """keyword_presets.yaml を読み込み _PRESETS に展開する"""
    global _PRESETS
    target = path or DEFAULT_PRESETS_PATH
    if not os.path.exists(target):
        print(f"WARN: keyword_presets.yaml が見つかりません: {target}", file=sys.stderr)
        return
    with open(target, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    for name, entry in data.items():
        if isinstance(entry, dict) and "keywords" in entry:
            _PRESETS[name] = entry["keywords"]
            if entry.get("compounds"):
                _PRESET_COMPOUNDS[name] = list(entry["compounds"])
        elif isinstance(entry, list):
            _PRESETS[name] = entry
    print(f"keyword_presets: {len(_PRESETS)} プリセット読み込み済み", file=sys.stderr)


def resolve_keywords(opt):
    """
    option dict から最終的なキーワードリストを返す。
    preset が指定されていれば展開し、keywords と結合（重複排除）する。
    """
    preset_name = opt.get("preset", "")
    base = list(_PRESETS.get(preset_name, []))
    if preset_name and not base:
        print(f"WARN: preset '{preset_name}' が見つかりません。keywords のみ使用します。", file=sys.stderr)
    extra = opt.get("keywords", [])
    # 重複排除（順序維持）
    seen = set()
    merged = []
    for kw in base + extra:
        if kw not in seen:
            seen.add(kw)
            merged.append(kw)
    return merged


# ---- ES5 コード生成 ----

def build_input_reader(input_module):
    """getModuleResult → text 正規化の固定パターン"""
    return (
        'var rawInput = $runner.getModuleResult("{mod}");\n'
        'var text = "";\n'
        'if (rawInput && typeof rawInput === "object" && rawInput.text) {{\n'
        '    text = String(rawInput.text).trim();\n'
        '}} else if (typeof rawInput === "string") {{\n'
        '    text = rawInput.trim();\n'
        '}}\n'
        'text = text.replace(/[　 ]/g, "").replace(/[？?。、！!「」]/g, "");\n'
    ).format(mod=input_module)


def build_repeat_guard(repeat_limit=2):
    """
    リピート検知ブロック（先頭に挿入）。
    REPEAT → 直前 TTS に戻る。REPEAT_LIMIT → オペレーター転送。
    """
    lines = [
        "// ---- リピート検知（もう一度/もう一回） ----",
        "if (/もう一度|もう一回|くりかえし|繰り返し|聞こえません|もう少し/.test(text)) {",
        '    var repeatRaw = $runner.getObject("repeat_count");',
        "    var repeatCount = repeatRaw ? parseInt(String(repeatRaw), 10) : 0;",
        "    if (repeatCount < {limit}) {{".format(limit=repeat_limit),
        "        $runner.setObject(\"repeat_count\", repeatCount + 1);",
        '        $runner.setResult("REPEAT");',
        "    } else {",
        '        $runner.setResult("REPEAT_LIMIT");',
        "    }",
        "} else {",
        '    $runner.setObject("repeat_count", 0);',
        "",
    ]
    return lines


def close_repeat_guard():
    return ["}"]


def build_branches(options, indent=""):
    """
    options リストからif/else if 分岐コードを生成する。
    preset と keywords を resolve_keywords でマージ済みのものを使う。
    """
    lines = []
    branches = []
    for opt in options:
        label    = opt.get("label", "")
        keywords = resolve_keywords(opt)
        if not keywords:
            print(f"WARN: label='{label}' にキーワードがありません（preset も keywords も未指定）", file=sys.stderr)
            continue
        pattern = "|".join(re.escape(k) for k in keywords)
        branches.append((pattern, label))

    for i, (pattern, label) in enumerate(branches):
        prefix = "if" if i == 0 else "} else if"
        lines.append('{indent}{prefix} (/{pattern}/.test(text)) {{'.format(
            indent=indent, prefix=prefix, pattern=pattern
        ))
        lines.append('{indent}    $runner.setResult("{label}");'.format(
            indent=indent, label=label
        ))

    if branches:
        lines.append("{indent}}} else {{".format(indent=indent))
        lines.append('{indent}    $runner.setResult("NO_RESULT");'.format(indent=indent))
        lines.append("{indent}}}".format(indent=indent))

    return lines


# ---- ブロック種別ごとのジェネレーター ----

def gen_youken_script(block):
    """用件判定 ES5 コードを生成"""
    input_module = block.get("input_module", "入力_用件")
    options      = block.get("options", [])
    repeat_guard = block.get("repeat_guard", True)
    repeat_limit = block.get("repeat_limit", 2)

    lines = [build_input_reader(input_module)]

    if repeat_guard:
        lines.extend(build_repeat_guard(repeat_limit))
        indent = "    "
    else:
        indent = ""

    lines.extend(build_branches(options, indent))

    if repeat_guard:
        lines.extend(close_repeat_guard())

    return "\n".join(lines)


def gen_enum_classifier_script(block):
    """
    汎用 enum 分類器（個人/法人・はい/いいえ・初診/再診 等）。
    options の各エントリで preset: または keywords: を使ってキーワードを指定する。
    """
    input_module = block.get("input_module", "")
    options      = block.get("options", [])
    repeat_guard = block.get("repeat_guard", True)
    repeat_limit = block.get("repeat_limit", 2)

    if not input_module:
        print(f"WARN: enum_classifier に input_module が未指定です", file=sys.stderr)

    lines = [build_input_reader(input_module)]

    if repeat_guard:
        lines.extend(build_repeat_guard(repeat_limit))
        indent = "    "
    else:
        indent = ""

    lines.extend(build_branches(options, indent))

    if repeat_guard:
        lines.extend(close_repeat_guard())

    return "\n".join(lines)


def gen_faq_script(block):
    """FAQ 完全一致判定 ES5 コードを生成"""
    input_module = block.get("input_module", "OpenAI_RAG")
    faq_map      = block.get("faq_map", [])
    repeat_guard = block.get("repeat_guard", True)
    repeat_limit = block.get("repeat_limit", 2)

    lines = [build_input_reader(input_module)]

    if repeat_guard:
        lines.extend(build_repeat_guard(repeat_limit))
        indent = "    "
    else:
        indent = ""

    lines.append("{indent}var faqMap = {{".format(indent=indent))
    for i, entry in enumerate(faq_map):
        # キーは build_input_reader と同じ正規化を通す: 実行時 text は空白と
        # ？?。、！!「」 を除去済みのため、生の q のままでは逐語一致でも
        # faqMap[text] が永久にミスする（dead entry）。
        q_norm = re.sub(r"[　 ]", "", entry.get("q", ""))
        q_norm = re.sub(r"[？?。、！!「」]", "", q_norm)
        # 文字列リテラルは json.dumps で生成（改行・制御文字・引用符を全て安全に
        # エスケープ。手動 replace では複数行 YAML の a: | が生改行のまま入り
        # Nashorn SyntaxError でスクリプト全死になる）。
        q_js = json.dumps(q_norm, ensure_ascii=False)
        a_js = json.dumps(entry.get("a", ""), ensure_ascii=False)
        comma = "," if i < len(faq_map) - 1 else ""
        lines.append('{indent}    {q}: {a}{comma}'.format(indent=indent, q=q_js, a=a_js, comma=comma))
    lines.append("{indent}}};".format(indent=indent))
    lines.append("")

    lines.append("{indent}var answer = faqMap[text];".format(indent=indent))
    lines.append("{indent}if (answer) {{".format(indent=indent))
    lines.append('{indent}    $runner.setObject("scripts-faq", answer);'.format(indent=indent))
    lines.append('{indent}    $runner.setResult("ANSWER");'.format(indent=indent))
    lines.append("{indent}}} else {{".format(indent=indent))
    lines.append('{indent}    $runner.setResult("NO_RESULT");'.format(indent=indent))
    lines.append("{indent}}}".format(indent=indent))

    if repeat_guard:
        lines.extend(close_repeat_guard())

    return "\n".join(lines)


def gen_department_script(block):
    """診療科正規化 ES5 コードを生成（SKILL_診療科.md の最長一致ロジック準拠）"""
    input_module = block.get("input_module", "入力_診療科")
    departments  = block.get("departments", [])
    repeat_guard = block.get("repeat_guard", True)
    repeat_limit = block.get("repeat_limit", 2)

    lines = [build_input_reader(input_module)]

    if repeat_guard:
        lines.extend(build_repeat_guard(repeat_limit))
        indent = "    "
    else:
        indent = ""

    lines.append("{indent}var DEPARTMENTS = [".format(indent=indent))
    for dept in departments:
        # json.dumps で引用符/バックスラッシュ/改行を安全にエスケープ
        lines.append('{indent}    {dept},'.format(indent=indent,
                                                  dept=json.dumps(str(dept), ensure_ascii=False)))
    lines.append("{indent}];".format(indent=indent))
    lines.append("")

    lines.append("{indent}var matched = null;".format(indent=indent))
    lines.append("{indent}var maxLen = 0;".format(indent=indent))
    lines.append("{indent}for (var i = 0; i < DEPARTMENTS.length; i++) {{".format(indent=indent))
    lines.append("{indent}    var dept = DEPARTMENTS[i];".format(indent=indent))
    lines.append("{indent}    if (text.indexOf(dept) >= 0 && dept.length > maxLen) {{".format(indent=indent))
    lines.append("{indent}        matched = dept;".format(indent=indent))
    lines.append("{indent}        maxLen = dept.length;".format(indent=indent))
    lines.append("{indent}    }}".format(indent=indent))
    lines.append("{indent}}}".format(indent=indent))
    lines.append("")

    lines.append("{indent}if (matched) {{".format(indent=indent))
    lines.append("{indent}    $runner.setResult(matched);".format(indent=indent))
    lines.append("{indent}}} else {{".format(indent=indent))
    lines.append('{indent}    $runner.setResult("NO_RESULT");'.format(indent=indent))
    lines.append("{indent}}}".format(indent=indent))

    if repeat_guard:
        lines.extend(close_repeat_guard())

    return "\n".join(lines)


# ---- n_choice（認定部品）配線ジェネレーター ----
# 2026-07-14 監査 #1（docs/amivoice/keyword_presets_audit_20260714.md）対応:
# 旧 build_branches（部分一致 + 定義順先勝ち）は「予約をキャンセルしたい」→予約 の
# 誤確定を起こすため退役。enum_classifier / youken は認定部品 modules/n_choice の
# engine（正規化 → DTMF → 完全一致 → 複合 → 最長一致 keyword → NO_RESULT）に
# spec を充填して配線する。生成時に n_choice oracle の lint_config + 衝突検査で
# fail-closed（問題があれば生成を止める — 黙って通さない）。

N_CHOICE_TEMPLATE = os.path.join(
    os.path.dirname(__file__), "..", "modules", "n_choice", "script.js"
)
_N_CHOICE_ORACLE = None


def _load_n_choice_oracle():
    """modules/n_choice/oracle.py を動的 import（生成時検証に使用）"""
    global _N_CHOICE_ORACLE
    if _N_CHOICE_ORACLE is None:
        import importlib.util
        p = os.path.join(os.path.dirname(__file__), "..", "modules", "n_choice", "oracle.py")
        spec_ = importlib.util.spec_from_file_location("n_choice_oracle", p)
        mod = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(mod)
        _N_CHOICE_ORACLE = mod
    return _N_CHOICE_ORACLE


def _js_json(obj):
    """spec を script.js に埋め込む JS リテラル（JSON 互換）に変換"""
    return json.dumps(obj, ensure_ascii=False)


def build_n_choice_config(block):
    """enum_classifier / youken ブロック → n_choice spec config を構築する。

    判定設計（script-input-handling.md B1〜B7 準拠）:
      - TOKEN_MAP: 全キーワードを完全一致で登録（短い語・1 文字語はここのみ）
      - COMPOUND_PATTERNS: block/preset の compounds（複合発話 — keyword より先に評価）
      - KEYWORD_PATTERNS: 2 文字以上の語を部分一致・**長い順**（最長一致）で登録
      - 同一キーワードが複数ラベルに載っていたら ERROR（fail-closed）
    """
    options = block.get("options", [])
    oracle = _load_n_choice_oracle()
    dtmf_map = {}
    token_map = []
    compound_patterns = []
    keyword_entries = []   # (keyword, label)
    seen_kw = {}           # keyword -> label（ラベル間衝突検査）

    for opt in options:
        label = opt.get("label", "")
        keywords = resolve_keywords(opt)
        if not keywords:
            print(f"WARN: label='{label}' にキーワードがありません", file=sys.stderr)
            continue
        if opt.get("dtmf") is not None:
            dtmf_key = str(opt["dtmf"])
            # n_choice engine の DTMF 判定は /^[0-9]$/（1桁のみ）。複数桁キーは
            # 生成できても永久に到達しない dead entry になるため fail-closed。
            if not re.fullmatch(r"[0-9]", dtmf_key):
                raise SystemExit(
                    f"[ERROR] label='{label}' の dtmf '{dtmf_key}' は 1 桁（0-9）のみ対応です"
                    f"（n_choice engine は複数桁 DTMF を判定しません — fail-closed）")
            dtmf_map[dtmf_key] = label
        # engine は正規化済み文字列（フィラー・語尾除去後）に対して照合するため、
        # 辞書側も同じ正規化を通した形で登録する（「受けたい」→「受け」等。
        # そのままだと語尾除去で永久に一致しない dead keyword になる — oracle lint が検出）。
        norm_keywords = []
        for k in keywords:
            nk = oracle._normalize(k)
            if nk and nk not in norm_keywords:
                norm_keywords.append(nk)
        # 完全一致（TOKEN）: 全キーワード
        token_map.append({"regex": "|".join(re.escape(k) for k in norm_keywords),
                          "result": label})
        for k in norm_keywords:
            if k in seen_kw and seen_kw[k] != label:
                raise SystemExit(
                    f"[ERROR] キーワード '{k}' が複数ラベルに登録されています"
                    f"（{seen_kw[k]} / {label}）— spec を修正してください（fail-closed）")
            seen_kw[k] = label
            # 部分一致は 2 文字以上のみ（1 文字語は完全一致でしか判定しない — 監査 #3）
            if len(k) >= 2:
                keyword_entries.append((k, label))
            else:
                print(f"  [INFO] 1文字語 '{k}' ({label}) は完全一致のみで判定します",
                      file=sys.stderr)
        # 複合パターン（block の options[].compounds / preset の compounds）
        # regex は実行時 new RegExp() で初めて評価されるため、生成時に Python re で
        # compile 検証する（不正パターンが初回発話で SyntaxError → スクリプト全死を防ぐ）
        for c in (opt.get("compounds") or []) + list(_PRESET_COMPOUNDS.get(opt.get("preset", ""), [])):
            try:
                re.compile(c)
            except re.error as e:
                raise SystemExit(
                    f"[ERROR] label='{label}' の compounds 正規表現が不正です: '{c}' ({e})")
            compound_patterns.append({"regex": c, "result": label})

    # 最長一致: キーワード長の降順で登録（同長は定義順）
    keyword_patterns = [
        {"regex": re.escape(k), "result": lbl}
        for k, lbl in sorted(keyword_entries, key=lambda x: -len(x[0]))
    ]

    return {
        "dtmf_map": dtmf_map,
        "token_map": token_map,
        "digit_keyword_patterns": [],
        "compound_patterns": compound_patterns,
        "keyword_patterns": keyword_patterns,
    }


def gen_n_choice_script(block):
    """enum_classifier / youken → n_choice engine（認定部品）に spec を充填して配線する。"""
    input_module = block.get("input_module", "")
    if not input_module:
        print("WARN: input_module が未指定です", file=sys.stderr)
    # 旧 gen_youken_script 系の repeat_guard/repeat_limit は n_choice engine に存在しない
    # （REPEAT 判定は scaffold の STT wiring / repeat filter が担当）。指定されても
    # 黙って落とさず明示警告する（REPEAT 分岐 edge が dead になるのを気づけるように）。
    if block.get("repeat_guard") or block.get("repeat_limit"):
        print(f"  [WARN] block '{block.get('module_name', '?')}': repeat_guard/repeat_limit は"
              f" n_choice engine では無視されます（REPEAT は scaffold の repeat filter が担当）。"
              f" scaffold 側 REPEAT edge の有無を確認してください", file=sys.stderr)

    config = build_n_choice_config(block)

    # 生成時検証: n_choice oracle の lint（各リテラルが自ラベルへ分類されるか = shadow 検出）
    oracle = _load_n_choice_oracle()
    issues = oracle.lint_config(config)
    if issues:
        for i in issues:
            print(f"  [LINT] {i['where']}: '{i['literal']}' は {i['result']} のはずが"
                  f" {i['got']} に分類されます", file=sys.stderr)
        raise SystemExit(
            f"[ERROR] n_choice spec lint 失敗 {len(issues)} 件 — "
            f"キーワード衝突/シャドーを解消してください（fail-closed）")

    dtmf_map = config["dtmf_map"]
    token_map = config["token_map"]
    compound_patterns = config["compound_patterns"]
    keyword_patterns = config["keyword_patterns"]

    with open(N_CHOICE_TEMPLATE, encoding="utf-8") as f:
        tpl = f.read()
    return (tpl
            .replace("{{INPUT_MODULE}}", input_module)
            .replace("{{CONTEXT_NAME}}", block.get("save_to", "") or "")
            .replace("{{CONTEXT_DISPLAY_TYPE}}", block.get("display_type", "TEXT") or "TEXT")
            .replace("{{DTMF_MAP}}", _js_json(dtmf_map))
            .replace("{{TOKEN_MAP}}", _js_json(token_map))
            .replace("{{DIGIT_KEYWORD_PATTERNS}}", _js_json([]))
            .replace("{{COMPOUND_PATTERNS}}", _js_json(compound_patterns))
            .replace("{{KEYWORD_PATTERNS}}", _js_json(keyword_patterns)))


GENERATORS = {
    # 監査 #1 対応: youken / enum_classifier は認定 n_choice engine へ配線
    # （旧 gen_youken_script / gen_enum_classifier_script は退役 — 部分一致+定義順先勝ちのため）
    "youken":          gen_n_choice_script,
    "enum_classifier": gen_n_choice_script,
    "faq":             gen_faq_script,
    "department":      gen_department_script,
}


# ---- scaffold JSON への埋め込み ----

def find_module(flow_data, module_name):
    """フロー JSON（再帰）からモジュール名で検索し、dict を返す"""
    if isinstance(flow_data, list):
        for item in flow_data:
            result = find_module(item, module_name)
            if result is not None:
                return result
    elif isinstance(flow_data, dict):
        if flow_data.get("name") == module_name:
            return flow_data
        for v in flow_data.values():
            result = find_module(v, module_name)
            if result is not None:
                return result
    return None


def validate_input_modules(scaffold, script_blocks):
    """
    script_blocks の input_module が scaffold JSON に存在するか検証する。
    存在しない場合は WARNING を出す（SKIP はしない — 生成は続ける）。
    """
    for block in script_blocks:
        input_mod   = block.get("input_module", "")
        module_name = block.get("module_name", "")
        if not input_mod:
            continue
        if find_module(scaffold, input_mod) is None:
            print(
                f"  [WARN] input_module '{input_mod}' が scaffold に見つかりません"
                f"（block: {module_name}）— モジュール名を確認してください",
                file=sys.stderr,
            )


def embed_scripts(scaffold, script_blocks):
    """scaffold JSON に Scripts コードを埋め込む"""
    applied = []
    skipped = []

    for block in script_blocks:
        block_type  = block.get("type", "")
        module_name = block.get("module_name", "")

        gen_fn = GENERATORS.get(block_type)
        if not gen_fn:
            skipped.append(f"{module_name}: 未知のtype={block_type}")
            continue

        script_code = gen_fn(block)

        module_obj = find_module(scaffold, module_name)
        if module_obj is None:
            skipped.append(f"{module_name}: scaffold に見つかりません")
            continue

        if "params" not in module_obj:
            module_obj["params"] = {}
        module_obj["params"]["script"] = script_code
        applied.append(module_name)

    return applied, skipped


# ---- メイン ----

def main():
    parser = argparse.ArgumentParser(
        description="設計書 YAML の script_blocks から ES5 Scripts を生成し scaffold JSON に埋め込む"
    )
    parser.add_argument("--yaml",     required=True, help="設計書 YAML ファイルパス")
    parser.add_argument("--scaffold", required=True, help="scaffold JSON ファイルパス")
    parser.add_argument("--out",      required=True, help="出力 JSON ファイルパス")
    parser.add_argument("--presets",  default="",    help="keyword_presets.yaml パス（省略時は自動検索）")
    args = parser.parse_args()

    for path in [args.yaml, args.scaffold]:
        if not os.path.exists(path):
            print(f"ERROR: ファイルが見つかりません: {path}", file=sys.stderr)
            sys.exit(1)

    # プリセット読み込み
    load_presets(args.presets or None)

    with open(args.yaml, encoding="utf-8") as f:
        design = yaml.safe_load(f)

    script_blocks = design.get("script_blocks", [])
    if not script_blocks:
        print("WARNING: 設計書 YAML に script_blocks セクションがありません。", file=sys.stderr)
        sys.exit(0)

    print(f"script_blocks: {len(script_blocks)} ブロック", file=sys.stderr)

    with open(args.scaffold, encoding="utf-8") as f:
        scaffold = json.load(f)

    # input_module 存在チェック
    validate_input_modules(scaffold, script_blocks)

    applied, skipped = embed_scripts(scaffold, script_blocks)

    for name in applied:
        print(f"  [OK] {name}", file=sys.stderr)
    for msg in skipped:
        print(f"  [SKIP] {msg}", file=sys.stderr)

    os.makedirs(os.path.dirname(args.out) if os.path.dirname(args.out) else ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(scaffold, f, ensure_ascii=False, indent=2)

    print(
        f"出力: {args.out}  (適用 {len(applied)} 件, スキップ {len(skipped)} 件)",
        file=sys.stderr,
    )
    if skipped:
        print("  スキップ項目を確認してください（module_name と scaffold の一致を確認）", file=sys.stderr)


if __name__ == "__main__":
    main()
