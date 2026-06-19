# Independent Audit Verdict -- engine_16_stage_correspondence_v1

Audit mode: read-only audit / fresh audit. Auditor wrote only this
`audit_verdict.md`. No git add/commit. Freshness tier: TIER-2
results-available; I read the build card, source, result JSONs, bound receipts,
and recomputed packet-local values from source without rerunning builder scripts
that overwrite result artifacts.

## Bottom Line

VERDICT: PASS AS A SCRATCH DIAGNOSTIC, CORRESPONDENCE FAIL CONFIRMED.

The builder's central claims are sustained: the owner-corrected 16-row table was
built as explicit Bloch-ball affine channel compositions; it produces 15
defined component IDs; it has 0/16 exact component matches against the
discovered eng64 16; order erasure collapses to 8; pairing-scramble also scores
0 exact matches; label permutation is invariant; one commuting pair is honestly
reported; G.2a and substrate positive/negative gates are green/red as intended.

The deeper diagnosis is not "pipeline artifact." It is primarily a realization
mismatch: the discovered-16 are behavioral classes from the old eng64 four-stroke
schedule realization, while the defined-16 are new terrain-flow/channel
compositions on the same 2x2 density/Bloch carrier. They are the same broad
numeric kind (one-qubit density-channel outputs measured by the same
fingerprint family), but they are not the same realized channel family. The
exact fingerprint metric is valid enough to reject exact correspondence, but
too brittle to diagnose pairing semantics by itself. v2 should use graded
channel metrics and a realization-alignment search before treating another
0/16 as hypothesis death.

Accepted ceiling: `scratch_diagnostic`, `hypothesis_test_only`,
`promotion_allowed=false`, `formal_admission_allowed=false`. No stage,
Matrix64, QIT-engine, axis, bridge, manifold, physics, or target-system
admission is earned.

## Fresh Checks

Read-bound evidence:

- Build card: `system_v6/sims/engine_16_stage_correspondence_v1/build_card.md`
- Packet source: `engine_16_stage_correspondence_v1_common.py`
- Primary result: `results/engine_16_stage_correspondence_v1_results.json`
- Envelope: `results/engine_16_stage_correspondence_v1_envelope_results.json`
- Registered hypothesis: `system_v6/receipts/ratchet_geometry_order_hypothesis_20260612.md`
- Standards codex: `system_v6/receipts/audit_standards_codex_v1.md`
- Fingerprint reference: `system_v6/sims/eng64_stage_fingerprint_ids_v0/`
- Baseline v0: `system_v6/sims/engine_16_stage_definition_correspondence_v0/`

Fresh commands run:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_envelope_results.json
```

Result: `ok=true`.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/gcm_substrate_check.py system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_lineage_free_negative.json
```

Result: `ok=false`, with expected missing-lineage errors.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/engine_16_stage_correspondence_v1/results/engine_16_stage_correspondence_v1_envelope_results.json
```

Result: `ok=true`.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/engine_16_stage_correspondence_v1/tests
```

Result: `5 passed`.

I did not run `validate_engine_16_stage_correspondence_v1.py` because the
validator writes `results/engine_16_stage_correspondence_v1_validator_results.json`,
which would violate the read-only audit boundary.

## Exact Correspondence Recompute

Import-level recomputation from `engine_16_stage_correspondence_v1_common.py`
returned:

```json
{
  "stage_count": 16,
  "defined_distinct": 15,
  "discovered_distinct": 16,
  "exact_matches": 0,
  "order_erasure_distinct": 8,
  "pairing_scramble_exact_matches": 0,
  "commuting_pair_count": 1
}
```

The exact match matrix is all zero. The 15 defined component IDs and 16
discovered component IDs are disjoint. This verifies the second 0/16 as a real
computed result under the committed method, not a prose/pipeline artifact.

## Four Recomputed Channels

