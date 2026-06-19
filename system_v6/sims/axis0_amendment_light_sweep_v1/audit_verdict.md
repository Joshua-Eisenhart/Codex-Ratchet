# Independent audit verdict - axis0_amendment_light_sweep_v1

Bottom line: ACCEPTED for the narrow Supplement-1-pinned light scope. CP.11 and
CP.14 are citable from this packet as supplement-pinned light co-survivors
pending their named heavy/follow-on teeth; CP.12 is excluded by the
distinction-boundary row; CP.13 remains open + queued-heavy. This remains a
`scratch_diagnostic` packet only: no Axis-0 admission, no uniqueness, no
physics/bridge/FEP promotion, and no canonical-process promotion.

Family-status sentence:

```text
Within the already-audited committed Axis-0 carrier, the family now has the
anchor alias class plus A0.CP.11 and A0.CP.14 as supplement-pinned light
co-survivors pending heavy/follow-on teeth; A0.CP.12 is excluded by the current
distinction-boundary computation, and A0.CP.13 is open + queued-heavy for the
global Phi_0/I_c z4 bipartition computation.
```

Holodeck-consequence note: CP.12 cannot be cited as the Axis-0/render-layer
co-readout on this packet. The current formula-pinned light row reads a
different distinction: its vector is deterministically recoverable from the
Axis-3/Axis-6 style keys at majority accuracy `1.0`, so the holodeck doctrine's
expectation 2 needs to keep the connection as TBD/blocked or name a new render
adapter and earn it separately.

## Audit Metadata

| Field | Value |
| --- | --- |
| auditor | independent Codex audit, not builder |
| write_scope | only this `audit_verdict.md`; no git add/commit |
| freshness_tier | `TIER-3` because the prompt and v0 audit verdict were visible; decisive formula/vector rows were independently recomputed |
| standards_codex | `system_v6/receipts/audit_standards_codex_v1.md` |
| standards_commit | `c83842e55` |
| binding_pin_source | `34596316d:system_v6/receipts/axis0_registry_amendment_1_20260612.md` |
| v0 blocked verdict | `system_v6/sims/axis0_amendment_light_sweep_v0/audit_verdict.md` |
| claim_ceiling | `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false` |

## Verdict Table

