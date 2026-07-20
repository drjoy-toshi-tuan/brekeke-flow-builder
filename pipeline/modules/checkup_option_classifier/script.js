// [SCRIPT-OPT] 受診オプション検査 抽出・正規化（オプション選択 generate_by_OpenAI 置換）
// 入力: STT 結果テキスト（自由発話）
// 出力: 正規化検査名（複数は「、」区切り） | "不明" | "無い" | "復唱途中切断"
// Nashorn(ES5.1)想定。NFKC 正規化 + 音声誤認補正 + 否定語除外 + 複数マッチ対応。
// parity: checkup_option_classifier/oracle.py（同一辞書・同一手順）。
// #274 で ITEMS を universe 化（施設非依存・33種）＋ facility_offered サブセットを追加（engine v2→v3）。
// @part-id: checkup_option_classifier
// @engine-version: v3
//
// 【判定優先順位】
//   1. マッチあり（否定除外後・facility_offered サブセット後）→ 正規化名を「、」結合
//   2. 不明系発話かつマッチ無し → "不明"
//   3. 無い系発話かつマッチ無し → "無い"
//   4. どれにも該当しない → "復唱途中切断"
//
// @template SOURCE_MODULE: 入力モジュール名
var SOURCE_MODULE = "{{SOURCE_MODULE}}";
// @template CONTEXT_NAME: 保存先 context 名（例: detail）（wiring）
var CONTEXT_NAME = "{{CONTEXT_NAME}}";
// @template CONTEXT_DISPLAY_TYPE: context の displayType（例: TEXT）（wiring）
var CONTEXT_DISPLAY_TYPE = "{{CONTEXT_DISPLAY_TYPE}}";
// @template FACILITY_OFFERED: 施設が受けられる canonical の配列（wiring・null=universe 絞り込みなし）
var FACILITY_OFFERED = {{FACILITY_OFFERED}};

// @spec-begin

// 音声誤認補正テーブル（nrm() 後に適用。ロック/ドッグ/トック → ドック）
var SOUND_FOLDS = [
    ["人間ロック","人間ドック"],["人間ドッグ","人間ドック"],["人間トック","人間ドック"],
    ["脳ロック","脳ドック"],["脳ドッグ","脳ドック"],
    ["心臓ロック","心臓ドック"],
    ["大腸ロック","大腸ドック"],["大腸ドッグ","大腸ドック"],
    ["肺ロック","肺ドック"],["肺ドッグ","肺ドック"],
    ["眼科ロック","眼科ドック"],["眼科ドッグ","眼科ドック"],
    ["レディースロック","レディースドック"],["レディースドッグ","レディースドック"],
    ["2日ロック","2日ドック"],["二日ロック","二日ドック"],["二日ドッグ","二日ドック"],
    ["日帰りロック","日帰りドック"]
];

// 不明検知パターン（正規化後テキストに対して test）
var FUMEI_PATTERN = /わからない|わかりません|わかんない|不明|当日決め|当日きめ|まだ決め|まだきめ|決まっていない|決まってない|きまっていない|決めていない|きめていない|相談したい|しょうだんしたい/;

// 無い検知パターン
var NAI_PATTERN = /追加しない|追加なし|ついかしない|ついかなし|不要|ふよう|いらない|いりません|特にない|とくにない|ありません|結構です|けっこうです|大丈夫です|だいじょうぶです|希望なし|希望はなし/;

// 否定マーカー（アイテムキーワード直後に付く語。buildNegated で使用）
var NEGATE_MARKERS = [
    "はいらない","はいりません","はいらん",
    "をキャンセル","はキャンセル","のキャンセル",
    "はやめ","をやめ",
    "は不要","は受けない","は受けません"
];

