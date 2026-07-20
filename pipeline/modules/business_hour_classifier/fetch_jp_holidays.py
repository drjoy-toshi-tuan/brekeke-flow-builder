"""fetch_jp_holidays.py — 内閣府公式 CSV から日本の祝日を yyyy-MM-dd リスト化。

データソース (CC-BY ライセンス、内閣府 大臣官房総務課、更新 年 1):
  https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv
  メタデータ: https://data.e-gov.go.jp/data/api/action/package_show?id=cao_20190522_0002

毎年 2 月頃に内閣府が翌年分を CSV に追記して公開する。3 月初旬を目処に本スクリプトを
実行して取得 → 出力テキストを Brekeke Note `drjoy.holidays` に末尾追記する運用。

Usage:
  python fetch_jp_holidays.py                 # 当年 + 翌年 (既定)
  python fetch_jp_holidays.py 2027            # 指定年のみ
  python fetch_jp_holidays.py 2026 2027       # 範囲指定 (両端含む)
  python fetch_jp_holidays.py --all           # CSV 全件 (1955-)
  python fetch_jp_holidays.py 2026 2027 -o holidays.txt    # ファイル出力
  python fetch_jp_holidays.py 2026 2027 | clip             # クリップボードに乗せる (Windows)

stdlib のみ (pip install 禁止ポリシー準拠)。
"""
from __future__ import annotations

import argparse
import csv
import datetime as _dt
import io
import ssl
import sys
import urllib.request

CSV_URL = "https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv"


def _build_ssl_context() -> ssl.SSLContext:
    """社内 TLS インスペクション対策 SSL context ([[feedback_tls_inspection_corp_pc]] 準拠)。

    Windows 証明書ストア (ROOT/CA) を投入 + VERIFY_X509_STRICT 解除。Linux/CCR では
    enum_certificates が無いため no-op で certifi のみのデフォルト動作にフォールバック。
    """
    ctx = ssl.create_default_context()
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    if not hasattr(ssl, "enum_certificates"):
        return ctx
    for store_name in ("ROOT", "CA"):
        try:
            for cert_der, _enc, trust in ssl.enum_certificates(store_name):
                if trust is True or (isinstance(trust, set) and trust):
                    try:
                        pem = ssl.DER_cert_to_PEM_cert(cert_der)
                        ctx.load_verify_locations(cadata=pem)
                    except ssl.SSLError:
                        continue
        except OSError:
            continue
    return ctx


def fetch_csv() -> list[tuple[str, str]]:
    """内閣府 CSV を取得し (yyyy-MM-dd, 祝日名) の list で返す。"""
    ctx = _build_ssl_context()
    with urllib.request.urlopen(CSV_URL, timeout=15, context=ctx) as resp:
        raw = resp.read()
    # Shift_JIS (cp932 superset で読む)
    text = raw.decode("cp932", errors="replace")
    reader = csv.reader(io.StringIO(text))
    out: list[tuple[str, str]] = []
    for i, row in enumerate(reader):
        if i == 0 or len(row) < 2:  # ヘッダー / 空行スキップ
            continue
        raw_date, name = row[0].strip(), row[1].strip()
        if not raw_date:
            continue
        try:
            dt = _dt.datetime.strptime(raw_date, "%Y/%m/%d").date()
        except ValueError:
            print(f"WARN: skipping unparseable row {i}: {row!r}", file=sys.stderr)
            continue
        out.append((dt.isoformat(), name))
    return out


def filter_years(rows: list[tuple[str, str]], year_from: int, year_to: int) -> list[tuple[str, str]]:
    return [(d, n) for (d, n) in rows if year_from <= int(d[:4]) <= year_to]


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("years", nargs="*", type=int,
                   help="フィルタ年 (1 個=その年のみ / 2 個=範囲)。省略時は当年+翌年")
    p.add_argument("--all", action="store_true", help="フィルタなしで全件出力")
    p.add_argument("-o", "--out", help="ファイル出力先 (省略時 stdout)")
    p.add_argument("--with-name", action="store_true", help="祝日名も付与 (yyyy-MM-dd,祝日名)")
    args = p.parse_args(argv)

    rows = fetch_csv()

    if not args.all:
        if len(args.years) == 0:
            today = _dt.date.today()
            year_from, year_to = today.year, today.year + 1
        elif len(args.years) == 1:
            year_from = year_to = args.years[0]
        elif len(args.years) == 2:
            year_from, year_to = sorted(args.years)
        else:
            print("ERROR: years は 0 / 1 / 2 個まで", file=sys.stderr)
            return 2
        rows = filter_years(rows, year_from, year_to)

    lines = []
    for date, name in rows:
        if args.with_name:
            lines.append(f"{date},{name}")
        else:
            lines.append(date)
    body = "\n".join(lines) + "\n"

    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        print(f"wrote {len(lines)} lines to {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
