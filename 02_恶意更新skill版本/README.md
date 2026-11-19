# 恶意更新 Skill 版本

[返回仓库首页](../README.md)

已收录 **37 个 Skill、37 对真实更新、74 份旧／新版快照**。下面保留来源分组，版本类型明确区分。

| 类型 | 来源目录 | Skill / 更新对 | 完整快照 |
| --- | --- | ---: | ---: |
| 发布版本号更新 | [MalSkills](release_versions/01_MalSkills/) | 1 | 2 |
| 发布版本号更新 | [MalSkillBench](release_versions/02_MalSkillBench/) | 17 | 34 |
| 发布版本号更新 | [MaliciousSkillBench](release_versions/03_MaliciousSkillBench/) | 6 | 12 |
| Git 提交版本更新 | [MaliciousAgentSkillsBench](git_commit_versions/MaliciousAgentSkillsBench/) | 13 | 26 |

24 对具有注册表发布版本号；另 13 对使用 Git 提交标识，其中 1 对仅 README 变化。只有 MalSkills 的 1 对确认本次变化引入恶意分发指令；旧版整体良性与全局首次恶意版本仍未确认，其余采用来源恶意收录标签。

`supporting/` 只存放辅助材料，不计入上述数量：

- [MalSkills 来源调查](supporting/malskills-source-history/)：100 条单快照来源与调查记录。
- [MalSkills 早期历史候选](supporting/malskills-legacy-trace/)：200 条来源索引、42 个带历史 Skill、212 个候选版本对及部分恢复文件；含良性来源记录。
- [SkillLeakBench 追溯核查](supporting/skillleakbench-audit/)：83 条待追溯恶意案例，本次新增更新为 0；已收录的 6 对不重复计数。

各来源内部 `unverified/`、`candidates/` 和排除项保持原样。不能将支持材料中的单快照或候选数量与 37 对正式更新相加。