// universe オプション（reference/checkup/universe_options.tsv・正規化済みキーワード。定義順＝優先順位・先勝ち）
// [canonical, [post-normalized-keywords, ...]]
var ITEMS = [
    ["CEA", ["cea", "cea", "がん胎児性抗原"]],
    ["CA19-9", ["ca199", "ca199", "ca199", "膵臓マーカー"]],
    ["AFP", ["afp", "afp", "アルファフェトプロテイン", "肝臓マーカー"]],
    ["PSA（前立腺）", ["psa前立腺", "psa", "ぴーえすえー", "前立腺", "前立腺がん", "男性の血液検査"]],
    ["CA125（卵巣）", ["ca125卵巣", "ca125", "卵巣マーカー"]],
    ["腫瘍マーカーセット", ["腫瘍マーカーセット", "腫瘍マーカー", "血液のがん検査", "腫瘍マーカーセット", "腫瘍の検査"]],
    ["マンモグラフィ", ["マンモグラフィ", "マンモ", "マンモグラフィ", "乳房x線", "3dマンモ", "乳房レントゲン", "乳がん検診", "乳がん", "乳癌検診"]],
    ["乳腺超音波検査", ["乳腺超音波検査", "乳腺超音波", "乳腺エコー", "乳房超音波", "乳房エコー", "胸のエコー", "乳腺"]],
    ["経膣超音波検査", ["経膣超音波検査", "経膣エコー", "経腟超音波", "経膣超音波", "内診エコー"]],
    ["子宮頸がん検査", ["子宮頸がん検査", "子宮頸部細胞診", "子宮頸がん", "子宮頚がん", "頸がん検査", "子宮けいがん", "子宮がん検診", "子宮がん", "hpv"]],
    ["子宮体がん検査", ["子宮体がん検査", "子宮体がん", "子宮内膜", "体がん", "子宮たいがん"]],
    ["肝炎ウイルス検査", ["肝炎ウイルス検査", "肝炎ウイルス", "b型肝炎", "c型肝炎", "hbs", "hcv", "肝炎検査"]],
    ["性感染症・梅毒検査", ["性感染症梅毒検査", "性感染症", "梅毒", "sti", "tpha", "rpr"]],
    ["アレルギー検査", ["アレルギー検査", "アレルギー", "view39", "ビュー39", "特異的ige", "花粉"]],
    ["甲状腺検査", ["甲状腺検査", "甲状腺", "甲状腺ホルモン", "tsh", "ft3", "ft4", "サイログロブリン"]],
    ["エクオール検査", ["エクオール検査", "エクオール", "大豆イソフラボン"]],
    ["脳MRI・MRA", ["脳mrimra", "頭部mri", "mra", "脳mri", "脳血管撮影"]],
    ["下腹部MRI（骨盤腔）", ["下腹部mri骨盤腔", "下腹部mri", "骨盤mri", "骨盤腔mri"]],
    ["内臓脂肪CT", ["内臓脂肪ct", "内臓脂肪", "内臓脂肪ct", "メタボct"]],
    ["胸部CT（肺）", ["胸部ct肺", "胸部ct", "肺ct", "低線量ct", "肺の検査"]],
    ["冠動脈CT（心臓）", ["冠動脈ct心臓", "冠動脈ct", "心臓ct", "心臓の検査"]],
    ["骨密度検査（DEXA）", ["骨密度検査dexa", "骨密度", "dexa", "デキサ", "骨粗鬆症", "骨の検査"]],
    ["眼底・眼圧検査", ["眼底眼圧検査", "眼底", "眼圧", "緑内障", "眼底検査", "眼圧検査"]],
    ["胃内視鏡検査", ["胃内視鏡検査", "胃カメラ", "胃内視鏡", "上部消化管内視鏡"]],
    ["大腸内視鏡検査", ["大腸内視鏡検査", "大腸カメラ", "大腸内視鏡", "下部消化管内視鏡", "下のカメラ", "大腸ドック"]],
    ["睡眠時無呼吸検査", ["睡眠時無呼吸検査", "睡眠時無呼吸", "sas", "いびき", "無呼吸", "アプノモニター"]],
    ["動脈硬化検査", ["動脈硬化検査", "動脈硬化", "血管年齢", "血管の硬さ", "abi", "cavi"]],
    ["BNP検査", ["bnp検査", "bnp", "びーえぬぴー", "心不全の検査"]],
    ["肺機能検査", ["肺機能検査", "肺機能", "呼吸機能", "スパイロ", "息を吐く検査"]],
    ["ヘリコバクターピロリ菌検査", ["ヘリコバクターピロリ菌検査", "ピロリ", "ヘリコバクター", "ピロリ菌", "胃の血液検査"]],
    ["喀痰検査", ["喀痰検査", "喀痰", "かくたん", "痰の検査"]],
    ["マイクロアレイ血液検査", ["マイクロアレイ血液検査", "マイクロアレイ", "がんの血液検査", "遺伝子レベルの検査"]],
    ["転倒予防診断", ["転倒予防診断", "転倒予防", "身体バランス", "筋力チェック"]]
];

// 包含関係: 複合コースが一致した場合、構成単体アイテムを結果から除外する
// [compound_canonical, [excluded_canonicals]]
var SUBSUMES = [
    ["腫瘍マーカーセット", ["CEA", "CA19-9", "AFP", "PSA（前立腺）", "CA125（卵巣）"]]
];

// @spec-end

