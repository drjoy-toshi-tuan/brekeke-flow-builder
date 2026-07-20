---
name: kamei-normalize
description: Brekeke IVR用の「診療科名正規化スクリプト（kamei_normalize.js）」を生成するスキル。AmiVoice STT出力から正式な診療科名（canonical）へ決定論的に分類するES5.1/Nashornスクリプトを作成する。LLM不使用・辞書最長一致方式。「診療科スクリプト」「科名正規化」「DEPARTMENTS追加」「kamei_normalize」「診療科リストからスクリプト生成」「科名追加してほしい」など、Brekeke診療科分類スクリプトに関する依頼があれば必ずこのスキルを使うこと。DEPARTMENTS・WAKARANAI・TRAILERSの中身変更依頼にも使用する。
---

# 診療科名正規化スクリプト生成（kamei_normalize.js）

Brekeke IVR用の診療科分類スクリプトを生成・更新する。
**ロジック部分（`nrm()`・`decide()`・入力取得・DB保存・`setResult`）は絶対に変更しない。**

## 変更可否ルール

| 箇所 | 変更可否 |
|------|---------|
| `WAKARANAI` の中身 | ✅ 変更可 |
| `DEPARTMENTS` の中身 | ✅ 変更可 |
| `TRAILERS` の中身 | ✅ 変更可 |
| `nrm()` 関数 | ❌ 変更禁止 |
| `decide()` 関数 | ❌ 変更禁止 |
| 入力取得・ログ・`setResult` | ❌ 変更禁止 |
| DB保存ブロック | ❌ 変更禁止 |

## 言語・環境制約

- JavaScript **ES5.1（Nashorn）** のみ
- `var` のみ（`let`/`const`/アロー関数 **禁止**）
- `String.normalize` **禁止**（Nashorn非対応）
- ループ変数の重複 **禁止**
- 外部API呼び出し **禁止**

## DEPARTMENTS定義ルール

```javascript
["正式科名（canonical）", ["キー1", "キー2", "ひらがな読み1", ...]],
```

1. **canonical名は正式名称をそのまま**（中黒「・」付きもそのまま）
2. **キーリストに含めるもの:**
   - 正式名称（canonicalそのまま）
   - 中黒なし表記（例: `リウマチ膠原病感染内科`）
   - 主要な漢字エイリアス（例: `膠原病`、`リウマチ`）
   - ひらがな読み（複数可）
3. **包含関係は長い名前を先に定義:**
   ```
   小児心臓血管外科 → 小児外科 → 小児科
   消化器内科 → 消化器外科
   ```

## 出力値・フロー分岐

| 出力 | 意味 | DB保存 | フロー |
|------|------|--------|--------|
| 正式科名（canonical） | 認識成功 | ✅ | 次ステップへ |
| `登録なし` | わからない系発話 | ✅ | スキップ・再質問しない |
| `NO_RESULT` | 空/数字のみ/不一致 | ❌ | リトライ |

## Branch正規表現セット（必ずセットで出力）

| 用途 | 正規表現 |
|------|---------|
| ① NO_RESULT判定 | `^NO_RESULT$` |
| ② 登録なし判定 | `^登録なし$` |
| ③ 有効科名判定 | `^(?!NO_RESULT$|登録なし$).+$` |

## 実行手順

1. ユーザーから診療科リストを受け取る（なければ確認する）
2. 包含関係を確認し、長い名前を先に並べる
3. 各科のキーリスト（canonical・中黒なし・読み・エイリアス）を生成
4. 下記テンプレートの `WAKARANAI`・`DEPARTMENTS`・`TRAILERS` のみ置き換えて出力
5. `nrm()`・`decide()`・入力取得・DB保存・`setResult` は**一切変更しない**

## 出力テンプレート（このフォーマットを厳守）

