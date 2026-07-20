"""
build_bivr.py — フローJSONから .bivr パッケージを生成するスクリプト

使い方:
    # 単一フロー
    python3 scripts/build_bivr.py output/reviewed_テスト病院_受付.json

    # 複数フローを1つの .bivr に同梱
    python3 scripts/build_bivr.py output/flow1.json output/flow2.json -o output/combined.bivr

    # ワイルドカードで一括指定
    python3 scripts/build_bivr.py output/四谷メディカルキューブ_*.json -o output/四谷メディカルキューブ.bivr

    # 【推奨: 既存フロー修正時】元BIVRのフローを引き継ぎつつ修正分だけ差し替え
    python3 scripts/build_bivr.py output/patched_flow.json --merge-base docs/reference/original.bivr -o output/result.bivr

.bivr 仕様:
    - ZIPアーカイブ（拡張子を .bivr に変えたもの）
    - 内部に flows/ フォルダを持つ
    - フローJSONは @flow_{URLエンコード済みフロー名}.txt として配置
    - エンコード: 小文字a-zと数字0-9はそのまま、他は全て%XX
    - JSONは1行（minified）で格納
    - 1つの .bivr に複数フローを同梱可能

--merge-base オプション:
    元の .bivr に含まれる全フローをベースとして読み込み、
    引数で指定したJSONと同名のフローだけを差し替えて出力する。
    既存フロー修正時に、修正対象以外のフローが抜け落ちるのを防ぐ。
"""

import json
import sys
import os
import zipfile
from pathlib import Path


def load_flow(json_path: str) -> dict:
    with open(json_path, encoding="utf-8") as f:
        return json.load(f)


def flow_to_minified(flow: dict) -> str:
    return json.dumps(flow, ensure_ascii=False, separators=(",", ":"))


def encode_flow_name(name: str) -> str:
    """フロー名をBrekeke PBX互換でURLエンコードする。
    小文字a-zと数字0-9はそのまま、それ以外は全て%XXエンコード。"""
    result = []
    for b in name.encode("utf-8"):
        if (0x61 <= b <= 0x7A) or (0x30 <= b <= 0x39):
            result.append(chr(b))
        else:
            result.append(f"%{b:02X}")
    return "".join(result)


def load_flows_from_bivr(bivr_path: str) -> dict:
    """既存の .bivr からフロー名→(flow_dict) の辞書を返す。"""
    flows = {}
    with zipfile.ZipFile(bivr_path, "r") as zf:
        for entry in zf.namelist():
            if not entry.startswith("flows/"):
                continue
            raw = zf.read(entry).decode("utf-8")
            try:
                flow = json.loads(raw)
                name = flow.get("name", "")
                if name:
                    flows[name] = flow
            except json.JSONDecodeError:
                print(f"[WARN] JSONパース失敗（スキップ）: {entry}")
    return flows


def build_bivr(json_paths: list, output_path: str = None, merge_base: str = None) -> str:
    """複数のフローJSONを1つの .bivr にパッケージングする。

    merge_base が指定された場合、元BIVRの全フローをベースにして
    json_paths で指定されたフローだけを差し替える。
    """
    # 修正済みフローをロード（フロー名→flow_dict）
    patched = {}
    for json_path in json_paths:
        flow = load_flow(json_path)
        flow_name = flow.get("name", "")
        if not flow_name:
            print(f"[ERROR] JSONに 'name' フィールドがありません: {json_path}")
            sys.exit(1)
        patched[flow_name] = flow

    # ベースBIVRがある場合、元フローを読み込んで差し替えをマージ
    if merge_base:
        if not os.path.exists(merge_base):
            print(f"[ERROR] --merge-base で指定したファイルが見つかりません: {merge_base}")
            sys.exit(1)
        base_flows = load_flows_from_bivr(merge_base)
        # 元フローに修正分を上書きマージ
        merged = {**base_flows, **patched}
        replaced = [name for name in patched if name in base_flows]
        added = [name for name in patched if name not in base_flows]
        print(f"[INFO] ベースBIVR: {merge_base} ({len(base_flows)}フロー)")
        for name in replaced:
            print(f"       差し替え: {name}")
        for name in added:
            print(f"       新規追加: {name}")
        flows_dict = merged
    else:
        flows_dict = patched

    # 出力パスの決定
    if output_path is None:
        first_name = next(iter(flows_dict))
        group = first_name.split("$")[0] if "$" in first_name else first_name
        safe_group = group.replace("$", "_").replace("/", "_").replace("\\", "_")
        base_dir = Path(json_paths[0]).parent
        output_path = str(base_dir / f"{safe_group}.bivr")

    # バイト再現性のため ZIP エントリの更新時刻を固定する。
    # writestr に str 名を渡すと zipfile が time.localtime() を刻むため、
    # 同一内容でもビルド毎に SHA が変わってしまう（git noise / byte 一致検証不可）。
    # ZipInfo を固定日時で生成して書き込むことで、決定論ビルドが成果物レイヤまで再現可能になる。
    _FIXED_ZIP_DATE = (1980, 1, 1, 0, 0, 0)  # ZIP の最小許容日時
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for flow_name, flow in flows_dict.items():
            encoded_name = encode_flow_name(flow_name)
            archive_entry = f"flows/@flow_{encoded_name}.txt"
            minified_json = flow_to_minified(flow)
            zinfo = zipfile.ZipInfo(filename=archive_entry, date_time=_FIXED_ZIP_DATE)
            zinfo.compress_type = zipfile.ZIP_DEFLATED  # ZipInfo 既定は STORED のため明示
            zinfo.external_attr = 0o644 << 16  # -rw-r--r--
            zf.writestr(zinfo, minified_json.encode("utf-8"))

    print(f"[OK] 生成完了: {output_path}")
    print(f"     フロー数: {len(flows_dict)}")
    for flow_name, flow in flows_dict.items():
        mod_count = len(flow.get("modules", {}))
        tag = " ← 修正済み" if flow_name in patched else ""
        print(f"     - {flow_name} ({mod_count} modules){tag}")
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 scripts/build_bivr.py <flow.json> [-o <output.bivr>]")
        print("  python3 scripts/build_bivr.py <flow1.json> <flow2.json> ... [-o <output.bivr>]")
        print("  python3 scripts/build_bivr.py <patched.json> --merge-base <original.bivr> -o <output.bivr>")
        sys.exit(1)

    output_path = None
    merge_base = None
    args = list(sys.argv[1:])

    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args):
            output_path = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            print("[ERROR] -o の後に出力パスを指定してください")
            sys.exit(1)

    if "--merge-base" in args:
        idx = args.index("--merge-base")
        if idx + 1 < len(args):
            merge_base = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            print("[ERROR] --merge-base の後に元BIVRパスを指定してください")
            sys.exit(1)

    json_paths = [f for f in args if os.path.exists(f)]
    missing = [f for f in args if not os.path.exists(f)]
    for m in missing:
        print(f"[WARN] ファイルが見つかりません: {m}")

    if not json_paths:
        print("[ERROR] 有効なJSONファイルが見つかりません")
        sys.exit(1)

    build_bivr(json_paths, output_path, merge_base)


if __name__ == "__main__":
    main()
