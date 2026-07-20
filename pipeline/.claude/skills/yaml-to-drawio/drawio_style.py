"""
drawio_style.py — AI電話設計書 drawio の「視覚標準」SSoT(Single Source of Truth)。

このファイルは drawio-templates/ プロジェクトが正本(原本)を保持する。
yaml-to-drawio / canva-to-drawio 等の各 skill は、このファイルの **バイト完全一致の
コピー(vendored copy)** を自分のディレクトリに置き、そこから import すること。

⚠️ 各 skill の vendored コピーをその場で編集してはならない。
   変更は必ずこの正本に入れ、`check_sync.py` で全コピーへ再配布(同期)する。
   drawio-templates/check_sync.py が正本と各コピーのハッシュ不一致を検出する。

定義する視覚語彙:
  - 4 種別カラーパレット(announce / question / item / end) と TYPE_MAP
  - エッジ色ヒューリスティック(予約=青 / 変更=橙 / キャンセル=赤 / 種類=緑 / 合流=灰)
  - ノード描画(node_xml) … type / announce / repeat 属性を埋め込む
  - エッジ描画(edge_xml) … 通常エッジ + kind="failure"(聴取失敗=赤・破線)
  - 凡例(LEGEND_XML)
  - アナウンス一覧ページ(build_announce_page) … 聴取項目|復唱|リトライ|失敗時|発話文言、src_ref 同期

ゴールデン参照: drawio-templates/reference/銚子市立病院_改善版_2page.drawio
標準仕様書:     drawio-templates/drawio_standard.md
"""
import re
from html import escape

# 同期チェック用。正本を変更したら必ず上げること(check_sync.py が照合に使う)。
# 2026-06-05.1: edge_xml に kind="failure"(聴取失敗の赤・破線)追加、
#               build_announce_page に「リトライ」「失敗時」列を追加(CSTS フィードバック)。
STYLE_VERSION = "2026-06-05.1"


# ─── 9 ブロック型 → drawio 4 種別 ───
# (type_str, fillColor, strokeColor, is_strong)
TYPE_MAP = {
    "opening":                 ("announce", "#FFF3E0", "#FB8C00", True),
    "announcement":            ("announce", "#FFF3E0", "#FB8C00", True),
    "hearing":                 ("item",     "#F5F5F5", "#616161", False),
    "subflow":                 ("item",     "#F5F5F5", "#616161", False),
    "context_match_router":    ("question", "#E3F2FD", "#1976D2", True),
    "script":                  ("question", "#E3F2FD", "#1976D2", True),
    "date_of_call_classifier": ("question", "#E3F2FD", "#1976D2", True),
    "call_transfer":           ("item",     "#F5F5F5", "#616161", False),
    "termination":             ("end",      "#FFEBEE", "#E53935", True),
    "augment":                 ("item",     "#FFF9C4", "#9E9E9E", False),
}


def resolve_type_color(btype: str, is_branch: bool):
    """ブロック型 + 分岐有無 → (type_str, fill, stroke, strong)。
    hearing も conditions あり時は question 色に上書き。
    """
    type_str, fill, stroke, strong = TYPE_MAP.get(btype, ("item", "#F5F5F5", "#616161", False))
    if is_branch and type_str == "item":
        return ("question", "#E3F2FD", "#1976D2", True)
    return (type_str, fill, stroke, strong)


def edge_color_for(match_str: str) -> str:
    """conditions[].match の値からエッジ色を推定。"""
    s = (match_str or "").strip()
    if not s or s in ("other", "default", "unknown", "NO_RESULT"):
        return "#9E9E9E"
    if any(k in s for k in ("新規", "予約", "定期受診")):
        return "#1976D2"
    if "変更" in s:
        return "#FB8C00"
    if "キャンセル" in s:
        return "#E53935"
    if any(k in s for k in ("健診", "健康診断", "がん", "予防接種", "ワクチン", "ドック")):
        return "#43A047"
    return "#757575"


def sanitize_id(name: str, used: dict) -> str:
    """ノード ID をサニタイズ(衝突防止)。used は呼び出し側で共有する辞書。"""
    base = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    if not base or base[0].isdigit():
        base = "n_" + base
    if base in used:
        used[base] += 1
        return f"{base}_{used[base]}"
    used[base] = 0
    return base


# ─── ノード / エッジ描画 ───
NODE_W = 180
NODE_H = 44


