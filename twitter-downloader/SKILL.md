---
name: twitter-downloader
description: Download videos from X (Twitter) posts using twmd — a fast, API-less downloader
---

# X / Twitter Video Downloader (twmd)

Download videos from individual X (Twitter) posts using `twmd`, an API-less Go-based downloader.

## When to Use

Use this skill when users:
- Provide an X/Twitter post URL and want to download its video
- Mention "下载推文视频", "download Twitter video", "save X video", "下载 X 视频"
- Share a link like `https://x.com/username/status/123456` or `https://twitter.com/username/status/123456`

## Usage

### Basic Syntax

```bash
python scripts/download_tweet.py "TWEET_URL" [OPTIONS]
```

### Common Scenarios

**Download video from a tweet**:
```bash
python scripts/download_tweet.py "https://x.com/username/status/1234567890"
```

**Specify output directory**:
```bash
python scripts/download_tweet.py "https://x.com/username/status/1234567890" -o ~/Downloads/twitter
```

**Download in specific quality**:
```bash
python scripts/download_tweet.py "https://x.com/username/status/1234567890" -q 720
```

**Print video URL without downloading**:
```bash
python scripts/download_tweet.py "https://x.com/username/status/1234567890" --url-only
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `url` | X/Twitter post URL (required) | - |
| `-o, --output` | Output directory | Current directory |
| `-q, --quality` | Video quality: `best`, `1080`, `720`, `480` | `best` |
| `--url-only` | Print video direct URL without downloading | False |
| `--cookies` | Path to cookies file (for private/restricted content) | None |

## Dependencies

```bash
pip install yt-dlp
```

No additional setup needed. `yt-dlp` handles public X/Twitter posts without cookies or API keys.

## Output Structure

```
OutputDir/
└── <tweet_id>.mp4     # Downloaded video file
```

`twmd` names files by tweet ID. The script reports the file path after download.

## Authentication (Optional)

For private accounts or login-gated content, export cookies from your browser:

1. Install a browser extension like "Get cookies.txt LOCALLY"
2. Log in to X, then export cookies for `x.com` as a Netscape-format `.txt` file
3. Pass the file with `--cookies`:

```bash
python scripts/download_tweet.py "URL" --cookies ~/x-cookies.txt
```

## Claude Integration

When user provides an X/Twitter post URL and wants to download its video:

1. **Check if yt-dlp is installed**:
   ```bash
   yt-dlp --version
   ```

2. **Install if missing**:
   ```bash
   pip install yt-dlp
   ```

3. **Execute download**:
   ```bash
   python twitter-downloader/scripts/download_tweet.py "TWEET_URL" -o ./output
   ```

4. **Report the downloaded file** to the user with its path and size.

## Common Issues

**Q: Download fails with "Unable to extract" error?**
A: Update yt-dlp first: `pip install -U yt-dlp` — X/Twitter frequently changes its API.

**Q: The tweet has no video?**
A: Try `--url-only` to check what media yt-dlp can find. Image-only tweets will not yield a video URL.

**Q: Need to download from a private account?**
A: Export browser cookies (see Authentication section above) and pass with `--cookies`.

**Q: Why not just use youtube-downloader for Twitter URLs?**
A: You can — yt-dlp handles Twitter URLs too. This skill provides a Twitter-focused interface with cleaner prompts and no unneeded options (playlists, subtitles, etc.).

## References

- [yt-dlp GitHub](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp supported sites (includes Twitter/X)](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)
