# AUDIT VERDICT - axis0_cosurvivor_heavy_v0

Bottom line: **PASS_WITH_CAVEATS at scratch_diagnostic ceiling.** The heavy exclusion survives audit. CP.11 and CP.14 conform to Supplement 1's pinned formulas, recompute as the same accepted light objects, pass the boundary re-check, then fail the heavy Axis-0 family teeth by one-step and multi-step stability-class mismatch against the anchor. The family-closing sentence may say: **Axis-0 = the anchor alias class** on the committed 33-cell carrier.

This does **not** mean CP.11 or CP.14 are dead formulas. It means the pinned CP.11 FEP dS/dt readout and pinned CP.14 marginal-entropy readout are computable non-Axis-0 readouts under this carrier and contract. CP.11 is not minted as a co-equal FEP Axis-0 member. CP.14 does not make the marginal-vs-correlation fork both-live inside Axis-0. The FEP reading as its own object remains untouched by this packet.

Freshness tier: **TIER-3 annotation-verify with independent recomputation.** I was exposed to the builder's claimed numbers in the audit prompt and read result surfaces, so this is not blind. The decisive rows below were recomputed from source/carrier during the audit rather than copied from builder prose.

## Contract Checks

- Binding standards: `system_v6/receipts/audit_standards_codex_v1.md`, especially pinning, freshness, builder/audit boundary, and corrected vocabulary.
- Binding formula pins: `system_v6/receipts/axis0_registry_amendment_1_20260612.md`, Supplement 1, commit `34596316d`.
- First heavy format precedent: `c27d3dd39:system_v6/sims/axis0_contender_heavy_v0/`.
- Builder/auditor boundary: no builder-authored `audit_verdict.md` existed before this audit; this file is the only audit write.
- Claim ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Formula Pin Conformance

PASS.

CP.11 implementation:

- Supplement pin: system typed von Neumann entropy of the committed cell state object; rate is one-step difference under the committed generator family; per-cell sign is majority `sign(S_after - S_before)`; no bath terms or new channels.
- Heavy code: `cp11_raw()` computes vN entropy from the cell Bloch vector, computes `after - before` for each outgoing committed generator image, takes signs, and stores the vote sum per cell.
- Result row says `adapter_status=supplement_1_formula_recomputed_on_committed_33_cell_carrier` and matches accepted light vector hash.

CP.14 implementation:

- Supplement pin: single-cell reduced vN entropy with committed-adjacency directed difference using the anchor gradient machinery.
- Heavy code: `cp14_raw()` computes single-cell vN entropy per committed carrier cell and sums `S(dst)-S(src)` over committed edges.
- Result row says `adapter_status=supplement_1_formula_recomputed_on_committed_33_cell_carrier` and matches accepted light vector hash.

No formula drift found. The heavy pass tests the same pinned light objects that `4ef6cf0d8` accepted as light co-survivors pending heavy teeth.

## Recomputed Heavy Teeth

Independent recomputation from `discrete_axis0_field_v0_common.rebuild_committed_carrier()` gave:

| row | hamming vs anchor | boundary re-check | one-step stability | multi-step stability | final |
|---|---:|---|---|---|---|
| A0.CP.11 | 19/33 | pass | mismatch | mismatch | `excluded-by-stability-class-mismatch` |
| A0.CP.14 | 21/33 | pass | mismatch | mismatch | `excluded-by-stability-class-mismatch` |

Sampled cells independently checked for both contenders: `0, 1, 2, 7, 13, 16, 20, 32`.

CP.11 samples:

| cell | anchor raw/sign | CP.11 raw/sign | agrees |
|---:|---|---|---|
| 0 | `-38/97` / -1 | `4.0` / +1 | no |
| 1 | `-12/97` / -1 | `2.0` / +1 | no |
| 2 | `-28/97` / -1 | `4.0` / +1 | no |
| 7 | `29/97` / +1 | `2.0` / +1 | yes |
| 13 | `-31/97` / -1 | `2.0` / +1 | no |
| 16 | `0` / 0 | `-2.0` / -1 | no |
| 20 | `20/97` / +1 | `4.0` / +1 | yes |
| 32 | `-15/97` / -1 | `4.0` / +1 | no |

CP.14 samples:

| cell | anchor raw/sign | CP.14 raw/sign | agrees |
|---:|---|---|---|
| 0 | `-38/97` / -1 | `1.370445655906088` / +1 | no |
| 1 | `-12/97` / -1 | `0.170720164031216` / +1 | no |
| 2 | `-28/97` / -1 | `0.145839613919121` / +1 | no |
| 7 | `29/97` / +1 | `-0.245775366668471` / -1 | no |
| 13 | `-31/97` / -1 | `0.145839613919121` / +1 | no |
| 16 | `0` / 0 | `0.0` / 0 | yes |
| 20 | `20/97` / +1 | `-0.145839613919121` / -1 | no |
| 32 | `-15/97` / -1 | `1.370445655906088` / +1 | no |

Anchor stability was recomputed fresh from the carrier, not read from prior verdict prose:

