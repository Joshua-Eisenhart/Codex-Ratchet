from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


WIKI_PROBE_PATH = Path('/Users/joshuaeisenhart/wiki/tools/wiki_probe.py')


def load_module():
    spec = importlib.util.spec_from_file_location('wiki_probe', WIKI_PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_probe_wiki_counts_only_public_page_dirs(tmp_path):
    module = load_module()
    (tmp_path / 'entities').mkdir()
    (tmp_path / 'concepts').mkdir()
    (tmp_path / 'comparisons').mkdir()
    (tmp_path / 'queries').mkdir()
    (tmp_path / 'raw').mkdir()
    (tmp_path / 'concepts' / '_archive').mkdir()
    (tmp_path / 'concepts' / '_meta').mkdir()

    (tmp_path / 'index.md').write_text('# Wiki Index\n\nTotal pages: 4\n- [[entity-a]]\n- [[concept-a]]\n- [[comparison-a]]\n- [[query-a]]\n', encoding='utf-8')
    (tmp_path / 'log.md').write_text('# log\n', encoding='utf-8')
    (tmp_path / 'SCHEMA.md').write_text('# schema\n', encoding='utf-8')
    (tmp_path / 'entities' / 'entity-a.md').write_text('[[concept-a]]\n', encoding='utf-8')
    (tmp_path / 'concepts' / 'concept-a.md').write_text('[[entity-a]]\n', encoding='utf-8')
    (tmp_path / 'comparisons' / 'comparison-a.md').write_text('[[concept-a]]\n', encoding='utf-8')
    (tmp_path / 'queries' / 'query-a.md').write_text('[[concept-a]]\n', encoding='utf-8')
    (tmp_path / 'raw' / 'raw-note.md').write_text('[[entity-a]]\n', encoding='utf-8')
    (tmp_path / 'concepts' / '_archive' / 'old.md').write_text('[[entity-a]]\n', encoding='utf-8')
    (tmp_path / 'concepts' / '_meta' / 'meta.md').write_text('[[entity-a]]\n', encoding='utf-8')

    payload = module.probe_wiki(tmp_path)

    assert payload['page_count'] == 4
    assert payload['index_header_count'] == 4
    assert payload['missing_pages'] == []
    assert payload['broken_links'] == []


def test_probe_wiki_reports_conservative_malformed_wikilinks(tmp_path):
    module = load_module()
    for dirname in ['entities', 'concepts', 'comparisons', 'queries']:
        (tmp_path / dirname).mkdir()

    (tmp_path / 'index.md').write_text('# Wiki Index\n\nTotal pages: 1\n- [[concept-a]]\n', encoding='utf-8')
    (tmp_path / 'log.md').write_text('# log\n', encoding='utf-8')
    (tmp_path / 'concepts' / 'concept-a.md').write_text('[[[bad-link]]]\n[[]]\n', encoding='utf-8')

    payload = module.probe_wiki(tmp_path)

    malformed = payload.get('malformed_wikilinks', [])
    assert len(malformed) >= 2
    assert any(item['pattern'] == 'triple_bracket' for item in malformed)
    assert any(item['pattern'] == 'empty_wikilink' for item in malformed)


def test_probe_wiki_cli_writes_json_output(tmp_path):
    module = load_module()
    (tmp_path / 'entities').mkdir()
    (tmp_path / 'concepts').mkdir()
    (tmp_path / 'comparisons').mkdir()
    (tmp_path / 'queries').mkdir()
    (tmp_path / 'index.md').write_text('# Wiki Index\n\nTotal pages: 1\n- [[concept-a]]\n', encoding='utf-8')
    (tmp_path / 'log.md').write_text('# log\n', encoding='utf-8')
    (tmp_path / 'concepts' / 'concept-a.md').write_text('body\n', encoding='utf-8')

    out = tmp_path / 'probe.json'
    payload = module.probe_wiki(tmp_path, output_path=out)

    written = json.loads(out.read_text(encoding='utf-8'))
    assert written['page_count'] == payload['page_count'] == 1
