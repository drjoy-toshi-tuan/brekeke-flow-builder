# 設計書 — 諏訪赤十字病院健診センター 健診
# 生成元: @director エージェント
# 生成日: 2026/04/16
# 確認レポート: docs/designs/確認レポート_諏訪赤十字病院健診センター_健診_20260416.md
#
# ⚠️ BLOCKER あり: 元資料（Customer Docs）が欠落しています。
# docs/reference/customer_docs/【健診1】：諏訪赤十字病院健診センター.md が存在しないため、
# 標準的な健診フロー構造でスケルトンを生成しています。
# Customer Docs を配置後、@director で再生成してください。
version: "1.0"

# --- セクション1: 基本情報 ---
basic_info:
  facility_name: "諏訪赤十字病院健診センター"
  group_name: "諏訪赤十字病院健診センター"
  flow_name: "諏訪赤十字病院健診センター$健診"
  target_facility: "諏訪赤十字病院健診センター"
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
    - name: "諏訪赤十字病院健診センター$健診"
      role: "main"
      description: "冒頭チェーン → 個人情報サブフロー（氏名→生年月日→電話番号）→ 用件聴取 → 用件別分岐 → RAGサブフロー → 終話"
    - name: "諏訪赤十字病院健診センター$氏名聴取"
      role: "sub"
      description: "氏名聴取 → 結果返却"
    - name: "諏訪赤十字病院健診センター$生年月日聴取"
      role: "sub"
      description: "生年月日聴取（復唱あり）→ 結果返却"
    - name: "諏訪赤十字病院健診センター$電話番号聴取"
      role: "sub"
      description: "着信番号分岐 → 電話番号聴取/復唱確認 → 結果返却"
    - name: "諏訪赤十字病院健診センター$RAG検索"
      role: "sub"
      description: "FAQ検索ループ → 結果返却"
  subflows:
    - name: "諏訪赤十字病院健診センター$氏名聴取"
      target: "氏名聴取"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "氏名聴取サブフロー"
    - name: "諏訪赤十字病院健診センター$生年月日聴取"
      target: "生年月日聴取"
      recitation: "あり"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "生年月日聴取サブフロー。復唱あり（デフォルト）"
    - name: "諏訪赤十字病院健診センター$電話番号聴取"
      target: "電話番号聴取_復唱あり"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "電話番号聴取サブフロー。MOBILEパスの着信番号確認あり"
    - name: "諏訪赤十字病院健診センター$RAG検索"
      target: "RAG検索"
      transition_module: "drjoy^Custom Module$Custom Jump to Flow"
      termination: "return"
      notes: "FAQ検索サブフロー。パターン3: 問合せルート内 + 全終話前に配置"

# --- セクション3: フローの目的 ---
purpose: "諏訪赤十字病院健診センターの健診専用AI電話。患者からの電話を受け、個人情報（氏名・生年月日・電話番号）を聴取後、用件（予約・変更・キャンセル・問合せ）を振り分け、折り返し受付を自動化する。Gen2→Gen3移管。"

