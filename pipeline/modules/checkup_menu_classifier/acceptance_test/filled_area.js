// [SCRIPT-MENU] 健診CC メニュー選択 決定論分類（エリア選択/施設選択×2 の generate_by_OpenAI 置換）。
// parity: checkup_menu_classifier/oracle.py（同一辞書・同一手順・同一順序）。テストの正は acceptance_test/cases.tsv。
// 入力: $runner.getModuleResult(SOURCE_MODULE) / 出力: メニュー別ラベル | "NO_RESULT"
// Nashorn(ES5.1)想定。※ SOURCE_MODULE / MENU の2行のみ組込先ごとの設定行。これ以外の行の改変は再受入。
// @part-id: checkup_menu_classifier
// @engine-version: v2
var SOURCE_MODULE = "__SOURCE_MODULE__";
// @spec-begin
var MENU = "area"; // "area" | "shinjuku_shibuya" | "tokyo_shinagawa"
// @spec-end

// @spec-begin
var WAKARANAI_MARKERS = [
  "わからない", "わかりません", "わかんない", "分からない", "分かりません"
];
// @spec-end

// MENU 別定義（DTMF 表 + 語彙。語彙は定義順＝優先順）
// @spec-begin
var MENUS = {
  "area": {
    dtmf: { "1": "神奈川エリア", "2": "新宿渋谷エリア", "3": "東京品川エリア" },
    vocab: [
      ["神奈川エリア", ["厚木", "あつぎ"]],
      ["新宿渋谷エリア", ["ヒロオカ", "広岡", "渋谷ウエスト", "west", "ウェスト"]],
      ["東京品川エリア", ["秋葉原", "あきはばら", "鉄鋼ビル", "丸の内", "まるのうち", "みなと健診"]],
      ["神奈川エリア", ["神奈川", "かながわ"]],
      ["新宿渋谷エリア", ["新宿", "しんじゅく", "渋谷", "しぶや"]],
      ["東京品川エリア", ["東京", "とうきょう", "品川", "しながわ"]],
      ["神奈川エリア", ["一番", "1番"]],
      ["新宿渋谷エリア", ["二番", "2番"]],
      ["東京品川エリア", ["三番", "3番"]]
    ]
  },
  "shinjuku_shibuya": {
    dtmf: { "1": "ヒロオカクリニック", "2": "渋谷ウエストクリニック" },
    vocab: [
      ["ヒロオカクリニック", ["ヒロオカ", "ひろおか", "広岡"]],
      ["渋谷ウエストクリニック", ["渋谷ウエスト", "ウエスト", "west", "ウェスト"]],
      ["ヒロオカクリニック", ["一番", "1番"]],
      ["渋谷ウエストクリニック", ["二番", "2番"]]
    ]
  },
  "tokyo_shinagawa": {
    dtmf: { "1": "ヘルスケアクリニック秋葉原", "2": "鉄鋼ビル丸の内クリニック", "3": "みなと健診クリニック" },
    vocab: [
      ["ヘルスケアクリニック秋葉原", ["秋葉原", "あきはばら"]],
      ["鉄鋼ビル丸の内クリニック", ["鉄鋼ビル", "丸の内", "まるのうち"]],
      ["みなと健診クリニック", ["みなと", "港"]],
      ["ヘルスケアクリニック秋葉原", ["一番", "1番"]],
      ["鉄鋼ビル丸の内クリニック", ["二番", "2番"]],
      ["みなと健診クリニック", ["三番", "3番"]]
    ]
  }
};
// @spec-end

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  s = "" + Java.type("java.text.Normalizer").normalize(s, Java.type("java.text.Normalizer$Form").NFKC); // NFKC: 半角カナ/全半/互換を正規化（FAQ Matcher と同方式）
  s = s.replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  s = s.replace(/[Ａ-Ｚａ-ｚ]/g, function (c) {
    var h = String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
    return h.toLowerCase();
  });
  s = s.replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
  var strip = ["、", "。", "，", "．", ",", ".", "・", "･", ":", ";", "：", "；",
               "!", "！", "?", "？", "…", "‥", "〜", "～", "「", "」", "『", "』",
               "(", ")", "（", "）", "[", "]", "【", "】", "<", ">", "＜", "＞",
               "\"", "'", "“", "”", "‘", "’", "｢", "｣", "-",
               "　", " ", "\t", "\r", "\n"];
  for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
  return s;
}

function decide(s, cfg) {
  // 1. 空
  if (s === "") return "NO_RESULT";
  // 2. 数字のみ → MENU 別 DTMF 表
  if (/^[0-9]+$/.test(s)) {
    return cfg.dtmf.hasOwnProperty(s) ? cfg.dtmf[s] : "NO_RESULT";
  }
  var i, k;
  // 3. わからない検知
  for (i = 0; i < WAKARANAI_MARKERS.length; i++) { if (s.indexOf(WAKARANAI_MARKERS[i]) >= 0) return "NO_RESULT"; }
  // 4. MENU 別語彙走査（定義順・部分一致）
  for (i = 0; i < cfg.vocab.length; i++) {
    var keys = cfg.vocab[i][1];
    for (k = 0; k < keys.length; k++) { if (s.indexOf(keys[k]) >= 0) return cfg.vocab[i][0]; }
  }
  // 5. 不一致
  return "NO_RESULT";
}

var cfg = MENUS[MENU];
var r = $runner.getModuleResult(SOURCE_MODULE);
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var norm = nrm(raw);
var out = (cfg == null) ? "NO_RESULT" : decide(norm, cfg);
$runner.getLogger().info("[SCRIPT-MENU] menu=" + MENU + " raw=" + raw + " norm=" + norm + " out=" + out);
$runner.setResult(out);
