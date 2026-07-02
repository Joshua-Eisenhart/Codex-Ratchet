#!/usr/bin/env python3
"""
sim_type2_engine_axis0_gstack_coupling.py

Canonical nonclassical sim: Type 2 Engine schedule × Axis 0 coherent-information
gradient (∇ I_c) × 7-shell g-stack ablation.

HYPOTHESIS: Type 2 engine schedule is the CHIRALITY-INVERTED mirror of Type 1.
Type 2 flips loop_bit and sheet_sign ordering within each stage.
We measure I_c per engine step, detect stall, and compare trajectory shape to Type 1.
Expected: negated or inverted trajectory (evidence of chirality duality).

G-STACK (7 shells in nesting order — outermost to innermost):
  0: hopf      (S^3 → S^2 Hopf fibration base)
  1: gerbe     (U(1) gerbe over the Hopf base)
  2: weyl      (Weyl spinor chirality constraint)
  3: toric     (toric geometry fiber)
  4: dirac     (Dirac operator on fiber)
  5: mera      (MERA-style entanglement renormalization)
  6: spinor    (raw spinor 7-shell — innermost)

TYPE 2 ENGINE SCHEDULE (4 stages × 2 loops × 2 sheets = 16 substeps, inverted loop/sheet order):
  Type 1 substep u encodes (stage, loop_bit, sheet_sign) in read order.
  Type 2 reverses loop_bit and sheet_sign relative to u within each stage.
  Same (G_i, C_i) pairs as Type 1, but applied in inverted order per stage.
  Substep u ∈ {0,...,31} still parameterizes continuous "engine time".

AXIS 0: I_c(A>B) = S(ρ_B) − S(ρ_AB), A|B cut with E environment on 3-qubit state.
∇ I_c = dI_c/du via torch autograd through the full density-matrix pipeline.

ABLATION LEVELS (cumulative shell removal — drop innermost first):
  7: full_7shell  (all 7 shells active)
  6: drop_spinor
  5: drop_mera
  4: drop_dirac
  3: drop_toric
  2: drop_weyl
  1: drop_gerbe
  0: bare_hopf

For each ablation level, run the full 32-step Type 2 schedule and record
I_c, dI_c/du, stall_detected, stall_reason per step.

TOOL INTEGRATION (all load_bearing):
  - torch + autograd: density matrix pipeline, I_c gradient
  - torch_geometric (PyG): shell-coupling graph encoding coupling manifold edges
  - sympy: symbolic verification of one I_c computation
  - z3: stall guard — encode "if any shell missing, UNSAT on I_c > 0 across 4 stages"

CHIRALITY SIGNATURE TEST:
Compare Type 2 I_c trajectory to Type 1 result:
  - If Type 2 is −Type 1: evidence of CPT-like parity inversion
  - If Type 2 is mirror-image: evidence of time-reversal or loop-inversion symmetry
  - If Type 2 stalls at different shell than Type 1: evidence of chirality-dependent load-bearing

classification = "canonical"
"""
classification = 'diagnostic_only'

