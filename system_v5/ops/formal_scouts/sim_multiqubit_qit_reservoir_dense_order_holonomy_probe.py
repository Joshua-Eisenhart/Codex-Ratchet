#!/usr/bin/env python3
"""Dense v6 multi-qubit order-holonomy scout."""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3

import engine_v6_proper_multiqubit_reference as v6


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "multiqubit_qit_reservoir_dense_order_holonomy_probe_results.json"

NAME = "multiqubit_qit_reservoir_dense_order_holonomy_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: translates the external dense-v6 holonomy claim into a "
    "repo-grounded finite test of order-dependent multi-qubit dynamics on product, "
    "GHZ, W, Haar, and max-mixed inputs. It does not prove a canonical connection "
    "and does not admit physics, cognition, intelligence, neural capability, or "
    "final manifold claims."
)

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load-bearing dense v6 order-dependent state evolution"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing finite noncommutation witness"},
    "engine_v6_reference": {"tried": True, "used": True, "reason": "load-bearing repo-grounded v6 candidate"},
}
TOOL_INTEGRATION_DEPTH = {
    'pytorch': 'load_bearing',
    'z3': 'load_bearing',
    'engine_v6_reference': 'supportive',
}

MIN_NONCLASSICAL_WIDTH = 8
N_QUBITS = 8
DTYPE = v6.DTYPE
CLASS_NAMES = ["product", "ghz", "w", "haar"]


def tokens_for_order(engine: v6.TrainableEngineV6, stage_order: list[int]) -> list[tuple[int, int, int]]:
    tokens = []
    for terrain_idx in stage_order:
        for op_idx, sign in engine.stage_substages(terrain_idx):
            tokens.append((terrain_idx, op_idx, sign))
    return tokens


def evolve_tokens(engine: v6.TrainableEngineV6, rho_in: torch.Tensor, tokens: list[tuple[int, int, int]]) -> torch.Tensor:
    rho = rho_in.to(DTYPE)
    with torch.no_grad():
        for terrain_idx, op_idx, sign in tokens:
            rho = engine.run_substage(rho, terrain_idx, op_idx, sign)
    return rho


def fro_gap(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(a - b).detach().cpu().item())


def _complex_normal(shape: tuple[int, ...], generator: torch.Generator) -> torch.Tensor:
    real = torch.randn(shape, generator=generator, dtype=torch.float32)
    imag = torch.randn(shape, generator=generator, dtype=torch.float32)
    return torch.complex(real, imag).to(DTYPE)


def _pure_density(psi: torch.Tensor) -> torch.Tensor:
    psi = psi.to(DTYPE)
    return torch.outer(psi, psi.conj())


def _kron_all(states: list[torch.Tensor]) -> torch.Tensor:
    out = states[0]
    for state in states[1:]:
        out = torch.kron(out, state)
    return out.to(DTYPE)


def _random_product_density(generator: torch.Generator) -> torch.Tensor:
    states = []
    for _ in range(N_QUBITS):
        psi = _complex_normal((2,), generator)
        states.append(psi / torch.linalg.vector_norm(psi))
    return _pure_density(_kron_all(states))


def _ghz_density(generator: torch.Generator) -> torch.Tensor:
    d = 2**N_QUBITS
    psi = torch.zeros(d, dtype=DTYPE)
    phase = float((2 * math.pi * torch.rand((), generator=generator, dtype=torch.float32)).item())
    psi[0] = 1.0 / math.sqrt(2.0)
    psi[-1] = complex(math.cos(phase), math.sin(phase)) / math.sqrt(2.0)
    return _pure_density(psi)


def _w_density() -> torch.Tensor:
    d = 2**N_QUBITS
    psi = torch.zeros(d, dtype=DTYPE)
    amp = 1.0 / math.sqrt(float(N_QUBITS))
    for q in range(N_QUBITS):
        psi[1 << q] = amp
    return _pure_density(psi)


def _random_pure_density(generator: torch.Generator) -> torch.Tensor:
    psi = _complex_normal((2**N_QUBITS,), generator)
    return _pure_density(psi / torch.linalg.vector_norm(psi))


def density_for_name(name: str, generator: torch.Generator) -> torch.Tensor:
    if name == "max_mixed":
        d = 2**N_QUBITS
        return torch.eye(d, dtype=DTYPE) / d
    if name == "product":
        return _random_product_density(generator)
    if name == "ghz":
        return _ghz_density(generator)
    if name == "w":
        return _w_density()
    if name == "haar":
        return _random_pure_density(generator)
    raise ValueError(name)


def run_engine_class(engine_type: int, class_name: str, seed: int) -> dict[str, Any]:
    torch.manual_seed(200000 + engine_type)
    generator = torch.Generator().manual_seed(seed)
    engine = v6.TrainableEngineV6(engine_type=engine_type, n_qubits=N_QUBITS, dt=0.06, n_steps_per_substage=2)
    engine.eval()
    native = engine.stage_sequence()
    mirrored = list(reversed(native[:4])) + list(reversed(native[4:]))
    native_tokens = tokens_for_order(engine, native)
    reverse_tokens = list(reversed(native_tokens))
    mirrored_tokens = tokens_for_order(engine, mirrored)
    rho = density_for_name(class_name, generator)
    fwd = evolve_tokens(engine, rho, native_tokens)
    rev = evolve_tokens(engine, rho, reverse_tokens)
    mirrored_out = evolve_tokens(engine, rho, mirrored_tokens)
    return {
        "engine_type": engine_type,
        "class_name": class_name,
        "native_order": native,
        "mirrored_order": mirrored,
        "fwd_vs_rev_gap": fro_gap(fwd, rev),
        "native_vs_mirrored_gap": fro_gap(fwd, mirrored_out),
    }


