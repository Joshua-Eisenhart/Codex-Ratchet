# CODEX_ONLY_CAPSULE_EXECUTION_TOPOLOGY v1

## Objective
Phase out local LLM execution and use Codex-thread capsules only for A2/A1.

Deterministic runtime remains local:
- A0
- B
- SIM

## Topology
- Thread A2: meta-governance and proposal shaping
- Thread A1: structured strategy generation
- Local runtime: deterministic compile/evaluate/simulate loop

All cross-thread/runtime exchange occurs via ZIP capsules only.

## Flow
1. A0 emits `A0_TO_A1_SAVE_ZIP`
2. A1 consumes save ZIP and emits `A1_TO_A0_STRATEGY_ZIP`
3. A0 compiles to `A0_TO_B_EXPORT_BATCH_ZIP`
4. B emits `B_TO_A0_STATE_UPDATE_ZIP`
5. SIM emits `SIM_TO_A0_SIM_RESULT_ZIP`
6. A0 emits updated save ZIP upward
7. A2 consumes A1/A0 summaries and emits `A2_TO_A1_PROPOSAL_ZIP`

## Non-negotiable constraints
- No shared memory between threads.
- No side channels outside ZIP artifacts.
- A1 must emit canonical schema only.
- A2 must emit proposal ZIP only.
- A0 remains deterministic hinge.

## Migration steps
1. Freeze local-LLM adapter as non-authoritative.
2. Replace local-LLM invocation with Codex-thread ZIP handoff wrapper.
3. Keep validator gates unchanged.
4. Require replay parity before decommissioning local adapter paths.
