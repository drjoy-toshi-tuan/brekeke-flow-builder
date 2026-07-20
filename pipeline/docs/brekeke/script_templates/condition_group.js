// Script Template: condition_group
// 入力モジュールの出力値をグループ番号に分類（多段分岐用）
// プレースホルダー: {{INPUT_MODULE}} = 入力元モジュール名（OpenAI モジュール）
// プレースホルダー: {{MAPPING}} = 値→グループ番号の JSON オブジェクト
// プレースホルダー: {{DEFAULT_GROUP}} = マッピングに該当しない場合のデフォルトグループ番号
// 出力: グループ番号文字列（"1", "2", ... "10"）

var input = $runner.getModuleResult("{{INPUT_MODULE}}");
var mapping = {{MAPPING}};
var group = mapping[input];
if (!group) { group = "{{DEFAULT_GROUP}}"; }
$runner.setResult(group);
