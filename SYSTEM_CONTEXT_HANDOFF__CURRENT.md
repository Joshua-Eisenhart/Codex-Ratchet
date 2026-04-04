# System Context Handoff — Current

Status: rolling handoff surface
Purpose: preserve current understanding and planning so a new Hermes thread can pick up the work without losing the frame

## 1. Current overall direction

The immediate priority is not broad v5 completion.
The immediate priority is to get the QIT engine prototype properly ratcheted and simulated in a scientifically respectable pre-Axis program.

The broader v5 system should later grow out of that substrate.

## 2. Core scientific frame

- Root constraints do not create geometry directly.
- They restrict admissible math and admissible geometry.
- Broader carrier layers stay nested; narrower layers do not simply replace them.
- The current chain is best understood as:
  constraints -> admissibility charter C -> admissible manifold M(C) -> geometry buildup -> Weyl working layer -> bridge family Xi -> cut family A|B -> kernel family Phi_0(rho_AB)
- Bridge and cut are separate open layers.
- Axis 0 comes after a legitimate lower stack and after a bridge/cut exists.

## 3. Current anti-smoothing rules

- Do not collapse executable winners, doctrine-facing winners, and pointwise discriminators into one fake closure.
- Open branches remain open until mechanically narrowed.
- Underpowered sims are diagnostic_only.
- No prose upgrades a result; only artifact class and proper tool use can.

## 4. QIT proto sim method

The sim plan is:
- build small sims as legos
- start from root constraints
- use the proper tool stack by tier
- include negatives
- emit witnesses/artifacts
- compose upward only from admitted or clearly fenced pieces
- finish pre-Axis tiers before real Axis-entry work

## 5. Hermes role

Hermes is being treated as:
- the A2 high-entropy ingestion plane
- a bounded planning/audit surface
- a support layer for the scientific and architectural work

Hermes should not be asked to ingest the whole repo/system at once.
Hermes should be fed bounded packs slowly.

## 6. Current planning docs created

Main planning bundle currently includes:
- `SYSTEM_META_PLAN__REPOS_PYTHON_SKILLS_HERMES.md`
- `HERMES_STACK_AND_ADDONS_PLAN.md`
- `BOUNDED_HERMES_INGESTION_PROTOCOL.md`
- `QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md`
- `LEGO_SIM_CONTRACT.md`
- `NONCLASSICAL_SYSTEM_TOOL_PLAN.md`
- `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`
- `SKILLS_PLAN__KEEP_BUILD_PATCH_RETIRE.md`
- `PYTHON_REPO_SKILLS_INVENTORY_AND_CLEANUP_PLAN.md`
- `FULL_MACHINE_PYTHON_REPO_SKILLS_INVENTORY.md`

## 7. Current environment/cleanup understanding

- Main repo remains on Desktop.
- Git repos remain in `~/GitHub`.
- Clean external Python-related folder chosen: `/Users/joshuaeisenhart/python`
- Homebrew Python is the current likely canonical interpreter family.
- `.venv_spec_graph` inside the repo is a cleanup target, but not deletable yet because repo code still references it.
- The cleanup should happen slowly: standardize/install/test first, delete redundancy later.
- Hidden environment/tooling surfaces known so far include at least: `~/Library/Python/3.13`, `~/Library/Python/3.9`, `~/.local`, `~/.conda`, `~/.hermes/hermes-agent/venv`, `~/LevRatchet`, and `~/GitHub/reference/*`.

## 8. Important external/reference surfaces

Known relevant source families include:
- `~/GitHub/reference/other/z3`
- `~/GitHub/reference/deepmind/alphageometry`
- `~/GitHub/reference/other/dreamcoder-ec`
- `~/GitHub/hermes-agent-self-evolution`
- `awesome-hermes-agent` as a curated ecosystem list
- `lev-os` and related Leviathan surfaces as bounded external source families
- `/Users/joshuaeisenhart/LevRatchet` as a real archive/ingest source that should likely be archived and processed

## 9. What deeper reading has recently confirmed

