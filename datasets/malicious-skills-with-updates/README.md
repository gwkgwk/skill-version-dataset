# 有版本更新的恶意 Skill

本目录只统计可对照旧版/新版的同一 skill；单版本恶意样本不计入更新数量。

**严格证据集目前是 1 个 skill、1 条确认的恶意分发指令更新。** 另有 2 个带历史版本的候选 skill，不能将候选数与确认数相加。

| Skill | 有版本更新的候选 | 本次确认结果 |
| --- | --- | --- |
| zaycv/clawhub | 7 个已记录版本 | 归档 1.0.0 → 1.0.3 新增安全事件中披露的恶意分发安装指令；确认 1 条 |
| zaycv/shield | 2 个已记录版本 | 1.0.0 → 1.0.1 的版本变化存在，但恶意行为变化尚未独立确认；仅候选 |

## 严格证据集

[confirmed_updates/MCU-0001/](confirmed_updates/MCU-0001/) 包含完整 old/new 目录、文件哈希、Git tree、主文档差异和判断依据。old 为新版提交的**直接第一父提交**，其注册表元数据为 1.0.0。

确认范围是归档 Git 路径历史中恶意分发指令的引入。旧版整体良性、完整注册表历史的最早恶意发布、实际感染均未确认，不能把它直接标注成已证实的“良性 → 恶意”真值。

## 候选与排除

- [candidates/skills.json](candidates/skills.json)：2 个候选、9 个不同版本的索引。
- [candidates/recorded_version_pairs.json](candidates/recorded_version_pairs.json)：7 组按已记录版本相邻配对的候选，其中 4 组在采集时两侧主文档可读；它们不全是连续发布，也不全是恶意行为更新。
- [excluded_single_version/index.json](excluded_single_version/index.json)：98 个没有取得两个不同版本的恶意收录样本，明确排除在更新数据集计数之外。

100 个恶意收录样本及其调查材料只作为[来源档案](../malskills-malicious-introductions/README.md)，不能宣称为 100 个恶意更新 skill。原始恶意标签只针对 MalSkills 收录快照；历史版本标签保持未知。来源无法验证的记录仍在原档案 unverified/ 中独立保留。

离线校验：`python verify_dataset.py`。第三方 skill 原文保留原作者权利与原有许可。