| Check | Verdict | Notes |
| --- | --- | --- |
| CP.11 pin conformance | PASS | Source computes system typed vN entropy of the committed cell state, one-step `S_after - S_before` over committed generator images, and per-cell majority sign. No bath terms or new channels observed. |
| CP.14 pin conformance | PASS | Source computes single-cell reduced vN entropy and sums committed outgoing adjacency differences `S(dst)-S(src)`. |
| CP.12 pin/readout | EXCLUDED | The trace-norm one-step error-change vector computes, but distinction-boundary fails because Axis-3/Axis-6 style keys deterministically recover the vector. |
| CP.13 | OPEN + QUEUED-HEAVY | Adapter bound to global Phi_0/I_c with z4 typing; no fake 33-cell global proxy emitted. |
| Pin-bite rows | PASS | Fresh recomputation gives CP.11 `13` changed cells vs v0 and CP.14 `8` changed cells vs v0. The pins mattered. |
| Fork row under pins | PASS | CP.14-vs-anchor disagreement is `21` cells under the pinned formula; v0 pre-pin row was `20`. |
| Co-survivor labels | PASS | CP.11 and CP.14 pass boundary and owner guard, disagree with the anchor, and are not aliases of each other. |
| Owner guard | PASS | Deliberate chirality tracker is excluded; CP.11, CP.12, and CP.14 do not track Type1/2 chirality. |
| Julia mirror | PASS | In-memory Julia recomputation, with `main()` suppressed, returned `all_pass=true`, `reads_peer_result=false`, and the same CP.11/CP.12/CP.14 vector hashes. |
| Packet validator | PASS with caveat | Read-only call to `validate_packet(...)` passes all packet gates. Generic validator passes in default mode. Strict tool-intent mode fails on a missing canonical `tool_intent.engine_tool_intent.julia` slot. |
| Claim ceiling | PASS | Stored JAX and envelope results are `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. |

## Recomputed Values

Independent scratch recomputation of the three computed 33-cell vectors produced
these hashes, matching the stored JAX and Julia rows:

```json
{
  "A0.CP.11": "262a08d201d19e83c04ecea327a9500775fb5c21f037d46df804c2f7e99b0b8e",
  "A0.CP.12": "ace6d042330e9ec7ec4f9980e31ecb4bbb64dc6c11a8620b745b15126938d843",
  "A0.CP.14": "6f6f13db90f5a26b4c024ddd4c7e15ab4bd4e9c79b2007806fc478081139e449"
}
```

Stored/import-recomputed count table:

```json
{
  "candidate_count": 4,
  "computed_vector_count": 3,
  "cp11_pin_bite_count": 13,
  "cp14_pin_bite_count": 8,
  "fork_disagreement_count": 21,
  "owner_guard_excluded_count": 1,
  "prior_light_exclusion_count": 3,
  "queued_heavy_count": 2
}
```

Distinction-boundary rows:

```text
A0.CP.11: reads_axis0=true, axis3_majority=0.9393939393939394, axis6_majority=0.9393939393939394, tracks_chirality=false, hamming_vs_anchor=19
A0.CP.12: reads_axis0=false, axis3_majority=1.0, axis6_majority=1.0, tracks_chirality=false, hamming_vs_anchor=15
A0.CP.14: reads_axis0=true, axis3_majority=0.8787878787878788, axis6_majority=0.6666666666666666, tracks_chirality=false, hamming_vs_anchor=21
```

## Commands And Checks

Read-only/import-only checks run:

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
imported axis0_amendment_light_sweep_v1_jax.py, called build_result(), compared counts/verdicts/vector_hashes to stored JAX JSON
PY
-> all_pass=true; live counts/verdicts/vector hashes matched; pin bites 13/8; fork 21

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
rebuilt CP.11/CP.12/CP.14 vectors independently from discrete_axis0_field_v0_common committed carrier
PY
-> all three vector hashes matched stored JAX hashes; pin bites 13/8

JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e '<include Julia source with main suppressed; call build_result()>'
-> all_pass=true; reads_peer_result=false; CP.11/CP.12/CP.14 hashes matched

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_envelope_results.json
-> ok=true

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-tool-intent system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_envelope_results.json
-> ok=false; missing tool_intent.engine_tool_intent.julia

PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-tool-intent system_v6/sims/axis0_amendment_light_sweep_v1/results/axis0_amendment_light_sweep_v1_envelope_results.json
-> ok=false; engines.pytorch missing; missing tool_intent.engine_tool_intent.julia
```

I did not run the live writer entrypoints for JAX, Julia, envelope, validator,
or pytest because this audit's live repo write scope allows only this verdict
file.

## Named Caveats

1. **Scratch ceiling only.** This accepts the pinned light rerun, not Axis-0
   admission, uniqueness, bridge, physics, gravity, FEP, or canonical status.
2. **Strict generic tool-intent caveat.** The envelope carries Julia intent in
   `TOOL_INTENT_MATRIX`, but the stricter generic validator expects it under
   `tool_intent.engine_tool_intent.julia`; the packet validator passes because
   it calls the generic validator with `require_tool_intent=False`.
3. **No PyTorch/all-three claim.** PyTorch is honestly omitted for this light
   pass. Any all-three envelope or torch/autograd claim remains blocked.
4. **TIER-3 freshness.** The audit is independent in arithmetic/formula tracing
   but not blind, because the prompt and v0 verdict were visible.
5. **CP.12 is not rescued by being computed.** It has a valid light vector and
   heavy queue, but the current boundary row excludes it from Axis-0 co-survivor
   use on this carrier.
6. **CP.13 is not a vector result.** It is an adapter-bound heavy queue row only.
7. **`failed_light_rows` wording.** For CP.11 and CP.14,
   `per-cell-disagreement-from-anchor` is the non-alias/co-survivor signal, not
   an exclusion failure.
8. **Untracked packet.** `git status --short -- system_v6/sims/axis0_amendment_light_sweep_v1`
   shows the packet directory as untracked at audit time.

## Final Adjudication

`axis0_amendment_light_sweep_v1` fixes the decisive v0 formula-pin failure for
CP.11 and CP.14. The current citable light status is:

```text
A0.CP.11: supplement-pinned light co-survivor, pending heavy/follow-on teeth.
A0.CP.12: excluded-by-distinction-boundary for the current render/FEP light row.
A0.CP.13: open + queued-heavy; global Phi_0/I_c z4 computation still unrun.
A0.CP.14: supplement-pinned light co-survivor, pending heavy/follow-on teeth.
```

