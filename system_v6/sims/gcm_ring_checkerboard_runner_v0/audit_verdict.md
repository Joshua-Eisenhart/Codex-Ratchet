# Fresh Audit Verdict - gcm_ring_checkerboard_runner_v0

Fresh audit / read-only audit except this file. Auditor: independent cross-backend
auditor. Authorized live write: this file only. No git add/commit.

Bottom line: VERDICT = GENUINE-WITH-CAVEATS, and the builder's "strict green"
headline is too strong unless the locality claim is weakened. The core
M(C)-preservation headline survives fresh recomputation for the frozen 16-state
survivor set: applying the packet's A, B, AB, and AABB maps sends every image
state through the carve's own C1-C3 executable predicates with zero violations.
The nontrivial dynamic fact is the AB tick: all 16 states move, the image set is
all 16 survivors, and the period spectrum is [2]. The AABB row is identity on
all 16 states and must not be cited as nontrivial preservation.

Claim ceiling:
`scratch_diagnostic`; `carrier-and-pins-relative`; frozen 16-survivor
single-token CA run-surface only; `promotion_allowed=false`;
`formal_admission_allowed=false`; not THE manifold; not full CA field dynamics;
not QCA/GNVW; not runtime flux; not terrain/axis/physics admission.

## M(C) Preservation

Accepted, with scope.

Fresh recomputation imported:

- `system_v6/sims/gcm_ring_checkerboard_runner_v0/gcm_ring_checkerboard_runner_v0_common.py`
- `system_v6/sims/gcm_constraint_carve_v1/gcm_constraint_carve_v1_common.py`
- `system_v6/sims/gcm_constraint_carve_v1/results/gcm_constraint_carve_v1_results.json`

The carve predicate hash matched source and result:

```text
predicate_text_sha256 = 9be02933ef7e99fc92e519008528a89a5a6a291120772ae58dc90d76cf5b0747
constraint_ids = [
  C1_finite_density_carrier,
  C2_probe_distinguishability_xz_local_adapter_pin,
  C3_persistence_n01_order_gap
]
```

Fresh image audit:

| map | images C1-C3 admissible | moved | fixed | image count | period spectrum |
|---|---:|---:|---:|---:|---|
| A half-step | yes | 16 | 0 | 16 | [2] |
| B half-step | yes | 8 | 8 | 16 | [1, 2] |
| AB tick | yes | 16 | 0 | 16 | [2] |
| AABB tick | yes | 0 | 16 | 16 | [1] |

Adjudication: AB preservation is not vacuous identity; it is real movement on
the carved survivor set. But it is also survivor-restricted by construction:
the maps are built from carve `survivor_edges`, so this does not prove
invariance for off-survivor states, full field configurations, or an independent
manifold law. It proves only that the packet's frozen carved survivor dynamics
preserves the C1-C3 M(C) survivor set under the local adapter pins.

## Periodicity Versus Preregistration

Do not smooth this. The old classical-floor doctrine row had
alternating=period-2 and paired=period-4, and later demoted that period contrast
to implementation-correctness / definitional circularity. This packet computes
AB=[2] and AABB=[1].

This is not flagged as a JSON or code error. It is a rule-construction and
object/schedule difference:

- the GCM runner defines `AB` and `AABB` from the same carved A/B maps;
- A and B are involutive swap/singleton maps on this survivor graph;
- therefore AABB = A then A then B then B cancels to identity;
- the old v0 support's paired period-4 row is not reproduced here.

Citation rule for this row: cite AB=[2] as a nontrivial survivor-set dynamics
row. Cite AABB=[1] as a real mismatch/difference from the older support and as
identity under this packet's AABB schedule, not as a period-4 confirmation.

## Panel-11 Locality Witnesses

Mixed. The packet did not implement the panel-11 witnesses explicitly.

Fresh witness audit:

- disjoint pair/singleton decomposition passes for A and B phase maps;
- AB also decomposes into disjoint pairs after composition;
- strict light-cone `<= one ring_index site per half-step` fails:
  - A half-step max cyclic ring distance = 3;
  - B half-step max cyclic ring distance = 7;
  - AB tick max cyclic ring distance = 6.

So the rule is local only if "local" means the carved block graph edges, not the
emitted ring-edge/ring-index metric. Panel 11 asked for one-site light-cone
speed; under that reading, this runner does not pass the witness.

