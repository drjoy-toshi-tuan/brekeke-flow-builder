// intent_classifier_v2 — Evidence→Event→Rule 推論エンジン（決定論・LLM近似）
// 設計正本: docs/governance/intent-engine-v2-design.md
// 大原則: Rule は生テキストを読まない。 Text → Evidence → Event → Intent → Output
// パイプライン: 正規化(+filler除去) → Evidence検出(否定=evidenceの_neg化)
//   → Event合成(fixpoint) → Rule適用 → 競合解消(Specific>General) → 1テキスト出力
// 出力: setResult = ルーティング label（閉集合: intents ∪ {CLARIFY, REPEAT, NO_RESULT}）
//       setObject("intent_result_{{STEP_NAME}}") = 構造化結果（evidence/event/rule trace）
// ランタイム: Brekeke @General$Script（Nashorn / ES5 only）
// @part-id: intent_classifier_v2
// @engine-version: v2-evidence
//
// 【テンプレート（設定行）】
//   {{INPUT_MODULE}}   直前の入力（STT/DTMF）モジュール名（wiring）
//   {{CONTEXT_NAME}}   保存先 context 名（wiring）
//   {{STEP_NAME}}      ステップ名（wiring・構造化結果の保存キー）
//   {{SPEC_JSON}}      仕様 DATA（spec・hash 対象）:
//     { "question_type": "menu"|"yes_no"|"open",
//       "clarify_margin": 1,
//       "yes_label": "肯定", "no_label": "否定",
//       "numbers": {"1": "予約", ...},               // DTMF/番号発話 → label 直結
//       "synonyms": {"_YES_": [...], "_NO_": [...]}, // yes/no トークン（CLARIFY 判定用）
//       "extractors": [{"name","regex","group"}],
//       "evidences": [{"name","keywords":[],"patterns":[],"negatable":false}],
//       "events":    [{"name","all":[],"any":[]}],   // fixpoint 合成（event の入れ子可）
//       "rules":     [{"intent","all":[],"none":[]}] }
//   specificity = rule.all を base evidence まで再帰展開した集合サイズ。
//   Specific > General。異 intent が margin 未満で拮抗 → CLARIFY（推測禁止）。

var logger = (typeof $runner !== "undefined" && $runner.getLogger) ? $runner.getLogger() : null;
var INPUT_MODULE = "{{INPUT_MODULE}}";
var CONTEXT_NAME = "{{CONTEXT_NAME}}";
var STEP_NAME = "{{STEP_NAME}}";
// @spec-begin
var SPEC = {{SPEC_JSON}};
// @spec-end

// ================= 1. Normalize（oracle.py と完全一致必須） =================
var FILLERS = ["えっとー", "えっと", "えーとー", "えーと", "ええとー", "ええと", "あのー", "あの", "えー", "うーんと", "えとー", "えっ"];

function normalize(s) {
    if (s === null || s === undefined) return "";
    var n = String(s);
    n = n.replace(/[\r\n\t]/g, "");
    n = n.replace(/[０-９]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFF10 + 0x30); });
    n = n.replace(/[Ａ-Ｚａ-ｚ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0xFEE0); });
    n = n.replace(/[A-Z]/g, function (c) { return c.toLowerCase(); });
    n = n.replace(/[ァ-ヶ]/g, function (c) { return String.fromCharCode(c.charCodeAt(0) - 0x60); });
    n = n.replace(/[\s　]/g, "");
    n = n.replace(/[。、，．！？!?「」『』【】（）()・…]/g, "");
    for (var i = 0; i < FILLERS.length; i++) {
        while (n.indexOf(FILLERS[i]) >= 0) n = n.replace(FILLERS[i], "");
    }
    return n;
}

var NEG_MARKERS = ["ない", "なくて", "ません", "不要", "結構", "やめ", "なしで"];
// 依頼形「〜てもらえませんか」「〜できませんか」は否定でなく丁寧依頼。除外する。
var NEG_REQUEST_EXCLUDES = ["てもらえ", "もらえ", "てくれ", "てもらい", "ていただけ", "できます", "いただけ"];
var NEG_WINDOW = 12;
var REPEAT_MARKERS = ["もう一度", "もういちど", "聞こえ", "きこえ", "繰り返", "くりかえ", "もっかい"];

function hasNegationAfter(t, idx) {
    var win = t.substring(idx, idx + NEG_WINDOW);
    for (var i = 0; i < NEG_MARKERS.length; i++) {
        var m = NEG_MARKERS[i];
        var pos = win.indexOf(m);
        if (pos < 0) continue;
        var prefix = win.substring(0, pos);
        if (m === "ません") {
            var excluded = false;
            for (var j = 0; j < NEG_REQUEST_EXCLUDES.length; j++) {
                var ex = NEG_REQUEST_EXCLUDES[j];
                if (prefix.length >= ex.length && prefix.substring(prefix.length - ex.length) === ex) {
                    excluded = true;
                    break;
                }
            }
            if (excluded) continue;
        }
        if ((m === "ない" || m === "なくて") && prefix.length >= 2
                && prefix.substring(prefix.length - 2) === "しか") {
            continue;  // しかない = affirmative "have no choice but to"
        }
        return true;
    }
    return false;
}

