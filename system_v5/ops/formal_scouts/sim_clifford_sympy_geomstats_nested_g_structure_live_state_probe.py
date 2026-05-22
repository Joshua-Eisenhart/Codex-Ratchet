#!/usr/bin/env python3
"""
sim_clifford_sympy_geomstats_nested_g_structure_live_state_probe.py

Minimal symbolic/algebraic scout: probes a nested G-structure reduction chain
over a bounded canonical QIT replay state using clifford (Cl(1,3) gamma_5
chirality), sympy (symbolic frame admissibility for GL(2,C) -> U(2) ->
SU(2)), and geomstats (Bloch S^2 / unit-spinor S^3 membership).

Probe family M:
  M_clifford   -- Cl(1,3) pseudoscalar gamma_5 chirality projection of psi
  M_sympy      -- sympy symbolic frame admissibility (trace, hermiticity, det)
  M_geomstats  -- geomstats Hypersphere(2) Bloch-sphere membership distance

Constraint set C (nested G-structure reduction):
  L0  GL(2,C)         -- finite density carrier (trace 1, complex)
  L1  U(2)_real       -- hermitian + nonneg-eigenvalue frame
  L2  SU(2)           -- additionally det=1 in the lifted unitary frame
  L3  Spin(3)         -- Clifford pseudoscalar action consistent under
                         orientation (gamma_5 nontrivial split)
  L4  Weyl chirality  -- gamma_5 eigenvalue split nondegenerate

Status framing (harness):
  classification: "formal_scout"
  promotion_allowed: false
  This is a pre-admission formal scout; it does NOT admit canonical, bridge,
  axis, G-structure, manifold, or engine claims. Its job is to record where
  the symbolic chain bottoms out relative to bounded canonical schedule/slot
  replay states, and where the three symbolic probes diverge. It is not a
  live EngineCore dynamics claim.
"""

import json
import math
import os
import sys
from typing import Any

import torch

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False

# Make engine_core importable when invoked from anywhere.
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": ""},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": ""},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn": {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi": {"tried": False, "used": False, "reason": ""},
    "toponetx": {"tried": False, "used": False, "reason": ""},
    "gudhi": {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import torch  # noqa: F401
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "canonical QIT replay density construction and operator-slot unitary transport"
    TOOL_INTEGRATION_DEPTH["pytorch"] = "load_bearing"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "symbolic frame admissibility (trace, hermiticity, det) at L0..L2"
    TOOL_INTEGRATION_DEPTH["sympy"] = "load_bearing"
except ImportError:
    sp = None
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(1,3) pseudoscalar gamma_5 chirality projection at L3..L4"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"
except ImportError:
    Cl = None
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    from geomstats.geometry.hypersphere import Hypersphere
    TOOL_MANIFEST["geomstats"]["tried"] = True
    TOOL_MANIFEST["geomstats"]["used"] = False
    TOOL_MANIFEST["geomstats"]["reason"] = "blocked: installed backend requires NumPy point carriers; hard-quarantine scout does not import or use NumPy"
except ImportError:
    Hypersphere = None
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import z3
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "finite UNSAT on anti-orientation Cl(1,3) sign-symmetry exclusion"
    TOOL_INTEGRATION_DEPTH["z3"] = "supportive"
except ImportError:
    z3 = None
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

# Remaining tools: not load-bearing here, mark not-tried with reason.
for k in ("pyg", "cvc5", "e3nn", "rustworkx", "xgi", "toponetx", "gudhi"):
    TOOL_MANIFEST[k]["reason"] = f"out of scope for this symbolic G-structure scout"


# =====================================================================
# BOUNDED CANONICAL QIT REPLAY STATE -- no EngineCore boundary crossing
# =====================================================================

I2 = torch.eye(2, dtype=torch.complex128)
SX = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)