def node_xml(node_id, x, y, name, btype, is_branch, announce="", repeat="無し"):
    type_str, fill, stroke, strong = resolve_type_color(btype, is_branch)
    bold = "fontStyle=1;" if strong else ""
    sw = "2" if strong else "1.5"
    style = (
        f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
        f"fontColor=#212121;fontSize=12;arcSize=30;strokeWidth={sw};{bold}"
    )
    safe = escape(name)
    # 銚子 改善版に合わせ、ノード自体に announce / repeat / type 属性を持たせる
    # (ページ2「アナウンス一覧」が src_ref でこのノードを参照して同期する)
    return (
        f'        <object id="{node_id}" label="{safe}" type="{type_str}" '
        f'repeat="{escape(repeat)}" announce="{escape(announce)}">\n'
        f'          <mxCell parent="1" style="{style}" vertex="1">\n'
        f'            <mxGeometry height="{NODE_H}" width="{NODE_W}" x="{x}" y="{y}" as="geometry" />\n'
        f"          </mxCell>\n"
        f"        </object>"
    )


# 聴取失敗(リトライ上限到達)エッジの色。終話枠と同じ赤を破線で使う。
FAILURE_EDGE_COLOR = "#E53935"


def edge_xml(src_id, tgt_id, label, kind="normal"):
    """エッジ XML を生成。
    kind="normal"  : match 値で色分けした通常の実線エッジ(既定・後方互換)
    kind="failure" : 聴取失敗(リトライ上限到達)の遷移。赤・破線・斜体ラベル。
                     label 省略時は「聴取失敗」を既定表示。
    """
    if kind == "failure":
        color = FAILURE_EDGE_COLOR
        text = label or "聴取失敗"
        style = (
            f"endArrow=classic;html=1;rounded=1;edgeStyle=orthogonalEdgeStyle;jettySize=auto;"
            f"orthogonalLoop=1;dashed=1;dashPattern=6 4;strokeColor={color};strokeWidth=1.5;"
            f"fontSize=10;fontColor={color};labelBackgroundColor=#FFFFFF;fontStyle=2;"
        )
        value_attr = f' value="{escape(text)}"'
        return (
            f'        <mxCell edge="1" parent="1" source="{src_id}" target="{tgt_id}" '
            f'style="{style}"{value_attr}>'
            f'<mxGeometry relative="1" as="geometry" />'
            f"</mxCell>"
        )

    color = edge_color_for(label)
    safe_label = escape(label) if label else ""
    bold = "fontStyle=1;" if label and color != "#9E9E9E" else ""
    style = (
        f"endArrow=classic;html=1;rounded=1;edgeStyle=orthogonalEdgeStyle;jettySize=auto;"
        f"orthogonalLoop=1;strokeColor={color};strokeWidth=1.5;"
    )
    if label:
        style += f"fontSize=10;fontColor={color};labelBackgroundColor=#FFFFFF;{bold}"
    value_attr = f' value="{safe_label}"' if label else ""
    return (
        f'        <mxCell edge="1" parent="1" source="{src_id}" target="{tgt_id}" '
        f'style="{style}"{value_attr}>'
        f'<mxGeometry relative="1" as="geometry" />'
        f"</mxCell>"
    )


