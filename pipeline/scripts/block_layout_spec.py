#!/usr/bin/env python3
"""
block_layout_spec.py -- ブロック型ごとのレイアウト定義

各ブロック型について以下を定義:
  - size: (w_cells, h_cells) ブロックが占めるグリッドセル数
  - slots: {内部モジュール役割名: (col_offset, row_offset)} ブロックトップ基準の相対セル座標
         col_offset / row_offset は 0 から始まる整数インデックス

scaffold_generator.py が生成するモジュール構造と完全に同期していること。

使い方:
    from block_layout_spec import BLOCK_SPECS, cell_to_px, BLOCK_VPAD, BLOCK_HPAD
    spec = BLOCK_SPECS["hearing_echo"]
    x, y = cell_to_px(block_top_col + spec.slots["TTS"][0],
                      block_top_row + spec.slots["TTS"][1])
"""

from dataclasses import dataclass, field

# ─── グリッド定数 ─────────────────────────────────────────────────
# 1 セルのピクセル寸法（Brekeke Flow Designer の推奨モジュール間隔に合わせる）
CELL_WIDTH  = 180     # モジュール本体の幅
CELL_HEIGHT = 150     # モジュール間の縦方向ピッチ

# save-* サブモジュールのオフセット（メイン層から見た相対ピクセル）
SUB_OFFSET_X = 220
SUB_OFFSET_Y = 30

# ブロック間のパディング（ブロックトップから次のブロックトップまで）
BLOCK_VPAD = 80       # 縦方向のブロック間余白
BLOCK_HPAD = 100      # 横方向のブロック間余白

# 1 ブロックが横方向に確保するセル幅（主層 1 + 副層 1 = 2 セル相当）
COLS_PER_BLOCK = 2


# ─── ブロックレイアウト仕様 ─────────────────────────────────────────
@dataclass
class BlockSpec:
    """ブロック型ごとのレイアウト仕様"""
    name: str
    size: tuple[int, int]                     # (横セル数, 縦セル数)
    slots: dict[str, tuple[int, int]] = field(default_factory=dict)
    # 役割名 → (col, row) の相対セル座標。基本的に主層は col=0、副層は col=1
    # save-* サブモジュールは本体と同じ col/row に +SUB_OFFSET_{X,Y} で描画する前提


# 主モジュール名は scaffold_generator.py の build_*() 関数と同期させること
# slot の key は「役割ラベル」。実際のモジュール名は命名規則に従って動的生成される

# opening: wait → ContextModel → incoming-classifier → acceptance_times
OPENING = BlockSpec(
    name="opening",
    size=(1, 4),
    slots={
        "wait":                  (0, 0),
        "ContextModel":          (0, 1),
        "incoming-classifier":   (0, 2),
        "acceptance_times":      (0, 3),
    },
)

# announcement: TTS + save-TTS
ANNOUNCEMENT = BlockSpec(
    name="announcement",
    size=(2, 2),
    slots={
        "TTS":  (0, 0),
        # save-TTS は同じセル位置に SUB_OFFSET で付く（slot としては TTS と同じ）
        # 定数セット手段（save_to + save_value 指定時）の saveContext2DB
        "設定":  (1, 0),
    },
)

# hearing (echo_back なし)
# 視覚規約（2026-07-19 確定・施設担当者フィードバック）: 「thẳng hàng」= 同一列（縦に積む）。
#   - col0: Retry（単独列・TTS/STTの列より左）
#   - col1: TTS と STT は同一列（縦に積む。TTS が上、STT がその下）
#   - col2: Script/OpenAI 判定系はすべて同一列に集約（縦一列＝「判定はここ」visual）
#   - col3: save2db 等の保存・補助系
# 多段分岐: CMR_群1〜群10(row=6, col=0〜9) — 条件数>6 のときのみ使用
HEARING_SIMPLE = BlockSpec(
    name="hearing_simple",
    size=(10, 7),
    slots={
        "Retry":            (0, 0),
        "TTS":              (1, 0),
        "STT":              (1, 1),
        # 決定論スクリプト/OpenAI 判定系（col2 に集約・縦一列）
        "OpenAI":           (2, 0),
        "repeat_filter":    (2, 1),
        "script_fallback":  (2, 2),
        "script_answer":    (2, 3),
        "script_群分類":     (2, 4),
        # 保存・補助系（col3 にまとめる）
        "save2db":          (3, 0),
        "saveDefault_STT":  (3, 1),
        "saveDefault_OAI":  (3, 2),
        "save2db_登録なし":  (3, 3),
        "FAQ回答":           (3, 4),
        # 多段分岐（条件数 > スロット上限の場合のみ使用）
        "CMR_群1":          (0, 6),
        "CMR_群2":          (1, 6),
        "CMR_群3":          (2, 6),
        "CMR_群4":          (3, 6),
        "CMR_群5":          (4, 6),
        "CMR_群6":          (5, 6),
        "CMR_群7":          (6, 6),
        "CMR_群8":          (7, 6),
        "CMR_群9":          (8, 6),
        "CMR_群10":         (9, 6),
    },
)

