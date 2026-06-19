# Engine-independence relabel — honest INDEPENDENT-RECOMPUTE vs VERIFY-PAYLOAD lanes (2026-06-13)

```yaml
receipt_kind: framing_relabel_fix + on-disk correction of the systemic receipt's paraphrase
severity: framing, not math — the relabel changes the independence LABEL going forward; no math, no mass-regenerate
status: builder edit applied + py_compile-checked + shape-tested + shared-validator re-accepts; committed envelopes NOT regenerated
write_target: scripts/build_three_engine_envelope.py (edited) + this receipt
parent: system_v6/receipts/engine_independence_overclaim_systemic_20260612.md
```

## Bottom line

The systemic receipt's prescribed single relabel point (`scripts/build_three_engine_envelope.py`) is the right file, but the field it named (`engine_consensus.independent=true`) does **not** flow through that builder, and is **not present on disk** in that literal form. The honest fix that the builder *can* own is the `divergence`/`max_divergence` block, which it copies through verbatim. The edit adds a computed, honest `divergence.engine_independence` annotation driven by a new caller-declared `lane_evidence` map, plus a guard that rejects the disease at the one point the builder can see it. Framing is fixed going forward; the 43 committed envelopes are not regenerated.

## On-disk correction to the systemic receipt (re-derived from disk, 2026-06-13)

The systemic receipt quoted the smoking gun as `"engine_consensus": {"independent": true}` + `"max_divergence": 0.0`. Verified against disk:

- **`engine_consensus.independent=true` is NOT on disk anywhere.** Zero committed envelopes carry it. The `engine_consensus` blocks that exist (e.g. `gcm_constraint_carve_2q_v0`) use `*_agreement` booleans (`survivor_count_agreement`, etc.), not an `independent` field. The receipt's quote is a paraphrase of the *meaning*, not a literal field.
- The only `"independent": true` strings in carve envelopes (`gcm_constraint_carve_v0/_v1/_2q_v0`) sit at `/existence_tests/independent` — a **domain** field (did the existence test find an independent survivor set), unrelated to engine independence. Do not relabel that one; it is correct.
- `"max_divergence": 0.0` IS real and IS the tautological field: it lives at `/divergence/max_divergence`. Across the estate, **182 committed envelopes carry `divergence.max_divergence`; 165 of them are exactly `0.0`** — consistent with the systemic receipt's "guaranteed-by-construction" finding for shared-payload verify lanes.

So the receipt's *math* (shared-core verify lanes cannot diverge -> `max_divergence ~ 0` is structural) holds; its *field name* for the relabel target was a paraphrase. This receipt records the real target: `divergence`.

## Where the fields actually live (structural map)

- The central builder `build_three_engine_envelope.build_envelope()` emits `engines`, `engine_contract`, `crossover_proofs`, and `divergence` (the last copied through verbatim from the caller). It **never** emitted `engine_consensus` at all.
- `engine_consensus` is built per-packet by each sim's `write_envelope_spec.py` (its own local `engine_consensus()` fn) and injected into the envelope via `build_envelope(..., extra_fields={"engine_consensus": ...})`, where it is `copy.deepcopy`'d through opaquely.
- Therefore a "clean edit relabeling `engine_consensus.independent`" in the central builder is **not literally possible** — that object is not visible to the builder as structured data. The builder *can* honestly own `divergence`/`max_divergence`, which is the actual tautological-zero field.

## The edit (applied to scripts/build_three_engine_envelope.py)

New optional kwarg `lane_evidence: Mapping[str, str] | None` on `build_envelope`. Each lane maps to one of:

- `independent_recompute` — lane recomputes the core natively (real second opinion)
- `verify_payload` — lane consumes one shared core-compute payload and only verifies it
- `unspecified` — **conservative default**: caller did not declare; builder does NOT grant an independence claim by silence

The builder then attaches `divergence.lane_evidence` (the normalized map) and `divergence.engine_independence`:

```
engine_independence = {
  independent_recompute_lanes: [...],
  verify_payload_lanes: [...],
  unspecified_lanes: [...],
  independent_signal: <true iff >=2 independent_recompute lanes>,
  max_divergence_meaning: <one of four honest labels, see below>,
  note: "...shared core-compute...cannot diverge...structural..."
}
```

