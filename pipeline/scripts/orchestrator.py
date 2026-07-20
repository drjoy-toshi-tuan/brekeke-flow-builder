#!/usr/bin/env python3
"""
orchestrator.py -- VoiceBot Flow Builder パイプラインオーケストレーター

Pythonスクリプトによるパイプライン自動制御。
QAリトライループ、prompter→reviewer直列実行、tester+build並列実行、Git自動ブランチ、Human-in-the-Loop承認を実装。

Usage:
    python3 scripts/orchestrator.py --pattern 1 --spec docs/migration/gen2_xxx.md
    python3 scripts/orchestrator.py --pattern 2 --spec output/scenarios/xxx_yyy/設計書_xxx_yyy.yaml --base docs/reference/xxx.bivr
    python3 scripts/orchestrator.py --pattern 3 --spec docs/migration/gen2_xxx.md
    python3 scripts/orchestrator.py --pattern 4 --spec docs/migration/gen1_xxx.md
    python3 scripts/orchestrator.py --resume
    python3 scripts/orchestrator.py --dry-run --pattern 1 --spec docs/migration/gen2_xxx.md
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time

# Windows環境でUTF-8出力を強制（cp932でのUnicodeEncodeErrorを防止）
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
# 子プロセスにもUTF-8 I/Oを強制（scaffold_generator等が日本語パスをstdoutに出力する際のcp932→UTF-8化け防止）
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

PROJECT_DIR = Path(__file__).resolve().parent.parent

# claude CLI のフルパスを起動時に解決（Windows + Git Bash 混在環境での解決失敗を防ぐ）
# 1) 環境変数 CLAUDE_CMD で明示指定可
# 2) shutil.which で見つかればそれを採用（ただし実在チェック）。`.cmd` `.exe` 拡張子も試行
# 3) 候補パス（.local/bin/claude.exe、AppData 配下等）を実在チェックで探索
# 4) 見つからなければ "claude" を返してエラーを自然に報告
def _resolve_claude_cmd() -> str:
    env_cmd = os.environ.get("CLAUDE_CMD")
    if env_cmd and Path(env_cmd).exists():
        return env_cmd
    for name in ("claude", "claude.exe", "claude.cmd"):
        found = shutil.which(name)
        if found and Path(found).exists():
            return found
    home = Path.home()
    for cand in (
        home / ".local" / "bin" / "claude.exe",
        home / ".local" / "bin" / "claude.cmd",
        home / "AppData" / "Roaming" / "Claude" / "claude-code" / "claude.exe",
        home / ".claude" / "local" / "claude.exe",
    ):
        if cand.exists():
            return str(cand)
    # バージョンディレクトリ配下を探索（例: AppData/Roaming/Claude/claude-code/2.x.x/claude.exe）
    claude_code_dir = home / "AppData" / "Roaming" / "Claude" / "claude-code"
    if claude_code_dir.exists():
        for ver_dir in sorted(claude_code_dir.iterdir(), reverse=True):
            for exe_name in ("claude.exe", "claude.cmd", "claude"):
                cand = ver_dir / exe_name
                if cand.exists():
                    return str(cand)
    return "claude"

CLAUDE_CMD: str = _resolve_claude_cmd()

AGENT_TIMEOUT = 3600         # フォールバック（個別設定がない場合）
VALIDATOR_TIMEOUT = 120      # 2分
SCRIPT_TIMEOUT = 60          # 1分

# ステップ別タイムアウト（パイプライン全体60分設計）
STEP_TIMEOUTS = {
    "director":  3600,   # 60分（Opusで最重量。大規模gen2ソース対応）
    "qa":        1200,   # 20分
    "generator": 4800,   # 80分（5用件ルート+サブフロー多数の大規模フロー対応）
    "prompter":  1800,   # 30分（Opusで重い）
    "reviewer":  1200,   # 20分（レポート生成後の後処理でタイムアウトしていた）
    "fixer":     1200,   # 20分（外科的修正のみ。重くなっても1200で十分）
    "tester":     300,   # 5分
    "dirlite":    600,   # 10分（差分分析のみ。軽量タスク）
}
MAX_QA_RETRIES = 3
MAX_VALIDATOR_RETRIES = 3

# ---------------------------------------------------------------------------
# ステップ別トークン累積器
# ---------------------------------------------------------------------------
# invoke_agent が呼ばれるたびに自動でこのバケツに加算される。
# メインループがステップ開始前にリセットし、終了後に step_timings へ書き込む。
_step_token_acc: dict = {
    "input": 0, "output": 0,
    "cache_read": 0, "cache_creation": 0,
    "cost_usd": 0.0,
}

def _reset_token_acc() -> None:
    global _step_token_acc
    _step_token_acc = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "cost_usd": 0.0}

def _add_tokens(usage: dict) -> None:
    """invoke_agent の usage 辞書を累積器に加算する"""
    if not usage:
        return
    _step_token_acc["input"]            += usage.get("input", 0)
    _step_token_acc["output"]           += usage.get("output", 0)
    _step_token_acc["cache_read"]       += usage.get("cache_read", 0)
    _step_token_acc["cache_creation"]   += usage.get("cache_creation", 0)
    _step_token_acc["cost_usd"]         += usage.get("cost_usd", 0.0)

def _get_token_acc() -> dict:
    """現在の累積値のコピーを返す（空なら None を返す）"""
    total = _step_token_acc["input"] + _step_token_acc["output"]
    if total == 0:
        return {}
    return dict(_step_token_acc)

# ANSI色
class C:
    RESET  = "\033[0m"
    RED    = "\033[31m"
    GREEN  = "\033[32m"
    YELLOW = "\033[33m"
    BLUE   = "\033[34m"
    CYAN   = "\033[36m"
    BOLD   = "\033[1m"

# ---------------------------------------------------------------------------
# ログ
# ---------------------------------------------------------------------------

def log_info(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.BLUE}[{ts}] INFO{C.RESET}  {msg}")

def log_ok(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.GREEN}[{ts}] OK{C.RESET}    {msg}")

def log_warn(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.YELLOW}[{ts}] WARN{C.RESET}  {msg}")

def log_error(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{C.RED}[{ts}] ERROR{C.RESET} {msg}")

def log_step(step: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n{C.BOLD}{C.CYAN}[{ts}] === {step} ==={C.RESET}")
    print(f"  {msg}")

# ---------------------------------------------------------------------------
# パイプライン状態
# ---------------------------------------------------------------------------

@dataclass
class PipelineState:
    pattern: int = 1
    facility: str = ""
    flow: str = ""
    assignee: str = "hamaguchi"
    spec_path: str = ""
    base_path: str = ""
    environment: str = "demo"
    current_step: str = "init"
    qa_retry_count: int = 0
    validator_retry_count: int = 0
    outputs: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    started_at: str = ""
    ended_at: str = ""
    step_timings: dict = field(default_factory=dict)
    branch_name: str = ""
    skip_qa: bool = False
    skip_tester: bool = False
    unattended: bool = False
    clean_legacy: bool = False  # Pattern 2: True で base の legacy Critical も含めて修正、False で dirlite touched ブロックのみ
    allow_director_llm: bool = False  # True で従来の director LLM 起草を許可。既定は決定論入口（/sparring-intake: drawio/CSV → YAML）のみ
    dirlite_manifest: dict = field(default_factory=dict)  # Pattern 2: dirlite が出力する manifest v2 {version, affects, sections}

    def save(self):
        # 成果物は output/scenarios/{施設}_{flow}/ 配下に集約する（master 保護方針）
        path = PROJECT_DIR / "output" / "scenarios" / f"{self.facility}_{self.flow}" / f"pipeline_state_{self.facility}_{self.flow}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)
        return path

    @classmethod
    def load(cls, path: str) -> "PipelineState":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)

    @classmethod
    def find_latest(cls) -> Optional["PipelineState"]:
        """output/scenarios/*/ 配下の最新 pipeline_state を検索（旧 output/ 直下も後方互換で見る）"""
        output_dir = PROJECT_DIR / "output"
        # 新: output/scenarios/{施設}/pipeline_state_*.json
        states = list(output_dir.glob("scenarios/*/pipeline_state_*.json"))
        # 旧: output/pipeline_state_*.json（後方互換、移行期のみ）
        states += list(output_dir.glob("pipeline_state_*.json"))
        states.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if states:
            return cls.load(str(states[0]))
        return None

# ---------------------------------------------------------------------------
# 施設名・フロー名の推定
# ---------------------------------------------------------------------------

def extract_names(spec_path: str) -> tuple:
    """設計書パスから施設名・フロー名を推定"""
    name = Path(spec_path).stem  # 設計書_海老名総合病院_外来予約 or gen2_イーストメディカル_健診
    # gen2_ / gen1_ プレフィックスを除去（移管元ファイルをそのまま渡した場合）
    for prefix in ("gen2_", "gen1_", "設計書_"):
        name = name.replace(prefix, "", 1) if name.startswith(prefix) else name.replace(prefix, "")
    parts = name.split("_", 1)
    facility = parts[0] if parts else "unknown"
    flow = parts[1] if len(parts) > 1 else "main"
    return facility, flow

# ---------------------------------------------------------------------------
# コマンド実行ヘルパー
# ---------------------------------------------------------------------------

def run_cmd(cmd: list, timeout: int = SCRIPT_TIMEOUT, cwd: str = None,
            stdin_input: str = None) -> tuple:
    """コマンドを実行し (exit_code, stdout, stderr) を返す。

    FileNotFoundError は Claude CLI auto-update 等の transient 失敗で起きるため、
    最大 3 回まで指数バックオフ (1s, 2s) でリトライする。

    stdin_input を渡すと subprocess.run の input= に流す。Windows の
    CreateProcess は lpCommandLine の長さに 32,767 文字の上限があり、
    超えると WinError 206 を返す（Python は FileNotFoundError として翻訳）。
    長大なプロンプト (claude -p の prompt 引数) は argv ではなく stdin で
    渡すことでこの上限を回避する。
    """
    last_err = ""
    for attempt in range(3):
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or str(PROJECT_DIR),
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", f"TIMEOUT after {timeout}s: {' '.join(cmd)}"
        except FileNotFoundError:
            last_err = f"Command not found: {cmd[0]}"
            if attempt < 2:
                time.sleep(2 ** attempt)  # 1s, 2s で再試行
                continue
            return -2, "", last_err
    return -2, "", last_err

_TOKEN_EXHAUSTION_PATTERNS = [
    "context window", "token limit", "too many tokens",
    "context length", "maximum context", "rate limit",
    "overloaded", "capacity",
]

def detect_token_exhaustion(stderr: str, stdout: str) -> bool:
    """トークン枯渇・レート制限を示すパターンを検出"""
    combined = (stderr + stdout).lower()
    return any(p in combined for p in _TOKEN_EXHAUSTION_PATTERNS)

def _encode_path_claude(path_str: str) -> str:
    """ディレクトリパスを Claude Code のプロジェクト名エンコード規則に変換する。

    規則（実測ベース）:
      ':' → '--'  (例: C: → C--)
      '/' '\\' '.' '_' ' ' → '-'
      ASCII英数字・'-' → そのまま
      非ASCII（日本語等） → '-' 1文字
    """
    result = ""
    for c in path_str:
        if c == ':':
            result += '--'
        elif c in '/\\._: ':
            result += '-'
        elif c == '-' or (c.isascii() and c.isalnum()):
            result += c
        else:
            result += '-'
    return result


def _get_claude_project_dir() -> Optional[Path]:
    """PROJECT_DIR に対応する ~/.claude/projects/ のサブディレクトリを返す。"""
    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        return None

    encoded = _encode_path_claude(str(PROJECT_DIR))
    target = claude_projects / encoded
    if target.exists():
        return target

    # 完全一致しない場合: 先頭20文字で部分一致検索
    prefix = encoded[:20]
    matches = [d for d in claude_projects.iterdir()
               if d.is_dir() and d.name.startswith(prefix)]
    if not matches:
        return None
    # 最も名前長が近いものを選ぶ
    return min(matches, key=lambda d: abs(len(d.name) - len(encoded)))


def _parse_iso_timestamp(ts_str: str) -> float:
    """JSONL エントリの ISO 8601 timestamp → Unix timestamp。パース失敗時は 0.0 を返す。"""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0.0


def _read_usage_from_recent_jsonl(start_ts: float) -> dict:
    """エージェント実行後、直近作成された JSONL からトークン使用量を集計して返す。

    start_ts (unix timestamp) 以降に更新された JSONL ファイルを探し、
    **start_ts 以降に記録された** assistant メッセージの usage だけを合算する。
    JSONL エントリの timestamp フィールドでフィルタすることで、過去セッション分の
    トークンを誤って合算するバグを防ぐ。

    並列パイプラインで別ワークツリーの JSONL と混合しないよう、
    PROJECT_DIR のプロジェクトディレクトリのみを検索する。
    """
    proj_dir = _get_claude_project_dir()
    search_dirs = [proj_dir] if proj_dir else []

    # プロジェクトディレクトリが特定できなければ全ディレクトリを対象に（フォールバック）
    if not search_dirs:
        claude_projects = Path.home() / ".claude" / "projects"
        if claude_projects.exists():
            search_dirs = [d for d in claude_projects.iterdir() if d.is_dir()]

    best_file = None
    best_mtime = start_ts  # start_ts より後に更新されたものだけ

    for d in search_dirs:
        for jsonl_file in d.glob("*.jsonl"):
            try:
                mtime = jsonl_file.stat().st_mtime
                if mtime > best_mtime:
                    best_mtime = mtime
                    best_file = jsonl_file
            except OSError:
                pass

    if not best_file:
        return {}

    total = {"input": 0, "output": 0, "cache_read": 0, "cache_creation": 0, "cost_usd": 0.0}
    seen_ids: set = set()
    try:
        with open(best_file, encoding="utf-8", errors="replace") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("type") != "assistant":
                        continue
                    # start_ts より前に記録されたエントリは過去セッション分なのでスキップ
                    ts_str = obj.get("timestamp", "")
                    if ts_str:
                        entry_ts = _parse_iso_timestamp(ts_str)
                        if entry_ts < start_ts:
                            continue
                    msg = obj.get("message", {})
                    msg_id = msg.get("id", "")
                    if msg_id:
                        if msg_id in seen_ids:
                            continue
                        seen_ids.add(msg_id)
                    usage = msg.get("usage", {})
                    total["input"]         += usage.get("input_tokens", 0)
                    total["output"]        += usage.get("output_tokens", 0)
                    total["cache_read"]    += usage.get("cache_read_input_tokens", 0)
                    total["cache_creation"]+= usage.get("cache_creation_input_tokens", 0)
                except (json.JSONDecodeError, AttributeError, TypeError):
                    pass
    except Exception:
        pass

    # 何も取得できなければ空を返す
    has_data = any(isinstance(v, int) and v > 0 for v in total.values())
    return total if has_data else {}


def invoke_agent(agent_name: str, prompt: str, model_override: str = "") -> tuple:
    """Claude Code エージェントを呼び出す。

    通常モード（ファイル書き込み等のツール実行を維持）で起動し、
    実行後に JSONL ファイルからトークン使用量を取得してステップ別累積器に加算する。

    NOTE: --output-format json は Write ツールを抑制するため使用しない。
          トークン集計は ~/.claude/projects/{project}/*.jsonl から行う。

    Args:
        model_override: 指定時に --model フラグでエージェント定義の model を上書きする。
                        例: "claude-sonnet-5"

    Returns:
        (exit_code, agent_output_text, stderr, usage_dict)
        usage_dict: {input, output, cache_read, cache_creation, cost_usd}
    """
    timeout = STEP_TIMEOUTS.get(agent_name, AGENT_TIMEOUT)
    log_info(f"@{agent_name} を起動中... (タイムアウト: {timeout//60}分)")

    start_ts = time.time()
    # Windows の引数長制限 (32,767 chars) を回避するため、prompt は stdin で渡す。
    # 4/28 SKILL_CONTRACT 追加以降、prompter のプロンプトが ~40K に達して
    # WinError 206 → FileNotFoundError として失敗する事例が発生していた。
    cmd = [CLAUDE_CMD, "-p", "--agent", agent_name]
    if model_override:
        cmd += ["--model", model_override]
    code, raw_stdout, stderr = run_cmd(cmd, timeout=timeout, stdin_input=prompt)

    agent_output = raw_stdout

    # JSONL からトークン使用量を取得
    usage: dict = _read_usage_from_recent_jsonl(start_ts)
    if usage:
        _add_tokens(usage)

    if code == 0:
        if usage:
            effective_in = usage["input"] + usage["cache_read"]
            log_ok(
                f"@{agent_name} 完了  "
                f"[入力:{effective_in:,} / 出力:{usage['output']:,} / "
                f"キャッシュ:{usage['cache_read']:,} / ${usage['cost_usd']:.4f}]"
            )
        else:
            log_ok(f"@{agent_name} 完了")
    else:
        if detect_token_exhaustion(stderr, agent_output):
            log_error(f"@{agent_name} トークン枯渇/レート制限で停止 (exit={code})")
        else:
            log_error(f"@{agent_name} 失敗 (exit={code})")
        if stderr:
            log_error(f"  stderr: {stderr[:500]}")
    return code, agent_output, stderr, usage

# ---------------------------------------------------------------------------
# パイプラインステップ
# ---------------------------------------------------------------------------

def step_create_branch(state: PipelineState) -> bool:
    """タスク用ブランチを作成（masterの最新を取得してから分岐）"""
    branch = f"feature/{state.facility}_{state.flow}"
    state.branch_name = branch

    # 現在のブランチ確認
    code, stdout, _ = run_cmd(["git", "branch", "--show-current"])
    current = stdout.strip()
    if current == branch:
        log_info(f"既にブランチ {branch} にいます")
        return True

    # masterに戻ってリモート最新を取得
    log_info("masterの最新を取得中...")
    run_cmd(["git", "stash"])  # 未コミット変更を退避
    code, _, stderr = run_cmd(["git", "checkout", "master"])
    if code != 0:
        log_warn(f"masterへのチェックアウト失敗: {stderr}")

    # リモートが設定されている場合のみpull
    code, stdout, _ = run_cmd(["git", "remote", "-v"])
    if stdout.strip():
        code, _, stderr = run_cmd(["git", "pull", "origin", "master"])
        if code == 0:
            log_ok("master最新取得完了")
        else:
            log_warn(f"git pull 失敗（続行します）: {stderr}")

    # ブランチが存在するか確認
    code, stdout, _ = run_cmd(["git", "branch", "--list", branch])
    if stdout.strip():
        log_info(f"既存ブランチ {branch} にチェックアウト")
        code, _, stderr = run_cmd(["git", "checkout", branch])
    else:
        log_info(f"新規ブランチ {branch} を作成")
        code, _, stderr = run_cmd(["git", "checkout", "-b", branch])

    if code != 0:
        log_error(f"ブランチ操作失敗: {stderr}")
        return False

    log_ok(f"ブランチ: {branch}")
    return True


def step_director(state: PipelineState) -> bool:
    """Director: 設計書を生成"""
    # resume 時の director skip: output/scenarios/{施設}_{flow}/ に既存設計書があれば
    # 再生成不要（director LLM 呼び出しは ~10〜20 分かかるため、無駄を避ける）。
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    existing_yaml = scenario_dir / f"設計書_{state.facility}_{state.flow}.yaml"
    existing_md = scenario_dir / f"設計書_{state.facility}_{state.flow}.md"
    if existing_yaml.exists():
        log_info(f"既存設計書を再利用（director skip）: {existing_yaml.name}")
        state.outputs["design_spec"] = str(existing_yaml)
        _normalize_state_from_yaml(state)
        return True
    if existing_md.exists():
        log_info(f"既存設計書を再利用（director skip）: {existing_md.name}")
        state.outputs["design_spec"] = str(existing_md)
        return True

    # 設計書 YAML が無い場合、既定では director LLM を起動しない（keystone: YAML 生成に LLM を置かない）。
    # 決定論入口（/sparring-intake）で設計書を作ってから再実行すること。
    if not state.allow_director_llm:
        state.errors.append("design_spec not found (director LLM is disabled by default)")
        log_error(
            f"設計書がありません: {existing_yaml}\n"
            f"  director LLM による自動起草は既定で無効です（YAML 生成は決定論入口のみ）。\n"
            f"  次のいずれかで設計書を作成してから再実行してください:\n"
            f"    - /sparring-intake {state.facility} {state.flow}（drawio → scenario_from_drawio.py）\n"
            f"    - CSV 入口: tools/raw_to_spec.py → tools/csv_to_yaml.py\n"
            f"    - 壁打ちで YAML を直接作成して {existing_yaml} に配置\n"
            f"  （従来の director LLM 起草を使う場合のみ --allow-director-llm を付ける）"
        )
        return False

    # 作業種別ヒントをプロンプトに付加（Gen2/Gen1移管時）
    pattern_hint = ""
    if state.pattern == 3:
        pattern_hint = "\n作業種別: Gen2→Gen3移管"
    elif state.pattern == 4:
        pattern_hint = "\n作業種別: Gen1→Gen3移管"

    # 移管ノートなら先頭を読み、"元資料: " の行から Customer Doc パスを抽出して必読指示に含める
    # (Gen2 移管では移管ノートは80行程度の要約で、全量データは元資料の Markdown に入っているため)
    source_hint = ""
    try:
        spec_full = PROJECT_DIR / state.spec_path if not Path(state.spec_path).is_absolute() else Path(state.spec_path)
        if spec_full.exists() and spec_full.suffix == ".md":
            head = spec_full.read_text(encoding="utf-8", errors="replace").splitlines()[:20]
            for line in head:
                # 「# 元資料: ...」または「元資料: ...」行を検出
                m = re.search(r"元資料[:：]\s*(\S+)", line)
                if m:
                    source_path = m.group(1).strip("`'\" ")
                    source_hint = (
                        f"\n【重要・必読】入力資料は要約・移管ノートです。"
                        f"**本文の全量データ（診療科リスト・TTS文言・分岐条件等）は元資料側に記載**されています。"
                        f"元資料を必ず Read ツールで全量読み込んでから設計書を生成してください:\n"
                        f"元資料: {source_path}\n"
                        f"移管ノートだけで設計書を起草するのは禁止。TTS 文言・診療科名等を推測・仮置き・"
                        f"TODO_* プレースホルダーで埋めることもしない。"
                    )
                    break
    except Exception:
        pass

    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    scenario_dir.mkdir(parents=True, exist_ok=True)  # director Write 用に事前作成
    scenario_dir_rel = f"output/scenarios/{state.facility}_{state.flow}"
    prompt = (
        f"以下の資料から設計書を生成してください。\n"
        f"入力資料: {state.spec_path}\n"
        f"出力形式: YAML（docs/specs/設計書テンプレート.yaml に準拠、scenario_flow ブロック構造）\n"
        f"出力先（ディレクトリは作成済み）:\n"
        f"  - 設計書: {scenario_dir_rel}/設計書_{state.facility}_{state.flow}.yaml\n"
        f"  - 確認レポート: {scenario_dir_rel}/確認レポート_{state.facility}_{state.flow}_{{YYYYMMDD}}.md\n"
        f"ブロック型と output_format の選定は docs/brekeke/モジュール選定ガイド_v2.md を参照してください。\n"
        f"\n"
        f"## 必須ルール（違反は validator で機械検出され reject されます）\n"
        f"\n"
        f"1. **モジュール名・step 名・termination 名は ASCII または安全な日本語のみ**。\n"
        f"   丸数字（①②③…⑩）/ 環境依存文字 / 特殊記号は **絶対禁止**。\n"
        f"   元資料（commubo抽出 / Gen2 customer_doc）に `END_①` `出口②` のような番号付き出口が\n"
        f"   あっても、Gen3 では `END_紹介状なし` `END_HP案内` 等 **意味のある日本語に置換**すること。\n"
        f"\n"
        f"2. **ContextMatchRouter の `reference_module` はモジュール名のみ**。\n"
        f"   ❌ NG: `reference_module: \"classification\"` (= context 名)\n"
        f"   ❌ NG: `reference_module: \"incoming-classifier\"` (= architecture 名)\n"
        f"   ❌ NG: `reference_module: \"診察券番号聴取\"` (= subflow 内の何か、step 名でなければ NG)\n"
        f"   ✅ OK: `reference_module: \"OpenAI_用件確認\"` (= 同フロー内の OpenAI モジュール名)\n"
        f"   ✅ OK: `reference_module: \"電話番号聴取\"` (= subflow ブロックの step 名そのもの)\n"
        f"\n"
        f"3. **ContextMatchRouter の conditions は必ず最後に `match: \"other\"` を含め、その next も明示**。\n"
        f"   暗黙のフォールバックは禁止（scaffold ERROR、validator CMR-007 で機械検出）。\n"
        f"\n"
        f"4. **Gen1 → Gen3 変換では OpenAI + ContextMatchRouter + context を活用**。\n"
        f"   Gen1 の「箱が直接条件分岐を持つ」構造（用件の分岐_0/1/2/3 等の重複箱）は、\n"
        f"   Gen3 では **OpenAI が用件分類 → context に保存 → ContextMatchRouter で参照** に集約する。\n"
        f"   重複箱を独立ブロック化しないこと（`feedback_gen1_director_default_rules` 第 3 項）。\n"
        f"\n"
        f"上記 4 点は CLAUDE.md / .claude/agents/director.md の\n"
        f"既存記述を抜粋した「再強調」です。詳細は agent 定義書を参照してください。"
        f"{source_hint}"
        f"{pattern_hint}"
    )
    # Direction-2: director は Sonnet で実行（agent 定義の Opus を上書き）
    code, stdout, stderr, _ = invoke_agent("director", prompt, model_override="claude-sonnet-5")
    if code != 0:
        state.errors.append(f"director failed: {stderr[:200]}")
        return False

    # 出力ファイルの存在確認: output/scenarios/{施設}_{flow}/ 配下を最優先、
    # 後方互換で docs/designs/ も探す（過去施設の resume 用、将来削除予定）。
    yaml_path = scenario_dir / f"設計書_{state.facility}_{state.flow}.yaml"
    md_path = scenario_dir / f"設計書_{state.facility}_{state.flow}.md"
    legacy_yaml = PROJECT_DIR / "docs" / "designs" / f"設計書_{state.facility}_{state.flow}.yaml"
    legacy_md = PROJECT_DIR / "docs" / "designs" / f"設計書_{state.facility}_{state.flow}.md"
    if yaml_path.exists():
        state.outputs["design_spec"] = str(yaml_path)
    elif md_path.exists():
        state.outputs["design_spec"] = str(md_path)
    elif legacy_yaml.exists():
        state.outputs["design_spec"] = str(legacy_yaml)
    elif legacy_md.exists():
        state.outputs["design_spec"] = str(legacy_md)
    else:
        state.errors.append(
            f"director output not found at {scenario_dir} (or docs/designs/ legacy path)"
        )
        log_error(f"設計書ファイルが見つかりません: {scenario_dir}/設計書_*.{{yaml,md}}")
        return False

    # 設計書 YAML の basic_info.facility_name / scenario_name で state を正規化
    # （extract_names がファイル名ベースで誤推定していた場合の救済）
    _normalize_state_from_yaml(state)

    return True


def step_yaml_scaffold(state: PipelineState) -> bool:
    """P1+1 Step 1: flow-draft MD → YAML スケルトン生成（決定論スクリプト）"""
    # flow-draft MD を探す: output/scenarios/{facility}_{flow}/ 配下に flow_draft_*.md があるか
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    candidates = sorted(scenario_dir.glob("flow_draft_*.md"), reverse=True)
    if not candidates:
        # --spec で直接 flow_draft MD を渡している場合
        if state.spec_path and "flow_draft" in state.spec_path:
            fd_path = Path(state.spec_path)
        else:
            log_error(
                f"flow-draft MD が見つかりません: {scenario_dir}/flow_draft_*.md\n"
                f"先に /flow-draft スキルで構造ドラフトを作成し、"
                f"output/scenarios/{state.facility}_{state.flow}/flow_draft_YYYYMMDD.md として保存してください。"
            )
            state.errors.append("flow-draft MD not found")
            return False
    else:
        fd_path = candidates[0]

    log_info(f"flow-draft MD: {fd_path.name}")
    script = PROJECT_DIR / "tools" / "yaml_scaffold_template.py"
    cmd = [
        sys.executable, str(script),
        "--flow-draft", str(fd_path),
        "--facility", state.facility,
        "--flow", state.flow,
    ]
    ok, stdout, stderr = run_cmd(cmd, timeout=60)
    for line in stderr.strip().splitlines():
        if line.startswith("ERROR"):
            log_error(line)
        else:
            log_info(line)
    if not ok:
        state.errors.append("yaml_scaffold_template failed")
        return False

    skeleton_path = stdout.strip()
    if not skeleton_path or not Path(skeleton_path).exists():
        log_error(f"スケルトン YAML の出力先が不明: '{skeleton_path}'")
        state.errors.append("yaml_scaffold_template: output path unknown")
        return False

    state.outputs["yaml_skeleton"] = skeleton_path
    log_ok(f"スケルトン YAML: {Path(skeleton_path).name}")
    return True


