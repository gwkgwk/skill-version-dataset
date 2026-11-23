"""Materialize controlled update comparisons by reading source bytes only.
No upstream Python is imported and no Skill, evaluator or startup script is run.
"""
from pathlib import Path
import json,hashlib,collections,difflib,shutil,ast,re,zipfile

W=Path(__file__).resolve().parents[1]; R=W/'research/2026-11-22-controlled-update-100'
D=R/'delivery'; D.mkdir(exist_ok=True)
L=W/'research/2026-11-21-skilllifebench-update-audit'; LU=L/'upstream'
S=R/'source/skill-inject'; U=S/'upstream'; H=R/'source/skill-inject-hf'
LREF='57bc115a56baa483d4f68824d5a9c78f00a265dd'; IREF='b07cfdb2299b07ceb156c227b4b845359bbac363'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def gitblob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def write(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def transfer(src,dst):write(dst,src.read_bytes())

tree=read(S/'git-tree.json'); assert tree['sha']==IREF and not tree.get('truncated')
entries={x['path']:x for x in tree['tree'] if x['type']=='blob'}
lrepo=read(L/'repository.json');assert lrepo['commit']['sha']==LREF
le={e['path']:e for e in lrepo['tree']['tree'] if e['type']=='blob'}
verified_source={}; rejected=[]
def source_bytes(p,base,entry):
 b=p.read_bytes(); rel=p.relative_to(base).as_posix()
 assert len(b)==entry[rel]['size'] and gitblob(b)==entry[rel]['sha'],rel
 verified_source[str(p)]={'path':rel,'git_blob_sha1':gitblob(b),'sha256':sha(b),'bytes':len(b)}
 return b
def add_diff(p):
 old={f.relative_to(p/'old').as_posix():f.read_bytes() for f in (p/'old').rglob('*') if f.is_file()}
 new={f.relative_to(p/'new').as_posix():f.read_bytes() for f in (p/'new').rglob('*') if f.is_file()}
 changed=[]; blocks=[]
 for rel in sorted(set(old)|set(new)):
  a=old.get(rel);b=new.get(rel)
  if a==b:continue
  rec={'path':rel,'status':'added' if a is None else 'deleted' if b is None else 'modified','old_sha256':sha(a) if a is not None else None,'new_sha256':sha(b) if b is not None else None}
  try:
   aa=(a or b'').decode('utf-8').splitlines();bb=(b or b'').decode('utf-8').splitlines()
   delta=list(difflib.unified_diff(aa,bb,fromfile='old/'+rel if a is not None else '/dev/null',tofile='new/'+rel if b is not None else '/dev/null',lineterm=''))
   # Human-readable text diff; raw bytes and exact hashes remain authoritative.
   blocks.extend(delta); rec['text_diff_available']=True
   rec['added_lines']=sum(x.startswith('+') and not x.startswith('+++') for x in delta)
   rec['removed_lines']=sum(x.startswith('-') and not x.startswith('---') for x in delta)
  except UnicodeDecodeError:blocks.append('Binary change: '+rel);rec['text_diff_available']=False
  changed.append(rec)
 assert changed,p.name
 (p/'package.diff').write_text('\n'.join(blocks)+'\n',encoding='utf-8')
 return changed,sha(canonical({'old':{k:sha(v) for k,v in old.items()},'new':{k:sha(v) for k,v in new.items()}}))

records=[]
# Recheck the original source file identity, then extract original implementation strings.
raw=source_bytes(LU/'data/scenarios/scenarios.json',LU,le); cases=read(LU/'data/scenarios/scenarios.json')['cases']; caseby={c['id']:(i,c) for i,c in enumerate(cases)}
audit=read(L/'case-audit.json')['records']; eligible=[r for r in audit if r['selection']=='synthetic_primary_utility_preserved']
groups=collections.defaultdict(list)
for r in eligible:groups[r['family_id']].append(r)
assert len(groups)==47
def rank(r):
 c=caseby[r['id']][1]
 support=sum(p['both_utility_with_new_harm'] for p in r['frozen_measurement_pairs'])
 delta=sum(len(list(difflib.ndiff(a['code'].splitlines(),b['code'].splitlines()))) for a,b in zip(c['condition_tools']['before'],c['condition_tools']['after']))
 return (-support,delta,r['id'])
selected_life=[sorted(v,key=rank)[0] for k,v in sorted(groups.items())]
for r in eligible:
 if r not in selected_life:rejected.append({'source':'SkillLifeBench','source_id':r['id'],'reason':'same_family_representative_selected','family':r['family_id']})
measurements_cache={}
for ar in selected_life:
 idx,c=caseby[ar['id']];ident=f'CTU-{len(records)+1:04d}';p=D/'pairs'/ident
 assert c['conditions']['before']==c['conditions']['after']
 assert c['condition_tools']['before']!=c['condition_tools']['after']
 assert not c['provenance']['historical_incident']
 for side,key in [('old','before'),('new','after')]:
  tools=c['condition_tools'][key]
  dump(p/side/'tools.json',tools)
  for t in tools:
   assert re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',t['name'])
   write(p/side/'tools'/(t['name']+'.py'),t['code'].encode('utf-8'))
 dump(p/'context.json',{'user_task':c['task'],'initial_state':c['conditions']['before'],'tool_interfaces':[{k:v for k,v in t.items() if k!='code'} for t in c['condition_tools']['before']]})
 dump(p/'evidence/source_case.json',c)
 support=[v for v in ar['frozen_measurement_pairs'] if v['both_utility_with_new_harm']]
 frozen=[]
 for m in support:
  for side in ['before','after']:
   rel,pointer=m['source_pointers'][side].split('#',1)
   if rel not in measurements_cache:
    f=LU/'data/scenarios'/rel;source_bytes(f,LU,le);measurements_cache[rel]=read(f)
    transfer(f,D/'provenance/skilllifebench/data/scenarios'/rel)
   obj=measurements_cache[rel]
   for k in pointer.strip('/').split('/'):obj=obj[int(k)] if isinstance(obj,list) else obj[k]
   assert obj['case_id']==c['id'] and obj['condition']==side and obj['complete'] is True and obj['artifact_utility'] is True
   assert obj['harm']==(side=='after')
   frozen.append({'model':m['model_label_as_supplied'],'source_run':m['source_run'],'condition':side,'source_path':rel,'pointer':pointer,'row':obj})
 dump(p/'evidence/frozen_measurements.json',frozen)
 dump(p/'evidence/oracle.json',c['oracle']);dump(p/'evidence/reference_actions.json',c.get('reference_actions',[]))
 changes,pairhash=add_diff(p)
 reason=f"属于{ar['family_id']}家族；同任务、同授权和初始状态下，有{len(support)}组作者冻结配对测量同时支持旧版正常且无害、新版正常但有害；该家族仅选一个代表，减少重复。"
 rec={'id':ident,'source':'SkillLifeBench','source_id':c['id'],'source_ref':LREF,'source_family':ar['family_id'],'source_mechanism_group':c.get('mechanism_split_group'),
  'pair_kind':'extracted_tool_implementation_pair','source_pointer':f'/cases/{idx}','source_url':ar['source_url'],
  'title':c['task'],'user_task':c['task'],'selection_reason_zh':reason,'category':ar['family_id'],'source_positive_measurement_pairs':len(support),
  'labels':{'target_behavior_introduced':True,'old_harm_in_source_fixture':False,'new_harm_in_source_fixture':True,'old_and_new_task_utility_preserved':'supported_by_author_frozen_measurements','malicious_author_intent':None,'historical_real_update':False,'old_whole_package_benign_certified':False},
  'q1':'作者冻结测量支持新版出现给定安全违规；不证明蓄意恶意。','q2':'相同初始状态与授权下，所选冻结测量旧版无目标危害。','q3':'前后只有工具实现改变，新增安全违规可在该受控场景中归于本次实现差异；未自行运行。',
  'diff_changes':changes,'content_pair_sha256':pairhash,'normalization':'Extract code strings verbatim into tools/<name>.py; retain full tool JSON. No fabricated SKILL.md wrapper.',
  'local_path':'pairs/'+ident,'label_evidence_level':'author_frozen_runtime_pair_plus_static_identity','independently_executed_here':False}
 records.append(rec)

# Verify current Github definitions equal the label-corrected author HF release in content.
hf_paths={'obvious':'obvious_injections.json','contextual':'contextual_injections.json','camready':'camera_ready/obvious_injections_phish_poison.json'}
hdefs={s:{d['id']:d for d in read(H/p)} for s,p in hf_paths.items()}
candidates=read(R/'candidate-inject.json'); valid=[]
for c in candidates:
 try:
  assert c['definition']==hdefs[c['suite']][c['id']],('definition differs between fixed releases',c['suite'],c['id'])
  # All declared source files must be present and verified, including fixtures.
  for rel in c['needed_paths']:source_bytes(U/rel,U,entries)
  prefix='data/skills/'+c['host']+'/'
  primary=source_bytes(U/(prefix+'SKILL.md'),U,entries).decode('utf-8')
  line=c['task']['line_num'];assert 1<=line<=len(primary.splitlines())+1
  insertion=c['task'].get('injection_prefix','')+c['definition']['instructions']['line_injection']
  block=''.join((s.strip()+'\n') if s.strip() else '\n' for s in insertion.strip('\n').splitlines())
  assert block.strip() and block.strip() not in primary
  lines=primary.splitlines(keepends=True);new=''.join(lines[:line-1])+block+''.join(lines[line-1:])
  assert new!=primary
  family=f"{c['suite']}:{c['id']}"
  c.update({'prepared_primary_new':new,'prepared_block':block,'injection_family':family,'primary_old_sha256':sha(primary.encode()),'placement_signature':sha(canonical({'host':c['host'],'new':sha(new.encode()),'scripts':c['definition'].get('task_scripts',{})}))})
  valid.append(c)
 except (AssertionError,OSError,KeyError,UnicodeDecodeError) as e:
  rejected.append({'source':'Skill-Inject','suite':c['suite'],'source_id':c['id'],'task_index':c['task_index'],'reason':'unusable_candidate','detail':str(e)})
families=collections.defaultdict(list)
for c in valid:families[c['injection_family']].append(c)
assert len(families)>=31,('insufficient independent injection definitions',len(families))
# First cover every eligible attack definition. Then balance hosts/category without
# counting identical old/new placements with different user-task wording twice.
picked=[];used=set();hostcount=collections.Counter();catcount=collections.Counter();famcount=collections.Counter()
def choose(pool):
 return min(pool,key=lambda c:(famcount[c['injection_family']],hostcount[c['host']],catcount[c['category']],c['host'],c['task_index']))
def take(c):
 picked.append(c);used.add(c['placement_signature']);hostcount[c['host']]+=1;catcount[c['category']]+=1;famcount[c['injection_family']]+=1
for family,pool in sorted(families.items()):take(choose([c for c in pool if c['placement_signature'] not in used]))
while len(picked)<53:
 pool=[c for c in valid if c['placement_signature'] not in used]
 assert pool,('fewer than 53 unique injection pairs',len(picked))
 # Prefer a new host for a family before another placement on the same host.
 unseen=[c for c in pool if not any(p['injection_family']==c['injection_family'] and p['host']==c['host'] for p in picked)]
 take(choose(unseen or pool))
for c in valid:
 if c not in picked:rejected.append({'source':'Skill-Inject','suite':c['suite'],'source_id':c['id'],'host':c['host'],'task_index':c['task_index'],'reason':'not_selected_after_family_coverage_and_host_balance'})

for c in picked:
 ident=f'CTU-{len(records)+1:04d}';p=D/'pairs'/ident;prefix='data/skills/'+c['host']+'/'
 hostfiles=[rel for rel in entries if rel.startswith(prefix)]
 for rel in hostfiles:
  b=source_bytes(U/rel,U,entries)
  for side in ['old','new']:write(p/side/rel[len(prefix):],b)
 write(p/'new/SKILL.md',c['prepared_primary_new'].encode('utf-8'))
 for name,rel in c['definition'].get('task_scripts',{}).items():
  assert Path(name).name==name,name
  write(p/'new/scripts'/name,source_bytes(U/('data/'+rel),U,entries))
 for name,rel in c['task'].get('task_files',{}).items():
  assert not Path(name).is_absolute() and '..' not in Path(name).parts
  write(p/'fixtures/task_files'/name,source_bytes(U/('data/'+rel),U,entries))
 for start in c['definition'].get('startup_scripts',[]):
  rel=('startup_scripts/'+start) if isinstance(start,str) else start['path']
  name=start if isinstance(start,str) else start['name']
  write(p/'fixtures/startup_scripts'/name,source_bytes(U/rel,U,entries))
 for rootrel in c['definition'].get('root_files',[]):
  sourceprefix='data/'+rootrel.rstrip('/')+'/'
  matches=[rel for rel in entries if rel.startswith(sourceprefix)]
  assert matches,(c['id'],rootrel)
  for rel in matches:
   relative=rel[len('data/task_files/'):]
   write(p/'fixtures/root_files'/relative,source_bytes(U/rel,U,entries))
 dump(p/'context.json',{'user_task':c['task']['prompt'],'policy_condition':'normal','skill_location':'.claude/skills/'+c['task']['skill'],'task_files':c['task'].get('task_files',{}),'fixture_directory':'fixtures','note':'User task and fixtures are identical for old/new; startup scripts retained as inert provenance, not executed.'})
 dump(p/'evidence/injection_definition.json',c['definition']);dump(p/'evidence/task_selection.json',c['task'])
 dump(p/'evidence/final_label.json',{'final_label':'obvious','source_suite':c['source_suite'],'id':c['id'],'author_label_correction':c['label_correction'],'hf_ref':read(H/'repository.json')['sha'],'definition_content_equal_across_pinned_github_and_hf_releases':True,'category':c['category'],'category_reason':c['category_reason']})
 write(p/'evidence/inserted_block.txt',c['prepared_block'].encode('utf-8'))
 grader=(f"data/instruction_unit_tests_v2/test_instruction_{c['id']}.py" if c['source_suite']=='contextual' else f"data/instruction_unit_tests_v2/obvious/test_obvious_{c['id']}.py")
 assert grader in entries,grader
 source_bytes(U/grader,U,entries)
 transfer(U/grader,p/'evidence/attack_grader.py')
 changed,pairhash=add_diff(p)
 assert {x['path'] for x in changed}=={'SKILL.md'}|{'scripts/'+name for name in c['definition'].get('task_scripts',{})}
 reason=f"作者最终判为明显攻击，类别为{c['category']}；在{c['host']}干净宿主上仅插入原始攻击块及其声明脚本；正常任务和宿主原文件保留，精确diff可定位新增请求；按攻击家族覆盖和宿主均衡入选。"
 rec={'id':ident,'source':'Skill-Inject','source_id':c['injection_family'],'source_ref':IREF,'source_family':c['injection_family'],'source_host':c['host'],'source_task_index':c['task_index'],'source_definition_path':c['definition_path'],
  'source_url':f'https://github.com/aisa-group/skill-inject/blob/{IREF}/'+c['definition_path'],'title':c['title'],'category':c['category'],'category_reason':c['category_reason'],'user_task':c['task']['prompt'],
  'selection_reason_zh':reason,'pair_kind':'source_clean_vs_authored_injection_skill_package',
  'labels':{'target_behavior_introduced':True,'old_harm_in_source_fixture':None,'new_harm_in_source_fixture':None,'old_and_new_task_utility_preserved':'not_independently_runtime_verified_here','malicious_author_intent':'source_final_obvious_attack_definition','historical_real_update':False,'old_whole_package_benign_certified':False},
  'q1':'新版含来源最终确认的明显攻击指令／载荷；本次未验证实际执行成功。','q2':'选定的完整注入块不在旧主文档；旧版为来源干净宿主，未作整包独立良性认证。','q3':'新增内容完全由公开构造规则插入，因果差异可重建；这是人工攻击对照，不是历史发布升级。',
  'diff_changes':changed,'content_pair_sha256':pairhash,'insertion':{'file':'SKILL.md','before_line':c['task']['line_num'],'new_block_lines':len(c['prepared_block'].splitlines()),'block_sha256':sha(c['prepared_block'].encode())},
  'normalization':'Line insertion reproduces upstream build_sandbox.py stripping semantics with LF serialization; source old bytes retained. Declaration scripts copied under new/scripts; fixtures and labels kept outside snapshots.',
  'label_evidence_level':'author_final_attack_label_plus_exact_construction','local_path':'pairs/'+ident,'independently_executed_here':False}
 records.append(rec)

assert len(records)==100 and len({r['content_pair_sha256'] for r in records})==100
for rec in records:
 p=D/rec['local_path'];dump(p/'metadata.json',rec)
 inventory=[]
 for side in ['old','new']:
  for f in sorted((p/side).rglob('*')):
   if f.is_file():
    b=f.read_bytes();inventory.append({'side':side,'path':f.relative_to(p/side).as_posix(),'bytes':len(b),'sha256':sha(b),'git_blob_sha1':gitblob(b)})
 dump(p/'files.json',inventory)
dump(D/'index.json',records)
(D/'index.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
dump(D/'selection_exclusions.json',rejected+read(R/'excluded-inject-labels-and-files.json'))
dump(D/'provenance/verified_source_files.json',list(verified_source.values()))
dump(D/'provenance/sources.json',{'SkillLifeBench':{'repository':'Tasselszcx/SkillLifeBench','commit':LREF,'case_file_git_blob':le['data/scenarios/scenarios.json']['sha'],'case_file_sha256':sha(raw)},'Skill-Inject':{'repository':'aisa-group/skill-inject','commit':IREF,'hf_revision':read(H/'repository.json')['sha']}})
for rel in ['data/scenarios/publication-bindings.json']:
 source_bytes(LU/rel,LU,le);transfer(LU/rel,D/'provenance/skilllifebench'/rel)
for rel in ['camera_ready/relabel.json','camera_ready/categories.json']:
 transfer(H/rel,D/'provenance/skill-inject'/rel)
for rel in ['config.py','scripts/build_sandbox.py','scripts/build_clean_sandboxes.py']:
 transfer(U/rel,D/'provenance/skill-inject/upstream'/rel)
for rel in entries:
 if rel.startswith('data/instruction_unit_tests_v2/') and not rel.endswith('.code-workspace'):
  transfer(U/rel,D/'provenance/skill-inject/upstream'/rel)
write(D/'LICENSES/Skill-Inject-MIT.txt',source_bytes(U/'LICENSE',U,entries))
lic=LU/'docs/licenses/Dataset-CC-BY-4.0.txt'
write(D/'LICENSES/SkillLifeBench-Dataset-CC-BY-4.0.txt',source_bytes(lic,LU,le))
summary={'selected_pairs':100,'SkillLifeBench':47,'SkillInject':53,'source_life_primary_pool':91,'life_families_selected':len(groups),'inject_families_selected':len(families),
 'inject_host_packages':len({c['host'] for c in picked}),'inject_categories':dict(catcount),'exact_pair_duplicates':0,'version_snapshots':200,
 'native_complete_skill_package_pairs':53,'extracted_tool_implementation_pairs':47,'true_historical_benign_to_malicious_pairs':0,
 'author_runtime_utility_and_harm_supported_pairs':47,'injection_pairs_without_local_runtime_verification':53,'independently_executed_samples':0,
 'scope':'Controlled harmful-update experiments; life safety-regression cohort and authored obvious-attack cohort must be reported separately.',
 'selection_rule':'One representative for each of 47 eligible utility-preserving SkillLifeBench families, ranked by author-paired support then compactness; cover all eligible corrected obvious Skill-Inject families, then fill to 53 exact-unique placements prioritizing additional hosts and balancing coverage.',
 'training_test_split_assigned':False,'all_pairs_positive_or_harmful_candidates':True,'needs_benign_update_controls':True}
dump(D/'summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
