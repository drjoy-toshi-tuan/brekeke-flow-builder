# -*- coding: utf-8 -*-
"""extract-yesno-synonyms — Brekeke ログから yes/no 意図発話を抽出し、
エンティティ類義語辞書アップロード用 CSV を生成する skill 本体。

Usage:
    python process.py <YYYYMM>
    python process.py <YYYYMM> --raw-dir <path> --out-dir <path>

Defaults:
    --raw-dir = C:/Users/hamaguchi.t/yes_no_analysis_<YYYYMM>/raw
    --out-dir = C:/Users/hamaguchi.t/yes_no_analysis_<YYYYMM>

入力: <raw-dir>/<YYYYMMDD>.csv 群 (Brekeke 日次ログ、UTF-8、ヘッダー無し)
出力: <out-dir>/ 配下に 9 ファイル (バケット 6 種 + raw + summary + 辞書 CSV)

詳細: SKILL.md 参照。
"""

import argparse
import csv
import glob
import io
import os
import re
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------------------
# Regex / Label / Keyword definitions
# ---------------------------------------------------------------------------

SD_PAT = re.compile(r'save-([^:;]+):([^;]*)')
# 2026-07-17: 実ログでは openAI_/script_ (小文字) が主流（OpenAI_/Script_ は少数）。
# 両方拾うため大小文字を区別しない。
OA_PAT = re.compile(r'openAI_([^:;]+):([^;]*)', re.IGNORECASE)
SC_PAT = re.compile(r'script_([^:;]+):([^;]*)', re.IGNORECASE)

# 2026-07-17: 肯定/否定 は intent_classifier_v2 / yes_no_classifier / n_choice 等
# 決定論部品群の標準 yes/no ラベル語彙。実ログの yes/no 判定結果の大半を占めるため必須。
YES_LABELS = {'あり', '該当', 'はい', '肯定', 'yes', 'true', 'Yes', 'YES', 'TRUE', 'True'}
NO_LABELS  = {'なし', '非該当', 'いいえ', '否定', 'no', 'false', 'No', 'NO', 'FALSE', 'False'}

YES_KEYWORDS = ['はい', 'うん', 'ええ', 'そう', 'あります', 'お願い', '希望',
                'する', 'します', 'いい', '良い',
                # 2026-05-22 拡張: unclear 救済用
                '当てはまります', '当てはまる', '対象です', 'ございます',
                'なります', '受けて', '通って', '入って', '了解',
                '分かりました', '分かった', '承知', 'OK', 'ok', 'Ok',
                '大丈夫です', '出ます', '行きます', '伺います', 'もちろん']
NO_KEYWORDS  = ['いいえ', 'いえ', '違', '結構', 'ありません', 'いりません',
                'やめ', '不要', '無し', 'なし',
                # 2026-05-22 拡張: unclear 救済用
                '当てはまりません', '当てはまらない', '対象では', '対象外',
                '駄目', 'ダメ', 'キャンセル', '断り', '断っ', '止め',
                '分かりません', '分からない', 'できません', 'できない',
                'いません', '出ません', '行きません']

STATUS_MARKERS = {'OK', 'NG', 'true', 'false', 'True', 'False', ''}

# Dictionary upload CSV: entity name -> list of bucket names to merge synonyms from.
# 1 行 1 エンティティ。各エンティティの類義語は複数 bucket を merge した完全一致 unique 集合。
# 2026-07-17: yes_no_result/no_no_result はキーワード推測救済の廃止に伴い常に空になったため除外。
DICT_ENTITIES = [
    ('はい',   ['yes_confirmed', 'yes_openai_only']),
    ('いいえ', ['no_confirmed', 'no_openai_only']),
]


# ---------------------------------------------------------------------------
# Text matchers
# ---------------------------------------------------------------------------