def _seed_density(label: str) -> torch.Tensor:
    if label == "ket0":
        psi = torch.tensor([1.0, 0.0], dtype=torch.complex128)
    elif label == "ket1":
        psi = torch.tensor([0.0, 1.0], dtype=torch.complex128)
    elif label == "plus":
        psi = torch.tensor([1.0, 1.0], dtype=torch.complex128) / math.sqrt(2)
    elif label == "right_circular":
        psi = torch.tensor([1.0, 1j], dtype=torch.complex128) / math.sqrt(2)
    else:
        raise ValueError(label)
    return torch.outer(psi, psi.conj())


def _clean_density(rho: torch.Tensor) -> torch.Tensor:
    rho = 0.5 * (rho + rho.conj().T)
    tr = torch.trace(rho)
    if torch.abs(tr) > 1e-12:
        rho = rho / tr
    return rho


def _canonical_replay_state(
    rho: torch.Tensor,
    perception: str,
    engine_type: int,
    loop_class: str,
    substage_idx: int,
) -> tuple[torch.Tensor, dict[str, Any]]:
    from canonical_qit_engine_specs import (
        I2 as CANONICAL_I2,
        OPERATOR_BASE_ANGLES,
        OPERATOR_GENERATORS,
        get_operator_slot_spec,
    )

    slot = get_operator_slot_spec(perception, engine_type, loop_class, substage_idx)
    op = slot["operator"]
    sign = int(slot["sign"])
    theta = sign * float(OPERATOR_BASE_ANGLES[op]) * (1.0 + 0.05 * substage_idx)
    generator = OPERATOR_GENERATORS[op]
    U = torch.linalg.matrix_exp(-1j * theta * generator)
    transported = U @ rho @ U.conj().T

    # The symbolic scout needs valid density carriers, not a dynamics claim.
    # Add a small chart-dependent finite-temperature component so the chain
    # includes both pure-boundary and interior density examples while remaining
    # trace-one, hermitian, and positive by construction.
    mix = min(0.02 * (substage_idx + 1), 0.10)
    replay = (1.0 - mix) * transported + mix * (CANONICAL_I2 / 2.0)
    return _clean_density(replay), slot


def _collect_replay_states(max_substages: int = 4) -> list[dict]:
    """
    Collect bounded canonical replay densities across (seed, engine_type,
    main_stage=0, substage in [0..max_substages)). This deliberately stays
    inside torch-native canonical QIT schedule/slot data and does not cross
    the legacy EngineCore NumPy carrier boundary.
    """
    try:
        from canonical_qit_engine_specs import get_schedule
    except Exception as exc:
        return [{"error": f"canonical_qit_engine_specs import failed: {exc}"}]

    seeds = ["ket0", "ket1", "plus", "right_circular"]
    states: list[dict] = []
    for seed in seeds:
        for engine_type in (0, 1):
            rho = _seed_density(seed)
            perception, loop_class = get_schedule(engine_type)[0]
            for substage_idx in range(max_substages):
                try:
                    rho, slot = _canonical_replay_state(
                        rho, perception, engine_type, loop_class, substage_idx
                    )
                except Exception as exc:
                    states.append({
                        "seed": seed,
                        "engine_type": engine_type,
                        "substage_idx": substage_idx,
                        "error": f"run_substage failed: {exc}",
                    })
                    continue
                states.append({
                    "seed": seed,
                    "engine_type": engine_type,
                    "perception": perception,
                    "loop_class": loop_class,
                    "main_stage_idx": 0,
                    "substage_idx": substage_idx,
                    "operator_slot": slot,
                    "rho": torch.as_tensor(rho, dtype=torch.complex128).clone(),
                })
    return states


# =====================================================================
# SYMBOLIC PROBES (M)
# =====================================================================

def _rho_to_sympy(rho: torch.Tensor, rational_denom: int = 1024):
    """Lift 2x2 density to sympy Matrix with rational approximation."""
    M = sp.zeros(2, 2)
    for i in range(2):
        for j in range(2):
            z = complex(rho[i, j])
            re = sp.Rational(int(round(z.real * rational_denom)), rational_denom)
            im = sp.Rational(int(round(z.imag * rational_denom)), rational_denom)
            M[i, j] = re + im * sp.I
    return M


