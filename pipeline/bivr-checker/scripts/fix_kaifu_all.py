#!/usr/bin/env python3
"""海風診療所 全Stage一括修正スクリプト

Stage 1: 構造修正
  - サブフロー結果返却スクリプト追加（氏名/生年月日/RAG）
  - 生年月日SF OAI-002 module参照修正
  - DTMF retry 0→2
  - detection_flag → "デフォルト"
  - リトライfalse整合性修正（分岐あり→ループ、なし→次へ）
  - prompt_false設定
  - saveContextModel2DB fields修正
  - キー順序・スロット数・必須フィールド正規化
  - 海外着信: 終話→受付継続に修正

Stage 2: profile_words充実化（全STT/DTMFモジュール）

レイアウト修正: 冒頭x=0起点、終話下配置、重なり解消、y_range確保
"""
import json
import sys
import io
import re
from pathlib import Path

OUTPUT_DIR = Path("output/海風診療所")
INPUT_DIR = Path("input/海風診療所")

CORRECT_KEY_ORDER = ['layout', 'next', 'subs', 'name', 'description', 'matchingmethod', 'type', 'params']
EMPTY_NEXT = {"condition": "", "label": "", "nextModuleName": ""}
EMPTY_SUB = {"moduleName": "", "label": ""}

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
    "drjoy^External Integration$RAG": {"next": 4, "subs": 3},
}

RETURN_SCRIPT = '''var res = $runner.getModuleResult("{source}");
$runner.setResult(res);
var flowName = $runner.getCurrentFlowName();
var rid = $ivr.getRID();
var key = flowName + "." + rid;
$ivr.setObject(key, res);'''

FILLERS_10 = ["あ", "あー", "あの", "え", "えー", "えっと", "ん", "はい", "ま", "そうですね"]
FILLERS_3 = ["あ", "え", "えー"]
SUFFIXES_4 = ["です", "で", "なんですが", "になります"]

def entry(h, y, fillers=None, suffixes=None, drops=1):
    lines = [f"{h} {y}"]
    if fillers:
        for f in fillers:
            lines.append(f"{h} {f}{y}")
    if suffixes:
        for s in suffixes:
            lines.append(f"{h} {y}{s}")
    for i in range(1, min(drops + 1, len(y))):
        d = y[i:]
        if len(d) >= 2:
            lines.append(f"{h} {d}")
    return lines

def dedup(lines):
    return list(dict.fromkeys(lines))

def reorder_keys(mod, name):
    r = {}
    for k in CORRECT_KEY_ORDER:
        if k in mod: r[k] = mod[k]
    for k in mod:
        if k not in r: r[k] = mod[k]
    return r

def ensure_fields(mod, name):
    if 'name' not in mod: mod['name'] = name
    if 'description' not in mod: mod['description'] = ''
    if 'matchingmethod' not in mod:
        mod['matchingmethod'] = 0 if 'Retry Counter' in mod.get('type','') else 1
    if isinstance(mod.get('matchingmethod'), str):
        mod['matchingmethod'] = int(mod['matchingmethod'])

def fix_slots(mod):
    t = mod.get('type', '')
    if t in TYPE_SLOTS:
        exp = TYPE_SLOTS[t]
        nexts = mod.get('next', [])
        while len(nexts) < exp['next']: nexts.append(dict(EMPTY_NEXT))
        mod['next'] = nexts[:exp['next']]
        subs = mod.get('subs', [])
        if exp['subs'] == 0:
            mod['subs'] = []
        else:
            while len(subs) < exp['subs']: subs.append(dict(EMPTY_SUB))
            mod['subs'] = subs[:exp['subs']]

def make_return_mod(source, x, y, name):
    mod = {
        "layout": {"x": x, "y": y}, "next": [], "subs": [dict(EMPTY_SUB)]*3,
        "name": name, "description": "", "matchingmethod": 1,
        "type": "@General$Script", "params": {"script": RETURN_SCRIPT.format(source=source)},
    }
    fix_slots(mod)
    return mod

