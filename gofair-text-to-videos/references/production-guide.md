# 文案成片 · 生产指南（页面推镜版管线）

本文档是 SKILL.md 工作流的详细展开。所有命令在 Windows Git Bash 环境验证过（2026-11，v18 版模板）。

## 0. 依赖

- Node.js + `npm i playwright && npx playwright install chromium`
- Python 3 + `pip install edge-tts`
- ffmpeg（PATH 可用）

## 1. 工作区结构（复制 assets/template 后）

```
项目/
├── render-p.js              # 逐帧渲染器（playwright 截图 + 子帧混帧）
├── package.json             # playwright 依赖
├── lib/core.js              # Reel 场景引擎（spring/lerp/缓动 + __seek/__duration）
├── geo-pagecam/index.html   # 页面推镜版场景模板（v18 深色系，1080×1920）
├── geo-scene/captions.js    # 字幕数据 window.CAPTIONS=[{s,e,text},...]
├── geo-cover/cover.html     # 封面排版模板
├── assets/audio/            # voiceover.mp3 / subtitle.srt / bgm
└── out/                     # 帧缓存与成片
```

## 2. 配音（gen_voiceover.py）

```bash
python scripts/gen_voiceover.py --script 文案.txt --out-dir assets/audio --rate "+31%" [--fix 读音修正.txt]
```

- 音色 `zh-CN-YunjianNeural`（云健），pitch -2Hz；语速默认 +31%
- 文案预处理（脚本内置，2026-11 用户试听定稿）：`SEO→S E O`（S 读"艾斯"节奏自然）、`GEO→记 E 欧`（G 直接读会断成"GE..O"，谐音"记"最顺滑）、`AI` 不处理（本就读"爱"，拆开生硬）、`DeepSeek→Deep Seek`（按单词连读），写 SRT 时自动还原为正常写法
- `--fix` 文件每行一条 `错读字=谐音字`（如 `同行=同航`），SRT 输出还原为错读字
- 输出：`voiceover.mp3`、`subtitle.srt`，stdout 打印 `sentences=N last_end=XX.XXs` —— **场景 duration 必须用这个总时长**
- 若文案修改导致句子数变化：新 SRT 与旧场景时间轴按"文本相同→时间平移；新增句→取新句时间"重映射（参考 resync 思路：章节级 delta，逐组替换带计数断言，防止多行替换漏移）

## 3. 字幕（srt_to_captions.py）

```bash
python scripts/srt_to_captions.py assets/audio/subtitle.srt geo-scene/captions.js
```

生成 `window.CAPTIONS = [{"s":..,"e":..,"text":".."}]`。关键词高亮在 geo-pagecam/index.html 的 `KW = /(GEO|SEO|AI|DeepSeek)/g` 正则里，按新文案主题改。

## 4. 场景搭建（geo-pagecam/index.html）

### 4.1 布局几何（v19 定稿，勿随意改动）

| 元素 | 值 | 说明 |
|---|---|---|
| 画布 | 1080×1920 | 竖屏 |
| 顶部字幕带 | y **240~346** | 下移定稿（2026-11）：抖音状态栏 ~66 + 搜索/标签栏 ~120 挡住旧 92 位置，整体下移 148px；基础字号 28；超长句**按标点符号换行**成两行（splitClauses 在 ，。！？、；：…— 后切句，整个子句放不下才整体移下行，单子句超宽才逐字兜底），行宽上限 maxW=840；纯描边框（无底色，rgba(140,170,255,.55) 3px 圆角20）+ 文字投影 |
| 浏览器窗口 #win | left 27, top 238, w 1026, h 1480 | WIN_SCALE=0.84，transform-origin 50% 0（**旧值**；页面推镜版若再启用需按新字幕带重算 top） |
| 窗口视觉底边 | ≈238+1480×0.84≈1481 | 抖音标题遮挡区约 1500 起 |
| 字幕带↔窗口间距 | ≥40px | 两行字幕时 |
| 底部 | 1500 以下不放关键内容 | 抖音标题/文案/右侧按钮栏 |

改动任何几何后必须重新核算：窗口视觉底 = top + height×WIN_SCALE ≤ 1483；字幕带最底（两行 ≈346）+ 40 < 内容 top。

### 4.2 场景脚本结构

