#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""combine_spec_sheets.py — CSV入口パイプラインが生成した複数シートCSVを1つのHTMLに統合する。

raw_to_spec.py が出力する Sheet1_input / Sheet2_flow / Sheet3_blocktype / Sheet_AmiVoice /
Sheet_Context / Sheet_Script / Sheet_Settings / Sheet_Termination / Sheet_TTS は
output/scenarios/{facility}_{flow}/ 配下に別々の CSV として存在する。
顧客への技術仕様確認用に、これらを1ファイルにまとめて閲覧しやすくする。

外部ライブラリ不使用（openpyxl 等はインストール禁止のため）。標準ライブラリの csv/html のみ。

使い方:
  python3 tools/combine_spec_sheets.py --facility <施設名> --flow <フロー名>
  python3 tools/combine_spec_sheets.py --facility <施設名> --flow <フロー名> --out <出力パス>
"""
from __future__ import annotations

import argparse
import csv
import html
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# シートファイル名サフィックス → (表示順, 見出し, 説明)
SHEET_SECTIONS = [
    ("Sheet1_input", "① 聴取項目・トーク内容 一覧",
     "電話で何を聞き、何を話すか。各項目の質問文・選択肢・聞き取り直し回数など。"),
    ("Sheet2_flow", "② 分岐ルート（予約／変更／キャンセル／その他）",
     "ご用件ごとに、どの項目をどの順番で聞くかのルート。"),
    ("Sheet3_blocktype", "③ 項目種別の確認",
     "各項目がどの処理方式（聴取・自動判定・案内のみ 等）で扱われるかの一覧。"),
    ("Sheet_AmiVoice", "④ 音声認識 登録単語",
     "音声認識の精度を上げるために登録する単語（科名・固有名詞 等）。"),
    ("Sheet_Context", "⑤ 保存する情報の一覧",
     "通話中に取得・保存する情報の項目（お名前・電話番号 等）。"),
    ("Sheet_Script", "⑥ 自動判定ロジック",
     "選択肢の振り分けなど、プログラムが自動判定する処理の一覧。"),
    ("Sheet_Settings", "⑦ 設定値",
     "施設名・電話番号・受付時間などの基本設定。"),
    ("Sheet_Termination", "⑧ 終話パターン",
     "通話の終わり方（正常終了・転送・お断り 等）ごとの案内文言。"),
    ("Sheet_TTS", "⑨ 発話文言 一覧",
     "実際に読み上げる文言の全リスト（確認用）。"),
]


def _read_csv(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _render_table(header: list[str], rows: list[list[str]]) -> str:
    if not header:
        return '<p class="empty">（データなし）</p>'
    thead = "".join(f"<th>{html.escape(h)}</th>" for h in header)
    trs = []
    for row in rows:
        cells = list(row) + [""] * (len(header) - len(row))
        tds = "".join(f"<td>{html.escape(c).replace(chr(10), '<br>')}</td>" for c in cells[:len(header)])
        trs.append(f"<tr>{tds}</tr>")
    return (
        f'<div class="table-wrap"><table><thead><tr>{thead}</tr></thead>'
        f'<tbody>{"".join(trs)}</tbody></table></div>'
    )


def build_html(facility: str, flow: str, scenario_dir: Path) -> str:
    sections_html = []
    toc_html = []
    found_any = False
    for suffix, title, desc in SHEET_SECTIONS:
        matches = sorted(scenario_dir.glob(f"spec_*_{suffix}.csv"))
        anchor = suffix
        if not matches:
            sections_html.append(
                f'<section id="{anchor}"><h2>{html.escape(title)}</h2>'
                f'<p class="desc">{html.escape(desc)}</p>'
                f'<p class="empty">（このシートは未生成です）</p></section>'
            )
            continue
        found_any = True
        header, rows = _read_csv(matches[0])
        toc_html.append(f'<li><a href="#{anchor}">{html.escape(title)}</a>（{len(rows)}件）</li>')
        sections_html.append(
            f'<section id="{anchor}"><h2>{html.escape(title)}</h2>'
            f'<p class="desc">{html.escape(desc)}</p>'
            f'{_render_table(header, rows)}</section>'
        )
    if not found_any:
        raise SystemExit(f"[ERROR] シートCSVが1件も見つかりません: {scenario_dir}")

    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>設計仕様まとめ — {html.escape(facility)} {html.escape(flow)}</title>
<style>
  body {{ font-family: 'Segoe UI','Hiragino Sans','Yu Gothic UI',sans-serif; margin: 0; background: #f9fafb; color: #111827; line-height: 1.6; }}
  header {{ background: linear-gradient(135deg, #1e40af, #3b82f6); color: #fff; padding: 2rem; text-align: center; }}
  header h1 {{ margin: 0 0 0.3rem; font-size: 1.6rem; }}
  header p {{ margin: 0; opacity: 0.85; font-size: 0.9rem; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem; }}
  nav.toc {{ background: #fff; border-radius: 10px; padding: 1rem 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  nav.toc h2 {{ font-size: 1rem; margin: 0 0 0.5rem; }}
  nav.toc ul {{ margin: 0; padding-left: 1.2rem; }}
  nav.toc a {{ color: #2563eb; text-decoration: none; }}
  nav.toc a:hover {{ text-decoration: underline; }}
  section {{ background: #fff; border-radius: 10px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  section h2 {{ font-size: 1.15rem; border-bottom: 2px solid #2563eb; padding-bottom: 0.4rem; margin: 0 0 0.4rem; }}
  .desc {{ color: #6b7280; font-size: 0.85rem; margin: 0 0 0.8rem; }}
  .empty {{ color: #9ca3af; font-size: 0.85rem; }}
  .table-wrap {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
  th {{ background: #f3f4f6; text-align: left; padding: 0.5rem 0.7rem; white-space: nowrap; position: sticky; top: 0; }}
  td {{ padding: 0.5rem 0.7rem; border-bottom: 1px solid #e5e7eb; vertical-align: top; }}
  tr:hover td {{ background: #f9fafb; }}
  footer {{ text-align: center; color: #9ca3af; font-size: 0.8rem; padding: 2rem 0; }}
</style>
</head>
<body>
<header>
  <h1>設計仕様まとめ — {html.escape(facility)} {html.escape(flow)}</h1>
  <p>CSV入口パイプラインが生成した各シートを1ページに統合したものです（顧客確認用）。</p>
</header>
<div class="container">
  <nav class="toc"><h2>目次</h2><ul>{"".join(toc_html)}</ul></nav>
  {"".join(sections_html)}
</div>
<footer>tools/combine_spec_sheets.py により自動生成</footer>
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="複数シートCSVを1つのHTMLに統合する")
    ap.add_argument("--facility", required=True, help="施設名")
    ap.add_argument("--flow", required=True, help="フロー名")
    ap.add_argument("--out", help="出力パス（省略時 output/scenarios/{facility}_{flow}/設計仕様まとめ_{facility}_{flow}.html）")
    args = ap.parse_args()

    scenario_dir = REPO / "output" / "scenarios" / f"{args.facility}_{args.flow}"
    if not scenario_dir.is_dir():
        raise SystemExit(f"[ERROR] シナリオディレクトリが見つかりません: {scenario_dir}")

    out_path = Path(args.out) if args.out else scenario_dir / f"設計仕様まとめ_{args.facility}_{args.flow}.html"
    doc = build_html(args.facility, args.flow, scenario_dir)
    out_path.write_text(doc, encoding="utf-8")
    print(f"[OK] {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
