#!/usr/bin/env python3
"""
ユアクリニックお茶の水_診療 メインフロー修正パッチ
設計書に基づく修正:
  1. contextName inquiryContent -> inquiry
  2. acceptance_times に転送時間帯分岐(true_transfer)を追加
  3. リトライ上限到達を終話_上限エラーに変更
  4. 終話_上限エラー チェーンを追加
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
main_path = os.path.join(BASE, "draft_ユアCLお茶水_診療.json")

with open(main_path, encoding="utf-8") as f:
    d = json.load(f)

# 修正1: コンテキストフィールド inquiryContent -> inquiry
fields_str = d["modules"]["コンテキスト設定"]["params"]["fields"]
fields_str = fields_str.replace('"inquiryContent"', '"inquiry"')
d["modules"]["コンテキスト設定"]["params"]["fields"] = fields_str

# 修正2: OpenAI_問い合わせ内容 の contextName -> inquiry
d["modules"]["OpenAI_問い合わせ内容"]["params"]["contextName"] = "inquiry"

# 修正3: acceptance_times に転送時間帯分岐を追加
d["modules"]["受付時間判定"]["next"] = [
    {"condition": "^TIMEOUT$", "label": "timeout", "nextModuleName": "時間外_アナウンス"},
    {"condition": "^ERROR$", "label": "error", "nextModuleName": "時間外_アナウンス"},
    {"condition": "^false$", "label": "rejected", "nextModuleName": "時間外_アナウンス"},
    {"condition": "^true_transfer$", "label": "転送時間帯", "nextModuleName": "転送_アナウンス"},
    {"condition": "^true$", "label": "acceptable", "nextModuleName": "冒頭_アナウンス"}
]

# 修正4: リトライ_問い合わせ内容 No more -> 終話_上限エラー
for nx in d["modules"]["リトライ_問い合わせ内容"]["next"]:
    if nx.get("label") == "No more":
        nx["nextModuleName"] = "終話_上限エラー"
        break

# 修正5: 終話_上限エラー チェーンを追加
subs3 = [{"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}]

d["modules"]["終話_上限エラー"] = {
    "layout": {"x": 2200, "y": 1350},
    "next": [{"condition": "^.*$", "label": "Next Module", "nextModuleName": "完了フラグ_上限エラー"}],
    "subs": [{"moduleName": "save-上限エラー", "label": "save-上限エラー"}, {"moduleName": "", "label": ""}, {"moduleName": "", "label": ""}],
    "name": "終話_上限エラー",
    "description": "",
    "matchingmethod": 1,
    "type": "drjoy^Text To Speech$Text to speech",
    "params": {"prompt": "", "stop_by_dtmf": "No", "category_words": ""}
}
d["modules"]["save-上限エラー"] = {
    "layout": {"x": 1920, "y": 1350},
    "next": [],
    "subs": subs3,
    "name": "save-上限エラー",
    "description": "",
    "matchingmethod": 1,
    "type": "drjoy^Persistence$save2db",
    "params": {"contextName": "", "contextDisplayType": "TEXT"}
}
d["modules"]["完了フラグ_上限エラー"] = {
    "layout": {"x": 2200, "y": 1550},
    "next": [{"condition": "^.*$", "label": "next", "nextModuleName": "切断_上限エラー"}],
    "subs": subs3,
    "name": "完了フラグ_上限エラー",
    "description": "",
    "matchingmethod": 1,
    "type": "drjoy^Persistence$saveCompletionFlag2db",
    "params": {"status": "2", "smsFlag": "-1"}
}
d["modules"]["切断_上限エラー"] = {
    "layout": {"x": 2200, "y": 1750},
    "next": [],
    "subs": subs3,
    "name": "切断_上限エラー",
    "description": "",
    "matchingmethod": 1,
    "type": "@IVR$Disconnect",
    "params": {}
}

# 出力
with open(main_path, "w", encoding="utf-8") as f:
    f.write(json.dumps(d, ensure_ascii=False, separators=(",", ":")))

print("修正完了: モジュール数=" + str(len(d["modules"])))

# 検証
fields_ok = '"inquiry"' in d["modules"]["コンテキスト設定"]["params"]["fields"]
inquiry_no_old = '"inquiryContent"' not in d["modules"]["コンテキスト設定"]["params"]["fields"]
openai_ok = d["modules"]["OpenAI_問い合わせ内容"]["params"]["contextName"] == "inquiry"
retry_ok = any(nx["nextModuleName"] == "終話_上限エラー" for nx in d["modules"]["リトライ_問い合わせ内容"]["next"])
transfer_ok = any(nx.get("label") == "転送時間帯" for nx in d["modules"]["受付時間判定"]["next"])

print("  inquiry contextName OK:", fields_ok and inquiry_no_old)
print("  OpenAI contextName OK:", openai_ok)
print("  リトライ No more -> 終話_上限エラー:", retry_ok)
print("  acceptance_times 転送時間帯分岐:", transfer_ok)
print("  終話_上限エラー チェーン存在:", "終話_上限エラー" in d["modules"])
