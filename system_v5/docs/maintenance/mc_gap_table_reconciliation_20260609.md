# M(C) Gap Table Reconciliation - 2026-06-09

## Scope And Ceiling

This is a maintenance reconciliation note only. It does not promote M(C) v1, does not install packages, does not rebuild any runner, and does not admit Axis0, bridge, physics, manifold, same-carrier geometry, topology readout, or AI/GNN readout claims.

Current ceiling: v1 may be kept as quarantined `scratch_diagnostic` fuel. Stage 4 remains locked until a proper consumer-aware gate admits the exact fields and receipts needed by the next consumer.

## Current Artifact Map

| Artifact | Path | Current role |
|---|---|---|
| Wave A receipt | `system_v5/docs/maintenance/wave_a_cs_ai_no_install_shakedown_20260609.md`; result `system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json` | `scratch_diagnostic` / `tool_capability`; six no-install micro-probes passed, but downstream consumers remain blocked. |
| v0 deferred gap table | `system_v5/docs/maintenance/tool_integration_audit_20260609/mc_gap_table_DEFERRED_LADDER_INPUT.md` | Still valid for v0 and the pre-v1 gap analysis. It records which M(C) fields were present, missing, or externalized in the old profile. |
| v1 quarantine receipt | `system_v5/docs/maintenance/mc_v1_quarantine_20260609.md`; result `system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json` | Keep in place as fenced scratch graveyard fuel. It ran one phase early during tool-tuning and must not drive ladder movement. |
| v1 tool-lego fit ledger | `system_v5/docs/maintenance/mc_v1_tool_lego_fit_receipt_ledger_20260609.md` | Five no-install `tool_lego_fit_probe` receipts now map exact M(C) v1 fields to exact tool/API surfaces. This hardens the gap table only; no promotion or stage movement. |
| old/v0 profile | `system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_envelope_results.json` | Present. `scratch_diagnostic`, `all_pass=true`, `promotion_allowed=false`, `formal_admission_allowed=false`; finite density/probe profile with 125 grid points, 27 admitted records, and density/probe controls. |

## Schema-Aware Field Reconciliation

| M(C) contract field | v1 current-schema key | v1 state under current schema | Ceiling |
|---|---|---|---|
| finite support `S` | `support_S` | Present. Emits `size=9` with element records, admitted flags, density/probe values, composition, bracketing, carrier readout, full probe keys, and rejection reasons. | Scratch structural coverage only. |
| active constraint set `C` | `constraint_set_C` | Present. Names `F01`, `N01`, density/probe constraints, composition rules, bracketing rules, and carrier rules. | Scratch coverage; not consumer admission. |
| probe/readout family `M/P` | `M_over_P` | Present. Lists `P=["density","composition","bracketing","carrier","axes"]` and the full probe family. | Scratch coverage; not Stage 4 unlock. |
| quotient relation `~_M` | `quotient_relation` | Present. Defines the full-key rule and emits `quotient_S_mod_M` plus `quotient_Adm_C_mod_M`; bracketing is visible in the key. | Scratch coverage; quotient still needs consumer-aware gate. |
| admissibility predicate `Adm_C` | `Adm_C` | Present. Predicate is `density_probe_C && F01 && N01 && bracketing && carrier`; emits admitted and rejected records. | Scratch coverage; not formal admission. |
| composition and local path rules | `composition_and_local_paths` | Present. Names allowed paths and forbidden erasures/reassociation. | Scratch coverage; not same-carrier geometry. |
| bracketing in quotient | `bracketing_in_quotient` | Present. `wired_in=true`; left/right records and drop-bracketing control are emitted. | Scratch coverage; not nonassociative carrier admission. |
| carrier readout map | `carrier_readout_map` | Present for admitted IDs, with octonion readout and Cl(6) surface details. | Scratch coverage; not bridge, physics, or manifold. |
| axes `A_i:M(C)->V_i` | `axes_A_i` | Present. Emits `A_entropy_bits`, `A_order_gap`, and `A_associator_norm` maps over admitted IDs. | Scratch coverage; not Axis0 or axis-level admission. |
| negative and erased controls | `negative_controls` | Present. Includes `drop_F01`, `drop_N01`, `drop_bracketing`, `commuting`, `associative`, `carrier_erasure`, and `label_shuffle`; all report `all_engines_flip=true`. | Scratch evidence; controls still need admission gate review. |
| evidence handles / receipts | `receipts` | Present. Includes envelope, Julia, JAX, PyTorch, and canon artifact paths/hashes. | Evidence handles only; no staging or promotion. |
| claim ceiling | `claim_ceiling` | Present. Explicitly says no promotion, no formal admission, no bridge, no physics, no Axis0, no manifold claim. | Binding ceiling for this reconciliation. |

