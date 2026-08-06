# S2 TEST_CANNOT_FAIL — expected clean: parametrized computed names.
import pytest

@pytest.mark.parametrize("actual,expected", [(1, 1)])
def test_pair(actual, expected):
    assert actual == expected
