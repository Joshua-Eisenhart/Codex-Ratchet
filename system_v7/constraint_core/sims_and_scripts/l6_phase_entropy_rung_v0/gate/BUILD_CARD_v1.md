# BUILD CARD v1 — gate lane, l6_phase_entropy_rung_v0

Lane: THE GATE (code only). Ceiling: `classification="scratch_diagnostic"`, `promotion_allowed=false` everywhere.
The gate computes; it never adjudicates the rung. Receipts report what ran. Deterministic, seed 0.

## Deliverable

One file: `gate_runner.py` in THIS directory
(`/Users/joshuaeisenhart/Codex-Ratchet/system_v7/constraint_core/sims_and_scripts/l6_phase_entropy_rung_v0/gate/`).

When run with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 gate_runner.py` it must:

1. consume the inputs below,
2. compute the candidate behaviour pool, per-candidate collapsed-demand-edge mass `L_D` per family,
   survivors, partition-refinement frontier, and coface gradient receipts by IMPORTING the v0.5 engine,
3. execute ALL ordered set-partitions of the 4 active demand families (order-open law),
4. run the three controls IN CODE (phase-erasure, behavioral source-attribution of the injected
   result-dependent functional, anti-by-construction with both sides executed),
5. run the SMT lane on z3 AND cvc5 with inputs derived from the actual finite tables,
6. emit `rung_receipt_v1.json` (byte-deterministic) and `gate_lane_receipt_v1.json` (run metadata),
7. print the frontier + a headline table to stdout,
8. exit 0 only if the internal validation checklist passes (fail-closed otherwise).

Do NOT create, modify, move, or delete ANY file outside this `gate/` directory.
Read everything else read-only. Never edit `ratchet_engine.py`, the surface, or the candidate lanes.

## Inputs (paths relative to this file's directory = `SCRIPT_DIR`; resolve via `Path(__file__).resolve().parent`)

- `RUNG_DIR = SCRIPT_DIR.parent`
- Surface: `RUNG_DIR/surface/surface_v1.json` — `row_blocks.fixture_observations` is a list of 18 rows,
  `row_id` 0..17 in order. Row fields: `a, shell_radius, purity, negativity, entropy_bits, orientation,
  chern_signed, radial_index, row_id, provenance`.
- Demands: `RUNG_DIR/surface/demand_families_v1.json` — `families.<name>.edges`, each edge has
  `row_i, row_j`. The 4 families and edge counts (assert them): `factorization_boundary`=16,
  `marginal_entropy_level`=72, `orientation_winding`=9, `shell_position`=72.
  `orientation_winding` is the phase/sign demand family.
- Candidate behaviours (landed): `RUNG_DIR/candidates/<fam>/behavior_v1.json` for
  `marginal-vn`, `noise-floor`, `orientation-augmented`. Detect landed families by globbing
  `RUNG_DIR/candidates/*/behavior_v1.json`; record every candidate directory WITHOUT a behavior file
  as `missing_recorded_not_blocking` (currently `coherence-functionals`, `relative-entropy-ref`,
  `weaker-carriers`).
- Noise-floor extras: `RUNG_DIR/candidates/noise-floor/variants_v1.json` (16-feature shared basis +
  33 weight vectors) and `RUNG_DIR/candidates/noise-floor/injection_manifest_v1.json`
  (consult ONLY AFTER behavioral detection, for the cross-check).
- v0.5 engine: `ENGINE_DIR = (SCRIPT_DIR / ".." / ".." / ".." / "ratchet").resolve()`
  (= `system_v7/constraint_core/ratchet`). `sys.path.insert(0, str(ENGINE_DIR))` then
  `from ratchet_engine import compute_frontier_cache, ordered_gate_hypotheses, execute_schedules,
  _pairwise_order_matrix, _decomposition_census, _normalise_partition, _sha_json`.
  IMPORT the frontier/schedule logic. Do NOT reimplement it.
- v0.5 schema for the fit report: `ENGINE_DIR/schemas/ratchet_order_open_run.schema.json`.

## Behavior-file schema normalization (the three landed lanes differ)

Normalize every variant to `{lane_family, variant_id, values[engine][row][channel]}` where
`engine ∈ {julia, jax, torch, numpy_control}` and values are float64 numpy arrays of shape (18, C):

- `marginal-vn`: `variants` is a LIST; `variant_id` key; `per_row_values[engine]` = flat list of 18
  floats (C=1). Declared julia sign per family edge lives at
  `induced_sign_predictions[family][k].sign_julia`.
- `noise-floor`: `variants` is a LIST; `per_row_values[engine]` = flat list of 18 floats (C=1).
  Declared signs: `sign_predictions[family].signs` (list in demand-edge order).
- `orientation-augmented`: `variants` is a DICT keyed by variant_id (iterate in sorted key order);
  `per_row_values[engine]` = list of 18 lists (C = number of channels). Declared fused sign:
  `induced_sign_predictions[family][k].fused_sign`; fusion rule is lexicographic over channels on the
  julia leg with tie tolerance 1e-12 (first channel with |diff| > tol sets the sign; all-within-tol → 0).

Deterministic candidate order: lane directories sorted alphabetically; within `marginal-vn` and
`noise-floor` keep file list order; within `orientation-augmented` sorted variant_id order.
Total variants expected: 8 (mvn) + 33 (nf) + 16 (oa) = 57 (assert).

## Part 1 — behaviour pool, L_D, survivors, frontier, gradients

- Canonical leg = julia. `SIGN_TOL = 1e-12`.
- Per variant, partition the 18 rows by union-find over pairs (i<j, fixed order): merge iff
  every channel satisfies `|v[i,c] - v[j,c]| <= SIGN_TOL`. `assignments = _normalise_partition(
  [root_of(r) for r in 0..17])`. `cell_count = len(set(assignments))`.
- `collapsed_demand_edges[family] = sum(assignments[i] == assignments[j] for each family edge)`.
  This is `L_D` per family (the coface: demanded edges the quotient collapses).
- Alias-collapse across the WHOLE pool: variants with identical `assignments` form one behaviour row
  `{id: "<lane_family>:<variant_id>" of first member, members: [...], lane_families: sorted set,
  assignments, partition_digest: _sha_json(list(assignments)), cell_count, variant_count,
  collapsed_demand_edges}`. Sort behaviour rows by `(cell_count, partition_digest)`, then assign
  `behaviour_index`.
- `family_order = ["factorization_boundary", "marginal_entropy_level", "orientation_winding",
  "shell_position"]`.
- `cache = compute_frontier_cache(behaviour_rows, family_order)` (16 masks). Survivors at a mask =
  rows with `L_D = 0` on every active family; frontier = partition-refinement minimal survivors —
  all computed by the imported engine code.
- `schedules = ordered_gate_hypotheses(family_order)` — assert len == 75 (all ordered set-partitions
  of 4 families).
- `schedule_receipts = execute_schedules(schedules, family_order, cache)` — this yields the coface
  gradient receipts (`gradient_hypotheses`, `drive_survivors`), per-step controls, and statuses from
  the imported v0.5 gradient law. Keep them verbatim.
- `order_matrix = _pairwise_order_matrix(family_order, cache)`;
  `census = _decomposition_census(schedule_receipts)`;
  convergence-or-divergence across orders = number of distinct `final_frontier_fingerprint` values
  over all 75 receipts plus the census rows (record both; no verdict prose).

## Part 2 — validity data (recorded, not adjudicated)

- Cross-substrate: per variant, `max |Δ|` over rows×channels for the three pairs
  julia/jax, julia/torch, jax/torch. Record the max and `lt_1e-9` boolean. `numpy_control` delta vs
  julia recorded separately as `comparison_only`.
- Declared-sign crosscheck: recompute julia-leg signs per family edge (scalar: sign of
  `v[j]-v[i]` with SIGN_TOL; vector: lexicographic fusion as above) and compare against each lane's
  declared signs (schema map above). Record mismatch counts per variant per family (expected 0;
  nonzero is recorded and appended to open_digs, not fatal).

## Part 3 — controls IN CODE

### 3a. Phase-erasure (must flip the phase-demand results)

- Phase classes: group the 18 rows by EXACT equality of the phase-erased projection
  `(a, shell_radius, purity, negativity, entropy_bits, radial_index, abs(chern_signed))`.
  Assert: exactly 9 classes, each of size 2, and the class pairs equal the 9
  `orientation_winding` edges as unordered pairs.
- Erased values per variant (julia leg): `v_er[r] = v[min(class_of(r))]` (channel-wise).
- Recompute per-family sign vectors and `L_D` on `v_er`.
- Requirements checked in code (fail-closed): every variant has ALL 9 `orientation_winding` signs = 0
  after erasure; every variant that carried k>0 of those edges before erasure has its carried count
  flip to 0 (record per-variant `carried_before`, `carried_after`, `flipped`).
- Also record `identity_under_erasure` per variant: `max|v_er - v| <= 1e-15`
  (true for phase-blind variants; a self-check, recorded).

### 3b. Behavioral source-attribution of the injected result-dependent functional

Scope: the 33 noise-floor variants (re-executable from the declared shared basis + weights) plus the
two in-code functionals of 3c. The gate's re-execution here is CONTROL machinery (numpy control-only);
it is not candidate evidence — candidate evidence stays the three-engine values.

- Shared basis (16 features, from `variants_v1.json.basis`, implement exactly):
  `[a, shell_radius, purity, negativity, entropy_bits, orientation, chern_signed, a*entropy_bits,
  shell_radius*purity, negativity*entropy_bits, a^2, entropy_bits^2, sin(pi*a), cos(pi*shell_radius),
  orientation*entropy_bits, 1.0]`.
- Reproduction precondition: `max|basis@w - recorded julia values| < 1e-9` per variant (record; if any
  variant fails, mark it `not_attributable` and skip it from the detector, recorded).
- Detector (identical for every subject): scales `SIGMas = [1e-3, 1e-2]`, `K = 8` draws per scale,
  fresh `rng = np.random.default_rng(0)` PER SCALE. For each draw: copy the row table; for each row in
  order, for each column in order `[a, shell_radius, purity, negativity, entropy_bits]`, add
  `sigma * rng.standard_normal()`. Obligation held fixed: `orientation`, `chern_signed`,
  `radial_index`, and the demand edge set are untouched.
- Per subject and scale, with `d0[e] = v0[row_j]-v0[row_i]` on the 9 `orientation_winding` edges and
  `dk` the same on draw k:
  - `baseline_carrying = all(|d0[e]| > SIGN_TOL)`
  - `margin = min |d0[e]|`
  - `input_response = max_{e,k} |dk[e] - d0[e]|`
  - `flip_fraction = (# of (e,k) with sign(dk[e]) != sign(d0[e])) / 72`
- FLAG rule (declared discrimination rule, applied uniformly): flagged iff `baseline_carrying` AND at
  ANY tested scale (`input_response > margin` AND `flip_fraction >= 0.05`). Meaning recorded in the
  receipt: the phase-edge carrying signal sits below the functional's input-response floor and the
  carried sign pattern scrambles under input perturbation with the obligation held fixed — the
  functional tracks results, not inputs.
- Record ALL metrics for ALL subjects at ALL scales (auditability of the threshold), the flagged set,
  and ONLY THEN load `injection_manifest_v1.json` and record
  `{manifest_injected_id, detected_ids, detected_contains_manifest_id, extra_flags}` as
  kill-attribution data.

### 3c. Anti-by-construction (both sides executed)

Construct in gate code, on the same 16-feature basis, and push BOTH through the identical detector:

- `gate_anti_result_copy`: weights = 1.0 on `entropy_bits` (index 4) and 1e-3 on `orientation`
  (index 5), zeros elsewhere. Expectation checked in code: FLAG = true.
- `gate_declared_arity_counter`: weights = 1.0 on `orientation` (index 5), zeros elsewhere.
  Expectation checked in code: FLAG = false.

Both executions and both outcomes go in the receipt. Expectation failure = internal validation
failure (exit nonzero).

## Part 4 — SMT lane (z3 AND cvc5; both must agree on every instance)

Structural claim: "no phase-blind functional (formal class: functions of the phase-erased row
projection) can carry the phase-sign demand edges." Solver inputs must be DERIVED from the actual
finite tables (compute the projection classes by comparing actual field values; never assert booleans).

- Phase-erased class map: `erased_class[r]` from exact-equality grouping of
  `(a, shell_radius, purity, negativity, entropy_bits, radial_index, abs(chern_signed))`
  (same map as 3a). Full class map: `full_class[r]` from the tuple WITH `orientation` and signed
  `chern_signed` retained.
- REAL instance, per family F: one integer variable per erased class; for each edge (i,j) in F assert
  `var[erased_class[i]] != var[erased_class[j]]`. Solve with z3 (`z3.Solver`, `Int`) and cvc5
  (python API, integer sort). Expected and checked fail-closed: `orientation_winding` → UNSAT on BOTH
  solvers. The other three families' results are recorded (expected SAT — a phase-blind functional can
  carry them; recorded, not adjudicated beyond the check that both solvers agree).
- ERASED CONTROL A ("drop the sign columns from the demand"): rebuild the demand under its own mining
  rule (`equal radial_index AND unequal orientation`) from the sign-dropped row table (columns
  `orientation` and `chern_signed` removed). The rule cannot fire → 0 edges → instance with no
  constraints → SAT on both solvers. Record `edge_count = 0`, `vacuous = true`, and the flip
  UNSAT→SAT.
- ERASED CONTROL B (non-vacuous flip; sign columns retained in the projection): same 9
  `orientation_winding` edges, but variables indexed by `full_class`. SAT expected on both solvers;
  record a witness model (class → value) from z3.
- Fail-closed checks: both controls SAT on both solvers; real `orientation_winding` UNSAT on both;
  z3 == cvc5 on every instance.
- Receipt records per instance: the row→class maps, per-edge class pairs, solver name/version,
  result strings.

## Part 5 — receipts and stdout

### `rung_receipt_v1.json` (byte-deterministic)

- Serialize with `json.dumps(receipt, sort_keys=True, indent=2) + "\n"`; NO timestamps, NO
  wall-clock, NO absolute paths (use paths relative to RUNG_DIR); floats emitted as computed.
- Write via create-or-require-identical: if the file exists and bytes differ → print
  `BYTE_IDENTITY_FINDING` and exit nonzero (results are append-only; a real change goes to
  `rung_receipt_v2.json` — do not implement auto-bump, fail instead).
- Top-level keys (all present): `schema_version` ("l6_phase_entropy_rung_receipt/1.0"),
  `classification` ("scratch_diagnostic"), `promotion_allowed` (false), `seed` (0),
  `claim_ceiling` ("scratch_diagnostic — the gate computes; receipts report what ran; no rung
  adjudication"), `inputs` (relative path + sha256 of surface, demands, every behavior file,
  variants, injection manifest), `candidate_families` (landed + missing_recorded_not_blocking),
  `validity` (Part 2), `behaviours` (rows incl. assignments + L_D), `frontier_cache_summary`
  (per mask: active_families, survivor_count, frontier_ids, frontier fingerprint),
  `gate_order_search` (all 75 schedule receipts verbatim, pairwise order matrix, decomposition
  census, distinct endpoint fingerprint count), `controls` (3a/3b/3c full records),
  `smt` (Part 4 full records), `kill_attribution` (per behaviour: families with L_D>0 and the edge
  counts; the 3b attribution block), `open_digs` (missing candidate families; any validity
  failures; any sign-crosscheck mismatches; nonempty by construction since three families are
  missing), `v0_5_schema_fit` (boolean + list of required keys the receipt lacks, computed against
  the actual schema file), `internal_validation` (name + pass for every fail-closed check).

### `gate_lane_receipt_v1.json`

Run metadata (timestamps allowed here): engine versions (z3, cvc5, numpy, python), the sha256 of the
`rung_receipt_v1.json` bytes this run computed, and `what_ran` (list of the stages). This file is
overwrite-allowed.

### stdout

- Headline table: one line per behaviour row — behaviour id, member count, cell_count, L_D per family
  (4 numbers), survivor-under-all-four yes/no.
- Frontier at the full mask (all 4 families active): ids + fingerprint. Frontier for each of the 75
  schedules is in the receipt; print the distinct-endpoint count and the census.
- Control lines: phase-erasure summary, detector flagged set + manifest cross-check, anti-by-
  construction outcomes.
- SMT lines: per instance solver results + agreement.
- Final line: `INTERNAL_VALIDATION: ALL PASS (n checks)` or the failing check name.

## Hard constraints

- Python: `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` (z3, cvc5, numpy present).
- Deterministic: seed 0 everywhere; two consecutive runs must be byte-identical on
  `rung_receipt_v1.json` (second run passes the create-or-require-identical check).
- Language discipline in receipt strings: survived/admitted/excluded/collapsed/carried/consistent-with;
  never causes/creates/drives/produces/generates/proves.
- No network. No new dependencies. Single file `gate_runner.py`. No writes outside `gate/`.

## STOP condition

Build `gate_runner.py`, run it twice with the sim-stack python from inside `gate/`, confirm exit 0
both times and `BYTE_IDENTITY` holds (second run must not raise), confirm both receipts exist, then
STOP. Do not commit. Do not touch anything else.
