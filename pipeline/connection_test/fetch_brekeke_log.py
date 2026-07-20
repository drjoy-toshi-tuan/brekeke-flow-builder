#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_brekeke_log.py — Brekeke 管理画面から通話ログ CSV を自動取得 (Selenium)

Phase 4: Selenium + Chrome で Brekeke PA にログインし、
指定期間の通話ログを CSV でダウンロードして output/{施設}/logs/ に保存する。

実行環境: ローカル Windows PC（Brekeke が社内ネットワーク上にある想定）
必要: Python 3.x / selenium 4.x（ChromeDriver は Selenium Manager が自動管理）

Usage:
  python connection_test\\fetch_brekeke_log.py ^
      --facility 福岡大学 ^
      --flow     診療 ^
      [--date    2026-07-09]   # 取得日(省略=今日)
      [--days    1]             # 遡る日数(省略=1)
      [--headless]              # ブラウザを表示しない

認証情報は環境変数 or .env で指定:
  BREKEKE_URL    例: https://your-brekeke.example.com
  BREKEKE_USER   管理者ユーザー名
  BREKEKE_PASS   パスワード
"""

import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path


def load_dotenv(path: str = ".env") -> None:
    p = Path(path)
    if not p.exists():
        # gen_flow ルートの .env も探す
        p = Path(__file__).parent.parent / ".env"
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


# ── Selenium ドライバ初期化 ───────────────────────────────────────────────

def make_driver(headless: bool, download_dir: str):
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    options.add_experimental_option("prefs", {
        "download.default_directory":        download_dir,
        "download.prompt_for_download":      False,
        "download.directory_upgrade":        True,
        "safebrowsing.enabled":              True,
    })
    # Selenium 4.6+ は Selenium Manager が ChromeDriver を自動ダウンロード
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    return driver


# ── ログイン ──────────────────────────────────────────────────────────────

def login(driver, base_url: str, user: str, password: str) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    login_url = base_url.rstrip("/") + "/pa/"
    print(f"[LOGIN] {login_url}")
    driver.get(login_url)

    wait = WebDriverWait(driver, 15)

    # ユーザー名入力（一般的な name/id 候補）
    for selector in ["username", "user", "loginId", "login_id", "email"]:
        try:
            el = driver.find_element(By.NAME, selector)
            el.clear()
            el.send_keys(user)
            break
        except Exception:
            continue

    # パスワード入力
    for selector in ["password", "pass", "passwd"]:
        try:
            el = driver.find_element(By.NAME, selector)
            el.clear()
            el.send_keys(password)
            break
        except Exception:
            continue

    # ログインボタン押下
    for selector in [
        "//input[@type='submit']",
        "//button[@type='submit']",
        "//button[contains(text(),'ログイン')]",
        "//button[contains(text(),'Login')]",
        "//input[@value='Login']",
    ]:
        try:
            btn = driver.find_element(By.XPATH, selector)
            btn.click()
            break
        except Exception:
            continue

    # ログイン完了待機（URL 変化 or ログアウトリンク出現）
    try:
        wait.until(lambda d: "logout" in d.page_source.lower() or d.current_url != login_url)
    except Exception:
        pass

    if "logout" not in driver.page_source.lower() and "ログアウト" not in driver.page_source:
        raise RuntimeError(
            "ログインに失敗しました。BREKEKE_URL / USER / PASS を確認してください。\n"
            f"現在の URL: {driver.current_url}"
        )
    print(f"[LOGIN] OK  (現在URL: {driver.current_url})")


# ── 通話ログ CSV ダウンロード ─────────────────────────────────────────────

def fetch_call_log(
    driver,
    base_url: str,
    date_from: str,
    date_to: str,
    download_dir: str,
    scenario_filter: str = "",
) -> Path:
    """
    Brekeke PA の通話ログページを開き、CSV をダウンロードして返す。

    Brekeke のバージョンによって URL やフォーム名が異なる場合がある。
    うまく動かない場合は --debug オプションでブラウザを表示して確認すること。
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC

    base = base_url.rstrip("/")
    wait = WebDriverWait(driver, 20)

    # 候補 URL を順に試す
    log_urls = [
        f"{base}/pa/call_log",
        f"{base}/pa/#/call_log",
        f"{base}/pa/calllog",
        f"{base}/pa/logs",
        f"{base}/pa/reports/call_log",
    ]

    for url in log_urls:
        driver.get(url)
        time.sleep(1.5)
        if "404" not in driver.title and driver.current_url != base + "/pa/":
            print(f"[LOG_PAGE] {driver.current_url}")
            break

    # 日付範囲入力（よくある name 候補）
    for name_from in ["from", "date_from", "startDate", "start_date", "fromDate"]:
        try:
            el = driver.find_element(By.NAME, name_from)
            el.clear()
            el.send_keys(date_from)
            break
        except Exception:
            continue

    for name_to in ["to", "date_to", "endDate", "end_date", "toDate"]:
        try:
            el = driver.find_element(By.NAME, name_to)
            el.clear()
            el.send_keys(date_to)
            break
        except Exception:
            continue

    # シナリオフィルタ（あれば）
    if scenario_filter:
        for name in ["scenario", "scenarioName", "flow"]:
            try:
                el = driver.find_element(By.NAME, name)
                el.clear()
                el.send_keys(scenario_filter)
                break
            except Exception:
                continue

    # 検索ボタン押下
    for xpath in [
        "//button[contains(text(),'検索')]",
        "//button[contains(text(),'Search')]",
        "//input[@value='検索']",
        "//input[@value='Search']",
        "//button[@type='submit']",
    ]:
        try:
            driver.find_element(By.XPATH, xpath).click()
            time.sleep(2)
            break
        except Exception:
            continue

    # ダウンロード前のファイル一覧
    before = set(Path(download_dir).glob("*.csv"))

    # CSV エクスポートボタン押下
    for xpath in [
        "//button[contains(text(),'CSV')]",
        "//a[contains(text(),'CSV')]",
        "//button[contains(text(),'エクスポート')]",
        "//a[contains(text(),'エクスポート')]",
        "//button[contains(text(),'Export')]",
        "//a[contains(text(),'Download')]",
    ]:
        try:
            driver.find_element(By.XPATH, xpath).click()
            print(f"[EXPORT] CSV ダウンロード開始")
            break
        except Exception:
            continue

    # ダウンロード完了待機（最大 30 秒）
    csv_path = None
    for _ in range(30):
        time.sleep(1)
        after = set(Path(download_dir).glob("*.csv"))
        new_files = after - before
        if new_files:
            csv_path = max(new_files, key=lambda p: p.stat().st_mtime)
            break

    if csv_path is None:
        # 直接 URL アクセスで CSV を取得する試み（フォールバック）
        print("[WARN] ダウンロードボタンが検出できませんでした。直接 URL を試みます...")
        from urllib.parse import urlencode
        params = urlencode({"format": "csv", "from": date_from, "to": date_to, "encoding": "UTF-8"})
        export_url = f"{base}/pa/call_log/export?{params}"
        driver.get(export_url)
        time.sleep(3)
        after = set(Path(download_dir).glob("*.csv"))
        new_files = after - before
        if new_files:
            csv_path = max(new_files, key=lambda p: p.stat().st_mtime)

    if csv_path is None:
        raise RuntimeError(
            "CSV ファイルのダウンロードを確認できませんでした。\n"
            f"ダウンロードフォルダ: {download_dir}\n"
            "ヒント: --no-headless オプションでブラウザを表示して手動確認してください。"
        )

    print(f"[DOWNLOAD] {csv_path}")
    return csv_path


