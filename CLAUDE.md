# Codex Ratchet — Claude Reference Instructions

## LEV OS BOOT (BINDING, 2026-07-19 owner order — fires via .claude/hooks/session-start.sh)
This repo runs UNDER Lev OS. Front door: /Users/joshuaeisenhart/GitHub/lev — read AGENTS.md (iron-clad laws), dna/graph.yaml (C1 FINITUDE / C2 NON-COMMUTATION), .lev/validation-gates.yaml BEFORE work. CR-facing Lev branch: lev-main fable/cr-sim-eval-pack (Ratchet policy receipts). Hooks installed: session boot + post-compaction rule re-injection (.claude/hooks/). Inventory before generation, every task.

This file is Claude-facing project guidance and reference doctrine. It is not Codex authority. Codex behavior is governed by repo-root `AGENTS.md`; Codex may read this file only as project-process reference.

## BINDING STATE 2026-07-04 (owner corrections — read before anything else)

1. Axis 0 = an entropy gradient, at the BEGINNING, innate. It is the drive. The readout (Phi_0, needs a cut, via Xi) is LATE. Two objects, one name — never conflate. A ratchet cannot move without a gradient.
2. Tentative (owner: "could be wrong"): positive entropy (growth/expansion) and negative entropy (records/locks) are each their own gradients; Axis 0 = the gradient between them.
3. MSS = Minimal Evolving Persistent Structure. MSS = ratchet = tower = nesting = replicator (one thing, different names). The ratchet is NESTED: each rung runs ON the one below; density matrices come early; Shannon and later entropies are licensed late.
4. Name: quantum-entropic-geometry. "Entangled rolling dice" is a METAPHOR — never mechanize metaphors into sim designs.
5. The owner's docs are the spec. Axis 0 spec: system_v7/constraint_core/reference_docs_from_josh/physics_program/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md (sections 37-38 are the sim requirements + controls). Build from cited doc sections or do not build.
6. Process (violating this produced 5 audit-killed builds on 2026-07-04): no build without a card citing doc sections; sims run ON the sim engines (constraint_core/engines lane, GKSL generators, aligned Julia) — ad-hoc scripts are not sims; a task must come from a measured doc-vs-repo gap, never invented; one lane at a time; fresh audit before any claim.
7. Standing goal: get the QIT engines running on the corrected foundation (drive at the front, Phi_0 late). First step: baseline `python3 run_all.py` in system_v7/constraint_core and `validate_engines.py` in constraint_core/engines (Julia engine there has never been run).
8. A0_raw is an unfused LIST, not a vector — no component mixing; no unearned algebra anywhere.

## CB WORK — BINDING 2026-08-08 (fires every session; read before touching constraint_box/)

**START HERE: `constraint_box/CB_READ_THIS_FIRST.md`** — the reading order, with what each
document gives you. Read it before touching anything under `constraint_box/`.

**There is already a working ConstraintBox.** Packaged at `constraint_box/src/constraintbox/`:
929 passing tests, 33 CLI subcommands, mini-LevOS flow kernel, the S1-S4 estate ladder,
ClaimGate integration. Install it: `pip install -e constraint_box/src`. Then `constraintbox --help`.

Six rules. Each one exists because it was broken.

1. **FIND BEFORE BUILD.** Before writing any new script, search the package for the
   capability: `grep -rl "<thing>" constraint_box/src/constraintbox/` and
   `constraintbox --help`. If it exists, use it. `cb_heavy_gate.py` duplicated
   `constraintbox estate` and was worse. Twenty `cb_*.py` scripts were written that
   never import the package.

2. **A SCRIPT THAT DOES NOT IMPORT `constraintbox` IS NOT CB WORK.** The kernel is
   `mini_levos.py` — MiniLevRuntime, FlowPolicy, typed hook nodes, six budgets,
   hash-chained ledger, five terminals, 30 construction + 30 runtime invariants.
   A wave IS a FlowPolicy. A council IS nodes. A member IS a registered hook. A gate
   IS a GATE-kind node. Looping back IS a transition. A dead loop IS the HOLD terminal.
   Do not re-implement sequencing, budgets, receipts or terminals outside the kernel.

3. **LAYER ORDER, NO SKIPPING.** CB -> sim engines -> manifold -> DOFs -> engines ->
   holodeck. Running holodeck while CB is unfinished is a violation, not progress.
   State the layer before starting. If the task is not at the current layer, refuse it.

4. **DO NOT RUN A TOOL BLINDLY.** A tool with no fixture, no negative control and no
   declared expected output is not ready to be pointed at real material. Widening a
   pattern until it matches 16x more is noise, not extraction.

5. **REPORT THE WHOLE STATE, NOT THE FAVOURABLE SUBSET.** If the ladder reads DRIFT
   overall, the headline is DRIFT. Required-only counts go after the overall number,
   never instead of it. `exists < runs < passes local rerun < canonical by process` —
   never imply a higher rung from a lower one.

