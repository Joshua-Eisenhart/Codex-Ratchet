MEGABOOT_RATCHET_SUITE v7.4.8-PROJECTS
DATE_UTC: 2026-02-02T00:00:00Z
AUTHORITY: CANON (bundle control surface)

RELEASE_NOTE v1 (HUMAN; NON-ENFORCEABLE)
- Full regeneration: Axis-3 is now ONLY the engine-family split (Type-1 vs Type-2).
- Geometry is a constraint manifold and exists before Axes 0–6; Axes 0–6 are functions/slices on that manifold.
- Removes all Axis-3 bindings to chirality/handedness/spinor/Berry/flux language (those are legacy/candidate only).
- Bootpacks are stored as standalone files under BOOTPACKS/ (Thread B kernel remains pinned).

BOOTPACK VERSIONS (this bundle)
- BOOTPACK_THREAD_A_v2.60
- BOOTPACK_THREAD_S_v1.64
- BOOTPACK_THREAD_B_v3.9.13
- BOOTPACK_THREAD_SIM_v2.10
- BOOTPACK_THREAD_M_v1.0 (optional)

==================================================
SECTION 0 — DEFINITIONS (HARD)
==================================================

BOOT ORDER
- Human-run paste sequence to initialize threads in a new Project.

HOW THE SYSTEM RUNS
- Post-boot operational loops (S↔B, A↔SIM) with back-and-forth corrections.

SAVE LEVELS
- MIN checkpoint: PROJECT_SAVE_DOC v1 compiled from minimal fuel (snapshot + runbook + bootpacks).
- FULL+ ratchet step: PROJECT_SAVE_DOC v1 compiled from full seal fuel (snapshot + REPORT_POLICY_STATE + REPORT_STATE + DUMP_TERMS + DUMP_LEDGER_BODIES + DUMP_INDEX + DUMP_EVIDENCE_PENDING + audit-at-seal-time).
- FULL++ complete save: PROJECT_SAVE_DOC v1 compiled from FULL+ plus CAMPAIGN_TAPE v1 (batch history for deterministic replay/migration + graveyard reconstruction).

CAMPAIGN TAPE
- CAMPAIGN_TAPE v1 is the complete batch history (EXPORT_BLOCK + B REPORT per batch), used for replay/migration.
EXPORT TAPE
- EXPORT_TAPE v1 is the pre-run planned batch list (EXPORT_BLOCK only), used for mega batching and later automation.



==================================================
SECTION 0.1 — REBOOT KIT (HARD, HUMAN-RUN)
==================================================

TWO-DOC WORKFLOW (HARD)
- To reboot a dead / bloated Project, you only need:
  (1) MEGABOOT_RATCHET_SUITE v7.4.8-PROJECTS (this file; static)
  (2) PROJECT_SAVE_DOC v1 (dynamic; prefer FULL+)

CANON RESTORE vs COMPLETE SAVE (HARD)
- CANON RESTORE (minimum required to restore Thread B canon):
  * Paste THREAD_S_SAVE_SNAPSHOT v2 into THREAD_B (see MSG-003 in BOOTPACK_THREAD_B).
- COMPLETE SAVE (minimum required to regenerate compiled docs deterministically):
  * PROJECT_SAVE_DOC v1 that contains:
    - THREAD_S_SAVE_SNAPSHOT v2
    - REPORT_POLICY_STATE (from Thread B at seal time)
    - REPORT_STATE (from Thread B at seal time)
    - DUMP_TERMS v1
    - DUMP_LEDGER_BODIES v1
    - DUMP_INDEX v1
    - DUMP_EVIDENCE_PENDING v1
- AUDITED SAVE (recommended for determinism):
  * COMPLETE SAVE + a passing Thread S audit:
    INTENT: AUDIT_PROJECT_SAVE_DOC
    OUTPUT: AUDIT_PROJECT_SAVE_DOC_REPORT v1

REBOOT PROCEDURE (S-FIRST; deterministic; HARD)
1) Boot threads per BOOT ORDER.
2) In THREAD_S, paste the PROJECT_SAVE_DOC v1 you want to restore from.
3) In THREAD_S, run:
   INTENT: AUDIT_PROJECT_SAVE_DOC
4) If PASS:
   - THREAD_S will provide an atomic “COPY TO: THREAD_B_RESTORE” block containing THREAD_S_SAVE_SNAPSHOT v2.
5) Paste that THREAD_S_SAVE_SNAPSHOT v2 into THREAD_B.
6) In THREAD_B, run:
   REQUEST REPORT_STATE
   REQUEST REPORT_POLICY_STATE
7) Continue ratcheting (or seal again).

