#!/usr/bin/env python3
"""
gen_properties.py — Brekeke IVR プロパティファイルをスクリプトで生成する

scaffold_tts サイドカー + 設計書 YAML から全 TTS プロパティ行を機械的に解決し、
サブフロー TTS テンプレートおよび環境設定テンプレートと結合して .md ファイルを出力する。

LLM 不使用。完全決定論的。

Usage:
    python3 scripts/gen_properties.py <yaml_spec_path> [--env demo|prod] [--out <output_path>]
"""

import argparse
import json
import re
import sys
from pathlib import Path

# DTMF タグ除去用正規表現
# customer_doc に旧 OpenAI Assistant 仕様の `<dtmf/>` `<dtmf2 digit="N"/>` タグが
# 含まれていることがあるが、Brekeke + Google TTS は処理しないため
# そのまま読み上げられてしまう。DTMF 入力受付は STT モジュールの dtmf_max_length /
# termdtmf 側で表現済みなので、TTS テキストからは除去する。
# `<speak type="telephone"...>` は別ルール（電話番号復唱で SSML 例外として保持）
# のため除去対象外。
_DTMF_TAG_RE = re.compile(r"\s*<\s*dtmf2?\b[^>]*/?>\s*", re.IGNORECASE)


def strip_dtmf_tags(text: str) -> str:
    """TTS テキストから <dtmf/> <dtmf2 digit="N"/> 等のタグを除去する。

    末尾の余計な空白も併せて整える。<speak> タグは対象外。
    """
    if not text:
        return text
    cleaned = _DTMF_TAG_RE.sub("", text)
    return cleaned.rstrip()


def strip_tts_wrapper(text: str) -> str:
    """先頭に直書きされた {tts_g:...} / {tts_ai:...} ラッパーを剥がす（冪等化）。

    gen_properties は必ず {tts_g:{text}} で 1 枚ラップするため、director が
    tts_announcement にラッパーを直書きしたり、サイドカーが既にラップ済みだと
    {tts_g:{tts_g:...}} と二重化する。ここで巻く前に既存ラッパーを全段剥がしておく。
    ラッパーが無ければ素通し。
    """
    if not text:
        return text
    t = text.strip()
    changed = True
    while changed:
        changed = False
        for pref in ("{tts_g:", "{tts_ai:", "{TTS_AI:"):
            if t.startswith(pref) and t.endswith("}"):
                t = t[len(pref):-1].strip()
                changed = True
                break
    return t

# Windows 環境で UTF-8 出力を強制
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ──────────────────────────────────────────────────────────────────────────
# 標準END系モジュールのデフォルト発話（施設依存しない汎用文言）
#
# director が yaml に書き忘れても、gen_properties がここから埋める。
# 施設固有の文言がある場合は yaml の tts_modules で上書き可能（resolve_tts_texts
# が優先してそちらを採用）。
#
# 命名揺れ対策: scaffold 側の命名（END_非通知）と yaml 慣習（非通知_アナウンス）
# の両方をキーとして登録する。
# ──────────────────────────────────────────────────────────────────────────

# 予約系完了デフォルト（新規/変更/キャンセル/確認/当日/企業 の各完了共通）
_DEFAULT_RESERVATION_COMPLETE = (
    "お申し込みを受け付けました。"
    "3営業日以内に担当者より折り返しのお電話、もしくはショートメールにてご連絡いたします。"
    "お電話ありがとうございました。それでは失礼いたします。"
)

# 受付不可／別窓口案内デフォルト（インフル・コロナ・予防接種・各種受付終了系）
_DEFAULT_CANNOT_ACCEPT = (
    "大変申し訳ございませんが、このお電話ではこちらのご用件は受け付けできません。"
    "お手数をおかけいたしますが、代表電話にお掛け直しください。"
    "それでは失礼いたします。"
)

