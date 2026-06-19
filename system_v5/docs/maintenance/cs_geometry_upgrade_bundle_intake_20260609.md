# CS Geometry Upgrade Bundle Intake

Status: processed incoming scaffold packet.
Date: 2026-06-09.
Source archive: `/Users/joshuaeisenhart/Desktop/codex_ratchet_cs_geometry_upgrade_bundle_v1_2026-06-09.zip`
Archive sha256: `922deb11ebdb9b5a6fa01509d899660d6ebf9d6c3c906e7f8e64c209041ee97d`
Scratch extract: `/tmp/codex_ratchet_cs_geometry_upgrade_bundle_v1/build_codex_ratchet_cs_geometry_v1`

Classification: `design_scaffold_intake`.
Promotion allowed: `false`.
Formal admission allowed: `false`.

This intake records what can be used from the packet without letting a scaffold,
candidate library menu, or old Lev/provider vocabulary become Codex Ratchet
runtime truth.

## Verification Run

Checksum manifest verification:

```text
ok=true
listed_files=54
actual_files_excluding_manifest=54
hash_failures=0
missing=0
extra=0
```

Bundle local smokes were run under the shared sim-stack Python:

```text
codex_cs_curriculum_smoke.py: ok, classes=12, queue=10
current_edge_candidate_manifest_smoke.py: ok, library_count=20
codex_geometry_manifest_smoke.py: ok
library_sets_catalog_smoke.py: ok
mc_object_schema_smoke.py: ok
three_engine_agent_contract_smoke.py: ok
```

Current repo runtime guards were rerun after unpacking:

```text
scripts/codex_runtime_env_doctor.py: ok=True, install_state=stable_observed
scripts/audit_runtime_mapping_references.py: ok=True, failure_count=0
```

No package install was performed.

## Accepted Into Current Planning

The packet is useful as a planning scaffold for the CS and geometry layer. The
accepted order is:

```text
finite carrier
-> graph / hypergraph / rewrite representation
-> multiway or causal event graph
-> topology / quotient / basin readouts
-> GNN / AI only after the explicit graph object exists
```

This is compatible with the current Codex Ratchet rule that M(C), carrier,
probe family, operation family, and negative controls must be explicit before
same-carrier geometry can promote.

The packet's geometry tower is accepted only as visibility and queue structure:

```text
F01/N01 roots
-> M(C) admissibility object
-> carrier/readout
-> spinor/Clifford
-> Hopf
-> Weyl/chirality
-> holonomy/order
-> bracketing/nonassociativity
-> multi-spinor/network
-> metric
-> topology/graph/cell complex
-> terrain/operator
-> basins
-> cross-model readout matrix
-> entropy/memory
-> physics controls
```

The packet's immediate same-carrier micro-lego target is acceptable only at
`scratch_diagnostic` or `tool_lego_fit_probe` ceiling until M(C) is filled:

```text
Hopf fiber/base loop law, or Weyl-on-Hopf chirality,
over one explicit carrier, with erased-control and demotion condition.
```

The CS class map is accepted as a candidate tool-class menu, not as an install
order. Good first micro-probe rows should start from tools already verified in
the current shared runtime: `rustworkx`, `xgi`, `TopoNetX`, `gudhi`,
`torch_geometric`, `cvc5`, `z3`, and `sympy`.

## Open M(C) Object Gap

The packet correctly keeps the M(C) object unfinished. These fields remain open
for admission-grade work:

- finite carrier set or tensor anchor;
- admissible state family;
- probe family;
- operation/control family;
- equivalence relation;
- positive witnesses;
- negative or erased controls;
- blocked downstream consumers;
- receipt schema and validator.

Until those are explicit, same-carrier geometry is useful fuel but not a
manifold completion, G-structure selection, Axis0 unlock, physics claim, or
bridge admission.

## Rejected Or Port-Required

Do not import the bundle wholesale into active skills, agents, schemas, or
runtime maps.

The following parts require porting before use:

- Several schemas have `lev.*` or `https://lev.dev/...` identifiers and Lev
  titles despite Codex filenames. They need Codex Ratchet ids, titles, and
  authority wording before installation.
- The three-engine agent catalog uses provider ids such as `lev-sim-julia`,
  `lev-sim-jax`, `lev-sim-torch`, and `lev-proof-solver`. These need Codex
  role ids and current authority boundaries before they can become live agents.
- The full library catalog is a reference menu, not current runtime truth. It
  includes rows that conflict with the live map, including `bayeux`, DGL,
  `torch_scatter`, `torch_sparse`, PythonCall, DLPack, and CondaPkg. Current
  repo runtime maps override those rows.
- `support_probe_julia.jl` probes the wrong level for carrier truth unless it
  is rewritten to run under the strict carrier project with
  `JULIA_LOAD_PATH=@:@stdlib`.
- `support_probe.py` is useful as a quarantine sanity check, but it treats
  candidate rows as raw imports and includes non-target rows such as
  `graphology-python?`. The repo doctor remains authoritative.
- `numpy_contamination_scanner.py` is not installable as-is. It carries Lev
  wording and an allow marker, and its regexes falsely flag `jnp.array` and
  `jnp.asarray` as forbidden `np.array` / `np.asarray`.

## Bundle Probe Findings

The quarantined Python support probe agreed with the current runtime on the
core Python stack:

```text
jax 0.10.1
diffrax 0.7.2
dynamiqs 0.3.4
netket 3.21.0
torch 2.11.0
torch_geometric 2.7.0
torchode 1.0.1
torchdiffeq 0.2.5
xitorch 0.3.0
cvxpylayers 1.2.0
cvc5 1.3.3
julia 1.12.6 available
```

It also reported missing non-required rows:

```text
pytorch3d
graphology
```

The quarantined contamination scan passed on `system_v5/codex_skills`, but
produced false blocks on JAX code in `scripts/codex_engine_stack_shakedown.py`
because of the `jnp.*` regex bug. Treat its current output as diagnostic only.

## Current Queue Effect

The packet changes queue pressure but not evidence status.

Recommended next actions:

1. Finish the M(C) gap table as an explicit finite object.
2. Refresh Tier-A CS micro-probes using installed tools first:
   `rustworkx`, `xgi`, `TopoNetX`, `gudhi`, `torch_geometric`, `z3`, `cvc5`.
3. Port a Codex-native contamination scanner with correct token boundaries and
   `codex-allow-classical-boundary` style markers.
4. Only then consider isolated candidates such as Catlab, AlgebraicRewriting,
   CombinatorialSpaces, egglog, or PGMax, one install-intent at a time.

No result, skill, or agent should cite this bundle as proof that a package is
installed, load-bearing, or admission-bearing. It is an intake scaffold and a
queue-shaping document.