FAILSAFE (HARD)
- If audit REFUSES due to missing fuel, you can still restore canon if you have *any* valid THREAD_S_SAVE_SNAPSHOT v2.
  (You just won’t be able to deterministically regenerate all compiled docs without FULL+ fuel.)

==================================================
SECTION 0.2 — READABILITY + ROSETTA (HUMAN; NON-ENFORCEABLE)
==================================================

THREAD_B READABILITY TARGET
- Keep Thread B canon readable to mainstream mathematicians/scientists:
  * Prefer standard terms as ratcheted TERM_DEF tokens (snake_case is fine).
  * Use MATH_DEF + DEF_FIELD to define objects/structures in a proof-adjacent style.
  * Avoid importing “axes/Jung/IGT/MBTI/I-Ching” labels into Thread B canon (drift risk).

ROSETTA OVERLAY (DOES NOT RATCHET)
- Maintain a separate Rosetta mapping layer that:
  * References Thread B IDs / TERM tokens.
  * Adds human labels / metaphors / cross-domain analogies OUTSIDE Thread B.
  * Never overwrites canon; it only annotates.

MINING THREADS / BIG DOCS
- Dump large “fuel” docs into a separate noncanon workspace (Thread A or a dedicated lab thread).
- Output only tight, atomic EXPORT_BLOCK candidates to Thread B.
- Treat Rosetta mappings as OPTIONAL overlays, not canon.

==================================================
SECTION 0.3 — MINING + ROSETTA ARTIFACTS (HARD BOUNDARY; HUMAN-RUN)
==================================================

WHY THIS EXISTS (HARD)
- Thread B is the canon kernel. It must stay clean:
  - no Jung/MBTI/IGT terms
  - no “axes” labels that you may later reorder/rename
  - no private language that blocks mainstream math readability
- But you still need a place to:
  - ingest “fuel” docs (big, messy, high-level)
  - build and maintain label overlays (“rosetta”)
  - generate engineering artifacts that *compile down* to the kernel

SOLUTION (HARD)
- Create an OPTIONAL noncanon lab thread: THREAD_M (Mining/Rosetta Lab).
- THREAD_M never writes canon. Only Thread B commits canon.
- THREAD_M’s job is to turn messy fuel into *two lanes* of artifacts:
  (1) KERNEL LANE (ratchet-safe): candidate TERM/MATH objects expressed in Thread B-safe tokens.
  (2) OVERLAY LANE (labels): Jung/IGT/engineering labels that point to kernel anchors.

HARD BOUNDARY RULE (HARD)
- Nothing from THREAD_M enters Thread B unless it is:
  - an EXPORT_BLOCK v1 draft that obeys Thread B’s fences, OR
  - raw fuel transformed into such a draft.
- “Rosetta” labels NEVER appear inside Thread B canon exports.

RECOMMENDED ARTIFACTS (NONCANON; DETERMINISTIC)
- FUEL_DIGEST v1
  - purpose: compress large external docs into a rebootable, line-cited digest
- ROSETTA_MAP v1
  - purpose: overlay labels anchored to kernel IDs/TERMs (non-authoritative)
- EXPORT_CANDIDATE_PACK v1
  - purpose: sanitized EXPORT_BLOCK drafts *ready* to paste into Thread B

MINIMAL FORMAT: ROSETTA_MAP v1 (STRUCTURAL; NON-AUTHORITATIVE)
- ROSETTA_MAP is NOT allowed to justify canon.
- ROSETTA_MAP may only annotate/label already-existing canon (or propose a candidate).
```text
BEGIN ROSETTA_MAP v1
PROJECT_ID: <string>
DATE_UTC: 2026-01-29T05:33:46Z
KERNEL_BASELINE: <string>   # e.g., ruleset_sha256 or project save doc id
LABEL_LAYERS:
- <string>                  # e.g., IGT, ENGINEERING, HUMAN_READABILITY
MAPPINGS:
- MAP_ID: <string>
  KERNEL_ANCHOR: <TERM or ID or UNKNOWN>
  OVERLAY_LABEL: <string>
  LAYER: <one of LABEL_LAYERS>
  STATUS: PROVISIONAL|STABLE|REVOKED
  INVARIANTS:
  - <string>                # “must stay true” constraints referenced from kernel items
  SOURCE_POINTERS:
  - <string>                # file + line range or “provided text”
END ROSETTA_MAP v1
```

MINIMAL FORMAT: FUEL_DIGEST v1 (STRUCTURAL)
```text
BEGIN FUEL_DIGEST v1
PROJECT_ID: <string>
DATE_UTC: 2026-01-29T05:33:46Z
SOURCES:
- SOURCE_ID: <string>
  SOURCE_POINTER: <string>  # file + line range or external pointer
EXTRACTS:
- EXTRACT_ID: <string>
  SUMMARY: <string>         # short, literal
  KERNEL_SUGGESTIONS:
  - <string>                # candidate TERM names, MATH_DEF names, PROBE themes
  ROSETTA_SUGGESTIONS:
  - <string>                # overlay labels / engineering handles
  SOURCE_POINTERS:
  - <string>
END FUEL_DIGEST v1
```

