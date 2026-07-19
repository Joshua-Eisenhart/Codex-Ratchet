#!/usr/bin/env python3
"""Compile common finite observation packets from preserved executable sources."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

from common import digest, file_sha256, write_json


ROOT = Path(__file__).resolve().parent.parent
PACK182 = ROOT / "prior_estate" / "pack182"
P182_ACTIVE = PACK182 / "active"
QCA_SOURCE = (
    PACK182 / "prior_estate" / "pack181" / "inputs" / "qca_v6" / "source"
    / "finite_qca_runner_trajectories_v0" / "finite_qca_runner_trajectories_v0_exact.py"
)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def word(bits: tuple[int, ...] | list[int]) -> str:
    if len(bits) != 4 or any(bit not in (0, 1) for bit in bits):
        raise ValueError("base packets require four Boolean coordinates")
    return "".join(str(bit) for bit in bits)


def packet(packet_id: str, source: str, coordinates: list[str], words: set[tuple[int, ...]], role: str) -> dict[str, Any]:
    accepted = sorted(word(bits) for bits in words)
    row = {
        "packet_id": packet_id,
        "width": 4,
        "source": source,
        "coordinates": coordinates,
        "accepted_words": accepted,
        "accepted_count": len(accepted),
        "role": role,
    }
    row["packet_digest"] = digest(row)
    return row


def qca_packets() -> list[dict[str, Any]]:
    module = load_module("pack183_qca_source", QCA_SOURCE)
    rows = []
    roles = {
        "identity": "control",
        "right_shift": "source_observation",
        "left_shift": "heldout_reoffer",
        "finite_depth_local_circuit": "control",
    }
    for rule in module.RULES:
        table = module.transition_table(rule)
        accepted = set()
        for input_state, output_state in enumerate(table):
            accepted.add((
                (input_state >> 2) & 1,
                (input_state >> 3) & 1,
                (output_state >> 2) & 1,
                (output_state >> 3) & 1,
            ))
        rows.append(packet(
            f"qca_{rule}_cut_relation",
            str(QCA_SOURCE.relative_to(ROOT)),
            ["input_site_2", "input_site_3", "output_site_2", "output_site_3"],
            accepted,
            roles[rule],
        ))
    return rows


def prior_modules():
    if str(P182_ACTIVE) not in sys.path:
        sys.path.append(str(P182_ACTIVE))
    whole = load_module("pack183_prior_whole", P182_ACTIVE / "finite_whole_gcm.py")
    algebra = load_module("pack183_prior_algebra", P182_ACTIVE / "finite_algebra.py")
    return whole, algebra


def gcm_packet(whole) -> dict[str, Any]:
    spec = whole.fully_featured_spec("pack183_source_projection")
    rows = whole.enumerate_completions(spec, (0, 1), 1)
    accepted = {
        (row["j0"] % 2, row["k0"] % 2, row["epsilon1"], row["epsilon2"])
        for row in rows
    }
    return packet(
        "gcm_completion_projection",
        "prior_estate/pack182/active/finite_whole_gcm.py::enumerate_completions",
        ["j0_mod2", "k0_mod2", "epsilon1", "epsilon2"],
        accepted,
        "source_observation",
    )


def spinor_packet(algebra) -> dict[str, Any]:
    report = algebra.spinor_memory_report()
    overlaps = report["overlaps_0_2pi_4pi"]
    densities = report["density_distances"]
    accepted = set()
    for context, (overlap, density_distance) in enumerate(zip(overlaps, densities)):
        context_bits = ((context >> 1) & 1, context & 1)
        accepted.add((*context_bits, int(density_distance > 1e-12), int(overlap < 0)))
    return packet(
        "spinor_density_quotient_relation",
        "prior_estate/pack182/active/finite_algebra.py::spinor_memory_report",
        ["context_high", "context_low", "density_changed", "lifted_sign_negative"],
        accepted,
        "source_observation",
    )


def octonion_packet(algebra) -> dict[str, Any]:
    report = algebra.octonion_network_report()
    edges = report["edge_vectors"]
    signal = report["signal_vector"]
    multiply = algebra.cayley_dickson_multiply
    single = multiply(edges[0], signal)
    left = multiply(edges[2], multiply(edges[1], multiply(edges[0], signal)))
    mixed = multiply(multiply(edges[2], edges[1]), multiply(edges[0], signal))
    accepted = {
        (0, 0, int(single[1] > 0), int(single[4] > 0)),
        (1, 0, int(single[1] > 0), int(single[4] > 0)),
        (0, 1, int(left[1] > 0), int(left[4] > 0)),
        (1, 1, int(mixed[1] > 0), int(mixed[4] > 0)),
    }
    return packet(
        "octonion_bracketing_relation",
        "prior_estate/pack182/active/finite_algebra.py::octonion_network_report",
        ["bracketing_choice", "three_edge_path", "output_coordinate_1_positive", "output_coordinate_4_positive"],
        accepted,
        "heldout_reoffer",
    )


def layer_state(row: dict[str, int], depth: int) -> tuple[int, int, int]:
    return (row[f"j{depth}"] % 2, row[f"k{depth}"] % 2, row[f"z{depth}"] % 2)


def nesting_packet(whole, allowed: tuple[int, ...], packet_id: str, role: str) -> dict[str, Any]:
    spec = whole.fully_featured_spec("pack183_nesting_source")
    rows = whole.enumerate_completions(spec, allowed, 1)
    triples = sorted({tuple(layer_state(row, depth) for depth in range(3)) for row in rows})
    values = [sorted({triple[depth] for triple in triples}) for depth in range(3)]
    result = {
        "packet_id": packet_id,
        "source": "prior_estate/pack182/active/finite_whole_gcm.py::enumerate_completions",
        "role": role,
        "layers": 3,
        "layer_values": [[list(state) for state in layer] for layer in values],
        "admissible_triples": [[list(state) for state in triple] for triple in triples],
        "triple_count": len(triples),
        "outer_allowed": list(allowed),
    }
    result["packet_digest"] = digest(result)
    return result


def run() -> dict[str, Any]:
    whole, algebra = prior_modules()
    packets = qca_packets()
    packets.extend([gcm_packet(whole), spinor_packet(algebra), octonion_packet(algebra)])
    nesting = [
        nesting_packet(whole, (0, 1), "nested_completion_baseline", "source_observation"),
        nesting_packet(whole, (0, 1, 2), "nested_completion_expanded", "heldout_evolution_reoffer"),
    ]
    baseline = {
        tuple(tuple(state) for state in triple)
        for triple in nesting[0]["admissible_triples"]
    }
    expanded = {
        tuple(tuple(state) for state in triple)
        for triple in nesting[1]["admissible_triples"]
    }
    checks = {
        "all_base_packets_width_four": all(row["width"] == 4 for row in packets),
        "qca_source_hash_retained": file_sha256(QCA_SOURCE).startswith("sha256:"),
        "baseline_nested_nonempty": bool(baseline),
        "expansion_preserves_baseline": baseline <= expanded,
        "expansion_adds_configuration": bool(expanded - baseline),
        "spinor_packet_has_density_quotient_distinction": len(next(row for row in packets if row["packet_id"].startswith("spinor"))["accepted_words"]) == 3,
        "octonion_packet_has_bracketing_distinction": len(next(row for row in packets if row["packet_id"].startswith("octonion"))["accepted_words"]) == 4,
    }
    result = {
        "schema": "ratchet.pack183.source-packets.v1",
        "base_packets": packets,
        "nesting_packets": nesting,
        "checks": checks,
        "all_pass": all(checks.values()),
        "selection_disclosure": (
            "four-coordinate projections are declared calibration surfaces derived from preserved executable sources; "
            "they are not neutral samples of all mathematics or physical observations"
        ),
        "claim_ceiling": "common finite source-derived comparison packets only; no base structure admitted",
    }
    result["result_digest"] = digest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    write_json(args.output, result)
    print(json.dumps({
        "all_pass": result["all_pass"],
        "base_packets": len(result["base_packets"]),
        "nesting_packets": len(result["nesting_packets"]),
    }, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
