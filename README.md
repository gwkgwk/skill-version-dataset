# Skill Version Dataset

本仓库将不同来源的数据分开存放，安全标签按各数据集的证据保留。

| 数据集 | 位置 | 范围与安全标签 |
| --- | --- | --- |
| GitSkills 真实更新 | [datasets/gitskills-real-updates-500/](datasets/gitskills-real-updates-500/) | 500 个 skill、500 个仓库、500 条真实更新、1,000 份完整目录快照；安全标签全部未标注，不作为良性真值 |
| 有版本更新的恶意 Skill | [datasets/malicious-skills-with-updates/](datasets/malicious-skills-with-updates/) | 严格证据：1 个 skill、1 条恶意分发指令更新；另列 2 个多版本候选，98 个单版本样本排除 |
| MalSkillBench 恶意收录 Skill 真实更新 | [datasets/malskillbench-malicious-updates/](datasets/malskillbench-malicious-updates/) | 17 个不同 Skill、17 对实际内容更新、34 份完整快照；新版整包与恶意收录包一致。4 个未验证候选单列，旧版安全性及恶意行为首次引入未知 |
| MaliciousSkillBench 真实更新（另审查 SkillLifeBench） | [datasets/maliciousskillbench-real-updates/](datasets/maliciousskillbench-real-updates/) | 新增 6 个恶意收录 Skill、6 对实际内容更新、12 份完整快照；26 条未验证记录单列。SkillLifeBench 的 2 个原生更新为安全修复，未计入恶意更新 |
| MaliciousAgentSkillsBench Git 提交版本更新 | [datasets/maliciousagentskillsbench-git-updates/](datasets/maliciousagentskillsbench-git-updates/) | 新增 13 个恶意收录 Skill、13 对 Git 提交更新、26 份完整快照；其中 1 对仅 README 变化。与发布版本号更新分开，144 条未计入记录单列 |
| MalSkills 来源档案（不计作更新集） | [datasets/malskills-malicious-introductions/](datasets/malskills-malicious-introductions/) | 100 个恶意单快照的来源与调查材料；不等于 100 个恶意更新 skill。无法验证的情况单独保留 |
| MalSkills 历史追溯 | 本仓库根目录的原有数据，说明见下文 | 包含原始 benign / malicious 快照标签和历史候选对；历史版本及更新对没有独立安全真值 |

GitSkills 与 MalSkills 原始文件分开存放，未将 GitSkills 数据混入恶意样本集。

按**注册表发布版本号更新**统计，去重后为 **24 个 Skill、24 对更新、48 份旧／新版快照**：MalSkills 1 个 + MalSkillBench 17 个 + MaliciousSkillBench 6 个。另有 MaliciousAgentSkillsBench 新增的 **13 个 Skill、13 对 Git 提交版本更新、26 份快照**，不把 Git SHA 误称为发布版本号。两类一起统计共 **37 个 Skill、37 对更新、74 份快照**，其中本批 1 对只修改 README。74 份快照不等于 74 个恶意版本，旧版安全性未全部确认；已确认更新引入恶意分发指令仍为 1 对，其余采用来源恶意收录标签，尚未确认首次引入。

[GitSkills 安全初审报告](audits/gitskills-real-updates-500/README.md)：500 条全量规则初筛，44 条助手上下文复核；安全标签仍全部未知，不能直接作为良性真值。

GitSkills 入口：[采集说明](datasets/gitskills-real-updates-500/README.md)、[500 条索引](datasets/gitskills-real-updates-500/updates_index.csv)、[下载 ZIP](datasets/gitskills-real-updates-500/gitskills-real-updates-500.zip)、[校验报告](datasets/gitskills-real-updates-500/verification_report.json)。

## MalSkills 历史版本追溯

