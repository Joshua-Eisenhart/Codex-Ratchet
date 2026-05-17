# Public API contract — informal scout (math-named primitives only)

This file specifies the primitives an informal-scout candidate module exports. The
scout is a proposal mine and falsifier lab — NOT a canonical result surface. Every
identifier here is a literal math object (channel, operator, projector, density
matrix, holonomy, etc.). Jargon imported from prior drafts (`axis`, `Ax0..Ax6`,
`engine_stage`, `gstack`, `Engine A/B`, `terrain`, `prime_resonance`, `Type 1/2`,
`Carnot`, `Szilard`, `IGT`, `I-Ching`, `hexagram`) is OUT. If a generator emits any
of those names, the proposal is contaminated and is not eligible for promotion.

Carrier: 4-qubit Hilbert space, dim = 16. Qobjs use `dims=[[2,2,2,2],[2,2,2,2]]`.

## Scope and status

- This is informal scout output. Status vocabulary: SURVIVED / KILLED / OPEN /
  NOT_YET_TESTED. Not PASS/FAIL.
- Promotion to `system_v4/probes/` requires (a) literal-math name, (b) reviewer
  audit, (c) at least one tool integration that is load-bearing (not decorative).
- Sidequest claim ceiling: `noncanonical_exploration`. No bridge claims.

## Required primitives (math-named)

Each candidate exports the following module-level functions. The runner imports
and calls them; stdout has no effect.

### `pauli_basis_with_u1_connection() -> dict`

Construct an operator basis on the 4-qubit carrier together with a U(1) connection
1-form discretized as a 16×16 Hermitian operator on the carrier.

Returns:
```python
{
    "carrier_dim": 16,
    "operator_basis_qt": list[qt.Qobj],     # Hermitian basis, dims=[[2,2,2,2],[2,2,2,2]]
    "u1_connection_qt": qt.Qobj,            # connection operator A; holonomy nontrivial on closed loops
    "is_on_basis_span": callable,           # (rho_qt) -> bool: state is reachable by basis-generated flow
}
```

Constraints:
- `u1_connection_qt` must give nontrivial holonomy `exp(i ∮ A)` on at least one
  closed loop (matches `u1_holonomy_integral()`).
- `is_on_basis_span(rho)` returns True for `|0⟩^⊗4⟨0|^⊗4` and for any state
  produced by `exp(-iαH) ρ exp(+iαH)` with H in the basis.

### `nonidentity_kraus_channel_pair() -> dict`

Two distinct CPTP channels A, B on the carrier such that A∘B ≠ B∘A on at least
one input density matrix.

Returns:
```python
{
    "channel_A_kraus": list[qt.Qobj],       # Kraus operators summing to identity ∑ K†K = I
    "channel_B_kraus": list[qt.Qobj],
    "rho_witness_qt": qt.Qobj,              # input on which order matters
    "rho_AB_qt": qt.Qobj,                   # A(B(ρ))
    "rho_BA_qt": qt.Qobj,                   # B(A(ρ))
    "trace_distance_AB_BA": float,          # > 0
}
```

### `dephasing_channel(basis: str, strength: float, rho_qt) -> dict`

Apply a dephasing channel on the named single-qubit basis (`"z"` or `"x"`) at
strength γ ∈ [0,1] to a 4-qubit input. Reports purity before/after.

Returns:
```python
{
    "basis": str,                           # "z" or "x"
    "strength": float,
    "output_rho_qt": qt.Qobj,
    "purity_input": float,                  # Tr(ρ²)
    "purity_output": float,                 # Tr(ρ_out²) ≤ purity_input
    "fixed_subspace_basis_state": qt.Qobj,  # an eigenstate of the dephasing pointer basis
}
```

### `unitary_rotation_channel(axis: str, angle: float, rho_qt) -> dict`

Apply `U = exp(-i (angle/2) σ_axis ⊗ I ⊗ I ⊗ I)` to ρ. `axis ∈ {"x","z"}`.

