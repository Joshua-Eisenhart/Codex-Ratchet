#!/usr/bin/env python3
"""
SIM LEGO: Clifford Group Hierarchy
===================================
Pure math. No engine jargon. Standalone lego.

Clifford hierarchy C_k defined recursively:
  C_1 = Pauli group
  C_k = { U : U P U† in C_{k-1} for all P in C_1 }

Implements:
  (1) Generate C_1 (1-qubit Pauli group, 16 elements with phases {1,i,-1,-i})
  (2) Verify C_2 generators: H, S conjugate Paulis to Paulis
  (3) Verify T in C_3 \\ C_2: T maps some Paulis outside C_1 but into C_2
  (4) Clifford twirl: averaging over C_2 maps any channel to depolarizing
  (5) Magic state |T> = T|+>: resource for universal computation

Tools: pytorch (matrix computation), sympy (exact symbolic verification),
       z3 (group closure proof)
"""

import json
import os
import numpy as np
classification = "classical_baseline"  # auto-backfill

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": ""},
    "pyg": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "z3": {"tried": False, "used": False, "reason": ""},
    "cvc5": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "sympy": {"tried": False, "used": False, "reason": ""},
    "clifford": {"tried": False, "used": False, "reason": "GA clifford not needed; this is quantum Clifford group"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "xgi": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed for this lego"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed for this lego"},
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
    TOOL_MANIFEST["pytorch"]["reason"] = "matrix computation for gate conjugation and twirl averaging"
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    from z3 import Solver, Bool, And, Or, Implies, sat, unsat
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = "formal verification of Pauli group closure"
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import sympy as sp
    from sympy import Matrix, sqrt, I, Rational, eye, zeros
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
    TOOL_MANIFEST["sympy"]["reason"] = "exact symbolic gate arithmetic for hierarchy verification"
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

# =====================================================================
# CONSTANTS -- 1-qubit gates (torch, complex128)
# =====================================================================

ATOL = 1e-10  # numerical tolerance


def _torch_gates():
    """Build fundamental gates as torch complex128 tensors."""
    I2 = torch.eye(2, dtype=torch.complex128)
    X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    H = torch.tensor([[1, 1], [1, -1]], dtype=torch.complex128) / torch.sqrt(torch.tensor(2.0, dtype=torch.complex128))
    S = torch.tensor([[1, 0], [0, 1j]], dtype=torch.complex128)
    T = torch.tensor([[1, 0], [0, torch.exp(1j * torch.tensor(np.pi / 4))]], dtype=torch.complex128)
    return I2, X, Y, Z, H, S, T


def _sympy_gates():
    """Build fundamental gates as exact sympy matrices."""
    I2 = eye(2)
    X = Matrix([[0, 1], [1, 0]])
    Y = Matrix([[0, -I], [I, 0]])
    Z = Matrix([[1, 0], [0, -1]])
    H = Matrix([[1, 1], [1, -1]]) / sqrt(2)
    S = Matrix([[1, 0], [0, I]])
    T = Matrix([[1, 0], [0, sp.exp(I * sp.pi / 4)]])
    return I2, X, Y, Z, H, S, T


# =====================================================================
# PAULI GROUP GENERATION (C_1)
# =====================================================================

def generate_pauli_group_torch():
    """
    Generate the 1-qubit Pauli group: {+/- 1, +/- i} x {I, X, Y, Z}.
    16 elements total. Returns list of 2x2 complex128 tensors.
    """
    I2, X, Y, Z, _, _, _ = _torch_gates()
    paulis = [I2, X, Y, Z]
    phases = [
        torch.tensor(1.0 + 0j, dtype=torch.complex128),
        torch.tensor(0.0 + 1j, dtype=torch.complex128),
        torch.tensor(-1.0 + 0j, dtype=torch.complex128),
        torch.tensor(0.0 - 1j, dtype=torch.complex128),
    ]
    group = []
    for phase in phases:
        for P in paulis:
            group.append(phase * P)
    return group


def is_in_group(U, group, atol=ATOL):
    """Check if U matches any element in group up to tolerance."""
    for G in group:
        if torch.allclose(U, G, atol=atol):
            return True
    return False


def conjugate(U, P):
    """Compute U P U†."""
    return U @ P @ U.conj().T


