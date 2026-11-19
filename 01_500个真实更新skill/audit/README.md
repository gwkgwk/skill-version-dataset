[返回仓库首页](../../README.md)

# GitSkills 500 条更新安全初审

结论：不能将这 500 条更新统一认定为良性。它们是真实历史更新，但 500 条安全标签仍为未知；本次没有生成良性或恶意真值。

已覆盖 2,604 份原始文件的字节清单，其中 2,595 份 UTF-8 文本进入规则扫描，9 份二进制未进行语义分析。两份带单个 NUL 的 SKILL.md 已作为文本扫描，未整份跳过。17 类规则分别记录新增、删除及既有迹象。

规则初筛：320 条无规则命中，147 条低优先级，33 条中优先级。这些是复核优先级，不能映射为良性/恶意或概率。

助手对全部 33 条中优先级以及另外 11 条做了上下文复核，共 44 条。复核阅读了匹配上下文、主文档差异和部分相关脚本；没有声称对 44 条全部依赖或 500 条全部语义做过审计，也不是独立人工双审。

## 值得继续审查的变化

- GSU-0285：新增跳过权限检查的启动示例。
- GSU-0304：删除原有提交前必须确认的要求。
- GSU-0414：从建议安装依赖改为自动静默安装未固定版本的 yfinance。
- GSU-0329：新增从 GitHub 自动配置/启动 MCP 服务的方式，外部服务实现不在快照内。
- GSU-0008：新增恢复聊天应用用户标识的逻辑，涉及本机私人聊天数据与授权边界。

这些现象不足以推断攻击意图；恶意版本数量不能由规则命中数计算。GSU-0284 的 curl-pipe-shell、GSU-0322 的 uvx GitHub fallback、GSU-0498 的 @latest 依赖均已在旧版存在。

## 文件与复现

- [review_decisions.csv](review_decisions.csv)：500 条逐条结果与 44 条复核备注。
- [findings.jsonl](findings.jsonl)：按文件、行号、版本和新增/既有状态保存证据。
- [unscanned_files.json](unscanned_files.json)：没有进行语义分析的二进制清单。
- [review_summary.json](review_summary.json)：覆盖与统计。

在 GitHub 仓库根目录运行（扫描器只读样本，不执行它们）：
```bash
python 01_500个真实更新skill/audit/scan_updates.py --dataset-root 01_500个真实更新skill
```

单行正则无法完整发现多行数据流、编码/混淆、动态加载、外部依赖和运行时行为，也可能漏掉删除防护语句导致的风险。扫描无命中不能证明无害。作为良性评测集前，需要逐条语义审计、固定并审查依赖、验证运行时和授权边界，并由独立审阅者判定；旧版也必须先建立可信基线。

## 44 条上下文复核记录

