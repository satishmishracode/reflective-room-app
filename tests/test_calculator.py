import os
import sys
import pytest

# Ensure the project root is on the path so calculator can be imported
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, PROJECT_ROOT)

import calculator


def test_add():
    assert calculator.add(2, 3) == 5


def test_subtract():
    assert calculator.subtract(5, 2) == 3


def test_multiply():
    assert calculator.multiply(4, 3) == 12


def test_divide():
    assert calculator.divide(10, 2) == 5


def test_divide_by_zero():
    with pytest.raises(ValueError):
        calculator.divide(1, 0)
