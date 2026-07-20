"""n_choice — Python オラクル（script.js v4 の独立再現）

script.js（Brekeke / Nashorn ES5）の判定ロジックを Python で 1:1 に再現する。
n_choice は「設定（DTMF_MAP / TOKEN_MAP / *_PATTERNS）」を施設・設問ごとに充填する
汎用 N 択エンジンなので、oracle も config を引数で受け取る純関数として実装する。

判定順（script.js と同一）:
  空 → 正規化 → DTMF(単一数字) → TOKEN(完全一致) → 先頭数字+語 → 複合 → 単独keyword
  → filler のみ → no_match（いずれも NO_RESULT）
"""
import re

# 正規化で使うフィラー（先頭/末尾から除去）
_FILLER = r"(えーと|えーっと|えー|あのー|あの|うーんと|うーん|まー|まあ|そうですね|えっと|そのー|あー|んー|んーと|ねえ|ちょっと)+"
_DIALECT = r"(だべさ|だべ|っしょ|べし|だす|んだ|じゃん|だよね|じゃね|やん|やねん|やで|やんか|やわ|ねん|やろ|じゃけん|じゃけ|けん|ばい|たい|さー|さあ)$"
_POLITE = r"(でございます|ございます|いただけますか|いただきたい|させていただきたい|でしょうか|いたします|ですよね|ですわ|だわ)$"
_CASUAL = r"(だよ|だね|だぜ|だろ|じゃね|じゃん|っす|すか|かよ|だっけ|っけ|だわ|やん|やろ|やで|けど|けんど|だに|ずら|だら)$"
_POLITE2 = r"(です|でお願いします|お願いします|なんですけど|にお願い|ですけど|なんですが|をお願い)$"
_FILLER_ONLY = r"^(えー[っとー]*|えっと|えーっと|あのー?|うーん?|まあ|その|はい|うん|ん+)+$"
_DIGIT_SUFFIX = r"^([0-9])(です|だ|でお願いします|でお願い|ね|よ|かな)+$"
_PUNCT = r"[、。,.:;!?！？「」『』（）()\s\r\n\t]"