- `CH` 数组：章节 `{t0, t1, name}`，边界 = SRT 对应句的起始时间；总时长 = 配音 last_end
- `SH = 1520`：每屏高度；`#view` 高 1416（窗口 1480 - chrome 64）；每屏内容做到 ~1400px 内
- `add(html, css, t0, opt)`：元素逐张浮出；t0 对齐该内容对应字幕句的 s 值；opt.z 推镜深度、dy 浮出距离
- `scrollAt(t)`：章节切换时页面上滑一屏（1.05s inOutCubic）
- 结尾固定三件套：身份卡、关注卡、订阅按钮（光标点击 + 已订阅弹跳）、"咱们下期，再见！"渐变字
- 主题色：舞台 radial #1c2a5e→#060a1e、窗口 #0d1226、卡片 #141d3c、文字 #f2f6ff/#93a2c8、主色 #4f7cff/#8a5cff、关键词 #7ea6ff

### 4.3 内容组件化要求（用户硬性要求，每次必做）

**A. 组件丰富多样（≥5 种类型/全片，一屏混用 2~3 种）**

| 组件类型 | 适用内容 | 样式要点 |
|---|---|---|
| 数字大卡 | 关键数据（提升率/成本/时长） | 数字 80~120px 主色渐变，下方小注灰字 |
| 对比双栏卡 | 前后对比 / A vs B | 左右两栏 + 中间 VS 圆徽，败方降饱和 |
| 清单勾选卡 | 要点/步骤列表 | 每行前 ✓ 图标逐条浮出，错峰 0.4s |
| 金句引用条 | 核心结论/口号 | 左侧竖色条 + 大字一行，轻微光效 |
| 标签/徽章组 | 关键词群、能力项 | 圆角胶囊错落排布，逐个弹入 |
| 图标+短语句 | 功能/卖点 | 圆底图标 + 1 行短句，2×2 或横向排 |
| 时间线/步骤条 | 流程、方法论 | 竖向节点连线，节点依次点亮 |
| 仪表/进度件 | 占比、达成度 | 弧形/条形进度，动画增长 |

- 主题色沿用 v19（#4f7cff/#8a5cff 主色、#7ea6ff 关键词、卡片 #141d3c），可按文案调性新增 1 个强调色，全片 ≤3 色
- 高级感手法：卡片微渐变+1px 高光描边、圆角统一（16~24px）、阴影柔和、留白 ≥30%、标题层级分明（大字主标 + 小字灰注）

**B. 动效要求（每个组件必须带）**

- 入场动效从这些中选并混用：translateY 浮出上滑、opacity 渐显、scale 缩放弹入（cubic-bezier 回弹）、描边/光效扫过、数字滚动（JS 递增）、勾选打勾动画
- 元素逐张错峰出现：间隔 0.3~0.6s，对齐对应字幕句的 s 值；章节切换已有整屏上滑，不要叠加额外大位移
- 动效时长 0.5~0.8s，用 inOutCubic 类缓动，避免生硬线性

**C. 文字提炼原则（不照抄口播稿）**

- 屏幕文字是**视觉摘要**，逐字内容交给顶部字幕带；每屏 = 多段重点文字（每段 1 行主标 + 1 行小注的量级）
- 提炼方法：划出每句的"重点词/数字/结论"→ 按上表匹配组件 → 多余修饰语全部删掉
- 提炼后仍超宽的文本：缩短而不是缩小字号；每屏宁少勿多，留白 ≥30%
- 静帧目检标准（4.4）：一眼能看到"这屏讲了什么重点"，看不到大段复制口播的整句文字

### 4.4 静帧验证

```bash
node render-p.js geo-pagecam/index.html x --still 5:out/a5.png --still 44:out/a44.png --still 85:out/a85.png --nogpu
```
检查：文字溢出/截断、卡片重叠、字幕与窗口重叠、封面元素完整；**组件多样性达标（一屏 ≥2 种样式、全片 ≥5 种）、无整句照抄口播稿的大段文字**。用 ViewImage 目检。

### 4.5 封面式大字版模板（geo-bigtext/index.html，用户定稿风格）

用户反馈页面推镜版"网页字体太小看不清"后定稿的第二套自有风格：**去掉浏览器窗口，内容直接全屏铺排**，字号为封面级。

**布局几何**：

| 元素 | 值 | 说明 |
|---|---|---|
| 画布 | 1080×1920 | 竖屏 |
| 顶部字幕带 | y **240~346** | 与页面推镜版同规则：下移避开抖音状态栏+搜索条（旧 92 位置被挡） |
| 内容起笔 | y ≥398 | 字幕带两行最底 346 之下留 50px |
| 内容底界 | ≤1500 | 抖音标题遮挡区之上（装饰元素可放宽到 ~1510） |
| 章节 .sec | 每屏 1920 高（SH=1920） | 章节切换整屏上滑 1.05s（scrollAt 与页面推镜版同算法） |
| 背景 | 固定层 | 封面同款：深蓝渐变 #0a0f2c→#131b45→#1a1440 + 三枚光斑（render 中缓漂）+ 90px 网格 + 300px 幽灵 GEO 字 |

