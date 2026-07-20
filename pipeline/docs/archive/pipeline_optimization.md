# パイプライン最適化設計

> 目標: 1シナリオあたり30分〜最大1時間30分で完了
> 現状推定: director(10分) + generator(15分) + prompter(15分) + reviewer(25-30分) + validator(数秒) = 65-70分（ループなし時）

---

## 施策1: 並列化（generator → prompter + reviewer を同時実行）

### 現状（直列）

```
generator → prompter → reviewer → validator → build_bivr
 15分        15分       25-30分     数秒        数秒
                                              合計: 55-60分
```

### 最適化後（並列）

```
generator ──┬── prompter（prompt記述）     15分
            └── reviewer（構造校閲のみ）   15-20分（観点削減後）
                     ↓ 両方完了後
               マージ（prompter出力をreview済みJSONに統合）  1-2分
                     ↓
               validator（最終検証）  数秒
                     ↓
               build_bivr  数秒
                                              合計: 30-35分
```

**効果**: 15分短縮（prompterとreviewer構造校閲が並列実行）

### 実装方法

PLエージェントのパイプライン実行部分を以下のように変更:

```bash
# 並列実行（Claude Codeの Task 機能を使用）
# Task 1: prompter
@prompter output/draft_〇〇病院_診療.json のOpenAIプロンプトを記述して

# Task 2: reviewer（構造校閲のみ — プロンプト校閲はスキップ）
@reviewer output/draft_〇〇病院_診療.json を構造校閲して（プロンプト内容チェックはスキップ）

# 両方完了後: マージ
# prompterの出力（prompt入りJSON）に、reviewerの構造修正を適用
python3 -c "
import json
# prompter output (prompt filled)
with open('output/draft_prompted_xxx.json') as f:
    prompted = json.load(f)
# reviewer output (structure fixed)  
with open('output/reviewed_xxx.json') as f:
    reviewed = json.load(f)
# マージ: reviewerの構造修正をベースに、prompterのpromptを上書き
for mod_name, mod in prompted['modules'].items():
    if 'generate_by_OpenAI' in mod.get('type', ''):
        if mod.get('params', {}).get('prompt'):
            reviewed['modules'][mod_name]['params']['prompt'] = mod['params']['prompt']
with open('output/reviewed_xxx.json', 'w') as f:
    json.dump(reviewed, f, ensure_ascii=False, separators=(',', ':'))
"

# 最終検証
python schemas/validator.py output/reviewed_xxx.json
```

### 並列化の前提条件

- prompterは `params.prompt` のみを変更し、構造（next/subs/layout等）には触らない → **reviewerの構造修正と競合しない**
- reviewerは `params.prompt` の内容チェック（観点10）を並列時にはスキップする → prompterの出力後に最終チェックとして実行

### 並列化できないケース

- **P2（既存修正）でプロンプト修正のみの場合**: 構造校閲が不要なのでprompterだけ実行（並列化の意味なし）
- **reviewerが構造を大幅に修正した場合**: prompterが書いたpromptのcontextNameやnext条件が変わる可能性がある。この場合はマージ後にプロンプト整合性チェック（観点10相当）を追加実行する

---

## 施策2: reviewerの効率化（validatorとの役割分担明確化）

### 現状の重複

reviewer（LLM）とvalidator.py（Pythonスクリプト）で同じ項目を二重チェックしている。

| チェック内容 | reviewer観点 | validator コード | 重複 |
|---|---|---|---|
| startモジュールの存在 | 観点1 | S-001, S-003 | ✅ 重複 |
| 遷移先の存在確認 | 観点1 | T-001 | ✅ 重複 |
| 孤立モジュール検出 | 観点1 | T-002 | ✅ 重複 |
| subs参照先の存在確認 | 観点5 | T-003 | ✅ 重複 |
| ラベル重複検出 | 観点1 | T-004 | ✅ 重複 |
| STT next構造（TIMEOUT/ERROR/NO_RESULT） | 観点4 | STT-001〜004 | ✅ 重複 |
| TTS next label = "Next Module" | 観点3 | TTS-001 | ✅ 重複 |
| stop_by_dtmf = "Yes"/"No" | 観点3 | TTS-002 | ✅ 重複 |
| Retry condition/label | 観点4 | R-001〜005 | ✅ 重複 |
| save2dbサブモジュール接続 | 観点5 | SB-001, SB-002 | ✅ 重複 |
| 命名規則 | 観点6 | N-001〜003 | ✅ 重複 |
| OpenAI module空欄 | 観点3 | OAI-001, OAI-002 | ✅ 重複 |
| OpenAI next順序 | 観点3 | OAI-004 | ✅ 重複 |
| saveContextModel2DB fields | 観点3 | CTX-010〜017 | ✅ 重複 |
| DTMF params | 観点3 | (CLAUDE.md記載) | 部分重複 |

### 最適化後の役割分担

**validator.pyに任せる（reviewerからスキップ）**:
- 構造整合性の機械的チェック（観点1の大部分）: startの存在、遷移先存在、孤立モジュール、ラベル重複
- STT/TTS/Retry/OpenAI のパラメータ形式チェック（観点3, 4の大部分）
- save2dbサブモジュール接続チェック（観点5の大部分）
- 命名規則チェック（観点6）

