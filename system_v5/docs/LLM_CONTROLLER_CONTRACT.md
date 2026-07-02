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
They are not. Collapsing them surfaces false summaries that persist across sessions.

---

## Controller Intercept Rule

**Named failure mode: Narrative Substitution for Gate Obedience.**

The controller's generalized failure is extracting a plausible story from the rules and obeying the story instead of the rules. The story feels like the rules. It is not the rules.

Evidence this failure is active:
- "Some locals are strong, so successor work is informative" — the story is plausible; the gate criterion is not satisfied
- "Most coupling work is done, so bridge claims are reasonable" — plausible; gate not cited
- "The agent said it's done, and it was working hard" — agent output is not the verification
- "This is the obvious next step given the research direction" — obvious is not admitted

**Intercept procedure:**
1. Read the controlling docs for the turn: `AGENTS.md`, `CODEX.md` when
   present, this contract, `ENFORCEMENT_AND_PROCESS_RULES.md`,
   `LEGO_SIM_CONTRACT.md`, and task-relevant ledger/source/result files.
2. When a proposed action feels like the natural next step given the research narrative: pause.
3. Name the specific gate criterion the action requires.
4. Cite the result file that satisfies that criterion from this session.
5. If the file cannot be cited: the gate is not satisfied. The action is excluded under the active constraint set.
6. Report: "Gate not satisfied: [gate name]. Blocking. [what evidence is needed]."

Do not smooth over gate failures with narrative. A smooth narrative that leads to the right answer by a different path is still a harness violation.

---

## Hard Build Guardrail

Controllers must preserve this order and distinction:

1. tool sims stay active
2. tool sims split to micro-probes: one tool, one function/API surface, one tiny claim, one bounded target, one positive/negative/boundary set
3. each tool finds useful bounded legos to test itself on before it is used inside lego-stage claims
4. tool-integration sims stay active only after the individual tool functions being coupled have their own receipts
5. lego sims stay active across the registry
6. classical baselines and controls may run more freely, but never as nonclassical or bridge evidence
7. coupling / coexistence execution is after lego-stage completion by default
8. any earlier pairwise/coexistence row must be an explicit bounded exception with named parent legos and no promotion claim
9. exploratory coupling does not authorize higher-stage promotion
10. bridge / axis / engine work remains late and gated

Do not rewrite this into "some locals are strong, so broad successor work can start."

The allowed middle is narrow: record future coupling candidates while the lego stage is active, and run only explicit bounded exceptions when the parent legos, stop rule, and no-promotion boundary are named.

For nonclassical manifold work, controllers must also preserve the finite-map
gate. A candidate step is not admitted unless it declares the domain, codomain
or output object, finite PEPS3D carrier anchor from the first finite
carrier/probe step, torch-native spinor state or spinor-derived density,
quaternionic map/invariant when quaternion language is used, F01/N01 witnesses,
negative/control, receipt path, and blocked downstream consumers. PEPS3D is not
a late layer after substages. A 16-stage-site inventory plus 64 operator rows
does not satisfy 64-substage manifold-cell embedding.

## Sim-Mode Full Wizard Parallelism

For sim/proof/tool-stage work, Full Wizard is not a decorative wrapper. It is the controller's default admission and parallelization mechanism.

Controllers must treat independent tool/function/API surfaces as parallel-safe for LLM packet authoring, audit, and queue planning. z3, cvc5, sympy, Clifford, geomstats, e3nn, rustworkx, XGI, TopoNetX, GUDHI, PyG, PyTorch/autograd, and other isolated tool rows may all be scouted in the same Wizard pass, provided each worker has one bounded tool/function/lego-target triple.

The Python runner may remain serial. Git/index mutation remains serial. That does not make planning, authoring, auditing, or follow-up scouting serial.

A sim-mode Full Wizard run is invalid if it narrows to one tool or one packet before a real parallel preflight has checked the other independent tool surfaces, unless the user explicitly asked for that one named tool. When runtime capacity exists, parent workers should use child workers for source slices, tool-row audits, and follow-up scouting. If child fanout stalls, reroute or debug the fanout path; do not continue as if a Full Wizard ran.

