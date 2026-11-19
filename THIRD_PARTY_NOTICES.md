# 第三方来源与归属

本仓库为多来源研究数据的整理集合。以下公开数据集提供种子、标签、来源线索或原始内容；当前仓库中的更新配对和克隆筛选由后续追溯与核验产生，不是全部由上游直接发布。

| 上游来源 | 在本项目中的用途 |
| --- | --- |
| [GitSkills 官方样本库](https://github.com/giuseppedestefanis/gitskills-sample)、[完整数据页面](https://huggingface.co/datasets/mvaccargiu/gitskills) | 500 对真实更新的身份种子；内容从对应原始 Git 仓库恢复 |
| [MalSkills](https://github.com/security-pride/MalSkills) | 恶意单快照标签与来源种子；正式更新中收录 1 对恶意分发指令引入 |
| [MalSkillBench](https://github.com/lxyeternal/MalSkillBench) | 17 对发布版本更新的恶意来源包与比对依据 |
| [MaliciousSkillBench](https://github.com/protectskills/MaliciousSkillBench) | SRC004 / SkillLeakBench 来源分组中恢复 6 对发布版本更新 |
| [MaliciousAgentSkillsBench](https://github.com/protectskills/MaliciousAgentSkillsBench) | 13 对 Git 提交版本更新的恶意来源标签与原始仓库线索 |
| [SkillReuse](https://github.com/zly123987/skill-reuse)、[Zenodo 语料](https://zenodo.org/records/19245910) | 恶意安装指令文档快照及公开克隆图；本项目核验 20 对全文相同克隆 |
| [SkillLeakBench 原仓库](https://github.com/AgentSkillsPrivacy/SkillLeakBench) | 83 条恶意案例的版本来源核查；原仓库直接追溯新增 0 对 |
| [SkillLifeBench](https://github.com/Tasselszcx/SkillLifeBench) | 演化数据核查与排除说明，未计入新增恶意更新 |
| [openclaw-removed-skills 归档](https://github.com/friuns2/openclaw-removed-skills) | 部分下架 Skill 的原提交和历史文件恢复来源 |

每条记录保留的原始仓库、路径、提交、哈希和上游身份是更细粒度的归属依据。GitHub 页面中的仓库所有者或 scopedName 不自动等同于 Skill 的原始发布者，分析时需结合具体源路径。

[Snyk 调查](https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/)及 [Antiy CERT ClawHavoc 报告](https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/)等用于安全事件交叉核对，事件报告本身不提供所有历史版本的安全标签。

各第三方内容保留原有归属、许可证与权利。SkillReuse 的 Zenodo 记录标注 CC BY 4.0；这不改变其中其他原作者可能持有的权利。本项目 [LICENSE.md](LICENSE.md) 仅对本项目有权许可的原创贡献授予许可。

使用本集合时，请引用本项目，并根据所用子集引用相应上游论文或数据集。原始 README、固定提交信息和校验回执保留在各目录的来源或证据文件中。