STANDARD_TTS_DEFAULTS: dict[str, str] = {
    # ── システム系エラー終話 ─────────────────────────────────
    "END_非通知":
        "大変申し訳ございません。現在、非通知番号からの受付をしておりません。"
        "恐れ入りますが、発信者番号を通知してお掛け直しください。"
        "それでは失礼いたします。",
    "非通知_アナウンス":
        "大変申し訳ございません。現在、非通知番号からの受付をしておりません。"
        "恐れ入りますが、発信者番号を通知してお掛け直しください。"
        "それでは失礼いたします。",
    # END_時間外 / 時間外_アナウンス は acceptance_times モジュール内で TTS を再生するため削除（2026-07-09）
    "END_聴取失敗":
        "何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。"
        "恐れ入りますが、改めておかけ直しください。"
        "それでは失礼いたします。",
    "聴取失敗_アナウンス":
        "何度かお聞き取りを試みましたが、難しかったためお電話を終了いたします。"
        "恐れ入りますが、改めておかけ直しください。"
        "それでは失礼いたします。",
    "終話_失敗":
        "誠に申し訳ございません。何度かお聞き取りを試みましたが難しかったため、"
        "お電話を終了いたします。それでは失礼いたします。",

    # ── 予約系完了（施設固有文言があれば yaml で上書き） ────
    "END_予約完了":         _DEFAULT_RESERVATION_COMPLETE,
    "END_予約完了_単一":    _DEFAULT_RESERVATION_COMPLETE,
    "END_予約完了_複数":    _DEFAULT_RESERVATION_COMPLETE,
    "END_新規完了":         _DEFAULT_RESERVATION_COMPLETE,
    "END_変更完了":         _DEFAULT_RESERVATION_COMPLETE,
    "END_キャンセル完了":   _DEFAULT_RESERVATION_COMPLETE,
    "END_キャンセル完了_単一": _DEFAULT_RESERVATION_COMPLETE,
    "END_キャンセル完了_複数": _DEFAULT_RESERVATION_COMPLETE,
    "END_確認完了":         _DEFAULT_RESERVATION_COMPLETE,
    "END_当日完了":         _DEFAULT_RESERVATION_COMPLETE,
    "END_企業完了":         _DEFAULT_RESERVATION_COMPLETE,

    # ── 受付不可／別窓口案内（症状別終了、診療科受付終了等）───
    "END_インフルエンザ":        _DEFAULT_CANNOT_ACCEPT,
    "END_コロナ":                _DEFAULT_CANNOT_ACCEPT,
    "END_予防接種":              _DEFAULT_CANNOT_ACCEPT,
    "END_ワクチン":              _DEFAULT_CANNOT_ACCEPT,
    "END_皮膚科案内":            _DEFAULT_CANNOT_ACCEPT,
    "END_受付不可":              _DEFAULT_CANNOT_ACCEPT,
    "END_受付不可診療科":        _DEFAULT_CANNOT_ACCEPT,
    "END_当日予約不可":          _DEFAULT_CANNOT_ACCEPT,
    "END_他院案内":              _DEFAULT_CANNOT_ACCEPT,
}


# 個人情報4種（slot: patient_name/date_of_birth/phone/card_number）の主要TTSに対する
# 書き忘れ救済用デフォルト文言。scaffold_generator.py の build_tts() はこれらのモジュールで
# params.prompt を空欄のまま出力するため（TTS発話文言はプロパティ側で定義する前提・CLAUDE.md）、
# 設計書 YAML に director が個別の tts_modules/step_details を書かなかった場合、
# ここで解決されなければ properties に "TODO_発話内容を記入" が literal に出力され、
# 気付かれないまま本番投入されるリスクがある（qa_validator.py の TTS-COVERAGE チェック参照）。
# slot phone v2（docs/specs/slot_phone_v2.md）: 電話番号の復唱は素の TTS ノード + オブジェクト参照に
# 統一され、文言はすべてプロパティ側で定義する（DOB Re-confirmation / 診察券番号復唱は従来どおり
# scaffold 埋め込み）。
_SLOT_TTS_DEFAULTS = {
    "patient_name":   "受診される方のお名前を、フルネームでお話しください。",
    "date_of_birth":  "受診される方の生年月日を、西暦でお話しいただくか、ダイヤルプッシュで入力してください。",
    "phone_contact":  "日中、ご連絡の取れるお電話番号を、市外局番からダイヤルプッシュで入力してください。",
    "card_number":    "診察券番号を、ダイヤルプッシュで入力してください。",
}

