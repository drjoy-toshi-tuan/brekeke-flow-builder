#!/usr/bin/env python3
"""
structural_fixer.py -- VFBが繰り返す既知エラーパターンを機械的に修正する

Usage:
    python scripts/structural_fixer.py output/貝塚病院_健診_20260417.json [--dry-run]
    python scripts/structural_fixer.py output/*.json --dry-run

対応パターン（修正）:
    VFB-034: DTMF termdtmf/stop_play_when_speech 修正
    VFB-010: Retry prompt_true を標準文言に修正
    VFB-021/006: Retry prompt_false を設定
    VFB-007: Retry subs に save2db を接続
    VFB-025: saveCompletionFlag status=0 → status=2（非通知フロー名のみ）
    TTS label修正: TTS next label を "Next Module" に修正
    stop_by_dtmf修正: "true"/"false" → "No"/"Yes"
    STT success修正: 個別パターン → ^.+$ に統合
    DTMF retry修正: "0" → "2"
    DTMF prompt修正: {recstart} を設定

対応パターン（検出のみ）:
    VFB-001: ContextMatchRouter が存在しない
    VFB-002: Re-confirmation node data が存在しない
    VFB-016: profile_words が空
    VFB-028: DRY原則違反（同一プロンプトの重複モジュール）
    TERM-001: 到達不能な完了フラグ (CRITICAL)
    TERM-002: 到達不能な終話TTS (WARNING)
    TERM-003: 到達不能なDisconnect (WARNING)
    TERM-004: 完了フラグ→TTS名の不一致 (WARNING)
    TERM-005: 同一status+smsFlagの完了フラグがTTS文言も同一 (WARNING)
"""

import json
import sys
import os
import re
import glob
import argparse
import copy

# --- 定数 ---

STANDARD_PROMPT_TRUE = "{tts_g:申し訳ございません。 うまく聞き取りが出来ませんでした。 再度、}"
DEFAULT_PROMPT_FALSE_A = "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"

TYPE_TTS = "drjoy^Text To Speech$Text to speech"
TYPE_STT = "drjoy^AmiVoice$Speech to Text"
TYPE_DTMF = "drjoy^External Integration$DTMF AmiVoice STT Input"
TYPE_RETRY = "drjoy^Text To Speech$Speech Retry Counter"
TYPE_SAVE2DB = "drjoy^Persistence$save2db"
TYPE_COMPLETION_FLAG = "drjoy^Persistence$saveCompletionFlag2db"
TYPE_OPENAI = "drjoy^External Integration$generate_by_OpenAI"
TYPE_CMR = "drjoy^Context Logic$ContextMatchRouter"
TYPE_RECONFIRM = "drjoy^Text To Speech$Re-confirmation node data"


# --- I/O ---

def load_flow(path):
    """フローJSONを読み込み"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_flow(path, data):
    """フローJSONを保存（indent=2, ensure_ascii=False）"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


# --- 修正関数 ---

def fix_dtmf_termdtmf(flow):
    """VFB-034: DTMF termdtmf を # に、stop_play_when_speech を Yes に修正"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_DTMF:
            continue
        params = mod.get("params", {})

        if params.get("termdtmf") == "*":
            params["termdtmf"] = "#"
            fixes.append(f'  [FIX] VFB-034: {name} --termdtmf "*" → "#"')

        if params.get("stop_play_when_speech") == "No":
            params["stop_play_when_speech"] = "Yes"
            fixes.append(f'  [FIX] VFB-034: {name} --stop_play_when_speech "No" → "Yes"')

        if params.get("remove_term") != "Yes":
            old = params.get("remove_term", "(未設定)")
            params["remove_term"] = "Yes"
            fixes.append(f'  [FIX] VFB-034: {name} --remove_term "{old}" → "Yes"')

    return fixes


def fix_retry_prompt_true(flow):
    """VFB-010: Retry prompt_true を標準文言に修正"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_RETRY:
            continue
        params = mod.get("params", {})
        current = params.get("prompt_true", "")

        # 標準文言と異なる場合に修正（空文字は除く --意図的な空もあり得る）
        if current and current != STANDARD_PROMPT_TRUE:
            params["prompt_true"] = STANDARD_PROMPT_TRUE
            # 短縮表示
            display_old = current[:40] + "..." if len(current) > 40 else current
            fixes.append(f'  [FIX] VFB-010: {name} --prompt_true → 標準文言')

    return fixes