MINIMAL FORMAT: EXPORT_CANDIDATE_PACK v1 (STRUCTURAL)
```text
BEGIN EXPORT_CANDIDATE_PACK v1
PROJECT_ID: <string>
DATE_UTC: 2026-01-29T05:33:46Z
CANDIDATES:
- CANDIDATE_ID: <string>
  INTENT: PASTE_TO_THREAD_B
  EXPORT_BLOCK_DRAFT: <verbatim block, Thread B-safe tokens only>
  NOTES: <string>           # outside Thread B; explains origin + mapping
  SOURCE_POINTERS:
  - <string>
END EXPORT_CANDIDATE_PACK v1
```


==================================================
==================================================
SECTION 0.4 — FOUNDATION ROADMAP (HUMAN; NON-ENFORCEABLE)
==================================================

PURPOSE
- This is a direction-setting roadmap for what to *feed* into Thread B over time.
- It does not change kernel rules. It is safe to edit without touching Thread B.
- Goal: build a proof-like foundation that assumes as little as possible while staying readable to mathematicians.

PRINCIPLES (HUMAN)
1) Least-assumption ordering
   - Prefer structures that do not require coordinates, metrics, or classical “time” language early.
   - Use the derived-only fence as a feature: if a term trips the fence, ratchet it explicitly instead of smuggling it in.

2) Branch-parallel foundations (recommended)
   - Run multiple branches with different feed orders.
   - Promote only structures that recur across branches (avoid “ordering artifacts”).

3) Geometry can come early — but as topology-first
   - Start with adjacency / boundary / connectivity style primitives before metric and coordinate commitments.
   - Let metric-like notions be admitted later as derived structure.

4) No axis labels inside Thread B canon
   - Axis/engine label overlays belong in Thread M (or other noncanon threads).
   - Thread B should store the underlying math/structure with neutral identifiers.

TRACKS (SUGGESTED)
TRACK_G (least-assumption geometry/topology-first)
- Phase G1 — Operators + grammar scaffolding
  * Ratchet math glyph operators explicitly (e.g. equals_sign, digit_sign, etc).
  * Ratchet formula grammar ladder objects (tokenization → parsing → wellformedness) as terms/MATH_DEF.
- Phase G2 — Proto-structure
  * Build minimal relation/composition language (without coordinates).
  * Candidate topics: adjacency, path, cycle, boundary, equivalence, partial order.
- Phase G3 — Topology
  * Candidate topics: continuity as constraint, homotopy-like invariants, gluing/composition, fiber/bundle primitives.
- Phase G4 — Geometry (coordinate-free)
  * Candidate topics: metric/connection/curvature admitted *only when required*, and only via explicit ratchet.

TRACK_Q (pragmatic QIT-first)
- Phase Q1 — Operators + grammar scaffolding (same as G1)
- Phase Q2 — QIT primitives as working substrate
  * Use density_matrix / channel / measurement / entropy terms as working objects.
  * Keep the “emergence” claim separate: this track is for building machinery + testing operators.
- Phase Q3 — Reconcile with TRACK_G
  * Attempt to re-derive QIT objects from the topology/algebra built in TRACK_G.

TRACK_A (optional; algebra-first)
- Phase A1 — Semigroup/group/ring-like candidates (all explicit)
- Phase A2 — Linear structures (vector_space / inner_product) admitted explicitly
- Phase A3 — Link to geometry + QIT representations

AXIS MATH + ORTHOGONALITY (WHEN READY)
TOPOLOGY4 INTRO CHECKPOINT (HUMAN; NON-ENFORCEABLE)
- When to bring the “Topology4” content forward:
  1) After QIT core carriers + operator/grammar scaffolding have stabilized (few/no SCHEMA_FAILs).
  2) After the variance-class split (deductive vs inductive) is at least TERM_PERMITTED in Thread B.
  3) Then admit the Topology4 base-class MATH_DEF and TERM_DEF items (eulerian, lagrangian, open_system, closed_system, unitary, cptp_channel) as neutral math.
  4) Immediately pair with SIM evidence (Topology4 channel family + Terrain8 bridging) so meanings stay anchored.
- Keep “axis labels” + Jung/IGT tokens out of Thread B while doing this; keep them in Thread M overlays.

STAGE8 NOTE (HUMAN; NON-ENFORCEABLE)
- Optional planning shorthand: Stage8 = (Topology4 bases) × (AXIS-3 engine-family split).
- Treat as planning-only until independently supported by evidence gates.

