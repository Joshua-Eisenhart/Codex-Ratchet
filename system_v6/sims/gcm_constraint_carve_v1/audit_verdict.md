# Independent Audit Verdict - gcm_constraint_carve_v1

audit_mode: independent fresh read-only audit; live repo read-only except this file
freshness_tier: TIER-3 annotation-verify with independent scratch recomputation
auditor: Codex cross-backend auditor
audit_date: 2026-06-12
standards_codex: system_v6/receipts/audit_standards_codex_v1.md
binding_checkpoint: ab6305a87 / system_v6/receipts/hermes_architecture_corrections_20260612.md
v0_fail_contract: e5d0065a6 / system_v6/sims/gcm_constraint_carve_v0/audit_verdict.md

Bottom line: VERDICT = FAIL AS HERMES CHECKPOINT, with the failure at the validator-tooth gate.

The built carve itself recomputes as terrain-blind C1-C3 over the current carrier and pins: 125 candidates, 33 density subcarrier rows, 16 survivors, 8 quotient classes; v0-C4 regression gives 8 survivors, 4 quotient classes, and removes [31, 33, 41, 43, 81, 83, 91, 93]. Source honesty, downstream-only terrain readout, identity-leak reporting/exclusion, controls, three backend agreement, and G.2a mostly pass at the bounded packet level.

The checkpoint still does not earn "the first real candidate substrate" because the packet validator does not independently fail on a source-only terrain-framed admissibility injection. It fails only after the mutated result is regenerated and the emitted terrain guard goes red. A validator that trusts stale emitted guard fields is not the checkpoint's promised tooth.

Accepted ceiling: still `scratch_diagnostic`, carrier-and-pins-relative, `promotion_allowed=false`, `formal_admission_allowed=false`, not THE manifold, not terrain-atlas admission, not a `gcm_object_id` source for substrate-first enforcement.

## Binding Question

Hermes checkpoint, adopted verbatim:

> "Does gcm_constraint_carve_v1 land terrain-blind, with source-honest C, no-identity-leak independence, downstream-only terrain readout, and a validator that would fail if terrain knowledge enters admissibility?"

Answer: no. It lands most of the math and process content, but not the validator independence tooth.

## Criterion Results

| Criterion | Verdict | Finding |
|---|---|---|
| 1. Terrain-blind admissibility path | PASS_WITH_SCOPE | Current source path uses only finite grid candidates, density, x/z active probe, and order-gap helpers for active C. Candidate construction itself does not encode terrain/atlas labels. |
| 2. Source-honest C | PASS_WITH_SCOPE | C1-C3 are literal executable local adapter pins whose build-card source lines say the predicates they execute. They are not owner-source theorem predicates. |
| 3. No-identity-leak | PASS_WITH_CAVEAT | `identity_leak_detected=true` means the positive control fired: candidate id, coordinate tuple, and direct constraint fingerprint recover survived/killed at 1.0. After excluding identity keys, best predictor is `radius_squared` at 0.968, so the implemented independence tooth passes `< 1.0`, narrowly. |
| 4. Downstream-only terrain readout | PASS | The 8 quotient classes are computed before the readout. Terrain/region labels are post-carve fields with `can_affect_survival=false`, `survival_inputs=[]`, and `terrain_atlas_not_claimed=true`. |
| 5. Validator teeth and G.2a | FAIL_WITH_PARTIAL_TOOTH | G.2a passes. Regenerated mutated results fail. But direct source injection plus validator on existing emitted results stays green, so the validator itself does not independently catch terrain knowledge entering admissibility source. |
| 6. Arithmetic, existence probes, controls | PASS | Fresh recomputation and scratch reruns reproduce 16/8 and v0 regression 8/4; empty-C, overconstrained, erasure-bite, probe-scramble, and blindness controls fire. |
| 7. M(C,t) step | PRESENT_WITH_CAVEAT | A local C5 downstream hook recomputes 8 survivors and 4 quotient classes. This is a local adapter hook inside a scratch diagnostic, not full M(C,t) admission. |

## Evidence Paths

