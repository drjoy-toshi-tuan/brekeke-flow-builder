"""inquiry_classifier — Python オラクル（script.js v1 の独立再現）

総合相談室の「ご用件」自由発話を決定論分類する。script.js と 1:1。
出力: 相談 / 予約 / 大代表 / 定型案内 / その他 / NO_RESULT
優先順位（顧客大原則）: 相談 ＞ 予約 ＞ 大代表 ＞ 定型案内（RULES 配列順・先勝ち）。
"""
import re

# RULES（配列順＝優先順位。groups は AND、exclude は排他）
RULES = [
    {"label": "相談",
     "groups": [r"相談|ご相談|総合相談室|相談室|退院|退院調整|転院|ケアマネ|ケアマネージャー|在宅|介護|医療相談|ソーシャルワーカー|ソーシャルワーカ|MSW|PSW"],
     "exclude": ""},
    {"label": "予約",
     "groups": [r"予約|ご予約|受診予約|外来予約|予約変更|予約の変更|予約確認|予約の確認|受診|診察|外来|キャンセル|取り消し|取消"],
     "exclude": ""},
    {"label": "大代表",
     "groups": [r"代表|代表番号|大代表|別の部署|他の部署|違う部署|別の窓口|かけ間違|間違え|担当部署"],
     "exclude": ""},
    {"label": "定型案内",
     "groups": [r"場所|駐車場|行き方|道順|アクセス|受付時間|診療時間|外来時間|面会時間|何時|営業時間|電話番号|番号"],
     "exclude": ""},
]

NO_QUESTION = re.compile(r"^(特にありません|特にないです|特にない|ないです|ありません|なし|無し|大丈夫です|だいじょうぶです|結構です|けっこうです|以上です|いじょうです)$")
FILLER_ONLY = re.compile(r"^(えー[っとー]*|えっと|えーっと|あのー?|うーん?|まあ|その|はい|うん|ん+)+$")
_PUNCT = re.compile(r"[、。,.!?！？\s\r\n\t]")
_DIGITS_ONLY = re.compile(r"^[0-9０-９]+$")


def classify(input_text):
    """用件分類。返り値: 相談/予約/大代表/定型案内/その他/NO_RESULT"""
    if input_text is None or input_text == "":
        return "NO_RESULT"
    normalized = _PUNCT.sub("", str(input_text))
    if normalized == "":
        return "NO_RESULT"
    if NO_QUESTION.match(normalized):
        return "NO_RESULT"
    if FILLER_ONLY.match(normalized):
        return "NO_RESULT"
    if _DIGITS_ONLY.match(normalized):
        return "NO_RESULT"
    for rule in RULES:
        if rule["exclude"] and re.search(rule["exclude"], normalized):
            continue
        if all(re.search(g, normalized) for g in rule["groups"]):
            return rule["label"]
    # 何らかの発話はあるがキーワード非該当 → その他（伝言・折返しの安全な受け皿）
    return "その他"
