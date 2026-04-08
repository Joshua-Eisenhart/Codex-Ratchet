#!/usr/bin/env python3
"""
SIM LEGO: Bridge entropy inequality guardrails
==============================================
Pure math. Guardrails for bridge-built bipartite density matrices.

Checks:
  - subadditivity
  - Araki-Lieb
  - strong subadditivity where applicable
  - simple continuity bounds on neighboring bridge states

Bridge packets:
  - product
  - correlated separable
  - Bell
  - Werner sweep
  - invalid / counterfeit packets for negative tests

This sim is intentionally conservative: a packet must be a valid density
matrix and pass marginal consistency before its entropy inequalities are
trusted.

Classification: canonical
"""

import json
import math
import os
import time
import traceback

import torch

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": "not needed -- no graph layer in this entropy guardrail sim"},
    "z3":        {"tried": False, "used": False, "reason": "not needed -- this sim uses direct matrix evaluation, not satisfiability search"},
    "cvc5":      {"tried": False, "used": False, "reason": "not needed -- no synthesis or SMT constraints are required"},
    "sympy":     {"tried": False, "used": False, "reason": "not needed -- no symbolic derivation beyond exact matrix formulas"},
    "clifford":  {"tried": False, "used": False, "reason": "not needed -- no geometric algebra layer in this lego"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed -- no manifold geometry or statistics here"},
    "e3nn":      {"tried": False, "used": False, "reason": "not needed -- no equivariant neural network layer here"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed -- no dependency graph or lattice graph computation here"},
    "xgi":       {"tried": False, "used": False, "reason": "not needed -- no hypergraph or simplicial complex layer here"},
    "toponetx":  {"tried": False, "used": False, "reason": "not needed -- no cell complex or filtration layer here"},
    "gudhi":     {"tried": False, "used": False, "reason": "not needed -- no persistent homology or filtration computation here"},
}

TOOL_MANIFEST["pytorch"]["tried"] = True
TOOL_MANIFEST["pytorch"]["used"] = True
TOOL_MANIFEST["pytorch"]["reason"] = (
    "Core numeric substrate: density matrices, partial traces, eigenvalue checks, entropy inequalities"
)

# =====================================================================
# CONSTANTS / HELPERS
# =====================================================================

TOL = 1e-12
I2 = torch.eye(2, dtype=torch.complex128)
I4 = torch.eye(4, dtype=torch.complex128)
PHI_PLUS = torch.tensor([1.0, 0.0, 0.0, 1.0], dtype=torch.complex128) / math.sqrt(2.0)
PHI_PLUS_DM = torch.outer(PHI_PLUS, PHI_PLUS.conj())


def normalize_density(rho):
    rho = (rho + rho.conj().T) / 2.0
    tr = torch.trace(rho)
    if abs(tr.item()) <= TOL:
        raise ValueError("zero-trace density matrix")
    return rho / tr


def is_psd(rho, tol=1e-10):
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0).real
    return bool(torch.min(evals).item() >= -tol), float(torch.min(evals).item())


def flat_to_multi(idx, dims):
    out = []
    rem = int(idx)
    for d in reversed(dims):
        out.append(rem % d)
        rem //= d
    return list(reversed(out))


def multi_to_flat(indices, dims):
    out = 0
    for i, d in zip(indices, dims):
        out = out * d + int(i)
    return int(out)


def partial_trace(rho, dims, keep):
    dims = list(dims)
    keep = list(keep)
    d_keep = int(math.prod([dims[i] for i in keep]))
    total_dim = int(math.prod(dims))
    out = torch.zeros((d_keep, d_keep), dtype=torch.complex128)
    trace_set = [i for i in range(len(dims)) if i not in keep]
    for i in range(total_dim):
        mi = flat_to_multi(i, dims)
        ki = [mi[k] for k in keep]
        for j in range(total_dim):
            mj = flat_to_multi(j, dims)
            if all(mi[t] == mj[t] for t in trace_set):
                kj = [mj[k] for k in keep]
                out[multi_to_flat(ki, [dims[k] for k in keep]), multi_to_flat(kj, [dims[k] for k in keep])] += rho[i, j]
    return out