2026-11-18 整理。来源固定为 [security-pride/MalSkills](https://github.com/security-pride/MalSkills/tree/46d60f09cef00fd3a9c01272be63dbd273ab4444/data/ground_truth)，
历史文件通过保留原提交的 [friuns2/openclaw-removed-skills](https://github.com/friuns2/openclaw-removed-skills) 恢复。

本仓库收录版本索引、候选更新对和部分已恢复的原始文件。**212 组记录不等于 212 组已下载或已标注的更新样本。**

| 范围 | Skill 数 | 旧版本记录 / 候选版本对 |
| --- | ---: | ---: |
| 收录版本被标为 benign 且保留历史 | 40 | 205 |
| 收录版本被标为 malicious 且保留历史 | 2 | 7 |
| 合计 | 42 | 212 |

正式 MalSkills 清单有 200 个单版本样本（100 benign / 100 malicious），本仓库保留其全部版本索引。
source/all_697_metadata_records.json 还保留上游所有 697 份样本元数据；697 不是正式评测集大小。

## 已恢复范围

- 对 5 个 skill 的 15 个版本记录进行了文件恢复，15 份元数据版本号均核对一致。
- 保存 12 份可读取的 SKILL.md 和 15 份 _meta.json，共 27 份原始文件。
- 保存 7 组主文档差异，见 [diff_summary.json](diff_summary.json)。
- 6 个恶意候选版本的目录经上游清单核对，目录全部文件均恢复；3 个良性 skill 仅恢复主文档与元数据，随附脚本等文件尚未收录。
- zaycv/clawhub 的 1.0.7、1.0.8、1.0.10 主文档被本机防护拦截，未包含在上传包中；其来源链接和缺失状态保留。

| Skill | 核查版本 |
| --- | --- |
| zaycv/shield | 1.0.0、1.0.1 |
| zaycv/clawhub | 1.0.0、1.0.3、1.0.4、1.0.6、1.0.7、1.0.8、1.0.10 |
| byungkyu/api-gateway | 1.0.54、1.0.58 |
| autogame-17/evolver | 1.29.9、1.32.2 |
| pskoett/self-improving-agent | 3.0.2、3.0.5 |

## 文件入口

- [版本追溯清单](版本追溯清单.md)：42 个带历史 skill 的完整列表与来源。
- [candidate_update_pairs_212.json](candidate_update_pairs_212.json)：每对的旧新版本、发布时刻、原提交与恢复链接。
- [final_200_version_index.json](final_200_version_index.json)：正式 200 个样本的版本线索。
- [recovery_results.json](recovery_results.json)：实际恢复状态、版本核对和 SHA-256。
- [audit_summary.json](audit_summary.json)：统计口径和覆盖范围。
- recovered/：已验证可读取的原始文件；diffs/：主文档差异；source/：原始 CSV 与元数据。
- [MANIFEST.sha256](MANIFEST.sha256)：上传文件的 SHA-256 清单。

## 标签与评测边界

CSV 标签针对 MalSkills 收录的快照。历史版本没有独立真值，更新对也没有真值；候选对的 update_security_label 保持 null。
只有核查旧版正常、新版恶意以及本次变化的因果证据后，才能作为“正常 → 恶意”更新样本。

版本对按已记录的发布时间排序后相邻配对，可能缺少中间发布版本，不能视为完整连续发布历史。
最新版本仅指 MalSkills 收录时的快照，不表示当前注册表最新版。
evolver、self-improving-agent 的所选两版 SKILL.md 相同；这不能证明整包没有变更。

这些文件含恶意指令或代码研究样本，应作为不可信数据静态查看；收录不代表推荐安装。整理过程未执行任何样本。

## 校验

在仓库根目录运行：

```bash
python verify_dataset.py
```

校验脚本仅检查文件哈希、统计和恢复状态，不执行样本。

## 来源与权利

MalSkills 分析器的 Apache-2.0 许可证不自动适用于第三方 skill 样本。
样本仍适用原作者的权利与许可；本仓库保留原始 CSV、owner/slug、版本、发布时间、提交和恢复来源，不重新授予第三方内容许可证。
上游说明见 [source/ground_truth_README.md](source/ground_truth_README.md)。