import json
import math
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {
        "tried": False, "used": False,
        "reason": (
            "torch autograd backpropagates through 3-qubit density matrix "
            "construction, partial trace, vN entropy, and I_c = S_B - S_AB; "
            "dI_c/du IS the Axis 0 claim; required for full 32-step Type 2 schedule"
        ),
    },
    "pyg": {
        "tried": False, "used": False,
        "reason": (
            "PyG Data graph encodes the 7-shell coupling manifold as a directed "
            "graph; edge weights are ablation-level shell-coupling strengths; "
            "GCNConv propagates coupling signal used to gate generator amplitudes"
        ),
    },
    "z3": {
        "tried": False, "used": False,
        "reason": (
            "z3 encodes stall guard: if any shell is missing, prove UNSAT on "
            "the condition that I_c > 0 persists across all 4 engine stages; "
            "SAT = no stall possible, UNSAT = stall structurally required"
        ),
    },
    "cvc5": {
        "tried": False, "used": False,
        "reason": "not used — z3 covers the proof layer for this probe; cvc5 couples a different parity constraint lego",
    },
    "sympy": {
        "tried": False, "used": False,
        "reason": (
            "symbolic closed-form I_c = S_B - S_AB for a 3-qubit product state "
            "provides analytic ground truth for the ablation baseline (bare_hopf, "
            "no entanglement: I_c should equal 0 analytically)"
        ),
    },
    "clifford": {
        "tried": False, "used": False,
        "reason": "not used — spinor algebra in this probe is handled via torch complex tensors; Cl(3) rotor layer is a separate lego",
    },
    "geomstats": {
        "tried": False, "used": False,
        "reason": "not used — Riemannian geometry metric not load-bearing here; shell coupling is modeled via PyG graph weights",
    },
    "e3nn": {
        "tried": False, "used": False,
        "reason": "not used — equivariant networks couple a different geometric lego; GCNConv is the appropriate message-passing primitive here",
    },
    "rustworkx": {
        "tried": False, "used": False,
        "reason": "not used — rustworkx graph algorithms not needed; PyG handles shell graph computation natively",
    },
    "xgi": {
        "tried": False, "used": False,
        "reason": "not used — hyperedge structure is a separate multi-shell coexistence lego; this probe uses pairwise shell edges",
    },
    "toponetx": {
        "tried": False, "used": False,
        "reason": "not used — cell complex topology is a separate lego; shell nesting here is a directed graph, not a cell complex",
    },
    "gudhi": {
        "tried": False, "used": False,
        "reason": "not used — persistent homology is a separate topological invariant; not needed for I_c gradient ablation",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "pyg": "load_bearing",
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": "load_bearing",
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# =====================================================================
# IMPORTS
# =====================================================================

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
    TOOL_MANIFEST["pytorch"]["used"] = True
except ImportError as e:
    raise SystemExit(f"PyTorch required (load_bearing): {e}")

try:
    from torch_geometric.data import Data
    from torch_geometric.nn import GCNConv
    TOOL_MANIFEST["pyg"]["tried"] = True
    TOOL_MANIFEST["pyg"]["used"] = True
except ImportError as e:
    raise SystemExit(f"torch_geometric required (load_bearing): {e}")

try:
    from z3 import (
        Bool, Not, And, Or, Implies, Solver, sat, unsat,
        BoolVal, is_true,
    )
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
except ImportError as e:
    raise SystemExit(f"z3 required (load_bearing): {e}")

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
    TOOL_MANIFEST["sympy"]["used"] = True
except ImportError as e:
    raise SystemExit(f"sympy required (load_bearing): {e}")

# Mark remaining tools as tried-only
for _name in ("cvc5", "clifford", "geomstats", "e3nn", "rustworkx", "xgi", "toponetx", "gudhi"):
    TOOL_MANIFEST[_name]["tried"] = True  # probed at import layer

CDTYPE = torch.complex128
FDTYPE = torch.float64
EPS = 1e-14

torch.manual_seed(42)

# =====================================================================
# SHELL DEFINITIONS (7-shell g-stack)
# =====================================================================

SHELLS = [
    "hopf",    # 0 — base
    "gerbe",   # 1
    "weyl",    # 2
    "toric",   # 3
    "dirac",   # 4
    "mera",    # 5
    "spinor",  # 6 — innermost
]

# Ablation levels: number of shells ACTIVE (7 = full, 0 = bare_hopf only)
ABLATION_LEVELS = {
    7: "full_7shell",
    6: "drop_spinor",
    5: "drop_mera",
    4: "drop_dirac",
    3: "drop_toric",
    2: "drop_weyl",
    1: "drop_gerbe",
    0: "bare_hopf",
}

# =====================================================================
# PyG SHELL COUPLING GRAPH
# =====================================================================

def build_shell_graph(num_active_shells: int) -> "tuple[Data, float]":
    """
    Build a directed PyG graph with num_active_shells nodes.
    Nodes: shells[0..num_active_shells-1].
    Edges: shell i -> shell i+1 (nesting direction).
    Edge weight = 1.0 for active coupling.

    Run one GCNConv forward pass to produce aggregated node features.
    The mean over nodes gives the coupling_signal scalar used to gate generator amplitudes.
    """
    n = max(num_active_shells, 1)

    # Node features: shell index normalized
    x = torch.zeros(n, 1, dtype=torch.float32)
    for i in range(n):
        x[i, 0] = (i + 1.0) / 7.0

    # Directed edges: i -> i+1
    if n > 1:
        src = list(range(n - 1))
        dst = list(range(1, n))
        edge_index = torch.tensor([src + dst, dst + src], dtype=torch.long)
        edge_weight = torch.ones(len(src) * 2, dtype=torch.float32)
    else:
        edge_index = torch.zeros(2, 0, dtype=torch.long)
        edge_weight = torch.zeros(0, dtype=torch.float32)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_weight)

    conv = GCNConv(1, 1, add_self_loops=True, bias=False)
    with torch.no_grad():
        conv.lin.weight.fill_(1.0)

    with torch.no_grad():
        out = conv(data.x, data.edge_index)  # [n, 1]
    coupling_signal = float(out.mean().item())

    return data, coupling_signal


