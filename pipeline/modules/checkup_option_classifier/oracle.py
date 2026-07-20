#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""受診オプション検査 抽出・正規化 オラクル（checkup_option_classifier / engine v3・universe）。

Brekeke @General$Script（script.js）と同一ロジックの Python 参照実装。LLM 不使用。
入力（STT結果テキスト）からオプション検査名を抽出・正規化する（複数抽出・マルチ）。

#274 で ITEMS を福井フラット（1施設）→ universe（被覆スコアカード reference/checkup/
universe_options.tsv・33種）へ差し替え、engine に facility_offered サブセットを追加（v2→v3）。
universe/facility_offered は department #263 と同型（施設非依存化＋配線でサブセット）。

出力は次のいずれか:
  - 正規化された検査名（複数は「、」区切り・ITEMS 定義順）
  - "不明"   … わからない等の不明意図
  - "無い"   … 追加なし意図
  - "復唱途中切断" … いずれにも該当しない

facility_offered（任意 set）指定時、universe で当たった canonical のうちサブセット外は除外
（配線＝施設が受けられるオプションだけ返す）。None＝universe（絞り込みなし）。

ランタイム差異の吸収:
  - script.js は Java.type("java.text.Normalizer").normalize() を使用
  - oracle.py は unicodedata.normalize("NFKC") を使用（同等）
  - strip リストと sound folds は完全同一
