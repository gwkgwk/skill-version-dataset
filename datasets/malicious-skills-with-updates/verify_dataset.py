"""Verify the curated update evidence without running any skill."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
load=lambda path:json.loads(path.read_text(encoding='utf-8'))

def main():
    candidates=load(ROOT/'candidates/skills.json')
    assert {x['skill_id'] for x in candidates}=={'zaycv/clawhub','zaycv/shield'}
    assert all(len({v['version'] for v in x['versions']})>=2 for x in candidates)
    assert len(load(ROOT/'excluded_single_version/index.json'))==98
    case=ROOT/'confirmed_updates/MCU-0001'
    metadata=load(case/'metadata.json');inventory=load(case/'files.json')
    assert metadata['old_commit']=='8275d463c9b25401d80098b07e65530444af8ff0'
    assert metadata['new_commit']=='93d548f298d9d996a42da85de09f9860136c2280'
    assert not metadata['benign_to_malicious_truth_confirmed']
    count=0
    for side,files in inventory.items():
        assert {p.relative_to(case/side).as_posix() for p in (case/side).rglob('*') if p.is_file()}=={f['path'] for f in files}
        for item in files:
            data=(case/side/item['path']).read_bytes()
            assert len(data)==item['bytes']
            assert hashlib.sha256(data).hexdigest()==item['sha256']
            assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['git_blob_sha1']
            count+=1
    assert 'github.com/Ddoy233/openclawcli' not in (case/'old/SKILL.md').read_text(encoding='utf-8')
    assert 'github.com/Ddoy233/openclawcli' in (case/'new/SKILL.md').read_text(encoding='utf-8')
    for line in (ROOT/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        digest,relative=line.split('  ',1);path=(ROOT/relative).resolve()
        assert path.is_relative_to(ROOT) and hashlib.sha256(path.read_bytes()).hexdigest()==digest,relative
    print(json.dumps({'verified':True,'confirmed_update_skills':1,'candidate_skills':2,'excluded_single_version_skills':98,'original_files_verified':count}))

if __name__=='__main__':main()
