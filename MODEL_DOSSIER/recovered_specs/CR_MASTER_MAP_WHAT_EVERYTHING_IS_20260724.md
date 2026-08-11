# Codex-Ratchet master map — what I think everything is

**Date:** 2026-07-24
**Author:** Claude (Fable 5), session `session/r0-three-engine-probes` at `6ccd79bdf`
**What this is:** my full current understanding of the estate — the foundation, the ratchet, the manifold, the axes, the QIT engines, IGT, the sim engines, ClaimGate, LevOS, and the new material. One map, in one place.
**What this is not:** canon. Every claim below carries one of four authority tags. Where two readings are live I hold both and say so. Where a claim is mine and not yours, I mark it.

**Authority tags used throughout:**

| Tag | Meaning |
|---|---|
| `OWNER-LOCK` | you stated it directly and have not superseded it |
| `OWNER-TENTATIVE` | you stated it with an explicit "could be wrong" |
| `CANDIDATE` | proposed (by Gemini, by me, or by a repo doc); named, not settled |
| `MY-READING` | my synthesis; you have not confirmed it |

Status ladder for implementation claims: `exists < runs < passes local rerun < canonical by process`. I never promote up that ladder in this document.

---

## Part I — The foundation

### I.1 The root axiom

`a = a iff a ~ b` — `OWNER-LOCK`.

Identity is not primitive. The only primitive is `~`: probe-relative indistinguishability under an active probe family `M`. A thing is itself only insofar as some probe family fails to distinguish it from something. Identity is earned from indistinguishability, never assumed.

This is the nominalist root. It is also, in your P-vs-NP direction, the same move as Myhill–Nerode: states of an automaton ARE equivalence classes under distinguishing experiments. One axiom, two literatures.

### I.2 The no-primitive family

`OWNER-LOCK` as a family; the exact registry membership is open (AR01 decision OD-02).

Nothing on this list may be smuggled in as free structure. Every one of these, if used, is an installed presumption that must be declared and can be charged against a candidate:

- no primitive identity, no primitive equality
- no primitive causality, no primitive time
- no primitive metric, no Cartesian origin, no privileged frame
- no primitive probability
- finitism — no completed infinities (F01)
- ordered foundations (N01)
- no Platonic dualism, no observer privilege
- no narrative-first inference, no free explanation
- no primitive global optimizer or evaluator

`MY-READING`: the deepest recurring failure mode of every LLM that touches this system — including me — is silently reinstalling one of these (usually identity, time, or metric) inside a formalization and then calling the result "the model." The AR01 audit's central finding is exactly this, and it is correct.

### I.3 The presumption floor

`OWNER-LOCK`. Axioms are GIVEN, not provable and not testable: `a = a iff a ~ b`, F01 finitism, N01 ordered foundations, and (likely) nonassociativity in the eventual algebra. It is a category error to "test" these; anything that contradicts them is simply wrong output.

Presumption is graded by containment (the Venn rule): classical mathematics is MORE presumptive than QIT, vector structure MORE presumptive than spinor structure, by definition — the containing theory presumes everything the contained one does plus more. Naturals are the most presumptive familiar object; the complex field is among the least. The ratchet prefers the least-presumptive structure that still survives.

The order among finitude / noncommutativity / nonassociativity / anticommutativity / sedenion-level structure is OPEN — `OWNER-LOCK` on the openness itself. Do not hard-code an order. G2/F4 are eventual targets, not current carriers.

### I.4 Language discipline

`OWNER-LOCK` (harness preamble). Banned verbs: causes, creates, drives, produces, generates, makes, forces, determines. Preferred: survived, admitted, excluded, indistinguishable, coupled with, co-varies under, UNSAT under, consistent with, pulled back. Every substantive claim needs three supports: a probe family M, admissibility status under active constraints C, and the quotient `S/~_M`. Missing any one demotes the claim to provisional.

---

## Part II — The Ratchet

### II.1 What the ratchet is

`OWNER-LOCK`. MSS = Minimal Evolving Persistent Structure. MSS = ratchet = tower = nesting = replicator — one thing, different names. The ratchet is NESTED: each rung runs ON the rung below. Density matrices come early; Shannon and the later entropies are licensed late.

