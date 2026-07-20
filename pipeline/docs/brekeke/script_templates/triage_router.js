// Script Template: triage_router — 受診相談 決定論トリアージ（LLM問診の置換・OpenAI不使用）
// JTAS ＋ 総務省消防庁「電話相談」プロトコル準拠の Top-Down Exclusion カスケードを純関数で実装。
// LLM 不使用・同一入力→同一出力。3 ゴール（救急/看護師/通常）を setResult し CMR で END を選ぶ。
// parity: modules/triage_router/oracle.py（同一辞書・同一手順・同順・oracle 39/39）。仕様 = 同 REQUIREMENTS.md /
//   output/scenarios/商談デモ_フリー発話受付/受診相談_トリアージ判定仕様_20260703.md。
//
// 答えの取り方（浜口さん確定 2026-07-03・実データ整合）:
//   - A ブロックの閉じた ABCD 4 問は VFB では置かず（患者86%が自由発話・純yes/no回答者0）、
//     生命兆候は CPA 語検知 ＋ 共通致死語 の自由発話走査で拾う（冒頭の緊急度確認1問はフロー側で温存）。
//   - 主訴分類・B（カテゴリ別 Red Flag）・C（修飾因子）は全て自由発話へのキーワード走査（over-triage bias）。
//
// プレースホルダー:
//   {{COMPLAINT_MODULE}} = 主訴（通話冒頭の用件フリー聴取の STT。カテゴリ分類の起点）。例: 入力_用件フリー聴取
//   {{DETAIL_MODULE}}    = 症状詳細（受診相談で開いて聞いた自由発話）。例: 入力_症状詳細聴取
//   （complaint＋detail の連結を全走査テキストとする＝oracle の all_free）
// Nashorn(ES5.1)想定: arrow / let / const / includes / テンプレート文字列 / 後読み(?<!) 不使用。

var Normalizer = Java.type("java.text.Normalizer");
var NForm      = Java.type("java.text.Normalizer$Form");

var GOAL1 = "GOAL1_救急";
var GOAL2 = "GOAL2_看護師";
var GOAL3 = "GOAL3_通常";

// NFKC 正規化 ＋ 空白畳み（oracle normalize と同手順）。全半角/カナ/互換ゆれ吸収。
function normalize(str) {
  if (!str) return "";
  var s;
  try { s = "" + Normalizer.normalize("" + str, NForm.NFKC); }
  catch (e) { s = "" + str; }
  return s.replace(/\s+/g, "");
}

// ---- A-0: CPA（心肺停止）語。全テキストへ検知 → 即 GOAL1 ------------------------
var CPA = /((呼吸|息).{0,5}(ない|なし|ませ|てな)|呼吸なし|脈.{0,4}(ない|なし|ませ)|心臓.{0,3}止ま|心停止|冷たくな(って|り|)|水没|沈んで|おぼれ|溺れ)/;

// ---- 主訴カテゴリ分類（自由発話への包含・優先順で先勝ち）------------------------
var CATEGORIES = ["頭痛めまい", "胸痛", "外傷出血", "腹痛", "発熱"];  // この順で先勝ち。全外れ=その他
var CATEGORY_RE = {
  "頭痛めまい": /(頭.{0,10}痛|頭痛|あたま.{0,10}痛|めまい|眩暈|くらくら|ふらつき|立ちくらみ)/,
  "胸痛":       /(胸.{0,5}痛|胸痛|胸.{0,5}苦し|動悸)/,
  "外傷出血":   /(けが|怪我|切った|切って|ぶつけ|打った|打撲|出血|血が出|骨折|転ん|転倒|やけど|火傷|捻挫|刺され|咬まれ|噛まれ)/,
  "腹痛":       /(腹.{0,5}痛|お腹.{0,5}痛|腹痛|胃.{0,5}痛|下腹|みぞおち)/,
  "発熱":       /(発熱|高熱|微熱|寒気|悪寒|熱っぽ|熱.{0,3}(あ|で|出|高|つ)|(38|39|40|41|42)度)/
};