- Treat “axes” as abstract orthogonal decompositions, not as labeled psychological constructs.
- Candidate topics: orthogonality, projection, decomposition lattices, invariant subspaces.
- Later, Thread M can overlay your axis labels onto these neutral structures.

ANTI-PITFALL NOTE (HUMAN)
- If the system “jumps” straight to advanced objects (e.g., Hopf fibrations / higher topology objects),
  treat that as a hypothesis, not a foundation.
- Use TRACK_G to force more intermediate topology/geometry scaffolding so later emergence is explainable.

==================================================
SECTION 0.5 — MIGRATION + GRAVEYARD (HARD BOUNDARY; HUMAN-RUN)
==================================================

DEFINITIONS (HARD)
REFRESH
- New Project, SAME megaboot + SAME bootpacks.
- Use: reboot when context is too big, or threads drift, with no version change.

UPGRADE
- New Project, NEW megaboot, but Thread B bootpack unchanged.
- Safe to restore from PROJECT_SAVE_DOC because kernel law is unchanged.

MIGRATION
- New Project, NEW megaboot, and Thread B bootpack changed.
- Do NOT load old Thread B snapshots into the new kernel.
- Instead: replay prior work through the new kernel using a Campaign Tape.

CAMPAIGN_TAPE v1 (HARD; OWNED BY THREAD_S)
- A Campaign Tape is the complete batch history needed to replay or migrate:
  (EXPORT_BLOCK vN + Thread B REPORT) for each batch, in order.
- This is the “massive text file of all the batches” needed for deterministic rebuilds.

BATCH_GRAVEYARD_DISCIPLINE (HARD)
After every batch (PASS or FAIL):
1) Append the exact EXPORT_BLOCK and the exact Thread B REPORT to CAMPAIGN_TAPE.
2) Build structural graveyard views in Thread S (no inference):
   - REJECT_HISTOGRAM (by TAG / OFFENDER_RULE)
   - OFFENDER_LINE_REPORT (verbatim lines that failed)
   - DERIVED_ONLY_HIT_REPORT (if any derived-only literals triggered)
3) Only then proceed to the next batch draft.

WHY THIS EXISTS (HUMAN)
- A save snapshot restores state, but a Campaign Tape enables:
  - migration across kernel-law changes
  - full graveyard reconstruction
  - deterministic replay debugging when something “should have worked”

==================================================
SECTION 0.6 — MASSIVE BATCHING + EXPORT_TAPE (HARD GUIDANCE; HUMAN-RUN)
==================================================

WHY THIS EXISTS (HARD)
- Thread B enforces a single-container rule (see MSG-001 in BOOTPACK_THREAD_B).
- That does NOT prevent large ingestion: one EXPORT_BLOCK can contain many SPEC lines.
- But for determinism + debugging + migration, you need:
  (1) a chunking discipline (what counts as a “batch”)
  (2) a recording discipline (EXPORT_TAPE and/or CAMPAIGN_TAPE)
  (3) a sealing discipline (PROJECT_SAVE_DOC v1 FULL+)

SINGLE-CONTAINER CONSTRAINT (HARD)
- Thread B will REJECT any message that contains more than one top-level container.
Therefore:
- You may not paste multiple EXPORT_BLOCKs in one message to Thread B.
- You may paste one EXPORT_BLOCK that contains many SPEC lines (subject to UI/file size limits).

MASSIVE BATCHING OPTIONS (HARD)
OPTION A — ONE HUGE EXPORT_BLOCK (manual speed)
- Pros: fastest when you are hand-feeding.
- Cons: harder forensic debugging; higher risk of truncation; more parks due to pressure.
- Discipline:
  * Keep internal topic grouping (operators → topology → geometry → engines).
  * Insert periodic PROBE_HYP “anchors” so the batch has visible checkpoints.

OPTION B — EXPORT_TAPE → SEQUENTIAL FEED (recommended for automation)
- EXPORT_TAPE v1 is a pre-run ordered list of EXPORT_BLOCKs (no Thread B reports).
- It is owned/compiled by Thread S (structural-only; no inference).
- A future feeder/automation can read EXPORT_TAPE and post each embedded EXPORT_BLOCK to Thread B as a separate message.

OPTION C — CAMPAIGN_TAPE (post-run replay/migration)
- CAMPAIGN_TAPE v1 is the post-run record: (EXPORT_BLOCK + THREAD_B_REPORT) per batch, in order.
- Always append after each batch (PASS or FAIL).
- This is the “massive text file of all the batches” required for deterministic rebuilds and migration.

SAFE SIZE GUIDANCE (HUMAN; NON-ENFORCEABLE)
- Early stabilization: ~25–100 SPEC lines per EXPORT_BLOCK.
- Seed libraries: ~200–500 SPEC lines per EXPORT_BLOCK (usually still reviewable).
- Above that: assume you must rely on CAMPAIGN_TAPE + Thread S graveyard reports rather than memory.

