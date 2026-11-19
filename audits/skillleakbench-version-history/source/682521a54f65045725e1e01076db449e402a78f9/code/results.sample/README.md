# Sample run — what the pipeline writes at each phase

A live run writes all intermediate artifacts under **`code/results/`**, which is **`.gitignore`d**
(runtime output; it holds downloaded third-party skill code and is regenerable, and the public
release removes developer identities). These small files show the **format** of each phase's
output so you can see the records without running — and without re-introducing developer
identities. Phase 1/2 values here are **anonymized**; the Phase 3 report is a real, mock-only run.

| File | Phase | Real run writes to |
|------|-------|--------------------|
| `01_phase1_skills_metadata.sample.json` | 1 — crawl | `code/results/phase1_downloads/skills_metadata.json` (+ `progress.json`, `zips/`, `repos/`) |
| `02_phase2_scan_result.sample.json` | 2 — static | `code/results/phase2_scan/<skill_id>_result.json` (regex `vulnerabilities`/`malicious_patterns` + `ast_flows`) |
| `02_phase2_candidates.sample.json` | 2 — static | `code/results/phase2_scan/candidates.json` (skills flagged by regex / AST flow / NL, with `reasons`) |
| `03_phase3_leak_report.sample.json` | 3 — dynamic | `<monitoring>/leak_report.json` (`leaked`, `channels`, `evidence`, `command_exit_status`) |

The scan-result sample mirrors a true positive: a hardcoded `sk-…` key (regex `VUL-001`) that also
flows into a network sink (`ast_flows`: `OPENAI_API_KEY → requests.post`). The leak report is the
actual output of `bash code/scripts/03_dynamic_validate.sh --self-test`: a skill exfiltrates the
sandbox-injected **forged** `OPENAI_API_KEY` to stdout and is detected (`leaked: true`).

## Regenerate a live run

```bash
# Phase 1 (needs SKILLSMP_API_KEY): writes code/results/phase1_downloads/
python3 code/phase1_collection/crawler.py  --config config.yaml all
python3 code/phase1_collection/extractor.py --config config.yaml
# Phase 2 (static): writes code/results/phase2_scan/ + code/results/phase2_nl/
bash code/scripts/02_static_filter.sh code/results/phase1_downloads/repos
# Phase 3 (dynamic self-test; Docker, no API key): writes a leak_report.json
bash code/scripts/03_dynamic_validate.sh --self-test
```

See the top-level `REPRODUCE.md` for the full T1–T6 walkthrough.
