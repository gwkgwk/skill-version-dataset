"""Offline verification of metadata and negative findings. No upstream code execution."""
import csv
import hashlib
import json
import zipfile
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
HEAD='682521a54f65045725e1e01076db449e402a78f9'
INITIAL='c5394845fbe336e8fded41b58375ecf37a9a387c'

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
        assert tree_hash(direct)==digest

def read_csv(path):return list(csv.DictReader(path.open(encoding='utf-8-sig')))

def main():
    summary=load(ROOT/'summary.json')
    refs=list((ROOT/'source').iterdir());assert len(refs)==6
    for directory in refs:
        commit=load(directory/'commit.json');tree=load(directory/'tree.json')
        verify_tree(tree)
        assert commit['sha']==directory.name and commit['tree']['sha']==tree['sha']
        assert not any(e['path'].split('/')[-1].lower()=='skill.md' for e in tree['tree'])
        for path in directory.rglob('*'):
            if path.is_file() and path.name not in ('commit.json','tree.json'):
                relative=path.relative_to(directory).as_posix()
                item=next(e for e in tree['tree'] if e['path']==relative)
                data=path.read_bytes()
                assert len(data)==item['size'] and git_hash('blob',data)==item['sha']
        rows=read_csv(directory/'data/skills_dataset.csv')
        assert len(rows)==520 and Counter(r['classification'] for r in rows)=={'vulnerable':437,'malicious':83}
    current=read_csv(ROOT/'source'/HEAD/'data/skills_dataset.csv')
    initial=read_csv(ROOT/'source'/INITIAL/'data/skills_dataset.csv')
    assert set(current[0])=={'source','skill_name','classification','patterns','issue_count','severity'}
    malicious=[r for r in current if r['classification']=='malicious']
    assert len(malicious)==83 and len({r['skill_name'] for r in malicious})==80
    issues=read_csv(ROOT/'source'/HEAD/'data/issues.csv')
    assert len(issues)==1708
    mal_issues=[r for r in issues if r['classification']=='malicious']
    assert len(mal_issues)==337 and len({r['skill_id'] for r in mal_issues})==83
    cases=load(ROOT/'unverified/malicious_cases_without_native_version_evidence.json')
    assert {r['source_case_id'] for r in cases}=={r['skill_id'] for r in mal_issues}
    assert len(cases)==83 and all(r['version_pair_confirmed'] is False for r in cases)
    assert len(read_csv(ROOT/'unverified/malicious_cases_index.csv'))==83
    comparison=load(ROOT/'evidence/malicious_metadata_revision_comparison.json')
    names=comparison['explicit_display_name_normalizations']
    def canonical(row):
        return tuple((k,names.get(row[k],row[k]) if k=='skill_name' else ';'.join(sorted(p.strip() for p in row[k].split(';'))) if k=='patterns' else row[k]) for k in sorted(row))
    a=Counter(canonical(r) for r in initial if r['classification']=='malicious')
    b=Counter(canonical(r) for r in malicious)
    assert a==b and comparison['equal_after_name_and_pattern_order_normalization'] is True
    archive=ROOT/'mirrors/SkillLeakBench-v1.2.zip';data=archive.read_bytes()
    receipt=load(ROOT/'evidence/zenodo_archive_receipt.json')
    assert len(data)==155135==receipt['bytes'] and sha(data)==receipt['sha256']
    assert 'md5:'+hashlib.md5(data).hexdigest()==receipt['expected_checksum']
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
        assert len(handle.infolist())==75
        assert not any(name.split('/')[-1].lower()=='skill.md' for name in handle.namelist())
        path=next(name for name in handle.namelist() if name.endswith('/data/skills_dataset.csv'))
        assert handle.read(path)==(ROOT/'source'/HEAD/'data/skills_dataset.csv').read_bytes()
    for item in load(ROOT/'evidence/huggingface_mirror_receipts.json'):
        assert item['ref']=='8264436a0483e2fc1aed84b80e5fde73ea52c3ca' and item['identical_to_github_head']
        assert sha((ROOT/'source'/HEAD/'data'/item['path']).read_bytes())==item['sha256']
    references=load(ROOT/'existing_updates_reference.json')
    assert len(references)==len({r['skill_id'] for r in references})==6
    assert all(r['new_count_this_audit']==0 and r['old_version']!=r['new_version'] for r in references)
    assert len(load(ROOT/'evidence/tags.json'))==4 and len(load(ROOT/'evidence/repository_history.json'))==9
    sample=load(ROOT/'source'/HEAD/'code/results.sample/01_phase1_skills_metadata.sample.json')
    assert sample[0]['repo_url']=='https://github.com/example-org/sample-skill'
    assert summary['new_registry_release_update_pairs']==summary['new_git_commit_update_pairs']==0
    assert summary['global_combined_skill_count_unchanged']==37
    manifest=ROOT/'MANIFEST.sha256'
    if manifest.exists():
        for line in manifest.read_text(encoding='utf-8').splitlines():
            digest,name=line.split('  ',1)
            assert sha((ROOT/name).read_bytes())==digest,name
    report={'passed':True,'method':'offline standard-library verification; no upstream code or Skill execution','source_rows':520,'malicious_records':83,'vulnerable_records':437,'unverified_native_version_cases':83,'existing_related_pairs_not_recounted':6,'new_release_version_pairs':0,'new_git_commit_pairs':0,'global_combined_count_unchanged':37,'git_commit_trees_checked':6,'main_history_commits_reviewed':9,'release_tags_reviewed':4,'zenodo_zip_members_checked':75,'checks':['reconstructed original Git directory trees','all supplied original file Git blob hashes','class counts and unique local issue case IDs','metadata comparison with explicit name and pattern-order normalization','Zenodo ZIP MD5 and SHA-256, content inventory and identical dataset','Hugging Face fixed-revision hash receipts','placeholder source examples excluded','existing six pairs referenced without new credit','manifest hashes when present'],'limit':'No new original Skill bytes, fixed sample commits or native release histories were found; absence in these inspected public artifacts does not prove no other versions exist.'}
    if not manifest.exists():(ROOT/'verification_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report),flush=True)

if __name__=='__main__':main()
