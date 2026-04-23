#!/usr/bin/env python3
"""
Axis 6 Precedence Check SIM
===========================
Formally tests and locks the Action Precedence (Axis 6) mapping for all 16 engine stages.

"DOWN (Topology-First): Topology precedes Operator -> Absorptive (-) mode."
"UP (Operator-First): Operator precedes Topology -> Emissive (+) mode."

1) Validates exact +/- assignment based on syntax mapping.
2) Proves there are exactly 8 UP and 8 DOWN mappings enabling 720 degree balanced closure.
3) Prevents "Bit" terminology semantic drift by formalizing Axis 6.
"""

import json
import os
import sys
from datetime import datetime, UTC

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from proto_ratchet_sim_runner import EvidenceToken

def parse_axis_6_precedence(stage_name):
    """
    Parses the Action Precedence (Axis 6) mapping based on the name.
    If the first two chars are Topology (Ne, Si, Se, Ni), it is DOWN / Absorptive (-).
    If the first two chars are Operator (Ti, Te, Fi, Fe), it is UP / Emissive (+).
    """
    topologies = ["Ne", "Si", "Se", "Ni"]
    operators = ["Ti", "Te", "Fi", "Fe"]
    
    first_two = stage_name[:2]
    last_two = stage_name[2:]
    
    if first_two in topologies and last_two in operators:
        return "DOWN", "-", last_two
    elif first_two in operators and last_two in topologies:
        return "UP", "+", first_two
    else:
        raise ValueError(f"Invalid stage grammar: {stage_name}")

def sim_axis_6_precedence():
    print(f"\n{'='*60}")
    print(f"AXIS 6 PRECEDENCE — CHIRALITY ALIGNMENT SIM")
    print(f"{'='*60}")

    type_1 = [
        "NeTi", "FiNe",   # Ne Topology
        "FeSi", "SiTe",   # Si Topology
        "TiSe", "SeFi",   # Se Topology
        "NiFe", "TeNi"    # Ni Topology
    ]

    type_2 = [
        "NeFi", "TiNe",   # Ne Topology
        "TeSi", "SiFe",   # Si Topology
        "FiSe", "SeTi",   # Se Topology
        "NiTe", "FeNi"    # Ni Topology
    ]

    total_stages = type_1 + type_2
    
    ups = 0
    downs = 0
    
    mapping_results = []
    
    print("Testing Non-Commutative Parse Tree:")
    for stage in total_stages:
        precedence, sign, operator = parse_axis_6_precedence(stage)
        mapping_results.append({
            "stage": stage,
            "axis_6": precedence,
            "sign": sign,
            "operator": operator
        })
        print(f"  [{stage}] -> {precedence} ➔ {sign}{operator}")
        if precedence == "UP": ups += 1
        if precedence == "DOWN": downs += 1

    tokens = []
    
    if ups == 8 and downs == 8:
        print("\n  ✓ PASS: Axis 6 Precedence is perfectly globally balanced (8 UP, 8 DOWN).")
        tokens.append(EvidenceToken(
            token_id="E_SIM_AXIS6_PRECEDENCE_OK",
            sim_spec_id="S_SIM_AXIS6_PRECEDENCE_V1",
            status="PASS",
            measured_value=1.0
        ))
    else:
        print(f"\n  ✗ FAIL: Imbalance detected! UP={ups}, DOWN={downs}")
        tokens.append(EvidenceToken(
            token_id="",
            sim_spec_id="S_SIM_AXIS6_PRECEDENCE_V1",
            status="KILL",
            measured_value=0.0,
            kill_reason="AXIS_6_IMBALANCE"
        ))

    out_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "a2_state", "sim_results", "axis_6_precedence_results.json"
    )
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    
    with open(out_file, "w") as f:
        json.dump({
            "schema": "SIM_EVIDENCE_v1",
            "file": "axis_6_precedence_sim.py",
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "evidence_ledger": [t.__dict__ for t in tokens],
            "measurements": mapping_results
        }, f, indent=2)

    return tokens

if __name__ == "__main__":
    sim_axis_6_precedence()
