import jax; jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import re
from itertools import permutations
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "rosetta_igt_qit_convergence_probe"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "rosetta_igt_qit_convergence_probe_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "rosetta_igt_qit_convergence_probe_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
QIT_DT = 0.01
QIT_STEPS = 512

VERTEX_LABELS = [
    ("win", "WIN"),
    ("win", "LOSE"),
    ("lose", "WIN"),
    ("lose", "LOSE"),
]
VERTEX_COORDS = [
    (1.0, 1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
    (-1.0, -1.0),
]
N_GENERIC = jnp.array([0.37, -0.51, 0.78], dtype=jnp.float64)
N_GENERIC = N_GENERIC / jnp.linalg.norm(N_GENERIC)
R0 = jnp.array([0.23, -0.31, 0.17], dtype=jnp.float64)


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def bool_scalar(value: bool) -> float:
    return 1.0 if value else 0.0


def vec_payload(v: Any) -> list[float]:
    return [py_float(v[i]) for i in range(int(v.shape[0]))]


def jax_x64_enabled() -> bool:
    try:
        return bool(jax.config.jax_enable_x64)
    except AttributeError:
        return bool(jax.config.read("jax_enable_x64"))


def source_numpy_markers() -> dict[str, bool]:
    text = Path(__file__).read_text(encoding="utf-8")
    return {
        "import_numpy_present": ("import " + "numpy") in text or ("from " + "numpy") in text,
        "np_dot_present": re.search(r"(?<![A-Za-z0-9_])np\.", text) is not None,
        "numpy_method_bridge_present": ("." + "numpy()") in text,
    }


def hamming(a: tuple[str, str], b: tuple[str, str]) -> int:
    return sum(1 for x, y in zip(a, b, strict=True) if x != y)


def adjacent(i: int, j: int) -> bool:
    return hamming(VERTEX_LABELS[i], VERTEX_LABELS[j]) == 1


def is_hamiltonian_cycle(cycle: list[int]) -> bool:
    if len(cycle) != 4 or len(set(cycle)) != 4:
        return False
    return all(adjacent(cycle[idx], cycle[(idx + 1) % len(cycle)]) for idx in range(len(cycle)))


def rotations(cycle: list[int]) -> list[list[int]]:
    return [cycle[idx:] + cycle[:idx] for idx in range(len(cycle))]


def cycle_key(cycle: list[int]) -> str:
    return ",".join(str(x + 1) for x in cycle)


def normalize_rotation(cycle: list[int]) -> list[int]:
    return sorted(rotations(cycle), key=cycle_key)[0]


def enumerate_directed_hamiltonian_cycles() -> list[list[int]]:
    return [list(p) for p in permutations(range(4)) if is_hamiltonian_cycle(list(p))]


def inequivalent_cycles_up_to_rotation(all_cycles: list[list[int]]) -> list[list[int]]:
    seen: set[str] = set()
    out: list[list[int]] = []
    for cycle in all_cycles:
        normalized = normalize_rotation(cycle)
        key = cycle_key(normalized)
        if key not in seen:
            seen.add(key)
            out.append(normalized)
    return sorted(out, key=cycle_key)


def signed_area2(cycle: list[int], coords: list[tuple[float, float]]) -> float:
    area2 = 0.0
    for idx, vertex in enumerate(cycle):
        nxt = cycle[(idx + 1) % len(cycle)]
        x1, y1 = coords[vertex]
        x2, y2 = coords[nxt]
        area2 += x1 * y2 - y1 * x2
    return float(area2)


def chirality_from_cycle(cycle: list[int], coords: list[tuple[float, float]]) -> int:
    area2 = signed_area2(cycle, coords)
    if area2 < -TOL:
        return 1
    if area2 > TOL:
        return -1
    return 0


def axis_flip_sequence(cycle: list[int]) -> list[str]:
    seq: list[str] = []
    for idx, vertex in enumerate(cycle):
        nxt = cycle[(idx + 1) % len(cycle)]
        a = VERTEX_LABELS[vertex]
        b = VERTEX_LABELS[nxt]
        if a[0] != b[0]:
            seq.append("lowercase_winlose_axis")
        elif a[1] != b[1]:
            seq.append("uppercase_WINLOSE_axis")
        else:
            seq.append("none")
    return seq


def cycle_payload(cycle: list[int], coords: list[tuple[float, float]]) -> dict[str, Any]:
    chi = chirality_from_cycle(cycle, coords)
    return {
        "cycle_vertices_1_based": [x + 1 for x in cycle],
        "cycle_labels": [[VERTEX_LABELS[i][0], VERTEX_LABELS[i][1]] for i in cycle],
        "axis_flip_sequence": axis_flip_sequence(cycle),
        "signed_area2": signed_area2(cycle, coords),
        "chirality": chi,
        "orientation_readout": (
            "cw_derived_from_negative_signed_area"
            if chi == 1
            else ("ccw_derived_from_positive_signed_area" if chi == -1 else "degenerate_zero_area")
        ),
    }


def build_igt() -> dict[str, Any]:
    all_cycles = enumerate_directed_hamiltonian_cycles()
    cycles = inequivalent_cycles_up_to_rotation(all_cycles)
    payloads = [cycle_payload(cycle, VERTEX_COORDS) for cycle in cycles]
    signs = [int(p["chirality"]) for p in payloads]
    return {
        "vertices": [
            {
                "id": idx + 1,
                "label": [VERTEX_LABELS[idx][0], VERTEX_LABELS[idx][1]],
                "coord": [VERTEX_COORDS[idx][0], VERTEX_COORDS[idx][1]],
            }
            for idx in range(4)
        ],
        "edges": [[i + 1, j + 1] for i in range(4) for j in range(i + 1, 4) if adjacent(i, j)],
        "directed_hamiltonian_cycle_count": len(all_cycles),
        "inequivalent_directed_cycles_up_to_rotation_count": len(cycles),
        "exactly_two_igt_cycles": len(cycles) == 2,
        "cycles": payloads,
        "igt_chirality": signs,
        "igt_chirality_signed": len(signs) == 2 and sorted(signs) == [-1, 1],
    }


def engine_s(engine: str, *, no_flip_control: bool = False) -> float:
    if no_flip_control or engine == "type1":
        return 1.0
    return -1.0


def bloch_rhs(engine: str, r: jax.Array, *, no_flip_control: bool = False) -> jax.Array:
    return 2.0 * engine_s(engine, no_flip_control=no_flip_control) * jnp.cross(N_GENERIC, r)


def rk4_bloch_step(engine: str, r: jax.Array, *, no_flip_control: bool = False) -> jax.Array:
    def f(x: jax.Array) -> jax.Array:
        return bloch_rhs(engine, x, no_flip_control=no_flip_control)

    k1 = f(r)
    k2 = f(r + 0.5 * QIT_DT * k1)
    k3 = f(r + 0.5 * QIT_DT * k2)
    k4 = f(r + QIT_DT * k3)
    return r + (QIT_DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def qit_chirality(engine: str, *, no_flip_control: bool = False) -> dict[str, Any]:
    r = R0
    circulation_sum = 0.0
    min_circulation = float("inf")
    max_circulation = float("-inf")
    for _ in range(QIT_STEPS):
        rdot = bloch_rhs(engine, r, no_flip_control=no_flip_control)
        circulation = py_float(jnp.dot(jnp.cross(r, rdot), N_GENERIC))
        circulation_sum += circulation
        min_circulation = min(min_circulation, circulation)
        max_circulation = max(max_circulation, circulation)
        r = rk4_bloch_step(engine, r, no_flip_control=no_flip_control)
    mean_circulation = circulation_sum / QIT_STEPS
    sign_value = 1 if mean_circulation > TOL else (-1 if mean_circulation < -TOL else 0)
    return {
        "engine": engine,
        "s_from_dynamics": engine_s(engine, no_flip_control=no_flip_control),
        "no_flip_control": no_flip_control,
        "mean_circulation": float(mean_circulation),
        "min_circulation": float(min_circulation),
        "max_circulation": float(max_circulation),
        "terminal_bloch": vec_payload(r),
        "chirality": sign_value,
    }


def build_qit() -> dict[str, Any]:
    type1 = qit_chirality("type1")
    type2 = qit_chirality("type2")
    no_flip_type1 = qit_chirality("type1", no_flip_control=True)
    no_flip_type2 = qit_chirality("type2", no_flip_control=True)
    signs = [int(type1["chirality"]), int(type2["chirality"])]
    no_flip_signs = [int(no_flip_type1["chirality"]), int(no_flip_type2["chirality"])]
    return {
        "terrain_equation_source": "Hamiltonian circulation channel of the engine_noncollapse_probe terrain equations: d rho/dt = -i[H0,rho] for Type1 and +i[H0,rho] for Type2, expressed as rdot = +/- 2 n x r.",
        "h0_generic_n": vec_payload(N_GENERIC),
        "initial_bloch": vec_payload(R0),
        "dt": QIT_DT,
        "steps": QIT_STEPS,
        "type1": type1,
        "type2": type2,
        "qit_chirality": signs,
        "qit_chirality_signed": len(signs) == 2 and sorted(signs) == [-1, 1],
        "no_flip_control": {
            "type1": no_flip_type1,
            "type2": no_flip_type2,
            "qit_chirality": no_flip_signs,
            "unique_chirality_count": len(set(no_flip_signs)),
            "correspondence_collapses": len(set(no_flip_signs)) < 2,
        },
    }


def residual_for(igt_signs: list[int], qit_signs: list[int], correspondence: str) -> float:
    if correspondence == "identity":
        return float(sum(abs(igt_signs[idx] - qit_signs[idx]) for idx in range(2)))
    if correspondence == "swap":
        return float(abs(igt_signs[0] - qit_signs[1]) + abs(igt_signs[1] - qit_signs[0]))
    return float("inf")


def test_correspondences(igt_signs: list[int], qit_signs: list[int]) -> dict[str, Any]:
    identity_residual = residual_for(igt_signs, qit_signs, "identity")
    swap_residual = residual_for(igt_signs, qit_signs, "swap")
    if identity_residual <= TOL and swap_residual > TOL:
        selected = "identity"
    elif swap_residual <= TOL and identity_residual > TOL:
        selected = "swap"
    elif identity_residual <= TOL and swap_residual <= TOL:
        selected = "both"
    else:
        selected = "none"
    return {
        "identity_residual": float(identity_residual),
        "swap_residual": float(swap_residual),
        "selected": selected,
        "aligned": selected in {"identity", "swap"},
    }


def randomized_winlose_control(
    cycles: list[list[int]], qit_signs: list[int], fixed_correspondence: str
) -> dict[str, Any]:
    perms = [list(p) for p in permutations(range(4))]
    rows: list[dict[str, Any]] = []
    fixed_matches = 0
    any_matches = 0
    degenerate = 0
    nonidentity_count = 0
    nonidentity_fixed_matches = 0
    for perm in perms:
        coords = [VERTEX_COORDS[perm[idx]] for idx in range(4)]
        signs = [chirality_from_cycle(cycle, coords) for cycle in cycles]
        identity_residual = residual_for(signs, qit_signs, "identity")
        swap_residual = residual_for(signs, qit_signs, "swap")
        fixed_residual = residual_for(signs, qit_signs, fixed_correspondence)
        is_identity_perm = perm == list(range(4))
        if not is_identity_perm:
            nonidentity_count += 1
            if fixed_residual <= TOL:
                nonidentity_fixed_matches += 1
        fixed_matches += 1 if fixed_residual <= TOL else 0
        any_matches += 1 if min(identity_residual, swap_residual) <= TOL else 0
        degenerate += 1 if any(sign == 0 for sign in signs) else 0
        rows.append(
            {
                "permutation_1_based": [x + 1 for x in perm],
                "is_original": is_identity_perm,
                "scrambled_igt_chirality": signs,
                "identity_residual": float(identity_residual),
                "swap_residual": float(swap_residual),
                "fixed_correspondence_residual": float(fixed_residual),
            }
        )
    decorrelates = nonidentity_fixed_matches < nonidentity_count
    return {
        "mode": "exhaustive_24_vertex_label_scrambles",
        "total_scrambles": len(perms),
        "nonidentity_scrambles": nonidentity_count,
        "fixed_correspondence": fixed_correspondence,
        "fixed_correspondence_match_count": fixed_matches,
        "nonidentity_fixed_correspondence_match_count": nonidentity_fixed_matches,
        "any_correspondence_match_count": any_matches,
        "degenerate_zero_area_count": degenerate,
        "fixed_correspondence_match_rate": fixed_matches / len(perms),
        "nonidentity_fixed_correspondence_match_rate": nonidentity_fixed_matches / max(nonidentity_count, 1),
        "decorrelates": decorrelates,
        "control_fired": decorrelates,
        "rows": rows,
    }


def random_sign_assignment_control(qit_signs: list[int]) -> dict[str, Any]:
    assignments = [[a, b] for a in [-1, 1] for b in [-1, 1]]
    any_work = 0
    identity_work = 0
    opposite_pairs = 0
    opposite_any_work = 0
    rows: list[dict[str, Any]] = []
    for signs in assignments:
        identity_residual = residual_for(signs, qit_signs, "identity")
        swap_residual = residual_for(signs, qit_signs, "swap")
        any_ok = min(identity_residual, swap_residual) <= TOL
        identity_ok = identity_residual <= TOL
        any_work += 1 if any_ok else 0
        identity_work += 1 if identity_ok else 0
        if signs[0] != signs[1]:
            opposite_pairs += 1
            opposite_any_work += 1 if any_ok else 0
        rows.append(
            {
                "random_igt_signs": signs,
                "identity_residual": float(identity_residual),
                "swap_residual": float(swap_residual),
                "any_correspondence_works": any_ok,
            }
        )
    return {
        "assignment_count": len(assignments),
        "any_correspondence_work_count": any_work,
        "identity_work_count": identity_work,
        "any_correspondence_work_rate": any_work / len(assignments),
        "identity_work_rate": identity_work / len(assignments),
        "opposite_signed_pair_count": opposite_pairs,
        "opposite_signed_pair_any_correspondence_work_count": opposite_any_work,
        "random_opposite_signed_pair_always_works_under_one_of_two_correspondences": (
            opposite_pairs > 0 and opposite_any_work == opposite_pairs
        ),
        "would_also_work": any_work > 0,
        "uninformative_warning": (
            "A two-item random opposite-sign assignment also aligns under identity or swap; "
            "signed two-ness alone is not enough for admission."
        ),
        "rows": rows,
    }


def parity_block(result: dict[str, Any]) -> dict[str, Any]:
    if not JULIA_REFERENCE_PATH.exists():
        return {
            "peer_result_path": str(JULIA_REFERENCE_PATH),
            "peer_available": False,
            "parity_max_diff": None,
            "worst_key": None,
            "within_1e_9": False,
            "strict_divergence_gt_1e_6": False,
            "missing_from_peer": sorted(result["shared_scalars"].keys()),
            "missing_from_self": [],
            "diffs": {},
            "status": "pending_peer",
        }
    peer = json.loads(JULIA_REFERENCE_PATH.read_text(encoding="utf-8"))
    self_scalars = result["shared_scalars"]
    peer_scalars = peer["shared_scalars"]
    missing_from_peer = sorted(set(self_scalars) - set(peer_scalars))
    missing_from_self = sorted(set(peer_scalars) - set(self_scalars))
    diffs: dict[str, float] = {}
    max_diff = 0.0
    worst_key = ""
    for key in sorted(set(self_scalars) & set(peer_scalars)):
        diff = abs(float(self_scalars[key]) - float(peer_scalars[key]))
        diffs[key] = diff
        if diff > max_diff:
            max_diff = diff
            worst_key = key
    within = not missing_from_peer and not missing_from_self and max_diff < TOL
    strict_divergence = bool(missing_from_peer or missing_from_self or max_diff > STRICT_STOP_TOL)
    return {
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "peer_available": True,
        "parity_max_diff": float(max_diff),
        "worst_key": worst_key,
        "within_1e_9": within,
        "strict_divergence_gt_1e_6": strict_divergence,
        "missing_from_peer": missing_from_peer,
        "missing_from_self": missing_from_self,
        "diffs": diffs,
        "status": "pass" if within else "fail_closed",
    }


def build_result() -> dict[str, Any]:
    igt = build_igt()
    qit = build_qit()
    cycles = inequivalent_cycles_up_to_rotation(enumerate_directed_hamiltonian_cycles())
    igt_signs = [int(x) for x in igt["igt_chirality"]]
    qit_signs = [int(x) for x in qit["qit_chirality"]]
    rosetta = test_correspondences(igt_signs, qit_signs)
    no_flip_rosetta = test_correspondences(igt_signs, qit["no_flip_control"]["qit_chirality"])
    randomized = randomized_winlose_control(cycles, qit_signs, str(rosetta["selected"]))
    random_sign = random_sign_assignment_control(qit_signs)

    fixed_alignment_controls_pass = (
        bool(rosetta["aligned"])
        and bool(randomized["control_fired"])
        and bool(qit["no_flip_control"]["correspondence_collapses"])
    )
    shared_signed_invariant = (
        fixed_alignment_controls_pass
        and not bool(random_sign["random_opposite_signed_pair_always_works_under_one_of_two_correspondences"])
    )
    rosetta_is_trivial_2ness = (
        not shared_signed_invariant
        and bool(random_sign["random_opposite_signed_pair_always_works_under_one_of_two_correspondences"])
    )

    verdicts = {
        "exactly_two_igt_cycles": igt["exactly_two_igt_cycles"],
        "igt_chirality_signed": igt["igt_chirality_signed"],
        "qit_chirality_signed": qit["qit_chirality_signed"],
        "rosetta_correspondence": rosetta["selected"],
        "fixed_correspondence_aligns": rosetta["aligned"],
        "randomized_winlose_control_decorrelates": randomized["decorrelates"],
        "no_flip_control_collapses": qit["no_flip_control"]["correspondence_collapses"],
        "random_sign_assignment_would_also_work": random_sign["would_also_work"],
        "fixed_alignment_controls_pass": fixed_alignment_controls_pass,
        "shared_signed_invariant": shared_signed_invariant,
        "rosetta_is_trivial_2ness": rosetta_is_trivial_2ness,
    }

    shared_scalars = {
        "igt_directed_hamiltonian_cycle_count": float(igt["directed_hamiltonian_cycle_count"]),
        "igt_inequivalent_cycles_up_to_rotation_count": float(
            igt["inequivalent_directed_cycles_up_to_rotation_count"]
        ),
        "igt_cycle_1_chirality": float(igt_signs[0]),
        "igt_cycle_2_chirality": float(igt_signs[1]),
        "igt_cycle_1_signed_area2": float(igt["cycles"][0]["signed_area2"]),
        "igt_cycle_2_signed_area2": float(igt["cycles"][1]["signed_area2"]),
        "qit_type1_chirality": float(qit_signs[0]),
        "qit_type2_chirality": float(qit_signs[1]),
        "qit_type1_mean_circulation": float(qit["type1"]["mean_circulation"]),
        "qit_type2_mean_circulation": float(qit["type2"]["mean_circulation"]),
        "qit_no_flip_type1_chirality": float(qit["no_flip_control"]["qit_chirality"][0]),
        "qit_no_flip_type2_chirality": float(qit["no_flip_control"]["qit_chirality"][1]),
        "qit_no_flip_unique_chirality_count": float(qit["no_flip_control"]["unique_chirality_count"]),
        "rosetta_identity_residual": float(rosetta["identity_residual"]),
        "rosetta_swap_residual": float(rosetta["swap_residual"]),
        "no_flip_identity_residual": float(no_flip_rosetta["identity_residual"]),
        "no_flip_swap_residual": float(no_flip_rosetta["swap_residual"]),
        "randomized_nonidentity_fixed_match_rate": float(
            randomized["nonidentity_fixed_correspondence_match_rate"]
        ),
        "randomized_degenerate_zero_area_count": float(randomized["degenerate_zero_area_count"]),
        "random_sign_any_correspondence_work_rate": float(random_sign["any_correspondence_work_rate"]),
        "random_sign_identity_work_rate": float(random_sign["identity_work_rate"]),
        "verdict_exactly_two_igt_cycles": bool_scalar(bool(verdicts["exactly_two_igt_cycles"])),
        "verdict_igt_chirality_signed": bool_scalar(bool(verdicts["igt_chirality_signed"])),
        "verdict_qit_chirality_signed": bool_scalar(bool(verdicts["qit_chirality_signed"])),
        "verdict_fixed_correspondence_aligns": bool_scalar(bool(verdicts["fixed_correspondence_aligns"])),
        "verdict_randomized_winlose_control_decorrelates": bool_scalar(
            bool(verdicts["randomized_winlose_control_decorrelates"])
        ),
        "verdict_no_flip_control_collapses": bool_scalar(bool(verdicts["no_flip_control_collapses"])),
        "verdict_random_sign_assignment_would_also_work": bool_scalar(
            bool(verdicts["random_sign_assignment_would_also_work"])
        ),
        "verdict_shared_signed_invariant": bool_scalar(bool(verdicts["shared_signed_invariant"])),
        "verdict_rosetta_is_trivial_2ness": bool_scalar(bool(verdicts["rosetta_is_trivial_2ness"])),
        "numpy_compute_used_flag": 0.0,
        "promotion_allowed_flag": 0.0,
    }

    tool_manifest = {
        "JAX jax.numpy x64": {
            "tried": True,
            "used": True,
            "role": "mirror_stress_jnp_x64_no_numpy",
            "reason": "load-bearing for Bloch circulation integration, vector cross products, norms, and signed QIT chirality readouts",
        },
        "Julia LinearAlgebra": {
            "tried": True,
            "used": False,
            "role": "peer_reference_expected",
            "reason": "supportive peer parity lane read from its result JSON when present; no Julia compute is used inside JAX",
        },
    }
    tool_depth = {"JAX jax.numpy x64": "load_bearing", "Julia LinearAlgebra": "supportive"}
    source_markers = source_numpy_markers()

    result: dict[str, Any] = {
        "sim_id": OBJECT_ID,
        "object_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0.0",
        "backend": "jax",
        "backend_roles": {
            "julia": "reference_native_linearalgebra_no_pycall_no_numpy",
            "jax": "mirror_stress_jnp_x64_no_numpy",
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "PROMOTION_ALLOWED": False,
        "FORMAL_ADMISSION_ALLOWED": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "dual_backend_rosetta_convergence_probe",
        "carrier_layer": "igt_four_ring_and_single_qubit_bloch_engine_chirality",
        "geometry_layer": "signed_square_orientation_vs_signed_bloch_circulation",
        "claim_ceiling": "Scratch diagnostic only: independent IGT cycle chirality and QIT engine circulation chirality comparison; no QIT, engine, axis, bridge, or formal admission claim.",
        "allowed_claims": [
            "IGT side enumerates the four-ring directed Hamiltonian cycles and derives signed orientation from traversal only",
            "QIT side integrates signed Bloch circulation from Type1/Type2 engine dynamics only",
            "Rosetta side tests identity/swap correspondences after independent invariants are computed",
            "controls report whether the sign-only match is informative or trivial",
        ],
        "blocked_consumers": [
            "QIT_engine_admission",
            "Axis0",
            "bridge",
            "formal_admission",
            "promotion",
            "canonical_engine_evidence",
        ],
        "out_of_scope": [
            "QIT admission",
            "engine promotion",
            "Axis0",
            "bridge",
            "gravity",
            "win/lose as dynamics",
        ],
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "source_alignment": {
            "igt_structure_source": "system_v4/probes/sim_igt_atom_2_structure.py",
            "qit_engine_source": "system_v5/julia_carrier/engine_noncollapse_probe.jl",
            "genealogy_rule": "/Users/joshuaeisenhart/wiki/concepts/igt-to-qit-engine-genealogy.md: Sim both independently; do not assert the connection in advance; let the pattern speak.",
        },
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "igt": igt,
        "qit": qit,
        "rosetta_test": rosetta,
        "controls": {
            "randomized_winlose": randomized,
            "no_flip": {
                "qit_no_flip": qit["no_flip_control"],
                "rosetta_under_no_flip": no_flip_rosetta,
                "control_fired": qit["no_flip_control"]["correspondence_collapses"],
            },
            "random_sign_assignment": random_sign,
        },
        "verdicts": verdicts,
        "shared_scalars": shared_scalars,
        "tools": ["JAX jax.numpy x64", "Julia LinearAlgebra"],
        "tool_manifest": tool_manifest,
        "TOOL_MANIFEST": tool_manifest,
        "tool_integration_depth": tool_depth,
        "TOOL_INTEGRATION_DEPTH": tool_depth,
        "numpy_compute_used": False,
        "source_numpy_markers": source_markers,
        "jax_x64_enabled": jax_x64_enabled(),
        "divergence_log": [
            "IGT chirality is derived from directed cycle traversal signed area on the win/lose x WIN/LOSE square.",
            "QIT chirality is derived from integrated Bloch circulation dot((r x rdot), n), using the Type1/Type2 commutator sign from the terrain equations.",
            "The randomized WIN/LOSE control exhaustively scrambles semantic vertex labels and checks whether the fixed correspondence remains correlated.",
            "The no-flip control removes the Weyl sign flip, making both QIT engine circulation signs the same and collapsing the two-element correspondence.",
            "The random-sign baseline is intentionally reported: a two-item opposite-sign random assignment can also align under identity or swap, so sign-only agreement remains uninformative for admission.",
        ],
        "honest_caveat": "The fixed identity correspondence aligns the independently computed signs, and both requested controls fire, but the random opposite-sign baseline means this scratch probe must not be treated as an admitted shared invariant.",
        "plain_sentence": "The IGT 2-ring and QIT engine independently align as a signed two-chirality pair under identity, but this sign-only Rosetta test is still vulnerable to trivial two-ness because a random opposite-sign pair would also align under one of the two correspondences.",
    }
    result["parity"] = parity_block(result)
    result["all_pass"] = (
        bool(result["jax_x64_enabled"])
        and not bool(result["numpy_compute_used"])
        and not any(source_markers.values())
        and bool(verdicts["exactly_two_igt_cycles"])
        and bool(verdicts["igt_chirality_signed"])
        and bool(verdicts["qit_chirality_signed"])
        and bool(verdicts["randomized_winlose_control_decorrelates"])
        and bool(verdicts["no_flip_control_collapses"])
        and bool(result["parity"]["within_1e_9"])
    )
    result["stop_condition_fired"] = bool(result["parity"]["strict_divergence_gt_1e_6"])
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["shared_scalars"]
    print(f"rosetta_igt_qit_convergence_probe jax wrote {RESULT_PATH}")
    print(
        "exactly_two_igt_cycles={exactly} igt_chirality=[{c1}, {c2}]".format(
            exactly=result["verdicts"]["exactly_two_igt_cycles"],
            c1=s["igt_cycle_1_chirality"],
            c2=s["igt_cycle_2_chirality"],
        )
    )
    print(
        "qit_chirality=[{q1}, {q2}] correspondence={corr} identity_residual={identity} swap_residual={swap}".format(
            q1=s["qit_type1_chirality"],
            q2=s["qit_type2_chirality"],
            corr=result["verdicts"]["rosetta_correspondence"],
            identity=s["rosetta_identity_residual"],
            swap=s["rosetta_swap_residual"],
        )
    )
    print(
        "controls randomized_decorrelates={rand} no_flip_collapses={noflip} random_sign_would_work={rsign}".format(
            rand=result["verdicts"]["randomized_winlose_control_decorrelates"],
            noflip=result["verdicts"]["no_flip_control_collapses"],
            rsign=result["verdicts"]["random_sign_assignment_would_also_work"],
        )
    )
    print(
        "shared_signed_invariant={shared} rosetta_is_trivial_2ness={trivial} parity_max_diff={diff} numpy_compute_used={numpy_used} jax_x64_enabled={x64}".format(
            shared=result["verdicts"]["shared_signed_invariant"],
            trivial=result["verdicts"]["rosetta_is_trivial_2ness"],
            diff=result["parity"]["parity_max_diff"],
            numpy_used=result["numpy_compute_used"],
            x64=result["jax_x64_enabled"],
        )
    )
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED rosetta_igt_qit_convergence_probe jax")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
