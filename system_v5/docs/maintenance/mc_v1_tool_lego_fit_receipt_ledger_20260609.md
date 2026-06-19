# M(C) v1 Tool-Lego Fit Receipt Ledger

Status: maintenance ledger, not promotion evidence.
Date: 2026-06-09.
Scope: no-install M(C) v1 tool-lego fit probes authored after the CS/AI stack upgrade plan.

## Claim Ceiling

The receipts below are accepted only as:

```text
classification=tool_lego_fit_probe
evidence_level=tool_lego_fit_probe
```

They are pre-lego fit evidence for exact M(C) v1 fields and exact tool/API
surfaces. They do not admit M(C), do not unlock Stage 4, and do not support
same-carrier geometry, topology readout promotion, AI/GNN readout promotion,
bridge, Axis0, physics, manifold, or formal admission claims.

Tool-tool coupling receipts in this ledger are accepted only as:

```text
classification=scratch_diagnostic
evidence_level=tool_tool_coupling_probe
```

They require prior parent fit receipts and also do not promote either parent
tool-lego.

## Accepted Receipts

| M(C) v1 field | Tool/API surface | Source | Result | Status |
| --- | --- | --- | --- | --- |
| `quotient_relation` | `cvc5` finite sort/function/assertion/checkSat | `system_v5/ops/formal_scouts/sim_mc_v1_quotient_relation_cvc5_tool_lego_fit_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` | pass, blocked strong consumers |
| `composition_and_local_paths` | `rustworkx.PyDiGraph`, topological/path/cycle APIs | `system_v5/ops/formal_scouts/sim_mc_v1_composition_paths_rustworkx_tool_lego_fit_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` | pass, blocked strong consumers |
| `Adm_C` / `constraint_set_C` | `xgi.Hypergraph`, hyperedges, incidence, node/edge views | `system_v5/ops/formal_scouts/sim_mc_v1_adm_constraint_xgi_tool_lego_fit_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | pass, blocked strong consumers |
| `bracketing_in_quotient` / `carrier_readout_map` | `toponetx.SimplicialComplex`, simplices, signed incidence | `system_v5/ops/formal_scouts/sim_mc_v1_bracketing_toponetx_tool_lego_fit_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | pass, blocked strong consumers |
| `axes_A_i` | `gudhi.SimplexTree`, filtration, persistence, Betti readout | `system_v5/ops/formal_scouts/sim_mc_v1_axes_gudhi_tool_lego_fit_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | pass, blocked strong consumers |

## Accepted Coupling Receipts

| Coupled fields | Parent receipts | Coupling source | Coupling result | Status |
| --- | --- | --- | --- | --- |
| `quotient_relation` + `composition_and_local_paths` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` + `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_quotient_path_cvc5_rustworkx_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_path_cvc5_rustworkx_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `Adm_C` / `constraint_set_C` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` + `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_adm_bracketing_xgi_toponetx_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_adm_bracketing_xgi_toponetx_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `axes_A_i` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` + `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `composition_and_local_paths` + `Adm_C` / `constraint_set_C` | `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` + `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_composition_adm_rustworkx_xgi_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_composition_adm_rustworkx_xgi_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `quotient_relation` + `Adm_C` / `constraint_set_C` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` + `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_quotient_adm_cvc5_xgi_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_adm_cvc5_xgi_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `quotient_relation` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` + `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `quotient_relation` + `axes_A_i` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` + `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_quotient_axes_cvc5_gudhi_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_axes_cvc5_gudhi_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `composition_and_local_paths` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` + `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `composition_and_local_paths` + `axes_A_i` | `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` + `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_composition_axes_rustworkx_gudhi_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_composition_axes_rustworkx_gudhi_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |
| `Adm_C` / `constraint_set_C` + `axes_A_i` | `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` + `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/sim_mc_v1_adm_axes_xgi_gudhi_coupling_probe.py` | `system_v5/ops/formal_scouts/results/mc_v1_adm_axes_xgi_gudhi_coupling_probe_results.json` | pass, scratch-only, blocked strong consumers |

## Verification Snapshot

Fresh checks run for the new GUDHI receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=21/21 classification=tool_lego_fit_probe stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
result JSON ignored by .gitignore:144
```

Batch receipt summary checked after GUDHI:

```text
cvc5, rustworkx, xgi, toponetx, gudhi:
  all_pass=true
  classification=tool_lego_fit_probe
  evidence_level=tool_lego_fit_probe
  promotion_allowed=false
  formal_admission_allowed=false
  stage_movement_allowed=false
stage4_unlock_allowed=false
```

Fresh checks run for the cvc5/rustworkx coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `cvc5` and `rustworkx`. The positive
certificate is SAT for the expected quotient-class path edges. The quotient
erasure control is UNSAT, and the cycle control breaks the rustworkx DAG
observable.

