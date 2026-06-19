#!/usr/bin/env python3
"""PyTorch leg -- autograd machinery (scoped, not the semantic arbiter).

Computation style UNIQUE to this leg: torch.autograd over the Bloch parameters.
  - builds rho(theta) = (I + theta_x X + theta_y Y + theta_z Z)/2 from leaf tensors
  - computes probe expectations tr(rho(theta) P) through the autograd graph
  - uses torch.autograd.grad to obtain the JACOBIAN d<P>/d theta and verifies the
    structural identity d tr(rho P)/d r_Q = delta_{P,Q} (the expectation is linear
    in the matching Bloch component, zero in the others) -- a derivative no other
    leg computes.
It does NOT call the Julia or JAX legs and does NOT read their results.
"""

import json
import os
from datetime import datetime, timezone

import torch

torch.set_default_dtype(torch.float64)

SIM_ID = "distinguishability_quotient_floor_v0"
HERE = os.path.dirname(os.path.abspath(__file__))

X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
I2 = torch.eye(2, dtype=torch.complex128)
PROBE_MATS = {"X": X, "Y": Y, "Z": Z}


def sha256_of(path):
    import hashlib

    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rho_of(theta):
    # theta: real tensor (3,) requiring grad; cast into complex matrix
    tc = theta.to(torch.complex128)
    return (I2 + tc[0] * X + tc[1] * Y + tc[2] * Z) / 2


def expectation(theta, P):
    return torch.real(torch.trace(rho_of(theta) @ P))


def main():
    with open(os.path.join(HERE, "spec.json")) as f:
        spec = json.load(f)
    bvs = spec["bloch_vectors_rational"]
    full = spec["probe_family_full"]
    erased = spec["probe_family_erased"]
    labels = sorted(bvs.keys())

    exp_full = {}
    exp_erased = {}
    # autograd Jacobian for one representative state (s1): d<P>/d theta
    jac_state = "s1"
    jacobian = {}

    for lab in labels:
        b = bvs[lab]
        theta = torch.tensor(
            [b["rx"][0] / b["rx"][1], b["ry"][0] / b["ry"][1], b["rz"][0] / b["rz"][1]],
            dtype=torch.float64,
            requires_grad=True,
        )
        ef = []
        for p in full:
            val = expectation(theta, PROBE_MATS[p])
            ef.append(round(float(val.detach()), 9))
            if lab == jac_state:
                (grad,) = torch.autograd.grad(val, theta, retain_graph=True, create_graph=False)
                jacobian[p] = [round(float(g), 9) for g in grad]
        exp_full[lab] = ef
        exp_erased[lab] = [round(float(expectation(theta, PROBE_MATS[p]).detach()), 9) for p in erased]

    # structural identity check: jacobian must be the identity selection
    # d tr(rho P)/d r_Q = 1 if P==Q else 0
    probe_index = {p: i for i, p in enumerate(full)}
    jac_identity_ok = True
    for p in full:
        for q in full:
            expected = 1.0 if p == q else 0.0
            got = jacobian[p][probe_index[q]]
            if abs(got - expected) > 1e-9:
                jac_identity_ok = False

    def quotient(expmap):
        classes, keys = [], []
        for lab in labels:
            key = tuple(expmap[lab])
            if key in keys:
                classes[keys.index(key)].append(lab)
            else:
                keys.append(key)
                classes.append([lab])
        return classes

    q_full = quotient(exp_full)
    q_erased = quotient(exp_erased)

    result = {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "engine": "pytorch",
        "computation_style": "autograd_jacobian_over_bloch_parameters",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "does_not_self_upgrade": True,
        "reads_peer_result": False,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": sha256_of(os.path.abspath(__file__)),
        "result_path": f"system_v7/sims/{SIM_ID}/results/{SIM_ID}_pytorch_results.json",
        "finite_set_size": len(labels),
        "state_labels": labels,
        "probe_expectations_full": exp_full,
        "probe_expectations_erased": exp_erased,
        "quotient_classes_full": q_full,
        "quotient_class_count_full": len(q_full),
        "quotient_classes_erased": q_erased,
        "quotient_class_count_erased": len(q_erased),
        "flip_pair": spec["flip_pair"],
        "autograd_receipt": {
            "jacobian_state": jac_state,
            "jacobian_dExp_dBloch": jacobian,
            "structural_identity": "d tr(rho P)/d r_Q = delta_{P,Q}",
            "jacobian_is_identity_selection": jac_identity_ok,
            "note": "autograd computes a derivative the eigendecomposition and vmap legs do not; it confirms the expectation is exactly linear in the matching Bloch component.",
        },
        "package_versions": {"torch": torch.__version__},
        "packages_used": ["torch"],
        "aligned_packages_load_bearing": ["torch"],
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "load-bearing autograd Jacobian d<P>/d(Bloch) verifying the linear-expectation structural identity"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
    }

    out = os.path.join(HERE, "results", f"{SIM_ID}_pytorch_results.json")
    with open(out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"pytorch leg wrote {out}")
    print(f"  jacobian identity ok: {jac_identity_ok}")
    print(f"  quotient classes full={len(q_full)} erased={len(q_erased)}")


if __name__ == "__main__":
    main()
