# S3 EXCEPT_SWALLOWS_SUCCESS — expected clean: failure remains failure.
def verify():
    try:
        work()
    except Exception:
        return False