Fresh checks run for the XGI/TopoNetX coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `xgi` and `toponetx`. XGI carries four
admitted-record hyperedges including left/right bracketing nodes. TopoNetX emits
a nontrivial signed incidence readout from those hyperedge members. Bracketing
collapse, pairwise projection, and empty-complex controls all change or demote
the coupled observable.

Fresh checks run for the GUDHI/TopoNetX coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `gudhi` and `toponetx`. GUDHI emits a
nontrivial finite filtration and persistence readout over the admitted M(C) v1
record IDs. TopoNetX emits a nontrivial signed incidence readout over the same
record IDs through bracketing/readout nodes. Axis scramble, bracketing collapse,
and erased/empty-carrier controls all change or demote the coupled observable.

Fresh checks run for the rustworkx/XGI coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `rustworkx` and `xgi`. Rustworkx emits a
finite acyclic ordered-path graph over the admitted M(C) v1 records. XGI emits
admitted-record hyperedges carrying path, bracketing, rho, constraint, and
status members. Path collapse, cycle control, and scalar status projection all
change or demote the coupled observable.

Fresh checks run for the cvc5/XGI coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `cvc5` and `xgi`. XGI emits admitted-record
hyperedges carrying quotient class, bracketing, rho, predicate, and status
members. cvc5 certifies that every admitted hyperedge has its quotient class
node; quotient erasure flips that all-edge claim to UNSAT. Status-only projection
is satisfiable only as a demoted weaker baseline.

Fresh checks run for the cvc5/TopoNetX coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `cvc5` and `toponetx`. TopoNetX emits a
finite left/right quotient-bracketing incidence fixture. cvc5 certifies the
left/right quotient-bracketing distinction; bracketing collapse and quotient
erasure both flip the strict distinction claim to UNSAT.

Fresh checks run for the cvc5/GUDHI coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `cvc5` and `gudhi`. GUDHI emits a finite
axes filtration over the admitted M(C) v1 record IDs. cvc5 certifies that every
admitted record has quotient-class and axes-field presence; quotient erasure and
axis erasure both flip the strict all-record claim to UNSAT. A vertices-only
filtration or scrambled axes readout is demoted baseline evidence only.

Fresh checks run for the rustworkx/TopoNetX coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `rustworkx` and `toponetx`. Rustworkx
emits an ordered local-path DAG over admitted M(C) v1 records. TopoNetX emits a
finite signed-incidence complex over the same path, record, bracket, and readout
nodes. Path collapse changes both observables, bracketing collapse changes the
incidence observable, and a cycle plus empty-complex control demotes the fixture.

Fresh checks run for the rustworkx/GUDHI coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `rustworkx` and `gudhi`. Rustworkx emits
an ordered local-path DAG over admitted M(C) v1 records. GUDHI emits a finite
axes filtration over the same admitted record IDs. Path collapse changes the
graph-side observable, axis erasure or label shuffle changes the filtration
observable, and a cycle plus vertices-only filtration demotes the fixture.

Fresh checks run for the XGI/GUDHI coupling receipt:

```text
SCOUT_DONE all_pass=true positive=3/3 negative=3/3 boundary=7/7 classification=scratch_diagnostic stage_movement_allowed=false
validate_receipt.py: all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: violation_total=0
py_compile: pass
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits
git diff --check: pass
```

The coupling's load-bearing tools are `xgi` and `gudhi`. XGI emits
admitted-record hyperedges carrying predicate, status, bracketing, rho, and axes
members. GUDHI emits a finite axes filtration over the same admitted record IDs.
Status-only projection changes the hypergraph-side observable, axis erasure or
label shuffle changes the filtration observable, and an empty hypergraph plus
vertices-only filtration demotes the fixture.

Batch receipt summary checked after the tenth coupling:

```text
validate_receipt.py: checked=15 all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict: checked=15 all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: checked=15 violation_total=0
py_compile: pass for all 15 sources
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits across all 15 sources
```

The blocked consumers are the same across the fit and coupling receipts:

```text
M(C)_system_fit
same_carrier_geometry
topology_readout_promotion
AI_GNN_readout_promotion
bridge
Axis0
physics
manifold_admission
```

## Routing Use

Agents may use this ledger to avoid reinstalling or rediscovering these package
surfaces. The correct next use is M(C) gap-table hardening and exact field/tool
mapping, plus scratch-only tool-tool coupling after parent fit receipts, not
layer completion or bridge work.

If a future packet tries to consume these receipts for a stronger claim, it must
cite a separate admission packet with the explicit M(C) fields, controls,
stage gate, and result evidence that justify the stronger consumer.
