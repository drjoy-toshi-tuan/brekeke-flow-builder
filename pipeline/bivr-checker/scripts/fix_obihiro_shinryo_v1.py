"""
fix_obihiro_shinryo_v1.py
帯広第一病院_診療 v1 修正スクリプト

修正内容:
1. CTX-017: additionalDepartment displayType DEPARTMENT → TEXT
2. CROSS-001: END_受付完了_携帯 / END_受付完了_固定 の prompt 設定
3. P-011 ×8: Retry prompt_false 設定（パターンA: 任意聴取→次へ進む）
"""

import json
import shutil
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

INPUT_JSON  = "output/帯広第一病院_診療_20260415.json"
OUTPUT_DIR  = "output/帯広第一病院/fixed_v1/flows"
OUTPUT_JSON = f"{OUTPUT_DIR}/帯広第一病院_診療_v1.json"
PROPS_IN    = "input/帯広第一病院/properties_帯広第一病院_診療.md"
PROPS_OUT   = "output/帯広第一病院/fixed_v1/properties_帯広第一病院_診療_v1.md"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(os.path.dirname(PROPS_OUT), exist_ok=True)

# -------------------------------------------------------
# フロー JSON 修正
# -------------------------------------------------------
with open(INPUT_JSON, encoding="utf-8") as f:
    flow = json.load(f)

changes = []

# --- Fix 1: CTX-017 additionalDepartment DEPARTMENT → TEXT ---
for name, mod in flow["modules"].items():
    if "saveContextModel2DB" in mod.get("type", ""):
        fields_raw = mod["params"].get("fields", "")
        if not fields_raw:
            continue
        fields = json.loads(fields_raw) if isinstance(fields_raw, str) else fields_raw
        modified = False
        for fi in fields:
            if fi.get("contextName") == "additionalDepartment" and fi.get("displayType") == "DEPARTMENT":
                fi["displayType"] = "TEXT"
                modified = True
                changes.append("CTX-017: additionalDepartment displayType DEPARTMENT → TEXT")
        if modified:
            mod["params"]["fields"] = json.dumps(fields, ensure_ascii=False)

# --- Fix 2: CROSS-001 END_受付完了_携帯 / 固定 prompt 設定 ---
END_PROMPT_MOBILE = (
    "{tts_g:申し込みを受付いたしました。"
    "3診療日以内に、折り返しお電話、もしくはショートメールにてご連絡いたします。"
    "携帯電話でおかけの方はこのあと、ショートメッセージをお送りしますので、"
    "内容確認と修正をお願いいたします。"
    "お電話ありがとうございました。それでは失礼いたします。}"
)
END_PROMPT_LANDLINE = (
    "{tts_g:申し込みを受付いたしました。"
    "3診療日以内に、折り返しお電話にてご連絡いたします。"
    "お電話ありがとうございました。それでは失礼いたします。}"
)

for mod_name, prompt_text, label in [
    ("END_受付完了_携帯", END_PROMPT_MOBILE,   "CROSS-001: END_受付完了_携帯 prompt 設定"),
    ("END_受付完了_固定", END_PROMPT_LANDLINE, "CROSS-001: END_受付完了_固定 prompt 設定"),
]:
    if mod_name in flow["modules"]:
        flow["modules"][mod_name]["params"]["prompt"] = prompt_text
        changes.append(label)

# --- Fix 3: P-011 Retry prompt_false 設定（パターンA: 任意聴取→次へ進む）---
PROMPT_FALSE_PATTERN_A = "{tts_g:かしこまりました。折り返しの際に確認させていただきます。}"

retry_targets = [
    "リトライ_診療科",
    "リトライ_追加診療科",
    "リトライ_現在の予約日",
    "リトライ_予約希望日",
    "リトライ_症状聴取",
    "リトライ_理由聴取",
    "リトライ_内容確認",
    "リトライ_最終確認",
]
for name in retry_targets:
    if name in flow["modules"]:
        current = flow["modules"][name]["params"].get("prompt_false", "")
        if not current:
            flow["modules"][name]["params"]["prompt_false"] = PROMPT_FALSE_PATTERN_A
            changes.append(f"P-011: {name} prompt_false 設定")

# 出力
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(flow, f, ensure_ascii=False, indent=2)

# -------------------------------------------------------
# Properties.md 修正
# -------------------------------------------------------
with open(PROPS_IN, encoding="utf-8") as f:
    props = f.read()

# END_受付完了.prompt を 携帯・固定に分割
OLD_END = "END_受付完了.prompt={tts_g:申し込みを受付いたしました。3診療日以内に、折り返しお電話、もしくはショートメールにてご連絡いたします。携帯電話でおかけの方はこのあと、ショートメッセージをお送りしますので、内容確認と修正をお願いいたします。お電話ありがとうございました。それでは失礼いたします。}"
NEW_END = (
    "END_受付完了_携帯.prompt={tts_g:申し込みを受付いたしました。"
    "3診療日以内に、折り返しお電話、もしくはショートメールにてご連絡いたします。"
    "携帯電話でおかけの方はこのあと、ショートメッセージをお送りしますので、"
    "内容確認と修正をお願いいたします。"
    "お電話ありがとうございました。それでは失礼いたします。}\n"
    "END_受付完了_固定.prompt={tts_g:申し込みを受付いたしました。"
    "3診療日以内に、折り返しお電話にてご連絡いたします。"
    "お電話ありがとうございました。それでは失礼いたします。}"
)
if OLD_END in props:
    props = props.replace(OLD_END, NEW_END)
    changes.append("P-020/PROP-001: END_受付完了.prompt → 携帯/固定 に分割")

# office_id 追加（pbx.db.name の前に挿入）
if "office_id=" not in props:
    props = props.replace("pbx.db.name=save.db", "office_id=\npbx.db.name=save.db")
    changes.append("PROP-002: office_id= 追加（値は要設定）")

# サブフロー用 TTS セクションを削除（メインフローの Properties.md はメインフロー専用）
# これらはサブフロー固有の Properties ファイルで管理する
SUBFLOW_SECTION = """# === サブフロー必須TTS ===
患者_診察券番号.prompt={tts_g:お持ちの方は診察券番号をお話しください。分からない方は「わからない」とお話しください。}
患者_氏名.prompt={tts_g:お名前を、「名前は、帯広一郎です。」のようにフルネームでお話しください。}
患者_生年月日.prompt={tts_g:患者様の生年月日を「昭和50年5月5日」のようにお話しください。}
患者_連絡先.prompt={tts_g:ご連絡先のお電話番号をお話ください。}"""
if SUBFLOW_SECTION in props:
    props = props.replace(
        SUBFLOW_SECTION,
        "# === サブフロー必須TTS（各サブフロー専用 Properties.md で管理）==="
    )
    changes.append("P-020/PROP-001: サブフロー用 TTS 行をメインフロー Properties.md から分離")

with open(PROPS_OUT, "w", encoding="utf-8") as f:
    f.write(props)

# -------------------------------------------------------
# サマリー出力
# -------------------------------------------------------
print(f"=== 修正完了 ===")
print(f"フローJSON : {OUTPUT_JSON}")
print(f"Properties : {PROPS_OUT}")
print(f"\n修正箇所 ({len(changes)}件):")
for c in changes:
    print(f"  [OK] {c}")