- Packet source: `system_v6/sims/gcm_constraint_carve_v1/gcm_constraint_carve_v1_common.py`
- Packet validator: `system_v6/sims/gcm_constraint_carve_v1/validate_gcm_constraint_carve_v1.py`
- Boundary helper: `scripts/builder_audit_boundary.py`
- Build card: `system_v6/sims/gcm_constraint_carve_v1/build_card.md`
- Main result: `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_results.json`
- Envelope result: `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_envelope_results.json`
- Existing validator result: `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_validator_results.json`

## Terrain-Blind Path

Current active C:

- `C1_finite_density_carrier`
- `C2_probe_distinguishability_xz_local_adapter_pin`
- `C3_persistence_n01_order_gap`

The source path is:

- `candidate_space()` enumerates `GRID_VALUES=(-1.0,-0.5,0.0,0.5,1.0)` as `(x,y,z)` records with `candidate_id`, `coord`, `coord_scaled`, and `radius_squared`; no terrain/atlas labels are constructed.
- `constraint_passes()` dispatches active C only to `is_density_candidate`, `active_probe_nonzero`, and `persistence_order_ok`.
- `build_quotient()` buckets survivors only by `probe_signature(coord, ("sigma_x", "sigma_z"))`.
- `post_carve_region_readout()` is called only after quotienting and returns `can_affect_survival=false` and `survival_inputs=[]`.
- `v0_rejected_C4_terrain_framed_residency_variant` is available only through `v0_regression_row()`, not `final_constraint_ids()`.

Terrain/atlas words exist in the file in the forbidden-token guard, the injected bad control, the downstream readout, and the rejected v0 regression explanation. I found no terrain/atlas term in the active survival predicates or candidate-space construction.

## Source-Honest C

The v0 citation problem is repaired by demotion and local pinning, not by pretending these are owner-source theorem lines.

- C1: build card says `C1_finite_density_carrier` accepts candidates on `GRID_VALUES={-1,-1/2,0,1/2,1}` with `x*x + y*y + z*z <= 1`; source executes `is_density_candidate(coord)`.
- C2: build card says active probe pair `(2*x, 2*z)` is not `(0,0)`; source executes `probe_signature(coord) != (0,0)` with `PROBE_FAMILY=("sigma_x","sigma_z")`, and explicitly marks this as a local adapter pin/demotion.
- C3: build card says `D_z after R_x` and `R_x after D_z` active x/z probe signatures differ; source computes both signatures through `dz_after_rx`, `rx_after_dz`, and `order_gap`, with pass threshold `>= 0.5` over integer-scaled signatures.

C4 is split out of active C. The validator checks active C length 3 and rejects `v0_rejected_C4_terrain_framed_residency_variant` inside `constraint_family_C`.

## No-Identity-Leak

The identity leak is the designed positive control:

- identity-inclusive features:
  - `candidate_id`: 1.0
  - `coord_tuple`: 1.0
  - `direct_constraint_fingerprint`: 1.0
- identity-excluded best predictor:
  - `radius_squared`: 0.968

Meaning: direct row identity and equivalent fingerprints can perfectly recover survived/killed, and the packet reports and excludes them. After exclusion, the best coarse feature still predicts 121/125 labels, so the independence result is narrow but not a perfect identity leak under the current standard.

Caveat: the implemented leak probe scores survived/killed over the full candidate set. It does not separately score whether Q0-Q7 quotient class labels are recoverable from identity fields among survivors. I did not find quotient construction reading `candidate_id`; it buckets by probe signature, but a future stronger quotient-class independence check would be cleaner.

## Downstream Readout

The packet does not compute an atlas match inside the carve. The downstream readout classifies the eight quotient signatures as:

- `mixed_active_probe_region`: 4 classes
- `x_axis_active_region`: 2 classes
- `z_axis_active_region`: 2 classes

This is a post-carve number/readout. The honest language is: `8 quotient classes`, plus partial post-carve probe-region labels. It is not a terrain-atlas match and not terrain admission.

## Validator-Tooth Finding

Two scratch tests were run.

### Regenerated Mutated Result

Scratch root: `/tmp/gcm_carve_v1_audit.5Jw5WC`

Procedure:

1. Copied `system_v6/sims/gcm_constraint_carve_v1/` and required scripts to scratch.
2. Ran common, JAX, PyTorch, Julia, envelope writer, packet validator, and pytest in scratch.
3. Mutated C2 source text to include `terrain label must be atlas-compatible before survival`.
4. Regenerated the common result.
5. Ran the validator.

