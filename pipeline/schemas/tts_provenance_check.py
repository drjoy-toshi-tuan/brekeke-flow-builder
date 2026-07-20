#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_provenance_check.py -- TTS 文言の出所（プロベナンス）機械チェック

INC-260716-2（秋田 終話文言ハルシネーション混入）の再発防止ゲート。
設計書 YAML 内の全 TTS 文言（retry_tts / reconfirm_tts 含む）を文単位に分割し、
「人間が確認した原資料」（Sheet_TTS.csv / sheet1_input.csv / customer_docs 等）に
存在するかを照合する。

ルール（2026-07-16 確定）:
  - コード（決定論）が生成する定型文はスキップしてよい
    （retry の「恐れ入りますが再度、」接頭辞、scaffold/csv_to_yaml の既定文言等）
  - それ以外で原資料に存在しない文 = AI が補完した可能性 → CRITICAL として列挙
  - retry 文も対象（接頭辞を剥がした残りが原資料に必要）

使い方:
    python3 schemas/tts_provenance_check.py <設計書.yaml> [--source FILE ...]

  --source 省略時は設計書と同じディレクトリから
  spec_*Sheet_TTS*.csv / sheet1_input.csv / spec_*Sheet1_input.csv /
  spec_*Sheet_Termination*.csv / reference/ 配下の .md .txt .csv を自動収集する。

終了コード:
    0: PASS（未照合文なし） / 1: FAIL（未照合文あり） / 2: 引数・入力エラー
