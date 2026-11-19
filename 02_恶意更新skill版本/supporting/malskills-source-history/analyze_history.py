"""Static cross-checks against recorded primary-source IOCs. No payload execution."""
import base64
import concurrent.futures
import difflib
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import quote

import collect_history as collector

ROOT=Path(__file__).resolve().parent
KNOWN_IPS=('91.92.242.30','95.92.242.30','96.92.242.30','202.161.50.59','54.91.154.110')

def inspect(snapshot):
    evidence=[]
    for item in snapshot.get('files',[]):
        if item['status']!='verified' or item['path']=='_meta.json':continue
        try:text=(ROOT/snapshot['directory']/'files'/item['path']).read_text(encoding='utf-8-sig')
        except UnicodeDecodeError:continue
        lines=text.splitlines()
        for i,line in enumerate(lines):
            if re.search(r'github\.com/Ddoy233/openclawcli',line,re.I) and re.search(r'download|install|run|extract',line,re.I):
                evidence.append({'rule':'reported_malware_repository_install_instruction','source_id':'SNYK-CLAWDHUB','path':item['path'],'line':i+1,'excerpt':line.strip()[:400]})
            ip=next((ip for ip in KNOWN_IPS if ip in line),None)
            if ip and re.search(r'(?:curl|wget).{0,180}\|\s*(?:ba)?sh\b',line,re.I):
                evidence.append({'rule':'reported_malware_ip_download_execute','source_id':'KOI-CLAW-HAVOC','path':item['path'],'line':i+1,'ioc':ip,'excerpt':line.strip()[:400]})
            # Decode string literals as inert text only; never contact decoded addresses.
            for match in re.finditer(r'[\x22\x27]([A-Za-z0-9+/]{40,16000}={0,2})[\x22\x27]',line):
                try:decoded=base64.b64decode(match.group(1),validate=True).decode('utf-8')
                except (ValueError,UnicodeDecodeError):continue
                ip=next((ip for ip in KNOWN_IPS if ip in decoded),None)
                context=' '.join(lines[max(0,i-1):i+2])
                if ip and re.search(r'(?:curl|wget)',decoded,re.I) and re.search(r'base64\s+(?:-D|-d|--decode)\s*\|\s*(?:ba)?sh\b',context,re.I):
                    evidence.append({'rule':'encoded_reported_malware_fetch_execute','source_id':'KOI-CLAW-HAVOC','path':item['path'],'line':i+1,'ioc':ip,'encoded_sha256':hashlib.sha256(match.group(1).encode()).hexdigest(),'decoded_text':decoded[:800]})
    return evidence

def first_parent_absence(record):
    first=record['snapshots'][0]
    parent=first['parents'][0] if first['parents'] else None
    result={'skill_id':record['skill_id'],'first_path_commit':first['commit_sha'],'first_parent':parent,'path':'skills/'+record['skill_id']}
    if not parent:
        result['status']='repository_root_commit';return result
    try:
        commit=collector.api.api(f'/repos/{collector.REPOSITORY}/git/commits/{parent}')
        result['parent_commit_exists']=True;result['parent_root_tree']=commit['tree']['sha']
        try:
            tree=collector.api.api(f'/repos/{collector.REPOSITORY}/git/trees/'+quote(parent+':'+result['path'],safe=''))
            result.update(status='directory_present_at_parent',parent_skill_tree=tree['sha'])
        except collector.api.Unavailable as error:
            result['status']='directory_absent_at_existing_parent' if str(error)=='http_404' else 'unverified_'+str(error)
    except Exception as error:result.update(status='unverified',error=str(error)[:100])
    collector.save(ROOT/'parent_evidence'/(record['skill_id'].replace('/','_')+'.json'),result)
    return result

def main():
    records=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'records').glob('*.json'))]
    assert len(records)==100
    all_evidence=[]
    for record in records:
        for snapshot in record['snapshots']:
            for flag in inspect(snapshot):all_evidence.append({'skill_id':record['skill_id'],'commit_sha':snapshot['commit_sha'],'version':snapshot.get('version_from_commit_message'),**flag})
    (ROOT/'static_ioc_evidence.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in all_evidence),encoding='utf-8')
    collector.api.authenticate()
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        parents=list(pool.map(first_parent_absence,records))
    # Verify the exact pre-update state, not merely the earlier release in metadata.
    claw=next(r for r in records if r['skill_id']=='zaycv/clawhub')
    bad=next(s for s in claw['snapshots'] if s['commit_sha']=='93d548f298d9d996a42da85de09f9860136c2280')
    parent=bad['parents'][0]
    raw=collector.api.api(f'/repos/{collector.REPOSITORY}/commits/{parent}')
    before=collector.snapshot(claw['skill_id'],raw)
    assert before['complete_directory'] and bad['complete_directory']
    assert not inspect(before) and inspect(bad)
    first=claw['snapshots'][0]
    assert before['primary']['git_blob_sha1']==first['primary']['git_blob_sha1']
    a=(ROOT/before['directory']/'files/SKILL.md').read_text(encoding='utf-8')
    b=(ROOT/bad['directory']/'files/SKILL.md').read_text(encoding='utf-8')
    case=ROOT/'confirmed_archive_introductions/zaycv_clawhub';case.mkdir(parents=True,exist_ok=True)
    (case/'SKILL.diff').write_text(''.join(difflib.unified_diff(a.splitlines(keepends=True),b.splitlines(keepends=True),fromfile='parent/SKILL.md',tofile='1.0.3/SKILL.md')),encoding='utf-8')
    decision={'skill_id':'zaycv/clawhub','version':'1.0.3','new_commit':bad['commit_sha'],'git_commit_at':bad['committer_date'],'registry_published_at_ms':bad['recorded_meta_latest']['publishedAt'],'parent_commit':parent,'parent_snapshot':before['directory'],'new_snapshot':bad['directory'],'parent_primary_equals_earliest_1_0_0':True,'old_version_has_this_campaign_install_instruction':False,'new_version_has_reported_campaign_install_instruction':True,'source_ids':['SNYK-CLAWDHUB','CLAWHUB-ISSUE-108'],'confirmed_scope':'first introduction in preserved Git history of this registry path at the pinned ref','global_first_published_malicious_version_confirmed':False,'global_first_published_malicious_version':None,'limitations':['Registry publication history may contain unarchived releases; version identifiers 1.0.1/1.0.2 have not been established as published or absent.','The preceding version has no independently established overall benign label.','This verifies introduction of reported malware-distribution instructions, not execution or infection of a victim.','Canonical archive repositories are unavailable; evidence comes from an archived Git mirror.']}
    collector.save(case/'decision.json',decision)
    print(json.dumps({'ioc_evidence_records':len(all_evidence),'skills_with_corroborated_ioc':len(set(x['skill_id'] for x in all_evidence)),'parent_absence':sum(x['status']=='directory_absent_at_existing_parent' for x in parents),'confirmed_archive_introductions':1,'global_first_confirmed':0,'api_remaining':collector.api.REMAINING}))

if __name__=='__main__':main()
