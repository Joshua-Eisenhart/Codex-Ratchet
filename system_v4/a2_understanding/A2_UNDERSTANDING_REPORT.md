# System V4 A2 Understanding Report
Status: ACTIVE RUNTIME
Version: v1

## 1. Whole-System Understanding
The system is transitioning from v3 flat/folder structures into a v4 graph-oriented structure.
`system_v3` and `core_docs` have been indexed as physical nodes (SOURCE_MASS and SYSTEM_NODE) across various Surface Classes (ACTIVE, SUPPORT, FUEL). 

## 2. Save and Append Understanding
Save layered behaviors and append lineages are being constructed as explicitly typed Edges in the new Graph. A2 will track cross-references natively rather than just textually.

## 3. Layered Brain Understanding
A2 is explicitly separated from A1 logic. The Graph distinguishes abstract understanding (what the files mean) from the physical artifacts.

## 4. First Graph Contract
The first bounded sequence builds a graph in NetworkX parameterized by Pydantic models.
Nodes encapsulate file realities. Attributes reflect surface_class.
Edges reflect cross-references (future update).

## 5. Next Bounded External Lanes
The system needs to extract semantic relationships from the files themselves (parsing markdown files for cross-links and state lineage) and feed them to the graph extraction logic.
