# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_A2MID_archive_signal_0005_runtime_alignment_auditnull_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction 1
- headline:
  - repaired runtime-facing alignment versus unresolved semantic debt
- kept explicit:
  - summary, state, sequence, soak, and retained events align on:
    - `60` passes
    - `960` accepted items
  - final state still keeps:
    - `evidence_pending_len 60`
    - `sim_promotion_status_len 360`
    - all promotion states `PARKED`
    - `kill_log_len 240`
- why it must survive:
  - the parent's main value is that runtime-facing repair still does not imply semantic closure

## Preserved contradiction 2
- headline:
  - zero packet parks and rejects versus large semantic burden
- kept explicit:
  - packet-facing surfaces end at:
    - `parked_total 0`
    - `rejected_total 0`
  - state still preserves:
    - sixty pending canonical evidence items
    - three hundred sixty parked promotion states
    - two hundred forty kill signals
- why it must survive:
  - transport cleanliness is still not semantic promotion closure

## Preserved contradiction 3
- headline:
  - final run snapshot integrity versus derivative endpoint drift
- kept explicit:
  - `summary.json`, `state.json`, and `state.json.sha256` agree on final hash `0045ff...`
  - the last retained event row ends on `299c9c...`
  - the replay audit ends on `ed1a34...`
- why it must survive:
  - the run closes more strongly at the snapshot layer than at either derivative endpoint

## Preserved contradiction 4
- headline:
  - deterministic replay versus replay-final-hash divergence and replay parking
- kept explicit:
  - `REPLAY_AUDIT.json` says determinism:
    - `pass true`
  - replay outcomes still end at:
    - `OK 60`
    - `PARK 481`
  - replay final hash does not match the run-final snapshot hash
- why it must survive:
  - replay determinism remains structurally useful but still not replay closure or replay authority

## Preserved contradiction 5
- headline:
  - root sequence retention versus missing inbox-local sequence retention and renamed consumed lane
- kept explicit:
  - root `sequence_state.json` survives with `A1 60`
  - `a1_inbox` contains only `consumed/`
  - `a1_inbox/sequence_state.json` is absent
  - consumed strategy packets use `400001` names while embedded packets use `000001`
  - fifty-nine of sixty same-position pairs differ byte-for-byte
- why it must survive:
  - the archive preserves real continuity and identity asymmetry and should not be smoothed into one lineage

## Preserved contradiction 6
- headline:
  - signal-audit nullability seam versus nonzero adjacent math-kill metadata
- kept explicit:
  - `SIGNAL_AUDIT.json` reports:
    - `kill_kind_counts.MATH_DEF 120`
  - the same audit surface keeps:
    - `killed_math_count null`
- why it must survive:
  - the parent explicitly preserves a local audit-surface nullability drift that should not be silently repaired

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
  - aligned sixty-pass runtime-facing counts as proof of promotion success
  - zero packet parks and rejects as proof of no semantic burden
  - replay determinism as proof of replay closure or superior final-hash authority
  - root sequence retention as proof of inbox-local continuity
  - renamed consumed packets as clean identity-equivalent substitutes for embedded packets
  - runtime-like sim paths as proof that local evidence bodies were retained
  - audit null fields as permission for silent backfill from adjacent counts
