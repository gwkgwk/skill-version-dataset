# MaliciousAgentSkillsBench：恶意收录 Skill 的真实 Git 版本更新

本批确认 **13 个不同 Skill、13 对 Git 提交版本、26 份完整目录快照**。不是 13 对注册表发布版本号更新；这些文件以不可变 Git 提交 SHA 标识版本。此前 24 个发布版本号更新 Skill 保持独立，本批不改变该口径。若同时纳入 Git 提交版本更新，合计 37 个 Skill。

| 仓库 / Skill | 旧提交 → 新提交 | 变化范围 |
|---|---|---|
| ArjenSchwarz/agentic-coding / project-init | `2d319c3e` → `415356a0` | instruction_code_or_reference_change |
| Interstellar-code/claud-skills / lark-agent-simple | `9cb2d6ba` → `b0e68a46` | README_only |
| LupoGrigi0/Human-Adjacent-Coordination / hacs | `4224e9e7` → `a87c2b07` | instruction_code_or_reference_change |
| Porkbutts/jetaasc-events / jetaasc-newsletter | `04d6af82` → `fcf7849e` | instruction_code_or_reference_change |
| andr81/pers-assist / weekly-plan | `b1ac047e` → `d69e622a` | instruction_code_or_reference_change |
| civitai/civitai / browser-automation | `ebb4376a` → `8c838263` | instruction_code_or_reference_change |
| frcusaca/foolish / ccw-maven-setup | `d22a8e9d` → `132c2aae` | instruction_code_or_reference_change |
| plurigrid/asi / load-skills | `d0e2f36e` → `9841ff44` | instruction_code_or_reference_change |
| romiluz13/cc10x / cc10x-router | `8474b911` → `f80a01db` | instruction_code_or_reference_change |
| ruvnet/RuVector / flow-nexus-platform | `d191be4a` → `5ae30183` | instruction_code_or_reference_change |
| schmug/karkinos / worker | `0221194c` → `1beaebc2` | instruction_code_or_reference_change |
| sfc-gh-dflippo/snowflake-dbt-demo / doc-scraper | `7685f42f` → `1683199c` | instruction_code_or_reference_change |
| syeda-hoorain-ali/physical-ai / image-generator | `0bddbaa3` → `9c254dbc` | instruction_code_or_reference_change |

其中 1 对仅修改 README，其余 12 对涉及 SKILL.md、脚本、模板或引用资源。**不把每一对都称为恶意载荷更新。** 恶意标签沿用来源基准，旧版和更新对安全标签未知，本批确认的恶意行为首次引入为 0。

## 来源和方法

1. 固定原始仓库 [MaliciousAgentSkillsBench](https://github.com/protectskills/MaliciousAgentSkillsBench/tree/f7d28b1a9de4eb33d552529cf79d1065d765f6c3)，检查 39 个可达提交。当前恶意 CSV 为 157 条，来自 69 个平台仓库别名；这些不是 157 个多版本样本。
2. 当前下载地址已隐藏；从最早公开提交 [eb431f4f](https://github.com/protectskills/MaliciousAgentSkillsBench/tree/eb431f4f9d855f558fce20fd7de098a0423b6160) 的 data/skills_dataset.csv 恢复来源。157 条记录对应 68 个实际 GitHub 仓库，40 个目前可访问。只使用公开历史，不运行上游工具、Skill 或安装脚本。
3. 与已公开的 MaliciousSkillBench SRC002 保留归档逐文件对应。对当前路径及已删除的历史路径检查 Git 历史，找到整个操作包与恶意收录快照完全相同的提交，旧版严格取其第一父提交。两版都有 SKILL.md，且存在真实内容变化。
4. 保存全部原始文件、Git SHA-1、SHA-256、大小、模式、完整目录树及从 Git 提交根树到 Skill 目录的路径证明。比对时仅排除注册表元数据、.DS_Store 和 Python 缓存，并统一根主文档大小写，落盘原始字节不改。
5. 13 个新版主文档 SHA-256 均同时对应汇总基准中的恶意文本身份。其中 project-init 是跨来源重复，汇总基准主来源为 SRC001，仍保留 SRC002 来源关联；未将它重复计入此前 24 个版本更新 Skill。

原始历史生态 CSV 的初始 120,711 条与当前 98,380 条是数据集整理范围变化；恶意身份始终 157 条。恶意 CSV 的历史变化主要补充／细化 Pattern、Severity 等标注，不能算 Skill 发布更新。v0.1–v0.8 是研究代码仓库版本，也不当作各恶意 Skill 的版本号。

## 未计入的 144 条

见 [unverified/records.json](unverified/records.json)，每条保留来源、核查范围和排除原因。包括原仓库不可访问、只能确认初始快照、历史包不匹配、缺少主文档或文件无法读取。没有将同名文件、复制目录或人工注入变体直接认作版本更新。

math-calculator 原仓库找到真实提交对，但新版 scripts/calculate.py 返回 OSError，无法交付完整快照，因此整对排除；未重试、未从归档或其他路径恢复。包含该文件的 SRC002 完整归档不随本包分发，保留校验值及来源记录。原仓库中受控、去武器化演示样本的两次目录布局对应相同的 2 个文件 blob，也没有算作更新。

## 文件入口与统计边界

- [updates_index.csv](updates_index.csv)、[updates.jsonl](updates.jsonl)：13 对完整 Git 版本索引与对比链接。
- pairs/MASC-0001/ 等：old/、new/、SKILL.diff、package.diff、files.json、Git 树、路径证明和标签／来源证据。
- [summary.json](summary.json)、[verification_report.json](verification_report.json)：统计及离线核验。
- source/：原始基准恶意清单、固定版本说明、选定历史来源行与汇总基准清单。大体量历史生态 CSV 仅保留已核验的哈希和固定提交链接，完整原文件保存在采集工作区。
- audit/ 与 unverified/：数据集历史、目录移动证据、仓库可访问性、去重、排除记录。

离线核验可检查原始文件哈希、目录完整性、Git 树与提交路径关系、第一父提交、主文档的公开恶意身份及已记录的完整源包清单对应关系。SRC002 原始归档字节在采集阶段校验，未包含在本包内，离线验证不重新读取该完整归档。

**这些结果不证明旧版良性，也不证明新增或变化的文件就是恶意行为成因，不确认全球首次恶意版本。** 这里的恶意收录标签不等于对整个来源仓库或作者作恶意判断。研究复现应固定 Git 提交，不把当前分支状态或当前扫描结果套用给历史版本。

校验：`python verify_dataset.py`。样本仅作为静态研究数据，不安装或执行。第三方内容保留原作者权利及适用许可。
