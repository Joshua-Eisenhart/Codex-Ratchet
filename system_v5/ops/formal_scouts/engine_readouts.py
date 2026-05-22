#!/usr/bin/env python3
"""
engine_readouts.py — output interpretation layer for operational QIT engines.

Provides static readout methods that interpret an engine trajectory or final
state into named quantities:

  - terrain_of_arrival:   nearest topology (Funnel/Vortex/Pit/Hill/Cannon/Spiral/
                          Source/Citadel) given the final Bloch position.
  - pattern_resolution:   winWIN / WINlose / LOSEwin / loseLOSE pattern from
                          examining outer-vs-inner-dominant moments.
  - entropy_signature:    Shannon / Renyi / Tsallis at start, middle, end.
  - persistence_class:    GUDHI persistence intervals of the Bloch trajectory.
  - holonomy_phase:       Berry phase along the trajectory.
  - full_readout:         all of the above combined.

Boundary: these are diagnostic labels/readouts over the current QIT engine
state trajectory. They are not source-native terrain/operator evidence by
themselves, and they must not be cited as the full terrain generator,
Weyl-sheet placement, or source operator-layer model without separate
source-generator receipts.

Source alignment:
  - canonical_qit_engine_specs.py (topology dicts, Bloch axes)
  - sim_closed_loop_holonomy_hysteresis_falsifier_probe.py (Berry phase reference)
  - sim_four_topology_behavior_class_chiral_loop_operator_separation_probe.py
    (centroid-classification reference)
"""

from __future__ import annotations

import math
import os
import pathlib
import sys
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import gudhi
import torch

_ROOT = pathlib.Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from canonical_qit_engine_specs import (
    SX,
    SY,
    SZ,
    TYPE_ONE_TOPOLOGIES,
    TYPE_TWO_TOPOLOGIES,
)

TORCH_COMPLEX_DTYPE = torch.complex128
TORCH_REAL_DTYPE = torch.float64
I2_T = torch.eye(2, dtype=TORCH_COMPLEX_DTYPE)
SX_T = torch.as_tensor(SX, dtype=TORCH_COMPLEX_DTYPE)
SY_T = torch.as_tensor(SY, dtype=TORCH_COMPLEX_DTYPE)
SZ_T = torch.as_tensor(SZ, dtype=TORCH_COMPLEX_DTYPE)


def _as_complex_tensor(value: Any) -> torch.Tensor:
    return torch.as_tensor(value, dtype=TORCH_COMPLEX_DTYPE)


def _rho_from_bloch(rx: float, ry: float, rz: float) -> torch.Tensor:
    return 0.5 * (I2_T + float(rx) * SX_T + float(ry) * SY_T + float(rz) * SZ_T)


# ---------------------------------------------------------------------------
# Topology centroid catalogue
# ---------------------------------------------------------------------------
#
# Build canonical Bloch centroid for each (engine_type, perception) pair using
# the topology projector axis + outer-loop result direction. The centroid is a
# fixed-direction unit vector on the Bloch sphere chosen to encode the topology's
# semantic mode (sink/source/hill/pit etc).
#
# Axis convention:
#   x → SX projector axis
#   y → SY projector axis
#   z → SZ projector axis
#
# Result convention:
#   "WIN"  → +1 along the axis (positive attractor)
#   "LOSE" → -1 along the axis (negative attractor)
#   "win"  → +0.5 along the axis (positive but weaker)
#   "lose" → -0.5 along the axis (negative but weaker)


def _axis_unit_vector(axis: str) -> torch.Tensor:
    if axis == "x":
        return torch.tensor([1.0, 0.0, 0.0], dtype=TORCH_REAL_DTYPE)
    elif axis == "y":
        return torch.tensor([0.0, 1.0, 0.0], dtype=TORCH_REAL_DTYPE)
    elif axis == "z":
        return torch.tensor([0.0, 0.0, 1.0], dtype=TORCH_REAL_DTYPE)
    else:
        raise ValueError(f"unknown axis: {axis}")


def _result_sign_magnitude(result: str) -> float:
    if result == "WIN":
        return +1.0
    elif result == "LOSE":
        return -1.0
    elif result == "win":
        return +0.5
    elif result == "lose":
        return -0.5
    else:
        raise ValueError(f"unknown result: {result}")


