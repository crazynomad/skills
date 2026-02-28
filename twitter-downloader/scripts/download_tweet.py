#!/usr/bin/env python3
"""
X / Twitter 视频下载器 - 基于 yt-dlp
从单条推文中下载视频，无需 API Key 和 cookies
"""

import sys
import argparse
import subprocess
import re
import shutil
from pathlib import Path


def check_ytdlp() -> bool:
    """检查 yt-dlp 是否安装"""
    if shutil.which('yt-dlp'):
        result = subprocess.run(['yt-dlp', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ yt-dlp 版本: {result.stdout.strip()}")
            return True
    print("❌ 未找到 yt-dlp，请先安装：pip install yt-dlp")
    return False


def is_twitter_url(url: str) -> bool:
    """判断是否为 X/Twitter URL"""
    return bool(re.search(r'(x\.com|twitter\.com)/\w+/status/\d+', url))


def download_tweet_video(url: str, output_dir: str = '.', quality: str = 'best',
                         url_only: bool = False, cookies_file: str | None = None) -> bool:
    """下载推文视频"""
    print("🐦 X / Twitter 视频下载器 (yt-dlp)")
    print("=" * 50)

    if not check_ytdlp():
        return False

    if not is_twitter_url(url):
        print(f"⚠️  URL 不像是 X/Twitter 帖子链接: {url}")
        print("   期望格式: https://x.com/username/status/1234567890")

    # 创建输出目录
    output_path = Path(output_dir)
    if not url_only:
        output_path.mkdir(parents=True, exist_ok=True)

    print(f"🔗 URL: {url}")
    if not url_only:
        print(f"📂 输出目录: {output_path.absolute()}")
        print(f"📊 质量: {quality}")

    if url_only:
        # 只打印视频直链，不下载
        cmd = ['yt-dlp', '-g', url]
        if cookies_file:
            cmd.extend(['--cookies', cookies_file])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📎 视频直链:")
            print(result.stdout.strip())
            return True
        else:
            print(f"\n❌ 获取视频链接失败:\n{result.stderr.strip()}")
            return False

    # 构建下载命令
    output_template = str(output_path / '%(id)s.%(ext)s')
    format_map = {
        'best':  'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '1080':  'bestvideo[height<=1080][ext=mp4]+bestaudio/best[height<=1080]',
        '720':   'bestvideo[height<=720][ext=mp4]+bestaudio/best[height<=720]',
        '480':   'bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480]',
    }

    cmd = [
        'yt-dlp',
        '-f', format_map.get(quality, format_map['best']),
        '-o', output_template,
        '--no-playlist',
        '--no-overwrites',
        '--progress',
    ]

    if cookies_file:
        cmd.extend(['--cookies', cookies_file])

    cmd.append(url)

    print()
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        for line in process.stdout:
            print(line, end='')

        process.wait()

        if process.returncode == 0:
            print("\n" + "=" * 50)
            print("✨ 下载完成!")

            downloaded = [f for f in output_path.iterdir()
                          if f.is_file() and not f.name.startswith('.')]
            if downloaded:
                print("\n📁 下载的文件:")
                for f in sorted(downloaded):
                    size_mb = f.stat().st_size / 1024 / 1024
                    print(f"   • {f.name} ({size_mb:.1f} MB)")
                    print(f"   📂 {f.absolute()}")
            return True
        else:
            print(f"\n❌ 下载失败，退出码: {process.returncode}")
            return False

    except KeyboardInterrupt:
        print("\n\n⚠️  下载被用户中断")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='X / Twitter 视频下载器（基于 yt-dlp）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 下载推文视频
  %(prog)s "https://x.com/username/status/1234567890"

  # 指定输出目录
  %(prog)s "https://x.com/username/status/1234567890" -o ~/Downloads/twitter

  # 只打印视频直链（不下载）
  %(prog)s "https://x.com/username/status/1234567890" --url-only

  # 指定分辨率
  %(prog)s "https://x.com/username/status/1234567890" -q 720

安装依赖:
  pip install yt-dlp
        """
    )

    parser.add_argument('url', help='X/Twitter 帖子 URL')
    parser.add_argument('-o', '--output', default='.',
                        help='输出目录（默认：当前目录）')
    parser.add_argument('-q', '--quality', default='best',
                        choices=['best', '1080', '720', '480'],
                        help='视频质量（默认：best）')
    parser.add_argument('--url-only', action='store_true',
                        help='只打印视频直链，不下载')
    parser.add_argument('--cookies', type=str,
                        help='Cookies 文件路径（用于私密或受限内容）')

    args = parser.parse_args()

    success = download_tweet_video(
        url=args.url,
        output_dir=args.output,
        quality=args.quality,
        url_only=args.url_only,
        cookies_file=args.cookies,
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
