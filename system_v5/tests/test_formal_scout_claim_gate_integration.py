import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "system_v5" / "ops" / "formal_scouts" / "validate_formal_scout_results.py"


def write_minimal_formal_scout(path: Path, allowed_claim: str) -> None:
    path.write_text(
        json.dumps(
            {
                "classification": "formal_scout",
                "promotion_allowed": False,
                "claim_ceiling": "Formal scout only; downstream consumers remain locked.",
                "positive": {"finite_map_runs": {"pass": True}},
                "graveyard_companions": {"label_only_control_rejected": {"pass": True}},
                "boundary": {"downstream_locked": {"pass": True}},
                "why_not_v4_probes": "v5 formal-scout fixture",
                "nearby_variants": {"total": 1, "passed": 1},
                "allowed_claims": [allowed_claim],
            }
        ),
        encoding="utf-8",
    )


def run_validator(*paths: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *(str(path) for path in paths)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_formal_scout_validator_rejects_completion_overclaim(tmp_path: Path) -> None:
    result_path = tmp_path / "overclaim_results.json"
    write_minimal_formal_scout(
        result_path,
        "L2 Weyl spinor layer is fully simed and parent-complete.",
    )

    result = run_validator(result_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    row = payload["results"][0]
    assert row["pass"] is False
    assert any("layer completion claim gate failed" in error for error in row["errors"])


def test_formal_scout_validator_accepts_bounded_claim(tmp_path: Path) -> None:
    result_path = tmp_path / "bounded_results.json"
    write_minimal_formal_scout(
        result_path,
        "L2 Weyl has bounded formal-scout coverage, not full layer completion.",
    )

    result = run_validator(result_path)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["all_pass"] is True


def test_formal_scout_validator_rejects_companion_markdown_overclaim(tmp_path: Path) -> None:
    result_path = tmp_path / "companion_results.json"
    write_minimal_formal_scout(
        result_path,
        "L2 Weyl has bounded formal-scout coverage, not full layer completion.",
    )
    result_path.with_suffix(".md").write_text(
        "L2 Weyl spinor layer is fully simed and parent-complete.\n",
        encoding="utf-8",
    )

    result = run_validator(result_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    row = payload["results"][0]
    assert row["pass"] is False
    assert any("layer completion claim gate failed" in error for error in row["errors"])


def test_formal_scout_validator_rejects_split_companion_markdown_overclaim(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "split_companion_results.json"
    write_minimal_formal_scout(
        result_path,
        "L2 Weyl has bounded formal-scout coverage, not full layer completion.",
    )
    result_path.with_name("split_companion_closeout.md").write_text(
        "L2 Weyl spinor layer\nhas now been ratified.\n",
        encoding="utf-8",
    )

    result = run_validator(result_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    row = payload["results"][0]
    assert row["pass"] is False
    assert any("layer completion claim gate failed" in error for error in row["errors"])


def test_formal_scout_validator_rejects_g_structure_companion_overclaim(
    tmp_path: Path,
) -> None:
    result_path = tmp_path / "g_structure_companion_results.json"
    write_minimal_formal_scout(
        result_path,
        "G-structure work has bounded formal-scout coverage only.",
    )
    result_path.with_name("g_structure_companion_report.md").write_text(
        "The true G-structure rows completed and the stack is unlocked.\n",
        encoding="utf-8",
    )

    result = run_validator(result_path)

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    row = payload["results"][0]
    assert row["pass"] is False
    assert any("layer completion claim gate failed" in error for error in row["errors"])