Clean scratch before mutation:

```text
common ok=true
jax ok=true
pytorch ok=true
julia ok=true
envelope ok=true
validator ok=true errors=[]
pytest: 5 passed
```

After mutation and regeneration:

```json
{
  "common_all_pass": false,
  "terrain_guard": {
    "clean": false,
    "errors": [
      "C2_probe_distinguishability_xz_local_adapter_pin: forbidden predicate token 'terrain'",
      "C2_probe_distinguishability_xz_local_adapter_pin: forbidden predicate token 'atlas'"
    ]
  },
  "validator": {
    "ok": false,
    "errors": [
      "common packet: terrain-blindness guard failed",
      "common packet: all_pass is not true",
      "terrain blindness guard failed"
    ]
  }
}
```

This proves the builder path recomputes a real guard and the emitted-result validator fails after guard regeneration.

### Source-Only Injection

Scratch root: `/tmp/gcm_carve_v1_validator_tooth.WBsSHC`

Procedure:

1. Copied the packet and required scripts to scratch.
2. Mutated the same C2 source text to include terrain/atlas wording.
3. Ran `validate_gcm_constraint_carve_v1.py` without regenerating result JSONs.

Result:

```json
{
  "validator_ok": true,
  "errors": []
}
```

This is the checkpoint failure. The validator reads the existing result/envelope and checks their emitted `terrain_blindness_guard.clean`; it does not independently recompute `blindness_guard()` from current source, rescan `constraint_family_C`, or compare `predicate_text_sha256` against a source recomputation. Therefore source terrain knowledge can enter admissibility source while a stale emitted guard lets the validator remain green.

Required repair before pass: validator must recompute the forbidden-token guard from current source, or compare a freshly recomputed predicate-text hash/guard errors against the emitted packet, and fail on mismatch. The repair should still preserve G.2a by accepting this independent audit file through `scripts/builder_audit_boundary.py`.

## Arithmetic And Controls

Fresh in-process recomputation against live source returned:

```json
{
  "all_pass": true,
  "candidate_count": 125,
  "density_count": 33,
  "active_C": [
    "C1_finite_density_carrier",
    "C2_probe_distinguishability_xz_local_adapter_pin",
    "C3_persistence_n01_order_gap"
  ],
  "survivor_count": 16,
  "quotient_class_count": 8,
  "kill_counts_by_constraint": {
    "C1_finite_density_carrier": 92,
    "C2_probe_distinguishability_xz_local_adapter_pin": 5,
    "C3_persistence_n01_order_gap": 12
  },
  "v0_regression_survivor_count": 8,
  "v0_regression_quotient_class_count": 4,
  "removed_by_v0_C4_candidate_ids": [31, 33, 41, 43, 81, 83, 91, 93],
  "identity_leak_detected": true,
  "identity_leak_excluded_best_accuracy": 0.968,
  "payload_validation_errors": []
}
```

Controls recomputed:

- empty-C: 125 survivors, degenerate/no manifold.
- overconstrained-C: 0 survivors, all killed.
- C1 erasure: 96 survivors, bite true.
- C2 erasure: 20 survivors, bite true.
- C3 erasure: 28 survivors, bite true.
- probe scramble: quotient moved true.
- blindness control: injected variant caught true.

Cross-backend scratch rerun:

- Python common: ok true.
- JAX lane: ok true.
- PyTorch lane: ok true.
- Julia lane: ok true.
- Envelope writer: ok true.
- Validator on clean scratch: ok true.
- Pytest on clean scratch: 5 passed.

## M(C,t) Step

The packet includes `M_C_t_hook` as a downstream local adapter step:

- update: `C -> C_prime = C plus C5_t1_positive_active_coordinate_pin`
- survivor count: 8
- quotient class count: 4
- survivor candidate ids: [58, 68, 81, 82, 83, 91, 92, 93]

This is present and recomputed from blind C1-C3 plus C5. It is not full dynamic M(C,t) admission and does not override the failed validator-tooth checkpoint.

## G.2a

G.2a passes.

- Build card says the packet uses `scripts/builder_audit_boundary.py` from birth.
- Common source imports `builder_audit_boundary_errors` and `builder_audit_boundary_ok`.
- Boundary source calls the shared helper.
- The helper accepts `audit_verdict.md` only when the first header lines declare an independent/fresh/read-only audit.