The ratchet is deterministic and comparison-based. LLMs may propose candidates; they may never settle MSS or the root constraints. The partition kernel computes; no model's word substitutes for the computation.

### II.2 What MSS is NOT

`OWNER-LOCK`, sharpened by AR01 (blocker 2, decision OD-04, and I concur): MSS is NOT generic Pareto sorting. A non-dominated survivor on some packet-relative partial order is not automatically MSS. MSS is the weakest-minimal-presumption admission rule for structures that are persistent and evolvable — still-killable, compositional, charged for every presumption they carry. Pareto settlement is at most a downstream reporting mechanism. Conflating the two lets a familiar strong carrier survive merely by being "not dominated," which is exactly the LLM familiar-math attractor.

Also `OWNER-LOCK`: MSS is coarseness-only, with D-thickening; MSS is a GATE, not a driver (the K-pack correction).

### II.3 The comparison unit and the ratchet's motion

`OWNER-LOCK` (the 07-21 corrections):

- **DON'T ratchet the ratchet.** The axioms are fixed. The ratchet improves its inventory of structures, never its own root comparator.
- **The comparison unit is the NESTED CHAIN** — a thing together with its next layer, compared against another chain. Flat single-layer comparison is invalid.
- **No maximality claims, ever.** The ratchet never declares a best. It seeks rivals-that-also-nest.
- **Chain EXTENSION is valid ratchet progress with no comparison at all.** Making nested things, then comparing, with longer chains over time, is the whole motion.
- **Branching frontier, Purgatory, re-merge.** Candidates that fail are not deleted; they park in Purgatory with witnesses and can re-enter when the frontier moves. Purgatory is the working space, not a graveyard.

### II.4 The generative-order fork (held open)

Two live readings on where MSS sits relative to probes and equivalence — AR01 decision OD-03, and I confirm the fork is real in your own statements:

- **A:** probes → `~` → quotient → MSS applied to surviving carriers.
- **B:** MSS admissibility first → it constrains which probes/distinctions are allowed → `~`.
- **C:** mutually constraining fixed point — a co-ratchet with no one-way first step.

`MY-READING`: C is most consistent with your "layers are SIMULTANEOUS" and "later-compatible organization feeds back" doctrine, but you have said things supporting B (MSS prior to operational equivalence). I hold all three. No one may call any of them forced.

### II.5 What a ratchet needs to move

`OWNER-LOCK` (binding state item 1): a ratchet cannot move without a gradient. The gradient is Axis 0, at the BEGINNING, innate — the drive. This is Part III's subject, and it is the single most-corrected item in the estate's history.

---

## Part III — The manifold

### III.1 The name and the dual

`OWNER-LOCK`. The system's name: **quantum-entropic-geometry**. The core dual (ROOT_CARD, your verbatim): operator-entropy × geometric manifold — entropy AS the surface, not entropy read off a separately existing surface. Nested on density matrices and probes; the MSS chain rides on it. "Entangled rolling dice" is a METAPHOR and must never be mechanized into a sim design.

`OWNER-LOCK` (the correction the AR01 audit independently re-found as blocker 4): geometry and entropy are ONE co-ratcheting nested construction at every depth. Any architecture that runs geometry as late lifts and entropy as telemetry, joined in a receipt, has replaced the model with two familiar tracks. Every layer must pair a geometric carrier with a typed entropy at that layer.

### III.2 Axis 0 — the two objects with one name

This is the item I got catastrophically wrong once (placing Axis 0 last in a layer ladder), so I state it with maximum care.

`OWNER-LOCK`:

1. **Axis 0, the drive:** an entropy gradient of the WHOLE manifold — at the beginning, innate, prior to any layer. It is a field-like role spanning every node of the manifold, not a rung in the ladder and not the last thing built. The ratchet moves because this gradient exists.
2. **Axis 0, the readout:** Φ₀ — needs a cut, arrives via Ξ, and is LATE. A cut-response functional evaluated on ρ_AB across a chosen cut.

Two objects, one name. Conflating them — especially demoting the drive to the position of the readout — is the canonical error.

`OWNER-TENTATIVE` (your explicit "could be wrong"): positive entropy (growth/expansion) and negative entropy (records/locks) are each their own gradients, and Axis 0 is the gradient BETWEEN them.

