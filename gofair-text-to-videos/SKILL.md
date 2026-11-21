---
name: gofair-text-to-videos
description: GoFair 文案成片技能——用户只需提供一份口播文案（txt，如"用 @文案.txt 做个视频"），背景音乐可不带：技能从用户预存的 BGM 目录里每次随机挑一首（首次使用时询问目录并长期记住，也可显式给文件覆盖）。本技能先根据文案内容推荐 3~5 种视频风格（从风格库：自有页面推镜版/封面式大字版/大字报 + styles 20 种 + vol2 20 种 + industry 60 条行业片）供用户确认，再让用户从 10 款音色（5 男 5 女）+ 语速 + 感情类型中选择配音并选择画幅，确认后自动解析文案、生成配音与逐句字幕、按所选风格搭建场景、自动制作封面并嵌入视频，最终交付带封面首帧、BGM 混音、字幕完整的成片 mp4 与 720p 预览。触发词：gofair、GoFair 文案成片、文案成片、文案转视频、做个视频、把这个文案做成视频、生成口播视频、脚本转视频、配着背景音乐做视频。
agent_created: true
---

# GoFair Text to Videos（文案成片）

## 概述

把一份口播文案 + 一段背景音乐，变成一条可直接发布的短视频：选音色/感情/语速 → 配音（edge-tts，10 款中文音色）→ 逐句字幕 → 代码渲染场景（DOM+CSS 3D，playwright 逐帧渲染）→ 封面（HTML 排版截图，进视频首帧 + mp4 元数据）→ ffmpeg 混音合成。全流程约 20~30 分钟，产出 1080×1920 成片 + 720p 预览。

## 必需输入

1. **文案文件**（txt）。期望结构（缺哪节就从正文推导）：
   - 【视频标题】【建议时长】【内容定位】
   - 一、前 3 秒钩子（快、狠、直击痛点）
   - 二、口播正文（可按小节分章节）
   - 三、结尾（固定引导：身份介绍 + 点关注 + 下期再见）
   - 【封面文案】大字 + 小字
   - 其余小节（话题标签/发布建议/合规说明）不进配音
2. **背景音乐**（可选）：用户显式给了 mp3/wav 文件就用它；没给则走「BGM 自动选曲」（见 Step 0 前置），从已保存的 BGM 目录随机挑一首

## 工作流

### Step -1 — BGM 自动选曲（用户没给背景音乐时必做）

用户只说"用 @文案.txt 做个视频"而不附 BGM 时，按下面顺序取背景音乐：

1. `python <skill>/scripts/pick_bgm.py`（stdout 直接输出选中的音频绝对路径）
2. **成功**：告诉用户"本次 BGM 随机选了：<文件名>（来自已保存目录）"，继续 Step 0
3. **报错（退出码 2，未设置目录）**：用 AskUserQuestion 或直接问用户要一个**存有多个 mp3 的目录路径**，拿到后执行 `python <skill>/scripts/pick_bgm.py --set-dir <目录>` 保存，再随机选曲；目录路径保存后长期有效，以后不再问
4. **报错（目录里没音频）**：告知用户目录已失效，请提供新目录，`--set-dir` 覆盖保存
5. 用户在某次调用时**显式附了 BGM 文件** → 直接用该文件，跳过本步骤（显式指定优先，不覆盖已保存目录）
6. 可用 `--list` 查看目录里全部可选曲目；`--reset` 清除保存的目录

### Step 0 — 风格推荐 + 配音选项（必做，全部确认后才开始制作）

**第一步：按文案推荐 3~5 种视频风格（必须推荐，不能只给固定两个）**