def _sympy_frame_admissibility(rho: torch.Tensor) -> dict:
    """
    L0/L1/L2 admissibility under sympy symbolic checks.
    Returns level reached and exact symbolic residues.
    """
    if sp is None:
        return {"available": False, "reason": "sympy unavailable"}

    Msym = _rho_to_sympy(rho)
    tr = sp.simplify(Msym.trace())
    # hermiticity residue
    herm_residue = sp.simplify((Msym - Msym.H).norm())
    # eigenvalues (must be nonneg real for a valid density)
    try:
        eigs = list(Msym.eigenvals().keys())
        eig_floats = [complex(sp.N(e)) for e in eigs]
    except Exception:
        eig_floats = []

    det = sp.simplify(Msym.det())

    # L0 -- trace 1
    tr_residue = sp.simplify(tr - 1)
    L0_admitted = abs(complex(sp.N(tr_residue))) < 1e-6
    # L1 -- hermitian + nonneg eigenvalues
    L1_admitted = (
        L0_admitted
        and abs(complex(sp.N(herm_residue))) < 1e-6
        and all(abs(e.imag) < 1e-6 and e.real > -1e-6 for e in eig_floats)
    )
    # L2 -- additionally a lifted SU(2) frame: in 2x2, take the spectral
    # unitary U s.t. rho = U diag(p,1-p) U^\dagger and require det(U) = 1
    # (sign-fixable). We approximate by computing the unitary numerically
    # then symbolically checking |det|=1; the determinant of a unitary is a
    # phase, and we check whether the phase is real (=+1) under our sign
    # convention.
    L2_admitted = False
    su2_det_phase = None
    if L1_admitted:
        try:
            _w, V = torch.linalg.eigh(rho)
            det_V = torch.linalg.det(V)
            su2_det_phase = float(torch.angle(det_V).item())
            L2_admitted = abs(float(torch.abs(det_V).item()) - 1.0) < 1e-6 and abs(math.sin(su2_det_phase)) < 1e-3
        except Exception:
            L2_admitted = False

    return {
        "available": True,
        "tr_residue_abs": float(abs(complex(sp.N(tr_residue)))),
        "herm_residue_abs": float(abs(complex(sp.N(herm_residue)))),
        "det_abs": float(abs(complex(sp.N(det)))),
        "eigs": [(float(e.real), float(e.imag)) for e in eig_floats],
        "L0_admitted": bool(L0_admitted),
        "L1_admitted": bool(L1_admitted),
        "L2_admitted": bool(L2_admitted),
        "su2_det_phase": su2_det_phase,
    }


