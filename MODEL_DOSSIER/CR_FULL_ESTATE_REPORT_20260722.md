# Codex-Ratchet Full Estate Report — 2026-07-22 (audit-ready)

> **SUPERSEDED 2026-07-22 (this section only):** Section 1's manifold table and layer ordering are
> superseded by `MODEL_DOSSIER/CR_CORRECTED_ENTROPIC_GEOMETRIC_MANIFOLD_AND_ESTATE_AUDIT_20260722.md`
> (webui-corrected architecture) and indicted in detail by
> `MODEL_DOSSIER/PROBLEMS_FOUND_MANIFOLD_AUDIT_20260722.md` (13 blockers / 17 majors / 7 minors).
> Decisive corrections: Axis 0 is NOT a rung — it is the manifold-wide entropy-geometry gradient
> field acting through every layer; Phi_0(rho_AB) is one candidate cut-response functional, not
> Axis 0 itself. Five kinds never to collapse: nested stratum / Axis 0 / Ratchet / engine DOF /
> runtime-governance. The rest of this report (statuses, provenance, sections 2-7) remains the
> working ledger, subject to the same problems doc.

## Preamble

**Purpose.** This document is assembled for external LLM audit. It exists so an
auditing model with no prior context on this repository can locate, cite, and
attack every load-bearing claim currently on record. It is not a pitch, not a
status update for the owner, and not evidence of anything beyond what each
citation supports. Every section below was authored by a separate pass over
the repository; this assembly pass re-verified the top-level repo-state
claims directly (git log, git merge-base, `gh run view`) and otherwise
preserved each section's own citations, status labels, and ABSENT/UNVERIFIED
markers without softening.

**Status-ladder legend** (never imply a higher label from a lower one):

| Label | Meaning |
|---|---|
| `exists` | File or object is present in the repo, read directly |
| `runs` | Executes without error (exit 0) |
| `passes local rerun` | Freshly re-executed this session (or the cited session) and confirmed the result matches the receipt on disk |
| `canonical by process` | passes local rerun + `SIM_TEMPLATE` lineage + tool manifest + non-empty reasons + classification field, per this repo's own admission contract |

**Epistemic-label legend:**

| Label | Meaning |
|---|---|
| `CANON` | Owner-verbatim or owner-doctrine, per `ROOT/ROOT_CARD.md`'s own stated authority |
| `FUEL-proposal` | Pre-admission evidence or corrective formalization; explicitly not itself ratchet-admitted; usually self-declares `promotion_allowed: false` |
| `DEMOTED` | Downgraded from a prior higher-sounding status by the repo's own later record |
| `KILLED` / `WITHDRAWN` | A specific claim or design was tested/reviewed and rejected, with the negative preserved on disk |
| `OPEN` | Named as unresolved by the repo's own sources; no verdict stands |
| `UNCERTAIN` | Two or more readings are live and not adjudicated here, or a claim could not be checked this pass |

**Nothing in this document is asserted beyond its cited receipt; absence of a
cite means treat the claim as unverified and audit it.**

## Repo state (verified this assembly pass)

- Branch: `session/r0-three-engine-probes` (`git branch --show-current`, confirmed this pass).
- `git log --oneline` on this branch shows, most recent first: `1760f9a4a` (spine packet-mode scaffolding, partial/deferred), `12422c278` (sync of pre-session working-tree state), `d5ccd9707` (ClaimGate hostile-control corpus, 10 classes), `dcf4a5003` ("CI GREEN (workflow 9/9, mechanical seal 35 pass / 0 REJECTED)"), `6b01f73f5`, `1795bc9a4`, `b1440d915`, and earlier stress/inventory/spine commits back through `52d1076e2`. Full messages are quoted where load-bearing in the sections below.
- `git merge-base --is-ancestor dcf4a5003 HEAD` returns true this pass — `dcf4a5003` is confirmed an ancestor of the current `HEAD`. Status: passes local rerun (this assembly pass).
- `gh run view 29969379442 --json status,conclusion,headSha,workflowName,createdAt` (this assembly pass) returns: `{"conclusion":"success","createdAt":"2026-07-23T00:32:48Z","headSha":"dcf4a500355d0399640e876fe78e1888889dcc40","status":"completed","workflowName":"three-engine seal (no numpy)"}`. This independently confirms the GitHub Actions run tied to commit `dcf4a5003` completed with conclusion `success` on the workflow named "three-engine seal (no numpy)". It confirms the run-level outcome; it does not itself re-derive the commit message's literal internal figure "workflow 9/9" (a per-job count inside that run) — section 2.7 below, written before this run was queried, still marks that literal sub-count as not independently re-verified. Both statements are compatible: run-level `success` is now confirmed directly; the "9/9" job-count breakdown is not separately itemized by this check.
- Commit `dcf4a5003`'s own message claim of "mechanical seal 35 pass / 0 REJECTED" was independently reproduced by a fresh local rerun of `scripts/ci_three_engine_seal.py` in the session that authored section 2 (see 2.7) and is consistent with the GitHub Actions success just confirmed.
- Uncommitted/untracked state at the time of this assembly pass (`git status --short`): four `.lev/` directories under `system_v7/constraint_core/` and three `system_v7/sims/*` paths are untracked local runtime state, not content edits; not otherwise material to this report.

## Table of contents

