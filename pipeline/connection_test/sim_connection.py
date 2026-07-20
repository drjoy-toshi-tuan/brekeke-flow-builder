#!/usr/bin/env python3
"""連結テスト (Pattern 7) 純Python シミュレータ ＝ 第4分岐層 verifier（無架電 / M2）。

本番(またはSTTスタブ版) .bivr のフローグラフを純Python で歩き、Brekeke のチェックポイント
トレース(col7)を**架電せずに**再生する。STT スタブの注入・正規化結果の routing・CMR・jump の
call/return・context(per-call setObject / save2db 空拒否)を再現し、配線(第4分岐層)を機械検証する。

設計経緯: memory project_layer_verifier_loop_design.md (4-verifier) / 仕様: REQUIREMENTS.md
位置づけ: ai-phone-standards/02_quality_standards/LAYER_VERIFIER_REGISTRY.md

────────────────────────────────────────────────────────────────────────────
検証境界 (記録サイドカー方式 ＝ COMPUTED / RECORDED)
────────────────────────────────────────────────────────────────────────────
COMPUTED（シムが独立計算 ＝ 検証対象）:
  - STT スタブ注入 (@General$Script の [STT-STUB] / DTMF セレクタ) ＝ TBL/DEF + per-node カウンタ
  - TTS = "OK" / wait = "<n>ms" / @IVR$Reject・Disconnect = "OK"
  - saveContextModel2DB = "OK" / saveCompletionFlag2db = "OK"
  - saveContext2DB = 解決済 contextValue（literal もしくは解決可能な <%var%>）
  - ContextMatchRouter = 一致スロット番号 / Speech Retry Counter = true|false (retry_count 基準)
  - Custom Jump to Flow = subflow の call/return + 末尾 jump の二重出力規則
  - 上記すべての next/subs/jump routing 判定

RECORDED（純Python で忠実計算不能 ＝ 検証せず golden 由来値を pinned 供給）:
  - generate_by_OpenAI / Entity Classifier / incoming-classifier / acceptance_times / RAG
  - modules/ オラクル未整備の埋め込み @General$Script（Scripts-* / 3診療日_生成 等）
  - 解決不能 <%var%> を保存する saveContext2DB（実ANI・OpenAI由来の日付など）

オラクル(modules/<part>/oracle.py)を配線した部品は RECORDED→COMPUTED へ昇格する
（M0→M2 ラダー）。--oracle-promote で個別ノードを COMPUTED 扱いにできる(将来拡張点)。
各 checkpoint は監査ログで layer(1誘導/2STT/3正規化/4分岐/0配線) と COMPUTED/RECORDED を明示。

────────────────────────────────────────────────────────────────────────────
使い方
────────────────────────────────────────────────────────────────────────────
  # golden で COMPUTED を検証しつつ recorded サイドカーを生成（自己受入の核）
  python connection_test/sim_connection.py calibrate \
      --bivr <連結テスト.bivr> --cases connection_test/cases/<施設>_<flow>.json \
      --golden-dir connection_test/golden/<施設>_<flow>

  # recorded を使って架電なしでトレースを再生・golden と byte 比較
  python connection_test/sim_connection.py run \
      --bivr <連結テスト.bivr> --cases connection_test/cases/<施設>_<flow>.json \
      --recorded connection_test/recorded/<施設>_<flow>.json \
      [--case 10] [--golden-dir <...>] [--audit]
"""
import argparse, json, re, zipfile, os, sys, io
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ── モジュールタイプ定数 ─────────────────────────────────────────────
T_TTS        = "drjoy^Text To Speech$Text to speech"
T_RETRY      = "drjoy^Text To Speech$Speech Retry Counter"
T_WAIT       = "Custom$wait"
T_SCRIPT     = "@General$Script"
T_DTMF       = "drjoy^External Integration$DTMF AmiVoice STT Input"
T_STT        = "drjoy^AmiVoice$Speech to Text"
T_CTXMODEL   = "drjoy^Persistence$saveContextModel2DB"
T_CTX2DB     = "drjoy^Persistence$saveContext2DB"
T_SAVE2DB    = "drjoy^Persistence$save2db"
T_FLAG2DB    = "drjoy^Persistence$saveCompletionFlag2db"
T_CMR        = "drjoy^Context Logic$ContextMatchRouter"
T_JUMP       = "drjoy^Custom Module$Custom Jump to Flow"
T_OPENAI     = "drjoy^External Integration$generate_by_OpenAI"
T_ENTITY     = "drjoy^External Integration$Entity Classifier"
T_INCOMING   = "drjoy^Incoming$incoming-classifier"
T_ACCEPT     = "drjoy^External Integration$acceptance_times"
T_RAG        = "drjoy^External Integration$RAG"
T_REJECT     = "@IVR$Reject"
T_DISCONNECT = "@IVR$Disconnect"

