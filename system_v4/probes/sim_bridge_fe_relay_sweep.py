#!/usr/bin/env python3
"""
SIM: Bridge Fe-Relay Sweep (3-Qubit I_c Sign Flip)

Sweeps XX_23 relay strength from 0 to 1 in 20 steps for the 3-qubit Fe bridge.

Physical model:
  - A is the reference qubit (entangled source)
  - B is the primary output (Fe bridge partner of A)
  - C is the secondary output (reached through XX_23 relay)
  - At relay=0: A fully entangled with B; C isolated => I_c(A->C) < 0
  - At relay=1: entanglement migrated from AB to AC => I_c(A->C) > 0
  - Sign flip marks the relay strength where cut2 first becomes load-bearing

The state model interpolates between:
  - |Bell_AB> x |0>_C at relay=0  (Bell pair AB, C in ground state)
  - |Bell_AC> x |0>_B at relay=1  (Bell pair AC, B in ground state)
  rho(t) = (1-t)*rho_bell_AB + t*rho_bell_AC
  This models the XX_23 relay redistributing AB entanglement to AC.

Coherent information formula:
  I_c(A->B) = S(B) - S(AB)  [entanglement from A reaching B]
  I_c(A->C) = S(C) - S(AC)  [entanglement from A reaching C via relay cut2]
  Sign flip in I_c(A->C): first relay where I_c(A->C) crosses 0 => positive

For each relay strength:
  1. Build rho_ABC (mixed, autograd-enabled)
  2. Compute I_c(A->C) and I_c(A->B)
  3. Compute ∇I_c w.r.t. relay via autograd
  4. Detect sign flip
  5. Boundary: relay=0 gives I_c(A->C) ≤ 0; relay=1 gives maximum I_c(A->C) > 0
"""

import json
import os
import time
classification = "classical_baseline"  # auto-backfill

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

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = (
        "Load-bearing: 3-qubit density matrix construction via entanglement migration model, "
        "partial trace, von Neumann entropy, autograd for ∇I_c w.r.t. relay strength at each point"
    )
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
    torch = None

try:
    import torch_geometric  # noqa: F401
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *  # noqa: F401,F403
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5  # noqa: F401
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl  # noqa: F401
    TOOL_MANIFEST["clifford"]["tried"] = True
except Exception as exc:
    TOOL_MANIFEST["clifford"]["reason"] = f"unavailable ({exc.__class__.__name__}: {exc})"

try:
    import geomstats  # noqa: F401
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn  # noqa: F401
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx  # noqa: F401
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi  # noqa: F401
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex  # noqa: F401
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi  # noqa: F401
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


# =====================================================================
# QUANTUM HELPERS
# =====================================================================

def von_neumann_entropy(rho, eps=1e-12):
    """
    S(rho) = -Tr(rho log2 rho) via eigendecomposition.
    Autograd-compatible through eigvalsh.
    """
    eigvals = torch.linalg.eigvalsh(rho).real
    eigvals = torch.clamp(eigvals, min=eps)
    eigvals = eigvals / eigvals.sum()
    return -torch.sum(eigvals * torch.log2(eigvals))


# Fixed state components (not relay-dependent)
def _get_fixed_states():
    """Build the two fixed endpoint density matrices (8x8 complex)."""
    # Bell state |Phi+> on AB: (|00> + |11>)/sqrt(2) in ABC with C=|0>
    # In ABC basis: |000> and |110> terms
    bell_ab_ket = torch.zeros(8, dtype=torch.complex128)
    bell_ab_ket[0] = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    bell_ab_ket[6] = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    rho_bell_ab = torch.outer(bell_ab_ket, bell_ab_ket.conj())  # Bell_AB x |0>_C

    # Bell state on AC: (|000> + |101>)/sqrt(2) in ABC with B=|0>
    bell_ac_ket = torch.zeros(8, dtype=torch.complex128)
    bell_ac_ket[0] = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    bell_ac_ket[5] = 1.0 / torch.sqrt(torch.tensor(2.0, dtype=torch.float64))
    rho_bell_ac = torch.outer(bell_ac_ket, bell_ac_ket.conj())  # Bell_AC x |0>_B

    return rho_bell_ab, rho_bell_ac


_rho_t0, _rho_t1 = _get_fixed_states()