1. [The manifold, layer by layer (math, names, formulas; canon vs fuel)](#1-the-manifold-layer-by-layer)
2. [Sim engines, libraries, tools — integration ladder, one by one](#2-sim-engines-libraries-tools--integration-ladder-one-by-one)
3. [ClaimGate — spec, components, implementation level, holes](#3-claimgate--spec-components-implementation-level-holes)
4. [The Ratchet — spec and implementation level](#4-the-ratchet--spec-and-implementation-level)
5. [Lev OS — current state, ClaimGate patch relation, issues](#5-lev-os--current-state-claimgate-patch-relation-issues)
6. [QIT engines + ALT engine types the estate can run](#6-qit-engines--alt-engine-types-the-estate-can-run)
7. [Fuel-not-canon proposals, negatives, alt sims, gaps, uncertainties](#7-fuel-not-canon-proposals-negatives-alt-sims-gaps-uncertainties)
8. [Questions for auditors](#questions-for-auditors)

---

## 1. The manifold, layer by layer

### 1.0 Source note (read before the rest)

The task names the atlas path as `system_v7/constraint_core/reference_docs_from_josh/physics_program/` §3.1. That directory does not contain an AXES_0_6 atlas file (checked: `ls` of that directory lists 15 files, none named AXES_0_6 or containing a §3.1 ladder). The 20-rung ladder with a math/status table lives instead at `/Users/joshuaeisenhart/Codex-Ratchet/system_v4/docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md` (dated 2026-03-30; a duplicate copy exists at `system_v5/READ ONLY Reference Docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS copy.md`; a third, byte-identical copy — 758 lines, diff-clean against the system_v4 copy treated as authoritative here — also exists at `system_v7/constraint_core/source_docs/user_attached_2026-07-02/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md`, inside the same `system_v7/constraint_core/` tree as the (non-existent) task-specified path). This is confirmed by `MODEL_DOSSIER/00_DURABLE_STATE_20260721.md:58`, which names that exact `system_v4/docs/` path as "the owner-attached 20-rung atlas §3.1." All atlas citations below use that file. ABSENT: no atlas file at the exact path the task specified — but a byte-identical copy is present elsewhere under `system_v7/constraint_core/`, so this is absence at the specific path, not absence anywhere under that tree.

Two documents carry different epistemic weight and must not be read as the same tier:

- `ROOT/ROOT_CARD.md` — owner-verbatim, top authority, outranks every spec (its own header, line 3).
- `/Users/joshuaeisenhart/Desktop/GEMINI_EVOLVING_PLAN_ASSESSMENT_AND_CORRECTED_ARCHITECTURE_2026-07-22.md` — self-declared "architectural reconciliation and execution plan. This is not a simulation receipt, a proof, or an admission of any physics claim" (its own line 4). Its §5–6 formalism (the `Z` tuple, `Sett_{G'}`, the typed entropy-geometry table) is a **FUEL-proposal**: a corrective re-formalization written against Gemini's draft, not owner text and not ratchet-admitted.

### Axis 0 — the entropy gradient that frames the whole ladder (read before the rungs)

**Correction to an earlier draft of this report:** a prior pass placed "Axis 0" only as the last rung of the ladder in (b) below. That placement conflates two distinct objects under one name — an error the owner has flagged as binding. This subsection is read before, and frames, everything below it.

CANON per owner doctrine, project `CLAUDE.md` ("BINDING STATE 2026-07-04," points 1–2, quoted verbatim):

> "1. Axis 0 = an entropy gradient, at the BEGINNING, innate. It is the drive. The readout (Phi_0, needs a cut, via Xi) is LATE. Two objects, one name — never conflate. A ratchet cannot move without a gradient.
> 2. Tentative (owner: 'could be wrong'): positive entropy (growth/expansion) and negative entropy (records/locks) are each their own gradients; Axis 0 = the gradient between them."

Two objects, one name — held apart through the rest of this section:

- **Axis 0 as drive (this subsection).** The entropy gradient of the whole manifold. Innate, present at the start, prior to any rung documented in (b) below. Every layer of that ladder — root constraints through the bridge/cut-state family — is presented as running ON this gradient; without it, per the owner's own words, "a ratchet cannot move." `ROOT/ROOT_CARD.md:12-14` ("THE DUAL") states the doctrinal basis for reading entropy as the literal surface the whole geometric manifold runs on, not a payload added afterward: "the dual ratcheting manifold with entropy/operators running as the literal surface of the geometry, requires dual ratcheting the operator entropy and the geometric constraint manifold."
- **Axis 0 as readout, `Phi_0` (late — (b) below, rung 20).** A different object sharing the same name: `Phi_0(rho_AB)`, a kernel family computed FROM a bipartite cut state, which itself needs the bridge `Xi` (rung 18) and the cut-state family `rho_AB` (rung 19) built first. This object is late in the ladder and is explicitly OPEN (atlas status "open but strongly narrowed" — see (b) and (e) below). It is not built. Its OPEN status is a claim about this separate, late object — not evidence against the drive-gradient framed here.

Owner-tentative reading (explicitly flagged "could be wrong," FUEL-tier, not adjudicated in this report): a two-gradient decomposition in which positive entropy (growth/expansion) and negative entropy (records/locks) are each their own gradient, and Axis 0 names the gradient between them. Source: `RATCHET_SPEC.md:90` ("Owner hypothesis (tentative, owner-flagged could be wrong): at the root the drive is a recorded asymmetry between distinction-opening tendency (growth/expansion) and distinction-locking tendency (records/locks); each tendency is its own gradient, and Axis 0 is the gradient between them.") and project `CLAUDE.md` "BINDING STATE 2026-07-04" point 2. Epistemic label: owner-tentative FUEL — a hypothesis under test, not itself ratchet-admitted, hedged by the owner as possibly wrong.

Nothing below this point builds or admits the drive-gradient itself. The ladder in (b) documents candidate geometric/mathematical realizations proposed to run ON it; rung 20 documents only the separate, late, OPEN readout object.

### (a) The root layer: constrained distinguishability

CANON per owner docs. `ROOT/ROOT_CARD.md:26-28` (owner verbatim, "THE ROOT SUBSTANCE"):

> "entropic monism is central... there is only one kind of substance — constraint on distinguishability. Identity is not primitive; it emerges from indistinguishability under probes (a=a iff a~b)."

The executable formalization of this (`system_v7/constraint_core/RATCHET_SPEC.md:62-68`, current process authority v0.5):

For a finite observation surface `X`, a finite set of demanded distinction edges `D`, and a proposed presentation/quotient `pi: X -> Q_pi`:

\[
C_D(\pi)=\{(x,y)\in D:\pi(x)=\pi(y)\},
\qquad
L_D(\pi)=|C_D(\pi)|.
\]

`RATCHET_SPEC.md:70-78` reads this as one object, two readings: geometrically, demanded edges are collapsed inside quotient blocks; informationally, demanded distinctions remain unresolved. The spec states explicitly (line 78) that "Entropy is therefore not a scalar payload running on a prior geometry in this process" — no Shannon/von Neumann/BKM/Fisher formula is installed at the root.

The two correlated pressures (`RATCHET_SPEC.md:32-39`, itself labeled "active owner pressures remain hypotheses under test," line 30):

- **F01 — finitude**: "every execution has finite evidence, proposal population, histories, controls, and budget. This does not prove a fundamental cell size or prevent later refinement."
- **N01 — noncommutation**: "order can be load-bearing, so order-sensitive candidates and schedule hypotheses must be tested. N01 does not install a matrix algebra or make every pair noncommute."
- (also listed, same block: MSS — weakest current survivor, line 36; T01 — grouping pressure / nonassociativity, line 38.)

Epistemic label: F01/N01/a=a-iff-a~b are **CANON per owner docs** as *doctrine* (`ROOT_CARD.md`), but the spec that operationalizes them is explicit that they remain **OPEN as hypotheses under test**, never themselves ratchet-admitted (axioms are presumed, not tested — `MODEL_DOSSIER/00_DURABLE_STATE_20260721.md:16`: "pointing verification machinery AT the axioms... = ratcheting the ratchet"). `ROOT/META_AXIOMS_LLM_FAILURE_GUARD.md:1-11` is a separate, non-ratcheted guard layer on LLM-authored fuel — it constrains what fuel is admissible to feed the ratchet, and is explicitly not itself a ratchet axiom (line 3-4).

### (b) The nested ladder, rung by rung (atlas §3.1)

Full table, `AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md:75-96` ("Full ladder in order"), transcribed exactly, atlas-status column as written (dated 2026-03-30 — see caveat below):

| Order | Layer | Exact mathematics (atlas) | Atlas status (2026-03-30) |
|---|---|---|---|
| 1 | root constraints | `F01_FINITUDE`, `N01_NONCOMMUTATION` | active |
| 2 | admissibility set | `C` | active |
| 3 | admissible manifold | `M(C)` | active |
| 4 | axis-slice rule | `A_i : M(C) -> V_i` | active |
| 5 | favored finite realization | `H = C^2`, `D(C^2)`, probes, Pauli basis | active |
| 6 | normalized carrier | `S^3 = { psi in C^2 : \|\|psi\|\| = 1 }` | active |
| 7 | Hopf projection | `pi(psi) = psi^dagger (sigma_x, sigma_y, sigma_z) psi in S^2` | active |
| 8 | Bloch sphere image | `S^2` | active |
| 9 | torus stratum | `T_eta = { psi_s(phi, chi; eta) : phi, chi in [0, 2pi) } subset S^3` | active |
| 10 | Clifford torus | `T_(pi/4)` | active |
| 11 | fiber-loop family | `gamma_fiber^s(u) = psi_s(phi_0 + u, chi_0; eta_0)` | active |
| 12 | lifted-base-loop family | `gamma_base^s(u) = psi_s(phi_0 - cos(2 eta_0) u, chi_0 + u; eta_0)` | active |
| 13 | left Weyl sheet | `psi_left in S^3` | active |
| 14 | right Weyl sheet | `psi_right in S^3` | active |
| 15 | left density | `rho_left = psi_left psi_left^dagger` | active |
| 16 | right density | `rho_right = psi_right psi_right^dagger` | active |
| 17 | engine runtime manifold | paired sheet state + torus coordinates + stage controls | active |
| 18 | bridge target family | `Xi : geometry / history -> rho_AB` | **open** |
| 19 | bipartite cut-state family | `rho_AB`, `rho_A`, `rho_B` | **open** |
| 20 | `Axis 0` kernel family | `Phi_0(rho_AB)` | **open but strongly narrowed** |

Supporting definitions the atlas attaches to this ladder: Hopf connection `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi` (`atlas:123`); horizontal condition `A(dot(gamma_base^s)) = 0` (`atlas:131`); frame unitary `V_s(u) = exp(-i H_s u)` with `H_left = +H_0`, `H_right = -H_0` (`atlas:143-145`).

**Currency caveat (must not be smoothed over):** the atlas's own header (`atlas:3-4`) self-labels "Date: 2026-03-30... Working support surface. This is an explicit atlas, not a doctrine rewrite." `MODEL_DOSSIER/00_DURABLE_STATE_20260721.md:43-44` (2026-07-21, fresher) states directly: "NO single canonical owner layer list exists (3 deep digs converge; commit d1b9a4497). Every numbered list is a downstream assistant reconciliation." Both readings are live and are not the same claim: the atlas's per-rung "active" column records which candidate math was in operative use in scout code as of March; it is not an admission verdict. The current admission verdict, run against the bundled manifold observation rows through the actual deterministic engine, is in `RATCHET_SPEC.md:293-303` (v0.6, executed):

```
legacy manifold instruments locally passing             8 / 8
manifold candidate parameter/name proposals            16,384
actual behavioral partitions                              224
aliases exposed                                         16,160
ordered gate/decomposition schedules                        75
orientation coface loss, radial -> radial+bit             9 -> 0
scientific manifold layers admitted                           0
```

So: 0 scientific manifold layers admitted by the deterministic v0.6 run, against a ladder whose atlas column marks 17 of 20 rungs "active." These are not contradictory once read correctly — "active" (in scout use) and "admitted" (survived the packet-relative MSS ratchet) are different predicates — but an external reader must not conflate them. `RATCHET_SPEC.md:305-307` adds the one earned fixture-relative result: "one extra binary orientation distinction beyond the radial scalar... It does not license a connection, bundle, topology, physical chirality, engine type, or canonical order."

`MODEL_DOSSIER/00_DURABLE_STATE_20260721.md:65-86` (2026-07-21 reality audit) gives per-object tiers that map onto specific rungs of this same ladder — quoted verbatim, object / tier / evidence:

| Atlas rung(s) it maps to | Object | Tier | Evidence path (from MODEL_DOSSIER table) |
|---|---|---|---|
| 9-14 (torus/Weyl sheets) | 16 engine stages | NOT worked out one-by-one | "right sheet = conj(left) (051943694); grid authored not discovered; census 14/16" |
| 13-14 | 2 engines / chirality flux split | genuine at scratch (1.76 rad, R²=0.982) | manifold_one receipts |
| whole ladder as one object | manifold_one | scratch ceiling; K2 BY-CONSTRUCTION | K1/K6 genuine; receipt `all_pass:true` flagged MISLEADING (no taint note) |
| 18-20 (Xi, cut, Phi0) | drive→quantum weld | HONEST NEGATIVE | local Kraus = separable/LOCC, negativity corr exactly 0.0; r2 entangling-generator 0.0445 < shuffle 0.162 |
| 18-20 | entanglement pawl | HONEST NEGATIVE | 4 right families swept; nothing sustains `S(A\|B)<0` past ~2 ticks; dissipation pinned 0.20 |

**Two-objects-one-name caveat, applied to this table specifically:** rung 20's row, "`Axis 0` kernel family," names only the LATE readout object `Phi_0(rho_AB)` — it is not the entropy-gradient drive framed above ("Axis 0 — the entropy gradient that frames the whole ladder"). The atlas source predates the owner's 2026-07-04 two-objects-one-name correction, which is why its own column header uses the bare name "Axis 0" for this late rung. This report preserves the atlas's wording verbatim (transcribed exactly, per this subsection's own header above) rather than silently editing the quoted table, and flags the naming collision here instead.

Epistemic label for the whole ladder: **FUEL-proposal** (an assistant-compiled realization table over standard QIT/Hopf-fibration mathematics), with rungs 1-8 individually **standard textbook math** (not itself in dispute) and rungs 18-20 explicitly **OPEN**.

### (c) Executable rung-relation arrows (`ratchet_contract/ratchetings/`)

All 15 arrow files in this directory carry, in-file, the identical self-declared claim ceiling: `classification = "tool_lego_fit_probe"`, `promotion_allowed = False`, `ordering_status = "PROPOSED not canon"`. None of these establishes a canonical layer ordering or bridge/axis admission by its own stated ceiling — this is asserted by the files themselves, not an external demotion. Epistemic label for every row in this section: **FUEL-proposal** (pre-admission evidence only), per `system_v7/constraint_core/CLAUDE.md`'s own definition of that tier.

Status checked this session: `ratchet_contract/ratchetings/root_foundation.py` was freshly re-run (`python3 root_foundation.py`, exit 0) — **passes local rerun**: verdict `ROOT_MECHANICS_HOLD`, `negatives_total=9`, `negatives_flipped=9`, `silent_hole_ids=[]` (matches `results/root_foundation.json`). The other 14 files below are **exists + prior receipt on disk** (`results/*.json`, file-modified today) — not independently re-run this session. An attempted re-run of `cut_dependent_entropy.py` was blocked by the script's own guard, `cut_dependent_entropy.py:404`: `raise SystemExit(f"refusing to reuse output: {OUT}")` — a deliberate no-clobber-of-existing-receipt design, not deleted here to force a re-run. Separately: the bare system `python3` in this environment lacks `jax` (`ModuleNotFoundError: No module named 'jax'`); the correct interpreter is `Makefile:5` (`PYTHON ?= $(SIM_PY)`) → `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`. This is an environment-tooling finding, not a repo-content finding.

| Arrow file | Object / exact statement (docstring cite) | Result highlight (receipt) |
|---|---|---|
| `root_foundation.py:871-898` | `S` = 16 tuples `(a,b,c,h) ∈ {0,1}^4`; probe family `M`; `a ~_M b` iff every probe in `M` agrees; `Q = S/~_M`; `reidentify` gate admits a proposed partition iff it reproduces `Q` exactly. Hidden coordinate `h` demonstrates no finite self-check can certify a probe family complete. | `results/root_foundation.json`: verdict `ROOT_MECHANICS_HOLD`, 9/9 negatives flip, 0 silent holes (re-verified this session) |
| `pure_to_vn.py:437-443` | Layer 0 = rays `\|psi><psi\|` on `C^2` (CP¹, Fubini-Study, `S=0` identically); Layer 1 = Bloch ball of mixed 2×2 density operators (`S>0` interior). Map = partial trace of a pure bipartite state on `C^2⊗C^2`. | classification `tool_lego_fit_probe` |
| `cut_dependent_entropy.py:16-38` | Layer J = joint `rho_AB` on `C^2⊗C^2`; Layer M = marginal pair `(rho_A,rho_B) = (Tr_B rho_AB, Tr_A rho_AB)`. CLAIM: `S(A\|B) = S(AB)-S(B)` and `I(A:B) = S(A)+S(B)-S(AB)` are born at the joint cut, unrecoverable from the marginal pair. On the Bell state (t=π/4): `S(A\|B) = 0 - 1 = -1` bit. | `results/cut_dependent_entropy.json`: `s_cond_bell_bits = -1.0` (confirmed by direct JSON read) |
| `extension_fibre_capacity.py:273-298` | Layer B = restricted marginal `rho_B = C_AB(rho_AB)`; Layer F = extension fibre `F_{A/B}(rho_B) = {rho_AB in finite family : ptrace(rho_AB,"R") = rho_B}`. Readout `kappa_{A/B}(rho_B) = log\|F_{A/B}(rho_B)\|`. HONEST CEILING (its own text): the 8-member finite probe family undercounts the true fibre — a sympy leg proves the whole one-parameter Werner family `p·bell+(1-p)·product` restricts to `I/2` for every `p`, a continuum the finite count of 4 misses. | `results/extension_fibre_capacity.json`: `fibre_maxmixed.kappa_bits = 2.0` (cardinality 4, on the finite probe family only); `fibre_product_01.kappa_bits = 0.0`; `symbolic_werner_family_identity.family_identity_exact = True` |
| `vn_to_shannon.py:66-71` | Layer 1 = Bloch ball with BKM metric + von Neumann entropy; Layer 2 = diagonal/simplex Δ¹ with Fisher-Rao metric + Shannon entropy. Map = CPTP dephasing channel `D(rho)=diag(rho_00,rho_11)`. | `results/vn_to_shannon.json`: verdict `RATCHETED_ONE_WAY` |
| `vn_to_shannon_basis_relativity.py:127-146` | Disclosure probe on the above: dephasing in `rho`'s OWN eigenbasis reconstructs `rho` exactly (`S(D_eigen(rho))-S(rho)=0`); the one-way drop only appears once the reference basis is FIXED independently of the state. States explicitly: "NOT a refutation... It IS a disclosure the receipt should carry: the one-way claim is basis-relative, not basis-free." | `results/vn_to_shannon_basis_relativity.json` |
| `renyi_alpha_axis.py:191-201` | Quantum Rényi family `S_alpha(rho) = 1/(1-alpha) ln Tr(rho^alpha)`, with limits `S_0 = ln rank(rho)` (α→0, Hartley/max-entropy), `S_1 = -Tr(rho ln rho)` (α→1, von Neumann), `S_inf = -ln lambda_max(rho)` (α→∞, min-entropy). Checks non-increase in α and that `S_0` is a one-way forgetting of the von Neumann spectrum. | `results/renyi_alpha_axis.json`: verdict `S0_ONEWAY_FORGET_OF_VN` |
| `bures_to_fubini_study.py:313-353` | Mixed layer = Bloch ball with Bures/SLD metric `g^B`; pure boundary = CP¹ with Fubini-Study `g^FS` and Berry curvature `F` via QGT `Q=g^FS+(i/2)F`. Map = `r→1` boundary limit of `g^B` vs `g^FS` computed directly. HONESTY NOTE: computed ratio at the pure boundary is 1 (identical), not the build card's expected 1/4, under the specific `g^FS=Re(Q)` (Provost-Vallée) convention used here — reported as computed, not forced to the card's expectation. | `results/bures_to_fubini_study.json`: verdict `BERRY_IRREDUCIBLE` |
| `real_vs_complex_tomography.py:375-412` | Real (rebit, n×n real symmetric) vs complex (qubit, n×n complex Hermitian) branches tested against local tomography `d2 = d1·d1`. Real branch: `real_tomography_gap = 10-9 = 1` (missing direction `Y⊗Y`, invisible to real-symmetric products); complex branch closes `16-16=0`. | `results/real_vs_complex_tomography.json`: verdict `COMPLEX_EARNED_BY_TOMOGRAPHY` |
| `magma_to_semigroup.py:499-503` | Finite combinatorial probe, magma→semigroup→commutative drop on a perturbed `Z/3Z` table. Self-declared: "external fuel only... does not establish a canonical, bridge, or axis-level ratchet." | `results/magma_to_semigroup.json` |
| `magma_smt_genuine.py:561-579` | Contrasted explicitly against `magma_to_semigroup.py`'s SMT check (called tautological there): pins the magma table as z3 `Function m: S×S→S`, encodes `(xy)z ~ x(yz)` as equations over the SAME pinned `m`; UNSAT core is checked (independently, in plain Python) to be exactly the associativity-violating triple; repairing/swapping the table flips SAT. | `results/magma_smt_genuine.json` |
| `algebra_ladder.py:623-651` | Chain `magma --[+assoc]--> semigroup --[+identity]--> monoid --[+comm]--> commutative monoid --[+inverse]--> abelian group` on a 4-element carrier, each arrow a congruence-closure quotient; structural entropy `S=ln\|S\|` drops per arrow; control chain `Z/4Z` (already satisfies all four laws) computed as bijective at every arrow. | `results/algebra_ladder.json` |
| `anticommutation_rung.py:684-717` | `S(V)` (commutative, `xy=yx`), `Lambda(V)` (Grassmann, `theta_i theta_j=-theta_j theta_i`, dim 4), `Cl(g)` (Clifford, symbolic metric `g`, `e_i e_j+e_j e_i=2g_ij`). Checks: `Cl(g=0) == Lambda(V)` exactly; symmetrization `Lambda(V)→S(V)` is non-injective (`theta1·theta2` vs `theta2·theta1` distinct, same symmetric image); n=1 control is a genuine bijection (computed `one_way=False`). Explicitly: does NOT settle the owner-open global order of {noncommutation, nonassociativity, anticommutation} (cites `ROOT/META_AXIOMS_LLM_FAILURE_GUARD.md` Part C). | `results/anticommutation_rung.json` |
| `finite_to_continuum_rung.py:746-778` | Nested dyadic partition `Y_k` of `[0,1]`, `\|Y_k\|=2^k`, `H_0(Y_k)=k ln 2`, `K_MAX=24` (finite throughout, no infinity constructed). Discretization is one-way forgetting (z3 UNSAT→SAT flip on erasure); the finite tower alone never pins a unique point without an added completeness/Cauchy axiom; control function already-constant on cells is recovered losslessly. | `results/finite_to_continuum_rung.json` |
| `law_order_branch.py:808-832` | On one fixed 4-element non-associative, non-commutative magma: impose `{A,C}` (associativity, commutativity) in both orders. (1) Endpoints: checked for genuine isomorphism (re-merge = order-independent destination = congruence-lattice join). (2) Path: intermediate entropy-drop trajectories checked for order-dependence (N01 test). (3) Control: subalgebra/homomorphic-image operators `S,H` run as a known non-re-merging branch, so the re-merge verdict is not a machinery artifact. | `results/law_order_branch.json` |

### (d) The corrected whole-candidate object `Z`, `Sett_{G'}`, packet-relative MSS

Source: `/Users/joshuaeisenhart/Desktop/GEMINI_EVOLVING_PLAN_ASSESSMENT_AND_CORRECTED_ARCHITECTURE_2026-07-22.md:119-203` (self-declared "not a simulation receipt, a proof, or an admission of any physics claim," line 4). **FUEL-proposal** — a corrective re-formalization, not owner-verbatim, not ratchet-admitted.

Whole candidate (`:121-135`):

\[
Z=
\left(
G,
\{X_A,Q_A,C_{AB},\mathcal F_{A/B},\rho_A,c_A\}_{A,B\in I_G},
\{\mathcal I^{y}_{e,k}\},
\mathcal R,
\mathcal A,
\mathcal P,
D_t,
\Pi_t
\right)
\]

with (`:137-147`): `G` = mutable nesting diagram; `X_A,Q_A` = finite survivor/operational quotient spaces; `C_{AB}` = restriction/coarse-graining maps; `F_{A/B}` = plural set-valued extension fibres; `rho_A,c_A` = density/topological-cochain data where licensed; `I^y_{e,k}` = instrument at engine type `e`, stage `k`, outcome `y`; `R` = record/history state; `A` = archive history; `P` = Purgatory; `D_t, Pi_t` = active finite demands and probes.

Settlement (`:149-158`), set-valued (zero, one, or several compatible whole states may survive):

\[
\operatorname{Sett}_{G'}(P(Z))
=
\left\{
Z':\mathcal C_{G'}(Z')=0,\ 
\mathcal A_{G'}(Z')=1
\right\}
\]

Comparison set and packet-relative MSS (`:162-179`):

\[
\mathcal C_t
=F_t\cup\{Z_{\mathrm{default}}\}
\cup\bigcup_j\operatorname{Sett}_{G'_j}(P_j(Z))
\]

\[
\operatorname{MSS}(D_t,\mathcal C_t)
=
\operatorname{Min}_{\preceq_{D_t}}
\{Z\in\mathcal C_t:Z\models D_t\}
\]

Explicit caveat in-doc (`:179`): "This never proves an absolute MSS. A later weaker candidate, new demand, new probe, or new nesting can reopen any tooth." This restates, in the `Z`/`Sett` vocabulary, the same MSS discipline already in `RATCHET_SPEC.md §6` (`pi ⪯ rho` when every block of `rho` lies inside a block of `pi`; `Surv(D) = {pi : L_D(pi)=0}`; `M(D) = min_⪯ Surv(D)`, `RATCHET_SPEC.md:140-150`) — the two formalisms are consistent, not independent confirmations (both descend from the same `RATCHET_SPEC.md` process; convergence here is expected by construction, not cross-family evidence).

Typed entropy-geometry table (`:193-201`, "not an entropy soup" — the doc's own words, `:203`):

| Domain | Licensed comparison | Coupled geometry |
|---|---|---|
| finite extension fibre | `kappa_{A/B}(x_B)=log\|F_{A/B}(x_B)\|` | finite refinement/restriction geometry |
| full-rank density stratum | `D_U(rho‖sigma)=Tr rho(log rho-log sigma)` | `g^BKM=Hess D_U` |
| pure-state branch | fidelity/transition probability | Fubini-Study metric + Berry curvature from the QGT |
| finite survivor graph | chosen state divergence | kernel `w_ab=K(D_ab)`, Laplacian `L=D-W` |
| classical record | KL divergence or `H(R)` | Fisher geometry |
| channel/process | normalized Choi-state divergence | pullback/channel geometry |
| GKSL semigroup, faithful stationary state | Spohn production | dissipative flow geometry (stated assumptions) |

Note the `kappa_{A/B}` row is the identical formula already executed (at FUEL tier) in `ratchet_contract/ratchetings/extension_fibre_capacity.py` (section (c) above) — the same object appears in both the Desktop corrective-formalism doc and a runnable probe with a numeric receipt (`kappa_bits=2.0` on the finite family, honestly ceilinged against the true continuum fibre).

### (e) Canon vs fuel — compact ledger

| Layer / object | Epistemic label | Basis |
|---|---|---|
| `a=a iff a~b`; constrained distinguishability; entropic monism | CANON per owner docs (doctrine); OPEN as tested hypothesis | `ROOT_CARD.md:26-28`; `MODEL_DOSSIER:16` (never itself ratcheted) |
| F01 (finitude), N01 (noncommutation) | CANON per owner docs (doctrine); explicitly "hypotheses under test" | `RATCHET_SPEC.md:30-39` |
| `C_D(pi)`, `L_D(pi)` root coface | Executable formalization, ratchet-process authority (not owner-verbatim wording, but the process's own root) | `RATCHET_SPEC.md:62-78` |
| Atlas §3.1 20-rung ladder (whole) | FUEL-proposal (assistant-compiled 2026-03-30 realization table) | `atlas:3-4`; `MODEL_DOSSIER:58` |
| Rungs 1-8 (root constraints through Bloch sphere) | Standard QIT/geometry math; ladder-*position* is proposal, the math itself is textbook | atlas `:77-84` |
| Rungs 9-17 (tori, Weyl sheets, engine runtime) | FUEL-proposal; "16 engine stages NOT worked out one-by-one" | `MODEL_DOSSIER:70` |
| Rung 18 (`Xi` bridge) | OPEN | atlas `:94`; `MODEL_DOSSIER:78` ("drive→quantum weld HONEST NEGATIVE") |
| Rung 19 (`rho_AB` cut-state family) | OPEN | atlas `:95` |
| Rung 20 (`Phi_0` kernel) | OPEN but strongly narrowed; `I_c` = "strongest simple signed candidate" | atlas `:96, 241`; physics-core doc `:920-921` ("no final Phi0 theorem is closed") |
| Two-gradient Axis-0 reading (positive/negative entropy as separate gradients, Axis 0 = the gradient between them) | Owner-tentative, explicitly flagged "could be wrong" | `RATCHET_SPEC.md:90`; project `CLAUDE.md` "BINDING STATE 2026-07-04" point 2 |
| Axis-0 drive (front, innate) vs Axis-0 readout `Phi_0` (late, needs `Xi`) — two objects, one name | Owner-binding distinction; NOT built (readout) | project `CLAUDE.md` point 1; `MODEL_DOSSIER:50` ("AXIS-0 = TWO OBJECTS ONE NAME... never conflate") |
| 13-layer list | DEMOTED | `MODEL_DOSSIER:62` ("scout code... DEMOTED — never present as owner list") |
| Killed/demoted atlas items | KILLED/DEMOTED (atlas's own words) | atlas `:252`: "raw local `left\|right` as final doctrine cut; runtime `ga0` as doctrine object" |
| All 15 `ratchet_contract/ratchetings/*.py` arrows | FUEL-proposal (self-declared: `promotion_allowed=False`, `ordering_status="PROPOSED not canon"`) | each file's own module-level constants, section (c) above |
| Desktop doc §5-6 (`Z`, `Sett_{G'}`, typed entropy-geometry table) | FUEL-proposal (corrective re-formalization, not owner-verbatim, not admitted) | doc's own line 4 |
| v0.6 executed manifold audit | canonical-by-process for its own narrow finding only ("one extra binary orientation distinction"); "scientific manifold layers admitted: 0" for everything else | `RATCHET_SPEC.md:296-307` |

#### What is not built

- `Xi` (the bridge from geometry/history to a cut state `rho_AB`) is OPEN at every source consulted: atlas rung 18 ("open"), `MODEL_DOSSIER` drive→quantum weld and entanglement-pawl rows (both "HONEST NEGATIVE"), physics-core doc §23 ("no final Phi0 theorem is closed," line 921).
- Axis-0 as readout (`Phi_0(rho_AB)`) is explicitly LATE and requires the `Xi` cut; Axis-0 as drive (entropy gradient) is explicitly EARLY/innate. These are two objects sharing one name, and the project's own binding instruction (`CLAUDE.md` "BINDING STATE 2026-07-04," point 1) states: "Two objects, one name — never conflate." `MODEL_DOSSIER:50` repeats this independently.
- No single canonical owner layer list exists, per the most current source read (`MODEL_DOSSIER:43-44`, 2026-07-21) — this is a live tension with rendering the atlas §3.1 table as *the* ladder; both readings (atlas-as-realization-table vs. "no canonical list") are held here rather than collapsed, per the repo's own anti-collapse discipline.

### Recent doctrine (2026-07-19 to 2026-07-21) — not yet reflected in the ladder above

Four owner-doctrine records postdate the ladder and ledger above and are not otherwise carried in this section. None is repo-canon in the sense of an executed, admitted sim; each is recorded at its own stated standing, with its own source. Where no in-repo doc states the doctrine, the citation is the owner-session memory record, read directly before citing here, and marked **owner doctrine record (out-of-repo)**.

**Entanglement central** (doctrine, 2026-07-19). Owner: "conditional quantum entropy can be negative. i think this matters... entanglement is central to this model." Negative quantum conditional entropy, `S(A|B)<0`, is read as the witness/fuel — a resource signature, distinct from mutual information (which stays non-negative and would be a pathology if it went negative). This doctrine has an executable witness already documented in this report: `ratchet_contract/ratchetings/cut_dependent_entropy.py`, verdict `CORRELATION_ENTROPY_BORN_AT_CUT`, `s_cond_bell_bits = -1.0` on the Bell state (see (c) above and section 4.5's arrow table below). Status of that witness, unchanged from (c) above: exists + prior receipt on disk, `classification: tool_lego_fit_probe`, `promotion_allowed: false`; this session's rerun attempt was blocked by the script's own no-clobber guard, not independently re-executed. It is FUEL-tier, not a canon admission. Coherent information `I(A>B) = -S(A|B)`, proposed as a quantum-side candidate realization of the Axis-0 drive (not the drive itself), is explicitly OPEN and not built as the specific nested-cut-gradient design the doctrine specifies ("next sim card = coherent-information gradient across the nested cut ladder," per the same memory record). Older `system_v4/probes/` files with "coherent_info" in their names exist (e.g. `sim_lego_coherent_info_advanced.py`) but predate this doctrine and were not checked against this specific design this pass — not cited as satisfying it. Source: owner doctrine record (out-of-repo), `user_entanglement_central_conditional_entropy_gradient.md`.

**The mesh = axes 7-12** (doctrine, 2026-07-20). Owner: "i said 'mesh'. it is my 7-12 axes." A single node is proposed to run the lower manifold, axes 0-6 (the ladder in (b) above); the FIELD of nodes is proposed as the upper manifold, axes 7-12. Node = engine-object (axis 7); inter-node gossip/relation = axis 8; a 2-node minimum is named as the smallest possible field. An F4-algebra binding (Aut of the Albert algebra `J3(O)`) is named as a CANDIDATE only — the owner's own words: "the numbers just match. and that is about it." An axis-8 field probe exists on disk and was not re-run this session but is corroborated by its own commit message: `system_v8/upper_manifold/axis8_field_v0.py`, receipt `system_v8/upper_manifold/results/axis8_field_v0_results.json` (`classification: scratch_diagnostic`, `promotion_allowed: false`, `verdict: PASS`, commit `6f806ce42`) — `non_commutation_witness.order_gap_mean = 0.4698734...` across all 28 unordered pairs (all nonzero, `order_gap_min = 0.0724`), and `kind_classification.n_new_kind_clusters = 14` ("14 new channel kind cluster(s) emerge under composition, distinct from the 3 base kinds") — both figures matching the memory record's stated predictions. Status: exists/self-reported PASS, not independently re-run this pass — do not read this as canon; it is a scratch-diagnostic probe consistent with the doctrine's predictions, nothing stronger. Source: owner doctrine record (out-of-repo), `user_mesh_is_upper_manifold_axes_7_12.md`.

**Ratchet comparison doctrine** (axiom-level corrections, 2026-07-21). Four owner corrections to the execution contract described in section 4 below: (1) the comparison unit is a NESTED CHAIN — a thing plus its next layer(s) — compared against another chain, never a flat single-layer candidate ("the ratchet can only compare nested things"); (2) no maximality is ever asserted — a frontier member is only coarsest-among-things-that-also-nest-so-far, and the search for a rival that also nests never closes; (3) chain-EXTENSION (finding more layers on an already-ratcheted chain) is valid ratchet progress with no comparison required at all; (4) the frontier BRANCHES — dead ends move to Purgatory with a named re-entry condition, incomparable candidates coexist, and behaviorally-equivalent branches may re-merge. A fifth, sharper correction: MSS is partition-coarseness only (no separate score), and persistence/evolvability/whole-nest requirements THICKEN the demand set rather than adding new scores. The axioms themselves (`a=a iff a~b`, F01 finitude, N01 noncommutation) are explicitly NOT ratcheted — they are the presumption floor, given, not provable, never pointed at by the system's own verification machinery. Status: partially already reflected, in the process spec's own words, at `RATCHET_SPEC.md:140-156` (nested-chain/no-maximality language — see section 4.2 below), so this is not purely out-of-repo; the branching-frontier/Purgatory/re-merge machinery itself is `exists`-level only (`ratchet_contract/mss.py`, section 4.4 below), not independently re-verified this pass. Source: owner doctrine record (out-of-repo), `user_dont_ratchet_the_ratchet_branching_frontier.md`; in-repo partial echo, `RATCHET_SPEC.md:140-156`.

**Object doctrine** (2026-07-21). Owner: the QIT engines "don't presume objects to be real... probes on distinguishability help see shared attractor-like basins and shared object-like qualities... a shared correlation so high that it can become a pseudo identity." Reading: the engines are object-FORMING machinery, not object-presuming machinery. Pseudo-identity = correlation-so-high-across-probes (a shared attractor basin); objectivity = redundancy across perspective-probes, in the form of quantum-Darwinism-style objective records; legitimacy scales with how many of the engines' own stages/loops/geometry-entropy structure a candidate survives. OPEN fork, held not resolved: the owner's stated philosophy wants GRADED pseudo-identity (a correlation threshold); the running kernel (`IDENTITY_GATE`, `pi_probes == pi_reidentify`, section 4.4 below) implements EXACT behavioral partition-merge only. A threshold-based graded merge would smuggle in a metric choice not yet specified. Status: FUEL/OPEN — a philosophical/design frame, not an executed sim; the exact-merge kernel it is held against is `exists`+`runs` (section 4.4 below). Source: owner doctrine record (out-of-repo), `user_qit_engines_object_forming_pseudo_identity.md`.

**P-vs-NP direction** — cross-reference only; carried in full in section 7(c)#10 below (owner hypothesis, `a=a iff a~b` as Myhill-Nerode, first-tooth 2SAT/3SAT/XOR-SAT battery specified but not built). Not restated here, per this report's own no-duplication convention.

### Uncertainties flagged

- UNCERTAIN: whether the atlas's per-rung "active" status (2026-03-30) still holds for rungs 1-17 given no independent re-audit of those specific rungs was performed in this session beyond what `MODEL_DOSSIER`'s 2026-07-21 table already covers (rungs 9-17 only). What would settle it: a rung-by-rung re-run of the atlas's own referenced scout code, dated and receipted, the same way `MODEL_DOSSIER §4` did for rungs 9-20.
- UNCERTAIN: whether `cut_dependent_entropy.py`'s claimed verbatim lift from `system_v8/nested_manifold/rungC_joint_cuts.py` is byte-accurate — not independently diffed this session (out of scope for time budget). What would settle it: a direct diff of the named functions between the two files.
- UNCERTAIN: whether the 14 non-`root_foundation` ratchetings receipts would reproduce byte-identically on a fresh run — not checked this session (see status note in section (c)). What would settle it: deleting or redirecting each `OUT` path and re-running with `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

### Absent / unverified (index)

- AXES_0_6 atlas file ABSENT at the task-specified path `system_v7/constraint_core/reference_docs_from_josh/physics_program/` — found instead at `system_v4/docs/AXES_0_6_AND_CONSTRAINT_MANIFOLD_EXPLICIT_ATLAS.md`.
- `cut_dependent_entropy.py`'s claimed verbatim lift from `system_v8/nested_manifold/rungC_joint_cuts.py` not independently diffed.
- 14 of 15 ratchetings arrow scripts (all except `root_foundation.py`) not independently re-run this session — receipts on disk only, dated today; `cut_dependent_entropy.py` rerun attempt blocked by its own no-clobber guard, not forced past.
- Whether atlas rungs 1-8 and 10-17's March-2026 "active" status column still holds was not independently re-verified rung-by-rung beyond what `MODEL_DOSSIER`'s 2026-07-21 audit already covers for rungs 9-20.
- No single canonical owner layer list exists per `MODEL_DOSSIER` (2026-07-21) — this is in tension with rendering the atlas as THE ladder; both readings preserved, not collapsed.

---

## 2. Sim engines, libraries, tools — integration ladder, one by one

Primary source: `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md` (dated 2026-07-22). The file has two layers: an opening "campaign order" section describing intent, and a later "MEASURED INTEGRATION MATRIX 2026-07-22" section that explicitly says it "supersedes the guesses above" (line 67). This report follows the measured section as current; the opening section is retained framing, not a competing live reading — the doc itself resolves the order.

### 2.1 Engines

Status: passes local rerun. This session reran `python3 scripts/ci_three_engine_seal.py` fresh — output `three-engine CI seal: 35 receipt(s) pass, 0 REJECTED`, matching commit `dcf4a5003`'s claim of "35 pass / 0 REJECTED."

| Engine | Version | Owner-spec role | Measured state | Source |
|---|---|---|---|---|
| JAX | 0.10.1 | base workhorse — jax.numpy x64, "the load-bearing relaxation" | INTEGRATED, load-bearing in `cut_dependent_entropy, pure_to_vn, renyi_alpha_axis, vn_to_shannon`, and (post CI-green commit) `bures_to_fubini_study, real_vs_complex_tomography, extension_fibre_capacity, vn_to_shannon_basis_relativity`, plus 3 thermo sims | `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:71` |
| Julia 1.12 / QuantumOptics | 1.2.6 | authoritative canon | INTEGRATED, load-bearing in the same arrow set via `*_julia.jl` files | `:72` |
| PyTorch | 2.11.0 | DEFERRED per owner ("needs rented cloud GPUs"); not required by the seal (2 engines suffice) | load-bearing in exactly one arrow (`cut_dependent_entropy` — complex128 eigvalsh/einsum ptrace, per `ratchet_contract/ratchetings/results/cut_dependent_entropy.json` `tool_integration_depth.torch=load_bearing` + `engine_values.torch_S_cond_bell`); AVAILABLE (imported, not load-bearing) elsewhere | `:73`, `:26` |
| numpy | 2.3.4 | CONTAINED satellite — allowed as downstream CPU analytical layer, NEVER load-bearing, NEVER the sim engine | CONTROL-ONLY estate-wide; the seal hard-rejects any receipt labeling numpy/scipy/mpmath `load_bearing` | `:62`, `claimgate_plugin/three_engine_seal.py:29,93-96` |

Epistemic label on the numpy rule: CANON per the owner's 2026-07-22 spec update (`INTEGRATION_INVENTORY_AND_CAMPAIGN.md:60-65`), which explicitly "supersedes prior numpy rules" — reverting the blanket-reject stance recorded in commit `68c22f81a` ("harden(seal): reject numpy PRESENCE at all"). Both textual states exist in git history; the doc marks the newer one authoritative, so this report follows that resolution rather than treating it as an open divergence.

Verified numpy-free directly this session (not just trusting receipt metadata): grepped the `_jax.py` legs for the four previously-numpy-red arrows plus the three thermo sims — `bures_to_fubini_study_jax.py`, `real_vs_complex_tomography_jax.py`, `extension_fibre_capacity_jax.py`, `vn_to_shannon_basis_relativity_jax.py`, `carnot_engine_jax.py`, `szilard_engine_jax.py`, `quantum_otto_engine_jax.py` — zero matches for `import numpy` / `from numpy`. Status: passes local rerun.

### 2.2 Python libraries, one by one

Legend (the doc's own, `:68`): INTEGRATED = load-bearing in a committed arrow · SUPPORTIVE = cross-check role in a committed arrow · AVAILABLE = installed/importable, not load-bearing anywhere · stress-probe-demonstrated = capability shown in `sim_engines/stress/`, explicitly `promotion_allowed: false`, not wired into any arrow.

**INTEGRATED / SUPPORTIVE (load-bearing or cross-check in a committed arrow):**
- `dynamiqs` 0.3.4 — INTEGRATED, JAX quantum leg (asqarray/ptrace/entropy_vn) in the numpy-free quantum-entropy arrows (`:19,77`).
- `z3-solver` 4.16 — INTEGRATED load-bearing in `magma_smt_genuine` (`ratchet_contract/ratchetings/results/magma_smt_genuine.json`, verdict `MECHANISM_ENCODED_UNSAT`); SUPPORTIVE cross-check in roughly 13 other arrows (`:79`).
- `sympy` 1.14 — INTEGRATED load-bearing (exact identities) in ~10 arrows, including as the sole load-bearing tool in the two symbolic exemption cases `finite_to_continuum_rung` and `law_order_branch` (both receipts' `tool_manifest.sympy.used=true`, checked this session) (`:80`).
- `cvc5` 1.3.3 — SUPPORTIVE dual-SMT cross-check in ~15 arrows (`:81`).
- `qutip` 5.2.3 — SUPPORTIVE/control cross-check in ~8 arrows; one inconsistency on record: `vn_to_shannon.json` labels qutip `load_bearing` in `tool_integration_depth` even though the doc itself calls this "a minor inconsistency" since the arrow passes on jax+julia alone (`:100-111`, receipt checked this session). Flag as OPEN / unreconciled metadata, not corrected.
- `torch` 2.11.0 — INTEGRATED in exactly 1 arrow (`cut_dependent_entropy`, complex128 leg) (`:83`).
- `diffrax` 0.7.2 — SUPPORTIVE in the 3 thermo sims per `system_v8/thermo_engines/results/carnot_engine.json` (`tool_integration_depth.diffrax=supportive`, checked this session) — a step up from the doc's own AVAILABLE listing at line 86, which predates the thermo-trio commit `dcf4a5003`.

**AVAILABLE (installed, importable, not load-bearing in any committed arrow) — JAX ecosystem** (`:86`): `diffrax` 0.7.2 (elsewhere than thermo), `netket` 3.21, `quimb` 1.14 (+`cotengra` 0.8, `autoray`, `kahypar`), `ott-jax` 0.6, `e3nn-jax` 0.21, `jaxlie` 1.5, `optax` 0.2.8, `optimistix` 0.1, `jaxopt` 0.8.5, `lineax` 0.1.1, `equinox` 0.13.8, `flax` 0.12.7, `dm-haiku` 0.0.16, `blackjax` 1.5, `numpyro` 0.21, `flowMC` 0.6, `jax-verify` 1.0, `auto_LiRPA` 0.7, `jraph`, `mctx`, `chex`, `oryx`, `jaxga` 0.0.2, `galois` 0.4.11 (named a "finite-field load-bearing candidate" — proposal, not yet promoted). The doc notes `diffrax`/`netket`/`quimb` are imported in `system_v8` `jax_scale_lanes`/`jax_estate_test`, but those are unsealed, non-arrow scripts, so the doc keeps them AVAILABLE rather than INTEGRATED (`:87`).

**AVAILABLE — proof/dynamics/topology/convex** (`:89`): `maude` 1.6 (rewrite, unused); `pysindy` 2.1, `pykoopman` 1.2.1, `PyDMD`, `derivative` (dynamics ID, numpy-satellite home by design); `TopoNetX` 0.4, `gudhi` 3.12, `rustworkx` 0.17, `xgi` 0.10, `networkx` 3.6, `igraph` 1.0 (topology); `cvxpy` 1.9, `cvxpylayers` 1.2, `diffcp`, `clarabel`, `osqp`, `scs`, `highspy` (convex, paired with the unbound `qics` repo).

**AVAILABLE — PyTorch ecosystem** (`:90`): `torch-geometric` 2.7, `torchdiffeq` 0.2.5, `torchode` 1.0.1, `xitorch` 0.3, `torch_ga` 0.0.6, `e3nn` 0.6, `geomstats` 2.8, `lightning` 2.6.5, `torchrl` 0.13.3, `evotorch` 0.6.1.

**AVAILABLE — other quantum SDKs, unused in any arrow** (`:91`): `qutip-jax` 0.1.1, `cirq` 1.6.1, `qiskit` 2.4.1, `pennylane` 0.44.1 (+lightning), `clifford` 1.5.1, `kingdon` 2.1.1.

**AVAILABLE — prob/ML/evolutionary** (`:92`): `inferactively-pymdp` 1.0.3 (active inference/FEP), `dynamax` 1.0.1, `pymc` 6.0, `pytensor`, `arviz`, `scikit-learn` 1.8, `umap-learn`, `hdbscan`, `pymoo`, `deap`, `cma`, `ribs`.

### 2.3 Julia libraries, one by one

**INTEGRATED:**
- `QuantumOptics` 1.2.6 — INTEGRATED authoritative leg (entropy_vn/ptrace) in the same arrow set as JAX/dynamiqs (`:23,72,78`).

**AVAILABLE** (installed in `system_v5/julia_carrier`, importable, not load-bearing in any sealed arrow) (`:88`): `QuantumClifford` 0.11.4, `Yao` 0.9.3, `QuantumToolbox` 0.44, `CliffordAlgebras` 0.1.4, `Grassmann` 0.8.44, `Octonions` 0.2.3, `Quaternions` 0.7.7, `ITensors` 0.9.30 / `ITensorMPS` / `ITensorNetworks` / `TensorKit` / `PEPSKit` / `TensorOperations`, `Manifolds` 0.11.27 / `ManifoldsBase` / `GeometryBasics` / `CombinatorialSpaces`, `DifferentialEquations` 8.0 / `DynamicalSystems` 3.6.8 / `ChaosTools` 3.5.4 / `Attractors` 1.38.4, `Symbolics` 6.58 / `Z3.jl` 1.0.4, `Flux` 0.16.10 / `Lux` 1.31.4 / `Zygote` 0.7.10 / `Enzyme` 0.13.154, `PythonCall` 0.9.35 / `DLPack` 0.3.1 / `CondaPkg` — this bridge trio is marked "env-incompatible per Gemini, not in carrier" (`:88`): a documented incompatibility, not merely an unused import.

**SERIALIZED SPINE STACK smoke-test** (`:120`, dated 2026-07-22, "install-and-test sweep — all functional, not just importable"): Julia carrier, 7/7 one-real-operation smokes pass — `Catlab` SymmetricGraph, `Arrow` roundtrip, `Z3` unsat (And takes Vector), `Satisfiability.jl` sat, `DynamicalSystems` Henon map, `QuantumOptics` entropy_vn, `PackageCompiler` loads. `Catlab`, `Arrow`, `Satisfiability`, `PackageCompiler` were added to the carrier the same day. Status label for this batch: runs (smoke-tested), not INTEGRATED into any sealed arrow — the doc itself only claims "functional," not load-bearing.

### 2.4 Proof tools (engine-agnostic, spans both Python and Julia)

| Tool | Version | Level | Where |
|---|---|---|---|
| z3 (python `z3-solver`) | 4.16 | INTEGRATED load-bearing in `magma_smt_genuine`; SUPPORTIVE in ~13 arrows | `:29,79` |
| cvc5 | 1.3.3 | SUPPORTIVE dual-SMT cross-check, ~15 arrows | `:29,81` |
| sympy | 1.14 | INTEGRATED load-bearing, ~10 arrows (exact identities) | `:29,80` |
| `Z3.jl` (Julia) | 1.0.4 | AVAILABLE, not load-bearing in any sealed arrow | `:24,88` |

The two-SMT-engine pattern (z3 + cvc5 both `tried: true, used: true`) recurs across every arrow's `tool_manifest` — for example `finite_to_continuum_rung.json` and `law_order_branch.json` (both read this session) — but cvc5's own manifest entry in both explicitly disclaims mechanism-encoding: "Generic single-valued-function non-vacuity witness; NOT a mechanism encoding." This is the tool's own manifest declining a stronger claim than it supports — preserve this ceiling statement rather than smoothing it into "z3+cvc5 prove X."

### 2.5 Dynamics / topology / convex tools

All AVAILABLE per the doc, none load-bearing in a sealed arrow as of this session: `pysindy`/`pykoopman`/`PyDMD`/`derivative` (dynamics identification, Koopman/SINDy — named as intended "arbiter lanes," not yet built); `TopoNetX`/`gudhi`/`rustworkx`/`xgi`/`networkx`/`igraph` (topology); `cvxpy`/`cvxpylayers`/`diffcp`/`clarabel`/`osqp`/`scs`/`highspy` (convex, paired with unbound repo `qics`) (`:89`). Epistemic label: FUEL-proposal — the library→arrow map (2.8 below) names some of these for near-term wiring, but none has a committed arrow receipt yet.

### 2.6 Stress-probe lane — 7 probes, unofficial, capability-demonstrated only

Source: `sim_engines/stress/results/*.json` (7 files, all read this session). Every probe carries `"classification": "unofficial_stress_probe"` and `"promotion_allowed": false` — the doc's own claim ceiling, not this report's addition. None feeds a sealed arrow; each exists to demonstrate a library's capability before an integration decision.

| Probe | Key numbers | Unofficial label |
|---|---|---|
| `entropy_gradient_sweep_stress.json` | 3-way agreement (JAX/dynamiqs/Julia) max divergence `3.33e-16`; grad vs closed-form max divergence `3.63e-15`; 247,614 points/s on a 100,001-point sweep; `s_cond_min_bits=-1.0` at the Bell state | "engine exercise only — no manifold/axis/bridge claim; parks by definition" |
| `galois_field_ladder_probe.json` | GF(2^8) generator order = 255 (sympy-factored 3·5·17); subfield ladder GF(2^1..2^8) fixed-point counts exact (2,4,16,256); Frobenius freshman's-dream holds in-field, fails over Z (negative control) | "capability demonstration only — candidate role for algebra_ladder; not integrated into any arrow; parks by definition" |
| `diffrax_lindblad_cycle_probe.json` | time-dependent Lindblad (linear ω ramp) vs closed form: max divergence `4.82e-9`; vs dynamiqs mesolve: `4.81e-9`; negative control (frozen Hamiltonian) shows zero population drift vs `0.150` drift when dissipative — flips as expected | "capability demonstration only — diffrax time-dependent Lindblad solve, cross-checked exact; parks by definition" |
| `ott_w2_eigdist_probe.json` | Sinkhorn W2² on distinct eigenvalue clouds vs exact closed form: relative divergence `2.6e-4`; identical-spectra case converges to `5.7e-12` (near-zero, correct); negative control (distinct vs identical spectra) flips as expected | "capability demonstration only — ott-jax Sinkhorn W2 on eigenvalue clouds, exact-closed-form cross-checked; parks by definition" |
| `quantumclifford_orbit_probe.json` | exhaustive 2-qubit signed-Pauli enumeration: 435 pairs considered, 60 unique canonical stabilizer tableaux (matches sympy's closed-form count `2^n·∏(2^k+1)`); negative control (anticommuting pair) correctly excluded | "capability demonstration only — QuantumClifford stabilizer-tableau enumeration exercise; parks by definition" |
| `attractors_basins_probe.json` | Newton fractal on z³−1: 3 attractors found, matched to sympy exact roots to max distance `1.11e-16`; negative control z¹−1 correctly collapses to 1 basin | "capability demonstration only — Attractors.jl/DynamicalSystems.jl basin mapping cross-checked by sympy exact roots; parks by definition"; doc's own note: this is a capability "nothing else in the estate provides" |
| `itensors_mps_cut_probe.json` | GHZ-8 MPS cut entropy = 1.0 bit exactly (bond dim 2), matches closed form to 0 divergence; cross-checked against dense QuantumOptics GHZ-4 (divergence `2.22e-16`); negative control (product state) gives `9.6e-16` ≈ 0 bits | "capability demonstration only — ITensors/ITensorMPS bond-SVD entropy at an MPS cut, cross-checked by QuantumOptics dense + closed form; parks by definition" |

Epistemic label for all 7: FUEL-proposal / pre-admission evidence only. Per this repo's `tool_lego_fit_probe` convention, these do not satisfy canonical, bridge, QIT, GStack, axis, or nonclassical admission by themselves, and each receipt states its own ceiling explicitly.

### 2.7 CI seal state

Status: passes local rerun, this session. `python3 scripts/ci_three_engine_seal.py` → `three-engine CI seal: 35 receipt(s) pass, 0 REJECTED`. The 35 receipts are every `ratchet_contract/ratchetings/results/*.json` (15 files, matching the doc's 15-arrow list exactly) plus `system_v8/*/results/*.json` (20 files across `exceptional_binding`, `manifold`, `thermo_engines`, `tool_ledger`, `upper_manifold`), excluding files ending `_nvidia_referee.json` (`scripts/ci_three_engine_seal.py:16-26`).

What the seal enforces (`claimgate_plugin/three_engine_seal.py`, read in full this session): a receipt is admitted only if (A) it carries ≥2 authoritative engines (Julia/JAX/PyTorch — the code's `AUTHORITATIVE` tuple at line 30 also lists `pytorch` as an alias) each marked `load_bearing` in `tool_integration_depth` AND each carrying a numeric `engine_values` entry, those values agree within `1e-6` (recomputed from the values themselves, not trusted from a receipt field), and — outside CI's `SEAL_METADATA_ONLY` mode — the JAX leg is re-run fresh and reproduces its recorded numerics to `1e-9`; or (B) the receipt declares `engine_contract.numeric_engine_required=false` with a stated reason (the exemption path used by `finite_to_continuum_rung` and `law_order_branch`). Any receipt with numpy/scipy/mpmath labeled `load_bearing` is an absolute reject regardless of anything else (lines 93-96). A `load_bearing` engine whose own `engines_ran` field says `False` is rejected as self-contradictory metadata (lines 119-125) — a metadata-consistency check, not itself a re-execution.

The CI workflow (`.github/workflows/three-engine-seal.yml`, read this session) runs on every push/pull_request on GitHub's servers with `python-version: "3.12"` and no sim environment installed — it runs in `SEAL_METADATA_ONLY=1` mode, catching the numpy-presence and engine-agreement checks but skipping the jax-re-derive execution check (that re-derive is asserted, per the workflow's own comment at lines 1-7, to run locally via pre-commit + Stop hook). This assembly pass independently confirmed the GitHub Actions run itself: `gh run view 29969379442` returns `{"conclusion":"success","createdAt":"2026-07-23T00:32:48Z","headSha":"dcf4a500355d0399640e876fe78e1888889dcc40","status":"completed","workflowName":"three-engine seal (no numpy)"}` — the run tied to commit `dcf4a5003` completed successfully. This confirms the run-level outcome directly; it does not itemize the commit message's literal internal "9/9" job-count breakdown, and this session did not independently verify whether the local pre-commit/Stop hook genuinely invokes the jax-re-derive path outside `SEAL_METADATA_ONLY` mode — mark that half UNVERIFIED; what would settle it: reading `.git/hooks/pre-commit` or the Stop-hook script and confirming it invokes `three_engine_seal.py` without `SEAL_METADATA_ONLY` set.

Commit `dcf4a5003` (`git show --stat`, read this session) is confirmed an ancestor of the current session's `HEAD` (`git merge-base --is-ancestor dcf4a5003 HEAD` → true). Its message claims workflow "9/9" and seal "35 pass / 0 REJECTED"; this session's independent rerun reproduces the 35/0 figure exactly, and this assembly pass's fresh `gh run view` confirms the tied GitHub Actions run completed with conclusion `success`.

### 2.8 Library → arrow integration map (adopted vs rejected)

Source: `INTEGRATION_INVENTORY_AND_CAMPAIGN.md:123-126`, credited to an "NVIDIA deepseek draft, Claude-triaged." Epistemic label: FUEL-proposal — a ranked plan, not yet executed as sealed arrows (the stress-probe lane in the same section is offered as pre-admission evidence, explicitly not promotion).

**Adopted, ranked:**
1. `diffrax` → carnot + otto (time-dependent Lindblad cycles) — the doc claims this "clears 2 CI-reds + the open-system-dynamics capability gap." Checked against the current receipts: `diffrax` appears as `supportive` (not the ranked headline role) in `system_v8/thermo_engines/results/carnot_engine.json`'s `tool_integration_depth`, alongside `jax` and `julia` as the actual `load_bearing` engines. So the pairing was adopted and the CI-reds did clear (confirmed by commit `dcf4a5003` and this session's rerun), but diffrax's landed role is supportive, not the sole clearing mechanism — hold this as the more precise reading against the doc's shorthand.
2. `galois` → `algebra_ladder` (finite fields) — capability demonstrated in the stress probe (2.6 above); not present in `algebra_ladder.json`'s `tool_manifest` (`{cvc5, sympy, z3}` only, checked this session). Status: FUEL-proposal, not yet wired.
3. `diffrax` → `bures_to_fubini_study` (GKSL transport) — `bures_to_fubini_study.json`'s `tool_integration_depth` (checked this session) lists `cvc5, jax, julia, qutip, sympy, z3`, no diffrax entry. Status: FUEL-proposal, not yet wired, despite the arrow itself now being numpy-free and CI-green via jax/julia/sympy/z3/cvc5/qutip alone.
4. `ott-jax` → `real_vs_complex_tomography` (W2 Sinkhorn) — capability demonstrated in the stress probe; `real_vs_complex_tomography.json`'s `tool_integration_depth` (checked this session) lists `cvc5, jax, julia, sympy, z3`, no ott entry. Status: FUEL-proposal, not yet wired.
5. `QuantumClifford` → `magma_smt_genuine` (orbit enumeration cross-check) — capability demonstrated in the stress probe; `magma_smt_genuine.json` shows only `z3` load-bearing + `cvc5` supportive (checked this session). Status: FUEL-proposal, not yet wired.
6. `Attractors`/`DynamicalSystems` → `law_order_branch` + `finite_to_continuum_rung` (basins/Lyapunov) — capability demonstrated in the stress probe; both target receipts currently declare `numeric_engine_required=false` and run pure-symbolic (sympy/z3/cvc5 only, `jax=False, julia=False` in `engines_ran`, checked this session). Status: FUEL-proposal, not yet wired; note this pairing would move these two arrows from the symbolic-exemption class into the numeric-engine class if executed.

**Rejected, with stated reason** (`:125`): `netket`-NQS for `szilard` ("speculative research, not integration"); `quimb`-PEPS for the 2-qubit basis sim ("overkill"); `jax-verify` → `root_foundation` ("domain mismatch — finite/symbolic arrow").

Net reading: of the 6 adopted pairings, only pairing 1 (diffrax→thermo) shows up in a committed receipt's `tool_integration_depth`, and there it is `supportive` rather than the ranked headline role. Pairings 2–6 remain at capability-demonstrated (stress-probe) status, not integrated. This is a genuine gap between the "adopted, ranked" plan and the measured receipts — present as OPEN, not as completed integration.

### 2.9 Unbound repos (triage state, not integration)

Per `:32-38`, unclassified as of 2026-07-22: `qics` (conic solver, paired with the cvxpy stack), `deeptime` (Koopman/MSM), `auto_LiRPA` (NN verification bounds, pairs with jax-verify), `physlib`, `resclasses`, `codex-autoresearch`, `pysindy`/`pykoopman` source clones, the `leviathan-*` family + `lev` (Lev OS itself — a separately documented integration lane), `hermes-agent*`, `AnyFlow`/`flowm`/`lpwm`/`le-wm`/`Sana`/`Sofia`/`alco` (doc's own note: "unclear — inspect"), `stylegan3` ("likely out of scope"). All ABSENT from any sealed arrow; this report did not independently inspect these repos' contents this session — treat the doc's characterizations as unverified-by-this-session pending direct inspection.

### 2.10 M1 16GB engineering constraints

Per `:64`, target machine = M1 MacBook Pro, 16GB unified memory. Rules recorded (attributed to "the Gemini M1 survival rules, grounded" — an external-model-sourced constraint set, not independently re-derived by this report): sequential engine execution only (never JAX-Metal + PyTorch-MPS concurrently — named risk "swap-death"); JAX preallocation disabled (`XLA_PYTHON_CLIENT_PREALLOCATE=false`); half-precision perception models once PyTorch is used; roughly 4-6GB active RAM ceiling per stage; M1 unified-memory-architecture zero-copy described as "genuinely zero-copy" between engines sharing silicon. Epistemic label: CANON per an owner-adopted Gemini-chain verdict recorded at `:65` — the doc records that a full alternate "stack" proposal built around these constraints was REJECTED (cutting dynamiqs would break 4 working arrows; the proposed core included unintegrated pennylane/kingdon/V-JEPA2 and an env-incompatible PythonCall/DLPack bridge not in the carrier), while these specific M1 rules were kept.

### 2.11 Per-arrow wiring table (measured directly, this session)

Read from each arrow's result JSON (`ratchet_contract/ratchetings/results/*.json`) rather than the doc's own summary table, to catch drift since 2026-07-22 17:08 — the doc's own per-arrow table (`:94-111`) predates the `dcf4a5003` clearances for several rows. ● = load_bearing per `tool_integration_depth`, ○ = present but not load_bearing / control, — = absent from `tool_integration_depth` or engine not run.

| Arrow | JAX | Julia | torch | qutip | z3/cvc5/sympy | Seal (this session) |
|---|:--:|:--:|:--:|:--:|---|:--:|
| cut_dependent_entropy | ● | ● | ● | ○ | z3○ cvc5○ sympy● | pass |
| pure_to_vn | ● | ● | — | ○ | z3○ cvc5○ sympy● | pass |
| renyi_alpha_axis | ● | ● | — | ○ | z3○ cvc5○ sympy● | pass |
| vn_to_shannon | no `tool_integration_depth` field found on this receipt | same | — | ● (per doc, a minor inconsistency) | — | pass; jax/julia `engine_values` agree exactly (`0.5623351446188083` each) |
| bures_to_fubini_study | ● | ● | — | ○ | z3○ cvc5○ sympy● | pass, max cross-engine divergence `4.69e-8` |
| real_vs_complex_tomography | ● | ● | — | — | z3○ cvc5○ sympy● | pass, max cross-engine divergence `0.0` |
| extension_fibre_capacity | no `tool_integration_depth` field found on this receipt | same | — | — | — | pass; jax/julia `engine_values` agree exactly (`1.3862943611198906`) |
| vn_to_shannon_basis_relativity | ● | ● | — | — | none run (`engines_ran` False for cvc5/qutip/sympy/z3) | pass; jax/julia agree exactly |
| carnot_engine (v8) | ● | ● | — | — (`engines_ran.qutip=False`) | diffrax○ | pass, max divergence `1.19e-15` |
| szilard_engine (v8) | ● | ● | — | — | — | pass, max divergence `1.55e-14` |
| quantum_otto_engine (v8) | ● | ● | — | ○ | — | pass, max divergence `3.03e-9` |
| finite_to_continuum_rung | — | — | — | — | z3○ cvc5○ sympy● | pass — EXEMPT (`numeric_engine_required=false`) |
| law_order_branch | — | — | — | — | z3○ cvc5○ sympy● | pass — EXEMPT (`numeric_engine_required=false`) |
| algebra_ladder | — | — | — | — | z3○ cvc5○ sympy○ (all `supportive` per this receipt's own field) | pass — pure-SMT; `engines_ran` shows jax/julia/numpy all False |
| anticommutation_rung | — | — | — | — | z3, cvc5 present in `engines_ran` (True); no `tool_integration_depth` on this receipt | pass — pure-SMT |
| magma_smt_genuine | — | — | — | — | z3● cvc5○ | pass — pure-SMT |
| magma_to_semigroup | — | — | — | — | z3, cvc5, sympy present in `engines_ran`; no `tool_integration_depth` field | pass — pure-SMT |
| root_foundation | — | — | — | — | none of z3/cvc5/sympy ran; `python_stdlib=True` only | pass — pure combinatorial, no proof-tool intent flagged |

Discrepancy note against the doc's own per-arrow table (`:94-111`): that table, timestamped earlier in the same file, still shows `bures_to_fubini_study`, `real_vs_complex_tomography`, `extension_fibre_capacity`, `vn_to_shannon_basis_relativity`, and the 3 thermo sims as "RED numpy" / "RED no engine value." This session's direct receipt reads and the CI seal rerun both show all of these passing, numpy-free. Two textual states exist in the same document — the newer state (post-`dcf4a5003`, confirmed by fresh rerun) supersedes the older table, but the older table is still on disk unedited. Flag as OPEN doc-hygiene, not a live empirical divergence.

### 2.12 What remains OPEN / UNVERIFIED in this section

- Whether the local pre-commit / Stop hook genuinely invokes the jax-re-derive path of `three_engine_seal.py` (outside `SEAL_METADATA_ONLY` mode) — not independently checked this session; settled by reading the hook script directly.
- The claimed GitHub Actions "workflow 9/9" per-job figure from the `dcf4a5003` commit message — this assembly pass confirmed the run itself completed with conclusion `success` (`gh run view 29969379442`), but did not itemize the individual job count inside that run.
- The 6 unbound-repo triage characterizations the doc itself marks "unclear — inspect" (`AnyFlow`/`flowm`/`lpwm`/`le-wm`/`Sana`/`Sofia`/`alco`) — remain uninspected by this report.
- `galois`, `ott-jax`, `QuantumClifford`, `Attractors`/`DynamicalSystems`, and diffrax-as-load-bearing-for-`bures_to_fubini` are all at stress-probe / capability-demonstrated status only — none is wired into a sealed arrow's `tool_integration_depth` as of this session's reads, despite the "adopted, ranked" framing in section 2.8. Do not read the map's "adopted" language as "integrated."

### Absent / unverified (index)

- Local pre-commit/Stop hook invocation of the jax-re-derive seal path (outside SEAL_METADATA_ONLY) — not read this session.
- GitHub Actions per-job "9/9" breakdown for the run tied to commit dcf4a5003 — run-level `success` now confirmed (`gh run view 29969379442`, this assembly pass), but the internal job count was not itemized.
- Contents of the ~6 unclear unbound repos (AnyFlow/flowm/lpwm/le-wm/Sana/Sofia/alco) — doc itself flags these as uninspected.
- qics, deeptime, auto_LiRPA, physlib, resclasses, codex-autoresearch repo contents — not opened this session.
- Whether galois/ott-jax/QuantumClifford/Attractors adoption in the library-map has since been wired into any arrow after this session's read timestamp.

---

## 3. ClaimGate — spec, components, implementation level, holes

### Mission

Owner north star (session-memory record of a recurring 2026-07-20/22
directive, cross-referenced against the two repo citations below): "put LLMs
in deterministic boxes — gates and hooks they can't control, less likely to
hack." Target is stated as hack-resistance, not unhackability.

The threat model an LLM has against a gate is framed as four moves. Two are
verbatim in repo comments; the other two are implemented but not enumerated
together in one repo doc (UNCERTAIN — would be settled by the owner adding a
single `THREAT_MODEL.md`):

1. **EDIT the gate** — gate code/policy must sit outside the constrained
   agent's write access. Repo-verifiable partial implementation: `gate_registry.json:2`
   ("The producing agent must NOT be able to write this file… in production:
   branch-protected / CODEOWNERS / harness-owned path") and its
   `TRUST_ROOT_BOUNDARY` note (quoted verbatim below) admitting this is NOT
   yet true in the current repo.
2. **FAKE the input** — `CLAIMGATE_POSTMORTEM_20260722.md:11-13` names this
   verbatim: "**Class:** fake-input (threat move #2)." The fix cited there:
   `three_engine_seal.py` re-runs the jax leg instead of trusting
   `engines_ran`.
3. **SKIP the gate** — `hooks/pre_commit_gate_receipts.sh:4` names this
   verbatim: "ClaimGate's threat model, move #3: an LLM can SKIP a gate it
   must CALL, but it [cannot skip a gate the HARNESS FIRES]." Implemented as
   a git pre-commit hook, not a called function.
4. **LOGIC GAP** — the gate's own logic is tested against planted bypasses.
   Repo evidence: `gatecheck.mjs` (a meta-gate over `claimgate.mjs`/`archfence.mjs`/
   `hammer.mjs`, exit 0 `GATE_ACCEPTED` / 3 `GATE_UNTRUSTED` / 1 else,
   `gatecheck.mjs:127`) plus the hostile-control fixture corpus below, which
   `CLAIMGATE_POSTMORTEM_20260722.md` miss #6 names as "the next ClaimGate
   deliverable."

Epistemic label: FUEL-proposal for the unified "4-move" framing (owner
directive, not yet written as a single repo doc); CANON per repo comments for
moves #2 and #3 individually; the code implementing all four is `runs` (see
component table).

### Component-by-component table

All exit-code behavior below was re-verified this session by reading the
named source and, where marked "passes local rerun," by fresh execution
(`bash claimgate_plugin/fixtures/hostile/run_hostile_controls.sh`, exit 0,
"RESULT: no drift — all gate exits match recorded actuals" — full output
transcribed in the hostile-corpus section).

| Component | Role | Status ladder | Integration | Exit codes |
|---|---|---|---|---|
| `claimgate_plugin/claimgate.mjs` | tier0 receipt linter (R1 verdict-inflation, R2 claim-without-evidence, R3 baseline-honesty, R4 preregistration, R5 recompute) + `admit-module` (G1-G5 near-duplicate/inventory gate) | passes local rerun (this session) | load_bearing (fires inside `post_receipt_gate.sh` and `claim_verify.py` tier0) | `lint-receipt`: 0 ADMISSIBLE, 1 REJECTED, 2 malformed. `admit-module`: 0 ADMIT, 3 PARK_FOR_REVIEW, 1 REJECT, 2 error |
| `claimgate_plugin/three_engine_seal.py` | hard structural seal: numpy/scipy/mpmath may never be `load_bearing`; a numeric claim needs >=2 authoritative engines (`julia`/`jax`/`torch`/`pytorch`) each `load_bearing` with an agreeing numeric `engine_value`, and the `jax` leg must re-run and reproduce its recorded values to `1e-9` | passes local rerun (this session, via `post_receipt_gate.sh` calls in the corpus run) | load_bearing (hard-fails `post_receipt_gate.sh`) | 0 pass, 1 REJECT, 2 usage/parse error (both non-zero fail closed per the calling hook) |
| `claimgate_plugin/claim_verify.py` (v2) | tier dispatcher, tier0-tier4, policy sourced from `gate_registry.json` external to the receipt; rejects a receipt that declares its own `verification.*.cmd`; tier4 requires an exact `verdict: CLEAN` token, an `auditor:` identity different from the producer, and a fresh `evalcheck.mjs` calibration against a sealed deck; hash-pins the sibling `AUDIT_VERDICT.md` before any tier runs (cross-tier bootstrap guard) | passes local rerun (this session) | load_bearing (fired from `post_receipt_gate.sh`) | 0 VERIFIED, 1 REJECTED, 2 usage/IO, 3 INSUFFICIENT_DEPTH |
| `claimgate_plugin/gate_registry.json` | external policy: `claim_kinds` → `required_tiers`; `gates{cmd,result_path,expect}` (tier2/3 argv, never receipt-declared); `audit_policy.calibration_gates` | exists (data, consumed by `claim_verify.py` runs above) | supportive (policy source, not code) | n/a |
| `claimgate_plugin/hooks/post_receipt_gate.sh` | fired-side composition: `claimgate.mjs` → `three_engine_seal.py` → `claim_verify.py` → (conditionally) `ratchet_floor.py`; advisory `suggest.mjs` runs best-effort on any non-clean exit but never alters the gate's own exit | passes local rerun (this session) | load_bearing | propagates `claim_verify`'s exit (0/1/2/3); overrides to 1 on `three_engine_seal` non-zero; floor exit 1/2 overrides, floor exit 3 (PARK, unknown key) is benign and preserved |
| `claimgate_plugin/hooks/pre_commit_gate_receipts.sh` | git-level fired hook (closes threat move #3): scans staged `ratchet_contract/`, `system_v8/`, `fuel_gate/` `results/*.json` for a `verdict`/`classification` field, runs `post_receipt_gate.sh` per file | exists / runs (wraps `post_receipt_gate.sh`, which was fresh-run this session; the git-staged-file-diff logic itself was read, not executed, this session) | load_bearing when `install_git_hooks.sh` has installed it as `.git/hooks/pre-commit` | 0/3 allow commit, 1 blocks commit, other exit warns without blocking |
| `claimgate_plugin/claim_admission.mjs` | CR-side ENVELOPE check for the serialized transport canary — non-final; re-hashes every artifact from disk, checks the digest chain, the z3 proof-status axis, Gate M1 binding, and mock quarantine | passes local rerun (this session) | load_bearing (terminal node of the canary's `.lev` flow) | 0 envelope-sound, 3 PARKED, 1 REJECTED |
| `claimgate_plugin/ratchet_floor.py` | monotone floor comparator ("constraints only tighten") | passes local rerun (this session, via `post_receipt_gate.sh`) | load_bearing when a receipt carries `floor_claims` | 0 ADMITTED, 1 REJECTED (regression/direction tamper), 2 IO, 3 PARKED (unknown key, needs `--allow-new-keys`) |
| `claimgate_plugin/suggest.mjs` | advisory-only fix-generator; never gates; its own exit/output is discarded by the calling hook | runs (invoked as best-effort advisory during this session's corpus rerun) | supportive, explicitly non-gating | n/a to the gate decision |
| `sim_engines/serialized/serialized_stage.py` + `run_spine.sh` + `.lev/flows/cr-serialized-physics.flow.yaml` | the transport canary spine: `julia → jax → pysindy → z3 → claim_admission`, tombstone-and-boot (each stage its own process, re-hashes the prior artifact from disk), packet mode for wrapping real CR packets unchanged | exists (read this session; not freshly executed — the hostile-corpus ledger fixtures encode its output schema but were pre-built, not generated fresh here) | load_bearing to the canary; EXPLICITLY not load-bearing to physics (see claim ceiling below) | stage script: 0 stage bound, 1 fail-closed abort, 2 usage |
| `sim_engines/serialized/test_ratchet_mask.py` | independent structural re-verification of the Julia carrier-calibration Arrow mask (16×16 torus adjacency: symmetric, zero-diagonal, degree-4, periodic, bipartite) — run by `serialized_stage.py` before trusting the julia stage's own exit code | exists (read; not executed this session) | load_bearing (referenced explicitly: "exit code 0 + file-exists is not evidence") | 0 all assertions hold, 1 any failure |
| `claimgate_plugin/fixtures/hostile/*` + `run_hostile_controls.sh` | the hostile-control fixture corpus and its drift-check runner (this is the acceptance suite for every row above) | passes local rerun (this session, fresh execution, see below) | load_bearing as regression, not as a live gate | runner: 0 no drift, 1 drift detected or unreadable fixture |
| `claimgate_plugin/lev_patch/claim-admission.ts` + `index.ts` | proposed Lev-native `physics.claim-admission` capability | KILLED / WITHDRAWN (2026-07-22, by the file's own header) | none — not implemented, not wired | n/a |

### The seal contract, precisely (`three_engine_seal.py`)

Transcribed from the docstring and `check()` (`claimgate_plugin/three_engine_seal.py:1-176`):

A sim receipt is admitted only if ONE of:
- **(A) EVIDENCE** — it carries `>=2` authoritative engines (`julia`/`jax`/`torch`/`pytorch`) that each have a `load_bearing` label in `TOOL_INTEGRATION_DEPTH` AND a numeric `engine_values.<engine>_*`; those values AGREE (`max(abs(a-b)) <= 1e-6` across the verified set, recomputed here, not trusted); AND the `jax` leg is re-run (`<receipt_stem>_jax.py` next to the receipt) and reproduces its recorded numeric fields to `<1e-9`.
- **(B) EXEMPT** — `engine_contract.numeric_engine_required == false` with an `exemption_reason`.

Everything else REJECTS: `numpy`/`scipy`/`mpmath` labeled `load_bearing` (absolute, checked first); a load-bearing engine whose `engines_ran` flag says `False` (contradiction, rejected on its face); fewer than 2 verified engines; disagreeing engine values; a `jax` leg that will not re-run, produces no JSON, or does not reproduce; an unreadable receipt (fails CLOSED, exit 1). `SEAL_METADATA_ONLY` env var skips only the jax re-run step (for CI without the sim env) — the numpy-ban and agreement checks still run unconditionally. Exit: 0 pass, 1 REJECT, 2 usage.

### The transport canary + status axes

`sim_engines/serialized/serialized_stage.py` and its bound flow
`.lev/flows/cr-serialized-physics.flow.yaml` implement "tombstone-and-boot":
each stage (`julia`, `jax`, `pysindy`, `z3`) runs as its own process, re-derives
the prior stage's artifact digest from disk before running (never trusts the
ledger), writes its own immutable artifact, and exits. Chain invariant:
`SHA256(input_artifact_on_disk) == output_digest` recorded by the prior stage
(`serialized_stage.py:17-18`).

Claim ceiling, quoted verbatim from the flow file's header
(`.lev/flows/cr-serialized-physics.flow.yaml:1-7`): "this flow proves
transport properties ONLY — process tombstoning, atomic artifacts, re-derived
digest chain, negative-science routing … and mock quarantine … It emits NO
scientific claims and is not 'Phase 1 of the physics.'"

Three status axes are kept separate and never collapsed (this is the direct
fix for postmortem miss #3, "status-axis collapse"):
- `execution_status` — `COMPLETED` / `INFRA_ERROR`. Reserved for process-level
  success; a scientific negative result is still `COMPLETED`.
- `scientific_status` — `SUPPORT` (real payload) / `INCONCLUSIVE` (mock
  payload) / `COUNTEREXAMPLE` (a SAT proof or a crosscheck stage reporting
  `counterexample: true` in packet mode).
- `proof_status` (z3 stage only) — `UNSAT` / `SAT` / `UNKNOWN` /
  `NOT_APPLICABLE`.

A SAT result is explicitly a **preserved counterexample**, not a crash: with
`--force-fail`, `serialized_stage.py` sets `proof_status="SAT"`,
`scientific_status="COUNTEREXAMPLE"`, and still exits 0 ("it must REACH
admission; nonzero exit is for infra failure only",
`serialized_stage.py:78-79`). `claim_admission.mjs` then REJECTS (exit 1) that
SAT receipt with the line "proof is SAT: a counterexample EXISTS and its
receipt is preserved as completed negative science. Admission refused;
evidence retained for evaluation." (`claim_admission.mjs:83-86`) — rejected as
an admission, but the receipt itself reached the envelope check intact rather
than being lost as a tool error.

Mock quarantine: any stage not listed in `SPINE_REAL` writes `payload:"mock"`;
`claim_admission.mjs` PARKS (exit 3) if any stage is mock, regardless of how
clean the chain otherwise is (`claim_admission.mjs:110-117`) — "mock stages
prove the spine, never the physics."

### The hostile-control fixture corpus — 10 fixture files, 11 named classes, 7 HOLDS / 3 GAP

`CLAIMGATE_POSTMORTEM_20260722.md` miss #6 names 11 classes: digest mutation,
missing parent, renamed metric, stale policy, duplicate JSON key, NaN,
timeout, solver UNKNOWN, solver SAT, false self-report, human override.
**ABSENT**: `false self-report` has no fixture file anywhere under
`claimgate_plugin/fixtures/hostile/` (verified: no `false_self_report` or
"self_report"-named file in the repo) — it is named as a target class in the
postmortem but not yet built as a fixture. 10 `*.expected.json` files exist
for the other 10 classes; `missing_parent` internally runs two ledger
scenarios (r1: first stage absent; r2: middle stage absent) but is recorded
as one class/one file.

Fresh rerun this session (`bash claimgate_plugin/fixtures/hostile/run_hostile_controls.sh`):

```
class | expected_exit | actual_exit | status | drift?
digest_mutation | 1 | 1 | HOLDS | no-drift
duplicate_json_key | 1 | 0 | GAP | no-drift
human_override | 1 | 1 | HOLDS | no-drift
missing_parent | 3 | 3 | HOLDS | no-drift
nan_values | 1 | 1 | GAP | no-drift
renamed_metric | 3 | 0 | GAP | no-drift
solver_sat_counterexample | 1 | 1 | HOLDS | no-drift
solver_unknown | 3 | 3 | HOLDS | no-drift
stale_policy | 3 | 3 | HOLDS | no-drift
timeout_hang | 1 | 1 | HOLDS | no-drift
RESULT: no drift — all gate exits match recorded actuals.
```
7 HOLDS (digest_mutation, human_override, missing_parent,
solver_sat_counterexample, solver_unknown, stale_policy, timeout_hang) / 3 GAP
(duplicate_json_key, nan_values, renamed_metric) — status: passes local rerun
(this session), matching every recorded `actual_exit` in the individual
`*.expected.json` files with zero drift.

The 3 GAP classes, verbatim from their `*.expected.json`:

**1. `duplicate_json_key`** (`fixtures/hostile/duplicate_json_key.expected.json`)
— "Confirmed exploitable, GAP on every stage." A JSON object carrying the
same key twice (`all_pass` then `classification`) is parsed last-wins by both
`node JSON.parse` and `python json.load`; none of `claimgate.mjs` (tier0),
`three_engine_seal.py`, `claimgate.py` (claim_verify's own tier0), or
`claim_verify.py` inspects raw bytes for repeated keys. Decisive fixture
(`duplicate_json_key_laundered_pass.json`): first-occurrence values read
`all_pass:false`, `classification:hostile_control_fixture` (a failing,
corpus-marked receipt); last-occurrence values read `all_pass:true`,
`classification:scratch_diagnostic` — the full chain reaches **VERIFIED, exit
0**. Hardening recommendation on record but not applied: a shared
duplicate-key-rejecting parse (`object_pairs_hook`-style) across every gate.

**2. `nan_values`** (`fixtures/hostile/nan_values.expected.json`) — "The gate
has no NaN defense on the recompute contract." Root cause named precisely:
in `claimgate.mjs` R5, `Math.abs(got - claimed) > tol` is `false` when `got`
is `NaN` (JS NaN comparisons are false), so a NaN recompute counts as a
MATCH; `null` coerces to `0` in `mean`/`sum`, so an all-null raw array
"matches" a claim of `0.0` and also satisfies R2 provenance. The recorded
`actual_exit 1` on the shipped fixture is an artifact of the mandatory
corpus-marker classification failing an unrelated allowlist check, not NaN
detection — the same NaN payload under an allowed classification runs the
full chain to exit 0 VERIFIED (documented as a counterfactual, not shipped as
a fixture). A second variant (bare `NaN` literal, invalid JSON) reads
`HOLDS_AT_CHAIN_LEVEL_ONLY` — it is blocked only because node's `JSON.parse`
rejects the token before python's more permissive `json.load` (which accepts
bare NaN as `float('nan')`) ever gets a turn; `claim_verify.py` invoked
directly on the same bytes with no recompute contract exits 0 VERIFIED. Fix
direction on record, not applied: a `Number.isFinite` guard on recompute
inputs, mirroring the fix already applied to `ratchet_floor.py`.

**3. `renamed_metric`** (`fixtures/hostile/renamed_metric.expected.json`) —
three named gaps. (1) **Park is non-gating**: `ratchet_floor.py` correctly
PARKS (exit 3) a receipt whose locked floor key `acc` (floor 0.8,
higher_is_better) vanished via rename to `acc_v2` carrying a regressed value
(0.31), with a rename hint (`nearest_existing_key: acc`, `similarity: 0.5`)
— but `post_receipt_gate.sh` treats floor-exit-3 as benign and the fired
chain exits **0** on the only channel a harness consumes. (2) **Container
rename is fully silent**: `post_receipt_gate.sh` only fires the floor stage
when the receipt's own `floor_claims` key is truthy (`hooks/post_receipt_gate.sh:59`); nothing
cross-checks the store's locked keys against the receipt, so renaming the
container key (`floor_claims → floor_claims_v2`) bypasses floor enforcement
entirely with zero floor output and exit 0. (3) **The advisory layer
launders the rename**: quoted verbatim from the fixture — "suggest.mjs
responds to the park by recommending 'pass --allow-new-keys to admit'
(against the default store it even calls acc_v2 'a genuinely new floor
metric')." Cross-check against `suggest.mjs:409-426` (this session): the
suggestion tool DOES carry a similarity-based guard (`sim >= 0.5` steers to
"do NOT pass --allow-new-keys… rename-evasion path"), and 0.5 meets that
threshold against the fixture's own custom `RF_STORE`; the fixture's note
that the laundering path fires "against the default store" is not something
this session re-derived independently — the two readings (guard fires on the
fixture's declared store vs. laundering fires only on an unregistered
default store lacking the `acc` key) are BOTH live and not adjudicated here;
report both, do not collapse. Fresh rerun this session confirms the
top-line exit-0 GAP (`renamed_metric | 3 | 0 | GAP | no-drift`) independent of
that sub-question.

Two additional caveats surfaced inside the nominally-HOLDS classes, verbatim:
`solver_sat_counterexample.expected.json` gap_note — `claim_admission.mjs`
HOLDS, "but the tier0/claim_verify side has NO SAT-as-negative-science axis…
a solver-SAT counterexample routed through tier0 lint or the tier ladder
instead of the envelope check has no vocabulary to preserve it." Same
structure in `solver_unknown.expected.json` for the UNKNOWN axis. These are
real, narrower gaps inside classes whose top-level verdict is HOLDS — the
corpus's own text distinguishes the envelope-check path (HOLDS) from the
older tier-ladder path (gap), and both readings are preserved here rather
than folded into either the HOLDS or GAP tally.

### The withdrawn `physics.claim-admission` capability

`claimgate_plugin/lev_patch/claim-admission.ts:1-16` (header, verbatim):
"WITHDRAWN 2026-07-22 (webui audit) — do not implement as written… This
proposed a FINALIZING physics.claim-admission capability: one function that
interprets the proof, decides truth, and writes canon. The audit rejects
that collapse: Lev claim admission is deliberately NON-FINAL; truth
evaluation belongs to core/eval… settlement is a separate later policy
layer. The invented `registerCapability` / `@lev-os/flowmind-types` surface
also does not exist — the real native seam is `lev.call` (currently a
design-doc span name, not yet wired)." `lev_patch/index.ts` (the registration
shim) depends on that same non-existent registry API and is withdrawn with
it. Epistemic label: KILLED. This is postmortem miss #4 ("authority
collapse") named and closed by demotion, not by a working replacement — the
replacement is composition (below), not a second finalizing gate.

### Trust-root open finding (agent-writable)

`gate_registry.json:22-29`, `audit_policy.TRUST_ROOT_BOUNDARY`, quoted
verbatim: "This registry + the sealed decks + evalcheck.mjs are the trust
root. They MUST live on a path the producing agent cannot write
(branch-protected / CODEOWNERS / harness-owned). In the current repo
they do NOT — so 'external policy' is only real once relocated. claim_verify
reports their hashes so tampering is at least detectable; it cannot
self-enforce its own immutability." `FIXTURE_CORPUS.md:95-98` restates this
as an open item from the 2026-07-20 wide-stress workflow: "TRUST-ROOT
BOUNDARY (open, deployment-level): gate_registry.json + evaldeck + the
fixtures live in the agent-writable repo today." Status: OPEN. Nothing in
this session's reading or rerun closes it — the tier4 audit-calibration
mechanism (`_auditor_calibrated`, `claim_verify.py:169-189`) re-derives
calibration per run instead of trusting a static file, which narrows but does
not eliminate this gap, since the registry and sealed decks themselves remain
on an agent-writable path.

### Composition doctrine (never one gate)

Stated as the CR-side envelope check's own scope note,
`claim_admission.mjs:6-12` (verbatim): "A complete hash chain proves
provenance and byte identity ONLY; it never proves the mathematics. Truth
evaluation belongs to Lev core/eval, and settlement to the later policy
layer. This check is one composable link: CR stage execution → CR envelope
check (THIS) → Lev effect persistence → non-final claim intake → core/eval →
policy → settlement. It must never become a self-certifying gate."
`CLAIMGATE_POSTMORTEM_20260722.md`'s closing section states the same
doctrine as an owner directive: "ClaimGate is not a fork and not inside Lev:
it overlays a pure current lev-os/leviathan install," naming the CR-side
overlay (`three_engine_seal` + envelope check + hooks, exists) and the
Lev-side seam (a registered eval contract in `core/eval`, described as
existing upstream in `~/lev-main` per `LEV_ATTACH_MAP_20260722.md`, with the
CR eval-pack work "now orphaned in ~/lev-main" pending re-apply as a patch,
not assumed live). `LEV_WIRING.md` documents a second, independent
composition leg: `lev_steering_producer.py` renders a `post_receipt_gate.sh`
run into a five-file source projection that Lev's `orchestration
claimgate-steering consume` independently recomputes host-side (verdicts
`host_consumed` / `host_reviewed_failed` / `host_blocked`) — "a source
projection cannot self-promote." Both legs (the git-fired local hook and the
Lev host-recompute) are stated as enforcing the same underlying gate,
neither superseding the other.

### What this session did not verify

- The transport canary's live spine (`serialized_stage.py`, `run_spine.sh`,
  `catlab_ratchet.jl`, `test_ratchet_mask.py`) was read but not freshly
  executed this session — julia/pyarrow dependencies were not invoked;
  status is `exists`, not `runs`, for those four files specifically.
- Whether the Lev-side `core/eval` CR evaluator pack (`plugins/sim-witness/evals/cr_constraint_battery/`)
  is currently live in `~/lev-main` was not re-checked this session; treat
  `LEV_ATTACH_MAP_20260722.md`'s account as the most recent record, not
  re-verified here.
- The `renamed_metric` "against the default store" claim (above) is reported
  as written in the fixture; this session did not independently re-run
  `suggest.mjs` against an unregistered default store to adjudicate the
  apparent tension with the guard code at `suggest.mjs:416`.

### Absent / unverified (index)

- `false_self_report` hostile fixture: named as an 11th class in `CLAIMGATE_POSTMORTEM_20260722.md` miss #6 but no fixture file exists under `claimgate_plugin/fixtures/hostile/` — ABSENT, not built.
- A single repo document enumerating all 4 threat-model moves together does not exist; moves #2 and #3 are named verbatim in code comments, moves #1 and #4 are implemented (`gate_registry.json` TRUST_ROOT_BOUNDARY note; `gatecheck.mjs` + hostile corpus) but not numbered in-repo — the unified framing is sourced from session memory, not a repo citation.
- Whether `suggest.mjs`'s rename-evasion guard (`sim>=0.5`, `suggest.mjs:416`) actually contradicts or is consistent with the `renamed_metric` fixture's "against the default store" laundering claim was not adjudicated this session — both readings reported, live.
- Live execution state of `sim_engines/serialized/serialized_stage.py`, `run_spine.sh`, `catlab_ratchet.jl`, and `test_ratchet_mask.py` this session: not run (julia/pyarrow legs not invoked); status is exists/read only, not runs.
- Current live status of the Lev-side `core/eval` CR evaluator pack (`plugins/sim-witness/evals/cr_constraint_battery/`) in `~/lev-main` was not re-checked this session; relying on `LEV_ATTACH_MAP_20260722.md`'s prior account.
- `gates_manifest.json` / `gatecheck.mjs`'s own 10/10 pass claim was not re-run this session (only grepped for exit-code shape) — cited as exists/runs, not passes-local-rerun.

---

## 4. The Ratchet — spec and implementation level

### 4.1 Owner doctrine (epistemic label: CANON, outranks everything below)

`ROOT/ROOT_CARD.md` states its own authority: "This directory holds OWNER VERBATIM only. It outranks every spec, pack, wiki concept, memory file, and machine-generated draft in this repository" (`ROOT/ROOT_CARD.md:3-5`). Quoted owner content (`ROOT_CARD.md:9-31`, sourced to `OWNER_VOICE_ratchet_core_20260704.md`):

- Identity: "mss, ratchet, tower, nesting, nested ratchet, replicators... are all the 'same thing' stated in different ways. the MSS has minimal evolving persistent structure. it ratchets, it nests, it replicates" (line 9-11).
- The nesting law: "the ratchet is actually NESTED. where each thing sits on the thing before... everything runs with probes if it is MSS. though there might be deeper MSS under them. and they run on that. then all the math is CONSTRAINED by the previous rungs" (line 15-19).
- The chain: "the weyl spinor is on nested hopf tori, and that is on s2 and that on s3. and maybe with more intermediary steps and more depths going both ways" (line 20-21).
- The driver: "constraints with time and exploration/randomness/'heat' leads to attractor basins" (line 22-23).
- The root substance: "entropic monism is central... there is only one kind of substance — constraint on distinguishability. Identity is not primitive; it emerges from indistinguishability under probes (a=a iff a~b)" (line 26-28).

The card names its own "corrections this card forces" (`ROOT_CARD.md:52-62`): MSS is never "a mere gate" or a bare acronym — the owner's words define it, and machine refinements (a weakest-survivor-gate search discipline) are downstream candidates, never replacements. It states explicitly: "The kernel/pawl/purgatory vocabulary of the July pack lineage is machine draft, not owner spec. Usable as engineering, never citable as doctrine" (line 59-60). Everything from 4.2 onward is that engineering, read against this doctrine, not a restatement of it — this framing is repeated in `MODEL_DOSSIER/06_RATCHET_MECHANICS.md:24-37`.

### 4.2 Process specification (`system_v7/constraint_core/RATCHET_SPEC.md`, v0.5 — process authority, not owner doctrine)

The compact law (`RATCHET_SPEC.md:9-18`): "Root only in constrained distinguishability. Propose structures, gates, subgates, orders, gradients, weakness relations, and controls freely. Execute finite populations. Admit only a packet-relative MSS antichain supported by a witnessed entropy–geometry coface gradient. Preserve every alternative and death. Nothing about list order is canon." F01 (finitude), N01 (noncommutation), MSS (weakest current survivor), and T01 (grouping pressure) are named explicitly as "active pressures... hypotheses under test" (`RATCHET_SPEC.md:30-41`) — the spec's own statement that these axioms are not themselves ratcheted; they are the fixed floor the ratcheting runs against.

Comparison unit is nested, never flat: entropy and geometry are one finite coface, `C_D(pi) = {(x,y) in D : pi(x)=pi(y)}`, `L_D(pi) = |C_D(pi)|` (`RATCHET_SPEC.md:66-68`), explicitly "not a scalar payload running on a prior geometry" (line 76). MSS is defined by partition-coarseness only, never a global minimum: `pi ⪯ rho` when every block of `rho` lies inside a block of `pi`; `Surv(D) = {pi : L_D(pi)=0}`; `M(D) = min_⪯ Surv(D)` may contain incomparable members, and "the engine never chooses one by taste" (`RATCHET_SPEC.md:140-153`). No maximality is asserted — rival weakness relations (categorical, computational, resource, predictive, dynamical preorders) are named "live digs," not settled (line 155-156). Chain extension as valid progress without comparison is explicit: an admitted presentation "can later be weakened, split, internally rebuilt, demoted, or killed without deleting its historical receipt" (line 57-58); two branches inducing the same partition digest "re-merge... convergence is basin evidence... it does not canonize one path" (line 110-111). "No tooth becomes scientific manifold canon from a generated process fixture" (line 177).

Later sections (`RATCHET_SPEC.md` §14-15, v0.6/v0.7 amendments) add a preservation law: "byte preservation" (artifacts remain present or are explicitly listed absent) plus "semantic surfacing" (every live branch, negative, conflict, and audit reversal must be discoverable from the front door) (`RATCHET_SPEC.md:328-333`).

Status: exists; passes local rerun by its own self-test (4.3). Epistemic label: process-authority for this bundle's own engine — explicitly a machine formalization measured against `ROOT_CARD.md`, not a replacement for it (`system_v7/constraint_core/CLAUDE.md` banner, `RATCHET_V0_5_ORDER_OPEN_PROCESS`).

### 4.3 Kernel implementation state

The v0.5 engine lives at `system_v7/constraint_core/ratchet/ratchet_engine.py`; `ratchet/ratchet_kernel.py` is a two-line compatibility shim re-exporting from it (`ratchet_kernel.py:1-19`, read directly this session). Its documented self-test run (`RATCHET_SPEC.md:209-235`) reports: 81 finite generated rows, 32,400 parameter proposals executed, 3,147 actual behavioural partition classes, 29,253 parameter aliases exposed, 75 ordered gate/decomposition schedules, 44 distinct intermediate trajectories, 1 distinct final packet frontier, 0 scientific manifold layers admitted. `MODEL_DOSSIER/06_RATCHET_MECHANICS.md` table 1 independently reruns this in a prior session: "Self-test, passes local rerun (fresh, this session: `PASS order_open_ratchet_v0_5`). Runs on generated combinatorial fixtures only; has never called Julia, JAX, or PyTorch."

On the memory-recalled claim "FIRST GREEN 146/0/0": present on disk, but not what the recalled framing implies. `system_v7/constraint_core/bundle_manifest.json:867` (`validation_environment.audited_input_harness_receipt`) records `{"pass": 146, "fail": 0, "skip": 0, "environment": "source archive owner environment"}` — an externally-claimed number from a prior input archive. The same manifest states: "The 129 input's front door reported 146/0/0 in a fuller environment but shipped no matching top-level report" (`bundle_manifest.json:850`; repeated verbatim in `00_START_HERE.md:15` and `docs/BUNDLE_GUIDE.md:12`). What this container actually reran and can stand behind is different: `validation_environment.local_fast_harness` = `{"pass": 152, "fail": 0, "skip": 0, "green": true}`, stamped 2026-07-12 03:00 UTC (`bundle_manifest.json:858-864`; `00_START_HERE.md:15`). A third figure exists for the legacy full aggregate harness: `python3 run_all.py` returns 109 pass / 4 fail / 33 skip (`archive/RATCHET_V0_2_UPGRADE_REPORT.md:97`), which `CLAUDE.md`'s own hard rules name as honestly red and not to be edited toward green.

Three distinct counts, three distinct harnesses: order-open kernel self-test = PASS; local_fast_harness = 152/0/0 (stamped, locally reproducible); legacy `run_all.py` = 109/4/33 (honestly red). "146/0/0" is present but is provenance from another environment with no matching receipt in this repo, not an independently verified figure here. This session did not re-execute any of the three harnesses fresh — all three counts are read from stamped receipts on disk. Status: `146/0/0` = exists (unverifiable external claim); `152/0/0` = passes local rerun (per the stamped receipt, not re-confirmed this session); `109/4/33` = passes local rerun (declared honestly red, per the same stamped receipt).

### 4.4 The execution contract (`ratchet_contract/`) — gates, MSS, frontier, purgatory

`ratchet_contract/README.md:1-7`: "This is fuel-adjacent infrastructure, not the ratchet itself... so executable candidates can be compared with zero LLM judgment." Six gates (`ratchet_contract/gates.py`): `buildability_gate`, `probe_validity_gate`, `IDENTITY_GATE` (`pi_probes == pi_reidentify` → PASS — the executable form of `a=a iff a~b`), `persistence_gate`, `evolvability_gate`, `extension_gate`, and `adequacy` (their AND). `ratchet_contract/mss.py` computes `pairwise_mss` and `frontier` from partition-coarseness alone (`_partition_coarser`), never a score. `frontier()` builds a fresh `purgatory: list[dict]` on every call (`mss.py:240-278`, read directly) — each entry carries an immutable failure stage and a named `re_entry_condition` string (`mss.py:250,265,278`; conditions defined in `_RE_ENTRY_CONDITIONS` at `mss.py:85`).

Independently adversarially audited (`ratchet_contract/results/AUDIT_VERDICT.md`, dated 2026-07-20, read directly): "CONTRACT V0 AUDIT: CLEAN — MSS is pure partition_coarser (no smuggled score), the IDENTITY_GATE FAIL is behaviorally earned, gates flip on constructed inputs, the kernel is a faithful port, no verdict is LLM-judged or hardcoded," against 6 named attacks, all `found_fabrication:false`, with two low-severity findings (F1: dead negative-control scaffolding, F2: under-shown FAIL branches) named and fixed the same day. `ratchet_contract/bridge_validation/results/AUDIT_VERDICT.md` reports the same pattern for the two bridges, with 2 non-fatal caveats carried forward (see 4.6), per `MODEL_DOSSIER/06_RATCHET_MECHANICS.md:147`, not re-read verbatim this session. Status: passes local rerun (`ratchet_contract/results/selfcheck.json`; corroborated as rerun fresh in a prior session by `MODEL_DOSSIER/06_RATCHET_MECHANICS.md:53-56`, not independently re-executed again this session). Integration level: L0/available, no LLM or network call in the gate machinery itself (`MODEL_DOSSIER/06_RATCHET_MECHANICS.md:92`: "no_llm_or_network_calls_clean: true"). Epistemic label: audited CLEAN — a distinct fact from canonical-by-process; these components carry no `SIM_TEMPLATE`/tool-manifest/classification field, so per `MODEL_DOSSIER/06_RATCHET_MECHANICS.md:41-45` they cap at "passes local rerun."

A real (non-toy) run through this contract exists once: `ratchet_contract/fuel_sims/practice_run.py` ran the bridge on two real 2-qubit carriers (a qutip GKSL density-matrix candidate vs. a classical finite relation) over an 18-action shared deck, producing a frontier with one survivor (spinor) and one purgatory entry (classical, `failed_at: persistence_demand`) (`MODEL_DOSSIER/07_RATCHET_ACTUAL_STATE.md` §1, §4; source `ratchet_contract/fuel_sims/results/practice_run.json`, commit `d41907742`). Both that commit and the dossier name this a practice artifact, not an MSS verdict: one of four demanded pairs was never separated for the classical carrier at the base horizon (a root-specific confound at `root_plus0` — re-rooted at `root_00`, the same pair survives for both carriers), and a second loss traces to one exec file's `_delay_step` implementation, not a property of the classical-relational family generally. Status: `runs` per the commit's own self-report ("passes local rerun, byte-identical x2"); this session did not re-execute it (it needs qutip and a memory floor a prior reporting session's own gate refused under — a fail-closed refusal, not a defect), so the claim stands as documented, not independently reconfirmed here.

Upstream of the practice pair, `fuel_gate/fuel_adequacy_gate.py` ("Principle Zero") returns `HOLD_INSUFFICIENT_FUEL` on the actual candidate pool `system_v8/candidates/` — two of six required fuel roles (`countermodel`, `ablation_control`) are empty (`MODEL_DOSSIER/07_RATCHET_ACTUAL_STATE.md` §1; `fuel_gate/results/first_pool_verdict.json`). This hold is inherited by every pairwise comparison drawn from that pool, including the practice pair. Epistemic label: HOLD (a deterministic gate verdict, not an opinion).

### 4.5 The arrows: ratchet teeth run so far, with verdicts (`ratchet_contract/ratchetings/results/*.json`)

All rows below carry `classification: "tool_lego_fit_probe"` and `promotion_allowed: false` (confirmed by direct read of `pure_to_vn.json`, `root_foundation.json`, `extension_fibre_capacity.json` this session) — every arrow is FUEL-proposal by its own declared field, none is canon.

| Arrow (file) | Verdict | z3/cvc5 | Note |
|---|---|---|---|
| `pure_to_vn.json` | `EMERGES_ONE_WAY` | unsat/unsat | VN entropy born at the partial-trace cut; julia-vs-jax witness divergence `1.11e-16`; `engines_ran` all true (cvc5/jax/julia/qutip/sympy/z3) |
| `vn_to_shannon.json` | `RATCHETED_ONE_WAY` | — | VN→Shannon is RATCHETED_ONE_WAY under dephasing |
| `renyi_alpha_axis.json` | `S0_ONEWAY_FORGET_OF_VN` | unsat/unsat | Rényi-0 = ln(rank) is a one-way forget of the VN spectrum |
| `bures_to_fubini_study.json` | `BERRY_IRREDUCIBLE` | — | Berry curvature not recoverable from the (real, symmetric) Bures metric |
| `anticommutation_rung.json` | `ANTICOMM_ARROWS_ONEWAY` | unsat | symmetrization (forgetting sign) is one-way from anticommuting to commuting |
| `finite_to_continuum_rung.json` | `CONTINUUM_ABOVE_FINITE_ONEWAY` | unsat/unsat | discretization is one-way many-to-one |
| `real_vs_complex_tomography.json` | `COMPLEX_EARNED_BY_TOMOGRAPHY` | unsat/unsat | complex tomography dimension count (`d2=d1^2`) holds, real fails it |
| `algebra_ladder.json` | `LADDER_ONE_WAY` | unsat (2 of 4 links; other 2 `not_run`) | associativity and inverse drop one-way; identity/commutativity are honest bijections on the tested carrier, not forced |
| `law_order_branch.json` | `REMERGE_PATH_DEPENDENT` | unsat (order-erased) | sub-verdicts `chain_control.verdict = CHAIN`, `contrast_pair_result.verdict = GENUINE_BRANCH` — endpoints re-merge, paths stay order-dependent; a genuinely non-remerging branch is pinned as a separate control |
| `magma_to_semigroup.json` | `DROP_ONE_WAY` | unsat (witness pair) | associativity quotient drop is one-way (bracketing history unrecoverable) |
| `magma_smt_genuine.json` | `MECHANISM_ENCODED_UNSAT` | unsat (live table); sat (erased) | the one arrow whose SMT leg is mechanism-tied, not the generic tautology named below |
| `cut_dependent_entropy.json` | `CORRELATION_ENTROPY_BORN_AT_CUT` | — | negative conditional entropy `S(A\|B)<0` born at the cut, no classical shadow |
| `extension_fibre_capacity.json` | `FIBRE_CAPACITY_MEASURES_ONEWAYNESS` | — | untracked/new on disk this session (`git status`: `??`); floor claim `kappa_maxmixed_nats = ln2 ≈ 1.386` |
| `vn_to_shannon_basis_relativity.json` | `BASIS_RELATIVE_DISCLOSURE` | — | the one row with `direction: lower_is_better` |
| `root_foundation.json` | `ROOT_MECHANICS_HOLD` | — | below-the-magma probe: 9/9 constructed negatives correctly caught (HOLD on under-discrimination, FAIL on unearned identity/over-merge, a tolerance-relation non-transitivity witness, a one-way refinement forgetful map, a from-inside-M3 completeness gap); every "iff" reported relative to the active probe family only |
| `cut_dependent_entropy_nvidia_referee.json` | (external cross-check, not an arrow) | — | 4 of 4 queried NVIDIA-hosted models (`meta/llama-3.3-70b`, `openai/gpt-oss-120b`, `nvidia/llama-3.3-nemotron-super-49b`, `mistralai/mistral-nemotron`) returned `parsed.verdict = SURVIVES` |

A systemic caveat is named in the commit history, not hidden in the receipts: commit `b12c0e8c7` records "every z3/cvc5 leg is the SAME generic single-valued-function tautology... mislabeled TOOL_INTEGRATION_DEPTH=load_bearing," and follow-up commits `4fcd539d6`/`d2cdc4cbf` record the fix — z3/cvc5 downgraded to `supportive` and removed from each arrow's `core_ok` conjunction, with the real witness (numpy/sympy/jax/julia recompute) carrying the verdict. Confirmed on disk: `pure_to_vn.json`'s `TOOL_INTEGRATION_DEPTH` reads `{"z3": "supportive", "cvc5": "supportive", "jax": "load_bearing", "julia": "load_bearing", "sympy": "load_bearing", "qutip": "supportive"}` (read directly). `magma_smt_genuine.json` is named the one exception (its z3 leg is mechanism-tied: perturbing the encoded table flips the result). The most recent commit on this lane (`dcf4a5003`, "CI GREEN") claims all remaining numpy-red arrows moved to a jax.numpy base plus Julia leg, engine values agreeing under `1e-6`; this session read the resulting field (divergence `1.11e-16` on `pure_to_vn.json`) but did not re-execute the CI workflow beyond the fresh local seal rerun already reported in section 2.7 and this assembly pass's `gh run view` confirmation (both consistent with CI GREEN), so the underlying per-arrow science claims are `runs`/`passes local rerun` per those checks, not re-confirmed a third time here.

Epistemic label for the whole arrow set: FUEL-proposal (`tool_lego_fit_probe`, `promotion_allowed: false` on every row). `RATCHET_SPEC.md` §10-11 and `MODEL_DOSSIER/07_RATCHET_ACTUAL_STATE.md` are explicit that zero scientific manifold layers are admitted regardless of how many arrows pass.

### 4.6 The floor mechanism — a literal monotone ratchet

`ratchet_contract/run_ratchet_tick.py` runs a bounded two-tick frontier/MSS advancement contract, reusing the six gates and `frontier`/`pairwise_mss` machinery (`run_ratchet_tick.py:1-30`, read directly). Its floor receipt, `ratchet_contract/results/ratchet_tick_floors_v2.json`, records a monotone floor: `ratchet_tick.demand_count` fixed at floor 6 (`higher_is_better`) and `ratchet_tick.purgatory_count` fixed at floor 0 (`lower_is_better`), logged across a sha256-chained decision sequence (`prev_entry_sha256` links each entry to the previous one, `GENESIS` at the root), each entry stamped `action: "new"` then `"hold"` — the floor was set once and has only ever held, never regressed, across every logged tick. This is a concrete executable instance of chain-extension without any comparison collapsing anything: each tick either extends the chain at the same floor or does not run. Status: exists, and the receipt is internally consistent on read; this session did not re-execute `run_ratchet_tick.py` to reproduce the chain fresh.

### 4.7 What settlement / re-nesting machinery is not yet built

The task's terms "set-valued Sett," "Purgatory store," and "re-offer loop" do not appear as named objects anywhere in `ROOT/`, `RATCHET_SPEC.md`, or `ratchet_contract/` (checked by direct grep this session: `Sett\b`, `set-valued`, `re-offer`, `reoffer` return no matches in those trees; the one verbal echo, "eligible for re-offer," is in a different, superseded pack file, `ROOT/ROOT_RATCHET_KERNEL_pack178.md:71`, which `ROOT_CARD.md:59-60` explicitly demotes to "machine draft, not owner spec"). What exists instead, checked directly this session:

- The set-valued frontier itself is real: `M(D)` (`RATCHET_SPEC.md` §6) and `mss.py`'s `frontier()` both explicitly permit an antichain with more than one incomparable minimal survivor and never pick one — this is the live analogue of "Sett," just not under that name.
- Purgatory as a per-run list, not a cross-run store: `mss.py:240` builds `purgatory: list[dict] = []` fresh inside every call to `frontier()`. No code path was found that reads a prior run's purgatory list back in on a later run to check `re_entry_condition`s against newly available evidence. Each entry's `re_entry_condition` (`mss.py:250,265,278`) is a string a human or a future run must notice and act on manually; it is not itself an executing loop.
- `RATCHET_SPEC.md` §2 (lines 43-51) names `tested_frontiers` and `evidence_ledger` as append-only conceptual state, but the shipped `ratchet_engine.py --run` / `--validate` commands (§10, §13) operate on one packet's fixture at a time; no code path was found that merges an old run's frontier into a new one as a persistent, growing ledger across invocations.

The proposed plan for closing this gap is named, not built: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/V8_PRELAUNCH_AUDIT_AND_PLAN_20260715.md`, "Phase 5 — Build the actual Ratchet Packet A" (lines 313-321), lists as still-to-do: "Implement plural MSS frontiers, target-free drive, HOLD, Purgatory fingerprints, and material-context re-entry" (item 3) and "Give Julia, JAX, PyTorch, Z3, and cvc5 distinct claim-bearing roles" (item 4), with an exit gate of "two independent encodings, SAT plus UNSAT-with-negation where applicable, executable replay, complete minimal-survivor antichains, and no hand-installed winner" (line 320). This document is dated 2026-07-15 and is a plan, not a receipt — read it as OPEN/proposed, not as evidence the machinery it describes now exists. A document with sections literally labelled "D," "E," "F" on this exact settlement/re-nesting gap was not located in this session's search of the Desktop tree; the closest matching material is this Phase 5 block, plus the open-gaps table in `MODEL_DOSSIER/06_RATCHET_MECHANICS.md` table 3b (7 named gaps, including gap 1, "SMT bridge is not independent," and gap 2, "trace-to-partition bridge for real carriers," both bearing on re-nesting machinery). This is flagged explicitly as UNCERTAIN: what would settle it is the orchestrator naming the exact file path if a different "section 5" / "slices D-F" document was intended.

Two further named-and-open gaps bear on settlement directly, both stated by the repo itself rather than found newly here:

- The SMT-relational bridge is not yet an independent decider: `bridge_smt_relational.py`'s `union()` call only merges a pair when `decision.reference_same` (the same pure-Python recursion the action-predictive bridge uses) is already true — z3 and cvc5 gate agreement with that recursion, they do not decide the partition themselves (`MODEL_DOSSIER/06_RATCHET_MECHANICS.md` table 3b, gap 1; confirmed by that document's own reading of the source file, not independently re-read line-by-line this session).
- Engine adapters are interface-only: `JuliaEngineAdapter`, `JaxEngineAdapter`, `PyTorchEngineAdapter` in `ratchet_contract/contract.py` all raise `NotImplementedError` (`MODEL_DOSSIER/06_RATCHET_MECHANICS.md` table 1, table 3b gap 5); the one live numeric substrate in the practice run (qutip) bypasses this interface entirely.

An untracked, uncommitted file present on disk this session (`git status`: `??`) partly narrows one of these gaps: `ratchet_contract/bridge_validation/mutation_arbiter_test.py` and its result `results/mutation_arbiter_test.json` mutation-test the rival predictive-quotient bridges (`bridge_word_bfs` vs `bridge_action_predictive`) — 4 injected faults, 3 producing a genuine disagreement the arbiter then sides against on 3/3 checks, 1 fault (`prefix_comparison_skipped`) producing a named `coverage_finding` instead of a disagreement. The file's own declared scope caps this at "practice/fuel development only — promotion_allowed=false, formal_admission_allowed=false." Status: exists (uncommitted); this session read the JSON directly but did not re-execute the test file. Epistemic label: FUEL-proposal, not yet promoted, not yet part of the committed record.

### 4.8 Divergent readings held open (not collapsed)

- Owner MSS (`ROOT_CARD.md`, undated, verbatim) vs. spec MSS (`RATCHET_SPEC.md` §6, v0.5, partition-refinement only): the card is explicit these are not the same thing — the spec's installed weakness relation is one proposed operationalization, and `ROOT_CARD.md:54-56` warns against ever treating "weakest-survivor gate search discipline" as the owner's MSS definition itself. Both readings stay live here; neither is dropped in favour of the other.
- Whether partition-refinement is also the correct nominalist presumption metric: `MODEL_DOSSIER/07_RATCHET_ACTUAL_STATE.md` §3 documents three sequential, mutually inconsistent LLM-authored rankings on this question (`STRAWMAN_AUDIT.md`, then `PRESUMPTION_RANKING_CORRECTION.md` inverting it, then `RANKING_VOID_llm_did_ratchets_job.md` voiding both), landing on HOLD by the repo's own rule that an LLM may never compute this ranking. `ROOT/HOW_THE_ENGINES_RUN_THE_RATCHET.md` (per the same dossier page) separately proposes, as an unexecuted hypothesis, that the already-installed partition-coarseness relation may turn out to be the correct metric once run on compiled candidates — named as a hypothesis the code would decide by being run, not yet run. Both readings — "partition refinement is a proposed weakness relation among rivals" and "partition refinement may itself be the nominalist presumption metric" — remain open and are not merged here.

### Absent / unverified (index)

- Literal "146/0/0" as a figure independently reproduced in this container: ABSENT as a verified figure — `bundle_manifest.json` itself calls it a provenance claim from another environment with no matching top-level report. Treat memory's "FIRST GREEN 146/0/0" as UNVERIFIED against this repo's own receipts. What would settle it: locate and rerun the exact source archive/environment that produced it.
- "Set-valued Sett," "Purgatory store," and "re-offer loop" as named, built objects: ABSENT under those names anywhere in `ROOT/`, `RATCHET_SPEC.md`, or `ratchet_contract/` (grep returned no matches). Live analogues exist (frontier antichain `M(D)`; per-call purgatory list with `re_entry_condition` strings) but no persistent cross-run store or scheduled retry loop was found.
- A "Desktop audit doc" with sections literally labelled D, E, F on the settlement/re-nesting gap: NOT located in this session's search. The nearest match found and cited is `V8_PRELAUNCH_AUDIT_AND_PLAN_20260715.md` Phase 5 (a numbered, not lettered, section). What would settle it: the orchestrator supplying the exact file path if a different document was intended.
- 152/0/0 `local_fast_harness` and 109/4/33 `run_all.py` figures: read from stamped receipts on disk, NOT re-executed fresh in this session. Status capped at "passes local rerun" per the receipt's own timestamp, not re-verified today.
- `ratchet_engine.py --self-test`, `run_contract_selfcheck.py`, `run_ratchet_tick.py`: none re-executed fresh in this session; all statements about them are read from existing JSON/MD receipts and a prior session's dossier (MODEL_DOSSIER), not this session's own execution.
- `practice_run.json`'s "byte-identical x2" rerun claim: self-reported by its own commit; `MODEL_DOSSIER/06_RATCHET_MECHANICS.md` records a prior session's attempt to reproduce it was blocked by the file's own memory-floor gate. Not attempted again this session.
- Whether the "CI GREEN" commit (`dcf4a5003`) workflow itself currently passes on GitHub CI: this assembly pass confirmed via `gh run view 29969379442` that the tied Actions run completed with conclusion `success`; the resulting JSON fields on disk (e.g. `pure_to_vn.json`'s engine divergence `1.11e-16`) were also read directly.
- `ratchet_contract/bridge_validation/mutation_arbiter_test.py` and its result JSON: present but uncommitted (`git status` `??`); read directly but not re-executed this session.

---

## 5. Lev OS — current state, ClaimGate patch relation, issues

**Bottom line.** The only live Lev checkout is `~/lev-main`, pure `lev-os/leviathan` upstream `main`, read-only for this report. It ships real CR-facing scaffolding (`plugins/sim-witness`, a `codex_ratchet.engine_leg_result.v1` adapter, an evaluator-pack loader) but none of the orchestration/steering surface, ClaimGate gate rows, or ratchet-forward enforcement that earlier CR-side docs describe. The CR-side rebuild plan (`lev_patch/`) is explicitly withdrawn as written. `LEV_WIRING.md`'s "verified live 2026-07-22" claims about `orchestration claimgate-steering` describe a deleted branch/worktree, not the checkout that exists now; `LEV_ATTACH_MAP_20260722.md` (same day, later timestamp) is the reading consistent with what I independently re-verified below.

### 5.1 Install state (verified this session, read-only)

- `~/lev-main` exists — `git log --oneline -1` → `1efe47f4b Merge origin/main into the composable Now checkpoint` (2026-07-21 15:08:20 -0500), branch `main`, remote `origin` = `https://github.com/lev-os/leviathan.git`. `runs`.
- `~/GitHub/lev` — the path named as "front door" in this project's own CLAUDE.md ("LEV OS BOOT... Front door: /Users/joshuaeisenhart/GitHub/lev") — **does not exist** (`ls` → No such file or directory). That CLAUDE.md line, and its paired claim "CR-facing Lev branch: lev-main fable/cr-sim-eval-pack", are stale against the live filesystem. `CLAUDE.md` itself is not being edited here; flagging only.
- The global `lev` binary (`~/.local/bin/lev`) is a symlink straight into `~/lev-main/core/poly/bin/lev` — `runs`, verified by `readlink -f`. This differs from `LEV_WIRING.md`'s "The binary" section, which describes the symlink pointing at `~/lev-main/.worktrees/current-main-20260715/core/poly/bin/lev` and a separate `~/GitHub/lev` poly build. Neither the worktree path nor `~/GitHub/lev` exists now — that two-binary picture is dead.
- `lev --help` runs and lists command groups: `build`, `config`, `context-graph` (includes `ratchet-admission`), `daemon`, `event-dispatch`, `exec` (`eval`, `exec`, `exec-status`, `done`, …), several `plugin:*` groups, `poly`, `testing`, `tmux-harness`, `validator`, `workstream`. CORRECTION (identical cited binary, `~/.local/bin/lev` → `~/lev-main/core/poly/bin/lev`, same commit `1efe47f4b`, rerun this pass): the listing does contain an **`orchestration:` group**, with four subcommands — `assign`, `cdo`, `execute-epic`, `task` — an epic/task-assignment surface unrelated to ClaimGate. None of the four is `claimgate-steering`.
- Directly tested: `lev orchestration` (bare) → `Unknown command: orchestration`, exit 1. `lev orchestration claimgate-steering` and `lev orchestration claimgate-steering consume` both also → `Unknown command: orchestration`, exit 1. `runs`. These subcommands are invoked directly by bare name (for example `lev cdo`), not through an `orchestration` namespace prefix — so the bare-command failure confirms `claimgate-steering` is absent, not that the `orchestration` group itself is absent. The section 5.3 bottom-line verdict (claimgate-steering surface KILLED-in-current-checkout) stands; the premise above it was wrong and is fixed here.
- Repo-wide case-insensitive search `grep -rIli "claimgate" .` (excluding `node_modules`) in `~/lev-main` returns exactly one hit: `docs/_inbox/20260619-claimgate-leviathan-convergence.md`. No `claimgate` token anywhere in `dna/gates.yaml`, no `core/orchestration/test-fixtures/claimgate-steering` path exists at all.
- `dna/gates.yaml` at repo root has zero `claimgate` matches (`grep -in "claimgate" dna/gates.yaml` → exit 1, no output). This directly contradicts `LEV_WIRING.md`'s claim of "Two Lev gates enforce this in `dna/gates.yaml` (`status: enforced`, `owner: claimgate`): `claimgate_steering_admitted`, `claimgate_blocks_overclaim`." Those gate rows are **ABSENT** from the checkout that exists today.

**Reading the two source docs together (both present, dated 2026-07-22, contents disagree):** `LEV_WIRING.md` carries its own banner at line 1 saying paths citing `~/GitHub/lev` or `~/lev-main/.worktrees/*` are deleted checkouts, and that the `orchestration claimgate-steering` surface "was branch-only work, lost with the old tree" — but the body of the same file below the banner still narrates that surface as "Verified live 2026-07-22" (good/bad fixture runs, gate rows). `LEV_ATTACH_MAP_20260722.md`, written after (file mtime 17:25 vs 17:22), states plainly: "ABSENT upstream: `lev orchestration` (steering-consume gone for good), claimgate rows in `dna/gates.yaml`." My independent verification above (fresh `grep`/CLI probes, not re-reading either doc's prose) matches the attach map, not the banner-contradicted body of `LEV_WIRING.md`. Do not cite `LEV_WIRING.md`'s "Steering-consume" or "Known findings for the Lev dev" sections as current state — they are design record of a deleted branch, per that file's own banner and per this session's live check.

### 5.2 What upstream `~/lev-main` genuinely ships for CR (verified `exists`/`runs`)

- `plugins/sim-witness/` is a real plugin directory with `evals/`, `src/`, `tests/`, `config.yaml`. `exists`.
- CR-named eval packs under `plugins/sim-witness/evals/`: `cr_constraint_battery`, `cr_cross_engine_parity`, `cr_ordered_channel_parity`, `cr_scc_quotient_parity`, `cr_qit_bridge_stream_v0`, each with a `*.eval.yaml`. Read `cr_constraint_battery.eval.yaml`: `schema: lev.evaluator_pack.v1`, `kind: shipped_evaluator_pack`, `entrypoints.flow: flows/measure.flow.yaml`, `entrypoints.sensor: companions/sensor.mjs`, `policies.gate: policies/gate-policy.yaml` — a real, on-disk template of the shape the attach map's "minimal attach" plan says to clone. `exists`, integration level **L0 available** (present, not yet exercised by any CR receipt in this session).
- `src/cr-result-adapter.ts` exports `CR_ENGINE_LEG_RESULT_SCHEMA = 'codex_ratchet.engine_leg_result.v1'` and a frozen `CR_FORBIDDEN_FACT_NAMES` list: `['all_pass', 'promotion_allowed', 'formal_admission_allowed', 'does_not_self_upgrade']` (`cr-result-adapter.ts:9-20`). A fact matching one of these returns `{ok:false, reason:'verdict_bit_requested', detail:'... is a CR self-assessment bit and cannot become a gate observable'}` (`cr-result-adapter.ts:64,183`). This is the "one-brain" contract, confirmed by reading code, not by trusting either doc's paraphrase — note the exact forbidden-name list differs slightly from `LEV_ATTACH_MAP`'s paraphrase (`all_pass`/`promotion_allowed`/`verdict`/`gate_proof`); the literal tokens `verdict` and `gate_proof` do not appear in this array, `verdict_bit_requested` is the *reason code*, not a forbidden fact name. Transcribed exactly here to avoid compounding the paraphrase.
- Companion tests exist: `plugins/sim-witness/tests/cr-*.test.ts` (6 files: `cr-constraint-battery`, `cr-cross-engine-parity`, `cr-ordered-channel-parity`, `cr-qit-bridge-stream-v0`, `cr-result-adapter`, `cr-scc-quotient-parity`, plus `cr-scout-lego-adapter`). `exists`; not executed this session (would require a build step outside the read-only scope of this check), so status stays at `exists`, not `runs`.
- Supporting primitives cited by `LEV_WIRING.md` and independently confirmed present on disk: `core/eval/src/evaluator-pack-loader.ts`, `core/exec/src/handlers/eval.ts` (absolute-path run resolution logic present around the cited region — `resolveRunPath`/`loadDecision`), `core/exec/src/loop/until.ts`, `core/exec/src/run/evidence.ts`, `core/exec/src/gate-run.ts`, `core/exec/src/handlers/gate.ts`, `core/event-dispatch/src/trigger-dispatcher.ts`. All `exists`; none executed this session.
- `plugins/manifest.json` (generated 2026-06-19T06:25:29Z, 52 plugins listed) has **no `sim-witness` entry**. UNCERTAIN whether this means sim-witness isn't formally plugin-registered, or the manifest is simply stale relative to when sim-witness was added (manifest predates the plugin's apparent presence). What would settle it: regenerate the manifest and check whether sim-witness appears, or find the manifest-generation command's inclusion rule.

### 5.3 What is absent (independently confirmed, not just cited)

- `lev orchestration` — no such subcommand; the entire `orchestration claimgate-steering consume` surface described across most of `LEV_WIRING.md`'s body does not exist in `~/lev-main`. **KILLED-in-current-checkout** (it may exist in git history on a deleted branch on the remote — not checked, would require a network fetch out of scope for a read-only local check).
- `core/orchestration/test-fixtures/claimgate-steering/{good,bad}` — path does not exist (`find` returned nothing).
- `dna/gates.yaml` claimgate rows (`claimgate_steering_admitted`, `claimgate_blocks_overclaim`) — absent, confirmed by direct grep.
- `ratchet-forward floor comparison` — `LEV_ATTACH_MAP` and `LEV_WIRING.md` agree this is undeclared/unenforced anywhere; not independently re-derived this session beyond confirming the cited file `core/context-graph/src/handlers/graph-apply-overlay.ts` exists (`ls` confirmed the containing dir; full contents not read this pass). **OPEN**, consistent across both docs.
- `ratchet-admission.flow.yaml` (`core/flowmind/system/ratchet-admission.flow.yaml`) exists on disk and is boot-priority 3, "5 Meta-Gates Wrapping 7 Processing Stages" per its own header. Read its executor, `core/flowmind/src/kernel/system-flowmind-executor.ts:234-260` (`evaluateYaml`): the method's own comment says "MVP: all YAML stages pass at boot — they're constraint declarations, not runtime checks... For now, stages pass at boot." This is a direct code-comment confirmation of the "boot-stub, do not trust it as a gate" characterization — not a paraphrase, the source literally says stages pass at boot.
- `lev ratchet-admission` — tested directly (`lev ratchet-admission --help` → `Error executing 'ratchet-admission': Cannot read properties of undefined (reading 'winner_axes')`, an unhandled runtime error, not a help screen). Traced the handler: `core/context-graph/src/handlers/ratchet-admission.ts:1-10` header docstring: `"graph:ratchet_admission — AAVF WINNER ratification gate... writes the ratified ratified_composition block into dna/graph.yaml."` This is a Lev-internal AAVF (axis-composition ratification) writer, unrelated to CR receipts or ClaimGate — confirms the attach map's characterization ("the AAVF graph writer, NOT a receipt gate") from the source docstring itself, not from the doc's say-so.
- No trace of a `fable/cr-sim-eval-pack` branch in this checkout: `git branch -a` and `git branch -r` both return nothing for `cr-sim|claimgate|fable`; `git log --all --oneline | grep -i claimgate` returns exactly one commit, `5ff338513 Capture ClaimGate ↔ Leviathan convergence analysis as inbox draft` — the same inbox doc found by the file search. The branch itself is not present locally (may or may not still exist on the GitHub remote; not checked — that would need a fetch, out of scope for read-only-local verification).

### 5.4 The zero-touch attach plan (as specified in `LEV_ATTACH_MAP_20260722.md`, status: **FUEL-proposal**, not yet built)

Five steps, none requiring a write to `~/lev-main`:
1. Build an evaluator pack inside CR at `claimgate_plugin/evals/claimgate/` (schema `lev.evaluator_pack.v1`, a `companions/sensor.mjs` wrapping `claim_verify.py` exit codes into `lev.evaluator.result.v1`, a `policies/gate-policy.yaml`, a `pass.eval.js` suite), cloning the `cr_constraint_battery` shape confirmed present in 5.2. **Checked this session: `claimgate_plugin/evals/` does not yet exist in the CR repo** (`ls` → No such file or directory) — this step is planned, not built.
2. Run it through Lev's own eval brain by absolute path: `cd ~/lev-main && ./core/poly/bin/lev eval run /Users/joshuaeisenhart/Codex-Ratchet/claimgate_plugin/evals/claimgate/pass.eval.js --json`, landing a decision at `~/.local/share/lev/execution-ledger/artifacts/eval/<runId>/decision.json`. Not run this session (step 1's input doesn't exist yet).
3. The harness-fired leg is unchanged: `lev exec --verifier 'python3 claimgate_plugin/claim_verify.py ...'` — this leg does not depend on the orchestration surface and is not affected by the absences in 5.3.
4. Symlinks into `~/lev-main` are ruled out ("DEAD (fractal-scan containment I-35/N-35)"); an `.lev/local.config.yaml` `eval.roots` override is flagged as possible but "= untracked file in the read-only repo — owner's call only." Not attempted (would be a write to `~/lev-main`, out of scope for this read-only check regardless).
5. `docs/_inbox/20260619-claimgate-leviathan-convergence.md` — confirmed present in `~/lev-main`, one commit (`5ff338513`) — already frames ClaimGate as a sanctioned `plugins/` surface; cited as the upstream landing point for a future `dna/gates.yaml` row. `exists` as a design doc; not a merged capability.

### 5.5 CR-side rebuild attempt: `claimgate_plugin/lev_patch/` — status **WITHDRAWN**, not live

Two files exist in the CR repo, dated 2026-07-22:
- `lev_patch/claim-admission.ts` opens with: `"WITHDRAWN 2026-07-22 (webui audit) — do not implement as written."` (line 1). The header explains why: the file proposed one `physics.claim-admission` capability that "interprets the proof, decides truth, and writes canon" in a single function — the exact "one self-certifying gate" / authority-collapse failure named in `claimgate_plugin/CLAIMGATE_POSTMORTEM_20260722.md` (section 4, lines 36-43: "collapsing claim intake, evaluation, and settlement... the finalizing TS capability is WITHDRAWN; truth belongs to Lev `core/eval`, settlement to policy"). The file also states its imports were never real: `@lev-os/agentfs-sdk` and `@lev-os/flowmind-types` are commented-out "proposed imports — these packages are the patch's dependency ask" (`claim-admission.ts:19-21`), and "the real native seam is `lev.call` (currently a design-doc span name, not yet wired)" (`claim-admission.ts:9-10`).
- `lev_patch/index.ts` still imports `claimAdmissionCapability` from the withdrawn file and calls it "PROPOSED LEV PATCH... the registry API below is the ASK, not a currently-existing Lev surface" (`index.ts:1-9`). This file is stale/orphaned relative to its own import target's withdrawal notice.

Epistemic label for `lev_patch/` as a whole: **DEMOTED/WITHDRAWN** by its own header, kept on disk as, in the postmortem's words, "an honest negative, per repo doctrine" (`CLAIMGATE_POSTMORTEM_20260722.md` line 15). It is not the current attach plan — 5.4's evaluator-pack route is what `LEV_ATTACH_MAP_20260722.md` currently recommends instead.

### 5.6 CR-side script already reflects the honest-degrade posture

`claimgate_plugin/run_through_lev.sh` (mtime 2026-07-22 17:21, i.e. written after the branch-loss was discovered) runs the ClaimGate fired gate (`post_receipt_gate.sh`) as leg 1, then for leg 2 explicitly probes `"$lev_bin" orchestration --help` before attempting a steering-consume call; on failure it prints `"Lev at $lev_root has no 'orchestration' subcommand (pure upstream main; steering-consume was branch-only and is being rebuilt as the ClaimGate patch)... ClaimGate leg stands; Lev host-recompute SKIPPED — not silently passed."` and exits 0 (script comment: "ClaimGate leg stands" — the CR-local gate is not weakened by Lev's missing surface, but nothing calls Lev today). This script's own comment (line ~13) states plainly: `"~/GitHub/lev deleted; ~/lev-main = the only Lev (pure upstream main)"` — matching the live-filesystem check in 5.1 independently.

### 5.7 Open items

| Item | Status | Note |
|---|---|---|
| `agentfs-sdk` (`@lev-os/agentfs-sdk`) | ABSENT as an importable package for the ClaimGate patch | Only ever a commented-out "proposed import" in the withdrawn `lev_patch/claim-admission.ts:20`. `~/lev-main` does have unrelated AgentFS concepts (`crates/lev-agentfs`, `docs/specs/spec-agentfs.md`) but no `@lev-os/agentfs-sdk` package was found (`grep` across `package.json` files, no hit). |
| `lev.call` | UNWIRED | `claim-admission.ts:9-10`: "the real native seam is `lev.call` (currently a design-doc span name, not yet wired)." Not found as a live CLI or API surface in `~/lev-main` this session (`grep -rln "lev\.call"` across `.ts`/`.md` in lev-main returns only design-doc/spec hits, e.g. `docs/specs/spec-exec.md`, `docs/specs/spec-poly.md`, `docs/specs/spec-flowmind.md`, `core/exec/src/execution/dispatch/exec-local-ops.ts` — none confirmed as an executable capability registry in this pass; would need deeper read to promote past `exists`). |
| Stale `dna/gates.yaml` grep bug named in `LEV_WIRING.md` ("Known findings for the Lev dev") | Moot in the current checkout | The gate rows the finding is about (`claimgate_blocks_overclaim`) do not exist in `~/lev-main`'s `dna/gates.yaml` at all (5.1) — the finding describes a state (gate present, assertion stale) that no longer matches what's on disk; either the gate was removed along with the rest of the orchestration surface, or the finding was against the deleted worktree the banner warns about. Not re-derivable without the deleted tree. |
| CLAUDE.md "LEV OS BOOT" pointer to `~/GitHub/lev` and branch `fable/cr-sim-eval-pack` | STALE vs. live filesystem | Confirmed both absent this session (5.1, 5.3). Flagging for the owner's awareness; not edited as part of this report. |
| sim-witness plugin registration | UNCERTAIN | Not in `plugins/manifest.json` (generated 2026-06-19); could mean unregistered or a stale manifest. Settled by regenerating the manifest or reading its generation script's inclusion rule — not done this session. |

### Absent / unverified (index)

- Whether `fable/cr-sim-eval-pack` still exists on the `lev-os/leviathan` GitHub remote (not fetched).
- Whether any CR receipt has been run end-to-end through `plugins/sim-witness`'s `cr_*` evaluator packs.
- Full contents of `core/context-graph/src/handlers/graph-apply-overlay.ts:75-94`.
- Whether `lev.call` is wired anywhere beyond design-doc/spec mentions.
- Whether `plugins/sim-witness` is formally registered (`manifest.json` has no entry, but the manifest predates the plugin's likely addition).

---

## 6. QIT engines + ALT engine types the estate can run

### 6.1 The proposed 16-stage engine contract (FUEL-proposal, not repo canon)

The formulas below are transcribed from `/Users/joshuaeisenhart/Desktop/GEMINI_EVOLVING_PLAN_ASSESSMENT_AND_CORRECTED_ARCHITECTURE_2026-07-22.md`, sections 4.3 and 8. This file sits outside the Codex-Ratchet repo (a Desktop planning artifact, not tracked in git) and states its own standing on line 4: "Architectural reconciliation and execution plan. This is not a simulation receipt, a proof, or an admission of any physics claim." Epistemic label: **FUEL-proposal / OPEN** — a corrected-architecture critique of a Gemini plan, not owner-canon and not something the repo has built end to end.

Axes (section 4.3, lines 87-102):

| Axis | Meaning |
|---|---|
| Scientific engine type | Type 1 or Type 2 mathematical degree of freedom |
| Loop | outer or inner |
| Stage role | four placements per loop |
| Operator candidate | four candidates tested at each placement |
| Runtime backend | Julia, JAX, or PyTorch implementation/referee |

\[
2\ \text{engine types}\times2\ \text{loops}\times4\ \text{roles}=16\ \text{stage placements},\qquad 16\times4=64\ \text{local candidate cells.}
\]

Line 110 is explicit that 64 candidate cells does not mean 64 substages execute; the Ratchet instead compares competing global interpretations \(H_{\mathrm{native}}, H_{\mathrm{select}}, H_{\mathrm{all4}}, H_{\mathrm{mix}}\). Line 117 warns: "A 16-dimensional latent coordinate, 16 torus/grid nodes, 16 basins, and the 16 engine placements are also distinct objects. They must never be identified merely because the number matches." That warning is load-bearing for section 6.2 below.

Stage instrument and engine composition (section 8, lines 332-361):

\[
\mathcal I^{y}_{e,\ell,r,x}:\mathcal D(\mathcal H_x)\to\mathcal D_{\le1}(\mathcal H_{f(x,y)}),\qquad
\mathcal E_{e,\ell}=\mathcal S_{e,\ell,4}\circ\mathcal S_{e,\ell,3}\circ\mathcal S_{e,\ell,2}\circ\mathcal S_{e,\ell,1}\ \text{(rightmost first)}.
\]

\[
p(y\mid o)=\operatorname{Tr}\mathcal I^{y}_{e,k}(\rho_o),\qquad U_{e,k}=I(O:Y_k\mid Y_{<k}).
\]

Required ablations (line 361): "deletion of each stage, deletion of each loop, order reversal, engine-type swap, record erasure, and input-object permutation. A stage with zero unique work remains an honest finding." No repo file implements `\mathcal I^y_{e,\ell,r,x}` or `\mathcal E_{e,\ell}` literally — this is the FUEL-proposal contract, not a built object. What the repo has built is described next, and none of it should be read as an instance of this exact contract.

### 6.2 What the repo already runs against pieces of that contract — do not conflate

Two existing objects independently produce a "16" and a per-stage information-work measurement, on different definitions of "stage." Per the section-4.3 warning above, they are held apart, not identified with each other or with the FUEL-proposal contract.

**`system_v8/nested_manifold/stage64_constraint_tournament.py`** (313 lines) builds its own 16 = "4 terrain families × 2 sheets (L/R) × 2 loop fields (f=±1)" grid, tests a mutual-constraint tournament (commutation kill K1, frame-sign selection K2, chirality consistency K3) over 4 candidate generator pairs per stage. Result: `system_v8/nested_manifold/results/stage64/receipt.json` — `schema: "ratchet.v8.nested-manifold.stage64.v0"`, `all_pass: true`, `claim_ceiling: "executed finite instance of the 16x4 mutual-constraint tournament; no uniqueness/optimality claim; frame sign declared, not derived"`, `promotion_allowed: false`. Label: **exists, runs (all_pass true in the committed receipt) — classification `unofficial`/scratch-diagnostic tier by its own claim ceiling**; this "16" is the family×sheet×loop-field decomposition, not the engine-type×loop×role decomposition of section 4.3.

**`system_v8/engines_perception/engine_processor_v0.py`** (661 lines) is the closest existing repo analog to the section-8 stage-instrument requirement. It runs a LEFT and a RIGHT engine (8 stage64 L-side operating generators each; RIGHT = complex-conjugated generators, opposite schedule order — an engine-type-swap-like control by construction, not a ceteris-paribus ablation of one variable) over an inner loop (2 within-word passes) and an outer loop (2 across-word epochs), and computes per-stage unique work as a Holevo-information gain, not the literal \(U_{e,k}=I(O:Y_k\mid Y_{<k})\) formula. Result `system_v8/engines_perception/results/processor_v0/receipt.json`: `promotion_allowed: false`, `claim_ceiling: "unofficial working sim; perception-lane evidence only; no bridge/axis claims"`, `all_pass: false` (2 of 11 named checks fail, retained as honest negatives, not smoothed). Findings on file:
- "LOO bit decoding L 0.7812 / R 0.8438 (chance 0.5); final Holevo chi L 0.2892 / R 0.2528 bits."
- "unique work: 9/16 slots strictly positive on L (10/16 on R); ... negative slots L=[4, 5, 10, 11, 12, 13, 15] (dissipative carving reduces chi where it fires — kept as finding)."
- "stage-deletion: every one of the 8 L stages measurably changes accuracy, chi, or the information profile" (`checks.stage_deletion_witness_measurable_change: true`).
- "loop ablations: inner-only vs outer-only error patterns differ in 12 of 96 positions" (`checks.inner_outer_ablations_lose_different_information: true`).
- honest failure: `checks.heldout_admissibility_above_majority_both_engines: false` and `checks.automaton_and_engine_above_chance_with_complementarity_matrix: false` — held-out packet admissibility (`qca_left_shift_cut_relation`, `octonion_bracketing_relation`) is "not learnable word-wise from the other 7 packets," recorded as "HONEST NEGATIVE (data-limited, not engine-limited)."
- controls present: shuffled-label null (`checks.shuffled_label_adm_null_at_chance: true`), shuffled-assignment bit control (`checks.shuffled_assignment_bit_control_collapses: true`), frozen-engine control (`checks.frozen_engine_control_no_information_gain: true`).

Label: **exists, runs, passes-local-rerun is not re-verified this session (receipt read from disk only) — classification `unofficial working sim`, `promotion_allowed: false`**. Against the section-8 required-ablations list: stage-deletion (present), loop-deletion via inner/outer ablation (present), input-object permutation via shuffled controls (present), record erasure via frozen-engine control (present, as conditioning-off rather than literal record erasure); order-reversal and an isolated engine-type-swap ablation (as opposed to L/R being separately-authored engines from the start) are **not** run as named, isolated tests. `system_v8/engines_perception/processor_at_scale.py` (718 lines) is a companion at-scale run with the same claim ceiling; its receipt (`results/at_scale/receipt.json`) is also `all_pass: false` by design (same class of honest negatives). Two further receipts, `processor_v0_run1_overdissipated_negative` and `processor_v0_run2_weak_writing_negative`, are retained failed variants, not deleted.

### 6.3 Thermo engines (carnot / szilard / otto) — current CI-passing state

Enforcement mechanism: `.github/workflows/three-engine-seal.yml` runs `scripts/ci_three_engine_seal.py`, which globs `system_v8/*/results/*.json` (and `ratchet_contract/ratchetings/results/*.json`) through `claimgate_plugin/three_engine_seal.py` in `SEAL_METADATA_ONLY=1` mode, rejecting any receipt that contains numpy or lacks ≥2 agreeing engines. **Freshly reran this session** (`python3 scripts/ci_three_engine_seal.py`, HEAD `1760f9a4a`): `three-engine CI seal: 35 receipt(s) pass, 0 REJECTED`, exit 0 — status: **passes local rerun**, matching commit `dcf4a5003` ("CI GREEN (workflow 9/9, mechanical seal 35 pass / 0 REJECTED)... thermo trio (carnot/szilard/otto) now jax.numpy-x64 base with `_jax.py` (dynamiqs/diffrax) + `_julia.jl` (QuantumOptics) legs"). Each of the three thermo receipts was also independently reran through the seal script alone, individually confirming `2 engines ['jax', 'julia'] agree; no numpy` at exit 0. This assembly pass additionally confirmed via `gh run view 29969379442` that the GitHub Actions run tied to commit `dcf4a5003` completed with conclusion `success` on workflow "three-engine seal (no numpy)."

| Engine | File(s) | What it computes | `engines_ran` | `max_cross_engine_divergence` | `all_pass` | `classification` | `claim_ceiling` |
|---|---|---|---|---|---|---|---|
| Carnot | `system_v8/thermo_engines/carnot_engine.py` (jax.numpy base), `_jax.py` (diffrax Lindblad thermal-contact cross-check), `_julia.jl` (QuantumOptics `timeevolution.master` Gibbs-relaxation leg) | Ideal-gas P-V Carnot cycle: trapezoid-integrated \(\eta\), \(W_{net}\), against \(\eta=1-T_c/T_h\) and \(W_{net}=nR\Delta T\ln r\) closed forms; a Lindblad-relaxation cross-check on the isothermal-contact premise | jax: true, julia: true, qutip: false | 1.19e-15 | true | classical_baseline | `engine_competence_check_only`, `promotion_allowed: false` |
| Szilard | `system_v8/thermo_engines/szilard_engine.py`, `_jax.py` (dynamiqs measurement/erasure cycle), `_julia.jl` (QuantumOptics projectors + entropies) | One-molecule/one-bit engine as a density-operator measurement-and-erasure cycle: `extracted_work_kT = S(S_post)+S(M)-S(joint) = ln 2` (Landauer-saturated), `net_work_kT <= 0` closed-cycle bound, a no-measurement control giving `I(S:M)=0` | jax: true, julia: true | 1.55e-14 | true | classical_baseline | `engine_competence_check_only`, `promotion_allowed: false` |
| Quantum Otto | `system_v8/thermo_engines/quantum_otto_engine.py` (jnp x64 density matrices), `_jax.py` (dynamiqs `mesolve`), `_julia.jl` (QuantumOptics `master` dynamics), qutip `mesolve` as a supportive (not load-bearing) third cross-check | Spin-1/2 quantum Otto cycle, Zeeman gap as piston: two isochoric + two isentropic strokes on jnp midpoint-exponential unitary strokes and a GKSL Liouvillian `expm` for thermal relaxation | julia: true, jax: true, qutip: true | 3.03e-09 | true | classical_baseline | `engine_competence_check_only`, `promotion_allowed: false` |

`szilard_engine.json`'s `engine_machinery_used.note`: "base is classical single-molecule statistical mechanics on jax.numpy x64; the julia/jax legs recompute the SAME kT ln2 extracted-work / Landauer bookkeeping as the density-operator measurement/erasure cycle ... Substrate migration only; the science and claim ceiling are unchanged." All three declare `numpy: false` in `engine_machinery_used`. None of the three seeks a higher status than `engine_competence_check_only` / `classical_baseline` — they are competence checks on the engine substrate, not physics or bridge claims, and none cites `system_v4/probes/SIM_TEMPLATE.py` lineage directly (`SIM_TEMPLATE` string absent from `carnot_engine.py`); a `classification` field and populated `tool_manifest`/`tool_integration_depth` are present in all three (e.g. `carnot_engine.py:75` `TOOL_MANIFEST`, `:401` `"classification": "classical_baseline"`). **Status: passes local rerun (CI seal + individual seal, this session; GitHub Actions run success independently confirmed this assembly pass); does not claim canonical-by-process.**

### 6.4 Two-QIT-engine whole-manifold sim (deep_integration lane)

`system_v8/deep_integration/manifold_qit_engines_full.py` (518 lines), line 4: "Whole manifold + TWO QIT engines running together for 60 ticks, with qutip as the solver stack (the independent QIT-engine referee doubles as the runtime)." Line 7: "UNOFFICIAL / working-sim bar. NOT proof-level. promotion_allowed=false." A LEFT engine runs the 8 left-sheet `stage64` operating generators forward; a RIGHT engine runs the same 8 generators complex-conjugated in reverse order (chirality = schedule orientation), coupled by an entangling XY pulse each tick, read out via `ptrace`/`entropy_vn`/`negativity`/`Phi0` (the `manifold_one` cut-family convention, weights [0.5, 0.5]).

Result `system_v8/deep_integration/results/full_sim/receipt.json`: `all_pass: true`, `promotion_allowed: false`, `claim_ceiling: "executed 60-tick integrated instance of manifold drive + two chirality-split QIT engines on qutip; unofficial working-sim bar; no uniqueness, optimality, or physics claim beyond the executed checks"`. Selected findings on file: chained-count drive matches cumulative Hartley capacity to 166.255997 bits exactly; chirality flux splits over 7 cycles with linear-fit slope 0.2159 rad/cycle, \(R^2=0.98239\); joint `max I(L:R)=0.2804` bits, `max negativity=0.093315`; four negative controls all fire as designed (freeze/scramble/erase/decouple). A prior run under the raw receipt stage order is kept, not discarded, as an honest negative: `results/full_sim_run1_receipt_order_flux_negative` — "family f+/f- blocks compose to ~identity, chirality flux degenerates" — behind the now-declared interleaved traversal. Status: **exists, receipt on disk shows all_pass true; not rerun this session.**

Adjacent, unresolved: **`system_v8/histories_referee/mcwf_referee_v0.py`** — a Monte Carlo wave-function (quantum-trajectory) referee meant to cross-check the same GKSL law family by unraveling `qutip.mcsolve` against `mesolve`. Per `system_v8/tool_ledger/TOOL_LEDGER.md` (lines 159-161), the prior run hit a real qutip API-usage bug — `res.states` from `qt.mcsolve` at `ntraj>1, store_states=True` returns arrays, not per-trajectory `Qobj` lists — "a genuine `qutip.mcsolve` API-usage bug in the referee script ... left un-fixed with the crash recorded." Currently on disk, `system_v8/histories_referee/results/` contains only `mcwf_referee_v0_blocked_20260719/` (verified via `ls`) — no receipt for `mcwf_referee_v0` itself exists. **Status: BLOCKED, OPEN** — what would settle it: a fix to the `run_mcwf_ensemble` loop's assumption about `mcsolve`'s per-version return shape.

### 6.5 ALT engine types the sim estate can run beyond the owner model

Everything below is labeled **OPTION-not-canon**: capability demonstrations that a differently-shaped engine could be built, not evidence that the owner's Axis-0/QIT model requires or licenses them. Primary evidence source: `sim_engines/stress/` (repo root, outside `system_v8/`), 7 probes described in `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md` line 126 as "unofficial_stress_probe, promotion_allowed=false, parks by definition." **All 6 of the following stress-probe scripts were freshly rerun this session** (`/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 sim_engines/stress/<probe>.py`); each reproduced `all_checks_pass: true` with only the `seconds` timing field differing from the committed receipt (diffs reverted via `git checkout --` afterward, so the working tree is unchanged) — status for each: **passes local rerun, this session**.

| ALT engine type | Library (today) | Stress-probe evidence (this session) | First official sim would be | Effort |
|---|---|---|---|---|
| Classical automata / dynamical-systems | Julia `DynamicalSystems.jl` + `Attractors.jl` v1.38.4 | `sim_engines/stress/attractors_basins_probe.py`/`.jl` → `results/attractors_basins_probe.json`: Newton-map basins of \(z^3-1\), `AttractorsViaRecurrences` on a 101×101 grid finds exactly 3 attractors at the cube roots (`max_distance` to sympy-exact roots = 1.11e-16), basin fractions ≈1/3 each; negative control on \(z^1-1\) correctly finds 1 attractor. Also corroborated in `system_v8/engine_estate/results/julia/receipt.json` (`attractors_bistable_basins_L13`, PASS). | A committed `system_v8` "basin/attractor engine" lane comparable to `thermo_engines/`: map a real receipted GKSL/coupling law onto a dynamical system, extract basins/Lyapunov spectrum, compare to a closed-form or SMT-checked control. | Small — the stress probe is already most of the wiring; promoting it needs a `TOOL_MANIFEST`/classification header and a second (JAX or Julia-authoritative-pair) leg. |
| Stabilizer / Clifford | Julia `QuantumClifford.jl` 0.11.4 | `sim_engines/stress/quantumclifford_orbit_probe.py`/`.jl` → exhaustive 2-qubit signed-Pauli-pair enumeration (435 pairs considered, 240 rejected anticommuting, 15 rejected dependent) finds exactly 60 unique canonical stabilizer tableaux, matching the closed-form count \(2^n\prod(2^k+1)\) computed independently in sympy; 1-qubit negative control gives 6, not 60. | A stabilizer-circuit engine (Clifford-only GHZ/graph-state family) cross-checked against the existing dense-density-matrix (`QuantumOptics`) and MPS (`ITensors`) legs on the same states. | Medium — needs a real circuit family and a cross-engine agreement gate, not just an enumeration count. |
| Tensor-network / MPS | Julia `ITensors.jl`/`ITensorMPS.jl` 0.9.30/0.4.1 | `sim_engines/stress/itensors_mps_cut_probe.py`/`.jl`: 8-site GHZ MPS, bond dimension 2 at the cut, cut entropy = 1.0 bit (`div_from_closed_form: 0.0`); product-state negative control gives 9.6e-16 bits; cross-checked against dense `QuantumOptics` on GHZ-4 (1.0000000000000002 bits). Also in `system_v8/engine_estate/results/julia/receipt.json` (`itensors_schmidt_cut_L7`, PASS). | An MPS-native engine for a system size where dense density matrices become impractical (e.g. an 8-16 site chain), with the current dense legs kept as the small-size cross-check. | Medium-large — genuine payoff requires a system size dense methods cannot reach; at current small sizes it is a cross-check, not a capability gap-filler. |
| Open-system GKSL (time-dependent) | JAX `diffrax` 0.7.2 + `dynamiqs` | `sim_engines/stress/diffrax_lindblad_cycle_probe.py`: time-dependent Lindblad solve (ramped drive) against a closed form (max div 4.82e-9) and against `dynamiqs.mesolve` (4.81e-9); Gibbs-ratio-at-equilibrium check (div 1.7e-14); frozen-population and flipped-sign negative controls both fire correctly. Per `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md` line 124, this is the top-ranked adopted library pairing: "diffrax->carnot+otto (time-dependent Lindblad cycles — clears 2 CI-reds + the open-system-dynamics capability gap)." | Fold the already-demonstrated time-dependent (ramped-Hamiltonian) Lindblad solve into the Otto/Carnot engines themselves, replacing the current constant-Hamiltonian-per-stroke approximation. | Small — the capability is demonstrated; the remaining work is wiring it into `quantum_otto_engine_jax.py` as a genuine time-dependent stroke rather than piecewise-constant. |
| OT / geometry | JAX `ott-jax` 0.6.0 | `sim_engines/stress/ott_w2_eigdist_probe.py`: Sinkhorn \(W_2\) distance between eigenvalue-cloud distributions of two density matrices, cross-checked against a pure-python exact 1-D sorted-coupling closed form (`sinkhorn_w2sq` = 0.008127... matching within `rel_tolerance: 0.001`); negative control on identical spectra gives W2² = 5.7e-12, correctly below the distinct-spectra floor of 0.001. | An optimal-transport-based distance/geometry engine comparing the QIT engines' state trajectories (e.g. Otto-cycle spectral flow) via W2 rather than trace distance or relative entropy alone. | Medium — needs a real trajectory to compare, not synthetic eigenvalue clouds; the transport-solver plumbing itself is already proven. |
| Finite-field / algebraic | Python `galois` 0.4.11 | `sim_engines/stress/galois_field_ladder_probe.py`: GF(2^8) primitive-element order = 255 (`sympy_prime_factors_255 = [3,5,17]`), Frobenius freshman's-dream identity holds in GF(7^3) and fails over `Z` (negative control fires), subfield fixed-point ladder GF(2^1..2^8) exact at every level. Also load-bearing today in `system_v8/deep_integration/results/dynamics_fields/receipt.json` (GF(7)/GF(8) word-match and unit-closure checks). | Per `INTEGRATION_INVENTORY_AND_CAMPAIGN.md` line 124, the ranked next step is `galois->algebra_ladder` — wire the finite-field ladder into the `algebra_ladder` arrow as a load-bearing decision, not just a capability probe. | Small — already load-bearing in one arrow (`dynamics_fields`); extending to `algebra_ladder` is a scoping exercise, not new capability. |
| Hopfield / QHN candidate | Python `pennylane` 0.44.1(+lightning) | Weakest evidence of the eight: no Hopfield-specific test exists anywhere searched (`grep` for `Hopfield`/`QHN` across `system_v8` returns only two negative notes — `system_v8/spinor_jepa/lane2_vector_jepa/run_lane2.py:610` "no energy/Hopfield structure is [charged]" and `lane5_multivector/run_lane5.py:792` "No Hopfield/energy structure charged". The only pennylane evidence found is a generic "pennylane Bell circuit" smoke line in `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:119` (one of 14 one-real-operation smokes; no located script or receipt for this specific line beyond the summary row — **UNCERTAIN**, could not verify further). Pennylane's stronger, unrelated integration (`system_v8/tool_ledger/TOOL_LEDGER.md:126`: KAK-compiled two-sheet unitary stage circuit, unitary-vs-`expm` diff 8.713e-15) demonstrates pennylane can build real circuits, but not a Hopfield/QHN one specifically. | A quantum Hopfield/associative-memory circuit (parameterized energy landscape, basin-of-attraction readout) built and cross-checked the way the Bell-circuit smoke and the KAK-stage circuit already are (cirq/qiskit third-engine agreement, per `TOOL_LEDGER.md:149-150`). | Large — no Hopfield-specific object exists yet; this is a new candidate from nothing, not a promotion of existing evidence. |
| FEP / active-inference | Python `inferactively-pymdp` 1.0.3 | Two live, conflicting readings on disk, held apart rather than collapsed: (a) `system_v8/tool_ledger/TOOL_LEDGER.md:18` records pymdp as **INTEGRATED** — a real 2-state/2-obs POMDP `Agent(A,B,D)` whose A-matrix is the empirical probe-outcome distribution of one real packet (`obj-000:view:1`), one `infer_states()` belief update moving the posterior 0.5000→0.6000 in the correct Bayesian direction (`system_v8/tool_ledger/results/pymdp_result.json`, `system_v8/tool_ledger/test_pymdp_active_inference.py`); (b) `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md` lists `inferactively-pymdp 1.0.3 (active inference/FEP)` under its "AVAILABLE (installed, importable, NOT load-bearing in any committed arrow yet)" tier. Both are accurate at their own level: at the **tool-integration-probe** level pymdp has been run and gives a real result; at the **engine level** (a candidate ALT engine comparable to `thermo_engines/carnot_engine.py`) nothing exists — `find system_v8 -iname "*fep*" -o -iname "*active_inference*" -o -iname "*pymdp*"` returns only the one tool-ledger probe file and its result JSON, no dedicated FEP/active-inference engine directory. | A committed active-inference engine: a real receipted GKSL/manifold observation stream driving a pymdp `Agent` across multiple ticks (not one belief update), with a shuffled-observation and frozen-agent negative control analogous to `engine_processor_v0.py`'s controls. | Medium — the one-shot integration probe already proves the library works on real data; the gap is scaling one belief update to a multi-tick engine with controls, not first-time integration. |

### What is absent or unverified

- No repo file implements the section-8 formulas `\mathcal I^y_{e,\ell,r,x}` or `\mathcal E_{e,\ell}` literally; `stage64_constraint_tournament.py` and `engine_processor_v0.py` are independently-authored, pre-existing objects that address similar generic requirements (a 16-cell stage grid; per-stage informational work) under different formalisms. Treating any of them as "the" implementation of the Gemini-doc contract would be the exact conflation section 4.3 itself warns against.
- The specific "pennylane Bell circuit" smoke test named in `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:119` could not be located as a standalone script or receipt beyond that one summary line — marked UNCERTAIN; would be settled by finding or rerunning the underlying smoke script.
- `mcwf_referee_v0.py` is BLOCKED on a real `qutip.mcsolve` API-usage defect (multi-trajectory `store_states=True` return-shape mismatch); no receipt exists on disk. Would be settled by fixing `run_mcwf_ensemble`'s assumption about `mcsolve`'s per-installed-version return type and rerunning.
- Thermo-engine `SIM_TEMPLATE` lineage (per `system_v4/probes/SIM_TEMPLATE.py`) was checked only for `carnot_engine.py` (string absent); not checked for `szilard_engine.py` or `quantum_otto_engine.py`. None of the three claims canonical-by-process, so this gap does not affect their stated ceiling.
- `manifold_qit_engines_full.py`'s `results/full_sim/receipt.json` (`all_pass: true`) was read from disk, not rerun this session — status is exists/receipt-on-disk, one rung below the "passes local rerun, this session" label given to the six ALT-engine stress probes and the CI seal.

### Absent / unverified (index)

- A literal repo implementation of the Gemini-doc stage instrument `I^y_{e,l,r,x}` or engine composition `E_{e,l}` formulas is ABSENT; `stage64` and `engine_processor_v0` are different, independently-authored objects.
- The specific "pennylane Bell circuit" smoke test (`INTEGRATION_INVENTORY_AND_CAMPAIGN.md:119`) has no located standalone script or receipt beyond the summary line — UNCERTAIN.
- `mcwf_referee_v0` has no receipt on disk (BLOCKED on a real `qutip.mcsolve` API-usage defect, unresolved).
- `SIM_TEMPLATE` lineage for `szilard_engine.py` and `quantum_otto_engine.py` not individually checked (only `carnot_engine.py`, where the string is absent).
- `manifold_qit_engines_full.py`'s `full_sim` receipt (`all_pass` true) was read from disk, not rerun this session.

---

## 7. Fuel-not-canon proposals, negatives, alt sims, gaps, uncertainties

Status ladder used throughout: `exists < runs < passes local rerun < canonical-by-process`. Integration levels: `L0 available` / `supportive` / `load_bearing`. Epistemic labels: `CANON` (owner docs) / `FUEL-proposal` / `DEMOTED` / `KILLED` / `OPEN`. Every item cites its file. Nothing in this section is canon; that is the point of it.

### (a) FUEL pile — proposed, not canon

**Judge/weakness-relation proposals**

- D1–D4 rival demand/probe families — `system_v8/candidates/judge_rival_demand_families.md`. Four candidate `(D,M)` judge families (conditional-continuation "thin-plus", cut-conditioned joint-vs-marginal, outer-regrouping/associator, future-viability backpressure) proposed to replace the base campaign's two-anonymous-packet judge. A table (lines 273–280) states which candidate pairs each family *could* separate; "both remain" is the stated default outcome, not a kill. Status: `exists`; every family flagged `PROPOSED_NOT_YET_SIMULATED` (line 7) until source-native transcript rows are supplied. FUEL-proposal.
- 4 rival weakness (≼) preorders — `system_v8/candidates/judge_rival_weakness_relations.md`. Resource (description-length), categorical (factorisation/universal-property), predictive (continuation-language reachability), and dynamical (basin-size) preorders proposed against the installed partition-refinement `≼_part` (`system_v7/constraint_core/RATCHET_SPEC.md` §6). Each section predicts a different reordering of {spinor/QIT, classical-relational, nonassociative, top-down} than the current ranking (summarised lines 137–142). Status: `exists`, none executed against real data; explicitly "conditional throughout" (line 3). FUEL-proposal.
- Presumption-ranking void — `system_v8/candidates/STRAWMAN_AUDIT.md` → `PRESUMPTION_RANKING_CORRECTION.md` → `RANKING_VOID_llm_did_ratchets_job.md`. The original structure-count ranking (classical < spinor/QIT < nonassoc < top-down) was first corrected by a second LLM pass, then the entire exercise was voided: "An LLM computing relative MSS / presumption is an LLM pretending to be the ratchet. BOTH rankings are void." (`RANKING_VOID_llm_did_ratchets_job.md`). All three documents are `exists`, immutable receipts; the void is itself FUEL, not a resolved verdict — no presumption ranking currently stands.

**Rival manifold candidates (system_v8/candidates/, all `promotion_allowed: false`, `formal_admission_allowed: false`)**

- `candidate_classical_bottomup_v2.md`, `candidate_spinor_qit_v2.md`, `candidate_foreign_nonassoc_v2.md`, `candidate_topdown_12to0_v2.md` — v2 restatements of the four standing rival carriers (finite relation / spinor-QIT-density / octonion-nonassociative / 12-to-0 top-down schedule). Each v2 names its diff from v1 explicitly (e.g. `candidate_foreign_nonassoc_v2.md` §9) rather than silently overwriting; v1 files remain on disk unchanged as history. Status: `exists`, authored proposal, not executed code.
- `candidate_ablation_flattened.md` — nesting/composition-flattened ablation control against `candidate_classical_bottomup.md`, filling the fuel-adequacy gate's `ablation_control` slot (`fuel_gate/fuel_adequacy_gate.py`).
- `candidate_countermodel_no_mechanism.md` — lookup/replay countermodel that reproduces the observed pair-level result tables *without* the claimed relational mechanism, filling the `countermodel` slot.
- `candidate_middle_out_order_rival.md` — bidirectional-from-a-middle-layer schedule, authored by an NVIDIA-hosted model (`qwen/qwen3-next-80b-a3b-instruct`), explicitly built to fill a gap `candidate_topdown_12to0.md`'s own weaknesses section names but does not build.
- `candidate_stress_variant_stochastic_counts.md` — stochastic-count structural rival, authored via `grok` CLI (`grok-build-0.1`), framed as a stress-variant whose whole claim rests on a named adversarial stress it must survive.
- Three stage-5 build cards, `system_v8/candidates/cards/CARD_assoc_sign_order_branch.md`, `CARD_hopf_fiber_phase_forget_arrow.md`, `CARD_schmidt_tori_foliation_arrow.md` — proposal-sim cards (not yet built) extending the committed `law_order_branch`/`pure_to_vn` arrows into the owner-open associativity/anticommutativity ordering and the Hopf-fibre phase-forget and Schmidt-torus-foliation rungs. Ceiling on every card: `classification = "tool_lego_fit_probe"`, `promotion_allowed = false`, `ordering_status = "PROPOSED not canon"`.

**Rival bridge / arbiter fuel**

- `bridge_word_bfs.py` vs `bridge_action_predictive.py` — `ratchet_contract/bridge_validation/`. Two independently built predictive-quotient bridges (forward word-BFS/union-find vs bounded backward color-refinement) cross-checked over 17 toy cases (`results/rival_agreement.json`: `cases_checked: 17, all_agree: true`) plus a 10-case control battery (`stress_rival_agreement.json`). New this session: `mutation_arbiter_test.py`/`results/mutation_arbiter_test.json` deliberately faults each bridge (`depth_off_by_one`, `prefix_comparison_skipped`, `memo_poisoned`, `base_case_wrong`) to check the agreement test can detect faults. 3 of 4 faults are caught (`disagreement_found: true`); `prefix_comparison_skipped` on `bridge_word_bfs` is **not** caught (`coverage_finding: true`) — a live coverage gap in the 17-case battery, named not fixed. All: `promotion_allowed: false`, "practice/fuel development only" (own `scope` field).
- `extension_fibre_capacity.py` — `ratchet_contract/ratchetings/extension_fibre_capacity.py`, result `results/extension_fibre_capacity.json`. Proposes a quantitative Hartley/Rényi-0 "extension-fibre capacity" `κ_{A/B}(ρ_B) = log|F_{A/B}(ρ_B)|` on top of the committed `cut_dependent_entropy` one-way-marginalization witness. Provenance note in the file itself: a GPT-webui pack (`scratchpad/ratchet190/.../manifold_sim.py`) already computed a similar field; that pack's self-grading is explicitly **not adopted** — this is an independent minimal rebuild citing the pack only for the idea. Result: `verdict: FIBRE_CAPACITY_MEASURES_ONEWAYNESS`, two independent engines (Julia+QuantumOptics canon, JAX+dynamiqs) agree to <1e-9, `max_cross_engine_divergence: 0.0`. Status: passes local rerun; ceiling `classification: tool_lego_fit_probe`, `promotion_allowed: false`, `ordering_status: "PROPOSED not canon"`.
- `cut_dependent_entropy_nvidia_referee.json` — `ratchet_contract/ratchetings/results/`. A REFUTE-FIRST adversarial NVIDIA cross-family panel (4 live models: deepseek-v4-flash-probed-but-capacity-exhausted, meta-llama-3.3-70b, openai/gpt-oss-120b, nvidia-nemotron-super-49b, mistral-nemotron) run against the committed `cut_dependent_entropy` claim. `verdict_tally: {SURVIVES: 4, REFUTED: 0, OPEN: 0}`, `any_refutation: false`. Two models independently converged on the same unexcluded confound: the claim is established only for the pure two-qubit family, not mixed states or higher dimensions — an open boundary the sim's own docstring already concedes (`ordering_status: "PROPOSED not canon"`). This is cross-model FUEL evidence for the claim, not a ratchet verdict — the panel is advisory, not an admission gate.

**Other proposed-not-built lanes named in the estate**

- Checkerboard admissibility — `system_v4/probes/sim_checkerboard_admissibility.py` (v4-era; also referenced as ring-checkerboard step-counts 2×2/4×4/8×8 in `MODEL_DOSSIER/00_DURABLE_STATE_20260721.md` line 46 as one of the VARIABLE shell topologies in the open frame 𝔊). Not re-run this session; `exists` only, superseded-generation lane.
- Dynamics-identification "arbiter" lanes — `pysindy`/`pykoopman`/`PyDMD`/`derivative` are listed **AVAILABLE** for "Koopman/SINDy arbiter lanes" (`system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:30,35`). Caveat: `pysindy` itself is *not* fuel — it is already `INTEGRATED` and `load_bearing` on the `dynamics_fields` receipt (`system_v8/tool_ledger/TOOL_LEDGER.md:124`, `system_v8/deep_integration/tools_dynamics_fields.py`). No file on disk names a "PySINDy-residual" lane verbatim; the unbuilt fuel item is specifically the *arbiter* comparison against `pykoopman`/`PyDMD`, not PySINDy's own use.
- Quantum Hopfield memory — `system_v7/constraint_core/MODEL_LAYER_LEDGER.md:855` (`quantum_hopfield_memory_sim.py`). Explicitly labeled "Hypothetical lane; owner doctrine under test" — earns "memory as energy-descent recall" and a 3-qubit floor, "does NOT claim biological plausibility or a derived-from-Hamiltonian energy." No literal "QHN" token found on disk; ABSENT under that name — the real artifact is the Hopfield-class quartic sim above.
- kingdon multivectors — currently `INTEGRATED` (not FUEL): `MODEL_DOSSIER/01_INTEGRATION_INVENTORY.md:180`, "float64 Cl(4) recomputation of the Julia gamma5 receipt, all 3 residuals 0.0." Listed here because the task named it; its actual status is a supportive cross-check tool, already load-bearing-adjacent, not a pending proposal.
- Holodeck / JEPA — `system_v8/loop2_world` (`perception_intelligence_v0.py`), receipt `system_v8/loop2_world/results/intelligence/receipt.json` per `MODEL_DOSSIER/04_LAYERS_L9_UP_AND_FIELD.md:129`. JEPA-proto lane is `all_pass: false` (self-reported, red check named): `belief_persistence_holevo_above_permutation_null` is `false` (0.00428 bits vs null p95 0.00436 — just under). This is an honest-negative FUEL result, not a working capability.
- Packet-mode spine — `sim_engines/serialized/serialized_stage.py` (`SPINE_PACKET=<path.json>` env-var dispatch). Per commit `1760f9a4a` ("spine(partial, deferred): packet-mode scaffolding in serialized_stage.py ... INCOMPLETE by owner reprioritization (engines first); canary mode intact and regression-tested"). Status: `exists`, partial, deliberately deferred, not finished.
- Gate M5 "claim semantic witness binding" — named in `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:65` as one of the items **kept** from an otherwise-rejected Gemini stack proposal ("hardens the ClaimGate metadata-trust holes — worth building"). Also referenced in the withdrawn `claimgate_plugin/lev_patch/claim-admission.ts:35` ("Gate M5 UNSAT verification"). Status: named requirement, not implemented; ABSENT as code.

### (b) NEGATIVES preserved

| Item | Receipt / evidence | What happened | Label |
|---|---|---|---|
| `mcwf_referee_v0` blocked | `system_v8/histories_referee/results/mcwf_referee_v0_blocked_20260719/receipt.json` | `"status": "BLOCKED_MEMORY_GUARD"`, `"message": "refused to import qutip: available system memory 21.459% < 25% threshold. No sim executed."` The prior `results/mcwf_referee_v0/` path was moved to this `_blocked_20260719` path per commit `12422c278`. `promotion_allowed: false`. | BLOCKED (self-refused, not a science failure) |
| `physics.claim-admission` finalizing TS capability | `claimgate_plugin/lev_patch/claim-admission.ts:1-12` | File header: `"WITHDRAWN 2026-07-22 (webui audit) — do not implement as written."` Reason on file: it collapsed claim intake, truth evaluation, and canon-writing into one function; Lev claim admission must stay non-final, with `core/eval` (present in `lev-main`, per commit `eba31410f`) owning truth evaluation and a separate policy/settlement layer owning finalization. The invented `registerCapability`/`@lev-os/flowmind-types` surface does not exist in Lev either. Replacement: `claimgate_plugin/claim_admission.mjs` relabeled as a non-final CR-side envelope check. | WITHDRAWN (kept on disk as an honest negative, per file's own comment) |
| Rejected library pairings | `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:125` | Verbatim: "Rejected w/ reason: netket-NQS szilard (speculative research, not integration), quimb-PEPS for 2-qubit basis sim (overkill), jax-verify->root_foundation (domain mismatch — finite/symbolic arrow)." Note: `netket` and `quimb` are elsewhere `INTEGRATED` for *other* arrows (`MODEL_DOSSIER/01_INTEGRATION_INVENTORY.md:85,92`) — the rejection is pairing-specific, not a library-wide ban. `jax-verify` is separately `BLOCKED` on its own import in two batteries (`MODEL_DOSSIER/01_INTEGRATION_INVENTORY.md:183,254`: `AttributeError: module 'jax.lax' has no attribute 'standard_naryop'`). | REJECTED (pairing-specific) / DEMOTED (jax-verify import-blocked independently) |
| Gemini stack rejection | commit `df89108aa`, `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:65` | Verbatim: "Gemini chain verdict: stack REJECTED (cuts dynamiqs = breaks 4 working arrows; core = unintegrated pennylane/kingdon/V-JEPA2 + env-incompatible PythonCall/DLPack bridge not in carrier). KEEP: the M1 survival rules, the 4 engineering laws (SMT isolation, dimensionality bottleneck, DLPack layout-transpose, jaxtyping padding), and Gate M5..." | REJECTED (stack), with 5 named sub-items KEPT explicitly |
| S³-as-minimum-forced | memory `project_constraint_manifold_derivation_result.md` (2026-06-03, 48 days old at time of read — flagged stale by the harness itself); on-disk evidence: `system_v5/julia_carrier/nonchiral_carrier_f01n01_negative_control.jl` + `..._results.json` | Result JSON: `"forced_or_chosen": "chosen_principle"`, `"classification": "diagnostic_only_negative_control"`, qubit_dim2 carrier `"chiral": false, verdict": "admitted nonchiral"`. F01+N01 (finitude + noncommutation) admit a FAMILY {dim 2,3,4,6,8}→S³,S⁵,S⁷...; dim=2→S³ is a named MINIMALITY CHOICE, not forced. Codex2's initial "forced" claim was rejected by a grok+gemini adversarial cross-check per the same memory file. | KILLED (the strong "S³ forced by F01+N01" claim); the weak "S³ admissible as a choice" survives. On-disk receipt confirmed — this is not memory-only. |
| Fuel-vs-canon presumption ranking | see (a) above, `RANKING_VOID_llm_did_ratchets_job.md` | Both the original ranking and its correction voided. | VOIDED (no ranking currently stands) |
| ClaimGate self-audit misses (6, historical) | `claimgate_plugin/CLAIMGATE_POSTMORTEM_20260722.md` | Named misses, each with a "why missed" and a "now encoded" fix: (1) trusted `engines_ran: true` metadata instead of re-deriving; (2) mock stages could reach ADMITTED; (3) a SAT/counterexample treated as an infrastructure crash (exit 1) instead of a completed negative result; (4) `physics.claim-admission` self-certifying (see WITHDRAWN row above); (5) claim ceilings absent (a 2-colorability witness read as "physics"); (6) no hostile-control suite existed before this session's stress work. All fixed per the file's "Now encoded" fields, EXCEPT item 6, which names the hostile-control suite as "the next ClaimGate deliverable" — since then partially built (see the stress ledger in (c)). | 5 of 6 fixed-and-encoded per file; 1 in progress |

### (c) GAPS — with proposed solutions and named uncertainty

**1. Three ClaimGate hostile gaps (proven HOLEs, fix sketches routed not applied)** — `claimgate_plugin/stress/CROSS_MODEL_STRESS_LEDGER.md`, section "Holes routed, not fixed here" (verbatim fix sketches, none of the three files edited this session):
  - `claimgate/claimgate.py`, `requires_control_rigor()` (cited at line ~179): a receipt with `classification == "canonical"` but no `accepted_status_label` and `promotion_allowed: false` is **admitted** (exit 0) when it should be rejected as self-contradictory. Fixture: `stress/holes/tier0_cand4_canonical_no_controls.json`. Fix sketch: fire control-rigor on `classification == "canonical"` directly, or reject the classification/promotion/no-status-label combination outright.
  - `claimgate.mjs` and `claimgate/claimgate.py`, both: no content-level SMT-mechanism-vs-tautology detector exists. A generic single-valued-function tautology (`recover(k)==A and ==B -> A==B`), repackaged with a valid `preregistered` block and `classification=canonical`, is admitted on **both** gates (exit 0). Fixture: `stress/holes/smt_clean_tautology_admitted_by_both_gates.json`. Fix sketch (named as harder/judgment-shaped): require SMT constraints to reference the receipt's own claimed objects/operators, not a domain-free skeleton — flagged for design discussion, possibly belongs at the fresh-audit layer rather than the deterministic gate.
  - `ratchet_floor.py`, `token_similarity`/`nearest_key` (cited at line ~84): Jaccard token-set similarity misses `gk.acc` vs `gk.accuracy` (score 1/3, below the 0.5 rename threshold), so a renamed key with a 10-point regression is silently admitted as a "new floor" under `--allow-new-keys`. Fixture: `stress/holes/floor_renamed_key/`. Fix sketch: add prefix/substring/edit-distance scoring alongside Jaccard, and surface the rename hint even under `--allow-new-keys`.
  Manifest evidence: `node gatecheck.mjs stress_manifest.json` → `cases_run: 17, trusted: false, verdict: GATE_REJECTED, 13 ok, 4 failures` — the 4 failures are exactly these 3 named holes (the SMT hole counted twice, once per gate). `gatecheck` correctly refuses to certify the estate clean until these are fixed. **UNCERTAIN**: whether a schema-valid disguised trap would be caught by the meta-gate's (`gatecheck.mjs`/`evalcheck.mjs`) semantic-discrimination logic is explicitly named as untested — the three meta-gate catches on record were all schema-level (exit 2), never semantic (exit 1). Settling this needs a schema-valid meta-gate trap fixture, not yet built.

**2. Settlement machinery (slices D–F) unbuilt** — `claimgate_plugin/CLAIMGATE_POSTMORTEM_20260722.md` names the pattern (claim intake → `core/eval` → policy → settlement must stay separate links, not merged) and the withdrawn `claim-admission.ts` names the missing native seam (`lev.call`, "currently a design-doc span name, not yet wired"). No slice D/E/F plan file was found on disk under this literal name; ABSENT as a named plan — the closest artifact is the ordering statement itself in the postmortem and in `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md`'s "bridge is `orchestration claimgate-steering consume`" line. Proposed solution (inferred from the postmortem's own stated architecture, not an existing card): author slice cards for (D) non-final claim intake wiring, (E) `core/eval` policy composition, (F) settlement/canon-write, each gated by the same envelope check pattern already proven for the CR-side link.

**3. D2 (nonassociativity slot in C_t) OPEN** — memory `project_ratchet_v0_2_landing_20260710.md` (11 days old at read time, flagged stale by the harness): "D2 (nonassociativity slot in C_t) STILL OPEN — blocks the root presentation packet build" and later in the same file, "root presentation packet build dispatched to codex1 Sol-xhigh (D2 defaulted: nonassoc NOT in C_t, carried as open attack)." This is a memory-sourced claim about a 2026-07-10 session; no fresher on-disk resolution was found this pass. **UNVERIFIED-memory** pending a fresh read of the current `system_v7/constraint_core/ratchet/RATCHET_SPEC.md` root-presentation-packet code to confirm whether C_t now includes a nonassociativity slot. This is a *different* "D2" than the `judge_rival_demand_families.md` D2 (cut-conditioned joint-vs-marginal witness) above — same token, two unrelated objects; do not conflate.

**4. Tower co-ratchet dynamics UNEARNED** — memory `project_tower_assembly_campaign_20260704.md` (18 days old, flagged stale): the 12-rung tower chain (`tower_chain_run_v0`, commit `c0880bb6d`) runs green end-to-end but is explicitly `scratch_diagnostic/DRAFT_UNAUDITED`; "co-ratchet DYNAMICS still unearned" with an evening-update fork: "co-arm REAL (feedback-cut kills it), but rolling-vs-dead dice tie EXACTLY... THREE READINGS HELD: vocabulary-too-poor / observable-is-content-not-count / drive-doctrine-fails-at-toy-scale." Proposed next step per the same memory: resolve the fork by testing which of the three readings the tie survives under an enriched fact vocabulary. **UNVERIFIED-memory**, no fresher on-disk resolution found.

**5. PyTorch deferred (cloud GPUs)** — `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:64`: "PyTorch = LATER — needs rented cloud GPUs; deferred. Not required by the seal (2 engines suffice)." Two-engine seal (JAX + Julia) is the current requirement; PyTorch remains a first-class-when-scoped third leg per the `pytorch-sim` skill, not currently mandatory. Proposed solution: rent cloud GPU time when a PyTorch-load-bearing sim is actually scoped; no such sim is queued on disk currently.

**6. jax-metal / float32 conflict, M1 hardware ceiling** — `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md:64`: "Target machine = M1 MacBook Pro, 16GB unified memory... SEQUENTIAL engine execution (never JAX-Metal + PyTorch-MPS concurrently — swap-death); JAX preallocation off (`XLA_PYTHON_CLIENT_PREALLOCATE=false`); half-precision perception models when PyTorch is eventually used; ~4-6GB active RAM ceiling per stage." Separately, `torch_ga` is `PRUNED (float32-only)` (`MODEL_DOSSIER/01_INTEGRATION_INVENTORY.md:106`): under `torch.set_default_dtype(torch.float64)`, `geom_prod` raises `expected m1 and m2 to have the same dtype: float != double` — hard-coded float32 internals, not float64-safe. These are two distinct float32 issues (an M1 concurrency/precision engineering rule vs. a specific library's hard-coded dtype) that the task's phrasing conflates; both are named, neither is resolved by a workaround on disk.

**7. Trust-root writability** — `claimgate_plugin/FIXTURE_CORPUS.md` lines ~91-93: "TRUST-ROOT BOUNDARY (open, deployment-level): gate_registry.json + evaldeck + the fixtures live in the agent-writable repo today. 'External policy' is only real once they move to a branch-protected / CODEOWNERS / harness-owned path. claim_verify cannot self-enforce its own registry's immutability." Named as "the honest limit, not a bug to fix" alongside the CONSENSUS RESIDUAL finding (a semantically-wrong-but-structurally-clean artifact passes every mechanical gate; only bounded LLM audit — tier4 — catches it, and tier4 itself needs the trust root protected). Proposed solution (stated, not implemented): move `gate_registry.json`/evaldeck/fixtures to a branch-protected or CODEOWNERS-gated path outside agent write access.

**8. Lev claim-intake absent-by-name** — commit `eba31410f` (git-log-verifiable): "Lev binding inventory vs ~/lev-main: lev.call ABSENT(unwired), claim-admission-v1 ABSENT-by-name, core/eval PRESENT w/ CR eval tests, exec-receipts PRESENT, agentfs-sdk ABSENT, AgentPing PRESENT w/ authority limits." No file on disk under `claimgate_plugin/` or elsewhere in this repo currently restates this inventory as a standing doc — it is a commit-message-level finding, not re-verified against the current `~/lev-main` worktree this session. **UNVERIFIED** without a fresh grep of `~/lev-main` itself (outside this repo's tree), which this pass did not perform.

**9. 64→16 reduction — two distinct, non-conflicting readings found; neither is "an experiment not run" in a simple sense**
  - Reading A (system_v6/v4-era, historical): `system_v6/receipts/workedout_possibilities_mining_20260609.md:316-390` documents an "Open 64->16 equivalence warning" from `system_v4/docs/ENGINE_64_SCHEDULE_ATLAS.md:367-370`: two different 8-way constructions coexist in owner source surfaces, and the 64-runtime-step / 16-chart-locked-macro-stage relationship was flagged unresolved at that time. This thread is superseded by the current system_v8 engine-ontology work below and was not re-run this session.
  - Reading B (current, system_v8): `MODEL_DOSSIER/05_ENGINE_STAGES_LOOPS_CYCLES.md:19` and `system_v8/nested_manifold/results/stage64/receipt.json` — this reduction **has been measured**, not left unrun: of the 64-candidate grid, 16/64 (25%) are the executed dynamics, a further 16/64 are selection-load-bearing-only (`deletion_partner_under_determined: true` for all 16), and the remaining 32/64 (50%) are demonstrated inert by an actual executed deletion test (`deletion_killed_wall_outcome_unchanged: true` for all 16 affected stages). Caveat carried from the same file (§6, line ~363): these deletion-test gates are themselves construction identities of a fixed 2×2 commutator grid — "32 are provably inert" is a sound arithmetic fact about this specific structure, not evidence the tournament could have picked differently, because it structurally could not.
  **This is a genuine ambiguity, not a settled fact**: if "the 64->16 experiment" in the task brief refers to Reading A (the open equivalence warning), it remains OPEN/UNVERIFIED against current code. If it refers to the operating-candidate count, it is Reading B and has in fact been run, audited (`system_v8/nested_manifold/results/stage64/AUDIT_VERDICT.md`, commit `a95b859ce`), and explicitly capped as a construction-identity result, not a discovery. Both readings are held here rather than collapsed.

**10. P-vs-NP direction (owner hypothesis, first tooth not built)** — memory `project_qit_engines_p_vs_np_direction.md`: owner (2026-07-21) — "the qit engines themselves can get at p vs np as a problem fundamentally. maybe even solve it." Rigorous anchor named: `a = a iff a ~ b` IS Myhill–Nerode (partition kernel = minimal-DFA/lower-bound technique — "the one place the axiom already IS the proof technique"). Strongest defensible form named: P≠NP as a computational second law / Carnot-bound analogue. Barriers explicitly named (any claimed route must state which it evades): relativization/natural-proofs/algebrization, BBBV-Grover optimality, finite-run-cannot-settle-∀-claims, the XOR-SAT trap (clustered-hard solution geometry that is nonetheless poly-time via Gaussian elimination — geometry ≠ hardness), strict-finitism reformulation. First tooth specified but **not built**: (1) a complexity-terrain battery on the estate's own constraint packets with a 2-SAT positive control, 3-SAT hard-region test, and XOR-SAT negative control (a metric that calls XOR-SAT "hard" is reading geometry, not hardness — an honest-fail design); (2) a Myhill–Nerode partition-kernel-as-minimal-machine lane on finite languages; (3) a generation-vs-verification cost-curve measurement inside existing finite worlds/receipts. No file matching this battery (2SAT/3SAT/XOR-SAT terrain sweep) was found on disk this pass — ABSENT as executable code; the legacy `system_v4/probes/p_vs_np_sim.py` (cited in `READ ONLY Legacy core_docs/deep_research_results/DR_p_vs_np_qit.md`) is a different, older toy framing (verification-as-projection-overlap vs generation-as-random-CPTP-search) and is not the same battery.

### (d) UNCERTAINTIES — live divergent readings, held plural

- **S³/dim=2 minimality**: the killed reading is "F01+N01 force S³" (KILLED, see (b)). The surviving reading is "F01+N01 admit a family {dim 2,3,4,6,8}→S³,S⁵,S⁷...; dim=2/S³ is a chosen minimality principle, consistent with but not derived from the root constraints" (`system_v5/julia_carrier/nonchiral_carrier_f01n01_negative_control_results.json`). What would settle it further: a named, separately-stated minimality axiom (M01) tested the same adversarial way the chirality and ordering claims were tested in the same memory thread — not yet attempted on-disk under that name.
- **64→16**: two live, non-conflicting readings held in (c)#9 above — an older open equivalence-warning thread (system_v4/v6-era, not re-run) vs. a newer measured operating-candidate-count result (system_v8, audited, capped as construction-identity). What would settle which the task brief meant: re-reading the original `ENGINE_64_SCHEDULE_ATLAS.md` 8-way-construction ambiguity against current `stage64_constraint_tournament.py` code to see if it was ever addressed, since the system_v8 audit trail does not cite the system_v4/v6 warning by name.
- **D2 nonassociativity slot**: OPEN per an 11-day-old memory note ("STILL OPEN," "carried as open attack"); no fresher on-disk resolution found this pass. What would settle it: read the current root-presentation-packet code/spec in `system_v7/constraint_core/ratchet/` for whether `C_t` now names a nonassociativity slot, and diff against the memory's "D2 defaulted: nonassoc NOT in C_t" claim.
- **Tower co-ratchet three-way fork** (vocabulary-too-poor / observable-is-content-not-count / drive-doctrine-fails-at-toy-scale): held plural in the source memory itself, unresolved as of that session. What would settle it: rerun the coratchet loop with an enriched fact vocabulary (the memory's own proposed next step) and check whether the rolling-vs-dead tie breaks.
- **Meta-gate semantic-discrimination question** (from (c)#1): whether `gatecheck.mjs`/`evalcheck.mjs` would catch a schema-valid disguised trap is explicitly named as untested in `CROSS_MODEL_STRESS_LEDGER.md` — "This is a genuine, narrow result... it is still OPEN whether a schema-valid disguised trap... would be caught by the semantic discrimination logic." What would settle it: construct a schema-valid (correct `id`/`cmd`/`args`/`expect_exit`, correct `evaluator`/`verdict`/`cases` deck shape) disguised-trap fixture and run it through `gatecheck.mjs`/`evalcheck.mjs` — not yet built.
- **cut_dependent_entropy scope boundary**: the NVIDIA referee panel returned unanimous SURVIVES (4/4) but two independently-responding models converged on the same unexcluded confound — the claim is established only for a pure two-qubit family, not mixed states or higher dimensions (`ratchet_contract/ratchetings/results/cut_dependent_entropy_nvidia_referee.json`). The sim's own docstring already concedes this scope limit (`ordering_status: "PROPOSED not canon"`), so this is a genuine, named, open boundary rather than a hidden gap — held open pending a mixed-state/higher-dimension extension, not yet built.
- **Lev claim-intake inventory freshness**: the `lev.call ABSENT`/`claim-admission-v1 ABSENT-by-name` finding is commit-message-level (`eba31410f`) and was not re-verified against the current `~/lev-main` worktree this pass. What would settle it: a fresh grep of `~/lev-main` for `lev.call` and `claim-admission-v1` outside this repo's tree.

### Sources read this pass

`system_v8/candidates/judge_rival_demand_families.md`, `judge_rival_weakness_relations.md`, `STRAWMAN_AUDIT.md`, `PRESUMPTION_RANKING_CORRECTION.md`, `RANKING_VOID_llm_did_ratchets_job.md`, all 8 `candidate_*.md` files and 3 `cards/*.md` files, `system_v8/candidates/superseded/*` (listing only); `MODEL_DOSSIER/00_DURABLE_STATE_20260721.md`, `01_INTEGRATION_INVENTORY.md`, `05_ENGINE_STAGES_LOOPS_CYCLES.md`; `claimgate_plugin/failures.jsonl`; `claimgate_plugin/stress/CROSS_MODEL_STRESS_LEDGER.md`, `stress_manifest.json`; `claimgate_plugin/FIXTURE_CORPUS.md`; `claimgate_plugin/CLAIMGATE_POSTMORTEM_20260722.md`; `claimgate_plugin/lev_patch/claim-admission.ts`; `system_v8/histories_referee/results/mcwf_referee_v0_blocked_20260719/receipt.json`; `system_v8/INTEGRATION_INVENTORY_AND_CAMPAIGN.md`; `ratchet_contract/bridge_validation/results/{rival_agreement,mutation_arbiter_test,stress_rival_agreement}.json`; `ratchet_contract/ratchetings/extension_fibre_capacity.py` + result; `ratchet_contract/ratchetings/results/cut_dependent_entropy_nvidia_referee.json`; `system_v5/julia_carrier/nonchiral_carrier_f01n01_negative_control.jl` + result JSON; `system_v6/receipts/workedout_possibilities_mining_20260609.md`; `git log` (this branch, `session/r0-three-engine-probes`) and `git show df89108aa`, `eba31410f`; memory files `project_qit_engines_p_vs_np_direction.md`, `project_ratchet_v0_2_landing_20260710.md`, `project_tower_assembly_campaign_20260704.md`, `project_constraint_manifold_derivation_result.md` (all flagged stale by the memory harness itself, ages noted inline).

### Absent / unverified (index)

- Literal "checkerboard carrier calibration" as a named artifact — not found under that exact name; closest match is `system_v4/probes/sim_checkerboard_admissibility.py` (older lane) plus ring-checkerboard shell topology as a VARIABLE in `MODEL_DOSSIER/00_DURABLE_STATE_20260721.md` line 46.
- Literal "PySINDy-residual lane" — not found; PySINDy is INTEGRATED/load_bearing already (`TOOL_LEDGER.md:124`); the unbuilt fuel item is a pykoopman/PyDMD arbiter comparison, not a "residual" lane.
- Literal "QHN" token — ABSENT; the real artifact is `quantum_hopfield_memory_sim.py` (Hopfield-class, not named QHN).
- Slice D/E/F settlement-machinery plan file — no file found under this literal name; inferred only from `CLAIMGATE_POSTMORTEM_20260722.md`'s stated architecture.
- D2 nonassociativity-slot current status — memory-sourced only (11 days old at read time, harness-flagged stale); not re-verified against current `system_v7/constraint_core/ratchet` code this pass.
- Tower co-ratchet three-way fork resolution — memory-sourced only (18 days old, harness-flagged stale); no fresher on-disk resolution found.
- Lev claim-intake ABSENT-by-name inventory — commit-message-level (`eba31410f`) only; not re-verified against the current `~/lev-main` worktree this pass (that worktree is outside this repo's tree).
- 64->16 "experiment not run" as literally phrased — ambiguous; found two distinct on-disk readings (system_v4/v6-era open equivalence warning vs system_v8 measured/audited operating-candidate-count), neither is a simple "not run" fact; held as open ambiguity in section (c)#9 and (d).
- 2SAT/3SAT/XOR-SAT complexity-terrain battery for the P-vs-NP direction — ABSENT as executable code; only the memory-recorded specification exists (`project_qit_engines_p_vs_np_direction.md`); the legacy `p_vs_np_sim.py` is a different, unrelated toy framing.

---

## Questions for auditors

These are aimed at the weakest points in this report. Each names a specific
claim, the section it lives in, and what a successful attack would look
like.

1. **Atlas vs. no-canonical-list.** Section 1(b) presents the 20-rung atlas
   table as the operative ladder while section 1's own source note quotes
   `MODEL_DOSSIER` saying "no single canonical owner layer list exists."
   Is this genuinely a live, non-collapsible tension, or is the atlas simply
   the wrong document to be citing at all — and if so, what should replace
   it as the ladder of record?

2. **The three kernel harness figures.** Section 4.3 lists "146/0/0"
   (unverifiable external provenance), "152/0/0" (stamped, not rerun this
   session), and "109/4/33" (legacy, honestly red). Does any external
   auditor have access to the "source archive owner environment" that
   produced 146/0/0, or should that figure be struck from every future
   report until it is reproduced somewhere?

3. **The z3/cvc5 tautology history.** Commit `b12c0e8c7` found every
   z3/cvc5 leg across the arrow set was the same generic tautology
   mislabeled `load_bearing`, fixed in `4fcd539d6`/`d2cdc4cbf` — except
   `magma_smt_genuine.py`, named the one mechanism-tied exception. Has
   anyone independently re-derived, arrow by arrow, that no other SMT leg
   still smuggles a tautology under a different guise? Section 2.4 flags
   this exact risk (cvc5's own manifest disclaiming "NOT a mechanism
   encoding") but no arrow-by-arrow re-audit is cited.

4. **The three named ClaimGate GAP holes.** Section 3's hostile-corpus
   table shows `duplicate_json_key`, `nan_values`, and `renamed_metric`
   still reaching a passing exit code through the live gate chain, with
   fix sketches routed but not applied. If any of these three receipt
   payloads were submitted today through `post_receipt_gate.sh`, would the
   commit actually be blocked — or does this report's own "passes local
   rerun" language on the *rest* of ClaimGate overstate how gated the
   estate currently is?

5. **Trust-root writability.** Section 3 states `gate_registry.json`, the
   sealed decks, and the fixture corpus all live on a path the producing
   agent can write to. Given that, what independent guarantee — if any —
   prevents an agent from editing the trust root itself in the same commit
   that edits a receipt, and does any check in this report actually rule
   that out, or only detect it after the fact via hash comparison?

6. **CI-green scope.** Section 2.7 and this report's repo-state block cite
   a GitHub Actions run (`29969379442`) with `conclusion: success` on
   commit `dcf4a5003`. That workflow runs `SEAL_METADATA_ONLY=1` — it
   checks numpy-absence and engine-value agreement, not a fresh JAX
   re-derivation. Does "CI green" in the commit history and in this report
   mean anything stronger than "metadata is well-formed and two numbers
   match to 1e-6," and if so, where is that stronger check evidenced?

7. **cut_dependent_entropy's scope limit.** Section 4.5 and section 7(a)
   both note that the NVIDIA referee panel's unanimous SURVIVES verdict
   coexists with two independent models flagging the same gap: the claim
   is established only for the pure two-qubit family. Given how much
   downstream language ("entanglement central," "correlation entropy born
   at the cut") leans on this one arrow, is a two-qubit-only demonstration
   sufficient grounds for that framing, or does the framing outrun the
   evidence?

8. **64→16, which reading.** Section 7(c)#9 holds two readings open: an
   old unresolved 8-way-construction ambiguity (system_v4/v6) and a newer
   audited "32 of 64 provably inert" result (system_v8) that is explicitly
   a construction identity of a fixed grid, not evidence the tournament
   could have gone differently. Is "provably inert" doing any real work
   here, or is it a tautology dressed as a finding — and does anyone know
   whether the older ambiguity was ever actually addressed by the newer
   work, given the newer work never cites the older warning?

9. **The P-vs-NP direction.** Section 7(c)#10 records an owner hypothesis
   that the QIT engines "get at P vs NP fundamentally," anchored on
   `a=a iff a~b` as Myhill–Nerode, with no executable battery built yet.
   Given the named barriers (relativization, natural proofs, BBBV
   optimality, the XOR-SAT geometry-vs-hardness trap), is there any
   version of this direction that survives first contact with a real
   2-SAT/3-SAT/XOR-SAT terrain sweep, or is the anchor observation (the
   axiom already being a proof technique) doing less work than the
   framing implies once barriers are taken seriously?

10. **What changes if everything here is true.** Every arrow in section 4.5
    and 7(a), and the entire manifold ladder in section 1, is FUEL-proposal
    or explicitly `promotion_allowed: false`, and the deterministic v0.6
    manifold audit reports zero scientific manifold layers admitted. If an
    auditor accepted every citation in this document at face value, what —
    concretely — would that license them to believe about the owner's
    underlying physics program that they could not already believe from
    `ROOT_CARD.md` alone? Is the estate's sheer volume of FUEL evidence
    doing any actual evidential work, or is it activity that has not yet
    moved the admission needle?
