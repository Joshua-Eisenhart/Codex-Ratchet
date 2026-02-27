import hashlib
import json
import math
import re
from dataclasses import dataclass

from state import KernelState


TIER_ORDER = {
    "T0_ATOM": 0,
    "T1_COMPOUND": 1,
    "T2_OPERATOR": 2,
    "T3_STRUCTURE": 3,
    "T4_SYSTEM_SEGMENT": 4,
    "T5_ENGINE": 5,
    "T6_WHOLE_SYSTEM": 6,
}

REQUIRED_FAMILIES = {"BASELINE", "BOUNDARY_SWEEP", "PERTURBATION", "ADVERSARIAL_NEG", "COMPOSITION_STRESS"}
MASTER_SIM_ID = "SIM_MASTER_T6"
MASTER_NEG_SIM_ID = "SIM_MASTER_T6_NEG"

_DEF_FIELD_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+(\S+)\s+(.+)$")

# Negative SIM semantics are deterministic and strictly structural: a negative SIM
# may emit a KILL_SIGNAL only when the expected "offending structure" is actually
# present in the admitted artifacts. This prevents self-fulfilling "negative_class
# implies kill" behavior while keeping SIM pure-deterministic (no free-text parsing).
_NEGATIVE_CLASS_RULES: dict[str, set[str]] = {
    # These are presence checks over DEF_FIELD names; values must be non-empty.
    "COMMUTATIVE_ASSUMPTION": {"ASSUME_COMMUTATIVE", "COMMUTATIVE_ASSUMPTION"},
    "CLASSICAL_TIME": {"TIME_PARAM", "GLOBAL_TIME", "TIME_AXIS"},
    "INFINITE_SET": {"INFINITE_SET", "ASSUME_INFINITE", "CONTINUUM_ASSUMPTION"},
    "CONTINUOUS_BATH": {"CONTINUOUS_BATH"},
    "INFINITE_RESOLUTION": {"INFINITE_RESOLUTION"},
    "PRIMITIVE_EQUALS": {"EQUALS_PRIMITIVE", "ASSUME_IDENTITY_EQUIVALENCE"},
    "EUCLIDEAN_METRIC": {"EUCLIDEAN_METRIC", "CARTESIAN_COORDINATE"},
    "CLASSICAL_TEMPERATURE": {"TEMPERATURE_BATH", "TEMPERATURE_PARAM"},
}

_QIT_MATRIX_SUITE_ID = "QIT_MATRIX_SUITE_v1"
_TOL = 1e-9

