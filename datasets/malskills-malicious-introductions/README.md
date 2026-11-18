# 恶意 Skill 的首次出现追溯：MalSkills 100 个样本

已对固定版本 MalSkills 的 **100 个恶意样本**查询归档 Git 历史，恢复 114 个路径提交快照，并额外恢复 1 个关键提交的直接父版本。

**确认结果必须分两层：归档路径历史中确认 1 条恶意分发指令的首次引入；全注册表发布历史中的首次恶意版本确认 0 条。** 0 表示尚未达到证据标准，不表示没有恶意更新。

## 可确认的归档引入

`zaycv/clawhub` 的归档 **1.0.3**，提交 `93d548f298d9d996a42da85de09f9860136c2280`，首次新增下载并运行 `Ddoy233/openclawcli` 的前置安装说明，同时增加 glot 页面执行引导。

该提交时间为 **2026-01-31 13:34:46 UTC**；注册表元数据中的发布时间单独保存在 decision.json，不能与 Git 提交时间混用。直接父提交为 `8275d463c9b25401d80098b07e65530444af8ff0`，父目录元数据版本是 1.0.0，父版主文档 blob 与最早 1.0.0 完全一致，未含这条分发说明。1.0.3 的元数据和 Git 提交消息相互对应。

[Snyk 独立调查](https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/) 将同一发布者/技能及该下载仓库与恶意 CLI 分发联系起来；[官方项目 Issue #108](https://github.com/openclaw/clawhub/issues/108) 另有事件报告和账号下架处置记录。

证据见 [decision.json](confirmed_archive_introductions/zaycv_clawhub/decision.json) 与 [主文档差异](confirmed_archive_introductions/zaycv_clawhub/SKILL.diff)。这证明的是归档 Git 中该指令的引入，**不是此前版本整体良性的认证，也不是受害者实际感染的证明**。

尚未得到权威完整发布列表；1.0.1/1.0.2 是否曾发布没有建立证据。针对缺失版本的公开提交搜索无结果不构成不存在的证明。因此不将 1.0.3 写成全注册表的确定首恶版本。

## 全部样本结果

- 99 个样本的收录主文档 SHA-256 与归档种子提交一致；另 1 个对应已知被主机拦截的 blob，未分发该内容。不可把“未检查”写成哈希不匹配。
- 61 个样本的可读历史中，存在安全报告 IOC 与下载执行/安装指令的静态交叉佐证。包括上述 1 条归档引入；其余仅能说在最早可取得快照已出现，不能建立此前良性版本。
- 39 个样本尚不足以建立“具体版本恶意行为 + 独立安全事件”的联系，已单独保留；例如 zaycv/shield 的名称/域名变化不够证明恶意行为何时开始。
- 100 条全局首次恶意版本仍未知，保存在独立 unresolved 清单；没有给任何历史版本或更新对擅自新增整体安全真值。
- 100 个最早路径提交的父提交均可访问，该路径在父提交返回不存在。这是当前指定路径的归档导入边界；不排除注册表未归档版本、早期改名或其他分支。

## 分开存放与入口

- [index.csv](index.csv) / [index.jsonl](index.jsonl)：100 条逐条结果，来源可验证性、事件关联、首次观测和全局未知字段分列。
- [corroborated_observations/](corroborated_observations/)：61 条具有静态事件 IOC 佐证的观测索引，**不当作已经独立人工双审的训练真值**。
- [unverified/incident_or_behavior_not_corroborated.jsonl](unverified/incident_or_behavior_not_corroborated.jsonl)：39 条独立事件/行为证据不足的样本。
- [unverified/source_content_not_verified.jsonl](unverified/source_content_not_verified.jsonl)：原始收录内容尚不能比对的样本。
- [unverified/global_first_version_not_established.jsonl](unverified/global_first_version_not_established.jsonl)：100 条全局首恶版本未确定清单；与上面维度可以重叠，不应相加当作样本数。
- artifacts/：原始 Git 跟踪文件、目录树与逐文件哈希；histories/、records/、parent_evidence/：固定提交的历史和谱系证据。
- [static_ioc_evidence.jsonl](static_ioc_evidence.jsonl)：文件/行号、来源 ID、直接或静态解码得到的 IOC。只把 base64 当文本解码，没有运行命令或访问攻击地址。
- [source/event_sources.json](source/event_sources.json)：3 份安全研究一手报告、4 个官方项目问题记录的核验；只保存链接、证据锚点、摘要、哈希，不转载完整文章。

## 方法边界

原 openclaw/skills 与 clawdbot/skills 当前对本次访问返回 404，不能声称已访问到原注册表仓库。归档快照与固定 MalSkills 原文哈希匹配提高可追溯性，但不能代替作者身份或完整注册表发布记录。4 个官方注册表 API 请求因本机代理错误未取得结果，明确记录在 live_registry_checks.json。

安全事件的发布日期、登记发布时间、归档提交时间分别保存。事件记录按精确 owner/slug、明确恶意下载来源、明确 IOC+执行链分开匹配；仅发布者相同、名称相似或普通 glot.io 链接不能自动认定某版本恶意。单行匹配和静态解码仍可能漏掉复杂流；没有执行样本、安装依赖、访问恶意基础设施或绕过主机拦截。已知被拦截的 3 个 blob 在全部提交中按内容 ID 排除，共 5 处快照缺失。

分发保留原始数据集快照的 malicious 标签，但历史版本/更新对的标签保持 null。第三方 skill 原文适用原作者权利和各自许可；本整理不统一重新授权。

离线校验：`python verify_dataset.py`。原始文件字节、Git blob 与目录树哈希、种子一致性、100 条分组和关键父子关系均可复核。