EXPORT_TAPE v1 (NEW)
- Use when you want a single downloadable doc containing *all planned batches* before running them.
- After running, promote to CAMPAIGN_TAPE by appending each block together with its Thread B report.



==================================================
SECTION 0.7 — HUGE BOOT DEBUG + REDUNDANCY (HARD GUIDANCE; HUMAN-RUN)
==================================================

GOAL (HARD)
- Keep Thread B pure (no partial acceptance, no “ignore errors”), while making mega-batch failures debuggable and replayable.

HARD RULE: RECORD BEFORE REPAIR
- If a batch fails, do not “tweak and re-run” blindly.
- First: record it (CAMPAIGN_TAPE), then isolate the offender, then patch with a NEW EXPORT_ID.

FAILURE ISOLATION PROTOCOL v1 (HARD)
When Thread B responds with REJECT_BLOCK (or any FAIL-like RESULT):
1) RECORD (always)
   - Append exact (EXPORT_BLOCK + THREAD_B_REPORT) to CAMPAIGN_TAPE (Thread S).
2) FORENSICS (structural only)
   - Run Thread S:
     * BUILD_OFFENDER_LINE_REPORT
     * BUILD_REJECT_HISTOGRAM
     * BUILD_DERIVED_ONLY_HIT_REPORT
3) PATCH (no deletion)
   - Create a new EXPORT_BLOCK with a new EXPORT_ID.
   - Move offending lines into your living graveyard (PARK/REJECT-driven queues), do not erase them.
4) RETRY
   - Re-run only the patched EXPORT_BLOCK.

BINARY-SEARCH SPLIT (HUMAN; OPTIONAL; last resort)
- If no clear offender emerges:
  - Split the failing EXPORT_BLOCK into smaller blocks (by SPEC lines).
  - Feed them in a fresh branch (or a fresh Project if you require strict no-side-effect debugging).
  - Record each attempt into CAMPAIGN_TAPE.

EXPORT_BLOCK PREFLIGHT (RECOMMENDED FOR HUGE BLOCKS)
- Before feeding a large EXPORT_BLOCK (e.g. >200 SPEC lines):
  - Run Thread S INTENT: BUILD_EXPORT_BLOCK_LINT_REPORT
  - Paste: latest THREAD_S_SAVE_SNAPSHOT v2 + the candidate EXPORT_BLOCK
- Treat LINT findings as “must resolve or intentionally graveyard” before Thread B.

REDUNDANCY / RE-FEED DISCIPLINE (HARD)
- Never rely on memory for “did we already feed this?”
- Use Thread S INTENT: BUILD_TAPE_SUMMARY_REPORT on EXPORT_TAPE / CAMPAIGN_TAPE to:
  - list ENTRY_INDEX → EXPORT_ID → RESULT
  - detect duplicates
  - choose a replay cursor deterministically
- If you must re-feed a previously accepted batch:
  - prefer a NEW Project replay from CAMPAIGN_TAPE (clean determinism),
  - or mark BRANCH_ID="REPLAY" and keep the duplicate in tape history.



==================================================
==================================================
SECTION 0.8 — AXIS SEMANTICS CLARIFICATION (NONCANON, HUMAN MAP)
==================================================

CORE POINT (HARD FOR HUMAN PRACTICE)
- Thread B remains QIT+math first.
- Axes 0–6 are functions/slices on the constraint manifold; they are not primitives.
- Overlay labels (Jung / IGT / MBTI) stay outside Thread B canon unless explicitly promoted later.

AXIS-1 × AXIS-2 (TOPOLOGY4 IS NOT “GRAPH EDGES”)
- AXIS-1 = bath coupling regime (isothermal ↔ adiabatic analog).
- AXIS-2 = boundary / representation regime (Eulerian ↔ Lagrangian; open ↔ closed boundary).
- AXIS-1 × AXIS-2 yields 4 base regimes (“Topology4”): four orthogonal base classes.
  * Graph edges come later as adjacency/transition structure BETWEEN these bases.
  * The axis product is the base-class split itself, not the edges.

AXIS-3 (ENGINE-FAMILY SPLIT: TYPE-1 VS TYPE-2)
- AXIS-3 selects the Type-1 vs Type-2 engine family.
- AXIS-3 is not a chirality/handedness/spinor/Berry/flux tag.
- Terrain8 is Topology4 × (AXIS-3 family) as a bookkeeping cross-product, not a geometry primitive.

