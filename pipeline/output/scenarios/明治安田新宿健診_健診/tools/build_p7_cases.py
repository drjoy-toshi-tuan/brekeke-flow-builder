# -*- coding: utf-8 -*-
"""明治安田新宿健診: Pattern 7（連結テスト）ケース表 JSON を生成する。

このフローは設計書 YAML が無い VN ハンドメイド bivr のため、gen_p7_cases.py
（YAML→ケース）は使えない。代わりにフローグラフ（work/graph.txt）から読み取った
分岐を手動でケース化する。出力 JSON はそのまま
  - connection_test/stub_stt_connection.py の --cases（STTスタブ生成）
  - gen_p7_cases.py --to-csv（人間記入用 CSV 書き出し）
の両方に渡せる形式（cases / defaults / meta / selector）。

フロー要点（call path）:
  Main: 冒頭待ち→営業時間チェック→着信電話番号_判定(分類)
        →(固定/携帯)冒頭アナウンス→jump-個人[患者名/生年月日/電話番号を先に聴取]
        →折り返し案内→用件(STT)→用件分類→用件_分岐(CMR 1/2/3/4)
        →jump-予約/変更/キャンセル/FAQ→終話_分岐→通話完了
        (非通知/海外/WebRTC → 時間外切断 で着信拒否)

defaults は「テスト対象でない全 STT ノード」を最短完走させる既定注入。
_order は部分文字列衝突回避のため長い／具体的なキーを先に並べる
（def_for は _order を上から見て node 名に含まれる最初のキーの値を使う）。

expect は下書き（connection_test/REQUIREMENTS.md の方針どおり、実機ゴールデンログ
観察後に人間が確定させる）。終端はほぼ「通話完了」(Reject) で、差分はルート checkpoints。
"""
import sys, io, json, zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = Path(__file__).resolve().parent.parent
BIVR = HERE / "output" / "明治安田新宿健診_Azure.bivr"
OUT = HERE / "output" / "明治安田新宿健診_連結テスト_cases.json"

ENTRY_FLOW = "Main｜健診"

# ---- defaults: テスト対象外ノードの最短完走注入 -----------------------------
# キーは _order の順（長い/具体的を先に）。値は attempt 順の配列。
DEFAULTS = {
    "_order": [
        "復唱生年月日西暦", "復唱生年月日",        # 個人: 西暦/和暦の復唱(はい)
        "確認_現在の予約日", "確認_キャンセル理由",  # キャンセル
        "連絡先番号_携帯確認", "復唱_電話番号",      # 個人: 電話確認
        "最後の問い合わせ",                          # FAQ
        "変更内容", "現在の予約日",                   # 変更
        "追加オプション", "希望コース", "希望日程",   # 予約
        "連絡先番号", "生年月日", "患者名",          # 個人: DTMF/氏名
        "その他", "用件",                            # FAQ補助 / 用件
    ],
    "復唱生年月日西暦": ["はい"],
    "復唱生年月日": ["はい"],
    "確認_現在の予約日": ["10月1日"],
    "確認_キャンセル理由": ["都合が悪くなったため"],
    "連絡先番号_携帯確認": ["はい"],
    "復唱_電話番号": ["はい"],
    "最後の問い合わせ": ["特にありません"],
    "変更内容": ["日付を変更したいです"],
    "現在の予約日": ["10月1日"],
    "追加オプション": ["オプションはありません"],
    "希望コース": ["日帰りコース"],
    "希望日程": ["10月1日"],
    "連絡先番号": ["09012345678"],
    "生年月日": ["19800101"],
    "患者名": ["やまだ たろう"],
    "その他": ["特にありません"],
    "用件": ["健診の予約"],
    "_fallback": ["NO_RESULT"],
}

