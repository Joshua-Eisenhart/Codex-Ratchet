# ClaimGate post-mortem — what it missed and why (2026-07-22)

The webui audit (doc sha `63352c17…`) found real holes in gates I had already
called hardened. This is the honest accounting: each miss, why it happened,
and the control that now encodes it. A gate that has not failed a hostile test
has not been tested.

## The misses

### 1. Trusted metadata instead of re-deriving
The original seal read `engines_ran: true` and believed it. A forged boolean
passed. **Why missed:** the gate was written to check the receipt's story, not
the world. **Class:** fake-input (threat move #2). **Now encoded:** seal
re-runs the jax leg; envelope check re-hashes every artifact from disk; the
carrier stage's mask is re-verified by an independent test the producer
cannot influence.

### 2. Mock receipts could reach ADMITTED
The canary's mock stages wrote `proof_status: UNSAT` and the auditor admitted
the chain. Caught by Grok, confirmed by the webui audit. **Why missed:** the
gate distinguished valid-vs-tampered but not real-vs-placeholder — no payload
axis existed. **Class:** unlabeled-placeholder laundering. **Now encoded:**
`payload: real|mock` on every manifest; any mock parks the run
(mock quarantine). Unofficial/stress sims use the same channel: they exercise
engines, they never admit.

### 3. SAT treated as a crash
`--force-fail` exited 1 before publishing, so a counterexample never reached
admission — negative science was converted into an infrastructure failure and
lost. **Why missed:** one exit code was carrying three meanings. **Class:**
status-axis collapse. **Now encoded:** three axes
(`execution_status` / `scientific_status` / `proof_status`), SAT publishes a
`COMPLETED/COUNTEREXAMPLE/SAT` receipt that reaches the envelope check and is
rejected-with-evidence-preserved; UNKNOWN parks separately.

### 4. One self-certifying gate
`physics.claim-admission` interpreted the proof, decided truth, and wrote
canon in one function — collapsing claim intake, evaluation, and settlement.
**Why missed:** I designed the gate as the terminal authority instead of one
link. **Class:** authority collapse. **Now encoded:** the `.mjs` is a
NON-FINAL CR-side envelope check; the finalizing TS capability is WITHDRAWN;
truth belongs to Lev `core/eval`, settlement to policy. Composition, not
merger.

### 5. Claim ceilings absent
"Gate M1 PASSED — smuggling structurally impossible" claimed physics from a
2-colorability witness. **Why missed:** naming drifted upward (calibration →
Gate → Ratchet) with no ceiling field forcing the licensed conclusion.
**Class:** claim inflation. **Now encoded:** `claim_ceiling` in the carrier
receipt ("carrier property only"); the canary's flow header states it proves
transport only.

### 6. No hostile-control suite
Every gate was tested on its happy path plus the failures I could imagine.
The audit's Campaign-0 list (digest mutation, missing parent, renamed metric,
stale policy, duplicate JSON key, NaN, timeout, solver UNKNOWN, solver SAT,
false self-report, human override) is the checklist a gate must fail-closed
against BEFORE it guards anything. **Why missed:** builder tested own gate.
**Class:** self-audit. **To encode:** the hostile-control fixture set is the
next ClaimGate deliverable (Slice A acceptance campaign); every future gate
change reruns it.

## The pattern underneath

All six are one failure: **the gate believed the story it was handed** —
metadata, exit codes, its own naming, its own tests. The correction is one
principle applied everywhere: re-derive from bytes, label every axis
separately, cap every claim, and let a different authority judge than the one
that produced.

## ClaimGate as a patch over pure Lev (owner directive 2026-07-22)

ClaimGate is not a fork and not inside Lev: it overlays a pure current
`lev-os/leviathan` install. The overlay surface:
- CR-side: three_engine_seal + envelope check + hooks (exists, this repo);
- Lev-side: a registered eval contract in `core/eval` (the seam EXISTS
  upstream — with CR eval tests already in the fable/cr-sim-eval-pack work
  now orphaned in ~/lev-main; salvage = re-apply as patch, not assume live);
- the hostile-control fixture set as the patch's own test suite.

Open question the owner posed: what minimal sim-engine capability does
ClaimGate itself need (if any) to make Lev better? Candidate answer so far:
only exact re-derivation (a jax/julia leg re-run) and typed predicates —
i.e. the engines as VERIFIERS, not as runtime dependencies. To be settled by
the Slice A build.
