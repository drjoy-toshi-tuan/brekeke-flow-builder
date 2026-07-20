#!/usr/bin/env python3
"""
AmiVoice 単語登録 CSV 生成ツール（ノード別出力モード）

ソース:
  1. docs/amivoice/base_keywords.yaml  — マスターキーワード定義（target_nodes フィールドで配布先を指定）
  2. 設計書 YAML の script_blocks       — 施設固有キーワード（youken/faq/department）
  3. docs/amivoice/misrecognition_log.csv — 実ログ由来の誤認識補正（任意）

出力:
  ノード名ごとに 1 CSV ファイル
    output/scenarios/{施設}_{flow}/amivoice/{ノード名}.csv

使い方:
  # 基本（マスター + 設計書から生成）
  python tools/gen_amivoice_dict.py \
      --base docs/amivoice/base_keywords.yaml \
      --yaml output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml \
      --facility 東京都立豊島病院 \
      --flow 診療 \
      --out-dir output/scenarios/東京都立豊島病院_診療/amivoice

  # 実ログ追加
  python tools/gen_amivoice_dict.py \
      --base docs/amivoice/base_keywords.yaml \
      --yaml output/scenarios/東京都立豊島病院_診療/設計書_東京都立豊島病院_診療.yaml \
      --log  docs/amivoice/misrecognition_log.csv \
      --facility 東京都立豊島病院 \
      --flow 診療 \
      --out-dir output/scenarios/東京都立豊島病院_診療/amivoice \
      --openai-alias
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML が必要です。requirements.txt を確認してください。", file=sys.stderr)
    sys.exit(1)


# ---- データ構造 ----

class Entry:
    def __init__(self, word, reading="", category="", priority="medium",
                 source="", note="", target_nodes=None):
        self.word         = word.strip()
        self.reading      = reading.strip()
        self.category     = category
        self.priority     = priority
        self.source       = source
        self.note         = note
        self.target_nodes = target_nodes or []

    def key(self):
        return (self.word, self.reading)


# ---- ソース1: base_keywords.yaml ----

def load_base(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    for category, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            if not isinstance(item, dict) or not item.get("word"):
                continue
            entries.append(Entry(
                word         = item.get("word", ""),
                reading      = item.get("reading", ""),
                category     = category,
                priority     = item.get("priority", "medium"),
                source       = "base_keywords.yaml",
                note         = item.get("note", ""),
                target_nodes = item.get("target_nodes", []),
            ))
    return entries


# ---- ソース1b: keyword_master.json + keyword_custom.json ----
# keyword_master.json: tools/ 配下の共通マスター（label/synonyms/misrecognition/target_nodes）
# keyword_custom.json: output/scenarios/{施設}_{flow}/ 配下の施設固有上書き（同スキーマ）
# マージ規則: custom の label が master と同じ → custom が優先（上書き）。新規 label → 追加。

def _keyword_items_to_entries(items, source):
    entries = []
    for item in items:
        label = (item.get("label") or "").strip()
        if not label:
            continue
        nodes = item.get("target_nodes", [])
        base_kwargs = dict(
            category=item.get("category", "keyword"),
            priority=item.get("priority", "medium"),
            source=source,
            target_nodes=nodes,
        )
        entries.append(Entry(word=label, reading=item.get("reading", ""),
                             note=item.get("note", ""), **base_kwargs))
        for syn in item.get("synonyms", []):
            entries.append(Entry(word=syn, note=f"synonym → {label}", **base_kwargs))
        for wrong in item.get("misrecognition", []):
            entries.append(Entry(word=label,
                                 note=f"誤認識補正: {wrong} → {label}", **base_kwargs))
    return entries


def load_keyword_master(master_path, custom_path=""):
    """keyword_master.json（＋任意で keyword_custom.json）を読み、マージ済み Entry リストを返す。"""
    def _load_items(path):
        if not path or not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("keywords", [])

    master_items = _load_items(master_path)
    custom_items = _load_items(custom_path)

    # label でマージ: custom が master を上書き
    custom_labels = {c.get("label") for c in custom_items if c.get("label")}
    master_only = [i for i in master_items
                   if i.get("label") and i["label"] not in custom_labels]

    entries = _keyword_items_to_entries(master_only, "keyword_master.json")
    entries += _keyword_items_to_entries(custom_items, "keyword_custom.json")
    return entries


# ---- ソース2: 設計書 YAML の script_blocks ----

def load_from_yaml(path):
    entries = []
    if not path or not os.path.exists(path):
        return entries

    with open(path, encoding="utf-8") as f:
        design = yaml.safe_load(f)

    script_blocks = design.get("script_blocks", [])
    for block in script_blocks:
        block_type  = block.get("type", "")
        input_mod   = block.get("input_module", "")
        target_node = [input_mod] if input_mod else []

        # 用件キーワード
        if block_type == "youken":
            for opt in block.get("options", []):
                for kw in opt.get("keywords", []):
                    entries.append(Entry(
                        word         = kw,
                        reading      = "",
                        category     = "youken",
                        priority     = "high",
                        source       = "script_blocks/youken",
                        note         = f"label={opt.get('label', '')}",
                        target_nodes = target_node,
                    ))

        # FAQ キーワード（faqMap のキー）
        elif block_type == "faq":
            faq_input = block.get("faq_input_module", input_mod)
            for entry in block.get("faq_map", []):
                q = entry.get("q", "")
                if q:
                    entries.append(Entry(
                        word         = q,
                        reading      = "",
                        category     = "faq",
                        priority     = "high",
                        source       = f"script_blocks/faq/{block.get('module_name', '')}",
                        note         = "",
                        target_nodes = [faq_input] if faq_input else [],
                    ))

        # 診療科名
        elif block_type == "department":
            for dept in block.get("departments", []):
                entries.append(Entry(
                    word         = dept,
                    reading      = "",
                    category     = "department",
                    priority     = "high",
                    source       = "script_blocks/department",
                    note         = "",
                    target_nodes = target_node,
                ))

    return entries


# ---- ソース3: misrecognition_log.csv ----
# CSV 形式: wrong,correct,count,note,target_nodes
# target_nodes は省略可（省略時は全ノードに配布）
# 例: お薬,予約,12,AmiVoice音響混同,入力_用件

def load_log(path):
    entries = []
    if not path or not os.path.exists(path):
        return entries

    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wrong   = row.get("wrong", "").strip()
            correct = row.get("correct", "").strip()
            count   = row.get("count", "0").strip()
            note    = row.get("note", "").strip()
            nodes_raw = row.get("target_nodes", "").strip()
            target_nodes = [n.strip() for n in nodes_raw.split("|") if n.strip()] if nodes_raw else []

            if wrong and correct:
                entries.append(Entry(
                    word         = correct,
                    reading      = "",
                    category     = "log_derived",
                    priority     = "high" if int(count or 0) >= 5 else "medium",
                    source       = "misrecognition_log.csv",
                    note         = f"誤認識: {wrong} → {correct}（{count}件）{' ' + note if note else ''}",
                    target_nodes = target_nodes,
                ))
    return entries


# ---- OpenAI フォネティックエイリアス生成（任意） ----

def gen_openai_aliases(entries, facility):
    try:
        import urllib.request
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("WARN: OPENAI_API_KEY が未設定のため alias 生成をスキップします。", file=sys.stderr)
            return []

        targets = [e for e in entries if e.priority == "high" and e.category in ("youken", "department")]
        if not targets:
            return []

        word_list = "\n".join(f"- {e.word}（{e.category}）" for e in targets[:30])
        prompt = (
            f"施設名: {facility}\n"
            "以下の単語リストについて、AmiVoice STT が音響的に混同しやすい誤認識パターンを各単語につき1〜3個列挙してください。\n"
            "出力形式: JSON配列 [{\"word\": \"予約\", \"aliases\": [\"お薬\", \"規約\", \"ようやく\"]}]\n"
            "単語リスト:\n" + word_list
        )

        payload = json.dumps({
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        text = result["choices"][0]["message"]["content"]
        start = text.find("[")
        end   = text.rfind("]") + 1
        alias_data = json.loads(text[start:end])

        alias_entries = []
        for item in alias_data:
            word    = item.get("word", "")
            aliases = item.get("aliases", [])
            # 元エントリの target_nodes を引き継ぐ
            original = next((e for e in entries if e.word == word), None)
            orig_nodes = original.target_nodes if original else []
            for alias in aliases:
                alias_entries.append(Entry(
                    word         = word,
                    reading      = alias,
                    category     = "alias",
                    priority     = "medium",
                    source       = "openai_alias",
                    note         = f"音響混同エイリアス: {alias} → {word}",
                    target_nodes = orig_nodes,
                ))
        print(f"  OpenAI alias: {len(alias_entries)} エントリ生成", file=sys.stderr)
        return alias_entries

    except Exception as e:
        print(f"WARN: OpenAI alias 生成失敗: {e}", file=sys.stderr)
        return []


# ---- ノード別グルーピング ----

def group_by_node(all_entries):
    """
    target_nodes リストに基づいてエントリをノード別に分類する。
    target_nodes が空のエントリは _global バケツに入れる（全ノードに配布しない）。
    """
    node_map = defaultdict(list)
    for e in all_entries:
        if e.target_nodes:
            for node in e.target_nodes:
                node_map[node].append(e)
        else:
            node_map["_global"].append(e)
    return node_map


# ---- 重複排除・マージ（ノード内） ----

def merge(entries):
    seen = {}
    for e in entries:
        k = e.key()
        if k not in seen:
            seen[k] = e
        else:
            existing = seen[k]
            rank = {"high": 2, "medium": 1, "low": 0}
            if rank.get(e.priority, 0) > rank.get(existing.priority, 0):
                seen[k] = e
    return list(seen.values())


# ---- CSV 出力（ノード単位） ----

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
CATEGORY_ORDER = {"youken": 0, "faq": 1, "department": 2, "date": 3, "date_hope": 3,
                  "number": 4, "history": 4, "system": 5, "log_derived": 6, "alias": 7}


def write_node_csv(entries, out_path):
    entries_sorted = sorted(
        entries,
        key=lambda e: (
            CATEGORY_ORDER.get(e.category, 9),
            PRIORITY_ORDER.get(e.priority, 9),
            e.word,
        )
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "reading", "category", "priority", "source", "note"])
        for e in entries_sorted:
            writer.writerow([e.word, e.reading, e.category, e.priority, e.source, e.note])

    return len(entries_sorted)


# ---- メイン ----

def main():
    parser = argparse.ArgumentParser(description="AmiVoice 単語登録 CSV 生成（ノード別）")
    parser.add_argument("--base",         required=True,  help="base_keywords.yaml パス")
    parser.add_argument("--yaml",         default="",     help="設計書 YAML パス（script_blocks を読む）")
    parser.add_argument("--log",          default="",     help="misrecognition_log.csv パス（任意）")
    parser.add_argument("--keyword-master", default="",   help="keyword_master.json パス（任意。tools/keyword_master.json）")
    parser.add_argument("--keyword-custom", default="",   help="keyword_custom.json パス（任意。施設固有上書き。--keyword-master 必須）")
    parser.add_argument("--facility",     required=True,  help="施設名（ログ・サマリー用）")
    parser.add_argument("--flow",         default="",     help="フロー名（出力ディレクトリ名に使用）")
    parser.add_argument("--out-dir",      required=True,  help="出力ディレクトリ（{ノード名}.csv を書き出す）")
    parser.add_argument("--openai-alias", action="store_true", help="OpenAI でフォネティックエイリアスを生成")
    args = parser.parse_args()

    if not os.path.exists(args.base):
        print(f"ERROR: base_keywords.yaml が見つかりません: {args.base}", file=sys.stderr)
        sys.exit(1)

    all_entries = []

    # ソース1: base
    base = load_base(args.base)
    print(f"base_keywords.yaml: {len(base)} エントリ", file=sys.stderr)
    all_entries.extend(base)

    # ソース2: 設計書 YAML
    if args.yaml:
        from_yaml = load_from_yaml(args.yaml)
        print(f"script_blocks:       {len(from_yaml)} エントリ", file=sys.stderr)
        all_entries.extend(from_yaml)

    # ソース1b: keyword_master + keyword_custom
    if args.keyword_master:
        km = load_keyword_master(args.keyword_master, args.keyword_custom)
        print(f"keyword_master/custom: {len(km)} エントリ", file=sys.stderr)
        all_entries.extend(km)

    # ソース3: 実ログ
    if args.log:
        from_log = load_log(args.log)
        print(f"misrecognition_log:  {len(from_log)} エントリ", file=sys.stderr)
        all_entries.extend(from_log)

    # OpenAI alias（任意）
    if args.openai_alias:
        aliases = gen_openai_aliases(all_entries, args.facility)
        all_entries.extend(aliases)

    # ノード別グルーピング
    node_map = group_by_node(all_entries)

    # 各ノードの CSV を出力
    total_files = 0
    total_entries = 0
    for node_name, entries in sorted(node_map.items()):
        if node_name == "_global":
            print(f"  [SKIP] target_nodes 未設定エントリ {len(entries)} 件（_global バケツ）", file=sys.stderr)
            continue

        merged = merge(entries)
        # ファイル名に使えない文字を置換
        safe_name = node_name.replace("/", "_").replace("\\", "_")
        out_path = os.path.join(args.out_dir, f"{safe_name}.csv")
        count = write_node_csv(merged, out_path)
        print(f"  [{node_name}] {out_path}  ({count} エントリ)", file=sys.stderr)
        total_files += 1
        total_entries += count

    print(
        f"\n完了: {total_files} ノード / 合計 {total_entries} エントリ  "
        f"→ {args.out_dir}/",
        file=sys.stderr,
    )

    # サマリー（全エントリ合算）
    from collections import Counter
    cat_cnt = Counter(e.category for e in all_entries if e.target_nodes)
    print(f"  カテゴリ別（配布対象）: {dict(cat_cnt)}", file=sys.stderr)


if __name__ == "__main__":
    main()