The v1 result also reports `M_C_v1_field_coverage_summary.present_in_object` for `S`, `C`, `M/P`, `~_M`, `Adm_C`, composition, bracketing, local path rules, carrier readout map, axes, controls, receipts, and ceiling, with `still_external=[]`. That narrows the structural gap relative to v0, but it does not change the promotion ceiling.

## Tool-Lego Fit Reconciliation

The following receipts are now field-specific fit checks against the quarantined
v1 object after the consumer gate. Each receipt is accepted only as
`classification=tool_lego_fit_probe` / `evidence_level=tool_lego_fit_probe`.

| M(C) v1 field | Fit receipt | Tool/API surface | Current effect |
|---|---|---|---|
| `quotient_relation` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` | `cvc5` finite relations and SAT/UNSAT API | Field has a load-bearing SMT fit receipt for one bounded quotient fixture. |
| `composition_and_local_paths` | `system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` | `rustworkx.PyDiGraph`, topological/path/cycle APIs | Field has a load-bearing DAG/path fit receipt for one bounded local-path fixture. |
| `Adm_C` / `constraint_set_C` | `system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | `xgi.Hypergraph`, hyperedges, incidence, node/edge views | Field has a load-bearing hypergraph/incidence fit receipt for one bounded admissibility/constraint fixture. |
| `bracketing_in_quotient` / `carrier_readout_map` | `system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `toponetx.SimplicialComplex`, simplices, signed incidence | Field has a load-bearing signed-incidence fit receipt for one bounded bracketing/readout fixture. |
| `axes_A_i` | `system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `gudhi.SimplexTree`, filtration, persistence, Betti readout | Field has a load-bearing filtration fit receipt for one bounded axes fixture. |

Batch validation after the five receipts:

```text
validate_receipt.py: checked=5 all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict-scope --require-run-boundary: checked=5 all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: checked=5 violation_total=0
py_compile: pass
```

All five receipts report:

```text
promotion_allowed=false
formal_admission_allowed=false
stage_movement_allowed=false
stage4_unlock_allowed=false
```

and block:

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

This changes the gap table as follows: the listed v1 fields now have exact
tool/API fit receipts available for future consumer-aware packets. It does not
change the v1 object from scratch fuel into an admitted object, and it does not
authorize same-carrier geometry, topology readout, AI/GNN readout, bridge,
Axis0, physics, manifold, or stage movement.

## Tool-Tool Coupling Receipts

Ten scratch-only coupling receipts now exist after the parent fit receipts:

