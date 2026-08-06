# S2 TEST_CANNOT_FAIL — expected clean: declared skip body.
import pytest

def test_not_supported():
    pytest.skip("not supported")