def _normalize(s):
    """script.js の正規化を忠実に再現。"""
    # 全角数字 → 半角
    s = "".join(chr(ord(c) - 0xFEE0) if "０" <= c <= "９" else c for c in s)
    # 記号・空白除去
    s = re.sub(_PUNCT, "", s)
    # 先頭/末尾フィラー除去
    s = re.sub("^" + _FILLER, "", s)
    s = re.sub(_FILLER + "$", "", s)
    # 方言/敬語/タメ口 接尾辞除去
    s = re.sub(_DIALECT, "", s)
    s = re.sub(_POLITE, "", s)
    s = re.sub(_CASUAL, "", s)
    s = re.sub(_POLITE2, "", s)
    # AmiVoice カテゴリ重複正規化: "再診再診" → "再診"
    if len(s) >= 4:
        for dl in range(len(s) // 2, 1, -1):
            chunk = s[:dl]
            if re.match("^(" + re.escape(chunk) + ")+$", s):
                s = chunk
                break
    # 数字＋語尾 trim: "1です" → "1"
    m = re.match(_DIGIT_SUFFIX, s)
    if m:
        s = m.group(1)
    return s


def classify(input_text, config):
    """N 択判定。config = {
        'dtmf_map': {'1':'ラベル',...},
        'token_map': [{'regex':'...','result':'ラベル'},...],
        'digit_keyword_patterns': [{'digit':'1','regex':'...','result':'ラベル'},...],
        'compound_patterns': [{'regex':'...','result':'ラベル'},...],
        'keyword_patterns': [{'regex':'...','result':'ラベル'},...],
    }
    返り値: ラベル文字列 / 'NO_RESULT'
    """
    dtmf_map = config.get("dtmf_map", {})
    token_map = config.get("token_map", [])
    digit_keyword_patterns = config.get("digit_keyword_patterns", [])
    compound_patterns = config.get("compound_patterns", [])
    keyword_patterns = config.get("keyword_patterns", [])

    if input_text is None or input_text == "":
        return "NO_RESULT"

    s = _normalize(str(input_text))
    if s == "":
        return "NO_RESULT"

    # DTMF（単一数字）
    if re.match(r"^[0-9]$", s):
        return dtmf_map[s] if s in dtmf_map else "NO_RESULT"

    # TOKEN（完全一致）
    for t in token_map:
        if re.match("^(" + t["regex"] + ")$", s):
            return t["result"]

    # 先頭数字 + 語
    hd = re.match(r"^([0-9])", s)
    if hd:
        for dk in digit_keyword_patterns:
            if dk["digit"] == hd.group(1) and re.search(dk["regex"], s):
                return dk["result"]

    # 複合（先に評価）
    for cp in compound_patterns:
        if re.search(cp["regex"], s):
            return cp["result"]

    # 単独 keyword
    for kp in keyword_patterns:
        if re.search(kp["regex"], s):
            return kp["result"]

    # filler のみ
    if re.match(_FILLER_ONLY, s):
        return "NO_RESULT"

    return "NO_RESULT"


# ============================================================================
# spec 自己整合性 lint（#245）— テスト除外でなく spec 修正を強制するためのマシンガード
# ----------------------------------------------------------------------------
# 「テストで落ちるケースをテスト対象から除外して合格にする」運用を機械的に封じる。
# 核心の不変条件: 各 token/keyword/compound パターンの "単純リテラル選択肢" L は、
# それ自身を入力したとき自分の result に分類されねばならない（classify(L)==result）。
#   - 正規化で語尾が消えて死ぬ keyword（例「そうです」→「そう」で keyword「そうです」に非ヒット）を検出。
#   - 先行する広いパターンに食われる shadow（例 後置の「予約変更」が先行「予約」に奪われる）を検出。
# digit_keyword_patterns は先頭数字必須でリテラル単体検査が成立しないため対象外。
# ============================================================================

# 正規表現メタ文字。これを含む選択肢は「単純リテラル」とみなさず lint 対象外（誤検出回避）。
_REGEX_META = set(".*+?()[]{}\\|")


def _literal_alternatives(regex):
    """正規表現を top-level '|' で割り、メタ文字を含まない単純リテラル選択肢だけ返す。
    先頭 ^ / 末尾 $ のアンカーは剥がしてから判定する（例「^はい」→「はい」）。"""
    out = []
    for alt in str(regex).split("|"):
        a = alt
        if a.startswith("^"):
            a = a[1:]
        if a.endswith("$"):
            a = a[:-1]
        if not a:
            continue
        if any(c in _REGEX_META for c in a):
            continue
        out.append(a)
    return out


def lint_config(config):
    """spec 設定の自己整合性 lint。問題リストを返す（空なら健全）。

    各問題 = {where, literal, result, got}:
      where   … token_map / compound_patterns / keyword_patterns
      literal … 検査したリテラル
      result  … その設定が宣言する分類結果
      got     … 実際の classify(literal) の結果（result と不一致＝問題）
    """
    issues = []
    groups = [
        ("token_map", config.get("token_map", [])),
        ("compound_patterns", config.get("compound_patterns", [])),
        ("keyword_patterns", config.get("keyword_patterns", [])),
    ]
    for where, entries in groups:
        for e in entries:
            result = e.get("result")
            for lit in _literal_alternatives(e.get("regex", "")):
                got = classify(lit, config)
                if got != result:
                    issues.append({
                        "where": where,
                        "literal": lit,
                        "result": result,
                        "got": got,
                    })
    return issues


# ============================================================================
# P6 受入カバレッジ（#245）— 受入ケース集合が spec の判定要素を何 % 発火させたか
# ----------------------------------------------------------------------------
# 「通る言い回しだけ並べて落ちる言い回しを避ける」狭いスコープを定量検出する。
#   - 構造カバレッジ: ラベル / DTMF / NO_RESULT。本来 100% であるべき → ゲート FAIL 対象。
#   - 表面カバレッジ: keyword/token/compound の各リテラル選択肢。dodge した言い回しが
#     未カバー一覧として出る → 計測表示（WARN・スコア向上はスコアカード PJ）。
# lint_config（各パターンが発火し "得る"）と対。coverage（各パターンが実際に発火 "した"）。
# ============================================================================

# top-level '|' 分割で全選択肢がメタ文字なし（アンカー除く）なら選択肢粒度、そうでなければ
# パターン粒度で要素を数える。lint と同じ判定基準を使い、母集合と発火 id を一致させる。
def _plain_alts_or_none(regex):
    alts = []
    for alt in str(regex).split("|"):
        a = alt
        if a.startswith("^"):
            a = a[1:]
        if a.endswith("$"):
            a = a[:-1]
        if not a or any(c in _REGEX_META for c in a):
            return None
        alts.append(a)
    return alts or None


def _fired_element(prefix, idx, regex, s, full=False):
    """発火したパターンの要素 id を返す（母集合 id と同じ命名規則）。"""
    plain = _plain_alts_or_none(regex)
    if plain is None:
        return "%s:%d" % (prefix, idx)
    for a in plain:
        hit = re.match("^(" + re.escape(a) + ")$", s) if full else re.search(re.escape(a), s)
        if hit:
            return "%s:%d:%s" % (prefix, idx, a)
    return "%s:%d" % (prefix, idx)


def classify_trace(input_text, config):
    """classify と同一判定を行い (result, 発火要素 id) を返す。
    要素 id: dtmf:<digit> / token:<i>[:<alt>] / digit:<i> / compound:<i>[:<alt>]
    / keyword:<i>[:<alt>] / NO_RESULT。"""
    dtmf_map = config.get("dtmf_map", {})
    token_map = config.get("token_map", [])
    digit_keyword_patterns = config.get("digit_keyword_patterns", [])
    compound_patterns = config.get("compound_patterns", [])
    keyword_patterns = config.get("keyword_patterns", [])

    if input_text is None or input_text == "":
        return "NO_RESULT", "NO_RESULT"
    s = _normalize(str(input_text))
    if s == "":
        return "NO_RESULT", "NO_RESULT"

    if re.match(r"^[0-9]$", s):
        if s in dtmf_map:
            return dtmf_map[s], "dtmf:" + s
        return "NO_RESULT", "NO_RESULT"

    for i, t in enumerate(token_map):
        if re.match("^(" + t["regex"] + ")$", s):
            return t["result"], _fired_element("token", i, t["regex"], s, full=True)

    hd = re.match(r"^([0-9])", s)
    if hd:
        for i, dk in enumerate(digit_keyword_patterns):
            if dk["digit"] == hd.group(1) and re.search(dk["regex"], s):
                return dk["result"], "digit:%d" % i

    for i, cp in enumerate(compound_patterns):
        if re.search(cp["regex"], s):
            return cp["result"], _fired_element("compound", i, cp["regex"], s)

    for i, kp in enumerate(keyword_patterns):
        if re.search(kp["regex"], s):
            return kp["result"], _fired_element("keyword", i, kp["regex"], s)

    if re.match(_FILLER_ONLY, s):
        return "NO_RESULT", "NO_RESULT"
    return "NO_RESULT", "NO_RESULT"


def coverage(config, inputs):
    """受入ケース入力集合 inputs が spec の判定要素を何 % 発火させたかを返す。

    返り値 dict:
      labels       : (covered:list, total:list)  全結果ラベルの被覆
      dtmf         : (covered:list, total:list)  DTMF 各桁の被覆
      no_result_case: bool                        NO_RESULT を期待するケースが 1 件以上あるか
      surface      : (covered:list, total:list)  keyword/token/compound の各リテラル選択肢の被覆
      structural_ok: bool                         labels 全被覆 ∧ dtmf 全被覆 ∧ no_result_case
    """
    dtmf_map = config.get("dtmf_map", {})
    labels = set(dtmf_map.values())
    surface = []
    for grp, prefix in (
        ("token_map", "token"),
        ("compound_patterns", "compound"),
        ("keyword_patterns", "keyword"),
        ("digit_keyword_patterns", "digit"),
    ):
        for i, e in enumerate(config.get(grp, [])):
            if e.get("result") is not None:
                labels.add(e["result"])
            plain = _plain_alts_or_none(e.get("regex", ""))
            if plain is None:
                surface.append("%s:%d" % (prefix, i))
            else:
                surface.extend("%s:%d:%s" % (prefix, i, a) for a in plain)
    labels.discard("NO_RESULT")

    fired = set()
    results = []
    for x in inputs:
        r, eid = classify_trace(x, config)
        results.append(r)
        fired.add(eid)

    covered_labels = labels & set(results)
    covered_dtmf = {d for d in dtmf_map if ("dtmf:" + d) in fired}
    has_no_result = any(r == "NO_RESULT" for r in results)
    surface_set = set(surface)
    covered_surface = surface_set & fired

    structural_ok = (
        covered_labels == labels
        and covered_dtmf == set(dtmf_map)
        and has_no_result
    )
    return {
        "labels": (sorted(covered_labels), sorted(labels)),
        "dtmf": (sorted(covered_dtmf), sorted(dtmf_map)),
        "no_result_case": has_no_result,
        "surface": (sorted(covered_surface), sorted(surface_set)),
        "structural_ok": structural_ok,
    }


# ============================================================================
# 類義語密度トリップワイヤー（#245）— スコアカード PJ への引き渡し候補を機械検出
# ----------------------------------------------------------------------------
# 実ログ無しで測れる唯一の「実発話ロバスト性」の代理指標＝施設提供の類義語リスト（spec の
# 表面形）の厚み。薄いラベルは実発話で NO_RESULT に倒れやすい＝スコアカード（実ログ）検証の
# 優先候補。coverage（テスト網羅）とは別軸（厚み≠網羅）。
#
# 合意した初期値: content ラベルの音声類義語が floor(=3) 未満 かつ DTMF 救済が無い → WARN。
# DTMF 救済のあるラベル（押下で到達可）は薄くても到達性は担保されるため WARN 対象外（情報表示のみ）。
# 「入院」「電話」のような自然な言い換えの無い単形語と、本当に薄いリストは機械では区別不能なため
# FAIL にせず WARN＋人間 ack とする。閾値は将来カタログ成熟ベースライン（中央値）に連動させる。
# ============================================================================

def synonym_forms(config):
    """ラベル → 音声類義語（単純リテラル選択肢）の集合。DTMF は数えない。"""
    forms = {}
    for grp in ("token_map", "compound_patterns", "keyword_patterns"):
        for e in config.get(grp, []):
            result = e.get("result")
            if result is None:
                continue
            forms.setdefault(result, set()).update(_literal_alternatives(e.get("regex", "")))
    return forms


def density_report(config, floor=3):
    """各 content ラベルの音声類義語の厚みと薄さ WARN を返す。

    返り値 {label: {count, forms, dtmf_backed, warn}}。
      warn = (count < floor) and (not dtmf_backed)  ← 合意した初期判定
    """
    dtmf_vals = set(config.get("dtmf_map", {}).values())
    forms = synonym_forms(config)
    labels = (set(forms) | dtmf_vals)
    labels.discard("NO_RESULT")
    out = {}
    for label in labels:
        fs = sorted(forms.get(label, set()))
        dtmf_backed = label in dtmf_vals
        out[label] = {
            "count": len(fs),
            "forms": fs,
            "dtmf_backed": dtmf_backed,
            "warn": (len(fs) < floor and not dtmf_backed),
        }
    return out


# 亀田 各設問の config（engine + 設問データを同時検証する受入用）。
# 値は output/scenarios/亀田総合病院_総合相談室 の各 n_choice インスタンスと一致。
KAMEDA_CALLER_TYPE = {
    "dtmf_map": {"1": "患者本人・家族", "2": "連携医療機関", "3": "行政"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "本人|家族|患者|母|父|親|息子|娘", "result": "患者本人・家族"},
        {"regex": "クリニック|診療所|病院|医療機関|医院|連携先", "result": "連携医療機関"},
        {"regex": "市役所|役所|役場|保健所|行政|地域包括|包括支援|福祉課", "result": "行政"},
    ],
}

