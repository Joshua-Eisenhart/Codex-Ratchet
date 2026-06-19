# system_v6 — clean start (2026-06-09)

The MINE is v5 and earlier **and the wiki** (`~/wiki` — concepts, projects, raw owner docs). v6 starts empty and grows only by need: math objects, doctrine, probe families, and geometry come from mining either source; both confer zero status on import.

## Intake rules (narrow, gated — the only rules here)

1. **No copy-sweeps.** A file enters v6 only when a current build card needs it. Bulk imports are banned.
2. **Imports re-earn status.** v5 history confers nothing. On arrival a sim starts at `exists`, must pass the current gates fresh (validator `--require-pytorch` [+ `--require-source-backed` where claimed], capability-probe criterion for any `load_bearing` label), and keeps the standard ceilings (`classification`, `promotion_allowed`, `formal_admission_allowed`).
3. **One home.** Importing a surface supersedes its v5 copy; the v5 copy is historical from that moment — never edited to show progress, never the authority.
4. **Current conventions only:** identical PIN block across engine legs; like-for-like shared-scalar divergence (never aggregate over different observables); evidence ladder = Julia canon value → exact/symbolic confirmation → z3+cvc5 derive-in-solver → cross-engine agreement as smoke test only; numpy/scipy/mpmath control-lane only; deprecated tools per the skill rosters (torch_ga/clifford → kingdon, qutip-jax → dynamiqs, jraph → PyG, qiskit/pennylane/cirq out).
5. **Three engines by role**, not TMR-as-evidence: Julia = canon (structure-carrying types, arbitration), JAX = batched/exhaustive sweeps, PyTorch = graph/network/autograd machinery. All-three mode only for claim-bearing rungs; diagnostics may run Julia + one consumer with the mode declared.

First-import candidates when a task needs them (all already on current conventions, verified 2026-06-09): `foundation_nested_hopf_weyl_signed_cut_ratchet` (GENUINE-WITH-CAVEATS, hardened), the 8 new capability probes, `validate_three_engine_sim_result.py` + `verify_load_bearing_has_capability_probe.py`.

## Layout (dirs created on first use, never pre-made empty)

```
system_v6/
  README.md                  # this contract — the only doc in v6; receipts are the record
  sims/<object_id>/          # ONE FOLDER PER SIM, atomic: <id>_julia.jl, <id>_jax.py,
                             #   <id>_pytorch.py, <id>_envelope.py, results/*.json,
                             #   audit_verdict.md (fresh-context verdict lives WITH the sim)
  probes/<engine>/           # capability probes + their result JSONs (the engine x math-class
                             #   matrix cells); julia/ jax/ pytorch/ shared/
  carrier/julia/             # the strict Julia canon project (Project.toml + Manifest), imported
                             #   once, the ONLY Julia env sims may use; optional pkgs NEVER here
  optional/<name>/           # isolated pilot projects, own Project/env (e.g. acsets, kingdon-swap)
  receipts/                  # cross-sim artifacts only: capability-matrix snapshots, campaign
                             #   verdicts — flat files, date-stamped, no subtree growth
  foundations/               # the ONLY doc surface: root axioms + doctrine, owner-voice.
                             #   Rules: every claim labeled OWNER-QUOTE / ALIGNED-FORMAL-HOME /
                             #   ASSISTANT-GLOSS with sources; no LLM-invented numbering schemes
                             #   (the A0-A8 lesson); AXIOMS never conflated with AXES; drafts are
                             #   drafts until owner approves exact wording; few files, tuned hard
```

Layout rules: a sim's legs, envelope, results, and audit verdict never separate (the v5 scatter
— legs in `julia_carrier/`, results in two places, verdicts in `/tmp` — is the anti-pattern).
Shared gate scripts stay in repo `scripts/` (machinery is referenced, not copied). No `docs/`
tree will ever exist here. Anything not fitting these six entries triggers a contract review
before a seventh is added.

## Absence-claim rule (owner-prompted, 2026-06-09)

No lane may write "needs foundations / needs definition / missing / absent" for any item without FIRST: (1) grep-quoting the exact searches run against `system_v5/READ ONLY Reference Docs/`, `READ ONLY Legacy core_docs/`, `~/wiki/raw/`, and any file already cited in its own sources-read line; (2) distinguishing "math not on file" from "sim/receipt not yet built" — these are different claims. Absence requires the same evidence standard as presence. (Failure mode this fences: a lane cited `terrain math.md` as read, while marking items answered at lines 80-90 of that file as "needs foundations.")

## Novelty-claim rule (owner-prompted, 2026-06-09)

