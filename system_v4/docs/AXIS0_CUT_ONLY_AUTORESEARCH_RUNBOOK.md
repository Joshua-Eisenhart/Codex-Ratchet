# Axis 0 Cut-Only Autoresearch Runbook

**Date:** 2026-03-29
**Status:** SUPERSEDED. Older cut-only launch surface retained for audit context only. Do not use as the current cut owner runbook.
**Superseded by:** [AXIS0_CUT_TAXONOMY.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_TAXONOMY.md), [AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_HISTORY_WINDOW_CUT_CONTRACT.md), and [AXIS0_TYPED_SHELL_CUT_CONTRACT.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_TYPED_SHELL_CUT_CONTRACT.md).
**Purpose:** Reusable launch surface for bounded `codex-autoresearch` rounds that target only the `A|B` cut question for `Axis 0`.

---

## Owner Surfaces

- [AXIS0_ACTIVE_PACKET_INDEX.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_ACTIVE_PACKET_INDEX.md) is the compact entrypoint for the current active `Axis 0` packet stack; use it before this superseded runbook.

- [AXIS0_MANIFOLD_BRIDGE_OPTIONS.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md)
- [AXIS0_CUT_CANDIDATE_BASIN.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/AXIS0_CUT_CANDIDATE_BASIN.md)
- [PROTO_RATCHET_FOUR_SURFACES.md](/Users/joshuaeisenhart/Desktop/Codex%20Ratchet/system_v4/docs/PROTO_RATCHET_FOUR_SURFACES.md)

---

## Hard Scope

- Freeze geometry.
- Freeze the current kernel basin.
- Freeze the current bridge verdicts.
- Work only on exact typed `A|B` cut candidates.
- Output only doc updates under `system_v4/docs/`.

Do not:

- redefine `Xi`
- redefine the geometry ladder
- promote runtime `GA0` from proxy to kernel
- promote raw `L|R` from control to doctrine
- revive the killed shell-strata pointwise implementation

---

## Launch Prompt

```text
$codex-autoresearch
Mode: plan
Run a bounded proto-ratchet round only on the exact A|B cut question for Axis 0. Use system_v4/docs/AXIS0_MANIFOLD_BRIDGE_OPTIONS.md as the bridge owner packet and system_v4/docs/AXIS0_CUT_CANDIDATE_BASIN.md as the cut owner packet. Freeze geometry, freeze the current kernel basin, and freeze the current bridge verdicts. Use bounded parallel lanes for: cut candidate enumeration, kill criteria, bridge compatibility, source-tight QIT formulations, and anti-smoothing audit. Do not redefine Xi. Do not collapse cut, bridge, and kernel into one object. Do not promote raw L|R from control to doctrine. Output only updates to docs in system_v4/docs/.
```

---

## Suggested Lane Split

1. exact typed history-window cuts
2. exact typed shell/interior-boundary cuts
3. exact typed point-reference cuts
4. kill-criteria and acceptance-test audit
5. anti-smoothing audit

---

## Success Condition

The round succeeds if it produces:

- a tighter typed cut table
- explicit keep/open/kill status for each cut family
- bridge-to-cut compatibility notes
- no drift back into geometry or kernel redesign
