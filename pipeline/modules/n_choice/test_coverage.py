"""n_choice — P6 受入カバレッジの回帰テスト（#245）

coverage() が「狭いスコープ」を定量検出できること、classify_trace の発火 id が
カバレッジ母集合と整合すること（被覆率の計算が壊れていないこと）を保証する。
実行: python3 modules/n_choice/test_coverage.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402

YESNO = {
    "dtmf_map": {"1": "あり", "2": "なし"},
    "token_map": [],
    "digit_keyword_patterns": [],
    "compound_patterns": [],
    "keyword_patterns": [
        {"regex": "あり|はい|そう", "result": "あり"},
        {"regex": "なし|いいえ|ちがう", "result": "なし"},
    ],
}


def test_structural_fail_on_missing_dtmf():
    """DTMF の片方を叩かないケース集合は構造 FAIL。"""
    cov = oracle.coverage(YESNO, ["1", "あり", "なし", ""])  # dtmf "2" を未被覆
    assert cov["structural_ok"] is False, "DTMF 未被覆を検出できていない"
    dc, dt = cov["dtmf"]
    assert "2" in set(dt) - set(dc)


def test_structural_fail_on_missing_label():
    """あるラベルに到達するケースが無ければ構造 FAIL。"""
    cov = oracle.coverage(YESNO, ["1", "2", "あり", ""])  # 結果に「なし」が出ない…
    # ↑ dtmf "2"→なし なので label なし は被覆される。なしを完全に消すには dtmf も外す:
    cov2 = oracle.coverage(YESNO, ["1", "あり", "はい", ""])  # なし系を一切叩かない
    assert cov2["structural_ok"] is False
    lc, lt = cov2["labels"]
    assert "なし" in set(lt) - set(lc)


def test_structural_fail_on_missing_no_result():
    """NO_RESULT を期待するケースが無ければ構造 FAIL。"""
    cov = oracle.coverage(YESNO, ["1", "2", "あり", "なし"])  # NO_RESULT ケースなし
    assert cov["no_result_case"] is False
    assert cov["structural_ok"] is False


def test_structural_ok_when_complete():
    """全ラベル・全 DTMF・NO_RESULT を網羅すれば構造 OK。"""
    cov = oracle.coverage(YESNO, ["1", "2", "あり", "なし", "ぐぬぬ"])
    assert cov["structural_ok"] is True


def test_surface_coverage_counts():
    """表面被覆 = 叩いたリテラル / 全リテラル。叩いた分だけ被覆に入る。"""
    cov = oracle.coverage(YESNO, ["あり", "なし"])  # 各 keyword[0]:あり / keyword[1]:なし のみ
    sc, st = cov["surface"]
    assert "keyword:0:あり" in sc and "keyword:1:なし" in sc
    assert "keyword:0:はい" not in sc and "keyword:0:そう" not in sc
    assert set(sc) <= set(st)


def test_trace_ids_within_universe():
    """classify_trace の発火 id（surface 系）が必ず coverage 母集合に含まれること。
    一致しないと被覆率が過小評価される（計算の健全性インバリアント）。"""
    import test_oracle  # noqa: E402

    BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "acceptance_test")
    for spec, cfg in test_oracle.SPECS.items():
        path = os.path.join(BASE, spec, "cases.tsv")
        if not os.path.exists(path):
            continue
        inputs = [inp for inp, _ in test_oracle.load_cases(path)]
        _, surface_total = oracle.coverage(cfg, inputs)["surface"]
        universe = set(surface_total)
        for x in inputs:
            _, eid = oracle.classify_trace(x, cfg)
            if eid == "NO_RESULT" or eid.startswith("dtmf:"):
                continue
            assert eid in universe, f"{spec}: 発火 id {eid!r} が母集合外（input={x!r}）"


def test_density_warns_on_thin_voice_only_label():
    """音声 < 3 形 かつ DTMF 救済なしのラベルは WARN（合意した初期判定）。"""
    cfg = {
        "dtmf_map": {"1": "予約"},  # 「予約」だけ DTMF 救済、「相談」は音声のみ
        "token_map": [],
        "digit_keyword_patterns": [],
        "compound_patterns": [],
        "keyword_patterns": [
            {"regex": "予約|よやく|予約したい", "result": "予約"},
            {"regex": "相談", "result": "相談"},  # 音声 1 形・DTMF なし → WARN
        ],
    }
    dr = oracle.density_report(cfg, floor=3)
    assert dr["相談"]["warn"] is True, "音声のみ薄ラベルを WARN できていない"
    assert dr["予約"]["warn"] is False, "DTMF 救済ラベルを誤って WARN している"


def test_density_no_warn_when_dtmf_backed():
    """薄くても DTMF 救済があれば WARN しない（入院/電話 型）。"""
    cfg = {
        "dtmf_map": {"1": "入院", "2": "外来"},
        "token_map": [],
        "digit_keyword_patterns": [],
        "compound_patterns": [],
        "keyword_patterns": [
            {"regex": "入院", "result": "入院"},        # 1 形だが DTMF 救済あり
            {"regex": "外来|通院", "result": "外来"},
        ],
    }
    dr = oracle.density_report(cfg, floor=3)
    assert dr["入院"]["warn"] is False and dr["入院"]["dtmf_backed"] is True


def main():
    tests = [
        test_structural_fail_on_missing_dtmf,
        test_structural_fail_on_missing_label,
        test_structural_fail_on_missing_no_result,
        test_structural_ok_when_complete,
        test_surface_coverage_counts,
        test_trace_ids_within_universe,
        test_density_warns_on_thin_voice_only_label,
        test_density_no_warn_when_dtmf_backed,
    ]
    fail = 0
    for t in tests:
        try:
            t()
            print(f"[n_choice cov test] {t.__name__}: PASS")
        except AssertionError as e:
            fail += 1
            print(f"[n_choice cov test] {t.__name__}: FAIL — {e}")
    print(f"[n_choice cov test] {len(tests) - fail}/{len(tests)} PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
