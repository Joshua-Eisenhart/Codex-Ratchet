# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_signal_0004_summary_replay_audit_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - forty-step summary window versus sixty-pass retained transport surface
- kept explicit:
  - `summary.json` and `soak_report.md` say:
    - `steps_completed 40`
    - `accepted_total 640`
  - `events.jsonl`, `state.json`, and `sequence_state.json` retain:
    - `60` result rows
    - `accepted_batch_count 60`
    - `A1 60`
    - `960` total accepted across retained result rows
- why it must survive:
  - the parent's main archive value is compressed accounting over a larger retained execution lattice

## Preserved contradiction 2
- headline:
  - zero packet parks and rejects versus large semantic debt
- kept explicit:
  - packet-facing surfaces end at:
    - `parked_total 0`
    - `rejected_total 0`
  - final state still keeps:
    - `evidence_pending_len 60`
    - `kill_log_len 240`
    - `sim_promotion_status_len 360`
    - all promotion states `PARKED`
- why it must survive:
  - transport cleanliness is not semantic promotion closure in this archive run

## Preserved contradiction 3
- headline:
  - final run snapshot integrity versus event-lattice endpoint drift
- kept explicit:
  - `summary.json`, `state.json`, and `state.json.sha256` agree on final hash `6e07a4...`
  - the last retained result row ends on `d08f6d...`
- why it must survive:
  - the run closes more strongly at the snapshot layer than at the event-lattice endpoint

## Preserved contradiction 4
- headline:
  - deterministic replay versus divergent replay final hash and parked replay texture
- kept explicit:
  - `REPLAY_AUDIT.json` says determinism check:
    - `pass true`
  - replay final hash is `e840db...`
  - replay final hash does not match run-final `6e07a4...`
  - replay outcomes still end at:
    - `OK 60`
    - `PARK 481`
- why it must survive:
  - replay determinism is structurally useful but still not replay closure or replay authority

## Preserved contradiction 5
- headline:
  - root sequence retention versus missing inbox-local sequence retention
- kept explicit:
  - root `sequence_state.json` survives with `A1 60`
  - `a1_inbox` contains only `consumed/`
  - `a1_inbox/sequence_state.json` is absent
- why it must survive:
  - the archive preserves real retention asymmetry and should not be smoothed into continuity

## Preserved contradiction 6
- headline:
  - renamed strategy lanes and replay inventory versus clean validation overread
- kept explicit:
  - embedded strategy packets use a `000001` lane
  - consumed residue uses a `400001` lane
  - only the first same-position pair is byte-identical
  - replay covers the full `541` packet lattice one-for-one
  - most replay events still park
- why it must survive:
  - packet coverage and naming proximity do not collapse into clean equivalence or validation

## Preserved contradiction 7
- headline:
  - runtime-like sim evidence paths versus no local sim subtree
- kept explicit:
  - retained outputs point at runtime-like `sim/sim_evidence_*` paths
  - the archive run root contains no local `sim/` directory
- why it must survive:
  - this run preserves structurally rich evidence references without preserving local evidence bodies

## Non-preserved overreads
- not preserved:
  - forty-step summary counts as the full retained execution truth
  - zero packet parks and rejects as proof of no semantic burden
  - replay determinism as proof of replay closure or superior final-hash authority
  - root sequence retention as proof of inbox-local sequence continuity
  - renamed consumed packets as clean identity-equivalent strategy history
  - runtime-like sim paths as proof that local evidence bodies were retained
