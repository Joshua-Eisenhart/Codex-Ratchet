# Fresh Audit Verdict: geo_s3_alternative_probe_families_v0

Scope: fresh read-only audit of `geo_s3_alternative_probe_families_v0`. I did not build this packet. The only intended write from this audit is this `audit_verdict.md`; I did not `git add` or commit.

Calibrated bar used: `system_v6/receipts/audit_bar_calibration_20260610.md`. The binding bar keeps route genuineness, can-fail controls, erasure honesty, scratch ceilings, and capability-probe gates, while using exactness-class stability rather than blanket byte-stability.

Accepted ceiling if accepted: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. No formal admission, global S3 uniqueness, global stack uniqueness, bridge/axis claim, or canonical-by-process claim is accepted.

## Commands and Recomputations

- `git status --short -- system_v6/sims/geo_s3_alternative_probe_families_v0` returned `?? system_v6/sims/geo_s3_alternative_probe_families_v0/`.
- Read-only packet-validator logic:
  - command form used: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... validate(payload, julia) ...`
  - output: `{"errors": [], "read_only_validator_logic_ok": true}`.
  - I did not run `validate_geo_s3_alternative_probe_families_v0.py` via its CLI because `main()` writes `results/geo_s3_alternative_probe_families_v0_validator_results.json` at lines 134-135, which would violate the one-file audit write constraint.
- Strict source-backed validator:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_s3_alternative_probe_families_v0/results/geo_s3_alternative_probe_families_v0_envelope_results.json`
  - output: `{"ok": true, "result_json": "system_v6/sims/geo_s3_alternative_probe_families_v0/results/geo_s3_alternative_probe_families_v0_envelope_results.json"}`.
- Parent lineage recomputation matched the envelope for all listed parent files. Recomputed selected hashes:
  - S3 parent envelope: `3c407fc647856ea668d8055deb690198ffda3e9156de066be51be3792eaa7f00`.
  - S3/S4 mode parent envelope: `55c098fd6a6d1ddaa0e5257f9429a41a56d1cdd17e5fd4f2998ea2f76ae4e889`.
  - uniqueness map: `6c54eb010628d7c8f66f32ad417cb852a19fe36aa32bd916c7ce5440976e8dc2`.
- Anchor row hashes recomputed exactly:
  - `s3_parent_X_Y_Z_probe_row`: `c78f4187ac7a21a564dbe1bca112b15131599b9f69446583f1ef0a65bf7de88c`.
  - `s3_parent_tetrahedral_refinement_control_row`: `3ec254c7690a5c0c2715fd5db7be94aa7439c3f0d176a074e32dfd29781629bb`.
  - `s3_s4_parent_z_probe_classes`: `37d4cd5f077cba70a9f09aa17fefdb3aa226dd6501c7dc17b186b32e6b568550`.
- `rg -n "fixture" system_v6/sims/geo_s3_alternative_probe_families_v0` returned no hits.

## Q1 - Families Genuine

Source quote points:

- The source defines the committed Pauli XYZ family at `geo_s3_alternative_probe_families_v0.py:156-165`.
- The SIC tetrahedron effects are exact symbolic rows with `quarter / SQRT3` at `geo_s3_alternative_probe_families_v0.py:167-174`.
- The MUB XYZ effects are defined at `geo_s3_alternative_probe_families_v0.py:176-185`.
- The single-axis Z and random-frame null rows are defined at `geo_s3_alternative_probe_families_v0.py:187-202`.
- The Julia sidecar mirrors these rows in `geo_s3_alternative_probe_families_v0_julia.jl:37-65`.

Recomputed:

- SIC Bloch vectors are `(1,1,1)/sqrt(3)`, `(1,-1,-1)/sqrt(3)`, `(-1,1,-1)/sqrt(3)`, and `(-1,-1,1)/sqrt(3)`. Every pairwise Bloch dot is `-1/3`, so every qubit-state overlap is `(1 + dot)/2 = 1/3`.
- Exact ket representatives recomputed from the Bloch vectors also give every pairwise `|<a|b>|^2 = 1/3`.
- MUB bases checked as Z, X, and Y bases. Cross-basis overlap sets for `X-Y`, `X-Z`, and `Y-Z` are all exactly `{1/2}`.
- Single-axis Z is genuinely coarse: it has only the two Z projectors.
- The random-frame null is rank-deficient by construction and by recomputation: frame rank `3`, deficiency `1`.