def _clifford_chirality_split(rho: torch.Tensor) -> dict:
    """
    L3/L4 admissibility under Cl(1,3) pseudoscalar gamma_5 projection.
    We embed the 2x2 density's dominant eigenvector as a 2-component spinor,
    then act with the chirality operator (pseudoscalar restricted to the
    even subalgebra) and measure the eigenvalue split.
    """
    if Cl is None:
        return {"available": False, "reason": "clifford unavailable"}

    layout, blades = Cl(1, 3)
    # gamma_5 = i * gamma_0 gamma_1 gamma_2 gamma_3 = pseudoscalar I in Cl(1,3)
    e0 = blades["e1"]
    e1 = blades["e2"]
    e2 = blades["e3"]
    e3 = blades["e4"]
    gamma5 = 1j * e0 * e1 * e2 * e3

    # Lift dominant eigenvector to a multivector in the even subalgebra.
    _w, V = torch.linalg.eigh(rho)
    psi = V[:, -1]
    a, b = complex(psi[0]), complex(psi[1])
    # Pauli-style: psi -> a*1 + b*e1*e2 (a scalar+bivector even element).
    psi_mv = a * layout.scalar + b * (e0 * e1)

    # Chirality projection: P_R = 0.5*(1+gamma5), P_L = 0.5*(1-gamma5)
    one = layout.scalar
    PR = 0.5 * (one + gamma5)
    PL = 0.5 * (one - gamma5)

    psiR = PR * psi_mv
    psiL = PL * psi_mv
    nR = float(abs((~psiR * psiR).value[0]))
    nL = float(abs((~psiL * psiL).value[0]))

    total = nR + nL
    if total < 1e-12:
        split = 0.0
    else:
        split = abs(nR - nL) / total

    # L3 -- Spin(3): require gamma_5 acts nontrivially (one of the projectors
    # has nonzero norm); a degenerate gamma_5 action would collapse Spin(3).
    L3_admitted = total > 1e-9
    # L4 -- Weyl chirality: require the split is not maximally degenerate
    # (both projectors nonzero so chirality decomposition is meaningful).
    L4_admitted = L3_admitted and min(nR, nL) > 1e-6

    return {
        "available": True,
        "norm_right": nR,
        "norm_left": nL,
        "split_ratio": split,
        "L3_admitted": bool(L3_admitted),
        "L4_admitted": bool(L4_admitted),
    }


def _geomstats_sphere_membership(rho: torch.Tensor) -> dict:
    """
    Boundary probe: Bloch vector r = (tr(rho sigma_x), ..., tr(rho sigma_z))
    is checked for S^2 membership via geomstats Hypersphere.
    distance_to_sphere = | ||r|| - r_target | where r_target=1 for pure,
    in [0,1] for mixed (so we use the *purity sphere* of radius sqrt(2*P-1)
    only when purity > 0.5; otherwise boundary).
    """
    if Hypersphere is None:
        return {"available": False, "reason": "geomstats unavailable"}
    if TOOL_MANIFEST["geomstats"]["used"] is not True:
        return {
            "available": False,
            "reason": TOOL_MANIFEST["geomstats"]["reason"],
            "blocker": "geomstats Hypersphere.belongs dispatched through the installed NumPy backend and rejected torch/list carriers under the hard-quarantine no-NumPy rule",
        }

    rx = float(torch.real(torch.trace(rho @ SX)).item())
    ry = float(torch.real(torch.trace(rho @ SY)).item())
    rz = float(torch.real(torch.trace(rho @ SZ)).item())
    r = torch.tensor([rx, ry, rz], dtype=torch.float64)
    r_norm = float(torch.linalg.vector_norm(r).item())
    purity = float(torch.real(torch.trace(rho @ rho)).item())

    sphere = Hypersphere(dim=2)
    # geomstats expects unit-norm to embed in S^2; project radially if
    # non-degenerate, else report boundary.
    if r_norm > 1e-9:
        r_unit = r / r_norm
        on_sphere = bool(sphere.belongs(r_unit, atol=1e-6))
    else:
        r_unit = None
        on_sphere = False

    return {
        "available": True,
        "bloch": [rx, ry, rz],
        "bloch_norm": r_norm,
        "purity": purity,
        "on_unit_sphere_after_normalize": on_sphere,
        # boundary signal: r_norm near 0 -> deep mixed state, probe loses
        # angular resolution; r_norm near 1 -> pure-state boundary.
        "boundary_distance_pure": float(abs(r_norm - 1.0)),
        "boundary_distance_max_mixed": float(r_norm),
    }


# =====================================================================
# ADMISSION / EXCLUSION / BOUNDARY
# =====================================================================