- **GSU-0008** `sensitive_data_review`：新增从本机 KakaoTalk plist 哈希恢复用户标识的穷举逻辑；配合既有聊天数据库读取功能涉及私人数据。说明限定本人的设备/账户，但未验证运行行为和授权落实。 [原提交对照](https://github.com/hivgb1-ai/do-better-workspace-v2/compare/d9853eb8bcea0ed0f28b3b5e17a5011991f5dcc0...643bc1cc82f4e7a768d972979455ff741c46b11c)

- **GSU-0024** `context_explained`：新增成熟度元数据与空 allowed-tools 声明；不能仅凭声明判断宿主的实际权限。未见此次匹配的危险行为。 [原提交对照](https://github.com/ivegamsft/basecoat/compare/b529f9e7a3e8aba7735325d967003c2eec5a87b1...ed46b66a82f5d6cb4ef1f88460e20f6ee41cce7c)

- **GSU-0061** `context_explained`：allowed-tools 由列表改为单行，所列工具相同；命中源于格式变化。 [原提交对照](https://github.com/monotio/spa-vue-template/compare/a53a92fabb6f307969e528d00502568196d9163b...06d8bc6f0b9aa753f38101494b13308700e9696f)

- **GSU-0067** `context_explained`：新增检查 worktree 外部引用、移除失效 npm 全局链接后重新链接的步骤；安全绕过语句是明确禁止，不是要求绕过。 [原提交对照](https://github.com/Jpk0512/ryu-next/compare/b2744b5e4dc508a9d17d0c2848594107c186fa05...3a99aaa20fc8c74c7824ea86cc85b2caef0fd7c6)

- **GSU-0079** `context_explained`：更新社交平台参数文档；npx postbridge-cli 已在旧版使用，此次命中不是首次引入远程包执行。 [原提交对照](https://github.com/post-bridge-hq/agent-mode/compare/b8e4178c805f313d2565b27de27b2a46b949a958...4ee31f757aca702a31db64010253094d125fed1c)

- **GSU-0095** `context_explained`：旧版 pyc 被删除，新版无该二进制；主要变更是将流水线路径改为 skill 根目录相对路径。未反编译旧 pyc。 [原提交对照](https://github.com/fx818/Seller-Churn/compare/16956e83aadbe96e04a40c8ebc7bf79d5573d7b1...ba1f2ea08ad51f77ca0a4414b68518e91f99093e)

- **GSU-0113** `configuration_write_review`：新增可写入 ~/.claude/settings.json 的状态栏安装程序及工具声明。文档要求用户同意，安装器保存备份；仍需核查状态栏脚本及运行权限。 [原提交对照](https://github.com/GaGa55555LaLa/agent-master/compare/aae8a9f8c3fed138d5aae6565ceff71c96d20162...0b7b8f4af00c02a152183081cfe3f86b52b99a2a)

- **GSU-0133** `host_security_review`：新增 SSH 安装 profiler 及调整 /proc/sys/kernel/perf_event_paranoid、kptr_restrict 的步骤。性能分析语境可解释用途，但涉及主机安全配置，不能据此标为无风险。 [原提交对照](https://github.com/JetBrains/youtrackdb/compare/7e19d84b5110d0926398cd3a7a079e8974d0ba28...a55372058e69e235369c9246ece7eaaf9a14ff04)

- **GSU-0176** `context_explained`：新增文字要求测试章节引用运维步骤而非重复 curl 命令，属于写作说明。 [原提交对照](https://github.com/SensorsIot/Universal-Embedded-Workbench/compare/aca51fb757afe23dc63899898bf3e81705c0bf19...f341c2f60fbffeedf904d0d4332de07ef717ccc4)

- **GSU-0202** `context_explained`：提示注入语句是 test-case-patterns.md 中的防御测试输入；此次变化增加基础设施失败时禁止自动修补提示词的前置条件。 [原提交对照](https://github.com/RelevanceAI/relevance-builder-kit/compare/52ee6648db2ffc86e7af3005a8d18cb6fedfa821...dcf4426ad89af5adc269d2684b1ee2882cfa2113)

- **GSU-0220** `data_quality_review`：两版主文档同一位置均含一个 NUL，位于 RG\x00BA 代码示例；已按 UTF-8 扫描，没有因 NUL 整份跳过。新增脚本处理图片和本地 XML，NUL 是既有数据质量问题。 [原提交对照](https://github.com/ZHLX2005/fr/compare/b5e4fab52e24d08d242e89d2d039da91ddeb2c07...75be57de67af280aaa82e3dc7b00a3966a05a087)

- **GSU-0221** `context_explained`：without confirmation 命中实际是禁止未确认推断；新增路径穿越、符号链接和版本目录约束。 [原提交对照](https://github.com/xingwudao/open-xquant/compare/11a9702d16c2051dd034281c6d6c48fc05597195...6af7fa77f143e2f5dfc9d96464f9f60b66b4c60a)

- **GSU-0231** `context_explained`：已阅读新增 triage.sh；rm -rf 位于输出计划的字符串，不是脚本直接执行。SKILL 保留逐层明确批准；可选 --fetch 会修改 Git 引用。输出计划中的路径引用仍需使用者复核。 [原提交对照](https://github.com/thevibeworks/deva/compare/01f69852c567085517424dba2de91a2e5ae0ef0a...e4c9f8bca45aea43834c78187281526b0cb27e6f)

- **GSU-0232** `context_explained`：既有 npx markdownlint 的目标从 workflows 改到 writeups，另增仓库外部验证脚本引用；没有因这条命中确认恶意。 [原提交对照](https://github.com/26zl/cybersec-toolkit/compare/a7dba452d4f9ec4ee873c48f7175165c62684ed6...1d959e6ea0750587416396198a6a970a4cc2e71f)

- **GSU-0237** `external_code_review`：新增 Skill 工具声明，并将动态提示词加载改为 sibyl.orchestrate.render_skill_prompt；该 Python 模块在 skill 目录外，不在本数据包中，不能验证动态生成内容。 [原提交对照](https://github.com/Sibyl-Research-Team/AutoResearch-SibylSystem/compare/f800e93ab93df681b810be7cadbb523c2b300680...8e23f32e75578b3a43b1dc56f146e64eece80556)

- **GSU-0259** `context_explained`：rm -rf 命中是新增数据丢失警告，建议只删除出错的索引槽；属于风险提示。 [原提交对照](https://github.com/jamie8johnson/cqs/compare/acdcd644d88a27d4fdb23516adba24e74032ad29...3f016872f5b7c1703c9c4e1904cf8871522b8d98)

- **GSU-0283** `external_instructions_review`：由读取本地知识库改为 WebFetch GitHub main 分支规则，再将规则用于目标仓库，未固定外部内容提交；新增工具声明与外部信任边界需要审查。 [原提交对照](https://github.com/BoardPandas/BP/compare/6e05900cd625825ade582ac4b005ad3083874ed1...1b54cb08730076d418560d4c05f2a66f4fdc0c52)

- **GSU-0284** `inherited_risk`：curl https://mise.run | sh 两版都有，此次仅修改弃用时间文档；不能将既有下载执行归因于本次更新。未验证安装端点。 [原提交对照](https://github.com/brentmitchell25/mise-plugin/compare/26bedb8e4c553609cd9fdff7a20be9cda878ec16...f07b45b7ae10ce97a73e234a3797d58c471f4470)

- **GSU-0285** `permission_bypass_review`：新增 references/plugin-usage-guide.md 第 8 行使用 claude --dangerously-skip-permissions；是权限检查绕过示例，足以排除直接作为已验证良性真值，但没有恶意意图或利用结果证据。 [原提交对照](https://github.com/allanpk716/patent-disclosure-writer-skill/compare/783c02e2c8d7422dddfbb232904287531428dc51...73798ba10681e91e950a7b8c8563fcd1a67b7614)

- **GSU-0304** `approval_regression_review`：旧版要求提交前得到用户确认、不能自行 commit；新版删除该句，改为分析后直接提交并报告。属于可验证的确认边界变化，不能单凭此认定恶意。 [原提交对照](https://github.com/haribote/dotfiles/compare/d0014f69bfc3c05824e61ce30551c6b26c923550...df6a792e42250c442357455c9f3141233441d91a)

- **GSU-0314** `tool_scope_review`：新增 Bash 等工具声明、将 ADR 模板拆分到引用文件并增加 arch-sync 协作。权限声明与被调用的外部 skill 需按宿主授权解释。 [原提交对照](https://github.com/tobiwan88/weather-station/compare/b6e745b2d21a4817d23baadc588e49fc5e168655...ee372f2afb7319ee46425141d6ab85fd838e86b2)

- **GSU-0315** `overwrite_policy_review`：concealment 命中是不要要求用户重组文件夹，属于误报；此次确实增加 current-state.md 默认覆盖及 headless 覆盖外来格式的说明，涉及覆盖策略。 [原提交对照](https://github.com/simonconway1979/os-intelligence/compare/6b94f39cf6f77bd2601a6025632a29e48f72c540...fb0b14432b174ee78311c963be086c24c2d56acf)

- **GSU-0322** `inherited_risk`：GitHub uvx fallback 旧版已经存在。此次脚本重构并取消固定数据根目录，改由 CLI/配置/cwd 决定；不能把该 fallback 当成新增恶意下载。外部 CLI 未审计。 [原提交对照](https://github.com/upbit-official/upbit-strategy-toolkit/compare/27835d998f085b00245d5b1708134e536557a80f...e0163ebf505e44a5d34b9816707049aae568ab1a)

- **GSU-0328** `context_explained`：改写为路径约束、dry-run、明确保护操作确认和定向修改规则；新增 Edit/AskUserQuestion 声明与防护语境一致。 [原提交对照](https://github.com/bniceley50/GravenSpire/compare/ce634c360b70b5d2e7ba620a6710940285a1a694...32e13a65e20ae767dcde4c4f117538ff2c733ec1)

- **GSU-0329** `remote_service_review`：由手工 clone/build 注册改为 npx -y github:GemachDAO/gdex-skill 自动初始化 MCP 并从 GitHub 启动；未固定提交且服务代码不在 skill 目录。旧版也依赖外部源码，此次增加自动配置方式，不能据此认证良性。 [原提交对照](https://github.com/GemachDAO/gdex-skill/compare/d04ad1176ed31576d0411a6946247f0acabd96d7...fc8e1ca38699ec119bb9ff673e5c96c0e1bbef84)

- **GSU-0348** `context_explained`：读取 OneDrive/SharePoint 的 requests.get 使用 graph.microsoft.com，认证头用于该 API；同节写回也指向 Graph。未发现此处向无关域名发送凭据的证据，未验证运行时或权限。 [原提交对照](https://github.com/markus41/Claude-m/compare/5558cf063ad1327bf8e35de0f26af7f49e8dd730...c8836aeea0f1bfb30dabd6371483f97392cb58da)

- **GSU-0352** `context_explained`：新增 Do not push without explicit confirmation，以及移动/改名需确认；匹配是保护性否定，不是绕过确认。 [原提交对照](https://github.com/kjgarza/marketplace-claude/compare/f6802edf414df03a09b64391163706d2185d1099...d354c6a2f8df077a805007f560cded7d464560ee)

- **GSU-0371** `external_instructions_review`：新增 Node/npm 工具声明、依赖安装和指向 datopian/portaljs main 分支的规范工作流；npx tsc 是类型检查语境。外部动态规则及依赖仍不在已审计范围。 [原提交对照](https://github.com/gabrielmoreira/agent-skills-mirror/compare/7d028d066d2c72c4e169b1f495e292411815847f...b4501eab9a3c15807b62fffa46bd89534ab7e0b7)

- **GSU-0373** `context_explained`：allowed-tools 从单行改 YAML 列表，所列四项工具保持一致；PNG 两版相同且未解析图像潜在内容。 [原提交对照](https://github.com/robinsadeghpour/content-workflow/compare/b2b12f5ae554a38494a955ff519530af02ce18bf...2fb3b69d3cf555758f2ea55514e57446939c8839)

- **GSU-0379** `context_explained`：os.environ 命中是说明测试会替换环境，仅保留 PATH/HOME/TMPDIR 并注入固定测试身份；没有凭据外传证据。 [原提交对照](https://github.com/ishkamiel/ishlib/compare/0288d1190178f7bd83cb97f4744185cf106e55b3...bbcccd7a8d2af225e52f350ca0770c3de4f3a379)

- **GSU-0384** `context_explained`：忽略先前指令的文本是既有防注入测试与 not.toMatch 断言；此次仅新增与 BOLA 检查的执行顺序说明。 [原提交对照](https://github.com/Globussoft-Technologies/medcore/compare/e3166f0f8ba3ba9a6aac02360da5a50f03c45e49...221d21a9f4099bb588cce2d648488413f8f942c1)

- **GSU-0410** `context_explained`：curl noise 是图形学噪声术语，非网络下载命令。 [原提交对照](https://github.com/rlefko/rycraft/compare/75048ebfb928b1ad24e6ea52011d6cf86f3f6588...14ddcad51d6eceab4904e9291c53e7e3639a18d5)

- **GSU-0414** `automatic_install_review`：新增捕获导入失败后静默执行 pip install yfinance，未固定版本，并抑制 stdout/stderr；旧版仅提示安装或降级搜索。行为边界发生变化，外部依赖未审计。 [原提交对照](https://github.com/luongjames8/aiib-research-skill/compare/66ccd02e5dbd67538ce277fdd7329b29ec9a18c1...42b0059e9697713a6d89d9d070ac9ef9352015b7)

- **GSU-0418** `deployment_review`：新增 SSH root 到固定主机的部署和健康检查示例；urllib 示例请求该主机容器内 localhost。属于部署语境，未连接主机或证实其归属。 [原提交对照](https://github.com/AlexMobiCraft/FREESPORT/compare/93288dc24adfd5b707dd200a17889ddc4182d32e...5e16df4d6d4950ce0da7bfe369fda1ef3673d831)

- **GSU-0425** `context_explained`：NEVER Without Confirmation 是新增防护标题，要求修改防火墙/SSH/规则/安全服务前确认。 [原提交对照](https://github.com/datnp1003/anos/compare/a8f93fededb93919df891d4f5dee5da6081aaa32...badfac29dfaa61aad312964987da4d9d0a8370b7)

- **GSU-0426** `workflow_override_review`：文档自称本地最高优先级覆盖并自动处理 archive/journal，含有条件的自动 commit/push；旧版已有自动 push 步骤。git rm --cached 是精确索引整理，不是删除工作树；外部任务脚本及授权依据未核实。 [原提交对照](https://github.com/SilentFlower/flower-trellis/compare/c6109828cae69bb9064dcd169d1c78dc1ab622cf...90220a671eb92ec9c3681e6efe4946aead5d0c39)

- **GSU-0428** `context_explained`：os.environ.get 示例用于资源名称配置，新增要求给所有消费资源的计算单元传递环境变量，没有直接凭据读取证据。 [原提交对照](https://github.com/Boise-State-Development/agentcore-public-stack/compare/d4f06dd194b11a26c58ad33fc53840867dca1685...b40a59e78265fd4b705cca44a50814d810df5f87)

- **GSU-0436** `context_explained`：YAML 描述、标签、兼容性与 allowed-tools 换行格式调整；工具列表内容未增加。 [原提交对照](https://github.com/flight505/skill-forge/compare/7623f2cbb7fc95becbaeda1cf5b89882bd880081...177611650f5d0e5f5fe7c83f1a752c38ac0c5c28)

- **GSU-0437** `context_explained`：新增脚本向配置常量 http://localhost:12017 的 Whisper 服务上传指定音频，并保存字幕；并非已证实向外部攻击者外传。未运行服务或验证传输授权。 [原提交对照](https://github.com/m0rg0t/tutorial-video-creator-skill/compare/934600c4d4fc343a6a80b5c5a3be45260f4739bd...59dd47075757fd3bb5b764b4fe5e5743c6ac174a)

- **GSU-0453** `tool_scope_review`：新增 Task 工具并把最佳实践搜索改为并行研究代理；属于可观察的工具/执行模型变化，未见该上下文中的直接恶意证据。 [原提交对照](https://github.com/shakefu/contextium/compare/28ef0c44296ced938989e1de2ebbe1d5d286ce03...6a8ba46d37e605427cd0b4a5924e0b224a851baa)

- **GSU-0468** `context_explained`：新增 rpc_server.py 的进程启动使用固定 argv 列表，默认本地 bash 脚本，未传 shell=True；环境变量用于图路径。只复核此入口，未完整逐行审计所有新增分析模块。 [原提交对照](https://github.com/jankneumann/agentic-content-analyzer/compare/6ce6fcedda76245797a27ef2fa88817fd535b3e2...e686d9ee6f62eaa476f87c5a4f83fbfc2d2e0b22)

- **GSU-0469** `context_explained`：新增批处理器用 argv 列表调用同目录 clean_stale/check_missing/validate；有批量修改本地翻译文件的功能，未执行或完整验证下游脚本。 [原提交对照](https://github.com/CofficLab/Cisum/compare/8ff9bcb783ef978233eb5b30d72be5aec2e877b1...6e1c5c4a87a549f52046ba660611d365dceceb23)

- **GSU-0478** `tool_scope_review`：新增 Read/Write/Bash/Glob/Grep 声明；没有默认权限基线，不能仅凭声明判定实际提权或恶意。 [原提交对照](https://github.com/AmbroseTriC/ECON53_DAC/compare/1661bd81ed4f446442f966d7f318fa58721d64ad...7adc8d3dd22ce5d4ea8915f8caed4f6415cba8b6)

- **GSU-0498** `inherited_risk`：将 pnpm dlx ctx7@latest 改为 npx ctx7@latest；未固定依赖风险旧版已有，仍保留不要提交凭据、不要发送私有信息的说明。 [原提交对照](https://github.com/driver-labs/app/compare/2bc744fc2b280fac4d153bc56d745a9ec06c84a0...c8fb34df4ea884311c55c0cd3537255a42c42bc4)