`max_divergence_meaning` resolves to:
- any unspecified lane -> `"independence-unverified ... treat max_divergence as a SHAPE/agreement check, not an independence signal."`
- `>=2` independent -> `"... a genuine cross-engine independence signal."`
- exactly 1 independent (the ~43 reality: Julia recomputes, JAX+PyTorch verify) -> `"... structural (shared payload), not an independence signal — the single independent lane is the only second opinion."`
- 0 independent -> `"structural (shared payload), not an independence signal ... tautologically ~0."`

Guard `_guard_extra_fields_independence`: if a caller injects `extra_fields.engine_consensus.independent=true` while the declared lane evidence does NOT support an independence signal (`<2` independent-recompute lanes), `build_envelope` raises `ValueError`. This catches the receipt's disease at the single point the builder can see it.

The builder itself **never** emits `engine_consensus.independent=true`. `max_divergence` math is untouched (still copied through verbatim).

## Diff proposal (the applied patch, summarized)

- Added module constants `LANE_EVIDENCE_INDEPENDENT / _VERIFY / _UNSPECIFIED` + `_LANE_EVIDENCE_KINDS`.
- Added `_normalize_lane_evidence()`, `_engine_independence_annotation()`, `_guard_extra_fields_independence()`.
- Added `lane_evidence` kwarg to `build_envelope` (between `generated_at` and `extra_fields`).
- Replaced inline `"divergence": copy.deepcopy(dict(divergence))` with a `divergence_record` that carries the new `lane_evidence` + `engine_independence` annotation.
- `git diff --stat`: `scripts/build_three_engine_envelope.py | 132 +++..-`, 131 insertions / 1 deletion.

## Verification (this session)

- `python3 -m py_compile scripts/build_three_engine_envelope.py` -> `PY_COMPILE OK`.
- Shape test (using the real committed `gcm_constraint_carve_2q_v0` spec so lane source/result files hash):
  - (a) default / all `unspecified` -> `independent_signal=False`, label = `independence-unverified`; `max_divergence` unchanged at `0.0`.
  - (b) `julia=independent_recompute, jax/pytorch=verify_payload` (the ~43 reality) -> `independent_signal=False`, `independent_recompute_lanes=['julia']`, label contains `structural (shared payload)`.
  - (c) inject `extra_fields.engine_consensus.independent=true` with `<2` independent lanes -> `ValueError` raised (guard fires).
  - (d) `>=2` independent lanes -> `independent_signal=True`, genuine-signal label; injected consensus passthrough allowed.
- Shared validator `scripts/validate_three_engine_sim_result.py validate(env, require_pytorch=True)` -> `NONE` errors -> `ok:True`. The added `divergence` sub-keys are accepted; the validator reads `divergence` permissively (requires `engine_values`, `julia_authoritative`, presence of `max_divergence`; does not reject extra keys).

## Affected-packet handling

- **Framing fixed going forward only.** Any envelope rebuilt through `build_envelope` from now on carries the honest annotation; a caller that wants `engine_consensus.independent=true` must declare `>=2` independent-recompute lanes or the build fails.
- **The committed envelopes are NOT regenerated** (sha-cascade / registry-drift lesson, per the parent receipt). The ~43 core-shared packets keep their existing `divergence.max_divergence: 0.0` until their next legitimate rebuild; the honest framing attaches then. This receipt + the parent systemic receipt document the affected set in the interim.
- **No math changed.** Survivor/class/cut counts and `max_divergence` values are byte-identical; only the LABEL/annotation is added.

## Open / not done here

- Per-packet `lane_evidence` declarations are not back-filled into the 43 `write_envelope_spec.py` callers — they will pick the conservative `unspecified` default (honest "independence-unverified") until each is updated to declare which lane independently recomputes. That is per-packet build work, out of scope for this single-point builder edit.
- The systemic receipt's per-packet nuances (decorative JAX/PyTorch observables on `gcm_runtime_flux_3q_v1`, the `gcm_2q_freeze_and_cut_v0` copied count fields, the `gcm_geometry_attach_2q_v1` decorative `sympy_guard`) are NOT addressed by the builder edit; they are per-packet, named in the parent receipt, carried forward.
