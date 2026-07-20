"""
tools/raw_to_spec.py — Sheet1 CSV → 全シート自動生成エンジン

依存:
  - tools/normalize_dictionary.json  (聴取項目名 → block_type マッピング)
  - openpyxl  (pip install openpyxl — Owner 承認後。未承認時は CSV フォールバック)

使い方:
  python3 tools/raw_to_spec.py --input sheet1_input.csv --facility 中部徳洲会病院 --flow 診療

Sheet1 列:
  聴取項目名 | TTS文言 | choices (|区切り) | retry回数 | retry後遷移先 | reconfirm | amivoice_words

自動生成:
  Sheet2 (Flow E2E)  — choices から全ルートを列挙
  Sheet3 (Block)     — block_type / 入力方式 / context変数 を auto fill
  Sheet_TTS          — モジュール名 → 発話テキスト 一覧
  Sheet_AmiVoice     — step別 登録単語リスト
  Sheet_Context      — 変数名 / display_type / enum値
  Sheet_Termination  — 終話パターン (スケルトン)
  Sheet_Settings     — 施設設定 (スケルトン)
"""

import csv
import json
import re
import sys
from pathlib import Path
from itertools import product

DICT_PATH = Path(__file__).parent / "normalize_dictionary.json"


# ---------------------------------------------------------------------------
# ユーティリティ
# ---------------------------------------------------------------------------

def load_dictionary() -> tuple[list[dict], str]:
    data = json.loads(DICT_PATH.read_text(encoding="utf-8"))
    return data["items"], data["dtmf_tts_pattern"]


def normalize(item_name: str, dictionary: list[dict]) -> dict | None:
    """最長キーワード一致。一致なし → None (🔴)"""
    name = item_name.strip()
    best, best_len = None, 0
    for entry in dictionary:
        for kw in entry["keywords"]:
            if kw in name and len(kw) > best_len:
                best, best_len = entry, len(kw)
    return best


def detect_dtmf(tts_text: str, dtmf_pattern: str) -> bool:
    """TTS文言に単独数字(1-9)があれば True"""
    return bool(re.search(dtmf_pattern, tts_text))


def safe_id(name: str) -> str:
    """モジュール名用: 日本語そのまま、スペース→_"""
    return name.strip().replace(" ", "_").replace("　", "_")


# ---------------------------------------------------------------------------
# Sheet1 読み込み
# ---------------------------------------------------------------------------

def read_sheet1(csv_path: str) -> list[dict]:
    dictionary, dtmf_pattern = load_dictionary()
    rows = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["聴取項目名"].strip()
            tts  = row.get("TTS文言", "").strip()
            choices_raw = row.get("choices", "").strip()
            choices = [c.strip() for c in choices_raw.split("|") if c.strip()] if choices_raw else []
            amivoice_raw = row.get("amivoice_words", "").strip()
            amivoice = [w.strip() for w in amivoice_raw.split("|") if w.strip()] if amivoice_raw else []

            entry = normalize(name, dictionary)
            if entry is None:
                status = "🔴"
                block_type, input_mode, context_var, display_type = "UNKNOWN", "UNKNOWN", "", ""
                canonical_name, processing, processing_note, risk, output_format = name, "", "", "", ""
            else:
                status        = "🟢"
                block_type    = entry["block_type"]
                context_var   = entry.get("context_var") or ""
                display_type  = _infer_display_type(entry, choices)
                canonical_name    = entry.get("canonical_name") or name
                processing        = entry.get("processing", "")
                processing_note   = entry.get("processing_note", "")
                risk              = entry.get("risk", "")
                output_format     = entry.get("output_format", "")
                if entry.get("dtmf_force") or detect_dtmf(tts, dtmf_pattern):
                    input_mode = "DTMF+AmiVoice"
                else:
                    input_mode = entry.get("input_mode", "AmiVoice")

            rows.append({
                "name":             name,
                "canonical_name":   canonical_name,
                "tts":              tts,
                "choices":          choices,
                "retry":            row.get("retry回数", "3").strip(),
                "retry_next":       row.get("retry後遷移先", "").strip(),
                "reconfirm":        row.get("reconfirm", "なし").strip(),
                "amivoice":         amivoice,
                "block_type":       block_type,
                "input_mode":       input_mode,
                "context_var":      context_var,
                "display_type":     display_type,
                "processing":       processing,
                "processing_note":  processing_note,
                "risk":             risk,
                "output_format":    output_format,
                "status":           status,
            })

    # canonical_name の重複解消: 同じ辞書エントリに複数行がマッチすると
    # canonical_name が衝突し、scenario_flow の step が同名になって
    # 上書き事故につながる（例: 代表案内 と 通話切断ガイダンス が両方
    # 'END_代表案内' になる、連絡先番号(携帯)/(固定) が両方 '電話番号' になる 等）。
    # 2回目以降の衝突行は、辞書由来の canonical ではなく元の聴取項目名
    # （既に行ごとに一意）にフォールバックする。
    seen_canonical: dict = {}
    for r in rows:
        c = r["canonical_name"]
        if c in seen_canonical:
            r["canonical_name"] = r["name"]
        else:
            seen_canonical[c] = True
    return rows