def text_has_yes(text):
    """`いい` が `いいえ` 含む発話で誤発火しないよう先に `いいえ`/`いえ` を除去してから判定."""
    stripped = text
    for nk in ('いいえ', 'いえ'):
        stripped = stripped.replace(nk, '')
    for k in YES_KEYWORDS:
        if k == 'いい':
            if 'いい' in stripped:
                return True
        else:
            if k in text:
                return True
    return False


def text_has_no(text):
    return any(k in text for k in NO_KEYWORDS)


def classify_label(lbl):
    if not lbl:
        return 'other'
    if lbl in YES_LABELS:
        return 'yes'
    if lbl in NO_LABELS:
        return 'no'
    return 'other'


# ---------------------------------------------------------------------------
# Trace parser
# ---------------------------------------------------------------------------

def parse_trace(trace):
    """`;` 区切りトレース文字列から (kind, key, value, pos) を出現順に返す."""
    tokens = []
    for m in SD_PAT.finditer(trace):
        tokens.append(('SD', m.group(1), m.group(2).strip(), m.start()))
    for m in OA_PAT.finditer(trace):
        tokens.append(('OA', m.group(1), m.group(2).strip(), m.start()))
    for m in SC_PAT.finditer(trace):
        tokens.append(('SC', m.group(1), m.group(2).strip(), m.start()))
    tokens.sort(key=lambda x: x[3])
    return tokens


def pair_utterances(tokens):
    """各 SD (real utterance) に対し、次の SD の手前までに現れる最初の OA / SC を紐付ける."""
    pairs = []
    n = len(tokens)
    for i, (kind, key, val, _) in enumerate(tokens):
        if kind != 'SD' or val in STATUS_MARKERS:
            continue
        oa_label = oa_key = sc_label = sc_key = ''
        for j in range(i + 1, n):
            k2, key2, val2, _ = tokens[j]
            if k2 == 'SD':
                break
            if k2 == 'OA' and not oa_label:
                oa_label, oa_key = val2, key2
            if k2 == 'SC' and not sc_label:
                sc_label, sc_key = val2, key2
        pairs.append({
            'sd_num': key,
            'utterance': val,
            'openai_key': oa_key,
            'openai_label': oa_label,
            'script_key': sc_key,
            'script_label': sc_label,
        })
    return pairs


def classify_pair(p):
    """2026-07-17: 実ログは script_ 判定が主流(openAI_ は少数)なので script_label を優先し
    無ければ openai_label にフォールバック。かつ NO_RESULT/other をキーワードで
    "救済"するのは廃止(field種別を問わずキーワード一致するだけで拾ってしまい、
    部署名/日付/電話種別等の非yes-no fieldが辞書に混入するリスクの方が大きいため)。
    label自体が明確にyes/no語彙(YES_LABELS/NO_LABELS。肯定/否定含む)の場合のみ確定扱いする。"""
    text = p['utterance']
    lbl = p['script_label'] or p['openai_label']
    cls = classify_label(lbl)
    has_yes = text_has_yes(text)
    has_no = text_has_no(text)

    if cls == 'other':
        return 'unclear'
    if cls == 'yes':
        if has_yes and not has_no: return 'yes_confirmed'
        if has_no: return 'disagree'
        return 'yes_openai_only'
    if cls == 'no':
        if has_no and not has_yes: return 'no_confirmed'
        if has_yes: return 'disagree'
        return 'no_openai_only'
    return 'unclear'


def scenario_short(scenario):
    s = scenario
    for sep in ('$', '^'):
        if sep in s:
            s = s.rsplit(sep, 1)[-1]
    return s


# ---------------------------------------------------------------------------
# Per-file processor
# ---------------------------------------------------------------------------

def process_file(path, date_str):
    with open(path, 'rb') as f:
        raw = f.read().decode('utf-8', errors='replace')
    reader = csv.reader(io.StringIO(raw))
    for row in reader:
        if len(row) < 8:
            continue
        call_id = row[0]
        scenario = row[4] if len(row) > 4 else ''
        trace = ','.join(row[7:])  # 列数が変動するので 7 列目以降は結合
        tokens = parse_trace(trace)
        for p in pair_utterances(tokens):
            p['date'] = date_str
            p['call_id'] = call_id
            p['scenario'] = scenario_short(scenario)
            yield p


