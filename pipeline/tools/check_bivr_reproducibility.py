# -*- coding: utf-8 -*-
"""check_bivr_reproducibility.py — コミット済み .bivr が設計書からの再ビルドと一致するか検査する。

成果物ドリフト（コミット bivr が設計書 SSoT＋現行パイプラインの出力と乖離している状態）を
機械検出するゲート（Issue #229）。設計書 YAML を正本とし、scaffold_generator → layout_calculator
→ build_bivr の正規チェーンで再ビルドした bivr の **フロー JSON**（ZIP タイムスタンプ非依存）を
コミット済み bivr のフロー JSON と突合する。

build_bivr は #224 で ZIP 日時固定済み（バイト再現可能）だが、本ゲートは ZIP メタデータに依存せず
**デコード後のフロー JSON 内容**で比較するため、より頑健に「中身の」ドリフトだけを検出する。

使い方:
    # 単一シナリオ（ディレクトリ指定。設計書とコミット bivr を規約から自動解決）
    python tools/check_bivr_reproducibility.py output/scenarios/<施設>_<flow>/

    # 明示指定
    python tools/check_bivr_reproducibility.py --spec <設計書.yaml> --bivr <コミット.bivr>

    # 複数シナリオを一括（ドリフトが1件でもあれば exit 1）
    python tools/check_bivr_reproducibility.py output/scenarios/*/

終了コード: 0=全一致（ドリフトなし） / 1=ドリフト検出 / 2=実行エラー（再ビルド失敗等）。
"""
import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = PROJECT_ROOT / "scripts"


def _flows_of(bivr_path: Path) -> dict:
    """bivr(ZIP) の全フロー JSON を {flow_name: flow_dict} で返す。フロー名は JSON の name 優先、
    無ければ ZIP エントリ名。"""
    flows = {}
    with zipfile.ZipFile(bivr_path) as z:
        for n in z.namelist():
            try:
                d = json.loads(z.read(n).decode("utf-8"))
            except Exception:
                continue
            key = d.get("name") or n
            flows[key] = d
    return flows


def _resolve_pair(arg_path: Path, spec_override, bivr_override):
    """シナリオディレクトリ（または明示指定）から (spec_yaml, committed_bivr) を解決する。
    コミット bivr は『連結テスト』を含まない .bivr を主成果物とみなす。"""
    if spec_override and bivr_override:
        return Path(spec_override), Path(bivr_override)
    d = arg_path
    if d.is_file():
        d = d.parent
    specs = sorted(d.glob("設計書_*.yaml")) or sorted(d.glob("*.yaml"))
    bivrs = [b for b in sorted(d.glob("*.bivr")) if "連結テスト" not in b.name]
    spec = Path(spec_override) if spec_override else (specs[0] if specs else None)
    bivr = Path(bivr_override) if bivr_override else (bivrs[0] if bivrs else None)
    return spec, bivr