| Coupled fields | Parent receipts | Coupling result | Ceiling |
|---|---|---|---|
| `quotient_relation` + `composition_and_local_paths` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` and `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_path_cvc5_rustworkx_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `Adm_C` / `constraint_set_C` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` and `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_adm_bracketing_xgi_toponetx_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `axes_A_i` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` and `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `composition_and_local_paths` + `Adm_C` / `constraint_set_C` | `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` and `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_composition_adm_rustworkx_xgi_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `quotient_relation` + `Adm_C` / `constraint_set_C` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` and `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_adm_cvc5_xgi_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `quotient_relation` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` and `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `quotient_relation` + `axes_A_i` | `mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json` and `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_quotient_axes_cvc5_gudhi_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `composition_and_local_paths` + `bracketing_in_quotient` / `carrier_readout_map` | `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` and `mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `composition_and_local_paths` + `axes_A_i` | `mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json` and `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_composition_axes_rustworkx_gudhi_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |
| `Adm_C` / `constraint_set_C` + `axes_A_i` | `mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json` and `mc_v1_axes_gudhi_tool_lego_fit_probe_results.json` | `system_v5/ops/formal_scouts/results/mc_v1_adm_axes_xgi_gudhi_coupling_probe_results.json` | `classification=scratch_diagnostic`, `evidence_level=tool_tool_coupling_probe`, no promotion, no stage movement |

The coupling source is:

```text
system_v5/ops/formal_scouts/sim_mc_v1_quotient_path_cvc5_rustworkx_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_adm_bracketing_xgi_toponetx_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_composition_adm_rustworkx_xgi_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_quotient_adm_cvc5_xgi_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_quotient_axes_cvc5_gudhi_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_composition_axes_rustworkx_gudhi_coupling_probe.py
system_v5/ops/formal_scouts/sim_mc_v1_adm_axes_xgi_gudhi_coupling_probe.py
```

First coupling receipt summary:

```text
all_pass=true
positive=3/3
negative=3/3
boundary=7/7
load_bearing_tools=cvc5,rustworkx
promotion_allowed=false
formal_admission_allowed=false
stage_movement_allowed=false
stage4_unlock_allowed=false
```

The coupled positive case uses a rustworkx finite DAG/path object over quotient
class edges and a cvc5 SAT certificate for the expected path-edge constraints.
The quotient-erasure control flips the cvc5 certificate to UNSAT, and the cycle
control breaks the rustworkx DAG observable. This is the correct next rung after
two parent tool-fit receipts, but it remains scratch diagnostic evidence only.

The second coupled positive case uses XGI admitted-record hyperedges over
bracketing/readout/status members and converts those members into a TopoNetX
signed-incidence fixture. Bracketing collapse, pairwise projection, and
empty-complex controls change or demote the coupled observable. This is also
scratch diagnostic evidence only and is not topology readout promotion.

The third coupled positive case uses GUDHI to build an axes_A_i filtration over
the admitted M(C) v1 record IDs and TopoNetX to build a bracketing/readout
incidence fixture over the same record IDs. Axis scramble, bracketing collapse,
and erased/empty-carrier controls change or demote the coupled observable. This
is scratch diagnostic evidence only and is not topology readout, axis, geometry,
or Stage 4 promotion.

The fourth coupled positive case uses rustworkx to build an ordered local-path
DAG and XGI to build admitted-record hyperedges carrying path, bracketing, rho,
constraint, and status members over the same record IDs. Path collapse, cycle
control, and scalar status projection change or demote the coupled observable.
This is scratch diagnostic evidence only and is not composition, admissibility,
topology, geometry, or Stage 4 promotion.

The fifth coupled positive case uses XGI to build admitted-record hyperedges
carrying quotient class, bracketing, rho, predicate, and status members. cvc5
certifies that every admitted hyperedge has its quotient class node; quotient
erasure flips that all-edge claim to UNSAT. Status-only projection is satisfiable
only as a demoted weaker baseline. This is scratch diagnostic evidence only and
is not quotient, admissibility, topology, geometry, or Stage 4 promotion.

The sixth coupled positive case uses TopoNetX to build a finite left/right
quotient-bracketing incidence fixture. cvc5 certifies the left/right
quotient-bracketing distinction; bracketing collapse and quotient erasure both
flip the strict distinction claim to UNSAT. This is scratch diagnostic evidence
only and is not quotient, bracketing, topology, geometry, or Stage 4 promotion.