```javascript
// [SCRIPT-DEPT] 診療科 決定論分類。公式{N}科辞書・最長一致。
// 入力: $runner.getModuleResult("入力_診療科") / 出力: 科名 | "登録なし"(わからない) | "NO_RESULT"
// Nashorn(ES5.1)想定: String.normalize 不使用。診療科入力は漢字/ひらがな科名・読みのため、
//   全角数字→半角・空白/記号除去・末尾定型語除去 の限定正規化で十分（NFKCの実効サブセット）。

// =====================================================================
// ✅ 変更可: WAKARANAI・DEPARTMENTS・TRAILERS の中身のみ
// ❌ 変更禁止: nrm()・decide()・入力取得・ログ・setResult・DB保存
// =====================================================================

var WAKARANAI = [
  // 分かる系否定
  "わからない","わかりません","わかりませんでした",
  "わかんない","わかんないです","わかんないですね",
  "わからないです","わからないですね",
  "わからなかった","わかりかねます",
  // 知る系否定
  "知らない","知りません","知らん","知らないです","知りませんでした",
  // その他不明系
  "不明","不明です","決まっていない","決まってない","きまっていない","未定","忘れ","わすれ"
];

var DEPARTMENTS = [
  // フォーマット: ["正式科名（canonical）", ["キー1","キー2","読み1","読み2", ...]],
  // 重要: 包含関係がある科（例: 小児科⊂小児外科⊂小児心臓血管外科）は長い名前を先に定義すること
  ["消化器内科", ["消化器内科","しょうかきないか","しょうかき"]],
  ["内科",       ["内科","ないか"]],
  // ... 全科をここに定義
];

var TRAILERS = [
  "でお願いします","をお願いします","おねがいします","になります",
  "です","でお願い","が希望","を希望","希望","の方","のほう","科目","かな","かも"
];

// =====================================================================
// ❌ 以下は変更禁止
// =====================================================================

function nrm(raw) {
  var s = (raw == null) ? "" : String(raw);
  s = s.replace(/[０-９]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
  var strip = [" ","　","「","」","、","。","・","．","，","\u201c","\u201d","\t","\r","\n"];
  for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
  s = s.replace(/^\s+|\s+$/g, "");
  var changed = true;
  while (changed) {
    changed = false;
    for (var t = 0; t < TRAILERS.length; t++) {
      var tt = TRAILERS[t].split("・").join("");
      if (tt && s.length > tt.length && s.lastIndexOf(tt) === s.length - tt.length) {
        s = s.substring(0, s.length - tt.length); changed = true;
      }
    }
  }
  return s;
}

function decide(s) {
  if (s === "") return "NO_RESULT";
  for (var i = 0; i < WAKARANAI.length; i++) {
    if (s.indexOf(WAKARANAI[i].split("・").join("")) >= 0) return "登録なし";
  }
  if (/^[0-9]+$/.test(s)) return "NO_RESULT";
  var keys = [];
  for (var d = 0; d < DEPARTMENTS.length; d++) {
    var canon = DEPARTMENTS[d][0]; var ks = DEPARTMENTS[d][1];
    for (var k = 0; k < ks.length; k++) { keys.push([ks[k], canon, keys.length]); }
  }
  keys.sort(function(a, b) { return (b[0].length - a[0].length) || (a[2] - b[2]); });
  for (var j = 0; j < keys.length; j++) { if (s.indexOf(keys[j][0]) >= 0) return keys[j][1]; }
  return "NO_RESULT";
}

var r = $runner.getModuleResult("入力_診療科");
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }
var norm = nrm(raw);
var out = decide(norm);
$runner.getLogger().info("[SCRIPT-DEPT] raw=" + raw + " norm=" + norm + " out=" + out);

if (out !== "NO_RESULT") {
  var contextField = {
    contextName: "clinicalDepartment",
    displayType: "DEPARTMENT",
    value: out
  };
  try {
    $ivr.exec("save2db", "save", JSON.stringify({ contextField: contextField }));
  } catch(e) { /* silent */ }
}

$runner.setObject("科名_正規化結果", out);
$runner.setResult(out);
```

## 出力前チェック（必須）

- [ ] `DEPARTMENTS` の包含関係が正しい順序（長い名前が先）か
- [ ] `nrm()`・`decide()`・入力取得・DB保存・`setResult` を一切変更していないか
- [ ] ES5.1ルール違反（`let`/`const`/アロー関数/`String.normalize`）がないか
- [ ] Branch正規表現3種をセットで出力しているか
- [ ] コメント1行目の `{N}` に実際の科数を入れているか