def fix_retry_prompt_false(flow):
    """VFB-021/006: Retry prompt_false が空文字 → パターンAデフォルト設定"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_RETRY:
            continue
        params = mod.get("params", {})
        current = params.get("prompt_false", "")

        if current == "":
            params["prompt_false"] = DEFAULT_PROMPT_FALSE_A
            fixes.append(f'  [FIX] VFB-021: {name} --prompt_false → パターンA')

    return fixes


def fix_retry_save2db(flow):
    """VFB-007: Retry subs に save2db を接続"""
    fixes = []
    modules = flow.get("modules", {})

    # まず既存の save2db パターンを探す（save-history や save-xxx）
    existing_save2db = []
    for mod_name, mod in modules.items():
        if mod.get("type") == TYPE_SAVE2DB:
            existing_save2db.append(mod_name)

    for name, mod in modules.items():
        if mod.get("type") != TYPE_RETRY:
            continue
        subs = mod.get("subs", [])

        # すでに save2db が接続されているか確認
        has_save = any(
            s.get("moduleName", "").startswith("save-") and s.get("moduleName", "") != ""
            for s in subs
        )
        if has_save:
            continue

        # 同名の聴取ステップの save2db を探す
        # リトライ_xxx → save-xxx のパターンを試す
        retry_suffix = name.replace("リトライ_", "")
        candidate_save = f"save-{retry_suffix}"

        # 前段のTTS/STTに接続されている save2db を使う
        # まず Retry の true 遷移先（TTS）を探す
        true_target = None
        for n in mod.get("next", []):
            if n.get("condition") == "true":
                true_target = n.get("nextModuleName", "")
                break

        save_target = None
        if true_target and true_target in modules:
            tts_mod = modules[true_target]
            for s in tts_mod.get("subs", []):
                sname = s.get("moduleName", "")
                if sname and sname.startswith("save-"):
                    save_target = sname
                    break

        # candidate_save が modules に存在するか確認
        if candidate_save in modules:
            save_target = candidate_save
        elif save_target is None and existing_save2db:
            # フォールバック: 最初に見つかった save2db を使う
            save_target = existing_save2db[0]

        if save_target:
            # subs の空きスロットに追加
            inserted = False
            for s in subs:
                if s.get("moduleName", "") == "":
                    s["moduleName"] = save_target
                    s["label"] = save_target
                    inserted = True
                    break
            if not inserted:
                # スロットがない場合は先頭に追加
                subs.insert(0, {"moduleName": save_target, "label": save_target})

            fixes.append(f'  [FIX] VFB-007: {name} --subs に {save_target} を接続')

    return fixes


def fix_completion_flag_status(flow):
    """VFB-025: status=0 を status=2 に修正（非通知フロー名のみ）"""
    fixes = []
    flow_name = flow.get("name", "")

    # フロー名に「非通知」を含む場合のみ適用... ではなく、
    # モジュール名に「非通知」「診察券なし」を含む saveCompletionFlag の status=0 を修正
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_COMPLETION_FLAG:
            continue
        params = mod.get("params", {})
        status = params.get("status", "")

        if status == "0":
            # 非通知・診察券なし終話パスの status=0 は status=2 に修正
            # ただし真の途中切断（モジュール名で判別）は除外
            if "非通知" in name or "診察券なし" in name or "代表" in name:
                params["status"] = "2"
                fixes.append(f'  [FIX] VFB-025: {name} --status "0" → "2"')
            else:
                fixes.append(f'  [WARN] VFB-025: {name} --status="0" を検出（要確認）')

    return fixes


def fix_tts_label(flow):
    """TTS next label を 'Next Module' に修正"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_TTS:
            continue
        for n in mod.get("next", []):
            cond = n.get("condition", "")
            label = n.get("label", "")
            if cond == "^.*$" and label != "Next Module" and label != "":
                old_label = label
                n["label"] = "Next Module"
                fixes.append(f'  [FIX] TTS-001: {name} --label "{old_label}" → "Next Module"')

    return fixes