The seventh coupled positive case uses GUDHI to build a finite axes filtration
over admitted M(C) v1 record IDs. cvc5 certifies that every admitted record has
quotient-class and axes-field presence; quotient erasure and axis erasure both
flip the strict all-record claim to UNSAT. A vertices-only filtration or
scrambled axes readout is demoted baseline evidence only. This is scratch
diagnostic evidence only and is not quotient, axes, topology, geometry, or Stage
4 promotion.

The eighth coupled positive case uses rustworkx to build an ordered local-path
DAG over admitted M(C) v1 records and TopoNetX to build a finite signed-incidence
complex over the same path, record, bracket, and readout nodes. Path collapse
changes both observables, bracketing collapse changes the incidence observable,
and a cycle plus empty-complex control demotes the fixture. This is scratch
diagnostic evidence only and is not composition, bracketing, topology, geometry,
or Stage 4 promotion.

The ninth coupled positive case uses rustworkx to build an ordered local-path
DAG over admitted M(C) v1 records and GUDHI to build a finite axes filtration
over the same admitted record IDs. Path collapse changes the graph-side
observable, axis erasure or label shuffle changes the filtration observable, and
a cycle plus vertices-only filtration demotes the fixture. This is scratch
diagnostic evidence only and is not composition, axes, topology, geometry, or
Stage 4 promotion.

The tenth coupled positive case uses XGI to build admitted-record hyperedges
carrying predicate, status, bracketing, rho, and axes members, and GUDHI to
build a finite axes filtration over the same admitted record IDs. Status-only
projection changes the hypergraph-side observable, axis erasure or label shuffle
changes the filtration observable, and an empty hypergraph plus vertices-only
filtration demotes the fixture. This is scratch diagnostic evidence only and is
not admissibility, axes, topology, geometry, or Stage 4 promotion.

Batch receipt summary after the tenth coupling:

```text
validate_receipt.py: checked=15 all_pass=true hard_finding_count=0 warning_count=0
validate_receipt.py --strict: checked=15 all_pass=true hard_finding_count=0 warning_count=0
lint_sim_contract.py: checked=15 violation_total=0
py_compile: pass for all 15 sources
hidden shortcut scan for numpy/.numpy/np./pandas/pickle/csv: no hits across all 15 sources
```

## Important Distinction

The old deferred gap table remains valid for v0: it accurately records that the v0 profile had density/probe support, a probe-relative quotient, admissibility records, controls, receipts, and a scratch ceiling, while many composition, bracketing, local path, carrier/readout, and axes fields were externalized or missing.

The quarantined v1 scratch diagnostic reduces many of those structural gaps by putting the current-schema fields into one object. That is useful, but it is still `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`. It does not unlock Stage 4 by itself.

Fresh blocker found during this reconciliation: `scripts/validate_receipt.py system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json` initially exited nonzero with `all_pass=false`, `hard_finding_count=1`, hard finding `missing_name`, and warnings for missing `demotion_condition`, `out_of_scope`, `next_lego_target`, `promotion_condition`, and `blocked_until`. The envelope generator was repaired to emit those consumer-facing metadata fields, and the envelope was rerun. Receipt validation now passes with zero warnings. This fixes metadata consumability only; it does not promote v1 or unlock Stage 4.

## Wave A Relationship

Wave A is only tool-capability evidence. It can inform future tool-lego fit probes because the no-install micro-probes show local function on tiny finite fixtures for `rustworkx`, `xgi`, `TopoNetX`, `GUDHI`, `cvc5`, `pytorch`, and `torch_geometric`.

Wave A cannot certify `M(C)_system_fit`, same-carrier geometry, topology/AI readout promotion, bridge, Axis0, physics, or manifold admission. Its own result blocks those downstream consumers until an exact consumer receipt names the finite object, explicit M(C) fields or tool-lego target, negative controls, and claim ceiling.

## Next Admissible Steps

