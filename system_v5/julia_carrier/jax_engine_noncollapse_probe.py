import jax; jax.config.update("jax_enable_x64", True)

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any

import jax.numpy as jnp


OBJECT_ID = "engine_noncollapse_probe"
BASE_DIR = Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier")
RESULT_PATH = BASE_DIR / "engine_noncollapse_probe_jax_results.json"
JULIA_REFERENCE_PATH = BASE_DIR / "engine_noncollapse_probe_julia_results.json"
TOL = 1.0e-9
STRICT_STOP_TOL = 1.0e-6
DISTINCT_TOL = 1.0e-5
DT = 0.002
STAGE_STEPS = 90
TERRAIN_STEPS = 360
PIT_SOURCE_STEPS = 4200

I2 = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
SX = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SY = jnp.array([[0.0 + 0.0j, -1.0j], [1.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SZ = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, -1.0 + 0.0j]], dtype=jnp.complex128)
SM = jnp.array([[0.0 + 0.0j, 0.0 + 0.0j], [1.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
SP = jnp.array([[0.0 + 0.0j, 1.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
P_UP = jnp.array([[1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 0.0 + 0.0j]], dtype=jnp.complex128)
P_DN = jnp.array([[0.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]], dtype=jnp.complex128)
N_GENERIC = jnp.array([0.37, -0.51, 0.78], dtype=jnp.float64)
N_GENERIC = N_GENERIC / jnp.linalg.norm(N_GENERIC)
H0 = N_GENERIC[0] * SX + N_GENERIC[1] * SY + N_GENERIC[2] * SZ
HC = 0.63 * SZ
EPS_F = 0.17
EPS_V = 0.08
EPS_P = 0.05
GAMMA_F_Z = 0.46
GAMMA_F_X = 0.19
GAMMA_P = 2.35
KAPPA_UP = 0.37
KAPPA_DN = 0.23
L_SHARED = [jnp.sqrt(GAMMA_F_Z) * SZ, jnp.sqrt(GAMMA_F_X) * SX]
L_PIT = jnp.sqrt(GAMMA_P) * SM
L_SOURCE = jnp.sqrt(GAMMA_P) * SP
PROJECTORS = [P_UP, P_DN]
KAPPAS = [KAPPA_UP, KAPPA_DN]


def py_float(x: Any) -> float:
    return float(jax.device_get(x))


def py_bool(x: Any) -> bool:
    return bool(jax.device_get(x))


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


def dag(m: jax.Array) -> jax.Array:
    return jnp.conj(m.T)


def comm(h: jax.Array, rho: jax.Array) -> jax.Array:
    return h @ rho - rho @ h


def density_from_bloch(r: jax.Array) -> jax.Array:
    return 0.5 * (I2 + r[0] * SX + r[1] * SY + r[2] * SZ)


def bloch_z(rho: jax.Array) -> float:
    return py_float(jnp.real(jnp.trace(rho @ SZ)))


def project_density(rho: jax.Array) -> jax.Array:
    rho_h = (rho + dag(rho)) / 2.0
    vals, vecs = jnp.linalg.eigh(rho_h)
    vals = jnp.maximum(jnp.real(vals), 0.0)
    total = py_float(jnp.sum(vals))
    if total <= 1.0e-15:
        return I2 / 2.0
    rho_p = vecs @ jnp.diag(vals.astype(jnp.complex128)) @ dag(vecs)
    rho_p = (rho_p + dag(rho_p)) / 2.0
    return rho_p / jnp.real(jnp.trace(rho_p))


def dissipator(l: jax.Array, rho: jax.Array) -> jax.Array:
    ldl = dag(l) @ l
    return l @ rho @ dag(l) - 0.5 * (ldl @ rho + rho @ ldl)


def sum_dissipators(ls: list[jax.Array], rho: jax.Array) -> jax.Array:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for l in ls:
        out = out + dissipator(l, rho)
    return out


def dephase_generator(rho: jax.Array) -> jax.Array:
    out = jnp.zeros((2, 2), dtype=jnp.complex128)
    for p, kappa in zip(PROJECTORS, KAPPAS, strict=True):
        out = out + kappa * (p @ rho @ p - 0.5 * (p @ rho + rho @ p))
    return out


def comm_coeff(engine: str, no_flip_control: bool) -> complex:
    if no_flip_control or engine == "type1":
        return -1.0j
    return 1.0j


def terrain_generator(terrain: str, engine: str, rho: jax.Array, *, no_flip_control: bool = False) -> jax.Array:
    c = comm_coeff(engine, no_flip_control)
    if terrain in {"Funnel", "Cannon"}:
        return sum_dissipators(L_SHARED, rho) + c * EPS_F * comm(H0, rho)
    if terrain in {"Vortex", "Spiral"}:
        return c * comm(H0, rho) + EPS_V * sum_dissipators(L_SHARED, rho)
    if terrain in {"Pit", "Source"}:
        l_p = L_SOURCE if terrain == "Source" and not no_flip_control else L_PIT
        return dissipator(l_p, rho) + c * EPS_P * comm(H0, rho)
    if terrain in {"Hill", "Citadel"}:
        return c * comm(HC, rho) + dephase_generator(rho)
    raise ValueError(f"unknown terrain: {terrain}")


def rk4_step(rho: jax.Array, terrain: str, engine: str, *, no_flip_control: bool = False) -> jax.Array:
    def f(x: jax.Array) -> jax.Array:
        return terrain_generator(terrain, engine, x, no_flip_control=no_flip_control)

    k1 = f(rho)
    k2 = f(rho + 0.5 * DT * k1)
    k3 = f(rho + 0.5 * DT * k2)
    k4 = f(rho + DT * k3)
    return project_density(rho + (DT / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4))


def integrate_terrain(terrain: str, engine: str, rho0: jax.Array, *, steps: int, no_flip_control: bool = False) -> jax.Array:
    rho = rho0
    for _ in range(steps):
        rho = rk4_step(rho, terrain, engine, no_flip_control=no_flip_control)
    return rho


def trace_distance(a: jax.Array, b: jax.Array) -> float:
    delta = (a - b + dag(a - b)) / 2.0
    vals = jnp.linalg.eigvalsh(delta)
    return py_float(0.5 * jnp.sum(jnp.abs(vals)))


def placement_rows(engine: str) -> list[dict[str, str]]:
    if engine == "type1":
        return [
            {"loop": "inner", "terrain": "Funnel", "grammar_label": "win"},
            {"loop": "inner", "terrain": "Vortex", "grammar_label": "lose"},
            {"loop": "inner", "terrain": "Pit", "grammar_label": "lose"},
            {"loop": "inner", "terrain": "Hill", "grammar_label": "win"},
            {"loop": "outer", "terrain": "Funnel", "grammar_label": "LOSE"},
            {"loop": "outer", "terrain": "Vortex", "grammar_label": "WIN"},
            {"loop": "outer", "terrain": "Pit", "grammar_label": "LOSE"},
            {"loop": "outer", "terrain": "Hill", "grammar_label": "WIN"},
        ]
    return [
        {"loop": "inner", "terrain": "Cannon", "grammar_label": "lose"},
        {"loop": "inner", "terrain": "Spiral", "grammar_label": "win"},
        {"loop": "inner", "terrain": "Source", "grammar_label": "lose"},
        {"loop": "inner", "terrain": "Citadel", "grammar_label": "win"},
        {"loop": "outer", "terrain": "Cannon", "grammar_label": "WIN"},
        {"loop": "outer", "terrain": "Spiral", "grammar_label": "LOSE"},
        {"loop": "outer", "terrain": "Source", "grammar_label": "LOSE"},
        {"loop": "outer", "terrain": "Citadel", "grammar_label": "WIN"},
    ]


def run_engine(engine: str, rho0: jax.Array, *, no_flip_control: bool = False) -> list[jax.Array]:
    rho = rho0
    states = [rho]
    for row in placement_rows(engine):
        rho = integrate_terrain(row["terrain"], engine, rho, steps=STAGE_STEPS, no_flip_control=no_flip_control)
        states.append(rho)
    return states


def trajectory_metrics(a: list[jax.Array], b: list[jax.Array]) -> dict[str, Any]:
    distances = [trace_distance(x, y) for x, y in zip(a, b, strict=True)]
    return {
        "max_trace_distance": float(max(distances)),
        "terminal_trace_distance": float(distances[-1]),
        "per_state_trace_distances": [float(x) for x in distances],
    }


def terrain_pairwise(engine: str, rho0: jax.Array) -> dict[str, Any]:
    terrains = [row["terrain"] for row in placement_rows(engine)[:4]]
    terminals = {terrain: integrate_terrain(terrain, engine, rho0, steps=TERRAIN_STEPS) for terrain in terrains}
    pair_distances: dict[str, float] = {}
    min_distance = float("inf")
    for i in range(len(terrains) - 1):
        for j in range(i + 1, len(terrains)):
            key = f"{terrains[i]}__{terrains[j]}"
            dist = trace_distance(terminals[terrains[i]], terminals[terrains[j]])
            pair_distances[key] = float(dist)
            min_distance = min(min_distance, dist)
    return {
        "terrains": terrains,
        "pair_distances": pair_distances,
        "min_pairwise_trace_distance": float(min_distance),
        "all_pairwise_distinct": min_distance > DISTINCT_TOL,
    }


def grammar_balance() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for engine in ["type1", "type2"]:
        rows = placement_rows(engine)
        outer = [row["grammar_label"] for row in rows if row["loop"] == "outer"]
        inner = [row["grammar_label"] for row in rows if row["loop"] == "inner"]
        out[engine] = {
            "outer_WIN": outer.count("WIN"),
            "outer_LOSE": outer.count("LOSE"),
            "inner_win": inner.count("win"),
            "inner_lose": inner.count("lose"),
            "balanced": (
                outer.count("WIN") == 2
                and outer.count("LOSE") == 2
                and inner.count("win") == 2
                and inner.count("lose") == 2
            ),
        }
    return out


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
            "stop_condition_fired": False,
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
    for key, value in self_scalars.items():
        if key in peer_scalars:
            diff = abs(float(value) - float(peer_scalars[key]))
            diffs[key] = diff
            if diff > max_diff:
                max_diff = diff
                worst_key = key
    within = not missing_from_peer and not missing_from_self and max_diff < TOL
    strict_divergence = max_diff > STRICT_STOP_TOL
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
        "stop_condition_fired": strict_divergence,
        "status": "pass" if within else "fail_closed",
    }


def build_result() -> dict[str, Any]:
    rho0 = density_from_bloch(jnp.array([0.23, -0.31, 0.17], dtype=jnp.float64))
    type1 = run_engine("type1", rho0)
    type2 = run_engine("type2", rho0)
    no_flip_type1 = run_engine("type1", rho0, no_flip_control=True)
    no_flip_type2 = run_engine("type2", rho0, no_flip_control=True)
    flip_metrics = trajectory_metrics(type1, type2)
    no_flip_metrics = trajectory_metrics(no_flip_type1, no_flip_type2)

    type1_terrain = terrain_pairwise("type1", rho0)
    type2_terrain = terrain_pairwise("type2", rho0)
    balances = grammar_balance()

    pit_terminal = integrate_terrain("Pit", "type1", rho0, steps=PIT_SOURCE_STEPS)
    source_terminal = integrate_terrain("Source", "type2", rho0, steps=PIT_SOURCE_STEPS)
    pit_z = bloch_z(pit_terminal)
    source_z = bloch_z(source_terminal)

    verdicts = {
        "engines_distinct_under_flip": flip_metrics["max_trace_distance"] > DISTINCT_TOL,
        "collapse_under_no_flip_control": no_flip_metrics["max_trace_distance"] <= TOL,
        "four_terrains_distinct_per_engine": bool(type1_terrain["all_pairwise_distinct"])
        and bool(type2_terrain["all_pairwise_distinct"]),
        "outcomes_balanced_grammar": bool(balances["type1"]["balanced"]) and bool(balances["type2"]["balanced"]),
        "pit_source_opposite_z_flow": pit_z < -0.5 and source_z > 0.5,
    }
    verdicts["owner_noncollapse_supported"] = (
        verdicts["engines_distinct_under_flip"]
        and verdicts["collapse_under_no_flip_control"]
        and verdicts["pit_source_opposite_z_flow"]
    )

    shared_scalars = {
        "c1_flip_trajectory_max_trace_distance": float(flip_metrics["max_trace_distance"]),
        "c1_flip_terminal_trace_distance": float(flip_metrics["terminal_trace_distance"]),
        "c1_no_flip_control_max_trace_distance": float(no_flip_metrics["max_trace_distance"]),
        "c1_no_flip_control_terminal_trace_distance": float(no_flip_metrics["terminal_trace_distance"]),
        "c2_type1_min_pairwise_terrain_trace_distance": float(type1_terrain["min_pairwise_trace_distance"]),
        "c2_type2_min_pairwise_terrain_trace_distance": float(type2_terrain["min_pairwise_trace_distance"]),
        "c3_type1_outer_WIN_count": float(balances["type1"]["outer_WIN"]),
        "c3_type1_outer_LOSE_count": float(balances["type1"]["outer_LOSE"]),
        "c3_type1_inner_win_count": float(balances["type1"]["inner_win"]),
        "c3_type1_inner_lose_count": float(balances["type1"]["inner_lose"]),
        "c3_type2_outer_WIN_count": float(balances["type2"]["outer_WIN"]),
        "c3_type2_outer_LOSE_count": float(balances["type2"]["outer_LOSE"]),
        "c3_type2_inner_win_count": float(balances["type2"]["inner_win"]),
        "c3_type2_inner_lose_count": float(balances["type2"]["inner_lose"]),
        "c4_type1_pit_terminal_z": float(pit_z),
        "c4_type2_source_terminal_z": float(source_z),
        "c4_pit_source_z_sum": float(pit_z + source_z),
        "engine_stage_placements_per_engine": 8.0,
        "engine_total_stage_placements": 16.0,
        "verdict_engines_distinct_under_flip": bool_scalar(verdicts["engines_distinct_under_flip"]),
        "verdict_collapse_under_no_flip_control": bool_scalar(verdicts["collapse_under_no_flip_control"]),
        "verdict_four_terrains_distinct_per_engine": bool_scalar(verdicts["four_terrains_distinct_per_engine"]),
        "verdict_outcomes_balanced_grammar": bool_scalar(verdicts["outcomes_balanced_grammar"]),
        "verdict_pit_source_opposite_z_flow": bool_scalar(verdicts["pit_source_opposite_z_flow"]),
        "verdict_owner_noncollapse_supported": bool_scalar(verdicts["owner_noncollapse_supported"]),
        "stage_grammar_dynamics_claim_flag": 0.0,
        "numpy_compute_used_flag": 0.0,
    }

    tool_manifest = {
        "JAX jax.numpy x64": {
            "tried": True,
            "used": True,
            "role": "mirror_stress_jnp_x64_no_numpy",
            "reason": "load-bearing for jax.numpy x64 density-matrix Lindblad/RK4 evolution, PSD projection, trace distances, eigenvalue checks, and JSON result scalars",
        },
        "Julia LinearAlgebra": {
            "tried": True,
            "used": False,
            "role": "peer_reference_expected",
            "reason": "supportive peer parity lane read from its result JSON when present; no Julia compute is used inside JAX",
        },
    }
    tool_depth = {
        "JAX jax.numpy x64": "load_bearing",
        "Julia LinearAlgebra": "supportive",
    }
    source_markers = source_numpy_markers()

    result: dict[str, Any] = {
        "object_id": OBJECT_ID,
        "backend": "jax",
        "backend_roles": {
            "julia": "reference_exact_native_linearalgebra",
            "jax": "mirror_stress_jnp_x64_no_numpy",
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "PROMOTION_ALLOWED": False,
        "FORMAL_ADMISSION_ALLOWED": False,
        "sim_execution_kind": "nonclassical",
        "sim_class": "engine_noncollapse_probe",
        "carrier_layer": "single_qubit_density_matrix_left_right_weyl_engine_diagnostic",
        "geometry_layer": "owner_terrain_lindblad_generators_on_left_right_weyl_flip",
        "claim_ceiling": "Scratch diagnostic only: tests owner Type 1/Type 2 engine non-collapse criteria under Weyl-flipped terrain equations; no Axis0, gravity, bridge, win/lose dynamics, promotion, or formal admission claim.",
        "allowed_claims": [
            "computed scratch verdicts for owner non-collapse criteria C1-C4",
            "no-flip control checks whether distinctness is load-bearing on Weyl sign and Pit/Source operator flip",
            "stage WIN/LOSE and win/lose counts are grammar only",
        ],
        "blocked_consumers": [
            "Axis0",
            "gravity",
            "bridge",
            "formal_admission",
            "promotion",
            "win_lose_dynamical_claim",
            "canonical_engine_admission",
        ],
        "out_of_scope": [
            "Axis0",
            "gravity",
            "bridge",
            "formal admission",
            "promotion",
            "win/lose as dynamics",
        ],
        "created_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__)),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_REFERENCE_PATH),
        "julia_reference_path": str(JULIA_REFERENCE_PATH),
        "tol": TOL,
        "strict_stop_tol": STRICT_STOP_TOL,
        "distinct_tol": DISTINCT_TOL,
        "dt": DT,
        "stage_steps": STAGE_STEPS,
        "terrain_steps": TERRAIN_STEPS,
        "pit_source_steps": PIT_SOURCE_STEPS,
        "h0_generic_n": vec_payload(N_GENERIC),
        "sigma_convention": {
            "sigma_minus": "[[0,0],[1,0]], sink toward Pauli-z=-1",
            "sigma_plus": "[[0,1],[0,0]], source toward Pauli-z=+1",
        },
        "source_alignment": {
            "owner_source": "system_v5/READ ONLY Reference Docs/apple axes terrain operator math.md:1249-1306",
            "atlas_source": "system_v5/READ ONLY Reference Docs/ENGINE_64_SCHEDULE_ATLAS.md:103-116",
            "weyl_sheet_pair_tie_in": "Uses the same s=+1/s=-1 left/right Weyl sign flip family as weyl_sheet_pair_probe; this is a consistency note only.",
        },
        "engine_equations": {
            "type1": [
                "Funnel: sum_k D_Lk(rho) - i eps_F [H0,rho]",
                "Vortex: -i[H0,rho] + eps_V sum_k D_Lk(rho)",
                "Pit: D_sigma_minus(rho) - i eps_P [H0,rho]",
                "Hill: -i[H_C,rho] + sum_j kappa_j(P_j rho P_j - 0.5{P_j,rho})",
            ],
            "type2": [
                "Cannon: sum_k D_Lk(rho) + i eps_F [H0,rho]",
                "Spiral: +i[H0,rho] + eps_V sum_k D_Lk(rho)",
                "Source: D_sigma_plus(rho) + i eps_P [H0,rho]",
                "Citadel: +i[H_C,rho] + sum_j kappa_j(P_j rho P_j - 0.5{P_j,rho})",
            ],
        },
        "placements": {"type1": placement_rows("type1"), "type2": placement_rows("type2")},
        "grammar_balance": balances,
        "trajectory_metrics": {"flip": flip_metrics, "no_flip_control": no_flip_metrics},
        "terrain_distinctness": {"type1": type1_terrain, "type2": type2_terrain},
        "pit_source_flow": {
            "type1_pit_terminal_z": float(pit_z),
            "type2_source_terminal_z": float(source_z),
            "opposite_signs": verdicts["pit_source_opposite_z_flow"],
        },
        "controls": {
            "same_sign_no_flip_control": "Type 2 is evaluated with s=+1/H_R=+H0-equivalent commutator sign and Source mapped to sigma_minus/Pit dynamics; this must collapse trajectories.",
            "win_lose_fence": "WIN/LOSE and win/lose are counted only as chart grammar, not as a dynamical variable.",
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
            "Type 1 and Type 2 trajectories are compared from the same rho0 under the Weyl-flipped terrain equations.",
            "The decisive no-flip control removes the Weyl sign flip and maps Source to Pit/sigma_minus dynamics; it must collapse trajectories to zero trace distance.",
            "Pit versus Source is tested as sigma_minus sink z-flow versus sigma_plus source z-flow.",
            "WIN/LOSE and win/lose labels are balanced chart grammar only, not a dynamical distinctness claim.",
        ],
        "honest_caveat": "scratch_diagnostic is used intentionally; this result is not canonical admission, promotion, Axis0, gravity, bridge, or win/lose dynamical evidence.",
        "plain_sentence": "The owner's two engines stay distinct under the Weyl-flipped terrain dynamics when C1 and C4 pass; they collapse when the no-flip control sets both engines to s=+1 and maps Source back to Pit/sigma_minus dynamics.",
    }
    result["parity"] = parity_block(result)
    result["all_pass"] = (
        bool(result["jax_x64_enabled"])
        and not bool(result["numpy_compute_used"])
        and not any(source_markers.values())
        and all(bool(v) for v in verdicts.values())
        and bool(result["parity"]["within_1e_9"])
    )
    result["stop_condition_fired"] = (
        not bool(verdicts["collapse_under_no_flip_control"])
        or bool(result["parity"]["strict_divergence_gt_1e_6"])
    )
    return result


def main() -> None:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    s = result["shared_scalars"]
    print(f"engine_noncollapse_probe jax wrote {RESULT_PATH}")
    print(
        "C1 distinct max_trace_distance={distinct} no_flip_control={control}".format(
            distinct=s["c1_flip_trajectory_max_trace_distance"],
            control=s["c1_no_flip_control_max_trace_distance"],
        )
    )
    print(
        "C4 pit_z={pit} source_z={source}".format(
            pit=s["c4_type1_pit_terminal_z"],
            source=s["c4_type2_source_terminal_z"],
        )
    )
    print(
        "terrain_min_type1={t1} terrain_min_type2={t2}".format(
            t1=s["c2_type1_min_pairwise_terrain_trace_distance"],
            t2=s["c2_type2_min_pairwise_terrain_trace_distance"],
        )
    )
    print(
        "parity_max_diff={diff} numpy_compute_used={numpy_used} jax_x64_enabled={x64}".format(
            diff=result["parity"]["parity_max_diff"],
            numpy_used=result["numpy_compute_used"],
            x64=result["jax_x64_enabled"],
        )
    )
    if result["stop_condition_fired"]:
        print("STOP_CONDITION_FIRED engine_noncollapse_probe jax")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