# 相談区分（patientCategory）: 入院 / 外来 / 新規
KAMEDA_PATIENT_CATEGORY = {
    "dtmf_map": {"1": "入院", "2": "外来", "3": "新規"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "入院", "result": "入院"},
        {"regex": "外来|通院", "result": "外来"},
        {"regex": "新規|初めて|はじめて|初診", "result": "新規"},
    ],
}

# 担当者確認（staffKnown）: わかる / わからない
# 否定の丁寧形「わかりません/分かりません/わかりかねます/知りません」を否定側で明示し先に評価する。
# bare「わかり/分かり」での判定は禁止（肯定 わかります と否定 わかりません を取り違えるため）。2026-06-17 修正。
KAMEDA_STAFF_KNOWN = {
    "dtmf_map": {"1": "わかる", "2": "わからない"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "わからない|わかりません|分からない|分かりません|わかりかね|分かりかね|わからな|分からな|不明|いいえ|知らない|知りません|知らな", "result": "わからない"},
        {"regex": "わかる|わかります|分かる|分かります|^はい|存じ|知って", "result": "わかる"},
    ],
}

# F1（inquiryType）: 相談予約 / 受診
KAMEDA_F1 = {
    "dtmf_map": {"1": "相談予約", "2": "受診"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "相談予約|相談|予約の相談", "result": "相談予約"},
        {"regex": "受診|診察|診て|外来", "result": "受診"},
    ],
}

