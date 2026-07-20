#!/usr/bin/env python3
"""
verify_fixes.py -- 修正済みフローJSONの品質検証スクリプト

修正済みフローJSONを教師データの統計と照合し、品質スコアを算出する。

Usage:
    python scripts/verify_fixes.py output/貝塚病院_健診_20260417.json [output/貝塚病院_氏名聴取_20260417.json ...]
"""

import json
import sys
import os
import subprocess
import re
import io

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

HEAD_CLIP_PATTERNS = [
    ("よやく", "やく"),
    ("へんこう", "んこう"),
    ("しょうわ", "ょうわ"),
    ("れいわ", "いわ"),
    ("へいせい", "いせい"),
    ("たいしょう", "いしょう"),
    ("いちがつ", "ちがつ"),
    ("にがつ", "がつ"),
    ("ついたち", "いたち"),
]

# ============================================================
# ヘルパー
# ============================================================

def load_flow(path):
    """フローJSONを読み込む"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_modules_by_type(flow_data, *types):
    """指定タイプのモジュールを取得"""
    modules = flow_data.get("modules", {})
    result = {}
    for name, mod in modules.items():
        mod_type = mod.get("type", "")
        if mod_type in types:
            result[name] = mod
    return result


def get_word_count(profile_words):
    """profile_wordsの語数をカウント"""
    if not profile_words:
        return 0
    return len([line for line in profile_words.split("\n") if line.strip()])


def detect_input_type(module_name, modules, mod):
    """入力種別を推定（freetext判定用）"""
    search_text = module_name.lower()
    # yes_no keywords
    yes_no_kw = ["復唱", "よろしい", "正しい", "確認"]
    if any(k in module_name for k in yes_no_kw):
        return "yes_no"
    # freetext keywords (問い合わせ、連絡事項、その他 etc.)
    freetext_kw = ["連絡事項", "問い合わせ", "フリー", "自由", "その他"]
    if any(k in module_name for k in freetext_kw):
        return "freetext"
    return "general"


def has_fillers(profile_words):
    """フィラーTOP6が含まれるかチェック"""
    if not profile_words:
        return False
    lines = [line.strip() for line in profile_words.split("\n") if line.strip()]
    for line in lines:
        parts = line.split(" ", 1)
        yomi = parts[1] if len(parts) == 2 else parts[0]
        for f in FILLER_TOP6:
            if yomi.startswith(f) and yomi != f:
                return True
    return False


def has_head_clip(profile_words):
    """頭切れパターンが含まれるかチェック"""
    if not profile_words:
        return False
    lines = [line.strip() for line in profile_words.split("\n") if line.strip()]
    all_yomi = []
    for line in lines:
        parts = line.split(" ", 1)
        yomi = parts[1] if len(parts) == 2 else parts[0]
        all_yomi.append(yomi)

    yomi_set = set(all_yomi)
    for full, clipped in HEAD_CLIP_PATTERNS:
        if clipped in yomi_set:
            return True

    # Generic head-clip detection
    hyouki_yomis = {}
    for line in lines:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            hyouki, yomi = parts
            if hyouki not in hyouki_yomis:
                hyouki_yomis[hyouki] = []
            hyouki_yomis[hyouki].append(yomi)
    for hyouki, yomis in hyouki_yomis.items():
        if len(yomis) > 1:
            longest = max(yomis, key=len)
            for y in yomis:
                if y != longest and longest.endswith(y):
                    return True
    return False


def has_maa(profile_words):
    """「まー」が含まれるかチェック"""
    if not profile_words:
        return False
    lines = [line.strip() for line in profile_words.split("\n") if line.strip()]
    for line in lines:
        parts = line.split(" ", 1)
        yomi = parts[1] if len(parts) == 2 else parts[0]
        if yomi == "まー" or yomi.startswith("まー"):
            # 「まー」単独、またはフィラーとして「まー」で始まるもの
            # ただし「ま」は許可（FILLER_TOP6に含まれる）
            if "まー" in yomi:
                return True
    return False


def find_module_after_stt(tts_name, all_modules):
    """TTS -> STT -> 次モジュール のチェーンを辿り、STT成功遷移先を返す"""
    tts_mod = all_modules.get(tts_name, {})
    tts_next = None
    for nx in tts_mod.get("next", []):
        if nx.get("nextModuleName"):
            tts_next = nx["nextModuleName"]
            break
    if not tts_next:
        return None, None

    stt_mod = all_modules.get(tts_next, {})
    stt_type = stt_mod.get("type", "")
    if stt_type not in (STT_TYPE, DTMF_TYPE):
        return None, None

    for nx in stt_mod.get("next", []):
        cond = nx.get("condition", "")
        if cond in ("^.+$", "^.*$"):
            next_name = nx["nextModuleName"]
            next_mod = all_modules.get(next_name, {})
            return next_name, next_mod
    return None, None


def check_retry_false_consistency(all_retry, all_flows):
    """リトライfalse遷移先の整合性チェック

    Returns:
        (mismatch_count, mismatch_details): 不一致件数と詳細リスト
    """
    # 全フローのモジュールを統合
    all_modules = {}
    for flow_data in all_flows:
        all_modules.update(flow_data.get("modules", {}))

    skip_conds = {"^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", "^.*$", ""}
    mismatch_count = 0
    mismatch_details = []

    for name, mod, _ in all_retry:
        true_dest = ""
        false_dest = ""
        for n in mod.get("next", []):
            if n.get("condition") == "true":
                true_dest = n.get("nextModuleName", "")
            elif n.get("condition") == "false":
                false_dest = n.get("nextModuleName", "")

        if not true_dest:
            continue

        next_name, next_mod = find_module_after_stt(true_dest, all_modules)
        if not next_mod:
            continue

        # 次モジュールの分岐を解析
        specific_branches = []
        wildcard_dest = ""
        for nx in next_mod.get("next", []):
            cond = nx.get("condition", "")
            nm = nx.get("nextModuleName", "")
            if cond in skip_conds:
                if cond in ("^.+$", "^.*$"):
                    wildcard_dest = nm
            else:
                specific_branches.append((cond, nm))

        has_branch = len(specific_branches) > 0

        if has_branch:
            # 分岐あり → false遷移先はtrue遷移先と同じ（無限ループ）
            correct_false = true_dest
        else:
            # 分岐なし → false遷移先はワイルドカード遷移先（次へ進む）
            correct_false = wildcard_dest

        if correct_false and false_dest != correct_false:
            mismatch_count += 1
            mismatch_details.append({
                "retry": name,
                "current_false": false_dest,
                "expected_false": correct_false,
                "reason": "無限ループ" if has_branch else "次へ進む",
            })

    return mismatch_count, mismatch_details


def check_retry_tts_japanese(all_retry, all_flows):
    """Retry→TTS日本語接続チェック (WARNING出力のみ)

    Returns:
        warnings: WARNINGリスト
    """
    all_modules = {}
    for flow_data in all_flows:
        all_modules.update(flow_data.get("modules", {}))

    warnings = []
    # 「再度、」の後に自然につながる質問語
    question_starts = [
        "ご用件", "お名前", "診療科", "ご希望", "お聞か", "お伝え",
        "おっしゃ", "お話", "お選び", "何科", "お住まい", "郵便番号",
        "担当者", "受診", "ご回答", "市町村", "コース", "検査", "検診",
        "オプション", "ご予約", "お答え", "企業名", "組合名",
        "変更", "キャンセル", "ご連絡", "お電話番号",
    ]

    for name, mod, _ in all_retry:
        true_dest = ""
        for n in mod.get("next", []):
            if n.get("condition") == "true":
                true_dest = n.get("nextModuleName", "")

        if not true_dest:
            continue

        prompt_true = mod.get("params", {}).get("prompt_true", "")
        # prompt_true の末尾を取得
        pt_match = re.search(r"\{tts_g:(.+?)\}", prompt_true)
        pt_text = pt_match.group(1).strip() if pt_match else ""
        if not pt_text:
            continue

        tts_mod = all_modules.get(true_dest, {})
        if tts_mod.get("type") != TTS_TYPE:
            continue

        tts_prompt = tts_mod.get("params", {}).get("prompt", "")
        tts_match = re.search(r"\{tts_g:(.+?)\}", tts_prompt)
        tts_text = tts_match.group(1).strip() if tts_match else ""

        ends_with_saido = pt_text.endswith("再度、")

        if ends_with_saido:
            if not tts_text:
                # TTS prompt空の場合もWARNING
                warnings.append(
                    f"[WARN] {name}: prompt_true末尾『再度、』+ TTS先頭『(空)』"
                    f"が不自然。方法A(prompt_true修正)または方法B(STT直接指定)を検討"
                )
            else:
                found_question = any(tts_text.startswith(q) for q in question_starts)
                if not found_question:
                    tts_head = tts_text[:15]
                    warnings.append(
                        f"[WARN] {name}: prompt_true末尾『再度、』+ TTS先頭『{tts_head}』"
                        f"が不自然。方法A(prompt_true修正)または方法B(STT直接指定)を検討"
                    )

    return warnings


def check_openai_prompt(prompt):
    """OpenAIプロンプトの品質チェック（7セクション完全準拠）"""
    results = {
        "has_role": False,
        "has_context": False,
        "has_output_spec": False,
        "has_security": False,
        "has_algorithm": False,
        "has_fewshot": False,
        "has_important_principles": False,
        "has_no_result": False,
    }
    if not prompt:
        return results

    # # Role
    results["has_role"] = bool(re.search(r"#\s*Role", prompt))
    # # Context
    results["has_context"] = bool(re.search(r"#\s*Context", prompt))
    # # 出力仕様
    results["has_output_spec"] = bool(re.search(r"#\s*出力仕様", prompt))
    # セキュリティ/プロンプトインジェクション
    results["has_security"] = bool(
        re.search(r"(インジェクション|セキュリティ)", prompt)
    )
    # # 判定アルゴリズム AND STEP構造（STEP1〜STEP4）
    has_algo_header = bool(re.search(r"#\s*判定アルゴリズム", prompt))
    has_step1 = bool(re.search(r"STEP\s*1", prompt))
    has_step2 = bool(re.search(r"STEP\s*2", prompt))
    results["has_algorithm"] = has_algo_header and has_step1 and has_step2
    # # Few-Shot AND 例が15個以上（→ が15個以上）
    has_fewshot_header = bool(re.search(r"#\s*Few-Shot|#\s*Few\s*Shot", prompt))
    arrow_count = len(re.findall(r"→", prompt))
    results["has_fewshot"] = has_fewshot_header and arrow_count >= 15
    results["fewshot_arrow_count"] = arrow_count
    # 重要原則
    results["has_important_principles"] = bool(re.search(r"重要原則", prompt))
    # NO_RESULT
    results["has_no_result"] = "NO_RESULT" in prompt

    return results


def run_validator(flow_paths, script_dir):
    """validator.py を subprocess で呼び出してCRITICAL数を取得"""
    validator_path = os.path.join(script_dir, "validator.py")
    if not os.path.exists(validator_path):
        return None, "validator.py が見つかりません"

    cmd = [sys.executable, validator_path] + flow_paths + ["--json", "--no-props"]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        # --json outputs JSON array
        output = result.stdout.strip()
        if output:
            data = json.loads(output)
            total_critical = 0
            all_issues = []
            for r in data:
                total_critical += r.get("critical_count", 0)
                for issue in r.get("issues", []):
                    if issue.get("severity") == "CRITICAL":
                        all_issues.append(issue)
            return total_critical, all_issues
        else:
            # If no JSON output, try parsing exit code
            return (0 if result.returncode == 0 else -1), result.stderr
    except subprocess.TimeoutExpired:
        return -1, "validator.py タイムアウト"
    except json.JSONDecodeError as e:
        return -1, f"validator.py JSON解析エラー: {e}"
    except Exception as e:
        return -1, f"validator.py 実行エラー: {e}"


# ============================================================
# メイン検証ロジック
# ============================================================

def verify_flows(flow_paths):
    """全フローを検証して品質スコアを算出"""
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # 全フローのモジュールを収集
    all_stt_dtmf = []  # (name, mod, flow_data)
    all_openai = []     # (name, mod, flow_data)
    all_retry = []      # (name, mod, flow_data)
    all_tts = []        # (name, mod, flow_data)
    all_flows = []
    total_modules = 0

    for path in flow_paths:
        flow_data = load_flow(path)
        all_flows.append(flow_data)
        modules = flow_data.get("modules", {})
        total_modules += len(modules)

        for name, mod in modules.items():
            mod_type = mod.get("type", "")
            if mod_type in (STT_TYPE, DTMF_TYPE):
                all_stt_dtmf.append((name, mod, flow_data))
            elif mod_type == OAI_TYPE:
                all_openai.append((name, mod, flow_data))
            elif mod_type == RETRY_TYPE:
                all_retry.append((name, mod, flow_data))
            elif mod_type == TTS_TYPE:
                all_tts.append((name, mod, flow_data))

    results = {
        "flow_count": len(flow_paths),
        "total_modules": total_modules,
        "checks": {},
        "score": 0,
    }

    # ============================================================
    # A. profile_words 品質 (配点40点)
    # ============================================================
    pw_checks = {}

    # A-1: 空モジュール (10点)
    empty_count = 0
    stt_total = len(all_stt_dtmf)
    for name, mod, _ in all_stt_dtmf:
        pw = mod.get("params", {}).get("profile_words", "")
        wc = get_word_count(pw)
        if wc == 0:
            empty_count += 1
    pw_checks["empty"] = {
        "label": "空モジュール",
        "pass_count": stt_total - empty_count,
        "total": stt_total,
        "fail_count": empty_count,
        "max_score": 8,
        "score": 8 if empty_count == 0 else 0,
        "status": "OK" if empty_count == 0 else "FAIL",
    }

    # A-2: 語数範囲 50-300 (10点)
    range_ok = 0
    for name, mod, _ in all_stt_dtmf:
        pw = mod.get("params", {}).get("profile_words", "")
        wc = get_word_count(pw)
        if wc == 0:
            # 空は A-1 でカウント済み、ここではスキップ
            continue
        if 50 <= wc <= 300:
            range_ok += 1
    non_empty = stt_total - empty_count
    pw_checks["word_range"] = {
        "label": "語数範囲(50-300)",
        "pass_count": range_ok,
        "total": non_empty,
        "max_score": 8,
        "score": round(8 * (range_ok / non_empty), 1) if non_empty > 0 else 8,
        "status": "OK" if non_empty == 0 or range_ok == non_empty else "WARN",
    }

    # A-3: フィラーTOP6含有 (10点) — freetext以外
    filler_targets = []
    filler_ok = 0
    for name, mod, flow_data in all_stt_dtmf:
        pw = mod.get("params", {}).get("profile_words", "")
        input_type = detect_input_type(name, flow_data.get("modules", {}), mod)
        if input_type == "freetext":
            continue
        filler_targets.append(name)
        if has_fillers(pw):
            filler_ok += 1
    filler_total = len(filler_targets)
    filler_rate = (filler_ok / filler_total * 100) if filler_total > 0 else 100
    pw_checks["fillers"] = {
        "label": "フィラーTOP6含有",
        "pass_count": filler_ok,
        "total": filler_total,
        "rate": round(filler_rate, 1),
        "max_score": 6,
        "score": round(6 * min(filler_rate / 80, 1), 1) if filler_total > 0 else 6,
        "status": "OK" if filler_rate >= 80 else "WARN",
    }

    # A-4: 頭切れパターン含有 (5点)
    clip_targets = []
    clip_ok = 0
    for name, mod, flow_data in all_stt_dtmf:
        pw = mod.get("params", {}).get("profile_words", "")
        input_type = detect_input_type(name, flow_data.get("modules", {}), mod)
        if input_type == "freetext":
            continue
        clip_targets.append(name)
        if has_head_clip(pw):
            clip_ok += 1
    clip_total = len(clip_targets)
    clip_rate = (clip_ok / clip_total * 100) if clip_total > 0 else 100
    pw_checks["head_clip"] = {
        "label": "頭切れ含有",
        "pass_count": clip_ok,
        "total": clip_total,
        "rate": round(clip_rate, 1),
        "max_score": 4,
        "score": round(4 * min(clip_rate / 70, 1), 1) if clip_total > 0 else 4,
        "status": "OK" if clip_rate >= 70 else "WARN",
    }

    # A-5: 「まー」不在 (4点)
    maa_count = 0
    for name, mod, _ in all_stt_dtmf:
        pw = mod.get("params", {}).get("profile_words", "")
        if has_maa(pw):
            maa_count += 1
    pw_checks["no_maa"] = {
        "label": "「まー」不在",
        "fail_count": maa_count,
        "total": stt_total,
        "max_score": 4,
        "score": 4 if maa_count == 0 else 0,
        "status": "OK" if maa_count == 0 else "FAIL",
    }

    # A-6: detection_flag チェック (絶対遵守事項 — 空/検出しない は FAIL)
    df_bad = 0
    df_details = []
    for name, mod, _ in all_stt_dtmf:
        df = mod.get("params", {}).get("detection_flag", "")
        if df != "デフォルト":
            df_bad += 1
            df_details.append(f"{name}: detection_flag=\"{df or '(empty)'}\" (should be \"デフォルト\")")
    pw_checks["detection_flag"] = {
        "label": "detection_flag",
        "pass_count": stt_total - df_bad,
        "total": stt_total,
        "fail_count": df_bad,
        "max_score": 5,
        "score": 5 if df_bad == 0 else 0,
        "status": "OK" if df_bad == 0 else "FAIL",
        "details": df_details if df_details else [],
    }

    # A-7: 全角数字チェック (絶対遵守事項 — 全角があれば FAIL)
    zenkaku_bad = 0
    zenkaku_details = []
    for name, mod, _ in all_stt_dtmf:
        pw = mod.get("params", {}).get("profile_words", "")
        if pw:
            zenkaku_chars = [c for c in pw if '\uff10' <= c <= '\uff19']
            if zenkaku_chars:
                zenkaku_bad += 1
                zenkaku_details.append(f"{name}: 全角数字{len(zenkaku_chars)}文字")
    pw_checks["zenkaku_digits"] = {
        "label": "全角数字",
        "pass_count": stt_total - zenkaku_bad,
        "total": stt_total,
        "fail_count": zenkaku_bad,
        "max_score": 5,
        "score": 5 if zenkaku_bad == 0 else 0,
        "status": "OK" if zenkaku_bad == 0 else "FAIL",
        "details": zenkaku_details if zenkaku_details else [],
    }

    pw_subtotal = sum(c["score"] for c in pw_checks.values())
    results["checks"]["profile_words"] = {
        "label": "A. profile_words",
        "max_score": 40,
        "score": pw_subtotal,
        "items": pw_checks,
    }

    # ============================================================
    # B. OpenAIプロンプト品質 (配点40点)
    # ============================================================
    oai_checks = {}
    oai_total = len(all_openai)

    if oai_total > 0:
        # 全OpenAIモジュールのチェック結果を事前計算
        all_prompt_checks = []
        for n, m, _ in all_openai:
            prompt = m.get("params", {}).get("prompt", "")
            all_prompt_checks.append(check_openai_prompt(prompt))

        # B-1: # Role (4点)
        role_ok = sum(1 for c in all_prompt_checks if c["has_role"])
        oai_checks["role"] = {
            "label": "# Role",
            "pass_count": role_ok,
            "total": oai_total,
            "rate": round(role_ok / oai_total * 100, 1),
            "max_score": 4,
            "score": 4 if role_ok == oai_total else round(4 * role_ok / oai_total, 1),
            "status": "OK" if role_ok == oai_total else "FAIL",
        }

        # B-2: # Context (4点)
        ctx_ok = sum(1 for c in all_prompt_checks if c["has_context"])
        oai_checks["context"] = {
            "label": "# Context",
            "pass_count": ctx_ok,
            "total": oai_total,
            "rate": round(ctx_ok / oai_total * 100, 1),
            "max_score": 4,
            "score": 4 if ctx_ok == oai_total else round(4 * ctx_ok / oai_total, 1),
            "status": "OK" if ctx_ok == oai_total else "FAIL",
        }

        # B-3: # 出力仕様 (4点)
        out_ok = sum(1 for c in all_prompt_checks if c["has_output_spec"])
        oai_checks["output_spec"] = {
            "label": "# 出力仕様",
            "pass_count": out_ok,
            "total": oai_total,
            "rate": round(out_ok / oai_total * 100, 1),
            "max_score": 4,
            "score": 4 if out_ok == oai_total else round(4 * out_ok / oai_total, 1),
            "status": "OK" if out_ok == oai_total else "FAIL",
        }

        # B-4: セキュリティ/プロンプトインジェクション (4点)
        sec_ok = sum(1 for c in all_prompt_checks if c["has_security"])
        oai_checks["security"] = {
            "label": "セキュリティ",
            "pass_count": sec_ok,
            "total": oai_total,
            "rate": round(sec_ok / oai_total * 100, 1),
            "max_score": 4,
            "score": 4 if sec_ok == oai_total else round(4 * sec_ok / oai_total, 1),
            "status": "OK" if sec_ok == oai_total else "FAIL",
        }

        # B-5: # 判定アルゴリズム + STEP構造 (8点)
        algo_ok = sum(1 for c in all_prompt_checks if c["has_algorithm"])
        oai_checks["algorithm"] = {
            "label": "判定アルゴリズム+STEP",
            "pass_count": algo_ok,
            "total": oai_total,
            "rate": round(algo_ok / oai_total * 100, 1),
            "max_score": 8,
            "score": 8 if algo_ok == oai_total else round(8 * algo_ok / oai_total, 1),
            "status": "OK" if algo_ok == oai_total else "FAIL",
        }

        # B-6: # Few-Shot + 例15個以上 (8点)
        fs_ok = sum(1 for c in all_prompt_checks if c["has_fewshot"])
        oai_checks["fewshot"] = {
            "label": "Few-Shot(15例+)",
            "pass_count": fs_ok,
            "total": oai_total,
            "rate": round(fs_ok / oai_total * 100, 1),
            "max_score": 8,
            "score": 8 if fs_ok == oai_total else round(8 * fs_ok / oai_total, 1),
            "status": "OK" if fs_ok == oai_total else "FAIL",
        }

        # B-7: # 重要原則（再掲） (4点)
        imp_ok = sum(1 for c in all_prompt_checks if c["has_important_principles"])
        oai_checks["important_principles"] = {
            "label": "重要原則（再掲）",
            "pass_count": imp_ok,
            "total": oai_total,
            "rate": round(imp_ok / oai_total * 100, 1),
            "max_score": 4,
            "score": 4 if imp_ok == oai_total else round(4 * imp_ok / oai_total, 1),
            "status": "OK" if imp_ok == oai_total else "FAIL",
        }

        # B-8: NO_RESULT (4点)
        nr_ok = sum(1 for c in all_prompt_checks if c["has_no_result"])
        oai_checks["no_result"] = {
            "label": "NO_RESULT",
            "pass_count": nr_ok,
            "total": oai_total,
            "rate": round(nr_ok / oai_total * 100, 1),
            "max_score": 4,
            "score": 4 if nr_ok == oai_total else round(4 * nr_ok / oai_total, 1),
            "status": "OK" if nr_ok == oai_total else "FAIL",
        }
    else:
        # No OpenAI modules
        for key, label, max_s in [
            ("role", "# Role", 4), ("context", "# Context", 4),
            ("output_spec", "# 出力仕様", 4), ("security", "セキュリティ", 4),
            ("algorithm", "判定アルゴリズム+STEP", 8), ("fewshot", "Few-Shot(15例+)", 8),
            ("important_principles", "重要原則（再掲）", 4), ("no_result", "NO_RESULT", 4),
        ]:
            oai_checks[key] = {
                "label": label, "pass_count": 0, "total": 0,
                "max_score": max_s, "score": max_s, "status": "N/A",
            }

    oai_subtotal = sum(c["score"] for c in oai_checks.values())
    results["checks"]["openai_prompt"] = {
        "label": "B. OpenAIプロンプト",
        "max_score": 40,
        "score": oai_subtotal,
        "items": oai_checks,
    }

    # ============================================================
    # C. 構造品質 (配点20点)
    # ============================================================
    struct_checks = {}

    # C-1: validator.py CRITICAL = 0 (8点)
    critical_count, critical_detail = run_validator(flow_paths, script_dir)
    if critical_count is None:
        # validator.py not found
        struct_checks["critical"] = {
            "label": "CRITICAL",
            "fail_count": -1,
            "max_score": 8,
            "score": 0,
            "status": "ERROR",
            "detail": str(critical_detail),
        }
    elif critical_count < 0:
        struct_checks["critical"] = {
            "label": "CRITICAL",
            "fail_count": -1,
            "max_score": 8,
            "score": 0,
            "status": "ERROR",
            "detail": str(critical_detail),
        }
    else:
        struct_checks["critical"] = {
            "label": "CRITICAL",
            "fail_count": critical_count,
            "max_score": 8,
            "score": 8 if critical_count == 0 else 0,
            "status": "OK" if critical_count == 0 else "FAIL",
        }

    # C-2: Retry prompt_false が空でない (4点)
    retry_total = len(all_retry)
    retry_nonempty = 0
    for name, mod, _ in all_retry:
        pf = mod.get("params", {}).get("prompt_false", "")
        if pf.strip():
            retry_nonempty += 1
    struct_checks["prompt_false"] = {
        "label": "prompt_false非空",
        "pass_count": retry_nonempty,
        "total": retry_total,
        "max_score": 2,
        "score": round(2 * (retry_nonempty / retry_total), 1) if retry_total > 0 else 2,
        "status": "OK" if retry_total == 0 or retry_nonempty == retry_total else "WARN",
    }

    # C-3: TTS next label が "Next Module" (4点)
    tts_total = len(all_tts)
    tts_ok = 0
    for name, mod, _ in all_tts:
        nexts = mod.get("next", [])
        all_nm = True
        for n in nexts:
            if n.get("label", "") != "Next Module":
                all_nm = False
                break
        if all_nm and nexts:
            tts_ok += 1
    struct_checks["tts_label"] = {
        "label": "TTS label",
        "pass_count": tts_ok,
        "total": tts_total,
        "max_score": 4,
        "score": round(4 * (tts_ok / tts_total), 1) if tts_total > 0 else 4,
        "status": "OK" if tts_total == 0 or tts_ok == tts_total else "WARN",
    }

    # C-4: リトライfalse整合性 (4点)
    retry_false_mismatch, retry_false_details = check_retry_false_consistency(
        all_retry, all_flows
    )
    struct_checks["retry_false"] = {
        "label": "リトライfalse整合性",
        "fail_count": retry_false_mismatch,
        "total": retry_total,
        "max_score": 4,
        "score": 4 if retry_false_mismatch == 0 else 0,
        "status": "OK" if retry_false_mismatch == 0 else "FAIL",
    }
    if retry_false_details:
        struct_checks["retry_false"]["details"] = retry_false_details

    # C-5: Retry→TTS日本語接続チェック（2点）
    retry_tts_warnings = check_retry_tts_japanese(all_retry, all_flows)
    retry_tts_bad = len(retry_tts_warnings)
    struct_checks["retry_tts_japanese"] = {
        "label": "Retry→TTS日本語接続",
        "fail_count": retry_tts_bad,
        "max_score": 2,
        "score": 2 if retry_tts_bad == 0 else 0,
        "status": "OK" if retry_tts_bad == 0 else "WARN",
    }

    # C-5: saveContextModel2DB fields チェック（標準12フィールド全属性）
    # CLAUDE.md Section 7「標準フィールド（デフォルト12フィールド）」に準拠
    DEFAULT_FIELDS = {
        "classification":       {"displayType": "CLASSIFICATION",    "editable": True,  "deletable": False, "itemDefault": True},
        "patientName":          {"displayType": "TEXT",              "editable": True,  "deletable": False, "itemDefault": True},
        "medicalCardNumber":    {"displayType": "NUMBER",            "editable": True,  "deletable": False, "itemDefault": True},
        "clinicalDepartment":   {"displayType": "DEPARTMENT",        "editable": True,  "deletable": False, "itemDefault": True},
        "patientDateOfBirth":   {"displayType": "DATE_OF_BIRTH",     "editable": True,  "deletable": False, "itemDefault": True},
        "reason":               {"displayType": "TEXT",              "editable": True,  "deletable": False, "itemDefault": True},
        "reservationDate":      {"displayType": "DATE",              "editable": True,  "deletable": False, "itemDefault": True},
        "telephoneNumber":      {"displayType": "PHONE_NUMBER_CALL", "editable": False, "deletable": False, "itemDefault": True},
        "additionalPhoneNumber":{"displayType": "PHONE_NUMBER",      "editable": True,  "deletable": False, "itemDefault": True},
        "status":               {"displayType": "STATUS",            "editable": True,  "deletable": False, "itemDefault": True},
        "callId":               {"displayType": "NUMBER",            "editable": True,  "deletable": True,  "itemDefault": False},
        "dateOfCall":           {"displayType": "DATE",              "editable": False, "deletable": False, "itemDefault": True},
    }
    fields_warnings = []
    for flow_data in all_flows:
        for mname, mod in flow_data.get("modules", {}).items():
            if "saveContextModel2DB" in mod.get("type", ""):
                fields_str = mod.get("params", {}).get("fields", "")
                if fields_str:
                    try:
                        fields_list = json.loads(fields_str)
                        field_map = {f["contextName"]: f for f in fields_list}
                        # 標準12フィールド全属性チェック
                        for cn, expected in DEFAULT_FIELDS.items():
                            if cn not in field_map:
                                fields_warnings.append(f"{cn}: missing (standard field required)")
                                continue
                            actual = field_map[cn]
                            for attr in ["displayType", "editable", "deletable", "itemDefault"]:
                                if actual.get(attr) != expected[attr]:
                                    fields_warnings.append(
                                        f"{cn}.{attr}={actual.get(attr)} (should be {expected[attr]})"
                                    )
                        # status.rangeValues 5値チェック
                        if "status" in field_map:
                            rv = field_map["status"].get("rangeValues", [])
                            if len(rv) < 5:
                                fields_warnings.append(f"status.rangeValues: {len(rv)} values (should be 5)")
                    except json.JSONDecodeError:
                        fields_warnings.append("fields JSON parse error")
    if fields_warnings:
        struct_checks["fields_check"] = {
            "label": "fields定義",
            "fail_count": len(fields_warnings),
            "max_score": 0,
            "score": 0,
            "status": "WARN",
            "details": fields_warnings,
        }

    struct_subtotal = sum(c["score"] for c in struct_checks.values())
    results["checks"]["structure"] = {
        "label": "C. 構造",
        "max_score": 20,
        "score": struct_subtotal,
        "items": struct_checks,
    }
    if retry_tts_warnings:
        results["checks"]["structure"]["warnings"] = retry_tts_warnings

    # ============================================================
    # 総合スコア
    # ============================================================
    results["score"] = pw_subtotal + oai_subtotal + struct_subtotal
    results["max_score"] = 100
    results["pass"] = results["score"] >= 80
    results["judgment"] = "PASS" if results["pass"] else "FAIL"

    return results


# ============================================================
# コンソール出力
# ============================================================

def format_check_line(check, key=None):
    """1つのチェック項目を整形"""
    status = check.get("status", "?")
    label = check.get("label", "?")
    max_score = check.get("max_score", 0)
    score = check.get("score", 0)

    if status == "OK":
        icon = "[OK] "
    elif status == "WARN":
        icon = "[WARN]"
    elif status == "FAIL":
        icon = "[FAIL]"
    elif status == "N/A":
        icon = "[N/A]"
    else:
        icon = "[ERR]"

    # Build detail string
    if "rate" in check:
        detail = f"{check['pass_count']}/{check['total']} ({check['rate']}%)"
    elif "fail_count" in check and "total" in check:
        if check["fail_count"] >= 0:
            detail = f"{check['fail_count']}件"
        else:
            detail = check.get("detail", "エラー")
    elif "pass_count" in check and "total" in check:
        detail = f"{check['pass_count']}/{check['total']}"
    elif "fail_count" in check:
        if check["fail_count"] >= 0:
            detail = f"{check['fail_count']}件"
        else:
            detail = check.get("detail", "エラー")
    else:
        detail = ""

    label_padded = label.ljust(20)
    detail_padded = detail.ljust(25)
    score_str = f"{score}/{max_score}"

    return f"  {icon} {label_padded} {detail_padded} {score_str}"


def print_report(results):
    """コンソールにレポートを出力"""
    sep = "=" * 60

    print(sep)
    print("[VERIFY] 品質検証結果")
    print(sep)
    print(f"フロー数: {results['flow_count']}  総モジュール数: {results['total_modules']}")
    print()

    for section_key in ["profile_words", "openai_prompt", "structure"]:
        section = results["checks"][section_key]
        print(f"--- {section['label']} ({section['max_score']}点) ---")
        for item_key, item in section["items"].items():
            print(format_check_line(item, item_key))
        print(f"  小計: {section['score']}/{section['max_score']}")
        print()

    print(sep)
    print(f"総合スコア: {results['score']}/{results['max_score']}")
    print(f"判定: {results['judgment']} (80点以上で合格)")
    print(sep)


# ============================================================
# メイン
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/verify_fixes.py <flow.json> [flow2.json ...]")
        print()
        print("修正済みフローJSONの品質スコアを算出します。")
        sys.exit(1)

    flow_paths = []
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            continue
        if not os.path.isfile(arg):
            print(f"[WARN] ファイルが見つかりません: {arg}", file=sys.stderr)
            continue
        flow_paths.append(arg)

    if not flow_paths:
        print("[ERROR] 検証対象のファイルがありません。", file=sys.stderr)
        sys.exit(1)

    results = verify_flows(flow_paths)

    # Console output
    print_report(results)

    # ⛔ BLOCKER check: profile_words quality gate
    pw_section = results.get("checks", {}).get("profile_words", {}).get("items", {})
    blockers = []

    # A-1: 空モジュールは BLOCKER
    empty_item = pw_section.get("empty", {})
    if empty_item.get("fail_count", 0) > 0:
        blockers.append(f"A-1 空モジュール {empty_item['fail_count']}件 — @pw-generator を実行してください")

    # A-2: 語数範囲 80%未満は警告
    range_item = pw_section.get("word_range", {})
    if range_item.get("total", 0) > 0:
        range_rate = range_item.get("pass_count", 0) / range_item["total"] * 100
        if range_rate < 50:
            blockers.append(f"A-2 語数範囲 {range_item['pass_count']}/{range_item['total']} ({range_rate:.0f}%) — @pw-generator の辞書が適用されていない可能性があります")

    # A-3: フィラー含有 50%未満は警告
    filler_item = pw_section.get("fillers", {})
    if filler_item.get("total", 0) > 0:
        filler_rate = filler_item.get("rate", 0)
        if filler_rate < 50:
            blockers.append(f"A-3 フィラー含有率 {filler_rate:.0f}% — @pw-generator の辞書が適用されていない可能性があります")

    if blockers:
        print()
        print("⛔" * 30)
        print("[BLOCKER] profile_words が教師データ水準に達していません。")
        print("以下を確認してください:")
        for b in blockers:
            print(f"  - {b}")
        print()
        print("【対処】@pw-generator エージェントを実行して辞書を再生成してください。")
        print("        ハードコード辞書での代用は禁止です（PIPELINE_SPEC.md Stage 2 参照）。")
        print("⛔" * 30)

    # JSON output to file (alongside input)
    output_dir = os.path.dirname(os.path.abspath(flow_paths[0]))
    output_path = os.path.join(output_dir, "verify_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n[INFO] 検証結果を保存しました: {output_path}")


if __name__ == "__main__":
    main()
