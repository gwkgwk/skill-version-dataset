"""Offline data/provenance verification using stdlib. Never imports sample code."""
import csv
import hashlib
import json
import urllib.parse
from pathlib import Path

ROOT=Path(__file__).resolve().parent
HEAD='f7d28b1a9de4eb33d552529cf79d1065d765f6c3'
INITIAL='eb431f4f9d855f558fce20fd7de098a0423b6160'

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def sha(data):return hashlib.sha256(data).hexdigest()
def git_hash(kind,data):return hashlib.sha1(kind.encode()+b' '+str(len(data)).encode()+b'\0'+data).hexdigest()

def tree_hash(entries):
    entries=sorted(entries,key=lambda e:(e['path']+('/' if e['type']=='tree' else '')).encode())
    data=b''.join(e['mode'].lstrip('0').encode()+b' '+e['path'].encode()+b'\0'+bytes.fromhex(e['sha']) for e in entries)
    return git_hash('tree',data)

def verify_tree(tree):
    assert not tree.get('truncated')
    for prefix,digest in [('',tree['sha'])]+[(e['path']+'/',e['sha']) for e in tree['tree'] if e['type']=='tree']:
        direct=[{**e,'path':e['path'][len(prefix):]} for e in tree['tree'] if e['path'].startswith(prefix) and '/' not in e['path'][len(prefix):]]
        assert tree_hash(direct)==digest,(prefix,digest)

def normalized(items):
    return {('SKILL.md' if p.lower()=='skill.md' else p):digest for p,digest in items.items() if p!='_meta.json' and '.DS_Store' not in p.split('/') and '__pycache__' not in p.split('/') and not p.endswith('.pyc')}

def verify_source(directory):
    tree=load(directory/'tree.json');verify_tree(tree)
    commit=load(directory/'commit.json')
    assert commit['tree']['sha']==tree['sha']
    for path in directory.rglob('*'):
        if path.is_file() and path.name not in ('tree.json','commit.json'):
            relative=path.relative_to(directory).as_posix()
            item=next(e for e in tree['tree'] if e['path']==relative)
            assert git_hash('blob',path.read_bytes())==item['sha'],relative
    return tree