1. 先通读文案，判断：行业/题材（咖啡？教育？法律？软件？……）、调性（热血带货 / 冷静科普 / 温暖故事 / 幽默）、目标平台
2. 从下面三层风格库中挑出 **3~5 个最匹配的候选**，每个候选附一句"为什么适合这条文案"：
   - **自有风格**（模板自带，开箱即用）：
     - 页面推镜版：模拟浏览器窗口逐屏上滑 + 3D 推镜，适合科普/教程/演示"网页内容"的文案，深色系有冲击力（geo-pagecam，v19 深色主题）
     - **封面式大字版**（用户定稿推荐）：去掉浏览器窗口，全屏封面级大字排版（标题 74~210px），组件丰富（SEO 划线钩子、黄色胶囊、大数字滚动、VS 对比卡、勾选清单、GEO 呼吸光晕、订阅粒子爆发），字号大、手机端清晰易读，适合口播科普/观点输出类文案（geo-bigtext）
     - 大字报字幕版：全屏大字 + 关键词高亮，制作快，适合纯口播
   - **styles/ 通用风格 20 种**（sy-style-100 主仓库 `styles/`）：01-handdrawn 手绘、02-isometric 等距、03-flat 扁平、04-lineart 线稿、05-3d 三维、06-morph 变形、07-sticker 贴纸、08-hud 界面仪表、09-collage 拼贴、10-glass 玻璃、11-bauhaus 包豪斯、12-synthwave 合成波、13-pixel 像素、14-liquid 液态、15-variety 综艺、16-pagecam 页面推镜、17-editorial 杂志排版、18-ink 水墨、19-clay 黏土、20-xxx（看目录）
   - **industry/ 行业广告片 60 条**（`industry/`，每风格 3 个行业）：01a-coffee 咖啡、01b-minsu 民宿、01c-wedding 婚庆、02a-factory 工厂、02b-park 公园、02c-supply 供应链、03a-edu 教育、03b-onboard 入职、03c-app APP、04a-arch 建筑、04b-law 法律、04c-watch 腕表、05a-gummy 糖果、05b-lipstick 口红、05c-blender 小家电、06a-gym 健身、06b-earbuds 耳机、06c-course 课程、07a-clean 保洁、07b-pet 宠物、07c-grocery 生鲜、08a-survey 问卷、08b-security 安防、08c-esports 电竞、09a-bookshop 书店、09b-travel 旅行、09c-kitchen 厨房、10a-beauty 美妆、10b-home 家居、10c-radio 电台……
   - **vol2/ 第二期风格 20 种**（`vol2/`，进目录看）
3. 主仓库路径：`F:\WorkBuddy\2026-11-20-09-57-18\sy-style-100-extract\sy-style-100-main\`（styles / vol2 / industry 都在这里；用 `node make.js still <编号> <秒>` 可出单帧预览）
4. 用 AskUserQuestion 呈现候选（单题最多 4 个选项，第 5 个放"其他"提示）；**建议给每个候选渲染 1~2 张 --still 静帧或用 make.js still 出预览图**，present_files 给用户看过再选
5. **用户确认风格后才能进入下一步**；若选了 styles/vol2/industry 的模板，复制该模板工程到项目目录改造（换文案文字、拉长 duration、按 Step 3 的时间轴方法重排），渲染管线与 Step 5 相同

**第二步：配音三项（音色试听 → 选择）**

1. **配音性别**：男声（5 款）/ 女声（5 款）
2. **音色**（5 位候选见下表）。注意 AskUserQuestion 单题最多 4 个选项：把前 4 位做成选项，第 5 位在题干里注明"选'其他'输入：xxx"。**强烈建议先跑试听**：`python <skill>/scripts/gen_voiceover.py --demo --out-dir assets/audio` 会生成 10 段（男女各 5）试听 mp3，present_files 给用户听完再选；`--demo` 可与 `--emotion` 组合（用同一感情预设试听）
3. **语速**：+31%（默认，信息密度高）或 +0% 正常语速（可自定义，如 +20%）
4. **感情类型**（5 种预设，见下表）
5. **画幅**：竖屏 1080×1920（抖音/视频号，推荐）或 横屏 1920×1080（B站/公众号）

**音色表（男 5 / 女 5，均实测可用；以 `--demo` 试听为准，edge-tts 官方音色列表会变动，若报 NoAudioReceived 就 `edge_tts.list_voices()` 重新核对替换）：**

| 性别 | 音色 | voice 参数 | 特点 |
|---|---|---|---|
| 男 | 云健 | zh-CN-YunjianNeural | 热血激昂、解说感强，科普/数码/带货首选（历史默认） |
| 男 | 云扬 | zh-CN-YunyangNeural | 新闻主播音，专业稳重，财经/行业解读 |
| 男 | 云希 | zh-CN-YunxiNeural | 阳光年轻，语感轻快，生活方式/轻科普 |
| 男 | 云夏 | zh-CN-YunxiaNeural | 少年音、萌系活泼，年轻化人设/搞笑向 |
| 男 | 安德鲁 | en-US-AndrewMultilingualNeural | 磁性暖男，表现力强，中文带轻微外语腔（多语言音色） |
| 女 | 晓晓 | zh-CN-XiaoxiaoNeural | 温暖亲和、全能通用，最稳女声（女声默认） |
| 女 | 晓伊 | zh-CN-XiaoyiNeural | 年轻干练，职场/干货分享 |
| 女 | 晓北 | zh-CN-liaoning-XiaobeiNeural | 东北话，幽默接地气，唠嗑感强 |
| 女 | 晓妮 | zh-CN-shaanxi-XiaoniNeural | 陕西话，明亮大方，地方特色人设 |
| 女 | 艾娃 | en-US-AvaMultilingualNeural | 亲切甜美、表现力丰富，中文带轻微外语腔（多语言音色） |

**感情类型表（5 种预设；edge-tts 不支持 SSML style，感情由 语速偏移+音调+音量 组合模拟，自动叠加在基础语速上）：**

| 感情类型 | 语速偏移 | 音调 | 音量 | 适用 |
|---|---|---|---|---|
| 标准口播 | +0% | -2Hz | +0% | 默认，通用 |
| 激昂热血 | +8% | +4Hz | +8% | 钩子开场、带货、励志 |
| 沉稳叙事 | -4% | -8Hz | -4% | 纪录片感、深度内容 |
| 轻快活泼 | +5% | +8Hz | +4% | 好物、日常、搞笑 |
| 温柔知性 | -2% | +2Hz | +0% | 情感、治愈、女性向 |

例：基础语速 +31% + 感情"激昂热血" → 实际 +39%。

**封面**：有【封面文案】小节则按它做，否则从标题自动提炼大字+小字（无需询问）。

### Step 1 — 初始化工作区

把 `assets/template/` 整个复制到项目目录（保持相对结构：`lib/core.js`、`render-p.js`、`geo-pagecam/index.html`、`geo-bigtext/index.html`、`geo-scene/captions.js`、`geo-cover/cover.html`、`package.json`）。依赖：`npm i playwright && npx playwright install chromium`；python 需 `edge-tts`；系统需 ffmpeg。

### Step 2 — 配音 + 字幕

```
python <skill>/scripts/gen_voiceover.py --script 文案.txt --out-dir assets/audio \
    --voice zh-CN-YunjianNeural --rate "+31%" --emotion 激昂热血 [--fix 读音修正.txt]