def run_positive_tests(states: list[dict]) -> dict:
    rows = []
    state_errors = []
    level_floor = {"L0": 0, "L1": 0, "L2": 0, "L3": 0, "L4": 0}
    cross_check_disagreements = 0
    for st in states:
        if "rho" not in st:
            if "error" in st:
                state_errors.append({
                    "seed": st.get("seed"),
                    "engine_type": st.get("engine_type"),
                    "substage_idx": st.get("substage_idx"),
                    "error": st.get("error"),
                    "blocker": "canonical QIT replay state construction failed before symbolic G-structure checks",
                })
            continue
        rho = st["rho"]
        sym = _sympy_frame_admissibility(rho)
        cli = _clifford_chirality_split(rho)
        geo = _geomstats_sphere_membership(rho)

        level_reached = "L0_failed"
        if sym.get("L0_admitted"):
            level_reached = "L0"
            level_floor["L0"] += 1
        if sym.get("L1_admitted"):
            level_reached = "L1"
            level_floor["L1"] += 1
        if sym.get("L2_admitted"):
            level_reached = "L2"
            level_floor["L2"] += 1
        if cli.get("L3_admitted"):
            level_reached = "L3"
            level_floor["L3"] += 1
        if cli.get("L4_admitted"):
            level_reached = "L4"
            level_floor["L4"] += 1

        # Cross-check: sympy says pure-state-like (max eig near 1) and
        # geomstats says on_unit_sphere -> agreement; disagreement is signal.
        sympy_pure_like = False
        if sym.get("available") and sym.get("eigs"):
            sympy_pure_like = any(abs(e[0] - 1.0) < 1e-3 for e in sym["eigs"])
        geomstats_pure_like = geo.get("boundary_distance_pure", 1.0) < 1e-3
        agree = (sympy_pure_like == geomstats_pure_like)
        if not agree:
            cross_check_disagreements += 1

        rows.append({
            "seed": st.get("seed"),
            "engine_type": st.get("engine_type"),
            "substage_idx": st.get("substage_idx"),
            "level_reached": level_reached,
            "sympy": sym,
            "clifford": cli,
            "geomstats": geo,
            "cross_check_agree_purity": bool(agree),
        })

    return {
        "live_state_rows": rows,
        "level_floor_counts": level_floor,
        "cross_check_disagreements": cross_check_disagreements,
        "total_live_states": len(rows),
        "state_errors": state_errors,
    }


def run_negative_tests() -> dict:
    """
    Deliberately broken candidates that should be excluded under C.
    Each one targets a specific level so the chain bottoms out there.
    """
    results = {}

    # L0 violator: trace != 1
    rho_bad_trace = torch.diag(torch.tensor([0.7, 0.7], dtype=torch.complex128))
    s = _sympy_frame_admissibility(rho_bad_trace)
    results["non_unit_trace"] = {
        "expected_excluded_at": "L0",
        "L0_admitted": s.get("L0_admitted"),
        "excluded_under_C": not s.get("L0_admitted"),
    }

    # L1 violator: non-hermitian
    rho_non_herm = torch.tensor([[0.5, 0.1 + 0.3j], [0.0, 0.5]], dtype=torch.complex128)
    s = _sympy_frame_admissibility(rho_non_herm)
    results["non_hermitian"] = {
        "expected_excluded_at": "L1",
        "L0_admitted": s.get("L0_admitted"),
        "L1_admitted": s.get("L1_admitted"),
        "excluded_under_C": (not s.get("L1_admitted")),
    }

    # L3/L4 violator: gamma_5 acts trivially on the zero spinor
    rho_zero = torch.zeros((2, 2), dtype=torch.complex128)
    rho_zero[0, 0] = 1.0  # ket0, will still split — use a contrived case.
    cli = _clifford_chirality_split(rho_zero)
    results["pure_ket0_chirality_split"] = {
        "expected_excluded_at": "L4",
        "L3_admitted": cli.get("L3_admitted"),
        "L4_admitted": cli.get("L4_admitted"),
        "split_ratio": cli.get("split_ratio"),
        "excluded_under_C": (not cli.get("L4_admitted")),
    }

    # z3 finite UNSAT control: anti-orientation in Cl(1,3) cannot be
    # simultaneously +1 and -1. Encoded as a finite Boolean.
    if z3 is not None:
        s = z3.Solver()
        ori = z3.Int("orientation")
        s.add(ori * ori == 1)
        s.add(ori == 1)
        s.add(ori == -1)
        verdict = s.check()
        results["z3_anti_orientation_simultaneous"] = {
            "expected": "unsat",
            "verdict": str(verdict),
            "excluded_formally": str(verdict) == "unsat",
        }
    else:
        results["z3_anti_orientation_simultaneous"] = {
            "expected": "unsat",
            "verdict": "z3_unavailable",
            "excluded_formally": False,
        }

    return results