# hearing (echo_back あり)
# HEARING_SIMPLE と同じ列構成（col0=Retry / col1=TTS+STT / col2=Script+OpenAI / col3=save系）を
# 「主質問」「復唱（再確認）」の2ターンぶん、同じ列のまま row を下へ伸ばして積む
# （列の役割は1ブロック通して固定＝「左列＝リトライ全部」「中列＝聞く系全部」
#   「右列＝判定系全部」という一貫した visual にする）。
# 言い直しサルベージ（否定+訂正の複合発話から再抽出・INC-260716-2）は既存 STT の
# raw text を再解析するだけの Script 1個のみ（専用 TTS/STT/Retry は伴わない）ため col2 に置く。
HEARING_ECHO = BlockSpec(
    name="hearing_echo",
    size=(10, 9),
    slots={
        # col0: Retry 系（主質問→row0 / 復唱→row2）
        "Retry":            (0, 0),
        "Retry_復唱":       (0, 2),
        # col1: TTS/STT 系（主質問→row0-1 / 復唱→row2-3）
        "TTS":              (1, 0),
        "STT":              (1, 1),
        "復唱":              (1, 2),
        "STT_復唱":          (1, 3),
        # col2: 決定論スクリプト/OpenAI 判定系（縦一列に集約）
        "OpenAI":           (2, 0),
        "repeat_filter":    (2, 1),
        "OpenAI_復唱":      (2, 2),
        "言い直しサルベージ": (2, 3),
        "script_fallback":  (2, 4),
        "script_answer":    (2, 5),
        "script_群分類":     (2, 6),
        # col3: 保存・補助系
        "save2db":          (3, 0),
        "save2db_復唱":      (3, 1),
        "saveDefault_STT":  (3, 2),
        "saveDefault_OAI":  (3, 3),
        "save2db_登録なし":  (3, 4),
        "FAQ回答":           (3, 5),
        # enum + echo_back の場合の合流 CMR
        "CMR_復唱後":        (1, 7),
        # 多段分岐（条件数 > スロット上限の場合のみ使用）
        "CMR_群1":          (0, 8),
        "CMR_群2":          (1, 8),
        "CMR_群3":          (2, 8),
        "CMR_群4":          (3, 8),
        "CMR_群5":          (4, 8),
        "CMR_群6":          (5, 8),
        "CMR_群7":          (6, 8),
        "CMR_群8":          (7, 8),
        "CMR_群9":          (8, 8),
        "CMR_群10":         (9, 8),
    },
)

# hearing (input_method: dtmf_split, Pattern C): DTMF 分離
# 同じ列規約（col0=Retry / col1=TTS+STT / col2=Script・OpenAI）を適用。
# DTMF 分岐: save_label_0..N を row 2 で横並び
HEARING_DTMF_SPLIT = BlockSpec(
    name="hearing_dtmf_split",
    size=(10, 3),
    slots={
        "Retry":     (0, 0),
        "TTS":       (1, 0),
        "STT":       (1, 1),       # STT-DTMF
        "OpenAI":    (2, 0),       # 発話路
        "repeat_filter": (2, 1),
        "save2db":   (3, 0),
        # save_label_0..9 (Pattern C 専用)
        "save_label_0":  (0, 2),
        "save_label_1":  (1, 2),
        "save_label_2":  (2, 2),
        "save_label_3":  (3, 2),
        "save_label_4":  (4, 2),
        "save_label_5":  (5, 2),
        "save_label_6":  (6, 2),
        "save_label_7":  (7, 2),
        "save_label_8":  (8, 2),
        "save_label_9":  (9, 2),
    },
)

# cmr_chain (Pattern C 後段): CMR を縦に N 個積む
CMR_CHAIN = BlockSpec(
    name="cmr_chain",
    size=(1, 10),
    slots={f"cmr_chain_{i}": (0, i) for i in range(10)},
)

# subflow: 単一 jump_XXX
SUBFLOW = BlockSpec(
    name="subflow",
    size=(1, 1),
    slots={"jump": (0, 0)},
)

# context_match_router / script / date_of_call_classifier / call_transfer
SINGLE_BOX = BlockSpec(
    name="single_box",
    size=(1, 1),
    slots={"box": (0, 0)},
)