AXIS-4 (VARIANCE-ORDER: TWO MATH CLASSES; NOT “LOOP ORDER”)
- AXIS-4 is the math-class split: DEDUCTIVE vs INDUCTIVE variance-order.
- The familiar “loop order” sequences (SEQ01–SEQ04, FWD/REV) are derived probes of:
  (AXIS-4 variance-order) × (Topology4) × (AXIS-6 precedence).

AXIS-6 (PRECEDENCE / COMPOSITION ORDER)
- AXIS-6 is precedence (UP/DOWN) on composition (AB ≠ BA pressure).
- Do not conflate with AXIS-4:
  * AXIS-4 = variance-order regime
  * AXIS-6 = operator precedence within a regime

ORTHOGONALITY GUARDRAILS (HARD)
- AXIS-4 ≠ AXIS-6 (variance class vs precedence).
- AXIS-1×AXIS-2 define base topology families; adjacency edges are additional structure.
- AXIS-3 is the engine-family split; do not bind it to any legacy substrate.

SECTION 1 — PROJECT INSTRUCTIONS (HARD, HUMAN-RUN)
==================================================

PROJECT_PINNING_RULE (HARD)
- Any change to any bootpack (A/B/S/SIM) ⇒ NEW megaboot + NEW Project.
- Never patch in place inside an existing Project.

PROJECT_CREATE_STEPS
1) Create NEW Project named:
   LEV_RATCHET — v7.4.8-PROJECTS
2) Create four threads:
   - THREAD_A
   - THREAD_S
   - THREAD_B
   - THREAD_SIM


CANDIDATE CANON BUILD ORDER (NONCANON; ROADMAP)
- You suggested the *ratchet order* should be independent of axis labels and likely:
  0 → 6 → 5 → 3 → 4 → (1×2)
- Interpreted in “pure math / QIT” terms (no axis labels needed in Thread B):
  * (0) correlation / entropy monotones (operational information measures)
  * (6) precedence / noncommutation pressure (AB ≠ BA as admissible evidence)
  * (5) generator regime split (spectral vs gradient / stable vs exploratory operator families)
  * (3) engine-family split (Type-1 vs Type-2)
  * (4) variance-order split (deductive vs inductive class; variance trajectory)
  * (1×2) Topology4 base classes (channel-admissibility × chart-lens) → 4 orthogonal terrain classes
- This is a *roadmap*, not a commitment: the graveyard can resurrect a different order later.


==================================================
SECTION 1.1 — BOOT ORDER (PASTE SEQUENCE)
==================================================

BOOT ORDER (HARD)
1) THREAD_A   — Orchestrator (human-run). Emits atomic copy/paste instructions.
2) THREAD_S   — Compiler. Needed early to validate fuel shape and produce save docs.
3) THREAD_B   — Canon kernel.
4) THREAD_SIM — Evidence wrapper.

HARD NOTE
- Thread B cannot boot other threads. Only the human can paste boot texts.
- “A boots all threads” means: A outputs copy/paste boxes; the human executes them.

==================================================
SECTION 1.2 — BOOT VERIFY (SYNC SMOKE TEST)
==================================================

BOOT VERIFY MACRO v1 (HARD)
COPY TO: THREAD_B
```text
REQUEST REPORT_STATE
```

OPTIONAL L0 SMOKE PROBE (RECOMMENDED IF YOU SUSPECT A TRUNCATED / MISMATCHED BOOTPACK)
- Purpose: detect “undefined term use” failures caused by missing L0_LEXEME_SET or wrong kernel boot.
- EMIT_MODE: REPORT_ONLY ensures no state changes if accepted.

COPY TO: THREAD_B
```text
BEGIN EXPORT_BLOCK v1
EXPORT_ID: SMOKE_L0_LEXEME_PROBE
TARGET: THREAD_B_ENFORCEMENT_KERNEL
PROPOSAL_TYPE: SMOKE_TEST

CONTENT:
PROBE_HYP P_L0_SMOKE
PROBE_KIND P_L0_SMOKE CORR PROBE
WITNESS P_L0_SMOKE CORR finite
WITNESS P_L0_SMOKE CORR dimensional
END EXPORT_BLOCK v1
```

EXPECTED (HARD)
- If you see TAG: UNDEFINED_TERM_USE for "finite" or "dimensional": STOP. Your boot is not the expected kernel.


COPY TO: THREAD_S
```text
INTENT: BUILD_COMMAND_CARD_SELF_CHECK
```

COPY TO: THREAD_SIM
```text
INTENT: BUILD_SIM_COMMAND_CARD_SELF_CHECK
```

IF ANY FAILS (HARD)
- Do NOT proceed to sealing.
- Fix by discarding the Project and rebooting from last PASS save doc.

==================================================
SECTION 2 — HOW THE SYSTEM RUNS (CAMPAIGN LOOP)
==================================================