# ============================================================================
# A3 Phase2 部品調達（工場長）— count>=2 の真の多択を n_choice spec として調達。
# 認定（certified_hashes 登録）は実機 P6 PASS 後の人間ゲート。ここは oracle PASS まで。
# ============================================================================

# 受診歴: 再診 / 新規（count=6）
SAISHIN_SHINKI = {
    "dtmf_map": {"1": "再診", "2": "新規"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "再診|さいしん|前にかかった|通院|かかりつけ|以前", "result": "再診"},
        {"regex": "新規|初めて|はじめて|初診|今回が初", "result": "新規"},
    ],
}

# 顧客種別: 企業 / 個人（count=5）
KIGYO_KOJIN = {
    "dtmf_map": {"1": "企業", "2": "個人"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "企業|法人|会社|勤め先|勤務先", "result": "企業"},
        {"regex": "個人|自費|プライベート", "result": "個人"},
    ],
}

# 受診歴: 再診 / 初診（count=3）
SAISHIN_SHOSHIN = {
    "dtmf_map": {"1": "再診", "2": "初診"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "再診|前にかかった|通院|かかりつけ|以前", "result": "再診"},
        {"regex": "初診|初めて|はじめて|今回が初", "result": "初診"},
    ],
}

# 当日確認: 本日 / 別日（count=3）
BETSUJITSU_HONJITSU = {
    "dtmf_map": {"1": "本日", "2": "別日"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        # 別日は「本日以外」を含むので先に評価
        {"regex": "別日|別の日|明日以降|あした|明日|来週|他の日|後日|翌日", "result": "別日"},
        {"regex": "本日|今日|きょう|当日", "result": "本日"},
    ],
}

