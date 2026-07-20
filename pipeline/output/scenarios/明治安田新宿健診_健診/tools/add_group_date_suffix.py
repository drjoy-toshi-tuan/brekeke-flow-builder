# -*- coding: utf-8 -*-
"""bivr のグループ名に日付サフィックス _YYYYMMDD を付ける（インポート時の本番衝突回避）。

目的:
  Brekeke へインポートすると同一グループ名だと本番と同じ場所に入ってしまうため、
  グループ名にだけ日付サフィックスを付けて別グループとして取り込めるようにする。

規約（memory: reference_naming_date_suffix_on_group）:
  - 日付サフィックス _YYYYMMDD は **グループ名のみ**。フロー名は素のまま。
  - jump (Custom Jump to Flow の params.flowname) のグループ参照も verbatim で追従。

手法（バイト忠実）:
  - フロー JSON 内の "{group}$" を "{group}_{date}$" に生テキスト置換
    （name フィールドと jump flowname の両方を同時にカバー。本文には "{group}$" は
     出現しないことを別途検証済み＝プロンプト/分岐は不変）。
  - zip エントリ名は「グループとフロー名の区切り = 最初の %24($)」の直前に _date を挿入。
    これで元の URL エンコード方式（VN製/Python製）をそのまま温存できる。

使い方:
  python tools/add_group_date_suffix.py <in.bivr> <out.bivr> <group> <YYYYMMDD>
"""
import sys, io, zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    in_path, out_path, group, date = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    mark = group + "$"                 # 本文/フロー名/jump 内のグループ区切り
    new_mark = group + "_" + date + "$"
    n_content, n_entry = 0, 0

    with zipfile.ZipFile(in_path) as zin:
        infos = zin.infolist()
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in infos:
                fn = info.filename
                data = zin.read(fn)
                if fn.endswith(".txt"):
                    text = data.decode("utf-8")
                    c = text.count(mark)
                    if c:
                        text = text.replace(mark, new_mark)
                        n_content += c
                    data = text.encode("utf-8")
                    # エントリ名: 先頭 %24（group/flow 区切り）の直前へ _date を挿入
                    if "%24" in fn:
                        fn = fn.replace("%24", "_" + date + "%24", 1)
                        n_entry += 1
                zout.writestr(fn, data)

    # 検証
    with zipfile.ZipFile(out_path) as z:
        groups = set()
        leftover = 0
        for n in z.namelist():
            d = __import__("json").loads(z.read(n).decode("utf-8"))
            groups.add(d.get("name", "").split("$")[0])
            leftover += z.read(n).decode("utf-8").count(mark) - z.read(n).decode("utf-8").count(new_mark)
    print(f"  in  : {in_path}")
    print(f"  out : {out_path}")
    print(f"  置換: 本文 {n_content} 箇所 / エントリ名 {n_entry} 個")
    print(f"  新グループ名: {sorted(groups)}")
    if groups != {group + "_" + date}:
        raise SystemExit(f"ERROR: グループ名が想定外: {groups}")
    print("  OK")


if __name__ == "__main__":
    main()