**reviewerに残す（LLMでないとできない）**:
- **観点0: セキュリティ・インジェクション検査** — パターンマッチだけでは検出できない巧妙なインジェクション
- **観点2: モジュール選定ガイド照合** — 「この場面ではこのモジュールを使うべき」という判断（LLM必須）
- **観点7: 業務ロジック検証（設計書との突合せ）** — 聴取項目の網羅性、分岐条件の一致（LLM必須）
- **観点8: ライセンス・コンプライアンス検査** — 外部URL・商標の検出（LLM有効）
- **観点9: IVRプロパティ整合性** — propertiesファイルとJSONの突合せ
- **観点10: OpenAIプロンプト出力ラベル整合性** — next条件とprompt出力仕様の突合せ（LLM有効）

### 効果の見積もり

| 項目 | 現状 | 最適化後 |
|---|---|---|
| reviewerのチェック観点数 | 10（+1追加で11） | 6（0, 2, 7, 8, 9, 10） |
| reviewer所要時間（推定） | 25-30分 | **12-18分** |
| validator所要時間 | 数秒（変更なし） | 数秒 |

### reviewer.mdへの変更

各観点の冒頭に以下の注記を追加:

```markdown
### 1. 構造整合性チェック
> **⚡ 効率化**: 以下のチェックは `validator.py` が機械的に実行するため、
> reviewerは **validator.py が検出できない論理的な構造問題のみ** をチェックする。
> 具体的には: 到達不能パスの意図判定、循環参照の意図判定（Retryループかそうでないか）。
> validator.py で検出可能な項目（startの存在、遷移先存在、孤立モジュール、ラベル重複）はスキップしてよい。
```

同様の注記を観点3, 4, 5, 6にも追加。

---

## 施策3: settings.jsonのYes/No確認削減

### 現状の問題

画像のようなケースで、pythonスクリプトの実行時にYes/No確認が発生している。

### 追加するallowパターン

```json
{
  "permissions": {
    "allow": [
      // --- 既存のパターンに追加 ---

      // Python一行スクリプト（zipfile, json等の標準ライブラリ操作）
      "Bash(cd * && python3 << *)",
      "Bash(python3 << *)",

      // reviewer/prompterのマージスクリプト
      "Bash(python3 scripts/merge_prompt.py *)",

      // ファイル内容確認（wc -l, file等）
      "Bash(wc -l *)",
      "Bash(file *)",

      // readlinkやrealpath（パス解決）
      "Bash(readlink *)",
      "Bash(realpath *)",

      // 改行コード変換
      "Bash(dos2unix *)",
      "Bash(unix2dos *)",

      // diffの詳細オプション
      "Bash(diff -u *)",
      "Bash(diff --color *)",

      // タスクの並列実行用
      "Task"
    ]
  }
}
```

### 特に効果が大きいパターン

| パターン | 頻度 | 効果 |
|---|---|---|
| `Bash(cd * && python3 << *)` | reviewer/generatorが毎回使用 | 5-10回/シナリオのYes/No削減 |
| `Bash(python3 << *)` | ヒアドキュメントでのPython実行 | 同上 |
| `Task` | 並列実行に必須 | 並列化の前提条件 |

---

## 最適化後のパイプライン全体像

### P1: 新規作成（最適化版）

```
@director（Opus）                                    5-10分
    ↓
@generator（Sonnet）                                 10-15分
    ↓
┌── @prompter（Opus）— prompt記述            ┐
│                                              │ 並列  12-18分
└── @reviewer（Sonnet）— 構造校閲（6観点）   ┘
    ↓ 両方完了
マージスクリプト                                     1-2分
    ↓
validator.py（53チェック）                            数秒
    ↓
[CRITICAL残存時] → 修正ループ（最大3回）
    ↓
@reviewer 観点10（プロンプト整合性チェック）          3-5分
    ↓
build_bivr.py                                       数秒
                                          ────────────────
                                          合計: 30-50分（ループなし時）
                                                45-70分（ループ1回あり時）
```

### ループの発生確率を下げる施策

| ループ原因 | 対策 | 効果 |
|---|---|---|
| generatorの構造ミス → reviewer修正 → validator再検証 | **generatorに自己検証ステップを強化**（チェックリストの厳格化） | ループ発生率↓ |
| prompterの出力ラベル不一致 → reviewer観点10で検出 | **設計書の出力ラベル列をSingle Source of Truth化**（今回の設計書拡張） | ループ発生率↓ |
| validator CRITICAL → reviewer差し戻し | **validatorチェックの一部をgenerator自己検証に前倒し**（生成直後にvalidator軽量版を実行） | ループ発生率↓ |

### generator自己検証の強化案

generatorがJSON出力直後に、validator.pyを **自分で** 実行して主要CRITICALをその場で修正する:

```markdown
## 成果物出力後の自己検証（必須）

JSON出力後、reviewerに渡す前に以下を実行すること:

\`\`\`bash
python schemas/validator.py output/draft_{施設名}_{フロー名}.json --no-props
\`\`\`

CRITICALが検出された場合は **その場で修正して再検証** する（最大2回）。
2回で解消しない場合のみreviewerに渡す。
```

これにより、reviewer到達時点で構造的なCRITICALがほぼ解消済みとなり、reviewerは業務ロジック・セキュリティ・プロンプト整合性に集中できる。

---

## まとめ: 時間削減の内訳

| 施策 | 削減時間（推定） |
|---|---|
| 並列化（prompter + reviewer構造校閲） | -15分 |
| reviewer観点削減（11→6） | -10〜15分 |
| Yes/No確認削減 | -3〜5分 |
| generatorの自己検証強化（ループ回避） | -5〜10分（ループ1回分） |
| **合計** | **-33〜45分** |

**現状65-70分 → 最適化後30-40分（ループなし時）**