def main():
    rows=[json.loads(line) for line in (ROOT/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==len({r['id'] for r in rows})==len({r['skill_id'] for r in rows})==13
    csv_rows=list(csv.DictReader((ROOT/'updates_index.csv').open(encoding='utf-8-sig')))
    assert [(r['id'],r['old_commit'],r['new_commit']) for r in csv_rows]==[(r['id'],r['old_commit'],r['new_commit']) for r in rows]
    for ref in (HEAD,INITIAL):
        directory=ROOT/'source/original_benchmark'/ref
        verify_source(directory)
        assert load(directory/'commit.json')['sha']==ref
    current=list(csv.DictReader((ROOT/'source/original_benchmark'/HEAD/'data/malicious_skills.csv').open(encoding='utf-8-sig')))
    originals={(r['source'],r['repo'],r['skill_name']):r for r in current}
    assert len(originals)==157
    consolidated=ROOT/'source/consolidated_benchmark'
    source_tree=verify_source(consolidated)
    archive_entry=next(e for e in source_tree['tree'] if e['path']=='packages/SRC002_packages.tar.gz')
    assert archive_entry['sha']=='14f605bbc785779c2733f69c1010709e999ea4c5'
    labels={r['benchmark_id']:r for r in csv.DictReader((consolidated/'metadata/benchmark_manifest.csv').open(encoding='utf-8-sig'))}
    packages=list(csv.DictReader((consolidated/'packages/package_manifest.csv').open(encoding='utf-8-sig')))
    historical={ (r['source'],r['repo'],r['skill_name']):r for r in load(ROOT/'source/selected_historical_source_rows.json')}
    assert set(historical)=={tuple(r['benchmark_source_key']) for r in rows}
    file_count=byte_count=0;new_primary_hashes=[]
    for row in rows:
        directory=ROOT/row['local_directory']
        assert load(directory/'metadata.json')==row
        assert row['version_kind']=='git_commit_snapshot' and row['old_version']=='git:'+row['old_commit'] and row['new_version']=='git:'+row['new_commit']
        assert row['published_release_version_change_confirmed'] is False
        assert row['old_security_label'] is None and row['update_security_label'] is None
        assert row['first_malicious_introduction_confirmed'] is False and row['global_first_malicious_version'] is None
        assert originals[tuple(row['benchmark_source_key'])]['classification']=='malicious'
        url=urllib.parse.urlparse(historical[tuple(row['benchmark_source_key'])]['url'])
        assert url.hostname=='github.com' and '/'.join(url.path.strip('/').split('/')[:2]).lower()==row['origin_repository'].lower()
        proofs=load(directory/'git_path_proofs.json')
        assert proofs['new']['commit']['parents'][0]['sha']==row['old_commit']
        inventories=load(directory/'files.json')
        for side in ('old','new'):
            tree=load(directory/(side+'_tree.json'));verify_tree(tree)
            proof=proofs[side];commit=proof['commit']
            assert commit['sha']==row[side+'_commit']
            digest=commit['tree']['sha']
            assert '/'.join(step['component'] for step in proof['steps'])==row['origin_path']
            for step in proof['steps']:
                node=step['tree']
                assert not node.get('truncated') and node['sha']==digest and tree_hash(node['tree'])==digest
                digest=next(e['sha'] for e in node['tree'] if e['path']==step['component'] and e['type']=='tree')
            assert digest==tree['sha']==proof['leaf_tree_sha']
            blobs={e['path']:e for e in tree['tree'] if e['type']=='blob'}
            assert set(blobs)=={f['path'] for f in inventories[side]}
            actual={p.relative_to(directory/side).as_posix() for p in (directory/side).rglob('*') if p.is_file()}
            assert actual==set(blobs)
            for item in inventories[side]:
                path=directory/side/item['path'];assert not path.is_symlink()
                data=path.read_bytes()
                assert len(data)==item['size'] and sha(data)==item['sha256']
                assert git_hash('blob',data)==item['git_blob_sha1']==blobs[item['path']]['sha']
                assert item['mode']==blobs[item['path']]['mode']
                file_count+=1;byte_count+=len(data)
        operations=[normalized({f['path']:f['git_blob_sha1'] for f in inventories[s]}) for s in ('old','new')]
        assert 'SKILL.md' in operations[0] and 'SKILL.md' in operations[1]
        changed=[p for p in sorted(set(operations[0])|set(operations[1])) if operations[0].get(p)!=operations[1].get(p)]
        assert changed and changed==row['operational_changed_files']
        expected=normalized({f['path']:f['git_blob_sha1'] for f in load(directory/'source_package_files.json')})
        assert operations[1]==expected
        primary=next(f for f in inventories['new'] if f['path'].lower()=='skill.md')
        new_primary_hashes.append(primary['sha256'])
        proof=load(directory/'additional_label_proof.json')
        label=proof['benchmark_record']
        assert label==labels[label['benchmark_id']] and label['label']=='1' and 'SRC002' in label['source_ids']
        assert primary['sha256']==label['exact_hash']
        assert proof['source_archive_git_blob_sha1']==archive_entry['sha']
        for package in proof['package_records']:
            assert package in packages and package['source_id']=='SRC002' and package['sanitized']=='no'
            assert package['package_relative_path']==row['source_package_prefix']
            assert package['package_archive_sha256']==row['source_archive_sha256']
        for name,info in row['diffs'].items():
            data=(directory/name).read_bytes()
            assert len(data)==info['bytes'] and sha(data)==info['sha256']
        assert row['diffs']['package.diff']['bytes']>0
    assert file_count==78 and byte_count==746621 and len(set(new_primary_hashes))==13
    excluded=load(ROOT/'unverified/records.json')
    assert len(excluded)==144
    excluded_keys={tuple(r['source_key']) for r in excluded}
    accepted_keys={tuple(r['benchmark_source_key']) for r in rows}
    assert not excluded_keys & accepted_keys and excluded_keys | accepted_keys==set(originals)
    assert not (ROOT/'pairs/MASC-0014').exists()
    assert not list(ROOT.rglob('SRC002_packages.tar.gz'))
    relocation=load(ROOT/'audit/sample_relocation/receipt.json')
    old=load(ROOT/'audit/sample_relocation/old_tree.json');new=load(ROOT/'audit/sample_relocation/new_tree.json')
    verify_tree(old);verify_tree(new)
    assert old['sha']==new['sha'] and relocation['changed_file_count']==0
    dedup=load(ROOT/'audit/deduplication.json')
    assert len(dedup['prior_release_version_skill_ids'])==24 and len(dedup['new_origin_identities'])==13
    assert not set(new_primary_hashes) & set(dedup['prior_primary_sha256_to_skill_id'])
    summary=load(ROOT/'summary.json')
    assert summary['original_files']==file_count and summary['original_bytes']==byte_count
    assert sum(r['change_scope']=='README_only' for r in rows)==1
    manifest=ROOT/'MANIFEST.sha256'
    if manifest.exists():
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest,name=line.split('  ',1)
            assert sha((ROOT/name).read_bytes())==digest,name
    report={'passed':True,'method':'offline standard-library checks; no sample execution','accepted_git_commit_version_pairs':13,'new_registry_release_version_pairs':0,'complete_snapshots':26,'original_files':file_count,'original_bytes':byte_count,'excluded_records':144,'only_README_changed':1,'first_malicious_introductions_confirmed':0,'checks':['original Git blob hashes, SHA-256 and complete directory inventory','Git directory trees reconstructed','commit root trees to Skill paths reconstructed','exact first-parent API lineage','source malicious CSV membership','whole recorded source-package inventory equality','independent frozen malicious primary-text SHA-256 equality','actual non-metadata changes and diff hashes','source metadata Git blob membership','candidate partition and previous-primary-hash deduplication','controlled sample relocation excluded','manifest when present'],'limits':['Full SRC002 archive integrity was checked at collection; archive intentionally omitted and not re-read offline','Full historical ecosystem CSV hash receipts and selected provenance rows are provided; full CSV not included','No independent runtime or first-malicious-introduction confirmation']}
    if not manifest.exists():(ROOT/'verification_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
