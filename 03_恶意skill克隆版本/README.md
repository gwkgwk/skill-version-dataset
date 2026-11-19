[返回仓库首页](../README.md)

# SkillReuse 恶意内容克隆：独立核验集合

整理日期：2026-11-19。来源论文：*Latent Reuse in Agent Skills: Multi-modal Clone Detection at Ecosystem Scale*。

本目录单独收录该论文公开语料中能够静态核验的恶意安装指令快照及其克隆，不与良性更新集混放，不计入已确认版本更新数量。

## 本次结果

| 范围 | 数量 | 证据口径 |
| --- | ---: | --- |
| 官方原始语料 | 155,547 行 | Zenodo 原文件 1,460,271,174 字节，官方 MD5 核对通过 |
| 恶意安装指令快照 | 62 份 | 不同语料记录，包含 42 个不同 SKILL.md 内容 SHA-256、21 个 scopedName |
| 全文相同的恶意克隆 | 20 对 / 20 组 / 40 份快照 | 不同源路径之间的原始 SKILL.md 字节 SHA-256 完全相同；均为同一发布者的不同 slug，不能称为跨作者传播 |
| 安全工具测试夹具 | 1 份 | invariantlabs-ai/mcp-scan 的 tests/skills/malicious-skill/SKILL.md，单独保留，不视为真实投毒发布 |
| 安全文档排除项 | 1 份 | skillvet 中引用 IOC 的安全说明，未判恶意 |
| 公开关系图候选 | 632 条 | 按上述恶意载荷相关 scopedName 匹配，只作核查线索；含安全测试夹具的关联 |
| 主机阻止项 | 3 行 | 1 份提取记录被阻止；另 2 行命中此前已被阻止的内容哈希，均不收录内容、不绕过读取 |
| 本次新增真实版本更新 | 0 对 | 没有确认旧版→新版或恶意首次引入；既有 37 个更新 Skill 总量不变 |

“62 份”不是 62 个独立 Skill，也不是 62 个不同恶意版本。快照用 `sha256:<内容哈希>` 标识，属于内容身份，不是注册表发布版本号或 Git 提交版本。部分文档声明 `version: 1.0.0`，仅作为未验证声明保留，不当作真实发布证据。

## 恶意判断与克隆证据

只在数据中进行 base64 静态解码，没有执行解码结果，也没有访问恶意下载地址。62 份快照的编码安装指令均包含从 ClawHavoc 已知基础设施 `91[.]92[.]242[.]30` 获取内容并交给 shell 执行的行为。该基础设施与 AMOS 的关联由 [Antiy CERT 事件报告](https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/) 支持。我们确认的是文档包含恶意分发指令，未下载或动态验证远端二进制。

20 对克隆使用原始内容 SHA-256 判定全文完全相同，源仓库路径不同。这能证明静态内容克隆，不能证明传播方向、发布时间或版本演变。安全夹具虽包含同类恶意安装指令，但用途与真实投毒发布不同，因此独立存放。

## 与论文 22 个样本、3 条关系的区别

[论文第 4.7 节](https://arxiv.org/html/2603.22447v2#S4.SS7) 报告 22 个恶意 Skill、3 条保留恶意载荷的克隆关系。公开语料中多个不同路径、不同哈希的记录共用同一个 scopedName；公开 Parquet 关系图仅提供 `skill_a, skill_b, fused, cross_author`，没有语料行号、内容哈希、源路径或版本。

本次找到 22 个载荷相关 scopedName（其中一个属于安全测试夹具），不能据此认定复现了论文的 22 个样本清单。原图仅有 2 条边的两端名称都匹配到了含恶意安装指令的记录；由于名称歧义，这 2 条也未升级为已确认保留载荷的具体快照对。论文报告的 3 条关系尚未独立复现，见 `unverified/paper_counts_not_reproduced.json`。

632 条候选关联不能直接标为恶意；同名匹配和高克隆分数都不能证明恶意载荷存在。确认集合使用可复核的全文相同证据，另行保存图中候选及其 876 条来源记录元数据。

## 文件入口

- [malicious_snapshots_index.csv](malicious_snapshots_index.csv)：62 份恶意安装指令快照索引。
- [malicious_snapshots_index.json](malicious_snapshots_index.json)：来源、原始哈希、语料行号、静态行为证据和版本证据状态。
- [confirmed_exact_content_clone_pairs.json](confirmed_exact_content_clone_pairs.json)：20 对已核验全文相同克隆。
- [confirmed_exact_content_clone_groups.json](confirmed_exact_content_clone_groups.json)：20 个克隆组。
- `malicious_payload_snapshots/`：每份记录和去除长编码字符串、禁用 URL 后的 SKILL 文本。
- `security_test_fixtures/`：1 份安全测试夹具。
- `excluded_security_documentation/`：1 份排除的安全说明。
- [published_graph_candidate_edges.json](published_graph_candidate_edges.json)：632 条图中候选，安全标签均为未知。
- `unverified/`：同名映射、论文统计差异、主机阻止项，均单独保留。
- `evidence/`：官方语料校验回执、Zenodo 元数据、固定 Git 提交信息和原始公开关系图。

上传内容为移除所有长度至少 24 字符的 base64 字符集字符串、禁用 URL 的研究副本，不能当作原始字节快照使用；原始文件哈希对应 Zenodo 语料中的原始文本。未上传 1.46 GB 全量语料、可执行的恶意安装命令或远端载荷。每份内容仍保留原始来源归属。

## 来源与许可

- [官方代码及关系图](https://github.com/zly123987/skill-reuse/tree/0125acaaac79ef3fd5ab3146549de5c2b84b6785)，固定提交 `0125acaaac79ef3fd5ab3146549de5c2b84b6785`。
- [Zenodo 官方语料](https://zenodo.org/records/19245910)，文件 `skills_with_content.jsonl`，官方 MD5 `fb4a146f93f9dd0439a7f7b2cc40807b`，本次 SHA-256 `8df8666e45391d13fe42f075865d338a0478eb183a9e4bebc782f5cde7cd4b72`。
- 论文：Jiaying Zhu, Lyuye Zhang, Wenbo Guo, Yang Liu. ASE 2026. DOI [10.1145/3832783.3837468](https://doi.org/10.1145/3832783.3837468)。
- Zenodo 记录标注 CC BY 4.0；第三方 Skill 原有许可和归属仍需保留，本目录不另行授予第三方代码许可。研究副本的移除与禁用处理已明确标注。

## 校验

本目录运行 `python -S verify_dataset.py` 可核对上传文件哈希、克隆组、原图 Git blob 和计数。安装 pyarrow 后，`verify_graph.py` 还能重新从原始 Parquet 过滤并核对 632 条候选边。

如已有官方原始语料，可运行 `python -S verify_dataset.py --corpus <skills_with_content.jsonl路径>`，重新核对官方全文件校验值及 63 份载荷记录（62 份主集合 + 1 份测试夹具）的逐行来源绑定；不会执行任何样本。离线元数据校验本身不能替代外部原始语料验证。
