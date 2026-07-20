# -*- coding: utf-8 -*-
"""明治安田新宿健診: generate_by_OpenAI モジュールを AzureOpenAI_Gen_Text_V1 へ置換する単発パッチ。

目的:
  ハンドメイド(VN製)の本番 .bivr 内の OpenAI 分岐モジュール(全 16 箇所)を、
  中身(プロンプト/分岐/params)を一切変えずに Azure 版モジュールへ差し替える。

理由:
  推論エンジンを OpenAI Assistant API から AzureOpenAI へ切り替える。フローの
  振る舞い(プロンプト・分岐条件・next/subs・layout)は完全に温存する要件。

対象:
  type == "drjoy^External Integration$generate_by_OpenAI"  (16 箇所)
    -> "drjoy^External Integration$AzureOpenAI_Gen_Text_V1"

ルール (中身を変えない担保):
  - JSON を round-trip せず、type フィールド文字列のみを生テキスト置換する
    （キー順・空白・エンコードを一切触らない = プロンプト/分岐は完全保存）。
  - params キーは両モジュールで完全一致（module/prompt/functionCall/promptTTS/
    contextName/contextDisplayType の 6 個）。本ファイルには addCurrentDate が
    1 箇所も無いため params の調整も不要（検証で再確認）。
  - zip エントリ名(URLエンコード済フロー名)・zip 構造は元のまま温存。

結果:
  output/明治安田新宿健診_Azure.bivr を出力（入力 .bivr は温存）。
  置換件数を検証し、16 でなければ異常終了。
"""
import sys, io, zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC_TYPE = '"type":"drjoy^External Integration$generate_by_OpenAI"'
DST_TYPE = '"type":"drjoy^External Integration$AzureOpenAI_Gen_Text_V1"'
EXPECTED = 16

HERE = Path(__file__).resolve().parent.parent
SRC = HERE / "明治安田新宿健診.bivr"
OUT = HERE / "output" / "明治安田新宿健診_Azure.bivr"


def main():
    if not SRC.exists():
        raise SystemExit(f"ERROR: 入力 .bivr が見つかりません: {SRC}")
    OUT.parent.mkdir(parents=True, exist_ok=True)

    replaced = 0
    with zipfile.ZipFile(SRC) as zin:
        infos = zin.infolist()
        with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zout:
            for info in infos:
                data = zin.read(info.filename)
                if info.filename.endswith(".txt"):
                    text = data.decode("utf-8")
                    c = text.count(SRC_TYPE)
                    if c:
                        text = text.replace(SRC_TYPE, DST_TYPE)
                        replaced += c
                    # 念のため: addCurrentDate が紛れていないか（Azure schema に無い）
                    if "addCurrentDate" in text:
                        print(f"  [WARN] addCurrentDate 検出: {info.filename}")
                    data = text.encode("utf-8")
                # 元のエントリ名でそのまま書き戻す（zip 構造温存）
                zout.writestr(info.filename, data)

    print(f"Source : {SRC}")
    print(f"Output : {OUT}")
    print(f"置換    : {replaced} 箇所 (期待 {EXPECTED})")

    if replaced != EXPECTED:
        raise SystemExit(f"ERROR: 置換件数 {replaced} != {EXPECTED}。中断。")

    # 検証: 出力に OpenAI 型が残っていない / Azure 型が 16 / それ以外は元と一致
    残OpenAI = 残Azure = 0
    with zipfile.ZipFile(OUT) as z:
        for n in z.namelist():
            if not n.endswith(".txt"):
                continue
            t = z.read(n).decode("utf-8")
            残OpenAI += t.count(SRC_TYPE)
            残Azure += t.count(DST_TYPE)
    print(f"検証    : 残 generate_by_OpenAI={残OpenAI} / AzureOpenAI_Gen_Text_V1={残Azure}")
    if 残OpenAI != 0 or 残Azure != EXPECTED:
        raise SystemExit("ERROR: 検証失敗。")
    print("OK: 変換完了。")


if __name__ == "__main__":
    main()
