#!/usr/bin/env python3
"""
File Organizer - Mac 智能文件整理助手

专注于整理下载文件夹中的办公文档，避免误移动代码文件。
与 disk-cleaner 配合，保护重要文件不被清理。
"""

import argparse
import json
import os
import plistlib
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


@dataclass
class FileCategory:
    """文件分类定义"""
    name: str
    icon: str
    extensions: list[str]
    description: str
    min_size_bytes: int = 0


@dataclass
class OrganizeResult:
    """整理结果"""
    mode: str
    scan_time: str
    scope: str = ""
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

    # 文件分类（专注办公文档，避免误移动代码）
    FILE_CATEGORIES = [
        FileCategory(
            name="演示文稿",
            icon="📊",
            extensions=[".ppt", ".pptx", ".key", ".odp"],
            description="PPT/Keynote 演示文稿",
        ),
        FileCategory(
            name="文档",
            icon="📝",
            extensions=[".doc", ".docx", ".pages", ".rtf", ".odt"],
            description="Word/Pages 文档",
        ),
        FileCategory(
            name="表格",
            icon="📈",
            extensions=[".xls", ".xlsx", ".numbers", ".csv", ".ods"],
            description="Excel/Numbers 表格",
        ),
        FileCategory(
            name="PDF",
            icon="📄",
            extensions=[".pdf"],
            description="PDF 文件",
        ),
        FileCategory(
            name="图片",
            icon="🖼️",
            extensions=[".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".bmp", ".tiff"],
            description="图片文件",
        ),
        FileCategory(
            name="视频",
            icon="🎬",
            extensions=[".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
            description="视频文件",
        ),
        FileCategory(
            name="音频",
            icon="🎵",
            extensions=[".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"],
            description="音频文件",
        ),
        FileCategory(
            name="压缩包",
            icon="📦",
            extensions=[".zip", ".rar", ".7z", ".tar", ".gz", ".dmg", ".pkg"],
            description="压缩包和安装包",
        ),
        FileCategory(
            name="电子书",
            icon="📚",
            extensions=[".epub", ".mobi", ".azw3", ".djvu"],
            description="电子书文件",
        ),
    ]

    # 大文件只显示这些明确用途的扩展名
    LARGE_FILE_EXTENSIONS = {
        # 文档
        ".pdf", ".ppt", ".pptx", ".key", ".doc", ".docx",
        ".xls", ".xlsx", ".pages", ".numbers",
        # 媒体
        ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v",
        ".mp3", ".wav", ".flac", ".aac", ".m4a",
        # 图片
        ".jpg", ".jpeg", ".png", ".gif", ".heic", ".psd", ".ai",
        # 压缩包
        ".zip", ".rar", ".7z", ".dmg", ".pkg", ".iso",
        # 电子书
        ".epub", ".mobi", ".azw3",
    }

    # 排除的目录（类似 Mole 白名单机制）
    EXCLUDED_DIRS = {
        # 系统/隐藏目录
        ".git", ".svn", ".hg",
        ".cache", ".npm", ".yarn", ".pnpm",
        ".venv", "venv", "env", ".env",
        "__pycache__", ".pytest_cache",
        "node_modules", "vendor", "packages",
        # macOS 系统
        "Library", ".Trash",
        # IDE/编辑器
        ".idea", ".vscode", ".vs",
        # 构建产物
        "build", "dist", "target", "out",
        "DerivedData", "Pods",
    }

    # 排除的文件模式
    EXCLUDED_PATTERNS = {
        ".DS_Store", "Thumbs.db", ".localized",
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "Cargo.lock", "Gemfile.lock", "poetry.lock",
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

    def _should_exclude(self, path: Path) -> bool:
        """检查是否应该排除该路径"""
        # 检查目录名
        for part in path.parts:
            if part in self.EXCLUDED_DIRS:
                return True
            if part.startswith("."):
                return True

        # 检查文件名
        if path.name in self.EXCLUDED_PATTERNS:
            return True

        return False

    def _is_screenshot(self, path: Path) -> bool:
        """判断是否为截图文件"""
        name = path.name.lower()
        patterns = ["screenshot", "屏幕快照", "截屏", "screen shot", "截图"]
        return any(p in name for p in patterns)

    def _get_category(self, path: Path) -> Optional[FileCategory]:
        """获取文件所属分类"""
        ext = path.suffix.lower()
        for category in self.FILE_CATEGORIES:
            if ext in category.extensions:
                return category
        return None

    def _create_smart_folder(self, name: str, query: str, scope_path: Path, output_dir: Path) -> Path:
        """创建 macOS 智能文件夹（.savedSearch）"""
        saved_search = {
            "CompatibleVersion": 1,
            "RawQuery": query,
            "SearchCriteria": {
                "CurrentFolderPath": [str(scope_path)],
                "FXScopeArrayOfPaths": [str(scope_path)],
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
            existing.discard("")  # 移除空行

            self.MOLE_WHITELIST.write_text("\n".join(sorted(existing)) + "\n")
            print(f"🔒 已添加到 disk-cleaner 白名单: {path}")
        except Exception as e:
            print(f"⚠️  添加白名单失败: {e}")

    def create_manual_folders(self, scope: str = "downloads") -> OrganizeResult:
        """手动模式：创建智能文件夹"""
        # 确定范围
        if scope == "downloads":
            scope_path = self.DOWNLOADS
            scope_name = "下载文件夹"
        elif scope == "documents":
            scope_path = self.DOCUMENTS
            scope_name = "文档文件夹"
        elif scope == "home":
            scope_path = self.HOME
            scope_name = "用户目录"
        else:
            scope_path = Path(scope)
            scope_name = scope

        print(f"🖐️ 手动模式 - 整理范围: {scope_name}")
        print("")

        # 创建输出目录
        output_dir = self.DESKTOP / "待整理"
        output_dir.mkdir(exist_ok=True)

        result = OrganizeResult(
            mode="manual",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scope=str(scope_path),
            output_path=str(output_dir),
        )

        # 为每个分类创建智能文件夹
        for category in self.FILE_CATEGORIES:
            ext_query = " || ".join(f'kMDItemFSName == "*{ext}"c' for ext in category.extensions)
            query = f"({ext_query})"
            folder_name = f"{category.icon} {category.name}"

            folder_path = self._create_smart_folder(folder_name, query, scope_path, output_dir)
            if folder_path:
                result.smart_folders.append({
                    "name": folder_name,
                    "path": str(folder_path),
                    "category": category.name,
                })
                print(f"  ✅ {folder_name}")

        # 添加大文件智能文件夹（限定扩展名）
        large_ext_query = " || ".join(f'kMDItemFSName == "*{ext}"c' for ext in self.LARGE_FILE_EXTENSIONS)
        large_query = f"({large_ext_query}) && kMDItemFSSize >= 104857600"  # 100MB
        folder_path = self._create_smart_folder("💾 大文件 (>100MB)", large_query, scope_path, output_dir)
        if folder_path:
            result.smart_folders.append({
                "name": "💾 大文件 (>100MB)",
                "path": str(folder_path),
                "category": "大文件",
            })
            print(f"  ✅ 💾 大文件 (>100MB)")

        print("")
        print(f"📁 智能文件夹已创建: {output_dir}")
        print(f"📍 搜索范围: {scope_path}")
        print("💡 双击智能文件夹查看匹配的文件，然后自行整理")

        return result

    def auto_organize(self, scope: str = "downloads", days: int = 365, dry_run: bool = False) -> OrganizeResult:
        """自动模式：扫描并整理文件"""
        # 确定范围
        if scope == "downloads":
            scope_path = self.DOWNLOADS
            scope_name = "下载文件夹"
        elif scope == "documents":
            scope_path = self.DOCUMENTS
            scope_name = "文档文件夹"
        else:
            scope_path = Path(scope)
            scope_name = scope

        print(f"🤖 自动模式 - 整理范围: {scope_name}")
        print("")

        if not scope_path.exists():
            print(f"❌ 目录不存在: {scope_path}")
            return None

        result = OrganizeResult(
            mode="auto",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            scope=str(scope_path),
        )

        # 计算时间阈值
        cutoff_date = datetime.now() - timedelta(days=days)

        # 扫描文件
        print(f"🔍 扫描最近 {days} 天内的文件...")

        categorized = {cat.name: [] for cat in self.FILE_CATEGORIES}
        categorized["其他"] = []

        try:
            for path in scope_path.rglob("*"):
                # 排除检查
                if self._should_exclude(path):
                    continue

                if path.is_dir():
                    continue

                # 获取文件信息
                info = self._get_file_info(path)
                if not info:
                    continue

                # 检查修改时间
                if info["modified"] < cutoff_date:
                    continue

                # 分类
                category = self._get_category(path)
                if category:
                    categorized[category.name].append(info)
                # 不归类未知文件（避免误移动）

        except PermissionError:
            print(f"❌ 无法访问: {scope_path}")
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

        if result.total_files == 0:
            print("ℹ️  未找到符合条件的文件")
            return result

        # 显示结果
        print(f"📊 找到 {result.total_files} 个文件, {self._format_size(result.total_size_bytes)}")
        print("")

        for cat in self.FILE_CATEGORIES:
            if cat.name in result.categories:
                data = result.categories[cat.name]
                print(f"  {cat.icon} {cat.name}: {data['count']} 个, {data['size_human']}")

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

        moved_count = 0
        for cat in self.FILE_CATEGORIES:
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
                    moved_count += 1
                except Exception as e:
                    print(f"  ⚠️  移动失败: {src.name} - {e}")

        print(f"✅ 整理完成: {moved_count} 个文件 → {output_dir}")

        # 添加到白名单
        self._add_to_whitelist(str(output_dir))

        return result

    def organize_screenshots(self, auto: bool = False, days: int = 90) -> OrganizeResult:
        """整理截图文件"""
        print("📸 整理截图文件")
        print("")

        result = OrganizeResult(
            mode="auto" if auto else "scan",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        cutoff_date = datetime.now() - timedelta(days=days)
        screenshots = []

        # 扫描截图位置
        for location in self.SCREENSHOT_LOCATIONS:
            if not location.exists():
                continue

            try:
                for path in location.iterdir():
                    if not path.is_file():
                        continue

                    if not self._is_screenshot(path):
                        continue

                    info = self._get_file_info(path)
                    if info and info["modified"] >= cutoff_date:
                        screenshots.append(info)
            except PermissionError:
                continue

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

    def find_large_files(self, min_size_mb: int = 100, limit: int = 50, scope: str = "home") -> OrganizeResult:
        """发现大文件（仅显示明确用途的文件类型）"""
        print(f"💾 查找大于 {min_size_mb}MB 的文件（仅文档/媒体类）")
        print("")

        result = OrganizeResult(
            mode="scan",
            scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        min_size_bytes = min_size_mb * 1024 * 1024
        large_files = []

        # 确定扫描范围
        if scope == "home":
            scan_paths = [self.DOCUMENTS, self.DOWNLOADS, self.DESKTOP, self.PICTURES]
        elif scope == "downloads":
            scan_paths = [self.DOWNLOADS]
        else:
            scan_paths = [Path(scope)]

        for scan_path in scan_paths:
            if not scan_path.exists():
                continue

            try:
                for path in scan_path.rglob("*"):
                    # 排除检查
                    if self._should_exclude(path):
                        continue

                    if path.is_dir():
                        continue

                    # 只显示明确用途的文件类型
                    if path.suffix.lower() not in self.LARGE_FILE_EXTENSIONS:
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

        if result.total_files == 0:
            print("ℹ️  未找到符合条件的大文件")
            return result

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
            for f in files[:10]:
                print(f"  💾 {f['size_human']:>10}  {f['name']}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")
            print("")

        result.categories = by_location

        return result

    def show_status(self):
        """显示当前状态"""
        print("📊 文件整理助手状态")
        print("")

        # 检查下载文件夹
        try:
            downloads_count = len(list(self.DOWNLOADS.iterdir()))
            print(f"📥 下载文件夹: {downloads_count} 个项目")
        except PermissionError:
            print("📥 下载文件夹: ⚠️ 无权限访问")

        # 检查截图
        screenshot_count = 0
        for loc in self.SCREENSHOT_LOCATIONS:
            if loc.exists():
                try:
                    for p in loc.iterdir():
                        if self._is_screenshot(p):
                            screenshot_count += 1
                except PermissionError:
                    pass
        print(f"📸 截图文件: {screenshot_count} 张")

        # 检查白名单
        if self.MOLE_WHITELIST.exists():
            whitelist = [l for l in self.MOLE_WHITELIST.read_text().strip().split("\n") if l]
            print(f"🔒 白名单项目: {len(whitelist)} 个")
        else:
            print("🔒 白名单项目: 0 个")


def main():
    parser = argparse.ArgumentParser(
        description="File Organizer - Mac 智能文件整理助手",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --manual                    # 手动模式（默认整理下载文件夹）
  %(prog)s --manual --scope documents  # 手动模式，整理文档文件夹
  %(prog)s --auto                      # 自动整理下载文件夹
  %(prog)s --auto --dry-run            # 预览，不实际移动
  %(prog)s --screenshots               # 查看截图
  %(prog)s --screenshots --auto        # 自动整理截图
  %(prog)s --large-files               # 查找大文件
  %(prog)s --status                    # 查看状态
        """
    )

    # 模式选项
    parser.add_argument("--manual", action="store_true", help="手动模式：创建智能文件夹")
    parser.add_argument("--auto", action="store_true", help="自动模式：自动整理文件")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，不实际移动文件")

    # 功能选项
    parser.add_argument("--screenshots", action="store_true", help="整理截图文件")
    parser.add_argument("--large-files", action="store_true", help="查找大文件")
    parser.add_argument("--status", action="store_true", help="显示状态")

    # 范围选项
    parser.add_argument("--scope", default="downloads",
                        help="整理范围: downloads（默认）, documents, home, 或自定义路径")

    # 参数选项
    parser.add_argument("--days", type=int, default=365, help="扫描最近 N 天的文件（默认 365）")
    parser.add_argument("--min-size", type=int, default=100, help="大文件最小尺寸 MB（默认 100）")

    # 输出选项
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    organizer = FileOrganizer()

    # 状态
    if args.status:
        organizer.show_status()
        return

    # 手动模式
    if args.manual:
        result = organizer.create_manual_folders(args.scope)
        if args.json and result:
            print(json.dumps({
                "mode": result.mode,
                "scope": result.scope,
                "output_path": result.output_path,
                "smart_folders": result.smart_folders,
            }, indent=2, ensure_ascii=False))
        return

    # 自动模式
    if args.auto and not args.screenshots:
        result = organizer.auto_organize(args.scope, args.days, args.dry_run)
        if args.json and result:
            print(json.dumps({
                "mode": result.mode,
                "scope": result.scope,
                "total_files": result.total_files,
                "total_size_bytes": result.total_size_bytes,
                "output_path": result.output_path,
            }, indent=2, ensure_ascii=False))
        return

    # 截图
    if args.screenshots:
        organizer.organize_screenshots(auto=args.auto, days=args.days)
        return

    # 大文件
    if args.large_files:
        organizer.find_large_files(min_size_mb=args.min_size, scope=args.scope)
        return

    # 无参数时显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