python <skill>/scripts/srt_to_captions.py assets/audio/subtitle.srt geo-scene/captions.js
```

- `--voice` 用 Step 0 选的音色、`--emotion` 用选的感情类型、`--rate` 用选的语速（感情语速偏移自动叠加）
- gen_voiceover.py 输出 `voiceover.mp3` + `subtitle.srt`，并打印总时长和句数（场景 duration 用它）
- 谐音字修正（如"同行→同航"）写进 `--fix` 文件（每行 `错读=正读`），SRT 会自动还原回正确文字

### Step 3 — 搭建场景时间轴

按 `references/production-guide.md` 的模板说明操作场景文件（**按 Step 0 选定的风格选文件**：页面推镜版改 `geo-pagecam/index.html`，封面式大字版改 `geo-bigtext/index.html`）：
- **章节 CH**：把正文小节边界对齐到 SRT 句子起始时间
- **每屏元素**：从文案内容生成卡片/标题/列表，出现时间 t0 对齐对应字幕句的 s 值
- **captions.js**：Step 2 已生成，直接可用（关键词高亮正则按文案主题调整）
- 改完先渲染 3~5 张 `--still` 静帧验证布局（溢出/重叠/字幕安全区），再全量渲染

### Step 3.5 — 场景内容创作要求（每次做视频必做，硬性要求）

**要求 1：组件丰富、美观、有高级感，排版好看**

- 整条视频**不得只用一种卡片样式**：一屏之内至少混用 2~3 种不同组件，全片至少出现 5 种以上组件类型（如：数字大卡、对比双栏卡、清单勾选卡、金句引用条、标签/徽章组、仪表/进度件、图标+短语句、时间线/步骤条等，可按文案题材自由设计新样式）
- 每个组件要有**动效/动画**：浮出上滑、渐显、缩放弹入、光效扫过、描边点亮、数字滚动等，元素逐张错峰出现（间隔 0.3~0.6s），不要整屏同时闪现
- 排版要求：对齐统一、间距呼吸感、主次层级分明（大数字/关键词放大、说明文字缩小变灰）、色彩克制（主色+强调色不超过 3 种），体现高级感；静帧目检不达标的排版必须重排

**要求 2：文字内容自行整理提炼，不照抄口播稿**

- **不要把每句话都放上**：屏幕文字是"视觉摘要"，不是配音的逐字稿（逐字内容由顶部字幕带承担）
- 从文案中**提炼重点词、关键数字、金句短句**，一次性可放多段重点文字，但每段控制在 1 行主标题 + 1 行小注的量级
- 同一个重点用**不同组件**展示：如"3 个痛点"→ 3 张图标短卡；"前后对比"→ 对比双栏卡；"核心结论"→ 金句引用条；"数据"→ 数字大卡
- 提炼原则：动词开头有行动力、数字优先、每屏留白 ≥30%，宁少勿多

### Step 4 — 封面

编辑 `geo-cover/cover.html`：大字 =【封面文案】大字，小字 = 小字，顶部品牌名与页脚按文案定位填写；playwright 以 1080×1920 截图保存 PNG。改封面文字后用静帧目检排版（防孤字换行/越界）。

### Step 5 — 渲染 + 合成

```
node render-p.js geo-pagecam/index.html x --frames out/frames --mb 2 --shutter 0.5 --nogpu   # 90s 约 7~10 分钟
```
然后按 production-guide.md 的 ffmpeg 命令：混音（人声 1.0 + BGM 0.08，amix normalize=0）→ 帧序列 + 音轨 + 封面首帧淡出叠加 → attached_pic 元数据封面 → 720p 预览。

### Step 6 — 交付收尾（必做，硬性要求）

1. **成片移动到文案所在目录**：把最终交付物（成片 mp4、720p 预览 mp4、封面 PNG、voiceover.mp3、subtitle.srt）**移动到用户文案文件所在的那个目录**（从用户提供的文案路径取目录；文件名可带视频标题前缀，避免覆盖同名文件）
2. **删除全部生成缓存**：交付物移走后，删除项目目录里的所有临时产物——`out/frames`（约 1.2GB 帧缓存）、`out/mixed.wav`、`out/video.mp4` 中间产物、`--still` 静帧、`assets/audio/demo/*.mp3` 试听等；**不要删工程源文件**（geo-pagecam/index.html、geo-scene/captions.js、geo-cover/cover.html 等保留，便于下次复用改造）
3. 删大目录用 PowerShell `Remove-Item -LiteralPath <路径> -Recurse -Force -Confirm:$false`（逐条执行，不用 rm -rf）
4. 清理完成后 `present_files` 交付：预览在前、成片在后，并告知用户成片所在目录

## 硬性规则（踩过的坑，必须遵守）

1. **先静帧后全量**：任何布局/时间轴改动，先 `--still` 抽 3~5 帧验证，再渲染 2682 帧
2. **抖音安全区**：顶部字幕带 **240~346px**（2026-11 定稿：抖音状态栏 ~66px + 搜索/标签栏 ~120px 会挡住 92px 的旧位置，字幕带与内容整体下移 148px；基础字号 28，超长句按标点符号换行成两行、不为单行缩字号）；底部 1500px 以下不放置关键内容；大字版内容起笔 ≥398、底界 ≤1500
3. **渲染尾部报错**：render-p.js 结尾 rmSync `_sub` 被沙箱拦截报 Node 错误是**已知无害**，先数帧数（duration×fps）确认完整再决定是否重渲
4. **删大目录用 PowerShell `Remove-Item -LiteralPath` 逐路径**，不用 rm -rf（沙箱拦截）
5. **ffmpeg**：音频 concat 必须 `a=1`；volumedetect 的 `-ss/-t` 放 `-i` 之前；一条命令多个输出会都取输入 0，抽帧验证逐条执行
6. **混音**：`amix=inputs=N:normalize=0`，BGM volume 0.08 起步（用户要求"人声盖过背景"），叮音效等点缀音用 adelay 定位混入
7. 封面同时进**首帧 1 秒淡出叠加**和 **mp4 元数据（attached_pic）**，两处都要
8. **场景内容两铁律**（Step 3.5）：①组件样式 ≥5 种且带动效，排版有高级感；②屏幕文字只放提炼后的重点词/金句/数字，不照抄口播稿——违反任意一条都不允许交付
9. **交付收尾**（Step 6）：成片/预览/封面/配音/字幕必须**移动到文案所在目录**，然后删除全部生成缓存（帧缓存、中间产物、试听等），只留工程源文件——不做完这条不算交付

详细参数、命令全文、横屏适配方法、时间轴同步算法 → `references/production-guide.md`
