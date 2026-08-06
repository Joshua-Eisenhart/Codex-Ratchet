# S5 DECORATIVE_IMPORT — expected to trip: parameter shadows the import.
import numpy as np

def render(np):
    return np.array([1])
