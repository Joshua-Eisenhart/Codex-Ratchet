# LLM Controller Contract

## Document Status
| Field | Value |
|-------|-------|
| **created** | 2026-04-08 |
| **purpose** | Prevent truth-maintenance drift in LLM-controlled sim sessions |
| **trigger** | Audit found Phase 7 C2 overclaim, stale registry, status label collapse |

---

## The Core Problem

LLMs treat "exists," "runs," "passes," "verified," and "canonical" as interchangeable.
They are not. Collapsing them produces false summaries that persist across sessions.

---

## Required Status Labels

Use ONLY these four labels. Never combine them. Never imply a higher label from a lower one.

| Label | Meaning | What proves it |
|---|---|---|
| `exists` | File or result is present in the repo | `ls` or `git status` shows it |
| `runs` | File executes without error | Local rerun completes, exit code 0 |
| `passes local rerun` | All tests in the file produce expected status | Fresh run output confirms it |
| `canonical by process` | Passes local rerun AND meets all template/tool/depth requirements | All of the above + SIM_TEMPLATE + tool manifest + classification field |

**Never write**: "28/28 PASS" without specifying which criteria were tested.
**Never write**: "verified" without citing the result file path and which run produced it.
**Never write**: "canonical" without confirming it meets canonical requirements per ENFORCEMENT_AND_PROCESS_RULES.md.

---

## Claim → Evidence → Verification Table

Before making any broad repo-state claim, fill this table:

| Claim | Source file | Result path | Criteria checked | Status label |
|---|---|---|---|---|
| (example) "28 families pass Phase 7" | sim_phase7_baseline_validation.py | phase7_baseline_validation_results.json | C1=✓ C2=PARTIAL(4/28) C3=✓ C4=✓ | passes local rerun (C1/C3/C4 only) |

Do not summarize without this table. Do not let a passing result on some criteria imply passing on all.

---

## Separate Lanes — Never Merge

These three programs run in parallel. Their progress does NOT aggregate.

| Lane | What it tracks | Current blocker |
|---|---|---|
| **Foundation migration** | 28 families numpy → torch | C2_graph_topology: 11/28 non-null, 0 mismatches |
| **Seam proof depth** | z3/cvc5 load-bearing on bridge/Phi0 | CLOSED 2026-04-08 for Phi0; open for Axis 6 |
| **Stack/nesting sims** | shell-local → coupling → coexistence | coupling sims in progress (2026-04-08) |

A breakthrough in lane 3 does not close a gap in lane 1.

---

## Coupling/Nesting Program (shell-local → emergence)

The correct research order is:
1. **Shell-local lego sims** — which primitive objects (states, operators, probes, entropies) are well-defined in isolation on each candidate shell?
2. **Pairwise coupling sims** — which shell-local structures remain compatible when two shells are active? Which interact nontrivially?
3. **Multi-shell coexistence** — small (2-3 shell) stacking tests
4. **Topology-variant reruns** — same coupling test, different topology class (topology-stable vs topology-sensitive)
5. **Emergence tests** — what entropy gradients, probes, or operators only appear when multiple shells run together?
6. **Bridge claims** — rho_AB, Xi, Phi0, Axis 0 — ONLY AFTER steps 1-5

Do not skip to step 6. Do not make bridge claims before shell-local and coupling work exists.

---

## Hard Stop Rules

1. **No registry/doc status edits** until the corresponding code/result gate is explicitly satisfied and the result file path is cited.

2. **Phase 7 completion** requires C2_graph_topology tested for all 28 families — not a subset.

3. **No claim of "canonical"** without SIM_TEMPLATE + tool manifest with non-empty reason fields + classification field set + passes local rerun.

4. **No "28/28" claims** without specifying exactly which criteria (C1/C2/C3/C4) were tested per family.

5. **Ban on absolute repo-state claims** unless the model cites a current file path and result from this run. "The repo has X" requires `ls` or `cat` evidence from this session.

---

## Batch Worker Constraints

When launching background agents:
- Each agent gets a **bounded task** with explicit deliverables
- The controller does a **consolidation pass** after agent completion:
  - Check for overclaim (agent says "all pass" → verify the specific criteria)
  - Check for stale doc edits (agent edited a doc → verify the code gate was met first)
  - Check for schema drift (agent used non-template format → flag for correction)

Do not take agent output at face value. Verify claims against result files.

---

## Prompt Structure for Sub-agents

Every agent prompt should have these sections in order:

1. **Read order**: which files to read first (ENFORCEMENT_AND_PROCESS_RULES.md, SIM_TEMPLATE.py, relevant result JSONs)
2. **Non-negotiable guardrails**: template compliance, tool manifest, non-empty reasons, classification field
3. **Allowed claims**: what this agent is permitted to conclude (bounded by its task)
4. **Required verification**: what must be run locally before the agent reports success
5. **Stop rules**: conditions under which the agent must stop and report back rather than proceeding

---

## Current Known Stale State (2026-04-08)

| Doc | Stale claim | Actual state |
|---|---|---|
| PYTORCH_RATCHET_BUILD_PLAN.md Phase 7 table | "PASS" for all 28 | C2_graph_topology: surface consistent, 0 mismatches; migration registry still NOT_STARTED |
| MIGRATION_REGISTRY.md | all 28 NOT_STARTED | torch sims and result files exist |
| ENFORCEMENT_AND_PROCESS_RULES.md | "enforcement is aspirational" | partially true — hook exists but not all sims comply |

These must be corrected before any agent reports "docs are current."