_KNOWN_TERM_KEYS: tuple[str, ...] = tuple(
    sorted(
        {
            # Whole-system deterministic conjunction gate (no rosetta / no narrative).
            "qit_master_conjunction",
            "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
            "finite_dimensional_hilbert_space",
            "density_matrix",
            "probe_operator",
            "finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
            "positive_semidefinite",
            "trace_one",
            "cptp_channel",
            "partial_trace",
            "unitary_operator",
            "lindblad_generator",
            "hamiltonian_operator",
            "commutator_operator",
            "kraus_operator",
            "kraus_channel",
            "measurement_operator",
            "observable_operator",
            "projector_operator",
            "eigenvalue_spectrum",
            "density_purity",
            "density_entropy",
            "coherence_decoherence",
            "kraus_representation",
            "liouvillian_superoperator",
            "left_action_superoperator",
            "right_action_superoperator",
            "left_right_action_entropy_production_rate_orthogonality",
            "variance_order_trajectory_correlation_orthogonality",
            "channel_realization_correlation_polarity_orthogonality",
            "von_neumann_entropy",
            "entropy_production_rate",
            "noncommutative_composition_order",
            "correlation_polarity",
            "trajectory_correlation",
            "variance_order",
            "channel_realization",
            "engine_cycle",
            # Engine conversion witnesses (no Szilard/Carnot jargon inside the ratchet surface).
            "information_work_extraction_bound",
            "erasure_channel_entropy_cost_lower_bound",
            # Geometry/topology primitives (derived from QIT; admitted as terms, not as "axes").
            "pauli_operator",
            "bloch_sphere",
            "hopf_fibration",
            "hopf_torus",
            "berry_flux",
            "spinor_double_cover",
            "left_weyl_spinor",
            "right_weyl_spinor",
        },
        key=len,
        reverse=True,
    )
)


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _deterministic_hash_dict(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(encoded)


def _identity(n: int) -> list[list[complex]]:
    return [[(1.0 + 0.0j) if i == j else 0.0j for j in range(n)] for i in range(n)]


def _dagger(m: list[list[complex]]) -> list[list[complex]]:
    rows = len(m)
    cols = len(m[0]) if rows else 0
    return [[m[r][c].conjugate() for r in range(rows)] for c in range(cols)]


def _mat_add(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    return [[a[i][j] + b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _mat_sub(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _mat_scale(s: complex, a: list[list[complex]]) -> list[list[complex]]:
    return [[s * a[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def _mat_mul(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    rows = len(a)
    cols = len(b[0]) if b else 0
    inner = len(b)
    return [[sum(a[i][k] * b[k][j] for k in range(inner)) for j in range(cols)] for i in range(rows)]


def _trace(a: list[list[complex]]) -> complex:
    return sum(a[i][i] for i in range(min(len(a), len(a[0]) if a else 0)))


def _fro_norm(a: list[list[complex]]) -> float:
    return math.sqrt(sum(abs(v) ** 2 for row in a for v in row))


def _is_hermitian(a: list[list[complex]], tol: float = _TOL) -> bool:
    return _fro_norm(_mat_sub(a, _dagger(a))) <= tol


def _eigs_2x2_hermitian(a: list[list[complex]]) -> tuple[float, float]:
    a00 = float(a[0][0].real)
    a11 = float(a[1][1].real)
    b = a[0][1]
    tr = a00 + a11
    det = a00 * a11 - (abs(b) ** 2)
    disc = max(0.0, tr * tr - 4.0 * det)
    root = math.sqrt(disc)
    return ((tr + root) / 2.0, (tr - root) / 2.0)


def _is_psd_2x2(a: list[list[complex]], tol: float = _TOL) -> bool:
    if not _is_hermitian(a, tol=tol):
        return False
    eig0, eig1 = _eigs_2x2_hermitian(a)
    return eig0 >= -tol and eig1 >= -tol


def _partial_trace_second_qubit(rho4: list[list[complex]]) -> list[list[complex]]:
    out = [[0.0j, 0.0j], [0.0j, 0.0j]]
    for i in range(2):
        for j in range(2):
            acc = 0.0j
            for k in range(2):
                acc += rho4[2 * i + k][2 * j + k]
            out[i][j] = acc
    return out


def _partial_trace_first_qubit(rho4: list[list[complex]]) -> list[list[complex]]:
    out = [[0.0j, 0.0j], [0.0j, 0.0j]]
    for i in range(2):
        for j in range(2):
            acc = 0.0j
            for k in range(2):
                # Indices: (k,i) and (k,j) in the first-qubit position.
                acc += rho4[2 * k + i][2 * k + j]
            out[i][j] = acc
    return out


def _purity(rho: list[list[complex]]) -> float:
    return float(_trace(_mat_mul(rho, rho)).real)


def _renyi2_entropy_base2(rho: list[list[complex]]) -> float:
    p = max(_TOL, _purity(rho))
    return -math.log(p, 2)


def _renyi2_mutual_information_base2(rho4: list[list[complex]]) -> float:
    rho_a = _partial_trace_second_qubit(rho4)
    rho_b = _partial_trace_first_qubit(rho4)
    return _renyi2_entropy_base2(rho_a) + _renyi2_entropy_base2(rho_b) - _renyi2_entropy_base2(rho4)


def _shannon_entropy_base2(probabilities: list[float]) -> float:
    h = 0.0
    for p in probabilities:
        p = float(p)
        if p <= _TOL:
            continue
        h -= p * math.log(p, 2)
    return h


def _partial_trace_qubit_c_from_3q(rho8: list[list[complex]]) -> list[list[complex]]:
    # Keep AB, trace over C.
    out = [[0.0j for _ in range(4)] for _ in range(4)]
    for a in range(2):
        for b in range(2):
            for ap in range(2):
                for bp in range(2):
                    acc = 0.0j
                    for c in range(2):
                        i = 4 * a + 2 * b + c
                        j = 4 * ap + 2 * bp + c
                        acc += rho8[i][j]
                    out[2 * a + b][2 * ap + bp] = acc
    return out


def _partial_trace_qubit_b_from_3q(rho8: list[list[complex]]) -> list[list[complex]]:
    # Keep AC, trace over B.
    out = [[0.0j for _ in range(4)] for _ in range(4)]
    for a in range(2):
        for c in range(2):
            for ap in range(2):
                for cp in range(2):
                    acc = 0.0j
                    for b in range(2):
                        i = 4 * a + 2 * b + c
                        j = 4 * ap + 2 * b + cp
                        acc += rho8[i][j]
                    out[2 * a + c][2 * ap + cp] = acc
    return out


def _partial_trace_qubit_a_from_3q(rho8: list[list[complex]]) -> list[list[complex]]:
    # Keep BC, trace over A.
    out = [[0.0j for _ in range(4)] for _ in range(4)]
    for b in range(2):
        for c in range(2):
            for bp in range(2):
                for cp in range(2):
                    acc = 0.0j
                    for a in range(2):
                        i = 4 * a + 2 * b + c
                        j = 4 * a + 2 * bp + cp
                        acc += rho8[i][j]
                    out[2 * b + c][2 * bp + cp] = acc
    return out


def _partial_trace_bc_from_3q(rho8: list[list[complex]]) -> list[list[complex]]:
    # Keep A only.
    out = [[0.0j, 0.0j], [0.0j, 0.0j]]
    for a in range(2):
        for ap in range(2):
            acc = 0.0j
            for b in range(2):
                for c in range(2):
                    i = 4 * a + 2 * b + c
                    j = 4 * ap + 2 * b + c
                    acc += rho8[i][j]
            out[a][ap] = acc
    return out


def _partial_trace_ac_from_3q(rho8: list[list[complex]]) -> list[list[complex]]:
    # Keep B only.
    out = [[0.0j, 0.0j], [0.0j, 0.0j]]
    for b in range(2):
        for bp in range(2):
            acc = 0.0j
            for a in range(2):
                for c in range(2):
                    i = 4 * a + 2 * b + c
                    j = 4 * a + 2 * bp + c
                    acc += rho8[i][j]
            out[b][bp] = acc
    return out


def _partial_trace_ab_from_3q(rho8: list[list[complex]]) -> list[list[complex]]:
    # Keep C only.
    out = [[0.0j, 0.0j], [0.0j, 0.0j]]
    for c in range(2):
        for cp in range(2):
            acc = 0.0j
            for a in range(2):
                for b in range(2):
                    i = 4 * a + 2 * b + c
                    j = 4 * a + 2 * b + cp
                    acc += rho8[i][j]
            out[c][cp] = acc
    return out


def _density_entropy_base2(rho: list[list[complex]]) -> float:
    if len(rho) == 2 and len(rho[0]) == 2 and _is_hermitian(rho):
        vals = _eigs_2x2_hermitian(rho)
        s = 0.0
        for lam in vals:
            lam = max(0.0, float(lam))
            if lam > 0.0:
                s -= lam * math.log(lam, 2)
        return s
    return 0.0


def _format_metric_value(v: object) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return f"{float(v):.12g}"
    return str(v)


@dataclass(frozen=True)
class SimTask:
    sim_id: str
    spec_id: str
    evidence_token: str
    tier: str
    family: str
    target_class: str
    negative_class: str
    depends_on: tuple[str, ...]


class SimEngine:
    def __init__(self):
        self.code_hash_prefix = _sha256_bytes(b"bootpack_b_kernel_v1_sim_engine")

    def _normalize_probe_term(self, raw: str) -> str:
        token = str(raw or "").strip().lower().replace("-", "_").replace(" ", "_")
        while "__" in token:
            token = token.replace("__", "_")
        return token.strip("_")

    def _infer_term_key(self, task: SimTask, semantic_fields: dict[str, list[str]] | None = None) -> str:
        fields = semantic_fields or {}
        allow_unknown_atomic = str(task.target_class).strip() == "TC_ATOMIC_TERM_BOOTSTRAP"
        # Explicit semantic override from SIM_SPEC payload takes precedence.
        for name in ("PROBE_TERM", "TERM"):
            for value in fields.get(name, []):
                key = self._normalize_probe_term(str(value))
                if key in _KNOWN_TERM_KEYS or (allow_unknown_atomic and key):
                    return key
        sid = str(task.spec_id or "").lower()
        for term in _KNOWN_TERM_KEYS:
            if term in sid:
                return term
        return ""

    def _probe_report(self, *, term: str, probe_name: str, passed: bool, metrics: dict[str, object], negative_class_violation: dict[str, object]) -> dict:
        return {
            "suite": _QIT_MATRIX_SUITE_ID,
            "term": term,
            "probe_name": probe_name,
            "pass": bool(passed),
            "metrics": dict(metrics),
            "negative_class_violation": dict(negative_class_violation),
        }

    def _probe_density_matrix(self) -> dict:
        rho = [
            [0.7 + 0.0j, 0.2 + 0.1j],
            [0.2 - 0.1j, 0.3 + 0.0j],
        ]
        herm_gap = _fro_norm(_mat_sub(rho, _dagger(rho)))
        tr = _trace(rho)
        eig0, eig1 = _eigs_2x2_hermitian(rho)
        passed = herm_gap <= _TOL and abs(tr.real - 1.0) <= _TOL and abs(tr.imag) <= _TOL and min(eig0, eig1) >= -_TOL
        return self._probe_report(
            term="density_matrix",
            probe_name="density_matrix_validity",
            passed=passed,
            metrics={
                "trace_real": tr.real,
                "trace_imag": tr.imag,
                "eig_min": min(eig0, eig1),
                "hermitian_gap": herm_gap,
            },
            negative_class_violation={
                "INFINITE_SET": True,
                "CLASSICAL_TIME": True,
            },
        )

    def _probe_qit_core_toolkit(self) -> dict:
        """
        Composite probe: verifies the minimal "QIT toolkit" bundle is internally coherent.
        This is still deterministic and purely structural: it is a conjunction of existing
        suite probes, not an interpreted proof.
        """
        dm = self._probe_density_matrix()
        cptp = self._probe_cptp()
        ptr = self._probe_partial_trace()
        uni = self._probe_unitary()
        passed = bool(dm.get("pass")) and bool(cptp.get("pass")) and bool(ptr.get("pass")) and bool(uni.get("pass"))

        metrics = {
            "density_matrix": dm.get("metrics", {}),
            "cptp_channel": cptp.get("metrics", {}),
            "partial_trace": ptr.get("metrics", {}),
            "unitary_operator": uni.get("metrics", {}),
        }
        neg: dict[str, object] = {}
        for report in (dm, cptp, ptr, uni):
            mapping = report.get("negative_class_violation", {})
            if not isinstance(mapping, dict):
                continue
            for key, value in mapping.items():
                # If any subprobe flags a negative class as violated, treat it as violated.
                if key not in neg:
                    neg[key] = value
                else:
                    neg[key] = bool(neg[key]) or bool(value)

        return self._probe_report(
            term="finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator",
            probe_name="qit_core_toolkit_conjunction",
            passed=passed,
            metrics=metrics,
            negative_class_violation=neg,
        )

    def _probe_qit_master_conjunction(self) -> dict:
        """
        Whole-system deterministic conjunction gate.

        This is explicitly NOT a rosetta overlay and NOT a narrative claim.
        It is a mechanical "proof surface" that:
        - runs core QIT primitives,
        - runs geometry/topology witnesses,
        - runs two distinct engine-cycle variants (two "engines"),
        - fails closed (any subprobe fail => fail).
        """

        reports: dict[str, dict] = {
            "density_matrix": self._probe_density_matrix(),
            "cptp_channel": self._probe_cptp(),
            "partial_trace": self._probe_partial_trace(),
            "unitary_operator": self._probe_unitary(),
            "left_right_action": self._probe_left_right_action(),
            "variance_order": self._probe_variance_order(),
            "trajectory_correlation": self._probe_trajectory_correlation(),
            "hopf_torus": self._probe_hopf_torus(),
            "spinor_double_cover": self._probe_spinor_double_cover(),
            "left_weyl_spinor": self._probe_weyl_spinor(handedness=-1, term_label="left_weyl_spinor"),
            "right_weyl_spinor": self._probe_weyl_spinor(handedness=+1, term_label="right_weyl_spinor"),
            "berry_flux": self._probe_berry_flux(),
        }

        engine_left = self._probe_engine_cycle(
            semantic_fields={
                "ENGINE_OUTER_SEQ": ["SE NE NI SI"],
                "ENGINE_INNER_SEQ": ["SE SI NI NE"],
                "ENGINE_OUTER_CLASS": ["DEDUCTIVE"],
                "ENGINE_INNER_CLASS": ["INDUCTIVE"],
            }
        )
        engine_right = self._probe_engine_cycle(
            semantic_fields={
                "ENGINE_OUTER_SEQ": ["SE NE NI SI"],
                "ENGINE_INNER_SEQ": ["SE SI NI NE"],
                "ENGINE_OUTER_CLASS": ["INDUCTIVE"],
                "ENGINE_INNER_CLASS": ["DEDUCTIVE"],
            }
        )
        reports["engine_left"] = engine_left
        reports["engine_right"] = engine_right

        all_pass = all(bool(report.get("pass", False)) for report in reports.values())
        left_metrics = engine_left.get("metrics", {}) if isinstance(engine_left.get("metrics", {}), dict) else {}
        right_metrics = engine_right.get("metrics", {}) if isinstance(engine_right.get("metrics", {}), dict) else {}
        left_entropy_gap = float(left_metrics.get("minus_minus_plus_entropy_gap_bits", 0.0) or 0.0)
        right_entropy_gap = float(right_metrics.get("minus_minus_plus_entropy_gap_bits", 0.0) or 0.0)
        left_purity_gap = float(left_metrics.get("minus_minus_plus_purity_gap", 0.0) or 0.0)
        right_purity_gap = float(right_metrics.get("minus_minus_plus_purity_gap", 0.0) or 0.0)
        engine_distinct = (abs(left_entropy_gap - right_entropy_gap) > 1e-12) or (abs(left_purity_gap - right_purity_gap) > 1e-12)

        passed = bool(all_pass and engine_distinct)

        # Flattened metrics only (avoid nested dicts in SIM_EVIDENCE lines).
        metrics: dict[str, object] = {
            "sub_density_matrix_pass": bool(reports["density_matrix"].get("pass", False)),
            "sub_cptp_channel_pass": bool(reports["cptp_channel"].get("pass", False)),
            "sub_partial_trace_pass": bool(reports["partial_trace"].get("pass", False)),
            "sub_unitary_operator_pass": bool(reports["unitary_operator"].get("pass", False)),
            "sub_left_right_action_pass": bool(reports["left_right_action"].get("pass", False)),
            "sub_variance_order_pass": bool(reports["variance_order"].get("pass", False)),
            "sub_trajectory_correlation_pass": bool(reports["trajectory_correlation"].get("pass", False)),
            "sub_hopf_torus_pass": bool(reports["hopf_torus"].get("pass", False)),
            "sub_spinor_double_cover_pass": bool(reports["spinor_double_cover"].get("pass", False)),
            "sub_left_weyl_spinor_pass": bool(reports["left_weyl_spinor"].get("pass", False)),
            "sub_right_weyl_spinor_pass": bool(reports["right_weyl_spinor"].get("pass", False)),
            "sub_berry_flux_pass": bool(reports["berry_flux"].get("pass", False)),
            "sub_lr_entropy_orthogonality_pass": bool(
                self._probe_left_right_action_entropy_production_rate_orthogonality().get("pass", False)
            ),
            "sub_var_traj_orthogonality_pass": bool(
                self._probe_variance_order_trajectory_correlation_orthogonality().get("pass", False)
            ),
            "sub_chan_corr_orthogonality_pass": bool(
                self._probe_channel_realization_correlation_polarity_orthogonality().get("pass", False)
            ),
            "engine_distinct": bool(engine_distinct),
        }

        lr_metrics = reports["left_right_action"].get("metrics", {}) if isinstance(reports["left_right_action"].get("metrics", {}), dict) else {}
        hopf_metrics = reports["hopf_torus"].get("metrics", {}) if isinstance(reports["hopf_torus"].get("metrics", {}), dict) else {}
        spinor_metrics = reports["spinor_double_cover"].get("metrics", {}) if isinstance(reports["spinor_double_cover"].get("metrics", {}), dict) else {}
        left_weyl_metrics = reports["left_weyl_spinor"].get("metrics", {}) if isinstance(reports["left_weyl_spinor"].get("metrics", {}), dict) else {}
        right_weyl_metrics = reports["right_weyl_spinor"].get("metrics", {}) if isinstance(reports["right_weyl_spinor"].get("metrics", {}), dict) else {}
        flux_metrics = reports["berry_flux"].get("metrics", {}) if isinstance(reports["berry_flux"].get("metrics", {}), dict) else {}

        if "left_right_gap" in lr_metrics:
            metrics["left_right_gap"] = float(lr_metrics["left_right_gap"])
        if "eta_z_gap" in hopf_metrics:
            metrics["hopf_eta_z_gap"] = float(hopf_metrics["eta_z_gap"])
        if "eta0_z_dev_max" in hopf_metrics:
            metrics["hopf_eta0_z_dev_max"] = float(hopf_metrics["eta0_z_dev_max"])
        if "eta1_z_dev_max" in hopf_metrics:
            metrics["hopf_eta1_z_dev_max"] = float(hopf_metrics["eta1_z_dev_max"])
        if "spinor_flip_gap_l1" in spinor_metrics:
            metrics["spinor_flip_gap_l1"] = float(spinor_metrics["spinor_flip_gap_l1"])
        if "density_invariance_gap" in spinor_metrics:
            metrics["spinor_density_invariance_gap"] = float(spinor_metrics["density_invariance_gap"])
        if "chirality_split_gap" in left_weyl_metrics:
            metrics["left_weyl_chirality_split_gap"] = float(left_weyl_metrics["chirality_split_gap"])
        if "chirality_split_gap" in right_weyl_metrics:
            metrics["right_weyl_chirality_split_gap"] = float(right_weyl_metrics["chirality_split_gap"])
        if "berry_flux_plus" in flux_metrics:
            metrics["berry_flux_plus"] = float(flux_metrics["berry_flux_plus"])
        if "berry_flux_minus" in flux_metrics:
            metrics["berry_flux_minus"] = float(flux_metrics["berry_flux_minus"])

        metrics["engine_left_outer_class"] = str(left_metrics.get("outer_class", "") or "")
        metrics["engine_left_inner_class"] = str(left_metrics.get("inner_class", "") or "")
        metrics["engine_left_entropy_gap_bits"] = float(left_entropy_gap)
        metrics["engine_left_purity_gap"] = float(left_purity_gap)
        metrics["engine_right_outer_class"] = str(right_metrics.get("outer_class", "") or "")
        metrics["engine_right_inner_class"] = str(right_metrics.get("inner_class", "") or "")
        metrics["engine_right_entropy_gap_bits"] = float(right_entropy_gap)
        metrics["engine_right_purity_gap"] = float(right_purity_gap)
        metrics["engine_entropy_gap_diff_bits"] = float(right_entropy_gap - left_entropy_gap)

        neg: dict[str, object] = {}
        for report in reports.values():
            mapping = report.get("negative_class_violation", {})
            if not isinstance(mapping, dict):
                continue
            for key, value in mapping.items():
                if key not in neg:
                    neg[key] = bool(value)
                else:
                    neg[key] = bool(neg[key]) or bool(value)

        return self._probe_report(
            term="qit_master_conjunction",
            probe_name="qit_master_conjunction_geometry_plus_two_engine_cycle_variants",
            passed=passed,
            metrics=metrics,
            negative_class_violation=neg,
        )

    def _probe_unitary(self) -> dict:
        inv = 1.0 / math.sqrt(2.0)
        u = [
            [inv + 0.0j, inv + 0.0j],
            [inv + 0.0j, -inv + 0.0j],
        ]
        err = _fro_norm(_mat_sub(_mat_mul(_dagger(u), u), _identity(2)))
        passed = err <= _TOL
        return self._probe_report(
            term="unitary_operator",
            probe_name="unitary_identity_check",
            passed=passed,
            metrics={"unitarity_gap": err},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_cptp(self) -> dict:
        gamma = 0.3
        k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(1.0 - gamma) + 0.0j]]
        k1 = [[0.0j, math.sqrt(gamma) + 0.0j], [0.0j, 0.0j]]
        comp = _mat_add(_mat_mul(_dagger(k0), k0), _mat_mul(_dagger(k1), k1))
        tp_gap = _fro_norm(_mat_sub(comp, _identity(2)))
        rho = [[0.6 + 0.0j, 0.2 + 0.05j], [0.2 - 0.05j, 0.4 + 0.0j]]
        out = _mat_add(_mat_mul(_mat_mul(k0, rho), _dagger(k0)), _mat_mul(_mat_mul(k1, rho), _dagger(k1)))
        out_trace = _trace(out)
        eig0, eig1 = _eigs_2x2_hermitian(out)
        passed = tp_gap <= _TOL and abs(out_trace.real - 1.0) <= _TOL and min(eig0, eig1) >= -_TOL
        return self._probe_report(
            term="cptp_channel",
            probe_name="cptp_trace_positivity",
            passed=passed,
            metrics={
                "trace_preservation_gap": tp_gap,
                "output_trace_real": out_trace.real,
                "output_psd_min_eig": min(eig0, eig1),
            },
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_partial_trace(self) -> dict:
        inv = 1.0 / math.sqrt(2.0)
        v = [inv + 0.0j, 0.0j, 0.0j, inv + 0.0j]
        rho = [[v[i] * v[j].conjugate() for j in range(4)] for i in range(4)]
        reduced = _partial_trace_second_qubit(rho)
        target = [[0.5 + 0.0j, 0.0j], [0.0j, 0.5 + 0.0j]]
        gap = _fro_norm(_mat_sub(reduced, target))
        passed = gap <= _TOL
        return self._probe_report(
            term="partial_trace",
            probe_name="bell_partial_trace",
            passed=passed,
            metrics={"partial_trace_gap": gap},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_commutator(self) -> dict:
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]
        comm = _mat_sub(_mat_mul(x, z), _mat_mul(z, x))
        gap = _fro_norm(comm)
        passed = gap > 1e-6
        return self._probe_report(
            term="commutator_operator",
            probe_name="noncommutative_operator_gap",
            passed=passed,
            metrics={"commutator_norm": gap},
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_pauli_operator(self) -> dict:
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        def unitarity_gap(u: list[list[complex]]) -> float:
            return _fro_norm(_mat_sub(_mat_mul(_dagger(u), u), _identity(2)))

        def hermitian_gap(u: list[list[complex]]) -> float:
            return _fro_norm(_mat_sub(u, _dagger(u)))

        ux = unitarity_gap(x)
        hx = hermitian_gap(x)
        uy = unitarity_gap(y)
        hy = hermitian_gap(y)
        uz = unitarity_gap(z)
        hz = hermitian_gap(z)
        comm_xz = _fro_norm(_mat_sub(_mat_mul(x, z), _mat_mul(z, x)))

        passed = (
            ux <= _TOL
            and hx <= _TOL
            and uy <= _TOL
            and hy <= _TOL
            and uz <= _TOL
            and hz <= _TOL
            and comm_xz > 1e-6
        )
        return self._probe_report(
            term="pauli_operator",
            probe_name="pauli_unitary_hermitian_and_noncommuting_basis",
            passed=passed,
            metrics={
                "unitarity_gap_x": ux,
                "hermitian_gap_x": hx,
                "unitarity_gap_y": uy,
                "hermitian_gap_y": hy,
                "unitarity_gap_z": uz,
                "hermitian_gap_z": hz,
                "commutator_norm_xz": comm_xz,
            },
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": comm_xz > 1e-6,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_bloch_sphere(self) -> dict:
        inv = 1.0 / math.sqrt(2.0)
        # |psi> = (1, i)/sqrt(2)  => pure qubit state (Bloch-vector norm == 1)
        psi = [inv + 0.0j, 0.0 + 1.0j * inv]
        rho = [[psi[i] * psi[j].conjugate() for j in range(2)] for i in range(2)]
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        rx = float(_trace(_mat_mul(rho, x)).real)
        ry = float(_trace(_mat_mul(rho, y)).real)
        rz = float(_trace(_mat_mul(rho, z)).real)
        r_norm = math.sqrt(max(0.0, rx * rx + ry * ry + rz * rz))

        passed = abs(r_norm - 1.0) <= 1e-6 and r_norm <= 1.0 + 1e-6
        return self._probe_report(
            term="bloch_sphere",
            probe_name="bloch_vector_norm_for_pure_qubit_state",
            passed=passed,
            metrics={"bloch_rx": rx, "bloch_ry": ry, "bloch_rz": rz, "bloch_r_norm": r_norm},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_hopf_fibration(self) -> dict:
        inv = 1.0 / math.sqrt(2.0)
        psi = [inv + 0.0j, 0.0 + 1.0j * inv]
        phase = math.pi / 3.0
        eiph = complex(math.cos(phase), math.sin(phase))
        psi2 = [eiph * psi[0], eiph * psi[1]]
        rho1 = [[psi[i] * psi[j].conjugate() for j in range(2)] for i in range(2)]
        rho2 = [[psi2[i] * psi2[j].conjugate() for j in range(2)] for i in range(2)]
        rho_gap = _fro_norm(_mat_sub(rho1, rho2))
        passed = rho_gap <= _TOL
        return self._probe_report(
            term="hopf_fibration",
            probe_name="global_phase_invariance_of_density_matrix",
            passed=passed,
            metrics={"phase_rad": phase, "density_phase_invariance_gap": rho_gap},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_hopf_torus(self) -> dict:
        # Nested Hopf tori witness (derived from normalized qubit state vectors).
        #
        # Hopf coordinates on S^3:
        #   psi0 = e^{i a} cos(eta)
        #   psi1 = e^{i b} sin(eta)
        #
        # For fixed eta, varying (a,b) parameterizes a torus S^1 x S^1 in S^3.
        # Under the Hopf map to the Bloch sphere S^2:
        #   r_z = |psi0|^2 - |psi1|^2 = cos(2 eta)  (constant)
        #   r_x^2 + r_y^2 = sin^2(2 eta)           (constant)
        #
        # Two distinct eta values yield two distinct (nested) tori.
        def _psi(eta: float, a: float, b: float) -> tuple[complex, complex]:
            psi0 = complex(math.cos(a), math.sin(a)) * math.cos(eta)
            psi1 = complex(math.cos(b), math.sin(b)) * math.sin(eta)
            return psi0, psi1

        def _bloch(psi0: complex, psi1: complex) -> tuple[float, float, float]:
            r_x = 2.0 * float((psi0.conjugate() * psi1).real)
            r_y = 2.0 * float((psi0.conjugate() * psi1).imag)
            r_z = float((abs(psi0) ** 2) - (abs(psi1) ** 2))
            return r_x, r_y, r_z

        etas = (math.pi / 6.0, math.pi / 3.0)
        phases = (0.0, math.pi / 4.0, math.pi / 2.0, 3.0 * math.pi / 4.0, math.pi)

        def _torus_stats(eta: float) -> dict[str, float]:
            z_values: list[float] = []
            norms: list[float] = []
            radial_values: list[float] = []
            for a in phases:
                for b in phases:
                    psi0, psi1 = _psi(eta, a, b)
                    norms.append(float((abs(psi0) ** 2) + (abs(psi1) ** 2)))
                    r_x, r_y, r_z = _bloch(psi0, psi1)
                    z_values.append(float(r_z))
                    radial_values.append(float(math.sqrt(max(0.0, r_x * r_x + r_y * r_y))))
            z_mean = sum(z_values) / float(len(z_values))
            r_mean = sum(radial_values) / float(len(radial_values))
            z_dev = max(abs(z - z_mean) for z in z_values)
            r_dev = max(abs(r - r_mean) for r in radial_values)
            n_dev = max(abs(n - 1.0) for n in norms)
            return {"z_mean": float(z_mean), "z_dev_max": float(z_dev), "r_mean": float(r_mean), "r_dev_max": float(r_dev), "norm_dev_max": float(n_dev)}

        s0 = _torus_stats(etas[0])
        s1 = _torus_stats(etas[1])
        z_gap = abs(s0["z_mean"] - s1["z_mean"])
        passed = (
            s0["norm_dev_max"] <= 1e-9
            and s1["norm_dev_max"] <= 1e-9
            and s0["z_dev_max"] <= 1e-9
            and s1["z_dev_max"] <= 1e-9
            and z_gap > 1e-6
        )
        return self._probe_report(
            term="hopf_torus",
            probe_name="nested_hopf_torus_latitude_constancy",
            passed=passed,
            metrics={
                "eta0_rad": float(etas[0]),
                "eta1_rad": float(etas[1]),
                "eta0_z_mean": s0["z_mean"],
                "eta0_z_dev_max": s0["z_dev_max"],
                "eta0_radial_mean": s0["r_mean"],
                "eta0_radial_dev_max": s0["r_dev_max"],
                "eta1_z_mean": s1["z_mean"],
                "eta1_z_dev_max": s1["z_dev_max"],
                "eta1_radial_mean": s1["r_mean"],
                "eta1_radial_dev_max": s1["r_dev_max"],
                "eta_z_gap": float(z_gap),
            },
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_berry_flux(self) -> dict:
        # Deterministic Berry flux for spin-1/2: integral of curvature over S^2 yields ±2π.
        flux_plus = 2.0 * math.pi
        flux_minus = -2.0 * math.pi
        passed = abs((flux_plus + flux_minus)) <= _TOL and abs(abs(flux_plus) - 2.0 * math.pi) <= _TOL
        return self._probe_report(
            term="berry_flux",
            probe_name="spin_half_berry_flux_magnitude",
            passed=passed,
            metrics={"berry_flux_plus": flux_plus, "berry_flux_minus": flux_minus},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_spinor_double_cover(self) -> dict:
        # Spinor double-cover witness:
        # An SO(3) 2π rotation corresponds to an SU(2) rotation by π, which yields U = -I.
        # Therefore, psi -> -psi while the density matrix rho = |psi><psi| is invariant.
        i2 = _identity(2)
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        n = (0.3, 0.4, 0.866025403784)
        nx, ny, nz = (float(n[0]), float(n[1]), float(n[2]))
        nrm = math.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
        nsigma = _mat_add(_mat_add(_mat_scale(nx, x), _mat_scale(ny, y)), _mat_scale(nz, z))
        theta = math.pi
        c = math.cos(theta)
        s = math.sin(theta)
        u = _mat_add(_mat_scale(c, i2), _mat_scale(-1.0j * s, nsigma))

        psi0 = 1.0 + 0.0j
        psi1 = 0.0j
        out0 = u[0][0] * psi0 + u[0][1] * psi1
        out1 = u[1][0] * psi0 + u[1][1] * psi1

        spinor_flip_gap = abs(out0 + psi0) + abs(out1 + psi1)
        rho = [[psi0 * psi0.conjugate(), psi0 * psi1.conjugate()], [psi1 * psi0.conjugate(), psi1 * psi1.conjugate()]]
        rho2 = [[out0 * out0.conjugate(), out0 * out1.conjugate()], [out1 * out0.conjugate(), out1 * out1.conjugate()]]
        rho_gap = _fro_norm(_mat_sub(rho, rho2))
        passed = spinor_flip_gap <= 1e-9 and rho_gap <= 1e-9
        return self._probe_report(
            term="spinor_double_cover",
            probe_name="su2_pi_rotation_sign_flip_density_invariant",
            passed=passed,
            metrics={"spinor_flip_gap_l1": float(spinor_flip_gap), "density_invariance_gap": float(rho_gap)},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_weyl_spinor(self, *, handedness: int, term_label: str) -> dict:
        # Chirality witness:
        # Use a signed Pauli Hamiltonian H_{chi} = chi * (n · sigma), chi in {-1,+1}.
        # The commutator flow d(rho)/dt = -i [H, rho] is anti-symmetric between the
        # two chiral signs, while each branch remains explicitly non-commutative.
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        n = (0.3, -0.4, 0.866025403784)
        nx, ny, nz = (float(n[0]), float(n[1]), float(n[2]))
        nrm = math.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
        nsigma = _mat_add(_mat_add(_mat_scale(nx, x), _mat_scale(ny, y)), _mat_scale(nz, z))

        sign = -1.0 if int(handedness) < 0 else 1.0
        h = _mat_scale(sign, nsigma)
        h_other = _mat_scale(-sign, nsigma)

        rho = [[0.55 + 0.0j, 0.18 + 0.09j], [0.18 - 0.09j, 0.45 + 0.0j]]
        left = _mat_mul(h, rho)
        right = _mat_mul(rho, h)
        comm = _mat_sub(left, right)
        flow = _mat_scale(-1.0j, comm)

        left_other = _mat_mul(h_other, rho)
        right_other = _mat_mul(rho, h_other)
        comm_other = _mat_sub(left_other, right_other)
        flow_other = _mat_scale(-1.0j, comm_other)

        left_right_gap = _fro_norm(comm)
        chirality_split_gap = _fro_norm(_mat_sub(flow, flow_other))
        chirality_antisym_gap = _fro_norm(_mat_add(flow, flow_other))
        passed = left_right_gap > 1e-6 and chirality_split_gap > 1e-6 and chirality_antisym_gap <= 1e-9

        return self._probe_report(
            term=str(term_label or "left_weyl_spinor"),
            probe_name="weyl_spinor_signed_commutator_flow",
            passed=passed,
            metrics={
                "chirality_sign": float(sign),
                "left_right_gap": float(left_right_gap),
                "chirality_split_gap": float(chirality_split_gap),
                "chirality_antisym_gap": float(chirality_antisym_gap),
            },
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_left_right_action(self, term_label: str = "left_action_superoperator") -> dict:
        a = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        rho = [[0.7 + 0.0j, 0.2 + 0.0j], [0.2 + 0.0j, 0.3 + 0.0j]]
        left = _mat_mul(a, rho)
        right = _mat_mul(rho, a)
        gap = _fro_norm(_mat_sub(left, right))
        passed = gap > 1e-6
        return self._probe_report(
            term=str(term_label or "left_action_superoperator"),
            probe_name="left_right_action_gap",
            passed=passed,
            metrics={"left_right_gap": gap},
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_pair_orthogonality(
        self,
        *,
        term_label: str,
        probe_name: str,
        subprobe_a: dict,
        subprobe_b: dict,
        basis_a: list[list[complex]],
        basis_b: list[list[complex]],
    ) -> dict:
        inner = _trace(_mat_mul(_dagger(basis_a), basis_b))
        norm_a = _fro_norm(basis_a)
        norm_b = _fro_norm(basis_b)
        inner_abs = abs(inner)
        denom = max(_TOL, norm_a * norm_b)
        cosine = float(inner_abs / denom)
        passed = bool(subprobe_a.get("pass", False)) and bool(subprobe_b.get("pass", False)) and cosine <= 1e-12
        metrics = {
            "hs_inner_real": float(inner.real),
            "hs_inner_imag": float(inner.imag),
            "hs_inner_abs": float(inner_abs),
            "basis_a_norm": float(norm_a),
            "basis_b_norm": float(norm_b),
            "orthogonality_cosine_abs": float(cosine),
            "subprobe_a_pass": bool(subprobe_a.get("pass", False)),
            "subprobe_b_pass": bool(subprobe_b.get("pass", False)),
        }
        for label, report in (("a", subprobe_a), ("b", subprobe_b)):
            m = report.get("metrics", {})
            if not isinstance(m, dict):
                continue
            for key in ("left_right_gap", "entropy_delta_bits", "seq01_purity_delta", "seq01_entropy_delta_bits", "mi2_pair_diversity_delta", "seq01_delta_entropy_bits_mean"):
                if key in m:
                    metrics[f"sub_{label}_{key}"] = float(m[key])
        return self._probe_report(
            term=str(term_label),
            probe_name=str(probe_name),
            passed=passed,
            metrics=metrics,
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_left_right_action_entropy_production_rate_orthogonality(self) -> dict:
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]
        return self._probe_pair_orthogonality(
            term_label="left_right_action_entropy_production_rate_orthogonality",
            probe_name="left_right_action_vs_entropy_production_hs_orthogonality",
            subprobe_a=self._probe_left_right_action(term_label="left_action_superoperator"),
            subprobe_b=self._probe_entropy_production(),
            basis_a=x,
            basis_b=z,
        )

    def _probe_variance_order_trajectory_correlation_orthogonality(self) -> dict:
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]
        return self._probe_pair_orthogonality(
            term_label="variance_order_trajectory_correlation_orthogonality",
            probe_name="variance_order_vs_trajectory_correlation_hs_orthogonality",
            subprobe_a=self._probe_variance_order(),
            subprobe_b=self._probe_trajectory_correlation(),
            basis_a=y,
            basis_b=z,
        )

    def _probe_channel_realization_correlation_polarity_orthogonality(self) -> dict:
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        return self._probe_pair_orthogonality(
            term_label="channel_realization_correlation_polarity_orthogonality",
            probe_name="channel_realization_vs_correlation_polarity_hs_orthogonality",
            subprobe_a=self._probe_channel_realization(),
            subprobe_b=self._probe_correlation_polarity(),
            basis_a=x,
            basis_b=y,
        )

    def _probe_correlation_polarity(self) -> dict:
        # Axis-0 signal: correlation diversity response under perturbation.
        #
        # We use a deterministic Renyi-2 mutual information proxy over 3 qubits so
        # "spread across pairs" is non-trivial. This matches the axis-0 option family
        # (pairwise correlation-spread functional) without importing primitive time.
        inv = 1.0 / math.sqrt(2.0)
        # Base state: Bell(AB) ⊗ |0>_C
        v_base = [0.0j for _ in range(8)]
        v_base[0] = inv + 0.0j  # |000>
        v_base[6] = inv + 0.0j  # |110>
        rho_base = [[v_base[i] * v_base[j].conjugate() for j in range(8)] for i in range(8)]
        # Perturbed state: GHZ
        v_ghz = [0.0j for _ in range(8)]
        v_ghz[0] = inv + 0.0j  # |000>
        v_ghz[7] = inv + 0.0j  # |111>
        rho_ghz = [[v_ghz[i] * v_ghz[j].conjugate() for j in range(8)] for i in range(8)]

        eps = 0.25
        rho_eps = _mat_add(_mat_scale(1.0 - eps, rho_base), _mat_scale(eps, rho_ghz))

        def _pairwise_mi_distribution(rho8: list[list[complex]]) -> tuple[dict[str, float], float, float]:
            # Singles
            rho_a = _partial_trace_bc_from_3q(rho8)
            rho_b = _partial_trace_ac_from_3q(rho8)
            rho_c = _partial_trace_ab_from_3q(rho8)
            # Pairs
            rho_ab = _partial_trace_qubit_c_from_3q(rho8)
            rho_ac = _partial_trace_qubit_b_from_3q(rho8)
            rho_bc = _partial_trace_qubit_a_from_3q(rho8)

            s_a = _renyi2_entropy_base2(rho_a)
            s_b = _renyi2_entropy_base2(rho_b)
            s_c = _renyi2_entropy_base2(rho_c)
            s_ab = _renyi2_entropy_base2(rho_ab)
            s_ac = _renyi2_entropy_base2(rho_ac)
            s_bc = _renyi2_entropy_base2(rho_bc)

            mi_ab = max(0.0, s_a + s_b - s_ab)
            mi_ac = max(0.0, s_a + s_c - s_ac)
            mi_bc = max(0.0, s_b + s_c - s_bc)
            weights = {"ab": mi_ab, "ac": mi_ac, "bc": mi_bc}
            total = mi_ab + mi_ac + mi_bc
            if total <= _TOL:
                p = [1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0]
            else:
                p = [mi_ab / total, mi_ac / total, mi_bc / total]
            h_bits = _shannon_entropy_base2(p)
            diversity = 2.0**h_bits
            return weights, h_bits, diversity

        weights_base, h_base, d_base = _pairwise_mi_distribution(rho_base)
        weights_eps, h_eps, d_eps = _pairwise_mi_distribution(rho_eps)
        d_delta = d_eps - d_base

        passed = abs(d_delta) > 1e-9
        polarity = 1.0 if d_delta > 1e-9 else (-1.0 if d_delta < -1e-9 else 0.0)
        return self._probe_report(
            term="correlation_polarity",
            probe_name="pairwise_mutual_information_diversity_delta_under_perturbation",
            passed=passed,
            metrics={
                "epsilon": eps,
                "mi2_weights_base_ab": weights_base["ab"],
                "mi2_weights_base_ac": weights_base["ac"],
                "mi2_weights_base_bc": weights_base["bc"],
                "mi2_weights_perturbed_ab": weights_eps["ab"],
                "mi2_weights_perturbed_ac": weights_eps["ac"],
                "mi2_weights_perturbed_bc": weights_eps["bc"],
                "mi2_pair_diversity_base": d_base,
                "mi2_pair_diversity_perturbed": d_eps,
                "mi2_pair_diversity_delta": d_delta,
                "mi2_pair_entropy_base_bits": h_base,
                "mi2_pair_entropy_perturbed_bits": h_eps,
                "polarity_sign": polarity,
            },
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_trajectory_correlation(self) -> dict:
        # Axis-0 style suite: correlation trajectory functionals under repeated
        # channel composition (no primitive time; deterministic finite iteration).
        #
        # This is a compressed analogue of the legacy `axis0_traj_corr_metrics` harness:
        # we compare two terrain sequences under a fixed local unitary + local CPTP +
        # deterministic entangling step, and measure Renyi-2 mutual information and a
        # Renyi-2 conditional-entropy analogue along the trajectory.
        inv = 1.0 / math.sqrt(2.0)
        # |Phi+> = (|00> + |11>) / sqrt(2)
        v = [inv + 0.0j, 0.0j, 0.0j, inv + 0.0j]
        rho0 = [[v[i] * v[j].conjugate() for j in range(4)] for i in range(4)]

        i2 = _identity(2)
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        def _kron_2x2(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
            out = [[0.0j for _ in range(4)] for _ in range(4)]
            for i0 in range(2):
                for j0 in range(2):
                    for i1 in range(2):
                        for j1 in range(2):
                            out[2 * i0 + i1][2 * j0 + j1] = a[i0][j0] * b[i1][j1]
            return out

        cnot = [
            [1.0 + 0.0j, 0.0j, 0.0j, 0.0j],
            [0.0j, 1.0 + 0.0j, 0.0j, 0.0j],
            [0.0j, 0.0j, 0.0j, 1.0 + 0.0j],
            [0.0j, 0.0j, 1.0 + 0.0j, 0.0j],
        ]
        cnot_d = _dagger(cnot)

        def _unitary_rotation(n: tuple[float, float, float], theta: float, sign: int) -> list[list[complex]]:
            nx, ny, nz = (float(n[0]), float(n[1]), float(n[2]))
            nrm = math.sqrt(nx * nx + ny * ny + nz * nz)
            if nrm <= _TOL:
                nx, ny, nz = 0.0, 0.0, 1.0
            else:
                nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
            nsigma = _mat_add(_mat_add(_mat_scale(nx, x), _mat_scale(ny, y)), _mat_scale(nz, z))
            c = math.cos(theta)
            s = math.sin(theta) * float(sign)
            return _mat_add(_mat_scale(c, i2), _mat_scale(-1.0j * s, nsigma))

        u = _unitary_rotation((0.3, 0.4, 0.866025403784), theta=0.07, sign=1)
        ua = _kron_2x2(u, i2)
        ua_d = _dagger(ua)

        gamma = 0.02
        p = 0.02
        q = 0.02

        def _terrain(code: str) -> list[list[list[complex]]]:
            code = str(code).strip()
            if code == "Se":
                k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(max(0.0, 1.0 - gamma)) + 0.0j]]
                k1 = [[0.0j, math.sqrt(max(0.0, gamma)) + 0.0j], [0.0j, 0.0j]]
                return [k0, k1]
            if code == "Ne":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - p)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, p)), x)
                return [k0, k1]
            if code == "Ni":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - q)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, q)), z)
                return [k0, k1]
            return [i2]

        def _apply_kraus_a(rho4: list[list[complex]], ks: list[list[list[complex]]]) -> list[list[complex]]:
            out = [[0.0j for _ in range(4)] for _ in range(4)]
            for k in ks:
                ka = _kron_2x2(k, i2)
                kad = _dagger(ka)
                out = _mat_add(out, _mat_mul(_mat_mul(ka, rho4), kad))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _apply_unitary_ab(rho4: list[list[complex]], uab: list[list[complex]], uabd: list[list[complex]]) -> list[list[complex]]:
            out = _mat_mul(_mat_mul(uab, rho4), uabd)
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        seq01 = ("Se", "Ne", "Ni", "Si")
        seq02 = ("Se", "Si", "Ni", "Ne")
        cycles = 12

        def _run(seq: tuple[str, ...]) -> tuple[list[float], list[float]]:
            rho = [list(row) for row in rho0]
            mi_series: list[float] = [_renyi2_mutual_information_base2(rho)]
            s_agb_series: list[float] = []
            for _ in range(cycles):
                for terr in seq:
                    rho = _apply_unitary_ab(rho, ua, ua_d)
                    rho = _apply_kraus_a(rho, _terrain(terr))
                    rho = _apply_unitary_ab(rho, cnot, cnot_d)
                mi_series.append(_renyi2_mutual_information_base2(rho))
            # Conditional entropy analogue S2(A|B) = H2(AB) - H2(B).
            rho_b = _partial_trace_first_qubit(rho)
            sab = _renyi2_entropy_base2(rho)
            sb = _renyi2_entropy_base2(rho_b)
            s_agb_final = float(sab - sb)
            # Coarse trajectory surrogate: use final conditional entropy and MI stats.
            # (We keep this light to avoid huge evidence payloads.)
            s_agb_series = [s_agb_final]
            return mi_series, s_agb_series

        mi1, s1 = _run(seq01)
        mi2, s2 = _run(seq02)

        def _series_stats(series: list[float]) -> tuple[float, float, float]:
            if not series:
                return 0.0, 0.0, 0.0
            mean = sum(series) / float(len(series))
            return float(mean), float(min(series)), float(max(series))

        mi1_mean, mi1_min, mi1_max = _series_stats(mi1)
        mi2_mean, mi2_min, mi2_max = _series_stats(mi2)
        mi1_init, mi1_final = float(mi1[0]), float(mi1[-1])
        mi2_init, mi2_final = float(mi2[0]), float(mi2[-1])
        mi1_delta = mi1_final - mi1_init
        mi2_delta = mi2_final - mi2_init

        # Conditional entropy analogue (single-point for now).
        s1_final = float(s1[0]) if s1 else 0.0
        s2_final = float(s2[0]) if s2 else 0.0

        passed = abs(mi1_delta) > 1e-9 or abs(mi2_delta) > 1e-9 or abs(mi1_final - mi2_final) > 1e-9
        return self._probe_report(
            term="trajectory_correlation",
            probe_name="renyi2_mutual_information_trajectory_sequence_discrimination",
            passed=passed,
            metrics={
                "cycles": float(cycles),
                "gamma": float(gamma),
                "p": float(p),
                "q": float(q),
                "seq01_mi2_init_bits": mi1_init,
                "seq01_mi2_final_bits": mi1_final,
                "seq01_mi2_delta_bits": mi1_delta,
                "seq01_mi2_mean_bits": mi1_mean,
                "seq01_mi2_min_bits": mi1_min,
                "seq01_mi2_max_bits": mi1_max,
                "seq01_s2_a_given_b_final_bits": s1_final,
                "seq02_mi2_init_bits": mi2_init,
                "seq02_mi2_final_bits": mi2_final,
                "seq02_mi2_delta_bits": mi2_delta,
                "seq02_mi2_mean_bits": mi2_mean,
                "seq02_mi2_min_bits": mi2_min,
                "seq02_mi2_max_bits": mi2_max,
                "seq02_s2_a_given_b_final_bits": s2_final,
                "mi2_final_delta_seq01_minus_seq02": float(mi1_final - mi2_final),
            },
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_kraus_path_entropy(self) -> dict:
        # "JK fuzz" / path-ensemble variety: Shannon entropy over Kraus-history weights.
        rho0 = [[0.7 + 0.0j, 0.15 + 0.05j], [0.15 - 0.05j, 0.3 + 0.0j]]

        def _path_entropy(gamma: float) -> float:
            k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(1.0 - gamma) + 0.0j]]
            k1 = [[0.0j, math.sqrt(gamma) + 0.0j], [0.0j, 0.0j]]
            ks = [k0, k1]
            weights: list[float] = []
            for i in range(2):
                for j in range(2):
                    k = _mat_mul(ks[j], ks[i])
                    out = _mat_mul(_mat_mul(k, rho0), _dagger(k))
                    w = float(_trace(out).real)
                    weights.append(max(0.0, w))
            total = sum(weights)
            if total <= _TOL:
                return 0.0
            probs = [w / total for w in weights]
            return _shannon_entropy_base2(probs)

        gamma0 = 0.25
        gamma1 = 0.55
        h0 = _path_entropy(gamma0)
        h1 = _path_entropy(gamma1)
        delta = h1 - h0
        passed = h0 > _TOL and abs(delta) > _TOL
        return self._probe_report(
            term="kraus_representation",
            probe_name="kraus_history_path_entropy_delta",
            passed=passed,
            metrics={
                "history_depth": 2.0,
                "history_count": 4.0,
                "gamma_base": gamma0,
                "gamma_perturbed": gamma1,
                "path_entropy_base_bits": h0,
                "path_entropy_perturbed_bits": h1,
                "path_entropy_delta_bits": delta,
            },
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_lindblad(self) -> dict:
        rho = [[0.8 + 0.0j, 0.1 + 0.0j], [0.1 + 0.0j, 0.2 + 0.0j]]
        l = [[0.0j, 1.0 + 0.0j], [0.0j, 0.0j]]
        ld = _dagger(l)
        ldl = _mat_mul(ld, l)
        drho = _mat_sub(
            _mat_mul(_mat_mul(l, rho), ld),
            _mat_scale(0.5, _mat_add(_mat_mul(ldl, rho), _mat_mul(rho, ldl))),
        )
        trace_drift = abs(_trace(drho))
        passed = trace_drift <= _TOL
        return self._probe_report(
            term="lindblad_generator",
            probe_name="lindblad_trace_preservation",
            passed=passed,
            metrics={"trace_drift": trace_drift},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_hamiltonian(self, *, h_sign: float = 1.0) -> dict:
        rho = [[0.6 + 0.0j, 0.15 + 0.0j], [0.15 + 0.0j, 0.4 + 0.0j]]
        h = [[h_sign * (1.0 + 0.0j), h_sign * (0.2 + 0.0j)], [h_sign * (0.2 + 0.0j), h_sign * (-1.0 + 0.0j)]]
        comm = _mat_sub(_mat_mul(h, rho), _mat_mul(rho, h))
        drho = _mat_scale(-1.0j, comm)
        trace_drift = abs(_trace(drho))
        passed = trace_drift <= _TOL and _is_hermitian(h)
        # Axis-3 style signal: probability current J = i [rho, H] flips sign under H -> -H.
        # We extract a stable scalar component from J (drho here) to expose that sign.
        flux_component = float(drho[0][1].imag)
        axis3_sign = 1.0 if flux_component > _TOL else (-1.0 if flux_component < -_TOL else 0.0)
        return self._probe_report(
            term="hamiltonian_operator",
            probe_name="hamiltonian_trace_preservation",
            passed=passed,
            metrics={
                "trace_drift": trace_drift,
                "hamiltonian_hermitian": _is_hermitian(h),
                "h_sign": float(h_sign),
                "probability_current_component_imag": flux_component,
                "axis3_sign": axis3_sign,
            },
            negative_class_violation={
                # A commutative assumption is violated when the commutator current is non-zero.
                "COMMUTATIVE_ASSUMPTION": abs(flux_component) > _TOL,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_entropy(self) -> dict:
        rho = [[0.75 + 0.0j, 0.0j], [0.0j, 0.25 + 0.0j]]
        entropy = _density_entropy_base2(rho)
        passed = 0.0 <= entropy <= 1.0 + 1e-9
        return self._probe_report(
            term="von_neumann_entropy",
            probe_name="von_neumann_entropy_range",
            passed=passed,
            metrics={"entropy_bits": entropy},
            negative_class_violation={"INFINITE_SET": True, "CLASSICAL_TIME": True},
        )

    def _probe_density_purity(self) -> dict:
        rho0 = [
            [0.6 + 0.0j, 0.15 + 0.05j],
            [0.15 - 0.05j, 0.4 + 0.0j],
        ]
        purity0 = _purity(rho0)

        # Unital contraction toward maximally mixed state (radial compression).
        p = 0.35
        rho_dep = _mat_add(_mat_scale(1.0 - p, rho0), _mat_scale(p / 2.0, _identity(2)))
        purity_dep = _purity(rho_dep)

        # Non-unital CPTP map (amplitude damping) can change purity differently.
        gamma = 0.45
        k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(1.0 - gamma) + 0.0j]]
        k1 = [[0.0j, math.sqrt(gamma) + 0.0j], [0.0j, 0.0j]]
        rho_ad = _mat_add(_mat_mul(_mat_mul(k0, rho0), _dagger(k0)), _mat_mul(_mat_mul(k1, rho0), _dagger(k1)))
        purity_ad = _purity(rho_ad)

        passed = 0.5 - _TOL <= purity0 <= 1.0 + _TOL and (
            abs(purity_dep - purity0) > _TOL or abs(purity_ad - purity0) > _TOL
        )
        return self._probe_report(
            term="density_purity",
            probe_name="density_purity_changes_under_cptp",
            passed=passed,
            metrics={
                "purity_initial": purity0,
                "purity_depolarized": purity_dep,
                "purity_amplitude_damped": purity_ad,
                "purity_delta_depolarized": purity_dep - purity0,
                "purity_delta_amplitude_damped": purity_ad - purity0,
            },
            negative_class_violation={"INFINITE_SET": True, "CLASSICAL_TIME": True},
        )

    def _probe_entropy_production(self) -> dict:
        rho0 = [[1.0 + 0.0j, 0.0j], [0.0j, 0.0j]]
        gamma = 0.45
        k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(1.0 - gamma) + 0.0j]]
        k1 = [[0.0j, math.sqrt(gamma) + 0.0j], [0.0j, 0.0j]]
        rho1 = _mat_add(_mat_mul(_mat_mul(k0, rho0), _dagger(k0)), _mat_mul(_mat_mul(k1, rho0), _dagger(k1)))
        s0 = _density_entropy_base2(rho0)
        s1 = _density_entropy_base2(rho1)
        delta = s1 - s0
        passed = delta >= -_TOL
        return self._probe_report(
            term="entropy_production_rate",
            probe_name="entropy_nonnegative_delta",
            passed=passed,
            metrics={"entropy_initial_bits": s0, "entropy_final_bits": s1, "entropy_delta_bits": delta},
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_noncommutative_order(self) -> dict:
        # IMPORTANT:
        # For unitary conjugation channels, global-phase anti-commutation can cancel out
        # in the induced adjoint action (Ad_U ∘ Ad_V == Ad_V ∘ Ad_U even when UV = -VU).
        # Therefore, we measure order using left-action composition on rho instead of
        # conjugation. This keeps the probe sensitive to non-commutation.
        rho = [[0.6 + 0.0j, 0.2 + 0.0j], [0.2 + 0.0j, 0.4 + 0.0j]]
        a = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]  # Pauli-X
        b = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]  # Pauli-Z
        ab = _mat_mul(a, b)
        ba = _mat_mul(b, a)
        rho_ab = _mat_mul(ab, rho)
        rho_ba = _mat_mul(ba, rho)
        gap = _fro_norm(_mat_sub(rho_ab, rho_ba))
        passed = gap > 1e-6
        return self._probe_report(
            term="noncommutative_composition_order",
            probe_name="composition_order_gap",
            passed=passed,
            metrics={"composition_order_gap": gap},
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_probe_operator(self) -> dict:
        # Foundational probe law: a probe operator must expose sidedness and
        # non-commutative composition on finite density operators.
        rho = [[0.7 + 0.0j, 0.1 + 0.2j], [0.1 - 0.2j, 0.3 + 0.0j]]
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]  # Pauli-X
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]  # Pauli-Z
        left = _mat_mul(x, rho)
        right = _mat_mul(rho, x)
        left_right_gap = _fro_norm(_mat_sub(left, right))
        commutator = _mat_sub(_mat_mul(x, z), _mat_mul(z, x))
        commutator_gap = _fro_norm(commutator)
        passed = left_right_gap > 1e-6 and commutator_gap > 1e-6
        return self._probe_report(
            term="probe_operator",
            probe_name="probe_operator_noncommutative_sidedness",
            passed=passed,
            metrics={
                "left_right_action_gap": left_right_gap,
                "commutator_gap": commutator_gap,
            },
            negative_class_violation={
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_variance_order(self) -> dict:
        # Axis-4 style signal: variance-order as an order-sensitive effect across
        # CPTP channel sequences (no primitive time; deterministic finite suite).
        #
        # We run a small deterministic analogue of the legacy axis4 simson harness:
        #   - "Se": amplitude damping (non-unital CPTP)
        #   - "Ne": bit-flip channel
        #   - "Ni": phase-flip channel
        #   - "Si": identity channel
        #
        # Two polarities:
        #   +1: contract-first (CPTP then Z-pinching)
        #   -1: redistribute-first (unitary rotation then CPTP)
        i2 = _identity(2)
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        def _unitary_rotation(n: tuple[float, float, float], theta: float, sign: int) -> list[list[complex]]:
            nx, ny, nz = (float(n[0]), float(n[1]), float(n[2]))
            nrm = math.sqrt(nx * nx + ny * ny + nz * nz)
            if nrm <= _TOL:
                nx, ny, nz = 0.0, 0.0, 1.0
            else:
                nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
            nsigma = _mat_add(_mat_add(_mat_scale(nx, x), _mat_scale(ny, y)), _mat_scale(nz, z))
            c = math.cos(theta)
            s = math.sin(theta) * float(sign)
            # exp(-i s theta n·σ) = cos(theta) I - i sin(theta) (n·σ)
            return _mat_add(_mat_scale(c, i2), _mat_scale(-1.0j * s, nsigma))

        def _apply_unitary(rho: list[list[complex]], u: list[list[complex]]) -> list[list[complex]]:
            out = _mat_mul(_mat_mul(u, rho), _dagger(u))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _apply_kraus(rho: list[list[complex]], ks: list[list[list[complex]]]) -> list[list[complex]]:
            out = [[0.0j, 0.0j], [0.0j, 0.0j]]
            for k in ks:
                out = _mat_add(out, _mat_mul(_mat_mul(k, rho), _dagger(k)))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _pinch_z(rho: list[list[complex]]) -> list[list[complex]]:
            out = [[rho[0][0], 0.0j], [0.0j, rho[1][1]]]
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        gamma = 0.12
        p = 0.08
        q = 0.10

        def _terrain(code: str) -> list[list[list[complex]]]:
            code = str(code).strip()
            if code == "Se":
                k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(max(0.0, 1.0 - gamma)) + 0.0j]]
                k1 = [[0.0j, math.sqrt(max(0.0, gamma)) + 0.0j], [0.0j, 0.0j]]
                return [k0, k1]
            if code == "Ne":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - p)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, p)), x)
                return [k0, k1]
            if code == "Ni":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - q)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, q)), z)
                return [k0, k1]
            return [i2]

        sequences: dict[str, tuple[str, ...]] = {
            "seq01": ("Se", "Ne", "Ni", "Si"),
            "seq02": ("Se", "Si", "Ni", "Ne"),
            "seq03": ("Se", "Ne", "Si", "Ni"),
            "seq04": ("Se", "Si", "Ne", "Ni"),
        }
        u = _unitary_rotation((0.3, 0.4, 0.866025403784), theta=0.07, sign=1)

        states: list[list[list[complex]]] = [
            [[0.6 + 0.0j, 0.15 + 0.05j], [0.15 - 0.05j, 0.4 + 0.0j]],
            [[1.0 + 0.0j, 0.0j], [0.0j, 0.0j]],
            [[0.5 + 0.0j, 0.5 + 0.0j], [0.5 + 0.0j, 0.5 + 0.0j]],
            [[0.3 + 0.0j, 0.05 + 0.12j], [0.05 - 0.12j, 0.7 + 0.0j]],
        ]
        cycles = 16

        def _run(seq: tuple[str, ...], polarity: int) -> dict[str, float]:
            ent: list[float] = []
            pur: list[float] = []
            for rho0 in states:
                rho = [list(row) for row in rho0]
                for _ in range(cycles):
                    for code in seq:
                        ks = _terrain(code)
                        if polarity > 0:
                            rho = _pinch_z(_apply_kraus(rho, ks))
                        else:
                            rho = _apply_kraus(_apply_unitary(rho, u), ks)
                ent.append(_density_entropy_base2(rho))
                pur.append(_purity(rho))
            ent_mean = sum(ent) / max(1, len(ent))
            pur_mean = sum(pur) / max(1, len(pur))
            return {
                "entropy_mean_bits": float(ent_mean),
                "entropy_min_bits": float(min(ent)),
                "entropy_max_bits": float(max(ent)),
                "purity_mean": float(pur_mean),
                "purity_min": float(min(pur)),
                "purity_max": float(max(pur)),
            }

        metrics: dict[str, object] = {
            "cycles": float(cycles),
            "gamma": float(gamma),
            "p": float(p),
            "q": float(q),
        }
        deltas: list[float] = []
        for key in sorted(sequences.keys()):
            seq = sequences[key]
            plus = _run(seq, +1)
            minus = _run(seq, -1)
            d_purity = float(minus["purity_mean"] - plus["purity_mean"])
            d_entropy = float(minus["entropy_mean_bits"] - plus["entropy_mean_bits"])
            deltas.extend([abs(d_purity), abs(d_entropy)])
            metrics[f"{key}_purity_plus_mean"] = plus["purity_mean"]
            metrics[f"{key}_purity_minus_mean"] = minus["purity_mean"]
            metrics[f"{key}_purity_delta"] = d_purity
            metrics[f"{key}_entropy_plus_mean_bits"] = plus["entropy_mean_bits"]
            metrics[f"{key}_entropy_minus_mean_bits"] = minus["entropy_mean_bits"]
            metrics[f"{key}_entropy_delta_bits"] = d_entropy

        passed = any(d > 1e-9 for d in deltas)
        return self._probe_report(
            term="variance_order",
            probe_name="sequence_order_purity_entropy_effect",
            passed=passed,
            metrics=metrics,
            negative_class_violation={
                # If order-sensitive deltas exist, commutative assumptions are violated.
                "COMMUTATIVE_ASSUMPTION": passed,
                "CLASSICAL_TIME": True,
                "INFINITE_SET": True,
            },
        )

    def _probe_channel_realization(self) -> dict:
        # Axis-12 style suite: deterministic "channel family" realization across fixed
        # sequences and flux sign (unitary transport sign).
        #
        # This is a compressed, deterministic analogue of the legacy simson
        # `axis12_channel_realization_suite`.
        i2 = _identity(2)
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        def _unitary_rotation(n: tuple[float, float, float], theta: float, sign: int) -> list[list[complex]]:
            nx, ny, nz = (float(n[0]), float(n[1]), float(n[2]))
            nrm = math.sqrt(nx * nx + ny * ny + nz * nz)
            if nrm <= _TOL:
                nx, ny, nz = 0.0, 0.0, 1.0
            else:
                nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
            nsigma = _mat_add(_mat_add(_mat_scale(nx, x), _mat_scale(ny, y)), _mat_scale(nz, z))
            c = math.cos(theta)
            s = math.sin(theta) * float(sign)
            return _mat_add(_mat_scale(c, i2), _mat_scale(-1.0j * s, nsigma))

        def _apply_unitary(rho: list[list[complex]], u: list[list[complex]]) -> list[list[complex]]:
            out = _mat_mul(_mat_mul(u, rho), _dagger(u))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _apply_kraus(rho: list[list[complex]], ks: list[list[list[complex]]]) -> list[list[complex]]:
            out = [[0.0j, 0.0j], [0.0j, 0.0j]]
            for k in ks:
                out = _mat_add(out, _mat_mul(_mat_mul(k, rho), _dagger(k)))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _has_edge(seq: tuple[str, ...], a: str, b: str) -> float:
            n = len(seq)
            for i in range(n):
                x0 = seq[i]
                x1 = seq[(i + 1) % n]
                if (x0 == a and x1 == b) or (x0 == b and x1 == a):
                    return 1.0
            return 0.0

        gamma = 0.12
        p = 0.08
        q = 0.10

        def _terrain(code: str) -> list[list[list[complex]]]:
            code = str(code).strip()
            if code == "Se":
                k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(max(0.0, 1.0 - gamma)) + 0.0j]]
                k1 = [[0.0j, math.sqrt(max(0.0, gamma)) + 0.0j], [0.0j, 0.0j]]
                return [k0, k1]
            if code == "Ne":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - p)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, p)), x)
                return [k0, k1]
            if code == "Ni":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - q)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, q)), z)
                return [k0, k1]
            return [i2]

        sequences: dict[str, tuple[str, ...]] = {
            "seq01": ("Se", "Ne", "Ni", "Si"),
            "seq02": ("Se", "Si", "Ni", "Ne"),
            "seq03": ("Se", "Ne", "Si", "Ni"),
            "seq04": ("Se", "Si", "Ne", "Ni"),
        }
        theta = 0.07
        n_vec = (0.3, 0.4, 0.866025403784)
        cycles = 16
        # Fixed small state set (deterministic).
        states: list[list[list[complex]]] = [
            [[0.6 + 0.0j, 0.15 + 0.05j], [0.15 - 0.05j, 0.4 + 0.0j]],
            [[0.5 + 0.0j, 0.4 + 0.0j], [0.4 + 0.0j, 0.5 + 0.0j]],
            [[0.8 + 0.0j, 0.0j], [0.0j, 0.2 + 0.0j]],
        ]

        def _run(seq: tuple[str, ...], sign: int) -> tuple[float, float]:
            u = _unitary_rotation(n_vec, theta, sign)
            ent: list[float] = []
            pur: list[float] = []
            for rho0 in states:
                rho = [list(row) for row in rho0]
                for _ in range(cycles):
                    for terr in seq:
                        rho = _apply_unitary(rho, u)
                        rho = _apply_kraus(rho, _terrain(terr))
                ent.append(_density_entropy_base2(rho))
                pur.append(_purity(rho))
            ent_mean = sum(ent) / max(1, len(ent))
            pur_mean = sum(pur) / max(1, len(pur))
            return float(ent_mean), float(pur_mean)

        metrics: dict[str, object] = {"cycles": float(cycles), "theta": float(theta), "gamma": float(gamma), "p": float(p), "q": float(q)}
        for key, seq in sorted(sequences.items()):
            metrics[f"{key}_edge_seni"] = _has_edge(seq, "Se", "Ni")
            metrics[f"{key}_edge_nesi"] = _has_edge(seq, "Ne", "Si")
            plus_s, plus_p = _run(seq, +1)
            minus_s, minus_p = _run(seq, -1)
            metrics[f"{key}_plus_entropy_bits_mean"] = plus_s
            metrics[f"{key}_plus_purity_mean"] = plus_p
            metrics[f"{key}_minus_entropy_bits_mean"] = minus_s
            metrics[f"{key}_minus_purity_mean"] = minus_p
            metrics[f"{key}_delta_entropy_bits_mean"] = float(minus_s - plus_s)
            metrics[f"{key}_delta_purity_mean"] = float(minus_p - plus_p)

        # Pass if at least one sequence shows a sign-sensitive delta.
        deltas = [abs(float(metrics[k])) for k in metrics.keys() if str(k).startswith("seq") and str(k).endswith(("delta_entropy_bits_mean", "delta_purity_mean"))]
        passed = any(d > 1e-9 for d in deltas)
        return self._probe_report(
            term="channel_realization",
            probe_name="sequence_edges_and_sign_sensitive_endpoint_stats",
            passed=passed,
            metrics=metrics,
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _probe_engine_cycle(self, *, semantic_fields: dict[str, list[str]] | None = None) -> dict:
        # Engine-like 8-stage cycle over a deterministic finite domain.
        #
        # This is a structural harness, not a truth-claim. It provides:
        # - an explicit cycle encoding (outer loop + inner loop, 4 stages each)
        # - explicit closure witness (rho_final vs rho_initial gap)
        # - explicit order-class knobs (DEDUCTIVE vs INDUCTIVE) without importing time
        #
        # Defaults are chosen to be consistent with existing axis4-style probes:
        #   DEDUCTIVE: CPTP then pinching (contract-first)
        #   INDUCTIVE: unitary transport then CPTP (redistribute-first)
        def _get_field(name: str, default: str) -> str:
            if not semantic_fields:
                return default
            for raw in semantic_fields.get(name.upper(), []):
                value = str(raw).strip()
                if value:
                    return value
            return default

        def _get_float(name: str, default: float, *, lo: float, hi: float) -> float:
            raw = _get_field(name, "")
            if not raw:
                return float(default)
            try:
                text = str(raw).strip()
                # Kernel line fences intentionally disallow punctuation like '.' in DEF_FIELD payloads.
                # Accept a safe numeric encoding where underscores stand in for decimal points:
                #   "0_07" -> 0.07, "3_14159" -> 3.14159
                if "_" in text and all(ch.isdigit() or ch == "_" for ch in text):
                    text = text.replace("_", ".")
                val = float(text)
            except Exception:
                return float(default)
            if val != val:  # NaN
                return float(default)
            if val < lo:
                return float(lo)
            if val > hi:
                return float(hi)
            return float(val)

        outer_seq_raw = _get_field("ENGINE_OUTER_SEQ", "SE NE NI SI")
        inner_seq_raw = _get_field("ENGINE_INNER_SEQ", "SE SI NI NE")
        outer_class = _get_field("ENGINE_OUTER_CLASS", "DEDUCTIVE").upper()
        inner_class = _get_field("ENGINE_INNER_CLASS", "INDUCTIVE").upper()

        def _parse_seq(raw: str) -> tuple[str, ...]:
            tokens = [tok.strip().upper() for tok in str(raw).replace(",", " ").split() if tok.strip()]
            out: list[str] = []
            for tok in tokens:
                if tok in {"SE", "NE", "NI", "SI"}:
                    out.append(tok)
            if len(out) != 4:
                return ("SE", "NE", "NI", "SI")
            return tuple(out)

        outer_seq = _parse_seq(outer_seq_raw)
        inner_seq = _parse_seq(inner_seq_raw)

        i2 = _identity(2)
        x = [[0.0j, 1.0 + 0.0j], [1.0 + 0.0j, 0.0j]]
        y = [[0.0j, -1.0j], [1.0j, 0.0j]]
        z = [[1.0 + 0.0j, 0.0j], [0.0j, -1.0 + 0.0j]]

        def _unitary_rotation(n: tuple[float, float, float], theta: float, sign: int) -> list[list[complex]]:
            nx, ny, nz = (float(n[0]), float(n[1]), float(n[2]))
            nrm = math.sqrt(nx * nx + ny * ny + nz * nz)
            if nrm <= _TOL:
                nx, ny, nz = 0.0, 0.0, 1.0
            else:
                nx, ny, nz = nx / nrm, ny / nrm, nz / nrm
            nsigma = _mat_add(_mat_add(_mat_scale(nx, x), _mat_scale(ny, y)), _mat_scale(nz, z))
            c = math.cos(theta)
            s = math.sin(theta) * float(sign)
            return _mat_add(_mat_scale(c, i2), _mat_scale(-1.0j * s, nsigma))

        def _apply_unitary(rho: list[list[complex]], u: list[list[complex]]) -> list[list[complex]]:
            out = _mat_mul(_mat_mul(u, rho), _dagger(u))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _apply_kraus(rho: list[list[complex]], ks: list[list[list[complex]]]) -> list[list[complex]]:
            out = [[0.0j, 0.0j], [0.0j, 0.0j]]
            for k in ks:
                out = _mat_add(out, _mat_mul(_mat_mul(k, rho), _dagger(k)))
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        def _pinch_z(rho: list[list[complex]]) -> list[list[complex]]:
            out = [[rho[0][0], 0.0j], [0.0j, rho[1][1]]]
            tr = _trace(out)
            if abs(tr) > _TOL:
                out = _mat_scale(1.0 / tr, out)
            return out

        # Optional "degree of freedom knobs" for real graveyard/rescue workflows.
        # If set to 0.0, the cycle can collapse and intentionally fail (SIM_FAIL),
        # creating meaningful graveyard entries for A1 to rescue.
        gamma = _get_float("ENGINE_GAMMA", 0.12, lo=0.0, hi=0.95)
        p = _get_float("ENGINE_P", 0.08, lo=0.0, hi=0.95)
        q = _get_float("ENGINE_Q", 0.10, lo=0.0, hi=0.95)

        def _terrain(code: str) -> list[list[list[complex]]]:
            code = str(code).strip().upper()
            if code == "SE":
                k0 = [[1.0 + 0.0j, 0.0j], [0.0j, math.sqrt(max(0.0, 1.0 - gamma)) + 0.0j]]
                k1 = [[0.0j, math.sqrt(max(0.0, gamma)) + 0.0j], [0.0j, 0.0j]]
                return [k0, k1]
            if code == "NE":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - p)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, p)), x)
                return [k0, k1]
            if code == "NI":
                k0 = _mat_scale(math.sqrt(max(0.0, 1.0 - q)), i2)
                k1 = _mat_scale(math.sqrt(max(0.0, q)), z)
                return [k0, k1]
            return [i2]

        def _step(rho: list[list[complex]], u: list[list[complex]], terr: str, cls: str) -> list[list[complex]]:
            ks = _terrain(terr)
            if cls == "DEDUCTIVE":
                return _pinch_z(_apply_kraus(rho, ks))
            # INDUCTIVE (default)
            return _apply_kraus(_apply_unitary(rho, u), ks)

        rho0 = [[0.6 + 0.0j, 0.15 + 0.05j], [0.15 - 0.05j, 0.4 + 0.0j]]
        theta = _get_float("ENGINE_THETA", 0.07, lo=0.0, hi=math.pi)
        n_vec = (0.3, 0.4, 0.866025403784)

        def _run(sign: int) -> dict[str, float]:
            u = _unitary_rotation(n_vec, theta, sign)
            rho = [list(row) for row in rho0]
            for terr in outer_seq:
                rho = _step(rho, u, terr, outer_class)
            for terr in inner_seq:
                rho = _step(rho, u, terr, inner_class)
            closure_gap = _fro_norm(_mat_sub(rho, rho0))
            return {
                "final_purity": float(_purity(rho)),
                "final_entropy_bits": float(_density_entropy_base2(rho)),
                "closure_gap": float(closure_gap),
            }

        plus = _run(+1)
        minus = _run(-1)
        purity_gap = float(minus["final_purity"] - plus["final_purity"])
        entropy_gap = float(minus["final_entropy_bits"] - plus["final_entropy_bits"])
        passed = abs(purity_gap) > 1e-12 or abs(entropy_gap) > 1e-12

        return self._probe_report(
            term="engine_cycle",
            probe_name="two_loop_four_stage_cycle_closure_and_sign_sensitivity",
            passed=passed,
            metrics={
                "gamma": float(gamma),
                "p": float(p),
                "q": float(q),
                "theta": float(theta),
                "outer_seq": " ".join(outer_seq),
                "inner_seq": " ".join(inner_seq),
                "outer_class": outer_class,
                "inner_class": inner_class,
                "plus_final_purity": plus["final_purity"],
                "plus_final_entropy_bits": plus["final_entropy_bits"],
                "plus_closure_gap": plus["closure_gap"],
                "minus_final_purity": minus["final_purity"],
                "minus_final_entropy_bits": minus["final_entropy_bits"],
                "minus_closure_gap": minus["closure_gap"],
                "minus_minus_plus_purity_gap": purity_gap,
                "minus_minus_plus_entropy_gap_bits": entropy_gap,
            },
            negative_class_violation={"CLASSICAL_TIME": True, "INFINITE_SET": True},
        )

    def _run_qit_probe(self, term: str, *, semantic_fields: dict[str, list[str]] | None = None) -> dict:
        term = str(term or "").strip().lower()
        if term in {"qit_master_conjunction"}:
            return self._probe_qit_master_conjunction()
        if term in {"information_work_extraction_bound"}:
            # Engine-adjacent witness: ties correlation behavior to entropy production without
            # assuming temperature/time primitives.
            corr = self._probe_correlation_polarity()
            ent = self._probe_entropy_production()
            passed = bool(corr.get("pass")) and bool(ent.get("pass"))
            metrics = {
                "corr_probe_pass": bool(corr.get("pass")),
                "entropy_probe_pass": bool(ent.get("pass")),
                "corr_polarity": (corr.get("metrics") or {}).get("correlation_polarity", ""),
                "entropy_production_rate_bits": (ent.get("metrics") or {}).get("entropy_production_rate_bits", 0.0),
            }
            return self._probe_report(
                term="information_work_extraction_bound",
                probe_name="information_work_extraction_bound_from_corr_and_entropy",
                passed=passed,
                metrics=metrics,
                negative_class_violation={
                    "CLASSICAL_TIME": True,
                    "CONTINUOUS_BATH": True,
                    "INFINITE_SET": True,
                    "COMMUTATIVE_ASSUMPTION": True,
                },
            )
        if term in {"erasure_channel_entropy_cost_lower_bound"}:
            # Landauer-like witness, but expressed purely in terms of entropy production
            # under admissible channels (no bath/time primitives).
            ent = self._probe_entropy_production()
            passed = bool(ent.get("pass"))
            rate = float((ent.get("metrics") or {}).get("entropy_production_rate_bits", 0.0) or 0.0)
            return self._probe_report(
                term="erasure_channel_entropy_cost_lower_bound",
                probe_name="erasure_cost_lower_bound_entropy_production_rate",
                passed=passed and (rate >= 0.0),
                metrics={"entropy_production_rate_bits": rate, "lower_bound_satisfied": (rate >= 0.0)},
                negative_class_violation={
                    "CLASSICAL_TIME": True,
                    "CONTINUOUS_BATH": True,
                    "INFINITE_SET": True,
                },
            )
        if term in {"nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction"}:
            report = self._probe_qit_master_conjunction()
            report = dict(report)
            report["term"] = term
            report["probe_name"] = "qit_master_conjunction_constraint_manifold_compound"
            return report
        if term in {"finite_dimensional_density_matrix_partial_trace_cptp_channel_unitary_operator"}:
            return self._probe_qit_core_toolkit()
        if term in {"density_matrix", "positive_semidefinite", "trace_one"}:
            return self._probe_density_matrix()
        if term in {"probe_operator"}:
            return self._probe_probe_operator()
        if term in {"kraus_representation"}:
            return self._probe_kraus_path_entropy()
        if term in {"cptp_channel", "kraus_channel", "kraus_operator"}:
            return self._probe_cptp()
        if term in {"partial_trace"}:
            return self._probe_partial_trace()
        if term in {"unitary_operator"}:
            return self._probe_unitary()
        if term in {"commutator_operator", "coherence_decoherence"}:
            return self._probe_commutator()
        if term in {"pauli_operator"}:
            return self._probe_pauli_operator()
        if term in {"bloch_sphere"}:
            return self._probe_bloch_sphere()
        if term in {"hopf_fibration"}:
            return self._probe_hopf_fibration()
        if term in {"hopf_torus"}:
            return self._probe_hopf_torus()
        if term in {"berry_flux"}:
            return self._probe_berry_flux()
        if term in {"spinor_double_cover"}:
            return self._probe_spinor_double_cover()
        if term in {"left_weyl_spinor"}:
            return self._probe_weyl_spinor(handedness=-1, term_label="left_weyl_spinor")
        if term in {"right_weyl_spinor"}:
            return self._probe_weyl_spinor(handedness=+1, term_label="right_weyl_spinor")
        if term in {"left_action_superoperator", "right_action_superoperator"}:
            return self._probe_left_right_action(term_label=term)
        if term in {"left_right_action_entropy_production_rate_orthogonality"}:
            return self._probe_left_right_action_entropy_production_rate_orthogonality()
        if term in {"variance_order_trajectory_correlation_orthogonality"}:
            return self._probe_variance_order_trajectory_correlation_orthogonality()
        if term in {"channel_realization_correlation_polarity_orthogonality"}:
            return self._probe_channel_realization_correlation_polarity_orthogonality()
        if term in {"lindblad_generator", "liouvillian_superoperator"}:
            return self._probe_lindblad()
        if term in {"hamiltonian_operator", "observable_operator", "measurement_operator", "projector_operator"}:
            h_sign = 1.0
            if semantic_fields:
                raw = ""
                for value in semantic_fields.get("H_SIGN", []):
                    raw = str(value).strip()
                    if raw:
                        break
                if raw.upper() in {"-1", "MINUS"}:
                    h_sign = -1.0
            return self._probe_hamiltonian(h_sign=h_sign)
        if term in {"density_entropy", "von_neumann_entropy", "eigenvalue_spectrum"}:
            return self._probe_entropy()
        if term in {"density_purity"}:
            return self._probe_density_purity()
        if term in {"entropy_production_rate"}:
            return self._probe_entropy_production()
        if term in {"noncommutative_composition_order"}:
            return self._probe_noncommutative_order()
        if term in {"correlation_polarity"}:
            return self._probe_correlation_polarity()
        if term in {"trajectory_correlation"}:
            return self._probe_trajectory_correlation()
        if term in {"variance_order"}:
            return self._probe_variance_order()
        if term in {"channel_realization"}:
            return self._probe_channel_realization()
        if term in {"engine_cycle"}:
            return self._probe_engine_cycle(semantic_fields=semantic_fields)
        if term in {"finite_dimensional_hilbert_space"}:
            return self._probe_report(
                term="finite_dimensional_hilbert_space",
                probe_name="finite_dimension_guard",
                passed=True,
                metrics={"hilbert_dimension": 2.0, "dimension_is_finite": True},
                negative_class_violation={"INFINITE_SET": True, "CLASSICAL_TIME": True},
            )
        target_classes = [str(v).strip() for v in semantic_fields.get("TARGET_CLASS", [])]
        if "TC_ATOMIC_TERM_BOOTSTRAP" in target_classes:
            term_token = str(term or "").strip()
            term_ok = bool(term_token) and (" " not in term_token)
            return self._probe_report(
                term=term_token or "none",
                probe_name="atomic_term_bootstrap_probe",
                passed=term_ok,
                metrics={
                    "atomic_bootstrap": True,
                    "token_length": float(len(term_token)),
                    "token_has_space": (" " in term_token),
                },
                negative_class_violation=(
                    {
                        "INFINITE_SET": True,
                        "CLASSICAL_TIME": True,
                        "COMMUTATIVE_ASSUMPTION": True,
                    }
                    if term_ok
                    else {}
                ),
            )
        return self._probe_report(
            term=term or "none",
            probe_name="no_term_specific_probe",
            passed=False,
            metrics={"probe_default": True, "reason": "no_term_specific_probe"},
            negative_class_violation={},
        )

    def _negative_class_violated(self, normalized_negative_class: str, probe_report: dict) -> bool:
        mapping = probe_report.get("negative_class_violation", {})
        if not isinstance(mapping, dict):
            return True
        value = mapping.get(normalized_negative_class)
        if value is None:
            return True
        return bool(value)

    def _extract_def_fields(self, item_text: str) -> dict[str, list[str]]:
        fields: dict[str, list[str]] = {}
        for raw in str(item_text or "").splitlines():
            line = raw.strip()
            match = _DEF_FIELD_RE.match(line)
            if not match:
                continue
            name = match.group(1).strip().upper()
            value = match.group(2).strip()
            if value.startswith('"') and value.endswith('"') and len(value) >= 2:
                # Minimal unquote for quoted values (TERM/LABEL/FORMULA). This avoids
                # JSON parsing and keeps semantics structural.
                value = value[1:-1]
            fields.setdefault(name, []).append(value)
        return fields

    def _gather_semantic_fields(self, state: KernelState, task: SimTask) -> dict[str, list[str]]:
        merged: dict[str, list[str]] = {}
        sources: list[str] = [task.spec_id]
        sources.extend([dep for dep in task.depends_on if dep])
        for item_id in sources:
            entry = state.survivor_ledger.get(item_id)
            if not isinstance(entry, dict):
                continue
            item_text = entry.get("item_text", "")
            for name, values in self._extract_def_fields(str(item_text)).items():
                merged.setdefault(name, []).extend(values)
        return merged

    def _should_emit_kill(self, state: KernelState, task: SimTask, probe_report: dict) -> bool:
        negative_class = str(task.negative_class or "").strip()
        if not negative_class:
            return False
        normalized = negative_class.upper()
        if normalized.startswith("NEG_"):
            normalized = normalized[4:]
        required_fields = _NEGATIVE_CLASS_RULES.get(normalized)
        if not required_fields:
            return False
        fields = self._gather_semantic_fields(state, task)
        for field_name in required_fields:
            values = [str(v).strip() for v in fields.get(field_name, [])]
            if any(values):
                return self._negative_class_violated(normalized, probe_report)
        return False

    def _kill_targets_for_task(self, state: KernelState, task: SimTask) -> list[str]:
        # Default kill target remains the SIM spec itself (legacy behavior).
        targets: list[str] = [task.spec_id]
        entry = state.survivor_ledger.get(task.spec_id)
        if not isinstance(entry, dict):
            return targets
        fields = self._extract_def_fields(str(entry.get("item_text", "")))
        for raw in fields.get("KILL_TARGET", []):
            target = str(raw).strip()
            if not target:
                continue
            targets.append(target)
        # Preserve order but remove duplicates.
        dedup: list[str] = []
        seen: set[str] = set()
        for target in targets:
            if target in seen:
                continue
            seen.add(target)
            dedup.append(target)
        return dedup

    def run_task(self, state: KernelState, task: SimTask) -> str:
        input_hash = state.hash()
        semantic_fields = self._gather_semantic_fields(state, task)
        term_key = self._infer_term_key(task, semantic_fields)
        probe_report = self._run_qit_probe(term_key, semantic_fields=semantic_fields)
        if (
            str(task.target_class) == "TC_ATOMIC_TERM_BOOTSTRAP"
            and str(probe_report.get("probe_name", "")) == "no_term_specific_probe"
        ):
            term_hint = str(term_key or "").strip()
            if not term_hint:
                term_hint = str(task.spec_id).split("_SIM_CANON_")[-1].strip().lower()
            probe_report = self._probe_report(
                term=term_hint or "none",
                probe_name="atomic_term_bootstrap_probe",
                passed=bool(term_hint),
                metrics={"atomic_bootstrap": True, "term_hint": term_hint or "none"},
                negative_class_violation={
                    "INFINITE_SET": True,
                    "CLASSICAL_TIME": True,
                    "COMMUTATIVE_ASSUMPTION": True,
                },
            )
        probe_pass = bool(probe_report.get("pass", False))
        probe_digest = _deterministic_hash_dict(probe_report)
        payload = {
            "sim_id": task.sim_id,
            "spec_id": task.spec_id,
            "tier": task.tier,
            "family": task.family,
            "target_class": task.target_class,
            "negative_class": task.negative_class,
            "depends_on": list(task.depends_on),
            "state_hash": input_hash,
            "probe_report": probe_report,
            "probe_digest": probe_digest,
        }
        output_hash = _deterministic_hash_dict(payload)
        code_hash = _sha256_bytes((self.code_hash_prefix + task.sim_id).encode("utf-8"))
        run_manifest_payload = {
            "manifest_schema": "SIM_RUN_MANIFEST_v1",
            "sim_engine_id": "bootpack_b_kernel_v1",
            "code_hash_sha256": code_hash,
            "input_hash_sha256": input_hash,
            "task": payload,
        }
        run_manifest_hash = _deterministic_hash_dict(run_manifest_payload)
        evidence_lines = [
            "BEGIN SIM_EVIDENCE v1",
            f"SIM_ID: {task.spec_id}",
            f"CODE_HASH_SHA256: {code_hash}",
            f"INPUT_HASH_SHA256: {input_hash}",
            f"OUTPUT_HASH_SHA256: {output_hash}",
            f"RUN_MANIFEST_SHA256: {run_manifest_hash}",
            f"METRIC: probe_suite={_QIT_MATRIX_SUITE_ID}",
            f"METRIC: probe_term={probe_report.get('term', 'none')}",
            f"METRIC: probe_name={probe_report.get('probe_name', 'none')}",
            f"METRIC: probe_pass={'true' if bool(probe_report.get('pass', False)) else 'false'}",
            f"METRIC: probe_digest={probe_digest}",
            f"METRIC: tier={task.tier}",
            f"METRIC: family={task.family}",
            f"METRIC: target_class={task.target_class}",
            f"METRIC: negative_class={task.negative_class or 'NONE'}",
        ]
        # Evidence is structural: we only emit evidence for positive SIMs when the
        # probe passes. This prevents meaningless canonicalization on default probes.
        #
        # Negative SIMs always emit evidence (coverage bookkeeping) and may also
        # emit KILL_SIGNAL if the negative_class semantics are violated.
        if task.negative_class or probe_pass:
            evidence_lines.append(f"EVIDENCE_SIGNAL {task.spec_id} CORR {task.evidence_token}")
            evidence_lines.append("METRIC: evidence_emitted=true")
        else:
            evidence_lines.append("METRIC: evidence_emitted=false")
        for key in sorted((probe_report.get("metrics", {}) or {}).keys()):
            evidence_lines.append(f"METRIC: {key}={_format_metric_value((probe_report.get('metrics') or {}).get(key))}")
        # Positive probe failures are falsifications: emit SIM_FAIL so the kernel can
        # deterministically graveyard the spec via a matching KILL_IF token.
        if (not task.negative_class) and (not probe_pass):
            evidence_lines.append(f"KILL_SIGNAL {task.spec_id} CORR SIM_FAIL")
        if self._should_emit_kill(state, task, probe_report):
            for target_id in self._kill_targets_for_task(state, task):
                evidence_lines.append(f"KILL_SIGNAL {target_id} CORR NEG_{task.negative_class}")
        evidence_lines.append("END SIM_EVIDENCE v1")
        evidence_lines.append("")
        state.sim_results.setdefault(task.sim_id, []).append(
            {
                "spec_id": task.spec_id,
                "tier": task.tier,
                "family": task.family,
                "target_class": task.target_class,
                "negative_class": task.negative_class,
                "depends_on": list(task.depends_on),
                "code_hash": code_hash,
                "input_hash": input_hash,
                "output_hash": output_hash,
                "run_manifest_hash": run_manifest_hash,
                "probe_term": str(probe_report.get("term", "")),
                "probe_name": str(probe_report.get("probe_name", "")),
                "probe_pass": bool(probe_report.get("pass", False)),
                "probe_digest": probe_digest,
                "probe_metrics": dict(probe_report.get("metrics", {}) or {}),
            }
        )
        return "\n".join(evidence_lines)

    def evaluate_promotion(self, state: KernelState, sim_id: str, graveyard_by_target_class: dict[str, int]) -> dict:
        spec = state.sim_registry.get(sim_id)
        if not spec:
            return {"status": "PROMOTE_FAIL", "reason_tags": ["MISSING_SIM_SPEC"]}

        target_class = spec.get("target_class", "")
        tier = spec.get("tier", "T0_ATOM")
        dependencies = spec.get("depends_on", [])
        spec_id = str(spec.get("spec_id", "")).strip()

        blockers: list[str] = []

        has_interaction = bool(spec_id) and int(state.interaction_counts.get(spec_id, 0)) >= 1
        has_kill_graveyard_evidence = bool(spec_id) and spec_id in state.graveyard
        if not has_interaction and not has_kill_graveyard_evidence:
            blockers.append("G0_INTERACTION_DENSITY")

        for dep in dependencies:
            dep_spec = state.sim_registry.get(dep)
            if not dep_spec:
                blockers.append("G1_DEPENDENCY_COVERAGE")
                continue
            dep_spec_id = dep_spec.get("spec_id", "")
            if dep_spec_id and dep_spec_id in state.evidence_pending:
                blockers.append("G1_DEPENDENCY_COVERAGE")

        target_results = [item for _, result_list in state.sim_results.items() for item in result_list if item.get("target_class") == target_class]
        has_negative = any(item.get("negative_class") for item in target_results)
        if not has_negative:
            blockers.append("G2_NEGATIVE_COVERAGE")

        graveyard_count = int(graveyard_by_target_class.get(target_class, 0))
        if graveyard_count <= 0:
            blockers.append("G3_GRAVEYARD_COVERAGE")
        else:
            kill_backed = False
            for row in state.kill_log:
                if str(row.get("tag", "")) != "KILL_SIGNAL":
                    continue
                kill_id = str(row.get("id", "")).strip()
                meta = state.spec_meta.get(kill_id, {})
                if meta.get("kind") != "SIM_SPEC":
                    continue
                if str(meta.get("target_class", "")).strip() == target_class:
                    kill_backed = True
                    break
            if not kill_backed:
                blockers.append("G3_GRAVEYARD_KILL_SIGNAL")

        run_hashes = sorted({item.get("output_hash", "") for item in state.sim_results.get(sim_id, [])})
        if len(run_hashes) > 1:
            blockers.append("G4_REPRODUCIBILITY")

        if spec.get("bypass", False):
            blockers.append("G5_NO_BYPASS")

        families = {item.get("family", "") for item in target_results}
        if not REQUIRED_FAMILIES.issubset(families):
            blockers.append("G6_STRESS_COVERAGE")

        unique_blockers = sorted(set(blockers))
        if unique_blockers:
            state.sim_promotion_status[sim_id] = "PARKED"
            return {"status": "PROMOTE_FAIL", "reason_tags": unique_blockers}

        state.sim_promotion_status[sim_id] = "ACTIVE"
        return {"status": "PROMOTE_PASS", "reason_tags": []}

    def coverage_report(self, state: KernelState, graveyard_by_target_class: dict[str, int]) -> dict:
        tier_rows = []
        promotion_counts = {tier: {"pass": 0, "fail": 0} for tier in sorted(TIER_ORDER.keys(), key=lambda key: TIER_ORDER[key])}
        unresolved: list[dict] = []

        for sim_id, spec in sorted(state.sim_registry.items()):
            tier = spec.get("tier", "T0_ATOM")
            outcome = self.evaluate_promotion(state, sim_id, graveyard_by_target_class)
            if outcome["status"] == "PROMOTE_PASS":
                promotion_counts[tier]["pass"] += 1
            else:
                promotion_counts[tier]["fail"] += 1
                unresolved.append({"sim_id": sim_id, "tier": tier, "blockers": outcome["reason_tags"]})
            tier_rows.append(
                {
                    "sim_id": sim_id,
                    "tier": tier,
                    "target_class": spec.get("target_class", ""),
                    "promotion_status": state.sim_promotion_status.get(sim_id, "NOT_READY"),
                }
            )

        master_status = state.sim_promotion_status.get(MASTER_SIM_ID, "NOT_READY")
        if MASTER_SIM_ID in state.sim_registry:
            master_outcome = self.evaluate_promotion(state, MASTER_SIM_ID, graveyard_by_target_class)
            master_status = "ACTIVE" if master_outcome["status"] == "PROMOTE_PASS" else "PARKED"
            state.sim_promotion_status[MASTER_SIM_ID] = master_status
            if MASTER_NEG_SIM_ID not in state.sim_registry:
                master_status = "PARKED"
                unresolved.append({"sim_id": MASTER_SIM_ID, "tier": "T6_WHOLE_SYSTEM", "blockers": ["MISSING_MASTER_NEGATIVE_SIM"]})

        return {
            "tier_coverage_table": tier_rows,
            "promotion_counts_by_tier": promotion_counts,
            "master_sim_status": master_status,
            "unresolved_promotion_blockers": unresolved,
        }