# ── CSV 後処理 ──────────────────────────────────────────────────────────────

def filter_and_save(src_csv: Path, out_path: Path, keyword: str) -> int:
    """キーワードでフィルタして out_path に保存。行数を返す。"""
    text = src_csv.read_text(encoding="utf-8-sig", errors="replace")
    lines = text.splitlines(keepends=True)
    if not lines:
        out_path.write_text("", encoding="utf-8-sig")
        return 0

    header = lines[0]
    if keyword:
        data = [l for l in lines[1:] if keyword in l]
    else:
        data = lines[1:]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(header + "".join(data), encoding="utf-8-sig")
    return len(data)


def detect_trace_column(csv_path: Path) -> int:
    text = csv_path.read_text(encoding="utf-8-sig", errors="replace")
    for line in text.splitlines():
        if "__テストセレクタ" in line:
            for i, col in enumerate(line.split(",")):
                if "__テストセレクタ" in col:
                    return i
    return -1


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    load_dotenv()

    ap = argparse.ArgumentParser(description="Brekeke 通話ログ CSV 取得 (Selenium)")
    ap.add_argument("--facility",    default="",    help="施設名")
    ap.add_argument("--flow",        default="",    help="フロー名")
    ap.add_argument("--date",        default="",    help="取得対象日 YYYY-MM-DD（省略=今日）")
    ap.add_argument("--days",        type=int, default=1, help="遡る日数（省略=1）")
    ap.add_argument("--scenario",    default="",    help="シナリオ名フィルタ（部分一致）")
    ap.add_argument("--out",         default="",    help="出力 CSV パス")
    ap.add_argument("--headless",    action="store_true", help="ヘッドレスモード（画面非表示）")
    ap.add_argument("--no-headless", action="store_true", help="ブラウザを表示（デフォルト）")
    ap.add_argument("--url",         default="",    help="Brekeke URL（env: BREKEKE_URL）")
    ap.add_argument("--user",        default="",    help="ユーザー名（env: BREKEKE_USER）")
    ap.add_argument("--password",    default="",    help="パスワード（env: BREKEKE_PASS）")
    args = ap.parse_args()

    brekeke_url  = args.url      or os.environ.get("BREKEKE_URL",  "")
    brekeke_user = args.user     or os.environ.get("BREKEKE_USER", "")
    brekeke_pass = args.password or os.environ.get("BREKEKE_PASS", "")

    if not brekeke_url:
        print("[ERROR] BREKEKE_URL が未設定です。", file=sys.stderr)
        print("  .env ファイルに以下を記述してください:", file=sys.stderr)
        print("    BREKEKE_URL=https://your-brekeke.example.com", file=sys.stderr)
        print("    BREKEKE_USER=admin", file=sys.stderr)
        print("    BREKEKE_PASS=password", file=sys.stderr)
        return 1
    if not brekeke_user or not brekeke_pass:
        print("[ERROR] BREKEKE_USER / BREKEKE_PASS が未設定です。", file=sys.stderr)
        return 1

    # 日付範囲
    if args.date:
        date_to = datetime.strptime(args.date, "%Y-%m-%d")
    else:
        date_to = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    date_from = date_to - timedelta(days=args.days - 1)
    date_from_str = date_from.strftime("%Y-%m-%d")
    date_to_str   = date_to.strftime("%Y-%m-%d")

    # 出力パス
    ts = date_to.strftime("%Y%m%d")
    facility = args.facility or "unknown"
    flow     = args.flow     or "flow"
    if args.out:
        out_path = Path(args.out)
    else:
        out_path = Path(f"output/{facility}/logs/{facility}_{flow}_run_{ts}.csv")

    # ダウンロード先（一時ディレクトリ）
    import tempfile
    download_dir = str(Path(tempfile.mkdtemp()))

    # ヘッドレス設定（デフォルト: 表示あり。--headless で非表示）
    headless = args.headless and not args.no_headless

    driver = None
    try:
        print(f"[START] Selenium Chrome 起動 (headless={headless})")
        driver = make_driver(headless=headless, download_dir=download_dir)
        login(driver, brekeke_url, brekeke_user, brekeke_pass)
        csv_path = fetch_call_log(
            driver, brekeke_url,
            date_from_str, date_to_str,
            download_dir,
            args.scenario,
        )
    finally:
        if driver:
            driver.quit()

    # フィルタ & 保存
    keyword = args.scenario or args.facility
    count = filter_and_save(csv_path, out_path, keyword)
    print(f"[OK] {count} レコード → {out_path}")

    # トレース列検出
    col = detect_trace_column(out_path)
    if col >= 0:
        print(f"[INFO] チェックポイントトレース列: {col} (0-based, --col-trace に指定)")
    else:
        print("[WARN] トレース列が自動検出できませんでした。Brekeke ログの列名を確認してください。")

    print(f"\n[NEXT] python connection_test\\compare_p7_results.py \\")
    print(f"         --log   {out_path} \\")
    print(f"         --cases connection_test\\cases\\{facility}_{flow}_*.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