# ---- cases ------------------------------------------------------------------
# 各 case: (covers説明, inject{node:[seq]}, 終端, [checkpoints])
RAW = [
    # ---- A: 用件分類（Main: OpenAi_入力用件 → 用件_分岐 CMR） ----
    ("用件=健診の予約 → 予約サブフロー → 通話完了",
     {"入力_用件": ["健診の予約"]}, "通話完了",
     ["用件分類:健診の予約", "用件_分岐 ^1$→jump-予約", "予約完走→終話_分岐 ^1$"]),
    ("用件=予約の変更 → 変更サブフロー → 通話完了",
     {"入力_用件": ["予約の変更"]}, "通話完了",
     ["用件分類:予約の変更", "用件_分岐 ^2$→Jump-変更", "終話_分岐 ^2$"]),
    ("用件=予約のキャンセル → キャンセルサブフロー → 終話④ → 通話完了",
     {"入力_用件": ["予約のキャンセル"]}, "通話完了",
     ["用件分類:予約のキャンセル", "用件_分岐 ^3$→jump-キャンセル", "終話_分岐 ^3$→status-終話④"]),
    ("用件=その他お問い合わせ → FAQサブフロー → 問い合わせ_分岐 → 通話完了",
     {"入力_用件": ["その他お問い合わせ"]}, "通話完了",
     ["用件分類:その他お問い合わせ", "用件_分岐 ^4$→jump-FAQ", "終話_分岐 ^4$→問い合わせ_分岐"]),
    ("用件 NO_RESULT→1回リトライで復帰（リトライ_入力用件 true / save-不明1）",
     {"入力_用件": ["NO_RESULT", "健診の予約"]}, "通話完了",
     ["OpenAi_入力用件 NO_RESULT→save-不明1", "リトライ_入力用件 true→用件", "2回目=健診の予約"]),
    ("用件 NO_RESULT 連続→リトライ枯渇（リトライ_入力用件 false → save-不明 → 時間外切断）",
     {"入力_用件": ["NO_RESULT"]}, "時間外切断",
     ["OpenAi_入力用件 NO_RESULT 反復", "リトライ_入力用件 false→save-不明", "時間外切断(Reject)"]),

    # ---- B: 個人サブフロー 生年月日（個人は全コール先頭で実行される） ----
    ("生年月日=西暦8桁 → 判定WESTERN → 西暦復唱(はい) → 着信番号分類",
     {"入力_生年月日": ["19851231"], "入力_復唱生年月日西暦": ["はい"]}, "通話完了",
     ["OpenAI_生年月日→日付正規化", "OpenAI_生年月日判定 WESTERN→復唱生年月日_西暦",
      "OpenAI_入力_復唱生年月日和暦 はい→着信番号分類"]),
    ("生年月日=和暦 → 判定JAPANESE → 和暦復唱(はい) → 着信番号分類",
     {"入力_生年月日": ["昭和60年5月3日"], "入力_復唱生年月日": ["はい"]}, "通話完了",
     ["OpenAI_生年月日判定 JAPANESE→復唱生年月日", "OpenAI_復唱生年月日 はい→着信番号分類"]),
    ("生年月日 復唱=いいえ→再聴取→2回目はい（OpenAI_入力_復唱生年月日和暦 いいえ）",
     {"入力_復唱生年月日西暦": ["いいえ", "はい"]}, "通話完了",
     ["復唱(西暦) いいえ→生年月日 再聴取", "再聴取後 復唱=はい→着信番号分類"]),
    ("生年月日 NO_RESULT→リトライ→2回目で復帰（OpenAI_生年月日 NO_RESULT）",
     {"入力_生年月日": ["NO_RESULT", "19800101"]}, "通話完了",
     ["OpenAI_生年月日 NO_RESULT→リトライ_生年月日", "2回目=19800101→判定へ"]),

    # ---- C: 個人サブフロー 連絡先電話番号 ----
    ("電話番号 携帯確認=はい → 連絡先番号_確認 OK → 電話番号_判定②（既定経路の明示確認）",
     {"入力_連絡先番号_携帯確認": ["はい"]}, "通話完了",
     ["連絡先番号_確認 OK→電話番号_判定②", "Scripts-個人→個人完走"]),
    ("電話番号 携帯確認=いいえ → 連絡先番号_確認 NG → DTMF再入力 → 復唱OK",
     {"入力_連絡先番号_携帯確認": ["いいえ"], "入力_連絡先番号": ["09012345678"],
      "入力_復唱_電話番号": ["はい"]}, "通話完了",
     ["連絡先番号_確認 NG→連絡先番号", "入力_連絡先番号(DTMF)→Scripts-電話番号",
      "OpenAI_復唱_電話番号 OK→電話番号_判定②"]),

    # ---- D: 予約サブフロー（用件=健診の予約 起点） ----
    ("予約: 希望コース NO_RESULT→リトライ復帰（OpenAI_希望コース NO_RESULT/save-不明）",
     {"入力_用件": ["健診の予約"], "入力_希望コース": ["NO_RESULT", "日帰りコース"]}, "通話完了",
     ["OpenAI_希望コース NO_RESULT→save-不明→リトライ_受診内容②", "2回目=日帰りコース→追加オプション"]),
    ("予約: 追加オプション NO_RESULT→リトライ復帰（入力_VALID NO_RESULT/save-不明③）",
     {"入力_用件": ["健診の予約"], "入力_追加オプション": ["NO_RESULT", "オプションはありません"]}, "通話完了",
     ["入力_追加オプション NO_RESULT→save-不明③→リトライ_追加オプション", "2回目→入力_VALID VALID→希望日程"]),
    ("予約: 希望日程 NO_RESULT→リトライ復帰（OpenAI_希望日程 NO_RESULT/save-不明②）",
     {"入力_用件": ["健診の予約"], "入力_希望日程": ["NO_RESULT", "10月1日"]}, "通話完了",
     ["OpenAI_希望日程 NO_RESULT→save-不明②→リトライ_希望日程", "2回目=10月1日→予約完走"]),

    # ---- E: 変更サブフロー（用件=予約の変更 起点） ----
    ("変更: 現在の予約日(日付)→変更内容①(VALID) 正常完走",
     {"入力_用件": ["予約の変更"], "入力_現在の予約日": ["10月1日"],
      "入力_変更内容①": ["日付を変更したいです"]}, "通話完了",
     ["OpenAI_現在の予約日→日付正規化→変更内容①", "OpenAI_入力_変更内容① VALID→完走"]),
    ("変更: 現在の予約日 NO_RESULT→リトライ復帰（save-不明）",
     {"入力_用件": ["予約の変更"], "入力_現在の予約日": ["NO_RESULT", "10月1日"]}, "通話完了",
     ["OpenAI_現在の予約日 NO_RESULT→save-不明→リトライ_現在の予約日", "2回目=10月1日"]),
    ("変更: 現在の予約日=非日付→正規表現外れ→リトライ（^(?!日付)$ ブランチ）",
     {"入力_用件": ["予約の変更"], "入力_現在の予約日": ["わかりません", "10月1日"]}, "通話完了",
     ["OpenAI_現在の予約日 非日付出力→リトライ_現在の予約日", "2回目=10月1日→変更内容①"]),
    ("変更: 変更内容① NO_RESULT→リトライ復帰（save-不明②）",
     {"入力_用件": ["予約の変更"], "入力_現在の予約日": ["10月1日"],
      "入力_変更内容①": ["NO_RESULT", "日付を変更したいです"]}, "通話完了",
     ["入力_変更内容① NO_RESULT→save-不明②→リトライ_変更内容①", "2回目→VALID完走"]),

    # ---- F: キャンセルサブフロー（用件=予約のキャンセル 起点） ----
    ("キャンセル: 現在の予約日(日付)→キャンセル理由 正常完走",
     {"入力_用件": ["予約のキャンセル"], "入力_確認_現在の予約日": ["10月1日"],
      "入力_確認_キャンセル理由": ["都合が悪くなったため"]}, "通話完了",
     ["openAI_確認_現在の予約日→確認_キャンセル理由", "openAI_確認_キャンセル理由 ノイズ除去→完走"]),
    ("キャンセル: 確認_現在の予約日 NO_RESULT→リトライ復帰（save-不明）",
     {"入力_用件": ["予約のキャンセル"], "入力_確認_現在の予約日": ["NO_RESULT", "10月1日"]}, "通話完了",
     ["openAI_確認_現在の予約日 NO_RESULT→save-不明→リトライ", "2回目=10月1日"]),
    ("キャンセル: キャンセル理由 NO_RESULT→リトライ復帰（save-不明③）",
     {"入力_用件": ["予約のキャンセル"], "入力_確認_キャンセル理由": ["NO_RESULT", "都合が悪くなったため"]}, "通話完了",
     ["openAI_確認_キャンセル理由 NO_RESULT→save-不明③→リトライ", "2回目で復帰"]),

    # ---- G: FAQサブフロー（用件=その他お問い合わせ 起点） ----
    ("FAQ: 最後の問い合わせ=質問あり → 要対応 → RAG（FAQ_モジュール）",
     {"入力_用件": ["その他お問い合わせ"], "入力_最後の問い合わせ_携帯以外": ["駐車場はありますか"]}, "通話完了",
     ["OpenAI_問い合わせ内容判定 要対応→FAQ_モジュール(RAG)", "Scripts-FAQ成功→問い合わせ完走"]),
    ("FAQ: 最後の問い合わせ=質問なし → 対応不要 → Scripts-問い合わせ",
     {"入力_用件": ["その他お問い合わせ"], "入力_最後の問い合わせ_携帯以外": ["特にありません"]}, "通話完了",
     ["OpenAI_問い合わせ内容判定 対応不要→Scripts-問い合わせ", "save-問い合わせ内容→完走"]),
    ("FAQ: 最後の問い合わせ NO_RESULT→リトライ復帰",
     {"入力_用件": ["その他お問い合わせ"], "入力_最後の問い合わせ_携帯以外": ["NO_RESULT", "特にありません"]}, "通話完了",
     ["OpenAI_問い合わせ内容判定 NO_RESULT→リトライ_最後の問い合わせ_携帯以外", "2回目で復帰"]),

    # ---- H: 着信種別分類（Main: 着信電話番号_判定 incoming-classifier） ----
    # ※ 1件でも分類器ノードを inject すると全コールで分類器がスタブ化される。
    #   分類器を inject しないケースは既定で「携帯」ルート（実機 ANI 相当）を通る＝回帰なし。
    ("着信種別=非通知 → 着信拒否（save-非通知→非通知→時間外切断）",
     {"着信電話番号_判定": ["非通知"]}, "時間外切断",
     ["着信電話番号_判定 ^非通知$→save-非通知", "非通知→時間外切断(Reject)"]),
    ("着信種別=固定 → 通常受付（冒頭アナウンス→個人→用件→予約）",
     {"着信電話番号_判定": ["固定"], "入力_用件": ["健診の予約"]}, "通話完了",
     ["着信電話番号_判定 ^固定$→冒頭アナウンス", "通常フロー完走"]),
]