This file intentionally declares independent/fresh/read-only audit status in its header.

## Block K Closeout

Gates cited:

- Hermes checkpoint criteria from `system_v6/receipts/hermes_architecture_corrections_20260612.md`.
- v0 five-step repair contract from `system_v6/sims/gcm_constraint_carve_v0/audit_verdict.md`.
- G.2a from `system_v6/receipts/audit_standards_codex_v1.md`.
- No-identity-leak standard from `system_v6/receipts/audit_standards_codex_v1.md`.

Admission decisions:

- terrain-blind source path: admitted with scope.
- source-honest C1-C3 local adapter pins: admitted with scope.
- no-identity-leak independence: admitted with caveat.
- downstream-only terrain readout: admitted.
- arithmetic/controls/backend agreement: admitted.
- validator-tooth checkpoint: blocked/failed.
- first real candidate substrate: not admitted.
- `gcm_object_id` for substrate-first enforcement: blocked until validator tooth is repaired and the checkpoint is re-audited.

Narrative substitutions intercepted:

- "16/8 and strict green mean substrate" was refused because direct source-injection validator tooth is green.
- "8 quotient classes means terrain atlas match" was refused; it is only a number plus downstream probe-region readout.
- "identity_leak_detected=true means quotient failed" was refused; here it is a positive-control report, with a separate caveat that quotient-class leak was not separately scored.

Worker claims verified:

- Source-honest C lane: checked against build card, common source, Julia source, validator, and result JSON.
- Terrain/validator lane: checked against source, result, direct and regenerated scratch mutation tests.
- Identity/downstream/M(C,t) lane: checked against standards, source, result JSON, and recomputation.

Worker claims not verified:

- None accepted without controller verification. Some worker line numbers were treated as pointers only and rechecked by direct source/result reads.

Status label changes to registry:

- None. No git add/commit. No registry edit.

Blocked actions:

- Do not assign `gcm_object_id`.
- Do not enable substrate-first enforcement from this packet.
- Do not cite as THE manifold, terrain atlas admission, axis admission, engine admission, physics admission, or canonical by process.

Next unblocked step:

Repair `validate_gcm_constraint_carve_v1.py` so it independently recomputes terrain-blindness from current source/admissibility predicate text, or compares the emitted guard hash against a fresh recomputation and fails on mismatch. Then rerun the exact scratch source-injection validator test.

---

## Second-Pass Re-Audit - 2026-06-12

Bottom line: VERDICT = PASS AS HERMES CHECKPOINT. With the repaired validator tooth, `gcm_constraint_carve_v1` now earns Hermes's adopted phrase: "the first real candidate substrate" at `scratch_diagnostic` strength, carrier-and-pins-relative, `promotion_allowed=false`, `formal_admission_allowed=false`, and still not THE manifold or terrain-atlas admission.

This pass adjudicates the five checkpoint criteria together:

| Criterion | Second-pass verdict | Evidence |
|---|---|---|
| 1. Terrain-blind admissibility path | PASS_WITH_SCOPE | Criteria 1-4 from the first pass carry because the repair diff from `7c3b80d25` to `a7847f12a` changes exactly one packet file: `validate_gcm_constraint_carve_v1.py` (`77` insertions). Current result still reports active C as C1-C3 only. |
| 2. Source-honest C | PASS_WITH_SCOPE | No C-source, build-card, backend, envelope, or result-source files changed in the repair diff. C1-C3 remain local executable adapter pins, not owner-source theorem predicates. |
| 3. No-identity-leak independence | PASS_WITH_CAVEAT | Current result still reports `identity_leak_detected=true` as the positive control and `identity_leak_excluded_best_accuracy=0.968 < 1.0` after identity-key exclusion. |
| 4. Downstream-only terrain readout | PASS | Current result still reports post-carve readout with `can_affect_survival=false`, `survival_inputs=[]`, and `terrain_atlas_not_claimed=true`. |
| 5. Validator teeth and G.2a | PASS | Source-only C2 terrain/atlas injection now makes the validator fail red without regenerating results, then clean source returns green. `gcm_constraint_carve_v1_boundary.boundary_errors(...)` returns `[]` for both packet and envelope after this audit append. |

