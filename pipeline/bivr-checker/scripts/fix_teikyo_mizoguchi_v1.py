#!/usr/bin/env python3
"""
fix_teikyo_mizoguchi_v1.py — 帝京大学附属溝口病院 診療フロー PROMPT-001 修正パッチ

修正内容:
  - OpenAI モジュールの prompt 出力仕様に、next条件の stripped ラベルを追加
  - 担当医モジュールの prose 形式 bullet を clean label 形式に修正
  - 空の jump スロットを削除
  - .bivr 再構築
"""

import json
import os
import sys
import glob
import zipfile
from urllib.parse import quote

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

FIXED_DIR = "output/帝京大学付属溝口病院/fixed/flows"
MAIN_FLOW = os.path.join(FIXED_DIR, "帝京溝口$診療_20260413.json")
BIVR_OUT = "output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed.bivr"


def add_bullets_to_output_spec(prompt: str, labels: list[str]) -> str:
    """
    prompt の # 出力仕様 セクションに、labels を箇条書きとして追加する。
    既に存在する場合はスキップ。
    挿入位置: セクション末尾の --- または次の # の直前。
    """
    for label in labels:
        bullet = f"- {label}"
        if bullet in prompt:
            continue  # already present
        # Find the 出力仕様 section
        idx = prompt.find("# 出力仕様")
        if idx < 0:
            continue
        # Find end of section (next # heading or ---)
        rest = prompt[idx:]
        # Find the last bullet before a separator or next section
        lines = rest.split("\n")
        insert_line_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            if i == 0:
                continue  # skip the heading line itself
            if stripped.startswith("#") and i > 0:
                insert_line_idx = i
                break
        if insert_line_idx is None:
            # End of prompt
            prompt = prompt.rstrip() + f"\n{bullet}\n"
        else:
            # Insert before the line at insert_line_idx (within rest)
            # Find last bullet line before insert_line_idx
            last_bullet_idx = None
            for i in range(insert_line_idx - 1, 0, -1):
                if lines[i].strip().startswith("-") or lines[i].strip().startswith("*"):
                    last_bullet_idx = i
                    break
            if last_bullet_idx is not None:
                insert_pos = last_bullet_idx + 1
            else:
                insert_pos = 1  # after heading line
            lines.insert(insert_pos, bullet)
            rest = "\n".join(lines)
            prompt = prompt[:idx] + rest
    return prompt


def fix_prose_bullet(prompt: str, old_text: str, clean_label: str, note: str = "") -> str:
    """
    output spec 内の prose 形式 bullet を clean label に置換し、
    説明文は ※ コメントとして後に追記する。
    """
    old_bullet = f"- {old_text}"
    new_bullet = f"- {clean_label}"
    if old_bullet not in prompt:
        return prompt
    if note:
        replacement = f"{new_bullet}\n※ {note}"
    else:
        replacement = new_bullet
    return prompt.replace(old_bullet, replacement, 1)


def clean_empty_next_slots(mods):
    """empty condition/label/nextModuleName スロットを削除"""
    count = 0
    for mod in mods.values():
        next_arr = mod.get("next", [])
        cleaned = [n for n in next_arr if n.get("condition") or n.get("nextModuleName")]
        if len(cleaned) < len(next_arr):
            count += len(next_arr) - len(cleaned)
            mod["next"] = cleaned
    return count