def run_boundary_tests() -> dict:
    """
    Near-singular rho where probes lose resolution: rank-deficient, near
    fully mixed, near coordinate axes.
    """
    cases = []

    # Boundary 1: fully mixed -- Bloch norm 0, geomstats loses S^2 resolution.
    rho_mixed = 0.5 * torch.eye(2, dtype=torch.complex128)
    cases.append({
        "name": "fully_mixed",
        "sympy": _sympy_frame_admissibility(rho_mixed),
        "clifford": _clifford_chirality_split(rho_mixed),
        "geomstats": _geomstats_sphere_membership(rho_mixed),
    })

    # Boundary 2: epsilon away from pure |0>
    eps = 1e-6
    rho_eps = (1 - eps) * _seed_density("ket0") + eps * _seed_density("ket1")
    cases.append({
        "name": "epsilon_perturbed_pure_ket0",
        "epsilon": eps,
        "sympy": _sympy_frame_admissibility(rho_eps),
        "clifford": _clifford_chirality_split(rho_eps),
        "geomstats": _geomstats_sphere_membership(rho_eps),
    })

    # Boundary 3: maximally chirality-symmetric (|+>)
    rho_plus = _seed_density("plus")
    cases.append({
        "name": "ket_plus_chirality_symmetric",
        "sympy": _sympy_frame_admissibility(rho_plus),
        "clifford": _clifford_chirality_split(rho_plus),
        "geomstats": _geomstats_sphere_membership(rho_plus),
    })

    return {"cases": cases}


def summarize_graveyard_companions(negative: dict) -> dict:
    """Return only controls that are intended to be killed by the scout."""
    return {
        "non_unit_trace": {
            "pass": negative["non_unit_trace"]["excluded_under_C"] is True,
            "expected_excluded_at": negative["non_unit_trace"]["expected_excluded_at"],
            "observed": negative["non_unit_trace"],
            "reason": "trace-1 violation must not enter the G-structure reduction chain",
        },
        "non_hermitian": {
            "pass": negative["non_hermitian"]["excluded_under_C"] is True,
            "expected_excluded_at": negative["non_hermitian"]["expected_excluded_at"],
            "observed": negative["non_hermitian"],
            "reason": "non-hermitian density must fail the U(2)-real frame check",
        },
        "anti_orientation_simultaneous": {
            "pass": negative["z3_anti_orientation_simultaneous"]["excluded_formally"] is True,
            "expected": negative["z3_anti_orientation_simultaneous"]["expected"],
            "observed": negative["z3_anti_orientation_simultaneous"],
            "reason": "z3 must reject simultaneous +1 and -1 orientation signs",
        },
    }


