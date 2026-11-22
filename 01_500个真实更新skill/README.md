[返回仓库首页](../README.md)

# 500 个已人工确认良性 Skill 更新（用户确认）

整理日期：2026-11-22。共 500 对真实 Git 更新、1000 份完整 Skill 子目录快照，来自 15 个仓库。

**这 500 对旧／新版均标注为“已人工确认良性（用户确认）”。标签依据是数据集维护者于 2026-11-22 报告已完成人工确认；没有提供审核人、实际审核日期、方法或逐条记录，以上字段留空。整理助手未独立复现安全审核。**

标签来源见 [人工确认声明](human_review_confirmation.json)，安全审核证据的可用性见 [证据状态](independent_review_evidence.json)。真实历史、父提交与文件身份的核验结果独立保留。

每对包含 old/、new/、SKILL.diff、metadata.json 和前后目录树。旧提交是新提交的第一父提交，两侧均存在同一路径 Skill；前后主文档的说明或实现有实际变化。排除仅头部版本/更新时间变化及完整旧新版内容完全相同的重复对。

版本类型为 Git commit；不把提交 SHA 当作发布版本号。恢复的是完整 Skill 子目录，未审计或打包仓库其他路径、关联 Skill、外部依赖和运行环境。

| 来源 | 版本对 |
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

文件入口：`updates.json` 为正式真实更新索引；`human_review_confirmation.json` 记录用户提供的人工确认；`excluded_and_unverified.json` 保存未入选原因；`sources.json` 保存固定来源。

源代码、指令、脚本仅作为研究数据保存，没有安装或执行。文件哈希和 Git 树核验不能替代安全复核。良性标签来自用户报告的人工确认，不由官方来源或无规则命中推导。

许可：第三方内容保留各来源及文件原有许可，见原始目录中的 LICENSE/NOTICE 和 sources.json；仓库级许可提示不替代文件级许可。本包不对第三方内容重新授予统一许可。

复核：运行 `python -S verify_delivery.py` 校验文件身份、目录覆盖、去重和说明内容变化；不会执行样本。

统计独立性：这些 Skill 可能来自同一批量提交或相似模板，不能视为相互独立的攻击/更新机制。训练测试应按仓库、提交事件和模板家族分组。

当前版本对对应 208 个不同的仓库/新提交事件，最大单次提交涉及 28 个入选 Skill。与原有 500 对的主文档字节配对重复为 0 对；此检查不替代语义去重。

替换记录：本目录于 2026-11-22 替换原 GitSkills 500 对更新；旧数据可从仓库提交 7af3c962202bdb34f5e7647c555fe29d6c83a85a 的同名目录恢复，不在当前集合重复计数。
