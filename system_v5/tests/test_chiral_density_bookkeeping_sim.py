from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


REPO_ROOT = Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
SIM_PATH = REPO_ROOT / "system_v4" / "probes" / "sim_chiral_density_bookkeeping.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sim_chiral_density_bookkeeping", SIM_PATH)
    assert spec is not None and spec.loader is not None, "sim_chiral_density_bookkeeping.py is missing"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_density_bookkeeping_helpers_construct_valid_left_right_densities():
    module = _load_module()
    sample = module.compute_bookkeeping_sample(eta=np.pi / 4, theta1=0.3, theta2=1.1)

    rho_L = np.array(sample["rho_L"], dtype=complex)
    rho_R = np.array(sample["rho_R"], dtype=complex)
    rho_sum = np.array(sample["rho_sum"], dtype=complex)
    left_projector = np.array(sample["left_projector"], dtype=complex)
    right_projector = np.array(sample["right_projector"], dtype=complex)

    assert np.allclose(rho_L, rho_L.conj().T)
    assert np.allclose(rho_R, rho_R.conj().T)
    assert np.isclose(np.trace(rho_L), 1.0)
    assert np.isclose(np.trace(rho_R), 1.0)
    assert np.min(np.linalg.eigvalsh(rho_L)).real >= -1e-10
    assert np.min(np.linalg.eigvalsh(rho_R)).real >= -1e-10
    assert np.allclose(rho_sum, rho_L + rho_R)
    assert np.allclose(left_projector @ right_projector, np.zeros((2, 2), dtype=complex))
    assert np.allclose(left_projector @ left_projector, left_projector)
    assert np.allclose(right_projector @ right_projector, right_projector)
