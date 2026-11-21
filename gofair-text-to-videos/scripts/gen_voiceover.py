#!/usr/bin/env python3
"""文案 -> 配音 mp3 + 逐句 SRT（edge-tts，10 款中文音色 + 感情类型预设）。

用法:
  python gen_voiceover.py --script 文案.txt --out-dir assets/audio --rate "+31%"
  python gen_voiceover.py --script 文案.txt --voice zh-CN-XiaoxiaoNeural --emotion 激昂热血
  python gen_voiceover.py --script 文案.txt --demo --out-dir demo/    # 生成 10 段音色试听

--fix 文件每行一条 `错读字=谐音字`（如 同行=同航），配音用谐音字、SRT 还原为错读字。
内置修正: SEO 拆 "S E O"、GEO 读 "记 E 欧"、AI 原样、DeepSeek 拆词，SRT 自动还原。
输出: <out-dir>/voiceover.mp3 + <out-dir>/subtitle.srt，stdout 打印 sentences 与 last_end。
场景 duration 必须取 last_end。

注意: edge-tts 不支持 SSML style，"感情类型"由 语速偏移+音调+音量 预设组合模拟。
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

# ---------- 音色表（男 5 / 女 5，均为 edge-tts 实测可用） ----------
VOICES = {
    # 男声
    "zh-CN-YunjianNeural":  ("云健",   "男", "热血激昂、解说感强，科普/数码/带货首选（历史默认）"),
    "zh-CN-YunyangNeural":  ("云扬",   "男", "新闻主播音，专业稳重，财经/行业解读"),
    "zh-CN-YunxiNeural":    ("云希",   "男", "阳光年轻，语感轻快，生活方式/轻科普"),
    "zh-CN-YunxiaNeural":   ("云夏",   "男", "少年音、萌系活泼，年轻化人设/搞笑向"),
    "en-US-AndrewMultilingualNeural": ("安德鲁", "男", "磁性暖男，表现力强，中文带轻微外语腔（多语言音色）"),
    # 女声
    "zh-CN-XiaoxiaoNeural": ("晓晓",   "女", "温暖亲和、全能通用，最稳女声（女声默认）"),
    "zh-CN-XiaoyiNeural":   ("晓伊",   "女", "年轻干练，职场/干货分享"),
    "zh-CN-liaoning-XiaobeiNeural": ("晓北", "女", "东北话，幽默接地气，唠嗑感强"),
    "zh-CN-shaanxi-XiaoniNeural":   ("晓妮", "女", "陕西话，明亮大方，地方特色人设"),
    "en-US-AvaMultilingualNeural":  ("艾娃",   "女", "亲切甜美、表现力丰富，中文带轻微外语腔（多语言音色）"),
}

# ---------- 感情类型预设（rate 偏移叠加到基础语速上，pitch/volume 直接替换） ----------
EMOTIONS = {
    "标准口播": {"rate": 0,  "pitch": "-2Hz", "volume": "+0%"},
    "激昂热血": {"rate": 8,  "pitch": "+4Hz", "volume": "+8%"},
    "沉稳叙事": {"rate": -4, "pitch": "-8Hz", "volume": "-4%"},
    "轻快活泼": {"rate": 5,  "pitch": "+8Hz", "volume": "+4%"},
    "温柔知性": {"rate": -2, "pitch": "+2Hz", "volume": "+0%"},
}

DEMO_TEXT = "大家好，欢迎来到我的频道。这里是一段音色试听，用来对比不同主播的声音质感。"
DEMO_DIR_NAME = "demo"

def load_text(path: Path) -> str:
    """读取文案并剥掉非口播小节（标题/发布建议/合规说明等元信息）。"""
    raw = path.read_text(encoding="utf-8")
    lines = []
    skip_headers = ("【话题标签", "【封面文案", "【字幕建议", "【互动引导", "【发布时段",
                    "【视频标题", "【建议时长", "【内容定位", "【抖音昵称", "合规", "发布建议")
    for line in raw.splitlines():
        t = line.strip()
        if not t:
            continue
        # 元信息/小节标题/合规说明一律不进配音
        if "】" in t or t.startswith(("【", "-", "======", "本稿已按")) or re.match(r"^[一二三四五六七八九十]+、", t):
            continue
        lines.append(t)
    return "\n".join(lines)

def build_pronunciation(src: str, fix_pairs):
    """字读修正: 字母逐读 + 谐音字。返回 (配音文本, 反向映射)。

    字母词规则（2026-11 用户定稿 H4 方案，试听对比后确认）:
    - SEO -> "S E O"   S 读"艾斯"两音节，空格节奏自然
    - GEO -> "记 E 欧"  G 直接读易断成"GE..O"，用谐音"记"最顺滑（与 SEO 同节奏）
    - AI  -> 不处理     中文音色本就读"爱"，拆开反而生硬
    - DeepSeek -> "Deep Seek"  按英文单词连读，避免整体被当乱码
    """
    prn = src
    prn = prn.replace("DeepSeek", "Deep Seek")
    prn = re.sub(r"SEO", "S E O", prn)
    prn = re.sub(r"GEO", "记 E 欧", prn)
    for wrong, homo in fix_pairs:
        prn = prn.replace(wrong, homo)
    reverse = {
        "Deep Seek": "DeepSeek", "S E O": "SEO", "记 E 欧": "GEO",
    }
    for wrong, homo in fix_pairs:
        reverse[homo] = wrong
    return prn, reverse

def restore(t: str, reverse) -> str:
    for k, v in reverse.items():
        t = t.replace(k, v)
    return t

def fmt_srt_time(ticks: int) -> str:
    ms = ticks / 10000
    h, rem = divmod(int(ms), 3600000)
    m, rem = divmod(rem, 60000)
    s, mill = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{mill:03d}"

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", help="文案 txt 路径（--demo 试听模式可不传）")
    ap.add_argument("--out-dir", default="assets/audio")
    ap.add_argument("--voice", default="zh-CN-YunjianNeural")
    ap.add_argument("--rate", default="+31%", help="基础语速，如 +31% / +0%")
    ap.add_argument("--pitch", default=None, help="音调，如 -2Hz（不传则取感情预设）")
    ap.add_argument("--volume", default=None, help="音量，如 +0%（不传则取感情预设）")
    ap.add_argument("--emotion", default="标准口播", choices=list(EMOTIONS), help="感情类型预设")
    ap.add_argument("--fix", default="", help="读音修正文件（每行 错读=谐音）")
    ap.add_argument("--demo", action="store_true", help="生成 10 段音色试听到 <out-dir>/demo/")
    args = ap.parse_args()

    em = EMOTIONS[args.emotion]
    m = re.match(r"([+-]?\d+)%", args.rate.strip())
    base_rate = int(m.group(1)) if m else 0
    rate = f"{base_rate + em['rate']:+d}%"
    pitch = args.pitch if args.pitch is not None else em["pitch"]
    volume = args.volume if args.volume is not None else em["volume"]

    import edge_tts

    # ---------- 试听模式：10 段短样本 ----------
    if args.demo:
        demo_dir = Path(args.out_dir) / DEMO_DIR_NAME
        demo_dir.mkdir(parents=True, exist_ok=True)
        for vid, (name, gender, _desc) in VOICES.items():
            out = demo_dir / f"{gender}-{name}.mp3"
            await edge_tts.Communicate(DEMO_TEXT, vid, rate=rate, pitch=pitch, volume=volume).save(str(out))
            print(f"demo ok: {out.name}")
        print(f"demo done -> {demo_dir} (rate={rate} pitch={pitch} volume={volume} emotion={args.emotion})")
        return

    if not args.script:
        sys.exit("ERROR: --script is required unless --demo")
    src = load_text(Path(args.script))
    fix_pairs = []
    if args.fix:
        for line in Path(args.fix).read_text(encoding="utf-8").splitlines():
            if "=" in line:
                a, b = line.strip().split("=", 1)
                if a and b:
                    fix_pairs.append((a, b))
    prn, reverse = build_pronunciation(src, fix_pairs)

    import edge_tts
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    c = edge_tts.Communicate(prn, args.voice, rate=rate, pitch=pitch, volume=volume, boundary="SentenceBoundary")
    bounds, audio = [], bytearray()
    with open(out_dir / "voiceover.mp3", "wb") as f:
        async for chunk in c.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                bounds.append(chunk)

    lines = []
    for i, b in enumerate(bounds, 1):
        txt = restore(b["text"], reverse).strip()
        if not txt:
            continue
        lines.append(f"{i}\n{fmt_srt_time(b['offset'])} --> {fmt_srt_time(b['offset'] + b['duration'])}\n{txt}\n")
    (out_dir / "subtitle.srt").write_text("\n".join(lines), encoding="utf-8")

    total = (bounds[-1]["offset"] + bounds[-1]["duration"]) / 1e7 if bounds else 0
    vname = VOICES.get(args.voice, ("?", "?", "?"))[0]
    print(f"voice={vname}({args.voice}) rate={rate} pitch={pitch} volume={volume} emotion={args.emotion} sentences={len(bounds)} last_end={total:.2f}s")
    if not bounds:
        sys.exit("ERROR: no sentence boundaries — check script text")

if __name__ == "__main__":
    asyncio.run(main())