def fix_retry_false(modules):
    """リトライfalse整合性修正（verifyと同一ロジック）"""
    fixes = []
    skip = {'^TIMEOUT$','^ERROR$','^NO_RESULT$','^.+$','^.*$',''}

    for rname, rmod in modules.items():
        if 'Retry Counter' not in rmod.get('type',''): continue
        true_t = false_t = ''
        for n in rmod.get('next',[]):
            if n['condition'] == 'true': true_t = n['nextModuleName']
            if n['condition'] == 'false': false_t = n['nextModuleName']
        if not true_t or true_t not in modules: continue

        # TTS→STT→次モジュール
        tts = modules.get(true_t, {})
        stt_name = ''
        for n in tts.get('next',[]):
            if n.get('nextModuleName'):
                stt_name = n['nextModuleName']; break
        if not stt_name or stt_name not in modules: continue
        stt = modules[stt_name]
        if 'Speech to Text' not in stt.get('type','') and 'DTMF' not in stt.get('type',''): continue

        next_name = ''
        for n in stt.get('next',[]):
            if n.get('condition') in ('^.+$','^.*$') and n.get('nextModuleName'):
                next_name = n['nextModuleName']; break
        if not next_name or next_name not in modules: continue

        next_mod = modules[next_name]
        specific = [(c,nm) for nx in next_mod.get('next',[])
                    for c, nm in [(nx.get('condition',''), nx.get('nextModuleName',''))]
                    if c not in skip and nm]
        wildcard = ''
        for nx in next_mod.get('next',[]):
            if nx.get('condition') in ('^.+$','^.*$') and nx.get('nextModuleName'):
                wildcard = nx['nextModuleName']

        has_branch = len(specific) > 0
        correct = true_t if has_branch else wildcard
        correct_pf = '' if has_branch else '{tts_g:かしこまりました。折り返しの際に確認させていただきます。}'

        if correct and false_t != correct:
            for n in rmod.get('next',[]):
                if n['condition'] == 'false': n['nextModuleName'] = correct
            rmod['params']['prompt_false'] = correct_pf
            kind = 'ループ' if has_branch else '次へ'
            fixes.append(f'{rname}: {false_t}→{correct} [{kind}]')
    return fixes


