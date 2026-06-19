import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from audit_three_engine_source_claims import audit_engine


def good_payload() -> dict:
    return {
        "schema_version": "three_engine_sim_result_v1",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "claim_path_tools": ["CliffordAlgebras", "Z3", "diffrax", "z3", "cvc5"],
        "engines": {
            "julia": {
                "ran": True,
                "source_path": "system_v5/julia_carrier/example.jl",
                "packages_used": ["CliffordAlgebras", "Z3"],
                "aligned_packages_load_bearing": ["CliffordAlgebras"],
                "package_observables": {"CliffordAlgebras": "basis multiplication observable"},
                "reads_peer_result": False,
            },
            "jax": {
                "ran": True,
                "source_path": "system_v5/jax_carrier/example.py",
                "packages_used": ["jax", "jax.numpy", "z3", "cvc5", "quimb.tensor", "diffrax"],
                "aligned_packages_load_bearing": ["diffrax", "z3", "cvc5"],
                "package_observables": {
                    "diffrax": "ODE trajectory observable",
                    "z3": "SMT polarity observable",
                    "cvc5": "SMT polarity observable",
                },
                "reads_peer_result": False,
            },
            "pytorch": {
                "ran": True,
                "source_path": "system_v5/pytorch_carrier/example.py",
                "packages_used": ["torch", "clifford", "geomstats", "e3nn"],
                "aligned_packages_load_bearing": ["geomstats"],
                "package_observables": {"geomstats": "manifold distance observable"},
                "reads_peer_result": False,
            },
        },
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": "unsat", "load_bearing": True},
            "cvc5": {"ran": True, "verdict": "unsat", "load_bearing": True},
            "julia_z3": {"ran": True, "verdict": "sat", "load_bearing": True},
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": 1.0, "jax": 1.0, "pytorch": 1.0},
            "max_divergence": 0.0,
        },
    }


