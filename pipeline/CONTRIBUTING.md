# CONTRIBUTING — 共同運用ルール（人間向け）

voicebot-flow-builder を複数メンバーで運用するためのルール。
Claude Code エージェント向けの恒久ルールは `CLAUDE.md`（このファイルとセットで読む）。

## TL;DR

1. **触ってよいのは `output/scenarios/{施設}_{flow}/` 配下だけ**（自由ゾーン）
2. **全変更は feature ブランチ → PR**。master へ直 push しない
3. それ以外のパス = **保護ゾーン**。変更したい場合も PR は出してよいが、
   @TS-dong-nc のレビューが必須で、**マージも @TS-dong-nc が行う**
4. **依存追加・ツールインストール禁止**（必要なら相談）
5. **secret は絶対にコミットしない**

## ゾーン定義（allowlist 方式）

### 自由ゾーン

| パス | 内容 |
|---|---|
| `output/scenarios/{施設}_{flow}/` | シナリオ成果物一式（YAML / bivr / レポート / properties）と顧客資料（`reference/`） |

### 保護ゾーン（自由ゾーン以外すべて）

| パス | 守る理由 |
|---|---|
| `CLAUDE.md` / `.claude/` | エージェントの憲法・権限設定（settings.json の deny rules）・agent prompts |
| `.github/` | CODEOWNERS / ガード workflow 自体 |
| `scripts/` `schemas/` `tools/` | validator / scaffold / orchestrator 等の検品ゲート本体 |
| `docs/ai/skills/` `docs/brekeke/` | プロンプト品質・モジュール選定の SSoT |
| `.gitignore` `requirements.txt` | secret 除外・依存固定 |

## ブランチ / PR 運用

- ブランチ名: `feature/{施設名}_{フロー名}`（orchestrator が自動作成するものに準拠）
- 自由ゾーンのみの PR: コードオーナーレビュー不要。そのままマージ可
- 保護ゾーンを 1 ファイルでも含む PR: CODEOWNERS によりレビュー必須 + **マージは @TS-dong-nc**
  - 非オーナーが保護ゾーン入りの push を master に載せると `guard-master.yml` が自動で push 前の状態へ復元する
- force-push 禁止。master への push ごとに `backup/<timestamp>` タグが自動作成される（ロールバック用）

## 環境・依存

- `pip install` / `npm install` 等のインストールは全環境で禁止（Claude にも人間にも適用）
- `requirements.txt` への依存追加は @TS-dong-nc 承認制
- ツール不足時は相談（マネージャーが手動セットアップ）

## 顧客情報・secret

- 顧客資料は `output/scenarios/{施設}_{flow}/reference/` へ
- `.env` / `.server_auth.json` / `*.key` / credentials はコミット禁止（.gitignore 済み。`git add -f` での強制追加も禁止）
- 本リポジトリには病院名・設計書等の顧客情報が含まれる。リポジトリへのアクセス権自体を社外秘として扱う

## Claude Code を使う場合

- `CLAUDE.md` / `.claude/` 配下を変更させない（変更案が出たら PR で提案）
- `.claude/patch_box/current/*.md` はローカル専用（git 管理外）。CLAUDE.md より優先される動的指示の仕組みのため、リポジトリ経由で共有しない
