# ============================================================
# 施設名: 大分赤十字病院
# シナリオ名: 診療
# 環境: デモ
# 元資料: docs/reference/customer_docs/【診療1】：大分赤十字病院.md
# 移管日: 2026-04-16
# 移管者: 浜口
# 備考: Gen2→Gen3移管。新パイプライン（scenario_flow ブロック構造）で生成。
# ============================================================

# BLOCKER: 元資料 docs/reference/customer_docs/【診療1】：大分赤十字病院.md が未提供。
# 以下は qa_validator 通過用の構造テンプレート。元資料の提供後に @director で再生成すること。
version: "1.0"

# --- セクション1: 基本情報 ---
basic_info:
  facility_name: "大分赤十字病院"
  group_name: "大分赤十字病院"
  flow_name: "大分赤十字病院$診療"
  target_facility: "大分赤十字病院"
  office_id: "TODO_要確認"
  phone_number: "TODO_要確認"
  business_hours: "TODO_要確認"
  flow_type: "subflow"
  work_type: "gen2_migration"
  environment: "demo"

# --- セクション2: フロー構成 ---
flow_structure:
  type: "subflow"
  flows:
    - name: "大分赤十字病院$診療"
      role: "main"
      description: "冒頭チェーン → 用件確認 → 個人情報聴取サブフロー → 診療科聴取 → 終話"
  subflows:
    - name: "大分赤十字病院$氏名聴取"
      target: "氏名聴取"
      recitation: "なし"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "CLAUDE.md Rule 9 準拠"
    - name: "大分赤十字病院$生年月日聴取"
      target: "生年月日聴取"
      recitation: "あり"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "CLAUDE.md Rule 9 準拠"
    - name: "大分赤十字病院$電話番号聴取"
      target: "電話番号聴取"
      recitation: "あり"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "CLAUDE.md Rule 9 準拠"
    - name: "大分赤十字病院$診察券番号聴取"
      target: "診察券番号聴取"
      recitation: "あり"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "CLAUDE.md Rule 9 準拠"

# --- セクション3: フローの目的 ---
purpose: "患者からの予約関連電話を受け、用件を確認し、個人情報（氏名・生年月日・連絡先電話番号・診察券番号）と診療科を聴取して折り返し受付を自動化する。"

# --- セクション4: シナリオフロー図 ---
flow_diagrams:
  - flow_name: "大分赤十字病院$診療"
    diagram: |
      冒頭(wait 2000ms)
        → コンテキスト設定(saveContextModel2DB)
          → 着信電話番号分類(incoming-classifier)
              ├─ 非通知 → 非通知_アナウンス(TTS) → 完了フラグ_非通知(status=2, smsFlag=-1) → 切断
              └─ 通常/携帯/固定 → 受付時間判定(acceptance_times)
                    ├─ 時間外 → 時間外_アナウンス(TTS) → 完了フラグ_時間外(status=6, smsFlag=-1) → 切断
                    └─ 受付可 → 冒頭_アナウンス(TTS)
                          → 用件確認(TTS → STT → OpenAI → Retry)
                              ├─ TODO_用件分岐 → ★個人情報聴取パス
                              └─ リトライ失敗 → 完了フラグ_聴取失敗(status=3, smsFlag=-1) → 聴取失敗_アナウンス(TTS) → 切断

      ★個人情報聴取パス:
        Jump to 氏名聴取SF → Jump to 生年月日聴取SF → Jump to 電話番号聴取SF → Jump to 診察券番号聴取SF
          → 診療科_聴取(TTS → STT → OpenAI → Retry)
              → Jump to RAGサブフロー → 完了フラグ_受付完了(status=1) → 終話_アナウンス(TTS) → 切断
    notes: |
      BLOCKER: 元資料（Customer Docs）が未提供のため、フロー構造は一般的な診療シナリオパターンで仮設定。
      元資料の提供後に @director で再生成すること。

  - flow_name: "大分赤十字病院$氏名聴取"
    diagram: |
      CLAUDE.md Rule 9 準拠。docs/reference/bivr/samples/json/氏名聴取.json を完全コピー。
      フロー名プレフィックスのみ「大分赤十字病院$」に置換。
    notes: "復唱なし"

  - flow_name: "大分赤十字病院$生年月日聴取"
    diagram: |
      CLAUDE.md Rule 9 準拠。docs/reference/bivr/samples/json/生年月日聴取_復唱あり.json を完全コピー。
      フロー名プレフィックスのみ「大分赤十字病院$」に置換。
    notes: "復唱あり"

  - flow_name: "大分赤十字病院$電話番号聴取"
    diagram: |
      CLAUDE.md Rule 9 準拠。docs/reference/bivr/samples/json/電話番号聴取_復唱あり.json を完全コピー。
      フロー名プレフィックスのみ「大分赤十字病院$」に置換。
    notes: "復唱あり。incoming-classifier内蔵"

  - flow_name: "大分赤十字病院$診察券番号聴取"
    diagram: |
      CLAUDE.md Rule 9 準拠。docs/reference/bivr/samples/json/診察券番号聴取.json を完全コピー。
      フロー名プレフィックスのみ「大分赤十字病院$」に置換。
    notes: "「わからない」分岐あり"