def _infer_display_type(entry: dict, choices: list[str]) -> str:
    bt = entry.get("block_type", "")
    if bt == "dob":           return "DATE_OF_BIRTH"
    if bt == "phone":         return "PHONE_NUMBER"
    if bt == "card_number":   return "NUMBER"
    if bt == "patient_name":  return "TEXT"
    if bt == "clinical_department": return "DEPARTMENT"
    if choices:               return "CLASSIFICATION"
    return "TEXT"


# ---------------------------------------------------------------------------
# Sheet2 — E2E ルート生成
# ---------------------------------------------------------------------------

def build_routes(rows: list[dict]) -> list[list[tuple]]:
    """
    choices が複数 → 分岐点。全 E2E パスを (step名, enum値orNone) のリストで返す。
    """
    axes = []
    for row in rows:
        if len(row["choices"]) > 1:
            axes.append([(row["name"], c) for c in row["choices"]])
        else:
            axes.append([(row["name"], None)])

    return [list(combo) for combo in product(*axes)]


# ---------------------------------------------------------------------------
# 各シートデータ生成
# ---------------------------------------------------------------------------

def gen_tts_sheet(rows: list[dict]) -> list[dict]:
    """TTS一覧: モジュール名 → 発話テキスト"""
    out = []
    for row in rows:
        if not row["tts"] or row["block_type"] == "opening":
            name = f"tts_{safe_id(row['name'])}"
        else:
            name = f"tts_{safe_id(row['name'])}"

        out.append({"モジュール名": name, "発話テキスト": row["tts"],
                    "由来": "AUTO", "原資料照合✅": ""})

        if row["retry"] and int(row["retry"]) > 0 and row["tts"]:
            retry_tts = f"恐れ入りますが再度、{row['tts']}"
            out.append({"モジュール名": f"tts_{safe_id(row['name'])}_retry",
                        "発話テキスト": retry_tts, "由来": "AUTO", "原資料照合✅": ""})

        if row["reconfirm"] == "あり":
            out.append({"モジュール名": f"tts_{safe_id(row['name'])}_reconfirm",
                        "発話テキスト": f"〇〇ですね。", "由来": "AUTO(要確認)",
                        "原資料照合✅": ""})
    return out


def gen_amivoice_sheet(rows: list[dict]) -> list[dict]:
    """AmiVoice辞書: step別 登録単語"""
    out = []
    for row in rows:
        if row["input_mode"] == "none":
            continue
        words = "、".join(row["amivoice"]) if row["amivoice"] else "(未入力)"
        out.append({"StepID": safe_id(row["name"]), "登録単語": words,
                    "入力方式": row["input_mode"]})
    return out


def gen_context_sheet(rows: list[dict]) -> list[dict]:
    """Context変数: 変数名 / display_type / enum値"""
    seen = set()
    out = []
    for row in rows:
        var = row["context_var"]
        if not var or var in seen:
            continue
        seen.add(var)
        enum_vals = "|".join(row["choices"]) if row["choices"] else ""
        out.append({"変数名": var, "DisplayType": row["display_type"],
                    "enum値(|区切り)": enum_vals})
    return out