# ─── 凡例 ───
LEGEND_XML = """
        <mxCell id="legend_bg" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#BDBDBD;strokeWidth=1;arcSize=8;" value="" vertex="1">
          <mxGeometry height="240" width="280" x="LEGEND_X" y="80" as="geometry" />
        </mxCell>
        <mxCell id="legend_title" parent="1" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#212121;" value="凡例" vertex="1">
          <mxGeometry height="20" width="80" x="LEGEND_X_PAD" y="90" as="geometry" />
        </mxCell>
        <mxCell id="lg_announce_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;strokeColor=#FB8C00;fontColor=#212121;fontSize=11;fontStyle=1;arcSize=30;strokeWidth=2;" value="アナウンス" vertex="1">
          <mxGeometry height="28" width="100" x="LEGEND_X_PAD" y="118" as="geometry" />
        </mxCell>
        <mxCell id="lg_announce_text" parent="1" style="text;html=1;align=left;fontSize=11;fontColor=#424242;" value=": opening / announcement" vertex="1">
          <mxGeometry height="28" width="170" x="LEGEND_TXT_X" y="118" as="geometry" />
        </mxCell>
        <mxCell id="lg_question_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E3F2FD;strokeColor=#1976D2;fontColor=#212121;fontSize=11;fontStyle=1;arcSize=30;strokeWidth=2;" value="質問/分岐" vertex="1">
          <mxGeometry height="28" width="100" x="LEGEND_X_PAD" y="150" as="geometry" />
        </mxCell>
        <mxCell id="lg_question_text" parent="1" style="text;html=1;align=left;fontSize=11;fontColor=#424242;" value=": CMR / script / classifier / hearing(分岐)" vertex="1">
          <mxGeometry height="28" width="220" x="LEGEND_TXT_X" y="150" as="geometry" />
        </mxCell>
        <mxCell id="lg_item_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#616161;fontColor=#212121;fontSize=11;arcSize=30;strokeWidth=1.5;" value="項目" vertex="1">
          <mxGeometry height="28" width="100" x="LEGEND_X_PAD" y="182" as="geometry" />
        </mxCell>
        <mxCell id="lg_item_text" parent="1" style="text;html=1;align=left;fontSize=11;fontColor=#424242;" value=": hearing / subflow / call_transfer" vertex="1">
          <mxGeometry height="28" width="200" x="LEGEND_TXT_X" y="182" as="geometry" />
        </mxCell>
        <mxCell id="lg_end_box" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFEBEE;strokeColor=#E53935;fontColor=#212121;fontSize=11;fontStyle=1;arcSize=30;strokeWidth=2;" value="終話" vertex="1">
          <mxGeometry height="28" width="100" x="LEGEND_X_PAD" y="214" as="geometry" />
        </mxCell>
        <mxCell id="lg_end_text" parent="1" style="text;html=1;align=left;fontSize=11;fontColor=#424242;" value=": termination" vertex="1">
          <mxGeometry height="28" width="100" x="LEGEND_TXT_X" y="214" as="geometry" />
        </mxCell>
        <mxCell id="lg_note" parent="1" style="text;html=1;align=left;fontSize=10;fontColor=#757575;whiteSpace=wrap;" value="エッジ色は match 値で自動判別(青=予約系/橙=変更系/赤=キャンセル/緑=種類分岐/灰=合流)。赤の破線=リトライ上限到達時(聴取失敗)の遷移。" vertex="1">
          <mxGeometry height="56" width="270" x="LEGEND_X_PAD" y="248" as="geometry" />
        </mxCell>
"""


def legend_xml_at(legend_x: int) -> str:
    """凡例 XML を指定 X 座標に配置して返す(y は固定 80。上部配置用)。"""
    legend_x_pad = legend_x + 15
    legend_txt_x = legend_x + 125
    return (
        LEGEND_XML
        .replace("LEGEND_X_PAD", str(legend_x_pad))
        .replace("LEGEND_TXT_X", str(legend_txt_x))
        .replace("LEGEND_X", str(legend_x))
    )


# 凡例の 4 種別スウォッチ定義(build_legend 用)
_LEGEND_SWATCHES = [
    ("#FFF3E0", "#FB8C00", "アナウンス", ": opening / announcement", True),
    ("#E3F2FD", "#1976D2", "質問/分岐", ": CMR / script / classifier / hearing(分岐)", True),
    ("#F5F5F5", "#616161", "項目", ": hearing / subflow / call_transfer", False),
    ("#FFEBEE", "#E53935", "終話", ": termination", True),
]


def build_legend(legend_x: int, legend_y: int = 80) -> str:
    """凡例を任意の原点 (legend_x, legend_y) に配置して生成する。
    legend_xml_at は y 固定だが、中央寄せレイアウトで凡例を下部などに置きたい
    呼び出し側のために原点を任意化したもの。視覚(配色・ラベル)は LEGEND_XML と同一。
    """
    x_pad = legend_x + 15
    txt_x = legend_x + 125
    parts = [
        f'        <mxCell id="legend_bg" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#BDBDBD;strokeWidth=1;arcSize=8;" value="" vertex="1">\n'
        f'          <mxGeometry height="240" width="290" x="{legend_x}" y="{legend_y}" as="geometry" />\n'
        f'        </mxCell>',
        f'        <mxCell id="legend_title" parent="1" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;fontSize=13;fontStyle=1;fontColor=#212121;" value="凡例" vertex="1">\n'
        f'          <mxGeometry height="20" width="80" x="{x_pad}" y="{legend_y + 10}" as="geometry" />\n'
        f'        </mxCell>',
    ]
    sy = legend_y + 38
    for i, (fill, stroke, label, desc, bold) in enumerate(_LEGEND_SWATCHES):
        fs = "fontStyle=1;" if bold else ""
        sw = "2" if bold else "1.5"
        parts.append(
            f'        <mxCell id="lg_box_{i}" parent="1" style="rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor=#212121;fontSize=11;{fs}arcSize=30;strokeWidth={sw};" value="{escape(label)}" vertex="1">\n'
            f'          <mxGeometry height="28" width="100" x="{x_pad}" y="{sy}" as="geometry" />\n'
            f'        </mxCell>'
        )
        parts.append(
            f'        <mxCell id="lg_txt_{i}" parent="1" style="text;html=1;align=left;fontSize=11;fontColor=#424242;" value="{escape(desc)}" vertex="1">\n'
            f'          <mxGeometry height="28" width="190" x="{txt_x}" y="{sy}" as="geometry" />\n'
            f'        </mxCell>'
        )
        sy += 32
    parts.append(
        f'        <mxCell id="lg_note" parent="1" style="text;html=1;align=left;fontSize=10;fontColor=#757575;whiteSpace=wrap;" value="エッジ色は match 値で自動判別(青=予約系/橙=変更系/赤=キャンセル/緑=種類分岐/灰=合流)。赤の破線=リトライ上限到達時(聴取失敗)の遷移。" vertex="1">\n'
        f'          <mxGeometry height="56" width="270" x="{x_pad}" y="{sy}" as="geometry" />\n'
        f'        </mxCell>'
    )
    return "\n".join(parts)