**字号体系（封面级，区别于页面推镜版）**：

| 用途 | 字号 |
|---|---|
| 章节大标题 .h2 | 88px（超过 10 字降 74px 防换行溢出） |
| 钩子大标题 | 108px |
| SEO 划线钩子 / GEO 大字 | 172px / 170px（斜体渐变 + drop-shadow） |
| 78% 大数字 | 210px |
| 结论大字 | 60~66px |
| 卡片主文 | 36~46px |
| 小注/说明 | 26~34px |

**内置组件（改文案时保留组件结构、替换文字）**：SEO 划线钩子（strike 线 scaleX 动画 0.9~2.2s）、黄色胶囊 pill-y、芯片 chip、搜索框、搜索结果卡 ×3、AI 对话卡、GEO 定义大字卡（呼吸光晕 drop-shadow 正弦）、VS 对比卡 ×3、78% 数字滚动卡（0→78 计数 + 进度条生长，61~66.2s）、勾选清单 ×3、渐变结论条、订阅按钮（白底呼吸→83.03s 光标点击→红底弹跳 + 光环 + 14 粒子爆发）。

**复用与差异**：字幕 HUD（drawCaption/splitClauses/KW）、CH 时间轴、scrollAt、updateSub 订阅逻辑与 geo-pagecam 完全同源；配音混音可复用同一音轨。改造新文案时：换 CH 时间轴 → 换各屏文字（遵守 4.3 组件化要求，提炼不照抄）→ 对齐元素 t0 → 静帧验证。

## 5. 全量渲染

```bash
node render-p.js geo-pagecam/index.html x --frames out/frames --mb 2 --shutter 0.5 --nogpu
```

（封面式大字版同理：`node render-p.js geo-bigtext/index.html x --frames out/frames-bt --mb 2 --shutter 0.5 --nogpu`，实测 89.4s 约 6 分 45 秒）

- 90s × 30fps ≈ 2682 帧，约 7~10 分钟；`--mb 2` 双子帧 + tmix 混帧出运动模糊
- **已知无害报错**：结尾 `fs.rmSync(_sub)` 在沙箱里可能抛 Node 错误——帧已混好，`ls out/frames/f*.jpg | wc -l` 验证 = duration×fps 即可
- 支持断点续渲（已存在的完整 JPEG 跳过）
- 横屏适配：render-p.js 里 `VW/VH` 硬编码 1080×1920，改为 1920×1080；场景内 stage/#win/字幕带/安全区几何同步重排（抖音横屏安全区：左右两侧留 200px 给互动栏）

## 6. 混音 + 合成 + 封面（一次完成）

### 6.1 混音（人声 + BGM）

BGM 来源（按优先级）：① 用户本次显式给的音频文件；② `python scripts/pick_bgm.py` 从已保存目录随机选一首（首次运行报错退出码 2 时，问用户要目录并用 `--set-dir` 保存，之后长期有效）；选中后复制为 `assets/audio/bgm.mp3` 再混音。

```bash
ffmpeg -y -v error -i assets/audio/voiceover.mp3 -i assets/audio/bgm.mp3 -filter_complex \
  "[1:a]volume=0.08[bg];[0:a][bg]amix=inputs=2:duration=first:normalize=0[out]" \
  -map "[out]" -ar 44100 -ac 2 out/mixed.wav
```

- BGM 0.08 起步（用户偏好：人声明显盖过背景）；需要点缀音（如关注"叮"）再叠一路 `adelay=83030|83030` 的音效，峰值可比人声高 2~3dB
- 混好后分段 volumedetect 验证（`-ss` 放 `-i` 前！）

### 6.2 帧序列 + 音轨 + 封面首帧

```bash
ffmpeg -y -v error -framerate 30 -i out/frames/f%05d.jpg -i out/mixed.wav -loop 1 -framerate 30 -t 1.0 -i "out/封面.png" \
  -filter_complex "[2:v]format=rgba,fade=t=out:st=0.55:d=0.45:alpha=1[ov];[0:v][ov]overlay=0:0:enable='lt(t,1.02)'[v]" \
  -map "[v]" -map 1:a -c:v libx264 -preset medium -crf 15 -pix_fmt yuv420p -movflags +faststart -c:a aac -b:a 192k -shortest out/video.mp4
```

### 6.3 封面写入元数据