# ─── slot ブロック型 ─────────────────────────────────────────────────────
# scaffold_generator._build_slot() が生成するモジュール列と同期させること。
# save-* 副層は col=1 に SUB_OFFSET で付く前提のため slots に含めない。

# slot: patient_name — TTS + STT(氏名カナ) + Retry
SLOT_PATIENT_NAME = BlockSpec(
    name="slot_patient_name",
    size=(2, 7),
    slots={
        "TTS":     (0, 0),
        "save2db": (1, 0),
        "STT":     (0, 1),
        "Retry":   (0, 2),
        # 全音声入力ブロック共通: もう一度/待って検出（STT→[repeat_filter]→次）
        "repeat_filter": (1, 1),
        # echo_back: true 明示時のみ生成される確認チェーン（date_of_birth と同一命名・
        # scaffold_generator._build_slot 内 slot=="patient_name" の echo_back 分岐）
        "DOB_reconf":    (0, 3),
        "confirm_STT":   (0, 4),
        "confirm_Retry": (0, 5),
        "yes_no_script": (0, 6),
    },
)

# slot: date_of_birth — TTS + DTMF_STT + Retry + DOB_reconf + confirmSTT + confirmRetry + yes_no_script
# + 言い直しサルベージ（否定+訂正の複合発話を再確認する1回のみのループ・INC-260716-2）
SLOT_DATE_OF_BIRTH = BlockSpec(
    name="slot_date_of_birth",
    size=(2, 11),
    slots={
        "TTS":           (0, 0),
        "save2db":       (1, 0),
        "STT":           (0, 1),
        "Retry":         (0, 2),
        "DOB_reconf":    (0, 3),
        "confirm_STT":   (0, 4),
        "confirm_Retry": (0, 5),
        "yes_no_script": (0, 6),
        # 全音声入力ブロック共通: もう一度/待って検出（STT→[repeat_filter]→次）
        "repeat_filter": (1, 1),
        # 言い直しサルベージ: 復唱_言い直し(DOBノード) → 入力_再確認 → リトライ_再確認 →
        # script_再確認分類（save-{step}_再確認 は confirm_STT_sv の副層）
        "DOB_reconf_sv":    (0, 7),
        "confirm_STT_sv":   (0, 8),
        "confirm_Retry_sv": (0, 9),
        "yes_no_script_sv": (0, 10),
    },
)

# slot: phone v2（docs/specs/slot_phone_v2.md）— 3 列構造（2026-07-19 施設担当者
# フィードバック: ANI路と連絡先路が隣接して密着していたのを、中央の incoming
# classifier を軸に左右対称へ変更）:
#   col=0（左）: ANI 路（PhoneNorm CASE B → 復唱 TTS → 確認 STT → retry → yes_no）
#   col=1（中央）: 着信分類(incoming) + save2db — 2つの路の起点として中心に配置
#   col=2（右）: 連絡先路
#   nashi_mrb (row=4, col=2) は next_no_phone 指定時のみ使用（省略可）
#   AI_TALK 施設は echo_*（外部復唱 TTS）が生成されない（module prompt 読み）— 欠けても整合
SLOT_PHONE = BlockSpec(
    name="slot_phone",
    size=(3, 15),
    slots={
        # 中央 (col=1): 着信分類 → 2路の分岐起点。save2db も中央（両路共有のため）
        "incoming":          (1,  0),
        "save2db":           (1,  1),
        # ANI 路 (col=0・左): PhoneNorm CASE B → 復唱 TTS → 確認 STT → retry → yes_no
        "norm_ANI":          (0,  0),
        "echo_ANI":          (0,  1),
        "confirm_STT_ANI":   (0,  2),
        "retry_ANI_confirm": (0,  3),
        "script_ANI":        (0,  4),
        # ANI サルベージ（言い直し番号・1回のみ）
        "norm_ANI_sv":       (0,  5),
        "echo_ANI_sv":       (0,  6),
        "confirm_STT_ANI_sv": (0, 7),
        "retry_ANI_sv":      (0,  8),
        "script_ANI_sv":     (0,  9),
        # リトライ枯渇フォールバック（ANI 採用 → next）
        "fallback_set":      (0, 10),
        # 全音声入力ブロック共通: もう一度/待って検出（STT→[repeat_filter]→次）
        "repeat_filter":         (0, 11),   # 電話番号(base) STT の直後
        "repeat_filter_連絡先":   (2, 11),   # 連絡先 STT の直後（連絡先路の列）
        # 連絡先 路 (col=2・右)
        "TTS_renrakusaki":   (2,  0),
        "STT_renrakusaki":   (2,  1),
        "retry_renrakusaki": (2,  2),
        "norm_renrakusaki":  (2,  3),
        "nashi_mrb":         (2,  4),   # next_no_phone 指定時のみ使用
        "echo_renrakusaki":  (2,  5),
        "confirm_STT_ren":   (2,  6),
        "retry_ren_confirm": (2,  7),
        "script_ren":        (2,  8),
        # 連絡先サルベージ（言い直し番号・1回のみ）
        "norm_ren_sv":       (2,  9),
        "echo_ren_sv":       (2, 10),
        "confirm_STT_ren_sv": (2, 12),
        "retry_ren_sv":      (2, 13),
        "script_ren_sv":     (2, 14),
    },
)

