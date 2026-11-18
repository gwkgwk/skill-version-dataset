# `paper_crop`：从论文 PDF 截原图/表（完整说明）

把论文 PDF 里某张图/表裁成 slide 用 PNG。**只用 `pdftoppm`(渲染) + PIL(裁剪/去白边)**——
不用 ImageMagick，也别用 `pdfcrop`（它只裁整页 PDF 边距，分不开图与同页的 caption/正文）。

---

## 标准 recipe（任意论文图通用）

```bash
# 1. 数页数 + 按 caption 唯一短语定位图所在页
pdfinfo papers/PAPER.pdf | grep Pages
for p in $(seq 1 NPAGES); do
  pdftotext -f $p -l $p papers/PAPER.pdf - 2>/dev/null | grep -q "唯一 caption 短语" && echo "page $p"
done
# 2. 该页渲成高 DPI PNG（300 是甜点。pdftoppm 零填充页号：-f 4 → fig-p-04.png，用 /tmp/<ref>-p* 通配）
pdftoppm -png -r 300 -f P -l P papers/PAPER.pdf /tmp/<ref>-p
# 3. 行密度分离 图↔caption，裁剪 + 阈值去白边（PIL+numpy）
uv run --with pillow --with numpy python - <<'PY'
from PIL import Image, ImageChops; import numpy as np
im=Image.open('/tmp/<ref>-p-0P.png').convert('RGB'); g=np.array(im.convert('L'))
dens=(g<250).sum(axis=1)            # 每行暗像素数：图=连续密集块，density-0 的 gap 之后才是 caption
# 看 dens>3 的行段定出图的上下界 Y0,Y1（图块结束 → 密度 0 gap → caption 开始 = 断点）
band=(g[Y0:Y1]<250); xs=np.where(band.any(axis=0))[0]; X0,X1=xs.min(),xs.max()
crop=im.crop((X0-10,Y0-10,X1+10,Y1+10))
d=np.array(ImageChops.difference(crop,Image.new('RGB',crop.size,(255,255,255))).convert('L'))
ys,xs=np.where(d>8); crop.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1)).save('imgs/OUT.png')
PY
# 4. Read imgs/OUT.png 亲眼核 must_show + 字够大
```

并发时**每图用唯一 `/tmp/<ref>-p` 前缀**，别和兄弟 agent 撞名。

---

## 1 · 定位页（caption grep）

- **grep 一个有辨识度的多词 caption 短语**，别 grep 光秃秃的 "Figure 2"——正文里常有对图的交叉引用（"as shown in Figure 2"），裸编号会匹配到错误的页/位置。
- per-page 的 grep 循环**最后一次迭代退出码非 0**（最后那个 `grep` 没命中）是**正常的**，即使它前面已正确打印了目标页——别当失败。

## 2 · DPI 阶梯（清晰度）

- **300 DPI 是甜点**：满文字宽的图裁出约 1900px，slide ~10cm 宽 ≈ 480 effective DPI，最小公式/下标都清晰；150 DPI 缩放后会糊。
- **密集多面板图 → 400 DPI**（如 7 面板：300 下只 ~1742px、字软；400 → ~2324px 锐利）。
- **单独抠一个窄子面板（300 DPI 下 < ~600px）→ 600 DPI**：**复用同一裁框、guide 坐标 ×2 重渲**即可（如某 L 子面板 300 下仅 452px → 600 下 902px）。
- 升 DPI 前先**收紧裁框到核心面板**；裁框收到位仍发虚才提 DPI。

## 3 · 多图同页消歧（最高频失败类）

一页常不止一个图/表，"从上往下第一个密集块"经常**不是**目标图：
- **Table 在 Figure 上方 / 另一个 Figure 在下方**：第一个密集块可能是表，不是目标图。
- **稳健做法：裁出几条不同的竖向子带、逐条 `Read`**，确认哪些密集行真属于目标图，再定最终裁框。别一刀切。
- **L/R 双面板图**：按面板间**全零密度的竖向 gutter** 切，只留要的那侧（不是按中点）。
- **N 面板 teaser**：面板数可能比你以为的多（3 个蓝框而非 2 个）；面板间只隔**一条窄白通道**时要当**一个框**整体保留（合并所有面板的水平范围），别切开。
- 口诀：**独立图之间的 gutter = 切；同一图各面板之间的 channel = 留**。

## 4 · 图 ↔ caption 分界（行密度的细节）

- 图常在**页顶**、caption 在**下方**且图上方没印图号——此时第一个密集块就是图，切它**下方**的 gap。
- **(a)/(b) 子标签、底部花括号标注（"pre-loop / loop window g / post-loop"）在图块内**，与图之间只隔**一条细 gap**；真正的图/caption 分界是**更靠下的大空白带**。按**第一个** gap 切会切掉这些合法子标签——要找更靠下的大空白带。
- **booktabs 表格**：`\midrule`/`\bottomrule` 渲染成全宽暗线，全页密度扫会被邻表的 rule 误导；把行密度**限制在左侧标签列（~300–1100px）**再找最后一行数据下方的 bottomrule。
- **image-grid 的抗锯齿底边**会读出 ~低非零密度，别误当成 subcaption（真 subcaption 更靠下）。

## 5 · 彩色面板 / 边框检测

- 面板边框是**彩色**（蓝色圆角框）时，灰度 `<250` 列扫可能找错分界、或抓到无关的页边元素。改用**蓝像素竖线检测** `B>120 & B-R>40 & B-G>40` 定真边界。
- 图块**最外侧的高密度列通常是面板边框**，不是页面伪影——保留别裁。
- **淡化/灰显元素**（虚线框、alpha 混合层）仍高于 `<250` 阈值会被保留——别把阈值提太高把它们裁没。

## 6 · 阈值与去白边

- 两处阈值：内容掩膜 `<250`、去白边 diff `>8`（>8 才能去掉抗锯齿灰晕；纯 `ImageChops` 去白会欠裁留灰边）。

## 7 · 环境（几乎每个 agent 都会踩）

- **别假设系统 `python3` 有 numpy / PIL / yaml**：homebrew python3 通常都没有，且 `pip` 被 PEP-668 拦。一律 `uv run --with pillow --with numpy python -`（或一次性 venv）。
- 解析 `outline.yaml` 时若没 yaml 模块，直接读行段，或 `uv run --with pyyaml`。
- 退路：只有 PIL 没 numpy 时，可用纯 PIL `px[x,y]` 像素循环算行/列密度。

## 8 · 验收铁律

- 永远 `Read` 存好的 PNG，逐条核 `must_show`，并**脑补 slide 缩放**（300 DPI 满宽图 ≈ 1900px ≈ 10cm 上可读）。
- 最小标签发虚 → 先收紧裁框到核心，不够再提 DPI。
- **输出路径要精确，别碰别的文件**。
- `pdfcrop` 只能裁整页边距，分不开同页的图与 caption/正文——像素级 PIL 才是"一页里抠一张图"的对工具。
