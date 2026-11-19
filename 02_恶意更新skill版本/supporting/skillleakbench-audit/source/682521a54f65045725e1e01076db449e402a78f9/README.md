# How Your Credentials Are Leaked by LLM Agent Skills: An Empirical Study

[![ASE 2026](https://img.shields.io/badge/ASE-2026-b31b1b.svg)](https://conf.researchr.org/home/ase-2026)
[![arXiv](https://img.shields.io/badge/arXiv-2604.03070-orange.svg)](https://arxiv.org/abs/2604.03070)
[![dataset: HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20dataset-HuggingFace-yellow.svg)](https://huggingface.co/datasets/AgentSkillPrivacy/SkillLeakBench)
[![Artifact: Zenodo](https://img.shields.io/badge/artifact-Zenodo-blue.svg)](https://doi.org/10.5281/zenodo.19367969)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

This repository contains the credential-leakage **dataset**, **detection pipeline**, and a
**reproducible analysis suite** introduced in our ASE 2026 paper, [*How Your Credentials Are Leaked
by LLM Agent Skills: An Empirical Study*](https://arxiv.org/abs/2604.03070). We collected __170,226 skills__ from
SkillsMP, an agent-skill marketplace, and analyzed a **17,022-skill**
sample through static secret extraction, dynamic sandbox testing with mock credentials, and
manual classification by three security reviewers. We identified **520 affected skills** with
**1,708 security issues** and a taxonomy of **10 leakage patterns** (4 vulnerability + 6 malicious).

## Citation

If you use this dataset or framework, please cite:

```bibtex
@inproceedings{skillleakbench2026,
  title     = {How Your Credentials Are Leaked by {LLM} Agent Skills: An Empirical Study},
  author    = {Chen, Zhihao and Zhang, Ying and Liu, Yi and Deng, Gelei and Li, Yuekang and Zhang, Yanjun and Ning, Jianting and Zhang, Leo and Ma, Lei and Li, Zhiqiang},
  booktitle = {Proceedings of the 41st IEEE/ACM International Conference on Automated Software Engineering (ASE)},
  year      = {2026},
  note      = {To appear},
}
```

## Reproduce the results (offline, no secrets)

Every reported dataset/taxonomy number is regenerated from `data/` alone — no API keys, no Docker:

```bash
pip install -r requirements.txt
python3 code/helper.py             # interactive menu (banner + options); or use subcommands:
python3 code/helper.py doctor      # check environment
python3 code/helper.py analyze     # reproduce 520/437/83, 1,708 issues, Table 3, R6, R8
```

Each check also runs standalone (e.g. `python3 code/analysis/rq2_taxonomy.py --check`). See
[`code/analysis/README.md`](code/analysis/README.md) for the script-to-number map and
[`data/README.md`](data/README.md) for the dataset schema. For a step-by-step walkthrough of all
six reproduction checks — offline numbers, static detection, the forged-credential sandbox test,
and real crawled skills — see [`REPRODUCE.md`](REPRODUCE.md).

## Scope of this release

The **reproducible core** of this artifact is the released **dataset** plus the **analysis suite**:
`python3 code/helper.py analyze` regenerates every reported dataset and taxonomy statistic
offline (no secrets, no Docker).

The **detection pipeline** implements the paper's methodology, with unit tests:
- **Phase 2** — keyword + NL-semantic filtering **and AST source→sink detection**
  (`code/phase2_static/ast_analyzer.py`, tree-sitter, Python/JS): for each credential reference it
  resolves the enclosing function and flags a flow into a network/log/file sink, per the paper's
  method. Tests: `test_ast_analyzer.py`, `test_scanner.py`.
- **Phase 3** — the **dual-condition (Benign/Adversarial) differential classification**
  (`code/phase3_dynamic/differential.py`, B≥2 / A≥1 over 3 rounds → profile → label). Test:
  `test_differential.py`.

Operational note: the **agent-driven dynamic validation** (`--dual`) drives a Claude Code agent
inside the Docker sandbox, so it requires **Docker + an `ANTHROPIC_API_KEY`**; the non-interactive
`--self-test` (forged-credential leak detection) needs Docker only, and the offline `analyze` path
needs neither. The released `data/` reproduces the paper's dataset, taxonomy, and
disclosure/popularity results.

## Project Structure

```
SkillLeakBench/
├── data/                          # Released, sanitized datasets (see data/README.md)
│   ├── skills_dataset.csv         # 520 affected cases (437 vulnerable + 83 malicious)
│   ├── issues.csv                 # 1,708 per-issue records (skill, pattern, severity)
│   ├── remediation_summary.csv    # disclosure outcomes (R6)
│   └── popularity_hardcoded_repos.csv  # name-free repo popularity (R8)
├── code/
│   ├── helper.py                  # CLI: doctor / init / analyze / build / run / status / clean
│   ├── analysis/                  # reproduction suite (verify, rq1/rq2, remediation, popularity, patterns)
│   ├── phase1_collection/         # Phase 1: SkillsMP crawler + extractor
│   ├── phase2_static/             # Phase 2: static filtering (scanner + AST source→sink + NL)
│   ├── phase3_dynamic/            # Phase 3: dynamic validation (Docker sandbox)
│   ├── scripts/                   # pipeline run scripts + lib.sh
│   ├── utils/                     # config_loader + path_helper
│   ├── results.sample/            # per-phase output formats (live runs write to code/results/, gitignored)
│   └── results/                   # live run artifacts (gitignored; created on run)
├── config.yaml                    # pipeline configuration
├── REPRODUCE.md                   # T1–T6 reproduction walkthrough
└── requirements.txt
```

## Disclaimer

__This repository contains examples of credential leakage and malicious agent skills for research purposes only.__

## Pipeline Overview

| Phase | Description | Output |
|-------|-------------|--------|
| 1. Dataset Collection | Crawl and download skills from SkillsMP | Source code + NL descriptions |
| 2. Static Filtering | Keyword matching + NL semantic analysis + AST-based sink detection | 3,156 candidate skills |
| 3. Dynamic Validation | Instrumented Docker sandbox + dual-condition (B/A) testing, mock credentials | flagged skills |
| 4. Manual Classification | Three reviewers cross-reference intent vs. behavior | 520 confirmed cases |

*(The end-to-end funnel counts — 3,156 candidates, 1,427 dynamically reviewed — require the full study corpus; the released code implements the methodology and reproduces the dataset analyses. See "Scope of this release".)*

Running the full pipeline requires credentials and Docker:

```bash
python3 code/helper.py init                     # create code/.env, then add SKILLSMP_API_KEY / GITHUB_TOKEN
python3 code/helper.py build                    # build the sandbox image (docker build -t skill-leakbench code/phase3_dynamic)
#   prefer not to build? pull the prebuilt image instead:
#   docker pull ghcr.io/agentskillsprivacy/skill-leakbench:latest
#   docker tag  ghcr.io/agentskillsprivacy/skill-leakbench:latest skill-leakbench
python3 code/helper.py run --skip 1             # run phases 2-4 (--skip 1 only skips re-crawling)

# Verify the Phase-3 sandbox detects a leak end-to-end (Docker only — no API key, no network):
bash code/scripts/03_dynamic_validate.sh --self-test   # -> leaked=true, channels=[stdout]
# (wraps code/phase3_dynamic/test_e2e_sandbox.sh; also runs under `pytest code/phase3_dynamic`)
```

> **Phase 2 input:** the scanner / NL / AST analyzers read *extracted skill directories* under
> `code/results/phase1_downloads/repos/` (one folder per skill) produced by Phase 1 — **not** the released
> `data/*.csv`. `--skip 1` only skips re-crawling; the downloaded repos must still be present. (The
> offline `analyze` path above reproduces the paper's numbers from `data/` alone, no repos needed.)

The dynamic phase runs a candidate in an isolated, instrumented container (network/filesystem monitoring
and honeypot credential files). All **leak-target** credentials are **mock** — the planted OpenAI/AWS/DB
keys a skill might exfiltrate are forged. It has three entry points (see
`code/scripts/03_dynamic_validate.sh`): `--self-test` (above — non-interactive, no key, demonstrates
leak detection on a forged third-party credential); `--dual CANDIDATES` (agent-driven Benign/Adversarial
differential via `run_dual.py`, needs a valid `ANTHROPIC_API_KEY`); and `--interactive CANDIDATES`
(human-in-the-loop menu via `executor.py`). See `code/phase3_dynamic/` and the Scope note above.

> **Threat model:** in `--dual` the Claude Code agent needs *real* Anthropic auth to operate, so that key
> (via `ANTHROPIC_API_KEY` or a mounted `CLAUDE_CREDENTIALS_FILE`) is the one real secret in the sandbox
> and an untrusted skill could read it — **use a low-value, scoped key**. The mock `ANTHROPIC_API_KEY` is
> never exported (so it can't shadow the agent's auth); the forged third-party keys are the leak targets;
> and `--self-test` needs no real key at all.

## Data

| Classification | Cases | Issues |
|---------------|-------|--------|
| Vulnerable | 437 | 1,371 |
| Malicious | 83 | 337 |
| **Total** | **520** | **1,708** |

`data/issues.csv` holds one row per security issue (skill, pattern, academic code, severity);
`data/skills_dataset.csv` aggregates them per case. Releases are de-identified (developer GitHub
usernames removed) and exclude live credential values. See [`data/README.md`](data/README.md).

The CSVs in `data/` are also published on Hugging Face at [`AgentSkillPrivacy/SkillLeakBench`](https://huggingface.co/datasets/AgentSkillPrivacy/SkillLeakBench) (loadable via the 🤗 `datasets` library).

## Ethics

This study uses the following disclosure and privacy safeguards:

1. **Research purpose only** — defensive security research on the agent-skill ecosystem.
2. **No live attacks** — the planted *leak-target* credentials are all mock (non-real); the only real secret is the agent's own API key, used solely in `--dual` (use a low-value, scoped key).
3. **Responsible disclosure** — all 520 affected skills were reported to SkillsMP; all 83 malicious skills were removed, and as of the May 2026 re-check 100 of 107 hardcoded-credential cases are no longer discoverable at their original locations.
4. **Aggregate reporting** — results are reported as aggregate patterns.
5. **Anonymization** — developer identities and live credential values are removed from the release.

## License

`SkillLeakBench` is licensed under the MIT License. See [LICENSE](LICENSE) for details.