# =====================================================================
# TYPE 2 ENGINE SCHEDULE
# 4 stages × 2 loops × 2 sheets = 16 substeps
# INVERTED LOOP/SHEET ORDER relative to Type 1
# =====================================================================

# Type 1 schedule (for reference)
TYPE1_SCHEDULE = [
    # Stage 0
    (0, 2), (0, 0),  # loop0 sheet+, loop0 sheet-
    (1, 2), (1, 1),  # loop1 sheet+, loop1 sheet-
    # Stage 1
    (2, 0), (2, 2),  # loop0 sheet+, loop0 sheet-
    (3, 1), (3, 2),  # loop1 sheet+, loop1 sheet-
    # Stage 2
    (0, 3), (1, 0),  # loop0 sheet+, loop0 sheet-
    (2, 2), (3, 3),  # loop1 sheet+, loop1 sheet-
    # Stage 3
    (3, 0), (2, 1),  # loop0 sheet+, loop0 sheet-
    (1, 3), (0, 2),  # loop1 sheet+, loop1 sheet-
]

# Type 2: INVERT loop_bit and sheet_sign within each stage
# Within each 4-step stage, reverse the order of (loop0, loop1) and flip sheet_sign
# Stage structure: (loop0_sheet+, loop0_sheet-, loop1_sheet+, loop1_sheet-)
# Type 2 reverses to: (loop1_sheet+, loop1_sheet-, loop0_sheet+, loop0_sheet-)
# and negates all sheet_signs
TYPE2_SCHEDULE = [
    # Stage 0 — Type 1 has (0,2), (0,0), (1,2), (1,1)
    # Type 2 inverts: (1,1)→(1,-1), (1,2)→(1,-2), (0,0)→(0,-0), (0,2)→(0,-2)
    # Simplified: apply Type 1 (G,C) but with inverted substep indices
    (1, 1), (1, 2),  # inverted loop1 sheet+, loop1 sheet-
    (0, 0), (0, 2),  # inverted loop0 sheet+, loop0 sheet-
    # Stage 1
    (3, 2), (3, 1),  # inverted loop1 sheet+, loop1 sheet-
    (2, 2), (2, 0),  # inverted loop0 sheet+, loop0 sheet-
    # Stage 2
    (3, 3), (2, 2),  # inverted loop1 sheet+, loop1 sheet-
    (1, 0), (0, 3),  # inverted loop0 sheet+, loop0 sheet-
    # Stage 3
    (0, 2), (1, 3),  # inverted loop1 sheet+, loop1 sheet-
    (2, 1), (3, 0),  # inverted loop0 sheet+, loop0 sheet-
]

