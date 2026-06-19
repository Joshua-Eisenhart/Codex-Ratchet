# Independent Audit Verdict - gcm_qca_runner_2q_v0

Audit mode: fresh read-only audit. Auditor: independent Codex audit. Freshness tier:
TIER-2 results-available. The only authorized live repo write for this audit is this
`audit_verdict.md` file. No git add, commit, generated-result rewrite, validator-result
rewrite, or pytest writer path was run.

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS.

The packet genuinely computes opposite 2Q-site finite open-chain support-rank transport
rates from realized unitaries:

- `engine_L_flux_IN_left_O1`: `L = -2` log2-qubits/step.
- `engine_R_flux_OUT_right_O1`: `R = +2` log2-qubits/step.

Claim ceiling: `scratch_diagnostic; carrier-and-pins-relative`. This is the first
computed L/R chirality-transport invariant for this specific scratch 2Q realization, not
formal admission, not a finite-ring automorphism-class GNVW index, not runtime flux family
closure, and not engine admission.

The old packet conditionality is resolved for citation at this scratch ceiling: the
committed 2Q registry object `gcm2qobj_715e9424ea66468243108751fb59395f` and body hash
`57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac` are present and
audited via the keystone commit `8326405e6`. The live runner source/result still contains
stale `in_flight_per_owner_prompt` / conditional fields because this audit was not
authorized to rewrite source or results; the verdict resolves the condition only as an
audit/citation boundary.

## Caveats That Matter

1. Mirror relation caveat: the sign flip is a real computed transport-direction flip, not
   a metadata readback. But the full L and R dressed unitaries are not proven to be literal
   spatial reflections of one identical local dressing. The source builds L as a left
   transport layer with L local dressing and R as a right transport layer with R local
   dressing. A fresh variant check shows the sign is independent of the local dressing, so
   the result is not tuned by those local gates. Cite "opposite transport realized by L/R
   rules", not "full mirror-conjugate engine pair".
2. M(C) preservation caveat: the packet's M(C) rows are registry/hash/pin preservation
   rows over resolved 2Q lineage, with `transport_only_internal_state_unchanged=true`.
   They do not recompute every stored 2Q density state after every QCA unitary and prove
   that the transformed state remains a 2Q carve survivor. Cite carrier-and-pins-relative
   M(C) preservation only, not dynamic state-space invariance under the QCA.

## Recomputed Transport Accounting

The live source uses `SITE_QUBITS = 2`, `LOCAL_DIM = 4`, and
`SUPPORT_DIM_BASE = LOCAL_DIM**2 = 16`. The support-rank routine conjugates a basis of
input-region matrix units by the realized unitary, factors the image across the cut with
an operator-Schmidt/SVD span rank, and converts:

```text
right_channel_count = log_16(right_crossing_support_rank)
left_channel_count  = log_16(left_crossing_support_rank)
signed_log_local_dim_index = right_channel_count - left_channel_count
signed_log2_index = signed_log_local_dim_index * SITE_QUBITS
```

Fresh no-write recomputation returned:

| rule | right rank | left rank | signed local | signed log2 | ratio |
| --- | ---: | ---: | ---: | ---: | --- |
| `engine_L_flux_IN_left_O1` | 1 | 16 | -1 | -2 | `1/4` |
| `engine_R_flux_OUT_right_O1` | 16 | 1 | +1 | +2 | `4/1` |
| `calibration_left_shift` | 1 | 16 | -1 | -2 | `1/4` |
| `calibration_right_shift` | 16 | 1 | +1 | +2 | `4/1` |
| `nonchiral_onsite_index0` | 1 | 1 | 0 | 0 | `1/1` |
| `balanced_pair_swap_index0` | 16 | 16 | 0 | 0 | `1/1` |
| `gauge_inserted_R_engine` | 16 | 1 | +1 | +2 | `4/1` |
| `swap_control_L_to_R` | 16 | 1 | +1 | +2 | `4/1` |

The `+/-2` magnitude follows from the 2Q-per-site local dimension. One transported site
has Hilbert dimension `4 = 2^2`, so a one-site channel contributes `+/-1` in base-4
log-index units and `+/-2` in log2-qubits/step.

## Opposite-Sign And Tuning Check

The code does not contain `right_wires` / `left_wires` flow metadata for the target rows.
`metadata_flow_fields_present` recomputed as `false` for every QCA index row.

Construction readout:

- L target: `brickwork_engine("left", ..., "L", "flux_IN_left")`.
- R target: `brickwork_engine("right", ..., "R", "flux_OUT_right")`.
- `swap_control_L_to_R` re-instantiates the R-side rule from the L-side rule; its unitary
  hash equals the R target hash. This is a direction-swap control, not a proof of full
  spatial mirror conjugacy.

Fresh no-write variant check:

| direction | local dressing | signed log2 |
| --- | --- | ---: |
| left | L | -2 |
| left | R | -2 |
| left | neutral | -2 |
| right | L | +2 |
| right | R | +2 |
| right | neutral | +2 |

This kills the "separately tuned local gates created the sign" concern. The sign is bound
to the transport direction after realized-operator rank extraction.

## Controls And Solver Gates

Fresh no-write recomputation:

