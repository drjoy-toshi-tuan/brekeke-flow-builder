"""
入間ハート病院 3バージョン差分分析スクリプト
VFB → Fixed → Human の差分を4項目で分析する
"""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE = "training_data/feedback/corrections/入間ハート病院/extracted"

def load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_flows(version):
    d = f"{BASE}/{version}"
    flows = {}
    import os
    for fname in os.listdir(d):
        if fname.endswith('.json'):
            key = fname.replace('.json', '')
            flows[key] = load(f"{d}/{fname}")
    return flows

flows_vfb   = load_flows('vfb')
flows_fixed = load_flows('fixed')
flows_human = load_flows('human')

report = []

# ===========================
# 1. profile_words
# ===========================
report.append("# 入間ハート病院 差分分析レポート v2")
report.append("## 1. profile_words（単語登録）\n")

all_flow_names = sorted(set(list(flows_fixed.keys()) + list(flows_human.keys())))
for fname in all_flow_names:
    fflow = flows_fixed.get(fname, {}).get('modules', {})
    hflow = flows_human.get(fname, {}).get('modules', {})
    all_mods = sorted(set(list(fflow.keys()) + list(hflow.keys())))
    for mname in all_mods:
        f_pw = fflow.get(mname, {}).get('params', {}).get('profile_words', '')
        h_pw = hflow.get(mname, {}).get('params', {}).get('profile_words', '')
        if f_pw == h_pw and not f_pw:
            continue
        if f_pw != h_pw:
            report.append(f"### [{fname} / {mname}]")
            report.append(f"**FIXED:**\n```\n{f_pw}\n```")
            report.append(f"**HUMAN:**\n```\n{h_pw}\n```\n")
        elif f_pw:
            report.append(f"### [{fname} / {mname}] — SAME")
            report.append(f"```\n{f_pw}\n```\n")

# ===========================
# 2. saveContextModel2DB (コンテキストスキーマ設定)
# ===========================
report.append("\n## 2. saveContextModel2DB（コンテキストスキーマ設定）\n")

CTX_TYPE = "drjoy^Persistence$saveContextModel2DB"
for fname in all_flow_names:
    fflow = flows_fixed.get(fname, {}).get('modules', {})
    hflow = flows_human.get(fname, {}).get('modules', {})
    f_ctxmods = {k: v for k, v in fflow.items() if v.get('type') == CTX_TYPE}
    h_ctxmods = {k: v for k, v in hflow.items() if v.get('type') == CTX_TYPE}
    all_mod_names = sorted(set(list(f_ctxmods.keys()) + list(h_ctxmods.keys())))
    for mname in all_mod_names:
        f_fields = f_ctxmods.get(mname, {}).get('params', {}).get('fields', '')
        h_fields = h_ctxmods.get(mname, {}).get('params', {}).get('fields', '')
        if f_fields != h_fields:
            report.append(f"### [{fname} / {mname}]")
            try:
                f_parsed = json.dumps(json.loads(f_fields), ensure_ascii=False, indent=2) if f_fields else '(なし)'
            except:
                f_parsed = f_fields or '(なし)'
            try:
                h_parsed = json.dumps(json.loads(h_fields), ensure_ascii=False, indent=2) if h_fields else '(なし)'
            except:
                h_parsed = h_fields or '(なし)'
            report.append(f"**FIXED:**\n```json\n{f_parsed}\n```")
            report.append(f"**HUMAN:**\n```json\n{h_parsed}\n```\n")

# ===========================
# 3. saveContext2DB（各モジュールのコンテキスト保存）
# ===========================
report.append("\n## 3. saveContext2DB（各モジュールのコンテキスト保存）\n")