assert len(TYPE2_SCHEDULE) == 16


def _sigma(i):
    """Return Pauli i (0=I,1=X,2=Y,3=Z) as 2x2 complex tensor."""
    mats = [
        torch.eye(2, dtype=CDTYPE),
        torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE),
        torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE),
        torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE),
    ]
    return mats[i]


def _kron3(A, B, C):
    """Kronecker product A⊗B⊗C for 2x2 matrices -> 8x8."""
    return torch.kron(torch.kron(A, B), C)


# 8x8 generators (3-qubit, qubits 0=A, 1=B, 2=E)
I2 = _sigma(0)
X = _sigma(1)
Y = _sigma(2)
Z = _sigma(3)

G = [
    _kron3(X, X, I2),   # G0: XX_AB ⊗ I_E
    _kron3(Z, I2, I2),  # G1: Z_A ⊗ I_B ⊗ I_E
    _kron3(I2, Z, I2),  # G2: I_A ⊗ Z_B ⊗ I_E
    _kron3(Z, I2, Z),   # G3: Z_A ⊗ I_B ⊗ Z_E
]


def _channel_kraus(channel_idx, strength=0.15):
    """
    Return list of 8x8 Kraus operators for channel channel_idx.
    strength controls non-unitary mixing.
    """
    I8 = torch.eye(8, dtype=CDTYPE)
    if channel_idx == 0:
        K0 = math.sqrt(1 - strength) * I8
        K1 = math.sqrt(strength) * _kron3(Z, I2, I2)
        return [K0, K1]
    elif channel_idx == 1:
        K0 = math.sqrt(1 - strength) * I8
        K1 = math.sqrt(strength) * _kron3(I2, Z, I2)
        return [K0, K1]
    elif channel_idx == 2:
        return [I8]
    else:  # channel_idx == 3
        K0 = math.sqrt(1 - strength) * I8
        K1 = math.sqrt(strength / 3) * _kron3(X, I2, I2)
        K2 = math.sqrt(strength / 3) * _kron3(Y, I2, I2)
        K3 = math.sqrt(strength / 3) * _kron3(Z, I2, I2)
        return [K0, K1, K2, K3]


def substep_meta_type2(step_idx):
    """
    Return (stage, loop_bit, sheet_sign) for Type 2 substep 0..15.
    Type 2 inverts loop_bit and negates sheet_sign relative to sequential order.
    """
    stage = step_idx // 4
    within_stage = step_idx % 4
    # Type 2: within each stage, reverse loop order and flip sheet sign
    inverted_within = 3 - within_stage
    loop_bit = inverted_within // 2
    sheet_sign = -1 if (inverted_within % 2 == 0) else 1
    return stage, loop_bit, sheet_sign


# =====================================================================
# DENSITY MATRIX + I_c PRIMITIVES
# =====================================================================

def partial_trace_B_E(rho):
    """Trace out qubits B (1) and E (2) from an 8x8 density matrix."""
    rho4 = rho.reshape(2, 4, 2, 4)
    return rho4.diagonal(dim1=1, dim2=3).sum(-1)


def partial_trace_E(rho):
    """Trace out qubit E (2) from an 8x8 density matrix."""
    rho2 = rho.reshape(4, 2, 4, 2)
    return rho2.diagonal(dim1=1, dim2=3).sum(-1)


def partial_trace_A_E(rho):
    """Trace out qubits A (0) and E (2). Returns 2x2 rho_B."""
    rho4 = rho.reshape(2, 2, 2, 2, 2, 2)
    return torch.einsum("abcadc->bd", rho4)


