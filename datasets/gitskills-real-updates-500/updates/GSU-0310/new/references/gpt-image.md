# GPT-Image-2 使用指南（找图来源 `source: gpt_image`）

> 下方 API schema 对齐 OpenAI 官方 imagegen skill
> （权威参考：`~/.codex/skills/.system/imagegen/references/image-api.md` 与 `cli.md`）。

## 一句话定位

意思丰富的插图/流程图首选之一；当 `web` / `plot` / `tikz` 反复搞不定时求助于它。
**唯一缺点是贵**——所以不要默认用它，能用 paper_crop/tikz/plot 解决的就别开。

## 能力与特性

- **几乎没有短板**：与传统图像模型不同，它**几乎不会把文字写错**。
- 内置一个 **GPT-4o**：世界知识偏旧，但**专门训练过平面设计审美**，版式排布通常很好看。
- **会自己补全内容**：描述模糊时，GPT-4o 会用自己的知识把文字/元素补上——这是双刃剑：
  既省事，也可能加进你不想要的字。**要精确控制文字时必须显式约束**（见模板）。
- **风格一致性很好**：给一个风格描述（"现代风格""扁平插画"等），整图风格统一。
- **能读伪代码/源码画流程图**：可直接把一段伪代码、甚至**一整个 Python 源文件**丢给它画成流程图。
- 版式它**自己会想**（且通常很好，因为专门训练过），也可以外部指定。

## 常用提示词模板（duanyll 惯用）

```
请你帮我制作一幅用于 PPT 的插图，白色背景，现代风格，展示下面给定的内容，
只包含我提供给你的文字（防止你自己加字）：

<这里直接给一小段 Markdown 格式的大纲 / 伪代码 / 源码>
```

- 「白色背景」→ 贴 beamer 白底不突兀。
- 「现代风格」可替换为任意风格描述，一致性好。
- 「只包含我提供的文字」这句 **load-bearing**：不仅给定文字，还要**逐条列出允许出现的全部文字串**，并**明确禁止**其它文字/数字/水印/坐标刻度/字母——否则模型会自加 "CPU"/"memory"/坐标 tick 等"看着合理"的标签。
- **要流程图就明说"画成流程图"**（圆角矩形=步骤、菱形=判断、回环箭头=循环），把伪代码给它让它**构图**；只给代码不说"流程图"，它会当 lstlisting 抄成代码清单。
- 中文斜杠标签（`emb / 编码`、`lmhead / 解码`）必须**逐字照抄**进 prompt——能渲对正因为你照抄了；重试时也一字不差。
- 想自己定版式就在提示词里加版式要求；不加则用它自带的（通常够好）。

## 何时选它

- 表达的意思**信息量大 / 概念抽象**，文字描述比画图省力。
- `web` 找不到合适的、`plot`/`tikz` 试了几轮仍不理想。
- 需要"一张好看的概念插画"而非精确数据图（数据图用 `plot`）。

## 验收（与其它来源一样，必须亲眼看）

- **核文字要裁文字带放大看**：整图 1024/1536px 太小、缩略图看不清标签——裁出文字所在横带、放大后逐字核。文字带**不一定在底部**（可能在 0.6–0.8 高度），第一次裁到空白就**往上**重裁。
- 伪代码/含符号的图里，**下划线 `_`、`<`、`→`** 是最易丢/串的 token，逐字符核；给文字留**右边距**避免贴边。
- 文字是否**完全是给定内容**、没加字/改字；风格/配色贴合白底；分辨率够清晰。
- 不达标：调紧提示词（更明确的文字约束/版式）重试，或换来源。

## 用 edit 端点重绘 / 合成已有图（`source: gpt_image`，由一张粗糙图改良）

除了从文字生成，`gen-image.py` 也支持 **edit 端点**——把一张**意思正确但质量差**的图
（低清截图、带水印、风格不统一、混入无关元素）丢给它，要求**重绘成干净统一的幻灯片风格**。
实测有效：一张带"知乎"水印、还粘了无关小图的对比学习示意图，一句"重绘成白底现代风、保留这两句中文、
禁止水印/其它文字"，就还回了干净版（见 contrastive 帧）。

```bash
# 重绘单张：原图 + “redraw in clean slide style, keep content” 提示
python3 tools/gen-image.py <prompt-file> <out.png> --edit rough.png [--quality high]
# 合成多张（gpt-image-2 最多 16 张）：
python3 tools/gen-image.py <prompt-file> <out.png> --edit a.png b.png c.png
# 局部重绘：透明处才重画
python3 tools/gen-image.py <prompt-file> <out.png> --edit base.png --mask mask.png
```