Q1 result: the four named families are real finite probe families. Caveat C2 below applies to `B_mub_xyz`: it is genuine, but numerically identical to the committed Pauli XYZ IC family.

## Q2 - Battery

Source quote points:

- Frame rank, separation, quotient classes, and N01/order rows are computed in `compute_family_rows()` at `geo_s3_alternative_probe_families_v0.py:267-310`.
- Parent anchors are read from the S3 parent, S3/S4 mode parent, lifted IC rows, and uniqueness map in `anchor_rows()` at `geo_s3_alternative_probe_families_v0.py:327-362`.
- Build gates require anchor binding, all alternatives, z quotient match, co-survivors, exact ranks, quotient classes, SMT erased flips, Julia sidecar pass, no peer read, and one-to-one tool calls at `geo_s3_alternative_probe_families_v0.py:525-544`.

Recomputed:

```json
{
  "frame_ranks_recomputed": {
    "A_sic_tetrahedron": 4,
    "B_mub_xyz": 4,
    "C_single_axis_z": 2,
    "D_random_frame_null": 3,
    "committed_pauli_xyz": 4
  },
  "survival_flags": {
    "A_sic_tetrahedron": true,
    "B_mub_xyz": true,
    "C_single_axis_z": false,
    "D_random_frame_null": false,
    "committed_pauli_xyz": true
  }
}
```

One quotient recomputation: `C_single_axis_z` identifies exactly the transverse half-axis states:

```json
{
  "classes_by_state_label": [
    ["+z"],
    ["-z"],
    ["+x", "+y", "-x", "-y"]
  ],
  "identical_state_pairs": [
    ["+x", "+y"],
    ["+x", "-x"],
    ["+x", "-y"],
    ["+y", "-x"],
    ["+y", "-y"],
    ["-x", "-y"]
  ]
}
```

Q2 result: the battery is genuine. Separation matrices are present for all family pairs; frame-rank rows match `d^2=4` where claimed; single-axis and null controls fail as expected; parent anchors and lifted IC anchors are hash-bound.

## Q3 - Expected Co-Survival and Discrimination

The packet reports the honest co-survival case in `structural_answer`: SIC, MUB, and committed Pauli XYZ are listed under `ic_co_survivors`, while single-axis Z is listed as the z-quotient reproducer and the null is rank deficient.

Recomputed discriminating row:

```json
{
  "N01_nonparallel_counts": {
    "A_sic_tetrahedron": 6,
    "B_mub_xyz": 12,
    "C_single_axis_z": 0,
    "D_random_frame_null": 6,
    "committed_pauli_xyz": 12
  },
  "committed_equals_mub_effect_rows": true
}
```

Interpretation:

- SIC and MUB co-survive informational completeness and six-shell separation.
- SIC and MUB tie on full six-state separation and frame rank. SIC differs from MUB/committed on the recomputed nonparallel-pair count (`6` vs `12`), but that is not a committed projective measurement-order reproduction row.
- MUB and committed Pauli XYZ tie exactly because their effect rows are identical. This is an exact alias/tie at the IC-family level, not a discriminating alternative.
- Single-axis Z fires the failure control: it separates `9/15` pairs, rank `2`, and collapses the four transverse half-axis states.
- The null deficiency is computed: rank `3`, deficiency `1`, with `+y` and `-y` collapsed.

Q3 result: the anti-collapse finding is mostly honest, but with Caveat C2 and C3. The correct uniqueness-map implication is:

> Co-survivors exist at the IC/separation level. SIC is a genuine IC co-survivor. MUB XYZ is an exact tie/alias with the committed Pauli XYZ IC family. The committed stack is not uniquely identified by IC/separation alone; in this packet it is distinguished only by the assembled parent structure of IC family plus z-coarsening plus committed projective N01/order behavior, not by a single alternative-family row.

## Q4 - Shape Repair and Validators

