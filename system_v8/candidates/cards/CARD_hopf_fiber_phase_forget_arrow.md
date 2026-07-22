# BUILD CARD — hopf_fiber_phase_forget_arrow

Proposal-sim card (cr-ratchet, stage-5). Standard finite math only. No coined terms.
Ceiling: `classification = "tool_lego_fit_probe"`, `promotion_allowed = false`,
`ordering_status = "PROPOSED not canon"`.

## Goal

Build the documented arrow BELOW `pure_to_vn` that the memory explicitly queued
("continue arrows below (pure <- spinor/ray via Hopf phase-forget)"). The Hopf
projection `pi: S^3 -> S^2` sends the normalized spinor to its Bloch point,
forgetting the `U(1)` fiber. This is a strictly lower rung than `pure_to_vn`
(whose layer 0 is already the ray `CP^1`): here the object above is the full
spinor `S^3` WITH global/fiber phase, and the arrow forgets that phase. Prove the
map is one-way (the whole fiber collapses to one Bloch point) and that the
lost datum — the fiber phase and its holonomy under the Hopf connection — is not
recoverable from the Bloch point alone. This is a fully documented owner-ladder
layer (atlas §3.1 rungs 6->7->8) not yet built.

## Per-rung formal objects

| Rung | Formal object | Equation | Doc citation |
|---|---|---|---|
| carrier (above) | normalized spinor carrier | `S^3 = { psi in C^2 : ||psi|| = 1 }` | atlas §3.1 rung 6 |
| chart | Hopf spinor coordinates | `psi_s(phi,chi;eta) = [e^{i(phi+chi)}cos eta, e^{i(phi-chi)}sin eta]^T` | atlas §3.2, AXIS0 doc L1020-1026 |
| map | Hopf projection | `pi(psi) = psi^dagger (sigma_x, sigma_y, sigma_z) psi in S^2` | atlas §3.1 rung 7, §3.3 |
| image (below) | Bloch sphere | `S^2` (pure-state boundary, `≅ CP^1`) | atlas §3.1 rung 8 |
| density tie | pure density | `rho(psi) = |psi><psi| = 1/2(I + r·sigma)`, `r = pi(psi)` | atlas §3.3 |
| connection | Hopf connection (what is lost) | `A = -i psi^dagger dpsi = dphi + cos(2eta) dchi` | atlas §3.3, AXIS0 doc L1028-1032 |
| fiber loop | pure fiber motion | `gamma_fiber(u) = psi_s(phi_0+u, chi_0; eta_0)`, `rho_fiber(u) = rho_fiber(0)` | atlas §3.4, AXIS0 doc L1044-1046 |
| base loop | horizontal lifted base motion | `gamma_base(u) = psi_s(phi_0 - cos(2eta_0)u, chi_0+u; eta_0)`, `A(dot gamma_base)=0` | atlas §3.4, AXIS0 doc L1048-1054 |

## The arrow(s) to gate

1. FIBER FORGET IS ONE-WAY. The whole fiber (a `U(1)` circle above each Bloch
   point) maps to a single `r = pi(psi)`. Load-bearing witness: `psi` and
   `e^{i a} psi` (global phase) — and, distinctly, two points on the same Hopf
   fiber — have identical `pi(psi)` and identical `rho = |psi><psi|`, but are
   distinct in `S^3`. `pi` is non-injective; no inverse. This is the phase-forget
   arrow strictly below `pure_to_vn`.
2. WHAT IS LOST IS THE FIBER + ITS HOLONOMY. The fiber loop leaves `rho`
   invariant (`rho_fiber(u) = rho_fiber(0)`, atlas §3.4) — so fiber motion is
   invisible in the Bloch image; the base loop DOES move `rho`. The geometric
   phase (holonomy of `A` around a base loop) is the irreducible datum: the
   Bloch point plus a closed base loop recover the state only up to the Berry
   phase `oint A`. Witness (standard): solid-angle holonomy on `S^2` — a base
   loop enclosing solid angle `Omega` returns phase `-Omega/2`, not readable
   from the endpoint Bloch point.

Expected verdict: `EMERGES_ONE_WAY` / `RATCHETED_ONE_WAY` for the fiber-forget
projection, with the holonomy as the named irreducible (twin of "Berry curvature
irreducible from Bures" in the committed `bures_to_fubini_study`, one rung lower).

## Rivals / controls

- GENUINE control (must stay invertible on its image): the base loop
  `gamma_base` (horizontal, `A(dot gamma_base)=0`) — its `rho` DOES change with
  `u`, so on the base motion the Bloch point tracks the state. Fiber motion
  (invariant `rho`) vs base motion (varying `rho`) is the discriminating pair:
  `control_is_one_way = False` computed on base motion, `True` on fiber.
  Directly parallels the fiber/base density laws in atlas §3.4.
- Rival "phase is recoverable": refuted by the explicit global-phase pair
  (`psi` vs `e^{i a}psi`) with identical density.
- Rival "holonomy is just a coordinate artifact": refuted by a value-coupled
  control — a contractible (zero-area) base loop returns trivial phase while a
  finite-solid-angle loop returns `-Omega/2`; the phase co-varies with enclosed
  area, so it is geometric not gauge.
- Anti-tautology: the witness is the recomputed `pi(psi)` collision and the
  recomputed holonomy integral, NOT a `recover(k)==A/==B` SMT stand-in.

## Three-engine scoping

- `sympy` — LOAD-BEARING. Exact `pi(psi)`, exact `rho = |psi><psi|`, symbolic
  fiber-invariance `rho_fiber(u) = rho_fiber(0)`, exact connection
  `A = dphi + cos(2eta)dchi`, symbolic solid-angle holonomy.
- `numpy` — LOAD-BEARING. Finite spinor grid, fiber/base collision witnesses,
  numeric holonomy (line integral of `A` around a discretized base loop) vs
  enclosed solid angle.
- `z3` / `cvc5` — SUPPORTIVE only (`smt_role = supportive_nonvacuity_only`),
  out of `core_ok`. Do not label load-bearing; the numpy/sympy recompute carries
  the arrow.
- `jax` — memory-gated; batched holonomy sweep over base loops if `>= 0.40`.
- `julia` — memory-gated; reference recompute of `pi`, `rho`, and the holonomy
  integral (Canon).
- `qutip` — memory-gated; independent Bloch-vector / density cross-check.

## Acceptance

- Starts from `SIM_TEMPLATE.py`; full manifest + positive/negative/boundary.
- Result JSON in `ratchet_contract/ratchetings/results/`; passes local rerun.
- ClaimGate hook tier0 PASS, exit 3 acceptable; receipt declares
  `classification` + `promotion_allowed=false`.
- Lev record: schema-valid projection; wiring may stay BLOCKED (honest residual).

## Ceiling

`tool_lego_fit_probe`, `promotion_allowed=false`. Does not settle a canonical
layer ordering or support promotion. Poset effect if it holds: extends Axis A
downward — `spinor S^3 (with fiber phase) ->[Hopf pi] Bloch S^2 / CP^1` sits
below `pure_to_vn`, and names the fiber holonomy as the irreducible lost datum,
PROPOSED.
