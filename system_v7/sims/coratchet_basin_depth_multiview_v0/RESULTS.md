# Installed Qubit-Channel Contraction Results

Classification: `scratch_diagnostic`
Promotion allowed: `false`
Formal admission allowed: `false`

Claim-audit status: `semantic fabrication found`; nominal numeric values remain
mechanically reproducible.

## Strongest Result

Both independent runtimes find a strict affine contraction of the Bloch ball:

| installed cycle | largest Bloch singular value | spectral contraction gap |
|---|---:|---:|
| Type1 left | 0.3988799053 | 0.6420135561 |
| Type2 right | 0.3406122483 | 0.6731681786 |

Because each largest Bloch singular value is below one, each complete installed
cycle is a global trace-distance contraction on the qubit Bloch ball. It has a
unique full-rank fixed point, and the whole Bloch ball is its basin. This is a
real attracting fixed point of the explicit map, not a clustered endpoint or a
label-defined basin.

Julia and JAX agree on the affine matrices and offsets to below `9e-16`, and on
the fixed density matrices to below `5e-16`.

## Why This Is Not A Ratchet Basin Result

The contraction is not distinctive:

- the native Type1 contraction gap spans ranks `17..32` of 33 after ties, with
  a `27.3%` midrank percentile;
- the native Type2 gap spans ranks `3..18` of 33 after ties, with a `69.7%`
  midrank percentile, below the preregistered `95%` boundary;
- both native gaps also fail the matched random dissipative-channel control;
- the current four-count and free-length results remain red.

The installed cycle therefore does not show that the Ratchet selected this
order, selected four substages, or produced special basin geometry. Dissipation
was installed in every terrain map, and generic dissipative cycles also
contract. The attraction is principally a property of that construction.

## Preregistered Verdict

Both lanes emit `LOCAL_OR_FRAGILE_INSTALLED_BASIN_ONLY` because the genericity
gate fails and the overly strict Bures covariance check is numerically fragile.
The covariance defect is confined to Bures values near zero; state trajectories,
spectra, trace distance, and relative entropy remain covariant near machine
precision. It is not evidence for or against a physical basin.

The independent post-run interpretation is stricter and clearer:

```text
INSTALLED_GLOBAL_ATTRACTING_FIXED_POINTS_GENERIC_ORDER_NOT_SELECTED
```

This label is descriptive only. It is not a passed Ratchet verdict. See
`FABRICATION_AUDIT.md` for the full claim audit.

## Readout Perspectives

- **Liouville spectrum:** unique fixed eigenoperator and transverse decay.
- **Bloch geometry:** global affine contraction with three singular directions.
- **Trace distance:** every pair of states contracts each full cycle.
- **Umegaki relative entropy:** decreases stroboscopically toward the fixed
  point, as data processing predicts for a fixed-point-preserving CPTP map.
- **Bures distance:** contracts numerically, with near-zero cancellation making
  the `1e-9` covariance threshold too brittle.
- **Schedule atlas:** the fixed point and contraction depth move with channel
  order; the native order is not a shared outlier across the two types.
- **Parameter atlas:** the global attracting fixed points survive the registered
  `0.9`, `1.0`, and `1.1` multipliers.

## Invalidated Or Nongating Evidence

- The same-channel schedule atlas is scientifically important but was not a
  preregistered gating null.
- The JAX and Julia random-channel nulls are not the same null family.
- Data-processing and unitary covariance checks are theorem-level consistency
  checks, not new evidence for basin depth.
- The two runtimes replicate one installed mathematical model; they are not two
  independent physical models.
- The name `coratchet_basin_depth_multiview_v0` is historical and overclaims
  what the artifact measures.

## Next Depth

The next nonredundant layer is a finite rational Bloch-lattice transition graph
over schedule lengths `2..8`, multiple lattice resolutions, and alternate
projection tie-breaks. That lane can expose recurrent classes, separatrices,
may/must basins, leakage, metastability, and quotient lumpability. The current
continuous affine cycles have whole-carrier basins, so they have mixing depth
but no nontrivial internal basin boundary to discover.
