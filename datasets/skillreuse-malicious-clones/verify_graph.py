"""Read published Parquet as data and verify the filtered edge list."""
import json
from pathlib import Path
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parent
rows=json.loads((ROOT/'malicious_snapshots_index.json').read_text(encoding='utf-8'))+json.loads((ROOT/'security_test_fixtures_index.json').read_text(encoding='utf-8'))
names=pa.array(sorted({r['scopedName'] for r in rows}))
table=pq.read_table(ROOT/'evidence/upstream/results/ecosystem/repro_fullcorpus_theta080_edges.parquet')
assert len(table)==1059923
mask=pc.or_(pc.is_in(table['skill_a'],value_set=names),pc.is_in(table['skill_b'],value_set=names))
actual=table.filter(mask).to_pylist()
stored=json.loads((ROOT/'published_graph_candidate_edges.json').read_text(encoding='utf-8'))
assert actual==[{k:r[k] for k in ['skill_a','skill_b','fused','cross_author']} for r in stored]
assert len(actual)==632
print(json.dumps({'status':'passed','original_graph_edges':len(table),'reproduced_candidate_edges':len(actual),'payload_status_not_inferred_from_edges':True}))
