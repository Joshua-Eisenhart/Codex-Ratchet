# Codex v4.3 Route Cards

These are Codex-native route cards for Wizard v4.3 mode. They are not completed agents unless the runtime returns a real subagent receipt.

Each route should return:

```yaml
route_id:
sources_read:
mmm_l0_ref:
mmm_v4_3_ref:
saliency_preload_before_rules:
what_checked:
conclusion:
open_or_blocked:
claim_boundary:
output_artifact:
status:
```

## `v43.object_card_guard`

Purpose: preserve the primary object before any council, proxy, sim, or follow-up claim.

Read first:

- `PACKET_MANIFEST_v4_2.md`
- `SALIENCY_TRANCHE_02_V4_3_OBJECT_PRESERVATION_MAINTENANCE_CANDIDATE.md`
- task object card or packet JSON

Check:

- object statement and hash;
- first-class fields;
- source anchors;
- required invariants;
- evidence spine;
- blocked consumers.

Acceptance: validator exits 0 and the route also names any semantic drift that schema validation would not catch.

Blocked when: object card is absent, hash is stale, source anchors are missing, or the task wants to claim progress without a card.

## `v43.proxy_drift_scanner`

Purpose: catch adapter, probe, analogy, metric, model, or carrier language that is being promoted into object truth.

Read first:

- object card;
- lateral mappings;
- compiled answer or follow-up packet.

Check:

- `use_type`;
- `promotion_allowed`;
- `preserves`;
- `loses`;
- `preconditions`;
- `kill_control`;
- positive vs forbidden terms.

Acceptance: every lateral move is typed, every promotion is legal, and every proxy/analogy states what it loses.

Blocked when: Axis0, FEP, scalar entropy, PEPS3D, Wolfram, model consensus, or a readout becomes the object.

## `v43.mmm_admission_gate`

Purpose: improve MMMs without promoting reference-only candidates by vibes.

Read first:

- `/Users/joshuaeisenhart/wiki/wizard/packet-v4-3-current/mmm/FULL_MMM_v4_3.md`;
- `/Users/joshuaeisenhart/wiki/wizard/packet-v4-3-current/mmm/COMPACT_MMM_v4_3.md`;
- `/Users/joshuaeisenhart/wiki/wizard/packet-v4-3-current/mmm/mini/MEMBER_MINI_MMM_REGISTRY_v4_3.md`;
- target candidate MMM slice.

Check:

- exact duplicates;
- semantic overlap;
- behavior comparison target;
- conformance requirement;
- promotion boundary.

Acceptance: candidate status is one of `duplicate`, `merge_candidate`, `new_reference_only`, or `admitted_after_conformance`, with evidence for the label.

Blocked when: no conformance check exists, behavior comparison is absent, or the candidate is being promoted only because it sounds useful.

## `v43.maintenance_route_truth`

Purpose: keep cron, worker, wiki, memory, and shared-state maintenance receipt-bound.

Read first:

- current task;
- claimed worker or cron receipt;
- touched files;
- current process or file evidence when available.

Check:

- observed vs inferred route state;
- worker launch status;
- MMM preload fields;
- output artifact path;
- shared-state write owner.

Acceptance: route status is `observed`, `blocked`, `deferred`, `superseded`, or `not_run`, with a named evidence path or command result.

Blocked when: historical job ids are treated as live, controller-local thinking is counted as a worker, or memory recall is treated as current proof.

## `v43.wiki_processing_router`

Purpose: attach v4.3/MMM maintenance to actual wiki processing instead of only route discussion.

Read first:

- owner correction or source packet;
- current wiki receiver page;
- relevant index/front-door page;
- current v4.2/v4.3 claim ceiling.

Check:

- which wiki page now teaches the correction;
- whether the update is source processing, planning, or runtime promotion;
- link/probe state when a probe exists;
- downstream blocked consumers.

Acceptance: one bounded receiver surface is named, with pre/post state and a claim ceiling.

Blocked when: the task discusses live sims or model convergence but no wiki receiver or claim ceiling is named.

## `v43.pattern_intake_porter`

Purpose: port useful Claude or Hermes skill/agent mechanics into Codex without authority contamination.

Read first:

- current repo/wiki authority;
- source Claude or Hermes skill/agent/receipt;
- `claude-pattern-intake` packet skill when Claude material is involved;
- Hermes bounded-intake rules when Hermes material is involved.

Check:

- source type;
- mechanic accepted or rejected;
- authority reason;
- target Codex surface;
- minimal test;
- risks.

Acceptance: each accepted mechanic becomes a pattern card with a target surface and local validation command. Each rejected mechanic has an authority or route-truth reason.

Blocked when: the port copies source doctrine verbatim, imports Claude/Hermes as authority, or creates a Codex skill that cannot be validated locally.
