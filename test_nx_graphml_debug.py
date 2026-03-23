import sys
import networkx as nx
from system_v4.skills.v4_graph_builder import SystemGraphBuilder

print("Starting debug...")
builder = SystemGraphBuilder("/Users/joshuaeisenhart/Desktop/Codex Ratchet")
builder.load_graph_artifacts(version_label="a2_refinery")

G = builder._export_graph_for_graphml()

print("Graph loaded. Checking nodes...")
for n, data in G.nodes(data=True):
    for k, v in data.items():
        if isinstance(v, str):
            try:
                from lxml import etree
                etree.Element('test').text = v
            except ValueError as e:
                print(f"BAD NODE {n} ATTR {k}: {repr(v)}")

print("Checking edges...")
for u, v, data in G.edges(data=True):
    for k, val in data.items():
        if isinstance(val, str):
            try:
                from lxml import etree
                etree.Element('test').text = val
            except ValueError as e:
                print(f"BAD EDGE {u}->{v} ATTR {k}: {repr(val)}")

print("Done checking.")
