"""Recover inert archival Git evidence. Never follows or runs artifact URLs/code."""
import concurrent.futures
import hashlib
import importlib.util
import json
import re
import threading
import urllib.parse
import urllib.request
from pathlib import Path, PurePosixPath

import requests

ROOT=Path(__file__).resolve().parent
WORKSPACE=ROOT.parent.parent
REPOSITORY='friuns2/openclaw-removed-skills'
spec=importlib.util.spec_from_file_location('trusted_collector',ROOT/'tooling/github_io.py')
api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api);api.ROOT=ROOT
LOCAL=threading.local()
LOCK=threading.Lock()
BLOCKED={('zaycv/clawhub',sha,'SKILL.md') for sha in ['78ab78a7bb7a13ec8e4fac416d9707f7e5602508','6b1230a3730f630d5c0d0df6a6d93e9d97eb9add','87f860c49564e9748c7f588ec57a4a3466c5ffe8']}
BLOCKED_BLOBS={'b4437106f47cd532bd7c2544f110c45d7a18b42e','12fee728ca9588a172c9cbefe225dfb6eb663409','7e861d5befb0dfb112562a24831552504218ae52'}

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def raw_get(path):
    assert path.startswith('/')
    if not hasattr(LOCAL,'raw'):
        LOCAL.raw=requests.Session();LOCAL.raw.proxies.update(urllib.request.getproxies())
    response=LOCAL.raw.get('https://raw.githubusercontent.com'+path,timeout=(12,35))
    if response.status_code!=200:raise RuntimeError('raw_http_'+str(response.status_code))
    assert urllib.parse.urlparse(response.url).hostname=='raw.githubusercontent.com'
    return response.content

def indicators(data):
    try:text=data.decode('utf-8-sig')
    except UnicodeDecodeError:return []
    rules=[('snyk_ddoy233_payload_repository',r'github\.com/Ddoy233/openclawcli', 'SNYK-CLAWDHUB'),('known_campaign_ip',r'\b(?:91\.92\.242\.30|95\.92\.242\.30|96\.92\.242\.30|202\.161\.50\.59|54\.91\.154\.110)\b','KOI-CLAW-HAVOC'),('external_glot_execution_lure',r'glot\.io/snippets/','KOI-CLAW-HAVOC'),('openclawcli_forum_unverified',r'openclawcli\.forum','UNVERIFIED-DOMAIN'),('obfuscated_execution',r'(?:base64\s+(?:-D|-d|--decode).{0,50}\|\s*(?:ba)?sh|eval\s*\(.{0,100}(?:atob|base64))','BEHAVIOR-ONLY'),('remote_script_execution',r'(?:curl|wget).{0,200}\|\s*(?:ba)?sh|(?:exec|eval)\s*\(.{0,150}(?:urlopen|requests\.)','BEHAVIOR-ONLY')]
    found=[]
    for number,line in enumerate(text.splitlines(),1):
        for rule,pattern,source in rules:
            if re.search(pattern,line,re.I):
                found.append({'rule':rule,'line':number,'source_id':source,'line_sha256':hashlib.sha256(line.encode()).hexdigest(),'excerpt':line.strip()[:350]})
    return found