def run_validator(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/validate_three_engine_sim_result.py", str(path), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_accepts_valid_three_engine_payload(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps(good_payload()), encoding="utf-8")

    result = run_validator(path, "--require-pytorch")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_accepts_torch_ga_only_pytorch_lane(tmp_path: Path) -> None:
    payload = good_payload()
    payload["engines"]["pytorch"]["packages_used"] = ["torch", "torch_ga"]
    payload["engines"]["pytorch"]["aligned_packages_load_bearing"] = ["torch_ga"]
    payload["engines"]["pytorch"]["package_observables"] = {"torch_ga": "legacy GA observable"}
    path = tmp_path / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator(path, "--require-pytorch")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_rejects_bare_jax_payload(tmp_path: Path) -> None:
    payload = good_payload()
    payload["engines"]["jax"]["aligned_packages_load_bearing"] = ["jax.numpy"]
    path = tmp_path / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator(path)

    assert result.returncode == 1
    assert "jax must have at least one aligned load-bearing package" in result.stdout


def test_rejects_cross_run_echo(tmp_path: Path) -> None:
    payload = good_payload()
    payload["engines"]["julia"]["reads_peer_result"] = True
    path = tmp_path / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator(path)

    assert result.returncode == 1
    assert "julia.reads_peer_result must be false" in result.stdout


def test_rejects_numpy_claim_path(tmp_path: Path) -> None:
    payload = good_payload()
    payload["claim_path_tools"].append("numpy")
    path = tmp_path / "result.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    result = run_validator(path)

    assert result.returncode == 1
    assert "control-only tools may not appear" in result.stdout


def finite_field_payload(jax_source: Path, julia_source: Path) -> dict:
    payload = good_payload()
    payload["claim_path_tools"] = ["galois", "julia_gf4_stdlib", "z3", "cvc5"]
    payload["engines"] = {
        "julia": {
            "ran": True,
            "source_path": str(julia_source),
            "packages_used": ["julia_gf4_stdlib"],
            "aligned_packages_load_bearing": ["julia_gf4_stdlib"],
            "package_observables": {"julia_gf4_stdlib": "GF(4) projective incidence observable"},
            "reads_peer_result": False,
        },
        "jax": {
            "ran": True,
            "source_path": str(jax_source),
            "packages_used": ["galois", "z3", "cvc5"],
            "aligned_packages_load_bearing": ["galois", "z3", "cvc5"],
            "package_observables": {
                "galois": "GF(4) projective incidence observable",
                "z3": "SMT polarity observable",
                "cvc5": "SMT polarity observable",
            },
            "reads_peer_result": False,
        },
    }
    payload["divergence"]["engine_values"] = {"julia": 1.0, "jax": 1.0}
    return payload


def write_minimal_julia_gf4_source(path: Path) -> None:
    path.write_text(
        """
function gf4_add(a::Int, b::Int)
    xor(a, b)
end

function gf4_mul(a::Int, b::Int)
    a == 0 || b == 0 ? 0 : ((a + b) % 3) + 1
end

function gf4_inv(a::Int)
    gf4_mul(a, a)
end

function rank_gf4(rows)
    length(rows)
end

function span_projective_points(rows)
    projective_class.(rows)
end

function projective_class(vec)
    tuple(vec...)
end

function frobenius_boundary(points)
    [gf4_mul(x, x) for x in points]
end
""",
        encoding="utf-8",
    )


def test_strict_source_backed_accepts_committed_q4_finite_field_routes() -> None:
    path = ROOT / "system_v6/sims/geo_s1_q4_finite_incidence_v0/results/geo_s1_q4_finite_incidence_v0_envelope_results.json"

    result = run_validator(path, "--strict-source-backed")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_strict_source_backed_rejects_fake_galois_route(tmp_path: Path) -> None:
    jax_source = tmp_path / "fake_galois_route.py"
    jax_source.write_text(
        """
import cvc5
from cvc5 import Kind
import galois
import z3

solver = z3.Solver()
solver.add(z3.Bool("claim"))
cvc = cvc5.Solver()
term = cvc.mkTerm(Kind.TRUE)
cvc.assertFormula(term)
""",
        encoding="utf-8",
    )
    julia_source = tmp_path / "good_julia_gf4_route.jl"
    write_minimal_julia_gf4_source(julia_source)
    payload_path = tmp_path / "fake_route_envelope.json"
    payload_path.write_text(json.dumps(finite_field_payload(jax_source, julia_source)), encoding="utf-8")

    result = run_validator(payload_path, "--strict-source-backed")

    assert result.returncode == 1
    assert "declared load-bearing packages imported but source-token-thin: galois" in result.stdout


def test_source_audit_accepts_sympy_rational_log_but_rejects_import_only(tmp_path: Path) -> None:
    rich_source = tmp_path / "rich_sympy.py"
    rich_source.write_text(
        """
import sympy as sp

endpoint = -sp.Rational(1, 3) * sp.log(sp.Rational(1, 3))
""",
        encoding="utf-8",
    )
    fake_source = tmp_path / "fake_sympy.py"
    fake_source.write_text("import sympy as sp\nTOKEN = 'sympy manifest only'\n", encoding="utf-8")
    rec = {
        "source_path": str(rich_source),
        "packages_used": ["sympy"],
        "aligned_packages_load_bearing": ["sympy"],
        "reads_peer_result": False,
    }

    rich = audit_engine("pytorch", rec, ROOT)
    fake = audit_engine("pytorch", {**rec, "source_path": str(fake_source)}, ROOT)

    assert rich["classification"] == "source_backed_rich_tool_claim"
    assert "sympy" in rich["source_backed_load_bearing"]
    assert fake["classification"] == "declared_rich_but_source_thin_or_baseline"
    assert "sympy" in fake["source_thin_load_bearing"]


def test_source_audit_accepts_jax_scipy_linalg_expm_but_rejects_import_only(tmp_path: Path) -> None:
    rich_source = tmp_path / "rich_jax_scipy.py"
    rich_source.write_text(
        """
import jax.scipy.linalg as jsp_linalg
import z3

propagator = jsp_linalg.expm(generator)
solver = z3.Solver()
solver.add(z3.Bool("claim"))
solver.check()
""",
        encoding="utf-8",
    )
    fake_source = tmp_path / "fake_jax_scipy.py"
    fake_source.write_text(
        """
import jax.scipy.linalg as jsp_linalg
import z3

solver = z3.Solver()
solver.add(z3.Bool("claim"))
solver.check()
""",
        encoding="utf-8",
    )
    rec = {
        "source_path": str(rich_source),
        "packages_used": ["jax.scipy.linalg", "z3"],
        "aligned_packages_load_bearing": ["jax.scipy.linalg", "z3"],
        "reads_peer_result": False,
    }

    rich = audit_engine("jax", rec, ROOT)
    fake = audit_engine("jax", {**rec, "source_path": str(fake_source)}, ROOT)

    assert rich["classification"] == "source_backed_rich_tool_claim"
    assert "jax.scipy.linalg" in rich["source_backed_load_bearing"]
    assert fake["classification"] == "mixed_source_backed_with_thin_claims"
    assert "jax.scipy.linalg" in fake["source_thin_load_bearing"]


def test_source_audit_accepts_grassmann_basis_macro_but_rejects_import_only(tmp_path: Path) -> None:
    rich_source = tmp_path / "rich_grassmann.jl"
    rich_source.write_text(
        """
using Grassmann

function row()
    @basis S"++"
    v1 * v2
end
""",
        encoding="utf-8",
    )
    fake_source = tmp_path / "fake_grassmann.jl"
    fake_source.write_text("using Grassmann\nVALUE = string(Grassmann)\n", encoding="utf-8")
    rec = {
        "source_path": str(rich_source),
        "packages_used": ["Grassmann"],
        "aligned_packages_load_bearing": ["Grassmann"],
        "reads_peer_result": False,
    }

    rich = audit_engine("julia", rec, ROOT)
    fake = audit_engine("julia", {**rec, "source_path": str(fake_source)}, ROOT)

    assert rich["classification"] == "source_backed_rich_tool_claim"
    assert "Grassmann" in rich["source_backed_load_bearing"]
    assert fake["classification"] == "declared_rich_but_source_thin_or_baseline"
    assert "Grassmann" in fake["source_thin_load_bearing"]


def tool_intent_payload(tmp_path: Path, *, fake_jax_diffrax: bool = False, omit_observable: bool = False) -> dict:
    julia_source = tmp_path / "tool_intent_julia.jl"
    julia_source.write_text(
        """
using CliffordAlgebras

alg = CliffordAlgebra(3)
""",
        encoding="utf-8",
    )
    jax_source = tmp_path / "tool_intent_jax.py"
    if fake_jax_diffrax:
        jax_source.write_text(
            """
import cvc5
import diffrax
import z3

solver = z3.Solver()
solver.add(z3.Bool("claim"))
cvc = cvc5.Solver()
""",
            encoding="utf-8",
        )
    else:
        jax_source.write_text(
            """
import cvc5
import diffrax
import z3

term = diffrax.ODETerm(lambda t, y, args: y)
solver = z3.Solver()
solver.add(z3.Bool("claim"))
cvc = cvc5.Solver()
""",
            encoding="utf-8",
        )
    pytorch_source = tmp_path / "tool_intent_pytorch.py"
    pytorch_source.write_text(
        """
from geomstats.geometry.hypersphere import Hypersphere

sphere = Hypersphere(dim=2)
""",
        encoding="utf-8",
    )
    payload = good_payload()
    payload["engines"]["julia"]["source_path"] = str(julia_source)
    payload["engines"]["jax"]["source_path"] = str(jax_source)
    payload["engines"]["pytorch"]["source_path"] = str(pytorch_source)
    if omit_observable:
        payload["engines"]["jax"]["package_observables"].pop("diffrax")
    payload["tool_intent"] = {
        "claim_classes": ["dynamic-manifold"],
        "engine_tool_intent": {
            "julia": {"CliffordAlgebras": "basis multiplication observable"},
            "jax": {
                "diffrax": "ODE trajectory observable",
                "z3": "SMT polarity observable",
                "cvc5": "SMT polarity observable",
            },
            "pytorch": {"geomstats": "manifold distance observable"},
        },
    }
    return payload


def test_require_tool_intent_accepts_source_backed_package_intents(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps(tool_intent_payload(tmp_path)), encoding="utf-8")

    result = run_validator(path, "--require-pytorch", "--require-tool-intent")

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["ok"] is True


def test_require_tool_intent_rejects_fake_intent_source_tokens(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps(tool_intent_payload(tmp_path, fake_jax_diffrax=True)), encoding="utf-8")

    result = run_validator(path, "--require-pytorch", "--require-tool-intent")

    assert result.returncode == 1
    assert "jax.diffrax tool_intent declared but source-token-thin/not-backed" in result.stdout


def test_require_tool_intent_rejects_missing_package_observable(tmp_path: Path) -> None:
    path = tmp_path / "result.json"
    path.write_text(json.dumps(tool_intent_payload(tmp_path, omit_observable=True)), encoding="utf-8")

    result = run_validator(path, "--require-pytorch", "--require-tool-intent")

    assert result.returncode == 1
    assert "jax.package_observables.diffrax must name the exact observable" in result.stdout
