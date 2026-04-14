import json, os, numpy as np
classification = "classical_baseline"  # auto-backfill
divergence_log = "Classical baseline: the FEP derivative bridge is checked here by direct trajectory-correlation numerics, not a canonical nonclassical witness."
TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "trajectory derivatives and correlation numerics"},
}
TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
}

with open("../a2_state/sim_results/bridge_engine_fep_holodeck.json", "r") as f:
    d = json.load(f)

for tname, tdata in d["trajectories"].items():
    ga0 = np.array(tdata["ga0_trajectory"])
    fep = np.array(tdata["fep_trajectory"])
    d_ga0 = np.diff(ga0)
    d_fep = np.diff(fep)
    
    # Check absolute vs derivative correlations
    r_abs = np.corrcoef(ga0, fep)[0,1]
    r_vel = np.corrcoef(d_ga0, d_fep)[0,1]
    
    print(f"[{tname}] Abs Correlation   : {r_abs:+.4f}")
    print(f"[{tname}] d(ga0) vs d(FEP)  : {r_vel:+.4f}")
