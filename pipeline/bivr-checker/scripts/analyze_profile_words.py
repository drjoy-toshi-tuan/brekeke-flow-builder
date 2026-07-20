import zipfile, json, re, os, urllib.parse, sys, io
from collections import Counter, defaultdict

BASE = "C:/Users/takahashi.s/VSCode/bivr-checker/training_data"
OUTPUT_FILE = "C:/Users/takahashi.s/VSCode/bivr-checker/scripts/profile_words_analysis_result.txt"

out_lines = []
def pr(s=""):
    out_lines.append(s)

# Collect all pair bivr files
bivr_files = {}
for i in range(1, 21):
    pair_dir = os.path.join(BASE, f"pair_{i:02d}")
    if not os.path.isdir(pair_dir):
        continue
    for f in os.listdir(pair_dir):
        if f.endswith('.bivr'):
            bivr_files[f"pair_{i:02d}"] = os.path.join(pair_dir, f)

pr("=== Found .bivr files ===")
for k, v in sorted(bivr_files.items()):
    pr(f"  {k}: {os.path.basename(v)}")

# Parse all flows from all bivr files
all_modules = []

for pair_name, bivr_path in sorted(bivr_files.items()):
    try:
        zf = zipfile.ZipFile(bivr_path)
    except:
        pr(f"  SKIP (not zip): {bivr_path}")
        continue

    for entry in zf.namelist():
        if not entry.startswith('flows/') or not entry.endswith('.txt'):
            continue
        data = zf.read(entry)
        text = data.decode('utf-8', errors='replace').lstrip('\ufeff')

        try:
            flow = json.loads(text)
        except json.JSONDecodeError:
            pr(f"  JSON parse error: {pair_name}/{entry}")
            continue

        flow_name = urllib.parse.unquote(entry.replace('flows/@flow_', '').replace('.txt', ''))

        modules = flow.get('modules', {})
        for mod_name, mod_data in modules.items():
            mod_type = mod_data.get('type', '')
            params = mod_data.get('params', {})
            pw = params.get('profile_words', '')

            if pw:
                all_modules.append({
                    'pair': pair_name,
                    'flow_name': flow_name,
                    'module_name': mod_name,
                    'module_type': mod_type,
                    'profile_words': pw,
                    'params': params,
                })

pr(f"\n=== Total modules with profile_words: {len(all_modules)} ===\n")

# Determine module category
def get_input_type(mod_type):
    if 'DTMF' in mod_type and 'STT' in mod_type:
        return 'STT+DTMF'
    elif 'DTMF' in mod_type:
        return 'DTMF'
    elif 'STT' in mod_type:
        return 'STT'
    else:
        return 'Other'

filler_patterns = [
    'そうですね', 'あのー', 'えーと', 'えっと', 'あー', 'あの', 'えー', 'んー',
    'はい', 'あ', 'え', 'ん', 'ま', 'まー',
]

tail_patterns = [
    'ですけれども', 'ですけども', 'なんですが', 'なんだけど', 'になります', 'なんです',
    'でして', 'だけど', 'です', 'だよ', 'って', 'で', 'ね', 'さ', 'か', 'が', 'の', 'に', 'を', 'は', 'や',
]

def guess_purpose(mod_name, flow_name):
    name = mod_name + ' ' + flow_name
    if any(k in name for k in ['用件', '要件', 'ようけん', '分岐', '振り分け', '振分']):
        return '用件分類'
    if any(k in name for k in ['氏名', '名前', 'しめい', 'なまえ', 'お名前']):
        return '氏名'
    if any(k in name for k in ['生年月日', 'せいねん', '誕生日']):
        return '生年月日'
    if any(k in name for k in ['診療科', '科目', 'しんりょうか']):
        return '診療科'
    if any(k in name for k in ['復唱', 'ふくしょう', '確認', 'かくにん']):
        return '復唱確認'
    if any(k in name for k in ['電話番号', 'でんわ', '番号']):
        return '電話番号'
    if any(k in name for k in ['健診', 'けんしん', 'コース', 'こーす']):
        return '健診コース'
    if any(k in name for k in ['予約', 'よやく']):
        return '予約'
    if any(k in name for k in ['日時', '日付', '時間', '曜日', '希望日']):
        return '日時'
    if any(k in name for k in ['ワクチン', 'わくちん', '接種']):
        return 'ワクチン'
    if any(k in name for k in ['保険', 'ほけん']):
        return '保険'
    return 'その他'

