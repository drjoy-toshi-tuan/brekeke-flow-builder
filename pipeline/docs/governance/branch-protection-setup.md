# ブランチ保護セットアップ手順（Team プラン有効化後）

allowlist 方式（CODEOWNERS + guard-master.yml）の本命の enforcement はブランチ保護。
Team プラン有効化後、この手順で設定する。

## 0. 前提: Team プランは organization 用

GitHub Team は org プラン。個人アカウント (TS-dong-nc) のままでは private repo にブランチ保護を掛けられない。

1. org を作成し Team プランを適用
2. 本リポジトリを org へ Transfer（Settings → Danger Zone → Transfer ownership）
   - 旧 URL からのリダイレクトは自動で張られるが、以下は順次更新する:
     - 各メンバーのローカル clone の remote URL
     - `start_ui.py` の `REPO_URL`（個人 repo URL がハードコードされている）
     - push-watchdog 等、リポジトリ URL を参照する自動化
3. メンバーは **Write 権限**で追加（Admin は不可）

## 1. master のブランチ保護（Settings → Branches または Rulesets）

- [ ] Require a pull request before merging: **ON**
  - Required approvals: **0**（シナリオ PR をレビュー無しで回すため）
  - Require review from Code Owners: **ON** ← これが allowlist の本体
- [ ] Block force pushes: **ON**
- [ ] Restrict deletions: **ON**
- [ ] (Rulesets の場合) Bypass list に **repo admin + github-actions** を追加
  ← guard-master の自動復元 push と、オーナーの master 直 push（従来規約）を通すため
  - classic branch protection の場合は "Do not allow bypassing the above settings" を **OFF**

## 2. 動作確認チェックリスト

- [ ] テスト用アカウントで `output/scenarios/` のみの PR → レビュー無しでマージできる
- [ ] 保護パス（例: `scripts/` 配下）を含む PR → Code Owner レビューが要求される
- [ ] 非オーナーの master 直 push → 拒否される
- [ ] 保護パス PR を非オーナーがマージ → guard-master が復元する（仕様。保護パス PR はオーナーがマージする運用）

## 3. バックログ（任意）

- [ ] `tests/` を required status check 化（CI workflow 追加後）
- [ ] secret 混入チェック CI（private repo の GitHub push protection は GHAS が必要なため、SHA 固定の gitleaks 等で代替）
- [ ] CLAUDE.md「成果物の置き場所」冒頭の「GitHub が個人アカウントのため…」記述を org 移管後に更新
