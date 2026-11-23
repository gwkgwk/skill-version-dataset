# 第三方来源与归属

本仓库为多来源研究数据的整理集合。以下公开数据集提供种子、标签、来源线索或原始内容；当前仓库中的更新配对和克隆筛选由后续追溯与核验产生，不是全部由上游直接发布。

| 上游来源 | 在本项目中的用途 |
| --- | --- |
| [GitSkills 官方样本库](https://github.com/giuseppedestefanis/gitskills-sample)、[完整数据页面](https://huggingface.co/datasets/mvaccargiu/gitskills) | 仅为替换前 500 对的历史来源，不属于当前 500 对 |
| [MalSkills](https://github.com/security-pride/MalSkills) | 恶意单快照标签与来源种子；正式更新中收录 1 对恶意分发指令引入 |
| [MalSkillBench](https://github.com/lxyeternal/MalSkillBench) | 17 对发布版本更新的恶意来源包与比对依据 |
| [MaliciousSkillBench](https://github.com/protectskills/MaliciousSkillBench) | SRC004 / SkillLeakBench 来源分组中恢复 6 对发布版本更新 |
| [MaliciousAgentSkillsBench](https://github.com/protectskills/MaliciousAgentSkillsBench) | 13 对 Git 提交版本更新的恶意来源标签与原始仓库线索 |
| [SkillReuse](https://github.com/zly123987/skill-reuse)、[Zenodo 语料](https://zenodo.org/records/19245910) | 恶意安装指令文档快照及公开克隆图；本项目核验 20 对全文相同克隆 |
| [SkillLeakBench 原仓库](https://github.com/AgentSkillsPrivacy/SkillLeakBench) | 83 条恶意案例的版本来源核查；原仓库直接追溯新增 0 对 |
| [SkillLifeBench](https://github.com/Tasselszcx/SkillLifeBench) | 独立受控子集中的47对工具实现安全回归；不计为真实历史恶意更新 |
| [Skill-Inject](https://github.com/aisa-group/skill-inject)、[作者数据与最终标签](https://huggingface.co/datasets/davidsmts/skill-inject) | 独立受控子集中的53对完整宿主包与攻击注入对照；沿用作者最终标签 |
| [openclaw-removed-skills 归档](https://github.com/friuns2/openclaw-removed-skills) | 部分下架 Skill 的原提交和历史文件恢复来源 |

每条记录保留的原始仓库、路径、提交、哈希和上游身份是更细粒度的归属依据。GitHub 页面中的仓库所有者或 scopedName 不自动等同于 Skill 的原始发布者，分析时需结合具体源路径。

[Snyk 调查](https://snyk.io/articles/clawdhub-malicious-campaign-ai-agent-skills/)及 [Antiy CERT ClawHavoc 报告](https://www.antiy.net/p/clawhavoc-analysis-of-large-scale-poisoning-campaign-targeting-the-openclaw-skill-market-for-ai-agents/)等用于安全事件交叉核对，事件报告本身不提供所有历史版本的安全标签。

各第三方内容保留原有归属、许可证与权利。SkillReuse 的 Zenodo 记录标注 CC BY 4.0；这不改变其中其他原作者可能持有的权利。本项目 [LICENSE.md](LICENSE.md) 仅对本项目有权许可的原创贡献授予许可。

使用本集合时，请引用本项目，并根据所用子集引用相应上游论文或数据集。原始 README、固定提交信息和校验回执保留在各目录的来源或证据文件中。

## 当前 500 对的原始仓库

以下来源的固定提交、许可线索与逐对路径见 [来源清单](01_500个真实更新skill/sources.json)。良性标签另来自用户报告的人工确认，不能把原始仓库维护者描述为此次人工审核人。

| 仓库 | 更新对 |
|---|---:|
| [anthropics/skills](https://github.com/anthropics/skills) | 6 |
| [cloudflare/skills](https://github.com/cloudflare/skills) | 18 |
| [expo/skills](https://github.com/expo/skills) | 25 |
| [getsentry/skills](https://github.com/getsentry/skills) | 23 |
| [google-labs-code/stitch-skills](https://github.com/google-labs-code/stitch-skills) | 9 |
| [google/skills](https://github.com/google/skills) | 75 |
| [googleworkspace/cli](https://github.com/googleworkspace/cli) | 48 |
| [hashicorp/agent-skills](https://github.com/hashicorp/agent-skills) | 1 |
| [huggingface/skills](https://github.com/huggingface/skills) | 16 |
| [microsoft/skills](https://github.com/microsoft/skills) | 172 |
| [openai/skills](https://github.com/openai/skills) | 19 |
| [stripe/ai](https://github.com/stripe/ai) | 10 |
| [supabase/agent-skills](https://github.com/supabase/agent-skills) | 2 |
| [trailofbits/skills](https://github.com/trailofbits/skills) | 72 |
| [vercel-labs/agent-skills](https://github.com/vercel-labs/agent-skills) | 4 |

## 100对受控更新的固定来源

- SkillLifeBench：`57bc115a56baa483d4f68824d5a9c78f00a265dd`；场景和作者冻结测量，数据许可副本为CC BY 4.0。
- Skill-Inject：`b07cfdb2299b07ceb156c227b4b845359bbac363`；宿主包、原始攻击定义及构造规则。保留来源MIT许可，第三方宿主内许可继续适用。
- Skill-Inject最终标签：Hugging Face修订`e3ec7ff5514b7b95023cb1e8f803e212e06d0e75`；修订后的明显攻击定义已与固定GitHub来源解析核对。

逐条来源、改动说明、选取理由、证据等级与许可证见[04_100对受控更新样本](04_100对受控更新样本/README.md)。此次整理不是对旧版整包良性或新版攻击成功的独立运行认证。
