# SkillReuse

Replication package for the paper *Latent Reuse in Agent Skills: Multi-modal
Clone Detection at Ecosystem Scale*.

## Citation

If you use SkillReuse or its datasets, please cite:

```bibtex
@inproceedings{zhu2026latent,
  author    = {Jiaying Zhu and Lyuye Zhang and Wenbo Guo and Yang Liu},
  title     = {Latent Reuse in Agent Skills: Multi-modal Clone Detection at Ecosystem Scale},
  booktitle = {Proceedings of the 41st IEEE/ACM International Conference on Automated Software Engineering},
  year      = {2026},
  doi       = {10.1145/3832783.3837468}
}
```

## Folder Structure

```
skill-reuse/
├── src/                        # Source code
│   ├── pipeline.py             # End-to-end pipeline orchestrator (Phases 0-5)
│   ├── pipeline_v2.py          # Lightweight pipeline variant (embedding + candidates)
│   ├── models.py               # Data models (Skill, CodeBlock, PipelineMetrics)
│   ├── llm_config.py           # LLM provider configuration (OpenAI / Anthropic)
│   ├── phase0_characterization.py  # Phase 0: Skill characterisation and language detection
│   ├── phase1_preprocessing.py     # Phase 1: Multi-modal decomposition (YAML / NL / code)
│   ├── phase2_similarity.py        # Phase 2: Per-channel similarity (TF-IDF, MinHash, edit dist.)
│   ├── phase3_fusion.py            # Phase 3: Cross-modal logistic fusion with interaction terms
│   ├── phase4_graph.py             # Phase 4: Clone-graph construction and community detection
│   ├── phase5_blast_radius.py      # Phase 5: Blast-radius and propagation analysis
│   ├── contrastive_fusion.py       # Contrastive cross-modal fusion model
│   ├── local_embeddings.py         # Local TF-IDF + SVD multi-modal embeddings
│   ├── embeddings.py               # OpenAI-backed embedding utilities
│   ├── ast_similarity.py           # AST-level structural similarity
│   ├── security_propagation.py     # Vulnerability propagation through clone graph
│   ├── benchmark.py                # SkillReuse-Bench: benchmark construction and evaluation
│   ├── annotator.py                # LLM-based clone-pair annotation
│   ├── run_evaluation.py           # Full evaluation driver (SkillReuse + baselines)
│   ├── run_eval_local.py           # Local-only evaluation (no API embeddings)
│   ├── run_eval_cached.py          # Cached evaluation with pre-computed embeddings
│   └── phase_a_fetch_content.py    # Skill content fetcher from GitHub
├── data/
│   ├── skills_content/
│   │   └── skills_with_content.jsonl   # 155k skills with full content (Zenodo; see below)
│   ├── skills_catalog.json             # Skill catalogue metadata
│   └── gold_standard/
│       └── annotation_guidelines.md    # Manual annotation guidelines
├── benchmark/
│   ├── auto_labeled.jsonl          # 300 labelled clone pairs (SkillReuse-Bench)
│   ├── synthetic_contents.jsonl    # Synthetic mutations for Type-2/3 pairs
│   ├── evaluation_results.json     # Evaluation results (Table 3 in paper)
│   ├── evaluation_results_v2.json  # Local-only evaluation results
│   └── benchmark_stats.json        # Benchmark composition statistics
├── scripts/
│   └── dump_fullcorpus_clusters.py  # Materialise the full-corpus clone graph (RQ3)
├── results/
│   └── ecosystem/                   # Full-corpus clone graph at theta = 0.80 (see "Clone graph")
│       ├── repro_fullcorpus_theta080_clusters.jsonl
│       ├── repro_fullcorpus_theta080_components.tsv
│       ├── repro_fullcorpus_theta080_edges.parquet
│       └── repro_fullcorpus_theta080_clusters_stats.json
├── config.ini.example          # LLM configuration template
├── requirements.txt            # Python dependencies
└── README.md
```

## Dataset

The full skill corpus (`data/skills_content/skills_with_content.jsonl`, 155,547 skills,
1.4 GB) is hosted on Zenodo due to GitHub's file size limit:

> **Download:** https://doi.org/10.5281/zenodo.19245910

After downloading, place the file at `data/skills_content/skills_with_content.jsonl`.

## Clone graph (RQ3)

`results/ecosystem/` ships the ecosystem-scale clone graph reported in Table 5, at the
conservative operating point **theta = 0.80**. These are the detected clone
relationships themselves, so the deduplication figures can be inspected per skill
rather than only in aggregate.