`OWNER-LOCK` (07-19 doctrine): entanglement is CENTRAL. Negative conditional entropy S(A|B) < 0 is a witness and fuel. Coherent information I(A⟩B) is the quantum-side candidate for the Axis-0 gradient. A product-lane-at-chance control is the supporting receipt shape.

`CANDIDATE` only: any specific formula for the Axis-0 cofield (including the set-union/telemetry tuple in the Gemini-derived pack). AR01 blocker 6 is right: typed carrier, maps, units, and a uniqueness argument have not been supplied for any specific formula. The ROLE is locked; every FORMULA is a candidate.

### III.3 The five kinds — never collapsed

`OWNER-LOCK` (the corrected architecture doc, confirmed by your Gemini thread): five different kinds of thing live in this system and must never be flattened into one "stack diagram":

1. **Strata / layers** — the nested carriers (contexts, quotients, density carriers, …).
2. **Axis 0** — the manifold-wide entropy–geometry gradient field over ALL strata.
3. **The Ratchet** — the admission process that moves ON the strata.
4. **Engine degrees of freedom** — the QIT engines' own axes (stage, loop, chirality, flux).
5. **Governance** — ClaimGate, seals, receipts, LevOS. Control plane, not physics.

Most historical drift in this repo consists of one kind being drawn inside another's diagram.

### III.4 The stratum ladder — held as candidate, in two rival presentations

The manifold's generative topology is decision OD-08 — NOT settled. What exists:

**Presentation A — the semantic spine (`MANIFOLD_CANDIDATE_A`), `CANDIDATE`:**

```text
CTX → QUOT → DENS → (PURE | MIX) → HOPF → CHIR → CUT → CORR → PROC → HIST → WHOLE
```

- CTX: finite contexts/addresses under a declared probe family
- QUOT: the quotient S/~ — operational equivalence classes
- DENS: density carriers (ρ) — early, per the nesting doctrine
- PURE/MIX: pure-state and mixed-state information geometry as rival elaborations
- HOPF: Hopf/ring structure (S³ fibration machinery, holonomy)
- CHIR: chirality/orientation
- CUT: cuts A|B — the licensing structure for Φ₀-type readouts
- CORR: correlation/entanglement structure across cuts
- PROC: processes/channels
- HIST: histories
- WHOLE: whole-manifold closure

This chain is coherent and useful as an ENGINEERING scaffold. But AR01 blocker 3 is correct and I adopt it: as written it is a one-way enrichment chain, and your model is nested-simultaneous with downward/backward constraint. The spine is a candidate presentation, not the checksum.

**Presentation B — the L0–L8 nested entropic-geometry table (your paste, 07-22), `CANDIDATE` (owner-supplied as "helper fuel," explicitly not canon):** a formal table of nine indexed levels, each row pairing a geometric object with a typed entropy, diagram indexed by (depth ℓ, cut A), Axis 0 as gradient field over all nodes. This is closer to the doctrine (entropy-geometry paired per level, field over the whole) but you supplied it as search fuel, not spec.

**Presentation C — ring-checkerboard / nested shells, `CANDIDATE`, live rival (decision OD-05):** you have described ring-checkerboard/nested shells with its entropy gradient as proposed LITERAL manifold machinery — the finite carrier itself, not a chart. The compact pack demoted it to a late HOPF feature; AR01 blocker 5 flags that demotion and I agree it was a demotion, not a derivation. Both readings (native support vs late presentation) stay live.

`MY-READING` on how to hold all three: A is a build order for software, B is the closest formal statement of the doctrine, C is a rival literal carrier. They answer different questions and none of them is the manifold. The manifold checksum does not exist yet as a single artifact; producing it requires your OD-08 answer.

### III.5 Where spinors, chirality, and global orientation enter

OPEN — decision OD-06. The repo contains spinors in at least four roles: early closure witnesses, engine chirality, 720°-memory carriers, late graded observables. The compact pack chose "late CHIR branch" unilaterally. Per your locks I keep: density-operator-only formalism (no Bloch-vector reasoning), chirality installed-not-forced (three audits), and the unrun γ₅ literal sim as a named debt. The roles are NOT one "spinor layer."