def build_pw_date():
    lines = []
    months = [("1月","いちがつ"),("2月","にがつ"),("3月","さんがつ"),("4月","しがつ"),
              ("5月","ごがつ"),("6月","ろくがつ"),("7月","しちがつ"),("8月","はちがつ"),
              ("9月","くがつ"),("10月","じゅうがつ"),("11月","じゅういちがつ"),("12月","じゅうにがつ")]
    for h,y in months: lines.append(f"{h} {y}")
    days = [("1日","ついたち"),("2日","ふつか"),("3日","みっか"),("4日","よっか"),
            ("5日","いつか"),("6日","むいか"),("7日","なのか"),("8日","ようか"),
            ("9日","ここのか"),("10日","とおか"),("11日","じゅういちにち"),("12日","じゅうににち"),
            ("13日","じゅうさんにち"),("14日","じゅうよっか"),("15日","じゅうごにち"),
            ("16日","じゅうろくにち"),("17日","じゅうしちにち"),("18日","じゅうはちにち"),
            ("19日","じゅうくにち"),("20日","はつか"),("21日","にじゅういちにち"),
            ("22日","にじゅうににち"),("23日","にじゅうさんにち"),("24日","にじゅうよっか"),
            ("25日","にじゅうごにち"),("26日","にじゅうろくにち"),("27日","にじゅうしちにち"),
            ("28日","にじゅうはちにち"),("29日","にじゅうくにち"),("30日","さんじゅうにち"),
            ("31日","さんじゅういちにち")]
    for h,y in days: lines.append(f"{h} {y}")
    for h,y in [("来週","らいしゅう"),("再来週","さらいしゅう"),("来月","らいげつ"),
                ("明日","あした"),("明後日","あさって"),("今週","こんしゅう"),("今月","こんげつ")]:
        lines.extend(entry(h, y, FILLERS_10, SUFFIXES_4, 2))
    for h,y in [("月曜日","げつようび"),("火曜日","かようび"),("水曜日","すいようび"),
                ("木曜日","もくようび"),("金曜日","きんようび"),("土曜日","どようび"),("日曜日","にちようび")]:
        lines.extend(entry(h, y, FILLERS_3, ["です","なんですが"], 2))
    for h,y in [("わからない","わからない"),("わかりません","わかりません"),("未定","みてい")]:
        lines.extend(entry(h, y, FILLERS_10, None, 2))
    for h,y in [("1","いち"),("2","に"),("3","さん"),("4","よん"),("4","し"),("5","ご"),
                ("6","ろく"),("7","なな"),("7","しち"),("8","はち"),("9","きゅう"),("10","じゅう")]:
        lines.append(f"{h} {y}")
    return dedup(lines)


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    all_fixes = []

    # Property.md読み込み
    tts_prompts = {}
    prop_path = INPUT_DIR / "properties_海風診療所_診療.md"
    with open(prop_path, encoding='utf-8') as f:
        for line in f:
            m = re.match(r'(.+?)\.prompt=\{tts_g:(.+?)\}', line.strip())
            if m: tts_prompts[m.group(1)] = m.group(2)

    # ================================================================
    # メインフロー修正
    # ================================================================
    main_path = OUTPUT_DIR / "海風診療所_診療_20260409.json"
    with open(main_path, encoding='utf-8') as f:
        data = json.load(f)
    modules = data['modules']

    # detection_flag → "デフォルト"
    for name, mod in modules.items():
        t = mod.get('type','')
        if 'Speech to Text' in t or 'DTMF' in t:
            mod.setdefault('params',{})['detection_flag'] = 'デフォルト'

    # DTMF retry修正
    for name, mod in modules.items():
        if 'DTMF' in mod.get('type',''):
            if mod.get('params',{}).get('retry') == '0':
                mod['params']['retry'] = '2'
                all_fixes.append(f'DTMF retry: {name} 0→2')
            if mod.get('params',{}).get('termdtmf') == '*':
                mod['params']['termdtmf'] = '#'
            if mod.get('params',{}).get('stop_play_when_speech') == 'No':
                mod['params']['stop_play_when_speech'] = 'Yes'

    # リトライfalse修正
    retry_fixes = fix_retry_false(modules)
    all_fixes.extend(retry_fixes)

    # saveContextModel2DB fields修正
    ctx = modules.get('コンテキスト設定', {})
    if ctx:
        fields = json.loads(ctx.get('params',{}).get('fields','[]'))
        field_map = {f['contextName']: f for f in fields}

        # status修正
        if 'status' in field_map:
            field_map['status']['editable'] = True
            field_map['status']['rangeValues'] = [
                {"id":"0","order":0,"value":"途中切断"},
                {"id":"1","order":1,"value":"未処理"},
                {"id":"2","order":2,"value":"代表案内"},
                {"id":"3","order":3,"value":"転送"},
                {"id":"6","order":6,"value":"時間外"},
            ]
        # callId修正
        if 'callId' in field_map:
            field_map['callId']['displayType'] = 'NUMBER'
            field_map['callId']['editable'] = True
        # contextNameJp修正
        if 'patientName' in field_map: field_map['patientName']['contextNameJp'] = '患者名'
        if 'telephoneNumber' in field_map: field_map['telephoneNumber']['contextNameJp'] = '電話番号'
        if 'dateOfCall' in field_map: field_map['dateOfCall']['contextNameJp'] = '入電日時'
        if 'patientDateOfBirth' in field_map: field_map['patientDateOfBirth']['contextNameJp'] = '生年月日(和暦)'
        if 'classification' in field_map: field_map['classification']['contextNameJp'] = '区分'

        ctx['params']['fields'] = json.dumps(list(field_map.values()), ensure_ascii=False, indent=2)
        all_fixes.append('fields修正: status/callId/contextNameJp')

    # profile_words充実化
    pw_map = {
        '入力_用件確認': dedup(
            entry("予約","よやく",FILLERS_10,SUFFIXES_4,2) +
            entry("変更","へんこう",FILLERS_10,SUFFIXES_4,2) +
            entry("キャンセル","きゃんせる",FILLERS_10,SUFFIXES_4,2) +
            entry("問い合わせ","といあわせ",FILLERS_10,SUFFIXES_4,2) +
            entry("新規予約","しんきよやく",FILLERS_3) +
            entry("予約変更","よやくへんこう",FILLERS_3) +
            entry("予約キャンセル","よやくきゃんせる",FILLERS_3) +
            entry("確認","かくにん",FILLERS_3,["です","なんですが"],1) +
            entry("聞きたい","ききたい",FILLERS_3)
        ),
        '入力_来院歴確認': dedup(
            entry("はい","はい") + entry("いいえ","いいえ") +
            entry("あります","あります",FILLERS_10,None,2) +
            entry("ありません","ありません",FILLERS_10,None,2) +
            entry("初めて","はじめて",FILLERS_10,["です"],2) +
            entry("通っています","かよっています",FILLERS_3) +
            [f"はい {y}" for y in ["はあ","あい","い"]] +
            [f"いいえ {y}" for y in ["いーえ","いい","いえ"]]
        ),
        '入力_健診_診療確認': dedup(
            entry("健診","けんしん",FILLERS_10,SUFFIXES_4,2) +
            entry("診療","しんりょう",FILLERS_10,SUFFIXES_4,2) +
            entry("健康診断","けんこうしんだん",FILLERS_3,["です"],2) +
            entry("受診","じゅしん",FILLERS_3,["です"],1)
        ),
        '入力_個人_団体確認': dedup(
            entry("個人","こじん",FILLERS_10,SUFFIXES_4,2) +
            entry("団体","だんたい",FILLERS_10,SUFFIXES_4,2) +
            entry("会社","かいしゃ",FILLERS_3,["です"],1) +
            entry("個人的","こじんてき",FILLERS_3)
        ),
        '入力_一般_雇入れ確認': dedup(
            entry("一般","いっぱん",FILLERS_10,SUFFIXES_4,2) +
            entry("雇入れ","やといいれ",FILLERS_10,SUFFIXES_4,2) +
            entry("一般健診","いっぱんけんしん",FILLERS_3,["です"],2) +
            entry("雇入れ健診","やといいれけんしん",FILLERS_3,["です"],2)
        ),
        '入力_オプション確認': dedup(
            entry("特にない","とくにない",FILLERS_10,["です"],2) +
            entry("ありません","ありません",FILLERS_10,None,2) +
            entry("大丈夫","だいじょうぶ",FILLERS_3,["です"],1) +
            entry("血液検査","けつえきけんさ",FILLERS_3,["です"],1) +
            entry("心電図","しんでんず",FILLERS_3,["です"],1) +
            entry("レントゲン","れんとげん",FILLERS_3,["です"],1) +
            entry("視力検査","しりょくけんさ",FILLERS_3) +
            entry("聴力検査","ちょうりょくけんさ",FILLERS_3)
        ),
        '入力_保険_自由確認': dedup(
            entry("保険","ほけん",FILLERS_10,SUFFIXES_4,2) +
            entry("自由","じゆう",FILLERS_10,SUFFIXES_4,2) +
            entry("保険診療","ほけんしんりょう",FILLERS_3,["です"],2) +
            entry("自由診療","じゆうしんりょう",FILLERS_3,["です"],2)
        ),
        '入力_点滴_検査_その他確認': dedup(
            entry("点滴","てんてき",FILLERS_10,SUFFIXES_4,2) +
            entry("検査","けんさ",FILLERS_10,SUFFIXES_4,2) +
            entry("その他","そのた",FILLERS_10,SUFFIXES_4,2) +
            entry("点滴診療","てんてきしんりょう",FILLERS_3) +
            entry("検査診療","けんさしんりょう",FILLERS_3)
        ),
        '入力_点滴内容': dedup(
            entry("ビタミン","びたみん",FILLERS_10,["です","なんですが"],2) +
            entry("にんにく","にんにく",FILLERS_10,["です","なんですが"],2) +
            entry("美白","びはく",FILLERS_3,["です"],1) +
            entry("疲労回復","ひろうかいふく",FILLERS_3,["です"],2) +
            entry("プラセンタ","ぷらせんた",FILLERS_3,["です"],2) +
            entry("ダイエット","だいえっと",FILLERS_3,["です"],2) +
            entry("わからない","わからない",FILLERS_3)
        ),
        '入力_検査内容': dedup(
            entry("血液検査","けつえきけんさ",FILLERS_10,["です","なんですが"],2) +
            entry("アレルギー検査","あれるぎーけんさ",FILLERS_3,["です"],2) +
            entry("がん検診","がんけんしん",FILLERS_3,["です"],2) +
            entry("性病検査","せいびょうけんさ",FILLERS_3,["です"],2) +
            entry("PCR","ぴーしーあーる",FILLERS_3) +
            entry("わからない","わからない",FILLERS_3)
        ),
        '入力_心理_中医_相談': dedup(
            entry("心理","しんり",FILLERS_10,SUFFIXES_4,2) +
            entry("中医","ちゅうい",FILLERS_10,SUFFIXES_4,2) +
            entry("相談","そうだん",FILLERS_10,SUFFIXES_4,2) +
            entry("カウンセリング","かうんせりんぐ",FILLERS_3,["です"],2)
        ),
        '入力_予約希望日': build_pw_date(),
        '入力_現在の予約日': build_pw_date(),
        '入力_変更希望日': build_pw_date(),
        '入力_キャンセル希望日': build_pw_date(),
        '入力_予約内容': dedup(
            entry("日時変更","にちじへんこう",FILLERS_10,["です","なんですが"],2) +
            entry("時間変更","じかんへんこう",FILLERS_3,["です"],1) +
            entry("日にち変更","ひにちへんこう",FILLERS_3,["です"],1) +
            entry("内容変更","ないようへんこう",FILLERS_3,["です"],1) +
            entry("コース変更","こーすへんこう",FILLERS_3,["です"],1) +
            entry("担当変更","たんとうへんこう",FILLERS_3) +
            entry("確認","かくにん",FILLERS_3,["です","したい"],1) +
            entry("わからない","わからない",FILLERS_3)
        ),
    }

    for mname, pw_lines in pw_map.items():
        if mname in modules:
            modules[mname]['params']['profile_words'] = '\n'.join(pw_lines)
            all_fixes.append(f'PW: {mname} → {len(pw_lines)}語')

    # 全モジュール正規化
    for mname in list(modules.keys()):
        mod = modules[mname]
        ensure_fields(mod, mname)
        fix_slots(mod)
        modules[mname] = reorder_keys(mod, mname)

    with open(main_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # ================================================================
    # サブフロー修正
    # ================================================================
    sf_files = [
        ("氏名", OUTPUT_DIR / "海風診療所_氏名聴取_20260409.json", "入力_患者_氏名"),
        ("生年月日", OUTPUT_DIR / "海風診療所_生年月日聴取_20260409.json", "復唱_患者_生年月日"),
        ("電話番号", OUTPUT_DIR / "海風診療所_電話番号聴取_20260409.json", None),
        ("RAG", OUTPUT_DIR / "海風診療所_RAG検索_20260409.json", None),
    ]

    for label, sf_path, ret_source in sf_files:
        with open(sf_path, encoding='utf-8') as f:
            sf = json.load(f)
        mods = sf['modules']

        # detection_flag
        for name, mod in mods.items():
            t = mod.get('type','')
            if 'Speech to Text' in t or 'DTMF' in t:
                mod.setdefault('params',{})['detection_flag'] = 'デフォルト'

        # DTMF retry
        for name, mod in mods.items():
            if 'DTMF' in mod.get('type',''):
                if mod.get('params',{}).get('retry') == '0':
                    mod['params']['retry'] = '2'
                    all_fixes.append(f'DTMF retry: {name} 0→2')

        # 結果返却スクリプト追加（氏名/生年月日）
        if ret_source and f'script_結果返却_{label}' not in mods:
            # STT success遷移先設定
            for name, mod in mods.items():
                if 'Speech to Text' in mod.get('type','') or 'DTMF' in mod.get('type',''):
                    for n in mod.get('next',[]):
                        if n.get('condition') == '^.+$' and not n.get('nextModuleName'):
                            n['nextModuleName'] = f'script_結果返却_{label}'
                # OpenAI肯定遷移
                if 'generate_by_OpenAI' in mod.get('type',''):
                    for n in mod.get('next',[]):
                        if n.get('condition') == '^肯定$' and not n.get('nextModuleName'):
                            n['nextModuleName'] = f'script_結果返却_{label}'
                # Retry false
                if 'Retry Counter' in mod.get('type',''):
                    for n in mod.get('next',[]):
                        if n.get('condition') == 'false' and not n.get('nextModuleName'):
                            n['nextModuleName'] = f'script_結果返却_{label}'

            ret_mod = make_return_mod(ret_source, 0, 1200, f'script_結果返却_{label}')
            mods[f'script_結果返却_{label}'] = ret_mod
            all_fixes.append(f'SCR-002: script_結果返却_{label} 追加')

        # 生年月日 OAI-002修正
        if label == '生年月日':
            oai = mods.get('openAI_復唱_患者生年月日', {})
            if oai.get('params',{}).get('module') == '入力_患者_復唱連絡先':
                oai['params']['module'] = '入力_復唱_患者生年月日'
                all_fixes.append('OAI-002: openAI module参照修正')

        # リトライfalse修正
        sf_retry_fixes = fix_retry_false(mods)
        all_fixes.extend(sf_retry_fixes)

        # 全モジュール正規化
        for mname in list(mods.keys()):
            mod = mods[mname]
            ensure_fields(mod, mname)
            fix_slots(mod)
            mods[mname] = reorder_keys(mod, mname)

        with open(sf_path, 'w', encoding='utf-8') as f:
            json.dump(sf, f, ensure_ascii=False, indent=2)

    # ================================================================
    # レイアウト修正（メインフロー）
    # ================================================================
    with open(main_path, encoding='utf-8') as f:
        data = json.load(f)
    modules = data['modules']

    # 全モジュールをx=-500シフト（x=500起点→x=0起点）
    for name, mod in modules.items():
        ly = mod.get('layout',{})
        ly['x'] = ly.get('x',0) - 500

    # y座標を拡張（y_range >= 118*100 = 11800px）
    current_y_vals = [mod.get('layout',{}).get('y',0) for mod in modules.values()]
    current_range = max(current_y_vals) - min(current_y_vals)
    target_range = len(modules) * 100
    if current_range < target_range:
        scale = target_range / current_range if current_range > 0 else 1
        min_y = min(current_y_vals)
        for name, mod in modules.items():
            ly = mod.get('layout',{})
            old_y = ly.get('y',0)
            ly['y'] = int((old_y - min_y) * scale + min_y)

    # 重なり解消
    coords = {}
    for name, mod in modules.items():
        ly = mod.get('layout',{})
        key = (ly.get('x',0), ly.get('y',0))
        if key in coords:
            ly['y'] += 150  # 150px下にずらす
            all_fixes.append(f'重なり解消: {name} y+150')
        coords[(ly.get('x',0), ly.get('y',0))] = name

    with open(main_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    all_fixes.append('レイアウト修正: x=0起点, y拡張, 重なり解消')

    # ================================================================
    print(f"=== 海風診療所 全Stage修正 ({len(all_fixes)}件) ===\n")
    for f in all_fixes[:30]:
        print(f"  ✓ {f}")
    if len(all_fixes) > 30:
        print(f"  ... 他{len(all_fixes)-30}件")

if __name__ == "__main__":
    main()
