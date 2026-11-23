"""Select candidates without running benchmark code or sample payloads."""
from pathlib import Path
import json,ast,collections,hashlib
R=Path(__file__).resolve().parent/'2026-11-22-controlled-update-100'
S=R/'source/skill-inject'; U=S/'upstream'; H=R/'source/skill-inject-hf'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
t=read(S/'git-tree.json'); entries={e['path']:e for e in t['tree'] if e['type']=='blob'}
config=ast.parse((U/'config.py').read_text(encoding='utf-8'))
mapping=next(ast.literal_eval(n.value) for n in config.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name) and n.target.id=='SKILL_MAPPING')
rules={(r['suite'],r['id']):r for r in read(H/'camera_ready/relabel.json')}
categories={(r['suite'],r['id']):r for r in read(H/'camera_ready/categories.json')}
all_defs=[]; exclusions=[]
for suite,rel in [('obvious','data/obvious_injections.json'),('contextual','data/contextual_injections.json'),('camready','data/obvious_injections_camready_phish_poison.json')]:
 for d in read(U/rel):
  orig='obvious' if suite=='camready' else suite; k=(orig,d['id'])
  label=rules.get(k,{}).get('final_label',orig)
  if label!='obvious':
   exclusions.append({'suite':suite,'id':d['id'],'title':d['title'],'reason':'author_final_label_'+label});continue
  ck=('obvious_phish_poison',d['id']) if suite=='camready' else k
  assert ck in categories,(suite,d['id'])
  all_defs.append({'suite':suite,'source_suite':orig,'definition':d,'definition_path':rel,'category':categories[ck]['category'],'category_reason':categories[ck]['reason'],'label_correction':rules.get(k)})
assert len(all_defs)==37,len(all_defs)
paths={'LICENSE','README.md','config.py','scripts/build_sandbox.py','scripts/build_clean_sandboxes.py'}
paths.update(e for e in entries if e.startswith('data/instruction_unit_tests_v2/') and not e.endswith('.code-workspace'))
candidates=[]
for d in all_defs:
 inj=d['definition']; unique=set()
 for i,task in enumerate(inj['tasks']):
  host=mapping.get(task['skill'],task['skill']);prefix='data/skills/'+host+'/'
  hostfiles=[p for p in entries if p.startswith(prefix)]
  key=(host,task.get('line_num'),task.get('injection_prefix',''))
  if key in unique:continue
  unique.add(key)
  if not hostfiles or any(entries[p]['mode'] not in ['100644','100755'] for p in hostfiles):
   exclusions.append({'suite':d['suite'],'id':inj['id'],'task_index':i,'reason':'missing_or_nonregular_host'});continue
  assert prefix+'SKILL.md' in entries,(host,'primary missing')
  needed=set(hostfiles)
  needed.update('data/'+v for v in inj.get('task_scripts',{}).values())
  needed.update('data/'+v for v in task.get('task_files',{}).values())
  for startup in inj.get('startup_scripts',[]):
   if isinstance(startup,str):needed.add('startup_scripts/'+startup)
   else:needed.add(startup['path'])
  missing=needed-set(entries)
  if missing:
   exclusions.append({'suite':d['suite'],'id':inj['id'],'task_index':i,'reason':'missing_declared_files','paths':sorted(missing)});continue
  paths.update(needed)
  candidates.append({**{k:v for k,v in d.items() if k!='definition'},'id':inj['id'],'title':inj['title'],'task_index':i,'host':host,'task':task,'definition':inj,'needed_paths':sorted(needed)})
dump(R/'candidate-inject.json',candidates);dump(R/'excluded-inject-labels-and-files.json',exclusions)
dump(R/'download-paths.json',sorted(paths))
print(json.dumps({'eligible_attack_definitions':len(all_defs),'candidate_distinct_placements':len(candidates),'host_packages':len({c['host'] for c in candidates}),'upstream_files_to_download':len(paths),'source_bytes':sum(entries[p]['size'] for p in paths),'excluded_records':len(exclusions)},ensure_ascii=False))
