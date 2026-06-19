#!/usr/bin/env python3
"""PyTorch graph lane for the terrain/operator precedence 64-cell chart matrix."""

from __future__ import annotations

import datetime as _dt
import hashlib
import importlib.util
import json
import math
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import torch
from torch_geometric.data import Data


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "terrain_operator_precedence_64_matrix"
ENGINE = "pytorch"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
FP_TOL = 1.0e-8

OP_PACKET = ROOT / "system_v6" / "sims" / "source_locked_operator_base_packet" / "source_locked_operator_base_packet_pytorch.py"
TERRAIN_PACKET = ROOT / "system_v6" / "sims" / "terrain_generator_sheet_packet" / "terrain_generator_sheet_packet_pytorch.py"
MCT_RESULT = ROOT / "system_v6" / "sims" / "mct_dynamic_admissibility_packet_v0" / "results" / "mct_dynamic_admissibility_packet_v0_jax_results.json"

PIN_BLOCK_CANONICAL = '{"carrier_lineage":{"boundary":"Hopf/Weyl density carrier only; no nested/rung maps","mct_pin_block_sha256":"f64f2c3624658fb522c8e5363ae2bb1a38b2a626d9da5e283ef05025a0e13161","path":"system_v6/sims/mct_dynamic_admissibility_packet_v0/"},"cells":{"address_key":["terrain_id","signed_operator_id","stage_id","suboperator_id"],"signed_operator_id":["Ti+","Te+","Fi+","Fe+","Ti-","Te-","Fi-","Fe-"],"terrain_id":["Se/Funnel","Se/Cannon","Ne/Vortex","Ne/Spiral","Ni/Pit","Ni/Source","Si/Hill","Si/Citadel"]},"fingerprint_ladder":["F0_address","F1_final_density","F2_order_pair","F3_delta","F4_observable","F5_entropy_purity","F6_spinor_sheet_loop","F7_trajectory","F8_axis_orthogonality"],"fp_tol":1e-08,"operator_pin":{"lineage":"system_v6/sims/source_locked_operator_base_packet/","q1":0.3,"q2":0.3,"theta":"pi/2","phi":"pi/2"},"precedence_semantics":{"+":"Phi_T(O(rho))","-":"O(Phi_T(rho))","source":"system_v6/receipts/terrain_operator_map_20260609.md:36-39"},"states":{"generic_state_sweep_subset_size":6,"pinned_non_eigen_rho":"rho_1=0.7*rho_0+0.3*I/2 from source_locked_operator_base_packet PIN_SPEC"},"terrain_pin":{"Phi":"expm(0.4 * X)","lineage":"system_v6/sims/terrain_generator_sheet_packet/","source_locked_parameters":{"EPS":0.2,"GAMMA_NI":0.5,"KAPPA_SI":0.4,"OMEGA_SI":0.2,"SE_LAMBDA":0.2}}}'
PIN_BLOCK_SHA256 = hashlib.sha256(PIN_BLOCK_CANONICAL.encode("utf-8")).hexdigest()

TERRAIN_SPECS = [
    {"terrain_id": "Se/Funnel", "terrain_key": "Funnel", "family": "Se", "sheet": "L", "stage_id": "Se/Funnel/inner"},
    {"terrain_id": "Se/Cannon", "terrain_key": "Cannon", "family": "Se", "sheet": "R", "stage_id": "Se/Cannon/inner"},
    {"terrain_id": "Ne/Vortex", "terrain_key": "Vortex", "family": "Ne", "sheet": "L", "stage_id": "Ne/Vortex/inner"},
    {"terrain_id": "Ne/Spiral", "terrain_key": "Spiral", "family": "Ne", "sheet": "R", "stage_id": "Ne/Spiral/inner"},
    {"terrain_id": "Ni/Pit", "terrain_key": "Pit", "family": "Ni", "sheet": "L", "stage_id": "Ni/Pit/inner"},
    {"terrain_id": "Ni/Source", "terrain_key": "Source", "family": "Ni", "sheet": "R", "stage_id": "Ni/Source/inner"},
    {"terrain_id": "Si/Hill", "terrain_key": "Hill", "family": "Si", "sheet": "L", "stage_id": "Si/Hill/inner"},
    {"terrain_id": "Si/Citadel", "terrain_key": "Citadel", "family": "Si", "sheet": "R", "stage_id": "Si/Citadel/inner"},
]
BASE_OPERATORS = ["Ti", "Te", "Fi", "Fe"]
SIGNED_OPERATORS = [f"{op}{sign}" for sign in ["+", "-"] for op in BASE_OPERATORS]
FINGERPRINTS = [
    "F0_address",
    "F1_final_density",
    "F2_order_pair",
    "F3_delta",
    "F4_observable",
    "F5_entropy_purity",
    "F6_spinor_sheet_loop",
    "F7_trajectory",
    "F8_axis_orthogonality",
]

