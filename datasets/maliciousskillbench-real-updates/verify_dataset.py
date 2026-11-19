"""Offline hashes, completeness, provenance, version and lineage checks; no sample execution."""
import csv
import hashlib
import json
import tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent

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

def main():
    rows=[json.loads(line) for line in (ROOT/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==len({r['skill_id'] for r in rows})==len({r['id'] for r in rows})==6
    csv_rows=list(csv.DictReader((ROOT/'updates_index.csv').open(encoding='utf-8-sig')))
    assert [(r['id'],r['skill_id'],r['old_version'],r['new_version']) for r in csv_rows]==[(r['id'],r['skill_id'],r['old_version'],r['new_version']) for r in rows]
    for source in ('protect','skilllife'):
        tree=load(ROOT/'source'/source/'tree.json');verify_tree(tree)
        commit=load(ROOT/'source'/source/'commit.json')
        assert commit['tree']['sha']==tree['sha']
        for path in (ROOT/'source'/source).rglob('*'):
            if path.is_file() and path.name not in ('tree.json','commit.json'):
                relative=path.relative_to(ROOT/'source'/source).as_posix()
                entry=next(e for e in tree['tree'] if e['path']==relative)
                assert git_hash('blob',path.read_bytes())==entry['sha']
    labels={r['benchmark_id']:r for r in csv.DictReader((ROOT/'source/protect/metadata/benchmark_manifest.csv').open(encoding='utf-8-sig'))}
    packages={r['benchmark_id']:r for r in csv.DictReader((ROOT/'source/protect/packages/package_manifest.csv').open(encoding='utf-8-sig'))}
    source_tree=load(ROOT/'source/protect/tree.json')
    file_count=byte_count=0
    for row in rows:
        directory=ROOT/row['local_directory']
        assert load(directory/'metadata.json')==row
        lineage=load(directory/'lineage.json')
        assert lineage['sha']==row['new_commit'] and lineage['parents'][0]['sha']==row['old_commit']
        assert row['old_version']!=row['new_version'] and row['old_security_label'] is None
        assert row['update_security_label'] is None and row['first_malicious_introduction_confirmed'] is False
        inventories=load(directory/'files.json')
        for side in ('old','new'):
            tree=load(directory/(side+'_tree.json'));verify_tree(tree)
            blobs={e['path']:e['sha'] for e in tree['tree'] if e['type']=='blob'}
            assert set(blobs)=={e['path'] for e in inventories[side]}
            actual={p.relative_to(directory/side).as_posix() for p in (directory/side).rglob('*') if p.is_file()}
            assert actual==set(blobs)
            for item in inventories[side]:
                path=directory/side/item['path'];assert not path.is_symlink()
                data=path.read_bytes()
                assert len(data)==item['size'] and sha(data)==item['sha256']
                assert git_hash('blob',data)==item['git_blob_sha1']==blobs[item['path']]
                file_count+=1;byte_count+=len(data)
            meta=load(directory/side/'_meta.json')
            assert meta['owner'].lower()+'/'+meta['slug'].lower()==row['skill_id']
            assert meta['latest']['version']==row[side+'_version']
        operational=[normalized({e['path']:e['git_blob_sha1'] for e in inventories[s]}) for s in ('old','new')]
        changed=[p for p in sorted(set(operational[0])|set(operational[1])) if operational[0].get(p)!=operational[1].get(p)]
        assert changed and set(changed)==set(row['operational_changed_files'])
        assert operational[1]==normalized({e['path']:e['git_blob_sha1'] for e in load(directory/'benchmark_package_files.json')})
        proof=load(directory/'benchmark_label_proof.json')
        assert proof['benchmark_record']==labels[row['benchmark_id']]
        assert proof['package_record']==packages[row['benchmark_id']]
        assert proof['benchmark_record']['label']=='1' and proof['benchmark_record']['provenance']=='wild'
        assert proof['package_record']['sanitized']=='no' and proof['package_record']['hygiene_filtered']=='no'
        archive=ROOT/'source/protect/packages'/proof['package_record']['package_archive']
        assert sha(archive.read_bytes())==proof['package_record']['package_archive_sha256']
        with tarfile.open(archive,'r:gz') as handle:
            prefix=row['benchmark_package_prefix']+'/'
            members=[m for m in handle.getmembers() if m.isfile() and m.name.startswith(prefix)]
            originals={}
            for member in members:
                data=handle.extractfile(member).read()
                originals[member.name[len(prefix):]]=git_hash('blob',data)
            assert normalized(originals)==operational[1]
            assert sha(handle.extractfile(row['source_metadata_archive_path']).read())==row['source_metadata_sha256']
        metadata=(directory/'source_registry_metadata.json').read_bytes()
        assert sha(metadata)==row['source_metadata_sha256']
        assert json.loads(metadata)['latest']['version']==row['new_version']
        for name,info in row['diffs'].items():
            data=(directory/name).read_bytes()
            assert sha(data)==info['sha256'] and len(data)==info['bytes']
        assert row['diffs']['package.diff']['bytes']>0
    assert file_count==123 and byte_count==456600
    rejected=load(ROOT/'unverified/registry_records.json')
    assert len(rejected)==26 and not ({r['skill_id'] for r in rows}&{r['skill_id'] for r in rejected})
    dedup=load(ROOT/'audit/deduplication.json')
    assert len(set(dedup['previous_skill_ids'])|{r['skill_id'] for r in rows})==24
    index=load(ROOT/'source/skilllife/data/scenarios/sources/index.json')
    evolution=[e for e in index['entries'] if e['class']=='E']
    assert len(evolution)==99 and sum(e['provenance_stratum']=='unchanged_native_skill_source' for e in evolution)==2
    native=load(ROOT/'audit/skilllife_native_updates.json')
    assert len(native)==2 and all(c['provenance']['historical_incident'] is False and c['provenance']['chronology_direction']=='safety_improvement' for c in native)
    cohort=load(ROOT/'source/skilllife/data/scenarios/sources/scenarios/cohort-new194-frozen.json')
    original={c['id']:c for c in cohort['cases']}
    for case in native:
        assert case['provenance']==original[case['id']]['provenance']
    summary=load(ROOT/'summary.json')
    assert summary['original_files']==file_count and summary['original_bytes']==byte_count
    manifest=ROOT/'MANIFEST.sha256'
    if manifest.exists():
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest,name=line.split('  ',1)
            assert sha((ROOT/name).read_bytes())==digest,name
    report={'passed':True,'mode':'offline; no sample execution','accepted_distinct_skills':6,'update_pairs':6,'complete_snapshots':12,'original_files':file_count,'original_bytes':byte_count,'unverified_registry_records':26,'prior_overlap':0,'combined_distinct_skills':24,'checks':['original Git blob and SHA-256 hashes','reconstructed Git trees and source metadata membership','exact first-parent API lineage','registry identity and version','full operational package equality','benchmark malicious label membership','actual non-metadata changes','diff hashes','deduplication','synthetic/native-safety-fix exclusion','manifest hashes when present'],'new_first_malicious_introductions_confirmed':0}
    if not manifest.exists():(ROOT/'verification_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