// ---- B: カテゴリ別 Red Flag（自由発話走査・発火で GOAL1）------------------------
// [カテゴリ, [[flag_id, pattern], ...]]。data-driven（語彙拡張は表を足すだけ）。
var RED_FLAGS = {
  "頭痛めまい": [
    ["突発激痛", /(突然|急に|いきなり|バット|殴られ)/],
    ["最悪の痛み", /(今まで.{0,4}(ない|無い)|人生で|経験.{0,4}(ない|無い)|最悪|かつてない)/],
    ["増悪", /(だんだん.{0,3}(強|ひど)|どんどん.{0,3}痛|強くなっ|悪化)/],
    ["神経脱落", /(しびれ|痺れ|力が?入らな|麻痺|動かせな)/],
    ["意識言語", /(ろれつ|呂律|変なこと|焦点.{0,3}合わ|意識.{0,4}(もうろう|ぼんやり|おかし))/],
    ["嘔吐", /(吐いた|嘔吐|吐き気がひど|強い吐き気)/],
    ["視覚異常", /(見えな|かすむ|二重に見え|視野が?欠け)/]
  ],
  "胸痛": [
    ["突発持続", /(突然.{0,4}(始ま|痛)|急に.{0,3}痛|いきなり)/],
    ["放散痛", /((首|あご|顎|肩|肩甲骨|背中|腕).{0,6}(痛|広が|放散|しびれ|だる))|放散/],
    ["安静時痛", /(安静|じっと|寝て.{0,3}痛|動かなくても|何もしなくても)/],
    ["冷汗", /(冷や?汗|脂汗|汗が?止まらな)/],
    ["薬無効", /(ニトロ|舌下|(薬|くすり).{0,4}(効か(な|ず)|効きませ|効いてな|治ま(らな|りませ|らず)))/],
    ["ピル", /(ピル|避妊薬|経口避妊)/],
    ["DVT", /((足|脚|ふくらはぎ|足首).{0,4}(腫れ|むくみ))|長.{0,3}座|エコノミー/]
  ],
  "腹痛": [
    ["激痛", /(激し|激痛|今まで.{0,4}(ない|無い)|のたうち|耐えられ)/],
    ["胸背部併発", /((胸|背中).{0,4}痛)/],
    ["ヘルニア嵌頓", /(こぶ|しこり|(足の付け根|股|そけい|鼠径).{0,4}(出|腫れ|膨ら))/],
    ["頭痛併発", /(頭が?痛|頭痛)/]
  ],
  "発熱": [
    ["高熱薬無効", /((39|40|４０|３９|４１|41).{0,2}度|(解熱|薬|くすり).{0,4}効かな|高熱)/],
    ["意識障害", /(意識.{0,4}(もうろう|ぼんやり|おかし)|もうろう)/],
    ["神経症状", /((手足|腕|足).{0,4}(動か|感覚)|しびれ|麻痺)/],
    ["けいれん", /(けいれん|痙攣|ひきつけ)/],
    ["基礎疾患", /(心臓|肝臓|糖尿|透析|持病|治療中|免疫)/],
    ["脱水", /(尿.{0,4}(出な|少な|減)|(唇|皮膚).{0,3}乾|水分.{0,3}(取れ|摂れ)な|脱水|ぐったり)/]
  ],
  "外傷出血": [
    ["気道腫脹", /((喉|のど|舌).{0,3}腫れ|息.{0,3}(しづら|苦し))/],
    ["髄液漏", /((透明|さらさら).{0,4}(鼻水|耳)|耳だれ|髄液)/],
    ["複視", /(二重に見え|複視|見え方.{0,3}(おかし|変))/],
    ["阻血肢", /((指先|手足|足先|患部).{0,5}(冷た|青ざめ|白く|紫))/],
    ["開放骨折", /(骨.{0,3}(見え|出て)|開放骨折)/],
    ["止血不能", /((圧迫|押さえ).{0,6}(止ま|出血)|血.{0,4}止ま(らな|りませ|ませ|らず)|大量.{0,3}出血)/]
  ]
};

// ---- 共通致死語（カテゴリ非依存・常時走査。A系サインを取りこぼさない）------------
var COMMON_LETHAL = [
  ["意識障害", /(意識が?(ない|もうろう|ぼんやり|遠のく)|反応が?(ない|薄)|呼びかけ.{0,4}反応)/],
  ["呼吸困難", /(息が?(できな|苦し)|呼吸.{0,3}(困難|苦し)|息が?荒)/],
  ["けいれん", /(けいれん|痙攣|ひきつけ)/],
  ["麻痺", /(ろれつ|呂律|半身.{0,3}(動か|しびれ)|片側.{0,3}(動か|しびれ)|顔.{0,3}(ゆがみ|下が))/],
  ["大量出血", /(大量.{0,3}出血|血が?(止まらな|どくどく|噴)|血だらけ)/],
  ["冷汗", /(冷や?汗|脂汗)/],
  ["突発激痛", /(突然|急に|いきなり).{0,10}(激痛|激し|ひどい?痛|殴られ|割れる|バット|耐えられ)/],
  ["最悪の痛み", /((今まで|人生|かつて).{0,6}(ない|無い).{0,6}痛|最悪.{0,4}痛|経験.{0,4}(ない|無い).{0,6}痛)/]
];

