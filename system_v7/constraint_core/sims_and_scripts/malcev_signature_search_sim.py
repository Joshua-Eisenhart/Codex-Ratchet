#!/usr/bin/env python3
"""malcev_signature_search_sim -- name and search the T01 ceiling.

UP-113 found the current engine ceiling: the natural engine brackets are Jacobi
brackets, so they do not demand the octonion fork. This sim turns the open
ceiling into an algebraic detector:

  lie              = Jacobi identity holds.
  malcev_not_lie   = Jacobi fails, but the Malcev identity holds.
  neither          = both fail.

Reference gates are rebuilt from scratch:
  * Im(H) commutator is su(2): Jacobi holds.
  * Im(O) commutator is the 7-dim simple Malcev algebra: Jacobi fails and
    Malcev holds.
  * a random antisymmetric bracket on R^7 fails both.
  * a corrupted Malcev identity sign breaks the Im(O) detector.

Then engine-native finite brackets are harvested from actual mechanics:
per-terrain GKSL generators, segment channels, stage-composition log
differences, operator-pair products at terrain casings, and cross-engine Choi
mirror combinations. Each harvested source span is tested directly as a
projected finite bracket, and its commutator closure is also tested when it
adds information. A malcev_not_lie engine hit would be serialized loudly.

scratch_diagnostic, promotion_allowed=false. Seeded rng(0). Standalone numpy.
"""

import json
import math
import sys
from collections import Counter

import numpy as np


SEED = 0
JACOBI_TOL = 1e-8
MALCEV_TOL = 1e-8
INDEPENDENCE_TOL = 1e-9

SX = np.array([[0, 1], [1, 0]], complex)
SY = np.array([[0, -1j], [1j, 0]], complex)
SZ = np.array([[1, 0], [0, -1]], complex)
I2 = np.eye(2, dtype=complex)
SP = 0.5 * (SX + 1j * SY)
SM = 0.5 * (SX - 1j * SY)
G = 0.35
KAP = 1.0

TERR = {
    0: (+1, "damp", +1),
    1: (+1, "depol", 0),
    2: (+1, "damp", -1),
    3: (+1, "proj", 0),
    4: (-1, "damp", -1),
    5: (-1, "depol", 0),
    6: (-1, "damp", +1),
    7: (-1, "proj", 0),
}


def real_vec(mat):
    arr = np.asarray(mat, dtype=complex).reshape(-1)
    return np.concatenate([arr.real, arr.imag])


def mat_from_real_vec(vec, shape):
    half = len(vec) // 2
    flat = np.asarray(vec[:half]) + 1j * np.asarray(vec[half:])
    return flat.reshape(shape)


def real_norm(mat):
    return float(np.linalg.norm(real_vec(mat)))


def independent_basis(mats, tol=INDEPENDENCE_TOL):
    basis = []
    labels = []
    qcols = []
    shape = None
    for idx, item in enumerate(mats):
        if isinstance(item, tuple):
            label, mat = item
        else:
            label, mat = f"seed_{idx}", item
        if shape is None:
            shape = np.asarray(mat).shape
        v = real_vec(mat)
        residual = v.copy()
        for q in qcols:
            residual -= q * float(np.dot(q, residual))
        nrm = float(np.linalg.norm(residual))
        if nrm > tol:
            q = residual / nrm
            qcols.append(q)
            basis.append(mat_from_real_vec(q, shape))
            labels.append(label)
    return basis, labels


def projection_data(basis):
    if not basis:
        raise ValueError("empty basis")
    return np.column_stack([real_vec(b) for b in basis])


def project_to_basis(mat, basis, basis_matrix=None):
    if basis_matrix is None:
        basis_matrix = projection_data(basis)
    target = real_vec(mat)
    coeff, *_ = np.linalg.lstsq(basis_matrix, target, rcond=None)
    residual = float(np.linalg.norm(basis_matrix @ coeff - target))
    return coeff, residual


def commutator(a, b):
    return a @ b - b @ a


