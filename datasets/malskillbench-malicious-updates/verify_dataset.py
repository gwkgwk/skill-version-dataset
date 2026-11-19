"""Offline structural/hash verification. Never imports or executes sample code."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def git_hash(kind, data):
    return hashlib.sha1(kind.encode() + b' ' + str(len(data)).encode() + b'\0' + data).hexdigest()

def immediate_hash(entries):
    ordered = sorted(entries, key=lambda e: (e['path'] + ('/' if e['type'] == 'tree' else '')).encode())
    data = b''.join(e['mode'].lstrip('0').encode() + b' ' + e['path'].encode() + b'\0' + bytes.fromhex(e['sha']) for e in ordered)
    return git_hash('tree', data)

def verify_tree(tree):
    assert not tree.get('truncated')
    entries = tree['tree']
    for prefix, expected in [('', tree['sha'])] + [(e['path'] + '/', e['sha']) for e in entries if e['type'] == 'tree']:
        direct = [{**e, 'path': e['path'][len(prefix):]} for e in entries if e['path'].startswith(prefix) and '/' not in e['path'][len(prefix):]]
        assert immediate_hash(direct) == expected, ('tree', prefix, expected)

def main():
    rows = [json.loads(line) for line in (ROOT/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows) == len({r['id'] for r in rows}) == len({r['skill_id'] for r in rows}) == 17
    assert len(list(csv.DictReader((ROOT/'updates_index.csv').open(encoding='utf-8-sig')))) == 17
    candidates = {r['skill_id']: r for r in read(ROOT/'source/registry_history_candidates.json')}
    rejected = read(ROOT/'unverified/index.json')
    assert len(rejected) == 4
    assert set(candidates) == {r['skill_id'] for r in rows} | {r['skill_id'] for r in rejected}
    assert not ({r['skill_id'] for r in rows} & {r['skill_id'] for r in rejected})
    commit = read(ROOT/'source/benchmark_commit.json')
    proof = read(ROOT/'source/benchmark_path_proof.json')
    assert commit['sha'] == '3548e2837adf58b96497f2c688f96beff26485da'
    expected = commit['tree']['sha']
    for step in proof:
        tree = step['tree']
        assert tree['sha'] == expected and not tree.get('truncated')
        assert immediate_hash(tree['tree']) == expected
        if step['component'] != 'sample_directories':
            expected = next(e['sha'] for e in tree['tree'] if e['path'] == step['component'])
    roots = {e['path']: e['sha'] for e in proof[-1]['tree']['tree']}
    files_count = byte_count = 0
    for row in rows:
        directory = ROOT/row['local_directory']
        assert read(directory/'metadata.json') == row
        lineage = read(directory/'lineage.json')
        assert lineage['new_commit'] == row['new_commit'] and lineage['parents'][0] == row['old_commit']
        assert row['old_version'] != row['new_version'] and row['operational_changed_files']
        assert row['old_security_label'] is None and row['update_security_label'] is None
        assert row['first_malicious_introduction_confirmed'] is False and row['global_first_malicious_version'] is None
        inventories = read(directory/'files.json')
        operational = [{e['path']: e['git_blob_sha1'] for e in inventories[side] if e['path'] != '_meta.json' and '__pycache__' not in e['path'].split('/') and not e['path'].endswith('.pyc')} for side in ('old', 'new')]
        assert operational[0] != operational[1], 'metadata-only update'
        for side in ('old', 'new'):
            tree = read(directory/(side+'_tree.json'))
            verify_tree(tree)
            blobs = {e['path']: e['sha'] for e in tree['tree'] if e['type'] == 'blob'}
            inventory = inventories[side]
            assert {e['path'] for e in inventory} == set(blobs)
            actual = {str(p.relative_to(directory/side)).replace('\\', '/') for p in (directory/side).rglob('*') if p.is_file()}
            assert actual == set(blobs)
            for item in inventory:
                path = directory/side/item['path']
                assert not path.is_symlink()
                data = path.read_bytes()
                assert len(data) == item['size']
                assert git_hash('blob', data) == item['git_blob_sha1'] == blobs[item['path']]
                assert hashlib.sha256(data).hexdigest() == item['sha256']
                files_count += 1
                byte_count += len(data)
            meta = read(directory/side/'_meta.json')
            assert meta['owner']+'/'+meta['slug'] == row['skill_id']
            assert meta['latest']['version'] == row[side+'_version']
        benchmark = read(directory/'benchmark_tree.json')
        verify_tree(benchmark)
        assert roots[row['benchmark_directory'].split('/')[-1]] == benchmark['sha']
        expected_blobs = {e['path']: e['sha'] for e in benchmark['tree'] if e['type'] == 'blob'}
        actual_blobs = {('SKILL.md' if e['path'] == 'skill.md' else e['path']): e['git_blob_sha1'] for e in inventories['new'] if e['path'] != '_meta.json'}
        assert actual_blobs == expected_blobs
        metadata_bytes = (directory/'source_registry_metadata.json').read_bytes()
        source = candidates[row['skill_id']]
        assert git_hash('blob', metadata_bytes) == source['metadata_git_blob_sha1']
        assert hashlib.sha256(metadata_bytes).hexdigest() == source['metadata_sha256']
        assert json.loads(metadata_bytes)['latest']['version'] == row['benchmark_labeled_version']
        for filename, info in row['diffs'].items():
            data = (directory/filename).read_bytes()
            assert len(data) == info['bytes'] and hashlib.sha256(data).hexdigest() == info['sha256']
        assert (directory/'package.diff').stat().st_size > 0
    assert files_count == 298 and byte_count == 1879905
    assert sum(r['new_version_is_benchmark_labeled_version'] for r in rows) == 16
    summary = read(ROOT/'summary.json')
    assert summary['original_file_occurrences'] == files_count and summary['original_bytes'] == byte_count
    manifest = ROOT/'MANIFEST.sha256'
    if manifest.exists():
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest, name = line.split('  ', 1)
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    report = {'passed': True, 'method': 'offline standard-library verification; no sample execution', 'accepted_skills': 17, 'update_pairs': 17, 'complete_snapshots': 34, 'original_files': files_count, 'original_bytes': byte_count, 'unverified_excluded': 4, 'checks': ['original Git blob and SHA-256 hashes', 'complete package tree reconstruction', 'exact first-parent lineage', 'registry identity and versions', 'benchmark commit/tree membership and full operational package equality', 'diff hashes', 'candidate partition', 'manifest hashes when present'], 'first_malicious_introduction_confirmed': 0}
    if not manifest.exists():
        (ROOT/'verification_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))

if __name__ == '__main__':
    main()
