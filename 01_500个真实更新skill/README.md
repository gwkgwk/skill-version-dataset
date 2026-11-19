[返回仓库首页](../README.md)

# GitSkills：500 条真实 skill 更新

采集日期：2026-11-18（北京时间）。

从 [GitSkills](https://arxiv.org/abs/2608.10906) 官方样本库选取 skill 身份，再从 GitHub 官方 Git API 恢复真实提交前后的文件。
本数据集包含 **500 条更新、500 个不同 skill、500 个实际仓库、1,000 份完整 skill 目录快照**。
所有条目均具有真实提交谱系和原始内容变化，未构造或反向删除恶意段落来制造前身。

## 采集结果

| 指标 | 数量 |
| --- | ---: |
| 真实 Git 提交更新对 | 500 |
| 不同 skill（实际仓库＋路径） | 500 |
| 实际 GitHub 仓库 | 500 |
| 完整旧新 skill 目录 | 1,000 |
| 已校验原始文件 | 2604 |
| 带随附脚本、引用或其他文件的更新 | 171 |
| 已独立重算并匹配的 Git 目录树哈希 | 1,000 |
| 新版 SKILL.md 与 GitSkills 收录 blob 一致 | 447 |

更新提交时间范围（UTC）：2025-11-20T22:40:26Z 至 2026-07-23T02:09:47Z。

## 每条数据包含什么

```text
updates/GSU-0001/
  old/                  # 旧提交下的完整 skill 目录
  new/                  # 新提交下的完整 skill 目录
  metadata.json         # 仓库、路径、旧新提交、日期、来源、变化统计
  lineage.json          # 新提交与第一父提交的谱系证据
  files.json            # 两版文件列表、模式、大小、Git SHA-1、SHA-256
  old_tree.json         # GitHub 原始目录树清单
  new_tree.json
  SKILL.diff            # 标准 Git 文本差异，含文件末尾换行标记
```

入口：[updates.jsonl](updates.jsonl)、[updates_index.csv](updates_index.csv)、[summary.json](summary.json)、[verification_report.json](verification_report.json)。

## “真实更新”的口径

- 新版为仓库中确实存在的一次 Git 提交，旧版严格取该提交的第一父提交。
- 两版在相同路径下都存在带 name/description 元数据的 SKILL.md，正文至少 100 字符。
- 两版 SKILL.md 的原始内容不同，排除仅有空白或行尾变化的情况。
- 每个 skill 只收录一条更新，对旧新内容对去重；每个 GitSkills 仓库标识最多两条。
- 恢复 skill 根目录下的全部 Git 跟踪文件，逐文件核对 Git blob SHA-1 与 SHA-256，并独立重建整个 Git tree 哈希。
- 标签保持未知：old_security_label、new_security_label、update_security_label 均为 null。

**Git 提交更新不等于语义版本发布，也不等于恶意更新。** 这 500 条数据尚未人工标注正常或恶意。

## 来源与筛选

官方样本仓库：[giuseppedestefanis/gitskills-sample](https://github.com/giuseppedestefanis/gitskills-sample)，固定提交 `fff3df93beeee51a5444450891751f143e38da3e`。
原始 ZIP 为 86,721,947 字节，Git blob SHA-1 为 `b2c5b19033285d2361a20df94d36e3eb922b6a1a`，已核对。
样本 SQLite 含 29,786 份文件记录，属于 GitSkills 全量数据的公开子样本。

候选必须是内容去重代表、规范 SKILL.md、有效元数据、已抓取历史、至少两次提交，位置为 canonical 或 skills-dir。
按固定种子对候选仓库轮转排序，异步抓取，收录首先完成且满足条件的 500 条，因此不声称是全生态随机代表样本。
历史查询截止到各条 GitSkills 记录的 discovery/history 最晚时刻加一秒；每条 metadata.json 保存实际查询 URL 和截止时间。

GitSkills 的内容抓取与历史补全可能发生在不同时间，因此部分恢复新版与其收录 blob 不同；它们仍是同一 GitSkills skill 身份的真实历史更新。
`gitskills_snapshot_matches_new_primary` 明确标记这一差异。

## 覆盖限制

- 只覆盖触及 SKILL.md 的提交，不覆盖“仅修改脚本而未修改 SKILL.md”的更新。
- 完整目录是 skill 目录内部的 Git 跟踪文件；不包含目录外引用、外部依赖、Git LFS 实体或运行环境。
- 两版任一目录超过 60 个文件或 2 MB、包含符号链接/子模块、存在本机不支持的文件名，均不收录。
- 文件创建、删除、改名导致没有同路径旧版，或仓库/历史不可访问时，保留排除记录，不重建前身。
- 全部样本作为不可信静态数据读取；未安装或执行任何 skill、脚本或上游仓库代码。

## 离线校验

```bash
python verify_dataset.py
```

校验内容包括 500 个唯一 skill、父子提交关系、全部原始文件哈希、1,000 个 Git tree 哈希和 MANIFEST.sha256。
工作目录保留原始 SQLite 时，还会核对 500 条来源在 GitSkills 表中确实存在；分发包通过 selected_seeds.json 和固定上游版本保留追溯线索。

## 权利与引用

GitSkills 的汇编元数据为 CC-BY-4.0；skill 原文与随附文件继续遵守来源仓库各自许可，不能统一重新授权。
每条 seed 保存 origin_license，原始文件字节不变。详细数据来源见 source/provenance.json 和 source/GitSkills_sample_README.md。
引用：Destefanis, Graziotin, Vaccargiu, Ortu. GitSkills: A Dataset of Agent Skills on GitHub. arXiv:2608.10906 / MSR 2027 Mining Challenge.
