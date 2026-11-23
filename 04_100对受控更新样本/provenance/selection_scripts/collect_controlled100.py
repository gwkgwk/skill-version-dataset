"""Download inert source data only. Never import or execute upstream code."""
from pathlib import Path
import urllib.request,json,hashlib,sys,concurrent.futures
ROOT=Path(__file__).resolve().parent/'2026-11-22-controlled-update-100'
SOURCE=ROOT/'source'/'skill-inject'; SOURCE.mkdir(parents=True,exist_ok=True)
REF='b07cfdb2299b07ceb156c227b4b845359bbac363'
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ControlledSkillUpdateResearch/1.0'}),timeout=90) as r:return r.read()
def dump(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
treepath=SOURCE/'git-tree.json'
if not treepath.exists():treepath.write_bytes(get(f'https://api.github.com/repos/aisa-group/skill-inject/git/trees/{REF}?recursive=1'))
TREE=json.loads(treepath.read_bytes());assert TREE['sha']==REF and not TREE.get('truncated')
ENTRIES={x['path']:x for x in TREE['tree'] if x['type']=='blob'}
def fetch(path):
 p=SOURCE/'upstream'/path;e=ENTRIES[path]
 if p.exists():data=p.read_bytes()
 else:
  data=get(f'https://raw.githubusercontent.com/aisa-group/skill-inject/{REF}/{path}')
  assert len(data)==e['size'] and blob(data)==e['sha'],path
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 assert blob(data)==e['sha'],path
 return {'path':path,'size':len(data),'git_blob_sha1':e['sha'],'sha256':hashlib.sha256(data).hexdigest()}
INITIAL=['data/obvious_injections.json','data/contextual_injections.json','data/obvious_injections_camready_phish_poison.json','data/obvious_to_contextual_camready.json','data/tasks.json','config.py','scripts/build_sandbox.py','scripts/build_clean_sandboxes.py','LICENSE','README.md']
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--hf-definitions':
  hf=ROOT/'source/skill-inject-hf';ref=json.loads((hf/'repository.json').read_bytes())['sha']
  rels=['obvious_injections.json','contextual_injections.json','camera_ready/obvious_injections_phish_poison.json']
  def hf_fetch(rel):
   p=hf/rel;p.parent.mkdir(parents=True,exist_ok=True)
   if not p.exists():p.write_bytes(get(f'https://huggingface.co/datasets/davidsmts/skill-inject/resolve/{ref}/{rel}'))
   return {'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(hf_fetch,rels))
  dump(hf/'definitions-receipt.json',{'ref':ref,'files':results});print(json.dumps(results));raise SystemExit(0)
 paths=INITIAL if len(sys.argv)==1 else json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
 ok=[];failed=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
  futures={ex.submit(fetch,p):p for p in paths}
  for f in concurrent.futures.as_completed(futures):
   try:ok.append(f.result())
   except Exception as e:failed.append({'path':futures[f],'error':str(e)})
 dump(SOURCE/'last-download-receipt.json',{'ref':REF,'verified':ok,'failed':failed})
 if len(sys.argv)==1:
  hf=ROOT/'source/skill-inject-hf';hf.mkdir(parents=True,exist_ok=True)
  info=json.loads(get('https://huggingface.co/api/datasets/davidsmts/skill-inject'));ref=info['sha'];dump(hf/'repository.json',info)
  for rel in ['camera_ready/relabel.json','camera_ready/categories.json','README.md']:
   p=hf/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(get(f'https://huggingface.co/datasets/davidsmts/skill-inject/resolve/{ref}/{rel}'))
 print(json.dumps({'requested':len(paths),'downloaded_verified':len(ok),'failed':failed},ensure_ascii=False))
 if failed:raise SystemExit(2)
