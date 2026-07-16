# Fresh-context audit — l5_reaudit_data_driven_v1 (2026-07-11)

Verdict: CLEAN (two minor process notes; no fabrication).

Survived the strongest falsifier: mutating one measured shell_radius value changed every candidate's RMSE and flipped
the nested-vs-scalar verdict in opposite directions across seeds — numbers are load-bearing on the data. The
suspicious byte-identical RMSE (nested vs scalar) is a checkable degeneracy: unconstrained cubics in different bases
coincide when the PAVA monotonicity constraint doesn't bind (it binds on seed 1, where they genuinely diverge by
~0.0008). The leakage gate is real — the auditor injected a live cos-smuggle and the AST gate killed it. Splits
genuine; heldout never reaches fitters; tolerance sits 2-4 orders above observed gaps (not tuned).

FULL honest ranking (heldout RMSE, seed 0): polynomial_degree3 0.0143 < monotone_piecewise_linear 0.0394 <
scalar_stratum = nested_shell_structured 0.0588 << constant 0.371; overfit control flips (0 fit -> 21.98 heldout).
The simplest generic model beats every structured candidate on this finite surface — which undercuts, rather than
supports, any residual case for the withdrawn nested-shell claim.

Minor notes: (1) the leakage gate was hardened 3x post-freeze (scientific payload byte-identical across all 10
records — verified); card.md does not disclose the gate iteration. (2) The gate does not ban a hand-rolled polynomial
approximation of the generator — theoretical residual smuggling surface, unexploited here.

Orchestrator correction (owned): the audit task framing selectively cited the piecewise-linear win and omitted the
polynomial_degree3 outright win; the auditor caught it. The complete ranking above is the record.

Ceiling (self-declared by the artifact, audit-confirmed correct): scratch_diagnostic, passes local rerun; does NOT
restore or replace the withdrawn L5 demotion claim; manifold admission stays blocked. The L5 question remains OPEN
with real empirical weight now on "simple generic beats structure at this prediction obligation."