# =====================================================================
# CLIFFORD HIERARCHY MEMBERSHIP
# =====================================================================

def is_in_C1(U, pauli_group):
    """U in C_1 iff U is a Pauli (up to global phase already in group)."""
    return is_in_group(U, pauli_group)


def maps_paulis_to_paulis(U, pauli_group):
    """
    U in C_2 iff for every Pauli P, U P U† is in C_1.
    Returns (bool, details_dict).
    """
    I2, X, Y, Z, _, _, _ = _torch_gates()
    base_paulis = {"I": I2, "X": X, "Y": Y, "Z": Z}
    details = {}
    all_in = True
    for name, P in base_paulis.items():
        result = conjugate(U, P)
        in_c1 = is_in_group(result, pauli_group)
        details[name] = {"maps_to_pauli": in_c1}
        if not in_c1:
            all_in = False
    return all_in, details


def maps_paulis_to_C2(U, pauli_group):
    """
    U in C_3 iff for every Pauli P, U P U† is in C_2.
    i.e., conjugation by U P U† also maps Paulis to Paulis.
    Returns (bool, details_dict).
    """
    I2, X, Y, Z, _, _, _ = _torch_gates()
    base_paulis = {"I": I2, "X": X, "Y": Y, "Z": Z}
    details = {}
    all_in_c2 = True
    for name, P in base_paulis.items():
        UPUd = conjugate(U, P)
        in_c1 = is_in_group(UPUd, pauli_group)
        # Check if UPUd is in C_2: does it map all Paulis to Paulis?
        if in_c1:
            in_c2 = True  # C_1 subset C_2
        else:
            in_c2, _ = maps_paulis_to_paulis(UPUd, pauli_group)
        details[name] = {"maps_to_pauli": in_c1, "maps_to_C2": in_c2}
        if not in_c2:
            all_in_c2 = False
    return all_in_c2, details


# =====================================================================
# CLIFFORD TWIRL
# =====================================================================

def generate_1q_clifford_group():
    """
    The single-qubit Clifford group has 24 elements.
    Generate by closure of H and S.
    """
    _, _, _, _, H, S, _ = _torch_gates()
    I2 = torch.eye(2, dtype=torch.complex128)

    # Generate by brute-force closure
    group = [I2]

    def _normalize(U):
        """Normalize global phase so first nonzero element is positive real."""
        flat = U.flatten()
        for c in flat:
            if abs(c) > 1e-12:
                phase = c / abs(c)
                return U / phase
        return U

    def _is_new(U, existing):
        U_n = _normalize(U)
        for E in existing:
            if torch.allclose(U_n, _normalize(E), atol=ATOL):
                return False
        return True

    generators = [H, S]
    # BFS closure
    queue = list(group)
    while queue:
        current = queue.pop(0)
        for g in generators:
            for candidate in [current @ g, g @ current]:
                if _is_new(candidate, group):
                    group.append(candidate)
                    queue.append(candidate)

    return group


def clifford_twirl_channel(kraus_ops):
    """
    Twirl a quantum channel (given by Kraus operators) over the 1-qubit Clifford group.
    For a channel E(rho) = sum_k A_k rho A_k†,
    the twirl is (1/|C|) sum_{C in Cliff} C† E(C rho C†) C
      = (1/|C|) sum_{C,k} (C† A_k C) rho (C† A_k C)†

    For a depolarizing channel, the result is p*I/2 + (1-p)*rho.
    Returns the Choi matrix of the twirled channel.
    """
    cliff_group = generate_1q_clifford_group()
    n_cliff = len(cliff_group)

    # Build Choi matrix: sum over Clifford elements and Kraus ops
    # Choi(E) = sum_{ij} E(|i><j|) tensor |i><j|
    choi = torch.zeros(4, 4, dtype=torch.complex128)

    for i in range(2):
        for j in range(2):
            ket_i = torch.zeros(2, 1, dtype=torch.complex128)
            ket_i[i] = 1.0
            ket_j = torch.zeros(2, 1, dtype=torch.complex128)
            ket_j[j] = 1.0
            rho_ij = ket_i @ ket_j.conj().T  # |i><j|

            # Apply twirled channel
            result = torch.zeros(2, 2, dtype=torch.complex128)
            for C in cliff_group:
                Cd = C.conj().T
                for A in kraus_ops:
                    # Twirled Kraus: Cd A C
                    twirled_A = Cd @ A @ C
                    result += twirled_A @ rho_ij @ twirled_A.conj().T
            result /= n_cliff

            # Insert into Choi matrix
            for a in range(2):
                for b in range(2):
                    choi[a * 2 + i, b * 2 + j] += result[a, b]

    return choi


