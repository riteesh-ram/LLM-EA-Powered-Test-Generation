"""
SECTION 8: ====================================================================
GENERATED TESTS
================================================================================
"""


def test_calculator_add():
    result, error = calculator(a=10, operation="add", b=5)
    assert result == 15
    assert error is None


def test_calculator_sub():
    result, error = calculator(a=10, operation="sub", b=5)
    assert result == 5
    assert error is None


def test_calculator_mul():
    result, error = calculator(a=10, operation="mul", b=5)
    assert result == 50
    assert error is None


def test_calculator_div():
    result, error = calculator(a=10, operation="div", b=5)
    assert result == 2.0
    assert error is None


def test_calculator_mod():
    result, error = calculator(a=10, operation="mod", b=5)
    assert result == 0
    assert error is None


def test_calculator_exp():
    result, error = calculator(a=10, operation="exp", b=5)
    assert result == 100000.0
    assert error is None


def test_calculator_floordiv():
    result, error = calculator(a=10, operation="floordiv", b=5)
    assert result == 2
    assert error is None


def test_calculator_sqrt():
    result, error = calculator(a=10, operation="sqrt")
    assert result == 3.1622776601683795
    assert error is None


def test_calculator_sqrt_error():
    result, error = calculator(a=0, operation="sqrt")
    assert result is None
    assert error == "Invalid operation"


def test_statistics_calculator_mean():
    result, error = statistics_calculator(numbers=[1, 2, 3], operation="mean")
    assert result == 2.0
    assert error is None


def test_statistics_calculator_median():
    result, error = statistics_calculator(numbers=[1, 2, 3], operation="median")
    assert result == 2.0
    assert error is None


def test_statistics_calculator_variance():
    result, error = statistics_calculator(numbers=[1, 2, 3], operation="variance")
    assert result == 1.0
    assert error is None


def test_statistics_calculator_std_dev():
    result, error = statistics_calculator(numbers=[1, 2, 3], operation="std_dev")
    assert result == 1.0
    assert error is None


def test_statistics_calculator_invalid_operation():
    result, error = statistics_calculator(numbers=[1, 2, 3], operation="invalid")
    assert result is None
    assert error == "Invalid operation"