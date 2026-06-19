# Codex Ratchet — Claude Reference Instructions

This file is Claude-facing project guidance and reference doctrine. It is not Codex authority. Codex behavior is governed by repo-root `AGENTS.md`; Codex may read this file only as project-process reference.

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

All human-readable docs live under `system_v5/docs/` (with subdirs: `plans/`, `references/`, `new content/`, `archive/`, `archive_old/`, `archive_hermes_overlaps/`). See `REPO_LAYOUT.md` for the map. Do not create `docs/` at repo root.

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
