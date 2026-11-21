#!/usr/bin/env python3
"""SRT -> geo-pagecam 场景字幕数据 captions.js。

用法:
  python srt_to_captions.py assets/audio/subtitle.srt geo-scene/captions.js

输出: window.CAPTIONS = [{"s":起始秒,"e":结束秒,"text":"还原后的句子"}, ...]
场景里的关键词高亮正则（index.html 中 KW）按文案主题自行调整。
"""
import re
import sys
from pathlib import Path


def parse_srt(path: Path):
    blocks = path.read_text(encoding="utf-8").strip().split("\n\n")
    out = []
    for block in blocks:
        lines = [x for x in block.splitlines() if x.strip()]
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+)\s*-->\s*(\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        s = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        e = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        text = "".join(lines[2:]).strip()
        out.append((s, e, text))
    return out


def main():
    if len(sys.argv) < 3:
        sys.exit("usage: python srt_to_captions.py <in.srt> <out-captions.js>")
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    entries = parse_srt(src)
    if not entries:
        sys.exit(f"ERROR: no entries parsed from {src}")
    items = ", ".join(
        '{{"s":{:.3f},"e":{:.3f},"text":{}}}'.format(s, e, json_dumps(t))
        for s, e, t in entries
    )
    dst.write_text("window.CAPTIONS = [" + items + "];\n", encoding="utf-8")
    print(f"captions: {len(entries)} entries -> {dst}  (last end {entries[-1][1]:.2f}s)")


def json_dumps(s: str) -> str:
    import json
    return json.dumps(s, ensure_ascii=False)


if __name__ == "__main__":
    main()