# slot phone v2 の復唱 TTS デフォルト文言。
# GOOGLE: <%additionalPhoneNumber%>（CASE A/B とも setObject される統一参照）+ SSML say-as telephone。
# AI_TALK: SSML 非対応 — ANI 路は整形済み <%incoming_phone%>（CASE B が setObject）を読む。
#          連絡先路/サルベージ（CASE A）は外部 TTS を挟まず module prompt（#data#）で読む
#          （_phone_norm_prompt_lines が module prompt のプロパティ行を出力する）。
_PHONE_RECONF_GOOGLE_ANI = (
    "ご連絡先の電話番号は、今おかけいただいている、"
    "<speak><say-as interpret-as=\"telephone\"><%additionalPhoneNumber%></say-as></speak>、"
    "でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。"
)
_PHONE_RECONF_GOOGLE = (
    "ご連絡先の電話番号は、"
    "<speak><say-as interpret-as=\"telephone\"><%additionalPhoneNumber%></say-as></speak>、"
    "でよろしいですか？「はい、そうです」もしくは「いいえ、違います」でお答えください。"
)
_PHONE_RECONF_AI_ANI = (
    "ご連絡先の電話番号は、今おかけいただいている、<%incoming_phone%>、でよろしいですか？"
    "「はい、そうです」もしくは「いいえ、違います」でお答えください。"
)
_PHONE_NORM_PROMPT_AI = (
    "ご連絡先の電話番号は、#data#、でよろしいですか？"
    "「はい、そうです」もしくは「いいえ、違います」でお答えください。"
)


def _phone_slot_steps(spec_data: dict) -> list[str]:
    """scenario_flow から slot phone の step 名を列挙する。"""
    steps: list[str] = []
    for block in spec_data.get("scenario_flow", []) or []:
        btype = block.get("type", "")
        step = block.get("step", "")
        if not step:
            continue
        slot_kind = block.get("slot", "") if btype == "slot" else _SLOT_KIND_BY_TYPE.get(btype, "")
        if slot_kind == "phone":
            steps.append(step)
    return steps


def build_phone_norm_prompt_lines(spec_data: dict, tts_wrap: str) -> list[str]:
    """AI_TALK 施設のみ: CASE A の Phone Normalization に module prompt を
    プロパティで与える行を返す（#data# は module 内部変数のため module prompt でしか読めない）。
    GOOGLE 施設は空リスト（module prompt は空のまま・外部 TTS が読む）。"""
    if tts_wrap != "tts_ai":
        return []
    lines: list[str] = []
    for step in _phone_slot_steps(spec_data):
        for mod in (f"正規化_{step}_連絡先", f"正規化_{step}_連絡先言い直し",
                    f"正規化_{step}_ANI言い直し"):
            lines.append(f"{mod}.prompt={{tts_ai:{_PHONE_NORM_PROMPT_AI}}}")
    return lines

# type: slot の slot 値 → デフォルト種別。ファーストクラスエイリアス（dob/phone/patient_name/
# card_number を type に直接指定するケース）も同じ種別にマッピングする。
_SLOT_KIND_BY_TYPE = {
    "dob": "date_of_birth",
    "phone": "phone",
    "patient_name": "patient_name",
    "card_number": "card_number",
}


