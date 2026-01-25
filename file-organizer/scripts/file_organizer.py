#!/usr/bin/env python3
"""
File Organizer - Mac 智能文件整理助手

支持上班族/码农两种模板，手动/自动两种整理模式。
与 disk-cleaner 配合，保护重要文件不被清理。
"""

import argparse
import json
import os
import plistlib
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader


@dataclass
class FileCategory:
    """文件分类定义"""
    name: str
    icon: str
    extensions: list[str]
    description: str
    min_size_bytes: int = 0  # 最小文件大小（用于智能文件夹）


@dataclass
class Template:
    """用户模板定义"""
    name: str
    display_name: str
    description: str
    categories: list[FileCategory]


@dataclass
class OrganizeResult:
    """整理结果"""
    template: str
    mode: str
    scan_time: str
    total_files: int = 0
    total_size_bytes: int = 0
    categories: dict = field(default_factory=dict)
    output_path: str = ""
    smart_folders: list = field(default_factory=list)


class FileOrganizer:
    """文件整理器"""

    # 用户目录
    HOME = Path.home()
    DESKTOP = HOME / "Desktop"
    DOWNLOADS = HOME / "Downloads"
    DOCUMENTS = HOME / "Documents"
    PICTURES = HOME / "Pictures"

    # 截图默认位置
    SCREENSHOT_LOCATIONS = [
        HOME / "Desktop",
        HOME / "Pictures" / "Screenshots",
        HOME / "Documents" / "Screenshots",
    ]

    # 配置目录
    CONFIG_DIR = HOME / ".config" / "file-organizer"
    MOLE_WHITELIST = HOME / ".config" / "mole" / "whitelist.txt"

    # 模板定义
    TEMPLATES = {
        "office-worker": Template(
            name="office-worker",
            display_name="上班族",
            description="关注办公文档、演示文稿、表格、PDF",
            categories=[
                FileCategory(
                    name="演示文稿",
                    icon="📊",
                    extensions=[".ppt", ".pptx", ".key"],
                    description="PPT/Keynote 演示文稿",
                ),
                FileCategory(
                    name="文档",
                    icon="📝",
                    extensions=[".doc", ".docx", ".pages", ".rtf"],
                    description="Word/Pages 文档",
                ),
                FileCategory(
                    name="表格",
                    icon="📈",
                    extensions=[".xls", ".xlsx", ".numbers", ".csv"],
                    description="Excel/Numbers 表格",
                ),
                FileCategory(
                    name="PDF",
                    icon="📄",
                    extensions=[".pdf"],
                    description="PDF 文件",
                    min_size_bytes=1024 * 1024,  # 1MB
                ),
                FileCategory(
                    name="图片",
                    icon="🖼️",
                    extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"],
                    description="图片文件",
                ),
            ],
        ),
        "developer": Template(
            name="developer",
            display_name="码农",
            description="关注代码、配置文件、Markdown 文档",
            categories=[
                FileCategory(
                    name="代码",
                    icon="💻",
                    extensions=[
                        ".py", ".js", ".ts", ".jsx", ".tsx",
                        ".go", ".rs", ".java", ".swift", ".kt",
                        ".c", ".cpp", ".h", ".hpp",
                        ".rb", ".php", ".sh", ".bash",
                    ],
                    description="源代码文件",
                ),
                FileCategory(
                    name="配置",
                    icon="⚙️",
                    extensions=[
                        ".json", ".yaml", ".yml", ".toml",
                        ".env", ".ini", ".cfg", ".conf",
                    ],
                    description="配置文件",
                ),
                FileCategory(
                    name="文档",
                    icon="📝",
                    extensions=[".md", ".markdown", ".txt", ".rst"],
                    description="Markdown/文本文档",
                ),
                FileCategory(
                    name="数据",
                    icon="🗃️",
                    extensions=[".db", ".sqlite", ".sqlite3", ".sql"],
                    description="数据库文件",
                ),
                FileCategory(
                    name="密钥",
                    icon="🔑",
                    extensions=[".pem", ".key", ".crt", ".cer", ".p12"],
                    description="密钥/证书文件",
                ),
            ],
        ),
    }

    # 通用分类（下载、截图、大文件）
    COMMON_CATEGORIES = {
        "downloads": FileCategory(
            name="下载文件",
            icon="📥",
            extensions=[],  # 所有文件
            description="Downloads 文件夹中的文件",
        ),
        "screenshots": FileCategory(
            name="截图",
            icon="📸",
            extensions=[".png", ".jpg", ".jpeg"],
            description="屏幕截图文件",
        ),
        "archives": FileCategory(
            name="压缩包",
            icon="📦",
            extensions=[".zip", ".rar", ".7z", ".tar", ".gz", ".dmg"],
            description="压缩包和磁盘镜像",
        ),
        "large_files": FileCategory(
            name="大文件",
            icon="💾",
            extensions=[],  # 所有文件
            description="占用空间的大文件",
            min_size_bytes=100 * 1024 * 1024,  # 100MB
        ),
    }

    def __init__(self):
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def _get_file_info(self, path: Path) -> dict:
        """获取文件信息"""
        try:
            stat = path.stat()
            return {
                "path": str(path),
                "name": path.name,
                "size_bytes": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "created": datetime.fromtimestamp(stat.st_ctime),
            }
        except (OSError, PermissionError):
            return None

    def _is_screenshot(self, path: Path) -> bool:
        """判断是否为截图文件"""
        name = path.name.lower()
        # macOS 截图命名模式
        patterns = [
            "screenshot",
            "屏幕快照",
            "截屏",
            "screen shot",
            "截图",
        ]
        return any(p in name for p in patterns)

    def _create_smart_folder(self, name: str, query: str, output_dir: Path) -> Path:
        """创建 macOS 智能文件夹（.savedSearch）"""
        # 智能文件夹是一个 plist 文件
        saved_search = {
            "CompatibleVersion": 1,
            "RawQuery": query,
            "SearchCriteria": {
                "CurrentFolderPath": [str(self.HOME)],
                "FXScopeArrayOfPaths": [str(self.HOME)],
            },
        }

        folder_path = output_dir / f"{name}.savedSearch"

        try:
            with open(folder_path, "wb") as f:
                plistlib.dump(saved_search, f)
            return folder_path
        except Exception as e:
            print(f"⚠️  创建智能文件夹失败: {e}")
            return None

    def _add_to_whitelist(self, path: str):
        """将路径添加到 disk-cleaner 白名单"""
        try:
            self.MOLE_WHITELIST.parent.mkdir(parents=True, exist_ok=True)

            existing = set()
            if self.MOLE_WHITELIST.exists():
                existing = set(self.MOLE_WHITELIST.read_text().strip().split("\n"))

            existing.add(path)

            self.MOLE_WHITELIST.write_text("\n".join(sorted(existing)) + "\n")
            print(f"🔒 已添加到 disk-cleaner 白名单: {path}")
        except Exception as e:
            print(f"⚠️  添加白名单失败: {e}")

    def get_template(self, name: str) -> Optional[Template]:
        """获取模板"""
        return self.TEMPLATES.get(name)

    def list_templates(self):
        """列出所有模板"""
        print("📋 可用模板:")
        print("")
        for name, template in self.TEMPLATES.items():
            print(f"  {template.display_name} ({name})")
            print(f"    {template.description}")
            print(f"    关注: {', '.join(c.name for c in template.categories)}")
            print("")

    def create_manual_folders(self, template_name: str) -> OrganizeResult:
        """手动模式：创建智能文件夹"""
        template = self.get_template(template_name)
        if not template:
            print(f"❌ 未知模板: {template_name}")
            return None

        print(f"🖐️ 手动模式 - {template.display_name}模板")
        print("")

        # 创建输出目录
        output_dir = self.DESKTOP / "待整理"
        output_dir.mkdir(exist_ok=True)

        result = OrganizeResult(
            template=template_name,
            mode="manual",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            output_path=str(output_dir),
        )

        # 为每个分类创建智能文件夹
        for category in template.categories:
            ext_query = " || ".join(f'kMDItemFSName == "*{ext}"' for ext in category.extensions)

            # 添加大小条件
            if category.min_size_bytes > 0:
                size_kb = category.min_size_bytes // 1024
                query = f"({ext_query}) && kMDItemFSSize >= {size_kb}000"
                folder_name = f"{category.icon} {category.name} (>{self._format_size(category.min_size_bytes)})"
            else:
                query = ext_query
                folder_name = f"{category.icon} {category.name}"

            folder_path = self._create_smart_folder(folder_name, query, output_dir)
            if folder_path:
                result.smart_folders.append({
                    "name": folder_name,
                    "path": str(folder_path),
                    "category": category.name,
                })
                print(f"  ✅ 创建智能文件夹: {folder_name}")

        # 添加通用智能文件夹
        common_folders = [
            ("📥 本周下载", f'kMDItemFSName == "*" && kMDItemContentCreationDate >= $time.today(-7)'),
            ("📸 最近截图", 'kMDItemFSName == "*截*" || kMDItemFSName == "*screenshot*"c'),
            ("💾 大文件 (>100MB)", 'kMDItemFSSize >= 100000000'),
        ]

        for name, query in common_folders:
            folder_path = self._create_smart_folder(name, query, output_dir)
            if folder_path:
                result.smart_folders.append({
                    "name": name,
                    "path": str(folder_path),
                    "category": "通用",
                })
                print(f"  ✅ 创建智能文件夹: {name}")

        print("")
        print(f"📁 智能文件夹已创建: {output_dir}")
        print("💡 打开文件夹，双击智能文件夹查看匹配的文件，然后自行整理")

        return result

    def scan_files(
        self,
        template_name: str,
        days: int = 365,
        scan_paths: list[Path] = None,
    ) -> dict[str, list[dict]]:
        """扫描符合条件的文件"""
        template = self.get_template(template_name)
        if not template:
            return {}

        if scan_paths is None:
            scan_paths = [self.HOME]

        # 计算时间阈值
        cutoff_date = datetime.now() - timedelta(days=days)

        # 构建扩展名集合
        all_extensions = set()
        for category in template.categories:
            all_extensions.update(ext.lower() for ext in category.extensions)

        # 扫描文件
        results = {cat.name: [] for cat in template.categories}

        print(f"🔍 扫描最近 {days} 天内修改的文件...")

        for scan_path in scan_paths:
            if not scan_path.exists():
                continue

            try:
                for path in scan_path.rglob("*"):
                    # 跳过隐藏文件和目录
                    if any(part.startswith(".") for part in path.parts):
                        continue

                    # 跳过目录
                    if path.is_dir():
                        continue

                    # 检查扩展名
                    ext = path.suffix.lower()
                    if ext not in all_extensions:
                        continue

                    # 获取文件信息
                    info = self._get_file_info(path)
                    if not info:
                        continue

                    # 检查修改时间
                    if info["modified"] < cutoff_date:
                        continue

                    # 分类
                    for category in template.categories:
                        if ext in [e.lower() for e in category.extensions]:
                            # 检查大小限制
                            if info["size_bytes"] >= category.min_size_bytes:
                                results[category.name].append(info)
                            break

            except PermissionError:
                continue

        return results

    def auto_organize(
        self,
        template_name: str,
        days: int = 365,
        dry_run: bool = False,
    ) -> OrganizeResult:
        """自动模式：扫描并整理文件"""
        template = self.get_template(template_name)
        if not template:
            print(f"❌ 未知模板: {template_name}")
            return None

        print(f"🤖 自动模式 - {template.display_name}模板")
        print("")

        # 扫描文件
        scanned = self.scan_files(template_name, days)

        result = OrganizeResult(
            template=template_name,
            mode="auto",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        # 统计
        for category_name, files in scanned.items():
            if files:
                total_size = sum(f["size_bytes"] for f in files)
                result.categories[category_name] = {
                    "files": files,
                    "count": len(files),
                    "size_bytes": total_size,
                    "size_human": self._format_size(total_size),
                }
                result.total_files += len(files)
                result.total_size_bytes += total_size

        if result.total_files == 0:
            print("ℹ️  未找到符合条件的文件")
            return result

        # 显示扫描结果
        print(f"📊 扫描结果: {result.total_files} 个文件, {self._format_size(result.total_size_bytes)}")
        print("")

        for cat in template.categories:
            if cat.name in result.categories:
                data = result.categories[cat.name]
                print(f"  {cat.icon} {cat.name}: {data['count']} 个文件, {data['size_human']}")

        print("")

        if dry_run:
            print("🔍 预览模式，不会移动文件")
            return result

        # 创建输出目录
        timestamp = datetime.now().strftime("%Y%m%d")
        output_dir = self.DESKTOP / f"已整理文件-{timestamp}"
        output_dir.mkdir(exist_ok=True)
        result.output_path = str(output_dir)

        # 移动文件
        print("📦 正在整理文件...")

        for cat in template.categories:
            if cat.name not in result.categories:
                continue

            cat_dir = output_dir / cat.name
            cat_dir.mkdir(exist_ok=True)

            for file_info in result.categories[cat.name]["files"]:
                src = Path(file_info["path"])
                dst = cat_dir / src.name

                # 处理重名
                if dst.exists():
                    stem = dst.stem
                    suffix = dst.suffix
                    counter = 1
                    while dst.exists():
                        dst = cat_dir / f"{stem}_{counter}{suffix}"
                        counter += 1

                try:
                    shutil.move(str(src), str(dst))
                    file_info["new_path"] = str(dst)
                except Exception as e:
                    print(f"  ⚠️  移动失败: {src.name} - {e}")

        print(f"✅ 整理完成: {output_dir}")

        # 添加到白名单
        self._add_to_whitelist(str(output_dir))

        return result

    def organize_downloads(self, auto: bool = False, days: int = 30) -> OrganizeResult:
        """整理下载文件夹"""
        print("📥 整理下载文件夹")
        print("")

        result = OrganizeResult(
            template="downloads",
            mode="auto" if auto else "manual",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        if not self.DOWNLOADS.exists():
            print("❌ Downloads 文件夹不存在")
            return result

        try:
            list(self.DOWNLOADS.iterdir())
        except PermissionError:
            print("❌ 无法访问 Downloads 文件夹")
            print("💡 请在「系统设置 → 隐私与安全性 → 文件和文件夹」中授权")
            return result

        # 分类定义
        download_categories = {
            "文档": [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"],
            "图片": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".svg"],
            "视频": [".mp4", ".mov", ".avi", ".mkv", ".wmv"],
            "音频": [".mp3", ".wav", ".flac", ".aac", ".m4a"],
            "压缩包": [".zip", ".rar", ".7z", ".tar", ".gz", ".dmg"],
            "安装包": [".pkg", ".app", ".exe", ".msi"],
            "代码": [".py", ".js", ".ts", ".json", ".yaml", ".html", ".css"],
        }

        # 扫描
        cutoff_date = datetime.now() - timedelta(days=days)
        categorized = {cat: [] for cat in download_categories}
        categorized["其他"] = []

        try:
            for path in self.DOWNLOADS.iterdir():
                if path.name.startswith(".") or path.is_dir():
                    continue

                info = self._get_file_info(path)
                if not info:
                    continue

                if info["modified"] < cutoff_date:
                    continue

                ext = path.suffix.lower()
                found = False
                for cat_name, extensions in download_categories.items():
                    if ext in extensions:
                        categorized[cat_name].append(info)
                        found = True
                        break

                if not found:
                    categorized["其他"].append(info)
        except PermissionError:
            print("❌ 无法访问 Downloads 文件夹")
            print("💡 请在「系统设置 → 隐私与安全性 → 文件和文件夹」中授权")
            return result

        # 统计
        for cat_name, files in categorized.items():
            if files:
                total_size = sum(f["size_bytes"] for f in files)
                result.categories[cat_name] = {
                    "files": files,
                    "count": len(files),
                    "size_bytes": total_size,
                    "size_human": self._format_size(total_size),
                }
                result.total_files += len(files)
                result.total_size_bytes += total_size

        # 显示结果
        print(f"📊 扫描结果: {result.total_files} 个文件, {self._format_size(result.total_size_bytes)}")
        print("")

        for cat_name, files in categorized.items():
            if files:
                size = sum(f["size_bytes"] for f in files)
                print(f"  📁 {cat_name}: {len(files)} 个文件, {self._format_size(size)}")

        if auto and result.total_files > 0:
            print("")
            print("📦 正在整理...")

            output_dir = self.DOWNLOADS / "已整理"
            output_dir.mkdir(exist_ok=True)
            result.output_path = str(output_dir)

            for cat_name, files in categorized.items():
                if not files:
                    continue

                cat_dir = output_dir / cat_name
                cat_dir.mkdir(exist_ok=True)

                for file_info in files:
                    src = Path(file_info["path"])
                    dst = cat_dir / src.name

                    if dst.exists():
                        stem = dst.stem
                        suffix = dst.suffix
                        counter = 1
                        while dst.exists():
                            dst = cat_dir / f"{stem}_{counter}{suffix}"
                            counter += 1

                    try:
                        shutil.move(str(src), str(dst))
                    except Exception as e:
                        print(f"  ⚠️  移动失败: {src.name} - {e}")

            print(f"✅ 整理完成: {output_dir}")

        return result

    def organize_screenshots(self, auto: bool = False, days: int = 90) -> OrganizeResult:
        """整理截图文件"""
        print("📸 整理截图文件")
        print("")

        result = OrganizeResult(
            template="screenshots",
            mode="auto" if auto else "manual",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        cutoff_date = datetime.now() - timedelta(days=days)
        screenshots = []

        # 扫描截图位置
        for location in self.SCREENSHOT_LOCATIONS:
            if not location.exists():
                continue

            for path in location.iterdir():
                if not path.is_file():
                    continue

                if not self._is_screenshot(path):
                    continue

                info = self._get_file_info(path)
                if info and info["modified"] >= cutoff_date:
                    screenshots.append(info)

        if not screenshots:
            print("ℹ️  未找到截图文件")
            return result

        result.total_files = len(screenshots)
        result.total_size_bytes = sum(s["size_bytes"] for s in screenshots)

        # 按月份分组
        by_month = {}
        for ss in screenshots:
            month_key = ss["modified"].strftime("%Y-%m")
            if month_key not in by_month:
                by_month[month_key] = []
            by_month[month_key].append(ss)

        print(f"📊 找到 {result.total_files} 张截图, {self._format_size(result.total_size_bytes)}")
        print("")

        for month, files in sorted(by_month.items(), reverse=True):
            size = sum(f["size_bytes"] for f in files)
            print(f"  📅 {month}: {len(files)} 张, {self._format_size(size)}")

        result.categories = {
            month: {
                "files": files,
                "count": len(files),
                "size_bytes": sum(f["size_bytes"] for f in files),
            }
            for month, files in by_month.items()
        }

        if auto and screenshots:
            print("")
            print("📦 正在整理...")

            output_dir = self.PICTURES / "截图整理"
            output_dir.mkdir(exist_ok=True)
            result.output_path = str(output_dir)

            for month, files in by_month.items():
                month_dir = output_dir / month
                month_dir.mkdir(exist_ok=True)

                for file_info in files:
                    src = Path(file_info["path"])
                    dst = month_dir / src.name

                    if dst.exists():
                        continue

                    try:
                        shutil.move(str(src), str(dst))
                    except Exception as e:
                        print(f"  ⚠️  移动失败: {src.name} - {e}")

            print(f"✅ 整理完成: {output_dir}")

        return result

    def find_large_files(self, min_size_mb: int = 100, limit: int = 50) -> OrganizeResult:
        """发现大文件"""
        print(f"💾 查找大于 {min_size_mb}MB 的文件")
        print("")

        result = OrganizeResult(
            template="large_files",
            mode="scan",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = []

        # 扫描用户目录
        scan_paths = [self.DOCUMENTS, self.DOWNLOADS, self.DESKTOP, self.PICTURES]

        for scan_path in scan_paths:
            if not scan_path.exists():
                continue

            try:
                for path in scan_path.rglob("*"):
                    if path.name.startswith(".") or path.is_dir():
                        continue

                    info = self._get_file_info(path)
                    if info and info["size_bytes"] >= min_size_bytes:
                        info["location"] = scan_path.name
                        large_files.append(info)

            except PermissionError:
                continue

        # 按大小排序
        large_files.sort(key=lambda x: x["size_bytes"], reverse=True)
        large_files = large_files[:limit]

        result.total_files = len(large_files)
        result.total_size_bytes = sum(f["size_bytes"] for f in large_files)

        print(f"📊 找到 {result.total_files} 个大文件, 共 {self._format_size(result.total_size_bytes)}")
        print("")

        # 按位置分组显示
        by_location = {}
        for f in large_files:
            loc = f["location"]
            if loc not in by_location:
                by_location[loc] = []
            by_location[loc].append(f)

        for location, files in by_location.items():
            print(f"📁 {location}:")
            for f in files[:10]:  # 每个位置显示前10个
                print(f"  💾 {f['size_human']:>10}  {f['name']}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
            print("")

        result.categories = by_location

        return result


def main():
    parser = argparse.ArgumentParser(
        description="File Organizer - Mac 智能文件整理助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --list-templates                    # 列出所有模板
  %(prog)s --template office-worker --manual   # 上班族模板，手动模式
  %(prog)s --template developer --auto         # 码农模板，自动模式
  %(prog)s --downloads                         # 整理下载文件夹
  %(prog)s --screenshots --auto                # 自动整理截图
  %(prog)s --large-files --min-size 500        # 查找大于500MB的文件
        """
    )

    # 模板选项
    parser.add_argument("--list-templates", action="store_true", help="列出所有可用模板")
    parser.add_argument("--template", "-t", choices=["office-worker", "developer"], help="选择模板")

    # 模式选项
    parser.add_argument("--manual", action="store_true", help="手动模式：创建智能文件夹")
    parser.add_argument("--auto", action="store_true", help="自动模式：自动整理文件")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际移动文件")

    # 功能选项
    parser.add_argument("--downloads", action="store_true", help="整理下载文件夹")
    parser.add_argument("--screenshots", action="store_true", help="整理截图文件")
    parser.add_argument("--large-files", action="store_true", help="查找大文件")

    # 参数选项
    parser.add_argument("--days", type=int, default=365, help="扫描最近 N 天的文件（默认 365）")
    parser.add_argument("--min-size", type=int, default=100, help="大文件最小尺寸 MB（默认 100）")

    # 输出选项
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--html", action="store_true", help="HTML 格式报告")

    args = parser.parse_args()

    organizer = FileOrganizer()

    # 列出模板
    if args.list_templates:
        organizer.list_templates()
        return

    # 模板操作
    if args.template:
        if args.manual:
            result = organizer.create_manual_folders(args.template)
        elif args.auto:
            result = organizer.auto_organize(args.template, args.days, args.dry_run)
        else:
            print("❌ 请指定模式: --manual 或 --auto")
            return

        if args.json and result:
            print(json.dumps({
                "template": result.template,
                "mode": result.mode,
                "scan_time": result.scan_time,
                "total_files": result.total_files,
                "total_size_bytes": result.total_size_bytes,
                "output_path": result.output_path,
            }, indent=2, ensure_ascii=False))
        return

    # 下载文件夹
    if args.downloads:
        organizer.organize_downloads(auto=args.auto, days=args.days)
        return

    # 截图
    if args.screenshots:
        organizer.organize_screenshots(auto=args.auto, days=args.days)
        return

    # 大文件
    if args.large_files:
        organizer.find_large_files(min_size_mb=args.min_size)
        return

    # 无参数时显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