def _topology_centroid(topology_spec: dict) -> torch.Tensor:
    """Build a Bloch centroid for a topology spec."""
    axis = topology_spec["projector_axis"]
    outer_result = topology_spec["outer"]["result"]
    inner_result = topology_spec["inner"]["result"]
    base_dir = _axis_unit_vector(axis)
    # Outer dominates; inner contributes orthogonal lean
    outer_mag = _result_sign_magnitude(outer_result)
    inner_mag = _result_sign_magnitude(inner_result)
    # Orthogonal axis for inner contribution
    if axis == "x":
        ortho = torch.tensor([0.0, 0.5, 0.5], dtype=TORCH_REAL_DTYPE) / math.sqrt(0.5)
    elif axis == "y":
        ortho = torch.tensor([0.5, 0.0, 0.5], dtype=TORCH_REAL_DTYPE) / math.sqrt(0.5)
    else:
        ortho = torch.tensor([0.5, 0.5, 0.0], dtype=TORCH_REAL_DTYPE) / math.sqrt(0.5)
    centroid = outer_mag * base_dir + 0.3 * inner_mag * ortho
    norm = float(torch.linalg.vector_norm(centroid).item())
    if norm > 1e-12:
        return centroid / norm * min(1.0, norm)
    return base_dir * outer_mag


def _build_topology_centroid_catalogue() -> dict[str, dict[str, torch.Tensor]]:
    """
    Return {"type_one": {perception: centroid}, "type_two": {perception: centroid}}.
    """
    out: dict[str, dict[str, torch.Tensor]] = {"type_one": {}, "type_two": {}}
    for perception, spec in TYPE_ONE_TOPOLOGIES.items():
        out["type_one"][perception] = _topology_centroid(spec)
    for perception, spec in TYPE_TWO_TOPOLOGIES.items():
        out["type_two"][perception] = _topology_centroid(spec)
    return out


TOPOLOGY_CENTROIDS = _build_topology_centroid_catalogue()


# ---------------------------------------------------------------------------
# EngineReadout class
# ---------------------------------------------------------------------------