All four sampled rows were recomputed from the explicit affine composition,
applied to `eng64.RHO_REPR`, rounded at `FP_TOL=1e-7`, and hashed through
`eng64.component_id_for_fingerprint`.

| Stage | Composition | Component ID | Exact in discovered set | Nearest fingerprint L2 | Nearest affine-channel L2 |
|---|---|---:|---:|---:|---:|
| `TiSe` | `T_Se o D_z` | `eng64_fp_8bf0e242db60c5cb` | false | 0.151241004149 | 0.533741997576 |
| `SeFi` | `R_x o T_Se` | `eng64_fp_a862e4373e415d77` | false | 0.315141809814 | 0.677049624059 |
| `FiNe` | `T_Ne o R_x` | `eng64_fp_9eb18ccd407404af` | false | 0.332336224415 | 1.737919366893 |
| `TeSi` | `T_Si o D_x` | `eng64_fp_b44a8bbd9fdf1a50` | false | 0.110582735762 | 0.956152238458 |

Sample recomputed affine rows:

- `TiSe`: matrix
  `[[0.297977803379,-0.062439852781,0.112846177549],[0.078992324284,0.297977803379,-0.089199789687],[-0.062439852781,0.078992324284,0.425682576255]]`,
  translation `[0,0,0]`, fingerprint
  `[0.2834332,0,-0.0227526,-0.000136,-0.0227526,0.000136,0.7165668,0]`.
- `SeFi`: matrix
  `[[0.425682576255,-0.089199789687,0.112846177549],[0.089199789687,-0.112846177549,-0.425682576255],[0.112846177549,0.425682576255,-0.089199789687]]`,
  translation `[0,0,0]`, fingerprint
  `[0.4822502,0,-0.0098027,-0.2237476,-0.0098027,0.2237476,0.5177498,0]`.
- `FiNe`: matrix
  `[[0.055902108969,0.997032059667,0.052934168636],[0.997032059667,-0.052934168636,-0.055902108969],[-0.052934168636,0.055902108969,-0.997032059667]]`,
  translation `[0,0,0]`, fingerprint
  `[0.9555431,0,-0.1787137,-0.1026737,-0.1787137,0.1026737,0.0444569,0]`.
- `TeSi`: matrix
  `[[1,0,0],[0,0.432183953531,-0.1827244448],[0,0.1827244448,0.432183953531]]`,
  translation `[0,0,0]`, fingerprint
  `[0.2682385,0,0.0682647,-0.0174182,0.0682647,0.0174182,0.7317615,0]`.

## Deeper Diagnosis

Question: are the defined and discovered objects even the same kind?

Finding: same broad carrier/fingerprint domain, different realized channel
families.

The defined-16 are explicit affine maps on Bloch coordinates built from:

- terrain flows selected from `geo_s5_terrain_flows_v0` at `t=1`;
- `D_z`, `D_x`, `R_x`, `R_z` with `lambda=0.7`, `theta=pi/2`;
- one ordered terrain/channel composition per stage.

The discovered-16 come from the old eng64 realization:

- `axis1`: amplitude-damping Kraus maps with `gamma=0.30`;
- `axis2`: open Lindblad loop or closed `R_x(theta=pi/3)`;
- `axis5`: hot `S_z` dephasing or cold `R_x(pi/4)`;
- `axis6`: substage order toggle;
- `axis3/axis4`: Carnot/Szilard stroke table and forward/reverse four-stroke
  schedule.

So this is not a pure domain mismatch. The fingerprint method applies to both:
2x2 density outputs from the same representative density matrix. But it only
compares one representative output vector exactly, so it cannot by itself decide
whether a near channel equivalence, parameter retuning, or schedule mapping
exists.

Nearest-distance evidence:

- nearest output-fingerprint L2: min `0.090323520972`, median
  `0.225110376342`, mean `0.285933920950`, max `0.714954546299`;