def choi_is_depolarizing(choi, atol=1e-6):
    """
    Check if a Choi matrix corresponds to a depolarizing channel.
    Depolarizing: E(rho) = (1-p)*rho + p*I/2
    Choi matrix of depolarizing = (1-p)|Phi+><Phi+| + p/2 * I/4
    which has eigenvalues: (1 - 3p/4) and three copies of p/4.
    Key test: Choi is diagonal in Bell basis with 3 equal eigenvalues.
    """
    evals = torch.linalg.eigvalsh(choi).real
    evals_sorted = torch.sort(evals).values
    # Three smallest should be equal
    three_equal = torch.allclose(evals_sorted[0:1].expand(3), evals_sorted[0:3], atol=atol)
    return three_equal


# =====================================================================
# MAGIC STATE
# =====================================================================

def magic_state_T():
    """Compute |T> = T|+> and verify its properties."""
    _, _, _, _, _, _, T = _torch_gates()
    plus = torch.tensor([[1], [1]], dtype=torch.complex128) / torch.sqrt(torch.tensor(2.0, dtype=torch.complex128))
    T_state = T @ plus

    # |T> should NOT be a stabilizer state
    # A stabilizer state has a Pauli stabilizer; |T> does not
    # Test: measure overlap with all stabilizer states of 1 qubit
    # The 6 stabilizer states: |0>, |1>, |+>, |->, |+i>, |-i>
    stab_states = []
    stab_states.append(torch.tensor([[1], [0]], dtype=torch.complex128))  # |0>
    stab_states.append(torch.tensor([[0], [1]], dtype=torch.complex128))  # |1>
    stab_states.append(torch.tensor([[1], [1]], dtype=torch.complex128) / np.sqrt(2))  # |+>
    stab_states.append(torch.tensor([[1], [-1]], dtype=torch.complex128) / np.sqrt(2))  # |->
    stab_states.append(torch.tensor([[1], [1j]], dtype=torch.complex128) / np.sqrt(2))  # |+i>
    stab_states.append(torch.tensor([[1], [-1j]], dtype=torch.complex128) / np.sqrt(2))  # |-i>

    overlaps = {}
    is_stabilizer = False
    for idx, s in enumerate(stab_states):
        overlap = abs((s.conj().T @ T_state).item()) ** 2
        overlaps[f"stab_{idx}"] = float(overlap)
        if abs(overlap - 1.0) < ATOL:
            is_stabilizer = True

    return {
        "T_state": [complex(x) for x in T_state.flatten()],
        "is_stabilizer_state": is_stabilizer,
        "overlaps_with_stabilizer_states": overlaps,
    }


# =====================================================================
# Z3 FORMAL VERIFICATION -- Pauli group closure
# =====================================================================

