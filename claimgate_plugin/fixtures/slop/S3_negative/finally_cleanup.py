# S3 EXCEPT_SWALLOWS_SUCCESS — expected clean: cleanup is in finally.
def verify():
    try:
        return work()
    finally:
        cleanup()