// ---- C: 修飾因子（自由発話走査・発火で GOAL2）------------------------------------
// 小児: oracle は後読み (?<![0-9])[0-5](歳|才) だが Nashorn(ES5.1) は後読み非対応のため
//   (^|[^0-9])[0-5](歳|才) で「直前が数字でない」を表現（"15歳"→ 5歳部分は直前"1"でブロック）。
var MODIFIERS = [
  ["歩行不能", /(歩けな|歩けませ|立てな|立ち上がれ|動けな)/],
  ["高齢", /((6[5-9]|[7-9][0-9]|1[01][0-9]).{0,1}(歳|才)|高齢|お年寄)/],
  ["小児", /((^|[^0-9])[0-5](歳|才)|乳児|赤ちゃん|生後|新生児)/],
  ["妊娠", /(妊娠|妊婦|おめでた)/],
  ["抗凝固薬", /(血.{0,3}(さらさら|サラサラ)|ワー?ファリン|ワルファリン|抗凝固|血液.{0,3}(薬|くすり)|DOAC|バイアスピリン|イグザレルト|エリキュース)/],
  ["止血困難", /((30分|三十分|ずっと).{0,5}(出血|血)|コップ.{0,2}(1|一)杯|止まらな.{0,3}(出血|血))/],
  ["局所処置", /((あご|顎).{0,4}(外れ|動かな|開かな)|(腫れ|痛み).{0,4}広が|蜂窩織炎)/],
  ["歯科ハイリスク", /(歯.{0,6}(心臓|糖尿)|歯.{0,4}(抜け|折れ).{0,6}(血.{0,3}薬|さらさら|抗凝固))/]
];

// ---- カスケード関数 --------------------------------------------------------------
function classifyComplaint(complaint) {
  var t = normalize(complaint);
  var i;
  for (i = 0; i < CATEGORIES.length; i++) {
    if (CATEGORY_RE[CATEGORIES[i]].test(t)) return CATEGORIES[i];
  }
  return "その他";
}

function scanRedFlags(category, allText) {
  var t = normalize(allText);
  var fired = [];
  var list = RED_FLAGS[category] || [];
  var i;
  for (i = 0; i < list.length; i++) {
    if (list[i][1].test(t)) fired.push(category + "/" + list[i][0]);
  }
  for (i = 0; i < COMMON_LETHAL.length; i++) {
    if (COMMON_LETHAL[i][1].test(t)) {
      var tag = "共通/" + COMMON_LETHAL[i][0];
      if (fired.indexOf(tag) < 0) fired.push(tag);
    }
  }
  return fired;
}

function scanModifiers(allText) {
  var t = normalize(allText);
  var fired = [];
  var i;
  for (i = 0; i < MODIFIERS.length; i++) {
    if (MODIFIERS[i][1].test(t)) fired.push(MODIFIERS[i][0]);
  }
  return fired;
}

// ---- 入力読込 --------------------------------------------------------------------
var complaint = "";
try { complaint = String($runner.getModuleResult("{{COMPLAINT_MODULE}}") || ""); } catch (e) { complaint = ""; }
var detail = "";
try { detail = String($runner.getModuleResult("{{DETAIL_MODULE}}") || ""); } catch (e2) { detail = ""; }

var allFree = complaint + " " + detail;  // oracle: all_free = " ".join([complaint] + free_texts)

// ---- Top-Down Exclusion（短絡・ランクダウン禁止）--------------------------------
var goal, block, reason, category = "";

if (CPA.test(normalize(allFree))) {
  goal = GOAL1; block = "A0"; reason = "A-0:CPA語検知";
} else {
  // A-1..A-4（閉じた ABCD）は VFB では置かない＝abcd 全 no 相当でスキップ。
  category = classifyComplaint(complaint);
  var red = scanRedFlags(category, allFree);
  if (red.length > 0) {
    goal = GOAL1; block = "B"; reason = "B:" + red.join(",");
  } else {
    var mod = scanModifiers(allFree);
    if (mod.length > 0) {
      goal = GOAL2; block = "C"; reason = "C:" + mod.join(",");
    } else {
      goal = GOAL3; block = "D"; reason = "D:全否定（危険サインなし）";
    }
  }
}

// ---- 監査用に $runner へ載せる ＋ Dr.JOY 記録（save2db）--------------------------
// 副作用は try/catch で保護（save2db が office_id 未設定等で失敗しても setResult=goal は必ず返す）。
try {
  $runner.setObject("triageGoal", goal);
  $runner.setObject("triageReason", reason);
  $runner.setObject("triageCategory", category);
  $ivr.exec("save2db", "save", JSON.stringify({
    contextField: { contextName: "triageGoal", displayType: "TEXT", value: goal }
  }));
  $ivr.exec("save2db", "save", JSON.stringify({
    contextField: { contextName: "triageCategory", displayType: "TEXT", value: category }
  }));
} catch (eSave) {
  $runner.getLogger().info("[TRIAGE] save2db skip: " + eSave);
}

$runner.getLogger().info("[TRIAGE] goal=" + goal + " block=" + block + " category=" + category +
                         " reason=" + reason + " complaint='" + complaint + "' detail='" + detail + "'");
$runner.setResult(goal);
