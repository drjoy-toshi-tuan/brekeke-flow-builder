import { sampleScriptsBlock } from './samples';

// ─────────────────────────────────────────────────────────────────────────────
// Knowledge cho AI sinh code/prompt chuẩn Brekeke.
//
//   - BREKEKE_SCRIPT_KNOWLEDGE: bản chắt lọc API $runner / $ivr + quy ước kết quả
//     (rút từ các script THẬT đang chạy) + few-shot là chính các script mẫu đó
//     (src/ai/samples/). Đây là phần định hình để AI gen code không bị lỗi.
//   - OPENAI_PROMPT_KNOWLEDGE: khung cho prompt của node OpenAI — sẽ bổ sung mẫu sau.
// ─────────────────────────────────────────────────────────────────────────────

// API reference chắt lọc từ script thật (custom_classification, Clinical Department
// Classifier, DOB Re-confirmation, Module Result Binder, Phone Normalization).
const BREKEKE_API_GUIDE = `## 実行環境
- スクリプトは AI電話 (Brekekeベース) の Logic ノード「Script」モジュールの本体として実行される。
- 言語: ES5相当の JavaScript（var / function を使う。アロー関数・let/const・テンプレートリテラルは避ける）。
- ブラウザ/Node API（window, document, require, fetch 等）は使用不可。
- 発信者の回答（STT 済みテキスト、または DTMF）を解析し、結果を setResult で返す。

## $runner API
- var logger = $runner.getLogger(); logger.info(msg) / logger.warn(msg) / logger.error(msg)
- $runner.getProperty(name) → ノードのプロパティ値（未設定は null）。例: "module"（参照元モジュール名）, "prompt", "saveXxx2DB"。
- $runner.getModuleResult(moduleName) → 他モジュールの結果。文字列 or { text: "..." } の両方あり得る。
    必ずガードする:
      var r = $runner.getModuleResult(name);
      var text = (r && typeof r === "object" && r.text) ? String(r.text) : (r == null ? "" : String(r));
      text = text.trim();
- $runner.getObject(name) / $runner.setObject(name, value) → コンテキストオブジェクト。setObject した値は後続で <%name%> として参照可能。
- $runner.get(key) / $runner.set(key, value) → 通話内セッション変数（例: "seq" の連番管理）。
- $runner.setResult(value) → 【最重要】ここで返す文字列がノードの分岐正規表現（^value$）と照合され分岐が決まる。
    NO_RESULT / REPEAT / INVALID などでも必ず setResult する（リトライ・フォールバック分岐のため）。

## $ivr API
- $ivr.exec("save2db", "save", JSON.stringify({ contextField: { contextName, displayType, value } }))
    → コンテキストを DB 保存。displayType: CLASSIFICATION | DEPARTMENT | DATE | DATE_OF_BIRTH | PHONE_NUMBER | NUMBER | TEXT。
- $ivr.exec("save2db", "save", JSON.stringify({ utterance: {...} })) → 対話ログ保存。
- $ivr.exec("save2db", "parseTimestamp", isoString) → ミリ秒タイムスタンプ。
- $ivr.exec("tts-prompt", "extractTaggedContent", JSON.stringify({ prompt: p, stripTags: true })) → TTSタグ除去。
- $ivr.exec("system-variable", "replaceTemplateVariables", text) → <%変数%> を展開。
- $ivr.play(prompt, true) → TTS 再生。プロンプト内の #data# は算出値へ置換して使う（prompt.split("#data#").join(value)）。
- $ivr.connected() → 接続中か。$ivr.getRID() → リクエストID。$ivr.getOtherNumber() → 発信者番号。
- 外部呼び出し（save2db 等）は必ず try/catch で囲む。

## 結果 (setResult) の慣習値
- NO_RESULT : 入力なし/空
- REPEAT    : 「もう一度」等の聞き返し要求
- INVALID   : 不正入力（再質問へ）
- TIMEOUT / ERROR（または time_out / error）: 参照元モジュール異常はそのまま透過
- NOT_COVERED : 値は取れたがどのグループにも該当しない
- それ以外   : intent ラベル/正規化値（分岐の正規表現と一致させる）

## STT 正規化の定石（正規表現照合の前に必ず実施）
- 全角数字→半角、全角英字→半角、カタカナ→ひらがな、記号・空白除去。
- 元号/数字の STT 誤認識補正（例: 円→年、じゅう→10 系）。単音番号＋助動詞は ^…$ 完全一致で誤判定回避。`;

export const BREKEKE_SCRIPT_KNOWLEDGE = `${BREKEKE_API_GUIDE}

## 出力ルール
- 出力は完成したスクリプト本体（純 JavaScript）のみ。Markdown・説明・\`\`\` フェンスは付けない。
- 構文エラーがなく（new Function で parse 可能）、上記 API 慣習に従うこと。

## 実際に稼働しているサンプル（このスタイル・APIに厳密に従うこと）
${sampleScriptsBlock()}`;

export const OPENAI_PROMPT_KNOWLEDGE = `
## Bối cảnh node OpenAI
- Prompt chạy trong node OpenAI của flow AI電話: nhận câu trả lời (đã STT) của người gọi
  và phải phân tích/chuẩn hoá nó theo yêu cầu, output khớp với các nhánh của node.
- Prompt nên: nêu vai trò, mô tả input, liệt kê các giá trị output hợp lệ, ràng buộc
  "chỉ trả về 1 trong các giá trị đó, không thêm chữ nào khác".

## Prompt mẫu (DÁN THÊM các mẫu chuẩn vào đây khi có)
(chưa có mẫu — sẽ được bổ sung)
`;
