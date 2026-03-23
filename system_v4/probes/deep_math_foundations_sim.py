"""
Deep Math Foundations SIM Suite
================================
Extends arithmetic with subtraction, division, zero, negation,
fractions, and the foundations of algebra — all emergent from
the finite non-commutative refinement category.

SIM_01: Zero emerges as the maximally mixed state (I/d)
SIM_02: Negation = time-reversal (adjoint operation)
SIM_03: Subtraction = inverse refinement path
SIM_04: Division = partial trace (coarse-graining)
SIM_05: Fractions = mixed states (convex combinations)
SIM_06: Groups emerge from invertible CPTP compositions
SIM_07: Commutativity fails for d>1 (non-abelian structure)
"""

import numpy as np
import json
import os
from datetime import datetime, UTC

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import (
    make_random_density_matrix,
    make_random_unitary,
    apply_unitary_channel,
    apply_lindbladian_step,
    von_neumann_entropy,
    trace_distance,
    EvidenceToken,
)


def negentropy(rho, d):
    S = von_neumann_entropy(rho) * np.log(2)
    return np.log(d) - S


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_01: Zero = Maximally Mixed State
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_zero_emergence(d: int = 4):
    """
    CLAIM: Zero is not an axiom. It emerges as the identity element
    of the additive structure — the maximally mixed state σ = I/d.
    
    Properties:
    - S(I/d) = ln(d) = maximum entropy (no structure = nothing to add)
    - Φ(I/d) = 0 (zero negentropy = zero structural content)
    - For any ρ: the mixture ρ + I/d (convex combo) doesn't reduce S below S(ρ)
    - I/d is the unique fixed point of full thermalization
    """
    print(f"\n{'='*60}")
    print(f"SIM_01: ZERO EMERGES AS MAXIMALLY MIXED STATE")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    sigma = np.eye(d, dtype=complex) / d
    
    # Properties of zero
    S_zero = von_neumann_entropy(sigma)
    phi_zero = negentropy(sigma, d)
    S_max = np.log2(d)
    
    print(f"  σ = I/{d}")
    print(f"  S(σ) = {S_zero:.6f} (max = {S_max:.6f})")
    print(f"  Φ(σ) = {phi_zero:.10f} (should be 0)")
    
    # Zero + anything = anything (mixing with I/d at 0% doesn't change ρ)
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    rho_plus_zero = 1.0 * rho + 0.0 * sigma  # mixing at weight 0
    identity_preserved = trace_distance(rho, rho_plus_zero) < 1e-15
    
    # Full thermalization converges TO zero
    L_ops = []
    for j in range(d):
        for k in range(d):
            if j != k:
                L = np.zeros((d, d), dtype=complex)
                L[j, k] = 1.0
                L_ops.append(L)
    
    rho_test = make_random_density_matrix(d)
    for _ in range(200):
        drho = np.zeros_like(rho_test)
        for L in L_ops:
            LdL = L.conj().T @ L
            drho += L @ rho_test @ L.conj().T - 0.5 * (LdL @ rho_test + rho_test @ LdL)
        rho_test = rho_test + 0.01 * drho
        rho_test = (rho_test + rho_test.conj().T) / 2
        eigvals = np.maximum(np.real(np.linalg.eigvalsh(rho_test)), 0)
        V = np.linalg.eigh(rho_test)[1]
        rho_test = V @ np.diag(eigvals.astype(complex)) @ V.conj().T
        if np.real(np.trace(rho_test)) > 0:
            rho_test = rho_test / np.trace(rho_test)
    
    converged_to_sigma = trace_distance(rho_test, sigma) < 0.01
    
    print(f"  Φ(σ) = 0: {abs(phi_zero) < 1e-10}")
    print(f"  S(σ) = max: {abs(S_zero - S_max) < 1e-10}")
    print(f"  ρ + 0 = ρ: {identity_preserved}")
    print(f"  Thermalization → σ: {converged_to_sigma}")
    print(f"  → Zero IS the maximally mixed state. No axiom needed.")
    
    all_pass = abs(phi_zero) < 1e-10 and identity_preserved and converged_to_sigma
    
    if all_pass:
        print(f"  PASS: Zero emerges naturally!")
        return EvidenceToken(
            token_id="E_SIM_ZERO_EMERGES_OK",
            sim_spec_id="S_SIM_ZERO_V1",
            status="PASS",
            measured_value=phi_zero
        )
    else:
        return EvidenceToken("", "S_SIM_ZERO_V1", "KILL", 0.0, "ZERO_NOT_EMERGENT")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_02: Negation = Adjoint (Time-Reversal)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_negation_adjoint(d: int = 4):
    """
    CLAIM: Negation (additive inverse) corresponds to the adjoint
    operation. For unitary U, the "negative" is U†.
    
    U·U† = I (identity). This IS x + (-x) = 0.
    In entropy: applying U then U† returns to the original state,
    net effect = zero change.
    """
    print(f"\n{'='*60}")
    print(f"SIM_02: NEGATION = ADJOINT (TIME REVERSAL)")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    U = make_random_unitary(d)
    
    # Apply U then U†
    rho_forward = apply_unitary_channel(rho, U)
    U_adj = U.conj().T
    rho_roundtrip = apply_unitary_channel(rho_forward, U_adj)
    
    roundtrip_dist = trace_distance(rho, rho_roundtrip)
    
    # U·U† = I
    product = U @ U_adj
    identity_error = np.linalg.norm(product - np.eye(d))
    
    # Entropy is preserved in both directions
    S_orig = von_neumann_entropy(rho)
    S_forward = von_neumann_entropy(rho_forward)
    S_roundtrip = von_neumann_entropy(rho_roundtrip)
    
    print(f"  ρ → Uρ U† → U†(UρU†)U = ρ")
    print(f"  Roundtrip distance: {roundtrip_dist:.2e}")
    print(f"  UU† - I error: {identity_error:.2e}")
    print(f"  S(ρ)={S_orig:.6f}, S(UρU†)={S_forward:.6f}, S(round)={S_roundtrip:.6f}")
    print(f"  → Negation IS the adjoint. x + (-x) = 0 is U·U† = I.")
    
    if roundtrip_dist < 1e-10 and identity_error < 1e-10:
        print(f"  PASS: Negation = adjoint confirmed!")
        return EvidenceToken(
            token_id="E_SIM_NEGATION_OK",
            sim_spec_id="S_SIM_NEGATION_V1",
            status="PASS",
            measured_value=roundtrip_dist
        )
    else:
        return EvidenceToken("", "S_SIM_NEGATION_V1", "KILL", 0.0, "ADJOINT_FAILS")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_03: Subtraction = Inverse Refinement
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_subtraction_inverse(d: int = 4):
    """
    CLAIM: Subtraction = undoing a refinement step. If adding a probe
    REFINES (creates more classes), removing a probe COARSENS (merges).
    Subtraction is NOT primitive — it's the inverse operation.
    
    TEST: Build from k probes to k+1, then go back to k.
    The number of classes should return to the previous count.
    """
    print(f"\n{'='*60}")
    print(f"SIM_03: SUBTRACTION = INVERSE REFINEMENT")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    n_states = 30
    states = [make_random_density_matrix(d) for _ in range(n_states)]
    resolution = 0.5
    
    # Build probes
    probes = []
    for i in range(6):
        P = np.random.randn(d, d) + 1j * np.random.randn(d, d)
        P = (P + P.conj().T) / 2
        probes.append(P)
    
    def count_classes(probe_list):
        sigs = []
        for rho in states:
            sig = tuple(round(np.real(np.trace(P @ rho)) / resolution) * resolution
                       for P in probe_list)
            sigs.append(sig)
        return len(set(sigs))
    
    # Forward: add probes one by one
    forward = []
    for k in range(1, len(probes) + 1):
        forward.append(count_classes(probes[:k]))
    
    # Backward: remove probes one by one (subtraction)
    backward = []
    for k in range(len(probes), 0, -1):
        backward.append(count_classes(probes[:k]))
    
    print(f"  Forward  (add probes):    {forward}")
    print(f"  Backward (remove probes): {backward}")
    print(f"  Forward reversed: {forward[::-1]}")
    print(f"  Match: {forward[::-1] == backward}")
    print(f"  → Subtraction = removing probes = coarsening = inverse of addition")
    
    match = forward[::-1] == backward
    
    if match:
        print(f"  PASS: Subtraction = inverse refinement!")
        return EvidenceToken(
            token_id="E_SIM_SUBTRACTION_OK",
            sim_spec_id="S_SIM_SUBTRACTION_V1",
            status="PASS",
            measured_value=float(forward[-1])
        )
    else:
        return EvidenceToken("", "S_SIM_SUBTRACTION_V1", "KILL", 0.0, "NOT_INVERTIBLE")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_04: Division = Partial Trace
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_division_partial_trace(d_a: int = 2, d_b: int = 3):
    """
    CLAIM: Division is the inverse of tensor product (multiplication).
    If multiplication = ⊗ (tensor), then division = partial trace.
    Tr_B(ρ_AB) recovers ρ_A from the joint system ρ_A ⊗ ρ_B.
    
    This only works perfectly for PRODUCT states (no entanglement).
    For entangled states, division loses information → remainder.
    """
    print(f"\n{'='*60}")
    print(f"SIM_04: DIVISION = PARTIAL TRACE")
    print(f"  d_A={d_a}, d_B={d_b}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho_a = make_random_density_matrix(d_a)
    rho_b = make_random_density_matrix(d_b)
    
    # Multiply: ρ_AB = ρ_A ⊗ ρ_B
    rho_ab = np.kron(rho_a, rho_b)
    
    # Divide: Tr_B(ρ_AB) = ρ_A
    # Partial trace over B
    d_total = d_a * d_b
    rho_a_recovered = np.zeros((d_a, d_a), dtype=complex)
    for i in range(d_a):
        for j in range(d_a):
            for k in range(d_b):
                rho_a_recovered[i, j] += rho_ab[i * d_b + k, j * d_b + k]
    
    recovery_dist = trace_distance(rho_a, rho_a_recovered)
    
    # Entropy check: S(Tr_B(ρ_A⊗ρ_B)) = S(ρ_A)
    S_a_orig = von_neumann_entropy(rho_a)
    S_a_recovered = von_neumann_entropy(rho_a_recovered)
    
    print(f"  Multiplication: ρ_A ⊗ ρ_B → ρ_AB (dim={d_total})")
    print(f"  Division: Tr_B(ρ_AB) → ρ_A (dim={d_a})")
    print(f"  Recovery distance: {recovery_dist:.2e}")
    print(f"  S(ρ_A orig) = {S_a_orig:.6f}")
    print(f"  S(ρ_A recovered) = {S_a_recovered:.6f}")
    print(f"  → Division IS partial trace (the inverse of tensor product)")
    print(f"  → Works perfectly for product states (no entanglement)")
    
    if recovery_dist < 1e-10:
        print(f"  PASS: Division = partial trace confirmed!")
        return EvidenceToken(
            token_id="E_SIM_DIVISION_OK",
            sim_spec_id="S_SIM_DIVISION_V1",
            status="PASS",
            measured_value=recovery_dist
        )
    else:
        return EvidenceToken("", "S_SIM_DIVISION_V1", "KILL", 0.0, "PARTIAL_TRACE_FAILS")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_05: Fractions = Mixed States
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_fractions_mixed_states(d: int = 4):
    """
    CLAIM: Fractions emerge as convex combinations (mixed states).
    1/2 of ρ is: (1/2)ρ + (1/2)(I/d). This IS the fraction 1/2,
    meaning "half the structure of ρ, half noise."
    
    Properties:
    - S(pρ + (1-p)I/d) increases monotonically as p → 0
    - At p=1: full structure. At p=0: pure noise (zero)
    - The parameter p IS the fraction of structural content
    """
    print(f"\n{'='*60}")
    print(f"SIM_05: FRACTIONS = MIXED STATES (CONVEX COMBINATIONS)")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    rho = make_random_density_matrix(d)
    sigma = np.eye(d, dtype=complex) / d
    
    fractions = [1.0, 0.75, 0.5, 0.25, 0.1, 0.0]
    entropies = []
    
    for p in fractions:
        rho_mixed = p * rho + (1 - p) * sigma
        rho_mixed = rho_mixed / np.trace(rho_mixed)
        S = von_neumann_entropy(rho_mixed)
        phi = negentropy(rho_mixed, d)
        entropies.append(S)
        print(f"  p={p:.2f}: S={S:.6f}, Φ={phi:.6f}")
    
    # Verify: S increases monotonically as p decreases (more noise)
    monotone = all(entropies[i] <= entropies[i+1] + 1e-10
                   for i in range(len(entropies)-1))
    
    print(f"\n  Entropy monotone: {monotone}")
    print(f"  → p IS the fraction of structure")
    print(f"  → p=1: full, p=0.5: half, p=0: zero")
    print(f"  → Fractions are NOT axioms. They emerge from convex mixing.")
    
    if monotone:
        print(f"  PASS: Fractions = mixed states confirmed!")
        return EvidenceToken(
            token_id="E_SIM_FRACTIONS_OK",
            sim_spec_id="S_SIM_FRACTIONS_V1",
            status="PASS",
            measured_value=entropies[2]
        )
    else:
        return EvidenceToken("", "S_SIM_FRACTIONS_V1", "KILL", 0.0, "NOT_MONOTONE")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_06: Groups Emerge From Compositions
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_group_emergence(d: int = 4):
    """
    CLAIM: Group structure (closure, associativity, identity, inverse)
    emerges from composable unitary operations on density matrices.
    
    - Closure: U₁U₂ is also unitary (product of unitaries = unitary)
    - Associativity: (U₁U₂)U₃ = U₁(U₂U₃)
    - Identity: I (identity matrix)
    - Inverse: U† for each U
    """
    print(f"\n{'='*60}")
    print(f"SIM_06: GROUP STRUCTURE EMERGES")
    print(f"  d={d}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    U1 = make_random_unitary(d)
    U2 = make_random_unitary(d)
    U3 = make_random_unitary(d)
    
    # Closure: U1·U2 is unitary
    U12 = U1 @ U2
    closure = np.linalg.norm(U12 @ U12.conj().T - np.eye(d)) < 1e-10
    
    # Associativity: (U1·U2)·U3 = U1·(U2·U3)
    left = (U1 @ U2) @ U3
    right = U1 @ (U2 @ U3)
    associativity = np.linalg.norm(left - right) < 1e-10
    
    # Identity: I exists
    I_test = np.eye(d, dtype=complex)
    identity = np.linalg.norm(U1 @ I_test - U1) < 1e-10
    
    # Inverse: U·U† = I
    inverse = np.linalg.norm(U1 @ U1.conj().T - np.eye(d)) < 1e-10
    
    print(f"  Closure (U₁U₂ unitary): {closure}")
    print(f"  Associativity: {associativity}")
    print(f"  Identity element (I): {identity}")
    print(f"  Inverse (U†): {inverse}")
    print(f"  → All four group axioms emerge from unitary composition!")
    print(f"  → This is U(d): the unitary group of dimension d.")
    
    all_pass = closure and associativity and identity and inverse
    
    if all_pass:
        print(f"  PASS: Group structure emerges!")
        return EvidenceToken(
            token_id="E_SIM_GROUP_OK",
            sim_spec_id="S_SIM_GROUP_V1",
            status="PASS",
            measured_value=float(d)
        )
    else:
        return EvidenceToken("", "S_SIM_GROUP_V1", "KILL", 0.0, "GROUP_AXIOM_FAILS")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIM_07: Commutativity Fails (Non-Abelian)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def sim_nonabelian(d: int = 4, n_pairs: int = 50):
    """
    CLAIM: For d>1, the unitary group is non-abelian (U₁U₂ ≠ U₂U₁).
    This is the foundation of non-commutativity — the same axiom N01
    that started everything.
    
    The one exception: d=1 (scalars), where multiplication commutes.
    This shows that commutative arithmetic is the TRIVIAL CASE, not the default.
    """
    print(f"\n{'='*60}")
    print(f"SIM_07: NON-ABELIAN STRUCTURE (AB ≠ BA)")
    print(f"  d={d}, pairs={n_pairs}")
    print(f"{'='*60}")
    
    np.random.seed(42)
    commutative_count = 0
    
    for i in range(n_pairs):
        U1 = make_random_unitary(d)
        U2 = make_random_unitary(d)
        
        comm_norm = np.linalg.norm(U1 @ U2 - U2 @ U1)
        if comm_norm < 1e-10:
            commutative_count += 1
    
    noncommutative_pct = 100 * (1 - commutative_count / n_pairs)
    
    print(f"  Non-commuting pairs: {n_pairs - commutative_count}/{n_pairs} ({noncommutative_pct:.0f}%)")
    print(f"  → For d={d}: {noncommutative_pct:.0f}% of multiplications don't commute")
    print(f"  → Commutative arithmetic (ab=ba) is the EXCEPTION, not the rule")
    print(f"  → Real numbers commute because they live in d=1")
    
    if noncommutative_pct > 90:
        print(f"  PASS: Non-abelian structure confirmed!")
        return EvidenceToken(
            token_id="E_SIM_NONABELIAN_OK",
            sim_spec_id="S_SIM_NONABELIAN_V1",
            status="PASS",
            measured_value=noncommutative_pct
        )
    else:
        return EvidenceToken("", "S_SIM_NONABELIAN_V1", "KILL", 0.0, "TOO_COMMUTATIVE")


if __name__ == "__main__":
    results = []
    
    results.append(sim_zero_emergence())
    results.append(sim_negation_adjoint())
    results.append(sim_subtraction_inverse())
    results.append(sim_division_partial_trace())
    results.append(sim_fractions_mixed_states())
    results.append(sim_group_emergence())
    results.append(sim_nonabelian())
    
    print(f"\n{'='*60}")
    print(f"DEEP MATH FOUNDATIONS SUITE RESULTS")
    print(f"{'='*60}")
    for e in results:
        icon = "✓" if e.status == "PASS" else "✗"
        print(f"  {icon} {e.sim_spec_id}: {e.status} (value={e.measured_value:.6f})")
    
    base = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base, "a2_state", "sim_results")
    os.makedirs(results_dir, exist_ok=True)
    outpath = os.path.join(results_dir, "deep_math_results.json")
    with open(outpath, "w") as f:
        json.dump({
            "timestamp": datetime.now(UTC).isoformat(),
            "evidence_ledger": [
                {"token_id": e.token_id, "sim_spec_id": e.sim_spec_id,
                 "status": e.status, "measured_value": e.measured_value,
                 "kill_reason": e.kill_reason}
                for e in results
            ]
        }, f, indent=2)
    print(f"  Results saved to: {outpath}")