class EngineReadout:
    """Static methods that interpret an engine trajectory / final state."""

    @staticmethod
    def terrain_of_arrival(
        final_state: Any,
        all_topology_specs: dict[str, dict[str, dict]] | None = None,
    ) -> dict[str, Any]:
        """
        Compare the final state's Bloch vector to each topology's centroid;
        return the nearest topology label (Funnel/Vortex/Pit/Hill or
        Cannon/Spiral/Source/Citadel).

        final_state: 2x2 density matrix.
        """
        rho = _as_complex_tensor(final_state)
        bloch = torch.stack([
            torch.real(torch.trace(SX_T @ rho)),
            torch.real(torch.trace(SY_T @ rho)),
            torch.real(torch.trace(SZ_T @ rho)),
        ]).to(TORCH_REAL_DTYPE)

        catalogue = all_topology_specs if all_topology_specs is not None else {
            "type_one": TYPE_ONE_TOPOLOGIES,
            "type_two": TYPE_TWO_TOPOLOGIES,
        }

        # Compute distances to all centroids
        best_label = None
        best_engine_type = None
        best_perception = None
        best_distance = float("inf")
        all_distances: dict[str, dict[str, float]] = {"type_one": {}, "type_two": {}}

        for engine_type_label, perception_dict in catalogue.items():
            centroid_dict = TOPOLOGY_CENTROIDS[engine_type_label]
            for perception, spec in perception_dict.items():
                centroid = centroid_dict[perception]
                d = float(torch.linalg.vector_norm(bloch - centroid).item())
                all_distances[engine_type_label][perception] = d
                if d < best_distance:
                    best_distance = d
                    best_engine_type = engine_type_label
                    best_perception = perception
                    best_label = spec["realization"]

        return {
            "terrain": best_label,
            "engine_type": best_engine_type,
            "perception": best_perception,
            "distance": best_distance,
            "bloch": [float(x) for x in bloch.tolist()],
            "all_distances": all_distances,
        }

    @staticmethod
    def pattern_resolution(trajectory: list[dict]) -> dict[str, Any]:
        """
        Examine the trajectory's outer-vs-inner-dominant moments.
        Returns one of: winWIN, WINlose, LOSEwin, loseLOSE (Type 1)
                    or: loseWIN, winLOSE, LOSElose, WINwin (Type 2)

        The pattern is read from the dominant entropy direction over the trajectory:
          - Average entropy in outer-loop_class substages vs inner-loop_class substages
          - Higher entropy = more uncertainty (lose); lower = stable (win)
          - Outer dominant + final close to attractor → outer = capital letter
          - Inner dominant or counter → inner = lowercase
        """
        if not trajectory:
            return {"pattern": None, "n_records": 0}

        outer_records = [r for r in trajectory if r.get("loop_class") == "outer"]
        inner_records = [r for r in trajectory if r.get("loop_class") == "inner"]

        outer_mean_ent = (
            float(torch.tensor([r["entropy"] for r in outer_records], dtype=TORCH_REAL_DTYPE).mean().item())
            if outer_records else 0.0
        )
        inner_mean_ent = (
            float(torch.tensor([r["entropy"] for r in inner_records], dtype=TORCH_REAL_DTYPE).mean().item())
            if inner_records else 0.0
        )

        outer_mean_pur = (
            float(torch.tensor([r["purity"] for r in outer_records], dtype=TORCH_REAL_DTYPE).mean().item())
            if outer_records else 0.0
        )
        inner_mean_pur = (
            float(torch.tensor([r["purity"] for r in inner_records], dtype=TORCH_REAL_DTYPE).mean().item())
            if inner_records else 0.0
        )

        # Classification: lower entropy / higher purity = "WIN" (dominant);
        # higher entropy / lower purity = "lose"
        # The outer's strength is encoded by purity diff vs inner
        outer_stronger = outer_mean_pur > inner_mean_pur
        outer_capital = outer_mean_pur > 0.55
        inner_capital = inner_mean_pur > 0.55

        # Build pattern by trajectory's outer vs inner result
        outer_label = "WIN" if outer_capital else ("LOSE" if outer_mean_ent > 0.5 else "win")
        inner_label = "WIN" if inner_capital else ("LOSE" if inner_mean_ent > 0.5 else "win")
        # Normalize to canonical patterns (case-coherent labels)
        if outer_stronger:
            # Outer dominant: capitalize outer, lowercase inner
            outer_label_final = outer_label.upper() if outer_label != "lose" else "LOSE"
            inner_label_final = inner_label.lower() if inner_label != "WIN" else "win"
        else:
            outer_label_final = outer_label.lower() if outer_label != "LOSE" else "lose"
            inner_label_final = inner_label.upper() if inner_label != "win" else "WIN"

        pattern = outer_label_final + inner_label_final

        return {
            "pattern": pattern,
            "outer_mean_entropy": outer_mean_ent,
            "inner_mean_entropy": inner_mean_ent,
            "outer_mean_purity": outer_mean_pur,
            "inner_mean_purity": inner_mean_pur,
            "n_outer_records": len(outer_records),
            "n_inner_records": len(inner_records),
        }

    @staticmethod
    def entropy_signature(trajectory: list[dict]) -> dict[str, Any]:
        """
        Compute Shannon / Renyi-2 / Tsallis-2 entropy at start, middle, end of trajectory.

        Shannon: -Σ p log p
        Renyi-2: -log Σ p²
        Tsallis-2: (1 - Σ p²) / (2-1) = 1 - Σ p²
        """
        if not trajectory:
            return {}

        def get_eigs(record: dict) -> torch.Tensor:
            # Approximate eigenvalues from purity and entropy:
            # For 2-dim: eigs (p, 1-p) with purity = p² + (1-p)²
            # Use von Neumann entropy directly + purity to recover (p, 1-p)
            pur = float(record.get("purity", 0.5))
            # purity = 2p² - 2p + 1; solve: 2p² - 2p + (1-pur) = 0
            # p = (1 ± sqrt(1 - 2(1-pur))) / 2 = (1 ± sqrt(2pur - 1)) / 2
            disc = max(0.0, 2 * pur - 1.0)
            r = math.sqrt(disc)
            p_high = (1 + r) / 2
            p_low = (1 - r) / 2
            return torch.tensor([max(p_low, 1e-15), max(p_high, 1e-15)], dtype=TORCH_REAL_DTYPE)

        positions = {
            "start": 0,
            "middle": len(trajectory) // 2,
            "end": len(trajectory) - 1,
        }
        out: dict[str, dict[str, float]] = {}
        for label, pos in positions.items():
            eigs = get_eigs(trajectory[pos])
            eigs = eigs / eigs.sum()
            shannon = float((-(eigs * torch.log(eigs)).sum()).item())
            renyi2 = float((-torch.log((eigs ** 2).sum())).item())
            tsallis2 = float((1 - (eigs ** 2).sum()).item())
            out[label] = {
                "shannon": shannon,
                "renyi_2": renyi2,
                "tsallis_2": tsallis2,
            }
        out["delta_shannon"] = out["end"]["shannon"] - out["start"]["shannon"]
        out["n_records"] = len(trajectory)
        return out

    @staticmethod
    def persistence_class(trajectory: list[dict]) -> dict[str, Any]:
        """GUDHI persistence of the Bloch trajectory point cloud."""
        if not trajectory:
            return {"h0_count": 0, "max_finite_h0_persistence": 0.0}

        points = [[float(x) for x in r["bloch"]] for r in trajectory]
        # Rips complex with edge length matched to typical Bloch ball scale
        rips = gudhi.RipsComplex(points=points, max_edge_length=0.6)
        st = rips.create_simplex_tree(max_dimension=1)
        intervals = st.persistence()

        h0 = [p for dim, p in intervals if dim == 0]
        finite_h0 = [death - birth for birth, death in h0 if death < float("inf")]
        h1 = [p for dim, p in intervals if dim == 1]
        finite_h1 = [death - birth for birth, death in h1 if death < float("inf")]

        return {
            "h0_count": len(h0),
            "h0_finite_count": len(finite_h0),
            "max_finite_h0_persistence": float(max(finite_h0)) if finite_h0 else 0.0,
            "h1_count": len(h1),
            "h1_finite_count": len(finite_h1),
            "max_finite_h1_persistence": float(max(finite_h1)) if finite_h1 else 0.0,
        }

    @staticmethod
    def holonomy_phase(trajectory: list[dict]) -> dict[str, Any]:
        """
        Berry phase along the trajectory.

        Berry phase γ = -arg(Π_k <ψ_k | ψ_{k+1}>)
        where ψ_k is the dominant eigenvector of ρ_k.

        For a closed loop, γ ≠ 0 indicates non-trivial holonomy.
        """
        if not trajectory:
            return {"berry_phase": 0.0, "n_records": 0}

        # Reconstruct ρ at each step from Bloch, then take dominant eigenvector
        eigenvectors = []
        for record in trajectory:
            rx, ry, rz = record["bloch"]
            rho = _rho_from_bloch(float(rx), float(ry), float(rz))
            _, vecs = torch.linalg.eigh((rho + rho.mH) / 2)
            # Dominant eigenvector
            psi = vecs[:, -1].clone()
            # Phase fix: first non-zero component positive real
            for i in range(2):
                if float(torch.abs(psi[i]).item()) > 1e-12:
                    psi = psi * torch.conj(psi[i]) / torch.abs(psi[i])
                    break
            eigenvectors.append(psi)

        # Loop overlap product
        product = complex(1.0, 0.0)
        for k in range(len(eigenvectors)):
            psi_k = eigenvectors[k]
            psi_kp1 = eigenvectors[(k + 1) % len(eigenvectors)]
            ovr = complex(torch.vdot(psi_k, psi_kp1).item())
            if abs(ovr) > 1e-12:
                product *= ovr / abs(ovr)

        berry_phase = float(-math.atan2(product.imag, product.real))
        return {
            "berry_phase": berry_phase,
            "abs_berry_phase": abs(berry_phase),
            "n_records": len(trajectory),
        }

    @classmethod
    def full_readout(
        cls,
        trajectory: list[dict],
        schedule_record: dict | None = None,
    ) -> dict[str, Any]:
        """All readouts combined into a single 'engine output' dict."""
        # Extract final state from the last trajectory record's Bloch
        if not trajectory:
            return {"empty": True}
        last_record = trajectory[-1]
        rx, ry, rz = last_record["bloch"]
        rho_final = _rho_from_bloch(float(rx), float(ry), float(rz))

        return {
            "terrain_of_arrival": cls.terrain_of_arrival(rho_final),
            "pattern_resolution": cls.pattern_resolution(trajectory),
            "entropy_signature": cls.entropy_signature(trajectory),
            "persistence_class": cls.persistence_class(trajectory),
            "holonomy_phase": cls.holonomy_phase(trajectory),
            "schedule_summary": (
                {
                    "compose_rule": schedule_record.get("compose_rule"),
                    "n_iter": schedule_record.get("n_iter"),
                    "total_substages": schedule_record.get("total_substages"),
                }
                if schedule_record else None
            ),
            "final_bloch": last_record["bloch"],
            "n_trajectory_records": len(trajectory),
        }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 70)
    print("engine_readouts.py — smoke test")
    print("=" * 70)

    from engine_core import EngineCore, generate_initial_density
    from engine_schedule import Schedule

    # Build a simple trajectory
    rho0 = generate_initial_density(23)
    eng_t1 = EngineCore(engine_type=0)
    eng_t2 = EngineCore(engine_type=1)
    sched = Schedule(engines=[eng_t1, eng_t2], n_iter=1)
    out = sched.run(rho0)

    print(f"\n1. Centroid catalogue (Type 1 perceptions):")
    for perception, centroid in TOPOLOGY_CENTROIDS["type_one"].items():
        print(f"   {perception} ({TYPE_ONE_TOPOLOGIES[perception]['realization']}): "
              f"{[round(float(x), 3) for x in centroid]}")
    print(f"\n   Type 2 perceptions:")
    for perception, centroid in TOPOLOGY_CENTROIDS["type_two"].items():
        print(f"   {perception} ({TYPE_TWO_TOPOLOGIES[perception]['realization']}): "
              f"{[round(float(x), 3) for x in centroid]}")

    print("\n2. terrain_of_arrival")
    rx, ry, rz = out["final_bloch"]
    rho_final = _rho_from_bloch(float(rx), float(ry), float(rz))
    toa = EngineReadout.terrain_of_arrival(rho_final)
    print(f"   terrain={toa['terrain']}  engine_type={toa['engine_type']}  "
          f"perception={toa['perception']}  distance={toa['distance']:.4f}")

    print("\n3. pattern_resolution")
    pat = EngineReadout.pattern_resolution(out["trajectory"])
    print(f"   pattern: {pat['pattern']}")
    print(f"   outer mean ent: {pat['outer_mean_entropy']:.4f}  "
          f"inner: {pat['inner_mean_entropy']:.4f}")
    print(f"   outer mean pur: {pat['outer_mean_purity']:.4f}  "
          f"inner: {pat['inner_mean_purity']:.4f}")

    print("\n4. entropy_signature")
    ent = EngineReadout.entropy_signature(out["trajectory"])
    print(f"   start shannon: {ent['start']['shannon']:.4f}  "
          f"end shannon: {ent['end']['shannon']:.4f}  "
          f"delta: {ent['delta_shannon']:.4f}")

    print("\n5. persistence_class")
    per = EngineReadout.persistence_class(out["trajectory"])
    print(f"   H0 count: {per['h0_count']}  "
          f"max H0 finite: {per['max_finite_h0_persistence']:.4f}")
    print(f"   H1 count: {per['h1_count']}")

    print("\n6. holonomy_phase")
    hol = EngineReadout.holonomy_phase(out["trajectory"])
    print(f"   Berry phase: {hol['berry_phase']:.4f}  "
          f"abs: {hol['abs_berry_phase']:.4f}")

    print("\n7. full_readout")
    fr = EngineReadout.full_readout(out["trajectory"], out["schedule_record"])
    print(f"   terrain: {fr['terrain_of_arrival']['terrain']}  "
          f"pattern: {fr['pattern_resolution']['pattern']}  "
          f"berry: {fr['holonomy_phase']['berry_phase']:.4f}")
    print(f"   n trajectory records: {fr['n_trajectory_records']}")

    # 8. Test distinguishability across multiple initial states
    print("\n8. Distinguishability: multiple initial states")
    readouts = []
    for seed in range(6):
        rho_s = generate_initial_density(seed)
        eng_a = EngineCore(engine_type=0)
        eng_b = EngineCore(engine_type=1)
        sched_s = Schedule(engines=[eng_a, eng_b], n_iter=1)
        out_s = sched_s.run(rho_s)
        fr_s = EngineReadout.full_readout(out_s["trajectory"], out_s["schedule_record"])
        readouts.append({
            "seed": seed,
            "terrain": fr_s["terrain_of_arrival"]["terrain"],
            "pattern": fr_s["pattern_resolution"]["pattern"],
            "berry": fr_s["holonomy_phase"]["berry_phase"],
        })
        print(f"   seed={seed}: terrain={fr_s['terrain_of_arrival']['terrain']}  "
              f"pattern={fr_s['pattern_resolution']['pattern']}  "
              f"berry={fr_s['holonomy_phase']['berry_phase']:+.4f}")
    distinct_terrains = len({r["terrain"] for r in readouts})
    distinct_patterns = len({r["pattern"] for r in readouts})
    print(f"\n   distinct terrains across 6 seeds: {distinct_terrains}")
    print(f"   distinct patterns across 6 seeds: {distinct_patterns}")

    print("\n" + "=" * 70)
    print("engine_readouts.py SMOKE TEST PASS")
    print("=" * 70)
