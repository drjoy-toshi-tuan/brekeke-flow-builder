<!--
施設名: 大阪公立大学医学部附属病院 先端予防医療部附属クリニック MedCity21
group_name: Medcity21
シナリオ名: 健診
環境: 本番
元資料: docs/reference/customer_docs/【健診1】：大阪公立大学医学部附属病院Medcity21.md
移管日: 2026-04-27
移管者: 浜口
備考: Gen2→Gen3 移管。長文（1205行）プロンプトのため確定版見極め必須。Gen2 形式（Assistant プロンプト + function schema + yaml の三層統合型）。
-->

### 移管方針
- **group_name は `Medcity21` に固定**（短縮形）。`basic_info.facility_name` / `basic_info.group_name` / `basic_info.flow_name` および `flow_structure.flows[].name` / `subflows[].name` すべてで「Medcity21」を一貫使用する。flow_name は `Medcity21$健診_YYYYMMDD` 形式。元資料の正式名「大阪公立大学医学部附属病院 先端予防医療部附属クリニック MedCity21」は **TTS 文言（冒頭挨拶等）でのみ使用**。長すぎてフロー名や ID には載せない。
- 用件分岐は冒頭で 5 つ（予約 / 変更 / キャンセル / オプション / 問合せ）＋聴取失敗フォールバック。**Pattern A**（OpenAI 直後で classification 分岐）で組む。echo_back や複数 context 組合せの分岐は無いため Pattern B 不要。
- サブフロー: PatientName（受診者名 1 枠）／ DateOfBirth（生年月日・復唱 1 回有り）／ AdditionalPhoneNumber（電話番号、phone_type による 3 分岐 anonymous/mobile/{ip_phone,other}）／ FAQ_RAG（FAQ参照V2、is_question ガード付き）。**いずれもメインに展開せず Jump to Flow**。
- Date of Call Classifier 不要（受付時間外分岐の指示なし、`endpoint=時間外` enum はあるがフロー記載なし → director 判断で省略可）。
- addCurrentDate: 予約希望時期（preferredDate）／生年月日（patientDateOfBirth）／現在の予約日（reservationDate）の前段 OpenAI には scaffold 側で自動付与されるので director は触らない。

### 施設固有の特殊ルール
- **救済語（言い換え辞書）**: 「健診」←{検針／返信／天候診断／返金控寸断／検診}、「人間ドック」←{人間ロック／ドック／ロック／人間独}、「予約」←{薬／お薬}、「変更」←{取り直す等}、「キャンセル」←{やめる等}、肯定←{肺／いいです}、否定←{が今／PHVます}。**incoming-classifier の生成プロンプトで救済語マッピングを必ず注釈に含める**。
- 数字正規化: `[CcＣｃ]/for/ふぉー/フォー/しー/しい/し → 4`、`ごー/ごお/ご → 5`、`救急 → 99`、`GO/go → 5`。電話番号 OpenAI モジュールに反映。
- コースリスト 10 種（人間ドック/標準/ライフスタイル/がん/スマートエグゼクティブ/エグゼクティブ/PETCTエグゼクティブ/エイジングチェック/スタイリッシュ/ラグジュアリー）＋ オプション 3 種（超音波/マンモグラフィ/3Dマンモグラフィ）＋ 健保組合 2 種（協会けんぽ/大阪市国保）。**列挙は元資料を参照、director は course/option/company の 3 個 generate_by_OpenAI に enum + aliases を渡すよう指示**。
- 期間表現の特殊条件:「現在の予約日は本日を含め一週間以内？」（変更）「本日を含め2週間以内？」（キャンセル）「2週間以上先」（予約希望時期）。Yes/No 分岐の閾値が 3 通り混在。各条件確認の **再質問は最大 3 回**（通常は 2 回）。
- 終話テンプレ選択ロジック（4 分岐・順序固定）: ①classification=問合せ AND reply=希望しない → 返信不要 (status=7)／②classification∈{予約,変更,オプション,問合せ} AND additionalPhoneNumber が 090/080/070/060 開始 → 共通・携帯 (status=1, smsFlag=1)／③同上で携帯以外 → 共通・携帯以外 (status=1, smsFlag=1)／④classification=キャンセル → キャンセル (status=1, smsFlag=2)。**この優先順を維持**。050（ip_phone）は 090/080/070/060 に含めない点に注意（携帯以外扱い）。
- 代表案内（status=2, smsFlag=0）に流すケース: 変更で「1週間以内 Yes」／キャンセルで「2週間以内 Yes」／問合せ内容に「健診の結果／人間ドックの結果／健康診断の結果」を含む／非通知で電話番号取得失敗。
- 振替希望 Yes 時は **classification を「変更」に書き換える**（updateContext 必要）。
- echo_back 対象: **生年月日のみ 1 回復唱**（patientDateOfBirth）、非通知 (anonymous) 時の電話番号確認 1 回。氏名／その他項目は復唱・確認禁止。

### director が見落としやすいポイント
- **長すぎる正式名を group_name や flow 名に使わない**。「大阪公立大学医学部附属病院 先端予防医療部附属クリニック MedCity21」は TTS のみ。group_name=`Medcity21`（先頭 M 大文字、city 小文字、21 半角）。launch_parallel の regex 制約上、半角スペース・括弧・全角文字 NG。
- 元資料は冒頭に「更新日時: 2026/01/14 冒頭アナウンス文言の年末年始の休診日を削除」と記載。**冒頭アナウンスは「お電話ありがとうございます。人間ドック、MedCity21のAI電話です。」のみ**で、年末年始休診告知は含めない（旧版の混入に注意）。
- 元資料中の SSML タグ（`<speak>`, `<break>`, `<dtmf/>` 等）は **すべて削除**して `{tts_g:...}` 小文字で記述。電話番号読み上げ・breakc 等の演出は TTS 側に任せる。
- FAQ参照V2 は **is_question ガード付き**（短い名詞/応答は QA スキップ）で実装。RAG サブフローを `scenario_flow` に `type:subflow` ブロックとして必ず配置（`rag_subflow` セクションのみは NG）。FAQ ヒットなしの許可文は固定文言「ご質問いただいた内容はAI電話ではご対応できませんので、折り返しご連絡時にご確認ください。」。
- 電話番号の聴取は phone_type 3 分岐（anonymous / mobile / {ip_phone, other}）。mobile は incoming_phone_number で確認、anonymous はバリデ通過後に復唱、ip_phone/other は復唱しない。**3 経路で別 TTS / 別ロジックなので AdditionalPhoneNumber サブフロー内で context_match_router 必要**。
- function `endpoint` enum に「時間外」が含まれるが、フロー記載なし → director 判断で実装スコープから外す（or 別途確認）。
- 聴取失敗フォールバック (F) は classification を「問合せ」に書き換えて E フローへ合流する仕様。incoming-classifier のデフォルト（catch-all `^*$`）から接続。
- ラスト質問の応答は reply に影響しない（reply は問合せ_返信希望で確定）。「ない」等の否定でも reply は維持。
- 氏名複数名: 最初の 1 名のみ patientName / patientDateOfBirth、2 人目以降は reason に「氏名（カタカナ）, yyyy-MM-dd」改行追記。**OpenAI プロンプトに明記**。
- function スキーマの required 配列は 20 項目すべて必須。display_type は `CLASSIFICATION` / `TEXT` / `DATE` / `DATE_OF_BIRTH` / `PHONE_NUMBER` / `STATUS` を使い分け。

### 詳細は元資料を参照
docs/reference/customer_docs/【健診1】：大阪公立大学医学部附属病院Medcity21.md
