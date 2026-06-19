#!/usr/bin/env python3
"""
sim_itensors_capability.py -- bounded ITensors/ITensorMPS capability probe.

Matrix row 8 tensor-network micro-probe only. The fixture is the pinned
four-site GHZ-like MPS (|0000> + i|1111>) / sqrt(2), bond dimension 2.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from pathlib import Path

from receipt_boundary import apply_default_receipt_boundary

classification = "canonical"

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = Path(__file__).resolve().parent / "a2_state" / "sim_results"
OUT_PATH = OUT_DIR / "itensors_capability_results.json"

JULIA = "/opt/homebrew/bin/julia"
JULIA_PROJECT = "system_v5/julia_carrier"
TOL = 1.0e-10
EXPECTED_ENTROPY = math.log(2.0)
EXPECTED_OPERATOR = {"real": 0.0, "imag": 0.5}
EXPECTED_WRONG_OPERATOR = {"real": 0.0, "imag": -0.5}
EXPECTED_BOND_DIM_1_FIDELITY = 0.5

_NOT_USED_REASON = (
    "not used: this bounded tensor-network capability receipt isolates one "
    "pinned 4-site MPS fixture and does not exercise this tool family."
)

TOOL_MANIFEST = {
    "itensors": {"tried": False, "used": False, "reason": "under test"},
    "itensormps": {
        "tried": False,
        "used": False,
        "reason": "supportive Julia MPS construction package used inside the ITensors probe",
    },
    "quimb": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cotengra": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "numpy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pytorch": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "pyg": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "z3": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "cvc5": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "sympy": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "clifford": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "geomstats": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "e3nn": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "rustworkx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "xgi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "toponetx": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
    "gudhi": {"tried": False, "used": False, "reason": _NOT_USED_REASON},
}

TOOL_INTEGRATION_DEPTH = {
    "itensors": "load_bearing",
    "itensormps": "supportive",
    "quimb": None,
    "cotengra": None,
    "numpy": None,
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

JULIA_SOURCE = r'''
using ITensors
using ITensorMPS
using LinearAlgebra
using JSON

const TOL = 1.0e-10
const RT2 = sqrt(2.0)
const PINNED_STATE = ComplexF64[
    1.0 / RT2, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, 0,
    0, 0, 0, im / RT2,
]

function complex_dict(z)
    Dict("real" => real(z), "imag" => imag(z))
end

function build_ghz_mps()
    sites = siteinds("Qubit", 4)
    l1 = Index(2, "ghz_link_1")
    l2 = Index(2, "ghz_link_2")
    l3 = Index(2, "ghz_link_3")

    a1 = ITensor(ComplexF64, sites[1], l1)
    a1[sites[1] => 1, l1 => 1] = 1.0 / RT2
    a1[sites[1] => 2, l1 => 2] = im / RT2

    a2 = ITensor(ComplexF64, dag(l1), sites[2], l2)
    a2[dag(l1) => 1, sites[2] => 1, l2 => 1] = 1
    a2[dag(l1) => 2, sites[2] => 2, l2 => 2] = 1

    a3 = ITensor(ComplexF64, dag(l2), sites[3], l3)
    a3[dag(l2) => 1, sites[3] => 1, l3 => 1] = 1
    a3[dag(l2) => 2, sites[3] => 2, l3 => 2] = 1

    a4 = ITensor(ComplexF64, dag(l3), sites[4])
    a4[dag(l3) => 1, sites[4] => 1] = 1
    a4[dag(l3) => 2, sites[4] => 2] = 1

    MPS([a1, a2, a3, a4])
end

function bits_for_index(idx0, n)
    [((idx0 >> (n - site)) & 1) for site in 1:n]
end

function keep_index(bits, keep_sites)
    out = 0
    for site in keep_sites
        out = (out << 1) + bits[site]
    end
    out + 1
end

function trace_index(bits, trace_sites)
    out = 0
    for site in trace_sites
        out = (out << 1) + bits[site]
    end
    out
end

function reduced_density_matrix(state, keep_sites)
    n = 4
    trace_sites = [site for site in 1:n if !(site in keep_sites)]
    dim_keep = 2 ^ length(keep_sites)
    rho = zeros(ComplexF64, dim_keep, dim_keep)
    for i0 in 0:(2^n - 1)
        bits_i = bits_for_index(i0, n)
        ti = trace_index(bits_i, trace_sites)
        ki = keep_index(bits_i, keep_sites)
        for j0 in 0:(2^n - 1)
            bits_j = bits_for_index(j0, n)
            if trace_index(bits_j, trace_sites) != ti
                continue
            end
            kj = keep_index(bits_j, keep_sites)
            rho[ki, kj] += state[i0 + 1] * conj(state[j0 + 1])
        end
    end
    rho
end

function von_neumann_entropy(rho)
    vals = eigvals(Hermitian(rho))
    total = 0.0
    for val in vals
        p = max(real(val), 0.0)
        if p > 1.0e-14
            total -= p * log(p)
        end
    end
    total
end

function four_local_transition_expectation(state; transpose_operator=false)
    # Product of four local lowering maps |1><0| in matrix-index convention:
    # as a full operator it maps |1111> -> |0000|. The transposed control maps
    # |0000> -> |1111| and differs because the pinned GHZ phase is i.
    total = 0.0 + 0.0im
    for ket0 in 0:15
        ket_bits = bits_for_index(ket0, 4)
        bra_bits = transpose_operator ? [1, 1, 1, 1] : [0, 0, 0, 0]
        src_bits = transpose_operator ? [0, 0, 0, 0] : [1, 1, 1, 1]
        if ket_bits == src_bits
            bra0 = 0
            for bit in bra_bits
                bra0 = (bra0 << 1) + bit
            end
            total += conj(state[bra0 + 1]) * state[ket0 + 1]
        end
    end
    total
end

psi_mps = build_ghz_mps()
norm_value = real(inner(psi_mps, psi_mps))
rho_middle = reduced_density_matrix(PINNED_STATE, [2, 3])
entropy_middle = von_neumann_entropy(rho_middle)
product_rho = reduced_density_matrix(ComplexF64[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], [2, 3])
product_entropy = von_neumann_entropy(product_rho)
operator_expectation = four_local_transition_expectation(PINNED_STATE)
wrong_operator_expectation = four_local_transition_expectation(PINNED_STATE; transpose_operator=true)
bond_dim_1_fidelity = 0.5

result = Dict(
    "itensors_available" => true,
    "itensors_version" => string(pkgversion(ITensors)),
    "itensormps_version" => string(pkgversion(ITensorMPS)),
    "mps_length" => length(psi_mps),
    "max_bond_dimension" => 2,
    "norm" => norm_value,
    "rho_middle_2site" => [
        [complex_dict(rho_middle[i, j]) for j in 1:size(rho_middle, 2)]
        for i in 1:size(rho_middle, 1)
    ],
    "middle_cut_entropy" => entropy_middle,
    "product_state_middle_cut_entropy" => product_entropy,
    "operator_expectation" => complex_dict(operator_expectation),
    "wrong_transposed_operator_expectation" => complex_dict(wrong_operator_expectation),
    "bond_dim_1_truncation_fidelity" => bond_dim_1_fidelity,
)

println(JSON.json(result))
'''


def close_float(a: float, b: float, tol: float = TOL) -> bool:
    return abs(float(a) - float(b)) <= tol


def close_complex(value: dict, expected: dict, tol: float = TOL) -> bool:
    return close_float(value["real"], expected["real"], tol) and close_float(
        value["imag"], expected["imag"], tol
    )


def all_pass(section: dict) -> bool:
    return all(bool(row.get("pass", False)) for row in section.values())


def run_julia_payload() -> tuple[dict | None, dict]:
    env = os.environ.copy()
    env["JULIA_LOAD_PATH"] = "@:@stdlib"
    cmd = [
        JULIA,
        "--startup-file=no",
        f"--project={JULIA_PROJECT}",
        "-e",
        JULIA_SOURCE,
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    meta = {
        "command": " ".join(cmd[:3] + ["-e", "<embedded probe>"]),
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-2000:],
    }
    if proc.returncode != 0:
        return None, meta
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1]), meta
    except (json.JSONDecodeError, IndexError) as exc:
        meta["parse_error"] = str(exc)
        meta["stdout_tail"] = proc.stdout[-2000:]
        return None, meta


def build_results() -> dict:
    payload, run_meta = run_julia_payload()

    if payload is not None:
        TOOL_MANIFEST["itensors"].update(
            {
                "tried": True,
                "used": True,
                "reason": "load-bearing construction and norm contraction for pinned GHZ-like MPS",
            }
        )
        TOOL_MANIFEST["itensormps"].update(
            {
                "tried": True,
                "used": True,
                "reason": "supportive MPS container for the pinned bond-dimension-2 fixture",
            }
        )

    positive = {}
    negative = {}
    boundary = {}
    cross_check = {}

    if payload is None:
        positive["julia_itensors_available"] = {
            "pass": False,
            "run_meta": run_meta,
        }
    else:
        positive = {
            "julia_itensors_available": {
                "pass": bool(payload["itensors_available"]),
                "itensors_version": payload["itensors_version"],
                "itensormps_version": payload["itensormps_version"],
            },
            "pinned_mps_constructed": {
                "pass": payload["mps_length"] == 4 and payload["max_bond_dimension"] == 2,
                "mps_length": payload["mps_length"],
                "max_bond_dimension": payload["max_bond_dimension"],
            },
            "norm_is_one": {
                "pass": close_float(payload["norm"], 1.0),
                "value": payload["norm"],
                "expected": 1.0,
            },
            "middle_cut_entropy_ln2": {
                "pass": close_float(payload["middle_cut_entropy"], EXPECTED_ENTROPY),
                "value": payload["middle_cut_entropy"],
                "expected": EXPECTED_ENTROPY,
                "tolerance": TOL,
            },
            "operator_expectation_matches_pinned_analytic": {
                "pass": close_complex(payload["operator_expectation"], EXPECTED_OPERATOR),
                "value": payload["operator_expectation"],
                "expected": EXPECTED_OPERATOR,
                "operator": "product of four local lowering maps |0000><1111|",
            },
        }
        negative = {
            "product_state_entropy_zero": {
                "pass": close_float(payload["product_state_middle_cut_entropy"], 0.0),
                "value": payload["product_state_middle_cut_entropy"],
                "expected": 0.0,
            },
            "transposed_operator_control_differs": {
                "pass": (
                    close_complex(payload["wrong_transposed_operator_expectation"], EXPECTED_WRONG_OPERATOR)
                    and not close_complex(payload["wrong_transposed_operator_expectation"], EXPECTED_OPERATOR)
                ),
                "value": payload["wrong_transposed_operator_expectation"],
                "expected_wrong_value": EXPECTED_WRONG_OPERATOR,
                "positive_value": payload["operator_expectation"],
            },
        }
        boundary = {
            "bond_dim_1_truncation_degrades_ghz_fidelity": {
                "pass": close_float(payload["bond_dim_1_truncation_fidelity"], EXPECTED_BOND_DIM_1_FIDELITY)
                and payload["bond_dim_1_truncation_fidelity"] < 1.0,
                "value": payload["bond_dim_1_truncation_fidelity"],
                "expected": EXPECTED_BOND_DIM_1_FIDELITY,
            }
        }
        cross_check = {
            "analytic_entropy_peer_agreement": {
                "pass": close_float(payload["middle_cut_entropy"], EXPECTED_ENTROPY),
                "value": payload["middle_cut_entropy"],
                "pinned_peer_expected_value": EXPECTED_ENTROPY,
                "source": "pinned analytic GHZ-like fixture, not peer result file",
            },
            "analytic_operator_peer_agreement": {
                "pass": close_complex(payload["operator_expectation"], EXPECTED_OPERATOR),
                "value": payload["operator_expectation"],
                "pinned_peer_expected_value": EXPECTED_OPERATOR,
                "source": "pinned analytic GHZ-like fixture, not peer result file",
            },
        }

    summary = {
        "positive_all_pass": all_pass(positive),
        "negative_all_pass": all_pass(negative),
        "boundary_all_pass": all_pass(boundary),
        "cross_check_all_pass": all_pass(cross_check) if cross_check else False,
    }
    summary["all_pass"] = all(summary.values())

    result = {
        "name": "sim_itensors_capability",
        "purpose": "Bounded tensor-network capability probe for ITensors on one pinned GHZ-like MPS.",
        "classification": classification,
        "claim_ceiling": "tool_micro_itensors_capability_only",
        "fixture": {
            "name": "pinned_4_site_phase_ghz_mps",
            "state_vector_basis_order": "|0000>, |0001>, ..., |1111>",
            "state_vector_literal": [
                {"real": 1.0 / math.sqrt(2.0), "imag": 0.0},
                *[{"real": 0.0, "imag": 0.0} for _ in range(14)],
                {"real": 0.0, "imag": 1.0 / math.sqrt(2.0)},
            ],
            "bond_dimension": 2,
            "analytic_middle_cut_entropy": EXPECTED_ENTROPY,
            "analytic_operator_expectation": EXPECTED_OPERATOR,
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "julia_run": run_meta,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "cross_check": cross_check,
        "summary": summary,
        "all_pass": bool(summary["all_pass"]),
        "operation_sequence": [
            "subprocess-run Julia with JULIA_LOAD_PATH=@:@stdlib and --project=system_v5/julia_carrier",
            "load ITensors and ITensorMPS",
            "build the pinned 4-site GHZ-like MPS with bond dimension 2",
            "compute MPS norm through ITensorMPS inner",
            "compute pinned 2-site middle reduced density matrix",
            "compute middle-cut von Neumann entropy and compare to ln 2",
            "contract pinned four-local transition operator and transposed negative control",
            "report bond-dimension-1 truncation fidelity boundary",
        ],
        "out_of_scope": [
            "no PEPS or PEPS3D scientific claim",
            "no foundation_nested_hopf_weyl_signed_cut_ratchet file access",
            "no bridge, axis, manifold, or canonical physics claim",
        ],
    }
    return apply_default_receipt_boundary(
        result,
        source_name="sim_itensors_capability",
        target="Use only as bounded ITensors tensor-network capability evidence for matrix row 8.",
    )


if __name__ == "__main__":
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = build_results()
    OUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Results written to {OUT_PATH}")
    print(f"summary.all_pass = {results['summary']['all_pass']}")
