# FLAGGED — 1Q Registry Body-Hash Drift on Rebuild (2026-06-12, integrity investigation)

```yaml
receipt_kind: integrity_flag
severity: HIGH (the frozen substrate is the foundation of the entire climb)
trigger: the helper-drift refresh (codex2) found that rebuilding gcm_object_id_freeze_v0's
  registry produces registry_body_sha256 = 4308e9b7...94b711c3, but the committed value +
  the helper's EXPECTED_REGISTRY_BODY_SHA256 = 0fddf60c...c6221ed; gcm_object_id stays stable
  (gcmobj_a40e54e1...). Value diff NOT empty -> refresh correctly STOPPED, no overwrite.
status: UNDER INVESTIGATION — do not build new substrate-consuming packets on the assumption
  the 1Q registry body is reproducible until this is classified
```

## The two hypotheses (the investigation must decide)

H1 (BENIGN — serialization non-determinism): the registry BODY serialization has a
non-canonical element (dict ordering / float repr / set iteration) that rebuilds to a
different byte string, while the gcm_object_id (computed over a canonical subset) stays
stable. FIX: canonicalize the body-hash input (sorted keys, pinned float format), recompute,
repin EXPECTED_REGISTRY_BODY_SHA256 once, byte-stable thereafter.

H2 (SERIOUS — source drift): the carve/freeze SOURCE genuinely changed since the registry
was frozen, so the rebuild legitimately differs. This would mean the frozen substrate is NOT
reproducible from current source — a foundational crack requiring a re-freeze + a sweep of
everything that cited the old body hash.

## Context that bounds it

The fresh-context verification (10bf57a1f, earlier today) RECOMPUTED the 1Q registry and got
0fddf60c (matching). The drift appeared AFTER the helper was edited (2Q/3Q/4Q extensions). So
the most likely cause is H1 (the rebuild PATH now serializes differently, perhaps via a
helper import), not H2 (the carve math is unchanged — gcm_object_id is stable, which is
computed over the survivor content). But this MUST be confirmed by byte-level diff, not
assumed.

## The gate

No paper-over: the refresh did NOT overwrite (correct). The investigation byte-diffs the
rebuilt body vs committed, identifies the differing bytes, classifies H1 vs H2, and only then
fixes (canonicalize+repin for H1; re-freeze+sweep for H2). The gcm_object_id stability is
reassuring but not sufficient — the body hash is a committed integrity claim and must be
reproducible or honestly re-pinned.

---

## CLOSED — H1 confirmed, fixed, reproducible, drift-immune (2026-06-12)

RESOLUTION: **H1 (benign).** Byte-diff (codex1 investigation + codex2 fresh-context audit + controller)
confirms the ONLY differing hash-input bytes are `source_locks.substrate_check_helper` (the helper's
git_last_commit + sha256, which moved when the helper was edited for the 2Q/3Q/4Q extensions). ALL math
is byte-identical: gcm_object_id (gcmobj_a40e54e1...), pinned_spec_sha256, all 16 survivors / 8 classes /
6 regions, counts. **H2 (source drift) RULED OUT.**

FIX (5 `.py` files; ZERO results.json touched — no re-freeze, no identity change, no math change):
- `gcm_object_id_freeze_v0.py`: `FROZEN_SOURCE_LOCKS` pins the helper source-lock to its at-birth value
  (e4bcfb05...) so the 1Q registry reproduces 0fddf60c byte-stable regardless of future helper edits.
- 1Q validator: asserts the frozen lock == the frozen constant (anti-tamper preserved against a known value).
- 2Q/3Q/4Q validators: exclude helper-OUTPUT diagnostic control subtrees from the byte-reproduce check
  (version-dependent helper echoes) + ADD a LIVE negative-rejection re-run.

VERIFICATION (controller + codex2 FIX_SOUND on 5 falsifiers + grok blind panel):
- 1Q rebuild reproduces 0fddf60c...c6221ed byte-exactly; 2Q 57c8b47b / 3Q 623785e4 / 4Q bf92c850
  registry hashes UNCHANGED; zero results.json drift.
- Drift-immune: simulated helper sha-change AND output-schema growth -> all four stay green.
- grok blind panel found a residual negative-rejection coverage gap; hardening (live negative re-run) added;
  empirically proven: injecting a helper regression (always ok=True) -> all 3 downstream validators go RED.
- Anti-tamper: frozen-lock tamper, survivor-row tamper, wrong-substrate payload, AND helper-regression all caught.

**GATE LIFTED:** the 1Q registry body is reproducible (drift-immune) and honestly pinned. New
substrate-consuming packets (incl. 8Q carve) are re-enabled. Ceiling unchanged: scratch_diagnostic,
carrier/pins-relative; NOT a re-freeze, NOT an identity change, NOT a math change, NOT canonical-by-process.
