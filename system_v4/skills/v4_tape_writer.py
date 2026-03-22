import json
import time
from pathlib import Path
from typing import Dict, List, Any


class V4TapeWriter:
    """
    Handles generation of explicit artifact contracts:
    - EXPORT_BLOCK: A0 -> B compiled block
    - THREAD_B_REPORT: Output from B adjudication
    - SIM_EVIDENCE_PACK: Output from SIM Holodeck
    - CAMPAIGN_TAPE.jsonl: Canonical append-only log of (EXPORT, REPORT) pairs
    """
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.campaign_tape_path = self.output_dir / "CAMPAIGN_TAPE.jsonl"
        self.export_tape_path = self.output_dir / "EXPORT_TAPE.jsonl"

    def write_export_block(self, batch_id: str, targets: List[Dict], alternatives: List[Dict]) -> str:
        """
        Formats candidates into strict EXPORT_BLOCK grammar.
        """
        block_lines = [
            f"BEGIN EXPORT_BLOCK v1",
            f"EXPORT_ID: {batch_id}",
            f"TARGET: THREAD_B_ENFORCEMENT_KERNEL",
            f"PROPOSAL_TYPE: A1_STRATEGY_BATCH",
            f"CONTENT:"
        ]

        def _format_item(item):
            lines = [
                f"  ITEM_CLASS: {item.get('item_class', 'AXIOM_HYP')}",
                f"  ID: {item.get('id')}",
                f"  KIND: {item.get('kind')}",
                f"  REQUIRES: {','.join(item.get('requires', []))}"
            ]
            for df in item.get("def_fields", []):
                lines.append(f"  DEF_FIELD: {df.get('name')}={df.get('value')} ({df.get('value_kind')})")
            for ax in item.get("asserts", []):
                lines.append(f"  ASSERT: {ax.get('token_class')} {ax.get('token')}")
            return "\n".join(lines)

        for t in targets:
            block_lines.append(_format_item(t))
            block_lines.append("")

        for a in alternatives:
            block_lines.append("  [ALTERNATIVE]")
            block_lines.append(_format_item(a))
            block_lines.append("")

        block_lines.append(f"END EXPORT_BLOCK v1\n")
        block_str = "\n".join(block_lines)

        file_path = self.output_dir / f"{batch_id}_EXPORT_BLOCK.txt"
        file_path.write_text(block_str)
        
        # Append to EXPORT_TAPE
        with open(self.export_tape_path, "a") as f:
            f.write(json.dumps({
                "batch_id": batch_id,
                "timestamp": time.time(),
                "content": block_str
            }) + "\n")

        return block_str

    def write_thread_b_report(self, batch_id: str, outcomes: List[Any], export_block_str: str) -> str:
        """
        Formats B Kernel outcomes into a THREAD_B_REPORT and appends 
        the pair (EXPORT_BLOCK, REPORT) to CAMPAIGN_TAPE.jsonl.
        """
        lines = [
            f"BEGIN THREAD_B_REPORT v1",
            f"FOR_EXPORT_ID: {batch_id}",
            f"OUTCOMES:"
        ]
        
        serializable_outcomes = []
        for o in outcomes:
            lines.append(f"  {o.candidate_id} -> {o.outcome} {o.stage_failed or ''} {o.reason_tag or ''}")
            serializable_outcomes.append({
                "candidate_id": o.candidate_id,
                "outcome": o.outcome,
                "stage": o.stage_failed,
                "reason": o.reason_tag,
                "detail": o.detail
            })
            
        lines.append(f"END THREAD_B_REPORT v1\n")
        report_str = "\n".join(lines)
        
        file_path = self.output_dir / f"{batch_id}_B_REPORT.txt"
        file_path.write_text(report_str)

        # Append pair to CAMPAIGN_TAPE
        with open(self.campaign_tape_path, "a") as f:
            f.write(json.dumps({
                "batch_id": batch_id,
                "timestamp": time.time(),
                "export_block": export_block_str,
                "thread_b_report": report_str,
                "outcomes": serializable_outcomes
            }) + "\n")
            
        return report_str

    def write_sim_evidence_pack(self, batch_id: str, results: Dict) -> str:
        """
        Records full SIM evidence for a batch.

        Each evidence item includes the canonical SIM_EVIDENCE v1 block
        (with hashes and signal lines), outcome, and detail string.
        """
        lines = [
            f"BEGIN SIM_EVIDENCE_PACK v1",
            f"BATCH_ID: {batch_id}",
            f"SURVIVOR_COUNT: {len(results)}",
            "",
        ]

        all_evidence_dicts: List[Dict] = []

        for sid, res_list in results.items():
            pass_count = sum(1 for r in res_list if getattr(r, 'outcome', '') == "PASS")
            fail_count = sum(1 for r in res_list if getattr(r, 'outcome', '') == "FAIL")
            total = len(res_list)
            lines.append(f"  SURVIVOR: {sid}  ({pass_count}/{total} PASS, {fail_count}/{total} FAIL)")

            for r in res_list:
                # Emit canonical evidence block if the result object has it
                if hasattr(r, 'to_evidence_block'):
                    lines.append(f"    {r.to_evidence_block()}")
                else:
                    lines.append(f"    SIM_ID: {getattr(r, 'sim_id', '?')}  "
                                 f"OUTCOME: {getattr(r, 'outcome', '?')}  "
                                 f"DETAIL: {getattr(r, 'detail', '')[:120]}")

                # Collect serializable dicts for JSONL sidecar
                if hasattr(r, 'to_dict'):
                    all_evidence_dicts.append(r.to_dict())
                else:
                    all_evidence_dicts.append({
                        "sim_id": getattr(r, 'sim_id', ''),
                        "outcome": getattr(r, 'outcome', ''),
                        "detail": getattr(r, 'detail', ''),
                        "target_id": getattr(r, 'target_id', sid),
                    })

            lines.append("")

        lines.append(f"END SIM_EVIDENCE_PACK v1\n")
        pack_str = "\n".join(lines)

        # Write human-readable pack
        file_path = self.output_dir / f"{batch_id}_SIM_EVIDENCE.txt"
        file_path.write_text(pack_str)

        # Write machine-readable JSONL sidecar
        jsonl_path = self.output_dir / f"{batch_id}_SIM_EVIDENCE.jsonl"
        with open(jsonl_path, "w") as f:
            for ev in all_evidence_dicts:
                f.write(json.dumps(ev) + "\n")

        return pack_str