# --- セクション4: シナリオフロー図 ---
flow_diagrams:
  - flow_name: "諏訪赤十字病院健診センター$健診"
    diagram: |
      wait(2000ms)
        → saveContextModel2DB
        → incoming-classifier
            ├─ 非通知 → 非通知_アナウンス(TTS) → 完了フラグ_非通知(status=2,smsFlag=-1) → 切断
            └─ 通常 → acceptance_times
                        ├─ 時間外 → 時間外_アナウンス(TTS) → 完了フラグ_時間外(status=6,smsFlag=-1) → 切断
                        └─ 受付可 → 冒頭_アナウンス(TTS)
                                      → ジャンプ_氏名聴取(Custom Jump to Flow)
                                      → ジャンプ_生年月日聴取(Custom Jump to Flow)
                                      → ジャンプ_電話番号聴取(Custom Jump to Flow)
                                      → 用件確認(TTS+STT+OpenAI)
                                          ├─ 予約 → TODO_要確認（予約ルート詳細は Customer Docs 参照）
                                          │     → ジャンプ_RAG(pre-termination) → END_受付完了
                                          ├─ 変更 → TODO_要確認（変更ルート詳細は Customer Docs 参照）
                                          │     → ジャンプ_RAG(pre-termination) → END_変更完了
                                          ├─ キャンセル → TODO_要確認（キャンセルルート詳細は Customer Docs 参照）
                                          │     → ジャンプ_RAG(pre-termination) → END_キャンセル完了
                                          └─ その他問合せ → 問合せ内容(STT+OpenAI)
                                                → ジャンプ_RAG(inquiry) → END_問い合わせ

      ─── 終話パターン ───
      END_受付完了: 完了フラグ_受付完了(status=1,smsFlag=TODO_要確認) → 終話_受付完了(TTS) → 切断
      END_変更完了: 完了フラグ_変更完了(status=1,smsFlag=TODO_要確認) → 終話_変更完了(TTS) → 切断
      END_キャンセル完了: 完了フラグ_キャンセル完了(status=1,smsFlag=TODO_要確認) → 終話_キャンセル完了(TTS) → 切断
      END_問い合わせ: 完了フラグ_問い合わせ(status=1,smsFlag=TODO_要確認) → 終話_問い合わせ(TTS) → 切断
      END_聴取失敗: 完了フラグ_聴取失敗(status=3,smsFlag=-1) → 終話_聴取失敗(TTS) → 切断
    notes: |
      Customer Docs（【健診1】：諏訪赤十字病院健診センター.md）が欠落。
      標準的な健診フロー構造でスケルトンを作成。予約・変更・キャンセル各ルートの
      詳細聴取ステップ（予約種類・健診種類等）はCustomer Docs確認後に補完すること。

  - flow_name: "諏訪赤十字病院健診センター$氏名聴取"
    diagram: |
      docs/reference/bivr/samples/json/氏名聴取.json を完全コピー。
      フロー名プレフィックスのみ「諏訪赤十字病院健診センター$」に置換。
    notes: "CLAUDE.md Rule 9/11 準拠。個人情報サブフロー.bivr を完全コピー。"

  - flow_name: "諏訪赤十字病院健診センター$生年月日聴取"
    diagram: |
      docs/reference/bivr/samples/json/生年月日聴取.json を完全コピー。
      フロー名プレフィックスのみ「諏訪赤十字病院健診センター$」に置換。
    notes: "CLAUDE.md Rule 9/11 準拠。復唱あり（デフォルト）。"

  - flow_name: "諏訪赤十字病院健診センター$電話番号聴取"
    diagram: |
      docs/reference/bivr/samples/json/電話番号聴取_復唱あり.json を完全コピー。
      フロー名プレフィックスのみ「諏訪赤十字病院健診センター$」に置換。
    notes: "CLAUDE.md Rule 9/10/11 準拠。"

  - flow_name: "諏訪赤十字病院健診センター$RAG検索"
    diagram: |
      docs/reference/bivr/samples/json/RAG検索.json を完全コピー。
      フロー名プレフィックスのみ「諏訪赤十字病院健診センター$」に置換。
    notes: "CLAUDE.md Rule 16 準拠。パターン3。"

# --- セクション4b: シナリオフロー定義（ブロック構成）---
scenario_flow:
  # --- 冒頭ブロック ---
  - step: 冒頭
    type: opening
    use_acceptance_times: true
    next: 用件確認

  # --- サブフロー: 個人情報聴取 ---
  - step: jump_氏名聴取
    type: subflow
    flowname: "諏訪赤十字病院健診センター$氏名聴取"
    next: jump_生年月日聴取

  - step: jump_生年月日聴取
    type: subflow
    flowname: "諏訪赤十字病院健診センター$生年月日聴取"
    next: jump_電話番号聴取

  - step: jump_電話番号聴取
    type: subflow
    flowname: "諏訪赤十字病院健診センター$電話番号聴取"
    next: 用件確認

  # --- 聴取ブロック: 用件確認 ---
  - step: 用件確認
    type: hearing
    output_format: enum
    echo_back: false
    conditions:
      - match: "予約"
        next: END_受付完了
      - match: "変更"
        next: END_変更完了
      - match: "キャンセル"
        next: END_キャンセル完了
      - match: "その他問合せ"
        next: 問合せ内容

  # --- 聴取ブロック: 問合せ内容 ---
  - step: 問合せ内容
    type: hearing
    output_format: text
    next: jump_RAG検索_inquiry

  # --- RAGサブフロー（問合せルート）---
  - step: jump_RAG検索_inquiry
    type: subflow
    flowname: "諏訪赤十字病院健診センター$RAG検索"
    next: END_問い合わせ

  # --- 終話ブロック ---
  - step: END_受付完了
    type: termination
    termination_ref: "END_受付完了"

  - step: END_変更完了
    type: termination
    termination_ref: "END_変更完了"

  - step: END_キャンセル完了
    type: termination
    termination_ref: "END_キャンセル完了"

  - step: END_問い合わせ
    type: termination
    termination_ref: "END_問い合わせ"