# 変更内容: 受診内容 / 日程変更（count=3）
HENKO_NAIYO_NITTEI = {
    "dtmf_map": {"1": "受診内容", "2": "日程変更"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        # 日程系を先に（「内容」と紛れないよう日付語を優先）
        {"regex": "日程|日にち|日時|予約日|スケジュール|曜日", "result": "日程変更"},
        {"regex": "受診内容|内容|コース|検査内容", "result": "受診内容"},
    ],
}

# 予約手段: ネット / 電話（count=2）
NET_DENWA = {
    "dtmf_map": {"1": "ネット", "2": "電話"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "ネット|インターネット|ウェブ|web|オンライン", "result": "ネット"},
        {"regex": "電話", "result": "電話"},
    ],
}

# 残薬確認: あり / なし / 処方されていない（count=2 / 3択）
ZANYAKU = {
    "dtmf_map": {"1": "あり", "2": "なし", "3": "処方されていない"},
    "token_map": [],
    "digit_keyword_patterns": [],
    # 「処方されていない」は否定述語を含むので compound で最優先評価。
    # 正規化で末尾「です」等が除去される（処方されていません→処方されてい）ため stem で拾う。
    "compound_patterns": [
        {"regex": "処方されてい|処方されてな|薬は出てい|薬が出てい|処方なし|処方無", "result": "処方されていない"},
    ],
    # 否定を先に評価（「ません」は正規化で残る）。肯定の「残っています→残ってい」と衝突しないよう
    # なし側は否定述語（ません/ない/飲み切）のみで拾う。
    "keyword_patterns": [
        {"regex": "ありません|残っていません|残ってない|飲み切|なし|ない", "result": "なし"},
        {"regex": "あり|残って|余って|まだある", "result": "あり"},
    ],
}

# --- カレス記念病院_診療（Pattern 1 新規・CSV入口）調達分。choices[] の number/strong 記法を
#     dtmf/strong_keywords にフォールバックする scaffold_generator.py 修正後の実出力を転記。
#     3 spec とも DTMF 1/2(/3) 付き・strong:true につき keywords 全体を COMPOUND 扱い（KEYWORD 空）。