// ================= 2. Detect Evidence =================
// 否定は evidence の属性: negatable な evidence が否定スコープ内 → "{name}_neg" として成立
function detectEvidence(t, reason) {
    var facts = {};
    var evidences = SPEC.evidences || [];
    var i, j;
    for (i = 0; i < evidences.length; i++) {
        var ev = evidences[i];
        var matchEnd = -1;
        var hit = null;
        var kws = ev.keywords || [];
        for (j = 0; j < kws.length; j++) {
            var kw = normalize(kws[j]);
            var pos = kw === "" ? -1 : t.indexOf(kw);
            if (pos >= 0) { matchEnd = pos + kw.length; hit = kws[j]; break; }
        }
        if (matchEnd < 0) {
            var pats = ev.patterns || [];
            for (j = 0; j < pats.length; j++) {
                var m = new RegExp(pats[j]).exec(t);
                if (m) { matchEnd = m.index + m[0].length; hit = pats[j]; break; }
            }
        }
        if (matchEnd < 0) continue;
        if (ev.negatable && hasNegationAfter(t, matchEnd)) {
            facts[ev.name + "_neg"] = true;
            reason.push("L2:evidence:" + ev.name + "_neg(" + hit + ")");
        } else {
            facts[ev.name] = true;
            reason.push("L2:evidence:" + ev.name + "(" + hit + ")");
        }
    }
    // 同義語トークン（_YES_/_NO_ 等）も evidence として facts に載せる
    var synonyms = SPEC.synonyms || {};
    for (var tok in synonyms) {
        if (!synonyms.hasOwnProperty(tok)) continue;
        var syns = synonyms[tok];
        for (j = 0; j < syns.length; j++) {
            var syn = normalize(syns[j]);
            if (syn !== "" && t.indexOf(syn) >= 0) {
                facts[tok] = true;
                reason.push("L2:token:" + syns[j] + "->" + tok);
                break;
            }
        }
    }
    return facts;
}

// ================= 3. Build Events（fixpoint） =================
function buildEvents(facts, reason) {
    var events = SPEC.events || [];
    var changed = true;
    var guard = events.length + 1;
    while (changed && guard > 0) {
        changed = false;
        guard -= 1;
        for (var i = 0; i < events.length; i++) {
            var evt = events[i];
            if (facts[evt.name]) continue;
            var ok = true;
            var all = evt.all || [];
            for (var j = 0; j < all.length; j++) {
                if (!facts[all[j]]) { ok = false; break; }
            }
            if (ok && evt.any && evt.any.length > 0) {
                var anyHit = false;
                for (j = 0; j < evt.any.length; j++) {
                    if (facts[evt.any[j]]) { anyHit = true; break; }
                }
                ok = anyHit;
            }
            if (ok) {
                facts[evt.name] = true;
                reason.push("L3:event:" + evt.name);
                changed = true;
            }
        }
    }
    return facts;
}

// ================= specificity: event を base evidence へ再帰展開 =================
function baseEvidenceSet(cond, eventsByName, seen) {
    if (seen[cond]) return {};
    seen[cond] = true;
    var out = {};
    var evt = eventsByName[cond];
    if (!evt) {
        out[cond] = true;
        return out;
    }
    var deps = (evt.all || []).concat(evt.any || []);
    for (var i = 0; i < deps.length; i++) {
        var sub = baseEvidenceSet(deps[i], eventsByName, seen);
        for (var k in sub) { if (sub.hasOwnProperty(k)) out[k] = true; }
    }
    return out;
}

function ruleSpecificity(rule, eventsByName) {
    var acc = {};
    var all = rule.all || [];
    for (var i = 0; i < all.length; i++) {
        var sub = baseEvidenceSet(all[i], eventsByName, {});
        for (var k in sub) { if (sub.hasOwnProperty(k)) acc[k] = true; }
    }
    var n = 0;
    for (var k2 in acc) { if (acc.hasOwnProperty(k2)) n += 1; }
    return n;
}