def step_yaml_fill(state: PipelineState) -> bool:
    """P1+1 Step 2: スケルトン YAML + customer_doc → Sonnet が PLACEHOLDER を埋める"""
    skeleton_path = state.outputs.get("yaml_skeleton", "")
    if not skeleton_path or not Path(skeleton_path).exists():
        log_error("スケルトン YAML がありません（step_yaml_scaffold を先に実行してください）")
        state.errors.append("yaml_skeleton not found")
        return False

    skeleton_rel = Path(skeleton_path).relative_to(PROJECT_DIR)
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    final_yaml = scenario_dir / f"設計書_{state.facility}_{state.flow}.yaml"

    # customer_doc（--spec）の参照
    spec_note = ""
    if state.spec_path:
        spec_note = (
            f"- **顧客資料**: `{state.spec_path}`（必ず Read ツールで全量読み込んで参照すること）\n"
        )

    prompt = f"""\
P1+1 パイプライン — YAML プレースホルダー補完タスク

あなたは {state.facility} {state.flow} フローの設計書 YAML の補完を担当します。

## 入力

- **スケルトン YAML**: `{skeleton_rel}`（scaffold_template.py が生成した骨格。`{{PLACEHOLDER_*}}` が埋まっていない）
{spec_note}
## 作業内容

1. スケルトン YAML を Read ツールで読み込む。
2. 顧客資料（--spec）がある場合は Read ツールで全量読み込む。
3. **`{{PLACEHOLDER_*}}` を全て実際の値に置換して**、完成した YAML を書き出す。

### 補完ルール

| PLACEHOLDER | 補完内容 |
|---|---|
| `{{PLACEHOLDER_GROUP_NAME}}` | Brekeke グループ名（フロー名プレフィックス）。通常 `{state.facility}$` 形式 |
| `{{PLACEHOLDER_FLOW_NAME}}` | Brekeke フロー名。`{{GROUP_NAME}}{state.flow}` 形式 |
| `{{PLACEHOLDER_TARGET_FACILITY}}` | 施設の正式名称（顧客資料から） |
| `{{PLACEHOLDER_PHONE_NUMBER}}` | 施設の代表電話番号（顧客資料から。不明なら "TODO_要確認"） |
| `{{PLACEHOLDER_BUSINESS_HOURS}}` | 受付時間帯（顧客資料から） |
| `{{PLACEHOLDER_PURPOSE}}` | フローの目的（1〜3文、顧客資料の概要から） |
| `{{PLACEHOLDER_TTS}}` | TTS 発話文言。`{{tts_g:...}}` 形式（顧客資料の文言 or 標準テンプレート） |
| `{{PLACEHOLDER_SAVE_TO}}` | context フィールド名（camelCase、例: `classification` `patientName`） |
| `{{PLACEHOLDER_CHOICES}}` | hearing の choices リスト（顧客資料から） |
| `{{PLACEHOLDER_LABELS}}` | hearing の output_labels（choices と同じラベル名リスト） |
| `{{PLACEHOLDER_STT_TYPE}}` | `"DTMF_AmiVoice"` または `"AmiVoice"` |
| `{{PLACEHOLDER_OAI_TYPE}}` | `"classify"` / `"normalize"` / `"free_text"` |
| `{{PLACEHOLDER_STATUS}}` | 終話ステータス番号（1=未処理 2=代表案内 3=聴取失敗 6=時間外） |
| `{{PLACEHOLDER_SMS_FLAG}}` | SMS フラグ（1=送信 -1=不要）。SMS 機能のないフローは -1 |
| `{{PLACEHOLDER_NEXT}}` | 次ステップ名（scenario_flow の step 名を参照して補完） |
| `{{PLACEHOLDER_REFERENCE_MODULE}}` | ContextMatchRouter の参照モジュール名（直前の OpenAI モジュール名） |
| `{{PLACEHOLDER_RETRY_FAILURE}}` | リトライ失敗時の遷移先 step 名 |
| `{{PLACEHOLDER_SCRIPT_TEMPLATE}}` | script_template 値（yes_no_classifier / n_choice / custom 等） |
| `{{PLACEHOLDER_OTHER_NEXT}}` | CMR の other 分岐先 step 名 |
| `{{PLACEHOLDER_FLOWNAME}}` | subflow の Brekeke フロー名（`GROUP_NAME$サブフロー名` 形式） |
| `{{PLACEHOLDER_TRANSFER_FAILURE_TTS}}` | 転送失敗時の TTS 文言 |
| `{{PLACEHOLDER_DATE}}` | 本日の日付 YYYY/MM/DD |
| context_fields セクション | 顧客資料を参照して全量を正しく定義する（PLACEHOLDER 行を置換） |
| hearing_items セクション | save_to / output_labels / STT タイプ / notes を顧客資料から埋める |
| step_details セクション | 各ステップの TTS 文言を顧客資料から埋める |
| termination_patterns セクション | 各終話の TTS・status・sms_flag を顧客資料から埋める |

### 品質ルール

- TTS 文言は `{{tts_g:〇〇〇}}` 形式（SSML 禁止・大文字 TTS_AI 禁止）
- ContextMatchRouter の conditions は必ず末尾に `match: "other"` を含める
- N 択 hearing（polar 以外）は `choices:` の宣言が必須
- context_fields の `status` フィールドは `display_type: STATUS` で定義する
- モジュール名・step 名に丸数字（①②）や環境依存文字を使わない

## 出力

完成した設計書 YAML を以下のパスに書き出す:
`{final_yaml.relative_to(PROJECT_DIR)}`

スケルトン YAML の `{{PLACEHOLDER_*}}` を全て置換して出力すること。
書き出したら最後に「補完完了: {final_yaml.name}」と出力する。
"""

    log_info("Sonnet エージェントで YAML プレースホルダーを補完中...")
    ok, stdout, stderr = _run_subagent(
        prompt=prompt,
        model="claude-sonnet-5",
        timeout=900,
    )
    if not ok:
        log_error("yaml_fill_placeholders エージェント失敗")
        state.errors.append(f"yaml_fill failed: {stderr[:200]}")
        return False

    # 出力ファイルの確認
    if not final_yaml.exists():
        log_error(f"補完 YAML の出力先が見つかりません: {final_yaml}")
        state.errors.append("yaml_fill: final yaml not written")
        return False

    state.outputs["design_spec"] = str(final_yaml)
    _normalize_state_from_yaml(state)
    log_ok(f"設計書 YAML 補完完了: {final_yaml.name}")
    return True


def _normalize_state_from_yaml(state: PipelineState) -> None:
    """director 出力の YAML から basic_info.facility_name / scenario_name を読み、
    state.facility / state.flow を正規化する。ファイル名も合わせてリネーム。

    extract_names() は spec パスのファイル名から推定するため、
    `【診療1】：医誠会国際総合病院.md` のような customer_doc を spec に渡すと
    facility=`【診療1】：医誠会国際総合病院` / flow=`main` と誤抽出される。
    director が正しく書いた YAML を正として上書きする。
    """
    spec_path = state.outputs.get("design_spec", "")
    if not spec_path or not str(spec_path).endswith(".yaml"):
        return
    try:
        import yaml
        with open(spec_path, encoding="utf-8") as f:
            spec_data = yaml.safe_load(f) or {}
    except Exception as e:
        log_warn(f"設計書 YAML 読み取りに失敗したため state 正規化をスキップ: {e}")
        return

    bi = spec_data.get("basic_info", {}) or {}
    new_facility = str(bi.get("facility_name") or "").strip()
    new_scenario = str(bi.get("scenario_name") or "").strip()
    # scenario_name が未設定の既存 YAML は flow_name の '$' 以降から派生
    if not new_scenario:
        flow_name = str(bi.get("flow_name") or "").strip()
        if "$" in flow_name:
            new_scenario = flow_name.split("$", 1)[1]

    if not new_facility or not new_scenario:
        # qa_validator T-2 で警告/CRITICAL。ここでは state 更新せず後工程に委ねる
        return
    if new_facility == state.facility and new_scenario == state.flow:
        return

    old_facility, old_flow = state.facility, state.flow
    state.facility = new_facility
    state.flow = new_scenario
    log_info(f"設計書 YAML から state 正規化: {old_facility}_{old_flow} → {state.facility}_{state.flow}")

    # 設計書ファイル名も合わせてリネーム（後続ステップが新名称で再読み込みできるように）
    old_path = Path(spec_path)
    old_token = f"設計書_{old_facility}_{old_flow}"
    new_token = f"設計書_{state.facility}_{state.flow}"
    if old_token in old_path.name:
        new_path = old_path.parent / old_path.name.replace(old_token, new_token)
        if new_path.exists() and new_path != old_path:
            log_warn(f"リネーム先 {new_path.name} が既に存在。旧ファイルを残します")
        else:
            old_path.rename(new_path)
            state.outputs["design_spec"] = str(new_path)
            log_info(f"設計書ファイルもリネーム: {old_path.name} → {new_path.name}")


def _run_qa_validator(spec: str, json_report: str | None = None) -> tuple:
    """qa_validator.py を実行し (exit_code, stdout, stderr) を返す

    json_report を指定すると Issue 詳細を JSON でダンプする（yaml_auto_fixer.py 用）。
    """
    cmd = ["python3", "schemas/qa_validator.py", spec]
    if json_report:
        cmd += ["--json-report", json_report]
    return run_cmd(cmd, timeout=VALIDATOR_TIMEOUT)


def _run_yaml_auto_fixer(spec: str, report: str) -> tuple[bool, str]:
    """yaml_auto_fixer.py を実行。(適用したか, stderr メッセージ) を返す"""
    cmd = ["python3", "scripts/yaml_auto_fixer.py", "--spec", spec, "--report", report]
    code, stdout, stderr = run_cmd(cmd, timeout=VALIDATOR_TIMEOUT)
    if stderr:
        print(stderr)
    # stderr の "適用: N 件" を見て N>0 を判定
    applied = False
    for line in stderr.splitlines():
        if "適用:" in line and "件" in line:
            m = re.search(r"適用:\s*(\d+)\s*件", line)
            if m and int(m.group(1)) > 0:
                applied = True
                break
    return applied, stderr


def step_qa(state: PipelineState) -> bool:
    """QA: 機械チェック（qa_validator.py）→ yaml_auto_fixer → 不備は人間（壁打ち）へ差し戻し

    フロー（v2 / 2026-06-19: Director 自律差し戻しループを廃止）:
      1. qa_validator.py 実行（--json-report 付き）
      2. CRITICAL あり → yaml_auto_fixer.py で fix_category="auto" を機械適用 → 再チェック
      3. それでも CRITICAL あり → **人間（壁打ち）へ差し戻し**（自律 LLM ループは置かない）

    旧版は残存 CRITICAL を Director に最大 MAX_QA_RETRIES 回 自律差し戻ししていたが、
    ループ・ガバナンス v0.2（project-governance/docs/loop-governance.md §9）で
    「ライン内に自律修復 LLM を置かない／修復は工場外の人間壁打ち」へ転換。
    残存 CRITICAL は人間が壁打ちで設計書（＝生成器入力）を直し、パイプラインを再実行する。
    """
    spec = state.outputs.get("design_spec", state.spec_path)
    reports_dir = PROJECT_DIR / "output" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    qa_report_path = str(reports_dir / f"qa_report_{state.facility}_{state.flow}.json")
    state.qa_retry_count = 1  # 自律リトライ廃止（機械チェック 1 パス + auto-fix のみ）

    # ── 機械チェック → 機械 auto-fix → 再チェック（決定論のみ・LLM 差し戻しなし）──
    log_info("QA機械チェック")
    code, stdout, stderr = _run_qa_validator(spec, json_report=qa_report_path)
    print(stdout)

    mechanical_pass = (code == 0)
    if mechanical_pass:
        log_ok("QA機械チェック PASS")
    else:
        log_warn("QA機械チェック FAIL -- CRITICAL検出")
        # yaml_auto_fixer で fix_category='auto' の Issue を機械修正 → 再チェック
        if Path(qa_report_path).exists():
            log_info("yaml_auto_fixer: fix_category='auto' の Issue を機械修正")
            applied, _ = _run_yaml_auto_fixer(spec, qa_report_path)
            if applied:
                code, stdout, _ = _run_qa_validator(spec, json_report=qa_report_path)
                print(stdout)
                if code == 0:
                    log_ok("yaml_auto_fixer で CRITICAL を全解消 → QA PASS")
                    mechanical_pass = True

    if not mechanical_pass:
        # ── 残存 CRITICAL を「壁打ち Claude が拾える差し戻し票」として提示し halt ──
        # 受け手は壁打ち相手の Claude。どの gate / どの check / どの設計書の差し戻しかを
        # 一目で判断できる構造にする（散文の指示は最小限）。
        criticals = []
        try:
            report = json.loads(Path(qa_report_path).read_text(encoding="utf-8"))
            criticals = [i for i in report.get("issues", []) if i.get("severity") == "CRITICAL"]
        except Exception:
            pass
        log_error("=" * 64)
        log_error(f"【差し戻し】入口ゲート(qa_validator) → 人間（壁打ち）: CRITICAL {len(criticals)} 件")
        log_error(f"  直す対象（＝生成器入力）: {spec}")
        if criticals:
            for i in criticals:
                log_error(f"  ・[{i.get('code', '?')}] {i.get('message', '')}")
        else:
            log_error(f"  （詳細は差し戻し票を参照: {qa_report_path}）")
        log_error(f"  差し戻し票(JSON): {qa_report_path}")
        log_error("  → 壁打ちで上記を設計書に反映 → パイプライン再実行（成果物でなく設計書を直す）")
        log_error("=" * 64)
        codes = ",".join(i.get("code", "?") for i in criticals) or "(report参照)"
        state.errors.append(
            f"KICKBACK[入口ゲート/qa_validator] CRITICAL x{len(criticals)} [{codes}] -> human(壁打ち). "
            f"design={spec} ticket={qa_report_path}"
        )
        if state.unattended:
            log_warn("無人モード: 機械チェック未解消のまま続行（残存問題は成果物に記録）")
        else:
            return False

    # LLM審査は廃止済み。全チェックがqa_validator.pyに統合された。
    return True


def step_copy_subflows(state: PipelineState) -> bool:
    """copy_subflows.py: サブフロー静的JSONをサンプルからコピーしリネームする"""
    spec = state.outputs.get("design_spec", state.spec_path)
    if not spec:
        log_warn("copy_subflows: 設計書パスが不明のためスキップ")
        return True

    # 命名規則（2026-06-04）: 日付サフィックスは group_name 側に含まれ、copy_subflows は
    # サブフロー名を `{group_name}$target`（日付なし）で生成する。--date は後方互換で受理されるが
    # 命名には不使用（copy_subflows.py 側で no-op）。
    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "copy_subflows.py"),
        "--spec", str(spec),
    ]
    log_info(f"copy_subflows: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=SCRIPT_TIMEOUT,
                              encoding="utf-8", errors="replace")
    if result.stdout:
        print(result.stdout)
    if result.returncode != 0:
        log_error(f"copy_subflows 失敗:\n{result.stderr}")
        state.errors.append(f"copy_subflows failed: {result.stderr[:200]}")
        return False
    return True


def step_scaffold_generator(state: PipelineState) -> bool:
    """scaffold_generator.py: YAML設計書からフローJSON骨格を自動生成する（必須ステップ）"""
    spec = state.outputs.get("design_spec", state.spec_path)
    if not spec:
        log_error("scaffold_generator: 設計書パスが不明 — パイプライン停止")
        state.errors.append("scaffold: 設計書パス不明")
        return False

    # YAML 設計書でない場合は致命的エラー（generator はパッチモード専用）
    if not str(spec).endswith(".yaml"):
        log_error(f"scaffold_generator: YAML設計書ではありません ({spec}) — パイプライン停止")
        state.errors.append(f"scaffold: YAML設計書が必要ですが {Path(spec).suffix} が指定されています")
        return False

    # 旧パイプラインの成果物を削除（build_bivr がメインフロー重複を拾うのを防止）
    spec_stem = Path(spec).stem.replace("設計書_", "")
    json_dir = PROJECT_DIR / "output" / "json"
    for prefix in ("prompted_", "reviewed_", "merged_", "scaffold_"):
        old = json_dir / f"{prefix}{spec_stem}.json"
        if old.exists():
            old.unlink()
            log_info(f"旧ファイル削除: {old.name}")

    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "scaffold_generator.py"),
        str(spec),
    ]
    log_info(f"scaffold_generator: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            timeout=SCRIPT_TIMEOUT)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_error(f"scaffold_generator 失敗 — パイプライン停止:\n{result.stderr[:200]}")
        state.errors.append(f"scaffold: {result.stderr[:200]}")
        return False

    # スキャフォールドファイルのパスを spec 名から導出（stdout の文字化けに依存しない）
    spec_stem = Path(spec).stem.replace("設計書_", "")
    scaffold_path = str(PROJECT_DIR / "output" / "json" / f"scaffold_{spec_stem}.json")
    if not Path(scaffold_path).exists():
        log_error("scaffold_generator: 出力ファイルが見つかりません — パイプライン停止")
        state.errors.append("scaffold: 出力ファイル不明")
        return False

    state.outputs["scaffold_json"] = scaffold_path
    log_ok(f"Scaffold: {Path(scaffold_path).name}")
    return True


def step_gen_scripts(state: PipelineState) -> bool:
    """gen_scripts.py: 設計書YAMLの script_blocks から ES5 Scripts を生成し scaffold に埋め込む。
    script_blocks セクションが無い設計書では no-op（scaffold_json はそのまま次工程へ）。
    """
    scaffold = state.outputs.get("scaffold_json")
    if not scaffold or not Path(scaffold).exists():
        log_error("gen_scripts: scaffold_json が存在しません")
        state.errors.append("gen_scripts: scaffold_json 不在")
        return False

    spec = state.outputs.get("design_spec", state.spec_path)
    if not spec or not str(spec).endswith(".yaml") or not Path(str(spec)).exists():
        log_info("gen_scripts: YAML設計書が見つからないためスキップ")
        return True

    scaffold_path = Path(scaffold)
    scripted_path = scaffold_path.with_name(scaffold_path.stem + "_scripted.json")

    cmd = [
        sys.executable,
        str(PROJECT_DIR / "tools" / "gen_scripts.py"),
        "--yaml", str(spec),
        "--scaffold", str(scaffold),
        "--out", str(scripted_path),
    ]
    log_info(f"gen_scripts: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            timeout=SCRIPT_TIMEOUT)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_error(f"gen_scripts 失敗 — パイプライン停止:\n{result.stderr[:200]}")
        state.errors.append(f"gen_scripts: {result.stderr[:200]}")
        return False

    if not scripted_path.exists():
        # script_blocks セクション不在 → no-op（gen_scripts.py が exit 0 のみで --out を書かない）
        log_info("gen_scripts: script_blocks 未定義のためスキップ（scaffold は変更なし）")
        return True

    state.outputs["scaffold_json"] = str(scripted_path)
    log_ok(f"Scripts: {scripted_path.name}")
    return True


def step_test_scaffold_generator(state: PipelineState) -> bool:
    """test_scaffold_generator.py: Pattern 6 (テストフロー) 専用 scaffold

    本番 scaffold_generator.py には触らず、テスト用 block 型
    (inline_script / context_match_router / opening / announcement / termination) のみ対応
    した別スクリプトを呼ぶ。出力は通常 scaffold と同じ output/json/scaffold_*.json 形式で、
    以降の layout / add_date / build_bivr が共通で拾えるようにする。
    """
    spec = state.outputs.get("design_spec", state.spec_path)
    if not spec:
        log_error("test_scaffold: 設計書パスが不明 — パイプライン停止")
        state.errors.append("test_scaffold: 設計書パス不明")
        return False

    if not str(spec).endswith(".yaml"):
        log_error(f"test_scaffold: YAML設計書ではありません ({spec}) — パイプライン停止")
        state.errors.append(f"test_scaffold: YAML設計書が必要")
        return False

    spec_stem = Path(spec).stem.replace("設計書_", "")
    json_dir = PROJECT_DIR / "output" / "json"
    old = json_dir / f"scaffold_{spec_stem}.json"
    if old.exists():
        old.unlink()
        log_info(f"旧ファイル削除: {old.name}")

    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "test_scaffold_generator.py"),
        str(spec),
    ]
    log_info(f"test_scaffold_generator: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            timeout=SCRIPT_TIMEOUT)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_error(f"test_scaffold_generator 失敗 — パイプライン停止:\n{result.stderr[:200]}")
        state.errors.append(f"test_scaffold: {result.stderr[:200]}")
        return False

    scaffold_path = str(json_dir / f"scaffold_{spec_stem}.json")
    if not Path(scaffold_path).exists():
        log_error("test_scaffold_generator: 出力ファイルが見つかりません")
        state.errors.append("test_scaffold: 出力ファイル不明")
        return False

    state.outputs["scaffold_json"] = scaffold_path
    # build_bivr が merged_json/reviewed_json を期待するため、両方に scaffold_json を登録
    state.outputs["merged_json"] = scaffold_path
    state.outputs["reviewed_json"] = scaffold_path
    log_ok(f"Test Scaffold: {Path(scaffold_path).name}")
    return True


def step_extract_bivr(state: PipelineState) -> bool:
    """Pattern 2: base_path が .bivr の場合に JSON に展開し、base_path を更新する。
    JSON の場合はそのまま通過。"""
    base = state.base_path
    if not base:
        log_error("extract_bivr: --base が指定されていません")
        state.errors.append("extract_bivr: base_path 不明")
        return False

    if not base.endswith(".bivr"):
        log_info(f"extract_bivr: JSON 直接指定のためスキップ ({Path(base).name})")
        return True

    if not Path(base).exists():
        log_error(f"extract_bivr: BIVR が見つかりません: {base}")
        state.errors.append(f"extract_bivr: {base} 不在")
        return False

    # 専用ディレクトリに展開（他施設の旧ファイルとの混在を防止）
    bivr_stem = Path(base).stem  # "北里大学TSC"
    output_dir = PROJECT_DIR / "output" / "json" / f"_extracted_{bivr_stem}"
    if output_dir.exists():
        import shutil
        shutil.rmtree(str(output_dir))
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "extract_bivr.py"),
        str(base),
        "-o", str(output_dir),
    ]
    log_info(f"extract_bivr: BIVR 展開 → {output_dir}")
    code, stdout, stderr = run_cmd(cmd, timeout=SCRIPT_TIMEOUT)
    if stdout:
        print(stdout)
    if code != 0:
        log_error(f"extract_bivr 失敗: {stderr[:200]}")
        state.errors.append(f"extract_bivr: {stderr[:200]}")
        return False

    # 展開された JSON のうちメインフロー（最大モジュール数）を base_path にセット
    extracted = sorted(output_dir.glob("*.json"), key=lambda p: p.stat().st_size, reverse=True)
    if not extracted:
        log_error("extract_bivr: 展開後の JSON が見つかりません")
        return False

    main_json = str(extracted[0])
    state.base_path = main_json
    state.outputs["draft_json"] = main_json
    log_ok(f"BIVR 展開完了: {Path(main_json).name} (メインフロー)")

    for p in extracted[1:]:
        log_info(f"  サブフロー: {p.name}")

    return True


def step_scaffold_extractor(state: PipelineState) -> bool:
    """scaffold_extractor.py: 既存JSONから scenario_flow YAML を逆抽出（Pattern 2 専用）"""
    json_path = state.base_path
    if not json_path or not Path(json_path).exists():
        log_error(f"scaffold_extractor: 既存JSONが見つかりません: {json_path}")
        state.errors.append(f"extract: {json_path} 不在")
        return False

    extracted_yaml = PROJECT_DIR / "output" / "json" / f"extracted_{Path(json_path).stem}.yaml"
    garbage_report = PROJECT_DIR / "output" / "reports" / f"garbage_{Path(json_path).stem}.md"

    # --full-spec で逆走（hearing_items/step_details/context_fields 等も出力）。リフレッシュモードで必須。
    # プロパティファイルは customer_docs から auto 検出（存在すれば --properties に渡す）。
    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "scaffold_extractor.py"),
        str(json_path),
        "-o", str(extracted_yaml),
        "--garbage-report", str(garbage_report),
        "--full-spec",
        "--facility-name", state.facility,
        "--flow-name", state.flow,
    ]
    property_candidates = [
        PROJECT_DIR / "docs" / "reference" / "customer_docs" / f"property_{state.facility}_{state.flow}.md",
        PROJECT_DIR / "docs" / "reference" / "customer_docs" / f"property_{state.facility}.md",
    ]
    for prop_path in property_candidates:
        if prop_path.exists():
            cmd.extend(["--properties", str(prop_path)])
            log_info(f"scaffold_extractor: properties 検出 → {prop_path.name}")
            break
    log_info(f"scaffold_extractor: {' '.join(cmd[:3])}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            timeout=SCRIPT_TIMEOUT)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_error(f"scaffold_extractor 失敗: {result.stderr[:200]}")
        state.errors.append(f"extract: {result.stderr[:200]}")
        return False

    if not extracted_yaml.exists():
        log_error("scaffold_extractor: 出力 YAML が見つかりません")
        return False

    state.outputs["extracted_yaml"] = str(extracted_yaml)
    state.outputs["design_spec"] = str(extracted_yaml)  # dirlite / gen_p7_cases が参照
    if garbage_report.exists():
        state.outputs["garbage_report"] = str(garbage_report)
        log_warn(f"ガベージモジュール検出: {garbage_report}")
    log_ok(f"Extracted YAML: {extracted_yaml.name}")
    return True


def step_layout_calculator(state: PipelineState) -> bool:
    """layout_calculator.py: フローJSONのモジュールレイアウト自動計算"""
    scaffold = state.outputs.get("scaffold_json")
    if not scaffold or not Path(scaffold).exists():
        log_error("layout_calculator: scaffold_json が存在しません")
        state.errors.append("layout: scaffold_json 不在")
        return False

    spec_path = state.outputs.get("design_spec", state.spec_path)
    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "layout_calculator.py"),
        str(scaffold),
    ]
    if spec_path and str(spec_path).endswith(".yaml") and Path(str(spec_path)).exists():
        cmd.append(str(spec_path))
    log_info(f"layout_calculator: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace",
                            timeout=SCRIPT_TIMEOUT)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_error(f"layout_calculator 失敗:\n{result.stderr[:200]}")
        state.errors.append(f"layout: {result.stderr[:200]}")
        return False

    log_ok("Layout: レイアウト計算完了")
    return True


