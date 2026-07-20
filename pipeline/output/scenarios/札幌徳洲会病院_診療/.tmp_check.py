import yaml
with open('output/scenarios/札幌徳洲会病院_診療/設計書_札幌徳洲会病院_診療.yaml', 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)

print('--- CMR check (each must end with match: other) ---')
for block in data['scenario_flow']:
    if block['type'] == 'context_match_router':
        last_match = block['conditions'][-1].get('match')
        print(f"  {block['step']}: last={last_match} -> {'OK' if last_match == 'other' else 'FAIL'}")

print('--- hearing enum CMR check ---')
for block in data['scenario_flow']:
    if block['type'] == 'hearing' and block.get('output_format') == 'enum' and 'conditions' in block:
        last_match = block['conditions'][-1].get('match') if block['conditions'] else None
        ok = last_match in ('other', 'default')
        print(f"  {block['step']}: last={last_match} -> {'OK' if ok else 'FAIL'}")

print('--- reference_module check ---')
for block in data['scenario_flow']:
    if 'reference_module' in block:
        print(f"  {block['step']}: reference_module={block['reference_module']}")

print('--- Verify all next references exist as steps ---')
all_steps = set(b['step'] for b in data['scenario_flow'])
all_terms = set(t['name'] for t in data['termination_patterns'])
all_targets = all_steps | all_terms
missing = []
for block in data['scenario_flow']:
    if 'next' in block and block.get('next') and block['next'] not in all_targets:
        missing.append((block['step'], block['next']))
    if 'conditions' in block:
        for cond in block['conditions']:
            if 'next' in cond and cond['next'] not in all_targets:
                missing.append((block['step'], cond['next']))
if missing:
    for m in missing:
        print(f"  MISSING: {m[0]} -> {m[1]}")
else:
    print('  All next references exist')

import re
print('--- Banned char check ---')
text = open('output/scenarios/札幌徳洲会病院_診療/設計書_札幌徳洲会病院_診療.yaml', 'r', encoding='utf-8').read()
banned = re.findall(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮]', text)
print(f"  Found banned chars: {len(banned)}")
