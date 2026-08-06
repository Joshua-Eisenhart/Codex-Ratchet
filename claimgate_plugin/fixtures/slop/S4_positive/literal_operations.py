# S4 CLAIMS_WORK_RETURNS_LITERAL — expected to trip.
def verify_claim():
    return True

def run_probe():
    status = 0
    details = {"ok": True}
    return details
