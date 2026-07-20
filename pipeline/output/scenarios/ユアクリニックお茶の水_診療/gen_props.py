#!/usr/bin/env python3
"""
ユアクリニックお茶の水_診療 IVRプロパティ生成スクリプト
環境: デモ
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "../../.."))
OUT = BASE

TTS_TYPE = "drjoy^Text To Speech$Text to speech"
RETRY_TYPE = "drjoy^Text To Speech$Speech Retry Counter"

def load_flow(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def collect_tts_props(flow):
    lines = []
    for mod_name, m in flow["modules"].items():
        t = m.get("type", "")
        if t == TTS_TYPE:
            prompt = m.get("params", {}).get("prompt", "")
            if not prompt:
                prompt = "TODO_発話内容を記入"
            lines.append(mod_name + ".prompt=" + prompt)
        # Retry Counter の prompt_true/prompt_false はフローJSON内で管理するためプロパティには出力しない
    return lines

main_flow = load_flow(os.path.join(OUT, "draft_ユアCLお茶水_診療.json"))
name_flow = load_flow(os.path.join(OUT, "draft_ユアCLお茶水_氏名聴取.json"))
phone_flow = load_flow(os.path.join(OUT, "draft_ユアCLお茶水_電話番号聴取.json"))

main_tts = collect_tts_props(main_flow)
name_tts = collect_tts_props(name_flow)
phone_tts = collect_tts_props(phone_flow)

# env_demo.txt を読み込む
env_demo_path = os.path.join(ROOT, "docs", "specs", "env_demo.txt")
with open(env_demo_path, encoding="utf-8") as f:
    env_demo = f.read()

# プロパティファイル生成
lines = []
lines.append("# IVRプロパティ: ユアCLお茶水_診療")
lines.append("# 環境: デモ")
lines.append("# 生成日: 2026-04-01")
lines.append("# 対象フロー: ユアCLお茶水$診療 + 氏名聴取 + 電話番号聴取")
lines.append("")
lines.append("> 注意: 設計書にBLOCKER項目(B-1~B-4)が残存しています。")
lines.append("> TODO_発話内容を記入の箇所は実際の発話内容に差し替えてください。")
lines.append("> B-1: office_id (TODO_要確認)")
lines.append("> B-2: デモ050番号 (TODO_要確認)")
lines.append("> B-3: 時間外AI聴取継続仕様 (デフォルト: 継続あり)")
lines.append("> B-4: リトライ失敗時転送条件 (デフォルト: 切断)")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## メインフロー (ユアCLお茶水$診療)")
lines.append("")
for line in main_tts:
    lines.append(line)
lines.append("")
lines.append("## 氏名聴取サブフロー (ユアCLお茶水$氏名聴取)")
lines.append("")
for line in name_tts:
    lines.append(line)
lines.append("")
lines.append("## 電話番号聴取サブフロー (ユアCLお茶水$電話番号聴取)")
lines.append("")
for line in phone_tts:
    lines.append(line)
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 環境設定 (デモ)")
lines.append("")
lines.append(env_demo)

props_path = os.path.join(OUT, "properties_ユアCLお茶水_診療.md")
with open(props_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("[OK] プロパティ出力: " + props_path)
print("  メインフロー TTS: " + str(len(main_tts)) + "行")
print("  氏名聴取 TTS: " + str(len(name_tts)) + "行")
print("  電話番号聴取 TTS: " + str(len(phone_tts)) + "行")
