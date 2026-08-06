# S2 TEST_CANNOT_FAIL — expected clean: declared skip decorator.
import pytest

@pytest.mark.skip(reason="not supported")
def test_not_supported():
    perform_work()
