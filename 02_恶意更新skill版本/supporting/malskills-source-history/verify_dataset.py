"""Offline evidence verification. Does not import or execute any Skill artifact."""
import collections
import hashlib
import json
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parent
BLOCKED_BLOBS={'b4437106f47cd532bd7c2544f110c45d7a18b42e','12fee728ca9588a172c9cbefe225dfb6eb663409','7e861d5befb0dfb112562a24831552504218ae52'}
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def hash_git(data,kind):return hashlib.sha1(f'{kind} {len(data)}\0'.encode()+data).hexdigest()

def verify_tree(tree):
    children=collections.defaultdict(list)
    expected={'':tree['sha']}
    for entry in tree['tree']:
        path=PurePosixPath(entry['path']);parent=str(path.parent)
        children['' if parent=='.' else parent].append(entry)
        if entry['type']=='tree':expected[entry['path']]=entry['sha']
    def reconstruct(directory):
        entries=children[directory]
        entries.sort(key=lambda x:PurePosixPath(x['path']).name.encode()+ (b'/' if x['type']=='tree' else b''))
        data=bytearray()
        for entry in entries:
            sha=reconstruct(entry['path']) if entry['type']=='tree' else entry['sha']
            data+=entry['mode'].lstrip('0').encode()+b' '+PurePosixPath(entry['path']).name.encode()+b'\0'+bytes.fromhex(sha)
        actual=hash_git(data,'tree');assert actual==expected[directory],directory
        return actual
    reconstruct('')

def main():
    seeds=load(ROOT/'source/selected_100_seeds.json')
    assert len(seeds)==100 and all(s['benchmark_label']=='malicious' for s in seeds)
    index=[json.loads(x) for x in (ROOT/'index.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(index)==100 and len(set(r['skill_id'] for r in index))==100
    expected_ids={s['skill_id'] for s in seeds}
    assert expected_ids==set(r['skill_id'] for r in index)
    files=trees=partial=source_matches=0
    directories=set()
    for row in index:
        assert row['global_first_malicious_version'] is None and not row['global_first_introduction_confirmed']
        assert row['historical_security_label'] is None and row['update_security_label'] is None
        record=load(ROOT/row['record_path'])
        assert record['skill_id']==row['skill_id']
        for snapshot in record['snapshots']:directories.add(snapshot['directory'])
        newest=record['snapshots'][-1]
        primary=newest['primary']
        if primary['status']=='verified':
            assert primary['sha256']==row['benchmark_primary_sha256'];source_matches+=1
        else:assert row['archive_seed_primary_hash_match'] is None
        history=load(ROOT/'histories'/(row['skill_id'].replace('/','_')+'.json'))
        assert [s['commit_sha'] for s in record['snapshots']]==[h['sha'] for h in reversed(history)]
        assert len(history)<100
        parent=load(ROOT/'parent_evidence'/(row['skill_id'].replace('/','_')+'.json'))
        assert parent['status']=='directory_absent_at_existing_parent' and parent['parent_commit_exists']
    case=load(ROOT/'confirmed_archive_introductions/zaycv_clawhub/decision.json')
    directories.add(case['parent_snapshot'])
    for relative in directories:
        directory=(ROOT/relative).resolve();assert directory.is_relative_to(ROOT/'artifacts')
        snapshot=load(directory/'snapshot.json');tree=load(directory/'tree.json')
        assert not tree.get('truncated');assert snapshot['tree_sha']==tree['sha']
        inventory={f['path']:f for f in snapshot['files']}
        assert set(inventory)=={e['path'] for e in tree['tree'] if e['type']!='tree'}
        expected_paths=set()
        for entry in tree['tree']:
            if entry['type']=='tree':continue
            item=inventory[entry['path']]
            assert item['git_blob_sha1']==entry['sha'] and item['mode']==entry['mode'] and item['bytes']==entry['size']
            path=directory/'files'/item['path']
            if item['status']=='verified':
                assert item['git_blob_sha1'] not in BLOCKED_BLOBS
                assert not path.is_symlink() and path.resolve().is_relative_to(directory)
                data=path.read_bytes();assert len(data)==item['bytes']
                assert hash_git(data,'blob')==item['git_blob_sha1']
                assert hashlib.sha256(data).hexdigest()==item['sha256'];files+=1
                expected_paths.add(item['path'])
            else:
                assert not path.exists();partial+=1
        actual_paths={p.relative_to(directory/'files').as_posix() for p in (directory/'files').rglob('*') if p.is_file()}
        assert actual_paths==expected_paths
        verify_tree(tree);trees+=1
    before=load(ROOT/case['parent_snapshot']/'snapshot.json');after=load(ROOT/case['new_snapshot']/'snapshot.json')
    assert after['parents'][0]==before['commit_sha']==case['parent_commit']
    assert after['commit_sha']==case['new_commit'] and after['recorded_meta_latest']['version']=='1.0.3'
    assert before['recorded_meta_latest']['version']=='1.0.0'
    old=(ROOT/case['parent_snapshot']/'files/SKILL.md').read_text(encoding='utf-8')
    new=(ROOT/case['new_snapshot']/'files/SKILL.md').read_text(encoding='utf-8')
    assert 'github.com/Ddoy233/openclawcli' not in old and 'github.com/Ddoy233/openclawcli' in new
    assert not case['global_first_published_malicious_version_confirmed']
    def ids(path):return {json.loads(x)['skill_id'] for x in (ROOT/path).read_text(encoding='utf-8').splitlines()}
    corroborated=ids('corroborated_observations/index.jsonl');unresolved=ids('unverified/incident_or_behavior_not_corroborated.jsonl')
    assert not corroborated&unresolved and corroborated|unresolved==expected_ids
    assert ids('unverified/global_first_version_not_established.jsonl')==expected_ids
    assert ids('unverified/source_content_not_verified.jsonl')=={'zaycv/clawhub'}
    manifest=ROOT/'MANIFEST.sha256'
    if manifest.exists():
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest,relative=line.split('  ',1)
            path=(ROOT/relative).resolve();assert path.is_relative_to(ROOT)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==digest,relative
    report={'verified':True,'skills':100,'source_hash_matches':source_matches,'snapshot_tree_hashes_reconstructed':trees,'original_files_verified':files,'missing_file_occurrences_explicitly_excluded':partial,'static_ioc_corroborated_skills':len(corroborated),'unverified_incident_or_behavior_skills':len(unresolved),'global_first_versions_unknown':100,'archive_introductions_confirmed':1}
    if not manifest.exists():(ROOT/'verification_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