Accepted sim-mode closeout must distinguish:

- authored or queued packet;
- runner-executed result;
- receipt-backed ledger update;
- blocked/deferred tool surfaces;
- follow-up options that were actually Made, Scouted, and Audited.

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

## Separate Evidence Tracks — Never Merge

These programs do not aggregate, and none of them overrides the hard stage gate.

| Lane | What it tracks | Current blocker |
|---|---|---|
| **Foundation migration** | 28 families numpy → torch | C2_graph_topology: 11/28 non-null, 0 mismatches |
| **Seam proof depth** | z3/cvc5 load-bearing on bridge/Phi0 | CLOSED 2026-04-08 for Phi0; open for Axis 6 |
| **Stack/nesting sims** | shell-local completion plus bounded coupling/coexistence exploration | exploratory only until broader parent coverage is earned |

A breakthrough in the late-stage track does not close a gap in the foundation track, and it does not override the hard stage gate.

---

## Coupling/Nesting Program (exploration before promotion)

The correct research order is:

1. keep shell-local lego coverage expanding across the registry
2. record bounded pairwise/coexistence candidates from already-strong local parents
3. run an earlier pairwise/coexistence candidate only as an explicit bounded exception with named parents, stop rule, and no-promotion boundary
4. promote broader topology-variant / emergence work only after parent local and coupling evidence are strong enough
5. keep bridge claims — rho_AB, Xi, Phi0, Axis 0 — later than the exploratory coupling loop

Do not treat exploratory coupling as proof that the coupling stage is earned.
Do not skip to bridge claims at all.

---

## Hard Stop Rules

1. **No registry/doc status edits** until the corresponding code/result gate is explicitly satisfied and the result file path is cited.
2. Use the controller-side validator before accepting any worker closeout: `system_v4/skills/llm_research_enforcement_validator.py`.
3. Keep the gap matrix current in `docs/LLM_RESEARCH_GAP_MATRIX.json`; do not promote cells without evidence paths.
4. No broad coupling/coexistence/topology/emergence/bridge/axis queueing or launch merely because exploratory couplings exist.
5. No debugging stacked uncertainty. If a compound, stack, coupling, or integration packet fails and any participating tool function lacks an individual useful-lego receipt, stop debugging the compound packet and decompose to the first missing micro proof.
6. **Phase 7 completion** requires C2_graph_topology tested for all 28 families — not a subset.
7. **No claim of "canonical"** without SIM_TEMPLATE + tool manifest with non-empty reason fields + classification field set + passes local rerun.
8. **No "28/28" claims** without specifying exactly which criteria (C1/C2/C3/C4) were tested per family.
9. **Ban on absolute repo-state claims** unless the model cites a current file path and result from this run. "The repo has X" requires `ls` or `cat` evidence from this session.
10. **No nonclassical manifold, flux, Xi, Phi0, Axis0, basin, or physics queueing** unless the lower dependency receipt chain is cited from this session. If the chain is missing, only a bounded lower micro-scout or blocked-reason artifact is admissible.
11. **No label-first manifold claims.** `quaternion`, `Hopf`, `terrain`, `PEPS3D`, `substage`, `flux`, and `Axis0` language must be backed by explicit finite maps, carrier anchors, controls, and result paths.
12. **No layer/manifold completion wording without the claim gate.** Before a closeout, status artifact, prompt, or worker report says a layer is fully simed/simmed/simulated, parent-complete, stack-ready, admitted, true-G-structure complete, Axis0/FEP/flux unlocked, physics/gravity advanced, or final-manifold admitted, run `make layer-completion-claim-gate CLAIM_FILE=<claim text file when applicable>`. A failing gate blocks the claim even if local scout/result validators are green.

---

## Batch Worker Constraints