# Process each module
results = []
for mod in all_modules:
    pw = mod['profile_words']
    # JSON already parsed \n into real newlines
    lines = [l.strip() for l in pw.split('\n') if l.strip()]

    input_type = get_input_type(mod['module_type'])
    purpose = guess_purpose(mod['module_name'], mod['flow_name'])

    words_data = []
    for line in lines:
        parts = line.split(' ', 1)
        if len(parts) == 2:
            hyouki, yomi = parts[0], parts[1]
        else:
            hyouki, yomi = line, line

        found_filler = None
        for fp in filler_patterns:
            if yomi.startswith(fp):
                found_filler = fp
                break

        found_tail = None
        for tp in tail_patterns:
            if yomi.endswith(tp):
                found_tail = tp
                break

        words_data.append({
            'hyouki': hyouki,
            'yomi': yomi,
            'filler': found_filler,
            'tail': found_tail,
        })

    results.append({
        'pair': mod['pair'],
        'flow_name': mod['flow_name'],
        'module_name': mod['module_name'],
        'module_type': mod['module_type'],
        'input_type': input_type,
        'purpose': purpose,
        'line_count': len(lines),
        'words_data': words_data,
        'raw_pw': pw,
    })

# === STATISTICS ===
pr("=" * 80)
pr("1. 1モジュールあたりの登録語数")
pr("=" * 80)
counts = [r['line_count'] for r in results]
pr(f"  総モジュール数: {len(results)}")
pr(f"  平均: {sum(counts)/len(counts):.1f}")
pr(f"  最小: {min(counts)}")
pr(f"  最大: {max(counts)}")
pr(f"  中央値: {sorted(counts)[len(counts)//2]}")

count_dist = Counter(counts)
pr(f"  分布:")
for k in sorted(count_dist.keys()):
    pr(f"    {k}語: {count_dist[k]}モジュール")

pr()
pr("=" * 80)
pr("2. 入力種別ごとの語数")
pr("=" * 80)
by_purpose = defaultdict(list)
for r in results:
    by_purpose[r['purpose']].append(r['line_count'])

for purpose in sorted(by_purpose.keys(), key=lambda x: -len(by_purpose[x])):
    vals = by_purpose[purpose]
    pr(f"  {purpose}: {len(vals)}モジュール, 平均{sum(vals)/len(vals):.1f}語, 範囲{min(vals)}-{max(vals)}")

pr()
pr("=" * 80)
pr("3. フィラーパターンの採用率")
pr("=" * 80)
filler_counter = Counter()
filler_modules = 0
total_words = 0
filler_words = 0
for r in results:
    has_filler = False
    for w in r['words_data']:
        total_words += 1
        if w['filler']:
            filler_counter[w['filler']] += 1
            filler_words += 1
            has_filler = True
    if has_filler:
        filler_modules += 1

pr(f"  フィラーを含むモジュール: {filler_modules}/{len(results)} ({filler_modules/len(results)*100:.1f}%)")
pr(f"  フィラーを含む語: {filler_words}/{total_words} ({filler_words/total_words*100:.1f}%)")
pr(f"  使用されているフィラー種数: {len(filler_counter)}/{len(filler_patterns)}")
pr(f"  各フィラーの使用回数:")
for fp, cnt in filler_counter.most_common():
    pr(f"    {fp}: {cnt}回")

unused = set(filler_patterns) - set(filler_counter.keys())
if unused:
    pr(f"  未使用フィラー: {', '.join(sorted(unused))}")

pr()
pr("=" * 80)
pr("4. 語尾パターンの採用率")
pr("=" * 80)
tail_counter = Counter()
tail_modules = 0
tail_words = 0
for r in results:
    has_tail = False
    for w in r['words_data']:
        if w['tail']:
            tail_counter[w['tail']] += 1
            tail_words += 1
            has_tail = True
    if has_tail:
        tail_modules += 1

pr(f"  語尾パターンを含むモジュール: {tail_modules}/{len(results)} ({tail_modules/len(results)*100:.1f}%)")
pr(f"  語尾パターンを含む語: {tail_words}/{total_words} ({tail_words/total_words*100:.1f}%)")
pr(f"  使用されている語尾種数: {len(tail_counter)}/{len(tail_patterns)}")
pr(f"  各語尾の使用回数:")
for tp, cnt in tail_counter.most_common():
    pr(f"    {tp}: {cnt}回")

unused_tails = set(tail_patterns) - set(tail_counter.keys())
if unused_tails:
    pr(f"  未使用語尾: {', '.join(sorted(unused_tails))}")

