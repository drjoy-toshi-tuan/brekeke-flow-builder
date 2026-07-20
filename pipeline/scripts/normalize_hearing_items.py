#!/usr/bin/env python3
"""
normalize_hearing_items.py — 聴取項目名の正規化 + シナリオブロック生成

Usage:
  python3 scripts/normalize_hearing_items.py --input <file> [--output <yaml>] [--show-unmatched]

Input types (auto-detected by extension):
  .txt / .pdf.txt  — PDF から抽出したテキスト（pdftotext 等の出力）
  .xml             — draw.io XML ファイル

Output:
  scenario_flow 形式の YAML スニペット（stdout または --output ファイル）

Examples:
  python3 scripts/normalize_hearing_items.py --input 仕様書.txt
  python3 scripts/normalize_hearing_items.py --input フロー.drawio.xml --output flow_blocks.yaml
  python3 scripts/normalize_hearing_items.py --input 仕様書.txt --show-unmatched
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml


# ============================================================
# カタログ読み込み
# ============================================================

_CATALOG_PATH = Path(__file__).parent.parent / "docs" / "specs" / "hearing_item_catalog.yaml"


def load_catalog(catalog_path: Path = _CATALOG_PATH) -> list[dict]:
    """hearing_item_catalog.yaml を読み込んで返す。"""
    with catalog_path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("items", [])


def build_synonym_map(items: list[dict]) -> dict[str, dict]:
    """
    シノニム → カタログエントリ の逆引き辞書を作る。
    マッチングは正規化後の文字列で行う。
    """
    mapping: dict[str, dict] = {}
    for item in items:
        canonical = item["canonical"]
        # canonical 自身もシノニムに含める
        all_syns = [canonical] + list(item.get("synonyms", []))
        for syn in all_syns:
            key = _normalize_key(syn)
            if key not in mapping:
                mapping[key] = item
    return mapping


def _normalize_key(text: str) -> str:
    """空白・全角ハイフン・アンダースコアなどを除去して小文字化する。"""
    text = text.strip()
    # 全角スペース → 空白
    text = text.replace("　", "")
    # 半角スペース除去
    text = text.replace(" ", "")
    # 全角ハイフン → 通常ハイフン
    text = text.replace("－", "-").replace("－", "-")
    # アンダースコア・中黒を除去（内部モジュール名 用件_聴取 / 資料表記 初診・再診確認 の
    # 表記ゆれを synonym 追加なしで吸収する。catalog 側の synonyms は資料の生ラベルのみ）
    text = text.replace("_", "").replace("・", "")
    # 統一（ひらがな・カタカナは保持）
    return text.lower()


# ============================================================
# 入力パーサー
# ============================================================

def extract_labels_from_text(text: str) -> list[str]:
    """
    プレーンテキスト（PDF 抽出など）から聴取項目候補を抽出する。

    ヒューリスティック:
      - 「聴取項目」「ヒアリング項目」などの見出し行の後に続くリスト
      - 行頭に番号・記号がついたリスト項目
      - 括弧付きラベル（例: 「診療科」「予約希望日」）
    """
    candidates: list[str] = []

    # パターン1: 行頭に ・/●/○/数字. のリスト
    list_pattern = re.compile(
        r"^[\s]*(?:[・●○■□▶►▷\-\*]|\d+[.)、。])\s*(.+)$",
        re.MULTILINE,
    )
    for m in list_pattern.finditer(text):
        item = m.group(1).strip()
        if _is_plausible_label(item):
            candidates.append(item)

    # パターン2: 「〜聴取」「〜確認」「〜選択」などのキーワードを含む行
    keyword_pattern = re.compile(
        r"([^\n]{2,20}(?:聴取|確認|選択|ヒアリング|入力|取得|判定))",
    )
    for m in keyword_pattern.finditer(text):
        item = m.group(1).strip()
        if _is_plausible_label(item):
            candidates.append(item)

    # パターン3: 括弧に囲まれたラベル
    bracket_pattern = re.compile(r"[「『【〔\(（]([^」』】〕\)）]{2,20})[」』】〕\)）]")
    for m in bracket_pattern.finditer(text):
        item = m.group(1).strip()
        if _is_plausible_label(item):
            candidates.append(item)

    # 重複除去（順序保持）
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


def _is_plausible_label(text: str) -> bool:
    """ラベルとして妥当かどうかの簡易フィルタ。"""
    if len(text) < 2 or len(text) > 30:
        return False
    # 英数字のみ → 除外
    if re.fullmatch(r"[a-zA-Z0-9\s\-_]+", text):
        return False
    # URL・日付っぽいもの → 除外
    if re.search(r"https?://|www\.|\.com", text):
        return False
    return True


def extract_labels_from_drawio(xml_text: str) -> list[str]:
    """
    draw.io XML から聴取項目候補を抽出する。

    draw.io の mxCell value 属性または label 属性から日本語テキストを取り出す。
    """
    candidates: list[str] = []

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"ERROR: draw.io XML のパースに失敗しました: {e}", file=sys.stderr)
        return candidates

    # mxCell の value 属性を走査
    for elem in root.iter():
        for attr in ("value", "label"):
            raw = elem.get(attr, "")
            if not raw:
                continue
            # HTML タグを除去
            clean = re.sub(r"<[^>]+>", "", raw).strip()
            # HTML エンティティを簡易デコード
            clean = (
                clean.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&nbsp;", " ")
                .replace("<br>", " ")
            )
            clean = clean.strip()
            if clean and _is_plausible_label(clean):
                candidates.append(clean)

    # 重複除去
    seen: set[str] = set()
    unique: list[str] = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            unique.append(c)
    return unique


# ============================================================
# マッチング
# ============================================================

def match_labels(
    labels: list[str],
    synonym_map: dict[str, dict],
) -> tuple[list[tuple[str, dict]], list[str]]:
    """
    抽出ラベルリストをカタログと照合する。

    Returns:
        matched: [(original_label, catalog_entry), ...]
        unmatched: [original_label, ...]
    """
    matched: list[tuple[str, dict]] = []
    unmatched: list[str] = []

    for label in labels:
        key = _normalize_key(label)
        entry = synonym_map.get(key)

        if entry is None:
            # 部分一致フォールバック: カタログキーが label を含む or label がキーを含む
            entry = _fuzzy_match(key, synonym_map)

        if entry is not None:
            matched.append((label, entry))
        else:
            unmatched.append(label)

    return matched, unmatched


def _fuzzy_match(key: str, synonym_map: dict[str, dict]) -> dict | None:
    """
    完全一致しない場合の部分一致フォールバック。
    カタログ内のシノニムキーが key に含まれる、または key がシノニムキーに含まれる場合にマッチ。
    短すぎるキー（2文字以下）は除外して誤マッチを防ぐ。
    """
    best: dict | None = None
    best_len = 0

    for catalog_key, entry in synonym_map.items():
        if len(catalog_key) <= 2:
            continue
        # catalog_key が key に含まれる（例: "診療科" ⊂ "診療科聴取"）
        if catalog_key in key or key in catalog_key:
            if len(catalog_key) > best_len:
                best = entry
                best_len = len(catalog_key)

    return best


# ============================================================
# YAML ブロック生成
# ============================================================

def _get(entry: dict, key: str) -> Any:
    """カタログの値を取得（"~" は None 扱い）。"""
    v = entry.get(key)
    return None if v in (None, "~") else v


def build_design_sections(
    matched: list[tuple[str, dict]],
    catalog_items: list[dict] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """
    マッチ結果から設計書テンプレート準拠の 3 セクションを生成する。
      - scenario_flow : step / type / (slot) / output_format / next|conditions
      - hearing_items : stt_type / save_to / openai_processing / output_labels 等（hearing/faq のみ）
      - step_details  : tts_announcement(TODO) / mapping(TODO) / next_step(TODO) 等
    重複 canonical は除去（最初の出現を採用）。next は文書出現順で仮チェーンし、
    分岐（conditions）の遷移先は TODO_next のまま人間壁打ちで確定する。
    """
    seen_canonical: set[str] = set()
    entries: list[dict] = []
    for _original_label, entry in matched:
        canonical = entry["canonical"]
        if canonical in seen_canonical:
            continue
        seen_canonical.add(canonical)
        entries.append(entry)

    # next_hint（FAQ照合 等）の遷移先がマッチ結果に無ければカタログから自動追加する
    # — 問い合わせ系はすべて FAQ照合 の入力（資料に FAQ が明記されないことが多い）
    if catalog_items:
        by_canonical = {it["canonical"]: it for it in catalog_items}
        for entry in list(entries):
            hint = _get(entry, "next_hint")
            if hint and hint not in seen_canonical and hint in by_canonical:
                seen_canonical.add(hint)
                entries.append(by_canonical[hint])

    scenario_flow: list[dict[str, Any]] = []
    hearing_items: list[dict[str, Any]] = []
    step_details: list[dict[str, Any]] = []

    for idx, entry in enumerate(entries):
        canonical = entry["canonical"]
        block_type = entry.get("block_type", "hearing")
        next_step = _get(entry, "next_hint") or (
            entries[idx + 1]["canonical"] if idx + 1 < len(entries) else "TODO_next"
        )

        block: dict[str, Any] = {"step": canonical, "type": block_type}

        if block_type == "opening":
            block["use_acceptance_times"] = True
            block["next"] = next_step

        elif block_type in ("slot", "card_number"):
            slot_kind = _get(entry, "slot")
            if block_type == "slot" and slot_kind:
                block["slot"] = slot_kind
            block["next"] = next_step

        elif block_type in ("hearing", "faq"):
            fmt = _get(entry, "output_format")
            if fmt:
                block["output_format"] = fmt
            labels = entry.get("output_labels") or []
            if fmt == "enum" and labels:
                # 分岐先は資料からは決められない — 壁打ちで確定する。
                # next_hint がある場合のみ default 側をヒント先へ仮接続する
                # （例: 追加の質問 — あり(default)→FAQ照合 / なし→終話(TODO)）
                hint = _get(entry, "next_hint")
                block["conditions"] = [
                    {"match": lb,
                     "next": hint if (hint and lb == "default") else "TODO_next"}
                    for lb in labels
                ]
            else:
                block["next"] = next_step
                block["retry_failure"] = "end_failure"

            stt = _get(entry, "stt_type") or "AmiVoice_STT"
            is_dtmf = stt == "DTMF_AmiVoice"
            proc = _get(entry, "processing")
            # hearing_items.openai_processing は設計書テンプレートの語彙に合わせる:
            # processing=openai の場合のみ OpenAI 後処理あり（datetime→convert / それ以外→classify）。
            # script / none は OpenAI 不使用 = "none"（判定は認定 script 部品 / 生保存）
            if proc == "openai":
                openai_processing = "convert" if fmt == "datetime" else "classify"
            else:
                openai_processing = "none"

            hearing_items.append({
                "order": len(hearing_items) + 1,
                "name": canonical,
                "stt_type": stt,
                "dtmf_max_length": 1 if is_dtmf else None,
                "retry_count": 2,
                "echo_back": False,
                "save_to": _get(entry, "save_to") or "TODO_要確認",
                "openai_processing": openai_processing,
                "output_format": fmt or "text",
                "output_labels": labels,
                "notes": f"処理方式: {proc or 'none'} — {_get(entry, 'processing_ref') or ''}".strip(" —"),
            })

            step_details.append({
                "step_name": canonical,
                "tts_announcement": "TODO_資料転記",
                "input_method": "dtmf_voice" if is_dtmf else "voice_only",
                "save_to": _get(entry, "save_to") or "TODO_要確認",
                "next_step": next_step if not (fmt == "enum" and labels) else "TODO_要確認",
                "retry_failure": "end_failure",
            })

        scenario_flow.append(block)

    return {
        "scenario_flow": scenario_flow,
        "hearing_items": hearing_items,
        "step_details": step_details,
    }


def render_yaml(sections: dict[str, list[dict[str, Any]]]) -> str:
    """3 セクションを設計書テンプレート順で YAML 文字列にレンダリングする。"""
    header = (
        "# normalize_hearing_items.py が生成した設計書ドラフト断片\n"
        "# 設計書テンプレート（docs/specs/設計書テンプレート.yaml）の\n"
        "# セクション4b (scenario_flow) / 6 (hearing_items) / 7 (step_details) に対応。\n"
        "# TODO_next / TODO_要確認 / TODO_資料転記 は壁打ちで人間が確定すること。\n"
    )
    body = yaml.dump(
        {k: v for k, v in sections.items() if v},
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        indent=2,
    )
    return header + body


# ============================================================
# メイン
# ============================================================

def main() -> int:
    parser = argparse.ArgumentParser(
        description="聴取項目名を正規化して scenario_flow YAML ブロックを生成する",
    )
    parser.add_argument("--input", "-i", required=True, help="入力ファイル (.txt / .xml)")
    parser.add_argument("--output", "-o", help="出力 YAML ファイル (省略時: stdout)")
    parser.add_argument(
        "--catalog",
        default=str(_CATALOG_PATH),
        help=f"カタログ YAML パス (デフォルト: {_CATALOG_PATH})",
    )
    parser.add_argument(
        "--show-unmatched",
        action="store_true",
        help="マッチしなかったラベルを stderr に表示する",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: 入力ファイルが見つかりません: {input_path}", file=sys.stderr)
        return 1

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        print(f"ERROR: カタログファイルが見つかりません: {catalog_path}", file=sys.stderr)
        return 1

    # カタログ読み込み
    catalog_items = load_catalog(catalog_path)
    synonym_map = build_synonym_map(catalog_items)

    # 入力ファイル読み込み & ラベル抽出
    raw = input_path.read_text(encoding="utf-8", errors="replace")

    suffix = input_path.suffix.lower()
    if suffix == ".xml":
        labels = extract_labels_from_drawio(raw)
        source_type = "draw.io XML"
    else:
        # .txt / .pdf.txt / その他
        labels = extract_labels_from_text(raw)
        source_type = "テキスト"

    if not labels:
        print(f"WARN: {source_type} から聴取項目候補が見つかりませんでした。", file=sys.stderr)

    print(f"INFO: {source_type} から {len(labels)} 件の候補を抽出しました。", file=sys.stderr)

    # マッチング
    matched, unmatched = match_labels(labels, synonym_map)

    print(
        f"INFO: マッチ {len(matched)} 件 / 未マッチ {len(unmatched)} 件",
        file=sys.stderr,
    )

    if args.show_unmatched and unmatched:
        print("\n--- 未マッチ項目 (カタログに追加を検討) ---", file=sys.stderr)
        for u in unmatched:
            print(f"  {u}", file=sys.stderr)

    # YAML 生成
    sections = build_design_sections(matched, catalog_items)
    yaml_text = render_yaml(sections)

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(yaml_text, encoding="utf-8")
        print(f"INFO: {out_path} に書き出しました。", file=sys.stderr)
    else:
        print(yaml_text)

    return 0


if __name__ == "__main__":
    sys.exit(main())
