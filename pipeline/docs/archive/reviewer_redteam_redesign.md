# reviewer レッドチーム再定義 + validator 拡充設計

> **原則**: 機械的に判定可能なチェックは全てvalidator.pyに集約する。
> reviewerは「レッドチーム」として、設計意図との矛盾・業務ロジックの穴・セキュリティの盲点を攻める。

---

## 新しい役割定義

### validator.py — 「これに通ればフローは壊れない」

| 性質 | 説明 |
|---|---|
| 確定的 | 結果は常に同じ（LLMの揺れがない） |
| 高速 | 数秒で完了 |
| 網羅的 | 全モジュール・全パラメータを走査 |
| 拡張容易 | 新しいルールはPythonで追加 |
| 守備範囲 | JSON構造、パラメータ形式、接続整合性、命名規則、プロンプト出力ラベル整合性 |

### reviewer — 「これが通ればフローは正しく機能する」（レッドチーム）

| 性質 | 説明 |
|---|---|
| 判断的 | 文脈・意図・業務知識に基づく判断が必要 |
| 攻撃的 | 「このフローで患者が困るケースはないか」を探す |
| 設計書依存 | 設計書との突合せが主な作業 |
| 守備範囲 | 業務ロジックの矛盾、セキュリティリスク、モジュール選定の妥当性、プロンプト品質 |

---

## validator.py に追加すべきチェック項目

### 現状（52チェック）のカテゴリ

| カテゴリ | 件数 | 内容 |
|---|---|---|
| S（Structure） | 3 | 必須フィールド、フロー名形式、startの存在 |
| T（Transition） | 4 | 遷移先存在、孤立モジュール、subs参照先、ラベル重複 |
| STT | 5 | next構造、TIMEOUT/ERROR/NO_RESULT存在、success形式、個別パターン禁止 |
| TTS | 3 | next label、stop_by_dtmf、prompt形式 |
| OAI（OpenAI） | 4 | module空欄/存在、promptTTS、next順序 |
| R（Retry） | 5 | condition/label形式、retry_count |
| SB（save2db） | 2 | subs接続、modules定義 |
| N（Naming） | 3 | 禁止文字、環境依存文字 |
| CTX（Context） | 7 | saveContextModel2DBのfields構造 |
| P（Properties） | 7 | プロパティ整合性 |
| PH（Phone） | 3 | Phone Normalization |
| SCR（Script） | 4 | スクリプトモジュール |
| J（Jump） | 2 | Jump to Flow |

### 追加すべきチェック（reviewerから移管 + 新規）

#### PROMPT系（新規）— プロンプト出力ラベル整合性

```python
# PROMPT-001: next分岐ラベルがprompt出力仕様に含まれているか
# PROMPT-002: prompt出力仕様にあるがnextに対応しないラベル（Warning）
# PROMPT-003: OpenAIモジュールのpromptが空欄のまま（個人情報サブフロー除外）
# PROMPT-004: ワイルドカード分岐時にNO_RESULTが出力仕様にない
```

