import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def run_gate(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/validate_layer_completion_claims.py", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_formal_scout_result(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "sim_id": "l2_weyl_fixture",
                "classification": "formal_scout",
                "promotion_allowed": False,
                "claim_ceiling": (
                    "Formal scout only; no stacking, flux, Xi/Phi0, Axis0, "
                    "FEP, physics, or final manifold admission."
                ),
                "blocked_consumers": ["stacking", "final_manifold_admission"],
                "summary": {"all_pass": True, "max_sites": 64},
            }
        ),
        encoding="utf-8",
    )


def test_rejects_full_layer_claim_backed_only_by_formal_scout(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl spinor/chirality is fully simed and parent-complete.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_only_fully_simed_wording(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl spinor layer is only fully simed.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_multiline_completion_claim(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text("L2 Weyl spinor layer is\nparent-complete.\n", encoding="utf-8")

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_multiline_completion_claim_with_copula(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text("L2 Weyl spinor layer\nis parent-complete.\n", encoding="utf-8")

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_multiline_completion_claim_with_auxiliary(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text("L2 Weyl spinor layer\nhas now been ratified.\n", encoding="utf-8")

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_finalized_greenlit_and_accepted_wording(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 layer is finalized, greenlit, and accepted for stack use.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_does_not_synthesize_completion_claim_across_three_unrelated_lines(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl spinor layer has bounded scout evidence.\n"
        "This middle line separates the subject from the status.\n"
        "The unrelated checklist item is complete.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr


def test_does_not_synthesize_completion_claim_across_two_complete_sentences(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl spinor layer has bounded scout evidence.\n"
        "The unrelated checklist item is complete.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr


def test_does_not_synthesize_completion_claim_across_two_unpunctuated_unrelated_lines(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl spinor layer has bounded scout evidence\n"
        "The unrelated checklist item is complete\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr


def test_ignores_quoted_and_fenced_authority_phrases(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "\n".join(
            [
                "> Before any claim of final manifold admission, run the gate.",
                "```text",
                "L2 Weyl spinor layer is fully simed and parent-complete.",
                "```",
                "Actual status: bounded formal-scout coverage, not full layer completion.",
            ]
        ),
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr


def test_ignores_inline_code_authority_phrases(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "Bad wording example: `L2 Weyl spinor layer is fully simed and parent-complete`.\n"
        "Actual status: bounded formal-scout coverage, not full layer completion.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr


def test_rejects_closed_out_and_ratified_wording(tmp_path: Path) -> None:
    evidence = tmp_path / "l8_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text("L8 layer is closed out and ratified for stack.\n", encoding="utf-8")

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_not_but_completion_contrast_wording(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 layer is not just bounded; it is actually fully simed and stack-ready.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_rejects_promoted_shipped_graduated_wording(tmp_path: Path) -> None:
    evidence = tmp_path / "carrier_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "The PEPS3D carrier is promoted, shipped, and graduated for bridge use.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.promotes_unpromoted_evidence" for v in payload["violations"])


def test_allows_explicit_bounded_scout_language(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "claim.md"
    claim.write_text(
        "L2 Weyl has bounded formal-scout coverage, not full layer completion.\n",
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_allows_zero_counts_and_future_work_in_correction_docs(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "correction.md"
    claim.write_text(
        "\n".join(
            [
                "fully complete layer rows: 0",
                "true G-structure rows completed: 0",
                "official G-structure selected: false",
                "finish/deepen one individual L0-L8 layer until it becomes parent-complete",
                "No current receipt satisfies that full role.",
            ]
        ),
        encoding="utf-8",
    )

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_rejects_status_that_marks_scout_layer_complete(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    status = tmp_path / "status.json"
    status.write_text(
        json.dumps(
            {
                "classification": "formal_scout_status",
                "claim_ceiling": "Bounded formal-scout coverage only.",
                "terminology_correction_20260528": {
                    "fully_complete_layer_rows": 1,
                    "true_g_structure_rows_completed": 0,
                },
                "layers": {
                    "L2_weyl_spinor_chirality": {
                        "full_spinor_network_result": str(evidence),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--status", str(status), "--resolve-status-receipts")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "status.complete_rows_conflict_with_scouts" for v in payload["violations"])


def test_rejects_terminal_campaign_status_backed_by_scouts(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    status = tmp_path / "terminal_status.json"
    status.write_text(
        json.dumps(
            {
                "classification": "formal_scout_status",
                "campaign_terminal": True,
                "continuation_required": False,
                "layers": {
                    "L2_weyl_spinor_chirality": {
                        "full_spinor_network_result": str(evidence),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--status", str(status), "--resolve-status-receipts")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    codes = {v["code"] for v in payload["violations"]}
    assert "status.terminal_campaign_conflicts_with_scouts" in codes
    assert "status.no_continuation_conflicts_with_scouts" in codes


def test_rejects_admission_arrays_backed_by_scouts(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    status = tmp_path / "array_status.json"
    status.write_text(
        json.dumps(
            {
                "classification": "formal_scout_status",
                "layers_admitted": ["L2_weyl_spinor_chirality"],
                "layers": {
                    "L2_weyl_spinor_chirality": {
                        "full_spinor_network_result": str(evidence),
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--status", str(status), "--resolve-status-receipts")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "status.admission_array_conflicts_with_scouts" for v in payload["violations"])


def test_require_status_fails_when_status_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing_status.json"

    result = run_gate("--status", str(missing), "--require-status")

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "status.required_status_missing" for v in payload["violations"])


def test_no_inputs_fails_closed() -> None:
    result = run_gate()

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "input.no_sources" for v in payload["violations"])


def test_empty_claim_file_fails_closed(tmp_path: Path) -> None:
    evidence = tmp_path / "l2_result.json"
    write_formal_scout_result(evidence)
    claim = tmp_path / "empty.md"
    claim.write_text("   \n", encoding="utf-8")

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(v["code"] == "claim.empty_claim_file" for v in payload["violations"])


def test_rejects_self_promoting_result_without_full_contract(tmp_path: Path) -> None:
    evidence = tmp_path / "self_promoting_result.json"
    evidence.write_text(
        json.dumps(
            {
                "classification": "canonical",
                "promotion_allowed": True,
                "allowed_claims": ["L2 Weyl layer is fully simed and parent-complete."],
                "TOOL_MANIFEST": {"torch": {"used": True, "role": "load_bearing"}},
                "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(
        v["code"] == "evidence.self_promotes_without_full_contract"
        for v in payload["violations"]
    )


def test_rejects_missing_classification_boolean_self_promotion(tmp_path: Path) -> None:
    evidence = tmp_path / "bool_promoting_result.json"
    evidence.write_text(
        json.dumps(
            {
                "layer_complete": True,
                "parent_complete": True,
                "summary": "local fixture",
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(
        v["code"] == "evidence.self_promotes_without_full_contract"
        for v in payload["violations"]
    )


def test_rejects_numeric_self_promoting_evidence_without_full_contract(tmp_path: Path) -> None:
    evidence = tmp_path / "numeric_promoting_result.json"
    evidence.write_text(
        json.dumps(
            {
                "classification": "canonical",
                "promotion_allowed": True,
                "fully_complete_layer_rows": 1,
                "TOOL_MANIFEST": {"torch": {"used": True, "role": "load_bearing"}},
                "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(
        v["code"] == "evidence.self_promotes_without_full_contract"
        for v in payload["violations"]
    )


def test_rejects_completion_encoded_in_json_key_without_full_contract(tmp_path: Path) -> None:
    evidence = tmp_path / "key_promoting_result.json"
    evidence.write_text(
        json.dumps(
            {
                "classification": "canonical",
                "promotion_allowed": True,
                "l2_layer_complete_status": "yes",
                "TOOL_MANIFEST": {"torch": {"used": True, "role": "load_bearing"}},
                "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(
        v["code"] == "evidence.self_promotes_without_full_contract"
        for v in payload["violations"]
    )


def test_rejects_completion_encoded_in_json_key_value_pair(tmp_path: Path) -> None:
    evidence = tmp_path / "status_value_promoting_result.json"
    evidence.write_text(
        json.dumps(
            {
                "classification": "canonical",
                "promotion_allowed": True,
                "l2_status": "admitted",
                "TOOL_MANIFEST": {"torch": {"used": True, "role": "load_bearing"}},
                "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing"},
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(
        v["code"] == "evidence.self_promotes_without_full_contract"
        for v in payload["violations"]
    )


def test_allows_false_completion_encoded_in_json_key(tmp_path: Path) -> None:
    evidence = tmp_path / "false_key_result.json"
    evidence.write_text(
        json.dumps({"l2_layer_complete_status": "no"}),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 0, result.stdout + result.stderr


def test_rejects_token_name_drop_without_load_bearing_tools(tmp_path: Path) -> None:
    evidence = tmp_path / "name_drop_result.json"
    evidence.write_text(
        json.dumps(
            {
                "classification": "canonical",
                "promotion_allowed": True,
                "finite_map": "F01 N01 torch spinor PEPS3D MPS PEPS2D PyG",
                "domain": "8 16 32 64 sites",
                "codomain_or_output": (
                    "von_neumann mutual_information conditional_entropy "
                    "coherent_information log_negativity"
                ),
                "allowed_claims": ["L2 Weyl layer is fully simed."],
                "TOOL_MANIFEST": {
                    "torch": {"used": True, "role": "supportive"},
                    "z3": {"used": True, "role": "supportive"},
                },
                "TOOL_INTEGRATION_DEPTH": {"torch": "supportive", "z3": "supportive"},
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    row = next(
        v
        for v in payload["violations"]
        if v["code"] == "evidence.self_promotes_without_full_contract"
    )
    assert any(item.startswith("load_bearing_tools:") for item in row["missing_contract"])


def test_rejects_completion_text_in_generic_json_string_field(tmp_path: Path) -> None:
    evidence = tmp_path / "description_promoting_result.json"
    evidence.write_text(
        json.dumps(
            {
                "classification": "formal_scout",
                "promotion_allowed": False,
                "claim_ceiling": "Formal scout only.",
                "description": "L2 Weyl spinor layer is in final form and stack-ready.",
            }
        ),
        encoding="utf-8",
    )

    result = run_gate("--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert any(
        v["code"] == "evidence.self_promotes_without_full_contract"
        for v in payload["violations"]
    )


def test_innocuous_missing_classification_does_not_become_scout_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "plain_metadata.json"
    evidence.write_text(json.dumps({"note": "plain fixture"}), encoding="utf-8")
    claim = tmp_path / "claim.md"
    claim.write_text("L2 layer is fully simed.\n", encoding="utf-8")

    result = run_gate("--claim-file", str(claim), "--evidence", str(evidence))

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    codes = {v["code"] for v in payload["violations"]}
    assert "claim.completion_without_completion_evidence" in codes
    assert "claim.promotes_unpromoted_evidence" not in codes
