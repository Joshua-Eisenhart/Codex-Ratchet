# Audit Verdict: geo_s67_alternative_topologies_v0

Audit date: 2026-06-11
Auditor: codex1 cross-backend auditor
Scope: read-only audit of codex2 packet, except this `audit_verdict.md`.

## Verdict

VERDICT: ACCEPT AS SCRATCH DISCRIMINATOR, WITH NAMED CAVEATS.

The packet genuinely computes a four-alternative topology discriminator against the committed S6/S7 battery. The Mobius row is not a relabeled torus pass: the 2:1 cover counting survives, but the committed Z4 lens action does not descend through the twisted cover classes. Therefore the Mobius row is COMPUTED PARTIAL and fails the full battery at `lens_quotient_commensurability`.

Ceiling: `scratch_diagnostic` only. No promotion, no formal admission, no canonical uniqueness theorem, and no implication beyond these four variants: `A_path`, `B_star`, `C_complete`, `mobius_grid`.

## Evidence Paths

- Target source: `system_v6/sims/geo_s67_alternative_topologies_v0/geo_s67_alternative_topologies_v0.py`
- Julia leg: `system_v6/sims/geo_s67_alternative_topologies_v0/geo_s67_alternative_topologies_v0_julia.jl`
- Envelope result: `system_v6/sims/geo_s67_alternative_topologies_v0/results/geo_s67_alternative_topologies_v0_envelope_results.json`
- Julia result: `system_v6/sims/geo_s67_alternative_topologies_v0/results/geo_s67_alternative_topologies_v0_julia_results.json`
- Existing validator result: `system_v6/sims/geo_s67_alternative_topologies_v0/results/geo_s67_alternative_topologies_v0_validator_results.json`
- Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`

## Parent Lineage And Anchors

Envelope source hash:

- `geo_s67_alternative_topologies_v0.py`: `9d03df169611dc07fe3f83339bb37f4f2dcbad50fb21941993d69899f50a5d01`

Parent result hashes byte-bound in the packet:

- `geo_s7_discrete_refinement_v0`: result `1f0d55d6a36292cb669921ea13f104898ca8ef342b686ebbf769c44c550c1803`, source `374141367362e6e685f8d7f4b50e84d90affa309563fb9ca81b24f10a4314cc5`
- `geo_s6_s7_mode_sweep_v0`: result `665ed52239659a40884f59e03c451a73a8e887bffcc2291cae535fb16a714211`, source `407160fdc8104eab8f0f0e7c7dff2f20c21275ba2d5d3a238df2f7e7dd3f9f43`
- `ring_checkerboard_support_graph_probe`: result `f0c42e979885150b758c16562476cb261783cd8c4d73f718ac413e62e2a583c4`, source `8214cdbf6101ac7e0d3faefade7335c208d07331be314e2bee57fb9c3d7c4016`
- `engine_stage_word_cost_discriminator_v0`: result `e7dd0a2e19f51e4f5071626c6218944ab1b0fccd83c4bcf95552df61501e2734`, source `830853bcec2d707c9d5a26eff44eec5fea7904231a78f02f81ad5f7ec19d2c8f`, commit prefix `123b8e7d8`

Cost anchors read from the committed cost parent:

- committed ring/local word: `[4, 8, 4]`
- all-to-all n16 double control: `64`

## Q1 Topologies Genuine

Source construction is real graph construction, not labels-only:

```text
edges_for("A_path", n) -> {(i, i + 1) for i in range(n - 1)}
edges_for("B_star", n) -> {(0, i) for i in range(1, n)}
edges_for("C_complete", n) -> {(i, j) for i in range(n) for j in range(i + 1, n)}
```

The Julia leg independently constructs the same graph families using `Graphs.SimpleGraph`, `add_edge!`, `degree`, `ne`, and cycle rank. Fresh Julia recomputation returned:

```json
[
  {"topology":"mobius_grid","N":8,"edge_count":8,"degree_min":2,"degree_max":2,"cycle_rank":1},
  {"topology":"C_complete","N":16,"edge_count":120,"degree_min":15,"degree_max":15,"cycle_rank":105},
  {"topology":"A_path","N":8,"edge_count":7,"degree_min":1,"degree_max":2,"cycle_rank":0}
]
```

Mobius source quote:

```text
if cover == "mobius":
    return ((a + n // 2) % n, (-b) % n)
```

This is a genuine twisted gluing because the second coordinate is orientation-reversed under the half-shift, and recomputation shows it breaks the lens descent that the torus cover preserves. Caveat: the byte source implements `b -> -b mod n`, not the literal zero-based `b -> n - 1 - b` form. Those are conjugate orientation-reversing reflections, but the packet should not claim the exact textual `(i,j) ~ (i+N,M-1-j)` formula unless it either changes the source or states the coordinate convention.

## Q2 Like-For-Like Battery

Per-topology battery rows present in the survival matrix:

- refinement/convergence row;
- lens commensurability/orbit row;
- locality/cost row;
- S6 leakage-class row.

Fresh recomputation of an alternative topology orbit row:

```json
{
  "topology": "C_complete",
  "N": 16,
  "admits_lens_law": true,
  "orbit_count": 4,
  "orbit_size_min": 4,
  "orbit_size_max": 4
}
```

Fresh cost recomputation:

```json
{
  "B_star": {"observed_cost_profile": [8, 16, 16], "passes_bounded_cost_row": false},
  "C_complete": {"observed_cost_profile": [16, 64, 64], "passes_bounded_cost_row": false},
  "mobius_grid": {"observed_cost_profile": [4, 8, 4], "passes_bounded_cost_row": true}
}
```

S6 leakage class results are well-defined only for the committed ring anchor. Path and star lose the closed cycle, complete collapses ring-neighbor labels into all-to-all reachability, and Mobius preserves local rows but identifies orientation-reversed boundary data; the packet correctly marks all four alternatives as not having the committed S6 class set.

## Q3 Mobius Row

Fresh recomputation at `N=8`, shift `[2,2]`:

```json
{
  "cover": "mobius",
  "chart_point_count": 64,
  "cover_orbit_count": 32,
  "cover_orbit_size_min": 2,
  "cover_orbit_size_max": 2,
  "lens_orbit_count": 16,
  "lens_orbit_size_min": 4,
  "lens_orbit_size_max": 4,
  "lens_action_well_defined_on_cover": false,
  "admits_committed_lens_law": false
}
```

Control recomputation for the ordinary torus cover at the same `N=8`, shift `[2,2]`:

```json
{
  "cover": "torus",
  "chart_point_count": 64,
  "cover_orbit_count": 32,
  "cover_orbit_size_min": 2,
  "cover_orbit_size_max": 2,
  "lens_action_well_defined_on_cover": true,
  "admits_committed_lens_law": true
}
```

Concrete Mobius failure witness under the packet rule: for `p=(0,1)`, its cover partner is `q=(4,7)`. Lens step sends them to `(2,3)` and `(6,1)`. The cover class of `(2,3)` is `{(2,3),(6,5)}`; the cover class of `(6,1)` is `{(6,1),(2,7)}`. These are not equal. Thus the cover count survives, but the lens action is not well-defined on the twisted cover classes.

What survives:

- size-2 cover classes;
- `2 * physical == chart` counting;
- ring-like degree and bounded local cost `[4,8,4]`;
- closed-cycle graph row in the bare graph profile.

What breaks:

- committed Z4 lens quotient descent;
- orientation-stable S6 leakage class taxonomy;
- full ring/torus structural answer.

## Q4 Survival Matrix

Deaths and killing rows:

- `A_path`: killed by `closed_holonomy`. Fresh graph row: `degree_min=1`, `cycle_rank=0`, SMT closed-cycle query `unsat`; closing-edge erased/control query `sat`.
- `B_star`: killed by `closed_holonomy` first; cost also fails with `[8,16,16]`.
- `C_complete`: survives automorphism/lens rows but killed by `locality_cost` with `[16,64,64]`, hitting the all-to-all 64 control.
- `mobius_grid`: killed by `lens_quotient_commensurability`; cost survives but lens descent fails.

Structural answer traced to matrix:

- the ring/torus uniquely provides closed cyclic local successor/predecessor rows;
- a 2:1 torus cover whose classes are preserved by the Z4 lens shift;
- bounded loop-local cost under the committed `[4,8,4]` word rather than the all-to-all `64` control;
- local S6 preserve/move/cross/leave leakage classes without orientation erasure by the topology.

No tested alternative survives the full battery.

## Q5 Standard Checks

Classification and ceiling:

- envelope: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `all_pass=true`;
- source constants match this ceiling.

Controls:

- `path_closed_holonomy_killed=true`;
- `complete_graph_cost_control_fires=true`;
- `smt_agreement=true`;
- `erased_flip_controls_fire=true`;
- recomputed z3 path proof: real `unsat`, closing-edge control `sat`, `asserted_precomputed_boolean=false`;
- recomputed cvc5 path proof: real `unsat`, closing-edge control `sat`, `asserted_precomputed_boolean=false`;
- Julia Z3 result: real `unsat`, closing-edge control `sat`, `asserted_precomputed_boolean=false`.

Mode and lanes:

- mode: `julia_canon_plus_jax_diagnostic`;
- lanes: `julia`, `jax`;
- omitted PyTorch rationale: no graph/network/autograd torch claim path for this topology battery.

Real Julia leg:

- source uses `Graphs` and `Z3`;
- result has `reads_peer_result=false`;
- Graphs.jl recomputation matched graph rows for path, complete, and Mobius;
- Julia versions recorded: Julia `1.12.6`, Graphs `1.14.0`, Z3 `1.0.4`.

Tool calls:

- claim path tools are exactly `Graphs`, `Z3`, `jax`, `z3`, `cvc5`;
- top-level `tool_calls` count is 5 and names match one-to-one;
- every top-level tool call is marked load-bearing with positive, negative/control, boundary, and demotion fields.

Capability receipts:

- Python sidecar receipts exist and pass for `z3`, `cvc5`, and `graphs` under `system_v4/probes/a2_state/sim_results/*_capability_results.json`.
- Current v6 Julia Z3 capability receipt exists and passes: `system_v6/probes/julia/results/z3_capability_results.json`.
- Caveat: the packet does not embed a `capability_receipts` key, and current strict-v6 capability triage still treats Graphs/JAX-style substrate capability coverage as mixed. This does not kill the scratch discriminator, but it blocks any stronger load-bearing promotion language.

No setup-wording issue:

- `rg` found no forbidden `fixture` wording in the target packet source/results.

Versions and seeds:

- Python `3.13.6`;
- JAX `0.10.1`;
- z3 `4.16.0.0`;
- cvc5 `1.3.3`;
- Julia `1.12.6`;
- Graphs `1.14.0`;
- seed: `20260611`.

Validator:

- existing validator result has `ok=true`, `validator_ok=true`, `errors=[]`, generated `2026-06-11T09:43:06Z`.
- I did not rerun the validator because the script writes `geo_s67_alternative_topologies_v0_validator_results.json`, and this audit was read-only except this verdict file.

## Named Caveats

1. `MOBIUS_COORDINATE_FORM`: source uses `b -> -b mod n`, not literal `b -> n - 1 - b`. It is a real orientation-reversing twist and not a torus, but the exact textual class-rule claim should use the source convention or be patched in a future builder pass.
2. `CAPABILITY_RECEIPTS_NOT_EMBEDDED`: load-bearing tools are genuine in the packet, and adjacent receipts exist for several tools, but the envelope lacks an explicit `capability_receipts` field.
3. `FULL_WIZARD_NOT_RUN`: native Codex subagent spawning was not used because the available `spawn_agent` tool is permitted only when the user explicitly requests delegation/subagents. This audit is controller-local plus fresh tool recomputation, not a full Max Assembly receipt topology.
4. `UNTRACKED_PACKET`: the target directory is currently untracked in git. This is not a mathematical defect, but it is repo hygiene state and should not be hidden.
5. `FOUR_VARIANTS_ONLY`: the uniqueness implication is only against `A_path`, `B_star`, `C_complete`, and `mobius_grid`; it does not classify all possible alternative topology families.

## Recomputations Performed

Commands were stdout-only or read-only:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3` imported the packet source without running `main()` and recomputed Mobius/torus cover rows, complete-graph orbit row, path graph row, cost rows, and z3/cvc5 erased flips.
- `julia --project=.` rebuilt Graphs.jl rows for `mobius_grid N=8`, `C_complete N=16`, and `A_path N=8` without writing results.
- `jq` read parent lineage, cost anchors, S6/S7 parent rows, tool calls, versions, and validator status.
- `rg` checked the target packet for forbidden setup wording and hardcoded/precomputed-warning surfaces.

No `git add` or `git commit` was run.