Returns:
```python
{
    "axis": str,
    "angle": float,
    "output_rho_qt": qt.Qobj,
    "purity_preserved": bool,               # |Tr(ρ²) − Tr(ρ_out²)| < 1e-9
    "trace_distance_from_input": float,
}
```

### `m_equivalence_witness() -> dict`

Two density matrices that are NOT element-equal but have IDENTICAL probe-
expectation tuples under a fixed probe family M. Operational form of `a ~_M b`.

Returns:
```python
{
    "rho_a_qt": qt.Qobj,
    "rho_b_qt": qt.Qobj,
    "are_distinct": bool,                   # rho_a != rho_b
    "share_probe_class": bool,              # tuple(Tr(M_i ρ_a)) == tuple(Tr(M_i ρ_b))
    "probe_class_a": tuple[float, ...],
    "probe_class_b": tuple[float, ...],
}
```

### `finite_truncation_witness(truncation_n: int) -> int`

Deterministic integer-valued function of an integer truncation parameter.
Non-constant in `truncation_n`. Encodes finitude (F01) by depending on the
finite cutoff in a non-vacuous way.

### `probe_expectation_quotient(rho_qt) -> dict`

The probe family M defines an equivalence quotient on density matrices. Return
the M-class signature plus a canonical representative.

Returns:
```python
{
    "probe_vector": list[float],
    "canonical_representative_qt": qt.Qobj,
    "compression_ratio": float,             # input_dof / output_dof > 1
    "recovery_trace_distance": float,
}
```

Constraint: two M-equivalent inputs (from `m_equivalence_witness`) must yield
identical `probe_vector`s.

### `u1_holonomy_integral(loop_radius: float = 1.0, n_steps: int = 64) -> dict`

Path-ordered integral of `u1_connection_qt` around a closed loop in parameter
space. Returns Berry-phase-style geometric phase.

Returns:
```python
{
    "loop_radius": float,
    "holonomy_phase": float,                # radians; nonzero for nontrivial loop
    "holonomy_unitary_2x2": list[list[complex]],
    "is_unitary": bool,
    "winding_estimate": float,
}
```

### `weyl_chirality_projectors() -> dict`

Left/right Weyl projectors `P_L = (I − γ_5)/2`, `P_R = (I + γ_5)/2` on the
spinor subspace. Test on `|0⟩` and `|1⟩` Bloch eigenstates.

Returns:
```python
{
    "P_L_qt": qt.Qobj,
    "P_R_qt": qt.Qobj,
    "bloch_z_under_P_L": float,             # ≈ +1 on |0⟩
    "bloch_z_under_P_R": float,             # ≈ −1 on |1⟩
    "opposite_signs": bool,
}
```

### `landauer_work_bound(p_bit: float, n_cycles: int = 1) -> dict`

Measurement-feedback-erasure cycle on a biased classical bit. Reports extracted
work and the Landauer bound `H(p) · kT · ln 2`.

Returns:
```python
{
    "p_bit": float,
    "entropy_bits": float,                  # H(p) = −p log2 p − (1−p) log2(1−p)
    "work_extracted_kT": float,             # ∈ [0, H(p) ln 2]
    "landauer_bound_kT": float,             # H(p) · ln 2
    "efficiency": float,                    # work / bound ∈ [0,1]
    "n_cycles": int,
}
```

### `decoherence_free_subspace_projector(noise_basis: str) -> dict`

Projector onto the DFS of a single-basis dephasing channel (`"z"` or `"x"`).

Returns:
```python
{
    "noise_basis": str,
    "dfs_dimension": int,                   # ≥ 1
    "dfs_projector_qt": qt.Qobj,
    "sample_dfs_state_qt": qt.Qobj,
    "invariance_error": float,              # ||D[L] ρ|| ≈ 0
}
```

### `petz_recovery(noise_basis: str, post_channel_rho_qt) -> dict`

Petz dual `ℛ_σ(ρ_out) = σ^{1/2} ε†(σ_out^{−1/2} ρ_out σ_out^{−1/2}) σ^{1/2}`
recovery of a pre-channel state estimate.