# ---------------------------------------------------------------------------
# Aggregation + writers
# ---------------------------------------------------------------------------

def aggregate(bucket_pairs, with_text_match=False):
    agg = defaultdict(lambda: {
        'count': 0, 'scenarios': Counter(),
        'openai_labels': Counter(), 'script_labels': Counter(),
        'yes_kw': False, 'no_kw': False,
    })
    for p in bucket_pairs:
        a = agg[p['utterance']]
        a['count'] += 1
        if p['scenario']:     a['scenarios'][p['scenario']] += 1
        if p['openai_label']: a['openai_labels'][p['openai_label']] += 1
        if p['script_label']: a['script_labels'][p['script_label']] += 1
        if with_text_match:
            if text_has_yes(p['utterance']): a['yes_kw'] = True
            if text_has_no(p['utterance']):  a['no_kw']  = True
    rows = []
    for utt, a in agg.items():
        scen = '|'.join(f"{s}({c})" for s, c in a['scenarios'].most_common(5))
        oal  = '|'.join(f"{l}({c})" for l, c in a['openai_labels'].most_common(5))
        scl  = '|'.join(f"{l}({c})" for l, c in a['script_labels'].most_common(5))
        row = [utt, a['count'], scen, oal, scl]
        if with_text_match:
            row.extend(['Y' if a['yes_kw'] else '', 'Y' if a['no_kw'] else ''])
        rows.append(row)
    rows.sort(key=lambda r: -r[1])
    return rows


def write_bucket(out_dir, name, rows, headers):
    p = os.path.join(out_dir, f'{name}.csv')
    with open(p, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for r in rows:
            w.writerow(r)
    return p


def build_dict_csv(out_dirs, dict_out_dir=None):
    """1 個以上の bucket 出力ディレクトリを merge して辞書アップロード CSV を生成.

    仕様 (2026-05-22 検証済 / 2026-05-22 拡張):
    - 2 列 (`エンティティ名`, `類義語`)
    - 1 行 1 エンティティ
    - 類義語は `/` 区切りで packing
    - 全 field 二重引用符
    - **完全一致 unique** (句読点・空白・記号バリエーションは別物として保持)
    - エンティティごとに `DICT_ENTITIES` で指定された複数 bucket (confirmed +
      openai_only + no_result) を merge
    - `out_dirs` が複数指定された場合は全月の bucket csv を utterance キーで accumulate

    Args:
        out_dirs: bucket csv ディレクトリ (str) or list[str]。複数月 accumulate 時はリスト。
        dict_out_dir: 出力 CSV 配置ディレクトリ。省略時は out_dirs の先頭。
    """
    if isinstance(out_dirs, str):
        out_dirs = [out_dirs]
    if dict_out_dir is None:
        dict_out_dir = out_dirs[0]

    def collect_merged(bucket_names):
        merged = {}
        for d in out_dirs:
            for bn in bucket_names:
                bucket_csv = os.path.join(d, f'{bn}.csv')
                if not os.path.exists(bucket_csv):
                    continue
                with open(bucket_csv, 'r', encoding='utf-8-sig') as f:
                    for r in csv.DictReader(f):
                        utt = r['utterance']
                        if not utt:
                            continue
                        cnt = int(r['count'])
                        merged[utt] = merged.get(utt, 0) + cnt
        return sorted(merged.items(), key=lambda x: (-x[1], x[0]))

    out_path = os.path.join(dict_out_dir, 'entity_synonyms_final_slash.csv')
    counts = {}
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, quoting=csv.QUOTE_ALL)
        w.writerow(['エンティティ名', '類義語'])
        for entity_name, bucket_names in DICT_ENTITIES:
            syns = [k for k, _ in collect_merged(bucket_names)]
            counts[entity_name] = len(syns)
            w.writerow([entity_name, '/'.join(syns)])
    return out_path, counts