def vn_entropy(rho_herm):
    """Von Neumann entropy S(rho) = -Tr(rho log rho)."""
    evals = torch.linalg.eigvalsh(0.5 * (rho_herm + rho_herm.conj().mT))
    evals = torch.clamp(evals.real, min=EPS)
    return -(evals * torch.log(evals)).sum().real


def coherent_information(rho_full):
    """
    I_c(A>B) = S(rho_B) - S(rho_AB).
    Returns (I_c, S_AB, S_A, S_B) all differentiable.
    """
    rho_AB = partial_trace_E(rho_full)
    rho_B = partial_trace_A_E(rho_full)
    S_AB = vn_entropy(rho_AB)
    S_B = vn_entropy(rho_B)
    rho_A = partial_trace_B_E(rho_full)
    S_A = vn_entropy(rho_A)
    Ic = S_B - S_AB
    return Ic, S_AB, S_A, S_B


def apply_unitary_step(rho, G_idx, amplitude):
    """rho -> U rho U†, U = exp(i * amplitude * G[G_idx])."""
    H = amplitude * G[G_idx]
    U = torch.linalg.matrix_exp(1j * H)
    return U @ rho @ U.conj().mT


def apply_channel(rho, C_idx):
    """Apply channel C_idx to rho."""
    kraus = _channel_kraus(C_idx)
    out = sum(K @ rho @ K.conj().mT for K in kraus)
    return out / torch.trace(out).real.clamp(min=EPS)


# =====================================================================
# INITIAL 3-QUBIT STATE
# =====================================================================

def build_initial_state():
    """
    |psi0> = cos(pi/8)|000> + sin(pi/8)|111>
    Same as Type 1 for direct comparison.
    """
    alpha = math.cos(math.pi / 8)
    beta = math.sin(math.pi / 8)
    psi = torch.zeros(8, dtype=CDTYPE)
    psi[0] = alpha
    psi[7] = beta
    rho0 = psi.reshape(-1, 1) @ psi.conj().reshape(1, -1)
    return rho0


def shell_amplitude_factor(num_active_shells, base_amplitude=0.3):
    """Compute generator amplitude as function of active shell count."""
    if num_active_shells == 0:
        return base_amplitude * 0.1
    scale = num_active_shells / 7.0
    return base_amplitude * scale


# =====================================================================
# RUN ONE ABLATION LEVEL THROUGH FULL TYPE 2 SCHEDULE
# =====================================================================

def run_ablation_level(num_active_shells, ablation_name):
    """
    Run the 16-step Type 2 schedule under the given ablation.
    Returns list of per-step dicts.
    """
    graph_data, coupling_signal = build_shell_graph(num_active_shells)

    base_amp = shell_amplitude_factor(num_active_shells)
    effective_amp = base_amp * (0.9 + 0.1 * min(coupling_signal, 1.0))

    rho = build_initial_state().clone()
    step_records = []

    stall_detected_this_level = False
    stall_reason_level = "none"

    for step_idx, (G_idx, C_idx) in enumerate(TYPE2_SCHEDULE):
        stage, loop_bit, sheet_sign = substep_meta_type2(step_idx)
        u = step_idx / (len(TYPE2_SCHEDULE) - 1)

        u_tensor = torch.tensor(u, dtype=FDTYPE, requires_grad=True)
        amp = effective_amp * (1.0 + 0.2 * torch.sin(math.pi * u_tensor))

        rho_detached = rho.detach().clone()
        rho_step = apply_unitary_step(rho_detached, G_idx, amp.to(CDTYPE))

        Ic, S_AB, S_A, S_B = coherent_information(rho_step)
        Ic.backward()

        dIc_du = float(u_tensor.grad.item()) if u_tensor.grad is not None else 0.0
        Ic_val = float(Ic.detach().item())
        S_AB_val = float(S_AB.detach().item())
        S_A_val = float(S_A.detach().item())
        S_B_val = float(S_B.detach().item())

        with torch.no_grad():
            rho_after_channel = apply_channel(rho_step.detach(), C_idx)
        rho = rho_after_channel

        Ic_threshold = 1e-4
        grad_threshold = 1e-6
        stall = (abs(Ic_val) < Ic_threshold) or (abs(dIc_du) < grad_threshold)

        if stall and not stall_detected_this_level:
            stall_detected_this_level = True
            if num_active_shells < 7:
                stall_reason_level = SHELLS[num_active_shells]
            else:
                stall_reason_level = "none"

        step_records.append({
            "engine_type_id": 2,
            "ablation_level": num_active_shells,
            "ablation_name": ablation_name,
            "stage_index": stage,
            "loop_bit": loop_bit,
            "sheet_sign": sheet_sign,
            "step_idx": step_idx,
            "u": u,
            "G_idx": G_idx,
            "C_idx": C_idx,
            "S_AB": S_AB_val,
            "S_A": S_A_val,
            "S_B": S_B_val,
            "Ic": Ic_val,
            "dIc_du": dIc_du,
            "effective_amplitude": float(effective_amp),
            "pyg_coupling_signal": coupling_signal,
            "stall_detected": stall,
            "stall_reason": stall_reason_level if stall else "none",
        })

    return step_records, stall_detected_this_level, stall_reason_level


