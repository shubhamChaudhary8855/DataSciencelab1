from app.analyzer import review


def test_eval_is_flagged():
    score, findings = review("value = eval(user_input)", "python")
    assert score < 100
    assert any(f.rule_id == "SEC-EVAL" for f in findings)


def test_hardcoded_secret_is_flagged():
    _, findings = review("api_key = 'super-secret-value'", "python")
    assert any(f.rule_id == "SEC-HARDCODED-SECRET" for f in findings)


def test_clean_code():
    score, findings = review("def add(a, b):\n    return a + b\n", "python")
    assert score == 100
    assert findings == []