"""

import argparse
import glob
import os
import re
import sys

import yaml

# ── コード生成の定型（照合免除） ──────────────────────────

# retry 接頭辞（csv_to_yaml.py / scaffold が機械的に付与）— 剥がして残りを照合する
RETRY_PREFIXES = [
    "恐れ入りますが再度、",
    "恐れ入りますが、再度",
]

# 決定論コードが埋め込む既定文言（csv_to_yaml.py / scaffold_generator.py 由来）。
# ここに載る文はソース照合を免除する。追加時は生成元スクリプトの行を併記すること。
CODE_GENERATED_SENTENCES = {
    # csv_to_yaml.py END_非通知 既定
    "恐れ入りますが、電話番号を通知しておかけ直しください",
    "お電話ありがとうございました",
    "それでは失礼いたします",
}

# 記入待ちプレースホルダー（V-1/qa_validator 側の担当。ここでは WARNING 表示のみ）
PLACEHOLDER_RE = re.compile(r"[（(]要記入")

_VAR_RE = re.compile(r"<%\s*[^%]+?\s*%>")
_TTS_WRAP_RE = re.compile(r"^\{tts_(?:g|ai)\s*:\s*(.*)\}$", re.DOTALL)


def normalize(text: str) -> str:
    """照合用正規化: tts ラッパー除去 → 変数プレースホルダー除去 → 空白・句読点類を除去"""
    m = _TTS_WRAP_RE.match(text.strip())
    if m:
        text = m.group(1)
    text = _VAR_RE.sub("", text)
    text = re.sub(r"[\s　]+", "", text)
    text = re.sub(r"[、。，．・…！!？?「」『』【】（）()\\\"'“”​]+", "", text)
    return text


def split_sentences(text: str) -> list[str]:
    """{tts_g:...} を剥がし 。！？ で文分割"""
    m = _TTS_WRAP_RE.match(text.strip())
    if m:
        text = m.group(1)
    parts = re.split(r"(?<=[。！？!?])", text)
    return [p.strip() for p in parts if p.strip()]


def strip_retry_prefix(sentence: str) -> str:
    for p in RETRY_PREFIXES:
        if sentence.startswith(p):
            return sentence[len(p):]
    return sentence


def collect_tts(d: dict) -> list[tuple[str, str, str]]:
    """設計書から (場所, フィールド, TTSテキスト) を列挙"""
    out = []
    for sd in d.get("step_details") or []:
        if not isinstance(sd, dict):
            continue
        name = str(sd.get("step_name", "?"))
        for fld in ("tts_announcement", "retry_tts", "reconfirm_tts"):
            v = sd.get(fld)
            if isinstance(v, str) and v.strip():
                out.append((f"step_details:{name}", fld, v))
    for tm in d.get("tts_modules") or []:
        if isinstance(tm, dict) and isinstance(tm.get("announcement"), str):
            out.append((f"tts_modules:{tm.get('module_name', '?')}", "announcement",
                        tm["announcement"]))
    for tp in d.get("termination_patterns") or []:
        if isinstance(tp, dict) and isinstance(tp.get("tts_announcement"), str):
            out.append((f"termination:{tp.get('name', '?')}", "tts_announcement",
                        tp["tts_announcement"]))
    return out


def autodetect_sources(spec_path: str) -> list[str]:
    base = os.path.dirname(os.path.abspath(spec_path))
    pats = [
        "spec_*Sheet_TTS*.csv", "spec_*Sheet1_input*.csv", "sheet1_input.csv",
        "spec_*Sheet_Termination*.csv", "spec_*Sheet2*.csv",
        os.path.join("reference", "*.md"), os.path.join("reference", "*.txt"),
        os.path.join("reference", "*.csv"),
    ]
    found: list[str] = []
    for p in pats:
        found.extend(sorted(glob.glob(os.path.join(base, p))))
    return found


def load_corpus(paths: list[str]) -> str:
    """全ソースを正規化済み 1 本のテキストに結合"""
    chunks = []
    for p in paths:
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                chunks.append(normalize(f.read()))
        except OSError as e:
            print(f"[WARN] ソースを読めません: {p} ({e})", file=sys.stderr)
    return "\n".join(chunks)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="TTS 文言プロベナンス照合")
    ap.add_argument("spec", help="設計書 YAML パス")
    ap.add_argument("--source", action="append", default=[],
                    help="原資料ファイル（複数可）。省略時は自動収集")
    args = ap.parse_args()

    try:
        with open(args.spec, encoding="utf-8") as f:
            d = yaml.safe_load(f.read())
    except (OSError, yaml.YAMLError) as e:
        print(f"[ERROR] 設計書を読めません: {e}")
        sys.exit(2)
    if not isinstance(d, dict):
        print("[ERROR] YAML のルートが辞書ではありません")
        sys.exit(2)

    sources = args.source or autodetect_sources(args.spec)
    if not sources:
        print("[ERROR] 原資料が見つかりません。--source で指定してください")
        sys.exit(2)
    corpus = load_corpus(sources)
    if not corpus.strip():
        print("[ERROR] 原資料が空です")
        sys.exit(2)

    unmatched: list[tuple[str, str, str]] = []
    placeholders = 0
    checked = 0
    seen: set[tuple[str, str]] = set()  # (場所, 正規化文) 重複抑止

    for loc, fld, raw in collect_tts(d):
        if PLACEHOLDER_RE.search(raw):
            placeholders += 1
            continue
        for sent in split_sentences(raw):
            base = strip_retry_prefix(sent)
            norm = normalize(base)
            if not norm:
                continue  # 変数のみ・記号のみ
            if norm in CODE_GENERATED_SENTENCES:
                continue  # コード生成の定型 → 免除
            checked += 1
            if norm in corpus:
                continue
            key = (loc, norm)
            if key not in seen:
                seen.add(key)
                unmatched.append((loc, fld, base))

    print(f"=== tts_provenance_check: {args.spec} ===")
    print(f"原資料: {len(sources)} ファイル / 照合文数: {checked} / "
          f"未照合: {len(unmatched)} / 要記入プレースホルダー: {placeholders}")
    print()
    if unmatched:
        print("[CRITICAL] 以下の文は原資料に見つかりません（AI 補完・転記ミスの疑い）。")
        print("           原資料（PDF原本/CSV）と突き合わせ、正なら原資料側に追記、")
        print("           誤なら設計書側を修正してください。")
        print()
        for loc, fld, sent in unmatched:
            print(f"  - {loc} .{fld}")
            print(f"      「{sent}」")
        sys.exit(1)
    print("PASS -- 全 TTS 文言が原資料と照合できました")
    sys.exit(0)


if __name__ == "__main__":
    main()
