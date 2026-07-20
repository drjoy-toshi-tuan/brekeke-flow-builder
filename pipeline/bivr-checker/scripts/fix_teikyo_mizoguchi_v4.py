#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
帝京大学附属溝口病院 v4 修正スクリプト

Fix 1: DTMFモジュール profile_words 設定（11箇所）
Fix 2: 予約希望日 当日/翌日/明後日 → 代表電話案内 分岐追加
Fix 3: 変更/キャンセルルート順序変更（診療科 → 注射装具確認）
Fix 4: 用件確認からの距離圧縮（y >= 7000 を -4700シフト + 再配置）
"""

import json
import zipfile
import urllib.parse
import os

BASE = "G:/共有ドライブ/01_個人フォルダ🚩/09_AI電話事業部/髙橋翔太/bivr-checker"
FLOW_PATH = f"{BASE}/output/帝京大学付属溝口病院/fixed/flows/帝京溝口$診療_20260413.json"
OUT_BIVR = f"{BASE}/output/帝京大学付属溝口病院/帝京大学附属溝口病院_fixed.bivr"

with open(FLOW_PATH, "r", encoding="utf-8") as f:
    flow = json.load(f)

M = flow["modules"]

# ===========================================================================
# Fix 1: profile_words（DTMFモジュール）
# ===========================================================================

# 肯定否定共通辞書（はい/いいえ系）
YES_NO_WORDS = (
    "はい はい\n"
    "はい はあ\n"
    "はい あい\n"
    "はい い\n"
    "はーい はーい\n"
    "ええ ええ\n"
    "そうです そうです\n"
    "そうです おうです\n"
    "そうです うです\n"
    "はい、あります はいあります\n"
    "あります あります\n"
    "もちろん もちろん\n"
    "はい、そうです はいそうです\n"
    "いいえ いいえ\n"
    "いいえ いい\n"
    "ありません ありません\n"
    "いいえ、ありません いいえありません\n"
    "違います ちがいます\n"
    "ちがいます がいます\n"
    "違う ちがう\n"
    "なし なし\n"
    "いえ いえ\n"
    "いや いや\n"
    "ない ない\n"
    "わからない わからない\n"
    "わかりません わかりません"
)

# 用件確認（1〜5択 + テキスト）
YOUKEN_WORDS = (
    "予約 よやく\n"
    "よやく やく\n"
    "お願いしたい おねがいしたい\n"
    "ねがいしたい ねがいしたい\n"
    "受診したい じゅしんしたい\n"
    "しんしたい しんしたい\n"
    "診てほしい みてほしい\n"
    "初診 しょしん\n"
    "予約したい よやくしたい\n"
    "新規予約 しんきよやく\n"
    "変更 へんこう\n"
    "へんこう えんこう\n"
    "予約変更 よやくへんこう\n"
    "日程変更 にっていへんこう\n"
    "日にちを変えたい ひにちをかえたい\n"
    "時間を変えたい じかんをかえたい\n"
    "ずらしたい ずらしたい\n"
    "キャンセル きゃんせる\n"
    "きゃんせる やんせる\n"
    "キャンセルしたい きゃんせるしたい\n"
    "取消 とりけし\n"
    "とりけし りけし\n"
    "やめたい やめたい\n"
    "行けなくなった いけなくなった\n"
    "受診できなくなった じゅしんできなくなった\n"
    "予約確認 よやくかくにん\n"
    "かくにん かくにん\n"
    "確認したい かくにんしたい\n"
    "予約を確認 よやくをかくにん\n"
    "その他 そのた\n"
    "その他問合せ そのたといあわせ\n"
    "問い合わせ といあわせ\n"
    "聞きたい ききたい\n"
    "質問 しつもん\n"
    "わからない わからない\n"
    "一 いち\n"
    "二 に\n"
    "三 さん\n"
    "四 よん\n"
    "五 ご\n"
    "1番 いちばん\n"
    "2番 にばん\n"
    "3番 さんばん\n"
    "4番 よんばん\n"
    "5番 ごばん"
)

# 注射・装具確認（はい/いいえ + 関連語）
CHUSHASOUGU_WORDS = (
    "はい はい\n"
    "はい はあ\n"
    "はい あい\n"
    "はい い\n"
    "はーい はーい\n"
    "ええ ええ\n"
    "そうです そうです\n"
    "そうです おうです\n"
    "はい、あります はいあります\n"
    "あります あります\n"
    "注射 ちゅうしゃ\n"
    "ちゅうしゃ ゅうしゃ\n"
    "特定注射 とくていちゅうしゃ\n"
    "美容注射 びようちゅうしゃ\n"
    "装具 そうぐ\n"
    "そうぐ おうぐ\n"
    "コルセット こるせっと\n"
    "サポーター さぽーたー\n"
    "義肢 ぎし\n"
    "いいえ いいえ\n"
    "いいえ いい\n"
    "ありません ありません\n"
    "いいえ、ありません いいえありません\n"
    "違います ちがいます\n"
    "ない ない\n"
    "わからない わからない\n"
    "わかりません わかりません"
)

# 検査有無（はい/いいえ + 検査関連語）
KENSAKIMU_WORDS = (
    "はい はい\n"
    "はい はあ\n"
    "はい あい\n"
    "はい い\n"
    "ええ ええ\n"
    "そうです そうです\n"
    "そうです おうです\n"
    "はい、あります はいあります\n"
    "あります あります\n"
    "検査 けんさ\n"
    "けんさ えんさ\n"
    "CT しーてぃー\n"
    "MRI えむあーるあい\n"
    "レントゲン れんとげん\n"
    "エコー えこー\n"
    "いいえ いいえ\n"
    "いいえ いい\n"
    "ありません ありません\n"
    "いいえ、ありません いいえありません\n"
    "ない ない\n"
    "違います ちがいます\n"
    "わからない わからない\n"
    "わかりません わかりません"
)

# 術前検査（はい/いいえ + 術前関連語）
JIJUTSUZEN_WORDS = (
    "はい はい\n"
    "はい はあ\n"
    "はい あい\n"
    "はい い\n"
    "ええ ええ\n"
    "そうです そうです\n"
    "そうです おうです\n"
    "手術前 しゅじゅつまえ\n"
    "じゅつまえ じゅつまえ\n"
    "術前 じゅつぜん\n"
    "手術の前 しゅじゅつのまえ\n"
    "オペ前 おぺまえ\n"
    "術前検査 じゅつぜんけんさ\n"
    "いいえ いいえ\n"
    "いいえ いい\n"
    "そうではありません そうではありません\n"
    "違います ちがいます\n"
    "ない ない\n"
    "わからない わからない\n"
    "わかりません わかりません"
)

# 時間指定（はい/いいえ + 時間指定関連語）
JIKANTEI_WORDS = (
    "はい はい\n"
    "はい はあ\n"
    "はい あい\n"
    "はい い\n"
    "ええ ええ\n"
    "そうです そうです\n"
    "そうです おうです\n"
    "時間指定 じかんしてい\n"
    "じかんしてい かんしてい\n"
    "時間があります じかんがあります\n"
    "はい、あります はいあります\n"
    "あります あります\n"
    "指定 していしてい\n"
    "いいえ いいえ\n"
    "いいえ いい\n"
    "ありません ありません\n"
    "いいえ、ありません いいえありません\n"
    "特にありません とくにありません\n"
    "ない ない\n"
    "わからない わからない\n"
    "わかりません わかりません"
)

# DTMFモジュール → profile_words マッピング
dtmf_profile_map = {
    "入力_診察券確認":        YES_NO_WORDS,
    "入力_本日予約確認":      YES_NO_WORDS,
    "入力_用件確認":          YOUKEN_WORDS,
    "入力_受診歴確認":        YES_NO_WORDS,
    "入力_前回と同じ確認":    YES_NO_WORDS,
    "入力_紹介状確認":        YES_NO_WORDS,
    "入力_注射装具_変更":     CHUSHASOUGU_WORDS,
    "入力_注射装具_キャンセル": CHUSHASOUGU_WORDS,
    "入力_検査有無":          KENSAKIMU_WORDS,
    "入力_術前検査":          JIJUTSUZEN_WORDS,
    "入力_時間指定":          JIKANTEI_WORDS,
}

fixed_count_1 = 0
for mod_name, words in dtmf_profile_map.items():
    if mod_name in M:
        M[mod_name]["params"]["profile_words"] = words
        fixed_count_1 += 1
        print(f"[Fix1] profile_words 設定: {mod_name}")
    else:
        print(f"[Fix1] WARNING: モジュール未発見: {mod_name}")

print(f"\n[Fix1] 完了: {fixed_count_1}/{len(dtmf_profile_map)} モジュール処理\n")


# ===========================================================================
# Fix 2: 予約希望日 当日/翌日/明後日 → 代表電話案内 分岐
# ===========================================================================

TOUJITSU_PROMPT_ADDITION = (
    "\n\n---\n\n"
    "## 【特殊判定：当日・翌日・明後日 → 代表電話案内】（最優先）\n\n"
    "STEP3の出力前に以下を確認する。\n"
    "ユーザーの発話が下記のいずれかに該当する場合は、日付正規化より優先して「要代表案内」を出力すること：\n\n"
    "### 当日パターン\n"
    "今日・本日・当日・今すぐ・今から・今日中・本日中\n\n"
    "### 翌日パターン\n"
    "明日・あす・翌日・明日中\n\n"
    "### 明後日パターン\n"
    "明後日・あさって\n\n"
    "→ 出力: 要代表案内\n\n"
    "※ただし「今月の○日」「今週の○曜日」など特定日付を指す場合は通常処理。\n"
    "※「上旬」「中旬」「下旬」「来週」「再来週」などの期間表現は通常処理。\n"
    "※「明日以降でお願いします」のように明日を下限として使う場合は通常処理。"
)

def add_toujitsu_branch(module_name):
    if module_name not in M:
        print(f"[Fix2] WARNING: モジュール未発見: {module_name}")
        return
    mod = M[module_name]
    # プロンプトに追記
    mod["params"]["prompt"] += TOUJITSU_PROMPT_ADDITION
    # ^.+$ の前に 要代表案内 条件を挿入
    new_next = []
    inserted = False
    for n in mod["next"]:
        if n["condition"] == "^.+$" and not inserted:
            new_next.append({
                "condition": "^要代表案内$",
                "label": "要代表案内",
                "nextModuleName": "完了フラグ_代表案内_本日"
            })
            inserted = True
        new_next.append(n)
    mod["next"] = new_next
    print(f"[Fix2] 当日/翌日/明後日 分岐追加: {module_name}")

add_toujitsu_branch("OpenAI_予約希望日")
add_toujitsu_branch("OpenAI_予約希望日_変更")
print()


# ===========================================================================
# Fix 3: 変更/キャンセルルート順序変更（診療科 → 注射装具確認）
# ===========================================================================

# 3-1: OpenAI_用件確認 の 変更/キャンセル分岐先を変更
for n in M["OpenAI_用件確認"]["next"]:
    if n["condition"] == "^変更$":
        old = n["nextModuleName"]
        n["nextModuleName"] = "診療科_聴取_変更"
        print(f"[Fix3] OpenAI_用件確認 ^変更$: {old} → 診療科_聴取_変更")
    elif n["condition"] == "^キャンセル$":
        old = n["nextModuleName"]
        n["nextModuleName"] = "診療科_聴取_キャンセル"
        print(f"[Fix3] OpenAI_用件確認 ^キャンセル$: {old} → 診療科_聴取_キャンセル")

# 3-2: OpenAI_診療科_変更 success → 注射装具確認_変更（旧: 検査有無確認）
for n in M["OpenAI_診療科_変更"]["next"]:
    if n["condition"] == "^.+$" and n.get("label") == "success":
        old = n["nextModuleName"]
        n["nextModuleName"] = "注射装具確認_変更"
        print(f"[Fix3] OpenAI_診療科_変更 success: {old} → 注射装具確認_変更")

# 3-3: OpenAI_注射装具_変更 ^.+$ → 検査有無確認（旧: 診療科_聴取_変更）
for n in M["OpenAI_注射装具_変更"]["next"]:
    if n["condition"] == "^.+$":
        old = n["nextModuleName"]
        n["nextModuleName"] = "検査有無確認"
        print(f"[Fix3] OpenAI_注射装具_変更 ^.+$: {old} → 検査有無確認")

# 3-4: OpenAI_診療科_キャンセル success → 注射装具確認_キャンセル（旧: 予約日_聴取_キャンセル）
for n in M["OpenAI_診療科_キャンセル"]["next"]:
    if n["condition"] == "^.+$" and n.get("label") == "success":
        old = n["nextModuleName"]
        n["nextModuleName"] = "注射装具確認_キャンセル"
        print(f"[Fix3] OpenAI_診療科_キャンセル success: {old} → 注射装具確認_キャンセル")

# 3-5: OpenAI_注射装具_キャンセル ^.+$ → 予約日_聴取_キャンセル（旧: 診療科_聴取_キャンセル）
for n in M["OpenAI_注射装具_キャンセル"]["next"]:
    if n["condition"] == "^.+$":
        old = n["nextModuleName"]
        n["nextModuleName"] = "予約日_聴取_キャンセル"
        print(f"[Fix3] OpenAI_注射装具_キャンセル ^.+$: {old} → 予約日_聴取_キャンセル")

print()


# ===========================================================================
# Fix 4: レイアウト調整
# ===========================================================================

# 4-1: y >= 7000 を全て -4700 シフト（用件確認からの距離を圧縮）
shifted = 0
for mod_name, mod in M.items():
    y = mod["layout"].get("y", 0)
    if y >= 7000:
        mod["layout"]["y"] = y - 4700
        shifted += 1
print(f"[Fix4] 一括シフト(-4700): {shifted} モジュール処理")

# 4-2: 順序変更の影響で位置がずれたモジュールを手動再配置
# 背景:
#   変更ルート: 注射装具確認_変更 は y=7721 → 3021（シフト後）だが、
#               新1st step の 診療科_聴取_変更 が y=4051 なので注射装具は y=5000+ でないといけない
#   キャンセルルート: 注射装具確認_キャンセル は y=2700（シフト対象外）なので
#               診療科_聴取_キャンセル(y=4051)の下に移す必要がある

layout_overrides = {
    # ── 変更ルート：注射装具グループ（新2nd step, y=5000〜5300）──
    "注射装具確認_変更":          {"x": -600,  "y": 5000},
    "save-注射装具確認_変更":     {"x": -300,  "y": 5000},
    "入力_注射装具_変更":         {"x": -600,  "y": 5130},
    "OpenAI_注射装具_変更":       {"x": -600,  "y": 5300},
    "リトライ_注射装具_変更":     {"x": -880,  "y": 5300},
    "save-リトライ_注射装具_変更":{"x": -1100, "y": 5300},

    # ── 変更ルート：検査有無グループ（新3rd step, y=5600〜5730）──
    "検査有無確認":               {"x": -600,  "y": 5600},
    "save-検査有無確認":          {"x": -300,  "y": 5600},
    "入力_検査有無":              {"x": -600,  "y": 5730},

    # ── キャンセルルート：注射装具グループ（新2nd step, y=5000〜5300）──
    "注射装具確認_キャンセル":          {"x": -2110, "y": 5000},
    "save-注射装具確認_キャンセル":     {"x": -1810, "y": 5000},
    "入力_注射装具_キャンセル":         {"x": -1810, "y": 5130},
    "OpenAI_注射装具_キャンセル":       {"x": -1800, "y": 5300},
    "リトライ_注射装具_キャンセル":     {"x": -2080, "y": 5300},
    "save-リトライ_注射装具_キャンセル":{"x": -2300, "y": 5300},

    # ── キャンセルルート：予約日グループ（新3rd step, y=5600〜5730）──
    "予約日_聴取_キャンセル":          {"x": -1800, "y": 5600},
    "save-予約日_聴取_キャンセル":     {"x": -1500, "y": 5600},
    "入力_予約日_キャンセル":          {"x": -1800, "y": 5730},
}

override_count = 0
for mod_name, coords in layout_overrides.items():
    if mod_name in M:
        M[mod_name]["layout"] = coords
        override_count += 1
        print(f"[Fix4] 座標上書き: {mod_name} → x={coords['x']}, y={coords['y']}")
    else:
        print(f"[Fix4] (skip) モジュール未発見: {mod_name}")

print(f"\n[Fix4] 完了: {override_count} モジュール再配置\n")


# ===========================================================================
# 出力: JSON保存
# ===========================================================================
with open(FLOW_PATH, "w", encoding="utf-8") as f:
    json.dump(flow, f, ensure_ascii=False, indent=2)
print(f"[OUTPUT] JSON保存: {FLOW_PATH}")


# ===========================================================================
# 出力: .bivr ビルド
# ===========================================================================
flow_name = flow["name"]  # 帝京溝口$診療_20260413
encoded_name = urllib.parse.quote(flow_name, safe="")
txt_filename = f"@flow_{encoded_name}.txt"
flow_json_str = json.dumps(flow, ensure_ascii=False)

with zipfile.ZipFile(OUT_BIVR, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    zf.writestr(f"flows/{txt_filename}", flow_json_str)

print(f"[OUTPUT] .bivr ビルド完了: {OUT_BIVR}")
print(f"         └ flows/{txt_filename}")

# 統計
print("\n" + "="*50)
print("v4 修正 完了サマリー")
print("="*50)
print(f"  Fix1 profile_words: {fixed_count_1} DTMFモジュール")
print(f"  Fix2 当日/翌日/明後日分岐: OpenAI_予約希望日, OpenAI_予約希望日_変更")
print(f"  Fix3 ルート順序変更: 変更/キャンセルとも 診療科→注射装具確認 の順に")
print(f"  Fix4 レイアウト: {shifted}モジュール一括シフト + {override_count}モジュール再配置")