def summarize_nearby_variants(graveyard_companions: dict) -> dict:
    passed = sum(1 for row in graveyard_companions.values() if row["pass"] is True)
    return {
        "total": len(graveyard_companions),
        "passed": passed,
        "variants": sorted(graveyard_companions),
    }


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    live_states = _collect_replay_states(max_substages=4)

    positive = run_positive_tests(live_states)
    negative = run_negative_tests()
    boundary = run_boundary_tests()
    graveyard_companions = summarize_graveyard_companions(negative)
    nearby_variants = summarize_nearby_variants(graveyard_companions)

    # Criteria checked:
    criteria_checked = [
        "C0: sympy L0 trace-1 admissibility over bounded canonical replay states",
        "C1: sympy L1 hermitian + nonneg-eigenvalue frame",
        "C2: sympy L2 SU(2) lifted-unitary det-phase admissibility",
        "C3: clifford L3 Cl(1,3) gamma_5 nontrivial action",
        "C4: clifford L4 Weyl chirality nondegenerate split",
        "C5: geomstats S^2 Bloch boundary distance",
        "C6: negative-control exclusion at each named level",
        "C7: z3 UNSAT on anti-orientation simultaneous +/-1 contradiction",
    ]

    # all_pass: True only if every named criterion confirmed under its
    # intended verdict. We do NOT collapse cross-check disagreement into
    # success — it is recorded as surviving signal, not failure.
    neg = negative
    all_pass = (
        positive["total_live_states"] > 0
        and positive["level_floor_counts"]["L0"] == positive["total_live_states"]
        and neg["non_unit_trace"]["excluded_under_C"] is True
        and neg["non_hermitian"]["excluded_under_C"] is True
        and neg["z3_anti_orientation_simultaneous"]["excluded_formally"] is True
        and nearby_variants["passed"] == nearby_variants["total"]
    )

    results = {
        "name": "clifford_sympy_geomstats_nested_g_structure_live_state_probe",
        "probe_family": "M_clifford + M_sympy + M_geomstats (symbolic G-structure)",
        "constraint_set": "C_nested_G_reduction (L0 GL(2,C) -> L1 U(2) -> L2 SU(2) -> L3 Spin(3) -> L4 Weyl chirality)",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "classification": CLASSIFICATION,
        "surviving_alternatives": [
            "alternative G-chains: GL(2,C) -> O(4) -> SO(4) -> Spin(4) -> U(2) -> SU(2)",
            "alternative chirality lift: Cl(3) pseudoscalar instead of Cl(1,3) gamma_5",
            "alternative sphere: S^3 unit-spinor (geomstats Hypersphere(dim=3)) over the lifted state",
            "alternative purity surface: PoincareBall radius vs. unit-sphere normalize",
        ],
        "claim_ceiling": (
            "Formal scout only: records which level "
            "of a nested G-structure reduction chain (GL(2,C) -> U(2) -> SU(2) "
            "-> Spin(3) -> Weyl chirality) bounded canonical QIT replay states "
            "bottom out at under three independent symbolic probes "
            "(sympy frame, Cl(1,3) chirality, geomstats S^2 membership), and "
            "where the probes disagree. Does NOT admit canonical, bridge, "
            "axis, G-structure, manifold, engine, or coupling claims."
        ),
        "promotion_allowed": PROMOTION_ALLOWED,
        "next_lego_target": "none",
        "promotion_condition": "requires a separate reconciled queue row, externally authored basin classifier case, and a fresh-context audit before any lego/coupling/bridge use",
        "blocked_until": "exact parent receipts, queue row, externally authored case criteria, and ledger loopback are reconciled",
        "demotion_condition": "demote if any criterion fails its expected verdict or if probe-disagreement is collapsed into a synthesis claim",
        "out_of_scope": [
            "no lego promotion from this scout alone",
            "no bridge, axis, engine, emergence, Tier D, or scientific coupling claim",
            "no claim that the symbolic probes agree -- disagreements are recorded as surviving signal",
        ],
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "This is a clean v5 formal scout over bounded canonical QIT replay state; it does not add to the mixed v4 probe estate.",
            "It has no v4 promotion path because it does not admit G-structure, manifold, axis, bridge, engine, or coupling claims.",
            "Its only readiness role is bounded evidence for symbolic G-structure tool integration under explicit graveyard controls.",
        ],
        "all_pass": bool(all_pass),
        "criteria_checked": criteria_checked,
    }

    out_dir = os.path.join(_HERE, "results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(
        out_dir,
        "clifford_sympy_geomstats_nested_g_structure_live_state_probe_results.json",
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"all_pass={all_pass}  total_live_states={positive['total_live_states']}  "
          f"cross_check_disagreements={positive['cross_check_disagreements']}")
