import re
from pathlib import Path
from system_v4.skills.a2_graph_refinery import A2GraphRefinery
from system_v4.skills.v4_graph_builder import GraphNode, GraphEdge

def parse_clusters(md_path: Path):
    if not md_path.exists():
        return []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    
    clusters = []
    current_cluster = None
    
    for line in lines:
        match = re.search(r'`(SKILL_CLUSTER::[a-zA-Z0-9_\-]+)`', line)
        if match:
            if current_cluster:
                clusters.append(current_cluster)
            current_cluster = {
                "id": match.group(1),
                "members": [],
                "properties": {"source_doc": md_path.name}
            }
            continue
            
        if current_cluster:
            # Capture properties like `- `name`: `something``
            prop_match = re.search(r'-\s+`([^`]+)`:\s+`([^`]+)`', line)
            if prop_match:
                current_cluster["properties"][prop_match.group(1)] = prop_match.group(2)
            
            # Capture any other backticked skill names if indented
            # e.g. "  - `a2-brain-surface-refresher`"
            # Ignore standard English words
            items = re.findall(r'-\s+`([a-z0-9\-]+)`', line)
            for item in items:
                if item not in ["name", "status", "source_family", "cluster_type", "integration_state"]:
                    current_cluster["members"].append(item)
                    
    if current_cluster:
        clusters.append(current_cluster)
        
    return clusters

def run_materialization(repo_root: str):
    root = Path(repo_root)
    refinery = A2GraphRefinery(str(root))
    
    # 1. Parse specs
    specs = [
        root / "system_v4/specs/03_V4_SKILL_CLUSTER_SPEC.md",
        root / "system_v4/specs/04_V4_IMPORTED_SKILL_CLUSTER_MAP.md"
    ]
    
    all_clusters = []
    for spec in specs:
        all_clusters.extend(parse_clusters(spec))
        
    # 2. Materialize
    added_nodes = 0
    added_edges = 0
    
    for c in all_clusters:
        cid = c["id"]
        
        # Pop specific reserved fields to avoid kwarg collisions in v4_graph_builder
        node_name = c["properties"].pop("name", cid.replace("SKILL_CLUSTER::", "").replace("-", " ").title())
        node_layer = c["properties"].pop("layer", "L1_SKILL_CLUSTERS")
        node_type = c["properties"].pop("node_type", "SKILL_CLUSTER")
        
        # Add the cluster node
        refinery.builder.add_node(GraphNode(
            id=cid,
            node_type=node_type,
            name=node_name,
            description=f"Skill Cluster materialized from {c['properties'].get('source_doc')}",
            layer="L1_SKILL_CLUSTERS",
            trust_zone="A2_LOW_CONTROL",
            authority="CROSS_VALIDATED",
            properties=c["properties"]
        ))
        added_nodes += 1
        
        # Add member edges
        for member in set(c["members"]):
            skill_name = member.replace("-", "_").lower()
            target_id = f"SKILL::{member}"
            if not refinery.builder.node_exists(target_id):
                alt_target = f"SKILL::{skill_name}"
                if refinery.builder.node_exists(alt_target):
                    target_id = alt_target
                    
            # Add edge: SKILL -> SKILL_CLUSTER (MEMBER_OF)
            refinery.builder.add_edge(GraphEdge(
                source_id=target_id, target_id=cid,
                relation="MEMBER_OF", attributes={"discovered_in": c['properties'].get('source_doc', "unknown")}
            ))
            added_edges += 1
                
    refinery._save()
    print(f"Materialized {added_nodes} SKILL_CLUSTER nodes and {added_edges} MEMBER_OF edges natively.")

if __name__ == "__main__":
    run_materialization(str(Path(__file__).resolve().parents[2]))