# RECORDED 扱いのモジュールタイプ（純Python で忠実計算不能）
RECORDED_TYPES = {T_OPENAI, T_ENTITY, T_INCOMING, T_ACCEPT, T_RAG}

# checkpoint 値の layer 分類（監査用）。0=配線/インフラ
def layer_of(mtype, is_stub):
    if mtype in (T_DTMF, T_STT) or is_stub:        return 2   # STT
    if mtype == T_TTS:                              return 1   # 誘導TTS
    if mtype in (T_SCRIPT, T_OPENAI, T_ENTITY, T_INCOMING, T_ACCEPT, T_RAG):
        return 3                                               # 正規化/AI
    if mtype in (T_CMR, T_JUMP, T_RETRY):           return 4   # 分岐
    return 0                                                   # save/wait/reject 等 配線

LANE = {3: "A", 4: "B", 1: "E", 2: "E", 0: "E"}  # 層→差し戻しレーン(test-feedback-loop.md)


def short(name):
    return name.split("$")[-1] if name else name


class Terminate(Exception):
    """@IVR$Reject / Disconnect でコール終了。"""


class SimError(Exception):
    pass


class Sim:
    def __init__(self, flows_by_full, recorded_for_case, calibrate_tokens=None):
        self.flows = flows_by_full                       # {fullname: data}
        self.by_short = {}
        for full, d in flows_by_full.items():
            self.by_short.setdefault(short(full), d)
        self.ctx = {}                                    # setObject / saved contexts
        self.stub_counter = {}                           # nkey -> int
        self.retry_counter = {}                          # retry node fullkey -> int
        self.trace = []                                  # [(key, value)]
        self.audit = []                                  # [(key, value, layer, status)]
        # RECORDED 供給: {key: [values...]} を FIFO 消費（ループ反復対応）
        self.recorded = {k: list(v) for k, v in (recorded_for_case or {}).items()}
        self.recorded_seed = {}                          # calibrate 時に収集
        # calibrate モード: golden トークン列を順に消費して COMPUTED を突合
        self.cal = calibrate_tokens                      # [(key, value)] or None
        self.cal_ptr = 0
        self.mismatch = []                               # [(idx, key, computed, golden)]
        self.checked = 0

    # ── golden 突合（calibrate）/ recorded 供給（run）共通の checkpoint 発行 ──
    def emit(self, key, value, layer, status):
        self.trace.append((key, value))
        self.audit.append((key, value, layer, status))
        if self.cal is not None:
            # calibrate: golden の次トークンと突合（COMPUTED）or 収集（RECORDED）
            if self.cal_ptr >= len(self.cal):
                raise SimError(f"golden 枯渇: 余剰 checkpoint {key}:{value}")
            gk, gv = self.cal[self.cal_ptr]
            self.cal_ptr += 1
            if gk != key:
                raise SimError(
                    f"配線ズレ @#{self.cal_ptr}: シム='{key}' / golden='{gk}' "
                    f"(値 シム='{value}' golden='{gv}')")
            if status == "RECORDED":
                self.recorded_seed.setdefault(key, []).append(gv)
            else:
                self.checked += 1
                if value != gv:
                    self.mismatch.append((self.cal_ptr, key, value, gv))

    def recorded_value(self, key):
        """RECORDED 値を供給。run=サイドカーから FIFO / calibrate=golden 突合側で収集。"""
        if self.cal is not None:
            # calibrate 中は emit() 側が golden から値を取得するためここでは仮値
            if self.cal_ptr < len(self.cal):
                return self.cal[self.cal_ptr][1]
            return ""
        q = self.recorded.get(key)
        if not q:
            raise SimError(f"recorded サイドカーに値が無い: {key}")
        return q.pop(0)

    # ── 条件マッチ（next / subs ルーティング）─────────────────────
    @staticmethod
    def match(condition, value):
        if condition == "" :
            return False
        if condition in ("true", "false"):
            return condition == value
        if condition == "^*$":            # Brekeke 流 catch-all（無効正規表現の慣用）
            return True
        try:
            return re.fullmatch(condition, value) is not None
        except re.error:
            return condition == value

    def route(self, module, value):
        for nx in module.get("next", []):
            tgt = nx.get("nextModuleName")
            if tgt and self.match(nx.get("condition", ""), value):
                return tgt
        return None

    # ── STT スタブ実行（[STT-STUB] 注入ロジックを純Python で再現）──────
    def run_stub(self, mname, script):
        if "selected tc" in script:                      # __保存tc セレクタ保存器
            sel = str(self.ctx.get("__sel", ""))
            tcid = re.sub(r"[^0-9]", "", sel) or "1"
            self.ctx["__tc_id"] = tcid
            return tcid
        mt = re.search(r"var TBL = (.*?);\s*$", script, re.M)
        md = re.search(r"var DEF = (.*?);\s*$", script, re.M)
        mk = re.search(r'var nkey = "(.*?)"', script)
        if not (mt and md and mk):
            raise SimError(f"STT スタブの TBL/DEF/nkey を解析できません: {mname}")
        TBL = json.loads(mt.group(1)); DEF = json.loads(md.group(1)); nkey = mk.group(1)
        tc = str(self.ctx.get("__tc_id", ""))
        seq = TBL.get(tc) or DEF
        n = self.stub_counter.get(nkey, 0)
        self.stub_counter[nkey] = n + 1
        return seq[n] if n < len(seq) else seq[-1]

    @staticmethod
    def resolve_ctx_value(raw, ctx):
        """saveContext2DB / CMR の <%var%> を context から解決。未解決は None。"""
        m = re.fullmatch(r"<%\s*(.+?)\s*%>", raw or "")
        if m:
            return ctx.get(m.group(1))                   # None = 未解決 → RECORDED
        return raw                                       # literal

    # ── 1 ノードの処理 → (checkpoint値, layer, status, route用value) ──
    def dispatch(self, mname, m):
        t = m.get("type", "")
        p = m.get("params", {})
        is_stub = t == T_SCRIPT and "[STT-STUB]" in (p.get("script", ""))

        if t in (T_DTMF, T_STT) and mname.startswith("__"):   # __テストセレクタ
            v = str(self.ctx.get("__sel", ""))
            return v, 2, "COMPUTED", v
        if is_stub:
            v = self.run_stub(mname, p.get("script", ""))
            return v, 2, "COMPUTED", v
        if t == T_TTS:
            return "OK", 1, "COMPUTED", "OK"
        if t == T_WAIT:
            return f"{p.get('wait','')}ms", 0, "COMPUTED", "OK"
        if t == T_CTXMODEL:
            return "OK", 0, "COMPUTED", "OK"
        if t == T_FLAG2DB:
            return "OK", 0, "COMPUTED", "OK"
        if t == T_CTX2DB:
            resolved = self.resolve_ctx_value(p.get("contextValue", ""), self.ctx)
            if resolved is None:                          # <%var%> 未解決 → RECORDED
                v = self.recorded_value(f"{self.prefix}{short(mname)}")
            else:
                v = resolved
            cn = p.get("contextName")
            if cn and v != "":                            # save2db 空拒否は saveContext2DB も同様
                self.ctx[cn] = v
            return v, 0, ("RECORDED" if resolved is None else "COMPUTED"), v
        if t == T_SAVE2DB:                                # 通常 subs 専用。main 到達時のみ
            cv = self.resolve_ctx_value(p.get("contextValue", ""), self.ctx)
            v = "" if cv is None else cv
            return v, 0, "COMPUTED", v
        if t == T_CMR:
            key_name = self.resolve_ctx_value(p.get("module1Name", ""), self.ctx) or ""
            idx = 0
            for i in range(1, 11):
                val = p.get(f"module1Value{i}", "")
                if val and val == key_name:
                    idx = i
                    break
            return str(idx), 4, "COMPUTED", str(idx)
        if t == T_RETRY:
            rc = int(str(p.get("retry_count", "0")) or "0")
            key = f"{self.prefix}{short(mname)}#retry"
            n = self.retry_counter.get(key, 0) + 1
            self.retry_counter[key] = n
            v = "true" if n <= rc else "false"
            return v, 4, "COMPUTED", v
        if t in (T_REJECT, T_DISCONNECT):
            return "OK", 0, "COMPUTED", "OK"
        if t in RECORDED_TYPES or t == T_SCRIPT:          # OpenAI/Entity/分類器/正規化Script
            v = self.recorded_value(f"{self.prefix}{short(mname)}")
            return v, layer_of(t, False), "RECORDED", v
        raise SimError(f"未対応モジュールタイプ: {t} ({mname})")

    # ── フロー walk（call/return）────────────────────────────────
    def walk(self, flow, prefix, depth=0):
        if depth > 40:
            raise SimError("再帰が深すぎます（jump ループ疑い）")
        self.prefix = prefix
        cur = flow["start"]
        last_value = ""
        guard = 0
        while cur:
            guard += 1
            if guard > 2000:
                raise SimError("ステップ上限超過（無限ループ疑い）")
            m = flow["modules"].get(cur)
            if m is None:
                raise SimError(f"未定義モジュール参照: {prefix}{cur}")
            t = m.get("type", "")

            if t == T_JUMP:
                # subflow を call → 戻り値を取得 → 末尾なら二重出力
                tgt_full = m.get("params", {}).get("flowname", "").split("^", 1)[-1]
                sub = self.flows.get(tgt_full) or self.by_short.get(short(tgt_full))
                if sub is None:
                    raise SimError(f"jump 先フロー未解決: {tgt_full}")
                ret = self.walk(sub, f"{prefix}{short(cur)}.", depth + 1)
                self.prefix = prefix
                nxt = self.route(m, ret)
                # 規則(golden 実証): jump は空トークンを出力。次が非 jump なら戻り値も出力。
                self.emit(f"{prefix}{short(cur)}", "", 4, "COMPUTED")
                if nxt is not None and flow["modules"].get(nxt, {}).get("type") == T_JUMP:
                    pass                                  # 連鎖中の中間 jump = 空のみ
                else:
                    self.emit(f"{prefix}{short(cur)}", ret, 4, "COMPUTED")
                last_value = ret
                cur = nxt
                if cur is None:
                    return last_value
                continue

            value, layer, status, route_v = self.dispatch(cur, m)
            self.emit(f"{prefix}{short(cur)}", value, layer, status)
            last_value = value

            if t in (T_REJECT, T_DISCONNECT):
                raise Terminate()
            nxt = self.route(m, route_v)
            if nxt is None:
                return last_value                         # next 不一致 = subflow return
            cur = nxt
        return last_value

    def run_case(self, entry_flow, dtmf):
        self.ctx = {"__sel": str(dtmf)}
        self.stub_counter = {}; self.retry_counter = {}
        self.trace = []; self.audit = []
        try:
            self.walk(entry_flow, "", 0)
        except Terminate:
            pass

    def trace_line(self):
        return "".join(f"{k}:{v};" for k, v in self.trace)


