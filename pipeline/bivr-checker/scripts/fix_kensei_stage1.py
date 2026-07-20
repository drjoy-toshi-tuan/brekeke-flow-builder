#!/usr/bin/env python3
"""健生病院 Stage 1: 構造修正スクリプト

修正内容:
  1. N-001: 丸数字モジュール名を数字に改名（用件①→用件1 等）
  2. STT-003: 氏名SF 入力_患者_氏名 success遷移先設定
  3. SCR-002: 氏名・生年月日SF 結果返却スクリプト追加
  4. 分岐_変更キャンセル参照ミス: OpenAI_用件②→OpenAI_用件1
  5. saveContextModel2DB fields: デフォルト12フィールド準拠に再構築
  6. リトライfalse: 分岐なしモジュールは次へ進む（パターンA）に変更
  7. detection_flag: モジュール側の値を保持（削除しない）
  8. VFB既知パターン修正: termdtmf, stop_play_when_speech, retry等
"""
import json
import sys
import io
import re
from pathlib import Path
from collections import OrderedDict

OUTPUT_DIR = Path("output/健生病院")

# Brekeke正規キー順序
CORRECT_KEY_ORDER = ['layout', 'next', 'subs', 'name', 'description', 'matchingmethod', 'type', 'params']
EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}

# 結果返却スクリプトテンプレート
RETURN_SCRIPT = '''var res = $runner.getModuleResult("{source}");
$runner.setResult(res);

var flowName = $runner.getCurrentFlowName();
var rid = $ivr.getRID();
var key = flowName + "." + rid;
$ivr.setObject(key, res);'''

# モジュールタイプ別スロット数
TYPE_SLOTS = {
    "@General$Script": {"next": 12, "subs": 3},
    "drjoy^Context Logic$ContextMatchRouter": {"next": 10, "subs": 3},
    "drjoy^AmiVoice$Speech to Text": {"next": 11, "subs": 3},
    "drjoy^External Integration$DTMF AmiVoice STT Input": {"next": 11, "subs": 3},
    "drjoy^External Integration$generate_by_OpenAI": {"next": 10, "subs": 3},
    "drjoy^Text To Speech$Speech Retry Counter": {"next": 2, "subs": 3},
    "drjoy^Text To Speech$Text to speech": {"next": 1, "subs": 3},
    "drjoy^Text To Speech$Re-confirmation node data": {"next": 1, "subs": 3},
    "drjoy^TS Custom Module$DOB Re-confirmation": {"next": 5, "subs": 3},
    "drjoy^Persistence$saveCompletionFlag2db": {"next": 1, "subs": 3},
    "drjoy^Persistence$saveContext2DB": {"next": 1, "subs": 3},
    "drjoy^Persistence$saveContextModel2DB": {"next": 1, "subs": 3},
    "drjoy^Persistence$save2db": {"next": 0, "subs": 0},
    "drjoy^External Integration$acceptance_times": {"next": 4, "subs": 3},
    "drjoy^Incoming$incoming-classifier": {"next": 5, "subs": 3},
    "drjoy^Custom Module$Custom Jump to Flow": {"next": 1, "subs": 3},
    "Custom$wait": {"next": 1, "subs": 3},
    "@IVR$Disconnect": {"next": 0, "subs": 0},
    "drjoy^TS Custom Module$Phone Normalization": {"next": 5, "subs": 3},
}


def reorder_keys(mod, name):
    """Brekeke正規キー順序に並び替え"""
    reordered = {}
    for key in CORRECT_KEY_ORDER:
        if key in mod:
            reordered[key] = mod[key]
    for key in mod:
        if key not in reordered:
            reordered[key] = mod[key]
    return reordered


def ensure_module_fields(mod, name):
    """必須フィールド補完"""
    if 'name' not in mod:
        mod['name'] = name
    if 'description' not in mod:
        mod['description'] = ''
    if 'matchingmethod' not in mod:
        t = mod.get('type', '')
        mod['matchingmethod'] = 0 if 'Retry Counter' in t else 1


