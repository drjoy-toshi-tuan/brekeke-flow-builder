#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pair_01 (帯広第一病院) VFB生成版から profile_words と OpenAI プロンプトのベースラインを抽出する
"""
import json, os, glob, urllib.parse, re, sys

sys.stdout.reconfigure(encoding='utf-8')

FLOWS_DIR = 'C:/Users/takahashi.s/VSCode/bivr-checker/training_data/pair_01/bivr_extracted/flows/'

# Load all flow files
flows = {}
for fp in glob.glob(os.path.join(FLOWS_DIR, '@flow_*.txt')):
    fname = os.path.basename(fp)
    decoded = urllib.parse.unquote(fname.replace('@flow_', '').replace('.txt', ''))
    with open(fp, 'r', encoding='utf-8') as f:
        data = json.load(f)
    flows[decoded] = data

STT_TYPES = [
    'drjoy^AmiVoice$Speech to Text',
    'drjoy^External Integration$DTMF AmiVoice STT Input'
]
OAI_TYPE = 'drjoy^External Integration$generate_by_OpenAI'

# ==============================
# PART 1: profile_words
# ==============================
print('=' * 80)
print('PART 1: profile_words の現状')
print('=' * 80)

all_empty_pw = []
all_set_pw = []

for flow_name, data in sorted(flows.items()):
    print(f'\n### フロー: {flow_name}')
    modules = data.get('modules', {})
    print(f'    モジュール数: {len(modules)}')

    stt_count = 0
    empty_pw = []
    set_pw = []

    for mod_name, mod in modules.items():
        mod_type = mod.get('type', '')
        if mod_type not in STT_TYPES:
            continue
        stt_count += 1
        params = mod.get('params', {})
        pw = params.get('profile_words', '')
        type_label = 'DTMF+STT' if 'DTMF' in mod_type else 'STT'

        if not pw or pw.strip() == '':
            empty_pw.append((mod_name, type_label))
            all_empty_pw.append((flow_name, mod_name, type_label))
            continue

        # Parse lines - profile_words uses \n as separator
        lines = [l for l in pw.split('\n') if l.strip()]

        # Check patterns
        has_filler = any(p in pw for p in ['あ ', 'え ', 'えー', 'あの', 'はい ', 'ま ', 'あー', 'えっと', 'んー'])
        has_gobi = any(p in pw for p in ['です', 'で ', 'なんですが', 'だけど', 'になります', 'でして'])
        has_atamakire = any(p in pw for p in ['やく', 'んこう', 'がつ', 'いたち', 'ょうわ', 'おうです', 'あい '])

        entry = {
            'flow': flow_name,
            'name': mod_name,
            'type': type_label,
            'line_count': len(lines),
            'has_filler': has_filler,
            'has_gobi': has_gobi,
            'has_atamakire': has_atamakire,
            'preview': lines[:20]
        }
        set_pw.append(entry)
        all_set_pw.append(entry)

    print(f'    STT/DTMFモジュール合計: {stt_count}')
    print(f'    profile_words 空: {len(empty_pw)}')
    print(f'    profile_words 設定済: {len(set_pw)}')

    if empty_pw:
        print(f'\n    --- profile_words が空のモジュール ({len(empty_pw)}個) ---')
        for name, tp in empty_pw:
            print(f'      [{tp}] {name}')

    if set_pw:
        print(f'\n    --- profile_words が設定されているモジュール ({len(set_pw)}個) ---')
        for item in set_pw:
            print(f'\n      [{item["type"]}] {item["name"]}')
            print(f'        行数: {item["line_count"]}')
            print(f'        フィラー: {"あり" if item["has_filler"] else "なし"}')
            print(f'        語尾パターン: {"あり" if item["has_gobi"] else "なし"}')
            print(f'        頭切れパターン: {"あり" if item["has_atamakire"] else "なし"}')
            print(f'        先頭20行:')
            for line in item['preview']:
                print(f'          {line}')

# ==============================
# PART 2: OpenAI prompts
# ==============================
print('\n\n' + '=' * 80)
print('PART 2: OpenAI プロンプトの現状')
print('=' * 80)

total_oai = 0
with_security = 0
with_fewshot = 0
with_role = 0
with_context = 0
with_output = 0

for flow_name, data in sorted(flows.items()):
    print(f'\n### フロー: {flow_name}')
    modules = data.get('modules', {})

    for mod_name, mod in modules.items():
        if mod.get('type') != OAI_TYPE:
            continue
        total_oai += 1

        params = mod.get('params', {})
        prompt = params.get('prompt', '')
        module_ref = params.get('module', '')
        prompt_tts = params.get('promptTTS', '')

        # Section headers
        headers = re.findall(r'^(#+\s+.+)$', prompt, re.MULTILINE)

        has_role_sec = bool(re.search(r'#\s*Role', prompt, re.IGNORECASE))
        has_context_sec = bool(re.search(r'#\s*Context', prompt, re.IGNORECASE))
        has_output_sec = bool(re.search(r'#\s*(出力|Output)', prompt, re.IGNORECASE))
        has_sec = bool(re.search(r'(セキュリティ|インジェクション|injection|security)', prompt, re.IGNORECASE))
        few_shot_matches = re.findall(r'(例[：:]|例\d|入力例|出力例|Example|サンプル)', prompt, re.IGNORECASE)
        has_fs = len(few_shot_matches) > 0

        if has_role_sec: with_role += 1
        if has_context_sec: with_context += 1
        if has_output_sec: with_output += 1
        if has_sec: with_security += 1
        if has_fs: with_fewshot += 1

        # Output values
        output_values = []
        in_output_section = False
        for line in prompt.split('\n'):
            if re.match(r'^#+\s*(出力|Output)', line, re.IGNORECASE):
                in_output_section = True
                continue
            if in_output_section and re.match(r'^#+\s', line):
                in_output_section = False
            if in_output_section and line.strip().startswith('-'):
                val = line.strip().lstrip('- ')
                # Extract just the key value before explanation
                parts = re.split(r'[：:（]', val, maxsplit=1)
                if parts:
                    output_values.append(parts[0].strip())

        # Next conditions
        next_list = mod.get('next', [])
        next_conditions = [(n.get('condition', ''), n.get('label', ''), n.get('nextModuleName', '')) for n in next_list]
        user_conditions = [c for c in next_conditions if c[0] not in ['^TIMEOUT$', '^ERROR$', '^NO_RESULT$', '']]

        print(f'\n  [{mod_name}]')
        print(f'    module参照: {module_ref}')
        print(f'    promptTTS: {"空" if not prompt_tts else prompt_tts[:50]}')
        print(f'    プロンプト文字数: {len(prompt)}')
        print(f'    セクション構造:')
        if headers:
            for h in headers:
                print(f'      {h}')
        else:
            print(f'      (セクション見出しなし)')
        print(f'    # Role: {"あり" if has_role_sec else "なし"}')
        print(f'    # Context: {"あり" if has_context_sec else "なし"}')
        print(f'    # 出力仕様: {"あり" if has_output_sec else "なし"}')
        print(f'    セキュリティ: {"あり" if has_sec else "なし"}')
        print(f'    Few-Shot: {"あり" if has_fs else "なし"} ({len(few_shot_matches)}件)')
        if output_values:
            print(f'    出力値: {output_values}')
        else:
            print(f'    出力値: (未検出)')

        # Branch labels (non-system)
        branch_labels = []
        for cond, label, target in user_conditions:
            if cond != '^.+$':
                branch_labels.append(label)

        print(f'    next分岐:')
        for cond, label, target in next_conditions:
            marker = ''
            if cond not in ['^TIMEOUT$', '^ERROR$', '^NO_RESULT$', '', '^.+$']:
                if output_values and label not in output_values:
                    marker = ' *** MISMATCH'
            print(f'      {cond:20s} label={label:20s} → {target}{marker}')

        # Consistency
        if branch_labels and output_values:
            bl_set = set(branch_labels)
            ov_set = set(output_values)
            missing_in_prompt = bl_set - ov_set
            missing_in_next = ov_set - bl_set
            if missing_in_prompt:
                print(f'    [整合性] next分岐にあるがprompt出力にない: {missing_in_prompt}')
            if missing_in_next:
                print(f'    [整合性] prompt出力にあるがnext分岐にない: {missing_in_next}')

# ==============================
# PART 3: Quality Summary
# ==============================
print('\n\n' + '=' * 80)
print('PART 3: 品質スコアサマリー')
print('=' * 80)

print(f'\n--- profile_words ---')
print(f'  全STT/DTMFモジュール: {len(all_empty_pw) + len(all_set_pw)}')
print(f'  profile_words設定済: {len(all_set_pw)}')
print(f'  profile_words空: {len(all_empty_pw)}')
if all_empty_pw:
    print(f'\n  空モジュール一覧:')
    for flow, name, tp in all_empty_pw:
        print(f'    [{tp}] {flow} / {name}')

print(f'\n  設定済モジュールの統計:')
if all_set_pw:
    line_counts = [e['line_count'] for e in all_set_pw]
    print(f'    行数: min={min(line_counts)}, max={max(line_counts)}, avg={sum(line_counts)/len(line_counts):.0f}')
    filler_count = sum(1 for e in all_set_pw if e['has_filler'])
    gobi_count = sum(1 for e in all_set_pw if e['has_gobi'])
    atama_count = sum(1 for e in all_set_pw if e['has_atamakire'])
    print(f'    フィラーパターンあり: {filler_count}/{len(all_set_pw)}')
    print(f'    語尾パターンあり: {gobi_count}/{len(all_set_pw)}')
    print(f'    頭切れパターンあり: {atama_count}/{len(all_set_pw)}')

print(f'\n--- OpenAIプロンプト ---')
print(f'  総数: {total_oai}')
print(f'  # Role あり: {with_role}/{total_oai}')
print(f'  # Context あり: {with_context}/{total_oai}')
print(f'  # 出力仕様 あり: {with_output}/{total_oai}')
print(f'  セキュリティ あり: {with_security}/{total_oai}')
print(f'  Few-Shot あり: {with_fewshot}/{total_oai}')

# Quality scores
print(f'\n  品質評価:')
print(f'    セクション構造: {"OK" if with_role >= total_oai * 0.8 else "NG"} (Role {with_role}/{total_oai})')
print(f'    セキュリティ: {"OK" if with_security >= total_oai * 0.5 else "NG"} ({with_security}/{total_oai})')
print(f'    Few-Shot: {"OK" if with_fewshot >= total_oai * 0.3 else "NG"} ({with_fewshot}/{total_oai})')