def step_generator(state: PipelineState) -> bool:
    """Generator: スキャフォールドJSONをパッチしてフローJSONを完成させる（パッチモード専用）"""
    scaffold = state.outputs.get("scaffold_json")
    if not scaffold or not Path(scaffold).exists():
        log_error("generator: scaffold_json が存在しません — パイプライン停止（scaffold ステップの成功が必須）")
        state.errors.append("generator: scaffold_json 不在")
        return False

    # scenario_flow 対応設計書の場合、scaffold が完成品を出すため generator はスキップ
    spec = state.outputs.get("design_spec", state.spec_path)
    if spec and str(spec).endswith(".yaml"):
        try:
            import yaml
            with open(spec, encoding="utf-8") as f:
                spec_data = yaml.safe_load(f)
            if spec_data.get("scenario_flow"):
                # scaffold v2 で TODO_scaffold=0 → draft として scaffold をそのまま採用
                draft_path = str(PROJECT_DIR / "output" / "json" / f"draft_{state.facility}_{state.flow}.json")
                shutil.copy2(scaffold, draft_path)
                state.outputs["draft_json"] = draft_path
                # scaffold ファイルを削除（日付サフィックスなしのフロー名が build_bivr に混入するのを防止）
                try:
                    Path(scaffold).unlink()
                    log_info(f"scaffold ファイル削除: {Path(scaffold).name}")
                except OSError:
                    pass
                log_ok(f"Generator: scenario_flow 検出 → scaffold 完成品を draft として採用: {Path(draft_path).name}")
                return True
        except Exception:
            pass  # YAML 読み込み失敗時は従来の generator パッチモードにフォールバック

    prompt = (
        f"スキャフォールドファイルが生成済みです: {scaffold}\n"
        "パッチモードで動作してください: スキャフォールドJSONを Read し、"
        "設計書の routing_map を参照して TODO_scaffold をすべて解消してから "
        f"output/json/draft_{state.facility}_{state.flow}.json として出力してください。\n"
        f"設計書: {spec}\n\n"
        "【パッチモード作業ルール — 厳守】\n"
        "1. JSON編集は Edit / Write / Read ツールで直接行うこと。\n"
        "   scripts/ や任意のパスに Python スクリプトを新規生成して Bash で実行しないこと。\n"
        "2. validator.py を手動実行しないこと。バリデーションは後続パイプラインステップが担当する。\n"
        "3. python3 -c による JSON 検査は最小限にとどめること（Read ツールで代替できる場合は Read を使うこと）。\n"
        "4. スキャフォールドの構造（モジュール定義・type・params の骨格）は信頼してよい。\n"
        "   next / subs の接続と TODO_scaffold の解消に集中すること。"
    )

    code, stdout, stderr, _ = invoke_agent("generator", prompt)
    if code != 0:
        state.errors.append(f"generator failed: {stderr[:200]}")
        return False

    # draft ファイル検出: 施設名+フロー名の完全一致でサブフロー誤選択を防ぐ
    json_dir = PROJECT_DIR / "output" / "json"
    # まず exact match（日付なし）を優先
    exact = json_dir / f"draft_{state.facility}_{state.flow}.json"
    if exact.exists():
        drafts = [exact]
    else:
        # 日付サフィックス付き (draft_{facility}_{flow}_YYYYMMDD.json) にフォールバック
        drafts = sorted(
            json_dir.glob(f"draft_{state.facility}_{state.flow}_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    if not drafts:
        # フォールバック: specファイルのpathが【診療1】：病院名.md のような形式の場合など、
        # extract_names が正しく施設名・フロー名を取れず、generatorが別名で出力することがある。
        # サブフローキーワードを除く draft_*.json の中で最新のものを主フローとみなし、
        # state.facility / state.flow を実ファイル名から更新する。
        SUBFLOW_KEYWORDS = ["聴取", "RAG", "サブフロー", "subflow"]
        candidates = sorted(
            [p for p in json_dir.glob("draft_*.json")
             if not any(kw in p.stem for kw in SUBFLOW_KEYWORDS)],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if candidates:
            stem = candidates[0].stem.replace("draft_", "", 1)
            parts = stem.split("_", 1)
            if len(parts) == 2:
                old_name = f"{state.facility}_{state.flow}"
                state.facility, state.flow = parts[0], parts[1]
                log_info(f"施設名・フロー名を実ファイルから更新: {old_name} → {state.facility}_{state.flow}")
            drafts = candidates[:1]
    if drafts:
        state.outputs["draft_json"] = str(drafts[0])
        log_ok(f"Draft: {drafts[0].name}")
    else:
        log_error("Draft JSONが見つかりません")
        state.errors.append("No draft JSON found")
        return False

    return True


def step_validator(state: PipelineState, json_path: str, flags: str = "",
                   report_key: str = "") -> bool:
    """Validator: JSON構造チェック。report_key を指定するとレポートをファイル保存する。
    auto_fixer が読む --json-report も同時に生成する（存在すれば後段の auto_fixer が利用）。
    """
    cmd = ["python3", "schemas/validator.py", json_path]
    if flags:
        cmd.extend(flags.split())

    # JSON 形式レポートも生成（auto_fixer が機械読み）
    json_report_dir = PROJECT_DIR / "output" / "reports"
    json_report_dir.mkdir(parents=True, exist_ok=True)
    json_report_path = json_report_dir / f"validator_json_{state.facility}_{state.flow}.json"
    cmd.extend(["--json-report", str(json_report_path)])

    # 設計書 YAML を渡してblock_nameを付与（fixer のブロック特定精度向上）
    spec = state.outputs.get("design_spec") or state.spec_path
    if spec and str(spec).endswith(".yaml") and Path(str(spec)).exists():
        cmd.extend(["--yaml", str(spec)])

    code, stdout, stderr = run_cmd(cmd, timeout=VALIDATOR_TIMEOUT)
    print(stdout)

    # レポートをファイルに保存（後続の fixer が参照）
    if report_key:
        report_dir = PROJECT_DIR / "output" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_file = report_dir / f"{report_key}_{state.facility}_{state.flow}.md"
        report_file.write_text(stdout, encoding="utf-8")
        state.outputs[report_key] = str(report_file)
        log_info(f"Validatorレポート保存: {report_file.name}")

    if json_report_path.exists():
        state.outputs["validator_json_report"] = str(json_report_path)

    if code == 0:
        log_ok("Validator PASS")
        return True
    else:
        log_warn(f"Validator FAIL (exit={code})")
        if "CRITICAL" in stdout:
            log_warn("CRITICAL検出 — auto_fixer で機械修正 → fixer で残りを処理")
        return False


def step_format_prompt_strings(state: PipelineState) -> bool:
    """format_prompt_strings: OpenAI/Retry モジュールのリテラル \\n を実改行に正規化。
    prompter / fixer が Edit 時にエスケープ記法で書き込む事故を機械的に修復。
    Pattern 2（既存修正）では独立ステップとして挿入。Pattern 1/3/4 では step_prompter 内で呼ばれる。
    """
    json_path = (state.outputs.get("merged_json")
                 or state.outputs.get("reviewed_json")
                 or state.outputs.get("prompted_json")
                 or state.outputs.get("draft_json", ""))
    if not json_path or not Path(json_path).exists():
        log_info("format_prompt_strings: 対象 JSON なし、スキップ")
        return True
    cmd = ["python3", str(PROJECT_DIR / "scripts" / "format_prompt_strings.py"), json_path]
    code, stdout, stderr = run_cmd(cmd)
    if stderr:
        log_info(stderr.strip().splitlines()[0])
    return True


def step_properties_from_json(state: PipelineState) -> bool:
    """properties_from_json: Pattern 2 用。JSON のインラインプロンプトから properties ファイル生成。
    Pattern 2 は scaffold を走らせず tts_modules リストが無いため、既存 JSON の inline prompt を
    転記して properties を作る。P-010 大量発生を防ぐ。
    """
    json_path = (state.outputs.get("merged_json")
                 or state.outputs.get("reviewed_json")
                 or state.outputs.get("prompted_json")
                 or state.outputs.get("draft_json", "")
                 or state.base_path)
    if not json_path or not Path(json_path).exists():
        log_info("properties_from_json: 対象 JSON なし、スキップ")
        return True

    # 出力は output/scenarios/{施設}_{flow}/properties_{facility}_{flow}.md
    out_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"properties_{state.facility}_{state.flow}.md"
    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "properties_from_json.py"),
        str(json_path),
        "-o", str(out_path),
        "--env", state.environment or "prod",
    ]
    log_info(f"properties_from_json: {Path(json_path).name} → {out_path.name}")
    code, stdout, stderr = run_cmd(cmd)
    if stderr:
        for line in stderr.strip().splitlines():
            log_info(line)
    if out_path.exists():
        state.outputs["properties"] = str(out_path)
        log_ok(f"Properties: {out_path.name}")
    else:
        log_warn("properties_from_json: 出力ファイル生成失敗")

    # Pattern 2: dirlite manifest の Properties Manifest セクションがあれば customer_docs + manifest をマージ
    if state.pattern == 2 and state.dirlite_manifest:
        _merge_pattern2_properties(state, out_path)

    return True  # Properties 失敗はブロッキングしない


def _merge_pattern2_properties(state: "PipelineState", out_path: Path) -> None:
    """Pattern 2: customer_docs/{施設}property.txt + dirlite manifest の Properties Manifest を
    マージして、TODO を実値で上書きする。manifest が無ければ何もしない。
    """
    affects = state.dirlite_manifest.get("affects", []) or []
    if "properties" not in affects:
        log_info("Properties merge: manifest.affects に properties 無し、マージスキップ")
        return

    # customer_docs property.txt を探す
    candidates = [
        PROJECT_DIR / "docs" / "reference" / "customer_docs" / f"{state.facility}property.txt",
        PROJECT_DIR / "docs" / "reference" / "customer_docs" / f"{state.facility}_{state.flow}property.txt",
        PROJECT_DIR / "docs" / "reference" / "customer_docs" / f"{state.facility}_property.txt",
    ]
    base_prop_path = next((p for p in candidates if p.exists()), None)
    if not base_prop_path:
        log_info(f"Properties merge: customer_docs に {state.facility}property.txt 等が無い、マージスキップ")
        return

    try:
        base_text = base_prop_path.read_text(encoding="utf-8", errors="replace")
        current_text = out_path.read_text(encoding="utf-8", errors="replace") if out_path.exists() else ""
    except Exception as e:
        log_warn(f"Properties merge 失敗（読込）: {e}")
        return

    # {モジュール名}.prompt= の行を base から拾い、current の TODO 行を実値に置換
    base_entries: dict[str, str] = {}
    for line in base_text.splitlines():
        m = re.match(r"^([^#\s][^=\s]*)\.prompt=(.*)$", line)
        if m:
            base_entries[m.group(1).strip()] = m.group(2).strip()

    if not base_entries:
        log_info(f"Properties merge: {base_prop_path.name} に .prompt= 行なし、スキップ")
        return

    new_lines: list[str] = []
    replaced = 0
    for line in current_text.splitlines():
        m = re.match(r"^([^#\s][^=\s]*)\.prompt=(.*)$", line)
        if m:
            key = m.group(1).strip()
            cur_val = m.group(2).strip()
            if key in base_entries and "TODO_" in cur_val:
                new_lines.append(f"{key}.prompt={base_entries[key]}")
                replaced += 1
                continue
        new_lines.append(line)

    # Properties Manifest セクション (manifest.sections.properties) から追加プロパティを反映。
    # `.prompt=` のみではなく、Phone2Name の `.FOUND_KATAKANA_NAME_DEFAULT_TMP=` 等の
    # 任意の `{module}.{field}=value` 形式の bullet 行も拾う。value は verbatim copy
    # （`{tts_g:}` ラッパーや `<% %>` を勝手に付与しない）。
    manifest_props = state.dirlite_manifest.get("sections", {}).get("properties", "")
    added_from_manifest = 0
    # 既存 property 行から key を抽出（一般的な `key=value` 形式）
    def _extract_key(text_line: str) -> str:
        s = text_line.strip()
        if not s or s.startswith("#") or "=" not in s:
            return ""
        k = s.split("=", 1)[0].strip()
        return k if re.match(r"^[\w\.\-]+$", k) else ""
    existing_keys = {_extract_key(nl) for nl in new_lines}
    existing_keys.discard("")

    for line in manifest_props.splitlines():
        # bullet/箇条書きの装飾を剥がす
        stripped = line.strip().lstrip("-*` \t")
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, val = stripped.partition("=")
        key = key.strip().rstrip("`")  # 末尾 backtick も剥がす
        val = val.strip().rstrip("`")
        # key が識別子っぽい (英数字 + . + _ + - で構成) かチェック
        if not re.match(r"^[\w\.\-]+$", key):
            continue
        if key in existing_keys:
            continue
        new_lines.append(f"{key}={val}")
        existing_keys.add(key)
        added_from_manifest += 1

    if replaced > 0 or added_from_manifest > 0:
        try:
            out_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
            log_ok(f"Properties merge: {base_prop_path.name} から {replaced} 件置換、manifest から {added_from_manifest} 件追加")
        except Exception as e:
            log_warn(f"Properties merge 失敗（書込）: {e}")
    else:
        log_info("Properties merge: 置換対象なし")


def step_auto_fixer(state: PipelineState) -> bool:
    """auto_fixer: validator の json レポートから fix_category=auto の Issue を機械的に修正する。
    LLM を一切使わず決定論的に処理するため、高速 + トークン消費ゼロ。
    LAYOUT 再計算が必要な場合は layout_calculator.py を呼び直す。
    """
    json_report = state.outputs.get("validator_json_report", "")
    json_path = (state.outputs.get("merged_json")
                 or state.outputs.get("reviewed_json")
                 or state.outputs.get("prompted_json", ""))
    spec = state.outputs.get("design_spec", state.spec_path)

    if not json_report or not Path(json_report).exists():
        log_info("auto_fixer: JSON レポートが無いためスキップ")
        return True
    if not json_path or not Path(json_path).exists():
        log_warn(f"auto_fixer: 対象 JSON が無い ({json_path})")
        return True

    # レポートから auto 件数を事前カウント
    try:
        with open(json_report, encoding="utf-8") as f:
            rep = json.load(f)
        auto_count = sum(1 for i in rep.get("issues", []) if i.get("fix_category") == "auto")
    except Exception:
        auto_count = 0

    if auto_count == 0:
        log_info("auto_fixer: auto カテゴリの Issue なし、スキップ")
        return True

    log_info(f"auto_fixer: {auto_count} 件の自動修正を適用")
    cmd = ["python3", "scripts/auto_fixer.py",
           "--json", json_path,
           "--report", json_report]
    if spec and str(spec).endswith(".yaml"):
        cmd.extend(["--spec", str(spec)])

    code, stdout, stderr = run_cmd(cmd, timeout=VALIDATOR_TIMEOUT)
    # stderr に詳細ログが載る
    if stderr:
        for line in stderr.strip().splitlines():
            log_info(line)

    if code == 0:
        log_ok(f"auto_fixer 完了（{auto_count} 件処理）")
        return True
    log_warn(f"auto_fixer 失敗 (exit={code}): {stderr[:200]}")
    return True  # 失敗してもパイプラインは継続（fixer が後で拾う）


def _list_prompter_targets(state: PipelineState) -> list[dict]:
    """設計書から prompter LLM が処理すべき OpenAI モジュールを列挙する。
    Yes/No（復唱確認）は scaffold が固定プロンプトを埋め込み済みのため除外。
    サブフローのプロンプトもリファレンスからコピー済みのため除外。
    range_values も抽出して渡すことで prompter 側の JSON/設計書 Read を排除する。
    """
    spec_path = state.outputs.get("design_spec", state.spec_path)
    if not spec_path or not str(spec_path).endswith(".yaml"):
        return []
    try:
        import yaml
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except Exception:
        return []

    scenario_flow = spec.get("scenario_flow", [])
    # hearing_items は director (Pattern 1/3/4) では "name" キー、scaffold_extractor 逆走 (Pattern 2) では "step_name" キー
    # どちらでも動くように両方で index を張る
    hearing_index = {}
    for h in spec.get("hearing_items", []) or []:
        if not h:
            continue
        key = h.get("name") or h.get("step_name")
        if key:
            hearing_index[key] = h
    step_index = {s["step_name"]: s for s in spec.get("step_details", []) if s and s.get("step_name")}
    # context_fields をコンテキスト名でインデックス化（range_values 取得用）
    ctx_index = {
        c["context_name"]: c
        for c in spec.get("context_fields", [])
        if isinstance(c, dict) and c.get("context_name")
    }

    targets = []
    for block in scenario_flow:
        if block.get("type") != "hearing":
            continue
        if block.get("unreachable"):
            continue  # 到達不能ブロックは refresh 対象外（scaffold_extractor TTS-first 時の unreachable フラグ）
        output_format = block.get("output_format", "text")
        if output_format == "text":
            continue  # OpenAI なし

        step = block["step"]
        h_item = hearing_index.get(step) or hearing_index.get(step.rsplit("_", 1)[0], {})
        step_detail = step_index.get(step) or step_index.get(step.rsplit("_", 1)[0], {})

        processing = h_item.get("openai_processing", "classify")
        save_to = h_item.get("save_to", "")
        ctx_field = ctx_index.get(save_to, {})

        targets.append({
            "module_name": f"OpenAI_{step}",
            "step_name": step,
            "processing": processing,
            "output_format": output_format,
            "tts_announcement": step_detail.get("tts_announcement", ""),
            "output_labels": h_item.get("output_labels", []),
            "openai_rules": step_detail.get("openai_rules", {}),
            "stt_type": h_item.get("stt_type", "AmiVoice_STT"),
            "save_to": save_to,
            "range_values": ctx_field.get("range_values", []),
        })
    return targets


def _inject_and_finalize_prompter(
    state: "PipelineState",
    sidecar_path: Path,
    prompted_path: Path,
) -> None:
    """inject_prompts.py でサイドカー → JSON に注入し state.outputs を更新する。"""
    inj_cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "inject_prompts.py"),
        str(sidecar_path),
        str(prompted_path),
    ]
    inj_code, _inj_out, inj_err = run_cmd(inj_cmd)
    if inj_code == 0:
        log_ok(inj_err.strip().splitlines()[0] if inj_err.strip() else "inject_prompts: 完了")
    elif inj_code == 2:
        log_warn(f"inject_prompts 部分成功: {inj_err.strip()}")
    else:
        log_warn(f"inject_prompts 失敗 (exit={inj_code}): {inj_err[:300]}")

    if prompted_path.exists():
        state.outputs["prompted_json"] = str(prompted_path)
        log_ok(f"Prompted: {prompted_path.name}")
    else:
        found = sorted(
            (PROJECT_DIR / "output" / "json").glob(f"prompted_{state.facility}*"),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        if found:
            state.outputs["prompted_json"] = str(found[0])
            log_ok(f"Prompted (fallback): {found[0].name}")
        else:
            log_warn("Prompted JSON が見つかりません（draft JSON で続行）")


def step_prompter(state: PipelineState) -> bool:
    """Prompter: OpenAIプロンプトをサイドカーMDに書き出し、inject_prompts.py でJSONに注入する。

    【優先順位】
    1. gen_prompts.py（決定論スクリプト）でテンプレート充填を試みる（LLM 不使用）
    2. exit=0 → 全モジュール解決 → LLM 呼び出しなし
    3. exit=2 → 一部未解決 → フォールバック対象のみ LLM(prompter) に渡す
    4. 設計書なし等の旧来フロー → 従来通り LLM(prompter) で全量処理

    JSONへのEditは不要。inject_prompts.pyがjson.dumpsで正しくエンコードして注入する。
    """
    draft = state.outputs.get("draft_json", "")

    # 対象モジュール列挙（設計書から全情報を抽出済み）
    targets = _list_prompter_targets(state)
    prompted_path = PROJECT_DIR / "output" / "json" / f"prompted_{state.facility}_{state.flow}.json"
    # サイドカー（プロンプター中間成果物）は scenarios/{施設}/ 配下に置く
    sidecar_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = sidecar_dir / f"prompts_{state.facility}_{state.flow}.md"

    if not targets:
        log_info("Prompter: 対象 OpenAI モジュールなし（全て scaffold で解決済み）")
        shutil.copy2(draft, str(prompted_path))
        state.outputs["prompted_json"] = str(prompted_path)
        return True

    # --- Step A: draft → prompted にコピー（inject_prompts.py の注入先として使用） ---
    shutil.copy2(draft, str(prompted_path))

    # -----------------------------------------------------------------------
    # Step A-1: gen_prompts.py で決定論的テンプレート充填を試みる（LLM 不使用）
    # -----------------------------------------------------------------------
    spec_path = state.outputs.get("design_spec", state.spec_path)
    gen_prompts_script = PROJECT_DIR / "scripts" / "gen_prompts.py"
    fallback_modules: list[str] = []

    if spec_path and str(spec_path).endswith(".yaml") and gen_prompts_script.exists():
        log_info(f"gen_prompts.py: {len(targets)} 件を決定論的に生成中（LLM 不使用）")
        gp_cmd = [
            sys.executable, str(gen_prompts_script),
            "--spec", str(spec_path),
            "--output", str(sidecar_path),
        ]
        gp_code, _gp_out, gp_err = run_cmd(gp_cmd, timeout=60)

        for line in gp_err.strip().splitlines():
            if line.startswith("OK"):
                log_ok(line)
            elif line.startswith("WARN") or line.startswith("FALLBACK"):
                log_warn(line)
            else:
                log_info(line)

        if gp_code == 0:
            # 全モジュールを決定論的に解決 → LLM スキップ
            log_ok(f"gen_prompts: 全 {len(targets)} 件を LLM なしで生成完了")
            state.outputs["prompter_sidecar"] = str(sidecar_path)
            # inject → prompted_json
            _inject_and_finalize_prompter(state, sidecar_path, prompted_path)
            return True

        elif gp_code == 2:
            # 一部未解決 → FALLBACK 対象を LLM に渡す
            for line in gp_err.strip().splitlines():
                if line.startswith("FALLBACK:"):
                    # "FALLBACK: N 件は LLM(prompter) でのフォールバック推奨: ModA, ModB"
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        fallback_modules = [m.strip() for m in parts[2].split(",") if m.strip()]
            resolved = len(targets) - len(fallback_modules)
            log_info(
                f"gen_prompts: {resolved}/{len(targets)} 件を決定論的に解決。"
                f" {len(fallback_modules)} 件を LLM(prompter) にフォールバック: "
                + ", ".join(fallback_modules)
            )
        else:
            log_warn(f"gen_prompts.py 失敗 (exit={gp_code}) → LLM(prompter) で全量処理")
    else:
        log_info("gen_prompts.py: 設計書 YAML なし → LLM(prompter) で全量処理")

    # -----------------------------------------------------------------------
    # Step A-2: LLM(prompter) で残りのモジュールを処理
    # -----------------------------------------------------------------------
    # LLM に渡す対象: fallback_modules に絞る（一部解決済みの場合）
    llm_targets = targets if not fallback_modules else [
        t for t in targets if t["module_name"] in fallback_modules
    ]
    log_info(f"Prompter(LLM): {len(llm_targets)} モジュールのプロンプトをサイドカーへ書き出し")

    # LLM 書き出し先を prompt 構築前に確定する（Bug-fix: 後で変えると prompt と不一致）
    llm_sidecar_path = sidecar_path
    if fallback_modules and sidecar_path.exists():
        llm_sidecar_path = sidecar_path.with_suffix(".llm.md")

    # --- Step B: 必要な SKILL テンプレートを orchestrator で読み込んで埋め込む ---
    SKILL_FILE_MAP = {
        "classify":  "SKILL_A_classification",
        "judge":     "SKILL_B_yes_no",
        "convert":   "SKILL_C_date",
        "normalize": "SKILL_D_normalization",
        "summarize": "SKILL_E_freetext",
    }
    SKILL_LABEL = {
        "classify":  "SKILL_A（分類型・N択判定）",
        "judge":     "SKILL_B（はい/いいえ判定型）",
        "convert":   "SKILL_C（日付変換型）",
        "normalize": "SKILL_D（正規化型・リスト照合）",
        "summarize": "SKILL_E（自由テキスト型）",
    }
    skill_dir = PROJECT_DIR / "docs" / "ai" / "skills"
    needed_skills = {SKILL_FILE_MAP.get(t["processing"], "SKILL_A_classification") for t in llm_targets}
    skill_texts: dict[str, str] = {}
    for sk in needed_skills:
        candidates = list(skill_dir.glob(f"{sk}*.md"))
        if candidates:
            skill_texts[sk] = candidates[0].read_text(encoding="utf-8")

    skill_section = ""
    for sk, content in skill_texts.items():
        skill_section += f"\n\n---\n## テンプレート: {sk}\n\n{content}"

    # --- Step C: モジュール別指示を組み立て ---
    # CONTRACT ブロック（4 層責任モデル: prompter↔CMR/script 等の整合保証用メタ情報）を構築
    contracts = _build_prompter_contracts(draft, llm_targets)

    module_instructions = []
    for t in llm_targets:
        labels = ", ".join(t["output_labels"]) if t["output_labels"] else "（なし）"
        rules = t.get("openai_rules", {})
        mapping_str = ""
        if rules.get("mapping"):
            mapping_str = "\n  マッピング:\n" + "\n".join(
                f"    - {m.get('input', '')} → {m.get('output', '')}"
                for m in rules["mapping"]
            )
        rv = t.get("range_values", [])
        range_str = ""
        if rv:
            range_str = "\n  range_values:\n" + "\n".join(
                f"    - id={r.get('id', '')} value={r.get('value', '')}"
                for r in rv if isinstance(r, dict)
            )

        # CONTRACT ブロック（あれば）
        contract = contracts.get(t["module_name"])
        contract_block = f"\n\n  CONTRACT:\n```\n{_format_contract_block(contract)}\n```" if contract else ""

        module_instructions.append(
            f"### {t['module_name']}\n"
            f"- パターン: {SKILL_LABEL.get(t['processing'], t['processing'])}\n"
            f"- TTS文言: 「{t['tts_announcement']}」\n"
            f"- 出力ラベル: {labels}\n"
            f"- STT種別: {t['stt_type']}\n"
            f"- 保存先: {t['save_to']}"
            f"{mapping_str}{range_str}"
            f"{contract_block}"
        )

    module_block = "\n\n".join(module_instructions)

    prompt = (
        f"以下の {len(llm_targets)} 件の OpenAI モジュールのプロンプトを記述し、"
        f"サイドカーファイルに書き出してください。\n"
        f"必要な情報は全てこのプロンプトに含まれています。\n\n"
        f"**書き出し先サイドカーファイル**: {llm_sidecar_path}\n\n"
        f"> **フローJSON・設計書・SKILL_*.md ファイルの Read は不要です。**\n"
        f"> Write ツールで {llm_sidecar_path} に全モジュールのプロンプトをまとめて書き出してください。\n"
        f"> JSONファイルへの Edit は一切不要です（inject_prompts.py が自動で注入します）。\n\n"
        f"## サイドカーファイルの書式\n\n"
        f"```\n"
        f"## モジュール名（例: OpenAI_診療科）\n"
        f"# Role\n"
        f"あなたは...\n\n"
        f"---\n\n"
        f"# Context（重要）\n"
        f"...\n\n"
        f"## 次のモジュール名\n"
        f"# Role\n"
        f"...\n"
        f"```\n\n"
        f"- `## モジュール名` がセクション区切り（モジュール名は下記対象一覧の通り）\n"
        f"- セクション内はプロンプト本文をそのまま記述（JSON エスケープ不要）\n"
        f"- 改行は実改行で書く（`\\n` リテラル禁止）\n"
        f"- Write ツール 1 回で全モジュール分を一括書き出し\n\n"
        f"## 対象モジュール（{len(llm_targets)}件）\n\n"
        f"{module_block}\n\n"
        f"## 作業ルール\n"
        f"- 下記テンプレートのプレースホルダーを対象モジュールの情報で埋めること\n"
        f"- next / subs / contextName 等への言及は不要（プロンプト本文のみ記述）\n"
        f"- **各モジュールの `CONTRACT:` ブロックがあれば必ず先に読む**。`docs/ai/skills/SKILL_CONTRACT.md` の "
        f"ハードルール（forbidden_in_context のリテラル禁止 / abstract_context をベースに / "
        f"downstream_references で出力厳格化）を必ず適用する\n"
        f"- CONTRACT ブロック自体はサイドカー本文に書かない（OpenAI に渡すのはプロンプト本文のみ、"
        f"orchestrator のメタ情報なので消費するだけで貼り付けない）\n"
        f"{skill_section}"
    )

    code, stdout, stderr, _ = invoke_agent("prompter", prompt)

    # exit code とサイドカー実在を厳格チェック（B 案）。
    # prompter が空欄プロンプトを残したまま後段に流れると、validator が大量の
    # PROMPT-003 Critical を出し、fixer がそれを直そうとして詰まる。
    # invoke_agent 内で FileNotFoundError は 3 回リトライ済なので追加リトライは不要。
    if code != 0 or not llm_sidecar_path.exists():
        # フォールバック: LLM が llm_sidecar_path ではなく sidecar_path に書いた可能性
        if not llm_sidecar_path.exists() and sidecar_path.exists():
            pass  # sidecar_path に直接書いた → そのまま続行
        else:
            msg = (
                f"prompter failed (exit={code}, sidecar_exists={llm_sidecar_path.exists()}): "
                f"{stderr[:200]}"
            )
            state.errors.append(msg)
            log_error(msg)
            return False

    # gen_prompts（script）と LLM の出力を sidecar_path にマージ
    if fallback_modules and llm_sidecar_path != sidecar_path and llm_sidecar_path.exists():
        script_content = sidecar_path.read_text(encoding="utf-8") if sidecar_path.exists() else ""
        llm_content = llm_sidecar_path.read_text(encoding="utf-8")
        merged = (script_content.rstrip() + "\n\n" + llm_content.strip()) if script_content else llm_content
        sidecar_path.write_text(merged, encoding="utf-8")
        llm_sidecar_path.unlink(missing_ok=True)
        log_info("gen_prompts + LLM サイドカーをマージ完了")

    # --- Step D: inject_prompts.py でサイドカー → JSON に注入 ---
    state.outputs["prompter_sidecar"] = str(sidecar_path)
    _inject_and_finalize_prompter(state, sidecar_path, prompted_path)
    return True


def step_reviewer(state: PipelineState) -> bool:
    """[退役 2026-06-24] reviewer（in-line レッドチーム校閲）は keystone（テスト完了までライン内 LLM ゼロ）により退役。
    PIPELINE_STEPS から除去済み。校閲は壁打ち時に人間+Claude が out-of-line で実施する
    （知見: docs/ai/skills/SKILL_redteam_review.md・旧定義: .claude/agents/archive/reviewer.md）。
    本体は stray 呼出 / --resume 互換のための退役 no-op（以降の旧ロジックは未到達・別PRで掃除）。"""
    log_info("step_reviewer は退役（keystone: ライン内 LLM ゼロ）。レッドチーム校閲は壁打ち時に out-of-line で実施（SKILL_redteam_review.md）。")
    return True
    # ── 以下は旧 reviewer ロジック（未到達・別PRで掃除予定）──
    sidecar_path = state.outputs.get("prompter_sidecar", "")
    spec = state.outputs.get("design_spec", state.spec_path)

    if not sidecar_path or not Path(sidecar_path).exists():
        log_warn("サイドカーMDが見つかりません — reviewer スキップ")
        return True

    prompt = (
        f"以下のプロンプトサイドカーMDをレッドチーム校閲してください。\n"
        f"サイドカーMD（OpenAIプロンプト全文）: {sidecar_path}\n"
        f"設計書（hearing_items / step_details 参照用）: {spec}\n\n"
        f"チェック観点:\n"
        f"  1. 攻撃耐性: プロンプトインジェクション・役割反転・複合意図への耐性\n"
        f"  2. 分岐判断の正確性: 出力値が設計書の conditions と一致しているか\n"
        f"  3. 出力の安全性: 意図しない長文・オウム返し・制約違反がないか\n\n"
        f"JSON全文の Read は不要です。サイドカーMDに全プロンプトが集約されています。"
    )
    code, stdout, stderr, _ = invoke_agent("reviewer", prompt)
    if code != 0:
        log_error("Reviewer 失敗")
        return False

    # レビューレポートの場所を記録（reviewer は JSON を修正しない）
    report = PROJECT_DIR / "output" / "reports" / f"review_report_{state.facility}_{state.flow}.md"
    if report.exists():
        state.outputs["review_report"] = str(report)
        log_ok(f"Review report: {report.name}")
    else:
        reports = sorted(
            (PROJECT_DIR / "output" / "reports").glob("review_report_*.md"),
            key=lambda p: p.stat().st_mtime, reverse=True,
        )
        if reports:
            state.outputs["review_report"] = str(reports[0])
            log_ok(f"Review report: {reports[0].name}")
        else:
            log_warn("校閲レポートが見つかりません")

    # reviewed_json は reviewer が出力する場合のみ。通常は merged_json を引き継ぐ
    reviewed = sorted(
        (PROJECT_DIR / "output" / "json").glob(f"reviewed_{state.facility}*"),
        key=lambda p: p.stat().st_mtime, reverse=True,
    )
    if reviewed:
        state.outputs["reviewed_json"] = str(reviewed[0])
        log_ok(f"Reviewed JSON: {reviewed[0].name}")
    else:
        # reviewer はサイドカーMD方式のため JSON を出力しない → merged_json を引き継ぐ
        fallback = state.outputs.get("merged_json") or state.outputs.get("prompted_json") or ""
        state.outputs["reviewed_json"] = fallback
        if fallback:
            log_info(f"Reviewed JSON なし → merged_json を引き継ぎ: {Path(fallback).name}")

    return True


def _extract_module_names_from_text(text: str) -> set[str]:
    """レポートテキストからモジュール名を抽出（複数のパターンに対応）"""
    names: set[str] = set()
    # パターン1: "[Critical/Warning] CODE モジュール名 > field: msg"
    for m in re.finditer(r"\[(?:Critical|Warning|CRITICAL|WARNING)\][^\n]*?\b([A-Z]+-\d+)\b\s+([^\s>:]+)", text):
        names.add(m.group(2))
    # パターン2: "[C/W/I] [CODE] モジュール名 > ..."
    for m in re.finditer(r"\[[CWI]\]\s+\[[A-Z]+-\d+\]\s+([^\s>:]+)\s*>", text):
        names.add(m.group(1))
    # パターン3: reviewer 形式 "**モジュール名**: \`xxx\`" or "モジュール名: `xxx`"
    for m in re.finditer(r"モジュール(?:名)?[:：]\s*[`'\"]?([^\s`'\"]+)[`'\"]?", text):
        names.add(m.group(1))
    # パターン4: "### C-001: ... 'モジュール名'"
    for m in re.finditer(r"###\s+[A-Z]+-\d+:.*?[`'\"]([^`'\"]+)[`'\"]", text):
        names.add(m.group(1))
    return {n for n in names if n and not n.startswith("(")}


def _group_reports_by_block(
    reports: dict[str, str],
    yaml_path: str,
    validator_json_report: str = "",
) -> dict[str, dict[str, list[str]]]:
    """全レポートをブロック単位にグルーピング。
    返り値: {block_name: {report_source: [matching_lines]}}

    validator については --yaml 付き実行でblock_nameが埋め込まれたJSONレポートを
    直接読み込む（テキスト解析不要）。reviewer / tester はテキスト解析を継続。
    """
    try:
        from block_mapper import build_module_to_block_map, build_block_type_map
    except ImportError:
        sys.path.insert(0, str(PROJECT_DIR / "scripts"))
        from block_mapper import build_module_to_block_map, build_block_type_map

    if not yaml_path or not Path(yaml_path).exists():
        return {}

    mod_to_block = build_module_to_block_map(yaml_path)
    grouped: dict[str, dict[str, list[str]]] = {}

    # ── validator: JSON レポートから直接読み込み（テキスト解析廃止）──
    _val_text_for_fallback = reports.get("validator", "")
    if validator_json_report and Path(validator_json_report).exists():
        try:
            with open(validator_json_report, encoding="utf-8") as _f:
                _val_json = json.load(_f)
            for _issue in _val_json.get("issues", []):
                # prompter / properties 担当は fixer に渡さない
                if _issue.get("fix_category") in ("prompter", "properties", "human", "auto"):
                    continue
                blk = _issue.get("block_name", "")
                if not blk:
                    # block_name が空の場合はモジュール名で逆引き
                    blk = mod_to_block.get(_issue.get("module", ""), "_unmapped")
                if blk and blk != "_unmapped":
                    # 表示用の行文字列を組み立て（fixer が読むレポートに含める）
                    sev   = _issue.get("severity", "")
                    code  = _issue.get("code", "")
                    mod   = _issue.get("module", "")
                    fld   = _issue.get("field", "")
                    msg   = _issue.get("message", "")
                    icon  = {"CRITICAL": "[C]", "WARNING": "[W]", "INFO": "[I]"}.get(sev, "[?]")
                    line_str = f"{icon} [{code}] {mod} > {fld}: {msg}"
                    grouped.setdefault(blk, {}).setdefault("validator", []).append(line_str)
        except Exception as _e:
            log_warn(f"validator JSON report 読み込み失敗、テキスト解析にフォールバック: {_e}")
            _val_text_for_fallback = reports.get("validator", "")
        else:
            _val_text_for_fallback = ""  # JSON 読み込み成功 → テキスト解析スキップ

    # ── reviewer / tester（およびvalidator JSON失敗時）はテキスト解析 ──
    _ISSUE_KEYWORDS = (
        "[C]", "[W]",                          # validator.py 個別指摘行: [C] [code] / [W] [code]
        "CRITICAL", "Critical", "WARNING", "Warning",
        "[CRITICAL]", "[WARNING]", "[FAIL]",   # tester.py 形式
        "修正担当: fixer", "修正担当:fixer",
        "<fixer>",
    )

    text_sources = {
        "reviewer": reports.get("reviewer", ""),
        "tester":   reports.get("tester", ""),
    }
    if _val_text_for_fallback:
        text_sources["validator"] = _val_text_for_fallback

    for source, text in text_sources.items():
        if not text:
            continue
        for line in text.split("\n"):
            stripped = line.strip()
            # 指摘行のみ対象（キーワードを含まない行はスキップ）
            if not any(kw in stripped for kw in _ISSUE_KEYWORDS):
                continue
            # 修正担当が fixer 以外の指摘は渡さない
            if "<prompter>" in stripped or "<properties>" in stripped or "<human>" in stripped or "<auto>" in stripped:
                continue
            mods_in_line = set()
            for mod_name in mod_to_block:
                if mod_name and mod_name in stripped:
                    mods_in_line.add(mod_name)
            if not mods_in_line:
                continue
            # 完全一致ブロック: 行内の全モジュールが同一ブロックに属する場合のみ配分
            blocks_in_line = {mod_to_block.get(m, "_unmapped") for m in mods_in_line}
            if len(blocks_in_line) == 1:
                blk = next(iter(blocks_in_line))
                grouped.setdefault(blk, {}).setdefault(source, []).append(stripped)

    # opening / termination ブロックは fixer 対象外（scaffold が固定生成するため修正不要）
    try:
        _block_types = build_block_type_map(yaml_path)
        _excluded = {"opening", "termination"}
        excluded_blocks = [blk for blk in grouped if _block_types.get(blk, "") in _excluded]
        for blk in excluded_blocks:
            log_info(f"fixer 対象外（固定ブロック）: {blk} ({_block_types.get(blk, '?')})")
            del grouped[blk]
    except Exception:
        pass  # YAML 読み込み失敗時はフィルタなしで続行

    return grouped


def step_fixer(state: PipelineState) -> bool:
    """[退役 2026-06-24] keystone（ライン内に自律修復 LLM を置かない）により step_fixer を退役。
    PIPELINE_STEPS から除去済み。残存 Critical は人間（壁打ち）が生成器を直して再実行する。
    本体は stray 呼出 / --resume 互換のための退役 no-op（以降の旧ロジックは未到達・別PRで掃除）。
    ※ Pattern 2 の外科的修正 step_fixer_modify は別機構（governance §1-7 surgical patch）で存続。"""
    log_info("step_fixer は退役（keystone: ライン内に自律修復 LLM 不在）。残存 Critical は壁打ちで生成器を直して再実行してください。")
    state.outputs.setdefault("fixer_report", "")
    return True
    # ── 以下は旧 fixer ロジック（未到達・別PRで掃除予定）──

    def _read_report(key: str, fallback_name: str) -> tuple[str, str]:
        """レポートパスとテキストを返す。存在しない場合は ("", "") """
        path = state.outputs.get(key, "")
        if not path:
            path = str(PROJECT_DIR / "output" / "reports" / f"{fallback_name}_{state.facility}_{state.flow}.md")
        p = Path(path)
        return (str(p), p.read_text(encoding="utf-8", errors="replace")) if p.exists() else ("", "")

    val1_path, val1_text   = _read_report("validator_report", "validator_report")
    review_path, rev_text  = _read_report("review_report",    "review_report")
    test_path,  test_text  = _read_report("test_report",      "test_report")

    def _count_reviewer_criticals(text: str) -> int:
        """reviewer (Haiku) のレポート形式に特化した Critical カウント。

        reviewer は以下の形式で Critical を出す（2026-04-21 観察）:
        - サマリ行: `- 重大度別: Critical 3 / Warning 2 / Info 0`
        - 個別行（全角括弧）: `- **指摘内容**（Critical）`
        - 個別行（半角括弧）: `- **指摘内容**(Critical)`
        - 表セル: `| Critical |` / 強調: `**Critical**`

        サマリを優先、無ければ個別マーカーを積算。
        """
        m = re.search(r'Critical\s+(\d+)\s*件|Critical[:\s]\s*(\d+)\s*(?:件|/|\s|$)',
                      text, re.IGNORECASE)
        if m:
            return int(m.group(1) or m.group(2) or 0)
        return (
            text.count("（Critical）")
            + text.count("(Critical)")
            + text.count("**Critical**")
            + text.count("| Critical |")
        )

    def _count_criticals(text: str) -> int:
        # validator.py: サマリ行 "[Critical]: N" から件数を抽出
        m = re.search(r'\[Critical\]:\s*(\d+)', text)
        val_count = int(m.group(1)) if m else 0
        # validator.py: 個別行 "  [C] [CODE]" を直接カウント
        line_count = sum(1 for l in text.splitlines() if l.strip().startswith("[C]"))
        # tester.py: [CRITICAL] 形式
        tester_count = text.count("[CRITICAL]")
        return max(val_count, line_count) + tester_count

    reviewer_critical_count = _count_reviewer_criticals(rev_text)
    total_criticals = (
        _count_criticals(val1_text)
        + reviewer_critical_count
        + _count_criticals(test_text)
    )

    if total_criticals == 0 and not (val1_text or rev_text or test_text):
        log_info("レポートなし — fixer スキップ")
        return True
    if total_criticals == 0:
        log_ok("全レポートにCriticalなし — fixer スキップ")
        return True

    log_warn(f"Critical 合計 {total_criticals} 件検出 — fixer (Sonnet) でブロック単位修正")
    json_path = (state.outputs.get("reviewed_json")
                 or state.outputs.get("merged_json")
                 or state.outputs.get("prompted_json")
                 or state.outputs.get("draft_json", ""))

    # ── ブロック単位にグルーピング ──
    spec_path = state.outputs.get("design_spec", state.spec_path)
    reports_dict = {
        "validator": val1_text,
        "reviewer":  rev_text,
        "tester":    test_text,
    }
    block_groups = _group_reports_by_block(
        reports_dict,
        str(spec_path) if spec_path else "",
        validator_json_report=state.outputs.get("validator_json_report", ""),
    )

    # ── Pattern 2: dirlite が touched したブロックのみに scope 制限 ──
    # 既定では legacy Critical (base に元から存在する未到達モジュール等) は fixer の対象外とする。
    # --clean-legacy を指定すると全ブロックを対象に従来挙動。
    if state.pattern == 2 and not state.clean_legacy and block_groups:
        dirlite_path = state.outputs.get("dirlite_report", "")
        if dirlite_path and Path(dirlite_path).exists():
            try:
                dirlite_text = Path(dirlite_path).read_text(encoding="utf-8", errors="replace")
                # `### ブロック「{name}」(...)` or `### ブロック {name} (...)` から block 名抽出
                touched_blocks: set[str] = set()
                for line in dirlite_text.splitlines():
                    m = re.match(r"^###\s+ブロック[\s「]+([^「」\(（\n]+?)(?:[」\(（\s]|$)", line)
                    if m:
                        touched_blocks.add(m.group(1).strip())
                if touched_blocks:
                    before_count = len(block_groups)
                    had_unmapped = "_unmapped" in block_groups
                    filtered = {
                        b: g for b, g in block_groups.items()
                        if b in touched_blocks  # _unmapped も drop（legacy garbage モジュール経路を遮断）
                    }
                    skipped = before_count - len(filtered)
                    if skipped > 0:
                        legacy_blocks = [b for b in block_groups if b not in touched_blocks and b != "_unmapped"]
                        log_info(
                            f"Pattern 2 scope filter: dirlite touched {len(touched_blocks)} ブロックに限定 — "
                            f"legacy {len(legacy_blocks)} ブロック"
                            + (" + _unmapped" if had_unmapped else "")
                            + f" の Critical は skip"
                        )
                        log_info("  legacy も修正する場合は --clean-legacy を指定")
                        block_groups = filtered
                    else:
                        log_info(f"Pattern 2 scope filter: 全 {before_count} ブロックが dirlite touched 範囲内")
                else:
                    log_warn(
                        "dirlite_report から touched ブロック名を抽出できず — 全 Critical を fixer に流す（後方互換）"
                    )
            except Exception as e:
                log_warn(f"Pattern 2 scope filter 失敗: {e} — 全 Critical を fixer に流す")
        else:
            log_warn("dirlite_report が見つからず scope filter スキップ — 全 Critical を fixer に流す")

    # properties / prompter 担当 Critical の有無を判定
    all_reports_text = val1_text
    _prop_critical_codes = ["P-000", "P-010", "P-016", "P-013", "P-014", "P-020"]
    has_prop_criticals = any(code in all_reports_text for code in _prop_critical_codes)
    props_file = state.outputs.get("properties", "")
    # reviewer の指摘は設計上すべてプロンプト品質に関するもの（構造系は validator が担当）
    # そのため reviewer に Critical が 1 件でもあれば prompter ルートを発動させる
    has_prompt_criticals = (
        reviewer_critical_count > 0
        or bool(re.search(
            r"修正担当.*prompter|担当.*prompter|PROMPT-\d+.*Critical|Critical.*PROMPT-\d+",
            rev_text, re.IGNORECASE,
        ))
        or "<prompter>" in val1_text  # validator.py の PROMPT-xxx Critical を検出
    )

    # ── ブロック単位 fixer 並列ジョブ ──
    fix_results: dict[str, str] = {}

    def _run_block_fixer(block_name: str, source_lines: dict) -> str:
        """1ブロック分の修正を fixer に依頼"""
        report_text = []
        for source, lines in source_lines.items():
            if not lines:
                continue
            report_text.append(f"--- {source} ---")
            report_text.extend(lines if isinstance(lines, list) else [str(lines)])
            report_text.append("")
        report_summary = "\n".join(report_text)

        try:
            sys.path.insert(0, str(PROJECT_DIR / "scripts"))
            from block_mapper import build_module_to_block_map
            mod_to_block = build_module_to_block_map(str(spec_path)) if spec_path else {}
            block_modules = sorted(m for m, b in mod_to_block.items() if b == block_name)
        except Exception:
            block_modules = []

        block_modules_str = ", ".join(block_modules) if block_modules else "（モジュール一覧取得失敗）"

        prompt = (
            f"【ブロック単位修正タスク】\n"
            f"対象ブロック: {block_name}\n"
            f"修正対象JSON: {json_path}\n\n"
            f"このブロックに属するモジュール:\n{block_modules_str}\n\n"
            f"このブロックに対する Critical/Warning 指摘:\n{report_summary}\n\n"
            f"【厳守事項】\n"
            f"1. 上記モジュールの params のみ Edit ツールで修正すること\n"
            f"2. 他のブロックのモジュールには絶対に触らないこと\n"
            f"3. next/subs の接続構造は変更しないこと（scaffold が保証済み）\n"
            f"4. 「修正担当: prompter」「修正担当: properties」と記載された指摘はスキップ\n"
            f"5. 修正完了後「ブロック {block_name}: 修正完了」と報告すること"
        )

        code, stdout, stderr, _ = invoke_agent("fixer", prompt)
        if code != 0:
            return f"ブロック {block_name}: 修正失敗 ({stderr[:100]})"
        return f"ブロック {block_name}:\n{stdout[:500]}"

    if block_groups:
        log_info(f"修正対象ブロック数: {len(block_groups)} — 並列実行（最大3）")
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_run_block_fixer, blk, sources): blk
                for blk, sources in block_groups.items()
                if blk != "_unmapped"
            }
            for future in as_completed(futures):
                blk = futures[future]
                try:
                    fix_results[blk] = future.result()
                    log_ok(f"  ✓ {blk} 修正完了")
                except Exception as e:
                    fix_results[blk] = f"ブロック {blk}: 例外 {e}"
                    log_error(f"  ✗ {blk} 例外: {e}")

        if "_unmapped" in block_groups:
            log_info("_unmapped 指摘 — 単独 fixer で対応")
            fix_results["_unmapped"] = _run_block_fixer("_unmapped", block_groups["_unmapped"])
    else:
        log_warn("ブロック単位グルーピング失敗 — 全レポートを単一 fixer で処理")
        fix_results["_全体"] = _run_block_fixer("_全体", {"all": [val1_text, rev_text, test_text]})

    fix_stdout = "\n\n".join(fix_results.values())
    fix_code = 0  # 個別失敗は許容（パイプライン全体の継続のため）

    # --- properties: properties系 Critical を修正（P-010/P-016等が検出された場合のみ） ---
    # gen_properties.py で再生成するのが最も確実（LLM 修正より正確）
    prop_code = -1
    prop_stdout = ""
    if has_prop_criticals and props_file:
        log_info("properties系Critical検出（P-010/P-016等）— gen_properties.py で再生成")
        spec = state.outputs.get("design_spec", state.spec_path)
        if spec:
            regen_cmd = [
                sys.executable,
                str(PROJECT_DIR / "scripts" / "gen_properties.py"),
                str(spec),
                "--env", "demo",
            ]
            regen_result = subprocess.run(
                regen_cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace",
                timeout=SCRIPT_TIMEOUT,
            )
            prop_code = regen_result.returncode
            prop_stdout = regen_result.stdout
            if regen_result.returncode == 0:
                log_ok("properties 再生成完了（P-010/P-016 対応）")
            else:
                log_warn(f"properties 再生成失敗: {regen_result.stderr[:100]}")
                prop_stdout = f"（properties再生成失敗: {regen_result.stderr[:200]}）"

    # --- prompter: プロンプト品質系 Critical を修正（該当する場合のみ） ---
    p_code = -1
    p_stdout = ""
    if has_prompt_criticals:
        log_info("プロンプト系Critical検出 — サイドカー方式で修正")
        spec = state.outputs.get("design_spec", state.spec_path)
        sidecar_path = state.outputs.get("prompter_sidecar", "")

        # Step 1: PROMPT-003（注入失敗）はサイドカーが既存ならinject_prompts.pyで再注入して解消
        if sidecar_path and Path(sidecar_path).exists() and json_path:
            log_info("inject_prompts.py 再実行（PROMPT-003 注入漏れ対応）")
            inject_cmd = [
                sys.executable,
                str(PROJECT_DIR / "scripts" / "inject_prompts.py"),
                sidecar_path,
                json_path,
            ]
            inject_result = subprocess.run(
                inject_cmd, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=SCRIPT_TIMEOUT,
            )
            if inject_result.returncode in (0, 2):  # 0=全件成功 / 2=部分成功
                log_ok(f"inject_prompts 再注入: {inject_result.stderr.strip()}")
                p_code = 0
                p_stdout = inject_result.stderr.strip()
            else:
                log_warn(f"inject_prompts 再注入失敗: {inject_result.stderr[:100]}")

        # Step 2: プロンプト品質 Critical は prompter（サイドカー方式）で修正
        # 対象: PROMPT-001/002/004（validator 構造コード） + reviewer の semantic Critical 全て
        # reviewer の指摘は設計上すべてプロンプト品質（「要改善点」等の semantic 指摘）であり、
        # 構造系は validator で別途検出される。reviewer Critical は無条件で prompter に渡す。
        quality_issues = (
            bool(re.search(r"PROMPT-00[124]", val1_text + rev_text))
            or reviewer_critical_count > 0
        )
        if quality_issues:
            trigger = []
            if re.search(r"PROMPT-00[124]", val1_text + rev_text):
                trigger.append("validator PROMPT-001/002/004")
            if reviewer_critical_count > 0:
                trigger.append(f"reviewer Critical {reviewer_critical_count}件")
            log_info(f"プロンプト品質Critical検出（{' + '.join(trigger)}）— prompter(サイドカー)で修正")
            prompt_fix_prompt = (
                f"校閲レポート/バリデータレポートにプロンプト品質の Critical 指摘があります。\n"
                f"reviewer の指摘は設計上すべて prompter が修正対象です（構造系は validator / fixer が別途担当）。\n"
                f"サイドカーMD を更新してください。\n\n"
                f"サイドカーMD: {sidecar_path}\n"
                f"設計書: {spec}\n"
                f"バリデータレポート: {val1_path}\n"
                f"校閲レポート: {review_path}\n\n"
                f"修正方針:\n"
                f"  1. サイドカーMD（{sidecar_path}）の該当モジュールのセクションのみ Edit で修正\n"
                f"  2. ## セクション見出し（モジュール名）は変更しないこと\n"
                f"  3. validator の PROMPT-001/002/004 系（出力ラベル不一致・NO_RESULT 欠落・インジェクション対策欠落等）は必ず対応\n"
                f"  4. reviewer の Critical 指摘（要改善点／複合意図／曖昧出力仕様等の semantic 指摘）も該当セクションに反映\n"
                f"  5. 絶対ルール（Few-Shot は SKILL_C のみ採用、他では書かない等、prompter.md 参照）は遵守\n"
                f"  6. 修正完了後「プロンプト品質修正完了」と報告"
            )
            pq_code, pq_out, pq_err, _ = invoke_agent("prompter", prompt_fix_prompt)
            if pq_code == 0:
                # サイドカー更新後に inject_prompts.py で JSON に反映
                inject_cmd = [
                    sys.executable,
                    str(PROJECT_DIR / "scripts" / "inject_prompts.py"),
                    sidecar_path,
                    json_path,
                ]
                subprocess.run(inject_cmd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=SCRIPT_TIMEOUT)
                log_ok("サイドカー修正 + 再注入完了")
                p_code = 0
                p_stdout = pq_out[:500]
            else:
                log_warn(f"prompter修正失敗: {pq_err[:100]}")
                p_stdout = f"（prompter実行失敗: {pq_err[:200]}）"

    # 修正後に .bivr を再ビルド
    if fix_code == 0 or (has_prompt_criticals and p_code == 0):
        log_info("fixer修正完了 — .bivr 再ビルド")
        step_parallel_tester_build(state)
        step_collect_scenario(state)

    # 整合性チェックは auto_fixer 内蔵の validator で実施済み
    # （ここでは ad-hoc 検証は行わない）

    # ── 修正レポートをシナリオフォルダ直下に出力 ──────────────────────
    _write_fixer_report(
        state=state,
        json_path=json_path,
        val_count=_count_criticals(val1_text),
        rev_count=_count_criticals(rev_text),
        test_count=_count_criticals(test_text),
        total_criticals=total_criticals,
        fix_stdout=fix_stdout,
        p_stdout=p_stdout,
        has_prompt_criticals=has_prompt_criticals,
        final_val_out="（fixer後の整合性チェックは auto_fixer 内蔵の validator で実施済み）",
        rev_text=rev_text,
    )

    return True