# --- セクション5: コンテキストフィールド一覧（saveContextModel2DB 用）---
context_fields:
  # --- 標準フィールド（itemDefault: true）---
  - context_name: "classification"
    context_name_jp: "用件"
    display_type: "CLASSIFICATION"
    range_values:
      - order: "1"
        value: "予約"
      - order: "2"
        value: "変更"
      - order: "3"
        value: "キャンセル"
      - order: "4"
        value: "その他問合せ"
    item_default: true
    editable: true
    deletable: true
    notes: "用件区分。TODO_要確認: Customer Docs から正確な選択肢を確認"

  - context_name: "patientName"
    context_name_jp: "氏名"
    display_type: "TEXT"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "氏名聴取サブフローで聴取。カタカナ変換"

  - context_name: "patientDateOfBirth"
    context_name_jp: "生年月日"
    display_type: "DATE_OF_BIRTH"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "生年月日聴取サブフローで聴取"

  - context_name: "telephoneNumber"
    context_name_jp: "電話番号（着信）"
    display_type: "PHONE_NUMBER_CALL"
    range_values: []
    item_default: true
    editable: false
    deletable: true
    notes: "着信番号自動格納"

  - context_name: "additionalPhoneNumber"
    context_name_jp: "連絡先電話番号"
    display_type: "PHONE_NUMBER"
    range_values: []
    item_default: true
    editable: true
    deletable: true
    notes: "電話番号聴取サブフローで聴取"

  - context_name: "status"
    context_name_jp: "状態"
    display_type: "STATUS"
    range_values:
      - order: "1"
        value: "未処理"
      - order: "2"
        value: "非通知"
      - order: "3"
        value: "聴取失敗"
      - order: "6"
        value: "時間外"
    item_default: true
    editable: true
    deletable: true
    notes: "1=未処理(正常完了) 2=非通知 3=聴取失敗 6=時間外"

  - context_name: "dateOfCall"
    context_name_jp: "受電日時"
    display_type: "DATE"
    range_values: []
    item_default: true
    editable: false
    deletable: false
    notes: "受電日時自動格納"

  - context_name: "callId"
    context_name_jp: "通話ID"
    display_type: "TEXT"
    range_values: []
    item_default: true
    editable: false
    deletable: true
    notes: "通話ID自動格納"

  # --- 施設固有フィールド（itemDefault: false）---
  - context_name: "inquiry"
    context_name_jp: "問合せ内容"
    display_type: "TEXT"
    range_values: []
    item_default: false
    editable: true
    deletable: true
    notes: "その他問合せルートのみ。フリーテキスト"

  # TODO_要確認: Customer Docs確認後に予約種類・健診種類等の施設固有フィールドを追加

