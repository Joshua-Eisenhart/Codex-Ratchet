# S3 EXCEPT_SWALLOWS_SUCCESS — expected clean: exception is re-raised.
def verify():
    try:
        work()
    except Exception:
        log()
        raise