def main():
    print("=== 帝京大学附属溝口病院 PROMPT-001 修正パッチ ===")
    print()

    with open(MAIN_FLOW, encoding='utf-8') as f:
        flow = json.load(f)
    mods = flow["modules"]

    # ── Fix 1: OpenAI_診療科_再診 ──
    mod = mods.get("OpenAI_診療科_再診")
    if mod:
        print("[Fix 1] OpenAI_診療科_再診: grouped label追加")
        p = mod["params"]["prompt"]
        p = add_bullets_to_output_spec(p, ["(精神科|心療内科)", "(歯科|口腔外科)"])
        mod["params"]["prompt"] = p
        print("  [OK] (精神科|心療内科), (歯科|口腔外科) を出力仕様に追加")
    else:
        print("[SKIP] OpenAI_診療科_再診 not found")

    # ── Fix 2: OpenAI_担当医_リハ ──
    mod = mods.get("OpenAI_担当医_リハ")
    if mod:
        print("\n[Fix 2] OpenAI_担当医_リハ: prose bullet → clean label")
        p = mod["params"]["prompt"]
        old = '原先生（「原」「はら」「原先生」「はらせんせい」に該当する場合）'
        p = fix_prose_bullet(p, old, "原先生",
            "「原」「はら」「原先生」「はらせんせい」に該当する場合に「原先生」を出力すること。それ以外はユーザーの発話内容をそのまま出力（「先生」が付いていない場合は「先生」を付加する）。")
        # Remove 'ユーザーの発話内容をそのまま（...）' bullet if it exists (covered by success ^.+$)
        p = p.replace(
            "- ユーザーの発話内容をそのまま（正規化後のテキスト。「先生」が付いていない場合は「先生」を付加する）\n",
            "")
        mod["params"]["prompt"] = p
        print("  [OK] 原先生 bullet を clean label に修正")
    else:
        print("[SKIP] OpenAI_担当医_リハ not found")

    # ── Fix 3: OpenAI_診療科_初診 ──
    mod = mods.get("OpenAI_診療科_初診")
    if mod:
        print("\n[Fix 3] OpenAI_診療科_初診: grouped label追加")
        p = mod["params"]["prompt"]
        p = add_bullets_to_output_spec(p, [
            "(精神科|心療内科)",
            "(歯科|口腔外科)",
            "(産科|妊婦健診|小児眼科|斜視外来)",
        ])
        mod["params"]["prompt"] = p
        print("  [OK] (精神科|心療内科), (歯科|口腔外科), (産科|妊婦健診|小児眼科|斜視外来) を追加")
    else:
        print("[SKIP] OpenAI_診療科_初診 not found")

    # ── Fix 4: OpenAI_担当医_初診 ──
    mod = mods.get("OpenAI_担当医_初診")
    if mod:
        print("\n[Fix 4] OpenAI_担当医_初診: prose bullet → clean label")
        p = mod["params"]["prompt"]
        old = '平井先生（「平井」「ひらい」「平井先生」「ひらいせんせい」に該当する場合）'
        p = fix_prose_bullet(p, old, "平井先生",
            "「平井」「ひらい」「平井先生」「ひらいせんせい」に該当する場合に「平井先生」を出力すること。それ以外はユーザーの発話内容をそのまま出力（「先生」が付いていない場合は「先生」を付加する）。")
        p = p.replace(
            "- ユーザーの発話内容をそのまま（正規化後のテキスト。「先生」が付いていない場合は「先生」を付加する）\n",
            "")
        mod["params"]["prompt"] = p
        print("  [OK] 平井先生 bullet を clean label に修正")
    else:
        print("[SKIP] OpenAI_担当医_初診 not found")

    # ── Fix 5: OpenAI_診療科_変更 ──
    mod = mods.get("OpenAI_診療科_変更")
    if mod:
        print("\n[Fix 5] OpenAI_診療科_変更: grouped label追加")
        p = mod["params"]["prompt"]
        p = add_bullets_to_output_spec(p, [
            "(精神科|心療内科)",
            "(歯科|口腔外科)",
            "(放射線科|補聴器外来)",
        ])
        mod["params"]["prompt"] = p
        print("  [OK] (精神科|心療内科), (歯科|口腔外科), (放射線科|補聴器外来) を追加")
    else:
        print("[SKIP] OpenAI_診療科_変更 not found")

    # ── Fix 6: OpenAI_検査内容 ──
    mod = mods.get("OpenAI_検査内容")
    if mod:
        print("\n[Fix 6] OpenAI_検査内容: grouped label追加")
        p = mod["params"]["prompt"]
        p = add_bullets_to_output_spec(p, ["(MRI|CT|内視鏡)"])
        mod["params"]["prompt"] = p
        print("  [OK] (MRI|CT|内視鏡) を追加")
    else:
        print("[SKIP] OpenAI_検査内容 not found")

    # ── Fix 7: OpenAI_診療科_キャンセル ──
    mod = mods.get("OpenAI_診療科_キャンセル")
    if mod:
        print("\n[Fix 7] OpenAI_診療科_キャンセル: grouped label追加")
        p = mod["params"]["prompt"]
        p = add_bullets_to_output_spec(p, [
            "(精神科|心療内科)",
            "(歯科|口腔外科)",
            "(放射線科|補聴器外来)",
        ])
        mod["params"]["prompt"] = p
        print("  [OK] (精神科|心療内科), (歯科|口腔外科), (放射線科|補聴器外来) を追加")
    else:
        print("[SKIP] OpenAI_診療科_キャンセル not found")

    # ── Fix 8: 空スロット削除 ──
    print("\n[Fix 8] 空 next スロット削除")
    removed = clean_empty_next_slots(mods)
    print(f"  [OK] {removed} スロット削除")

    # ── 保存 ──
    with open(MAIN_FLOW, 'w', encoding='utf-8') as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] saved: {MAIN_FLOW}")

    # ── .bivr 再構築 ──
    flow_files = glob.glob(os.path.join(FIXED_DIR, "*.json"))
    with zipfile.ZipFile(BIVR_OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fpath in flow_files:
            with open(fpath, encoding='utf-8') as f:
                fl = json.load(f)
            flow_name = fl.get("name", "")
            entry_name = f"flows/@flow_{quote(flow_name, safe='')}.txt"
            json_str = json.dumps(fl, ensure_ascii=False, separators=(',', ':'))
            zf.writestr(entry_name, json_str.encode('utf-8'))
    size = os.path.getsize(BIVR_OUT)
    print(f"[OK] .bivr rebuilt: {BIVR_OUT} ({size:,} bytes)")
    print()
    print("=== 完了 ===")


if __name__ == "__main__":
    main()