---

## Part IV — The axes

### IV.1 Axes 0–6 (the lower manifold)

- **Axis 0** — Part III.2 above. Whole-manifold entropy–geometry gradient (drive) + late cut-readout Φ₀. `OWNER-LOCK` on the role split.
- **Axes 1–3** — the three distinct polarities doctrine holds that axes 0, 3, 6 are three DIFFERENT polarities never to be collapsed (`OWNER-LOCK` on distinctness). My best current reading of 1–3: the ordered structural axes on which contexts, quotients, and carriers differentiate — but the historical repo ledgers conflict, and per AR01 blocker 7 I decline to assert a table. `OPEN`.
- **Axis 4** — qualitative DIRECTION: induction/heating versus deduction/cooling. `OWNER-SOURCE` (the corrected appendix), quantitative binding open. Whether heating/cooling is literal thermodynamics or a directional information label is your OD-16 call; the Szilard/Carnot boundary-engines doctrine ("boundary engines, not failures") suggests the thermodynamic reading is at least structural, `MY-READING`.
- **Axis 5** — AMOUNT/intensity: hot/cold magnitude. `OWNER-SOURCE`. How magnitude is measured without an unearned root metric is genuinely open — a metric here would violate the no-primitive-metric constraint unless earned.
- **Axis 6** — PRECEDENCE: `TopoOp = DOWN`, `OpTopo = UP` — whether topology applies before operator or operator before topology, i.e. the non-commutation of application order, made into an axis. `OWNER-SOURCE`. The Axis-6 seam is the named open seam in the proof lane.

Historical repository axis tables that conflict with these (Axis 0 as XOR/parity/etc., different 4/5 meanings) are MINE material — never to be imported.

### IV.2 Axes 7–12 (the upper manifold — the mesh)

`OWNER-LOCK` (07-20): the MESH is axes 7–12, the upper manifold / field level.

- **Axis 7:** node = engine-object. An engine that runs is a node.
- **Axis 8:** gossip = relation between engine-objects; a failure-card is an axis-8 payload.
- A 2-node mesh is the MINIMAL field. F4 is a candidate structure at this level.
- 9–12: unmapped in current work; `OPEN`.

The mesh is where multi-engine phenomena (redundancy, objectivity in the quantum-Darwinism sense) are supposed to live — see Part X.2.

---

## Part V — The QIT engines

### V.1 What an engine is

`OWNER-LOCK`. Two independent engine TYPES, each containing BOTH loops:

- **Type 1:** outer loop Deduction, inner loop Induction.
- **Type 2:** outer loop Induction, inner loop Deduction.

Stage orders (the engine checksum):

- **Deduction:** `Ne → Si → Se → Ni`
- **Induction:** `Ne → Ni → Se → Si`

The outer-to-inner state and record handoff is UNRESET — the inner loop inherits the outer loop's state and records without a wipe. This unreset handoff is load-bearing doctrine, not an implementation detail.

Chirality is an engine identity property (the two types are chiral partners under loop exchange, `MY-READING` of your chirality-installed results — installed, not forced).

