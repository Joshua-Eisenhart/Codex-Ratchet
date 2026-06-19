#!/usr/bin/env python3
"""Packet-local validator for terrain_spinor_shell_nest_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "terrain_spinor_shell_nest_v0"
classification = "supporting"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive packet-local validation of emitted result JSON"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive validator source hashing"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive result path checks"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATHS = {
    "julia": RESULT_DIR / f"{SIM_ID}_julia_results.json",
    "jax": RESULT_DIR / f"{SIM_ID}_jax_results.json",
    "pytorch": RESULT_DIR / f"{SIM_ID}_pytorch_results.json",
    "envelope": RESULT_DIR / f"{SIM_ID}_envelope_results.json",
}
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
SOURCE_PATH = SIM_DIR / f"validate_{SIM_ID}.py"
REQUIRED_TERRAINS = {"Se_Funnel_L", "Ni_Pit_L", "Si_Hill_L", "Se_Cannon_R"}
REQUIRED_PROPERTIES = {
    "bloch_flow",
    "lr_signed_separation",
    "shell_leakage_class",
    "shell_conditioned_gamma5_shift",
}
RUNG1_UNRAVELING_CONVENTION = (
    "standard quantum-jump unraveling: K_eff=-iH-1/2 sum_j L_j^dagger L_j for no-jump drift, "
    "jump maps psi -> L_j psi/||L_j psi||, ensemble density obeys the Lindblad generator. "
    "This is a choice; the density generator is the invariant object."
)
TOL = 1.0e-8


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    phase = "post_audit"
    if len(sys.argv) > 1:
        if sys.argv[1] not in {"--phase=builder", "--phase=post_audit", "--phase=post-audit"}:
            print("usage: validate_terrain_spinor_shell_nest_v0.py [--phase=builder|--phase=post_audit]", file=sys.stderr)
            return 2
        phase = "builder" if sys.argv[1] == "--phase=builder" else "post_audit"

    errors: list[str] = []
    payloads: dict[str, Any] = {}
    for label, path in RESULT_PATHS.items():
        if not path.exists():
            errors.append(f"missing {label} result: {path.relative_to(ROOT)}")
            continue
        payloads[label] = load_json(path)

    env = payloads.get("envelope")
    if isinstance(env, dict):
        require(errors, env.get("schema_version") == "three_engine_sim_result_v1", "envelope schema_version mismatch")
        require(errors, env.get("standard_schema_mode") == "FIELD", "standard_schema_mode must be FIELD")
        require(errors, env.get("classification") == "scratch_diagnostic", "classification must be scratch_diagnostic")
        require(errors, env.get("promotion_allowed") is False, "promotion_allowed must be false")
        require(errors, env.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
        require(errors, env.get("all_pass") is True, "all_pass must be true")
        require(errors, env.get("engine_contract", {}).get("mode") == "all_three_full_sims", "engine mode must be all_three_full_sims")
        require(errors, set(env.get("engines", {})) == {"julia", "jax", "pytorch"}, "envelope must contain julia/jax/pytorch engines")
        require(errors, RUNG1_UNRAVELING_CONVENTION in env.get("pin_spec", ""), "rung-1 quantum-jump convention text pin missing")
        require(errors, env.get("rung1_unraveling_convention_text_pin") == RUNG1_UNRAVELING_CONVENTION, "rung-1 quantum-jump convention text pin mismatch")
        require(errors, env.get("controls", {}).get("level_a_byte_exact_s5", {}).get("pass") is True, "S5 byte-exact control must pass")
        require(errors, env.get("controls", {}).get("spinor_blind_quotient_first", {}).get("kills_signed_rows") is True, "spinor-blind control must kill signed rows")
        require(errors, env.get("controls", {}).get("shell_blind_no_placement", {}).get("kills_leakage_rows") is True, "shell-blind control must kill leakage rows")
        require(errors, env.get("controls", {}).get("permuted_etas", {}).get("pass") is True, "permuted eta control must pass")
        require(errors, env.get("controls", {}).get("naive_conditioning_fails", {}).get("pass") is True, "naive conditioning control must pass")
        require(errors, env.get("si_frame_row", {}).get("honest_status") in {"own_frame_computed", "incompatible_not_forced"}, "Si frame row must be honest")
        require(errors, env.get("crossover_proofs", {}).get("z3", {}).get("verdict") == "unsat", "z3 proof must be unsat")
        require(errors, env.get("crossover_proofs", {}).get("cvc5", {}).get("verdict") == "unsat", "cvc5 proof must be unsat")
        require(errors, env.get("crossover_proofs", {}).get("z3", {}).get("erased_control_verdict") == "sat", "z3 erased control must be sat")
        require(errors, env.get("crossover_proofs", {}).get("cvc5", {}).get("erased_control_verdict") == "sat", "cvc5 erased control must be sat")
        require(errors, env.get("divergence", {}).get("julia_authoritative") is True, "divergence.julia_authoritative must be true")
        require(errors, float(env.get("divergence", {}).get("max_divergence", 1.0)) <= TOL, "max_divergence too large")

        matrix = env.get("three_level_property_matrix", {})
        require(errors, REQUIRED_PROPERTIES <= set(matrix), "property matrix missing required properties")
        shell_prop = matrix.get("shell_leakage_class", {})
        require(errors, shell_prop.get("level_a") in {"undefined", "degenerate"}, "shell leakage must be undefined/degenerate at level a")
        require(errors, shell_prop.get("level_c") == "exists", "shell leakage must exist at level c")

        rows = env.get("load_bearing_decomposition", {})
        require(errors, REQUIRED_TERRAINS <= set(rows), "missing required terrain decomposition rows")
        for terrain in REQUIRED_TERRAINS & set(rows):
            row = rows[terrain]
            require(errors, row.get("level_a_bloch", {}).get("pass") is True, f"{terrain} level-a Bloch row must pass")
            require(errors, row.get("level_b_spinor", {}).get("pass") is True, f"{terrain} level-b spinor row must pass")
            require(errors, row.get("level_c_shell", {}).get("pass") is True, f"{terrain} level-c shell row must pass")

        parent_lineage = env.get("parent_lineage", {}).get("consumed_inputs", [])
        parent_ids = {row.get("sim_id") for row in parent_lineage if isinstance(row, dict)}
        require(errors, len(parent_lineage) >= 5, "parent lineage must include five parents")
        require(errors, "terrain_exact_mirror_finder_v0" in parent_ids, "parent lineage must include terrain_exact_mirror_finder_v0")
        mirror_rows = [row for row in parent_lineage if isinstance(row, dict) and row.get("sim_id") == "terrain_exact_mirror_finder_v0"]
        require(errors, bool(mirror_rows and mirror_rows[0].get("sha256") and mirror_rows[0].get("commit_hint") == "81b38c3e6"), "mirror-law parent must carry hash and 81b38c3e6 commit hint")
        se_anchor = env.get("se_funnel_l_anchor_4_25", {})
        require(errors, se_anchor.get("computed_in_packet") is True, "Se_Funnel_L 4/25 anchor must be computed in packet")
        require(errors, se_anchor.get("inherited_via_rung1") is False, "Se_Funnel_L 4/25 anchor must not be inherited via rung 1")
        require(errors, se_anchor.get("bloch_angular_frequency_squared") == "4/25", "Se_Funnel_L 4/25 literal anchor missing")
        require(errors, se_anchor.get("pass") is True, "Se_Funnel_L 4/25 anchor must pass")
        require(errors, bool(env.get("capability_receipts")), "capability receipts must be present")
        require(errors, bool(env.get("tool_calls")), "one-to-one tool calls must be present")
        torch_depth = env.get("TOOL_INTEGRATION_DEPTH", {}).get("pytorch", {})
        for supportive_tool in ("torch_geometric", "geomstats", "e3nn", "clifford"):
            require(errors, torch_depth.get(supportive_tool) == "supportive", f"{supportive_tool} must be supportive in PyTorch leg")
        for load_bearing_tool in ("torch.func", "sympy", "z3", "cvc5"):
            require(errors, torch_depth.get(load_bearing_tool) == "load_bearing", f"{load_bearing_tool} must remain load_bearing in PyTorch leg")
        if phase == "builder":
            errors.extend(builder_audit_boundary_errors(env, SIM_DIR / "audit_verdict.md"))

    for label in ("julia", "jax", "pytorch"):
        payload = payloads.get(label)
        if not isinstance(payload, dict):
            continue
        require(errors, payload.get("all_pass") is True, f"{label} all_pass must be true")
        require(errors, payload.get("reads_peer_result") is False, f"{label} must not read peer results")
        require(errors, payload.get("classification") == "scratch_diagnostic", f"{label} classification mismatch")

    payload = {
        "schema_version": f"{SIM_ID}.validator.v1",
        "sim_id": SIM_ID,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "validator": str(SOURCE_PATH.relative_to(ROOT)),
        "validator_sha256": sha256_file(SOURCE_PATH),
        "phase": phase,
        "ok": not errors,
        "errors": errors,
        "checked_paths": [str(path.relative_to(ROOT)) for path in RESULT_PATHS.values()],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATOR_RESULT_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": not errors, "errors": errors, "result_path": str(VALIDATOR_RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