6. **RESOLVE WHAT YOU CAN LOOK UP.** A question answerable by reading the repo is not
   an owner decision. Ask the owner only for rulings that require his intent.

**Scope discipline:** new builds, refactors and research are out of scope unless asked.
When a ranked list suggests work, check it against rule 3 before acting on it.

---

## Harness Preamble (priming — read first, every session)

You are working under a nominalist constraint-admissibility harness.

Root axiom: `a = a iff a ~ b`. Identity is probe-relative, not primitive. The only primitive is `~`, probe-relative indistinguishability under an active probe family `M`.

Every substantive claim needs three supports: probe family `M`, admissibility (survivor status under active constraints `C`), and a quotient (the equivalence class `S/~_M`). If you cannot cite all three, demote the claim to provisional.

Banned verbs: causes, creates, drives, produces, generates, makes, forces, determines. Preferred verbs: survived, admitted, excluded, indistinguishable, coupled with, co-varies under, UNSAT under, consistent with, stable under probe, pulled back.

Status ladder: `exists < runs < passes local rerun < canonical by process`. Never imply a higher label from a lower one.

Preserve divergence. Do not collapse surviving candidates. Pushback on harness conflicts rather than smoothing.

**Current Wizard harness for Claude reference:** `~/wiki/wizard/` — read `README.md`, `00-read-first.md`, and `AGENTS.md` first when Claude is asked to use the Wizard. For nominalist-CS support material, use `~/wiki/wizard/harness-consolidated/`; the old `~/wiki/harness/` path is provenance/support, not the active Wizard boot surface.

---

## Operating Principles (Karpathy)

1. **Think before coding.** State ambiguity explicitly; present multiple interpretations rather than silently picking one. Push back if a simpler approach exists. Ask, don't guess.
2. **Simplicity first.** No features beyond what was asked. No abstractions for single-use code. No error handling for impossible scenarios. If a senior engineer would say "overcomplicated," rewrite.
3. **Surgical changes.** Don't "improve" adjacent code. Match existing style. Mention unrelated dead code, don't delete it. Every changed line must trace to the request.
4. **Goal-driven execution.** Turn tasks into success criteria (write the failing test first, then make it pass). Don't report "done" without checking the criterion.

### Verification discipline (session-learned)

After any multi-step action chain — especially when another agent (Hermes, Codex) reports completion — verify state directly before trusting the claim:
- `ps aux | grep <process>` before trusting "I killed it"
- `git status` / `git log` before trusting "I committed it"
- Read the actual file before trusting "I fixed it"
- Runtime shape tests (not just string-presence) for load-bearing loops (overnight runner, queue controllers)

## Read First (every session)
Before any work: read `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md` and `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`.

**Docs home (updated 2026-07-22, owner order "we are in v8"):** current-era docs (state reports, audits, layer math, durable state) live in `MODEL_DOSSIER/` at repo root. `system_v5/docs/` is a HISTORICAL archive — read it as a mine, never write new docs there. Do not create `docs/` at repo root. GENERAL RULE (same class as "old docs are a mine"): any path or rule in this file stamped with an earlier system era (v4/v5) is historical unless re-affirmed; the live surfaces are `system_v8/`, `MODEL_DOSSIER/`, `ROOT/`, and current receipts. When an era-stamped rule conflicts with where current work lives, ASK or follow the current era — do not obey stale canon silently.

---

## Status Labels (mandatory — never collapse)

Use ONLY these four labels. Never imply a higher label from a lower one:

| Label | Meaning |
|---|---|
| `exists` | File is present in repo |
| `runs` | Executes without error (exit 0) |
| `passes local rerun` | Fresh run confirms all tests pass |
| `canonical by process` | passes local rerun + SIM_TEMPLATE + tool manifest + non-empty reasons + classification field |

Never write "verified," "confirmed," "28/28 PASS," or "all pass" without specifying which criteria were checked and citing the result file path from this session.

---

## Hard Stage Gate

> **SUPERSEDED FRAMING NOTE (2026-06-08):** the current execution roadmap is `~/wiki/projects/codex-ratchet/current-canonical-plan-and-anti-drift-2026-06-08.md` (4-layer Julia-Canon / JAX / PyTorch / world-engine stack). `17_actual_lego_registry.md` + `MIGRATION_REGISTRY.md` are now a **MINE for math objects, NOT the roadmap**. The stage-gate ORDERING below still holds (tool → integration → lego → coupling → bridge); the *registry it pointed at* is historical. Current frontier is named by current receipts + repo gates, not by the old registry rows.

Do not soften this into flexible lanes (the ORDER is binding; the lego stage is verified by current receipts/gates, not the old registry):

1. tool sims
2. tool-integration sims
3. all lego rows, one by one, until the lego stage is complete — verified by current receipts and repo gates (the old `17_actual_lego_registry.md` is historical/a mine, not the authority)
4. only then couplings
5. only after coupling/coexistence/topology/emergence evidence, bridge or axis-level claims

