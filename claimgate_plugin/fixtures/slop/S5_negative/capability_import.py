# S5 DECORATIVE_IMPORT — expected clean: conditional capability import.
try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False