```bash
ffmpeg -y -v error -i out/video.mp4 -i "out/封面.png" -map 0 -map 1 -c copy -disposition:v:1 attached_pic out/tmp.mp4 && mv out/tmp.mp4 out/video.mp4
```

### 6.4 预览

```bash
ffmpeg -y -v error -i out/video.mp4 -vf scale=720:1280 -c:v libx264 -preset medium -crf 23 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart out/预览.mp4
```

抽首帧确认封面、抽 0.9s 确认淡出正常。

### 6.5 交付收尾（硬性要求：移动成片到文案目录 + 清空缓存）

**第一步：确定文案目录。** 从用户提供的文案文件路径（如 `D:\video-works\proj1\文案.txt`）取其所在目录作为交付目录。

**第二步：移动交付物**（PowerShell `Move-Item -LiteralPath`，成片文件名建议带视频标题前缀，目标有同名文件时先重命名不覆盖）：

| 文件 | 来源 |
|---|---|
| `<标题>-成片.mp4` | out/video.mp4 |
| `<标题>-预览.mp4` | out/预览.mp4 |
| `<标题>-封面.png` | out/封面.png |
| voiceover.mp3 | assets/audio/voiceover.mp3 |
| subtitle.srt | assets/audio/subtitle.srt |

**第三步：删除全部生成缓存**（逐条 PowerShell `Remove-Item -LiteralPath <路径> -Recurse -Force -Confirm:$false`，不要 rm -rf）：

- `out/frames/`（约 1.2GB 帧缓存，最大头）
- `out/mixed.wav`、`out/video.mp4`（中间产物）、`out/a*.png`（--still 静帧）、`out/预览.mp4`、`out/封面.png`（已移走确认后）
- `assets/audio/demo/`（10 段试听 mp3）
- 配音生成的 `voiceover.mp3`、`subtitle.srt` 原位置（已复制/移走）

**不要删**：工程源文件（geo-pagecam/index.html、geo-scene/captions.js、geo-cover/cover.html、lib/、render-p.js）——保留供下次复用改造；若用户明确不再需要整个项目目录，需经用户确认后才可删。

**第四步**：清理完成后 `present_files`（预览在前、成片在后），并明确告知用户成片现在位于文案所在目录。

## 7. 封面模板（geo-cover/cover.html）

结构：顶部品牌行（@名称 + 右侧小标签）→ 大字标题（可两行）→ 黄色胶囊副题 → 三个内容 chips → 底部居中页脚小字（"AI"青色 #25f4ee 高亮）。深色底 + 大字号（大字 ~150px）。

截图：

```bash
node -e "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch({args:['--disable-gpu','--force-color-profile=srgb']});const p=await b.newPage({viewport:{width:1080,height:1920},deviceScaleFactor:1});await p.goto('file:///'+process.cwd().replace(/\\\\/g,'/')+'/geo-cover/cover.html');await p.waitForTimeout(500);await p.screenshot({path:'out/封面.png',clip:{x:0,y:0,width:1080,height:1920}});await b.close();console.log('ok')})();"
```

排版雷区：孤字换行（缩字号或加 white-space:nowrap）、副标题折行、下划线过长、chips 换行——截图后必须目检一轮。

## 8. 踩坑清单（血泪教训，逐条遵守）

1. **ffmpeg 音频 concat 必须 `a=1`**（`concat=n=3:v=0:a=1`），漏了报 "Input link in0 does not match"
2. **volumedetect 的 `-ss/-t` 必须放 `-i` 之前**，放输出端统计的是全片
3. **一条 ffmpeg 命令多个输出文件时，后续输出默认取输入 0 的流**——抽帧验证逐条独立执行
4. **atrim 语法**：`atrim=0:3.718`（范围）与 `atrim=start=3.718`（起点）写法不同
5. **删帧缓存等大目录**：PowerShell `Remove-Item -LiteralPath <路径> -Recurse -Force -Confirm:$false`；管道 Remove-Item 会被沙箱拦（InputObjectNotBound）
6. **python 批量替换源码**：每条替换带 `count` 断言（`assert s.count(old)==exp`），先长串后短串，防止误替换；多行 add() 调用时收尾行也要核对
7. **批量改时间轴**：所有相对时间表达式（如 `67.23 + i * 1.2`、`(t - 83.03) / 0.7`）都要枚举替换，漏一处就音画错位；替换后全量 grep 旧时间值确认归零
8. **改完 HTML 先 --still 后全量**，永远不要跳过静帧验证
9. **Windows 路径**：Bash 里 ffmpeg -vf 的引号用单引号包裹滤镜，双引号转义易炸
