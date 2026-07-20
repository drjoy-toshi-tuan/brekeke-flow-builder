# -*- coding: utf-8 -*-
"""triage_router — 受診相談 決定論トリアージ オラクル（Python 正本）。

JTAS / 総務省消防庁「電話相談」プロトコル準拠の Top-Down Exclusion カスケードを
純関数で実装する。LLM 不使用。同一入力→同一出力（乱数/時刻/IO なし）。

答えの取り方（浜口さん確定 2026-07-03）:
  - A ブロック（本当に救急かの一番最初）だけ閉じた Yes/No（abcd 引数で受ける）。
    A-0 CPA だけは閉じ質問ですらなく全テキストへのキーワード検知。
  - B（カテゴリ別 Red Flag）/ C（修飾因子）は **自由発話へのキーワード走査**（over-triage bias）。

出力: GOAL1_救急 / GOAL2_看護師 / GOAL3_通常（＋監査用 reason）。

詳細仕様: REQUIREMENTS.md ／ ../../output/scenarios/商談デモ_フリー発話受付/受診相談_トリアージ判定仕様_20260703.md
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

GOAL1 = "GOAL1_救急"
GOAL2 = "GOAL2_看護師"
GOAL3 = "GOAL3_通常"

# ---- A-0: CPA（心肺停止）語。全テキストへ検知 → 即 GOAL1 -------------------
# 否定形は「ない/なし/ません/てない」等のゆれを吸収（実発話は促音便・丁寧形が普通）。
_CPA = re.compile(
    r"((呼吸|息).{0,5}(ない|なし|ませ|てな)|呼吸なし|"
    r"脈.{0,4}(ない|なし|ませ)|心臓.{0,3}止ま|心停止|冷たくな(って|り|)|"
    r"水没|沈んで|おぼれ|溺れ)"
)

# ---- A-1..A-4: ABCD（閉じた Yes/No）。yes / unclear = 危険側 ----------------
ABCD_KEYS = ("A1_意識", "A2_気道", "A3_呼吸", "A4_循環")

# ---- 主訴カテゴリ分類（自由発話への包含・優先順で先勝ち） -------------------
CATEGORIES = ("頭痛めまい", "胸痛", "外傷出血", "腹痛", "発熱")  # この順で先勝ち。全外れ=その他
_CATEGORY_RE = {
    "頭痛めまい": re.compile(r"(頭.{0,10}痛|頭痛|あたま.{0,10}痛|めまい|眩暈|くらくら|ふらつき|立ちくらみ)"),
    "胸痛": re.compile(r"(胸.{0,5}痛|胸痛|胸.{0,5}苦し|動悸)"),
    "外傷出血": re.compile(r"(けが|怪我|切った|切って|ぶつけ|打った|打撲|出血|血が出|骨折|転ん|転倒|やけど|火傷|捻挫|刺され|咬まれ|噛まれ)"),
    "腹痛": re.compile(r"(腹.{0,5}痛|お腹.{0,5}痛|腹痛|胃.{0,5}痛|下腹|みぞおち)"),
    "発熱": re.compile(r"(発熱|高熱|微熱|寒気|悪寒|熱っぽ|熱.{0,3}(あ|で|出|高|つ)|(38|39|40|41|42)度)"),
}

# ---- B: カテゴリ別 Red Flag（自由発話走査・発火で GOAL1）--------------------
# {カテゴリ: [(flag_id, pattern), ...]}。data-driven（語彙拡張は表を足すだけ）。
RED_FLAGS: dict[str, list[tuple[str, re.Pattern]]] = {
    "頭痛めまい": [
        ("突発激痛", re.compile(r"(突然|急に|いきなり|バット|殴られ)")),
        ("最悪の痛み", re.compile(r"(今まで.{0,4}(ない|無い)|人生で|経験.{0,4}(ない|無い)|最悪|かつてない)")),
        ("増悪", re.compile(r"(だんだん.{0,3}(強|ひど)|どんどん.{0,3}痛|強くなっ|悪化)")),
        ("神経脱落", re.compile(r"(しびれ|痺れ|力が?入らな|麻痺|動かせな)")),
        ("意識言語", re.compile(r"(ろれつ|呂律|変なこと|焦点.{0,3}合わ|意識.{0,4}(もうろう|ぼんやり|おかし))")),
        ("嘔吐", re.compile(r"(吐いた|嘔吐|吐き気がひど|強い吐き気)")),
        ("視覚異常", re.compile(r"(見えな|かすむ|二重に見え|視野が?欠け)")),
    ],
    "胸痛": [
        ("突発持続", re.compile(r"(突然.{0,4}(始ま|痛)|急に.{0,3}痛|いきなり)")),
        ("放散痛", re.compile(r"((首|あご|顎|肩|肩甲骨|背中|腕).{0,6}(痛|広が|放散|しびれ|だる))|放散")),
        ("安静時痛", re.compile(r"(安静|じっと|寝て.{0,3}痛|動かなくても|何もしなくても)")),
        ("冷汗", re.compile(r"(冷や?汗|脂汗|汗が?止まらな)")),
        ("薬無効", re.compile(r"(ニトロ|舌下|(薬|くすり).{0,4}(効か(な|ず)|効きませ|効いてな|治ま(らな|りませ|らず)))")),
        ("ピル", re.compile(r"(ピル|避妊薬|経口避妊)")),
        ("DVT", re.compile(r"((足|脚|ふくらはぎ|足首).{0,4}(腫れ|むくみ))|長.{0,3}座|エコノミー")),
    ],
    "腹痛": [
        ("激痛", re.compile(r"(激し|激痛|今まで.{0,4}(ない|無い)|のたうち|耐えられ)")),
        ("胸背部併発", re.compile(r"((胸|背中).{0,4}痛)")),
        ("ヘルニア嵌頓", re.compile(r"(こぶ|しこり|(足の付け根|股|そけい|鼠径).{0,4}(出|腫れ|膨ら))")),
        ("頭痛併発", re.compile(r"(頭が?痛|頭痛)")),
    ],
    "発熱": [
        ("高熱薬無効", re.compile(r"((39|40|４０|３９|４１|41).{0,2}度|(解熱|薬|くすり).{0,4}効かな|高熱)")),
        ("意識障害", re.compile(r"(意識.{0,4}(もうろう|ぼんやり|おかし)|もうろう)")),
        ("神経症状", re.compile(r"((手足|腕|足).{0,4}(動か|感覚)|しびれ|麻痺)")),
        ("けいれん", re.compile(r"(けいれん|痙攣|ひきつけ)")),
        ("基礎疾患", re.compile(r"(心臓|肝臓|糖尿|透析|持病|治療中|免疫)")),
        ("脱水", re.compile(r"(尿.{0,4}(出な|少な|減)|(唇|皮膚).{0,3}乾|水分.{0,3}(取れ|摂れ)な|脱水|ぐったり)")),
    ],
    "外傷出血": [
        ("気道腫脹", re.compile(r"((喉|のど|舌).{0,3}腫れ|息.{0,3}(しづら|苦し))")),
        ("髄液漏", re.compile(r"((透明|さらさら).{0,4}(鼻水|耳)|耳だれ|髄液)")),
        ("複視", re.compile(r"(二重に見え|複視|見え方.{0,3}(おかし|変))")),
        ("阻血肢", re.compile(r"((指先|手足|足先|患部).{0,5}(冷た|青ざめ|白く|紫))")),
        ("開放骨折", re.compile(r"(骨.{0,3}(見え|出て)|開放骨折)")),
        ("止血不能", re.compile(r"((圧迫|押さえ).{0,6}(止ま|出血)|血.{0,4}止ま(らな|りませ|ませ|らず)|大量.{0,3}出血)")),
    ],
}

# ---- 共通致死語（カテゴリ非依存・常時走査。A系サインを取りこぼさない）------
COMMON_LETHAL: list[tuple[str, re.Pattern]] = [
    ("意識障害", re.compile(r"(意識が?(ない|もうろう|ぼんやり|遠のく)|反応が?(ない|薄)|呼びかけ.{0,4}反応)")),
    ("呼吸困難", re.compile(r"(息が?(できな|苦し)|呼吸.{0,3}(困難|苦し)|息が?荒)")),
    ("けいれん", re.compile(r"(けいれん|痙攣|ひきつけ)")),
    ("麻痺", re.compile(r"(ろれつ|呂律|半身.{0,3}(動か|しびれ)|片側.{0,3}(動か|しびれ)|顔.{0,3}(ゆがみ|下が))")),
    ("大量出血", re.compile(r"(大量.{0,3}出血|血が?(止まらな|どくどく|噴)|血だらけ)")),
    ("冷汗", re.compile(r"(冷や?汗|脂汗)")),
    ("突発激痛", re.compile(r"(突然|急に|いきなり).{0,10}(激痛|激し|ひどい?痛|殴られ|割れる|バット|耐えられ)")),
    ("最悪の痛み", re.compile(r"((今まで|人生|かつて).{0,6}(ない|無い).{0,6}痛|最悪.{0,4}痛|経験.{0,4}(ない|無い).{0,6}痛)")),
]

# ---- C: 修飾因子（自由発話走査・発火で GOAL2）------------------------------
MODIFIERS: list[tuple[str, re.Pattern]] = [
    ("歩行不能", re.compile(r"(歩けな|歩けませ|立てな|立ち上がれ|動けな)")),
    ("高齢", re.compile(r"((6[5-9]|[7-9][0-9]|1[01][0-9]).{0,1}(歳|才)|高齢|お年寄)")),
    ("小児", re.compile(r"((?<![0-9])[0-5](歳|才)|乳児|赤ちゃん|生後|新生児)")),
    ("妊娠", re.compile(r"(妊娠|妊婦|おめでた)")),
    ("抗凝固薬", re.compile(r"(血.{0,3}(さらさら|サラサラ)|ワー?ファリン|ワルファリン|抗凝固|血液.{0,3}(薬|くすり)|DOAC|バイアスピリン|イグザレルト|エリキュース)")),
    ("止血困難", re.compile(r"((30分|三十分|ずっと).{0,5}(出血|血)|コップ.{0,2}(1|一)杯|止まらな.{0,3}(出血|血))")),
    ("局所処置", re.compile(r"((あご|顎).{0,4}(外れ|動かな|開かな)|(腫れ|痛み).{0,4}広が|蜂窩織炎)")),
    ("歯科ハイリスク", re.compile(r"(歯.{0,6}(心臓|糖尿)|歯.{0,4}(抜け|折れ).{0,6}(血.{0,3}薬|さらさら|抗凝固))")),
]


@dataclass
class TriageResult:
    goal: str
    block: str            # A0 / A / B / C / D
    reason: str           # 発火根拠（監査）
    category: str = ""    # 主訴カテゴリ（分類できた場合）
    fired: list[str] = field(default_factory=list)  # 発火フラグ一覧

    def as_dict(self) -> dict:
        return {"goal": self.goal, "block": self.block, "reason": self.reason,
                "category": self.category, "fired": self.fired}


def normalize(s: str) -> str:
    """NFKC 正規化（全半角/カナ/互換ゆれ吸収）＋空白畳み。既存部品と同方式。"""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"\s+", "", s)


def detect_cpa(text: str) -> bool:
    return bool(_CPA.search(normalize(text)))


def abcd_positive(abcd: dict | None) -> tuple[bool, list[str]]:
    """A1..A4 のうち yes / unclear（=安全側で危険扱い）を発火として返す。"""
    fired: list[str] = []
    if not abcd:
        return False, fired
    for k in ABCD_KEYS:
        v = (abcd.get(k) or "no").strip().lower()
        if v in ("yes", "unclear"):
            fired.append(k if v == "yes" else f"{k}(unclear)")
    return bool(fired), fired


def classify_complaint(text: str) -> str:
    t = normalize(text)
    for cat in CATEGORIES:
        if _CATEGORY_RE[cat].search(t):
            return cat
    return "その他"


def scan_red_flags(category: str, text: str) -> list[str]:
    """カテゴリ別 Red Flag ＋ 共通致死語 を自由発話へ走査。発火 flag_id 一覧。"""
    t = normalize(text)
    fired: list[str] = []
    for flag_id, pat in RED_FLAGS.get(category, []):
        if pat.search(t):
            fired.append(f"{category}/{flag_id}")
    for flag_id, pat in COMMON_LETHAL:
        if pat.search(t):
            tag = f"共通/{flag_id}"
            if tag not in fired:
                fired.append(tag)
    return fired


def scan_modifiers(text: str) -> list[str]:
    t = normalize(text)
    return [mid for mid, pat in MODIFIERS if pat.search(t)]


def triage(*, abcd: dict | None = None, complaint: str = "",
           free_texts: list[str] | None = None) -> TriageResult:
    """A→B→C→D カスケード（Top-Down Exclusion・短絡・ランクダウンなし）。"""
    free_texts = free_texts or []
    all_free = " ".join([complaint] + list(free_texts))

    # A-0: CPA（全テキスト）
    if detect_cpa(all_free):
        return TriageResult(GOAL1, "A0", "A-0:CPA語検知")

    # A-1..A-4: ABCD（閉じた Yes/No・unclear=危険側）
    pos, fired = abcd_positive(abcd)
    if pos:
        return TriageResult(GOAL1, "A", "A:" + ",".join(fired), fired=fired)

    # B: 主訴分類 → カテゴリ別 Red Flag ＋ 共通致死語（自由発話走査）
    category = classify_complaint(complaint)
    red = scan_red_flags(category, all_free)
    if red:
        return TriageResult(GOAL1, "B", "B:" + ",".join(red), category=category, fired=red)

    # C: 修飾因子（自由発話走査）
    mod = scan_modifiers(all_free)
    if mod:
        return TriageResult(GOAL2, "C", "C:" + ",".join(mod), category=category, fired=mod)

    # D: 全否定
    return TriageResult(GOAL3, "D", "D:全否定（危険サインなし）", category=category)


if __name__ == "__main__":
    # 手動確認用（生 PII は扱わない・合成発話のみ）
    demo = triage(complaint="胸が痛くて、腕にも広がってきて冷や汗が出ています")
    print(demo.as_dict())