def resolve_slot_tts_defaults(spec_data: dict) -> dict[str, str]:
    """scenario_flow から個人情報4種の slot ブロックを検出し、書き忘れ救済用デフォルト文言を
    実際の step 名（director が書いた名前。固定文字列ではない）にひも付けて返す。
    施設固有の文言は tts_modules/step_details で上書きされる（resolve_tts_texts 側で優先）。
    """
    defaults: dict[str, str] = {}
    for block in spec_data.get("scenario_flow", []) or []:
        btype = block.get("type", "")
        step = block.get("step", "")
        if not step:
            continue
        if btype == "slot":
            slot_kind = block.get("slot", "")
        else:
            slot_kind = _SLOT_KIND_BY_TYPE.get(btype, "")
        if slot_kind == "phone":
            defaults[f"聴取_{step}_連絡先"] = _SLOT_TTS_DEFAULTS["phone_contact"]
            # slot phone v2: 復唱 TTS ノード（プロパティ管理）。AI_TALK の連絡先路/サルベージは
            # 外部 TTS ノード自体が生成されない（module prompt 読み）ため ANI のみ。
            ai_talk = (spec_data.get("basic_info", {}).get("tts_platform") or "GOOGLE").upper() == "AI_TALK"
            if ai_talk:
                defaults[f"復唱_{step}_ANI"] = _PHONE_RECONF_AI_ANI
            else:
                defaults[f"復唱_{step}_ANI"] = _PHONE_RECONF_GOOGLE_ANI
                defaults[f"復唱_{step}_連絡先"] = _PHONE_RECONF_GOOGLE
                defaults[f"復唱_{step}_ANI言い直し"] = _PHONE_RECONF_GOOGLE
                defaults[f"復唱_{step}_連絡先言い直し"] = _PHONE_RECONF_GOOGLE
        elif slot_kind in ("patient_name", "date_of_birth", "card_number"):
            defaults[step] = _SLOT_TTS_DEFAULTS[slot_kind]
    return defaults


def resolve_tts_texts(spec_data: dict) -> dict[str, str]:
    """設計書 YAML から TTS テキストを解決する。
    優先順位: tts_modules > step_details > slot系デフォルト(個人情報4種) > STANDARD_TTS_DEFAULTS
    施設固有の文言は yaml で上書き可能。standard defaults は書き忘れ救済用。
    """
    texts: dict[str, str] = {}
    for tm in spec_data.get("tts_modules", []):
        name = tm.get("module_name", "")
        text = tm.get("announcement", "") or tm.get("text", "")
        if name and text:
            texts[name] = text
    for sd in spec_data.get("step_details", []):
        name = sd.get("step_name", "")
        text = sd.get("tts_announcement", "")
        if name and text and name not in texts:
            texts[name] = text
    # 個人情報4種の slot デフォルト（yaml で定義されていない場合のみ適用）
    for name, default_text in resolve_slot_tts_defaults(spec_data).items():
        if name not in texts:
            texts[name] = default_text
    # 標準END系デフォルト（yaml で定義されていない場合のみ適用）
    for name, default_text in STANDARD_TTS_DEFAULTS.items():
        if name not in texts:
            texts[name] = default_text
    return texts


def build_tts_lines(
    tts_module_names: list[str],
    tts_texts: dict[str, str],
    wrap: str = "tts_g",
) -> tuple[list[str], list[str]]:
    """TTS プロパティ行リストと TODO モジュールリストを返す。
    wrap = ラッパー識別子（AI_TALK 施設は "tts_ai"、それ以外は "tts_g"）。"""
    lines: list[str] = []
    todo: list[str] = []
    for name in tts_module_names:
        text = tts_texts.get(name, "")
        if text:
            text = strip_tts_wrapper(strip_dtmf_tags(text))
            lines.append(f"{name}.prompt={{{wrap}:{text}}}")
        else:
            lines.append(f"{name}.prompt={{{wrap}:TODO_発話内容を記入}}")
            todo.append(name)
    return lines, todo