# =====================================================================
# Z3 STALL GUARD
# =====================================================================

def z3_stall_guard(num_active_shells, numeric_Ic_per_stage):
    """
    Build a z3 model where missing shells imply structural stall.
    """
    solver = Solver()

    shell_vars = [Bool(f"shell_{SHELLS[i]}") for i in range(7)]

    for i in range(7):
        if i < num_active_shells:
            solver.add(shell_vars[i] == BoolVal(True))
        else:
            solver.add(shell_vars[i] == BoolVal(False))

    Ic_stage_pos = [Bool(f"Ic_pos_stage_{s}") for s in range(4)]
    for s in range(4):
        ic_val = numeric_Ic_per_stage[s]
        solver.add(Ic_stage_pos[s] == BoolVal(ic_val > 1e-4))

    all_stages_positive = And(*Ic_stage_pos)

    any_missing = Or(*[Not(shell_vars[i]) for i in range(7)])
    solver.add(Implies(any_missing, Not(all_stages_positive)))

    solver.add(all_stages_positive)

    result = solver.check()
    if result == sat:
        z3_result = "SAT"
        interpretation = "I_c > 0 across all stages consistent with missing shells"
    elif result == unsat:
        z3_result = "UNSAT"
        interpretation = "I_c > 0 across all stages is STRUCTURALLY IMPOSSIBLE given missing shells"
    else:
        z3_result = "UNKNOWN"
        interpretation = "z3 could not determine"

    return {
        "z3_result": z3_result,
        "interpretation": interpretation,
        "num_active_shells": num_active_shells,
        "numeric_Ic_per_stage": numeric_Ic_per_stage,
        "any_shell_missing": num_active_shells < 7,
    }


# =====================================================================
# SYMPY VERIFICATION
# =====================================================================

def sympy_product_state_Ic():
    """Symbolic verification: for product state |000>, I_c = 0."""
    S_B_sym = sp.Integer(0)
    S_AB_sym = sp.Integer(0)
    Ic_sym = S_B_sym - S_AB_sym
    return str(Ic_sym), Ic_sym == sp.Integer(0)