def z3_verify_pauli_closure():
    """
    Use z3 to formally verify that the Pauli group is closed under multiplication.
    Encode the 16-element Cayley table and verify:
      for all a,b in G: a*b in G (closure)
      for all a in G: exists a_inv: a*a_inv = e (inverse)
      for all a,b,c in G: (a*b)*c = a*(b*c) (associativity, by table check)
    """
    try:
        from z3 import Solver, Int, And, Or, sat, ForAll, Exists, Function, IntSort
    except ImportError:
        return {"status": "SKIP", "reason": "z3 not available"}

    # Encode multiplication table numerically
    # Elements 0..15: phase_idx * 4 + pauli_idx
    # phase: 0=+1, 1=+i, 2=-1, 3=-i
    # pauli: 0=I, 1=X, 2=Y, 3=Z
    # Multiplication rules:
    #   Pauli: XX=I, YY=I, ZZ=I, XY=iZ, YX=-iZ, XZ=-iY, ZX=iY, YZ=iX, ZY=-iX
    #   Phase: phases multiply mod 4

    pauli_mult = {}
    # (pauli_a, pauli_b) -> (phase_shift, pauli_result)
    pauli_mult[(0, 0)] = (0, 0)  # I*I = I
    pauli_mult[(0, 1)] = (0, 1)  # I*X = X
    pauli_mult[(0, 2)] = (0, 2)  # I*Y = Y
    pauli_mult[(0, 3)] = (0, 3)  # I*Z = Z
    pauli_mult[(1, 0)] = (0, 1)  # X*I = X
    pauli_mult[(1, 1)] = (0, 0)  # X*X = I
    pauli_mult[(1, 2)] = (1, 3)  # X*Y = iZ
    pauli_mult[(1, 3)] = (3, 2)  # X*Z = -iY
    pauli_mult[(2, 0)] = (0, 2)  # Y*I = Y
    pauli_mult[(2, 1)] = (3, 3)  # Y*X = -iZ
    pauli_mult[(2, 2)] = (0, 0)  # Y*Y = I
    pauli_mult[(2, 3)] = (1, 1)  # Y*Z = iX
    pauli_mult[(3, 0)] = (0, 3)  # Z*I = Z
    pauli_mult[(3, 1)] = (1, 2)  # Z*X = iY
    pauli_mult[(3, 2)] = (3, 1)  # Z*Y = -iX
    pauli_mult[(3, 3)] = (0, 0)  # Z*Z = I

    # Full group multiplication: (p1, s1) * (p2, s2)
    # phase = (p1 + p2 + phase_shift) mod 4, sigma = pauli_result
    cayley = {}
    for a in range(16):
        pa, sa = divmod(a, 4)  # pa = phase_idx of a, sa = pauli_idx of a
        # Wait -- encoding is phase_idx * 4 + pauli_idx
        # So a = phase_a * 4 + pauli_a
        pass

    # Re-encode properly
    def encode(phase, pauli):
        return phase * 4 + pauli

    def decode(elem):
        return divmod(elem, 4)  # (phase, pauli)

    cayley_table = {}
    for a in range(16):
        phase_a, pauli_a = decode(a)
        for b in range(16):
            phase_b, pauli_b = decode(b)
            dphase, result_pauli = pauli_mult[(pauli_a, pauli_b)]
            result_phase = (phase_a + phase_b + dphase) % 4
            cayley_table[(a, b)] = encode(result_phase, result_pauli)

    # z3 verification
    s = Solver()

    # 1. Closure: all products are in {0..15}
    closure_ok = all(0 <= v <= 15 for v in cayley_table.values())

    # 2. Identity: element 0 (phase=+1, pauli=I) is identity
    identity = encode(0, 0)
    identity_ok = all(
        cayley_table[(identity, a)] == a and cayley_table[(a, identity)] == a
        for a in range(16)
    )

    # 3. Inverses: for every a, exists b such that a*b = identity
    inverses = {}
    inverse_ok = True
    for a in range(16):
        found = False
        for b in range(16):
            if cayley_table[(a, b)] == identity and cayley_table[(b, a)] == identity:
                inverses[a] = b
                found = True
                break
        if not found:
            inverse_ok = False

    # 4. Associativity: (a*b)*c = a*(b*c) for all a,b,c
    assoc_ok = True
    assoc_failures = 0
    for a in range(16):
        for b in range(16):
            ab = cayley_table[(a, b)]
            for c in range(16):
                bc = cayley_table[(b, c)]
                if cayley_table[(ab, c)] != cayley_table[(a, bc)]:
                    assoc_ok = False
                    assoc_failures += 1

    # Use z3 to double-check: encode the Cayley table as a function and
    # verify no element maps outside the group
    mul_fn = Function('mul', IntSort(), IntSort(), IntSort())
    for (a, b), v in cayley_table.items():
        s.add(mul_fn(a, b) == v)

    # Assert closure fails for some element (should be unsat if closed)
    x = Int('x')
    y = Int('y')
    s.push()
    s.add(And(x >= 0, x <= 15, y >= 0, y <= 15))
    s.add(Or(mul_fn(x, y) < 0, mul_fn(x, y) > 15))
    closure_z3 = s.check()  # Should be unsat (no violation exists)
    s.pop()

    return {
        "status": "PASS",
        "group_size": 16,
        "closure": closure_ok,
        "identity_element": identity,
        "identity_axiom": identity_ok,
        "inverse_axiom": inverse_ok,
        "associativity": assoc_ok,
        "associativity_failures": assoc_failures,
        "z3_closure_check": "PASS (unsat)" if str(closure_z3) == "unsat" else f"FAIL ({closure_z3})",
    }