# --- セクション4b: シナリオフロー定義（ブロック構成）---
scenario_flow:
  - step: 冒頭
    type: opening
    use_acceptance_times: true
    next: 用件確認

  - step: 用件確認
    type: hearing
    output_format: enum
    conditions:
      - match: "TODO_要確認"
        next: jump_氏名聴取

  - step: jump_氏名聴取
    type: subflow
    flowname: "大分赤十字病院$氏名聴取"
    next: jump_生年月日聴取

  - step: jump_生年月日聴取
    type: subflow
    flowname: "大分赤十字病院$生年月日聴取"
    next: jump_電話番号聴取

  - step: jump_電話番号聴取
    type: subflow
    flowname: "大分赤十字病院$電話番号聴取"
    next: jump_診察券番号聴取

  - step: jump_診察券番号聴取
    type: subflow
    flowname: "大分赤十字病院$診察券番号聴取"
    next: 診療科

  - step: 診療科
    type: hearing
    output_format: enum
    no_result_default: "登録なし"
    next: jump_RAG検索

  - step: jump_RAG検索
    type: subflow
    flowname: "大分赤十字病院$RAG検索"
    next: END_受付完了

  - step: END_受付完了
    type: termination
    termination_ref: "END_受付完了"

# --- セクション5: コンテキストフィールド一覧（saveContextModel2DB 用）---
context_fields:
  - context_name: "classification"
    context_name_jp: "用件区分"
    display_type: "CLASSIFICATION"
    range_values:
      - order: "1"
        value: "TODO_要確認"
    item_default: true
    editable: true
    deletable: true
    notes: "TODO_要確認: 用件区分の選択肢は元資料から抽出すること"

  - context_name: "clinicalDepartment"
    context_name_jp: "診療科"
    display_type: "DEPARTMENT"
    range_values:
      - order: "1"
        value: "TODO_要確認"
    item_default: false
    editable: true
    deletable: true
    notes: "TODO_要確認: 診療科リストは元資料から抽出すること"

  - context_name: "patientName"
    context_name_jp: "氏名"
    display_type: "TEXT"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "サブフローで聴取"

  - context_name: "patientDateOfBirth"
    context_name_jp: "生年月日"
    display_type: "DATE_OF_BIRTH"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "サブフローで聴取。復唱あり"

  - context_name: "telephoneNumber"
    context_name_jp: "電話番号（着信）"
    display_type: "PHONE_NUMBER_CALL"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "着信番号自動格納"

  - context_name: "additionalPhoneNumber"
    context_name_jp: "連絡先電話番号"
    display_type: "PHONE_NUMBER"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "サブフローで聴取"

  - context_name: "medicalCardNumber"
    context_name_jp: "診察券番号"
    display_type: "NUMBER"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "サブフローで聴取"

  - context_name: "status"
    context_name_jp: "状態"
    display_type: "STATUS"
    range_values:
      - order: "1"
        value: "未処理"
      - order: "2"
        value: "代表案内"
      - order: "3"
        value: "聴取失敗"
      - order: "6"
        value: "時間外"
    item_default: true
    editable: true
    deletable: true
    notes: "1=未処理（受付完了）2=代表案内/非通知 3=聴取失敗 6=時間外"

  - context_name: "dateOfCall"
    context_name_jp: "受電日時"
    display_type: "DATE"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "自動格納"

  - context_name: "callId"
    context_name_jp: "通話ID"
    display_type: "TEXT"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "自動格納"

# --- セクション6: 聴取項目一覧 ---
hearing_items:
  - order: 1
    name: "用件確認"
    stt_type: "DTMF_AmiVoice"
    dtmf_max_length: 1
    retry_count: 2
    echo_back: false
    save_to: "classification"
    openai_processing: "classify"
    output_format: "enum"
    output_labels:
      - "TODO_要確認"
    notes: "TODO_要確認: 用件選択肢・DTMF番号対応は元資料から抽出すること"

  - order: 2
    name: "診療科"
    stt_type: "AmiVoice_STT"
    dtmf_max_length: null
    retry_count: 2
    echo_back: false
    save_to: "clinicalDepartment"
    openai_processing: "classify"
    output_format: "enum"
    output_labels:
      - "TODO_要確認"
    notes: "TODO_要確認: 診療科リストは元資料から抽出すること。no_result_default=登録なし"