The lane records use the standard result shape: each engine record includes `source_path`, `source_sha256`, `result_path`, `result_sha256`, `packages_used`, `aligned_packages_load_bearing`, `reads_peer_result`, `tool_manifest`, `tool_integration_depth`, and `tool_calls`; this is enforced by the validator at `validate_geo_s3_alternative_probe_families_v0.py:51-55`.

Validator evidence:

- Read-only validator logic returned `errors=[]`.
- Strict source-backed validator returned `ok=true`.

Shape caveat: I do not find literal `{subtree, hash}` pairs in this packet. The shape repair is accepted as standard lane shape plus source/result hashes and validator acceptance, not as a commit-level proof that a previous edit was shape-only.

## Q5 - Standard Hygiene

- Honest mode: `engine_contract.mode` is `julia_canon_plus_jax_diagnostic`; lanes are `["julia","jax"]`; PyTorch is explicitly omitted because no graph/network/autograd claim path is scoped. Source lines `562-571` emit this.
- Parent lineage: present and recomputed on disk; hashes match.
- Real Julia leg: Julia source computes family rows, ranks, QuantumOptics positivity receipt, and Julia Z3 erased-flip proof at `geo_s3_alternative_probe_families_v0_julia.jl:37-190`.
- z3/cvc5 with erased flip: envelope reports both `verdict="sat"`, `erased_verdict="unsat"`, `erased_flip_detected=true`, and `asserted_precomputed_boolean=false`.
- Capability receipts: Python versions are recorded for `python=3.13.6`, `sympy=1.14.0`, `z3=4.16.0`, `cvc5=1.3.3`, `jax=0.10.1`, `torch=2.11.0`, `qutip=5.2.3`; Julia receipt records `julia_version=1.12.6`, project `system_v5/julia_carrier`.
- One-to-one tool calls: `claim_path_tools` and `tool_calls` both have the five tools `sympy`, `z3`, `cvc5`, `QuantumOptics`, and `Z3`.
- Seeds: envelope records `python=20260611` and `julia=20260611`.
- No fixture wording: repo search returned no hits under this packet.
- Ceilings: `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`; blocked consumers include formal admission, global S3 uniqueness, global stack uniqueness, bridge/axis claims, and canonical-by-process status.

## Named Caveats

- C1 - Untracked packet state: `git status` reports the whole target directory as untracked. This audit accepts current on-disk evidence only; it is not committed repo truth.
- C2 - MUB alias/tie: `B_mub_xyz` is numerically identical to `committed_pauli_xyz` in the emitted effect rows. Treat it as an exact IC-level tie/alias with the committed Pauli XYZ family, not as an independent family that discriminates the committed IC anchor.
- C3 - Composite-row assembly: `families_reproducing_full_composite_pattern` is empty, and the source formula requires a single family to be both IC, z-quotient-matching, and committed-order-reproducing. The accepted uniqueness implication is therefore assembled from parent rows, not demonstrated by one family row reproducing the full committed composite pattern.
- C4 - Shape-only proof limit: standard lane shape and source/result hashes are present and validators pass, but I found no literal `{subtree, hash}` pair proof or committed diff proving the prior repair was shape-only.
- C5 - Validator CLI write constraint: the packet validator's CLI writes a timestamped validator result. I ran the validator logic read-only and ran the strict source-backed validator normally.

## Verdict

VERDICT: `GENUINE-WITH-CAVEATS`.

The packet genuinely demonstrates the expected co-survivor case at the named diagnostic ceiling: SIC and MUB/Pauli XYZ co-survive IC rank and six-state separation; single-axis Z fails separation while reproducing the z-probe quotient classes; the random-frame null is rank deficient; parent anchors and lifted IC anchors are hash-bound; z3/cvc5 and Julia Z3 erased controls are present; and strict source-backed validation passes.

The result must not be promoted to "S3 unique" or "stack unique." The strongest accepted statement is: named S3 probe-family alternatives have been compared at `scratch_diagnostic` ceiling; IC/separation alone admits co-survivors; the committed stack is distinguished only by the assembled IC plus z-coarsening plus committed projective N01/order structure under this battery, with MUB XYZ tying the committed Pauli IC row exactly.

Ceiling restated: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. No formal admission, global S3 uniqueness, global stack uniqueness, bridge/axis claim, or canonical-by-process status is accepted.
