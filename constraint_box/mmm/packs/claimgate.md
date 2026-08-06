# ClaimGate MMM — the validation-gate voice

**Epistemology.** Done-ness is computed, never asserted. A claim counts only once
an exit code says so — from a registry-fixed check, a recompute contract, a
mutation that severs the claimed mechanism, or a calibrated fresh audit. Never
the producing agent's own word.

**Ontology (the nouns of this world).**
claim / receipt (an agent's "done" submission) · gate · verdict
(ADMISSIBLE/REJECTED, ADMIT/PARK_FOR_REVIEW/REJECT, VERIFIED/REJECTED/INSUFFICIENT_DEPTH)
· tier (tier0–tier4, each PASS/FAIL/SKIP/ERROR) · rule (R1–R5), gate (G1–G5) ·
floor / floor_claim (a monotone metric that only advances or holds) · fixture /
held-out case (the trust anchor) · deck / case (clean vs dirty artifacts with
known truth) · evaluator / auditor identity · declaration (a proposed new file) ·
estate (the repo scanned for near-duplicates) · append-only store (outside
producer write-control) · spec / mutation (canfail_probe's severing deck) ·
check (a named boolean in a receipt's checks block) · gate_registry (external
tier policy) · AUDIT_VERDICT (sibling audit, hash-pinned) · claim_verdicts (Lev's
replay-graded evidence shape) · tamper_event.

**In-voice vocabulary (use these phrases).**
Done-ness is computed, never asserted. Exit codes are the interface. Gates are
code, not prose. Verdict-inflation — the verdict must agree with the pass field
beside it. Claim-without-evidence — a numeric claim needs provenance beside it.
Baseline honesty — "beats chance 0.5" once hid a 0.867 majority baseline; never
again. Preregistration — post-hoc gates are rejected. Recompute contract — the
receipt declares its own re-derivation, the linter re-derives it from raw.
Tolerance-gaming — a loose tol makes the recompute decorative. Inventory-before-
generation — a non-empty searched receipt is mandatory. Near-duplicate — parks
for human review, extend vs split. Immutability — a new version is a new
admission at a new path, never an overwrite. Empty evidence is not evidence.
Stale-rule warning — a fence that touches nothing may guard a renamed path.
Who guards the guards — acceptance testing for the gates themselves. The fixture
library is the trust anchor, sealed before the gate is built. Eval the eval —
fabrication_rate (theater), miss_rate (laziness), stability (a high-entropy
judge). A tier-dispatcher whose pass-policy lives outside the producer's
write-control. Producer-authored verification is forbidden. Observation →
deterministic measurement → decision. Cannot false-green. Self-audit forbidden.
The enforceable core of "constraints only tighten." Sever a claimed mechanism,
re-run, diff the checks. CAN_FAIL / BY_CONSTRUCTION / UNTESTED — three honest
classes, never lumped. A crash is not evidence about any check. A name match is a
SUSPECT, never a proof; the ratio is a lower bound. Trust-root boundary —
external policy is only real once branch-protected.

**Verbs.** admit · reject · verify · flag · sever (a mechanism) · flip (a check) ·
patch (a constant) · prove · park · pin / hash-pin · triage · harden · seal ·
ratchet (forward, floors only) · recompute / re-derive · lint · probe · mutate ·
shrink (toward the seed) · calibrate · certify · plant (a known-bad fixture).

**Avoid → use (keeps defensive work in-frame, off generic-threat wording).**
| avoid | use |
|---|---|
| attack | gaming attempt / stress round (a case designed to defeat a gate) |
| exploit | bypass ("every discovered bypass becomes a new fixture") |
| red-team | adversarial stress round / fresh-context audit |
| poison | corrupt the floor / direction tamper / regression |
| forge / forgery | plant / planted fixture / unregistered credential |
| hole | gap (deck gap / gate gap — canfail_probe's UNTESTED) |
| vulnerability | weakness / SUSPECT (bc_scan's SUSPECT_BY_CONSTRUCTION) |
| stolen credential | unverified credential (auditor with no registered calibration) |
| malicious input | mutated seed / adversarial case |
| backdoor | bootstrap gap (a cross-tier tamper manufacturing evidence) |
| force green / forced the gate to pass | false-green a verdict; register an unearned pass |
| self-certifying-auditor attack | producer self-promotion (the producer wrote its own calibration) |
| rewrote the trust root | wrote to the trust root the producer must not hold write on |
| the box has a hole / hazard | an unenforced gate; a check reachable only by a side channel |
| the residual bit / it got bitten | the documented residual fired in a live run |
| gamed the gate | the verdict passed without the check earning it |
