# External Audit Prompt: QIT-FEP Axis0 Spinor Path-Integral Scout

Audit the revised Codex Ratchet formal scout:

- `system_v5/ops/formal_scouts/sim_qit_fep_axis0_path_integral_spinor_probe.py`
- `system_v5/ops/formal_scouts/results/qit_fep_axis0_path_integral_spinor_probe_results.json`
- `system_v5/ops/QIT_FEP_AXIS0_SPINOR_PATH_INTEGRAL_WORKOUT_20260523.md`

Verdict options:

- `ADMIT_AS_FORMAL_SCOUT`
- `REVISE`
- `REJECT`

Scope:

This is not a canonization request. The scout proposes a finite QIT-FEP
Axis0 candidate over spinor density states and finite Kraus-history path sums.
It explicitly does not admit final Axis0, full FEP, Markov blanket ontology,
holography, ER=EPR, or physics.

Core math:

```text
H_A = C^2
H_B = C^2
rho_AB in D(H_A tensor H_B)
h = (a_1, ..., a_T)
K_h = K_{T,a_T} ... K_{1,a_1}

Z_path =
  sum_h Tr[(E_A tensor I_B) (K_h tensor I_B) rho_AB (K_h^dagger tensor I_B)]

tau_AB =
  sum_h (sqrt(E_A) tensor I_B)
        (K_h tensor I_B) rho_AB (K_h^dagger tensor I_B)
        (sqrt(E_A) tensor I_B)

rho_AB|E = tau_AB / Tr(tau_AB)

F_Q(sigma_AB)
  = D(sigma_AB || tau_AB / Z_path) - log Z_path

Phi_QFEP_provisional =
  log Z_path + I_c(A -> B)_{rho_AB|E}

I_c(A -> B) = S(rho_B) - S(rho_AB)
```

Current receipt highlights:

```text
all_pass = true
formal scout fresh rerun validator = pass
contract lint = 0 violations
no NumPy usage
git diff whitespace check = pass

noncommuting_order_gap = 0.02709174596856334
commuting_quantum_order_gap = 0.0
commuting_classical_order_gap = 0.0

path_count 4  -> gap 0.02709174596856334
path_count 8  -> gap 0.024895335308016797
path_count 16 -> gap 0.014230348602011

I_c gap, entangled vs product = 0.08597299491014523
Phi gap, entangled vs product = 0.04183211133489706

B-side fixed-cut gauge:
rho_A gap                = 3.0411136596227075e-16
posterior rho_A gap      = 1.2566871346510768e-16
Z_path gap               = 2.220446049250313e-16
I_c gap                  = 4.440892098500626e-16
Phi gap                  = 0.0
not claimed              = invariance over arbitrary non-isometric extensions

manifold grid:
variance = 0.01477739658942105
flux_mean_gap = 0.16531492915707058
eta_span = 0.08451591404861725
commuting Z-only flux_mean_gap = 0.0

parameter robustness:
grid_size = 27
min_order_gap = 0.0010019519603086113
mean_order_gap = 0.037915135344573754
max_order_gap = 0.07711372784194415

component decomposition:
order gaps:
  log_z                = 0.023151225744149073
  coherent_information = 0.015610894719935431
  mutual_information   = 0.010626726006251419
  Phi provisional      = 0.03876212046408445
  Phi mutual-info      = 0.012524499737897654

commuting order gaps:
  log_z                = 0.0
  coherent_information = 3.608224830031759e-16
  Phi provisional      = 3.3306690738754696e-16

Opus first-pass objections already repaired:

- posterior-free-energy identity demoted to correctness boundary, with a
  tracked data-processing margin;
- B-side control renamed to fixed-cut reference gauge, not alternate
  purification;
- z3 dependency fence moved to boundary and labeled declared nonpromotion
  guard, not a derivation;
- parameter robustness sweep added;
- mutual-information candidate added to component decomposition.
```

Audit questions:

1. Are the pass conditions real falsifiers or are any still tautological?
2. Is `Phi_QFEP_provisional = log Z + I_c` honestly scoped as provisional?
3. Does the scout avoid classical Markov-chain ontology as a primitive?
4. Does the B-side fixed-cut gauge control now make the right claim?
5. Does the commuting manifold null actually separate flux sensitivity from
   generic grid variance?
6. What is the strongest remaining failure mode?
7. Which alternative Axis0 candidate should be tested next?

Return concise findings, file/section references if available, and a verdict.
