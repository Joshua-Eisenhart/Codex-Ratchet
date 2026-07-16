# Root presentation packet v0 — read this first if you arrived with no context

This directory holds the FIRST claim-bearing receipt packet built under the Ratchet v0.3 process
(`../../RATCHET_SPEC.md` is the process authority; `../../ratchet/GRADIENT_DRIVE.md` is the drive law).

## What the packet tests

One finite history of constrained distinction attempts (an immutable seeded stream of
`(history_prefix, probe, mark_a, mark_b, verdict)` records) is handed to five rival presentations, each of which
builds its own structure from the stream alone:

- G1 — contextual partial distinction table
- G2 — probe-blind support + equivalence + quotient (the legacy shape)
- G2P — probe-respecting quotient (added by an audit-forced reopen; see below)
- G3 — pre-object event/incidence structure
- G4 — history-indexed order-sensitive table

Frozen obligation: retain one named distinction across a supplied update without pre-given object identity.
Drive (v0.3): a typed finite distinction potential V (count of unresolved obligation-relevant distinctions);
transition requires a licensed nonzero gradient — no gradient, no tooth.

## Result (ceiling: TESTED_SURVIVOR, scratch_diagnostic, promotion_allowed=false)

Survivors G1, G2P, G3, G4; probe-blind G2 fails (its quotient merges the two marks the obligation must keep
distinct); kernel-computed minimal frontier: {G1}. Transition: CLIMB. The equivalence/quotient FAMILY is NOT
excluded — only the probe-blind variant died. Ten open attacks are recorded in the receipt; they are load-bearing
caveats, not footnotes.

## Why you should trust the numbers more than the prose

This packet was audit-killed once and hardened twice. `graveyard/AUDIT_FINDINGS_v0_20260710.md` is the append-only
ledger of every fabrication found by fresh-context adversarial audits (hardcoded kill reasons, decorative controls,
a shared-carrier root violation, a strawman quotient, and finally a gameable injection detector — each either fixed
or honestly demoted to an open attack). The frozen corpses of earlier versions live beside it with hashes.
`python3 packet.py` regenerates `receipt.json` byte-identically (seed 0);
`python3 ../../ratchet/ratchet_kernel.py --validate receipt.json` must return ok:true.

Nothing here is canonical. The receipt is the claim; the graveyard is the evidence that the claim was attacked.
