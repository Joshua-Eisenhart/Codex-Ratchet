# V9 Current State — 2026-08-06

## Outcome

The repository now has one development release spine for five independent
products. It is runnable as a software organization and inventory layer. It is
not a promoted scientific release.

Version: `9.0.0.dev1`

Release state: `development_candidate`

Promotion: `false`

## Products

| Product | Version | Independent root | Current software state |
|---|---:|---|---|
| ConstraintBox | `0.4.0.dev1` | `constraint_box/` | exact five-tool core declared, exercised, and tested; legacy-wide migration remains |
| ClaimGate | `0.1.0.dev1` | `claimgate_plugin/` | standalone finite contract and package metadata; no CB import in SMT surface |
| Sim Engines | `0.1.0.dev1` | `sim_engines/` | profile installer, 89-row registry, live doctor, strict Julia environment |
| Codex Ratchet | `9.0.0.dev1` | `system_v9/codex_ratchet/` | product/release boundary plus stack verifier |
| Holodeck | `0.1.0.dev1` | `holodeck/` | light independent scaffold, optional world-model profile, no engine promotion |

## ConstraintBox

### Core that is actually owned by CB

| Tool | Version observed | Core exercise |
|---|---:|---|
| Z3 | `4.16.0.0` | finite integer constraints |
| cvc5 | `1.3.3` | finite integer constraints |
| SymPy | `1.14.0` | exact symbolic expression |
| rustworkx | `0.17.1` | finite workflow graph |
| Maude Python | `1.6.0` | bounded rewrite module |

The combined observation SHA-256 is
`5c09bc21101c77c76f209ef34ce2154b89d1745419ef28493553bc16e76296b9`.

The default `constraintbox` command now enters the lean core. The old broad CLI
is retained as `constraintbox-legacy`. JAX, PyTorch, Julia,
Java/TLC/Apalache, and PySINDy are excluded from the CB core.

### Remaining CB debt

- Historical modules still implement a much wider surface. Their presence is
  legacy source, not expansion of the v9 core.
- Historical tests that assume an embedded ClaimGate must be migrated to an
  external bridge test. Re-embedding ClaimGate would violate the v9 boundary.
- The audited custody pattern distilled from Desktop packs is not yet cleanly
  ported into the five-tool core.
- The passing CB-to-Sim external packet currently relies on a locally
  instantiated historical Julia carrier. It must be moved to the portable Sim
  Engines environment before it can be a cold-machine v9 bridge claim.

## ClaimGate

ClaimGate owns `finite_constraint_contract.v1`; its SMT surface no longer
imports `constraintbox.constraints`. Its standalone tests run with
`PYTHONPATH=.`. A wheel was built locally as
`codex_claimgate-0.1.0.dev1-py3-none-any.whl`, SHA-256
`b167c17e272c7fa86c5ea5076f9b19b02a449d99a28371c4c0558af8d35365aa`.

The old `claimgate/` tree is marked legacy. The root `claimgate_plugin/` tree is
the v9 product authority.

## Sim Engines

### Live inventory

| Measure | Count |
|---|---:|
| registered tools | 89 |
| registered installed or visible | 89 |
| registered missing | 0 |
| unchecked | 0 |
| strict Julia direct dependencies | 21 |
| unregistered installed Python distributions | 306 |

Visibility is not integration. Each row separately records live visibility,
declared integration level, named profiles, source paths, and evidence paths.

### Portable installation

Python profiles are resolved recursively by `sim_engines/install.py`:

- `cb-mirror`
- `python-base`
- `jax`
- `torch`
- `qit-python`
- `graph-topology`
- `system-identification`
- `holodeck-world-model`

Julia uses `sim_engines/install/julia/Project.toml` plus the checked-in,
machine-generated `Manifest.toml`. All 21 direct packages loaded from the
active project during the latest doctor pass.

Java, TLC, and Apalache are visible but quarantined in Sim Engines. They are
not part of CB and are not v9 default requirements.

### Remaining Sim Engines debt

- Run a true cold-machine install/doctor/test from the declared profiles.
- Decide which of the 306 unregistered local distributions deserve a registry
  row; do not copy the local environment wholesale.
- Replace old aggregate comparisons with independent full-map comparisons for
  the CR-to-Sim bridge.
- Continue upgrading `installed_only` rows only when a named API, workload,
  control, and result artifact are actually exercised.

## Holodeck

The default install has no heavy dependency. The optional development profile
can see NumPy, SciPy, PyTorch, PyTorch Geometric, Lightning, Gymnasium,
scikit-learn, and e3nn. Eight old world-model files are indexed as candidate
sources, not integrated engines.

The QIT bridge remains
`blocked_pending_independent_qit_engine_reality_gate`. Holodeck perception,
memory, and world-model operation are not claimed by this release.

## Bridges

| Bridge | Current level | Status |
|---|---|---|
| CB -> ClaimGate | imported in source | legacy adapter exercised before v9 |
| CB -> Sim Engines | API smoke | 16 focused checks passed after historical carrier setup |
| CR -> CB | API smoke | legacy adapter exercised before v9 |
| CR -> Sim Engines | function-level receipt | v9 full-map retest required |
| Holodeck -> Sim Engines | installed only | declared, not exercised |
| Holodeck -> QIT engines | installed only | blocked on QIT reality gate |
| CR -> Holodeck | installed only | declared, not exercised |

All bridge directions, schemas, timeouts, tests, and fail-closed statuses live
in `system_v9/bridges/registry.v9.json`.

## Desktop curation

Twelve recent relevant archives were SHA-256 indexed. Zero were copied into
the active repository. The useful deltas were distilled into implementation
requirements and candidate-science gates in
`system_v9/intake/DESKTOP_CURATION_20260806.md` and its machine-readable index.

## Verification

| Check | Result |
|---|---:|
| v9 structural verifier | 125/125 |
| ConstraintBox v9 boundary | 6/6 |
| ConstraintBox five-tool exercise | 5/5 |
| ClaimGate standalone test methods | 23/23 |
| Sim Engines registry tests | 7/7 |
| Holodeck boundary tests | 3/3 |
| CB-to-Sim external packet focused checks | 16/16 |
| Wiki probe contract tests | 3/3 |

The structural verifier reports
`claim_ceiling=structural_product_and_bridge_verification_only` and
`promotion_allowed=false`.

## Quarantine and source-control state

The original working tree contains older modified result/receipt files that
ClaimGate refused to admit because required provenance and preregistration were
absent. They were not copied into this clean v9 branch. The v9 branch is the
clean consolidation lane; the old worktree remains preserved for deliberate
later review.

## What v9 does not establish

- a complete or admitted manifold;
- real Type 1 and Type 2 QIT engines;
- sixteen unique stage abilities;
- an operational quantum-Hopfield engine inside those stages;
- a Holodeck perception/world model;
- physics, TOE, mathematical-foundation, or scientific proof;
- admission or release of historical result receipts.

## Next order

1. Finish product packaging and cold-machine installation checks.
2. Port strict external custody into CB without enlarging its core.
3. Produce fresh v9 bridge receipts, starting with CB -> ClaimGate and CR -> CB.
4. Retest CR -> Sim Engines by independent full-map recomputation.
5. Proceed through QIT gates `G0v`, `G1`, `G2`, and `G3`.
6. Only then build Holodeck adapters on independently real QIT and trainable
   world-model engines.