# ─── アナウンス一覧(銚子 改善版フォーマット / 独立ページ = タブ2) ───
# 「聴取項目 | 復唱 | リトライ | 失敗時 | 発話文言」の5列テーブルを別ページとして組む。
#   - ヘッダー: 薄灰(#EEEEEE) + 灰枠(#9E9E9E)
#   - 聴取項目セル: ブロック型の配色で塗り、src_ref でページ1の対応ノード id を指す
#   - 復唱セル  : echo_back を「あり/無し」で表示
#   - リトライ列: 再聴取回数(例「×2」/ 非聴取行は「-」)
#   - 失敗時列  : リトライ上限到達時の挙動(終話 / スキップ / 切断 / -)
TBL_NAME_W = 130
TBL_ECHO_W = 50
TBL_RETRY_W = 60
TBL_FAIL_W = 70
TBL_TEXT_W = 540
TBL_TOTAL_W = TBL_NAME_W + TBL_ECHO_W + TBL_RETRY_W + TBL_FAIL_W + TBL_TEXT_W


def _row_height(text: str) -> int:
    # 発話文言列は約 34 全角文字/行。最小 52(銚子 改善版の標準行高)
    n = len(text or "")
    lines = max(1, -(-n // 34))   # ceil(n/34)
    return max(52, 26 + lines * 18)


def _unpack_announce_row(row):
    """行タプルを (name, echo, retry, failure, text, fill, stroke, src_id) に正規化。
    後方互換: 旧 6 タプル (name, echo, text, fill, stroke, src_id) も受理し、
    retry / failure を空欄("-")で補完する。
    """
    if len(row) >= 8:
        name, echo, retry, failure, text, fill, stroke, src_id = row[:8]
    else:  # 旧 6 タプル
        name, echo, text, fill, stroke, src_id = row[:6]
        retry, failure = "-", "-"
    return name, echo, (retry or "-"), (failure or "-"), text, fill, stroke, src_id


def build_announce_page(rows, facility_title=""):
    """ページ2「アナウンス一覧」の diagram XML を組み立てる。
    rows: [(聴取項目名, 復唱, リトライ, 失敗時, 発話文言, fillColor, strokeColor, src_id), ...]
          (旧 6 タプル形式も後方互換で受理)
    """
    start_x, start_y = 40, 50
    name_x = start_x
    echo_x = name_x + TBL_NAME_W
    retry_x = echo_x + TBL_ECHO_W
    fail_x = retry_x + TBL_RETRY_W
    text_x = fail_x + TBL_FAIL_W

    parts = []
    # タイトル
    title = "アナウンス一覧（ページ1ノードと同期）"
    parts.append(
        f'        <mxCell id="p2_title" parent="1" '
        f'style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=18;fontStyle=1;fontColor=#212121;" '
        f'value="{escape(title)}" vertex="1">'
        f'<mxGeometry height="36" width="790" x="{name_x}" y="{start_y}" as="geometry" /></mxCell>'
    )
    # ヘッダー行(薄灰)
    hy = start_y + 44
    HDR = "rounded=0;whiteSpace=wrap;html=1;fillColor=#EEEEEE;strokeColor=#9E9E9E;fontSize=12;fontStyle=1;fontColor=#212121;align=center;verticalAlign=middle;"
    for col, (cx, cw, label) in enumerate([
        (name_x, TBL_NAME_W, "聴取項目"),
        (echo_x, TBL_ECHO_W, "復唱"),
        (retry_x, TBL_RETRY_W, "リトライ"),
        (fail_x, TBL_FAIL_W, "失敗時"),
        (text_x, TBL_TEXT_W, "発話文言"),
    ]):
        parts.append(
            f'        <mxCell id="p2_h{col}" parent="1" style="{HDR}" value="{escape(label)}" vertex="1">'
            f'<mxGeometry height="32" width="{cw}" x="{cx}" y="{hy}" as="geometry" /></mxCell>'
        )
    # データ行
    y = hy + 32
    for i, row in enumerate(rows):
        name, echo, retry, failure, text, fill, stroke, src_id = _unpack_announce_row(row)
        h = _row_height(text)
        sid = i if not src_id else src_id
        src_attr = f' src_ref="{src_id}"' if src_id else ""
        name_style = (
            f"rounded=0;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
            f"fontSize=12;fontStyle=1;fontColor=#212121;align=center;verticalAlign=middle;"
        )
        cell_style = (
            f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#9E9E9E;"
            f"fontSize=11;fontColor=#212121;align=center;verticalAlign=middle;"
        )
        text_style = (
            f"rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#9E9E9E;"
            f"fontSize=11;fontColor=#212121;align=left;verticalAlign=middle;spacingLeft=8;spacingRight=8;"
        )
        # 聴取項目セル(src_ref でページ1ノードを参照)
        parts.append(
            f'        <object id="p2_label_{sid}" label="{escape(name)}"{src_attr} announce="{escape(text)}">\n'
            f'          <mxCell style="{name_style}" vertex="1" parent="1">\n'
            f'            <mxGeometry x="{name_x}" y="{y}" width="{TBL_NAME_W}" height="{h}" as="geometry" />\n'
            f'          </mxCell>\n'
            f'        </object>'
        )
        # 復唱セル
        parts.append(
            f'        <mxCell id="p2_repeat_{sid}" value="{escape(echo)}" style="{cell_style}" vertex="1" parent="1">'
            f'<mxGeometry x="{echo_x}" y="{y}" width="{TBL_ECHO_W}" height="{h}" as="geometry" /></mxCell>'
        )
        # リトライ列
        parts.append(
            f'        <mxCell id="p2_retry_{sid}" value="{escape(retry)}" style="{cell_style}" vertex="1" parent="1">'
            f'<mxGeometry x="{retry_x}" y="{y}" width="{TBL_RETRY_W}" height="{h}" as="geometry" /></mxCell>'
        )
        # 失敗時列
        parts.append(
            f'        <mxCell id="p2_fail_{sid}" value="{escape(failure)}" style="{cell_style}" vertex="1" parent="1">'
            f'<mxGeometry x="{fail_x}" y="{y}" width="{TBL_FAIL_W}" height="{h}" as="geometry" /></mxCell>'
        )
        # 発話文言セル(src_ref でページ1ノードを参照)
        parts.append(
            f'        <object id="p2_text_{sid}" label="{escape(text)}"{src_attr} announce="{escape(text)}">\n'
            f'          <mxCell style="{text_style}" vertex="1" parent="1">\n'
            f'            <mxGeometry x="{text_x}" y="{y}" width="{TBL_TEXT_W}" height="{h}" as="geometry" />\n'
            f'          </mxCell>\n'
            f'        </object>'
        )
        y += h

    page_w = text_x + TBL_TEXT_W + 60
    page_h = y + 60
    body = "\n".join(parts)
    return (
        f'  <diagram name="アナウンス一覧" id="yaml_to_drawio_announce">\n'
        f'    <mxGraphModel dx="1414" dy="743" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{page_w}" pageHeight="{page_h}" math="0" shadow="0">\n'
        f'      <root>\n'
        f'        <mxCell id="0" />\n'
        f'        <mxCell id="1" parent="0" />\n'
        f'{body}\n'
        f'      </root>\n'
        f'    </mxGraphModel>\n'
        f'  </diagram>'
    )


def assemble_mxfile(pages) -> str:
    """diagram 文字列のリストを 1 つの mxfile に束ねる。"""
    if isinstance(pages, str):
        pages = [pages]
    body = "\n".join(p for p in pages if p)
    return (
        '<mxfile host="app.diagrams.net" agent="Claude (drawio-templates SSoT)">\n'
        + body
        + "\n</mxfile>\n"
    )