def fix_stop_by_dtmf(flow):
    """stop_by_dtmf を 'No'/'Yes' に修正（"true"/"false" は誤り）"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_TTS:
            continue
        params = mod.get("params", {})
        val = params.get("stop_by_dtmf", "")

        if val == "true":
            params["stop_by_dtmf"] = "Yes"
            fixes.append(f'  [FIX] TTS-002: {name} --stop_by_dtmf "true" → "Yes"')
        elif val == "false":
            params["stop_by_dtmf"] = "No"
            fixes.append(f'  [FIX] TTS-002: {name} --stop_by_dtmf "false" → "No"')

    return fixes


def fix_stt_success(flow):
    """STT の success 遷移が ^.+$ でない場合に修正"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        mod_type = mod.get("type", "")
        if mod_type != TYPE_STT:
            continue

        next_list = mod.get("next", [])
        # success スロットを探す（condition が ^.+$ でない最後の非空スロット）
        has_standard_success = False
        non_standard_success = []

        for i, n in enumerate(next_list):
            cond = n.get("condition", "")
            label = n.get("label", "")
            if cond == "^.+$" and label == "success":
                has_standard_success = True
            elif cond and cond not in ("^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", ""):
                non_standard_success.append((i, n))

        if not has_standard_success and non_standard_success:
            # 最後の非標準パターンを ^.+$ に修正
            idx, slot = non_standard_success[-1]
            old_cond = slot["condition"]
            slot["condition"] = "^.+$"
            slot["label"] = "success"
            fixes.append(
                f'  [FIX] STT-003: {name} --success条件 "{old_cond}" → "^.+$"'
            )

    return fixes