def build_summary(out_dir, files, file_stats, all_pairs, buckets, written, dict_csv):
    sm = []
    sm.append(f'# Yes/No 抽出サマリー\n')
    sm.append(f'処理ファイル: {len(files)} / 抽出ペア合計: {len(all_pairs)}\n')

    sm.append('\n## ファイル毎ペア数\n')
    for ds, cnt, st in file_stats:
        sm.append(f'- {ds}: {cnt} ({st})')

    sm.append('\n## バケット内訳\n')
    sm.append('| バケット | ペア数 | ユニーク発話数 |')
    sm.append('|---|---:|---:|')
    for bname in ['yes_confirmed', 'no_confirmed', 'yes_openai_only',
                  'no_openai_only', 'yes_no_result', 'no_no_result',
                  'disagree', 'unclear']:
        _, cnt, uniq = written[bname]
        sm.append(f'| {bname} | {cnt} | {uniq} |')

    for bname in ['yes_confirmed', 'no_confirmed', 'yes_openai_only',
                  'no_openai_only', 'yes_no_result', 'no_no_result',
                  'disagree', 'unclear']:
        sm.append(f'\n## 上位 20 発話: {bname}\n')
        with open(written[bname][0], 'r', encoding='utf-8-sig', newline='') as f:
            r = csv.reader(f)
            next(r)
            top = [row for i, row in enumerate(r) if i < 20]
        if not top:
            sm.append('(該当なし)')
            continue
        sm.append('| # | count | utterance | openai_labels |')
        sm.append('|---:|---:|---|---|')
        for i, row in enumerate(top, 1):
            utt = row[0].replace('|', '\\|')
            oal = row[3].replace('|', '\\|')
            sm.append(f'| {i} | {row[1]} | {utt} | {oal} |')

    sm.append('\n## 観測事項\n')
    disagree_oa = Counter()
    for p in buckets['disagree']:
        kws = '|'.join(sorted(set(
            [k for k in YES_KEYWORDS if k in p['utterance']] +
            [k for k in NO_KEYWORDS if k in p['utterance']])))
        disagree_oa[(p['openai_label'], kws)] += 1
    sm.append('disagree (OpenAIラベル, 検出キーワード) 上位:')
    for (oa, kws), c in disagree_oa.most_common(10):
        sm.append(f'- openai={oa} / kw={kws}: {c}')

    sm.append('\n## 辞書アップロード用 CSV\n')
    sm.append(f'`{dict_csv}` を そのまま エンティティ管理画面にアップロード可能。')
    sm.append('既存エンティティと同名の場合は上書きされる。')

    smp = os.path.join(out_dir, 'summary.md')
    with open(smp, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sm))
    return smp


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_accumulate(out_dirs, dict_out_dir):
    """複数の bucket 出力ディレクトリを merge して累積 dict csv を生成."""
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    os.makedirs(dict_out_dir, exist_ok=True)
    dict_csv, dict_counts = build_dict_csv(out_dirs, dict_out_dir=dict_out_dir)
    print('=== Accumulated from ===')
    for d in out_dirs:
        print(f'  {d}')
    print(f'=== Dict upload -> {dict_csv} ===')
    for name, n in dict_counts.items():
        marker = ' ✅ >=500' if n >= 500 else ''
        print(f'  {name}: {n}{marker}')
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n', 1)[0])
    p.add_argument('yyyymm', nargs='?',
                   help='対象月 (YYYYMM 例: 202604)。--accumulate 時は省略可')
    p.add_argument('--raw-dir', help='Brekeke 日次 CSV 配置ディレクトリ', default=None)
    p.add_argument('--out-dir', help='出力先', default=None)
    p.add_argument('--accumulate', nargs='+', metavar='OUT_DIR',
                   help='複数の yes_no_analysis_<YYYYMM>/ を merge して累積 dict csv のみ生成')
    p.add_argument('--accumulate-out', metavar='DIR',
                   help='累積 dict csv の配置先 (省略時は --accumulate の先頭)')
    args = p.parse_args(argv)

    if args.accumulate:
        dict_out = args.accumulate_out or args.accumulate[0]
        return run_accumulate(args.accumulate, dict_out)

    if not args.yyyymm:
        p.error('yyyymm is required when --accumulate is not used')

    yyyymm = args.yyyymm.replace('-', '')
    default_out = rf'C:\Users\hamaguchi.t\yes_no_analysis_{yyyymm}'
    out_dir = args.out_dir or default_out
    raw_dir = args.raw_dir or os.path.join(out_dir, 'raw')
    os.makedirs(out_dir, exist_ok=True)

    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

    files = sorted(glob.glob(os.path.join(raw_dir, '*.csv')))
    if not files:
        print(f'no input CSVs in {raw_dir}', file=sys.stderr)
        return 1
    print(f'input dir: {raw_dir} ({len(files)} files)')

    all_pairs = []
    file_stats = []
    for fp in files:
        date_str = os.path.basename(fp).replace('.csv', '')
        try:
            pairs = list(process_file(fp, date_str))
            all_pairs.extend(pairs)
            file_stats.append((date_str, len(pairs), 'ok'))
            print(f'{date_str}: {len(pairs)} pairs')
        except Exception as e:
            file_stats.append((date_str, 0, f'fail: {e}'))
            print(f'{date_str}: FAIL {e}')

    print(f'\ntotal pairs: {len(all_pairs)}')

    buckets = defaultdict(list)
    for p in all_pairs:
        bn = classify_pair(p)
        p['bucket'] = bn
        buckets[bn].append(p)

    raw_csv = os.path.join(out_dir, 'all_pairs_raw.csv')
    with open(raw_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['date', 'call_id', 'scenario', 'question_name',
                    'utterance', 'openai_label', 'script_label', 'bucket'])
        for p in all_pairs:
            w.writerow([p['date'], p['call_id'], p['scenario'],
                        p['openai_key'] or p['script_key'],
                        p['utterance'], p['openai_label'],
                        p['script_label'], p['bucket']])

    base_h = ['utterance', 'count', 'scenarios', 'openai_labels', 'script_labels']
    ext_h  = base_h + ['text_yes_match', 'text_no_match']

    written = {}
    for bn in ['yes_confirmed', 'no_confirmed', 'yes_openai_only',
               'no_openai_only', 'yes_no_result', 'no_no_result']:
        rows = aggregate(buckets[bn], with_text_match=False)
        written[bn] = (write_bucket(out_dir, bn, rows, base_h), len(buckets[bn]), len(rows))
    for bn in ['disagree', 'unclear']:
        rows = aggregate(buckets[bn], with_text_match=True)
        written[bn] = (write_bucket(out_dir, bn, rows, ext_h), len(buckets[bn]), len(rows))

    dict_csv, dict_counts = build_dict_csv(out_dir)
    smp = build_summary(out_dir, files, file_stats, all_pairs, buckets, written, dict_csv)

    print('\n=== Bucket counts ===')
    for bn in ['yes_confirmed', 'no_confirmed', 'yes_openai_only',
               'no_openai_only', 'yes_no_result', 'no_no_result',
               'disagree', 'unclear']:
        path, cnt, uniq = written[bn]
        print(f'{bn}: pairs={cnt} unique={uniq} -> {path}')
    print(f'raw -> {raw_csv}')
    print(f'summary -> {smp}')
    print(f'dict upload -> {dict_csv}')
    print('=== Dict entity synonym counts ===')
    for name, n in dict_counts.items():
        print(f'  {name}: {n}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
