"""n_choice — spec 自己整合性 lint の回帰テスト（#245）

lint_config が「テストで落ちるケースを除外して合格にする」運用の温床になる
spec 不備（dead keyword / shadow）を実際に検出できることを保証する。
clean な spec は誤検出しないことも確認する。
実行: python3 modules/n_choice/test_lint.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oracle  # noqa: E402


def _has_literal(issues, literal):
    return any(it["literal"] == literal for it in issues)


def test_dead_keyword_desu_stripped():
    """bug1 クラス: 語尾「です」が正規化で除去され keyword「そうです」が死ぬ spec を検出。"""
    bad = {
        "dtmf_map": {"1": "あり", "2": "なし"},
        "token_map": [],
        "digit_keyword_patterns": [],
        "compound_patterns": [],
        "keyword_patterns": [
            {"regex": "そうです|はい", "result": "あり"},   # 「そうです」→正規化で「そう」になり死ぬ
            {"regex": "いいえ|ちがいます", "result": "なし"},
        ],
    }
    # 前提の不変条件が崩れていること（実機相当）を確認
    assert oracle.classify("そうです", bad) != "あり", "前提: そうです は死んでいるはず"
    issues = oracle.lint_config(bad)
    assert _has_literal(issues, "そうです"), f"dead keyword を検出できていない: {issues}"


def test_shadowed_pattern_precedence():
    """bug2 クラス: 後置の具体パターンが先行の広いパターンに食われる shadow を検出。"""
    bad = {
        "dtmf_map": {"1": "予約", "2": "変更"},
        "token_map": [],
        "digit_keyword_patterns": [],
        "compound_patterns": [],
        "keyword_patterns": [
            {"regex": "予約", "result": "予約"},        # 広い先行
            {"regex": "予約変更|予約を変更", "result": "変更"},  # 後置だが「予約」に食われる
        ],
    }
    assert oracle.classify("予約変更", bad) == "予約", "前提: 予約変更 は予約に食われるはず"
    issues = oracle.lint_config(bad)
    assert _has_literal(issues, "予約変更"), f"shadow を検出できていない: {issues}"


def test_clean_config_no_false_positive():
    """健全な spec を誤検出しないこと（既存 11 spec も含めて確認）。"""
    clean = {
        "dtmf_map": {"1": "あり", "2": "なし"},
        "token_map": [],
        "digit_keyword_patterns": [],
        "compound_patterns": [],
        "keyword_patterns": [
            {"regex": "そう|はい|あり", "result": "あり"},   # 正規化後も生きるリテラル
            {"regex": "いいえ|ちがう|なし", "result": "なし"},
        ],
    }
    assert oracle.lint_config(clean) == [], "clean config を誤検出している"
    # 認定済み全 spec が lint を通ること（regression）
    import test_oracle  # noqa: E402
    for spec, cfg in test_oracle.SPECS.items():
        assert oracle.lint_config(cfg) == [], f"既存 spec {spec} が lint で落ちた（誤検出 or 真の不備）"


def main():
    tests = [
        test_dead_keyword_desu_stripped,
        test_shadowed_pattern_precedence,
        test_clean_config_no_false_positive,
    ]
    fail = 0
    for t in tests:
        try:
            t()
            print(f"[n_choice lint test] {t.__name__}: PASS")
        except AssertionError as e:
            fail += 1
            print(f"[n_choice lint test] {t.__name__}: FAIL — {e}")
    print(f"[n_choice lint test] {len(tests) - fail}/{len(tests)} PASS")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