`OWNER-LOCK` (OD-15 safe state, consistent with your statements): the ORDER, the dual-loop relation, the chirality identity, and the unreset handoff are locked. The specific channel/CPTP bindings proposed for Ne/Si/Se/Ni (Gemini's proposals) are RIVAL CANDIDATES — to be discriminated by deletion, substitution, and thermodynamic tournaments, not adopted because they are familiar.

### V.2 What "64" means

Two count-statements exist in your record and I believe they are the SAME claim in two vocabularies — `MY-READING`, flagged for your confirmation (this is OD-10):

- Older memory: 8 macro-stages / 32 microsteps per engine; 64 = PAIR total, never a stage count.
- Current checksum: 16 ordered engine positions × 4 rival candidate bindings per position = 64 candidate CELLS; `4^16` complete assignments.

Reconciliation: each engine has 8 positions (4 outer + 4 inner); the PAIR has 16 positions; 4 bindings per position gives 64 cells; 64 is a pair-level candidate count, never a sequential stage count. Both statements agree that nothing runs through 64 steps.

What 64 is NOT: 16 macro rows × 4 chronological substages (candidate → measurement → gate → receipt). That is a runtime bookkeeping object. The repo's current 64-slot packet is built that way, which makes it a DIFFERENT typed object from the engine checksum (see V.3).

### V.3 The live defect in the repo's engine packet

Verified this session on the current branch, not just on the stale main the auditors saw: `system_v7/sims/qit_full_type1_type2_64_live_v1/qit_full_type1_type2_64_live_v1_common.py` orders Type-1 outer deductive as `Se → Ne → Ni → Si` — not the checksum's `Ne → Si → Se → Ni`. All four loop orders in that file differ from the checksum.

Consequence (AR01 blocker 8, and I confirm it): every test that packet passed is evidence about a DIFFERENT finite protocol that happens to share labels with your engines. Those passes cannot validate the owner engines. The packet must either be corrected to the checksum orders or renamed and kept as a separate protocol whose results never touch engine-validation claims. Your call which (OD-10/OD-11 branch C keeps both under different names).

### V.4 Engine mechanics doctrine that survives regardless

`OWNER-LOCK` cluster: engines are COMPRESSION (loop-foundations binding); the engine must RUN to count (a stage-grammar label on a non-running object is nothing); 3-qubit minimum reaffirmed twice; stage-per-qubit is a hypothesis, not a result; WIN/LOSE is pure stage-grammar.

---

## Part VI — IGT

`OWNER-LOCK`:

- The four outcomes are `WINwin`, `WINlose`, `LOSEwin`, `LOSElose` — outer-case = outer loop, inner-case = inner loop. WIN and LOSE are never moralized; they are stage-grammar readouts, not value judgments.
- KK / KU / UK / UU (known-knowns through unknown-unknowns) = the IGT quadrants = stage readouts. The epistemic quadrant structure and the IGT outcome structure are the same 2×2 seen from two sides.
- IGT is to be simmed INDEPENDENTLY (the I-Ching correspondence is run as its own lane, never merged into engine validation).
- No MBTI import: Ne/Si/Se/Ni are formal position labels in the engine grammar. The typological vocabulary is a naming convenience, and any psychological semantics is explicitly out of scope.
- Terrain/topology: the packet vocabulary pairs a topology label (which of Ne/Si/Se/Ni) with a terrain and a precedence (operator-first vs terrain-first, which is Axis 6 appearing inside the engine). `MY-READING` of the intended relation: Axis-6 precedence is the engine-internal appearance of the manifold's TopoOp/OpTopo axis — the engine DOF and the manifold axis are typed differently but co-vary. Unconfirmed.

---

## Part VII — The sim engines

### VII.1 The engine contract

`OWNER-LOCK` (current, supersedes all older strictness variants):

| Lane | Role |
|---|---|
| **Julia** | reference semantics / authoritative. QuantumOptics.jl is the canonical quantum carrier. Julia's number wins a divergence. |
| **JAX** | the numerical workhorse. `jax.numpy` in x64 is the base array layer. Batched/exhaustive sweeps, vmap/jit/grad. |
| **NumPy** | satellite/control ONLY. Never load-bearing, never the workhorse. (The three-engine seal currently rejects numpy PRESENCE in sealed receipts — stricter than the satellite rule; that strictness is an installed gate you approved for the sealed lane.) |
| **PyTorch** | support/training where specifically earned; the learning engine (JEPA lane); currently deferred to the cloud-GPU phase. |

Machine: M1 MacBook Pro, 16 GB — batch sizes and parallel dispatch are sized to this.

### VII.2 The integrated library estate (measured, this session)

**Julia side — installed, exercised, fresh-verified:**

- QuantumOptics.jl — canonical density-operator carrier; authoritative legs of the three-engine sims
- QuantumClifford.jl — stabilizer/Clifford orbit probe (stress-verified)
- ITensors.jl — MPS cut-entropy probe (stress-verified)
- Catlab.jl — categorical carrier; the C4□C4 torus carrier calibration (BFS + SMT dual bipartiteness witnesses, polarity control)
- Z3.jl — SMT witnesses inside Julia legs (real API: `BoolVar(name, ctx)`, vector-form `Z3.And`)
- Attractors.jl — basin-of-attraction probe (stress-verified)
- Metatheory.jl — e-graph/rewriting lane, installed, probe queued
- CliffordAlgebras.jl / Grassmann.jl — geometric-algebra carriers (earlier-era legs)

**JAX side — installed, exercised, fresh-verified:**

- jax (x64) — base; the entropy-gradient sweep probe hit ~247k pts/s with 3-way agreement at 1e-15
- diffrax — Lindblad/GKSL ODE integration (stress-verified; adopted for the thermo arrows)
- ott-jax — optimal transport, W2 distances between eigdists (stress-verified)
- galois — finite-field ladder probe (stress-verified; numpy-backed internally, used in the control-adjacent lane, never sealed load-bearing)

**Solver/proof lane:** z3 (Python), cvc5 — load-bearing UNSAT/SAT with real-vs-erased verdict flips; sympy exact symbolic.

**New modalities (installed and probed this session, all HOLD):**

- dimod + neal — annealing/QUBO: exhaustive 2^16 enumeration = JAX Metropolis = dimod = neal on the Ising comparator, ΔE error 0.0
- pgmpy — factor-graph VariableElimination: exact vs VE at 1e-10, wrong-factor control diverges 0.33–0.73

**Evaluated and REJECTED (with reasons on file):** netket (NQS lane), quimb (PEPS lane), jax-verify; cuQuantum (no NVIDIA GPU on this machine — queued for the cloud phase); jax-metal (float32-only — violates the x64 requirement).

### VII.3 The sim contract

Every canonical sim: starts from SIM_TEMPLATE, carries `classification`, `TOOL_MANIFEST` (tried/used/reason), `TOOL_INTEGRATION_DEPTH`, positive + negative + boundary sections; at least one tool beyond the numeric baseline load-bearing; load-bearing means a CAPABILITY PROBE passes, not a string match. Scratch scripts are not sims. Stress-lane probes carry `unofficial_stress_probe` classification and `promotion_allowed: false` — they park by definition and can never promote anything.

### VII.4 The stress lane (the "unofficial sims" you ordered)

9 probes, all at `passes local rerun` as of the 07-23 validation: entropy_gradient_sweep, galois_field_ladder, diffrax_lindblad_cycle, ott_w2_eigdist, quantumclifford_orbit, attractors_basins, itensors_mps_cut, ising_comparator, factor_graph_settlement. Their job is to prove the LIBRARIES are genuinely wired and mutually consistent — they make zero physics claims.

---

## Part VIII — ClaimGate and the control plane

### VIII.1 Mission

`OWNER-LOCK`: put LLMs in deterministic boxes. The four-move threat model: an LLM can (1) edit the check, (2) fake the input, (3) skip the gate, (4) exploit a logic gap. Gates are CODE, hooks-fired, never LLM judgment. Truth is computed, never asserted.

### VIII.2 What is installed and verified (all `passes local rerun` at `6ccd79bdf`)

- **Three-engine seal** (`claimgate_plugin/three_engine_seal.py`): fail-closed; numpy/scipy/mpmath presence in a sealed receipt → REJECT; requires ≥2 authoritative engines load-bearing with numeric agreement < 1e-6; RE-RUNS the JAX leg and requires field reproduction < 1e-9 (it does not trust metadata — this closed the webui audit's holes). On CI, blocking: a numpy sim turns the repo RED un-bypassably. Last full run: 35 receipts pass, 0 rejected.
- **Transport canary** (`sim_engines/serialized/`): tombstone-and-boot serialized stage; stdlib sqlite ledger; re-derived SHA-256 chains; mock quarantine (mock payloads PARK, never admit); three status axes — execution_status / scientific_status / proof_status, where SAT means a completed COUNTEREXAMPLE reaching admission (exit 0) and a nonzero exit is infrastructure only, never a scientific verdict. No scientific claims by construction.
- **Carrier calibration** (`catlab_ratchet.jl`): C4□C4 torus, BFS + Z3 dual bipartiteness witnesses, odd-cycle polarity control, claim ceiling "carrier property only."
- **Envelope admission** (`claim_admission.mjs`): CR-side envelope check, explicitly NON-FINAL (exit 0 envelope-sound / 3 PARKED / 1 REJECTED); re-derives digests from disk; UNKNOWN parks separately from SAT.
- **Hostile-control corpus** (11 fixture classes + expected files + runner): standing no-drift regression. Current truth: **7 HOLD / 3 GAP**. The three open gaps: duplicate-JSON-key last-wins, NaN recompute "matches," renamed-metric silent chain-pass. The fix (an intake supervisor with `object_pairs_hook` dup-key rejection + NaN guard + schema pinning) is designed and queued as a codex card; acceptance = the corpus flips 2 gaps to HOLD with zero drift on the 7 HOLDs.
- **Postmortem** on file: 6 named misses of the earlier ClaimGate, each mapped to a hostile fixture.

### VIII.3 The composition (no self-certifying gate)

`OWNER-LOCK` via the webui audit doc: no single gate certifies itself. The chain composes: CR seal → Lev intake → core/eval → settlement. Each stage checks the previous stage's artifact; verdict bits live in exactly one brain (Lev's decision), receipts carry evidence only.

### VIII.4 The honest limit

AR01's enforcement-ladder point stands and I adopt it: ClaimGate as installed is an ARTIFACT CHECKER + envelope gate + CI tripwire. It can reject an artifact lacking a valid route. It cannot physically prevent a shell-capable LLM from bypassing it. The later ladder rungs (route broker → supervised execution → capability-confined runtime → causally attested LevOS-mediated runtime) are design targets, not installed. Nothing installed may borrow a later rung's language.

---

## Part IX — LevOS

`OWNER-LOCK` handling rules: `~/lev-main` is THE only Lev; read-only to me; no docs saved there; pull-only updates; ClaimGate patches live in Codex-Ratchet.

**Verified live seams (this session, `passes local rerun`):**

- `lev eval run <abs-path>.eval.js` — zero-touch evaluator; emits `lev.eval_decision.v1` into the execution ledger. A CR constraint-battery pass suite has been decided through pure upstream Lev — the decision artifact verified by schema, not by prose.
- `lev exec --verifier` — verifier-mode execution.
- `plugins/sim-witness` — carries cr_* eval packs and a `codex_ratchet.engine_leg_result.v1` adapter; upstream partially landed the old bridge design.
- One-brain contract holds: receipts carry NO verdict bits.

**Verified ABSENT (never claim them):** orchestration/steering (dead), agentfs-sdk, `lev.call` (unwired). `lev ratchet-admission` is the AAVF graph writer, NOT a receipt gate. The old fable/cr-sim-eval-pack branch's Lev-side implementation is unrecoverable (Trash emptied); its design survives in the wiring doc, bannered historical.

**The overread trap (AR01 blocker 10, confirmed):** a receipt saying `host_evidence_consumed` with `live_lev_consumed: false` is evidence-import, not "ran under LevOS." Only a decision artifact from a live Lev invocation counts, and only for claims that are actually Lev-integrated.

---

## Part X — The new directions

### X.1 P vs NP

`OWNER-TENTATIVE` hypothesis: the QIT engines get at P vs NP fundamentally. The anchor is exact: `a = a iff a ~ b` IS the Myhill–Nerode move — state = distinguishability class. The strongest form of the hypothesis: NP-hardness as a computational second law. First tooth (queued): a 2SAT / 3SAT / XOR-SAT terrain battery, where XOR-SAT is the control that separates geometry from hardness (it has the geometry but is in P). Status: direction only; nothing built validates it.

### X.2 Object-forming doctrine

`OWNER-LOCK` (07-21): the QIT engines are object-FORMING machinery. Pseudo-identity = correlation-so-high-across-probes (basins). Objectivity = redundancy across perspective-probes — the quantum-Darwinism form, which is why the mesh (axes 7–12) matters: redundancy needs multiple nodes. Legitimacy = surviving the engines' own loops. Open fork: graded pseudo-identity versus kernel-exact merge.

### X.3 The GPU / great-problems program

`CANDIDATE` (the Gemini GPU doc — audited clean as a correction document): bounded GPU campaigns on rented NVIDIA hardware (cuQuantum lane), each with an entry gate; annealing/tensor-network/solver tools as BOUNDED SEARCH, never proof oracles; a finite namesake result never solves an all-input/continuum/theorem-level problem. AR01 blocker 12's caution adopted: nothing yet shows the Ratchet contributes a new METHOD to these problems rather than governance around standard search. That is the bar the program has to clear.

### X.4 The recovery/control pack and audit round

The 20260723 v1 pack + AR01 audit (the zip this document responds to): the pack is a recovery archive / hostile-test catalogue / proposed governance layer — NOT boot canon, per its own audit. Sixteen owner decisions (OD-01–OD-16) gate any v2. The companion document to this one (`AR01_ZIP_REPAIR_LEDGER_20260724.md`) itemizes what needs fixing there.

---

## Part XI — What is genuinely open (the anti-collapse register)

Held-open forks, none of which I or any model may close:

1. Root object: installed executable floor vs strict nominalist floor vs two-lane (OD-01).
2. Exact root-constraint registry membership (OD-02).
3. MSS ↔ probes generative order: A/B/C (OD-03; Part II.4).
4. MSS admission rule precise statement vs any Pareto machinery (OD-04).
5. Ring-checkerboard: native literal carrier vs late presentation vs both-as-rivals (OD-05).
6. Spinor/chirality/orientation entry points — at least four roles, not one layer (OD-06).
7. Axis-0 formula (role locked, every formula candidate) (OD-07).
8. Manifold generative topology — the spine is CANDIDATE_A only (OD-08).
9. v8 content binding — v8 is your word; no single tree is yet bound to it. `origin/main` is 213 commits behind this session branch and still fronts v6-era docs; the branch has `system_v8/` but binding it is your act (OD-09).
10. 64 = candidate cells vs runtime substages — my reconciliation in V.2 awaits your confirmation (OD-10).
11. Repo engine packet stage orders contradict the checksum — correct or rename (OD-11; Part V.3).
12. Build order: ClaimGate/Lev first vs sim-engine independence first vs parallel-then-joined (OD-12; current de facto state is C — both advanced in parallel, no joint claim made).
13. Evidence-lane applicability matrix by claim type (OD-13).
14. Order of finitude/noncomm/nonassoc/anticomm/sedenion (META_AXIOMS Part C — permanently un-hard-coded until you say).
15. Positive/negative entropy gradients as separate gradients (your own tentative).
16. Graded pseudo-identity vs kernel exact merge (X.2).
17. D2 nonassociativity discriminator — installed, not forced; still open.
18. Axis-6 seam in the proof lane — open since 2026-04.

---

## Part XII — Implementation status ledger (honest labels)

| Object | Status | Receipt anchor |
|---|---|---|
| Three-engine seal + CI enforcement | passes local rerun (35/0) + green GitHub run | commits `69c3dc021`, `4e3acbca9`; run 29969379442 |
| Transport canary + carrier calibration | passes local rerun | `sim_engines/serialized/` receipts |
| Envelope admission (claim_admission.mjs) | passes local rerun | hostile runner output |
| Hostile corpus | passes local rerun; 7 HOLD / 3 GAP standing | `claimgate_plugin/fixtures/hostile/` |
| Stress lane (9 probes) | passes local rerun | `sim_engines/stress/` receipts |
| Lev eval seam (`lev.eval_decision.v1`) | passes local rerun | execution-ledger artifact, schema-verified |
| New modalities (dimod/neal, pgmpy) | passes local rerun | ising_comparator, factor_graph_settlement |
| Metatheory.jl lane | exists (installed; probe queued) | Project.toml commit |
| 64-slot engine packet | runs — but implements a DIFFERENT schedule than the checksum | Part V.3 |
| γ₅ literal spinor sim | exists, never run | named debt, task #7 |
| Axis-0 cofield formula | CANDIDATE only — nothing typed/earned | — |
| Manifold checksum (single authoritative graph) | does not exist | blocked on OD-08 |
| v2 recovery pack | must not exist yet | blocked on OD-01–OD-16 |
| GPU/cuQuantum lane | not started (no local GPU) | — |
| P-vs-NP terrain battery | not started | queued direction |

Nothing in this document is canonical by process. The strongest label anything here carries is `passes local rerun`, and the doctrine sections carry your authority, not mine.
