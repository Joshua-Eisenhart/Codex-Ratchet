# S3 EXCEPT_SWALLOWS_SUCCESS — expected clean: absent capability is false.
try:
    import imaginary_package
    HAVE_X = True
except ImportError:
    HAVE_X = False