function nrm(raw) {
    var s = (raw == null) ? "" : String(raw);
    s = "" + Java.type("java.text.Normalizer").normalize(s, Java.type("java.text.Normalizer$Form").NFKC);
    s = s.replace(/[０-９]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    s = s.replace(/[Ａ-Ｚａ-ｚ]/g, function(c){ return String.fromCharCode(c.charCodeAt(0) - 0xFEE0).toLowerCase(); });
    s = s.replace(/[A-Z]/g, function(c){ return c.toLowerCase(); });
    var strip = ["、","。","，","．",",",".","-","・","･",":","；","：","!","！","?","？","…","‥","〜","～",
                 "「","」","『","』","(",")","（","）","[","]","【","】","<",">","＜","＞",
                 "\"","'","“","”","‘","’","｢","｣","　"," ","\t","\r","\n"];
    for (var i = 0; i < strip.length; i++) { s = s.split(strip[i]).join(""); }
    for (var f = 0; f < SOUND_FOLDS.length; f++) { s = s.split(SOUND_FOLDS[f][0]).join(SOUND_FOLDS[f][1]); }
    return s;
}

// 否定されたアイテムの canonical 集合を返す
function buildNegated(s) {
    var neg = {};
    for (var i = 0; i < ITEMS.length; i++) {
        var canon = ITEMS[i][0];
        var kws = ITEMS[i][1];
        outer:
        for (var k = 0; k < kws.length; k++) {
            for (var m = 0; m < NEGATE_MARKERS.length; m++) {
                if (s.indexOf(kws[k] + NEGATE_MARKERS[m]) >= 0) {
                    neg[canon] = true;
                    break outer;
                }
            }
        }
    }
    return neg;
}

// キーワード一致アイテムを返す（否定・重複除外、SUBSUMES 適用済み、facility_offered サブセット済み）
function matchItems(s, negated) {
    var matched = [];
    var seen = {};
    for (var i = 0; i < ITEMS.length; i++) {
        var canon = ITEMS[i][0];
        if (negated[canon] || seen[canon]) { continue; }
        var kws = ITEMS[i][1];
        for (var k = 0; k < kws.length; k++) {
            if (s.indexOf(kws[k]) >= 0) {
                matched.push(canon);
                seen[canon] = true;
                break;
            }
        }
    }
    // SUBSUMES 適用: 複合コースに包含される単体アイテムを除外
    var excludedBySub = {};
    for (var m = 0; m < matched.length; m++) {
        for (var si = 0; si < SUBSUMES.length; si++) {
            if (matched[m] === SUBSUMES[si][0]) {
                var excluded = SUBSUMES[si][1];
                for (var e = 0; e < excluded.length; e++) { excludedBySub[excluded[e]] = true; }
            }
        }
    }
    var afterSub = [];
    for (var m2 = 0; m2 < matched.length; m2++) {
        if (!excludedBySub[matched[m2]]) { afterSub.push(matched[m2]); }
    }
    // facility_offered サブセット（配線・null=universe 絞り込みなし）
    if (FACILITY_OFFERED != null && typeof FACILITY_OFFERED.length === "number") {
        var offered = {};
        for (var fi = 0; fi < FACILITY_OFFERED.length; fi++) { offered[FACILITY_OFFERED[fi]] = true; }
        var subset = [];
        for (var fj = 0; fj < afterSub.length; fj++) { if (offered[afterSub[fj]]) { subset.push(afterSub[fj]); } }
        return subset;
    }
    return afterSub;
}

var logger = $runner.getLogger();

// === コンテキスト保存関数群（VFB 共通流儀: save2db + setObject + checkpoint。n_choice と同一）===
function _saveCheckpoint(value) {
    try { if (!$ivr.connected()) return; $ivr.exec("save2db", "save", JSON.stringify({ contextField: { contextName: "checkpoint", displayType: "TEXT", value: value } })); } catch (e) { logger.error("[saveContext2DB] Checkpoint: " + e); }
}
function _setObj(k, v) { try { $ivr.setObject(k, v); } catch (e) { logger.error("[saveContext2DB] setObj: " + e); } }
function saveContext(val, name, type) {
    var rid = $ivr.getRID(); var mod = $runner.getCurrentModuleName();
    _saveCheckpoint(mod + "_IN"); _setObj("checkpoint." + rid, mod + "_IN");
    if (name && val) { var req = JSON.stringify({ contextField: { contextName: name, displayType: type || "TEXT", value: val } }); logger.info("[saveContext2DB] " + req); try { $ivr.exec("save2db", "save", req); $runner.setObject(name, val); } catch (e) { logger.error("[saveContext2DB] " + e); } }
    _saveCheckpoint(mod + "_OUT"); _setObj("checkpoint." + rid, mod + "_OUT"); _setObj("saveContext." + rid, true);
}
// === END ===

var r = $runner.getModuleResult(SOURCE_MODULE);
var raw = "";
if (r != null) { if (typeof r === "object" && r.text != null) { raw = String(r.text); } else { raw = String(r); } }

var norm = nrm(raw);
logger.info("[checkup_option_classifier] raw=" + raw + " norm=" + norm);

var out;
if (norm === "") {
    out = "復唱途中切断";
} else {
    var hasFumei = FUMEI_PATTERN.test(norm);
    var hasNai   = NAI_PATTERN.test(norm);
    var negated  = buildNegated(norm);
    var matched  = matchItems(norm, negated);

    if (matched.length > 0) {
        out = matched.join("、");
    } else if (hasFumei) {
        out = "不明";
    } else if (hasNai) {
        out = "無い";
    } else {
        out = "復唱途中切断";
    }
}

logger.info("[checkup_option_classifier] out=" + out);
$runner.setResult(out);

// コンテキスト保存（スクリプト内で完結。@General$Script は subs の save2db を実行しないため必須）
saveContext(out, CONTEXT_NAME, CONTEXT_DISPLAY_TYPE);
