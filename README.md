# GoFair Text to Videos（文案成片技能）

把一份口播文案，自动变成一条可直接发布的短视频：**配音 → 逐句字幕 → 代码渲染场景 → 自动封面 → 混音合成**，全流程约 20~30 分钟，产出 1080×1920 成片 + 720p 预览。

面向 [WorkBuddy](https://www.workbuddy.cn/) 的 Agent Skill。安装后只需说一句：**「用 @文案.txt 做个视频」**。

## ✨ 特性

- **免指定 BGM**：预先设置一个音乐目录，每次自动随机挑一首当背景音；显式给了音频文件则优先用你的
- **风格库推荐**：按文案内容推荐 3~5 种最匹配的视频风格供确认——内置页面推镜版 / 封面式大字版两种自有风格，另附 100+ 风格库（styles 20 种 + vol2 20 种 + industry 60 条行业片）
- **10 款音色 + 5 种感情**：5 男 5 女可试听选择，语速 / 感情类型可调（edge-tts）
- **字母词读音定稿**：SEO 拆 `S E O`、GEO 读「记 E 欧」、AI 原样、DeepSeek 拆词连读，SRT 字幕自动还原正常写法
- **抖音安全区**：字幕带 240~346px（避开状态栏 + 搜索条）、底部 1500px 以上不放关键内容
- **组件化场景铁律**：每屏 ≥2~3 种组件、全片 ≥5 种类型、全部带入场动效；屏幕文字只放提炼后的重点词/数字/金句，不照抄口播稿
- **自动交付收尾**：成片自动放到文案所在目录，帧缓存等临时文件自动清理

## 📦 仓库结构

```
├── gofair-text-to-videos/    # Agent Skill 本体（安装到 WorkBuddy skills 目录）
│   ├── SKILL.md              # 技能主文件：触发词 + 工作流 + 音色/感情表 + 硬性规则
│   ├── references/           # production-guide.md 生产手册（几何/读音/命令/踩坑）
│   ├── scripts/              # gen_voiceover.py 配音 / pick_bgm.py BGM 选曲 / srt_to_captions.py
│   └── assets/template/      # 渲染管线模板（render-p.js + geo-pagecam + geo-bigtext + 封面）
└── sy-style-100-main/        # 风格库主仓库（styles / vol2 / industry / 渲染器 / 文档）
```

## 🚀 安装使用

1. 把 `gofair-text-to-videos/` 整个文件夹放入 `~/.workbuddy/skills/`（或在 WorkBuddy 技能页上传 zip）
2. 依赖：Node.js ≥ 18（`npm i playwright && npx playwright install chromium`）、Python + `edge-tts`、ffmpeg
3. WorkBuddy 对话里说：`用 @文案.txt 做个视频`
4. 首次会问一次 BGM 目录（存多首 mp3 的文件夹路径），之后永久记住
5. 按卡片提示选风格 → 音色 → 语速 → 感情 → 画幅，确认后等待出片

## 🎬 两种自有风格

| 风格 | 说明 | 适合 |
|---|---|---|
| **封面式大字版**（推荐） | 全屏封面级大字 74~210px，组件丰富（数字滚动、VS 对比卡、勾选清单、粒子订阅等），手机端清晰 | 口播科普 / 观点输出 |
| **页面推镜版** | 模拟浏览器窗口逐屏上滑 + 3D 推镜，深色系 | 演示"网页内容"类文案 |

## 📄 License

仅供团队内部与学习交流使用。