1. Keep v1 quarantined as `scratch_diagnostic`; receipt metadata now validates, but do not stage, promote, or build downstream from it.
2. Add consumer-aware gate language if needed so consumers must cite exact v1 fields, exact controls, exact blocked uses, and required receipt metadata before any tool-lego fit or Stage 4-adjacent work.
3. Use the five field/tool fit receipts for consumer-aware gap hardening only. Any next packet must name the exact v1 field, exact fit receipt, exact consumer, and blocked downstream uses.
4. The next smallest unfilled tool-stage work should be either a missing field/tool fit receipt or another scratch-only tool-tool coupling probe that cites two prior function receipts. Do not debug a tool, field, and coupling in one packet.
5. Only later consider stage movement after the proper contract, receipt, solver/control, composition/bracketing, carrier/readout, and stage gates pass under controller review.

## Controller Verification Commands

Run these after this note, from `/Users/joshuaeisenhart/Codex-Ratchet`:

```bash
test -f system_v5/docs/maintenance/mc_gap_table_reconciliation_20260609.md
sed -n '1,240p' system_v5/docs/maintenance/mc_gap_table_reconciliation_20260609.md
jq '{classification,all_pass,promotion_allowed,formal_admission_allowed,claim_ceiling,M_C_v1_field_coverage_summary}' system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json
jq '{classification,evidence_level,all_pass,pass_count,probe_count,promotion_allowed,formal_admission_allowed,blocked_downstream_consumers,claim_ceiling}' system_v5/ops/formal_scouts/results/wave_a_cs_ai_no_install_micro_probes_results.json
jq '{classification,all_pass,promotion_allowed,formal_admission_allowed,claim_ceiling,mc_profile_summary}' system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/foundation_mc_v1_admissibility_object_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_quotient_relation_cvc5_tool_lego_fit_probe_results.json system_v5/ops/formal_scouts/results/mc_v1_composition_paths_rustworkx_tool_lego_fit_probe_results.json system_v5/ops/formal_scouts/results/mc_v1_adm_constraint_xgi_tool_lego_fit_probe_results.json system_v5/ops/formal_scouts/results/mc_v1_bracketing_toponetx_tool_lego_fit_probe_results.json system_v5/ops/formal_scouts/results/mc_v1_axes_gudhi_tool_lego_fit_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_quotient_relation_cvc5_tool_lego_fit_probe.py system_v5/ops/formal_scouts/sim_mc_v1_composition_paths_rustworkx_tool_lego_fit_probe.py system_v5/ops/formal_scouts/sim_mc_v1_adm_constraint_xgi_tool_lego_fit_probe.py system_v5/ops/formal_scouts/sim_mc_v1_bracketing_toponetx_tool_lego_fit_probe.py system_v5/ops/formal_scouts/sim_mc_v1_axes_gudhi_tool_lego_fit_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_quotient_path_cvc5_rustworkx_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_quotient_path_cvc5_rustworkx_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_adm_bracketing_xgi_toponetx_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_adm_bracketing_xgi_toponetx_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_axes_bracketing_gudhi_toponetx_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_composition_adm_rustworkx_xgi_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_composition_adm_rustworkx_xgi_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_quotient_adm_cvc5_xgi_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_quotient_adm_cvc5_xgi_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_quotient_bracketing_cvc5_toponetx_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_quotient_axes_cvc5_gudhi_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_quotient_axes_cvc5_gudhi_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_composition_bracketing_rustworkx_toponetx_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_composition_axes_rustworkx_gudhi_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_composition_axes_rustworkx_gudhi_coupling_probe.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_receipt.py system_v5/ops/formal_scouts/results/mc_v1_adm_axes_xgi_gudhi_coupling_probe_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_mc_v1_adm_axes_xgi_gudhi_coupling_probe.py
git diff -- system_v5/docs/maintenance/mc_gap_table_reconciliation_20260609.md
git status --short -- system_v5/docs/maintenance/mc_gap_table_reconciliation_20260609.md
```

As of this note, the `validate_receipt.py` commands above are expected to pass
for v1 metadata consumability and field/tool fit consumability only. Passing
receipt validators are not M(C) admission.