def closure_under_commutator(seed_mats, max_dim=64, max_rounds=8):
    basis, labels = independent_basis(seed_mats)
    for _ in range(max_rounds):
        changed = False
        basis_matrix = projection_data(basis)
        current_n = len(basis)
        additions = []
        for i in range(current_n):
            for j in range(i + 1, current_n):
                mat = commutator(basis[i], basis[j])
                _, residual = project_to_basis(mat, basis, basis_matrix)
                if residual > 1e-8:
                    additions.append((f"closure_[{labels[i]},{labels[j]}]", mat))
        if not additions:
            break
        for label, mat in additions:
            trial = basis + [mat]
            new_basis, new_labels = independent_basis(list(zip(labels, basis)) + [(label, mat)])
            if len(new_basis) > len(basis):
                basis, labels = new_basis, new_labels
                changed = True
                if len(basis) >= max_dim:
                    return basis[:max_dim], labels[:max_dim], False
        if not changed:
            break
    basis_matrix = projection_data(basis)
    max_resid = 0.0
    for i in range(len(basis)):
        for j in range(i + 1, len(basis)):
            _, residual = project_to_basis(commutator(basis[i], basis[j]), basis, basis_matrix)
            max_resid = max(max_resid, residual)
    return basis, labels, bool(max_resid <= 1e-7)


def bracket_constants_from_matrices(basis):
    n = len(basis)
    basis_matrix = projection_data(basis)
    constants = np.zeros((n, n, n), dtype=float)
    max_resid = 0.0
    for i in range(n):
        for j in range(n):
            coeff, residual = project_to_basis(commutator(basis[i], basis[j]), basis, basis_matrix)
            constants[:, i, j] = coeff
            max_resid = max(max_resid, residual)
    return constants, max_resid


def bracket_from_constants(constants):
    def bracket(x, y):
        return np.einsum("kij,i,j->k", constants, x, y)

    return bracket


def normalize(v):
    nrm = float(np.linalg.norm(v))
    if nrm < 1e-15:
        return v
    return v / nrm


def jacobiator(bracket, x, y, z):
    return bracket(bracket(x, y), z) + bracket(bracket(y, z), x) + bracket(bracket(z, x), y)


def identity_defects(bracket, dim, rng, samples=128, corrupted_malcev=False):
    max_jacobi = 0.0
    max_malcev = 0.0
    witness = None
    for _ in range(samples):
        x, y, z = [normalize(rng.standard_normal(dim)) for _ in range(3)]
        jxyz = jacobiator(bracket, x, y, z)
        jnorm = float(np.linalg.norm(jxyz))
        lhs = jacobiator(bracket, x, y, bracket(x, z))
        rhs = bracket(jxyz, x)
        malcev_vec = lhs + rhs if corrupted_malcev else lhs - rhs
        mnorm = float(np.linalg.norm(malcev_vec))
        if jnorm > max_jacobi:
            witness = {
                "x": [float(v) for v in x],
                "y": [float(v) for v in y],
                "z": [float(v) for v in z],
                "jacobiator_norm": jnorm,
            }
        max_jacobi = max(max_jacobi, jnorm)
        max_malcev = max(max_malcev, mnorm)
    return max_jacobi, max_malcev, witness


def classify_bracket(bracket, dim, rng, samples=128, corrupted_malcev=False):
    jacobi_defect, malcev_defect, witness = identity_defects(
        bracket, dim, rng, samples=samples, corrupted_malcev=corrupted_malcev
    )
    if jacobi_defect <= JACOBI_TOL and not corrupted_malcev:
        cls = "lie"
    elif jacobi_defect > JACOBI_TOL and malcev_defect <= MALCEV_TOL:
        cls = "malcev_not_lie"
    else:
        cls = "neither"
    return {
        "classification": cls,
        "jacobi_defect_max": jacobi_defect,
        "malcev_defect_max": malcev_defect,
        "jacobi_witness": witness,
    }


def h_imag_bracket(x, y):
    return 2.0 * np.cross(x, y)


