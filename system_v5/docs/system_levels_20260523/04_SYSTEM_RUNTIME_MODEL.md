# System And Runtime Model

Date: 2026-05-23

Status: runtime-facing documentation. Not canon by itself.

2026-05-23 quarantine note: any current formal-scout pass/blocker wording in
this file is stale until clean independent reruns rebuild the cited receipts.

## 1. Runtime Truth Surfaces

The system trusts current executable receipts more than historical prose.

Important surfaces:

```text
system_v5/ops/formal_scouts/
system_v5/ops/formal_scouts/results/
system_v5/docs/
system_v5/ops/
scripts/lint_sim_contract.py
system_v5/ops/formal_scouts/validate_formal_scout_results.py
```

## 2. Basic Sim Contract

Every serious sim should expose:

```text
classification
TOOL_MANIFEST
TOOL_INTEGRATION_DEPTH
positive
graveyard_companions
boundary
all_pass
claim_ceiling
blockers
open_next_work
```

For nonclassical sims, PyTorch should be the load-bearing numerical surface.
NumPy should not be the load-bearing implementation for nonclassical QIT sims.

## 3. Current Runtime Stack

The working runtime pattern is:

```text
source/math docs
  -> formal scout script
  -> result JSON
  -> contract lint
  -> fresh-rerun validator
  -> audit/synthesis doc
```

## 4. Status Labels

Use these meanings:

```text
owner_thesis     human origin idea, not enforceable yet
candidate_fence  suspected derived constraint needing a gate
formal_scout     bounded executable probe, no promotion by itself
canonical         stronger status only when current admission surfaces allow it
graveyard         killed, demoted, or control-failed candidate
blocked           cannot proceed until named condition is met
open_next_work    known next work, not a blocker to current scout validity
```

## 5. Current Holodeck And Engine Receipts

Basic Holodeck-QIT-FEP scout:

```text
system_v5/ops/formal_scouts/sim_holodeck_qit_fep_predictive_world_model_probe.py
system_v5/ops/formal_scouts/results/holodeck_qit_fep_predictive_world_model_probe_results.json
```

Flux-guided QIT engine scout:

```text
system_v5/ops/formal_scouts/sim_flux_qit_engine_holodeck_runtime_probe.py
system_v5/ops/formal_scouts/results/flux_qit_engine_holodeck_runtime_probe_results.json
```

These were written as formal-scout anchors during the contaminated expansion
window. Their prior `all_pass` / `blockers = []` wording is stale until clean
independent reruns rebuild the cited receipts.

## 6. System-Level Build Order

Use this order for new research lines:

```text
1. language cleanup and authority boundary
2. finite carrier choice
3. micro operation/tool proof
4. single-fixture formal scout
5. matched controls
6. multi-seed/multi-topology/multi-carrier grid
7. coupling/integration scout
8. proof target extraction
9. admission or graveyard update
```

Do not skip from step 2 to step 8.

## 7. Enforcement Examples

F01 enforcement:

```text
finite dimension
finite token registry
finite path count
capacity overflow control
fresh-rerun timeout
```

N01 enforcement:

```text
forward vs reversed order
commuting control
token precedence swap
left/right action gap
classical baseline
```

No primitive equality enforcement:

```text
probe-family indistinguishability
basis/gauge controls
same-entropy but distinguishable states
```

No primitive probability enforcement:

```text
probability only appears as Tr(E rho) under named effect E
classical distribution baseline must be a control, not the main object
```

## 8. Machine-Readable Companion

The companion JSON is:

```text
system_v5/docs/system_levels_20260523/machine_readable/system_level_registry_20260523.json
```

That file is meant for tools and agents. This file is the human-readable
runtime explanation.
