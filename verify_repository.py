"""Verify the three-category layout. Never import or execute Skill sample code."""
import argparse,hashlib,json,re,subprocess,sys,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args()
    migration=load('.layout_migration.json');a,b,c=migration['categories']
    assert {p.name for p in ROOT.iterdir() if p.is_dir() and p.name!='.git'}=={a,b,c}
    for line in (ROOT/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        digest,name=line.split('  ',1);p=(ROOT/name).resolve();assert p.is_relative_to(ROOT)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
    checks=['three top-level data categories and maintenance-file SHA-256 hashes']
    identity_count=None
    if (ROOT/'.git').exists():
        entries=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0');index={}
        for entry in entries:
            if not entry:continue
            header,name=entry.split(b'\t',1);mode,sha,stage=header.decode().split();assert stage=='0'
            index[name.decode('utf-8')]=(mode,sha)
        changed=set(migration['maintenance_files_changed']);identity_count=0
        for row in migration['files']:
            if row['new_path'] not in changed:
                assert index[row['new_path']]==(row['mode'],row['git_blob_sha1']),row['new_path'];identity_count+=1
            if row['old_path']!=row['new_path']:assert row['old_path'] not in index or row['old_path'] in {'README.md','MANIFEST.sha256'}
        checks.append('original Git object identities preserved for all unmodified files, including the existing locally blocked record')
    updates=[json.loads(line) for line in (ROOT/a/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(updates)==500 and len({r['id'] for r in updates})==500
    for r in updates:assert (ROOT/a/r['local_directory']/'metadata.json').is_file()
    malicious_sources=[(b+'/release_versions/02_MalSkillBench',17),(b+'/release_versions/03_MaliciousSkillBench',6),(b+'/git_commit_versions/MaliciousAgentSkillsBench',13)]
    for directory,n in malicious_sources:
        rows=[json.loads(x) for x in (ROOT/directory/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(rows)==n
        for row in rows:assert (ROOT/directory/row['local_directory']/'metadata.json').is_file()
    assert len(list((ROOT/b/'release_versions/01_MalSkills/confirmed_updates').iterdir()))==1
    assert len(load(c+'/malicious_snapshots_index.json'))==62
    assert len(load(c+'/confirmed_exact_content_clone_pairs.json'))==20
    checks.append('500 real updates, 24 release updates, 13 Git updates, and 20 exact clone pairs remain separate')
    local_links=0
    controls=['README.md',b+'/README.md']+[x for x in migration['maintenance_files_changed'] if x.endswith('/README.md')]
    for name in set(controls):
        text=(ROOT/name).read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if target.startswith(('http:','https:','mailto:','#')):continue
            path=urllib.parse.unquote(target.split('#',1)[0]);p=(ROOT/name).parent/path
            assert p.exists(),(name,target);local_links+=1
    checks.append('all relative navigation links in moved authored READMEs resolve')
    scripts=[a+'/verify_dataset.py',b+'/release_versions/01_MalSkills/verify_dataset.py',b+'/release_versions/02_MalSkillBench/verify_dataset.py',b+'/release_versions/03_MaliciousSkillBench/verify_dataset.py',b+'/git_commit_versions/MaliciousAgentSkillsBench/verify_dataset.py',b+'/supporting/malskills-legacy-trace/verify_dataset.py',b+'/supporting/skillleakbench-audit/verify_audit.py',c+'/verify_dataset.py']
    results=[]
    if args.full:
        for name in scripts:
            result=subprocess.run([sys.executable,'-S',str(ROOT/name)],cwd=ROOT,capture_output=True)
            assert result.returncode==0,(name,result.stderr.decode('utf-8',errors='replace'))
            results.append({'script':name,'status':'passed'})
    output={'status':'passed_with_known_local_omission','checks':checks,'original_files':len(migration['files']),'unchanged_git_objects_checked':identity_count,'relative_links_checked':local_links,'full_offline_verifiers':results,'counts':migration['counts'],'known_local_omission':migration['preexisting_host_blocked_local_missing_record'],'source_history_full_reverification':'not run because its pre-existing host-blocked source record is unavailable; no recovery attempted','sample_code_executed':False}
    print(json.dumps(output,ensure_ascii=True,indent=2))
if __name__=='__main__':main()
