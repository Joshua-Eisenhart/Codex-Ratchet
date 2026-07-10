# Results

**Status:** `passes local rerun`
**Classification:** `scratch_diagnostic`
**Promotion:** blocked

The instrument and its independent mechanical validator are green.

Leviathan FlowMind regenerated both tool receipts, then reran the instrument,
validator, contract lint, and tests as a six-node deterministic gate graph.
Receipt: `rcpt-11e35733d5b600cf`, content hash
`315ab19729f84e91dfef8aad1112284c16254ef8f27f15829f631c2975601119`.

The separate active constraint-core harness also reran green at `123/0/0`
(report SHA-256
`5e724476efbfada289bd8bd275f24e09b18196cde852edd6b4d99ef1c3f906bc`).
Its regenerated evidence envelope has formation loss `43.546185436758485`, so
the broad green is not perception or object-success evidence.

## Measured

- 16 source macro slots parsed as 16 unique terrain/sign contexts.
- Two conditional product-cycle orientations evaluated separately.
- 64 beat maps per orientation, 128 fitted maps only because two candidate
  orientations were compared.
- Minimum beat and four-beat rollout held-out R2: `1.0`.
- Maximum beat RMSE: `1.2908363407180531e-15`.
- Maximum four-beat rollout RMSE: `1.729546854431812e-15`.
- Held-out 16-way macro-map re-identification: `16/16` for both orientations.
- All `128/128` beat-removal controls changed the endpoint.
- All `128/128` beat-duplication controls changed the endpoint.
- All 32 slot/orientation rows passed shared-sign, reversal, wrong-sign,
  terrain-erasure, operator-erasure, and all-permutation controls.
- Identity/identity boundary: all 24 orders agree exactly.
- Post-run identity-confound audit, reproduced in both orientations: full maps
  form `16` classes; operator erasure leaves `8`; terrain erasure leaves `4`;
  erasing both leaves `1`.

Minimum observed effects versus the full exact transition:

| Control | Minimum mean endpoint gap |
|---|---:|
| reverse candidate orientation | `7.83229600842517e-4` |
| wrong Axis-6 composition order | `4.715166293390853e-4` |
| remove one beat | `3.023679164264091e-3` |
| duplicate one beat | `8.784955781810345e-4` |
| erase terrain | `1.4938323770449374e-1` |
| erase operator | `5.117663092079e-3` |

The largest accepted fit error was about `1.73e-15`, so these controls are not
numerical aliases of the learned map.

PySINDy recovered all eight exact affine terrain generators with minimum
held-out derivative R2 `1.0` and maximum time-one flow RMSE
`3.0438151539315467e-16`. Its shuffled-derivative control had maximum R2
`0.025440843229064886`.

## Interpretation

Under this finite one-qubit house-map parameterization, a concrete 16 x 4
schedule is executable, externally recoverable, and locally sensitive to every
tested beat, sign, terrain, operator, and order intervention. The two engine
sheets also have different aggregate control profiles, but this packet does
not interpret those numeric profiles as personalities or distinct scientific
methods.

The result does not establish emergence. The four operator cells, their two
cycle orientations, the 16 source slots, canonical-first rotation, and the
house maps are inputs. Exact derivatives are also a stronger observation
surface than the trajectory-only PySINDy arbiter that previously found one
poorly identifiable projective terrain.

The `16 -> 8 -> 4 -> 1` ablation was added after the first green run to test
whether terrain/sign alone carried the flattering `16/16` result. It is useful
follow-up evidence, but it is post-hoc and should be independently repeated in
the next preregistered packet.

The next decisive experiment remains independent geometry-first and
entropy-first survivor ratchets over a declared superset. Only their
intersection may choose the stage interior; this packet can then test the
emitted sequence without receiving a hard-coded count of four.
