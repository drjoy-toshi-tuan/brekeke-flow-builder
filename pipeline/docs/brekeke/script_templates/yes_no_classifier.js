// [SCRIPT-YESNO] Yes/No 決定論分類（ECHO_YESNO_PROMPT 置換）。完全一致＋マーカー走査（否定優先）。
// parity: yes_no_classifier/oracle.py（同一辞書・同一手順・同一順序）。テストの正は acceptance_test/cases.tsv。
// 入力: $runner.getModuleResult(SOURCE_MODULE) / 出力: "肯定" | "否定" | "NO_RESULT"
// Nashorn(ES5.1)想定: String.normalize 不使用の限定正規化（全角数字/英字→半角・ASCII小文字化・記号空白除去）。
// ※ SOURCE_MODULE は組込先ごとの設定行（インスタンスパラメータ）。これ以外の行の改変は再受入。
// @part-id: yes_no_classifier
// @engine-version: v2
//
// 【テンプレート（穴あき正本）】
//   この .js は modules/yes_no_classifier/script.js（認定 filled 正本）と engine/spec が完全一致する穴あき版。
//   build_script が {{INPUT_MODULE}} を充填して @General$Script を生成する（A3 #2 出口）。
//   - wiring（設定行・hash 除外）: {{INPUT_MODULE}} … 直前の入力（STT/DTMF）モジュール名。var SOURCE_MODULE に充填。
//   - spec（規格・受入必須・@spec ブロック・hash 認定対象）: EXACT_YES / EXACT_NO / WAKARANAI_MARKERS /
//     NO_MARKERS / YES_MARKERS … 普遍ポーラ語彙（全用途共通。施設別に変えない）。
//   出力は固定で「肯定 / 否定 / NO_RESULT」。設計書の二択分岐（肯定/否定）に build_script が next 配線する。
//   ※ 純ポーラ判定（はい・いいえ系・あり/なし・希望/希望しない 等の polar 回答）専用。
//     本人/家族・個人/企業・検査/診察 等「中身の vocab が可変」な二択は n_choice（施設別 spec）の領分。
var SOURCE_MODULE = "{{INPUT_MODULE}}";

// @spec-begin
var EXACT_YES = [
  "はい", "はいです", "はいそうです", "そうです", "そうですね", "そうですよ",
  "ええ", "うん", "はいはい",
  "大丈夫", "大丈夫です", "合ってます", "合っています", "あってます", "あっています",
  "正しいです", "それで", "それでお願いします", "お願いします",
  "オッケー", "おっけー", "ok", "いち",
  "いいです", "いいですよ", "いいよ",
  "ございます", "問題ないです", "問題ありません", "構いません", "構わないです", "かまいません",
  "います", "いる"
];

var EXACT_NO = [
  "いいえ", "いえ", "いや",
  "違います", "ちがいます", "違う", "ちがう", "違いました",
  "間違い", "間違いです", "間違っています",
  "ダメ", "だめ", "駄目", "やめて", "やり直し", "もう一度",
  "に", "いません", "いない", "ありません", "ないです", "当てはまりません"
];

var WAKARANAI_MARKERS = [
  "わからない", "わかりません", "わかんない", "分からない", "分かりません"
];

// 部分一致・否定優先。「ない」単独は誤爆するため述語形のみ（REQUIREMENTS 参照）
var NO_MARKERS = [
  "当てはまりません", "ありません", "ないそうです", "ないです",
  "違います", "ちがいます", "違いました", "違う", "ちがう",
  "いいえ", "間違い", "駄目", "だめ", "ダメ", "やめて", "やり直し"
];

var YES_MARKERS = [
  "当てはまります", "そうです", "あります", "お願いします", "希望します", "はい"
];
// @spec-end

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  s = "" + Java.type("java.text.Normalizer").normalize(s, Java.type("java.text.Normalizer$Form").NFKC); // NFKC: 半角カナ/全半/互換を正規化（FAQ Matcher と同方式）
  // 全角数字→半角
  s = s.replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  // 全角英字→半角小文字
  s = s.replace(/[Ａ-Ｚａ-ｚ]/g, function (c) {
    var h = String.fromCharCode(c.charCodeAt(0) - 0xFEE0);
    return h.toLowerCase();
  });
  // ASCII 大文字→小文字
  s = s.replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
  // 句読点・記号・空白の除去（oracle.py PUNCT と同一集合。長音「ー」は除去しない）
  var strip = ["、", "。", "，", "．", ",", ".", "・", "･", ":", ";", "：", "；",
               "!", "！", "?", "？", "…", "‥", "〜", "～", "「", "」", "『", "』",
               "(", ")", "（", "）", "[", "]", "【", "】", "<", ">", "＜", "＞",
               "\"", "'", "“", "”", "‘", "’", "｢", "｣", "-",
               "　", " ", "\t", "\r", "\n"];
  for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
  return s;
}

function decide(s) {
  // 1. 空
  if (s === "") return "NO_RESULT";
  // 2. 数字のみ（DTMF 流入）
  if (/^[0-9]+$/.test(s)) {
    if (s === "1") return "肯定";
    if (s === "2") return "否定";
    return "NO_RESULT";
  }
  var i;
  // 3. 完全一致（肯定）
  for (i = 0; i < EXACT_YES.length; i++) { if (s === EXACT_YES[i]) return "肯定"; }
  // 4. 完全一致（否定）
  for (i = 0; i < EXACT_NO.length; i++) { if (s === EXACT_NO[i]) return "否定"; }
  // 5. わからない検知（「ないです」誤爆防止のためマーカー走査より先）
  for (i = 0; i < WAKARANAI_MARKERS.length; i++) { if (s.indexOf(WAKARANAI_MARKERS[i]) >= 0) return "NO_RESULT"; }
  // 6. 否定マーカー走査（否定優先）
  for (i = 0; i < NO_MARKERS.length; i++) { if (s.indexOf(NO_MARKERS[i]) >= 0) return "否定"; }
  // 7. 肯定マーカー走査
  for (i = 0; i < YES_MARKERS.length; i++) { if (s.indexOf(YES_MARKERS[i]) >= 0) return "肯定"; }
  // 8. 不一致
  return "NO_RESULT";
}

var r = $runner.getModuleResult(SOURCE_MODULE);
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var norm = nrm(raw);
var out = decide(norm);
$runner.getLogger().info("[SCRIPT-YESNO] raw=" + raw + " norm=" + norm + " out=" + out);
$runner.setResult(out);