IMPORTANT
- There is no single fixed 'runtime order'.
- The system runs as a human-managed loop with checkpoints.
- 'Sync' here just means: producing and verifying consistent artifacts across threads.

CAMPAIGN LOOP (HARD, HUMAN-RUN)
Loop A — Canon advance (THREAD_B)
- Feed batches (EXPORT_BLOCKs) into B.
- B accepts/rejects; canon state advances only on PASS.

Loop A2 — Graveyard discipline (THREAD_S)
- After every batch (PASS or FAIL):
  * Append (EXPORT_BLOCK + B REPORT) into CAMPAIGN_TAPE v1 (Thread S).
  * Update structural graveyard views (REJECT_HISTOGRAM, OFFENDER_LINE_REPORT, etc).

Loop B — Checkpoint / Seal (THREAD_S)
- At any checkpoint, B emits seal fuel:
  * REPORT_POLICY_STATE
  * REPORT_STATE (recommended for FULL+)
  * SAVE_SNAPSHOT (THREAD_S_SAVE_SNAPSHOT v2)
  * DUMP_TERMS (enumerated)
  * DUMP_LEDGER (full bodies)
  * DUMP_INDEX (recommended for FULL+)
  * DUMP_EVIDENCE_PENDING (recommended for FULL+)
- S compiles a save doc (MIN or FULL+).

Loop C — Audit / Decision (THREAD_S + optional THREAD_A)
- Thread S audits the save doc structurally (PASS/FAIL).
- If PASS: human declares checkpoint (MIN) or ratchet step (FULL+).
- If FAIL: rerun missing B dumps / reseal; Thread A may help debug (noncanon).

Loop D — Evidence (THREAD_SIM, optional)
- SIM can emit evidence packs (hash attestations) at checkpoints.
- Thread S audits SIM evidence formatting (hash format only). Thread A review is optional.
- Valid SIM evidence may be embedded into the save doc; invalid evidence is ignored.

REPAIR LOOP (HARD)
- If S refuses due to missing/placeholder fuel: re-run the missing B dump(s), then re-seal.
- If B emits headers-only or placeholders during FULL+ sealing: discard Project; reboot from last PASS FULL+ save.

==================================================
SECTION 3 — RESTORE PHASE (AFTER BOOT)
==================================================

RESTORE RULE (HARD)
- The only artifact that must be loaded into Thread B to restore canon is:
  THREAD_S_SAVE_SNAPSHOT v2

RESTORE_FROM_PROJECT_SAVE_DOC (HARD, RECOMMENDED)
1) Paste PROJECT_SAVE_DOC v1 into THREAD_S.
2) THREAD_S audit:
```text
INTENT: AUDIT_PROJECT_SAVE_DOC
```
3) If PASS: extract the embedded THREAD_S_SAVE_SNAPSHOT v2 and paste it (verbatim, as its own message) into THREAD_B.
4) Optional: paste the same PROJECT_SAVE_DOC into THREAD_A for TEACH/orchestration (noncanon).

SECTION 4 — SAVE LEVELS (MIN vs FULL+)
==================================================

PROJECT_SAVE_DOC v1 — MIN (REBOOTABLE CHECKPOINT)
Required contents:
- Bootpacks (A/B/S/SIM) verbatim
- Project runbook (boot order + restore + basic seal steps)
- THREAD_S_SAVE_SNAPSHOT v2 (to restore B)

Allowed (typical):
- REPORT_POLICY_STATE optional
- DUMP_TERMS and/or DUMP_LEDGER_BODIES may be omitted if the snapshot is fully enumerated
  (TERM_REGISTRY + full SURVIVOR_LEDGER bodies).

PROJECT_SAVE_DOC v1 — FULL+ (RATCHET STEP; DETERMINISTIC + MIGRATION-FRIENDLY)
Required contents:
- Everything in MIN
- REPORT_POLICY_STATE (provenance / policy flags)
- REPORT_STATE (regression check at seal time)
- DUMP_TERMS v1 (fully enumerated; no placeholders) OR equivalently enumerated TERM_REGISTRY in snapshot
- DUMP_LEDGER_BODIES v1 (full bodies; no headers-only) OR equivalently full bodies in snapshot
- DUMP_INDEX v1 (index cross-check; structural)
- DUMP_EVIDENCE_PENDING v1 (evidence cross-check; structural)
- Audit-at-seal-time block

NOTE (HARD)
- If any “equivalently enumerated in snapshot” claim fails audit, the save is FAIL.

RULE (HARD)
- Only FULL+ can advance the ratchet (become the “last PASS”).
- MIN is allowed as an interim checkpoint.

SECTION 5 — SEALING (CHECKPOINTS)
==================================================

THREAD_B SEAL FUEL (choose one; paste each request as its own message to THREAD_B)