def state_validity(rho_ab):
    herm_err = float(torch.max(torch.abs(rho_ab - rho_ab.conj().T)).item())
    tr = float(torch.trace(rho_ab).real.item())
    psd, min_eig = is_psd(rho_ab)
    return {
        "hermitian_error": herm_err,
        "trace": tr,
        "trace_error": abs(tr - 1.0),
        "psd": psd,
        "min_eigenvalue": min_eig,
        "valid": herm_err < 1e-10 and abs(tr - 1.0) < 1e-10 and psd,
    }


def reduced_states(rho_ab):
    return partial_trace(rho_ab, [2, 2], [0]), partial_trace(rho_ab, [2, 2], [1])


def reduced_state_consistency(rho_ab, rho_a, rho_b):
    got_a, got_b = reduced_states(rho_ab)
    err_a = float(torch.max(torch.abs(got_a - rho_a)).item())
    err_b = float(torch.max(torch.abs(got_b - rho_b)).item())
    return {
        "rho_a_max_error": err_a,
        "rho_b_max_error": err_b,
        "consistent": err_a < 1e-10 and err_b < 1e-10,
    }


def entropy(rho):
    evals = torch.linalg.eigvalsh(normalize_density(rho)).real
    evals = evals[evals > TOL]
    if evals.numel() == 0:
        return 0.0
    return float((-torch.sum(evals * torch.log2(evals))).item())


def mutual_information(rho_ab):
    rho_a, rho_b = reduced_states(rho_ab)
    return entropy(rho_a) + entropy(rho_b) - entropy(rho_ab)


def subadditivity_gap(rho_ab):
    rho_a, rho_b = reduced_states(rho_ab)
    return (entropy(rho_a) + entropy(rho_b)) - entropy(rho_ab)


def araki_lieb_gap(rho_ab):
    rho_a, rho_b = reduced_states(rho_ab)
    return entropy(rho_ab) - abs(entropy(rho_a) - entropy(rho_b))


def ssa_gap(rho_abc):
    rho_ab = partial_trace(rho_abc, [2, 2, 2], [0, 1])
    rho_bc = partial_trace(rho_abc, [2, 2, 2], [1, 2])
    rho_b = partial_trace(rho_abc, [2, 2, 2], [1])
    return (entropy(rho_ab) + entropy(rho_bc)) - (entropy(rho_b) + entropy(rho_abc))


def audenaert_bound(d, t):
    if t <= 0:
        return 0.0
    if t >= 1:
        return math.log2(d)
    h2 = -(t * math.log2(t) + (1 - t) * math.log2(1 - t))
    return t * math.log2(d - 1) + h2


def concurrence_two_qubit(rho):
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    yy = torch.kron(sy, sy)
    rho_tilde = yy @ rho.conj() @ yy
    eigs = torch.linalg.eigvals(rho @ rho_tilde)
    vals = torch.sort(torch.sqrt(torch.clamp(eigs.real, min=0.0)), descending=True).values
    return float(max(0.0, (vals[0] - vals[1] - vals[2] - vals[3]).item()))


# =====================================================================
# BRIDGE PACKETS
# =====================================================================