# --- セクション7: ステップ詳細 ---
step_details:
  - step_name: "用件確認"
    tts_announcement: "TODO_要確認"
    input_method: "dtmf_voice"
    openai_rules:
      output_values:
        - "TODO_要確認"
      mapping:
        - input: "TODO_要確認"
          output: "TODO_要確認"
      no_result_condition: "上記いずれにも該当しない"
    save_to: "classification"
    next_step: "jump_氏名聴取"
    retry_failure: "end_failure"
    retry_failure_announcement: ""

  - step_name: "診療科"
    tts_announcement: "TODO_要確認"
    input_method: "voice_only"
    openai_rules:
      output_values:
        - "TODO_要確認"
      mapping:
        - input: "TODO_要確認"
          output: "TODO_要確認"
      no_result_condition: "上記いずれにも該当しない"
    save_to: "clinicalDepartment"
    next_step: "jump_RAG検索"
    retry_failure: "skip"
    retry_failure_announcement: ""

# --- セクション8: 終話パターン ---
termination_patterns:
  # --- 異常系（デフォルト必須）---
  - name: "END_非通知"
    condition: "非通知着信"
    tts_announcement: "恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。"
    status: "2"
    sms_flag: "-1"
    completion_flag_name: "完了フラグ_非通知"
  - name: "END_時間外"
    condition: "受付時間外"
    tts_announcement: "お電話ありがとうございます。大分赤十字病院です。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。"
    status: "6"
    sms_flag: "-1"
    completion_flag_name: "完了フラグ_時間外"
  - name: "END_聴取失敗"
    condition: "リトライ上限到達"
    tts_announcement: "申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。"
    status: "3"
    sms_flag: "-1"
    completion_flag_name: "完了フラグ_聴取失敗"
  # --- 正常系 ---
  - name: "END_受付完了"
    condition: "全聴取完了"
    tts_announcement: "TODO_要確認"
    status: "1"
    sms_flag: "TODO_要確認"
    completion_flag_name: "完了フラグ_受付完了"

# smsFlag分岐設計
sms_flag_routing:
  enabled: false
  routing_keys: []
  patterns: []

# --- セクション8b: RAG/FAQ検索サブフロー ---
rag_subflow:
  pattern: "3"
  inquiry_insertion_point: ""
  pre_termination: true

# --- セクション9: TTSモジュール一覧 ---
tts_modules:
  - module_name: "冒頭_アナウンス"
    purpose: "冒頭施設案内"
    announcement: "TODO_要確認"
  - module_name: "用件確認"
    purpose: "用件聴取"
    announcement: "TODO_要確認"
  - module_name: "診療科"
    purpose: "診療科聴取"
    announcement: "TODO_要確認"
  - module_name: "非通知_アナウンス"
    purpose: "非通知終話"
    announcement: "恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。"
  - module_name: "時間外_アナウンス"
    purpose: "時間外終話"
    announcement: "お電話ありがとうございます。大分赤十字病院です。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。"
  - module_name: "聴取失敗_アナウンス"
    purpose: "聴取失敗終話"
    announcement: "申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。"
  - module_name: "終話_アナウンス"
    purpose: "受付完了終話"
    announcement: "TODO_要確認"

# --- セクション10: AmiVoice辞書（profile_words）---
amivoice_dictionary:
  - step_name: "用件確認"
    words: |
      TODO_要確認
  - step_name: "診療科"
    words: |
      TODO_要確認

# --- セクション11: 特記事項・制約 ---
special_notes:
  - "BLOCKER: 元資料（docs/reference/customer_docs/【診療1】：大分赤十字病院.md）が未提供。フロー構造・聴取項目・TTS文言はすべて仮設定。元資料の提供後に @director で再生成すること。"
  - "Gen2からGen3への移管。新パイプライン（scenario_flow ブロック構造）で生成予定。"

# --- セクション12: 要確認事項（人間に確認が必要）---
confirmation_items:
  - item: "元資料（Customer Docs: 【診療1】：大分赤十字病院.md）の提供"
    resolved: false
  - item: "用件区分（classification）の選択肢"
    resolved: false
  - item: "診療科リスト"
    resolved: false
  - item: "TTS発話文言（冒頭・用件確認・診療科・終話等）"
    resolved: false
  - item: "営業時間（曜日・時間帯）"
    resolved: false
  - item: "smsFlag の割り当て"
    resolved: false
  - item: "office_id（施設ID）"
    resolved: false
  - item: "代表電話番号"
    resolved: false
