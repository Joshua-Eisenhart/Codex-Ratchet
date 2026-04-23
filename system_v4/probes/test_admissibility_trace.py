import json, sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'skills'))
from sim_edge_state_writeback import GeometricEngine, TORUS_INNER, ct_mi

engine = GeometricEngine(engine_type=1)
state = engine.init_state(TORUS_INNER)
state = engine.run_cycle(state)
history = state.history

ct_mi_prev = 0.0
for i, step in enumerate(history):
    if i + 1 >= len(history):
        break
    ct_mi_now = ct_mi(step["rho_L"], history[i + 1]["rho_R"])
    d_ct_mi = ct_mi_now - ct_mi_prev
    d_ga0 = step["ga0_after"] - step["ga0_before"]
    
    sign_ga0 = float(np.sign(d_ga0)) if abs(d_ga0) > 1e-9 else 0.0
    sign_ct = float(np.sign(d_ct_mi)) if abs(d_ct_mi) > 1e-9 else 0.0
    
    print(f"[{i:2d}] {step['stage']} op={step['op_name']:2s} | d_ga0={d_ga0:7.4f} (sign {sign_ga0:2.0f}) | d_ct_mi={d_ct_mi:7.4f} (sign {sign_ct:2.0f}) | MATCH={sign_ga0==sign_ct}")
    ct_mi_prev = ct_mi_now