When launching background agents:
- Each agent gets a **bounded task** with explicit deliverables
- Agents write, repair, audit, and enqueue bounded probes. They do not execute sims; executable evidence comes from the Python runner and result JSONs.
- Micro tool workers get exactly one tool/function/lego-target triple. If they must debug more than one unknown at once, the packet is too large and must be split.
- The controller does a **consolidation pass** after agent completion:
  - Check for overclaim (agent says "all pass" → verify the specific criteria)
  - Check for stale doc edits (agent edited a doc → verify the code gate was met first)
  - Check for schema drift (agent used non-template format → flag for correction)

Do not take agent output at face value. Verify claims against result files.

---

## Prompt Structure for Sub-agents

Every agent prompt should have these sections in order:

1. **Read order**: which files to read first (`AGENTS.md`, `CODEX.md` when present, `ENFORCEMENT_AND_PROCESS_RULES.md`, `LLM_CONTROLLER_CONTRACT.md`, `LEGO_SIM_CONTRACT.md`, `SIM_TEMPLATE.py`, relevant ledger/audit/source/result JSONs)
2. **Non-negotiable guardrails**: hard stage gate, template compliance, tool manifest, non-empty reasons, classification field, finite-map gate, PEPS3D-from-start rule for nonclassical manifold work, no NumPy claim-bearing bridge
3. **Allowed claims**: what this agent is permitted to conclude (bounded by its task)
4. **Required verification**: what must be run locally before the agent reports success
5. **Stop rules**: conditions under which the agent must stop and report back rather than proceeding

For micro tool-stage workers, also include:

1. **Tool target**: exact tool and function/API surface.
2. **Lego target**: exact bounded lego or minimal fixture chosen to expose the tool.
3. **One variable**: what is allowed to be uncertain in this packet.
4. **Out of scope**: all stack, coupling, bridge, axis, engine, and promotion claims.
5. **Ledger loopback**: which tool/function row must be updated if the probe runs.

For manifold/foundation workers, also include:

1. **Finite map**: exact domain, codomain/output, and invariant or transition.
2. **Carrier**: torch-native spinor/quaternion object and PEPS3D site/bond/face/cell anchor from the start.
3. **Dependency receipts**: lower receipts required before this worker can advance.
4. **Blocked consumers**: flux, Xi, Phi0, Axis0, bridge, basin, and physics unless explicitly earned.
5. **Label ban**: no unearned manifold/layer/quaternion/Hopf/terrain/substage language.

---

## Controller Closeout — Block K (mandatory)

Every controller session ends with Block K from `~/wiki/harness/24_closeout_templates.md`. The closeout is the transmission channel between sessions; a rationalist closeout decays the shaped manifold before the next session boots.

```
Gates cited: <list of gates evaluated + step number from 06_coupling_program_order.md>
Admission decisions: <per gate: admitted | blocked | not evaluated>
Narrative substitutions intercepted: <if any adjacent-stage narratives were pressured and refused>
Worker claims verified: <per worker: which claims were checked against result files>
Worker claims not verified: <what was accepted on report only, if any>
Layer completion claim gate: <pass | fail | not_applicable; command path and CLAIM_FILE when used>
Status label changes to registry: <none | list with cited evidence path>
Blocked actions: <named actions that were refused with gate criterion>
```

Missing-field closeout reads as incomplete, not as finished. Do not smooth a Block K by omitting fields that would show refusals or unverifieds — the whole point of the channel is to carry the refusal shape forward.

---

## Current Controller State (verified 2026-05-01)

| Surface | Current state |
|---|---|
| Controller alignment audit | `controller_contract_current=true`, `docs_current=true`, `code_process_green=true` |
| Phase 7 C2 topology | surface consistent: 11 non-null, 17 null, 0 not-tested, 28 total; mismatch count 0 |
| Migration registry | `NOT_STARTED` remains a registry status label, not proof that no torch-family result files exist |
| Enforcement/process rules | bounded validators and commit-time manifest checks exist; full CI promotion remains future work |

Agents may report controller docs current only after `make align-strict-contract` passes.