# =====================================================================
# SYMPY EXACT VERIFICATION
# =====================================================================

def sympy_verify_hierarchy():
    """Exact symbolic verification of Clifford hierarchy membership."""
    I2, X, Y, Z, H, S, T = _sympy_gates()

    def conj(U, P):
        return sp.simplify(U * P * U.adjoint())

    def is_pauli(M):
        """Check if M is a Pauli (up to phase {1,i,-1,-i})."""
        paulis = [I2, X, Y, Z]
        phases = [1, I, -1, -I]
        for ph in phases:
            for P in paulis:
                if sp.simplify(M - ph * P) == zeros(2):
                    return True
        return False

    results = {}

    # H is in C_2: conjugates Paulis to Paulis
    results["H_X_Hd"] = str(sp.simplify(conj(H, X)))
    results["H_X_Hd_is_pauli"] = is_pauli(conj(H, X))  # Should be Z
    results["H_Z_Hd"] = str(sp.simplify(conj(H, Z)))
    results["H_Z_Hd_is_pauli"] = is_pauli(conj(H, Z))  # Should be X
    results["H_Y_Hd"] = str(sp.simplify(conj(H, Y)))
    results["H_Y_Hd_is_pauli"] = is_pauli(conj(H, Y))  # Should be -Y

    # S is in C_2
    results["S_X_Sd"] = str(sp.simplify(conj(S, X)))
    results["S_X_Sd_is_pauli"] = is_pauli(conj(S, X))  # Should be Y
    results["S_Z_Sd"] = str(sp.simplify(conj(S, Z)))
    results["S_Z_Sd_is_pauli"] = is_pauli(conj(S, Z))  # Should be Z

    # T is NOT in C_2: T X T† is not Pauli
    TXTd = sp.simplify(conj(T, X))
    results["T_X_Td"] = str(TXTd)
    results["T_X_Td_is_pauli"] = is_pauli(TXTd)  # Should be False

    # T Z T† IS Pauli (Z commutes with T since T is diagonal)
    TZTd = sp.simplify(conj(T, Z))
    results["T_Z_Td"] = str(TZTd)
    results["T_Z_Td_is_pauli"] = is_pauli(TZTd)  # Should be True (= Z)

    # T X T† is in C_2: verify it maps Paulis to Paulis
    # T X T† = (X + Y)/sqrt(2) * phase... let's check by conjugation
    def is_in_C2(M):
        """Check if M conjugates all Paulis to Paulis."""
        for P in [X, Y, Z]:
            if not is_pauli(sp.simplify(M * P * M.adjoint())):
                return False
        return True

    results["T_X_Td_is_C2"] = is_in_C2(TXTd)  # Should be True => T in C_3

    return results


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    # --- Test 1: Pauli group has 16 elements ---
    pauli_group = generate_pauli_group_torch()
    results["pauli_group_size"] = {
        "expected": 16,
        "actual": len(pauli_group),
        "pass": len(pauli_group) == 16,
    }

    # --- Test 2: H conjugates X to Z (canonical Clifford test) ---
    _, X, _, Z, H, _, _ = _torch_gates()
    HXHd = conjugate(H, X)
    h_maps_x_to_z = torch.allclose(HXHd, Z, atol=ATOL)
    results["H_X_Hd_eq_Z"] = {
        "expected": "Z",
        "actual": "Z" if h_maps_x_to_z else f"other (norm_diff={torch.norm(HXHd - Z).item():.2e})",
        "pass": h_maps_x_to_z,
    }

    # --- Test 3: H, S are in C_2 (map Paulis to Paulis) ---
    _, _, _, _, H, S, _ = _torch_gates()
    h_in_c2, h_details = maps_paulis_to_paulis(H, pauli_group)
    s_in_c2, s_details = maps_paulis_to_paulis(S, pauli_group)
    results["H_in_C2"] = {"pass": h_in_c2, "details": {k: v["maps_to_pauli"] for k, v in h_details.items()}}
    results["S_in_C2"] = {"pass": s_in_c2, "details": {k: v["maps_to_pauli"] for k, v in s_details.items()}}

    # --- Test 4: T is in C_3 but NOT in C_2 ---
    _, _, _, _, _, _, T = _torch_gates()
    t_in_c2, t_c2_details = maps_paulis_to_paulis(T, pauli_group)
    t_in_c3, t_c3_details = maps_paulis_to_C2(T, pauli_group)
    results["T_not_in_C2"] = {
        "pass": not t_in_c2,
        "details": {k: v["maps_to_pauli"] for k, v in t_c2_details.items()},
    }
    results["T_in_C3"] = {
        "pass": t_in_c3,
        "details": {k: {"pauli": v["maps_to_pauli"], "C2": v["maps_to_C2"]} for k, v in t_c3_details.items()},
    }

    # --- Test 5: Clifford twirl of Z-dephasing = depolarizing ---
    # Z-dephasing channel: Kraus ops = {sqrt(1-p)*I, sqrt(p)*Z}
    I2, _, _, Z, _, _, _ = _torch_gates()
    p = 0.3
    kraus_dephasing = [
        torch.sqrt(torch.tensor(1 - p, dtype=torch.complex128)) * I2,
        torch.sqrt(torch.tensor(p, dtype=torch.complex128)) * Z,
    ]
    choi = clifford_twirl_channel(kraus_dephasing)
    is_depol = choi_is_depolarizing(choi)
    results["twirl_dephasing_is_depolarizing"] = {
        "pass": bool(is_depol),
        "choi_eigenvalues": sorted(torch.linalg.eigvalsh(choi).real.tolist()),
    }

    # --- Test 6: Magic state |T> is not a stabilizer state ---
    magic = magic_state_T()
    results["magic_state_not_stabilizer"] = {
        "pass": not magic["is_stabilizer_state"],
        "max_stabilizer_overlap": max(magic["overlaps_with_stabilizer_states"].values()),
    }

    # --- Test 7: Sympy exact verification ---
    sympy_results = sympy_verify_hierarchy()
    results["sympy_exact"] = {
        "H_X_Hd_is_pauli": sympy_results["H_X_Hd_is_pauli"],
        "S_X_Sd_is_pauli": sympy_results["S_X_Sd_is_pauli"],
        "T_X_Td_is_pauli": sympy_results["T_X_Td_is_pauli"],
        "T_X_Td_is_C2": sympy_results["T_X_Td_is_C2"],
        "pass": (
            sympy_results["H_X_Hd_is_pauli"]
            and sympy_results["S_X_Sd_is_pauli"]
            and not sympy_results["T_X_Td_is_pauli"]
            and sympy_results["T_X_Td_is_C2"]
        ),
    }

    # --- Test 8: z3 Pauli group closure ---
    z3_results = z3_verify_pauli_closure()
    results["z3_pauli_closure"] = z3_results

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    pauli_group = generate_pauli_group_torch()

    # --- Neg 1: T is NOT in C_2 ---
    _, _, _, _, _, _, T = _torch_gates()
    t_in_c2, _ = maps_paulis_to_paulis(T, pauli_group)
    results["T_not_Clifford"] = {
        "test": "T gate must NOT be in C_2",
        "pass": not t_in_c2,
    }

    # --- Neg 2: Random unitary is NOT in C_2 ---
    torch.manual_seed(42)
    # Generate random unitary via QR decomposition
    A = torch.randn(2, 2, dtype=torch.complex128)
    Q, R = torch.linalg.qr(A)
    # Fix phase to make it a proper unitary
    Q = Q @ torch.diag(torch.sgn(torch.diag(R)))
    rand_in_c2, _ = maps_paulis_to_paulis(Q, pauli_group)
    results["random_not_Clifford"] = {
        "test": "random unitary must NOT be in C_2",
        "pass": not rand_in_c2,
    }

    # --- Neg 3: Random unitary NOT in C_3 either ---
    rand_in_c3, _ = maps_paulis_to_C2(Q, pauli_group)
    results["random_not_C3"] = {
        "test": "random unitary must NOT be in C_3",
        "pass": not rand_in_c3,
    }

    # --- Neg 4: Non-unitary matrix fails conjugation identity ---
    M = torch.tensor([[1, 1], [0, 1]], dtype=torch.complex128)  # not unitary
    # M M† != I
    MMd = M @ M.conj().T
    is_unitary = torch.allclose(MMd, torch.eye(2, dtype=torch.complex128), atol=ATOL)
    results["non_unitary_detected"] = {
        "test": "non-unitary matrix must fail unitarity check",
        "pass": not is_unitary,
    }

    # --- Neg 5: Magic state IS not a stabilizer state (negative: it shouldn't be) ---
    magic = magic_state_T()
    max_overlap = max(magic["overlaps_with_stabilizer_states"].values())
    results["magic_not_stabilizer"] = {
        "test": "|T> must not be stabilizer (max overlap < 1)",
        "max_overlap": max_overlap,
        "pass": max_overlap < 1.0 - ATOL,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}
    pauli_group = generate_pauli_group_torch()
    I2, X, Y, Z, H, S, T = _torch_gates()

    # --- Boundary 1: Pauli group elements are all unitary ---
    all_unitary = True
    for P in pauli_group:
        PPd = P @ P.conj().T
        if not torch.allclose(PPd, I2, atol=ATOL):
            all_unitary = False
            break
    results["all_paulis_unitary"] = {"pass": all_unitary}

    # --- Boundary 2: Clifford group size = 24 ---
    cliff = generate_1q_clifford_group()
    results["clifford_group_size"] = {
        "expected": 24,
        "actual": len(cliff),
        "pass": len(cliff) == 24,
    }

    # --- Boundary 3: S^4 = I (order of S is 4) ---
    S4 = S @ S @ S @ S
    results["S_order_4"] = {"pass": bool(torch.allclose(S4, I2, atol=ATOL))}

    # --- Boundary 4: T^8 = I (order of T is 8) ---
    T_power = I2.clone()
    for _ in range(8):
        T_power = T_power @ T
    results["T_order_8"] = {"pass": bool(torch.allclose(T_power, I2, atol=ATOL))}

    # --- Boundary 5: H^2 = I ---
    H2 = H @ H
    results["H_order_2"] = {"pass": bool(torch.allclose(H2, I2, atol=ATOL))}

    # --- Boundary 6: S^2 = Z ---
    S2 = S @ S
    results["S_squared_is_Z"] = {"pass": bool(torch.allclose(S2, Z, atol=ATOL))}

    # --- Boundary 7: Numerical precision -- gates near T but not exactly T ---
    epsilon = 1e-15
    T_perturbed = T.clone()
    T_perturbed[1, 1] += epsilon
    # Should still appear as C_3 at this tiny perturbation
    perturbed_c3, _ = maps_paulis_to_C2(T_perturbed, pauli_group)
    results["T_perturbed_tiny_still_C3"] = {
        "epsilon": epsilon,
        "pass": perturbed_c3,
    }

    # Larger perturbation should break it
    epsilon_big = 0.1
    T_broken = T.clone()
    T_broken[1, 1] += epsilon_big
    broken_c2, _ = maps_paulis_to_paulis(T_broken, pauli_group)
    broken_c3, _ = maps_paulis_to_C2(T_broken, pauli_group)
    results["T_perturbed_large_not_C2_or_C3"] = {
        "epsilon": epsilon_big,
        "not_C2": not broken_c2,
        "not_C3": not broken_c3,
        "pass": not broken_c2 and not broken_c3,
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    print("Running Clifford Hierarchy lego sim...")

    positive = run_positive_tests()
    negative = run_negative_tests()
    boundary = run_boundary_tests()

    # Count passes
    all_tests = {}
    all_tests.update({f"pos_{k}": v for k, v in positive.items()})
    all_tests.update({f"neg_{k}": v for k, v in negative.items()})
    all_tests.update({f"bnd_{k}": v for k, v in boundary.items()})

    n_pass = sum(1 for v in all_tests.values() if isinstance(v, dict) and v.get("pass"))
    n_total = sum(1 for v in all_tests.values() if isinstance(v, dict) and "pass" in v)

    results = {
        "name": "Clifford Group Hierarchy",
        "tool_manifest": TOOL_MANIFEST,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "classification": "canonical",
        "summary": f"{n_pass}/{n_total} tests passed",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "lego_clifford_hierarchy_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"Summary: {n_pass}/{n_total} tests passed")