# 受診歴確認: はい / いいえ / わからない（3択・DTMF 1/2/3）。
# いいえ を先に評価する（はい の「はじめて/初めて」が「はじめてではない/初めてではない」の
# 部分文字列に一致するシャドーを避けるため）。「そうです」は正規化で語尾が剥がれ発火しないため未使用。
JUSHINREKI_HAIIIEWAKARANAI = {
    "dtmf_map": {"2": "いいえ", "1": "はい", "3": "わからない"},
    "token_map": [
        {"regex": "^いいえ$", "result": "いいえ"},
        {"regex": "^はい$", "result": "はい"},
        {"regex": "^わからない$", "result": "わからない"},
    ],
    "digit_keyword_patterns": [],
    "compound_patterns": [
        {"regex": "(いいえ|はじめてではない|初めてではない|二回目|2回目|再診|前にも|通っている|通っています)", "result": "いいえ"},
        {"regex": "(はい|はじめて|初めて|初診|初めてです)", "result": "はい"},
        {"regex": "(わからない|わかりません|分からない|分かりません|不明)", "result": "わからない"},
    ],
    "keyword_patterns": [],
}

# 薬処方確認（変更キャンセル）: 飲んでいる / 飲んでいない（2択・DTMF 1/2）
FUKUYAKU_UMU = {
    "dtmf_map": {"1": "飲んでいる", "2": "飲んでいない"},
    "token_map": [
        {"regex": "^飲んでいる$", "result": "飲んでいる"},
        {"regex": "^飲んでいない$", "result": "飲んでいない"},
    ],
    "digit_keyword_patterns": [],
    "compound_patterns": [
        {"regex": "(飲んでいる|飲んでます|のんでいる|はい)", "result": "飲んでいる"},
        {"regex": "(飲んでいない|飲んでません|のんでいない|いいえ)", "result": "飲んでいない"},
    ],
    "keyword_patterns": [],
}

# 残薬確認（2択版・DTMF 1/2）。既存 ZANYAKU（3択・あり/なし/処方されていない）とは別 spec。
ZANYAKU_2CHOICE = {
    "dtmf_map": {"1": "はい", "2": "いいえ"},
    "token_map": [
        {"regex": "^はい$", "result": "はい"},
        {"regex": "^いいえ$", "result": "いいえ"},
    ],
    "digit_keyword_patterns": [],
    "compound_patterns": [
        {"regex": "(はい|あります|ある)", "result": "はい"},
        {"regex": "(いいえ|ありません|ない)", "result": "いいえ"},
    ],
    "keyword_patterns": [],
}

# 用件聴取（被覆スコアカード逆設計・全施設95万発話・音声グループ被覆97.2%／#271）。
# 被覆スコアカードPJ（ストア）手渡し INQUIRY_BASE をそのまま調達（VFB 正本エンジンで oracle 33/33・lint 0 検証済）。
# 施設は DTMF_MAP のキー順と facility オプション（相談/大代表/定型案内）を差し替えて instantiate（各々再 P6）。
# compound=specific sub-intent（キャンセル>変更>確認>疑義照会>健診）を generic「予約」より先に評価（先勝ち）。
# 「薬」= STT の予約化け（薬含む発話の72%が予約動詞共起）→ 予約新規へ吸収（根治は STT 辞書=E 層）。
# 診療科指定は「予約新規」の下位聴取（department_classifier）へ回すので用件メニューには持たない。
INQUIRY_BASE = {
    # 既定メニュー順（押下分布 1=予約新規/2=変更 が最多に符合）。施設で入れ替え可。
    "dtmf_map": {
        "1": "予約新規", "2": "予約変更", "3": "予約キャンセル",
        "4": "予約確認", "5": "健診", "0": "その他",
    },
    "token_map": [],
    "digit_keyword_patterns": [],
    # specific sub-intent を先に（generic「予約」より前＝先勝ち）
    "compound_patterns": [
        {"regex": "キャンセル|取り消|取消|とりけ|解約|中止", "result": "予約キャンセル"},
        {"regex": "変更|変え|日にち|日時|ずらし|振り替え|振替|リスケ|変わっ", "result": "予約変更"},
        {"regex": "確認|あってる|合ってる|取れてる|とれてる|入ってる|入ってます", "result": "予約確認"},
        {"regex": "疑義照会|疑義紹介|疑義", "result": "疑義照会"},
        {"regex": "健診|検診|人間ドック|ドック|健康診断", "result": "健診"},
    ],
    # generic 予約（新規/受診）＋ STT 化け（ようやく/要約/薬=予約）／ その他・折返し
    "keyword_patterns": [
        {"regex": "予約|受診|診察|外来|初診|再診|ようやく|よやく|要約|薬|診療", "result": "予約新規"},
        {"regex": "その他|問い合わせ|問合せ|尋ね|折り返し|折返し|着信", "result": "その他"},
    ],
}