def octonion_table():
    mult = np.zeros((8, 8), int)
    sign = np.zeros((8, 8), int)
    for i in range(8):
        mult[0, i] = i
        mult[i, 0] = i
        sign[0, i] = 1
        sign[i, 0] = 1
    for i in range(1, 8):
        mult[i, i] = 0
        sign[i, i] = -1
    triples = [(1, 2, 3), (1, 4, 5), (1, 7, 6), (2, 4, 6), (2, 5, 7), (3, 4, 7), (3, 6, 5)]
    for a, b, c in triples:
        for x, y, z, s in [
            (a, b, c, 1),
            (b, c, a, 1),
            (c, a, b, 1),
            (b, a, c, -1),
            (a, c, b, -1),
            (c, b, a, -1),
        ]:
            mult[x, y] = z
            sign[x, y] = s
    return mult, sign


O_MULT, O_SIGN = octonion_table()


def octonion_mul(u, v):
    out = np.zeros(8)
    for i, a in enumerate(u):
        if abs(a) < 1e-15:
            continue
        for j, b in enumerate(v):
            if abs(b) < 1e-15:
                continue
            out[O_MULT[i, j]] += O_SIGN[i, j] * a * b
    return out


def o_imag_bracket(x, y):
    ux = np.zeros(8)
    uy = np.zeros(8)
    ux[1:] = x
    uy[1:] = y
    return (octonion_mul(ux, uy) - octonion_mul(uy, ux))[1:]


def random_antisymmetric_constants(dim, rng):
    constants = np.zeros((dim, dim, dim), dtype=float)
    for i in range(dim):
        for j in range(i + 1, dim):
            v = rng.standard_normal(dim) / math.sqrt(dim)
            constants[:, i, j] = v
            constants[:, j, i] = -v
    return constants


def dissipator(l_op, rho):
    return l_op @ rho @ l_op.conj().T - 0.5 * (l_op.conj().T @ l_op @ rho + rho @ l_op.conj().T @ l_op)


def terrain_ops(ti):
    eps, kind, pole = TERR[ti]
    h = eps * (SX + SY + SZ) / math.sqrt(3)
    jumps = []
    if kind == "damp":
        jumps.append(SP if pole > 0 else SM)
    elif kind == "depol":
        jumps.extend([SX / math.sqrt(2), SY / math.sqrt(2)])
    else:
        jumps.append(SZ)
    return h, jumps


def lindblad_generator(ti):
    h, jumps = terrain_ops(ti)

    def gen(rho):
        out = -1j * G * (h @ rho - rho @ h)
        for jump in jumps:
            out += KAP * dissipator(jump, rho)
        return out

    return gen


def linear_map_matrix(fn):
    mat = np.zeros((4, 4), dtype=complex)
    for a in range(2):
        for b in range(2):
            e = np.zeros((2, 2), dtype=complex)
            e[a, b] = 1
            mat[:, 2 * a + b] = fn(e).reshape(4)
    return mat


def channel_from_generator(gen, t=1.0, steps=120):
    def chan(rho):
        dt = t / steps
        cur = rho.astype(complex)
        for _ in range(steps):
            k1 = gen(cur)
            k2 = gen(cur + 0.5 * dt * k1)
            k3 = gen(cur + 0.5 * dt * k2)
            k4 = gen(cur + dt * k3)
            cur = cur + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        return cur

    return linear_map_matrix(chan)


def choi_from_channel(channel_matrix):
    choi = np.zeros((4, 4), dtype=complex)
    for i in range(2):
        for j in range(2):
            e = np.zeros((2, 2), dtype=complex)
            e[i, j] = 1
            image = (channel_matrix @ e.reshape(4)).reshape(2, 2)
            choi += np.kron(e, image)
    return choi