def build_subflow_tts_lines(
    spec_data: dict,
    tts_texts: dict[str, str],
    templates_path: Path,
    wrap: str = "tts_g",
) -> tuple[list[str], list[str]]:
    """サブフロー用 TTS プロパティ行リストと TODO モジュールリストを返す。

    サブフロー種別の判定は flowname（`施設名$サブフロー名` 形式）の `$` 以降の
    ブロック識別子で行う。step 名の命名揺れ（jump_氏名聴取 / jump_共通_氏名 /
    jump_予約変更_診察券番号 等）に左右されない。

    フォールバック: flowname 不在時のみ step 部分一致（旧挙動）。
    """
    if not templates_path.exists():
        return [], []

    templates = json.loads(templates_path.read_text(encoding="utf-8"))
    template_list = templates.get("subflows", [])

    lines: list[str] = []
    todo: list[str] = []
    seen: set[str] = set()  # 同じサブフロー型が複数あっても重複出力しない

    for block in spec_data.get("scenario_flow", []):
        if block.get("type") != "subflow":
            continue
        flowname = block.get("flowname", "") or ""
        step = block.get("step", "") or ""
        # flowname から サブフロー識別子を抽出（`施設名$氏名聴取` → `氏名聴取`）
        subflow_id = flowname.split("$", 1)[1] if "$" in flowname else flowname
        for tmpl in template_list:
            keyword = tmpl.get("match_keyword", "")
            if not keyword or keyword in seen:
                continue
            # 優先: flowname 識別子に keyword が含まれる（ブロック単位判定）
            # フォールバック: step 名に keyword が含まれる（旧挙動、flowname 無い場合用）
            if keyword in subflow_id or (not subflow_id and keyword in step):
                seen.add(keyword)
                default_texts = tmpl.get("default_texts", {})
                for mod_name in tmpl.get("required_tts", []):
                    text = tts_texts.get(mod_name, "") or default_texts.get(mod_name, "")
                    if text:
                        text = strip_tts_wrapper(strip_dtmf_tags(text))
                        lines.append(f"{mod_name}.prompt={{{wrap}:{text}}}")
                    else:
                        lines.append(f"{mod_name}.prompt={{{wrap}:TODO_発話内容を記入}}")
                        todo.append(mod_name)
                break

    return lines, todo


def detect_call_transfer(spec_data: dict) -> list[str]:
    """scenario_flow から call_transfer ブロックのモジュール名を返す"""
    modules: list[str] = []
    for block in spec_data.get("scenario_flow", []):
        if block.get("type") == "call_transfer":
            step = block.get("step", "")
            if step:
                modules.append(step)
    return modules