def snapshot(skill,commit):
    path='skills/'+skill
    key=urllib.parse.quote(commit['sha']+':'+path,safe='')
    directory=ROOT/'artifacts'/skill.replace('/','_')/commit['sha']
    record={'commit_sha':commit['sha'],'committer_date':commit['commit']['committer']['date'],'message':commit['commit']['message'].splitlines()[0],'parents':[p['sha'] for p in commit['parents']],'commit_url':f'https://github.com/{REPOSITORY}/commit/'+commit['sha'],'directory':directory.relative_to(ROOT).as_posix(),'files':[],'indicators':[],'security_label':None}
    try:
        tree=api.api(f'/repos/{REPOSITORY}/git/trees/{key}?recursive=1')
        record['tree_sha']=tree['sha'];save(directory/'tree.json',tree)
        blobs=[x for x in tree['tree'] if x['type']!='tree']
        if tree.get('truncated') or len(blobs)>150 or sum(x.get('size',0) for x in blobs)>3000000:raise RuntimeError('tree_coverage_limit')
        for blob in blobs:
            relative=blob['path'];item={'path':relative,'git_blob_sha1':blob['sha'],'mode':blob['mode'],'bytes':blob.get('size'),'status':'not_retrieved'}
            record['files'].append(item)
            if (skill,commit['sha'],relative) in BLOCKED or blob['sha'] in BLOCKED_BLOBS:
                item['status']='previously_blocked_by_host_security_not_retried';continue
            parts=PurePosixPath(relative).parts
            if blob['type']!='blob' or blob['mode']=='120000' or any(x in ('.','..','.git') or re.search(r'[<>:"\\|?*]',x) or x.endswith(('.', ' ')) for x in parts):
                item['status']='unsupported_path_or_mode';continue
            output=directory/'files'/relative
            try:
                if output.exists():data=output.read_bytes()
                else:
                    data=raw_get('/'+REPOSITORY+'/'+commit['sha']+'/'+urllib.parse.quote(path+'/'+relative,safe='/'))
                assert api.git_sha(data)==blob['sha'] and len(data)==blob.get('size',len(data))
                output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(data)
                item.update(status='verified',sha256=hashlib.sha256(data).hexdigest())
                for flag in indicators(data):record['indicators'].append({'path':relative,**flag})
            except Exception as error:
                item['status']='unavailable_'+type(error).__name__
        record['complete_directory']=all(x['status']=='verified' for x in record['files'])
        record['primary']=next((x for x in record['files'] if x['path']=='SKILL.md'),None)
        metadata=directory/'files/_meta.json'
        if metadata.exists():
            meta=json.loads(metadata.read_text(encoding='utf-8-sig'));record['recorded_meta_latest']=meta.get('latest')
        match=re.match(r'(?:skill|meta):\s+.*?\s+v([^ ]+)',record['message'])
        record['version_from_commit_message']=match.group(1) if match else None
        record['status']='snapshot_recovered' if record['primary'] and record['primary']['status']=='verified' else 'primary_unavailable'
    except Exception as error:
        record.update(status='unavailable',error=str(error)[:140],complete_directory=False)
    save(directory/'snapshot.json',record)
    return record

def process(row):
    skill=row['skill_id'];latest=row['versions_oldest_first'][-1]
    result={'skill_id':skill,'benchmark_seed':row,'archive_repository':REPOSITORY,'source_repository_status':'canonical_registry_mirror_unavailable_in_prior_check','history_query_ref':latest['commit_sha'],'snapshots':[],'first_malicious_version':None,'global_first_introduction_confirmed':False}
    try:
        endpoint=f'/repos/{REPOSITORY}/commits?'+urllib.parse.urlencode({'sha':latest['commit_sha'],'path':'skills/'+skill,'per_page':100})
        history=api.api(endpoint)
        result['history_url']='https://api.github.com'+endpoint
        result['path_commits_returned']=len(history);result['history_truncated']=len(history)==100
        save(ROOT/'histories'/ (skill.replace('/','_')+'.json'),[{'sha':c['sha'],'commit':{'tree':c['commit']['tree'],'committer':{'date':c['commit']['committer']['date']},'message':c['commit']['message']},'parents':c['parents'],'html_url':c['html_url']} for c in history])
        # GitHub returns newest first. Preserve API order; do not sort untrusted timestamps.
        for commit in reversed(history):
            result['snapshots'].append(snapshot(skill,commit))
        newest=result['snapshots'][-1] if result['snapshots'] else None
        result['benchmark_primary_matches_archive_seed']=(newest['primary']['sha256']==row['benchmark_skill_md_sha256']) if newest and newest.get('primary',{}).get('status')=='verified' else None
        result['status']='history_recovered' if newest else 'no_history'
    except Exception as error:result.update(status='unavailable',error=str(error)[:140])
    save(ROOT/'records'/(skill.replace('/','_')+'.json'),result)
    with LOCK:print(json.dumps({'skill':skill,'status':result['status'],'commits':len(result['snapshots']),'seed_matches':result.get('benchmark_primary_matches_archive_seed'),'api_remaining':api.REMAINING}),flush=True)
    return result

def main():
    api.authenticate()
    seeds_path=ROOT/'source/selected_100_seeds.json'
    if not seeds_path.exists():seeds_path=WORKSPACE/'tmp/skill-version-dataset/final_200_version_index.json'
    rows=[r for r in json.loads(seeds_path.read_text(encoding='utf-8')) if r['benchmark_label']=='malicious']
    assert len(rows)==100
    save(ROOT/'source/selected_100_seeds.json',rows)
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for result in pool.map(process,rows):results.append(result)
    save(ROOT/'collection_summary.json',{'skills':len(results),'history_recovered':sum(x['status']=='history_recovered' for x in results),'snapshots':sum(len(x['snapshots']) for x in results),'seed_hash_matches':sum(x.get('benchmark_primary_matches_archive_seed',False) for x in results),'api_requests':api.CALLS,'api_remaining':api.REMAINING})
    print((ROOT/'collection_summary.json').read_text(encoding='utf-8'),flush=True)

if __name__=='__main__':main()