# ── bivr ローダ ───────────────────────────────────────────────────
def load_bivr(path):
    with zipfile.ZipFile(path) as z:
        flows = {}
        for n in z.namelist():
            d = json.loads(z.read(n).decode("utf-8"))
            flows[d["name"]] = d
    return flows


def find_entry(flows, entry_short):
    for full, d in flows.items():
        if short(full) == entry_short:
            return d
    # フォールバック: 該当 short を含む
    for full, d in flows.items():
        if entry_short in short(full):
            return d
    raise SimError(f"entry フロー '{entry_short}' が見つかりません")


def parse_golden(path):
    """golden ファイルの col7 トレース行を [(key, value)] に分解。"""
    text = Path(path).read_text(encoding="utf-8")
    line = None
    for ln in text.splitlines():
        if ln.strip() and not ln.startswith("#"):
            line = ln.strip()
            break
    if line is None:
        raise SimError(f"トレース行が空: {path}")
    toks = []
    for tok in line.split(";"):
        if tok == "":
            continue
        k, _, v = tok.partition(":")
        toks.append((k, v))
    return toks


def golden_files(golden_dir):
    """{case_id: path} を golden ディレクトリから収集（caseNN_*.txt）。"""
    out = {}
    for f in sorted(os.listdir(golden_dir)):
        m = re.match(r"case(\d+)_", f)
        if m and f.endswith(".txt"):
            out[m.group(1)] = os.path.join(golden_dir, f)
    return out