**実装方法**:
```python
def check_prompt_label_consistency(data, result):
    """OpenAIモジュールのnext分岐条件とprompt出力仕様の整合性チェック"""
    modules = data.get("modules", {})
    flow_name = data.get("name", "")
    
    # 個人情報サブフロー判定（除外対象）
    personal_keywords = ["氏名聴取", "生年月日聴取", "電話番号聴取", "診察券番号聴取"]
    is_personal_subflow = any(kw in flow_name for kw in personal_keywords)
    
    for mod_name, mod in modules.items():
        if "generate_by_OpenAI" not in mod.get("type", ""):
            continue
            
        prompt = mod.get("params", {}).get("prompt", "")
        next_list = mod.get("next", [])
        
        # PROMPT-003: prompt空欄チェック（個人情報サブフロー除外）
        if not prompt and not is_personal_subflow:
            result.issues.append(Issue("CRITICAL", "PROMPT-003", mod_name,
                "params.prompt",
                "OpenAIモジュールのpromptが空欄です（@prompter未実行の可能性）"))
            continue  # prompt空なら以降のチェックは不可能
        
        if not prompt:
            continue
        
        # next配列から有効な分岐ラベルを抽出
        skip_conditions = {"^TIMEOUT$", "^ERROR$", "^NO_RESULT$", "^.+$", "^.*$", ""}
        branch_labels = set()
        has_wildcard = False
        for nxt in next_list:
            cond = nxt.get("condition", "")
            if cond in ("^.+$", "^.*$"):
                has_wildcard = True
            elif cond and cond not in skip_conditions:
                # ^予約$ → 予約
                label = cond.strip("^$")
                branch_labels.add(label)
        
        # promptから出力仕様を抽出
        # 「# 出力仕様」セクション内の「- {ラベル}」行を収集
        prompt_labels = set()
        in_output_section = False
        for line in prompt.split("\n"):
            stripped = line.strip()
            if "出力仕様" in stripped:
                in_output_section = True
                continue
            if in_output_section:
                if stripped.startswith("#") and "出力仕様" not in stripped:
                    in_output_section = False
                    continue
                if stripped.startswith("- "):
                    label = stripped[2:].strip()
                    # 括弧内の説明を除去
                    label = label.split("（")[0].split("(")[0].strip()
                    if label and label != "NO_RESULT":
                        prompt_labels.add(label)
        
        # PROMPT-001: next分岐ラベルがprompt出力仕様に含まれているか
        if branch_labels:
            missing = branch_labels - prompt_labels
            if missing:
                result.issues.append(Issue("CRITICAL", "PROMPT-001", mod_name,
                    "params.prompt vs next",
                    f"next分岐ラベル {missing} がプロンプトの出力仕様に含まれていません "
                    f"― OpenAIがこのラベルを出力できず遷移失敗します"))
        
            # PROMPT-002: prompt出力仕様にあるがnextに対応しないラベル
            extra = prompt_labels - branch_labels
            if extra and not has_wildcard:
                result.issues.append(Issue("WARNING", "PROMPT-002", mod_name,
                    "params.prompt vs next",
                    f"プロンプトの出力仕様 {extra} にnext分岐条件がありません "
                    f"（ワイルドカードもなし）"))
        
        # PROMPT-004: ワイルドカード分岐時のNO_RESULT存在確認
        if has_wildcard and not branch_labels:
            if "NO_RESULT" not in prompt:
                result.issues.append(Issue("WARNING", "PROMPT-004", mod_name,
                    "params.prompt",
                    "ワイルドカード分岐ですが、プロンプトにNO_RESULTの記載がありません"))
```

#### DTMF系（新規）— 現状のvalidatorにDTMF固有チェックがない

```python
# DTMF-001: DTMFモジュールのpromptに{recstart}が含まれているか
# DTMF-002: max_dtmf_lengthが設定されているか
# DTMF-003: retryが設定されているか（"0"は不可）
# DTMF-004: termdtmf/remove_term/stop_play_when_speechが設定されているか
```

#### FLOW系（新規）— 冒頭チェーン構造の検証

```python
# FLOW-001: startモジュールがwaitタイプか
# FLOW-002: waitの直後がsaveContextModel2DBか
# FLOW-003: saveContextModel2DBの後にincoming-classifierがあるか
# FLOW-004: 非通知パスにsaveCompletionFlag2db + Disconnectがあるか
# FLOW-005: 時間外パスにTTS + saveCompletionFlag2db + Disconnectがあるか
```

#### REACH系（新規）— 到達可能性の深い検証

```python
# REACH-001: startから到達不能なモジュール（BFS/DFS）
# REACH-002: 終話パス（Disconnect）への到達保証（全パスがDisconnectに到達するか）
# REACH-003: Retryを経由しないループ検出
```

#### SAVECTX系（新規）— saveContext2DBの禁止パターン

```python
# SAVECTX-001: contextValueに#data#が含まれている（Re-confirmation専用記法）
# SAVECTX-002: contextName/contextDisplayType/contextValueのいずれかが空
# SAVECTX-003: OpenAIがcontextNameに保存済みなのに重複してsaveContext2DBがある
```

### 追加後のチェック数見積もり

| カテゴリ | 現状 | 追加 | 合計 |
|---|---|---|---|
| 既存13カテゴリ | 52 | — | 52 |
| PROMPT（新規） | — | 4 | 4 |
| DTMF（新規） | — | 4 | 4 |
| FLOW（新規） | — | 5 | 5 |
| REACH（新規） | — | 3 | 3 |
| SAVECTX（新規） | — | 3 | 3 |
| **合計** | **52** | **19** | **71** |

---

