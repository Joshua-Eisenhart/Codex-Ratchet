# THE RATCHETING GEOMETRY ORDER — the Registered Hypothesis (2026-06-12)

```yaml
receipt_kind: registered_hypothesis
provenance: codex-app derivation, OWNER-CORRECTED in-session (the rho-placement fix is the
  owner's: pure density matrices appear immediately after the phase quotient, NOT late);
  forwarded by the owner; the owner doctrine: proposals are allowed and REQUIRED — this is
  the hypothesis, to be tested, not canon
status: hypothesis to test on the carved substrate; reconcile w/ the deep-read lane
  (ratcheting_geometry_order_20260612.md) when it lands
```

## The clean geometry order (the ratchet ladder, owner-corrected)

1 Hilbert space H = C^2 | 2 normalized spinors S(H) = S^3 | 3 the phase action psi ->
e^{i theta} psi (fiber U(1) = S^1) | 4 projective space P(H) = S^3/S^1 = CP^1 = S^2 |
**5 PURE DENSITY MATRICES rho = |psi><psi| — exactly where phase is erased (the owner's
correction: right after the quotient)** | 6 probes/observables A = A*, <A> = Tr(A rho) |
7 Pauli/Bloch coordinates rho = (I + r.sigma)/2 (pure: |r|=1 = S^2) | 8 MIXED states
D(C^2) = the Bloch ball B^3 | 9 the Hopf connection A = -i psi†dpsi = dphi + cos(2eta)dchi |
10 curvature F = dA = -2sin(2eta) deta^dchi | 11 fixed-eta tori T_eta = S^1 x S^1 inside
S^3 | 12 holonomy/flux on loops and strips | 13 channels D_z, D_x, R_x, R_z | 14 generator
flows on D(C^2): expansion / circulation / contraction / retention | 15 ordered
compositions (channel-after-flow vs flow-after-channel) | 16 finite discretizations of
S^3/S^2/T_eta/D(C^2) | 17 tensor products (C^2)^{ox2}, (C^2)^{ox3} | 18 reduced matrices
rho_A = Tr_B rho_AB | 19 entanglement/mutual information | 20 Cl(6) on C^8 | 21 the number
tower R, C, H, O | 22 the Hopf tower (S^0->S^1->S^1; S^1->S^3->S^2; S^3->S^7->S^4;
S^7->S^15->S^8 — no fifth) | 23 the symmetry spaces SU(2), SU(3), G2, Spin(7), Spin(8), F4.

THE RATCHET RULE AT EVERY ROW: X_{n+1} = { x in X_n : condition_n(x) } — each layer's
geometry is a constraint that shrinks/alters the survivor shape; the next layer acts on
what remains. (The G-tower reading: each reduction eliminates structures that cannot
coexist with the next level's constraints — ratcheting by exclusion.)

## The 16 stages — THE SECOND PROPOSED MATH (hypothesis; the first proposal scored 0 exact
matches vs the discovered behavioral classes — this one inherits that test)

The stages are NOT 16 base spaces — they are 16 ordered dynamical geometries on D(C^2):
4 terrain flows x 4 channels, NATIVE PAIRINGS ONLY, x 2 orders = 16. The pinned pairing
convention (a hypothesis choice): Ti<->D_z, Te<->D_x, Fi<->R_x, Fe<->R_z; Se/Ne native to
the z-side maps, Ni/Si native to the x-side maps.

| Stage | Composition | | Stage | Composition |
|---|---|---|---|---|
| TiSe | T_Se ∘ D_z | | TeNi | T_Ni ∘ D_x |
| SeTi | D_z ∘ T_Se | | NiTe | D_x ∘ T_Ni |
| FiSe | T_Se ∘ R_x | | FeNi | T_Ni ∘ R_z |
| SeFi | R_x ∘ T_Se | | NiFe | R_z ∘ T_Ni |
| TiNe | T_Ne ∘ D_z | | TeSi | T_Si ∘ D_x |
| NeTi | D_z ∘ T_Ne | | SiTe | D_x ∘ T_Si |
| FiNe | T_Ne ∘ R_x | | FeSi | T_Si ∘ R_z |
| NeFi | R_x ∘ T_Ne | | SiFe | R_z ∘ T_Si |

