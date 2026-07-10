# Foundation Repository Research Status

Date: 2026-07-09

## Verdict

External repository research produced five distinct load-bearing tool roles,
not a pile of interchangeable packages:

1. PySINDy for bounded continuous affine-generator identification.
2. PyKoopman `Identity + EDMD` for bounded finite affine-map identification.
3. PyDMD and deeptime for independent spectral/kinetic recognition.
4. ALCO/GAP for exact J3(O) algebra-oracle parity.
5. QICS and Physlib for numerical and formal associative entropy/DPI oracles.

All source checkouts are under `/Users/joshuaeisenhart/GitHub`. Isolated
runtimes are under `/Users/joshuaeisenhart/.local/share/codex-ratchet`.
The canonical sim-stack was not downgraded or mutated for ALCO, deeptime,
QICS, or Physlib.

## Exact Validations

| Tool | Pin | Validation | Current role |
|---|---|---|---|
| PySINDy | v2.1.0 / `1edf3126...` | six selected upstream tests; bounded affine capability green | continuous generator instrument |
| PyKoopman | v1.2.1 / `61d24f76...` | five selected EDMD tests; full distribution quarantined | explicit-affine `Identity + EDMD` only |
| PyDMD | 2025.8.1 | independent clean/control discriminator lane green | spectral recognizer |
| deeptime | v0.4.5 / `79837fdc...` | isolated VAMP lane green | independent kinetic recognizer |
| ALCO | v1.1.2 / `e10ec05a...` | upstream 0 failures over 6 files; local exact oracle 23/23 | J3(O) algebra oracle |
| QICS | v1.1.3 / `be18e5ef...` | complete upstream suite 22/22; local fixed-input oracle 11/11 with byte-identical rerun | associative relative-entropy/DPI numerical oracle |
| Physlib | `a1962508...` | `QuantumInfo.Entropy.DPI` build success, 8617 jobs, zero source `sorry`/`admit` hits | formal associative DPI reference |

## Scientific Boundary

The tools improve independence and exactness, but they do not prove the engine
architecture. The four operators and searched cycles remain input candidates.
Type 1 survives the current finite learning/sweep packet; Type 2 does not.
PyDMD/deeptime can recognize the two supplied Type-2 trajectory classes but do
not select truth.

The QICS packet performs nine optimal solves, agrees with direct spectral
Umegaki relative entropy to `8.17e-10`, preserves six pinching/depolarizing
contractions, and rejects six non-CPTP controls. This is bounded associative
matrix evidence only.

ALCO has the exceptional carrier but no entropy or DPI. QICS and Physlib have
associative entropy/DPI machinery but no exceptional J3(O) composite. The
missing bridge is therefore explicit: exceptional spectral functional
calculus, entropy, Jordan-positive maps, and a bounded DPI with composition
limits stated rather than borrowed.

No repository in this audit earns Axis0, a canonical engine, perception,
object formation, MMM/ontology authority, mesh projection, or physics.
