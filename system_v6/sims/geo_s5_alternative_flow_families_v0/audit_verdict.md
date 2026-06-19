# Audit Verdict - geo_s5_alternative_flow_families_v0

auditor: codex1_cross_backend
audit_date: 2026-06-11
scope: read-only audit except this file
calibration: system_v6/receipts/audit_bar_calibration_20260610.md
status: PASS_WITH_CAVEATS
ceiling: scratch_diagnostic only; promotion_allowed=false; formal_admission_allowed=false

## Sources Checked

- `system_v6/sims/geo_s5_alternative_flow_families_v0/geo_s5_alternative_flow_families_v0.py`
- `system_v6/sims/geo_s5_alternative_flow_families_v0/geo_s5_alternative_flow_families_v0_julia.jl`
- `system_v6/sims/geo_s5_alternative_flow_families_v0/results/geo_s5_alternative_flow_families_v0_envelope_results.json`
- `system_v6/sims/geo_s5_alternative_flow_families_v0/results/geo_s5_alternative_flow_families_v0_julia_results.json`
- `system_v6/sims/geo_s5_alternative_flow_families_v0/results/geo_s5_alternative_flow_families_v0_validator_results.json`
- Parent envelopes for `geo_s5_terrain_flows_v0`, `ratchet_s6_terrain_sweep_v0`, `terrain_exact_mirror_finder_v0`, `geo_s2_s5_mode_sweep_v0`
- `system_v6/receipts/stack_uniqueness_map_20260611.md`

Short source quotes used:

- Packet ceiling: "It is a scratch diagnostic" (`geo_s5_alternative_flow_families_v0.py:4-6`).
- Null construction intent: "Deterministic sign-preserving shuffle" (`geo_s5_alternative_flow_families_v0.py:290-293`).
- Calibration bar: "Byte-stability -> EXACTNESS-CLASS STABILITY" (`audit_bar_calibration_20260610.md:7-8`).
- Uniqueness map ceiling: "The evidence does not support \"the unique stack.\"" (`stack_uniqueness_map_20260611.md:13-17`).

## Q1 - Alternatives Genuine

Result: PASS_WITH_CAVEAT.

The four alternatives are actually constructed and wired into the packet:

- `A_gradient_zero_antisymmetric`: `gradient_family()` builds eight explicit affine `A,b` rows (`geo_s5_alternative_flow_families_v0.py:262-272`).
- `B_hamiltonian_only`: `hamiltonian_family()` builds skew-generator rows using `skew(...)` (`geo_s5_alternative_flow_families_v0.py:275-287`, `218-220`).
- `C_shuffled_coefficients_null`: `shuffled_null_family(...)` rotates positive and negative magnitude lists and rebuilds `A,b` (`geo_s5_alternative_flow_families_v0.py:290-317`), then deliberately overrides `Ni_Pit_L` and `Ni_Source_R` (`318-321`).
- `D_bounded_quadratic_non_affine`: `quadratic_family(...)` marks `Se_Funnel_L` non-affine and adds `(1 - r_x^2 - r_y^2 - r_z^2) * [r_x^2/10, 0, 0]` (`325-334`).

Recomputation:

- `Se_Funnel_L` null row is a genuine sign-pattern-preserving shuffle: committed signs and null signs both equal `[-,-,+,+,-,-,-,+,-,0,0,0]`, and values changed.
- Named caveat: `Ni_Pit_L` and `Ni_Source_R` are not pure sign-slot shuffles after the deliberate override; `Ni_Pit_L` changes off-diagonal nonzero sign slots to zero and sets `b_z=-4/5`. This does not kill Q1, but the null family should be described as "sign-shuffled with explicit Ni validity-kill overrides," not as uniformly sign-shuffled in every row.

## Q2 - Like-For-Like Battery

Result: PASS_WITH_CAVEATS.

The implemented battery is like-for-like against the committed family on:

- quotient-survival matrix / `56/56` anchor (`quotient_matrix`, `family_battery`, lines `410-429`, `495-560`);
- leakage classes and S6 class names (`leakage_class`, `s6_class`, lines `346-359`);
- fixed-point/basin rows (`fixed_survival`, lines `362-396`);
- mirror solve-space classification (`family_pair_mirror`, lines `459-492`);
- N01 `Fi_R_x` order-gap rows (`family_battery`, lines `503-527`);
- committed parent exact controls (`committed_parent_exact_control`, lines `732-758`).

Recomputations:

- For `B_hamiltonian_only`, quotient row recomputed to `ordered_pairs=56`, `distinguished_pairs=56`, `collapsed_pairs=[]`, hence quotient survival is true.
- For the same family, mirror row recomputed to false: all four mirror classes are `S1_continuum_pure_rotation_axis_flip`, which fails the committed mirror-structure comparison for `Ni` and `Si`.
- Committed anchor row byte-exact checks recomputed true:
  - committed `Se_Funnel_L` order-gap norm squared = parent `4/25`;
  - committed quotient distinguished-pair count = parent `56`.