def gen_termination_sheet(rows: list[dict], route_names: list[str]) -> list[dict]:
    """Termination: 終話パターン スケルトン（ルート別に行を生成）

    ルートが複数ある場合は各ルートに対応した終話パターン行を追加。
    適用ルート列: 空=全ルート共通、コンマ区切り=該当ルートのみ
    """
    shared = [
        {"名前": "END_時間外",   "TTS": "(要記入)", "status": "6", "SMSフラグ": "-2",
         "完了フラグ": "完了フラグ_時間外", "適用ルート(コンマ区切り)": ""},
        {"名前": "END_非通知",   "TTS": "{tts_g:恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。}",
         "status": "2", "SMSフラグ": "-2", "完了フラグ": "完了フラグ_非通知",
         "適用ルート(コンマ区切り)": ""},
        {"名前": "END_聴取失敗", "TTS": "(要記入)", "status": "0", "SMSフラグ": "-2",
         "完了フラグ": "完了フラグ_聴取失敗", "適用ルート(コンマ区切り)": ""},
    ]
    if len(route_names) <= 1:
        shared.insert(0, {"名前": "END_通話完了", "TTS": "(要記入)", "status": "1", "SMSフラグ": "1",
                          "完了フラグ": "完了フラグ_通話完了", "適用ルート(コンマ区切り)": ""})
        return shared

    # 複数ルート: ルートごとに END_ 行を追加
    out = []
    for rn in route_names:
        label = rn.replace("ルート", "")
        out.append({
            "名前": f"END_{label}完了",
            "TTS": "(要記入)",
            "status": "1",
            "SMSフラグ": "1",
            "完了フラグ": f"完了フラグ_{label}完了",
            "適用ルート(コンマ区切り)": rn,
        })
    out.extend(shared)
    return out


def gen_script_sheet() -> list[dict]:
    """Sheet_Script: カスタムスクリプト挿入スケルトン

    参照ID: Sheet2 の custom_scripts1 / custom_scripts2 / custom_scripts3 の N と対応。
    スクリプト種別:
      date_calc   — 日付計算（〇日後 等）
      hours_check — 時間帯判定（祝日カレンダー等）
      custom      — その他カスタムロジック
    出力1〜5 / 次1〜5: スクリプト結果の分岐（output → next モジュール名）。空列はスキップ。
    other→次: 上記以外の結果が来た場合の next。省略時は end_failure。
    スクリプト内容: ES5 スクリプト本文（P6 受入テスト必須）。
    """
    return [
        {
            "参照ID":              "1",
            "ステップ名":          "(例) 受付日計算",
            "挿入位置(前のステップ)": "(例) 氏名",
            "スクリプト種別":      "date_calc",
            "適用ルート(コンマ区切り)": "(例) 予約ルート",
            "出力1": "OK",   "次1": "(例) 診療科",
            "出力2": "",     "次2": "",
            "出力3": "",     "次3": "",
            "出力4": "",     "次4": "",
            "出力5": "",     "次5": "",
            "other→次":     "end_failure",
            "スクリプト内容": "(要記入: ES5スクリプト本文。P6受入テスト必須)",
        },
        {
            "参照ID":              "2",
            "ステップ名":          "(例) 時間帯判定",
            "挿入位置(前のステップ)": "(例) 冒頭",
            "スクリプト種別":      "hours_check",
            "適用ルート(コンマ区切り)": "",
            "出力1": "受付時間内", "次1": "(例) 用件確認",
            "出力2": "時間外",    "次2": "(例) END_時間外",
            "出力3": "",          "次3": "",
            "出力4": "",          "次4": "",
            "出力5": "",          "次5": "",
            "other→次":     "end_failure",
            "スクリプト内容": "(要記入: ES5スクリプト本文。P6受入テスト必須)",
        },
        {
            "参照ID":              "3",
            "ステップ名":          "",
            "挿入位置(前のステップ)": "",
            "スクリプト種別":      "custom",
            "適用ルート(コンマ区切り)": "",
            "出力1": "", "次1": "",
            "出力2": "", "次2": "",
            "出力3": "", "次3": "",
            "出力4": "", "次4": "",
            "出力5": "", "次5": "",
            "other→次":     "",
            "スクリプト内容": "",
        },
    ]


