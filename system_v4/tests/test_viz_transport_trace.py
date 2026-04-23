from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_PATH = REPO_ROOT / "system_v4" / "probes" / "sim_parallel_transport_s2_classical.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("sim_parallel_transport_s2_classical", SIM_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_trace_transport_loop_octant_shape_and_order() -> None:
    module = _load_module()
    trace = module.trace_transport_loop_octant(steps_per_arc=8)

    assert trace
    assert np.allclose(trace[0]["base_xyz"], np.array([0.0, 0.0, 1.0]), atol=1e-6)
    assert np.allclose(trace[-1]["base_xyz"], np.array([0.0, 0.0, 1.0]), atol=5e-2)

    step_indices = [record["step_index"] for record in trace]
    assert step_indices == list(range(len(trace)))

    for record in trace:
        assert set(record) >= {"step_index", "arc_id", "loop_progress", "base_xyz", "tangent_xyz"}
        assert len(record["base_xyz"]) == 3
        assert len(record["tangent_xyz"]) == 3
        assert 0.0 <= record["loop_progress"] <= 1.0
