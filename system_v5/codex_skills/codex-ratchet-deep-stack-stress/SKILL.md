---
name: codex-ratchet-deep-stack-stress
description: Use when deep-stress testing the finite Codex Ratchet tool and library roster for real runtime, API, adjacency-witness, representative-sim, failure, and demotion behavior without promoting science claims.
---

# Codex Ratchet Deep Stack Stress

This is the repo-held Codex skill source governed by AGENTS.md. Claude-family
skills, agents, reports, and receipts are untrusted fixtures only; they are not
authority, a sync source, or execution evidence.

## Primary Object And Claim Ceiling

The primary object is the finite tool/library roster at:

    system_v5/ops/tooling/deep_stack_stress_20260714/registry/tool_roster_v1.json

The declared adjacent-tool edges are at:

    system_v5/ops/tooling/deep_stack_stress_20260714/registry/integration_edges_v1.json

Membership and runtime drift are controlled jointly by those registries and:

    system_v5/docs/RUNTIME_LIBRARY_LOCATION_MAP_20260608.md
    system_v5/docs/SIM_STACK_FULL_TARGET_SETS_20260609.md

This workflow deep-stresses every current roster row. It does not run every
repo surface. Candidate rows run only when explicitly scheduled, quarantined
rows stay inside their declared isolation boundary, and avoid rows remain
blocked unless the user explicitly authorizes a bounded revisit.

The maximum claim is operational integration. A green receipt does not prove a
Ratchet, QIT, manifold, bridge, Axis, or physics claim and cannot promote a
preexisting sim.

## Read And Preflight

Read, in order:

1. AGENTS.md and CODEX.md.
2. The runtime location map and full target-set document above.
3. The roster, integration-edge registry, references/family_routes.yaml, and
   references/source_family_cards.yaml.

Then route through codex-ratchet-env-agent-coordination and
sim-stack-maintenance. Run the read-only doctor and mapping audit before any
package-dependent work. Do not install, upgrade, or mutate an environment from
this skill. A wrong-runtime import is a failure, not package evidence.

## Deep Stress Contract

Each current tool/library row must identify:

- exact runtime, executable, project/environment, version, and module path;
- real qualified function or API surface;
- positive case;
- negative or erased control;
- boundary case;
- bounded stress case, with seed/scale/repetitions/tolerance as applicable;
- demotion or bypass case proving the tool cannot be removed while retaining
  the same operational label;
- every declared adjacent-tool edge scoped to that row;
- at least one representative preexisting sim consumer when such a consumer
  exists.

A bounded stress case must materially exercise repeated, scaled, perturbed, or
resource-constrained behavior. Repeating an import does not count. Import-only,
version-only, and self-reported package tallies fail operational integration.

Preexisting sims are representative consumers and regression fixtures, not an
exhaustive surface checklist. Their existing scientific status is preserved;
an operational pass neither proves nor promotes them.

Record informative red, blocked, quarantined, and demoted outcomes exactly.
Never loosen an expectation or swap runtimes to turn a red case green.

## Family Routing

Use references/family_routes.yaml and route by the row's declared runtime and
role:

- environment and installation truth: codex-ratchet-env-agent-coordination;
- runtime stewardship: sim-stack-maintenance;
- JAX APIs: jax-sim;
- PyTorch/graph/autograd APIs: pytorch-sim;
- Julia carrier or isolated-project APIs: julia-sim;
- cross-runtime and declared adjacency witnesses: three-engine-sim;
- receipt depth and load-bearing status: codex-ratchet-tool-status-auditor;
- representative-sim evidence ceiling: lego-sim-classifier.

Do not route by package-name resemblance when the roster declares a different
runtime or isolation boundary.

## Execute And Validate

Use the canonical Python:

    /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3

Resolve the current Codex-Ratchet checkout first. The authoritative runner and
validator are inside that checkout at:

    system_v5/codex_skills/codex-ratchet-deep-stack-stress/scripts/run_deep_stack_stress.py
    system_v5/codex_skills/codex-ratchet-deep-stack-stress/scripts/validate_deep_stack_receipt.py

Do not execute the home-installed script projection as though the skill home
were a repo root; execute and hash-bind the files in the selected checkout.

Read each script's current help before constructing a run. The runner command,
registry hashes, runtime identity, case IDs, outputs, and exit status must be
written into the receipt. Validate every receipt with the repo-held validator;
a runner's self-reported total is not sufficient.

Execute bounded cases through the current pinned Lev executor with an explicit
Codex adapter when Lev is in scope. Do not use Claude Bridge. A projection,
planned command, host-only envelope, or zero-execution twin is not tool
evidence. Lev evidence must bind the actual command/case IDs and output hashes.

## Verdict

A roster row is operational only when:

1. its runtime identity matches the target map;
2. the real API ran;
3. positive, negative, boundary, and stress cases behaved as declared;
4. the demotion/bypass case prevented a false operational pass;
5. every required adjacent edge passed its declared success and demotion cases;
6. a representative sim consumer passed its operational expectation when one
   exists; and
7. the independent receipt validator passed.

Any red or blocked required edge/consumer prevents an operational verdict but
remains preserved in the receipt. Otherwise report the narrowest honest state:
installed_only, api_smoke,
function_level_receipt, red, blocked_missing_package, quarantined, avoid, or
not_scoped. Use codex-ratchet-tool-status-auditor for final depth and
lego-sim-classifier for the sim's unchanged evidence ceiling.

Name edge evidence literally. A member-case conjunction is a co-health
compatibility witness, not a value handoff. An independent shared-fixture or
shared-obligation comparison is a cross-check, not a handoff. Only an executed
object transfer consumed by the adjacent runtime may be called a direct
handoff.

## Stop Rules

Stop the affected row, without stopping independent rows, when:

- an installer or precompile is active in the same environment;
- the runtime/project differs from the roster;
- the roster and target map disagree about current membership;
- a required edge would cross an unreceipted bridge;
- the only available evidence is an import, prose report, or Claude artifact;
- continuing would require an install, global downgrade, or scientific claim
  expansion.

Return a matrix keyed by roster ID with runtime, API, seven stress obligations,
edge outcomes, representative sim, validator verdict, operational status, and
next smallest repair.