| File | Size | Contents |
|---|---|---|
| `repro_fullcorpus_theta080_clusters.jsonl` | 3.5 MB | One JSON object per multi-skill cluster, largest first: `{cluster_id, size, skill_ids[]}`. 10,365 clusters covering 91,792 skills. |
| `repro_fullcorpus_theta080_components.tsv` | 5.1 MB | `skill_id <TAB> component_id <TAB> component_size` for all 137,470 analysed skills, singletons included. |
| `repro_fullcorpus_theta080_edges.parquet` | 6.8 MB | All 1,059,923 clone pairs: `skill_a`, `skill_b`, `fused` (clone score), `cross_author`. |
| `repro_fullcorpus_theta080_clusters_stats.json` | 853 B | Derived statistics with a field-by-field comparison against Table 5. |

Skills are identified by scoped name (e.g. `@anthropics/docx`), matching the
`scopedName` field of the corpus records, so any file here joins directly against
`data/skills_content/skills_with_content.jsonl`.

The JSONL and TSV files need only the standard library. Reading the Parquet edge list
additionally requires `pyarrow` (and `pandas` for the DataFrame example below):

```bash
pip install pyarrow pandas
```

### Examples

Find the clone family a given skill belongs to:

```python
import csv
rows = {r["skill_id"]: r for r in csv.DictReader(open(
    "results/ecosystem/repro_fullcorpus_theta080_components.tsv"), delimiter="\t")}
print(rows["@anthropics/docx"])        # -> component_id, component_size
```

List the members of the largest clusters:

```python
import json
with open("results/ecosystem/repro_fullcorpus_theta080_clusters.jsonl") as fh:
    clusters = [json.loads(line) for line in fh]      # already sorted, largest first
print(clusters[1]["size"], clusters[1]["skill_ids"][:5])
```

Pull every clone of one skill, with its score:

```python
import pyarrow.parquet as pq
t = pq.read_table("results/ecosystem/repro_fullcorpus_theta080_edges.parquet")
df = t.to_pandas()
print(df[(df.skill_a == "@anthropics/docx") | (df.skill_b == "@anthropics/docx")])
```

Cross-author reuse only (95.3% of edges):

```python
print(df[df.cross_author].shape[0])     # -> 1010480
```

### Regenerating

```bash
python3 scripts/dump_fullcorpus_clusters.py --theta 0.80
```

The script streams the cached full-corpus scoring run (`full_155k_run/`, candidate-pair
scores as Parquet), thresholds the fused score, and runs connected components. Like the
other corpus-scale analyses it requires that run as an external input; `--theta` accepts
any threshold in the reported sweep. Every figure written to
`repro_fullcorpus_theta080_clusters_stats.json` is recomputed from the pair scores, and
the graph is self-consistent: rebuilding the components from `edges.parquet` alone
reproduces the same partition (56,043 components, 45,678 singletons, largest 61,651).

## Environment Setup

**Python 3.10+** is required.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure LLM access (needed only for LLM-based phases)
cp config.ini.example config.ini
# Edit config.ini to add your API key, or set the environment variable:
export OPENAI_API_KEY="sk-..."
```

> The pipeline and evaluation scripts can run **without** an LLM key when using
> local-only mode (`run_eval_local.py`), which relies on TF-IDF + SVD embeddings.

## Running the Experiments

### Reproduce main results (Table 3 -- no API key needed)

```bash
python -m src.run_eval_local 5000
```

This loads up to 5 000 skills, builds SkillReuse-Bench (300 pairs), trains the
logistic fusion model, runs all baselines, and prints the full results table
including per-clone-type recall and the ablation study. Results are saved to
`benchmark/evaluation_results.json`.

### Run the full pipeline (Phases 0-5)

```bash
python -m src.pipeline
```

Runs all six phases on a 10% stratified sample and writes a Markdown report to
`results/partial/`.

### Run evaluation with API embeddings

```bash
python -m src.run_evaluation 5000
```

Requires an OpenAI API key. Computes API-backed embeddings and runs the full
evaluation suite.

### Pre-computed results

The `benchmark/` directory ships with pre-computed evaluation results so that
reviewers can inspect the numbers without re-running the pipeline:

- `evaluation_results.json` -- main results (Table 3)
- `evaluation_results_v2.json` -- local-only results
- `benchmark_stats.json` -- benchmark composition (Table 2)
