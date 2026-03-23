#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


ROLE_NEG_CLASSES: dict[str, list[str]] = {
    "STEELMAN_CORE": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "STEELMAN_ALT_FORMALISM": ["COMMUTATIVE_ASSUMPTION", "INFINITE_SET"],
    "DEVIL_CLASSICAL_TIME": ["CLASSICAL_TIME"],
    "DEVIL_COMMUTATIVE": ["COMMUTATIVE_ASSUMPTION"],
    "DEVIL_CONTINUUM": ["CONTINUOUS_BATH", "INFINITE_SET", "INFINITE_RESOLUTION"],
    "DEVIL_EQUALS_SMUGGLE": ["COMMUTATIVE_ASSUMPTION", "INFINITE_SET"],
    "BOUNDARY_REPAIR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "RESCUER_MINIMAL_EDIT": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "RESCUER_OPERATOR_REFACTOR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "ENTROPY_LENS_VN": ["CLASSICAL_TIME", "CONTINUOUS_BATH"],
    "ENTROPY_LENS_MUTUAL": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "ENGINE_LENS_SZILARD_CARNOT": ["CONTINUOUS_BATH", "CLASSICAL_TIME", "INFINITE_SET"],
}


ROLE_CLAIMS: dict[str, list[str]] = {
    "STEELMAN_CORE": [
        "Construct finite noncommutative substrate with explicit probe terms.",
        "Preserve structural diversity and avoid narrative smoothing.",
    ],
    "STEELMAN_ALT_FORMALISM": [
        "Construct alternate formalism preserving constraints and probeability.",
    ],
    "DEVIL_CLASSICAL_TIME": [
        "Generate explicit classical time assumption variants for kill pressure.",
    ],
    "DEVIL_COMMUTATIVE": [
        "Generate explicit commutative collapse variants for kill pressure.",
    ],
    "DEVIL_CONTINUUM": [
        "Generate explicit continuum/infinite assumptions for kill pressure.",
    ],
    "DEVIL_EQUALS_SMUGGLE": [
        "Generate identity/equality-smuggling variants for kill pressure.",
    ],
    "BOUNDARY_REPAIR": [
        "Generate boundary repairs around known failures with explicit lineage.",
    ],
    "RESCUER_MINIMAL_EDIT": [
        "Generate minimal-edit rescue attempts from recent graveyard targets.",
    ],
    "RESCUER_OPERATOR_REFACTOR": [
        "Generate operator-level rescue rewrites from recent graveyard targets.",
    ],
    "ENTROPY_LENS_VN": [
        "Frame entropy via density-matrix operator witnesses and nonclassical boundaries.",
    ],
    "ENTROPY_LENS_MUTUAL": [
        "Frame entropy/correlation via partial-trace and trajectory witnesses.",
    ],
    "ENGINE_LENS_SZILARD_CARNOT": [
        "Extract QIT-compatible engine witnesses and isolate classical assumptions.",
    ],
}


ROLE_RISKS: dict[str, list[str]] = {
    "STEELMAN_CORE": ["No primitive classical assumptions."],
    "STEELMAN_ALT_FORMALISM": ["No hidden Euclidean/time primitives."],
    "DEVIL_CLASSICAL_TIME": ["Adversarial lane; expected failure."],
    "DEVIL_COMMUTATIVE": ["Adversarial lane; expected failure."],
    "DEVIL_CONTINUUM": ["Adversarial lane; expected failure."],
    "DEVIL_EQUALS_SMUGGLE": ["Adversarial lane; expected failure."],
    "BOUNDARY_REPAIR": ["Do not collapse narrative plurality."],
    "RESCUER_MINIMAL_EDIT": ["Rescue may fail; keep failure explicit."],
    "RESCUER_OPERATOR_REFACTOR": ["Rescue may fail; keep failure explicit."],
    "ENTROPY_LENS_VN": ["No primitive bath/time assumptions."],
    "ENTROPY_LENS_MUTUAL": ["No classical collapse assumptions."],
    "ENGINE_LENS_SZILARD_CARNOT": ["No primitive temperature/time assumptions."],
}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_memo(
    *,
    run_id: str,
    sequence: int,
    role: str,
    term_candidates: list[str],
    support_terms: list[str],
    rescue_targets: list[str],
) -> dict:
    role_u = str(role).strip().upper()
    return {
        "schema": "A1_LAWYER_MEMO_v1",
        "run_id": str(run_id),
        "sequence": int(sequence),
        "role": role_u,
        "claims": list(ROLE_CLAIMS.get(role_u, ["Generate explicit nonclassical claims."])),
        "risks": list(ROLE_RISKS.get(role_u, ["No narrative smoothing."])),
        "graveyard_rescue_targets": list(rescue_targets),
        "proposed_negative_classes": list(ROLE_NEG_CLASSES.get(role_u, ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"])),
        "proposed_terms": list(term_candidates),
        "support_terms": [str(x).strip() for x in support_terms if str(x).strip()],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Stub external memo provider for A1 exchange testing.")
    ap.add_argument("--request-json", required=True)
    ap.add_argument("--response-json", required=True)
    args = ap.parse_args(argv)

    req = _read_json(Path(args.request_json).expanduser().resolve())
    run_id = str(req.get("run_id", "")).strip()
    sequence = int(req.get("sequence", 0) or 0)
    roles = [str(x).strip().upper() for x in (req.get("required_roles", []) or []) if str(x).strip()]
    term_candidates = [str(x).strip() for x in (req.get("term_candidates", []) or []) if str(x).strip()]
    support_term_candidates = [str(x).strip() for x in (req.get("support_term_candidates", []) or []) if str(x).strip()]
    rescue_targets = [str(x).strip() for x in (req.get("graveyard_rescue_targets", []) or []) if str(x).strip()]

    memos = [
        _build_memo(
            run_id=run_id,
            sequence=sequence,
            role=role,
            term_candidates=term_candidates,
            support_terms=support_term_candidates,
            rescue_targets=rescue_targets,
        )
        for role in roles
    ]

    out = {
        "schema": "A1_EXTERNAL_MEMO_RESPONSE_v1",
        "run_id": run_id,
        "sequence": sequence,
        "memos": memos,
    }
    out_path = Path(args.response_json).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": out["schema"], "out": str(out_path), "memo_count": len(memos)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