CTX2_TYPE = "drjoy^Persistence$saveContext2DB"
for fname in all_flow_names:
    fflow = flows_fixed.get(fname, {}).get('modules', {})
    hflow = flows_human.get(fname, {}).get('modules', {})
    f_mods = {k: v for k, v in fflow.items() if v.get('type') == CTX2_TYPE}
    h_mods = {k: v for k, v in hflow.items() if v.get('type') == CTX2_TYPE}
    all_mod_names = sorted(set(list(f_mods.keys()) + list(h_mods.keys())))
    for mname in all_mod_names:
        f_p = f_mods.get(mname, {}).get('params', {})
        h_p = h_mods.get(mname, {}).get('params', {})
        if f_p != h_p:
            report.append(f"### [{fname} / {mname}]")
            report.append(f"**FIXED:** contextName=`{f_p.get('contextName','')}` contextValue=`{f_p.get('contextValue','')}`")
            report.append(f"**HUMAN:** contextName=`{h_p.get('contextName','')}` contextValue=`{h_p.get('contextValue','')}`\n")
        # show modules only in human
        elif mname not in f_mods and mname in h_mods:
            report.append(f"### [HUMAN_ONLY {fname} / {mname}]")
            report.append(f"**HUMAN:** contextName=`{h_p.get('contextName','')}` contextValue=`{h_p.get('contextValue','')}`\n")

# ===========================
# 4. OpenAI prompt
# ===========================
report.append("\n## 4. OpenAIプロンプト\n")

OAI_TYPE = "drjoy^External Integration$generate_by_OpenAI"
for fname in all_flow_names:
    fflow = flows_fixed.get(fname, {}).get('modules', {})
    hflow = flows_human.get(fname, {}).get('modules', {})
    f_mods = {k: v for k, v in fflow.items() if v.get('type') == OAI_TYPE}
    h_mods = {k: v for k, v in hflow.items() if v.get('type') == OAI_TYPE}
    all_mod_names = sorted(set(list(f_mods.keys()) + list(h_mods.keys())))
    for mname in all_mod_names:
        f_p = f_mods.get(mname, {}).get('params', {})
        h_p = h_mods.get(mname, {}).get('params', {})
        f_prompt = f_p.get('prompt', '')
        h_prompt = h_p.get('prompt', '')
        f_module = f_p.get('module', '')
        h_module = h_p.get('module', '')
        if f_prompt != h_prompt or f_module != h_module:
            report.append(f"### [{fname} / {mname}]")
            if f_module != h_module:
                report.append(f"- module: FIXED=`{f_module}` → HUMAN=`{h_module}`")
            if f_prompt != h_prompt:
                report.append(f"**FIXED prompt:**\n```\n{f_prompt}\n```")
                report.append(f"**HUMAN prompt:**\n```\n{h_prompt}\n```\n")
        # human_only
        elif mname not in f_mods and mname in h_mods:
            report.append(f"### [HUMAN_ONLY {fname} / {mname}]")
            report.append(f"**HUMAN prompt:**\n```\n{h_prompt}\n```\n")

# ===========================
# 5. 新規モジュール（human_onlyの追加モジュール）
# ===========================
report.append("\n## 5. Human版のみに存在するモジュール\n")

for fname in all_flow_names:
    fflow = flows_fixed.get(fname, {}).get('modules', {})
    hflow = flows_human.get(fname, {}).get('modules', {})
    only_human = set(hflow.keys()) - set(fflow.keys())
    if only_human:
        report.append(f"### [{fname}]")
        for mname in sorted(only_human):
            mod = hflow[mname]
            report.append(f"- `{mname}` (type: `{mod.get('type','')}`) params: {list(mod.get('params',{}).keys())}")
        report.append("")

only_fixed_total = []
for fname in all_flow_names:
    fflow = flows_fixed.get(fname, {}).get('modules', {})
    hflow = flows_human.get(fname, {}).get('modules', {})
    only_fixed = set(fflow.keys()) - set(hflow.keys())
    if only_fixed:
        for mname in sorted(only_fixed):
            only_fixed_total.append(f"[{fname} / {mname}]")

if only_fixed_total:
    report.append("\n## 6. Fixed版のみに存在するモジュール（Humanで削除）\n")
    for item in only_fixed_total:
        report.append(f"- {item}")

# Write report
out_path = "training_data/feedback/corrections/入間ハート病院/diff_report_v2.md"
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report))

print(f"[OK] 差分レポート出力: {out_path}")
print(f"     セクション: profile_words / saveContextModel2DB / saveContext2DB / OpenAIプロンプト / 追加・削除モジュール")