def step_auto_fixer_post_test(state: PipelineState) -> bool:
    """テスター後の auto_fixer パス: validator を再実行して fresh JSON report を取得し、
    機械的に修正できる Issue（fix_category=auto）を適用する。
    テスターが Critical を検出した場合に決定論的にクリアする（残存は人間壁打ちへ・step_fixer 退役）。
    """
    json_path = (state.outputs.get("merged_json")
                 or state.outputs.get("modified_json")
                 or state.outputs.get("reviewed_json")
                 or state.outputs.get("prompted_json", ""))
    if not json_path or not Path(json_path).exists():
        log_info("auto_fixer_post_test: 対象 JSON なし、スキップ")
        return True

    log_info("auto_fixer_post_test: Validator 再実行 → fresh report 生成")
    step_validator(state, json_path, report_key="validator_post_test_report")
    return step_auto_fixer(state)


def step_validator_final(state: PipelineState) -> bool:
    """validator_final は廃止。パイプラインのステップ互換性のためスキップで通過する。
    残存 Critical の最終チェックは collect_scenario 前の validator（auto_fixer 内蔵）で十分。
    残存 Critical は人間（壁打ち）が生成器を直して再実行する（step_fixer 退役 2026-06-24）。
    """
    log_info("validator_final: スキップ（廃止済み — auto_fixer 内の validator で代替）")
    return True  # パイプライン継続（commit/approve まで進める）


