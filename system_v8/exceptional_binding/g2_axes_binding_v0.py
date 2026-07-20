#!/usr/bin/env python3
"""G2-axes binding v0 — turns the owner's numerology hypothesis into a test.

OWNER HYPOTHESIS (2026-07-20, owner's own epistemic label: "the numbers just
match and that is about it"): the 7 axes (0-6) of the manifold's per-stage
fingerprint may be bound to G2 -- 7 axes <-> the 7-dim fundamental
representation of G2 (= the imaginary octonions Im(O)); field axes 7-12
<-> F4 at the Choi level (OUT OF SCOPE for v0, follow-up only).

PREREGISTERED TEST DESIGN (fixed before results were read):

(1) Build the 14 G2 derivation generators acting on Im(O) (7-dim), NOT by
    citing a dimension from a JSON (the vendored
    system_v8/inputs/pack_artifacts/exceptional_stack_geometry_pack186.py
    reuses the octonion Cayley-Dickson multiplication (cd_multiply) but does
    NOT itself contain explicit 14 generator matrices -- it cites
    g2_dim == 14 from a separate result JSON. So this sim reuses pack186's
    cd_multiply machinery for the octonion product, and DERIVES the 14
    generators itself as the null space of the Leibniz-rule constraint
    D(xy) = D(x)y + x D(y) over the full octonion basis -- i.e. Der(O),
    computed from octonion structure constants, not asserted.

(2) The manifold's 7-axis feature vectors: NOT a newly invented embedding.
    The L07 layer of system_v8/unified/results/manifold_unified_v2/receipt.json
    already stores, for each of 16 stage channels
    (family_{0..3}|{L,R}|f{+1,-1}), a genuine 7-component "vector" field
    (axis0_drive_polarity_signed_volume .. axis6_precedence_gap) computed on
    a fixed asymmetric probe state. This sim uses those 16x7 vectors AS-IS.
    No Bloch-drift/entropy-stroke/chirality/order-sensitivity descriptor is
    hand-built for this v0 -- the manifold already emits a 7-dim descriptor
    per stage, and using it directly is more honest than re-deriving a proxy.
    This substitution (using the pre-existing axis-vector rather than a
    custom Bloch-drift descriptor named in the task) is declared here as an
    INSTALLED design choice, not something forced by any prior layer.

(3) Test: measure whether the 14 G2 generators organize the manifold's own
    partitions of the 16 stages, via an "orbit-alignment" score (defined
    below), for three partitions read directly off the stage data:
      - P_terrain8:  (family, sheet) pair -> 8 classes  ("8-terrain partition";
        family in {0,1,2,3} x sheet in {L,R} literally matches the 8 terrain
        Choi objects referenced elsewhere in system_v8/upper_manifold/axis8_field_v0.py)
      - P_chirality: sheet label (L vs R)  ("L/R chirality split")
      - P_supdown:   sign(axis1_dissipative_entropy_delta_bits) per stage
        ("S-up/S-down split" -- read directly off the fingerprint's own
        entropy-stroke coordinate, not invented)

    ORBIT-ALIGNMENT SCORE (per algebra, per partition) -- REVISED after a
    preregistered-but-degenerate first design (kept honest in the receipt's
    "design_history" field): the first design used the FULL 14-generator
    joint tangent span T_i = span{g_k @ v_i} and a projection residual. That
    was found, on the first run, to be structurally non-discriminating: 14
    generic skew-symmetric generators applied to any fixed 7-vector v_i
    generically saturate the *entire* available tangent space at v_i (the
    6-dim hyperplane orthogonal to v_i, since g^T=-g forces v_i . (g_k v_i)
    = 0), REGARDLESS of which 14-dim generator set was used -- so control
    and G2 produced numerically identical scores (control std ~1e-17). This
    is reported as a finding, not hidden.

    The score actually used is a SINGLE-GENERATOR directional-alignment
    score, which is not subject to that saturation degeneracy: for a pair
    (i,j), i != j, with displacement d_ij = v_j - v_i,
        a_ij = max_k | cos_angle( d_ij, g_k @ v_i ) |
    (best alignment of the displacement with any ONE generator's action at
    v_i, over k=1..14). The partition-preservation score for partition P is
        score(P) = mean(a_ij : i,j same-class) - mean(a_ij : i,j cross-class)
    Positive score = same-class displacements are better explained by SOME
    individual generator direction than cross-class displacements. Unlike
    the full-span residual, this depends on which specific 14 directions
    are chosen (not just their joint span), so it is a real, non-degenerate
    test of whether G2's particular generators privilege the manifold's own
    partitions over generic alternatives. The reported G2 score is the mean
    of score(P) over the three partitions.

(4) CONTROLS:
    (a) 20 random 14-generator antisymmetric sets in so(7) (random skew-
        symmetric 7x7 matrices, Gram-Schmidt orthonormalized among
        themselves as elements of the 21-dim space of skew matrices -- NOT
        asserted closed Lie subalgebras, per the task's explicit fallback
        "(or random antisymmetric generator sets)"). The G2 score must
        exceed this control distribution; percentile is reported honestly
        either way.
    (b) Scrambled-descriptor control: a single fixed random permutation of
        the 7 axis components, applied to all 16 vectors before rerunning
        the exact G2 pipeline. If the G2 generators are organizing real
        axis-identity structure (not just raw point geometry), the score
        should collapse toward the random-control range once axis identity
        is scrambled.

(5) F4 / Choi-level axes 7-12 are explicitly OUT OF SCOPE for v0.

HONEST OUTCOME RULE (preregistered): if the G2 score falls inside the
random-control distribution (<95th percentile), verdict =
NUMEROLOGY_NOT_REJECTED_AS_SUCH. If it exceeds the 95th percentile,
verdict = G2_ORGANIZES_AXES_CANDIDATE. Either way promotion_allowed=false;
this is a tool_lego_fit_probe-class result, not a canonical admission.

Interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
Substrate: torch float64 (CPU). No network, no deletes, no commits.
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import torch

torch.set_default_dtype(torch.float64)

ROOT = Path(__file__).resolve().parents[2]
RECEIPT_PATH = ROOT / "system_v8/unified/results/manifold_unified_v2/receipt.json"
OUT_DIR = Path(__file__).resolve().parent / "results"
SEED = 20260720

# ---------------------------------------------------------------------------
# Octonion algebra (Cayley-Dickson doubling), reused in spirit from
# exceptional_stack_geometry_pack186.py's cd_multiply -- reimplemented here
# on torch tensors so the whole pipeline runs on one substrate.
# ---------------------------------------------------------------------------


def cd_conjugate(v: torch.Tensor) -> torch.Tensor:
    out = -v.clone()
    out[0] = v[0]
    return out


def cd_multiply(a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
    n = a.shape[0]
    if n == 1:
        return a * b
    half = n // 2
    a1, a2 = a[:half], a[half:]
    b1, b2 = b[:half], b[half:]
    top = cd_multiply(a1, b1) - cd_multiply(cd_conjugate(b2), a2)
    bot = cd_multiply(b2, a1) + cd_multiply(a2, cd_conjugate(b1))
    return torch.cat([top, bot])


def octonion_basis(i: int) -> torch.Tensor:
    out = torch.zeros(8)
    out[i] = 1.0
    return out


def octonion_structure_constants() -> torch.Tensor:
    """C[i,j,k] such that e_i * e_j = sum_k C[i,j,k] e_k, exact from cd_multiply."""
    basis = [octonion_basis(i) for i in range(8)]
    C = torch.zeros(8, 8, 8)
    for i in range(8):
        for j in range(8):
            C[i, j, :] = cd_multiply(basis[i], basis[j])
    return C


# ---------------------------------------------------------------------------
# Der(O): solve the Leibniz-rule linear system for derivations of O, i.e.
# the honest from-structure-constants construction of the G2 Lie algebra,
# rather than citing dim(Der(O))=14 from a JSON.
# ---------------------------------------------------------------------------


def solve_der_O(C: torch.Tensor) -> dict[str, Any]:
    """Solve for 8x8 matrices D with D(e_i * e_j) = D(e_i) e_j + e_i D(e_j)
    for every basis pair (i,j). Unknowns: D is 8x8 (64 unknowns), flattened
    row-major as D[a,b] -> index a*8+b. Each (i,j,k) triple with C[i,j,k]!=0
    contributes one linear row (built exactly via the structure constants),
    but easiest is to build the constraint for every (i,j) as an 8-vector
    equation and stack all 8*8 of them (many redundant/dependent -- that's
    fine, SVD null space handles it).
    """
    n = 8
    rows = []
    for i in range(n):
        ei = octonion_basis(i)
        for j in range(n):
            ej = octonion_basis(j)
            eij = cd_multiply(ei, ej)  # e_i * e_j, an 8-vector in basis coords
            # Constraint (as a function of unknown D, flattened a*8+b):
            #   sum_c eij[c] * D[c,:]   -  sum_b ej[b] * D[i,b]  applied...
            # Build directly: D(e_i*e_j) = sum_c eij[c] D_row(c) where D_row(c)
            # is the c-th row of D (since D acts linearly: D(sum c_m e_m) =
            # sum c_m D(e_m) = sum c_m D[:,m] if D stored as D applied to
            # basis vectors column-wise). Store D as D[:, m] = D(e_m), i.e.
            # unknown matrix M with columns M[:,m] = D(e_m), flatten as
            # index r*8+m for entry M[r,m].
            #
            # LHS: D(e_i*e_j) = sum_c eij[c] * D(e_c) = sum_c eij[c] M[:,c]
            #   -> row r: sum_c eij[c] * M[r,c]
            # RHS: D(e_i)*e_j + e_i*D(e_j)
            #   D(e_i) = M[:,i] (a vector); (M[:,i]) * e_j is left-mult by
            #   the octonion vector M[:,i] against fixed e_j -> a linear
            #   map of M[:,i], i.e. R_{e_j} applied to column i of M.
            #   Similarly e_i*D(e_j) = L_{e_i} applied to column j of M.
            for r in range(n):
                row_coef = torch.zeros(n, n)  # coefficient on M[a,b]
                # LHS contributes to M[r, c] with weight eij[c]
                row_coef[r, :] += eij
                # RHS term1: D(e_i)*e_j, component r of (v * e_j) where
                # v = M[:,i]. (v*e_j)_r = sum_a v[a] * (e_a*e_j)[r]
                #           = sum_a M[a,i] * C[a,j,r]
                row_coef[:, i] -= C[:, j, r]
                # RHS term2: e_i*D(e_j), component r of (e_i * w), w=M[:,j]
                #           = sum_b w[b] * (e_i*e_b)[r] = sum_b M[b,j]*C[i,b,r]
                row_coef[:, j] -= C[i, :, r]
                rows.append(row_coef.reshape(-1))
    A = torch.stack(rows)  # (n*n*n, n*n)
    U, S, Vh = torch.linalg.svd(A, full_matrices=True)
    tol = 1e-8 * S.max()
    null_mask = S < tol
    n_free = A.shape[1] - S.shape[0] + int(null_mask.sum())
    # Vh has shape (n*n, n*n); null space vectors are the last rows of Vh
    # whose singular value (if within range) is below tol, plus any beyond
    # the singular-value count (exact zero rows from a wide/short A).
    rank = int((S >= tol).sum())
    null_dim = A.shape[1] - rank
    null_basis = Vh[rank:, :]  # (null_dim, 64)
    generators = null_basis.reshape(null_dim, n, n)
    return {
        "structure_constants_checked": True,
        "linear_system_rows": int(A.shape[0]),
        "linear_system_unknowns": int(A.shape[1]),
        "rank": rank,
        "null_dim": null_dim,
        "generators_8x8": generators,
        "singular_values_near_null": [float(x) for x in S[max(0, rank - 3):rank + 3]],
    }


def restrict_to_imaginary(generators_8x8: torch.Tensor) -> torch.Tensor:
    """Der(O) generators fix e_0=1 automatically (Leibniz forces D(1)=0);
    verify that and restrict each generator to its 7x7 action on Im(O)
    = span(e_1..e_7)."""
    fixes_identity = torch.allclose(generators_8x8[:, :, 0], torch.zeros(generators_8x8.shape[0], 8), atol=1e-6)
    maps_im_to_im = torch.allclose(generators_8x8[:, 0, :], torch.zeros(generators_8x8.shape[0], 8), atol=1e-6)
    g7 = generators_8x8[:, 1:, 1:]
    return g7, fixes_identity, maps_im_to_im


def orthonormalize_generators(gens: torch.Tensor) -> torch.Tensor:
    """Gram-Schmidt (via QR on flattened generators) to get a well-
    conditioned spanning set of the same subspace, dimension preserved."""
    k = gens.shape[0]
    flat = gens.reshape(k, -1)
    Q, R = torch.linalg.qr(flat.T)  # Q: (dim, k) if k <= dim else truncated
    k_eff = min(k, Q.shape[1])
    ortho = Q[:, :k_eff].T.reshape(k_eff, gens.shape[1], gens.shape[2])
    return ortho


def skew_symmetrize_check(gens7: torch.Tensor) -> dict[str, Any]:
    diffs = [float(torch.max(torch.abs(g + g.T))) for g in gens7]
    return {"max_symmetric_part_over_generators": max(diffs), "all_skew_within_1e-6": max(diffs) < 1e-6}


# ---------------------------------------------------------------------------
# Manifold 7-axis descriptors (real data, not invented) + partitions.
# ---------------------------------------------------------------------------


def load_manifold_descriptors() -> dict[str, Any]:
    receipt = json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))
    l07 = receipt["layer_computations"]["L07"]
    stages = l07["fingerprints"]
    labels = [s["stage"] for s in stages]
    vectors = torch.tensor([s["vector"] for s in stages])
    families, sheets, fsigns = [], [], []
    for lab in labels:
        fam_part, sheet_part, f_part = lab.split("|")
        families.append(int(fam_part.split("_")[1]))
        sheets.append(sheet_part)
        fsigns.append(1 if "+1" in f_part else -1)
    axis1_signs = [1 if v[1].item() >= 0 else -1 for v in vectors]
    return {
        "labels": labels,
        "vectors": vectors,
        "families": families,
        "sheets": sheets,
        "fsigns": fsigns,
        "axis1_signs": axis1_signs,
        "coordinate_count": l07["coordinate_count"],
        "stage_count": l07["stage_count"],
        "fixed_probe": l07["fixed_probe"],
    }


def build_partitions(desc: dict[str, Any]) -> dict[str, list[int]]:
    n = len(desc["labels"])
    terrain8 = [f"{fam}|{sh}" for fam, sh in zip(desc["families"], desc["sheets"])]
    chirality = desc["sheets"]
    supdown = ["up" if s > 0 else "down" for s in desc["axis1_signs"]]

    def to_class_ids(labels_list: list[str]) -> list[int]:
        uniq = sorted(set(labels_list))
        idx = {u: k for k, u in enumerate(uniq)}
        return [idx[label] for label in labels_list]

    return {
        "P_terrain8": to_class_ids(terrain8),
        "P_chirality": to_class_ids(chirality),
        "P_supdown": to_class_ids(supdown),
    }


# ---------------------------------------------------------------------------
# Orbit-alignment score.
# ---------------------------------------------------------------------------


def generator_action_directions(gens: torch.Tensor, vectors: torch.Tensor) -> torch.Tensor:
    """For each point v_i, return the (k, 7) matrix of g_k @ v_i (the
    action of each of the k generators at that point)."""
    return torch.stack([torch.stack([g @ v for g in gens]) for v in vectors])  # (n, k, 7)


def orbit_alignment_score(gens: torch.Tensor, vectors: torch.Tensor, partition: list[int]) -> dict[str, Any]:
    n = vectors.shape[0]
    actions = generator_action_directions(gens, vectors)  # (n, k, 7)
    action_norms = torch.linalg.norm(actions, dim=2)  # (n, k)
    same_align, cross_align = [], []
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = vectors[j] - vectors[i]
            norm_d = float(torch.linalg.norm(d))
            if norm_d < 1e-14:
                continue
            dots = actions[i] @ d  # (k,)
            denom = action_norms[i] * norm_d
            valid = denom > 1e-14
            if not bool(valid.any()):
                continue
            cos_vals = torch.zeros_like(dots)
            cos_vals[valid] = dots[valid] / denom[valid]
            best_alignment = float(torch.max(torch.abs(cos_vals)))
            if partition[i] == partition[j]:
                same_align.append(best_alignment)
            else:
                cross_align.append(best_alignment)
    mean_same = sum(same_align) / len(same_align) if same_align else float("nan")
    mean_cross = sum(cross_align) / len(cross_align) if cross_align else float("nan")
    return {
        "mean_alignment_same_class": mean_same,
        "mean_alignment_cross_class": mean_cross,
        "score": mean_same - mean_cross,
        "n_same_pairs": len(same_align),
        "n_cross_pairs": len(cross_align),
    }


def aggregate_score(gens: torch.Tensor, vectors: torch.Tensor, partitions: dict[str, list[int]]) -> dict[str, Any]:
    per_partition = {name: orbit_alignment_score(gens, vectors, part) for name, part in partitions.items()}
    mean_score = sum(p["score"] for p in per_partition.values()) / len(per_partition)
    return {"per_partition": per_partition, "mean_score": mean_score}


# ---------------------------------------------------------------------------
# Controls.
# ---------------------------------------------------------------------------


def random_antisymmetric_generator_set(gen: torch.Generator, k: int = 14, dim: int = 7) -> torch.Tensor:
    """k random 7x7 skew-symmetric matrices, Gram-Schmidt orthonormalized
    against each other (as points in the dim*(dim-1)/2 - dim'l space of
    skew matrices) so they are k linearly independent generators, matching
    the same "orthonormalize a 14-generator set" treatment given to the
    genuine G2 generators, for a fair comparison."""
    skew_list = []
    for _ in range(k):
        M = torch.randn(dim, dim, generator=gen)
        skew_list.append(M - M.T)
    flat = torch.stack(skew_list).reshape(k, -1)
    Q, R = torch.linalg.qr(flat.T)
    k_eff = min(k, Q.shape[1])
    ortho = Q[:, :k_eff].T.reshape(k_eff, dim, dim)
    # re-antisymmetrize after orthonormalization (QR on flattened skew
    # matrices can pick up a tiny symmetric residual at float precision)
    ortho = 0.5 * (ortho - ortho.transpose(1, 2))
    return ortho


def run_controls(vectors: torch.Tensor, partitions: dict[str, list[int]], n_controls: int = 20) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(SEED)
    control_scores = []
    for trial in range(n_controls):
        gens = random_antisymmetric_generator_set(gen)
        agg = aggregate_score(gens, vectors, partitions)
        control_scores.append(agg["mean_score"])
    return {"n_controls": n_controls, "scores": control_scores}


def percentile_of(value: float, distribution: list[float]) -> float:
    below = sum(1 for x in distribution if x < value)
    return 100.0 * below / len(distribution)


def scrambled_descriptor_control(gens: torch.Tensor, vectors: torch.Tensor, partitions: dict[str, list[int]], perm_seed: int = SEED + 1) -> dict[str, Any]:
    gen = torch.Generator().manual_seed(perm_seed)
    perm = torch.randperm(vectors.shape[1], generator=gen)
    scrambled = vectors[:, perm]
    agg = aggregate_score(gens, scrambled, partitions)
    return {"permutation": perm.tolist(), "result": agg}


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------


def main() -> int:
    checks: dict[str, Any] = {}
    findings: list[str] = []

    C = octonion_structure_constants()
    der = solve_der_O(C)
    checks["der_O_dimension_is_14"] = der["null_dim"] == 14
    findings.append(
        f"Der(O) solved from Leibniz-rule linear system on octonion structure "
        f"constants: rank={der['rank']}, null_dim={der['null_dim']} "
        f"(expected 14 for Der(O)=g2)."
    )

    gens8 = der["generators_8x8"]
    gens7, fixes_identity, maps_im_to_im = restrict_to_imaginary(gens8)
    checks["generators_fix_identity"] = bool(fixes_identity)
    checks["generators_preserve_imaginary_octonions"] = bool(maps_im_to_im)

    gens7_ortho = orthonormalize_generators(gens7)
    checks["orthonormalized_generator_count_is_14"] = gens7_ortho.shape[0] == 14
    skew_check = skew_symmetrize_check(gens7_ortho)
    checks["g2_generators_are_skew_in_so7"] = skew_check["all_skew_within_1e-6"]

    desc = load_manifold_descriptors()
    checks["loaded_16_stages"] = len(desc["labels"]) == 16
    checks["loaded_7_axis_coordinates"] = desc["coordinate_count"] == 7

    partitions = build_partitions(desc)
    checks["terrain8_has_8_classes"] = len(set(partitions["P_terrain8"])) == 8
    checks["chirality_has_2_classes"] = len(set(partitions["P_chirality"])) == 2
    checks["supdown_has_2_classes"] = len(set(partitions["P_supdown"])) == 2

    g2_result = aggregate_score(gens7_ortho, desc["vectors"], partitions)

    controls = run_controls(desc["vectors"], partitions, n_controls=20)
    percentile = percentile_of(g2_result["mean_score"], controls["scores"])
    checks["g2_score_computed"] = True
    checks["control_distribution_built_n20"] = len(controls["scores"]) == 20

    scrambled = scrambled_descriptor_control(gens7_ortho, desc["vectors"], partitions)
    scrambled_percentile = percentile_of(scrambled["result"]["mean_score"], controls["scores"])
    checks["scrambled_control_computed"] = True
    # NOTE: whether the scrambled score is lower than the G2 score is an
    # EMPIRICAL RESULT of the probe, not a mechanical validity check on the
    # sim itself -- it must not gate all_pass. It is reported separately
    # under scrambled_descriptor_control / findings below.
    scrambled_collapses_toward_control = bool(
        scrambled["result"]["mean_score"] < g2_result["mean_score"]
    )

    above_95th = percentile >= 95.0
    if above_95th:
        verdict = "G2_ORGANIZES_AXES_CANDIDATE"
    else:
        verdict = "NUMEROLOGY_NOT_REJECTED_AS_SUCH"

    import statistics
    control_mean = statistics.mean(controls["scores"])
    control_std = statistics.pstdev(controls["scores"])

    result: dict[str, Any] = {
        "schema": "ratchet.g2_axes_binding.v0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "design_history": [
            "First design (full 14-generator joint tangent-span projection "
            "residual) was run and found degenerate: control_std ~= "
            "2.2e-17 and control_mean numerically equal to the G2 score "
            "(both -0.0501712840579715...), because 14 generic "
            "skew-symmetric generators applied to any fixed 7-vector "
            "generically saturate the full 6-dim tangent hyperplane "
            "orthogonal to that vector, independent of which 14-dim "
            "generator set is used. That design could not have "
            "distinguished G2 from random by construction, so it was "
            "replaced (same run, before any interpretation of the "
            "degenerate numbers as a G2 result) with the single-generator "
            "directional-alignment score described in the module "
            "docstring and used for the numbers reported below.",
        ],
        "owner_hypothesis": (
            "7 manifold axes (0-6) <-> 7-dim fundamental rep of G2 (Im(O)); "
            "field axes 7-12 <-> F4 at Choi level (out of scope v0). "
            "Owner's own epistemic label: 'the numbers just match and that is "
            "about it'."
        ),
        "installed_choices": [
            "Der(O) built by solving the Leibniz linear system on octonion "
            "structure constants derived from a standard Cayley-Dickson "
            "octonion multiplication table (basis-dependent presentation; "
            "Der(O)=g2 up to isomorphism is basis-independent).",
            "Manifold 7-axis descriptor is the L07 layer's own 'vector' field "
            "(axis0..axis6) taken as-is per stage; no additional Bloch-drift/"
            "chirality/order-sensitivity descriptor invented for v0.",
            "P_terrain8 = (family, sheet) tuple partition of the 16 stages, "
            "8 classes.",
            "P_chirality = sheet label (L vs R).",
            "P_supdown = sign(axis1_dissipative_entropy_delta_bits) per "
            "stage, read directly off the fingerprint's own entropy-stroke "
            "coordinate.",
            "Orbit-alignment score defined per docstring section (3) above; "
            "aggregate = mean over the 3 partitions.",
            "Random controls: 20 random 14-generator antisymmetric sets in "
            "so(7), NOT asserted to be closed Lie subalgebras (per the "
            "task's own fallback wording).",
        ],
        "der_O": {
            "linear_system_rows": der["linear_system_rows"],
            "linear_system_unknowns": der["linear_system_unknowns"],
            "rank": der["rank"],
            "null_dim": der["null_dim"],
            "singular_values_near_null": der["singular_values_near_null"],
            "fixes_identity": bool(fixes_identity),
            "maps_imaginary_to_imaginary": bool(maps_im_to_im),
            "skew_symmetric_in_so7": skew_check,
        },
        "manifold_descriptors": {
            "fixed_probe": desc["fixed_probe"],
            "stage_count": desc["stage_count"],
            "coordinate_count": desc["coordinate_count"],
            "labels": desc["labels"],
        },
        "partitions": {
            "P_terrain8": partitions["P_terrain8"],
            "P_chirality": partitions["P_chirality"],
            "P_supdown": partitions["P_supdown"],
        },
        "g2_score": g2_result,
        "control_distribution": {
            "n_controls": controls["n_controls"],
            "scores": controls["scores"],
            "mean": control_mean,
            "std": control_std,
            "min": min(controls["scores"]),
            "max": max(controls["scores"]),
        },
        "g2_percentile_vs_controls": percentile,
        "scrambled_descriptor_control": {
            "mean_score": scrambled["result"]["mean_score"],
            "percentile_vs_same_controls": scrambled_percentile,
            "scrambled_score_below_g2_score": scrambled_collapses_toward_control,
        },
        "verdict": verdict,
        "verdict_rule": (
            "G2_ORGANIZES_AXES_CANDIDATE iff g2_percentile_vs_controls >= 95.0; "
            "else NUMEROLOGY_NOT_REJECTED_AS_SUCH. Preregistered before this "
            "run's numbers were read."
        ),
        "findings": findings,
        "checks": checks,
        "all_pass": all(checks.values()),
        "f4_scope_note": "F4 / Choi-level axes 7-12 explicitly OUT OF SCOPE for v0; follow-up only.",
        "caveats": [
            "The G2 generators are basis-dependent as matrices (Der(O) is "
            "only defined up to conjugation); the orbit-alignment score is "
            "therefore ALSO basis-dependent unless the manifold's axis "
            "ordering is independently known to align with the octonion "
            "basis ordering used here. This sim does NOT establish that "
            "alignment -- it tests it, and the scrambled-descriptor control "
            "is the direct probe of exactly this assumption.",
            "Orthonormalizing the 14 Der(O) generators via QR changes their "
            "matrix representation (a different real linear combination) "
            "but not the 14-dim subspace/orbit structure they span; the "
            "orbit-alignment score depends only on the spanned tangent "
            "subspace T_i, not on the specific generator basis chosen, so "
            "this is safe.",
            "16 stages is a small sample (120 same/cross-class ordered "
            "pairs per partition at most); the control distribution (n=20) "
            "is likewise small. Percentile estimates from n=20 controls "
            "have coarse resolution (5-point steps); treat percentile as "
            "indicative, not a precise p-value.",
        ],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "g2_axes_binding_v0_receipt.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "verdict": verdict,
        "g2_mean_score": g2_result["mean_score"],
        "g2_percentile_vs_controls": percentile,
        "control_mean": control_mean,
        "control_std": control_std,
        "scrambled_mean_score": scrambled["result"]["mean_score"],
        "all_pass": result["all_pass"],
        "out_path": str(out_path),
    }, indent=2))
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
