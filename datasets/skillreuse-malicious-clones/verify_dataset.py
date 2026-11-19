"""Verify inert metadata and hashes; never execute downloaded Skill content."""
import argparse,collections,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--corpus',type=Path);args=parser.parse_args()
    checks=[]
    for line in (ROOT/'MANIFEST.sha256').read_text(encoding='utf-8').splitlines():
        sha,name=line.split('  ',1);p=ROOT/name
        assert p.resolve().is_relative_to(ROOT.resolve())
        assert hashlib.sha256(p.read_bytes()).hexdigest()==sha,name
    checks.append('all packaged file hashes match MANIFEST.sha256')
    summary=read('summary.json');rows=read('malicious_snapshots_index.json');fixtures=read('security_test_fixtures_index.json')
    assert len(rows)==summary['malicious_loader_snapshots']==62
    assert len({r['content_sha256'] for r in rows})==summary['malicious_loader_distinct_content_hashes']==42
    assert len(fixtures)==1 and fixtures[0]['path'].startswith('tests/')
    assert all(r['security_label']=='campaign_loader_instruction_confirmed' for r in rows)
    assert all(any(e['encoding'].startswith('base64_') and e['fetch_command'] and e['execution_command'] and e['known_campaign_ip']=='91.92.242.30' for e in r['evidence']) for r in rows)
    records={r['sample_id']:r for r in rows+fixtures}
    for r in rows+fixtures:
        assert not r['has_verified_version_update']
        assert r['published_version'] is None and r['git_commit_version'] is None and r['first_malicious_version'] is None
        assert not r['original_record_included']
        assert r['snapshot_version']=='sha256:'+r['content_sha256']
        assert (ROOT/r['content_file']).is_file()
        assert read(str(Path(r['content_file']).with_name('record.json')))==r
    checks.append('62 original-content hash identities, security classifications and defanged artifact references verified')
    pairs=read('confirmed_exact_content_clone_pairs.json');groups=read('confirmed_exact_content_clone_groups.json')
    assert len(groups)==len(pairs)==20
    expected=[]
    for g in groups:
        members=[records[x] for x in g['sample_ids']]
        assert len(members)>=2
        assert len({r['content_sha256'] for r in members})==1
        assert members[0]['content_sha256']==g['content_sha256']
        assert len({(r['repoFullName'],r['path']) for r in members})==g['distinct_source_paths']
        for i,a in enumerate(members):
            for b in members[i+1:]:
                if (a['repoFullName'],a['path'])!=(b['repoFullName'],b['path']):expected.append((a['sample_id'],b['sample_id'],a['content_sha256']))
    assert expected==[(r['sample_a'],r['sample_b'],r['content_sha256']) for r in pairs]
    assert all(not p['is_version_update'] for p in pairs)
    checks.append('20 exact-content clone pairs across distinct source paths verified')
    repo=read('evidence/upstream_repository.json');tree={x['path']:x for x in repo['tree']['tree']}
    for p in (ROOT/'evidence/upstream').rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(ROOT/'evidence/upstream').as_posix();b=p.read_bytes()
        assert hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()==tree[rel]['sha']
    checks.append('original public graph and README match immutable upstream Git blob hashes')
    edges=read('published_graph_candidate_edges.json');assert len(edges)==632
    assert sum(e['both_names_have_payload_matching_records'] for e in edges)==2
    assert all(e['security_label'] is None and e['status'].startswith('candidate_only') and not e['is_version_update'] for e in edges)
    endpoints=read('unverified/graph_endpoint_source_records.json');names=collections.defaultdict(list)
    for r in endpoints:names[r['scopedName']].append(r)
    for e in edges:
        for side in ['a','b']:
            ns=names[e['skill_'+side]]
            assert e['endpoint_'+side+'_corpus_record_count']==len(ns)
            assert e['endpoint_'+side+'_distinct_content_hashes']==len({r['content_sha256'] for r in ns})
    checks.append('632 graph links retain unknown security labels and explicit name-to-content ambiguity')
    assert summary['verified_version_update_pairs_added']==0 and summary['previous_verified_update_skill_total_unchanged']==37
    assert not summary['paper_three_payload_retaining_links_independently_reproduced']
    corpus_verified=False
    if args.corpus:
        target={r['line_number']:r for r in rows+fixtures};md5=hashlib.md5();sha=hashlib.sha256();n=0
        with args.corpus.open('rb') as inp:
            for n,b in enumerate(inp,1):
                md5.update(b);sha.update(b)
                if n not in target:continue
                r=target[n];d=json.loads(b);content=d['full_content'].encode('utf-8')
                assert hashlib.sha256(b).hexdigest()==r['record_sha256']
                assert hashlib.sha256(content).hexdigest()==r['content_sha256']
                assert hashlib.sha1(f'blob {len(content)}\0'.encode()+content).hexdigest()==r['content_git_blob_sha1']
                assert all(d[k]==r[k] for k in ['id','scopedName','repoFullName','path','githubUrl'])
        receipt=read('evidence/corpus_download_receipt.json')
        assert n==155547 and md5.hexdigest()==receipt['md5'] and sha.hexdigest()==receipt['sha256']
        corpus_verified=True;checks.append('all 63 indexed payload-bearing source records bound byte-for-byte to checksum-verified Zenodo corpus')
    result={'status':'passed','checks':checks,'original_corpus_reverified':corpus_verified,'sample_execution':False,'network_payload_fetch':False,'limitations':'Defanged copies cannot establish original hashes without the external 1.46 GB corpus. Published graph edges lack frozen source-content bindings. No release-version transitions established.'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