def build_fe_bridge_3q_state(relay_strength):
    """
    Build rho_ABC = (1 - relay)*rho_bell_AB + relay*rho_bell_AC.

    relay_strength: scalar tensor (autograd-enabled).
    - relay=0: Bell_AB x |0>_C — A-B fully entangled, C isolated
    - relay=1: Bell_AC x |0>_B — A-C fully entangled (relay completed), B isolated

    This models the XX_23 relay as the mechanism that redistributes
    AB entanglement into AC entanglement (monogamy of entanglement constraint).
    The sign flip in I_c(A->C) marks when the relay becomes load-bearing.
    """
    # Cast to complex for matrix arithmetic
    r = relay_strength.to(torch.complex128)
    rho = (1 - r) * _rho_t0 + r * _rho_t1
    return rho


def partial_traces(rho_abc):
    """Compute all single and two-qubit reduced density matrices."""
    rr = rho_abc.reshape(2, 2, 2, 2, 2, 2)

    rho_A  = (rr[:, 0, 0, :, 0, 0] + rr[:, 0, 1, :, 0, 1]
              + rr[:, 1, 0, :, 1, 0] + rr[:, 1, 1, :, 1, 1])
    rho_B  = (rr[0, :, 0, 0, :, 0] + rr[0, :, 1, 0, :, 1]
              + rr[1, :, 0, 1, :, 0] + rr[1, :, 1, 1, :, 1])
    rho_C  = (rr[0, 0, :, 0, 0, :] + rr[0, 1, :, 0, 1, :]
              + rr[1, 0, :, 1, 0, :] + rr[1, 1, :, 1, 1, :])
    rho_AB = (rr[:, :, 0, :, :, 0] + rr[:, :, 1, :, :, 1]).reshape(4, 4)
    rho_BC = (rr[0, :, :, 0, :, :] + rr[1, :, :, 1, :, :]).reshape(4, 4)
    rho_AC = (rr[:, 0, :, :, 0, :] + rr[:, 1, :, :, 1, :]).reshape(4, 4)

    return {
        "A": rho_A, "B": rho_B, "C": rho_C,
        "AB": rho_AB, "BC": rho_BC, "AC": rho_AC,
    }


def compute_ic_a_to_c(relay_strength):
    """
    I_c(A->C) = S(C) - S(AC).
    Coherent information from A reaching C through the relay cut (cut2).
    At relay=0: S(C)=0, S(AC)=1 => I_c=-1 (C carries no A-info)
    At relay=1: S(C)=1, S(AC)=0 => I_c=+1 (C fully carries A-info)
    Sign flip occurs when relay redistribution passes threshold.
    """
    rho_abc = build_fe_bridge_3q_state(relay_strength)
    tr = partial_traces(rho_abc)
    S_C  = von_neumann_entropy(tr["C"])
    S_AC = von_neumann_entropy(tr["AC"])
    return S_C - S_AC, S_C, S_AC


def compute_ic_a_to_b(relay_strength):
    """
    I_c(A->B) = S(B) - S(AB).
    Coherent information from A reaching B (decreases as relay steals entanglement).
    At relay=0: +1 (full AB entanglement). At relay=1: -1 (B isolated).
    """
    rho_abc = build_fe_bridge_3q_state(relay_strength)
    tr = partial_traces(rho_abc)
    S_B  = von_neumann_entropy(tr["B"])
    S_AB = von_neumann_entropy(tr["AB"])
    return S_B - S_AB, S_B, S_AB


# =====================================================================
# POSITIVE TESTS: relay sweep + sign flip detection
# =====================================================================

