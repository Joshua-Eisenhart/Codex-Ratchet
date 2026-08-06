# S3 EXCEPT_SWALLOWS_SUCCESS — expected to trip.
def verify_one():
    try:
        work()
    except Exception:
        return True

def check_two():
    try:
        work()
    except Exception:
        return {"ok": True}

def run_three():
    passed = False
    try:
        work()
    except Exception:
        passed = True
    return passed

def validate_four():
    try:
        work()
    except:
        pass
    return True