# slot: card_number — TTS + STT + Retry + script + echoTTS + echoSTT + echoRetry + echoScript
# + 言い直しサルベージ（否定+訂正の複合発話から番号を再抽出する1回のみのループ・INC-260716-2。
# date_of_birth と役割は同型だが、抽出 Script が独立モジュールな点のみ異なる）
SLOT_CARD_NUMBER = BlockSpec(
    name="slot_card_number",
    size=(2, 12),
    slots={
        "TTS":          (0, 0),
        "save2db":      (1, 0),
        "STT":          (0, 1),
        "Retry":        (0, 2),
        "script":       (0, 3),
        "echo_TTS":     (0, 4),
        "echo_STT":     (0, 5),
        "echo_Retry":   (0, 6),
        "echo_script":  (0, 7),
        # 全音声入力ブロック共通: もう一度/待って検出（STT→[repeat_filter]→次）
        "repeat_filter": (1, 1),
        # 言い直しサルベージ: script_言い直し(抽出) → 復唱_言い直し → 入力_再確認 →
        # script_再確認判定（save-{step}_再確認 は salvage_STT の副層）
        "salvage_extract": (0, 8),
        "salvage_TTS":     (0, 9),
        "salvage_STT":     (0, 10),
        "salvage_judge":   (0, 11),
    },
)

# termination: 完了フラグ → END_TTS → 切断 の縦 3 段 (save-END は副層)
TERMINATION = BlockSpec(
    name="termination",
    size=(1, 3),
    slots={
        "完了フラグ":  (0, 0),
        "END_TTS":     (0, 1),
        "切断":        (0, 2),
    },
)

# ─── ブロック型 → spec の索引 ──────────────────────────────────────
BLOCK_SPECS: dict[str, BlockSpec] = {
    "opening":                 OPENING,
    "announcement":            ANNOUNCEMENT,
    "hearing_simple":          HEARING_SIMPLE,
    "hearing_echo":            HEARING_ECHO,
    "hearing_dtmf_split":      HEARING_DTMF_SPLIT,
    "subflow":                 SUBFLOW,
    "context_match_router":    SINGLE_BOX,
    "script":                  SINGLE_BOX,
    "date_of_call_classifier": SINGLE_BOX,
    "call_transfer":           SINGLE_BOX,
    "termination":             TERMINATION,
    "cmr_chain":               CMR_CHAIN,
    # slot 型（slot_kind ごとに分離）
    "slot_patient_name":       SLOT_PATIENT_NAME,
    "slot_date_of_birth":      SLOT_DATE_OF_BIRTH,
    "slot_phone":              SLOT_PHONE,
    "slot_card_number":        SLOT_CARD_NUMBER,
}


def get_block_spec(block_type: str, echo_back: bool = False,
                    input_method: str = "voice_only",
                    slot_kind: str = "") -> BlockSpec:
    """block type + echo_back/input_method/slot_kind フラグから該当 spec を返す"""
    if block_type in ("hearing", "intent", "free_text", "clinical_department", "faq"):
        if input_method == "dtmf_split":
            return HEARING_DTMF_SPLIT
        return HEARING_ECHO if echo_back else HEARING_SIMPLE
    if block_type == "slot":
        return BLOCK_SPECS.get(f"slot_{slot_kind}", SINGLE_BOX)
    return BLOCK_SPECS.get(block_type, SINGLE_BOX)


def cell_to_px(col: int, row: int) -> tuple[int, int]:
    """セル座標 (col, row) をピクセル座標 (x, y) に変換"""
    x = col * (CELL_WIDTH + BLOCK_HPAD)
    y = row * CELL_HEIGHT
    return x, y


def block_top_px(block_col: int, block_row: int) -> tuple[int, int]:
    """ブロック配置グリッドの (col, row) をピクセル座標に変換。
    ブロック配置は COLS_PER_BLOCK セル単位で横方向に区切る。
    """
    x = block_col * COLS_PER_BLOCK * (CELL_WIDTH + BLOCK_HPAD)
    y = block_row * CELL_HEIGHT  # 縦は連続セル数で配置（ブロックごとの H を積算）
    return x, y
