# SkillLeakBench 原仓库版本追溯核查

本次新增 **0 对恶意 Skill 版本更新**。此前通过 MaliciousSkillBench SRC004 来源整理的 6 对仍保留，未再次计数。全局统计保持：发布版本号更新 24 个 Skill、Git 提交版本更新 13 个 Skill，两类合计 37 个。

## 核查范围

- 原仓库 [AgentSkillsPrivacy/SkillLeakBench](https://github.com/AgentSkillsPrivacy/SkillLeakBench/tree/682521a54f65045725e1e01076db449e402a78f9) 固定提交 `682521a54f65045725e1e01076db449e402a78f9`，检查 main 的 9 个可达提交，以及 v1、v1.0、v1.1、v1.2 共 4 个发布标签，涉及 6 个不同提交树。
- 初始提交 `c5394845fbe336e8fded41b58375ecf37a9a387c` 及各发布树的数据文件；当前 issues.csv、skills_dataset.csv、数据说明和示例来源文件。
- [官方 Zenodo 归档](https://zenodo.org/records/19367969)：核验其 v1.2 压缩包校验值和 75 个成员文件清单，仅按数据读取。
- [官方 Hugging Face 镜像](https://huggingface.co/datasets/AgentSkillPrivacy/SkillLeakBench)：检查 3 次镜像提交的公开元数据、当前文件树，并核对固定提交 `8264436a0483e2fc1aed84b80e5fde73ea52c3ca` 的两份主 CSV 与 GitHub 逐字节一致。

## 为什么没有新增版本对

公开表有 520 条受影响记录，其中 83 条 malicious、437 条 vulnerable。83 条恶意记录对应 83 个本地 issue case ID、80 种显示名称，重复名称不能仅凭名字合并或断言为不同真实 Skill。漏洞记录不能当作恶意样本。

各 Git 提交树和 Zenodo 归档均没有原始 SKILL.md 或 Skill 历史包。公开表没有 Git 仓库地址、提交 SHA、发布版本号或原始 Skill 内容哈希。7 个名称含 owner/slug，是身份线索，但不足以把恶意标签绑定到任意历史版本。

最早公开 CSV 也不包含这些版本证据。初始／当前 83 条恶意记录经显式显示名称规范化（7 个 owner/slug 补充及 3 个 -002 后缀调整）和模式列表排序后，记录多重集合完全一致。这里是标注显示方式变化，不是 83 个 Skill 的版本更新。

`code/results.sample/01_phase1_skills_metadata.sample.json` 使用 example-org/sample-skill 和 <redacted> 等占位值，只是结果格式示例，不能当作真实恶意来源。v1–v1.2 是研究代码／数据发布版本，不是各恶意 Skill 的版本号。

## 已有的 6 对相关结果：不重复增加

| Skill | 已恢复发布版本对 |
|---|---|
| abdullah4ai/openclaw-watchdog | 1.0.5 → 1.1.2 |
| c-goro/skillguard | 0.2.2 → 1.0.1 |
| cgnl/nano-banana-antigravity | 1.0.0 → 1.1.0 |
| orlyjamie/wed | 1.0.2 → 1.0.3 |
| seyhunak/deep-research | 1.0.0 → 1.0.1 |
| zadahmed/nervepay | 1.0.0 → 1.2.0 |

原文件与版本证据见 [已有数据集](../../datasets/maliciousskillbench-real-updates/README.md)；索引副本见 [existing_updates_reference.json](existing_updates_reference.json)。其恶意版本标签依据是之前核验的汇总基准 SRC004 完整包对应关系，本次匿名原始 CSV 没有提供新的逐案例版本绑定证据，不将其改称为新增确认。

## 证据和未验证记录

- [summary.json](summary.json)、[verification_report.json](verification_report.json)：统计和离线核验结果。
- [unverified/malicious_cases_index.csv](unverified/malicious_cases_index.csv)：83 个本地恶意案例的待追溯索引；JSON 保留缺失证据及状态。
- source/：6 个固定提交的原始 CSV、Git 提交和目录树，以及当前公开说明。
- evidence/：发布标签、元数据变化、镜像相等性和归档核查材料；mirrors/：官方归档元数据及原始 ZIP。

没有凭同名或作者名把其他 GitHub 仓库强行认作原始样本；未安装或运行任何 Skill、上游采集器或检测程序。无法验证的记录保留，等待能够绑定到原始字节／固定版本的额外证据。

校验：`python verify_audit.py`。第三方原始内容保留其许可及作者权利。