def _write_fixer_report(
    state: "PipelineState",
    json_path: str,
    val_count: int,
    rev_count: int,
    test_count: int,
    total_criticals: int,
    fix_stdout: str,
    p_stdout: str,
    has_prompt_criticals: bool,
    final_val_out: str,
    rev_text: str,
) -> None:
    """修正レポートをシナリオフォルダ直下に出力する"""
    from datetime import datetime as _dt
    now = _dt.now()
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%Y-%m-%d %H:%M")

    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    scenario_dir.mkdir(parents=True, exist_ok=True)
    report_path = scenario_dir / f"fixer_report_{date_str}.md"

    sections = [
        f"# Fixer修正レポート — {state.facility} {state.flow}",
        f"生成日時: {time_str}\n",
        "## 修正前 Critical サマリー\n",
        "| ソース | Critical 件数 |",
        "|---|---|",
        f"| バリデータ（構造チェック） | {val_count} 件 |",
        f"| レビュアー（レッドチーム校閲） | {rev_count} 件 |",
        f"| テスター（プロンプト品質・ルート到達性） | {test_count} 件 |",
        f"| **合計** | **{total_criticals} 件** |",
        "",
        "## Fixer修正完了内容\n",
        fix_stdout.strip() if fix_stdout.strip() else "_（fixer スキップ — Critical なし）_",
        "",
    ]

    if has_prompt_criticals:
        sections += [
            "## プロンプト品質修正完了内容（prompter担当）\n",
            p_stdout.strip() if p_stdout.strip() else "_（出力なし）_",
            "",
        ]

    # 残存指摘一覧: 最終バリデータ全出力 + レビュアーレポート全文
    final_val_block = final_val_out.strip() if final_val_out.strip() else "_（指摘なし）_"
    rev_block       = rev_text.strip()       if rev_text.strip()       else "_（レポートなし）_"

    sections += [
        "## 残存指摘一覧（要人間確認）\n",
        "### 最終バリデータ結果（Critical / Warning / Info 全件）\n",
        "```",
        final_val_block,
        "```",
        "",
        "### レビュアーレポート（1パスで修正しきれなかった分を含む）\n",
        rev_block,
        "",
        "---",
        f"対象JSON: `{json_path}`",
    ]

    report_path.write_text("\n".join(sections), encoding="utf-8")
    state.outputs["fixer_report"] = str(report_path)
    log_ok(f"修正レポート出力: {report_path.relative_to(PROJECT_DIR)}")


def step_merge(state: PipelineState) -> bool:
    """Merge: prompted_json を merged_json として引き継ぐ（reviewer は merge より後に実行）"""
    final = state.outputs.get("prompted_json") or state.outputs.get("draft_json", "")
    if not final:
        log_error("マージ対象のJSONが見つかりません")
        return False

    state.outputs["merged_json"] = final
    log_ok(f"Merge完了: {Path(final).name}")
    return True


def _parse_mode_header(spec_path: str) -> str:
    """修正指示ファイル先頭の YAML フロントマター風ヘッダから Mode 値を読み取る。

    書式:
        ---
        Mode: Refresh
        ---

    Mode 行が無い、フロントマターが無い、ファイルが読めない場合は "Modify" を返す（既存挙動）。
    """
    if not spec_path or not Path(spec_path).exists():
        return "Modify"
    try:
        with open(spec_path, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return "Modify"

    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return "Modify"
    end_idx = -1
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx == -1:
        return "Modify"

    for line in lines[1:end_idx]:
        m = re.match(r"^\s*Mode\s*:\s*(\S+)\s*$", line)
        if m:
            return m.group(1)
    return "Modify"


def _build_prompter_contracts(draft_json_path: str, targets: list[dict]) -> dict[str, dict]:
    """各 OpenAI モジュールの prompter [CONTRACT] ブロック構築。

    4 層責任モデル (memory: project_4layer_responsibility_model) に基づく。
    詳細仕様: docs/ai/skills/SKILL_CONTRACT.md

    内容:
      - downstream_references: scaffold JSON の参照スキャナー (find_module_references) で抽出
      - forbidden_in_context: tts_announcement 内のリテラル数値例（「4月1日」「0401」等）
      - abstract_context: output_format から推定された抽象記述
      - stt_pre_normalized: 設計書 amivoice_dictionary の use_template から推定（Phase 2）

    Returns:
        {module_name: contract_dict}。スキャン失敗時は空 dict（CONTRACT 注入スキップ）
    """
    contracts: dict[str, dict] = {}
    if not draft_json_path or not Path(draft_json_path).exists():
        return contracts

    try:
        with open(draft_json_path, encoding="utf-8") as f:
            draft = json.load(f)
    except Exception:
        return contracts

    # find_module_references をインポート（schemas/module_graph.py）
    sys.path.insert(0, str(PROJECT_DIR / "schemas"))
    try:
        from module_graph import find_module_references
    except ImportError:
        return contracts

    # tts_announcement からリテラル数値例を抽出する正規表現
    # 例: 「4月1日」「0401」「5月10日のように」等
    _LITERAL_EXAMPLE_RE = re.compile(
        r"(?P<jp>\d{1,2}\s*月\s*\d{1,2}\s*日)"
        r"|(?P<mmdd>(?<![0-9])\d{4}(?![0-9]))"
        r"|(?P<dotdate>(?<![0-9])\d{4}-\d{1,2}-\d{1,2}(?![0-9]))"
    )

    for t in targets:
        mod_name = t.get("module_name", "")
        if not mod_name:
            continue
        contract: dict = {}

        # purpose / output_target
        if t.get("save_to"):
            contract["output_target_field"] = t["save_to"]
        if t.get("output_format"):
            contract["output_target_format"] = t["output_format"]

        # forbidden_in_context — TTS 文言から数字リテラル例を抽出
        tts = t.get("tts_announcement", "") or ""
        forbidden = []
        seen = set()
        for m in _LITERAL_EXAMPLE_RE.finditer(tts):
            val = m.group(0)
            if val not in seen:
                seen.add(val)
                forbidden.append(val)
        if forbidden:
            contract["forbidden_in_context"] = forbidden

        # abstract_context — output_format / save_to から推定
        save_to = t.get("save_to", "") or "回答"
        of = t.get("output_format", "")
        if of == "datetime":
            contract["abstract_context"] = (
                f"直前にユーザーへ {save_to} の入力を依頼した。"
                f"フォーマットは「M月D日」「MMDD 4桁」「YYYY年M月D日」のいずれか。"
            )
        elif of == "enum":
            labels = t.get("output_labels") or []
            label_str = " / ".join(labels) if labels else "（CONTRACT.downstream_references 参照）"
            contract["abstract_context"] = (
                f"直前にユーザーへ {save_to} の入力を依頼した。"
                f"出力ラベル: {label_str}。"
            )
        else:
            contract["abstract_context"] = f"直前にユーザーへ {save_to} の入力を依頼した。"

        # downstream_references — 汎用スキャナーで参照箇所抽出
        try:
            refs = find_module_references(draft, mod_name)
        except Exception:
            refs = []
        if refs:
            # condition は None になる ref も多いので冗長な None は除く
            cleaned = []
            for r in refs:
                cr = {k: v for k, v in r.items() if v is not None and v != ""}
                cleaned.append(cr)
            contract["downstream_references"] = cleaned

        contracts[mod_name] = contract

    return contracts


def _format_contract_block(contract: dict) -> str:
    """contract dict を [CONTRACT]…[/CONTRACT] テキストに整形（YAML 風）。"""
    lines = ["[CONTRACT]"]
    for key in ("purpose", "output_target_field", "output_target_format"):
        if key in contract:
            lines.append(f"{key}: {contract[key]}")
    if "forbidden_in_context" in contract:
        lines.append("forbidden_in_context:")
        for v in contract["forbidden_in_context"]:
            lines.append(f"  - \"{v}\"")
    if "abstract_context" in contract:
        ac = contract["abstract_context"].rstrip()
        if "\n" in ac:
            lines.append("abstract_context: |")
            for ln in ac.split("\n"):
                lines.append(f"  {ln}")
        else:
            lines.append(f"abstract_context: {ac}")
    if "stt_pre_normalized" in contract:
        lines.append("stt_pre_normalized:")
        for k, v in contract["stt_pre_normalized"].items():
            lines.append(f"  {k}: {v}")
    if "downstream_references" in contract:
        lines.append("downstream_references:")
        for ref in contract["downstream_references"]:
            lines.append(f"  - caller: {ref.get('caller', '')}")
            for k in ("caller_type", "ref_kind", "condition"):
                if k in ref:
                    lines.append(f"    {k}: {ref[k]}")
    lines.append("[/CONTRACT]")
    return "\n".join(lines)


def _extract_existing_openai_prompts(json_path: str) -> dict:
    """既存フローJSON から OpenAI モジュールの params.prompt を {モジュール名: プロンプト本文} 形式で抽出。

    Brekeke のモジュール構造:
        modules: {モジュール名: {type, params: {prompt, ...}, ...}}

    type に "generate_by_OpenAI" を含むモジュールを対象にする。
    """
    result: dict = {}
    if not json_path or not Path(json_path).exists():
        return result
    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return result

    modules = data.get("modules", {})
    if not isinstance(modules, dict):
        return result

    for name, mod in modules.items():
        if not isinstance(mod, dict):
            continue
        if "generate_by_OpenAI" not in str(mod.get("type", "")):
            continue
        prompt = mod.get("params", {}).get("prompt", "")
        if prompt:
            result[name] = prompt
    return result


def _write_refresh_instructions(state: PipelineState, json_path: str, mod_body: str) -> str:
    """リフレッシュモード用の指示書を機械的に生成して書き出す。dirlite agent は呼ばない。

    Returns: 書き出した指示書ファイルのパス
    """
    existing = _extract_existing_openai_prompts(json_path)
    out_path = PROJECT_DIR / "output" / "reports" / f"refresh_instructions_{state.facility}_{state.flow}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# リフレッシュ指示書 — {state.facility} {state.flow}",
        "",
        "## モード",
        "Refresh（全 OpenAI モジュールのプロンプトを最新 SKILL テンプレート準拠で書き直す）",
        "",
        "## 対象既存JSON",
        f"- {json_path}",
        "",
        f"## 対象 OpenAI モジュール（{len(existing)}件 — 既存 BIVR から抽出）",
        "",
    ]
    for name in sorted(existing.keys()):
        lines.append(f"- `{name}`（既存プロンプト {len(existing[name])} 文字）")
    lines.append("")
    lines.append("## 修正指示ファイル本文（参考情報）")
    lines.append("")
    if mod_body.strip():
        lines.append(mod_body.strip())
    else:
        lines.append("（自由記述なし）")
    lines.append("")
    lines.append("## 後続処理")
    lines.append("")
    lines.append("step_prompter_refresh が既存プロンプトを参考材料として prompter agent に渡し、最新 SKILL テンプレートで一から書き起こす。inject_prompts.py がサイドカーを JSON に注入する。")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)


def step_dirlite(state: PipelineState) -> bool:
    """DirLite (Pattern 2専用): 修正指示ファイルの Mode ヘッダで分岐。

    - Mode: Refresh → orchestrator が機械的に refresh_instructions を生成し dirlite agent はスキップ
    - それ以外      → dirlite agent を呼んで差分指示書を生成
    """
    json_path = state.base_path
    if not json_path or not Path(json_path).exists():
        log_error(f"既存JSONが見つかりません: {json_path} — --base に既存JSONのパスを指定してください")
        return False

    # patch DSL 判定（docs/specs/bivr-patch-dsl.md）: spec が YAML かつ top-level patches: を
    # 持つ場合は「人間承認済み patch ファイル」— dirlite/fixer（LLM）を使わず
    # tools/bivr_patch.py が決定論適用する。
    spec_p = Path(state.spec_path)
    if spec_p.suffix in (".yaml", ".yml"):
        try:
            import yaml as _yaml
            spec_doc = _yaml.safe_load(spec_p.read_text(encoding="utf-8"))
        except Exception as e:
            log_error(f"patch YAML の読み込みに失敗: {e}")
            return False
        if isinstance(spec_doc, dict) and isinstance(spec_doc.get("patches"), list):
            state.outputs["bivr_patch"] = str(spec_p)
            log_ok(f"patch DSL モード: {spec_p.name}"
                   f"（{len(spec_doc['patches'])} 変更 — dirlite/fixer はスキップ・決定論適用）")
            return True

    # Mode 判定
    mode = _parse_mode_header(state.spec_path)
    if mode == "Refresh":
        # 修正指示ファイル本文（フロントマター以降）を読む
        try:
            content = Path(state.spec_path).read_text(encoding="utf-8")
        except Exception:
            content = ""
        body = ""
        lines = content.splitlines()
        if lines and lines[0].strip() == "---":
            for i, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    body = "\n".join(lines[i + 1 :])
                    break

        instructions_path = _write_refresh_instructions(state, json_path, body)
        state.outputs["refresh_instructions"] = instructions_path
        log_ok(f"リフレッシュ指示書: {Path(instructions_path).name}（dirlite agent はスキップ）")
        return True

    # 既存挙動（プロンプト修正モード）
    prompt = (
        f"以下の既存フローJSONと修正指示を読んで、fixerが実行できる差分指示書を生成してください。\n"
        f"既存フローJSON: {json_path}\n"
        f"修正指示ファイル: {state.spec_path}\n\n"
        f"出力先: output/reports/dirlite_report_{state.facility}_{state.flow}.md"
    )
    code, stdout, stderr, _ = invoke_agent("dirlite", prompt)
    if code != 0:
        state.errors.append(f"dirlite failed: {stderr[:200]}")
        return False

    report_path = PROJECT_DIR / "output" / "reports" / f"dirlite_report_{state.facility}_{state.flow}.md"
    if report_path.exists():
        state.outputs["dirlite_report"] = str(report_path)
        log_ok(f"差分指示書: {report_path.name}")
        # Manifest 形式 (v2) の frontmatter affects を解析して state に保存
        manifest = _parse_dirlite_manifest(str(report_path))
        if manifest:
            state.dirlite_manifest = manifest
            affects = manifest.get("affects", []) or []
            log_info(f"dirlite manifest v{manifest.get('version', '?')}: affects={affects}")
    else:
        log_warn("差分指示書ファイルが見つかりません — fixer_modify はスキップされます")
    return True