def gen_settings_sheet(facility: str, flow: str) -> list[dict]:
    """Settings: 施設設定 スケルトン"""
    return [
        {"キー": "facility_name", "値": facility, "備考": "施設名"},
        {"キー": "flow_name",     "値": flow,     "備考": "フロー名"},
        {"キー": "office_id",     "値": "(要記入)", "備考": "Dr.JOY office_id"},
        {"キー": "env",           "値": "demo",    "備考": "demo / prod"},
        {"キー": "sms_enabled",   "値": "true",    "備考": "SMS送信フラグ"},
        {"キー": "business_hours","値": "(要記入)", "備考": "例: 平日 9:00-17:00"},
        {"キー": "phone_number",  "値": "(要記入)", "備考": "代表電話番号"},
        {"キー": "faq_mode",      "値": "standard",
         "備考": "standard / mismatch_tts / ari_nashi（FAQ ブロックの型。sheet_faq 使用時のみ有効）"},
        {"キー": "faq_mismatch_tts", "値": "",
         "備考": "faq_mode=mismatch_tts のみ。リスト不一致時の読み上げ文言"},
        {"キー": "faq_ari_nashi_tts", "値": "",
         "備考": "faq_mode=ari_nashi のみ。例: 他にご質問はありますか？「あり」「なし」でお答えください。"},
    ]


# ---------------------------------------------------------------------------
# CSV フォールバック出力
# ---------------------------------------------------------------------------

def _auto_route_columns(rows: list[dict]) -> tuple[list[str], dict[str, dict[str, str]]]:
    """
    choices が複数ある最初の intent/hearing/faq ステップを見つけて
    ルート列名を自動生成し、各セルのデフォルト値を返す。

    Returns:
        route_names : e.g. ["予約ルート", "変更ルート", "キャンセルルート"]
        pre_fill    : {row_name: {route_name: cell_value}}

    セル値ルール:
        "✓"             = このルートに含まれる（canonical名を使う）
        choice値 (文字列) = intent/faq/hearing ステップにおける分岐トリガー値
        "カスタム名"    = このルートに含まれるがBrekeke命名規則上の固有名を付ける
        ""              = このルートには含まれない
    """
    for row in rows:
        if len(row["choices"]) > 1 and row["block_type"] in ("intent", "hearing", "faq", "clinical_department"):
            choices = row["choices"]
            route_names = [f"{c}ルート" for c in choices]
            pre_fill: dict[str, dict[str, str]] = {}
            for r in rows:
                pre_fill[r["name"]] = {}
                if r["name"] == row["name"]:
                    # 分岐ステップ: セル値 = そのルートに入るchoice値
                    for i, c in enumerate(choices):
                        pre_fill[r["name"]][route_names[i]] = c
                elif r["block_type"] == "termination":
                    # termination は各ルートに別々に対応付ける（全ルートにデフォルト✓は不適切）
                    for rn in route_names:
                        pre_fill[r["name"]][rn] = ""  # user が設定
                else:
                    for rn in route_names:
                        pre_fill[r["name"]][rn] = "✓"
            return route_names, pre_fill

    # 分岐なし → 単一ルート
    return ["メインルート"], {r["name"]: {"メインルート": "✓"} for r in rows}