def matrix_log_if_defined(mat):
    try:
        vals, vecs = np.linalg.eig(mat)
        if np.min(np.abs(vals)) < 1e-10:
            return None, "singular_eigenvalue"
        cond = float(np.linalg.cond(vecs))
        if not np.isfinite(cond) or cond > 1e10:
            return None, "ill_conditioned_eigenvectors"
        log_mat = vecs @ np.diag(np.log(vals)) @ np.linalg.inv(vecs)
        recon = vecs @ np.diag(np.exp(np.log(vals))) @ np.linalg.inv(vecs)
        residual = float(np.linalg.norm(recon - mat))
        if residual > 1e-7:
            return None, f"reconstruction_residual_{residual:.2e}"
        return log_mat, "ok"
    except np.linalg.LinAlgError as exc:
        return None, f"lin_alg_error_{exc}"


def unique_labeled(mats, tol=1e-10):
    basis, labels = independent_basis(mats, tol=tol)
    return list(zip(labels, basis))


def harvest_engine_objects():
    generators = [(f"L_terrain_{ti}", linear_map_matrix(lindblad_generator(ti))) for ti in sorted(TERR)]
    channels = [(f"S_terrain_{ti}", channel_from_generator(lindblad_generator(ti))) for ti in sorted(TERR)]
    chois = [(f"J_terrain_{ti}", choi_from_channel(mat)) for ti, mat in [(int(label.rsplit("_", 1)[1]), m) for label, m in channels]]

    log_diffs = []
    log_skip_reasons = Counter()
    for a in range(len(channels)):
        for b in range(a + 1, len(channels)):
            la, sa = channels[a]
            lb, sb = channels[b]
            log_ab, status_ab = matrix_log_if_defined(sa @ sb)
            log_ba, status_ba = matrix_log_if_defined(sb @ sa)
            if log_ab is None or log_ba is None:
                log_skip_reasons[f"{status_ab}|{status_ba}"] += 1
                continue
            log_diffs.append((f"log({la}*{lb})-log({lb}*{la})", log_ab - log_ba))

    op_pair_products = []
    for ti in sorted(TERR):
        h, jumps = terrain_ops(ti)
        local = [(f"H_{ti}", h)]
        for idx, jump in enumerate(jumps):
            local.append((f"J_{ti}_{idx}", jump))
            local.append((f"Jdag_{ti}_{idx}", jump.conj().T))
        local.append((f"Z_{ti}", SZ))
        for i, (la, a) in enumerate(local):
            for j, (lb, b) in enumerate(local):
                if i != j:
                    op_pair_products.append((f"{la}*{lb}", a @ b))

    choi_mirror_commutators = []
    for i in range(len(chois)):
        for j in range(i + 1, len(chois)):
            li, ji = chois[i]
            lj, jj = chois[j]
            choi_mirror_commutators.append((f"[{li},{lj}]_mirror", commutator(ji, jj)))

    left_right_mirrors = []
    for ti in sorted(TERR):
        h, jumps = terrain_ops(ti)
        for label, op in [(f"H_{ti}", h)] + [(f"jump_{ti}_{k}", jump) for k, jump in enumerate(jumps)]:
            left_right_mirrors.append((f"Lmirror_{label}", np.kron(op, I2)))
            left_right_mirrors.append((f"Rmirror_{label}", np.kron(I2, op.T)))

    return {
        "gksl_generator_superoperators": unique_labeled(generators),
        "segment_channel_maps": unique_labeled(channels),
        "stage_composition_log_difference_maps": unique_labeled(log_diffs),
        "operator_pair_products_at_casings": unique_labeled(op_pair_products),
        "cross_engine_choi_mirror_commutators": unique_labeled(choi_mirror_commutators + left_right_mirrors),
    }, {"stage_log_difference_skips": dict(log_skip_reasons), "stage_log_difference_count": len(log_diffs)}


def matrix_preview(mat, max_entries=16):
    flat = np.asarray(mat).reshape(-1)
    preview = []
    for val in flat[:max_entries]:
        preview.append([float(np.real(val)), float(np.imag(val))])
    return preview