def load_cases(path):
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    entry = cfg.get("meta", {}).get("entry_flow")
    cases = {c["id"]: c for c in cfg["cases"]}
    return entry, cases


# ── サブコマンド ───────────────────────────────────────────────────
def cmd_calibrate(args):
    flows = load_bivr(args.bivr)
    entry_short, cases = load_cases(args.cases)
    entry = find_entry(flows, entry_short)
    gfiles = golden_files(args.golden_dir)
    sidecar = {}
    total_checked = total_mismatch = 0
    rc = 0
    for cid, gpath in gfiles.items():
        if cid not in cases:
            print(f"[skip] case{cid}: cases に未定義"); continue
        toks = parse_golden(gpath)
        sim = Sim(flows, recorded_for_case={}, calibrate_tokens=toks)
        try:
            sim.run_case(entry, cases[cid]["dtmf"])
        except SimError as e:
            print(f"[FAIL] case{cid}: {e}"); rc = 1; continue
        leftover = len(toks) - sim.cal_ptr
        sidecar[cid] = sim.recorded_seed
        rec_n = sum(len(v) for v in sim.recorded_seed.values())
        status = "PASS" if (not sim.mismatch and leftover == 0) else "FAIL"
        if status == "FAIL":
            rc = 1
        total_checked += sim.checked; total_mismatch += len(sim.mismatch)
        print(f"[{status}] case{cid}: COMPUTED {sim.checked-len(sim.mismatch)}/{sim.checked} 一致"
              f" / RECORDED {rec_n} 収集 / golden 余り {leftover}")
        for idx, key, cv, gv in sim.mismatch[:12]:
            print(f"        ✗ #{idx} {key}: シム='{cv}' golden='{gv}'")
        if leftover > 0:
            nk, nv = toks[sim.cal_ptr]
            print(f"        ✗ golden 未消費 先頭 #{sim.cal_ptr+1}: {nk}:{nv}")
    if args.recorded:
        Path(args.recorded).parent.mkdir(parents=True, exist_ok=True)
        Path(args.recorded).write_text(
            json.dumps(sidecar, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nrecorded サイドカー → {args.recorded}")
    print(f"\n総計 COMPUTED 一致 {total_checked-total_mismatch}/{total_checked}"
          f"（不一致 {total_mismatch}）")
    return rc


def cmd_run(args):
    flows = load_bivr(args.bivr)
    entry_short, cases = load_cases(args.cases)
    entry = find_entry(flows, entry_short)
    sidecar = json.loads(Path(args.recorded).read_text(encoding="utf-8")) if args.recorded else {}
    gfiles = golden_files(args.golden_dir) if args.golden_dir else {}
    # 対象: --case 指定 > golden のあるケース > recorded サイドカーにあるケース
    if args.case:
        targets = [args.case]
    elif gfiles:
        targets = sorted(gfiles.keys(), key=lambda x: int(x))
    else:
        targets = sorted(sidecar.keys(), key=lambda x: int(x))
    if not targets:
        print("[warn] 実行対象ケースがありません（golden も recorded も無い）"); return 0
    rc = 0
    for cid in targets:
        if cid not in cases:
            print(f"[skip] case{cid}: 未定義"); continue
        sim = Sim(flows, recorded_for_case=sidecar.get(cid, {}))
        try:
            sim.run_case(entry, cases[cid]["dtmf"])
        except SimError as e:
            print(f"[ERROR] case{cid}: {e}"); rc = 1; continue
        line = sim.trace_line()
        if cid in gfiles:
            gline = "".join(f"{k}:{v};" for k, v in parse_golden(gfiles[cid]))
            ok = (line == gline)
            print(f"[{'PASS' if ok else 'FAIL'}] case{cid}: byte {'一致' if ok else '不一致'}"
                  f" (sim {len(line)}B / golden {len(gline)}B)")
            if not ok:
                rc = 1
                # 先頭差分位置
                for i, (a, b) in enumerate(zip(line, gline)):
                    if a != b:
                        print(f"        差分@{i}: sim…'{line[max(0,i-30):i+10]}' / "
                              f"golden…'{gline[max(0,i-30):i+10]}'")
                        break
        else:
            print(f"[case{cid}] {line}")
        if args.audit:
            comp = sum(1 for *_, s in sim.audit if s == "COMPUTED")
            rec = len(sim.audit) - comp
            print(f"        監査: COMPUTED {comp} / RECORDED {rec} / 計 {len(sim.audit)}")
            by = {}
            for _, _, lyr, st in sim.audit:
                by.setdefault((lyr, st), 0)
                by[(lyr, st)] += 1
            for (lyr, st), c in sorted(by.items()):
                print(f"          layer{lyr}({LANE.get(lyr,'-')}) {st}: {c}")
    return rc


# ════════════════════════════════════════════════════════════════════
# 構造監査モード ＝ サブフローをフラット化して監査（第4分岐層 verifier・無架電・golden 不要）
#   route_walker.py の到達性テストを置換。jump 先 JSON をメインに吸収（flatten）してから、
#   到達性 / dead-end / broken_ref / 未到達(coverage) / CMR・分類器の catch-all 欠落 を検査。
#   出力は schemas/tester.py が期待する WalkResult 互換オブジェクト（generate_report 無改修）。
# ════════════════════════════════════════════════════════════════════
_ERROR_CONDS = frozenset({"^TIMEOUT$", "^ERROR$", "^NO_RESULT$"})


def is_catchall(c):
    return c in ("^.*$", "^*$", ".*", "*")


def is_terminal_type(t):
    return ("Reject" in t) or ("Disconnect" in t) or ("Call Transfer" in t)


def active_nexts(m):
    return [(n.get("condition", ""), n["nextModuleName"])
            for n in m.get("next", []) if n.get("nextModuleName")]


# ── WalkResult 互換データモデル（schemas/route_walker.py と同じ duck type）──
@dataclass
class ARoute:
    path: list = field(default_factory=list)     # list[str]（名前空間付きモジュール名）
    terminal: str = ""
    terminal_type: str = ""                      # disconnect/transfer/dead_end/broken_ref/cycle/max_depth/script_return
    classification: str = ""

    def __iter__(self):                          # generate_report は step を str() する
        return iter(self.path)


@dataclass
class AIssue:
    code: str
    severity: str
    message: str


@dataclass
class AResult:
    routes: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    total_modules: int = 0
    reached_modules: set = field(default_factory=set)
    unreached_modules: list = field(default_factory=list)

    @property
    def coverage(self):
        return 0.0 if not self.total_modules else len(self.reached_modules) / self.total_modules * 100


# ── フラット化: Custom Jump to Flow を再帰インラインし単一フローに吸収 ──
def flatten(flows, main_full):
    """{full:flow} と main の full 名から、jump を全て吸収した単一フロー dict を返す。

    - jump J(→サブフロー S, 継続 R=J.next) ごとに S を呼び出し点別プレフィックスでコピー。
    - S の next 到達 main-chain ノードのうち empty-next / catch-all 欠落(=取りこぼし値で外へ出る)に
      戻り辺 → R を合成（サブフロー fall-through=呼び出し元への return を再現）。subs は走査・複製対象外扱い。
    - Reject/Disconnect/Call Transfer は終端（戻り辺なし）。自己/祖先循環は展開せず stub 化。
    """
    by_short = {}
    for f, d in flows.items():
        by_short.setdefault(short(f), d)
    out = {}
    participating = {main_full}                       # full 名で記録（短名衝突での誤混入を防ぐ）

    def resolve_jump(m):
        raw = m.get("params", {}).get("flowname", "")
        full = raw.split("^", 1)[-1] if "^" in raw else raw
        return (flows.get(full) or by_short.get(short(full))), full

    def inline(flow, prefix, returns, stack):
        participating.add(flow["name"])
        mods = flow.get("modules", {})
        # このフローの next 到達 main-chain（subs は辿らない）
        reach = set()
        st = flow.get("start")
        dfs = [st] if st in mods else []
        while dfs:
            cur = dfs.pop()
            if cur in reach or cur not in mods:
                continue
            reach.add(cur)
            for _, t in active_nexts(mods[cur]):
                if t in mods:
                    dfs.append(t)
        for mn, m in mods.items():
            nm = prefix + mn
            t = m.get("type", "")
            if "Jump to Flow" in t:
                sub, full = resolve_jump(m)
                jouts = [prefix + t2 for _, t2 in active_nexts(m)]   # この scope の継続
                jret = jouts if jouts else returns
                if sub is None:
                    out[nm] = {"type": "__BROKEN_JUMP__", "params": {"_ref": full}, "next": [], "subs": []}
                    continue
                if short(sub["name"]) in stack:
                    out[nm] = {"type": "__CYCLIC_JUMP__", "params": {"_ref": short(sub["name"])}, "next": [], "subs": []}
                    continue
                subpfx = nm + "/"
                out[nm] = {"type": "__INLINED_JUMP__", "params": {},
                           "next": [{"condition": "^.*$", "label": "", "nextModuleName": subpfx + sub["start"]}],
                           "subs": []}
                inline(sub, subpfx, jret, stack | {short(sub["name"])})
            else:
                nx = [{"condition": n.get("condition", ""), "label": n.get("label", ""),
                       "nextModuleName": prefix + n["nextModuleName"]}
                      for n in m.get("next", []) if n.get("nextModuleName")]
                node = {"type": t, "params": m.get("params", {}), "next": nx, "subs": m.get("subs", [])}
                # 戻り配線（インラインされたサブフローのみ。returns is not None）
                if returns is not None and mn in reach and not is_terminal_type(t):
                    conds = [c for c, _ in active_nexts(m)]
                    if (not conds) or (not any(is_catchall(c) for c in conds)):
                        for r in returns:
                            node["next"].append({"condition": "^.*$", "label": "→return", "nextModuleName": r})
                out[nm] = node

    inline(flows[main_full], "", None, {short(main_full)})
    flat = {"name": short(main_full) + "__flat", "start": flows[main_full]["start"], "modules": out}
    return flat, participating


def _classify(r):
    s = " ".join(r.path)
    if r.terminal_type in ("dead_end", "broken_ref", "max_depth", "cycle"):
        return r.terminal_type
    if "時間外" in s:
        return "時間外"
    if "非通知" in s:
        return "非通知"
    if "リトライ" in s:
        return "リトライ経由"
    return "正常"


def _sample_routes(M, start, cap=60, max_depth=400):
    """表示用に代表ルートを少数サンプリング（各ルート acyclic・業務優先・retry は false 収束側）。
    検出はグラフ解析側で行うため、ここでは issue を一切出さない（route 爆発を避ける）。"""
    routes = []

    def dfs(cur, path, onpath):
        if len(routes) >= cap:
            return
        if cur not in M:
            routes.append(ARoute(path + [cur], cur, "broken_ref")); return
        if cur in onpath or len(path) >= max_depth:
            routes.append(ARoute(path + [cur], cur, "cycle")); return
        m = M[cur]; t = m.get("type", ""); np = path + [cur]
        if is_terminal_type(t):
            routes.append(ARoute(np, cur, "transfer" if "Call Transfer" in t else "disconnect")); return
        if t in ("__BROKEN_JUMP__", "__CYCLIC_JUMP__"):
            routes.append(ARoute(np, cur, "broken_ref")); return
        acts = active_nexts(m)
        if not acts:
            routes.append(ARoute(np, cur, "dead_end")); return
        if "Retry Counter" in t:                       # 代表は収束側（false）
            ft = [t2 for c, t2 in acts if c == "false"]
            dfs(ft[0] if ft else acts[0][1], np, onpath | {cur}); return
        biz = [t2 for c, t2 in acts if c not in _ERROR_CONDS]
        err = [t2 for c, t2 in acts if c in _ERROR_CONDS]
        for t2 in (biz + err):
            if len(routes) >= cap:
                break
            dfs(t2, np, onpath | {cur})

    dfs(start, [], frozenset())
    for r in routes:
        r.classification = _classify(r)
    return routes


def structural_audit(flows, main_full, max_routes=10000, max_depth=400):
    """フラット化して構造監査。WalkResult 互換の AResult を返す。
    検出はグラフ解析（到達性 + 逆到達性 trap）+ node-local catch-all。ルート全列挙はしない。"""
    res = AResult()
    flat, participating = flatten(flows, main_full)
    M = flat["modules"]
    main_short = short(main_full)

    # ── node-local: catch-all 欠落 ──
    #   AUD-1（CMR 無一致0 の受け皿なし）= participating 全フロー / CRITICAL
    #   AUD-2（分類器 Script catch-all なし）= メインフローのみ（サブフロー fall-through は設計上の return）
    for f, d in flows.items():
        if f not in participating:
            continue
        sf = short(f)
        for mn, m in d.get("modules", {}).items():
            t = m.get("type", "")
            conds = [c for c, _ in active_nexts(m)]
            if T_CMR in t:
                if not any(Sim.match(c, "0") for c in conds):
                    res.issues.append(AIssue("AUD-1", "CRITICAL",
                        f"{sf}:{mn} ContextMatchRouter に無一致(0)の受け皿が無い（silent mis-route）"))
            elif f == main_full and "@General$Script" in t and not mn.startswith("__") \
                    and "[STT-STUB]" not in (m.get("params", {}).get("script", "")):
                enum = [c for c in conds if c not in _ERROR_CONDS and not is_catchall(c)]
                anchored = [c for c in enum if c.startswith("^") and c.endswith("$")]
                if len(anchored) >= 2 and not any(is_catchall(c) for c in conds):
                    res.issues.append(AIssue("AUD-2", "WARNING",
                        f"{sf}:{mn} 分類器 Script に catch-all 無し（{len(anchored)}列挙・取りこぼし値の受け皿なし）"))

    # ── 到達性（フラット後・単一パス BFS）──
    start = flat["start"]
    reached = set()
    stack = [start] if start in M else []
    while stack:
        cur = stack.pop()
        if cur in reached or cur not in M:
            continue
        reached.add(cur)
        for _, t in active_nexts(M[cur]):
            stack.append(t)

    # ── R-2 broken_ref（到達ノードの参照先不在 / 未解決・循環 jump）──
    for nm in sorted(reached):
        t = M[nm].get("type", "")
        if t == "__BROKEN_JUMP__":
            res.issues.append(AIssue("R-2", "CRITICAL", f"jump 先未解決: {nm} → {M[nm]['params'].get('_ref')}")); continue
        if t == "__CYCLIC_JUMP__":
            res.issues.append(AIssue("R-2", "WARNING", f"循環 jump 展開不能: {nm} → {M[nm]['params'].get('_ref')}")); continue
        for c, tgt in active_nexts(M[nm]):
            if tgt not in M:
                res.issues.append(AIssue("R-2", "CRITICAL", f"参照先不在: {nm} →[{c}] {tgt}"))

    # ── R-1 dead-end / trap：到達ノードから終端へ到達できないものを逆到達性で検出 ──
    terminals = {nm for nm in reached if is_terminal_type(M[nm].get("type", ""))}
    rev = {}
    for nm in reached:
        for _, tgt in active_nexts(M[nm]):
            if tgt in reached:
                rev.setdefault(tgt, set()).add(nm)
    good = set(terminals); st = list(terminals)
    while st:
        n = st.pop()
        for p in rev.get(n, ()):
            if p not in good:
                good.add(p); st.append(p)
    stuck = [nm for nm in sorted(reached - good)
             if M[nm].get("type", "") not in ("__BROKEN_JUMP__", "__CYCLIC_JUMP__")]
    for nm in stuck[:20]:
        kind = "dead end（next 未接続）" if not active_nexts(M[nm]) else "trap（終端に到達不能なループ）"
        res.issues.append(AIssue("R-1", "CRITICAL", f"{nm}: {kind}"))
    if len(stuck) > 20:
        res.issues.append(AIssue("R-1", "CRITICAL", f"…ほか {len(stuck)-20} 件の終端到達不能ノード"))

    # ── R-3 coverage（save2db / インライン jump pass-through を除外）──
    def counts(nm):
        t = M[nm].get("type", "")
        return (T_SAVE2DB not in t) and (t != "__INLINED_JUMP__")
    total = {nm for nm in M if counts(nm)}
    res.total_modules = len(total)
    res.reached_modules = {nm for nm in reached if nm in total}
    res.unreached_modules = sorted(total - res.reached_modules)
    if res.unreached_modules:
        res.issues.append(AIssue("R-3", "WARNING",
            f"未到達モジュール {len(res.unreached_modules)}件: "
            + ", ".join(res.unreached_modules[:10])
            + ("..." if len(res.unreached_modules) > 10 else "")))

    # ── 表示用ルート（少数サンプル・issue は出さない）──
    res.routes = _sample_routes(M, start)
    return res, flat


def cmd_audit(args):
    if args.flows:
        flows, main_full = load_flows_json(args.flows, args.subflows)
    else:
        flows = load_bivr(args.bivr)
        entry_short = args.entry or (load_cases(args.cases)[0] if args.cases else None)
        main_full = None
        for full in flows:
            if entry_short and (short(full) == entry_short or entry_short in short(full)):
                main_full = full
                break
        if not main_full:
            raise SystemExit("entry フロー未特定。--entry <短名> か --cases を指定してください。")
    res, flat = structural_audit(flows, main_full, max_routes=args.max_routes)
    if args.emit_flat:
        Path(args.emit_flat).parent.mkdir(parents=True, exist_ok=True)
        Path(args.emit_flat).write_text(json.dumps(flat, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"flatten 出力 → {args.emit_flat}")
    crit = sum(1 for i in res.issues if i.severity == "CRITICAL")
    warn = sum(1 for i in res.issues if i.severity == "WARNING")
    print(f"=== 構造監査 {short(main_full)} ===")
    print(f"ルート {len(res.routes)} / カバレッジ {len(res.reached_modules)}/{res.total_modules} "
          f"({res.coverage:.1f}%) / CRITICAL {crit} / WARNING {warn}")
    for i in res.issues:
        print(f"  [{i.severity}] {i.code}: {i.message}")
    return 1 if crit else 0


def load_flows_json(main_path, subflows):
    flows = {}
    d = json.loads(Path(main_path).read_text(encoding="utf-8"))
    flows[d["name"]] = d
    main_full = d["name"]
    for p in (subflows or []):
        s = json.loads(Path(p).read_text(encoding="utf-8"))
        flows[s["name"]] = s
    return flows, main_full


def main():
    ap = argparse.ArgumentParser(description="連結テスト純Python シミュレータ（第4分岐層 verifier）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("calibrate", help="golden で COMPUTED を検証し recorded サイドカーを生成")
    c.add_argument("--bivr", required=True)
    c.add_argument("--cases", required=True)
    c.add_argument("--golden-dir", required=True)
    c.add_argument("--recorded", default="")
    c.set_defaults(func=cmd_calibrate)
    r = sub.add_parser("run", help="recorded を使って架電なしでトレース再生・golden 比較")
    r.add_argument("--bivr", required=True)
    r.add_argument("--cases", required=True)
    r.add_argument("--recorded", default="")
    r.add_argument("--golden-dir", default="")
    r.add_argument("--case", default="")
    r.add_argument("--audit", action="store_true")
    r.set_defaults(func=cmd_run)
    a = sub.add_parser("audit", help="サブフローをフラット化して構造監査（到達性/dead-end/broken_ref/catch-all・golden不要）")
    a.add_argument("--flows", default="", help="メインフロー JSON（--subflows と併用）")
    a.add_argument("--subflows", nargs="*", default=[], help="サブフロー JSON（複数可）")
    a.add_argument("--bivr", default="", help="bivr 入力（--flows の代わり）")
    a.add_argument("--entry", default="", help="bivr 入力時の entry フロー短名")
    a.add_argument("--cases", default="", help="bivr 入力時 entry を cases.json から取得")
    a.add_argument("--emit-flat", dest="emit_flat", default="", help="フラット化フローの JSON 出力先")
    a.add_argument("--max-routes", dest="max_routes", type=int, default=10000)
    a.set_defaults(func=cmd_audit)
    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
