"""Offline provenance/byte verification only; never execute Skill code."""
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def git_blob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def normalize(text):
    text=text.replace('\r\n','\n')
    if text.startswith('---\n') and '\n---' in text[4:]:
        end=text.index('\n---',4)
        return re.sub(r'(?m)^\s*(?:version|updated_at|last_updated|last-modified):[^\n]*\n?', '',text[4:end])+text[end:]
    return text


def main():
    rows=read(ROOT/'updates.json');summary=read(ROOT/'summary.json');seen=set();files=0;size=0;checked={}
    assert len(rows)==summary['packaged_real_update_pairs']
    assert len({(r['repository'],r['skill_directory']) for r in rows})==len(rows)
    for i,row in enumerate(rows,1):
        assert row['id']==f'OPU-{i:04d}'
        directory=ROOT/row['local_directory'];assert directory.resolve().is_relative_to(ROOT)
        assert read(directory/'metadata.json')==row
        commit=read(directory/'lineage.json')
        assert commit['sha']==row['new_commit'] and commit['parents'][0]['sha']==row['old_commit']
        assert row['old_commit']!=row['new_commit']
        assert all(row[k]=='benign' for k in ['old_security_label','new_security_label','update_security_label'])
        assert row['human_review_confirmed'] and row['human_review']['label_basis']=='user_attestation'
        assert row['human_review']['reviewer_identity'] is None and row['human_review']['actual_review_date'] is None
        assert row['human_review']['independently_validated_by_assistant'] is False
        signature=[]
        for side in ['old','new']:
            records=row[side]['files'];root=directory/side
            assert {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}=={f['path'] for f in records}
            mapping={}
            for record in records:
                p=root/record['path'];assert p.resolve().is_relative_to(root.resolve()) and not p.is_symlink()
                data=p.read_bytes();assert len(data)==record['size']
                assert git_blob(data)==record['git_blob_sha1']
                sha=hashlib.sha256(data).hexdigest();assert sha==record['sha256'];checked[p.resolve()]=sha
                mapping[record['path']]=record['git_blob_sha1'];files+=1;size+=len(data)
            tree=read(directory/(side+'-tree.json'))
            assert not tree.get('truncated')
            assert {e['path']:e['sha'] for e in tree['tree'] if e['type']=='blob'}==mapping
            signature.append(tuple((f['path'],f['git_blob_sha1'],f['mode']) for f in sorted(records,key=lambda f:f['path'])))
        signature=tuple(signature);assert signature not in seen;seen.add(signature)
        assert normalize((directory/'old/SKILL.md').read_text(encoding='utf-8-sig'))!=normalize((directory/'new/SKILL.md').read_text(encoding='utf-8-sig'))
    assert files==summary['original_file_count'] and size==summary['original_bytes']
    confirmation=read(ROOT/'human_review_confirmation.json')
    assert confirmation['confirmed_update_pairs']==500 and confirmation['confirmed_version_snapshots']==1000
    assert confirmation['case_ids']==[r['id'] for r in rows]
    assert confirmation['independently_validated_by_assistant'] is False
    assert [json.loads(s) for s in (ROOT/'updates.jsonl').read_text(encoding='utf-8').splitlines()]==rows
    if (ROOT/'MANIFEST.sha256').exists():
        for line in (ROOT/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
            sha,name=line.split('  ',1);path=ROOT/name
            actual=checked.get(path.resolve())
            if actual is None:actual=hashlib.sha256(path.read_bytes()).hexdigest()
            assert actual==sha,name
    print(json.dumps({'status':'passed','real_update_pairs':len(rows),'original_snapshots':2*len(rows),
                      'files_checked':files,'bytes_checked':size,'user_reported_human_confirmed_benign_pairs':500,'assistant_independent_security_audit_completed':False,'sample_code_executed':False},indent=2))


if __name__=='__main__':main()
