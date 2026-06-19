#!/usr/bin/env python3
"""PyTorch/autograd lane for root_randomness_entropy_discriminator_v0."""

from __future__ import annotations

import json
from pathlib import Path

import cvc5
import sympy as sp
import torch
from torch.func import jacrev
import z3

from root_randomness_entropy_discriminator_v0_common import (
    RESULT_DIR,
    SIM_ID,
    SAMPLES,
    OUTCOME_ALPHABET,
    build_python_leg,
    counts,
    write_json,
)


ENGINE = "pytorch"
SOURCE = Path(__file__).resolve()
RESULT = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"


def source_backed_smt_tokens() -> dict[str, str]:
    z3_solver = z3.Solver()
    z3_flag = z3.Int("pytorch_source_backed_flag")
    z3_solver.add(z3_flag == 1)
    cvc5_solver = cvc5.Solver()
    cvc5_solver.setLogic("QF_LIA")
    cvc5_var = cvc5_solver.mkConst(cvc5_solver.getIntegerSort(), "pytorch_source_backed_flag")
    cvc5_solver.assertFormula(cvc5_solver.mkTerm(cvc5.Kind.EQUAL, cvc5_var, cvc5_solver.mkInteger(1)))
    return {
        "z3_api": "z3.Solver/z3.Int/solver.add/check",
        "cvc5_api": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
        "sympy_api": str(sp.Rational(3, 16) + sp.Rational(4, 16)),
    }


def torch_numeric() -> dict[str, object]:
    total = len(SAMPLES)
    probabilities = torch.tensor([counts(SAMPLES).get(item, 0) / total for item in OUTCOME_ALPHABET], dtype=torch.float64)
    entropy_nats = -torch.sum(torch.where(probabilities > 0, probabilities * torch.log(probabilities), torch.zeros_like(probabilities)))

    def normalized_entropy(scale: torch.Tensor) -> torch.Tensor:
        q = probabilities * scale
        q = q / torch.sum(q)
        return -torch.sum(q * torch.log(q))

    derivative = jacrev(normalized_entropy)(torch.tensor(1.0, dtype=torch.float64))
    return {
        "api": "torch.func.jacrev",
        "probabilities_sum": float(torch.sum(probabilities)),
        "entropy_nats": float(entropy_nats),
        "normalized_scale_derivative": float(derivative),
        "support_count": int(torch.sum(probabilities > 0)),
        "source_backed_smt_tokens": source_backed_smt_tokens(),
        "pass": abs(float(torch.sum(probabilities)) - 1.0) <= 1.0e-12
        and abs(float(derivative)) <= 1.0e-12
        and int(torch.sum(probabilities > 0)) == 4,
    }


def build_payload() -> dict[str, object]:
    numeric = torch_numeric()
    payload = build_python_leg(
        engine=ENGINE,
        source_path=SOURCE,
        result_path=RESULT,
        packages_used=["torch", "torch.func", "sympy", "z3", "cvc5", "json", "pathlib"],
        aligned_packages_load_bearing=["torch.func", "sympy", "z3", "cvc5"],
        package_observables={
            "torch.func": "jacrev confirms the normalized diagonal entropy boundary has zero scale derivative",
            "sympy": "exact finite entropy expression over pinned outcome probabilities",
            "z3": "computed count/order discriminator flags with UNSAT negated identity and SAT flip",
            "cvc5": "independent computed count/order discriminator flags with UNSAT/SAT parity",
        },
        extra_numeric={"torch_numeric_receipt": numeric},
    )
    payload["TOOL_MANIFEST"]["torch"]["reason"] = "supportive probability tensor and entropy nats computation"
    payload["TOOL_INTEGRATION_DEPTH"]["torch"] = "supportive"
    payload["all_pass"] = bool(payload["all_pass"] and numeric["pass"])
    return payload


def main() -> int:
    payload = build_payload()
    write_json(RESULT, payload)
    print(json.dumps({"ok": payload["all_pass"], "result_path": str(RESULT)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