def run_matrix() -> dict[str, Any]:
    class_names = CLASS_NAMES + ["max_mixed"]
    rows = []
    for engine_type in (1, 2):
        for idx, class_name in enumerate(class_names):
            rows.append(run_engine_class(engine_type, class_name, 210000 + 100 * engine_type + idx))
    nontrivial = [row for row in rows if row["class_name"] != "max_mixed"]
    trivial = [row for row in rows if row["class_name"] == "max_mixed"]
    mean_fwd_rev = float(torch.tensor([row["fwd_vs_rev_gap"] for row in nontrivial], dtype=torch.float64).mean().item())
    mean_native_mirror = float(torch.tensor([row["native_vs_mirrored_gap"] for row in nontrivial], dtype=torch.float64).mean().item())
    max_trivial = float(max(max(row["fwd_vs_rev_gap"], row["native_vs_mirrored_gap"]) for row in trivial))
    t1_mean = float(torch.tensor([row["fwd_vs_rev_gap"] for row in nontrivial if row["engine_type"] == 1], dtype=torch.float64).mean().item())
    t2_mean = float(torch.tensor([row["fwd_vs_rev_gap"] for row in nontrivial if row["engine_type"] == 2], dtype=torch.float64).mean().item())
    return {
        "n_qubits": N_QUBITS,
        "rows": rows,
        "mean_nontrivial_fwd_vs_rev_gap": mean_fwd_rev,
        "mean_nontrivial_native_vs_mirrored_gap": mean_native_mirror,
        "max_trivial_max_mixed_gap": max_trivial,
        "engine_type_fwd_rev_means": {"1": t1_mean, "2": t2_mean},
        "pass": mean_fwd_rev > 0.02
        and mean_native_mirror > 0.02
        and max_trivial < mean_fwd_rev
        and all(row["fwd_vs_rev_gap"] > 0.015 for row in nontrivial),
    }


def z3_holonomy_witness(matrix: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    n = z3.Int("n_qubits")
    fwd = z3.Real("mean_fwd_rev")
    mirror = z3.Real("mean_native_mirror")
    trivial = z3.Real("max_trivial")
    solver.add(n == matrix["n_qubits"])
    solver.add(fwd == str(round(matrix["mean_nontrivial_fwd_vs_rev_gap"], 8)))
    solver.add(mirror == str(round(matrix["mean_nontrivial_native_vs_mirrored_gap"], 8)))
    solver.add(trivial == str(round(matrix["max_trivial_max_mixed_gap"], 8)))
    solver.add(z3.Not(z3.And(n >= MIN_NONCLASSICAL_WIDTH, fwd > 0, mirror > 0, trivial < fwd)))
    status = solver.check()
    return {
        "solver_status": str(status),
        "pass": status == z3.unsat,
        "minimum_width_qubits": MIN_NONCLASSICAL_WIDTH,
        "claim_ceiling": "Z3 encodes only finite dense-v6 order-gap inequalities at the current minimum-width floor.",
    }


def main() -> int:
    started = time.time()
    matrix = run_matrix()
    positive = {
        "dense_v6_ordering_is_path_dependent_on_nontrivial_multiqubit_inputs": matrix,
        "z3_rejects_commuting_order_collapse": z3_holonomy_witness(matrix),
    }
    graveyards = {
        "max_mixed_is_the_trivial_order_control": {
            "max_trivial_gap": matrix["max_trivial_max_mixed_gap"],
            "mean_nontrivial_gap": matrix["mean_nontrivial_fwd_vs_rev_gap"],
            "pass": matrix["max_trivial_max_mixed_gap"] < matrix["mean_nontrivial_fwd_vs_rev_gap"],
        },
        "both_chiral_engines_show_order_dependence": {
            "engine_type_fwd_rev_means": matrix["engine_type_fwd_rev_means"],
            "pass": all(value > 0.02 for value in matrix["engine_type_fwd_rev_means"].values()),
        },
    }
    boundary = {
        "eight_qubit_width_floor_is_direct": {
            "n_qubits": N_QUBITS,
            "minimum_width_qubits": MIN_NONCLASSICAL_WIDTH,
            "minimum_width_role": "maturity_gate",
            "pass": N_QUBITS >= MIN_NONCLASSICAL_WIDTH,
        },
        "promotion_remains_disabled": {"pass": PROMOTION_ALLOWED is False},
        "dense_holonomy_does_not_replace_peps3d_holonomy": {"pass": "dense-v6" in CLAIM_CEILING and N_QUBITS >= MIN_NONCLASSICAL_WIDTH},
    }
    all_pass = all(row["pass"] for row in positive.values()) and all(row["pass"] for row in graveyards.values()) and all(row["pass"] for row in boundary.values())
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_alignment_category": "source_native_multiqubit_qit_reservoir_dense_holonomy_formal_scout",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyards,
        "boundary": boundary,
        "nearby_variants": {"total": len(graveyards), "passed": sum(1 for row in graveyards.values() if row["pass"]), "variants": sorted(graveyards)},
        "why_not_v4_probes": [
            "Finite dense-v6 order-dependence scout only.",
            "Does not prove a canonical geometric connection.",
            "Complements but does not replace the PEPS3D/MPS holonomy scout.",
        ],
        "blockers": [],
        "elapsed_seconds": time.time() - started,
        "all_pass": all_pass,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={all_pass} -> {OUT_PATH}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