def fix_slots(mod):
    """next/subsスロット数修正"""
    t = mod.get('type', '')
    if t in TYPE_SLOTS:
        expected = TYPE_SLOTS[t]
        # next
        nexts = mod.get('next', [])
        while len(nexts) < expected['next']:
            nexts.append(dict(EMPTY_NEXT))
        mod['next'] = nexts[:expected['next']]
        # subs
        subs = mod.get('subs', [])
        while len(subs) < expected['subs']:
            subs.append(dict(EMPTY_SUB))
        if expected['subs'] == 0:
            mod['subs'] = []
        else:
            mod['subs'] = subs[:expected['subs']]


def make_return_module(source_module, x, y):
    """結果返却スクリプトモジュール生成"""
    mod = {
        "layout": {"x": x, "y": y},
        "next": [],
        "subs": [dict(EMPTY_SUB), dict(EMPTY_SUB), dict(EMPTY_SUB)],
        "name": "",
        "description": "",
        "matchingmethod": 1,
        "type": "@General$Script",
        "params": {"script": RETURN_SCRIPT.format(source=source_module)},
    }
    fix_slots(mod)
    return mod


def rename_modules(data, rename_map):
    """モジュール名を一括リネーム"""
    modules = data['modules']

    # modules辞書のキーをリネーム
    new_modules = {}
    for old_name, mod in modules.items():
        new_name = rename_map.get(old_name, old_name)
        mod['name'] = new_name
        new_modules[new_name] = mod
    data['modules'] = new_modules

    # start
    if data.get('start', '') in rename_map:
        data['start'] = rename_map[data['start']]

    # 全nextの参照先もリネーム
    for mname, mod in data['modules'].items():
        for n in mod.get('next', []):
            old = n.get('nextModuleName', '')
            if old in rename_map:
                n['nextModuleName'] = rename_map[old]

    # 全subsの参照先もリネーム
    for mname, mod in data['modules'].items():
        for s in mod.get('subs', []):
            old = s.get('moduleName', '')
            if old in rename_map:
                s['moduleName'] = rename_map[old]

    # params内の参照もリネーム (module, module1Name, module2Name等)
    for mname, mod in data['modules'].items():
        params = mod.get('params', {})
        for pk in list(params.keys()):
            val = params[pk]
            if isinstance(val, str) and val in rename_map:
                params[pk] = rename_map[val]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    fixes = []

    # ================================================================
    # メインフロー修正
    # ================================================================
    main_path = OUTPUT_DIR / "健生病院_健診_20260420.json"
    with open(main_path, encoding='utf-8') as f:
        data = json.load(f)

    modules = data['modules']

    # --- 1. N-001: 丸数字リネーム ---
    rename_map = {}
    for mname in list(modules.keys()):
        new_name = mname.replace('①', '1').replace('②', '2').replace('③', '3')
        if new_name != mname:
            rename_map[mname] = new_name

    if rename_map:
        rename_modules(data, rename_map)
        modules = data['modules']
        for old, new in rename_map.items():
            fixes.append(f"N-001: {old} → {new}")

    # --- 4. 分岐_変更キャンセル 参照ミス修正 ---
    cmr = modules.get('分岐_変更キャンセル')
    if cmr:
        params = cmr.get('params', {})
        # OpenAI_用件2 (リネーム後) を OpenAI_用件1 に修正
        if params.get('module1Name') == 'OpenAI_用件2':
            params['module1Name'] = 'OpenAI_用件1'
            params['module2Name'] = 'OpenAI_用件1'
            # Value1/Value2も用件1の出力値に合わせる
            params['module1Value1'] = '変更'
            params['module2Value1'] = '変更'
            params['module1Value2'] = 'キャンセル'
            params['module2Value2'] = 'キャンセル'
            fixes.append("CMR修正: 分岐_変更キャンセル module→OpenAI_用件1, values=変更/キャンセル")

    # --- 6. リトライfalse修正 ---
    # OpenAI分岐数を確認して、分岐なし(^.*$のみ)は次へ進む
    for mname, mod in modules.items():
        if 'Retry Counter' not in mod.get('type', ''):
            continue
        # true遷移先のTTS→STT→OpenAIの分岐数を確認
        true_target = ''
        for n in mod.get('next', []):
            if n.get('condition') == 'true':
                true_target = n.get('nextModuleName', '')

        # TTS名からSTT/OpenAI名を推定
        base_name = true_target  # TTS名
        stt_name = f'入力_{base_name}'
        oai_name = f'OpenAI_{base_name}'

        if oai_name in modules:
            oai = modules[oai_name]
            specific = [n for n in oai.get('next', [])
                       if n.get('nextModuleName')
                       and n.get('condition', '') not in ('^TIMEOUT$', '^ERROR$', '^NO_RESULT$', '^.+$', '^.*$', '')]
            if len(specific) == 0:
                # 分岐なし(^.*$のみ) → 次へ進む
                # ^.*$の遷移先を取得
                catch_all_target = ''
                for n in oai.get('next', []):
                    if n.get('condition') in ('^.+$', '^.*$') and n.get('nextModuleName'):
                        catch_all_target = n['nextModuleName']
                        break
                if catch_all_target:
                    for n in mod.get('next', []):
                        if n.get('condition') == 'false':
                            old = n['nextModuleName']
                            if old != catch_all_target:
                                n['nextModuleName'] = catch_all_target
                                mod['params']['prompt_false'] = '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}'
                                fixes.append(f"リトライ修正: {mname} false: {old} → {catch_all_target} (分岐なし→次へ)")

    # --- 8. VFB既知パターン修正 ---
    for mname, mod in modules.items():
        t = mod.get('type', '')
        params = mod.get('params', {})

        # DTMF: termdtmf * → #
        if 'DTMF' in t:
            if params.get('termdtmf') == '*':
                params['termdtmf'] = '#'
                fixes.append(f"VFB-034: {mname} termdtmf *→#")
            if params.get('stop_play_when_speech') == 'No':
                params['stop_play_when_speech'] = 'Yes'
                fixes.append(f"VFB-034: {mname} stop_play_when_speech No→Yes")
            if params.get('retry') == '0':
                params['retry'] = '2'
                fixes.append(f"VFB-034: {mname} retry 0→2")

    # --- 全モジュール: キー順序・必須フィールド・スロット数 ---
    for mname in list(modules.keys()):
        mod = modules[mname]
        ensure_module_fields(mod, mname)
        fix_slots(mod)
        modules[mname] = reorder_keys(mod, mname)

    with open(main_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    fixes.append(f"メインフロー保存: {main_path}")

    # ================================================================
    # 氏名サブフロー修正
    # ================================================================
    sf_path = OUTPUT_DIR / "健生病院_氏名聴取_20260420.json"
    with open(sf_path, encoding='utf-8') as f:
        sf = json.load(f)

    # STT-003: success遷移先設定
    stt = sf['modules'].get('入力_患者_氏名', {})
    for n in stt.get('next', []):
        if n.get('condition') == '^.+$':
            if not n.get('nextModuleName'):
                n['nextModuleName'] = 'script_結果返却_氏名'
                fixes.append("STT-003: 入力_患者_氏名 success→script_結果返却_氏名")

    # リトライfalse
    retry = sf['modules'].get('リトライ_患者_氏名', {})
    for n in retry.get('next', []):
        if n.get('condition') == 'false':
            if not n.get('nextModuleName') or n['nextModuleName'] == '':
                n['nextModuleName'] = 'script_結果返却_氏名'
                fixes.append("リトライ_患者_氏名 false→script_結果返却_氏名")

    # SCR-002: 結果返却スクリプト追加
    ret_mod = make_return_module("入力_患者_氏名", 0, 900)
    ret_mod['name'] = 'script_結果返却_氏名'
    sf['modules']['script_結果返却_氏名'] = ret_mod
    fixes.append("SCR-002: script_結果返却_氏名 追加")

    for mname in list(sf['modules'].keys()):
        mod = sf['modules'][mname]
        ensure_module_fields(mod, mname)
        fix_slots(mod)
        sf['modules'][mname] = reorder_keys(mod, mname)

    with open(sf_path, 'w', encoding='utf-8') as f:
        json.dump(sf, f, ensure_ascii=False, indent=2)
    fixes.append(f"氏名SF保存: {sf_path}")

    # ================================================================
    # 生年月日サブフロー修正
    # ================================================================
    sf_path = OUTPUT_DIR / "健生病院_生年月日聴取_20260420.json"
    with open(sf_path, encoding='utf-8') as f:
        sf = json.load(f)

    # SCR-002: 結果返却スクリプト追加
    # 復唱確認後の肯定→結果返却
    oai_reconf = sf['modules'].get('openAI_復唱_患者生年月日', {})
    for n in oai_reconf.get('next', []):
        if n.get('condition') == '^肯定$':
            if not n.get('nextModuleName') or n['nextModuleName'] == '':
                n['nextModuleName'] = 'script_結果返却_生年月日'
                fixes.append("openAI_復唱_患者生年月日 肯定→script_結果返却_生年月日")

    # リトライfalseも
    for rname in ['リトライ_患者_生年月日', 'リトライ_復唱_患者生年月日']:
        r = sf['modules'].get(rname, {})
        for n in r.get('next', []):
            if n.get('condition') == 'false':
                if not n.get('nextModuleName') or n['nextModuleName'] == '':
                    n['nextModuleName'] = 'script_結果返却_生年月日'
                    fixes.append(f"{rname} false→script_結果返却_生年月日")

    ret_mod = make_return_module("復唱_患者_生年月日", 0, 1200)
    ret_mod['name'] = 'script_結果返却_生年月日'
    sf['modules']['script_結果返却_生年月日'] = ret_mod
    fixes.append("SCR-002: script_結果返却_生年月日 追加")

    # DTMF retry修正
    for mname, mod in sf['modules'].items():
        if 'DTMF' in mod.get('type', ''):
            if mod.get('params', {}).get('retry') == '0':
                mod['params']['retry'] = '2'
                fixes.append(f"DTMF retry修正: {mname} 0→2")

    for mname in list(sf['modules'].keys()):
        mod = sf['modules'][mname]
        ensure_module_fields(mod, mname)
        fix_slots(mod)
        sf['modules'][mname] = reorder_keys(mod, mname)

    with open(sf_path, 'w', encoding='utf-8') as f:
        json.dump(sf, f, ensure_ascii=False, indent=2)
    fixes.append(f"生年月日SF保存: {sf_path}")

    # ================================================================
    # 電話番号サブフロー（キー順序・スロット数のみ）
    # ================================================================
    sf_path = OUTPUT_DIR / "健生病院_電話番号聴取_20260420.json"
    with open(sf_path, encoding='utf-8') as f:
        sf = json.load(f)

    for mname, mod in sf['modules'].items():
        if 'DTMF' in mod.get('type', ''):
            if mod.get('params', {}).get('retry') == '0':
                mod['params']['retry'] = '2'
                fixes.append(f"DTMF retry修正: {mname} 0→2")

    for mname in list(sf['modules'].keys()):
        mod = sf['modules'][mname]
        ensure_module_fields(mod, mname)
        fix_slots(mod)
        sf['modules'][mname] = reorder_keys(mod, mname)

    with open(sf_path, 'w', encoding='utf-8') as f:
        json.dump(sf, f, ensure_ascii=False, indent=2)
    fixes.append(f"電話番号SF保存: {sf_path}")

    # ================================================================
    # 結果表示
    # ================================================================
    print(f"=== 健生病院 Stage 1: 構造修正 ({len(fixes)}件) ===\n")
    for fix in fixes:
        print(f"  ✓ {fix}")


if __name__ == "__main__":
    main()