- `all_pass_recomputed_no_write = true`
- quantization: all indices integer and all signed-log2 values multiples of `SITE_QUBITS`
- zero controls: `nonchiral_onsite_index0 = 0`, `balanced_pair_swap_index0 = 0`
- gauge control: `gauge_inserted_R_engine` preserves `+2`
- z3 QF_LIA contract negation: `unsat`
- cvc5 QF_LIA contract negation: `unsat`
- z3/cvc5 same-sign mutation: `unsat` in both solvers
- stored and rebuilt validator function API checks: `ok=true`, `0` errors, no write path

## Finite-Ring Fence

The standard-math note is decisive: on a finite periodic ring, the automorphism-class GNVW
index is trivial. This packet handles that correctly.

Accepted:

- computed nonzero quantity is the finite open-chain 2Q-site support-rank transport rate
  over realized unitaries;
- ring row is only a local brickwork/light-cone closure witness;
- result and envelope state `finite_ring_nonzero_gnvw_claim = "not_claimed"`;
- ring locality witness has one-site-per-half-step nearest-neighbor closure.

Rejected:

- any nonzero finite periodic-ring automorphism-class GNVW claim;
- any claim that this finite-ring row classifies the realized automorphism.

## 2Q Lineage, Hardened Helper, And G.2a

Keystone dependency:

- commit `8326405e6` is on current `main`;
- registry object id: `gcm2qobj_715e9424ea66468243108751fb59395f`;
- registry body hash: `57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac`;
- registry counts: `544` survivors, `8` quotient classes, `6` candidate regions;
- `gcm_2q_freeze_and_cut_v0` audit verdict exists and confirms the stored 2Q carrier math
  at scratch scope.

Current hardened-helper checks, run no-write through the function API:

| payload | ok | key error codes |
| --- | --- | --- |
| positive runner packet | true | none |
| lineage-free negative | false | `GCM_OBJECT_ID_MISMATCH`, `GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH`, `GCM_LINEAGE_BASE_REGISTRY_BODY_SHA256_MISMATCH`, `GCM_LINEAGE_CONSUMPTION_MISSING` |
| 2Q object with only 1Q lineage | false | `GCM_LINEAGE_CONSUMPTION_MISSING`, `GCM2Q_LINEAGE_CONSUMPTION_MISSING` |
| wrong 2Q hash | false | `GCM2Q_LINEAGE_REGISTRY_BODY_SHA256_MISMATCH` |

G.2a is satisfied by design: builder output did not author this verdict, packet fields set
`no_builder_audit_verdict=true`, and the shared boundary helper accepts independent/fresh
audit headers instead of requiring permanent audit-file absence.

Post-write no-write validation returned:

- `builder_boundary_errors_after_audit_file = []`
- stored validator function API: `ok=true`, `errors=[]`, `warnings=[]`
- rebuilt validator function API: `ok=true`, `errors=[]`, `warnings=[]`

## Citation Rule

Allowed citation:

> `gcm_qca_runner_2q_v0` is a scratch-diagnostic, carrier-and-pins-relative 2Q QCA runner
> in which realized finite open-chain 2Q-site local-unitary rules compute opposite
> support-rank transport rates: `flux_IN_left` has `-2` log2-qubits/step and
> `flux_OUT_right` has `+2` log2-qubits/step. The finite-ring component is locality/
> closure only, and the 2Q registry conditionality is resolved by the audited
> `gcm_2q_freeze_and_cut_v0` registry at commit `8326405e6`.

Required caveats:

- finite-ring automorphism-class GNVW index remains trivial and is not claimed;
- full runtime flux family rows such as `J_ent`, `J_cut`, and related currents remain 3Q
  gated;
- full mirror-conjugacy of the dressed L/R unitaries is not established;
- M(C) preservation is carrier-and-pins-relative, not dynamic invariance of all evolved
  density states;
- no formal admission, promotion, engine admission, bridge/axis/physics claim, or manifold
  closure follows from this packet.

Forbidden citation:

- "nonzero finite-ring GNVW automorphism-class invariant";
- "runtime flux family confirmed";
- "engine admitted";
- "full L/R mirror-conjugate unitary pair proven";
- "M(C) dynamically invariant under the QCA on all 2Q states";
- "formal admission" or "canonical promotion".

## Fresh No-Write Commands

The audit avoided live writer paths. In particular, it did not run the packet main, the
validator main, or pytest, because those paths write result or validator JSONs.

Fresh checks were run with the Makefile interpreter
`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`:

- imported `gcm_qca_runner_2q_v0_common.py` and called `build_packet()` no-write;
- imported `validate_gcm_qca_runner_2q_v0.py` and called `validate_packet(...)` no-write
  on stored and rebuilt payloads;
- recomputed all QCA index rows and support ranks;
- ran a local-dressing variant check for left/right transport directions;
- checked current `scripts/gcm_substrate_check.py` hardened-helper behavior against
  positive, lineage-free, only-1Q-lineage, and wrong-2Q-hash payloads;
- after writing this audit verdict, re-ran the builder boundary and stored/rebuilt
  validator function API no-write checks;
- read `~/wiki/codex-ratchet-research/standard-math/gnvw-index-1d-qca.md` for the
  finite-ring fence.
