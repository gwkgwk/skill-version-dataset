"""Record the assistant's targeted contextual review separately from safety truth."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parent
# Only records actually inspected in this review. These are not human ground truth.
NOTES={
'GSU-0008':('sensitive_data_review','新增从本机 KakaoTalk plist 哈希恢复用户标识的穷举逻辑；配合既有聊天数据库读取功能涉及私人数据。说明限定本人的设备/账户，但未验证运行行为和授权落实。'),
'GSU-0013':('unused',''),
'GSU-0024':('context_explained','新增成熟度元数据与空 allowed-tools 声明；不能仅凭声明判断宿主的实际权限。未见此次匹配的危险行为。'),
'GSU-0061':('context_explained','allowed-tools 由列表改为单行，所列工具相同；命中源于格式变化。'),
'GSU-0067':('context_explained','新增检查 worktree 外部引用、移除失效 npm 全局链接后重新链接的步骤；安全绕过语句是明确禁止，不是要求绕过。'),
'GSU-0079':('context_explained','更新社交平台参数文档；npx postbridge-cli 已在旧版使用，此次命中不是首次引入远程包执行。'),
'GSU-0095':('context_explained','旧版 pyc 被删除，新版无该二进制；主要变更是将流水线路径改为 skill 根目录相对路径。未反编译旧 pyc。'),
'GSU-0113':('configuration_write_review','新增可写入 ~/.claude/settings.json 的状态栏安装程序及工具声明。文档要求用户同意，安装器保存备份；仍需核查状态栏脚本及运行权限。'),
'GSU-0133':('host_security_review','新增 SSH 安装 profiler 及调整 /proc/sys/kernel/perf_event_paranoid、kptr_restrict 的步骤。性能分析语境可解释用途，但涉及主机安全配置，不能据此标为无风险。'),
'GSU-0176':('context_explained','新增文字要求测试章节引用运维步骤而非重复 curl 命令，属于写作说明。'),
'GSU-0202':('context_explained','提示注入语句是 test-case-patterns.md 中的防御测试输入；此次变化增加基础设施失败时禁止自动修补提示词的前置条件。'),
'GSU-0220':('data_quality_review','两版主文档同一位置均含一个 NUL，位于 RG\\x00BA 代码示例；已按 UTF-8 扫描，没有因 NUL 整份跳过。新增脚本处理图片和本地 XML，NUL 是既有数据质量问题。'),
'GSU-0221':('context_explained','without confirmation 命中实际是禁止未确认推断；新增路径穿越、符号链接和版本目录约束。'),
'GSU-0231':('context_explained','已阅读新增 triage.sh；rm -rf 位于输出计划的字符串，不是脚本直接执行。SKILL 保留逐层明确批准；可选 --fetch 会修改 Git 引用。输出计划中的路径引用仍需使用者复核。'),
'GSU-0232':('context_explained','既有 npx markdownlint 的目标从 workflows 改到 writeups，另增仓库外部验证脚本引用；没有因这条命中确认恶意。'),
'GSU-0237':('external_code_review','新增 Skill 工具声明，并将动态提示词加载改为 sibyl.orchestrate.render_skill_prompt；该 Python 模块在 skill 目录外，不在本数据包中，不能验证动态生成内容。'),
'GSU-0259':('context_explained','rm -rf 命中是新增数据丢失警告，建议只删除出错的索引槽；属于风险提示。'),
'GSU-0283':('external_instructions_review','由读取本地知识库改为 WebFetch GitHub main 分支规则，再将规则用于目标仓库，未固定外部内容提交；新增工具声明与外部信任边界需要审查。'),
'GSU-0284':('inherited_risk','curl https://mise.run | sh 两版都有，此次仅修改弃用时间文档；不能将既有下载执行归因于本次更新。未验证安装端点。'),
'GSU-0285':('permission_bypass_review','新增 references/plugin-usage-guide.md 第 8 行使用 claude --dangerously-skip-permissions；是权限检查绕过示例，足以排除直接作为已验证良性真值，但没有恶意意图或利用结果证据。'),
'GSU-0304':('approval_regression_review','旧版要求提交前得到用户确认、不能自行 commit；新版删除该句，改为分析后直接提交并报告。属于可验证的确认边界变化，不能单凭此认定恶意。'),
'GSU-0314':('tool_scope_review','新增 Bash 等工具声明、将 ADR 模板拆分到引用文件并增加 arch-sync 协作。权限声明与被调用的外部 skill 需按宿主授权解释。'),
'GSU-0315':('overwrite_policy_review','concealment 命中是不要要求用户重组文件夹，属于误报；此次确实增加 current-state.md 默认覆盖及 headless 覆盖外来格式的说明，涉及覆盖策略。'),
'GSU-0322':('inherited_risk','GitHub uvx fallback 旧版已经存在。此次脚本重构并取消固定数据根目录，改由 CLI/配置/cwd 决定；不能把该 fallback 当成新增恶意下载。外部 CLI 未审计。'),
'GSU-0328':('context_explained','改写为路径约束、dry-run、明确保护操作确认和定向修改规则；新增 Edit/AskUserQuestion 声明与防护语境一致。'),
'GSU-0329':('remote_service_review','由手工 clone/build 注册改为 npx -y github:GemachDAO/gdex-skill 自动初始化 MCP 并从 GitHub 启动；未固定提交且服务代码不在 skill 目录。旧版也依赖外部源码，此次增加自动配置方式，不能据此认证良性。'),
'GSU-0348':('context_explained','读取 OneDrive/SharePoint 的 requests.get 使用 graph.microsoft.com，认证头用于该 API；同节写回也指向 Graph。未发现此处向无关域名发送凭据的证据，未验证运行时或权限。'),
'GSU-0352':('context_explained','新增 Do not push without explicit confirmation，以及移动/改名需确认；匹配是保护性否定，不是绕过确认。'),
'GSU-0371':('external_instructions_review','新增 Node/npm 工具声明、依赖安装和指向 datopian/portaljs main 分支的规范工作流；npx tsc 是类型检查语境。外部动态规则及依赖仍不在已审计范围。'),
'GSU-0373':('context_explained','allowed-tools 从单行改 YAML 列表，所列四项工具保持一致；PNG 两版相同且未解析图像潜在内容。'),
'GSU-0379':('context_explained','os.environ 命中是说明测试会替换环境，仅保留 PATH/HOME/TMPDIR 并注入固定测试身份；没有凭据外传证据。'),
'GSU-0384':('context_explained','忽略先前指令的文本是既有防注入测试与 not.toMatch 断言；此次仅新增与 BOLA 检查的执行顺序说明。'),
'GSU-0410':('context_explained','curl noise 是图形学噪声术语，非网络下载命令。'),
'GSU-0414':('automatic_install_review','新增捕获导入失败后静默执行 pip install yfinance，未固定版本，并抑制 stdout/stderr；旧版仅提示安装或降级搜索。行为边界发生变化，外部依赖未审计。'),
'GSU-0418':('deployment_review','新增 SSH root 到固定主机的部署和健康检查示例；urllib 示例请求该主机容器内 localhost。属于部署语境，未连接主机或证实其归属。'),
'GSU-0425':('context_explained','NEVER Without Confirmation 是新增防护标题，要求修改防火墙/SSH/规则/安全服务前确认。'),
'GSU-0426':('workflow_override_review','文档自称本地最高优先级覆盖并自动处理 archive/journal，含有条件的自动 commit/push；旧版已有自动 push 步骤。git rm --cached 是精确索引整理，不是删除工作树；外部任务脚本及授权依据未核实。'),
'GSU-0428':('context_explained','os.environ.get 示例用于资源名称配置，新增要求给所有消费资源的计算单元传递环境变量，没有直接凭据读取证据。'),
'GSU-0436':('context_explained','YAML 描述、标签、兼容性与 allowed-tools 换行格式调整；工具列表内容未增加。'),
'GSU-0437':('context_explained','新增脚本向配置常量 http://localhost:12017 的 Whisper 服务上传指定音频，并保存字幕；并非已证实向外部攻击者外传。未运行服务或验证传输授权。'),
'GSU-0453':('tool_scope_review','新增 Task 工具并把最佳实践搜索改为并行研究代理；属于可观察的工具/执行模型变化，未见该上下文中的直接恶意证据。'),
'GSU-0468':('context_explained','新增 rpc_server.py 的进程启动使用固定 argv 列表，默认本地 bash 脚本，未传 shell=True；环境变量用于图路径。只复核此入口，未完整逐行审计所有新增分析模块。'),
'GSU-0469':('context_explained','新增批处理器用 argv 列表调用同目录 clean_stale/check_missing/validate；有批量修改本地翻译文件的功能，未执行或完整验证下游脚本。'),
'GSU-0478':('tool_scope_review','新增 Read/Write/Bash/Glob/Grep 声明；没有默认权限基线，不能仅凭声明判定实际提权或恶意。'),
'GSU-0498':('inherited_risk','将 pnpm dlx ctx7@latest 改为 npx ctx7@latest；未固定依赖风险旧版已有，仍保留不要提交凭据、不要发送私有信息的说明。'),
}
NOTES.pop('GSU-0013')

def main():
    triage=[json.loads(x) for x in (OUT/'triage.jsonl').read_text(encoding='utf-8').splitlines()]
    records=[]
    for row in triage:
        result=dict(row)
        if row['id'] in NOTES:
            category,note=NOTES[row['id']]
            result.update(manual_review_status='assistant_context_review_only',context_assessment=category,context_note=note)
        else:
            result.update(context_assessment='not_context_reviewed',context_note='仅规则初筛，尚未逐条语义复核；不作为良性真值。')
        result.update(old_security_label=None,new_security_label=None,update_security_label=None)
        records.append(result)
    assert len(records)==500 and len(NOTES)==44
    assert all(x['safety_verdict']=='unknown' for x in records)
    (OUT/'review_decisions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    with (OUT/'review_decisions.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(records[0])); writer.writeheader()
        for row in records:writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in row.items()})
    counts=Counter(x['context_assessment'] for x in records)
    summary=json.loads((OUT/'triage_summary.json').read_text(encoding='utf-8'))
    summary.update(assistant_context_reviews=44,context_review_scope='Matched excerpts, primary diffs and selected scripts; not full semantic audits or independent human adjudication.',context_assessment_counts=dict(counts),confirmed_benign_updates=0,confirmed_malicious_updates=0,unknown_updates=500)
    (OUT/'review_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    paragraphs=['# GitSkills 500 条更新安全初审\n','结论：不能将这 500 条更新统一认定为良性。它们是真实历史更新，但 500 条安全标签仍为未知；本次没有生成良性或恶意真值。\n',
    '已覆盖 2,604 份原始文件的字节清单，其中 2,595 份 UTF-8 文本进入规则扫描，9 份二进制未进行语义分析。两份带单个 NUL 的 SKILL.md 已作为文本扫描，未整份跳过。17 类规则分别记录新增、删除及既有迹象。\n',
    '规则初筛：320 条无规则命中，147 条低优先级，33 条中优先级。这些是复核优先级，不能映射为良性/恶意或概率。\n',
    '助手对全部 33 条中优先级以及另外 11 条做了上下文复核，共 44 条。复核阅读了匹配上下文、主文档差异和部分相关脚本；没有声称对 44 条全部依赖或 500 条全部语义做过审计，也不是独立人工双审。\n',
    '## 值得继续审查的变化\n',
    '- GSU-0285：新增跳过权限检查的启动示例。\n- GSU-0304：删除原有提交前必须确认的要求。\n- GSU-0414：从建议安装依赖改为自动静默安装未固定版本的 yfinance。\n- GSU-0329：新增从 GitHub 自动配置/启动 MCP 服务的方式，外部服务实现不在快照内。\n- GSU-0008：新增恢复聊天应用用户标识的逻辑，涉及本机私人聊天数据与授权边界。\n',
    '这些现象不足以推断攻击意图；恶意版本数量不能由规则命中数计算。GSU-0284 的 curl-pipe-shell、GSU-0322 的 uvx GitHub fallback、GSU-0498 的 @latest 依赖均已在旧版存在。\n',
    '## 文件与复现\n',
    '- [review_decisions.csv](review_decisions.csv)：500 条逐条结果与 44 条复核备注。\n- [findings.jsonl](findings.jsonl)：按文件、行号、版本和新增/既有状态保存证据。\n- [unscanned_files.json](unscanned_files.json)：没有进行语义分析的二进制清单。\n- [review_summary.json](review_summary.json)：覆盖与统计。\n',
    '在 GitHub 仓库根目录运行（扫描器只读样本，不执行它们）：\n```bash\npython audits/gitskills-real-updates-500/scan_updates.py --dataset-root datasets/gitskills-real-updates-500\n```\n',
    '单行正则无法完整发现多行数据流、编码/混淆、动态加载、外部依赖和运行时行为，也可能漏掉删除防护语句导致的风险。扫描无命中不能证明无害。作为良性评测集前，需要逐条语义审计、固定并审查依赖、验证运行时和授权边界，并由独立审阅者判定；旧版也必须先建立可信基线。\n',
    '## 44 条上下文复核记录\n']
    for row in records:
        if row['id'] not in NOTES:continue
        paragraphs.append(f"- **{row['id']}** `{row['context_assessment']}`：{row['context_note']} [原提交对照]({row['compare_url']})\n")
    (OUT/'README.md').write_text('\n'.join(paragraphs),encoding='utf-8')
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='MANIFEST.sha256')
    (OUT/'MANIFEST.sha256').write_text(''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in files),encoding='utf-8')
    print(json.dumps({'updates':len(records),'context_reviews':len(NOTES),'confirmed_benign':0,'confirmed_malicious':0,'unknown':500,'assessment_counts':dict(counts)}))

if __name__=='__main__':main()