Same standard as the absence rule, mirrored: before recording an owner statement as NEW doctrine ("owner lock", "owner decision", dated to a session), grep the corpus (Rosetta transcription, READ ONLY Reference Docs, wiki concepts/raw, prior receipts). If the content is already on file, cite the standing sources and mark the session statement as a RESTATEMENT. Dating standing doctrine to the day it was repeated misattributes novelty and corrupts provenance. (Failure this fences: the Axis-0 Ne/Ni-vs-Se/Si feedback polarity — stated throughout the corpus including the owner's pre-AI workbook — was recorded as a 2026-06-09 "owner lock.")

## The Workflow (locked 2026-06-09 — proven over 10 sims; this is the operating loop)

ROLES: Owner = direction, wording surgery, owner-only mappings (e.g. Type1/Type2<->Rosetta sides). Overseer (Claude/Fable, thin) = cards, lane launches, one-command mechanical verifies, ceiling enforcement, synthesis. codex2 (all effort levels, mass-parallel) = ALL building, auditing, blind derivation, corpus mining. grok-4.3 + gemini-3.1-pro (API) = independent theory advisories on math-bearing claims, cite-or-discard. Hermes = wiki/provenance surface (never written from repo lanes).

THE LOOP, per bounded object:
1. PICK one object from the dependency queue (or owner directive). One object, one claim, one card.
2. MINE FIRST: corpus search before the card (absence rule + novelty rule). Found sources get cited INTO the card; nothing is "missing" or "new" without the greps.
3. CARD: math-first (standard terms lead, owner labels annotate); PIN block mandatory; controls that can fail; ceiling stated; exact files-to-create list.
4. FAN-OUT (file-disjoint, background, no waiters): xhigh builder + medium BLIND expected-values (never sees the build) + high adversarial pre-audit + low preflight when assets are reused. Effort spread = council diversity.
5. MECHANICAL VERIFY (overseer): validator --require-pytorch personally run; build numbers vs blind-lane numbers. Builder's word is never evidence.
6. FRESH AUDIT: separate codex2 (did not build) executes the pre-audit checklist + recomputes at least one value by hand. Verdict: GENUINE / GENUINE-WITH-CAVEATS / DECORATIVE / BROKEN. Outside advisories where the claim is theory-bearing.
7. HARDEN the named gaps — one bounded batch, additive instrumentation keeps claim values byte-stable; re-verify.
8. COMMIT atomically: sim + results + audit_verdict.md together (per-sim folder). Campaign artifacts -> receipts/, date-stamped.
9. RECORD: memory entry; scaffold additions only under provenance discipline (owner-quote / standing-source / assistant-gloss).
MASS-SPAWN where file-disjoint; never two writers on one path. DECORATIVE verdicts are normal output, not failures — the loop exists to catch them (it caught 2 of 10 cores today and both were repaired to gates).

THE PLAN (current ladder positions, 2026-06-09):
A. Foundations/doctrine — scaffold sections 0-21 standing; OPEN: owner wording surgery (root sentence, Axis-0 wording, Hume/Jung/Pauli placement).
B. M(C,t) packet — THE FRONT DOOR per constraint-manifold-architecture (dynamic: carries the witness-step index W_n). NEXT MAJOR BUILD.
C. Geometry on M(C) — ratchet layers + currents. DONE at scratch: operator packet (commutator lattice), terrain packet (8 generators + invariant columns), flux emergence (curvature member, Chern=1). NEXT: 64-cell decoding matrix; axis-independence discriminators 0/3/6; Xi bakeoff (behind B).
D. Carrier discriminators — DONE: G2 installed, lattice seats, PG(3,2)/box-kites. NEXT: split-O/split-G2; Cl(8) triality; ring_checkerboard_support_graph_probe.
E. Engines — dual-stack witness DONE at scratch (gates met, literal loops, ablations). NEXT: 64-state runtime distinctness (currently n_distinct=16).
FENCED until earned: Axis-0 closure, Xi selection, bridge, physics names, world engine.

## Queue ordering correction (owner, 2026-06-09)

IGT-facing work (win/lose readout follow-ons, I Ching/automaton encoding, IGT grammar tests) is DEFERRED until the QIT engines are done. The IGT/symbolic context was big-picture orientation, not build queue. The QIT engine track runs on math already in hand: M(C,t) packet (in flight) -> 64-cell operator/terrain precedence matrix -> axis independence discriminators 0/3/6 -> engine runtime distinctness (n_distinct 16 -> ?) -> Xi bakeoff. IGT correspondence tests come AFTER, as the independent-sim-then-compare rule already requires (igt-to-qit-engine-genealogy: never assert the connection in advance).
