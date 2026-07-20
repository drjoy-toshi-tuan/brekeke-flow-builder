// @part-id: text_normalizer
// @engine-version: v2
//
// text_normalizer — 自由テキスト聴取値のクリーン化エンジン（変換器・分類はしない）。
// 認定仕様: docs/governance/part-certification-spec.md
//   engine = 全用途でバイト不変のアルゴリズム（engine_hash 対象）
//   spec   = 施設/設問ごとに正当に変わるデータ（@spec で囲う・spec_hash 対象）
//   wiring = 入力元/保存先（part.json の wiring_vars に列挙・両ハッシュから除外）
//
// oracle.py と同一ロジック（parity 必須）:
//   1. 句読点正規化（，→、 ．→。）
//   2. 全角英数字・記号→半角 / 全角スペース→半角
//   3. フィラー除去（トークン境界のみ・最長一致・直後の読点ごと）
//   4. 連続空白圧縮・trim / 連続読点圧縮 / 先頭末尾の句読点除去
//   5. 文末の丁寧体コピュラ除去（です/でした/ですね/ですよ/ですわ のみ。
//      「ます」系は動詞語幹を壊す/「ません」は否定の意味を反転させるため対象外・v2で追加）
//   6. 空になったら元の trim 済み文字列を返す（冪等・情報を捨てない）
// 意味の書き換え（要約・言い換え・敬語変換）はしない。

// --- wiring（part.json の wiring_vars に列挙すること）---
var SOURCE_MODULE = "{{SOURCE_MODULE}}";

// @spec-begin
// generic_free_text: フィラー語彙（長い順 = 最長一致）。
// 施設固有の口癖・方言フィラーを足す場合は spec 変更 → 再受入。
var FILLERS = [
  "なんていうか", "あのですね", "うーんと", "ええと",
  "えーっと", "えーと", "えっと", "あのー", "あのう",
  "そのー", "そのう", "うーん", "なんか",
  "まぁ", "まあ", "えー", "あー", "うー"
];
// @spec-end

// （ここから下が engine = 不変アルゴリズム。placeholder を置かないこと）
var logger = $runner.getLogger();

function toHalfwidth(text) {
  var out = "";
  for (var i = 0; i < text.length; i++) {
    var ch = text.charAt(i);
    var code = text.charCodeAt(i);
    if (ch === "　") {            // 全角スペース
      out += " ";
    } else if (code >= 0xFF01 && code <= 0xFF5E) {
      out += String.fromCharCode(code - 0xFEE0);
    } else {
      out += ch;
    }
  }
  return out;
}

function stripFillers(text) {
  var changed = true;
  while (changed) {
    changed = false;
    for (var i = 0; i < FILLERS.length; i++) {
      var f = FILLERS[i];
      if (text.indexOf(f) === 0) {                       // 先頭のフィラー
        var rest = text.substring(f.length);
        rest = rest.replace(/^[、,。\s]+/, "");
        text = rest;
        changed = true;
        break;
      }
      // 読点・句点・空白の直後のフィラー（境界 1 文字を残して除去）
      var idx = -1;
      var search = 0;
      while (true) {
        var p = text.indexOf(f, search);
        if (p <= 0) { break; }
        var prev = text.charAt(p - 1);
        if (prev === "、" || prev === "," || prev === "。" ||
            prev === " " || prev === "\t" || prev === "\n") {
          idx = p;
          break;
        }
        search = p + 1;
      }
      if (idx > 0) {
        var tail = text.substring(idx + f.length).replace(/^[、,\s]+/, "");
        text = text.substring(0, idx) + tail;
        changed = true;
        break;
      }
    }
  }
  return text;
}

// 文末の丁寧体コピュラ（「ます」系は対象外・理由は上部コメント参照）
var TRAILING_COPULA = ["ですわ", "ですね", "ですよ", "でした", "です"];

function stripTrailingCopula(text) {
  var changed = true;
  while (changed) {
    changed = false;
    for (var i = 0; i < TRAILING_COPULA.length; i++) {
      var c = TRAILING_COPULA[i];
      var re = new RegExp("\\s*" + c.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "$");
      var m = re.exec(text);
      if (m) {
        text = text.substring(0, m.index);
        changed = true;
        break;
      }
    }
  }
  return text;
}

function normalizeText(raw) {
  if (raw === null || raw === undefined) { raw = ""; }
  raw = String(raw);
  var original = raw.replace(/^\s+|\s+$/g, "");

  var text = raw.replace(/，/g, "、").replace(/．/g, "。");
  text = toHalfwidth(text);
  text = stripFillers(text);
  text = text.replace(/\s+/g, " ").replace(/^\s+|\s+$/g, "");
  text = text.replace(/、{2,}/g, "、");
  text = text.replace(/^[、。]+/, "").replace(/[、。]+$/, "");
  text = stripTrailingCopula(text).replace(/^\s+|\s+$/g, "");

  return text !== "" ? text : original;
}

var rawInput = $runner.getModuleResult(SOURCE_MODULE);
var cleaned = normalizeText(rawInput);
logger.info("[text_normalizer] in='" + rawInput + "' out='" + cleaned + "'");
$runner.setResult(cleaned);