## reviewer.md の書き換え方針

### 新しい Role 定義

```markdown
---
name: reviewer
description: generatorが生成したフローJSONに対し、設計書との業務ロジック突合せ・セキュリティ監査・プロンプト品質検証をレッドチームとして実行する。機械的チェックはvalidator.pyに委任し、LLMでしか判断できない論理的・意図的な問題の検出に集中する。
model: sonnet
tools: Read, Write, Edit, Bash, Glob, Grep
---

# reviewer — フローJSON レッドチームエージェント

## 役割

あなたは **ボイスボットIVRフローのレッドチーム** です。
generatorとprompterが生成したフローJSONに対し、「このフローで患者が困るケースはないか」
「設計意図が正しく実装されているか」「セキュリティの盲点はないか」を攻撃的に検証します。

**あなたの仕事**: LLMでなければ判断できない論理的・業務的・セキュリティ的な問題を見つけること
**あなたの仕事ではないこと**: JSONの構造チェック、パラメータ形式の検証、命名規則の確認
（→ これらは validator.py が確実に実行する。二重チェックは不要）
```

### 新しい校閲観点（6カテゴリに集約）

#### 観点1: セキュリティ・インジェクション検査（現観点0 — 維持）

> 変更なし。LLMによる巧妙なパターン検出は機械的チェックでは不十分。

#### 観点2: モジュール選定の妥当性（現観点2 — 維持・強化）

> 「この場面ではこのモジュールを使うべき」という業務判断。設計書を読んで判断する。
> 例: 「診療科聴取にCLASSIFICATIONではなくDEPARTMENTを使っているか」

validator.pyはモジュールのtype文字列をチェックできるが、「この業務文脈でこのモジュールが適切か」は判断できない。

#### 観点3: 設計書との業務ロジック突合せ（現観点7 — 維持・最重要）

> **レッドチームの本領**。以下を攻撃的に検証する:
>
> - 設計書の全聴取項目がフローに実装されているか（漏れ検出）
> - 設計書にない余計なモジュールが追加されていないか（過剰実装検出）
> - 分岐条件が設計書と完全一致しているか
> - 終話パターンのstatus/smsFlagが設計書と一致しているか
> - コンテキスト定義（rangeValues等）が設計書と一致しているか
> - **「患者がこの選択肢を選んだとき、正しい終話に到達するか」をシミュレーション**

#### 観点4: OpenAIプロンプト品質検証（現観点10を強化 — レッドチーム的アプローチ）

> validator.pyはnext条件とprompt出力ラベルの「一致」を機械的にチェックする。
> reviewerは以下のLLMでしかできない品質検証を行う:
>
> - **Context文言の正確性**: プロンプト内のContext（「直前にユーザーに聞いた質問」）が実際のTTS文言と一致するか
> - **判定ロジックの網羅性**: はい/いいえ判定型で「ええ」「うん」等の口語が漏れていないか
> - **STT誤変換パターンの妥当性**: 追加された誤変換パターンが誤判定を引き起こさないか
> - **日付変換ルールの正確性**: 和暦変換、相対日付計算のロジックが正しいか
> - **診療科マッピングの妥当性**: 略称→正式名称のマッピングが正しいか（「整形」→「整形外科」は正しいが、「整形」→「形成外科」は誤り）

#### 観点5: ライセンス・コンプライアンス（現観点8 — 維持）

> 変更なし。

#### 観点6: IVRプロパティ整合性（現観点9 — 維持）

> 変更なし（propertiesファイルの存在・内容チェック）。
> ただし、propertiesの構造的な整合性（モジュール名一致等）はvalidator.pyのP系チェックが担当。
> reviewerは「発話文言の内容が設計書と一致するか」のみを確認する。

### 削除する観点（validator.pyに完全委任）

| 現観点 | 内容 | 委任先 |
|---|---|---|
| 観点1（構造整合性） | start存在、遷移先存在、孤立モジュール、ラベル重複 | validator S/T系 + REACH系 |
| 観点3（パラメータ設定値） | DTMF params、acceptance_times next、saveCompletionFlag | validator DTMF/OAI/R/CTX系 |
| 観点4（STTモジュール構造） | next 11スロット、TIMEOUT/ERROR/NO_RESULT、success形式 | validator STT系 |
| 観点3（TTSモジュール構造） | next label、stop_by_dtmf | validator TTS系 |
| 観点4（Retry Counter） | condition/label形式、retry_count | validator R系 |
| 観点5（save2db接続） | subs接続、modules定義 | validator SB系 |
| 観点6（命名規則） | 禁止文字、環境依存文字 | validator N系 |