def write_csv_all(rows, routes, facility, flow, out_dir: Path):
    base = f"spec_{facility}_{flow}"
    out_dir.mkdir(parents=True, exist_ok=True)

    def _write(name, fieldnames, data):
        path = out_dir / f"{base}_{name}.csv"
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(data)
        print(f"  ✓ {path.name}")
        return path

    print(f"\n=== CSV出力 → {out_dir} ===")

    # Sheet1
    _write("Sheet1_input", [
        "聴取項目名","canonical名(auto)","TTS文言","choices","retry回数","retry後遷移先",
        "reconfirm","amivoice_words","block_type(auto)","入力方式(auto)",
        "context変数(auto)","display_type(auto)","状態"
    ], [{
        "聴取項目名": r["name"],
        "canonical名(auto)": r["canonical_name"],
        "TTS文言": r["tts"],
        "choices": "|".join(r["choices"]),
        "retry回数": r["retry"], "retry後遷移先": r["retry_next"],
        "reconfirm": r["reconfirm"],
        "amivoice_words": "|".join(r["amivoice"]),
        "block_type(auto)": r["block_type"],
        "入力方式(auto)": r["input_mode"],
        "context変数(auto)": r["context_var"],
        "display_type(auto)": r["display_type"],
        "状態": r["status"],
    } for r in rows])

    # Sheet2 — E2Eルート (縦構造・ルート列自動生成)
    # choices が複数の intent/hearing ステップから E2E ルート列を自動生成。
    # セル値ルール:
    #   ✓         = このルートに含まれる（canonical名を使う）
    #   choice値   = intent/faqの分岐トリガー（用件確認で「予約」等）
    #   カスタム名 = Brekeke命名規則上の固有名（例: 診療科_予約）
    #   空         = このルートには含まれない
    route_names, pre_fill = _auto_route_columns(rows)
    HINT_COL = "[記入方法] ✓=含む(canonical名) / choice値=分岐トリガー / カスタム名=Brekeke固有名 / 空=含まない"
    FIXED_COLS = [
        "Step(canonical)", "入力元(Sheet1)",
        "block_type", "input_mode", "output_format",
        "processing", "処理参照(自動)", "risk",
    ]
    S2_HEADERS = FIXED_COLS + route_names + [HINT_COL]
    s2_data = []
    for row in rows:
        d = {
            "Step(canonical)":  row["canonical_name"],
            "入力元(Sheet1)":   row["name"],
            "block_type":       row["block_type"],
            "input_mode":       row["input_mode"],
            "output_format":    row["output_format"],
            "processing":       row["processing"],
            "処理参照(自動)":   row["processing_note"],
            "risk":             row["risk"],
        }
        for rn in route_names:
            d[rn] = pre_fill.get(row["name"], {}).get(rn, "✓")
        d[HINT_COL] = ""
        s2_data.append(d)
    _write("Sheet2_flow", S2_HEADERS, s2_data)

    # Sheet3 — Block type + ガイド
    s3_data = [{
        "聴取項目名": r["name"],
        "block_type(auto)": r["block_type"],
        "入力方式(auto)": r["input_mode"],
        "context変数(auto)": r["context_var"],
        "調整メモ": "",
        "---": "---",
        "ブロック選択ガイド": _block_guide(i),
    } for i, r in enumerate(rows)]
    _write("Sheet3_blocktype", [
        "聴取項目名","block_type(auto)","入力方式(auto)","context変数(auto)","調整メモ",
        "---","ブロック選択ガイド"
    ], s3_data)

    # 自動生成シート
    _write("Sheet_TTS", ["モジュール名","発話テキスト","由来","原資料照合✅"], gen_tts_sheet(rows))
    _write("Sheet_AmiVoice", ["StepID","登録単語","入力方式"], gen_amivoice_sheet(rows))
    _write("Sheet_Context", ["変数名","DisplayType","enum値(|区切り)"], gen_context_sheet(rows))
    _write("Sheet_Termination",
           ["名前","TTS","status","SMSフラグ","完了フラグ","適用ルート(コンマ区切り)"],
           gen_termination_sheet(rows, route_names))
    _write("Sheet_Script",
           ["参照ID","ステップ名","挿入位置(前のステップ)","スクリプト種別","適用ルート(コンマ区切り)",
            "出力1","次1","出力2","次2","出力3","次3","出力4","次4","出力5","次5",
            "other→次","スクリプト内容"],
           gen_script_sheet())
    _write("Sheet_Settings", ["キー","値","備考"], gen_settings_sheet(facility, flow))


def _route_label(route: list[tuple]) -> str:
    vals = [v for _, v in route if v]
    return "_".join(vals) if vals else "メイン"