def main():
    if not BIVR.exists():
        raise SystemExit(f"ERROR: Azure bivr が無い。先に convert_openai_to_azure.py を実行: {BIVR}")

    # bivr 内の全 STT ノード名（スタブ対象）を収集
    STT_TYPES = ("drjoy^AmiVoice$Speech to Text", "drjoy^External Integration$DTMF AmiVoice STT Input")
    CLS_TYPE = "drjoy^Incoming$incoming-classifier"
    stt_nodes, cls_nodes = set(), set()
    with zipfile.ZipFile(BIVR) as z:
        for n in z.namelist():
            d = json.loads(z.read(n).decode("utf-8"))
            for mn, m in d.get("modules", {}).items():
                if m.get("type") in STT_TYPES:
                    stt_nodes.add(mn)
                elif m.get("type") == CLS_TYPE:
                    cls_nodes.add(mn)

    # 検証1: defaults._order が全 STT ノードを被覆（_fallback 落ち=意図せぬ NO_RESULT を防ぐ）
    def matched(node):
        return any(kw in node for kw in DEFAULTS["_order"])
    uncovered = sorted(n for n in stt_nodes if not matched(n))
    if uncovered:
        raise SystemExit(f"ERROR: defaults._order で被覆できない STT ノード: {uncovered}")

    # 検証2: 各 case の inject ノードが実在（STT または incoming-classifier）
    valid_inject = stt_nodes | cls_nodes
    cases = []
    for i, (covers, inject, term, checks) in enumerate(RAW, 1):
        for node in inject:
            if node not in valid_inject:
                raise SystemExit(f"ERROR: case{i} inject 先 '{node}' が bivr に存在しない")
        cases.append({
            "id": str(i), "dtmf": str(i),
            "inject": inject,
            "expect": {"終端": term, "checkpoints": checks},
            "covers": [covers],
        })

    out = {
        "_about": ("連結(実機統合)テスト ケース表。STTを定数注入し本番フロー(Azure版)を実機"
                   "ハンズフリー実行する。冒頭で DTMF ケース番号を選択。inject値は配列=試行回数"
                   "依存(attempt-aware)。expect は下書き=実機ゴールデンログ観察後に人間が確定。"),
        "meta": {
            "facility": "明治安田新宿健診", "flow": "Main｜健診",
            "entry_flow": ENTRY_FLOW,
            "engine": "AzureOpenAI_Gen_Text_V1 へ置換後の bivr に対する連結テスト",
            "source_bivr": "明治安田新宿健診_Azure.bivr",
            "generated_by": "tools/build_p7_cases.py",
        },
        "selector": {"context": "__tc_id", "module": "__テストセレクタ", "usage": "発信→ケース番号+#"},
        "defaults": DEFAULTS,
        "cases": cases,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"STT ノード(スタブ対象): {len(stt_nodes)}  / 分類器ノード: {sorted(cls_nodes)}")
    print(f"ケース数: {len(cases)}")
    print(f"出力: {OUT}")


if __name__ == "__main__":
    main()
