#!/usr/bin/env python3
"""Packet-local validator for geo_s10_g2_family_v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s10_g2_family_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    envelope = load(RESULT_PATH)
    math_payload = envelope["math_payload"]
    algebra = math_payload["algebra"]
    tensor = math_payload["tensor_decomposition"]
    spin = math_payload["spin_triality_chain"]
    finite = math_payload["finite_structures"]
    controls = math_payload["controls"]

    require(envelope["all_pass"] is True, "envelope all_pass false")
    require(envelope["classification"] == "scratch_diagnostic", "classification drift")
    require(envelope["promotion_allowed"] is False, "promotion_allowed drift")
    require(envelope["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(envelope["gate_pass"]["no_crowned_winner"] is True, "family map crowned a winner")
    require(envelope["engine_contract"]["mode"] == "julia_canon_plus_jax_diagnostic", "engine mode declaration drift")
    require(envelope["engine_contract"]["lanes"] == ["julia", "jax"], "declared mode lanes drift")
    require("pytorch" in envelope["engine_contract"]["supportive_lanes"], "PyTorch supportive role missing")
    require("pytorch_required_validator" in envelope["engine_contract"]["omitted_requirements"], "PyTorch validator omission not declared")
    require(envelope["triality_scope_fence"] == "D4 diagram/character-node automorphism order, not explicit intertwiners", "triality scope fence drift")

    compact = algebra["compact_g2_aut_o"]
    split = algebra["split_g2_2_aut_o_split"]
    require(compact["derivation"]["nullity_dim_der"] == 14, "compact Der(O) dim drift")
    require(compact["derivation"]["rank"] == 50, "compact derivation rank drift")
    require(split["derivation"]["nullity_dim_der"] == 14, "split Der dim drift")
    require(split["derivation"]["rank"] == 50, "split derivation rank drift")
    require(compact["imaginary_norm_signature"] == {"negative": 0, "positive": 7, "zero": 0}, "compact imaginary signature drift")
    require(split["full_norm_signature"] == {"negative": 4, "positive": 4, "zero": 0}, "split full signature drift")
    require(split["trace_zero_norm_signature"] == {"negative": 4, "positive": 3, "zero": 0}, "split trace-zero signature drift")
    require(split["isotropic_zero_divisor_witness"]["nonzero_isotropic_and_zero_divisor"] is True, "split isotropic witness missing")

    picks = compact["su3_stabilizer_picks"]
    require(picks["e1"]["stabilizer_dim"] == 8, "compact e1 stabilizer dim drift")
    require(picks["e2"]["stabilizer_dim"] == 8, "compact e2 stabilizer dim drift")
    require(picks["orbit_dimension_e1"] == 6, "compact orbit dim drift")
    require(picks["conjugacy_check"]["conjugate_subspaces_equal"] is True, "compact stabilizers not conjugate")

    require(tensor["block_dimensions"] == [1, 7, 14, 27], "tensor block dimensions drift")
    require(tensor["dimension_sum"] == 49, "tensor dim sum drift")
    require(tensor["projector_ranks_exact"]["scalar_trace_rank"] == 1, "tensor scalar projector rank drift")
    require(tensor["projector_ranks_exact"]["symmetric_tracefree_rank"] == 27, "tensor 27 rank drift")
    require(tensor["lambda2_cross_product_map"]["image_rank_7_component"] == 7, "tensor 7 rank drift")
    require(tensor["lambda2_cross_product_map"]["kernel_rank_14_component"] == 14, "tensor 14 rank drift")

    require(spin["dimension_chain"] == [14, 21, 28], "spin dimension chain drift")
    require(spin["difference_dimensions"] == [7, 7, 14], "spin difference dims drift")
    require(spin["triality_check"]["automorphism_order"] == 6, "triality order drift")
    require(spin["triality_check"]["method"] == "D4 diagram/character-node automorphism order, not explicit intertwiners", "triality method scope drift")
    require(spin["triality_check"]["scope_fence"] == "D4 diagram/character-node automorphism order, not explicit intertwiners", "triality scope drift")
    require(spin["g2_extended_derivations_preserve_cayley_form"] is True, "G2 Cayley containment drift")

    psl = finite["psl2_7_matrix_route_python"]
    orient = finite["fano_orientation_family"]
    require(psl["sl2_7_order"] == 336, "SL(2,7) order drift")
    require(psl["psl2_7_order"] == 168, "PSL(2,7) order drift")
    require(psl["subgroup_chain_orders"] == [168, 21, 7, 1], "PSL subgroup chain drift")
    require(orient["fano_automorphism_order_by_incidence_permutations"] == 168, "Fano automorphism order drift")
    require(orient["pgl3_2_order_by_binary_matrix_enumeration"] == 168, "PGL(3,2) order drift")
    require(orient["labelled_fano_triad_arrangements"] == 30, "labelled Fano arrangement count drift")
    require(orient["valid_sign_orientation_choices_for_canonical_line_system"] == 16, "valid sign count drift")
    require(orient["orientation_family_count"] == 480, "orientation family count drift")
    require(orient["transported_table_hash_count"] == 480, "transported table hash count drift")

    assoc = algebra["associative_controls"]
    require(assoc["H"]["nullity_dim_der"] == 3, "H Der dim drift")
    require(assoc["M2R"]["nullity_dim_der"] == 3, "M2R Der dim drift")
    require(assoc["O_compact_one_sign_flipped"]["nullity_dim_der"] == 3, "corrupt O Der dim drift")
    require(algebra["permuted_transport_control"]["label_only_comparison_rejected"] is True, "permuted control missing")
    require(all(controls.values()), "fabrication controls not all true")

    require(envelope["crossover_proofs"]["z3"]["erase_flip"] is True, "z3 erase flip missing")
    require(envelope["crossover_proofs"]["cvc5"]["erase_flip"] is True, "cvc5 erase flip missing")
    require(envelope["nemo_hecke"]["committed_compare"]["all_match"] is True, "Nemo committed compare mismatch")
    require(envelope["nemo_hecke"]["current"]["claim_path_tools"] == ["Nemo"], "Nemo claim path must exclude supportive Hecke")
    require(envelope["nemo_hecke"]["current"]["runtime"]["active_project"].endswith("system_v6/optional/nemo_hecke/Project.toml"), "Nemo project drift")
    require(envelope["engines"]["julia"]["capability_receipts"]["carrier_project"].endswith("system_v5/julia_carrier/Project.toml"), "Julia carrier project drift")
    require(len(envelope["tool_calls"]) > 0, "top-level tool_calls must aggregate lane receipts")
    claim_tools = set(envelope["claim_path_tools"])
    receipt_tools = {call["tool"] for call in envelope["tool_calls"] if call.get("tool") in claim_tools}
    require(receipt_tools == claim_tools, "claim_path_tools not one-to-one with aggregate function-level receipts")

    print(json.dumps({"ok": True, "result_json": str(RESULT_PATH.relative_to(ROOT)), "mode": envelope["engine_contract"]["mode"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
