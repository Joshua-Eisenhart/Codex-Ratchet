from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = Path(__file__).resolve().parent
RESULT_PATH = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_results.json"
VALIDATOR_RESULT_PATH = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_lineage_free_negative.json"
WRONG_SUBSTRATE_NEGATIVE_PATH = SIM_DIR / "results" / "gcm_ratchet_order_matrix_v1_wrong_substrate_negative.json"

if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gcm_ratchet_order_matrix_v1_boundary import boundary_errors
from gcm_ratchet_order_matrix_v1_common import CLASSIFICATION, SIM_ID, validate_payload
from scripts.gcm_substrate_check import gcm_substrate_check


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    for path in [
        SIM_DIR / "build_card.md",
        SIM_DIR / "gcm_ratchet_order_matrix_v1_common.py",
        SIM_DIR / "gcm_ratchet_order_matrix_v1.py",
        SIM_DIR / "gcm_ratchet_order_matrix_v1_boundary.py",
        SIM_DIR / "builder_self_assessment.md",
        RESULT_PATH,
        LINEAGE_FREE_NEGATIVE_PATH,
        WRONG_SUBSTRATE_NEGATIVE_PATH,
    ]:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    payload = load_json(RESULT_PATH) if RESULT_PATH.exists() else {}
    if payload:
        errors.extend(validate_payload(payload))

    boundary = {"ok": False, "errors": ["payload missing"]}
    substrate_check = {"ok": False, "errors": ["payload missing"]}
    lineage_free_negative = {"ok": False, "errors": ["negative missing"]}
    wrong_substrate_negative = {"ok": False, "errors": ["negative missing"]}

    if payload:
        boundary_error_list = boundary_errors(payload)
        boundary = {"ok": not boundary_error_list, "errors": boundary_error_list}
        if boundary_error_list:
            errors.extend(boundary_error_list)
        substrate_check = gcm_substrate_check(payload)
        if substrate_check.get("ok") is not True:
            errors.append(f"substrate helper failed: {substrate_check.get('errors')}")

    if LINEAGE_FREE_NEGATIVE_PATH.exists():
        lineage_free_negative = gcm_substrate_check(load_json(LINEAGE_FREE_NEGATIVE_PATH))
        if lineage_free_negative.get("ok") is not False:
            errors.append("lineage-free negative did not fail")

    if WRONG_SUBSTRATE_NEGATIVE_PATH.exists():
        wrong_substrate_negative = gcm_substrate_check(load_json(WRONG_SUBSTRATE_NEGATIVE_PATH))
        if wrong_substrate_negative.get("ok") is not False:
            errors.append("wrong-substrate negative did not fail")

    result = {
        "ok": not errors,
        "sim_id": SIM_ID,
        "classification": payload.get("classification", CLASSIFICATION),
        "errors": errors,
        "substrate_check": substrate_check,
        "lineage_free_negative": lineage_free_negative,
        "wrong_substrate_negative": wrong_substrate_negative,
        "boundary": boundary,
    }
    write_json(VALIDATOR_RESULT_PATH, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
