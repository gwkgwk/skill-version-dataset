"""Offline structural and provenance checks. Never imports or executes samples."""
from pathlib import Path
import json,hashlib,collections

ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def files(p):return {f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob('*') if f.is_file()}
def safe(base,rel):
 p=(base/rel).resolve();assert p.is_relative_to(base.resolve()),rel
 return p

def verify():
 records=read(ROOT/'index.json');summary=read(ROOT/'summary.json')
 assert len(records)==100 and len({r['id'] for r in records})==100
 assert {p.name for p in (ROOT/'pairs').iterdir()}=={r['id'] for r in records}
 assert collections.Counter(r['source'] for r in records)=={'SkillLifeBench':47,'Skill-Inject':53}
 assert len([r for r in records if r['source']=='SkillLifeBench'])==len({r['source_family'] for r in records if r['source']=='SkillLifeBench'})
 assert len({r['source_family'] for r in records if r['source']=='Skill-Inject'})==34
 assert len({r['source_host'] for r in records if r['source']=='Skill-Inject'})==17
 defs=collections.Counter();all_pair_hashes=[];snapshots=0
 source_files=read(ROOT/'provenance/verified_source_files.json')
 source_hashes={x['path']:x['sha256'] for x in source_files if x['path'].startswith('data/skills/') or x['path'].startswith('data/task_scripts/')}
 relabel={(x['suite'],x['id']):x for x in read(ROOT/'provenance/skill-inject/camera_ready/relabel.json')}
 for r in records:
  p=safe(ROOT,r['local_path']);assert read(p/'metadata.json')==r
  old=files(p/'old');new=files(p/'new');assert old and new and old!=new
  snapshots+=2
  expected={(x['side'],x['path']):x for x in read(p/'files.json')}
  actual={}
  for side,inventory in [('old',old),('new',new)]:
   for path,b in inventory.items():
    safe(p/side,path);item=expected[(side,path)]
    assert item['sha256']==sha(b) and item['bytes']==len(b),(r['id'],side,path)
    assert item['git_blob_sha1']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
    actual[(side,path)]=item
  assert actual==expected
  changes={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
  assert changes=={x['path'] for x in r['diff_changes']}
  for x in r['diff_changes']:
   assert x['old_sha256']==(sha(old[x['path']]) if x['path'] in old else None)
   assert x['new_sha256']==(sha(new[x['path']]) if x['path'] in new else None)
  ph=sha(canonical({'old':{k:sha(v) for k,v in old.items()},'new':{k:sha(v) for k,v in new.items()}}))
  assert ph==r['content_pair_sha256'];all_pair_hashes.append(ph)
  assert not r['independently_executed_here'] and not r['labels']['historical_real_update']
  assert (p/'package.diff').stat().st_size>0 and r['target_behavior_zh'] and r['selection_reason_zh']
  context=read(p/'context.json')
  if r['source']=='SkillLifeBench':
   c=read(p/'evidence/source_case.json')
   assert c['id']==r['source_id'] and c['family_id']==r['source_family']
   assert c['conditions']['before']==c['conditions']['after']==context['initial_state']
   assert context['user_task']==c['task'] and not c['provenance']['historical_incident']
   for side,key in [('old','before'),('new','after')]:
    ts=read(p/side/'tools.json');assert ts==c['condition_tools'][key]
    for t in ts:assert (p/side/'tools'/(t['name']+'.py')).read_bytes()==t['code'].encode('utf-8')
   assert read(p/'evidence/oracle.json')==c['oracle']
   frozen=read(p/'evidence/frozen_measurements.json');groups=collections.defaultdict(dict)
   for f in frozen:
    obj=read(safe(ROOT/'provenance/skilllifebench/data/scenarios',f['source_path']))
    for key in f['pointer'].strip('/').split('/'):obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    assert obj==f['row'] and obj['case_id']==c['id'] and obj['condition']==f['condition']
    assert obj['complete'] is True and obj['artifact_utility'] is True
    assert obj['harm']==(f['condition']=='after')
    groups[(f['model'],f['source_run'])][f['condition']]=obj
   assert len(groups)==r['source_positive_measurement_pairs']
   for g in groups.values():
    assert set(g)=={'before','after'}
    if 'initial_state_sha256' in g['before']:assert g['before']['initial_state_sha256']==g['after']['initial_state_sha256']
  else:
   d=read(p/'evidence/injection_definition.json');t=read(p/'evidence/task_selection.json');lab=read(p/'evidence/final_label.json')
   assert lab['final_label']=='obvious' and lab['definition_content_equal_across_pinned_github_and_hf_releases']
   correction=relabel.get((lab['source_suite'],d['id']))
   assert correction==lab['author_label_correction']
   assert (correction or {}).get('final_label',lab['source_suite'])=='obvious'
   assert t==d['tasks'][r['source_task_index']] and context['user_task']==t['prompt'] and context['policy_condition']=='normal'
   for rel,b in old.items():assert sha(b)==source_hashes['data/skills/'+r['source_host']+'/'+rel]
   block=''.join(line.strip()+'\n' if line.strip() else '\n' for line in (t.get('injection_prefix','')+d['instructions']['line_injection']).strip('\n').splitlines())
   assert (p/'evidence/inserted_block.txt').read_bytes()==block.encode('utf-8')
   primary=old['SKILL.md'].decode('utf-8');assert block.strip() not in primary
   lines=primary.splitlines(keepends=True);at=t['line_num']-1
   assert new['SKILL.md']==(''.join(lines[:at])+block+''.join(lines[at:])).encode('utf-8')
   scripts={'scripts/'+k for k in d.get('task_scripts',{})}
   assert changes=={'SKILL.md'}|scripts and set(new)==set(old)|scripts
   for rel in set(old)-{'SKILL.md'}-scripts:assert new[rel]==old[rel]
   for name,path in d.get('task_scripts',{}).items():assert sha(new['scripts/'+name])==source_hashes['data/'+path]
   for name in t.get('task_files',{}):assert safe(p/'fixtures/task_files',name).is_file()
   assert (p/'evidence/attack_grader.py').is_file()
   defs[r['source_family']]+=1
 assert len(set(all_pair_hashes))==100 and snapshots==200
 assert summary['exact_pair_duplicates']==0 and summary['true_historical_benign_to_malicious_pairs']==0
 manifest=ROOT/'manifest-sha256.json'
 checked=0
 if manifest.exists():
  m=read(manifest)
  actual={f.relative_to(ROOT).as_posix() for f in ROOT.rglob('*') if f.is_file() and f!=manifest}
  assert actual==set(m)
  for rel,expected in m.items():assert sha(safe(ROOT,rel).read_bytes())==expected,rel
  checked=len(m)
 return {'status':'PASS','pairs':100,'snapshots':200,'life_pairs':47,'inject_pairs':53,'distinct_injection_definitions':len(defs),'exact_pair_duplicates':0,'snapshot_integrity':'PASS','controlled_diff_reconstruction':'PASS','author_frozen_evidence_consistency':'PASS','manifest_files_checked':checked,'runtime_samples_executed':0}

if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