# --- セクション6: 聴取項目一覧 ---
hearing_items:
  # --- サブフローで聴取する個人情報 ---
  - order: 1
    name: "氏名"
    stt_type: "AmiVoice_STT"
    dtmf_max_length: null
    retry_count: 2
    echo_back: false
    save_to: "patientName"
    openai_processing: "normalize"
    output_format: "text"
    output_labels: []
    notes: "氏名聴取サブフロー内。カタカナ変換"

  - order: 2
    name: "生年月日"
    stt_type: "AmiVoice_STT"
    dtmf_max_length: null
    retry_count: 2
    echo_back: false
    save_to: "patientDateOfBirth"
    openai_processing: "convert"
    output_format: "datetime"
    output_labels: []
    notes: "生年月日聴取サブフロー内。復唱あり"

  - order: 3
    name: "電話番号"
    stt_type: "DTMF_AmiVoice"
    dtmf_max_length: 11
    retry_count: 2
    echo_back: true
    save_to: "additionalPhoneNumber"
    openai_processing: "normalize"
    output_format: "text"
    output_labels: []
    notes: "電話番号聴取サブフロー内。incoming-classifier分岐。DTMF 0-9=電話番号の各桁入力, max_dtmf_length=11"

  # --- メインフローで聴取する業務項目 ---
  - order: 4
    name: "用件確認"
    stt_type: "DTMF_AmiVoice"
    dtmf_max_length: 1
    retry_count: 2
    echo_back: false
    save_to: "classification"
    openai_processing: "classify"
    output_format: "enum"
    output_labels:
      - "予約"
      - "変更"
      - "キャンセル"
      - "その他問合せ"
    notes: "DTMF 1=予約, 2=変更, 3=キャンセル, 4=その他問合せ。TODO_要確認: Customer Docs から正確な選択肢数を確認"

  - order: 5
    name: "問合せ内容"
    stt_type: "AmiVoice_STT"
    dtmf_max_length: null
    retry_count: 2
    echo_back: false
    save_to: "inquiry"
    openai_processing: "summarize"
    output_format: "text"
    output_labels: []
    notes: "音声のみ。フリーテキスト。その他問合せルートのみ"

  # TODO_要確認: Customer Docs確認後に予約ルート・変更ルート・キャンセルルートの聴取項目を追加

# --- セクション7: ステップ詳細 ---
step_details:
  # === 個人情報（サブフロー — 静的JSONコピーのため詳細省略）===
  # 氏名聴取: docs/reference/bivr/samples/json/氏名聴取.json 完全コピー
  # 生年月日聴取: docs/reference/bivr/samples/json/生年月日聴取.json 完全コピー
  # 電話番号聴取: docs/reference/bivr/samples/json/電話番号聴取_復唱あり.json 完全コピー

  # === メインフロー: 用件聴取 ===
  - step_name: "用件確認"
    tts_announcement: "TODO_要確認"
    input_method: "dtmf_voice"
    openai_rules:
      output_values:
        - "予約"
        - "変更"
        - "キャンセル"
        - "その他問合せ"
        - "NO_RESULT"
      mapping:
        - input: "DTMF 1 または「予約」「よやく」等を含む"
          output: "予約"
        - input: "DTMF 2 または「変更」「予約変更」等を含む"
          output: "変更"
        - input: "DTMF 3 または「キャンセル」「取り消し」等を含む"
          output: "キャンセル"
        - input: "DTMF 4 または「問合せ」「質問」等を含む"
          output: "その他問合せ"
      no_result_condition: "上記いずれにも該当しない"
    save_to: "classification"
    next_step: "予約→END_受付完了 / 変更→END_変更完了 / キャンセル→END_キャンセル完了 / その他問合せ→問合せ_内容"
    retry_failure: "end_failure"

  - step_name: "問合せ内容"
    tts_announcement: "TODO_要確認"
    input_method: "voice_only"
    openai_rules:
      output_values:
        - "フリーテキスト"
      mapping:
        - input: "音声認識結果"
          output: "フリーテキスト（そのまま保存）"
      no_result_condition: "音声認識結果が空"
    save_to: "inquiry"
    next_step: "ジャンプ_RAG(inquiry) → END_問い合わせ"
    retry_failure: "skip"

  # TODO_要確認: Customer Docs確認後に予約ルート・変更ルート・キャンセルルートのステップ詳細を追加

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
    tts_announcement: "お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。"
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
    condition: "予約ルート完了"
    tts_announcement: "TODO_要確認"
    status: "1"
    sms_flag: "1"
    completion_flag_name: "完了フラグ_受付完了"

  - name: "END_変更完了"
    condition: "変更ルート完了"
    tts_announcement: "TODO_要確認"
    status: "1"
    sms_flag: "1"
    completion_flag_name: "完了フラグ_変更完了"

  - name: "END_キャンセル完了"
    condition: "キャンセルルート完了"
    tts_announcement: "TODO_要確認"
    status: "1"
    sms_flag: "1"
    completion_flag_name: "完了フラグ_キャンセル完了"

  - name: "END_問い合わせ"
    condition: "その他問合せルート完了"
    tts_announcement: "TODO_要確認"
    status: "1"
    sms_flag: "1"
    completion_flag_name: "完了フラグ_問い合わせ"