- nearest full affine-channel L2, recomputed by probing the old eng64 stage
  maps on Bloch basis states: min `0.522729240697`, median
  `1.103578919487`, mean `1.098902409661`, max `1.737919366893`.

Interpretation: not epsilon-near. The distances are nonuniform, which means
there are local neighbors and a graded metric is useful, but the full-channel
distances are too large to call this an exact-method artifact. This supports
diagnosis (a): the realizations differ. Diagnosis (b) is only partially true:
the exact fingerprint is too strict for semantics and pairing diagnosis, but it
is not measuring the wrong carrier. Diagnosis (c) is true only for the
specific strong claim "these defined 16 reproduce the discovered eng64 16";
it does not by itself kill the broader geometry-order hypothesis on a differently
realized stage estate.

## Controls

Pairing scramble: confirmed. The wrong-pairing control swaps `Ti<->Te` and
`Fi<->Fe`, recomputes the 16 rows, and scores `0` exact matches, the same as
normal. Meaning: at this exact-match distance, the metric cannot see whether the
native pairing convention is doing work. The control ran correctly, but the
same-zero result is non-informative rather than confirming the pairing.

Order erasure: confirmed. Forcing both order variants of each terrain/operator
pair to the same `T_tau after operator` map collapses the 16 rows to 8 distinct
component IDs. This is theory-conforming: order is load-bearing in the normal
table except where a genuine commute/alias occurs.

Commuting pair: confirmed. Exactly one pair is reported as commuting under
tolerance:

- `Te<->Si`: `T_Si o D_x` and `D_x o T_Si`, commutator affine L2 `0.0`.

The other seven pair gaps are nonzero, ranging from `0.061027495509` to
`2.402111877609`.

Label permutation: confirmed invariant. Labels are applied after component
fingerprints; label field is not used in the hash.

## Flux Fate

The registered hypothesis supplement offered a flux-fate row: preserve pure
states/lift to Hopf flux vs erase pure states into mixed states. The packet did
not compute or emit a `flux_fate` column or equivalent field. That is an audit
finding, not a failure of the stated correspondence packet, because the build
card did not require this row. v2 should add it because it is cheap and directly
tests whether the stage table is doing the intended geometry work rather than
only producing component hashes.

## G.2a, Substrate, Coordinates

G.2a: satisfied from birth for this packet. The build card declares the boundary,
the result carries `no_builder_audit_verdict=true` and
`no_builder_audit_verdict_envelope_gate=true`, and the boundary helper accepts
this independent audit header.

Substrate: sustained. The envelope passes `scripts/gcm_substrate_check.py`
against `gcmobj_a40e54e13cec01466c9d675028b3574b` and registry body hash
`0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed`; the
lineage-free negative fails red with missing-lineage errors.

Coordinates: properly bounded. The packet uses Bloch coordinates and density
matrices as the 1Q carved-carrier channel representation. It does not promote
Bloch coordinates to final substrate, and the result fences stage/Matrix64/QIT
engine/axis/bridge/manifold/physics claims.

## Recommendation

Do v2, but reframe it. Do not run a third exact 0/16 table as if exact component
matching alone can answer the real question.

v2 should be `engine_16_stage_correspondence_v2_graded` or equivalent:

1. keep the exact-match row as a hard negative control;
2. add full affine-channel distances, Choi/superoperator distances where
   available, and multi-state fingerprint distances over a deterministic state
   panel;
3. compare the actual old eng64 operator schedules to the defined
   terrain/channel generators, not only output hashes;
4. add a finite parameter sweep for `lambda`, `theta`, and flow time `t` before
   declaring no near realization;
5. emit the flux-fate column from the supplement;
6. include pairing controls scored by graded metrics, not just exact hash count.

Bottom-line next claim: "The owner-corrected table is a valid scratch diagnostic
and an exact non-correspondence to the old eng64 discovered-16. The likely cause
is different realized channel families, not a bad hash pipeline. The next useful
test is graded realization alignment, not another exact-match rerun."
