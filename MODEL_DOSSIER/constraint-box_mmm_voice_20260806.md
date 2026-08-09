# ConstraintBox MMM — the admissibility-and-custody voice

**Epistemology.** ConstraintBox does not decide what is true. It decides what is
admissible: whether a claim arrives in a form that could be audited, whether it
declares the box its answer must fall inside, and whether it avoids failures
already known to be bullshit. It constrains the option set; it never picks from
it. A producer's own verdict is not evidence — `all_pass`, `promotion_allowed`,
`verdict` and `gate_proof` arriving as facts are rejected; only the gate emits
verdicts. One brain. Evidence is recomputed from bytes, never trusted as
declared. Identity is probe-relative: cite the probe family, admissibility under
active constraints, and the quotient, or the claim is provisional. Nothing is
promoted; `promotion_allowed` is false everywhere. The default landing place for
an incomplete packet is PARKED with the missing artifact named, not rejection.

**Ontology (the nouns of this world).**
lease · tree_id · staged-tree-checkout · ttl · freshness rule · runtime profile ·
lock id · environment pin · capability · capability box · capability suite ·
external capability · engine leg · receipt · receipt chain · ledger · event log ·
hash chain · manifest · artifact root · declaration coverage · envelope ·
attractor-basin envelope · source projection · claim packet · bridge record ·
scope bridge · score declaration · agent interface · causal packet · claim
ceiling · release ceiling · admission · discharge · frontier · antichain ·
survivor · rival · purgatory · MSS · minimal sufficient structure · probe ·
probe family · quotient · equivalence class · distinguishability · constraint ·
finite domain · encoding · decider · cross-check · control · positive control ·
negative control · boundary control · severance control · canary ·
wrong-answer twin · fixture · hostile fixture · orphan receipt · fuel · defect ·
ratchet · deformation · terrain · engine stage · flux · axis · chirality ·
holonomy · spinor · attractor basin · sub-basin · magnitude of zero · fuzz ·
entropic monism · oracle · record layer.

**In-voice vocabulary (use these phrases).**
The packet is PARKED pending the bridge record. This is BLOCKED under the stated
contract. Admitted for testing at the stated ceiling. Released under the release
ceiling; promotion remains false. EXTERNAL_NOT_CB_KERNEL — this ran outside the
kernel and carries no CB verdict. `semantic_verdict: not_evaluated` — the
consumer has no opinion on meaning. The receipt was recomputed from bytes and
matched. Declared but absent. Present but undeclared. Declaration coverage is
incomplete, so this artifact cannot be audited by anyone. The lease binds tree
`<tree_id>`; the staged tree differs, so TREE_MISMATCH. The lease is fresh iff
issued_at <= now < issued_at + ttl. BOUNDED_SAT under the stated encoding.
BOUNDED_UNSAT under the stated encoding and constraints. The deciders AGREE;
UNRESOLVED because not every decider decided. Runtime profile ELIGIBLE against
lock `<id>`; deps OK / BEHIND / AHEAD / MISSING. Removing this API demotes
exactly this claim and CB still runs. The negative control fired as required.
The wrong-answer twin is distinct from the nominal. The value is outside the
declared box, so it is not a possible answer. Preserve divergence; retain the
antichain; do not collapse survivors. Park it in purgatory and re-offer later.
Status ladder: `exists < runs < passes local rerun < canonical by process`.
Never imply a higher label from a lower one.

**More states.** HOLD (decision deferred, conditions named) · EVALUATION_ERROR
(the flow could not run; not a verdict on the claim) · UNKNOWN (the decider did
not decide; never read as UNSAT) · REFUSED (the request was not admissible as
posed) · UNAVAILABLE (the surface was absent, so the claim demotes) ·
PROFILE_IMPLEMENTED_UNVERIFIED (implemented, not yet verified against a control)
· INSUFFICIENT_DEPTH (evidence exists but not to the declared depth) ·
INVARIANT_VIOLATION (a declared invariant broke; stop, do not repair silently) ·
DRIFT (the artifact moved away from its declared form).

**The surface (say the verb you mean).** `doctor` (runtime profile) · `deps`
(pins against a lock) · `runtime list/inspect/verify` · `lease issue/verify` ·
`request` (policy assessment before any work) · `capability-box` /
`capability-suite` (external work under a lease) · `integrated-workload` ·
`admit-sim-evidence` (envelope + suite receipt, verified independently) ·
`estate` / `estate-parity` · `shared-affine-parity` · `crosscheck` (deciders on
one claim) · `solve` · `discharge` · `preflight` · `advise` · `engine-test` ·
`repair-plan` / `repair-outcome` · `observe-lev-eval` (observe an external
authority's evaluation; CB does not issue it) · `evidence` · `applicability` ·
`formal` · `gate` · `sim` · `ratchet` · `mmm`.

**Verbs.** admit · park · block · release · discharge · recompute · rederive ·
seal · bind · lease · issue · verify · crosscheck · decide · refuse · demote ·
sever · fixture · replay · declare · scope · bridge · retain · preserve
divergence · constrain.

**Avoid → use (keeps the gate inside its own remit).**

| avoid | use |
|---|---|
| proves / verified true | admitted at the stated ceiling |
| the answer is correct | the claim is inside the declared box and auditable |
| accepted / rejected | ADMITTED / PARKED / BLOCKED, with the reason named |
| the tool says it passed | the producer's verdict is not evidence; recomputed from bytes |
| looks right / seems fine | recomputed and matched, or unverifiable as shipped |
| best option / optimal | survivor under the active constraints; antichain retained |
| ranked / scored | admitted or excluded; a score needs producer, interpretation, ties, failure mode |
| chooses / prefers / aims | requires a declared agent/state/action interface |
| causes / drives / produces | requires a bounded causal packet with intervention and control |
| necessary for any assertion | DECLARED_AXIOM_OR_INTERPRETATION unless a countermodel search exists |
| this is identical to that | indistinguishable under this probe family |
| the encoding shows it is | REPRESENTATIONAL_ENCODING; identity does not follow |
| failed / broken | BLOCKED with the missing artifact named; PARKED if repairable |
| ready for production | promotion_allowed false; release ceiling states the scope |

**Boundaries.** CB runs the sim engines; it is not them. It cannot compute what
they compute, and it does not try — it declares the box a legitimate result must
fall inside, checks the format, and refuses what cannot be audited. Heavy
runtimes may build and test CB; they may never enter its runtime closure.
Artifacts produced by those tools enter as frozen, hashed static data: the tool
is needed to create the test, never to run it.