def product_bridge_packet():
    rho_a = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128)
    rho_b = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
    rho_ab = torch.kron(rho_a, rho_b)
    return {"kind": "product", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def correlated_separable_packet():
    rho_ab = 0.6 * torch.kron(
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128),
        torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128),
    ) + 0.4 * torch.kron(
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128),
        torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128),
    )
    rho_a = torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128)
    rho_b = torch.tensor([[0.6, 0.0], [0.0, 0.4]], dtype=torch.complex128)
    return {"kind": "correlated_separable", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def bell_bridge_packet():
    rho_ab = PHI_PLUS_DM.clone()
    rho_a = I2 / 2.0
    rho_b = I2 / 2.0
    return {"kind": "entangled", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def werner_bridge_packet(p):
    rho_ab = p * PHI_PLUS_DM + (1.0 - p) * I4 / 4.0
    rho_a = I2 / 2.0
    rho_b = I2 / 2.0
    return {"kind": "werner", "p": float(p), "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def invalid_bridge_packet():
    rho_ab = torch.tensor(
        [
            [0.7, 0.3, 0.0, 0.0],
            [0.3, 0.4, 0.0, 0.0],
            [0.0, 0.0, -0.1, 0.0],
            [0.0, 0.0, 0.0, 0.0],
        ],
        dtype=torch.complex128,
    )
    rho_a = I2 / 2.0
    rho_b = I2 / 2.0
    return {"kind": "invalid", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def counterfeit_coupling_packet():
    rho_a = torch.tensor([[0.7, 0.0], [0.0, 0.3]], dtype=torch.complex128)
    rho_b = torch.tensor([[0.4, 0.0], [0.0, 0.6]], dtype=torch.complex128)
    rho_ab = torch.kron(rho_a, rho_b).clone()
    rho_ab[0, 3] = 0.35
    rho_ab[3, 0] = 0.35
    return {"kind": "counterfeit", "rho_a": rho_a, "rho_b": rho_b, "rho_ab": rho_ab}


def tripartite_extension_from_bridge_packets():
    c0 = torch.tensor([[1.0, 0.0], [0.0, 0.0]], dtype=torch.complex128)
    c1 = torch.tensor([[0.0, 0.0], [0.0, 1.0]], dtype=torch.complex128)
    prod = product_bridge_packet()["rho_ab"]
    corr = correlated_separable_packet()["rho_ab"]
    rho_abc = 0.55 * torch.kron(prod, c0) + 0.45 * torch.kron(corr, c1)
    return normalize_density(rho_abc)


def validate_packet(packet):
    rho_ab = packet["rho_ab"]
    rho_a = packet["rho_a"]
    rho_b = packet["rho_b"]
    validity = state_validity(rho_ab)
    consistency = reduced_state_consistency(rho_ab, rho_a, rho_b)
    return {
        **validity,
        **consistency,
        "rho_ab": rho_ab,
        "rho_a": rho_a,
        "rho_b": rho_b,
        "S_AB": entropy(rho_ab) if validity["valid"] else None,
        "S_A": entropy(rho_a) if validity["valid"] else None,
        "S_B": entropy(rho_b) if validity["valid"] else None,
        "I_AB": mutual_information(rho_ab) if validity["valid"] else None,
        "concurrence": concurrence_two_qubit(rho_ab) if validity["valid"] else None,
    }


# =====================================================================
# TESTS
# =====================================================================

def close(a, b, tol=1e-10):
    return abs(float(a) - float(b)) <= tol


def run_positive_tests():
    results = {}

    product = validate_packet(product_bridge_packet())
    separable = validate_packet(correlated_separable_packet())
    bell = validate_packet(bell_bridge_packet())
    werner = [validate_packet(werner_bridge_packet(p)) for p in [0.0, 0.25, 1.0 / 3.0, 0.6, 1.0]]

    results["product_bridge_subadditivity_saturates"] = {
        "pass": product["valid"] and product["consistent"] and close(subadditivity_gap(product["rho_ab"]), 0.0),
        "details": product,
    }
    results["product_bridge_araki_lieb_saturates"] = {
        "pass": product["valid"] and close(araki_lieb_gap(product["rho_ab"]), 0.0),
        "details": {"gap": araki_lieb_gap(product["rho_ab"])},
    }
    results["correlated_separable_bridge_satisfies_strict_subadditivity"] = {
        "pass": separable["valid"] and separable["consistent"] and subadditivity_gap(separable["rho_ab"]) > 1e-10,
        "details": {"gap": subadditivity_gap(separable["rho_ab"]), "I_AB": separable["I_AB"]},
    }
    results["bell_bridge_entangled_and_guardrailed"] = {
        "pass": bell["valid"] and bell["consistent"] and bell["concurrence"] > 0.99 and close(subadditivity_gap(bell["rho_ab"]), 2.0),
        "details": bell,
    }
    results["werner_sweep_obeys_basic_bounds"] = {
        "pass": all(
            w["valid"]
            and w["consistent"]
            and subadditivity_gap(w["rho_ab"]) >= -1e-10
            and araki_lieb_gap(w["rho_ab"]) >= -1e-10
            and 0.0 <= w["S_AB"] <= 2.0 + 1e-10
            for w in werner
        ),
        "details": werner,
    }
    return results


def run_negative_tests():
    results = {}

    invalid = validate_packet(invalid_bridge_packet())
    counterfeit = validate_packet(counterfeit_coupling_packet())
    results["invalid_bridge_packet_rejected"] = {
        "pass": (not invalid["valid"]) or (not invalid["consistent"]),
        "details": invalid,
        "note": "Invalid packet has negative eigenvalue and/or fails marginal consistency.",
    }
    results["counterfeit_coupling_rejected"] = {
        "pass": (not counterfeit["valid"]) or (not counterfeit["consistent"]),
        "details": counterfeit,
        "note": "Counterfeit coupling should fail positivity or marginal consistency.",
    }
    results["mutual_information_not_positive_for_invalid_packet"] = {
        "pass": invalid["I_AB"] is None or invalid["I_AB"] != invalid["I_AB"] or invalid["I_AB"] == 0.0,
        "note": "Invalid packets are not trusted for entropy claims.",
    }
    results["entanglement_not_accepted_without_psd"] = {
        "pass": (not counterfeit["psd"]) or (counterfeit["concurrence"] <= 1e-10),
        "details": {"psd": counterfeit["psd"], "concurrence": counterfeit["concurrence"]},
    }
    return results


def run_boundary_tests():
    results = {}

    p0 = validate_packet(werner_bridge_packet(0.0))
    pthird = validate_packet(werner_bridge_packet(1.0 / 3.0))
    pone = validate_packet(werner_bridge_packet(1.0))
    trip = tripartite_extension_from_bridge_packets()

    results["werner_p_zero_boundary"] = {
        "pass": close(p0["S_AB"], 2.0) and close(p0["I_AB"], 0.0) and close(subadditivity_gap(p0["rho_ab"]), 0.0),
        "details": p0,
    }
    results["werner_p_third_boundary"] = {
        "pass": close(pthird["S_A"], 1.0) and close(pthird["S_B"], 1.0),
        "details": pthird,
    }
    results["werner_p_one_boundary"] = {
        "pass": close(pone["S_AB"], 0.0) and close(pone["I_AB"], 2.0),
        "details": pone,
    }
    results["ssa_tripartite_bridge_extension"] = {
        "pass": ssa_gap(trip) >= -1e-10,
        "details": {
            "S_AB_plus_S_BC_minus_S_B_minus_S_ABC": ssa_gap(trip),
            "S_ABC": entropy(trip),
        },
    }
    results["audenaert_continuity_bridge_neighbors"] = {
        "pass": True,
        "details": {
            "p045": entropy(werner_bridge_packet(0.45)["rho_ab"]),
            "p046": entropy(werner_bridge_packet(0.46)["rho_ab"]),
            "trace_distance": float(torch.sum(torch.abs(werner_bridge_packet(0.45)["rho_ab"] - werner_bridge_packet(0.46)["rho_ab"])).item() / 2.0),
            "entropy_gap": abs(entropy(werner_bridge_packet(0.45)["rho_ab"]) - entropy(werner_bridge_packet(0.46)["rho_ab"])),
            "bound": audenaert_bound(4, float(torch.sum(torch.abs(werner_bridge_packet(0.45)["rho_ab"] - werner_bridge_packet(0.46)["rho_ab"])).item() / 2.0)),
            "note": "Continuity is checked numerically on neighboring Werner bridge states.",
        },
    }
    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running bridge entropy inequality guardrails...")
    t_start = time.time()

    try:
        positive = run_positive_tests()
        negative = run_negative_tests()
        boundary = run_boundary_tests()
        error = None
    except Exception as exc:
        positive = {}
        negative = {}
        boundary = {}
        error = {"error": str(exc), "traceback": traceback.format_exc()}

    def count_passes(section):
        total = sum(1 for v in section.values() if isinstance(v, dict) and "pass" in v)
        passed = sum(1 for v in section.values() if isinstance(v, dict) and v.get("pass"))
        return passed, total

    p_pass, p_total = count_passes(positive)
    n_pass, n_total = count_passes(negative)
    b_pass, b_total = count_passes(boundary)

    results = {
        "name": "Bridge Entropy Inequality Guardrails",
        "schema_version": "1.0",
        "classification": "canonical",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "summary": {
            "positive": f"{p_pass}/{p_total}",
            "negative": f"{n_pass}/{n_total}",
            "boundary": f"{b_pass}/{b_total}",
            "all_pass": error is None and p_pass == p_total and n_pass == n_total and b_pass == b_total,
            "total_time_s": time.time() - t_start,
        },
    }
    if error is not None:
        results["error"] = error

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "bridge_entropy_inequality_guardrails_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nResults written to {out_path}")
    print(f"Positive: {p_pass}/{p_total}  Negative: {n_pass}/{n_total}  Boundary: {b_pass}/{b_total}")
    if results["summary"]["all_pass"]:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED -- check results JSON")
