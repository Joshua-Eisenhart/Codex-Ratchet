import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'skills'))

from engine_core import GeometricEngine
from qit_nonclassical_guards import bridge_guard_input, check_nonclassical_guards

engine = GeometricEngine(engine_type=1)
test_state = engine.init_state()
rho_AB = test_state.rho_AB
rho_L = test_state.rho_L
rho_R = test_state.rho_R

print("Sep frob:", np.linalg.norm(rho_AB - np.kron(rho_L, rho_R), ord='fro'))
inp = bridge_guard_input(rho_AB, rho_L, rho_R)
print("Input:", inp)
res = check_nonclassical_guards(inp)
print("Passed:", res.passed)
print("Violations:", res.violations)
