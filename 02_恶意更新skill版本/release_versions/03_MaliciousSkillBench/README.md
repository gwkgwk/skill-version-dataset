[返回仓库首页](../../../README.md)

# 两个基准的真实恶意收录 Skill 版本追溯

本批新增 **6 个不同 Skill、6 对真实内容更新、12 份完整快照**。与已有 18 个有版本更新的 Skill 去重后，共 24 个。这里的“恶意”采用来源基准的收录标签；不等于采集者独立确认恶意意图，也不等于本次更新首次引入恶意行为。

| Skill | 旧版 → 新版 | MaliciousSkillBench ID |
|---|---|---|
| abdullah4ai/openclaw-watchdog | 1.0.5 → 1.1.2 | ASB04_004950 |
| c-goro/skillguard | 0.2.2 → 1.0.1 | ASB04_002179 |
| cgnl/nano-banana-antigravity | 1.0.0 → 1.1.0 | ASB04_003082 |
| orlyjamie/wed | 1.0.2 → 1.0.3 | ASB04_003932 |
| seyhunak/deep-research | 1.0.0 → 1.0.1 | ASB04_003548 |
| zadahmed/nervepay | 1.0.0 → 1.2.0 | ASB04_002949 |

## 来源和收录要求

- [MaliciousSkillBench](https://github.com/protectskills/MaliciousSkillBench/tree/893afd609be22a2dfac5a2b94bbebb4eeb99515e) 固定提交 `893afd609be22a2dfac5a2b94bbebb4eeb99515e`。6 个结果均来自该基准 SRC004 / SkillLeakBench 的恶意标签，原始快照保留 wild 来源类别，未脱敏及未过滤。
- 恢复来源为 friuns2/openclaw-removed-skills 的保留原提交归档。每对旧版为新版提交的精确第一父提交，注册表元数据确认 owner/slug 和不同版本号。
- 新版全部操作文件与基准归档包逐文件 Git blob 相同。只在比对时排除注册表元数据、.DS_Store 和 Python 缓存，统一根主文档大小写；原始快照字节保留。
- 两版完整，至少一个非注册表元数据文件发生变化。保存 Git SHA-1、SHA-256、目录树和提交谱系，生成主文档及整包差异，不运行样本。
- 基准标签适用于收录快照；旧版安全标签和更新对安全标签为 null。**这 6 对均未确认恶意行为首次引入，旧版也未证明良性。**

## SkillLifeBench：0 个新增恶意更新

[数据文档](https://github.com/Tasselszcx/SkillLifeBench/blob/57bc115a56baa483d4f68824d5a9c78f00a265dd/docs/dataset.md) 固定提交 `57bc115a56baa483d4f68824d5a9c78f00a265dd`。99 个 E 类演化场景中，97 个为人工构造或修复后的构造版本对，不能算真实公开恶意版本更新。剩余两个 E-NATIVE 场景来自同一 skill-creator 的安全修复，来源明确标明 historical_incident=false、chronology_direction=safety_improvement。

- [符号链接及路径安全修复](https://github.com/openclaw/openclaw/commit/c275932aa4230fb7a8212fe1b9d2a18424874b3f)：`c06ad38… → c275932…`。
- [排除 VCS 目录](https://github.com/openclaw/openclaw/commit/3bfe990c33b176f42bb58038922bd9124a8c79b6)：`3f64d4a… → 3bfe990…`。

两对均核验第一父提交关系和原始模块 SHA-256（共 8 个版本文件），仅作为安全修复证据保留，不标成恶意 Skill。

## 未计入和去重

MaliciousSkillBench 的 7,505 个恶意身份是静态收录身份总数，不能当作 7,505 个真实版本更新。SRC001 是之前已处理的 MalSkillBench 来源，不重复增加数量；本次复核其 3,426 个静态包的归档目录，没有发现 `_meta.json` 历史元数据，没有提取或重试受拦截的 Skill 正文。另审阅其余 10 个源码归档的文件清单、来源类别与注册表元数据。

32 条原生注册表记录中，6 条通过，20 条缺少可恢复的父版本，6 条收录包与归档包不同。后 26 条保存在 [unverified/registry_records.json](unverified/registry_records.json)，不计入正式更新集。其余注入、合成和测试变体不当作公开发布历史；来源 URL 或名称本身不证明历史包身份。3 个原仓库查询返回 404，分别记录在 unverified/，没有把内部参考链接或依赖链接强行认作原仓库。

## 文件入口

- [updates_index.csv](updates_index.csv)、[updates.jsonl](updates.jsonl)：6 对版本索引。
- pairs/MSCU-0001/ 等：old/、new/、SKILL.diff、package.diff、Git 树、父提交、基准标签与文件比对证据。
- [summary.json](summary.json)、[verification_report.json](verification_report.json)：统计与离线校验。
- audit/：候选处理、来源分类、原生安全修复与去重记录；source/：固定版本原始元数据与清单。source/ 中的 SRC004 原始归档用于离线来源核验，其中其他单快照不计入正式 6 对更新。

校验：`python verify_dataset.py`。只读文件，不安装或执行 Skill。第三方内容保留其原作者权利及许可。