Returns:
```python
{
    "noise_basis": str,
    "recovered_rho_qt": qt.Qobj,
    "fidelity_to_input": float,
    "recovery_improves": bool,              # td(recovered, input) < td(post, input)
}
```

### `connes_distance(rho_a_qt, rho_b_qt) -> float`

Connes distance `sup { |φ_a(a) − φ_b(a)| : a ∈ A, ‖[D, a]‖ ≤ 1 }` between two
state functionals on the spectral triple `(A, H, D)`. Used as a candidate
distinguishability metric across reduction shells.

### `principal_bundle_reduction_chain() -> dict`

Candidate nested-subgroup chain `GL(n,C) → O(n) → SO(n) → U(n) → SU(n) → Sp(n)`
with constructive admissibility witnesses at each step. NOT an entropy stack.

Returns:
```python
{
    "steps": [
        {"from": "GL(n,C)", "to": "O(n)",  "witness": <obj>, "is_admissible": bool},
        {"from": "O(n)",    "to": "SO(n)", "witness": <obj>, "is_admissible": bool},
        {"from": "SO(n)",   "to": "U(n)",  "witness": <obj>, "is_admissible": bool},
        {"from": "U(n)",    "to": "SU(n)", "witness": <obj>, "is_admissible": bool},
        {"from": "SU(n)",   "to": "Sp(n)", "witness": <obj>, "is_admissible": bool},
    ],
    "z3_unsat_on_reversed_order": bool,     # structural ratchet signature
}
```

### `bipartite_entropy_family(rho_AB_qt) -> dict`

The signed bipartite entropy family on a 4-qubit state split A=(q0,q1), B=(q2,q3).

Returns:
```python
{
    "S_A": float, "S_B": float, "S_AB": float,
    "S_A_given_B": float,                   # S(AB) − S(B); SIGNED
    "mutual_information_AB": float,         # S(A) + S(B) − S(AB)
    "coherent_information_A_to_B": float,   # S(B) − S(AB); SIGNED
}
```

### `tool_manifest() -> dict`

`{tool_name: {used: bool, load_bearing: bool, reason: str}}`. At least one
non-numpy tool with `load_bearing=True`.

### `sidequest_claim_boundary() -> dict`

```python
{
    "classification": "side_quest_only",
    "admission_scope": "noncanonical_exploration",
    "promotion_allowed": False,
    "claim_ceiling": "<plain string>",
}
```

## Doctrine constraints

- pytorch is primary numeric. numpy only for tool bridging.
- `qt.mesolve` for Lindblad. All flat 16×16 Qobjs get `dims=[[2,2,2,2],[2,2,2,2]]`.
- Pure-math identifiers only. No persona/role names, no Jungian/IGT labels, no
  thermodynamic-cycle persona names (Carnot, Szilard) in variable or function
  names. The information-erasure cycle primitive is `landauer_work_bound`.
- No hash-style distinctness (`%`, `hash()`, `prime tests`) to manufacture probe
  separation. Distinctness must come from the algebraic structure of the
  channels/operators applied.
- Every tool listed in `tool_manifest` must actually be invoked in some primitive.

## Banned identifiers (auto-reject contamination)

`axis`, `Ax0`, `Ax1`..`Ax6`, `engine`, `engine_stage`, `Engine A`, `Engine B`,
`Type 1`, `Type 2`, `gstack`, `g_stack`, `terrain`, `Ti`, `Te`, `Fi`, `Fe` (as
function/operator names — the math objects keep their literal names like
`dephasing_channel`), `prime_resonance`, `prime_score`, `hexagram`,
`stage_to_hexagram`, `Carnot`, `Szilard`, `IGT`, `I_Ching`, `Jung`.

The math operations these aliased are kept — under their math names.

## How candidates are tested

The runner imports the module and calls each function. Pass/fail criteria are
not in this file. What the candidate sees is the function contract and the
banned-identifier list; what the runner checks is hidden.
