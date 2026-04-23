#!/usr/bin/env python3
"""
Deep Engine Surface Audit — Ground Truth Measurements
=======================================================
Computationally measures every topology primitive, every terrain,
every operator × polarity × spinor chirality combination.

No claims — just numbers.
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hopf_manifold import (
    quaternion_to_su2, su2_to_quaternion, random_s3_point,
    is_on_s3, is_su2, hopf_map, is_on_s2,
    fiber_action, sample_fiber, base_loop_point, lift_base_point,
    lifted_base_loop, berry_phase,
    torus_coordinates, clifford_torus_sample, torus_radii,
    sample_nested_torus, inter_torus_transport,
    TORUS_INNER, TORUS_CLIFFORD, TORUS_OUTER, NESTED_TORI,
    coherent_state_density, density_to_bloch, von_neumann_entropy_2x2,
    left_weyl_spinor, right_weyl_spinor, left_density, right_density,
    rotate_left, rotate_right, fiber_phase_left, fiber_phase_right,
)
from geometric_operators import (
    apply_Ti, apply_Fe, apply_Te, apply_Fi,
    negentropy, delta_phi, trace_distance_2x2,
    _ensure_valid_density, I2, SIGMA_X, SIGMA_Y, SIGMA_Z,
)
from engine_core import (
    GeometricEngine, EngineState, StageControls,
    STAGES, TERRAINS, OPERATORS,
)

rng = np.random.default_rng(42)


def section(title):
    print(f"\n{'═' * 72}")
    print(f"  {title}")
    print(f"{'═' * 72}")


def subsection(title):
    print(f"\n  ── {title} {'─' * max(50 - len(title), 4)}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 1: TOPOLOGY PRIMITIVES
# ═══════════════════════════════════════════════════════════════════

section("1. TOPOLOGY PRIMITIVES")

# 1a. S³/SU(2) roundtrip
subsection("1a. S³ ↔ SU(2) roundtrip")
n_test = 100
max_err = 0
for _ in range(n_test):
    q = random_s3_point(rng)
    U = quaternion_to_su2(q)
    q2 = su2_to_quaternion(U)
    err = np.linalg.norm(q - q2)
    max_err = max(max_err, err)
    assert is_on_s3(q), "S³ point not on S³"
    assert is_su2(U), "SU(2) matrix not unitary"
print(f"    {n_test} roundtrips, max error: {max_err:.2e}")
print(f"    All on S³: ✓,  All in SU(2): ✓")

# 1b. Hopf map: fiber invariance + surjectivity
subsection("1b. Hopf map π: S³ → S²")
n_test = 50
max_fiber_err = 0
for _ in range(n_test):
    q = random_s3_point(rng)
    p = hopf_map(q)
    assert is_on_s2(p), "Hopf image not on S²"
    # Fiber invariance: π(e^{iθ}·q) = π(q)
    for theta in [0.3, 1.0, np.pi, 2.5]:
        q_rot = fiber_action(q, theta)
        p_rot = hopf_map(q_rot)
        err = np.linalg.norm(p - p_rot)
        max_fiber_err = max(max_fiber_err, err)
print(f"    Fiber invariance max error: {max_fiber_err:.2e}")
print(f"    All images on S²: ✓")

# Check surjectivity: sample N pole, S pole, equator
test_bloch = [
    ("North pole", np.array([0, 0, 1.0])),
    ("South pole", np.array([0, 0, -1.0])),
    ("Equator +x", np.array([1, 0, 0.0])),
    ("Equator +y", np.array([0, 1, 0.0])),
]
for name, target in test_bloch:
    q = lift_base_point(target)
    p = hopf_map(q)
    err = np.linalg.norm(p - target)
    print(f"    {name}: lift → Hopf error = {err:.2e}")

# 1c. Berry phase
subsection("1c. Berry phase")
loop = lifted_base_loop(128)
bp = berry_phase(loop)
# For great circle on S², solid angle = 2π → Berry phase = -π
print(f"    Great circle Berry phase: {bp:.4f} (expected: {-np.pi:.4f})")
print(f"    Error: {abs(bp + np.pi):.2e}")

# 1d. Nested tori
subsection("1d. Nested tori (3 latitudes)")
for name, eta in [("Inner π/8", TORUS_INNER), ("Clifford π/4", TORUS_CLIFFORD), ("Outer 3π/8", TORUS_OUTER)]:
    R_maj, R_min = torus_radii(eta)
    q = torus_coordinates(eta, 0.5, 1.2)
    assert is_on_s3(q), f"{name} not on S³"
    b = hopf_map(q)
    print(f"    {name:15s}: R_maj={R_maj:.4f}, R_min={R_min:.4f}, |q|={np.linalg.norm(q):.6f}, Bloch_z={b[2]:+.4f}")

# Transport angle preservation
subsection("1e. Inter-torus transport")
q0 = torus_coordinates(TORUS_CLIFFORD, 1.5, 2.3)
for target_eta, name in [(TORUS_INNER, "→Inner"), (TORUS_OUTER, "→Outer")]:
    qt = inter_torus_transport(q0, TORUS_CLIFFORD, target_eta)
    assert is_on_s3(qt), f"Transport {name} not on S³"
    # Extract angles
    a, b_, c, d = qt
    z1 = a + 1j * b_
    z2 = c + 1j * d
    theta1_t = np.angle(z1)
    theta2_t = np.angle(z2)
    print(f"    {name}: θ₁={theta1_t:.4f} (orig 1.500), θ₂={theta2_t:.4f} (orig 2.300), |q|={np.linalg.norm(qt):.6f}")

# 1f. Weyl spinors
subsection("1f. Weyl spinors L/R")
for _ in range(5):
    q = random_s3_point(rng)
    psi_L = left_weyl_spinor(q)
    psi_R = right_weyl_spinor(q)

    # Test: iσ₂ · ψ_L* = ψ_R ?
    sigma_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    psi_R_check = 1j * sigma_y @ np.conj(psi_L)
    err = np.linalg.norm(psi_R - psi_R_check)

    # Fiber phase: L gets +θ, R gets -θ
    theta = 0.7
    psi_L_rot = fiber_phase_left(psi_L, theta)
    psi_R_rot = fiber_phase_right(psi_R, theta)
    phase_L = np.angle(np.vdot(psi_L, psi_L_rot))
    phase_R = np.angle(np.vdot(psi_R, psi_R_rot))

    # Densities
    rho_L = left_density(q)
    rho_R = right_density(q)
    d_LR = trace_distance_2x2(rho_L, rho_R)

    if _ == 0:
        print(f"    ψ_R = iσ₂·ψ_L* check error: {err:.2e}")
        print(f"    Fiber phase L: {phase_L:+.4f} (expected +0.700)")
        print(f"    Fiber phase R: {phase_R:+.4f} (expected -0.700)")
        print(f"    D(ρ_L, ρ_R): {d_LR:.4f}")

# Are L/R densities always orthogonal?
n_ortho = 0
for _ in range(100):
    q = random_s3_point(rng)
    rho_L = left_density(q)
    rho_R = right_density(q)
    d = trace_distance_2x2(rho_L, rho_R)
    if d > 0.5:
        n_ortho += 1
print(f"    D(ρ_L, ρ_R) > 0.5 in {n_ortho}/100 random points")


# ═══════════════════════════════════════════════════════════════════
# SECTION 2: TERRAIN AUDIT (8 terrains)
# ═══════════════════════════════════════════════════════════════════

section("2. TERRAIN AUDIT")

subsection("2a. Terrain parameters")
print(f"    {'Terrain':10s} {'loop':6s} {'expand':7s} {'open':5s} {'angle_mod':10s} {'dt_mod':8s}")
for t in TERRAINS:
    a_mod = 1.2 if t["expansion"] else 0.8
    d_mod = 1.2 if t["open"] else 0.8
    print(f"    {t['name']:10s} {t['loop']:6s} {str(t['expansion']):7s} {str(t['open']):5s} {a_mod:10.1f} {d_mod:8.1f}")

subsection("2b. Per-terrain operator strength (engine type modulation)")
for etype in [1, 2]:
    engine = GeometricEngine(engine_type=etype)
    print(f"\n    Engine Type {etype}:")
    print(f"    {'Stage':15s} {'eff_strength':>12s} {'dominant':>10s}")
    for i, stage in enumerate(STAGES):
        ctrl = StageControls(piston=1.0)
        eff = engine._operator_strength(stage, ctrl)
        dom = "FULL" if eff > 0.5 else "suppressed"
        if i < 16 or (i == 16):  # Show all fiber + first base
            print(f"    {stage['name']:15s} {eff:12.2f} {dom:>10s}")
    print(f"    ...")

subsection("2c. Terrain dynamics separation")
# Do different terrains produce genuinely different state evolution?
engine = GeometricEngine(engine_type=1)
s0 = engine.init_state(rng=np.random.default_rng(42))
terrain_outputs = {}
for i in range(32):
    s1 = engine.step(s0, stage_idx=i, controls=StageControls(piston=1.0))
    key = STAGES[i]["name"]
    terrain_outputs[key] = s1.rho_L.copy()

# Measure pairwise distances between stages with SAME operator but DIFFERENT terrain
print(f"\n    Same-operator cross-terrain distances (testing terrain is NOT just a label):")
for op in OPERATORS:
    stages_with_op = [k for k in terrain_outputs if k.endswith(f"_{op}")]
    if len(stages_with_op) >= 2:
        dists = []
        for i in range(len(stages_with_op)):
            for j in range(i+1, len(stages_with_op)):
                d = trace_distance_2x2(terrain_outputs[stages_with_op[i]], terrain_outputs[stages_with_op[j]])
                dists.append(d)
        avg_d = np.mean(dists)
        max_d = np.max(dists)
        print(f"    {op}: avg D = {avg_d:.6f}, max D = {max_d:.6f}, n_pairs = {len(dists)}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 3: OPERATOR AUDIT (Ti/Fe/Te/Fi × pure/mixed)
# ═══════════════════════════════════════════════════════════════════

section("3. OPERATOR AUDIT")

# Pure state: |0⟩
rho_pure_0 = np.array([[1, 0], [0, 0]], dtype=complex)
# Pure state: |+⟩ = (|0⟩ + |1⟩)/√2
rho_pure_plus = np.array([[0.5, 0.5], [0.5, 0.5]], dtype=complex)
# Mixed state: 0.7|0⟩⟨0| + 0.3|1⟩⟨1|
rho_mixed = np.array([[0.7, 0.1], [0.1, 0.3]], dtype=complex)
rho_mixed = _ensure_valid_density(rho_mixed)
# Maximally mixed
rho_max = I2 / 2

test_states = [
    ("pure |0⟩", rho_pure_0),
    ("pure |+⟩", rho_pure_plus),
    ("mixed 70/30", rho_mixed),
    ("max mixed", rho_max),
]

ops = [
    ("Ti", apply_Ti),
    ("Fe", apply_Fe),
    ("Te", apply_Te),
    ("Fi", apply_Fi),
]

for op_name, op_fn in ops:
    subsection(f"3. {op_name} on 4 test states × 2 polarities")
    print(f"    {'state':15s} {'pol':5s} {'S_before':>8s} {'S_after':>8s} {'ΔΦ':>8s} {'D(ρ,ρ\')':>8s} {'Δz':>8s}")
    for state_name, rho in test_states:
        for pol_name, pol in [("UP", True), ("DOWN", False)]:
            S_before = von_neumann_entropy_2x2(rho)
            phi_before = negentropy(rho)
            rho_after = op_fn(rho, polarity_up=pol)
            S_after = von_neumann_entropy_2x2(rho_after)
            phi_after = negentropy(rho_after)
            dphi = phi_after - phi_before
            d = trace_distance_2x2(rho, rho_after)
            # z-bias shift
            dz = abs(np.real(rho_after[0,0] - rho_after[1,1]) - np.real(rho[0,0] - rho[1,1]))
            print(f"    {state_name:15s} {pol_name:5s} {S_before:8.4f} {S_after:8.4f} {dphi:+8.4f} {d:8.4f} {dz:8.4f}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 4: L/R CONJUGATE DYNAMICS
# ═══════════════════════════════════════════════════════════════════

section("4. L/R CONJUGATE DYNAMICS")

# Engine runs each operator differently on L vs R
# Test: same initial state, same operator, left-path vs right-path
q0 = torus_coordinates(TORUS_CLIFFORD, 0.0, 0.0)
rho_L0 = left_density(q0)
rho_R0 = right_density(q0)

print(f"\n    Initial states:")
print(f"    ρ_L Bloch: {density_to_bloch(rho_L0)}")
print(f"    ρ_R Bloch: {density_to_bloch(rho_R0)}")
print(f"    D(L,R): {trace_distance_2x2(rho_L0, rho_R0):.4f}")

subsection("4a. Direct operator conjugation test")
# Apply each operator to L and R, show difference
print(f"    {'Op':5s} {'pol':5s} {'D(L_out, R_out)':>15s} {'ΔΦ_L':>8s} {'ΔΦ_R':>8s} {'Bloch_L_z':>10s} {'Bloch_R_z':>10s}")

for op_name, op_fn in ops:
    for pol_name, pol in [("UP", True), ("DOWN", False)]:
        # Left: normal
        rho_L_out = op_fn(rho_L0, polarity_up=pol)
        # Right: conjugate (as engine does it)
        sx = SIGMA_X
        if op_name == "Te":
            rho_R_out = op_fn(rho_R0, polarity_up=not pol)
        elif op_name in ("Ti", "Fe", "Fi"):
            rho_conj = sx @ rho_R0 @ sx
            rho_conj = op_fn(rho_conj, polarity_up=pol)
            rho_R_out = sx @ rho_conj @ sx
            rho_R_out = _ensure_valid_density(rho_R_out)
        else:
            rho_R_out = op_fn(rho_R0, polarity_up=pol)

        d_LR = trace_distance_2x2(rho_L_out, rho_R_out)
        dphi_L = negentropy(rho_L_out) - negentropy(rho_L0)
        dphi_R = negentropy(rho_R_out) - negentropy(rho_R0)
        bz_L = density_to_bloch(rho_L_out)[2]
        bz_R = density_to_bloch(rho_R_out)[2]
        print(f"    {op_name:5s} {pol_name:5s} {d_LR:15.4f} {dphi_L:+8.4f} {dphi_R:+8.4f} {bz_L:+10.4f} {bz_R:+10.4f}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 5: ENTROPY FORMS COMPARISON
# ═══════════════════════════════════════════════════════════════════

section("5. ENTROPY FORMS — L/R SYSTEM")

subsection("5a. Conditional entropy contract")
print("    The current engine evolves rho_L and rho_R separately.")
print("    Without a jointly evolved 4x4 rho_LR, conditional/mutual")
print("    entropy are not informative audit metrics here.")
print("    Replacing that bogus product-state readout with a causal")
print("    low-Axis0 vs high-Axis0 entropy comparison.")

engine = GeometricEngine(engine_type=1)
low = engine.init_state(rng=np.random.default_rng(42))
high = engine.init_state(rng=np.random.default_rng(42))
ctrl_low = {i: StageControls(piston=0.8, axis0=0.10) for i in range(32)}
ctrl_high = {i: StageControls(piston=0.8, axis0=0.90) for i in range(32)}
low = engine.run_cycle(low, controls=ctrl_low)
high = engine.run_cycle(high, controls=ctrl_high)
axes_low = engine.read_axes(low)
axes_high = engine.read_axes(high)
print(f"    Low Axis0:  level={low.ga0_level:.3f}, S(L)={von_neumann_entropy_2x2(low.rho_L):.4f}, S(R)={von_neumann_entropy_2x2(low.rho_R):.4f}, GA0={axes_low['GA0_entropy']:.4f}")
print(f"    High Axis0: level={high.ga0_level:.3f}, S(L)={von_neumann_entropy_2x2(high.rho_L):.4f}, S(R)={von_neumann_entropy_2x2(high.rho_R):.4f}, GA0={axes_high['GA0_entropy']:.4f}")
print(f"    ΔGA0(high-low) = {axes_high['GA0_entropy'] - axes_low['GA0_entropy']:+.4f}")

subsection("5b. Is one Weyl spinor 'better'?")
# Run many cycles from random starts, see if L or R consistently has higher Φ
n_trials = 50
L_higher = 0
for trial in range(n_trials):
    engine = GeometricEngine(engine_type=1)
    state = engine.init_state(eta=TORUS_CLIFFORD,
                               theta1=rng.uniform(0, 2*np.pi),
                               theta2=rng.uniform(0, 2*np.pi),
                               rng=np.random.default_rng(trial))
    state = engine.run_cycle(state)
    phi_L = negentropy(state.rho_L)
    phi_R = negentropy(state.rho_R)
    if phi_L > phi_R + 1e-6:
        L_higher += 1
R_higher = n_trials - L_higher
print(f"    After 32-stage Type 1 cycle ({n_trials} random starts):")
print(f"      Φ_L > Φ_R: {L_higher}/{n_trials}")
print(f"      Φ_R ≥ Φ_L: {R_higher}/{n_trials}")

# Same for Type 2
L_higher_t2 = 0
for trial in range(n_trials):
    engine = GeometricEngine(engine_type=2)
    state = engine.init_state(eta=TORUS_CLIFFORD,
                               theta1=rng.uniform(0, 2*np.pi),
                               theta2=rng.uniform(0, 2*np.pi),
                               rng=np.random.default_rng(trial))
    state = engine.run_cycle(state)
    phi_L = negentropy(state.rho_L)
    phi_R = negentropy(state.rho_R)
    if phi_L > phi_R + 1e-6:
        L_higher_t2 += 1
R_higher_t2 = n_trials - L_higher_t2
print(f"    After 32-stage Type 2 cycle ({n_trials} random starts):")
print(f"      Φ_L > Φ_R: {L_higher_t2}/{n_trials}")
print(f"      Φ_R ≥ Φ_L: {R_higher_t2}/{n_trials}")


# ═══════════════════════════════════════════════════════════════════
# SECTION 6: NEGATIVE TESTS
# ═══════════════════════════════════════════════════════════════════

section("6. NEGATIVE TESTS")

subsection("6a. De-chiralized control status")
print("    A true commutative/de-chiralized control path is not yet")
print("    implemented in engine_core.py.")
print("    The previous left-only diagnostic did not test commutativity.")
print("    Honest current status: chirality can be measured, but its")
print("    negation still needs a dedicated control lane.")

subsection("6b. Zero-strength engine should be identity")
engine = GeometricEngine(engine_type=1)
state = engine.init_state(rng=np.random.default_rng(42))
rho_L_init = state.rho_L.copy()
for i in range(32):
    ctrl = StageControls(piston=0.0)
    state = engine.step(state, stage_idx=i, controls=ctrl)
d_zero = trace_distance_2x2(rho_L_init, state.rho_L)
print(f"    Zero-piston cycle: D(init, end) = {d_zero:.6f}")
print(f"    {'✓' if d_zero < 0.01 else '✗'} Near-identity")

subsection("6c. Rényi-2 entropy comparison")
# S₂(ρ) = -log₂(Tr(ρ²)) — compare with von Neumann
for state_name, rho in test_states:
    S_vn = von_neumann_entropy_2x2(rho)
    purity = np.real(np.trace(rho @ rho))
    S_renyi2 = -np.log2(max(purity, 1e-15))
    print(f"    {state_name:15s}: S_vN = {S_vn:.4f}, S₂ = {S_renyi2:.4f}, purity = {purity:.4f}")

print(f"\n{'═' * 72}")
print(f"  AUDIT COMPLETE")
print(f"{'═' * 72}")

# Save raw output
base = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(base, "a2_state", "sim_results")
os.makedirs(results_dir, exist_ok=True)
outpath = os.path.join(results_dir, "deep_engine_audit.json")
with open(outpath, "w") as f:
    json.dump({
        "timestamp": datetime.now(UTC).isoformat(),
        "sections_run": ["topology", "terrains", "operators", "lr_conjugate", "entropy_forms", "negative_tests"],
        "note": "ground truth audit — numbers only, no claims",
    }, f, indent=2)
print(f"  Results saved: {outpath}")
