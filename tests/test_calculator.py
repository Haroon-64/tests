import pytest

from app.calculator import add, divide, multiply, subtract


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0


def test_subtract():
    assert subtract(5, 2) == 3
    assert subtract(2, 5) == -3
    assert subtract(0, 0) == 0


def test_multiply():
    assert multiply(3, 4) == 12
    assert multiply(-2, 3) == -6
    assert multiply(0, 5) == 0


def test_divide():
    assert divide(10, 2) == pytest.approx(5.0)
    assert divide(-10, 2) == pytest.approx(-5.0)
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