// ================= 4. Apply Rules =================
function applyRules(facts, reason) {
    var rules = SPEC.rules || [];
    var eventsByName = {};
    var evts = SPEC.events || [];
    for (var e = 0; e < evts.length; e++) eventsByName[evts[e].name] = evts[e];
    var fired = [];
    for (var i = 0; i < rules.length; i++) {
        var r = rules[i];
        var ok = true;
        var all = r.all || [];
        for (var j = 0; j < all.length; j++) {
            if (!facts[all[j]]) { ok = false; break; }
        }
        if (ok) {
            var none = r.none || [];
            for (j = 0; j < none.length; j++) {
                if (facts[none[j]]) { ok = false; break; }
            }
        }
        if (ok) {
            var spec = ruleSpecificity(r, eventsByName);
            fired.push({ intent: r.intent, spec: spec, order: i, all: all });
            reason.push("L4:rule:" + r.intent + "[" + all.join("+") + "](spec=" + spec + ")");
        }
    }
    return fired;
}

// ================= 5. Resolve Conflict（Specific > General） =================
function resolveConflict(fired, result) {
    // intent ごとに最高 specificity のみ残す
    var byIntent = {};
    var i;
    for (i = 0; i < fired.length; i++) {
        var f = fired[i];
        var cur = byIntent[f.intent];
        if (!cur || f.spec > cur.spec || (f.spec === cur.spec && f.order < cur.order)) {
            byIntent[f.intent] = f;
        }
    }
    var list = [];
    for (var k in byIntent) { if (byIntent.hasOwnProperty(k)) list.push(byIntent[k]); }
    list.sort(function (a, b) {
        if (b.spec !== a.spec) return b.spec - a.spec;
        return a.order - b.order;
    });
    var top1 = list[0];
    var top2 = list.length > 1 ? list[1] : null;
    var margin = (SPEC.clarify_margin === null || SPEC.clarify_margin === undefined)
        ? 1 : SPEC.clarify_margin;
    if (top1.intent === "CLARIFY") {
        result.intent = "CLARIFY";
        result.need_clarification = true;
        result.reason.push("L5:CLARIFY rule(spec=" + top1.spec + ") → 聞き返し");
        return result;
    }
    if (top2 !== null && (top1.spec - top2.spec) < margin) {
        result.intent = "CLARIFY";
        result.need_clarification = true;
        result.reason.push("L5:拮抗 " + top1.intent + "(spec=" + top1.spec + ") vs "
            + top2.intent + "(spec=" + top2.spec + ") → 聞き返し");
        return result;
    }
    result.intent = top1.intent;
    result.negation = false;
    for (i = 0; i < top1.all.length; i++) {
        if (top1.all[i].length > 4 && top1.all[i].indexOf("_neg", top1.all[i].length - 4) >= 0) {
            result.negation = true;
            break;
        }
    }
    result.confidence = top2 === null
        ? 1 : Math.round(top1.spec / (top1.spec + top2.spec) * 100) / 100;
    result.reason.push("L5:採用 " + top1.intent + "(spec=" + top1.spec + ")");
    return result;
}

