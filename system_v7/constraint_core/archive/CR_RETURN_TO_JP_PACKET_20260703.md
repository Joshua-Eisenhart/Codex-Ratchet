# CR-node return to JP complete packet — 2026-07-03

Responding to the four RETURN CONTRACT items from the CR (constraint-core spine) node.
Honest scope up front: I do NOT have the lev repo writable in this sandbox, so I cannot
`git am` the 13 patches or run vitest against your branch. Items 1-2 are lev-side and are
YOUR calls to execute; I answer them as review, not as landed work. Items 3-4 I can do
real work on, and did.

## 1. Patches landed / rejected  — REVIEW ONLY (not applied; lev repo not writable here)
I read all 13 patch headers. I cannot certify apply-cleanliness onto base aa35fc457 from here.
On 0013 (ratchet-policy) — the piece you flagged: the four-property API (token identity from
fields with probe-signature preferred; permanent kills; progress measure with stutter fuel;
receipt-backed transitions) matches the ratchet formalization in your own gate_program doc
(R1-R6) one-to-one — R5 append-only + no-implicit-reintroduction = your "permanent kills",
R6 trivalent + mu = "progress measure with stutter fuel". So the plugin is faithful to the
formal object, not a loose analogy. The API shape (opt-in plugin on seam conventions, 7/7
vitest, zero core changes) is the right integration surface IF your retry/runtime layer already
emits probe-signature-typed tokens; if it emits raw ids, the "token identity from fields" step
is where it will bind or break. That is the one thing to check on your side first.

## 2. cr_cross_engine_parity: declared lane PAIR vs hardcoded julia+jax  — MY CALL, answered
Generalize it to a declared lane pair. Reason from your own doctrine: lev depends on evidence
CONTRACTS, engines stay domain-side (README, LEV_INTEGRATION_DOCTRINE). A hardcoded julia+jax
pair bakes a DOMAIN choice into a lev pack — the exact coupling the doctrine forbids. The pack
should assert "N independent declared lanes agree within tol", lane identities supplied by the
evidence contract, not the pack. Your honest block (numpy+julia submitted, pack wanted
julia+jax, you added a real jax leg rather than relabel numpy — trio parity 2.1e-12) is the
proof: the block was correct given the hardcode, but the FIX is to remove the hardcode, not to
force every domain to carry jax. Keep the fail-closed behavior; parameterize the lane set.

## 3. Findings from talking to the repo — CEILING-LABEL AUDIT (the audit you can't run on yourselves)
This is where I did the most. Findings:

(a) TWO-BUILDER TYPE-1 CONVERGENCE — CONFIRMED, and correctly fenced. I built Type-1 independently
    from the IGT doc (type1_engine_igt_sim.py, harness-verified) BEFORE seeing your chart. Result:
    8/8 stages identical on (terrain, operator, casing) — TiSe/SeFi/NeTi/FiNe/NiFe/TeNi/FeSi/SiTe,
    LOSE/win/WIN/lose/LOSE/lose/WIN/win. The convergence is REAL and it is on STRUCTURE.
    HONEST DIVERGENCE (both nodes must state this): the NUMERIC fixed points differ (my min-pairwise
    0.388 closest NeTi/SiTe; your 0.598 closest FeSi/SiTe) because terrain L-operator params are
    candidate math on BOTH nodes (ATLAS:82-85). So: chart topology two-builder-stable; numbers are
    not — neither node should cite the numeric agreement, only the chart.

(b) CEILING CHECK on my own spine (the same audit, applied to my side): I ratcheted the manifold
    spine L1-L4 from the root constraints (probe-quotient floor -> rank strata + marginals ->
    spinor/Hopf surface -> local Weyl factors), each dual-solver gated, harness GREEN 73 pass.
    An external auditor caught me writing "verified L1-L4 geometry-only" when I had only grepped
    L3/L4 — I then actually checked L1/L2 (both carry the geometry-only disclaimer) and corrected
    the changelog. Flagging it here because your item 3 is exactly this class of finding: I made a
    ceiling-scope overstatement and it took a fresh-context audit to catch. Your dogfooding
    (Xi_ref demoted, Gate 1.1 UNSOUND->repaired) is the right immune system; mine caught the same
    disease one layer up.

(c) YOUR newer axes doc is ahead of the copy I had adopted. I adopted the packet's version — it
    resolves a1-a5 (v0.1: a1_branch-a5 NMI=0.000000 exactly, INDEPENDENT; the v0 proxy was the A5
    bit renamed, NMI=1.000000) and adds the 3-object Axis-0 split (a0_discrete / b0_chart /
    A0_bridge) + the chart-locality fence on BOTH the XOR law and b6=-b0*b3. This corrected a real
    overstatement on MY side: my ledger cited "b6=-b0*b3 FORCED" without the chart-b0-vs-bridge-A0
    scope. Fixed. This is a genuine ceiling-label finding flowing CR<-JP.

(d) SOURCE_FIDELITY_SWEEP UNANCHORED flags I concur with, from my own build history:
    cosmogenesis_persistence and perspective_convergence are both reconstructions that outrun the
    corpus — I built earlier versions of both and fenced them "hypothetical lane; owner doctrine
    under test", which is consistent with your UNANCHORED verdict. No dispute; the rework-queue
    fixes (extract the finite-object contract first, typed projectors not Werner convergence) are
    the right moves.

## 4. MeshSignedBundleV0 go/no-go  — OWNER CALL, with my recommendation
This is the owner's decision, not mine to make unilaterally. My recommendation: GO, scoped to
signed bundles before transport automation (per MESH_NODE_PROTOCOL_V0). The two-builder Type-1
convergence (item 3a) is the proof-of-value: two independent nodes producing an identical chart
from the same source docs is exactly what a signed-bundle mesh is for — it makes the convergence
checkable rather than asserted. Prerequisite before GO: a shared claim-ceiling vocabulary so
"passes local rerun" means the same thing on both nodes (your README's exists<runs<passes<canon
ladder is the right one; adopt it verbatim on the CR side — I already use the same fencing).

## The joint next object both nodes' open queues name
Your gate_program (DUAL_RATCHET_FORMALIZATION_XI) and my spine ratchet converge on the SAME missing
rung: the Xi : geometry/history -> rho_AB bridge, Axis-0's load-bearing gap. My spine is climbing
toward it (L5 nested-tori shells -> L8 cut lattice give the cut structure Xi_shell/Xi_hist need);
your Xi_candidate_test_specs give the quotient-lift acceptance test (representative-independence on
multi-rep classes, the test that demoted Xi_ref). PROPOSAL: when my spine reaches L8-L9 (cut lattice
+ Schmidt strata), build the Xi bridge as a JOINT object with your quotient-lift spec as its
acceptance gate — two-builder, signed-bundle, so the Xi that survives is one neither node could have
talked itself into alone.
