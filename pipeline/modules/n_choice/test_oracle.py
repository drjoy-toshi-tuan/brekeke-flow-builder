"""n_choice — オラクル単体テスト（各 spec の acceptance_test/<spec>/cases.tsv を実行）

n_choice は設問ごとに config（DTMF_MAP/KEYWORD_PATTERNS 等）を充填する汎用エンジン。
spec ディレクトリ名 → oracle config の対応で、亀田の各設問 spec をまとめて検証する。
cases.tsv が無い spec はスキップ（受入セット未整備でも他 spec は回る）。
実行: python3 modules/n_choice/test_oracle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acceptance_test")

# spec ディレクトリ名 → oracle config
SPECS = {
    "発信元": oracle.KAMEDA_CALLER_TYPE,
    "相談区分": oracle.KAMEDA_PATIENT_CATEGORY,
    "担当者確認": oracle.KAMEDA_STAFF_KNOWN,
    "F1": oracle.KAMEDA_F1,
    # A3 Phase2 部品調達（count>=2 の真の多択）
    "受診歴_再診新規": oracle.SAISHIN_SHINKI,
    "顧客種別_企業個人": oracle.KIGYO_KOJIN,
    "受診歴_再診初診": oracle.SAISHIN_SHOSHIN,
    "当日確認_別日本日": oracle.BETSUJITSU_HONJITSU,
    "変更内容_受診日程": oracle.HENKO_NAIYO_NITTEI,
    "予約手段_ネット電話": oracle.NET_DENWA,
    "残薬確認": oracle.ZANYAKU,
    # 被覆スコアカード逆設計の用件ベース spec（#271・ストア手渡し INQUIRY_BASE）
    "用件": oracle.INQUIRY_BASE,
    # カレス記念病院_診療（Pattern 1 新規・CSV入口）調達分
    "受診歴_はいいいえわからない": oracle.JUSHINREKI_HAIIIEWAKARANAI,
    "服薬有無": oracle.FUKUYAKU_UMU,
    "残薬有無_2択": oracle.ZANYAKU_2CHOICE,
}


def load_cases(path):
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            cases.append((parts[0], parts[1]))
    return cases


def lint_specs():
    """全 spec を自己整合性 lint にかける（#245 マシンガード）。
    1 件でも dead/shadow パターンがあれば FAIL（テスト除外で合格にする運用を機械的に封じる）。"""
    any_fail = False
    for spec, cfg in SPECS.items():
        issues = oracle.lint_config(cfg)
        if issues:
            any_fail = True
            print(f"[n_choice lint] {spec}: FAIL（{len(issues)} 件の dead/shadow パターン）")
            for it in issues:
                print(
                    f"    {it['where']}: リテラル {it['literal']!r} は "
                    f"{it['result']!r} に分類されるべきだが classify は {it['got']!r} を返す "
                    f"→ spec を修正すること（テストから除外して合格にするのは禁止 / #245）"
                )
        else:
            print(f"[n_choice lint] {spec}: PASS")
    return any_fail


def report_coverage(spec, cfg, inputs):
    """P6 受入カバレッジ（#245）を出力。構造未被覆なら True（=FAIL）を返す。
    表面被覆は % と未カバー一覧をレポートするのみ（FAIL にしない）。"""
    cov = oracle.coverage(cfg, inputs)
    lc, lt = cov["labels"]
    dc, dt = cov["dtmf"]
    sc, st = cov["surface"]
    spct = (100.0 * len(sc) / len(st)) if st else 100.0
    print(
        f"[n_choice cov] {spec}: 構造 labels {len(lc)}/{len(lt)} "
        f"dtmf {len(dc)}/{len(dt)} no_result={'有' if cov['no_result_case'] else '無'} | "
        f"表面 {len(sc)}/{len(st)} ({spct:.0f}%)"
    )
    if not cov["structural_ok"]:
        miss_l = sorted(set(lt) - set(lc))
        miss_d = sorted(set(dt) - set(dc))
        print(
            f"    STRUCTURAL FAIL: 未カバー labels={miss_l} dtmf={miss_d} "
            f"no_result={'OK' if cov['no_result_case'] else '欠落'} "
            f"→ 受入ケースを追加すること（除外して合格は禁止 / #245）"
        )
    uncovered = sorted(set(st) - set(sc))
    if uncovered:
        # 表面未カバー = テストが避けた言い回し。スコア向上はスコアカード PJ だが可視化はする。
        print(f"    表面未カバー（要追補・WARN）: {uncovered}")
    return not cov["structural_ok"]


def report_density(spec, cfg, floor=3):
    """類義語密度（#245）を出力。薄いラベルは WARN（スコアカード検証候補）。FAIL にはしない。"""
    dr = oracle.density_report(cfg, floor=floor)
    counts = sorted(d["count"] for d in dr.values())
    median = counts[len(counts) // 2] if counts else 0
    warns = {l: d for l, d in dr.items() if d["warn"]}
    thin_dtmf = {l: d for l, d in dr.items()
                 if d["count"] < floor and d["dtmf_backed"] and not d["warn"]}
    print(f"[n_choice density] {spec}: ラベル類義語 中央値 {median} 形 / floor={floor}")
    for label, d in sorted(warns.items(), key=lambda x: x[1]["count"]):
        print(
            f"    WARN 薄いラベル（音声 {d['count']} 形・DTMF救済なし）: {label!r} {d['forms']} "
            f"→ スコアカード PJ で実ログ検証を推奨（類義語の取りこぼし精度は実ログでしか測れない）"
        )
    if thin_dtmf:
        labels = ", ".join(f"{l}({d['count']}形)" for l, d in sorted(thin_dtmf.items()))
        print(f"    info 薄いが DTMF 救済あり（単形語か要確認）: {labels}")


def main():
    total = 0
    passed = 0
    any_fail = False
    for spec, cfg in SPECS.items():
        path = os.path.join(BASE, spec, "cases.tsv")
        if not os.path.exists(path):
            print(f"[n_choice oracle] {spec}: cases.tsv なし — スキップ")
            continue
        cases = load_cases(path)
        p = 0
        fails = []
        for inp, expected in cases:
            got = oracle.classify(inp, cfg)
            if got == expected:
                p += 1
            else:
                fails.append((inp, expected, got))
        total += len(cases)
        passed += p
        status = "PASS" if not fails else "FAIL"
        print(f"[n_choice oracle] {spec}: {p}/{len(cases)} {status}")
        for inp, expected, got in fails:
            any_fail = True
            print(f"    FAIL input={inp!r} expected={expected!r} got={got!r}")
        # P6 受入カバレッジ（#245）— 構造未被覆は FAIL、表面はレポートのみ
        if report_coverage(spec, cfg, [inp for inp, _ in cases]):
            any_fail = True
        # 類義語密度（#245）— 薄いラベルは WARN（スコアカード検証候補・FAIL にしない）
        report_density(spec, cfg)
    print(f"[n_choice oracle] 合計 {passed}/{total} PASS")
    # spec 自己整合性 lint（#245）— cases.tsv の有無に依らず全 spec を検査
    if lint_specs():
        any_fail = True
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