def _rebuild(spec: Path, workdir: Path) -> Path:
    """設計書 YAML を正規チェーンで再ビルドし、再ビルド bivr のパスを返す。失敗時は RuntimeError。"""
    env_run = {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    import os
    env = {**os.environ, **env_run}
    scaf = workdir / "scaffold.json"
    layout = workdir / "layout.json"
    out_bivr = workdir / "rebuild.bivr"

    def run(cmd):
        r = subprocess.run([sys.executable, *cmd], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, cwd=str(PROJECT_ROOT))
        if r.returncode != 0:
            raise RuntimeError("再ビルド失敗: %s\n%s" % (" ".join(str(c) for c in cmd),
                                                        (r.stderr or r.stdout or "").strip()[-1500:]))

    run([str(SCRIPTS / "scaffold_generator.py"), str(spec), str(scaf)])
    run([str(SCRIPTS / "layout_calculator.py"), str(scaf), str(spec), str(layout)])
    run([str(SCRIPTS / "build_bivr.py"), str(layout), "-o", str(out_bivr)])
    return out_bivr


def _diff_flows(committed: dict, rebuilt: dict) -> list:
    """フロー JSON 群を突合し、差分の人間可読リストを返す（空=一致）。"""
    diffs = []
    for fname in sorted(set(committed) | set(rebuilt)):
        if fname not in rebuilt:
            diffs.append("flow '%s': コミット版のみ（再ビルドに無い）" % fname)
            continue
        if fname not in committed:
            diffs.append("flow '%s': 再ビルドのみ（コミット版に無い）" % fname)
            continue
        cm = (committed[fname].get("modules") or {})
        rm = (rebuilt[fname].get("modules") or {})
        for mn in sorted(set(cm) - set(rm)):
            diffs.append("flow '%s': module '%s' がコミット版のみ（再ビルドで消失）" % (fname, mn))
        for mn in sorted(set(rm) - set(cm)):
            diffs.append("flow '%s': module '%s' が再ビルドのみ（コミット版に無い）" % (fname, mn))
        for mn in sorted(set(cm) & set(rm)):
            # キー順非依存で内容比較（params の script 本体差・next 差などを検出）
            if json.dumps(cm[mn], ensure_ascii=False, sort_keys=True) != \
               json.dumps(rm[mn], ensure_ascii=False, sort_keys=True):
                diffs.append("flow '%s': module '%s' の内容が相違（script/prompt/next 等）" % (fname, mn))
    return diffs


def check_one(arg_path: Path, spec_override=None, bivr_override=None) -> int:
    spec, bivr = _resolve_pair(arg_path, spec_override, bivr_override)
    label = (bivr.name if bivr else str(arg_path))
    if not spec or not spec.exists():
        print("[SKIP] %s: 設計書 YAML が見つかりません" % label)
        return 0
    if not bivr or not bivr.exists():
        print("[SKIP] %s: コミット bivr が見つかりません" % label)
        return 0
    try:
        with tempfile.TemporaryDirectory() as td:
            rebuilt_bivr = _rebuild(spec, Path(td))
            committed_flows = _flows_of(bivr)
            rebuilt_flows = _flows_of(rebuilt_bivr)
            diffs = _diff_flows(committed_flows, rebuilt_flows)
    except RuntimeError as e:
        print("[ERROR] %s: %s" % (label, e))
        return 2
    if not diffs:
        print("[OK] %s: コミット bivr == 設計書からの再ビルド（ドリフトなし）" % label)
        return 0
    print("[DRIFT] %s: %d 件の差分（コミット成果物が陳腐化）" % (label, len(diffs)))
    for d in diffs[:40]:
        print("  - " + d)
    if len(diffs) > 40:
        print("  … 他 %d 件" % (len(diffs) - 40))
    print("  → 設計書 YAML を SSoT として再ビルドを再コミットしてください"
          "（手動チェーンは README『手動ビルドチェーン』参照）。")
    return 1


def main():
    ap = argparse.ArgumentParser(
        prog="check_bivr_reproducibility.py",
        description="コミット済み .bivr が設計書 YAML からの再ビルドと一致するか検査する（成果物ドリフト検出・#229）。",
        epilog="終了コード: 0=一致 / 1=ドリフト / 2=再ビルド失敗。",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="シナリオディレクトリ（複数可・glob 展開可）")
    ap.add_argument("--spec", default=None, help="設計書 YAML を明示指定（paths は1件のみ前提）")
    ap.add_argument("--bivr", default=None, help="コミット bivr を明示指定")
    args = ap.parse_args()

    if not args.paths:
        ap.error("シナリオディレクトリを1つ以上指定してください（または --spec/--bivr）")

    worst = 0
    n_ok = n_drift = n_err = 0
    for p in args.paths:
        rc = check_one(Path(p), args.spec, args.bivr)
        worst = max(worst, rc)
        n_ok += (rc == 0)
        n_drift += (rc == 1)
        n_err += (rc == 2)
    if len(args.paths) > 1:
        print("\n[SUMMARY] OK=%d / DRIFT=%d / ERROR=%d（計 %d）"
              % (n_ok, n_drift, n_err, len(args.paths)))
    sys.exit(worst)


if __name__ == "__main__":
    main()
