# Toolset Expansion Fit-Probe Receipt - 2026-06-10

generated_at: `2026-06-10T20:38:33Z`

status: `complete`

classification: `tool_lego_fit_probe`

promotion_allowed: `false`

Scope: every probe below is a fit probe only. No probe promotes a lego, axis, bridge, or carrier claim.

## Artifacts

- Python probe script: `system_v6/probes/toolset_expansion_20260610_python.py`
- Julia probe script: `system_v6/probes/toolset_expansion_20260610_julia.jl`
- Python results: `system_v6/probes/toolset_expansion_20260610_python_results.json`
- Julia carrier results: `system_v6/probes/toolset_expansion_20260610_julia_carrier_results.json`
- TensorKit results: `system_v6/probes/toolset_expansion_20260610_tensorkit_results.json`
- Nemo+Hecke results: `system_v6/probes/toolset_expansion_20260610_nemo_hecke_results.json`
- Catlab results: `system_v6/probes/toolset_expansion_20260610_catlab_results.json`
- Ripserer results: `system_v6/probes/toolset_expansion_20260610_ripserer_results.json`

## Install Ledger

Carrier env discipline was preserved.

- Python sim-stack install: `galois==0.4.11` installed into `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.
- Python already present before this card: `quimb==1.14.0`, `cotengra==0.8.0`, `ott-jax==0.6.0`, `jaxopt==0.8.5`, `lineax==0.1.1`, `e3nn-jax==0.21.0`, `geomstats==2.8.0`, `netket==3.21.0`, `dynamiqs==0.3.4`.
- Julia carrier already present before this card: `ITensorMPS`, `ITensors`, `Grassmann`, `Manifolds`.
- Julia optional install: `TensorKit==0.17.0` in `system_v6/optional/tensorkit`.
- Julia optional install: `Nemo==0.56.0` and `Hecke==0.39.19` in `system_v6/optional/nemo_hecke`.
- Julia optional install: `Catlab==0.17.6` in `system_v6/optional/catlab`.
- Julia optional install: `Ripserer==0.16.16` in `system_v6/optional/ripserer`.
- Oscar was not installed; the card allowed the lighter `Nemo+Hecke` route if Oscar was too heavy.
- Catlab install note: initial registry tarball fetch reported an ACSets tree hash mismatch, then recovered by updating the ACSets git checkout and precompiling successfully.

## Verdict Table

| tool | seed use | probe result | verdict | layer-routed-to | installed-where |
| --- | --- | --- | --- | --- | --- |
| ITensorMPS | GHZ_n/W_n exact bond-2 MPS for n=6..8; entropies/reductions vs committed ladder values. | GHZ and W rows for n=6,7,8 had max bond 2; GHZ single and pair entropy matched `log(2)`; W entropies matched `H(1/n)` and `H(2/n)`. | useful-now | S1 named-state/tensor-network mirror | `system_v5/julia_carrier` |
| quimb(+cotengra) | Same GHZ_n/W_n check on Python plus one 8Q contraction tree. | GHZ/W max bond 2 for n=6,7,8; GHZ entropy matched committed `log(2)` rows; cotengra 8Q norm tree had width 3 and cost/flops 220. | useful-now | S1 tensor-network mirror for finite named-state receipts | sim-stack Python |
| Grassmann.jl | A and F=dA by exterior calculus; diff vs committed S2 values. | Exterior basis/wedge algebra produced `F = -2*sin(2*eta) d_eta wedge d_chi`, sign matching the committed S2 curvature. Caveat: chart coefficient derivative was explicit, not delegated to `Grassmann.d`. | useful-now | S2 connection/curvature form checks | `system_v5/julia_carrier` |
| ott | Wasserstein distance-to-uniform for S1 Haar receipts; compare power vs chi-square route. | Haar regularized OT cost `0.0892257643`; clustered cost `1.2971663922`; OT power ratio `14.5380`; chi-square power ratio `112.9412`. | useful-later | S1 statistical cross-check if Haar receipt is strengthened beyond scratch | sim-stack Python |
| jaxopt(+lineax) | Fixed-point solve for two terrain flows; limits vs committed S5 basins. | `Se_Cannon_R` and `Ni_Source_R` solved from exported A,b rows. Max lineax diff vs committed fixed points was `0.0` and `1.11e-16`; max jaxopt diff was below `7.76e-10`. | useful-now | S5 affine terrain fixed-point/basin solver sidecar | sim-stack Python |
| e3nn_jax | SU(2)-equivariance receipt for S1 commuting square via irreps. | Hopf vector after SU(2) z rotation matched `e3nn` vector irrep rotation with max abs diff `2.78e-16`. | useful-now | S1 equivariance/commuting-square cross-check | sim-stack Python |
| geomstats | S^3/S^2 geodesics/volumes vs Manifolds.jl/committed values. | S^2 and S^3 geodesic distances matched expected angle `0.7`; analytic volumes were S^2=`12.5663706144`, S^3=`19.7392088022`; N=4 lens volume `4.9348022005`. | useful-later | S1/S2/S3 geometry cross-checks when manifold API is needed | sim-stack Python |
| TensorKit | Small symmetric-tensor fusion check: SU(2) rep fit for S10. | `1/2 x 1/2 -> 0` and `1/2 x 1/2 -> 1` allowed; `1/2 x 1/2 -> 2` false; tensor product dim 4. | useful-later | S10 symmetric tensor and representation-fit checks | `system_v6/optional/tensorkit` |
| netket | Honest fit attempt vs basin/fixed-point work. | Tiny spin Hilbert and Ising operator worked, but the seed target is continuous Bloch affine basin/fixed-point work, not NetKet's natural QMB variational surface. | not-useful | not routed for S5 basin/fixed-point work; possible later QMB variational layer only | sim-stack Python |
| Oscar-or-Nemo+Hecke | `|PSL(2,7)|=168` group computation plus subgroup-chain/dimension check. | Nemo finite-field matrix route gave `SL(2,7)=336`, `PSL(2,7)=168`, subgroup chain `[168,21,7,1]`, and SU(2)/SU(3)/G2 dimensions `3/8/14`. | useful-later | S10 finite group and representation-chain toolchain | `system_v6/optional/nemo_hecke` |
| Catlab.jl | Encode 3 nesting-law arrow types plus S^3 -> L(N,1) -> S^2 commuting square. | Free-category presentation had 4 objects, 5 homs, 3 named arrow types, and 2 equations including `compose(quotient_arrow,density_arrow) => hopf_arrow`. | useful-later | nesting-law diagram checks before categorical promotion | `system_v6/optional/catlab` |
| dynamiqs | Conventions-approved qutip-jax replacement; one channel-evolution check vs committed S3/S4 values. | `dynamiqs.mesolve` dephasing run gave final x `0.6703200837` vs expected `exp(-0.4)=0.6703200460`, max diff `3.76e-08`; z stayed fixed at `0.0`. | useful-now | S3/S4 channel evolution sidecar, not a carrier replacement by itself | sim-stack Python, already present before this card |
| Ripserer.jl | Persistence on S7 complex vs gudhi Betti numbers. | Two 4-cycles sharing one vertex produced Ripserer Betti shape `[1,2]`, matching the committed GUDHI shape. Caveat: same Betti shape, not the full S7 mesh construction. | useful-now | S7 topology/persistence cross-checks | `system_v6/optional/ripserer` |
| galois | PG(3,3) point/line counts exact for q=3 twistor/lens follow-up. | Exact finite-field count returned 40 projective points and 130 lines; matched committed q=3 discriminator. | useful-now | q=3 twistor/lens finite-incidence follow-up | sim-stack Python, installed by this card |

## Verification

- `scripts/codex_runtime_env_doctor.py`: `ok=True`, `install_state=stable_observed`; no repo-local env pollution, missing expected modules, or active installers observed.
- `scripts/audit_runtime_mapping_references.py`: `ok=True`, `failure_count=0`, `warning_count=62`, `file_count=853`.
- Python fit probes completed and wrote `8` probe rows.
- Julia carrier fit probes completed and wrote `2` probe rows.
- Julia optional fit probes completed for TensorKit, Nemo+Hecke, Catlab, and Ripserer.
- Result JSON schema check: `6` result files, `14` probes, `0` classification/promotion problems.

## Boundary

These are fit probes only. The installed optional Julia projects are isolated under `system_v6/optional/*`; the Python package added by this card was installed only into the sim-stack Python env. No carrier-env package was added, and no result here is promotion evidence.