From deeper `system_v5` and bounded `system_v4` reads:
- enforcement, fail-closed process, fixed tool requirements, fixed artifact requirements, and fixed claim limits are central
- geometry is upstream of Axis 0
- bridge Xi is open
- cut A|B is open
- coherent information / negative conditional entropy is the strongest simple kernel family
- `Xi_hist` is the strongest live executable bridge family
- shell/interior-boundary is the strongest doctrine-facing cut family
- point-reference is the strongest live pointwise discriminator
- raw local L|R is control only and killed as sufficient
- executable winners, doctrine-facing winners, and pointwise discriminators must not be collapsed into one fake closure

## 10. system_v4 understanding so far

Current understanding:
- `system_v4` is the active build layer for runtime/graph/skill/probe/integration work
- it does not replace `system_v3` owner-law and canonical A2 brain
- `system_v4` already has a strong authority/support/superseded discipline
- it now needs deeper bounded reading to understand what active machinery is already present

Important already-found system_v4 surfaces:
- authoritative Ax0/bridge/cut docs
- graph/runtime/skill/probe machinery
- daemon/heartbeat + YAML/constraint surfaces

## 11. Daemon / heartbeat / YAML finding

A real daemon/heartbeat layer appears to already exist in `system_v4`, including:
- `system_v4/runners/run_refinery_daemon.py`
- `system_v4/skills/intent-compiler/heartbeat_daemon.py`
- `system_v4/skills/intent-compiler/dna.yaml`
- `system_v4/skills/intent-compiler/constraint_manifold.yaml`
- heartbeat logs/plist surfaces under probes

This means the daemon/heartbeat + YAML/constraint layer is not just external inspiration; it already exists in the repo and needs bounded reading.

Operational note:
- the graph-rich writeback path is no longer just a false green problem; with the richer stack available it reports real failures in `sim_edge_state_writeback.py`, so the writeback path itself is a real code/workflow problem to fix later.

## 12. Current best bounded next read packs

### Pack A — system_v4 Ax0/QIT authority packet
Read order:
1. `system_v4/docs/CONSTRAINT_GEOMETRY_AXIS0_SEPARATION.md`
2. `system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md`
3. `system_v4/docs/AXIS0_CUT_TAXONOMY.md`
4. `system_v4/docs/AXIS0_KERNEL_BRIDGE_CUT_HANDOFF.md`
5. `system_v4/docs/QIT_ENGINE_GEOMETRY_ENTROPY_BRIDGE_MASTER_TABLE.md`

Purpose:
- sharpen understanding of the lower scientific stack and the bridge/cut/kernel differentiation

### Pack B — system_v4 daemon/heartbeat/intent-compiler packet
Read order:
1. `system_v4/runners/run_refinery_daemon.py`
2. `system_v4/skills/intent-compiler/heartbeat_daemon.py`
3. `system_v4/skills/intent-compiler/dna.yaml`
4. `system_v4/skills/intent-compiler/constraint_manifold.yaml`
5. `system_v4/ctx/operating_protocol.yaml`
6. heartbeat logs/plist after that if needed

Purpose:
- understand the existing daemon/heartbeat + YAML constraint layer

## 13. Context-window preservation rule

Use this file as the rolling continuity surface.
Do not rely on chat memory alone.

When a bounded read pack finishes, update this handoff with:
- what the pack clarified
- what it owns
- what remains open
- what next pack should be read

## 14. Current most likely next useful docs to create later

- `CURRENT_PRE_AXIS_SIM_STATUS__KEEP_OPEN_DIAGNOSTIC_BROKEN.md`
- `CONSTRAINT_ENGINEERING_LAYER_PLAN.md`
- `HEARTBEAT_DAEMON_AND_REACTIVE_SYSTEM_PLAN.md`
- `HERMES_REPOS_AND_ECOSYSTEM_CLASSIFICATION.md`

## 15. Short handoff summary

A new Hermes thread should start from this frame:
- the QIT proto and pre-Axis sim ladder come first
- constraints/manifold/geometry/bridge/cut/kernel must stay separated
- Hermes is the bounded A2 high-entropy ingestion plane
- the repo needs slow stabilization, not mass deletion
- Homebrew Python is the current likely canonical interpreter family
- current richer tool stack is available under that canonical interpreter for most core graph/proof/geometry work, but `cvc5`, `quimb`, `qutip`, and `ripser` are still missing there
- `.venv_spec_graph` remains a legacy environment with additional packages and still-hardcoded references; it is not deletable yet
- system_v4 now needs deeper bounded reading to understand the active machinery
- the next recommended bounded read is the daemon/heartbeat/intent-compiler packet