def fix_dtmf_retry(flow):
    """DTMF の retry が "0" → "2" に修正"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_DTMF:
            continue
        params = mod.get("params", {})
        retry = params.get("retry", "")

        if retry == "0":
            params["retry"] = "2"
            fixes.append(f'  [FIX] DTMF-003: {name} --retry "0" → "2"')

    return fixes


def fix_dtmf_prompt(flow):
    """DTMF の params.prompt に {recstart} がない → {recstart} を設定"""
    fixes = []
    modules = flow.get("modules", {})
    for name, mod in modules.items():
        if mod.get("type") != TYPE_DTMF:
            continue
        params = mod.get("params", {})
        prompt = params.get("prompt", "")

        if "{recstart}" not in prompt:
            old = prompt if prompt else "(空)"
            params["prompt"] = "{recstart}"
            fixes.append(f'  [FIX] DTMF-001: {name} --prompt "{old}" → "{{recstart}}"')

    return fixes


# --- 検出のみ ---

def detect_warnings(flow):
    """検出のみのパターンをチェックして警告リストを返す"""
    warnings = []
    modules = flow.get("modules", {})

    # VFB-001: ContextMatchRouter が存在するか
    has_cmr = any(mod.get("type") == TYPE_CMR for mod in modules.values())
    if not has_cmr:
        warnings.append("  [WARN] VFB-001: ContextMatchRouter が存在しません")

    # VFB-002: Re-confirmation node data が存在するか
    has_reconfirm = any(mod.get("type") == TYPE_RECONFIRM for mod in modules.values())
    if not has_reconfirm:
        warnings.append("  [WARN] VFB-002: Re-confirmation node data が存在しません")

    # VFB-016: profile_words が空のSTTを検出
    for name, mod in modules.items():
        mod_type = mod.get("type", "")
        if mod_type in (TYPE_STT, TYPE_DTMF):
            params = mod.get("params", {})
            pw = params.get("profile_words", "")
            if not pw or pw.strip() == "":
                warnings.append(f"  [WARN] VFB-016: {name} --profile_words が空です")

    # VFB-028: DRY原則違反（同一プロンプトのTTSモジュールが複数存在）
    prompt_map = {}  # prompt → [module_names]
    for name, mod in modules.items():
        if mod.get("type") != TYPE_TTS:
            continue
        params = mod.get("params", {})
        prompt = params.get("prompt", "")
        if prompt and prompt.strip():
            prompt_map.setdefault(prompt, []).append(name)

    for prompt, names in prompt_map.items():
        if len(names) > 1:
            display = prompt[:30] + "..." if len(prompt) > 30 else prompt
            warnings.append(
                f"  [WARN] VFB-028: DRY原則違反 --同一プロンプトのTTSが{len(names)}個: "
                f"{', '.join(names[:3])}{'...' if len(names) > 3 else ''}"
            )

    # --- 終話チェーン整合性チェック (TERM-001 〜 TERM-005) ---

    # 逆引きマップ: モジュール名 → そのモジュールへ遷移してくるモジュール名のリスト
    reverse_map = {}  # target_name → [source_name, ...]
    for name, mod in modules.items():
        for n in mod.get("next", []):
            target = n.get("nextModuleName", "")
            if target:
                reverse_map.setdefault(target, []).append(name)

    # TERM-001: 到達不能な完了フラグ (CRITICAL)
    for name, mod in modules.items():
        if mod.get("type") != TYPE_COMPLETION_FLAG:
            continue
        sources = reverse_map.get(name, [])
        if len(sources) == 0:
            warnings.append(
                f"  [CRITICAL] TERM-001: {name} — 遷移元がありません（到達不能な完了フラグ）"
            )

    # TERM-002: 到達不能な終話TTS (WARNING)
    for name, mod in modules.items():
        if not name.startswith("END_"):
            continue
        if mod.get("type") != TYPE_TTS:
            continue
        sources = reverse_map.get(name, [])
        if len(sources) == 0:
            warnings.append(
                f"  [WARN] TERM-002: {name} — 遷移元がありません（到達不能な終話TTS）"
            )

    # TERM-003: 到達不能なDisconnect (WARNING)
    for name, mod in modules.items():
        if mod.get("type") != "@IVR$Disconnect":
            continue
        sources = reverse_map.get(name, [])
        if len(sources) == 0:
            warnings.append(
                f"  [WARN] TERM-003: {name} — 遷移元がありません（到達不能なDisconnect）"
            )

    # TERM-004: 完了フラグ→TTS名の不一致 (WARNING)
    for name, mod in modules.items():
        if mod.get("type") != TYPE_COMPLETION_FLAG:
            continue
        # 完了フラグ_{X} から {X} を抽出
        if not name.startswith("完了フラグ_"):
            continue
        flag_suffix = name[len("完了フラグ_"):]

        # 遷移先TTSモジュール名を取得
        for n in mod.get("next", []):
            target = n.get("nextModuleName", "")
            if not target or not target.startswith("END_"):
                continue
            end_suffix = target[len("END_"):]
            # flag_suffix と end_suffix が完全一致すればOK
            # 例: flag="代表案内" end="代表案内" → OK
            # 例: flag="受付完了" end="受付完了" → OK
            # 不一致の例:
            #   flag="代表案内" end="代表案内_新規予約" → WARNING（フラグが汎用なのにENDが特定ルート）
            #   flag="受付完了" end="受付完了_SMS無し" → WARNING（フラグとENDの対応が不自然）
            if flag_suffix == end_suffix:
                continue  # 完全一致 → OK
            # 不一致
            warnings.append(
                f"  [WARN] TERM-004: {name} → {target} — "
                f"名前の対応が不自然です（{flag_suffix} ≠ {end_suffix}）"
            )

    # TERM-005: 同一status+smsFlagの完了フラグがTTS文言も同一（DRY違反） (WARNING)
    # (status, smsFlag) でグループ化
    flag_groups = {}  # (status, smsFlag) → [(flag_name, tts_prompt), ...]
    for name, mod in modules.items():
        if mod.get("type") != TYPE_COMPLETION_FLAG:
            continue
        params = mod.get("params", {})
        status = params.get("status", "")
        sms_flag = params.get("smsFlag", "")
        group_key = (status, sms_flag)

        # 遷移先TTSのプロンプトを取得
        tts_prompt = None
        for n in mod.get("next", []):
            target = n.get("nextModuleName", "")
            if target and target in modules:
                target_mod = modules[target]
                if target_mod.get("type") == TYPE_TTS:
                    tts_prompt = target_mod.get("params", {}).get("prompt", "")
                    break

        flag_groups.setdefault(group_key, []).append((name, tts_prompt))

    for (status, sms_flag), entries in flag_groups.items():
        if len(entries) < 2:
            continue
        # 同一グループ内でプロンプトを比較
        prompts = [p for _, p in entries if p is not None]
        if len(prompts) < 2:
            continue
        # 全て同一かチェック
        if len(set(prompts)) == 1:
            flag_names = [n for n, _ in entries]
            warnings.append(
                f"  [WARN] TERM-005: DRY違反 — status={status}, smsFlag={sms_flag} の完了フラグが"
                f"{len(entries)}個あり、遷移先TTSプロンプトも同一です（集約可能）: "
                f"{', '.join(flag_names)}"
            )

    return warnings


# ============================================================
# Stage 1 追加修正: Brekeke必須要件
# ============================================================

SLOT_COUNTS = {
    "@General$Script": (12, 0), "drjoy^Context Logic$ContextMatchRouter": (10, 3),
    "drjoy^AmiVoice$Speech to Text": (11, 3), "drjoy^External Integration$DTMF AmiVoice STT Input": (11, 3),
    "drjoy^External Integration$generate_by_OpenAI": (10, 3), "drjoy^Text To Speech$Speech Retry Counter": (2, 3),
    "drjoy^Text To Speech$Text to speech": (1, 3), "drjoy^Text To Speech$Re-confirmation node data": (1, 3),
    "drjoy^Persistence$saveCompletionFlag2db": (1, 3), "drjoy^Persistence$saveContext2DB": (1, 3),
    "drjoy^Persistence$saveContextModel2DB": (1, 3), "drjoy^Persistence$save2db": (0, 0),
    "drjoy^External Integration$acceptance_times": (4, 3), "drjoy^Incoming$incoming-classifier": (5, 3),
    "drjoy^Custom Module$Custom Jump to Flow": (1, 3), "Custom$wait": (1, 3),
    "@IVR$Disconnect": (0, 0), "drjoy^External Integration$RAG": (4, 3),
    "drjoy^TS Custom Module$DOB Re-confirmation": (4, 3), "drjoy^TS Custom Module$Phone Normalization": (5, 3),
}
EMPTY_NEXT_SLOT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB_SLOT = {"moduleName": "", "label": ""}
KEY_ORDER = ["layout", "next", "subs", "name", "description", "matchingmethod", "type", "params"]
STT_TYPES = ("drjoy^AmiVoice$Speech to Text", "drjoy^External Integration$DTMF AmiVoice STT Input")


def fix_matchingmethod_type(flow):
    """matchingmethod を int型に変換（"1"→1, "0"→0）"""
    fixes = []
    for mname, mod in flow.get("modules", {}).items():
        mm = mod.get("matchingmethod")
        if isinstance(mm, str):
            mod["matchingmethod"] = int(mm) if mm.isdigit() else 1
            fixes.append(f"[FIX] MM-001: {mname} -- matchingmethod \"{mm}\" → {mod['matchingmethod']}")
        elif mm is None:
            mod["matchingmethod"] = 0 if "Retry" in mod.get("type", "") else 1
            fixes.append(f"[FIX] MM-001: {mname} -- matchingmethod missing → {mod['matchingmethod']}")
    return fixes


def fix_key_order(flow):
    """モジュールキーを正規順序に並び替え"""
    fixes = []
    modules = flow.get("modules", {})
    new_modules = {}
    for mname, mod in modules.items():
        keys = list(mod.keys())
        if keys[:len(KEY_ORDER)] != KEY_ORDER[:len(keys)]:
            ordered = {}
            for k in KEY_ORDER:
                if k in mod:
                    ordered[k] = mod[k]
            for k in mod:
                if k not in ordered:
                    ordered[k] = mod[k]
            new_modules[mname] = ordered
            fixes.append(f"[FIX] KEY-001: {mname} -- key order fixed")
        else:
            new_modules[mname] = mod
    flow["modules"] = new_modules
    return fixes


def fix_detection_flag_empty(flow):
    """STT/DTMFの detection_flag を "デフォルト" に修正（空/検出しない/未設定）"""
    fixes = []
    for mname, mod in flow.get("modules", {}).items():
        if mod.get("type", "") not in STT_TYPES:
            continue
        params = mod.get("params", {})
        df = params.get("detection_flag", "")
        if df != "デフォルト":
            params["detection_flag"] = "デフォルト"
            fixes.append(f"[FIX] DF-001: {mname} -- detection_flag \"{df or '(empty)'}\" → \"デフォルト\"")
    return fixes


def fix_maa_removal(flow):
    """profile_words から「まー」を含む行を削除"""
    fixes = []
    for mname, mod in flow.get("modules", {}).items():
        if mod.get("type", "") not in STT_TYPES:
            continue
        pw = mod.get("params", {}).get("profile_words", "")
        if not pw:
            continue
        lines = pw.split("\n")
        new_lines = []
        removed = 0
        for line in lines:
            parts = line.strip().split()
            if len(parts) >= 2 and "まー" in parts[1]:
                removed += 1
            else:
                new_lines.append(line)
        if removed > 0:
            mod["params"]["profile_words"] = "\n".join(new_lines)
            fixes.append(f"[FIX] MAA-001: {mname} -- removed {removed} lines with まー")
    return fixes


def fix_zenkaku_digits(flow):
    """profile_words 内の全角数字を半角に変換"""
    ZENKAKU = "０１２３４５６７８９"
    HANKAKU = "0123456789"
    fixes = []
    for mname, mod in flow.get("modules", {}).items():
        if mod.get("type", "") not in STT_TYPES:
            continue
        pw = mod.get("params", {}).get("profile_words", "")
        if not pw:
            continue
        new_pw = pw
        count = 0
        for z, h in zip(ZENKAKU, HANKAKU):
            c = new_pw.count(z)
            if c > 0:
                new_pw = new_pw.replace(z, h)
                count += c
        if count > 0:
            mod["params"]["profile_words"] = new_pw
            fixes.append(f"[FIX] ZEN-001: {mname} -- converted {count} full-width digits to half-width")
    return fixes


def fix_slot_counts(flow):
    """next/subs スロット数をタイプ別固定値に合わせる"""
    fixes = []
    for mname, mod in flow.get("modules", {}).items():
        mtype = mod.get("type", "")
        if mtype not in SLOT_COUNTS:
            continue
        exp_next, exp_subs = SLOT_COUNTS[mtype]
        cur_next = mod.get("next", [])
        cur_subs = mod.get("subs", [])
        if len(cur_next) != exp_next:
            if len(cur_next) > exp_next:
                mod["next"] = cur_next[:exp_next]
            else:
                mod["next"] = cur_next + [copy.deepcopy(EMPTY_NEXT_SLOT) for _ in range(exp_next - len(cur_next))]
            fixes.append(f"[FIX] SLOT-001: {mname} -- next {len(cur_next)} → {exp_next}")
        if len(cur_subs) != exp_subs:
            if len(cur_subs) > exp_subs:
                mod["subs"] = cur_subs[:exp_subs]
            else:
                mod["subs"] = cur_subs + [copy.deepcopy(EMPTY_SUB_SLOT) for _ in range(exp_subs - len(cur_subs))]
            fixes.append(f"[FIX] SLOT-001: {mname} -- subs {len(cur_subs)} → {exp_subs}")
    return fixes


def fix_context_model_fields(flow):
    """saveContextModel2DB の標準12フィールド属性を定義通りに修正"""
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
    REQUIRED_STATUS_RANGE = [
        {"id": "0", "order": 0, "value": "途中切断"},
        {"id": "1", "order": 1, "value": "未処理"},
        {"id": "2", "order": 2, "value": "代表案内"},
        {"id": "3", "order": 3, "value": "転送"},
        {"id": "6", "order": 6, "value": "時間外"},
    ]

    fixes = []
    modules = flow.get("modules", {})

    for mname, mod in modules.items():
        if "saveContextModel2DB" not in mod.get("type", ""):
            continue
        fields_str = mod.get("params", {}).get("fields", "")
        if not fields_str:
            continue
        try:
            fields_list = json.loads(fields_str)
        except json.JSONDecodeError:
            continue

        field_map = {f["contextName"]: f for f in fields_list}
        changed = False

        # 標準フィールド属性修正
        for cn, expected in DEFAULT_FIELDS.items():
            if cn not in field_map:
                continue
            actual = field_map[cn]
            for attr in ["displayType", "editable", "deletable", "itemDefault"]:
                if actual.get(attr) != expected[attr]:
                    old_val = actual.get(attr)
                    actual[attr] = expected[attr]
                    fixes.append(
                        f"[FIX] FIELDS: {mname} -- {cn}.{attr}: {old_val} → {expected[attr]}"
                    )
                    changed = True

        # status.rangeValues 5値補完
        if "status" in field_map:
            rv = field_map["status"].get("rangeValues", [])
            existing_ids = {str(r.get("id", "")) for r in rv}
            for req in REQUIRED_STATUS_RANGE:
                if req["id"] not in existing_ids:
                    rv.append(req)
                    fixes.append(f"[FIX] FIELDS: {mname} -- status.rangeValues: added id={req['id']} ({req['value']})")
                    changed = True
            if changed:
                field_map["status"]["rangeValues"] = sorted(rv, key=lambda r: int(r.get("order", r.get("id", 0))))

        # reservationDate 欠落補完
        if "reservationDate" not in field_map:
            new_field = {
                "contextName": "reservationDate",
                "contextNameJp": "予約日",
                "displayType": "DATE",
                "rangeValues": [],
                "editable": True,
                "deletable": False,
                "itemDefault": True,
            }
            idx = next((i for i, f in enumerate(fields_list) if f.get("contextName") == "callId"), len(fields_list))
            fields_list.insert(idx, new_field)
            fixes.append(f"[FIX] FIELDS: {mname} -- reservationDate field added")
            changed = True

        if changed:
            mod["params"]["fields"] = json.dumps(fields_list, ensure_ascii=False, indent=2)

    return fixes


# --- メインエントリ ---

def apply_all_fixes(flow, dry_run=False):
    """全修正を適用し、ログを返す"""
    all_fixes = []
    all_warnings = []

    # 修正ルールを順に適用
    fix_functions = [
        fix_matchingmethod_type,
        fix_key_order,
        fix_detection_flag_empty,
        fix_slot_counts,
        fix_maa_removal,
        fix_zenkaku_digits,
        fix_dtmf_termdtmf,
        fix_retry_prompt_true,
        fix_retry_prompt_false,
        fix_retry_save2db,
        fix_completion_flag_status,
        fix_tts_label,
        fix_stop_by_dtmf,
        fix_stt_success,
        fix_dtmf_retry,
        fix_dtmf_prompt,
        fix_context_model_fields,
    ]

    for fix_fn in fix_functions:
        fixes = fix_fn(flow)
        all_fixes.extend(fixes)

    # 検出のみ
    all_warnings = detect_warnings(flow)

    return all_fixes, all_warnings


def main():
    # Windows環境でのUTF-8出力対応
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr.encoding != "utf-8":
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="VFB出力の構造的自動修正")
    parser.add_argument("files", nargs="+", help="修正対象のフローJSON（glob対応）")
    parser.add_argument("--dry-run", action="store_true", help="修正せず結果のみ表示")
    args = parser.parse_args()

    # glob 展開
    expanded_files = []
    for pattern in args.files:
        matched = glob.glob(pattern)
        if matched:
            expanded_files.extend(matched)
        else:
            expanded_files.append(pattern)

    if not expanded_files:
        print("[ERROR] 対象ファイルが見つかりません", file=sys.stderr)
        return 1

    total_fixes = 0
    total_warnings = 0

    for filepath in expanded_files:
        if not os.path.isfile(filepath):
            print(f"[ERROR] ファイルが存在しません: {filepath}", file=sys.stderr)
            continue

        flow = load_flow(filepath)
        flow_name = flow.get("name", os.path.basename(filepath))
        module_count = len(flow.get("modules", {}))

        # dry-run の場合はコピーに適用
        if args.dry_run:
            import copy
            work_flow = copy.deepcopy(flow)
        else:
            work_flow = flow

        fixes, warnings = apply_all_fixes(work_flow, dry_run=args.dry_run)

        # フロー名 グループ名$フロー名 形式の自動修正 (S-002)
        current_name = work_flow.get("name", "")
        if "$" not in current_name and current_name:
            # ファイルパスからグループ名を推定
            # パターン: output/{施設名}/fixed/flows/{施設名}_xxx.json
            #           output/{施設名}_xxx.json
            abs_path = os.path.abspath(filepath)
            path_parts = abs_path.replace("\\", "/").split("/")
            group_name = ""
            # input/ or output/ の直下の施設名フォルダを探す
            for i, part in enumerate(path_parts):
                if part in ("input", "output") and i + 1 < len(path_parts):
                    candidate = path_parts[i + 1]
                    if candidate not in ("fixed", "extracted", "flows", "reports"):
                        group_name = candidate
                        break
            # ファイル名から施設名を推定（fallback）
            if not group_name:
                basename = os.path.splitext(os.path.basename(filepath))[0]
                # ファイル名が 施設名_フロー名_日付 形式なら施設名部分を取得
                if "_" in basename:
                    group_name = basename.split("_")[0]
            if group_name:
                new_name = f"{group_name}${current_name}" if not current_name.startswith("_") else f"{group_name}${'健診' if '健診' in filepath else '診療'}{current_name}"
                work_flow["name"] = new_name
                fixes.append(f"[FIX] S-002: flow name \"{current_name}\" → \"{new_name}\"")
                flow_name = new_name

        # 結果表示
        print("=" * 60)
        print(f"[STRUCTURAL_FIXER] 修正結果: {flow_name}")
        print("=" * 60)
        print(f"モジュール数: {module_count}")

        # 修正件数（[FIX] で始まるもののみカウント）
        fix_count = sum(1 for f in fixes if f.strip().startswith("[FIX]"))
        warn_in_fixes = [f for f in fixes if f.strip().startswith("[WARN]")]
        print(f"修正件数: {fix_count}")
        for f in fixes:
            print(f)

        warning_count = len(warnings) + len(warn_in_fixes)
        print(f"警告件数: {warning_count}")
        for w in warnings:
            print(w)

        total_fixes += fix_count
        total_warnings += warning_count

        # dry-run でなければ保存
        if not args.dry_run and fix_count > 0:
            save_flow(filepath, work_flow)
            print(f"\n[SAVED] {filepath}")
        elif args.dry_run:
            print(f"\n[DRY-RUN] 修正は適用されていません")

        print()

    # 複数ファイルの場合のサマリ
    if len(expanded_files) > 1:
        print("=" * 60)
        print(f"[SUMMARY] 総修正件数: {total_fixes} / 総警告件数: {total_warnings}")
        print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
