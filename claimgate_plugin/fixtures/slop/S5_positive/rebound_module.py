# S5 DECORATIVE_IMPORT — expected to trip: module binding is replaced before use.
import numpy as np

np = object()
VALUE = np
