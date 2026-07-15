# Tolerance-to-Equivalence Ratchet Rung v0

This packet is a mechanically tested finite tolerance-to-equivalence surrogate.
The deeper semantic audit demotes its former scratch-tooth wording: it does not
earn a Ratchet tooth. Its current state is OPEN with
HOLD_DESIGNED_SURROGATE. See SEMANTIC_AUDIT.md and the v1 semantic-forcing
preregistration.

## Packet map

- `spec.json` — frozen mathematical and code-gate contract.
- `results/final_report.json` — machine-readable G0-G10 decision and claim ceiling.
- `GATE_STATUS.md` — earned greens and preserved launch reds.
- `SIM_STACK_INVENTORY.md` — complete 139-tool, 29-edge, connected-repo, and working-code inventory.
- `SKILL_PROVIDER_STATUS.md` — Claude/Fable, skill parity, NVIDIA, and xAI control-plane status.
- `V8_PRELAUNCH_PLAN.md` — G11-G13 plan derived from the adversarial premortem.

## Definition

The state starts and remains OPEN. G0-G9 measure finite mechanics; G10 cannot
override a red semantic-forcing gate.

1. **R0 — tolerance substrate.** On finite labeled addresses `X_n`, enumerate every reflexive symmetric relation `T`. Transitivity is measured and may fail; `T` is not identity.
2. **R1 — earned equivalence.** Compute the least equivalence containing `T`, here the connected-component closure. A three-address chain `0~1~2` with `0!~2` is the frozen witness that tolerance need not already be transitive.
3. **R2 — bounded tooth.** For a frozen demand set `D`, compute coface loss `L_D(pi)` as the number of demanded pairs collapsed by presentation `pi`, and drive `g_D(pi->rho)=L_D(pi)-L_D(rho)`. A tooth can be authorized only when `g_D>0`; `g_D<=0` is `HOLD`.
4. **MSS — plural selection.** Enumerate admissible equivalences and return the complete nondominated antichain under two declared axes: added relation pairs and quotient fragmentation. No hidden scalarization or single narrative winner is allowed.

For the positive fixture, the universal initial presentation has loss `1`, the two-component closure has loss `0`, and the drive is `1`. Reverse, null, universal-proposal, demand-scramble, and flat-gradient controls all HOLD. The MSS antichain contains both the two-class zero-distortion presentation and the one-class zero-fragmentation presentation.

## Independent engine roles

| Lane | Load-bearing work in this packet | Exact ceiling |
|---|---|---|
| Julia + Graphs.jl | Independent exact `n=1..5` census and connected-component closure | Finite scratch fixture only |
| JAX x64 | Batched exhaustive census and fixed-point closure using `vmap` and `lax` | Finite scratch fixture only |
| PyTorch + PyG | Independent tensor census and `MessagePassing` reachability closure | Finite scratch fixture only |
| z3 | Free-Boolean relation SAT/UNSAT encoding | Four bounded queries only |
| cvc5 | Independent free-Boolean encoding of the same four queries | Four bounded queries only |
| Leviathan | Deterministic `lev.validate` orchestration and receipt replay | Process gate only; not scientific canon |

The engine lanes do not read one another's result files. NumPy is not on the claim path. No model verdict, training run, council vote, or prose judgment can open a gate.

## Exact finite census

| `n` | Reflexive symmetric tolerances | Equivalences | Nontransitive tolerances |
|---:|---:|---:|---:|
| 1 | 1 | 1 | 0 |
| 2 | 2 | 2 | 0 |
| 3 | 8 | 5 | 3 |
| 4 | 64 | 15 | 49 |
| 5 | 1024 | 52 | 972 |

All three engines independently reproduced this census and the two frozen closures with zero divergence.

## Code-gate sequence

- G0 freezes and validates the object card and preregistration before builders.
- G1 checks the exact finite census.
- G2 requires Julia/JAX/PyTorch closure parity.
- G3 requires z3 and cvc5 to pass SAT, implication-UNSAT, minimality-UNSAT, and dropped-transitivity SAT control queries.
- G4 reconstructs the coface drive from frozen demand edges.
- G5 requires exactly one positive tooth and all five HOLD controls.
- G6 requires the explicit plural MSS antichain.
- G7 proves engine-lane closure from peer result files.
- G8 binds sources, runtimes, classification, and claim ceiling.
- G9 requires coherent-envelope mutations to be rejected.
- G10 may replay deterministic validators, but cannot authorize v0 while the
  semantic-forcing gate is red.

The current result is recorded in results/final_report.json.
mechanical_code_gates_pass is true, semantic_forcing_pass is false, and
all_code_gates_pass is false. No Ratchet state advances.

## Run

From the isolated worktree root, with the documented Python runtime and Julia carrier available:

```sh
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -B \
  system_v7/sims/tolerance_to_equivalence_ratchet_rung_v0/run_pipeline.py
```

The no-model Lev replay is defined in `lev/flow.yaml`; its pinned executable identity and resulting receipt are recorded in `results/lev_replay_receipt.json`.

## What must happen before an official launch

Do not finish this fixture into a tooth. Build the sealed v1 preregistration,
then add its closed Julia/JAX/PyTorch lanes, post-seal held-out estate, semantic
mutations, and append-only pawl. Lev proof work remains necessary process
infrastructure but is not a substitute for those semantic gates.
