Bottom line: **BY_CONSTRUCTION**, not `GENUINE`. The packet passes its validator/test surfaces, and I recomputed the emitted routing values from source, but the central "chiral information routing" witness is an endpoint-arrival indicator derived directly from `signed_index`, not a mutual-information/transfer computation over a bit distribution and not a fair strongest Szilard comparison. Claim ceiling: **deterministic open-chain signed-index endpoint-routing toy only**; cite it only with the by-construction caveat.

## Verdict

- Verdict: **BY_CONSTRUCTION**
- Claim ceiling: `capability_discriminator_only`, narrowed by audit to `by_construction_signed_index_endpoint_routing_toy`
- Status ladder: validator/test surfaces **pass local rerun**; the capability claim is not canonical, not admitted, and not a genuine Szilard-vs-QIT discriminator.
- Freshness tier: `TIER-2` results/source available. No prior `ecd02` audit verdict was read because none existed; parent QCA v3 snippets were visible only as authority context.
- Write scope: read-only audit except this file, `system_v6/sims/ecd02_chiral_information_routing_v0/audit_verdict.md`.

## Fresh Checks

Fresh commands run with the Makefile interpreter `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`:

| Check | Result |
|---|---|
| `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/ecd02_chiral_information_routing_v0/results/ecd02_chiral_information_routing_v0_envelope_results.json` | exit 0, `ok: true` |
| packet-local `validate(payload)` imported directly to avoid live write to `*_validator_results.json` | exit 0, `errors: []` |
| `python -m pytest -q system_v6/sims/ecd02_chiral_information_routing_v0/tests/test_ecd02_chiral_information_routing_v0.py` | exit 0, `5 passed` |

The validator pass is real, but it checks the packet's declared deterministic contract. It does not prove that endpoint rows are independent information-flow measurements.

## Recomputed Numbers

I recomputed the load-bearing values from source rather than trusting the result JSON:

| Quantity | Fresh recompute |
|---|---:|
| QCA v3 consumed `R` index | `+1` |
| QCA v3 consumed `L` index | `-1` |
| QCA v3 consumed zero/index0 | `0` |
| forced `R` left falsifier index | `-1` |
| `R` left-to-right arrival | `1.0` at step `5` |
| `R` right-to-left arrival | `0.0`, no arrival |
| `R` asymmetry | `1.0` |
| `L` left-to-right arrival | `0.0`, no arrival |
| `L` right-to-left arrival | `1.0` at step `5` |
| `L` asymmetry | `-1.0` |
| Szilard/index0 asymmetry | `0.0` |
| mirror flip | `true` |

Source citation: `route_position()` is `start + signed_index * step`, and `mutual_information_bits()` returns `1.0` when the routed position equals an endpoint, else `0.0` (`ecd02_chiral_information_routing_v0_common.py:100-113`). The asymmetry rows then subtract these endpoint-arrival indicators (`ecd02_chiral_information_routing_v0_common.py:145-158`).

## Findings

### F1 - The routing statistic is definitional

The advertised routing witness is not computed from a joint distribution, transfer entropy, channel table, or measurement-feedback dynamics. It is computed from a deterministic position update using the already-consumed `signed_index`, and the endpoint "MI" is an indicator bit for position equality.

That means the positive result is reachable and reproducible, but it is not independent of the rule used to define movement. This is **definitional circularity** plus **rule-table readback**.

### F2 - The Szilard baseline is not strongest fair form

The baseline is implemented as `signed_index = 0` with `passes_capability = False` and a prose failure reason (`ecd02_chiral_information_routing_v0_common.py:191-196`). It does not instantiate the strongest same-chain Szilard measurement-memory-feedback loop, nor a two-bit entropy/readout test from the alt-view prediction.

So the packet shows "zero-index no motion cannot route under this toy," not "Szilard cannot route chirally under its strongest fair finite form."

### F3 - The mirror flip is real but forced by symmetry

The mirror row flips because the packet changes `signed_index` from `+1` to `-1`. That is a valid sign-swap control over the toy transport rule, but it is not an independent chirality witness beyond the same signed-index mechanism.

This is the sixth species requested by the audit card: **structure-by-symmetry**. The mirror exists because the construction is symmetric under sign reversal.

### F4 - No direct rule-id leak, but full signed-index leak

I checked a non-rule-id predictor using only `signed_index + injection_end`; it recovered all eight emitted arrivals with accuracy `1.0`. That is not a row-name identity leak, but it is enough to demote the claim because the reported endpoint-routing statistic is fully recoverable from the finite index field it is supposed to test.

### F5 - Julia leg is hardcoded relative to Python core

The Julia lane emits `R_routing_asymmetry = 1.0`, `L_routing_asymmetry = -1.0`, and `szilard_routing_asymmetry = 0.0` directly in `build_result()` (`ecd02_chiral_information_routing_v0_julia.jl:86-98`). It supplies an SMT consistency check over fixed integer rows, not an independent Julia recomputation of the endpoint routing process.

The cross-backend agreement is therefore not strong evidence for the capability. JAX/PyTorch share the Python core route, while Julia confirms the integer contract.

## Circularity Species Check

| Species | Audit result |
|---|---|
| `frozen-factor echo` | Not the primary defect as a complementary-factor count, but the packet does project a frozen source index into the moving statistic. Carried under F1/F4 rather than as a separate kill. |
| `definitional circularity` | **Present.** `route_position = start + signed_index * step` forces the endpoint result for this open chain. |
| `rule-table readback` | **Present.** The QCA v3 `signed_log2_index` is consumed and read back as routing direction/asymmetry. |
| `post-hoc statistic` | Not found. No statistical target set or p-value is used. |
| `shift-relabeling` | Not repeated as the old QCA v2 failure inside this packet, but the packet relies on the parent QCA v3 fixture for that cure. It does not add a fresh chirality-erased operator row. |
| `structure-by-symmetry` | **Present.** The mirror direction flips because the signed index is negated. |

## Relation To Alt-View Predictions

The registry/alt-view convergence was real as a reason to build a finite test, but this packet did not run the strongest finite tests those views described.

- ECD registry finite shape partially run: L/R opposite signed-index rows and index0 control were exercised.
- ECD registry missing teeth: no fresh chirality-erased row beyond index0/forced-left sign use; no label-free directional invariant independent of the signed index.
- Grok Option 2 not run: no two-bit joint state, no entropy reduction/increase comparison, no final projective readout entropy test.
- Gemini Q1 rank-1 not run: no equal-temperature bath/current setup and no persistent direction-dependent flux.
- The packet therefore does not confirm the alt-view "chiral information diode" prediction; it only implements a by-construction endpoint-routing proxy inspired by it.

## Citation Rule

Any future citation must say:

> `ecd02_chiral_information_routing_v0` passes local validator/test reruns as a deterministic open-chain signed-index endpoint-routing toy, but the fresh audit verdict is `BY_CONSTRUCTION`; it must not be cited as computed mutual information, transfer flow, a fair Szilard impossibility result, an admitted chiral information diode, finite-ring QCA admission, all-cells QCA admission, physics chirality, or QIT-engine capability admission.

Use the source/result paths together when citing:

- Source: `system_v6/sims/ecd02_chiral_information_routing_v0/ecd02_chiral_information_routing_v0_common.py`
- Envelope: `system_v6/sims/ecd02_chiral_information_routing_v0/results/ecd02_chiral_information_routing_v0_envelope_results.json`
- This audit: `system_v6/sims/ecd02_chiral_information_routing_v0/audit_verdict.md`