- Anchor one-step stability: `D_z 32/1`, `Ne_Spiral_R 23/10`, `Ni_Pit_L 28/5`, `Ni_Source_R 29/4`, `R_x 19/14`, `Se_Funnel_L 32/1` as match/differ.
- CP.11 one-step differs: most visibly `R_x 31/2` and `Ne_Spiral_R 29/4`.
- CP.14 one-step differs: most visibly `Ne_Spiral_R 5/28`, plus every listed generator differs from anchor.
- Anchor multi-step aggregate: depth 2 `match=846,differ=342`; depth 3 `match=4531,differ=2597`.
- CP.11 multi-step aggregate: depth 2 `match=1028,differ=160`; depth 3 `match=6025,differ=1103`.
- CP.14 multi-step aggregate: depth 2 `match=675,differ=513`; depth 3 `match=3708,differ=3420`.

The stability method matches the first heavy pass precedent: per-generator `match/differ` comparison of candidate signs under committed generator edges against the freshly recomputed anchor profile. This packet adds depth-2 and depth-3 ordered generator-walk profiles as an extension, not a replacement.

## Controls

PASS.

- Anchor self control returns `alias-of-anchor`.
- Deliberate alias control returns `alias-of-anchor`; this is important because the heavy teeth can return alias when the readout really collapses into the anchor.
- Prior exclusions remain excluded:
  - CP.1: `excluded-by-Hamming-disagreement-from-committed-sign-vector`, hamming 11.
  - CP.2: `excluded-by-source-sink-imbalance`, hamming 25.
  - CP.10: `excluded-by-degree-teeth-wrong-distinction`, hamming 25.
- Boundary re-checks pass for both CP.11 and CP.14; the exclusion is not a boundary failure.
- SMT bindings pass: z3, cvc5, and Julia Z3 negate the computed heavy-row bindings as UNSAT; mutation controls are SAT.

## Panel-9 Consistency

PASS. Panel 9 pre-registered that CP.11 and CP.14 alias under degree-1/linear-gradient-flow structure and come apart under degree >= 3 mixed-sign or boundary-flow-free scrambling.

The actual 33-cell carrier has 198 committed edges, i.e. six outgoing generator edges per cell. The forcing feature observed in this audit is **multi-neighbor mixed-sign structure**. Examples:

- Cell 1: CP.11 one-step entropy votes include `-1, 0, +1`; CP.11 majority sign is +1 while the anchor is -1.
- Cell 7: CP.11 stays +1, but CP.14 directed entropy sum is negative, so CP.14 separates from both CP.11 and the anchor behavior.
- Cell 16: CP.11 is -1 while CP.14 is 0 and the anchor is 0, showing the two pinned entropy readouts are not aliases.
- Cell 20: CP.11 is +1 while CP.14 is -1 under the same six-edge committed carrier.

This matches the panel's multi-neighbor mixed-sign mechanism. The audit did not need to invoke a post-hoc formula change or a boundary-flow-free scrambling story.

## Validators And Commands

Fresh commands run read-only, with bytecode/cache writes disabled:

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/axis0_cosurvivor_heavy_v0/results/axis0_cosurvivor_heavy_v0_envelope_results.json
```

Result: `ok=true`.

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
import importlib.util, json, sys
from pathlib import Path
path=Path('system_v6/sims/axis0_cosurvivor_heavy_v0/validate_axis0_cosurvivor_heavy_v0.py').resolve()
spec=importlib.util.spec_from_file_location('v', path)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
spec.loader.exec_module(mod)
errors, summary = mod.validate_payload()
print(json.dumps({'ok': not errors, 'errors': errors, 'verdicts': mod.verdict_map(summary['payload'])}, indent=2, sort_keys=True))
PY
```

Result: `ok=true`, `errors=[]`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/axis0_cosurvivor_heavy_v0/tests
```

Result: `4 passed`.

## Registry-Row Language

Permitted registry final state:

```text
A0.CP.11: excluded from the Axis-0 family under Supplement-1 pins by axis0_cosurvivor_heavy_v0: boundary re-check passed, but 19/33 cell disagreements plus one-step and multi-step stability-class mismatch against the anchor. CP.11 remains a computable FEP dS/dt readout, not a co-equal Axis-0 member under this carrier.

A0.CP.14: excluded from the Axis-0 family under Supplement-1 pins by axis0_cosurvivor_heavy_v0: boundary re-check passed, but 21/33 cell disagreements plus one-step and multi-step stability-class mismatch against the anchor. CP.14 remains a computable marginal-entropy readout; the marginal-vs-correlation fork is not both-live inside Axis-0 under this carrier.

Axis-0 family status under the committed 33-cell heavy teeth: anchor alias class only. This is scratch-diagnostic family adjudication, not formal/canonical Axis-0 admission or global uniqueness.
```

## Caveats

- This is a scratch diagnostic over the committed 33-cell carrier only.
- The packet is currently untracked in the working tree during audit.
- This audit did not rerun the live builder commands because the user constrained repo writes to this verdict file. Instead it used read-only validator calls and independent source recomputation.
- Full Wizard v4.2 native subagent topology was not run because this host only exposes subagent spawning when the user explicitly authorizes delegation; no subagent counts are claimed.
