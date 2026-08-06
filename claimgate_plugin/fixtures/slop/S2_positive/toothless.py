# S2 TEST_CANNOT_FAIL — expected to trip.
def test_no_assertion():
    perform_work()

def test_literal_only():
    assert True

def test_did_not_raise():
    try:
        perform_work()
    except Exception:
        assert False
