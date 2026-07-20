# -*- coding: utf-8 -*-
"""連結テスト bivr の __テストセレクタ(DTMFケース選択) の params を修正する。

問題:
  stub_stt_connection.py はセレクタ雛形を「フロー内の既存 DTMF モジュール」から複製する。
  明治安田では 入力_生年月日(8桁DTMF) が雛形になり、その検証条件・終端キーをそのまま継承して
  しまった結果、1〜2桁のケース番号が弾かれ NO_RESULT → __保存tc が既定値 1 に落ち、
  ケース2以降を選べなかった（実機ログで確認・2026-06-16）。

修正（実機実証済の北里セレクタ profile に合わせる）:
  - condition  : 'val.length>7&&val.length<9'(8桁限定) -> '' (長さ制限なし)
  - termdtmf   : '*' -> '#'  （プロンプト「#を押してください」と一致させる）
  - profile_words : 生年月日用の読み辞書 -> '' （数字DTMF選択には不要）
  - probability/silent_detection_ms -> '' （音声検出系の余計な縛りを外す）
  - retry      : '1' -> '2'  （取りこぼし許容）
  ※ DTMF 取得そのもの(detection_flag等)は生年月日入力で実績がある値を温存。

使い方: python tools/fix_selector_params.py <in.bivr> <out.bivr>
"""
import sys, io, json, zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

FIX = {
    "termdtmf": "#",
    "condition": "",
    "profile_words": "",
    "probability": "",
    "silent_detection_ms": "",
    "retry": "2",
}


def main():
    in_path, out_path = sys.argv[1], sys.argv[2]
    patched = False
    with zipfile.ZipFile(in_path) as zin:
        infos = zin.infolist()
        out_entries = []
        for info in infos:
            data = zin.read(info.filename)
            if info.filename.endswith(".txt"):
                d = json.loads(data.decode("utf-8"))
                sel = d.get("modules", {}).get("__テストセレクタ")
                if sel is not None:
                    before = dict(sel["params"])
                    sel["params"].update(FIX)
                    patched = True
                    print("=== __テストセレクタ params 修正 ===")
                    for k, v in FIX.items():
                        print(f"  {k}: {before.get(k)!r} -> {v!r}")
                    data = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            out_entries.append((info.filename, data))
    if not patched:
        raise SystemExit("ERROR: __テストセレクタ が見つかりません")
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for fn, data in out_entries:
            zout.writestr(fn, data)
    print(f"\n  out : {out_path}\n  OK")


if __name__ == "__main__":
    main()