# smsFlag分岐設計
sms_flag_routing:
  enabled: false
  routing_keys: []
  patterns: []

# --- セクション8b: RAG/FAQ検索サブフロー ---
rag_subflow:
  pattern: "3"
  inquiry_insertion_point: "問合せ内容聴取後"
  pre_termination: true

# --- セクション9: TTSモジュール一覧 ---
tts_modules:
  - module_name: "冒頭_アナウンス"
    purpose: "冒頭施設案内"
    announcement: "お電話ありがとうございます。諏訪赤十字病院健診センターのAI電話です。音声ガイダンスに従い、お答えください。"

  - module_name: "非通知_アナウンス"
    purpose: "非通知案内"
    announcement: "恐れ入りますが、電話番号を通知しておかけ直しください。お電話ありがとうございました。"

  - module_name: "時間外_アナウンス"
    purpose: "時間外案内"
    announcement: "お電話ありがとうございます。ただいまの時間は受付時間外です。受付時間内におかけ直しください。お電話ありがとうございました。"

  - module_name: "用件確認"
    purpose: "用件選択案内"
    announcement: "TODO_要確認"

  - module_name: "問合せ_内容"
    purpose: "問合せ内容聴取案内"
    announcement: "TODO_要確認"

  - module_name: "終話_受付完了"
    purpose: "予約受付完了終話"
    announcement: "TODO_要確認"

  - module_name: "終話_変更完了"
    purpose: "予約変更完了終話"
    announcement: "TODO_要確認"

  - module_name: "終話_キャンセル完了"
    purpose: "キャンセル完了終話"
    announcement: "TODO_要確認"

  - module_name: "終話_問い合わせ"
    purpose: "問い合わせ完了終話"
    announcement: "TODO_要確認"

  - module_name: "終話_聴取失敗"
    purpose: "聴取失敗終話"
    announcement: "申し訳ございません。ご回答を正しく聞き取ることができませんでした。恐れ入りますが、おかけ直しください。お電話ありがとうございました。"

# --- セクション10: AmiVoice辞書（profile_words）---
amivoice_dictionary:
  - step_name: "用件確認"
    words: |
      予約 よやく
      変更 へんこう
      キャンセル きゃんせる
      問合せ といあわせ
      取り消し とりけし
      問い合わせ といあわせ
      予約変更 よやくへんこう

  # TODO_要確認: Customer Docs確認後に予約ルート関連の辞書を追加

# --- セクション11: 特記事項・制約 ---
special_notes:
  - "Customer Docs（【健診1】：諏訪赤十字病院健診センター.md）が存在しないため、標準的な健診フロー構造でスケルトンを生成。Customer Docs 配置後に @director で再生成が必要"
  - "Gen2→Gen3移管案件。個人情報聴取はサブフロー分割型"
  - "RAGサブフローはパターン3（Gen2→Gen3デフォルト）: 問合せルート内 + 全終話前に配置"

# --- セクション12: 要確認事項 ---
confirmation_items:
  - item: "【BLOCKER】Customer Docs ファイル（docs/reference/customer_docs/【健診1】：諏訪赤十字病院健診センター.md）を配置し、@director で設計書を再生成すること"
    resolved: false
  - item: "営業時間（曜日・時間帯）"
    resolved: false
  - item: "office_id"
    resolved: false
  - item: "対象環境（デモ/本番）"
    resolved: false
  - item: "smsFlag の割り当て（各終話パターン別）"
    resolved: false
  - item: "各TTS発話文言（Customer Docs から転記）"
    resolved: false
  - item: "予約ルート・変更ルート・キャンセルルートの詳細聴取ステップ"
    resolved: false
  - item: "施設固有のコンテキストフィールド（予約種類・健診種類等）"
    resolved: false
