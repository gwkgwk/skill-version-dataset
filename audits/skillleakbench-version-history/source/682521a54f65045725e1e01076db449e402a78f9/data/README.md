---
license: mit
---

# SkillLeakBench Dataset

Credential leakage dataset for LLM agent skills (ASE 2026).

## Files

| File | Rows | Description |
|------|------|-------------|
| `skills_dataset.csv` | 520 | Confirmed leakage cases (437 vulnerable + 83 malicious), one row per case |
| `issues.csv` | 1,708 | One row per security issue: skill, pattern, academic code, severity |
| `remediation_summary.csv` | 3 | Disclosure outcomes per class (malicious 83/83; vulnerable 437/374/63; hardcoded 107/100/7) |
| `popularity_hardcoded_repos.csv` | 37 | Name-free popularity of hardcoded-credential repos (repo_status, stars, forks) |

`issues.csv` is the per-issue master; `skills_dataset.csv` is its per-skill aggregate (the analysis
suite reads both). `remediation_summary.csv` (R6) and `popularity_hardcoded_repos.csv` (R8) hold
different, non-joinable supplementary data, so they are kept as separate small tables.

## Columns (`skills_dataset.csv`)

| Column | Description |
|--------|-------------|
| `source` | Data source (`skillsmp`) |
| `skill_name` | Skill identifier (GitHub usernames removed) |
| `classification` | `malicious` or `vulnerable` |
| `patterns` | Semicolon-separated pattern names |
| `issue_count` | Number of security issues |
| `severity` | CRITICAL, HIGH, MEDIUM, or LOW |

`issues.csv` columns: `skill_id`, `skill_name`, `classification`, `pattern_id`, `academic_code`,
`pattern`, `severity` (one row per issue).

## Distribution

| Classification | Count | % |
|---------------|-------|---|
| Vulnerable | 437 | 84% |
| Malicious | 83 | 16% |

## Leakage Patterns

**Vulnerability (4)**: Information Exposure, Hardcoded Credentials, Insecure Storage, Artifact Leakage

**Malicious (6)**: Remote Exploitation, Defense Evasion, Credential Compromise, Data Exfiltration, Resource Hijacking, Persistence

## Usage

```python
import pandas as pd
df = pd.read_csv('skills_dataset.csv')
malicious = df[df['classification'] == 'malicious']
vulnerable = df[df['classification'] == 'vulnerable']
```

## Citation

```bibtex
@inproceedings{skillleakbench2026,
  title={How Your Credentials Are Leaked by {LLM} Agent Skills: An Empirical Study},
  author={Chen, Zhihao and Zhang, Ying and Liu, Yi and Deng, Gelei and Li, Yuekang and Zhang, Yanjun and Ning, Jianting and Zhang, Leo and Ma, Lei and Li, Zhiqiang},
  booktitle={Proceedings of the 41st IEEE/ACM International Conference on Automated Software Engineering (ASE)},
  year={2026}
}
```