The locality-removal control also needs careful wording. The packet's
`locality_removal_all_to_all` row is a global successor cycle over the 16
survivor ids, with period spectrum [16] and `carved_edge_subset=false`. It
breaks carved-block locality and disjoint-pair independence, but it is not an
all-to-all dependency witness in the full CA sense, and it has ring-index
distance 1. Safe citation: "global successor-cycle control, not carved-local,
period [16]."

## Presentation Map

Primary presentation is `nested_rings_torus_loops`.

Checked rows:

- `nested_rings_torus_loops -> flat_nested_checkerboard`:
  `checked_limited_support_equivalence_not_theorem`, with support count,
  lineage bijection, and parity rows agreeing.
- `nested_rings_torus_loops -> spherical_checkerboard`:
  `checked_lineage_and_shell_occupancy_only`, with shell IDs present and five
  occupied shells.

Gap: there is no direct flat-to-spherical row, and no full three-way
presentation equivalence. This satisfies the runbook only at a limited support
/ shell-occupancy level. It does not establish full presentation equivalence.

Inherited caveat from the attach verdict: carry
`G1_shell_pattern_is_carved_probe_support_signature` on any shell or geometry
wording. The shell/presentation pattern is a carved active-probe support
signature, not independent manifold geometry.

## Controls And Fences

Controls:

- all-to-all/global-successor control: period spectrum [16],
  `carved_edge_subset=false`;
- phase-merge control: conflict ids [1, 4, 6, 7, 8, 9, 11, 14], period
  spectrum [1, 2], changed versus AB;
- carve-erasure anchoring break: lineage removed, substrate check expected red.

Fresh substrate enforcement:

```text
positive gcm_substrate_check: ok=true, errors=[]
lineage-free negative: ok=false
negative errors: gcm_object_id mismatch; registry_body_sha256 missing from lineage;
missing lineage consumption
negative_failed_as_required=true
```

G.2a / builder-audit boundary:

- builder did not write this verdict;
- packet uses `scripts/builder_audit_boundary.py`;
- the helper accepted the pre-verdict state with no errors;
- this file's header declares fresh/read-only independent audit status, so the
  post-audit boundary is idempotent by the G.2a rule.

GNVW fence held:

- QCA/GNVW row is `named_not_run_2Q_plus_ladder`;
- qubit depth is `1Q`;
- no runtime/QIT flux claim is made.

Three coordinates are present:

- layer: `CA run-surface`, `layers 1-2 + 12 support`;
- nesting: `integrated-onto-the-carve`;
- qubit depth: `1Q`.

## Checks Run

- Read authority: `AGENTS.md`, `CODEX.md`,
  `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`,
  `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`,
  `system_v5/docs/LEGO_SIM_CONTRACT.md`, Wizard v4.2 packet/manifest, standards
  codex, CA doctrine receipt, runbook, panel 11, attach verdicts.
- Read packet source/results/build card/self-assessment.
- Fresh read-only Python recomputation with
  `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` and
  `PYTHONDONTWRITEBYTECODE=1`.
- Fresh read-only substrate and boundary helper calls.
- Sidecar read-only audits for presentation map, periodicity/controls, and
  locality/substrate/GNVW surfaces.

I did not run `validate_gcm_ring_checkerboard_runner_v0.py` as an entrypoint
because it writes `results/gcm_ring_checkerboard_runner_v0_validator_results.json`,
outside this audit's live write scope. The existing stored validator result is
green, and the relevant validation logic was checked/read-only.

## Citation Rule

Allowed citation:

`gcm_ring_checkerboard_runner_v0` = GENUINE-WITH-CAVEATS scratch diagnostic
showing the first nontrivial frozen carved-survivor dynamics on the GCM
substrate: AB maps all 16 survivors into C1-C3-admissible survivor states with
period spectrum [2], while substrate enforcement is green on real lineage and
red on lineage-free erasure.

Required caveats:

- carrier-and-pins-relative 16-survivor set only;
- AB is nontrivial, AABB is identity under this packet's schedule;
- no old v0 paired period-4 reproduction;
- strict panel-11 one-ring-site light-cone fails unless locality is redefined to
  carved block graph locality;
- presentation equivalence is limited, not full three-way equivalence;
- `G1_shell_pattern_is_carved_probe_support_signature`;
- QCA/GNVW is named-not-run; no runtime flux.

Forbidden citation:

Do not cite this as THE manifold, formal admission, full CA field dynamics,
full three-presentation equivalence, QCA/GNVW index evidence, runtime/QIT flux,
terrain/axis/physics admission, or proof that the carved shell pattern is
independent manifold geometry.
