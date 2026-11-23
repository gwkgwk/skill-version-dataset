"""Verify current dataset and user-supplied labels; never execute Skill code."""
import argparse,hashlib,json,re,subprocess,sys,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(name):return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--full',action='store_true');args=parser.parse_args()
    migration=load('.layout_migration.json');revision=load('.dataset_revision.json');a,b,c=migration['categories']
    assert revision['replaced_category']==a
    controlled=load('.controlled_updates_revision.json');d=controlled['category']
    assert {p.name for p in ROOT.iterdir() if p.is_dir() and p.name!='.git' and not p.name.startswith('__')}=={a,b,d}
    for line in (ROOT/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        sha,name=line.split('  ',1);p=(ROOT/name).resolve();assert p.is_relative_to(ROOT)
        assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,name
    checks=['three current data categories and current maintenance-file SHA-256 hashes'];identity_count=None
    if (ROOT/'.git').exists():
        entries=subprocess.check_output(['git','ls-files','--stage','-z'],cwd=ROOT).split(b'\0');index={}
        for entry in entries:
            if not entry:continue
            header,name=entry.split(b'\t',1);mode,sha,stage=header.decode().split();assert stage=='0'
            index[name.decode('utf-8')]=(mode,sha)
        changed=set(migration['maintenance_files_changed'])|set(revision['root_files_changed']);identity_count=0
        for row in migration['files']:
            if row['new_path'].startswith((a+'/',c+'/')):continue
            if row['new_path'] not in changed:
                assert index[row['new_path']]==(row['mode'],row['git_blob_sha1']),row['new_path'];identity_count+=1
            if row['old_path']!=row['new_path']:assert row['old_path'] not in index or row['old_path'] in {'README.md','MANIFEST.sha256'}
        checks.append('historical Git identities preserved outside the replaced category and changed root docs')
    rows=load(a+'/updates.json');assert len(rows)==500 and len({r['id'] for r in rows})==500
    assert len({(r['repository'],r['skill_directory']) for r in rows})==500
    for row in rows:
        assert (ROOT/a/row['local_directory']/'metadata.json').is_file()
        assert all(row[k]=='benign' for k in ['old_security_label','new_security_label','update_security_label'])
        assert row['human_review_confirmed'] and row['human_review']['label_basis']=='user_attestation'
        assert row['human_review']['reviewer_identity'] is None and row['human_review']['actual_review_date'] is None
        assert row['human_review']['independently_validated_by_assistant'] is False
    confirmation=load(a+'/human_review_confirmation.json')
    assert confirmation['confirmed_update_pairs']==500 and confirmation['confirmed_version_snapshots']==1000
    assert confirmation['case_ids']==[r['id'] for r in rows] and confirmation['independently_validated_by_assistant'] is False
    checks.append('500 benign labels trace to the user-reported manual confirmation without invented reviewer/date/evidence')
    for directory,n in [(b+'/release_versions/02_MalSkillBench',17),(b+'/release_versions/03_MaliciousSkillBench',6),(b+'/git_commit_versions/MaliciousAgentSkillsBench',13)]:
        updates=[json.loads(x) for x in (ROOT/directory/'updates.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(updates)==n
        for row in updates:assert (ROOT/directory/row['local_directory']/'metadata.json').is_file()
    assert len(list((ROOT/b/'release_versions/01_MalSkills/confirmed_updates').iterdir()))==1
    assert not (ROOT/c).exists()
    checks.append('500 user-confirmed benign pairs and 37 malicious-source pairs remain; clone category removed')
    main_set=load('UPDATE_DETECTION_MAIN_SET.json')
    assert [(x['name'],x['count']) for x in main_set['main_cohorts']]==[('benign_update_controls',500),('controlled_attack_content_updates',53)]
    assert [(x['name'],x['count']) for x in main_set['separate_evaluation_cohorts']]==[('controlled_safety_regressions',47)]
    assert {x['path'] for x in main_set['excluded_from_main_set']}=={b+'/'}
    controlled_rows=load(d+'/index.json')
    assert [x['id'] for x in controlled_rows if x['source']=='Skill-Inject']==[f'CTU-{i:04d}' for i in range(48,101)]
    assert [x['id'] for x in controlled_rows if x['source']=='SkillLifeBench']==[f'CTU-{i:04d}' for i in range(1,48)]
    checks.append('main update detection set excludes the removed clone category')
    assert load(d+'/summary.json')['selected_pairs']==100
    assert load(d+'/summary.json')['true_historical_benign_to_malicious_pairs']==0
    controls={'README.md','DATASET_CARD.md','THIRD_PARTY_NOTICES.md',a+'/README.md',b+'/README.md',d+'/README.md'}
    controls.update(x for x in migration['maintenance_files_changed'] if x.endswith('/README.md') and not x.startswith((a+'/',c+'/')))
    links=0
    for name in controls:
        for target in re.findall(r'\]\(([^)]+)\)',(ROOT/name).read_text(encoding='utf-8')):
            if target.startswith(('http:','https:','mailto:','#')):continue
            p=(ROOT/name).parent/urllib.parse.unquote(target.split('#',1)[0]);assert p.exists(),(name,target);links+=1
    scripts=[a+'/verify_delivery.py',b+'/release_versions/01_MalSkills/verify_dataset.py',b+'/release_versions/02_MalSkillBench/verify_dataset.py',b+'/release_versions/03_MaliciousSkillBench/verify_dataset.py',b+'/git_commit_versions/MaliciousAgentSkillsBench/verify_dataset.py',b+'/supporting/malskills-legacy-trace/verify_dataset.py',b+'/supporting/skillleakbench-audit/verify_audit.py',d+'/verify_dataset.py'];results=[]
    if args.full:
        for script in scripts:
            result=subprocess.run([sys.executable,'-S',str(ROOT/script)],cwd=ROOT,capture_output=True)
            assert result.returncode==0,(script,result.stderr.decode('utf-8',errors='replace'))
            results.append({'script':script,'status':'passed'})
    print(json.dumps({'status':'passed_with_known_local_omission','checks':checks,'unchanged_git_objects_checked':identity_count,
          'relative_links_checked':links,'full_offline_verifiers':results,
          'counts':dict({k:v for k,v in migration['counts'].items() if not k.startswith('malicious_clone') and k!='malicious_exact_clone_pairs'},user_reported_human_confirmed_benign_pairs=500,official_source_repositories=15,controlled_update_pairs=100,controlled_update_snapshots=200),
          'known_local_omission':migration['preexisting_host_blocked_local_missing_record'],
          'source_history_full_reverification':'not run: pre-existing host-blocked record; no recovery attempted',
          'assistant_independent_security_audit_completed':False,'sample_code_executed':False},ensure_ascii=True,indent=2))

if __name__=='__main__':main()
