#!/usr/bin/env python3
"""PyTorch/geomstats/e3nn leg for the SO(3)-vs-SU(2) S1 discriminator."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any

import geomstats.backend as gs
import sympy as sp
import torch
from e3nn import o3
from geomstats.geometry.special_orthogonal import SpecialOrthogonal


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s1_vector_vs_spinor_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
PIN_SPEC = (
    "geo_s1_vector_vs_spinor_v0|routes=SO3_vector_vs_SU2_spinor|"
    "U(theta)=diag(exp(-i theta/2),exp(i theta/2))|R(theta)=Rz(theta)|"
    "density_quotient=psi psi_dagger|compare_2pi_4pi|"
    "classification=scratch_diagnostic|promotion_allowed=false"
)

TOOL_MANIFEST = {
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SO(3) manifold distance check with torch backend",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing vector irrep return/equivariance boundary receipt",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact sign quotient symbolic control",
    },
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor substrate for geomstats and spinor/density norms",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "sympy": "load_bearing",
    "torch": "supportive",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def so3_z(theta: torch.Tensor) -> torch.Tensor:
    c = torch.cos(theta)
    s = torch.sin(theta)
    z = torch.zeros((), dtype=torch.float64)
    one = torch.ones((), dtype=torch.float64)
    return torch.stack(
        [
            torch.stack([c, -s, z]),
            torch.stack([s, c, z]),
            torch.stack([z, z, one]),
        ]
    )


def su2_z(theta: torch.Tensor) -> torch.Tensor:
    c = torch.cos(theta / 2)
    s = torch.sin(theta / 2)
    return torch.stack(
        [
            torch.stack([torch.complex(c, -s), torch.tensor(0.0 + 0.0j, dtype=torch.complex128)]),
            torch.stack([torch.tensor(0.0 + 0.0j, dtype=torch.complex128), torch.complex(c, s)]),
        ]
    )


def sympy_density_control() -> dict[str, Any]:
    a, b = sp.symbols("a b", real=True)
    psi = sp.Matrix([a + sp.I * b, 0])
    rho = psi * psi.conjugate().T
    minus_rho = (-psi) * (-psi).conjugate().T
    diff = sp.simplify(rho - minus_rho)
    return {
        "density_difference": [[sp.sstr(sp.simplify(diff[i, j])) for j in range(2)] for i in range(2)],
        "pass": all(sp.simplify(item) == 0 for item in diff),
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    torch.set_default_dtype(torch.float64)
    so3 = SpecialOrthogonal(n=3, point_type="matrix")
    identity = torch.eye(3, dtype=torch.float64)
    r2 = so3_z(torch.tensor(2.0 * torch.pi, dtype=torch.float64))
    r4 = so3_z(torch.tensor(4.0 * torch.pi, dtype=torch.float64))
    so3_distance_2pi = float(so3.metric.dist(identity, r2))
    so3_distance_4pi = float(so3.metric.dist(identity, r4))

    u2 = su2_z(torch.tensor(2.0 * torch.pi, dtype=torch.float64))
    u4 = su2_z(torch.tensor(4.0 * torch.pi, dtype=torch.float64))
    i2 = torch.eye(2, dtype=torch.complex128)
    su2_distance_2pi_to_identity = float(torch.linalg.norm(u2 - i2).real)
    su2_distance_2pi_to_minus_identity = float(torch.linalg.norm(u2 + i2).real)
    su2_distance_4pi_to_identity = float(torch.linalg.norm(u4 - i2).real)

    vector_irreps = o3.Irreps("1e")
    vector_irrep = o3.Irrep("1e")
    d0 = vector_irrep.D_from_angles(torch.tensor(0.0), torch.tensor(0.0), torch.tensor(0.0))
    d2 = vector_irrep.D_from_angles(torch.tensor(0.0), torch.tensor(0.0), torch.tensor(2.0 * torch.pi))
    d4 = vector_irrep.D_from_angles(torch.tensor(0.0), torch.tensor(0.0), torch.tensor(4.0 * torch.pi))
    e3nn_distance_2pi = float(torch.linalg.norm(d2 - d0))
    e3nn_distance_4pi = float(torch.linalg.norm(d4 - d0))
    try:
        o3.Irrep("1/2e")
        half_integer_rejected = False
        half_integer_error = None
    except Exception as exc:  # e3nn vector irreps intentionally reject half-integer spinors.
        half_integer_rejected = True
        half_integer_error = f"{type(exc).__name__}: {exc}"

    psi = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=torch.complex128)
    minus_psi = -psi
    rho = torch.outer(psi, psi.conj())
    minus_rho = torch.outer(minus_psi, minus_psi.conj())
    spinor_distance = float(torch.linalg.norm(psi - minus_psi).real)
    density_distance = float(torch.linalg.norm(rho - minus_rho).real)
    density_symbolic = sympy_density_control()

    receipts = {
        "geomstats_SO3_return": {
            "backend": gs.__name__,
            "object": "geomstats.geometry.special_orthogonal.SpecialOrthogonal(n=3, point_type='matrix')",
            "distance_identity_to_R_2pi": so3_distance_2pi,
            "distance_identity_to_R_4pi": so3_distance_4pi,
            "pass": so3_distance_2pi < 1e-12 and so3_distance_4pi < 1e-12,
        },
        "e3nn_vector_irrep_boundary": {
            "irreps": str(vector_irreps),
            "irrep": str(vector_irrep),
            "D_2pi_minus_D_0_norm": e3nn_distance_2pi,
            "D_4pi_minus_D_0_norm": e3nn_distance_4pi,
            "half_integer_spinor_irrep_rejected": half_integer_rejected,
            "half_integer_spinor_irrep_error": half_integer_error,
            "interpretation": "e3nn o3 vector irreps certify the vector/SO(3) route and do not carry SU(2) spinor sign data",
            "pass": e3nn_distance_2pi < 1e-12 and half_integer_rejected,
        },
        "torch_spinor_density_quotient": {
            "spinor_norm_difference_psi_minus_psi": spinor_distance,
            "density_norm_difference": density_distance,
            "sympy_density_control": density_symbolic,
            "pass": spinor_distance > 1.0 and density_distance < 1e-12 and density_symbolic["pass"],
        },
        "torch_SU2_return": {
            "distance_U_2pi_to_identity": su2_distance_2pi_to_identity,
            "distance_U_2pi_to_minus_identity": su2_distance_2pi_to_minus_identity,
            "distance_U_4pi_to_identity": su2_distance_4pi_to_identity,
            "pass": su2_distance_2pi_to_identity > 1.0
            and su2_distance_2pi_to_minus_identity < 1e-12
            and su2_distance_4pi_to_identity < 1e-12,
        },
    }
    all_pass = all(receipt["pass"] for receipt in receipts.values())
    payload = {
        "schema_version": f"{SIM_ID}_leg_v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "role_id": "pytorch_graph_network_sim_builder",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "packages_used": ["torch", "geomstats", "e3nn", "sympy"],
        "aligned_packages_load_bearing": ["geomstats", "e3nn", "sympy"],
        "claim_path_tools": ["geomstats", "e3nn", "sympy"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "route_receipts": receipts,
        "shared_scalars": {
            "so3_2pi_distance": so3_distance_2pi,
            "su2_2pi_identity_distance": su2_distance_2pi_to_identity,
            "su2_4pi_identity_distance": su2_distance_4pi_to_identity,
            "density_quotient_sign_distance": density_distance,
            "u_minus_u_rotation_distance": 0.0,
        },
        "controls": {
            "half_integer_irrep_rejection_control": {
                "pass": half_integer_rejected,
                "error": half_integer_error,
            },
        },
        "all_pass": all_pass,
    }
    RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": all_pass, "engine": "pytorch", "result_path": str(RESULT_PATH)}, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