MIN fuel (fast checkpoint)
```text
REQUEST REPORT_POLICY_STATE
```
```text
REQUEST SAVE_SNAPSHOT
```

FULL+ fuel (ratchet step / audit-complete; migration-friendly)
```text
REQUEST REPORT_POLICY_STATE
```
```text
REQUEST REPORT_STATE
```
```text
REQUEST SAVE_SNAPSHOT
```
```text
REQUEST DUMP_TERMS
```
```text
REQUEST DUMP_LEDGER
```
```text
REQUEST DUMP_INDEX
```
```text
REQUEST DUMP_EVIDENCE_PENDING
```

THREAD_S BUILD (both MIN and FULL+ use the same intent)
Copy the emitted fuel artifacts from THREAD_B into THREAD_S (same paste), then run:
```text
INTENT: BUILD_PROJECT_SAVE_DOC
PROJECT_SAVE_ID: <e.g. CKPT_v0001 or RAT_v0001>
```

THREAD_S AUDIT (structural; recommended every seal)
Paste the produced PROJECT_SAVE_DOC v1 back into THREAD_S (same paste), then run:
```text
INTENT: AUDIT_PROJECT_SAVE_DOC
```

THREAD_A REVIEW (optional; noncanon)
- Thread A may read the audit report and decide whether to treat the checkpoint as MIN vs FULL+.
- Thread A never replaces Thread S structural audit.

SECTION 6 — OLD / BROKEN SAVE UPGRADE (HARD)
==================================================

UPGRADE PIPELINE
1) Boot all threads (A→S→B→SIM).
2) Paste old/broken save into THREAD_S and run:
```text
INTENT: AUDIT_PROJECT_SAVE_DOC
```
3) If an embedded THREAD_S_SAVE_SNAPSHOT v2 exists: paste it into THREAD_B to restore.
   - SAFE ONLY if Thread B bootpack is unchanged; otherwise treat as MIGRATION (see SECTION 0.5).
4) In THREAD_B emit FULL+ seal fuel:
   - REQUEST REPORT_POLICY_STATE
   - REQUEST REPORT_STATE
   - REQUEST SAVE_SNAPSHOT
   - REQUEST DUMP_TERMS
   - REQUEST DUMP_LEDGER
   - REQUEST DUMP_INDEX
   - REQUEST DUMP_EVIDENCE_PENDING
5) THREAD_S: BUILD_PROJECT_SAVE_DOC (new PROJECT_SAVE_ID).
6) THREAD_S: AUDIT_PROJECT_SAVE_DOC.
PASS becomes the new ratchet step (FULL+).

FAIL-HARD
- If B emits placeholders or headers-only dumps during FULL+ fuel:
  discard Project; reboot from last PASS FULL+ checkpoint.

SECTION 7 — UNDERSCORE AND EQUALS POLICY (HARD)
==================================================

UNDERSCORE POLICY (HARD)
- '_' is structural joiner for compound/sentence terms.
- '_' carries no semantics and is not evidence-gated.
- Compound legality is validated by segment admissibility.

EQUALS POLICY (HARD)
- '=' is semantic and heavily gated.
- '=' allowed only inside FORMULA strings.
- '=' requires equals_sign CANONICAL_ALLOWED.
- Kernel assumes no equality semantics (no Platonic/Cartesian assumptions).

==================================================
SECTION 8 — FULL_SYSTEM_BOOT_SYNC_TEST v1
==================================================

1) Boot all threads (A→S→B→SIM).
2) Run BOOT VERIFY MACRO.
3) In B:
```text
REQUEST DUMP_TERMS
```
```text
REQUEST DUMP_LEDGER
```
Expect full enumeration + full bodies.
4) Seal FULL+ in THREAD_S (BUILD_PROJECT_SAVE_DOC) and audit it in THREAD_S (AUDIT_PROJECT_SAVE_DOC).
5) Optional: attach SIM_EVIDENCE_PACK; re-run THREAD_S audit. Thread A review is optional.

==================================================
SECTION 9 — BOOTPACKS (EXTERNAL FILES)
==================================================

BOOTPACK FILE PATHS (this bundle)
- BOOTPACKS/BOOTPACK_THREAD_A_v2.60.md
- BOOTPACKS/BOOTPACK_THREAD_S_v1.64.md
- BOOTPACKS/BOOTPACK_THREAD_B_v3.9.13.md
- BOOTPACKS/BOOTPACK_THREAD_SIM_v2.10.md
- BOOTPACKS/BOOTPACK_THREAD_M_v1.0.md (optional)

AUTHORITY NOTE (HARD)
- BOOTPACK_THREAD_B_v3.9.13.md is the SOLE_SOURCE_OF_TRUTH for Thread B kernel enforcement.
- This MEGABOOT defines bundle workflow and references bootpack texts; it does not override kernel enforcement.