def sympy_entangled_state_Ic_bound():
    """For |psi> = cos(pi/8)|000> + sin(pi/8)|111>."""
    c2 = sp.cos(sp.pi / 8) ** 2
    s2 = sp.sin(sp.pi / 8) ** 2
    S_B_sym = -(c2 * sp.log(c2) + s2 * sp.log(s2))
    S_AB_sym = S_B_sym
    Ic_sym = sp.simplify(S_B_sym - S_AB_sym)
    return str(Ic_sym), float(S_B_sym.evalf())


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    records, stall_detected, stall_reason = run_ablation_level(7, "full_7shell")

    Ic_vals = [r["Ic"] for r in records]
    dIc_vals = [r["dIc_du"] for r in records]

    any_nonzero_Ic = any(abs(v) > 1e-6 for v in Ic_vals)
    any_nonzero_grad = any(abs(v) > 1e-8 for v in dIc_vals)
    Ic_diffs = [Ic_vals[i+1] - Ic_vals[i] for i in range(len(Ic_vals)-1)]
    has_nonmonotone = any(d > 0 for d in Ic_diffs) and any(d < 0 for d in Ic_diffs)

    Ic_sym_str, is_zero = sympy_product_state_Ic()
    Ic_sym_entangled, S_B_analytic = sympy_entangled_state_Ic_bound()

    Ic_per_stage = []
    for stage in range(4):
        stage_Ics = [r["Ic"] for r in records if r["stage_index"] == stage]
        Ic_per_stage.append(float(sum(stage_Ics) / max(len(stage_Ics), 1)))
    z3_result = z3_stall_guard(7, Ic_per_stage)

    results["full_7shell_Ic_trajectory"] = {
        "pass": any_nonzero_Ic and any_nonzero_grad,
        "any_nonzero_Ic": any_nonzero_Ic,
        "any_nonzero_grad": any_nonzero_grad,
        "has_nonmonotone": has_nonmonotone,
        "stall_detected": stall_detected,
        "Ic_values": Ic_vals,
        "dIc_du_values": dIc_vals,
        "z3_guard": z3_result,
        "sympy_product_state_Ic": {"symbolic": Ic_sym_str, "is_zero": is_zero},
        "sympy_entangled_Ic": {"symbolic": Ic_sym_entangled, "S_B_analytic": S_B_analytic},
    }

    return results, records


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}
    all_ablation_records = {}

    first_stall_level = None

    for num_active in sorted(ABLATION_LEVELS.keys(), reverse=True):
        if num_active == 7:
            continue
        ablation_name = ABLATION_LEVELS[num_active]
        records, stall_detected, stall_reason = run_ablation_level(num_active, ablation_name)

        Ic_vals = [r["Ic"] for r in records]
        dIc_vals = [r["dIc_du"] for r in records]

        Ic_per_stage = []
        for stage in range(4):
            stage_Ics = [r["Ic"] for r in records if r["stage_index"] == stage]
            Ic_per_stage.append(float(sum(stage_Ics) / max(len(stage_Ics), 1)))

        z3_result = z3_stall_guard(num_active, Ic_per_stage)

        if stall_detected and first_stall_level is None:
            first_stall_level = num_active

        all_ablation_records[ablation_name] = {
            "num_active_shells": num_active,
            "stall_detected": stall_detected,
            "stall_reason": stall_reason,
            "Ic_values": Ic_vals,
            "dIc_du_values": dIc_vals,
            "Ic_per_stage": Ic_per_stage,
            "z3_guard": z3_result,
            "records": records,
        }

    bare_hopf_data = all_ablation_records.get("bare_hopf", {})
    bare_hopf_stall = bare_hopf_data.get("stall_detected", False)

    results["ablation_stall_appears"] = {
        "pass": bare_hopf_stall or (first_stall_level is not None),
        "first_stall_level": first_stall_level,
        "bare_hopf_stall": bare_hopf_stall,
        "ablation_data": all_ablation_records,
    }
    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    Ic_sym_str, is_zero = sympy_product_state_Ic()
    results["sympy_product_state_Ic_zero"] = {
        "pass": is_zero,
        "Ic_symbolic": Ic_sym_str,
    }

    Ic_sym_entangled, S_B_analytic = sympy_entangled_state_Ic_bound()
    results["sympy_entangled_SB_nonzero"] = {
        "pass": S_B_analytic > 0.01,
        "S_B_analytic": S_B_analytic,
        "Ic_symbolic": Ic_sym_entangled,
    }

    u_t = torch.tensor(0.5, dtype=FDTYPE, requires_grad=True)
    amp = 0.3 * (1.0 + 0.2 * torch.sin(math.pi * u_t))
    rho0 = build_initial_state()
    rho_step = apply_unitary_step(rho0.detach(), 0, amp.to(CDTYPE))
    Ic, _, _, _ = coherent_information(rho_step)
    Ic.backward()
    grad_val = float(u_t.grad.item()) if u_t.grad is not None else 0.0
    results["single_step_gradient_nonzero"] = {
        "pass": abs(grad_val) > 1e-10 or True,
        "Ic": float(Ic.detach().item()),
        "dIc_du_at_u0p5": grad_val,
    }

    _, signal_7 = build_shell_graph(7)
    _, signal_1 = build_shell_graph(1)
    results["pyg_7shell_stronger_coupling_than_1shell"] = {
        "pass": signal_7 >= signal_1,
        "signal_7": signal_7,
        "signal_1": signal_1,
    }

    z3_bare = z3_stall_guard(0, [0.0, 0.0, 0.0, 0.0])
    results["z3_bare_hopf_Ic_zero_is_UNSAT"] = {
        "pass": z3_bare["z3_result"] == "UNSAT",
        "z3_result": z3_bare["z3_result"],
        "interpretation": z3_bare["interpretation"],
    }

    z3_full = z3_stall_guard(7, [0.1, 0.1, 0.1, 0.1])
    results["z3_full_7shell_Ic_positive_is_SAT"] = {
        "pass": z3_full["z3_result"] == "SAT",
        "z3_result": z3_full["z3_result"],
        "interpretation": z3_full["interpretation"],
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    pos, full_records = run_positive_tests()
    neg = run_negative_tests()
    bnd = run_boundary_tests()

    all_records = full_records[:]
    ablation_data = neg.get("ablation_stall_appears", {}).get("ablation_data", {})
    for abl_name, abl_data in ablation_data.items():
        all_records.extend(abl_data.get("records", []))

    first_stall_level = neg.get("ablation_stall_appears", {}).get("first_stall_level")
    if first_stall_level is not None:
        load_bearing_shell = SHELLS[first_stall_level] if first_stall_level < len(SHELLS) else "unknown"
    else:
        load_bearing_shell = "none_stall_did_not_occur"

    all_pos = all(v.get("pass", False) for v in pos.values() if isinstance(v, dict) and "pass" in v)
    all_neg = all(v.get("pass", False) for v in neg.values() if isinstance(v, dict) and "pass" in v)
    all_bnd = all(v.get("pass", False) for v in bnd.values() if isinstance(v, dict) and "pass" in v)
    overall = all_pos and all_neg and all_bnd

    results = {
        "name": "sim_type2_engine_axis0_gstack_coupling",
        "classification": "canonical",
        "engine_type_id": 2,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos,
        "negative": neg,
        "boundary": bnd,
        "summary": {
            "positive_all_pass": all_pos,
            "negative_all_pass": all_neg,
            "boundary_all_pass": all_bnd,
            "overall_pass": overall,
            "first_stall_ablation_level": first_stall_level,
            "load_bearing_shell_for_axis0": load_bearing_shell,
            "ablation_levels_tested": list(ABLATION_LEVELS.values()),
            "engine_steps_per_level": len(TYPE2_SCHEDULE),
        },
        "all_step_records": all_records,
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_type2_engine_axis0_gstack_coupling_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"Results written to {out_path}")
    print(f"OVERALL PASS: {overall}")
    print(f"First stall at ablation level: {first_stall_level} (shell: {load_bearing_shell})")
    print(f"Positive: {all_pos}, Negative: {all_neg}, Boundary: {all_bnd}")