No partial local success authorizes coupling work.
No "some strong locals" exception exists.
Do not start pairwise/coexistence work just because a few lego anchors are strong.

---

## Coupling Program Order (shell-local → emergence)

This is the active research program. Do not skip steps or merge them:

1. **Shell-local lego sims** — complete the lego stage across the required registry rows first; which objects (states, operators, probes, entropies) are well-defined in isolation on each candidate shell?
2. **Pairwise coupling sims** — which shell-local structures remain compatible when two shells are active?
3. **Multi-shell coexistence** — small (2-3 shell) stacking/nesting tests
4. **Topology-variant reruns** — same coupling test, different topology class
5. **Emergence tests** — what quantities only appear when multiple shells run together?
6. **Bridge claims** (rho_AB, Xi, Phi0, Axis 0) — ONLY AFTER steps 1–5

Do not advance to step 6 without evidence from steps 1–5.

---

## Three Separate Lanes (never merge progress)

| Lane | What it tracks | Current status |
|---|---|---|
| ~~Foundation migration (numpy→torch)~~ — **SUPERSEDED 2026-06-08** | now the 4-layer engine architecture: Julia Canon / JAX workhorse / PyTorch first-class graph-engine / world-engine | PyTorch substrate active (389 scouts + 10/14 legos torch); numpy→torch is NOT a pending migration. numpy = control-only |
| Seam proof depth | z3/cvc5 load-bearing | Phi0 seam closed 2026-04-08; Axis 6 open |
| Stack/nesting sims | shell-local→coupling→coexistence | Layer triple catalog done; coupling matrix in progress |

---

## Sim Requirements

Every canonical sim must:
- Start from `system_v4/probes/SIM_TEMPLATE.py`
- Have `classification` field set: `"classical_baseline"` or `"canonical"`
- Have `TOOL_MANIFEST` with `tried`, `used`, and non-empty `reason` for every tool
- Have `TOOL_INTEGRATION_DEPTH` with `"load_bearing"`, `"supportive"`, or `None`
- Have positive + negative + boundary test sections
- Use interpreter defined in `Makefile` (`PYTHON` var — codex-ratchet env)

At least one tool outside the numeric baseline must be `load_bearing`.

Tool-lego fit probes may use `classification = "tool_lego_fit_probe"` only as
pre-admission evidence. They must state `promotion_allowed: false` in the result
summary or an equivalent claim ceiling, and they do not satisfy canonical,
bridge, QIT, GStack, axis, or nonclassical admission by themselves.

---

## Known Stale State (2026-04-08 — now itself SUPERSEDED 2026-06-08)

These rows describe the OLD numpy→torch migration framing, which is no longer the plan (PyTorch is now the first-class graph/network engine; numpy→torch is not a pending migration). Retained as historical:

- ~~Phase 7 table: "PASS" = C1/C3/C4 only; C2_graph_topology surface consistent (0 mismatches) — migration registry remains NOT_STARTED~~
- ~~MIGRATION_REGISTRY.md: shows all 28 NOT_STARTED; torch sims exist~~

Do not edit the OLD migration docs to show progress; they are a mine, not the roadmap. Current state lives in current receipts + repo gates + the 2026-06-08 canonical plan.

---

## System Framing (nonclassical constraint-admissibility)

This system is NOT classical state mechanics. It is a constraint-admissibility geometry:
- Distinguishability constraints are prior to entropy summaries. Do not infer ontology from entropy alone.
- Constraints eliminate what cannot persist; they do not deterministically generate what must exist.
- Surviving families are provisional. "Constraint-admitted" ≠ "theorem-proved."
- Later-compatible organization feeds back on which earlier candidates are meaningful. Evaluation is not purely forward.

**Operational rules** (required language discipline):
- Use "candidate," "admissible," "excluded," "indistinguishable," "stable under probe/coupling" — not classical certainty language
- Separate forward-evolution claims from backward-admissibility claims explicitly
- Never collapse multiple surviving candidates into one "true" object prematurely
- Prefer exclusion language over construction language ("L3 destroys L1's structure" not "L3 produces a dephased state")
- Treat z3 UNSAT as the primary proof form — structural impossibility is more fundamental than existence

**Do NOT do:**
- Use entropy as the master organizing variable
- Treat forward propagation and backward admissibility as the same process
- Infer that passing a test = being the correct object (a candidate that passes is still a candidate)
- Use "causes," "creates," "drives" — use "coupled with," "survived," "co-varies under"

---

## Anti-Patterns to Avoid

- "ALL PASS" when some tests are skipped or use weaker criteria
- Reporting agent output as verified without checking the result JSON
- Editing a registry/status doc before the sim passes
- Treating "exists" as "canonical"
- Launching coupling sims before shell-local sims exist for both layers
- Launching pairwise/coexistence work before the lego stage is complete across the registry
- Treating entropy as sufficient evidence for shell membership (coupling behavior determines shell)