要点（沿用上面的文字约束纪律，改图时更要收紧）：
- prompt 里**重复"只改 X、保持 Y 不变"**减少漂移；**逐字列出允许保留的全部文字**，并**显式禁止水印/logo/用户名/无关元素**——
  否则原图的水印或杂物会被"忠实"地一起重绘进去。
- 想去掉原图里的某块（如粘在一起的另一张子图），就**明说"删除右侧的 X 小图"**。
- `gpt-image-2` 恒高保真，**不要传 `--input-fidelity`**（那只给 gpt-image-1/1.5/-mini）。
- 先 `--quality low` 验证构图与文字对不对，满意再 `--quality high` 出终图。

## 调用方式（API schema）

本仓库用 `tools/gen-image.py <prompt-file> <out.png> [--model] [--size] [--quality] [--edit IMG... ] [--mask PNG]`——读 `.env` 的
`OPENAI_BASE`/`OPENAI_KEY`（OpenAI 兼容 relay）。无 `--edit` 打 `/images/generations`（JSON）；带 `--edit` 打
`/images/edits`（multipart 上传输入图），都把返回的 `b64_json` 解码存盘。纯 `python3`（stdlib urllib，multipart 手搓），无额外依赖。
（官方 codex skill 的 `image_gen.py` 是另一条路：走 `OPENAI_API_KEY` + openai SDK，schema 同下。）

> **并发信号量（重要）**：`gen-image.py` 用 **flock 跨进程信号量**把命中 relay 的并发压到
> `.env` 的 `OPENAI_CONCURRENCY_LIMIT`（默认 3，relay key 扛不住高并发）。看到
> **`all 3 slots busy; waiting`** 是**正常排队**，不是错误——给 **~600000ms 超时耐心等**，
> 别重试/杀进程。workflow 里一次铺开 7 张也安全：工具层自动把总并发卡在 3。

**端点**
- 生成：`POST /v1/images/generations`（`client.images.generate`）。
- 编辑/合成：`POST /v1/images/edits`（`client.images.edit`）——传 `image`（gpt-image-2 最多 16 张）+ 可选 `mask`，
  用来"在已有图上改一处""把几张图合成一张"。改图时在 prompt 里**重复"只改 X、保持 Y 不变"**减少漂移。

**模型**（都以 `gpt-image-` 开头）
| 模型 | 用途 |
|---|---|
| `gpt-image-2` | **默认**。质量最好、密集文字/图表强、图像输入恒高保真。做 PPT 插图就用它 |
| `gpt-image-1.5` | 需要**原生透明背景**时的回退（见下） |
| `gpt-image-1` / `-mini` | legacy / 便宜草稿 |

**参数**
- `prompt`、`model`、`n`(1–10)、`quality`(`low`/`medium`/`high`/`auto`)、`output_format`(`png` 默认 /`jpeg`/`webp`)、
  `output_compression`(0–100，仅 jpeg/webp)、`moderation`(`auto`/`low`)、`background`(`transparent`/`opaque`/`auto`)。
- `size`：gpt-image-2 支持 `auto` 或**任意 WxH**，需满足：最长边 ≤3840、长宽都是 **16 的倍数**、长短边比 ≤3:1、
  总像素 65.5万–829万（>2560×1440 实验性）。常用 `1024x1024`/`1536x1024`(横)/`1024x1536`(竖)/`2048x1152`/`3840x2160`/`auto`。
  legacy 模型只认 `1024x1024`/`1536x1024`/`1024x1536`/`auto`。
- **质量取舍**：草稿/缩略 `low`；**终图、密集文字、图表/示意图、高分辨率用 `medium`/`high`**（PPT 插图我们用 `high`）。
- **编辑专用**：`input_fidelity`(`low`/`high`)——**只对 gpt-image-1/1.5/-mini**，gpt-image-2 恒高保真**不要传**；`mask` 仅 edit。

**透明背景**：gpt-image-2 **不支持** API 的 `background=transparent`。要原生透明 → 用 `gpt-image-1.5` + `background=transparent` + `png/webp`；
或在 gpt-image-2 上画**纯色背景**再本地抠图。一般 PPT 插图用白底即可，不需要透明。

**返回 / 花费 / key 坑**
- 返回 `data[]`，每张取 `b64_json` 解码。
- 按 token 计费：high 1536×1024 ≈ 几千 image-token（一张几美分）；测试先用 `low`。慢，一张几分钟。
- **rate limit 比文本严**：并发别超 ~3，否则 429。
- key 排错（relay 实测）：`This token has no access to model X` = key 按模型授权（图像 key 调 chat 模型会这样，正常，直接用 gpt-image-2）；
  `Invalid token` = key 失效/写错，让用户更新 `.env`。探活：发个 `--max-time 14` 的小请求，**超时(在生成)=鉴权通过**。

**留档**：每张图的 prompt 存到 `<out>.prompt.txt`，可复现、可微调。