"""
import re
import unicodedata

# ===== @spec-begin =====

SOUND_FOLDS = [
    ("人間ロック","人間ドック"),("人間ドッグ","人間ドック"),("人間トック","人間ドック"),
    ("脳ロック","脳ドック"),("脳ドッグ","脳ドック"),
    ("心臓ロック","心臓ドック"),
    ("大腸ロック","大腸ドック"),("大腸ドッグ","大腸ドック"),
    ("肺ロック","肺ドック"),("肺ドッグ","肺ドック"),
    ("眼科ロック","眼科ドック"),("眼科ドッグ","眼科ドック"),
    ("レディースロック","レディースドック"),("レディースドッグ","レディースドック"),
    ("2日ロック","2日ドック"),("二日ロック","二日ドック"),("二日ドッグ","二日ドック"),
    ("日帰りロック","日帰りドック"),
]

FUMEI_PATTERN = re.compile(
    r"わからない|わかりません|わかんない|不明|当日決め|当日きめ|"
    r"まだ決め|まだきめ|決まっていない|決まってない|きまっていない|"
    r"決めていない|きめていない|相談したい|しょうだんしたい"
)

NAI_PATTERN = re.compile(
    r"追加しない|追加なし|ついかしない|ついかなし|不要|ふよう|"
    r"いらない|いりません|特にない|とくにない|ありません|"
    r"結構です|けっこうです|大丈夫です|だいじょうぶです|希望なし|希望はなし"
)

NEGATE_MARKERS = [
    "はいらない","はいりません","はいらん",
    "をキャンセル","はキャンセル","のキャンセル",
    "はやめ","をやめ",
    "は不要","は受けない","は受けません",
]

# universe オプション（reference/checkup/universe_options.tsv・正規化済みキーワード）。
# [canonical(出力ラベル・生), [post-normalized-keyword, ...]]。定義順＝マルチ出力の並び順。
ITEMS = [
    ("CEA", ["cea", "cea", "がん胎児性抗原"]),
    ("CA19-9", ["ca199", "ca199", "ca199", "膵臓マーカー"]),
    ("AFP", ["afp", "afp", "アルファフェトプロテイン", "肝臓マーカー"]),
    ("PSA（前立腺）", ["psa前立腺", "psa", "ぴーえすえー", "前立腺", "前立腺がん", "男性の血液検査"]),
    ("CA125（卵巣）", ["ca125卵巣", "ca125", "卵巣マーカー"]),
    ("腫瘍マーカーセット", ["腫瘍マーカーセット", "腫瘍マーカー", "血液のがん検査", "腫瘍マーカーセット", "腫瘍の検査"]),
    ("マンモグラフィ", ["マンモグラフィ", "マンモ", "マンモグラフィ", "乳房x線", "3dマンモ", "乳房レントゲン", "乳がん検診", "乳がん", "乳癌検診"]),
    ("乳腺超音波検査", ["乳腺超音波検査", "乳腺超音波", "乳腺エコー", "乳房超音波", "乳房エコー", "胸のエコー", "乳腺"]),
    ("経膣超音波検査", ["経膣超音波検査", "経膣エコー", "経腟超音波", "経膣超音波", "内診エコー"]),
    ("子宮頸がん検査", ["子宮頸がん検査", "子宮頸部細胞診", "子宮頸がん", "子宮頚がん", "頸がん検査", "子宮けいがん", "子宮がん検診", "子宮がん", "hpv"]),
    ("子宮体がん検査", ["子宮体がん検査", "子宮体がん", "子宮内膜", "体がん", "子宮たいがん"]),
    ("肝炎ウイルス検査", ["肝炎ウイルス検査", "肝炎ウイルス", "b型肝炎", "c型肝炎", "hbs", "hcv", "肝炎検査"]),
    ("性感染症・梅毒検査", ["性感染症梅毒検査", "性感染症", "梅毒", "sti", "tpha", "rpr"]),
    ("アレルギー検査", ["アレルギー検査", "アレルギー", "view39", "ビュー39", "特異的ige", "花粉"]),
    ("甲状腺検査", ["甲状腺検査", "甲状腺", "甲状腺ホルモン", "tsh", "ft3", "ft4", "サイログロブリン"]),
    ("エクオール検査", ["エクオール検査", "エクオール", "大豆イソフラボン"]),
    ("脳MRI・MRA", ["脳mrimra", "頭部mri", "mra", "脳mri", "脳血管撮影"]),
    ("下腹部MRI（骨盤腔）", ["下腹部mri骨盤腔", "下腹部mri", "骨盤mri", "骨盤腔mri"]),
    ("内臓脂肪CT", ["内臓脂肪ct", "内臓脂肪", "内臓脂肪ct", "メタボct"]),
    ("胸部CT（肺）", ["胸部ct肺", "胸部ct", "肺ct", "低線量ct", "肺の検査"]),
    ("冠動脈CT（心臓）", ["冠動脈ct心臓", "冠動脈ct", "心臓ct", "心臓の検査"]),
    ("骨密度検査（DEXA）", ["骨密度検査dexa", "骨密度", "dexa", "デキサ", "骨粗鬆症", "骨の検査"]),
    ("眼底・眼圧検査", ["眼底眼圧検査", "眼底", "眼圧", "緑内障", "眼底検査", "眼圧検査"]),
    ("胃内視鏡検査", ["胃内視鏡検査", "胃カメラ", "胃内視鏡", "上部消化管内視鏡"]),
    ("大腸内視鏡検査", ["大腸内視鏡検査", "大腸カメラ", "大腸内視鏡", "下部消化管内視鏡", "下のカメラ", "大腸ドック"]),
    ("睡眠時無呼吸検査", ["睡眠時無呼吸検査", "睡眠時無呼吸", "sas", "いびき", "無呼吸", "アプノモニター"]),
    ("動脈硬化検査", ["動脈硬化検査", "動脈硬化", "血管年齢", "血管の硬さ", "abi", "cavi"]),
    ("BNP検査", ["bnp検査", "bnp", "びーえぬぴー", "心不全の検査"]),
    ("肺機能検査", ["肺機能検査", "肺機能", "呼吸機能", "スパイロ", "息を吐く検査"]),
    ("ヘリコバクターピロリ菌検査", ["ヘリコバクターピロリ菌検査", "ピロリ", "ヘリコバクター", "ピロリ菌", "胃の血液検査"]),
    ("喀痰検査", ["喀痰検査", "喀痰", "かくたん", "痰の検査"]),
    ("マイクロアレイ血液検査", ["マイクロアレイ血液検査", "マイクロアレイ", "がんの血液検査", "遺伝子レベルの検査"]),
    ("転倒予防診断", ["転倒予防診断", "転倒予防", "身体バランス", "筋力チェック"]),
]

# 複合が構成単体を吸収（腫瘍マーカーセット ⊃ 個別マーカー）。universe レベルの SUBSUMES。
SUBSUMES = [
    ("腫瘍マーカーセット", ["CEA", "CA19-9", "AFP", "PSA（前立腺）", "CA125（卵巣）"]),
]

# ===== @spec-end =====

_STRIP_CHARS = set([
    "、","。","，","．",",",".","-","・","･",":","；","：","!","！","?","？","…","‥","〜","～",
    "「","」","『","』","(",")","（","）","[","]","【","】","<",">","＜","＞",
    "\"","'","“","”","‘","’","｢","｣","　"," ","\t","\r","\n",
])

def normalize(raw: str) -> str:
    if raw is None:
        return ""
    s = unicodedata.normalize("NFKC", str(raw))
    # full-width digits (already handled by NFKC, but explicit for parity)
    s = "".join(
        chr(ord(c) - 0xFEE0) if "０" <= c <= "９" else c for c in s
    )
    # ASCII alpha -> lowercase
    s = s.lower()
    # strip
    s = "".join(c for c in s if c not in _STRIP_CHARS)
    # sound folds
    for src, dst in SOUND_FOLDS:
        s = s.replace(src, dst)
    return s


def _build_negated(s: str) -> set:
    neg = set()
    for canon, kws in ITEMS:
        for kw in kws:
            for marker in NEGATE_MARKERS:
                if kw + marker in s:
                    neg.add(canon)
                    break
    return neg


def _match_items(s: str, negated: set, facility_offered=None) -> list:
    matched = []
    seen = set()
    for canon, kws in ITEMS:
        if canon in negated or canon in seen:
            continue
        for kw in kws:
            if kw in s:
                matched.append(canon)
                seen.add(canon)
                break
    # SUBSUMES: 複合コースが含まれる場合、構成単体を除外
    sub_excluded = set()
    for compound, constituents in SUBSUMES:
        if compound in seen:
            sub_excluded.update(constituents)
    out = [c for c in matched if c not in sub_excluded]
    # facility_offered サブセット（配線・None＝universe 絞り込みなし）
    if facility_offered is not None:
        out = [c for c in out if c in facility_offered]
    return out


def classify(raw: str, facility_offered=None) -> str:
    norm = normalize(raw)
    if not norm:
        return "復唱途中切断"

    has_fumei = bool(FUMEI_PATTERN.search(norm))
    has_nai   = bool(NAI_PATTERN.search(norm))
    negated   = _build_negated(norm)
    matched   = _match_items(norm, negated, facility_offered)

    if matched:
        return "、".join(matched)
    elif has_fumei:
        return "不明"
    elif has_nai:
        return "無い"
    else:
        return "復唱途中切断"


CANONICAL = [c for c, _ in ITEMS]


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for arg in sys.argv[1:]:
        print(f"{arg!r} -> {classify(arg)}")
