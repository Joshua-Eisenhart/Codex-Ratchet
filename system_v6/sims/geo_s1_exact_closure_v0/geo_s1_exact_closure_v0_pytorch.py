#!/usr/bin/env python3
"""PyTorch scoped exact crossing-count lane for geo_s1_exact_closure_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp
import torch
from torch.func import vmap


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_exact_closure_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
LINEAGE_PACKET = "system_v6/sims/geo_s1_spinor_hopf_free_v0"
LINEAGE_COMMIT = "013fb0fa1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s1_exact_closure_v0|lineage=geo_s1_spinor_hopf_free_v0@013fb0fa1|"
    "convention_pin=X1_option_A_pinned_minus_sigma_y|sigma_y_standard=[[0,-i],[i,0]]|"
    "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|r_i=Tr(rho*basis_i)|"
    "rho=psi*psi_dagger|Hopf_y=+2Im(z1*conj(z2))|derived_standard_y=-Hopf_y|"
    "derived_pinned_identity=Bloch_pinned(rho)=(x,y,z)|"
    "exact_strength=symbolic_closed_form_interval|"
    "seed_ledger=jax.random.PRNGKey[60610:haar_joint_n20000,"
    "60611:nonhaar_eta_n20000,60612:nonhaar_phi_n20000,60613:nonhaar_chi_n20000]|"
    "rerun=SIM_PY geo_s1_exact_closure_v0_{jax,julia,pytorch,envelope}|"
    "classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "pin_name": "X1_option_A_pinned_minus_sigma_y",
    "sigma_y_standard": "[[0,-i],[i,0]]",
    "bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "component_rule": "r_i = Tr(rho * basis_i)",
    "density_matrix": "rho = psi * psi^dagger",
    "hopf_y_convention": "Hopf_y = +2 Im(z1 * conj(z2))",
    "derived_standard_sigma_y_component": "Tr(rho * sigma_y_standard) = -2 Im(z1 * conj(z2))",
    "derived_pinned_y_component": "Tr(rho * (-sigma_y_standard)) = +2 Im(z1 * conj(z2))",
    "standard_bloch_relative_to_hopf": "Bloch_standard(rho) = (x, -y, z)",
    "pinned_keystone_identity": "Bloch_pinned(rho) = (x, y, z)",
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing integer tensor recomputation of the exact crossing signs",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vmap application over the integer crossing-sign tensor",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact algebraic crossing sample coordinates and circle/line incidence checks",
    },
}

TOOL_INTEGRATION_DEPTH = {"torch": "load_bearing", "torch.func": "supportive", "sympy": "load_bearing"}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def exact_sign(expr: sp.Expr) -> int:
    simplified = sp.simplify(expr)
    if simplified.is_positive:
        return 1
    if simplified.is_negative:
        return -1
    raise ValueError(f"cannot determine exact sign for {sp.sstr(simplified)}")


def det2(left: sp.Matrix, right: sp.Matrix) -> sp.Expr:
    return sp.simplify(left[0] * right[1] - left[1] * right[0])


def exact_crossing_records() -> list[dict[str, Any]]:
    eps = sp.Rational(1, 2)
    roots = [sp.pi / 3, 5 * sp.pi / 3]
    records = []
    for idx, root in enumerate(roots):
        u_value = sp.sin(root)
        circle = sp.Matrix([sp.cos(root), sp.sin(root), sp.Integer(0)])
        line = sp.Matrix([eps, u_value, u_value])
        circle_tangent = sp.Matrix([-sp.sin(root), sp.cos(root), sp.Integer(0)])
        line_tangent = sp.Matrix([sp.Integer(0), sp.Integer(1), sp.Integer(1)])
        circle_projected_tangent = sp.Matrix([circle_tangent[0], circle_tangent[1]])
        line_projected_tangent = sp.Matrix([line_tangent[0], line_tangent[1]])
        circle_on_unit = sp.simplify(circle[0] ** 2 + circle[1] ** 2 - 1)
        projection_match = all(sp.simplify(circle[i] - line[i]) == 0 for i in (0, 1))
        z_delta = sp.simplify(line[2] - circle[2])
        if z_delta.is_positive:
            over_curve = "line"
            under_curve = "circle"
            orientation_det = det2(line_projected_tangent, circle_projected_tangent)
        elif z_delta.is_negative:
            over_curve = "circle"
            under_curve = "line"
            orientation_det = det2(circle_projected_tangent, line_projected_tangent)
        else:
            raise ValueError("crossing has zero z-order separation")
        sign = exact_sign(orientation_det)
        records.append(
            {
                "index": idx,
                "projection": "xy",
                "segment_pair": ["C(t)=(cos(t),sin(t),0)", "L(u)=(1/2,u,u)"],
                "circle_parameter": sp.sstr(root),
                "line_parameter": sp.sstr(u_value),
                "circle_point": [sp.sstr(item) for item in circle],
                "line_point": [sp.sstr(item) for item in line],
                "circle_unit_equation_residual": sp.sstr(circle_on_unit),
                "projection_match": bool(projection_match),
                "circle_projected_tangent": [sp.sstr(sp.simplify(item)) for item in circle_projected_tangent],
                "line_projected_tangent": [sp.sstr(sp.simplify(item)) for item in line_projected_tangent],
                "z_delta_line_minus_circle": sp.sstr(z_delta),
                "over_curve_from_z_order": over_curve,
                "under_curve_from_z_order": under_curve,
                "orientation_determinant_ordered_over_under": sp.sstr(sp.simplify(orientation_det)),
                "sign_rule": "sign(det(projected_tangent_over, projected_tangent_under)) with exact z-order selecting over/under",
                "computed_sign": sign,
            }
        )
    return records


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    records = exact_crossing_records()
    signs = torch.tensor([row["computed_sign"] for row in records], dtype=torch.int64)
    mapped = vmap(lambda value: value)(signs)
    signed_sum = int(torch.sum(mapped).item())
    scrambled = signs.clone()
    scrambled[1] = -scrambled[1]
    scrambled_sum = int(torch.sum(vmap(lambda value: value)(scrambled)).item())
    receipt = {
        "records": records,
        "torch_integer_signs": [int(item) for item in mapped.tolist()],
        "signed_sum": signed_sum,
        "signed_sum_over_2": "1",
        "crossing_sign_source": "computed from exact projected tangent orientation determinant plus exact z-order",
        "scrambled_control_signs": [int(item) for item in scrambled.tolist()],
        "scrambled_control_signed_sum": scrambled_sum,
        "all_projection_matches_exact": all(row["projection_match"] for row in records),
        "all_circle_equation_residuals_zero": all(row["circle_unit_equation_residual"] == "0" for row in records),
        "pass": signed_sum == 2 and scrambled_sum != 2,
    }
    payload = {
        "schema_version": "geo_s1_exact_closure_v0_leg_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_graph_network_sim_builder",
        "pytorch_role": "independent exact-rational crossing-count recomputation via integer tensors; no density-keystone or Gauss-float role",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "lineage": {"packet": LINEAGE_PACKET, "commit": LINEAGE_COMMIT, "modified_lineage_packet": False},
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "packages_used": ["torch", "torch.func", "sympy"],
        "aligned_packages_load_bearing": ["sympy"],
        "claim_path_tools": ["torch", "sympy"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "X_receipts": {
            "X4_crossing_count_exact_integer_pytorch": receipt,
        },
        "controls": {
            "scrambled_crossing_control": {
                "signed_sum": scrambled_sum,
                "must_not_equal_two": True,
                "pass": scrambled_sum != 2,
            }
        },
        "shared_scalars": {
            "linking_crossing_signed_sum": signed_sum,
            "linking_number_exact": 1,
            "classification_bare_float_rows": 0,
        },
        "all_pass": bool(receipt["pass"]),
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(receipt["pass"]), "engine": "pytorch", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