def test_matrix_bracket_candidate(name, labeled_mats, rng):
    if len(labeled_mats) < 2:
        return []
    source_basis, source_labels = independent_basis(labeled_mats)
    results = []

    constants, closure_resid = bracket_constants_from_matrices(source_basis)
    source_result = classify_bracket(bracket_from_constants(constants), len(source_basis), rng, samples=128)
    source_result.update(
        {
            "name": f"{name}__source_span_projection",
            "harvest_family": name,
            "construction": "matrix_commutator_projected_to_original_harvest_span",
            "seed_dim": len(labeled_mats),
            "basis_dim": len(source_basis),
            "closure_residual_max": closure_resid,
            "basis_labels": source_labels[:24],
        }
    )
    results.append(source_result)

    closure_basis, closure_labels, closed = closure_under_commutator(labeled_mats)
    constants, closure_resid = bracket_constants_from_matrices(closure_basis)
    closure_result = classify_bracket(bracket_from_constants(constants), len(closure_basis), rng, samples=128)
    closure_result.update(
        {
            "name": f"{name}__commutator_closure",
            "harvest_family": name,
            "construction": "finite_commutator_closure_of_harvested_matrices",
            "seed_dim": len(labeled_mats),
            "basis_dim": len(closure_basis),
            "closure_residual_max": closure_resid,
            "closure_completed": closed,
            "basis_labels": closure_labels[:24],
        }
    )
    results.append(closure_result)
    return results


def run_reference_gates(rng):
    im_h = classify_bracket(h_imag_bracket, 3, rng, samples=128)
    im_h.update({"name": "Im(H)_commutator", "expected": "lie", "algebra": "su(2)"})

    im_o = classify_bracket(o_imag_bracket, 7, rng, samples=128)
    im_o.update({"name": "Im(O)_commutator", "expected": "malcev_not_lie", "algebra": "simple_7d_malcev"})

    random_constants = random_antisymmetric_constants(7, rng)
    random_result = classify_bracket(bracket_from_constants(random_constants), 7, rng, samples=128)
    random_result.update({"name": "random_antisymmetric_R7", "expected": "neither"})

    corrupted = classify_bracket(o_imag_bracket, 7, rng, samples=128, corrupted_malcev=True)
    corrupted.update(
        {
            "name": "Im(O)_with_corrupted_malcev_sign",
            "expected": "neither",
            "corruption": "uses lhs + rhs instead of lhs - rhs in Malcev identity",
        }
    )

    gates_pass = bool(
        im_h["classification"] == "lie"
        and im_h["jacobi_defect_max"] <= JACOBI_TOL
        and im_o["classification"] == "malcev_not_lie"
        and im_o["jacobi_defect_max"] > 1e-6
        and im_o["malcev_defect_max"] <= MALCEV_TOL
        and random_result["classification"] == "neither"
        and corrupted["classification"] == "neither"
        and corrupted["malcev_defect_max"] > 1e-6
    )
    return [im_h, im_o, random_result, corrupted], gates_pass


def print_detector_gates(reference_results, gates_pass):
    print("MALCEV SIGNATURE DETECTOR GATES")
    print("  target signature: Jacobi fails + Malcev passes => malcev_not_lie")
    for item in reference_results:
        print(
            "  {name}: class={cls} expected={exp} jacobi={jac:.3e} malcev={mal:.3e}".format(
                name=item["name"],
                cls=item["classification"],
                exp=item["expected"],
                jac=item["jacobi_defect_max"],
                mal=item["malcev_defect_max"],
            )
        )
    print(f"  detector_gates_pass: {gates_pass}")
    print()


def print_harvest_table(harvest_results):
    print("ENGINE HARVEST CENSUS TABLE")
    print(
        "  {name:<58} {dim:>4} {cls:<15} {jac:>11} {mal:>11} {resid:>11}".format(
            name="candidate", dim="dim", cls="class", jac="jacobi", mal="malcev", resid="closure"
        )
    )
    for item in harvest_results:
        print(
            "  {name:<58} {dim:>4d} {cls:<15} {jac:>11.3e} {mal:>11.3e} {resid:>11.3e}".format(
                name=item["name"][:58],
                dim=item["basis_dim"],
                cls=item["classification"],
                jac=item["jacobi_defect_max"],
                mal=item["malcev_defect_max"],
                resid=item["closure_residual_max"],
            )
        )
    print()