Named caveat:

- The envelope names the Python lane `jax`, but the claim path is Python symbolic/SMT using `sympy`, `z3`, and `cvc5`, not actual JAX. This is lane-label drift, not a numerical battery failure.

## Q3 - Survival Matrix

Result: PASS.

Recomputed survival/death matrix:

| Alternative | Validity | Affine | Quotient 56/56 | Mirror | N01 gaps match committed | Full signature | Killing row |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A_gradient_zero_antisymmetric | true | true | false | false | false | false | quotient_survival_56 |
| B_hamiltonian_only | true | true | true | false | false | false | mirror_structure |
| C_shuffled_coefficients_null | false | true | true | false | false | false | validity |
| D_bounded_quadratic_non_affine | true | false | true | false | false | false | affine_validity |

Death recomputed:

- `C_shuffled_coefficients_null` dies at `validity`; recomputed `Ni_Pit_L` fixed radius squared is `16`, so `valid_for_family=false`.

Survival recomputed:

- `B_hamiltonian_only` co-survives the valid affine quotient row: `56/56` ordered pairs distinguished, but it dies later at `mirror_structure` and also fails N01 full-signature matching.

Teeth check:

- The null model dies. It does not survive the battery; the killing row is `validity`.
- The battery has teeth against at least three qualitatively different failures: quotient collapse (`A`), physical validity failure (`C`), and affine-row failure (`D`). It also preserves a named co-survivor (`B`) without merging it into the committed family.

Headline answer:

- No named alternative reproduces the full committed signature. `full_signature_alternative_survivors=[]`; `any_alternative_reproduces_full_committed_signature=false`.

## Q4 - Standard / Process

Result: PASS_WITH_CAVEATS.

Checks accepted:

- Honest ceiling: result states `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Parent lineage: recomputed `git rev-parse HEAD:<envelope_path>` matched all recorded parent envelope blobs for S5 terrain, S6 sweep, mirror finder, S2/S5 sweep, and the uniqueness map.
- Real Julia leg: Julia source uses `Z3`, writes its own result path, and result records `reads_peer_result=false`.
- Scratch Julia Z3 recomputation: positive survivor-count assertion returned `sat`; erased/wrong count returned `unsat`.
- z3/cvc5 erased flip: Python recomputation returned real `unsat` and erased `sat` for both solvers on the committed `Se_Funnel_L/Fi_R_x` zero-gap assertion.
- Capability receipts: Python, SymPy, z3, and cvc5 versions/smoke checks are recorded.
- One-to-one tool calls: recorded calls are exactly `sympy`, `z3`, `cvc5`, `Z3`.
- No fixture wording: `rg "fixture|FIXTURE|mock|placeholder" system_v6/sims/geo_s5_alternative_flow_families_v0` returned no hits.
- Seeds: deterministic seed ledger records `python_symbolic_seed=2026061117`, `null_shuffle_seed=2026061117`, `rng_sampling=false`.
- Anti-collapse: `B_hamiltonian_only` is named as a valid affine quotient co-survivor and not merged into the committed family.

Named caveats:

1. `jax` lane label is inaccurate; the packet's Python lane is symbolic/SMT, not JAX.
2. Julia package names are recorded, but Julia package versions are not.
3. Existing validator result is green, but I did not rerun the validator because its main writes `validator_results.json` and the audit is read-only except this file.
4. The packet directory is currently untracked in git status, so the packet itself is local evidence until committed.
5. The result does not have an explicit `uniqueness_map_implication` field. The implication is recoverable from the uniqueness map and packet answer, but should be made explicit in a future builder patch.
6. Null-family wording should preserve the Ni override caveat: the family is not uniformly pure sign-slot shuffle after the explicit validity-kill overrides.

## Verdict

VERDICT: PASS_WITH_CAVEATS at `scratch_diagnostic` ceiling.

The packet supports this bounded statement:

> For the four named S5 alternative flow families tested here, none reproduces the full committed eight-terrain signature under the implemented battery. One alternative, `B_hamiltonian_only`, co-survives the valid affine quotient row but fails mirror-structure and N01/full-signature rows. The null model dies on validity, so the battery has teeth.

The packet narrows the S5 uniqueness-map gap row "alternative terrain flow families / alternative Lindblad-Hamiltonian generator sets / alternative basin/fixed-point families" for these four named families only. It does not prove global S5 terrain-generator uniqueness, minimality of the eight-generator set, global stack uniqueness, bridge/axis closure, or formal admission.