pr()
pr("=" * 80)
pr("5. 頭切れパターンの分析")
pr("=" * 80)
# Better approach: check if yomi is a proper suffix of a hiragana reading of hyouki
# But since we don't have a kana converter, use direct comparison
# head truncation = hyouki(reading) starts with chars that yomi doesn't have
# Practical: look for pairs where same hyouki has both full and truncated yomi
head_trunc_count = 0
head_trunc_examples = []
# Group by (pair, module) and hyouki
from itertools import groupby
for r in results:
    hyouki_groups = defaultdict(list)
    for w in r['words_data']:
        hyouki_groups[w['hyouki']].append(w['yomi'])
    for hyouki, yomis in hyouki_groups.items():
        if len(yomis) > 1:
            # Find the longest yomi as "full form"
            longest = max(yomis, key=len)
            for y in yomis:
                if y != longest and longest.endswith(y):
                    head_trunc_count += 1
                    if len(head_trunc_examples) < 40:
                        head_trunc_examples.append(f"表記='{hyouki}' 完全形='{longest}' 頭切れ='{y}' (欠落={longest[:len(longest)-len(y)]})")

pr(f"  頭切れ語数（同一表記内で短縮形が存在）: {head_trunc_count}")
pr(f"  総語数: {total_words}")
pr(f"  頭切れ率: {head_trunc_count/total_words*100:.1f}%")
pr(f"  例:")
for ex in head_trunc_examples[:30]:
    pr(f"    {ex}")

pr()
pr("  --- 頭切れの欠落文字数の分布 ---")
trunc_len_counter = Counter()
for r in results:
    hyouki_groups = defaultdict(list)
    for w in r['words_data']:
        hyouki_groups[w['hyouki']].append(w['yomi'])
    for hyouki, yomis in hyouki_groups.items():
        if len(yomis) > 1:
            longest = max(yomis, key=len)
            for y in yomis:
                if y != longest and longest.endswith(y):
                    removed = len(longest) - len(y)
                    trunc_len_counter[removed] += 1

for k in sorted(trunc_len_counter.keys()):
    pr(f"    {k}文字欠落: {trunc_len_counter[k]}回")

pr()
pr("=" * 80)
pr("6. フィラーx語尾クロス積の使用状況")
pr("=" * 80)
cross_counter = Counter()
for r in results:
    for w in r['words_data']:
        if w['filler'] and w['tail']:
            cross_counter[(w['filler'], w['tail'])] += 1

total_possible = len(filler_patterns) * len(tail_patterns)
actual_combos = len(cross_counter)
pr(f"  理論上の組み合わせ数: {total_possible}")
pr(f"  実際の組み合わせ数: {actual_combos} ({actual_combos/total_possible*100:.1f}%)")
if cross_counter:
    pr(f"  上位の組み合わせ:")
    for (f, t), cnt in cross_counter.most_common(25):
        pr(f"    {f}+{t}: {cnt}回")

pr()
pr("=" * 80)
pr("7. STT vs DTMF の profile_words の違い")
pr("=" * 80)
by_input_type = defaultdict(list)
for r in results:
    by_input_type[r['input_type']].append(r)

for it in sorted(by_input_type.keys()):
    mods = by_input_type[it]
    cnts = [m['line_count'] for m in mods]
    total_w_it = sum(cnts)
    filler_rate = sum(1 for m in mods for w in m['words_data'] if w['filler']) / max(total_w_it, 1)
    pr(f"  {it}: {len(mods)}モジュール, 平均{sum(cnts)/len(cnts):.1f}語, 範囲{min(cnts)}-{max(cnts)}, フィラー率{filler_rate*100:.1f}%")

pr()
pr("=" * 80)
pr("8. pair別の統計")
pr("=" * 80)
by_pair = defaultdict(list)
for r in results:
    by_pair[r['pair']].append(r)

for pair in sorted(by_pair.keys()):
    mods = by_pair[pair]
    cnts = [m['line_count'] for m in mods]
    purposes = set(m['purpose'] for m in mods)
    total_w_p = sum(cnts)
    pr(f"  {pair}: {len(mods)}モジュール, 総語数{total_w_p}, 平均{sum(cnts)/len(cnts):.1f}語, 種別={purposes}")

pr()
pr("=" * 80)
pr("9. 最も充実した profile_words の例 (TOP 3)")
pr("=" * 80)
sorted_by_count = sorted(results, key=lambda r: r['line_count'], reverse=True)
for i, most in enumerate(sorted_by_count[:3]):
    pr(f"\n  --- #{i+1}: {most['pair']}/{most['module_name']} ({most['purpose']}, {most['input_type']}) ---")
    pr(f"  語数: {most['line_count']}")
    lines = most['raw_pw'].split('\n')[:50]
    for l in lines:
        pr(f"    {l}")
    if most['line_count'] > 50:
        pr(f"    ... (残り {most['line_count']-50} 行)")

pr()
pr("=" * 80)
pr("10. 最も簡素な profile_words の例 (BOTTOM 3)")
pr("=" * 80)
for i, least in enumerate(sorted_by_count[-3:]):
    pr(f"\n  --- #{len(sorted_by_count)-2+i}: {least['pair']}/{least['module_name']} ({least['purpose']}, {least['input_type']}) ---")
    pr(f"  語数: {least['line_count']}")
    lines = least['raw_pw'].split('\n')
    for l in lines:
        pr(f"    {l}")

