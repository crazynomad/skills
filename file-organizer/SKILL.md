---
name: file-organizer
description: Mac 智能文件整理助手，支持上班族/码农模板，手动/自动两种整理模式
---

# File Organizer - Mac 智能文件整理助手

帮助用户整理散落在各处的重要文件，支持手动整理（智能文件夹）和自动整理两种模式，并与 disk-cleaner 配合保护重要文件。

## When to Use

Use this skill when users:
- 想整理电脑上的文件
- 文件太乱找不到东西
- 清理磁盘前想先把重要文件整理好
- 下载文件夹太乱想整理
- 截图太多想归类
- 想找出占空间的大文件

## Features

- **👔 上班族模板**: 关注 PPT、Word、Excel、PDF 等办公文件
- **💻 码农模板**: 关注代码、配置文件、Markdown 等开发文件
- **🖐️ 手动模式**: 创建智能文件夹，用户自己整理
- **🤖 自动模式**: 自动扫描并分类最近一年的文件
- **📥 下载整理**: 整理 Downloads 文件夹
- **📸 截图整理**: 整理截图文件
- **📦 大文件发现**: 找出占空间的大文件

## Templates

### 上班族 (office-worker)

关注文件类型：
- 📊 PPT/Keynote 演示文稿
- 📝 Word/Pages 文档
- 📈 Excel/Numbers 表格
- 📄 PDF 文件
- 🖼️ 图片文件

### 码农 (developer)

关注文件类型：
- 💻 代码文件 (.py, .js, .ts, .go, .rs, .java, .swift 等)
- ⚙️ 配置文件 (.json, .yaml, .toml, .env 等)
- 📝 Markdown 文档
- 🗃️ 数据库文件 (.db, .sqlite)
- 🔑 密钥/证书文件

## Usage

### 选择模板并创建智能文件夹（手动模式）

```bash
python scripts/file_organizer.py --template office-worker --manual
python scripts/file_organizer.py --template developer --manual
```

### 自动整理文件

```bash
python scripts/file_organizer.py --template office-worker --auto
python scripts/file_organizer.py --template developer --auto --days 365
```

### 整理下载文件夹

```bash
python scripts/file_organizer.py --downloads
python scripts/file_organizer.py --downloads --auto
```

### 整理截图

```bash
python scripts/file_organizer.py --screenshots
python scripts/file_organizer.py --screenshots --auto
```

### 发现大文件

```bash
python scripts/file_organizer.py --large-files
python scripts/file_organizer.py --large-files --min-size 500MB
```

### HTML 报告

```bash
python scripts/file_organizer.py --template office-worker --auto --html
```

## Modes

### 手动模式 (--manual)

1. 在桌面创建「待整理」文件夹
2. 内置多个 macOS 智能文件夹（Saved Search）：
   - 「大于 1MB 的 PDF」
   - 「本周修改的文档」
   - 「下载文件夹中的压缩包」
   - 等等...
3. 用户打开智能文件夹，自行拖拽整理

### 自动模式 (--auto)

1. 扫描用户目录，找出最近 N 天内新增/修改的感兴趣文件
2. 在桌面创建「已整理文件」文件夹
3. 按类型创建子文件夹并移动文件
4. 生成整理报告
5. 将该文件夹路径加入 disk-cleaner 白名单

## Output Structure

### 手动模式输出

```
~/Desktop/待整理/
├── 📁 大型PDF文件.savedSearch
├── 📁 本周文档.savedSearch
├── 📁 下载压缩包.savedSearch
└── 📁 最近截图.savedSearch
```

### 自动模式输出

```
~/Desktop/已整理文件-20240125/
├── 📁 文档/
│   ├── Word/
│   ├── PDF/
│   └── PPT/
├── 📁 表格/
├── 📁 图片/
├── 📁 截图/
└── 📁 大文件/
```

## Integration with disk-cleaner

自动模式会将整理后的文件夹路径写入 `~/.config/mole/whitelist.txt`，确保这些文件不会被 disk-cleaner 清理。

## Dependencies

- macOS (使用 Spotlight 和智能文件夹功能)
- Python 3.8+
- jinja2 (`pip install jinja2`)

## Credits

- 与 [disk-cleaner](../disk-cleaner/) 配合使用
- 灵感来自 macOS 智能文件夹功能