def main():
    rng = np.random.default_rng(SEED)
    reference_results, detector_gates_pass = run_reference_gates(rng)
    print_detector_gates(reference_results, detector_gates_pass)

    harvests, harvest_meta = harvest_engine_objects()
    harvest_results = []
    for name, labeled_mats in harvests.items():
        harvest_results.extend(test_matrix_bracket_candidate(name, labeled_mats, rng))

    print_harvest_table(harvest_results)

    census = Counter(item["classification"] for item in harvest_results)
    malcev_hits = [item for item in harvest_results if item["classification"] == "malcev_not_lie"]
    malcev_hit_serializations = []
    for hit in malcev_hits:
        family = hit["harvest_family"]
        labeled_mats = harvests[family]
        basis, labels = independent_basis(labeled_mats)
        malcev_hit_serializations.append(
            {
                "name": hit["name"],
                "basis_labels": labels,
                "basis_preview_real_imag_flat_first_16": [matrix_preview(mat) for mat in basis],
                "note": "Full construction is deterministic from this script, the seed, and the named harvest family.",
            }
        )

    no_engine_malcev = len(malcev_hits) == 0
    verdict_pass = bool(detector_gates_pass and no_engine_malcev)
    print("SUMMARY")
    print(f"  harvest_census: {dict(census)}")
    print(f"  engine_native_malcev_not_lie_hits: {len(malcev_hits)}")
    print(f"  expected_UP_113_outcome_lie_or_neither_only: {no_engine_malcev}")
    if malcev_hits:
        print("  MAJOR_FINDING: engine-native malcev_not_lie signature found; serialized in result JSON")
    else:
        print("  no engine-native Malcev-not-Lie demand found; H ceiling remains named, not broken")

    out = {
        "sim_id": "malcev_signature_search_sim",
        "name": "Malcev signature search for the T01 ceiling",
        "version": "1.0",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "seed": SEED,
        "source_context": {
            "up_113_source": "system_v7/constraint_core/sims_and_scripts/t01_grouping_demand_search_sim.py",
            "claim_ceiling": "diagnostic search only; no admission or octonion-fork promotion",
        },
        "tool_manifest": {
            "numpy": "load-bearing linear algebra for reference brackets, engine channel matrices, projection, closure, and identity defects"
        },
        "TOOL_MANIFEST": {
            "numpy": "load-bearing linear algebra for reference brackets, engine channel matrices, projection, closure, and identity defects"
        },
        "tool_integration_depth": {"numpy": "load_bearing"},
        "TOOL_INTEGRATION_DEPTH": {"numpy": "load_bearing"},
        "reference_detector_gates_pass": detector_gates_pass,
        "reference_objects": reference_results,
        "harvest_meta": harvest_meta,
        "harvest_results": harvest_results,
        "harvest_census": dict(census),
        "engine_native_malcev_not_lie_hits": [hit["name"] for hit in malcev_hits],
        "malcev_hit_serializations": malcev_hit_serializations,
        "controls": {
            "im_o_reference_classifies_malcev_not_lie": reference_results[1]["classification"] == "malcev_not_lie",
            "im_h_reference_classifies_lie": reference_results[0]["classification"] == "lie",
            "random_bracket_classifies_neither": reference_results[2]["classification"] == "neither",
            "corrupted_malcev_identity_breaks_im_o": reference_results[3]["classification"] == "neither",
        },
        "expected_honest_outcome_per_UP_113": "engine harvested candidates classify as lie or neither; malcev_not_lie would be a major finding",
        "octonion_fork_demand_found": bool(malcev_hits),
        "H_ceiling_named_as": "Im(O) commutator is the 7-dimensional simple Malcev algebra; current engine mechanics did not demand it",
        "banned_modes_observed": False,
        "verdict": "PASS" if verdict_pass else "FAIL",
    }
    path = __file__.replace(".py", "_results.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=1)
    print(f"  VERDICT: {out['verdict']}")
    print(f"ALL_GATES: {out['verdict']} -> {path}")
    sys.exit(0 if verdict_pass else 1)


if __name__ == "__main__":
    main()
