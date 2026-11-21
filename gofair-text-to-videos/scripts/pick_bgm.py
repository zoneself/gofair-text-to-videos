#!/usr/bin/env python3
"""BGM 随机选曲器：记住用户的 BGM 目录，每次运行随机挑一首。

用法:
  python pick_bgm.py                       # 从已保存的目录随机选一首，打印绝对路径
  python pick_bgm.py --set-dir <目录>      # 设置/更换 BGM 目录（保存到 config/bgm-dir.txt）
  python pick_bgm.py --list                # 列出目录里所有可选音频
  python pick_bgm.py --reset               # 清除已保存的目录

规则:
- 目录里扫描 mp3/wav/m4a/flac（不递归），随机取一首
- 目录不存在/没有音频时返回退出码 2 并打印提示，由 AI 引导用户提供目录后 --set-dir 保存
- 用户在调用时显式给了 BGM 文件路径则不需要本脚本（显式指定优先）
"""
import argparse
import random
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

CONFIG = Path(__file__).resolve().parent.parent / "config" / "bgm-dir.txt"
EXTS = {".mp3", ".wav", ".m4a", ".flac"}


def load_dir():
    if not CONFIG.exists():
        return None
    d = Path(CONFIG.read_text(encoding="utf-8").strip())
    return d if d.is_dir() else None


def list_audio(d: Path):
    return sorted(p for p in d.iterdir() if p.suffix.lower() in EXTS and p.is_file())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set-dir", help="设置 BGM 目录")
    ap.add_argument("--list", action="store_true", help="列出目录里的音频")
    ap.add_argument("--reset", action="store_true", help="清除已保存目录")
    args = ap.parse_args()

    if args.reset:
        if CONFIG.exists():
            CONFIG.unlink()
        print("cleared")
        return

    if args.set_dir:
        d = Path(args.set_dir).expanduser()
        if not d.is_dir():
            sys.exit(f"ERROR: 目录不存在: {d}")
        files = list_audio(d)
        if not files:
            sys.exit(f"ERROR: 目录里没有音频文件 (mp3/wav/m4a/flac): {d}")
        CONFIG.parent.mkdir(parents=True, exist_ok=True)
        CONFIG.write_text(str(d), encoding="utf-8")
        print(f"saved: {d} ({len(files)} 首可选)")
        return

    d = load_dir()
    if not d:
        sys.exit("ERROR: 未设置 BGM 目录（用 --set-dir 保存，退出码 2）")
    files = list_audio(d)
    if not files:
        sys.exit(f"ERROR: 已保存目录里没有音频文件: {d}（可 --set-dir 更换）")

    if args.list:
        for i, f in enumerate(files, 1):
            mark = " <-- 本次选中" if f == files[-1] else ""
            print(f"{i}. {f.name}")
        return

    pick = random.choice(files)
    print(pick)  # stdout 只输出选中的绝对路径，供脚本调用方直接使用


if __name__ == "__main__":
    main()