def _block_guide(idx: int) -> str:
    guide = [
        "用件聴取     → intent",
        "氏名聴取     → patient_name",
        "生年月日     → dob",
        "電話番号     → phone (常にDTMF)",
        "診察券番号   → card_number (常にDTMF)",
        "診療科       → clinical_department",
        "はい/いいえ  → hearing (enum2)",
        "自由発話     → free_text",
        "FAQ照合      → faq",
        "終話         → termination",
        "DTMF自動判定: TTS中に「1」「2」「3」単独 → DTMF+AmiVoice",
    ]
    return guide[idx] if idx < len(guide) else ""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Sheet1 CSV → 全シート自動生成\n\n"
                    "P1 新規作成の始め方:\n"
                    "  1. --init で入力テンプレートを配置（format 固定）\n"
                    "  2. 配置された sheet1_input.csv を Excel 等で記入\n"
                    "  3. --input で本ツールを実行 → 9 シート生成",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("--init", action="store_true",
                        help="入力テンプレート（sheet1_input.csv + 記入ガイド.md）を"
                             " output/scenarios/{施設}_{flow}/ にコピーして終了")
    parser.add_argument("--input",    default="", help="Sheet1 CSVパス（--init 時は不要）")
    parser.add_argument("--facility", default="施設名", help="施設名")
    parser.add_argument("--flow",     default="診療",  help="フロー名")
    parser.add_argument("--outdir",   default="output/spec_preview", help="出力ディレクトリ")
    args = parser.parse_args()

    if args.init:
        import shutil
        tmpl_dir = Path(__file__).resolve().parent / "spec_template"
        dest_dir = Path("output/scenarios") / f"{args.facility}_{args.flow}"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_csv = dest_dir / f"sheet1_input_{args.facility}_{args.flow}.csv"
        if dest_csv.exists():
            print(f"⚠️  既に存在します（上書きしません）: {dest_csv}")
            raise SystemExit(1)
        shutil.copy(tmpl_dir / "sheet1_input.csv", dest_csv)
        guide = tmpl_dir / "記入ガイド.md"
        if guide.exists():
            shutil.copy(guide, dest_dir / "記入ガイド.md")
        # 任意シート: 診療科リスト / FAQ リスト（不要なら削除してよい）
        optional = []
        for tmpl_name, label in (("sheet_department.csv", "診療科リスト"),
                                 ("sheet_faq.csv", "FAQリスト")):
            src_t = tmpl_dir / tmpl_name
            if src_t.exists():
                dst = dest_dir / f"{tmpl_name[:-4]}_{args.facility}_{args.flow}.csv"
                if not dst.exists():
                    shutil.copy(src_t, dst)
                optional.append((label, dst))
        print(f"✓ テンプレート配置: {dest_csv}")
        print(f"✓ 記入ガイド:       {dest_dir / '記入ガイド.md'}")
        for label, dst in optional:
            print(f"✓ {label}（任意・不要なら削除）: {dst}")
        print(f"\n次のステップ:")
        print(f"  1. {dest_csv} を Excel / Google シートで開いて記入（記入ガイド.md 参照）")
        print(f"  2. python3 tools/raw_to_spec.py --input {dest_csv} \\")
        print(f"         --facility {args.facility} --flow {args.flow} --outdir {dest_dir}")
        raise SystemExit(0)

    if not args.input:
        parser.error("--input は必須です（テンプレート配置は --init を使用）")

    rows = read_sheet1(args.input)
    routes = build_routes(rows)

    print("=== normalize 結果 ===")
    for r in rows:
        dtmf_mark = " [DTMF]" if r["input_mode"] == "DTMF+AmiVoice" else ""
        print(f"  {r['status']} {r['name']:20s} → {r['block_type']:25s}{dtmf_mark}")

    unknown = [r for r in rows if r["status"] == "🔴"]
    if unknown:
        print(f"\n⚠️  未知の項目 {len(unknown)}件 — 辞書への追加が必要:")
        for r in unknown:
            print(f"  🔴 {r['name']}")

    print(f"\n=== E2Eルート ({len(routes)}本) ===")
    for i, route in enumerate(routes):
        path = " → ".join(f"{n}({v})" if v else n for n, v in route)
        print(f"  Route {i+1}: {path}")

    write_csv_all(rows, routes, args.facility, args.flow, Path(args.outdir))
    print("\n完了。Googleシート / Excel にインポートして確認してください。")