// ================= 分類本体（oracle.py と完全一致必須） =================
function classify(rawInput) {
    var raw = (rawInput === null || rawInput === undefined) ? "" : String(rawInput);
    var result = { intent: "NO_RESULT", confidence: 0, entities: {}, variables: {},
                   negation: false, reason: [], evidences: [], events: [],
                   need_clarification: false };
    var t = normalize(raw);
    if (t === "") return result;

    var i;

    // ---- L0: DTMF / 番号発話 → label 直結（numbers map） ----
    // 全文一致（^…$ アンカー）限定の許容サフィックス。「1番の」「1の」「1番ので」等の
    // 助詞「の」継続は全文一致のみで許可する（部分一致に入れると「2の予定で…」等を誤選択するため）。
    var NUM_SUFFIX = "(で(おねがい|お願い|よろしく)?(します)?|を(おねがい|お願い)?(します)?"
                   + "|の(ほう)?(で(おねがい|お願い)?(します)?|を(おねがい|お願い)?(します)?)?"
                   + "|です|だ(よ|ね)?|よ|かな(あ)?|ね)?";
    var numbers = SPEC.numbers || {};
    if (/^[0-9]+$/.test(t) && numbers[t]) {
        result.intent = numbers[t];
        result.confidence = 1;
        result.reason.push("L0:DTMF=" + t);
        return result;
    }
    for (var num in numbers) {
        if (!numbers.hasOwnProperty(num)) continue;
        // 部分一致の N番/Nばん は「安全な継続」限定（2番目/2番線/一番早い 等の誤爆防止・oracle と同一）
        if (new RegExp("(^|[^0-9])" + num + "(ばん|番)(?=$|で|です|だ|ね|よ|かな|を|ください|おねがい|お願い)").test(t)
                || new RegExp("^" + num + "(ばん|番)?" + NUM_SUFFIX + "$").test(t)) {
            result.intent = numbers[num];
            result.confidence = 1;
            result.reason.push("L0:number:" + num);
            return result;
        }
    }
    var KANJI_NUM = [["一","1"],["二","2"],["三","3"],["四","4"],["五","5"],
                     ["六","6"],["七","7"],["八","8"],["九","9"],
                     ["いち","1"],["に","2"],["さん","3"],["よん","4"],["ご","5"],
                     ["ろく","6"],["なな","7"],["はち","8"],["きゅう","9"],["く","9"]];
    for (var ki = 0; ki < KANJI_NUM.length; ki++) {
        var kanji = KANJI_NUM[ki][0], digit = KANJI_NUM[ki][1];
        if (!numbers[digit]) continue;
        if (new RegExp("(^|[^一二三四五六七八九])" + kanji + "(ばん|番)(?=$|で|です|だ|ね|よ|かな|を|ください|おねがい|お願い)").test(t)
                || new RegExp("^" + kanji + "(ばん|番)?" + NUM_SUFFIX + "$").test(t)) {
            result.intent = numbers[digit];
            result.confidence = 1;
            result.reason.push("L0:kanji_num:" + kanji);
            return result;
        }
    }

    // ---- L1.5: エンティティ抽出 ----
    var extractors = SPEC.extractors || [];
    for (i = 0; i < extractors.length; i++) {
        var ex = extractors[i];
        var m = new RegExp(ex.regex).exec(t);
        if (m) {
            var g = (ex.group === null || ex.group === undefined) ? 1 : ex.group;
            result.entities[ex.name] = m[g];
            result.reason.push("L1.5:" + ex.name + "=" + m[g]);
        }
    }

    // ---- 2. Evidence / 3. Events / 4. Rules ----
    var facts = detectEvidence(t, result.reason);
    facts = buildEvents(facts, result.reason);
    var fk;
    for (fk in facts) { if (facts.hasOwnProperty(fk)) result.evidences.push(fk); }
    var fired = applyRules(facts, result.reason);

    if (fired.length === 0) {
        // REPEAT（トークン解決より先。「もう一度お願いします」の お願いします 誤爆防止）
        if (t.length <= 15) {
            for (i = 0; i < REPEAT_MARKERS.length; i++) {
                if (t.indexOf(REPEAT_MARKERS[i]) >= 0) {
                    result.intent = "REPEAT";
                    result.reason.push("L5:repeat_marker:" + REPEAT_MARKERS[i]);
                    return result;
                }
            }
        }
        // 文脈（question_type）: rule 不発時の yes/no トークン解決
        var qt = SPEC.question_type || "menu";
        if (qt === "yes_no") {
            if (facts["_YES_"] && facts["_NO_"]) {
                result.intent = "CLARIFY";
                result.need_clarification = true;
                result.reason.push("L5:yes_no両トークン検出");
                return result;
            }
            if (facts["_YES_"]) {
                result.intent = SPEC.yes_label || "YES";
                result.confidence = 1;
                result.reason.push("L5:yes_no文脈でYES");
                return result;
            }
            if (facts["_NO_"]) {
                result.intent = SPEC.no_label || "NO";
                result.confidence = 1;
                result.reason.push("L5:yes_no文脈でNO");
                return result;
            }
        }
        if (qt === "menu" && (facts["_YES_"] || facts["_NO_"])) {
            result.intent = "CLARIFY";
            result.need_clarification = true;
            result.reason.push("L5:menu文脈でyes/no単独 → 選択肢を特定できない");
            return result;
        }
        result.reason.push("L6:rule不発 → NO_RESULT（推測禁止）");
        return result;
    }

    // yes_no 文脈で両トークン共起は rule より CLARIFY を優先（「はい、いいえ」対策）
    if ((SPEC.question_type || "menu") === "yes_no" && facts["_YES_"] && facts["_NO_"]) {
        result.intent = "CLARIFY";
        result.need_clarification = true;
        result.reason.push("L5:yes_no両トークン検出");
        return result;
    }

    return resolveConflict(fired, result);
}

// ================= 6. Output（Brekeke ランタイムのみ） =================
if (typeof $runner !== "undefined") {
    var rawModule = $runner.getModuleResult(INPUT_MODULE);
    var inputText = "";
    if (rawModule && typeof rawModule === "object" && rawModule.text) {
        inputText = String(rawModule.text);
    } else if (rawModule !== null && rawModule !== undefined) {
        inputText = String(rawModule);
    }
    var res = classify(inputText);
    try {
        $runner.setObject("intent_result_" + STEP_NAME, JSON.stringify(res));
        if (CONTEXT_NAME !== "" && res.intent !== "NO_RESULT"
                && res.intent !== "CLARIFY" && res.intent !== "REPEAT") {
            $runner.setObject(CONTEXT_NAME, res.intent);
        }
    } catch (e) {
        if (logger) logger.error("[intent_v2] setObject: " + e);
    }
    $runner.setResult(res.intent);
}
