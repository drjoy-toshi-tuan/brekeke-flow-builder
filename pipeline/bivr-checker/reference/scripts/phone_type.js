// Script Template: phone_type
// 入力モジュールから取得した電話番号を「携帯」「固定」「その他」に分類
// プレースホルダー: {{INPUT_MODULE}} = 入力元モジュール名（電話番号文字列）
// 出力: 携帯 / 固定 / その他

var input = $runner.getModuleResult("{{INPUT_MODULE}}");
var res = "その他";

if (input) {
    // 数字以外を除去
    var num = input.toString().replace(/[^0-9]/g, "");

    if (num.length === 11 && /^(070|080|090)/.test(num)) {
        // 070/080/090 から始まる11桁 → 携帯
        res = "携帯";
    } else if (num.length === 11 && /^050/.test(num)) {
        // 050 から始まる11桁 → IP電話（携帯扱い）
        res = "携帯";
    } else if (num.length === 10 && /^0[1-9]/.test(num)) {
        // 0+市外局番（先頭0、2桁目が1-9）の10桁 → 固定
        res = "固定";
    }
}

$runner.setResult(res);