---

## 新しいパイプラインでのvalidator.pyの位置

### 現状
```
generator → prompter → reviewer（全観点） → validator → build_bivr
```

### 最適化後
```
generator → validator（構造チェック・即時修正）
    ↓ PASSした場合のみ次へ
┌── prompter（prompt記述）
└── reviewer（レッドチーム6観点）  ← 並列実行
    ↓ 両方完了
マージ
    ↓
validator（最終検証 — PROMPT系含む全71チェック）
    ↓
build_bivr
```

**ポイント**: validatorが2回走る。
1. **generator直後（構造チェック）**: 構造CRITICALをgeneratorがその場で修正。reviewerに壊れたJSONを渡さない
2. **マージ後（最終検証）**: PROMPT系チェック含む全チェック。最終関門

---

## reviewerの所要時間見積もり

| 観点 | 内容 | 推定時間 |
|---|---|---|
| 1. セキュリティ | インジェクション検査 | 2-3分 |
| 2. モジュール選定 | 設計書照合 | 2-3分 |
| 3. 業務ロジック | 設計書突合せ（本丸） | 5-8分 |
| 4. プロンプト品質 | Context・判定ロジック・マッピング | 3-5分 |
| 5. ライセンス | コンプライアンス | 1-2分 |
| 6. プロパティ | 発話文言の内容チェック | 2-3分 |
| **合計** | | **15-24分** |

現状25-30分から **約10分短縮**。加えて、構造的なCRITICALでの差し戻しループが発生しなくなるため、実効的にはさらに短縮。

---

## reviewer.md の新しい校閲レポートフォーマット

```markdown
# レッドチームレポート: {施設名} - {フロー名}

## ⚠ セキュリティ警告
{SECURITY-CRITICAL がある場合ここに先頭列挙。なければ「検出なし」}

## 設計書との突合せ結果

### 聴取項目の網羅性
| 設計書の聴取項目 | フローに実装 | 判定 |
|---|---|---|
| {項目名} | ✅ / ❌ | |

### 分岐条件の一致
| 分岐ポイント | 設計書の条件 | フローの条件 | 判定 |
|---|---|---|---|
| {用件分岐} | {選択肢} | {next条件} | ✅ / ❌ |

### 終話パターンの一致
| 終話名 | 設計書 status/smsFlag | フロー status/smsFlag | 判定 |
|---|---|---|---|
| {名前} | {値} | {値} | ✅ / ❌ |

## プロンプト品質チェック
| モジュール名 | Context正確性 | 判定ロジック | STT考慮 | 判定 |
|---|---|---|---|---|
| {名前} | ✅ / ❌ | ✅ / ❌ | ✅ / ❌ | |

## レッドチーム攻撃シナリオ
> 「このフローで患者が困るケース」を具体的に列挙する

1. **シナリオ**: {患者が「〇〇」と言った場合}
   **結果**: {どのモジュールに遷移するか}
   **問題**: {期待と異なる場合の具体的な問題}

2. ...

## 修正指示
| # | 重大度 | モジュール名 | 問題 | 修正内容 |
|---|---|---|---|---|
| 1 | Critical | {名前} | {問題} | {具体的な修正} |

## validator.pyとの連携
> 以下は validator.py で機械的に検証済み。reviewerは再チェック不要。
> validator.py 実行結果: {PASS / CRITICAL {n}件 / WARNING {n}件}
```

---

## まとめ

| 項目 | 変更前 | 変更後 |
|---|---|---|
| reviewer校閲観点 | 11カテゴリ（全方位チェック） | 6カテゴリ（レッドチーム特化） |
| reviewer所要時間 | 25-30分 | 15-24分 |
| validator.pyチェック数 | 52 | 71（19チェック追加） |
| validator.py実行回数 | 1回（最後） | 2回（generator直後 + マージ後） |
| ループリスク | 高（構造CRITICALがreviewer段階で発見） | 低（構造CRITICALはgenerator段階で解消） |
| 品質保証 | LLMの揺れに依存する部分が大 | 機械的チェック71件 + LLMレッドチーム |
