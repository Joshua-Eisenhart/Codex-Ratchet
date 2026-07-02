# HOPFIELD_SPEC.md — quaternionic Clifford-Hopfield convention (JAX mirror contract)

`object_id = clifford_hopfield` · `classification = clifford_hopfield_poc` · `promotion_allowed = false`

This file fixes the EXACT convention the Julia carrier (`clifford_hopfield.jl`) uses so the
JAX mirror reproduces the same numbers. The Julia side WRITES the reference artifacts
(`patterns.npy`, `weights.npy`, `probe.npy`, `clifford_hopfield_results.json`); the JAX lane
READS them and cross-validates. Julia computes; JAX diagnoses.

## Claim ceiling (binding on both engines)
COMPUTES finite invariants on a Clifford carrier. Does NOT assert layer-completion, manifold
admission, coupling, bridge (rho_AB/Xi/Phi0/Axis0), flux, FEP, or physics. The link to the
ratchet survivors (`layers/order_null_killtest.jl`, `layers/ratchet_survivor_reach_killtest.jl`)
is a DIAGNOSTIC analogy, not proven identity. A recovered pattern is a CANDIDATE survivor.

## 1. Carrier: unit quaternion = Cl(3,0)+ ≅ ℍ ≅ SU(2)
A neuron state is a unit quaternion stored as `q = (w, x, y, z)` (real 4-tuple), `|q| = 1`.
It is an element of the even subalgebra of Cl(3,0). The genuine reused realization (from
`layers/clifford_rotor_spinor_network_entanglement.jl`, generators verified `{Γa,Γb}=2δab` at
0.0 error) is the 2×2 SU(2) matrix

    Q(q) = w·I2 − i·( x·σx + y·σy + z·σz )

with `σx=[0 1;1 0]`, `σy=[0 -i;i 0]`, `σz=[1 0;0 -1]`. This map is faithful:

| quaternion op | matrix op | verified in-file |
|---|---|---|
| Hamilton product `q*p` | `Q(q)·Q(p)` | max abs err < 1e-10 over 200 random pairs |
| conjugate `conj(q)` | `Q(q)†` | by construction |
| `\|q\|²` | `det Q(q)` | by construction |
| `i*j=k`, `j*i=−k`, `i²=−1` | — | err = 0.0 |
| `{σx,σy}=0`, `σx²=I` | — | 0.0 |

The Hamilton product is NONCOMMUTATIVE (this is the N01 witness). All dynamics run on the
4-tuple `qmul`; the matrix form is used ONLY to verify the algebra.

### qmul (the one product both engines must match)
```
qmul((w1,x1,y1,z1),(w2,x2,y2,z2)) =
 ( w1*w2 - x1*x2 - y1*y2 - z1*z2,
   w1*x2 + x1*w2 + y1*z2 - z1*y2,
   w1*y2 - x1*z2 + y1*w2 + z1*x2,
   w1*z2 + x1*y2 - y1*x2 + z1*w2 )
```
`qconj(q)=(w,-x,-y,-z)`. `qnormalize(q)=q/|q|`.

## 2. Hebbian weights (the reference `weights.npy`)
```
W[i,j] = Σ_μ qmul( ξ^μ_i , qconj(ξ^μ_j) )      for i ≠ j
W[i,i] = 0
```
`W[i,j]` is a quaternion. Stored in `weights.npy` as a `(N, N, 4)` Float64 array
(`W_arr[i,j,:] = (w,x,y,z)`). `patterns.npy` is `(M, N, 4)`; `probe.npy` is `(N, 4)`.
N = 12, M = 3.

## 3. Energy
```
E = - Re Σ_{i,j} qmul( qmul( qconj(ξ_i), W[i,j] ), ξ_j ).real
```
Monotone non-increasing under the update below (checked in-file).

## 4. Update (deterministic async, cyclic order 1..N)
```
for i in 1..N:                       # FIXED cyclic order (NOT random)
    h = Σ_j qmul( W[i,j], ξ_j )       # left quaternion action
    ξ_i ← qnormalize(h)   if |h| > 1e-12
```
Iterate sweeps until `max_i geodesic(ξ_i^prev, ξ_i) < 1e-10` or 200 sweeps.
The cyclic (deterministic) order is REQUIRED: recall must be a pure function of `(W, ξ0)` so
the order-dependent-basin control isolates WEIGHT noncommutativity from update-order noise.
(An earlier random-order draft let the erased control land >1 apart — a metric artifact the
erased control caught; fixed and reported, not hidden.)

## 5. Readouts
- geodesic distance on S³: `acos(clamp(|<q,p>|, -1, 1))` ∈ [0, π/2] (sign-folded).
- recall overlap: `mean_i |<recovered_i, target_i>|` ∈ [0,1] (1 = identical up to global S³ sign).
- config distance: `mean_i geodesic(a_i, b_i)`. basin label = argmin over stored patterns.

## 6. Controls (JAX mirror should reproduce both)
1. GEOMETRIC vs CLASSICAL: flatten each unit quaternion to R⁴; classical real Hopfield
   `W_real = Σ_μ v^μ (v^μ)ᵀ` (4N×4N, per-neuron 4×4 diagonal blocks zeroed), update
   `v ← W_real v` then per-neuron renormalize to S³. Compare recovered basins. If identical
   to the quaternion version, the Clifford is DECORATIVE (reported honestly).
2. NONCOMMUTATIVE-ORDER (ratchet) basin probe: elementwise `W_AB[i,j]=qmul(A[i,j],B[i,j])`
   vs `W_BA[i,j]=qmul(B[i,j],A[i,j])`; recover from the same probe under each; basin distance
   above floor = order-dependent. Commuting control restricts entries to the complex
   subalgebra `(w,x,0,0)` where qmul commutes → W_AB==W_BA → basin gap collapses. Erased
   control `B:=A` → distance 0. `load_bearing_flip` iff full-quat above floor AND commuting
   control flat AND erased control zero.
   NOTE: matrix multiplication is noncommutative even over a commutative ring, so the probe is
   ELEMENTWISE (not a matrix product) to isolate the QUATERNION noncommutativity specifically.

## 7. Honest current results (this run, seed 20260602)
- recall (M=3, 30% corrupt of pattern 1): probe overlap 0.899 → recovered 0.634, basin = target.
- capacity: `max_reliable_M = 1` under the strict bar (mean overlap ≥ 0.95 AND basin-correct
  fraction ≥ 0.90). Recall is NOT reliable above M=1 at this threshold — reported, not inflated.
- Control 1: NOT decorative (quaternion basins differ from Euclidean-dot).
- Control 2: `load_bearing_flip = true` (full-quat order-dependent; commuting + erased flat).