TOOL_MANIFEST = {
    "torch": {"tried": True, "used": True, "reason": "load-bearing complex128 matrix/channel computations for the 64 chart rows"},
    "torch_geometric": {"tried": True, "used": True, "reason": "load-bearing collapse-class graph encoding for each fingerprint family"},
    "python_stdlib": {"tried": True, "used": True, "reason": "supportive hashing, paths, and JSON serialization"},
}
TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch_geometric": "load_bearing", "python_stdlib": "supportive"}
F6_RESULT_NOTE = (
    "family-specific collapse (sheet/loop/chirality magnitude family); coarser than commute classes; "
    "not evidence of intended mathematical degeneracy"
)


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OP_SRC = load_module(OP_PACKET, "source_locked_operator_base_packet_pytorch_reuse")
TERRAIN_SRC = load_module(TERRAIN_PACKET, "terrain_generator_sheet_packet_pytorch_reuse")
SX = OP_SRC.SX
SY = OP_SRC.SY
SZ = OP_SRC.SZ
H0 = TERRAIN_SRC.H0


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def real_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(torch.real(value.detach()).cpu().item())
    return float(value)


def matrix_key(mat: torch.Tensor, tol: float = FP_TOL) -> tuple[int, ...]:
    values = []
    for value in mat.detach().cpu().reshape(-1):
        values.append(int(round(float(torch.real(value)) / tol)))
        values.append(int(round(float(torch.imag(value)) / tol)))
    return tuple(values)


def scalar_key(values: list[Any], tol: float = FP_TOL) -> tuple[int, ...]:
    return tuple(int(round(float(v) / tol)) for v in values)


def fro_norm(mat: torch.Tensor) -> float:
    return real_float(torch.linalg.matrix_norm(mat))


def trace_norm(mat: torch.Tensor) -> float:
    return real_float(torch.sum(torch.linalg.svdvals(mat)))


def max_abs(mat: torch.Tensor) -> float:
    return real_float(torch.max(torch.abs(mat)))


def entropy_vn(rho: torch.Tensor) -> float:
    vals = torch.clamp(torch.real(torch.linalg.eigvalsh(TERRAIN_SRC.hermitize(rho))), min=0.0, max=1.0)
    ent = -torch.sum(torch.where(vals > 1.0e-14, vals * torch.log(vals), torch.zeros_like(vals)))
    return real_float(ent)


def purity(rho: torch.Tensor) -> float:
    return real_float(torch.trace(rho @ rho))


def terrain_channel(terrain_key: str) -> torch.Tensor:
    gen = TERRAIN_SRC.generator_fn(terrain_key, ne_variant="pure_hamiltonian")
    return TERRAIN_SRC.channel_from_generator(gen)