pr()
pr("=" * 80)
pr("11. profile_words の構造パターン分析")
pr("=" * 80)

same_count = 0
diff_count = 0
for r in results:
    for w in r['words_data']:
        if w['hyouki'] == w['yomi']:
            same_count += 1
        else:
            diff_count += 1
pr(f"  表記=よみ (同一): {same_count}/{total_words} ({same_count/total_words*100:.1f}%)")
pr(f"  表記!=よみ (変換あり): {diff_count}/{total_words} ({diff_count/total_words*100:.1f}%)")

pr()
pr("  --- 復唱確認モジュールの profile_words パターン ---")
confirm_count = 0
for r in results:
    if r['purpose'] == '復唱確認':
        confirm_count += 1
        if confirm_count <= 5:  # Show first 5 examples
            pr(f"    {r['pair']}/{r['module_name']}: {r['line_count']}語")
            lines = r['raw_pw'].split('\n')[:15]
            for l in lines:
                pr(f"      {l}")
            if r['line_count'] > 15:
                pr(f"      ... (+{r['line_count']-15})")
            pr()
pr(f"  復唱確認モジュール合計: {confirm_count}")

pr()
pr("  --- 用件分類モジュールの profile_words パターン ---")
youken_count = 0
for r in results:
    if r['purpose'] == '用件分類':
        youken_count += 1
        pr(f"    {r['pair']}/{r['module_name']}: {r['line_count']}語")
        lines = r['raw_pw'].split('\n')[:20]
        for l in lines:
            pr(f"      {l}")
        if r['line_count'] > 20:
            pr(f"      ... (+{r['line_count']-20})")
        pr()
pr(f"  用件分類モジュール合計: {youken_count}")

pr()
pr("  --- 診療科モジュールの profile_words パターン ---")
shinryo_count = 0
for r in results:
    if r['purpose'] == '診療科':
        shinryo_count += 1
        pr(f"    {r['pair']}/{r['module_name']}: {r['line_count']}語")
        lines = r['raw_pw'].split('\n')[:25]
        for l in lines:
            pr(f"      {l}")
        if r['line_count'] > 25:
            pr(f"      ... (+{r['line_count']-25})")
        pr()
pr(f"  診療科モジュール合計: {shinryo_count}")

# 12. Per-purpose filler/tail analysis
pr()
pr("=" * 80)
pr("12. 入力種別ごとのフィラー・語尾使用率")
pr("=" * 80)
for purpose in sorted(by_purpose.keys(), key=lambda x: -len(by_purpose[x])):
    purpose_results = [r for r in results if r['purpose'] == purpose]
    total_w_pur = sum(r['line_count'] for r in purpose_results)
    filler_w = sum(1 for r in purpose_results for w in r['words_data'] if w['filler'])
    tail_w = sum(1 for r in purpose_results for w in r['words_data'] if w['tail'])
    pr(f"  {purpose}: 総語数{total_w_pur}, フィラー{filler_w}({filler_w/max(total_w_pur,1)*100:.0f}%), 語尾{tail_w}({tail_w/max(total_w_pur,1)*100:.0f}%)")

# 13. Full module type listing
pr()
pr("=" * 80)
pr("13. モジュールtype一覧")
pr("=" * 80)
type_counter = Counter()
for r in results:
    type_counter[r['module_type']] += 1
for t, c in type_counter.most_common():
    pr(f"  {t}: {c}")

# 14. Detailed filler pattern by module (showing how many fillers per keyword)
pr()
pr("=" * 80)
pr("14. キーワードあたりのフィラー展開数の分析")
pr("=" * 80)
# For modules with >10 words, count unique hyouki and see how many yomi per hyouki
for r in sorted_by_count[:10]:
    if r['line_count'] >= 10:
        hyouki_groups = defaultdict(list)
        for w in r['words_data']:
            hyouki_groups[w['hyouki']].append(w['yomi'])
        multi = [(h, yomis) for h, yomis in hyouki_groups.items() if len(yomis) > 1]
        if multi:
            pr(f"\n  {r['pair']}/{r['module_name']} ({r['purpose']}): {r['line_count']}語, {len(hyouki_groups)}キーワード")
            for h, yomis in sorted(multi, key=lambda x: -len(x[1]))[:5]:
                pr(f"    '{h}': {len(yomis)}バリエーション")
                for y in yomis[:8]:
                    pr(f"      - {y}")
                if len(yomis) > 8:
                    pr(f"      ... (+{len(yomis)-8})")

# Write output
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

print(f"Analysis complete. Output written to {OUTPUT_FILE}")
print(f"Total modules analyzed: {len(results)}, Total words: {total_words}")