def main() -> None:
    parser = argparse.ArgumentParser(description="IVRプロパティ生成スクリプト")
    parser.add_argument("spec", help="設計書 YAML パス")
    parser.add_argument(
        "--env",
        choices=["demo", "prod"],
        default="demo",
        help="環境 (demo/prod、デフォルト: demo)",
    )
    parser.add_argument("--out", default=None, help="出力パス（省略時は自動導出）")
    args = parser.parse_args()

    try:
        import yaml
    except ImportError:
        print("Error: pyyaml が必要です", file=sys.stderr)
        sys.exit(1)

    project_root = Path(__file__).resolve().parent.parent
    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: 設計書が見つかりません: {spec_path}", file=sys.stderr)
        sys.exit(1)

    # ── 設計書を読む ──────────────────────────────────────────────────────────
    with open(spec_path, encoding="utf-8") as f:
        spec_data = yaml.safe_load(f)

    # 施設名・フロー名を取得。
    # 優先: basic_info.facility_name / scenario_name（正本。orchestrator.py の
    # _normalize_state_from_yaml と同じ参照元で、日付サフィックスを含まない）。
    # flow_structure.flows[0].name は「group_name$scenario_name」形式で、$ より前は
    # group_name（末尾に作業日 _YYYYMMDD を含む）であって facility_name ではないため、
    # これをそのまま「facility」として使うと出力先ディレクトリ名に日付とシナリオ名が
    # 二重に混入する（例: 東京都立豊島病院_診療_20260714_診療）。basic_info が欠けている
    # 旧形式 YAML のみ、そちらの split をフォールバックとして使う。
    basic_info = spec_data.get("basic_info", {}) or {}
    facility = str(basic_info.get("facility_name") or "").strip()
    flow = str(basic_info.get("scenario_name") or "").strip()

    if not facility or not flow:
        flow_name_full = (
            spec_data.get("flow_structure", {})
            .get("flows", [{}])[0]
            .get("name", "")
        )
        if "$" in flow_name_full:
            fallback_facility, fallback_flow = flow_name_full.split("$", 1)
        else:
            # ファイル名から導出（フォールバック）
            stem_raw = spec_path.stem.replace("設計書_", "")
            if "_" in stem_raw:
                parts = stem_raw.rsplit("_", 1)
                fallback_facility, fallback_flow = parts[0], parts[1]
            else:
                fallback_facility, fallback_flow = stem_raw, "診療"
        facility = facility or fallback_facility
        flow = flow or fallback_flow

    print(f"[gen_properties] 施設: {facility}  フロー: {flow}", file=sys.stderr)

    # office_id
    office_id = (
        spec_data.get("basic_info", {}).get("office_id", "")
        or "TODO_施設のoffice_idを入力"
    )

    # TTS ラッパー: AI_TALK 施設は {tts_ai:}、それ以外（GOOGLE / 未指定）は {tts_g:}。
    # scaffold_generator と同じ正規化（basic_info.tts_platform を大文字化）。
    tts_platform = (spec_data.get("basic_info", {}).get("tts_platform") or "GOOGLE").upper()
    tts_wrap = "tts_ai" if tts_platform == "AI_TALK" else "tts_g"
    print(f"[gen_properties] TTS platform: {tts_platform} → ラッパー {{{tts_wrap}:}}", file=sys.stderr)

    # ── TTS テキスト解決 ─────────────────────────────────────────────────────
    tts_texts = resolve_tts_texts(spec_data)
    print(f"[gen_properties] 設計書 TTS テキスト: {len(tts_texts)} 件", file=sys.stderr)

    # 個人情報4種（氏名/生年月日/電話番号/診察券番号）で、director が tts_modules/step_details に
    # 文言を書かず汎用デフォルトが適用されたモジュールを記録する（TODO ではないが要レビュー対象。
    # qa_validator.py の TTS-COVERAGE チェックとは別に、properties 生成側でも可視化する）。
    _explicit_texts: dict[str, str] = {}
    for tm in spec_data.get("tts_modules", []):
        n = tm.get("module_name", "")
        if n and (tm.get("announcement", "") or tm.get("text", "")):
            _explicit_texts[n] = "1"
    for sd in spec_data.get("step_details", []):
        n = sd.get("step_name", "")
        if n and sd.get("tts_announcement", ""):
            _explicit_texts[n] = "1"
    slot_defaults_used = sorted(
        name for name in resolve_slot_tts_defaults(spec_data) if name not in _explicit_texts
    )
    if slot_defaults_used:
        print(f"[gen_properties] 個人情報系デフォルト文言を使用（要レビュー）: "
              f"{', '.join(slot_defaults_used)}", file=sys.stderr)

    # ── scaffold TTS サイドカーを読む ─────────────────────────────────────────
    spec_stem = spec_path.stem.replace("設計書_", "")
    sidecar_path = project_root / "output" / "json" / f"scaffold_tts_{spec_stem}.json"
    tts_module_names: list[str] = []
    if sidecar_path.exists():
        tts_module_names = json.loads(sidecar_path.read_text(encoding="utf-8"))
        print(f"[gen_properties] TTS サイドカー: {len(tts_module_names)} モジュール", file=sys.stderr)
    else:
        print(f"[gen_properties] Warning: TTS サイドカーが見つかりません: {sidecar_path.name}", file=sys.stderr)
        print("[gen_properties] TTS 行なしで続行します（scaffold を先に実行してください）", file=sys.stderr)

    # ── TTS プロパティ行 ─────────────────────────────────────────────────────
    tts_lines, tts_todo = build_tts_lines(tts_module_names, tts_texts, tts_wrap)

    # slot phone v2: AI_TALK 施設は CASE A の Phone Normalization に module prompt を与える
    # （#data# は module 内部変数のため — docs/specs/slot_phone_v2.md）
    phone_norm_lines = build_phone_norm_prompt_lines(spec_data, tts_wrap)
    if phone_norm_lines:
        tts_lines.extend(phone_norm_lines)
        print(f"[gen_properties] slot phone v2 (AI_TALK) module prompt: {len(phone_norm_lines)} 行",
              file=sys.stderr)

    # ── サブフロー TTS（Step 4-B 相当） ──────────────────────────────────────
    templates_path = project_root / "docs" / "specs" / "subflow_property_templates.json"
    subflow_tts_lines, subflow_tts_todo = build_subflow_tts_lines(
        spec_data, tts_texts, templates_path, tts_wrap
    )
    if subflow_tts_lines:
        print(f"[gen_properties] サブフロー TTS: {len(subflow_tts_lines)} 行", file=sys.stderr)

    # ── Call Transfer モジュール ──────────────────────────────────────────────
    call_transfer_modules = detect_call_transfer(spec_data)

    # ── 環境テンプレート ──────────────────────────────────────────────────────
    env_file = "env_demo.txt" if args.env == "demo" else "env_prod.txt"
    env_path = project_root / "docs" / "specs" / env_file
    if env_path.exists():
        env_text = env_path.read_text(encoding="utf-8").strip()
    else:
        env_text = f"# 環境設定テンプレートが見つかりません: {env_file}"
    print(f"[gen_properties] 環境: {args.env} ({env_file})", file=sys.stderr)

    # ── 出力パスを決定 ────────────────────────────────────────────────────────
    # 成果物は output/scenarios/{施設}_{基底フロー名}/ 配下に集約する（master 保護方針）。
    # flow には _YYYYMMDD 日付サフィックスが含まれる場合があるため、ディレクトリ名は
    # 日付サフィックス除去後の基底名で作成する（output/scenarios の既存ディレクトリ命名規則と整合）。
    base_flow = re.sub(r"_\d{8}(_\d{8})*$", "", flow)
    if args.out:
        output_path = Path(args.out)
    else:
        output_dir = project_root / "output" / "scenarios" / f"{facility}_{base_flow}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"properties_{facility}_{flow}.md"

    # ── Markdown を組み立てる ─────────────────────────────────────────────────
    all_todo = tts_todo + subflow_tts_todo

    md: list[str] = []
    md.append(f"# IVR プロパティ — {facility} {flow}")
    md.append("")
    md.append("> Brekeke IVR の **「プロパティ」欄** に以下のテキストをコピー&ペーストしてください。")
    md.append("> `TODO_` で始まる値は実際の値に置き換えてから使用してください。")
    md.append("")
    md.append("```")

    # アナウンス（TTS prompt）
    md.append("# アナウンス（TTS prompt）")
    if tts_lines:
        md.extend(tts_lines)
    else:
        md.append("# （TTS モジュールなし — scaffold を実行してからこのスクリプトを再実行してください）")

    # サブフロー TTS
    if subflow_tts_lines:
        md.append("")
        md.append("# サブフローTTS")
        md.extend(subflow_tts_lines)

    # wait
    md.append("")
    md.append("# wait")
    md.append("冒頭.wait=2000")

    # 施設固有
    md.append("")
    md.append("# 施設固有（要編集）")
    md.append(f"office_id={office_id}")
    for ct in call_transfer_modules:
        md.append(f"{ct}.number=TODO_転送先番号を入力")

    # 環境設定
    md.append("")
    md.append("# 環境設定")
    md.append(env_text)

    md.append("```")
    md.append("")

    # TODO リスト
    md.append("## TODO リスト")
    md.append("")
    if office_id.startswith("TODO_"):
        md.append("- [ ] `office_id` を設定する")
    if all_todo:
        md.append("- [ ] 以下のモジュールにアナウンス文言を記入する:")
        for mod in all_todo:
            md.append(f"  - `{mod}`")
    if call_transfer_modules:
        md.append("- [ ] 転送先電話番号を設定する:")
        for ct in call_transfer_modules:
            md.append(f"  - `{ct}`")
    if not office_id.startswith("TODO_") and not all_todo and not call_transfer_modules:
        md.append("- （TODO 項目なし）")

    if slot_defaults_used:
        md.append("")
        md.append("## 要レビュー（個人情報聴取の汎用デフォルト文言を使用）")
        md.append("")
        md.append(
            "以下のモジュールは設計書に施設固有の文言（`tts_modules` / `step_details`）が"
            "無かったため、汎用デフォルトを自動適用しています。TODO ではなく発話として出力済みですが、"
            "施設の呼称・敬語レベルに合わせて調整が必要か確認してください:"
        )
        for mod in slot_defaults_used:
            md.append(f"  - `{mod}`")

    md.append("")
    md.append(
        "> **注意**: リトライモジュール（Speech Retry Counter）の `prompt_true` / `prompt_false` は"
        "IVRプロパティには記述しない。フローJSON内の params に直接記述すること。"
    )

    # ── 書き出し ──────────────────────────────────────────────────────────────
    output_path.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"[gen_properties] 完了: {output_path}", file=sys.stderr)
    print(str(output_path))


if __name__ == "__main__":
    main()