The jargon-free content: each = the Bloch ball acted on by one squash-or-rotate map and one
flow (expand/circulate/contract/retain), in one of the two orders; the 16-structure is real
exactly because flow ∘ channel != channel ∘ flow in general — the commutator IS the stage
distinction.

## The flux ladder (three tiers, never blurred)

1. BASE flux = the Hopf curvature data: Flux(eta1,eta2) = int_strip F = oint_boundary A
   (exists, audited to e-16 on the carved object);
2. STAGE flux = how each of the 16 ordered actions transports/changes A, F, holonomy, or
   torus-leaf position (computable per stage once stages act on the substrate — UNBUILT);
3. MULTI-QUBIT flux = correlation/chirality/memory flux on (C^2)^{ox3}+ (the runtime tier,
   3Q floor, GNVW candidate — UNBUILT).

## The test this hypothesis owns

On the carved substrate: build the 16 compositions per this table; compute their label-free
behavioral fingerprints; compare against the 16 DISCOVERED classes (the same correspondence
test the first proposal failed 0/16); either outcome = the result. The pairing convention
and the T_tau flow realizations are the pinned choices the test adjudicates.

## SUPPLEMENT 1 — the explicit math (Hermes, 2026-06-12; strengthens the hypothesis, changes nothing)

**THE FOUR FLOWS as explicit Lindblad generators** (Phi_t = e^{t L}; the general form
L(rho) = -i[H,rho] + sum_j gamma_j (L_j rho L_j† - {L_j†L_j, rho}/2); Bloch form r' = Ar + b):
- Phi_E (expansion / open dissipative): L_E = -i[H_E, .] + sum gamma_j D[L_j];
- Phi_C (Hamiltonian circulation): L_C = -i[H_C, .] (pure rotation, radius-preserving);
- Phi_K (source/sink contraction): L_K = gamma_- D[sigma_-] + gamma_+ D[sigma_+] - i[H_K, .]
  (attractor/source structure in B^3);
- Phi_P (retention/projection): L_P = kappa(Pi_+ rho Pi_+ + Pi_- rho Pi_- - rho) - i[H_P, .]
  w/ Pi_± = (I ± n.sigma)/2 (attraction toward invariant strata).
The channels likewise explicit: D_z^lambda: (x,y,z)->(lambda x, lambda y, z);
D_x^lambda: (x,y,z)->(x, lambda y, lambda z); R_x^theta, R_z^theta the conjugations by
exp(-i theta sigma/2). The 16 = the ordered pairs per the registered table; the order
defect Delta_{Phi,O}(rho) = Phi(O(rho)) - O(Phi(rho)) ~ t(LO - OL) infinitesimally.

**THE FLUX-FATE CRITERION (the stage-flux tier made precise — new):** for each of the 16
maps, exactly one of:
(a) the map PRESERVES pure states -> it acts on S^2, may lift to S^3, and its stage flux is
    the computable holonomy shift Delta h = h(eta_after) - h(eta_before) w/
    h(eta) = -2pi cos(2eta);
(b) the map sends pure -> mixed -> the Hopf lift is ERASED and geometric flux is undefined
    on the image — the computable question becomes lift-erasure itself (which maps destroy
    the fiber structure, and at what lambda/t thresholds).
Prediction the table carries: the rotation-side compositions (R_x/R_z with Phi_C) are
case (a) — flux-transporting; the dephasing-side compositions (D_z/D_x with Phi_E/Phi_K/
Phi_P at lambda<1) are case (b) — lift-erasing. The correspondence test + the order matrix
(both in flight) can read this off their computed channels; the flux-fate column = a free
additional row for either packet's audit.

**The one-sentence version (adopted):** C^2 -> S^3 -> quotient by S^1 -> CP^1 = S^2 ->
pure rho -> the Pauli/Bloch frame -> the ball D(C^2) -> Hopf tori + A + F + holonomy ->
the 16 ordered compositions of four channels with four flows -> their effect on flux
measured by whether they preserve, move, or erase the Hopf lift -> tensor products ->
reduced matrices -> entanglement -> Cl(6) -> R/C/H/O -> the Hopf tower -> the symmetry spaces.