def _parse_dirlite_manifest(report_path: str) -> dict:
    """dirlite_report.md の frontmatter (manifest_version: 2 形式) を解析。

    旧形式 (frontmatter なし) は空 dict を返す。新形式の場合は
    {"version": 2, "affects": [...], "sections": {"properties": "...本文...", ...}} を返す。
    """
    try:
        text = Path(report_path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fm_text = text[4:end]
    body = text[end + 4:]

    manifest = {"version": 1, "affects": [], "sections": {}}
    for line in fm_text.splitlines():
        line = line.rstrip()
        if line.startswith("manifest_version:"):
            try:
                manifest["version"] = int(line.split(":", 1)[1].strip())
            except Exception:
                pass
        elif line.startswith("affects:"):
            # `affects: [a, b]` インライン形式
            rest = line.split(":", 1)[1].strip()
            if rest.startswith("[") and rest.endswith("]"):
                manifest["affects"] = [
                    x.strip().strip("'\"")
                    for x in rest[1:-1].split(",")
                    if x.strip()
                ]
        elif line.lstrip().startswith("- ") and manifest["affects"] is not None:
            # YAML list 続き行 `  - properties`
            stripped = line.lstrip()[2:].strip().strip("'\"")
            if stripped and not stripped.startswith("#"):
                manifest["affects"].append(stripped)

    # セクション分割 (## N. タイトル ヘッダで切る)
    current_key = None
    current_lines: list[str] = []
    section_map = {
        "json_blocks": ["JSON ブロック変更", "ブロック単位の変更"],
        "properties": ["Properties Manifest", "IVRプロパティへの影響"],
        "phonebook": ["Phonebook Manifest"],
        "bivr_bundle": ["BIVR Bundle Manifest"],
        "layout": ["Layout Hints"],
        "context_settings": ["Context Settings Manifest", "コンテキスト設定"],
    }
    def _match_section(heading: str) -> str:
        for key, aliases in section_map.items():
            for alias in aliases:
                if alias in heading:
                    return key
        return ""
    for line in body.splitlines():
        if line.startswith("## "):
            if current_key:
                manifest["sections"][current_key] = "\n".join(current_lines).strip()
            current_key = _match_section(line)
            current_lines = []
        elif current_key:
            current_lines.append(line)
    if current_key:
        manifest["sections"][current_key] = "\n".join(current_lines).strip()
    return manifest


def step_prompter_refresh(state: PipelineState) -> bool:
    """Pattern 2 リフレッシュモード: 全 OpenAI モジュールを最新 SKILL テンプレート準拠で書き直す。

    既存プロンプトをスタイル参照として prompter に渡す。step_prompter と同じ形式の
    サイドカー出力 + inject_prompts.py 注入を行う。
    """
    json_path = state.base_path
    if not json_path or not Path(json_path).exists():
        log_error(f"既存JSONが見つかりません: {json_path}")
        return False

    targets = _list_prompter_targets(state)
    if not targets:
        log_warn("Prompter Refresh: 対象 OpenAI モジュールなし（設計書 yaml が未生成 or hearing ブロックなし）")
        return True

    existing_prompts = _extract_existing_openai_prompts(json_path)

    sidecar_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    sidecar_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = sidecar_dir / f"prompts_{state.facility}_{state.flow}.md"
    prompted_path = PROJECT_DIR / "output" / "json" / f"prompted_{state.facility}_{state.flow}.json"
    prompted_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(json_path, str(prompted_path))

    log_info(f"Prompter Refresh: {len(targets)} モジュールを書き直し（既存参照あり {len(existing_prompts)}件）")

    # SKILL テンプレートを埋め込む（step_prompter と同じロジック）
    SKILL_FILE_MAP = {
        "classify":  "SKILL_A_classification",
        "judge":     "SKILL_B_yes_no",
        "convert":   "SKILL_C_date",
        "normalize": "SKILL_D_normalization",
        "summarize": "SKILL_E_freetext",
    }
    SKILL_LABEL = {
        "classify":  "SKILL_A（分類型・N択判定）",
        "judge":     "SKILL_B（はい/いいえ判定型）",
        "convert":   "SKILL_C（日付変換型）",
        "normalize": "SKILL_D（正規化型・リスト照合）",
        "summarize": "SKILL_E（自由テキスト型）",
    }
    skill_dir = PROJECT_DIR / "docs" / "ai" / "skills"
    needed_skills = {SKILL_FILE_MAP.get(t["processing"], "SKILL_A_classification") for t in targets}
    skill_texts: dict = {}
    for sk in needed_skills:
        candidates = list(skill_dir.glob(f"{sk}*.md"))
        if candidates:
            skill_texts[sk] = candidates[0].read_text(encoding="utf-8")
    skill_section = ""
    for sk, content in skill_texts.items():
        skill_section += f"\n\n---\n## テンプレート: {sk}\n\n{content}"

    # モジュール別指示（既存プロンプトを「参考」として埋め込む）
    module_instructions = []
    for t in targets:
        labels = ", ".join(t["output_labels"]) if t["output_labels"] else "（なし）"
        rules = t.get("openai_rules", {})
        mapping_str = ""
        if rules.get("mapping"):
            mapping_str = "\n  マッピング:\n" + "\n".join(
                f"    - {m.get('input', '')} → {m.get('output', '')}"
                for m in rules["mapping"]
            )
        rv = t.get("range_values", [])
        range_str = ""
        if rv:
            range_str = "\n  range_values:\n" + "\n".join(
                f"    - id={r.get('id', '')} value={r.get('value', '')}"
                for r in rv if isinstance(r, dict)
            )

        existing = existing_prompts.get(t["module_name"], "")
        existing_block = ""
        if existing:
            existing_block = (
                f"\n\n  既存プロンプト（参考。語彙・分岐ラベル・施設固有表現・既知STT誤変換のみ抽出。\n"
                f"  古いセクション構造・リテラル\\n・古いモデル前提の表現は流用しない）:\n"
                f"  ```\n{existing}\n  ```"
            )

        module_instructions.append(
            f"### {t['module_name']}\n"
            f"- パターン: {SKILL_LABEL.get(t['processing'], t['processing'])}\n"
            f"- TTS文言: 「{t['tts_announcement']}」\n"
            f"- 出力ラベル: {labels}\n"
            f"- STT種別: {t['stt_type']}\n"
            f"- 保存先: {t['save_to']}"
            f"{mapping_str}{range_str}"
            f"{existing_block}"
        )

    module_block = "\n\n".join(module_instructions)
    refresh_instructions = state.outputs.get("refresh_instructions", "")
    free_text_note = ""
    if refresh_instructions and Path(refresh_instructions).exists():
        free_text_note = (
            f"\n\n## 修正指示ファイル本文（参考）\n\n"
            f"{refresh_instructions} の `## 修正指示ファイル本文（参考情報）` セクションを参照。"
        )

    prompt = (
        f"## モード: Pattern 2 リフレッシュモード（全 OpenAI モジュール書き直し）\n\n"
        f"prompter.md の「## リフレッシュモード」セクションに従い、"
        f"以下の {len(targets)} 件の OpenAI モジュールのプロンプトを **最新 SKILL テンプレート準拠で一から書き起こし**、"
        f"サイドカーファイルに書き出してください。既存プロンプトはスタイル参照のみ（patchwork 禁止）。\n\n"
        f"**書き出し先サイドカーファイル**: {sidecar_path}\n\n"
        f"> Write ツール 1 回で全モジュール分を一括書き出し。JSON への Edit は不要。\n\n"
        f"## サイドカーファイルの書式\n\n"
        f"```\n"
        f"## モジュール名（例: openAI_予約_通院歴確認）\n"
        f"# Role\n"
        f"あなたは...\n\n"
        f"---\n\n"
        f"# Context（重要）\n"
        f"...\n\n"
        f"## 次のモジュール名\n"
        f"# Role\n"
        f"...\n"
        f"```\n\n"
        f"- `## モジュール名` がセクション区切り（下記対象一覧の `### モジュール名` をそのまま使う）\n"
        f"- 改行は実改行で書く（`\\n` リテラル禁止）\n\n"
        f"## 対象モジュール（{len(targets)}件）\n\n"
        f"{module_block}\n"
        f"{free_text_note}\n\n"
        f"## 作業ルール\n"
        f"- 既存プロンプトから流用するのは語彙・分岐ラベル・施設固有表現・既知 STT 誤変換パターンのみ\n"
        f"- セクション構造は SKILL テンプレートに従う（`# Role` `# Context` `# プロンプトインジェクション対策` `# 出力仕様` `# 判定アルゴリズム` 等）\n"
        f"- tester.py 4本柱（# Role / # Context / NO_RESULT / インジェクション対策）を必ず満たす\n"
        f"{skill_section}"
    )

    code, stdout, stderr, _ = invoke_agent("prompter", prompt)
    if code != 0:
        state.errors.append(f"prompter_refresh failed: {stderr[:200]}")
        return False

    if not sidecar_path.exists():
        log_error(f"サイドカーファイルが見つかりません: {sidecar_path}")
        return False
    state.outputs["prompter_sidecar"] = str(sidecar_path)

    # inject_prompts.py で注入
    inj_cmd = [
        "python3",
        str(PROJECT_DIR / "scripts" / "inject_prompts.py"),
        str(sidecar_path),
        str(prompted_path),
    ]
    inj_code, inj_stdout, inj_stderr = run_cmd(inj_cmd, timeout=SCRIPT_TIMEOUT)
    if inj_code != 0:
        state.errors.append(f"inject_prompts failed: {inj_stderr[:200]}")
        return False

    state.outputs["prompted_json"] = str(prompted_path)
    state.outputs["modified_json"] = str(prompted_path)
    state.outputs["merged_json"] = str(prompted_path)
    state.outputs["draft_json"] = str(prompted_path)
    log_ok(f"prompter_refresh完了: {prompted_path.name}（{len(targets)} モジュール書き直し）")
    return True


def step_pattern2_apply(state: PipelineState) -> bool:
    """Pattern 2: dirlite の出力に応じて patch / modify / refresh を実行する dispatcher"""
    if state.outputs.get("bivr_patch"):
        return step_bivr_patch_apply(state)
    if state.outputs.get("refresh_instructions"):
        return step_prompter_refresh(state)
    if state.outputs.get("dirlite_report"):
        return step_fixer_modify(state)
    log_error("dirlite が出力ファイルを生成しませんでした（refresh_instructions も dirlite_report も無し）")
    return False


def step_bivr_patch_apply(state: PipelineState) -> bool:
    """Pattern 2 patch DSL: 人間承認済み patch YAML を tools/bivr_patch.py で決定論適用する。
    LLM 不使用・fail-closed（検証エラー時は何も書かずパイプライン停止 → 人間へ差し戻し）。"""
    json_path = state.base_path
    patch_path = state.outputs["bivr_patch"]
    report_path = (PROJECT_DIR / "output" / "reports"
                   / f"bivr_patch_report_{state.facility}_{state.flow}.md")

    cmd = [sys.executable, str(PROJECT_DIR / "tools" / "bivr_patch.py"),
           "--json", str(json_path), "--patch", str(patch_path),
           "--apply", "--report", str(report_path)]
    log_info(f"bivr_patch: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=SCRIPT_TIMEOUT)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_error("bivr_patch 検証失敗（何も適用されていません）— patch YAML を壁打ちで直して再実行")
        state.errors.append(f"bivr_patch: exit {result.returncode}")
        return False

    # touched モジュール（stdout 最終 JSON 行）→ validator の scope 制限に流用
    touched: list = []
    for line in reversed((result.stdout or "").splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                touched = json.loads(line).get("touched", [])
            except Exception:
                pass
            break
    if touched:
        # dirlite manifest 互換の affects として保存（validator_modify の scope 制限が読む）
        state.dirlite_manifest = {"version": 2, "affects": touched, "sections": {}}
        log_info(f"bivr_patch touched: {touched}")

    state.outputs["modified_json"] = str(json_path)
    state.outputs["merged_json"] = str(json_path)
    state.outputs["draft_json"] = str(json_path)
    state.outputs["bivr_patch_report"] = str(report_path)
    log_ok(f"bivr_patch 適用完了: {Path(json_path).name}")
    return True


def step_fixer_modify(state: PipelineState) -> bool:
    """Pattern 2専用 Fixer: dirlite差分指示書に基づいて既存JSONを外科的修正"""
    dirlite_report = state.outputs.get("dirlite_report", "")
    json_path = state.base_path

    if not json_path or not Path(json_path).exists():
        log_error(f"修正対象JSONが見つかりません: {json_path}")
        return False

    prompt = (
        f"以下の差分指示書に従って、既存フローJSONを外科的に修正してください。\n"
        f"差分指示書: {dirlite_report}\n"
        f"修正対象JSON: {json_path}\n\n"
        f"修正ルール:\n"
        f"- 差分指示書に記載された箇所のみEditツールで変更する\n"
        f"- 指示のない箇所は絶対に変更しない\n"
        f"- 新規TTSモジュールを追加した場合は、対応するIVRプロパティ追記行"
        f"（例: {{モジュール名}}.prompt={{tts_g:発話テキスト}}）を修正レポートに記載すること"
        f"（人間が後でpropertiesファイルに追記する）\n"
        f"- 修正完了後「完了: [変更内容の要約]」と報告すること"
    )
    code, stdout, stderr, _ = invoke_agent("fixer", prompt)
    if code != 0:
        state.errors.append(f"fixer_modify failed: {stderr[:200]}")
        return False

    # 修正後のJSONパスを各キーに登録（validator/reviewer/tester/build_bivr が参照）
    state.outputs["modified_json"] = json_path
    state.outputs["merged_json"] = json_path   # reviewer, tester, build_bivr が参照
    state.outputs["draft_json"] = json_path    # 互換性
    log_ok(f"fixer_modify完了: {Path(json_path).name}")
    return True


def step_validator_modify(state: PipelineState) -> bool:
    """Pattern 2専用: 修正済みJSONの構造チェック（プロンプトが存在するのでフルバリデーション）"""
    json_path = state.outputs.get("modified_json") or state.base_path
    if not json_path or not Path(json_path).exists():
        log_error("修正済みJSONが見つかりません")
        return False
    step_validator(state, json_path, report_key="validator_report")
    return True  # validator失敗はブロッキングしない（fixer が後処理）


def step_tester(state: PipelineState) -> bool:
    """Tester: プロンプト品質チェック + ルート到達性テスト（tester.py）"""
    json_path = state.outputs.get("merged_json") or state.outputs.get("reviewed_json", "")
    if not json_path:
        log_error("テスト対象のJSONが見つかりません")
        return False

    properties = state.outputs.get("properties", "")

    # レポート出力先
    report = PROJECT_DIR / "output" / "reports" / f"test_report_{state.facility}_{state.flow}.md"

    # tester.py コマンド構築
    cmd = [
        "python3", "schemas/tester.py", json_path,
        "-o", str(report),
    ]

    # サブフロー自動検出（聴取系・RAG系・その他 — メインフロー draft を除く全 draft_*.json）
    _main_stem_prefix = f"draft_{state.facility}_{state.flow}"
    subflows = sorted(
        p for p in (PROJECT_DIR / "output" / "json").glob(f"draft_{state.facility}*.json")
        if not p.stem.startswith(_main_stem_prefix)
    )
    if subflows:
        cmd.append("--subflows")
        cmd.extend([str(s) for s in subflows])

    # プロパティ
    if properties and Path(properties).exists():
        cmd.extend(["--properties", properties])

    code, stdout, stderr = run_cmd(cmd, timeout=VALIDATOR_TIMEOUT)

    if code == 2:
        log_error("Tester ABORT: prompter未実行のファイルです")
        return False

    if report.exists():
        state.outputs["test_report"] = str(report)
        content = report.read_text(encoding="utf-8")
        if "**判定**: PASS" in content:
            log_ok("Tester PASS")
            return True
        else:
            log_warn("Tester FAIL -- レポートを確認してください")
            return False

    if code == 0:
        log_ok("Tester 完了（レポート未生成）")
        return True

    log_warn("Tester 完了（結果不明）")
    return True  # テスター失敗はブロッキングしない（エスカレーションのみ）


def step_add_date_suffix(state: PipelineState) -> bool:
    """bivr 出力ファイル名用に日付サフィックスを *記録* する（フロー名は変更しない）。

    命名規則（2026-06-04, docs/brekeke/naming_convention.md）では日付サフィックス
    `_YYYYMMDD` は **group_name 側** に含まれ、scaffold（メイン name）と copy_subflows
    （サブフロー name）が group_name を verbatim 伝播する。したがってフロー名・サブフロー名・
    jump 参照に **後段で日付を付与してはならない**（旧実装は `{group}_date$flow` に対して
    末尾判定をすり抜け `..._date$flow_date` と二重付与し、廃止済みの旧形式を再生成していた）。

    ここでは name を一切書き換えず、bivr 出力ファイル名（`{facility}_{flow}_{date}.bivr`）用に
    date_suffix を group_name 末尾の `_YYYYMMDD` から抽出する（無ければ当日）。
    """
    json_path = state.outputs.get("merged_json") or state.outputs.get("reviewed_json", "")
    date_suffix = datetime.now().strftime("%Y%m%d")
    if json_path and Path(json_path).exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                name = json.load(f).get("name", "")
            group = name.split("$", 1)[0] if "$" in name else name
            m = re.search(r"_(\d{8})$", group)
            if m:
                date_suffix = m.group(1)
        except Exception:
            pass
    state.outputs["date_suffix"] = date_suffix
    log_ok(f"日付サフィックス記録（bivr 名用）: _{date_suffix}"
           f"（フロー名は group_name 側で版管理済み・name は変更しない）")
    return True


def step_build_bivr(state: PipelineState) -> bool:
    """build_bivr.py: .bivr パッケージ生成。メインフロー + サブフロー（RAG・個人情報系）を全て含める"""
    json_path = state.outputs.get("merged_json") or state.outputs.get("reviewed_json", "")
    if not json_path:
        log_error("ビルド対象のJSONが見つかりません")
        return False

    # 日付サフィックスは step_add_date_suffix で付与済み
    date_suffix = state.outputs.get("date_suffix", datetime.now().strftime("%Y%m%d"))

    # サブフロー draft JSON を全て含める（copy_subflows.py が output/json/draft_*.json に生成済み）
    # メインフローの draft は prompted/reviewed/merged と同じ flow_name を持つため除外する
    subflow_jsons: list[str] = []
    main_json_path = Path(json_path)
    json_dir = main_json_path.parent
    main_basename = main_json_path.name  # prompted_xxx.json / merged_xxx.json 等
    # メインフロー JSON の "name" フィールドを取得して重複を避ける
    try:
        with open(main_json_path, encoding="utf-8") as f:
            main_flow_name = json.load(f).get("name", "")
    except Exception:
        main_flow_name = ""
    # 命名規則（2026-06-04）では日付は group_name 側（`$` の前）に含まれ、メイン name と
    # サブフロー name は同じ group_name を verbatim 共有するため group ($ 前) 比較で正しく揃う。
    # 下の `_date_suffix_re`（末尾 `_8桁数字` 剥がし）は、旧形式（日付がフロー名末尾）の
    # 残置 draft が混ざった場合の後方互換セーフティネット。新形式の name は末尾が `$flow` のため
    # この正規表現にはマッチせず no-op となる（実害なし）。
    _date_suffix_re = re.compile(r'_\d{8}$')
    main_flow_base = _date_suffix_re.sub('', main_flow_name)
    # メイン flow の group (= `{group}$flow` の `$` 以前) を抽出。subflow フィルタに使う
    main_group = main_flow_name.split("$", 1)[0] if "$" in main_flow_name else ""
    for p in sorted(json_dir.glob("draft_*.json")):
        # draft_{facility or target_facility}_{step}.json のうち、
        # 1) メインフローと同じ base name を持つものは除外（日付サフィックス揺れ吸収）
        # 2) **同一 group (= 施設) のもののみ採用**。他施設の残置 draft が bivr 汚染を起こすのを防ぐ
        try:
            with open(p, encoding="utf-8") as f:
                sub_name = json.load(f).get("name", "")
            sub_base = _date_suffix_re.sub('', sub_name)
            sub_group = sub_name.split("$", 1)[0] if "$" in sub_name else ""
            if not sub_base or sub_base == main_flow_base:
                continue
            if main_group and sub_group != main_group:
                continue  # 他施設の subflow を除外
            subflow_jsons.append(str(p))
        except Exception:
            pass

    # Pattern 2: 既存 BIVR から extract した非 draft_ プレフィックス JSON もサブフロー候補
    # (`output/json/_extracted_*/`) — Brekeke の Jump to Flow 解決のため bundle に必須
    if state.pattern == 2 and json_dir.name.startswith("_extracted_"):
        already = {Path(p).name for p in subflow_jsons}
        for p in sorted(json_dir.glob("*.json")):
            if p == main_json_path or p.name in already:
                continue
            try:
                with open(p, encoding="utf-8") as f:
                    sub_name = json.load(f).get("name", "")
                sub_base = _date_suffix_re.sub('', sub_name)
                sub_group = sub_name.split("$", 1)[0] if "$" in sub_name else ""
                if not sub_base or sub_base == main_flow_base:
                    continue
                if main_group and sub_group != main_group:
                    continue  # 他施設フローを除外（extracted dir 内も同様）
                subflow_jsons.append(str(p))
            except Exception:
                pass

    cmd = ["python3", "scripts/build_bivr.py", json_path] + subflow_jsons
    # .bivr のときのみ --merge-base を使用（Pattern 2 では既存JSONを直接ビルド）
    if state.base_path and state.base_path.endswith(".bivr"):
        cmd.extend(["--merge-base", state.base_path])

    output_name = f"{state.facility}_{state.flow}_{date_suffix}.bivr"
    output_path = PROJECT_DIR / "output" / "bivr" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd.extend(["-o", str(output_path)])

    code, stdout, stderr = run_cmd(cmd)
    print(stdout)

    if code == 0:
        state.outputs["bivr"] = str(output_path)
        state.outputs["date_suffix"] = date_suffix
        if subflow_jsons:
            log_ok(f"Build: {output_name}  (メイン + サブフロー {len(subflow_jsons)} 件)")
        else:
            log_ok(f"Build: {output_name}")
        return True

    log_error(f"Build失敗: {stderr}")
    return False


def step_properties(state: PipelineState) -> bool:
    """Properties: IVRプロパティ（TTS発話文言）を生成（gen_properties.py スクリプト）"""
    spec = state.outputs.get("design_spec", state.spec_path)
    if not spec:
        log_warn("Properties: 設計書パスが不明 — スキップ")
        return True

    cmd = [
        sys.executable,
        str(PROJECT_DIR / "scripts" / "gen_properties.py"),
        str(spec),
        "--env", "demo",
    ]
    log_info(f"gen_properties: {Path(spec).name}")
    result = subprocess.run(
        cmd, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=SCRIPT_TIMEOUT,
    )
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if result.returncode != 0:
        log_warn(f"gen_properties 失敗（ブロッキングしない）: {result.stderr[:200]}")
        return True  # Properties 失敗はパイプラインをブロックしない

    # stdout の最終行が出力パス
    output_path_str = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    if output_path_str and Path(output_path_str).exists():
        state.outputs["properties"] = output_path_str
        log_ok(f"Properties: {Path(output_path_str).name}")
        return True

    # フォールバック検索: scenarios/{施設}/ を最優先、後方互換で output/ 直下も見る
    scenario_props = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}" / f"properties_{state.facility}_{state.flow}.md"
    legacy_props = PROJECT_DIR / "output" / f"properties_{state.facility}_{state.flow}.md"
    if scenario_props.exists():
        state.outputs["properties"] = str(scenario_props)
        log_ok(f"Properties: {scenario_props.name}")
    elif legacy_props.exists():
        state.outputs["properties"] = str(legacy_props)
        log_ok(f"Properties (legacy path): {legacy_props.name}")
    else:
        # glob で施設名一致を探す（scenarios → output/ の順）
        props_list = list((PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}").glob(f"properties_{state.facility}*"))
        props_list += list((PROJECT_DIR / "output").glob(f"properties_{state.facility}*"))
        props_list.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        if props_list:
            state.outputs["properties"] = str(props_list[0])
            log_ok(f"Properties: {props_list[0].name}")
        else:
            log_warn("Propertiesファイルが見つかりません")

    return True  # Properties 失敗はブロッキングしない


def step_parallel_prompter_properties(state: PipelineState) -> bool:
    """Prompter + Properties を並列実行"""
    log_info("Prompter + Properties 並列実行開始")

    sub_timings: dict = {}

    def _run_prompter():
        t0 = datetime.now()
        ok = step_prompter(state)
        sub_timings["prompter"] = round((datetime.now() - t0).total_seconds(), 1)
        return ok

    def _run_properties():
        t0 = datetime.now()
        ok = step_properties(state)
        sub_timings["properties"] = round((datetime.now() - t0).total_seconds(), 1)
        return ok

    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_run_prompter): "prompter",
            executor.submit(_run_properties): "properties",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                log_error(f"{name} 例外: {e}")
                results[name] = False

    for name, sec in sub_timings.items():
        log_info(f"  ⏱ {name}: {sec}秒")

    return all(results.values())


def step_parallel_tester_build(state: PipelineState) -> bool:
    """Tester + Build を並列実行（step_add_date_suffix 実行後に呼ぶこと）"""
    log_info("Tester + Build 並列実行開始")

    sub_timings: dict = {}

    def _run_tester():
        t0 = datetime.now()
        ok = step_tester(state)
        sub_timings["tester"] = round((datetime.now() - t0).total_seconds(), 1)
        return ok

    def _run_build():
        t0 = datetime.now()
        ok = step_build_bivr(state)
        sub_timings["build"] = round((datetime.now() - t0).total_seconds(), 1)
        return ok

    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(_run_tester): "tester",
            executor.submit(_run_build): "build",
        }
        for future in as_completed(futures):
            name = futures[future]
            try:
                results[name] = future.result()
            except Exception as e:
                log_error(f"{name} 例外: {e}")
                results[name] = False

    t_secs = sub_timings.get("tester", 0)
    b_secs = sub_timings.get("build", 0)
    log_info(f"  ⏱ Tester: {int(t_secs // 60)}分{int(t_secs % 60)}秒  /  "
             f"Build: {int(b_secs // 60)}分{int(b_secs % 60)}秒（並列）")
    # サブ計測を state.step_timings に保存（dashboard から参照可能にする）
    state.step_timings["tester"] = {"status": "ok" if results.get("tester") else "fail", "seconds": t_secs}
    state.step_timings["build"]  = {"status": "ok" if results.get("build")  else "fail", "seconds": b_secs}

    if not results.get("build", False):
        log_error("Build 失敗")
        return False

    if not results.get("tester", True):
        log_warn("Tester FAIL — レポートを確認してください（続行）")

    return True


def step_collect_scenario(state: PipelineState) -> bool:
    """output/json/ + output/bivr/ + properties を output/scenarios/{facility}_{flow}/ に集約する"""
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    scenario_json_dir = scenario_dir / "json"
    scenario_json_dir.mkdir(parents=True, exist_ok=True)

    copied = []

    # 1. JSONファイル: output/json/ から施設名を含む draft_/prompted_/merged_ を全コピー
    json_dir = PROJECT_DIR / "output" / "json"
    for f in json_dir.glob(f"*{state.facility}*.json"):
        if any(f.name.startswith(p) for p in ("prompted_", "draft_", "merged_")):
            dest = scenario_json_dir / f.name
            shutil.copy2(f, dest)
            copied.append(f.name)

    # 2. BIVRファイル
    bivr_path = state.outputs.get("bivr")
    if bivr_path and Path(bivr_path).exists():
        dest = scenario_dir / Path(bivr_path).name
        shutil.copy2(bivr_path, dest)
        copied.append(Path(bivr_path).name)

    # 3. プロパティファイル
    props_path = state.outputs.get("properties")
    if props_path and Path(props_path).exists():
        dest = scenario_dir / Path(props_path).name
        # 既に scenarios/{施設}/ 直下に出力されている場合（gen_properties.py の新パス仕様、
        # 2026-04-28 chore(output) 以降）は src == dest になるためコピーをスキップ。
        # Windows では同パスへの copy2 が WinError 32 (ファイルロック) でクラッシュする。
        try:
            same = Path(props_path).resolve() == dest.resolve()
        except Exception:
            same = False
        if not same:
            shutil.copy2(props_path, dest)
            copied.append(Path(props_path).name)
        else:
            # 既に正しい場所にあるのでスキップ（記録だけ残す）
            copied.append(Path(props_path).name + " (already in place)")
    else:
        # 既に scenarios/{施設}/ にあれば collect 不要、無ければ output/ 直下から救出
        scenario_props = scenario_dir / f"properties_{state.facility}_{state.flow}.md"
        legacy_props = PROJECT_DIR / "output" / f"properties_{state.facility}_{state.flow}.md"
        if scenario_props.exists():
            pass  # 既に正しい場所にある
        elif legacy_props.exists():
            shutil.copy2(legacy_props, scenario_dir / legacy_props.name)
            copied.append(legacy_props.name)

    # 4. 設計書・確認レポート は director が直接 output/scenarios/ に書く設計に統一済み
    # （旧経路 docs/designs/ → docs/archive/designs/ にアーカイブ）。
    # collect_scenario でのコピーは不要。レガシー互換を残したい場合は
    # docs/archive/designs/ から明示的に取り出すこと。

    # 5. Gen2/Gen1ソース: docs/migration/ から（施設名+フロー名で厳密フィルタ）
    migration_dir = PROJECT_DIR / "docs" / "migration"
    if migration_dir.exists():
        for f in migration_dir.glob(f"gen*_{state.facility}_{state.flow}*"):
            shutil.copy2(f, scenario_dir / f.name)
            copied.append(f.name)

    log_ok(f"成果物集約完了: {len(copied)}件 → {scenario_dir.name}/")
    return True


def step_gen_phonebook_csv(state: PipelineState) -> bool:
    """gen_phonebook_csv.py: 設計書 YAML の phonebook セクションから Dr.JOY 電話帳 CSV を生成。

    phonebook.enabled が無い / false の設計書では SKIP（電話帳機能を使わないシナリオ）。
    LLM 不使用の決定論スクリプト。失敗してもパイプラインは継続する（必須ステップではない）。
    """
    spec = state.outputs.get("design_spec", "")
    if not spec or not Path(spec).exists():
        log_warn("設計書が見つかりません、電話帳 CSV 生成をスキップ")
        return True
    if not str(spec).endswith(".yaml"):
        log_info("設計書が YAML 形式でないため電話帳 CSV 生成をスキップ")
        return True

    cmd = ["python3", "scripts/gen_phonebook_csv.py", spec]
    code, stdout, stderr = run_cmd(cmd, timeout=VALIDATOR_TIMEOUT)
    if code != 0:
        log_warn(f"電話帳 CSV 生成失敗: {stderr.strip()[:200]}")
        return True  # 非必須なのでブロックしない
    msg = (stdout or stderr).strip().splitlines()[-1] if (stdout or stderr).strip() else ""
    if msg.startswith("SKIP"):
        log_info(f"電話帳 CSV: {msg}")
    else:
        log_ok(f"電話帳 CSV: {msg}")
        # 出力先を state に記録（commit step の対象にする想定）
        scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
        csv_path = scenario_dir / f"phonebook_{state.facility}_{state.flow}.csv"
        if csv_path.exists():
            state.outputs["phonebook_csv"] = str(csv_path)

    # Pattern 2: gen_phonebook_csv.py が SKIP した（YAML 設計書に phonebook 無し）でも、
    # dirlite manifest の Phonebook Manifest があれば CSV テンプレートを生成する
    if state.pattern == 2 and state.dirlite_manifest:
        _gen_pattern2_phonebook_from_manifest(state)
    return True


def _gen_pattern2_phonebook_from_manifest(state: "PipelineState") -> None:
    """Pattern 2: dirlite manifest の Phonebook Manifest セクションから CSV を生成。
    括弧除去の整形ルールも適用する。
    """
    affects = state.dirlite_manifest.get("affects", []) or []
    if "phonebook" not in affects:
        return

    section = state.dirlite_manifest.get("sections", {}).get("phonebook", "")
    if not section.strip():
        log_info("Phonebook gen: manifest.affects.phonebook あるが section 本文なし、スキップ")
        return

    # 既存 CSV がシナリオ配下にあれば触らない（人間が編集済みの可能性）
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    csv_path = scenario_dir / f"phonebook_{state.facility}_{state.flow}.csv"
    if csv_path.exists():
        log_info(f"Phonebook gen: 既存 CSV ({csv_path.name}) を尊重、上書きしない")
        state.outputs["phonebook_csv"] = str(csv_path)
        return

    # manifest section を簡易 parse: `電話番号: {番号}, 氏名: {名}, フリガナ: {ヨミ}, リスト1〜5: {N}`
    entries: list[dict] = []
    for line in section.splitlines():
        if "電話番号" not in line:
            continue
        ent = {"電話番号": "", "氏名": "", "フリガナ": "", "リスト1": 0, "リスト2": 0, "リスト3": 0, "リスト4": 0, "リスト5": 0, "ブラックリスト": 0, "入電通知": 0}
        for m in re.finditer(r"(電話番号|氏名|フリガナ|ブラックリスト|入電通知)[:：]\s*([^\s,]+)", line):
            ent[m.group(1)] = m.group(2)
        # リスト1〜5: N → リストN を 1 に
        m_list = re.search(r"リスト1〜5[:：]\s*(\d+)", line)
        if m_list:
            n = int(m_list.group(1))
            if 1 <= n <= 5:
                ent[f"リスト{n}"] = 1
        # 個別 `リスト1: 1` など
        for n in range(1, 6):
            m_n = re.search(rf"リスト{n}[:：]\s*(\d+)", line)
            if m_n:
                ent[f"リスト{n}"] = int(m_n.group(1))
        # 氏名整形: 括弧除去
        if ent["氏名"]:
            ent["氏名"] = re.sub(r"[（(].*?[）)]", "", ent["氏名"]).strip()
        if ent["電話番号"]:
            entries.append(ent)

    if not entries:
        log_info("Phonebook gen: manifest から有効エントリ抽出できず、スキップ")
        return

    scenario_dir.mkdir(parents=True, exist_ok=True)
    header = ["電話番号", "氏名", "フリガナ", "ブラックリスト", "リスト1", "リスト2", "リスト3", "リスト4", "リスト5", "入電通知"]
    rows = [",".join(f'"{h}"' for h in header)]
    for ent in entries:
        rows.append(",".join(f'"{ent.get(h, "")}"' for h in header))
    csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    state.outputs["phonebook_csv"] = str(csv_path)
    log_ok(f"Phonebook gen (manifest): {csv_path.name} ({len(entries)} 件) — フリガナ未充填はあれば人間が記入")


# ---------------------------------------------------------------------------
# 完成品ゲート: oracle → Pattern 7（連結・実機） → Pattern 6（単体・実機）
# 「全テスト PASS の状態」だけを完成品として push 可にする（2026-06-10 導入）。
# - P7（結合）が先: 配線・properties・context 受け渡し＝シナリオごとに新しく作られる部分の検証。
# - P6（単体）が後: 発話揺れの責任境界＝部品ライフサイクルの検証。認定ハッシュ一致ならスキップ。
# - 実機の駆動（bivr インポート・発信）は人間。判定結果を対話で記録し test_gate JSON に永続化。
# ---------------------------------------------------------------------------

# === 部品規格 認定（二段判定ゲート v2）: docs/governance/part-certification-spec.md ===
# engine = 全用途で不変のアルゴリズム / spec = 受入必須の分類データ / wiring = デプロイ都合（除外）
_SPEC_BEGIN = "// @spec-begin"
_SPEC_END = "// @spec-end"
_PART_ID_RE = re.compile(r"^\s*//\s*@part-id:\s*(\S+)\s*$", re.M)
_ENGINE_VER_RE = re.compile(r"^\s*//\s*@engine-version:\s*(\S+)\s*$", re.M)


def _read_part_marker(text: str) -> tuple:
    """スクリプトの // @part-id: / // @engine-version: マーカー（種別の刻印）を読む。"""
    m = _PART_ID_RE.search(text)
    v = _ENGINE_VER_RE.search(text)
    return (m.group(1) if m else None, v.group(1) if v else None)


def _norm_body(lines: list) -> str:
    """各行 rstrip + 連続空行畳み込み + 前後 strip。整形差を無視しつつ意味差は残す。"""
    out, prev_blank = [], False
    for ln in lines:
        ln = ln.rstrip()
        if ln == "":
            if prev_blank:
                continue
            prev_blank = True
        else:
            prev_blank = False
        out.append(ln)
    return "\n".join(out).strip()


def _engine_spec_hashes(text: str, wiring_vars: list) -> tuple:
    """マーカー規約で engine_hash / spec_hash を算出。
    spec  = 全 @spec-begin..@spec-end ブロック（行コメント除く）。
    engine= それ以外 − wiring 行（var <name>=）− 全行コメント。
    placeholder は wiring/spec のみに在る前提（リンタ担保）なので engine は充填で不変。"""
    import hashlib
    norm_text = text.replace("\r\n", "\n").replace("\r", "\n")
    wiring_re = None
    if wiring_vars:
        wiring_re = re.compile(r"^\s*var\s+(" + "|".join(re.escape(w) for w in wiring_vars) + r")\s*=")
    spec_lines, engine_lines, in_spec = [], [], False
    for ln in norm_text.split("\n"):
        s = ln.strip()
        if s.startswith(_SPEC_BEGIN):
            in_spec = True
            continue
        if s.startswith(_SPEC_END):
            in_spec = False
            continue
        if s.startswith("//"):
            continue
        if in_spec:
            spec_lines.append(ln)
            continue
        if wiring_re and wiring_re.match(ln):
            continue
        engine_lines.append(ln)
    _h = lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()
    return _h(_norm_body(engine_lines)), _h(_norm_body(spec_lines))


def _part_dir(part_id: str) -> Path:
    return PROJECT_DIR / "modules" / part_id


def _load_part_manifest(part_id: str) -> dict:
    """modules/<part>/part.json（規格表: wiring_vars / specs カタログ）。"""
    p = _part_dir(part_id) / "part.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _certified_registry_path() -> Path:
    return PROJECT_DIR / "modules" / "certified_hashes.json"


def _load_certified_registry() -> dict:
    p = _certified_registry_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _test_gate_path(state: PipelineState) -> Path:
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    return scenario_dir / f"test_gate_{state.facility}_{state.flow}.json"


def _load_test_gate(state: PipelineState) -> dict:
    p = _test_gate_path(state)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_test_gate(state: PipelineState, gate: dict) -> None:
    p = _test_gate_path(state)
    p.parent.mkdir(parents=True, exist_ok=True)
    gate["updated_at"] = datetime.now().isoformat()
    p.write_text(json.dumps(gate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    state.outputs["test_gate"] = str(p)


# cert ゲートが本文走査する module 型 → 本文が入る params フィールド。
# @General$Script は params.script。DOB Re-confirmation Custom Module は値スクリプトを
# params.openAI_prompt に持つ（型名は厚木本番踏襲・中身は認定正本 dob_normalizer/script.js）。
# Custom Module 型でも @part-id マーカーを持つ本文は @General$Script と同じ二段ハッシュ判定にかける（Path A）。
# マーカー無しの本文は従来どおり part=None（認定対象外）で素通り。マップ外の型はスキップ。
_CERT_SCANNED_TYPES = {
    "@General$Script": "script",
    "drjoy^TS Custom Module$DOB Re-confirmation": "openAI_prompt",
}


def _local_cert_path(state: PipelineState) -> Path:
    """施設フロー固有の certified_local.json のパス（output/scenarios/{facility}_{flow}/）"""
    return PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}" / "certified_local.json"


def _load_local_cert(state: PipelineState) -> dict:
    """certified_local.json を読み込む。存在しない場合は空 dict を返す。"""
    p = _local_cert_path(state)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _save_local_cert(state: PipelineState, data: dict) -> None:
    """certified_local.json を保存する（output/scenarios/ 配下 = 自由ゾーン）"""
    p = _local_cert_path(state)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _collect_flow_scripts(state: PipelineState) -> list[dict]:
    """ビルド済み bivr 内の認定走査対象 module（_CERT_SCANNED_TYPES）を列挙し、二段判定の材料を付与する。
    戻り値: [{flow, module, part, engine_hash, spec_hash, engine_ok, spec_certified, local_certified}]
    part=None は @part-id マーカー無し（scaffold 補助 script 等＝認定対象外）。
    spec_certified: グローバル registry（certified_hashes.json）で認定済み。
    local_certified: ローカル registry（certified_local.json）で認定済み（施設専用）。"""
    import urllib.parse
    import zipfile

    bivr = state.outputs.get("bivr")
    if not bivr or not Path(bivr).exists():
        return []

    registry = _load_certified_registry()
    reg_parts = registry.get("parts", {})
    reg_specs = registry.get("specs", {})
    # 施設固有ローカル registry をマージ（spec_certified 判定に追加）
    local_cert = _load_local_cert(state)
    local_specs = local_cert.get("specs", {})
    found: list[dict] = []
    with zipfile.ZipFile(bivr) as z:
        for info in z.infolist():
            decoded = urllib.parse.unquote(info.filename)
            if not decoded.startswith("flows/"):
                continue
            try:
                flow = json.loads(z.read(info.filename).decode("utf-8"))
            except Exception:
                continue
            for mname, m in (flow.get("modules") or {}).items():
                body_field = _CERT_SCANNED_TYPES.get(m.get("type"))
                if body_field is None:
                    continue
                body = str(m.get("params", {}).get(body_field, ""))
                part_id, _ver = _read_part_marker(body)
                if not part_id:
                    found.append({
                        "flow": flow.get("name", decoded), "module": mname, "part": None,
                        "engine_hash": None, "spec_hash": None,
                        "engine_ok": False, "spec_certified": False, "local_certified": False,
                    })
                    continue
                wiring = _load_part_manifest(part_id).get("wiring_vars", [])
                eh, sh = _engine_spec_hashes(body, wiring)
                key = eh + ":" + sh
                found.append({
                    "flow": flow.get("name", decoded), "module": mname, "part": part_id,
                    "engine_hash": eh, "spec_hash": sh,
                    "engine_ok": reg_parts.get(part_id, {}).get("engine_hash") == eh,
                    "spec_certified": key in reg_specs,
                    "local_certified": key in local_specs,
                })
    return found


def step_oracle_gate(state: PipelineState) -> bool:
    """bivr 内の Script 部品を modules/ 正本と照合し、各部品の test_oracle.py を実行（無料・毎回）"""
    insts = _collect_flow_scripts(state)
    gate = _load_test_gate(state)
    gate["script_instances"] = insts
    if not insts:
        log_info("Script 部品なし — oracle 受入はスキップ")
        gate["oracle"] = "PASS_NO_SCRIPTS"
        _save_test_gate(state, gate)
        return True

    parts = sorted({i["part"] for i in insts if i["part"]})
    unknown = [i for i in insts if not i["part"]]
    for u in unknown:
        log_warn(f"modules/ 正本に一致しない Script: {u['module']}（scaffold テンプレ由来等。oracle 対象外）")

    failed = []
    for part in parts:
        test_py = PROJECT_DIR / "modules" / part / "test_oracle.py"
        if not test_py.exists():
            log_warn(f"{part}: test_oracle.py なし — oracle 受入未整備")
            failed.append(part)
            continue
        code, stdout, stderr = run_cmd(["python3", str(test_py)])
        tail = (stdout or stderr).strip().splitlines()
        log_info(f"{part}: {tail[0] if tail else 'no output'}")
        if code != 0:
            failed.append(part)

    if failed:
        gate["oracle"] = "FAIL:" + ",".join(failed)
        _save_test_gate(state, gate)
        log_error(f"Oracle 受入 FAIL: {', '.join(failed)} — cases.tsv（テストの正）に対して不一致")
        return False

    gate["oracle"] = "PASS"
    _save_test_gate(state, gate)
    log_ok(f"Oracle 受入 PASS（{len(parts)} 部品 / Script インスタンス {len(insts)} 個）")
    return True


def step_p7_generate(state: PipelineState) -> bool:
    """Pattern 7: 連結テスト（STT スタブ）bivr とケース表を生成"""
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    bivr = state.outputs.get("bivr")
    if not bivr or not Path(bivr).exists():
        log_error("bivr が見つからないため P7 生成不可")
        return False

    cases_path = PROJECT_DIR / "connection_test" / "cases" / f"{state.facility}_{state.flow}.json"
    if cases_path.exists():
        log_info(f"既存ケース表を使用（人間調整分を尊重）: {cases_path.name}")
    else:
        spec = state.outputs.get("design_spec")
        if not spec or not Path(spec).exists():
            hits = sorted(scenario_dir.glob("設計書_*.yaml"))
            spec = str(hits[0]) if hits else None
        if not spec:
            log_error("設計書 YAML が見つからないため P7 ケース表を生成できません")
            return False
        p7_cmd = [
            "python3", str(PROJECT_DIR / "scripts" / "gen_p7_cases.py"),
            "--spec", str(spec),
            "--facility", state.facility, "--flow", state.flow,
        ]
        # Pattern 2: 修正箇所（bivr_patch touched / dirlite affects）を通るケースを 優先=高 に
        affects = (state.dirlite_manifest or {}).get("affects", []) if state.pattern == 2 else []
        if affects:
            p7_cmd += ["--touched", ",".join(str(a) for a in affects)]
        code, stdout, stderr = run_cmd(p7_cmd)
        print(stdout)
        if code != 0:
            log_error(f"P7 ケース表生成失敗: {stderr}")
            return False
        log_info("DTMF 併用 hearing がある場合は --dtmf-steps での再生成か手動追補を推奨")

    # テスト項目 CSV を必ず書き出す（P7 実機テスト前の MUST）。
    # 既存ケース表を再利用した場合も、人間調整後の最終ケース JSON から CSV を作り直す。
    # CSV は 1 ケースずつ実機で叩いて PASS/FAIL を記入するワークシートを兼ねる。
    cases_csv = scenario_dir / f"連結テストケース_{state.facility}_{state.flow}.csv"
    code, stdout, stderr = run_cmd([
        "python3", str(PROJECT_DIR / "scripts" / "gen_p7_cases.py"),
        "--to-csv", str(cases_path), "--csv-out", str(cases_csv),
    ])
    if stdout:
        print(stdout)
    if code != 0 or not cases_csv.exists():
        log_error(f"P7 テスト項目 CSV の書き出しに失敗（P7 はテスト項目 CSV 必須のため停止）: {stderr}")
        return False
    state.outputs["p7_cases_csv"] = str(cases_csv)
    log_ok(f"P7 テスト項目 CSV: {cases_csv.name}")

    out_bivr = scenario_dir / f"連結テスト_{Path(bivr).name}"
    code, stdout, stderr = run_cmd([
        "python3", str(PROJECT_DIR / "connection_test" / "stub_stt_connection.py"),
        "--bivr", str(bivr), "--cases", str(cases_path), "--out", str(out_bivr),
    ])
    print(stdout)
    if code != 0:
        log_error(f"P7 連結テスト bivr 生成失敗: {stderr}")
        return False

    state.outputs["p7_cases"] = str(cases_path)
    state.outputs["p7_bivr"] = str(out_bivr)

    # --skip-tts 版も同時生成（TTS再生なし・フロー進行/context保存確認用）
    out_bivr_skip = scenario_dir / f"連結テスト_skip_tts_{Path(bivr).name}"
    code2, stdout2, stderr2 = run_cmd([
        "python3", str(PROJECT_DIR / "connection_test" / "stub_stt_connection.py"),
        "--bivr", str(bivr), "--cases", str(cases_path),
        "--out", str(out_bivr_skip), "--skip-tts",
    ])
    if stdout2:
        print(stdout2)
    if code2 != 0:
        log_warn(f"P7 skip-tts bivr 生成失敗（通常版は成功）: {stderr2}")
    else:
        state.outputs["p7_bivr_skip_tts"] = str(out_bivr_skip)
        log_ok(f"P7 skip-tts bivr: {out_bivr_skip.name}  ← 架電で即切断・ログでフロー進行確認")

    # 2026-07-16〜: P7 出力は stub / skip_tts の2種を常に揃える方針。
    # 「実音声で聞いて確認したい」ニーズは stub 版（TTS再生あり・STTスタブ）で既に満たされる。
    # 実機 AmiVoice に人手を介さず音声を注入する経路（音声注入レーン/Twilio+WAV）は本リポジトリ未整備のため、
    # --no-stub-stt（実機 AmiVoice・生身の話者が必要）を「実音声」として標準出力に含めるのは撤回した。
    # 生身の話者による実機確認自体は Step 5（人間の手動実機テスト）でカバーする。

    gate = _load_test_gate(state)
    gate["p7_bivr"] = str(out_bivr)
    gate["p7_cases_csv"] = str(cases_csv)
    if code2 == 0:
        gate["p7_bivr_skip_tts"] = str(out_bivr_skip)
    _save_test_gate(state, gate)
    log_ok(f"P7 連結テスト生成完了: {out_bivr.name}")
    return True


def step_p7_acceptance(state: PipelineState) -> bool:
    """Human: P7 連結テストの実機実行（駆動は手動）と判定記録"""
    gate = _load_test_gate(state)
    if state.unattended:
        gate["p7"] = "PENDING"
        _save_test_gate(state, gate)
        log_warn("無人モード: P7 実機は未実施（PENDING）— 完成品ゲート不成立のため push 不可")
        return True

    print(f"\n{C.BOLD}{'='*60}{C.RESET}")
    print(f"{C.BOLD}  Pattern 7 連結テスト — 実機実行（手動）{C.RESET}")
    print(f"{'='*60}")
    print(f"  1. Brekeke テスト番号へインポート: {state.outputs.get('p7_bivr')}")
    print(f"     └ skip_tts 版（即切断・フロー進行確認用）: {state.outputs.get('p7_bivr_skip_tts')}")
    print(f"  （TTS の実際の読み上げを耳で確認したい場合は上記 stub 版で聞ける。実機 AmiVoice を人手なしで")
    print(f"   駆動する音声注入は本リポジトリ未整備のため対象外）")
    print(f"  2. 発信 → ケース番号+# を入力（ハンズフリー実行）")
    print(f"  3. ケース表の expect と Brekeke ログを突合: {state.outputs.get('p7_cases')}")
    print(f"  4. テスト項目 CSV（PASS/FAIL 記入用）: {state.outputs.get('p7_cases_csv')}")
    print(f"  5. 完走トレースは connection_test/golden/ へ保存推奨")
    print(f"{'='*60}")
    try:
        answer = input(f"{C.BOLD}P7 全ケース PASS? [y=PASS / N=FAIL（中断して修正） / skip]: {C.RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        answer = "skip"

    if answer == "y":
        try:
            memo = input("ログ所在・特記事項（任意）: ").strip()
        except (EOFError, KeyboardInterrupt):
            memo = ""
        gate["p7"] = "PASS"
        gate["p7_evidence"] = memo
        _save_test_gate(state, gate)
        log_ok("P7 連結テスト PASS を記録")
        return True
    if answer == "skip":
        gate["p7"] = "SKIPPED"
        _save_test_gate(state, gate)
        log_warn("P7 をスキップ — 完成品ゲート不成立のため push 不可")
        return True
    gate["p7"] = "FAIL"
    _save_test_gate(state, gate)
    log_error("P7 FAIL — 修正後に --resume p7_gen で再実行してください")
    return False


def step_p6_gate(state: PipelineState) -> bool:
    """Pattern 6 二段判定: stage1=engine 照合（種別/改竄）, stage2=spec 認定（新規格は受入要求）。
    docs/governance/part-certification-spec.md"""
    gate = _load_test_gate(state)
    insts = gate.get("script_instances") or _collect_flow_scripts(state)
    marked = [i for i in insts if i["part"]]

    if not marked:
        gate["p6"] = "PASS_NO_SCRIPTS"
        _save_test_gate(state, gate)
        log_info("認定部品（@part-id マーカー）なし — P6 はスキップ")
        return True

    # --- stage 1b: engine 改竄 / 未登録 → 最優先でブロック ---
    bad_engine = sorted({(i["part"], (i["engine_hash"] or "")[:12]) for i in marked if not i["engine_ok"]})
    if bad_engine:
        print(f"\n{C.BOLD}{'='*60}{C.RESET}")
        print(f"{C.BOLD}  P6 stage1: engine 不一致 — {len(bad_engine)} 部品{C.RESET}")
        print(f"{'='*60}")
        for part, h in bad_engine:
            print(f"  - {part}: engine_hash {h}… が認定 engine と不一致（本体改竄 or 未登録の部品種別）")
        print(f"{'='*60}")
        gate["p6"] = "FAIL_ENGINE"
        _save_test_gate(state, gate)
        log_error("engine 不一致 — 意図的なエンジン改修なら certified_hashes.json の parts を更新（=種別再認定）、"
                  "そうでなければ正本修正。未登録の部品種別なら parts 登録が要")
        return False

    # --- stage 2: 未認定 spec（engine は既知）---
    # グローバル認定 OR ローカル認定（certified_local.json）のどちらかで認定済みなら PASS
    uncertified = sorted({(i["part"], i["engine_hash"], i["spec_hash"])
                          for i in marked if not i["spec_certified"] and not i["local_certified"]})
    if not uncertified:
        gate["p6"] = "PASS_CERTIFIED"
        _save_test_gate(state, gate)
        log_ok(f"全部品が engine+spec 認定済み（{len(marked)} インスタンス）— P6 スキップ")
        return True

    print(f"\n{C.BOLD}{'='*60}{C.RESET}")
    print(f"{C.BOLD}  Pattern 6 stage2: 未認定 spec（新規格）— {len(uncertified)} 件{C.RESET}")
    print(f"{'='*60}")
    blocked = False
    have_set = []  # 受入セットが実在する未認定 spec（手動 P6 で確認 → 登録可）
    for part, eh, sh in uncertified:
        manifest = _load_part_manifest(part)
        pdir = _part_dir(part)
        wiring = manifest.get("wiring_vars", [])
        # part.json.specs の各 filled_script を spec_hash 逆引き（この spec の受入セットが在るか）
        match = None
        for label, meta in manifest.get("specs", {}).items():
            fs = meta.get("filled_script")
            if fs and (pdir / fs).exists():
                _, _sh = _engine_spec_hashes((pdir / fs).read_text(encoding="utf-8"), wiring)
                if _sh == sh:
                    match = (label, meta.get("cases"))
                    break
        if match:
            have_set.append((part, eh, sh, match[0]))
            print(f"  - {part} [{match[0]}]（spec {sh[:12]}… 受入セットあり）")
            print(f"      テストの正: modules/{part}/{match[1]}")
        else:
            blocked = True
            print(f"  - {part}（engine {eh[:12]}… / spec {sh[:12]}… 未認定・受入セット無し）")
            print(f"      規格未定義: modules/{part}/acceptance_test/<spec>/ に受入セット"
                  f"（cases.tsv + 充填JS + 設計書）を作成し part.json.specs に登録せよ")
    print(f"{'='*60}")

    # 救出: 規格セット未定義の部品があればテスト不能 → 通さない
    if blocked:
        gate["p6"] = "BLOCKED_NO_SPEC_SET"
        _save_test_gate(state, gate)
        log_error("規格未定義の部品あり — 受入セット作成まで P6 を通せません（テスト無しでは絶対に通さない）")
        return False

    if state.unattended:
        gate["p6"] = "PENDING"
        _save_test_gate(state, gate)
        log_warn("無人モード: P6 実機は未実施（PENDING）— 完成品ゲート不成立のため push 不可")
        return True

    try:
        answer = input(f"{C.BOLD}上記 spec すべての P6 実機 PASS を確認した? [y / N（中断） / skip]: {C.RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        answer = "skip"

    if answer == "y":
        # 施設専用（個別対応）か共用登録かをメンバーが選択
        print(f"\n{C.BOLD}登録先を選択してください:{C.RESET}")
        print("  [1] local  — この施設専用（certified_local.json）。PR 不要、メンバーが即時登録可")
        print("  [2] global — 全施設共用（modules/certified_hashes.json）。owner の PR マージが必要")
        try:
            dest = input(f"{C.BOLD}登録先 [1=local / 2=global]: {C.RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            dest = "1"

        if dest == "2":
            # --- グローバル登録（従来通り modules/certified_hashes.json）---
            registry = _load_certified_registry()
            specs_reg = registry.setdefault("specs", {})
            for part, eh, sh in uncertified:
                specs_reg[eh + ":" + sh] = {
                    "part": part,
                    "certified_date": datetime.now().strftime("%Y-%m-%d"),
                    "scenario": f"{state.facility}_{state.flow}",
                }
            p = _certified_registry_path()
            p.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            gate["p6"] = "PASS"
            _save_test_gate(state, gate)
            log_ok(f"P6 PASS — {len(uncertified)} spec をグローバル認定レジストリへ登録: {p}")
            log_info("modules/README.md の認定台帳にも part×spec 行を追記してください")
        else:
            # --- ローカル登録（certified_local.json = 自由ゾーン、PR 不要）---
            local_data = _load_local_cert(state)
            local_specs_reg = local_data.setdefault("specs", {})
            for part, eh, sh in uncertified:
                local_specs_reg[eh + ":" + sh] = {
                    "part": part,
                    "certified_date": datetime.now().strftime("%Y-%m-%d"),
                    "facility": state.facility,
                    "flow": state.flow,
                    "scope": "local",
                }
            _save_local_cert(state, local_data)
            lp = _local_cert_path(state)
            gate["p6"] = "PASS"
            _save_test_gate(state, gate)
            log_ok(f"P6 PASS — {len(uncertified)} spec をローカル認定レジストリへ登録: {lp}")
            log_info("certified_local.json は output/scenarios/ 配下（自由ゾーン）のため PR 不要です")
        return True
    if answer == "skip":
        gate["p6"] = "SKIPPED"
        _save_test_gate(state, gate)
        log_warn("P6 をスキップ — 完成品ゲート不成立のため push 不可")
        return True
    gate["p6"] = "FAIL"
    _save_test_gate(state, gate)
    log_error("P6 FAIL — 部品/spec を修正（=再受入）後に --resume oracle_gate で再実行してください")
    return False


def step_score_gate(state: PipelineState) -> bool:
    """4 層採点ゲート: ビルド済みシナリオを tools/score_bivr.py で 4 層採点し、
    成績表 (scorecard_{flow}.md) を出力する。出荷判定は M2 層 (第1 文言・第4 分岐) のみ:
      - BLOCK (return False) … L1 本物 CRITICAL or L4 FAIL（フラット展開成功・本物の構造欠陥）
      - WARNING (継続)        … L4 PROVISIONAL（サブフロー展開で整合取れず＝テスト採点・暫定）
      - 非ゲート               … L3 det 率 (KPI) / L2 STT (M0)（Goodhart 回避）
    サブフローは『展開できれば全評価、整合取れなければ暫定 WARNING で止めない』
    （浜口さん仕様 2026-06-25 / 4層 verifier レジストリ内側ループの実体化）。"""
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    bivr = state.outputs.get("bivr")
    if not bivr or not Path(bivr).exists():
        hits = sorted(scenario_dir.glob("*.bivr"))
        bivr = str(hits[0]) if hits else None
    if not bivr:
        log_warn("採点対象 .bivr が見つからない — 4層採点ゲートをスキップ")
        return True

    md_out = scenario_dir / f"scorecard_{state.flow}.md"
    json_out = scenario_dir / f"scorecard_{state.flow}.json"
    code, stdout, stderr = run_cmd([
        "python3", str(PROJECT_DIR / "tools" / "score_bivr.py"),
        "--scenario-dir", str(scenario_dir),
        "--md-report", str(md_out), "--json-report", str(json_out),
    ])

    rep = {}
    if json_out.exists():
        try:
            rep = json.loads(json_out.read_text(encoding="utf-8"))
        except Exception:
            rep = {}
    ship = rep.get("ship_gate", "?")
    gate = _load_test_gate(state)
    gate["score_gate"] = ship
    gate["scorecard_md"] = str(md_out)
    _save_test_gate(state, gate)
    state.outputs["scorecard_md"] = str(md_out)

    for x in rep.get("layers", []):
        log_info(f"  第{x.get('layer')} {x.get('component')}: {x.get('status')}")
    if rep.get("provisional"):
        l4 = next((x for x in rep.get("layers", []) if x.get("layer") == 4), {})
        unres = l4.get("unresolved_subflows") or []
        log_warn("第4 分岐は暫定（テスト採点）: サブフローを展開しきれず整合不全"
                 + (f"／未解決サブフロー: {', '.join(unres)}" if unres else "")
                 + " — 出荷は止めないが梱包是正を推奨")

    if code != 0:
        log_error(f"4層採点ゲート BLOCK: {ship}")
        log_error(f"成績表（差し戻し票）: {md_out}")
        if stderr.strip():
            log_error(stderr.strip().splitlines()[-1])
        return False
    log_ok(f"4層採点ゲート: {ship}（成績表 {md_out.name}）")
    return True


def step_commit_evidence(state: PipelineState) -> bool:
    """テスト証跡（test_gate / P7 ケース表・bivr / 認定レジストリ）をコミット"""
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    targets = [scenario_dir]
    cases = state.outputs.get("p7_cases")
    if cases and Path(cases).exists():
        targets.append(Path(cases))
    cases_csv = state.outputs.get("p7_cases_csv")
    if cases_csv and Path(cases_csv).exists():
        targets.append(Path(cases_csv))
    reg = _certified_registry_path()
    if reg.exists():
        targets.append(reg)
    # 施設固有ローカル認定レジストリ（自由ゾーン）があれば証跡に含める
    local_cert = _local_cert_path(state)
    if local_cert.exists():
        targets.append(local_cert)
    for t in targets:
        run_cmd(["git", "add", str(t)])
    code, stdout, stderr = run_cmd([
        "git", "commit", "-m",
        f"[pipeline] {state.facility} {state.flow} 完成品ゲート証跡（P7/P6/oracle）",
    ])
    if code == 0:
        log_ok("テスト証跡コミット完了")
    elif "nothing to commit" in stderr or "nothing to commit" in stdout:
        log_info("コミット対象の変更なし")
    else:
        log_warn(f"テスト証跡コミット失敗: {stderr}")
    return True


def _write_run_history(state: PipelineState) -> Path | None:
    """pipeline 実行サマリを docs/run_history/{施設}_{flow}_{ts}.json に書き出す。

    Curator / Optimizer Agent が後で signal として使う統合データ。
    1 run = 1 ファイルにすることで並列実行時の merge 衝突を回避。
    output/ は将来 git 除外予定 (memory: project_output_git_redesign) なので
    docs/ 配下に置いて永続管理対象にする。
    """
    history_dir = PROJECT_DIR / "docs" / "run_history"
    history_dir.mkdir(parents=True, exist_ok=True)

    started = state.started_at or datetime.now().isoformat()
    try:
        ts = datetime.fromisoformat(started).strftime("%Y%m%d_%H%M%S")
    except Exception:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out_path = history_dir / f"{state.facility}_{state.flow}_{ts}.json"

    # step_timings から集計
    tot_in = tot_out = tot_cw = tot_cr = tot_sec = 0
    step_summary: dict = {}
    critical_codes: list[str] = []
    for sname, timing in (state.step_timings or {}).items():
        if not isinstance(timing, dict):
            continue
        sec = timing.get("seconds", 0) or 0
        tok = timing.get("tokens") or {}
        ti = tok.get("input", 0) or 0
        to = tok.get("output", 0) or 0
        tcw = tok.get("cache_creation", 0) or 0
        tcr = tok.get("cache_read", 0) or 0
        tot_sec += sec; tot_in += ti; tot_out += to; tot_cw += tcw; tot_cr += tcr
        entry: dict = {
            "status": timing.get("status", "?"),
            "seconds": sec,
        }
        if tok:
            entry["tokens"] = {"input": ti, "output": to, "cache_creation": tcw, "cache_read": tcr}
        if timing.get("reason"):
            entry["reason"] = timing["reason"]
        step_summary[sname] = entry

    # critical_code 抽出: validator_json_report (JSON) を優先、なければ
    # validator_report (md) からテキスト抽出する。fixer 後の最終 validator 結果が
    # 入る（残存 Critical のみ）。
    # NOTE: 旧実装は validator_report (md) を json.load で読んで毎回 except 握りつぶし
    # → critical_codes_seen が常に空になっていた。
    vp_json = state.outputs.get("validator_json_report")
    if vp_json and Path(vp_json).exists():
        try:
            with open(vp_json, encoding="utf-8") as f:
                vrep = json.load(f)
            for issue in vrep.get("issues", []) or []:
                if (issue.get("severity") or "").upper() != "CRITICAL":
                    continue
                code = issue.get("code") or issue.get("rule")
                if code and code not in critical_codes:
                    critical_codes.append(code)
        except Exception:
            pass
    else:
        # 後方互換: md レポートから "[C] [CODE]" 行を抽出
        vp_md = state.outputs.get("validator_report")
        if vp_md and Path(vp_md).exists():
            try:
                import re as _re
                text = Path(vp_md).read_text(encoding="utf-8")
                for m in _re.finditer(r"\[C\] \[([A-Z]+-[0-9]+[a-z]?)\]", text):
                    code = m.group(1)
                    if code not in critical_codes:
                        critical_codes.append(code)
            except Exception:
                pass

    # git head sha（feature branch 上で動いている前提）
    head_sha = ""
    try:
        code, out, _ = run_cmd(["git", "rev-parse", "HEAD"])
        if code == 0:
            head_sha = out.strip()
    except Exception:
        pass

    record = {
        "facility": state.facility,
        "flow": state.flow,
        "pattern": state.pattern,
        "started_at": state.started_at,
        "ended_at": state.ended_at or datetime.now().isoformat(),
        "duration_sec": round(tot_sec, 1),
        "unattended": state.unattended,
        "completed": state.current_step == "done" or True,  # commit step 到達時点で実質完走
        "tokens_total": {
            "input": tot_in,
            "output": tot_out,
            "cache_creation": tot_cw,
            "cache_read": tot_cr,
        },
        "step_summary": step_summary,
        "critical_codes_seen": critical_codes,
        "report_paths": {
            k: str(v) for k, v in (state.outputs or {}).items()
            if isinstance(v, str) and ("report" in k.lower() or "確認レポート" in str(v))
        },
        "git": {
            "feature_branch": state.branch_name,
            "head_sha": head_sha,
        },
        "schema_version": 1,
    }

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        log_info(f"run_history: {out_path.relative_to(PROJECT_DIR)}")
        return out_path
    except Exception as e:
        log_warn(f"run_history 書き出し失敗: {e}")
        return None


def step_git_commit(state: PipelineState) -> bool:
    """成果物をGitコミット（output/scenarios/{facility}_{flow}/ + docs/run_history/）"""
    scenario_dir = PROJECT_DIR / "output" / "scenarios" / f"{state.facility}_{state.flow}"
    if not scenario_dir.exists():
        log_warn(f"シナリオディレクトリが見つかりません: {scenario_dir}")
        return True

    # pipeline サマリを docs/run_history/ に書き出し（Curator 用 signal）
    history_path = _write_run_history(state)

    run_cmd(["git", "add", str(scenario_dir)])
    if history_path is not None:
        run_cmd(["git", "add", str(history_path)])

    msg = (
        f"[pipeline] {state.facility} {state.flow} "
        f"パターン{state.pattern} 生成・校閲・検品完了"
    )
    code, stdout, stderr = run_cmd(["git", "commit", "-m", msg])
    if code == 0:
        log_ok("Git commit 完了")
        return True

    if "nothing to commit" in stderr or "nothing to commit" in stdout:
        log_info("コミット対象の変更なし")
        return True

    log_error(f"Git commit 失敗: {stderr}")
    return False


def step_human_approval(state: PipelineState) -> bool:
    """人間に最終承認を求める（git push）"""
    if state.unattended:
        log_info("無人モード: Push をスキップ（ローカルコミットのみ）")
        if state.errors:
            log_warn(f"未解消の問題: {'; '.join(state.errors)}")
        return True

    gate = _load_test_gate(state)
    p7 = gate.get("p7", "未実施")
    p6 = gate.get("p6", "未実施")
    oracle = gate.get("oracle", "未実施")
    gate_ok = (str(oracle).startswith("PASS") and p7 == "PASS" and str(p6).startswith("PASS"))

    print(f"\n{C.BOLD}{'='*60}{C.RESET}")
    print(f"{C.BOLD}  パイプライン完了 -- 最終承認{C.RESET}")
    print(f"{'='*60}")
    print(f"  施設: {state.facility}")
    print(f"  フロー: {state.flow}")
    print(f"  パターン: {state.pattern}")
    print(f"  ブランチ: {state.branch_name}")
    print(f"  完成品ゲート: oracle={oracle} / P7={p7} / P6={p6}")
    print()
    print("  成果物:")
    for key, path in state.outputs.items():
        if Path(path).exists():
            size = Path(path).stat().st_size
            print(f"    {key}: {Path(path).name} ({size:,} bytes)")
    print(f"\n{'='*60}")

    if not gate_ok:
        log_warn("完成品ゲート未通過のため push は許可されません（ローカルコミットのみ）")
        log_info("実機テスト完了後に --resume p7_acceptance（または p6_gate）から再開してください")
        return True

    try:
        answer = input(f"\n{C.BOLD}Push to remote? [y/N]: {C.RESET}").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        answer = "n"

    if answer == "y":
        # リモートの存在確認
        code, stdout, _ = run_cmd(["git", "remote", "-v"])
        if not stdout.strip():
            log_warn("リモートが設定されていません。Push をスキップします")
            log_info("リモート設定後に手動で実行してください: git push -u origin " + state.branch_name)
            return True

        code, stdout, stderr = run_cmd(["git", "push", "-u", "origin", state.branch_name])
        if code == 0:
            log_ok(f"Push 完了: {state.branch_name}")
            # PR 作成（gh が使える場合）
            code, _, _ = run_cmd(["gh", "--version"])
            if code == 0:
                log_info("PR を作成中...")
                run_cmd([
                    "gh", "pr", "create",
                    "--title", f"[{state.facility}] {state.flow} フロー生成",
                    "--body", f"パターン{state.pattern}で生成。orchestrator.py による自動パイプライン。",
                ])
            return True
        else:
            log_error(f"Push 失敗: {stderr}")
            return False
    else:
        log_info("Push をスキップしました")
        return True

# ---------------------------------------------------------------------------
# パイプライン定義
# ---------------------------------------------------------------------------

PIPELINE_STEPS = {
    1: [  # 新規作成
        ("branch",       "ブランチ作成",                 step_create_branch),
        ("director",     "Director: 設計書生成",          step_director),
        ("qa",           "QA: 設計書レビュー",             None),  # special handling
        ("copy_subflows", "サブフローJSONコピー",           step_copy_subflows),
        ("scaffold",     "Scaffold: JSON骨格自動生成",    step_scaffold_generator),
        ("gen_scripts",  "Scripts: ES5コード自動生成",    step_gen_scripts),
        ("layout",       "Layout: レイアウト計算",         step_layout_calculator),
        ("generator",    "Generator: JSON生成/パッチ",    step_generator),
        ("prompter_props", "Prompter + Properties 並列",  step_parallel_prompter_properties),
        # [退役 2026-06-24] reviewer ステップは keystone により除去（校閲は壁打ち時に out-of-line で実施）
        ("merge",        "Merge: 統合",                   step_merge),
        ("validator",    "Validator: Final",               None),
        ("add_date",     "日付サフィックス記録（bivr名・name変更なし）", step_add_date_suffix),
        ("tester_build",      "Tester + Build 並列",            step_parallel_tester_build),
        ("auto_fixer",   "AutoFixer: 機械的修正 (トークン不要)", step_auto_fixer_post_test),
        # [退役 2026-06-24] fixer ステップは keystone により除去（残存 Critical は人間壁打ちへ・step_fixer は no-op）

        ("collect_scenario",  "成果物集約",                   step_collect_scenario),
        ("phonebook_csv",     "Dr.JOY 電話帳 CSV 生成",         step_gen_phonebook_csv),
        ("commit",            "Git: コミット",                step_git_commit),
        ("oracle_gate",       "Oracle: Script部品オラクル受入",  step_oracle_gate),
        ("p7_gen",            "Pattern 7: 連結テスト生成",       step_p7_generate),
        ("p7_acceptance",     "Human: P7 実機実行（結合）",      step_p7_acceptance),
        ("p6_gate",           "Pattern 6: 認定照合+単体受入",    step_p6_gate),
        ("commit_evidence",   "Git: テスト証跡コミット",         step_commit_evidence),
        ("score_gate",        "4層採点ゲート（成績表出力＋出荷可否）", step_score_gate),
        ("approve",      "Human: 最終承認",               step_human_approval),
    ],
    2: [  # 既存修正（fixer-first ライトウェイト + リフレッシュモード対応）
        ("branch",           "ブランチ作成",                        step_create_branch),
        ("extract_bivr",     "BIVR展開: .bivr → JSON",             step_extract_bivr),
        ("extract_scaffold", "ScaffoldExtractor: 既存JSONから scenario_flow 抽出", step_scaffold_extractor),
        ("dirlite",          "DirLite: モード判定 + 差分指示書 or リフレッシュ指示書生成",   step_dirlite),
        ("pattern2_apply",   "Pattern 2: モードに応じて修正/リフレッシュ実行", step_pattern2_apply),
        ("format_prompt",    "プロンプト改行正規化",                   step_format_prompt_strings),
        ("properties",       "Properties: JSON inline prompt から抽出", step_properties_from_json),
        ("validator_p2",     "Validator: 修正後チェック",              step_validator_modify),
        ("tester_build",     "Tester + Build 並列",                 step_parallel_tester_build),
        ("auto_fixer",       "AutoFixer: 機械的修正 (トークン不要)",   step_auto_fixer_post_test),
        ("collect_scenario", "成果物集約",                            step_collect_scenario),
        ("phonebook_csv",    "Dr.JOY 電話帳 CSV 生成",                step_gen_phonebook_csv),
        # [退役 2026-06-24] reviewer ステップは keystone により除去（校閲は壁打ち時に out-of-line で実施）
        # [退役 2026-06-24] fixer ステップは keystone により除去（残存 Critical は人間壁打ちへ）
        ("commit",           "Git: コミット",                        step_git_commit),
        ("oracle_gate",      "Oracle: Script部品オラクル受入",         step_oracle_gate),
        ("p7_gen",           "Pattern 7: 連結テスト生成",              step_p7_generate),
        ("p7_acceptance",    "Human: P7 実機実行（結合）",             step_p7_acceptance),
        ("p6_gate",          "Pattern 6: 認定照合+単体受入",           step_p6_gate),
        ("commit_evidence",  "Git: テスト証跡コミット",                step_commit_evidence),
        ("score_gate",       "4層採点ゲート（成績表出力＋出荷可否）",   step_score_gate),
        ("approve",          "Human: 最終承認",                      step_human_approval),
    ],
    3: [  # Gen2→Gen3
        ("branch",       "ブランチ作成",                 step_create_branch),
        ("director",     "Director: 設計書生成",          step_director),
        ("qa",           "QA: 設計書レビュー",             None),
        ("copy_subflows", "サブフローJSONコピー",           step_copy_subflows),
        ("scaffold",     "Scaffold: JSON骨格自動生成",    step_scaffold_generator),
        ("gen_scripts",  "Scripts: ES5コード自動生成",    step_gen_scripts),
        ("layout",       "Layout: レイアウト計算",         step_layout_calculator),
        ("generator",    "Generator: JSON生成/パッチ",    step_generator),
        ("prompter_props", "Prompter + Properties 並列",  step_parallel_prompter_properties),
        # [退役 2026-06-24] reviewer ステップは keystone により除去（校閲は壁打ち時に out-of-line で実施）
        ("merge",        "Merge: 統合",                   step_merge),
        ("validator",    "Validator: Final",               None),
        ("add_date",     "日付サフィックス記録（bivr名・name変更なし）", step_add_date_suffix),
        ("tester_build",      "Tester + Build 並列",            step_parallel_tester_build),
        ("auto_fixer",   "AutoFixer: 機械的修正 (トークン不要)", step_auto_fixer_post_test),
        # [退役 2026-06-24] fixer ステップは keystone により除去（残存 Critical は人間壁打ちへ・step_fixer は no-op）

        ("collect_scenario",  "成果物集約",                   step_collect_scenario),
        ("phonebook_csv",     "Dr.JOY 電話帳 CSV 生成",         step_gen_phonebook_csv),
        ("commit",            "Git: コミット",                step_git_commit),
        ("oracle_gate",       "Oracle: Script部品オラクル受入",  step_oracle_gate),
        ("p7_gen",            "Pattern 7: 連結テスト生成",       step_p7_generate),
        ("p7_acceptance",     "Human: P7 実機実行（結合）",      step_p7_acceptance),
        ("p6_gate",           "Pattern 6: 認定照合+単体受入",    step_p6_gate),
        ("commit_evidence",   "Git: テスト証跡コミット",         step_commit_evidence),
        ("score_gate",        "4層採点ゲート（成績表出力＋出荷可否）", step_score_gate),
        ("approve",      "Human: 最終承認",               step_human_approval),
    ],
    4: [  # Gen1→Gen3
        ("branch",       "ブランチ作成",                 step_create_branch),
        ("director",     "Director: 設計書生成",          step_director),
        ("qa",           "QA: 設計書レビュー",             None),
        ("copy_subflows", "サブフローJSONコピー",           step_copy_subflows),
        ("scaffold",     "Scaffold: JSON骨格自動生成",    step_scaffold_generator),
        ("gen_scripts",  "Scripts: ES5コード自動生成",    step_gen_scripts),
        ("layout",       "Layout: レイアウト計算",         step_layout_calculator),
        ("generator",    "Generator: JSON生成/パッチ",    step_generator),
        ("prompter_props", "Prompter + Properties 並列",  step_parallel_prompter_properties),
        # [退役 2026-06-24] reviewer ステップは keystone により除去（校閲は壁打ち時に out-of-line で実施）
        ("merge",        "Merge: 統合",                   step_merge),
        ("validator",    "Validator: Final",               None),
        ("add_date",     "日付サフィックス記録（bivr名・name変更なし）", step_add_date_suffix),
        ("tester_build",      "Tester + Build 並列",            step_parallel_tester_build),
        ("auto_fixer",   "AutoFixer: 機械的修正 (トークン不要)", step_auto_fixer_post_test),
        # [退役 2026-06-24] fixer ステップは keystone により除去（残存 Critical は人間壁打ちへ・step_fixer は no-op）

        ("collect_scenario",  "成果物集約",                   step_collect_scenario),
        ("phonebook_csv",     "Dr.JOY 電話帳 CSV 生成",         step_gen_phonebook_csv),
        ("commit",            "Git: コミット",                step_git_commit),
        ("oracle_gate",       "Oracle: Script部品オラクル受入",  step_oracle_gate),
        ("p7_gen",            "Pattern 7: 連結テスト生成",       step_p7_generate),
        ("p7_acceptance",     "Human: P7 実機実行（結合）",      step_p7_acceptance),
        ("p6_gate",           "Pattern 6: 認定照合+単体受入",    step_p6_gate),
        ("commit_evidence",   "Git: テスト証跡コミット",         step_commit_evidence),
        ("score_gate",        "4層採点ゲート（成績表出力＋出荷可否）", step_score_gate),
        ("approve",      "Human: 最終承認",               step_human_approval),
    ],
    11: [  # P1+1 新規作成（トークン節約版）: flow-draft MD → スケルトン → Sonnet 補完 → scaffold以降はP1と同じ
        ("branch",         "ブランチ作成",                       step_create_branch),
        ("yaml_scaffold",  "YAMLスケルトン生成 (flow-draft→骨格)", step_yaml_scaffold),
        ("yaml_fill",      "Sonnet: PLACEHOLDERを補完→完成YAML",  step_yaml_fill),
        ("qa",             "QA: 設計書レビュー",                  None),  # special handling
        ("copy_subflows",  "サブフローJSONコピー",                 step_copy_subflows),
        ("scaffold",       "Scaffold: JSON骨格自動生成",          step_scaffold_generator),
        ("gen_scripts",    "Scripts: ES5コード自動生成",          step_gen_scripts),
        ("layout",         "Layout: レイアウト計算",               step_layout_calculator),
        ("generator",      "Generator: JSON生成/パッチ",          step_generator),
        ("prompter_props", "Prompter + Properties 並列",          step_parallel_prompter_properties),
        # [退役 2026-06-24] reviewer ステップは keystone により除去（校閲は壁打ち時に out-of-line で実施）
        ("merge",          "Merge: 統合",                         step_merge),
        ("validator",      "Validator: Final",                    None),
        ("add_date",       "日付サフィックス記録（bivr名・name変更なし）", step_add_date_suffix),
        ("tester_build",   "Tester + Build 並列",                 step_parallel_tester_build),
        ("auto_fixer",     "AutoFixer: 機械的修正 (トークン不要)", step_auto_fixer_post_test),
        # [退役 2026-06-24] fixer ステップは keystone により除去（残存 Critical は人間壁打ちへ）

        ("collect_scenario",  "成果物集約",                       step_collect_scenario),
        ("phonebook_csv",     "Dr.JOY 電話帳 CSV 生成",            step_gen_phonebook_csv),
        ("commit",            "Git: コミット",                    step_git_commit),
        ("oracle_gate",       "Oracle: Script部品オラクル受入",    step_oracle_gate),
        ("p7_gen",            "Pattern 7: 連結テスト生成",         step_p7_generate),
        ("p7_acceptance",     "Human: P7 実機実行（結合）",        step_p7_acceptance),
        ("p6_gate",           "Pattern 6: 認定照合+単体受入",      step_p6_gate),
        ("commit_evidence",   "Git: テスト証跡コミット",           step_commit_evidence),
        ("score_gate",        "4層採点ゲート（成績表出力＋出荷可否）", step_score_gate),
        ("approve",           "Human: 最終承認",                  step_human_approval),
    ],
    6: [  # テストフロー生成 (Brekeke モジュール動作検証用、OpenAI/STT 不要の最小構成)
        # NOTE: 動作確認フェーズ中は branch/commit を外している (現ブランチで走らせるため)
        # 安定後に step_create_branch / step_git_commit を再有効化する
        ("test_scaffold",   "Test Scaffold: テスト用JSON生成", step_test_scaffold_generator),
        ("layout",          "Layout: レイアウト計算",       step_layout_calculator),
        ("add_date",        "日付サフィックス記録（bivr名・name変更なし）", step_add_date_suffix),
        ("build",           "Build: .bivr 生成",            step_build_bivr),
        ("collect_scenario","成果物集約",                   step_collect_scenario),
    ],
}


PATCH_BOX_DIR = PROJECT_DIR / ".claude" / "patch_box"


def _load_patch_box_current() -> list[tuple[str, str]]:
    """.claude/patch_box/current/*.md を読み込み、(filename, content) のリストを返す。

    `.gitkeep` 等の隠しファイルや非 .md ファイルは無視。
    PATCH_BOX 構想 Phase 1: 現在は `current/` のみ参照、`per_facility/` `per_phase/` は
    Phase 2 以降で追加予定。
    """
    current_dir = PATCH_BOX_DIR / "current"
    if not current_dir.is_dir():
        return []
    items: list[tuple[str, str]] = []
    for fp in sorted(current_dir.glob("*.md")):
        if fp.name.startswith("."):
            continue
        try:
            content = fp.read_text(encoding="utf-8").strip()
        except Exception:
            continue
        if content:
            items.append((fp.name, content))
    return items


def _archive_patch_box_consumed(items: list[tuple[str, str]]) -> None:
    """current/ の patch を consumed/{timestamp}_{filename} へ移送して current/ を空にする。"""
    if not items:
        return
    consumed_dir = PATCH_BOX_DIR / "consumed"
    consumed_dir.mkdir(parents=True, exist_ok=True)
    current_dir = PATCH_BOX_DIR / "current"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    for fname, _ in items:
        src = current_dir / fname
        if not src.exists():
            continue
        dst = consumed_dir / f"{ts}_{fname}"
        try:
            src.rename(dst)
        except Exception as e:
            log_warn(f"PATCH_BOX archive 失敗 ({fname}): {e}")
    log_info(f"PATCH_BOX: {len(items)} 件を consumed/ へアーカイブしました")


def run_pipeline(state: PipelineState, dry_run: bool = False):
    """パイプラインを実行"""
    steps = PIPELINE_STEPS.get(state.pattern)
    if not steps:
        log_error(f"不明なパターン: {state.pattern}")
        sys.exit(1)

    # ── PATCH_BOX 読み込み ─────────────────────────────────────────────
    # `.claude/patch_box/current/*.md`（gitignore・ローカル専用）を集約。各 Agent は
    # CLAUDE.md 経由で「PATCH_BOX は agents より優先（ただし CLAUDE.md の恒久ルールは
    # 上書きしない）」と指示されているので、環境変数 VFB_PATCH_BOX_CONTEXT に設定するだけで
    # 自動反映される。ファイルはローカル filesystem から読むため git 追跡の有無と無関係。
    patch_box_items = _load_patch_box_current() if not dry_run else []
    if patch_box_items:
        log_info(f"PATCH_BOX: {len(patch_box_items)} 件の動的指示を検出")
        for fname, _ in patch_box_items:
            log_info(f"  - {fname}")
        combined = "\n\n---\n\n".join(
            f"## PATCH_BOX entry: {fname}\n\n{content}" for fname, content in patch_box_items
        )
        os.environ["VFB_PATCH_BOX_CONTEXT"] = combined
    else:
        os.environ.pop("VFB_PATCH_BOX_CONTEXT", None)

    # spec ファイル内の参照パス（元資料・移管ノート等）の実在チェック
    # 福岡徳洲会_リハビリ (2026-04-27) で元資料パス誤記による事故を踏まえ、
    # director に投げる前に早期失敗させる（--resume 時も毎回チェック）
    if state.spec_path and not dry_run:
        validator = PROJECT_DIR / "scripts" / "reference_validator.py"
        if validator.exists():
            check = subprocess.run(
                [sys.executable, str(validator), "--quiet", state.spec_path],
                cwd=str(PROJECT_DIR),
                capture_output=True, text=True,
                encoding="utf-8", errors="replace",
            )
            if check.returncode != 0:
                log_error(f"spec 内の参照パスに不在ファイルあり: {state.spec_path}")
                if check.stderr:
                    for line in check.stderr.rstrip().splitlines():
                        log_error(f"  {line}")
                log_error("ノートのパス記述を実ファイル名に揃えてから再実行してください")
                sys.exit(1)

    state.started_at = datetime.now().isoformat()
    total = len(steps)

    # --resume: current_step 以降から再開
    start_idx = 0
    if state.current_step != "init":
        valid_ids = [s[0] for s in steps]
        found = False
        for i, (step_id, _, _) in enumerate(steps):
            if step_id == state.current_step:
                start_idx = i
                found = True
                break
        if not found:
            log_error(
                f"再開ステップ '{state.current_step}' がパターン {state.pattern} のステップ一覧に存在しません。\n"
                f"有効なステップ名: {', '.join(valid_ids)}\n"
                f"--resume-step で正しいステップ名を指定してください。"
            )
            sys.exit(1)
        log_info(f"ステップ '{state.current_step}' から再開")

    print(f"\n{C.BOLD}{'='*60}{C.RESET}")
    print(f"{C.BOLD}  VoiceBot Flow Builder -- パイプライン実行{C.RESET}")
    print(f"{'='*60}")
    print(f"  パターン: {state.pattern}")
    print(f"  施設: {state.facility}")
    print(f"  フロー: {state.flow}")
    print(f"  設計書: {state.spec_path}")
    if state.base_path:
        print(f"  ベース: {state.base_path}")
    print(f"  担当: {state.assignee}")
    print(f"  ステップ数: {total}")
    if state.skip_qa:
        print(f"  QA: スキップ")
    if state.skip_tester:
        print(f"  Tester: スキップ")
    print(f"{'='*60}\n")

    if dry_run:
        print(f"{C.BOLD}[DRY RUN] パイプラインステップ一覧:{C.RESET}\n")
        for i, (step_id, desc, _) in enumerate(steps, 1):
            skip = ""
            if step_id == "qa" and state.skip_qa:
                skip = " (SKIP)"
            elif step_id == "tester" and state.skip_tester:
                skip = " (SKIP)"
            print(f"  {i:2d}. [{step_id:12s}] {desc}{skip}")
        print(f"\n{C.BOLD}[DRY RUN] 実際の実行はされません{C.RESET}")
        return

    for i, (step_id, desc, func) in enumerate(steps[start_idx:], start_idx + 1):
        state.current_step = step_id
        state.save()

        log_step(f"Step {i}/{total}", desc)

        # スキップ判定
        if step_id == "qa" and state.skip_qa:
            log_info("QA スキップ (--skip-qa)")
            state.step_timings[step_id] = {"status": "skip", "seconds": 0}
            continue
        if step_id == "tester" and state.skip_tester:
            log_info("Tester スキップ (--skip-tester)")
            state.step_timings[step_id] = {"status": "skip", "seconds": 0}
            continue

        step_start = datetime.now()
        _reset_token_acc()  # このステップのトークン累積をリセット
        # ステップ開始時点で "running" + started_at を記録
        # → 途中kill・長時間停止時に外部から経過時間を計算可能
        state.step_timings[step_id] = {
            "status": "running",
            "seconds": 0,
            "started_at": step_start.isoformat(),
        }
        state.save()

        # 特殊ステップの処理
        success = False
        if step_id == "qa":
            success = step_qa(state)
        elif step_id == "validator":
            final_json = state.outputs.get("merged_json") or state.outputs.get("prompted_json", "")
            if final_json:
                # 結果に関わらずパイプラインを継続。Critical はレポートに保存して fixer が後処理
                step_validator(state, final_json, report_key="validator_report")
                success = True
            else:
                log_error("最終JSONが見つかりません")
        elif func:
            success = func(state)
        else:
            log_warn(f"ステップ {step_id} の実行関数が未定義")
            success = True

        step_elapsed = (datetime.now() - step_start).total_seconds()
        timing: dict = {
            "status": "ok" if success else "fail",
            "seconds": round(step_elapsed, 1),
            "started_at": step_start.isoformat(),
        }
        # トークン使用量を記録（invoke_agent 経由のステップのみ）
        tok = _get_token_acc()
        if tok:
            timing["tokens"] = tok
        # 失敗原因を記録（トークン枯渇 / タイムアウト / その他）
        if not success:
            err_text = " ".join(state.errors[-3:]) if state.errors else ""
            if detect_token_exhaustion(err_text, ""):
                timing["reason"] = "token_exhausted"
            elif step_elapsed >= STEP_TIMEOUTS.get(step_id, AGENT_TIMEOUT) - 10:
                timing["reason"] = "timeout"
            else:
                timing["reason"] = "agent_error"
        state.step_timings[step_id] = timing
        # ログ表示: 所要時間 + トークン使用量
        tok_summary = ""
        if tok:
            effective_in = tok["input"] + tok["cache_read"]
            tok_summary = (
                f"  入力:{effective_in:,} 出力:{tok['output']:,} "
                f"キャッシュ:{tok['cache_read']:,} ${tok['cost_usd']:.4f}"
            )
        log_info(f"  ⏱ {desc}: {int(step_elapsed // 60)}分{int(step_elapsed % 60)}秒{tok_summary}")

        if not success:
            log_error(f"ステップ '{step_id}' で失敗。パイプラインを停止します。")
            state.ended_at = datetime.now().isoformat()
            state.save()
            print(f"\n{C.YELLOW}再開するには:{C.RESET}")
            print(f"  python3 scripts/orchestrator.py --resume")
            sys.exit(1)

    # 完了
    state.current_step = "done"
    state.ended_at = datetime.now().isoformat()
    state.save()

    # ── PATCH_BOX を consumed/ へアーカイブ ──────────────────────────────
    _archive_patch_box_consumed(patch_box_items)

    total_elapsed = (datetime.fromisoformat(state.ended_at) - datetime.fromisoformat(state.started_at)).total_seconds()

    print(f"\n{C.BOLD}{C.GREEN}{'='*60}{C.RESET}")
    print(f"{C.BOLD}{C.GREEN}  パイプライン完了{C.RESET}")
    print(f"{C.GREEN}{'='*60}{C.RESET}")
    print(f"\n{C.BOLD}  ⏱ 合計所要時間: {int(total_elapsed // 60)}分{int(total_elapsed % 60)}秒{C.RESET}")

    # ─── ステップ別サマリー ───────────────────────────────────────
    total_input = total_output = total_cache = 0
    total_cost = 0.0
    print(f"\n  {'ステップ':<16s}  {'結果':<4s}  {'時間':>8s}  {'入力tok':>10s}  {'出力tok':>10s}  {'キャッシュ':>10s}  {'コスト':>8s}")
    print(f"  {'-'*16}  {'-'*4}  {'-'*8}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*8}")
    for sid, timing in state.step_timings.items():
        if timing["status"] == "skip":
            print(f"  {sid:<16s}  SKIP")
            continue
        mark = "✓" if timing["status"] == "ok" else "✗"
        secs = timing["seconds"]
        time_str = f"{int(secs // 60)}分{int(secs % 60):02d}秒"
        tok = timing.get("tokens", {})
        if tok:
            eff_in = tok["input"] + tok["cache_read"]
            out    = tok["output"]
            cache  = tok["cache_read"]
            cost   = tok["cost_usd"]
            total_input  += eff_in
            total_output += out
            total_cache  += cache
            total_cost   += cost
            print(f"  {sid:<16s}  {mark}     {time_str:>8s}  {eff_in:>10,}  {out:>10,}  {cache:>10,}  ${cost:>7.4f}")
        else:
            print(f"  {sid:<16s}  {mark}     {time_str:>8s}")
    print(f"  {'-'*16}  {'':4s}  {'':8s}  {'-'*10}  {'-'*10}  {'-'*10}  {'-'*8}")
    if total_input + total_output > 0:
        print(
            f"  {'合計（AIステップ）':<16s}  {'':4s}  {'':8s}  "
            f"{total_input:>10,}  {total_output:>10,}  {total_cache:>10,}  ${total_cost:>7.4f}"
        )

    # ─── 修正レポートのパスを最後に表示 ─────────────────────────────
    fixer_report = state.outputs.get("fixer_report", "")
    if fixer_report:
        rel = Path(fixer_report).relative_to(PROJECT_DIR) if Path(fixer_report).is_absolute() else fixer_report
        print(f"\n{C.BOLD}  📋 修正レポート: {rel}{C.RESET}")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="VoiceBot Flow Builder パイプラインオーケストレーター",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
パターン:
  1  新規作成    director → qa → generator → prompter+reviewer → validator → tester → build → P7連結(実機) → P6単体(認定照合)
  2  既存修正    dirlite → fixer(修正) → validator → tester+build → reviewer → fixer(Critical残存) → P7連結 → P6単体
  3  Gen2→Gen3  director → qa → generator → prompter+reviewer → validator → tester → build → P7連結 → P6単体
  4  Gen1→Gen3  director → qa → generator → prompter+reviewer → validator → tester → build → P7連結 → P6単体
  11 P1+1(節約)  flow-draft MD → スケルトン生成 → Sonnet補完 → qa → scaffold → prompter → validator → tester → P7連結 → P6単体
注: 完成品ゲート = oracle PASS + P7 実機 PASS + P6 認定（ハッシュ一致 or 実機 PASS）。未通過は push 不可
注: パターン3/4では --spec に docs/migration/gen2_*.txt または gen1_*.html を渡すこと
注: パターン11では --spec に flow-draft MD または customer_doc を渡す。flow_draft_*.md が scenario dir に必要
        """,
    )
    parser.add_argument("--pattern", type=int, choices=[1, 2, 3, 4, 6, 11], help="作業パターン (1-4, 6=テストフロー生成, 11=P1+1トークン節約版)")
    parser.add_argument("--spec", type=str, help="設計書パス")
    parser.add_argument("--base", type=str, default="", help="ベース .bivr パス (パターン2)")
    parser.add_argument("--assignee", type=str, default="hamaguchi", help="担当者名")
    parser.add_argument("--env", type=str, default="demo", choices=["demo", "prod"], help="環境")
    parser.add_argument("--resume", action="store_true", help="最後のチェックポイントから再開")
    parser.add_argument("--resume-state", type=str, help="特定の状態ファイルから再開 (例: output/scenarios/{施設}_{flow}/pipeline_state_xxx.json)")
    parser.add_argument("--resume-step", type=str, help="resume 時に current_step を上書きして指定ステップから再開 (例: scaffold, prompter_props, fixer)")
    parser.add_argument("--skip-qa", action="store_true", help="QAステップをスキップ")
    parser.add_argument("--skip-tester", action="store_true", help="Testerステップをスキップ")
    parser.add_argument("--clean-legacy", action="store_true",
                        help="Pattern 2: base の legacy Critical も含めて修正する（既定: dirlite touched ブロックのみ scope）")
    parser.add_argument("--dry-run", action="store_true", help="実行せずにステップ一覧を表示")
    parser.add_argument("--unattended", action="store_true", help="無人モード: 最終Push確認をスキップしてローカルコミットのみで完走")
    parser.add_argument("--allow-director-llm", action="store_true",
                        help="設計書 YAML が無い場合に director LLM の自動起草を許可する（既定: 無効。決定論入口 /sparring-intake で YAML を作る）")

    args = parser.parse_args()

    # --resume-state モード（特定ファイル指定）
    if args.resume_state:
        state_path = args.resume_state
        if not Path(state_path).exists():
            # output/ 直下も試みる
            state_path = str(PROJECT_DIR / "output" / args.resume_state)
        if not Path(state_path).exists():
            log_error(f"状態ファイルが見つかりません: {args.resume_state}")
            sys.exit(1)
        state = PipelineState.load(state_path)
        if args.resume_step:
            state.current_step = args.resume_step
            log_info(f"再開ステップを上書き: {args.resume_step}")
        log_info(f"パイプライン再開: {state.facility}_{state.flow} (step: {state.current_step})")
        if state.unattended:
            log_info("無人モード: Push自動スキップ")
        run_pipeline(state, dry_run=args.dry_run)
        return

    # --resume モード
    if args.resume:
        state = PipelineState.find_latest()
        if state is None:
            log_error("再開可能なパイプライン状態が見つかりません")
            sys.exit(1)
        if args.resume_step:
            state.current_step = args.resume_step
            log_info(f"再開ステップを上書き: {args.resume_step}")
        log_info(f"パイプライン再開: {state.facility}_{state.flow} (step: {state.current_step})")
        if state.unattended:
            log_info("無人モード: Push自動スキップ")
        run_pipeline(state, dry_run=args.dry_run)
        return

    # 通常モード: --pattern が必須。--spec は Pattern 2（BIVR のみ）では省略可
    if not args.pattern:
        parser.error("--pattern は必須です（--resume を使う場合を除く）")
    if not args.spec and args.pattern not in (2, 11):
        parser.error("--spec は必須です（Pattern 2 で --base のみ指定する場合を除く）")
    if not args.spec and args.pattern == 11:
        log_warn("Pattern 11: --spec 未指定。flow_draft_*.md をシナリオディレクトリから自動検索します")
    if not args.spec and args.pattern == 2 and not args.base:
        parser.error("Pattern 2 では --spec または --base のいずれかが必要です")

    if args.spec and not Path(args.spec).exists():
        log_error(f"設計書が見つかりません: {args.spec}")
        sys.exit(1)

    # Pattern 2: --spec を優先、flow が "main"（= _ を含まない）の場合は --base から再導出
    if args.pattern == 2:
        if args.base and not Path(args.base).exists():
            log_error(f"既存JSONが見つかりません: {args.base}")
            sys.exit(1)
        if args.spec:
            facility, flow = extract_names(args.spec)
            if flow == "main" and args.base:
                facility, flow = extract_names(args.base)
        elif args.base:
            facility, flow = extract_names(args.base)
        else:
            facility, flow = ("unknown", "main")
    else:
        facility, flow = extract_names(args.spec)

    state = PipelineState(
        pattern=args.pattern,
        facility=facility,
        flow=flow,
        assignee=args.assignee,
        spec_path=args.spec or "",
        base_path=args.base or "",
        environment=args.env,
        skip_qa=args.skip_qa,
        skip_tester=args.skip_tester,
        clean_legacy=args.clean_legacy,
        unattended=args.unattended,
        allow_director_llm=args.allow_director_llm,
    )

    run_pipeline(state, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