### Decisive Red-Green Test

I injected this source-only change into C2 in `gcm_constraint_carve_v1_common.py`:

```text
(2*x, 2*z) != (0, 0); terrain label must be atlas-compatible before survival
```

I then ran the packet validator without regenerating common, engine, envelope, or validator result inputs. It failed red with the repaired tooth:

```text
current source terrain blindness recompute failed
current source terrain blindness: C2_probe_distinguishability_xz_local_adapter_pin: forbidden predicate token 'terrain'
current source terrain blindness: C2_probe_distinguishability_xz_local_adapter_pin: forbidden predicate token 'atlas'
terrain blindness guard stale/mismatch: predicate_text_sha256
terrain blindness guard stale/mismatch: errors
terrain blindness guard stale/mismatch: clean
```

After reverting the source-only injection, the same validator returned:

```json
{
  "errors": [],
  "ok": true,
  "result_json": "system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_envelope_results.json"
}
```

This is the exact first-pass failure condition, now red-then-green.

### Other Gates Held

Commands and checks run in this second pass:

```text
git diff --name-status 7c3b80d25..a7847f12a -- system_v6/sims/gcm_constraint_carve_v1
M system_v6/sims/gcm_constraint_carve_v1/validate_gcm_constraint_carve_v1.py
```

```text
git diff --stat 7c3b80d25..a7847f12a -- system_v6/sims/gcm_constraint_carve_v1
.../validate_gcm_constraint_carve_v1.py | 77 ++++++++++++++++++++++
1 file changed, 77 insertions(+)
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/gcm_constraint_carve_v1/tests/test_gcm_constraint_carve_v1.py
5 passed
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_v1/validate_gcm_constraint_carve_v1.py
ok=true errors=[]
```

Direct result read after the red-green test:

```json
{
  "all_pass": true,
  "candidate_count": 125,
  "density_subcarrier_count": 33,
  "survivor_count": 16,
  "quotient_class_count": 8,
  "active_C": [
    "C1_finite_density_carrier",
    "C2_probe_distinguishability_xz_local_adapter_pin",
    "C3_persistence_n01_order_gap"
  ],
  "kill_counts_by_constraint": {
    "C1_finite_density_carrier": 92,
    "C2_probe_distinguishability_xz_local_adapter_pin": 5,
    "C3_persistence_n01_order_gap": 12
  },
  "v0_regression_survivor_count": 8,
  "v0_regression_quotient_class_count": 4,
  "M_C_t_survivor_count": 8,
  "M_C_t_quotient_class_count": 4,
  "terrain_guard_clean": true,
  "blindness_control_caught": true
}
```

Hash check: packet source/result hashes before the injection and after clean rerun were byte-identical. The result estate was not weakened or rewritten by the repair.

G.2a post-audit check:

```json
{
  "packet_boundary_errors": [],
  "envelope_boundary_errors": [],
  "no_builder_audit_verdict": true,
  "no_builder_audit_verdict_envelope_gate": true
}
```

### Checkpoint Consequence

Admitted now, at the stated ceiling:

- `gcm_constraint_carve_v1` is the first real candidate substrate, scratch and carrier-and-pins-relative.
- The `gcm_object_id` freeze is now unblocked.
- The substrate-first enforcement build is now unblocked.
- The 10-step ladder's step 2 is now unblocked.

Still blocked:

- terrain-atlas admission;
- THE manifold wording;
- axis, engine, physics, or formal admission claims;
- any promotion beyond this scratch carrier-and-pins-relative substrate candidate without the next receipt.

Block K delta:

- Gates cited: Hermes checkpoint criteria 1-5; validator-tooth source-only red-green; G.2a boundary helper; result-hash stability.
- Admission decisions: criteria 1-5 admitted together, with criteria 1-4 carried from first pass by validator-only repair diff and fresh live-result read; criterion 5 repaired and admitted.
- Narrative substitutions intercepted: "first real candidate substrate" is admitted only in Hermes's bounded words, not as THE manifold or formal admission.
- Worker claims verified: no worker report accepted without local command or file read in this second pass.
- Worker claims not verified: none accepted.
- Status label changes to registry: none in this audit; no git add/commit.
- Blocked actions: stronger manifold/terrain/axis/physics claims remain blocked.
