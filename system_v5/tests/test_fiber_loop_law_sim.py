from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


REPO_ROOT = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
SIM_PATH = REPO_ROOT / "system_v4" / "probes" / "sim_fiber_loop_law.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sim_fiber_loop_law", SIM_PATH)
    assert spec is not None and spec.loader is not None, "sim_fiber_loop_law.py is missing"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fiber_loop_law_helpers_keep_density_stationary_along_fiber():
    module = _load_module()
    sample = module.compute_fiber_loop_sample(eta=np.pi / 4, theta1=0.3, theta2=1.1, phase=1.7)

    rho_before = np.array(sample["rho_before"], dtype=complex)
    rho_after = np.array(sample["rho_after"], dtype=complex)
    hopf_before = np.array(sample["hopf_before"], dtype=float)
    hopf_after = np.array(sample["hopf_after"], dtype=float)

    assert np.allclose(rho_before, rho_before.conj().T)
    assert np.isclose(np.trace(rho_before), 1.0)
    assert np.min(np.linalg.eigvalsh(rho_before)).real >= -1e-10
    assert np.allclose(rho_before, rho_after)
    assert np.allclose(hopf_before, hopf_after)
    assert sample["density_gap"] < 1e-10
    assert sample["hopf_gap"] < 1e-10
