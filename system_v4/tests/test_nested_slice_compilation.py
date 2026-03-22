import os
import time
from pathlib import Path
from dataclasses import asdict
import json

from system_v4.skills.v4_graph_builder import SystemGraphBuilder
from system_v4.skills.registry_types import RegistryRecord, RegistryRelation
from system_v4.skills.slice_request import SliceRequest
from system_v4.skills.slice_compiler import SliceCompiler

def _utc_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def test_slice_compilation():
    print("--- [ V4 Nested Graph Slice Compiler Test ] ---")
    workspace = Path(os.path.abspath(".")).resolve()
    
    # 1. Load the massive V4 Graph populated from the V3 scripts
    builder = SystemGraphBuilder(str(workspace))
    success = builder.load_graph_artifacts(version_label="v3_ingest_pass1")
    if not success:
        print("Failed to load V4 system graph.")
        return
        
    print(f"Loaded Master Graph with {len(builder.pydantic_model.nodes)} Nodes and {len(builder.pydantic_model.edges)} Edges.")
    
    print("\n1. Translating Master Graph into bounded RegistryRecords...")
    records = {}
    relations = {}
    
    # Set up some anchor nodes heuristically for the test
    # We'll pretend A2 is extracting a slice of the graph related just to A1 operations
    for n_id, node in builder.pydantic_model.nodes.items():
        # Inject realistic values for the slice logic
        trust = "A2_SANDBOX"
        admissibility = "PROPOSAL_ONLY"
        
        # If it's a V3 tool mapped to the A1 layer, consider it ADMITTED for A1
        if node.layer == "A1":
            trust = "A1_OWNER"
            admissibility = "ADMITTED"
            
        rec = RegistryRecord(
            schema="A2_REGISTRY_RECORD_v1",
            schema_version="1",
            registry_id=node.id,
            revision=1,
            object_family="RuntimeProcessRecord",
            object_type=node.node_type,
            layer_scope=node.layer,
            created_utc=_utc_iso(),
            updated_utc=_utc_iso(),
            status=node.status,
            source_class=node.source_class,
            trust_zone=trust,
            admissibility_state=admissibility,
            lineage_refs=tuple(node.lineage_refs),
            witness_refs=tuple(node.witness_refs),
            content_hash="mock_hash",
            attrs={}
        )
        records[node.id] = rec
        
    # Pick a few specific nodes as anchors for our slice
    # For instance 'A1_WORKER_LAUNCH_PACKET' or any a1 tools
    a1_nodes = [node_id for node_id, rec in records.items() if rec.layer_scope == "A1"][:3]
    print(f" > Selected Anchor Nodes for nested subset: {a1_nodes}")
    
    print("\n2. Initializing SliceCompiler (Fail-Closed Boundaries)...")
    compiler = SliceCompiler(records=records, relations=relations, compiler_version="v4_integration")
    
    request = SliceRequest(
        request_id="SLICE_REQ_A1_EXEC",
        slice_class="DISPATCH",
        purpose="Extract A1 working slice",
        requesting_layer="A2",
        target_layer="A1",
        anchor_refs=tuple(a1_nodes),
        must_include_refs=(),
        relation_families=(),
        boundary_refs=(),
        trust_zone="A1_OWNER",
        admissibility_floor="ADMITTED",
        lineage_mode="MIN",
        witness_mode="NONE",
        return_target="a1_state",
        stop_rule="Fail Closed"
    )
    
    print("\n3. Executing Sub-Graph Slice Extraction...")
    manifest = compiler.compile(request)
    
    # We should have a valid slice because we selected ADMITTED A1 nodes matching the A1_OWNER trust zone filter
    print(f"\n--- [ Slice Dump ] ---")
    if hasattr(manifest, 'slice_id'):
        print(f"Slice ID: {manifest.slice_id}")
        print(f"Purpose: {manifest.purpose}")
        print(f"Extracted Members: {[m.ref for m in manifest.primary_members]}")
        print(f"Terminal Path Gate: {manifest.terminal_path_status}")
    else:
        print("Slice compilation rejected!")
        print(manifest)

if __name__ == "__main__":
    test_slice_compilation()