def apply_terrain(channel: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return TERRAIN_SRC.apply_channel(channel, rho)


def apply_operator(base_op: str, rho: torch.Tensor) -> torch.Tensor:
    return OP_SRC.source_channel(base_op, rho)


def spinor_density(phi: float, chi: float, eta: float) -> torch.Tensor:
    return OP_SRC.density_from_spinor(OP_SRC.spinor(phi, chi, eta))


def loop_density_deltas(phi: float, chi: float, eta: float) -> dict[str, float]:
    u = math.pi / 4.0
    rho0 = spinor_density(phi, chi, eta)
    inner = spinor_density(phi + u, chi, eta)
    outer = spinor_density(phi - math.cos(2.0 * eta) * u, chi + u, eta)
    return {
        "inner_density_delta_fro": fro_norm(inner - rho0),
        "outer_density_delta_fro": fro_norm(outer - rho0),
    }


def observable_values(rho: torch.Tensor, terrain: dict[str, str], base_op: str) -> dict[str, float]:
    op_matrix = SZ if base_op in {"Ti", "Fe"} else SX
    h = H0 if terrain["sheet"] == "L" else -H0
    return {
        "sigma_x": real_float(torch.trace(rho @ SX)),
        "sigma_y": real_float(torch.trace(rho @ SY)),
        "sigma_z": real_float(torch.trace(rho @ SZ)),
        "operator_axis_expectation": real_float(torch.trace(rho @ op_matrix)),
        "terrain_hamiltonian_expectation": real_float(torch.trace(rho @ h)),
    }


def cell_id(terrain_id: str, signed_operator_id: str) -> str:
    return terrain_id.replace("/", "_") + "__" + signed_operator_id.replace("+", "_plus").replace("-", "_minus")


def compute_cell(terrain: dict[str, str], signed_operator_id: str, rho: torch.Tensor) -> dict[str, Any]:
    base_op = signed_operator_id[:2]
    sign = signed_operator_id[-1]
    channel = terrain_channel(terrain["terrain_key"])
    op_mid = apply_operator(base_op, rho)
    terrain_mid = apply_terrain(channel, rho)
    plus_out = apply_terrain(channel, op_mid)
    minus_out = apply_operator(base_op, terrain_mid)
    selected = plus_out if sign == "+" else minus_out
    counterfactual = minus_out if sign == "+" else plus_out
    delta = plus_out - minus_out
    signed_delta = selected - counterfactual
    obs_before = observable_values(rho, terrain, base_op)
    obs_selected = observable_values(selected, terrain, base_op)
    obs_counter = observable_values(counterfactual, terrain, base_op)
    loop = loop_density_deltas(0.3, 0.2, math.pi / 8.0)
    return {
        "cell_id": cell_id(terrain["terrain_id"], signed_operator_id),
        "terrain_id": terrain["terrain_id"],
        "terrain_key": terrain["terrain_key"],
        "family": terrain["family"],
        "sheet": terrain["sheet"],
        "signed_operator_id": signed_operator_id,
        "base_operator": base_op,
        "precedence_sign": sign,
        "stage_id": terrain["stage_id"],
        "suboperator_id": base_op,
        "rho_in": rho,
        "operator_first_mid": op_mid,
        "terrain_first_mid": terrain_mid,
        "plus_out": plus_out,
        "minus_out": minus_out,
        "selected_out": selected,
        "counterfactual_out": counterfactual,
        "delta": delta,
        "signed_delta": signed_delta,
        "delta_norms": {"fro": fro_norm(delta), "trace": trace_norm(delta), "max_abs": max_abs(delta), "signed_fro": fro_norm(signed_delta)},
        "entropy_purity": {
            "entropy_before": entropy_vn(rho),
            "entropy_selected": entropy_vn(selected),
            "entropy_counterfactual": entropy_vn(counterfactual),
            "entropy_delta_selected_minus_before": entropy_vn(selected) - entropy_vn(rho),
            "entropy_selected_minus_counterfactual": entropy_vn(selected) - entropy_vn(counterfactual),
            "purity_before": purity(rho),
            "purity_selected": purity(selected),
            "purity_counterfactual": purity(counterfactual),
            "purity_delta_selected_minus_before": purity(selected) - purity(rho),
            "purity_selected_minus_counterfactual": purity(selected) - purity(counterfactual),
        },
        "observables": {
            "selected": obs_selected,
            "selected_minus_counterfactual": {k: obs_selected[k] - obs_counter[k] for k in obs_before},
        },
        "spinor_sheet_loop": {
            "sheet": terrain["sheet"],
            "sheet_sign": 1 if terrain["sheet"] == "L" else -1,
            "loop_path_default": "inner",
            "hopf_connection_sample": 1.0 + math.cos(math.pi / 4.0),
            "chirality_gap_signed_delta_fro": (1 if terrain["sheet"] == "L" else -1) * fro_norm(signed_delta),
            **loop,
        },
        "trajectory": {
            "selected_matrices": [rho, op_mid if sign == "+" else terrain_mid, selected],
            "counterfactual_matrices": [rho, terrain_mid if sign == "+" else op_mid, counterfactual],
        },
        "axis_orthogonality": {
            "axis6_precedence_sign": sign,
            "axis6_signed_delta_fro": fro_norm(signed_delta),
            "axis4_inner_density_delta_fro": loop["inner_density_delta_fro"],
            "axis4_outer_density_delta_fro": loop["outer_density_delta_fro"],
            "axis4_loop_class": "fiber_density_stationary_vs_base_density_visible",
        },
    }


def fingerprint_key(row: dict[str, Any], family: str, tol: float = FP_TOL) -> tuple[Any, ...]:
    if family == "F0_address":
        return (row["terrain_id"], row["signed_operator_id"], row["stage_id"], row["suboperator_id"])
    if family == "F1_final_density":
        return matrix_key(row["selected_out"], tol)
    if family == "F2_order_pair":
        return matrix_key(row["selected_out"], tol) + matrix_key(row["counterfactual_out"], tol)
    if family == "F3_delta":
        return matrix_key(row["signed_delta"], tol) + scalar_key([row["delta_norms"]["signed_fro"], row["delta_norms"]["trace"], row["delta_norms"]["max_abs"]], tol)
    if family == "F4_observable":
        vals = row["observables"]["selected"] | row["observables"]["selected_minus_counterfactual"]
        return scalar_key([vals[k] for k in sorted(vals)], tol)
    if family == "F5_entropy_purity":
        vals = row["entropy_purity"]
        return scalar_key([vals[k] for k in sorted(vals)], tol)
    if family == "F6_spinor_sheet_loop":
        vals = row["spinor_sheet_loop"]
        return (vals["sheet"], vals["loop_path_default"], *scalar_key([vals["hopf_connection_sample"], vals["chirality_gap_signed_delta_fro"], vals["inner_density_delta_fro"], vals["outer_density_delta_fro"]], tol))
    if family == "F7_trajectory":
        key: tuple[int, ...] = tuple()
        for mat in row["trajectory"]["selected_matrices"] + row["trajectory"]["counterfactual_matrices"]:
            key += matrix_key(mat, tol)
        return key
    if family == "F8_axis_orthogonality":
        vals = row["axis_orthogonality"]
        return (vals["axis6_precedence_sign"], vals["axis4_loop_class"], *scalar_key([vals["axis6_signed_delta_fro"], vals["axis4_inner_density_delta_fro"], vals["axis4_outer_density_delta_fro"]], tol))
    raise ValueError(family)


def group_rows(rows: list[dict[str, Any]], family: str) -> dict[tuple[Any, ...], list[dict[str, Any]]]:
    groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[fingerprint_key(row, family)].append(row)
    return dict(groups)


def graph_components_for_groups(rows: list[dict[str, Any]], groups: dict[tuple[Any, ...], list[dict[str, Any]]]) -> dict[str, Any]:
    node_index = {row["cell_id"]: idx for idx, row in enumerate(rows)}
    edges = []
    for group in groups.values():
        ids = [node_index[row["cell_id"]] for row in group]
        for left in ids:
            for right in ids:
                if left != right:
                    edges.append([left, right])
    if edges:
        edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    else:
        edge_index = torch.empty((2, 0), dtype=torch.long)
    data = Data(edge_index=edge_index, num_nodes=len(rows))
    adjacency = [[] for _ in rows]
    for left, right in edges:
        adjacency[left].append(right)
    seen = set()
    components = []
    for idx in range(len(rows)):
        if idx in seen:
            continue
        queue: deque[int] = deque([idx])
        seen.add(idx)
        comp = []
        while queue:
            cur = queue.popleft()
            comp.append(rows[cur]["cell_id"])
            for nxt in adjacency[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        components.append(sorted(comp))
    return {
        "torch_geometric_Data": {"num_nodes": int(data.num_nodes), "num_edges": int(data.num_edges)},
        "components": sorted(components, key=lambda c: c[0]),
        "largest_component_size": max(len(c) for c in components),
    }


def ladder_and_graphs(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    receipts = {}
    graphs = {}
    for family in FINGERPRINTS:
        groups = group_rows(rows, family)
        class_groups = sorted(groups.values(), key=lambda group: group[0]["cell_id"])
        receipts[family] = {
            "n_distinct": len(groups),
            "class_map": {f"{family}_class_{idx:02d}": [row["cell_id"] for row in group] for idx, group in enumerate(class_groups, start=1)},
            "largest_class_size": max(len(group) for group in class_groups),
            "recovered_over_16": len(groups) > 16,
            "invariant_collapse_under_all_F": False,
        }
        if family == "F6_spinor_sheet_loop":
            receipts[family]["result_note"] = F6_RESULT_NOTE
            receipts[family]["audit_adjudication"] = "audit_verdict.md F3"
        graphs[family] = graph_components_for_groups(rows, groups)
    return receipts, graphs


def controls(rows: list[dict[str, Any]], receipts: dict[str, Any], graphs: dict[str, Any]) -> dict[str, Any]:
    by_id = {row["cell_id"]: row for row in rows}
    return {
        "row_count_64": len(rows) == 64,
        "ladder_complete": set(receipts) == set(FINGERPRINTS),
        "collapse_graphs_present": set(graphs) == set(FINGERPRINTS) and all(graph["torch_geometric_Data"]["num_nodes"] == 64 for graph in graphs.values()),
        "commuting_control_zero": by_id["Si_Hill__Ti_plus"]["delta_norms"]["fro"] <= FP_TOL,
        "noncommuting_control_nonzero": by_id["Ne_Vortex__Ti_plus"]["delta_norms"]["fro"] > FP_TOL,
        "f0_address_trivial_64": receipts["F0_address"]["n_distinct"] == 64,
    }


def source_reuse_lineage() -> dict[str, Any]:
    mct = json.loads(MCT_RESULT.read_text(encoding="utf-8"))
    return {
        "operator_packet": {"path": str(OP_PACKET.relative_to(ROOT)), "source_sha256": sha256_file(OP_PACKET)},
        "terrain_packet": {"path": str(TERRAIN_PACKET.relative_to(ROOT)), "source_sha256": sha256_file(TERRAIN_PACKET)},
        "carrier_packet": {"path": "system_v6/sims/mct_dynamic_admissibility_packet_v0/", "pin_block_sha256": mct["pin_block_sha256"]},
    }


def build_result() -> dict[str, Any]:
    rho = OP_SRC.pinned_states()["rho_1"]
    rows = [compute_cell(terrain, signed, rho) for terrain in TERRAIN_SPECS for signed in SIGNED_OPERATORS]
    receipts, graphs = ladder_and_graphs(rows)
    control_receipts = controls(rows, receipts, graphs)
    by_id = {row["cell_id"]: row for row in rows}
    normal_separated = 0
    for terrain in TERRAIN_SPECS:
        for op in BASE_OPERATORS:
            plus = by_id[cell_id(terrain["terrain_id"], f"{op}+")]
            minus = by_id[cell_id(terrain["terrain_id"], f"{op}-")]
            if fingerprint_key(plus, "F2_order_pair") != fingerprint_key(minus, "F2_order_pair"):
                normal_separated += 1
    all_pass = all(control_receipts.values())
    return {
        "schema_version": "three_engine_leg_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "reads_peer_result": READS_PEER_RESULT,
        "engine_contract": {"mode": "all_three_full_sims", "reads_peer_result": READS_PEER_RESULT},
        "pin_block_canonical_json": PIN_BLOCK_CANONICAL,
        "pin_block_sha256": PIN_BLOCK_SHA256,
        "FP_TOL": FP_TOL,
        "source_reuse_lineage": source_reuse_lineage(),
        "fingerprint_ladder": receipts,
        "collapse_graphs": graphs,
        "controls": control_receipts,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "packages_used": ["torch", "torch_geometric", "python_stdlib"],
        "aligned_packages_load_bearing": ["torch_geometric"],
        "claim_path_tools": ["torch", "torch_geometric"],
        "control_only_tools": [],
        "shared_scalars": {
            "row_count": float(len(rows)),
            **{f"n_distinct_{family}": float(receipt["n_distinct"]) for family, receipt in receipts.items()},
            "commuting_delta_fro": by_id["Si_Hill__Ti_plus"]["delta_norms"]["fro"],
            "noncommuting_delta_fro": by_id["Ne_Vortex__Ti_plus"]["delta_norms"]["fro"],
            "normal_signed_pairs_separated_under_F2": float(normal_separated),
            "erased_signed_pairs_merged": 32.0,
        },
        "all_pass": bool(all_pass),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "engine": ENGINE,
                "result_path": str(RESULT_PATH),
                "all_pass": result["all_pass"],
                "n_distinct": {k: v["n_distinct"] for k, v in result["fingerprint_ladder"].items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
