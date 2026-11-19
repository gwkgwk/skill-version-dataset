[返回仓库首页](../../../README.md)

# MalSkillBench：有真实版本更新的恶意收录 Skill

**找到 17 个不同 Skill、17 对可复核的旧新版本，保存 34 份完整原始目录。** 单版本恶意样本、人工生成的不同攻击变体、基准仓库内部清理与格式修复均不计为真实注册表版本更新。

这里的“恶意”依据为 MalSkillBench 对收录内容的标签。本次验证的是样本来源、原文、完整目录及真实版本变化；没有独立运行样本或确认攻击效果。

## 版本清单

| Skill | 本次恢复的更新 | MalSkillBench 收录版本 |
| --- | --- | --- |
| anctro/psyclaw-openclaw-health | 0.2.0 → 0.5.0 | 0.5.0 |
| aphobiacat/aibtc | 1.0.0 → 1.0.7 | 1.0.7 |
| assassin-1234/clawtrial | 1.0.8 → 1.0.9 | 1.0.9 |
| auliollc/botroast | 1.0.0 → 1.3.0 | 1.3.0 |
| bowen31337/alex-browser-use | 1.0.0 → 1.1.0 | 1.1.0 |
| ccclucky/source-cult-follower | 1.1.5 → 1.1.6 | 1.1.6 |
| chenghaifeng08-creator/self-evolve-automaton | 1.0.0 → 1.0.2 | 1.0.2 |
| dub88/lobsterhood | 1.1.0 → 1.1.1 | 1.1.1 |
| globalcaos/teams-hack | 1.0.0 → 1.0.1 | 1.0.1 |
| gstdcoin/gstd | 1.0.9 → 1.0.10 | 1.0.12 |
| happybigmtn/bonero-miner | 1.0.1 → 2.0.0 | 2.0.0 |
| happybigmtn/botcoin-miner | 1.0.2 → 3.0.0 | 3.0.0 |
| jacksoyou/polymarket-prob-analyzer | 1.0.1 → 2.4.0 | 2.4.0 |
| shenmeng/shenmeng-dex-arbitrage | 1.0.0 → 1.3.1 | 1.3.1 |
| yuan-xuan/the-origin-huan-ai-soul-thought-protocol | 3.0.5 → 3.0.9 | 3.0.9 |
| zaycv/x-twitter-trends | 1.0.0 → 1.0.1 | 1.0.1 |
| zkclaw/zkclaw | 1.0.0 → 1.0.1 | 1.0.1 |

其中 **gstdcoin/gstd** 特别处理：1.0.10 → 1.0.12 只改变注册表元数据，已经排除；改为恢复 1.0.9 → 1.0.10 的直接父子提交。1.0.10 的全部操作文件与恶意收录版 1.0.12 完全相同；此处恶意内容关联依据是整包文件哈希相同，而非声称作者单独评测过 1.0.10。

## 证据标准

1. 固定来源为 MalSkillBench 提交 `3548e2837adf58b96497f2c688f96beff26485da` 的 malware/ 路径。
2. 从清理前的固定提交 `4394ba51db3c4fd557c00ec68503acfad837b308` 恢复 681 份原始 `_meta.json`，逐文件校验 Git blob，得到 21 个多版本候选。
3. 使用元数据中的 owner、slug、发布版本和上游提交，在 friuns2/openclaw-removed-skills 归档中恢复。每对旧版严格取新版 Git 提交的第一父提交，元数据须显示两个不同版本。
4. 新版全部操作文件与 MalSkillBench 收录包逐文件 Git blob 相同。对照时只去掉注册表 `_meta.json` 并统一根主文档的 SKILL.md/skill.md 大小写，原始落盘字节不改。主文档相同但侧脚本不同的包不收录。
5. 两版目录完整、至少一份非注册表元数据文件改变，排除只增删元数据及仅修改版本号的情况。文件保存 Git SHA-1、SHA-256、模式、大小，目录树独立重建校验。

## 未计入的 4 个候选

- halfmoon82/openclaw-guardian-suite：主文档相同，但归档整包与 MalSkillBench 有 10 个文件差异，无法直接把恶意标签转移给归档版本。
- zaycv/clawhub：本次目标版本 1.0.8 → 1.0.10 的主文档属于已知受主机拦截的 blob，未重新获取；之前已有的 1.0.0 → 1.0.3 证据仍在原数据集中，不重复算作本批新增结果。
- zaycv/google-workspace：旧版主文档写入/读取返回 OSError，不能组成完整版本对；未绕过拦截。
- noypearl/get-weather：采集时已校验，但打包读取新版 index.js 返回 OSError，无法交付完整目录，排除正式计数；未重试或换路径恢复。

见 [unverified/index.json](unverified/index.json)，均单独保留。

## 仓库内部修改为何不算版本更新

全仓库有 41 次可达提交，malware 路径有 5 次相关提交。其中发布清理只删除了 1,537 个样本的生成/验证产物，并对 3 个样本统一了 skill.md 文件名；另外 3 个主文档只给 argument-hint 加引号。这些不是外部恶意 Skill 的新发布版本。

最新仓库没有 `_meta.json`，并不表示没有上游版本线索；本批依靠清理前历史元数据追溯。真实多版本来自注册表提交，不把原始模板与人工恶意变体当作公开版本升级。

## 数据入口

- [updates_index.csv](updates_index.csv) / [updates.jsonl](updates.jsonl)：17 对索引。
- pairs/MSBU-0001/ 等：old/、new/、SKILL.diff、package.diff、源元数据、Git 树、提交谱系和判断口径。
- [source/benchmark_path_proof.json](source/benchmark_path_proof.json)：固定基准提交到 malware 目录的树证据；每对 benchmark_tree.json 保留对应收录包的树。
- [source/registry_history_candidates.json](source/registry_history_candidates.json)：21 个元数据候选，未等同为 21 个已恢复更新。
- [verification_report.json](verification_report.json)：离线验证结果。

**这些更新不自动构成“良性 → 恶意”或“恶意行为首次引入”真值。** 旧版安全性和首次引入仍未知；恶意标签来自来源基准。原注册表 Git 仓库当前不可访问，恢复来自保留提交的归档，不能断言完整注册表全历史已覆盖。

校验：`python verify_dataset.py`。只读样本，不安装或执行。第三方内容保留原作者权利与各自许可。