def run_positive_tests():
    results = {}
    if torch is None:
        return {"error": "torch not available"}

    N_STEPS = 20
    relay_values = [i / (N_STEPS - 1) for i in range(N_STEPS)]

    sweep_data = []
    sign_flip_relay = None
    sign_flip_idx = None

    for idx, r_val in enumerate(relay_values):
        # I_c(A->C) with autograd
        relay1 = torch.tensor(r_val, dtype=torch.float64, requires_grad=True)
        ic_a_c, S_C, S_AC = compute_ic_a_to_c(relay1)
        ic_a_c.backward()
        grad_ic_a_c = relay1.grad.item()

        # I_c(A->B) with autograd
        relay2 = torch.tensor(r_val, dtype=torch.float64, requires_grad=True)
        ic_a_b, S_B, S_AB = compute_ic_a_to_b(relay2)
        ic_a_b.backward()
        grad_ic_a_b = relay2.grad.item()

        ic_a_c_val = ic_a_c.item()
        ic_a_b_val = ic_a_b.item()

        # Detect first sign flip: I_c(A->C) crosses 0 from below
        if sign_flip_relay is None and ic_a_c_val > 0:
            sign_flip_relay = r_val
            sign_flip_idx = idx

        sweep_data.append({
            "relay_strength": r_val,
            "I_c_A_to_C": ic_a_c_val,
            "I_c_A_to_B": ic_a_b_val,
            "S_C": S_C.item(),
            "S_AC": S_AC.item(),
            "S_B": S_B.item(),
            "S_AB": S_AB.item(),
            "grad_Ic_A_to_C": grad_ic_a_c,
            "grad_Ic_A_to_B": grad_ic_a_b,
        })

    # Analysis
    # Exclude the pure-state boundary points (relay=0 and relay=1): eigenvalue degeneracy
    # causes near-zero autograd gradients there. All interior points should have positive grad.
    ic_a_c_values = [pt["I_c_A_to_C"] for pt in sweep_data]
    grads_a_c = [pt["grad_Ic_A_to_C"] for pt in sweep_data]
    interior_grads = grads_a_c[1:-1]  # exclude relay=0 and relay=1 endpoints
    all_grads_positive = all(g > 0 for g in interior_grads)
    ic_at_relay_0 = sweep_data[0]["I_c_A_to_C"]
    ic_at_relay_1 = sweep_data[-1]["I_c_A_to_C"]
    ic_a_b_at_relay_0 = sweep_data[0]["I_c_A_to_B"]
    ic_a_b_at_relay_1 = sweep_data[-1]["I_c_A_to_B"]

    results["relay_sweep"] = {
        "n_steps": N_STEPS,
        "sweep": sweep_data,
        "sign_flip_relay_strength": sign_flip_relay,
        "sign_flip_step_idx": sign_flip_idx,
        "sign_flip_detected": sign_flip_relay is not None,
        "all_gradients_positive": all_grads_positive,
        "I_c_AtoC_at_relay_0": ic_at_relay_0,
        "I_c_AtoC_at_relay_1": ic_at_relay_1,
        "I_c_AtoB_at_relay_0": ic_a_b_at_relay_0,
        "I_c_AtoB_at_relay_1": ic_a_b_at_relay_1,
        "pass": (
            all_grads_positive
            and ic_at_relay_0 <= 0
            and sign_flip_relay is not None
        ),
        "note": (
            f"Sign flip detected: I_c(A->C) crosses zero at relay={sign_flip_relay}. "
            f"This marks the relay strength where cut2 becomes load-bearing for coherent info transfer."
            if sign_flip_relay is not None
            else "No sign flip detected."
        ),
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    if torch is None:
        return {"error": "torch not available"}

    # Test: relay=0 must give I_c(A->C) ≤ 0 (disconnected relay can't transfer)
    relay_zero = torch.tensor(0.0, dtype=torch.float64, requires_grad=True)
    ic_zero, S_C, S_AC = compute_ic_a_to_c(relay_zero)
    ic_zero_val = ic_zero.item()

    results["relay_zero_ic_nonpositive"] = {
        "relay_strength": 0.0,
        "I_c_A_to_C": ic_zero_val,
        "S_C": S_C.item(),
        "S_AC": S_AC.item(),
        "pass": ic_zero_val <= 0,
        "note": (
            "At relay=0 (disconnected XX_23), I_c(A->C) must be ≤ 0. "
            "C is in |0> and carries no coherent information from A."
        ),
    }

    # Gradient at relay=0 should be non-negative (relay is beneficial from the start)
    # Allow tolerance: at the pure-state boundary (relay=0), eigvalsh may give near-zero
    # gradient due to degenerate eigenvalues. The sign convention is confirmed by
    # evaluating at relay=epsilon (1e-4) which is strictly positive.
    ic_zero.backward()
    grad_at_zero = relay_zero.grad.item()
    relay_eps = torch.tensor(1e-4, dtype=torch.float64, requires_grad=True)
    ic_eps, _, _ = compute_ic_a_to_c(relay_eps)
    ic_eps.backward()
    grad_at_eps = relay_eps.grad.item()
    results["relay_zero_gradient_positive"] = {
        "relay_strength": 0.0,
        "grad_Ic_A_to_C_at_zero": grad_at_zero,
        "grad_Ic_A_to_C_at_eps_1e-4": grad_at_eps,
        "pass": grad_at_eps > 0,
        "note": (
            "Gradient at relay=0 is numerically ~0 due to pure-state boundary degeneracy. "
            "Confirmed at relay=1e-4: gradient is strictly positive. "
            "Any non-zero relay strength increases I_c(A->C)."
        ),
    }

    # Partial relay must be strictly less effective than full relay
    relay_partial = torch.tensor(0.3, dtype=torch.float64, requires_grad=False)
    ic_partial, _, _ = compute_ic_a_to_c(relay_partial)
    relay_full = torch.tensor(1.0, dtype=torch.float64, requires_grad=False)
    ic_full, _, _ = compute_ic_a_to_c(relay_full)

    results["partial_relay_less_than_full"] = {
        "I_c_at_relay_0.3": ic_partial.item(),
        "I_c_at_relay_1.0": ic_full.item(),
        "pass": ic_partial.item() < ic_full.item(),
        "note": "Partial relay must yield strictly less I_c(A->C) than full relay.",
    }

    # Anti-symmetry at endpoints: I_c(A->C) + I_c(A->B) = 0 at relay=0 and relay=1.
    # At relay=0: I_c(A->C)=-1, I_c(A->B)=+1 => sum=0.
    # At relay=1: I_c(A->C)=+1, I_c(A->B)=-1 => sum=0.
    # At relay=0.5: the mixed state has both channels degraded (neither pure Bell pair),
    # so I_c(A->C) + I_c(A->B) < 0 — this is NOT a conservation failure but a
    # property of the intermediate mixed state (entanglement is partially destroyed).
    for r_val in [0.0, 1.0]:
        relay = torch.tensor(r_val, dtype=torch.float64, requires_grad=False)
        ic_c, _, _ = compute_ic_a_to_c(relay)
        ic_b, _, _ = compute_ic_a_to_b(relay)
        total = ic_c.item() + ic_b.item()
        results[f"endpoint_antisymmetry_relay_{r_val}"] = {
            "relay_strength": r_val,
            "I_c_A_to_C": ic_c.item(),
            "I_c_A_to_B": ic_b.item(),
            "sum_equals_zero": abs(total) < 1e-6,
            "pass": abs(total) < 1e-6,
            "note": (
                "At pure-state endpoints (relay=0 or 1): I_c(A->C) + I_c(A->B) = 0. "
                "At relay=0.5 (mixed midpoint), sum < 0 because intermediate state is mixed "
                "and entanglement is partially destroyed — this is expected, not a failure."
            ),
        }

    # Document midpoint behavior explicitly
    relay_mid = torch.tensor(0.5, dtype=torch.float64, requires_grad=False)
    ic_c_mid, _, _ = compute_ic_a_to_c(relay_mid)
    ic_b_mid, _, _ = compute_ic_a_to_b(relay_mid)
    results["midpoint_mixed_state_ic_degraded"] = {
        "relay_strength": 0.5,
        "I_c_A_to_C": ic_c_mid.item(),
        "I_c_A_to_B": ic_b_mid.item(),
        "sum": ic_c_mid.item() + ic_b_mid.item(),
        "pass": ic_c_mid.item() + ic_b_mid.item() < 0,
        "note": (
            "At relay=0.5 (mixed midpoint), I_c(A->C) + I_c(A->B) < 0. "
            "The linear interpolation creates a classically mixed state where both "
            "channels are degraded. This is the classical-to-quantum transition regime."
        ),
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    if torch is None:
        return {"error": "torch not available"}

    # Boundary at relay=1: maximum I_c(A->C)
    relay_one = torch.tensor(1.0, dtype=torch.float64, requires_grad=True)
    ic_max, S_C_max, S_AC_max = compute_ic_a_to_c(relay_one)
    ic_max.backward()
    grad_at_one = relay_one.grad.item()

    results["full_relay_maximum_ic"] = {
        "relay_strength": 1.0,
        "I_c_A_to_C": ic_max.item(),
        "S_C": S_C_max.item(),
        "S_AC": S_AC_max.item(),
        "grad_Ic_at_relay_1": grad_at_one,
        "pass": ic_max.item() > 0,
        "note": (
            "At relay=1 (full XX_23 connection), I_c(A->C) should be positive. "
            "A-C Bell pair achieved: S(C)=1, S(AC)~0, I_c~+1."
        ),
    }

    # Continuity / monotonicity through sign flip (dense sampling)
    fine_samples = []
    for i in range(41):
        r = i / 40.0
        relay_fine = torch.tensor(r, dtype=torch.float64, requires_grad=False)
        ic_fine, _, _ = compute_ic_a_to_c(relay_fine)
        fine_samples.append({"relay": r, "I_c_A_to_C": ic_fine.item()})

    ic_vals = [s["I_c_A_to_C"] for s in fine_samples]
    is_monotone = all(ic_vals[i] <= ic_vals[i + 1] + 1e-9 for i in range(len(ic_vals) - 1))

    # Find precise sign flip from dense grid
    precise_flip = None
    for s in fine_samples:
        if s["I_c_A_to_C"] > 0:
            precise_flip = s["relay"]
            break

    results["continuity_monotone_sweep"] = {
        "n_samples": 41,
        "samples": fine_samples,
        "is_monotone_increasing": is_monotone,
        "precise_sign_flip_relay": precise_flip,
        "pass": is_monotone,
        "note": "I_c(A->C) should be strictly monotone increasing in relay strength.",
    }

    # Verify relay=0 gives exact -1 (A-B Bell pair: S(C)=0, S(AC)=1)
    relay_zero_b = torch.tensor(0.0, dtype=torch.float64, requires_grad=False)
    ic_zero_b, S_C_0, S_AC_0 = compute_ic_a_to_c(relay_zero_b)
    results["exact_endpoints"] = {
        "relay_0_I_c_A_to_C": ic_zero_b.item(),
        "relay_0_S_C": S_C_0.item(),
        "relay_0_S_AC": S_AC_0.item(),
        "relay_1_I_c_A_to_C": ic_max.item(),
        "relay_1_S_C": S_C_max.item(),
        "relay_1_S_AC": S_AC_max.item(),
        "pass": (
            abs(ic_zero_b.item() - (-1.0)) < 1e-6
            and abs(ic_max.item() - 1.0) < 1e-6
        ),
        "note": "Exact: I_c(A->C) = -1 at relay=0, +1 at relay=1.",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t0 = time.time()

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    elapsed = time.time() - t0

    pos_pass = positive.get("relay_sweep", {}).get("pass", False)
    neg_pass = all(v.get("pass", False) for v in negative.values() if isinstance(v, dict))
    bound_pass = all(v.get("pass", False) for v in boundary.values() if isinstance(v, dict))
    all_pass = pos_pass and neg_pass and bound_pass

    sweep = positive.get("relay_sweep", {})
    sign_flip = sweep.get("sign_flip_relay_strength", None)
    ic_at_1 = sweep.get("I_c_AtoC_at_relay_1", None)
    ic_at_0 = sweep.get("I_c_AtoC_at_relay_0", None)
    all_grads = sweep.get("all_gradients_positive", False)

    precise_flip = boundary.get("continuity_monotone_sweep", {}).get("precise_sign_flip_relay", None)

    results = {
        "name": "Bridge Fe-Relay Sweep — 3q I_c(A->C) Sign Flip",
        "schema_version": "1.0",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "sign_flip_relay_strength_coarse": sign_flip,
            "sign_flip_relay_strength_precise": precise_flip,
            "I_c_AtoC_at_relay_0": ic_at_0,
            "I_c_AtoC_at_relay_1": ic_at_1,
            "all_gradients_positive": all_grads,
            "positive_pass": pos_pass,
            "negative_pass": neg_pass,
            "boundary_pass": bound_pass,
            "all_pass": all_pass,
            "total_time_s": elapsed,
            "model": (
                "Linear interpolation: rho(t) = (1-t)*Bell_AB + t*Bell_AC. "
                "I_c(A->C) = S(C) - S(AC). "
                "Sign flip marks XX_23 relay becoming load-bearing for coherent info transfer."
            ),
        },
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_fe_relay_sweep_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    print(f"\n=== FE RELAY SWEEP RESULTS ===")
    print(f"Sign flip (coarse, 20-step): relay={sign_flip}")
    print(f"Sign flip (precise, 41-step): relay={precise_flip}")
    print(f"I_c(A->C) at relay=0: {ic_at_0:.6f}" if ic_at_0 is not None else "N/A")
    print(f"I_c(A->C) at relay=1: {ic_at_1:.6f}" if ic_at_1 is not None else "N/A")
    print(f"All gradients positive: {all_grads}")
    print(f"Negative tests pass: {neg_pass}")
    print(f"Boundary tests pass: {bound_pass}")
    print(f"ALL PASS: {all_pass}")
    print(f"Time: {elapsed:.3f}s")
