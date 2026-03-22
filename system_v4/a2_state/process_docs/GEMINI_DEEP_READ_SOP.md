# Gemini Deep-Read Cross-Validation SOP
**TARGET:** Any LLM Agent executing the manual Deep-Read pass.

## Mission Context
Claude previously ingested ~3,600 files using a "shallow" batch script that only read the first 800 characters and auto-generated poor concepts.
Your job is to read the FULL files, extract deep formal constraints/Architectures, and inject them into the graph to validate and enrich it.

## Execution Rules
1. Do not reverse engineer the system or write custom extraction scripts from scratch.
2. Read the target document using your `view_file` tool.
3. Use the exact Python ingestion snippet provided below to push the concepts to the graph.

## Step-by-Step Cycle
For each document in the queue:

**Step 1:** Read the document fully (`view_file`).
**Step 2:** Formulate 3-8 high-value concepts (constraints, architectures, mechanics).
**Step 3:** Use `run_command` with this EXACT Python shell snippet to ingest the concepts:

```bash
cd "/Users/joshuaeisenhart/Desktop/Codex Ratchet" && python3 -c "
import sys
sys.path.insert(0, '.')
from system_v4.skills.a2_graph_refinery import A2GraphRefinery

r = A2GraphRefinery('.')
sid = r.start_session('GEMINI_DEEP_READ_PASS')

# Inject you extracted concepts here
concepts = [
    {
        'name': 'concept_name_here',
        'description': 'Detailed formal description here.',
        'tags': ['tag1', 'tag2', 'deep_read'],
        'authority': 'CANON' # Must be CANON for specs/fuel, DRAFT for work dirs
    },
    # Add more concepts...
]

r.process_extracted('/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/YOUR_FILE_NAME.md', concepts)

r.log_finding('Deep-read extraction completed for YOUR_FILE_NAME.md')
r.end_session()
"
```

**Step 4:** Move on to the next document in the queue. Do not overthink it! Just read, formulate, and run the snippet.
